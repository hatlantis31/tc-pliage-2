import json
import unittest
import os
import logging
import zipfile
import numpy as np
import pandas as pd
from pathlib import Path
from importlib import import_module
from typing import Tuple, List, Dict, Union
import warnings
from main_app_files.function_files._sharepoint_handling import SharePointHandler
import shutil

# Constants
SUPPORTED_ENCODINGS = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
FILE_TYPES = {
    'input': '_input',
    'single': '_expected_single_file',
    'joined': '_expected_joined_file'
}
EXPECTED_FILE_EXTENSIONS = ['.xlsx', '.csv']

# Set up logging

# Clear any existing handlers
root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)  # Set level specifically for this logger


class FileReader:
    """
    Utility class for file operations.

    This class provides methods to read different types of files (CSV, Excel) with various
    encodings and converts them to pandas DataFrames for testing parser functionality.
    """

    @staticmethod
    def read_with_encoding(file_path: Path) -> pd.DataFrame:
        """
        Try reading file with different encodings.

        Parameters:
            file_path (Path): Path to the file to be read

        Returns:
            pd.DataFrame: DataFrame containing the file contents

        Raises:
            UnicodeDecodeError: If file cannot be read with any supported encoding
        """
        for encoding in SUPPORTED_ENCODINGS:
            try:
                a = pd.read_csv(file_path, encoding=encoding)
                return a
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError(f"Unable to read {file_path} with any supported encoding")

    @staticmethod
    def read_file(file_path: Path, is_input_file: bool = False) -> Union[str, pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        Universal file reading method that handles different file types.

        Parameters:
            file_path (Path): Path to the file to be read
            is_input_file (bool): If True, return path as string for parser; otherwise read file content

        Returns:
            Union[str, pd.DataFrame, Dict[str, pd.DataFrame]]:
                - String path if is_input_file is True
                - DataFrame if single sheet/CSV
                - Dict of DataFrames if multi-sheet Excel

        Notes:
            - For Excel files with multiple sheets, returns a dictionary with sheet names as keys
            - For CSV files or single-sheet Excel, returns a DataFrame
        """
        if is_input_file:
            return str(file_path).replace('\\', '/')

        if file_path.suffix == '.xlsx':
            try:
                with pd.ExcelFile(file_path) as excel_file:
                    if len(excel_file.sheet_names) > 1:
                        return {sheet: pd.read_excel(file_path, sheet_name=sheet)
                                for sheet in excel_file.sheet_names}
                    return pd.read_excel(file_path)
            finally:
                # Ensure Excel file is closed
                import gc
                gc.collect()

        return FileReader.read_with_encoding(file_path)


class DataFrameProcessor:
    """
    Utility class for DataFrame operations.

    This class provides methods to process, standardize, and compare DataFrames,
    ensuring consistent handling of various data types, missing values, and column names.
    It is essential for reliable comparison between parser outputs and expected results.
    """

    # Class constant for NULL integer value
    NULL_INT_VALUE = -9223372036854775808

    @staticmethod
    def process_dataframe(df: Union[pd.DataFrame, dict, str]) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        Convert input to DataFrame or dictionary of DataFrames.

        Parameters:
            df (Union[pd.DataFrame, dict, str]): Input data structure or file path

        Returns:
            Union[pd.DataFrame, Dict[str, pd.DataFrame]]: Processed DataFrame(s)

        Raises:
            TypeError: If input is not a DataFrame, dict, or file path

        Notes:
            Handles various input formats including:
            - pandas DataFrame
            - Dictionary of DataFrames
            - Nested dictionaries
            - File paths (Excel or CSV)
        """
        if isinstance(df, pd.DataFrame):
            return DataFrameProcessor._clean_dataframe(df)
        elif isinstance(df, dict):
            # Handle nested dictionaries (file_name: {sheet_name: df})
            if any(isinstance(v, dict) for v in df.values()):
                # Take the first nested dictionary if there's only one
                if len(df) == 1:
                    return {k: DataFrameProcessor._clean_dataframe(v)
                            for k, v in next(iter(df.values())).items()}
                # Otherwise process all nested dictionaries
                return {k: DataFrameProcessor._clean_dataframe(v)
                        for outer_dict in df.values()
                        for k, v in outer_dict.items()}
            # Handle direct dictionary of DataFrames
            elif all(isinstance(v, pd.DataFrame) for v in df.values()):
                return {k: DataFrameProcessor._clean_dataframe(v)
                        for k, v in df.items()}
            elif len(df) == 0:
                return pd.DataFrame()
            elif not any(isinstance(v, (list, np.ndarray, pd.Series))
                         for v in df.values()):
                return DataFrameProcessor._clean_dataframe(pd.DataFrame([df]))
            return DataFrameProcessor._clean_dataframe(pd.DataFrame(df))
        elif isinstance(df, str):
            if df.endswith('.xlsx'):
                excel_file = pd.ExcelFile(df)
                if len(excel_file.sheet_names) > 1:
                    return {sheet: DataFrameProcessor._clean_dataframe(
                        pd.read_excel(df, sheet_name=sheet))
                        for sheet in excel_file.sheet_names}
                return DataFrameProcessor._clean_dataframe(pd.read_excel(df))
            return DataFrameProcessor._clean_dataframe(pd.read_csv(df))
        raise TypeError(f"Input must be DataFrame, dict, or file path, got {type(df)}")

    @staticmethod
    def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean DataFrame by handling missing values consistently.

        Parameters:
            df (pd.DataFrame): Input DataFrame to clean

        Returns:
            pd.DataFrame: Cleaned DataFrame with standardized missing values

        Notes:
            - Replaces empty strings, 'NULL', 'None', etc. with NaN
            - Converts columns to numeric where possible
            - Handles special NULL integer values
        """
        # Create a copy to avoid modifying the original
        df = df.copy()

        # Replace empty strings with NaN
        df = df.replace(r'^\s*$', np.nan, regex=True)

        # Handle string columns with None values - more thorough approach
        for col in df.columns:
            # For object/string columns, handle 'None' more carefully
            if pd.api.types.is_object_dtype(df[col]):
                # Replace Python None objects with np.nan
                df[col] = df[col].replace([None], np.nan)
                # Replace string 'None' with np.nan (case insensitive)
                mask = df[col].astype(str).str.strip().str.lower() == 'none'
                df.loc[mask, col] = np.nan

        # Replace various forms of NULL/None with NaN (as strings)
        df = df.replace(['NULL', 'null', 'None', 'none', 'NONE', ' None '], np.nan)

        # Replace minimum integer value with NaN
        df = df.replace(DataFrameProcessor.NULL_INT_VALUE, np.nan)

        # Handle numeric columns
        for col in df.columns:
            try:
                # Regular numeric handling for other columns
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                if numeric_series.notna().any():  # If there are any valid numbers
                    df[col] = numeric_series
                    # Replace NULL_INT_VALUE with NaN again after conversion
                    df[col] = df[col].replace(DataFrameProcessor.NULL_INT_VALUE, np.nan)
            except:
                continue

        return df

    @staticmethod
    def _infer_datetime_format(series: pd.Series) -> str:
        """
        Infer the datetime format from a series of datetime strings.

        Parameters:
            series (pd.Series): Series containing datetime strings

        Returns:
            str: The most likely datetime format string

        Notes:
            Tests various common datetime formats and returns the first one that works
            for the sample values in the series.
        """
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y/%m/%d %H:%M:%S',
            '%d-%m-%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%H:%M:%S',
        ]

        sample_values = series.dropna().astype(str).unique()
        if len(sample_values) == 0:
            return formats[0]

        for fmt in formats:
            try:
                for val in sample_values[:3]:
                    pd.to_datetime(val, format=fmt)
                return fmt
            except (ValueError, TypeError):
                continue

        return formats[0]

    @staticmethod
    def standardize_column(series1: Union[pd.Series, pd.DataFrame],
                           series2: Union[pd.Series, pd.DataFrame]) -> Tuple[pd.Series, pd.Series]:
        """
        Standardize data types between two series for comparison.

        Parameters:
            series1, series2 (Union[pd.Series, pd.DataFrame]): Input series or DataFrames

        Returns:
            Tuple[pd.Series, pd.Series]: Standardized series with consistent data types

        Notes:
            Attempts to convert both series to the same data type in this order:
            1. Datetime (if strings contain date-like patterns)
            2. Numeric (if convertible to numbers)
            3. String (as fallback)
        """
        # Convert DataFrame to Series if necessary
        if isinstance(series1, pd.DataFrame):
            series1 = series1.iloc[:, 0] if len(series1.columns) > 0 else pd.Series()
        if isinstance(series2, pd.DataFrame):
            series2 = series2.iloc[:, 0] if len(series2.columns) > 0 else pd.Series()

        # Convert to Series
        series1 = pd.Series(series1)
        series2 = pd.Series(series2)

        # Handle NULL integer value
        series1 = series1.replace(DataFrameProcessor.NULL_INT_VALUE, np.nan)
        series2 = series2.replace(DataFrameProcessor.NULL_INT_VALUE, np.nan)

        # Handle empty strings
        series1 = series1.replace(r'^\s*$', np.nan, regex=True)
        series2 = series2.replace(r'^\s*$', np.nan, regex=True)

        # Try to convert nanosecond timestamps first
        try:
            if series1.dtype == np.int64 and series1.astype(str).str.len().max() > 15:
                series1 = pd.to_datetime(series1, unit='ns')
            if series2.dtype == np.int64 and series2.astype(str).str.len().max() > 15:
                series2 = pd.to_datetime(series2, unit='ns')
        except:
            pass

        # Try datetime conversion with format inference
        try:
            if (isinstance(series1.iloc[0], str) and
                    any(c in series1.iloc[0] for c in ':-/') or
                    isinstance(series2.iloc[0], str) and
                    any(c in series2.iloc[0] for c in ':-/')):
                format1 = DataFrameProcessor._infer_datetime_format(series1)
                format2 = DataFrameProcessor._infer_datetime_format(series2)
                datetime_format = format1 if len(format1) > len(format2) else format2

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    series1 = pd.to_datetime(series1, format=datetime_format, errors='coerce')
                    series2 = pd.to_datetime(series2, format=datetime_format, errors='coerce')
                return series1, series2
        except:
            pass

        # Try numeric conversion
        try:
            num1 = pd.to_numeric(series1, errors='coerce')
            num2 = pd.to_numeric(series2, errors='coerce')
            if not num1.isna().all() and not num2.isna().all():
                return num1, num2
        except:
            pass

        # Convert to string as last resort
        return (series1.astype(str).replace('nan', np.nan),
                series2.astype(str).replace('nan', np.nan))

    def _standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names by handling duplicates consistently.

        Parameters:
            df (pd.DataFrame): Input DataFrame

        Returns:
            pd.DataFrame: DataFrame with standardized column names

        Notes:
            - The first occurrence of a column name is kept as is
            - Subsequent occurrences are numbered (e.g., 'col', 'col.1', 'col.2')
            - Handles empty and unnamed columns
        """
        df = df.copy()
        seen_columns = {}  # Dictionary to keep track of column occurrences
        new_columns = []

        for i, col in enumerate(df.columns):
            # Handle empty and unnamed columns
            if col == '' or col.isspace() or col.startswith('Unnamed:'):
                base_name = f'Unnamed: {i}'
            else:
                base_name = col.split('.')[0]  # Remove any existing suffixes

            # If this is the first occurrence of the column name
            if base_name not in seen_columns:
                seen_columns[base_name] = 0
                new_name = base_name
            else:
                # Increment the counter for this column name
                seen_columns[base_name] += 1
                new_name = f"{base_name}.{seen_columns[base_name]}"

            new_columns.append(new_name)

        df.columns = new_columns
        return df

    def standardize_dataframes(self, df1: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
                               df2: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Standardize two dataframes or dictionaries of dataframes for comparison.
        """
        df1 = DataFrameProcessor.process_dataframe(df1)
        df2 = DataFrameProcessor.process_dataframe(df2)

        # Handle nested dictionary structures (like from join_tables)
        def extract_dataframe_from_nested_dict(data):
            if isinstance(data, dict):
                # If it's a nested dictionary, flatten it
                if any(isinstance(v, dict) for v in data.values()):
                    # This is a nested structure like {filename: {sheet: df, sheet2: df2}}
                    # Extract the inner dictionary
                    inner_dict = next(iter(data.values()))
                    if isinstance(inner_dict, dict):
                        # If there's only one sheet, return that DataFrame
                        if len(inner_dict) == 1:
                            return next(iter(inner_dict.values()))
                        # If multiple sheets, you might want to concatenate or select a specific one
                        # For now, let's take the first one
                        return next(iter(inner_dict.values()))
                else:
                    # This is a simple dictionary of DataFrames
                    if len(data) == 1:
                        return next(iter(data.values()))
                    # Multiple DataFrames - take the first one or concatenate
                    return next(iter(data.values()))
            return data

        # Extract DataFrames from nested structures
        df1 = extract_dataframe_from_nested_dict(df1)
        df2 = extract_dataframe_from_nested_dict(df2)

        # Now both should be DataFrames
        if not isinstance(df1, pd.DataFrame):
            raise TypeError(f"After extraction, df1 is not a DataFrame: {type(df1)}")
        if not isinstance(df2, pd.DataFrame):
            raise TypeError(f"After extraction, df2 is not a DataFrame: {type(df2)}")

        # Continue with existing standardization logic
        return DataFrameProcessor._standardize_single_dataframe(df1, df2)

    @staticmethod
    def _standardize_single_dataframe(df1: pd.DataFrame, df2: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Standardize a single pair of DataFrames for direct comparison.

        Parameters:
            df1, df2 (pd.DataFrame): Input DataFrames

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: Standardized DataFrames

        Notes:
            - Resets indices
            - Ensures column names are strings
            - Handles unnamed columns
            - Standardizes data types for common columns
        """
        df1_copy = df1.copy().reset_index(drop=True)
        df2_copy = df2.copy().reset_index(drop=True)

        # Ensure all column names are strings
        df1_copy.columns = df1_copy.columns.astype(str)
        df2_copy.columns = df2_copy.columns.astype(str)

        # Handle unnamed columns
        df1_copy.columns = [f'Unnamed: {i}' if col == '' else col
                            for i, col in enumerate(df1_copy.columns)]
        df2_copy.columns = [f'Unnamed: {i}' if col == '' else col
                            for i, col in enumerate(df2_copy.columns)]

        # Clean both dataframes
        df1_copy = DataFrameProcessor._clean_dataframe(df1_copy)
        df2_copy = DataFrameProcessor._clean_dataframe(df2_copy)

        # Standardize columns
        for col in df1_copy.columns:
            if col in df2_copy.columns:
                df1_copy[col], df2_copy[col] = DataFrameProcessor.standardize_column(
                    df1_copy[col], df2_copy[col])

        return df1_copy, df2_copy

    def compare_dataframes(self, df1: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
                           df2: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
                           test_name: str,
                           suppress_errors: bool = False) -> Tuple[bool, str]:
        """
        Compare dataframes and return result with detailed error information.

        Parameters:
            df1, df2 (Union[pd.DataFrame, Dict[str, pd.DataFrame]]): DataFrames to compare
            test_name (str): Name of the test for logging purposes
            suppress_errors (bool): Whether to suppress error logging

        Returns:
            Tuple[bool, str]:
                - Boolean indicating success or failure
                - String with error details if failure

        Notes:
            - Compares DataFrames using pandas testing functionality
            - Provides detailed error information when differences are found
            - Tolerates small numerical differences
        """

        try:
            # Extract DataFrames from dictionaries if necessary
            if isinstance(df1, dict):
                df1 = next(iter(df1.values()))
            if isinstance(df2, dict):
                df2 = next(iter(df2.values()))

            # Sort columns to ensure consistent ordering
            df1 = df1.reindex(sorted(df1.columns), axis=1)
            df2 = df2.reindex(sorted(df2.columns), axis=1)

            # Rename duplicate columns consistently
            df1_cols = []
            for col in df1.columns:
                if col in df1_cols:
                    df1_cols.append(f"{col}.1")
                else:
                    df1_cols.append(col)
            df1.columns = df1_cols

            df2_cols = []
            for col in df2.columns:
                if col in df2_cols:
                    df2_cols.append(f"{col}.1")
                else:
                    df2_cols.append(col)
            df2.columns = df2_cols

            # Compare DataFrames
            pd.testing.assert_frame_equal(
                df1,
                df2,
                check_dtype=False,
                check_exact=False,
                check_index_type=False,
                rtol=1e-5,
                atol=1e-8
            )
            return True, ""

        except Exception as e:
            error_details = self._generate_comparison_error_details(df1, df2)
            if not suppress_errors:
                logger.error(error_details)
            return False, error_details

    def _generate_comparison_error_details(self, df1: pd.DataFrame, df2: pd.DataFrame) -> str:
        """
        Generate detailed error message for DataFrame comparison failures.

        Parameters:
            df1, df2 (pd.DataFrame): DataFrames that failed comparison

        Returns:
            str: Detailed error message highlighting differences

        Notes:
            Reports:
            - Shape mismatches
            - Column differences
            - Value differences in common columns
        """
        error_msg = "\nDetailed comparison:\n"
        error_msg += f"Shape mismatch: df1 {df1.shape} vs df2 {df2.shape}\n"
        error_msg += f"\nColumns in df1: {list(df1.columns)}\n"
        error_msg += f"Columns in df2: {list(df2.columns)}\n"

        diff_cols = []
        common_cols = set(df1.columns) & set(df2.columns)

        for col in common_cols:
            if not df1[col].equals(df2[col]):
                error_msg += f"\nDifferences in column '{col}':\n"
                error_msg += f"df1 unique values: {df1[col].unique()}\n"
                error_msg += f"df2 unique values: {df2[col].unique()}\n"
                diff_cols.append(col)

        error_msg += f"\nColumns with differences: {diff_cols}"
        return error_msg


class FileManager:
    """
    Handles file organization and classification.

    This class provides methods to identify and categorize test files based on naming
    conventions, supporting the testing of parsers with appropriate input and expected output files.
    """

    @staticmethod
    def is_multi_file_test(test_zip: Path) -> bool:
        """
        Check if zip contains multiple input files.

        Parameters:
            test_zip (Path): Path to the zip file

        Returns:
            bool: True if the zip contains multiple input files, False otherwise

        Notes:
            Detects if a test package contains multiple input files to determine
            if join_tables functionality should be tested.
        """
        with zipfile.ZipFile(test_zip, 'r') as zip_ref:
            input_files = [f for f in zip_ref.namelist() if '_input' in f]
            is_multi = len(input_files) > 1
            logger.info(f"Multi-file test detection: {is_multi} ({len(input_files)} input files)")
            return is_multi

    @staticmethod
    def group_files(files: List[Path]) -> Dict[str, List[Path]]:
        """
        Group files by their type based on naming convention.

        Parameters:
            files (List[Path]): List of file paths to group

        Returns:
            Dict[str, List[Path]]: Dictionary with file types as keys and lists of paths as values

        Notes:
            Categorizes files into:
            - 'input': Files containing input data for parsers
            - 'single': Files containing expected output from a single parser
            - 'joined': Files containing expected output from join_tables method
        """
        grouped = {
            'input': [],
            'single': [],
            'joined': []
        }

        for file in files:
            if '_expected_single_file' in file.name:
                grouped['single'].append(file)
            elif '_input' in file.name:
                grouped['input'].append(file)
            elif '_expected_joined_file' in file.name:
                grouped['joined'].append(file)

        logger.debug(f"Grouped files: {grouped}")
        return grouped


class TestProcessor:
    """
    Handles test execution logic for parser testing.

    This class processes test cases by:
    1. Extracting test files from zip archives
    2. Validating that parsers return proper DataFrame objects
    3. Comparing parser outputs with expected results
    4. Executing both individual parser tests and join_tables tests when applicable

    The class ensures that parsers meet the expected behavior and output requirements.
    """

    def __init__(self, handler_class: object):
        """
        Initialize the TestProcessor.

        Parameters:
            handler_class (object): The handler class to test
        """
        self.handler_class = handler_class
        self.file_reader = FileReader()
        self.df_processor = DataFrameProcessor()

    def process_test_case(self, test_zip: Path, test_dir: Path) -> None:
        """
        Process a single test case with support for multiple files.

        Parameters:
            test_zip (Path): Path to the zip file containing test data
            test_dir (Path): Directory where test files will be extracted

        Raises:
            ValueError: If no input files are found
            AssertionError: If test comparisons fail

        Notes:
            This method:
            1. Extracts test files from the zip
            2. Groups files by type
            3. Processes input files with the parser
            4. Performs individual and joined comparisons as appropriate
        """
        with zipfile.ZipFile(test_zip, 'r') as zip_ref:
            zip_ref.extractall(test_dir)

            # Group extracted files
            all_files = list(test_dir.glob('*'))
            grouped_files = FileManager.group_files(all_files)

            if not grouped_files['input']:
                raise ValueError(f"No input files found in {test_zip}")

            # Process input files
            parsed_results = self._process_input_files(grouped_files['input'])

            # First handle individual comparisons
            if grouped_files['single']:
                logger.info("Starting individual file comparisons...")
                self._handle_single_comparisons(parsed_results, grouped_files['single'])

            # Then handle joined comparison if available
            if grouped_files['joined']:
                logger.info("Starting joined file comparison...")
                self._handle_joined_comparison(parsed_results, grouped_files['joined'][0])

    def _verify_parser_result(self, result: object, file_name: str) -> bool:
        """
        Verify that the parser returns a proper DataFrame or dictionary of DataFrames.

        Parameters:
            result (object): The output from the parser method
            file_name (str): Name of the input file for error reporting

        Returns:
            bool: True if result is valid, raises exception otherwise

        Raises:
            TypeError: If parser result is not a DataFrame or dictionary of DataFrames

        Notes:
            This addresses requirement [1]: explicit validation of parser return type
        """
        if isinstance(result, pd.DataFrame):
            logger.debug(f"Parser for {file_name} returned a valid DataFrame")
            return True
        elif isinstance(result, dict):
            if all(isinstance(v, pd.DataFrame) for v in result.values()):
                logger.debug(f"Parser for {file_name} returned a valid dictionary of DataFrames")
                return True
            elif any(isinstance(v, dict) for v in result.values()):
                # Check if nested dictionaries contain DataFrames
                for k, v in result.items():
                    if isinstance(v, dict):
                        if not all(isinstance(inner_v, pd.DataFrame) for inner_v in v.values()):
                            raise TypeError(
                                f"Parser for {file_name} returned a nested dictionary with non-DataFrame values")
                logger.debug(f"Parser for {file_name} returned a valid nested dictionary of DataFrames")
                return True
            else:
                raise TypeError(
                    f"Parser for {file_name} returned a dictionary with non-DataFrame values: {type(next(iter(result.values()))).__name__}")
        else:
            raise TypeError(
                f"Parser for {file_name} must return a DataFrame or dictionary of DataFrames, got {type(result).__name__}")

    def _process_input_files(self, input_files: List[Path]) -> Dict[str, Union[pd.DataFrame, Dict]]:
        """
        Process all input files through the parser and validate return types.

        Parameters:
            input_files (List[Path]): List of input file paths

        Returns:
            Dict[str, Union[pd.DataFrame, Dict]]: Dictionary with file names as keys and parsed results as values

        Notes:
            This method validates that parser results are proper DataFrames or dictionaries of DataFrames,
            addressing requirement [1]: explicit validation of parser return type.
        """
        results = {}
        for input_file in input_files:
            input_path = self.file_reader.read_file(input_file, is_input_file=True)
            parser_result = self.handler_class.parser(input_path)

            # Validate that parser returns a proper DataFrame or dictionary of DataFrames
            self._verify_parser_result(parser_result, input_file.name)

            results[input_file.name] = parser_result
            self._log_parsing_result(input_file.name, parser_result)
        return results

    def _standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names by handling duplicates consistently.

        Parameters:
            df (pd.DataFrame): Input DataFrame

        Returns:
            pd.DataFrame: DataFrame with standardized column names

        Notes:
            Ensures column names are unique by adding suffixes to duplicates.
        """
        df = df.copy()
        seen_columns = set()
        new_columns = []

        for col in df.columns:
            base_name = col.split('.')[0]  # Remove any existing suffixes
            if base_name in seen_columns:
                new_columns.append(f"{base_name}.1")
            else:
                new_columns.append(base_name)
                seen_columns.add(base_name)

        df.columns = new_columns
        return df

    def _flatten_nested_dict_structure(self, data: Union[pd.DataFrame, Dict]) -> Union[
        pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        Transform nested dictionary structure from join_tables into flat structure.

        Transforms: {filename: {sheet: df, sheet2: df}}
        Into: {sheet: df, sheet2: df}

        This handles cases where join_tables returns nested dictionaries.
        """
        if not isinstance(data, dict):
            return data

        # Check if this is a nested structure
        first_value = next(iter(data.values()))
        if isinstance(first_value, dict):
            # This is nested: {filename: {sheet: df, sheet2: df}}
            # Flatten it to: {sheet: df, sheet2: df}
            flattened = {}
            for outer_key, inner_dict in data.items():
                if isinstance(inner_dict, dict):
                    # Add all inner key-value pairs to flattened dict
                    flattened.update(inner_dict)
                else:
                    # If inner value is not dict, use outer key
                    flattened[outer_key] = inner_dict
            return flattened
        else:
            # Already flat structure: {sheet: df, sheet2: df}
            return data

    def _handle_joined_comparison(self, parsed_results: Dict, expected_file: Path) -> None:
        """
        Handle comparison for joined results from multiple input files.
        """
        try:
            logger.info(f"Processing joined comparison with '{expected_file.name}'")

            # Special case for X8IfLongTermPowerCheckLogHandler
            if self.handler_class.__name__ == 'X8IfLongTermPowerCheckLogHandler':
                ucur_file_path = expected_file.parent / 'test_if.ucur'
                if not ucur_file_path.exists():
                    raise FileNotFoundError(f"Required UCUR file not found: {ucur_file_path}")

                def select_file(title=None, file_types=None, file_extension=None):
                    if file_types and ".ucur" in file_types:
                        return str(ucur_file_path)
                    return None

                joined_result = self.handler_class.join_tables(
                    parsed_results,
                    select_file=select_file
                )
            else:
                # Normal case for other handlers
                joined_result = self.handler_class.join_tables(parsed_results)

            # FLATTEN NESTED STRUCTURE - This is the key addition
            joined_result = self._flatten_nested_dict_structure(joined_result)

            # Validate join_tables result after flattening
            if isinstance(joined_result, dict):
                for key, value in joined_result.items():
                    if not isinstance(value, pd.DataFrame):
                        raise TypeError(f"join_tables result contains non-DataFrame: {type(value)} for key '{key}'")
            elif not isinstance(joined_result, pd.DataFrame):
                raise TypeError(f"join_tables result is not a DataFrame or dict: {type(joined_result)}")

            # Read expected result
            expected_df = self.file_reader.read_file(expected_file)

            # Debug logging
            logger.debug("=== Joined Result (after flattening) ===")
            if isinstance(joined_result, dict):
                logger.debug(f"Keys: {list(joined_result.keys())}")
                first_df = next(iter(joined_result.values()))
                logger.debug(f"First DataFrame shape: {first_df.shape}")
            else:
                logger.debug(f"DataFrame shape: {joined_result.shape}")

            # Standardize and compare
            std_result, std_expected = self.df_processor.standardize_dataframes(
                joined_result, expected_df)

            success, error_details = self.df_processor.compare_dataframes(
                std_result,
                std_expected,
                f"joined_test_{expected_file.name}",
                suppress_errors=True
            )

            if not success:
                logger.error("Comparison failed with the following differences:")
                logger.error(error_details)
                raise AssertionError(f"Join comparison failed:\n{error_details}")

            logger.info(f"Successfully completed joined comparison with '{expected_file.name}'")

        except Exception as e:
            logger.error(f"Join comparison failed: {str(e)}")
            raise


    def _handle_single_comparisons(self, parsed_results: Dict, expected_files: List[Path]) -> None:
        """
        Handle comparisons for single file results.
        """
        for input_name, parsed_result in parsed_results.items():
            logger.info(f"\nProcessing comparisons for input file: '{input_name}'")
            match_found = False
            comparison_errors = []

            # Check if join_tables is a custom method (not the default one)
            has_custom_join = (hasattr(self.handler_class, 'join_tables') and
                               self.handler_class.join_tables.__module__ != 'analysis_files.handler_files.base_handler')

            # Create result to test - always start with parser result
            single_file_dict = {input_name: parsed_result}

            if has_custom_join:
                logger.info(
                    f"Custom join_tables method found in {self.handler_class.__name__}, applying to parser result")
                try:
                    # Special case for X8IfLongTermPowerCheckLogHandler
                    if self.handler_class.__name__ == 'X8IfLongTermPowerCheckLogHandler':
                        ucur_file_path = next(iter(expected_files)).parent / 'test_if.ucur'
                        if not ucur_file_path.exists():
                            raise FileNotFoundError(f"Required UCUR file not found: {ucur_file_path}")

                        def select_file(file_type):
                            if file_type == 'if':
                                return str(ucur_file_path)
                            return None

                        result_to_test = self.handler_class.join_tables(
                            single_file_dict,
                            select_file=select_file
                        )
                    else:
                        result_to_test = self.handler_class.join_tables(single_file_dict)

                    # FLATTEN NESTED STRUCTURE - Apply the same transformation
                    result_to_test = self._flatten_nested_dict_structure(result_to_test)

                except Exception as e:
                    logger.error(f"join_tables method failed for parser result: {str(e)}")
                    raise
            else:
                logger.info(
                    f"No custom join_tables method found in {self.handler_class.__name__}, using parser result directly")
                result_to_test = parsed_result

            # Continue with existing comparison logic...
            for expected_file in expected_files:
                try:
                    logger.info(f"Comparing with expected result: '{expected_file.name}'")
                    expected_df = self.file_reader.read_file(expected_file)

                    # Perform comparison with errors suppressed
                    std_result, std_expected = self.df_processor.standardize_dataframes(
                        result_to_test, expected_df)
                    success, error_details = self.df_processor.compare_dataframes(
                        std_result,
                        std_expected,
                        f"single_test_{expected_file.name}",
                        suppress_errors=True
                    )

                    if success:
                        method_used = "parser+join_tables" if has_custom_join else "parser"
                        logger.info(
                            f"✓ Match found! Successfully compared '{input_name}' with '{expected_file.name}' using {method_used}")
                        match_found = True
                        break
                    else:
                        comparison_errors.append((expected_file.name, error_details))

                except Exception as e:
                    comparison_errors.append((expected_file.name, str(e)))
                    continue

            if not match_found:
                # Only show errors if no match was found
                error_msg = f"No matching expected result found for input file '{input_name}'. Errors:\n"
                for expected_name, error in comparison_errors:
                    error_msg += f"\nComparison with '{expected_name}':\n{error}\n"
                raise AssertionError(error_msg)

            logger.info(f"Successfully found match for input file '{input_name}'")

    @staticmethod
    def _log_parsing_result(file_name: str, result: Union[pd.DataFrame, Dict]) -> None:
        """
        Log parsing results for debugging.

        Parameters:
            file_name (str): Name of the input file
            result (Union[pd.DataFrame, Dict]): Parsed result

        Notes:
            Provides debug information about parsed results including shape and structure.
        """
        logger.debug(f"Parsed result for {file_name}:")
        if isinstance(result, dict):
            for k, v in result.items():
                logger.debug(f"Sheet '{k}' shape: {v.shape}")
        elif isinstance(result, pd.DataFrame):
            logger.debug(f"DataFrame shape: {result.shape}")


class TestParsers(unittest.TestCase):
    """
    Test suite for parser functionality verification.

    This class provides comprehensive testing of log file parsers to ensure they:
    1. Return proper DataFrame outputs
    2. Correctly parse log file contents
    3. Match expected output DataFrames
    4. Handle various error conditions appropriately

    The test suite downloads test files from SharePoint and runs multiple test cases for each parser.

    Usage:
        python -m unittest test_parsers.py

    Test Objectives:
        - Verify parsers return DataFrames with expected structure
        - Validate parsing functionality with real log files
        - Test join_tables functionality for multi-file parsers
        - Identify specific issues in parsers by detailed error reporting

    Expected Inputs:
        - Test zip files containing:
          - Input log files with '_input' in name
          - Expected output files with '_expected_single_file' or '_expected_joined_file' in name

    Expected Outputs:
        - Test pass/fail results
        - Detailed error reports for failures
        - Validation that parsers meet requirements
    """

    def __init__(self, methodName='runTest'):
        """
        Initialize the test suite.

        Parameters:
            methodName (str): Method name for unittest
        """
        super().__init__(methodName)
        self.sharepoint_handler = None

    def setUp(self):
        """
        Initialize test environment.

        This method:
        1. Configures logging
        2. Sets up SharePoint connection
        3. Creates test directories
        4. Downloads test files from SharePoint

        Raises:
            RuntimeError: If SharePoint authentication or download fails
        """
        logger.info("Setting up test environment")

        # SharePoint configuration
        self.sharepoint_url = "https://nikonglobaleu.sharepoint.com/sites/Teams_0006729/"
        self.sharepoint_folder = "Shared%20Documents/General/file_for_testing/Machine_logs/"

        # Initialize SharePoint handler with auto-authentication
        logger.info("Authenticating to SharePoint...")
        self.sharepoint_handler = SharePointHandler(self.sharepoint_url, auto_authenticate=True)
        if not self.sharepoint_handler.is_authenticated:
            raise RuntimeError(f"SharePoint authentication failed: {self.sharepoint_handler.authentication_error}")

        logger.info("SharePoint authentication successful")

        # Set up project paths
        self.project_root = Path(__file__).parent.parent  # Go up one more level
        self.test_files_path = Path(r"C:\nikon_Data\test_file_nlh")
        self.handlers_path = self.project_root / "analysis_files" / "handler_files"

        logger.debug(f"Project root: {self.project_root}")
        logger.debug(f"Test files path: {self.test_files_path}")
        logger.debug(f"Handlers path: {self.handlers_path}")

        # Create test directory if it doesn't exist
        self.test_files_path.mkdir(parents=True, exist_ok=True)
        logger.debug("Created test files directory")

        warnings.filterwarnings("ignore", category=ResourceWarning)
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # Download all test folders from SharePoint
        logger.info("Starting download of SharePoint folders")
        self.downloaded_folders = self.sharepoint_handler.download_sharepoint_folders(
            self.sharepoint_folder,
            self.test_files_path
        )

        if any(f.startswith("Error") for f in self.downloaded_folders):
            logger.error("Failed to download test folders from SharePoint")
            raise RuntimeError("Failed to download test folders from SharePoint")

        logger.info("Setup completed successfully")

    def _clean_test_directory(self, test_dir: Path):
        """
        Clean the test directory.

        Parameters:
            test_dir (Path): Directory to clean

        Raises:
            Exception: If directory cannot be cleaned or created

        Notes:
            Removes existing files and creates a fresh directory for testing.
        """
        logger.info(f"Cleaning test directory: {test_dir}")
        if test_dir.exists():
            try:
                shutil.rmtree(test_dir)
                logger.debug(f"Removed existing directory: {test_dir}")
            except Exception as e:
                logger.error(f"Error removing directory {test_dir}: {str(e)}")
                raise

        try:
            test_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created new directory: {test_dir}")
        except Exception as e:
            logger.error(f"Error creating directory {test_dir}: {str(e)}")
            raise

    def _download_test_files(self, handler_name: str) -> Path:
        """
        Download test files from SharePoint for a specific handler.

        Parameters:
            handler_name (str): Name of the handler to download test files for

        Returns:
            Path: Path to the test directory

        Raises:
            ValueError: If download fails

        Notes:
            Downloads and extracts test zip files for the specified handler.
        """
        logger.info(f"Downloading test files for handler: {handler_name}")
        test_dir = self.test_files_path / handler_name
        self._clean_test_directory(test_dir)

        try:
            # Construct the SharePoint folder path for this handler
            handler_sharepoint_folder = f"{self.sharepoint_folder}/{handler_name}"
            test_file_name = f"{handler_name}_tests.zip"

            logger.debug(f"Attempting to download {test_file_name} from {handler_sharepoint_folder}")

            # Download the test zip file using the new method
            result = self.sharepoint_handler.load_file_from_sharepoint(
                handler_sharepoint_folder,
                test_file_name,
                str(test_dir) + "/"
            )

            if isinstance(result, str) and result.startswith("Error"):
                logger.error(f"Failed to download test files: {result}")
                raise ValueError(f"Failed to download test files: {result}")

            logger.info(f"Successfully downloaded test files to {test_dir}")
            return test_dir
        except Exception as e:
            logger.error(f"Error downloading test files for {handler_name}: {str(e)}")
            raise

    def _import_handler_class(self, handler_file: str) -> object:
        """
        Import handler class dynamically.

        Parameters:
            handler_file (str): Name of the handler file

        Returns:
            object: Imported handler class

        Raises:
            Exception: If handler class cannot be imported

        Notes:
            Converts snake_case file names to CamelCase class names.
        """
        try:
            # Remove .py extension and convert to module path format
            handler_name = handler_file.replace('.py', '')

            # Convert snake_case to CamelCase for class name
            handler_class_name = ''.join(word.capitalize() for word in handler_name.split('_'))
            logger.info(f"Handler class name: {handler_class_name}")

            # Import the module
            module = import_module(f"analysis_files.handler_files.{handler_name}")
            handler_class = getattr(module, handler_class_name)

            logger.info(f"Successfully imported handler class: {handler_class}")
            return handler_class

        except Exception as e:
            logger.error(f"Error importing handler class from {handler_file}: {str(e)}")
            raise

    # Add context manager for file operations
    def _cleanup_test_files(self, test_dir: Path, exclude_zip: bool = False):
        """
        Clean up files in the test directory.

        Parameters:
            test_dir (Path): Directory to clean
            exclude_zip (bool): Whether to exclude zip files from cleanup

        Notes:
            Removes test files while handling file locking issues.
        """
        logger.info(f"Cleaning up files in {test_dir}")
        try:
            for file_path in test_dir.iterdir():
                if file_path.is_file():
                    if exclude_zip and file_path.suffix.lower() == '.zip':
                        continue
                    try:
                        # Close any open file handles before deletion
                        import gc
                        gc.collect()  # Force garbage collection
                        file_path.unlink(missing_ok=True)  # Use missing_ok=True to avoid errors
                        logger.debug(f"Removed file: {file_path}")
                    except PermissionError:
                        logger.warning(f"Could not remove file {file_path} - file is in use")
                    except Exception as e:
                        logger.warning(f"Failed to remove file {file_path}: {str(e)}")
        except Exception as e:
            logger.warning(f"Error during cleanup of {test_dir}: {str(e)}")

    def test_parsers(self):
        """
        Main test method for testing all parsers.

        This method:
        1. Identifies all handler files in the project
        2. Imports each handler class
        3. Runs test cases for each handler
        4. Reports test results with detailed error information

        Test Purpose:
            To verify that all parsers correctly process log files and produce expected outputs.

        Expected Inputs:
            Handler files with '_handler.py' suffix
            Test zip files with input and expected output files

        Expected Outputs:
            Test pass/fail results
            Detailed error reports for failures

        Notes:
            Addresses requirements [1, 2, 3, 8, 9] by testing each parser individually
            and verifying that they return proper DataFrames with expected content.
        """
        logger.info("Starting parser tests")
        handler_files = [f.name for f in self.handlers_path.glob('*_handler.py')]
        print(handler_files)
        logger.debug(f"Found handler files: {handler_files}")

        for handler_file in handler_files:
            logger.info(f"\nTesting handler: {handler_file}")

            try:
                handler_class = self._import_handler_class(handler_file)
                logger.debug(f"Successfully imported handler class: {handler_class.__name__}")

                # Find the corresponding test folder
                test_dir = self.test_files_path / handler_class.__name__
                if not test_dir.exists():
                    logger.warning(f"No test directory found for {handler_class.__name__}")
                    continue

                processor = TestProcessor(handler_class)

                # Process all zip files in the test directory
                test_zips = list(test_dir.glob("*.zip"))
                for test_zip in test_zips:
                    with self.subTest(handler=handler_class.__name__, test=test_zip.name):
                        try:
                            processor.process_test_case(test_zip, test_dir)
                        except Exception as e:
                            logger.error(f"Error in test {test_zip}: {str(e)}")
                            raise
                        finally:
                            # Clean up all files including the current zip file
                            self._cleanup_test_files(test_dir, exclude_zip=True)

            except Exception as e:
                logger.error(f"Error processing handler {handler_file}: {str(e)}")
                raise

    def tearDown(self):
        """
        Clean up after all tests.

        This method:
        1. Closes any open files
        2. Removes test directories

        Notes:
            Ensures that tests don't leave behind temporary files.
        """
        logger.info("Cleaning up test environment")
        try:
            # Close any open files
            import gc
            gc.collect()

            # Add delay before cleanup
            import time
            time.sleep(1)

            if self.test_files_path.exists():
                shutil.rmtree(self.test_files_path, ignore_errors=True)
                logger.debug(f"Removed test files directory: {self.test_files_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up test files: {str(e)}")


if __name__ == '__main__':
    # Run tests from command line with:
    # python test_parsers.py
    unittest.main()
