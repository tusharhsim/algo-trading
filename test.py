import requests

headers = {
    'Host': 'kite.zerodha.com',
    'Authorization': 'enctoken z5jhREcfvpqXXam+9yZ1z+CiFe9fMZvB7/+OeK3xbkchU8LoQscqI3cyFf2SlMTejGNyx6lsA0MrOdRAqqpZa2ll+CXxcvD4ZaXrlZbJv57yMjuDpXO3Gg==',
}

json_data = [
    {
        'exchange': 'NFO',
        'tradingsymbol': 'NIFTY22N1718300CE',
        'transaction_type': 'SELL',
        'variety': 'amo',
        'product': 'NRML',
        'order_type': 'LIMIT',
        'quantity': 500,
        'price': 102,
    },
]

response = requests.post('https://kite.zerodha.com/oms/margins/orders', headers=headers, json=json_data, verify=False)
print(response.text)