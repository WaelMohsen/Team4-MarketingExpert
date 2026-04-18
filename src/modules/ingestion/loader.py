from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pandas as pd

DataSource = pd.DataFrame | str | Path
ReadKeywordArguments = dict[str, Any]


@dataclass
class DataLoader:
    """
    Load ads analytics data into a pandas DataFrame.

    Supported inputs:
    - pandas DataFrame
    - .csv
    - .xlsx / .xls
    - .json
    - .parquet

    Optional cleanup:
    - strip whitespace from column names
    - drop columns that contain only null values
    """

    strip_column_whitespace: bool = True
    drop_all_null_columns: bool = True

    def load(
        self,
        source: DataSource,
        *,
        read_keyword_arguments: Optional[ReadKeywordArguments] = None,
    ) -> pd.DataFrame:
        """
        Load data from a DataFrame or file source, then apply optional cleanup.
        """
        read_keyword_arguments = read_keyword_arguments or {}

        dataframe = self.read(
            source,
            read_keyword_arguments=read_keyword_arguments,
        )

        if self.strip_column_whitespace:
            dataframe = self.strip_column_names(dataframe)

        if self.drop_all_null_columns:
            dataframe = self.drop_fully_null_columns(dataframe)

        return dataframe

    def read(
        self,
        source: DataSource,
        *,
        read_keyword_arguments: ReadKeywordArguments,
    ) -> pd.DataFrame:
        """
        Read data from the given source into a DataFrame.
        """
        if isinstance(source, pd.DataFrame):
            return source.copy()

        file_path = Path(source)

        self._validate_file_exists(file_path)

        file_extension = file_path.suffix.lower()
        reader = self._get_reader(file_extension)

        return reader(file_path, **read_keyword_arguments)

    def strip_column_names(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Remove leading and trailing whitespace from column names.
        """
        cleaned_dataframe = dataframe.copy()
        cleaned_dataframe.columns = [
            str(column_name).strip()
            for column_name in cleaned_dataframe.columns
        ]
        return cleaned_dataframe

    def drop_fully_null_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Remove columns where every value is null.
        """
        return dataframe.dropna(axis=1, how="all").copy()

    def _validate_file_exists(self, file_path: Path) -> None:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

    def _get_reader(self, file_extension: str):
        readers = {
            ".csv": pd.read_csv,
            ".xlsx": pd.read_excel,
            ".xls": pd.read_excel,
            ".json": pd.read_json,
            ".parquet": pd.read_parquet,
        }

        if file_extension not in readers:
            supported_extensions = ", ".join(readers.keys())
            raise ValueError(
                f"Unsupported file type '{file_extension}'. "
                f"Supported file types: {supported_extensions}"
            )

        return readers[file_extension]