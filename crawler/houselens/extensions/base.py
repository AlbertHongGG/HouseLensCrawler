from abc import ABC
from ..engine.events import EventBus

class BaseExtension(ABC):
    """
    外掛基底類別
    所有周邊服務 (視覺化、資料庫、通知) 都應繼承此類別，並在 setup 中註冊自己感興趣的事件。
    """
    def setup(self, bus: EventBus):
        """
        供子類別覆寫，以註冊事件監聽器。
        """
        pass
