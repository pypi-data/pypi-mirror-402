from tauro.cli.cli import UnifiedCLI, main

# Backwards compatibility: older code may import TauroCLI
TauroCLI = UnifiedCLI


def __getattr__(name):
    if name == "ContextInitializer":
        from tauro.cli.execution import ContextInitializer

        return ContextInitializer
    if name == "CLIPipelineExecutor":
        from tauro.cli.execution import PipelineExecutor

        return PipelineExecutor
    if name in ["TemplateCommand", "TemplateGenerator", "TemplateType"]:
        import tauro.cli.template as template

        return getattr(template, name)

    # For everything else, fall back to what's already in the module
    # or let typical attribute lookup handle it if we imported it above.
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Import core symbols that are safe
from tauro.cli.config import ConfigDiscovery, ConfigManager
from tauro.cli.core import (
    CLIConfig,
    ConfigCache,
    ConfigFormat,
    ConfigurationError,
    ExecutionError,
    ExitCode,
    LoggerManager,
    LogLevel,
    PathManager,
    SecurityError,
    SecurityValidator,
    TauroError,
    ValidationError,
)

__all__ = [
    "ConfigFormat",
    "LogLevel",
    "ExitCode",
    "TauroError",
    "ConfigurationError",
    "ValidationError",
    "ExecutionError",
    "SecurityError",
    "CLIConfig",
    "SecurityValidator",
    "LoggerManager",
    "PathManager",
    "ConfigCache",
    "ConfigDiscovery",
    "ConfigManager",
    "ContextInitializer",
    "CLIPipelineExecutor",
    "UnifiedCLI",
    "TauroCLI",  # legacy alias
    "main",
    "TemplateCommand",
    "TemplateGenerator",
    "TemplateType",
]
