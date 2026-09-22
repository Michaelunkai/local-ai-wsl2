"""Bounded outbound checks: unavailable internet must not disable local chats."""
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys
import time

URLS = ('https://www.python.org/', 'https://example.com/')
PROBE = '''import sys, urllib.request
try:
    with urllib.request.urlopen(sys.argv[1], timeout=4) as response:
        if response.status != 200:
            raise RuntimeError('Unexpected HTTP status')
except Exception as exc:
    print(type(exc).__name__)
    sys.exit(1)
'''


def probe(url):
    try:
        result = subprocess.run(
            [sys.executable, '-c', PROBE, url], capture_output=True,
            text=True, timeout=8, check=False,
        )
        return {'url': url, 'passed': result.returncode == 0,
                'error': None if result.returncode == 0 else 'HTTPS probe failed'}
    except subprocess.TimeoutExpired:
        return {'url': url, 'passed': False, 'error': 'DNS/HTTPS probe exceeded 8 seconds'}
    except OSError:
        return {'url': url, 'passed': False, 'error': 'Could not start HTTPS probe'}


def check():
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(probe, URLS))
    return {'timestamp': time.time(), 'internetReachable': any(r['passed'] for r in results),
            'allProbesPassed': all(r['passed'] for r in results), 'probes': results,
            'seconds': round(time.monotonic() - started, 3),
            'scope': 'Public DNS and verified HTTPS only; provider availability and browser authorization are separate.'}


if __name__ == '__main__':
    report = check()
    path = Path('/state/startup-internet.json')
    try:
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(report, indent=2), encoding='utf-8')
        temporary.replace(path)
    except OSError as exc:
        print('WARNING: Could not save internet diagnostic: ' + type(exc).__name__, flush=True)
    if report['allProbesPassed']:
        print('Startup public DNS and HTTPS checks passed', flush=True)
    elif report['internetReachable']:
        print('WARNING: One public HTTPS probe failed; internet is reachable but some sources may be unavailable.', flush=True)
    else:
        print('WARNING: Public DNS/HTTPS checks failed. Local chats remain available; online research may fail. See data/indexer/startup-internet.json.', flush=True)
