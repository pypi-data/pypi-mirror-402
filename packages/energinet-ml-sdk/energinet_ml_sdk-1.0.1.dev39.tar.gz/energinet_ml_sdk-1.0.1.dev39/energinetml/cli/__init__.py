#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" CLI module
"""

import click

try:
    from dotnetcore2 import runtime

    # Hack OS version to avoid licencing problems in azureml
    # TODO How else to get azureml Datasets working?
    # TODO Move to somewhere else?
    runtime.version = ("18", "10", "0")
except ImportError:
    pass

from energinetml.settings import PACKAGE_VERSION  # noqa: E402

from .model import model_group  # noqa: E402
from .project import project_group  # noqa: E402


@click.command()
def version():
    """
    Prints SDK version.
    """
    click.echo(PACKAGE_VERSION)


@click.group()
def main():
    """
    Click main entrypoint.
    """
    pass


main.add_command(project_group, "project")
main.add_command(model_group, "model")
main.add_command(version)
