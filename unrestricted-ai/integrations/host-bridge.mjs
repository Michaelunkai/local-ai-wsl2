// Authenticated Windows-side, on-demand MCP dispatcher. No public listener.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { integrationRevision } from './integration-revision.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
const token=fs.readFileSync(path.join(root,'bridge.key'),'utf8').trim();
const revision=integrationRevision(root);
const clients=new Map();
const definitions={
  memory:{entry:'@modelcontextprotocol/server-memory/dist/index.js',args:[],description:'Persistent local knowledge graph: store and retrieve user-requested facts, entities and relations across chats'},
  windows_ui:{command:path.join(root,'bin','windows-mcp.exe'),args:['serve','--config',path.join(root,'windows-ui.toml')],description:'Windows UI accessibility, screenshots, clicking, typing, scrolling and application control'},
  desktop:{entry:'@wonderwhy-er/desktop-commander/dist/index.js',args:[],description:'Windows files, folders, document editing, terminal commands and process management'},
  browser:{entry:'@playwright/mcp/cli.js',args:['--extension'],description:'Existing Chrome or Edge tabs using the official Playwright extension; requires extension installation and browser connection'},
  research_browser:{entry:'@playwright/mcp/cli.js',args:['--browser','chrome','--headless','--user-data-dir',path.join(root,'research-profile')],description:'Independent browser for public research and web interactions; does not share existing browser sessions'}
};
async function client(name){
  if(!definitions[name])throw Error('Unknown integration');
  if(!clients.has(name)){
    let pending;
    pending=(async()=>{
      const def=definitions[name];
      const profile=path.join(root,'profiles',name); fs.mkdirSync(profile,{recursive:true});
      const transport=new StdioClientTransport({command:def.command||process.execPath,args:def.command?def.args:[path.join(root,'node_modules',def.entry),...def.args],stderr:'inherit',env:{...process.env,MEMORY_FILE_PATH:path.join(profile,'knowledge.jsonl'),DESKTOP_COMMANDER_CONFIG_DIR:path.join(profile,'.claude-server-commander'),DESKTOP_COMMANDER_DISABLE_TELEMETRY:'1',POSTHOG_API_KEY:'',DO_NOT_TRACK:'1',ANONYMIZED_TELEMETRY:'false'}});
      const c=new Client({name:'Local AI Windows bridge',version:'1.0.0'});
      c.onclose=()=>{if(clients.get(name)===pending)clients.delete(name);};
      try {await c.connect(transport);} catch(error) {await transport.close().catch(()=>{});throw error;}
      return c;
    })();
    clients.set(name,pending); pending.catch(()=>{if(clients.get(name)===pending)clients.delete(name);});
  }
  return clients.get(name);
}
function authorized(req){
  const supplied=Buffer.from(req.headers.authorization||''); const expected=Buffer.from('Bearer '+token);
  return supplied.length===expected.length && crypto.timingSafeEqual(supplied,expected);
}
http.createServer(async(req,res)=>{
  res.setHeader('Content-Type','application/json');
  const send=(status,value)=>{res.writeHead(status);res.end(JSON.stringify(value));};
  if(!authorized(req))return send(401,{error:'Authentication required'});
  if(req.method==='GET'&&req.url==='/health')return send(200,{status:'ok',pid:process.pid,revision,integrations:definitions});
  if(req.method!=='POST')return send(404,{error:'Not found'});
  try{
    let text=''; for await(const chunk of req){text+=chunk;if(Buffer.byteLength(text)>1000000)throw Error('Request too large');}
    const body=JSON.parse(text); const c=await client(body.integration);
    if(req.url==='/tools'){
      const result=await c.listTools();
      if(body.tool){
        const selected=result.tools.find(t=>t.name===body.tool);
        if(!selected)throw Error('Unknown tool; discover the integration catalog first');
        return send(200,{tools:[selected]});
      }
      return send(200,{tools:result.tools.map(t=>({name:t.name,description:(t.description||'').trim().slice(0,180)})),next:'Request the selected tool_name to obtain its complete inputSchema before calling it.'});
    }
    if(req.url==='/call'){
      const result=await c.callTool({name:body.tool,arguments:body.arguments||{}},undefined,{timeout:180000});
      fs.appendFileSync(path.join(root,'..','logs','host-tools.jsonl'),JSON.stringify({time:new Date().toISOString(),integration:body.integration,tool:body.tool,isError:!!result.isError})+'\n');
      return send(200,result);
    }
    return send(404,{error:'Not found'});
  }catch(e){send(502,{error:e.message});}
}).listen(19381,'127.0.0.1');
