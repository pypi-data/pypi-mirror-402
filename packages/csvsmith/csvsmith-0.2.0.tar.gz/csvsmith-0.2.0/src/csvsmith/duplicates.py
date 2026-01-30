"""
Duplicate-related helpers for csvsmith.

Includes:
- count_duplicates_sorted: generic iterable duplicate counter
- add_row_digest: add a SHA-256 digest per row to a DataFrame
- find_duplicate_rows: return only rows that have duplicates
- dedupe_with_report: drop duplicates and report duplicate groups
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from typing import Iterable, List, Tuple, Hashable, Sequence, Optional

import pandas as pd


def count_duplicates_sorted(
    items: Iterable[Hashable],
    threshold: int = 2,
    reverse: bool = True,
) -> List[Tuple[Hashable, int]]:
    """
    Count occurrences in an iterable and return items whose frequency
    is at or above `threshold`, sorted by count.

    Args:
        items:
            Any iterable of hashable items (str, int, tuple, etc.)
        threshold:
            Minimum count to include in output (default: 2).
        reverse:
            Whether to sort in descending order (default: True).

    Returns:
        A list of (item, count) tuples sorted by frequency.
    """
    counter = Counter(items)
    duplicates = [(k, v) for k, v in counter.items() if v >= threshold]
    duplicates.sort(key=lambda x: x[1], reverse=reverse)
    return duplicates


def add_row_digest(
    df: pd.DataFrame,
    *,
    subset: Optional[Sequence[Hashable]] = None,
    exclude: Optional[Sequence[Hashable]] = None,
    colname: str = "row_digest",
    inplace: bool = False,
) -> pd.DataFrame:
    """
    Add a SHA-256 digest for each row of a DataFrame.

    Args:
        df:
            Input DataFrame.
        subset:
            Optional list/sequence of column labels to use for the digest.
            If None, all columns are used.
        exclude:
            Optional list/sequence of column labels to exclude from the digest,
            after `subset` is applied. This is useful for excluding ID columns,
            timestamps, etc.
        colname:
            Name of the digest column to add (default: "row_digest").
        inplace:
            If True, modify the original DataFrame and return it.
            If False (default), return a copy.

    Returns:
        DataFrame with an extra column containing hex digests.

    Notes:
        We use the ASCII "Unit Separator" (0x1F, "\\x1f") as the internal
        delimiter when concatenating row values before hashing. It is a
        non-printable control character that almost never appears in normal
        CSV data, which helps avoid accidental collisions like:

            ["ab", "c"] vs ["a", "bc"]

        Credo #5 of csvsmith: "Love thy \\x1f."
    """
    # Determine columns to include
    if subset is None:
        cols = list(df.columns)
    else:
        cols = list(subset)

    if exclude:
        exclude_set = set(exclude)
        cols = [c for c in cols if c not in exclude_set]

    # Convert to string, fill NaNs, and join with a non-printable separator
    concatted = df[cols].astype("string").fillna("").agg("\x1f".join, axis=1)
    digests = concatted.map(lambda s: sha256(s.encode("utf-8")).hexdigest())

    if inplace:
        df[colname] = digests
        return df
    else:
        df2 = df.copy()
        df2[colname] = digests
        return df2


def find_duplicate_rows(
    df: pd.DataFrame,
    *,
    subset: Optional[Sequence[Hashable]] = None,
) -> pd.DataFrame:
    """
    Return only rows that participate in duplicates.

    This is a convenience wrapper around `df.duplicated(keep=False)`.

    Args:
        df:
            Input DataFrame.
        subset:
            Columns to consider when identifying duplicates. If None,
            all columns are used.

    Returns:
        A DataFrame containing only rows that have at least one duplicate,
        preserving the original order and index.
    """
    mask = df.duplicated(subset=subset, keep=False)
    return df[mask]


def dedupe_with_report(
    df: pd.DataFrame,
    *,
    subset: Optional[Sequence[Hashable]] = None,
    exclude: Optional[Sequence[Hashable]] = None,
    keep: str = "first",
    digest_col: str = "row_digest",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Drop duplicate rows *and* return a report of what was duplicated.

    Args:
        df:
            Input DataFrame.
        subset:
            Columns to consider when identifying duplicates. If None,
            all columns are used.
        exclude:
            Columns to exclude from the duplicate check and digest,
            after `subset` is applied. Useful for ID columns, timestamps, etc.
        keep:
            Which duplicate to keep. Same semantics as pandas:
            "first", "last", or "False" (string). Default: "first".
        digest_col:
            Name of the temporary digest column used for grouping in the
            report (default: "row_digest").

    Returns:
        (df_deduped, report)

        df_deduped:
            DataFrame with duplicates dropped according to the effective
            subset (subset minus exclude) and `keep`.

        report:
            DataFrame with one row per duplicate group, columns:
              - digest_col: the SHA-256 row digest
              - count: number of rows in this group
              - indices: list of original DataFrame indices in this group

            Only groups with count > 1 are included, sorted by `count`
            descending.
    """
    # Determine effective subset for both hashing and drop_duplicates
    if subset is None:
        cols = list(df.columns)
    else:
        cols = list(subset)

    if exclude:
        exclude_set = set(exclude)
        cols = [c for c in cols if c not in exclude_set]

    subset_for_dupes: Optional[Sequence[Hashable]]
    if cols:
        subset_for_dupes = cols
    else:
        subset_for_dupes = None

    # Work on a copy with a digest column, using the effective subset
    work = add_row_digest(
        df,
        subset=subset_for_dupes,
        exclude=None,
        colname=digest_col,
        inplace=False,
    )

    grouped = work.groupby(digest_col, dropna=False)

    sizes = grouped.size().rename("count")
    indices_map = {k: list(v) for k, v in grouped.indices.items()}
    indices = pd.Series(indices_map, name="indices")

    report = (
        pd.concat([sizes, indices], axis=1)
        .reset_index()
        .rename(columns={"index": digest_col})
    )

    report = (
        report[report["count"] > 1]
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )

    df_deduped = df.drop_duplicates(subset=subset_for_dupes, keep=keep)
    return df_deduped, report
