import requests, logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

_INSTRUMENT_ID = '9270'
_END_DATE = '2022-09'
_OPTION_TYPE = 'PUT'

list_of_option_ids = []
list_of_options = []

URL = 'https://www.avanza.se/optioner-lista.html?name=&underlyingInstrumentId=' + _INSTRUMENT_ID + '&callIndicators=' + _OPTION_TYPE + '&selectedEndDates=' + _END_DATE + '&sortField=NAME&sortOrder=ASCENDING&activeTab=overview'
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
	def __init__(self, oid, name, price, greeks, url, strike_price):
		self.oid = oid
		self.name = name.lower()
		self.price = price
		self.greeks = greeks
		self.url = url
		self.strike_price = strike_price


def get_page(URL):
	logging.info(f'Requesting page {URL}')
	try:
		page = requests.get(URL)
	except Exception as e:
		logging.error(f'Encountered an issue when requesting page {URL}')
		logging.error(f'Stack trace: {e}')

	logging.info(f'Received page! Proceeding to parse HTML...')
	return BeautifulSoup(page.content, 'html.parser')

def get_options_list(soup):
	logging.info(f'Finding div containing list of options...')
	content_table = soup.find(id='contentTable')
	logging.info(f'Finding tbody containing list of options...')
	return content_table.find('tbody')

def get_list_of_option_ids(html_tbody):
	logging.info(f'Extracting option IDs from tbody...')
	list = []
	counter = 0

	for tr in html_tbody.find_all('tr'):
		#Find oid and name of option
		oid = tr.get('data-oid')
		name_element = tr.find('a', {"class": "link"})
		name = name_element.get('title')

		#Create new Option object and add to list
		option = Option(oid, name, None, None, None, None)
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
		return iv

def parse_strike_price(sp):
	try:
		numeric_filter = filter(str.isdigit, sp)
		numeric_string = ''.join(numeric_filter)
		return float(numeric_string)
	except Exception as e:
		logging.error(f'Exception when parsing strike price of option: {e}')

def get_option(option):
	#Construct URL to Avanzas option detail page
	option_details_url = OPTION_DETAILS_BASE_URL + option.oid + '/' + option.name

	#Request page and turn into BeautifulSoup object
	page = requests.get(option_details_url, allow_redirects=True)
	soup = BeautifulSoup(page.content, 'html.parser')

	#Find span containing sell price
	price_element = soup.find('span', {"class": "sellPrice"})
	price = parse_option_price(price_element.text)

	#Find element containing option info
	info_element = soup.find_all('ul', {"class": "primaryInfo"})[1]
	info_element_spans = info_element.find_all('span', {"class": "data"})

	#Find element contianing greeks
	greeks_element = soup.find('div', {"class": "derivative_greeks_data"})
	dl_element = greeks_element.find('dl')
	all_greeks_element = dl_element.find_all('dd')

	#Find strike price
	strike_price = parse_strike_price(info_element_spans[1].text.replace('&nbsp;',''))

	#Find IV
        #span = all_greeks_element[0].find('span').text
	iv = None#parse_option_iv(span)

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

	#Return
	return Option(option.oid, option.name, price, greeks, option_details_url, strike_price)

def get_options(list_of_options):
	logging.info(f'Looping through list of option ids I found...This will take some time, please be patient!')
	length = len(list_of_options)
	counter = 0
	list = []

	for option in list_of_options:
		list.append(get_option(option))
		counter = counter + 1
		logging.info(f'Progress: {counter}/{length}')
	return list

soup = get_page(URL)
html_tbody = get_options_list(soup)
list_of_options = get_list_of_option_ids(html_tbody)
options = get_options(list_of_options)

for option in options:
	logging.info(f'Name: {option.name}\tPrice: {option.price}\tStrike price: {option.strike_price}\tGreeks:')
	logging.info(f'\tIV: {option.greeks.iv}\tIV Buy: {option.greeks.iv_buy}\tIV Sell: {option.greeks.iv_sell}\tDelta: {option.greeks.delta}\tTheta: {option.greeks.theta}\tVega: {option.greeks.vega}\tGamma: {option.greeks.gamma}\tRho: {option.greeks.rho}')

#print(list_of_option_ids)
