import importlib
import logging
from collections.abc import Iterable
from types import ModuleType

from django.apps import apps
from django.tasks import Task, task_backends
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


def get_task(task: str) -> Task | None:
    return import_string(task)


def task_classes() -> tuple[Task]:
    return tuple({backend.task_class for backend in task_backends.all()})


def task_modules(name="tasks") -> Iterable[ModuleType]:
    for app in apps.get_app_configs():
        try:
            module = importlib.import_module(f"{app.name}.{name}")
        except (ImportError, ModuleNotFoundError):
            logger.debug("No tasks found for %s", app.name)
        else:
            logger.debug("Found %s", module.__name__)
            yield module


def tasks_from_module(mod: ModuleType, TYPES):
    for key in dir(mod):
        obj = getattr(mod, key)
        if isinstance(obj, TYPES):
            yield obj
        if isinstance(obj, ModuleType):
            if mod.__package__ == obj.__package__:
                yield from tasks_from_module(obj, TYPES)


def all_tasks() -> Iterable[Task]:
    TYPES = task_classes()
    for module in task_modules():
        yield from tasks_from_module(module, TYPES)
