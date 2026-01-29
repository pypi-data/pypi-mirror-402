from asalytic.models.algorand import AtomicTransfer

from asalytic.models.atomic_transfer import RandGallerySale
from asalytic.models.atomic_transfer import AB2GallerySale
from asalytic.models.atomic_transfer import AlgoDropSale
from asalytic.models.atomic_transfer import AlgoGemsSale
from asalytic.models.atomic_transfer import ALGOxNFTSale
from asalytic.models.atomic_transfer import AtomicSwapSale
from asalytic.models.atomic_transfer import DartroomSale
from asalytic.models.atomic_transfer import FlemishGiantsSale
from asalytic.models.atomic_transfer import OctorandSale
from asalytic.models.atomic_transfer import PixTrateSale
from asalytic.models.atomic_transfer import NFDSale
from asalytic.models.atomic_transfer import MNGOSale
from asalytic.models.atomic_transfer import Atomixwap
from asalytic.models.atomic_transfer import AsalyticSale
from asalytic.models.atomic_transfer import ShuflSale
from asalytic.models.atomic_transfer import UnknownPlatformSale
from asalytic.models.atomic_transfer import EXASale
from asalytic.models.atomic_transfer import FracctalLabsSale
from asalytic.models.atomic_transfer import AlgorillasExchangeSale
from asalytic.models.atomic_transfer import CGRSale

from asalytic.models.ASASale import ASASale
from typing import List

__all__ = ["ASASaleParser"]


class ASASaleParser:

    @staticmethod
    def parse_atomic_transfers(atomic_transfers: List[AtomicTransfer]) -> (List[ASASale], List[AtomicTransfer]):
        sales: List[ASASale] = []
        unknown: List[AtomicTransfer] = []

        for atomic_transfer in atomic_transfers:
            try:
                sale = RandGallerySale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = AB2GallerySale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = AlgoDropSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = AlgoGemsSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = ALGOxNFTSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = AtomicSwapSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = DartroomSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = FlemishGiantsSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = OctorandSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = PixTrateSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = NFDSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = MNGOSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = AsalyticSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = Atomixwap.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = ShuflSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = UnknownPlatformSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = EXASale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = FracctalLabsSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = AlgorillasExchangeSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            try:
                sale = CGRSale.init_from_atomic_transfer(atomic_transfer=atomic_transfer)
                sales.append(sale)
                continue
            except:
                pass

            unknown.append(atomic_transfer)

        sales = [ASASale(**sale.dict()) for sale in sales]

        return sales, unknown
