"""
Constants for the Modulo client.
"""

DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
SIGNATURE_VALID_SECONDS = 300  # 5 minutes validity for signatures

# Environment variable names
ENV_API_KEY = "MODULO_API_KEY"
ENV_SERVICE_ID = "MODULO_SERVICE_ID"
ENV_PRIVATE_KEY = "MODULO_PRIVATE_KEY"
ENV_BASE_URL = "MODULO_BASE_URL"

ENVIRONMENTS = {
    "production": "https://api.bluemachines.ai/modulo",
    "staging": "https://api.staging.bluemachines.ai/modulo",
    "development": "https://api.dev.bluemachines.ai/modulo",
    "local": "http://localhost:8081",
}
