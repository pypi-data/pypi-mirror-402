from nvidia_gpu_tools import find_gpus, Gpu, NvSwitch
from termcolor import cprint
from typing import List
import time
from termcolor import cprint
import subprocess





class ConfidentialComputeManager:
    """
    Manager for Confidential Compute (CC) mode on NVIDIA GPUs.
    """
    def __init__(self):
        self.devices = self.get_devices()

    def get_devices(self) -> List[Gpu]:
        try:
            gpus = subprocess.run(
                "lspci | grep 3D|awk '{print $1}'",
                shell=True,
                capture_output=True,
                text=True
            )
            gpus = [g for g in gpus.stdout.split("\n") if g]
            return gpus
        except Exception as e:
            cprint(f"Error getting GPUs: {e}", "red")
            return []

    def get_by_bdf(self, bdf: str) -> Gpu | NvSwitch:
        try:
            devices, _ = find_gpus(bdf)
            if devices:
                return devices[0]
            return None
               
        except Exception as e:
            cprint(f"Error getting device: {e}", "red")
            return None

    def toggle_device_mode(self, mode: str):
        try:
            for device in self.devices:
                try:
                    device_or_nvswitch = self.get_by_bdf(device)
                    if device_or_nvswitch is None:
                        cprint(f"Skipping {device}: device not found", "yellow")
                        continue
                    if hasattr(device_or_nvswitch, 'is_broken_gpu') and device_or_nvswitch.is_broken_gpu():
                        cprint(f"Skipping {device}: broken device", "yellow")
                        continue
                    if not hasattr(device_or_nvswitch, 'is_cc_query_supported') or not device_or_nvswitch.is_cc_query_supported:
                        cprint(f"Skipping {device}: CC mode not supported", "yellow")
                        continue
                    device_or_nvswitch.set_cc_mode(mode)
                    device_or_nvswitch.reset_with_os()
                    cprint(f"CC mode for device {device} set to {mode}", "green")
                except Exception as e:
                    cprint(f"Error setting CC mode for device {device} to {mode}: {e}", "red")
                    continue
        except Exception as e:
            cprint(f"Error toggling device mode: {e}", "red")
            return None

    def toggle_ppcie_mode(self, mode: str):
        try:
            for device in self.devices:
                try:
                    device_or_nvswitch = self.get_by_bdf(device)
                    if device_or_nvswitch is None:
                        cprint(f"Skipping {device}: device not found", "yellow")
                        continue
                    if hasattr(device_or_nvswitch, 'is_broken_gpu') and device_or_nvswitch.is_broken_gpu():
                        cprint(f"Skipping {device}: broken device", "yellow")
                        continue
                    if not hasattr(device_or_nvswitch, 'is_ppcie_query_supported') or not device_or_nvswitch.is_ppcie_query_supported:
                        cprint(f"Skipping {device}: PPCIE mode not supported", "yellow")
                        continue
                    device_or_nvswitch.set_ppcie_mode(mode)
                    device_or_nvswitch.reset_with_os()
                    cprint(f"PPCIE mode for device {device} set to {mode}", "green")
                except Exception as e:
                    cprint(f"Error setting PPCIE mode for device {device} to {mode}: {e}", "red")
                    continue
        except Exception as e:
            cprint(f"Error toggling PPCIE mode: {e}", "red")
            return None






def toggle_cc_mode(mode: str):
    cc_manager = ConfidentialComputeManager()
    cc_manager.toggle_device_mode(mode)
    time.sleep(10)
    cc_manager.toggle_ppcie_mode(mode)


