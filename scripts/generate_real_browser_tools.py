"""
BUDDY MK67 — Real Browser Tool Generator
Generates native browser tools from domain specifications.
Each tool follows: browser_<domain>_<operation> naming convention.
Each tool maps to ONE deterministic operation.
All tools delegate to BrowserEngine and return build_tool_result.
"""
import os
import textwrap

DOMAINS = {
    "browser_nav": {
        "module": "navigate_gen",
        "tools": [
            ("browser_nav_go_forward",      "Navigate forward in browser history.",   "go_forward",     [], "navigation"),
            ("browser_nav_search_bing",     "Search Bing for a query.",               "search",         [("query", "STRING", True)], "navigation"),
            ("browser_nav_search_duckduckgo","Search DuckDuckGo for a query.",        "search",         [("query", "STRING", True)], "navigation"),
            ("browser_nav_search_youtube",  "Search YouTube for a query.",            "search",         [("query", "STRING", True)], "navigation"),
            ("browser_nav_open_new_window", "Open a new browser window.",             "new_window",     [], "navigation"),
            ("browser_nav_navigate_to_bookmark","Navigate to a bookmarked URL.",      "navigate",       [("url", "STRING", True)], "navigation"),
            ("browser_nav_wait_for_load",   "Wait for page to fully load.",           "wait_for_load",  [], "navigation"),
            ("browser_nav_wait_for_element","Wait for a specific element to appear.", "wait_for_element",[("selector", "STRING", True)], "navigation"),
            ("browser_nav_stop_loading",    "Stop the current page from loading.",    "stop_loading",   [], "navigation"),
            ("browser_nav_set_viewport",    "Set viewport size.",                     "set_viewport",   [("width", "INTEGER", True), ("height", "INTEGER", True)], "navigation"),
        ]
    },
    "browser_dom": {
        "module": "dom_gen",
        "tools": [
            ("browser_dom_double_click",      "Double click an element.",              "double_click",     [("selector", "STRING", True)], "dom"),
            ("browser_dom_right_click",       "Right-click (context menu) an element.","right_click",      [("selector", "STRING", True)], "dom"),
            ("browser_dom_hover_element",     "Hover over an element.",                "hover",            [("selector", "STRING", True)], "dom"),
            ("browser_dom_focus_element",     "Focus an element.",                     "focus",            [("selector", "STRING", True)], "dom"),
            ("browser_dom_check_element_exists","Check if an element exists on page.", "element_exists",   [("selector", "STRING", True)], "dom"),
            ("browser_dom_get_element_text",  "Get text content of a specific element.","get_element_text",[("selector", "STRING", True)], "dom"),
            ("browser_dom_get_element_attr",  "Get an attribute of an element.",       "get_attribute",    [("selector", "STRING", True), ("attribute", "STRING", True)], "dom"),
            ("browser_dom_count_elements",    "Count elements matching a selector.",   "count_elements",   [("selector", "STRING", True)], "dom"),
            ("browser_dom_get_element_value", "Get the value of a form element.",      "get_value",        [("selector", "STRING", True)], "dom"),
            ("browser_dom_is_visible",        "Check if an element is visible.",       "is_visible",       [("selector", "STRING", True)], "dom"),
            ("browser_dom_is_enabled",        "Check if an element is enabled.",       "is_enabled",       [("selector", "STRING", True)], "dom"),
            ("browser_dom_is_checked",        "Check if a checkbox/radio is checked.", "is_checked",       [("selector", "STRING", True)], "dom"),
            ("browser_dom_scroll_to_element", "Scroll until element is visible.",      "scroll_to",        [("selector", "STRING", True)], "dom"),
            ("browser_dom_drag_and_drop",     "Drag element to target.",               "drag_drop",        [("source", "STRING", True), ("target", "STRING", True)], "dom"),
            ("browser_dom_get_bounding_box",  "Get element position and dimensions.",  "bounding_box",     [("selector", "STRING", True)], "dom"),
        ]
    },
    "browser_input": {
        "module": "input_gen",
        "tools": [
            ("browser_input_clear_field",     "Clear the value of an input field.",    "clear_field",      [("selector", "STRING", True)], "input"),
            ("browser_input_check_checkbox",  "Check a checkbox.",                     "check",            [("selector", "STRING", True)], "input"),
            ("browser_input_uncheck_checkbox","Uncheck a checkbox.",                   "uncheck",          [("selector", "STRING", True)], "input"),
            ("browser_input_toggle_checkbox", "Toggle checkbox state.",                "toggle",           [("selector", "STRING", True)], "input"),
            ("browser_input_select_radio",    "Select a radio button.",                "select_radio",     [("selector", "STRING", True)], "input"),
            ("browser_input_set_date",        "Set a date input value.",               "set_date",         [("selector", "STRING", True), ("date", "STRING", True)], "input"),
            ("browser_input_set_range",       "Set a range/slider value.",             "set_range",        [("selector", "STRING", True), ("value", "STRING", True)], "input"),
            ("browser_input_submit_form",     "Submit a form.",                        "submit_form",      [("selector", "STRING", True)], "input"),
            ("browser_input_press_enter",     "Press Enter key.",                      "press_enter",      [], "input"),
            ("browser_input_press_tab",       "Press Tab key.",                        "press_tab",        [], "input"),
            ("browser_input_press_escape",    "Press Escape key.",                     "press_escape",     [], "input"),
            ("browser_input_keyboard_shortcut","Execute a keyboard shortcut.",         "shortcut",         [("keys", "STRING", True)], "input"),
            ("browser_input_type_slowly",     "Type text character by character.",     "type_slowly",      [("selector", "STRING", True), ("text", "STRING", True)], "input"),
            ("browser_input_paste_text",      "Paste text from clipboard into field.","paste_text",        [("selector", "STRING", True), ("text", "STRING", True)], "input"),
            ("browser_input_scroll_up",       "Scroll page up.",                       "scroll_up",        [], "input"),
            ("browser_input_scroll_down",     "Scroll page down.",                     "scroll_down",      [], "input"),
            ("browser_input_scroll_to_top",   "Scroll to top of page.",               "scroll_top",       [], "input"),
            ("browser_input_scroll_to_bottom","Scroll to bottom of page.",             "scroll_bottom",    [], "input"),
        ]
    },
    "browser_extract": {
        "module": "extract_gen",
        "tools": [
            ("browser_extract_get_meta",        "Get page meta tags.",                 "get_meta",         [], "extract"),
            ("browser_extract_get_images",      "Get all image URLs from page.",       "get_images",       [], "extract"),
            ("browser_extract_get_headings",    "Get all heading elements.",            "get_headings",     [], "extract"),
            ("browser_extract_get_tables",      "Extract table data as structured JSON.","get_tables",     [], "extract"),
            ("browser_extract_get_forms",       "Get all form elements and their inputs.","get_forms",     [], "extract"),
            ("browser_extract_get_cookies",     "Get all cookies for current domain.", "get_cookies",      [], "extract"),
            ("browser_extract_get_local_storage","Get local storage data.",            "get_local_storage",[], "extract"),
            ("browser_extract_get_session_storage","Get session storage data.",        "get_session_storage",[], "extract"),
            ("browser_extract_get_console_logs","Get browser console logs.",            "get_console",     [], "extract"),
            ("browser_extract_get_network_requests","Get network request log.",        "get_network",      [], "extract"),
            ("browser_extract_get_page_metrics","Get page performance metrics.",       "get_metrics",      [], "extract"),
            ("browser_extract_get_computed_style","Get computed CSS of element.",       "get_style",        [("selector", "STRING", True)], "extract"),
            ("browser_extract_pdf_page",        "Save current page as PDF.",           "pdf",              [("path", "STRING", False)], "extract"),
            ("browser_extract_get_selection",   "Get currently selected text.",         "get_selection",    [], "extract"),
            ("browser_extract_get_page_size",   "Get page dimensions.",                "get_page_size",    [], "extract"),
        ]
    },
    "browser_tab": {
        "module": "tab_gen",
        "tools": [
            ("browser_tab_pin_tab",          "Pin the current tab.",                   "pin_tab",          [], "tab"),
            ("browser_tab_unpin_tab",        "Unpin the current tab.",                 "unpin_tab",        [], "tab"),
            ("browser_tab_mute_tab",         "Mute audio on current tab.",             "mute_tab",         [], "tab"),
            ("browser_tab_unmute_tab",       "Unmute audio on current tab.",           "unmute_tab",       [], "tab"),
            ("browser_tab_get_active_tab",   "Get info about the active tab.",         "get_active",       [], "tab"),
            ("browser_tab_close_other_tabs", "Close all tabs except the current one.", "close_others",     [], "tab"),
            ("browser_tab_close_tabs_right", "Close all tabs to the right.",           "close_right",      [], "tab"),
            ("browser_tab_reopen_closed_tab","Reopen the last closed tab.",            "reopen_closed",    [], "tab"),
            ("browser_tab_move_tab",         "Move tab to a new position.",            "move_tab",         [("from_index", "INTEGER", True), ("to_index", "INTEGER", True)], "tab"),
            ("browser_tab_count_tabs",       "Count open tabs.",                       "count_tabs",       [], "tab"),
        ]
    },
    "browser_auth": {
        "module": "auth_gen",
        "tools": [
            ("browser_auth_logout",           "Click logout/sign-out on current page.","logout",          [], "auth"),
            ("browser_auth_fill_signup_form", "Fill a registration/signup form.",       "fill_signup",     [("email", "STRING", True), ("password", "STRING", True)], "auth"),
            ("browser_auth_detect_2fa",       "Detect if 2FA/MFA is requested.",       "detect_2fa",      [], "auth"),
            ("browser_auth_fill_otp",         "Fill a one-time password field.",        "fill_otp",        [("code", "STRING", True)], "auth"),
            ("browser_auth_accept_terms",     "Accept terms and conditions checkbox.", "accept_terms",     [], "auth"),
            ("browser_auth_save_session",     "Save current session/cookies to file.", "save_session",     [("path", "STRING", False)], "auth"),
            ("browser_auth_load_session",     "Load session/cookies from file.",        "load_session",    [("path", "STRING", True)], "auth"),
            ("browser_auth_clear_cookies",    "Clear all cookies.",                     "clear_cookies",   [], "auth"),
            ("browser_auth_clear_cache",      "Clear browser cache.",                  "clear_cache",      [], "auth"),
            ("browser_auth_set_user_agent",   "Set a custom user agent string.",       "set_ua",           [("user_agent", "STRING", True)], "auth"),
        ]
    },
    "browser_wait": {
        "module": "wait_gen",
        "tools": [
            ("browser_wait_for_text",         "Wait until text appears on page.",      "wait_text",        [("text", "STRING", True)], "wait"),
            ("browser_wait_for_url_change",   "Wait for URL to change.",              "wait_url",          [], "wait"),
            ("browser_wait_for_download",     "Wait for a download to complete.",     "wait_download",     [], "wait"),
            ("browser_wait_seconds",          "Wait for N seconds.",                  "wait_seconds",      [("seconds", "INTEGER", True)], "wait"),
            ("browser_wait_for_network_idle", "Wait for network to be idle.",         "wait_network",      [], "wait"),
            ("browser_wait_for_element_gone", "Wait for element to disappear.",       "wait_gone",         [("selector", "STRING", True)], "wait"),
            ("browser_wait_for_navigation",   "Wait for navigation to complete.",     "wait_navigation",   [], "wait"),
            ("browser_wait_for_popup",        "Wait for popup/dialog to appear.",     "wait_popup",        [], "wait"),
            ("browser_wait_for_frame",        "Wait for iframe to load.",             "wait_frame",        [("selector", "STRING", True)], "wait"),
            ("browser_wait_for_value",        "Wait for input to have specific value.","wait_value",       [("selector", "STRING", True), ("value", "STRING", True)], "wait"),
        ]
    },
    "browser_js": {
        "module": "js_gen",
        "tools": [
            ("browser_js_execute",            "Execute JavaScript code in page.",      "execute_js",       [("code", "STRING", True)], "js"),
            ("browser_js_evaluate",           "Evaluate JS and return result.",        "evaluate_js",      [("expression", "STRING", True)], "js"),
            ("browser_js_inject_css",         "Inject CSS styles into page.",          "inject_css",       [("css", "STRING", True)], "js"),
            ("browser_js_inject_script",      "Inject a script tag into page.",        "inject_script",    [("src", "STRING", True)], "js"),
            ("browser_js_remove_element",     "Remove element from DOM via JS.",       "remove_element",   [("selector", "STRING", True)], "js"),
            ("browser_js_set_attribute",      "Set element attribute via JS.",         "set_attr",         [("selector", "STRING", True), ("attr", "STRING", True), ("value", "STRING", True)], "js"),
            ("browser_js_add_class",          "Add CSS class to element.",             "add_class",        [("selector", "STRING", True), ("class_name", "STRING", True)], "js"),
            ("browser_js_remove_class",       "Remove CSS class from element.",        "remove_class",     [("selector", "STRING", True), ("class_name", "STRING", True)], "js"),
            ("browser_js_set_inner_html",     "Set innerHTML of element.",             "set_html",         [("selector", "STRING", True), ("html", "STRING", True)], "js"),
            ("browser_js_get_computed_property","Get computed CSS property.",          "get_css",          [("selector", "STRING", True), ("property", "STRING", True)], "js"),
        ]
    },
    "browser_debug": {
        "module": "debug_gen",
        "tools": [
            ("browser_debug_enable_devtools", "Enable developer tools overlay.",       "enable_devtools",  [], "debug"),
            ("browser_debug_take_dom_snapshot","Take a full DOM snapshot.",            "dom_snapshot",     [], "debug"),
            ("browser_debug_list_event_listeners","List event listeners on element.", "list_listeners",    [("selector", "STRING", True)], "debug"),
            ("browser_debug_emulate_mobile",  "Emulate a mobile device.",              "emulate_mobile",   [("device", "STRING", True)], "debug"),
            ("browser_debug_emulate_geolocation","Set geolocation.",                  "set_geo",           [("lat", "STRING", True), ("lon", "STRING", True)], "debug"),
            ("browser_debug_toggle_offline",  "Toggle offline mode.",                  "toggle_offline",   [], "debug"),
            ("browser_debug_throttle_network","Throttle network speed.",               "throttle",         [("profile", "STRING", True)], "debug"),
            ("browser_debug_clear_all_data",  "Clear all browsing data.",              "clear_all",        [], "debug"),
            ("browser_debug_get_accessibility_tree","Get accessibility tree.",        "a11y_tree",         [], "debug"),
            ("browser_debug_check_page_errors","Check page for JS errors.",           "check_errors",     [], "debug"),
        ]
    },
}


def _class_name(tool_name: str) -> str:
    """browser_nav_go_back -> BrowserNavGoBack"""
    return "".join(w.capitalize() for w in tool_name.split("_"))


def _build_params_schema(params: list) -> str:
    if not params:
        return '{"type": "OBJECT", "properties": {}, "required": []}'
    props = {}
    required = []
    for p in params:
        name, typ, req = p[0], p[1], p[2]
        props[name] = {"type": typ}
        if req:
            required.append(name)
    import json
    schema = {"type": "OBJECT", "properties": props, "required": required}
    return json.dumps(schema)


def _build_execute_body(tool_name: str, engine_method: str, params: list, domain: str) -> str:
    """Generate the execute body that delegates to BrowserEngine."""
    args = []
    for p in params:
        args.append(f'parameters["{p[0]}"]')
    call_args = ", ".join(args) if args else ""
    # All calls include browser and player kwargs
    if call_args:
        call_args += ", "
    call_args += 'browser=parameters.get("browser"), player=player'
    return f'return BrowserEngine().{engine_method}({call_args})'


def generate_domain(domain_key: str, spec: dict, output_dir: str):
    """Generate a single domain file with all its tools."""
    module_name = spec["module"]
    tools = spec["tools"]
    
    lines = [
        f'"""Auto-generated {domain_key} tools — DO NOT EDIT MANUALLY."""',
        "from actions.base import Action, ActionRegistry",
        "from typing import Any",
        "",
        "",
    ]
    
    class_names = []
    for tool_name, desc, engine_method, params, domain_tag in tools:
        cls = _class_name(tool_name)
        class_names.append(cls)
        schema_str = _build_params_schema(params)
        exec_body = _build_execute_body(tool_name, engine_method, params, domain_tag)
        
        lines.append(f"class {cls}(Action):")
        lines.append(f"    @property")
        lines.append(f'    def name(self) -> str: return "{tool_name}"')
        lines.append(f"    @property")
        lines.append(f'    def description(self) -> str: return "{desc}"')
        lines.append(f"    @property")
        lines.append(f"    def parameters_schema(self) -> dict:")
        lines.append(f"        return {schema_str}")
        lines.append(f"    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:")
        lines.append(f"        from runtime.browser.engine import BrowserEngine")
        lines.append(f"        {exec_body}")
        lines.append("")
        lines.append("")

    # Registration block
    reg_items = ", ".join(class_names)
    lines.append(f"for _cls in [{reg_items}]:")
    lines.append(f"    ActionRegistry.register(_cls)")
    lines.append("")

    # Write file
    domain_dir = os.path.join(output_dir, domain_key)
    os.makedirs(domain_dir, exist_ok=True)
    filepath = os.path.join(domain_dir, f"{module_name}.py")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    # Ensure __init__.py imports it
    init_path = os.path.join(domain_dir, "__init__.py")
    import_line = f"from actions.{domain_key}.{module_name} import *  # noqa: F401,F403\n"
    if os.path.exists(init_path):
        with open(init_path, "r") as f:
            existing = f.read()
        if import_line.strip() not in existing:
            with open(init_path, "a") as f:
                f.write(import_line)
    else:
        with open(init_path, "w") as f:
            f.write(f'"""{domain_key} domain — auto-generated tools."""\n')
            f.write(import_line)
    
    return len(tools), filepath


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    actions_dir = os.path.join(project_root, "actions")
    
    total = 0
    print("=" * 60)
    print("BUDDY MK67 — Real Browser Tool Generator")
    print("=" * 60)
    for domain_key, spec in DOMAINS.items():
        count, path = generate_domain(domain_key, spec, actions_dir)
        total += count
        print(f"  [{domain_key}] Generated {count} tools -> {os.path.basename(path)}")
    print("-" * 60)
    print(f"  TOTAL: {total} new tools generated across {len(DOMAINS)} domains")
    print("=" * 60)


if __name__ == "__main__":
    main()
