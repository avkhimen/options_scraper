import time
from utility_classes import Company, Symbols, UnderpricedOptionsStrategy
from support_functions import get_input_args

def main():
	market = get_input_args().market
	threshold = get_input_args().discount_threshold
	strategy_to_run = get_input_args().strategy

	#symbols = ['MSFT', 'AMZN', 'NFLX', 'GOOG']
	symbols = Symbols(market).get_all_symbols()
	print('{} size is {} companies long'.format(market, len(symbols)))

	for symbol in symbols:
		print('------------------------------------------------------' \
			'---Processing {} number {} from {}'.format(symbol, symbols.index(symbol), len(symbols)))
		company = Company(symbol)
		try:
			if strategy_to_run == 'options':
				sleep_time = 1
				UnderpricedOptionsStrategy(company, market).test()
				time.sleep(sleep_time)
		except Exception as e:
			print(e)
		else:
			True

if __name__ == '__main__':
	main()
