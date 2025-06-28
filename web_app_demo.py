"""
Demo Web Interface for Structural Levels Management V2
Simplified version for UI preview without database dependencies.
"""

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime, date, time, timedelta
import secrets
from dotenv import load_dotenv
import pytz
from typing import Dict, Any, List

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# Set timezone
EST = pytz.timezone('America/New_York')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Simple user class for authentication
class User(UserMixin):
    def __init__(self, username):
        self.id = username

# Store user credentials securely
USERS = {
    os.environ.get('WEB_USERNAME', 'admin'): generate_password_hash(os.environ.get('WEB_PASSWORD', 'password'))
}

@login_manager.user_loader
def load_user(username):
    if username in USERS:
        return User(username)
    return None

def get_current_est_time():
    """Get current time in EST."""
    return datetime.now(EST)

def is_trading_day():
    """Check if today is a trading day."""
    current_time = get_current_est_time()
    return current_time.weekday() < 5  # Monday = 0, Friday = 4

def is_market_hours():
    """Check if we're in market hours (9:00 AM - 4:00 PM EST)."""
    current_time = get_current_est_time()
    market_start = time(9, 0)
    market_end = time(16, 0)
    return market_start <= current_time.time() <= market_end

@app.route('/')
@app.route('/levels')
@login_required
def levels_dashboard():
    """Main levels management dashboard with demo data."""
    current_time = get_current_est_time()
    today = current_time.date()
    
    # Demo data for UI preview
    es_status = {
        'csv_complete': True, 
        'manual_complete': False, 
        'overall_complete': False, 
        'total_levels': 28,
        'missing_csv': [],
        'missing_manual': ['pivot', 'pivot_high', 'pivot_low', 'pivot_ba_high', 'pivot_ba_low']
    }
    
    nq_status = {
        'csv_complete': False, 
        'manual_complete': True, 
        'overall_complete': False, 
        'total_levels': 15,
        'missing_csv': ['mgi_onh', 'mgi_onl', 'balance_area_high', 'balance_area_low'],
        'missing_manual': []
    }
    
    # Demo levels data
    es_levels = {
        'mgi_wk_op': 5825.75,
        'mgi_pm_vah': 5890.25,
        'mgi_pm_val': 5780.50,
        'mgi_pw_vah': 5870.00,
        'mgi_pw_val': 5790.25,
        'mgi_onh': 5845.75,
        'mgi_onl': 5812.25,
        'mgi_pdh': 5855.50,
        'mgi_pdl': 5805.75,
        'balance_area_high': 5880.00,
        'balance_area_low': 5800.00,
        'pivot': 5830.25,
        'pivot_high': 5850.75,
        'pivot_low': 5810.50
    }
    
    nq_levels = {
        'mgi_wk_op': 18250.75,
        'mgi_pm_vah': 18420.25,
        'mgi_pm_val': 18180.50,
        'mgi_pw_vah': 18390.00,
        'mgi_pw_val': 18200.25,
        'mgi_pdh': 18355.50,
        'mgi_pdl': 18205.75,
        'pivot': 18275.25,
        'pivot_high': 18320.75,
        'pivot_low': 18230.50,
        'pivot_ba_high': 18350.00,
        'pivot_ba_low': 18200.00
    }
    
    # Check if it's time to enter pivot levels (between 9:30-10:00 AM EST)
    pivot_entry_time = time(9, 30) <= current_time.time() <= time(22, 0)  # Extended for demo
    
    return render_template('levels_v2.html',
                         current_time=current_time,
                         today=today,
                         es_status=es_status,
                         nq_status=nq_status,
                         es_levels=es_levels,
                         nq_levels=nq_levels,
                         pivot_entry_time=pivot_entry_time,
                         is_trading_day=is_trading_day(),
                         is_market_hours=is_market_hours())

@app.route('/api/v2/manual-levels', methods=['POST'])
@login_required
def add_manual_levels():
    """Add manual pivot levels (demo)."""
    try:
        data = request.json
        symbol = data.get('symbol', '').upper()
        trading_date_str = data.get('trading_date')
        levels_data = data.get('levels', {})
        
        # Validate inputs
        if not symbol or symbol not in ['ES', 'NQ']:
            return jsonify({'error': 'Invalid symbol'}), 400
        
        if not levels_data:
            return jsonify({'error': 'No levels provided'}), 400
        
        # Simulate successful addition
        return jsonify({
            'success': True,
            'imported_count': len(levels_data),
            'message': f'Demo: Successfully added {len(levels_data)} {symbol} levels'
        })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/levels/<symbol>/<date_str>', methods=['GET'])
@login_required
def get_levels_for_date(symbol, date_str):
    """Get all levels for a specific symbol and date (demo)."""
    try:
        symbol = symbol.upper()
        if symbol not in ['ES', 'NQ']:
            return jsonify({'error': 'Invalid symbol'}), 400
        
        # Demo levels
        demo_levels = {
            'ES': {
                'mgi_wk_op': 5825.75,
                'mgi_pm_vah': 5890.25,
                'mgi_pm_val': 5780.50,
                'pivot': 5830.25,
                'pivot_high': 5850.75,
                'pivot_low': 5810.50
            },
            'NQ': {
                'mgi_wk_op': 18250.75,
                'mgi_pm_vah': 18420.25,
                'mgi_pm_val': 18180.50,
                'pivot': 18275.25,
                'pivot_high': 18320.75,
                'pivot_low': 18230.50
            }
        }
        
        return jsonify({
            'symbol': symbol,
            'trading_date': date_str,
            'levels': demo_levels.get(symbol, {})
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/completeness/<symbol>', methods=['GET'])
@login_required
def get_completeness_status(symbol):
    """Get completeness status for a symbol (demo)."""
    try:
        symbol = symbol.upper()
        if symbol not in ['ES', 'NQ']:
            return jsonify({'error': 'Invalid symbol'}), 400
        
        # Demo status
        demo_status = {
            'ES': {
                'csv_complete': True,
                'manual_complete': False,
                'overall_complete': False,
                'total_levels': 28,
                'missing_csv': [],
                'missing_manual': ['pivot', 'pivot_high', 'pivot_low']
            },
            'NQ': {
                'csv_complete': False,
                'manual_complete': True,
                'overall_complete': False,
                'total_levels': 15,
                'missing_csv': ['mgi_onh', 'mgi_onl'],
                'missing_manual': []
            }
        }
        
        return jsonify(demo_status.get(symbol, {}))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/csv-import', methods=['POST'])
@login_required
def manual_csv_import():
    """Manually trigger CSV import from watch folder (demo)."""
    try:
        # Simulate CSV import
        return jsonify({
            'successful_count': 2,
            'failed_count': 0,
            'processed_count': 2,
            'message': 'Demo: Processed ES_levels.csv and NQ_levels.csv successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/validate-levels', methods=['POST'])
@login_required
def validate_levels():
    """Validate level hierarchy for a symbol and date (demo)."""
    try:
        data = request.json
        symbol = data.get('symbol', '').upper()
        
        if not symbol or symbol not in ['ES', 'NQ']:
            return jsonify({'error': 'Invalid symbol'}), 400
        
        # Demo validation
        return jsonify({
            'is_valid': True,
            'errors': [],
            'warnings': ['Demo: Some levels may need adjustment for optimal trading']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        flash('Invalid username or password', 'danger')
    
    return render_template('login_simple.html')

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
    # Set up logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("🚀 xFGv2 Demo Web Interface Starting")
    print("="*60)
    print(f"📊 Demo credentials: admin / password")
    print(f"🌐 URL: http://localhost:5002")
    print(f"📁 Working from: xfgv2/ folder")
    print(f"⏰ Current time: {get_current_est_time().strftime('%H:%M:%S EST')}")
    print(f"📅 Trading day: {'Yes' if is_trading_day() else 'No'}")
    print(f"🔔 Market hours: {'Yes' if is_market_hours() else 'No'}")
    print("="*60)
    
    # Run the app
    port = int(os.environ.get('PORT', 5002))
    app.run(debug=True, host='0.0.0.0', port=port)