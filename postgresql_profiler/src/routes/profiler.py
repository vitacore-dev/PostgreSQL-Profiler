from flask import Blueprint

profiler_bp = Blueprint('profiler', __name__)

@profiler_bp.route('/health')
def health():
    return {'status': 'ok'}
