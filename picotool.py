import subprocess
import os

class Picotool:
    def __init__(self):
        self.nuke_file = "flash_nuke.uf2"

    def is_installed(self):
        try:
            subprocess.check_output(["picotool"])
            return True
        except:
            return False

    def picotool_info(self):
        try:
            output = subprocess.check_output(
                ["picotool", "info"])
            lines = output.decode().strip().split("\n")
            info = {}
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    info[key.strip()] = value.strip()

            return info
        except subprocess.CalledProcessError:
            return None

    def get_program_name(self):
        info = self.picotool_info()
        if not info:
            return None
        return info.get("name")

    def nuke_firmware(self):
        result = self.flash_firmware(self.nuke_file)
        return result

    def flash_firmware(self, firmware_file):
        firmware_file = os.path.join("firmware", firmware_file)

        if not os.path.exists(firmware_file):
            print("FATAL: Firmware file does not exist")
            return False

        try:
            subprocess.check_output(
                ["picotool", "load", "-v", "-x", firmware_file])
            return True
        except subprocess.CalledProcessError:
            return False
