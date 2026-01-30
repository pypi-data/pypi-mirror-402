"""
Development Mock Job Supervisor Module

This module provides a mock implementation of the JobSupervisorAbstract for development
and testing purposes. Instead of connecting to an actual dashboard API, it performs local
file operations and logging to simulate job supervision functionality.

This implementation is intended for use in development environments where the actual
AltaSigma infrastructure may not be available.
"""

import logging
from typing import Callable, Dict, Optional

from ..config.config import _module_config
from ..io.files import create_report, read_settings

from altasigma.jobsupervisor import JobSupervisorAbstract
from altasigma.io.data_management import BiographyInfo

logger = logging.getLogger(__name__)


class JobSupervisorDevMock(JobSupervisorAbstract):
    """
    Development mock implementation of the JobSupervisor.
    
    This class provides simplified implementations of job supervision operations
    that work in local development environments without requiring connections
    to the AltaSigma dashboard API. It uses local file storage and logging
    to simulate the behavior of a real job supervisor.
    """

    def __init__(
        self,
        augur_code: str,
        job_type: str,
        job_code: str,
    ):
        """
        Initialize a development mock job supervisor.
        
        Args:
            augur_code (str): The code identifying the Augur instance.
            job_type (str): The type of job being supervised (e.g., "learning", "prediction").
            job_code (str): The unique identifier for this specific job.
        
        Note:
            Unlike the real implementations, this mock does not require
            dashboard API connection parameters.
        """
        super().__init__(
            augur_code=augur_code,
            job_type=job_type,
            job_code=job_code,
            dashboard_api_host=None,
            dashboard_api_port=None,
        )

    def initialize(self, mapper_settings_fn: Callable):
        """
        Initialize a job using local settings.
        
        Reads settings from the local settings file and maps them to
        the format expected by the job implementation.
        
        Args:
            mapper_settings_fn (Callable): A function that maps settings from
                the system format to the format required by the job implementation.
                
        Returns:
            tuple[str, str, dict]: A tuple containing:
                - The job code (from module configuration)
                - An empty string (placeholder for augur code)
                - The mapped settings dictionary
        """
        settings = read_settings()

        custom_settings_object = mapper_settings_fn(settings)
        model_code = _module_config().job.job_code

        return model_code, "", custom_settings_object

    def report_progress(self, progress: float):
        """
        Mock implementation of progress reporting.
        
        In the development mock, progress reporting is a no-op.
        In a real implementation, this would update the job's progress in the dashboard.
        
        Args:
            progress (float): The job progress as a value.
        """
        # This method is required by the abstract class but has no implementation in the mock
        pass

    def report_failure(self, reason: str):
        """
        Report job failure by logging an error message.
        
        Args:
            reason (str): The reason for the job failure.
        """
        logger.error("Reporting failure.")

    def report_success(self, report: Dict, health: int | None = None, health_info: Dict | None = None, biography_info: BiographyInfo | None = None):
        """
        Report job success by saving the report to a local file.
        
        Args:
            report (Dict): The job's output report.
            health (int | None, optional): Health indicator for the job result. Defaults to None.
            health_info (Dict | None, optional): Detailed health assessment information. Defaults to None.
            biography_info (BiographyInfo | None, optional): Biographical information about the job. Defaults to None.
            
        Returns:
            int: Always returns 0 to indicate success.
        """
        create_report(self.job_code, report)
        return 0

    def initialize_realtime(self, settings_mapper_fn: Callable) -> tuple[str, str, dict]:
        """
        Initialize a real-time job using local settings.
        
        Similar to initialize() but specifically for real-time job types.
        
        Args:
            settings_mapper_fn (Callable): A function that maps settings from
                the system format to the format required by the real-time job implementation.
                
        Returns:
            tuple[str, str, dict]: A tuple containing:
                - An empty string (placeholder for job code)
                - An empty string (placeholder for augur code)
                - The mapped job settings dictionary
        """
        settings = read_settings()

        job_details = settings_mapper_fn(settings)

        return "", "", job_details