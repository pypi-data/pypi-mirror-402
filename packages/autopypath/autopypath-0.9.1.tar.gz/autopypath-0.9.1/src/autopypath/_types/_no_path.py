"""These are special internal types used by autopypath."""
# mypy: disable-error-code=override
# pyright: reportIncompatibleMethodOverride=false

from pathlib import Path
from typing import TYPE_CHECKING, final

from .._typing import Never, TypeAlias


class _NotSupported(NotImplementedError):
    """Exception raised when an unsupported operation is attempted on _NoPath.

    This exception indicates that the attempted operation is not supported.
    """


if TYPE_CHECKING:
    # During static analysis, make the "disabled" parameter un-callable:
    # nothing can ever satisfy a Never-typed argument.
    _UsagePreventedType: TypeAlias = Never
else:

    @final
    class _UsagePreventedType:
        """A type to indicate that a type is deliberately broken to prevent use of a method.

        This type is used as a type hint for method parameters in the :class:`_NoPath` class
        to indicate that these methods should not be used and will raise a :class:`_NotSupported`
        exception if called.

        It deliberately breaks the method signature to prevent accidental usage.

        This helps type checkers identify incorrect usage of these methods before runtime.
        """


_PathType: type[Path] = type(Path())
"""A type alias for the pathlib.Path type.

Generally, you cannot directly inherit from pathlib.Path because it is a C extension type.
This alias allows us to work around that limitation.
"""


_NOT_SUPPORTED_ERR: str = '_NoPath does not support this operation.'


@final
class _NoPath(_PathType):  # type: ignore[valid-type,misc]  # Magic to inherit from pathlib.Path
    """A sentinel Path type representing the absence of a path.

    This class is used to indicate that no valid path is available or applicable
    while still conforming to the expected Path type in type hints and function
    signatures without having to juggle ``None | Path`` types in those signatures.

    It inherits from :class:`~pathlib.Path` to maintain compatibility with path operations
    and type checking, but it signifies a 'no path' state and cannot be used to perform
    file system and other path-related operations.
    """

    def __hash__(self) -> int:
        """Hash for _NoPath objects always returns 0."""
        return 0

    def __repr__(self) -> str:
        """Representation of _NoPath."""
        return '<_NoPath>'

    def __str__(self) -> str:
        """String representation of _NoPath."""
        return '<_NoPath>'

    def __eq__(self, other: object) -> bool:
        """Equality comparison for _NoPath objects.

        :param object other: Another object to compare with.
        :return bool: True if both are _NoPath instances, False otherwise.
        """
        return isinstance(other, _NoPath)

    # methods overridden to prevent filesystem access and other path-related operations
    # all raise _NotSupported when called. This is maintained for type compatibility only.
    # and as a guardrail against misuse of this sentinel type for actual path operations.
    # The primary purpose of this class is to act as a sentinel value, not
    # to perform path operations and thus path operations are disabled.

    def __fspath__(self) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def __truediv__(self, key: object) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def __rtruediv__(self, key: object) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def exists(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def is_file(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def is_dir(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def open(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def read_text(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def read_bytes(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def write_text(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def write_bytes(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def mkdir(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def rmdir(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def unlink(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def rename(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def replace(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def touch(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def stat(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def chmod(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def lstat(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def owner(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def group(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def readlink(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def symlink_to(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def hardlink_to(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def absolute(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def resolve(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def samefile(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def expanduser(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def with_name(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def with_suffix(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def relative_to(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def is_absolute(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def is_reserved(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def joinpath(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def match(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    @property
    def parent(self) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    @property
    def parents(self) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    @property
    def parts(self) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    @property
    def drive(self) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    @property
    def root(self) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    @property
    def anchor(self) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    @property
    def name(self) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    @property
    def suffix(self) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    @property
    def suffixes(self) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    @property
    def stem(self) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def as_posix(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def as_uri(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def is_mount(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def is_symlink(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def is_block_device(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def is_char_device(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def is_fifo(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def is_socket(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def iterdir(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def glob(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    def rglob(self, _disabled: _UsagePreventedType) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    @classmethod
    def cwd(cls) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)

    @classmethod
    def home(cls) -> Never:
        raise _NotSupported(_NOT_SUPPORTED_ERR)
