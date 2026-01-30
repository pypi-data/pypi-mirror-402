import pytest
from pyntcli.commands.util import check_severity, SeverityException


@pytest.fixture
def risk_data():
    return {
        "securityTests": {
            'DidNotRun': 0,
            'Duration': 0,
            'Findings': 5,
            'Passed': 27,
            'RisksCounter': {'Critical': 2, 'High': 0, 'Low': 3, 'Medium': 3},
            'Warnings': 1
        }
    }


def test_exception_on_medium_severity(risk_data):
    with pytest.raises(SeverityException):
        check_severity('MEDIUM', risk_data)


def test_exception_on_high_severity(risk_data):
    with pytest.raises(SeverityException):
        check_severity('HIGH', risk_data)


def test_exception_on_critical_severity(risk_data):
    with pytest.raises(SeverityException):
        check_severity('CRITICAL', risk_data)


def test_no_exception_on_higher_than_all_severity():
    data_with_low_risk_only = {
        "securityTests": {
            'DidNotRun': 0,
            'Duration': 0,
            'Findings': 5,
            'Passed': 27,
            'RisksCounter': {'Critical': 0, 'High': 0, 'Low': 3, 'Medium': 0},
            'Warnings': 1
        }
    }
    try:
        check_severity('HIGH', data_with_low_risk_only)
    except SeverityException:
        pytest.fail("SeverityException was raised unexpectedly!")


def test_invalid_severity_flag(risk_data):
    with pytest.raises(ValueError):
        check_severity('invalid', risk_data)


def test_exception_on_all_flag(risk_data):
    with pytest.raises(SeverityException):
        check_severity('ALL', risk_data)


def test_no_exception_on_all_flag_when_empty():
    data_with_no_risks = {
        "securityTests": {
            'DidNotRun': 0,
            'Duration': 0,
            'Findings': 5,
            'Passed': 27,
            'RisksCounter': {'Critical': 0, 'High': 0, 'Low': 0, 'Medium': 0},
            'Warnings': 1
        }
    }
    try:
        check_severity('ALL', data_with_no_risks)
    except SeverityException:
        pytest.fail("SeverityException was raised unexpectedly!")
