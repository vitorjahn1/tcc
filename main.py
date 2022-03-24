import datetime
import hashlib
import json as json

from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse


class BlockChain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.nodes = set()
        self.create_block(proof=1, previous_hash='0')
        
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False

        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof ** 2 - previous_proof ** 2).encode()).hexdigest()

            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1

            return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha3_256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1

        while block_index < len(chain):
            block = block_index
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False

            previous_block = block
            block_index += 1

        return True

    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount})
        return self.get_previous_block('index') + 1

    def add_address(self, address):
        url_parse = urlparse(address)
        self.nodes.add(url_parse.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        next_lenght = len(self.chain)

        for node in network:
            reponse = requests.get(f'http://{node}/getchain')
            if reponse.status_code == 200:
                lenght = reponse.json()['lenght']
                chain = reponse.json()['chain']
                if lenght > next_lenght and self.is_chain_valid(chain):
                    next_lenght = lenght
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

app = Flask(__name__)
blockchain = BlockChain()
node_address = str(uuid4()).replace('-', '')


@app.route('/mineblock', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = blockchain['proof']
    proof = blockchain.proof_of_work(previous_block)
    block = blockchain.create_block(proof, previous_block)
    blockchain.add_transaction(sender=node_address, receiver='Vitor', amount=1)
    response = {'mesage': 'Você minerou um block',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions:': block['transactions']}
    return jsonify(response), 200


@app.route('/getchain')
def get_chain():
    response = {'chain': blockchain.chain,
                'lenght': len(blockchain.chain)}
    return jsonify(response), 200


@app.route('/isvalid')
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)


@app.route('/addtransaction', methods=['POST'])
def addtransaction():
    json = request.get_json()

    transacctions_keys = ['receiver', 'sender', 'amount']
    if not all(key in json for key in transacctions_keys):
        return 'Alguns elementos faltam', 400
    index = blockchain.add_transaction(sender=json['sender'], receiver=json['receiver'], amount=json['amount'])
    response = {f'Transação criada com sucesso : {index}'}
    return jsonify(response), 201


@app.route('/connectnode', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')

    if nodes is None:
        return 'vazio', 400

    for node in nodes:
        blockchain.add_node(node)

    response = {'mensagem':'todos os nos conectados'}
    return jsonify(response), 201

@app.route('/replacechain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()

    if is_chain_replaced:
        response = {'message': 'os nos tinham cadeias diferentes e por isso foram substituidas',
                    'new_chain': blockchain.chain}
    else: response = {'message':'não houve substituição',
                      'chain':blockchain.chain}

    return jsonify(response), 201


app.run(host='0.0.0.0', port=5000)

