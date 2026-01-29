"""Holy Bible API Python Client

A Python client library for the Holy Bible API.
"""

from holy_bible_api.create_bible_api import create_bible_api

# Re-export all types from openapi_client for convenience
import openapi_client
from openapi_client import *

# Automatically extend __all__ with openapi_client exports plus our custom function
__all__ = ["create_bible_api"] + openapi_client.__all__