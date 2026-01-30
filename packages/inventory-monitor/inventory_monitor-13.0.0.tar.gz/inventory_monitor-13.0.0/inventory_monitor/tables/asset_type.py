import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from inventory_monitor.models import AssetType


class AssetTypeTable(NetBoxTable):
    name = tables.Column(linkify=True)
    color = columns.ColorColumn()
    tags = columns.TagColumn()

    class Meta(NetBoxTable.Meta):
        model = AssetType
        fields = (
            "pk",
            "id",
            "name",
            "slug",
            "description",
            "color",
            "asset_count",
            "tags",
            "actions",
        )
        default_columns = (
            "name",
            "slug",
            "description",
            "color",
            "asset_count",
            "tags",
        )
