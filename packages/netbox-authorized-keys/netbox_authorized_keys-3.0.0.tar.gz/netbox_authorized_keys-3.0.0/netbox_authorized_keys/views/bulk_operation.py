from dcim.models import Device
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from netbox.views import generic
from virtualization.models import VirtualMachine

from netbox_authorized_keys import forms, models


class BaseBulkActionView(generic.object_views.BaseObjectView):
    """
    Base class for bulk add/remove operations on devices and virtual machines.

    Subclasses must define:
    - queryset: QuerySet for the model being managed
    - default_return_url: URL name to redirect to after operation
    - form_field_name: Name of the form field containing items (e.g., "authorized_keys", "credentials")
    - item_type_name: Display name for items (e.g., "Authorized Keys", "Credentials")
    """

    queryset = None
    default_return_url = None
    form_class = None
    form_field_name = None  # e.g., "authorized_keys" or "credentials"
    item_type_name = None  # e.g., "Authorized Keys" or "Credentials"

    def dispatch(self, request, *args, **kwargs):
        """Resolve the target object (Device or VirtualMachine) from URL kwargs."""
        if kwargs.get("device_id"):
            self.object = get_object_or_404(Device, pk=kwargs.get("device_id"))
        elif kwargs.get("virtual_machine_id"):
            self.object = get_object_or_404(VirtualMachine, pk=kwargs.get("virtual_machine_id"))

        return super().dispatch(request, *args, **kwargs)

    def get_extra_context(self, request, instance):
        """Build context for template rendering."""
        return_url = request.GET.get("return_url", reverse(self.default_return_url))

        params = {"obj": self.object, "instance": instance} if instance else {"obj": self.object}
        form = self.form_class(**params)
        return {
            "form": form,
            "object": self.object,
            "return_url": return_url,
            "item_type": self.item_type_name,
        }

    def get(self, request, *args, **kwargs):
        """Handle GET requests - display the form."""
        context = self.get_extra_context(request, instance=None)
        return render(request, self.template_name, context)

    def perform_action(self, item, object):
        """
        Perform the bulk action on a single item.

        Args:
            item: The item being added/removed (AuthorizedKey or Credential)
            object: The target object (Device or VirtualMachine)
        """
        raise NotImplementedError("Subclasses must implement perform_action")

    def post(self, request, *args, **kwargs):
        """Handle POST requests - process the form submission."""
        return_url = request.GET.get("return_url", reverse(self.default_return_url))
        form = self.form_class(request.POST)

        if form.is_valid():
            items = form.cleaned_data[self.form_field_name]

            for item in items:
                self.perform_action(item, self.object)

            return redirect(return_url)

        context = self.get_extra_context(request, instance=None)
        context.update({"form": form})
        return render(request, self.template_name, context)


class AuthorizedKeyBulkActionView(BaseBulkActionView):
    """Base class for AuthorizedKey bulk operations."""

    queryset = models.AuthorizedKey.objects.all()
    default_return_url = "plugins:netbox_authorized_keys:authorizedkey_list"
    form_field_name = "authorized_keys"
    item_type_name = "Authorized Keys"


class AuthorizedKeyBulkAddView(AuthorizedKeyBulkActionView):
    template_name = "netbox_authorized_keys/bulk_authorized_keys.html"
    form_class = forms.AuthorizedKeyAddForm

    def get_extra_context(self, request, instance):
        context = super().get_extra_context(request, instance)
        context.update({"action_text": "Add", "preposition": "to", "button_class": "success"})
        return context

    def get_required_permission(self):
        return "netbox_authorized_keys.add_authorizedkey"

    def perform_action(self, key, object):
        if isinstance(object, Device):
            key.devices.add(object)
        elif isinstance(object, VirtualMachine):
            key.virtual_machines.add(object)


class AuthorizedKeyBulkRemoveView(AuthorizedKeyBulkActionView):
    template_name = "netbox_authorized_keys/bulk_authorized_keys.html"
    form_class = forms.AuthorizedKeyRemoveForm

    def get_extra_context(self, request, instance):
        context = super().get_extra_context(request, instance)
        context.update({"action_text": "Remove", "preposition": "from", "button_class": "danger"})
        return context

    def get_required_permission(self):
        return "netbox_authorized_keys.delete_authorizedkey"

    def perform_action(self, key, object):
        if isinstance(object, Device):
            key.devices.remove(object)
        elif isinstance(object, VirtualMachine):
            key.virtual_machines.remove(object)


class CredentialBulkActionView(BaseBulkActionView):
    """Base class for Credential bulk operations."""

    queryset = models.Credential.objects.all()
    default_return_url = "plugins:netbox_authorized_keys:credential_list"
    form_field_name = "credentials"
    item_type_name = "Credentials"


class CredentialBulkAddView(CredentialBulkActionView):
    template_name = "netbox_authorized_keys/bulk_authorized_keys.html"
    form_class = forms.CredentialAddForm

    def get_extra_context(self, request, instance):
        context = super().get_extra_context(request, instance)
        context.update({"action_text": "Add", "preposition": "to", "button_class": "success"})
        return context

    def get_required_permission(self):
        return "netbox_authorized_keys.add_credential"

    def perform_action(self, credential, object):
        if isinstance(object, Device):
            credential.devices.add(object)
        elif isinstance(object, VirtualMachine):
            credential.virtual_machines.add(object)


class CredentialBulkRemoveView(CredentialBulkActionView):
    template_name = "netbox_authorized_keys/bulk_authorized_keys.html"
    form_class = forms.CredentialRemoveForm

    def get_extra_context(self, request, instance):
        context = super().get_extra_context(request, instance)
        context.update({"action_text": "Remove", "preposition": "from", "button_class": "danger"})
        return context

    def get_required_permission(self):
        return "netbox_authorized_keys.delete_credential"

    def perform_action(self, credential, object):
        if isinstance(object, Device):
            credential.devices.remove(object)
        elif isinstance(object, VirtualMachine):
            credential.virtual_machines.remove(object)
