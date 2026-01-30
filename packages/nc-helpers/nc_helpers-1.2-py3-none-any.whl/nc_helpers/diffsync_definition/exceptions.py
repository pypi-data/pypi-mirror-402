class UnknownDeviceTypeException(Exception):
    """Exception raised when an unknown device type is encountered."""
    
    def __init__(self, device_type):
        self.device_type = device_type
        super().__init__(f"Unknown device type: {device_type}")