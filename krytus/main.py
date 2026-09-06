import sys
import structlog

from krytus.bot import create_application
from krytus.config import config

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    logger_factory=structlog.PrintLoggerFactory(sys.stdout),
    cache_logger_on_first_use=True,
)


def main() -> None:
    application = create_application()
    
    print("Starting Krytus...")
    application.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()