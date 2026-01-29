# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.0.4]

### Fixed

- **`train_test_val_split` stratification cohort naming**: Fixed a bug where stratification
  column VALUES were included in cohort names, causing many unique cohorts (one per stratum
  with different date ranges). Now only the column NAMES are included in the cohort name
  (e.g., `Development_stratified_by_category` instead of `Development_A_2023-01-01_2023-06-15`),
  resulting in exactly 3 cohorts (Development, Validation, Test) regardless of stratification.

- **`read_data` with `merge_results=False`**: Fixed a bug where `cleanup()` was called on
  dict results, causing an AttributeError. Now properly applies cleanup to each DataFrame
  in the dict when `merge_results=False`.

- **`convert_to_polars_dtype` Date/Datetime ordering**: Fixed a bug where Datetime types
  were incorrectly converted to Date because the string "Datetime" starts with "Date",
  matching the Date branch first. Reordered checks so Datetime is checked before Date.

- **`read_schema_metadata` find_files API**: Updated to use correct CoreUtilities `find_files`
  API parameters (`use_regex=True`, `return_matching='directories'` instead of deprecated
  `pattern_type='regex'`, `mode='directory'`).

- **SQL test fixtures not skipping unavailable databases**: Fixed `create_connection` in
  conftest.py to properly return `None` when database connections fail. Previously,
  `conn.connect()` didn't raise exceptions when drivers were missing, causing tests to
  fail instead of skip. Now validates `conn.is_connected` after connection attempt and
  checks for missing host/database config early.

### Added

- Comprehensive unit tests for previously untested functions:
  - `read_data` with directories, patterns, and schema mismatch handling
  - `read_schema_metadata` with regex directory matching
  - `concat_series_dataframe` with schema merging
  - `convert_to_polars_dtype` type conversions
  - `convert_numeric_to_temporal` timestamp conversions
  - `save_data` file writing
  - `train_test_val_split` stratification cohort name regression tests

### Changed

- Updated `train_test_val_split` docstring with complete parameter documentation and
  notes about cohort naming behavior with stratification.
