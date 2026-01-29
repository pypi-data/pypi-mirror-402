import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from guirecognizerapp.call_manager import CallManager


def createApp() -> FastAPI:
  app = FastAPI()
  connectionManager = None

  @app.websocket("/ws")
  async def websocket_endpoint(websocket: WebSocket):
    nonlocal connectionManager

    if connectionManager is None:
      connectionManager = ConnectionManager()
    callManager = await connectionManager.connect(websocket)
    try:
      while True:
        rawData = await websocket.receive_text()
        asyncio.create_task(callManager.manageData(rawData))
    except WebSocketDisconnect:
      pass
    finally:
      connectionManager.disconnect(callManager)

  return app

class ConnectionManager:
  def __init__(self):
    self.appname = 'guirecognizerapp'
    self.activeConnections: list[WebSocket] = []
    self.callManagers: list[CallManager] = []

  async def connect(self, websocket: WebSocket) -> CallManager:
    await websocket.accept()
    self.activeConnections.append(websocket)
    callManager = CallManager(self.appname, websocket)
    self.callManagers.append(callManager)
    return callManager

  def disconnect(self, callManager: CallManager) -> None:
    callManager.remove()
    self.activeConnections.remove(callManager.websocket)
    self.callManagers.remove(callManager)
