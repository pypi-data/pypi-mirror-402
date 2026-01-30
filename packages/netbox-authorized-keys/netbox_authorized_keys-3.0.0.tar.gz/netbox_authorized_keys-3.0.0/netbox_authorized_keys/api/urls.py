from rest_framework.routers import DefaultRouter

from netbox_authorized_keys.api.views import (
    AuthorizedKeyDeviceViewSet,
    AuthorizedKeyViewSet,
    AuthorizedKeyVirtualMachineViewSet,
    CredentialDeviceViewSet,
    CredentialViewSet,
    CredentialVirtualMachineViewSet,
)

router = DefaultRouter()
router.register(r"authorized-keys", AuthorizedKeyViewSet)
router.register(r"devices", AuthorizedKeyDeviceViewSet)
router.register(r"virtual-machines", AuthorizedKeyVirtualMachineViewSet)
router.register(r"credentials", CredentialViewSet)
router.register(r"credential-devices", CredentialDeviceViewSet)
router.register(r"credential-virtual-machines", CredentialVirtualMachineViewSet)

urlpatterns = router.urls
