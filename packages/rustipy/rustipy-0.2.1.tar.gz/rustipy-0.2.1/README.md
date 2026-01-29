# Rustipy
## Introduction
This package introduces Option and Result, which are basic functional monad types, to your project!

## Installation
```bash
pip install rustipy
```
## Usage

### Result example
> check the test file for more examples
```python
from rustipy.result import Result, Ok, Err

def square(x: int) -> int:
    return x * x

def ok_if_positive(x: int) -> Result[int, str]:
    if x > 0:
        return Ok(x)
    else:
        return Err("Not positive")

def err_to_default_ok(e: str) -> Result[int, str]:
    return Ok(DEFAULT_VALUE)

def len_str(s: str) -> int:
    return len(s)

OK_VALUE = 100
DEFAULT_VALUE = 0

def test_flatten():
    ok_ok: Result[Result[int, str], str] = Ok(Ok(OK_VALUE))
    ok_err: Result[Result[int, str], str] = Ok(Err(ERR_VALUE))
    err_outer: Result[Result[int, str], str] = Err(OTHER_ERR_VALUE)
    ok_not_result: Result[int, str] = Ok(123)

    assert ok_ok.flatten() == Ok(OK_VALUE)
    assert ok_err.flatten() == Err(ERR_VALUE)
    assert err_outer.flatten() == Err(OTHER_ERR_VALUE)

    with pytest.raises(TypeError):
        ok_not_result.flatten()

def test_chaining_err_path():
    res = (
        Ok(-5)
            .map(square)
            .and_then(ok_if_positive) # Ok(25)
            .and_then(err_if_negative) # Ok(25)
            .and_then(lambda x: Err("Force Err")) # Err("Force Err")
            .or_else(err_to_default_ok) # Ok(DEFAULT_VALUE)
            .unwrap()
    )
    assert res == DEFAULT_VALUE
```

### Option example
> check the test file for more examples
```python
from rustipy.option import Option, Some, NONE
from tests.test_result import OK_VALUE

def int_to_some_str(x: int) -> Option[str]:
    return Some(str(x))

def int_to_nothing_if_odd(x: int) -> Option[int]:
    return NONE if x % 2 != 0 else Some(x)

def int_to_some_str(x: int) -> Option[str]:
    return Some(str(x))

def int_to_nothing_if_odd(x: int) -> Option[int]:
    return NONE if x % 2 != 0 else Some(x)

SOME_VALUE = 123

def test_and_then():
    some_even: Option[int] = Some(10)
    some_odd: Option[int] = Some(5)
    nothing: Option[int] = NONE

    assert some_even.and_then(int_to_some_str) == Some("10")
    assert some_odd.and_then(int_to_some_str) == Some("5")
    assert nothing.and_then(int_to_some_str) == NONE

    assert some_even.and_then(int_to_nothing_if_odd) == Some(10)
    assert some_odd.and_then(int_to_nothing_if_odd) == NONE
    assert nothing.and_then(int_to_nothing_if_odd) == NONE

def test_inspect():
    inspected_val = None
    def inspector(x: int):
        nonlocal inspected_val
        inspected_val = x * 2

    some: Option[int] = Some(SOME_VALUE)
    nothing: Option[int] = NONE

    assert some.inspect(inspector) is some # Returns self
    assert inspected_val == SOME_VALUE * 2

    inspected_val = None # Reset
    assert nothing.inspect(inspector) is nothing # Returns self
    assert inspected_val is None

def test_type_guards():
    some: Option[int] = Some(OK_VALUE)
    nothing: Option[int] = NONE

    if is_some(some):
        assert some.unwrap() == OK_VALUE
    else:
        pytest.fail("is_some failed for Some value")

    if is_nothing(some):
        pytest.fail("is_nothing succeeded for Some value")

    if is_some(nothing):
        pytest.fail("is_some succeeded for Nothing value")

    if is_nothing(nothing):
        # Can't unwrap Nothing, just check identity
        assert nothing is NONE
    else:
        pytest.fail("is_nothing failed for Nothing value")
```

## Distribution Steps

1. Make some changes
2. Increment the version at `[project]` section in `[pyproject.toml]`
3. Commit the changes
4. Build the package
```
$ uv build
```
5. Tag the release
```
$ git tag -vX.X.X
$ git push origin vX.X.X
```

Done