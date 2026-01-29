import sys
from types import TracebackType
from typing import Type, Optional
from .formatter import print_exception_with_vibes

def setup_exception_hook(mode: str) -> None:
    """
    Sets a custom exception hook to intercept crashes and display emotional support.
    :param mode: The mode of Delulify ('gentle', 'roast', 'chaotic').
    """
    
    def delulify_hook(
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_traceback: Optional[TracebackType]
    ) -> None:
        """
        Custom hook to intercept uncaught exceptions.
        """
        
        if issubclass(exc_type, (SystemExit, KeyboardInterrupt)):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        print_exception_with_vibes(exc_type, exc_value, exc_traceback, mode)

    sys.excepthook = delulify_hook