import json
import os
import os.path
import tomllib
from collections.abc import Callable
from copy import deepcopy
from enum import StrEnum
from pathlib import Path

try:
  import yaml
except ImportError:
  yaml = None

from jinja2 import Template

from .env import get_config_from_env
from .jinja.env_factory import JinjaEnvFactory
from .utils.dicts import dict_deep_merge, dict_init_dicts_from_list


class ConfigFormat(StrEnum):
  JSON = "json"
  YAML = "yaml"
  TOML = "toml"


class ConfigTpl:
  def __init__(
    self,
    *,
    defaults: dict | None = None,
    env_var_prefix: str | None = None,
    jinja_constructor_args: dict | None = None,
    jinja_filters: dict | None = None,
    jinja_globals: dict | None = None,
  ):
    """
    A constructor for Config Builder.

    Args:
        defaults (dict | None): Default values for configuration
        env_var_prefix (str | None): if specified, environment variables with
          this prefix will be injected into config
        jinja_constructor_args (dict | None): argument for Jinja environment constructor
        jinja_globals (dict | None): globals for Jinja environment constructor
        jinja_filters (dict | None): filters for Jinja environment constructor
    """
    self.jinja_env_factory: JinjaEnvFactory = JinjaEnvFactory(
      constructor_args=jinja_constructor_args,
      globs=jinja_globals,
      filters=jinja_filters,
    )
    if defaults is None:
      defaults = {}
    self.defaults = defaults
    self.env_var_prefix = env_var_prefix

  def set_global(self, k: str, v: Callable) -> None:
    """
    Sets a global for children Jinja environments
    """
    self.jinja_env_factory.set_global(k, v)

  def set_filter(self, k: str, v: Callable) -> None:
    """
    Sets a filter for children Jinja environments
    """
    self.jinja_env_factory.set_filter(k, v)

  def build_from_files(
    self,
    paths: list[str],
    overrides: dict | None = None,
    ctx: dict | None = None,
    file_type: ConfigFormat | str | None = None,
  ) -> dict:
    """
    Renders files from provided paths.

    Args:
        paths (list[str]): Paths to configuration files. Examples:
            ['/opt/myapp/myconfig_first.cfg', '/opt/myapp/myconfig_second.cfg']
        overrides (dict | None): Overrides are applied at the very end stage after all templates are rendered
        ctx (dict | None): additional rendering context which is NOT injected into configuration
    Returns:
        dict: The rendered configuration
    """
    (defaults, ctx, overrides) = dict_init_dicts_from_list(self.defaults, ctx, overrides)

    cfg = deepcopy(defaults)
    for cfg_path_raw in paths:
      cfg_path = os.path.realpath(cfg_path_raw)
      ctx_iter = deepcopy({**cfg, **ctx})
      cfg_iter: dict = self._render_cfg_from_file(cfg_path, ctx_iter, file_type)
      cfg = dict_deep_merge(cfg, cfg_iter)

    return self._finalize_cfg(cfg, overrides)

  def build_from_str(
    self,
    s: str,
    work_dir: str | None = None,
    overrides: dict | None = None,
    ctx: dict | None = None,
    file_type: ConfigFormat | str = ConfigFormat.JSON,
  ) -> dict:
    """
    Renders config from string.

    Args:
        s (str): a Jinja template string which can be rendered into [JSON, YAML, TOML] format
        work_dir (str): a working directory.
            Include statements in Jinja template will be resolved relatively to this path
        overrides (dict | None): Overrides are applied at the very end stage after all templates are rendered
        ctx (dict | None): additional rendering context which is NOT injected into configuration
        file_type (ConfigFormat | str): the format of the string, default is JSON
    Returns:
        dict: The rendered configuration
    """
    if work_dir is None:
      work_dir = str(Path.cwd())
    (defaults, ctx, overrides) = dict_init_dicts_from_list(self.defaults, ctx, overrides)
    cfg = self._render_cfg_from_str(s=s, ctx=dict_deep_merge(defaults, ctx), work_dir=work_dir, file_type=file_type)
    return self._finalize_cfg(cfg, overrides)

  def _render_cfg_from_file(self, path: str, ctx: dict, file_type: ConfigFormat | str | None = None) -> dict:
    """
    Renders a template file into config dictionary in two steps:
    1. Renders a file as Jinja template
    2. Parses the rendered file as [JSON, YAML, TOML] template
    """
    p = Path(path)
    jinja_env = self.jinja_env_factory.get_fs_jinja_environment(p.parent)
    tpl = jinja_env.get_template(p.name)

    if file_type is None:
      ext = p.suffix.lower()
      if ext == ".json":
        file_type = ConfigFormat.JSON
      elif ext == ".toml":
        file_type = ConfigFormat.TOML
      elif ext in (".yaml", ".yml"):
        file_type = ConfigFormat.YAML
      else:
        # Fall back to JSON
        file_type = ConfigFormat.JSON

    if isinstance(file_type, str):
      file_type = ConfigFormat(file_type)

    return _render_tpl(tpl, ctx, fmt=file_type)

  def _render_cfg_from_str(
    self,
    s: str,
    ctx: dict,
    work_dir: str,
    file_type: ConfigFormat | str = ConfigFormat.JSON,
  ) -> dict:
    jinja_env = self.jinja_env_factory.get_fs_jinja_environment(work_dir)
    tpl = jinja_env.from_string(s)

    if isinstance(file_type, str):
      file_type = ConfigFormat(file_type)

    return _render_tpl(tpl, ctx, fmt=file_type)

  def _finalize_cfg(self, cfg: dict, overrides: dict | None = None) -> dict:
    """Applies the final steps (env vars and overrides) to the configuration"""
    if overrides is None:
      overrides = {}
    cfg = dict_deep_merge(cfg, get_config_from_env(self.env_var_prefix))
    return dict_deep_merge(cfg, overrides)


def _render_tpl(tpl: Template, ctx: dict, fmt: ConfigFormat = ConfigFormat.JSON) -> dict:
  tpl_rendered = tpl.render(ctx)
  if fmt == ConfigFormat.JSON:
    return json.loads(tpl_rendered)
  if fmt == ConfigFormat.TOML:
    return tomllib.loads(tpl_rendered)
  if fmt == ConfigFormat.YAML:
    if yaml is None:
      msg = "PyYAML is not installed. Please install 'configtpl[yaml]'."
      raise ImportError(msg)
    result = yaml.safe_load(tpl_rendered)
    if result is None:
      return {}
    return result

  return {}
