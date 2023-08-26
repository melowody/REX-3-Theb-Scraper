import websocket
import json


class SocketBased:
    
    def __init__(self, socket: websocket.WebSocket):
        self.socket = socket
    
    def send_json_request(self, request):
        self.socket.send(json.dumps(request))

    def receive_json_response(self):
        response = self.socket.recv()
        if response:
            return json.loads(response)
