import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect 
from fastapi.responses import HTMLResponse

app = FastAPI(docs_url=None,
    redoc_url=None,)

candidates = ["Balen Shah", "KP Oli", "Prachanda", "Ramesh", "Sita"]
votes = [0] * len(candidates)
connected: set[WebSocket] = set()
voted: set[WebSocket] = set()


async def broadcast_votes():
    data = json.dumps({"type": "votes", "data": votes})
    disconnected = []
    for ws in connected:
        try:
            await ws.send_text(data)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        connected.discard(ws)
        voted.discard(ws)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected.add(websocket)
    await websocket.send_text(json.dumps({"type": "votes", "data": votes}))

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if msg.get("type") == "vote" and websocket not in voted:
                idx = msg.get("candidate", -1)
                if 0 <= idx < len(candidates):
                    votes[idx] += 1
                    voted.add(websocket)
                    await broadcast_votes()
            elif msg.get("type") == "vote" and websocket in voted:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Already voted"})
                )

    except WebSocketDisconnect:
        pass
    finally:
        connected.discard(websocket)
        voted.discard(websocket)


@app.get("/")
def root():
    return {"candidates": candidates, "votes": votes}

@app.get("/hi/")
def poke_me():
    return {"response":"yo"}