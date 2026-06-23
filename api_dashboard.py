# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
import threading
from account_database import AccountDatabase, AccountStatus
from campaign_automation import CampaignAutomation, InteractionEngine, ActionType
from proxy_manager import ProxyManager
from profile_generator import ProfileGenerator
from multi_account_manager import MultiAccountManager
import io
from openpyxl import load_workbook

app = Flask(__name__)
CORS(app)

# Инициализация компонентов
db = AccountDatabase()
automation = CampaignAutomation(db)
interaction_engine = InteractionEngine(db)
proxy_mgr = ProxyManager()
profile_gen = ProfileGenerator()

# Глобальные переменные для отслеживания процессов
running_campaigns = {}
account_creation_progress = {}

# ==================== DASHBOARD ROUTES ====================

@app.route('/')
def dashboard():
    """Главная страница дашборда"""
    stats = db.get_stats()
    return {
        'total_accounts': stats.get('total_accounts', 0),
        'valid_accounts': stats.get('valid_accounts', 0),
        'active_campaigns': stats.get('active_campaigns', 0),
        'pending_actions': stats.get('pending_actions', 0),
        'by_country': stats.get('by_country', {})
    }

# ==================== ACCOUNT MANAGEMENT ====================

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """Получить список аккаунтов с фильтрами"""
    try:
        status = request.args.get('status')
        country = request.args.get('country')
        limit = int(request.args.get('limit', 100))
        
        if status:
            accounts = db.get_accounts_by_status(status, limit)
        elif country:
            accounts = db.get_accounts_by_country(country)
        else:
            accounts = []
        
        return jsonify({
            'success': True,
            'count': len(accounts),
            'accounts': [
                {
                    'id': acc.get('id'),
                    'email': acc.get('email'),
                    'username': acc.get('username'),
                    'status': acc.get('status'),
                    'country': acc.get('country'),
                    'trust_score': acc.get('trust_score'),
                    'action_count': acc.get('action_count'),
                    'friend_count': acc.get('friend_count'),
                    'created_at': acc.get('created_at')
                }
                for acc in accounts
            ]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/accounts/<int:account_id>', methods=['GET'])
def get_account(account_id):
    """Получить детали аккаунта"""
    try:
        account = db.get_account(account_id)
        if not account:
            return jsonify({'success': False, 'error': 'Account not found'}), 404
        
        return jsonify({
            'success': True,
            'account': {
                'id': account.get('id'),
                'email': account.get('email'),
                'username': account.get('username'),
                'first_name': account.get('first_name'),
                'last_name': account.get('last_name'),
                'status': account.get('status'),
                'country': account.get('country'),
                'city': account.get('city'),
                'job_title': account.get('job_title'),
                'job_company': account.get('job_company'),
                'education_university': account.get('education_university'),
                'trust_score': account.get('trust_score'),
                'action_count': account.get('action_count'),
                'friend_count': account.get('friend_count'),
                'follower_count': account.get('follower_count'),
                'proxy_ip': account.get('proxy_ip'),
                'business_manager_id': account.get('business_manager_id'),
                'created_at': account.get('created_at'),
                'last_login': account.get('last_login')
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/accounts/<int:account_id>', methods=['PUT'])
def update_account(account_id):
    """Обновить аккаунт"""
    try:
        data = request.json
        if db.update_account(account_id, data):
            return jsonify({'success': True, 'message': 'Account updated'})
        return jsonify({'success': False, 'error': 'Update failed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/accounts/status/<status>', methods=['GET'])
def get_accounts_by_status(status):
    """Получить аккаунты по статусу"""
    try:
        limit = int(request.args.get('limit', 100))
        accounts = db.get_accounts_by_status(status, limit)
        
        return jsonify({
            'success': True,
            'status': status,
            'count': len(accounts),
            'accounts': [
                {'id': acc['id'], 'email': acc['email'], 'username': acc['username']}
                for acc in accounts
            ]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ==================== ACCOUNT CREATION ====================

@app.route('/api/create-accounts', methods=['POST'])
def create_accounts():
    """Создать новые аккаунты"""
    try:
        data = request.json
        count = data.get('count', 1)
        geo = data.get('geo', 'US')
        platform = data.get('platform', 'facebook')
        threads = data.get('threads', 5)
        use_proxy = data.get('use_proxy', True)
        
        # Создать менеджер аккаунтов
        manager = MultiAccountManager(geo, count)
        
        # Обновить прокси если нужно
        if use_proxy:
            proxy_mgr.refresh_proxies(geo)
        
        # Запустить создание в отдельном потоке
        progress_id = f"creation_{datetime.now().timestamp()}"
        account_creation_progress[progress_id] = {
            'status': 'running',
            'count': count,
            'created': 0,
            'valid': 0,
            'failed': 0,
            'geo': geo
        }
        
        def creation_worker():
            for i in range(count):
                try:
                    # Генерировать профиль
                    profile = profile_gen.generate_profile(geo, 'M')
                    email = f"{profile['first_name'].lower()}.{profile['last_name'].lower()}@mail.tm"
                    
                    account_data = {
                        'platform': platform,
                        'email': email,
                        'email_password': 'Pass123!',
                        'account_password': 'Pass123!',
                        'first_name': profile['first_name'],
                        'last_name': profile['last_name'],
                        'birthday': profile['birthday'].strftime('%Y-%m-%d'),
                        'gender': 'M',
                        'country': geo,
                        'city': profile['city'],
                        'job_title': profile['job'],
                        'education_university': profile['university'],
                        'status': 'valid',
                        'trust_score': 0.5,
                        'proxy_ip': proxy_mgr.get_proxy(geo) if use_proxy else None
                    }
                    
                    manager.add_account(account_data)
                    account_creation_progress[progress_id]['created'] += 1
                    account_creation_progress[progress_id]['valid'] += 1
                except Exception as e:
                    account_creation_progress[progress_id]['failed'] += 1
        
        thread = threading.Thread(target=creation_worker)
        thread.start()
        
        return jsonify({
            'success': True,
            'progress_id': progress_id,
            'message': f'Creating {count} accounts'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/creation-progress/<progress_id>', methods=['GET'])
def get_creation_progress(progress_id):
    """Получить прогресс создания аккаунтов"""
    try:
        progress = account_creation_progress.get(progress_id, {})
        return jsonify({
            'success': True,
            'progress': progress
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ==================== CAMPAIGN MANAGEMENT ====================

@app.route('/api/campaigns', methods=['GET'])
def get_campaigns():
    """Получить список кампаний"""
    try:
        status = request.args.get('status', 'active')
        with db._lock:
            import sqlite3
            with sqlite3.connect(db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM campaigns WHERE status = ? ORDER BY created_at DESC",
                    (status,)
                )
                campaigns = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'count': len(campaigns),
            'campaigns': campaigns
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/campaigns', methods=['POST'])
def create_campaign():
    """Создать новую кампанию"""
    try:
        data = request.json
        campaign_id = automation.create_campaign(
            campaign_name=data.get('campaign_name'),
            campaign_type=data.get('campaign_type', 'organic'),
            platform=data.get('platform', 'instagram'),
            strategy=data.get('strategy', 'engagement'),
            prompt=data.get('prompt'),
            config=data.get('config', {})
        )
        
        return jsonify({
            'success': True,
            'campaign_id': campaign_id,
            'message': 'Campaign created'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/campaigns/<int:campaign_id>/accounts', methods=['POST'])
def assign_accounts_to_campaign(campaign_id):
    """Назначить аккаунты на кампанию"""
    try:
        data = request.json
        account_ids = automation.assign_accounts_to_campaign(
            campaign_id,
            country=data.get('country'),
            min_trust_score=data.get('min_trust_score', 0.0),
            limit=data.get('limit')
        )
        
        return jsonify({
            'success': True,
            'assigned_count': len(account_ids),
            'account_ids': account_ids
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/campaigns/<int:campaign_id>/stats', methods=['GET'])
def get_campaign_stats(campaign_id):
    """Получить статистику кампании"""
    try:
        stats = automation.get_campaign_stats(campaign_id)
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/campaigns/<int:campaign_id>/start', methods=['POST'])
def start_campaign(campaign_id):
    """Запустить кампанию"""
    try:
        num_workers = request.json.get('num_workers', 5)
        
        if automation.start_automation(campaign_id, num_workers):
            running_campaigns[campaign_id] = {
                'status': 'running',
                'started_at': datetime.now().isoformat(),
                'workers': num_workers
            }
            
            return jsonify({
                'success': True,
                'message': f'Campaign {campaign_id} started'
            })
        return jsonify({'success': False, 'error': 'Failed to start campaign'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/campaigns/<int:campaign_id>/stop', methods=['POST'])
def stop_campaign(campaign_id):
    """Остановить кампанию"""
    try:
        automation.stop_automation()
        if campaign_id in running_campaigns:
            del running_campaigns[campaign_id]
        
        return jsonify({
            'success': True,
            'message': f'Campaign {campaign_id} stopped'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ==================== INTERACTIONS ====================

@app.route('/api/campaigns/<int:campaign_id>/interactions/create', methods=['POST'])
def create_interaction_network(campaign_id):
    """Создать сеть взаимодействий"""
    try:
        interaction_type = request.json.get('interaction_type', 'friendship')
        
        if interaction_engine.create_interaction_network(campaign_id, interaction_type):
            return jsonify({
                'success': True,
                'message': 'Interaction network created'
            })
        return jsonify({'success': False, 'error': 'Failed to create network'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/campaigns/<int:campaign_id>/interactions/execute', methods=['POST'])
def execute_interactions(campaign_id):
    """Выполнить взаимодействия"""
    try:
        action_type = request.json.get('action_type', ActionType.LIKE)
        
        if interaction_engine.execute_network_interactions(campaign_id, action_type):
            return jsonify({
                'success': True,
                'message': 'Interactions executed'
            })
        return jsonify({'success': False, 'error': 'Failed to execute'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/campaigns/<int:campaign_id>/interactions/stats', methods=['GET'])
def get_interaction_stats(campaign_id):
    """Получить статистику взаимодействий"""
    try:
        stats = interaction_engine.get_interaction_stats(campaign_id)
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ==================== ACTIONS ====================

@app.route('/api/actions/schedule', methods=['POST'])
def schedule_action():
    """Запланировать действие"""
    try:
        data = request.json
        action_id = automation.schedule_action(
            account_id=data.get('account_id'),
            action_type=data.get('action_type'),
            target_id=data.get('target_id'),
            action_data=data.get('action_data', {}),
            delay_minutes=data.get('delay_minutes', 0)
        )
        
        return jsonify({
            'success': True,
            'action_id': action_id,
            'message': 'Action scheduled'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/actions/execute', methods=['POST'])
def execute_action():
    """Выполнить действие немедленно"""
    try:
        data = request.json
        success = automation.execute_action(
            account_id=data.get('account_id'),
            action_type=data.get('action_type'),
            action_data=data.get('action_data', {})
        )
        
        return jsonify({
            'success': success,
            'message': 'Action executed' if success else 'Action failed'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ==================== PROXY MANAGEMENT ====================

@app.route('/api/proxies/refresh', methods=['POST'])
def refresh_proxies():
    """Обновить прокси"""
    try:
        data = request.json
        geo = data.get('geo', 'US')
        limit = data.get('limit', 300)
        
        def refresh_worker():
            proxy_mgr.refresh_proxies(geo, limit)
        
        thread = threading.Thread(target=refresh_worker)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Refreshing proxies for {geo}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/proxies/stats', methods=['GET'])
def get_proxy_stats():
    """Получить статистику прокси"""
    try:
        stats = proxy_mgr.db.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ==================== REPORTS & EXPORTS ====================

@app.route('/api/export/accounts', methods=['GET'])
def export_accounts():
    """Экспортировать аккаунты"""
    try:
        format_type = request.args.get('format', 'xlsx')
        status = request.args.get('status', 'valid')
        
        accounts = db.get_accounts_by_status(status)
        
        if format_type == 'json':
            return jsonify({
                'success': True,
                'accounts': accounts
            })
        
        elif format_type == 'csv':
            import csv
            output = io.StringIO()
            if accounts:
                writer = csv.DictWriter(output, fieldnames=accounts[0].keys())
                writer.writeheader()
                writer.writerows(accounts)
            
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'accounts_{status}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        
        elif format_type == 'txt':
            output = '\n'.join([
                f"{acc['email']}:{acc.get('account_password', 'N/A')}"
                for acc in accounts
            ])
            
            return send_file(
                io.BytesIO(output.encode()),
                mimetype='text/plain',
                as_attachment=True,
                download_name=f'accounts_{status}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
            )
        
        return jsonify({'success': False, 'error': 'Invalid format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Получить общую статистику"""
    try:
        stats = db.get_stats()
        proxy_stats = proxy_mgr.db.get_stats()
        
        return jsonify({
            'success': True,
            'accounts': stats,
            'proxies': proxy_stats,
            'running_campaigns': len(running_campaigns),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ==================== ERROR HANDLING ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'success': False, 'error': 'Server error'}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 FACEBOOK MULTI-ACCOUNT AUTOMATION DASHBOARD")
    print("="*60)
    print("📊 API Server running on http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
