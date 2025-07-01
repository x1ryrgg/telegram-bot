import logging
from aiogram.exceptions import TelegramNetworkError
from typing import Callable, Dict, Any
from aiogram.types import Update


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/info.log", encoding="utf-8"),
    ]
)

logger = logging.getLogger(__name__)


async def log_middleware(
        handler: Callable[[Update, Dict[str, Any]], Any],
        event: Update,
        data: Dict[str, Any]
) -> Any:
    """Middleware для логирования обработчиков """
    handler_name = handler.__qualname__ if hasattr(handler, "__qualname__") else handler.__name__
    update_type = event.event_type if hasattr(event, "event_type") else type(event).__name__
    user_id = event.from_user.id if hasattr(event, "from_user") else "N/A"

    logger.info(
        f"Handler '{handler_name}' started for {update_type} (user: {user_id})"
    )

    try:
        result = await handler(event, data)
        logger.info(
            f"Handler '{handler_name}' finished successfully for user {user_id}"
        )
        return result

    except TelegramNetworkError as e:
        logger.warning(
            f"Network error in handler '{handler_name}': {str(e)}",
            exc_info=True
        )
        raise

    except KeyError as e:
        if str(e) == "'refresh'":
            logger.warning(
                f"Refresh token error in handler '{handler_name}'",
                exc_info=True
            )
            raise
        logger.error(
            f"KeyError in handler '{handler_name}': {str(e)}",
            exc_info=True
        )
        raise

    except Exception as e:
        logger.error(
            f"Unexpected error in handler '{handler_name}': {str(e)}",
            exc_info=True
        )
        raise