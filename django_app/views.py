from django.shortcuts import render, get_object_or_404
from .models import Transaction, TransactionData, RpcException
import binascii
import requests
import jsonrpcclient
from pycoin.cmds.tx import script_for_address_or_opcodes
from pycoin.symbols.btc import create_bitcoinish_network
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


session = requests.Session()
retry = Retry(connect=3, backoff_factor=.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)


def show_all_txs(request):
    txs = Transaction.objects.all()
    for tx in txs:
        tx.save()
    return render(request, 'django_app/all_txs.html', context={
        'txs': txs
    })


def show_tx(request, txid:str):
    tx = get_object_or_404(Transaction, Id=txid)
    return render(request, 'django_app/one_tx.html', context={
        'tx': tx
    })


def get_network_data():
    return create_bitcoinish_network(
        wif_prefix_hex="80",
        address_prefix_hex="19",
        pay_to_script_prefix_hex="32",
        bip32_prv_prefix_hex="0488ade4",
        bip32_pub_prefix_hex="0488B21E",
        bech32_hrp="bc",
        bip49_prv_prefix_hex="049d7878",
        bip49_pub_prefix_hex="049D7CB2",
        bip84_prv_prefix_hex="04b2430c",
        bip84_pub_prefix_hex="04B24746",
        magic_header_hex="F1CFA6D3",
        default_port=3666,
        symbol='bsc',
        network_name='BCS',
        subnet_name='Chain'
    )


def get_last_utxo():
    utxo = session.get(TransactionData.UTXO_ADDRESS, verify=False)
    last_txid = utxo.json()[-1]['transactionId']
    last_index = utxo.json()[-1]['outputIndex']
    last_script = utxo.json()[-1]['scriptPubKey']
    return {
        'last_txid': last_txid,
        'last_index': last_index,
        'last_script': last_script
    }


def get_new_address():
    response = session.post(url=TransactionData.RPC_URL, json=jsonrpcclient.request('getnewaddress'))
    result = response.json()
    if not result['error']:
        return result['result']
    else:
        raise RpcException('Something went wrong while getting new address')


def send(request):
    network = get_network_data()
    utxo = get_last_utxo()
    address = get_new_address()

    tx_in = network.Tx.TxIn(utxo['last_txid'], utxo['last_index'], binascii.unhexlify(utxo['last_script']))
    script = script_for_address_or_opcodes(network, address)
    tx_out = network.Tx.TxOut(1e8, script)
    tx = network.Tx(1, [tx_in], [tx_out])
    tx.set_unspents([tx_out])

    create_transaction_dct = {
        "txid": tx.as_hex(),
        "vout": 1
    }

    create_transaction_address = {
        f"{address}": 1
    }

    response = session.post(TransactionData.RPC_URL, json=request(
        f'createrawtransaction "[{create_transaction_dct}]" "[{create_transaction_address}]"'), verify=False)

    response = session.post(TransactionData.RPC_URL, json=request(
        f'signrawtransactionwithkey "{tx.as_hex()}" "[\"{TransactionData.PRIV_KEY}\"]"'), verify=False)

    response = session.post(TransactionData.RPC_URL, json=request(
        f'sendrawtransaction "{tx.as_hex()}"'
    ), verify=False)
    newtx = response.json()['result']
    to_save = Transaction()
    to_save.Id = newtx
    to_save.save()