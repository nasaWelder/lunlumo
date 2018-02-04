# wallet_expect.py library for automating cli wallet
# Copyright (C) 2017-2018  u/NASA_Welder
"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from __future__ import print_function
import sys
if sys.version_info < (3,):
    ENCODING = None
    def b(x):
        return x
else:
    #import codecs
    ENCODING = "utf-8"
    def b(x):
        #return codecs.latin_1_encode(x)[0]
        return x.decode("utf-8")

import pexpect
import os
import os.path
import time
import getpass

# ./monero-wallet-cli --wallet-file testview --testnet --daemon-address testnet.kasisto.io:28081 --command transfer A16nFcW5XuU6Hm2owV4g277yWjjY6cVZy5YgE15HS6C8JujtUUP51jP7pBECqk78QW8K78yNx9LB4iB8jY3vL8vw3JhiQuX 1

MONERO_DIR = "/home/devarea/bin/monero-gui-v0.11.1.0/"

WALLET_SYNCED_PROMPT    = r"\[wallet [0-9A-Za-z]{6}\]:"                 # [wallet 9wXvk8]:
WALLET_NODAEMON_PROMPT  = r"\[wallet [0-9A-Za-z]{6} \(no daemon\)\]:"     # [wallet 9wXvk8 (no daemon)]:
WALLET_PASSWORD_PROMPT  = r"Wallet password:"
WALLET_ISOKAY_PROMPT    = r"Is this okay\?\s+\(Y/Yes/N/No\):"            # "Is this okay?  (Y/Yes/N/No):"   #submit_transfer has  "Is this okay? (Y/Yes/N/No):"



class Wallet(object):
    def __init__(self, walletFile = None, password = '',daemonAddress = None, daemonHost = None,testnet = False,cold = True,gui=False):
        self.gui = gui
        if self.gui:
            if sys.version_info < (3,):
                self.gui = False # not test python 2 tkinter yet
            else:
                import tkinter.messagebox as message
                global message

        self.ready = False
        self.TIMEOUT = 300   # may need to bump this up if using new wallets
        self.walletArgs = []

        self.walletFile = walletFile.split()[0]  #split is to defeat sneaky attack
        if not walletFile:
            raise Exception("Argument Error: Currently, this library does not automate wallet generation... maybe if you ask nicely we can add it")
        if not password:
            password = getpass.getpass(prompt="Password for %s:"%walletFile)
        self.walletArgs.extend(["--wallet-file",walletFile])

        self.rawPassword = password
        self.password = '"' + password + '"'
        self.walletArgs.extend(["--password",self.password])

        self.testnet = testnet
        if self.testnet:
            self.walletArgs.append("--testnet")

        if daemonAddress and daemonHost:
            # can only specify one
            raise Exception("Argument Error: Cannot specify both 'daemonAddress' and 'daemonHost', please choose one.")
        elif not daemonAddress and not daemonHost:
            pass   #start local daemon (will be annoying if not synced)
            self.daemonArg = None   #don't include in wallet start command
        elif daemonAddress:
            self.daemonArg = ["--daemon-address",daemonAddress.split()[0],"--trusted-daemon"]  #split is to defeat sneaky attack
        elif daemonHost:
            self.daemonArg = ["--daemon-host",daemonHost.split()[0],"--trusted-daemon"]  #split is to defeat sneaky attack

        if cold:
            self.cold = True
            if self.daemonArg: raise Exception("Argument Error: Cannot specify daemon if this should be a cold wallet")
        else:
            self.cold = False
            if self.daemonArg:
                self.walletArgs.extend(self.daemonArg)
        if self.testnet:
            print("".join(arg + ' ' for arg in self.walletArgs))

        self.startWallet()

    def haltAndCatchFire(self,err):
        print(err)
        print(self.child.before, self.child.after)
        print(str(self.child))
        self.stopWallet()
        raise Exception(err)

    def stopWallet(self):
        try:
            self.walletCmd("exit")
        except Exception as e:
            if "End Of File (EOF)" in str(e):
                print(" exit\r\n<exited wallet: %s>\r\n"% self.walletFile)
                return
        if not self.child.isalive(): return
        time.sleep(13)
        if self.child.isalive():
            self.child.terminate(force=True)

    def startWallet(self):
        self.cmdMonero = os.path.join(MONERO_DIR,"monero-wallet-cli")
        if self.testnet: print("self.cmdMonero: ",self.cmdMonero)
        self.child = pexpect.spawn(self.cmdMonero + ' ' + ''.join(arg + ' ' for arg in self.walletArgs),encoding= ENCODING)
        i = self.child.expect([pexpect.TIMEOUT, WALLET_SYNCED_PROMPT, WALLET_NODAEMON_PROMPT], timeout = self.TIMEOUT)
        if i == 0: # Timeout
            self.haltAndCatchFire('TIMEOUT ERROR! Wallet did not return within TIMEOUT limit %s' % self.TIMEOUT)

        elif i == 1: # WALLET_SYNCED_PROMPT
            if self.cold:
                self.haltAndCatchFire('ROGUE SYNC ERROR! Cold Wallet was asked for, but the wallet found a daemon! YOUR SEED COULD BE COMPROMISED!!')
            else: # hot waller, expected (pun intended)
                self.ready = True

        elif i ==2: # WALLET_NODAEMON_PROMPT
            if not self.cold:
                self.haltAndCatchFire('No Sync Error: wallet returned without finding daemon')
            else:
                self.ready = True
        self.TIMEOUT = 45
        print(self.child.before,end="")
        print(self.child.after,end="")


    def get_view_only_info(self,verbose=True):
        viewSecret= self.walletCmd("viewkey",verbose=verbose).split()[1]
        thisWalletAddress = self.walletCmd("address",verbose=verbose).split()[1]
        return viewSecret, thisWalletAddress

    def export_outputs(self,outputsFileName = "outputs_from_viewonly",verbose = True):
        # TODO check filename string validity
        info = self.walletCmd("export_outputs %s" % outputsFileName,verbose = True)
        if not ("Outputs exported to %s" % outputsFileName) in info:
            self.haltAndCatchFire('Wallet Error! unexpected result in export_outputs("%s"): %s' % (outputsFileName, info))
        else:
            return outputsFileName,info

    def import_outputs(self,outputsFileName = "outputs_from_viewonly",verbose = True):
        # TODO check filename string validity
        info = self.walletCmd("import_outputs %s" % outputsFileName,verbose = True)
        numOutputs = info.strip().split()[0]
        if not "outputs imported" in info:
            self.haltAndCatchFire('Wallet Error! unexpected result in import_outputs("%s"): %s' % (outputsFileName, info))
        else:
            return numOutputs,info

    def export_key_images(self,keyImagesFileName = "key_images_from_cold_wallet",verbose = True):
        # TODO check filename string validity
        info = self.walletCmd("export_key_images %s" % keyImagesFileName,verbose = True)
        if not ("Signed key images exported to %s" % keyImagesFileName) in info:
            self.haltAndCatchFire('Wallet Error! unexpected result in export_key_images("%s"): %s' % (keyImagesFileName, info))
        else:
            return keyImagesFileName,info

    def import_key_images(self,keyImagesFileName = "key_images_from_cold_wallet",verbose = True):
        # TODO check filename string validity
        info = self.walletCmd("import_key_images %s" % keyImagesFileName,verbose = True)
        # Signed key images imported to height 1091104, 25.482444280000 spent, 11.000000000000 unspent
        if not "Signed key images imported to height" in info:
            self.haltAndCatchFire('Wallet Error! unexpected result in import_key_images("%s"): %s' % (keyImagesFileName, info))
        else:
            height = info.strip().split(",")[0].split()[-1]
            spent  = info.strip().split(",")[1].split()[0].strip()
            unspent  = info.strip().split(",")[2].split()[0].strip()
            return height,spent,unspent,info

    def transfer(self,destAddress, amount, priority = "unimportant",autoConfirm = 0, verbose = True ):
        tx_string = 'transfer %s %s %s' % (priority,destAddress,amount)
        info = self.walletCmd(tx_string,verbose=verbose,autoConfirm = autoConfirm)
        if not self.cold:
            # saves unsigned_monero_tx to cwd
            if not "Unsigned transaction(s) successfully written to file:" in info:
                self.haltAndCatchFire('Wallet Error! unexpected result in transfer("%s"): %s' % (tx_string, info))
        return info

    def sign_transfer(self,autoConfirm = 0, verbose = True):
        # looks for unsigned_monero_tx in cwd
        info = self.walletCmd("sign_transfer",verbose=verbose,autoConfirm = autoConfirm)
        # saves signed_monero_tx to cwd
        if not "Transaction successfully signed to file signed_monero_tx" in info:
            self.haltAndCatchFire('Wallet Error! unexpected result in sign_transfer: %s' % (info))
        return info

    def submit_transfer(self,autoConfirm = 0, verbose = True):
        # looks for signed_monero_tx in cwd
        if self.cold:
            self.haltAndCatchFire('Wallet Error! Cold wallet cannot submit_transfer!')
        info = self.walletCmd("submit_transfer",verbose=verbose,autoConfirm = autoConfirm)
        if not "Money successfully sent" in info:
            self.haltAndCatchFire('Wallet Error! unexpected result in sign_transfer: %s' % (info))
        return info

    def transferViewOnly(self,destAddress, amount, priority = "unimportant",autoConfirm = 0, verbose = True):
        outFile,info = self.export_outputs(outFileName = "outputs_from_viewonly")

    def walletCmd(self,cmd,autoConfirm = False,verbose = True,NOP = False):
        self.filterBuffer = ""
        self.ready = False
        #if verbose: print(self.child.before,self.child.after)
        if not NOP: self.child.sendline(cmd)
        i = self.child.expect([pexpect.TIMEOUT, WALLET_SYNCED_PROMPT, WALLET_NODAEMON_PROMPT,WALLET_PASSWORD_PROMPT,WALLET_ISOKAY_PROMPT], timeout = self.TIMEOUT)
        if i == 0: # Timeout
            self.haltAndCatchFire('TIMEOUT ERROR! Wallet did not return within TIMEOUT limit %s' % self.TIMEOUT)

        elif i == 1: # WALLET_SYNCED_PROMPT
            if self.cold:
                self.haltAndCatchFire('ROGUE SYNC ERROR! Cold Wallet was asked for, but the wallet found a daemon! YOUR SEED COULD BE COMPROMISED!!')
            else: # hot waller, expected (pun intended)
                self.ready = True

        elif i ==2: # WALLET_NODAEMON_PROMPT
            if not self.cold:
                self.haltAndCatchFire('No Sync Error: wallet returned without finding daemon')
            else:
                self.ready = True
        elif i ==3:  #password Prompt
            if verbose:
                print(self.child.before + WALLET_PASSWORD_PROMPT + " <password supplied>",end="")
            self.walletCmd(self.rawPassword,autoConfirm,verbose=False)

        elif i ==4:   # WALLET_ISOKAY_PROMPT
            #if verbose:
                #print(self.child.before + self.child.after)
            if self.getConfirmation(self.child.before.rstrip() +" " + self.child.after.rstrip(),autoConfirm,verbose):
                self.ready = True

        if not self.ready:
            self.haltAndCatchFire("Automation Deadend: Wallet took us to somewhere we didn't plan")
        else:
            self.filterBuffer = ""
            if verbose:
                print(self.child.before,end="")
                print(self.child.after,end="")
            return self.child.before

    def getConfirmation(self,context,autoConfirm,verbose):
        self.autoConfirm = autoConfirm
        if autoConfirm:
            print(context + " <auto-confirming>",end="")
            self.walletCmd("y",autoConfirm,verbose=False)
            return self.ready
        elif self.gui:
            print(context + " <waiting for user>",end="")
            if message.askokcancel("User Confirmation",context):
                self.walletCmd("y",autoConfirm,verbose=False)
                return self.ready
            else:
                self.haltAndCatchFire("User Exit: user hit cancel on: %s" % context)
        else:
            try:
                print("\n"+"#"*80)
                print("#"*80)
                print("\r\nHUMAN INTERACTION NEEDED!\r\n")
                print("\r\n" + context,end="")
                self.child.interact(output_filter = self.confirmationFilter)
            except Exception as e:
                print("\r\n END OF HUMAN INTERACTION \r\n")
                print("#"*80)
                print("#"*80)
                if not "ONPURPOSE" == str(e).strip():
                    raise

            #print("after interact")
            self.walletCmd("dummy_command",self.autoConfirm,NOP = True,verbose=False)
            #self.haltAndCatchFire("Automation Deadend: haven't coded confirmation by live human")
            return self.ready

    def confirmationFilter(self,s):
        #print("buffer",self.filterBuffer)
        self.filterBuffer += b(s)
        if  "\r\n" in self.filterBuffer:
            if self.filterBuffer.lower() in ["y\r\n", "yes\r\n","y","yes"]:
                 self.filterBuffer = ""
                 raise Exception("ONPURPOSE")
            else:
                self.haltAndCatchFire("User Exit: user supplied input that killed automation: %s" % self.filterBuffer)
            self.filterBuffer = ""
        return s





if __name__ == "__main__":
    hotwallet = Wallet(walletFile = os.path.join(MONERO_DIR,"testview"), password = '',daemonAddress = "testnet.kasisto.io:28081",testnet = True,cold = False)
    coldwallet = Wallet(walletFile = os.path.join(MONERO_DIR,"testnet"), password = '',testnet = True,cold = True,gui=True)
    hsleep = 2

    hotwallet.export_outputs()
    time.sleep(hsleep)
    coldwallet.import_outputs()
    time.sleep(hsleep)
    coldwallet.export_key_images()
    time.sleep(hsleep)
    hotwallet.import_key_images()
    time.sleep(hsleep)
    hotwallet.transfer(priority = "unimportant", destAddress = "A16nFcW5XuU6Hm2owV4g277yWjjY6cVZy5YgE15HS6C8JujtUUP51jP7pBECqk78QW8K78yNx9LB4iB8jY3vL8vw3JhiQuX", amount = ".45",autoConfirm = 1)
    time.sleep(hsleep)
    coldwallet.sign_transfer(autoConfirm = 0)
    time.sleep(hsleep)
    hotwallet.submit_transfer(autoConfirm = 1)
    time.sleep(hsleep)
    #print(openwallet.child.before)
    hotwallet.stopWallet()
    coldwallet.stopWallet()




