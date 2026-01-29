# Ruby Gems Miner

A Python tool to mine and extract complete package lists from the RubyGems registry.

## Installation

```bash
pip install ruby-miner
```

## Usage

```bash
ruby-miner
```

Or use as a Python module:

```python
from ruby_miner import mine_ruby
mine_ruby()
```

## Data Source

- Gem Names: http://rubygems.org/names
- Gem Details: https://rubygems.org/api/v1/gems/{name}.json

## Output

**Location:** `../Package-List/Ruby.csv`

**Format:** CSV file with columns:

- ID (sequential number)
- Platform (always "RubyGems")
- Name (gem name)
- Homepage URL
- Repository URL
