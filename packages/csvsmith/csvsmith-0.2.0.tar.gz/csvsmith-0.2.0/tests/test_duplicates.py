import pandas as pd
import pandas.testing as pdt

from csvsmith.duplicates import (
    count_duplicates_sorted,
    add_row_digest,
    find_duplicate_rows,
    dedupe_with_report,
)


# -------------------------------------------------------------------
# count_duplicates_sorted
# -------------------------------------------------------------------


def test_count_duplicates_sorted_basic():
    items = ["a", "b", "a", "c", "a", "b"]
    result = count_duplicates_sorted(items)
    assert result == [("a", 3), ("b", 2)]


def test_count_duplicates_sorted_threshold():
    items = ["x", "x", "y", "y", "y"]
    result = count_duplicates_sorted(items, threshold=3)
    assert result == [("y", 3)]


def test_count_duplicates_sorted_reverse_false():
    items = ["a", "b", "a", "b", "b"]
    result = count_duplicates_sorted(items, reverse=False)
    assert result == [("a", 2), ("b", 3)]


def test_count_duplicates_sorted_empty_input():
    items: list[str] = []
    result = count_duplicates_sorted(items)
    assert result == []


def test_count_duplicates_sorted_numeric_items():
    items = [1, 2, 2, 3, 3, 3]
    result = count_duplicates_sorted(items)
    assert result == [(3, 3), (2, 2)]


def test_count_duplicates_sorted_threshold_above_all():
    items = ["a", "a", "b"]
    result = count_duplicates_sorted(items, threshold=5)
    assert result == []


# -------------------------------------------------------------------
# add_row_digest
# -------------------------------------------------------------------


def test_add_row_digest_basic():
    df = pd.DataFrame({"A": [1, 1, 2], "B": ["x", "x", "y"]})
    out = add_row_digest(df)
    assert "row_digest" in out.columns

    # identical rows → identical digests
    assert out["row_digest"].iloc[0] == out["row_digest"].iloc[1]
    # different row → different digest (very high probability)
    assert out["row_digest"].iloc[2] != out["row_digest"].iloc[0]


def test_add_row_digest_subset_columns():
    df = pd.DataFrame(
        {
            "A": [1, 1, 1],
            "B": ["x", "y", "z"],
        }
    )
    out = add_row_digest(df, subset=["A"], colname="digest_a")
    assert "digest_a" in out.columns
    assert len(out["digest_a"].unique()) == 1


def test_add_row_digest_inplace_true_returns_same_object():
    df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
    df_id_before = id(df)
    out = add_row_digest(df, inplace=True)
    df_id_after = id(df)
    assert df_id_before == df_id_after
    assert id(out) == id(df)
    assert "row_digest" in df.columns


def test_add_row_digest_handles_nans():
    df = pd.DataFrame({"A": [1, None, 1], "B": ["x", "x", None]})
    out = add_row_digest(df)
    assert "row_digest" in out.columns
    digest_series = out["row_digest"]
    assert digest_series.notna().all()
    assert digest_series.map(len).eq(64).all()


def test_add_row_digest_exclude_id_column():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "value": [10, 10, 20],
        }
    )

    # Without exclude: all rows differ (id is included)
    out_all = add_row_digest(df)
    assert len(out_all["row_digest"].unique()) == 3

    # With exclude: only "value" is used -> rows 0 and 1 should match
    out_no_id = add_row_digest(df, exclude=["id"])
    digests = out_no_id["row_digest"]
    assert digests.iloc[0] == digests.iloc[1]
    assert digests.iloc[2] != digests.iloc[0]


# -------------------------------------------------------------------
# find_duplicate_rows
# -------------------------------------------------------------------


def test_find_duplicate_rows_all_columns():
    df = pd.DataFrame(
        {
            "A": [1, 1, 2, 2, 2, 3],
            "B": ["x", "x", "y", "y", "z", "z"],
        }
    )
    dup_df = find_duplicate_rows(df)
    assert list(dup_df.index) == [0, 1, 2, 3]


def test_find_duplicate_rows_subset():
    df = pd.DataFrame(
        {
            "A": [1, 1, 2, 2, 2, 3],
            "B": [10, 11, 20, 21, 22, 30],
        }
    )
    dup_df = find_duplicate_rows(df, subset=["A"])
    assert list(dup_df.index) == [0, 1, 2, 3, 4]


def test_find_duplicate_rows_no_duplicates():
    df = pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})
    dup_df = find_duplicate_rows(df)
    assert dup_df.empty


def test_find_duplicate_rows_empty_df():
    df = pd.DataFrame(columns=["A", "B"])
    dup_df = find_duplicate_rows(df)
    assert dup_df.empty
    assert list(dup_df.columns) == ["A", "B"]


# -------------------------------------------------------------------
# dedupe_with_report
# -------------------------------------------------------------------


def test_dedupe_with_report_all_columns():
    df = pd.DataFrame(
        {
            "A": [1, 1, 2, 2, 2, 3],
            "B": ["x", "x", "y", "y", "z", "z"],
        }
    )

    deduped, report = dedupe_with_report(df)

    expected = df.drop_duplicates()
    pdt.assert_frame_equal(
        deduped.reset_index(drop=True),
        expected.reset_index(drop=True),
    )

    assert set(report.columns) == {"row_digest", "count", "indices"}
    assert sorted(report["count"].tolist(), reverse=True) == [2, 2]


def test_dedupe_with_report_subset_column():
    df = pd.DataFrame(
        {
            "A": [1, 1, 2, 2, 2, 3],
            "B": [10, 11, 20, 21, 22, 30],
        }
    )

    deduped, report = dedupe_with_report(df, subset=["A"])
    expected = df.drop_duplicates(subset=["A"])

    pdt.assert_frame_equal(
        deduped.reset_index(drop=True),
        expected.reset_index(drop=True),
    )

    assert sorted(report["count"].tolist(), reverse=True) == [3, 2]


def test_dedupe_with_report_no_duplicates_gives_empty_report():
    df = pd.DataFrame(
        {
            "A": [1, 2, 3],
            "B": ["x", "y", "z"],
        }
    )
    deduped, report = dedupe_with_report(df)
    expected = df.drop_duplicates()

    pdt.assert_frame_equal(
        deduped.reset_index(drop=True),
        expected.reset_index(drop=True),
    )
    assert report.empty


def test_dedupe_with_report_keep_last():
    df = pd.DataFrame(
        {
            "A": [1, 1, 1],
            "B": ["x", "y", "z"],
        }
    )

    deduped_first, _ = dedupe_with_report(df, subset=["A"], keep="first")
    deduped_last, _ = dedupe_with_report(df, subset=["A"], keep="last")

    assert deduped_first.iloc[0]["B"] == "x"
    assert deduped_last.iloc[0]["B"] == "z"


def test_dedupe_with_report_custom_digest_col_name():
    df = pd.DataFrame(
        {
            "A": [1, 1, 2, 2],
            "B": ["x", "x", "y", "y"],
        }
    )

    deduped, report = dedupe_with_report(df, digest_col="my_digest")

    expected = df.drop_duplicates()
    pdt.assert_frame_equal(
        deduped.reset_index(drop=True),
        expected.reset_index(drop=True),
    )

    assert "my_digest" in report.columns
    assert set(report.columns) == {"my_digest", "count", "indices"}
