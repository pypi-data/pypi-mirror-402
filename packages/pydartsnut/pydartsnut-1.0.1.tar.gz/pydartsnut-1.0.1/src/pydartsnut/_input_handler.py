"""Input handler module for pixeldarts hardware.

This module provides event-based input handling with debouncing and blocking
mechanisms for dart hits and button presses.
"""
from __future__ import annotations

import time
from typing import List, Tuple, Dict, Set, Any, Union

try:
    from typing import Protocol
except ImportError:
    # Python < 3.8
    from typing_extensions import Protocol

# Type aliases
DartPosition = List[int]  # [x, y] coordinates
DartHit = Tuple[int, int, int]  # (dart_index, x, y)
DartStates = List[DartPosition]  # List of 12 dart positions
ButtonStates = Dict[str, bool]  # Dictionary mapping button names to states


class EngineProtocol(Protocol):
    """Protocol defining the interface for the engine object."""
    
    def get_darts(self) -> DartStates:
        """Get current dart positions from hardware.
        
        Returns:
            List of 12 dart positions, each as [x, y] or [-1, -1] if not present.
        """
        ...
    
    def get_buttons(self) -> ButtonStates:
        """Get current button states from hardware.
        
        Returns:
            Dictionary mapping button names to their current pressed state.
        """
        ...


def _is_invalid_dart(pos: Union[List[int], Tuple[int, ...]]) -> bool:
    """Check if dart position is invalid (-1,-1 or 0,0).
    
    Args:
        pos: A list or tuple representing dart position [x, y].
        
    Returns:
        True if position is invalid ([-1, -1] or [0, 0]), False otherwise.
    """
    if not isinstance(pos, (list, tuple)) or len(pos) < 2:
        return True
    pos_list = [pos[0], pos[1]]
    return pos_list == [-1, -1] or pos_list == [0, 0]


class InputHandler:
    """Handles input from pixeldarts hardware.
    
    This class provides event-based input handling with debouncing and blocking
    mechanisms. It tracks dart hits as events (transitions from invalid to valid
    positions) and manages blocking state to prevent duplicate event detection.
    
    Attributes:
        IDLE_UNBLOCK_DURATION: Duration in seconds before a blocked dart is unblocked.
        engine: The engine object providing get_darts() and get_buttons() methods.
        last_buttons: Previous button states for change detection.
        last_darts: Previous dart states for change detection.
        blocked_dart_indices: Set of dart indices that are currently blocked.
        dart_idle_start_times: Dictionary mapping dart indices to timestamps
            when they started receiving invalid state.
    """

    IDLE_UNBLOCK_DURATION: float = 0.5  # 500 milliseconds in real time

    def __init__(self, engine: EngineProtocol) -> None:
        """Initialize the InputHandler.
        
        Args:
            engine: An object implementing the EngineProtocol interface, providing
                get_darts() and get_buttons() methods.
        """
        self.engine: EngineProtocol = engine
        self.last_buttons: ButtonStates = {}
        self.last_darts: DartStates = []
        
        # Dart index blocking system
        self.blocked_dart_indices: Set[int] = set()  # Track currently blocked dart indices
        self.dart_idle_start_times: Dict[int, float] = {}  # Track when each dart_index started receiving invalid state (timestamp)

    def _update_blocking_timers(self, dart_states: DartStates) -> None:
        """Update blocking timers based on current dart states.
        
        This method manages the unblocking mechanism for blocked darts. When a
        blocked dart receives invalid state ([-1, -1] or [0, 0]) for the duration
        specified by IDLE_UNBLOCK_DURATION, it will be unblocked.
        
        Args:
            dart_states: List of 12 dart positions from engine.get_darts().
                Each position should be [x, y] or [-1, -1] if not present.
        """
        if not isinstance(dart_states, (list, tuple)) or len(dart_states) != 12:
            return
        
        current_time = time.time()
        
        for dart_index in range(12):
            dart = dart_states[dart_index]
            
            # Normalize dart state
            if isinstance(dart, (list, tuple)) and len(dart) >= 2:
                dart_pos = [dart[0], dart[1]]
            else:
                dart_pos = [-1, -1]
            
            is_invalid = _is_invalid_dart(dart_pos)
            
            if dart_index in self.blocked_dart_indices:
                # Dart is blocked - only handle timer updates and unblocking
                if is_invalid:
                    # Receiving [-1, -1] or [0, 0] - track start time if not already tracking
                    if dart_index not in self.dart_idle_start_times:
                        self.dart_idle_start_times[dart_index] = current_time
                    
                    # Check if timer reached unblock duration
                    elapsed_time = current_time - self.dart_idle_start_times[dart_index]
                    if elapsed_time >= self.IDLE_UNBLOCK_DURATION:
                        timestamp = time.strftime("%H:%M:%S", time.localtime())
                        print(f"[{timestamp}] Dart {dart_index} UNBLOCKED after {elapsed_time:.2f}s of invalid state")
                        self.blocked_dart_indices.remove(dart_index)
                        del self.dart_idle_start_times[dart_index]
                else:
                    # Valid position received - reset timer (interrupts countdown)
                    if dart_index in self.dart_idle_start_times:
                        del self.dart_idle_start_times[dart_index]
            # Note: We don't block darts here - blocking only happens in get_dart_hits() when events fire

    def get_dart_hits(self) -> List[DartHit]:
        """Get dart hits from the hardware - event-based detection.
        
        This method only registers dart hits when a dart transitions from an
        invalid state ([-1, -1] or [0, 0]) to a valid position [x, y]. Once a
        dart hit is detected, that dart index is blocked to prevent duplicate
        events. The dart will be unblocked after IDLE_UNBLOCK_DURATION seconds
        of receiving invalid state.
        
        Returns:
            List of tuples (dart_index, x, y) for new dart hits detected
            since the last call. Each tuple contains:
                - dart_index: Integer from 0-11 identifying the dart
                - x: X coordinate (0-127)
                - y: Y coordinate (0-127)
        """
        raw_darts = self.engine.get_darts()
        dart_hits = []

        if self.last_darts == []:
            self.last_darts = raw_darts
            return dart_hits

        if isinstance(raw_darts, (list, tuple)) and len(raw_darts) == 12:
            for index, dart in enumerate(raw_darts):
                if isinstance(dart, (list, tuple)) and len(dart) >= 2:
                    # Event-based debounce: only register hit when transitioning from [-1, -1] to [x, y]
                    last_dart = self.last_darts[index] if index < len(self.last_darts) else [-1, -1]
                    last_invalid = _is_invalid_dart(last_dart)
                    curr_invalid = _is_invalid_dart(dart)
                    
                    if last_invalid and not curr_invalid:
                        # Check if this dart_index is blocked
                        if index not in self.blocked_dart_indices:
                            timestamp = time.strftime("%H:%M:%S", time.localtime())
                            print(f"[{timestamp}] Dart {index} BLOCKED (event fired at [{dart[0]}, {dart[1]}])")
                            dart_hits.append((index, dart[0], dart[1]))
                            # Block this dart_index immediately after detecting the event
                            self.blocked_dart_indices.add(index)
                            # Clear any existing idle timer since we just blocked it
                            if index in self.dart_idle_start_times:
                                del self.dart_idle_start_times[index]
                        else:
                            timestamp = time.strftime("%H:%M:%S", time.localtime())
                            print(f"[{timestamp}] Dart {index} transition detected but was already BLOCKED (skipped)")

            # Update blocking timers based on current dart states (after processing events)
            self._update_blocking_timers(raw_darts)

            # Update last darts
            self.last_darts = [
                (
                    list(p[:2])
                    if isinstance(p, (list, tuple)) and len(p) >= 2
                    else [-1, -1]
                )
                for p in raw_darts
            ]

        return dart_hits

    def get_active_darts(self) -> List[DartHit]:
        """Get all currently active darts on the board.
        
        This method reports ALL active darts regardless of blocking state.
        Blocking only affects get_dart_hits(), not get_active_darts().
        This is useful for registration and continuous tracking where you need
        to see all darts on the board. The blocking timers are still updated
        to allow unblocking of previously blocked darts.

        Returns:
            List of tuples (dart_index, x, y) for all active darts currently
            on the board. Each tuple contains:
                - dart_index: Integer from 0-11 identifying the dart
                - x: X coordinate (0-127)
                - y: Y coordinate (0-127)
        """
        active_darts = []
        current_darts = self.engine.get_darts()

        # Update blocking timers based on current dart states (for unblocking)
        if isinstance(current_darts, (list, tuple)) and len(current_darts) == 12:
            self._update_blocking_timers(current_darts)

        if isinstance(current_darts, (list, tuple)) and len(current_darts) == 12:
            for i in range(12):
                curr_dart = current_darts[i]
                if isinstance(curr_dart, (list, tuple)) and len(curr_dart) >= 2:
                    if not _is_invalid_dart(curr_dart):
                        # Report ALL active darts, regardless of blocking state
                        active_darts.append((i, curr_dart[0], curr_dart[1]))

        return active_darts

    def get_buttons(self) -> ButtonStates:
        """Get button states from the hardware - event-based detection.
        
        This method returns button states that are True only when a button
        transitions from not pressed to pressed. This provides event-based
        button detection rather than continuous state polling.
        
        Returns:
            Dictionary mapping button names to boolean values. Only buttons
            that have just been pressed (transitioned from False to True)
            will have True values. All other buttons will be False.
        """
        raw_buttons = self.engine.get_buttons()
        result = {btn: False for btn in raw_buttons.keys()}
        if self.last_buttons == raw_buttons:
            return result
        for btn_name, button_pressed in raw_buttons.items():
            if button_pressed:
                if self.last_buttons.get(btn_name) != button_pressed:
                    result[btn_name] = True
        self.last_buttons = raw_buttons
        return result

    def reset_blocking_state(self) -> None:
        """Reset the dart index blocking state.
        
        Clears all blocked dart indices and idle timers. This allows all
        dart indices to be eligible for event detection again.
        """
        self.blocked_dart_indices.clear()
        self.dart_idle_start_times.clear()
