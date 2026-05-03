from registries.domain_index import DOMAIN_TARGET_COUNTS


def test_local_domain_targets_match_the_approved_plan():
    assert DOMAIN_TARGET_COUNTS["files"] == 45
    assert DOMAIN_TARGET_COUNTS["storage"] == 25
    assert DOMAIN_TARGET_COUNTS["process"] == 26
    assert DOMAIN_TARGET_COUNTS["apps"] == 10
    assert DOMAIN_TARGET_COUNTS["services"] == 10
    assert DOMAIN_TARGET_COUNTS["windows"] == 8
    assert DOMAIN_TARGET_COUNTS["input"] == 5
    assert DOMAIN_TARGET_COUNTS["clipboard"] == 3
    assert DOMAIN_TARGET_COUNTS["screen"] == 4
    assert DOMAIN_TARGET_COUNTS["printers"] == 4
