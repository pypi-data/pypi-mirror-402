import websocket

def connect_progress_ws(address):
    ws = websocket.WebSocket()
    ws.connect(address)
    return ws

def wrap_ws_progress(ws):
    prev = 0
    while ws.connected:
        try:
            current = int(ws.recv())
            yield current - prev
            prev = current
        except websocket.WebSocketConnectionClosedException:
            return

class PyntProgress():
    def __init__(self, address, healthcheck, total, description) -> None:
        self.running = False
        self.trackable = PyntProgress.create_trackable(address, healthcheck)
        self.total = total
        self.description = description

    @staticmethod
    def create_trackable(address, healthcheck):
        try: 
            healthcheck()
            return wrap_ws_progress(connect_progress_ws(address))
        except TimeoutError:
            return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.running = False


