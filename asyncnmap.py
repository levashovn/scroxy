import nmap
import aionmap
# nm = nmap.PortScanner()
# nm.scan('31.40.16.0-255', '21-443')
# nm.command_line()
# print(nm.all_hosts())
# for host in nm.all_hosts():
# 	print('Host : %s (%s)' % (host, nm[host].hostname()))
# 	print('State : %s' % nm[host].state())
# 	for proto in nm[host].all_protocols():
# 		print('----------')
# 		print('Protocol : %s' % proto)
# 		lport = nm[host][proto].keys()
# 		for port in lport:
# 			print('port : %s\tstate : %s' % (port, nm[host][proto][port]['state']))



import asyncio
from datetime import datetime
import aiofiles

import aiohttp

proxy_type = "http"
test_url = "http://api.ipify.org"
timeout_sec = 4

diapazons = open('diapazons.txt')
diapazonsList = diapazons.read().splitlines()


async def is_bad_proxy(diapazon):
	scanner = aionmap.PortScannerYield()
	async for result in scanner.scan(diapazon, ports='8080,80', arguments='--open', sudo=True,
									 sudo_passwd='1991'):
		if isinstance(result, Exception):
			print("error")
		elif result.hosts_up == 0:
			print('0 hosts up')
		else:
			print(result.get_raw_data())
			# write_working(result.summary().get('NmapHost') +)


async def write_working(ipport):
	filename = 'probably_proxies.txt'
	# with open(filename, 'a') as file:
	#     file.write(ipport + '\n')

	async with aiofiles.open(filename, 'a') as f:
		await f.write(ipport + '\n')


tasks = []
loop = asyncio.get_event_loop()

for item in diapazonsList:
	tasks.append(asyncio.ensure_future(is_bad_proxy(item)))

print("Starting... \n")
loop.run_until_complete(asyncio.wait(tasks))
print("\n...Finished")
loop.close()
