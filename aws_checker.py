import concurrent.futures
import requests
from psycopg2 import sql, IntegrityError, pool
from contextlib import contextmanager
import local_congfig

db = pool.SimpleConnectionPool(1, 10,
							   user=local_congfig.DB_USER, password=local_congfig.DB_PASS,
							   database=local_congfig.DB_NAME, host=local_congfig.DB_HOST)

# proxyList = []
@contextmanager
def get_connection():
	con = db.getconn()
	try:
		yield con
	finally:
		db.putconn(con)


def select_proxies():
	with get_connection() as conn:

		try:
			proxyList = []
			cursor = conn.cursor()
			query = "select * from aws"
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
			delete_query = 'DELETE FROM aws WHERE curl = %s;'
			cursor.execute(delete_query, (curl,))
			cursor.close()
			conn.commit()
			return proxies
		except:
			conn.rollback()


def init_connection(proxy):
	print(proxy)
	protocol, ip, port = proxy['protocol'], str(proxy['ip']), str(proxy['port'])
	##SOCKS ARE CONNECTING  LIKE THIS {'http': 'socks5//:ip'}

	try:
		r = requests.get(protocol + '://api.ipify.org/', proxies={protocol: protocol + '://' + ip + ':' + port},
						 timeout=10, allow_redirects=False)

		if r.text != ip:
			raise Exception
		print(r.text, ip)
		return {'proxy': proxy, 'status': 'alive'}

	except Exception as exc:
		print(exc)
		delete_dead(proxy['curl'])
		return {'proxy': proxy, 'status': 'dead'}



proxyList = select_proxies()
with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:

	futures = [executor.submit(init_connection, proxy) for proxy in proxyList[len(proxyList)//2:]]
	for future in concurrent.futures.as_completed(futures):
		try:
			data = future.result()
			print(data)
		except Exception as exc:
			print(exc)



