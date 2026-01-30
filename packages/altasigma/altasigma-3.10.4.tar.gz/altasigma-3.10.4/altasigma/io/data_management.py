"""
Data Management Module

This module provides interfaces and utilities for accessing and managing data across
different storage backends, primarily focusing on S3 and Cassandra data sources.
It handles data source configuration, credential management, and data operations.

The module supports:
- Data source discovery and configuration
- Secure credential management for storage backends
- Read/write operations for S3 buckets
- Structured data source metadata representation
"""

import dataclasses
import io
import logging
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from typing import Optional, List, Dict

import boto3
import botocore

from ..config.config import _module_config, _data_man_config
from ..config.http_session import _http_session, _get_ssl_config
from ..credentials.credential_utils import _credential_utils

logger = logging.getLogger(__name__)


class DSType(Enum):
    """
    Enumeration of supported data source types.
    """
    S3 = "s3"
    Cassandra = "cassandra"


@dataclass(frozen=True)
class CassandraSettings:
    """
    Configuration settings for connecting to a Cassandra data source.
    
    Attributes:
        host (str): Hostname of the Cassandra cluster.
        port (int): Port number for Cassandra connection.
        user (str): Username for authentication.
        password (str): Password for authentication.
        datacenter (str): Cassandra datacenter name.
    """
    host: str
    port: int
    user: str
    password: str
    datacenter: str


@dataclass(frozen=True)
class S3Settings:
    """
    Configuration settings for connecting to an S3-compatible storage.
    
    Attributes:
        host (str): Hostname of the S3 service.
        port (int): Port number for S3 connection.
        accessKey (str): Access key for authentication.
        secretKey (str): Secret key for authentication.
        region (str): AWS region name.
    """
    host: str
    port: int
    accessKey: str
    secretKey: str
    region: str


@dataclass(frozen=True)
class DataSource:
    """
    Representation of a data source with its configuration and metadata.
    
    This class represents any type of data source in the system, containing
    its basic metadata and specific connection settings.
    
    Attributes:
        code (str): Unique identifier code for the data source.
        name (str): Human-readable name of the data source.
        ds_type (str): Type of data source (e.g., "s3", "cassandra").
        role (str): Role or purpose of the data source.
        settings (CassandraSettings | S3Settings): Type-specific connection settings.
        created_at (str): Timestamp when the data source was created.
    """
    code: str
    name: str
    ds_type: str
    role: str
    settings: CassandraSettings | S3Settings
    created_at: str

    @classmethod
    def from_dict(cls, d: Dict):
        """
        Create a DataSource instance from a dictionary representation.
        
        Args:
            d (Dict): Dictionary containing data source information.
            
        Returns:
            DataSource: A properly configured DataSource instance.
            
        Raises:
            ValueError: If the data source type is unknown.
        """
        ds = DataSource(**d)
        if d["ds_type"] == "cassandra":
            return dataclasses.replace(ds, settings=CassandraSettings(**d["settings"]))
        elif d["ds_type"] == "s3":
            return dataclasses.replace(ds, settings=S3Settings(**d["settings"]))
        raise ValueError(f"Unknown ds_type: {d['ds_type']}")


@dataclass
class S3Credentials:
    """
    Credentials for accessing S3-compatible storage.
    
    Attributes:
        access_key (str): Access key ID for S3 authentication.
        secret_key (str): Secret access key for S3 authentication.
        expires_at (int): Timestamp when these credentials expire.
    """
    access_key: str
    secret_key: str
    expires_at: int


@dataclass
class S3CredentialsRaw:
    """
    Raw representation of S3 credentials as received from the API.
    
    This class is used to parse the API response before converting
    to the standard S3Credentials format.
    
    Attributes:
        accessKey (str): Access key ID for S3 authentication.
        secretKey (str): Secret access key for S3 authentication.
        expiresAt (int): Timestamp when these credentials expire.
    """
    accessKey: str
    secretKey: str
    expiresAt: int

    def to_S3Credentials(self) -> S3Credentials:
        """
        Convert raw credentials to the standard S3Credentials format.
        
        Returns:
            S3Credentials: Standard credential representation.
        """
        return S3Credentials(self.accessKey, self.secretKey, self.expiresAt)


@dataclass
class CassandraCredentials:
    """
    Credentials for accessing Cassandra databases.
    
    This class omits the error field when passing it to consumers.
    If there are errors, the constructor will raise an exception.
    
    Attributes:
        username (str): Username for Cassandra authentication.
        password (str): Password for Cassandra authentication.
        expires_at (Optional[int]): Timestamp when these credentials expire, if applicable.
    """
    username: str
    password: str
    expires_at: Optional[int] = None


# Internal
@dataclass
class CassandraCredentialsRaw:
    """
    Raw representation of Cassandra credentials as received from the API.
    
    This class is used to parse the API response before converting
    to the standard CassandraCredentials format.
    
    Attributes:
        username (str): Username for Cassandra authentication.
        password (str): Password for Cassandra authentication.
        errors (List[str]): Any errors reported in the API response.
        dataSourceType (str): The type of data source (should be "cassandra").
        expiresAt (Optional[int]): Timestamp when these credentials expire, if applicable.
    """
    username: str
    password: str
    errors: List[str]
    dataSourceType: str
    expiresAt: Optional[int] = None

    def to_CassandraCredentials(self) -> CassandraCredentials:
        """
        Convert raw credentials to the standard CassandraCredentials format.
        
        Returns:
            CassandraCredentials: Standard credential representation.
            
        Raises:
            Exception: If errors are present in the raw credentials.
        """
        if len(self.errors) > 0:
            raise Exception(f"Errors in Cassandra Credential Response: {self.errors}")

        return CassandraCredentials(self.username, self.password, self.expiresAt)


def get_datasource_by_code(datasource_code: str) -> DataSource:
    """
    Retrieve a data source by its unique code.
    
    Args:
        datasource_code (str): The code identifier for the data source.
        
    Returns:
        DataSource: The requested data source configuration.
        
    Raises:
        HTTPError: If the API request fails.
    """
    access_token, _ = _credential_utils()._existing_token()

    response = _http_session().get(
        f"http://{_data_man_config().api_host}:{_data_man_config().api_port}/dataman/datasource/{datasource_code}",
        headers={"Authorization": f"Bearer {access_token}"})
    response.raise_for_status()
    return DataSource.from_dict(response.json())


def get_datasource(datasource_name: str) -> DataSource:
    """
    Retrieve a data source by its human-readable name.
    
    Args:
        datasource_name (str): The display name of the data source.
        
    Returns:
        DataSource: The requested data source configuration.
        
    Raises:
        ValueError: If no data source with the specified name exists.
        RuntimeError: If the API request fails.
    """
    access_token, _ = _credential_utils()._existing_token()

    data_sources_request = _http_session().get(
        f"http://{_data_man_config().api_host}:{_data_man_config().api_port}/dataman/datasources",
        headers={"Authorization": f"Bearer {access_token}"})
    if data_sources_request.status_code == 200:
        data_sources_response = data_sources_request.json()
        # use data_source_name to search for fitting data source code
        data_sources = [entry for entry in data_sources_response if entry["name"] == datasource_name]
        if not data_sources:
            raise ValueError(f"Data source with name '{datasource_name}' not found.")

        datasource_code = data_sources[0]["code"]
        return get_datasource_by_code(datasource_code)
    else:
        raise RuntimeError(
            f"Unexpected response from dataman: {data_sources_request.status_code}, {data_sources_request.text}")


def get_s3_credentials(datasource_code: str) -> S3Credentials:
    """
    Retrieve S3 credentials for a specific data source.
    
    Args:
        datasource_code (str): The code identifier for the S3 data source.
        
    Returns:
        S3Credentials: Credentials for accessing the S3 data source.
        
    Raises:
        HTTPError: If the credential request fails.
    """
    access_token, _ = _credential_utils()._existing_token()
    response = _http_session().get(
        f"http://{_data_man_config().api_host}:{_data_man_config().api_port}/dataman/s3/{datasource_code}/credentials",
        headers={"Authorization": f"Bearer {access_token}"})
    response.raise_for_status()
    response_j = response.json()
    logger.debug(f"S3 credentials response: {response_j}")
    return S3CredentialsRaw(**response_j).to_S3Credentials()


def get_cassandra_credentials(datasource_code: str) -> CassandraCredentials:
    """
    Retrieve Cassandra credentials for a specific data source.
    
    Args:
        datasource_code (str): The code identifier for the Cassandra data source.
        
    Returns:
        CassandraCredentials: Credentials for accessing the Cassandra data source.
        
    Raises:
        HTTPError: If the credential request fails.
        Exception: If the response contains errors.
    """
    access_token, _ = _credential_utils()._existing_token()
    response = _http_session().get(
        f"http://{_data_man_config().api_host}:{_data_man_config().api_port}/dataman/cassandra/{datasource_code}/credentials",
        headers={"Authorization": f"Bearer {access_token}"})
    response.raise_for_status()
    response_j = response.json()
    logger.debug(f"Cassandra credentials response: {response_j}")
    return CassandraCredentialsRaw(**response_j).to_CassandraCredentials()


class S3DataSource:
    """
    Represents an S3-compatible data source with its settings and credentials.
    
    This class handles the retrieval and management of S3 data source configuration
    and credentials, providing a unified interface for S3 operations.
    
    Attributes:
        code (str): Unique identifier code for the data source.
        name (str): Human-readable name of the data source.
        settings (S3Settings): Connection settings for the S3 service.
        credentials (S3Credentials): Authentication credentials for the S3 service.
    """
    code: str
    name: str
    settings: S3Settings
    credentials: S3Credentials

    def __init__(self, datasource_code: str):
        """
        Initialize an S3DataSource with a specific datasource code.
        
        This constructor retrieves the data source configuration and credentials
        automatically based on the provided code.
        
        Args:
            datasource_code (str): The code identifier for the S3 data source.
            
        Raises:
            ValueError: If the data source does not exist or is not an S3 data source.
            HTTPError: If API requests for configuration or credentials fail.
        """
        self.code = datasource_code
        datasource: DataSource = get_datasource_by_code(datasource_code)
        self.settings = datasource.settings
        self.name = datasource.name
        self.credentials = get_s3_credentials(datasource_code)


class Bucket:
    """
    Provides operations for a specific S3 bucket.
    
    This class encapsulates read and write operations for a specific bucket
    within an S3-compatible data source.
    
    Attributes:
        s3_datasource (S3DataSource): The S3 data source containing this bucket.
        bucket_name (str): The name of the bucket.
        _bucket: The boto3 Bucket resource object.
    """
    s3_datasource: S3DataSource
    bucket_name: str
    _bucket: None

    def __init__(self, s3_datasource: S3DataSource, bucket_name: str):
        """
        Initialize a Bucket with a data source and bucket name.
        
        Args:
            s3_datasource (S3DataSource): The S3 data source containing this bucket.
            bucket_name (str): The name of the bucket.
        """
        self.s3_datasource = s3_datasource
        self.bucket_name = bucket_name

        # Get SSL configuration for boto3
        ssl_config = _get_ssl_config()

        # Configure boto3 client with SSL settings
        boto3_config = {}
        if not ssl_config['verify']:
            # Disable SSL verification
            boto3_config['verify'] = False
        elif ssl_config['ca_bundle']:
            # boto3 uses AWS_CA_BUNDLE and instead of setting that too, lets just pass it as a variable what we read from REQUESTS_CA_BUNDLE
            boto3_config['verify'] = ssl_config['ca_bundle']

        self._bucket = boto3.resource(
            "s3",
            endpoint_url=f"{self.s3_datasource.settings.host}:{self.s3_datasource.settings.port}",
            aws_access_key_id=self.s3_datasource.credentials.access_key,
            aws_secret_access_key=self.s3_datasource.credentials.secret_key,
            **boto3_config
        ).Bucket(name=self.bucket_name)

    def read(self, path: str) -> BytesIO:
        """
        Read an object from the bucket.
        
        Args:
            path (str): The path to the object within the bucket.
            
        Returns:
            BytesIO: A byte stream containing the object's content.
            
        Raises:
            botocore.exceptions.ClientError: If the object cannot be read.
        """

        # NGDM expects paths without leading slashes
        path = path.removeprefix("/")

        file_obj = io.BytesIO()
        try:
            self._bucket.Object(path).download_fileobj(file_obj)
            file_obj.seek(0)
        except botocore.exceptions.ClientError as error:
            logger.error(f"Failed to get {path} in {self.bucket_name}")
            raise error
        return file_obj

    def write(self, path: str, content: BytesIO):
        """
        Write an object to the bucket.
        
        Args:
            path (str): The path where the object should be stored within the bucket.
            content (BytesIO): The byte stream containing the content to write.
            
        Raises:
            botocore.exceptions.ClientError: If the object cannot be written.
        """

        # NGDM expects paths without leading slashes
        path = path.removeprefix("/")

        try:
            content.seek(0)
            self._bucket.Object(path).upload_fileobj(content)
        except botocore.exceptions.ClientError as error:
            logger.error(f"Failed to write {path} in {self.bucket_name}")
            raise error


class CassandraDataSource:
    """
    Represents a Cassandra data source with its settings and credentials.
    
    This class handles the retrieval and management of Cassandra data source 
    configuration and credentials, providing a unified interface for Cassandra operations.
    
    Attributes:
        code (str): Unique identifier code for the data source.
        name (str): Human-readable name of the data source.
        settings (CassandraSettings): Connection settings for the Cassandra cluster.
        credentials (CassandraCredentials): Authentication credentials for Cassandra.
    """
    code: str
    name: str
    settings: CassandraSettings
    credentials: CassandraCredentials

    def __init__(self, datasource_code: str):
        """
        Initialize a CassandraDataSource with a specific datasource code.
        
        This constructor retrieves the data source configuration and credentials
        automatically based on the provided code.
        
        Args:
            datasource_code (str): The code identifier for the Cassandra data source.
            
        Raises:
            ValueError: If the data source does not exist or is not a Cassandra data source.
            HTTPError: If API requests for configuration or credentials fail.
            Exception: If the credential response contains errors.
        """
        self.code = datasource_code
        datasource: DataSource = get_datasource_by_code(datasource_code)
        self.settings = datasource.settings
        self.name = datasource.name
        self.credentials = get_cassandra_credentials(datasource_code)


@dataclass
class S3Data:
    """
    Metadata describing data stored in an S3-compatible storage.
    
    Attributes:
        ds_code (str): The data source code for the S3 service.
        bucket (str): The name of the bucket containing the data.
        path (str): The path to the data within the bucket.
        ds_type (str): The data source type, always "s3".
    """
    ds_code: str
    bucket: str
    path: str
    ds_type: str = "s3"


@dataclass
class CassandraData:
    """
    Metadata describing data stored in a Cassandra database.
    
    Attributes:
        ds_code (str): The data source code for the Cassandra cluster.
        keyspace (str): The Cassandra keyspace name.
        table (str): The Cassandra table name.
        ds_type (str): The data source type, always "cassandra".
    """
    ds_code: str
    keyspace: str
    table: str
    ds_type: str = "cassandra"


@dataclass
class TextEntry:
    """
    A text entry for biography information.
    
    Attributes:
        label (str): Display label for the text entry.
        value (str): The text content.
        key (Optional[str]): Optional unique identifier for the entry.
        type (str): The entry type, always "text".
    """
    label: str
    value: str
    key: Optional[str] = None
    type: str = "text"


@dataclass
class S3PathEntry:
    """
    An S3 path entry for biography information.
    
    Attributes:
        label (str): Display label for the entry.
        data (S3Data): The S3 location metadata.
        key (Optional[str]): Optional unique identifier for the entry.
        type (str): The entry type, always "s3_path".
    """
    label: str
    data: S3Data
    key: Optional[str] = None
    type: str = "s3_path"


@dataclass
class CassandraTableEntry:
    """
    A Cassandra table entry for biography information.
    
    Attributes:
        label (str): Display label for the entry.
        data (CassandraData): The Cassandra location metadata.
        key (Optional[str]): Optional unique identifier for the entry.
        type (str): The entry type, always "cassandra_table".
    """
    label: str
    data: CassandraData
    key: Optional[str] = None
    type: str = "cassandra_table"


# Type alias for biography information entries
BiographyInfoEntry = TextEntry | S3PathEntry | CassandraTableEntry

# Type alias for a full biography information set
BiographyInfo = List[BiographyInfoEntry]
