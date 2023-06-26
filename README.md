# GP2040-Flasher

> A cross-platform app to flash the RP2040 chip with firmware from the [GP2040-CE](https://github.com/OpenStickCommunity/GP2040-CE) project.

The only dependency is [picotool](https://github.com/raspberrypi/picotool) and Python on Mac, see platform specific notes below for requirements on Windows and Linux.

Currently, this is a PoC, working on all systems but the firmware to flash is hardcoded. This will be fixed soon by adding a Textual "GUI" and fetching releases from the GP2040-CE repository.

## Platform specific notes

### Windows

Windows requires win32api to be installed. (`pip install pywin32`)

### Linux

Linux requires pyudev to be installed. (`pip install pyudev`)

## Usage

1. Clone this repository
2. Run `python main.py`

If picotool is missing you will be given OS-specific instructions on how to install it.

## See also

[GP2040-Flasher-Pi](https://github.com/SavageCore/GP2040-Flasher-Pi) - Another version of this app designed to run on a Raspberry Pi with a 2.8" TFT display.

[monkeymademe's gist](https://gist.github.com/monkeymademe/82a575c63ee4a52c83a5aa0f6793307b) - A gist that inspired this project.
