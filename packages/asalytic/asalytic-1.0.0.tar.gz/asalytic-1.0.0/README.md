# Asalytic

A Python library for tracking NFT sales and listings on the Algorand blockchain.

## Features

- Track ASA (Algorand Standard Asset) sales across multiple NFT marketplaces
- Monitor active NFT listings
- Support for 16+ NFT platforms including Rand Gallery, Shufl, EXA, ALGO x NFT, and more
- Parse multiple metadata standards (ARC3, ARC19, ARC69)

## Installation

### From PyPI (Recommended)

```bash
pip install asalytic
```

### From Source

#### Quick Setup

**Windows:**
```batch
setup.bat
```

**Unix/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

#### Manual Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Unix/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Track Sales

```python
from asalytic.indexers.indexer import AsalyticIndexerClient
from asalytic.parsers.asa_sale_parser import ASASaleParser

indexer = AsalyticIndexerClient(
    indexer_address="https://mainnet-idx.4160.nodely.io",
    indexer_token="YOUR_TOKEN"
)

block = indexer.block_info(block_number)
atomic_transfers = indexer.get_atomic_transfers_from_block(block)

for at in atomic_transfers:
    sale = ASASaleParser.parse(at)
    if sale:
        print(f"asa_id={sale.asa_id} price={sale.price_in_algo} ALGO")
```

### Track Listings

```python
from asalytic.indexers.indexer import AsalyticIndexerClient
from asalytic.parsers.app_listings_at_parser import AppListingsATParser

indexer = AsalyticIndexerClient(
    indexer_address="https://mainnet-idx.4160.nodely.io",
    indexer_token="YOUR_TOKEN"
)

block = indexer.block_info(block_number)
atomic_transfers = indexer.get_atomic_transfers_from_block(block)

for at in atomic_transfers:
    listing = AppListingsATParser.parse(at)
    if listing:
        print(f"asa_id={listing.asa_id} price={listing.price_in_algo} ALGO")
```

## Demo Scripts

Run the demo scripts to see the library in action:

```bash
# Track sales from a specific block
python demo_track_sales.py

# Track listings from a specific block
python demo_track_listings.py
```

## License

MIT License - see LICENSE file for details.
