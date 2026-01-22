import requests
import os
import time
from pynostr.event import Event
from pynostr.relay import Relay
from pynostr.key import PrivateKey

# Clé privée depuis GitHub Secret (NOSTR_PRIVATE_KEY)
# Peut être au format nsec1... ou hex pur (64 caractères)
private_key_str = os.getenv('NOSTR_PRIVATE_KEY')

if not private_key_str:
    print("ERROR: NOSTR_PRIVATE_KEY secret is not set in GitHub Secrets")
    exit(1)

# Chargement de la clé (gère nsec ou hex)
try:
    pk = PrivateKey.from_nsec(private_key_str)
    print("Private key loaded as nsec")
except ValueError:
    try:
        pk = PrivateKey(bytes.fromhex(private_key_str))
        print("Private key loaded as hex")
    except ValueError:
        print("ERROR: Invalid key format (must be nsec... or 64-char hex)")
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
        return r.json()["bitcoin"]["usd"]
    except Exception as e:
        print(f"Price fetch error: {e}")
        return "?"

prix = get_btc_price()
content = f"Bitcoin Price: ${prix} USD (hourly update) #bitcoin #nostr"

event = Event(
    content=content,
    kind=1
)

# Signature correcte
event.sign(pk.hex())

print(f"Event created and signed (id: {event.id})")

posted_count = 0
for relay_url in relays:
    try:
        relay = Relay(relay_url)
        relay.connect()
        relay.publish(event)
        relay.close()
        print(f"Successfully posted to {relay_url}")
        posted_count += 1
    except Exception as e:
        print(f"Failed on {relay_url}: {e}")

print(f"Execution finished: {posted_count}/{len(relays)} relays successful")
print(f"Posted message: {content}")
