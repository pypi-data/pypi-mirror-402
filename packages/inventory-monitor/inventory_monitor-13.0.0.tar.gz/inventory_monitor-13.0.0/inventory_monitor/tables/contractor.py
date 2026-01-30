import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from inventory_monitor.models import Contractor


class ContractorTable(NetBoxTable):
    name = tables.Column(linkify=True)
    contracts_count = tables.Column()
    tenant = tables.Column(linkify=True)
    tags = columns.TagColumn()

    class Meta(NetBoxTable.Meta):
        model = Contractor
        fields = (
            "pk",
            "id",
            "name",
            "company",
            "address",
            "tenant",
            "comments",
            "contracts_count",
            "actions",
        )
        default_columns = ("id", "name", "company", "tenant", "contracts_count")
