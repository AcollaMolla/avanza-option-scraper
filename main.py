#!/usr/bin/python3

import requests, logging, csv, re, pathlib
from bs4 import BeautifulSoup
from datetime import datetime
from os.path import exists

logging.basicConfig(level=logging.DEBUG, filename='main.log')

_INSTRUMENT_ID = '9270'
_END_DATES = ['2022-09', '2022-10', '2022-11', '2022-12', '2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06']
_OPTION_TYPE = 'PUT'

list_of_all_options = []

#BASE_URL = 'https://www.avanza.se/optioner-lista.html?name=&underlyingInstrumentId=' + _INSTRUMENT_ID + '&callIndicators=' + _OPTION_TYPE
BASE_URL = 'https://www.avanza.se/optioner-lista.html?name=&underlyingInstrumentId='
OPTION_DETAILS_BASE_URL = 'https://www.avanza.se/optioner/om-optionen.html/'

class Greeks:
	def __init__(self, iv, iv_buy, iv_sell, delta, theta, vega, gamma, rho) :
		self.iv = iv
		self.iv_buy = iv_buy
		self.iv_sell = iv_sell
		self.delta = delta
		self.theta = theta
		self.vega = vega
		self.gamma = gamma
		self. rho = rho

class Option:
	def __init__(self, oid, name, price, greeks, url, strike_price, underlying_last_price, strike_date):
		self.oid = oid
		self.name = name.lower()
		self.price = price
		self.greeks = greeks
		self.url = url
		self.strike_price = strike_price
		self.underlying_last_price = underlying_last_price
		self.strike_date = strike_date

	def get_scrape_date(self):
		return str(datetime.today().strftime('%Y-%m-%d'))

#Check if CSV exist or create it
def create_csv():
	today = datetime.today().strftime('%Y-%m-%d')
	filename = today + '.csv'
	header = ['oid', 'name', 'price', 'iv', 'iv_buy', 'iv_sell', 'delta', 'theta', 'vega', 'gamma', 'rho', 'url', 'strike_price', 'underlying_last_price', 'strike_date', 'scrape_date']
	abs_path = str(pathlib.Path(__file__).parent.resolve())

	logging.info(f'Checking if CSV file {filename} exists...')
	logging.debug(f'Absolute path of Python script: {abs_path}')

	if exists(abs_path + '/data/' + filename):
		return abs_path + '/data/' + filename

	else:
		logging.warning(f'CSV file {filename} dont exist. Creating it...')
		with open(abs_path + '/data/' + filename, 'w', encoding='UTF-8') as f:
			writer = csv.writer(f)
			writer.writerow(header)
		return abs_path + '/data/' + filename

#Write all options to CSV
def to_csv(options, filepath):
	scrape_date = datetime.today().strftime('%Y-%m-%d')
	with open(filepath, 'a', encoding='UTF-8') as f:
		writer = csv.writer(f)
		for option in options:
			#Create a list of option data
			if option.greeks is not None:
				data = [option.oid, option.name, option.price, option.greeks.iv, option.greeks.iv_buy, option.greeks.iv_sell, option.greeks.delta, option.greeks.theta, option.greeks.vega, option.greeks.gamma, option.greeks.rho, option.url, option.strike_price, option.underlying_last_price, option.strike_date, scrape_date]
			else:
				data = [option.oid, option.name, option.price, None, None, None, None, None, None, None, None, option.url, option.strike_price, option.underlying_last_price, option.strike_date, scrape_date]
			writer.writerow(data)

#Get a list of all underlying stocks
def get_underlying_instrument_ids(soup):
	logging.info(f'Scraping page for all available underlying stocks...')
	list_of_underlying = []

	#Find HTML elements containing underlyings
	underlying_elem = soup.find(id='underlyingInstrumentId')
	option_elems = underlying_elem.find_all('option')

	#Loop through the elems and get IDs
	for option_elem in option_elems:
		list_of_underlying.append(option_elem.get('value'))

	#Return
	logging.info(f'Found {len(list_of_underlying)} underlyings!')
	return list_of_underlying

#construct URL param list of all end dates. NOTE: Perhaps this is not necessary...It seems like a empty selectedEndDates list result in all end dates.
def construct_url(url, underlying_id):
	logging.debug(f'Constructing end date parameters from list: {_END_DATES}')
	end_date_param_name = '&selectedEndDates='
	end_dates_param_list = ''

	#Add current instrument ID to url
	url = url + underlying_id + '&callIndicators=PUT'

	#Loop through all end dates and add them to url
	for end_date in _END_DATES:
		end_dates_param_list = end_dates_param_list + end_date_param_name + end_date

	#Return
	logging.debug(f'End date params list: {end_dates_param_list}')
	return url + end_dates_param_list + '&sortField=NAME&sortOrder=ASCENDING&activeTab=overview'

def get_page(URL):
	logging.info(f'Requesting page {URL}')
	try:
		page = requests.get(URL)
	except Exception as e:
		logging.error(f'Encountered an issue when requesting page {URL}')
		logging.error(f'Stack trace: {e}')

	logging.debug(f'Received page! Proceeding to parse HTML...')
	return BeautifulSoup(page.content, 'html.parser')

def get_options_list(soup):
	logging.debug(f'Finding div containing list of options...')
	content_table = soup.find(id='contentTable')
	logging.debug(f'Finding tbody containing list of options...')
	return content_table.find('tbody')

def get_list_of_option_ids(html_tbody):
	logging.debug(f'Extracting option IDs from tbody...')
	list = []
	counter = 0

	for tr in html_tbody.find_all('tr'):
		#Find oid and name of option
		oid = tr.get('data-oid')
		name_element = tr.find('a', {"class": "link"})
		name = name_element.get('title')

		#Create new Option object and add to list
		option = Option(oid, name, None, None, None, None, None, None)
		list.append(option)

		#Increase counter
		counter = counter + 1

	#Return
	logging.info(f'Found {counter} options!')
	return list

def parse_option_price(price):
	if price == '-':
		return None
	else:
		return float(price.replace(',', '.'))

def parse_option_iv(iv):
	if iv == '-':
		return None
	else:
		iv = parse_underlying_price(iv)
		return iv

def parse_strike_price(sp):
	try:
		numeric_filter = filter(str.isdigit, sp)
		numeric_string = ''.join(numeric_filter)
		return float(numeric_string)
	except Exception as e:
		logging.error(f'Exception when parsing strike price of option: {e}')

def parse_underlying_price(p):
	try:
		q = re.sub('[^0-9,]', '', p)
		q = q.replace(',', '.')
		return float(q)
	except Exception as e:
		logging.error(f'Exception when parsing underlying pricer: {e}')

def get_option(option):

	logging.debug(f'Scraping data for option: {option.name}')

	#Check if option name contians a '.' indicating decimal strike price. Then we need to replace with '-'
	if '.' in option.name:
		option.name = option.name.replace('.', '-')

	#Construct URL to Avanzas option detail page
	option_details_url = OPTION_DETAILS_BASE_URL + option.oid + '/' + option.name

	logging.debug(f'Scraping data for option: {option_details_url}')

	#Request page and turn into BeautifulSoup object
	page = requests.get(option_details_url, allow_redirects=True)
	soup = BeautifulSoup(page.content, 'html.parser')

	#Find span containing sell price
	price_element = soup.find('span', {"class": "sellPrice"})

	try:
		price = parse_option_price(price_element.text)
	except Exception as e:
		logging.error(f'Error when collecting option price: {e}')

	#find element containing underlying instrument data
	underlying_elem = soup.find('div', {"class": "underlying_instrument"})
	underlying_last_price = -1

	try:
		ul_elem = underlying_elem.find('ul', {"class": "cleanList"})

		if 'omxs' in option.name:
			logging.debug(f'Options underlying is OMX index named {option.name}. Applying special scraping rules...')
			li_elem = ul_elem.find_all('li')[1]

		elif 'omxesg' in option.name:
			logging.debug(f'Options underlying is OMXESG index named {option.name}. Applying special scraping rules...')
			li_elem = ul_elem.find_all('li')[1]

		else:
			li_elem = ul_elem.find_all('li')[3]

		span_elem = li_elem.find('span', {"class": "lastPrice"})
		underlying_last_price = parse_underlying_price(span_elem.find('span').text)

	except Exception as e:
		logging.error(f'Could not parse underlying instrument last price: {e}')

	#Find element containing option info
	try:
		info_element = soup.find_all('ul', {"class": "primaryInfo"})[1]
		info_element2 = soup.find_all('ul', {"class": "primaryInfo"})[0]
	except Exception as e:
		logging.error(f'Could not find list of option primary info: {e}')

	try:
		info_element_spans = info_element.find_all('span', {"class": "data"})
		info_element_spans2 = info_element2.find_all('span', {"class": "data"})

		#Find strike price
		strike_price = parse_underlying_price(info_element_spans[1].text.replace('&nbsp;',''))

		#Find strike date
		strike_date = info_element_spans2[2].text

	except Exception as e:
		logging.error(f'Error when collecting option strike price: {e}')

	#Find element contianing greeks
	greeks_element = soup.find('div', {"class": "derivative_greeks_data"})

	try:
		dl_element = greeks_element.find('dl')
		all_greeks_element = dl_element.find_all('dd')

		#Find IV
        	#span = all_greeks_element[0].find('span').text
		iv = None

		#Find IV buy
		span = all_greeks_element[0].find('span').text
		iv_buy = parse_option_iv(span)

		#Find IV sell
		iv_sell = None

		#Find delta
		span = all_greeks_element[2].find('span').text
		delta = parse_option_price(span)

		#Find theta
		span = all_greeks_element[3].find('span').text
		theta = parse_option_iv(span)

		#Find vega
		span = all_greeks_element[4].find('span').text
		vega = parse_option_iv(span)

		#Find gamma
		gamma = None

		#Find rho
		rho = None

		#Create a new Greeks object
		greeks = Greeks(iv, iv_buy, iv_sell, delta, theta, vega, gamma, rho)

	except Exception as e:
		logging.error(f'Error when parsing option greeks: {e}')

	#Return
	try:
		o = Option(option.oid, option.name, price, greeks, option_details_url, strike_price, underlying_last_price, strike_date)
	except Exception as e:
		logging.error(f'Could not create Option object. Will return Option with empty data: {e}')
		o = Option(option.oid, option.name, None, None, option_details_url, None, None, None)
	return o

def get_options(list_of_options):
	logging.debug(f'Looping through list of option ids I found...This will take some time, please be patient!')
	length = len(list_of_options)
	counter = 0
	list = []

	for option in list_of_options:
		list.append(get_option(option))
		counter = counter + 1
		logging.debug(f'Progress: {counter}/{length}')
	return list

url = construct_url(BASE_URL, _INSTRUMENT_ID)
soup = get_page(url)
list_of_underlying = get_underlying_instrument_ids(soup)

filepath = create_csv()

for underlying_id in list_of_underlying:
	logging.info(f'Collecting option info for underlying id {underlying_id}')
	url = construct_url(BASE_URL, underlying_id)
	soup = get_page(url)
	html_tbody = get_options_list(soup)
	list_of_options = get_list_of_option_ids(html_tbody)
	options = get_options(list_of_options)

	#Write options to csv
	to_csv(options, filepath)

logging.info(f'Done!')

#for option in options:
#	logging.info(f'Name: {option.name}\tPrice: {option.price}\tStrike price: {option.strike_price}\tGreeks:')
#	logging.info(f'\tIV: {option.greeks.iv}\tIV Buy: {option.greeks.iv_buy}\tIV Sell: {option.greeks.iv_sell}\tDelta: {option.greeks.delta}\tTheta: {option.greeks.theta}\tVega: {option.greeks.vega}\tGamma: {option.greeks.gamma}\tRho: {option.greeks.rho}')

#print(list_of_option_ids)
