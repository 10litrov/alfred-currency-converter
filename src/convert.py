#!/usr/bin/env python3

import datetime
import decimal
import json
import re
import urllib.request
import xml.etree.ElementTree as xml


MOSCOW_TZ = datetime.timezone(datetime.timedelta(hours=3), name='Europe/Moscow')
RATES_URL = 'http://www.cbr.ru/scripts/XML_daily_eng.asp'
RATES_PATH = 'rates.xml'
LOCAL_CURRENCY = {'CharCode': 'RUB', 'Nominal': '1', 'Value': '1'}


def get_rates():
    try:
        rates = xml.parse(RATES_PATH)
        rel = parser.parse(rates.getroot().attrib['Date'], dayfirst=True).replace(
            tzinfo=MOSCOW_TZ
        )
        now = datetime.datetime.today(tzinfo=MOSCOW_TZ)
        if (now - rel).days >= 1:
            raise Exception('Exchange rates are out of date')
    except:
        rates = xml.parse(urllib.request.urlopen(RATES_URL))
        rates.write(RATES_PATH)
    return rates


def get_currency(code):
    rate = get_rates().find('./Valute[CharCode="{:s}"]'.format(code))
    if rate is not None:
        return dict([(item.tag, item.text) for item in list(rate)])


def process_args(args):
    result = {'src': None, 'dst': None, 'amount': None}
    for arg in args:
        if re.match(r'^[0-9]+([.,][0-9]+)*$', arg):
            result['amount'] = float(arg.replace(',', '.'))
        else:
            currency = (
                get_currency(arg)
                if arg != LOCAL_CURRENCY['CharCode']
                else LOCAL_CURRENCY
            )
            key = 'dst' if result['src'] else 'src'
            result[key] = currency
    return result


def error():
    return json.dumps(
        {'items': [{'title': 'Please, enter the valid query', 'valid': False}]}
    )


def output(src, dst, amount, result):
    title = '{:n} {:s} = {:n} {:s}'.format(round(amount, 2), src, round(result, 2), dst)
    return json.dumps(
        {
            'items': [
                {
                    'title': title,
                    'subtitle': 'Action this item to copy result to the clipboard',
                    'arg': '{:n}'.format(round(result, 2)),
                    'text': {'copy': title, 'largetype': title},
                }
            ]
        }
    )


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
        result = (
            result
            / float(args['dst']['Value'].replace(',', '.'))
            * int(args['src']['Nominal'])
        )

    if src == dst:
        return error()

    return output(src, dst, amount, result)


def parse_number(value: str) -> decimal.Decimal:
    """Provides real number parser for argparse."""
    try:
        number = decimal.Decimal(value.replace(',', '.'))
    except decimal.InvalidOperation:
        raise argparse.ArgumentTypeError('should conform 3.14 or 3,14 format')
    return number


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Converts an amount from one currency to another.'
    )
    parser.add_argument(
        'amount',
        type=parse_number,
        help='amount to convert',
    )
    parser.add_argument(
        'from',
        help='source currency',
    )
    parser.add_argument(
        'to',
        nargs='?',
        default='RUB',
        help='target currency (default is %(default)s)',
    )

    # Alfred encloses the whole query in quotes so wee need to unwrap it
    if len(sys.argv) == 2:
        input_args = sys.argv[1].split(' ')
    else:
        input_args = sys.argv[1:]

    args = parser.parse_args(args=input_args)

    print(convert('{0.amount} {0.from} {0.to}'.format(args)))
