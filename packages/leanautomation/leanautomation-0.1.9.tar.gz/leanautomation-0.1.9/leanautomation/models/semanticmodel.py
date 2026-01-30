

import uuid

from pydantic import AliasChoices, BaseModel, Field

from leanautomation.models.item import Item, ItemType
class SemanticModel(Item):
    name: str = Field(validation_alias=AliasChoices('displayName'))
    type: ItemType = ItemType.SemanticModel