
import uuid

from pydantic import AliasChoices, BaseModel, Field

from leanautomation.models.item import ItemType, Item


class Dashboard(Item):
    name: str = Field(validation_alias=AliasChoices('displayName'))
    type: ItemType = ItemType.Dashboard
