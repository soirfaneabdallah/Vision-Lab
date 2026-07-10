# core/remote_camera.py
import asyncio
import threading
import queue
import socket
import numpy as np
import cv2
from aiohttp import web, WSMsgType


class RemoteCameraServer:
    def __init__(self, host="0.0.0.0", port=5001):
        self.host = host
        self.port = port
        self.frame_queue = queue.Queue(maxsize=10)
        self.latest_frame = None
        self.is_running = False
        self.thread = None
        self.loop = None
        self.runner = None

    def _get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
        except:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def start(self):
        if self.is_running:
            self.stop()
            # Laisser le temps au port de se libérer
            import time
            time.sleep(0.5)
        self.is_running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()

    def _run_server(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        app = web.Application()
        app.router.add_get("/", self.handle_index)
        app.router.add_get("/ws", self.handle_websocket)
        self.runner = web.AppRunner(app)
        self.loop.run_until_complete(self.runner.setup())
        site = web.TCPSite(self.runner, self.host, self.port)
        try:
            self.loop.run_until_complete(site.start())
            print(f"📱 Serveur caméra sur http://{self._get_local_ip()}:{self.port}")
            self.loop.run_forever()
        except Exception as e:
            print(f"❌ Erreur serveur : {e}")
            self.is_running = False

    async def handle_index(self, request):
        html = """
        <!DOCTYPE html>
        <html>
        <head><meta name="viewport" content="width=device-width,initial-scale=1">
        <title>FishID Camera</title>
        <style>body{margin:0;display:flex;justify-content:center;align-items:center;min-height:100vh;background:#000;}
        video{max-width:100%;max-height:100vh;display:none;}</style>
        </head>
        <body>
        <video id="video" autoplay playsinline></video>
        <script>
        const socket = new WebSocket('ws://' + location.host + '/ws');
        socket.binaryType = 'arraybuffer';
        const video = document.getElementById('video');
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        let streaming = false;

        async function startCamera() {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
          });
          video.srcObject = stream;
          video.play();
          video.addEventListener('loadedmetadata', () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            streaming = true;
            sendFrame();
          });
        }

        function sendFrame() {
          if (!streaming) return;
          ctx.drawImage(video, 0, 0);
          canvas.toBlob(blob => {
            if (blob && socket.readyState === WebSocket.OPEN) {
              socket.send(blob);
            }
          }, 'image/jpeg', 0.9);
          requestAnimationFrame(sendFrame);
        }

        socket.onopen = () => startCamera().catch(alert);
        </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')

    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        async for msg in ws:
            if msg.type == WSMsgType.BINARY:
                try:
                    nparr = np.frombuffer(msg.data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        if self.frame_queue.full():
                            try:
                                self.frame_queue.get_nowait()
                            except queue.Empty:
                                pass
                        self.frame_queue.put_nowait(frame)
                        self.latest_frame = frame
                except:
                    pass
            elif msg.type == WSMsgType.ERROR:
                break
        return ws

    def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        if self.loop and self.runner:
            self.loop.call_soon_threadsafe(self.loop.stop)
            if self.thread:
                self.thread.join(timeout=3)
        self.loop = None
        self.runner = None
        self.thread = None
        print("📱 Serveur caméra arrêté")

    def get_frame(self):
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return self.latest_frame