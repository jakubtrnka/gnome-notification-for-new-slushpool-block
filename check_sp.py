import json
import requests
import os
import sys
import re
import gi

from base64 import urlsafe_b64encode

RPC_PORT = 8332

RPC_USER = os.environ.get("BITCOIN_RPC_USER", default="")
RPC_PASS = os.environ.get("BITCOIN_RPC_PASS", default="")


def rpc_req(method: str, params=[]):
    url = f"http://localhost:{RPC_PORT}"
    payload = {
        "method": method,
        "params": params,
        "jsonrpc": "1.0",
    }
    headers = {"content-type": "content-type: text/plain;"}
    auth = (RPC_USER, RPC_PASS)
    resp = requests.post(
        url, data=json.dumps(payload), headers=headers, auth=auth
    ).json()
    return resp.get("result", {})


def _get_cb_tx_hash_from_block(block_hash: str):
    x = rpc_req("getblock", [block_hash])
    transactions = x.get("tx", [])
    try:
        cb = transactions[0]
    except IndexError:
        print("Unknown json data format", file=sys.stderr)
        exit(1)

    return cb


def get_nice_cb_transaction(block_hash: str):
    tx_hash = _get_cb_tx_hash_from_block(block_hash)
    nice_cb = rpc_req("getrawtransaction", [f"{tx_hash}", 1, f"{block_hash}"])
    return nice_cb


def coinbase_filter(cb: dict, func) -> bool:
    tx_inputs = cb.get("vin", [])
    try:
        raw_coinbase = tx_inputs[0].get("coinbase")
    except IndexError:
        print("Unknown cb tx format", file=sys.stderr)
        exit(1)

    return func(raw_coinbase)


def is_slushpool_block(raw_cb_hex: str) -> bool:
    try:
        raw_cb = bytes.fromhex(raw_cb_hex)
    except:
        print("invalid cb string", file=sys.stderr)
        return False
    utf_cb = raw_cb.decode("utf-8", "replace")
    if re.search(r"/slush/", utf_cb) is None:
        return False
    else:
        return True


def gnome_notify(blockhash: str):
    gi.require_version("Notify", "0.7")
    from gi.repository import Notify, GLib

    Notify.init("Bitcoin")
    Hello = Notify.Notification.new(
        "SlushPool Block",
        f"https://blockstream.info/block/{blockhash}",
        "dialog-information",
    )
    Hello.set_hint("sound-name", GLib.Variant.new_string("message-new-instant"))
    Hello.show()


def main():
    try:
        bl_hash = sys.argv[1]
    except IndexError:
        print("No block hash has been supplied", file=sys.stderr)
        exit(1)
    coinbase_tx = get_nice_cb_transaction(bl_hash)
    if coinbase_filter(coinbase_tx, func=is_slushpool_block):
        gnome_notify(bl_hash)


if __name__ == "__main__":
    main()
