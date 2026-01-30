from django.urls import include, path
from utilities.urls import get_model_urls

from netbox_authorized_keys import views

urlpatterns = [
    # Authorized Keys - registered views via @register_model_view
    path("authorized-keys/", include(get_model_urls("netbox_authorized_keys", "authorizedkey", detail=False))),
    path("authorized-keys/<int:pk>/", include(get_model_urls("netbox_authorized_keys", "authorizedkey"))),
    # Authorized Key Devices (M2M relations - custom views)
    path("authorized-keys/devices/", views.AuthorizedKeyDeviceListView.as_view(), name="authorizedkeydevice_list"),
    path(
        "authorized-keys/devices/<int:device_id>/add/",
        views.AuthorizedKeyBulkAddView.as_view(),
        name="authorizedkeydevice_add",
    ),
    path(
        "authorized-keys/devices/<int:device_id>/remove/",
        views.AuthorizedKeyBulkRemoveView.as_view(),
        name="authorizedkeydevice_remove",
    ),
    # Authorized Key Virtual Machines (M2M relations - custom views)
    path(
        "authorized-keys/virtual-machines/",
        views.AuthorizedKeyVirtualMachineListView.as_view(),
        name="authorizedkeyvirtualmachine_list",
    ),
    path(
        "authorized-keys/virtual-machines/<int:virtual_machine_id>/add/",
        views.AuthorizedKeyBulkAddView.as_view(),
        name="authorizedkeyvirtualmachine_add",
    ),
    path(
        "authorized-keys/virtual-machines/<int:virtual_machine_id>/remove/",
        views.AuthorizedKeyBulkRemoveView.as_view(),
        name="authorizedkeyvirtualmachine_remove",
    ),
    # Credentials - registered views via @register_model_view
    path("credentials/", include(get_model_urls("netbox_authorized_keys", "credential", detail=False))),
    path("credentials/<int:pk>/", include(get_model_urls("netbox_authorized_keys", "credential"))),
    # Credential Devices (M2M relations - custom views)
    path("credentials/devices/", views.CredentialDeviceListView.as_view(), name="credentialdevice_list"),
    path(
        "credentials/devices/<int:device_id>/add/",
        views.CredentialBulkAddView.as_view(),
        name="credentialdevice_add",
    ),
    path(
        "credentials/devices/<int:device_id>/remove/",
        views.CredentialBulkRemoveView.as_view(),
        name="credentialdevice_remove",
    ),
    # Credential Virtual Machines (M2M relations - custom views)
    path(
        "credentials/virtual-machines/",
        views.CredentialVirtualMachineListView.as_view(),
        name="credentialvirtualmachine_list",
    ),
    path(
        "credentials/virtual-machines/<int:virtual_machine_id>/add/",
        views.CredentialBulkAddView.as_view(),
        name="credentialvirtualmachine_add",
    ),
    path(
        "credentials/virtual-machines/<int:virtual_machine_id>/remove/",
        views.CredentialBulkRemoveView.as_view(),
        name="credentialvirtualmachine_remove",
    ),
]
