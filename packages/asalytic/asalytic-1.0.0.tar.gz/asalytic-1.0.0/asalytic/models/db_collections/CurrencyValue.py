from pydantic import BaseModel
from .PriceData import PriceData
from asalytic.models import ASASale


class CurrencyValue(BaseModel):
    algo: float = 0
    eth: float = 0
    btc: float = 0
    usd: float = 0

    def update_data(self, algo: float, eth: float, btc: float, usd: float):
        self.algo += algo
        self.eth += eth
        self.btc += btc
        self.usd += usd

    def update_with_price_data(self, algo: float, price_data: PriceData):
        self.algo += algo
        self.eth += algo * price_data.eth
        self.btc += algo * price_data.btc
        self.usd += algo * price_data.usd

    def update_with_currency_value(self, currency_value):
        self.algo += currency_value.algo
        self.eth += currency_value.eth
        self.btc += currency_value.btc
        self.usd += currency_value.usd

    def update_with_sale(self, sale: ASASale):
        sale_algo = sale.price / 1000000

        self.algo += sale_algo
        self.eth += sale_algo * sale.eth_price
        self.btc += sale_algo * sale.btc_price
        self.usd += sale_algo * sale.usd_price
