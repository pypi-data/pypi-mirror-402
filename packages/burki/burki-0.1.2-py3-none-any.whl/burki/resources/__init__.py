"""
Burki SDK Resources.

This package contains all resource classes for interacting with the Burki API.
"""

from burki.resources.assistants import AssistantsResource
from burki.resources.calls import CallsResource
from burki.resources.phone_numbers import PhoneNumbersResource
from burki.resources.documents import DocumentsResource
from burki.resources.tools import ToolsResource
from burki.resources.sms import SMSResource
from burki.resources.campaigns import CampaignsResource

__all__ = [
    "AssistantsResource",
    "CallsResource",
    "PhoneNumbersResource",
    "DocumentsResource",
    "ToolsResource",
    "SMSResource",
    "CampaignsResource",
]
