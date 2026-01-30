
import uuid

from pydantic import AliasChoices, BaseModel, Field

from leanautomation.models.item import ItemType, Item


class SQLEndpoint(Item):
    name: str = Field(validation_alias=AliasChoices('displayName'))
    type: ItemType = ItemType.SQLEndpoint
