from pydantic import BaseModel


class JobBase(BaseModel):
    title: str
    company: str
    location: str | None = None
    link: str | None = None
    salary: str | None = None
    status: str = "Applied"
    notes: str | None = None


class JobCreate(JobBase):
    pass


class JobUpdate(JobBase):
    pass


class JobOut(JobBase):
    id: int

    class Config:
        from_attributes = True
