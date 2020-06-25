"""
Memento - Logging discord bot
Copyright (C) 2020 - Saphielle Akiyama | saphielle.akiyama@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from asyncio import AbstractEventLoop, Task, get_event_loop, sleep
from collections.abc import Hashable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Generator, Tuple, Union


@dataclass(frozen=True)
class TimedValue:
    value: Any
    expires: datetime
    task: Task


NoneType = None.__class__


class TimedCache:
    """
    A dictionary that delete it's own keys
    a certain amount of time after being inserted

    The timer is reset / updated if an item is inserted in the same slot
    """

    def _make_delays(self, delay: Union[timedelta, datetime, int, None]) -> Tuple[int, datetime]:
        """converts a delay into seconds"""

        dt_now = datetime.now(tz=timezone.utc)

        converter = {
            timedelta: lambda: (delay.total_seconds(), (dt_now + delay)),
            datetime:  lambda: ((dt_now - delay.replace(tzinfo=timezone.utc)).total_seconds(), delay),
            int:       lambda: (delay, dt_now + timedelta(seconds=delay)),
            NoneType:  lambda: (self.timeout, dt_now + timedelta(seconds=self.timeout))
        }

        cls = delay.__class__

        if value := converter.get(cls, None)():
            return value

        raise TypeError("Expected (timedelta, datetime, int, None), got " + cls.__name__)

    def __init__(self, *,
                 timeout: Union[timedelta, datetime, int, None] = None,
                 loop: AbstractEventLoop = None,
                 initial_storage: dict = None):

        self.timeout = timeout or 600
        self.timeout, _ = self._make_delays(timeout)
        self.loop = loop or get_event_loop()
        self.storage = initial_storage or {}

    async def _timed_del(self, key: Hashable, timeout: int) -> None:
        """Deletes the item and the task associated with it"""
        self.storage.pop(await sleep(timeout, result=key))

    def __setitem__(self, key: Hashable, value: Any, *, timeout: int = None) -> None:
        if old_val := self.storage.pop(key, None):
            old_val.task.cancel()

        timeout, final_time = self._make_delays(timeout)
        self.storage[key] = TimedValue(value=value, expires=final_time,
                                       task=self.loop.create_task(self._timed_del(key, timeout=timeout)))

    def __delitem__(self, key: Hashable) -> None:
        self.storage[key].task.cancel()
        del self.storage[key]

    def get(self, key: Hashable, default: Any = None) -> Any:
        """ Get a value from TimedCache. """
        return getattr(self.storage.get(key, default), 'value', default)  # less painful than checking if we got the default

    def set(self, key: Hashable, value: Any, timeout: Union[timedelta, datetime, int, None] = None) -> Any:
        """ Set's the value into TimedCache. """
        self.__setitem__(key, value, timeout=timeout)
        return value

    def __getitem__(self, key: Hashable) -> Any:
        return self.storage[key].value

    def __iter__(self) -> iter:
        return iter(self.storage)

    def __len__(self) -> int:
        return len(self.storage)

    def _clean_data(self) -> Generator[Tuple[Hashable, Tuple[Any, str]], None, None]:
        dt_now = datetime.now(tz=timezone.utc)
        for key, timedvalue in self.storage.items():
            yield key, (timedvalue.value, f'Expires in {(timedvalue.expires - dt_now).total_seconds()} seconds')

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({dict(self._clean_data())})'

    __str__ = __repr__

    def __eq__(self, value: Any):
        return self.storage == value and self.__class__ == value.__class__

    def __bool__(self):
        return bool(self.storage)
