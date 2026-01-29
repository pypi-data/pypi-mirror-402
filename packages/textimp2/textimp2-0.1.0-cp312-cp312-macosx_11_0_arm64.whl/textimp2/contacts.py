import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Union

import polars as pl

DEFAULT_CONTACTS_DB_PATH = [
    *Path.home()
    .joinpath("Library/Application Support/AddressBook/Sources")
    .rglob("AddressBook-v22.abcddb"),
    Path.home().joinpath(
        "Library/Application Support/AddressBook/AddressBook-v22.abcddb"
    ),
]


def normalize_id(contact_id: str) -> str:
    """
    Normalize contact IDs (phone numbers and email addresses).

    Args:
        contact_id: Raw contact ID (phone number or email)

    Returns:
        Normalized contact ID:
        - Email addresses are lowercased and stripped
        - 10-digit phone numbers get +1 prefix
        - 11-digit phone numbers get + prefix
        - Other numbers are returned as-is
    """
    if "@" in contact_id:
        return contact_id.strip().lower()  # Email addresses

    numbers = "".join([c for c in contact_id if c.isdigit()])
    if len(numbers) == 10:
        return f"+1{numbers}"  # Assumes country code is +1 if not present
    elif len(numbers) == 11:
        return f"+{numbers}"
    else:
        return numbers  # Non traditional phone numbers


def coredata_to_datetime(coredata_timestamp):
    if coredata_timestamp is None:
        return None
    coredata_epoch = datetime(2001, 1, 1)
    return coredata_epoch + timedelta(seconds=coredata_timestamp)


def get_contacts(
    db_paths: Union[
        str, Path, List[Union[str, Path]], List[Path]
    ] = DEFAULT_CONTACTS_DB_PATH,
) -> pl.DataFrame:
    """
    Get contacts information from the AddressBook database(s).

    Args:
        db_paths: Path or list of paths to AddressBook database files

    Returns:
        DataFrame containing contact information with columns:
        - normalized_contact_id: Normalized phone number or email address
        - first_name: Contact's first name
        - last_name: Contact's last name
        - state: State from postal address
        - city: City from postal address
    """
    if isinstance(db_paths, (str, Path)):
        db_paths = [db_paths]

    dfs = []

    # Filter for existing paths to avoid errors on missing DBs
    valid_paths = [p for p in db_paths if Path(p).exists()]

    for db_path in valid_paths:
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            fields = """
                r.Z_PK as primary_key,
                COALESCE(r.ZFIRSTNAME, '') as first_name,
                COALESCE(r.ZLASTNAME, '') as last_name,
                COALESCE(a.ZSTATE, '') as state,
                COALESCE(a.ZCITY, '') as city,
                r.ZCREATIONDATE as creation_date,
                r.ZMODIFICATIONDATE as modification_date
                FROM ZABCDRECORD as r
                LEFT JOIN ZABCDPOSTALADDRESS as a on r.Z_PK = a.ZOWNER
            """

            # We need to be careful with schemas that might differ slightly or empty tables
            # But generally the AddressBook schema is consistent on macOS

            query = f"""
            SELECT 
                COALESCE(p.ZFULLNUMBER, '') as contact_id,
                {fields}
            LEFT JOIN ZABCDPHONENUMBER as p on r.Z_PK = p.ZOWNER
            WHERE p.ZFULLNUMBER IS NOT NULL

            UNION ALL

            SELECT 
                COALESCE(e.ZADDRESS, '') as contact_id,
                {fields}
            LEFT JOIN ZABCDEMAILADDRESS as e on r.Z_PK = e.ZOWNER
            WHERE e.ZADDRESS IS NOT NULL
            """
            # Define schema overrides to ensure consistency
            schema_overrides = {
                "contact_id": pl.Utf8,
                "primary_key": pl.Int64,
                "first_name": pl.Utf8,
                "last_name": pl.Utf8,
                "state": pl.Utf8,
                "city": pl.Utf8,
                "creation_date": pl.Float64,
                "modification_date": pl.Float64,
            }

            df = pl.read_database(
                query=query, connection=conn, schema_overrides=schema_overrides
            )
            dfs.append(df)
        except sqlite3.OperationalError:
            # If tables don't exist, we just skip this DB
            # print(f"Error reading from {db_path}: {e}")
            pass
        except Exception as e:
            print(f"Unexpected error processing {db_path}: {e}")
        finally:
            if conn:
                conn.close()

    if dfs:
        # Concatenate all results with how="diagonal" or checking schemas easier if we enforced it
        try:
            combined_df = pl.concat(dfs, how="vertical_relaxed")
        except Exception as e:
            print(f"Error concatenating contact DFs: {e}")
            return pl.DataFrame()

        if combined_df.is_empty():
            return pl.DataFrame()

        # Ensure proper types before operations
        combined_df = combined_df.cast(
            {
                "contact_id": pl.Utf8,
                "first_name": pl.Utf8,
                "last_name": pl.Utf8,
                "state": pl.Utf8,
                "city": pl.Utf8,
            }
        )

        return (
            combined_df.unique()
            .filter((pl.col("contact_id").str.len_chars() > 3))
            .with_columns(
                pl.col("contact_id")
                .map_elements(normalize_id, return_dtype=pl.Utf8)
                .alias("normalized_contact_id"),
                pl.col("creation_date")
                .map_elements(coredata_to_datetime, return_dtype=pl.Datetime)
                .dt.strftime("%Y-%m-%d %H:%M:%S")
                .alias("creation_date"),
                pl.col("modification_date")
                .map_elements(coredata_to_datetime, return_dtype=pl.Datetime)
                .dt.strftime("%Y-%m-%d %H:%M:%S")
                .alias("modification_date"),
            )
        )
    return pl.DataFrame()
