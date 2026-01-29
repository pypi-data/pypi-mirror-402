from typing import Optional
import requests

from asalytic.models import PriceConversion


def get_pricing_data() -> Optional[PriceConversion]:
    try:
        request = requests.get('https://min-api.cryptocompare.com/data/price?fsym=ALGO&tsyms=BTC,USD,ETH')
        data = request.json()

        return PriceConversion(usd=data['USD'],
                               btc=data['BTC'],
                               eth=data['ETH'])
    except:
        print('Error receiving pricing data.')
        return None
