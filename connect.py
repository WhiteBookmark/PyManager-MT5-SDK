"""
MT5 Manager API Connection Script.
Validates environment parameters and attempts an encrypted session with the MT5 Server.
"""
import os
import sys
from dotenv import load_dotenv

import MT5Manager
from validators import (
    sanitize_string,
    validate_server_endpoint,
    validate_login,
    validate_password,
    validate_timeout,
    validate_pump_mode,
)


def main() -> None:
    # Load configuration from .env file
    load_dotenv()

    # Read and sanitize raw environment variables
    raw_server = os.getenv("MT5_SERVER")
    raw_port = os.getenv("MT5_PORT", "443")
    raw_login = os.getenv("MT5_LOGIN")
    raw_password = os.getenv("MT5_PASSWORD")
    raw_group = os.getenv("MT5_GROUP")
    raw_timeout = os.getenv("MT5_TIMEOUT_MS", "15000")
    raw_pump_mode = os.getenv("MT5_PUMP_MODE", "0")

    # Global input validation
    try:
        host, port = validate_server_endpoint(raw_server, raw_port)
        login = validate_login(raw_login)
        password = validate_password(raw_password)
        timeout = validate_timeout(raw_timeout)
        pump_mode = validate_pump_mode(raw_pump_mode)
        group = sanitize_string(raw_group)
    except ValueError as val_err:
        print(f"[Validation Error]: {val_err}", file=sys.stderr)
        sys.exit(1)

    server_endpoint = f"{host}:{port}"

    print("=" * 60, flush=True)
    print("MetaTrader 5 Manager API - Connection Test", flush=True)
    print("=" * 60, flush=True)
    print(f"Server Endpoint : {server_endpoint}", flush=True)
    print(f"Login ID        : {login}", flush=True)
    print(f"Target Group    : {group if group else 'N/A'}", flush=True)
    print(f"Timeout         : {timeout} ms", flush=True)
    print(f"Pump Mode       : {pump_mode}", flush=True)
    print("-" * 60, flush=True)
    print("Attempting connection to MT5 trade server...", flush=True)

    manager = None
    is_connected = False
    try:
        manager = MT5Manager.ManagerAPI()

        # In mt5manager (Python wrapper), Connect() returns a bool (True on success, False on failure).
        # Never compare `connected == EnMTAPIRetcode.MT_RET_OK` because in Python `False == 0` is True.
        connected = manager.Connect(server_endpoint, login, password, pump_mode, timeout)
        is_connected = connected is True

        if is_connected:
            print("[SUCCESS] Connected to MetaTrader 5 Trade Server successfully!")
            print(f"Server Time (UNIX) : {manager.TimeServer()}")
            try:
                # NetworkAddress returns the remote host IP/endpoint
                if hasattr(manager, "NetworkAddress"):
                    print(f"Network Address    : {manager.NetworkAddress()}")
                # NetworkServer returns the server descriptive name if available
                if hasattr(manager, "NetworkServer"):
                    server_name = manager.NetworkServer()
                    if server_name:
                        print(f"Network Server     : {server_name}")
            except Exception as e:
                print(f"Metrics note       : {e}")

            # If a group was specified, verify group configuration
            if group:
                try:
                    grp = None
                    # GroupRequest queries the server directly without requiring local pump
                    if hasattr(manager, "GroupRequest"):
                        grp = manager.GroupRequest(group)
                    # GroupGet reads from local memory pump (active when pump_mode includes GROUPS)
                    if not grp and hasattr(manager, "GroupGet"):
                        grp = manager.GroupGet(group)

                    if grp:
                        print(f"Group '{group}' verified successfully on server.")
                    else:
                        print(f"Group '{group}' query returned no data (verify group name and Manager rights).")
                except Exception as grp_err:
                    print(f"Group verification note: {grp_err}")
        else:
            err_num, err_enum, err_desc = MT5Manager.LastError()
            err_name = err_enum.name if hasattr(err_enum, "name") else str(err_enum)
            print("[FAILED] Connection unsuccessful.")
            print(f"Return Value: {connected}")
            print(f"Return Code : {int(err_enum) if isinstance(err_enum, int) else err_enum} ({err_name})")
            print(f"Error Code  : {err_num}")
            print(f"Error Detail: {err_desc}")
            print("-" * 60)

            # Provide actionable diagnostic hints based on LastError() return code name
            if err_name in (
                "MT_RET_AUTH_FAILED",
                "MT_RET_AUTH_ACCOUNT_INVALID",
                "MT_RET_AUTH_MANAGER_TYPE",
                "MT_RET_AUTH_INVALID",
                "MT_RET_AUTH_ACCOUNT_DISABLED",
            ):
                print("Diagnostic Note: Authorization failed or account is not a valid Manager login.")
                print("1. Check if MT5_LOGIN and MT5_PASSWORD are correct in .env.")
                print("2. Ensure MT5_LOGIN is a registered *Manager* account with Manager API permissions (regular trader demo accounts cannot connect to MT5Manager).")
                print("3. Check if your current IP address (or ngrok egress server IP) is whitelisted in MT5 Administrator under Manager settings.")
            elif err_name == "MT_RET_ERR_TIMEOUT":
                print("Diagnostic Note: Connection timed out.")
                print(f"1. Verify if the target endpoint '{server_endpoint}' is reachable.")
                print(f"2. If connecting via ngrok, ensure your manager has started the TCP tunnel pointing to the MT5 server (e.g., ngrok tcp 443).")
                print(f"3. Ensure firewalls or local security policies allow outbound TCP traffic to port {port}.")
                print(f"4. If network latency is high, consider increasing MT5_TIMEOUT_MS in .env (current: {timeout} ms).")
            sys.exit(1)

    except Exception as exc:
        print(f"[FATAL ERROR] An unexpected exception occurred: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if manager is not None and is_connected:
            try:
                print("Disconnecting session cleanly...")
                manager.Disconnect()
            except Exception:
                pass


if __name__ == "__main__":
    main()
