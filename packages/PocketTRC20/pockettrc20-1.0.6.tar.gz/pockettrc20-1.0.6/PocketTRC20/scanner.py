import requests
import json
from .__main__ import checkConnection


def transaction(hash):
    if checkConnection() == True:
        if not len(hash) == 64:
            raise ValueError('Incorrect hash entered.') 
        else:
            details = {}
            link = 'https://apilist.tronscan.org/api/transaction-info?hash=' + hash
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'}
            get_link = requests.get(link, headers=headers).text
            check_hash = json.loads(get_link)
            if check_hash == {} or check_hash == {"message":"some parameters are missing"} or check_hash == {"riskTransaction":False}:
                raise KeyError('Unable to get details of this transaction.')
            else:
                token_check = check_hash["contractType"]
                if token_check == 31:
                    status = check_hash["contractRet"]
                    if status == 'SUCCESS':
                        from_address = check_hash["tokenTransferInfo"]["from_address"]
                        to_address = check_hash["tokenTransferInfo"]["to_address"]
                        amount = check_hash["tokenTransferInfo"]["amount_str"]
                        details['Status'] = status
                        details['From'] = from_address
                        details['To'] = to_address
                        details['Amount'] = str(amount)[0:-6] + ' USDT'
                        return details
                    else:
                        details['Status'] = status
                        details['Amount'] = '0 USDT'
                        return details
                elif token_check == 1:
                    status = check_hash["contractRet"]
                    if status == 'SUCCESS':
                        from_address = check_hash["contractData"]["owner_address"]
                        to_address = check_hash["contractData"]["to_address"]
                        amount = check_hash["contractData"]["amount"]
                        details['Status'] = status
                        details['From'] = from_address
                        details['To'] = to_address
                        details['Amount'] = str(amount)[0:-6] + ' TRX'
                        return details
                    else:
                        details['Status'] = status
                        details['Amount'] = '0 TRX'
                        return details
                else:
                    raise KeyError('Unable to get details of this transaction.')
    else:
        raise ConnectionError('Check your internet connection')
    
def status(hash):
    try:
        details = transaction(hash)['Status']
        return details
    except Exception as e:
        return e

def amount(hash, hide=False):
    try:
        details = transaction(hash)['Amount']
        if hide == True:
            return int(details[0:-5])
        elif hide != True and hide != False:
            raise ValueError('\'hide\' argument can be True or False only.')
        else:
            return details
    except Exception as e:
        return e
