"""
Notification Sender — push Windows toast notifications.
"""

from actions.base import Action, ActionRegistry


def notification_sender(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "send").lower()
    
    if action == "send":
        return _send_notification(parameters)
        
    return f"Unknown notification_sender action: {action}"


def _send_notification(params: dict) -> str:
    title = params.get("title", "BUDDY Notification")
    message = params.get("message", "")
    duration = int(params.get("duration", 5))
    
    if not message:
        return "Please provide a message for the notification."
        
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            title,
            message,
            icon_path=None,
            duration=duration,
            threaded=True
        )
        return f"Notification sent: '{title}: {message}'"
    except ImportError:
        pass
    except Exception as e:
        return f"Failed to send notification via win10toast: {e}"
        
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="BUDDY",
            timeout=duration
        )
        return f"Notification sent: '{title}: {message}'"
    except ImportError:
        pass
    except Exception as e:
        return f"Failed to send notification via plyer: {e}"
        
    return "Could not send notification (no supported library found). Install win10toast or plyer."


class NotificationSenderAction(Action):
    @property
    def name(self) -> str:
        return "notification_sender"

    @property
    def description(self) -> str:
        return "Send a native Windows toast notification."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "send"},
                "title": {"type": "STRING", "description": "Notification title"},
                "message": {"type": "STRING", "description": "Notification body message"},
                "duration": {"type": "INTEGER", "description": "Duration in seconds (default: 5)"},
            },
            "required": ["action", "message"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return notification_sender(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(NotificationSenderAction)
