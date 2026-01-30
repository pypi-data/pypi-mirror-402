from netbox.api.viewsets import NetBoxModelViewSet

from netbox_authorized_keys.api.serializers import (
    AuthorizedKeyDeviceSerializer,
    AuthorizedKeySerializer,
    AuthorizedKeyVirtualMachineSerializer,
    CredentialDeviceSerializer,
    CredentialSerializer,
    CredentialVirtualMachineSerializer,
)
from netbox_authorized_keys.filtersets import (
    AuthorizedKeyDeviceFilterSet,
    AuthorizedKeyFilterSet,
    AuthorizedKeyVirtualMachineFilterSet,
    CredentialDeviceFilterSet,
    CredentialFilterSet,
    CredentialVirtualMachineFilterSet,
)
from netbox_authorized_keys.models import (
    AuthorizedKey,
    AuthorizedKeyDevice,
    AuthorizedKeyVirtualMachine,
    Credential,
    CredentialDevice,
    CredentialVirtualMachine,
)


class AuthorizedKeyViewSet(NetBoxModelViewSet):
    queryset = AuthorizedKey.objects.all()
    serializer_class = AuthorizedKeySerializer
    filterset_class = AuthorizedKeyFilterSet


class AuthorizedKeyDeviceViewSet(NetBoxModelViewSet):
    queryset = AuthorizedKeyDevice.objects.all()
    serializer_class = AuthorizedKeyDeviceSerializer
    filterset_class = AuthorizedKeyDeviceFilterSet


class AuthorizedKeyVirtualMachineViewSet(NetBoxModelViewSet):
    queryset = AuthorizedKeyVirtualMachine.objects.all()
    serializer_class = AuthorizedKeyVirtualMachineSerializer
    filterset_class = AuthorizedKeyVirtualMachineFilterSet


class CredentialViewSet(NetBoxModelViewSet):
    queryset = Credential.objects.all()
    serializer_class = CredentialSerializer
    filterset_class = CredentialFilterSet


class CredentialDeviceViewSet(NetBoxModelViewSet):
    queryset = CredentialDevice.objects.all()
    serializer_class = CredentialDeviceSerializer
    filterset_class = CredentialDeviceFilterSet


class CredentialVirtualMachineViewSet(NetBoxModelViewSet):
    queryset = CredentialVirtualMachine.objects.all()
    serializer_class = CredentialVirtualMachineSerializer
    filterset_class = CredentialVirtualMachineFilterSet
