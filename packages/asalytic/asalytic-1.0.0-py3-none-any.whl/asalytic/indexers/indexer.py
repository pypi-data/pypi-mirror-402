import base64
from typing import List, Optional, Tuple
from collections import defaultdict
import json
import requests

from algosdk.v2client import indexer

from asalytic.models.algorand import Transaction, TransactionType, AtomicTransfer, Application
from asalytic.models import ASAOwner, Teal


class AsalyticIndexerClient(indexer.IndexerClient):
    """
    Custom class that wraps the indexer client. It provides additional methods for retrieving the blockchain data
    and converting it Asalytic domain objects.
    """

    def account_balance(self, wallet) -> int:
        account_info = self.account_info(address=wallet)

        return account_info['account']['amount']

    def block_transactions(self, block: int, limit: int = 3000) -> List[Transaction]:
        curr_block = self.health()['round']

        if block > curr_block:
            raise NotImplementedError

        next_token = None
        all_transactions: List[Transaction] = []

        while True:
            if next_token is None:
                round_transactions = self.search_transactions(round_num=block,
                                                              limit=limit)
            else:
                round_transactions = self.search_transactions(round_num=block,
                                                              limit=limit,
                                                              next_page=next_token)

            next_token = round_transactions.get("next-token", -1)

            if next_token == -1:
                break

            if len(round_transactions["transactions"]) == 0:
                break

            for txn in round_transactions["transactions"]:
                transaction = Transaction.init_from_transaction(transaction=txn)
                all_transactions.append(transaction)

        return all_transactions

    def block_extracted_transactions(self, block) -> List[Transaction]:
        transactions = self.block_transactions(block=block)

        extracted_transactions: List[Transaction] = []

        for txn in transactions:
            extracted_transactions.extend(txn.extracted_transactions)

        return extracted_transactions

    def block_atomic_transfers(self, block) -> List[AtomicTransfer]:
        curr_block_transactions = self.block_transactions(block=block)
        atomic_transfers: List[AtomicTransfer] = []

        group_id_to_transactions = defaultdict(list)

        for t in curr_block_transactions:
            if t.group is not None:
                group_id_to_transactions[t.group].append(t)

        for at_transactions in group_id_to_transactions.values():
            atomic_transfers.append(AtomicTransfer(transactions=at_transactions))

        return atomic_transfers

    def block_atomic_transfers_with_txns(self, block) -> Tuple[List[AtomicTransfer], List[Transaction]]:
        curr_block_transactions = self.block_transactions(block=block)
        atomic_transfers: List[AtomicTransfer] = []

        group_id_to_transactions = defaultdict(list)

        for t in curr_block_transactions:
            if t.group is not None:
                group_id_to_transactions[t.group].append(t)

        for at_transactions in group_id_to_transactions.values():
            atomic_transfers.append(AtomicTransfer(transactions=at_transactions))

        extracted_transactions: List[Transaction] = []

        for txn in curr_block_transactions:
            extracted_transactions.extend(txn.extracted_transactions)

        return atomic_transfers, extracted_transactions

    def asset_config_transactions(self, asa_id: int) -> List[Transaction]:

        next_token = None
        asset_config_transactions: List[Transaction] = []

        while True:
            if next_token is None:
                round_transactions = self.search_asset_transactions(asset_id=asa_id,
                                                                    txn_type='acfg')
            else:
                round_transactions = self.search_asset_transactions(asset_id=asa_id,
                                                                    txn_type='acfg',
                                                                    next_page=next_token)

            next_token = round_transactions.get("next-token", -1)

            if next_token == -1:
                break

            if len(round_transactions["transactions"]) == 0:
                break

            for txn in round_transactions["transactions"]:
                transaction = Transaction.init_from_transaction(transaction=txn)
                extracted_transaction = transaction.extracted_transactions

                for unpacked_txn in extracted_transaction:
                    if unpacked_txn.transaction_type == TransactionType.asset_config:
                        if unpacked_txn.asset_id == asa_id:
                            asset_config_transactions.append(unpacked_txn)

        return asset_config_transactions

    def created_asa_ids(self, creator_address: str) -> List[int]:

        next_token = None
        asa_ids: List[int] = []

        while True:
            created_assets_response = self.search_assets(creator=creator_address, next_page=next_token)

            next_token = created_assets_response.get("next-token", -1)

            if next_token == -1:
                break

            if len(created_assets_response["assets"]) == 0:
                break

            for asset in created_assets_response["assets"]:
                if not asset["deleted"]:
                    asa_ids.append(asset["index"])

        return asa_ids

    def retrieve_assets(self, wallet_address) -> List[ASAOwner]:
        next_token = None
        owned_asas: List[ASAOwner] = []

        while True:
            assets = self.lookup_account_assets(address=wallet_address,
                                                next_page=next_token)

            next_token = assets.get('next-token', None)

            for asset_info in assets['assets']:
                asa_balance = asset_info['amount']

                if asa_balance > 0 and not asset_info['deleted']:
                    owned_asas.append(ASAOwner(owner=wallet_address,
                                               asa_id=asset_info['asset-id'],
                                               balance=asa_balance))

            if next_token is None:
                break

        return owned_asas

    def retrieve_owners(self, asa_id: int) -> List[ASAOwner]:
        next_token = None
        owners: List[ASAOwner] = []

        while True:
            asset_response = self.asset_balances(asset_id=asa_id, next_page=next_token)

            next_token = asset_response.get('next-token', None)

            for txn in asset_response['balances']:
                if txn['amount'] >= 1:
                    owners.append(ASAOwner(owner=txn['address'],
                                           asa_id=asa_id,
                                           balance=txn['amount']))

            if next_token is None:
                break

        return owners

    def extract_transactions(self, wallet: str) -> List[Transaction]:
        """
        Extracts all the transactions that were the specified wallet was involved in.
        :param wallet:
        :return:
        """

        next_token = None
        transactions: List[Transaction] = []

        while True:
            if next_token is None:
                round_transactions = self.search_transactions(address=wallet)
            else:
                round_transactions = self.search_transactions(address=wallet,
                                                              next_page=next_token)

            next_token = round_transactions.get("next-token", -1)

            if next_token == -1:
                break

            if len(round_transactions["transactions"]) == 0:
                break

            for t in round_transactions["transactions"]:
                try:
                    # TODO: This is not valid for inner-transactions.
                    txn = Transaction.init_from_transaction(transaction=t)
                    transactions.append(txn)
                except NotImplementedError:
                    continue

        return transactions

    def retrieve_application(self, app_id: int) -> Application:
        app_response = self.search_applications(application_id=app_id)

        return Application.init_from_application(application=app_response['applications'][0])

    def retrieve_teal(self, tx_id: str, node_endpoint: str = 'https://mainnet-api.algonode.cloud/v2') -> Optional[Teal]:
        try:
            transaction_data = self.transaction(txid=tx_id)
            teal_byte_string = transaction_data['transaction']['signature']['logicsig']['logic']
            teal_b64_decoded = base64.b64decode(teal_byte_string)

            response = requests.post(url=f'{node_endpoint}/teal/disassemble',
                                     headers={'Content-Type': 'application/x-binary'},
                                     data=teal_b64_decoded)

            decompiled_teal = response.json()['result']

            return Teal(tx_id=tx_id,
                        address=transaction_data['transaction']['sender'],
                        teal_bytes=teal_byte_string,
                        decompiled_teal=decompiled_teal)
        except:
            return None
