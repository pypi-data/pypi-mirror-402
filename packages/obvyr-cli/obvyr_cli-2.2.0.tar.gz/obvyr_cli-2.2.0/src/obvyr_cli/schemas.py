from enum import Enum
from typing import List, Optional

import orjson
from pydantic import BaseModel, ConfigDict, Field, field_validator


class OutputMode(str, Enum):
    """Output execution modes for command wrapper."""

    AUTO = "auto"
    STREAM = "stream"
    BATCH = "batch"


class CommandExecutionConfig(BaseModel):
    """Configuration for command execution behaviour."""

    output_mode: OutputMode = Field(
        default=OutputMode.AUTO,
        description="Output mode: auto (CI detection), stream (force streaming), batch (force batch)",
    )
    preserve_ansi: bool = Field(
        default=True,
        description="Whether to preserve ANSI escape codes in output",
    )
    force_color: bool = Field(
        default=True,
        description="Whether to force color output via FORCE_COLOR environment variable",
    )


class RunCommandResponse(BaseModel):
    """
    Pydantic schema for storing command execution results.
    """

    command: List[str] = Field(
        ..., description="The executed command with its arguments."
    )
    output: Optional[str] = Field(
        None, description="Combined stdout and stderr output of the command."
    )
    stdout: Optional[str] = Field(
        None, description="Standard output of the command (deprecated)."
    )
    stderr: Optional[str] = Field(
        None, description="Standard error output of the command (deprecated)."
    )
    returncode: int = Field(..., description="Exit code of the command.")
    user: str = Field(
        ..., description="The system user who executed the command."
    )
    execution_time: float = Field(
        ..., description="Time taken to execute the command (in seconds)."
    )

    # Auto-clean data with field validators
    @field_validator("output", "stdout", "stderr")
    @classmethod
    def strip_whitespace(cls, value: str) -> Optional[str]:
        """Ensure output, stdout and stderr are stripped of excess whitespace or set to None if empty."""
        return value.strip() if value and value.strip() else None

    @field_validator("execution_time")
    @classmethod
    def round_execution_time(cls, value: float) -> float:
        """Round execution time to 4 decimal places for consistency."""
        return round(value, 4)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "command": ["ls", "-l"],
                "stdout": "file1.txt  file2.txt",
                "stderr": "",
                "returncode": 0,
                "user": "john_doe",
                "execution_time": 0.123,
            }
        }
    )

    def as_form_payload(self) -> dict:
        """Serialise the response into a dict suitable for multipart/form-data."""
        return {
            "command": orjson.dumps(self.command).decode("utf-8"),
            "output": self.output or "",
            "stdout": self.stdout or "",
            "stderr": self.stderr or "",
            "returncode": str(self.returncode),
            "user": self.user,
            "execution_time": str(self.execution_time),
        }
