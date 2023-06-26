import os
import platform
import subprocess
import time
import sys
import threading
from picotool import Picotool
from github import Github
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label

picotool = Picotool()
github = Github()
selected_firmware = None
detection_thread = None

if platform.system() == 'Linux':
    import pyudev

class LabelItem(ListItem):
    def __init__(self, label: str, file_name: str, browser_download_url: str) -> None:
        super().__init__()
        self.label = label
        self.file_name = file_name
        self.browser_download_url = browser_download_url

    def compose(self) -> ComposeResult:
        yield Label(self.label)
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

class GP2040FlasherApp(App):
    TITLE = "GP2040 Flasher"
    SUB_TITLE = "Select a firmware to flash"
    CSS_PATH = "css/list_view.css"

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit")
    ]

    def __init__(self):
        super().__init__()
        self.running = True

    def flash_pico(self):
        global selected_firmware
        if selected_firmware is not None:
            if picotool.get_program_name() is None:
                print("Flashing firmware...")
                result = picotool.flash_firmware(selected_firmware)

                if result:
                    print("Firmware flashed.")
                    print("")
                    # Wait for the Pico to reboot
                    time.sleep(2)
                else:
                    print("Firmware flash failed.")
                    print("")
                    self.running = False
            else:
                print("Nuking firmware...")
                picotool.nuke_firmware()
                print("Firmware nuked.")
                print("")
                # Wait for the Pico to reboot
                time.sleep(2)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)

        version, release_date, firmware_files = github.get_latest_release_info()

        if firmware_files is not None:
            items = []

            for firmware_file in firmware_files:
                version, name = github.get_info_from_firmware_file_name(firmware_file["name"])
                items.append(LabelItem(f"{name} ({version})", firmware_file["name"], firmware_file["browser_download_url"]))
            yield ListView(*items, classes="box")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        global selected_firmware

        print("Downloading firmware...")
        selected_firmware = github.download_file(event.item.browser_download_url)
        print("Firmware downloaded.")
        print("")
        print(selected_firmware)

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def action_quit(self) -> None:
        self.running = False
        sys.exit()

def flash_drive_handler(action, device, app):
    device_name = device.sys_name.split('/')[-1]
    if action == 'add' and device_name == "sda" and device.get('ID_VENDOR') == 'RPI' and device.get('ID_MODEL') == 'RP2':
        print("Pico detected (Linux)")
        print("")
        app.flash_pico()

def pico_detection_thread(app):
    while app.running:
        if detect_pico():
            print("Pico detected.")
            print("")
            app.flash_pico()
        time.sleep(1)

def main():
    global picotool
    global detection_thread

    app = GP2040FlasherApp()

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
        observer = pyudev.MonitorObserver(monitor, flash_drive_handler, app=app)
        observer.start()

    # Start pico detection thread
    detection_thread = threading.Thread(target=pico_detection_thread, args=(app,))
    detection_thread.start()

    app.run()
if __name__ == '__main__':
    main()
