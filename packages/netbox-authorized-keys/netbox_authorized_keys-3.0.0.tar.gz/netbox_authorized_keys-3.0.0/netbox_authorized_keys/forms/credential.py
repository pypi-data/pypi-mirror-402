from dcim.models import Device
from django import forms
from django.utils.translation import gettext_lazy as _
from netbox.forms import NetBoxModelBulkEditForm, NetBoxModelFilterSetForm, NetBoxModelForm, NetBoxModelImportForm
from utilities.forms.fields import (
    CommentField,
    CSVModelMultipleChoiceField,
    DynamicModelMultipleChoiceField,
    TagFilterField,
)
from utilities.forms.rendering import FieldSet
from virtualization.models import VirtualMachine

from netbox_authorized_keys.models import Credential, CredentialTypeChoices


class CredentialForm(NetBoxModelForm):
    # Django/NetBox automatically creates credential_type field from model choices

    username = forms.CharField(
        label=_("Username / Service Account"),
        required=True,
    )
    owner = forms.CharField(
        label=_("Owner"),
        required=True,
        help_text=_("Login of the administrator/owner"),
    )
    credential_storage = forms.CharField(
        label=_("Credential Storage"),
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        help_text=_("Key fingerprint, hash, or storage location (e.g., 1Password, .env file, LastPass, Keychain)"),
    )
    used_by = forms.CharField(
        label=_("Used By"),
        required=True,
        help_text=_("Which server uses this credential"),
    )
    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(attrs={"rows": 3}),
        required=True,
        help_text=_("Information about what the user/credential does, which service, etc. (supports Markdown)"),
    )

    devices = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        label=_("Devices"),
        required=False,
    )
    virtual_machines = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(),
        label=_("Virtual Machines"),
        required=False,
    )
    comments = CommentField()

    fieldsets = (
        FieldSet("credential_type", "username", "owner", name=_("Basic Information")),
        FieldSet("credential_storage", "used_by", "description", name=_("Credential Details")),
        FieldSet("devices", "virtual_machines", name=_("Host Assignment")),
        FieldSet("tags", name=_("Misc")),
    )

    class Meta:
        model = Credential
        fields = [
            "credential_type",
            "username",
            "owner",
            "credential_storage",
            "used_by",
            "description",
            "devices",
            "virtual_machines",
            "comments",
            "tags",
        ]


class CredentialFilterForm(NetBoxModelFilterSetForm):
    model = Credential

    credential_type = forms.ChoiceField(
        choices=[(None, "---------")] + [(choice[0], choice[1]) for choice in CredentialTypeChoices.CHOICES],
        required=False,
        label=_("Credential Type"),
    )
    username = forms.CharField(required=False)
    owner = forms.CharField(required=False)
    used_by = forms.CharField(required=False)
    description = forms.CharField(required=False)

    devices = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        label=_("Devices"),
        required=False,
    )
    virtual_machines = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(),
        label=_("Virtual Machines"),
        required=False,
    )

    tag = TagFilterField(model)


class CredentialBulkImportForm(NetBoxModelImportForm):
    # Django/NetBox automatically creates credential_type field from model choices

    devices = CSVModelMultipleChoiceField(
        queryset=Device.objects.all(),
        to_field_name="name",
        required=False,
        help_text=_('Comma-separated list of devices, encased with double quotes (e.g. "Router1,Switch2")'),
    )

    virtual_machines = CSVModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(),
        to_field_name="name",
        required=False,
        help_text=_('Comma-separated list of virtual machines, encased with double quotes (e.g. "VM1,VM2")'),
    )

    class Meta:
        model = Credential
        fields = [
            "credential_type",
            "username",
            "owner",
            "credential_storage",
            "used_by",
            "description",
            "devices",
            "virtual_machines",
            "comments",
            "tags",
        ]


class CredentialBulkEditForm(NetBoxModelBulkEditForm):
    credential_type = forms.ChoiceField(
        choices=[(None, "---------")] + [(choice[0], choice[1]) for choice in CredentialTypeChoices.CHOICES],
        required=False,
        label=_("Credential Type"),
    )
    username = forms.CharField(
        label=_("Username / Service Account"),
        required=False,
    )
    owner = forms.CharField(
        label=_("Owner"),
        required=False,
    )
    used_by = forms.CharField(
        label=_("Used By"),
        required=False,
    )
    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )
    devices = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        label=_("Devices"),
        required=False,
    )
    virtual_machines = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(),
        label=_("Virtual Machines"),
        required=False,
    )
    comments = CommentField()

    model = Credential

    fieldsets = (
        FieldSet("credential_type", "username", "owner", name=_("Basic Information")),
        FieldSet("used_by", "description", name=_("Credential Details")),
        FieldSet("devices", "virtual_machines", name=_("Host Assignment")),
        FieldSet("tags", name=_("Misc")),
    )

    nullable_fields = (
        "devices",
        "virtual_machines",
        "tags",
        "comments",
        "used_by",
        "description",
        "credential_storage",
    )
