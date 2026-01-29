#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Energinet ML python module
"""

from .settings import (  # noqa: E402
    PACKAGE_NAME,
    PACKAGE_VERSION,
)

__name__ = PACKAGE_NAME
__version__ = PACKAGE_VERSION

from .cli import main  # noqa: E402
from .core.logger import MetricsLogger  # noqa: E402
from .core.model import LoadedModel, Model, ModelArtifact, TrainedModel  # noqa: E402
from .core.project import Project  # noqa: E402
from .core.training import requires_parameter  # noqa: E402
