"""
Test configuration for Noveum SDK testing suite.
Loads configuration from environment variables.
"""

import os


class TestConfig:
    """Configuration for API testing"""

    # API Configuration
    API_KEY: str = os.getenv("NOVEUM_API_KEY", "")
    ORG_SLUG: str = os.getenv("NOVEUM_ORG_SLUG", "NoveumSDK")
    BASE_URL: str = os.getenv("NOVEUM_BASE_URL", "https://api.noveum.ai")

    # Test Data Configuration
    TEST_DATA_PREFIX: str = os.getenv("TEST_DATA_PREFIX", "sdk_test_")
    CLEANUP_ON_FAILURE: bool = os.getenv("CLEANUP_ON_FAILURE", "true").lower() == "true"
    VERBOSE_LOGGING: bool = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"

    # Test Execution Settings
    MAX_CONCURRENT_TESTS: int = int(os.getenv("MAX_CONCURRENT_TESTS", "5"))
    TEST_TIMEOUT_SECONDS: int = int(os.getenv("TEST_TIMEOUT_SECONDS", "30"))
    RETRY_FAILED_TESTS: bool = os.getenv("RETRY_FAILED_TESTS", "false").lower() == "true"

    @classmethod
    def validate(cls) -> tuple[bool, str | None]:
        """
        Validate that required configuration is present.
        Returns: (is_valid, error_message)
        """
        if not cls.API_KEY:
            return False, "NOVEUM_API_KEY environment variable not set"

        if not cls.API_KEY.startswith("nv_"):
            return False, "Invalid API key format. Expected 'nv_...'"

        if not cls.ORG_SLUG:
            return False, "NOVEUM_ORG_SLUG environment variable not set"

        return True, None

    @classmethod
    def display(cls):
        """Display current configuration (with masked API key)"""
        masked_key = f"{'*' * 8}...{'*' * 4} (set)" if cls.API_KEY else "NOT SET"

        print("=" * 60)
        print("TEST CONFIGURATION")
        print("=" * 60)
        print(f"API Key:              {masked_key}")
        print(f"Organization:         {cls.ORG_SLUG}")
        print(f"Base URL:             {cls.BASE_URL}")
        print(f"Test Data Prefix:     {cls.TEST_DATA_PREFIX}")
        print(f"Cleanup on Failure:   {cls.CLEANUP_ON_FAILURE}")
        print(f"Verbose Logging:      {cls.VERBOSE_LOGGING}")
        print(f"Max Concurrent Tests: {cls.MAX_CONCURRENT_TESTS}")
        print(f"Test Timeout:         {cls.TEST_TIMEOUT_SECONDS}s")
        print(f"Retry Failed Tests:   {cls.RETRY_FAILED_TESTS}")
        print("=" * 60)


def load_config_from_env_file(env_file: str = ".env"):
    """
    Load configuration from .env file if it exists.
    This is optional - environment variables take precedence.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv(env_file)
        return True
    except ImportError:
        print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
        return False
    except Exception as e:
        print(f"⚠️  Could not load {env_file}: {e}")
        return False


# Quick validation on import
if __name__ == "__main__":
    # Try to load from .env file
    load_config_from_env_file()

    # Display configuration
    TestConfig.display()

    # Validate
    is_valid, error = TestConfig.validate()
    if is_valid:
        print("✅ Configuration is valid!")
    else:
        print(f"❌ Configuration error: {error}")
