import textimp2
import polars as pl
import sys


def main():
    print("🚀 Starting textimp2 capability demonstration...")

    # 1. Load Data
    print("\n--- Loading Data ---")
    try:
        # Load Messages
        print("Loading messages...", end=" ")
        df_messages = textimp2.get_messages_polars()
        print(f"✅ Loaded {len(df_messages)} messages.")

        # Load Handles (map internal IDs to phone numbers/emails)
        print("Loading handles...", end=" ")
        df_handles = textimp2.get_handles_polars()
        print(f"✅ Loaded {len(df_handles)} handles.")

        # Load Attachments
        print("Loading attachments...", end=" ")
        df_attachments = textimp2.get_attachments_polars()
        print(f"✅ Loaded {len(df_attachments)} attachments.")

        # Load Contacts (from Mac Address Book)
        print("Loading contacts...", end=" ")
        df_contacts = textimp2.get_contacts()
        print(f"✅ Loaded {len(df_contacts)} contacts.")

    except Exception as e:
        print(f"\n❌ Error loading data: {e}")
        print(
            "Ensure you have granted permission to access Messages and Contacts if on macOS."
        )
        sys.exit(1)

    # 2. Enriched Messages Analysis
    # Join Messages -> Handles -> Contacts
    print("\n--- Message Analysis ---")

    if not df_messages.is_empty() and not df_handles.is_empty():
        # Handles: rowid is the key used in messages 'handle_id'
        # Rename rowid to handle_id for easier join, and id to contact_id (phone/email)
        df_handles_clean = df_handles.select(
            [
                pl.col("rowid").cast(pl.Int32).alias("handle_id"),
                pl.col("id").alias("raw_contact_id"),
            ]
        )

        # Join Messages with Handles
        df_enriched = df_messages.join(df_handles_clean, on="handle_id", how="left")

        # If we have contacts, try to resolve names
        if not df_contacts.is_empty():
            # Join with Contacts on normalized IDs if possible, or just raw match
            # For this example we'll assume exact match or simple normalization logic is handled
            # distinct contact identifiers
            df_contacts_clean = df_contacts.select(
                [
                    pl.col("normalized_contact_id"),
                    pl.col("first_name"),
                    pl.col("last_name"),
                ]
            ).unique(subset=["normalized_contact_id"])

            # Simple normalization for join (matching logic in textimp2.contacts)
            # We'll use the raw_contact_id to join with normalized_contact_id
            # (In a real app you might need more robust normalization)
            df_enriched = df_enriched.with_columns(
                pl.col("raw_contact_id").alias(
                    "normalized_contact_id"
                )  # Simplifying assumption for example
            ).join(df_contacts_clean, on="normalized_contact_id", how="left")

            # Create a display name
            df_enriched = df_enriched.with_columns(
                pl.when(pl.col("first_name").is_not_null())
                .then(
                    pl.concat_str(
                        [pl.col("first_name"), pl.col("last_name")], separator=" "
                    )
                )
                .otherwise(pl.col("raw_contact_id"))
                .alias("display_name")
            )
        else:
            df_enriched = df_enriched.with_columns(
                pl.col("raw_contact_id").alias("display_name")
            )

        print("\nTop 5 Active Chats:")
        top_chats = (
            df_enriched.group_by("display_name")
            .agg(pl.len().alias("message_count"))
            .sort("message_count", descending=True)
            .head(5)
        )
        print(top_chats)

        print("\nSent vs Received:")
        sent_received = df_enriched.group_by("is_from_me").agg(pl.len().alias("count"))
        print(sent_received)

        print("\nMessages per Year:")
        if "date" in df_enriched.columns:
            # Ensure date is datetime
            df_time = df_enriched.with_columns(pl.col("date").cast(pl.Datetime))
            msgs_per_year = (
                df_time.group_by(pl.col("date").dt.year().alias("year"))
                .agg(pl.len().alias("count"))
                .sort("year")
            )
            print(msgs_per_year)

    # 3. Attachment Analysis
    print("\n--- Attachment Analysis ---")
    if not df_attachments.is_empty():
        print(
            f"Total size of attachments: {df_attachments['total_bytes'].sum() / 1e9:.2f} GB"
        )

        print("\nTop 5 Mime Types:")
        top_mime = (
            df_attachments.group_by("mime_type")
            .agg(pl.len().alias("count"))
            .sort("count", descending=True)
            .head(5)
        )
        print(top_mime)

    print("\n✅ Demonstration Complete.")


if __name__ == "__main__":
    main()
