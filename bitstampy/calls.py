import datetime
import hashlib
import hmac
import requests
import time
from decimal import Decimal

_API_URL = 'https://www.bitstamp.net/api/v2/'


def dt(timestamp):
    """
    Convert a unix timestamp or ISO 8601 date string to a datetime object.
    """
    if not timestamp:
        return None
    try:
        timestamp = int(timestamp)
    except ValueError:
        try:
            timestamp = time.mktime(time.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f'))
        except ValueError:
            timestamp = time.mktime(time.strptime(timestamp, '%Y-%m-%d %H:%M:%S'))
    return datetime.datetime.fromtimestamp(timestamp)


class APIError(Exception):
    pass


class APICall(object):
    url = None
    method = 'get'

    def _process_response(self, response):
        """
        Process the response dictionary.

        If the dictionary is just being altered, then no return is necessary.
        Alternatively, a totally different response can be returned.
        """
        return

    def call(self, **params):
        # Form request
        r = None
        url = _API_URL + self.url
        if self.method == 'get':
            r = requests.get(url, params=params)
        elif self.method == 'post':
            r = requests.post(url, data=params)
        response = r.json()
        # API error?
        if isinstance(response, dict) and 'error' in response:
            raise APIError(response['error'])
        # Process fields
        new_response = self._process_response(response)
        if new_response is not None:
            response = new_response
        return response


def _get_nonce():
    return str(int(time.time() * 1e6))


class APIPrivateCall(APICall):
    method = 'post'

    def __init__(self, client_id, api_key, api_secret, *args, **kwargs):
        super(APIPrivateCall, self).__init__(*args, **kwargs)
        self.client_id = client_id
        self.api_key = api_key
        self.api_secret = api_secret

    def call(self, **params):
        nonce = _get_nonce()
        message = nonce + self.client_id + self.api_key
        signature = hmac.new(
            self.api_secret.encode('utf-8'), msg=message.encode('utf-8'), digestmod=hashlib.sha256)
        signature = signature.hexdigest().upper()
        params.update({
            'key': self.api_key, 'signature': signature, 'nonce': nonce
        })
        return super(APIPrivateCall, self).call(**params)


# Specific call classes
class APIAccountBalanceCall(APIPrivateCall):
    url = 'account_balances/'

    def _process_response(self, response):
        for pair in response:
            pair['total'] = Decimal(pair['total'])
            pair['available'] = Decimal(pair['available'])
            pair['reserved'] = Decimal(pair['reserved'])


class APIBitcoinDepositAddressCall(APIPrivateCall):
    url = 'btc_address/'


class APIBitcoinWithdrawalCall(APIPrivateCall):
    url = 'btc_withdrawal/'


class APIBuyLimitOrderCall(APIPrivateCall):
    url = 'buy/btceur/'

    def _process_response(self, response):
        response['datetime'] = dt(response['datetime'])
        response['price'] = Decimal(response['price'])
        response['amount'] = Decimal(response['amount'])


class APICancelOrderCall(APIPrivateCall):
    url = 'cancel_order/'


class APIEURUSDConversionRateCall(APICall):
    url = 'eur_usd/'

    def _process_response(self, response):
        response['buy'] = Decimal(response['buy'])
        response['sell'] = Decimal(response['sell'])


class APIOrderBookCall(APICall):
    url = 'order_book/btceur/'

    def _process_response(self, response):
        response['timestamp'] = dt(response['timestamp'])
        response['bids'] = [{
            'price': Decimal(price),
            'amount': Decimal(amount)
        } for (price, amount) in response['bids']]
        response['asks'] = [{
            'price': Decimal(price),
            'amount': Decimal(amount)
        } for (price, amount) in response['asks']]


class APIOpenOrdersCall(APIPrivateCall):
    url = 'open_orders/all/'

    def _process_response(self, response):
        for order in response:
            order['datetime'] = dt(order['datetime'])
            order['price'] = Decimal(order['price'])
            order['amount'] = Decimal(order['amount'])


class APIRippleDepositAddressCall(APIPrivateCall):
    url = 'ripple_address/'


class APIRippleWithdrawalCall(APIPrivateCall):
    url = 'ripple_withdrawal/'


class APISellLimitOrderCall(APIPrivateCall):
    url = 'sell/'

    def _process_response(self, response):
        response['datetime'] = dt(response['datetime'])
        response['price'] = Decimal(response['price'])
        response['amount'] = Decimal(response['amount'])


def process_ticker(ticker):
    ticker['last'] = Decimal(ticker['last'])
    ticker['high'] = Decimal(ticker['high'])
    ticker['low'] = Decimal(ticker['low'])
    ticker['vwap'] = Decimal(ticker['volume'])
    ticker['volume'] = Decimal(ticker['volume'])
    ticker['bid'] = Decimal(ticker['bid'])
    ticker['ask'] = Decimal(ticker['ask'])
    ticker['timestamp'] = dt(ticker['timestamp'])
    ticker['open'] = Decimal(ticker['open'])
    ticker['open_24'] = Decimal(ticker['open_24'])
    percent_change_24 = ticker['percent_change_24']
    if percent_change_24 is not None:
        ticker['percent_change_24'] = Decimal(percent_change_24)


class APITickerAllCall(APICall):
    url = 'ticker/'

    def _process_response(self, response):
        for pair in response:
            process_ticker(pair)


class APITickerCall(APICall):

    def __init__(self, pair):
        self.pair = pair
        self.url = f'ticker/{pair}'

    def _process_response(self, response):
        process_ticker(response)


class APITickerHourCall(APICall):

    def __init__(self, pair):
        self.pair = pair
        self.url = f'ticker_hour/{pair}'

    def _process_response(self, response):
        process_ticker(response)


class APITransactionsCall(APICall):

    def __init__(self, pair):
        self.pair = pair
        self.url = f'transactions/{pair}'

    def _process_response(self, response):
        for tx in response:
            tx['date'] = dt(tx['date'])
            tx['price'] = Decimal(tx['price'])
            tx['amount'] = Decimal(tx['amount'])


class APITradingPairsInfoCall(APICall):
    url = 'trading-pairs-info/'


class APIOhlcCall(APICall):

    def __init__(self, pair):
        self.pair = pair
        self.url = f'ohlc/{pair}'


class APIUnconfirmedBitcoinDepositsCall(APIPrivateCall):
    url = 'btc_unconfirmed/'

    def _process_response(self, response):
        response['amount'] = Decimal(response['amount'])
        response['address'] = Decimal(response['address'])
        response['confirmations'] = int(response['confirmations'])


class APIUserTransactionsCall(APIPrivateCall):
    url = 'user_transactions/'

    def _process_response(self, response):
        for tx in response:
            tx['datetime'] = dt(tx['datetime'])
            tx['usd'] = Decimal(tx['usd'])
            tx['btc'] = Decimal(tx['btc'])
            tx['fee'] = Decimal(tx['fee'])


class APIWithdrawalRequestsCall(APIPrivateCall):
    url = 'withdrawal-requests/'

    def _process_response(self, response):
        for wr in response:
            wr['datetime'] = dt(wr['datetime'])
            wr['amount'] = Decimal(wr['amount'])
