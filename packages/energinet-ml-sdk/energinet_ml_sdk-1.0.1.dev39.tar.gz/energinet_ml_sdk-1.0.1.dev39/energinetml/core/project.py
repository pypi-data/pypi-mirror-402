#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""[summary]
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict

from energinetml.settings import (
    DEFAULT_ENCODING,
    DEFAULT_LOCATION,
    PACKAGE_NAME,
    PACKAGE_VERSION,
)

from .configurable import Configurable
from .requirements import RequirementList


@dataclass
class Project(Configurable):
    """[summary]"""

    _CONFIG_FILE_NAME = "project.json"
    _REQUIREMENTS_FILE_NAME = "requirements.txt"

    name: str

    @classmethod
    def create(cls, *args: Any, **kwargs: Dict[str, Any]) -> Project:
        """[summary]

        Returns:
            [type]: [description]
        """
        project = super().create(*args, **kwargs)

        # Create requirements.txt file
        with open(project.requirements_file_path, "w", encoding=DEFAULT_ENCODING) as f:
            f.write(f"{PACKAGE_NAME}=={PACKAGE_VERSION}\n")

        return project

    @property
    def requirements_file_path(self) -> str:
        """Absolute path to requirements.txt file.

        Returns:
            str: [description]
        """
        return self.get_file_path(self._REQUIREMENTS_FILE_NAME)

    @cached_property
    def requirements(self) -> RequirementList:
        """Returns a list of project requirements from requirements.txt.

        Returns:
            RequirementList: [description]
        """
        if os.path.isfile(self.requirements_file_path):
            return RequirementList.from_file(self.requirements_file_path)
        else:
            return RequirementList()


# -- Machine Learning --------------------------------------------------------


@dataclass
class MachineLearningProject(Project):
    """[summary]"""

    subscription_id: str
    resource_group: str
    workspace_name: str
    vnet_name: str
    subnet_name: str
    location: str = field(default=DEFAULT_LOCATION)

    @property
    def vnet_resourcegroup_name(self) -> str:
        """The resource group where the VNET is located, typically
        the same as the workspace.

        Returns:
            str: [description]
        """
        return self.resource_group

    def default_model_path(self, model_name: str) -> str:
        """Returns default absolute path to folder where new models
        should be created at.

        Args:
            model_name (str): [description]

        Returns:
            str: [description]
        """
        return self.get_file_path(model_name)
