"""SDK constants and configuration defaults.

This module centralizes magic numbers and default values used throughout the SDK.
"""

# ==============================================================================
# Timeouts (seconds)
# ==============================================================================

# Default request timeout
DEFAULT_TIMEOUT = 30.0

# Buffer added to command timeout for HTTP request (accounts for network overhead)
COMMAND_TIMEOUT_BUFFER = 5

# Maximum timeout allowed for commands
MAX_COMMAND_TIMEOUT = 300

# Minimum timeout allowed for commands
MIN_COMMAND_TIMEOUT = 1

# Default wait timeout for bot to reach running state
DEFAULT_ENSURE_RUNNING_TIMEOUT = 30.0


# ==============================================================================
# Pagination
# ==============================================================================

# Default page size for list operations
DEFAULT_PAGE_LIMIT = 50

# Maximum page size for command history
MAX_HISTORY_LIMIT = 500

# Default pagination offset
DEFAULT_OFFSET = 0


# ==============================================================================
# Discord Limits
# ==============================================================================

# Maximum messages to fetch in a single request
MAX_MESSAGE_HISTORY = 100

# Maximum bans to fetch in a single request
MAX_BANS_LIMIT = 100

# Maximum members to fetch in a single request
MAX_MEMBERS_LIMIT = 100


# ==============================================================================
# Retry Configuration
# ==============================================================================

# Default number of retry attempts for failed requests
DEFAULT_MAX_RETRIES = 3

# Default delay between retries (seconds)
DEFAULT_RETRY_DELAY = 1.0


# ==============================================================================
# Webhook Signature Verification
# ==============================================================================

# Maximum age of a webhook payload before it's considered stale (seconds)
MAX_WEBHOOK_AGE_SECONDS = 300

# Allowed clock skew for webhook timestamps (seconds)
WEBHOOK_CLOCK_SKEW_TOLERANCE = 60


# ==============================================================================
# HTTP Status Codes
# ==============================================================================

# Status codes that should trigger automatic retry
RETRYABLE_STATUS_CODES = (502, 503, 504)

# Rate limit status code
RATE_LIMIT_STATUS_CODE = 429

# Server error threshold
SERVER_ERROR_THRESHOLD = 500
