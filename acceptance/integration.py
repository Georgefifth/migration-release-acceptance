"""Explicit, reviewed project configuration. Importing it executes trusted code."""
from dataclasses import dataclass
import importlib
import inspect
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
    candidate_transactional: bool = True


def candidate_paths(config):
    if config.candidates is not None:
        return config.candidates
    return {name: config.workload.fixtures / (name + '.sql') for name in ('breaking', 'expand')}


def check_call(function, count, label):
    """Bind placeholders only; never invoke factories or application operations."""
    if inspect.iscoroutinefunction(function) or inspect.isasyncgenfunction(function):
        raise ConfigurationError(label + ' must be synchronous; the runner does not await application code.')
    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        # Some extension callables expose no signature. Runtime verification is
        # still necessary; absence of introspection is not proof of bad code.
        return
    try:
        signature.bind(*([None] * count))
    except TypeError:
        raise ConfigurationError(label + ' must accept ' + str(count) + ' positional arguments as used by the runner.') from None


def check_factory(factory):
    check_call(factory, 3, 'application_factory(version, schema, dsn)')
    if not inspect.isclass(factory):
        # A function may return any reviewed adapter. Do not call it to inspect.
        return
    dynamic = inspect.getattr_static(factory, '__getattr__', None) is not None
    for name, count in (('start', 0), ('stop', 0), ('read', 2), ('create', 3), ('update', 3)):
        try:
            member = inspect.getattr_static(factory, name)
        except AttributeError:
            if dynamic:
                continue
            raise ConfigurationError('Adapter class must declare ' + name + '(); see the adapter contract.') from None
        if isinstance(member, staticmethod):
            function, arguments = member.__func__, count
        elif isinstance(member, classmethod):
            function, arguments = member.__func__, count + 1
        elif inspect.isfunction(member):
            function, arguments = member, count + 1
        else:
            # Descriptors and instance-created methods cannot be checked without
            # executing application code. Defer these to the actual run.
            continue
        check_call(function, arguments, 'Adapter ' + name + '() (including self/cls where applicable)')


def validate(config):
    """Check declarations and readable fixtures, without constructing apps or a DB."""
    if not isinstance(config, Integration):
        raise ConfigurationError('The configuration function must return Integration(application_factory, workload).')
    if type(config.candidate_transactional) is not bool:
        raise ConfigurationError('candidate_transactional must be a boolean.')
    if not callable(config.application_factory):
        raise ConfigurationError('application_factory must be callable; do not launch applications during configuration.')
    check_factory(config.application_factory)
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
    if workload.initialize is not None:
        check_call(workload.initialize, 2, 'initialize(schema, dsn)')
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
