NXT Asset Trader

Does direct asset trades with a market maker program that has better prices
than the "normal" Asset Exchange. Uses python2.

Only selected assets are available. Same asset IDs can be both bought
and sold. See market maker account NXT-YSKR-TC9G-X4RR-FV8NY for
up-to-date availability.

Asset <-> NXT swap with the market maker is done with "escrow operation"
described in the Nxt wiki:
https://wiki.nxtcrypto.org/wiki/The_Nxt_API#Escrow_Operations. If the
market maker behaves incorrectly, does not respond, or quotes a worse
price than is available on the "normal" Asset Exchange, assettrader.py
will not broadcast its part of the transaction.

Transaction costs are 2 NXT instead of the normal 1 NXT.

Usage example below. Make sure NRS is running on localhost.

Spend 1000 NXT (+ 2 NXT transaction cost) to buy SuperNET assets.
'secretphrase' is your account's secret. If your secret contains
spaces, use quotes.

python assettrader.py secretphrase buy 12071612744977229797 1000

Sell 10 SuperNET assets:

python assettrader.py secretphrase sell 12071612744977229797 10

Also commands "buytest" and "selltest" are available. These show what
price the market maker is willing to buy/sell at, without completing
the trade. This results in an unconfirmable transaction being
broadcast, so don't use this option too often.
