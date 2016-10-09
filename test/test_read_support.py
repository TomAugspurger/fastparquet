"""test_read_support.py - unit and integration tests for reading parquet data."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io
import json
import os
import sys
import tempfile
import unittest

import pandas as pd
import pytest

import parquet

TEST_DATA = "test-data"


def test_header_magic_bytes():
    """Test reading the header magic bytes."""
    f = io.BytesIO(b"PAR1_some_bogus_data")
    with pytest.raises(parquet.ParquetFormatException):
        p = parquet.ParquetFile(f)


def test_read_footer():
    """Test reading the footer."""
    p = parquet.ParquetFile(os.path.join(TEST_DATA, "nation.impala.parquet"))
    snames = {"schema", "n_regionkey", "n_name", "n_nationkey", "n_comment"}
    assert {s.name for s in p.schema} == snames
    assert set(p.columns) == snames - {"schema"}

files = [os.path.join(TEST_DATA, p) for p in
         ["gzip-nation.impala.parquet", "nation.dict.parquet",
          "nation.impala.parquet", "nation.plain.parquet",
          "snappy-nation.impala.parquet"]]
csvfile = os.path.join(TEST_DATA, "nation.csv")
cols = ["n_nationkey", "n_name", "n_regionkey", "n_comment"]
expected = pd.read_csv(csvfile, delimiter="|", index_col=0, names=cols)


@pytest.mark.parametrize("parquet_file", files)
def test_file_csv(parquet_file):
    """Test the various file times
    """
    p = parquet.ParquetFile(parquet_file)
    data = p.to_pandas()
    data.columns = cols   # some versions have slightly different naming
    data.set_index('n_nationkey', inplace=True)

    # FIXME: in future, reader will return UTF8 strings
    data['n_comment'] = data['n_comment'].str.decode('utf8')
    data['n_name'] = data['n_name'].str.decode('utf8')
    for col in cols[1:]:
        assert (data[col] == expected[col]).all()


def test_null_int():
    """Test reading a file that contains null records."""
    p = parquet.ParquetFile(os.path.join(TEST_DATA, "test-null.parquet"))
    data = p.to_pandas()
    expected = pd.DataFrame([{"foo": 1, "bar": 2}, {"foo": 1, "bar": None}])
    for col in data:
        assert data[col].equals(expected[col])


def test_converted_type_null():
    """Test reading a file that contains null records for a plain column that
     is converted to utf-8."""
    p = parquet.ParquetFile(os.path.join(TEST_DATA,
                                         "test-converted-type-null.parquet"))
    data = p.to_pandas()
    expected = pd.DataFrame([{"foo": "bar"}, {"foo": None}])
    for col in data:
        assert data[col].equals(expected[col])


def test_null_plain_dictionary():
    """Test reading a file that contains null records for a plain dictionary
     column."""
    p = parquet.ParquetFile(os.path.join(TEST_DATA,
                                         "test-null-dictionary.parquet"))
    data = p.to_pandas()
    expected = pd.DataFrame([{"foo": None}] + [{"foo": "bar"},
                             {"foo": "baz"}] * 3)
    for col in data:
        assert data[col].equals(expected[col])
