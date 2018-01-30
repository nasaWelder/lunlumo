# wallet-expect.py library for automating cli wallet
# Copyright (C) 2017-2018  u/NASA_Welder>
"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from __future__ import print_function


import pexpect
import os
import os.path
import time


# ./monero-wallet-cli --wallet-file testview --testnet --daemon-address testnet.kasisto.io:28081 --command transfer A16nFcW5XuU6Hm2owV4g277yWjjY6cVZy5YgE15HS6C8JujtUUP51jP7pBECqk78QW8K78yNx9LB4iB8jY3vL8vw3JhiQuX 1

MONERO_DIR = "/home/devarea/bin/monero-gui-v0.11.1.0/"

WALLET_SYNCED_PROMPT    = r"\[wallet [0-9A-Za-z]{6}\]:"                 # [wallet 9wXvk8]:
WALLET_NODAEMON_PROMPT  = r"\[wallet [0-9A-Za-z]{6} \(no daemon\)\]:"     # [wallet 9wXvk8 (no daemon)]:
WALLET_PASSWORD_PROMPT  = r"Wallet password:"
WALLET_ISOKAY_PROMPT    = r"Is this okay\?  \(Y/Yes/N/No\):"            # "Is this okay?  (Y/Yes/N/No):"


class Wallet(object):
    def __init__(self, walletFile = None, password = '',daemonAddress = None, daemonHost = None,testnet = False,cold = True):
        self.ready = False
        self.TIMEOUT = 45
        self.walletArgs = []

        self.walletFile = walletFile.split()[0]  #split is to defeat sneaky attack
        if not walletFile:
            raise Exception("Argument Error: Currently, this library does not automate wallet generation... maybe if you ask nicely we can add it")
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
                print(" exit\r\n<exited wallet>\r\n")
                return
        if not self.child.isalive(): return
        time.sleep(13)
        if self.child.isalive():
            self.child.terminate(force=True)

    def startWallet(self):
        self.cmdMonero = os.path.join(MONERO_DIR,"monero-wallet-cli")
        if self.testnet: print("self.cmdMonero: ",self.cmdMonero)
        self.child = pexpect.spawn(self.cmdMonero + ' ' + ''.join(arg + ' ' for arg in self.walletArgs))
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

        print(self.child.before,end="")
        print(self.child.after,end="")


    def transfer(self,destAddress, amount, priority = "unimportant", ):
        tx_string = 'transfer %s %s %s' % (priority,destAddress,amount)
        self.child.sendline(tx_string)

    def getViewOnly(self):
        viewSecret= self.walletCmd("viewkey").split()[1]
        thisWalletAddress = self.walletCmd("address").split()[1]
        return viewSecret, thisWalletAddress


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
            if self.getConfirmation(self.child.before.rstrip() + self.child.after.rstrip(),autoConfirm,verbose):
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
        else:
            try:
                print("#"*80)
                print("#"*80)
                print("\r\n\r\nHUMAN INTERACTION NEEDED!\r\n")
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
        self.filterBuffer += s
        if  "\r\n" in self.filterBuffer:
            if self.filterBuffer.lower() in ["y\r\n", "yes\r\n","y","yes"]:
                 self.filterBuffer = ""
                 raise Exception("ONPURPOSE")
            else:
                self.haltAndCatchFire("User Exit: user supplied input that killed automation: %s" % self.filterBuffer)
            self.filterBuffer = ""
        return s





if __name__ == "__main__":
    openwallet = Wallet(walletFile = os.path.join(MONERO_DIR,"testview"), password = '',daemonAddress = "testnet.kasisto.io:28081",testnet = True,cold = False)
    #openwallet = Wallet(walletFile = os.path.join(MONERO_DIR,"testnet"), password = '',testnet = True,cold = True)
    openwallet.getViewOnly()
    openwallet.walletCmd("transfer unimportant A16nFcW5XuU6Hm2owV4g277yWjjY6cVZy5YgE15HS6C8JujtUUP51jP7pBECqk78QW8K78yNx9LB4iB8jY3vL8vw3JhiQuX .45",autoConfirm = 1)
    #print(openwallet.child.before)
    openwallet.stopWallet()



