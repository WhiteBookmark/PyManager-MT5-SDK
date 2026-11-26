"""
Validators module for MT5 Manager connection parameters.
Provides reusable validation and sanitization functions to prevent silent configuration breakages.
"""
from typing import Optional, Tuple


def sanitize_string(val: Optional[str]) -> str:
    """
    Strips leading/trailing whitespaces and trailing slashes.
    Safely handles None, non-string types, and empty values.
    """
    if val is None:
        return ""
    if not isinstance(val, str):
        val = str(val)
    return val.strip().rstrip("/\\")


def validate_server_endpoint(server: Optional[str], port: Optional[int | str]) -> Tuple[str, int]:
    """
    Validates and formats the server host and port.
    Strips protocol schemes (e.g., tcp://, ssl://) and extracts embedded ports.
    Ensures port is within valid TCP range (1 - 65535).
    """
    cleaned_server = sanitize_string(server)
    if not cleaned_server:
        raise ValueError("Server host/IP cannot be empty or null.")

    # Strip any protocol scheme if provided (e.g. tcp://0.tcp.ngrok.io:15432)
    for scheme in ("tcp://", "ssl://", "tls://", "http://", "https://"):
        if cleaned_server.lower().startswith(scheme):
            cleaned_server = cleaned_server[len(scheme):].strip()
            break

    # If server already contains port in format host:port
    if ":" in cleaned_server:
        parts = cleaned_server.rsplit(":", 1)
        cleaned_server = parts[0].strip()
        port = parts[1].strip()

    if port is None or str(port).strip() == "":
        cleaned_port = 443
    else:
        try:
            cleaned_port = int(str(port).strip())
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Port must be a valid integer, received: {port}") from exc

    if not (1 <= cleaned_port <= 65535):
        raise ValueError(f"Port {cleaned_port} is out of bounds (1 - 65535).")

    return cleaned_server, cleaned_port


def validate_login(login: Optional[int | str]) -> int:
    """
    Validates the account login ID. Must be a positive integer.
    """
    if login is None:
        raise ValueError("Login cannot be null.")
    
    cleaned_login_str = sanitize_string(str(login))
    if not cleaned_login_str:
        raise ValueError("Login cannot be empty.")
    
    try:
        numeric_login = int(cleaned_login_str)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Login must be an integer, received: {login}") from exc
    
    if numeric_login <= 0:
        raise ValueError(f"Login must be a positive integer (> 0), received: {numeric_login}")
    
    return numeric_login


def validate_password(password: Optional[str]) -> str:
    """
    Validates that password is a non-empty string.
    """
    if password is None:
        raise ValueError("Password cannot be null.")
    if not isinstance(password, str):
        password = str(password)
    cleaned_pw = password.strip()
    if not cleaned_pw:
        raise ValueError("Password cannot be empty.")
    return cleaned_pw


def validate_timeout(timeout: Optional[int | str], default: int = 15000) -> int:
    """
    Validates timeout in milliseconds. Must be a positive integer.
    """
    if timeout is None or str(timeout).strip() == "":
        return default
    try:
        val = int(str(timeout).strip())
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Timeout must be an integer, received: {timeout}") from exc
    if val <= 0:
        raise ValueError(f"Timeout must be a positive integer (> 0), received: {val}")
    return val


def validate_pump_mode(pump_mode: Optional[int | str], default: int = 0) -> int:
    """
    Validates pump mode flags integer (0 for no local pump, or bitmask of EnPumpModes).
    Safely handles None, strings, and invalid values.
    """
    if pump_mode is None or str(pump_mode).strip() == "":
        return default
    try:
        val = int(str(pump_mode).strip())
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Pump mode must be an integer, received: {pump_mode}") from exc
    if val < 0:
        raise ValueError(f"Pump mode cannot be negative, received: {val}")
    return val

