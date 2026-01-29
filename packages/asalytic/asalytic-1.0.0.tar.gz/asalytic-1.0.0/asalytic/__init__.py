"""
Asalytic - A Python library for tracking NFT sales and listings on the Algorand blockchain.
"""

__version__ = "1.0.0"

# Core indexer
from asalytic.indexers.indexer import AsalyticIndexerClient

# Parsers
from asalytic.parsers.sale import ASASaleParser
from asalytic.parsers.listing.AppListingsATParser import AppListingsATParser
from asalytic.parsers.listing.ApplicationsParser import ApplicationParser
from asalytic.parsers.listing.SignatureListingsATParser import SignatureListingsATParser
from asalytic.parsers.listing.SignatureDelistingsATParser import SignatureDelistingsATParser
from asalytic.parsers.listing.AppDelistingsATParser import AppDelistingATParser

# Models
from asalytic.models import (
    ASA,
    ASACollection,
    ASAListing,
    ASAOwner,
    ASASale,
    ASAPriceEstimate,
    ASARarity,
    WalletConfiguration,
    Listing,
    Teal,
)

# Algorand types
from asalytic.models.algorand import (
    Transaction,
    TransactionType,
    AtomicTransfer,
    Application,
    PaymentTransaction,
    AssetTransferTransaction,
    AssetConfigTransaction,
)

__all__ = [
    "__version__",
    # Indexer
    "AsalyticIndexerClient",
    # Parsers
    "ASASaleParser",
    "AppListingsATParser",
    "ApplicationParser",
    "SignatureListingsATParser",
    "SignatureDelistingsATParser",
    "AppDelistingATParser",
    # Models
    "ASA",
    "ASACollection",
    "ASAListing",
    "ASAOwner",
    "ASASale",
    "ASAPriceEstimate",
    "ASARarity",
    "WalletConfiguration",
    "Listing",
    "Teal",
    # Algorand
    "Transaction",
    "TransactionType",
    "AtomicTransfer",
    "Application",
    "PaymentTransaction",
    "AssetTransferTransaction",
    "AssetConfigTransaction",
]
