"""Capture stdout/stderr and timings for concurrent real WebUI execution calls."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import time
import requests

base='http://open-webui:8080'
r=requests.post(base+'/api/v1/auths/signin',json={'email':'admin@localhost','password':'admin'},timeout=30)
r.raise_for_status()
headers={'Authorization':'Bearer '+r.json()['token']}
def check(index):
    started=time.monotonic()
    marker='SANDBOX-CONCURRENT-'+str(index)
    code=f'from pathlib import Path\nprint({marker!r}, flush=True)\nprint(sum(i*i for i in range(10)), flush=True)\nPath("sandbox-diagnostic-{index}.txt").write_text({marker!r})'
    try:
        response=requests.post(base+'/api/v1/utils/code/execute',headers=headers,json={'code':code},timeout=100)
        response.raise_for_status()
        result=response.json()
        return {'index':index,'seconds':time.monotonic()-started,'result':result,
                'passed':marker in result.get('stdout','') and '285' in result.get('stdout','') and not result.get('stderr')}
    except Exception as error:
        return {'index':index,'seconds':time.monotonic()-started,'passed':False,'error':str(error)}
report={'started':time.time(),'results':[]}
with ThreadPoolExecutor(max_workers=3) as pool:
    jobs=[pool.submit(check,i) for i in range(9)]
    for future in as_completed(jobs):
        result=future.result();report['results'].append(result)
        print(json.dumps(result),flush=True)
report['passed']=all(r['passed'] for r in report['results'])
report['finished']=time.time()
Path('/state/sandbox-concurrency-diagnostic.json').write_text(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
