from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest
from kubernetes import client, config
import logging
import os

from controller import (
    get_canary_status,
    create_canary_deployment,
    delete_canary_deployment,
    list_canary_deployments,
    update_canary_deployment,
)

app = Flask(__name__)

config.load_incluster_config()
extensions_v1_beta1 = client.ExtensionsV1beta1Api()
custom_api = client.CustomObjectsApi()

@app.route('/canary/<name>', methods=['GET'])
def get_canary(name):
    """
    Get the status of a canary deployment.
    """
    status = get_canary_status(name)
    if not status:
        raise BadRequest(f"No canary deployment found with name {name}")
    return jsonify(status)

@app.route('/canary/all', methods=['GET'])
def list_canaries():
    """
    List all canary deployments.
    """
    return jsonify(list_canary_deployments())

@app.route('/canary', methods=['POST'])
def create_canary():
    """
    Create a new canary deployment.
    """
    if not request.json or 'functionName' not in request.json:
        raise BadRequest("Invalid request")
    function_name = request.json['functionName']
    new_version = request.json.get('newVersion', None)
    old_version = request.json.get('oldVersion', None)
    policy = request.json.get('policy', None)
    create_canary_deployment(function_name, new_version, old_version, policy)
    return jsonify({'status': 'success'})

@app.route('/canary/<name>', methods=['PUT'])
def update_canary(name):
    """
    Update an existing canary deployment.
    """
    status = get_canary_status(name)
    if not status:
        raise BadRequest(f"No canary deployment found with name {name}")
    function_name = request.json.get('functionName', status['functionName'])
    new_version = request.json.get('newVersion', status['newVersion'])
    old_version = request.json.get('oldVersion', status['oldVersion'])
    policy = request.json.get('policy', status['policy'])
    update_canary_deployment(name, function_name, new_version, old_version, policy)
    return jsonify({'status': 'success'})

@app.route('/canary/<name>', methods=['DELETE'])
def delete_canary(name):
    """
    Delete a canary deployment.
    """
    status = get_canary_status(name)
    if not status:
        raise BadRequest(f"No canary deployment found with name {name}")
    delete_canary_deployment(name, status['functionName'], status['newVersion'], status['oldVersion'])
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))