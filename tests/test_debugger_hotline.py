import datetime
import importlib.util
import linecache
import os
import sys
import textwrap
import unittest

from spacetimepy.core.function_call import FunctionCallRepository
from spacetimepy.core.models import CodeDefinition, FunctionCall, StackSnapshot, StackSnapshotEdge, init_db
from spacetimepy.core.monitoring import SpaceTimeMonitor


class FrameProxy:
    def __init__(self, module, locals_=None):
        self.f_globals = module.__dict__
        self.f_locals = locals_ or {}


def write_module(path, return_expression):
    path.write_text(textwrap.dedent(f"""
        def target(x):
            value = x + 1
            return {return_expression}
    """))
    linecache.clearcache()


def load_module(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_monitor_without_sys_monitoring():
    Session = init_db(":memory:")
    session = Session()
    monitor = SpaceTimeMonitor.__new__(SpaceTimeMonitor)
    monitor.session = session
    monitor.call_tracker = FunctionCallRepository(session)
    monitor._code_definition_cache = {}
    return monitor



class DapClient:
    def __init__(self, host, port):
        import json
        import socket

        self.json = json
        self.sock = socket.create_connection((host, port), timeout=10)
        self.sock_file = self.sock.makefile("rwb")
        self.seq = 1

    def close(self):
        self.sock_file.close()
        self.sock.close()

    def request(self, command, arguments=None):
        request = {
            "seq": self.seq,
            "type": "request",
            "command": command,
            "arguments": arguments or {},
        }
        self.seq += 1
        self._send(request)
        return request["seq"]

    def wait_for_response(self, request_seq, timeout=10):
        while True:
            message = self.read_message(timeout=timeout)
            if message.get("type") == "response" and message.get("request_seq") == request_seq:
                if not message.get("success", False):
                    raise AssertionError(f"DAP request failed: {message}")
                return message

    def request_and_wait(self, command, arguments=None, timeout=10):
        request_seq = self.request(command, arguments)
        return self.wait_for_response(request_seq, timeout=timeout)

    def wait_for_event(self, event_name, timeout=10):
        while True:
            message = self.read_message(timeout=timeout)
            if message.get("type") == "event" and message.get("event") == event_name:
                return message

    def wait_for_stopped_thread(self, timeout=10):
        stopped = self.wait_for_event("stopped", timeout=timeout)
        return stopped["body"]["threadId"]

    def stack_frame_id(self, thread_id, name=None):
        stack = self.request_and_wait("stackTrace", {"threadId": thread_id})["body"]["stackFrames"]
        if name is None:
            return stack[0]["id"]
        for frame in stack:
            if frame.get("name") == name:
                return frame["id"]
        return stack[0]["id"]

    def continue_until_process_exits(self, process, timeout=20):
        import time

        deadline = time.monotonic() + timeout
        while process.poll() is None and time.monotonic() < deadline:
            try:
                message = self.read_message(timeout=1)
            except TimeoutError:
                continue

            if message.get("type") == "event" and message.get("event") == "stopped":
                thread_id = message["body"]["threadId"]
                self.request_and_wait("continue", {"threadId": thread_id})
            elif message.get("type") == "event" and message.get("event") in {"terminated", "exited"}:
                remaining = max(deadline - time.monotonic(), 0.1)
                process.wait(timeout=remaining)
                return

        if process.poll() is None:
            raise TimeoutError("Debuggee did not exit after continuing all stopped events")

    def read_message(self, timeout=10):
        import time

        deadline = time.monotonic() + timeout
        header = b""
        while b"\r\n\r\n" not in header:
            if time.monotonic() > deadline:
                raise TimeoutError("Timed out waiting for DAP message header")
            chunk = self.sock_file.read(1)
            if not chunk:
                raise EOFError("Debug adapter closed the connection")
            header += chunk

        content_length = None
        for line in header.decode("ascii").split("\r\n"):
            if line.lower().startswith("content-length:"):
                content_length = int(line.split(":", 1)[1].strip())
                break
        if content_length is None:
            raise ValueError(f"DAP message missing Content-Length: {header!r}")

        payload = self.sock_file.read(content_length)
        return self.json.loads(payload.decode("utf-8"))

    def _send(self, message):
        payload = self.json.dumps(message).encode("utf-8")
        header = f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii")
        self.sock_file.write(header + payload)
        self.sock_file.flush()


class TestRealDebugpyHotlineInteraction(unittest.TestCase):
    def test_debugpy_hotline_reload_records_snapshot_code_divergence(self):
        """Drive the real debugpy/DAP hotreplace flow used by the extension.

        This test is opt-in because it opens a local debugger socket and
        currently acts as a reproducer: the flow completes, but the function
        still returns the old code result.
        """
        #if os.environ.get("SPACETIMEPY_RUN_DEBUGPY_HOTLINE_TEST") != "1":
        #    self.skipTest("set SPACETIMEPY_RUN_DEBUGPY_HOTLINE_TEST=1 to run the real debugpy hotline test")

        try:
            import debugpy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"debugpy is not available: {exc}")

        import contextlib
        import socket
        import sqlite3
        import subprocess
        import tempfile
        from pathlib import Path

        def free_port():
            with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
                sock.bind(("127.0.0.1", 0))
                return sock.getsockname()[1]

        def target_source(multiplier, addend):
            return textwrap.dedent(f"""
                def target(x):
                    a = x + 1
                    b = a * {multiplier}
                    c = b + {addend}
                    return c
            """)

        def line_containing(path, text):
            for lineno, line in enumerate(path.read_text().splitlines(), start=1):
                if text in line:
                    return lineno
            raise AssertionError(f"Could not find {text!r} in {path}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "trace.db"
            result_path = temp_path / "result.txt"
            target_path = temp_path / "hotline_debugpy_target.py"
            launcher_path = temp_path / "hotline_debugpy_launcher.py"
            port = free_port()

            target_path.write_text(target_source(2, 1))
            b_line = line_containing(target_path, "b =")

            launcher_path.write_text(textwrap.dedent(f"""
                import pathlib
                import sys

                import debugpy
                import spacetimepy
                from spacetimepy.interface.debugger import hotline

                sys.path.insert(0, {str(temp_path)!r})
                debugpy.listen(("127.0.0.1", {port}))
                print("DEBUGPY_READY", flush=True)
                debugpy.wait_for_client()

                monitor = spacetimepy.init_monitoring({str(db_path)!r}, in_memory=False)
                import hotline_debugpy_target

                hotline(hotline_debugpy_target.target)
                spacetimepy.line()(hotline_debugpy_target.target)
                spacetimepy.start_session("Debugger Session test")
                result = hotline_debugpy_target.target(5)
                pathlib.Path({str(result_path)!r}).write_text(str(result))
                spacetimepy.end_session()
            """))

            env = os.environ.copy()
            env["PYTHONPATH"] = os.pathsep.join(
                [str(Path(__file__).resolve().parents[1] / "src"), env.get("PYTHONPATH", "")]
            )
            env["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            process = subprocess.Popen(
                [sys.executable, str(launcher_path)],
                cwd=temp_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            client = None
            try:
                ready = process.stdout.readline().strip()
                self.assertEqual(ready, "DEBUGPY_READY")

                client = DapClient("127.0.0.1", port)
                client.request_and_wait("initialize", {
                    "adapterID": "debugpy",
                    "clientID": "spacetimepy-tests",
                    "clientName": "SpaceTimePy tests",
                    "pathFormat": "path",
                    "linesStartAt1": True,
                    "columnsStartAt1": True,
                    "supportsVariableType": True,
                    "supportsRunInTerminalRequest": False,
                })
                client.request("attach", {"justMyCode": False})
                client.wait_for_event("initialized")
                client.request_and_wait("setBreakpoints", {
                    "source": {"path": str(target_path)},
                    "breakpoints": [{"line": b_line}],
                })
                client.request_and_wait("configurationDone")
                client.wait_for_response(2)

                thread_id = client.wait_for_stopped_thread(timeout=15)
                frame_id = client.stack_frame_id(thread_id, name="target")

                target_path.write_text(target_source(5, 7))
                linecache.clearcache()
                importlib.invalidate_caches()

                client.request_and_wait("evaluate", {
                    "expression": "_ahs_reload()",
                    "frameId": frame_id,
                    "context": "repl",
                })
                client.request_and_wait("continue", {"threadId": thread_id})

                thread_id = client.wait_for_stopped_thread(timeout=15)
                client.request_and_wait("evaluate", {
                    "expression": "_ahs_correct_jump()",
                    "frameId": frame_id,
                    "context": "repl",
                })
                client.request_and_wait("continue", {"threadId": thread_id})
                client.continue_until_process_exits(process, timeout=20)

                if process.poll() is None:
                    process.wait(timeout=20)
                self.assertEqual(process.returncode, 0)
            finally:
                if client is not None:
                    client.close()
                if process.poll() is None:
                    process.kill()
                    process.communicate()

            self.assertEqual(result_path.read_text(), "37")

            conn = sqlite3.connect(db_path)
            try:
                code_ids = {
                    row[0]
                    for row in conn.execute(
                        "select distinct code_definition_id from stack_snapshots where code_definition_id is not null"
                    )
                }
                self.assertGreaterEqual(len(code_ids), 2)
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
