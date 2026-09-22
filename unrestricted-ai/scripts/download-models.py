"""Reproduce verified downloads using pinned upstream commits and SHA-256."""
import argparse, hashlib, json, pathlib, subprocess, sys
p=argparse.ArgumentParser()
p.add_argument('--root',required=True)
p.add_argument('--only',default='',nargs='?',const='')
a=p.parse_args()
root=pathlib.Path(a.root)
venv=root/'runtime/hf-venv'
python=venv/'bin/python'
if not python.exists():
    subprocess.run([sys.executable,'-m','venv',str(venv)],check=True)
    subprocess.run([str(python),'-m','pip','install','huggingface_hub==1.32.0'],check=True)
hf=venv/'bin/hf'
for model in json.loads((root/'models.lock.json').read_text()):
    if a.only and model['directory']!=a.only: continue
    directory=root/'data/model-sources'/model['directory']
    for name,digest in model['files'].items():
        target=directory/name
        if not target.exists():
            subprocess.run([str(hf),'download',model['repository'],name,'--revision',model['revision'],'--local-dir',str(directory)],check=True)
        with target.open('rb') as source:
            actual=hashlib.file_digest(source,'sha256').hexdigest()
        if actual!=digest: raise RuntimeError('Checksum mismatch: '+str(target))
        print('Verified '+name,flush=True)
