import django_filters
from dcim.models import Device
from django.db.models import Q
from extras.filters import TagFilter
from netbox.filtersets import BaseFilterSet, NetBoxModelFilterSet
from utilities.filtersets import register_filterset
from virtualization.models import VirtualMachine

from netbox_authorized_keys.models import Credential, CredentialDevice, CredentialVirtualMachine


@register_filterset
class CredentialFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    username = django_filters.CharFilter()
    owner = django_filters.CharFilter()
    used_by = django_filters.CharFilter()
    description = django_filters.CharFilter()
    tag = TagFilter()

    devices = django_filters.ModelMultipleChoiceFilter(
        field_name="devices",
        queryset=Device.objects.all(),
        label="Devices",
    )
    virtual_machines = django_filters.ModelMultipleChoiceFilter(
        field_name="virtual_machines",
        queryset=VirtualMachine.objects.all(),
        label="Virtual Machines",
    )

    assigned_to_device = django_filters.ModelChoiceFilter(
        queryset=Device.objects.all(),
        method="filter_assigned_to_device",
        label="Assigned to Device",
    )

    unassigned_to_device = django_filters.ModelChoiceFilter(
        queryset=Device.objects.all(),
        method="filter_unassigned_to_device",
        label="Unassigned from Device",
    )

    assigned_to_virtual_machine = django_filters.ModelChoiceFilter(
        queryset=VirtualMachine.objects.all(),
        method="filter_assigned_to_virtual_machine",
        label="Assigned to Virtual Machine",
    )

    unassigned_to_virtual_machine = django_filters.ModelChoiceFilter(
        queryset=VirtualMachine.objects.all(),
        method="filter_unassigned_to_virtual_machine",
        label="Unassigned from Virtual Machine",
    )

    def filter_assigned_to_device(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(devices=value)

    def filter_unassigned_to_device(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.exclude(devices=value)

    def filter_assigned_to_virtual_machine(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(virtual_machines=value)

    def filter_unassigned_to_virtual_machine(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.exclude(virtual_machines=value)

    class Meta:
        model = Credential
        fields = [
            "id",
            "credential_type",
            "username",
            "owner",
            "credential_storage",
            "used_by",
            "description",
            "comments",
            "devices",
            "virtual_machines",
        ]

    def search(self, queryset, name, value):
        if value is None or not value.strip():
            return queryset

        filters = (
            Q(username__icontains=value)
            | Q(owner__icontains=value)
            | Q(used_by__icontains=value)
            | Q(description__icontains=value)
            | Q(comments__icontains=value)
            | Q(credential_storage__icontains=value)
            | Q(description__icontains=value)
            | Q(comments__icontains=value)
        )
        return queryset.filter(filters)


class CredentialDeviceFilterSet(BaseFilterSet):
    credential = django_filters.ModelMultipleChoiceFilter(
        field_name="credential",
        queryset=Credential.objects.all(),
        label="Credential",
    )

    device = django_filters.ModelMultipleChoiceFilter(
        field_name="device",
        queryset=Device.objects.all(),
        label="Device",
    )

    class Meta:
        model = CredentialDevice
        fields = ["id", "credential", "device"]


class CredentialVirtualMachineFilterSet(BaseFilterSet):
    credential = django_filters.ModelMultipleChoiceFilter(
        field_name="credential",
        queryset=Credential.objects.all(),
        label="Credential",
    )

    virtual_machine = django_filters.ModelMultipleChoiceFilter(
        field_name="virtual_machine",
        queryset=VirtualMachine.objects.all(),
        label="Virtual Machine",
    )

    class Meta:
        model = CredentialVirtualMachine
        fields = ["id", "credential", "virtual_machine"]
