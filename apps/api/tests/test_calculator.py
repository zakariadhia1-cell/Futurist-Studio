import pytest

from app.orchestrator.tools.calculator import safe_eval


def test_safe_eval_basic_arithmetic():
    assert safe_eval("1 + 2 * 3") == 7
    assert safe_eval("(1200 * 1.19)") == pytest.approx(1428.0)
    assert safe_eval("2 ** 10") == 1024
    assert safe_eval("-5 + 3") == -2


def test_safe_eval_rejects_function_calls():
    with pytest.raises(ValueError):
        safe_eval("__import__('os').system('echo hacked')")


def test_safe_eval_rejects_names():
    with pytest.raises(ValueError):
        safe_eval("os.system('echo hacked')")


def test_safe_eval_rejects_non_numeric_constants():
    with pytest.raises(ValueError):
        safe_eval("'a' + 'b'")
