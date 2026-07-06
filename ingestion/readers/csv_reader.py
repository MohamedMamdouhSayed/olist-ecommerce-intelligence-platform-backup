"""Reusable CSV reader utilities for ingestion source files."""

import logging
from pathlib import Path

import pandas as pd


logger = logging.getLogger(__name__)


class CSVReader:
    """Read and inspect CSV files for future ingestion workflows."""

    def validate_file_exists(self, path: str | Path) -> Path:
        """Validate that a CSV source file exists and return its resolved path.

        Args:
            path: File system path to the CSV source file.

        Raises:
            FileNotFoundError: If the path does not exist.
            IsADirectoryError: If the path points to a directory.

        Returns:
            The resolved ``Path`` for the source file.
        """
        file_path = Path(path).expanduser().resolve()
        logger.debug("Validating CSV file path: %s", file_path)

        if not file_path.exists():
            logger.error("CSV file does not exist: %s", file_path)
            raise FileNotFoundError(f"CSV file does not exist: {file_path}")

        if file_path.is_dir():
            logger.error("Expected a CSV file but received a directory: %s", file_path)
            raise IsADirectoryError(f"Expected a CSV file but received a directory: {file_path}")

        return file_path

    def load_dataframe(self, path: str | Path) -> pd.DataFrame:
        """Load a CSV file into a pandas DataFrame.

        Args:
            path: File system path to the CSV source file.

        Returns:
            A pandas DataFrame containing the CSV rows.
        """
        file_path = self.validate_file_exists(path)
        logger.info("Loading CSV file into DataFrame: %s", file_path)
        return pd.read_csv(file_path)

    def get_row_count(self, path: str | Path) -> int:
        """Return the number of rows in a CSV file.

        Args:
            path: File system path to the CSV source file.

        Returns:
            The number of records in the CSV file.
        """
        dataframe = self.load_dataframe(path)
        row_count = len(dataframe)
        logger.info("CSV row count for %s: %s", path, row_count)
        return row_count

    def preview(self, path: str | Path, n: int = 5) -> pd.DataFrame:
        """Return the first rows from a CSV file.

        Args:
            path: File system path to the CSV source file.
            n: Number of rows to return.

        Returns:
            A DataFrame containing the first ``n`` rows.
        """
        if n < 1:
            raise ValueError("Preview row count must be greater than zero.")

        dataframe = self.load_dataframe(path)
        logger.info("Previewing first %s rows from CSV file: %s", n, path)
        return dataframe.head(n)

