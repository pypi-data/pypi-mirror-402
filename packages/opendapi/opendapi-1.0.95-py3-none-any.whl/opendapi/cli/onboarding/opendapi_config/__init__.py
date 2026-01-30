"""
Interactive integration onboarding for opendapi config
"""

# pylint: disable=unused-import

from .base import InteractiveIntegrationOnboardBase

# NOTE: import all the ORM onboarders here so they are registered
from .orms.activerecord import ActiveRecordInteractiveIntegrationOnboard
from .orms.pynamodb import PynamoDBInteractiveIntegrationOnboard
