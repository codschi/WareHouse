from pydantic import BaseModel

class HTTPError(BaseModel):
    detail: str

    class Config:
        json_schema_extra = {
            "example": {"detail": "無法刪除：該資料尚有關聯紀錄。"}
        }