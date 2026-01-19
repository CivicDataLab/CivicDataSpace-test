"""
Centralized test data constants for CivicDataSpace tests.
Use these constants instead of hard-coding test data in test files.
"""

from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# Dataset Test Data
# ═══════════════════════════════════════════════════════════════════════════════

DATASET_DESCRIPTION = "Automated test dataset created on {date}"
DATASET_SECTORS = ["Budgets", "Education"]
DATASET_TAGS = ["Budget", "Transparency"]
DATASET_GEOGRAPHY = "India"
DATASET_SOURCE_URL = "https://example.com/data-source"
DATASET_LICENSE = "CC BY 4.0"

# ═══════════════════════════════════════════════════════════════════════════════
# UseCase Test Data
# ═══════════════════════════════════════════════════════════════════════════════

USECASE_SUMMARY = "Automated test usecase created on {date}"
USECASE_PLATFORM_URL = "https://example.com/platform"
USECASE_STATUS_ONGOING = "On Going"
USECASE_STATUS_COMPLETED = "Completed"
USECASE_SDG_GOAL = "SDG13"
USECASE_SECTORS = ["Budgets", "Education"]
USECASE_TAGS = ["Budget", "Transparency"]

# ═══════════════════════════════════════════════════════════════════════════════
# Profile Test Data
# ═══════════════════════════════════════════════════════════════════════════════

PROFILE_FIRST_NAME = "AutoTest"
PROFILE_LAST_NAME = "User"
PROFILE_BIO = "Automated test profile biography"

# ═══════════════════════════════════════════════════════════════════════════════
# Organization Test Data
# ═══════════════════════════════════════════════════════════════════════════════

ORG_NAME = "AutoTest Organization"
ORG_DESCRIPTION = "Automated test organization"

# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def get_timestamped_description(template: str = DATASET_DESCRIPTION) -> str:
    """
    Generate a timestamped description for test data.

    Args:
        template: Template string with {date} placeholder

    Returns:
        Description with current timestamp

    Example:
        >>> get_timestamped_description()
        'Automated test dataset created on 2026-01-13 15:30:45'
    """
    return template.format(date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

def get_timestamped_name(prefix: str) -> str:
    """
    Generate a unique name with timestamp for test data.

    Args:
        prefix: Prefix for the name (e.g., "Dataset", "UseCase")

    Returns:
        Name with current timestamp

    Example:
        >>> get_timestamped_name("Dataset")
        'Dataset_20260113_153045'
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
        '2026-01-13'
        >>> get_iso_date(-7)
        '2026-01-06'
    """
    from datetime import timedelta
    target_date = datetime.now() + timedelta(days=days_offset)
    return target_date.strftime('%Y-%m-%d')
