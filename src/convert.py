import sys
import re
from workflow import Workflow, web, ICON_WARNING


CBR_RATES_URL = 'http://www.cbr.ru/scripts/XML_daily_eng.asp'
DEF_VAL = {'CharCode': 'RUB', 'Nominal': '1', 'Value': '1'}


def get_rates():
	r = web.get(CBR_RATES_URL)
	r.raise_for_status()
	return r.xml()

def get_currency(char_code):
	rates = wf.cached_data('rates', get_rates, 3600)
	try:
		result = next(item for item in rates['Valute'] if item['CharCode'] == char_code)
	except StopIteration:
		result = None
	finally:
		return result

def parse_args(args):
	result = {'from':None, 'to':None, 'qty':None}
	for arg in args[:3]:
		if re.match('[0-9]+([.,][0-9]+)*', arg):
			result['qty'] = float(arg.replace(',', '.'))
		else:
			currency = get_currency(arg) if arg != DEF_VAL['CharCode'] else DEF_VAL
			key = 'to' if result['from'] else 'from'
			result[key] = currency
	return result

def show_result(wf, qty, src, res, dst):
	title_fmt = ('{:.2f}' if type(qty) == float else '{:d}') + ' {:s} = {:.2f} {:s}'
	title = title_fmt.format(qty, src, res, dst)
	copytext = '{:.2f}'.format(res)
	wf.add_item(title, 'Action this item to copy the result to clipboard', largetext=title, arg=copytext, valid=True)
	wf.send_feedback()

def show_error(wf):
	wf.add_item('Please, enter valid query', icon=ICON_WARNING)
	wf.send_feedback()


def main(wf):
	options = parse_args(wf.args[0].upper().split(' '))
	src = dst = DEF_VAL['CharCode']
	qty = res = 1
	if options['from']:
		src = options['from']['CharCode']
		qty = int(options['from']['Nominal'])
		res = float(options['from']['Value'].replace(',', '.'))
	if options['qty']:
		res = res / qty * options['qty']
		qty = options['qty']
	if options['to']:
		dst = options['to']['CharCode']
		res = res / float(options['to']['Value'].replace(',', '.')) * int(options['from']['Nominal'])
	if src != dst:
		show_result(wf, qty, src, res, dst)
	else:
		show_error(wf)


if __name__ == '__main__':
	wf = Workflow(capture_args=False)
	sys.exit(wf.run(main))