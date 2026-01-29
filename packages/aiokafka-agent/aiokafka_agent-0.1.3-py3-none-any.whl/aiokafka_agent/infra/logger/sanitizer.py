from logging import Filter
from re import compile

from aiokafka_agent.infra.datatype.string import fix_encoding


MAX_LENGTH: int = 10_024

# Combined regex pattern that handles:
# 1. ANSI escape sequences (removal)
# 2. Control characters (replacement with \xXX)
# 3. Newlines/carriage returns (replacement with \n and \r)
SANITIZE_PATTERN = compile(
    r"(\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]))|"  # ANSI escape sequences
    r"([\x00-\x1F\x7F-\x9F])|"  # Control characters
    r"(\n)|"  # Newlines
    r"(\r)",  # Carriage returns
)


class SanitizingFilter(Filter):
    """
    Logging filter that sanitizes log messages using a single regex pass
    """

    def _replace_match(self, match):
        """
        Replacement function for the combined regex
        """
        # Group 1: ANSI escape sequences (remove)
        if match.group(1):
            return ""
        # Group 2: Control characters (replace with \xXX)
        if match.group(2):
            return f"\\x{ord(match.group(2)):02x}"
        # Group 3: Newlines (replace with \n)
        if match.group(3):
            return "\\n"
        # Group 4: Carriage returns (replace with \r)
        if match.group(4):
            return "\\r"
        return match.group(0)

    def filter(self, record):
        """
        Sanitize the log message before emission using a single regex pass
        """
        if not record.msg:
            return True

        # Convert non-string messages to string first
        message = str(record.msg)[:MAX_LENGTH]

        # Single-pass sanitization
        message = SANITIZE_PATTERN.sub(self._replace_match, message)

        # Unicode normalization
        record.msg = fix_encoding(message, "utf-8")

        return True
