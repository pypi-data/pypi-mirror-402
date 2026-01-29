from pydantic import BaseModel
from typing import Optional, List, Any
from enum import Enum
import json
import base64

from asalytic.models.algorand.AssetTransferTransaction import AssetTransferTransaction
from asalytic.models.algorand.AssetConfigTransaction import AssetConfigTransaction
from asalytic.models.algorand.PaymentTransaction import PaymentTransaction
from asalytic.models.algorand.ApplicationTransaction import ApplicationTransaction, OnCompletion


class TransactionType(str, Enum):
    payment = 'pay'
    asset_transfer = 'axfer'
    application_call = 'appl'
    asset_config = 'acfg'
    key_registration = 'keyreg'
    asset_freeze = 'afrz'


# https://developer.algorand.org/docs/rest-apis/indexer/#transaction
class Transaction(BaseModel):
    asset_transfer_transaction: Optional[AssetTransferTransaction]
    asset_config_transaction: Optional[AssetConfigTransaction]
    payment_transaction: Optional[PaymentTransaction]
    application_transaction: Optional[ApplicationTransaction]

    # TODO:
    # Some types are missing: freeze,

    close_rewards: Optional[int]
    close_amount: Optional[int]

    round_time: Optional[int]
    confirmed_round: Optional[int]

    created_application_index: Optional[int]
    created_asset_index: Optional[int]

    fee: int

    group: Optional[str]
    txn_id: Optional[str]

    # (pay, keyreg, acfg, axfer, afrz, appl)
    txn_type: str

    note: Optional[str]

    receiver_rewards: Optional[int]

    sender: str
    sender_rewards: Optional[int]

    inner_txns: List[Any] = []

    @property
    def payment_amount(self) -> Optional[int]:
        if self.txn_type != 'pay':
            return None

        return self.payment_transaction.amount

    @property
    def payment_close_amount(self) -> Optional[int]:
        if self.txn_type != 'pay':
            return None

        return self.payment_transaction.close_amount

    @property
    def is_asset_create(self) -> bool:
        return self.created_asset_index is not None

    @property
    def is_asset_update(self) -> bool:
        if self.asset_config_transaction is not None:
            return self.asset_config_transaction.is_asset_update

        return False

    @property
    def is_asset_delete(self) -> bool:
        if self.asset_config_transaction is not None:
            return self.asset_config_transaction.is_asset_delete

        return False

    @property
    def json_note(self) -> Optional[dict]:
        try:
            return json.loads(base64.b64decode(self.note).decode('utf-8'))
        except:
            pass

        return None

    @property
    def asset_id(self) -> Optional[int]:
        """
        ID of the asset in case of a asset config transaction.
        :return:
        """
        if self.created_asset_index is not None:
            return self.created_asset_index

        try:
            asa_id = self.asset_config_transaction.asset_id
            if asa_id != 0:
                return asa_id
        except:
            pass

        return None

    @property
    def transaction_type(self) -> TransactionType:
        if self.txn_type == 'pay':
            return TransactionType.payment
        elif self.txn_type == 'keyreg':
            return TransactionType.key_registration
        elif self.txn_type == 'acfg':
            return TransactionType.asset_config
        elif self.txn_type == 'axfer':
            return TransactionType.asset_transfer
        elif self.txn_type == 'afrz':
            return TransactionType.asset_freeze
        elif self.txn_type == 'appl':
            return TransactionType.application_call

        raise NotImplementedError(f'Invalid transaction type: {self.txn_type}')

    @property
    def is_application_create(self):
        if self.created_application_index is not None and self.created_application_index != 0:
            return True

        return False

    @property
    def is_application_delete(self):

        if self.application_transaction and self.application_transaction.on_completion == OnCompletion.delete:
            return True

        return False

    @property
    def extracted_transactions(self):
        return extract_inner_transactions(transaction=self)

    @staticmethod
    def init_from_transaction(transaction: dict):
        try:
            asset_transfer = transaction.get('asset-transfer-transaction', None)
            asset_config = transaction.get('asset-config-transaction', None)
            payment = transaction.get('payment-transaction', None)
            application = transaction.get('application-transaction', None)

            inner_txns = transaction.get('inner-txns', [])
            inner_transactions = []

            if len(inner_txns) > 0:
                for txn in inner_txns:
                    inner_transactions.append(Transaction.init_from_transaction(txn))

            return Transaction(
                asset_transfer_transaction=AssetTransferTransaction.init_from_asset_transfer(
                    asset_transfer) if asset_transfer is not None else None,
                asset_config_transaction=AssetConfigTransaction.init_from_asset_config(
                    asset_config) if asset_config is not None else None,
                payment_transaction=PaymentTransaction.init_from_payment(payment) if payment is not None else None,
                application_transaction=ApplicationTransaction.init_from_application_transaction(
                    app_txn=application) if application is not None else None,
                close_rewards=transaction.get('close-rewards', None),
                close_amount=transaction.get('closing-amount', None),
                round_time=transaction.get('round-time', None),
                confirmed_round=transaction.get('confirmed-round', None),
                created_application_index=transaction.get('created-application-index', None),
                created_asset_index=transaction.get('created-asset-index', None),
                fee=transaction.get('fee', None),
                group=transaction.get('group', None),
                txn_id=transaction.get('id', None),
                txn_type=transaction.get('tx-type', None),
                note=transaction.get('note', None),
                receiver_rewards=transaction.get('receiver-rewards', None),
                sender=transaction.get('sender', None),
                sender_rewards=transaction.get('sender-rewards', None),
                inner_txns=inner_transactions
            )

        except:
            return None


def extract_inner_transactions(transaction: Transaction) -> List[Transaction]:
    extracted_transactions = [transaction]

    for t in transaction.inner_txns:
        unpacked_transactions = extract_inner_transactions(transaction=t)
        extracted_transactions.extend(unpacked_transactions)

    return extracted_transactions
