#!/usr/bin/env python3

 #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#                                      $  
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#  ____   ___   ____ _  _______ _____  $
# |  _ \ / _ \ / ___| |/ / ____|_   _| $
# | |_) | | | | |   | ' /|  _|   | |   $
# |  __/| |_| | |___| . \| |___  | |   $
# |_|    \___/ \____|_|\_\_____| |_|   $
#    _____ ____   ____ ____   ___      $
#   |_   _|  _ \ / ___|___ \ / _ \     $
#     | | | |_) | |     __) | | | |    $
#     | | |  _ <| |___ / __/| |_| |    $
#     |_| |_| \_|\____|_____|\___/     $
#                                      $    
 #                                    $
  #               (..)               $
   #$$$$$$$                  $$$$$$$$
           #$$$$$$$$$$$$$$$$$

import sys, colorama, requests
from .CLI import Scan


def checkConnection():
    try:
        requests.get('https://google.com', timeout=1)
        return True
    except:
        return False

def entry_point():
    colorama.init()
    if '--hash' in sys.argv:
        if len(sys.argv) == 3:
            if checkConnection() == True:
                hash = sys.argv[2]
                Scan().banner()
                Scan().hash_scanner(hash)
            else:
                print('\033[31m! Check your internet connection\033[0m')
                sys.exit(1)
        else:
            print('\033[31m! Hash wasn\'t entered\033[0m')
            sys.exit(1)
    elif '--info' in sys.argv:
        if len(sys.argv) == 2:
            print('PocketTRC20\nby Lao\nLicensed under MIT\n\nOptions:\n--hash TRANSACTION_HASH    scan transaction\n--info                     you\'re here')
            sys.exit(0)
        else:
            print('\033[31m! Unknown value: \033[0m' + sys.argv[2])
            sys.exit(1)
    else:
        print('\033[31m! Incorrect option\033[0m')
        sys.exit(1)


if __name__ == "__main__":
    entry_point()
