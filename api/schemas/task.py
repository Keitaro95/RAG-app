from pydantic import BaseModel, Field

class TaskBase(BaseModel):
    title: str | None = Field(None, example="クリーニングを取りに行く")

class TaskCreate(TaskBase):
    pass

class TaskCreateResponse(TaskCreate):
    id: int

    # cruds操作でdb接続するとき使用
    class Config:
        orm_mode = True

class Task(TaskBase):
    id: int
    done: bool | Field(False, description="完了フラグ")

    # cruds操作でdb接続するとき使用
    class Config:
        orm_mode = True
