import os
import platform
import time
import sys
from picotool import Picotool
from github import Github
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label
from textual import events
from textual.screen import Screen

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

class SelectionScreen(Screen):
    TITLE = "GP2040 Flasher 2"
    SUB_TITLE = "Select a firmware to flash"
    CSS_PATH = "css/list_view.css"

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
        app.switch_screen(FlashingScreen())

class FlashingScreen(Screen):
    def on_mount(self) -> None:
        if platform.system() == 'Linux':
            context = pyudev.Context()
            monitor = pyudev.Monitor.from_netlink(context)
            monitor.filter_by('block')
            observer = pyudev.MonitorObserver(monitor, self.flash_drive_handler)
            observer.start()
        else:
            print("Windows or Mac OS, not using udev")
            # threading.Thread(target=self.wait_for_pico_detection).start()
            # self.wait_for_pico_detection()
            self.run_worker(self.wait_for_pico_detection(), start=True, exclusive=True)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Label("Selected firmware: " + selected_firmware)
        yield Label("Waiting for Pico to be detected...", id="waiting-status")
        yield Footer()

    def flash_drive_handler(self, action, device):
        device_name = device.sys_name.split('/')[-1]
        if action == 'add' and device_name == "sda" and device.get('ID_VENDOR') == 'RPI' and device.get('ID_MODEL') == 'RP2':
            print("Pico detected.")
            print("Flashing firmware...")
            flash_pico(self)

    def wait_for_pico_detection(self):
        while True:
            if detect_pico():
                print("Pico detected.")
                print("Flashing firmware...")
                flash_pico(self)
            time.sleep(1)

class LayoutApp(App):
    TITLE = "GP2040 Flasher"

    def __init__(self):
        super().__init__()
        self.running = True

    def on_mount(self) -> None:
        self.push_screen(SelectionScreen())

    async def on_key(self, event: events.Key) -> None:
        if event.key == "q":
            self.running = False
            sys.exit()

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

def flash_pico(self):
    if selected_firmware is not None:
        if picotool.get_program_name() is None:
            print("Flashing firmware[blink]_[/]")
            if picotool.flash_firmware(selected_firmware):
                print("Firmware flashed successfully.")
                print("")
                # Wait for the Pico to reboot
                time.sleep(2)
            else:
                print("Firmware flash failed.")
                print("")
                app.running = False
                sys.exit()
        else:
            print("Nuking firmware...")
            picotool.nuke_firmware()
            print("Firmware nuked.")
            print("")
            # Wait for the Pico to reboot
            time.sleep(2)
    else:
        print("No firmware selected.")
        app.running = False
        sys.exit()

def main():
    if picotool.is_installed() is False:
        print("FATAL: picotool is not installed")
        if platform.system() == 'Windows':
            print("See: https://github.com/raspberrypi/pico-setup-windows/releases")
        elif platform.system() == 'Darwin':
            print("Run: brew install picotool")
        else:
            print("See: https://github.com/raspberrypi/pico-setup")
        return

    global app
    app = LayoutApp()

    app.run()

if __name__ == "__main__":
    main()
