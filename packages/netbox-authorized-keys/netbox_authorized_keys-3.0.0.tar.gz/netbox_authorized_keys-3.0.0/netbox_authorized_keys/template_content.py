from dcim.models import Device
from netbox.views import generic
from utilities.views import ViewTab, register_model_view
from virtualization.models import VirtualMachine

from netbox_authorized_keys.filtersets import AuthorizedKeyFilterSet, CredentialFilterSet
from netbox_authorized_keys.models import AuthorizedKey, Credential
from netbox_authorized_keys.tables import AuthorizedKeyTable, CredentialTable


class AuthorizedKeyTabView(generic.ObjectChildrenView):
    child_model = AuthorizedKey
    filterset = AuthorizedKeyFilterSet
    template_name = "netbox_authorized_keys/authorized_key_tabview_table.html"
    table = AuthorizedKeyTable

    def get_table(self, data, request, bulk_actions=True):
        table = super().get_table(data, request, bulk_actions=False)
        table.exclude = ["actions"]
        return table

    def get_permitted_actions(self, user, model=None):
        actions = super().get_permitted_actions(user, model)
        if isinstance(actions, list):
            actions = [action for action in actions if action not in ["bulk_delete", "bulk_edit"]]
        return actions


def create_authorized_key_tab_view(model):
    view_name = f"{model._meta.model_name}-authorized-keys"
    view_path = f"{model._meta.model_name}-authorized-keys"

    class ModelAuthorizedKeyTabView(AuthorizedKeyTabView):
        queryset = model.objects.all()

        if model == Device:
            tab = ViewTab(
                label="Authorized Keys",
                badge=lambda obj: AuthorizedKey.objects.filter(devices=obj.id).count(),
                permission="netbox_authorized_keys.view_authorizedkey",
            )

            def get_children(self, request, parent):
                children = self.child_model.objects.filter(devices=parent.id).restrict(request.user, "view")
                return children

            def get_extra_context(self, request, instance):
                return {
                    "model": "device",
                    "content_type": "authorized_key",
                }

        elif model == VirtualMachine:
            tab = ViewTab(
                label="Authorized Keys",
                badge=lambda obj: AuthorizedKey.objects.filter(virtual_machines=obj.id).count(),
                permission="netbox_authorized_keys.view_authorizedkey",
            )

            def get_children(self, request, parent):
                children = self.child_model.objects.filter(virtual_machines=parent.id).restrict(request.user, "view")
                return children

            def get_extra_context(self, request, instance):
                return {
                    "model": "virtual_machine",
                    "content_type": "authorized_key",
                }

    register_model_view(model, name=view_name, path=view_path)(ModelAuthorizedKeyTabView)


class CredentialTabView(generic.ObjectChildrenView):
    child_model = Credential
    filterset = CredentialFilterSet
    template_name = "netbox_authorized_keys/authorized_key_tabview_table.html"
    table = CredentialTable

    def get_table(self, data, request, bulk_actions=True):
        table = super().get_table(data, request, bulk_actions=False)
        table.exclude = ["actions"]
        return table

    def get_permitted_actions(self, user, model=None):
        actions = super().get_permitted_actions(user, model)
        if isinstance(actions, list):
            actions = [action for action in actions if action not in ["bulk_delete", "bulk_edit"]]
        return actions


def create_credential_tab_view(model):
    view_name = f"{model._meta.model_name}-credentials"
    view_path = f"{model._meta.model_name}-credentials"

    class ModelCredentialTabView(CredentialTabView):
        queryset = model.objects.all()

        if model == Device:
            tab = ViewTab(
                label="Credentials",
                badge=lambda obj: Credential.objects.filter(devices=obj.id).count(),
                permission="netbox_authorized_keys.view_credential",
            )

            def get_children(self, request, parent):
                children = self.child_model.objects.filter(devices=parent.id).restrict(request.user, "view")
                return children

            def get_extra_context(self, request, instance):
                return {
                    "model": "device",
                    "content_type": "credential",
                }

        elif model == VirtualMachine:
            tab = ViewTab(
                label="Credentials",
                badge=lambda obj: Credential.objects.filter(virtual_machines=obj.id).count(),
                permission="netbox_authorized_keys.view_credential",
            )

            def get_children(self, request, parent):
                children = self.child_model.objects.filter(virtual_machines=parent.id).restrict(request.user, "view")
                return children

            def get_extra_context(self, request, instance):
                return {
                    "model": "virtual_machine",
                    "content_type": "credential",
                }

    register_model_view(model, name=view_name, path=view_path)(ModelCredentialTabView)


for model in [Device, VirtualMachine]:
    create_authorized_key_tab_view(model)
    create_credential_tab_view(model)
