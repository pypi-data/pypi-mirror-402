import os
import subprocess
import uuid
from pathlib import Path

ERR_NO_VAL_PROVIDED = "An environment variable '{name}' is not set and no default value is provided."


def jinja_global_cmd(cmd: str) -> str:
  """
  Runs a system command provided as argument and returns the output

  Args:
      cmd (str): a command to execute
  """
  result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
  return result.stdout


def jinja_global_cwd() -> str:
  """
  Returns the current working directory
  """
  return str(Path.cwd())


def jinja_global_env(name: str, default: str | None = "") -> str | None:
  """
  Returns value of an environment variable

  Args:
      name (str): name of environment variable
      default (str | None): a default value to return
  """
  v = os.getenv(name, default)
  if v is None:
    raise ValueError(ERR_NO_VAL_PROVIDED.format(name=name))
  return v


def jinja_global_file(path: str) -> str:
  """
  Returns contents of file

  Args:
      path (str): path to file
  """
  with Path.open(path) as f:
    return f.read()


def jinja_global_uuid() -> str:
  """
  Generates UUID
  """
  return str(uuid.uuid4())
