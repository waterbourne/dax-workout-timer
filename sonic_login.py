#!/usr/bin/env python3
import asyncio
import websockets
import json

async def interact_with_page():
    uri = "ws://127.0.0.1:18800/devtools/page/9EA4EF9879721C744CC08AF53D6D44B1"
    
    async with websockets.connect(uri) as ws:
        # Enable Runtime
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.recv()
        
        # Evaluate JavaScript to find form fields
        js_code = """
            (function() {
                const inputs = document.querySelectorAll('input');
                const result = [];
                inputs.forEach((input, i) => {
                    result.push({
                        index: i,
                        type: input.type,
                        name: input.name,
                        id: input.id,
                        placeholder: input.placeholder
                    });
                });
                return result;
            })()
        """
        
        await ws.send(json.dumps({
            "id": 2,
            "method": "Runtime.evaluate",
            "params": {
                "expression": js_code,
                "returnByValue": True
            }
        }))
        response = await ws.recv()
        print("Inputs found:", response)

asyncio.run(interact_with_page())
