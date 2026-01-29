from dataclasses import dataclass
from typing import Collection

from buz.event import Event


@dataclass
class EventBusPublishResult:
    published_events: Collection[Event]
    failed_events: Collection[Event]
