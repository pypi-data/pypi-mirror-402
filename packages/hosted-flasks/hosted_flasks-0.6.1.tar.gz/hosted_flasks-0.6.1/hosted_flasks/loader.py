import logging

import os
import sys

from pathlib import Path
import markdown

import yaml

from importlib.util import spec_from_file_location, module_from_spec

from dataclasses import dataclass, field
from typing import Dict, List

from flask import Flask

from hosted_flasks             import statistics
from hosted_flasks.monkeypatch import Environment
from hosted_flasks.utils       import ensure_is_list

logger = logging.getLogger(__name__)

apps = []

@dataclass
class HostedFlask:
  name         : str

  path         : List[str] = None
  hostname     : List[str] = None

  imports      : Dict  = field(default_factory=dict)
  app          : str   = "app"

  handler      : Flask = field(repr=False, default=None)
  environ      : Dict  = None

  track        : List[str] = field(default_factory=list)
  log          : statistics.LogConfig = field(default_factory=dict)
  exclude      : statistics.Exclusions = field(default_factory=dict)

  hide         : bool  = False
  title        : str   = None
  description  : str   = None
  image        : str   = None
  github       : str   = None
  docs         : str   = None

  def __post_init__(self):
    if not self.path and not self.hostname:
      logger.fatal(f"⛔️ {self.name} needs at least one path or one hostname.")
      return

    # ensure path and hostname are lists
    self.path     = ensure_is_list(self.path)
    self.hostname = ensure_is_list(self.hostname)

    if not self.imports:
      raise ValueError("specify at least 1 module to import from")

    # ensure all imported paths are valid
    for name, path in self.imports.items():
      self.imports[name] = Path(path).resolve()

    # we need to add app to apps before loading the handler, because else the
    # monkeypatched os.environ.get won't be able to correct handle calls to it
    # at the time of loading the handler
    apps.append(self)

    logger.debug(f"before handler: {self}")

    # if the handler isn't provided, load it from the source
    if not self.handler:
      self.load_handler()

    # without a handler, we remove ourself from the apps
    if not self.handler:
      logger.fatal(f"⛔️ an app needs a handler: {self.name}")
      apps.remove(self)
      return

    # instantiate log configuration
    self.log = statistics.LogConfig(**self.log)

    # instantiate Exclusions
    self.exclude = statistics.Exclusions(self.exclude)

    # install a tracker
    if self.track:
      statistics.track(self)

  @property
  def appname(self):
    return self.app.split(":", 1)[-1]  # app or name:app or name.sub:app

  @property
  def appmodule(self):
    parts = self.app.split(":")
    parts.pop() # name
    if len(parts) == 1:
      return parts[0]
    # no module name explicitly provided, use that of the imported module
    if len(self.imports) == 1:
      return list(self.imports.keys())[0]
    raise ValueError("no module name provided in app setting, multiple loaded")

  def load_handler(self):
    # create a fresh monkeypatched environment scoped to the app name
    self.environ = Environment.scope(self.name)

    def import_module(name, module_path):
      spec = spec_from_file_location(name, module_path)
      mod = module_from_spec(spec)
      sys.modules[name] = mod
      spec.loader.exec_module(mod)
      return mod

    # import all required modules and extract the flask app as handler
    imported = {}
    for name, path in self.imports.items():
      try:
        imported[name] = import_module(name, path)
      except FileNotFoundError:
        logger.warning(f"😞 {name}: {path} doesn't exist")
      except Exception:
        logger.exception(f"😞 {name}: {path} failed to load due to")

    try:
      mod = imported[self.appmodule]
    except KeyError:
      return

    # extract the handler from the mod using the app configuration
    # app = module_name : app_variable_name
    # if only one module is loaded, it can be used as implicit default
    # if no name is provided, it defaults to app
    try:
      self.handler = getattr(mod, self.appname)
    except AttributeError:
      logger.warning(f"😞  path doesn't provide flask object: {self.app}")

def get_config(config=None):
  if not config:
    config = os.environ.get("HOSTED_FLASKS_CONFIG", Path() / "hosted-flasks.yaml")

  try:
    with open(config) as fp:
      return yaml.safe_load(fp)
  except FileNotFoundError:
    raise ValueError(f"💀 I need a config file. Tried: {config}")

def get_apps(config=None, force=False):
  global apps

  if not config:
    config = os.environ.get("HOSTED_FLASKS_CONFIG", Path() / "hosted-flasks.yaml")

  if force:
    apps.clear()

  # lazy load the apps
  if not apps:
    for name, settings in get_config(config)["apps"].items():
      settings["description"] = markdown.markdown(settings.pop("description", ""))
      add_app(name, **settings)
  return apps

def add_app(name, **kwargs):
  app = HostedFlask(name, **kwargs)  # adds self to global apps list
  logger.info(f"🌍 loaded app: {app.name}")
