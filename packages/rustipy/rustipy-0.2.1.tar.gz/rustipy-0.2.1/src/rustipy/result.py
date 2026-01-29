import copy
from collections.abc import Iterator, Callable
from typing import Generic, Never, TypeVar, final, TypeGuard, Literal, cast, Any, TYPE_CHECKING 
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .option import Option, Option, Some, NONE, is_some # type: ignore

from . import option

T = TypeVar('T') # Type of the success value
E = TypeVar('E') # Type of the error value
U = TypeVar('U') # Type for map result
F = TypeVar('F') # Type for map_err result
V = TypeVar('V') # Inner value type for flatten/transpose

# Abstract Base Class
class Result(Generic[T, E], ABC):
    """Abstract base class for Result types (Ok or Err)."""

    @abstractmethod
    def is_ok(self) -> bool:
        """Check if the result is Ok."""
        pass

    def is_err(self) -> bool:
        """Check if the result is Err."""
        return not self.is_ok()

    @abstractmethod
    def ok(self) -> 'option.Option[T]':
        """Convert Result[T, E] to Option[T], discarding the error if Err."""
        pass

    @abstractmethod
    def err(self) -> 'option.Option[E]':
        """Convert Result[T, E] to Option[E], discarding the success value if Ok."""
        pass

    @abstractmethod
    def map(self, op: Callable[[T], U]) -> 'Result[U, E]':
        """Map a Result[T, E] to Result[U, E] by applying a function to a contained Ok value."""
        pass

    @abstractmethod
    def map_err(self, op: Callable[[E], F]) -> 'Result[T, F]':
        """Map a Result[T, E] to Result[T, F] by applying a function to a contained Err value."""
        pass

    @abstractmethod
    def inspect(self, op: Callable[[T], None]) -> 'Result[T, E]':
        """Call a function with the contained Ok value for inspection."""
        pass

    @abstractmethod
    def inspect_err(self, op: Callable[[E], None]) -> 'Result[T, E]':
        """Call a function with the contained Err value for inspection."""
        pass

    @abstractmethod
    def expect(self, msg: str) -> T:
        """Return the contained Ok value, raise ValueError with msg if Err."""
        pass

    @abstractmethod
    def unwrap(self) -> T:
        """Return the contained Ok value, raise ValueError if Err."""
        pass

    @abstractmethod
    def expect_err(self, msg: str) -> E:
        """Return the contained Err value, raise ValueError with msg if Ok."""
        pass

    @abstractmethod
    def unwrap_err(self) -> E:
        """Return the contained Err value, raise ValueError if Ok."""
        pass

    @abstractmethod
    def and_then(self, op: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        """Call op if the result is Ok, otherwise return the Err value of self."""
        pass

    @abstractmethod
    def or_else(self, op: Callable[[E], 'Result[T, F]']) -> 'Result[T, F]':
        """Call op if the result is Err, otherwise return the Ok value of self."""
        pass

    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        """Return the contained Ok value or a provided default."""
        pass

    @abstractmethod
    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        """Return the contained Ok value or compute it from a function."""
        pass

    # --- New methods ---
    @abstractmethod
    def is_ok_and(self, predicate: Callable[[T], bool]) -> bool:
        """Return True if the result is Ok and the value inside it matches a predicate."""
        pass

    @abstractmethod
    def is_err_and(self, predicate: Callable[[E], bool]) -> bool:
        """Return True if the result is Err and the value inside it matches a predicate."""
        pass

    @abstractmethod
    def iter(self) -> Iterator[T]:
        """Return an iterator over the possibly contained Ok value."""
        pass

    @abstractmethod
    def map_or(self, default: U, func: Callable[[T], U]) -> U:
        """Apply a function to the contained Ok value, or return a default if Err."""
        pass

    @abstractmethod
    def map_or_else(self, default_func: Callable[[E], U], func: Callable[[T], U]) -> U:
        """Apply a function to the contained Ok value, or compute a default from the Err value."""
        pass

    @abstractmethod
    def or_(self, res: 'Result[T, F]') -> 'Result[T, F]':
        """Return the result if it is Ok, otherwise return res."""
        pass

    # Note: flatten requires T to be Result[V, E].
    @abstractmethod
    def flatten(self) -> 'Result[object, E]':
        """Convert Result[Result[V, E], E] to Result[V, E]."""
        pass

    # Note: transpose requires T to be Option[V].
    @abstractmethod
    def transpose(self) -> 'option.Option[Result[object, E]]':
        """Transpose a Result of an Option into an Option of a Result."""
        pass

    # Note: into_ok/into_err are conceptually consuming, but Python doesn't enforce this.
    # They raise errors if called on the wrong variant.
    @abstractmethod
    def into_ok(self) -> T:
        """Return the contained Ok value, consuming the self value. Raises if Err."""
        pass

    @abstractmethod
    def into_err(self) -> E:
        """Return the contained Err value, consuming the self value. Raises if Ok."""
        pass

    @abstractmethod
    def and_(self, res: 'Result[U, E]') -> 'Result[U, E]':
        """Return res if the result is Ok, otherwise return the Err value of self."""
        pass

    @abstractmethod
    def unwrap_or_default(self) -> T:
        """Return the contained Ok value or a default value for type T."""
        pass

    @abstractmethod
    def cloned(self) -> 'Result[T, E]':
        """Return a new Result with deep-copied inner values."""
        pass

    @abstractmethod
    def copied(self) -> 'Result[T, E]':
        """Return a new Result with shallow-copied inner values."""
        pass

    @abstractmethod
    def as_ref(self) -> 'Result[T, E]':
        """Convert &Result<T, E> to Result<&T, &E> (conceptually). Returns self."""
        pass

    @abstractmethod
    def as_mut(self) -> 'Result[T, E]':
        """Convert &mut Result<T, E> to Result<&mut T, &mut E> (conceptually). Returns self."""
        pass

    # --- New abstract method ---
    @abstractmethod
    def iter_mut(self) -> Iterator[T]:
        """Return a mutable iterator over the possibly contained Ok value."""
        pass

    @abstractmethod
    def map_or_default(self, func: Callable[[T], U]) -> U:
        """Apply a function to the contained Ok value, or return a default if Err."""
        pass

# Concrete class for Ok value
@final
class Ok(Result[T, E]):
    """Represents a successful Result containing a value."""
    __match_args__ = ('_value',)
    __slots__ = ('_value',)

    def __init__(self, value: T):
        self._value: T = value

    def is_ok(self) -> Literal[True]:
        return True

    def ok(self) -> 'option.Option[T]':
        return option.Some(self._value)

    def err(self) -> 'option.Option[E]':
        return option.NONE

    def map(self, op: Callable[[T], U]) -> Result[U, E]:
        return Ok(op(self._value))

    def map_err(self, op: Callable[[E], F]) -> Result[T, F]:
        # Type F doesn't matter here, error op is not called
        return Ok(self._value) # Or cast self? Ok(self._value) is safer

    def inspect(self, op: Callable[[T], None]) -> Result[T, E]:
        op(self._value)
        return self

    def inspect_err(self, op: Callable[[E], None]) -> Result[T, E]:
        # Error op is not called
        return self

    def expect(self, msg: str) -> T:
        return self._value

    def unwrap(self) -> T:
        return self._value

    def expect_err(self, msg: str) -> Never:
        raise ValueError(f"{msg}: {self._value!r}")

    def unwrap_err(self) -> Never:
        raise ValueError(f"Called unwrap_err on an Ok value: {self._value!r}")

    def and_then(self, op: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return op(self._value)

    def or_else(self, op: Callable[[E], Result[T, F]]) -> Result[T, F]:
        # Type F doesn't matter here, error op is not called
        return Ok(self._value) # Or cast self? Ok(self._value) is safer

    def unwrap_or(self, default: T) -> T:
        return self._value

    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        # Error op is not called
        return self._value

    # --- Implementations for new methods ---
    def is_ok_and(self, predicate: Callable[[T], bool]) -> bool:
        return predicate(self._value)

    def is_err_and(self, predicate: Callable[[E], bool]) -> Literal[False]:
        return False

    def iter(self) -> Iterator[T]:
        yield self._value

    def map_or(self, default: U, func: Callable[[T], U]) -> U:
        return func(self._value)

    def map_or_else(self, default_func: Callable[[E], U], func: Callable[[T], U]) -> U:
        return func(self._value)

    def or_(self, res: Result[T, F]) -> Result[T, F]:
        # Type F doesn't matter, return self (which is Ok)
        # Re-creating Ok is safer for type compatibility.
        return Ok(self._value)

    def flatten(self) -> Result[object, E]:
        # Assert that the inner value is a Result
        if isinstance(self._value, Result):
            # Cast self first, then access _value. Inner cast removed.
            inner_result: Result[object, E] = cast(Ok[Result[object, E], E], self)._value
            return inner_result
        else:
            # This case should ideally not happen if called correctly,
            # but raise an error for type safety.
            raise TypeError("Cannot flatten Ok containing non-Result value")

    def transpose(self) -> 'option.Option[Result[object, E]]':
        # Assert that the inner value is an Option
        if isinstance(self._value, option.Option):
            # Cast self first, then access _value. Inner cast removed.
            inner_option: option.Option[object] = cast(Ok[option.Option[object], E], self)._value
            # If self is Ok(Some(v)), return Some(Ok(v))
            # If self is Ok(Nothing), return Nothing
            if option.is_some(inner_option):
                # Use unwrap() which is guaranteed to succeed here
                return option.Some(Ok(inner_option.unwrap()))
            else: # inner_option is Nothing
                return option.NONE
        else:
            # This case should ideally not happen if called correctly,
            # but raise an error for type safety.
            raise TypeError("Cannot transpose Ok containing non-Option value")

    def into_ok(self) -> T:
        return self._value

    def into_err(self) -> Never:
        raise ValueError(f"Called into_err on an Ok value: {self._value!r}")

    def and_(self, res: Result[U, E]) -> Result[U, E]:
        # Self is Ok, so return the other result.
        return res

    def unwrap_or_default(self) -> T:
        # Self is Ok, return the contained value.
        return self._value

    def cloned(self) -> Result[T, E]:
        # Return a new Ok with a deep copy of the value.
        return Ok(copy.deepcopy(self._value))

    def copied(self) -> Result[T, E]:
        # Return a new Ok with a shallow copy of the value.
        return Ok(copy.copy(self._value))

    def as_ref(self) -> Result[T, E]:
        # Return self, conceptually borrowing.
        return self

    def as_mut(self) -> Result[T, E]:
        # Return self, conceptually borrowing mutably.
        return self

    # --- Implementation for new method ---
    def iter_mut(self) -> Iterator[T]:
        # Yield the contained value, allowing mutation if it's mutable.
        yield self._value

    def map_or_default(self, func: Callable[[T], U]) -> U:
        # Apply the function to the contained value.
        return func(self._value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Ok):
            return NotImplemented
        # Explicit cast to help type checker
        return self._value == cast(Ok[Any, Any], other)._value

    def __repr__(self) -> str:
        return f"Ok({self._value!r})"

# Concrete class for Err value
@final
class Err(Result[T, E]):
    """Represents a failed Result containing an error."""
    __match_args__ = ('_error',)
    __slots__ = ('_error',)

    def __init__(self, error: E):
        self._error: E = error

    def is_ok(self) -> Literal[False]:
        return False

    def ok(self) -> 'option.Option[T]':
        # Type T doesn't matter here
        return option.NONE

    def err(self) -> 'option.Option[E]':
        return option.Some(self._error)

    def map(self, op: Callable[[T], U]) -> Result[U, E]:
        # Type U doesn't matter here, success op is not called
        return Err(self._error) # Or cast self? Err(self._error) is safer

    def map_err(self, op: Callable[[E], F]) -> Result[T, F]:
        return Err(op(self._error))

    def inspect(self, op: Callable[[T], None]) -> Result[T, E]:
        # Success op is not called
        return self

    def inspect_err(self, op: Callable[[E], None]) -> Result[T, E]:
        op(self._error)
        return self

    def expect(self, msg: str) -> Never:
        raise ValueError(f"{msg}: {self._error!r}")

    def unwrap(self) -> Never:
        raise ValueError(f"Called unwrap on an Err value: {self._error!r}")

    def expect_err(self, msg: str) -> E:
        return self._error

    def unwrap_err(self) -> E:
        return self._error

    def and_then(self, op: Callable[[T], Result[U, E]]) -> Result[U, E]:
        # Type U doesn't matter here, success op is not called
        return Err(self._error) # Or cast self? Err(self._error) is safer

    def or_else(self, op: Callable[[E], Result[T, F]]) -> Result[T, F]:
        return op(self._error)

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        return op(self._error)

    # --- Implementations for new methods ---
    def is_ok_and(self, predicate: Callable[[T], bool]) -> Literal[False]:
        return False

    def is_err_and(self, predicate: Callable[[E], bool]) -> bool:
        return predicate(self._error)

    def iter(self) -> Iterator[T]:
        # Return an empty iterator
        return iter(()) # Or yield from ()

    def map_or(self, default: U, func: Callable[[T], U]) -> U:
        return default

    def map_or_else(self, default_func: Callable[[E], U], func: Callable[[T], U]) -> U:
        return default_func(self._error)

    def or_(self, res: Result[T, F]) -> Result[T, F]:
        # Return the alternative result 'res'
        return res

    def flatten(self) -> Result[object, E]:
        # If self is Err(e), return Err(e) regardless of inner type V
        # Recreating Err is safer for type compatibility.
        return Err(self._error)

    def transpose(self) -> 'option.Option[Result[object, E]]':
        # If self is Err(e), return Some(Err(e))
        # Recreating Err is safer for type compatibility.
        return option.Some(Err(self._error))

    def into_ok(self) -> Never:
        raise ValueError(f"Called into_ok on an Err value: {self._error!r}")

    def into_err(self) -> E:
        return self._error

    def and_(self, res: Result[U, E]) -> Result[U, E]:
        # Self is Err, so return self (cast to the correct type).
        # Recreating Err is safer. T type doesn't matter here.
        return Err(self._error)

    def unwrap_or_default(self) -> T:
        # Self is Err, return default value of T.
        # This implementation raises NotImplementedError because determining
        # the default value for a generic type T at runtime is unreliable
        # in Python without explicit information.
        # Users should handle Err explicitly or use unwrap_or/unwrap_or_else.
        raise NotImplementedError(
            "unwrap_or_default on Err requires knowing the type T or "
            "providing a default factory. Consider using unwrap_or or unwrap_or_else."
        )

    def cloned(self) -> Result[T, E]:
        # Return a new Err with a deep copy of the error.
        # T type doesn't matter here.
        return Err(copy.deepcopy(self._error))

    def copied(self) -> Result[T, E]:
        # Return a new Err with a shallow copy of the error.
        # T type doesn't matter here.
        return Err(copy.copy(self._error))

    def as_ref(self) -> Result[T, E]:
        # Return self, conceptually borrowing.
        return self

    def as_mut(self) -> Result[T, E]:
        # Return self, conceptually borrowing mutably.
        return self

    # --- Implementation for new method ---
    def iter_mut(self) -> Iterator[T]:
        # Return an empty iterator as there's no value to mutate.
        return iter(())

    def map_or_default(self, func: Callable[[T], U]) -> U:
        # Self is Err, return default value of U.
        # Similar to unwrap_or_default, determining the default for U
        # at runtime is unreliable without explicit info.
        raise NotImplementedError(
            "map_or_default on Err requires knowing the type U or "
            "providing a default factory. Consider using map_or or map_or_else."
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Err):
            return NotImplemented
        # Explicit cast to help type checker
        return self._error == cast(Err[Any, Any], other)._error

    def __repr__(self) -> str:
        return f"Err({self._error!r})"

# Helper type guards
def is_ok(val: Result[T, E]) -> TypeGuard[Ok[T, E]]:
    """Type guard to check if a Result is Ok."""
    return val.is_ok()

def is_err(val: Result[T, E]) -> TypeGuard[Err[T, E]]:
    """Type guard to check if a Result is Err."""
    return val.is_err()


