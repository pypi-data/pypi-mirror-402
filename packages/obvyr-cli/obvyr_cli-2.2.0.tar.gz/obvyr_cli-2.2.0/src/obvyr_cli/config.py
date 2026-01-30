"""
Configuration for Obvyr CLI.

The BaseSettings object will attempt to replace any properties
from environment variables, allowing environmental overrides.
"""

import logging
import secrets
from typing import Dict

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

DEFAULT_API_URL = "https://api.obvyr.com"


class ProfileSettings(BaseModel):
    """Configuration for an Obvyr CLI profile."""

    API_KEY: str
    API_URL: str = DEFAULT_API_URL
    ATTACHMENT_PATH: str | None = None
    ATTACHMENT_PATHS: list[str] = Field(default_factory=list)
    ATTACHMENT_MAX_AGE_SECONDS: int = 10
    TIMEOUT: float = 10.0
    VERIFY_SSL: bool = True
    TAGS: list[str] = Field(default_factory=list)

    @field_validator("TAGS", mode="before")
    @classmethod
    def parse_tags(cls, value: str | list[str]) -> list[str]:
        """Parse tags from comma-separated string or return list as-is."""
        if isinstance(value, str):
            return [tag.strip() for tag in value.split(",") if tag.strip()]
        return value or []

    @field_validator("ATTACHMENT_PATHS", mode="before")
    @classmethod
    def parse_attachment_paths(cls, value: str | list[str]) -> list[str]:
        """Parse attachment paths from comma-separated string or return list as-is."""
        if isinstance(value, str):
            return [path.strip() for path in value.split(",") if path.strip()]
        return value or []

    @model_validator(mode="after")
    def migrate_attachment_path(self) -> "ProfileSettings":
        """Migrate old ATTACHMENT_PATH to ATTACHMENT_PATHS."""
        # If new field has values, ignore old field
        if self.ATTACHMENT_PATHS:
            self.ATTACHMENT_PATH = None
            return self

        # If old field is set, migrate to new field
        if self.ATTACHMENT_PATH:
            logger.warning(
                "ATTACHMENT_PATH is deprecated. Use ATTACHMENT_PATHS instead."
            )
            self.ATTACHMENT_PATHS = [self.ATTACHMENT_PATH]
            self.ATTACHMENT_PATH = None

        return self


class Settings(BaseSettings):
    """Configuration and settings for the Obvyr CLI."""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="OBVYR_",
        env_nested_delimiter="__",
        env_ignore_empty=True,
        extra="ignore",
        populate_by_name=True,
    )

    SECRET_KEY: str = secrets.token_urlsafe(32)
    PROFILES: Dict[str, ProfileSettings] = Field(default_factory=dict)

    def get_profile(self, profile_name: str | None = None) -> ProfileSettings:
        """Return settings for the specified profile or default to DEFAULT profile."""
        if profile_name:
            active_profile = profile_name.strip().upper()
        else:
            active_profile = "DEFAULT"

        if active_profile not in self.PROFILES:
            raise ValueError(
                f"Profile '{active_profile}' not found in configuration."
            )
        profile = self.PROFILES[active_profile]

        return profile

    def list_profiles(self) -> list:
        """Return a list of available profiles."""
        return list(self.PROFILES.keys())

    def show_config(self, profile_name: str | None = None) -> dict:
        """Show active profile's settings (excluding API keys)."""
        active_profile = self.get_profile(profile_name)
        return {
            k.upper(): v
            for k, v in active_profile.model_dump().items()
            if "KEY" not in k.upper()
        }


def get_settings() -> Settings:
    """Return the current settings."""
    load_dotenv(".env", override=True)

    return Settings()
