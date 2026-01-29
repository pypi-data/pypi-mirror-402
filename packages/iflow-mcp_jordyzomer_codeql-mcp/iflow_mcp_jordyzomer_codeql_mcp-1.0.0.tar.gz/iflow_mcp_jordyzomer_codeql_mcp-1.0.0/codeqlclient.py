import time
import re
import os
import json
import subprocess
import threading
import uuid
from pathlib import Path


class CodeQLQueryServer:
    def __init__(self, codeql_path="codeql"):
        self.codeql_path = codeql_path
        self.proc = None
        self.reader_thread = None
        self.pending = {}
        self.running = True
        self.id_counter = 1
        self.progress_id = 0
        self.progress_callbacks = {}
        self.codeql_available = self._check_codeql_available()

    def _check_codeql_available(self):
        """Check if CodeQL binary is available"""
        try:
            result = subprocess.run(
                [self.codeql_path, "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def start(self):
        if not self.codeql_available:
            print("[Warning] CodeQL binary not found. Running in mock mode.")
            return

        self.proc = subprocess.Popen(
            [
                self.codeql_path,
                "execute",
                "query-server2",
                "--debug",
                "--tuple-counting",
                "--threads=0",
                "--evaluator-log-level",
                "5",
                "-v",
                "--log-to-stderr",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered
        )
        self.reader_thread = threading.Thread(
            target=self._read_loop, daemon=True
        )
        self.reader_thread.start()
        self.stderr_thread = threading.Thread(
            target=self._stderr_loop, daemon=True
        )
        self.stderr_thread.start()

    def _stderr_loop(self):
        while self.running:
            line = self.proc.stderr.readline()
            # For debugging
            # if line:
            #    print("[CodeQL stderr]", line.strip())

    def _read_loop(self):
        print("[*] Read loop started")
        while self.running:
            line = self.proc.stdout.readline()
            if not line:
                print("[*] Read loop: EOF or closed stdout")
                break
            print(f"[stdout] {line.strip()}")
            if line.startswith("Content-Length:"):
                try:
                    length = int(line.strip().split(":")[1])
                    blank = self.proc.stdout.readline()
                    content = self.proc.stdout.read(length)
                    print(f"[raw response body] {content.strip()}")
                    message = json.loads(content)
                    self._handle_message(message)
                except Exception as e:
                    print(f"[!] Failed to parse message: {e}")

    def _handle_message(self, message):
        print(f"\n[←] Received response:\n{json.dumps(message, indent=2)}\n")

        if message.get("method") == "ql/progressUpdated":
            params = message.get("params", {})
            progress_id = params.get("id")
            callback = self.progress_callbacks.get(progress_id)
            if callback:
                callback(params)
            else:
                print(
                    f"[ql-progress:{progress_id}] step={params.get('step')} / {params.get('maxStep')}"
                )
            return

        if "method" in message and message["method"] == "evaluation/progress":
            progress_id = message["params"].get("progressId")
            msg = message["params"].get("message")
            callback = self.progress_callbacks.get(progress_id)
            if callback:
                callback(msg)
            else:
                print(f"[progress:{progress_id}] {msg}")
            return

        if "id" in message:
            request_id = message["id"]
            if request_id in self.pending:
                self.pending[request_id].put(message)
            else:
                print(f"[!] Unexpected response for request {request_id}")

    def _send_request(self, method, params=None):
        if not self.codeql_available:
            print(f"[Mock] {method} called with params: {params}")
            return {
                "jsonrpc": "2.0",
                "id": self.id_counter,
                "result": {}
            }

        request = {
            "jsonrpc": "2.0",
            "id": self.id_counter,
            "method": method,
        }
        if params:
            request["params"] = params

        import queue
        response_queue = queue.Queue()
        self.pending[self.id_counter] = response_queue

        request_str = json.dumps(request)
        message = f"Content-Length: {len(request_str)}\r\n\r\n{request_str}"
        self.proc.stdin.write(message)
        self.proc.stdin.flush()

        self.id_counter += 1

        try:
            response = response_queue.get(timeout=60)
            del self.pending[request_id]
            return response
        except queue.Empty:
            print(f"[!] Timeout waiting for response to {method}")
            del self.pending[request_id]
            return {"error": "timeout"}

    def wait_for_completion_callback(self):
        import queue
        response_holder = queue.Queue()
        done = threading.Event()
        callback = lambda msg: response_holder.put(msg)
        return callback, done, response_holder

    def register_databases(self, db_paths, callback=None, progress_callback=None):
        if not self.codeql_available:
            print(f"[Mock] register_databases called with paths: {db_paths}")
            return

        if progress_callback:
            self.progress_id += 1
            self.progress_callbacks[self.progress_id] = progress_callback

        self._send_request("jsonrpc/databases/register", {
            "databases": db_paths
        })

    def quick_evaluate_and_wait(self, query_file, db_path, output_path, start, scol, end, ecol):
        if not self.codeql_available:
            print(f"[Mock] quick_evaluate called for {query_file}")
            return

        self._send_request("jsonrpc/quickEvaluate", {
            "queryFile": query_file,
            "dbPath": db_path,
            "outputPath": output_path,
            "startLine": start,
            "startCol": scol,
            "endLine": end,
            "endCol": ecol
        })

    def evaluate_and_wait(self, query_path, db_path, output_path):
        if not self.codeql_available:
            print(f"[Mock] evaluate called for {query_path}")
            return

        self._send_request("jsonrpc/evaluate", {
            "queryFile": query_path,
            "dbPath": db_path,
            "outputPath": output_path
        })

    def decode_bqrs(self, bqrs_path, fmt):
        if not self.codeql_available:
            print(f"[Mock] decode_bqrs called for {bqrs_path}")
            return "Mocked BQRS decoding result"

        result = subprocess.run(
            [self.codeql_path, "bqrs", "decode", "--format", fmt, bqrs_path],
            capture_output=True,
            text=True
        )
        return result.stdout

    def find_class_identifier_position(self, file_path, class_name):
        if not self.codeql_available:
            print(f"[Mock] find_class_identifier_position for {class_name}")
            return (1, 1, 1, 1)

        with open(file_path, "r") as f:
            content = f.read()

        pattern = rf"class\s+{re.escape(class_name)}\b"
        match = re.search(pattern, content)
        if match:
            pos = match.start()
            lines = content[:pos].split("\n")
            line_num = len(lines)
            col_num = len(lines[-1]) + 1
            return (line_num, col_num, line_num, col_num + len(class_name))
        raise ValueError(f"Class {class_name} not found")

    def find_predicate_identifier_position(self, file_path, predicate_name):
        if not self.codeql_available:
            print(f"[Mock] find_predicate_identifier_position for {predicate_name}")
            return (1, 1, 1, 1)

        with open(file_path, "r") as f:
            content = f.read()

        pattern = rf"predicate\s+{re.escape(predicate_name)}\b"
        match = re.search(pattern, content)
        if match:
            pos = match.start()
            lines = content[:pos].split("\n")
            line_num = len(lines)
            col_num = len(lines[-1]) + 1
            return (line_num, col_num, line_num, col_num + len(predicate_name))
        raise ValueError(f"Predicate {predicate_name} not found")