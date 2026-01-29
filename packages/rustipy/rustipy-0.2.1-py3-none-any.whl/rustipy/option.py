import typing
from typing import Generic, Literal, TypeVar, final, Any, Never, TypeGuard, TYPE_CHECKING
from collections.abc import Callable
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    pass # type: ignore

from . import result

T = TypeVar('T') # Type of the value in Some
U = TypeVar('U') # Type of the result of map/and_then
E = TypeVar('E') # Type for error in ok_or/ok_or_else (placeholder)

# Abstract Base Class (Optional but helps define the interface)
class Option(Generic[T], ABC):
    """Abstract base class for Option types."""

    @staticmethod
    def from_optional(value: T | None) -> 'Option[T]':
        """Create an Option from a value that might be None."""
        if value is None:
            return NONE
        return Some(value)

    @abstractmethod
    def unwrap_or_none(self) -> T | None:
        """Return the contained value or None if Nothing."""
        pass

    @abstractmethod
    def is_some(self) -> bool:
        """Check if the option is a Some value."""
        pass

    def is_none(self) -> bool:
        """Check if the option is a Nothing value."""
        return not self.is_some()

    @abstractmethod
    def map(self, func: Callable[[T], U]) -> 'Option[U]':
        """Apply a function to the contained value (if any)."""
        pass

    @abstractmethod
    def and_then(self, func: Callable[[T], 'Option[U]']) -> 'Option[U]':
        """Apply a function returning an Option to the contained value (if any)."""
        pass

    @abstractmethod
    def unwrap(self) -> T:
        """Return the contained value, raise ValueError if Nothing."""
        pass

    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        """Return the contained value or a default."""
        pass

    # New methods based on Rust's Option
    @abstractmethod
    def expect(self, msg: str) -> T:
        """Return the contained value, raise ValueError with msg if Nothing."""
        pass

    @abstractmethod
    def unwrap_or_else(self, func: Callable[[], T]) -> T:
        """Return the contained value or compute it from a function."""
        pass

    @abstractmethod
    def map_or(self, default: U, func: Callable[[T], U]) -> U:
        """Apply a function to the contained value or return a default."""
        pass

    @abstractmethod
    def map_or_else(self, default_func: Callable[[], U], func: Callable[[T], U]) -> U:
        """Apply a function to the contained value or compute a default."""
        pass

    @abstractmethod
    def ok_or(self, err: E) -> 'result.Result[T, E]':
        """Transform Option[T] into Result[T, E], mapping Some(v) to Ok(v) and Nothing to Err(err)."""
        pass

    @abstractmethod
    def ok_or_else(self, err_func: Callable[[], E]) -> 'result.Result[T, E]':
        """Transform Option[T] into Result[T, E], mapping Some(v) to Ok(v) and Nothing to Err(err_func())."""
        pass

    @abstractmethod
    def and_(self, optb: 'Option[U]') -> 'Option[U]':
        """Return Nothing if the option is Nothing, otherwise return optb."""
        pass

    @abstractmethod
    def filter(self, predicate: Callable[[T], bool]) -> 'Option[T]':
        """Return Nothing if the option is Nothing or the predicate returns False."""
        pass

    @abstractmethod
    def or_(self, optb: 'Option[T]') -> 'Option[T]':
        """Return the option if it contains a value, otherwise return optb."""
        pass

    @abstractmethod
    def or_else(self, func: Callable[[], 'Option[T]']) -> 'Option[T]':
        """Return the option if it contains a value, otherwise call func and return its result."""
        pass

    @abstractmethod
    def xor(self, optb: 'Option[T]') -> 'Option[T]':
        """Return Some if exactly one of self, optb is Some, otherwise return Nothing."""
        pass

    @abstractmethod
    def contains(self, value: T) -> bool:
        """Return True if the option is Some and contains the given value."""
        pass

    @abstractmethod
    def zip(self, other: 'Option[U]') -> 'Option[tuple[T, U]]':
        """Zip self with another Option. If both are Some, return Some((s, o)). Otherwise Nothing."""
        pass

    @abstractmethod
    def inspect(self, func: Callable[[T], None]) -> 'Option[T]':
        """Call a function with the contained value if Some."""
        pass

    # Note: Python doesn't have Rust's ownership/borrowing.
    # `take` in Python might mean returning the value and leaving Nothing,
    # but that changes the state, which is less functional.
    # This implementation returns the value as an Option and leaves the original unchanged.
    # A mutable version could be added if needed.
    @abstractmethod
    def take(self) -> 'Option[T]':
        """Take the value out of the option, leaving Nothing in its place (conceptually).
           This implementation returns the value as a new Option, leaving the original unchanged."""
        pass

    @abstractmethod
    def is_some_and(self, predicate: Callable[[T], bool]) -> bool:
        """Return True if the option is Some and the value inside it matches a predicate."""
        pass

    def __bool__(self) -> bool:
        """Return True if Some, False if Nothing."""
        return self.is_some()


# Concrete class for Some value
@final # Indicates this class should not be subclassed further
class Some(Option[T]):
    """Represents an Option that contains a value."""
    __match_args__ = ('_value',) # For structural pattern matching
    __slots__ = ('_value',) # Optimize memory usage

    def __init__(self, value: T):
        # Basic check: Some should not contain None itself,
        # unless T is explicitly Optional[Something] which is usually an anti-pattern here.
        if value is None:
             # This check might be too strict depending on use case, but good default
             # raise ValueError("Cannot initialize Some with None. Use Nothing instead.")
             pass # Allow None if T allows it, but generally discouraged
        self._value: T = value

    def is_some(self) -> Literal[True]: # Type hint refinement
        return True

    def map(self, func: Callable[[T], U]) -> Option[U]:
        """Apply func to the value and wrap in Some."""
        # Creates a new Some instance with the result.
        return Some(func(self._value))

    def and_then(self, func: Callable[[T], Option[U]]) -> Option[U]:
        """Apply func (which returns Option) to the value."""
        # The function already returns an Option, so just return its result.
        return func(self._value)

    def unwrap(self) -> T:
        """Return the contained value."""
        return self._value

    def unwrap_or(self, default: T) -> T:
        """Return the contained value."""
        # Default value is ignored since we have a value.
        return self._value

    def unwrap_or_none(self) -> T | None:
        """Return the contained value."""
        return self._value

    # Implementations for new methods in Some
    def expect(self, msg: str) -> T:
        """Return the contained value."""
        return self._value

    def unwrap_or_else(self, func: Callable[[], T]) -> T:
        """Return the contained value."""
        return self._value

    def map_or(self, default: U, func: Callable[[T], U]) -> U:
        """Apply the function to the contained value."""
        return func(self._value)

    def map_or_else(self, default_func: Callable[[], U], func: Callable[[T], U]) -> U:
        """Apply the function to the contained value."""
        return func(self._value)

    def ok_or(self, err: E) -> 'result.Result[T, E]':
        """Return Ok containing the value."""
        return result.Ok(self._value)

    def ok_or_else(self, err_func: Callable[[], E]) -> 'result.Result[T, E]':
        """Return Ok containing the value."""
        return result.Ok(self._value)

    def and_(self, optb: Option[U]) -> Option[U]:
        """Return optb because self is Some."""
        return optb

    def filter(self, predicate: Callable[[T], bool]) -> Option[T]:
        """Return self if the predicate returns True, otherwise Nothing."""
        if predicate(self._value):
            return self
        else:
            return NONE

    def or_(self, optb: Option[T]) -> Option[T]:
        """Return self because it contains a value."""
        return self

    def or_else(self, func: Callable[[], Option[T]]) -> Option[T]:
        """Return self because it contains a value."""
        return self

    def xor(self, optb: Option[T]) -> Option[T]:
        """Return Nothing if optb is Some, otherwise return self."""
        if optb.is_some():
            return NONE
        else:
            return self

    def contains(self, value: T) -> bool:
        """Return True if the contained value equals the given value."""
        return self._value == value

    def zip(self, other: Option[U]) -> Option[tuple[T, U]]:
        """If other is Some, return Some containing a tuple of both values."""
        if isinstance(other, Some):
            return Some((self._value, other._value))
        else:
            return NONE

    def inspect(self, func: Callable[[T], None]) -> Option[T]:
        """Call the function with the contained value and return self."""
        func(self._value)
        return self

    def take(self) -> Option[T]:
        """Return self (conceptually taking the value)."""
        # In Python, returning a new Some instance containing the value.
        # A mutable version would modify self to Nothing.
        return Some(self._value)

    def is_some_and(self, predicate: Callable[[T], bool]) -> bool:
        """Return the result of the predicate applied to the contained value."""
        return predicate(self._value)

    def __eq__(self, other: object) -> bool:
        # Check equality based on contained value
        if not isinstance(other, Some):
            return NotImplemented
        return self._value == typing.cast(Some[Any], other)._value

    def __repr__(self) -> str:
        return f"Some({self._value!r})"

# Concrete class for Nothing value (Singleton pattern)
@final # Indicates this class should not be subclassed further
class Nothing(Option[Any]): # Generic type doesn't matter for Nothing
    """Represents an Option that contains no value (singleton)."""
    __match_args__ = () # No arguments for matching
    __slots__ = () # No instance variables needed

    # Singleton implementation
    _instance: 'Nothing | None'  = None
    def __new__(cls) -> 'Nothing':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def is_some(self) -> Literal[False]: # Type hint refinement
        return False

    def map(self, func: Callable[[Any], U]) -> Option[U]:
        """Return Nothing, as there is no value to map."""
        # Function is ignored. Return the singleton Nothing instance.
        return self

    def and_then(self, func: Callable[[Any], Option[U]]) -> Option[U]:
        """Return Nothing, as there is no value to process."""
        # Function is ignored. Return the singleton Nothing instance.
        return self

    def unwrap(self) -> Never: # Type hint refinement
        """Raise ValueError as there is no value."""
        raise ValueError("Cannot unwrap a Nothing value.")

    def unwrap_or(self, default: T) -> T:
        """Return the default value."""
        return default

    def unwrap_or_none(self) -> T | None:
        """Return None."""
        return None

    # Implementations for new methods in Nothing
    def expect(self, msg: str) -> Never:
        """Raise ValueError with the provided message."""
        raise ValueError(msg)

    def unwrap_or_else(self, func: Callable[[], T]) -> T:
        """Compute the value using the provided function."""
        return func()

    def map_or(self, default: U, func: Callable[[Any], U]) -> U:
        """Return the default value."""
        return default

    def map_or_else(self, default_func: Callable[[], U], func: Callable[[Any], U]) -> U:
        """Compute the default value using the provided function."""
        return default_func()

    def ok_or(self, err: E) -> 'result.Result[Any, E]': # T is Any for Nothing
        """Return Err containing the provided error."""
        return result.Err(err)

    def ok_or_else(self, err_func: Callable[[], E]) -> 'result.Result[Any, E]': # T is Any for Nothing
        """Return Err containing the error computed by err_func."""
        return result.Err(err_func())

    def and_(self, optb: Option[U]) -> Option[U]:
        """Return Nothing because self is Nothing."""
        return self # self is the NOTHING singleton

    def filter(self, predicate: Callable[[Any], bool]) -> Option[object]:
        """Return Nothing because self is Nothing."""
        return self

    def or_(self, optb: Option[T]) -> Option[T]:
        """Return optb because self is Nothing."""
        return optb

    def or_else(self, func: Callable[[], Option[T]]) -> Option[T]:
        """Call func and return its result because self is Nothing."""
        return func()

    def xor(self, optb: Option[T]) -> Option[T]:
        """Return optb because self is Nothing."""
        return optb

    def contains(self, value: Any) -> Literal[False]:
        """Return False because self is Nothing."""
        return False

    def zip(self, other: Option[U]) -> Option[tuple[Any, U]]:
        """Return Nothing because self is Nothing."""
        return self

    def inspect(self, func: Callable[[Any], None]) -> Option[object]:
        """Do nothing and return self (Nothing)."""
        return self

    def take(self) -> Option[object]:
        """Return Nothing because self is Nothing."""
        return self

    def is_some_and(self, predicate: Callable[[Any], bool]) -> Literal[False]:
        """Return False because self is Nothing."""
        return False

    def __eq__(self, other: object) -> bool:
        # Nothing is equal to itself or None
        return other is self or other is None

    def __repr__(self) -> str:
        return "NONE"

NONE: Nothing = Nothing()

# Helper function to check if a value is Some and bind its type
def is_some(val: Option[T]) -> TypeGuard[Some[T]]:
    """Type guard to check if an Option is Some."""
    return val.is_some()

# Helper function to check if a value is Nothing
def is_nothing(val: Option[Any]) -> TypeGuard[Nothing]:
    """Type guard to check if an Option is Nothing."""
    return val.is_none()
