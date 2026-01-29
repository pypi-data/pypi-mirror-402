from envhealth import Checker, Reporter


def test_full_report():
    data = Checker().full_report()
    assert "system" in data
    assert "internet" in data
    assert "proxy" in data

    text = Reporter(data).pretty_text()
    assert "SYSTEM" in text
