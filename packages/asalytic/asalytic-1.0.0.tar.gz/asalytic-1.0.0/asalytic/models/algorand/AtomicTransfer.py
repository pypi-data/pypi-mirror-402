from typing import List, Optional

from pydantic import BaseModel

from asalytic.models.algorand import Transaction, TransactionType


class AtomicTransfer(BaseModel):
    transactions: List[Transaction]

    @property
    def payment_transactions(self) -> List[Transaction]:
        return list(filter(lambda txn: txn.transaction_type == TransactionType.payment, self.all_transactions))

    @property
    def asset_transfer_transactions(self) -> List[Transaction]:
        return list(filter(lambda txn: txn.transaction_type == TransactionType.asset_transfer, self.all_transactions))

    @property
    def group_id(self):
        return self.transactions[0].group

    @property
    def unique_asa_id_transferred(self) -> List[int]:
        unique_asas_transferred = set()

        for transaction in self.transactions:
            for txn in transaction.extracted_transactions:
                if txn.transaction_type == TransactionType.asset_transfer \
                        and txn.asset_transfer_transaction.asset_transferred:
                    unique_asas_transferred.add(txn.asset_transfer_transaction.asset_id)

        return list(unique_asas_transferred)

    @property
    def number_of_unique_asa_transferred(self) -> int:
        return len(self.unique_asa_id_transferred)

    @property
    def asa_id(self) -> Optional[int]:
        if self.number_of_unique_asa_transferred != 1:
            return None

        return self.unique_asa_id_transferred[0]

    @property
    def block(self) -> int:
        return self.transactions[0].confirmed_round

    @property
    def block_time(self) -> int:
        return self.transactions[0].round_time

    @property
    def all_transactions(self) -> List[Transaction]:
        txns: List[Transaction] = []
        for t in self.transactions:
            txns.extend(t.extracted_transactions)
        return txns

    @property
    def highest_payment_amount(self) -> Optional[int]:
        maxi = -1
        for txn in self.all_transactions:
            if txn.transaction_type == TransactionType.payment:
                maxi = max(maxi, txn.payment_transaction.amount)
                maxi = max(maxi, txn.payment_transaction.close_amount)

        return None if maxi == -1 else maxi

    def valid_transaction_types(self, transaction_types: List[TransactionType]) -> bool:
        if len(transaction_types) != len(self.transactions):
            raise NotImplementedError(
                f"Invalid transaction numbers. {len(self.transactions)} tnxs vs {len(transaction_types)} txn types")

        for i in range(len(self.transactions)):
            if self.transactions[i].transaction_type.value != transaction_types[i].value:
                return False

        return True

    def valid_inner_transaction_types(self, transaction_types: List[TransactionType]) -> bool:

        extracted_transactions = self.all_transactions

        if len(transaction_types) != len(extracted_transactions):
            raise NotImplementedError(
                f"Invalid transaction numbers. {len(self.transactions)} txns vs {len(transaction_types)} txn types")

        for i in range(len(extracted_transactions)):
            if extracted_transactions[i].transaction_type.value != transaction_types[i].value:
                return False

        return True
