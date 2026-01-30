"""Augur Job Supervision Package

This package provides a comprehensive framework for managing job lifecycles in Augur,
including initialization, progress tracking, and completion reporting across different
execution environments.

It implements the abstract factory pattern to provide environment-specific job supervision
while maintaining a consistent interface for client code.

Modules:
    abstract: Defines the abstract interface for job supervisors through the
        JobSupervisorAbstract base class that all implementations must follow.
    
    dev_mock: A mock implementation of the job supervisor for development and testing
        environments that simulates supervision through local operations and logging.
    
    factory: Factory module that automatically selects and instantiates the appropriate
        job supervisor implementation based on the runtime environment.
    
    http: Production implementation of the job supervisor that communicates with 
        the AltaSigma dashboard API over HTTP for real-time job monitoring.
    
    report_format: Utility functions for formatting data into standardized report
        formats expected by AltaSigma, including DataFrame conversion.

Directly Exposed Classes:
    JobSupervisorAbstract: Abstract base class defining the job supervisor interface.
    JobSupervisorHTTP: HTTP implementation of the job supervisor for production use.

Client code should typically use the factory module to obtain a job supervisor instance
rather than directly instantiating specific implementations.
"""
from altasigma.jobsupervisor.job_supervisor_abstract import \
    JobSupervisorAbstract
from altasigma.jobsupervisor.job_supervisor_http import JobSupervisorHTTP
