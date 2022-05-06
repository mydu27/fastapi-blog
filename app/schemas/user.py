from pydantic import BaseModel, Field


class FeedbackCreateBase(BaseModel):
    study_id: int
    info: str = Field(max_length=500)


class FeedbackUpdateBase(BaseModel):
    info: str = Field(max_length=500)
