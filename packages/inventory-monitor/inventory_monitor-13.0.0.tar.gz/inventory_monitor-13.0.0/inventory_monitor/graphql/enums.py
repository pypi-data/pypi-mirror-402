import strawberry

from inventory_monitor.models.asset import (
    AssignmentStatusChoices,
    LifecycleStatusChoices,
)
from inventory_monitor.models.contract import ContractTypeChoices
from inventory_monitor.models.rma import RMAStatusChoices

InventoryMonitorAssignmentStatusEnum = strawberry.enum(
    AssignmentStatusChoices.as_enum(), name="InventoryMonitorAssignmentStatusEnum"
)
InventoryMonitorLifecycleStatusEnum = strawberry.enum(
    LifecycleStatusChoices.as_enum(), name="InventoryMonitorLifecycleStatusEnum"
)
InventoryMonitorContractTypeEnum = strawberry.enum(
    ContractTypeChoices.as_enum(), name="InventoryMonitorContractTypeEnum"
)
InventoryMonitorRMAStatusEnum = strawberry.enum(RMAStatusChoices.as_enum(), name="InventoryMonitorRMAStatusEnum")

__all__ = (
    "InventoryMonitorAssignmentStatusEnum",
    "InventoryMonitorLifecycleStatusEnum",
    "InventoryMonitorContractTypeEnum",
    "InventoryMonitorRMAStatusEnum",
)
