# lunlumo
A python3 GUI for Monero that with automated cold transaction signing via QR code streams.

by u/NASA_Welder

email: nasawelder@protonmail.com

## Current Features

* Full Monero GUI for desktop Linux and Raspberry Pi (armv7)
* Automated Cold signing via QR code stream + webcam between Hot(watch-only wallet) and air-gapped (full wallet) machines
* Send / Receive normally via daemon connection with Hot full wallet
* Account Switching
* Subaddress selection and generation
* Comes with a python wallet-cli wrapper library that can be used standalone for your other needs (API not stable yet, but certainly useable)

## Roadmap

* Multisig cold-generation and cold-signing automation
* Wallet meta-data transfer and backup (saving/transferring address book and subaddress info separately from keys for transfer/backup/merge)
* GUI features added for monero cli functions
* Scan address via QR code. (Just hadn't gotten to this, yet)
* Integration with android / iOS apps
* arbitrary file transfer via QR in a standalone library
* Formal API for cli-wrapper library
* Bundle all dependencies with source for easier trust verification.


## Dependencies
lunlumo wraps the monero-wallet-cli. You must download the offical binaries from www.getmonero.org
Note: The goal is to eventually provide all dependencies via this github account for simpler trust verification.

The following assumes Ubuntu Mate:
* sudo apt-get install python3-tk       # this comes standard on some distributions, including ubuntu mate for raspi.
* sudo -H pip3 install Pillow --upgrade # >= 3.4
* sudo apt-get install libzbar0 libzbar-dev
* sudo -H pip3 install setuptools --upgrade
* sudo -H pip3 install zbarlight
* pip3 install --upgrade pip
* sudo apt-get build-dep python-pygame
* sudo apt install python-dev
* sudo -H pip3 install pygame
* sudo usermod -a -G video timepi  # raspi only

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
* Dell integrated webcam from 6 year old laptop

## Download
    git clone <this repository>

## Usage
    cd lunlumo/
    python3 lunlumo.py /path/to/monero-wallet-cli

## Babysitting fund

Toddlers and python don't mix.

Monero:
43cE9dmYdWvA5YaST7JcEb1BcDSGaqUPPYQdWnUCspd33LL5L71P3XEjZ8X6dsb4wHHRscRSFCiiT8dRk5nbr3tkUs1afvP
