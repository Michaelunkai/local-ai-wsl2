"""Wait for real service readiness after Compose starts/recreates containers."""
import os, time, runpy
from pathlib import Path
import requests
targets={'open-webui':'http://open-webui:8080/health','qdrant':'http://qdrant:6333/readyz','workspace-api':'http://workspace-api:8000/health','searxng':'http://searxng:8080/healthz','crawl4ai':'http://crawl4ai:11235/health','ollama':os.environ['OLLAMA_URL']+'/api/version','embeddings':os.environ['OLLAMA_EMBED_URL']+'/api/version'}
deadline=time.monotonic()+180
while time.monotonic()<deadline:
    failed=[]
    for name,url in targets.items():
        try: requests.get(url,timeout=3).raise_for_status()
        except requests.RequestException: failed.append(name)
    if not failed:
        print('All service readiness probes passed',flush=True)
        break
    print('Waiting for: '+', '.join(failed),flush=True)
    time.sleep(3)
else: raise SystemExit('Service startup deadline exceeded: '+', '.join(failed))
runpy.run_path(str(Path(__file__).with_name('check-startup-internet.py')), run_name='__main__')
