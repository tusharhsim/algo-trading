#importing libraries
from selenium.webdriver.common.by import By
from selenium import webdriver
from aiohttp import ClientSession
import pandas as pd
import keyboard
import asyncio
import logging
import json
import csv
import os


## variable data ##
#instrument = ['BANKNIFTY22512', 1200]
instrument = ['NIFTY22512', 1800]
token_data = {}
placed_orders = {}
open_positions = {}
order_adjustment = {}
enctokens = {}
remaining_qty = []

## logger's defination ##
FORMAT = '%(asctime)s - %(message)s'
logging.basicConfig(format=FORMAT)


## order functions ##
async def place_order(session, enctoken, tradingsymbol, transaction_type, order_type, quantity, price):
        try:
                resp = await session.post(url='https://kite.zerodha.com/oms/orders/regular',
                                         headers={'Authorization': 'enctoken %s' %(enctoken),'Content-Type': 'application/x-www-form-urlencoded'},
                                         data='exchange=NFO&tradingsymbol=%s&transaction_type=%s&order_type=%s&quantity=%s&price=%s&product=NRML'
                                         %(tradingsymbol, transaction_type, order_type, quantity, price))
                logging.warning(await resp.text())
                placed_orders[(await resp.json())['data']['order_id']] = enctoken
        except:
                pass

async def modify_order(session, enctoken, ids, price, qty = False):
        try:
                if qty:
                        resp = await session.put(url='https://kite.zerodha.com/oms/orders/regular/%s' %(ids),
                                                 headers={'Authorization': 'enctoken %s' %(enctoken),'Content-Type': 'application/x-www-form-urlencoded'},
                                                 data='quantity=%s&price=%s' %(qty, price))
                else:
                        resp = await session.put(url='https://kite.zerodha.com/oms/orders/regular/%s' %(ids),
                                                 headers={'Authorization': 'enctoken %s' %(enctoken),'Content-Type': 'application/x-www-form-urlencoded'},
                                                 data='price=%s' %(price))

                logging.warning(await resp.text())
        except:
                pass

async def cancel_order(session, enctoken, ids):
        try:
                resp = await session.delete(url='https://kite.zerodha.com/oms/orders/regular/%s' %(ids), headers={'Authorization': 'enctoken %s' %(enctoken)})
                logging.warning(await resp.text())
        except:
                pass

async def get_individual_order(session, enctoken, ids):
        try:
                resp = await session.get(url='https://kite.zerodha.com/oms/orders/%s' %(ids),
                                         headers={'Authorization': 'enctoken %s' %(enctoken),'Content-Type': 'application/x-www-form-urlencoded'})

                if 'OPEN' in (await resp.json())['data'][-1]['status']:
                        initial_buy_fund = float((await resp.json())['data'][0]['price']) * float((await resp.json())['data'][0]['quantity'])
                        max_buy_fund = initial_buy_fund - (float((await resp.json())['data'][-1]['price']) * float((await resp.json())['data'][-1]['filled_quantity']))
                        order_adjustment[ids] = [enctoken, int(max_buy_fund)]
        except:
                pass

async def get_order(session, enctoken, ids):
        try:
                resp = await session.get(url='https://kite.zerodha.com/oms/orders/%s' %(ids),
                                         headers={'Authorization': 'enctoken %s' %(enctoken),'Content-Type': 'application/x-www-form-urlencoded'})

                if 'OPEN' in (await resp.json())['data'][-1]['status']:
                        remaining_qty.append((await resp.json())['data'][-1]['pending_quantity'])
        except:
                pass

async def get_position(session, enctoken, tradingsymbol):
        try:
                resp = await session.get(url='https://kite.zerodha.com/oms/portfolio/positions', headers={'Authorization': 'enctoken %s' %(enctoken)})
                for position in (await resp.json())['data']['net']:
                        if (position['quantity'] > 0) and (tradingsymbol == position['tradingsymbol']):
                                open_positions[enctoken] = []
                                size = position['quantity']
                                while size > 0:
                                        if size <= instrument[1]:
                                                open_positions[enctoken].append(int(size))
                                                break
                                        open_positions[enctoken].append(instrument[1])
                                        size -= instrument[1]
        except:
                pass

async def buy_update(tradingsymbol, total_orders):
        async with ClientSession() as session:
                limit_price = 0
                while limit_price <= 0:
                        limit_price = float(''.join(i for i in input(f'new price for {tradingsymbol}\t\t') if i.isdigit() or i in '.') or 0)
                order_adjustment.clear()
                tasks = []
                for ids, enctoken in placed_orders.items():
                        task = asyncio.create_task(get_individual_order(session, enctoken, ids))
                        tasks.append(task)
                await asyncio.gather(*tasks)

                tasks = []
                for ids in order_adjustment:
                        qty = int((order_adjustment[ids][1]//(limit_price*50))*50)
                        if qty > 0  and qty <= instrument[1]:
                                task = asyncio.create_task(modify_order(session, order_adjustment[ids][0], ids, limit_price, qty))
                        if qty >= instrument[1]:
                                task = asyncio.create_task(modify_order(session, order_adjustment[ids][0], ids, limit_price, instrument[1]))
                        else:
                                continue
                        tasks.append(task)
                await asyncio.gather(*tasks)
                order_adjustment.clear()

                remaining_qty.clear()
                tasks = []
                for ids, enctoken in placed_orders.items():
                        task = asyncio.create_task(get_order(session, enctoken, ids))
                        tasks.append(task)
                await asyncio.gather(*tasks)
                print('total open orders\t%s/%s' %(sum(remaining_qty), total_orders))
                remaining_qty.clear()

async def update(tradingsymbol, total_orders):
        async with ClientSession() as session:
                limit_price = 0
                while limit_price <= 0:
                        limit_price = float(''.join(i for i in input(f'new price for {tradingsymbol}\t\t') if i.isdigit() or i in '.') or 0)
                tasks = []
                for ids, enctoken in placed_orders.items():
                        task = asyncio.create_task(modify_order(session, enctoken, ids, limit_price))
                        tasks.append(task)
                await asyncio.gather(*tasks)

                remaining_qty.clear()
                tasks = []
                for ids, enctoken in placed_orders.items():
                        task = asyncio.create_task(get_order(session, enctoken, ids))
                        tasks.append(task)
                await asyncio.gather(*tasks)
                print('total open orders\t%s/%s' %(sum(remaining_qty), total_orders))
                remaining_qty.clear()

async def cancel(tradingsymbol):
        async with ClientSession() as session:
                print(f'cancelling open orders for\t{tradingsymbol}')
                tasks = []
                for ids, enctoken in placed_orders.items():
                        task = asyncio.create_task(cancel_order(session, enctoken, ids))
                        tasks.append(task)
                await asyncio.gather(*tasks)
                placed_orders.clear()
                print(f'all open orders cancelled for \t{tradingsymbol}')

                open_positions.clear()
                tasks = []
                for enctoken in token_data:
                        task = asyncio.create_task(get_position(session, enctoken, tradingsymbol))
                        tasks.append(task)
                await asyncio.gather(*tasks)

async def available_margin(session, enctoken):
        try:
                margin = await session.get(url='https://kite.zerodha.com/oms/user/margins',
                                           headers={'Authorization': 'enctoken %s' %(enctoken)})
                uid = await session.get(url='https://kite.zerodha.com/oms/user/profile/full',
                                        headers={'Authorization': 'enctoken %s' %(enctoken)})
                enctokens[enctoken] = {'margin' : (await margin.json())['data']['equity']['net'], 'uId' : (await uid.json())['data']['user_id']}
        except:
                pass

async def margin_updater():
        enctokens.clear()
        tasks = []
        try:
                data = {}
                rate = 8

                with open('compounding_data.csv', newline='') as uData:
                    reader = csv.reader(uData)
                    next(reader)
                    for row in reader:
                        data[row[0].strip()] = int((1+rate/100) * float(row[1].strip()))

                df_comp = pd.DataFrame(data.items(), columns=['uid', 'margin'])
                df_comp = df_comp.sort_values(by=['uid'])
                df_comp.to_csv('compounding_data.csv', sep=',', encoding='utf-8', index= False)

                async with ClientSession() as session:
                        for enctoken in token_data:
                                task = asyncio.create_task(available_margin(session, enctoken))
                                tasks.append(task)
                        await asyncio.gather(*tasks)
                if len(enctokens) > 0:
                    df_data= pd.DataFrame({'enctoken' : enctokens.keys(),
                                      'margin' : [int(i['margin']) for i in enctokens.values()],
                                      'uid' : [i['uId'] for i in enctokens.values()]})
                df = pd.merge(df_data, df_comp,
                              on = 'uid',
                              how = 'inner')
                df['margin_x'] = df['margin_y']
                df = df.drop(columns='margin_y')
                df.columns = ['enctoken', 'margin', 'uid']
                df = df.sort_values(by=['uid'])
                df.to_csv('data.csv', sep=',', encoding='utf-8', index= False)
                print('\ntrading fund\t%s' %int(df['margin'].sum()))

        except Exception as e:
                print(f'margin_updater exception {e}')

def user_data():
        with open('data.csv', newline='') as uData:
                reader = csv.reader(uData)
                token_data.clear()
                next(reader)
                for row in reader:
                        token_data[row[0]] = int(float(row[1]))

def no_of_trades(price):
        quantity_data = {}
        total = 0
        for enctoken, capital in token_data.items():
                quantity_data[enctoken] = []
                buyable_qty = (capital//(price*50))*50
                while buyable_qty > 0:
                        if buyable_qty <= instrument[1]:
                                quantity_data[enctoken].append(int(buyable_qty))
                                total += int(buyable_qty)
                                break
                        quantity_data[enctoken].append(instrument[1])
                        total += int(instrument[1])
                        buyable_qty -= instrument[1]
        return quantity_data, total

## MAIN ##
async def Trade(contract):
        try:
                tradingsymbol = ('%s%s%s' %(instrument[0], int(''.join(i for i in input(f'{contract} strike\t') if i.isdigit())), contract))
                print(f'buying {tradingsymbol}')
                limit_price = 0
                while limit_price <= 0:
                        limit_price = float(''.join(i for i in input('limit price\t') if i.isdigit() or i in '.') or 0)
                quantity_data, total_orders = no_of_trades(limit_price)
                placed_orders.clear()
                async with ClientSession() as session:
                        tasks = []
                        for k,v in quantity_data.items():
                                for qty in v:
                                        task = asyncio.create_task(place_order(session, k, tradingsymbol, 'BUY', 'LIMIT', qty, limit_price))
                                        tasks.append(task)
                        await asyncio.gather(*tasks)
                print(f'bought {tradingsymbol}, press shift + U to update orders, DEL to exit')
                while True:
                        if keyboard.is_pressed("shift+U"):
                                await buy_update(tradingsymbol, total_orders)

                        if keyboard.is_pressed("del"):
                                await cancel(tradingsymbol)
                                print(f'all open positions gathered for {tradingsymbol}\n')
                                break

                buying_price = 0
                while buying_price <= 0:
                        buying_price = float(''.join(i for i in input(f'input the buying price of {tradingsymbol}\t\t') if i.isdigit() or i in '.') or 0)
                percent_loss = 100
                def_sl = (1-(percent_loss/100))*buying_price
                sl = def_sl
                percent_gain = 251
                tgt = (1+(percent_gain/100))*buying_price
                print('press shift + E to modify sl and target\n')

                flag = 0
                flag_2 = 0
                while True:
                        try:
                                ltp = float(driver.find_element(By.CSS_SELECTOR, 'span.last-price:nth-child(3)').text)

                                if ((ltp <= def_sl) or (ltp <= sl) or (ltp >= tgt)) and flag == 0:
                                        if flag_2 == 1:
                                                await cancel(tradingsymbol)
                                        async with ClientSession() as session:
                                                tasks = []
                                                for k,v in open_positions.items():
                                                        for qty in v:
                                                                task = asyncio.create_task(place_order(session, k, tradingsymbol, 'SELL', 'LIMIT', qty, ltp-1))
                                                                tasks.append(task)
                                                await asyncio.gather(*tasks)
                                        print(f'sold {tradingsymbol} automatically, press shift + U to update orders, DEL to liquidate')
                                        open_positions.clear()
                                        flag = 1

                                if keyboard.is_pressed("shift+A") and flag == 0 and flag_2 == 0:
                                        limit_price = 0
                                        while limit_price <= 0:
                                                limit_price = float(''.join(i for i in input(f'limit price for selling {tradingsymbol}\t') if i.isdigit() or i in '.') or 0)
                                        async with ClientSession() as session:
                                                tasks = []
                                                for k,v in open_positions.items():
                                                        for qty in v:
                                                                task = asyncio.create_task(place_order(session, k, tradingsymbol, 'SELL', 'LIMIT', qty, limit_price))
                                                                tasks.append(task)
                                                await asyncio.gather(*tasks)
                                        print(f'sold {tradingsymbol} manually, press shift + U to update orders, DEL to liquidate')
                                        open_positions.clear()
                                        flag_2 = 1

                                if keyboard.is_pressed("shift+E") and flag == 0:
                                        sl = float(''.join(i for i in input(f'input trailing sl for {tradingsymbol}\t\t') if i.isdigit() or i in '.') or sl)
                                        tgt = float(''.join(i for i in input(f'input new target for {tradingsymbol}\t\t') if i.isdigit() or i in '.') or tgt)
                                        print(f'def_sl  - {def_sl}')
                                        print(f'sl  - {sl}')
                                        print(f'tgt - {tgt}\n')


                                if keyboard.is_pressed("shift+U") and (flag == 1 or flag_2 == 1):
                                        await update(tradingsymbol, total_orders)

                                if keyboard.is_pressed("del") and (flag == 1 or flag_2 == 1):
                                        await cancel(tradingsymbol)
                                        async with ClientSession() as session:
                                                tasks = []
                                                for k,v in open_positions.items():
                                                        for qty in v:
                                                                task = asyncio.create_task(place_order(session, k, tradingsymbol, 'SELL', 'MARKET', qty, ltp))
                                                                tasks.append(task)
                                                await asyncio.gather(*tasks)
                                        open_positions.clear()
                                        print(f'liquidated {tradingsymbol}\n')
                                        #await margin_updater()
                                        token_data.clear()
                                        user_data()
                                        os.system('python user_pnl.v4.py')
                                        break

                        except:
                                pass

        except Exception as e:
                logging.error('manual %s trade unsuccessful -- %s\n' %(tradingsymbol,e))

print('N\nscalping beast welcomes you')
print('press ESC to exit the core loop\n')

#login
driver = webdriver.Chrome()
driver.implicitly_wait(14)

driver.get('https://kite.zerodha.com/')
driver.maximize_window()
driver.find_element(By.ID, "userid").send_keys('BQ0221')
driver.find_element(By.ID, "password").send_keys('reshmi.@7506')
driver.find_element(By.TAG_NAME, 'button').click()
driver.find_element(By.ID, 'pin').send_keys('973209')
driver.find_element(By.TAG_NAME, 'button').click()

#data input
user_data()
print('enctoken, fund:')
for i,j in token_data.items():
        print(' %s,\t%s' %(i,j))

input('\npress enter to trade\t')

#manualTrades
logging.warning('make what you can\n')

while True:
        try:
                if keyboard.is_pressed("shift+c"):
                        print('\nbutton pressed for CE')
                        asyncio.run(Trade('CE'))

                if keyboard.is_pressed("shift+p"):
                        print('\nbutton pressed for PE')
                        asyncio.run(Trade('PE'))

                if keyboard.is_pressed("esc"):
                        break

        except Exception as e:
                logging.critical('core event loop failed -- %s\n' %e)

driver.quit()
print('\ngood times?')
