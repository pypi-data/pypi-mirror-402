"""
polars-parquet-encrypt: Parquet encryption support for Polars

This package enables AES-256-GCM encryption for Polars Parquet files.
It works as a companion to the polars package and automatically enables
encryption features when installed.

Usage:
    import polars as pl
    import polars_parquet_encrypt  # This enables encryption support
    import os

    # Generate 32-byte key for AES-256
    key = os.urandom(32)

    # Write encrypted parquet
    df = pl.DataFrame({"a": [1, 2, 3]})
    df.write_parquet("encrypted.parquet", encryption_key=key)

    # Read encrypted parquet
    df_read = pl.read_parquet("encrypted.parquet", encryption_key=key)

Features:
    - AES-256-GCM authenticated encryption
    - Page-level encryption (data and dictionary pages)
    - Optimized performance with context reuse and in-place decryption
    - Cross-platform wheels (macOS, Linux)
"""

from polars_parquet_encrypt._internal import __version__

__all__ = ["__version__"]

# Print helpful message on import
print(f"polars-parquet-encrypt v{__version__} loaded - encryption support enabled")
print("Note: Make sure 'polars' is built with encryption feature enabled")
