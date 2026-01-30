from dcim.api.serializers_.devices import DeviceSerializer
from dcim.models import Device
from netbox.api.fields import SerializedPKRelatedField
from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers
from virtualization.api.serializers_.virtualmachines import VirtualMachineSerializer
from virtualization.models import VirtualMachine

from netbox_authorized_keys.models import (
    AuthorizedKey,
    AuthorizedKeyDevice,
    AuthorizedKeyVirtualMachine,
    Credential,
    CredentialDevice,
    CredentialVirtualMachine,
)


class AuthorizedKeySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_authorized_keys-api:authorizedkey-detail")
    devices = SerializedPKRelatedField(
        queryset=Device.objects.all(), serializer=DeviceSerializer, nested=True, required=False, many=True
    )

    virtual_machines = SerializedPKRelatedField(
        queryset=VirtualMachine.objects.all(),
        serializer=VirtualMachineSerializer,
        nested=True,
        required=False,
        many=True,
    )

    class Meta:
        model = AuthorizedKey
        fields = [
            "id",
            "display",
            "url",
            "public_key",
            "username",
            "full_name",
            "description",
            "comments",
            "devices",
            "virtual_machines",
            "tags",
        ]
        brief_fields = ("id", "url", "display", "description")


class AuthorizedKeyDeviceSerializer(NetBoxModelSerializer):
    authorized_key = AuthorizedKeySerializer(nested=True)
    device = DeviceSerializer(nested=True)

    class Meta:
        model = AuthorizedKeyDevice
        fields = ["id", "authorized_key", "device"]


class AuthorizedKeyVirtualMachineSerializer(NetBoxModelSerializer):
    authorized_key = AuthorizedKeySerializer(nested=True)
    virtual_machine = VirtualMachineSerializer(nested=True)

    class Meta:
        model = AuthorizedKeyVirtualMachine
        fields = ["id", "authorized_key", "virtual_machine"]


class CredentialSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_authorized_keys-api:credential-detail")
    devices = SerializedPKRelatedField(
        queryset=Device.objects.all(),
        serializer=DeviceSerializer,
        nested=True,
        required=False,
        many=True,
    )

    virtual_machines = SerializedPKRelatedField(
        queryset=VirtualMachine.objects.all(),
        serializer=VirtualMachineSerializer,
        nested=True,
        required=False,
        many=True,
    )

    class Meta:
        model = Credential
        fields = [
            "id",
            "display",
            "url",
            "credential_type",
            "username",
            "owner",
            "credential_storage",
            "used_by",
            "description",
            "comments",
            "devices",
            "virtual_machines",
            "tags",
        ]
        brief_fields = ("id", "url", "display", "username", "credential_type")


class CredentialDeviceSerializer(NetBoxModelSerializer):
    credential = CredentialSerializer(nested=True)
    device = DeviceSerializer(nested=True)

    class Meta:
        model = CredentialDevice
        fields = ["id", "credential", "device"]


class CredentialVirtualMachineSerializer(NetBoxModelSerializer):
    credential = CredentialSerializer(nested=True)
    virtual_machine = VirtualMachineSerializer(nested=True)

    class Meta:
        model = CredentialVirtualMachine
        fields = ["id", "credential", "virtual_machine"]
