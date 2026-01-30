"""
File System Operations Module

This module provides utilities for managing file system operations related to job runs,
reports, settings, and augur data. It handles directory creation, file reading/writing,
and job/model code management.

The module establishes standardized paths and file naming conventions to maintain
consistent data organization across the application.
"""

from datetime import datetime
import json
from typing import Dict, Optional
from pathlib import Path

# Standard paths used throughout the application
runs_path = "asruns"
report_file_name = "report.json"
settings_file_name = "augur_settings.json"
augurdata_path = "augurdata"


def ensure_run_dir(job_code: str):
    """
    Ensure that a job run directory exists for the given job code.
    
    Creates the directory structure for a specific job run if it doesn't already exist.
    
    Args:
        job_code (str): The unique identifier code for the job run.
    """
    path = Path(runs_path) / Path(job_code)
    path.mkdir(parents=True, exist_ok=True)


def ensure_augurdata_dir():
    """
    Ensure that the augur data directory exists.
    
    Creates the directory for storing augur data if it doesn't already exist.
    """
    Path(augurdata_path).mkdir(exist_ok=True)


def create_report(job_code: str, report: Dict):
    """
    Create and save a job report file.
    
    Writes the report dictionary to a standardized JSON file in the job's directory.
    
    Args:
        job_code (str): The unique identifier code for the job run.
        report (Dict): The report data to be saved.
    """
    path = Path(runs_path) / Path(job_code) / Path(report_file_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f)


def read_settings() -> Dict:
    """
    Read and parse the augur settings file.
    
    Loads the settings from the standard settings JSON file.
    
    Returns:
        Dict: The parsed settings dictionary.
        
    Raises:
        FileNotFoundError: If the settings file doesn't exist.
        json.JSONDecodeError: If the settings file contains invalid JSON.
    """
    path = Path(runs_path) / Path(settings_file_name)
    with open(path, "r") as f:
        return json.load(f)


def time_from_learning(name: str) -> datetime:
    """
    Extract the timestamp from a learning job name.
    
    Parses the job name to extract the datetime when the learning job was created.
    
    Args:
        name (str): The name of the learning job, following the format "YYYYMMDD_HHMMSS_LEARNING".
        
    Returns:
        datetime: The parsed datetime object representing when the job was created.
        
    Raises:
        ValueError: If the name doesn't follow the expected format.
    """
    return datetime.strptime(name[:-len("_LEARNING")], "%Y%m%d_%H%M%S")


def latest_model_code() -> Optional[str]:
    """
    Return the latest learning job code which is also the model code for that job
    
    Scans the runs directory for learning jobs and returns the code of the most recent one,
    which also serves as the model code for that job.
    
    Returns:
        Optional[str]: The job code of the most recent learning job, or None if no learning
                     jobs are found.
    """
    learning_jobs_with_time = [(time_from_learning(p.name), p) for p in Path(runs_path).glob("*_LEARNING/")]
    if len(learning_jobs_with_time) > 0:
        learning_jobs_with_time.sort(key=lambda x: x[0], reverse=True)
        return learning_jobs_with_time[0][1].name
    else:
        return None