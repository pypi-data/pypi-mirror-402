from textimp2._core import read_messages as _read_messages_arrow
from textimp2._core import read_handles as _read_handles_arrow
from textimp2._core import read_attachments as _read_attachments_arrow
from textimp2.contacts import get_contacts
import polars as pl

from typing import Optional, TYPE_CHECKING
import pyarrow as pa

if TYPE_CHECKING:
    import pandas as pd


def get_messages_arrow(path: Optional[str] = None) -> pa.RecordBatch:
    """
    Get messages as an Arrow RecordBatch.
    """
    return _read_messages_arrow(path)


def get_messages_polars(path: Optional[str] = None) -> pl.DataFrame:
    """
    Get messages as a Polars DataFrame.
    """
    batch = get_messages_arrow(path)
    return pl.from_arrow(batch)


def get_messages_pandas(path: Optional[str] = None) -> "pd.DataFrame":
    """
    Get messages as a Pandas DataFrame.
    """
    # Polars to_pandas is often faster/better handle for types than raw pyarrow sometimes
    return get_messages_polars(path).to_pandas()


def get_handles_arrow(path: Optional[str] = None) -> pa.RecordBatch:
    """
    Get handles as an Arrow RecordBatch.
    """
    return _read_handles_arrow(path)


def get_handles_polars(path: Optional[str] = None) -> pl.DataFrame:
    """
    Get handles as a Polars DataFrame.
    """
    batch = get_handles_arrow(path)
    return pl.from_arrow(batch)


def get_handles_pandas(path: Optional[str] = None) -> "pd.DataFrame":
    """
    Get handles as a Pandas DataFrame.
    """
    return get_handles_polars(path).to_pandas()


def get_attachments_arrow(path: Optional[str] = None) -> pa.RecordBatch:
    """
    Get attachments as an Arrow RecordBatch.
    """
    return _read_attachments_arrow(path)


def get_attachments_polars(path: Optional[str] = None) -> pl.DataFrame:
    """
    Get attachments as a Polars DataFrame.
    """
    batch = get_attachments_arrow(path)
    return pl.from_arrow(batch)


def get_attachments_pandas(path: Optional[str] = None) -> "pd.DataFrame":
    """
    Get attachments as a Pandas DataFrame.
    """
    return get_attachments_polars(path).to_pandas()


# Aliases for backward compatibility or convenience if needed
read_messages = get_messages_arrow
read_handles = get_handles_arrow
read_attachments = get_attachments_arrow

__all__ = [
    "get_messages_arrow",
    "get_messages_polars",
    "get_messages_pandas",
    "get_handles_arrow",
    "get_handles_polars",
    "get_handles_pandas",
    "get_attachments_arrow",
    "get_attachments_polars",
    "get_attachments_pandas",
    "get_contacts",
    "read_messages",
    "read_handles",
    "read_attachments",
]
