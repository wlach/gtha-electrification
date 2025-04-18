#!/usr/bin/env python

import sys

import polars as pl


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python concat-simplify-irradiance.py <input_file1> <input_file2> ..."
        )
        sys.exit(1)

    # Read the input files and concatenate them
    # into a single DataFrame
    df = pl.concat([pl.read_csv(filename) for filename in sys.argv[1:]])
    df = df.with_columns(
        pl.col("Date").str.slice(0, 10).str.strptime(pl.Date, "%Y-%m-%d").alias("Date")
    )

    # Output to single CSV to stdout
    df.write_csv(sys.stdout)
