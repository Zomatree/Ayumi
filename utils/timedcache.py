"""
Ayumi - Discord bot
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

import asyncio
import datetime as dt
import typing as tp
from collections.abc import Hashable
from dataclasses import dataclass


@dataclass(frozen=True)
class TimedValue:
    value: tp.Any
    expires: dt.datetime
    task: asyncio.Task


NoneType = None.__class__
DelayConvertable = tp.Union[dt.timedelta, dt.datetime, int, None]


class TimedCache:
    """
    A dictionary that delete it's own keys
    a certain amount of time after being inserted

    The timer is reset / updated if an item is inserted in the same slot
    """

    def _make_delays(self, delay: DelayConvertable) -> tp.Tuple[int, dt.datetime]:
        """converts a delay into seconds"""

        dt_now = dt.datetime.now(tz=dt.timezone.utc)

        converter = {
            dt.timedelta: lambda: (delay.total_seconds(), (dt_now + delay)),
            dt.datetime:  lambda: ((dt_now - delay.replace(tzinfo=dt.timezone.utc)).total_seconds(), delay),
            int:          lambda: (delay, dt_now + dt.timedelta(seconds=delay)),
            NoneType:     lambda: (self.timeout, dt_now + dt.timedelta(seconds=self.timeout))
        }

        cls = delay.__class__

        if value := converter.get(cls, None)():
            return value

        raise TypeError("Expected (dt.timedelta, dt.datetime, int, None), got " + cls.__name__)

    def __init__(self, *,
                 timeout: DelayConvertable = None,
                 loop: asyncio.AbstractEventLoop = None,
                 initial_storage: dict = None):

        self.timeout = timeout or 600
        self.timeout, _ = self._make_delays(timeout)
        self.loop = loop or asyncio.get_event_loop()
        self.storage = initial_storage or {}

    async def _timed_del(self, key: Hashable, timeout: int) -> None:
        """Deletes the item and the task associated with it"""
        self.storage.pop(await asyncio.sleep(timeout, result=key))

    def __setitem__(self, key: Hashable, value: tp.Any, *, timeout: int = None) -> None:
        if old_val := self.storage.pop(key, None):
            old_val.task.cancel()

        timeout, final_time = self._make_delays(timeout)
        coro = self._timed_del(key, timeout=timeout)
        self.storage[key] = TimedValue(value=value, expires=final_time, task=self.loop.create_task(coro))

    def __delitem__(self, key: Hashable) -> None:
        self.storage[key].task.cancel()
        del self.storage[key]

    def get(self, key: Hashable, default: tp.Any = None) -> tp.Any:
        """ Get a value from TimedCache. """
        return getattr(self.storage.get(key, default), 'value', default)  # less painful than checking if we got the default

    def set(self, key: Hashable, value: tp.Any, timeout: DelayConvertable = None) -> tp.Any:
        """ Set's the value into TimedCache. """
        self.__setitem__(key, value, timeout=timeout)
        return value

    def __getitem__(self, key: Hashable) -> tp.Any:
        return self.storage[key].value

    def __iter__(self) -> iter:
        return iter(self.storage)

    def __len__(self) -> int:
        return len(self.storage)

    def _clean_data(self) -> tp.Generator[tp.Tuple[Hashable, tp.Tuple[tp.Any, str]], None, None]:
        dt_now = dt.datetime.now(tz=dt.timezone.utc)
        for key, timedvalue in self.storage.items():
            yield key, (timedvalue.value, f'Expires in {(timedvalue.expires - dt_now).total_seconds()} seconds')

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({dict(self._clean_data())})'

    __str__ = __repr__

    def __eq__(self, value: tp.Any):
        return self.storage == value and self.__class__ == value.__class__

    def __bool__(self):
        return bool(self.storage)
