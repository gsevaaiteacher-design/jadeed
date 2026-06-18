"""
ROLE: 4/9 - SANDBOX ENGINE
DESCRIPTION: Execution Isolation for external tools and unsafe code blocks.
STRICT DOMAIN: Tool execution restriction & File access control ONLY.
-----------------------------------------------------------------------
"""
import subprocess
import os
import sys
import shutil
from pathlib import Path

class ZStudioSandbox:
    def __init__(self):
        self.VER = "1.0.0"
        self.workspace = Path(os.getenv('TEMP')) / "zstudio_sandbox"
        self._prepare_sandbox()

    def _prepare_sandbox(self):
        """Creates a fresh, clean workspace for tool execution."""
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def execute_tool(self, command_list, timeout=30):
        """
        Executes a tool inside a restricted environment.
         Restricted CWD (Current Working Directory)
         Environment variable stripping
         Execution Timeout
        """
        try:
            # Clean environment to prevent sensitive data leakage
            restricted_env = {
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                "TEMP": str(self.workspace),
                "TMP": str(self.workspace)
            }

            # Start Process
            process = subprocess.Popen(
                command_list,
                cwd=str(self.workspace),
                env=restricted_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False # Crucial: Prevents Shell Injection
            )

            stdout, stderr = process.communicate(timeout=timeout)
            
            return {
                "status": "success" if process.returncode == 0 else "failed",
                "exit_code": process.returncode,
                "output": stdout,
                "error": stderr
            }

        except subprocess.TimeoutExpired:
            process.kill()
            return {"status": "error", "message": "E_SANDBOX_TIMEOUT"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def secure_delete_workspace(self):
        """Cleans up all sandbox traces."""
        if self.workspace.exists():
            shutil.rmtree(self.workspace)

# Instance
sandbox_engine = ZStudioSandbox()