# -*- coding: utf-8 -*-

import sys, time, requests, json
from .config import __version__
from progress.bar import IncrementalBar


class Scan():
    def __init__(self):
        self.bar = IncrementalBar('Scanning transaction', max=7, suffix='%(percent)d%%')

    def banner(self):
        banner = '''
 $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$                                      $
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$  ____   ___   ____ _  _______ _____  $
$ |  _ \\ / _ \\ / ___| |/ / ____|_   _| $
$ | |_) | | | | |   | ' /|  _|   | |   $
$ |  __/| |_| | |___| . \\| |___  | |   $
$ |_|    \\___/ \\____|_|\\_\\_____| |_|   $
$    _____ ____   ____ ____   ___      $
$   |_   _|  _ \\ / ___|___ \\ / _ \\     $
$     | | | |_) | |     __) | | | |    $
$     | | |  _ <| |___ / __/| |_| |    $
$     |_| |_| \\_|\\____|_____|\\___/     $
$                                      $
 $                                    $
  $               (..)               $
   $$$$$$$$                  $$$$$$$$
           $$$$$$$$$$$$$$$$$$
                 \033[1;34mby Lao\033[0m
        '''
        print(banner + '         \033[34mv' + __version__ + '\033[0m')

    def check_latest_release(self):
        headers = {'Accept': 'application/vnd.github+json'}
        check_latest_release = requests.get('https://api.github.com/repos/codelao/PocketTRC20/releases/latest', headers=headers)
        if check_latest_release.status_code == 200:
            latest_release = json.loads(check_latest_release.text)
            if not latest_release['tag_name'] == 'v'+__version__:
                return latest_release['tag_name']

    def hash_scanner(self, hash):
        if not self.check_latest_release() == None:
            print('\033[32mNew PocketTRC20 release found!\033[0m\nInstalled release: v'+__version__+'\nLatest: '+self.check_latest_release()+'\n\nVisit \033[96mhttps://github.com/codelao/PocketTRC20/releases/latest\033[0m.\n')
        if not len(hash) == 64:
            print('\033[31m! Incorrect hash entered\033[0m')
            sys.exit(1)
        else:
            link = 'https://apilist.tronscan.org/api/transaction-info?hash=' + hash
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'}
            get_link = requests.get(link, headers=headers).text
            time.sleep(0.1)
            self.bar.next()
            self.check_hash = json.loads(get_link)
            time.sleep(0.1)
            self.bar.next()
            if self.check_hash == {} or self.check_hash == {"message":"some parameters are missing"} or self.check_hash == {"riskTransaction":False}:
                time.sleep(0.1)
                self.bar.finish()
                print('\033[31m! Unable to get details of this transaction\033[0m')
                sys.exit(1)
            else:
                token_check = self.check_hash["contractType"]
                time.sleep(0.1)
                self.bar.next()
                if token_check == 31:
                    status = self.check_hash["contractRet"]
                    time.sleep(0.1)
                    self.bar.next()
                    if status == 'SUCCESS':
                        from_address = self.check_hash["tokenTransferInfo"]["from_address"]
                        time.sleep(0.1)
                        self.bar.next()
                        to_address = self.check_hash["tokenTransferInfo"]["to_address"]
                        time.sleep(0.1)
                        self.bar.next()
                        amount = self.check_hash["tokenTransferInfo"]["amount_str"]
                        time.sleep(0.1)
                        self.bar.next()
                        time.sleep(0.1)
                        self.bar.finish()
                        print(
                            '\033[32mTransaction details:\033[0m' +
                            '\nStatus: ' + status +
                            '\nFrom: ' + from_address +
                            '\nTo: ' + to_address +
                            '\nAmount: ' + str(amount)[0:-6] + ' USDT'
                        )
                        sys.exit(0)
                    else:
                        time.sleep(0.1)
                        self.bar.finish()
                        print(
                            '\033[32mTransaction details:\033[0m' +
                            '\nStatus: ' + status +
                            '\nAmount: 0 USDT'
                        )
                        sys.exit(0)
                elif token_check == 1:
                    status = self.check_hash["contractRet"]
                    time.sleep(0.1)
                    self.bar.next()
                    if status == 'SUCCESS':
                        from_address = self.check_hash["contractData"]["owner_address"]
                        time.sleep(0.1)
                        self.bar.next()
                        to_address = self.check_hash["contractData"]["to_address"]
                        time.sleep(0.1)
                        self.bar.next()
                        amount = self.check_hash["contractData"]["amount"]
                        time.sleep(0.1)
                        self.bar.next()
                        time.sleep(0.1)
                        self.bar.finish()
                        print(
                            '\033[32mTransaction details:\033[0m' +
                            '\nStatus: ' + status +
                            '\nFrom: ' + from_address +
                            '\nTo: ' + to_address +
                            '\nAmount: ' + str(amount)[0:-6] + ' TRX'
                        )
                        sys.exit(0)
                    else:
                        time.sleep(0.1)
                        self.bar.finish()
                        print(
                            '\033[32mTransaction details:\033[0m' +
                            '\nStatus: ' + status +
                            '\nAmount: 0 TRX'
                        )
                        sys.exit(0)
                else:
                    time.sleep(0.1)
                    self.bar.finish()
                    print('\033[31m! Unable to get details of this transaction\033[0m')
                    sys.exit(1)
