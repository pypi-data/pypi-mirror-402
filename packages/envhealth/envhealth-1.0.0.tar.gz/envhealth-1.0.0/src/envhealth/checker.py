import platform
import psutil

from .network_check import check_internet, check_proxy
from .version_drift import check_version_drift
from .security_check import security_findings
from .cuda_benchmark import run_cuda_benchmark


class Checker:
    def full_report(self):
        return {
            "system": self.system(),
            "cpu": self.cpu(),
            "memory": self.memory(),
            "disk": self.disk(),
            "internet": check_internet(),
            "proxy": check_proxy(),
            "cuda": run_cuda_benchmark(),
            "version_drift": check_version_drift(),
            "security": security_findings(),
        }

    def system(self):
        return {
            "os": platform.system(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
        }

    def cpu(self):
        return {
            "cores": psutil.cpu_count(),
            "usage_percent": psutil.cpu_percent(interval=1),
        }

    def memory(self):
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / 1e9, 1),
            "used_percent": mem.percent,
        }

    def disk(self):
        disk = psutil.disk_usage("/")
        return {
            "total_gb": round(disk.total / 1e9, 1),
            "used_percent": disk.percent,
        }

    def exit_code(self, fail_on=None):
        if fail_on == "major":
            return 2
        if fail_on == "minor":
            return 1
        return 0
