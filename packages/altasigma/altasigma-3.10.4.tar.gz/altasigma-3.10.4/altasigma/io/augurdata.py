"""
Augur Data Management Module

This module provides utilities for reading and writing to Augur data storage in
both production and development environments. It abstracts the storage backend
differences between S3 (production) and local filesystem (development).

The module supports automatic initialization and environment-aware operations
through the singleton-style `_augurdata()` function.
"""

from io import BytesIO
from pathlib import Path

from .data_management import Bucket, S3DataSource
from .files import ensure_augurdata_dir, augurdata_path
from ..config.config import _module_config, RunEnv


def generate_augurdata_name(augur_code: str) -> str:
    """
    Generate a standardized name for Augur data sources.
    
    Args:
        augur_code (str): The Augur code identifier.
        
    Returns:
        str: A formatted name in the pattern 'augur-{code}' with lowercase code.
    """
    return f'augur-{augur_code.lower()}'


class AugurData:
    """
    Provides environment-aware access to Augur data storage.
    
    This class handles data operations for Augur, automatically using the appropriate
    storage backend based on the current environment (S3 for production, local
    filesystem for development).
    
    Attributes:
        bucket: S3 bucket for production environment.
        path: Local filesystem path for development environment.
    """
    bucket = None
    path = None

    def _initialize(self, augurdata_datasource_code: str):
        """
        Initialize the appropriate data storage backend.
        
        Sets up either an S3 bucket connection (production) or a local file path
        (development) based on the current environment.
        
        Args:
            augurdata_datasource_code (str): The data source code for accessing Augur data.
        """
        if _module_config().run_env == RunEnv.Prod:
            self.bucket = Bucket(S3DataSource(augurdata_datasource_code),
                                 generate_augurdata_name(_module_config().job.augur_code))
        elif _module_config().run_env == RunEnv.Dev:
            self.path = Path(augurdata_path)

    def read(self, path: str) -> BytesIO:
        """
        Read data from Augur storage.
        
        Retrieves content from either S3 (production) or local filesystem (development)
        depending on the current environment.
        
        Args:
            path (str): The path to the file within the Augur data storage.
            
        Returns:
            BytesIO: A byte stream containing the file content.
            
        Raises:
            Exception: If the Augur data storage has not been initialized.
        """
        if _module_config().run_env == RunEnv.Prod:
            if self.bucket is None:
                raise Exception("Augurdata bucket has not been initialized")
            return self.bucket.read(path)
        elif _module_config().run_env == RunEnv.Dev:
            ensure_augurdata_dir()
            final_path = self.path / Path(path)
            with open(final_path, "rb") as f:
                return BytesIO(f.read())

    def write(self, path: str, content: BytesIO):
        """
        Write data to Augur storage.
        
        Stores content to either S3 (production) or local filesystem (development)
        depending on the current environment.
        
        Args:
            path (str): The path where the file should be stored within Augur data storage.
            content (BytesIO): The byte stream containing the content to write.
            
        Raises:
            Exception: If the Augur data storage has not been initialized.
        """
        if _module_config().run_env == RunEnv.Prod:
            if self.bucket is None:
                raise Exception("Augurdata bucket has not been initialized")
            return self.bucket.write(path, content)
        elif _module_config().run_env == RunEnv.Dev:
            ensure_augurdata_dir()
            final_path = self.path / Path(path)
            final_path.parent.mkdir(parents=True, exist_ok=True)
            with open(final_path, "wb") as f:
                f.write(content.getbuffer())


# Global instance for singleton-like access
augurdata = None


def _augurdata():
    """
    Get or initialize the global AugurData instance.
    
    This function implements a singleton pattern, ensuring that only one
    AugurData instance is created and reused across multiple calls.
    
    Returns:
        AugurData: The global AugurData instance.
    """
    global augurdata
    if augurdata is not None:
        return augurdata
    else:
        augurdata = AugurData()
        return augurdata