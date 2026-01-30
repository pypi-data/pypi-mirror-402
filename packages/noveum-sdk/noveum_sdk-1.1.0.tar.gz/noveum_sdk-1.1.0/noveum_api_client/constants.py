"""
Exception message constants for the Noveum API Client.

IMPORTANT: These messages are part of the public API contract.
Changing them may break customer code that depends on specific error messages.
Always consider backwards compatibility when modifying these strings.
"""

# =============================================================================
# UnexpectedStatus Exception Messages
# =============================================================================

# Template for unexpected status code errors
# Placeholders: {status_code}, {content}
UNEXPECTED_STATUS_MESSAGE = "Unexpected status code: {status_code}\n\nResponse content:\n{content}"
