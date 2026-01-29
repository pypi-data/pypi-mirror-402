from typing import Protocol
from datetime import datetime

__all__ = ["LoggerInterface", "ConsoleLogger"]


class LoggerInterface(Protocol):
    def debug(self, message: str) -> None: ...

    def info(self, message: str) -> None: ...

    def warning(self, message: str) -> None: ...

    def error(self, message: str) -> None: ...

    def critical(self, message: str) -> None: ...


class ConsoleLogger(LoggerInterface):
    def info(self, message: str) -> None:
        ConsoleLogger.__log("INFO", message)

    def error(self, message: str) -> None:
        ConsoleLogger.__log("ERROR", message)

    def critical(self, message: str) -> None:
        ConsoleLogger.__log("CRITICAL", message)

    def warning(self, message: str) -> None:
        ConsoleLogger.__log("WARNING", message)

    def debug(self, message: str) -> None:
        ConsoleLogger.__log("DEBUG", message)

    @staticmethod
    def __log(level: str, message: str) -> None:
        print(f" {datetime.now()} | {level} | {message}")
