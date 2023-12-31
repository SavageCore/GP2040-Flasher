import os
import platform
import subprocess
import time
from picotool import Picotool

picotool = Picotool()
running = True

if platform.system() == 'Linux':
    import pyudev

def detect_pico():
    drives = []
    if platform.system() == 'Windows':
        import win32api
        win_drives = win32api.GetLogicalDriveStrings()
        win_drives =  win_drives.split('\000')[:-1]
        for d in win_drives:
            volume = win32api.GetVolumeInformation(d)
            if volume[0] == 'RPI-RP2':
                drives.append(d)

    elif platform.system() == 'Darwin':
        drives = ['/Volumes/RPI-RP2']

    for drive in drives:
        if os.path.exists(drive):
            return True
    return False

def flash_drive_handler(action, device):
    device_name = device.sys_name.split('/')[-1]
    if action == 'add' and device_name == "sda" and device.get('ID_VENDOR') == 'RPI' and device.get('ID_MODEL') == 'RP2':
        print("Pico detected (Linux)")
        print("")
        flash_pico()

def flash_pico():
    global picotool
    global running

    if picotool.get_program_name() is None:
        print("Flashing firmware...")
        result = picotool.flash_firmware('GP2040-CE_0.7.2_Stress.uf2')

        if result:
            print("Firmware flashed.")
            print("")
            # Wait for the Pico to reboot
            time.sleep(2)
        else:
            print("Firmware flash failed.")
            print("")
            running = False
    else:
        print("Nuking firmware...")
        picotool.nuke_firmware()
        print("Firmware nuked.")
        print("")
        # Wait for the Pico to reboot
        time.sleep(2)

def main():
    global picotool
    global running

    if picotool.is_installed() is False:
        print("FATAL: picotool is not installed")
        if platform.system() == 'Windows':
            print("See: https://github.com/raspberrypi/pico-setup-windows/releases")
        elif platform.system() == 'Darwin':
            print("Run: brew install picotool")
        else:
            print("See: https://github.com/raspberrypi/pico-setup")
        return

    if platform.system() == 'Linux':
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by('block')
        observer = pyudev.MonitorObserver(monitor, flash_drive_handler)
        observer.start()


    try:
        while running:
            if detect_pico():
                print("Pico detected.")
                print("")
                flash_pico()
            # else:
                # print("Raspberry Pi Pico not detected.")
    except:
            print("Program terminated by user.")

if __name__ == '__main__':
    main()
