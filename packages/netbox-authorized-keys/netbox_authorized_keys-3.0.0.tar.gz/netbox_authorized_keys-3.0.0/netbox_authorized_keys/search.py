"""
Search indexes for netbox_authorized_keys plugin.

This module defines search indexes for AuthorizedKey and Credential models,
enabling them to appear in NetBox's global search functionality.
"""

from netbox.search import SearchIndex

from .models import AuthorizedKey, Credential


class AuthorizedKeyIndex(SearchIndex):
    """Search index for AuthorizedKey model."""

    model = AuthorizedKey
    fields = (
        ("username", 100),  # Highest weight - primary identifier
        ("full_name", 200),  # High weight - important for user identification
        ("description", 500),  # Medium weight
        ("comments", 5000),  # Lower weight
        ("public_key", 10000),  # Lowest weight - large field
    )
    display_attrs = ("username", "full_name", "description")


class CredentialIndex(SearchIndex):
    """Search index for Credential model."""

    model = Credential
    fields = (
        ("username", 100),  # Highest weight - primary identifier
        ("owner", 200),  # High weight - important for ownership
        ("credential_type", 300),  # Important for filtering
        ("used_by", 400),  # Medium-high weight - which server uses it
        ("description", 500),  # Medium weight
        ("comments", 5000),  # Lower weight
        ("credential_storage", 10000),  # Lowest weight - technical field
    )
    display_attrs = ("username", "owner", "credential_type", "used_by", "description")


# Register search indexes with NetBox
indexes = [
    AuthorizedKeyIndex,
    CredentialIndex,
]
