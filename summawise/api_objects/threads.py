from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Tuple
from openai.types.beta import Thread as APIThread
from .. import utils, ai
from .generic import ApiObjList, BaseApiObj

@dataclass
class Thread(BaseApiObj):
    id: str
    name: str
    assistant: Tuple[str, str] # name, id
    created_at: datetime = field(default_factory = utils.utc_now)

    def get_api_obj(self) -> APIThread:
        if not self.id:
            raise ValueError("Thread ID must be specified to retrieve API object.")
        api_thread = ai.get_thread(self.id)
        return api_thread

class ThreadList(ApiObjList[Thread]):

    def __init__(self, threads: Iterable[Thread] = [], **kwargs):
        super().__init__(threads, cls = Thread, **kwargs)

    @staticmethod
    def from_dict_list(threads: Iterable[Thread], **kwargs) -> "ThreadList": # type: ignore
        return ApiObjList.from_dict_list(threads, cls = Thread, **kwargs) # type: ignore
