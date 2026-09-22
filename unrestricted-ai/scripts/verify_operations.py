"""Verify the automatic watcher without invoking the manual indexing endpoint."""
import json, os, time, uuid
from pathlib import Path
import requests
root='http://workspace-api:8000'
report={'timestamp':time.time(),'tests':{}}
def request(path,body=None):
    r=requests.post(root+path,json=body,timeout=30) if body is not None else requests.get(root+path,timeout=10)
    r.raise_for_status(); return r.json()
def wait_for(fn):
    deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        if fn(): return
        time.sleep(5)
    raise TimeoutError('Automatic watcher did not propagate the change in 180 seconds')
path=Path('/workspace/automatic-watcher-'+uuid.uuid4().hex+'.txt')
query='automatic watcher verification ruby lantern sentinel '+path.stem
relative='workspace/'+path.name
try:
    started=time.monotonic()
    path.write_text(query)
    wait_for(lambda:any(p['path']==relative for p in request('/search',{'query':query,'limit':10})['results']))
    report['tests']['automatic_create']={'pass':True,'seconds':time.monotonic()-started,'path':relative}
    print('PASS automatic_create',flush=True)
    started=time.monotonic(); path.unlink()
    wait_for(lambda:all(p['path']!=relative for p in request('/search',{'query':query,'limit':10})['results']))
    report['tests']['automatic_delete']={'pass':True,'seconds':time.monotonic()-started}
    print('PASS automatic_delete',flush=True)
    ollama=os.environ['OLLAMA_URL']; embedding=os.environ['OLLAMA_EMBED_URL']
    before=requests.get(ollama+'/api/ps',timeout=10).json()['models']
    request('/search',{'query':'local AI workspace verification phrase','limit':3})
    after=requests.get(ollama+'/api/ps',timeout=10).json()['models']
    assert before and [m['digest'] for m in before]==[m['digest'] for m in after],'Embedding evicted or replaced the resident chat model'
    embed=requests.get(embedding+'/api/ps',timeout=10).json()['models']
    assert embed and all(m['size_vram']==0 for m in embed),'Embeddings are using the GPU'
    report['tests']['embedding_isolation']={'pass':True,'resident_chat_models':[m['name'] for m in after],'embedding_vram_bytes':0}
    report['passed']=True
except Exception as error:
    report['passed']=False; report['error']=str(error)
finally:
    path.unlink(missing_ok=True)
    Path('/state/operations.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
raise SystemExit(0 if report['passed'] else 1)
