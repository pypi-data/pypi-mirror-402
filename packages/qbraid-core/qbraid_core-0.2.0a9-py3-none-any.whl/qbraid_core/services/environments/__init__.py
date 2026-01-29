# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module providing utilities for interfacing with qBraid environments

.. currentmodule:: qbraid_core.services.environments

Classes
----------

.. autosummary::
   :toctree: ../stubs/

   EnvironmentConfig
   EnvironmentManagerClient

Exceptions
------------

.. autosummary::
   :toctree: ../stubs/

   EnvironmentServiceRequestError

"""
from .client import EnvironmentManagerClient
from .create import create_local_venv
from .exceptions import (
    EnvironmentDownloadError,
    EnvironmentExtractionError,
    EnvironmentInstallError,
    EnvironmentNotFoundError,
    EnvironmentOperationError,
    EnvironmentRegistryError,
    EnvironmentServiceRequestError,
    EnvironmentValidationError,
    QbraidEnvironmentError,
)
from .kernels import add_kernels, get_all_kernels, remove_kernels
from .magic import add_magic_config, remove_magic_config
from .packages import pip_freeze, pip_install, pip_uninstall
from .paths import (
    find_python_in_env,
    get_default_envs_paths,
    get_env_path,
    get_next_tmpn,
    get_tmp_dir_names,
    which_python,
)
from .registry import (
    EnvironmentEntry,
    EnvironmentRegistryManager,
    get_current_platform,
    verify_python_executable,
)
from .schema import EnvironmentConfig
from .state import install_status_codes, update_state_json
from .validate import is_valid_env_name, is_valid_slug

__all__ = [
    "EnvironmentConfig",
    "EnvironmentEntry",
    "EnvironmentManagerClient",
    "EnvironmentRegistryManager",
    "QbraidEnvironmentError",
    "EnvironmentServiceRequestError",
    "EnvironmentOperationError",
    "EnvironmentDownloadError",
    "EnvironmentExtractionError",
    "EnvironmentInstallError",
    "EnvironmentNotFoundError",
    "EnvironmentRegistryError",
    "EnvironmentValidationError",
    "create_local_venv",
    "add_magic_config",
    "remove_magic_config",
    "find_python_in_env",
    "get_current_platform",
    "get_default_envs_paths",
    "get_env_path",
    "get_next_tmpn",
    "get_tmp_dir_names",
    "verify_python_executable",
    "which_python",
    "install_status_codes",
    "update_state_json",
    "is_valid_env_name",
    "is_valid_slug",
    "get_all_kernels",
    "add_kernels",
    "remove_kernels",
    "pip_install",
    "pip_uninstall",
    "pip_freeze",
]
