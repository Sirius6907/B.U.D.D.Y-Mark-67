from actions import ActionRegistry

def get_domain_count(registry, domain_prefix):
    return sum(1 for d in registry.get_all_declarations() if d["name"].startswith(domain_prefix))

def test_browser_domain_targets_match_the_approved_plan():
    assert get_domain_count(ActionRegistry, "browser_nav") >= 30
    assert get_domain_count(ActionRegistry, "browser_dom") >= 40
    assert get_domain_count(ActionRegistry, "browser_auth") >= 20
    assert get_domain_count(ActionRegistry, "browser_tabs") >= 20
    assert get_domain_count(ActionRegistry, "browser_cookies") >= 20
    assert get_domain_count(ActionRegistry, "browser_history") >= 20
    assert get_domain_count(ActionRegistry, "browser_media") >= 20
    assert get_domain_count(ActionRegistry, "browser_downloads") >= 15
    assert get_domain_count(ActionRegistry, "browser_extensions") >= 15
