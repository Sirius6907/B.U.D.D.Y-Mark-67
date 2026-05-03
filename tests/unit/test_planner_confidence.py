from brain.planning.confidence import score_plan_confidence


def test_native_verified_plan_scores_higher_than_ui_fallback_plan():
    native = score_plan_confidence(
        alias_match=0.95,
        preconditions_satisfied=True,
        verification_mode="verified_where_practical",
        native_first=True,
        telemetry_success_rate=0.98,
        ambiguity=0.05,
    )
    fallback = score_plan_confidence(
        alias_match=0.80,
        preconditions_satisfied=True,
        verification_mode="best_effort",
        native_first=False,
        telemetry_success_rate=0.70,
        ambiguity=0.25,
    )
    assert native > fallback
