from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label="Authorized Keys",
    icon_class="mdi mdi-key",
    groups=(
        (
            "SSH Public Keys",
            (
                PluginMenuItem(
                    link="plugins:netbox_authorized_keys:authorizedkey_list",
                    link_text="Authorized Keys",
                    permissions=["netbox_authorized_keys.view_authorizedkey"],
                ),
            ),
        ),
        (
            "Credentials",
            (
                PluginMenuItem(
                    link="plugins:netbox_authorized_keys:credential_list",
                    link_text="Passwords & Tokens",
                    permissions=["netbox_authorized_keys.view_credential"],
                ),
            ),
        ),
        (
            "Assignments",
            (
                PluginMenuItem(
                    link="plugins:netbox_authorized_keys:authorizedkeydevice_list",
                    link_text="SSH Keys - Devices",
                    permissions=["netbox_authorized_keys.view_authorizedkeydevice"],
                ),
                PluginMenuItem(
                    link="plugins:netbox_authorized_keys:authorizedkeyvirtualmachine_list",
                    link_text="SSH Keys - Virtual Machines",
                    permissions=["netbox_authorized_keys.view_authorizedkeyvirtualmachine"],
                ),
                PluginMenuItem(
                    link="plugins:netbox_authorized_keys:credentialdevice_list",
                    link_text="Credentials - Devices",
                    permissions=["netbox_authorized_keys.view_credentialdevice"],
                ),
                PluginMenuItem(
                    link="plugins:netbox_authorized_keys:credentialvirtualmachine_list",
                    link_text="Credentials - Virtual Machines",
                    permissions=["netbox_authorized_keys.view_credentialvirtualmachine"],
                ),
            ),
        ),
    ),
)
