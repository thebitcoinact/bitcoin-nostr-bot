import requests
import os
from pynostr.event import Event
from pynostr.relay import Relay
from pynostr.key import PrivateKey

print("=== Bitcoin Nostr Bot started ===")

private_key_str = os.getenv('NOSTR_PRIVATE_KEY')

if not private_key_str:
    print("ERROR: NOSTR_PRIVATE_KEY is empty or not set in GitHub Secrets")
    exit(1)

# Nettoyage basique et vérification hex
cleaned_key = private_key_str.strip().replace(' ', '').lower()
print(f"Key length after clean: {len(cleaned_key)}")
print(f"Key starts with: {cleaned_key[:8]}... (last 8: ...{cleaned_key[-8:]})")
print(f"Is hex? {'Yes' if len(cleaned_key) == 64 and all(c in '0123456789abcdef' for c in cleaned_key) else 'NO'}")

if len(cleaned_key) != 64 or not all(c in '0123456789abcdef' for c in cleaned_key):
    print("CRITICAL ERROR: Key is NOT a valid 64-char hex string. Fix your GitHub secret!")
    exit(1)

try:
    pk = PrivateKey(bytes.fromhex(cleaned_key))
    print("SUCCESS: Private key loaded from hex")
except Exception as e:
    print(f"Hex load failed: {str(e)}")
    exit(1)

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
        print(f"BTC price fetched: ${price}")
        return price
    except Exception as e:
        print(f"Price fetch failed: {e}")
        return "?"

price = get_btc_price()
content = f"Bitcoin Price: ${price} USD (hourly update) #bitcoin #nostr"

event = Event(content=content, kind=1)

# Signature
event.sign(pk.hex())

print(f"Event signed | ID: {event.id[:16]}...")

posted_count = 0
for url in relays:
    try:
        relay = Relay(url)
        relay.connect()
        relay.publish(event)
        relay.close()
        print(f"Posted successfully to {url}")
        posted_count += 1
    except Exception as e:
        print(f"Relay {url} failed: {str(e)}")

print(f"Done: {posted_count}/{len(relays)} relays successful")
print(f"Posted: {content}")
