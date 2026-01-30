"""
Job Supervisor Factory Module

This module provides a factory function for creating the appropriate JobSupervisor
implementation based on the current runtime environment. It abstracts away the details
of which JobSupervisor implementation to use, allowing client code to work with
JobSupervisors without being concerned with the specific implementation details.

The module automatically selects between development mock implementations and
production HTTP implementations based on configuration settings.
"""

from typing import Dict

from .job_supervisor_dev_mock import JobSupervisorDevMock
from .job_supervisor_abstract import JobSupervisorAbstract
from .job_supervisor_http import JobSupervisorHTTP

from ..config.config import _module_config, RunEnv


def _create_job_supervisor() -> JobSupervisorAbstract:
    """
    Factory function that creates the appropriate JobSupervisor implementation
    based on the current runtime environment.
    
    This function examines the module configuration to determine whether to create
    a development mock supervisor or a production HTTP-based supervisor. The function
    automatically retrieves all necessary configuration parameters from the module
    configuration.
    
    In development environments (RunEnv.Dev), it creates a JobSupervisorDevMock
    which simulates job supervision locally without requiring the full AltaSigma
    infrastructure.
    
    In production environments, it creates a JobSupervisorHTTP which communicates
    with the AltaSigma dashboard API to perform actual job supervision.
    
    Returns:
        JobSupervisorAbstract: An appropriate JobSupervisor implementation for the
            current environment. This will be either a JobSupervisorDevMock or a
            JobSupervisorHTTP instance, configured with values from the module
            configuration.
            
    """
    if _module_config().run_env == RunEnv.Dev:
        return JobSupervisorDevMock(
            augur_code=_module_config().job.augur_code,
            # Incorrectly typed in the library, passing a JobType instead of a string is correct
            job_type=_module_config().job.job_type,
            job_code=_module_config().job.job_code,
        )
    else:
        return JobSupervisorHTTP(
            augur_code=_module_config().job.augur_code,
            # Incorrectly typed in the library, passing a JobType instead of a string is correct
            job_type=_module_config().job.job_type,
            job_code=_module_config().job.job_code,
            dashboard_api_host=_module_config().dashboard.api_host,
            dashboard_api_port=_module_config().dashboard.api_port,
        )
