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

The output file will be stored in a folder named "Package-List" _in your current working directory_.

If you are using a virtual environment, "Package-List" will be located where `venv` is installed.

**Format:** CSV file with columns:

- ID (sequential number)
- Platform (always "RubyGems")
- Name (gem name)
- Homepage URL
- Repository URL
