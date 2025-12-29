from typing import Optional
from sqlmodel import Field, SQLModel

class Staff(SQLModel, table=True):
    StaffID: Optional[int] = Field(default=None, primary_key=True)
    stName: str
    stDept: str
    stTitle: Optional[str] = None
    stPhone: Optional[str] = None
    stEmail: Optional[str] = None
    username: Optional[str] = Field(default=None, unique=True)
    password: Optional[str] = None
    is_manager: bool = False