from pathlib import Path


def test_ui_does_not_use_invalid_qmessagebox_enum_path():
    source = Path("ui.py").read_text(encoding="utf-8")

    assert "QMessageBox.MessageBox.StandardButton.No" not in source
