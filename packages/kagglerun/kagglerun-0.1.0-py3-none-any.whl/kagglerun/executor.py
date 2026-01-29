"""
KaggleRun Core Executor

Execute Python code on Kaggle Jupyter kernels via REST API + WebSocket.
Supports real-time output streaming, file operations, and GPU detection.
"""

import json
import ssl
import time
import uuid
import base64
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from urllib.parse import urlparse

try:
    import requests
    import websocket
except ImportError as e:
    raise ImportError(
        "Required dependencies not found. Install with: pip install kagglerun"
    ) from e


class KaggleExecutor:
    """
    Execute Python code on Kaggle's free GPU kernels.

    Usage:
        executor = KaggleExecutor("https://your-kaggle-jupyter-url/proxy")
        result = executor.execute("print('Hello from H100!')")
        print(result['output_text'])

    Features:
        - Real-time output streaming via WebSocket
        - Automatic kernel state management (interrupt busy kernels)
        - File upload/download to /kaggle/working/
        - GPU detection and info
    """

    def __init__(
        self,
        base_url: str,
        verbose: bool = True,
        timeout: int = 120,
        on_output: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize KaggleExecutor.

        Args:
            base_url: Kaggle Jupyter proxy URL (from VS Code Server URL)
            verbose: Print status messages (default: True)
            timeout: Default execution timeout in seconds (default: 120)
            on_output: Optional callback for real-time output streaming
        """
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.default_timeout = timeout
        self.on_output = on_output
        self.kernel_id: Optional[str] = None
        self._session = requests.Session()

        # Disable websocket trace
        websocket.enableTrace(False)

    def _log(self, msg: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] {msg}")

    def test_connection(self) -> bool:
        """
        Test connectivity to Kaggle Jupyter API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            r = self._session.get(f"{self.base_url}/api", timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    def get_kernel_state(self, kernel_id: Optional[str] = None) -> str:
        """
        Get current kernel execution state.

        Args:
            kernel_id: Kernel ID (uses cached if not provided)

        Returns:
            Kernel state: 'idle', 'busy', or 'unknown'
        """
        kid = kernel_id or self.kernel_id
        if not kid:
            return 'unknown'
        try:
            r = self._session.get(f"{self.base_url}/api/kernels/{kid}", timeout=10)
            if r.status_code == 200:
                return r.json().get('execution_state', 'unknown')
        except Exception:
            pass
        return 'unknown'

    def wait_for_idle(self, timeout: int = 60) -> bool:
        """
        Wait for kernel to become idle.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if kernel became idle, False if timeout
        """
        if not self.kernel_id:
            return False

        self._log("Waiting for kernel to become idle...")
        start = time.time()
        while time.time() - start < timeout:
            state = self.get_kernel_state()
            if state == 'idle':
                self._log("Kernel is idle")
                return True
            self._log(f"Kernel state: {state}")
            time.sleep(2)
        return False

    def get_or_create_kernel(self) -> Optional[str]:
        """
        Get existing kernel or create a new one.

        Returns:
            Kernel ID or None if failed
        """
        # Try to use existing kernel
        try:
            r = self._session.get(f"{self.base_url}/api/kernels", timeout=10)
            if r.status_code == 200:
                kernels = r.json()
                if kernels:
                    self.kernel_id = kernels[0]['id']
                    self._log(f"Using existing kernel: {self.kernel_id[:8]}...")
                    return self.kernel_id
        except Exception as e:
            self._log(f"Error listing kernels: {e}")

        # Create new kernel
        try:
            r = self._session.post(
                f"{self.base_url}/api/kernels",
                json={"name": "python3"},
                timeout=30
            )
            if r.status_code in [200, 201]:
                self.kernel_id = r.json()['id']
                self._log(f"Created kernel: {self.kernel_id[:8]}...")
                return self.kernel_id
        except Exception as e:
            self._log(f"Error creating kernel: {e}")

        return None

    def interrupt_kernel(self) -> bool:
        """
        Interrupt current kernel execution.

        Returns:
            True if interrupt successful
        """
        if not self.kernel_id:
            return False
        try:
            r = self._session.post(
                f"{self.base_url}/api/kernels/{self.kernel_id}/interrupt",
                timeout=10
            )
            return r.status_code in [200, 204]
        except Exception:
            return False

    def execute(
        self,
        code: str,
        timeout: Optional[int] = None,
        wait_idle: bool = True
    ) -> Dict[str, Any]:
        """
        Execute Python code on Kaggle kernel.

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds (uses default if not set)
            wait_idle: Wait for kernel to be idle before executing

        Returns:
            Dict with keys:
                - success: bool
                - outputs: list of output strings
                - output_text: concatenated output
                - errors: list of error messages
                - execution_time: float (seconds)
        """
        timeout = timeout or self.default_timeout
        result = {
            "success": False,
            "outputs": [],
            "output_text": "",
            "errors": [],
            "execution_time": 0.0
        }

        start_time = time.time()

        # Ensure we have a kernel
        if not self.kernel_id:
            self.kernel_id = self.get_or_create_kernel()
        if not self.kernel_id:
            result["errors"].append("Failed to get or create kernel")
            return result

        # Handle busy kernel
        if wait_idle:
            state = self.get_kernel_state()
            if state == 'busy':
                self._log("Kernel is busy, interrupting...")
                self.interrupt_kernel()
                time.sleep(2)
            if not self.wait_for_idle(timeout=30):
                self._log("Warning: Kernel not idle, proceeding anyway")

        # Build WebSocket URL
        ws_url = self.base_url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_url}/api/kernels/{self.kernel_id}/channels"

        try:
            ws = websocket.create_connection(
                ws_url,
                sslopt={"cert_reqs": ssl.CERT_NONE},
                timeout=10
            )
            self._log("WebSocket connected")

            # Build execute message
            msg_id = str(uuid.uuid4())
            session_id = str(uuid.uuid4())

            execute_msg = {
                "header": {
                    "msg_id": msg_id,
                    "msg_type": "execute_request",
                    "username": "kagglerun",
                    "session": session_id,
                    "version": "5.3",
                    "date": datetime.now().astimezone().isoformat()
                },
                "parent_header": {},
                "metadata": {},
                "content": {
                    "code": code,
                    "silent": False,
                    "store_history": True,
                    "user_expressions": {},
                    "allow_stdin": False,
                    "stop_on_error": True
                },
                "channel": "shell"
            }

            ws.send(json.dumps(execute_msg))
            self._log(f"Executing code ({len(code)} chars)...")

            # Collect responses
            exec_start = time.time()
            idle_received = False

            while time.time() - exec_start < timeout:
                try:
                    ws.settimeout(1.0)
                    raw = ws.recv()
                    msg = json.loads(raw)
                    msg_type = msg.get("msg_type", "")
                    parent_id = msg.get("parent_header", {}).get("msg_id", "")

                    # Only process messages for our request
                    if parent_id and parent_id != msg_id:
                        continue

                    if msg_type == "stream":
                        text = msg["content"]["text"]
                        result["outputs"].append(text)
                        if self.on_output:
                            self.on_output(text)
                        elif self.verbose:
                            print(text, end='', flush=True)

                    elif msg_type == "execute_result":
                        data = msg["content"]["data"].get("text/plain", "")
                        result["outputs"].append(data)
                        if self.on_output:
                            self.on_output(data)
                        elif self.verbose:
                            print(data)

                    elif msg_type == "display_data":
                        data = msg["content"]["data"]
                        if "text/plain" in data:
                            result["outputs"].append(data["text/plain"])
                        if "image/png" in data:
                            result["outputs"].append("[IMAGE: base64 PNG]")

                    elif msg_type == "error":
                        ename = msg['content']['ename']
                        evalue = msg['content']['evalue']
                        err = f"{ename}: {evalue}"
                        result["errors"].append(err)
                        self._log(f"Error: {err}")

                    elif msg_type == "status":
                        state = msg["content"]["execution_state"]
                        if state == "idle":
                            idle_received = True
                            break

                except websocket.WebSocketTimeoutException:
                    continue
                except Exception as e:
                    self._log(f"WebSocket error: {e}")
                    break

            ws.close()

            result["success"] = idle_received and len(result["errors"]) == 0
            result["output_text"] = "".join(result["outputs"])
            result["execution_time"] = time.time() - start_time

        except Exception as e:
            result["errors"].append(str(e))
            self._log(f"Execution failed: {e}")

        return result

    def run_file(self, filepath: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a local Python file on Kaggle.

        Args:
            filepath: Path to local .py file
            timeout: Execution timeout

        Returns:
            Execution result dict
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            return self.execute(code, timeout)
        except Exception as e:
            return {"success": False, "errors": [str(e)], "outputs": [], "output_text": ""}

    def upload_file(self, local_path: str, remote_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a local file to /kaggle/working/.

        Args:
            local_path: Path to local file
            remote_name: Name on remote (uses local filename if not set)

        Returns:
            Execution result dict
        """
        import os
        if remote_name is None:
            remote_name = os.path.basename(local_path)

        with open(local_path, 'rb') as f:
            content = f.read()

        b64_content = base64.b64encode(content).decode()

        code = f'''
import base64
content = base64.b64decode('{b64_content}')
with open('/kaggle/working/{remote_name}', 'wb') as f:
    f.write(content)
import os
size = os.path.getsize('/kaggle/working/{remote_name}')
print(f"Uploaded: /kaggle/working/{remote_name} ({{size}} bytes)")
'''
        return self.execute(code)

    def save_text(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Save text content to /kaggle/working/.

        Args:
            filename: Name of file to create
            content: Text content

        Returns:
            Execution result dict
        """
        b64_content = base64.b64encode(content.encode()).decode()
        code = f'''
import base64
content = base64.b64decode('{b64_content}').decode()
with open('/kaggle/working/{filename}', 'w') as f:
    f.write(content)
import os
print(f"Saved: /kaggle/working/{filename} ({{os.path.getsize('/kaggle/working/{filename}')}} bytes)")
'''
        return self.execute(code)

    def read_file(self, remote_path: str) -> Dict[str, Any]:
        """
        Read a text file from remote.

        Args:
            remote_path: Full path or filename in /kaggle/working/

        Returns:
            Execution result with file content in output_text
        """
        if not remote_path.startswith('/'):
            remote_path = f'/kaggle/working/{remote_path}'
        code = f"print(open('{remote_path}').read())"
        return self.execute(code)

    def download_file(self, remote_path: str) -> Optional[bytes]:
        """
        Download a file from remote as bytes.

        Args:
            remote_path: Full path or filename in /kaggle/working/

        Returns:
            File content as bytes, or None if failed
        """
        if not remote_path.startswith('/'):
            remote_path = f'/kaggle/working/{remote_path}'

        code = f'''
import base64
with open('{remote_path}', 'rb') as f:
    print(base64.b64encode(f.read()).decode())
'''
        result = self.execute(code)
        if result["success"] and result["outputs"]:
            try:
                return base64.b64decode(result["outputs"][0].strip())
            except Exception:
                pass
        return None

    def list_files(self, path: str = "/kaggle/working/") -> Dict[str, Any]:
        """
        List files in a directory.

        Args:
            path: Directory path (default: /kaggle/working/)

        Returns:
            Execution result with file listing
        """
        code = f'''
import os
print("Contents of {path}:")
for item in sorted(os.listdir('{path}')):
    full = os.path.join('{path}', item)
    if os.path.isfile(full):
        size = os.path.getsize(full)
        print(f"  FILE: {{item}} ({{size}} bytes)")
    else:
        print(f"  DIR:  {{item}}/")
'''
        return self.execute(code)

    def get_gpu_info(self) -> Dict[str, Any]:
        """
        Get GPU information from the remote kernel.

        Returns:
            Execution result with GPU info
        """
        code = '''
import subprocess
try:
    out = subprocess.check_output(
        ['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'],
        text=True
    )
    print(f"GPU: {out.strip()}")
except Exception as e:
    print(f"No GPU available: {e}")
'''
        return self.execute(code)

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information from the remote kernel.

        Returns:
            Execution result with system info
        """
        code = '''
import sys
import platform
import os

print(f"Python: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"CPU Count: {os.cpu_count()}")

try:
    import torch
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA Device: {torch.cuda.get_device_name(0)}")
except ImportError:
    print("PyTorch: Not installed")
'''
        return self.execute(code)


def connect(url: str, **kwargs) -> KaggleExecutor:
    """
    Convenience function to create a KaggleExecutor.

    Args:
        url: Kaggle Jupyter proxy URL
        **kwargs: Additional arguments for KaggleExecutor

    Returns:
        Connected KaggleExecutor instance
    """
    executor = KaggleExecutor(url, **kwargs)
    if not executor.test_connection():
        raise ConnectionError(f"Failed to connect to {url}")
    return executor
