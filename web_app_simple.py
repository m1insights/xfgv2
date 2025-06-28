"""
Simple xFGv2 Web App for Deployment
Minimal version without database dependencies for initial deployment.
"""

import os
import sys
import logging
from datetime import datetime, time

# Print debug info for deployment
print(f"🐍 Python version: {sys.version}")
print(f"📁 Working directory: {os.getcwd()}")
print(f"📦 Available packages:")

try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
    print("✅ Flask imported successfully")
except ImportError as e:
    print(f"❌ Flask import failed: {e}")
    sys.exit(1)

try:
    from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
    print("✅ Flask-Login imported successfully")
except ImportError as e:
    print(f"❌ Flask-Login import failed: {e}")
    sys.exit(1)

try:
    from werkzeug.security import check_password_hash, generate_password_hash
    print("✅ Werkzeug security imported successfully")
except ImportError as e:
    print(f"❌ Werkzeug import failed: {e}")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Simple user storage (replace with database later)
USERS = {
    'admin': generate_password_hash('password')
}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id) if user_id in USERS else None

# Market hours helper
def is_market_hours():
    """Check if market is currently open (9:30 AM - 4:00 PM EST)."""
    try:
        now = datetime.now()
        current_time = now.time()
        return time(9, 30) <= current_time <= time(16, 0)
    except:
        return True  # Default to open if unable to determine

def is_trading_day():
    """Check if today is a trading day (Monday-Friday)."""
    try:
        return datetime.now().weekday() < 5  # 0-4 are Mon-Fri
    except:
        return True  # Default to trading day

@app.route('/health')
def health_check():
    """Health check endpoint for Render."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': 'xFGv2-simple'
    })

@app.route('/')
@login_required
def levels_dashboard():
    """Main dashboard."""
    current_time = datetime.now()
    
    # Mock data for initial deployment
    template_data = {
        'today': current_time.strftime('%Y-%m-%d'),
        'current_time': current_time,
        'is_market_hours': is_market_hours(),
        'is_trading_day': is_trading_day(),
        'pivot_entry_time': None,
        
        # Mock status data
        'es_status': {
            'csv_complete': False,
            'manual_complete': False,
            'overall_complete': False,
            'csv_count': 0,
            'manual_count': 0,
            'total_levels': 0
        },
        'nq_status': {
            'csv_complete': False,
            'manual_complete': False,
            'overall_complete': False,
            'csv_count': 0,
            'manual_count': 0,
            'total_levels': 0
        },
        
        # Mock levels data
        'es_levels': {},
        'nq_levels': {}
    }
    
    try:
        return render_template('levels_v2.html', **template_data)
    except Exception as e:
        # Fallback if template not found
        logger.warning(f"Template error: {e}")
        return jsonify({
            'status': 'xFGv2 Simple Mode Active',
            'message': 'Dashboard template not available in simple mode',
            'data': template_data,
            'timestamp': current_time.isoformat()
        })

@app.route('/api/v2/manual-levels', methods=['POST'])
@login_required
def add_manual_levels():
    """Add manual pivot levels."""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'ES')
        levels = data.get('levels', {})
        
        # For now, just return success
        logger.info(f"Manual levels for {symbol}: {levels}")
        
        return jsonify({
            'success': True,
            'message': f'Manual levels saved for {symbol}',
            'levels_added': len(levels)
        })
        
    except Exception as e:
        logger.error(f"Error adding manual levels: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/alert-settings', methods=['GET', 'POST'])
@login_required
def alert_settings():
    """Get or save alert settings."""
    try:
        if request.method == 'GET':
            return jsonify({
                'es': {
                    'distance': 3.0,
                    'cooldown': 15,
                    'enabled': True
                },
                'nq': {
                    'distance': 5.0,
                    'cooldown': 15,
                    'enabled': True
                },
                'global': {
                    'marketHoursOnly': True,
                    'dailyLimit': 50,
                    'testMode': True  # Default to test mode
                }
            })
        
        elif request.method == 'POST':
            settings = request.get_json()
            logger.info(f"Alert settings updated: {settings}")
            
            return jsonify({
                'success': True,
                'message': 'Alert settings saved successfully'
            })
            
    except Exception as e:
        logger.error(f"Error handling alert settings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/test-sms', methods=['POST'])
@login_required
def test_sms():
    """Send a test SMS message."""
    try:
        # Check if Twilio credentials are available
        if not all([
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN'),
            os.getenv('TWILIO_FROM_PHONE'),
            os.getenv('TWILIO_TO_PHONE')
        ]):
            return jsonify({
                'success': False,
                'message': 'Twilio credentials not configured'
            }), 400
        
        try:
            from twilio.rest import Client
            
            client = Client(
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN')
            )
            
            test_message = f"xFGv2 Test SMS - {datetime.now().strftime('%H:%M:%S')} EST"
            
            message = client.messages.create(
                body=test_message,
                from_=os.getenv('TWILIO_FROM_PHONE'),
                to=os.getenv('TWILIO_TO_PHONE')
            )
            
            return jsonify({
                'success': True,
                'message': f'Test SMS sent successfully! SID: {message.sid}'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'SMS send failed: {str(e)}'
            }), 500
            
    except ImportError:
        return jsonify({
            'success': False,
            'message': 'Twilio not installed'
        }), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and check_password_hash(USERS[username], password):
            user = User(username)
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('levels_dashboard'))
        
        return jsonify({'error': 'Invalid username or password'}), 401
    
    try:
        return render_template('login_simple.html')
    except Exception as e:
        # Fallback login for simple mode
        logger.warning(f"Login template error: {e}")
        return f"""
        <html>
        <head><title>xFGv2 Login</title></head>
        <body style="font-family: Arial; padding: 20px;">
        <h2>xFGv2 Simple Login</h2>
        <form method="post">
            <p>Username: <input type="text" name="username" value="admin"></p>
            <p>Password: <input type="password" name="password" value="password"></p>
            <p><input type="submit" value="Login"></p>
        </form>
        <p><small>Default: admin / password</small></p>
        </body>
        </html>
        """

@app.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    return redirect(url_for('login'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print("=" * 60)
    print("🚀 xFGv2 Simple Web Interface Starting")
    print("=" * 60)
    print(f"📊 Demo credentials: admin / password")
    print(f"🌐 URL: http://localhost:{port}")
    print(f"📁 Simple deployment mode (no database)")
    print(f"⏰ Current time: {datetime.now().strftime('%H:%M:%S')} EST")
    print(f"📅 Trading day: {'Yes' if is_trading_day() else 'No'}")
    print(f"🔔 Market hours: {'Yes' if is_market_hours() else 'No'}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=debug)