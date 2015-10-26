import urllib
import urllib2
import json
import time
import sys

mm_account_id = ""

def get_asset_name(asset_id):
    return nxt_api({'requestType' : 'getAsset', 'asset' : asset_id})["name"]

def get_decimals(asset_id):
    return int(nxt_api({'requestType' : 'getAsset', 'asset' : asset_id})["decimals"])

def nxt_api(values):
    url = 'http://localhost:7876/nxt'
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    return json.loads(response.read())

def send_message(message, secret_phrase):
    return nxt_api({'requestType' : 'sendMessage', 'secretPhrase' : secret_phrase,
        'recipient' : mm_account_id, 'messageToEncrypt' : message, 'encryptedMessageIsPrunable' : True,
        'deadline' : 5, 'feeNQT' : 100000000 })

def get_unconfirmed_ids():
    return nxt_api({'requestType' : 'getUnconfirmedTransactionIds' })["unconfirmedTransactionIds"]

def parse_transaction(bytes):
    return nxt_api({'requestType' : 'parseTransaction', 'transactionBytes' : bytes})

def sign_transaction(bytes, secret_phrase):
    return nxt_api({'requestType' : 'signTransaction', 'unsignedTransactionBytes' : bytes,
          'secretPhrase' : secret_phrase})

def send_request(request, asset_id, amount, secret_phrase):
    if request == "buy":
        tr = create_sendmoney_transaction(mm_account_id, amount, get_account_public_key(secret_phrase))
    elif request == "sell":
        tr = create_transferasset_transaction(mm_account_id, amount, asset_id, get_account_public_key(secret_phrase))
    else:
        raise Exception()
             
    m = {}    
    m["transaction"] = tr["unsignedTransactionBytes"]
    signed = sign_transaction(m["transaction"], secret_phrase)
    full_hash = signed["fullHash"]
    sig_hash = signed["signatureHash"]
    m["request"] = request
    m["assetid"] = asset_id
    m["fullhash"] = full_hash
    m["sighash"] = sig_hash
    send_message(json.dumps(m), secret_phrase)
    return (signed["transactionBytes"], full_hash)

def create_transferasset_transaction(recipient, amount_asset, asset_id, public_key):
    qnt = int(amount_asset * (pow(10, get_decimals(asset_id))))
    return nxt_api({'requestType' : 'transferAsset', 'recipient' : recipient, 'quantityQNT' : qnt,
          'feeNQT' : '100000000', 'deadline' : '5', 'publicKey' : public_key, 'asset' : asset_id})
   
def create_sendmoney_transaction(recipient, amount_nxt, public_key):
    return nxt_api({'requestType' : 'sendMoney', 'recipient' : recipient,
          'amountNQT' : int(amount_nxt * 100000000), 'feeNQT' : 100000000,
          'deadline' : 10, 'publicKey' : public_key })
          
def get_transaction(tr_id):
    return nxt_api(values = {'requestType' : 'getTransaction', 'transaction' : tr_id})

def get_nqt_for_tr(tr_id, full_hash, account):
    try:
        tr = get_transaction(tr_id)
        if tr["referencedTransactionFullHash"] == full_hash:
            if int(tr["feeNQT"]) >= 100000000 and tr["phased"] == False and \
                tr["recipientRS"] == account and tr["senderRS"] == mm_account_id:
                quantity = int(tr["amountNQT"])
                return quantity
            else:
                return 0
        else:
            return 0
    except:
        return 0
        
def get_qnt_for_tr(tr_id, expected_asset_id, full_hash, account):
    try:
        tr = get_transaction(tr_id)
        if tr["attachment"]["asset"] == str(expected_asset_id) and tr["referencedTransactionFullHash"] == full_hash:
            if "version.AssetTransfer" in tr["attachment"] and int(tr["feeNQT"]) >= 100000000 and \
                tr["phased"] == False and tr["recipientRS"] == account and \
                tr["senderRS"] == mm_account_id:

                quantity = int(tr["attachment"]["quantityQNT"])
                return quantity
            else:
                return 0
        else:
            return 0
    except:
        return 0

def get_nqt(full_hash, account):
    tr_ids = get_unconfirmed_ids()

    for tr_id in tr_ids:
        amount = get_nqt_for_tr(tr_id, full_hash, account)
        if amount > 0:
            return amount

    return 0

def get_qnt(expected_asset_id, full_hash, account):
    tr_ids = get_unconfirmed_ids()

    for tr_id in tr_ids:
        amount = get_qnt_for_tr(tr_id, expected_asset_id, full_hash, account)
        if amount > 0:
            return amount

    return 0

def get_balance(account):
    r = nxt_api({'requestType' : 'getBalance', 'account' : account}) 
    return float(r['unconfirmedBalanceNQT']) / 100000000.0


def get_account_public_key(secret_phrase):
    r = nxt_api({'requestType' : 'getAccountId', 'secretPhrase' : secret_phrase})
    return r["publicKey"]

def get_account_id(secret_phrase):
    r = nxt_api({'requestType' : 'getAccountId', 'secretPhrase' : secret_phrase})
    return r["accountRS"]
       
def get_avg_asset_price(asset, asset_quantity, action):
    if asset_quantity == 0:
        return 0

    if action == "buy":
        price_quants = get_asks(asset)
    elif action == "sell":
        price_quants = get_bids(asset)
    else:
        return 0
        
    assets_needed = asset_quantity
    price = 0.0

    for price_quant in price_quants:
        q = min(assets_needed, price_quant[1]) 
        price += price_quant[0] * q 
        assets_needed -= q

    if assets_needed > 0:
        return 0
    else:
        return price / asset_quantity
                
def get_asks(asset):
    k = 100000000.0 / (pow(10, get_decimals(asset)))
    req = nxt_api({'requestType' : 'getAskOrders', 'asset' : asset})

    asks = []

    for i in range(0, len(req["askOrders"])):
        qnt = int(req["askOrders"][i]["quantityQNT"])
        ask = (int(req["askOrders"][i]["priceNQT"]) / k, qnt / k)
        asks.append(ask)

    return asks

def get_bids(asset):
    k = 100000000.0 / (pow(10, get_decimals(asset)))
    req = nxt_api({'requestType' : 'getBidOrders', 'asset' : asset})

    bids = []

    for i in range(0, len(req["bidOrders"])):
        qnt = int(req["bidOrders"][i]["quantityQNT"])
        bid = (int(req["bidOrders"][i]["priceNQT"]) / k, qnt / k)
        bids.append(bid)

    return bids 

def mm_request(request, amount, account, asset_id, secret_phrase):
    (bytes, full_hash) = send_request(request, asset_id, amount, secret_phrase)
    wait_time = 0

    while wait_time < 60:
        print("-")
        wait_time += 1

        time.sleep(1)

        if request == "buy":
            qnt = 1.0 * get_qnt(asset_id, full_hash, account)
            if qnt > 0:
                k = 1.0 * (pow(10, get_decimals(asset_id)))
                num_assets = qnt / k 
                ae_price = get_avg_asset_price(asset_id, num_assets, "buy")
                amount_nxt = amount
                mm_price = amount_nxt / num_assets
                if mm_price > ae_price:
                    print "Asset exchange quote is better. Trade aborted. No payment sent.", ae_price, mm_price
                    return 
            
                nxt_api({'requestType' : 'broadcastTransaction', 'transactionBytes' : bytes})
                print "Received offer from market maker. Payment sent."
                print "Market maker price", mm_price
                print "Asset exchange price", ae_price
                print 
                print "Received", str(num_assets), get_asset_name(asset_id), "assets for", str(amount_nxt), "NXT"
                        
                return
                
        elif request == "sell":
            nqt = 1.0 * get_nqt(full_hash, account)
            if nqt > 0:
                k = 1.0 * (pow(10, get_decimals(asset_id)))
                amount_nxt = nqt / 100000000.0
                num_assets = amount 
                ae_price = get_avg_asset_price(asset_id, num_assets, "sell")
                mm_price = amount_nxt / num_assets
                
                if mm_price < ae_price:
                    print "Asset exchange quote is better. Trade aborted.", mm_price, ae_price
                    return 
            
                nxt_api({'requestType' : 'broadcastTransaction', 'transactionBytes' : bytes})
                print "Received bid from market maker. Assets sent."
                print "Market maker price", mm_price
                print "Asset exchange price", ae_price 
                print 
                print "Received", amount_nxt, "NXT for", num_assets, get_asset_name(asset_id), "assets",       

                return
            
    print "Received no offer from market maker, exiting"



def main():
    if len(sys.argv) == 1:
        print("Examples:")
        print("\n")
        print("python assettrader.py secretphrase - display account information")
        print("python assettrader.py secretphrase buy 3061160746493230502 1") 
        print("       --- buy Jinn, spend 1 NXT")
        print("python assettrader.py secretphrase sell 3061160746493230502 1")
        print("       --- sell 1 Jinn asset")

    elif len(sys.argv) == 2:
        secret_phrase = sys.argv[1]
        account = get_account_id(secret_phrase)
        print(account)

    elif len(sys.argv) == 5:
        secret_phrase = sys.argv[1]
        account = get_account_id(secret_phrase)

        request = sys.argv[2]
        asset_id = sys.argv[3]
        quantity = float(sys.argv[4])

        mm_request(request, quantity, account, asset_id, secret_phrase)

main()

    



