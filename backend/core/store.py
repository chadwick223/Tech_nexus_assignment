import json
import os
from filelock import FileLock
from django.conf import settings
from pathlib import Path

DATA_DIR = Path(settings.BASE_DIR) / 'data'
CART_FILE = DATA_DIR / 'cart.json'
LOCK_FILE = DATA_DIR / 'cart.json.lock'
INVENTORY_FILE = DATA_DIR / 'inventory.json'

DATA_DIR.mkdir(exist_ok=True)

def read_inventory():
    if not INVENTORY_FILE.exists():
        return {}
    with open(INVENTORY_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def _get_default_cart():
    return {"items": {}}

def read_cart():
    if not CART_FILE.exists():
        return _get_default_cart()
    with open(CART_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return _get_default_cart()

def write_cart(data):
    with open(CART_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def update_cart(func):
    """
    Acquires a file lock, reads the cart, applies the callback `func` to mutate data, 
    and writes it back. Returns the updated cart.
    """
    with FileLock(LOCK_FILE):
        cart_data = read_cart()
        func(cart_data)
        write_cart(cart_data)
        return cart_data
