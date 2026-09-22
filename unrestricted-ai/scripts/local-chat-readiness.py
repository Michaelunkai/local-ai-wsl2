"""
title: Local model readiness
author: Local workspace
version: 1.0.0
description: Show loading progress before a local model's first reply.
"""
import asyncio
import time
import aiohttp


class Filter:
    async def inlet(self, body: dict, __event_emitter__=None, __metadata__=None) -> dict:
        model = body.get('model', '')
        if not model.startswith(('local-qwen:', 'local-dolphin:')):
            return body
        if (__metadata__ or {}).get('task'):
            return body
        # Use the sandbox tool instead of Dolphin's recursive legacy XML prompt.
        if model.startswith('local-dolphin:'):
            body.setdefault('features', {})['code_interpreter'] = False
        url = 'http://host.docker.internal:11434'
        timeout = aiohttp.ClientTimeout(total=900)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url + '/api/ps') as response:
                response.raise_for_status()
                resident = (await response.json()).get('models', [])
            if any(item['name'] == model for item in resident):
                return body
            label = 'Qwen' if 'qwen' in model else 'Dolphin'
            started = time.monotonic()

            async def status(done=False, error=False):
                if __event_emitter__:
                    description = (f'{label} is ready' if done and not error else
                                   f'Loading {label} from local storage — {int(time.monotonic()-started)}s. Please wait; switching large models can take a few minutes.')
                    if error:
                        description = f'{label} could not load. Please retry; see the local Ollama log for details.'
                    await __event_emitter__({'type': 'status', 'data': {
                        'description': description, 'done': done, 'error': error}})

            async def preload():
                async with session.post(url + '/api/generate', json={
                    'model': model, 'prompt': '', 'stream': False, 'keep_alive': -1
                }) as response:
                    response.raise_for_status()
                    result = await response.json()
                    if result.get('error'):
                        raise RuntimeError(result['error'])

            await status()
            loading = asyncio.create_task(preload())
            try:
                while not loading.done():
                    await asyncio.wait({loading}, timeout=5)
                    if not loading.done():
                        await status()
                await loading
                await status(done=True)
            except BaseException:
                loading.cancel()
                await asyncio.gather(loading, return_exceptions=True)
                await status(done=True, error=True)
                raise
        return body
