"""Static contract review only: does not import the app or invoke any integration."""
import ast
import json
from pathlib import Path
import time

root=Path(__file__).resolve().parents[1]
tree=ast.parse((root/'scripts/workspace_api.py').read_text(encoding='utf-8-sig'))
schemas={}
for group,file in [('windows_ui','windows-ui-tool-schema.json'),('desktop','desktop-tool-schema.json')]:
    data=json.loads((root/'logs'/file).read_text(encoding='utf-8-sig'))
    schemas[group]={t['name']:t['inputSchema'] for t in data['tools']}

checks=[]
def check_keys(group,tool,keys):
    schema=schemas[group][tool]
    assert set(keys)<=set(schema['properties']),(group,tool,'unknown arguments',keys)
    assert set(schema.get('required',[]))<=set(keys),(group,tool,'missing arguments',keys)
    checks.append({'integration':group,'tool':tool,'arguments':sorted(keys)})

# Validate the literal UI-action mappings against previously captured upstream schemas.
for node in ast.walk(tree):
    if isinstance(node,ast.Assign) and isinstance(node.value,ast.Tuple) and len(node.value.elts)==2:
        name,args=node.value.elts
        if isinstance(name,ast.Constant) and isinstance(name.value,str) and isinstance(args,ast.Dict):
            if name.value in schemas['windows_ui']:
                check_keys('windows_ui',name.value,[k.value for k in args.keys])
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='call_host_tool' and len(node.args)==3:
        group,name,args=node.args
        if all(isinstance(x,ast.Constant) for x in (group,name)) and isinstance(args,ast.Dict):
            check_keys(group.value,name.value,[k.value for k in args.keys])

classes={n.name:{x.target.id for x in n.body if isinstance(x,ast.AnnAssign)} for n in tree.body if isinstance(n,ast.ClassDef)}
for cls,group,tool in [('WindowsRead','desktop','read_file'),('WindowsWrite','desktop','write_file'),('WindowsPowerShell','windows_ui','PowerShell')]:
    check_keys(group,tool,classes[cls])
assert len(checks)>=8,'Expected direct-tool mappings were not reviewed'
bridge=(root/'integrations/host-bridge.mjs').read_text()
assert 'USERPROFILE:profile' not in bridge,'Windows user profile must not be redirected'
assert "POSTHOG_API_KEY:''" in bridge,'Windows MCP telemetry opt-out missing'
assert 'DESKTOP_COMMANDER_CONFIG_DIR:' in bridge,'Project configuration directory missing'
adapter=(root/'scripts/configure-integration-storage.ps1').read_text()
upstream=(root/'integrations/node_modules/@wonderwhy-er/desktop-commander/dist/config.js').read_text()
assert "const CONFIG_DIR = path.join(USER_HOME, '.claude-server-commander');" in upstream or 'const CONFIG_DIR = process.env.DESKTOP_COMMANDER_CONFIG_DIR ||' in upstream
assert 'throw ' in adapter,'Storage adapter must stop on an unknown package layout'
report={'timestamp':time.time(),'review':'static_only','passed':True,'checks':checks,'not_verified':['Actual desktop operations','Browser connection','Direct-tool model behavior','Storage adapter execution','Live performance']}
(root/'logs/direct-tools-static-review.json').write_text(json.dumps(report,indent=2))
print('Static tool contracts reviewed:',len(checks),'; no application or integration executed')
