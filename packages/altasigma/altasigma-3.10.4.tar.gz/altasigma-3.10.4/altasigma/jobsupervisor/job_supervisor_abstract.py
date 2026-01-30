"""
Job Supervisor Abstract Base Class Module

This module defines the abstract interface of job supervisors Augurs.
Job supervisors are responsible for managing the lifecycle of jobs, including initialization,
progress tracking, and completion (success or failure) reporting.

Concrete implementations of this interface handle different execution environments
or communication protocols for job supervision.
"""

from abc import abstractmethod
from datetime import datetime
from typing import Callable, Dict, Optional
from altasigma.io.data_management import BiographyInfo


class JobSupervisorAbstract:
    """
    Abstract base class defining the interface for job supervision.
    
    A JobSupervisor is responsible for:
    1. Initializing jobs with appropriate settings
    2. Reporting job progress to the AltaSigma system
    3. Handling job completion (success or failure)
    4. Managing job-related metadata and reports
    
    Concrete subclasses must implement the abstract methods to provide
    specific behavior for different execution environments.
    """

    def __init__(
        self,
        augur_code: str,
        job_type: str,
        job_code: str,
        dashboard_api_host: str,
        dashboard_api_port: int,
    ):
        """
        Initialize a JobSupervisor with job identification and API connection details.
        
        Args:
            augur_code (str): The code identifying the Augur instance.
            job_type (str): The type of job being supervised (e.g., "learning", "prediction").
            job_code (str): The unique identifier for this specific job.
            dashboard_api_host (str): Hostname for the dashboard API.
            dashboard_api_port (int): Port number for the dashboard API.
        """
        self.augur_code = augur_code
        self.job_type = job_type
        self.job_code = job_code
        self.dashboard_api_host = dashboard_api_host
        self.dashboard_api_port = dashboard_api_port

    @abstractmethod
    def initialize(self, jop_details_mapper_fn: Callable) -> tuple[str, str, dict]:
        """
        Initialize a new job in the dashboard.
        
        This method registers the job with the dashboard and prepares
        it for execution.
        
        Args:
            jop_details_mapper_fn (Callable): A function that maps job details 
                from the system format to the format required by the job implementation.
                
        Returns:
            tuple[str, str, dict]: A tuple containing:
                - The job code
                - The augur code
                - The mapped job details dictionary
                
        Raises:
            NotImplementedError: This abstract method must be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def report_progress(self, progress: float):
        """
        Report the current progress of the job.
        
        Args:
            progress (float): The job progress as a value.
                
        Raises:
            NotImplementedError: This abstract method must be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def report_failure(self, reason: str):
        """
        Report that the job has failed.
        
        Args:
            reason (str): A description of why the job failed.
            
        Raises:
            NotImplementedError: This abstract method must be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def report_success(
        self, report: Dict, health: int | None, health_info: Dict | None, biography_info: BiographyInfo | None
    ) -> int:
        """
        Report that the job has completed successfully.
        
        Args:
            report (Dict): A dictionary containing the job's output report.
            health (int | None): An optional numeric health indicator for the job result.
            health_info (Dict | None): Optional detailed information about the health assessment.
            biography_info (BiographyInfo | None): Optional biographical information about the job.
            
        Returns:
            int: A status code indicating the success of the reporting operation.
            
        Raises:
            NotImplementedError: This abstract method must be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def initialize_realtime(self, settings_mapper_fn: Callable) -> tuple[str, str, dict]:
        """
        Initialize a real-time job in the supervision system.
        
        Similar to initialize() but specifically for real-time job types which
        may have different initialization requirements.
        
        Args:
            settings_mapper_fn (Callable): A function that maps job settings 
                from the system format to the format required by the real-time job implementation.
                
        Returns:
            tuple[str, str, dict]: A tuple containing:
                - The job code
                - The augur code
                - The mapped job settings dictionary
                
        Raises:
            NotImplementedError: This abstract method must be implemented by subclasses.
        """
        raise NotImplementedError
