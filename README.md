# lunlumo
A python3 GUI for Monero that will support automated cold transaction signing via QR code streams.

by u/NASA_Welder

email: nasawelder@protonmail.com

## Dependencies
lunlumo wraps the monero-wallet-cli. You must download the offical binaries from www.getmonero.org.
Note: The goal is to eventually provide all dependencies via this github account for simpler trust verification.

The following assumes Ubuntu Mate:
* sudo -H pip3 install Pillow --upgrade # >= 3.4
* sudo apt-get install libzbar0 libzbar-dev
* sudo -H pip3 install setuptools --upgrade
* sudo -H pip3 install zbarlight
* pip3 install --upgrade pip
* sudo -H pip3 install pygame

## Hardware / Setup
The GUI can be used standalone, on an internet connected computer for normal transaction usage, however, lunlumo's intended purpose is to allow cold transaction signing via QR code stream between 2 computers.

#### Internet Connected Linux Computer
* running lunlumo
* watch-only wallet
* v4L webcam

#### Air-gapped Computer (or Raspberry Pi)
* running lunlumo
* full wallet
* v4L webcam (or Raspberry Pi Camera)

##### Tested Webcams
* Logitech c170 ($20)

## Download
    git clone <this repository>
## Usage
    cd lunlumo/
    python3 lunlumo.py /path/to/monero-wallet-cli
## Babysitting fund

Toddlers and python don't mix.

Monero:
43cE9dmYdWvA5YaST7JcEb1BcDSGaqUPPYQdWnUCspd33LL5L71P3XEjZ8X6dsb4wHHRscRSFCiiT8dRk5nbr3tkUs1afvP
