import django_tables2 as tables
from django.utils.html import format_html
from netbox.tables import NetBoxTable, columns
from netbox.tables.columns import ChoiceFieldColumn, TagColumn

from netbox_authorized_keys.models import Credential, CredentialDevice, CredentialVirtualMachine


class CredentialTable(NetBoxTable):
    id = tables.Column(linkify=True, verbose_name="ID")
    credential_type = ChoiceFieldColumn()
    username = tables.Column(verbose_name="Username")
    owner = tables.Column(verbose_name="Owner")
    used_by = tables.Column(verbose_name="Used By")
    credential_storage = tables.Column(verbose_name="Storage")
    tags = TagColumn()

    class Meta(NetBoxTable.Meta):
        model = Credential
        fields = (
            "id",
            "credential_type",
            "username",
            "owner",
            "credential_storage",
            "used_by",
            "description",
            "comments",
            "tags",
        )
        default_columns = ("id", "credential_type", "username", "owner", "used_by", "description")

    def render_credential_storage(self, value, record):
        if not value:
            return format_html('<span class="text-muted">—</span>')
        return format_html('<span title="{}">{}</span>', value, record.rendered_fingerprint)


class CredentialDeviceTable(NetBoxTable):
    id = tables.Column(linkify=False, verbose_name="ID")

    credential = tables.Column(linkify=True)
    device = tables.Column(linkify=True)
    actions = columns.ActionsColumn(
        actions=(),
    )

    class Meta(NetBoxTable.Meta):
        model = CredentialDevice
        fields = ("credential", "device")


class CredentialVirtualMachineTable(NetBoxTable):
    id = tables.Column(linkify=False, verbose_name="ID")

    credential = tables.Column(linkify=True)
    virtual_machine = tables.Column(linkify=True)
    actions = columns.ActionsColumn(
        actions=(),
    )

    class Meta(NetBoxTable.Meta):
        model = CredentialVirtualMachine
        fields = ("credential", "virtual_machine")
