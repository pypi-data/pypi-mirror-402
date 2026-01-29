from pydantic import BaseModel
from typing import Optional


# https://developer.algorand.org/docs/rest-apis/indexer/#transactionpayment
class PaymentTransaction(BaseModel):
    amount: int
    close_amount: Optional[int]

    close_reminder_to: Optional[str]
    receiver: str

    @staticmethod
    def init_from_payment(payment: dict):
        try:
            return PaymentTransaction(amount=payment.get('amount', None),
                                      close_amount=payment.get('close-amount', None),
                                      close_reminder_to=payment.get('close-remainder-to', None),
                                      receiver=payment.get('receiver', None))
        except:
            return None
