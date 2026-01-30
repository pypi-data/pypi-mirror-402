"""Augur Data Management Package

This package provides a comprehensive data management system for Augur, handling
storage operations across different backends including S3, local filesystem, and Cassandra.

It abstracts away the differences between production and development environments,
providing a unified interface for data operations throughout the application.

Modules:
    augur_data: Core utilities for reading and writing to Augur data storage, with
        environment-aware operations through the `_augurdata()` singleton function.
    
    data_management: Interfaces for accessing and managing data across storage backends,
        handling data source configuration, credential management, and operations.
    
    filesystem: Utilities for managing file system operations related to job runs,
        reports, settings, and standardized path management.
    
    s3_parquet: Specialized utilities for reading and writing Parquet files between
        S3 storage and Pandas DataFrames with efficient temporary file handling.

This package is designed to be initialized automatically based on environment
configurations, providing seamless data access regardless of deployment context.
"""