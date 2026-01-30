import os
import shutil
import psutil
import logging

log = logging.getLogger(__name__)


def collect_audit_data():
    return {
        "disk": get_disk_usage(),
        "cpu": get_cpu_usage(),
        "memory": get_memory_usage(),
    }


def get_disk_usage():
    root_path = os.path.abspath(os.sep)
    total, used, free = shutil.disk_usage(root_path)
    percent_used = (used / total) * 100

    return {
        "total_gb": round(total / (1024 ** 3), 2),
        "used_gb": round(used / (1024 ** 3), 2),
        "free_gb": round(free / (1024 ** 3), 2),
        "percent_used": round(percent_used, 2),
    }


def get_cpu_usage():
    data = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
    }

    try:
        data["load_average"] = psutil.getloadavg()
    except (AttributeError, OSError):
        # Not available on Windows.
        pass

    return data


def get_memory_usage():
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "percent_used": mem.percent
    }
