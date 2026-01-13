"""
Health Check & Monitoring Endpoints
Add these routes to dcf_model.py for production monitoring
"""

from flask import jsonify
from datetime import datetime
import sys
import os

# Add these imports at the top of dcf_model.py
# from db_production import check_db_health


@app.route('/api/health')
def health_check():
    """
    Comprehensive health check endpoint for monitoring services
    Returns 200 if healthy, 503 if any critical component is down
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }
    
    overall_healthy = True
    
    # 1. Check API Keys
    api_keys_configured = bool(ALPHAVANTAGE_API_KEY)
    health_status['checks']['alpha_vantage_api'] = {
        'status': 'configured' if api_keys_configured else 'missing',
        'critical': True
    }
    if not api_keys_configured:
        overall_healthy = False
    
    # 2. Check Database
    try:
        from db_production import check_db_health
        db_healthy, db_message = check_db_health()
        health_status['checks']['database'] = {
            'status': 'healthy' if db_healthy else 'unhealthy',
            'message': db_message,
            'critical': True
        }
        if not db_healthy:
            overall_healthy = False
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'error',
            'message': str(e),
            'critical': True
        }
        overall_healthy = False
    
    # 3. Check Optional Services
    health_status['checks']['news_api'] = {
        'status': 'configured' if NEWS_API_KEY else 'optional_missing',
        'critical': False
    }
    
    # 4. System Information
    health_status['system'] = {
        'python_version': sys.version.split()[0],
        'environment': os.environ.get('FLASK_ENV', 'development'),
        'hostname': os.environ.get('RENDER_SERVICE_NAME', 'local')
    }
    
    # Set overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
        return jsonify(health_status), 503
    
    return jsonify(health_status), 200


@app.route('/api/status')
def system_status():
    """
    Detailed system status endpoint (for admins/debugging)
    """
    import psutil  # pip install psutil for production monitoring
    
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': int((datetime.utcnow() - app.start_time).total_seconds()),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_percent': disk.percent
            },
            'application': {
                'requests_served': app.request_count,
                'errors_encountered': app.error_count
            }
        }
        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Add request counter middleware
@app.before_request
def track_requests():
    """Track request count for monitoring"""
    if not hasattr(app, 'request_count'):
        app.request_count = 0
        app.error_count = 0
        app.start_time = datetime.utcnow()
    app.request_count += 1


@app.errorhandler(Exception)
def track_errors(error):
    """Track errors for monitoring"""
    if hasattr(app, 'error_count'):
        app.error_count += 1
    
    # Log error (in production, send to Sentry/logging service)
    print(f"❌ Error: {error}")
    
    # Return user-friendly error
    return jsonify({
        'success': False,
        'error': 'An unexpected error occurred. Please try again.'
    }), 500
