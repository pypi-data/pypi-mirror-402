"""Centralized configuration for prediction flags."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypedDict


@dataclass
class FlagConfig:
    """Configuration for a single prediction flag."""

    cli_name: str  # Name used in CLI (e.g., "--recycling-steps")
    api_name: str  # Name used in API (e.g., "recyclingSteps")
    type: type  # Type of the flag (bool, float, int, str)
    help_text: str  # Help text for CLI
    default: Any = None  # Default value
    transformer: Callable[[Any], Any] | None = None  # Optional value transformer


# Define all prediction flags in one place
PREDICTION_FLAGS = [
    FlagConfig(
        cli_name="recycling_steps",
        api_name="recycling_steps",
        type=int,
        help_text="The number of recycling steps to use for prediction. Default is 3.",
    ),
    FlagConfig(
        cli_name="diffusion_samples",
        api_name="diffusion_samples",
        type=int,
        help_text="The number of diffusion samples to use for prediction. Default is 1.",
    ),
    FlagConfig(
        cli_name="sampling_steps",
        api_name="sampling_steps",
        type=int,
        help_text="The number of sampling steps to use for prediction. Default is 200.",
    ),
    FlagConfig(
        cli_name="step_scale",
        api_name="step_scale",
        type=float,
        help_text="The step size is related to the temperature at which the diffusion process runs.",
    ),
]


class Flags(TypedDict):
    recycling_steps: int | None
    diffusion_samples: int | None
    sampling_steps: int | None
    step_scale: float | None

    @classmethod
    def _assert_annotations(cls):
        assert cls.__annotations__ == {flag_config.cli_name: (flag_config.type | None) for flag_config in PREDICTION_FLAGS}

    @classmethod
    def _gen_body(cls):
        for flag_config in PREDICTION_FLAGS:
            print(f"{flag_config.cli_name}: {flag_config.type.__qualname__} | None")


# Flags._assert_annotations()


def convert_to_api(cli_args: Flags) -> dict[str, Any]:
    """Convert CLI arguments to API flags dictionary.

    Args:
        cli_args: Dictionary of CLI arguments

    Returns:
        Dictionary of API flags with proper names and non-None values
    """
    flags = {}
    for flag_config in PREDICTION_FLAGS:
        cli_value = cli_args.get(flag_config.cli_name)
        if cli_value is not None:
            # Apply transformer if defined
            api_value = flag_config.transformer(cli_value) if flag_config.transformer else cli_value
            flags[flag_config.api_name] = api_value
    return flags


def add_click_options(command):
    """Decorator to add all prediction flag options to a Click command.

    Args:
        command: Click command to add options to

    Returns:
        Decorated command with all flag options
    """
    import click

    # Add options in reverse order so they appear in the correct order
    for flag_config in reversed(PREDICTION_FLAGS):
        option = click.option(
            f"--{flag_config.cli_name}",
            flag_config.cli_name,
            default=None,
            help=flag_config.help_text,
            is_flag=(flag_config.type is bool and flag_config.default is not True),
            type=flag_config.type,
        )

        command = option(command)

    return command
