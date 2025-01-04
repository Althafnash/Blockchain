import datetime
import hashlib
import json
from flask import Flask, jsonify, render_template, request
import os

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.load_chain()
        if not self.chain:
            self.create_block(proof=1, previous_hash='0')

    def create_block(self, proof, previous_hash):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": str(datetime.datetime.now()),
            "proof": proof,
            "previous_hash": previous_hash,
            "transactions": self.pending_transactions
        }
        self.pending_transactions = []  # Clear pending transactions after adding to the block
        self.chain.append(block)
        self.save_chain()
        return block

    def add_transaction(self, sender, receiver, amount):
        transaction = {
            "sender": sender,
            "receiver": receiver,
            "amount": amount
        }
        self.pending_transactions.append(transaction)
        return self.get_previous_block()["index"] + 1

    def load_chain(self):
        if os.path.exists("blockchain.json"):
            with open("blockchain.json", "r") as file:
                try:
                    self.chain = json.load(file)
                except json.JSONDecodeError:
                    self.chain = [] 

    def save_chain(self):
        with open("blockchain.json", "w") as file:
            json.dump(self.chain, file, indent=4)

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False

        while not check_proof:
            hash_operation = hashlib.sha256(
                str(new_proof**2 - previous_proof**2).encode()
            ).hexdigest()
            if hash_operation[:5] == "00000":
                check_proof = True
            else:
                new_proof += 1

        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1

        while block_index < len(chain):
            block = chain[block_index]
            if block["previous_hash"] != self.hash(previous_block):
                return False

            previous_proof = previous_block["proof"]
            proof = block["proof"]
            hash_operation = hashlib.sha256(
                str(proof**2 - previous_proof**2).encode()
            ).hexdigest()

            if hash_operation[:5] != "00000":
                return False
            previous_block = block
            block_index += 1

        return True


# Flask app
app = Flask(__name__)

# Blockchain instance
blockchain = Blockchain()


@app.route('/mine_block', methods=["GET"])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block["proof"]
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    block = blockchain.create_block(proof, previous_hash)

    response = {
        "MESSAGE": "A block is mined successfully!",
        "Index": block["index"],
        "Timestamp": block["timestamp"],
        "Proof": block["proof"],
        "Previous_hash": block["previous_hash"],
        "Transactions": block["transactions"]
    }

    return jsonify(response), 200


@app.route("/", methods=["GET"])
def index():
    return render_template("add_transaction.html")


@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    data = request.form
    sender = data.get("sender")
    receiver = data.get("receiver")
    amount = data.get("amount")

    if not sender or not receiver or not amount:
        return jsonify({"Message": "Transaction data is incomplete."}), 400

    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"Message": "Invalid amount format."}), 400

    index = blockchain.add_transaction(sender, receiver, amount)
    return jsonify({"Message": f"Transaction will be added to Block {index}"}), 201


@app.route('/get_chain', methods=["GET"])
def display_chain():
    response = {
        "chain": blockchain.chain,
        "length": len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/valid', methods=["GET"])
def valid():
    is_valid = blockchain.chain_valid(blockchain.chain)

    response = {
        "Message": "The Blockchain is valid." if is_valid else "The Blockchain is not valid."
    }

    return jsonify(response), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
