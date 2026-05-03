"""
registries.legacy_aliases — Maps old stub tool names → real namespaced tools.

The planner MUST resolve aliases BEFORE tool lookup.
This is the backward-compatibility bridge that prevents breakage
during the stub→real migration.
"""

from __future__ import annotations

# ── Legacy name → Real namespaced name ──
# Format: "old_stub_name": "browser_<domain>_<operation>"

LEGACY_ALIAS_MAP: dict[str, str] = {
    # ── browser_nav stubs ──
    "browser_nav_tool_1": "browser_nav_navigate_to_url",
    "browser_nav_tool_2": "browser_nav_navigate_to_domain",
    "browser_nav_tool_3": "browser_nav_search_google",
    "browser_nav_tool_4": "browser_nav_refresh_page",
    "browser_nav_tool_5": "browser_nav_go_back",
    "browser_nav_tool_6": "browser_nav_go_forward",
    "browser_nav_tool_7": "browser_nav_search_bing",
    "browser_nav_tool_8": "browser_nav_search_duckduckgo",
    "browser_nav_tool_9": "browser_nav_search_youtube",
    "browser_nav_tool_10": "browser_nav_open_new_window",
    "navigate_to_url": "browser_nav_navigate_to_url",
    "open_url": "browser_nav_navigate_to_url",
    "goto_url": "browser_nav_navigate_to_url",
    "search_google": "browser_nav_search_google",
    "go_back": "browser_nav_go_back",
    "go_forward": "browser_nav_go_forward",
    "refresh": "browser_nav_refresh_page",
    "reload_page": "browser_nav_refresh_page",

    # ── browser_dom stubs ──
    "browser_dom_tool_1": "browser_dom_click_element",
    "browser_dom_tool_2": "browser_dom_click_by_text",
    "browser_dom_tool_3": "browser_dom_click_by_role",
    "browser_dom_tool_4": "browser_dom_get_page_text",
    "browser_dom_tool_5": "browser_dom_press_key",
    "click_element": "browser_dom_click_element",
    "click": "browser_dom_click_element",
    "click_text": "browser_dom_click_by_text",
    "get_text": "browser_dom_get_page_text",
    "press_key": "browser_dom_press_key",

    # ── browser_input stubs ──
    "browser_input_tool_1": "browser_input_type_text",
    "browser_input_tool_2": "browser_input_fill_field",
    "browser_input_tool_3": "browser_input_select_dropdown",
    "browser_input_tool_4": "browser_input_upload_file",
    "browser_input_tool_5": "browser_input_scroll_page",
    "type_text": "browser_input_type_text",
    "fill_field": "browser_input_fill_field",
    "scroll_down": "browser_input_scroll_down",
    "scroll_up": "browser_input_scroll_up",

    # ── browser_extract stubs ──
    "browser_extract_tool_1": "browser_extract_get_title",
    "browser_extract_tool_2": "browser_extract_get_url",
    "browser_extract_tool_3": "browser_extract_get_html",
    "browser_extract_tool_4": "browser_extract_screenshot",
    "browser_extract_tool_5": "browser_extract_get_links",
    "get_title": "browser_extract_get_title",
    "get_url": "browser_extract_get_url",
    "screenshot": "browser_extract_screenshot",
    "get_page_source": "browser_extract_get_html",

    # ── browser_tab stubs ──
    "browser_tab_tool_1": "browser_tab_new_tab",
    "browser_tab_tool_2": "browser_tab_close_tab",
    "browser_tab_tool_3": "browser_tab_switch_tab",
    "browser_tab_tool_4": "browser_tab_list_tabs",
    "browser_tab_tool_5": "browser_tab_duplicate_tab",
    "new_tab": "browser_tab_new_tab",
    "close_tab": "browser_tab_close_tab",
    "switch_tab": "browser_tab_switch_tab",

    # ── browser_auth stubs ──
    "browser_auth_tool_1": "browser_auth_login_with_credentials",
    "browser_auth_tool_2": "browser_auth_detect_login_page",
    "browser_auth_tool_3": "browser_auth_detect_captcha",
    "browser_auth_tool_4": "browser_auth_handle_cookie_consent",
    "browser_auth_tool_5": "browser_auth_dismiss_popup",
    "login": "browser_auth_login_with_credentials",
    "dismiss_popup": "browser_auth_dismiss_popup",
    "accept_cookies": "browser_auth_handle_cookie_consent",
}


def resolve_alias(tool_name: str) -> str:
    """Resolve a legacy tool name to its real namespaced tool.

    Returns the original name if no alias exists (passthrough).
    """
    return LEGACY_ALIAS_MAP.get(tool_name, tool_name)


def is_legacy_name(tool_name: str) -> bool:
    """Check if a name is a legacy alias."""
    return tool_name in LEGACY_ALIAS_MAP


def get_all_aliases_for(real_name: str) -> list[str]:
    """Get all legacy aliases that map to a given real tool name."""
    return [alias for alias, target in LEGACY_ALIAS_MAP.items() if target == real_name]
