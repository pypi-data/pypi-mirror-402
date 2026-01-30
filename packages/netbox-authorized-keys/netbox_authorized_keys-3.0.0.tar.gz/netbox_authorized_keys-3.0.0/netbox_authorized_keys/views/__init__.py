from .authorizedkey import (
    AuthorizedKeyBulkDeleteView,
    AuthorizedKeyBulkEditView,
    AuthorizedKeyBulkImportView,
    AuthorizedKeyDeleteView,
    AuthorizedKeyEditView,
    AuthorizedKeyListView,
    AuthorizedKeyView,
)
from .bulk_operation import (
    AuthorizedKeyBulkActionView,
    AuthorizedKeyBulkAddView,
    AuthorizedKeyBulkRemoveView,
    CredentialBulkActionView,
    CredentialBulkAddView,
    CredentialBulkRemoveView,
)
from .credential import (
    CredentialBulkDeleteView,
    CredentialBulkEditView,
    CredentialBulkImportView,
    CredentialDeleteView,
    CredentialEditView,
    CredentialListView,
    CredentialView,
)
from .m2m_relation import (
    AuthorizedKeyDeviceListView,
    AuthorizedKeyVirtualMachineListView,
    CredentialDeviceListView,
    CredentialVirtualMachineListView,
)

__all__ = (
    # AuthorizedKey CRUD views
    "AuthorizedKeyListView",
    "AuthorizedKeyView",
    "AuthorizedKeyEditView",
    "AuthorizedKeyDeleteView",
    "AuthorizedKeyBulkImportView",
    "AuthorizedKeyBulkEditView",
    "AuthorizedKeyBulkDeleteView",
    # AuthorizedKey bulk operation views
    "AuthorizedKeyBulkActionView",
    "AuthorizedKeyBulkAddView",
    "AuthorizedKeyBulkRemoveView",
    # Credential CRUD views
    "CredentialListView",
    "CredentialView",
    "CredentialEditView",
    "CredentialDeleteView",
    "CredentialBulkImportView",
    "CredentialBulkEditView",
    "CredentialBulkDeleteView",
    # Credential bulk operation views
    "CredentialBulkActionView",
    "CredentialBulkAddView",
    "CredentialBulkRemoveView",
    # M2M relation views
    "AuthorizedKeyDeviceListView",
    "AuthorizedKeyVirtualMachineListView",
    "CredentialDeviceListView",
    "CredentialVirtualMachineListView",
)
