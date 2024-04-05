from enum import Enum, auto


# Error severity
class Severity(Enum):
    OK = auto()
    WARNING = auto()
    ERROR = auto()
    EXCEPTION = auto()

    def __str__(self) -> str:
        return self.name.capitalize()


class Response:

    def __init__(self, severity: Severity, value: int | str | list | dict | None):
        """
        A response is an object that handles a severity code and value.
        If the severity is OK, the value will containg data (string, list or dictionary).
        Otherwise, the value will contain an error message.
        :param severity: error severity
        :param value: value (or message)
        """
        self._severity = severity
        self._value = value

    def __str__(self):
        return str(self._value)

    @property
    def is_ok(self) -> bool:
        """
        Is the response severity Ok?
        :return: True if it is, False otherwise
        """
        return self._severity == Severity.OK

    @property
    def is_bool(self) -> bool:
        """
        Is the value a boolean?
        :return: True if it is, False otherwise
        """
        return isinstance(self._value, bool)

    @property
    def is_int(self) -> bool:
        """
        Is the value an integer?
        :return: True if it is, False otherwise
        """
        return isinstance(self._value, int)

    @property
    def is_str(self) -> bool:
        """
        Is the value a string?
        :return: True if it is, False otherwise
        """
        return isinstance(self._value, str)

    @property
    def is_list(self) -> bool:
        """
        Is the value a list?
        :return: True if it is, False otherwise
        """
        return isinstance(self._value, list)

    @property
    def is_dict(self) -> bool:
        """
        Is the value a dictionary?
        :return: True if it is, False otherwise
        """
        return isinstance(self._value, dict)

    @property
    def value(self) -> int | str | list | dict:
        """
        Return the response value
        :return: response value
        """
        return 'None' if self._value is None else self._value

    @property
    def severity(self) -> Severity:
        """
        Return the response severity
        :return:
        """
        return self._severity


class ResponseGenerator:

    def __init__(self):
        pass

    @staticmethod
    def ok(value: int | str | list | dict) -> Response:
        """
        Generate an OK response
        :param value: response value
        :return: Response object
        """
        return Response(Severity.OK, value)

    @staticmethod
    def warning(message: str) -> Response:
        """
        Generate a WARNING response
        :param message: warning message
        :return: Response object
        """
        return Response(Severity.WARNING, f'Warning: {message}')

    @staticmethod
    def error(message: str) -> Response:
        """
        Generate an ERROR response
        :param message: error message
        :return: Response object
        """
        return Response(Severity.ERROR, f'Error: {message}')

    @staticmethod
    def exception(message: str, exception_value: Exception) -> Response:
        """
        Generate an EXCEPTION response
        :param message: error message
        :param exception_value: exception
        :return: Response object
        """
        return Response(Severity.EXCEPTION, f'Exception: {message} - {repr(exception_value)}')


if __name__ == '__main__':
    pass
