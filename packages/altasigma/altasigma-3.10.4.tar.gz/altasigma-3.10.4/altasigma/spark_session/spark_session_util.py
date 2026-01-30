"""
Spark Session Utility Module

This module provides utilities for creating and configuring Apache Spark sessions
in Kubernetes environments with connections to various data sources like S3 and Cassandra.
It handles the complexities of Spark configuration for container-based deployments
and authentication to secured data sources.
"""

import os
import requests
from pyspark import SparkConf
from pyspark.sql import SparkSession

from ..config.http_session import _http_session, _get_ssl_config
from ..credentials.credential_utils import _credential_utils


def _get_datasource_info(data_source_name: str):
    """
    Retrieve information for a specific data source.

    This internal function queries the data management API to get connection
    details for a named data source.

    Args:
        data_source_name (str): The name of the data source to look up.

    Returns:
        dict: A dictionary with keys:
            - 'ds_type': The datasource type ('s3' or 'cassandra')
            - 'host': The hostname (without http://)
            - 'port': The port number as string

    Raises:
        ValueError: If the datasource cannot be retrieved or does not exist.
    """
    host_url = os.environ['HOST_URL']
    access_token, _ = _credential_utils()._existing_token()

    data_sources_request = _http_session().get(f"{host_url}/dataman/datasources",
                                               headers={"Authorization": f"Bearer {access_token}"})

    if data_sources_request.status_code != 200:
        error_msg = f"Failed to retrieve datasources list. Status: {data_sources_request.status_code}, Response: {data_sources_request.text}"
        print(f"ERROR: {error_msg}")
        raise ValueError(error_msg)

    data_sources_response = data_sources_request.json()

    # use data_source_name to search for fitting data source code
    matching_sources = [entry for entry in data_sources_response if entry["name"] == data_source_name]
    if len(matching_sources) != 1:
        error_msg = f"Expected exactly 1 datasource with name '{data_source_name}', found {len(matching_sources)}. Available datasources: {[ds['name'] for ds in data_sources_response]}"
        print(f"ERROR: {error_msg}")
        raise ValueError(error_msg)

    data_source = matching_sources[0]

    return {
        'ds_type': data_source['ds_type'],
        'host': data_source["settings"]["host"],
        'port': data_source["settings"]["port"]
    }


def get_spark_session(app_name=None, data_source_names=None, cassandra_user='',
                      cassandra_password='', s3_access_key='', s3_secret_key='',
                      # opt. debug params
                      spark_namespace='as-spark',
                      spark_container_image=None,
                      spark_exec_instance='2', spark_exec_mem='1g', spark_exec_core='1', spark_jars=None,
                      config_overrides=None):
    """
    Create and configure a Spark session optimized for Kubernetes deployment.
    
    This function sets up a Spark session with appropriate configurations for
    running in a Kubernetes environment, with connections to specified data sources.
    It handles authentication for S3 and Cassandra, configures executor resources,
    and manages the necessary JAR dependencies.
    
    Args:
        app_name (str, optional): Name for the Spark application. Defaults to the hostname.
        data_source_names (list, optional): List of data source names to connect to. Defaults to empty list.
        cassandra_user (str, optional): Username for Cassandra authentication. Defaults to empty string.
        cassandra_password (str, optional): Password for Cassandra authentication. Defaults to empty string.
        s3_access_key (str, optional): Access key for S3 authentication. Defaults to empty string.
        s3_secret_key (str, optional): Secret key for S3 authentication. Defaults to empty string.
        spark_namespace (str, optional): Kubernetes namespace for Spark executors. Defaults to 'as-spark'.
        spark_container_image (str, optional): Container image for Spark executors.
            If None, uses SPARK_EXECUTOR_IMAGE environment variable (required).
        spark_exec_instance (str, optional): Number of Spark executor instances. Defaults to '2'.
        spark_exec_mem (str, optional): Memory allocation per executor. Defaults to '1g'.
        spark_exec_core (str, optional): CPU cores per executor. Defaults to '1'.
        spark_jars (list, optional): List of JAR filenames to include. Should be absolute paths. Alls jars in /opt/spark/jars are already included.
        config_overrides (dict, optional): Dictionary of configuration overrides. Defaults to empty dict.

    Returns:
        SparkSession: A configured and initialized Spark session.
        
    Raises:
        KeyError: If required environment variables (SPARK_EXECUTOR_IMAGE, HOST_URL, HOSTNAME, K8S_NAMESPACE) are not set.
        ValueError: If datasource configuration cannot be retrieved.
    """
    if config_overrides is None:
        config_overrides = {}
    if app_name is None:
        app_name = os.environ['HOSTNAME']
    if data_source_names is None:
        data_source_names = []
    if spark_container_image is None:
        spark_container_image = os.environ['SPARK_EXECUTOR_IMAGE']

    conf = SparkConf()
    conf.setMaster("k8s://https://kubernetes.default.svc.cluster.local")

    config_dict = {
        "spark.kubernetes.namespace": spark_namespace,
        "spark.kubernetes.container.image": spark_container_image,
        "spark.executor.instances": spark_exec_instance,
        "spark.executor.memory": spark_exec_mem,
        "spark.executor.cores": spark_exec_core,
        "spark.driver.blockManager.port": "7777",
        "spark.driver.port": "2222",
        "spark.driver.host": f"{os.environ['HOSTNAME']}.{os.environ['K8S_NAMESPACE']}.svc.cluster.local",
        "spark.driver.bindAddress": "0.0.0.0",
        "spark.kubernetes.executor.podTemplateFile": "/spark-executor-template/executor_template.yaml",
        "spark.kubernetes.container.image.pullSecrets": "gitlab-sigmalto-com-pullcred",
        "spark.driver.extraClassPath": "/opt/spark/jars/*"
    }
    if spark_jars is not None:
        config_dict["spark.jars"] = ",".join(spark_jars)

    cassandra_cred = {
        # Cassandra
        "spark.cassandra.auth.username": cassandra_user,
        "spark.cassandra.auth.password": cassandra_password,
    }

    s3_cred = {
        # s3
        "spark.hadoop.fs.s3a.path.style.access": "true",
        "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
        "spark.hadoop.fs.s3a.access.key": s3_access_key,
        "spark.hadoop.fs.s3a.secret.key": s3_secret_key,
        "spark.hadoop.com.amazonaws.services.s3.enableV4": "true",
        "spark.hadoop.fs.s3a.aws.credentials.provider": "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
    }

    # Use global SSL configuration if verification is disabled
    ssl_config = _get_ssl_config()
    if not ssl_config['verify']:
        s3_cred["spark.hadoop.fs.s3a.connection.ssl.enabled"] = "false"

    # add datasource params to dicts
    for ds in data_source_names:
        ds_info = _get_datasource_info(ds)

        if ds_info['ds_type'] == 's3':
            # S3 endpoint needs host:port format
            s3_cred["spark.hadoop.fs.s3a.endpoint"] = f"{ds_info['host']}:{ds_info['port']}"
            config_dict.update(s3_cred)
        elif ds_info['ds_type'] == 'cassandra':
            # Cassandra uses separate host and port
            cassandra_cred["spark.cassandra.connection.host"] = ds_info['host']
            cassandra_cred["spark.cassandra.connection.port"] = ds_info['port']
            config_dict.update(cassandra_cred)

    config_dict = config_dict | config_overrides

    for key, value in config_dict.items():
        conf.set(key, value)

    return SparkSession.builder.appName(app_name).config(conf=conf).getOrCreate()
