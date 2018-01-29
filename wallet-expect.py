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
        self.child.sendline('exit')
        time.sleep(20)
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

        print(self.child.before)
        print(self.child.after)


    def transfer(self,destAddress, amount, priority = "unimportant", ):
        tx_string = 'transfer %s %s %s' % (priority,destAddress,amount)
        self.child.sendline(tx_string)

    def getViewOnly(self):
        viewSecret= self.walletCmd("viewkey").split()[1]
        thisWalletAddress = self.walletCmd("address").split()[1]
        return viewSecret, thisWalletAddress


    def walletCmd(self,cmd,autoConfirm = False,verbose = True):
        self.ready = False
        #if verbose: print(self.child.before,self.child.after)
        self.child.sendline(cmd)
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
            if verbose: print(self.child.before,self.child.after)
            self.walletCmd(self.rawPassword,autoConfirm)

        elif i ==4:   # WALLET_ISOKAY_PROMPT
            if verbose: print(self.child.before,self.child.after)
            if self.getConfirmation(self.child.before,autoConfirm,verbose):
                self.ready = True

        if not self.ready:
            self.haltAndCatchFire("Automation Deadend: Wallet took us to somewhere we didn't plan")
        else:
            return self.child.before

    def getConfirmation(self,context,autoConfirm,verbose):
        if autoConfirm:
            self.walletCmd("y",autoConfirm)
            return self.ready
        else:
            self.haltAndCatchFire("Automation Deadend: haven't coded confirmation by live human")
            return False






if __name__ == "__main__":
    openwallet = Wallet(walletFile = os.path.join(MONERO_DIR,"testview"), password = '',daemonAddress = "testnet.kasisto.io:28081",testnet = True,cold = False)
    #openwallet = Wallet(walletFile = os.path.join(MONERO_DIR,"testnet"), password = '',testnet = True,cold = True)
    openwallet.getViewOnly()
    openwallet.walletCmd("transfer unimportant A16nFcW5XuU6Hm2owV4g277yWjjY6cVZy5YgE15HS6C8JujtUUP51jP7pBECqk78QW8K78yNx9LB4iB8jY3vL8vw3JhiQuX .45",autoConfirm = True)
    print(openwallet.child.before)
    openwallet.stopWallet()



