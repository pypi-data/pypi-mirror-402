from pydantic import BaseModel


class MQMsgModel(BaseModel):
    topicCode: str | None = None
    msg: str | None = None
    correlationDataId: str | None = None
    dataKey: str | None = None
    manualFlag: bool | None = None
    groupId: str | None = None
    traceId: str | None = None
