"""Save new optimizer source as an evolutionary genotype for the next run.

Code is saved as *untrusted text* only and is never imported by the trusted host.
The next free-model call can critique/mutate it. All generated executables run only
in the networkless Docker sandbox.
"""
import json
import shutil
from pathlib import Path


def main():
    src = Path('candidate.py')
    report = Path('state/report.json')
    if not src.exists() or not report.exists():
        print('GENOTYPE: No candidate to preserve')
        return
    content = src.read_text(encoding='utf-8', errors='replace')
    if not content.strip() or len(content) > 20000:
        print('GENOTYPE: Candidate absent or oversized')
        return
    dest = Path('state/last_candidate.py')
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(content, encoding='utf-8')
    stats = json.loads(report.read_text())
    score_delta = stats.get('instructions_saved', 0)
    if score_delta > 0:
        # The stage improved; save source for inspection. It has NOT necessarily
        # improved by itself; pruning may have contributed. Not executed by host.
        Path('state/last_successful_candidate.py').write_text(content, encoding='utf-8')
    print(f'GENOTYPE: preserved for future mutation; AI-stage savings={score_delta}')

if __name__=='__main__': main()
