from netbox.views import generic
from utilities.views import register_model_view

from netbox_authorized_keys.filtersets import CredentialFilterSet
from netbox_authorized_keys.forms import (
    CredentialBulkEditForm,
    CredentialBulkImportForm,
    CredentialFilterForm,
    CredentialForm,
)
from netbox_authorized_keys.models import Credential
from netbox_authorized_keys.tables import CredentialTable


@register_model_view(Credential, name="list", path="", detail=False)
class CredentialListView(generic.ObjectListView):
    queryset = Credential.objects.all()
    table = CredentialTable
    filterset = CredentialFilterSet
    filterset_form = CredentialFilterForm


@register_model_view(Credential, name="", detail=True)
class CredentialView(generic.ObjectView):
    queryset = Credential.objects.prefetch_related("devices", "virtual_machines").all()

    def get_extra_context(self, request, instance):
        device_ids = [device.id for device in instance.devices.all()]
        virtual_machine_ids = [vm.id for vm in instance.virtual_machines.all()]

        return {
            "device_ids": device_ids,
            "virtual_machine_ids": virtual_machine_ids,
        }


@register_model_view(Credential, name="add", detail=False)
@register_model_view(Credential, name="edit", detail=True)
class CredentialEditView(generic.ObjectEditView):
    queryset = Credential.objects.all()
    form = CredentialForm


@register_model_view(Credential, name="delete", detail=True)
class CredentialDeleteView(generic.ObjectDeleteView):
    queryset = Credential.objects.all()


@register_model_view(Credential, name="bulk_import", detail=False)
class CredentialBulkImportView(generic.BulkImportView):
    queryset = Credential.objects.all()
    model_form = CredentialBulkImportForm


@register_model_view(Credential, name="bulk_edit", detail=False)
class CredentialBulkEditView(generic.BulkEditView):
    queryset = Credential.objects.all()
    filterset = CredentialFilterSet
    table = CredentialTable
    form = CredentialBulkEditForm


@register_model_view(Credential, name="bulk_delete", detail=False)
class CredentialBulkDeleteView(generic.BulkDeleteView):
    queryset = Credential.objects.all()
    filterset = CredentialFilterSet
    table = CredentialTable
