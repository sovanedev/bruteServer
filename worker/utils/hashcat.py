import subprocess
import threading
import time, os
from pathlib import Path

class HashcatRunner:
    def __init__(self, hashcat_path="hashcat", work_dir="/worker/hashcat_work"):
        self.hashcat_path = hashcat_path
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.process = None
        self.status = "idle"
        self.output_file = None
        self.error = None
        self._thread = None

        self.id = None

    def _run_hashcat(self, args):
        try:
            print(f"Запуск hashcat с аргументами: {args}")
            self.status = "running"
            self.process = subprocess.Popen(
                [self.hashcat_path] + args,
                cwd=str(self.work_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=self.env
            )
            stdout, stderr = self.process.communicate()
            print("stdout:", stdout)
            print("stderr:", stderr)
            if self.process.returncode == 0:
                self.status = "done"
            else:
                self.status = "error"
                self.error = stderr.strip()
                print(f"Hashcat завершился со статусом {self.status}\n\n{stdout}\n\n{stderr}")
        except Exception as e:
            self.status = "error"
            self.error = str(e)
            print(e)

    def start_bruteforce(self, 
                         hash_file: str, 
                         dict_file: str,
                         rule_file: str,
                         hash_type: int,
                         id: str,
                         output_file: str = "hashcat_output.txt", 
                         extra_args=None
                         ):
        if self.status == "running":
            raise RuntimeError("Hashcat is already running")
        

        self.output_file = self.work_dir / output_file

        self.env = os.environ.copy()
        session_path = f"/tmp/hashcat_gpu{os.getpid()}_{threading.get_ident()}"
        Path(session_path).mkdir(parents=True, exist_ok=True)
        self.env["HOME"] = session_path
        self.env["XDG_CACHE_HOME"] = session_path

        args = [
            "-m", str(hash_type),
            "-a", "0",
            hash_file,
            dict_file,
            "-r", rule_file,
            "--outfile", str(self.output_file),
            "--potfile-disable",
            "--session", f"session_{extra_args[-1]}{id}"
        ]

        if extra_args:
            args += extra_args

        self.id = id

        self._thread = threading.Thread(target=self._run_hashcat, args=(args,), daemon=True)
        self._thread.start()

    def is_running(self):
        return self.status == "running"

    def get_status(self):
        return {
            "status": self.status,
            "error": self.error,
            "output_file": str(self.output_file) if self.output_file else None
        }

    def wait_finish(self, timeout=None):
        if self._thread:
            self._thread.join(timeout=timeout)
        return self.status

    def stop(self):
        if self.process and self.status == "running":
            self.process.terminate()
            self.status = "stopped"

    def reset(self):
        self.process = None
        self.status = "idle"
        self.output_file = None
        self.error = None
        self._thread = None
        self.id = None
