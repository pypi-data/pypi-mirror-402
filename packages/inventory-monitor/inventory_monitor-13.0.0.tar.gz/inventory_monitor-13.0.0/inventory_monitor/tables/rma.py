import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from inventory_monitor.models import RMA


class RMATable(NetBoxTable):
    rma_number = tables.Column(linkify=True)
    asset = tables.Column(linkify=True)
    status = columns.ChoiceFieldColumn()
    tags = columns.TagColumn()

    class Meta(NetBoxTable.Meta):
        model = RMA
        fields = (
            "pk",
            "id",
            "rma_number",
            "asset",
            "original_serial",
            "replacement_serial",
            "status",
            "date_issued",
            "date_replaced",
            "issue_description",
            "vendor_response",
            "actions",
        )
        default_columns = (
            "id",
            "rma_number",
            "asset",
            "original_serial",
            "replacement_serial",
            "status",
            "date_issued",
            "date_replaced",
            "actions",
        )
