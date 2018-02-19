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
import re

# ./monero-wallet-cli --wallet-file testview --testnet --daemon-address testnet.kasisto.io:28081 --command transfer A16nFcW5XuU6Hm2owV4g277yWjjY6cVZy5YgE15HS6C8JujtUUP51jP7pBECqk78QW8K78yNx9LB4iB8jY3vL8vw3JhiQuX 1

MONERO_DIR = "/home/devarea/bin/monero-gui-v0.11.1.0/"
MONERO_DIR = "/home/devarea/bin/new_monero/"

WALLET_SYNCED_PROMPT    = r"\[wallet [0-9A-Za-z]{6}\]:"                 # [wallet 9wXvk8]:
WALLET_NODAEMON_PROMPT  = r"\[wallet [0-9A-Za-z]{6} \(no daemon\)\]:"     # [wallet 9wXvk8 (no daemon)]:
WALLET_PASSWORD_PROMPT  = r"Wallet password:"
WALLET_ISOKAY_PROMPT    = r"Is this okay\?\s+\(Y/Yes/N/No\):"            # "Is this okay?  (Y/Yes/N/No):"   #submit_transfer has  "Is this okay? (Y/Yes/N/No):"
WALLET_IMPOSTER_PROMPT  = r"\[wallet [0-9A-Za-z]{6}( \((no daemon|out of sync)\))?\]: \x1b\[0m\r\x1b\[K"
WALLET_FLUFF_PROMPT     = r"(\[wallet [0-9A-Za-z]{6}( \((no daemon|out of sync)\))?\]:)? ?(\r)?\x1b\[(K|[0-9;]+m)"
WALLET_ALL_PROMPT       = r"\[wallet [0-9A-Za-z]{6}( \((no daemon|out of sync)\))?\]:"
WALLET_LINE_CLEAR       = r"\x1b\[0m\r\x1b\[K"
WALLET_COLOR            = r"\x1b\[[0-9;]+m"
                           #\\x1b\[0m\\r\\x1b\[K

class Wallet(object):
    def __init__(self, walletFile = None, password = '',daemonAddress = None, daemonHost = None,testnet = False,cold = True,gui=False,postHydra = False,debug = True):
        self.gui = gui
        self._debug = debug
        self.postHydra = postHydra
        if self.gui: # TODO remove this as app will handle
            if sys.version_info < (3,):
                self.gui = False # not test python 2 tkinter yet
            else:
                import tkinter.messagebox as message
                global message

        self.ready = False
        self.TIMEOUT = 300   # may need to bump this up if using new wallets
        self.walletArgs = []

        # helium hydra
        ######################################################
        self.patterns = {}
        self.patterns.update({"address" : re.compile(r"[489AB][a-zA-Z0-9]{94}")}) # TODO remove chars not found in addresses, testnet subaddresses?
        self.patterns.update({"address_book" : re.compile(r"Index: [0-9]+\s+Address: [489A][a-zA-Z0-9]{94}\s+Payment ID: <[0-9]+>\s+Description:[\S ]*[\r\n]*")})
        self.patterns.update({"address_book_parts" : re.compile(r"Index: (?P<index>[0-9]+)\s+Address: (?P<address>[489A][a-zA-Z0-9]{94})\s+Payment ID: <(?P<payid>[0-9]+)>\s+Description:(?P<desc>[\S ]*)[\r\n]*")})
        self.patterns.update({"balance": re.compile(r"Balance: (?P<balance>[0-9\.]+), unlocked balance: (?P<unlocked>[0-9\.]+)")})


        if self.postHydra:
            self.patterns.update({"address" : re.compile(r"[489AB][a-zA-Z0-9]{94}")}) # TODO remove chars not found in addresses, testnet subaddresses?
            self.patterns.update({"address_book" : re.compile(r"Index: [0-9]+\s+Address: [489AB][a-zA-Z0-9]{94}\s+Payment ID: <[0-9]+>\s+Description:[\S ]*[\r\n]*")})
            self.patterns.update({"address_book_parts" : re.compile(r"Index: (?P<index>[0-9]+)\s+Address: (?P<address>[489AB][a-zA-Z0-9]{94})\s+Payment ID: <(?P<payid>[0-9]+)>\s+Description:(?P<desc>[\S ]*)[\r\n]*")})
            self.patterns.update({"balance": re.compile(r"Balance: (?P<balance>[0-9\.]+), unlocked balance: (?P<unlocked>[0-9\.]+)")})
            self.patterns.update({"status": re.compile(r"Refreshed[^\\]+")})

        #####################################################
        self.walletFile = walletFile.split()[0]  #split is to defeat sneaky attack
        if not walletFile:
            raise Exception("Argument Error: Currently, this library does not automate wallet generation... maybe if you ask nicely we can add it")
        if not password and not self.gui:
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

    def debug(self,title,msg):
        if self._debug:
            print("=================\nDEBUG: %s" % title)
            print(repr(msg))
            print("=================")

    def haltAndCatchFire(self,err):
        print(err)
        self.debug("Before",self.child.before)
        self.debug("After",self.child.after)

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
        i = self.child.expect([pexpect.EOF,pexpect.TIMEOUT, WALLET_SYNCED_PROMPT, WALLET_NODAEMON_PROMPT], timeout = self.TIMEOUT)
        if i == 0: # EOF
            print(self.child.before.replace("\x1b[0m","").replace("\x1b[1;31m","").replace("\x1b[1;37m",""))
            raise Exception(self.child.before.replace("\x1b[0m","").replace("\x1b[1;31m","").replace("\x1b[1;37m",""))
        elif i == 1: # Timeout
            self.haltAndCatchFire('TIMEOUT ERROR! Wallet did not return within TIMEOUT limit %s' % self.TIMEOUT)

        elif i == 2: # WALLET_SYNCED_PROMPT
            if self.cold:
                self.haltAndCatchFire('ROGUE SYNC ERROR! Cold Wallet was asked for, but the wallet found a daemon! YOUR SEED COULD BE COMPROMISED!!')
            else: # hot waller, expected (pun intended)
                self.ready = True

        elif i ==3: # WALLET_NODAEMON_PROMPT
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
        if self.postHydra:
            info = self.walletCmdHack(tx_string,verbose=verbose,timeout = 10,)
        else:
            info = self.walletCmd(tx_string,verbose=verbose,autoConfirm = autoConfirm)
        self.debug("transfer",info)
        #info = self.walletCmd(tx_string,verbose=verbose,autoConfirm = autoConfirm)
        if not self.cold:
            # saves unsigned_monero_tx to cwd
            if not "Unsigned transaction(s) successfully written to file:" in info or not "Transaction successfully submitted" in info:
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

    def status(self,verbose = True,refresh = False):
        if refresh:
            #self.walletCmd("refresh",verbose=verbose)
            self.child.sendline("refresh")
            time.sleep(.05)
        if self.postHydra:
            info = self.walletCmdHack("status",verbose=verbose,timeout = 15,faster = r"Refreshed[^\\]+")
            info = re.findall(self.patterns["status"],info)[-1]
        else:
            info = self.walletCmd("status",verbose=verbose)
        self.debug("status",info)
        info = info.replace("status","").replace("\r\n","")

        return info

    def balance(self,verbose = True):
        if self.postHydra:
            info = self.walletCmdHack("balance",verbose=verbose,timeout = 1,faster = r"nlock[^\\]+")
        else:
            info = self.walletCmd("balance",verbose=verbose)
        self.debug("balance",info)
        #info = info.replace("balance","",1).replace("\r\n","")
        match = self.patterns["balance"].search(info)
        if match:
            return match.group("balance"),match.group("unlocked")

        return "X.XXXXXXXXXXXX","X.XXXXXXXXXXXX"

    def address(self,verbose = True):
        if self.postHydra:
            info = self.walletCmdHack("address",verbose=verbose,)
        else:
            info = self.walletCmd("address",verbose=verbose)
        #info = self.walletCmd("address",verbose=verbose)
        self.debug("address",info)
        matches = re.findall(self.patterns["address"],info)
        #info = info.replace("address","",1).replace("\r\n","")
        return matches

    def address_book(self,verbose = True,add=None):
        #add should be a tuple (<address>,<description>|None)
        cmd = "address_book"
        if add:
            cmd += " add %s" % add[0]
            if add[1]: # the description (optional)
                cmd += " %s" % add[1]

        if self.postHydra:
            info = self.walletCmdHack("address_book",verbose=verbose,timeout=.6)
        else:
            info = self.walletCmd("address_book",verbose=verbose)
        #info = self.walletCmd(cmd,verbose=verbose)
        self.debug("address_book",info)
        entries = re.findall(self.patterns["address_book"],info)
        book = {}
        for e in entries:
            parts = self.patterns["address_book_parts"].match(e)
            entry = {"index":parts.group("index"),"address":parts.group("address"),"payid":parts.group("payid")}
            if parts.group("desc") == "":
                entry.update({"description":""})
            else:
                entry.update({"description":parts.group("desc")[1:]})
            entry.update({"menu": parts.group("index") + ": |" + parts.group("desc")[1:14] + "| " +  parts.group("address")[:8] + ".. <" + parts.group("payid")[:5] + "...>" })
            print("entry:")

            book.update({parts.group("index"):entry})
        #info = info.replace("address","",1).replace("\r\n","")

        return book
    #def transferViewOnly(self,destAddress, amount, priority = "unimportant",autoConfirm = 0, verbose = True):
    #
    ###########################################################################################################3
    def walletCmdHack(self,cmd,autoConfirm = False,verbose = True,NOP = False,timeout = 0.2,faster = r"THE_REGEX_EQUIV_OF_None_shlkjahdflkaj"):
        self.filterBuffer = ""
        self.ready = False
        self.hack_buffer = ""
        #if verbose: print(self.child.before,self.child.after)
        if not NOP:
            self.child.sendline(cmd)
        while 1:
            i = self.child.expect([pexpect.TIMEOUT, WALLET_IMPOSTER_PROMPT ,faster,WALLET_PASSWORD_PROMPT,WALLET_ISOKAY_PROMPT,pexpect.EOF], timeout = timeout)
            if i == 0: # Timeout: this is where we might think we're actually done
                #self.haltAndCatchFire('TIMEOUT ERROR! Wallet did not return within TIMEOUT limit %s' % self.TIMEOUT)
                self.debug("imposter timeout: %s"%cmd,self.child.before)
                self.hack_buffer += self.child.before
                self.child.sendline("get_to_the_prompt")
                self.debug("hack","get_to_the_prompt")
                k = self.child.expect([pexpect.TIMEOUT, "unknown command: get_to_the_prompt"], timeout = 2)
                if k == 0:
                    self.debug("HACK timeout: %s"%cmd,self.child.before)
                    self.haltAndCatchFire('TIMEOUT ERROR! Wallet cmd hack did not return within TIMEOUT limit')
                    break
                elif k == 1:
                    self.ready = True
                    break
            elif i == 1: # WALLET_IMPOSTER_PROMPT
                self.debug("got faux prompt: %s"%cmd,self.child.before)
                self.hack_buffer += self.child.before

            elif i ==2:  # faster
                self.debug("got faster: %s"%cmd,self.child.before + self.child.after)
                self.hack_buffer += self.child.before + self.child.after
                self.ready = True
                break

            elif i ==3:  #password Prompt
                self.debug("got password Prompt: %s"%cmd,self.child.before)
                if verbose:
                    print(self.child.before + WALLET_PASSWORD_PROMPT + " <password supplied>",end="")
                self.child.sendline(self.rawPassword)

            elif i ==4:   # WALLET_ISOKAY_PROMPT
                if verbose:
                    print(self.child.before + self.child.after)
                if self.gui:
                    if self.gui.confirm(self.child.before + self.child.after):
                        self.child.sendline("Y")
                    else:
                        self.child.sendline("N")
                        self.ready
                        break
                else:
                    self.child.sendline("Y")

            elif i ==5:   # EOF ...WTF
                self.debug("EOF Before",(self.child.before))
                self.debug("EOF After",(self.child.after))
                break

            else:
                self.debug("broke, got nothing: %s"%cmd,self.child.before)
                break

        self.debug("Final Hack Buffer: %s"%cmd,self.hack_buffer)
        self.filterBuffer = ""
        #final = self.hack_buffer.replace("\x1b[0m","").replace("\x1b[1;31m","").replace("\x1b[1;37m","").replace("\x1b[1;33m","").strip()
        final = re.sub(WALLET_ALL_PROMPT,'',self.hack_buffer)
        final = re.sub(WALLET_LINE_CLEAR,'',final)
        final = re.sub(WALLET_COLOR,'',final)
        self.hack_buffer = ""
        if verbose:
            print(self.child.before,end="")
            print(self.child.after,end="")
        if not self.ready:
            self.haltAndCatchFire("Automation Deadend: Wallet took us to somewhere we didn't plan")
        else:

            return final


    #############################################################################################################
    def walletCmd(self,cmd,autoConfirm = False,verbose = True,NOP = False,override = None):
        self.filterBuffer = ""
        self.ready = False
        #if verbose: print(self.child.before,self.child.after)
        if not NOP: self.child.sendline(cmd)
        if override:
            i = self.child.expect([pexpect.TIMEOUT,override], timeout = self.TIMEOUT)
            if i == 0: # Timeout
                self.haltAndCatchFire('TIMEOUT ERROR! Wallet did not return within TIMEOUT limit %s' % self.TIMEOUT)
            elif i == 1: # override
                self.ready = True
                if verbose:
                    print(self.child.before,end="")
                    print(self.child.after,end="")
                return self.child.after.replace("\x1b[0m","").replace("\x1b[1;31m","").replace("\x1b[1;37m","").replace("\x1b[1;33m","").strip()
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
            return self.child.before.replace("\x1b[0m","").replace("\x1b[1;31m","").replace("\x1b[1;37m","").replace("\x1b[1;33m","").strip()

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
    wallet = Wallet(walletFile = os.path.join(MONERO_DIR,"newtestview"), password = '',daemonHost="testnet.xmrchain.net", testnet = True,cold = 0,debug = True,postHydra = True)
    hsleep = 2
    time.sleep(hsleep)
    got = wallet.address()
    wallet.debug("result: address",got)
    time.sleep(hsleep)
    got = wallet.status()
    wallet.debug("result: status",got)
    time.sleep(hsleep)
    got = wallet.balance()
    wallet.debug("result: balance",got)
    time.sleep(hsleep)
    got = wallet.address_book()
    wallet.debug("result: address_book",got)

    got = wallet.transfer(priority = "unimportant", destAddress = "A16nFcW5XuU6Hm2owV4g277yWjjY6cVZy5YgE15HS6C8JujtUUP51jP7pBECqk78QW8K78yNx9LB4iB8jY3vL8vw3JhiQuX", amount = ".65",autoConfirm = 1)
    wallet.debug("result: transfer",got)
    wallet.stopWallet()

    """
    hotwallet = Wallet(walletFile = os.path.join(MONERO_DIR,"testview"), password = '',daemonAddress = "testnet.kasisto.io:28081",testnet = True,cold = False)
    coldwallet = Wallet(walletFile = os.path.join(MONERO_DIR,"testnet"), password = '',testnet = True,cold = True,gui=True)
    hsleep = 2
    p = coldwallet.address_book()
    import pprint
    pprint.pprint(p)
    sys.exit(0)
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
    """



