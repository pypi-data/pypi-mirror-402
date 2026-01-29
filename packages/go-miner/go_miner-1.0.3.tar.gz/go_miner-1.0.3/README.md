# Go Package Miner

A Python tool to mine and extract complete package lists from the Go modules registry.

## Installation

```bash
pip install go-miner
```

## Usage

```bash
go-miner
```

Or use as a Python module:

```python
from go_miner import mine_go
mine_go()
```

## Data Source

- Go Module Index: https://index.golang.org/index
- Go Proxy API: https://proxy.golang.org

## Output

**Location:** `../Package-List/Go.csv`

**Format:** CSV file with columns:

- ID (sequential number)
- Platform (always "Go")
- Name (full module path)
- Homepage URL (empty)
- Repository URL
