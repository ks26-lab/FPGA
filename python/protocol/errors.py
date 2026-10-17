"""
python.protocol.errors
======================
Standard error classes for runtime communication architecture.
"""


class FPGACommunicationError(Exception):
    """Base exception for all FPGA communication errors."""
    pass


class HardwareUnavailableError(FPGACommunicationError):
    """Raised when real hardware mode is requested but AXI peripheral access fails."""
    pass


class CommandParseError(FPGACommunicationError):
    """Raised when human CLI input cannot be parsed or validated."""
    pass


class InvalidRegisterError(FPGACommunicationError):
    """Raised when an illegal register offset or operation is attempted."""
    pass


class SceneNotSelectedError(FPGACommunicationError):
    """Raised when a scene-specific command is issued without selecting a scene."""
    pass
