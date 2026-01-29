import asyncio
from ..core.executor import Executor
from typing import List
from termcolor import cprint

class TroubleShoot:
    def __init__(self):
        self.executor = Executor()
        self.services = []
        self.modules = []
        self.processes = []

    @classmethod
    async def create(cls) -> "TroubleShoot":
        instance = cls()
        await instance.find_nvidia_modules()
        await instance.find_services_using_gpu()
        await instance.find_processes_using_gpu()
        return instance

    async def find_nvidia_modules(self) -> None:
        command = "sudo lsmod | grep nvidia | awk '{print $1}'"
        result = await self.executor.execute(command)
        self.modules = result.split("\n")

    async def find_services_using_gpu(self) -> None:
        command = "sudo systemctl list-units --type=service | grep nvidia | awk '{print $1}'"
        result = await self.executor.execute(command)
        self.services = result.split("\n")

    async def find_processes_using_gpu(self) -> List[int]:
        command = "sudo lsof /dev/nvidia* 2>/dev/null | awk 'NR>1 {print $2}' | sort -u"
        result = await self.executor.execute(command)
        self.processes = result.split("\n") if result else []

    async def get_gpu_pci_addresses(self) -> List[str]:
        command = "lspci | grep NVIDIA | grep -E '3D|VGA|Display' | awk '{print $1}'"
        result = await self.executor.execute(command)
        return [f"0000:{addr}" for addr in result.split("\n") if addr.strip()]

    async def reset_all_gpus(self) -> bool:
        cprint("="*80, "cyan")
        cprint("GPU RESET SEQUENCE", "cyan", attrs=["bold"])
        cprint("="*80, "cyan")

        cprint("\n[1/6] Stopping NVIDIA processes...", "yellow")
        for process in self.processes:
            if process.strip():
                cprint(f"  Stopping {process}...", "green")
                await self.executor.execute(f"sudo kill -9 {process}")

        cprint("\n[2/6] Stopping NVIDIA services...", "yellow")
        for service in self.services:
            if service.strip():
                cprint(f"  Stopping {service}...", "yellow")
                await self.executor.execute(f"sudo systemctl stop {service}")

        cprint("\n[3/6] Unloading kernel modules...", "yellow")
        module_unload_order = ["nvidia_uvm", "nvidia_drm", "nvidia_modeset", "nvidia"]
        for module in module_unload_order:
            if module in self.modules:
                cprint(f"  Unloading {module}...", "yellow")
                result = await self.executor.execute(f"sudo modprobe -r {module}")
                if result is not None:
                    cprint(f"    Module {module} unloaded", "green")

        gpu_addresses = await self.get_gpu_pci_addresses()
        
        cprint(f"\n[4/6] Resetting {len(gpu_addresses)} GPUs via PCIe...", "yellow")
        success = True
        for idx, addr in enumerate(gpu_addresses):
            reset_path = f"/sys/bus/pci/devices/{addr}/reset"
            result = await self.executor.execute(f"sudo sh -c 'echo 1 > {reset_path}'")
            if result is not None:
                cprint(f"  GPU {idx} ({addr}) reset", "green")
            else:
                cprint(f"  GPU {idx} ({addr}) reset failed", "red")
                success = False
        
        cprint("\n[5/6] Reloading kernel modules...", "yellow")
        for module in ["nvidia", "nvidia_modeset", "nvidia_drm", "nvidia_uvm"]:
            await self.executor.execute(f"sudo modprobe {module}")
        cprint("  Modules reloaded", "green")
        
        cprint("\n[6/6] Restarting NVIDIA services...", "yellow")
        for service in self.services:
            if service.strip():
                cprint(f"  Starting {service}...", "yellow")
                await self.executor.execute(f"sudo systemctl start {service}")

        cprint("\n" + "="*80, "cyan")
        if success:
            cprint("GPU RESET COMPLETE", "green", attrs=["bold"])
        else:
            cprint("GPU RESET FAILED", "red", attrs=["bold"])
        cprint("="*80, "cyan")
        return success

async def run_gpu_reset():
    troubleshoot = await TroubleShoot.create()
    await troubleshoot.reset_all_gpus()

if __name__ == "__main__":
    asyncio.run(run_gpu_reset())