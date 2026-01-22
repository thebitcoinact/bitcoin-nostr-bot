import requests
import os
import time
import ssl
from nostr.event import Event
from nostr.relay_manager import RelayManager
from nostr.key import PrivateKey

print("=== Bitcoin Nostr Bot started (python-nostr compatible) ===")

private_key_hex = os.getenv('NOSTR_PRIVATE_KEY')

if not private_key_hex:
    print("ERROR: NOSTR_PRIVATE_KEY is empty or not set")
    exit(1)

# Vérification hex stricte
cleaned_key = private_key_hex.strip().lower()
if len(cleaned_key) != 64 or not all(c in '0123456789abcdef' for c in cleaned_key):
    print(f"ERROR: Invalid hex key (length {len(cleaned_key)})")
    exit(1)

try:
    pk = PrivateKey(bytes.fromhex(cleaned_key))
    print("SUCCESS: Private key loaded from hex")
except Exception as e:
    print(f"Key load failed: {e}")
    exit(1)

# Clé publique hex (obligatoire pour Event)
public_key_hex = pk.public_key.hex()
print(f"Public key hex: {public_key_hex[:8]}...")

relays = [
    "wss://relay.damus.io",
    "wss://relay.primal.net",
    "wss://nostr.wine"
]

def get_btc_price():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
            timeout=10
        )
        r.raise_for_status()
        price = r.json()["bitcoin"]["usd"]
        print(f"BTC price: ${price}")
        return price
    except Exception as e:
        print(f"Price error: {e}")
        return "?"

price = get_btc_price()
content = f"Bitcoin Price: ${price} USD (hourly update) #bitcoin #nostr"

# Event avec public_key en premier
event = Event(
    public_key=public_key_hex,
    content=content,
    kind=1
)

pk.sign_event(event)

print(f"Event signed | ID: {event.id[:16]}...")

# RelayManager SANS timeout dans __init__
relay_manager = RelayManager()

for url in relays:
    relay_manager.add_relay(url)

relay_manager.open_connections({"cert_reqs": ssl.CERT_NONE})
time.sleep(3)  # Temps pour connexions (essentiel !)

relay_manager.publish_event(event)
time.sleep(5)  # Temps suffisant pour publication (augmente si besoin)

print("Event published via RelayManager")

# Logs des notices/erreurs des relays
while relay_manager.message_pool.has_notices():
    notice = relay_manager.message_pool.get_notice()
    print(f"Relay notice: {notice.content}")

relay_manager.close_connections()

print("Done - Bot run finished")
print(f"Posted message: {content}")
