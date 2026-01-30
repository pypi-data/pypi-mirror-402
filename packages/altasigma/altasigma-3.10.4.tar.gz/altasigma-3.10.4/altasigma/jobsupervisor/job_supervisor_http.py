"""
HTTP Job Supervisor Module

This module provides an HTTP-based implementation of the JobSupervisorAbstract interface.
It communicates with the AltaSigma dashboard API over HTTP to handle job initialization,
progress reporting, and job completion (success or failure) operations.

This implementation is intended for use in production environments.
"""

import enum
import json
import logging
from pprint import pformat
from typing import Callable, Dict

import requests

from altasigma.config.config import _module_config
from altasigma.config.http_session import _http_session
from altasigma.credentials.credential_utils import _credential_utils
from altasigma.jobsupervisor import JobSupervisorAbstract
from altasigma.io.data_management import BiographyInfo

logger = logging.getLogger(__name__)


class JobSupervisorHTTP(JobSupervisorAbstract):
    """
    HTTP-based implementation of JobSupervisor.
    
    This class provides job supervision operations by communicating with the AltaSigma
    dashboard API over HTTP. It manages job lifecycle events including initialization,
    progress reporting, and completion (success or failure) by sending appropriate
    API requests.
    
    Attributes:
        base_url (str): The base URL for the job supervisor API endpoints.
    """

    def __init__(
            self,
            augur_code: str,
            job_type: str,
            job_code: str,
            dashboard_api_host: str,
            dashboard_api_port: int
    ):
        """
        Initialize an HTTP-based job supervisor.
        
        Args:
            augur_code (str): The code identifying the Augur instance.
            job_type (str): The type of job being supervised.
            job_code (str): The unique identifier for this specific job.
            dashboard_api_host (str): Hostname for the dashboard API.
            dashboard_api_port (int): Port number for the dashboard API. If None, the port is omitted from the URL.
        """
        super().__init__(
            augur_code=augur_code,
            job_type=job_type,
            job_code=job_code,
            dashboard_api_host=dashboard_api_host,
            dashboard_api_port=dashboard_api_port,
        )
        if dashboard_api_port is None:
            self.base_url = f"http://{dashboard_api_host}/api/jobsupervisor"
        else:
            self.base_url = f"http://{self.dashboard_api_host}:{self.dashboard_api_port}/api/jobsupervisor"

    def initialize(self, mapper_settings_fn: Callable) -> tuple[str, str, dict]:
        """
        Initialize a job by making an HTTP request to the dashboard API.
        
        This method sends a job initialization request to the API and processes
        the response to extract job settings, model code, and data source information.
        
        Args:
            mapper_settings_fn (Callable): A function that maps API-provided settings 
                to the format required by the job implementation.
                
        Returns:
            tuple[str, str, dict]: A tuple containing:
                - model_code: The code for the model to be used
                - augurdata_datasource_code: The code for the Augur data source
                - custom_settings_object: The mapped job settings
                
        Raises:
            Exception: If the API response indicates an error.
        """
        url = self.base_url + "/initialize"

        if issubclass(self.job_type.__class__, enum.Enum):
            job_type = self.job_type.to_name()
        else:
            job_type = self.job_type

        data_dict = {
            "augurCode": self.augur_code,
            "jobType": job_type,
            "jobCode": self.job_code,
        }
        data = json.dumps(data_dict)
        logger.debug(f"Request body: {data}")
        access_token, _ = _credential_utils()._existing_token()
        response = _http_session().post(
            url, data=data, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        )
        if not response.ok:
            logger.error(
                f"Response for initialize was not ok. Status: [{response.status_code}]"
            )
        response_json = response.json()
        logger.debug(f"Response body: {response_json}")

        settings = response_json["augur"]["settings"]

        model_code = response_json["model"]["code"]
        augurdata_datasource_code = response_json["datapool"]["dataSourceCode"]
        custom_settings_object = mapper_settings_fn(settings)

        logger.info("Received Job Details: \n{}".format(pformat(
            custom_settings_object if isinstance(custom_settings_object, dict) else vars(custom_settings_object))))

        return model_code, augurdata_datasource_code, custom_settings_object

    def report_progress(self, progress: float):
        """
        Report job progress to the dashboard API.
        
        Note:
            This method is deprecated. Use report_progress_steps, report_progress_step_start
            and report_progress_step_end instead.
            
        Args:
            progress (float): The job progress as a value.
        """
        logger.warning(
            "report_progress is deprecated. Use report_progress_steps, report_progress_step_start and report_progress_step_end instead")

    def report_failure(self, reason: str):
        """
        Report job failure to the dashboard API.
        
        This method sends a failure notification with the provided reason to the
        job supervisor API.
        
        Args:
            reason (str): The reason for the job failure.
            
        Returns:
            int: The HTTP status code from the API response.
        """
        logger.error("Reporting failure.")
        url = self.base_url + "/failure"
        if issubclass(self.job_type.__class__, enum.Enum):
            job_type = self.job_type.to_name()
        else:
            job_type = self.job_type
        data_dict = {
            "augurCode": self.augur_code,
            "jobType": job_type,
            "jobCode": self.job_code,
            "message": reason,
        }
        data = json.dumps(data_dict)
        access_token, _ = _credential_utils()._existing_token()
        response = _http_session().post(
            url, data=data, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        )
        return response.status_code

    def report_success(self, report: Dict, health: int | None = None, health_info: Dict | None = None, biography_info: BiographyInfo | None = None) -> int:
        """
        Report job success to the dashboard API.
        
        This method sends a success notification with the job report and optional
        health and biography information to the job supervisor API.
        
        Args:
            report (Dict): The job's output report.
            health (int | None, optional): Health indicator for the job result. Defaults to None.
            health_info (Dict | None, optional): Detailed health assessment information. Defaults to None.
            biography_info (BiographyInfo | None, optional): Biographical information about the job. Defaults to None.
            
        Returns:
            int: The HTTP status code from the API response.
            
        Raises:
            Exception: If the API response indicates an error.
        """
        url = self.base_url + "/success"
        if issubclass(self.job_type.__class__, enum.Enum):
            job_type = self.job_type.to_name()
        else:
            job_type = self.job_type
        data_dict = {
            "jobCode": self.job_code,
            "jobType": job_type,
            "augurCode": self.augur_code,
            "data": report,
        }

        # Add optional properties if set
        if health is not None:
            data_dict["health"] = health
        if health_info is not None:
            data_dict["healthInfo"] = health_info
        if biography_info is not None:
            data_dict["biographyInfo"] = biography_info

        data = json.dumps(
            data_dict, default=lambda x: x.__dict__
        )  # To decode objects as dicts
        logger.debug(f"Learning report data string: {data}")
        access_token, _ = _credential_utils()._existing_token()
        response = _http_session().post(
            url, data=data, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        )
        # This is not recoverable, and we want any callers to exit 1 when this happens
        if not response.ok:
            raise Exception(f"Error while reporting: {response.status_code} {response.text}")
        return response.status_code

    def initialize_realtime(
            self,
            mapper_settings_fn: Callable,
    ) -> tuple[str, str, dict]:
        """
        Initialize a real-time job by making an HTTP request to the dashboard API.
        
        This method is similar to initialize() but specifically for real-time job types.
        It uses a different API endpoint and payload structure compared to batch jobs.
        
        This doesn't do much differently to the batch initialize method, but since this
        does not have a job, it may be hard or not correct to unify both methods. In any
        case, both methods should take the same mapper since they load the same settings.
        
        Args:
            mapper_settings_fn (Callable): A function that maps API-provided settings 
                to the format required by the real-time job implementation.
                
        Returns:
            tuple[str, str, dict]: A tuple containing:
                - An empty string (placeholder for job code)
                - augurdata_datasource_code: The code for the Augur data source
                - custom_settings_object: The mapped job settings
                
        Raises:
            Exception: If the API response indicates an error.
        """
        url = self.base_url + "/initializeRealtime"

        data_dict = {
            "augurCode": self.augur_code,
            "modelCode": _module_config().job.model_code,
            "settingsCode": _module_config().job.settings_code
        }
        data = json.dumps(data_dict)
        logger.debug(f"Request body: {data}")

        access_token, _ = _credential_utils()._existing_token()
        response = _http_session().post(
            url, data=data, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        )
        if not response.ok:
            raise Exception(
                f"Response for initialize was not ok. Status: [{response.status_code}], Text: [{response.text}]"
            )

        response_json = response.json()
        logger.info("INITIALIZE_REALTIME RESPONSE_JSON " + str(response_json))

        settings = response_json["augur"]["settings"]

        augurdata_datasource_code = response_json["datapool"]["dataSourceCode"]
        custom_settings_object = mapper_settings_fn(settings)

        logger.info("Received Job Details: \n{}".format(pformat(
            custom_settings_object if isinstance(custom_settings_object, dict) else vars(custom_settings_object))))

        return "", augurdata_datasource_code, custom_settings_object
