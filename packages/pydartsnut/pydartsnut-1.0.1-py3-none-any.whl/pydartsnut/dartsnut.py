"""Main module for Dartsnut hardware interface.

This module provides the Dartsnut class for interfacing with Dartsnut hardware,
including shared memory communication, dart position tracking, button state
monitoring, and data persistence.
"""
from __future__ import annotations

from multiprocessing import shared_memory, resource_tracker
import argparse
import sys
import json
import math
import time
import signal
import os
from typing import List, Dict, Any, Optional, Union
from ._input_handler import InputHandler, DartHit, ButtonStates, DartStates

class Dartsnut:
    """Main interface for Dartsnut hardware.
    
    This class provides methods to interact with Dartsnut hardware including:
    - Reading dart positions from the board
    - Reading button states
    - Updating the display frame buffer
    - Managing persistent data storage
    - Event-based input handling via InputHandler
    
    Attributes:
        running: Boolean flag indicating if the application should continue running.
        widget_params: Dictionary of widget parameters parsed from command line.
        shm: Shared memory object for display communication.
        shm_pdo: Shared memory object for input data.
        shm_buffer: Buffer view of display shared memory.
        shm_pdo_buf: Buffer view of input shared memory.
        data_store_path: Path to the directory for data storage.
        data_store_file: Path to the JSON file for data storage.
        input_handler: InputHandler instance for event-based input handling.
    """
    
    def __init__(self) -> None:
        # Register the signal handler for SIGINT
        signal.signal(signal.SIGINT, self.sigint_handler)
        
        # prevent the shared memory from being tracked by resource_tracker
        self.remove_shm_from_resource_tracker()

        # running state
        self.running = True

        # parse the arguments
        parser = argparse.ArgumentParser(description="Dartsnut")
        parser.add_argument(
            "--params",
            type=str,
            default="{}",
            help="JSON string for widget parameters"
        )
        parser.add_argument(
            "--shm",
            type=str,
            default="pdishm",
            help="Shared memory name"
        )
        parser.add_argument(
            "--data-store",
            type=str,
            default=None,
            help="Path to data store directory (defaults to script directory)"
        )
        args = parser.parse_args()
        # load the parameters
        try:
            self.widget_params = json.loads(args.params)
        except json.JSONDecodeError as e:
            print(args.params)
            print(f"Error decoding JSON: {e}")
            sys.exit(1)
        # load the shared memory for display
        try:
            self.shm = shared_memory.SharedMemory(name=args.shm, create=False)
        except FileNotFoundError:
            print(f"Shared memory file '{args.shm}' not found.")
            sys.exit(1)
        # map the input shared memory
        try:
            self.shm_pdo = shared_memory.SharedMemory(name="pdoshm", create=False)
        except FileNotFoundError:
            print(f"Shared memory file 'pdoshm' not found.")
            sys.exit(1)
        self.shm_buffer = self.shm.buf
        self.shm_pdo_buf = self.shm_pdo.buf
        
        # Initialize data store
        if args.data_store:
            self.data_store_path = args.data_store
        else:
            # Default to script directory
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                self.data_store_path = script_dir
            except NameError:
                # __file__ not available, fallback to current directory
                self.data_store_path = os.getcwd()
        
        # Create data store directory if it doesn't exist
        try:
            os.makedirs(self.data_store_path, exist_ok=True)
        except OSError as e:
            print(f"Warning: Could not create data store directory '{self.data_store_path}': {e}")
        
        # Set JSON file path
        self.data_store_file = os.path.join(self.data_store_path, "data.json")
        
        # Initialize input handler
        self.input_handler = InputHandler(self)

    def remove_shm_from_resource_tracker(self) -> None:
        """Monkey-patch multiprocessing.resource_tracker so SharedMemory won't be tracked.
        
        This is a workaround for a Python bug where SharedMemory objects are
        incorrectly tracked by the resource tracker, causing cleanup issues.
        
        More details at: https://bugs.python.org/issue38119
        """

        def fix_register(name, rtype):
            if rtype == "shared_memory":
                return
            return resource_tracker._resource_tracker.register(name, rtype)
        resource_tracker.register = fix_register

        def fix_unregister(name, rtype):
            if rtype == "shared_memory":
                return
            return resource_tracker._resource_tracker.unregister(name, rtype)
        resource_tracker.unregister = fix_unregister

        if "shared_memory" in resource_tracker._CLEANUP_FUNCS:
            del resource_tracker._CLEANUP_FUNCS["shared_memory"]

    def sigint_handler(self, signum: int, frame: Any) -> None:
        """Handle SIGINT signal (Ctrl+C).
        
        This function will be called when a SIGINT signal is received.
        Sets the running flag to False to allow graceful shutdown.
        
        Args:
            signum: Signal number (unused).
            frame: Current stack frame (unused).
        """
        self.running = False

    def update_frame_buffer(self, frame: Union[bytearray, Any]) -> bool:
        """Update the shared memory buffer with the given image or buffer.
        
        The frame can be either a bytearray or any object with a tobytes() method
        (such as PIL Image objects). The buffer must be in RGB888 format.
        
        Args:
            frame: Image data as bytearray or object with tobytes() method.
                Must be in RGB888 format.
        
        Returns:
            True if the frame buffer was successfully updated, False otherwise.
            Returns False if the display buffer is busy (status == 2) or in
            an invalid state.
        
        Raises:
            TypeError: If frame is not a bytearray and doesn't have a tobytes() method.
        """
        if isinstance(frame, bytearray):
            image_bytes = frame
        elif hasattr(frame, 'tobytes'):
            image_bytes = frame.tobytes()
        else:
            raise TypeError("frame must be a bytearray or have a 'tobytes' method")
        
        if (self.shm_buffer[0] == 2):
            return False
        elif (self.shm_buffer[0] == 1):
            self.shm_buffer[1:len(image_bytes)+1] = image_bytes
            self.shm_buffer[0] = 0
            return True
        else:
            return False

    def get_darts(self) -> DartStates:
        """Get current dart positions from the hardware.
        
        Reads raw dart positions from shared memory and maps them to the
        display coordinate system (0-127 for both x and y). Invalid positions
        are represented as [-1, -1].
        
        Returns:
            List of 12 dart positions. Each position is a list [x, y] where:
                - x, y: Coordinates in range 0-127, or -1 if dart not present
                - Positions are mapped from hardware coordinates (1800-39800)
                  to display coordinates (0-127)
        """
        darts: DartStates = []
        buf = self.shm_pdo_buf
        for i in range(12):
            x = buf[i*4+1] + (buf[i*4+2] << 8)
            y = buf[i*4+3] + (buf[i*4+4] << 8)
            if (x != 0xffff) & (y != 0xffff):
                if (y <= 1800):
                    y_mapped = 0
                elif (y >= 39800):
                    y_mapped = 127
                else:
                    y_mapped = math.floor((y - 1800) / 299)
                
                if (x <= 1800):
                    x_mapped = 0
                elif (x >= 39800):
                    x_mapped = 127
                else:
                    x_mapped = math.floor((x - 1800) / 299)
                darts.append([x_mapped, y_mapped])
            else:
                darts.append([-1, -1])
        return darts

    def get_buttons(self) -> ButtonStates:
        """Get current button states from the hardware.
        
        Reads button states from shared memory with debouncing (30ms delay).
        This method returns the current state of all buttons, not just events.
        For event-based button detection (only True on press), use get_button_events().
        
        Returns:
            Dictionary mapping button names to their current pressed state:
                - "btn_a": Button A state
                - "btn_b": Button B state
                - "btn_up": Up button state
                - "btn_right": Right button state
                - "btn_left": Left button state
                - "btn_down": Down button state
                - "btn_home": Home button state
                - "btn_reserved": Reserved button state
        """
        buttons: ButtonStates = {
            "btn_a": bool(self.shm_pdo_buf[0] & 1),
            "btn_b": bool(self.shm_pdo_buf[0] & 2),
            "btn_up": bool(self.shm_pdo_buf[0] & 4),
            "btn_right": bool(self.shm_pdo_buf[0] & 8),
            "btn_left": bool(self.shm_pdo_buf[0] & 16),
            "btn_down": bool(self.shm_pdo_buf[0] & 32),
            "btn_home": bool(self.shm_pdo_buf[0] & 64),
            "btn_reserved" : bool(self.shm_pdo_buf[0] & 128),
        }
        if not hasattr(self, "_button_states"):
            self._button_states = {k: False for k in buttons}
            self._button_last = {k: False for k in buttons}
            self._button_times = {k: 0 for k in buttons}
            self._debounce_delay = 0.03  # 30 ms debounce

        now = time.time()
        for k in buttons:
            if buttons[k] != self._button_last[k]:
                self._button_times[k] = now
                self._button_last[k] = buttons[k]
            if now - self._button_times[k] >= self._debounce_delay:
                self._button_states[k] = buttons[k]
            buttons[k] = self._button_states[k]
        return buttons

    def set_brightness(self, brightness: int) -> None:
        """Set the display brightness.
        
        Args:
            brightness: Brightness level between 10 and 100 (inclusive).
                Values outside this range are ignored.
        """
        if (10 <= brightness <= 100):
            self.shm_pdo_buf[49] = brightness

    def set_value(self, key: str, value: Any) -> None:
        """Set a key-value pair in the data store.
        
        The value is stored in a JSON file atomically (using a temporary file
        and rename operation) to prevent corruption during writes.
        
        Args:
            key: The key to store the value under.
            Must be a valid JSON key (string).
            value: Any JSON-serializable value (dict, list, str, int, float, bool, None).
        
        Raises:
            IOError: If the data store file cannot be written.
        """
        # Load existing data
        data = {}
        if os.path.exists(self.data_store_file):
            try:
                with open(self.data_store_file, 'r') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # If file is corrupted, start with empty dict
                print(f"Warning: Could not read data store file: {e}")
                data = {}
        
        # Update the key-value pair
        data[key] = value
        
        # Write atomically (write to temp file, then rename)
        temp_file = self.data_store_file + '.tmp'
        try:
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            # Atomic rename
            os.replace(temp_file, self.data_store_file)
        except (IOError, OSError) as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
            raise IOError(f"Could not write to data store file: {e}")

    def get_value(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a value from the data store.
        
        Args:
            key: The key to retrieve.
            default: The default value to return if key doesn't exist.
                Defaults to None.
        
        Returns:
            The value associated with the key, or default if key doesn't exist
            or if the data store file cannot be read.
        """
        if not os.path.exists(self.data_store_file):
            return default
        
        try:
            with open(self.data_store_file, 'r') as f:
                data = json.load(f)
            return data.get(key, default)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read data store file: {e}")
            return default

    def get_dart_hits(self) -> List[DartHit]:
        """Get dart hits from the hardware - event-based detection.
        
        This method only registers dart hits when a dart transitions from an
        invalid state ([-1, -1] or [0, 0]) to a valid position [x, y]. Once a
        dart hit is detected, that dart index is blocked to prevent duplicate
        events. The dart will be unblocked after 0.5 seconds of receiving invalid state.
        
        Returns:
            List of tuples (dart_index, x, y) for new dart hits detected
            since the last call. Each tuple contains:
                - dart_index: Integer from 0-11 identifying the dart
                - x: X coordinate (0-127)
                - y: Y coordinate (0-127)
        """
        return self.input_handler.get_dart_hits()

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
        return self.input_handler.get_active_darts()

    def reset_blocking_state(self) -> None:
        """Reset the dart index blocking state.
        
        Clears all blocked dart indices and idle timers. This allows all
        dart indices to be eligible for event detection again.
        """
        self.input_handler.reset_blocking_state()

    def get_button_events(self) -> ButtonStates:
        """Get button states from the hardware - event-based detection.
        
        This method returns button states that are True only when a button
        transitions from not pressed to pressed. This provides event-based
        button detection rather than continuous state polling.
        
        Returns:
            Dictionary mapping button names to boolean values. Only buttons
            that have just been pressed (transitioned from False to True)
            will have True values. All other buttons will be False.
            Button names: "btn_a", "btn_b", "btn_up", "btn_right", "btn_left",
            "btn_down", "btn_home", "btn_reserved".
        """
        return self.input_handler.get_buttons()
