"""SDK constants"""
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE_URL = os.getenv("CUBE_BASE_URL", "https://api.usecube.co")
DEFAULT_API_VERSION = os.getenv("CUBE_API_VERSION", "v1")
SDK_VERSION = "0.1.0"
