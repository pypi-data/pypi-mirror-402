"""
File: Adroit.py
Description: Python COM wrapper for Adroit OLE server runtime
Author: Diego Acuña
Revision: 0.1.1
Created: 2026-01-15
Last Modified: 2026-01-22
"""
import atexit
from typing import cast, Optional, TYPE_CHECKING, Any
import win32com.client
from win32com.client import gencache
import pythoncom
import pywintypes

if TYPE_CHECKING:
    # static type checkers / editors will read Adroit.pyi for this name
    from Adroit import Adroit as _AdroitBase  # type: ignore
else:
    _AdroitBase = object  # runtime base

AdroitType = Any  # runtime fallback for the _com attribute

# Module-level instance exposed to client code
adroit = None

class AdroitOLE(_AdroitBase):
    """Python COM wrapper for Adroit OLE server runtime"""
    # names on the proxied COM object we want to hide/deny at runtime
    BLOCKED_COM_NAMES = frozenset({
        "AlarmTag",
        "CreateAgent",
        "Join",
        "Leave",
        "LogTag",
        "RemoveAgent",
        "ScanTag",
    })

    def __init__(self, prog_id="adroitserver", auto_connect=True):
        self._prog_id = prog_id
        self._com: Optional["AdroitType"] = None
        self._connected = False
        if auto_connect:
            self.connect()

    def connect(self):
        if self._connected:
            return self
        pythoncom.CoInitialize()
        try:
            # prefer generated wrapper for IntelliSense
            try:
                self._com = cast("AdroitType", gencache.EnsureDispatch(self._prog_id))
            except Exception as e:
                # Some COM servers cannot automate makepy — fall back to dynamic (late) dispatch
                try:
                    self._com = cast("AdroitType", win32com.client.Dispatch(self._prog_id))
                except Exception:
                    raise
            self._connected = True
            return self
        except Exception:
            pythoncom.CoUninitialize()
            raise

    def close(self):
        if not self._connected:
            return
        try:
            # release reference to COM object
            self._com = None
        finally:
            try:
                pythoncom.CoUninitialize()
            finally:
                self._connected = False

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def __getattr__(self, name):
        # deny access to blocked COM names
        if name in self.BLOCKED_COM_NAMES:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        if self._com is None:
            raise AttributeError("Adroit COM object is not connected")
        return getattr(self._com, name)

    # Override COM FetchTags with custom implementation
    def FetchTags(self, *args, **kwargs):
        """
        FetchTags implementation that accepts a list/tuple of tag names.

        If the first positional argument is a list/tuple (or a `tag_names` kwarg is
        provided), the method will iterate each tag string of the form
        "agent.slot" and call the COM `Fetch(agent, slot)` for each, collecting
        results in a dict mapping the original tag string to its value.

        If no list is provided, falls back to the COM `FetchTags` if available.
        """
        # If caller passed a list/tuple of tag names, handle locally:
        if args and isinstance(args[0], (list, tuple)):
            tag_list = args[0]
        elif 'tag_names' in kwargs and isinstance(kwargs['tag_names'], (list, tuple)):
            tag_list = kwargs['tag_names']
        else:
            # Fallback to COM FetchTags if available and caller didn't supply a list
            if self._com is not None and hasattr(self._com, "FetchTags"):
                try:
                    return self._com.FetchTags(*args, **kwargs)
                except Exception:
                    pass
            return []

        results = {}
        # Use the COM `Fetch(agent, slot)` for each tag "agent.slot"
        for tag in tag_list:
            if not isinstance(tag, str):
                raise TypeError("Tag names must be strings in the form 'agent.slot'")
            if '.' not in tag:
                raise ValueError(f"Invalid tag name '{tag}'; expected 'agent.slot'")
            agent, slot = tag.split('.', 1)
            try:
                # call the instance's proxied COM Fetch (avoids depending on module-level `adroit`)
                value = self.Fetch(agent, slot)
            except Exception:
                # On error reading a tag, set value to None rather than failing all
                value = None
            results[tag] = value

        return results

    # Override COM Poke with custom implementation for setting tags
    def SetTag(self, *args, **kwargs):
        """
        SetTag implementation that calls the COM `Poke(agent, slot, value)`

        Supported call patterns:
        - `SetTag(agent, slot, value)` -> sets a single tag
        - `SetTag("agent.slot", value)` -> sets a single tag using dotted name
        - `SetTag({"agent.slot": value, ...})` -> set multiple using a dict
        - `SetTag([("agent.slot", value), ...])` -> set multiple using a list of pairs
        - `SetTag(tag_values=...)` -> same as above using keyword

        If no recognized pattern is provided and the proxied COM object exposes a
        `Poke` method, falls back to calling that directly with the supplied args.
        Returns the COM return value for single sets, or a dict mapping tag string
        to the return value (or `None` on error) for bulk sets.
        """
        # Normalize inputs into a list of (tag, value) pairs for bulk operations
        items = None

        # dict passed as first positional arg
        if args and isinstance(args[0], dict):
            items = list(args[0].items())
        # single positional list/tuple of pairs
        elif args and len(args) == 1 and isinstance(args[0], (list, tuple)):
            candidate = args[0]
            if all(isinstance(el, (list, tuple)) and len(el) == 2 for el in candidate):
                items = list(candidate)
        # tag_values kwarg
        elif 'tag_values' in kwargs:
            tv = kwargs['tag_values']
            if isinstance(tv, dict):
                items = list(tv.items())
            else:
                items = list(tv)

        # direct agent, slot, value call
        if len(args) == 3 and items is None:
            agent, slot, value = args
            try:
                return self.Poke(agent, slot, value)
            except Exception:
                return None

        # dotted tag string and value: SetTag("agent.slot", value)
        if len(args) == 2 and isinstance(args[0], str) and items is None:
            tag, value = args[0], args[1]
            if '.' not in tag:
                raise ValueError(f"Invalid tag name '{tag}'; expected 'agent.slot'")
            agent, slot = tag.split('.', 1)
            try:
                return self.Poke(agent, slot, value)
            except Exception:
                return None

        # If we were able to normalize to items, perform bulk Poke calls
        if items is not None:
            results = {}
            for tag, value in items:
                if not isinstance(tag, str):
                    raise TypeError("Tag names must be strings in the form 'agent.slot'")
                if '.' not in tag:
                    raise ValueError(f"Invalid tag name '{tag}'; expected 'agent.slot'")
                agent, slot = tag.split('.', 1)
                try:
                    res = self.Poke(agent, slot, value)
                except Exception:
                    res = None
                results[tag] = res
            return results

        # Fallback: if proxied COM object exposes Poke, try calling it directly
        if self._com is not None and hasattr(self._com, 'Poke'):
            try:
                return self._com.Poke(*args, **kwargs)
            except Exception:
                pass

        raise TypeError('Unrecognized SetTag arguments')
    
# create the module-level object but avoid connecting automatically at import time
adroit = AdroitOLE(auto_connect=False)
atexit.register(lambda: adroit.close())

def Main():
    try:
        # adroit is available as module variable `adroit`.
        # Connect lazily for interactive use:
        adroit.connect()
        print("Adroit is available as module variable `adroit`.")
        print("Ping ->", adroit.ping())
    except Exception as e:
        print("COM error:", e)
    finally:
        input("\nPress Enter to exit...")
        adroit.close()

if __name__ == "__main__":
    Main()