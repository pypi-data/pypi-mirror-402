import sys
from typing import Callable, Type

import typer

ErrorHandlingCallback = Callable[[Exception], int]


class ErrorHandlingTyper(typer.Typer):
    """
    Typer wrapper for adding global error handlers via @error_handler decorator
    """

    _error_handlers: dict[Type[Exception], ErrorHandlingCallback] = {}

    def error_handler(self, *exc: Type[Exception]):
        """
        Register an error handler for the given exception types
        """

        def decorator(
            f: ErrorHandlingCallback,
        ):
            for e in exc:
                if e in self._error_handlers:
                    raise KeyError(
                        "Only one error handler can be registered per Error type"
                    )

                self._error_handlers[e] = f

            return f

        return decorator

    def __call__(self, *args, **kwargs):
        try:
            super().__call__(*args, **kwargs)
        except Exception as e:
            try:
                callback = self._error_handlers[type(e)]
                exit_code = callback(e)
                raise typer.Exit(code=exit_code)

            except typer.Exit as e:
                sys.exit(e.exit_code)

            except KeyError:
                raise e
