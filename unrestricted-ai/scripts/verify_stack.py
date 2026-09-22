"""Run inside workspace-api; failures are recorded individually and cause a nonzero exit."""
import argparse, base64, json, os, struct, time, traceback, uuid, zlib
from pathlib import Path
import requests

REPORT={'timestamp':time.time(),'tests':{}}
parser=argparse.ArgumentParser()
parser.add_argument('--only',nargs='*',default=[])
parser.add_argument('--retry-failed',action='store_true')
args=parser.parse_args()
selected=args.only
if args.retry_failed:
    REPORT=json.loads(Path('/state/verification.json').read_text())
    selected=[name for name,result in REPORT['tests'].items() if not result['pass']]
    if not selected: print('No failed checks to retry'); raise SystemExit(0)
    REPORT.setdefault('retries',[]).append({'timestamp':time.time(),'tests':selected,'previous_results':{name:REPORT['tests'][name] for name in selected}})
OLLAMA=os.environ.get('OLLAMA_URL','http://host.docker.internal:11434')
def call(method,url,**kwargs):
    response=requests.request(method,url,timeout=kwargs.pop('timeout',180),**kwargs)
    if not response.ok: raise RuntimeError(f'{response.status_code} {url}: {response.text[:500]}')
    return response.json()
def test(name,fn):
    if selected and name not in selected: return
    start=time.monotonic()
    try:
        detail=fn(); REPORT['tests'][name]={'pass':True,'seconds':round(time.monotonic()-start,2),'detail':detail}
        print('PASS',name,flush=True)
    except Exception as error:
        REPORT['tests'][name]={'pass':False,'seconds':round(time.monotonic()-start,2),'error':str(error)}
        print('FAIL',name,str(error),flush=True)
def assert_true(value,message):
    if not value: raise AssertionError(message)
def inference(model):
    start=time.monotonic(); first=None; text=''; chunks=0; final={}
    body={'model':model,'messages':[{'role':'user','content':'What is 17 multiplied by 23? Reply with just the integer.'}],'stream':True,'options':{'num_predict':256,'temperature':0}}
    if model.startswith('local-qwen'): body['think']=False
    with requests.post(OLLAMA+'/api/chat',json=body,stream=True,timeout=600) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line: continue
            data=json.loads(line)
            if 'error' in data: raise RuntimeError(data['error'])
            token=data.get('message',{}).get('content','')
            if token:
                if first is None: first=time.monotonic()-start
                text+=token; chunks+=1
            if data.get('done'): final=data
    assert_true('391' in text,'Incorrect or empty arithmetic answer: '+text)
    assert_true(chunks>0 and final.get('done'),'Stream did not complete')
    return {'answer':text,'first_token_seconds':first,'tokens_per_second':final.get('eval_count',0)/(final.get('eval_duration',1)/1e9),'load_seconds':final.get('load_duration',0)/1e9}

def extended_context(model):
    paragraphs=[f'Reference paragraph {i:04d}: local project workflows support reproducible research, documentation, development and testing.' for i in range(700)]
    paragraphs.insert(250,'The long-context verification phrase is AMBER-STONE-6192.')
    body={'model':model,'messages':[{'role':'user','content':'Read the following reference document and report its long-context verification phrase.\n'+'\n'.join(paragraphs)+'\nReturn only the verification phrase.'}],'stream':False,'options':{'temperature':0,'num_predict':64}}
    if 'qwen' in model: body['think']=False
    result=call('POST',OLLAMA+'/api/chat',json=body,timeout=900)
    answer=result['message']['content']
    assert_true('AMBER-STONE-6192' in answer,'Long-context retrieval failed: '+answer)
    assert_true(result['prompt_eval_count']>8192,'Test did not exceed the default 8K context')
    resident=call('GET',OLLAMA+'/api/ps')['models']
    assert_true(any(m['name']==model and m['context_length']==32768 for m in resident),'32K context was not allocated')
    return {'answer':answer,'input_tokens':result['prompt_eval_count'],'context':32768,'load_seconds':result['load_duration']/1e9,'prompt_seconds':result['prompt_eval_duration']/1e9}
def search():
    data=call('POST','http://workspace-api:8000/web/search',json={'query':'Python official documentation','limit':3})
    assert_true(len(data['results'])>0,'No live search results'); return data
def crawl():
    data=call('POST','http://workspace-api:8000/web/crawl',json={'url':'https://www.python.org/'})
    assert_true(data['success'] and 'Python' in data['markdown'],'Crawl returned no useful Markdown'); return {'characters':len(data['markdown'])}
def retrieval():
    indexed=call('POST','http://workspace-api:8000/index',timeout=600)
    data=call('POST','http://workspace-api:8000/search',json={'query':'local AI workspace verification phrase','limit':5})
    assert_true(any(p['path']=='workspace/retrieval-check.md' and 'SILVER-ORCHID-742' in p['text'] for p in data['results']),'Known document not retrieved'); return {'indexed':indexed,'paths':[p['path'] for p in data['results']]}
def rag_answer():
    data=call('POST','http://workspace-api:8000/search',json={'query':'local AI workspace verification phrase','limit':3})
    context='\n'.join(p['text'] for p in data['results'])
    answer=call('POST',OLLAMA+'/api/chat',json={'model':'local-qwen:27b','messages':[{'role':'user','content':'From these retrieved files, give the workspace verification phrase.\n'+context}],'stream':False,'think':False,'options':{'num_predict':256}},timeout=600)
    text=answer['message']['content']; assert_true('SILVER-ORCHID-742' in text,'Model did not use retrieved context'); return text
def mcp():
    data=call('POST','http://workspace-api:8000/mcp/',headers={'Accept':'application/json, text/event-stream'},json={'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'verifier','version':'1'}}})
    assert_true('result' in data,'MCP initialization failed')
    result=call('POST','http://workspace-api:8000/mcp/',headers={'Accept':'application/json, text/event-stream'},json={'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'read_project_file','arguments':{'path':'workspace/retrieval-check.md'}}})
    assert_true('SILVER-ORCHID-742' in json.dumps(result),'MCP tool did not read the document')
    return data['result']['serverInfo']

def vision():
    def chunk(kind,data): return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',128,128,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\xff\0\0'*128)*128))+chunk(b'IEND',b'')
    answer=call('POST',OLLAMA+'/api/chat',json={'model':'local-qwen:27b','messages':[{'role':'user','content':'What is the main color of this image? Reply with one color name.','images':[base64.b64encode(png).decode()]}],'stream':False,'think':False,'options':{'num_predict':32,'temperature':0}},timeout=600)
    text=answer['message']['content']; assert_true('red' in text.lower(),'Vision answer incorrect: '+text); return text

def native_tools():
    messages=[{'role':'user','content':'Read workspace/retrieval-check.md using the provided tool, then tell me the verification phrase written in that file.'}]
    tools=[{'type':'function','function':{'name':'read_project_file','description':'Read a document by its project-relative path','parameters':{'type':'object','properties':{'path':{'type':'string'}},'required':['path']}}}]
    body={'model':'local-qwen:27b','messages':messages,'tools':tools,'stream':False,'think':False,'options':{'num_predict':256,'temperature':0}}
    response=call('POST',OLLAMA+'/api/chat',json=body,timeout=600)['message']
    assert_true(response.get('tool_calls'),'Model did not request the tool')
    messages.append(response)
    for tool in response['tool_calls']:
        function=tool['function']; assert_true(function['name']=='read_project_file','Unexpected tool')
        result=call('GET','http://workspace-api:8000/files/read',params=function['arguments'])
        messages.append({'role':'tool','tool_name':function['name'],'content':json.dumps(result)})
    body.pop('tools')
    answer=call('POST',OLLAMA+'/api/chat',json=body,timeout=600)['message']['content']
    assert_true('SILVER-ORCHID-742' in answer,'Model did not use tool result'); return answer

def generated_code(model):
    body={'model':model,'messages':[{'role':'user','content':'Write only Python code, no Markdown. Compute the sum of squares of the integers 1 through 12 inclusive and print the integer. Then write that integer to generated-'+model.split(':')[0]+'.txt in the current directory.'}],'stream':False,'options':{'num_predict':256,'temperature':0}}
    if 'qwen' in model: body['think']=False
    code=call('POST',OLLAMA+'/api/chat',json=body,timeout=600)['message']['content'].strip()
    if code.startswith('```'): code='\n'.join(code.splitlines()[1:-1])
    auth=call('POST','http://open-webui:8080/api/v1/auths/signin',json={'email':'admin@localhost','password':'admin'})
    data=call('POST','http://open-webui:8080/api/v1/utils/code/execute',headers={'Authorization':'Bearer '+auth['token']},json={'code':code})
    assert_true('650' in data.get('stdout','') and not data.get('stderr'),'Generated code failed: '+json.dumps(data))
    assert_true(Path('/workspace/generated-'+model.split(':')[0]+'.txt').read_text().strip()=='650','Generated code did not persist the result')
    return {'code':code,'stdout':data['stdout']}

def js_render():
    from html.parser import HTMLParser
    class VisibleText(HTMLParser):
        def __init__(self): super().__init__(); self.hidden=0; self.parts=[]
        def handle_starttag(self,tag,attrs):
            if tag in ('script','style'): self.hidden+=1
        def handle_endtag(self,tag):
            if tag in ('script','style'): self.hidden=max(0,self.hidden-1)
        def handle_data(self,data):
            if not self.hidden: self.parts.append(data)
    url='https://quotes.toscrape.com/js/'
    raw=requests.get(url,timeout=30); raw.raise_for_status()
    parser=VisibleText(); parser.feed(raw.text)
    assert_true('Albert Einstein' not in ''.join(parser.parts),'Fixture no longer requires JavaScript')
    data=call('POST','http://workspace-api:8000/web/crawl',json={'url':url})
    assert_true(data['success'] and 'Albert Einstein' in data['markdown'],'JavaScript-rendered quotation missing')
    return {'url':url,'javascript_only_text':'Albert Einstein','characters':len(data['markdown'])}
def ui():
    r=requests.get('http://open-webui:8080/health',timeout=20); r.raise_for_status(); return r.json()

def webui_tool_roundtrip(tool_id,model='local-qwen:27b'):
    auth=call('POST','http://open-webui:8080/api/v1/auths/signin',json={'email':'admin@localhost','password':'admin'})
    headers={'Authorization':'Bearer '+auth['token']}
    listed=call('GET','http://open-webui:8080/api/v1/tools/',headers=headers)
    assert_true(any(t['id']==tool_id for t in listed),'Tool connection absent: '+tool_id)
    body={'model':'local-qwen:27b','messages':[{'role':'user','content':'Use the read_project_file tool to read workspace/retrieval-check.md and tell me the verification phrase. Do not guess it.'}],'tool_ids':[tool_id],'stream':True,'params':{'function_calling':'native','temperature':0,'num_predict':256,'think':False}}
    body['model']=model
    if 'dolphin' in model:
        body['params']['function_calling']='legacy'
        body['params'].pop('think')
    # Use WebUI's saved-chat execution path. Its stateless OpenAI endpoint
    # intentionally returns raw tool calls for an API client to execute.
    message_id=str(uuid.uuid4())
    body.update(parent_id=None,id=message_id,session_id='local-stack-verifier',user_message={'id':str(uuid.uuid4()),'role':'user','content':body['messages'][0]['content'],'timestamp':int(time.time())})
    started=call('POST','http://open-webui:8080/api/chat/completions',headers=headers,json=body,timeout=600)
    chat_id=started['chat_id']
    message={}
    for attempt in range(180):
        chat=call('GET','http://open-webui:8080/api/v1/chats/'+chat_id,headers=headers)
        message=chat['chat']['history']['messages'].get(message_id,{})
        if message.get('done'): break
        time.sleep(2)
    text=json.dumps(message)
    assert_true(message.get('done') and 'SILVER-ORCHID-742' in text,'WebUI did not finish the tool response: '+text[-1000:])
    return {'tool_id':tool_id,'chat_id':chat_id,'answer_contains_verification_phrase':True,'message':message}

def live_context_answer():
    result=call('POST','http://workspace-api:8000/web/search',json={'query':'Python documentation official tutorial','limit':3})
    official=next(p for p in result['results'] if 'python.org' in p['url'])
    page=call('POST','http://workspace-api:8000/web/crawl',json={'url':official['url']})
    body={'model':'local-qwen:27b','messages':[{'role':'user','content':'Based only on this freshly fetched page, name the programming language it documents and give the source URL.\nURL: '+official['url']+'\n'+page['markdown'][:6000]}],'think':False,'stream':False,'options':{'temperature':0,'num_predict':128}}
    answer=call('POST',OLLAMA+'/api/chat',json=body,timeout=600)['message']['content']
    assert_true('Python' in answer and official['url'] in answer,'Live source not used in answer'); return answer
def sandbox():
    auth=call('POST','http://open-webui:8080/api/v1/auths/signin',json={'email':'admin@localhost','password':'admin'})
    data=call('POST','http://open-webui:8080/api/v1/utils/code/execute',headers={'Authorization':'Bearer '+auth['token']},json={'code':'from pathlib import Path\nprint(sum(i*i for i in range(10)))\nPath("sandbox-verification.txt").write_text("Sandbox persisted correctly")'})
    assert_true('285' in json.dumps(data),'Sandbox did not return the expected output: '+json.dumps(data)); return data
def webui_search():
    auth=call('POST','http://open-webui:8080/api/v1/auths/signin',json={'email':'admin@localhost','password':'admin'})
    data=call('POST','http://open-webui:8080/api/v1/retrieval/process/web/search',headers={'Authorization':'Bearer '+auth['token']},json={'queries':['Python official documentation']},timeout=240)
    assert_true(data.get('status') and data.get('loaded_count',0)>0,'WebUI did not load search results')
    return {'loaded_count':data['loaded_count'],'collections':data.get('collection_names'),'urls':data.get('filenames')}
def sandbox_boundaries():
    auth=call('POST','http://open-webui:8080/api/v1/auths/signin',json={'email':'admin@localhost','password':'admin'})
    code='''from pathlib import Path
import socket
assert Path("sandbox-verification.txt").read_text() == "Sandbox persisted correctly"
assert not Path("/project").exists()
try:
    Path("/etc/sandbox-write-test").write_text("test")
except OSError:
    print("ROOT_READ_ONLY")
else:
    raise AssertionError("Root filesystem is writable")
try:
    socket.create_connection(("1.1.1.1",443),timeout=3)
except OSError:
    print("EGRESS_BLOCKED")
else:
    raise AssertionError("Sandbox has internet egress")
'''
    data=call('POST','http://open-webui:8080/api/v1/utils/code/execute',headers={'Authorization':'Bearer '+auth['token']},json={'code':code})
    assert_true('ROOT_READ_ONLY' in data.get('stdout','') and 'EGRESS_BLOCKED' in data.get('stdout','') and not data.get('stderr'),'Sandbox boundary check failed')
    return data
def index_lifecycle():
    path=Path('/workspace/index-lifecycle-verification.txt')
    try:
        path.write_text('The indexing lifecycle sentinel is amber-lantern-9351.')
        call('POST','http://workspace-api:8000/index',timeout=600)
        data=call('POST','http://workspace-api:8000/search',json={'query':'amber-lantern-9351 indexing lifecycle sentinel','limit':5})
        assert_true(any(p['path']=='workspace/'+path.name for p in data['results']),'New file was not indexed')
        path.unlink()
        call('POST','http://workspace-api:8000/index',timeout=600)
        data=call('POST','http://workspace-api:8000/search',json={'query':'amber-lantern-9351 indexing lifecycle sentinel','limit':5})
        assert_true(all(p['path']!='workspace/'+path.name for p in data['results']),'Deleted file remained indexed')
        return 'Create and deletion propagated to Qdrant'
    finally:
        path.unlink(missing_ok=True)
test('open_webui',ui)
test('ollama',lambda:call('GET',OLLAMA+'/api/version'))
test('qdrant',lambda:call('GET','http://qdrant:6333/collections'))
test('qwen_extended_context',lambda:extended_context('local-qwen:27b-32k'))
test('dolphin_extended_context',lambda:extended_context('local-dolphin:24b-32k'))
test('qwen_stream',lambda:inference('local-qwen:27b'))
test('dolphin_stream',lambda:inference('local-dolphin:24b'))
test('switch_back_qwen',lambda:inference('local-qwen:27b'))
test('live_web_search',search)
test('webui_search_and_embedding',webui_search)
test('javascript_crawl',crawl)
test('sandbox_execution_through_webui',sandbox)
test('sandbox_isolation_and_persistence',sandbox_boundaries)
test('workspace_vector_retrieval',retrieval)
test('index_create_delete_lifecycle',index_lifecycle)
test('model_rag_answer',rag_answer)
test('mcp_handshake',mcp)
test('qwen_vision',vision)
test('qwen_native_tool_roundtrip',native_tools)
test('qwen_generated_code_execution',lambda:generated_code('local-qwen:27b'))
test('dolphin_generated_code_execution',lambda:generated_code('local-dolphin:24b'))
test('javascript_rendered_content',js_render)
test('web_search_crawl_model_answer',live_context_answer)
test('webui_openapi_tool_roundtrip',lambda:webui_tool_roundtrip('server:workspace'))
test('webui_mcp_tool_roundtrip',lambda:webui_tool_roundtrip('server:mcp:workspace-mcp'))
test('dolphin_webui_tool_roundtrip',lambda:webui_tool_roundtrip('server:workspace','local-dolphin:24b'))
REPORT['passed']=all(x['pass'] for x in REPORT['tests'].values())
REPORT['completed_at']=time.time()
Path('/state/verification-selected.json' if selected and not args.retry_failed else '/state/verification.json').write_text(json.dumps(REPORT,indent=2))
print(json.dumps(REPORT,indent=2))
raise SystemExit(0 if REPORT['passed'] else 1)
