from loguru._logger import logger as logger

__all__ = ['get_logger', 'set_level', 'configure_logging', 'logger']

def get_logger(name: str) -> Logger: ...
def set_level(level: str, module: str | None = ...) -> None: ...
def configure_logging(level: str = ..., format_string: str | None = ...) -> None: ...

# Names in __all__ with no definition:
#   logger
