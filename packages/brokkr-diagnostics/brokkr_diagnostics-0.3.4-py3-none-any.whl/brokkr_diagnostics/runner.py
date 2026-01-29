import asyncio
import json
from brokkr_diagnostics.nvidia import (
    run_driver_diagnostics,
    run_gpu_hardware_diagnostics,
    run_cuda_diagnostics,
)
from brokkr_diagnostics.pcie import run_lspci_diagnostics
from brokkr_diagnostics.kernel import (
    run_nvidia_services_diagnostics,
    run_kernel_logs_diagnostics,
    run_proc_diagnostics,
)
import os
from termcolor import cprint
from brokkr_diagnostics.infiniband import run_ib_diagnostics





async def run_diagnostics() -> list[dict]:
    """Run all diagnostics and return results with command names"""
    diagnostics = [
        ("driver", run_driver_diagnostics),
        ("gpu_hardware", run_gpu_hardware_diagnostics),
        ("cuda", run_cuda_diagnostics),
        ("pcie", run_lspci_diagnostics),
        ("nvidia_services", run_nvidia_services_diagnostics),
        ("kernel_logs", run_kernel_logs_diagnostics),
        ("system_info", run_proc_diagnostics),
        ("infiniband", run_ib_diagnostics),
    ]
    
    tasks = [func(format_type="json") for _, func in diagnostics]
    results = await asyncio.gather(*tasks)
    
    response = []
    for (name, _), result in zip(diagnostics, results):
        # result is a JSON string, parse it to include as object
        parsed = json.loads(result) if result else None
        response.append({"command": name, "result": parsed})
    
    return response



