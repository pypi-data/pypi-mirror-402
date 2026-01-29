# PHP/Packagist Miner

A Python tool to mine and extract complete package lists from the Packagist (Composer) registry.

## Installation

```bash
pip install php-miner
```

## Usage

```bash
php-miner
```

Or use as a Python module:

```python
from php_miner import mine_php
mine_php()
```

## Data Source

- Packagist Package List: https://packagist.org/packages/list.json
- Package Details: https://packagist.org/packages/{vendor}/{package}.json

## Output

**Location:** `../Package-List/PHP.csv`

**Format:** CSV file with columns:

- ID (sequential number)
- Platform (always "Packagist")
- Name (vendor/package format)
- Homepage URL
- Repository URL
