from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


# 1. The Request Model (What the client sends to us)
class ReviewRequest(BaseModel):
    code: str = Field(..., min_length=1, description="The source code to be reviewed")
    language: str = Field(default="python", description="The programming language")


# 2. A Sub-Model for a single detected issue
class Issue(BaseModel):
    issue_type: str = Field(
        description="Short name of the issue, e.g., 'Security Risk'"
    )
    severity: str = Field(description="e.g., 'Low', 'Medium', 'High'")
    description: str = Field(description="Detailed explanation of the problem")
    suggestion: Optional[str] = Field(default=None, description="Suggested code fix")


# 3. The Response Model (What we return to the client)
class ReviewResponse(BaseModel):
    id: Optional[int] = Field(
        default=None,
        description="Unique database identifier for the stored review record",
    )
    language: str = Field(description="The language that was reviewed")
    issues: List[Issue] = Field(description="A list of all detected issues")
    created_at: Optional[datetime] = Field(
        default=None,
        description="Timezone-aware UTC timestamp indicating when the review was created",
    )
