from app_bootstrap import bootstrap_application


def test_bootstrap_creates_report():
    report = bootstrap_application()
    assert report.log_path.endswith("buddy.log")
    assert isinstance(report.warnings, list)
