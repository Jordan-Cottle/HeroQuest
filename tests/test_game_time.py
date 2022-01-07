""" Test module for the game_Time.new.py module. """

from datetime import datetime, timedelta

import pytest

from hero_quest.game_time import (
    GLOBAL_CLOCK,
    GameClock,
    TimeSpent,
    Timer,
    TimerComplete,
)


def test_clock_moving_forward_when_time_spent():
    """Ensure GameClock objects move forward when time is spent."""
    clock = GameClock(start=datetime(year=2000, month=1, day=1))

    global_start_time = GLOBAL_CLOCK.current_time

    event = TimeSpent(days=2, hours=3, minutes=4, seconds=5)
    event.fire()

    assert clock.current_time == datetime(
        year=2000, month=1, day=3, hour=3, minute=4, second=5
    )
    assert GLOBAL_CLOCK.current_time == global_start_time + event.timdelta


def test_paused_clock_moving_forward_when_time_spent():
    """Ensure paused GameClock objects do not move forward when time is spent."""
    clock = GameClock(start=datetime(year=2000, month=1, day=1))

    start_time = clock.current_time
    global_start_time = GLOBAL_CLOCK.current_time

    clock.pause()

    event = TimeSpent(days=2, hours=3, minutes=4, seconds=5)
    event.fire()

    assert clock.current_time == start_time
    assert GLOBAL_CLOCK.current_time == global_start_time + event.timdelta


def test_resumed_clock_moving_forward_when_time_spent():
    """Ensure resumed GameClock objects move forward when time is spent."""
    clock = GameClock(start=datetime(year=2000, month=1, day=1))

    start_time = clock.current_time
    global_start_time = GLOBAL_CLOCK.current_time

    clock.pause()

    event = TimeSpent(days=2, hours=3, minutes=4, seconds=5)
    event.fire()

    assert clock.current_time == start_time
    assert GLOBAL_CLOCK.current_time == global_start_time + event.timdelta

    clock.resume()

    event.fire()
    assert clock.current_time == start_time + event.timdelta
    assert GLOBAL_CLOCK.current_time == global_start_time + (2 * event.timdelta)


@pytest.mark.parametrize(
    "start,delta,end",
    [
        (
            datetime(year=2000, month=5, day=5),
            timedelta(days=1),
            datetime(year=2000, month=5, day=4),
        ),
        (
            datetime(year=2000, month=5, day=5),
            timedelta(days=5),
            datetime(year=2000, month=4, day=30),
        ),
        (
            datetime(year=2000, month=1, day=1),
            timedelta(days=1),
            datetime(year=1999, month=12, day=31),
        ),
    ],
)
def test_clock_moving_backwards(start: datetime, delta: timedelta, end: datetime):
    """Ensure GameClock objects can move backwards."""
    clock = GameClock(start=start)

    clock.backward(delta)

    assert clock.current_time == end

    del clock


def test_timer_countdown():
    """Test that timers count down properly when time is spent."""

    timer = Timer(seconds=30)
    assert not timer.complete

    timer_completed = False

    @TimerComplete.handler
    def detect_timer_end(event: TimerComplete):
        nonlocal timer_completed

        assert event.timer is timer
        assert event.timer.complete
        timer_completed = True

    TimeSpent(seconds=30).fire()

    assert timer.complete
    assert (
        timer_completed
    ), "Timers should fire a timer completed event when they complete."

    # Clean up timer complete handler
    TimerComplete.remove_handler(detect_timer_end)


def test_timer_countdown_complete():
    """Test that timers complain if moved forward after being complete."""

    timer_duration = 30
    time_offset = timedelta(seconds=timer_duration)
    timer = Timer(seconds=timer_duration)
    assert not timer.complete

    timer.forward(time_offset)
    assert timer.complete

    # Undo automatic deactivation, simulates a flow/bug/misuse of timer.
    timer.active = True

    with pytest.raises(ValueError):
        timer.forward(time_offset)


def test_timer_moving_backwards():
    """Test that timers complain if moved forward after being complete."""

    timer_duration = 30
    time_offset = timedelta(seconds=5)
    timer = Timer(seconds=timer_duration)
    assert not timer.complete
    assert timer.time_remaining == timedelta(seconds=timer_duration)

    timer.backward(time_offset)
    assert not timer.complete
    assert timer.time_remaining == timedelta(seconds=timer_duration) + time_offset
