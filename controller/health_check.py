from flask import Blueprint, jsonify

health_check_bp = Blueprint('health_check', __name__)

@health_check_bp.route('/health_check', methods=['GET'])
def health_check():
    """
    Simple health check endpoint.
    """
    return jsonify({'status': 'OK'})