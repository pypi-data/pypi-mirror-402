from dcim.models import Device
from django.utils.translation import gettext_lazy as _
from netbox.forms import NetBoxModelFilterSetForm
from utilities.forms.fields import (
    DynamicModelMultipleChoiceField,
)
from virtualization.models import VirtualMachine

from netbox_authorized_keys.models import (
    AuthorizedKey,
    AuthorizedKeyDevice,
    AuthorizedKeyVirtualMachine,
    Credential,
    CredentialDevice,
    CredentialVirtualMachine,
)


class AuthorizedKeyDeviceFilterForm(NetBoxModelFilterSetForm):
    model = AuthorizedKeyDevice
    authorized_key = DynamicModelMultipleChoiceField(
        queryset=AuthorizedKey.objects.all(), label=_("Authorized Key"), required=False
    )
    device = DynamicModelMultipleChoiceField(queryset=Device.objects.all(), label=_("Device"), required=False)


class AuthorizedKeyVirtualMachineFilterForm(NetBoxModelFilterSetForm):
    model = AuthorizedKeyVirtualMachine
    authorized_key = DynamicModelMultipleChoiceField(
        queryset=AuthorizedKey.objects.all(), label=_("Authorized Key"), required=False
    )
    virtual_machine = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(), label=_("Virtual Machine"), required=False
    )


class CredentialDeviceFilterForm(NetBoxModelFilterSetForm):
    model = CredentialDevice
    credential = DynamicModelMultipleChoiceField(
        queryset=Credential.objects.all(), label=_("Credential"), required=False
    )
    device = DynamicModelMultipleChoiceField(queryset=Device.objects.all(), label=_("Device"), required=False)


class CredentialVirtualMachineFilterForm(NetBoxModelFilterSetForm):
    model = CredentialVirtualMachine
    credential = DynamicModelMultipleChoiceField(
        queryset=Credential.objects.all(), label=_("Credential"), required=False
    )
    virtual_machine = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(), label=_("Virtual Machine"), required=False
    )
