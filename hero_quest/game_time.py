"""Module for containing objects and logic relating to tracking in-game time.

Contains tools for setting up now clocks that count up as well as timers that count down.

This module also contains a few game time related constants, like the start date of the game.
"""
from datetime import datetime, timedelta
from logging import getLogger

from py_events import Event
from py_events.event import Handler

LOGGER = getLogger(__name__)

GAME_START = datetime(year=1234, month=3, day=12, hour=4, minute=53)
TIMER_BASE = datetime(year=5000, month=1, day=1)


class TimeSpent(Event):
    """Event for tracking when, and how much, time is spent doing a task."""

    def __init__(
        self,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> None:
        super().__init__()
        self.timdelta = timedelta(
            days=days, hours=hours, minutes=minutes, seconds=seconds
        )


class TimerComplete(Event):
    """Event fired when a timer completes."""

    def __init__(self, timer: "Timer") -> None:
        super().__init__()

        self.timer: Timer = timer


class GameClock:
    """Simple time tracking object that moves forward when a TimeSpent event is fired."""

    def __init__(self, start: datetime = GAME_START) -> None:
        self.current_time: datetime = start
        self.active: bool = True

        @TimeSpent.handler
        def move_time_forward(event: TimeSpent) -> None:
            """Handle moving the clock forward when time is spent."""
            if not self.active:
                LOGGER.debug(f"Skipping {self} due to being paused")
                return

            self.forward(event.timdelta)

        self.time_passing_handler: Handler = move_time_forward

    def forward(self, offset: timedelta) -> None:
        """Move the clock forward a set amount."""

        self.current_time += offset

    def backward(self, offset: timedelta) -> None:
        """Move the clock backward a set amount."""

        self.current_time -= offset

    def pause(self) -> None:
        """Pause clock from processing TimeSpent events."""

        self.active = False

    def resume(self) -> None:
        """Resume clock processing of TimeSpent events."""

        self.active = True


class Timer(GameClock):
    """Game timer that counts down instead of up when time passes."""

    def __init__(self, minutes: int = 0, seconds: int = 0) -> None:
        duration = minutes * 60 + seconds
        start = TIMER_BASE + timedelta(seconds=duration)
        super().__init__(start=start)

        self.active = True

    @property
    def complete(self) -> bool:
        """Check if the timer is complete or not."""
        return TIMER_BASE >= self.current_time

    @property
    def time_remaining(self) -> timedelta:
        """Calculate how much time is remaining on this timer."""
        return self.current_time - TIMER_BASE

    def forward(self, offset: timedelta) -> None:
        """Reduce time remaining on the timer."""

        if self.active and self.complete:
            raise ValueError("Completed timers should be deactivated.")

        self.current_time -= offset

        if self.complete:
            self.pause()
            TimerComplete(timer=self).fire()

    def backward(self, offset: timedelta) -> None:
        """Increase time remaining on the timer."""
        self.current_time += offset


GLOBAL_CLOCK = GameClock()
