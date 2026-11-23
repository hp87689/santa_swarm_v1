"""Commit machine-readable score feedback to agent memory, no AI involved."""
import json
from pathlib import Path


def main():
    path = Path('state/agent_history.json')
    rep = Path('state/report.json')
    if not path.exists() or not rep.exists():
        return
    history = json.loads(path.read_text())
    report = json.loads(rep.read_text())
    if history:
        history[-1]['model_instructions_saved'] = report.get('instructions_saved', 0)
        history[-1]['model_puzzles_improved'] = report.get('puzzles_improved', 0)
        history[-1]['total_instructions_saved_this_run'] = report.get('total_instructions_saved_this_run', 0)
        history[-1]['verified_after_score'] = report.get('new_score')
        path.write_text(json.dumps(history[-12:], indent=2), encoding='utf-8')
        print('EXPERIMENT FEEDBACK:', json.dumps(history[-1]))

if __name__ == '__main__':
    main()
