from netbox.views import generic
from utilities.views import register_model_view

from netbox_authorized_keys.filtersets import (
    AuthorizedKeyFilterSet,
)
from netbox_authorized_keys.forms import (
    AuthorizedKeyBulkEditForm,
    AuthorizedKeyBulkImportForm,
    AuthorizedKeyFilterForm,
    AuthorizedKeyForm,
)
from netbox_authorized_keys.models import AuthorizedKey
from netbox_authorized_keys.tables import AuthorizedKeyTable


@register_model_view(AuthorizedKey, name="list", path="", detail=False)
class AuthorizedKeyListView(generic.ObjectListView):
    queryset = AuthorizedKey.objects.all()
    table = AuthorizedKeyTable
    filterset = AuthorizedKeyFilterSet
    filterset_form = AuthorizedKeyFilterForm


@register_model_view(AuthorizedKey, name="", detail=True)
class AuthorizedKeyView(generic.ObjectView):
    queryset = AuthorizedKey.objects.prefetch_related("devices", "virtual_machines").all()

    def get_extra_context(self, request, instance):
        device_ids = [device.id for device in instance.devices.all()]
        virtual_machine_ids = [vm.id for vm in instance.virtual_machines.all()]

        return {
            "device_ids": device_ids,
            "virtual_machine_ids": virtual_machine_ids,
        }


@register_model_view(AuthorizedKey, name="add", detail=False)
@register_model_view(AuthorizedKey, name="edit", detail=True)
class AuthorizedKeyEditView(generic.ObjectEditView):
    queryset = AuthorizedKey.objects.all()
    form = AuthorizedKeyForm


@register_model_view(AuthorizedKey, name="delete", detail=True)
class AuthorizedKeyDeleteView(generic.ObjectDeleteView):
    queryset = AuthorizedKey.objects.all()


@register_model_view(AuthorizedKey, name="bulk_import", detail=False)
class AuthorizedKeyBulkImportView(generic.BulkImportView):
    queryset = AuthorizedKey.objects.all()
    model_form = AuthorizedKeyBulkImportForm


@register_model_view(AuthorizedKey, name="bulk_edit", detail=False)
class AuthorizedKeyBulkEditView(generic.BulkEditView):
    queryset = AuthorizedKey.objects.all()
    filterset = AuthorizedKeyFilterSet
    table = AuthorizedKeyTable
    form = AuthorizedKeyBulkEditForm


@register_model_view(AuthorizedKey, name="bulk_delete", detail=False)
class AuthorizedKeyBulkDeleteView(generic.BulkDeleteView):
    queryset = AuthorizedKey.objects.all()
    filterset = AuthorizedKeyFilterSet
    table = AuthorizedKeyTable
