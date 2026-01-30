"""AltaSigma package for data management and processing.

This package provides tools for credential management, data source operations,
configuration management, and job supervision.

The public API components are explicitly imported and exposed at the package level.
Users should import components directly from the `altasigma` package rather than
from individual submodules.

Examples:
    Recommended import style:
    
    >>> from altasigma import CredentialUtils, AltaSigma, S3DataSource
    
    Avoid importing from submodules directly:
    
    >>> # Not recommended
    >>> from altasigma.credentials.credential_utils import CredentialUtils

Note:
    Only components explicitly imported in this file are considered part of the
    public API. Other components within submodules should be treated as internal
    implementation details that may change without notice.

    The only exception to that is altasigma.spark_session.spark_session_util, which contains
    imports from pyspark. Not importing it here makes pyspark an optional dependency.
"""
from altasigma.credentials.credential_utils import CredentialUtils
from altasigma.initialize import AltaSigma, initialize
from altasigma.io.data_management import S3DataSource, Bucket, CassandraDataSource, BiographyInfo, BiographyInfoEntry, TextEntry, S3PathEntry, S3Data, CassandraTableEntry, CassandraData, get_datasource
from altasigma.config.config import RunEnv, JobType
from altasigma.jobsupervisor.reports import dataframe_to_table_report_data
# Spark is an optional dependency. If we add an import here it is no longer optional
# from altasigma.spark_session.spark_session_util import get_spark_session
from altasigma.progress_reporter.progress_reporter import ProgressReporter
