# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module defining custom exceptions for the qBraid runtime services module.

"""

from qbraid_core.exceptions import QbraidException


class QuantumRuntimeServiceRequestError(QbraidException):
    """Base class for errors raised by API requests made through qBraid runtime service clients."""
