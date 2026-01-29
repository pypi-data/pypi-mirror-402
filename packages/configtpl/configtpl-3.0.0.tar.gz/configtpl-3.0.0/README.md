# configtpl

This library builds configuration in two stages:

1. Renders the provided configuration as Jinja templates
1. Parses the rendered data as file with the specified format

# Features

- Uses Jinja2 capabilities to build a dynamic configuration
- Multiple configuration files might be passed. The library merges all of them into single config.
- Basic confuration includes Jinja functions and filters for general-purpose tasks:
  - Reading the environment variables
  - Execution of system commands
  - Hashing
- Reading parameters from environment variables
- Builds the configuration from files (`build_from_files` method) and from strinngs (`build_from_str` method)
- If the environment variable prefix is provided, merges the corresponding environment variables into the configuration.

# Standard features

## Filters

In addition to [Jinja buildin filters](https://tedboy.github.io/jinja2/templ14.html#list-of-builtin-filters), the library provides the following ones:


| Filter        | Description                                               |
|---------------|-----------------------------------------------------------|
| base64        | Base64 encoding                                           |
| base64_decode | Base64 decoding                                           |
| md5           | MD5 hash                                                  |
| sha256        | SHA-256 hash                                              |
| sha512        | SHA-512 hash                                              |
| split_space   | Splits a string with space separator into list of strings |

## Functions

See also [List of Global Functions](https://tedboy.github.io/jinja2/templ16.html#list-of-global-functions) on Jinja page

| Function                      | Description                                                    |
|-------------------------------|----------------------------------------------------------------|
| cmd(cmd: str)                 | Executes a system command and returns the standard output      |
| cwd()                         | Returns the current working directory                          |
| env(name: str, default: str)  | Returns the value of enviroment variable `name` if it exists,  |
|                               | or falls back to `default` value otherwise                     |
| file(path: str)               | Reads the file and returns the contents                        |
| uuid                          | Generates a UUID e.g `1f6c868d-f9b7-4d3f-b7c9-48048b065019`    |

# Precendence

1. Defaults
1. Configuration from given files or string
1. Environment variables, if variable prefix is provided
1. Overrides

# Examples

_You try run this example in the [docs/examples/readme]() directory by running the `run.sh` script._

The [functional tests folder](tests/functional) might be useful for more examples.

A very simple example of usage is provided below:
_This example uses YAML format which requires the yaml extra to be installed._

```yaml
# my_first_config.cfg
{% set my_val = "abc" %}
app:
  param_env: "{{ env('MY_ENV_VAR', 'default') }}"
  param1: "{{ my_val }}"
```

```yaml
# my_second_config.cfg
app:
  param2: def
  param3: "{{ app.param1 }}123"
hash: "{{ app.param1 | md5 }}"
override: test
param1_rev: "{{ app.param1 | str_rev }}"
param1_duplicated: "{{ str_duplicate(app.param1, 3) }}"

```


```python
# app.py
import json

from configtpl.main import ConfigTpl, ConfigFormat


def filter_str_rev(value: str) -> str:
  return value[::-1]


def function_str_duplicate(value: str, n_times: int) -> str:
  return value * n_times


builder = ConfigTpl(
  defaults={"default": "default_value"},
  env_var_prefix="MY_APP",
  jinja_globals={
    "str_duplicate": function_str_duplicate,
  },
  jinja_filters={
    "str_rev": filter_str_rev,
  },
)
cfg = builder.build_from_files(
  paths=["my_first_config.cfg", "my_second_config.cfg"],
  overrides={"override": "overridden"},
  file_type=ConfigFormat.YAML,
)
print(json.dumps(cfg, indent=2))  # noqa: T201

```

```bash
# Execution

MY_ENV_VAR=testing MY_APP__NESTED__VAR=hello python ./app.py

# output
{
  "default": "default_value",
  "app": {
    "param_env": "testing",
    "param1": "abc",
    "param2": "def",
    "param3": "abc123"
  },
  "hash": "900150983cd24fb0d6963f7d28e17f72",
  "override": "overridden",
  "param1_rev": "cba",
  "param1_duplicated": "abcabcabc",
  "nested": {
    "var": "hello"
  }
}
```
