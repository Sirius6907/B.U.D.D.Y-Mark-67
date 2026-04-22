"""
Window Manager — list, focus, minimize, maximize, and close windows.
Safety: Will not close windows belonging to protected processes.
"""

from actions.base import Action, ActionRegistry

# Protected substring list (won't close these via window title matching)
PROTECTED_WINDOW_SUBSTRINGS = ["program manager", "taskbar", "desktop", "buddy"]


def window_manager(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "list_windows").lower()
    
    if action == "list_windows":
        return _list_windows()
    if action == "focus":
        return _focus_window(parameters)
    if action == "minimize":
        return _minimize_window(parameters)
    if action == "maximize":
        return _maximize_window(parameters)
    if action == "close":
        return _close_window(parameters)
    if action == "arrange":
        return _arrange_windows(parameters)
        
    return f"Unknown window_manager action: {action}"


def _list_windows() -> str:
    try:
        import pygetwindow as gw
        windows = gw.getAllTitles()
        # Filter out empty titles
        active_windows = [w for w in windows if w.strip()]
        
        if not active_windows:
            return "No visible windows found."
            
        lines = ["🪟 Open Windows:"]
        for i, w in enumerate(active_windows, 1):
            lines.append(f"  {i}. {w}")
            
        return "\n".join(lines)
    except ImportError:
        return "pygetwindow not installed. Please run: pip install pygetwindow"
    except Exception as e:
        return f"Failed to list windows: {e}"


def _focus_window(params: dict) -> str:
    title = params.get("title", "")
    if not title:
        return "Please specify a window title to focus."
        
    try:
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle(title)
        if not windows:
            return f"No window found matching '{title}'."
            
        win = windows[0]
        if win.isMinimized:
            win.restore()
        win.activate()
        return f"Focused window: '{win.title}'"
    except Exception as e:
        return f"Failed to focus window: {e}"


def _minimize_window(params: dict) -> str:
    title = params.get("title", "")
    if not title:
        return "Please specify a window title to minimize."
        
    try:
        import pygetwindow as gw
        if title.lower() == "all":
            for win in gw.getAllWindows():
                if win.title.strip():
                    win.minimize()
            return "All windows minimized."
            
        windows = gw.getWindowsWithTitle(title)
        if not windows:
            return f"No window found matching '{title}'."
            
        win = windows[0]
        win.minimize()
        return f"Minimized window: '{win.title}'"
    except Exception as e:
        return f"Failed to minimize window: {e}"


def _maximize_window(params: dict) -> str:
    title = params.get("title", "")
    if not title:
        return "Please specify a window title to maximize."
        
    try:
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle(title)
        if not windows:
            return f"No window found matching '{title}'."
            
        win = windows[0]
        win.maximize()
        return f"Maximized window: '{win.title}'"
    except Exception as e:
        return f"Failed to maximize window: {e}"


def _close_window(params: dict) -> str:
    title = params.get("title", "")
    if not title:
        return "Please specify a window title to close."
        
    # Safety check
    title_lower = title.lower()
    for protected in PROTECTED_WINDOW_SUBSTRINGS:
        if protected in title_lower:
            return f"⛔ SAFETY LOCK: Cannot close protected window '{title}'."
            
    try:
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle(title)
        if not windows:
            return f"No window found matching '{title}'."
            
        win = windows[0]
        # Double check exact title safety just in case
        if any(p in win.title.lower() for p in PROTECTED_WINDOW_SUBSTRINGS):
            return f"⛔ SAFETY LOCK: Found window '{win.title}' but it is protected."
            
        win.close()
        return f"Closed window: '{win.title}'"
    except Exception as e:
        return f"Failed to close window: {e}"


def _arrange_windows(params: dict) -> str:
    # A placeholder for advanced arranging
    return "Window arranging is not fully implemented yet. Try using Windows Snap Assist."


class WindowManagerAction(Action):
    @property
    def name(self) -> str:
        return "window_manager"

    @property
    def description(self) -> str:
        return (
            "Manage desktop windows. List open windows, focus, minimize, maximize, or close them. "
            "Use 'all' as title to minimize all windows."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "list_windows | focus | minimize | maximize | close | arrange"},
                "title": {"type": "STRING", "description": "Window title substring to target"},
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return window_manager(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(WindowManagerAction)
