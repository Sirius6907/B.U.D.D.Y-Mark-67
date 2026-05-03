from registries.domain_index import DOMAIN_TARGET_COUNTS


def test_connectivity_domain_targets_match_the_approved_plan():
    assert DOMAIN_TARGET_COUNTS["network"] == 30
    assert DOMAIN_TARGET_COUNTS["wifi"] == 8
    assert DOMAIN_TARGET_COUNTS["bluetooth"] == 8
    assert DOMAIN_TARGET_COUNTS["usb"] == 6
    assert DOMAIN_TARGET_COUNTS["serial"] == 4
    assert DOMAIN_TARGET_COUNTS["shares"] == 4
