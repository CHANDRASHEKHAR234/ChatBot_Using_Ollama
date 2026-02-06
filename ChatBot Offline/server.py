# server.py
# Chatbot backend using Ollama Qwen via HTTP API
# pip install websockets requests

import asyncio
import json
import requests
from websockets import serve

HOST = "0.0.0.0"
PORT = 8765
MODEL_NAME ="qwen2.5:latest"   # make sure you have pulled it: ollama pull qwen
OLLAMA_URL = "http://localhost:11434/api/generate"

def call_ollama(prompt: str) -> str:
    """Send a prompt to Ollama and return response text."""
    try:
        payload = {"model": MODEL_NAME, "prompt": prompt}
        r = requests.post(OLLAMA_URL, json=payload, stream=True)
        reply = ""
        for line in r.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    reply += data["response"]
        return reply.strip() if reply else "[No response from Ollama]"
    except Exception as e:
        return f"[LLM ERROR: {e}]"

async def handle_ws(websocket):
    await websocket.send(json.dumps({"type": "system", "text": f"Connected to chatbot (model={MODEL_NAME})."}))
    async for msg in websocket:
        try:
            data = json.loads(msg)
        except:
            data = {"type": "message", "text": msg}

        if data.get("type") == "message":
            user_text = data.get("text", "")
            await websocket.send(json.dumps({"type": "user", "text": user_text}))

            loop = asyncio.get_event_loop()
            reply = await loop.run_in_executor(None, call_ollama, user_text)

            await websocket.send(json.dumps({"type": "assistant", "text": reply}))
        else:
            await websocket.send(json.dumps({"type": "system", "text": "Unrecognized message type."}))

async def main():
    print(f"🚀 WebSocket server running at ws://{HOST}:{PORT}")
    async with serve(handle_ws, HOST, PORT):
        await asyncio.Future()  # keep running

if __name__ == "__main__":
    asyncio.run(main())
