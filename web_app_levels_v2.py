"""
Web Interface for Structural Levels Management V2
Provides manual input for pivot levels and monitoring of CSV imports.
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

# Import our new levels manager
from src.structural_levels_v2 import StructuralLevelsManagerV2, LevelValidation
from src.csv_file_monitor import CSVFileMonitor, MonitorConfig

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# Set timezone
EST = pytz.timezone('America/New_York')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Initialize levels manager with error handling
try:
    levels_manager = StructuralLevelsManagerV2(DATABASE_URL)
    # Try to create tables if they don't exist
    levels_manager.create_tables()
except Exception as e:
    print(f"Warning: Could not initialize database: {e}")
    levels_manager = None

# Initialize CSV monitor with error handling
try:
    monitor_config = MonitorConfig(
        database_url=DATABASE_URL,
        watch_folder=os.environ.get('CSV_WATCH_FOLDER', '/tmp/csv_watch'),
        allowed_symbols=['ES', 'NQ']
    )
    csv_monitor = CSVFileMonitor(monitor_config) if levels_manager else None
except Exception as e:
    print(f"Warning: Could not initialize CSV monitor: {e}")
    csv_monitor = None

# Simple user class for authentication
class User(UserMixin):
    def __init__(self, username):
        self.id = username

# Store user credentials securely
USERS = {
    os.environ.get('WEB_USERNAME', 'admin'): generate_password_hash(os.environ.get('WEB_PASSWORD', 'changeme'))
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
    """Main levels management dashboard."""
    current_time = get_current_est_time()
    today = current_time.date()
    
    # Handle case where database is not available
    if levels_manager is None:
        # Return demo data for UI preview
        es_status = {'csv_complete': False, 'manual_complete': False, 'overall_complete': False, 'total_levels': 0}
        nq_status = {'csv_complete': False, 'manual_complete': False, 'overall_complete': False, 'total_levels': 0}
        es_levels = {}
        nq_levels = {}
    else:
        try:
            # Get completeness status for both symbols
            es_status = levels_manager.get_daily_completeness_status('ES', today)
            nq_status = levels_manager.get_daily_completeness_status('NQ', today)
            
            # Get current levels for display
            es_levels = levels_manager.get_levels_for_date('ES', today)
            nq_levels = levels_manager.get_levels_for_date('NQ', today)
        except Exception as e:
            print(f"Error getting data: {e}")
            # Return demo data for UI preview
            es_status = {'csv_complete': False, 'manual_complete': False, 'overall_complete': False, 'total_levels': 0}
            nq_status = {'csv_complete': False, 'manual_complete': False, 'overall_complete': False, 'total_levels': 0}
            es_levels = {}
            nq_levels = {}
    
    # Check if it's time to enter pivot levels (between 9:30-10:00 AM EST)
    pivot_entry_time = time(9, 30) <= current_time.time() <= time(10, 0)
    
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
    """Add manual pivot levels."""
    try:
        data = request.json
        symbol = data.get('symbol', '').upper()
        trading_date_str = data.get('trading_date')
        levels_data = data.get('levels', {})
        
        # Validate inputs
        if not symbol or symbol not in ['ES', 'NQ']:
            return jsonify({'error': 'Invalid symbol'}), 400
        
        if not trading_date_str:
            trading_date = date.today()
        else:
            trading_date = date.fromisoformat(trading_date_str)
        
        if not levels_data:
            return jsonify({'error': 'No levels provided'}), 400
        
        # Validate level types
        allowed_types = {'pivot', 'pivot_high', 'pivot_low', 'pivot_ba_high', 'pivot_ba_low', 'weekly_pivot'}
        invalid_types = set(levels_data.keys()) - allowed_types
        if invalid_types:
            return jsonify({'error': f'Invalid level types: {list(invalid_types)}'}), 400
        
        # Validate price values
        for level_type, price in levels_data.items():
            try:
                levels_data[level_type] = float(price)
            except (ValueError, TypeError):
                return jsonify({'error': f'Invalid price for {level_type}: {price}'}), 400
        
        # Add levels to database
        result = levels_manager.add_manual_levels(
            symbol=symbol,
            trading_date=trading_date,
            levels=levels_data,
            user=current_user.id
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'imported_count': result['imported_count'],
                'validation': result.get('validation', {}).__dict__ if hasattr(result.get('validation', {}), '__dict__') else result.get('validation', {})
            })
        else:
            return jsonify({'error': result.get('error', 'Unknown error')}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/levels/<symbol>/<date_str>', methods=['GET'])
@login_required
def get_levels_for_date(symbol, date_str):
    """Get all levels for a specific symbol and date."""
    try:
        symbol = symbol.upper()
        if symbol not in ['ES', 'NQ']:
            return jsonify({'error': 'Invalid symbol'}), 400
        
        trading_date = date.fromisoformat(date_str)
        levels = levels_manager.get_levels_for_date(symbol, trading_date)
        
        return jsonify({
            'symbol': symbol,
            'trading_date': date_str,
            'levels': levels
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/completeness/<symbol>', methods=['GET'])
@login_required
def get_completeness_status(symbol):
    """Get completeness status for a symbol."""
    try:
        symbol = symbol.upper()
        if symbol not in ['ES', 'NQ']:
            return jsonify({'error': 'Invalid symbol'}), 400
        
        date_str = request.args.get('date')
        if date_str:
            trading_date = date.fromisoformat(date_str)
        else:
            trading_date = date.today()
        
        status = levels_manager.get_daily_completeness_status(symbol, trading_date)
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/csv-import', methods=['POST'])
@login_required
def manual_csv_import():
    """Manually trigger CSV import from watch folder."""
    try:
        result = csv_monitor.manual_process_folder()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/validate-levels', methods=['POST'])
@login_required
def validate_levels():
    """Validate level hierarchy for a symbol and date."""
    try:
        data = request.json
        symbol = data.get('symbol', '').upper()
        trading_date_str = data.get('trading_date')
        
        if not symbol or symbol not in ['ES', 'NQ']:
            return jsonify({'error': 'Invalid symbol'}), 400
        
        if not trading_date_str:
            trading_date = date.today()
        else:
            trading_date = date.fromisoformat(trading_date_str)
        
        validation = levels_manager.validate_level_hierarchy(symbol, trading_date)
        
        return jsonify({
            'is_valid': validation.is_valid,
            'errors': validation.errors,
            'warnings': validation.warnings
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/nearby-levels', methods=['GET'])
@login_required
def get_nearby_levels():
    """Get levels near a specific price."""
    try:
        symbol = request.args.get('symbol', '').upper()
        price = float(request.args.get('price', 0))
        range_points = float(request.args.get('range', 5.0))
        date_str = request.args.get('date')
        
        if not symbol or symbol not in ['ES', 'NQ']:
            return jsonify({'error': 'Invalid symbol'}), 400
        
        if price <= 0:
            return jsonify({'error': 'Invalid price'}), 400
        
        if date_str:
            trading_date = date.fromisoformat(date_str)
        else:
            trading_date = date.today()
        
        nearby_levels = levels_manager.get_nearby_levels(
            symbol=symbol,
            price=price,
            range_points=range_points,
            trading_date=trading_date
        )
        
        return jsonify({
            'symbol': symbol,
            'reference_price': price,
            'range_points': range_points,
            'nearby_levels': nearby_levels
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/monitor')
@login_required
def monitor_dashboard():
    """CSV monitoring dashboard."""
    current_time = get_current_est_time()
    
    # Get recent import activity (last 7 days)
    # This would require adding a logging table to track imports
    # For now, just show folder status
    
    watch_folder_exists = os.path.exists(monitor_config.watch_folder)
    csv_files_count = 0
    
    if watch_folder_exists:
        from pathlib import Path
        csv_files = list(Path(monitor_config.watch_folder).glob("*.csv"))
        csv_files_count = len(csv_files)
    
    return render_template('monitor_v2.html',
                         current_time=current_time,
                         watch_folder=monitor_config.watch_folder,
                         watch_folder_exists=watch_folder_exists,
                         csv_files_count=csv_files_count,
                         is_trading_day=is_trading_day())

@app.route('/api/v2/folder-status', methods=['GET'])
@login_required
def get_folder_status():
    """Get status of CSV watch folder."""
    try:
        from pathlib import Path
        
        watch_path = Path(monitor_config.watch_folder)
        processed_path = watch_path / "processed"
        error_path = watch_path / "errors"
        
        status = {
            'watch_folder_exists': watch_path.exists(),
            'csv_files_count': len(list(watch_path.glob("*.csv"))) if watch_path.exists() else 0,
            'processed_files_count': len(list(processed_path.glob("*"))) if processed_path.exists() else 0,
            'error_files_count': len(list(error_path.glob("*"))) if error_path.exists() else 0,
            'folder_path': str(watch_path)
        }
        
        # Get file details
        if watch_path.exists():
            csv_files = []
            for csv_file in watch_path.glob("*.csv"):
                csv_files.append({
                    'name': csv_file.name,
                    'size': csv_file.stat().st_size,
                    'modified': datetime.fromtimestamp(csv_file.stat().st_mtime).isoformat()
                })
            status['csv_files'] = csv_files
        
        return jsonify(status)
        
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

# Template filters
@app.template_filter('currency')
def currency_filter(value):
    """Format currency."""
    if value is None:
        return 'N/A'
    return f"${value:,.2f}"

@app.template_filter('price')
def price_filter(value):
    """Format price."""
    if value is None:
        return 'N/A'
    return f"{value:.2f}"

if __name__ == '__main__':
    # Set up logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the app
    port = int(os.environ.get('PORT', 5002))
    app.run(debug=True, host='0.0.0.0', port=port)