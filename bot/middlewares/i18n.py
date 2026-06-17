from pathlib import Path
from aiogram import Dispatcher
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore

LOCALES_PATH = Path(__file__).parent.parent / "locales"


def setup_i18n(dp: Dispatcher) -> I18nMiddleware:
    i18n = I18nMiddleware(
        core=FluentRuntimeCore(path=str(LOCALES_PATH / "{locale}")),
        default_locale="uk",
    )
    i18n.setup(dp)
    return i18n
