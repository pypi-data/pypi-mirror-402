import requests
import time
import json
import hashlib
import struct
import base58
from enum import Enum
from math import ceil
from io import BytesIO
from decimal import Decimal
from typing import List, Dict, Tuple, Union, Optional

from ecdsa import SigningKey, VerifyingKey, SECP256k1
from ecdsa.util import sigencode_string, sigdecode_string

DECIMALS = 10**6
NODE = "http://denaro.mine.bz:3006/"
DEBUG = False

# --- Constants ---
ENDIAN = 'little'
CURVE = SECP256k1 # Changed from NIST256p to SECP256k1 to match denarolib's existing curve
SMALLEST = 1000000

# --- Helper Functions ---
def sha256(message: Union[str, bytes]):
    if isinstance(message, str):
        message = bytes.fromhex(message)
    return hashlib.sha256(message).hexdigest()

def byte_length(i: int):
    return ceil(i.bit_length() / 8.0)


class AddressFormat(Enum):
    FULL_HEX = 'hex'
    COMPRESSED = 'compressed'

def get_public_key_from_private_key(private_key_int: int) -> VerifyingKey:
    """
    Derives the public key VerifyingKey object from a private key integer.
    """
    signing_key = SigningKey.from_string(private_key_int.to_bytes(32, byteorder=ENDIAN), curve=CURVE)
    return signing_key.get_verifying_key()

def point_to_bytes(point: VerifyingKey, address_format: AddressFormat = AddressFormat.FULL_HEX) -> bytes:
    if address_format is AddressFormat.FULL_HEX:
        return point.to_string(encoding='uncompressed')
    elif address_format is AddressFormat.COMPRESSED:
        return point.to_string(encoding='compressed')
    else:
        raise NotImplementedError()

def bytes_to_point(point_bytes: bytes) -> VerifyingKey:
    try:
        return VerifyingKey.from_string(point_bytes, curve=CURVE)
    except Exception as e:
        raise ValueError(f"Invalid point_bytes for VerifyingKey: {e}")

def bytes_to_string(point_bytes: bytes) -> str:
    point = bytes_to_point(point_bytes)
    if len(point_bytes) == 65: # Uncompressed format
        address_format = AddressFormat.FULL_HEX
    elif len(point_bytes) == 33: # Compressed format
        address_format = AddressFormat.COMPRESSED
    else:
        raise NotImplementedError(f"Unsupported point_bytes length: {len(point_bytes)}")
    return point_to_string(point, address_format)

def point_to_string(point: VerifyingKey, address_format: AddressFormat = AddressFormat.COMPRESSED) -> str:
    if address_format is AddressFormat.FULL_HEX:
        point_bytes = point_to_bytes(point, AddressFormat.FULL_HEX)
        return point_bytes.hex()
    elif address_format is AddressFormat.COMPRESSED:
        # To get x and y from VerifyingKey, we need to access the underlying point object
        # The structure is VerifyingKey -> Public_key -> Point
        public_key_point = point.pubkey.point

        x = public_key_point.x()
        y = public_key_point.y()

        # Custom prefix logic based on original fastecdsa implementation
        prefix_byte = (42 if y % 2 == 0 else 43).to_bytes(1, ENDIAN)
        x_bytes = x.to_bytes(32, ENDIAN)
        
        address = base58.b58encode(prefix_byte + x_bytes)
        return address if isinstance(address, str) else address.decode('utf-8')
    else:
        raise NotImplementedError()

def string_to_bytes(string: str) -> bytes:
    try:
        point_bytes = bytes.fromhex(string)
    except ValueError:
        point_bytes = base58.b58decode(string)
    return point_bytes

def string_to_point(string: str) -> VerifyingKey:
    return bytes_to_point(string_to_bytes(string))

# --- TransactionOutput Class ---
class TransactionOutput:
    def __init__(self, address: str, amount: Decimal):
        if isinstance(address, VerifyingKey):
            raise Exception('TransactionOutput does not accept VerifyingKey anymore. Pass the address string instead')
        self.address = address
        self.address_bytes = string_to_bytes(address)
        self.public_key = string_to_point(address)
        assert (amount * SMALLEST) % 1 == 0.0, 'too many decimal digits'
        self.amount = amount

    def tobytes(self):
        amount = int(self.amount * SMALLEST)
        count = byte_length(amount)
        return self.address_bytes + count.to_bytes(1, ENDIAN) + amount.to_bytes(count, ENDIAN)

    def verify(self):
        return self.amount > 0 and isinstance(self.public_key, VerifyingKey)

    @property
    def as_dict(self):
        res = vars(self).copy()
        if 'public_key' in res: del res['public_key']
        return res

# --- TransactionInput Class ---
class TransactionInput:
    public_key = None
    signed: Tuple[int, int] = None
    amount: Decimal = None

    def __init__(self, input_tx_hash: str, index: int, private_key: int = None, amount: Decimal = None, public_key: VerifyingKey = None):
        self.tx_hash = input_tx_hash
        self.index = index
        self.private_key = private_key
        self.amount = amount
        self.public_key = public_key

    def sign(self, tx_hex: str, private_key: int = None):
        private_key_int = private_key if private_key is not None else self.private_key
        if private_key_int is None:
            raise Exception("Private key not available for signing.")
        
        signing_key = SigningKey.from_string(private_key_int.to_bytes(32, byteorder=ENDIAN), curve=CURVE)
        message_hash = bytes.fromhex(sha256(tx_hex))
        raw_signature = signing_key.sign(message_hash)
        
        self.signed = sigdecode_string(raw_signature, CURVE.order)

    def get_public_key(self) -> VerifyingKey:
        if self.private_key is not None:
            return get_public_key_from_private_key(self.private_key)
        if self.public_key is not None:
            return self.public_key
        raise Exception("Public key not available for signing")

    def tobytes(self):
        return bytes.fromhex(self.tx_hash) + self.index.to_bytes(1, ENDIAN)

    def get_signature(self):
        if self.signed is None:
            raise Exception("Transaction input not signed.")
        r, s = self.signed
        return r.to_bytes(32, ENDIAN).hex() + s.to_bytes(32, ENDIAN).hex()

    @property
    def as_dict(self):
        self_dict = vars(self).copy()
        self_dict['signed'] = self_dict['signed'] is not None
        if 'public_key' in self_dict and self_dict['public_key'] is not None: self_dict['public_key'] = point_to_string(self_dict['public_key'])
        if 'private_key' in self_dict: del self_dict['private_key']
        return self_dict

    def __eq__(self, other):
        assert isinstance(other, self.__class__)
        return (self.tx_hash, self.index) == (other.tx_hash, other.index)

# --- Transaction Class ---
class Transaction:
    def __init__(self, inputs: List[TransactionInput], outputs: List[TransactionOutput], message: bytes = None, version: int = None):
        if len(inputs) >= 256:
            raise Exception(f'You can spend max 255 inputs in a single transactions, not {len(inputs)}')
        if len(outputs) >= 256:
            raise Exception(f'You can have max 255 outputs in a single transactions, not {len(outputs)}')
        self.inputs = inputs
        self.outputs = outputs
        self.message = message
        if version is None:
            if all(len(tx_output.address_bytes) == 65 for tx_output in outputs): # Uncompressed
                version = 1
            elif all(len(tx_output.address_bytes) == 33 for tx_output in outputs): # Compressed
                version = 3
            else:
                raise NotImplementedError("Mixed or unknown address formats in outputs")
        if version > 3:
            raise NotImplementedError("Transaction version not supported")
        self.version = version
        
        self._hex: str = None
        self.fees: Decimal = None
        self.tx_hash: str = None

    def hex(self, full: bool = True):
        inputs, outputs = self.inputs, self.outputs
        hex_inputs = ''.join(tx_input.tobytes().hex() for tx_input in inputs)
        hex_outputs = ''.join(tx_output.tobytes().hex() for tx_output in outputs)

        version = self.version

        self._hex = ''.join([
            version.to_bytes(1, ENDIAN).hex(),
            len(inputs).to_bytes(1, ENDIAN).hex(),
            hex_inputs,
            (len(outputs)).to_bytes(1, ENDIAN).hex(),
            hex_outputs
        ])

        if not full and (version <= 2 or self.message is None):
            return self._hex

        if self.message is not None:
            if version <= 2:
                self._hex += bytes([1, len(self.message)]).hex()
            else:
                self._hex += bytes([1]).hex()
                self._hex += (len(self.message)).to_bytes(2, ENDIAN).hex()
            self._hex += self.message.hex()
            if not full:
                return self._hex
        else:
            self._hex += (0).to_bytes(1, ENDIAN).hex()

        if full:
            signatures = []
            for tx_input in inputs:
                signed = tx_input.get_signature()
                # This logic is problematic if multiple inputs use the same private key
                # but results in different signatures due to nonce.
                # Assuming here that we want unique signatures appended once.
                if signed not in signatures:
                    signatures.append(signed)
                    self._hex += signed

        return self._hex

    def hash(self):
        if self.tx_hash is None:
            self.tx_hash = sha256(self.hex(full=False))
        return self.tx_hash

    def sign(self, private_keys: list = []):
        for input_tx in self.inputs:
            if input_tx.private_key is not None:
                input_tx.sign(self.hex(full=False))
        return self

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.hex() == other.hex()
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

# --- Core Transaction Creation Functions ---
def create_transaction_hex(utxos: List[Dict], to_address: str, amount: Decimal, sender_privkey_hex: str, fee: Decimal) -> str:
    sender_privkey_int = int(sender_privkey_hex, 16)
    sender_public_key_point = get_public_key_from_private_key(sender_privkey_int)
    sender_public_address = point_to_string(sender_public_key_point)

    total_needed = amount + fee
    
    selected_inputs: List[TransactionInput] = []
    input_sum = Decimal('0.0')

    for utxo in utxos:
        if input_sum < total_needed:
            selected_inputs.append(
                TransactionInput(
                    input_tx_hash=utxo['tx_hash'],
                    index=utxo['index'],
                    private_key=sender_privkey_int,
                    amount=Decimal(str(utxo['amount'])) / DECIMALS, # Convert from smallest unit if necessary, assuming utxo['amount'] is in smallest unit
                    public_key=sender_public_key_point
                )
            )
            input_sum += Decimal(str(utxo['amount'])) / DECIMALS
        else:
            break
    
    if input_sum < total_needed:
        raise ValueError(f"Insufficient funds. Needed {total_needed}, but only found {input_sum}")

    outputs: List[TransactionOutput] = []
    outputs.append(TransactionOutput(address=to_address, amount=amount))

    change_amount = input_sum - total_needed
    if change_amount > Decimal('0'):
        outputs.append(TransactionOutput(address=sender_public_address, amount=change_amount))

    transaction = Transaction(inputs=selected_inputs, outputs=outputs)
    transaction.sign(private_keys=[sender_privkey_int])
    tx_hex = transaction.hex(full=True)

    return tx_hex

# --- Wrapper for sending transactions ---
def send(to_address: str, amount: Decimal, privkey_hex: str, fee: Optional[Decimal] = None) -> str:
    if fee is None:
        fee = Decimal('0.001')

    sender_privkey_int = int(privkey_hex, 16)
    sender_public_key = get_public_key_from_private_key(sender_privkey_int)
    sender_address = point_to_string(sender_public_key)

    # Fetch UTXOs for the sender's address
    address_info_response = get_address_info(sender_address)
    if address_info_response.status_code != 200:
        raise Exception(f"Failed to fetch address info: {address_info_response.text}")
    
    address_info = address_info_response.json()
    utxos_raw = address_info.get('utxos', [])

    utxos = []
    for utxo_raw in utxos_raw:
        # Assuming utxo_raw has 'tx_hash', 'tx_output_index', 'amount'
        utxos.append({
            'tx_hash': utxo_raw['tx_hash'],
            'index': utxo_raw['tx_output_index'],
            'amount': Decimal(utxo_raw['amount']) # Assuming amount is already in correct unit (e.g., float or string that Decimal can parse)
        })

    return create_transaction_hex(
        utxos=utxos,
        to_address=to_address,
        amount=amount,
        sender_privkey_hex=privkey_hex,
        fee=fee
    )


# Existing denarolib.py functions below this line

def get_node_info():
    response = requests.get(NODE)
    if DEBUG: print(response); print(response.json())
    return response

def get_status():
    response = requests.get(NODE+"get_status")
    if DEBUG: print(response); print(response.json())
    return response

def get_peers():
    response = requests.get(NODE+"get_peers")
    if DEBUG: print(response); print(response.json())
    return response

def get_block():
    response = requests.get(NODE+"get_block")
    if DEBUG: print(response); print(response.json())
    return response

def get_blocks():
    response = requests.get(NODE+"get_blocks")
    if DEBUG: print(response); print(response.json())
    return response

def get_transaction(txhash):
    response = requests.get(NODE+"get_transaction?"+txhash)
    if DEBUG: print(response); print(response.json())
    return response

def get_pending_transactions():
    response = requests.get(NODE+"get_transactions")
    if DEBUG: print(response); print(response.json())
    return response

def get_address_info(addr):
    response = requests.get(NODE+"get_address_info?address="+addr)
    if DEBUG: print(response); print(response.json())
    return response

def submit_tx(tx_hex):
    response = requests.post(NODE+"submit_tx", json={"tx_hex":tx_hex})
    if DEBUG: print(response); print(response.json())
    return response

def sync_blockchain():
    response = requests.get(NODE+"sync_blockchain")
    if DEBUG: print(response); print(response.json())
    return response

def get_mining_info():
    response = requests.get(NODE+"get_mining_info")
    if DEBUG: print(response); print(response.json())
    return response

def submit_block(id,content,txs):
    response = requests.post(NODE+"submit_block", json={"id":id, "block_content":content, "txs":txs})
    if DEBUG: print(response); print(response.json())
    return response