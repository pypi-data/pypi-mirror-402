"""
Constants for Wally Dev CLI.
"""

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR_CONFIG = 2
EXIT_ERROR_AUTH = 3
EXIT_ERROR_NETWORK = 4
EXIT_ERROR_API = 5
EXIT_ERROR_RUNTIME = 6
EXIT_INTERRUPTED = 130

# Default values
DEFAULT_TIMEOUT = 30
DEFAULT_CONNECT_TIMEOUT = 5
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF = 0.5
DEFAULT_BACKEND_URL = "https://api.wally.equallyze.com/backend/services/v0.0.1"

# Retry configuration
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

# User agent
USER_AGENT = "wally-dev/0.1.0"

# File names
CONFIG_FILE_NAME = ".wally-dev.json"
WORKSPACE_DIR_NAME = "workspace"
TESTCASES_DIR_NAME = "testCases"

# Lock status
LOCK_STATUS_LOCKED = "locked"
LOCK_STATUS_UNLOCKED = "unlocked"
