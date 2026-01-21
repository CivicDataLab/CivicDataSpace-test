"""
Centralized test data constants for CivicDataSpace tests.
Use these constants instead of hard-coding test data in test files.

This module contains all test data used across different test flows:
- Dataset creation (individual & organization)
- UseCase creation (individual & organization)
- Profile editing (individual & organization)
"""

from datetime import datetime, timedelta
from typing import Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# Dataset Test Data - Individual & Organization
# ═══════════════════════════════════════════════════════════════════════════════

class DatasetTestData:
    """Test data constants for dataset creation flows"""

    # Description templates
    DESCRIPTION_TEMPLATE = "Automated test description {timestamp}"

    # Sectors
    SECTORS = ["Budgets"]
    SECTORS_ALTERNATIVE = ["Education"]

    # Tags
    TAGS = ["Finance"]
    TAGS_ALTERNATIVE = ["Budget", "Transparency"]

    # Geography
    GEOGRAPHY = "Assam"
    GEOGRAPHY_ALTERNATIVE = "India"

    # Date formats
    DATE_INPUT_FORMAT = "09022021"  # DDMMYYYY format for input
    DATE_ISO_FORMAT = "2021-09-02"  # ISO format for validation
    DATE_ISO_ALT_FORMAT = "2021-02-09"  # Alternative ISO format

    # Source
    SOURCE_URL = "https://example.com"

    # License
    LICENSE = "CC BY 4.0 (Attribution)"
    LICENSE_SHORT = "CC BY 4.0"

    @staticmethod
    def get_description() -> str:
        """Generate timestamped description for dataset"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return DatasetTestData.DESCRIPTION_TEMPLATE.format(timestamp=timestamp)

    @staticmethod
    def get_all_data() -> Dict[str, Any]:
        """Get complete dataset test data as dictionary"""
        return {
            'description': DatasetTestData.get_description(),
            'sectors': DatasetTestData.SECTORS,
            'tags': DatasetTestData.TAGS,
            'geography': DatasetTestData.GEOGRAPHY,
            'date': DatasetTestData.DATE_INPUT_FORMAT,
            'source_url': DatasetTestData.SOURCE_URL,
            'license': DatasetTestData.LICENSE
        }


# ═══════════════════════════════════════════════════════════════════════════════
# UseCase Test Data - Individual & Organization
# ═══════════════════════════════════════════════════════════════════════════════

class UseCaseTestData:
    """Test data constants for UseCase creation flows"""

    # Summary templates
    SUMMARY_TEMPLATE_IND = "Automated Functional Test UseCase – {date}"
    SUMMARY_TEMPLATE_ORG = "Automated Org UseCase Test – {date}"

    # Platform URLs
    PLATFORM_URL_IND = "https://yourplatform.url"
    PLATFORM_URL_ORG = "https://orgplatform.url"

    # Running Status
    STATUS_ONGOING = "On Going"
    STATUS_COMPLETED = "Completed"
    STATUS_INITIATED = "Initiated"

    # Tags
    TAGS = ["Budget"]
    TAGS_ALTERNATIVE = ["Transparency"]

    # Sectors
    SECTORS = ["Budgets"]
    SECTORS_ALTERNATIVE = ["Education"]

    # Geography
    GEOGRAPHY = "India"
    GEOGRAPHY_ALTERNATIVE = "Assam"

    # SDG Goals
    SDG_GOALS = "SDG13"
    SDG_GOALS_ALTERNATIVE = ["SDG1", "SDG2"]

    # Dates
    START_DATE_INPUT = "01012023"  # DDMMYYYY format
    START_DATE_ISO = "2023-01-01"  # ISO format
    COMPLETED_DATE_INPUT = "01062023"
    COMPLETED_DATE_ISO = "2023-06-01"

    # Contributors (for reference, though currently skipped in tests)
    CONTRIBUTORS = ["Sanjay Pinna"]
    SUPPORTERS = ["CivicDataLab"]
    PARTNERS = ["CivicDataLab"]

    @staticmethod
    def get_summary(user_type: str = "individual") -> str:
        """
        Generate timestamped summary for UseCase

        Args:
            user_type: Either "individual" or "organization"
        """
        date = datetime.now().date()
        if user_type == "organization":
            return UseCaseTestData.SUMMARY_TEMPLATE_ORG.format(date=date)
        return UseCaseTestData.SUMMARY_TEMPLATE_IND.format(date=date)

    @staticmethod
    def get_platform_url(user_type: str = "individual") -> str:
        """Get platform URL based on user type"""
        return (UseCaseTestData.PLATFORM_URL_ORG if user_type == "organization"
                else UseCaseTestData.PLATFORM_URL_IND)

    @staticmethod
    def get_all_data(user_type: str = "individual") -> Dict[str, Any]:
        """Get complete UseCase test data as dictionary"""
        return {
            'summary': UseCaseTestData.get_summary(user_type),
            'platform_url': UseCaseTestData.get_platform_url(user_type),
            'status': UseCaseTestData.STATUS_ONGOING,
            'tags': UseCaseTestData.TAGS,
            'sectors': UseCaseTestData.SECTORS,
            'geography': UseCaseTestData.GEOGRAPHY,
            'sdg_goals': UseCaseTestData.SDG_GOALS,
            'start_date': UseCaseTestData.START_DATE_INPUT,
            'start_date_iso': UseCaseTestData.START_DATE_ISO
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Profile Test Data - Individual
# ═══════════════════════════════════════════════════════════════════════════════

class IndividualProfileTestData:
    """Test data constants for individual profile editing"""

    FIRST_NAME = "Saqib"
    LAST_NAME = "Manan"
    BIO = "Quality Assurance Engineer. Deriving Quality at CDL"

    # Alternative test data
    FIRST_NAME_ALT = "AutoTest"
    LAST_NAME_ALT = "User"
    BIO_ALT = "Automated test profile biography"

    # Social media links (for future use)
    GITHUB_URL = "https://github.com/testuser"
    LINKEDIN_URL = "https://linkedin.com/in/testuser"
    TWITTER_URL = "https://twitter.com/testuser"
    LOCATION = "Test City, Test Country"

    @staticmethod
    def get_all_data() -> Dict[str, str]:
        """Get complete individual profile test data"""
        return {
            'first_name': IndividualProfileTestData.FIRST_NAME,
            'last_name': IndividualProfileTestData.LAST_NAME,
            'bio': IndividualProfileTestData.BIO
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Profile Test Data - Organization
# ═══════════════════════════════════════════════════════════════════════════════

class OrganizationProfileTestData:
    """Test data constants for organization profile editing"""

    ORG_NAME = "CivicDataLab"
    ORG_DESCRIPTION = "Leading civic tech organization"
    ORG_BIO = "CivicDataLab works with data, tech, and design for public good."

    # Alternative test data
    ORG_NAME_ALT = "AutoTest Organization"
    ORG_DESCRIPTION_ALT = "Automated test organization"
    ORG_BIO_ALT = "Automated test organization for testing purposes"

    # Social media and contact info (for future use)
    WEBSITE_URL = "https://civicdatalab.org"
    TWITTER_URL = "https://twitter.com/civicdatalab"
    LINKEDIN_URL = "https://linkedin.com/company/civicdatalab"
    LOCATION = "Bangalore, India"

    @staticmethod
    def get_all_data() -> Dict[str, str]:
        """Get complete organization profile test data"""
        return {
            'org_name': OrganizationProfileTestData.ORG_NAME,
            'org_description': OrganizationProfileTestData.ORG_DESCRIPTION,
            'org_bio': OrganizationProfileTestData.ORG_BIO
        }


# ═══════════════════════════════════════════════════════════════════════════════
# File Upload Test Data
# ═══════════════════════════════════════════════════════════════════════════════

class FileTestData:
    """Test data for file uploads"""

    # Sample file names (actual paths defined in conftest.py fixtures)
    CSV_FILENAME = "sample_data.csv"
    LOGO_FILENAME = "sample_logo.png"
    PROFILE_IMAGE_FILENAME = "sample_profile.jpg"

    @staticmethod
    def get_unique_filename(base_filename: str) -> str:
        """
        Generate unique filename with timestamp

        Args:
            base_filename: Base filename (e.g., "sample_data.csv")

        Returns:
            Unique filename with timestamp (e.g., "sample_data_20260121_143025.csv")
        """
        import os
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(base_filename)
        return f"{name}_{timestamp}{ext}"


# ═══════════════════════════════════════════════════════════════════════════════
# Legacy Constants (for backwards compatibility)
# ═══════════════════════════════════════════════════════════════════════════════

# Dataset
DATASET_DESCRIPTION = DatasetTestData.DESCRIPTION_TEMPLATE
DATASET_SECTORS = DatasetTestData.SECTORS
DATASET_TAGS = DatasetTestData.TAGS
DATASET_GEOGRAPHY = DatasetTestData.GEOGRAPHY
DATASET_SOURCE_URL = DatasetTestData.SOURCE_URL
DATASET_LICENSE = DatasetTestData.LICENSE

# UseCase
USECASE_SUMMARY = UseCaseTestData.SUMMARY_TEMPLATE_IND
USECASE_PLATFORM_URL = UseCaseTestData.PLATFORM_URL_IND
USECASE_STATUS_ONGOING = UseCaseTestData.STATUS_ONGOING
USECASE_STATUS_COMPLETED = UseCaseTestData.STATUS_COMPLETED
USECASE_SDG_GOAL = UseCaseTestData.SDG_GOALS
USECASE_SECTORS = UseCaseTestData.SECTORS
USECASE_TAGS = UseCaseTestData.TAGS

# Profile
PROFILE_FIRST_NAME = IndividualProfileTestData.FIRST_NAME
PROFILE_LAST_NAME = IndividualProfileTestData.LAST_NAME
PROFILE_BIO = IndividualProfileTestData.BIO

# Organization
ORG_NAME = OrganizationProfileTestData.ORG_NAME
ORG_DESCRIPTION = OrganizationProfileTestData.ORG_DESCRIPTION


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def get_timestamped_description(template: str = DATASET_DESCRIPTION) -> str:
    """
    Generate a timestamped description for test data.

    Args:
        template: Template string with {timestamp} or {date} placeholder

    Returns:
        Description with current timestamp

    Example:
        >>> get_timestamped_description()
        'Automated test description 2026-01-21 15:30:45'
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Support both {date} and {timestamp} placeholders
    return template.format(date=timestamp, timestamp=timestamp)


def get_timestamped_name(prefix: str) -> str:
    """
    Generate a unique name with timestamp for test data.

    Args:
        prefix: Prefix for the name (e.g., "Dataset", "UseCase")

    Returns:
        Name with current timestamp

    Example:
        >>> get_timestamped_name("Dataset")
        'Dataset_20260121_153045'
    """
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def get_iso_date(days_offset: int = 0) -> str:
    """
    Get ISO format date (YYYY-MM-DD) with optional offset.

    Args:
        days_offset: Number of days to offset from today (negative for past dates)

    Returns:
        ISO format date string

    Example:
        >>> get_iso_date()
        '2026-01-21'
        >>> get_iso_date(-7)
        '2026-01-14'
    """
    target_date = datetime.now() + timedelta(days=days_offset)
    return target_date.strftime('%Y-%m-%d')


def get_date_input_format(days_offset: int = 0) -> str:
    """
    Get date in DDMMYYYY format for form input with optional offset.

    Args:
        days_offset: Number of days to offset from today (negative for past dates)

    Returns:
        Date string in DDMMYYYY format

    Example:
        >>> get_date_input_format()
        '21012026'
        >>> get_date_input_format(-30)
        '22122025'
    """
    target_date = datetime.now() + timedelta(days=days_offset)
    return target_date.strftime('%d%m%Y')
