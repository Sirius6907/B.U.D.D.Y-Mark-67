import webbrowser
from urllib.parse import quote_plus
from typing import Optional, Any, Callable
from actions.base import Action, ActionRegistry

class WeatherReportAction(Action):
    @property
    def name(self) -> str:
        return "weather_report"

    @property
    def description(self) -> str:
        return "Gives the weather report to user"

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "city": {"type": "STRING", "description": "City name"}
            },
            "required": ["city"]
        }

    def execute(self, parameters: dict, player: Optional[Any] = None, speak: Optional[Callable] = None, **kwargs) -> str:
        session_memory = kwargs.get("session_memory")
        city     = parameters.get("city")
        when     = parameters.get("time", "today")  

        if not city or not isinstance(city, str) or not city.strip():
            msg = "Sir, the city is missing for the weather report."
            self._log(msg, player)
            return msg

        city = city.strip()
        when = (when or "today").strip()

        search_query  = f"weather in {city} {when}"
        url           = f"https://www.google.com/search?q={quote_plus(search_query)}"

        try:
            opened = webbrowser.open(url)
            if not opened:
                raise RuntimeError("webbrowser.open returned False")
        except Exception as e:
            msg = f"Sir, I couldn't open the browser for the weather report: {e}"
            self._log(msg, player)
            return msg

        msg = f"Showing the weather for {city}, {when}, sir."
        self._log(msg, player)

        if session_memory:
            try:
                session_memory.set_last_search(query=search_query, response=msg)
            except Exception:
                pass

        return msg

    def _log(self, message: str, player=None) -> None:
        print(f"[Weather] {message}")
        if player:
            try:
                player.write_log(f"Buddy: {message}")
            except Exception:
                pass

ActionRegistry.register(WeatherReportAction)

def weather_action(parameters: dict, player=None, session_memory=None) -> str:
    return ActionRegistry.execute("weather_report", parameters, player=player, session_memory=session_memory)