from typing import Optional
from pydantic import BaseModel, ConfigDict

class StaffBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    stName: str
    stDept: str
    stTitle: Optional[str] = None
    stPhone: Optional[str] = None
    stEmail: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_manager: bool = False

class StaffCreate(StaffBase):
    pass

class Staff(StaffBase):
    StaffID: int

    class Config:
        from_attributes = True