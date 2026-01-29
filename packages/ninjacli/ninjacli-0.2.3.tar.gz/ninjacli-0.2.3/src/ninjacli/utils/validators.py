from pydantic import BaseModel, Field
from typing import Optional


class OutputFormat(BaseModel):
    step: str = Field(..., description="The ID for the step")
    content: Optional[str] = Field(None, description="Optional string which contains the content for the relevant step")
    tool: Optional[str] = Field(None, description="The ID for the called tool")
    input: Optional[str] = Field(None, description="Optional string which contains the input given to the called tool")
    output: Optional[str] = Field(None, description="Optional string which contains the output given by the called tool")