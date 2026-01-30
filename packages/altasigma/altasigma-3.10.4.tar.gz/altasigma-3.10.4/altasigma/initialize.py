from .io.augurdata import _augurdata, AugurData
from .config.config import _module_config, ModuleConfig, JobType
from .jobsupervisor.job_supervisor_helpers import _create_job_supervisor
from .jobsupervisor.job_supervisor_abstract import JobSupervisorAbstract
from dataclasses import dataclass


@dataclass
class AltaSigma:
    augurdata: AugurData
    config: ModuleConfig
    job_supervisor: JobSupervisorAbstract
    settings: dict


def initialize(settings_mapper_fn) -> AltaSigma:
    job_supervisor = _create_job_supervisor()
    if _module_config().job.job_type.is_batch_job():
        model_code, augurdata_datasource_code, custom_settings_object = job_supervisor.initialize(settings_mapper_fn)
    elif _module_config().job.job_type == JobType.RealtimeScoring:
        _, augurdata_datasource_code, custom_settings_object = job_supervisor.initialize_realtime(settings_mapper_fn)
    # This means it was passed a model code in the env and just received one.
    if _module_config().job.model_code is None:
        _module_config().job.model_code = model_code
    _augurdata()._initialize(augurdata_datasource_code)
    return AltaSigma(_augurdata(), _module_config(), job_supervisor, custom_settings_object)
