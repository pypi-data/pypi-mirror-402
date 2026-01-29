def dict_deep_merge(*dicts: dict[str, object]) -> dict[str, object]:
  """
  Deep merge multiple dictionaries recursively.
  Values in later dictionaries overwrite those in earlier ones.
  This function does not update any dictionary by reference.
  """

  def merge_two_dicts(d1: dict[str, object], d2: dict[str, object]) -> dict[str, object]:
    merged = d1.copy()
    for key, value in d2.items():
      if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
        merged[key] = merge_two_dicts(merged[key], value)
      else:
        merged[key] = value
    return merged

  result = {}
  for d in dicts:
    result = merge_two_dicts(result, d)

  return result


def dict_init_dicts_from_list(*ds: dict | None) -> tuple[dict]:
  """
  Initializes dictionaries.
  Returns an original dictionary for each item if dictionary is not None.
  Falls back to empty dict if argument is None.
  """
  return tuple(d if d is not None else {} for d in ds)
