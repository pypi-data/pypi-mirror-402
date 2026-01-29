# TextImp2

A Python library for interacting with iMessage data, built using Rust and Apache Arrow.

## Features

- **Fast & Efficient**: Built with Rust and `imessage-database` crate.
- **Arrow Integration**: Returns data as Apache Arrow RecordBatches, ensuring zero-copy or efficient conversion to Polars and Pandas.
- **Strict Typing**: Uses `imessage-database` structs for reliable parsing.

## Installation

```bash
git clone ...
cd textimp2
uv sync
```

## Usage

### Typed Getters

The library provides convenient getters for different DataFrames:

```python
import textimp2

# Get Polars DataFrames
df_msgs = textimp2.get_messages_polars()
df_handles = textimp2.get_handles_polars()

# Get Pandas DataFrames
df_msgs_pd = textimp2.get_messages_pandas()
df_handles_pd = textimp2.get_handles_pandas()

# Get Arrow RecordBatch
batch_msgs = textimp2.get_messages_arrow()
```

### Specifying a Database Path

All functions accept an optional `path` argument:

```python
df = textimp2.get_messages_polars("/path/to/chat.db")
```

## Permissions (macOS)

Accessing `~/Library/Messages/chat.db` requires **Full Disk Access**.
