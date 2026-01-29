import subprocess
import sys
import os
import time
import grpc
import atexit
# We will fix imports in the proto files to be relative, so we can import them here
# assuming we are inside the package.
from .api.v1 import core_pb2, core_pb2_grpc

class SwanLabClient:
    def __init__(self):
        self.proc = None
        self.stub = None
        self.channel = None
        self._start_backend()
        atexit.register(self._cleanup)

    def _start_backend(self):
        # Path to the logic binary, relative to this file
        # structure: swanlab_core/client.py -> bin/core
        base_dir = os.path.dirname(os.path.abspath(__file__))
        go_binary = os.path.join(base_dir, "bin", "core")

        if not os.path.exists(go_binary):
            raise FileNotFoundError(f"Go binary not found at {go_binary}")

        # Start Go process
        self.proc = subprocess.Popen(
            [go_binary],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True
        )

        try:
            # Read port
            port_line = self.proc.stdout.readline()
            if not port_line:
                raise RuntimeError("Go backend failed to start (no port output)")
            
            port = port_line.strip()
            # print(f"[SwanLab] Backend started on port {port}")

            # Connect gRPC
            target = f"localhost:{port}"
            self.channel = grpc.insecure_channel(target)
            self.stub = core_pb2_grpc.CoreServiceStub(self.channel)
        
        except Exception:
            self._cleanup()
            raise

    def log(self, key: str, value: float):
        if not self.stub:
            raise RuntimeError("SwanLab client not connected")

        # Create record
        # In a real app, handle types, timestamps, etc.
        record = core_pb2.ScalarRecord(
            index="0", # TODO: counters
            epoch="0",
            create_time=str(time.time()),
            key=key,
            data=[value]
        )
        
        self.stub.LogScalar(record)

    def _cleanup(self):
        if self.proc:
            # Closing stdin triggers the Go watchdog
            if self.proc.stdin:
                self.proc.stdin.close()
            # Wait for exit
            self.proc.wait(timeout=2)
            if self.proc.poll() is None:
                self.proc.kill()
            self.proc = None
            self.channel.close()

