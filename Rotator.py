# from fake_useragent import UserAgent
import json
import random
import requests
# from amplib.Collections.Parse.HTML import HtmlObject
from bs4 import BeautifulSoup as bs
from requests.exceptions import TooManyRedirects, RequestException, ProxyError, ConnectionError
from selenium import webdriver
import time
import traceback

import asyncio
from datetime import datetime
import aiofiles
import aiohttp
proxy_type = "http"
test_url = "http://api.ipify.org"
timeout_sec = 4

proxylistfile = open('proxy_list.txt')
proxyList = proxylistfile.read().splitlines()
# proxyList = proxylistfile.read().split(' ')

async def is_bad_proxy(ipport):
	session = aiohttp.ClientSession()
	try:
		# proxy_items = await ipport.split('://')
		# protocol, seek = proxy_items[0], proxy_items[1]
		response = await session.get(test_url, proxy=ipport, timeout=timeout_sec, allow_redirects=False)
		print(ipport)
		response_text = await response.text()
		if not response_text in ipport:
			raise Exception
		else:
			await write_working(ipport)
			print("Working:", ipport)
			await session.close()
	except:
		await session.close()
		print("Not Working:", ipport)


async def write_working(ipport):
	filename = 'working-proxies.txt'
	# with open(filename, 'a') as file:
	#     file.write(ipport + '\n')

	async with aiofiles.open(filename, 'a') as f:
		await f.write(ipport + '\n')



def main():
	tasks = []
	loop = asyncio.get_event_loop()

	for item in proxyList:
		tasks.append(asyncio.ensure_future(is_bad_proxy("http://" + item)))

	print("Starting... \n")
	loop.run_until_complete(asyncio.wait(tasks))
	print("\n...Finished")
	loop.close()


class ProxyRotator():
	def __init__(self):
		main()
		self.options = webdriver.ChromeOptions()
		self.options.add_argument('--headless')
		self.options.add_argument('--disable-gpu')
		self.options.add_argument("--screen-size=1980x1080")
		self.options.add_argument('--disable-dev-shm-usage')
		self.options.add_argument('--no-sandbox')
		# self.free_proxy_list()
		self.IPs = self.read_proxy_list()

	def read_proxy_list(self):
		proxies = []
		f = open('working-proxies.txt', 'r')
		proxy_list = f.read().splitlines()

		for proxy in proxy_list:
			proxy_items = proxy.split('://')
			d = {'protocol': proxy_items[0],
				 'ip': proxy_items[1].split(':')[0],
				 'port': proxy_items[1].split(':')[1]}

			proxies.append(d)
		return proxies

	def gimme_proxy(self):
		gimmeproxyUrl = 'https://gimmeproxy.com/api/getProxy?api_key=03f8d9e9-5c61-4c5d-9c05-9b7b947db22c&protocol=https'
		proxies = []
		for i in range(1, 10):
			code = requests.get(gimmeproxyUrl).text
			j = json.loads(code)
			protocol, ip, port = j['protocol'], j['ip'], j['port']
			proxies.append({
				'protocol': protocol,
				'ip': ip,
				'port': port
			})
		return proxies

	def free_proxy_list(self):
		proxies = []
		driver = webdriver.Chrome(chrome_options=self.options)
		driver.get('https://www.sslproxies.org/')
		next_status = driver.find_element_by_xpath("//li[@id='proxylisttable_next']").get_attribute('class')
		while not 'disabled' in next_status:
			next_status = driver.find_element_by_xpath("//li[@id='proxylisttable_next']").get_attribute('class')
			next = driver.find_element_by_xpath("//li[@id='proxylisttable_next']//a")
			try:
				code = driver.page_source
				html = bs(code, 'html.parser')
				rows = html.find('tbody').find_all('tr')
				print(len(rows))
				# rows = html.getElementByTagName('tbody').getElementsByTagName('tr')
				for row in rows:
					items = row.find('td')
					d = {'protocol': 'https',
						 'ip': items[0].text,
						 'port': items[1].text}
					proxies.append(d)
				next.click()
				time.sleep(1)
			except:
				break
		f = open('scraped_proxies.txt', 'w')
		f.write(proxies)
		f.close()
		return proxies

	def hidemyname(self):
		# prox = Proxy()
		# prox.proxy_type = ProxyType.MANUAL
		# prox.ssl_proxy = '195.123.228.82:8118'
		# capabilities = webdriver.DesiredCapabilities.CHROME
		# prox.add_to_capabilities(capabilities)
		proxies = []
		first_page = 'https://hidemyna.me/en/proxy-list/?type=s'
		driver = webdriver.Chrome(chrome_options=self.options)

		driver.get(url=first_page)
		time.sleep(10)
		page_cont = driver.find_elements_by_xpath("//div[@class='proxy__pagination']//li//a")
		pages = [page.get_attribute('href') for page in page_cont]
		for page in pages[1:]:
			driver.get(page)
			code = driver.page_source
			html = HtmlObject(code)
			rows = html.find(class_='proxy__t').find_all('tr')
			for row in rows[1:]:
				items = row.find('td')
				d = {'protocol': 'https',
					 'ip': items[0].text,
					 'port': items[1].text}
				proxies.append(d)
			time.sleep(2)
		return proxies

	## need request.exceptions.ProxyError in try
	def initiate_connection(self, url, cookies={}, headers={}):
		self.check_list()
		while True:
			proxy_index = self.random_proxy()
			proxy = self.IPs[proxy_index]
			proxie_dict = {proxy['protocol']: proxy['protocol'] + '://' + proxy['ip'] + ':' + proxy['port']}
			print(proxie_dict)
			try:
				r = requests.get(url=url, proxies=proxie_dict, cookies=cookies, headers=headers)
				return r.text
			except TooManyRedirects as e:
				# try:
				print('raising RequestExc')
				raise RequestException(e)
			# 	# except (TimeoutError, NewConnectionError, MaxRetryError, ProxyError) as e:
			# 	#     print('raising RequestExc')
			# 	#     # print('got here')
			# 	#     raise RequestException(e)
			#
			except RequestException:
				del self.IPs[proxy_index]
				print('Proxy ' + proxy['ip'] + ':' + proxy['port'] + ' was dead and deleted.')
				# finally:
				#     del self.IPs[proxy_index]
				#     print('Proxy ' + proxy['ip'] + ':' + proxy['port'] + ' was dead and deleted.')
			## it was throwing a chain of exceptions in my case, so I'm just using Exception, u requests.exceptions

	def give_proxy_dict(self):
		proxies_dict = []
		for proxy in self.IPs:
			d = {proxy['protocol']: proxy['protocol'] + '://' + proxy['ip'] + ':' + proxy['port']}
			proxies_dict.append(d)
		return proxies_dict

	def random_proxy(self):
		return random.randint(0, len(self.IPs) - 1)

	def count_proxies(self):
		return len(self.IPs)

	def check_list(self):
		proxy_list_len = self.count_proxies()
		if proxy_list_len > 0:
			pass
		else:
			new_hmn_proxies = self.free_proxy_list()
			for proxy in new_hmn_proxies:
				self.IPs.append(proxy)
			print(proxy_list_len)

PR = ProxyRotator()
print(PR.initiate_connection('http://api.ipify.org?format=json'))
print(PR.initiate_connection('http://api.ipify.org?format=json'))
print(PR.initiate_connection('http://api.ipify.org?format=json'))
print(PR.initiate_connection('http://api.ipify.org?format=json'))
print(PR.initiate_connection('http://api.ipify.org?format=json'))
print(PR.initiate_connection('http://api.ipify.org?format=json'))
print(PR.initiate_connection('http://api.ipify.org?format=json'))




