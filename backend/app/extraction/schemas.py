from typing import List, Optional
from pydantic import BaseModel, Field

class FieldDefinition(BaseModel):
    name: str = Field(..., description="Canonical field name")
    display_name: str = Field(..., description="Human-readable name")
    data_type: str = Field(..., description="STRING, INTEGER, DECIMAL, DATE, BOOLEAN, CURRENCY, IDENTIFIER")
    required: bool = Field(default=False)
    aliases: List[str] = Field(default_factory=list, description="Alternative labels for OCR matching")

class DocumentSchema(BaseModel):
    schema_name: str
    schema_version: str
    fields: List[FieldDefinition]
