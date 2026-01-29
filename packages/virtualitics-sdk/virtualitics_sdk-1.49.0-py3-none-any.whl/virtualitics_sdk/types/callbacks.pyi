from _typeshed import Incomplete
from enum import Enum
from typing import Any, Coroutine, Protocol
from virtualitics_sdk.page.card import Card as Card
from virtualitics_sdk.page.drilldown import DrilldownSize as DrilldownSize, DrilldownType as DrilldownType
from virtualitics_sdk.store.drilldown_store_interface import DrilldownStoreInterface as DrilldownStoreInterface
from virtualitics_sdk.store.store_interface import StoreInterface as StoreInterface

class CallbackType(Enum):
    STANDARD: str
    ASSET_DOWNLOAD: str
    DRILLDOWN: str
    PAGE_UPDATE: str
    CONTAINER_TOGGLE: str

class CallbackReturnType(Enum):
    CARD: str
    PAGE: str
    TEXT: str

CALLBACK_EXECUTABLE_TYPES: Incomplete

class DrilldownCallback(Protocol):
    """
    Protocol defining the required callback signature.
    Any callable matching this signature can be used as a drilldown callback.
    """
    def __call__(self, card: Card, input_data: dict[str, str | float | int], store_interface: DrilldownStoreInterface) -> Coroutine[Any, Any, None]:
        """
        Process drilldown data and add content to the card.

        :param card: Card object to add content to
        :param input_data: Dictionary containing input parameters related to the element that was engaged to trigger
                           this modal/popover
        :param store_interface: Optimal Interface for accessing persisted objects during modal/popover creation
        """

class PageUpdateCallback(Protocol):
    """
    Protocol/Type Hint for the CallbackType.PAGE_UPDATE typed callback

    The callback must be an async function with the following signature:

    async def example_callback(store_interface: StoreInterface,
                               step_clients: dict[str, Any] | None = None) -> None:

    :param store_interface: StoreInterface for modifying the page object and accessing stored data
    :param **step_clients: The pre-initialized clients (pyvip, etc) for the step
    """
    def __call__(self, store_interface: StoreInterface, **step_clients: dict[str, Any] | None) -> Coroutine[Any, Any, None]: ...

class StandardEventCallback(Protocol):
    '''
    Protocol/Type Hint for the CallbackType.STANDARD typed callback

    The callback must be an async function with the following signature:

    async def example_callback(store_interface: StoreInterface,
                               step_clients: dict[str, Any] | None = None) -> str:
        return "success message"

    :param store_interface: StoreInterface for modifying the page object and accessing stored data
    :param step_clients: The pre-initialized clients (pyvip, etc) for the step
    '''
    def __call__(self, store_interface: StoreInterface, **step_clients: dict[str, Any] | None) -> Coroutine[Any, Any, str]: ...

class ContainerToggleCallback:
    container_id: Incomplete
    callback_type: Incomplete
    visibility: Incomplete
    def __init__(self, visible: bool, container_id: str) -> None: ...

class AssetDownloadCallback:
    callback_type: Incomplete
    def __init__(self) -> None: ...

def page_update_callback(func: PageUpdateCallback): ...
def auto_refresh_callback(refresh_rate_seconds: int = 500): ...
def drilldown_callback(drilldown_type: DrilldownType, drilldown_size: DrilldownSize):
    """
        :param drilldown_type: DrilldownType.MODAL or DrilldownType.POPOVER
        :param drilldown_size: DrilldownSize.SMALL, MEDIUM, LARGE, SHEET
    """
def standard_event_callback(func: StandardEventCallback): ...
Callback = StandardEventCallback | PageUpdateCallback | DrilldownCallback | ContainerToggleCallback | AssetDownloadCallback
CallbackExecutable = StandardEventCallback | PageUpdateCallback | DrilldownCallback
