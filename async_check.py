
from datetime import datetime
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import aiohttp
import asyncpg
import requests
import json



MAX_NUMBER_OF_RETRIES = 5

async def read():
	conn = await asyncpg.connect(user='Levashovn', password='1qwerty7',
								 database='proxygrab', host='localhost')
	rows = await conn.fetch('SELECT curl, ip, protocol FROM pwproxies ')
	await conn.close()
	return [x['curl'] for x in rows]

async def delete_dead(dead_t):
	conn = await asyncpg.connect(user='Levashovn', password='1qwerty7',
								 database='proxygrab', host='localhost')
	await conn.execute("DELETE FROM pwproxies WHERE pwproxies.curl IN {}".format(dead_t))
	await conn.close()

async def update_status(ipport):
	check_time = datetime.now()
	conn = await asyncpg.connect(user='Levashovn', password='1qwerty7',
								 database='proxygrab', host='localhost')
	await conn.execute("UPDATE pwproxies SET last_checked = '{0}' WHERE pwproxies.curl = '{1}';".format(check_time, ipport))
	await conn.close()


def create_test_dict(dead_t):
	test_dict = []
	for dead in dead_t:
		d = {'http': dead}
		test_dict.append(d)
	print(test_dict)


def check():

	tasks = []
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)
	proxyList = loop.run_until_complete(read())
	for item in proxyList:
		# if not 'https' in item:
		tasks.append(asyncio.ensure_future(is_bad_proxy(item)))
		# else:
		# 	tasks.append(asyncio.ensure_future(check_ssl_proxy(item)))
	# tasks = [asyncio.ensure_future(item) for item in proxyList]
	try:
		dead = loop.run_until_complete(asyncio.gather(*tasks))
		print(dead)
		dead_t = tuple([item['proxy'] for item in dead if item['status'] == 'dead'])
		if dead_t:
			print(dead_t)
			loop.run_until_complete(delete_dead(dead_t))
			create_test_dict(dead_t)
		else:
			print('ALL ALIVE')
	except ValueError:
		print('db has no proxies to check')

	# loop.run_until_complete(asyncio.gather(*tasks))
	print("\n...Finished, The time is: %s" % datetime.now() )
	loop.close()



async def is_bad_proxy(first_ipport, retry_num=0, max_retries = MAX_NUMBER_OF_RETRIES):
	ipport = first_ipport.replace('https://', 'http://') if 'https' in first_ipport else first_ipport
	# ip = first_ipport.split(':')[1]
	session = aiohttp.ClientSession()
	try:
		response = await session.get('http://api.ipify.org/', proxy=ipport, timeout=4, allow_redirects=False)
		response_text = await response.text()
		print(response_text, ipport)
		if not response_text in ipport:

			raise Exception
		print("Working:", ipport)
		await session.close()
		return {'proxy': first_ipport, 'status': 'alive'}
	except asyncio.TimeoutError:
		await session.close()
		if retry_num < max_retries:
			print('Retry number ', retry_num, ', ip ', ipport)
			next_check = await is_bad_proxy(ipport, retry_num=retry_num + 1)
			return next_check
		else:
			print('Totally dead mens))', ipport)
			return {'proxy': ipport, 'status': 'dead'}
	except Exception as exc:
		print(str(exc))
		print("Not Working:", ipport)
		await session.close()
		return {'proxy': first_ipport, 'status': 'dead'}



## SLOW AS FUCK, I guess I'll stick to is_bad_proxy for now
async def check_ssl_proxy(ipport):
	try:
		response = requests.get('https://api.ipify.org', proxies={'https': ipport})
		ip = await response.text()
		if not ip in ipport:
			raise Exception
		# await write_working(ipport)
		print("Working SSL: ", ipport)
	except:
		print("Not Working SSL", ipport)
###############


# async def write_working(ipport):
# 	filename = 'working-proxies.txt'
# 	async with aiofiles.open(filename, 'w') as f:
# 		await f.write(ipport + '\n')


def free_proxy_list():
	url = 'https://www.proxy-list.download/api/v0/get?l=en&t=http'
	r = requests.get(url)
	j = json.loads(r.text)
	rows = j[0]['LISTA']
	for row in rows:
		d =	{'protocol': 'http',
			'ip' : row['IP'],
			'port': row['PORT'],
			'country_code': row['ISO'],
			'type': row['ANON'],
			'last_checked': datetime.now(),
			'curl': 'http://' + row['IP'] + ':' + row['PORT']}
		print(d)



if __name__ == '__main__':
	scheduler = AsyncIOScheduler()
	scheduler.add_job(check, 'interval', seconds=60)
	scheduler.start()
		# print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

	# Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
	try:
		asyncio.get_event_loop().run_forever()

	except (KeyboardInterrupt, SystemExit):
		print('why u did this?')
