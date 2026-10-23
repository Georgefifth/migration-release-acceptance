"""Explicit, reviewed project configuration. Importing it executes trusted code."""
from dataclasses import dataclass
import importlib
import json
from pathlib import Path
import re
from typing import Callable

from .workload import Workload


class ConfigurationError(Exception):
    pass


@dataclass(frozen=True)
class Integration:
    application_factory: Callable
    workload: Workload
    candidates: dict[str, Path] | None = None


def candidate_paths(config):
    if config.candidates is not None:
        return config.candidates
    return {name: config.workload.fixtures / (name + '.sql') for name in ('breaking', 'expand')}


def validate(config):
    """Check declarations and readable fixtures, without constructing apps or a DB."""
    if not isinstance(config, Integration):
        raise ConfigurationError('The configuration function must return Integration(application_factory, workload).')
    if not callable(config.application_factory):
        raise ConfigurationError('application_factory must be callable; do not launch applications during configuration.')
    workload = config.workload
    if not isinstance(workload, Workload):
        raise ConfigurationError('workload must be a Workload instance.')
    for name in ('name', 'entity', 'application_scope'):
        if not isinstance(getattr(workload, name), str) or not getattr(workload, name).strip():
            raise ConfigurationError('Set the workload ' + name + ' to a nonempty description.')
    for name in ('initial', 'created', 'old_write', 'new_write', 'new_update', 'old_update'):
        if not isinstance(getattr(workload, name), str):
            raise ConfigurationError('Set the synthetic ' + name + ' value to a string.')
    if workload.initialize is not None and not callable(workload.initialize):
        raise ConfigurationError('initialize must be callable or None.')
    if not isinstance(workload.provenance, dict):
        raise ConfigurationError('provenance must be a JSON-serializable dictionary.')
    try:
        json.dumps(workload.provenance, allow_nan=False)
    except (TypeError, ValueError):
        raise ConfigurationError('provenance must contain finite JSON-serializable values.') from None
    if not isinstance(workload.fixtures, Path):
        raise ConfigurationError('fixtures must be a pathlib.Path rooted in your reviewed project.')
    paths = candidate_paths(config)
    if not isinstance(paths, dict) or not paths:
        raise ConfigurationError('Declare at least one candidate name and reviewed SQL path.')
    for name, path in paths.items():
        if not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', name):
            raise ConfigurationError('Candidate names must use lowercase letters, digits, underscores or hyphens, starting with a letter (maximum 64 characters).')
        if not isinstance(path, Path):
            raise ConfigurationError('Each candidate SQL path must be a pathlib.Path.')
    fixtures = [('baseline.sql', workload.fixtures / 'baseline.sql'), *paths.items()]
    for name, path in fixtures:
        try:
            content = path.read_text()
        except (OSError, UnicodeError):
            raise ConfigurationError('Cannot read fixture ' + name + '; check the configured directory and UTF-8 file.') from None
        if not content.strip():
            raise ConfigurationError('Fixture ' + name + ' is empty; provide reviewed synthetic setup or candidate SQL.')
    return config


def load(reference):
    if not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*', reference):
        raise ConfigurationError('Use an explicit reviewed Python reference: package.module:configuration_function.')
    module, name = reference.split(':')
    try:
        function = getattr(importlib.import_module(module), name)
    except Exception:
        raise ConfigurationError('Cannot import the reviewed configuration. Check its module and installed dependencies.') from None
    if not callable(function):
        raise ConfigurationError('The configuration reference must name a callable function.')
    try:
        config = function()
    except Exception:
        # Even a user-raised ConfigurationError may contain private values.
        raise ConfigurationError('Cannot load the reviewed configuration. Check its module, dependencies and prepared application files.') from None
    return validate(config)
