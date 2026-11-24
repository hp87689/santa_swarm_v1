"""Persistent, adaptive quality-diversity population for Santa 2026.

Each genome specifies an independently run mathematical resynthesis strategy.
The survivor is always the shortest fully verified program *per puzzle*, not a
language-model opinion. Evolutionary mutation changes strategy parameters.
State is stored as JSON in the champion artifact, surviving GitHub restarts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import time
from pathlib import Path

from beam_resynthesis import improve_beam
from core import load_puzzles, load_submission, replay, save_submission, verify_all
from resynthesis import improve_resynthesis

MAX_POPULATION = 8
DEFAULT_GENOMES = [
    dict(id='beam_multi',method='beam',window_size=10,max_depth=4,
         beam_width=20,helper_cap=20,exploration=0,max_windows=60),
    dict(id='beam_wide',method='beam',window_size=14,max_depth=4,
         beam_width=36,helper_cap=24,exploration=1,max_windows=60),
    dict(id='beam_deep',method='beam',window_size=11,max_depth=5,
         beam_width=16,helper_cap=30,exploration=2,max_windows=40),
    dict(id='beam_explore',method='beam',window_size=15,max_depth=4,
         beam_width=12,helper_cap=48,exploration=3,max_windows=45),
    dict(id='inverse_two_step',method='legacy',window_size=10,max_depth=2,
         beam_width=8,helper_cap=20,exploration=0,max_windows=350),
    dict(id='beam_small',method='beam',window_size=8,max_depth=3,
         beam_width=10,helper_cap=12,exploration=0,max_windows=70),
]


def _new_memory():
    return {'version':2,'generation_count':0,
            'population':[dict(g, tested=0, improved=0, saved=0, created=0) for g in DEFAULT_GENOMES],
            'history':[]}

def load_memory(path):
    file = Path(path)
    if not file.exists():
        return _new_memory()
    try:
        mem = json.loads(file.read_text(encoding='utf-8'))
        if mem.get('version') == 2 and isinstance(mem.get('population'),list):
            valid=[]
            for g in mem['population'][:MAX_POPULATION]:
                if g.get('method') in ('beam','legacy') and isinstance(g.get('id'),str):
                    if all(type(g.get(k)) is int for k in ('window_size','max_depth','beam_width','helper_cap',
                                                           'exploration','max_windows','tested','improved','saved')):
                        valid.append(g)
            if valid:
                mem['population'] = valid
                mem['history'] = mem.get('history', [])[-15:]
                return mem
    except (ValueError,TypeError,OSError):
        pass
    return _new_memory()


def _mutate_genome(parent,rng,ident,generation):
    child = dict(parent)
    child.update(id=ident,created=generation,tested=0,improved=0,saved=0)
    # At least one parameter mutates, even when population has stagnated.
    keys = ('window_size','max_depth','beam_width','helper_cap','exploration','max_windows')
    for key in rng.sample(keys,k=rng.randint(2,4)):
        lo,hi,step = {
            'window_size':(6,18,2),'max_depth':(2,6,1),
            'beam_width':(6,48,6),'helper_cap':(8,56,8),
            'exploration':(0,4,1),'max_windows':(20,100,10),
        }[key]
        child[key]=max(lo,min(hi,child[key]+step*rng.choice([-1,1])))
    # Keep some legacy inverse-search diversity but most offspring use beam.
    if rng.random() < 0.12:
        child['method']=rng.choice(('legacy','beam'))
    return child


def _choose_population(population,rng,count=2):
    total = sum(x['tested'] for x in population)+1
    def score(x):
        # Smoothed reward to prevent previously lucky one-off wins dominating.
        payoff=(x['saved']+0.2*x['improved'])/(x['tested']+5)
        discovery=1.1*math.sqrt(math.log(total+1)/(x['tested']+1))
        return payoff+discovery+rng.random()*0.02
    return sorted(population,key=score,reverse=True)[:count]


def _evolve_population(pop,rng,generation):
    if len(pop)<2:
        return pop
    # Periodically replace the worst underexplored non-elite with a mutated
    # child of a high-performing or promising member. This is algorithm search,
    # not copying a public submission.
    ranks=sorted(pop,key=lambda g:(g['saved']/(g['tested']+4),g['improved']),reverse=True)
    parents=ranks[:max(2,len(ranks)//2)]
    parent=rng.choice(parents)
    if len(pop)>=MAX_POPULATION:
        victims=sorted(pop,key=lambda g:(g['saved']/(g['tested']+4),g['improved']))
        victim=next((g for g in victims if g['id'] not in {x['id'] for x in ranks[:2]}),victims[0])
        pop.remove(victim)
    ident=f"child_g{generation}_{rng.randint(0,9999):04d}"
    pop.append(_mutate_genome(parent,rng,ident,generation))
    return pop


def run_portfolio(puzzles,baseline,*,generation=1,memory=None,max_seconds=180,
                  max_puzzles=70,seconds_per_trial=1.1,trials_per_puzzle=2):
    if memory is None:
        memory=load_memory('__nonexistent_santa_swarm_memory__.json')
    rng=random.Random(generation*7147+1)
    chosen={pid:[ins[:] for ins in seq] for pid,seq in baseline.items()}
    pop=memory['population']
    started=time.monotonic()
    # Stable permutation per cycle: process different puzzles on different runs
    # rather than re-shuffling and accidentally selecting the same first rows.
    order=sorted(puzzles,key=lambda pid:hashlib.sha256(f'{pid}:cycle{(generation-1)//15}'.encode()).digest())
    sz=min(max_puzzles,len(order))
    offset=((generation-1)*sz)%len(order)
    chosen_ids=(order+order)[offset:offset+sz]
    stats={'generation':generation,'method':'multi_target_evolutionary_portfolio',
           'puzzles_attempted':0,'puzzles_improved':0,'instructions_saved':0,
           'states_expanded':0,'windows_tested':0,'valid_candidates':0,
           'invalid_candidates':0,'trial_errors':0,'arm_runs':{},'improvements':[]}
    for pid in chosen_ids:
        if time.monotonic()-started>max_seconds-0.03:
            break
        stats['puzzles_attempted']+=1
        puzzle=puzzles[pid]
        origin=chosen[pid]
        best=origin
        for gene in _choose_population(pop,rng,trials_per_puzzle):
            remain=max_seconds-(time.monotonic()-started)
            if remain<0.03:
                break
            seconds=min(seconds_per_trial,remain)
            seed=int(hashlib.sha256(f'{gene["id"]}:{generation}:{pid}'.encode()).hexdigest()[:15],16)
            gene['tested']+=1
            arm=stats['arm_runs'].setdefault(gene['id'],{'tested':0,'improved':0,'saved':0,'errors':0})
            arm['tested']+=1
            try:
                if gene['method']=='legacy':
                    proposal,diag=improve_resynthesis(
                        puzzle,best,seed=seed,width=gene['window_size'],
                        max_windows=gene['max_windows'],max_seconds=seconds)
                    stats['windows_tested']+=diag['windows_tested']
                else:
                    proposal,diag=improve_beam(puzzle,best,seed=seed,
                        max_seconds=seconds,max_windows=gene['max_windows'],
                        window_size=gene['window_size'],max_depth=gene['max_depth'],
                        beam_width=gene['beam_width'],helper_cap=gene['helper_cap'],
                        exploration=gene['exploration'])
                    stats['states_expanded']+=diag['states_expanded']
                    stats['windows_tested']+=diag['windows_tested']
                if len(proposal) < len(best):
                    try:
                        replay(puzzle,proposal)
                    except (ValueError,TypeError,OverflowError,ZeroDivisionError):
                        stats['invalid_candidates']+=1
                        continue
                    saved=len(best)-len(proposal)
                    best=proposal
                    gene['improved']+=1
                    gene['saved']+=saved
                    arm['improved']+=1
                    arm['saved']+=saved
                    stats['valid_candidates']+=1
            except Exception as err:
                stats['trial_errors']+=1
                arm['errors']+=1
        if len(best)<len(origin):
            replay(puzzle,best)
            chosen[pid]=best
            stats['puzzles_improved']+=1
            saved=len(origin)-len(best)
            stats['instructions_saved']+=saved
            stats['improvements'].append({'id':pid,'saved':saved})
    stats['previous_score']=verify_all(puzzles,baseline)
    stats['new_score']=verify_all(puzzles,chosen)
    assert stats['previous_score']-stats['new_score']==stats['instructions_saved']
    stats['elapsed_seconds']=round(time.monotonic()-started,2)
    memory['generation_count']=int(memory.get('generation_count',0))+1
    memory['history']=(memory.get('history',[])+[{
       'generation':generation,'saved':stats['instructions_saved'],
       'puzzles_improved':stats['puzzles_improved']}])[-15:]
    if generation%2==0:
        _evolve_population(pop,rng,generation)
    stats['population_size']=len(pop)
    stats['population_summary']=[{'id':g['id'],'method':g['method'],'tested':g['tested'],
                                  'saved':g['saved']} for g in pop]
    stats['note']='Every accepted edit independently replayed. Real improvements may be zero.'
    return chosen,stats,memory


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('puzzles');parser.add_argument('baseline');parser.add_argument('output');parser.add_argument('report')
    parser.add_argument('--memory',default='state/evolution_memory.json')
    parser.add_argument('--generation',type=int,default=1)
    parser.add_argument('--max-seconds',type=float,default=180)
    parser.add_argument('--max-puzzles',type=int,default=70)
    parser.add_argument('--seconds-per-trial',type=float,default=1.1)
    args=parser.parse_args()
    puzzles=load_puzzles(args.puzzles);base=load_submission(args.baseline)
    mem=load_memory(args.memory)
    chosen,report,mem=run_portfolio(puzzles,base,generation=args.generation,
        memory=mem,max_seconds=args.max_seconds,max_puzzles=args.max_puzzles,
        seconds_per_trial=args.seconds_per_trial)
    save_submission(args.output,chosen,puzzles)
    Path(args.memory).parent.mkdir(parents=True,exist_ok=True)
    Path(args.memory).write_text(json.dumps(mem,indent=2),encoding='utf-8')
    Path(args.report).parent.mkdir(parents=True,exist_ok=True)
    Path(args.report).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('EVOLUTIONARY PORTFOLIO:',json.dumps(report))

if __name__=='__main__':
    main()
