"""
Configuration Module for EMQX MCP Server

This module loads configuration parameters from environment variables,
specifically for connecting to the EMQX Cloud or self-hosted EMQX API.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# EMQX Cloud API configuration. 
# These variables should be set in the environment or .env file
EMQX_API_URL = os.getenv("EMQX_API_URL", "")  # Base URL for the EMQX HTTP API
EMQX_API_KEY = os.getenv("EMQX_API_KEY", "")  # API key for authentication
EMQX_API_SECRET = os.getenv("EMQX_API_SECRET", "")  # API secret for authentication