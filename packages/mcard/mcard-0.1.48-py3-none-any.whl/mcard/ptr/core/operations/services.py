"""
Services Operations Module
==========================

Contains operations for managing long-running services (servers, daemons).
Moved from builtins.py to separate concerns.
"""

from typing import Any
from mcard import MCard

def op_static_server(impl: dict, target: MCard, ctx: dict) -> Any:
    """
    Execute static_server builtin - manages HTTP static file server.

    Actions: deploy, status, stop
    Config: root_dir, port, host
    """
    import os
    import signal
    import socket
    import subprocess
    import time

    def _resolve_config_value(val: Any) -> Any:
        """Resolve environment variables in config values like '${VAR}'."""
        if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
            env_var = val[2:-1]
            return os.getenv(env_var, val)
        return val

    # Valid config keys: port, host, root_dir
    config = impl.get("config", {})
    action = ctx.get("action") or config.get("action", "status")
    
    # Default to HTTP_PORT from .env matching the project configuration
    default_port = int(os.getenv("HTTP_PORT", 5320))
    raw_port = ctx.get("port") or config.get("port", default_port)
    port = int(_resolve_config_value(raw_port))
    
    host = ctx.get("host") or config.get("host", "localhost")
    root_dir = ctx.get("root_dir") or config.get("root_dir", ".")

    # Resolve root_dir relative to project root
    project_root = os.getcwd()
    if not os.path.isabs(root_dir):
        root_dir = os.path.normpath(os.path.join(project_root, root_dir))

    pid_file = os.path.join(project_root, f".static_server_{port}.pid")

    def is_port_in_use(p: int) -> bool:
        # Use lsof to check if port is in use (handles both IPv4 and IPv6)
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{p}"], capture_output=True, text=True
            )
            return result.returncode == 0 and result.stdout.strip() != ""
        except Exception:
            # Fallback to socket check
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", p)) == 0

    def get_pid_on_port(p: int):
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{p}"], capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().split("\n")[0])
        except Exception:
            pass
        return None

    if action == "deploy":
        # Check if already running
        if is_port_in_use(port):
            pid = get_pid_on_port(port)
            return {
                "success": True,
                "message": "Server already running",
                "pid": pid,
                "port": port,
                "url": f"http://{host}:{port}",
                "status": "already_running",
            }

        # Verify root_dir exists
        if not os.path.isdir(root_dir):
            return {"success": False, "error": f"Directory not found: {root_dir}"}

        # Start Python HTTP server as background process
        try:
            process = subprocess.Popen(
                [
                    "python3",
                    "-m",
                    "http.server",
                    str(port),
                    "--bind",
                    host,
                    "--directory",
                    root_dir,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            # Save PID
            with open(pid_file, "w") as f:
                f.write(str(process.pid))

            # Wait for server to start
            time.sleep(1.0)

            if is_port_in_use(port):
                return {
                    "success": True,
                    "message": "Server deployed successfully",
                    "pid": process.pid,
                    "port": port,
                    "url": f"http://{host}:{port}",
                    "root_dir": root_dir,
                    "status": "running",
                }
            else:
                return {"success": False, "error": "Server started but not responding"}

        except Exception as e:
            return {"success": False, "error": f"Failed to start server: {e}"}

    elif action == "status":
        is_running = is_port_in_use(port)
        pid = get_pid_on_port(port)

        saved_pid = None
        if os.path.isfile(pid_file):
            try:
                with open(pid_file) as f:
                    saved_pid = int(f.read().strip())
            except Exception:
                pass

        return {
            "success": True,
            "running": is_running,
            "pid": pid,
            "saved_pid": saved_pid,
            "port": port,
            "url": f"http://{host}:{port}" if is_running else None,
            "status": "running" if is_running else "stopped",
        }

    elif action == "stop":
        pid = get_pid_on_port(port)

        if not pid:
            if os.path.isfile(pid_file):
                os.remove(pid_file)
            return {
                "success": True,
                "message": "No server running on this port",
                "port": port,
                "status": "stopped",
            }

        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)

            if is_port_in_use(port):
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)

            if os.path.isfile(pid_file):
                os.remove(pid_file)

            return {
                "success": True,
                "message": "Server stopped",
                "pid": pid,
                "port": port,
                "status": "stopped",
            }
        except ProcessLookupError:
            if os.path.isfile(pid_file):
                os.remove(pid_file)
            return {
                "success": True,
                "message": "Server was not running",
                "port": port,
                "status": "stopped",
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to stop server: {e}"}

    else:
        return {"success": False, "error": f"Unknown action: {action}"}


def op_websocket_server(impl: dict, target: MCard, ctx: dict) -> Any:
    """
    Execute websocket_server builtin - manages a Python-based WebSocket server.

    Actions: deploy, status, stop
    Config: port, host

    Uses Python's asyncio-based WebSocket server internally.
    """
    import os
    import signal
    import socket
    import subprocess
    import sys
    import time

    def _resolve_config_value(val: Any) -> Any:
        """Resolve environment variables in config values like '${VAR}'."""
        if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
            env_var = val[2:-1]
            return os.getenv(env_var, val)
        return val

    # Valid config keys: port, host, root_dir
    config = impl.get("config", {})
    action = ctx.get("action") or config.get("action", "status")

    # Default to WS_PORT from .env matching the project configuration
    default_port = int(os.getenv("WS_PORT", 5321))
    raw_port = ctx.get("port") or config.get("port", default_port)
    port = int(_resolve_config_value(raw_port))
    
    host = ctx.get("host") or config.get("host", "localhost")

    project_root = os.getcwd()
    pid_file = os.path.join(project_root, f".websocket_server_{port}.pid")

    def is_port_in_use(p: int) -> bool:
        # Use lsof to check if port is in use (handles both IPv4 and IPv6)
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{p}"], capture_output=True, text=True
            )
            return result.returncode == 0 and result.stdout.strip() != ""
        except Exception:
            # Fallback to socket check
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", p)) == 0

    def get_pid_on_port(p: int):
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{p}"], capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().split("\n")[0])
        except Exception:
            pass
        return None

    if action == "deploy":
        # Check if already running
        if is_port_in_use(port):
            pid = get_pid_on_port(port)
            return {
                "success": True,
                "message": "WebSocket server already running",
                "pid": pid,
                "port": port,
                "url": f"ws://{host}:{port}/",
                "status": "already_running",
            }

        # Python WebSocket server script (inline)
        ws_server_code = f'''
import asyncio
import json
import signal
import sys
import time
import yaml

try:
    import websockets
except ImportError:
    print("websockets module not found, using basic socket server")
    sys.exit(1)

# Import PTR components for CLM execution
try:
    from mcard.ptr.clm.loader import CLMChapterLoader
except ImportError:
    print("Warning: mcard.ptr not available, CLM execution disabled")
    CLMChapterLoader = None

connected_clients = set()

async def execute_clm(clm_yaml, input_data):
    """Execute CLM code and return result"""
    if not CLMChapterLoader:
        return {{"error": "CLM execution not available - mcard.ptr not installed"}}

    import tempfile
    import os

    try:
        start_time = time.time()

        # Parse YAML to get metadata
        clm_data = yaml.safe_load(clm_yaml)

        # Write YAML to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(clm_yaml)
            temp_path = f.name

        try:
            # Load chapter from YAML file
            chapter = CLMChapterLoader.load_from_yaml(temp_path)

            # Execute chapter's action directly with provided input
            result, state, logs = chapter.action.execute(input_data, {{}})

            execution_time = (time.time() - start_time) * 1000  # ms

            return {{
                "success": True,
                "result": result,
                "executionTime": execution_time,
                "chapter": clm_data.get("chapter", {{}}).get("title", "Unknown"),
                "concept": clm_data.get("clm", {{}}).get("abstract", {{}}).get("concept", "Unknown"),
                "logs": logs
            }}
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "executionTime": 0
        }}

async def handler(websocket):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                message_id = data.get("messageId")

                if msg_type == "clm_execute":
                    # Execute CLM
                    clm_code = data.get("clm", "")
                    input_data = data.get("input", {{}})

                    result = await execute_clm(clm_code, input_data)

                    # Send response with same messageId
                    response = {{
                        "messageId": message_id,
                        **result
                    }}
                    await websocket.send(json.dumps(response))

                elif msg_type == "ping":
                    # Respond to ping
                    await websocket.send(json.dumps({{
                        "messageId": message_id,
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    }}))
                else:
                    # Echo unknown messages
                    response = json.dumps({{
                        "messageId": message_id,
                        "type": "echo",
                        "original": message,
                        "clients": len(connected_clients)
                    }})
                    await websocket.send(response)

            except json.JSONDecodeError:
                await websocket.send(json.dumps({{
                    "error": "Invalid JSON"
                }}))
            except Exception as e:
                await websocket.send(json.dumps({{
                    "error": str(e)
                }}))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)

async def main():
    async with websockets.serve(handler, "{host}", {port}):
        print("WebSocket CLM Execution Server running on ws://{host}:{port}/")
        print("Ready to handle CLM execution requests")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
'''

        # Start Python WebSocket server as background process
        try:
            process = subprocess.Popen(
                [sys.executable, "-c", ws_server_code],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            # Save PID
            with open(pid_file, "w") as f:
                f.write(str(process.pid))

            # Wait for server to start
            time.sleep(1.5)

            if is_port_in_use(port):
                return {
                    "success": True,
                    "message": "WebSocket server deployed successfully",
                    "pid": process.pid,
                    "port": port,
                    "url": f"ws://{host}:{port}/",
                    "status": "running",
                }
            else:
                return {
                    "success": False,
                    "error": "Server started but not responding. Ensure 'websockets' package is installed: pip install websockets",
                }

        except Exception as e:
            return {"success": False, "error": f"Failed to start server: {e}"}

    elif action == "status":
        is_running = is_port_in_use(port)
        pid = get_pid_on_port(port)

        saved_pid = None
        if os.path.isfile(pid_file):
            try:
                with open(pid_file) as f:
                    saved_pid = int(f.read().strip())
            except Exception:
                pass

        return {
            "success": True,
            "running": is_running,
            "pid": pid,
            "saved_pid": saved_pid,
            "port": port,
            "url": f"ws://{host}:{port}/" if is_running else None,
            "status": "running" if is_running else "stopped",
        }

    elif action == "stop":
        pid = get_pid_on_port(port)

        if not pid:
            if os.path.isfile(pid_file):
                os.remove(pid_file)
            return {
                "success": True,
                "message": "No WebSocket server running on this port",
                "port": port,
                "status": "stopped",
            }

        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)

            if is_port_in_use(port):
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)

            if os.path.isfile(pid_file):
                os.remove(pid_file)

            return {
                "success": True,
                "message": "WebSocket server stopped",
                "pid": pid,
                "port": port,
                "status": "stopped",
            }
        except ProcessLookupError:
            if os.path.isfile(pid_file):
                os.remove(pid_file)
            return {
                "success": True,
                "message": "WebSocket server was not running",
                "port": port,
                "status": "stopped",
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to stop server: {e}"}

    else:
        return {"success": False, "error": f"Unknown action: {action}"}
