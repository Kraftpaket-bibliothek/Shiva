from pydantic import BaseModel, Field

#================================DTOs============================
class DataInput(BaseModel):
    Rules: list[str] = Field(default_factory=list, description="Collection of strings for Field A")
    Facts: list[str] = Field(default_factory=list, description="Collection of strings for Field B")
    RequiredOutcome: list[str] = Field(default_factory=list, description="Collection of strings for Field C")
#================================================================

#To note text stream will acts as the orchestrator for this subfolder.
