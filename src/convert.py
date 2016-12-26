import re, urllib2, json, datetime
from dateutil import tz, parser, relativedelta
import xml.etree.ElementTree as xml


RATES_URL = 'http://www.cbr.ru/scripts/XML_daily_eng.asp'
RATES_PATH = 'rates.xml'
LOCAL_CURRENCY = {'CharCode': 'RUB', 'Nominal': '1', 'Value': '1'}


def get_rates():
    try:
        rates = xml.parse(RATES_PATH)
        rel = parser.parse(rates.getroot().attrib['Date']).replace(tzinfo=tz.gettz('Europe/Moscow'))
        now = datetime.datetime.today().replace(tzinfo=tz.tzlocal())
        day = now.isoweekday()
        if day == 1:
            now = now.replace(day=now.day-2)
        elif day == 7:
            now = now.replace(day=now.day-1)
        if relativedelta.relativedelta(now, rel).days >= 1:
            raise Exception('Exchange rates are out of date')
    except:
        rates = xml.parse(urllib2.urlopen(RATES_URL))
        rates.write(RATES_PATH)
    return rates

def get_currency(code):
    rate = get_rates().find('./Valute[CharCode="{:s}"]'.format(code))
    if rate is not None:
        return dict([(item.tag, item.text) for item in list(rate)])

def process_args(args):
    result = {'src':None, 'dst':None, 'amount':None}
    for arg in args:
        if re.match(r'^[0-9]+([.,][0-9]+)*$', arg):
            result['amount'] = float(arg.replace(',', '.'))
        else:
            currency = get_currency(arg) if arg != LOCAL_CURRENCY['CharCode'] else LOCAL_CURRENCY
            key = 'dst' if result['src'] else 'src'
            result[key] = currency
    return result

def error():
    return json.dumps({'items': [{
        'title': 'Please, enter the valid query',
        'valid': False
    }]})

def output(src, dst, amount, result):
    title = '{:n} {:s} = {:n} {:s}'.format(round(amount, 2), src, round(result, 2), dst)
    return json.dumps({'items': [{
        'title': title,
        'subtitle': 'Action this item to copy result to the clipboard',
        'arg': '{:n}'.format(round(result, 2)),
        'text': {'copy': title, 'largetype': title}
    }]})


def convert(query):
    src = LOCAL_CURRENCY['CharCode']
    dst = LOCAL_CURRENCY['CharCode']
    amount = 1
    result = 1
    
    args = process_args(query.upper().split(' ')[:3])
    
    if args['src']:
        src = args['src']['CharCode']
        amount = int(args['src']['Nominal'])
        result = float(args['src']['Value'].replace(',', '.'))
    if args['amount']:
        result = result / amount * args['amount']
        amount = args['amount']
    if args['dst']:
        dst = args['dst']['CharCode']
        result = result / float(args['dst']['Value'].replace(',', '.')) * int(args['src']['Nominal'])
    
    if src == dst:
        return error()
    
    return output(src, dst, amount, result)
