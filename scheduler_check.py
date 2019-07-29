# from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import requests
import time
from datetime import datetime
import json
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.background import BlockingScheduler
from lxml import etree
import psycopg2
from psycopg2 import sql, IntegrityError, pool
from contextlib import contextmanager
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

db = pool.SimpleConnectionPool(1, 10,
							   user='Levashovn', password='1qwerty7',
							   database='proxygrab', host='localhost')

# proxyList = []

working_proxies =[]
@contextmanager
def get_connection():
	con = db.getconn()
	try:
		yield con
	finally:
		db.putconn(con)


def write_to_db(d):
	with get_connection() as conn:
		try:
			cursor = conn.cursor()
			query = sql.SQL("INSERT INTO {} VALUES (%s, %s, %s, %s, %s, %s, %s)").format(sql.Identifier('pwproxies'))

			cursor.execute(query, (
			d['curl'], d['ip'], d['protocol'], d['port'], d['country_code'], d['type'], d['last_checked']))
			cursor.close()
			conn.commit()
		except:
			conn.rollback()


def select_proxies():
	with get_connection() as conn:

		try:
			proxyList = []
			cursor = conn.cursor()
			query = "select * from pwproxies"
			cursor.execute(query)
			rows = cursor.fetchall()
			for row in rows:
				d = {
					'curl': row[0],
					'ip': row[1],
					'protocol': row[2],
					'port': row[3]
				}

				proxyList.append(d)
			cursor.close()
			conn.commit()
			return proxyList
		except:
			conn.rollback()


def delete_dead(curl):
	with get_connection() as conn:

		try:
			proxies = []
			cursor = conn.cursor()
			delete_query = 'DELETE FROM pwproxies WHERE curl = %s;'
			cursor.execute(delete_query, (curl,))
			cursor.close()
			conn.commit()
			return proxies
		except:
			conn.rollback()


def update_alive(last_checked, curl):
	with get_connection() as conn:

		try:
			proxies = []
			cursor = conn.cursor()
			update_query = 'Update pwproxies set last_checked = %s where curl = %s'
			cursor.execute(update_query, (last_checked, curl,))
			cursor.close()
			conn.commit()
			return proxies
		except:
			conn.rollback()


def init_connection(proxy):
	print(proxy)
	protocol, ip, port = proxy['protocol'], str(proxy['ip']), str(proxy['port'])
	##SOCKS ARE CONNECTING  LIKE THIS {'http': 'socks5//:ip'}
	if protocol == 'socks4' or protocol == 'socks5':
		protocol_url = 'http'
		protocol = protocol
	else:
		protocol_url = protocol
	try:
		r = requests.get(protocol_url + '://api.ipify.org/', proxies={protocol_url: protocol + '://' + ip + ':' + port},
						 timeout=10, allow_redirects=False)
		print(r.text, ip)
		if not r.text in ip:
			raise Exception
		last_check = datetime.now()
		update_alive(last_checked=last_check, curl=proxy['curl'])
		return {'proxy': proxy, 'status': 'alive'}
	except Exception as exc:
		print(exc)
		delete_dead(proxy['curl'])
		return {'proxy': proxy, 'status': 'dead'}


def main_check():
	proxyList = select_proxies()
	with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:

		futures = [executor.submit(init_connection, proxy) for proxy in proxyList]
		for future in concurrent.futures.as_completed(futures):
			try:
				data = future.result()
				print(data)
			except Exception as exc:
				print(exc)


#############################################################################################################
##########################################SCRAPERS###########################################################

def free_proxy_list():
	PROTOCOLS = ['http', 'https', 'socks4', 'socks5']
	for protocol in PROTOCOLS:
		url = 'https://www.proxy-list.download/api/v0/get?l=en&t={protocol}'.format(protocol=protocol)
		print(url)
		try:
			r = requests.get(url)
			j = json.loads(r.text)
			rows = j[0]['LISTA']
			for row in rows:
				d = {'protocol': protocol,
					 'ip': row['IP'],
					 'port': row['PORT'],
					 'country_code': row['ISO'],
					 'type': row['ANON'],
					 'last_checked': datetime.now(),
					 'curl': 'http://' + row['IP'] + ':' + row['PORT']}
				print(d)
				write_to_db(d)
		except:
			print('Unexpected error')


def ssl_proxies():
	url = 'https://sslproxies.org/'
	r = requests.get(url)
	response = etree.HTML(r.text)
	rows = response.xpath("//div[@class='table-responsive']//tbody//tr")
	print(len(rows))
	for row in rows:
		protocol = 'https' if row.xpath(".//td[7]/text()")[0] == 'yes' else 'http'

		ip = row.xpath('.//td[1]/text()')[0]
		port = row.xpath('.//td[2]/text()')[0]

		d = {'protocol': protocol,
			 'ip': ip,
			 'port': port,
			 'country_code': row.xpath('.//td[3]/text()')[0],
			 'type': row.xpath('.//td[5]/text()')[0],
			 'last_checked': datetime.now(),
			 'curl': protocol + '://' + ip + ':' + port}
		print(d)
		write_to_db(d)

def free_proxy_lists_net():
	init_url = 'http://www.freeproxylists.net/ru/?page=1'
	r = requests.get(init_url)
	print(r.text)

	response = etree.HTML(r.text)

def free_proxy_cz():
	page = 1
	url = 'http://free-proxy.cz/en/proxylist/main/{page}'
	header = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.52 Safari/536.5"}
	r = requests.get(url.format(page=page),headers=header)

	# last_page =
	response = etree.HTML(r.text)
	print(r.text)
	pag_els = response.xpath("//div[@class='paginator']//a")
	print(pag_els[-2].xpath('./text('))
	rows = response.xpath("//table[@id='proxy_list']//tr")
	# for row in rows:
	#
	# print(r.text)
# free_proxy_cz()


# def main_job():

#############################################################################################################
#############################################################################################################


if __name__ == '__main__':
	scheduler = BlockingScheduler({'apscheduler.executors.default': {
		'class': 'apscheduler.executors.pool:ThreadPoolExecutor', 'max_workers': '2'}})

	scheduler.add_job(main_check, 'interval', seconds=300, name='select_all')
	scheduler.add_job(free_proxy_list, 'interval', minutes=10)
	scheduler.add_job(ssl_proxies, 'interval', minutes=10)

	try:
		scheduler.start()
	except (KeyboardInterrupt, SystemExit):
		pass
