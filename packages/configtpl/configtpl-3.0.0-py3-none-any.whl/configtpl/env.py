import os


def _parse_env_var_value(value: str) -> object:  # noqa: PLR0911 too  many return statements
  """
  Parses a string value from an environment variable into a typed value.
  """
  if not value:
    return None

  # Values wrapped in single or double quotes are always strings
  if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
    return value[1:-1]

  # `true` and `false` are converted to corresponding Boolean values.
  if value == "true":
    return True
  if value == "false":
    return False

  # If value matches to format of integer of floating point number (consider negative values),
  # convert to corresponding numbers.
  try:
    return int(value)
  except ValueError:
    pass

  try:
    return float(value)
  except ValueError:
    pass

  return value


def get_config_from_env(env_prefix: str | None = None) -> dict:
  """
  Parses environment variables into a dictionary.
  If prefix is not provided, an empty dictionary is returned.
  """
  if env_prefix is None:
    return {}

  env_vars = {}
  prefix = f"{env_prefix}__"
  for key, value in os.environ.items():
    if key.startswith(prefix):
      path = key[len(prefix) :].lower().split("__")

      current_level = env_vars
      for part in path[:-1]:
        current_level = current_level.setdefault(part, {})
      current_level[path[-1]] = _parse_env_var_value(value)
  return env_vars
