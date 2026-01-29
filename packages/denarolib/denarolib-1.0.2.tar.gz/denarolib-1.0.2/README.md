# Denaro Python Client Module Documentation

This module is a lightweight Python client for interacting with a **Denaro blockchain node**.  
It provides helper functions to query node state, blockchain data, addresses, transactions, and to
build, sign, and submit transactions.

**Important**:  
**All functions that communicate with the node return a `requests.Response` object**, not parsed data.  
You must explicitly call `.json()`, `.text`, `.status_code`, etc., on the returned value.

---

## Requirements

### Python
- Python **3.8+**

### Dependencies

```bash
pip install requests ecdsa
````

---

## Configuration

```python
DECIMALS = 10**6
NODE = "http://denaro.mine.bz:3006/"
DEBUG = True
```

### Description

* **DECIMALS**
  Atomic units per Denaro coin (`1 DNR = 1,000,000 units`).

* **NODE**
  Base URL of the Denaro node API.

* **DEBUG**
  If enabled, prints the raw `requests.Response` object and its decoded JSON payload.

---

## Return Value Convention (IMPORTANT)

All network-related functions return:

```python
requests.Response
```

This allows you to manually inspect:

```python
response.status_code
response.headers
response.text
response.json()
```

Example:

```python
resp = get_status()
if resp.status_code == 200:
    data = resp.json()
```

---

## Node & Blockchain API Functions

All functions below **return `requests.Response`**.

---

### `get_node_info() -> requests.Response`

Fetches general node information.

```python
resp = get_node_info()
```

---

### `get_status() -> requests.Response`

Returns blockchain and node status.

```python
resp = get_status()
```

---

### `get_peers() -> requests.Response`

Returns the list of known peers.

```python
resp = get_peers()
```

---

### `get_block() -> requests.Response`

Returns the latest block.

```python
resp = get_block()
```

---

### `get_blocks() -> requests.Response`

Returns a list of recent blocks.

```python
resp = get_blocks()
```

---

### `get_transaction(txhash) -> requests.Response`

Fetches a transaction by its hash.

```python
resp = get_transaction("TX_HASH")
```

---

### `get_pending_transactions() -> requests.Response`

Returns all pending (mempool) transactions.

```python
resp = get_pending_transactions()
```

---

### `get_address_info(addr) -> requests.Response`

Returns balance and transaction history for an address.

```python
resp = get_address_info("DNR_ADDRESS")
```

---

### `submit_tx(tx_hex) -> requests.Response`

Submits a hex-encoded transaction to the network.

```python
resp = submit_tx(tx_hex)
```

---

### `sync_blockchain() -> requests.Response`

Triggers a blockchain synchronization.

```python
resp = sync_blockchain()
```

---

### `get_mining_info() -> requests.Response`

Returns mining-related information.

```python
resp = get_mining_info()
```

---

### `submit_block(id, content, txs) -> requests.Response`

Submits a mined block.

```python
resp = submit_block(
    id="BLOCK_ID",
    content="BLOCK_CONTENT",
    txs=[tx_hex_1, tx_hex_2]
)
```

---

## Cryptographic Utilities

These functions **do not** return `requests.Response`.

---

### `sha256(b: bytes) -> bytes`

Computes a SHA-256 hash.

---

### `double_sha256(b: bytes) -> bytes`

Computes SHA256(SHA256(data)).

---

### `amount_to_int(amount: float) -> int`

Converts a human-readable Denaro amount to atomic units.

```python
amount_to_int(1.0)  # 1000000
```

---

## Transaction Construction

---

### `build_tx_object(from_addr, to_addr, amount_int) -> dict`

Creates an unsigned transaction object.

---

### `serialize_tx(tx: dict) -> bytes`

Serializes a transaction deterministically (sorted keys, compact JSON).

---

### `sign_tx(tx_bytes, privkey_hex) -> dict`

Signs a serialized transaction using **ECDSA secp256k1**.

Returns a dictionary containing:

* `signature` (hex)
* `public_key` (hex)

---

### `make_tx_hex(from_addr, to_addr, amount, privkey_hex) -> str`

Builds, signs, serializes, and hex-encodes a transaction.

```python
tx_hex = make_tx_hex(...)
```

---

## Sending Transactions

---

### `send(from_addr, to_addr, amount, privkey_hex) -> requests.Response`

High-level convenience function.

* Builds the transaction
* Signs it
* Submits it to the node

```python
resp = send(
    from_addr="FROM_ADDRESS",
    to_addr="TO_ADDRESS",
    amount=0.5,
    privkey_hex="PRIVATE_KEY_HEX"
)
```

Returned value is a **`requests.Response`**.

---

## Notes & Limitations

* All node interactions return `requests.Response`
* Private keys must be raw hex strings
* No UTXO selection, fee calculation, or balance validation
* Debug mode may expose sensitive data in logs

---

## Example Usage

```python
resp = get_address_info("FROM_ADDRESS")
print(resp.status_code)
print(resp.json())

resp = send(
    from_addr="FROM_ADDRESS",
    to_addr="TO_ADDRESS",
    amount=1.0,
    privkey_hex="PRIVATE_KEY"
)
print(resp.json())
```

---

## Disclaimer

This module is provided as-is for development and experimentation.
Use extreme caution when handling real funds.


