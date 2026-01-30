# Fragment Stars API

Python SDK for purchasing Telegram Stars and Premium via Fragment API with dual commission modes.

## Features

- 🔐 **Dual Commission Modes**: KYC (lower commission) and Non-KYC (higher commission)
- 💰 **Prepayment Flow**: Automatic prepayment handling for Non-KYC mode
- ⚡ **Queue Management**: Automatic polling and status tracking
- 🎁 **Premium Eligibility**: Check if users can receive Premium gifts
- 📊 **Real-time Rates**: Get current commission rates
- 🔄 **Queue Status**: Monitor queue length and pause state

## Installation

```bash
pip install fragment-stars-api
```

## Quick Start

### Non-KYC Mode (Higher Commission)

No user cookies required - uses owner's cookies:

```python
from fragment_api import FragmentAPIClient

client = FragmentAPIClient()

# Buy 50 stars (Non-KYC mode)
result = client.buy_stars("username", 50, seed="your_seed_base64")
print(f"Success: {result.success}")
print(f"Mode: {result.mode}")  # 'no_kyc'
print(f"Commission: {result.commission_rate * 100}%")
```

### KYC Mode (Lower Commission)

Requires user's Fragment cookies:

```python
# Buy 50 stars (KYC mode)
result = client.buy_stars(
    "username", 
    50, 
    seed="your_seed_base64",
    cookies="user_cookies_base64"  # Providing cookies = KYC mode
)
print(f"Mode: {result.mode}")  # 'kyc'
```

### Check Commission Rates

```python
rates = client.get_rates()
print(f"Non-KYC: {rates.rate_no_kyc}%")
print(f"KYC: {rates.rate_with_kyc}%")
```

### Check Premium Eligibility

```python
result = client.check_premium_eligibility("username")
if result.eligible:
    print("✅ User is eligible for Premium gift")
else:
    print(f"❌ Not eligible: {result.error_code}")
```

### Check Queue Status

```python
status = client.get_queue_status()
print(f"Queue length: {status.queue_length}")
print(f"Is paused: {status.is_paused}")
```

## API Reference

### `FragmentAPIClient(base_url, timeout, poll_timeout)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | str | `https://fragment-api.ydns.eu:8443` | API URL |
| `timeout` | float | 30.0 | Request timeout (seconds) |
| `poll_timeout` | float | 300.0 | Max wait for queue (seconds) |

### `buy_stars(username, amount, seed, cookies=None, wait=True)`

Buy Telegram Stars.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | str | Yes | Telegram username |
| `amount` | int | Yes | Number of stars (minimum 50) |
| `seed` | str | Yes | Wallet seed (base64) |
| `cookies` | str | No | Fragment cookies (base64) - omit for Non-KYC mode |
| `wait` | bool | No | Wait for result (default: True) |

**Returns**: `PurchaseResult` with `success`, `mode`, `commission_rate`, etc.

### `buy_premium(username, duration, seed, cookies=None, wait=True)`

Buy Telegram Premium.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | str | Yes | Telegram username |
| `duration` | int | Yes | Months (3, 6, or 12) |
| `seed` | str | Yes | Wallet seed (base64) |
| `cookies` | str | No | Fragment cookies (base64) - omit for Non-KYC mode |
| `wait` | bool | No | Wait for result (default: True) |

### `get_rates()`

Get current commission rates.

**Returns**: `CommissionRatesResponse` with:
- `rate_no_kyc` - Non-KYC rate (percentage)
- `rate_with_kyc` - KYC rate (percentage)
- `rate_no_kyc_decimal` - Non-KYC rate (decimal)
- `rate_with_kyc_decimal` - KYC rate (decimal)

### `check_premium_eligibility(username)`

Check if user is eligible to receive Premium gift.

**Returns**: `CheckEligibilityResponse` with:
- `eligible` - Whether user is eligible
- `error_code` - Error code if not eligible
- `error_message` - Error description

### `get_queue_status()`

Get overall queue status.

**Returns**: `QueueStatusInfo` with:
- `queue_length` - Number of requests in queue
- `is_paused` - Whether queue is paused
- `pause_reason` - Reason for pause (if paused)

### `get_status(request_id)`

Get specific request status.

**Returns**: `QueuedRequest` with status details.

## Examples

See the [examples](examples/) directory for more:

- `buy_stars_no_kyc.py` - Purchase with Non-KYC mode
- `buy_stars_kyc.py` - Purchase with KYC mode
- `check_eligibility.py` - Check Premium eligibility
- `check_queue_status.py` - Monitor queue status

## Exceptions

```python
from fragment_api import FragmentAPIError, QueueTimeoutError

try:
    result = client.buy_stars("username", 50, seed="...")
except QueueTimeoutError:
    print("Request timed out")
except FragmentAPIError as e:
    print(f"Error: {e.error_code} - {e.message}")
```

## License

MIT
