# zeroArm_sdk/exceptions.py

class ArmNotFoundError(Exception):
    """No ZeroArm device found on the network."""
    pass


class ArmConnectionError(Exception):
    """Failed to connect, select SN, or establish communication."""
    pass


class ArmCommandError(Exception):
    """Command execution failed or invalid response."""
    pass