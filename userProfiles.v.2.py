#importing libraries
from aiohttp import ClientSession
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
def userData():
        try:
                with open('data.csv', newline='') as uData:
                        reader = csv.reader(uData)
                        try:
                                enctokens.clear()
                                next(reader)
                                for row in reader:
                                        enctokens.append(row[0])
                        except Exception as e:
                                logger.error('error in fetching enctokens -- %s' %e)
        except Exception as e:
                logger.error('error in reading data.csv -- %s' %e)
userData()

#asyncio order management
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
funds= []
failed= []
exceptions= []
async def profile(enctoken):
        async with ClientSession() as session:
                try:
                        details= await session.get(url='https://kite.zerodha.com/oms/user/profile/full', headers={'Authorization': 'enctoken %s' %(enctoken)})
#                       logger.info((await details.json())['data'])
                        margin= await session.get(url='https://kite.zerodha.com/oms/user/margins', headers={'Authorization': 'enctoken %s' %(enctoken)})
#                       logger.info((await margin.json())['data'])

##                        logger.info((await details.json())['data']['user_id'])
##                        print((await details.json())['data']['user_name'])
                        print((await details.json())['data']['email'])
##                        print((await details.json())['data']['bank_accounts'])
##                        print((await details.json())['data']['products'])
##                        print((await details.json())['data']['exchanges'])
##                        print('available funds -\t%s\n' %(await margin.json())['data']['equity']['net'])
##                        funds.append((await margin.json())['data']['equity']['net'])

                except Exception as e:
                        failed.append(enctoken)
                        exceptions.append(e)
                        

async def request():
                        try:
                                await asyncio.gather(*[profile(x) for x in zip(enctokens)], return_exceptions=True)
                        except Exception as e:
                                logger.error(e)

logger.info('user profiles\n\n')
asyncio.run(request())
print(f'\ncumulative available funds  --  {sum(funds)}')
if len(failed)>0:
    print()
    logger.error('couldnt fetch details for:')
    for(i,j) in zip(failed, exceptions):
        print('\t%s --\t%s' %(i, j))
input('\npress enter to exit\t')
