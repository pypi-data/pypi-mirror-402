"""
Progress Reporting Module

This module provides utilities for tracking and reporting progress in multi-step
processing tasks. It implements a structured approach to progress reporting
that includes step definitions, step activation/completion, and failure handling.

The progress reporting uses JSON-formatted messages printed to stdout, which can
be captured and processed by the Orchestration.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List
import json
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProgressStep:
    """
    Represents a defined step in a multi-step process.
    
    A ProgressStep defines a unit of work that will be tracked during execution.
    Steps have identifiers, human-readable titles, and descriptions explaining
    their purpose.
    
    Attributes:
        id (str): Unique identifier for the step.
        title (str): Human-readable title for the step.
        description (str): Detailed explanation of what the step does.
    """
    id: str
    title: str
    description: str


def formatted_now():
    """
    Get the current timestamp in ISO format with timezone information.
    
    Returns:
        str: Current timestamp in ISO 8601 format (YYYY-MM-DDTHH:MM:SS.sss+ZZ:ZZ).
    """
    return datetime.now().astimezone().isoformat()


class ProgressReporter:
    """
    Tracks and reports progress for multi-step processes.
    
    This class manages a collection of steps and their execution states,
    emitting structured JSON messages to stdout when steps start, end,
    or fail. It also performs validation to ensure steps are properly
    defined before being started or ended.
    
    Attributes:
        step_ids (set): Set of all defined step IDs.
        active_step_ids (set): Set of step IDs that are currently active/running.
    """

    def __init__(self):
        """
        Initialize a new ProgressReporter with empty step collections.
        """
        self.step_ids = set()
        self.active_step_ids = set()

    def report_progress_steps(self, progress_steps: List[ProgressStep]):
        """
        Define and report the steps that will be tracked in the process.
        
        This method should be called once at the beginning of the process to
        define all steps that will be tracked.
        
        Args:
            progress_steps (List[ProgressStep]): List of steps to be tracked.
        """
        self.step_ids = {s.id for s in progress_steps}
        msg = {
            "type": "progress_steps",
            "timestamp": formatted_now(),
            "steps": [asdict(s) for s in progress_steps]
        }
        print(json.dumps(msg))

    def report_progress_step_start(self, step_id: str):
        """
        Report that a step has started.
        
        Args:
            step_id (str): ID of the step that has started.
            
        Note:
            Warnings are logged if the step was not previously defined or
            if the step was already marked as active.
        """
        if step_id not in self.step_ids:
            logger.warning(f"Step {step_id} is not part of the steps list, but report_progress_step_start was reported for it")
        if step_id in self.active_step_ids:
            logger.warning(f"Step {step_id} is already marked as active, but report_progress_step_start was reported again")

        self.active_step_ids.add(step_id)
        msg = {
            "type": "progress_step_start",
            "timestamp": formatted_now(),
            "step": step_id,
        }
        print(json.dumps(msg))

    def report_progress_step_end(self, step_id: str):
        """
        Report that a step has completed successfully.
        
        Args:
            step_id (str): ID of the step that has completed.
            
        Note:
            Warnings are logged if the step was not previously defined or
            if the step was not marked as active.
        """
        if step_id not in self.step_ids:
            logger.warning(f"Step {step_id} is not part of the steps list, but report_progress_step_end was reported for it")
        if step_id not in self.active_step_ids:
            logger.warning(f"Step {step_id} is not marked as active, but report_progress_step_end was reported")

        if step_id in self.active_step_ids:
            self.active_step_ids.remove(step_id)

        msg = {
            "type": "progress_step_end",
            "timestamp": formatted_now(),
            "step": step_id,
        }
        print(json.dumps(msg))

    def report_progress_step_failure(self, step_id: str, error_msg: str):
        """
        Report that a step has failed with an error.
        
        Args:
            step_id (str): ID of the step that has failed.
            error_msg (str): Error message explaining the failure.
            
        Note:
            Warnings are logged if the step was not previously defined or
            if the step was not marked as active.
        """
        if step_id not in self.step_ids:
            logger.warning(f"Step {step_id} is not part of the steps list, but report_progress_step_failure was reported for it")
        if step_id not in self.active_step_ids:
            logger.warning(f"Step {step_id} is not marked as active, but report_progress_step_failure was reported")

        if step_id in self.active_step_ids:
            self.active_step_ids.remove(step_id)

        msg = {
            "type": "progress_step_end",
            "timestamp": formatted_now(),
            "step": step_id,
            "errorMsg": error_msg,
        }
        print(json.dumps(msg))


def execute_step(progress_reporter, step_id, step_function):
    """
    Execute a function with automatic progress reporting.
    
    This helper function wraps the execution of a step function with appropriate
    progress reporting calls. It reports when the step starts, and either when it
    successfully completes or when it fails with an error.
    
    Args:
        progress_reporter (ProgressReporter): The progress reporter instance.
        step_id (str): ID of the step being executed.
        step_function (Callable[[], T]): The function to execute as the step.
            This should be a lambda or function that takes no arguments.
            
    Returns:
        T: The return value from the step_function.
        
    Raises:
        Exception: Any exception raised by the step_function is re-raised after
            reporting the failure.
            
    Example:
        ```
        def run_my_step(arg1, arg2):
          return arg1, arg2

        value1, value2 = execute_step(
            progress_reporter=job_ctx.progress_reporter,
            step_id="my_step",
            step_function=lambda: run_my_step(arg1=1, arg2="2")
        )
        ```
    """
    progress_reporter.report_progress_step_start(step_id)
    try:
        return_value = step_function()
        progress_reporter.report_progress_step_end(step_id)
        return return_value
    except Exception as e:
        progress_reporter.report_progress_step_failure(step_id=step_id, error_msg=str(e))
        raise e
