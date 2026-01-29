import time


def run_cuda_benchmark():
    try:
        import torch

        if not torch.cuda.is_available():
            return {"cuda_available": False}

        start = time.time()
        a = torch.randn(1024, 1024, device="cuda")
        b = torch.randn(1024, 1024, device="cuda")
        torch.matmul(a, b)
        torch.cuda.synchronize()

        return {
            "cuda_available": True,
            "gpu_name": torch.cuda.get_device_name(0),
            "benchmark_time_sec": round(time.time() - start, 4),
        }

    except Exception:
        return {"cuda_available": False}
