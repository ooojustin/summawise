from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Iterable
from openai.types.beta import Thread as APIThread
from . import utils, ai
from .utils import ApiObjList, BaseApiObj

@dataclass
class Thread(BaseApiObj):
    id: str = ""
    name: str = ""
    created_at: datetime = field(default_factory = utils.utc_now)

    def get_api_obj(self) -> APIThread:
        if not self.id:
            raise ValueError("Thread ID must be specified to retrieve API object.")
        api_thread = ai.get_thread(self.id)
        return api_thread

class ThreadList(ApiObjList[Thread]):

    def __init__(self, assistants: Iterable[Thread] = [], **kwargs):
        super().__init__(assistants, cls = Thread, **kwargs)

    @staticmethod
    def from_dict_list(assistants: Iterable[Thread], **kwargs) -> "ThreadList": # type: ignore
        return ApiObjList.from_dict_list(assistants, cls = Assistant, **kwargs) # type: ignore
