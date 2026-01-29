import base64
import hashlib


def jinja_filter_split_space(s: str) -> list[str]:
  """Splits a multiline string into list of strings where each item is a line"""
  return s.strip().split()


def jinja_filter_md5(input_string: str) -> str:
  return hashlib.md5(input_string.encode()).hexdigest()


def jinja_filter_sha256(input_string: str) -> str:
  return hashlib.sha256(input_string.encode()).hexdigest()


def jinja_filter_sha512(input_string: str) -> str:
  return hashlib.sha512(input_string.encode()).hexdigest()


def jinja_filter_base64(input_string: str) -> str:
  return base64.b64encode(input_string.encode()).decode()


def jinja_filter_base64_decode(encoded_string: str) -> str:
  return base64.b64decode(encoded_string.encode()).decode()
