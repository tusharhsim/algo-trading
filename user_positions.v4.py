#importing libraries
from selenium.webdriver.common.by import By
from selenium import webdriver
from aiohttp import ClientSession
import keyboard
import asyncio
import logging
import json
import csv


#logger's defination
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(ch)


#enctoken input
enctokens=[]
lot_size = [1800]
with open('data.csv', newline='') as uData:
        reader = csv.reader(uData)
        enctokens.clear()
        next(reader)
        for row in reader:
                enctokens.append(row[0])


#asyncio orders requests
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

tokens = []
tTypes = []
exchanges = []
symbols = []
quantities = []
products = []

async def get_position(session, enctoken):
        try:
                details = await session.get(url='https://kite.zerodha.com/oms/portfolio/positions', headers={'Authorization': 'enctoken %s' %(enctoken)})
                for i in (await details.json())['data']['net']:
                        if (i['quantity']<0) and ('NIFTY' in i['tradingsymbol']):
                                tokens.append(enctoken)
                                tTypes.append('BUY')
                                exchanges.append(i['exchange'])
                                symbols.append(i['tradingsymbol'])
                                quantities.append(abs(i['quantity']))
                                products.append(i['product'])

                        if (i['quantity']>0):
                                size=i['quantity']
                                while size>0:
                                        if size<lot_size[0]:
                                                tokens.append(enctoken)
                                                tTypes.append('SELL')
                                                exchanges.append(i['exchange'])
                                                symbols.append(i['tradingsymbol'])
                                                quantities.append(abs(size))
                                                products.append(i['product'])
                                                break
                                        tokens.append(enctoken)
                                        tTypes.append('SELL')
                                        exchanges.append(i['exchange'])
                                        symbols.append(i['tradingsymbol'])
                                        quantities.append(lot_size[0])
                                        products.append(i['product'])
                                        size-=lot_size[0]

                        print('%s\t%s\t%s\t%s\t' %(i['exchange'], i['tradingsymbol'], i['product'], i['quantity']))
        except:
                pass

async def request():
        async with ClientSession() as session:
                tasks = []
                for token in enctokens:
                        task = asyncio.create_task(get_position(session, token))
                        tasks.append(task)
                await asyncio.gather(*tasks)

async def place_order(session, enctoken, exchange, symbol, tType, quantity, product):
        try:
                resp = await session.post(url='https://kite.zerodha.com/oms/orders/regular',
                                         headers={'Authorization': 'enctoken %s' %(enctoken),'Content-Type': 'application/x-www-form-urlencoded'},
                                         data='exchange=%s&tradingsymbol=%s&transaction_type=%s&order_type=MARKET&quantity=%s&product=%s'
                                         %(exchange, symbol, tType, quantity, product))
                logger.info(await resp.text())
        except:
                pass

async def exit_positions():
        async with ClientSession() as session:
                tasks = []
                for (token, exchange, symbol, tType, quantity, product) in zip(tokens, exchanges, symbols, tTypes, quantities, products):
                        task = asyncio.create_task(place_order(session, token, exchange, symbol, tType, quantity, product))
                        tasks.append(task)
                await asyncio.gather(*tasks)


logger.info('user positions\n\n')
asyncio.run(request())
if len(tokens) > 0:
        x = input('\npress Q or q to exit all open positions\t\t')
        if x=='Q' or x=='q':
                asyncio.run(exit_positions())
else:
        print('\nno open positions found!')
