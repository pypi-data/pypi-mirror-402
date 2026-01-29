# SystembolagetAPI

SystembolagetAPI lets you search and filter for products on [Systembolaget](https://www.systembolaget.se/) using their unofficial client api.

## Install

SystembolagetAPI is available on [PyPI](https://pypi.org/project/systembolaget-api/).

```bash
uv add systembolaget-api
pip install systembolaget-api
```

## Usage

```python
from systembolaget_api import (
    FilterOptions,
    SystembolagetAPI,
    SystembolagetClient,
)

client = SystembolagetClient()
api = SystembolagetAPI(client)

# Simple query only
api.search("Nils Oscar")

# Query with filters
api.search("wine", FilterOptions(price_max=200, country=["France"]))

# Everything
api.search(
    query="red wine",
    options=FilterOptions(
        price_min=100,
        price_max=500,
        country=["France", "Italy"],
        vintage=[2018, 2019],
    ),
)

# Simple search with sorting
api.search("Nils Oscar", sort_by="ProductLaunchDate", sort_direction="Ascending")

# With filters too
api.search(
    query="wine",
    sort_by="Price",
    sort_direction="Descending",
    options=FilterOptions(price_max=200, country=["France"]),
)
```