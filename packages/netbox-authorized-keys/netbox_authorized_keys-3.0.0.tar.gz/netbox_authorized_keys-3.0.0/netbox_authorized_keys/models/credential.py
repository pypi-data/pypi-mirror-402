from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from netbox.models import NetBoxModel
from utilities.choices import ChoiceSet
from utilities.querysets import RestrictedQuerySet


class CredentialTypeChoices(ChoiceSet):
    key = "Credential.credential_type"

    TYPE_PASSWORD = "password"
    TYPE_TOKEN = "token"
    TYPE_API_KEY = "api_key"

    CHOICES = [
        (TYPE_PASSWORD, _("Password"), "blue"),
        (TYPE_TOKEN, _("Token"), "green"),
        (TYPE_API_KEY, _("API Key"), "orange"),
    ]


class Credential(NetBoxModel):
    credential_type = models.CharField(
        max_length=50,
        choices=CredentialTypeChoices,
        default=CredentialTypeChoices.TYPE_PASSWORD,
        verbose_name=_("Credential Type"),
    )
    username = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        verbose_name=_("Username / Service Account"),
    )
    owner = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        verbose_name=_("Owner"),
        help_text=_("Login of the administrator/owner (e.g., admin, jkrupa)"),
    )
    credential_storage = models.TextField(
        verbose_name=_("Credential Storage"),
        blank=True,
        null=False,
        default="",
        help_text=_("Key fingerprint, hash, or storage location (e.g., 1Password, .env file, LastPass, Keychain)"),
    )
    used_by = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        default="",
        verbose_name=_("Used By"),
        help_text=_("Which server uses this credential"),
    )
    description = models.TextField(
        verbose_name=_("Description"),
        blank=False,
        default="",
        null=False,
        help_text=_("Information about what the user/credential does, which service, etc. (supports Markdown)"),
    )
    comments = models.TextField(
        blank=True,
        default="",
        null=False,
        verbose_name=_("Comments"),
        help_text=_("Additional notes, restrictions, or usage instructions"),
    )

    devices = models.ManyToManyField(
        to="dcim.device",
        related_name="credentials",
        blank=True,
        through="netbox_authorized_keys.CredentialDevice",
        verbose_name=_("Devices"),
    )

    virtual_machines = models.ManyToManyField(
        to="virtualization.virtualmachine",
        related_name="credentials",
        blank=True,
        through="netbox_authorized_keys.CredentialVirtualMachine",
        verbose_name=_("Virtual Machines"),
    )

    objects = RestrictedQuerySet.as_manager()

    def get_absolute_url(self):
        return reverse("plugins:netbox_authorized_keys:credential", args=[self.pk])

    def serialize_object(self, *, exclude=None):
        data = super().serialize_object(exclude=exclude or [])
        data["devices"] = list(self.devices.values_list("pk", flat=True))
        data["virtual_machines"] = list(self.virtual_machines.values_list("pk", flat=True))
        return data

    def __str__(self):
        return f"#{self.id}: {self.username} [{self.get_credential_type_display()}] / {self.used_by}"

    def get_credential_type_color(self):
        """Return the color associated with the credential type."""
        return CredentialTypeChoices.colors.get(self.credential_type)

    class Meta:
        ordering = ["id"]
        verbose_name = _("Credential")
        verbose_name_plural = _("Credentials")

    @property
    def rendered_fingerprint(self) -> str:
        """
        Returns a shortened version of the credential storage info.
        Example: "sha256:...Kj38dK2p"
        """
        if not self.credential_storage:
            return _("No storage info")

        if len(self.credential_storage) > 16:
            return f"...{self.credential_storage[-8:]}"
        return self.credential_storage


class CredentialDevice(models.Model):
    credential = models.ForeignKey(
        to="netbox_authorized_keys.Credential",
        on_delete=models.CASCADE,
    )
    device = models.ForeignKey(
        to="dcim.Device",
        on_delete=models.CASCADE,
    )

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        unique_together = ("credential", "device")
        ordering = ["id"]

    def __str__(self):
        return f"{self.credential} - {self.device}"


class CredentialVirtualMachine(models.Model):
    credential = models.ForeignKey(
        to="netbox_authorized_keys.Credential",
        on_delete=models.CASCADE,
    )
    virtual_machine = models.ForeignKey(
        to="virtualization.VirtualMachine",
        on_delete=models.CASCADE,
    )

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        unique_together = ("credential", "virtual_machine")
        ordering = ["id"]

    def __str__(self):
        return f"{self.credential} - {self.virtual_machine}"
