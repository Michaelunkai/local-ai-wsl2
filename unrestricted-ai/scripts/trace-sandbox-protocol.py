"""Diagnostic subclass of the installed WebUI executor; no production patch.

Run in the open-webui container. Records only protocol metadata for fixed test code.
"""
import asyncio
import json
import os
from pathlib import Path
import time
from open_webui.utils.code_interpreter import JupyterCodeExecuter


class TraceExecutor(JupyterCodeExecuter):
    def __init__(self, index):
        super().__init__(os.environ['CODE_EXECUTION_JUPYTER_URL'],
                         'from pathlib import Path\nprint(sum(i*i for i in range(10)))\n'
                         f'Path("sandbox-protocol-{index}.txt").write_text("trace complete")',
                         token=os.environ['CODE_EXECUTION_JUPYTER_AUTH_TOKEN'])
        self.started=time.monotonic()
        self.events=[]

    def event(self, kind, **values):
        self.events.append({'seconds':round(time.monotonic()-self.started,4),'event':kind,**values})

    async def init_kernel(self):
        self.event('create_kernel_start')
        await super().init_kernel()
        self.event('create_kernel_finished')

    async def execute_in_jupyter(self, ws):
        self.event('websocket_connected')
        owner=self
        class TraceSocket:
            async def send(self, value):
                message=json.loads(value)
                self.request_id=message['header']['msg_id']
                owner.event('send',message_type=message['header']['msg_type'])
                await ws.send(value)

            async def recv(self):
                value=await ws.recv()
                message=json.loads(value)
                owner.event('receive',message_type=message.get('msg_type'),
                            channel=message.get('channel'),
                            matches_request=message.get('parent_header',{}).get('msg_id')==self.request_id,
                            execution_state=message.get('content',{}).get('execution_state'))
                return value
        await super().execute_in_jupyter(TraceSocket())


async def check(index):
    async with TraceExecutor(index) as executor:
        result=await executor.run()
        executor.event('execution_returned')
        report={'index':index,'result':result.model_dump(),'events':executor.events,
                'passed':result.stdout=='285' and not result.stderr}
    executor.event('kernel_cleanup_finished')
    return report


async def main():
    report={'started':time.time(),'runs':await asyncio.gather(*(check(i) for i in range(3)))}
    report['passed']=all(run['passed'] for run in report['runs'])
    Path('/app/backend/data/sandbox-protocol-trace.json').write_text(json.dumps(report,indent=2))
    for run in report['runs']:
        print(json.dumps(run),flush=True)
    if not report['passed']:raise SystemExit(1)

asyncio.run(main())
