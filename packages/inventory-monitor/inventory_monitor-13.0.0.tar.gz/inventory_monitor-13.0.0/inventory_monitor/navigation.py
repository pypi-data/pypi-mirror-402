from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label="Inventory Monitor",
    icon_class="mdi mdi-monitor",
    groups=(
        (
            "Assets",
            (
                PluginMenuItem(
                    link="plugins:inventory_monitor:asset_list",
                    link_text="Assets",
                    permissions=["inventory_monitor.view_asset"],
                ),
                PluginMenuItem(
                    link="plugins:inventory_monitor:assettype_list",
                    link_text="Asset Types",
                    permissions=["inventory_monitor.view_assettype"],
                ),
                PluginMenuItem(
                    link="plugins:inventory_monitor:rma_list",
                    link_text="RMA",
                    permissions=["inventory_monitor.view_rma"],
                ),
                PluginMenuItem(
                    link="plugins:inventory_monitor:externalinventory_list",
                    link_text="External Inventory",
                    permissions=["inventory_monitor.view_externalinventory"],
                ),
                PluginMenuItem(
                    link="plugins:inventory_monitor:assetservice_list",
                    link_text="Services",
                    permissions=["inventory_monitor.view_assetservice"],
                ),
            ),
        ),
        (
            "Network Probe",
            (
                PluginMenuItem(
                    link="plugins:inventory_monitor:probe_list",
                    link_text="Probes",
                    permissions=["inventory_monitor.view_probe"],
                ),
                PluginMenuItem(
                    link="plugins:inventory_monitor:probediff",
                    link_text="Network Changes",
                    permissions=["inventory_monitor.view_probediff"],
                ),
            ),
        ),
        (
            "Contracts",
            (
                PluginMenuItem(
                    link="plugins:inventory_monitor:contractor_list",
                    link_text="Contractors",
                    permissions=["inventory_monitor.view_contractor"],
                ),
                PluginMenuItem(
                    link="plugins:inventory_monitor:contract_list",
                    link_text="Contracts",
                    permissions=["inventory_monitor.view_contract"],
                ),
                PluginMenuItem(
                    link="plugins:inventory_monitor:invoice_list",
                    link_text="Invoices",
                    permissions=["inventory_monitor.view_invoice"],
                ),
            ),
        ),
    ),
)
