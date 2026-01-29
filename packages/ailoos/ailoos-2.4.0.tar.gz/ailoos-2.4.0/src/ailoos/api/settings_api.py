"""
AILOOS Settings API
Real endpoints for UI and notification settings using the SettingsService.
"""

import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..core.logging import get_logger
from ..settings.service import SettingsService, UserNotFoundError, ValidationError
from ..settings.models import create_default_settings

logger = get_logger(__name__)

DEFAULT_USERNAME = "default"
DEFAULT_EMAIL = "default@ailoos.local"


class NotificationSettingsPayload(BaseModel):
    mute_all: Optional[bool] = None
    responses_app: Optional[bool] = None
    responses_email: Optional[bool] = None
    tasks_app: Optional[bool] = None
    tasks_email: Optional[bool] = None
    projects_app: Optional[bool] = None
    projects_email: Optional[bool] = None
    recommendations_app: Optional[bool] = None
    recommendations_email: Optional[bool] = None


class UiSettingsPayload(BaseModel):
    appearance: Optional[str] = None
    accent_color: Optional[str] = None
    font_size: Optional[str] = None
    send_with_enter: Optional[bool] = None
    ui_language: Optional[str] = None
    spoken_language: Optional[str] = None
    voice: Optional[str] = None


class SettingsAPI:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.service = SettingsService(db_path=db_path)
        self.app = FastAPI(
            title="AILOOS Settings API",
            description="Settings endpoints for UI and notification preferences",
            version="1.0.0"
        )
        self._register_routes()

    def _get_or_create_user_id(self, username: str) -> int:
        try:
            user = self.service.get_user_by_username(username)
            return user["id"]
        except UserNotFoundError:
            user = self.service.create_user(username=username, email=DEFAULT_EMAIL, name="AILOOS Default")
            return user["id"]

    def _register_routes(self) -> None:
        @self.app.get("/health")
        async def settings_health() -> Dict[str, Any]:
            return {"status": "ok", "db_path": self.db_path}

        @self.app.get("/notifications")
        async def get_notification_settings(
            username: str = Query(DEFAULT_USERNAME)
        ) -> Dict[str, Any]:
            user_id = self._get_or_create_user_id(username)
            settings = self.service.get_user_settings(user_id)
            return settings.notifications.to_dict()

        @self.app.put("/notifications")
        async def update_notification_settings(
            payload: NotificationSettingsPayload,
            username: str = Query(DEFAULT_USERNAME)
        ) -> Dict[str, Any]:
            user_id = self._get_or_create_user_id(username)
            data = payload.model_dump(exclude_none=True)
            updated = self.service.update_category_settings(
                user_id,
                "notifications",
                data
            )
            return updated.notifications.to_dict()

        @self.app.post("/notifications/reset")
        async def reset_notification_settings(
            username: str = Query(DEFAULT_USERNAME)
        ) -> Dict[str, Any]:
            user_id = self._get_or_create_user_id(username)
            defaults = create_default_settings().notifications.to_dict()
            updated = self.service.update_category_settings(user_id, "notifications", defaults)
            return updated.notifications.to_dict()

        @self.app.get("/ui")
        async def get_ui_settings(
            username: str = Query(DEFAULT_USERNAME)
        ) -> Dict[str, Any]:
            user_id = self._get_or_create_user_id(username)
            settings = self.service.get_user_settings(user_id)
            return settings.general.to_dict()

        @self.app.put("/ui")
        async def update_ui_settings(
            payload: UiSettingsPayload,
            username: str = Query(DEFAULT_USERNAME)
        ) -> Dict[str, Any]:
            user_id = self._get_or_create_user_id(username)
            data = payload.model_dump(exclude_none=True)
            updated = self.service.update_category_settings(
                user_id,
                "general",
                data
            )
            return updated.general.to_dict()

        @self.app.post("/ui/reset")
        async def reset_ui_settings(
            username: str = Query(DEFAULT_USERNAME)
        ) -> Dict[str, Any]:
            user_id = self._get_or_create_user_id(username)
            defaults = create_default_settings().general.to_dict()
            updated = self.service.update_category_settings(user_id, "general", defaults)
            return updated.general.to_dict()

        @self.app.exception_handler(UserNotFoundError)
        async def handle_user_not_found(_, exc: UserNotFoundError):
            return JSONResponse(status_code=404, content={"detail": str(exc)})

        @self.app.exception_handler(ValidationError)
        async def handle_validation_error(_, exc: ValidationError):
            return JSONResponse(status_code=400, content={"detail": str(exc)})


settings_api = SettingsAPI(
    db_path=os.getenv("AILOOS_SETTINGS_DB", "settings.db")
)


def create_settings_app() -> FastAPI:
    return settings_api.app
