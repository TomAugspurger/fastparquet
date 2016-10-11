
from itertools import product
import numpy as np
import os
import pandas as pd
from parquet import ParquetFile
from parquet import write
import pytest
import shutil
import tempfile
pyspark = pytest.importorskip("pyspark")
sc = pyspark.SparkContext.getOrCreate()
sql = pyspark.SQLContext(sc)


@pytest.yield_fixture()
def tempdir():
    d = tempfile.mkdtemp()
    yield d
    if os.path.exists(d):
        shutil.rmtree(d, ignore_errors=True)


@pytest.mark.parametrize("scheme,partitions,comp",
                         product(('simple', 'hive'),
                                 ([0], [0, 500]),
                                 (None, 'GZIP', 'SNAPPY')))
def test_pyspark_roundtrip(tempdir, scheme, partitions, comp):
    data = pd.DataFrame({'i32': np.arange(1000, dtype=np.int32),
                         'i64': np.arange(1000, dtype=np.int64),
                         'f': np.arange(1000, dtype=np.float64),
                         'hello': np.random.choice([b'hello', b'you',
                            b'people'], size=1000).astype("O")})

    fname = os.path.join(tempdir, 'test.parquet')
    write(fname, data, file_scheme=scheme, partitions=partitions)

    df = sql.read.parquet(fname)
    ddf = df.toPandas()
    for col in data:
        assert (ddf[col] == data[col]).all()


@pytest.mark.parametrize('partitions,comp',
                         product(([0], [0, 500]),
                                 (None, 'GZIP', 'SNAPPY')))
def test_roundtrip(tempdir, partitions, comp):
    data = pd.DataFrame({'i32': np.arange(1000, dtype=np.int32),
                         'i64': np.arange(1000, dtype=np.int64),
                         'f': np.arange(1000, dtype=np.float64),
                         'hello': np.random.choice([b'hello', b'you',
                            b'people'], size=1000).astype("O")})
    # data['a'] = np.array([b'a', b'b', b'c', b'd', b'e']*200, dtype="S1")
    # data['aa'] = data['a'].map(lambda x: 2*x).astype("S2")
    # data['cat'] = data.hello.astype('category')
    fname = os.path.join(tempdir, 'test.parquet')
    write(fname, data, file_scheme='simple', partitions=partitions,
          compression=comp)

    r = ParquetFile(fname)

    df = r.to_pandas()
    for col in r.columns:
        assert (df[col] == data[col]).all()

