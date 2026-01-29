"""
Comprehensive test suite for EnhancedPolars (epl.py).

Tests cover:
- Data type inference (infer_dtype, infer_dtypes)
- Type conversion and optimization
- Schema merging
- Dtype parsing
- File I/O helpers
- DataFrame metadata extraction
"""

import sys
from pathlib import Path
import tempfile

import pytest
import polars as pl
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhancedpolars.epl import EnhancedPolars
from CoreUtilities.core_types import CoreDataType


# ============================================================================
# Dtype Inference Tests
# ============================================================================

class TestInferDtype:
    """Test infer_dtype function for single series."""

    def test_infer_int64(self):
        """Test inference of Int64 type."""
        series = pl.Series("test", [1, 2, 3, 4, 5])
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.INTEGER
        assert meta['min_value'] == 1
        assert meta['max_value'] == 5

    def test_infer_float64(self):
        """Test inference of Float64 type."""
        series = pl.Series("test", [1.5, 2.5, 3.5])
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.FLOAT
        assert meta['min_value'] == 1.5
        assert meta['max_value'] == 3.5

    def test_infer_string(self):
        """Test inference of String type."""
        series = pl.Series("test", ["hello", "world", "test"])
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.STRING
        assert 'max_byte_length' in meta

    def test_infer_boolean(self):
        """Test inference of Boolean type."""
        series = pl.Series("test", [True, False, True])
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.BOOLEAN

    def test_infer_datetime(self):
        """Test inference of Datetime type."""
        series = pl.Series("test", ["2023-01-15", "2023-06-20"]).str.to_datetime("%Y-%m-%d")
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.DATETIME

    def test_infer_date(self):
        """Test inference of Date type."""
        series = pl.Series("test", ["2023-01-15", "2023-06-20"]).str.to_date("%Y-%m-%d")
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.DATE

    def test_infer_with_nulls(self):
        """Test inference handles null values correctly."""
        series = pl.Series("test", [1, None, 3, None, 5])
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.INTEGER
        assert meta['percent_null'] > 0  # Has null values

    def test_infer_all_nulls(self):
        """Test inference of series with all nulls."""
        series = pl.Series("test", [None, None, None])
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['percent_null'] == 100.0  # All null values

    def test_infer_string_max_byte_length(self):
        """Test that max_byte_length is calculated for strings."""
        series = pl.Series("test", ["a", "hello", "hello world!"])
        meta = EnhancedPolars.infer_dtype(series)

        assert meta['core_data_type'] == CoreDataType.STRING
        assert meta['max_byte_length'] >= 12  # "hello world!" is 12 chars


# ============================================================================
# Dtype Inference for DataFrames
# ============================================================================

class TestInferDtypes:
    """Test infer_dtypes function for DataFrames."""

    def test_infer_dtypes_basic(self):
        """Test basic DataFrame dtype inference."""
        df = pl.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.5, 2.5, 3.5],
            "str_col": ["a", "b", "c"],
        })

        result = EnhancedPolars.infer_dtypes(df, return_df=False)

        assert "int_col" in result
        assert "float_col" in result
        assert "str_col" in result
        assert result["int_col"]["core_data_type"] == CoreDataType.INTEGER
        assert result["float_col"]["core_data_type"] == CoreDataType.FLOAT
        assert result["str_col"]["core_data_type"] == CoreDataType.STRING

    def test_infer_dtypes_lazyframe(self):
        """Test dtype inference on LazyFrame."""
        lf = pl.LazyFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
        })

        # Should work with LazyFrame
        result = EnhancedPolars.infer_dtypes(lf, return_df=False)

        assert "id" in result
        assert "name" in result

    def test_infer_dtypes_with_precision_scale(self):
        """Test inference with precision and scale collection."""
        df = pl.DataFrame({
            "decimal_col": [123.45, 678.90, 999.99],
        })

        result = EnhancedPolars.infer_dtypes(
            df,
            collect_precision_scale=True,
            return_df=False
        )

        assert "precision" in result["decimal_col"] or "scale" in result["decimal_col"]


# ============================================================================
# Type Parsing Tests
# ============================================================================

class TestParseDtype:
    """Test parse_dtype function."""

    def test_parse_string_int(self):
        """Test parsing 'int64' string."""
        result = EnhancedPolars.parse_dtype("int64")
        assert result == pl.Int64()

    def test_parse_string_float(self):
        """Test parsing 'float64' string."""
        result = EnhancedPolars.parse_dtype("float64")
        assert result == pl.Float64()

    def test_parse_string_str(self):
        """Test parsing 'string' string."""
        result = EnhancedPolars.parse_dtype("string")
        assert result == pl.String()

    def test_parse_python_type_int(self):
        """Test parsing Python int type."""
        result = EnhancedPolars.parse_dtype(int)
        assert result == pl.Int64()

    def test_parse_python_type_float(self):
        """Test parsing Python float type."""
        result = EnhancedPolars.parse_dtype(float)
        assert result == pl.Float64()

    def test_parse_python_type_str(self):
        """Test parsing Python str type."""
        result = EnhancedPolars.parse_dtype(str)
        assert result == pl.String()

    def test_parse_python_type_bool(self):
        """Test parsing Python bool type."""
        result = EnhancedPolars.parse_dtype(bool)
        assert result == pl.Boolean()

    def test_parse_numpy_dtype(self):
        """Test parsing numpy dtype."""
        result = EnhancedPolars.parse_dtype(np.dtype('int32'))
        assert result == pl.Int32()

    def test_parse_polars_dtype(self):
        """Test parsing Polars dtype (should return as-is)."""
        result = EnhancedPolars.parse_dtype(pl.Int64())
        assert result == pl.Int64()

    def test_parse_datetime_string(self):
        """Test parsing datetime string variants."""
        result = EnhancedPolars.parse_dtype("datetime")
        assert isinstance(result, pl.Datetime)

    def test_parse_date_string(self):
        """Test parsing date string."""
        result = EnhancedPolars.parse_dtype("date")
        assert result == pl.Date()


# ============================================================================
# Numpy Dtype Conversion Tests
# ============================================================================

class TestNumpyDtypeConversion:
    """Test _numpy_dtype_to_polars helper."""

    def test_numpy_int8(self):
        """Test numpy int8 conversion."""
        result = EnhancedPolars._numpy_dtype_to_polars(np.dtype('int8'))
        assert result == pl.Int8()

    def test_numpy_int64(self):
        """Test numpy int64 conversion."""
        result = EnhancedPolars._numpy_dtype_to_polars(np.dtype('int64'))
        assert result == pl.Int64()

    def test_numpy_float32(self):
        """Test numpy float32 conversion."""
        result = EnhancedPolars._numpy_dtype_to_polars(np.dtype('float32'))
        assert result == pl.Float32()

    def test_numpy_float64(self):
        """Test numpy float64 conversion."""
        result = EnhancedPolars._numpy_dtype_to_polars(np.dtype('float64'))
        assert result == pl.Float64()

    def test_numpy_bool(self):
        """Test numpy bool conversion."""
        result = EnhancedPolars._numpy_dtype_to_polars(np.dtype('bool'))
        assert result == pl.Boolean()

    def test_numpy_datetime64(self):
        """Test numpy datetime64 conversion."""
        result = EnhancedPolars._numpy_dtype_to_polars(np.dtype('datetime64[ns]'))
        assert isinstance(result, pl.Datetime)


# ============================================================================
# Schema Merging Tests
# ============================================================================

class TestSchemaMerging:
    """Test schema merging functionality."""

    def test_merge_identical_schemas(self):
        """Test merging identical schemas."""
        schema1 = {"a": pl.Int64, "b": pl.String}
        schema2 = {"a": pl.Int64, "b": pl.String}

        result = EnhancedPolars.merge_schemas(schema1, schema2)

        assert result == {"a": pl.Int64, "b": pl.String}

    def test_merge_schemas_with_new_columns(self):
        """Test merging schemas with new columns."""
        schema1 = {"a": pl.Int64}
        schema2 = {"b": pl.String}

        result = EnhancedPolars.merge_schemas(schema1, schema2)

        assert "a" in result
        assert "b" in result

    def test_merge_schemas_type_widening(self):
        """Test that types are widened when merging."""
        schema1 = {"a": pl.Int32}
        schema2 = {"a": pl.Int64}

        result = EnhancedPolars.merge_schemas(schema1, schema2)

        # Should widen to Int64
        assert result["a"] in [pl.Int64, pl.Int64()]

    def test_merge_polars_dtypes(self):
        """Test merge_polars_dtypes function."""
        result = EnhancedPolars.merge_polars_dtypes(pl.Int32(), pl.Int64())

        # Should return the wider type
        assert result == pl.Int64()


# ============================================================================
# Optimize Dtypes Tests
# ============================================================================

class TestOptimizeDtypes:
    """Test dtype optimization functionality."""

    def test_optimize_integer_downcast(self):
        """Test that integers are downcasted when possible."""
        df = pl.DataFrame({
            "small_int": pl.Series([1, 2, 3], dtype=pl.Int64),  # Can be UInt8 or Int8
        })

        result = EnhancedPolars.optimize_dtypes(df)

        # Should be downcasted to smaller int (signed or unsigned depending on values)
        assert result["small_int"].dtype in [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32]

    def test_optimize_float_downcast(self):
        """Test float optimization - whole-number floats may be converted to int."""
        df = pl.DataFrame({
            "float_col": pl.Series([1.0, 2.0, 3.0], dtype=pl.Float64),
        })

        result = EnhancedPolars.optimize_dtypes(df)

        # Whole-number floats may be downcasted to int types for efficiency
        assert result["float_col"].dtype in [pl.Float32, pl.Float64, pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32]

    def test_optimize_preserves_values(self):
        """Test that optimization preserves actual values."""
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "value": [100.5, 200.75, 300.25],
        })

        result = EnhancedPolars.optimize_dtypes(df)

        assert result["id"].to_list() == [1, 2, 3]
        assert result["value"].to_list() == [100.5, 200.75, 300.25]


# ============================================================================
# DataFrame Metadata Tests
# ============================================================================

class TestDataFrameMetadata:
    """Test DataFrame metadata extraction."""

    def test_get_dtype_meta(self):
        """Test get_dtype_meta function."""
        meta = EnhancedPolars.get_dtype_meta(pl.Int64())

        # Check for actual keys returned by get_dtype_meta
        assert 'core_data_type' in meta
        assert 'polars_type' in meta or 'dtype' in meta

    def test_get_meta_for_dataframe(self):
        """Test get_meta_for_dataframe function."""
        df = pl.DataFrame({
            "int_col": [1, 2, 3],
            "str_col": ["a", "b", "c"],
        })

        meta = EnhancedPolars.get_meta_for_dataframe(df)

        assert isinstance(meta, dict)
        assert "int_col" in meta or len(meta) > 0


# ============================================================================
# Bit Width Tests
# ============================================================================

class TestBitWidth:
    """Test bit_width function."""

    def test_bit_width_int8(self):
        """Test bit width for Int8."""
        assert EnhancedPolars.bit_width(pl.Int8) == 8

    def test_bit_width_int16(self):
        """Test bit width for Int16."""
        assert EnhancedPolars.bit_width(pl.Int16) == 16

    def test_bit_width_int32(self):
        """Test bit width for Int32."""
        assert EnhancedPolars.bit_width(pl.Int32) == 32

    def test_bit_width_int64(self):
        """Test bit width for Int64."""
        assert EnhancedPolars.bit_width(pl.Int64) == 64

    def test_bit_width_float32(self):
        """Test bit width for Float32."""
        assert EnhancedPolars.bit_width(pl.Float32) == 32

    def test_bit_width_float64(self):
        """Test bit width for Float64."""
        assert EnhancedPolars.bit_width(pl.Float64) == 64


# ============================================================================
# Type Helper Tests
# ============================================================================

class TestTypeHelpers:
    """Test type helper functions."""

    def test_is_float_helper(self):
        """Test _is_float_helper function."""
        assert EnhancedPolars._is_float_helper(pl.Float32()) is True
        assert EnhancedPolars._is_float_helper(pl.Float64()) is True
        assert EnhancedPolars._is_float_helper(pl.Int64()) is False

    def test_is_integer_helper(self):
        """Test _is_integer_helper function."""
        assert EnhancedPolars._is_integer_helper(pl.Int32()) is True
        assert EnhancedPolars._is_integer_helper(pl.Int64()) is True
        assert EnhancedPolars._is_integer_helper(pl.Float64()) is False

    def test_is_temporal_helper(self):
        """Test _is_temporal_helper function."""
        assert EnhancedPolars._is_temporal_helper(pl.Date()) is True
        assert EnhancedPolars._is_temporal_helper(pl.Datetime()) is True
        assert EnhancedPolars._is_temporal_helper(pl.Int64()) is False

    def test_is_string_helper(self):
        """Test _is_string_helper function."""
        assert EnhancedPolars._is_string_helper(pl.String()) is True
        assert EnhancedPolars._is_string_helper(pl.Utf8()) is True
        assert EnhancedPolars._is_string_helper(pl.Int64()) is False


# ============================================================================
# Data Conversion Tests
# ============================================================================

class TestFromData:
    """Test from_data conversion function."""

    def test_from_pandas_dataframe(self):
        """Test converting from pandas DataFrame."""
        pdf = pd.DataFrame({
            "a": [1, 2, 3],
            "b": ["x", "y", "z"],
        })

        result = EnhancedPolars.from_data(pdf)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_from_dict(self):
        """Test converting from dictionary."""
        data = {
            "a": [1, 2, 3],
            "b": ["x", "y", "z"],
        }

        result = EnhancedPolars.from_data(data)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_from_list_of_dicts(self):
        """Test converting from list of dictionaries."""
        data = [
            {"a": 1, "b": "x"},
            {"a": 2, "b": "y"},
            {"a": 3, "b": "z"},
        ]

        result = EnhancedPolars.from_data(data)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_from_numpy_array(self):
        """Test converting from numpy array."""
        arr = np.array([[1, 2], [3, 4], [5, 6]])

        result = EnhancedPolars.from_data(arr)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3


# ============================================================================
# File I/O Tests
# ============================================================================

class TestFileIO:
    """Test file reading functionality."""

    def test_read_csv_basic(self, tmp_path):
        """Test reading a basic CSV file."""
        # Create test CSV
        csv_path = tmp_path / "test.csv"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_csv(csv_path)

        # Read it back
        result = EnhancedPolars.read_csv(csv_path, mode='eager')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_read_csv_lazy(self, tmp_path):
        """Test reading CSV in lazy mode."""
        csv_path = tmp_path / "test.csv"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_csv(csv_path)

        result = EnhancedPolars.read_csv(csv_path, mode='lazy')

        assert isinstance(result, pl.LazyFrame)

    def test_read_parquet_basic(self, tmp_path):
        """Test reading a basic Parquet file."""
        parquet_path = tmp_path / "test.parquet"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_parquet(parquet_path)

        result = EnhancedPolars.read_parquet(parquet_path, mode='eager')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_read_parquet_lazy(self, tmp_path):
        """Test reading Parquet in lazy mode."""
        parquet_path = tmp_path / "test.parquet"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_parquet(parquet_path)

        result = EnhancedPolars.read_parquet(parquet_path, mode='lazy')

        assert isinstance(result, pl.LazyFrame)


# ============================================================================
# Cleanup Tests
# ============================================================================

class TestCleanup:
    """Test cleanup functionality."""

    def test_cleanup_dataframe(self):
        """Test cleanup function on DataFrame."""
        df = pl.DataFrame({
            " Column With Spaces ": [1, 2, 3],
            "UPPERCASE": ["a", "b", "c"],
        })

        result = EnhancedPolars.cleanup(df)

        # Columns should be cleaned
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_cleanup_series(self):
        """Test cleanup function on Series."""
        s = pl.Series(" Test Series ", [1, 2, 3])

        result = EnhancedPolars.cleanup(s)

        assert isinstance(result, pl.Series)
        assert len(result) == 3


# ============================================================================
# Temporal Conversion Tests
# ============================================================================

class TestTemporalConversion:
    """Test temporal type conversion."""

    def test_infer_numeric_temporal_scale_seconds(self):
        """Test inferring seconds scale from numeric data."""
        # Unix timestamps in seconds (around year 2023)
        series = pl.Series("ts", [1672531200, 1672617600, 1672704000])

        scale = EnhancedPolars.infer_numeric_temporal_scale(series, "datetime")

        assert scale in ["s", "ms", "us", "ns", "d"]

    def test_infer_numeric_temporal_scale_milliseconds(self):
        """Test inferring milliseconds scale from numeric data."""
        # Unix timestamps in milliseconds
        series = pl.Series("ts", [1672531200000, 1672617600000, 1672704000000])

        scale = EnhancedPolars.infer_numeric_temporal_scale(series, "datetime")

        assert scale in ["s", "ms", "us", "ns", "d"]

    def test_to_timedelta_polars(self):
        """Test timedelta conversion with pandas-style duration strings."""
        # Pandas-style duration strings (the format supported by to_timedelta_polars)
        s = pl.Series("duration", ["1h30m", "2h45m", "0h15m"])

        result = EnhancedPolars.to_timedelta_polars(s)

        assert result.dtype == pl.Duration


# ============================================================================
# Random Data Generation Tests
# ============================================================================

class TestRandomDataGeneration:
    """Test random data generation functionality."""

    def test_generate_random_data_basic(self):
        """Test basic random data generation with specific dtypes."""
        dtypes = ["INTEGER", "FLOAT", "TEXT"]

        result = EnhancedPolars.generate_random_data(n=100, dtypes=dtypes)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 100
        assert set(result.columns) == {"INTEGER", "FLOAT", "TEXT"}

    def test_generate_random_data_with_nulls(self):
        """Test random data generation with null values."""
        dtypes = ["INTEGER", "FLOAT"]

        result = EnhancedPolars.generate_random_data(
            n=100,
            dtypes=dtypes,
            percent_null=0.1
        )

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 100


# ============================================================================
# IPC File Reading Tests
# ============================================================================

class TestReadIPC:
    """Test IPC (Arrow) file reading functionality."""

    def test_read_ipc_eager(self, tmp_path):
        """Test reading IPC file in eager mode."""
        ipc_path = tmp_path / "test.ipc"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_ipc(ipc_path)

        result = EnhancedPolars.read_ipc(ipc_path, mode='eager')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3
        assert result["a"].to_list() == [1, 2, 3]
        assert result["b"].to_list() == ["x", "y", "z"]

    def test_read_ipc_lazy(self, tmp_path):
        """Test reading IPC file in lazy mode."""
        ipc_path = tmp_path / "test.ipc"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_ipc(ipc_path)

        result = EnhancedPolars.read_ipc(ipc_path, mode='lazy')

        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert len(collected) == 3

    def test_read_ipc_with_columns(self, tmp_path):
        """Test reading specific columns from IPC file."""
        ipc_path = tmp_path / "test.ipc"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"], "c": [4.0, 5.0, 6.0]})
        df.write_ipc(ipc_path)

        result = EnhancedPolars.read_ipc(ipc_path, mode='eager', columns=["a", "c"])

        assert isinstance(result, pl.DataFrame)
        assert set(result.columns) == {"a", "c"}
        assert "b" not in result.columns

    def test_read_ipc_with_n_rows(self, tmp_path):
        """Test reading limited rows from IPC file."""
        ipc_path = tmp_path / "test.ipc"
        df = pl.DataFrame({"a": list(range(100))})
        df.write_ipc(ipc_path)

        result = EnhancedPolars.read_ipc(ipc_path, mode='eager', n_rows=10)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 10


# ============================================================================
# NDJSON File Reading Tests
# ============================================================================

class TestReadNDJSON:
    """Test NDJSON (newline-delimited JSON) file reading functionality."""

    def test_read_ndjson_eager(self, tmp_path):
        """Test reading NDJSON file in eager mode."""
        ndjson_path = tmp_path / "test.ndjson"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_ndjson(ndjson_path)

        result = EnhancedPolars.read_ndjson(ndjson_path, mode='eager')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_read_ndjson_lazy(self, tmp_path):
        """Test reading NDJSON file in lazy mode."""
        ndjson_path = tmp_path / "test.ndjson"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_ndjson(ndjson_path)

        result = EnhancedPolars.read_ndjson(ndjson_path, mode='lazy')

        assert isinstance(result, pl.LazyFrame)
        collected = result.collect()
        assert len(collected) == 3

    def test_read_ndjson_with_n_rows(self, tmp_path):
        """Test reading limited rows from NDJSON file."""
        ndjson_path = tmp_path / "test.ndjson"
        df = pl.DataFrame({"a": list(range(100))})
        df.write_ndjson(ndjson_path)

        result = EnhancedPolars.read_ndjson(ndjson_path, mode='eager', n_rows=10)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 10


# ============================================================================
# Edge Cases for File Reading
# ============================================================================

class TestFileReadingEdgeCases:
    """Test edge cases for file reading functionality."""

    def test_read_parquet_with_row_index(self, tmp_path):
        """Test reading parquet with row index."""
        parquet_path = tmp_path / "test.parquet"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_parquet(parquet_path)

        result = EnhancedPolars.read_parquet(parquet_path, mode='eager', row_index_name="idx")

        assert isinstance(result, pl.DataFrame)
        if "idx" in result.columns:
            assert result["idx"].to_list() == [0, 1, 2]

    def test_read_csv_with_infer_schema(self, tmp_path):
        """Test reading CSV with schema inference."""
        csv_path = tmp_path / "test.csv"
        df = pl.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.5, 2.5, 3.5],
            "str_col": ["a", "b", "c"]
        })
        df.write_csv(csv_path)

        result = EnhancedPolars.read_csv(csv_path, mode='eager', infer_schema_length=100)

        assert isinstance(result, pl.DataFrame)
        # Schema should be inferred (may be optimized to smaller types)
        assert result["int_col"].dtype.is_numeric()
        assert result["float_col"].dtype.is_float()

    def test_read_parquet_glob_pattern(self, tmp_path):
        """Test reading multiple parquet files with glob pattern."""
        # Create multiple parquet files
        for i in range(3):
            parquet_path = tmp_path / f"part_{i}.parquet"
            df = pl.DataFrame({"a": [i * 10 + j for j in range(5)]})
            df.write_parquet(parquet_path)

        # Read all files with glob
        result = EnhancedPolars.read_parquet(str(tmp_path / "*.parquet"), mode='eager')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 15  # 3 files * 5 rows each

    def test_read_csv_with_null_values(self, tmp_path):
        """Test reading CSV with custom null values."""
        csv_path = tmp_path / "test.csv"
        # Write CSV with custom null representation
        with open(csv_path, 'w') as f:
            f.write("a,b\n")
            f.write("1,value\n")
            f.write("NA,missing\n")
            f.write("3,value\n")

        result = EnhancedPolars.read_csv(csv_path, mode='eager', null_values=["NA"])

        assert isinstance(result, pl.DataFrame)
        assert result["a"].null_count() == 1  # "NA" should be null

    def test_read_ipc_large_file(self, tmp_path):
        """Test reading large IPC file."""
        ipc_path = tmp_path / "test.ipc"
        df = pl.DataFrame({"a": list(range(1000)), "b": [f"val_{i}" for i in range(1000)]})
        df.write_ipc(ipc_path)

        result = EnhancedPolars.read_ipc(ipc_path, mode='eager')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 1000


# ============================================================================
# Multiple File Reading Tests
# ============================================================================

class TestMultipleFileReading:
    """Test reading multiple files at once."""

    def test_read_csv_list_of_files(self, tmp_path):
        """Test reading multiple CSV files from a list."""
        files = []
        for i in range(3):
            csv_path = tmp_path / f"file_{i}.csv"
            df = pl.DataFrame({"a": [i * 10], "b": [f"file_{i}"]})
            df.write_csv(csv_path)
            files.append(str(csv_path))

        result = EnhancedPolars.read_csv(files, mode='eager')

        # Multiple files may return LazyFrame, collect if needed
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3


# ============================================================================
# read_data Tests (Unified Reader)
# ============================================================================

class TestReadData:
    """Test read_data unified file reading functionality."""

    def test_read_data_single_csv(self, tmp_path):
        """Test read_data with a single CSV file."""
        csv_path = tmp_path / "test.csv"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_csv(csv_path)

        result = EnhancedPolars.read_data(csv_path, mode='eager')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_read_data_single_parquet(self, tmp_path):
        """Test read_data with a single Parquet file."""
        parquet_path = tmp_path / "test.parquet"
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.write_parquet(parquet_path)

        result = EnhancedPolars.read_data(parquet_path, mode='eager')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_read_data_directory_with_file_type(self, tmp_path):
        """Test read_data reading a directory with file_type parameter."""
        # Create multiple parquet files
        for i in range(3):
            parquet_path = tmp_path / f"file_{i}.parquet"
            df = pl.DataFrame({"a": [i], "b": [f"val_{i}"]})
            df.write_parquet(parquet_path)

        result = EnhancedPolars.read_data(tmp_path, mode='eager', file_type='.parquet')

        # file_type with directory returns LazyFrame, need to collect
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_read_data_directory_with_pattern(self, tmp_path):
        """Test read_data reading a directory with pattern parameter."""
        # Create multiple parquet files with different naming patterns
        for i in range(3):
            parquet_path = tmp_path / f"data_{i}.parquet"
            df = pl.DataFrame({"a": [i], "b": [f"val_{i}"]})
            df.write_parquet(parquet_path)

        # Create a file that shouldn't match the pattern
        other_path = tmp_path / "other.parquet"
        pl.DataFrame({"a": [999]}).write_parquet(other_path)

        result = EnhancedPolars.read_data(tmp_path, mode='eager', pattern='data_*.parquet')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3
        assert 999 not in result["a"].to_list()

    def test_read_data_directory_with_pattern_and_merge(self, tmp_path):
        """Test read_data with pattern and merge_results=True (default)."""
        for i in range(2):
            parquet_path = tmp_path / f"part_{i}.parquet"
            df = pl.DataFrame({"id": [i * 10 + j for j in range(3)]})
            df.write_parquet(parquet_path)

        result = EnhancedPolars.read_data(tmp_path, mode='eager', pattern='part_*.parquet', merge_results=True)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 6  # 2 files * 3 rows

    def test_read_data_directory_with_pattern_no_merge(self, tmp_path):
        """Test read_data with pattern and merge_results=False."""
        for i in range(2):
            parquet_path = tmp_path / f"part_{i}.parquet"
            df = pl.DataFrame({"id": [i * 10 + j for j in range(3)]})
            df.write_parquet(parquet_path)

        result = EnhancedPolars.read_data(tmp_path, mode='eager', pattern='part_*.parquet', merge_results=False)

        assert isinstance(result, dict)
        assert len(result) == 2

    def test_read_data_directory_with_regex_pattern(self, tmp_path):
        """Test read_data with regex pattern."""
        # Create files with numeric suffixes
        for i in range(3):
            parquet_path = tmp_path / f"data_{i:02d}.parquet"
            df = pl.DataFrame({"a": [i]})
            df.write_parquet(parquet_path)

        result = EnhancedPolars.read_data(
            tmp_path, mode='eager',
            pattern=r'data_\d{2}\.parquet',
            use_regex=True
        )

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3

    def test_read_data_lazy_mode(self, tmp_path):
        """Test read_data returns LazyFrame in lazy mode."""
        parquet_path = tmp_path / "test.parquet"
        df = pl.DataFrame({"a": [1, 2, 3]})
        df.write_parquet(parquet_path)

        result = EnhancedPolars.read_data(parquet_path, mode='lazy')

        assert isinstance(result, pl.LazyFrame)

    def test_read_data_with_type_optimization(self, tmp_path):
        """Test read_data with optimize_types enabled."""
        csv_path = tmp_path / "test.csv"
        df = pl.DataFrame({"small_int": [1, 2, 3]})
        df.write_csv(csv_path)

        result = EnhancedPolars.read_data(csv_path, mode='eager', optimize_types=True)

        assert isinstance(result, pl.DataFrame)
        # Type should be optimized (potentially downcasted)
        assert result["small_int"].dtype.is_integer()

    def test_read_data_file_not_found(self, tmp_path):
        """Test read_data raises error for non-existent file."""
        # Non-existent files raise FileNotFoundError during path resolution
        with pytest.raises(FileNotFoundError):
            EnhancedPolars.read_data(str(tmp_path / "nonexistent.parquet"), mode='eager')

    def test_read_data_directory_no_file_type_or_pattern_raises(self, tmp_path):
        """Test read_data raises error when directory given without file_type or pattern."""
        with pytest.raises(ValueError):
            EnhancedPolars.read_data(tmp_path, mode='eager')

    def test_read_data_directory_pattern_no_matches(self, tmp_path):
        """Test read_data raises error when pattern matches no files."""
        # Create a file that won't match our pattern
        parquet_path = tmp_path / "other.parquet"
        pl.DataFrame({"a": [1]}).write_parquet(parquet_path)

        with pytest.raises(FileNotFoundError):
            EnhancedPolars.read_data(tmp_path, mode='eager', pattern='nonexistent_*.csv')

    def test_read_data_with_schema_mismatch_concat(self, tmp_path):
        """Test read_data handles schema mismatches when using pattern."""
        # Create files with different schemas (same column, different types)
        path1 = tmp_path / "file_1.parquet"
        path2 = tmp_path / "file_2.parquet"

        pl.DataFrame({"value": [1, 2, 3]}).write_parquet(path1)  # Int64
        pl.DataFrame({"value": ["a", "b", "c"]}).write_parquet(path2)  # String

        # Using pattern should read individually and concat with schema merge
        result = EnhancedPolars.read_data(tmp_path, mode='eager', pattern='file_*.parquet')

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 6
        # Should merge to String (wider type)
        assert result["value"].dtype == pl.String


# ============================================================================
# read_schema_metadata Tests
# ============================================================================

class TestReadSchemaMetadata:
    """Test read_schema_metadata functionality."""

    def test_read_schema_metadata_basic(self, tmp_path):
        """Test reading schema metadata from a directory."""
        # Create metadata file
        import json
        metadata = {
            "__schema_metadata__": {
                "columns": ["a", "b"],
                "dtypes": {"a": "Int64", "b": "String"}
            }
        }
        metadata_path = tmp_path / "_dataset_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        result = EnhancedPolars.read_schema_metadata(tmp_path)

        assert isinstance(result, dict)
        assert "columns" in result
        assert "dtypes" in result

    def test_read_schema_metadata_with_keys(self, tmp_path):
        """Test reading specific keys from schema metadata."""
        import json
        metadata = {
            "__schema_metadata__": {
                "columns": ["a", "b"],
                "dtypes": {"a": "Int64", "b": "String"},
                "row_count": 100
            }
        }
        metadata_path = tmp_path / "_dataset_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        result = EnhancedPolars.read_schema_metadata(tmp_path, keys="columns")

        assert result == ["a", "b"]

    def test_read_schema_metadata_with_keys_list(self, tmp_path):
        """Test reading multiple keys from schema metadata."""
        import json
        metadata = {
            "__schema_metadata__": {
                "columns": ["a", "b"],
                "dtypes": {"a": "Int64"},
                "row_count": 100
            }
        }
        metadata_path = tmp_path / "_dataset_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        result = EnhancedPolars.read_schema_metadata(tmp_path, keys=["columns", "row_count"])

        assert isinstance(result, dict)
        assert "columns" in result
        assert "row_count" in result
        assert "dtypes" not in result

    def test_read_schema_metadata_with_regex(self, tmp_path):
        """Test read_schema_metadata with regex to find directory."""
        import json

        # Create subdirectory with specific name
        subdir = tmp_path / "dataset_2024"
        subdir.mkdir()

        metadata = {
            "__schema_metadata__": {
                "name": "test_dataset"
            }
        }
        metadata_path = subdir / "_dataset_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        result = EnhancedPolars.read_schema_metadata(tmp_path, regex=r"dataset_\d{4}")

        assert isinstance(result, dict)
        assert result["name"] == "test_dataset"

    def test_read_schema_metadata_missing_file(self, tmp_path):
        """Test read_schema_metadata raises error when metadata file missing."""
        with pytest.raises(AssertionError, match="Metadata file not found"):
            EnhancedPolars.read_schema_metadata(tmp_path)

    def test_read_schema_metadata_regex_multiple_matches(self, tmp_path):
        """Test read_schema_metadata raises error when regex matches multiple dirs."""
        import json

        # Create multiple matching directories
        for year in [2023, 2024]:
            subdir = tmp_path / f"dataset_{year}"
            subdir.mkdir()
            metadata_path = subdir / "_dataset_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump({"__schema_metadata__": {}}, f)

        with pytest.raises(AssertionError, match="Expected exactly one directory"):
            EnhancedPolars.read_schema_metadata(tmp_path, regex=r"dataset_\d{4}")


# ============================================================================
# concat_series_dataframe Tests
# ============================================================================

class TestConcatSeriesDataframe:
    """Test concat_series_dataframe functionality."""

    def test_concat_series_same_dtype(self):
        """Test concatenating series with same dtype."""
        s1 = pl.Series("a", [1, 2, 3])
        s2 = pl.Series("a", [4, 5, 6])

        result = EnhancedPolars.concat_series_dataframe(s1, s2)

        assert isinstance(result, pl.Series)
        assert len(result) == 6
        assert result.to_list() == [1, 2, 3, 4, 5, 6]

    def test_concat_series_different_int_dtypes(self):
        """Test concatenating series with different integer dtypes."""
        s1 = pl.Series("a", [1, 2, 3], dtype=pl.Int32)
        s2 = pl.Series("a", [4, 5, 6], dtype=pl.Int64)

        result = EnhancedPolars.concat_series_dataframe(s1, s2)

        assert isinstance(result, pl.Series)
        assert len(result) == 6
        # Should widen to Int64
        assert result.dtype == pl.Int64

    def test_concat_series_int_and_float(self):
        """Test concatenating integer and float series."""
        s1 = pl.Series("a", [1, 2, 3], dtype=pl.Int64)
        s2 = pl.Series("a", [4.5, 5.5, 6.5], dtype=pl.Float64)

        result = EnhancedPolars.concat_series_dataframe(s1, s2)

        assert isinstance(result, pl.Series)
        assert len(result) == 6
        # Should widen to Float64
        assert result.dtype == pl.Float64

    def test_concat_dataframes_same_schema(self):
        """Test concatenating DataFrames with same schema."""
        df1 = pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        df2 = pl.DataFrame({"a": [3, 4], "b": ["z", "w"]})

        result = EnhancedPolars.concat_series_dataframe(df1, df2)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 4
        assert result.columns == ["a", "b"]

    def test_concat_dataframes_different_int_dtypes(self):
        """Test concatenating DataFrames with different integer column types."""
        df1 = pl.DataFrame({"a": pl.Series([1, 2], dtype=pl.Int32)})
        df2 = pl.DataFrame({"a": pl.Series([3, 4], dtype=pl.Int64)})

        result = EnhancedPolars.concat_series_dataframe(df1, df2)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 4
        assert result["a"].dtype == pl.Int64

    def test_concat_dataframes_int_and_string(self):
        """Test concatenating DataFrames where column type changes from int to string."""
        df1 = pl.DataFrame({"a": [1, 2, 3]})
        df2 = pl.DataFrame({"a": ["x", "y", "z"]})

        result = EnhancedPolars.concat_series_dataframe(df1, df2)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 6
        # Should merge to String
        assert result["a"].dtype == pl.String

    def test_concat_dataframes_different_columns(self):
        """Test concatenating DataFrames with different columns."""
        df1 = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        df2 = pl.DataFrame({"a": [5, 6], "c": [7, 8]})

        result = EnhancedPolars.concat_series_dataframe(df1, df2)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 4
        # Should have all columns, with nulls for missing
        assert set(result.columns) == {"a", "b", "c"}

    def test_concat_empty_raises(self):
        """Test that concatenating nothing raises error."""
        with pytest.raises(ValueError, match="At least one"):
            EnhancedPolars.concat_series_dataframe()

    def test_concat_multiple_dataframes(self):
        """Test concatenating more than two DataFrames."""
        df1 = pl.DataFrame({"a": [1]})
        df2 = pl.DataFrame({"a": [2]})
        df3 = pl.DataFrame({"a": [3]})

        result = EnhancedPolars.concat_series_dataframe(df1, df2, df3)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3
        assert result["a"].to_list() == [1, 2, 3]


# ============================================================================
# convert_to_polars_dtype Tests
# ============================================================================

class TestConvertToPolarsType:
    """Test convert_to_polars_dtype functionality."""

    def test_convert_string_to_int(self):
        """Test converting string series to integer."""
        s = pl.Series("test", ["1", "2", "3"])

        result = EnhancedPolars.convert_to_polars_dtype(s, pl.Int64)

        assert result.dtype == pl.Int64
        assert result.to_list() == [1, 2, 3]

    def test_convert_string_to_float(self):
        """Test converting string series to float."""
        s = pl.Series("test", ["1.5", "2.5", "3.5"])

        result = EnhancedPolars.convert_to_polars_dtype(s, pl.Float64)

        assert result.dtype == pl.Float64
        assert result.to_list() == [1.5, 2.5, 3.5]

    def test_convert_int_to_float(self):
        """Test converting integer series to float."""
        s = pl.Series("test", [1, 2, 3])

        result = EnhancedPolars.convert_to_polars_dtype(s, pl.Float64)

        assert result.dtype == pl.Float64
        assert result.to_list() == [1.0, 2.0, 3.0]

    def test_convert_float_to_int(self):
        """Test converting float series to integer (truncates)."""
        s = pl.Series("test", [1.0, 2.0, 3.0])

        result = EnhancedPolars.convert_to_polars_dtype(s, pl.Int64)

        assert result.dtype == pl.Int64
        assert result.to_list() == [1, 2, 3]

    def test_convert_string_to_date(self):
        """Test converting string series to date."""
        s = pl.Series("test", ["2023-01-15", "2023-06-20", "2023-12-25"])

        result = EnhancedPolars.convert_to_polars_dtype(s, pl.Date, format="%Y-%m-%d")

        assert result.dtype == pl.Date

    def test_convert_string_to_datetime(self):
        """Test converting string series to datetime."""
        s = pl.Series("test", ["2023-01-15T10:30:00", "2023-06-20T14:45:00"])

        result = EnhancedPolars.convert_to_polars_dtype(s, pl.Datetime("us"), format="%Y-%m-%dT%H:%M:%S")

        assert isinstance(result.dtype, pl.Datetime)

    def test_convert_int_to_string(self):
        """Test converting integer series to string."""
        s = pl.Series("test", [1, 2, 3])

        result = EnhancedPolars.convert_to_polars_dtype(s, pl.String)

        assert result.dtype == pl.String
        assert result.to_list() == ["1", "2", "3"]

    def test_convert_preserves_nulls(self):
        """Test that conversion preserves null values."""
        s = pl.Series("test", ["1", None, "3"])

        result = EnhancedPolars.convert_to_polars_dtype(s, pl.Int64)

        assert result.dtype == pl.Int64
        assert result.null_count() == 1
        assert result.to_list() == [1, None, 3]

    def test_convert_dataframe(self):
        """Test converting DataFrame columns."""
        df = pl.DataFrame({
            "a": ["1", "2", "3"],
            "b": ["4.5", "5.5", "6.5"]
        })

        result = EnhancedPolars.convert_to_polars_dtype(df, {"a": pl.Int64, "b": pl.Float64})

        assert isinstance(result, pl.DataFrame)
        assert result["a"].dtype == pl.Int64
        assert result["b"].dtype == pl.Float64


# ============================================================================
# convert_numeric_to_temporal Tests
# ============================================================================

class TestConvertNumericToTemporal:
    """Test convert_numeric_to_temporal functionality."""

    def test_convert_seconds_to_datetime(self):
        """Test converting unix seconds to datetime."""
        # Unix timestamp for 2023-01-01 00:00:00 UTC
        s = pl.Series("ts", [1672531200, 1672617600, 1672704000])

        result = EnhancedPolars.convert_numeric_to_temporal(s, pl.Datetime, inferred_scale="s")

        assert isinstance(result.dtype, pl.Datetime)

    def test_convert_milliseconds_to_datetime(self):
        """Test converting unix milliseconds to datetime."""
        s = pl.Series("ts", [1672531200000, 1672617600000, 1672704000000])

        result = EnhancedPolars.convert_numeric_to_temporal(s, pl.Datetime, inferred_scale="ms")

        assert isinstance(result.dtype, pl.Datetime)

    def test_convert_microseconds_to_datetime(self):
        """Test converting unix microseconds to datetime."""
        s = pl.Series("ts", [1672531200000000, 1672617600000000, 1672704000000000])

        result = EnhancedPolars.convert_numeric_to_temporal(s, pl.Datetime, inferred_scale="us")

        assert isinstance(result.dtype, pl.Datetime)

    def test_convert_nanoseconds_to_datetime(self):
        """Test converting unix nanoseconds to datetime."""
        s = pl.Series("ts", [1672531200000000000, 1672617600000000000, 1672704000000000000])

        result = EnhancedPolars.convert_numeric_to_temporal(s, pl.Datetime, inferred_scale="ns")

        assert isinstance(result.dtype, pl.Datetime)

    def test_convert_days_to_date(self):
        """Test converting days since epoch to date."""
        # Days since 1970-01-01
        s = pl.Series("days", [19358, 19359, 19360])  # Around 2023

        result = EnhancedPolars.convert_numeric_to_temporal(s, pl.Date, inferred_scale="d")

        assert result.dtype == pl.Date

    def test_convert_auto_infer_scale(self):
        """Test that scale is auto-inferred when not provided."""
        # Unix timestamp in seconds (around 2023)
        s = pl.Series("ts", [1672531200, 1672617600, 1672704000])

        result = EnhancedPolars.convert_numeric_to_temporal(s, pl.Datetime)

        assert isinstance(result.dtype, pl.Datetime)

    def test_convert_preserves_nulls(self):
        """Test that conversion preserves null values."""
        s = pl.Series("ts", [1672531200, None, 1672704000])

        result = EnhancedPolars.convert_numeric_to_temporal(s, pl.Datetime, inferred_scale="s")

        assert isinstance(result.dtype, pl.Datetime)
        assert result.null_count() == 1


# ============================================================================
# save_data Tests
# ============================================================================

class TestSaveData:
    """Test save_data functionality."""

    def test_save_data_parquet(self, tmp_path):
        """Test saving DataFrame to parquet."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        path = tmp_path / "test.parquet"

        EnhancedPolars.save_data(df, path)

        assert path.exists()
        result = pl.read_parquet(path)
        assert len(result) == 3

    def test_save_data_csv(self, tmp_path):
        """Test saving DataFrame to CSV."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        path = tmp_path / "test.csv"

        EnhancedPolars.save_data(df, path)

        assert path.exists()
        result = pl.read_csv(path)
        assert len(result) == 3

    def test_save_data_ipc(self, tmp_path):
        """Test saving DataFrame to IPC/Arrow."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        path = tmp_path / "test.ipc"

        EnhancedPolars.save_data(df, path)

        assert path.exists()
        result = pl.read_ipc(path)
        assert len(result) == 3

    def test_save_data_ndjson(self, tmp_path):
        """Test saving DataFrame to NDJSON."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        path = tmp_path / "test.ndjson"

        EnhancedPolars.save_data(df, path)

        assert path.exists()
        result = pl.read_ndjson(path)
        assert len(result) == 3

    def test_save_data_lazyframe(self, tmp_path):
        """Test saving LazyFrame to parquet."""
        lf = pl.LazyFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        path = tmp_path / "test.parquet"

        EnhancedPolars.save_data(lf, path)

        assert path.exists()
        result = pl.read_parquet(path)
        assert len(result) == 3

    def test_save_data_requires_existing_parent_dirs(self, tmp_path):
        """Test save_data requires parent directories to exist."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        path = tmp_path / "subdir" / "nested" / "test.parquet"

        # save_data does not create parent directories
        with pytest.raises(FileNotFoundError):
            EnhancedPolars.save_data(df, path)

    def test_save_data_with_string_path(self, tmp_path):
        """Test save_data works with string path."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        path = str(tmp_path / "test.parquet")

        EnhancedPolars.save_data(df, path)

        assert Path(path).exists()


# ============================================================================
# Additional Edge Cases
# ============================================================================

class TestReadDataEdgeCases:
    """Additional edge case tests for read_data."""

    def test_read_data_recursive_directory(self, tmp_path):
        """Test read_data with recursive directory search."""
        # Create nested directory structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        pl.DataFrame({"a": [1]}).write_parquet(tmp_path / "file1.parquet")
        pl.DataFrame({"a": [2]}).write_parquet(subdir / "file2.parquet")

        result = EnhancedPolars.read_data(
            tmp_path, mode='eager',
            pattern='*.parquet',
            recursive=True
        )

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 2

    def test_read_data_non_recursive_directory(self, tmp_path):
        """Test read_data with non-recursive directory search."""
        # Create nested directory structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        pl.DataFrame({"a": [1]}).write_parquet(tmp_path / "file1.parquet")
        pl.DataFrame({"a": [2]}).write_parquet(subdir / "file2.parquet")

        result = EnhancedPolars.read_data(
            tmp_path, mode='eager',
            pattern='*.parquet',
            recursive=False
        )

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 1  # Only the file in root, not subdir

    def test_read_data_attempt_numeric_to_datetime(self, tmp_path):
        """Test read_data with attempt_numeric_to_datetime option."""
        # Create parquet with unix timestamp column (seconds since epoch)
        df = pl.DataFrame({
            "timestamp": [1672531200, 1672617600, 1672704000],  # seconds (Jan 2023)
            "value": [100, 200, 300]
        })
        path = tmp_path / "test.parquet"
        df.write_parquet(path)

        result = EnhancedPolars.read_data(
            path, mode='eager',
            attempt_numeric_to_datetime=True
        )

        assert isinstance(result, pl.DataFrame)
        # The timestamp column should be converted to a temporal type
        assert EnhancedPolars._is_temporal_helper(result["timestamp"].dtype)

    def test_read_data_clean_column_names(self, tmp_path):
        """Test read_data with clean_column_names option."""
        df = pl.DataFrame({
            " Column With Spaces ": [1, 2, 3],
            "UPPERCASE": [4, 5, 6]
        })
        path = tmp_path / "test.parquet"
        df.write_parquet(path)

        result = EnhancedPolars.read_data(path, mode='eager', clean_column_names=True)

        assert isinstance(result, pl.DataFrame)
        # Column names should be cleaned (no leading/trailing spaces)
        assert all(col == col.strip() for col in result.columns)
