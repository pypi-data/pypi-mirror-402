from logging import ERROR, Formatter, LogRecord, StreamHandler

from aiokafka_agent.infra.context.globals import g
from aiokafka_agent.infra.logger.container import logger_secure
from aiokafka_agent.infra.logger.sanitizer import SanitizingFilter


class PlatformCEFHandler(StreamHandler):
    """
    На каждый обычный лог дублируем platform-json через logger_secure.view/log_error.
    """

    def emit(self, record: LogRecord) -> None:
        try:
            msg = record.getMessage()
            if record.levelno >= ERROR:
                tb_text = (
                    self.formatter.formatException(record.exc_info)
                    if record.exc_info
                    else None
                )
                logger_secure.log_error(
                    name=record.levelname,
                    message=msg,
                    status_code=getattr(record, "status_code", 500),
                    traceback_str=tb_text,
                )
            else:
                logger_secure.view(name=record.levelname, value=msg)
        except Exception:
            self.handleError(record)

    @staticmethod
    def _current_correlation_id() -> str | None:
        """
        Берём correlation_id из journal_context (нормативно) или из g как fallback.
        """
        ctx = g.get("journal_context") or {}
        cid = ctx.get("correlation_id") or g.get("correlation_id")
        return cid if cid else None


platform_handler = PlatformCEFHandler()
platform_handler.formatter = Formatter(
    fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S",
)
platform_handler.addFilter(SanitizingFilter())
