from netbox.views import generic

from netbox_authorized_keys.filtersets import (
    AuthorizedKeyDeviceFilterSet,
    AuthorizedKeyVirtualMachineFilterSet,
    CredentialDeviceFilterSet,
    CredentialVirtualMachineFilterSet,
)
from netbox_authorized_keys.forms import (
    AuthorizedKeyDeviceFilterForm,
    AuthorizedKeyVirtualMachineFilterForm,
    CredentialDeviceFilterForm,
    CredentialVirtualMachineFilterForm,
)
from netbox_authorized_keys.models import (
    AuthorizedKeyDevice,
    AuthorizedKeyVirtualMachine,
    CredentialDevice,
    CredentialVirtualMachine,
)
from netbox_authorized_keys.tables import (
    AuthorizedKeyDeviceTable,
    AuthorizedKeyVirtualMachineTable,
    CredentialDeviceTable,
    CredentialVirtualMachineTable,
)


# Authorized Key Devices
class AuthorizedKeyDeviceListView(generic.ObjectListView):
    queryset = AuthorizedKeyDevice.objects.all()
    table = AuthorizedKeyDeviceTable
    filterset = AuthorizedKeyDeviceFilterSet
    filterset_form = AuthorizedKeyDeviceFilterForm


# Authorized Key Virtual Machines
class AuthorizedKeyVirtualMachineListView(generic.ObjectListView):
    queryset = AuthorizedKeyVirtualMachine.objects.all()
    table = AuthorizedKeyVirtualMachineTable
    filterset = AuthorizedKeyVirtualMachineFilterSet
    filterset_form = AuthorizedKeyVirtualMachineFilterForm


# Credential Devices
class CredentialDeviceListView(generic.ObjectListView):
    queryset = CredentialDevice.objects.all()
    table = CredentialDeviceTable
    filterset = CredentialDeviceFilterSet
    filterset_form = CredentialDeviceFilterForm


# Credential Virtual Machines
class CredentialVirtualMachineListView(generic.ObjectListView):
    queryset = CredentialVirtualMachine.objects.all()
    table = CredentialVirtualMachineTable
    filterset = CredentialVirtualMachineFilterSet
    filterset_form = CredentialVirtualMachineFilterForm
