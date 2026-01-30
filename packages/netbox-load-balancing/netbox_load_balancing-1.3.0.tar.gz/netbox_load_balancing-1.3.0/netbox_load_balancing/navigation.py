from django.utils.translation import gettext_lazy as _
from django.conf import settings
from netbox.plugins import PluginMenuButton, PluginMenuItem, PluginMenu

plugin_settings = settings.PLUGINS_CONFIG.get("netbox_load_balancing", {})

virtual_menu_items = (
    PluginMenuItem(
        link="plugins:netbox_load_balancing:virtualippool_list",
        link_text=_("Virtual Pools"),
        permissions=["netbox_load_balancing.view_virtualippool"],
        buttons=(
            PluginMenuButton(
                "plugins:netbox_load_balancing:virtualippool_add",
                _("Add"),
                "mdi mdi-plus-thick",
                permissions=["netbox_load_balancing.add_virtualippool"],
            ),
            PluginMenuButton(
                "plugins:netbox_load_balancing:virtualippool_bulk_import",
                _("Import"),
                "mdi mdi-upload",
                permissions=["netbox_load_balancing.add_virtualippool"],
            ),
        ),
    ),
    PluginMenuItem(
        link="plugins:netbox_load_balancing:virtualip_list",
        link_text=_("Virtual IPs"),
        permissions=["netbox_load_balancing.view_virtualip"],
        buttons=(
            PluginMenuButton(
                "plugins:netbox_load_balancing:virtualip_add",
                _("Add"),
                "mdi mdi-plus-thick",
                permissions=["netbox_load_balancing.add_virtualip"],
            ),
            PluginMenuButton(
                "plugins:netbox_load_balancing:virtualip_bulk_import",
                _("Import"),
                "mdi mdi-upload",
                permissions=["netbox_load_balancing.add_virtualip"],
            ),
        ),
    ),
)

service_menu_items = (
    PluginMenuItem(
        link="plugins:netbox_load_balancing:lbservice_list",
        link_text=_("Services"),
        permissions=["netbox_load_balancing.view_lbservice"],
        buttons=(
            PluginMenuButton(
                "plugins:netbox_load_balancing:lbservice_add",
                _("Add"),
                "mdi mdi-plus-thick",
                permissions=["netbox_load_balancing.add_lbservice"],
            ),
            PluginMenuButton(
                "plugins:netbox_load_balancing:lbservice_bulk_import",
                _("Import"),
                "mdi mdi-upload",
                permissions=["netbox_load_balancing.add_lbservice"],
            ),
        ),
    ),
)

listener_menu_items = (
    PluginMenuItem(
        link="plugins:netbox_load_balancing:listener_list",
        link_text=_("Listeners"),
        permissions=["netbox_load_balancing.view_listener"],
        buttons=(
            PluginMenuButton(
                "plugins:netbox_load_balancing:listener_add",
                _("Add"),
                "mdi mdi-plus-thick",
                permissions=["netbox_load_balancing.add_listener"],
            ),
            PluginMenuButton(
                "plugins:netbox_load_balancing:listener_bulk_import",
                _("Import"),
                "mdi mdi-upload",
                permissions=["netbox_load_balancing.add_listener"],
            ),
        ),
    ),
)

pool_menu_items = (
    PluginMenuItem(
        link="plugins:netbox_load_balancing:pool_list",
        link_text=_("Pools"),
        permissions=["netbox_load_balancing.view_pool"],
        buttons=(
            PluginMenuButton(
                "plugins:netbox_load_balancing:pool_add",
                _("Add"),
                "mdi mdi-plus-thick",
                permissions=["netbox_load_balancing.add_pool"],
            ),
            PluginMenuButton(
                "plugins:netbox_load_balancing:pool_bulk_import",
                _("Import"),
                "mdi mdi-upload",
                permissions=["netbox_load_balancing.add_pool"],
            ),
        ),
    ),
)

monitor_menu_items = (
    PluginMenuItem(
        link="plugins:netbox_load_balancing:healthmonitor_list",
        link_text=_("Health Monitors"),
        permissions=["netbox_load_balancing.view_healthmonitor"],
        buttons=(
            PluginMenuButton(
                "plugins:netbox_load_balancing:healthmonitor_add",
                _("Add"),
                "mdi mdi-plus-thick",
                permissions=["netbox_load_balancing.add_healthmonitor"],
            ),
            PluginMenuButton(
                "plugins:netbox_load_balancing:healthmonitor_bulk_import",
                _("Import"),
                "mdi mdi-upload",
                permissions=["netbox_load_balancing.add_healthmonitor"],
            ),
        ),
    ),
)

member_menu_items = (
    PluginMenuItem(
        link="plugins:netbox_load_balancing:member_list",
        link_text=_("Members"),
        permissions=["netbox_load_balancing.view_member"],
        buttons=(
            PluginMenuButton(
                "plugins:netbox_load_balancing:member_add",
                _("Add"),
                "mdi mdi-plus-thick",
                permissions=["netbox_load_balancing.add_member"],
            ),
            PluginMenuButton(
                "plugins:netbox_load_balancing:member_bulk_import",
                _("Import"),
                "mdi mdi-upload",
                permissions=["netbox_load_balancing.add_member"],
            ),
        ),
    ),
)


if plugin_settings.get("top_level_menu"):
    menu = PluginMenu(
        label=_("Load Balancing"),
        groups=(
            (_("Virtual Pools/Addresses"), virtual_menu_items),
            (_("Services"), service_menu_items),
            (_("Listeners"), listener_menu_items),
            (_("Pools"), pool_menu_items),
            (_("Health Monitors"), monitor_menu_items),
            (_("Members"), member_menu_items),
        ),
        icon_class="mdi mdi-scale-balance",
    )
else:
    menu_items = (
        service_menu_items
        + listener_menu_items
        + pool_menu_items
        + monitor_menu_items
        + member_menu_items
    )
