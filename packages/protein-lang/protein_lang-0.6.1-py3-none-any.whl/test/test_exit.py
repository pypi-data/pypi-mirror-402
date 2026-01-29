import pytest

from protein import Interpreter, protein_comp
from protein.error import YAMLppExitError, YAMLppError




def test_exit_success():
    """
    `.exit` with explicit `.code` and `.message` must raise YAMLppExitError
    carrying the correct exit code and message.
    """
    src = """
    .exit:
      .code: 3
      .message: "Fatal error"
    """

    with pytest.raises(YAMLppExitError) as exc:
        protein_comp(src)

    assert exc.value.code == 3
    assert exc.value.message == "Fatal error"
    print("Exit message:", exc.value.message)
    print("Exit code:", exc.value.code)
    print("Exit str:", str(exc.value))


def test_exit_default_code():
    """
    `.exit` without `.code` must default to exit code 0 and still raise
    YAMLppExitError with the provided message.
    """
    src = """
    .exit:
      .message: "Done"
    """

    with pytest.raises(YAMLppExitError) as exc:
        protein_comp(src)
    assert exc.value.code == 0
    assert exc.value.message == "Done"
    print("Exit str:", str(exc.value))

def test_exit_code_type_error():
    """
    `.exit` must raise YAMLppError when `.code` is not an integer.
    """
    src = """
    .exit:
      .code: "not an int"
      .message: "Oops"
    """

    with pytest.raises(YAMLppError) as exc:
        protein_comp(src)

    assert "integer" in str(exc.value)


def test_exit_missing_message():
    """
    `.exit` must raise YAMLppError when `.message` is missing, because
    `.message` is a required field.
    """
    src = """
    .exit:
      .code: 1
    """

    with pytest.raises(YAMLppError) as exc:
        protein_comp(src)

    assert ".message" in str(exc.value)
