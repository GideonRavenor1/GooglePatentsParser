import logging


class Color:
    BOLD = "\033[1m"
    BLUE = "\033[94m"
    WHITE = "\033[97m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD_WHITE = BOLD + WHITE
    BOLD_BLUE = BOLD + BLUE
    BOLD_GREEN = BOLD + GREEN
    BOLD_YELLOW = BOLD + YELLOW
    BOLD_RED = BOLD + RED
    END = "\033[0m"


class ColorLogFormatter(logging.Formatter):
    FORMAT = "%(prefix)s[%(asctime)s] - [%(levelname)s] - %(message)s%(suffix)s"

    LOG_LEVEL_COLOR = {
        "DEBUG": {"prefix": "", "suffix": ""},
        "INFO": {"prefix": "", "suffix": ""},
        "WARNING": {"prefix": Color.BOLD_YELLOW, "suffix": Color.END},
        "ERROR": {"prefix": Color.BOLD_RED, "suffix": Color.END},
        "CRITICAL": {"prefix": Color.BOLD_RED, "suffix": Color.END},
    }

    def format(self, record):
        if not hasattr(record, "prefix"):
            record.prefix = self.LOG_LEVEL_COLOR.get(record.levelname.upper()).get(
                "prefix"
            )

        if not hasattr(record, "suffix"):
            record.suffix = self.LOG_LEVEL_COLOR.get(record.levelname.upper()).get(
                "suffix"
            )

        formatter = logging.Formatter(self.FORMAT)
        return formatter.format(record)


logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(ColorLogFormatter())
logger.addHandler(stream_handler)


class Message:
    @staticmethod
    def success_message(message: str) -> None:
        logger.info(message, extra={"prefix": Color.GREEN, "suffix": Color.END})

    @staticmethod
    def info_message(message: str) -> None:
        logger.info(message, extra={"prefix": Color.WHITE, "suffix": Color.END})

    @staticmethod
    def error_message(message: str) -> None:
        logger.error(message)

    @staticmethod
    def warning_message(message: str) -> None:
        logger.warning(message)
