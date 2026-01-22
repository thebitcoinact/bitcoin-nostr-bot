import requests
import os
import time
from pynostr.event import Event
from pynostr.relay import Relay
from pynostr.key import PrivateKey

# Clé depuis secret GitHub
private_key_hex = os.getenv('NOSTR_PRIVATE_KEY')

if not private_key_hex:
    print("Erreur : clé privée non trouvée !")
    exit(1)

relays = [
    "wss://relay.damus.io",
    "wss://relay.primal.net",
    "wss://nostr.wine"
]

def get_btc_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
        return r.json()["bitcoin"]["usd"]
    except Exception as e:
        print(f"Erreur prix : {e}")
        return "?"

prix = get_btc_price()
message = f"Prix du Bitcoin : ${prix} USD (mise à jour horaire) #bitcoin #nostr"

pk = PrivateKey(bytes.fromhex(private_key_hex))
event = Event(content=message, kind=1)
pk.sign(event)

posted = 0
for relay_url in relays:
    try:
        relay = Relay(relay_url)
        relay.connect()
        relay.publish(event)
        relay.close()
        print(f"Posté sur {relay_url}")
        posted += 1
    except Exception as e:
        print(f"Erreur {relay_url}: {e}")

print(f"Run terminé : {posted}/3 relays OK - {message}")
