# MetaTrader 5 Manager API (`MT5Manager`) Reference Manual

Official Python reference and architecture guide for the **MetaTrader 5 Manager API** wrapper (`mt5manager` on PyPI).

---

## 1. Overview & Installation

MetaTrader 5 Manager API is MetaQuotes' native interface for brokerage operations, risk management, automated dealer actions, liquidity routing, and administrative tasks.

### Installation
```powershell
pip install mt5manager
```

> [!IMPORTANT]
> - **PyPI Package Name**: `mt5manager`
> - **Python Import Name**: `MT5Manager` (case-sensitive)
> - **Platform Support**: Windows x64 (AMD64)
> - **Underlying Core**: Includes native `MT5APIManager64.dll` and C-extension `_core.pyd`.

```python
import MT5Manager

# Verify installation
print(dir(MT5Manager))
```

---

## 2. Architecture & Components

The library exports 4 module-level helper functions, 2 main API orchestrators, 7 core system enumerations, and 95 data and configuration structures:

| Category | Component Count | Description |
| :--- | :--- | :--- |
| **Module Functions** | 4 | Path initialization, error inspection, and licensing validation. |
| **Core Controllers** | 2 | `ManagerAPI` (367 methods) and `AdminAPI` (476 methods). |
| **Data Models (Structs)** | 25 | Active runtime entities (`MTUser`, `MTAccount`, `MTOrder`, `MTPosition`, `MTDeal`, etc.). |
| **Config Models (Structs)** | 70 | Server/broker configs prefixed with `MTCon*` (`MTConGroup`, `MTConSymbol`, etc.). |
| **System Enums** | 7 | Return codes, feeder statuses, logging modes, and split rounding rules. |

---

## 3. Module-Level Functions

### `InitializeManagerAPIPath(module_path: str, work_path: str) -> bool`
Resolves and registers the path to `MT5APIManager64.dll`. Automatically invoked upon importing the package.

### `LastError() -> tuple[int, EnMTAPIRetcode, str]`
Returns the status of the most recent operation as a tuple:
1. `code` (int): Internal system error code.
2. `retcode` ([EnMTAPIRetcode](#7-system-enumerations)): API return enumeration constant.
3. `message` (str): Human-readable error description.

### `LicenseCheckManager(manager: ManagerAPI, name: str) -> bool`
Validates licensing entitlements for a `ManagerAPI` session against the trade server.

### `LicenseCheckAdmin(admin: AdminAPI, name: str) -> bool`
Validates licensing entitlements for an `AdminAPI` session against the trade server.

---

## 4. `ManagerAPI` Reference

The `ManagerAPI` class is the primary interface for dealing operations, client management, position monitoring, and market data queries.

### 4.1 Connection & Server Lifecycle
- `Connect(server: str, login: int, password: str, pump_mode: int, timeout: int) -> bool`: Establishes an encrypted session to the MT5 trade server. Returns `True` on success or `False` on failure (always check `if connected is True:` — never compare with `MT_RET_OK` (`0`), because in Python `False == 0` is `True`). Call `MT5Manager.LastError()` on failure.
  - `pump_mode`: `0` connects without a background memory pump (recommended for direct RPC queries and scripts). Pass bitmask flags from `manager.EnPumpModes` (such as `PUMP_MODE_GROUPS`, `PUMP_MODE_USERS`, `PUMP_MODE_ORDERS`, `PUMP_MODE_POSITIONS`) to maintain local in-memory caches and receive real-time sink callbacks.
- `Disconnect()`: Gracefully terminates the session.
- `TimeServer() -> int`: Returns current UNIX server time.
- `TimeGet() -> int`: Returns synchronized local time.
- `TimeSubscribe(sink)` / `TimeUnsubscribe(sink)`: Subscribes to time heartbeat events.
- `NetworkAddress() -> str`: Remote host IP or domain.
- `NetworkServer() -> str`: Server descriptive name.
- `NetworkBytesRead() -> int` / `NetworkBytesSent() -> int`: Network I/O metrics.

### 4.2 User & Account Management
- `UserAdd(user: MTUser, master: str, investor: str) -> EnMTAPIRetcode`: Creates a new trading account with credentials.
- `UserUpdate(user: MTUser) -> EnMTAPIRetcode`: Persists modifications to an account.
- `UserDelete(login: int) -> EnMTAPIRetcode`: Removes a trading account.
- `UserGet(login: int) -> MTUser`: Fast read from the client memory pump.
- `UserRequest(login: int) -> MTUser`: Direct query to the central trade server.
- `UserGetByGroup(group: str) -> list[MTUser]`: Fetches accounts matching a group pattern (e.g. `real\\*`).
- `UserGetByLogins(logins_list: list[int]) -> list[MTUser]`: Batch retrieval of accounts.
- `UserPasswordCheck(type: int, login: int, password: str) -> bool`: Authenticates master, investor, or API password.
- `UserPasswordChange(type: int, login: int, password: str) -> bool`: Updates account passwords.
- `UserBalanceCheck(login: int, fix_flag: int) -> tuple[float, float]`: Audits and reconciles balance and credit integrity.
- `UserAccountGet(login: int) -> MTAccount`: Fetches real-time equity, balance, and margin metrics.

### 4.3 Order Management
- `OrderAdd(order: MTOrder) -> EnMTAPIRetcode`: Creates a new pending or market order.
- `OrderUpdate(order: MTOrder) -> EnMTAPIRetcode`: Adjusts price, volume, stop-loss, or take-profit.
- `OrderCancel(ticket: int) -> EnMTAPIRetcode`: Cancels an active pending order.
- `OrderDelete(ticket: int) -> EnMTAPIRetcode`: Purges an order from the database.
- `OrderGet(ticket: int) -> MTOrder`: Reads order record from memory pump.
- `OrderGetOpen() -> list[MTOrder]`: Retrieves all current active/pending orders across the server.
- `OrderRequest(ticket: int) -> MTOrder`: Queries order directly from server storage.
- `OrderRequestByLogins(logins: list[int]) -> list[MTOrder]`: Fetches pending orders for selected logins.

### 4.4 Position Management
- `PositionGet(login: int, symbol: str) -> MTPosition`: Queries open position for a given account and instrument.
- `PositionGetByTickets(tickets: list[int]) -> list[MTPosition]`: Fetches positions by ticket numbers.
- `PositionUpdate(position: MTPosition) -> EnMTAPIRetcode`: Modifies position properties (e.g., stop loss, take profit).
- `PositionDelete(ticket: int) -> EnMTAPIRetcode`: Forcibly closes/removes a position.
- `PositionSplit(ticket: int, volume_split: int) -> EnMTAPIRetcode`: Partitions a position into smaller lots.
- `PositionCheck(login: int) -> EnMTAPIRetcode`: Verifies position consistency against client balance.

### 4.5 Deals, History & Dealer Operations
- `DealAdd(deal: MTDeal) -> EnMTAPIRetcode`: Registers an executed trade or balance modification.
- `DealPerform(deal: MTDeal) -> EnMTAPIRetcode`: Direct execution of a deal.
- `DealRequest(ticket: int) -> MTDeal`: Retrieves trade record by deal ticket.
- `HistoryRequest(login: int, from_time: int, to_time: int) -> tuple[list[MTOrder], list[MTDeal]]`: Fetches closed orders and deals for a date range.
- `DealerBalance(login: int, amount: float, type: int, comment: str, check_margin: bool) -> int`: Deposits or withdraws balance/credit, returning the deal ticket.
- `DealerLock(request_id: int) -> EnMTAPIRetcode`: Locks a client dealing request for processing.
- `DealerAnswer(answer: MTConfirm) -> EnMTAPIRetcode`: Approves, requotes, or rejects a client request.

### 4.6 Market Data, Ticks & Books
- `TickLast(symbol: str) -> MTTick`: Retrieves the latest bid/ask tick for an instrument.
- `TickStat(symbol: str) -> MTTickStat`: Fetches session high, low, volume, and spread stats.
- `TickAdd(tick: MTTick) -> EnMTAPIRetcode`: Injects custom price ticks into the trading engine.
- `TickHistoryRequest(symbol: str, from_date: int, to_date: int) -> list[MTTick]`: Fetches historical tick series.
- `BookGet(symbol: str) -> MTBook`: Gets current Market Depth (Level II order book).
- `BookSubscribe(symbol: str, sink)` / `BookUnsubscribe(symbol: str, sink)`: Real-time order book streaming.
- `ChartRequest(symbol: str, from_time: int, to_time: int) -> list[MTChartBar]`: Requests OHLCV candlestick bars.

### 4.7 Symbol & Group Configuration
- `SymbolGet(name: str) -> MTConSymbol`: Queries symbol configuration (spread, digits, contract sizes, swap rules) from local pump.
- `SymbolGetArray() -> list[MTConSymbol]`: Retrieves all available server symbols from local pump.
- `SymbolUpdate(symbol: MTConSymbol) -> EnMTAPIRetcode`: Modifies symbol specifications.
- `GroupGet(name: str) -> MTConGroup`: Reads group parameters from the local memory pump (requires `pump_mode` with `PUMP_MODE_GROUPS`).
- `GroupRequest(name: str) -> MTConGroup`: Requests group configuration directly from the server (operates even when local memory pumping is disabled, `pump_mode=0`).
- `GroupUpdate(group: MTConGroup) -> EnMTAPIRetcode`: Modifies group properties.
- `HolidayGetArray() -> list[MTConHoliday]`: Retrieves trading calendar holidays.

### 4.8 Subscriptions & Sinks (Event Streaming)
- `Subscribe(sink)` / `Unsubscribe(sink)`: Global pump events.
- `UserSubscribe(sink)` / `UserUnsubscribe(sink)`: Account creation/modification stream.
- `OrderSubscribe(sink)` / `OrderUnsubscribe(sink)`: Order placement and execution stream.
- `PositionSubscribe(sink)` / `PositionUnsubscribe(sink)`: Position changes stream.
- `DealSubscribe(sink)` / `DealUnsubscribe(sink)`: Trade executions stream.
- `TickSubscribe(sink)` / `TickUnsubscribe(sink)`: Live tick feed stream.

---

## 5. `AdminAPI` Reference

The `AdminAPI` extends server access to infrastructural controls:

### Additional Administrative Capabilities
- **Backups & Disaster Recovery**:
  - `UserBackupList()`, `UserBackupRequest()`, `UserBackupRestore()`
  - `OrderBackupRestore()`, `PositionBackupRestore()`, `DealBackupRestore()`
- **Server Infrastructure & Clustering**:
  - `ServerActivate()`, `ServerLiveUpdate()`
  - `NetServerRestart()`, `NetServerUpdate()`, `NetServerTotal()`
  - `ClusterState()`
- **Gateways & Feeders**:
  - `GatewayGet()`, `GatewayUpdate()`, `GatewayRestart()`, `GatewaySubscribe()`
  - `FeederGet()`, `FeederUpdate()`, `FeederRestart()`
- **Plugins & Automation**:
  - `PluginGet()`, `PluginUpdate()`, `PluginModuleGet()`
  - `AutomationGet()`, `AutomationUpdate()`, `AutomationDelete()`
- **Ult Liquidity Bridge**:
  - `UltLiquidityGet()`, `UltLiquidityUpdate()`
  - `UltProviderGet()`, `UltRouteGet()`, `UltSymbolGet()`
- **VPS Administration**:
  - `VPSGet()`, `VPSSet()`, `VPSSubscribe()`

---

## 6. Key Data Structures (Models)

### Operational Entities

#### `MTUser`
Represents client master account data.
- **Fields**: `Login`, `Group`, `Name`, `FirstName`, `LastName`, `EMail`, `Company`, `City`, `State`, `Country`, `Phone`, `Leverage`, `Balance`, `Credit`, `InterestRate`, `CommissionDaily`, `CommissionMonthly`, `Rights`, `Status`, `Registration`, `LastAccess`, `LastIP`.

#### `MTAccount`
Represents real-time calculated financial state.
- **Fields**: `Login`, `Currency`, `Balance`, `Credit`, `Margin`, `MarginFree`, `MarginLevel`, `MarginLeverage`, `Profit`, `Equity`, `Floating`.

#### `MTOrder`
Represents orders placed in the system.
- **Fields**: `Order`, `ExternalID`, `Login`, `Symbol`, `Type`, `TypeFill`, `TypeTime`, `PriceOrder`, `PriceTrigger`, `PriceCurrent`, `PriceSL`, `PriceTP`, `VolumeInitial`, `VolumeCurrent`, `TimeSetup`, `TimeExpiration`, `TimeDone`, `State`, `Comment`.

#### `MTPosition`
Represents open market commitments.
- **Fields**: `Position`, `ExternalID`, `Login`, `Symbol`, `Action`, `Volume`, `PriceOpen`, `PriceCurrent`, `PriceSL`, `PriceTP`, `TimeCreate`, `TimeUpdate`, `Profit`, `Storage` (swap), `RateProfit`, `RateMargin`, `Comment`.

#### `MTDeal`
Represents settled trades or financial transactions.
- **Fields**: `Deal`, `Order`, `ExternalID`, `Login`, `Symbol`, `Action`, `Entry`, `Volume`, `Price`, `Profit`, `Storage`, `Commission`, `Fee`, `RateProfit`, `RateMargin`, `Time`, `Comment`.

#### `MTTick` & `MTTickStat`
Represents market pricing snapshots.
- `MTTick`: `Symbol`, `Bank`, `Time`, `TimeMSC`, `Bid`, `Ask`, `Last`, `Volume`, `VolumeReal`.
- `MTTickStat`: `Symbol`, `BidHigh`, `BidLow`, `AskHigh`, `AskLow`, `PriceOpen`, `PriceClose`, `PriceHigh`, `PriceLow`, `Volume`, `TradeDeals`.

#### `MTBook` & `MTBookItem`
Represents Level 2 Depth of Market.
- `MTBook`: `Symbol`, `Time`, `Items`.
- `MTBookItem`: `Type` (`BUY` or `SELL`), `Price`, `Volume`.

---

## 7. System Enumerations

### `EnMTAPIRetcode`
Return codes for API commands:
- `MT_RET_OK` (0): Success.
- `MT_RET_ERROR` (1): Generic error.
- `MT_RET_ERR_PARAMS` (2): Invalid parameter passed.
- `MT_RET_ERR_DATA` (3): Invalid or corrupted data.
- `MT_RET_AUTH_FAILED` (4): Authentication failed.
- `MT_RET_ERR_NOTFOUND` (5): Target entity not found.
- `MT_RET_ERR_PERMISSIONS` (6): Insufficient privileges.
- `MT_RET_ERR_TIMEOUT` (7): Command timed out.
- `MT_RET_REQUEST_DONE` (10009): Request processed.
- `MT_RET_TRADE_COMMON_ERROR` (10010): Common trade execution error.
- `MT_RET_TRADE_OFFQUOTES` (10014): No prices available.
- `MT_RET_TRADE_NO_MONEY` (10019): Margin check failed.

---

## 8. Practical Code Examples

### Example 1: Connecting and Reading User Details
```python
import MT5Manager

manager = MT5Manager.ManagerAPI()

# Connect to MT5 Server
SERVER_ADDRESS = "127.0.0.1:443"
MANAGER_LOGIN = 1000
MANAGER_PASSWORD = "ManagerSecurePassword"
TIMEOUT_MS = 30000
PUMP_MODE = 0  # 0 for lightweight direct queries, or manager.EnPumpModes flags

res = manager.Connect(SERVER_ADDRESS, MANAGER_LOGIN, MANAGER_PASSWORD, PUMP_MODE, TIMEOUT_MS)
if res is not True:
    err_code, ret, desc = MT5Manager.LastError()
    print(f"Connection failed: {desc} (code {err_code}, ret {ret})")
    exit(1)

print("Successfully connected to MetaTrader 5 trade server.")

# Fetch user details
target_login = 10001
user = manager.UserRequest(target_login)  # Direct request to server
if user:
    print(f"Login: {user.Login}")
    print(f"Name: {user.Name}")
    print(f"Group: {user.Group}")
    print(f"Balance: {user.Balance}")
    print(f"Leverage: 1:{user.Leverage}")

# Fetch real-time account financials
account = manager.UserAccountGet(target_login)
if account:
    print(f"Equity: {account.Equity}")
    print(f"Free Margin: {account.MarginFree}")
    print(f"Floating Profit: {account.Profit}")

manager.Disconnect()
```

### Example 2: Performing a Balance Adjustment (Deposit/Withdrawal)
```python
import MT5Manager

manager = MT5Manager.ManagerAPI()
manager.Connect("127.0.0.1:443", 1000, "password", 0, 15000)

target_login = 10001
deposit_amount = 500.00
comment = "Deposit via CRM"

# DealerBalance(login, amount, type, comment, check_margin)
# type: 2 represents Balance operation
deal_ticket = manager.DealerBalance(
    login=target_login,
    amount=deposit_amount,
    type=2,
    comment=comment,
    check_margin=False
)

if deal_ticket > 0:
    print(f"Balance operation completed. Deal Ticket: {deal_ticket}")
else:
    err_code, ret, desc = MT5Manager.LastError()
    print(f"Balance adjustment failed: {desc}")

manager.Disconnect()
```

### Example 3: Subscribing to Live Quotes
```python
import time
import MT5Manager

manager = MT5Manager.ManagerAPI()
manager.Connect("127.0.0.1:443", 1000, "password", 0, 15000)

# Request latest tick for EURUSD
tick = manager.TickLast("EURUSD")
if tick:
    print(f"EURUSD Bid: {tick.Bid} | Ask: {tick.Ask}")

manager.Disconnect()
```
