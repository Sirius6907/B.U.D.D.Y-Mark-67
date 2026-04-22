from .base import ActionRegistry

# Import all modules so they register themselves automatically
import actions.open_app
import actions.weather_report
import actions.send_message
import actions.reminder
import actions.computer_settings
import actions.screen_processor
import actions.youtube_video
import actions.desktop
import actions.browser_control
import actions.file_controller
import actions.code_helper
import actions.dev_agent
import actions.web_search
import actions.computer_control
import actions.game_updater
import actions.flight_finder
import actions.system_actions

import actions.process_manager
import actions.hardware_monitor
import actions.network_monitor
import actions.clipboard_manager
import actions.volume_controller
import actions.power_manager
import actions.notification_sender
import actions.window_manager
import actions.service_controller
import actions.startup_manager

# New modules
import actions.media_player
import actions.wifi_manager
import actions.system_optimizer
import actions.timer_manager
import actions.notes_manager
import actions.disk_analyzer
import actions.wallpaper_changer
import actions.system_restore
import actions.email_client
import actions.password_generator

# Missing from previous session
import actions.mouse_controller
import actions.keyboard_controller
import actions.usb_manager
import actions.system_info
import actions.zip_manager

# The 10 New Modules (Shadowplay, Safety Registry, etc)
import actions.text_to_speech
import actions.image_editor
import actions.registry_manager
import actions.system_diagnostics
import actions.file_searcher
import actions.camera_capture
import actions.pdf_manager
import actions.env_vars_manager
import actions.audio_recorder
import actions.screen_recorder

# Security, Privacy & Maintenance
import actions.firewall_manager
import actions.antivirus_manager
import actions.security_auditor
import actions.privacy_manager
import actions.software_manager

__all__ = ["ActionRegistry"]
