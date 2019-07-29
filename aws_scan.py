import json
import concurrent.futures
import nmap
import requests

from psycopg2 import sql, IntegrityError, pool
from contextlib import contextmanager
import local_congfig
##SETTING UP DB CON
db = pool.SimpleConnectionPool(1, 10,
							   user=local_congfig.DB_USER, password=local_congfig.DB_PASS,
							   database=local_congfig.DB_NAME, host=local_congfig.DB_HOST)
print('Successfully connected to db...')

@contextmanager
def get_connection():
	con = db.getconn()
	try:
		yield con
	finally:
		db.putconn(con)


def create_table():
	with get_connection() as conn:

		cursor = conn.cursor()
		query = sql.SQL("CREATE TABLE IF NOT EXISTS {} (curl VARCHAR (50) PRIMARY KEY, ip VARCHAR (50) NOT NULL, protocol VARCHAR (10) NOT NULL,port INT NOT NULL )").format(sql.Identifier('aws'))
		cursor.execute(query)
		cursor.close()
		conn.commit()


def write_to_db(d):
	with get_connection() as conn:
		try:
			cursor = conn.cursor()
			query = sql.SQL("INSERT INTO {} VALUES (%s, %s, %s, %s)").format(sql.Identifier('aws'))
			print(query)
			cursor.execute(query, (d['curl'], d['ip'], d['protocol'], d['port']))
			cursor.close()
			conn.commit()
		except:
			conn.rollback()


def scan_range(ip_range):
	nm = nmap.PortScanner()
	nm.scan(ip_range, '80,1080,8080,8081,8888,9999,3128,443,8443')
	for host in nm.all_hosts():
		print('----------------------------------------------------')
		print('Host : %s (%s)' % (host, nm[host].hostname()))
		print('State : %s' % nm[host].state())
		for proto in nm[host].all_protocols():
			print('----------')
		print('Protocol : %s' % proto)

		lport = nm[host][proto].keys()
		lports = sorted(lport)
		for port in lports:
			if nm[host][proto][port]['state'] == 'open':
				if port == '1080':
					d = {'curl': 'http://' + host + ':' + str(port),
						 'ip': host,
						 'protocol': 'socks4',
						 'port': str(port)}
					write_to_db(d)
				elif port == '443' or port == '8443':
					d = {'curl': 'https://' + host + ':' + str(port),
						 'ip': host,
						 'protocol': 'https',
						 'port': str(port)}
					write_to_db(d)
				else:
					d = {'curl': 'http://' + host + ':' + str(port),
						 'ip': host,
						 'protocol': 'http',
						 'port': str(port)}
					write_to_db(d)
			print('port : %s\tstate : %s' % (port, nm[host][proto][port]['state']))


create_table()
with concurrent.futures.ThreadPoolExecutor(max_workers=None) as executor:
	ip_ranges = requests.get('https://ip-ranges.amazonaws.com/ip-ranges.json')
	j = json.loads(ip_ranges.text)
	ranges = [prefix['ip_prefix'] for prefix in j['prefixes']]
	print(ranges)
	print(len(ranges))
	futures = [executor.submit(scan_range, ip_range) for ip_range in ranges]
	for future in concurrent.futures.as_completed(futures):
		try:
			data = future.result()
			print(data)
		except Exception as exc:
			print(exc)





