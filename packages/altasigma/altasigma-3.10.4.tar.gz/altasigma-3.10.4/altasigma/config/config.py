"""
Python module for configuration management in AltaSigma Modules.

This module defines job types, environment settings, and configuration classes
for various components of the system.
"""
import logging
import os
import sys
import threading
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


from ..credentials.credential_utils import _credential_utils
from ..credentials.token_refresher import TokenRefresher

logger = logging.getLogger(__name__)


class JobType(Enum):
    """Enumeration of job types for Modules/Augurs.

    Attributes:
        Learning (str): Job type for learning jobs.
        Evaluation (str): Job type for evaluation jobs.
        Prediction (str): Job type for prediction jobs.
        RealtimeScoring (str): Job type for real-time prediction jobs.
    """
    Learning = "learning"
    Evaluation = "evaluation"
    Prediction = "prediction"
    RealtimeScoring = "realtime-scoring"

    @classmethod
    def from_name(cls, name):
        """Converts a string name to its corresponding JobType enum.

        Args:
            name (str): The string name of the job type.

        Returns:
            JobType: The corresponding JobType enum.

        Raises:
            ValueError: If the provided name does not match any JobType.
        """
        for enum in JobType.__members__.values():
            if enum.value == name:
                return enum
        raise ValueError(f"{name} is not a valid JobType name.")

    def to_name(self):
        """Gets the string representation of the job type.

        Returns:
            str: The string name of the job type.
        """
        return self.value

    def is_batch_job(self):
        """Determines if the job type is a batch job.

        Returns:
            bool: True if the job type is Learning, Evaluation, or Prediction, False otherwise.
        """
        return self in [JobType.Learning, JobType.Evaluation, JobType.Prediction]

    def is_passed_model_in_env_in_prod(self):
        """Determines if the job type is passed a model in the production environment.

        Returns:
            bool: True if the job type is RealtimeScoring, False otherwise.
        """
        return self in [JobType.RealtimeScoring]

    def is_passed_model_in_env_in_dev(self):
        """Determines if the job type is passed a model in the development environment.

        Returns:
            bool: True if the job type is Evaluation, Prediction, or RealtimeScoring, False otherwise.
        """
        return self in [JobType.Evaluation, JobType.Prediction, JobType.RealtimeScoring]


class RunEnv(Enum):
    """Enumeration of running environments.

    Attributes:
        Dev (str): Development environment.
        Prod (str): Production environment.
    """
    Dev = "dev"
    Prod = "prod"

    @classmethod
    def from_name(cls, name):
        """Converts a string name to its corresponding RunEnv enum.

        Args:
            name (str): The string name of the run environment.

        Returns:
            RunEnv: The corresponding RunEnv enum.

        Raises:
            ValueError: If the provided name does not match any RunEnv.
        """
        for enum in RunEnv.__members__.values():
            if enum.value == name:
                return enum
        raise ValueError(f"{name} is not a valid RunEnv name.")

    def to_name(self):
        """Gets the string representation of the run environment.

        Returns:
            str: The string name of the run environment.
        """
        return self.value


@dataclass()
class JobConfig:
    """Configuration for a job.

    Attributes:
        augur_code (str): Identifier for the augur.
        job_type (JobType): Type of the job.
        job_code (str | None): Identifier for the job, None if not a batch job.
        model_code (str, optional): Identifier for the model. None at the start if JobType.Learning.
            Defaults to None.
        settings_code (str, optional): Identifier for settings. Only set for realtime_prediction. 
            Defaults to None.
        realtime_server_host (str, optional): Host for the realtime server. Defaults to None.
        realtime_server_port (str, optional): Port for the realtime server. Defaults to None.
    """
    augur_code: str
    job_type: JobType
    # None if not a batch job
    job_code: str | None
    # None at the start if JobType.Learning, because that creates a model_code, which will be received from the JobSupervisor
    model_code: str = None
    # Only set for realtime_prediction since that needs a stable identifier
    settings_code: str = None
    realtime_server_host: str = None
    realtime_server_port: str = None


@dataclass(frozen=True)
class DashboardConfig:
    """Configuration for the dashboard API.

    Attributes:
        api_host (str): Hostname for the dashboard API.
        api_port (int): Port number for the dashboard API.
    """
    api_host: str
    api_port: int


@dataclass(frozen=True)
class DataManConfig:
    """Configuration for the data management API.

    Attributes:
        api_host (str): Hostname for the data management API.
        api_port (int): Port number for the data management API.
    """
    api_host: str
    api_port: int


def generate_dev_job_code(job_type: JobType) -> str:
    """Generates a job code for development environment.

    Creates a job code based on current timestamp and job type.

    Args:
        job_type (JobType): Type of the job.

    Returns:
        str: A generated job code string.
    """
    return f'{datetime.now().strftime("%Y%m%dT%H%M%SZ")}_{job_type.to_name().upper()}'


@dataclass
class ModuleConfig:
    """Main configuration class for the module.

    This class holds all configuration parameters for the module,
    including job, dashboard, and data management configurations.

    Attributes:
        run_env (RunEnv): Running environment, either "dev" or "prod".
        job (JobConfig): Job configuration.
        dashboard (DashboardConfig | None): Dashboard API configuration.
        data_man (DataManConfig | None): Data management API configuration.
        package_log_level (int): Logging level for the package.
        root_log_level (int): Root logging level.
    """
    # "dev" | "prod"
    run_env: RunEnv

    job: JobConfig
    dashboard: DashboardConfig | None
    data_man: DataManConfig | None

    package_log_level: int
    root_log_level: int

    def __init__(self):
        """Initializes a ModuleConfig instance.

        Loads configuration from environment variables and sets up the necessary
        configurations for job processing, dashboard, and data management.
        """
        # General config parameters
        realtime_server_host = os.environ.get("JOB_ARG_REALTIME_SERVER_HOST", "0.0.0.0")
        realtime_server_port = os.environ.get("JOB_ARG_REALTIME_SERVER_PORT", 5000)

        # Always given
        self.run_env = RunEnv.from_name(os.environ["JOB_ENV"])
        job_type = JobType.from_name(os.environ["JOB_ARG_JOB_TYPE"])

        # Always either set, can be generated or not required
        augur_code = None
        if self.run_env == RunEnv.Prod:
            augur_code = os.environ["JOB_ARG_AUGUR_CODE"]
        job_code = None
        if job_type.is_batch_job():
            if self.run_env == RunEnv.Prod:
                job_code = os.environ["JOB_ARG_JOB_CODE"]
            elif self.run_env == RunEnv.Dev:
                job_code = generate_dev_job_code(job_type)

        model_code = None
        if (self.run_env == RunEnv.Prod and job_type.is_passed_model_in_env_in_prod()) or (
                self.run_env == RunEnv.Dev and job_type.is_passed_model_in_env_in_dev()):
            model_code = os.environ["JOB_ARG_MODEL_CODE"]

        settings_code = None
        if self.run_env == RunEnv.Prod and job_type == JobType.RealtimeScoring:
            settings_code = os.environ["JOB_ARG_SETTINGS_CODE"]

        self.job = JobConfig(
            augur_code=augur_code,
            job_type=job_type,
            job_code=job_code,
            model_code=model_code,
            settings_code=settings_code,
            realtime_server_host=realtime_server_host,
            realtime_server_port=realtime_server_port
        )
        if self.run_env == RunEnv.Prod:
            self.dashboard = DashboardConfig(os.environ["DASHBOARD_API_HOST"], os.environ["DASHBOARD_API_PORT"])
        self.data_man = _data_man_config()

        # In Code Capsule run jobs this is actually added by the orchestration, but it's also just hardcoded there.
        # Seems pointless to add it to the augur jobs too, just to satisfy the way the CredentialUtils is written
        os.environ["CLIENT_ID"] = "altasigma-frontend"
        if self.run_env == RunEnv.Dev:
            # In the workbench we need to override some things to make it fit with the CredentialsUtils, which otherwise would assume the Code Capsule + Device Auth Flow
            # Write the refresh token into the tmp file, because we neither do the device flow, nor have the mounted secret with a refresh token
            refresh_token = os.environ.get("AS_TOKEN")
            _credential_utils()._write_tokens_to_file("", refresh_token)

            # Fix client secret for non-device auth flow
            try:
                del os.environ['CLIENT_SECRET']
            except Exception as e:
                logger.warning(f"Unexpected error deleting environment variable CLIENT_SECRET: {e}")

        TokenRefresher().schedule_refresh()


module_config = None
data_man_config = None

def _module_config():
    """Gets or creates the module configuration.

    Returns:
        ModuleConfig: The module configuration instance.
    """
    global module_config
    if module_config is not None:
        return module_config
    else:
        module_config = ModuleConfig()
        return module_config

def _data_man_config():
    """Gets or creates the data management configuration.

    Returns:
        DataManConfig: The data management configuration instance.
    """
    global data_man_config
    if data_man_config is not None:
        return data_man_config
    else:
        data_man_config = DataManConfig(os.environ["DATA_MAN_API_HOST"], os.environ["DATA_MAN_API_PORT"])
        return data_man_config