#!/usr/bin/env python
# coding: utf-8

# # Crypto Currency! 

# ## Creating the blockchain

# In[1]:


import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# ## Part 1: Building a blockchain

# In[ ]:


class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block( proof = 1, previous_hash = "0")
        self.nodes = set()
        
    def create_block(self, proof, previous_hash):
        blocks = {
            "index" : len(self.chain) + 1,
            "timestamp" : str(datetime.datetime.now()),
            "proof" : proof,
            "previous_hash" : previous_hash,
            "transactions" : self.transactions
        }
        self.transactions = []
        self.chain.append(blocks)
        return blocks
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        
        new_proof = 1
        check_proof = False
        
        while check_proof is not True:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == "0000":
                check_proof = True
            else: 
                new_proof += 1
            
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys= True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block["previous_hash"] != self.hash(previous_block):
                return False
            previous_proof = previous_block["proof"]
            proof = block["proof"]
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != "0000":
                return False
            previous_block = block
            block_index += 1
        return True            
    
    def add_transaction(self, sender, reciever, amount):
        self.transactions.append({
            "sender" : sender,
            "reciever" : reciever,
            "amount" : amount
        })
        
        return self.get_previous_block()["index"] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f"http://{node}/get_chain")
            if response.status_code == 200:
                length = response.json()["length"]
                chain = response.json()["chain"]
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
            if longest_chain:
                self.chain = chain
                return True
            else:
                return False


# ## Mining the Blockchain
# 1. Creating webapp
# 2. Creating Bitcoin

# #### Web app

# In[ ]:


app = Flask(__name__)


# #### Create a address for the node on Port 5000

# In[ ]:


node_address = str(uuid4()).replace("-", "")


# #### Blockchain

# In[ ]:


blockchain = Blockchain()


# In[ ]:


@app.route("/mine_block", methods = ["GET"])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block["proof"]
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, reciever = "Gareema", amount = 1)
    block = blockchain.create_block(proof, previous_hash)
    response = {
        "transactions": block["transactions"],
        "message" : "Created the block. ",
        "index" : block["index"],
        "timestamp" : block["timestamp"],
        "proof" : block["proof"],
        "previous_hash" : block["previous_hash"],
    }
    return jsonify(response), 200


# In[ ]:


@app.route("/get_chain", methods = ["GET"])
def get_chain():
    response = {
        "chain" : blockchain.chain, 
        "length" : len(blockchain.chain)
    }
    return jsonify(response), 200


# In[ ]:


@app.route("/is_valid", methods = ["GET"])
def is_valid():
    valid = blockchain.is_chain_valid(blockchain.chain)
    if valid:
        response = {
            "message" : "Valid chain"
        }
    else:
        response = {
            "message" : "Invalid chain"
        }
    return jsonify(response), 200


# In[ ]:


@app.route("/add_transaction", methods = ["POST"])
def add_transaction():
    json = request.get_json()
    transaction_keys = ["sender", "reciever", "amount"]
    if not all(key in json for key in transaction_keys):
        return "Some elements from the keys are missing" , 400
    index = blockchain.add_transaction(json["sender"], json["reciever"], json["amount"])
    response = { "message" : f"This transaction will be added in the block {index}"}
    return jsonify(response), 201


# In[ ]:


@app.route("/connect_node", methods = ["POST"])
def connect_node():
    json = request.get_json()
    nodes = json.get("nodes")
    if nodes is None:
        return "No node", 201
    for node in nodes:
        blockchain.add_node(node)
    response = {"message" : "All the nodes are conected",
               "total_nodes" : list(blockchain.nodes)}
    return jsonify(response), 201


# In[ ]:


@app.route("/replace_chain", methods = ["GET"])
def replace_chain():
    valid = blockchain.replace_chain()
    if valid:
        response = {
            "message" : "Node had different chain, chain was replace",
            "new_chain" : blockchain.chain
        }
    else:
        response = {
            "message" : "All good, chain not replace",
            "actucal_chain" : blockchain.chain
        }
    return jsonify(response), 200

app.run(host = "0.0.0.0", port = 5002)