"""
Hardware detection utilities for Ailoos nodes.
Provides information about CPU, GPU, memory, and other hardware capabilities.
"""

import platform
import psutil
from typing import Dict, Any, Optional


def get_hardware_info() -> Dict[str, Any]:
    """
    Detect and return comprehensive hardware information.

    Returns:
        Dictionary with hardware specifications

    Example:
        info = get_hardware_info()
        print(f"CPU cores: {info['cpu_cores']}")
        print(f"Memory: {info['memory_gb']} GB")
    """
    try:
        # CPU Information
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "cpu_freq": _get_cpu_freq(),
            "cpu_percent": psutil.cpu_percent(interval=1)
        }

        # Memory Information
        memory = psutil.virtual_memory()
        memory_info = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "usage_percent": memory.percent
        }

        # GPU Information
        gpu_info = _detect_gpu()

        # System Information
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node()
        }

        # Network Information
        network_info = _get_network_info()

        # Storage Information
        storage_info = _get_storage_info()

        return {
            "cpu": cpu_info,
            "memory": memory_info,
            "gpu": gpu_info,
            "system": system_info,
            "network": network_info,
            "storage": storage_info,
            "detection_status": "success"
        }

    except Exception as e:
        return {
            "detection_status": "error",
            "error_message": str(e),
            "cpu": {"logical_cores": "unknown"},
            "memory": {"total_gb": "unknown"},
            "gpu": {"available": False}
        }


def _get_cpu_freq() -> Optional[Dict[str, float]]:
    """Get CPU frequency information."""
    try:
        freq = psutil.cpu_freq()
        if freq:
            return {
                "current_mhz": round(freq.current, 2),
                "min_mhz": round(freq.min, 2),
                "max_mhz": round(freq.max, 2)
            }
    except Exception:
        pass
    return None


def _detect_gpu() -> Dict[str, Any]:
    """Detect GPU information."""
    gpu_info = {
        "available": False,
        "count": 0,
        "devices": []
    }

    # Try PyTorch CUDA detection
    try:
        import torch
        if torch.cuda.is_available():
            gpu_info["available"] = True
            gpu_info["count"] = torch.cuda.device_count()

            for i in range(torch.cuda.device_count()):
                device_props = torch.cuda.get_device_properties(i)
                gpu_info["devices"].append({
                    "id": i,
                    "name": device_props.name,
                    "memory_gb": round(device_props.total_memory / (1024**3), 2),
                    "compute_capability": f"{device_props.major}.{device_props.minor}"
                })
    except ImportError:
        gpu_info["detection_note"] = "PyTorch not available for GPU detection"

    # Try other GPU detection methods if needed
    if not gpu_info["available"]:
        # Could add AMD GPU detection, Apple Silicon, etc.
        pass

    return gpu_info


def _get_network_info() -> Dict[str, Any]:
    """Get network interface information."""
    try:
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()

        interfaces = {}
        for interface_name, addresses in net_if_addrs.items():
            if interface_name in net_if_stats:
                stats = net_if_stats[interface_name]
                interfaces[interface_name] = {
                    "is_up": stats.isup,
                    "speed_mbps": getattr(stats, 'speed', 0),
                    "mtu": stats.mtu,
                    "addresses": [
                        {
                            "family": str(addr.family),
                            "address": addr.address,
                            "netmask": addr.netmask,
                            "broadcast": addr.broadcast
                        }
                        for addr in addresses
                    ]
                }

        return {
            "interfaces": interfaces,
            "connections": len(psutil.net_connections())
        }
    except Exception as e:
        return {"error": str(e)}


def _get_storage_info() -> Dict[str, Any]:
    """Get storage/disk information."""
    try:
        partitions = psutil.disk_partitions()
        disks = []

        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "filesystem": partition.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "usage_percent": usage.percent
                })
            except Exception:
                # Skip partitions we can't access
                continue

        io_counters = psutil.disk_io_counters()
        io_info = {}
        if io_counters:
            io_info = {
                "read_count": io_counters.read_count,
                "write_count": io_counters.write_count,
                "read_bytes": io_counters.read_bytes,
                "write_bytes": io_counters.write_bytes
            }

        return {
            "disks": disks,
            "io_counters": io_info
        }
    except Exception as e:
        return {"error": str(e)}


def get_training_capability_score() -> float:
    """
    Calculate a training capability score based on hardware.

    Returns:
        Score from 0.0 to 1.0 indicating training capability
    """
    try:
        info = get_hardware_info()

        score = 0.0

        # CPU score (0-0.3)
        cpu_cores = info["cpu"].get("logical_cores", 0)
        if isinstance(cpu_cores, int):
            cpu_score = min(cpu_cores / 16.0, 1.0) * 0.3  # 16 cores = max score
            score += cpu_score

        # Memory score (0-0.3)
        memory_gb = info["memory"].get("total_gb", 0)
        if isinstance(memory_gb, (int, float)):
            memory_score = min(memory_gb / 32.0, 1.0) * 0.3  # 32GB = max score
            score += memory_score

        # GPU score (0-0.4)
        gpu = info.get("gpu", {})
        if gpu.get("available", False):
            gpu_count = gpu.get("count", 0)
            gpu_score = min(gpu_count / 4.0, 1.0) * 0.4  # 4 GPUs = max score
            score += gpu_score

        return round(score, 3)

    except Exception:
        return 0.0


def is_capable_for_training(min_score: float = 0.3) -> bool:
    """
    Check if the hardware is capable of training.

    Args:
        min_score: Minimum capability score required

    Returns:
        True if capable for training
    """
    score = get_training_capability_score()
    return score >= min_score


def print_hardware_summary():
    """Print a formatted summary of hardware information."""
    info = get_hardware_info()

    print("=== Ailoos Hardware Detection ===")
    print(f"Status: {info['detection_status']}")

    if info['detection_status'] == 'success':
        print(f"CPU: {info['cpu']['logical_cores']} cores")
        print(f"Memory: {info['memory']['total_gb']} GB total")
        print(f"GPU: {len(info['gpu'].get('devices', []))} devices available")
        print(f"Platform: {info['system']['platform']} {info['system']['architecture']}")

        score = get_training_capability_score()
        print(f"Training Capability Score: {score:.3f}/1.0")

        capable = is_capable_for_training()
        print(f"Training Capable: {'Yes' if capable else 'No'}")
    else:
        print(f"Error: {info.get('error_message', 'Unknown error')}")

    print("=" * 35)


if __name__ == "__main__":
    print_hardware_summary()