"""Record pulled immutable image digests for subsequent launches."""
import json, os, pathlib, subprocess
root=pathlib.Path(__file__).resolve().parents[1]
cmd=['docker','compose','--env-file',str(root/'docker/.env'),'-f',str(root/'docker/docker-compose.yml'),'config','--format','json']
config=json.loads(subprocess.check_output(cmd))
lines=['services:']
for name,service in config['services'].items():
    if 'build' in service: continue
    details=json.loads(subprocess.check_output(['docker','image','inspect',service['image']]))[0]
    digests=details.get('RepoDigests',[])
    if not digests: raise RuntimeError('Image has no registry digest: '+service['image'])
    lines.extend(['  '+name+':','    image: '+digests[0]])
(root/'docker/images.lock.yml').write_text('\n'.join(lines)+'\n')
