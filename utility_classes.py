import requests
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from pprint import pprint

class Company:
	def __init__(self, symbol):
		self.symbol = symbol

	def get_market_cap(self):
		try:
			url = 'https://financialmodelingprep.com/api/v3/company/profile/' + str(self.symbol)
			r = requests.get(url)
			rjs = json.loads(r.text)
		except Exception as e:
			print(e)
		else:
			market_cap = float(rjs['profile']['mktCap'])
		return market_cap

	def get_1_year_target(self):

		url = 'https://ca.finance.yahoo.com/quote/' + str(self.symbol)
		xpath = '/html/body/div[1]/div/div/div[1]/div/div[3]/div[1]/div/div[1]/div/div/div/div[2]/div[2]/table/tbody/tr[8]/td[2]/span'

		options = Options()
		options.headless = True
		driver = webdriver.Firefox(options=options)

		try:
			driver.get(url)
			time.sleep(2)
		except Exception as e:
			print(e)
			try:
				driver.get(url)
				time.sleep(2)
			except Exception as e:
				print(e)
				one_year_target = None
		else:
			one_year_target = float(driver.find_element_by_xpath(xpath).get_attribute('innerHTML'))
		finally:
			driver.quit()

		return one_year_target

	def get_latest_price(self):
		try:
			url = 'https://financialmodelingprep.com/api/v3/quote/' + str(self.symbol)
			r = requests.get(url)
			rjs = json.loads(r.text)
		except Exception as e:
			print(e)
		else:
			price = float(rjs[0]['price'])
		return price

	def get_january_price(self):
		try:
			url = 'https://financialmodelingprep.com/api/v3/historical-price-full/' + str(self.symbol) + '?serietype=line'
			r = requests.get(url)
			day_closing_price_list = json.loads(r.text)['historical']
		except Exception as e:
			print(e)
		else:
			first_day = datetime.strptime(day_closing_price_list[0]['date'], "%Y-%m-%d")
			jan_2 = datetime.strptime("2020-01-02", "%Y-%m-%d")

			if first_day <= jan_2:
				for item in day_closing_price_list:
					if item['date'] == "2020-01-02":
						jan_price = float(item['close'])
						return jan_price
			else:
				return False

	def get_percent_down(self):
		january_price = self.get_january_price()
		latest_price = self.get_latest_price()
		return (january_price - latest_price) / january_price

	def get_options_dict(self):
		url = 'https://api.tdameritrade.com/v1/' \
		'marketdata/chains?apikey=LNJSWNR9RYZTUJQZRBHGJV5DZ5S9JDCY' \
		'&symbol=' + str(self.symbol)
		try:
			r = requests.get(url)
			rjs = json.loads(r.text)
		except Exception as e:
			print(e)
			call_options = None
			put_options = None
		else:
			call_options = rjs['callExpDateMap']
			put_options = rjs['putExpDateMap']
			
		return call_options, put_options

class Symbols:
	def __init__(self, market):
		self.market = str(market) # ETF|MUTUAL_FUND|COMMODITY|INDEX|CRYPTO|FOREX|TSX|AMEX|NASDAQ|NYSE|EURONEXT

	def get_all_symbols(self):
		"""Returns the list of symbols for each exchange"""
		try:
			r = requests.get('https://financialmodelingprep.com/api/v3/search?query=&exchange=' + self.market)
		except Exception as e:
			print(e)
		else:
			symbols = []
			for item in json.loads(r.text):
				symbols.append(str(item['symbol']))

		return symbols

class Strategy():
	def __init__(self, symbol, market_cap, target, latest_price, \
		jan_1st_price, market, percent_down, discount_from_jan, \
		discount_from_target, mid_cap_size, strategy):

		self.symbol = symbol
		self.market_cap = market_cap
		self.target = target
		self.latest_price = latest_price
		self.jan_1st_price = jan_1st_price
		self.market = market
		self.percent_down = percent_down
		self.discount_from_jan = discount_from_jan
		self.discount_from_target = discount_from_target
		self.mid_cap_size = mid_cap_size
		self.strategy = strategy
		self.document_name = (str(self.market) \
			+ '_' \
			+ str(self.strategy) \
			+ '_' \
			+ str(mid_cap_size) \
			+ '_cap_size_' \
			+ str(100 * self.discount_from_jan) \
			+ '_percent_from_jan' \
			+ '_analyst_target_difference_of_' \
			+ str(100 * self.discount_from_target) \
			+ '_percent.txt')

class UnderpricedStocksStrategy(Strategy):
	def execute_strategy(self):
		"""
		This strategy tests:
		1) Is the company market cap a mid-cap
		2) Is the company at least 50% down from january high
		3) Is the company target at least 20% below analyst target
		"""
		if (self.is_market_cap_mid_size() and \
			self.is_price_at_least_X_percent_down() and \
			self.is_company_target_at_least_X_percent_higher()):
			self.create_record()

	def is_market_cap_mid_size(self):
		if self.market_cap <= float(self.mid_cap_size):
			return True
		else:
			return False

	def is_price_at_least_X_percent_down(self):
		if self.percent_down >= self.discount_from_jan:
			return True
		else:
			return False

	def is_company_target_at_least_X_percent_higher(self):
		if self.target != 0:
			if (self.target - self.latest_price) / self.target >= self.discount_from_target:
				return True
			else:
				return False
		else:
			return False

	def create_record(self):
		"""Opens the document and werites info"""
		f = open(self.document_name, "a+")
		f.write("{} {} {} {} {}\r".format(self.symbol, self.market_cap, self.latest_price, self.target, self.percent_down))
		print("#####################################################Created record for {}".format(self.symbol))
		f.close()

class UnderpricedOptionsStrategy():
	def __init__(self, company, market, threshold):
		self.company = company
		self.options_dict = self.company.get_options_dict()
		self.call_options = self.options_dict[0]
		self.put_options = self.options_dict[1]
		self.market = market
		self.threshold = threshold
		self.document_name = str(self.market) + '_underpriced_options.txt'

	def execute_strategy(self):
		for expiry in self.call_options:
			for strike in self.call_options[expiry]:
				call_ratio = float(self.call_options[expiry][strike][0]['ask']) / (float(self.call_options[expiry][strike][0]['ask']) + float(strike))
				put_ratio = float(self.put_options[expiry][strike][0]['ask']) / (float(self.put_options[expiry][strike][0]['ask']) + float(strike))
				total_ratio = call_ratio + put_ratio
				if 0 < total_ratio <= self.threshold:
					description = self.call_options[expiry][strike][0]['description']
					latest_price = self.company.get_latest_price()
					call_price = float(self.call_options[expiry][strike][0]['ask'])
					put_price = float(self.put_options[expiry][strike][0]['ask'])
					call_theoretical_price = float(self.call_options[expiry][strike][0]['theoreticalOptionValue'])
					call_theoretical_vol = float(self.call_options[expiry][strike][0]['theoreticalVolatility'])
					put_theoretical_price = float(self.put_options[expiry][strike][0]['theoreticalOptionValue'])
					put_theoretical_vol = float(self.put_options[expiry][strike][0]['theoreticalVolatility'])
					self.create_option_record(description, latest_price, call_price, put_price, call_theoretical_vol, \
						call_theoretical_price, put_theoretical_vol, put_theoretical_price, total_ratio)

	def create_option_record(self, description, latest_price, call_price, put_price, \
		call_theoretical_vol, call_theoretical_price, put_theoretical_vol, put_theoretical_price, total_ratio):
		"""Opens the document and werites info"""
		f = open(self.document_name, "a+")
		f.write("{} | {} | {} | {} | {} | {} | {} | {} | {} | {}\r".format(self.company.symbol, description, latest_price, \
			call_price, put_price, call_theoretical_vol, call_theoretical_price, put_theoretical_vol, put_theoretical_price, total_ratio))
		print("#####################################################Created record for {}".format(self.company.symbol, description))
		f.close()

class UnderpricedCallOptionsStrategy():
	def __init__(self, company, market, threshold):
		self.company = company
		self.options_dict = self.company.get_options_dict()
		self.call_options = self.options_dict[0]
		#self.put_options = self.options_dict[1]
		self.market = market
		self.threshold = threshold
		self.document_name = str(self.market) + '_underpriced_call_options.txt'

	def execute_strategy(self):
		for expiry in self.call_options:
			for strike in self.call_options[expiry]:
				call_ratio = float(self.call_options[expiry][strike][0]['ask']) / (float(self.call_options[expiry][strike][0]['ask']) + float(strike))
				#put_ratio = float(self.put_options[expiry][strike][0]['ask']) / (float(self.put_options[expiry][strike][0]['ask']) + float(strike))
				total_ratio = call_ratio# + put_ratio
				if 0 < total_ratio <= self.threshold:
					description = self.call_options[expiry][strike][0]['description']
					latest_price = self.company.get_latest_price()
					call_price = float(self.call_options[expiry][strike][0]['ask'])
					#put_price = float(self.put_options[expiry][strike][0]['ask'])
					call_theoretical_price = float(self.call_options[expiry][strike][0]['theoreticalOptionValue'])
					call_theoretical_vol = float(self.call_options[expiry][strike][0]['theoreticalVolatility'])
					#put_theoretical_price = float(self.put_options[expiry][strike][0]['theoreticalOptionValue'])
					#put_theoretical_vol = float(self.put_options[expiry][strike][0]['theoreticalVolatility'])
					self.create_option_record(description, latest_price, call_price, 'put_price', call_theoretical_vol, \
						call_theoretical_price, 'put_theoretical_vol', 'put_theoretical_price', total_ratio)

	def create_option_record(self, description, latest_price, call_price, put_price, \
		call_theoretical_vol, call_theoretical_price, put_theoretical_vol, put_theoretical_price, total_ratio):
		"""Opens the document and werites info"""
		f = open(self.document_name, "a+")
		f.write("{} | {} | {} | {} | {} | {} | {} | {} | {} | {}\r".format(self.company.symbol, description, latest_price, \
			call_price, put_price, call_theoretical_vol, call_theoretical_price, put_theoretical_vol, put_theoretical_price, total_ratio))
		print("#####################################################Created record for {}".format(self.company.symbol, description))
		f.close()

class UnderpricedPutOptionsStrategy():
	def __init__(self, company, market, threshold):
		self.company = company
		self.options_dict = self.company.get_options_dict()
		#self.call_options = self.options_dict[0]
		self.put_options = self.options_dict[1]
		self.market = market
		self.threshold = threshold
		self.document_name = str(self.market) + '_underpriced_put_options.txt'

	def execute_strategy(self):
		for expiry in self.put_options:
			for strike in self.put_options[expiry]:
				#call_ratio = float(self.call_options[expiry][strike][0]['ask']) / (float(self.call_options[expiry][strike][0]['ask']) + float(strike))
				put_ratio = float(self.put_options[expiry][strike][0]['ask']) / (float(self.put_options[expiry][strike][0]['ask']) + float(strike))
				total_ratio = put_ratio
				if 0 < total_ratio <= self.threshold:
					description = self.put_options[expiry][strike][0]['description']
					latest_price = self.company.get_latest_price()
					#call_price = float(self.call_options[expiry][strike][0]['ask'])
					put_price = float(self.put_options[expiry][strike][0]['ask'])
					#call_theoretical_price = float(self.call_options[expiry][strike][0]['theoreticalOptionValue'])
					#call_theoretical_vol = float(self.call_options[expiry][strike][0]['theoreticalVolatility'])
					put_theoretical_price = float(self.put_options[expiry][strike][0]['theoreticalOptionValue'])
					put_theoretical_vol = float(self.put_options[expiry][strike][0]['theoreticalVolatility'])
					self.create_option_record(description, latest_price, 'call_price', put_price, 'call_theoretical_vol', \
						'call_theoretical_price', put_theoretical_vol, put_theoretical_price, total_ratio)

	def create_option_record(self, description, latest_price, call_price, put_price, \
		call_theoretical_vol, call_theoretical_price, put_theoretical_vol, put_theoretical_price, total_ratio):
		"""Opens the document and werites info"""
		f = open(self.document_name, "a+")
		f.write("{} | {} | {} | {} | {} | {} | {} | {} | {} | {}\r".format(self.company.symbol, description, latest_price, \
			call_price, put_price, call_theoretical_vol, call_theoretical_price, put_theoretical_vol, put_theoretical_price, total_ratio))
		print("#####################################################Created record for {}".format(self.company.symbol, description))
		f.close()