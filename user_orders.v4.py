#importing libraries
from aiohttp import ClientSession
import asyncio
import json
import csv


asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

#enctoken input
enctokens=[]
with open('data.csv', newline='') as uData:
        reader = csv.reader(uData)
        enctokens.clear()
        next(reader)
        for row in reader:
                enctokens.append(row[0])


#asyncio orders requests
orders = {}

async def get_orders(session, enctoken):
    try:
        details= await session.get(url='https://kite.zerodha.com/oms/orders', headers={'Authorization': 'enctoken %s' %(enctoken)})
        for i in ((await details.json())['data']):
                orders[i['order_id']] = [enctoken, i['variety']]
    except:
            pass

async def request():
        async with ClientSession() as session:
                tasks = []
                for token in enctokens:
                        task = asyncio.create_task(get_orders(session, token))
                        tasks.append(task)
                await asyncio.gather(*tasks)

async def cancel_orders(session, enctoken, variety, ids):
        try:
                details= await session.delete(url='https://kite.zerodha.com/oms/orders/%s/%s' %(variety, ids),
                                              headers={'Authorization': 'enctoken %s' %(enctoken)})
                print(await details.text())
        except:
                pass

async def cancel_request():
        async with ClientSession() as session:
                tasks = []
                for ids in orders:
                        task = asyncio.create_task(cancel_orders(session, orders[ids][0], orders[ids][1], ids))
                        tasks.append(task)
                await asyncio.gather(*tasks)

asyncio.run(request())

x = input('press Q or q to cancel all orders\t')
if x=='Q' or x=='q':
        asyncio.run(cancel_request())
