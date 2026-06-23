# -*- coding: utf-8 -*-
import threading
import time
import random
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from account_database import AccountDatabase
import queue

class ActionType:
    """Типы действий для кампаний"""
    LIKE = "like"
    COMMENT = "comment"
    FOLLOW = "follow"
    MESSAGE = "message"
    POST = "post"
    SHARE = "share"
    WATCH = "watch"
    TAG = "tag"

class CampaignAutomation:
    """Система автоматизации кампаний и массовых действий"""
    
    def __init__(self, db: AccountDatabase = None):
        self.db = db or AccountDatabase()
        self._lock = threading.Lock()
        self._running = False
        self.action_queue = queue.Queue()
        self.worker_threads = []
        
        # Параметры по умолчанию
        self.default_config = {
            'daily_action_limit': 50,
            'action_delay': (5, 15),  # секунды
            'batch_size': 10,
            'max_workers': 5,
            'retry_attempts': 3,
            'retry_delay': 30
        }
    
    def create_campaign(self, campaign_name: str, campaign_type: str, 
                       platform: str, strategy: str, prompt: str = None,
                       config: Dict = None) -> int:
        """Создать новую кампанию"""
        try:
            campaign_data = {
                'campaign_name': campaign_name,
                'campaign_type': campaign_type,  # organic, paid, engagement
                'platform': platform,
                'strategy': strategy,
                'prompt': prompt,
                'status': 'active',
                'start_date': datetime.now().isoformat(),
                'daily_actions_limit': config.get('daily_action_limit') if config else 50,
                'interaction_types': json.dumps([ActionType.LIKE, ActionType.COMMENT, ActionType.FOLLOW])
            }
            
            campaign_id = self.db.create_campaign(campaign_data)
            print(f"[+] Кампания '{campaign_name}' создана с ID {campaign_id}")
            return campaign_id
        except Exception as e:
            print(f"[-] Ошибка создания кампании: {e}")
        return None
    
    def assign_accounts_to_campaign(self, campaign_id: int, 
                                   country: str = None, 
                                   min_trust_score: float = 0.0,
                                   limit: int = None) -> List[int]:
        """Назначить аккаунты на кампанию"""
        try:
            # Получить валидные аккаунты
            if country:
                accounts = self.db.get_accounts_by_country(country, status='valid')
            else:
                accounts = self.db.get_accounts_by_status('valid', limit)
            
            # Фильтр по trust score
            filtered_accounts = [
                acc for acc in accounts 
                if acc.get('trust_score', 0) >= min_trust_score
            ]
            
            account_ids = [acc['id'] for acc in filtered_accounts[:limit] if limit else filtered_accounts]
            
            if self.db.assign_accounts_to_campaign(campaign_id, account_ids):
                print(f"[+] Назначено {len(account_ids)} аккаунтов на кампанию {campaign_id}")
                return account_ids
        except Exception as e:
            print(f"[-] Ошибка назначения аккаунтов: {e}")
        return []
    
    def schedule_action(self, account_id: int, action_type: str, 
                       target_id: str = None, action_data: Dict = None,
                       delay_minutes: int = 0) -> int:
        """Запланировать действие"""
        try:
            action_info = {
                'action_type': action_type,
                'target_id': target_id,
                'data': action_data or {},
                'scheduled_time': datetime.now() + timedelta(minutes=delay_minutes)
            }
            
            action_id = self.db.add_action(account_id, action_type, action_info)
            return action_id
        except Exception as e:
            print(f"[-] Ошибка планирования действия: {e}")
        return None
    
    def execute_like_action(self, account: Dict, target_id: str) -> bool:
        """Выполнить лайк"""
        try:
            account_id = account['id']
            token = account.get('access_token')
            proxy = account.get('proxy_ip')
            
            if not token:
                return False
            
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
            
            # Эмуляция лайка через API
            url = f"https://graph.instagram.com/v18.0/{target_id}/likes"
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.post(url, headers=headers, proxies=proxies, timeout=10)
            
            if response.status_code in [200, 201]:
                # Обновить действие
                self.db.update_account(account_id, {
                    'action_count': account.get('action_count', 0) + 1,
                    'last_action': datetime.now().isoformat()
                })
                return True
            
            return False
        except Exception as e:
            print(f"[-] Ошибка выполнения лайка: {e}")
            return False
    
    def execute_comment_action(self, account: Dict, target_id: str, 
                              comment_text: str = None) -> bool:
        """Выполнить комментарий"""
        try:
            account_id = account['id']
            token = account.get('access_token')
            proxy = account.get('proxy_ip')
            
            if not token or not comment_text:
                return False
            
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
            
            # Эмуляция комментария
            url = f"https://graph.instagram.com/v18.0/{target_id}/comments"
            headers = {'Authorization': f'Bearer {token}'}
            data = {'text': comment_text}
            
            response = requests.post(url, json=data, headers=headers, 
                                    proxies=proxies, timeout=10)
            
            if response.status_code in [200, 201]:
                self.db.update_account(account_id, {
                    'action_count': account.get('action_count', 0) + 1
                })
                return True
            
            return False
        except Exception as e:
            print(f"[-] Ошибка выполнения комментария: {e}")
            return False
    
    def execute_follow_action(self, account: Dict, target_user_id: str) -> bool:
        """Выполнить подписку"""
        try:
            account_id = account['id']
            token = account.get('access_token')
            proxy = account.get('proxy_ip')
            
            if not token:
                return False
            
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
            
            # Эмуляция подписки
            url = f"https://graph.instagram.com/v18.0/me/relationships"
            headers = {'Authorization': f'Bearer {token}'}
            data = {'users': target_user_id}
            
            response = requests.post(url, json=data, headers=headers, 
                                    proxies=proxies, timeout=10)
            
            if response.status_code in [200, 201]:
                self.db.update_account(account_id, {
                    'follower_count': account.get('follower_count', 0) + 1
                })
                return True
            
            return False
        except Exception as e:
            print(f"[-] Ошибка выполнения подписки: {e}")
            return False
    
    def execute_message_action(self, account: Dict, recipient_id: str, 
                              message_text: str) -> bool:
        """Отправить сообщение"""
        try:
            account_id = account['id']
            token = account.get('access_token')
            proxy = account.get('proxy_ip')
            
            if not token or not message_text:
                return False
            
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
            
            # Эмуляция отправки сообщения
            url = f"https://graph.instagram.com/v18.0/me/messages"
            headers = {'Authorization': f'Bearer {token}'}
            data = {
                'recipient_id': recipient_id,
                'message': message_text
            }
            
            response = requests.post(url, json=data, headers=headers, 
                                    proxies=proxies, timeout=10)
            
            if response.status_code in [200, 201]:
                return True
            
            return False
        except Exception as e:
            print(f"[-] Ошибка отправки сообщения: {e}")
            return False
    
    def execute_action(self, account_id: int, action_type: str, 
                      action_data: Dict) -> bool:
        """Выполнить действие"""
        try:
            account = self.db.get_account(account_id)
            if not account:
                return False
            
            if action_type == ActionType.LIKE:
                return self.execute_like_action(account, action_data.get('target_id'))
            
            elif action_type == ActionType.COMMENT:
                return self.execute_comment_action(account, action_data.get('target_id'),
                                                   action_data.get('text'))
            
            elif action_type == ActionType.FOLLOW:
                return self.execute_follow_action(account, action_data.get('target_id'))
            
            elif action_type == ActionType.MESSAGE:
                return self.execute_message_action(account, action_data.get('recipient_id'),
                                                   action_data.get('text'))
            
            return False
        except Exception as e:
            print(f"[-] Ошибка выполнения действия: {e}")
            return False
    
    def worker_thread(self, worker_id: int):
        """Рабочий поток для выполнения действий"""
        print(f"[*] Рабочий {worker_id} запущен")
        
        while self._running:
            try:
                # Получить действие из очереди
                try:
                    action_id, account_id, action_type, action_data = self.action_queue.get(timeout=5)
                except queue.Empty:
                    continue
                
                # Выполнить действие
                success = self.execute_action(account_id, action_type, action_data)
                
                # Обновить статус
                status = 'completed' if success else 'failed'
                self.db.update_action_status(action_id, status, 
                                            'Success' if success else 'Failed')
                
                # Случайная задержка
                delay = random.uniform(5, 15)
                time.sleep(delay)
                
                self.action_queue.task_done()
            
            except Exception as e:
                print(f"[-] Ошибка в рабочем потоке: {e}")
                time.sleep(5)
    
    def start_automation(self, campaign_id: int, num_workers: int = 5):
        """Запустить автоматизацию кампании"""
        try:
            self._running = True
            campaign = self.db.get_campaign(campaign_id)
            
            if not campaign:
                print(f"[-] Кампания {campaign_id} не найдена")
                return False
            
            print(f"[+] Запуск кампании '{campaign['campaign_name']}'")
            
            # Получить аккаунты кампании
            accounts = self.db.get_campaign_accounts(campaign_id)
            print(f"[+] Найдено {len(accounts)} аккаунтов для кампании")
            
            # Запустить рабочие потоки
            for i in range(num_workers):
                thread = threading.Thread(target=self.worker_thread, args=(i,), daemon=True)
                thread.start()
                self.worker_threads.append(thread)
            
            # Заполнить очередь действиями
            for account in accounts:
                # Получить действия для аккаунта
                # (в реальном приложении они должны быть загружены из БД)
                pass
            
            return True
        except Exception as e:
            print(f"[-] Ошибка запуска автоматизации: {e}")
        return False
    
    def stop_automation(self):
        """Остановить автоматизацию"""
        self._running = False
        print("[*] Остановка автоматизации...")
        
        # Ждать завершения рабочих потоков
        for thread in self.worker_threads:
            thread.join(timeout=5)
        
        self.worker_threads.clear()
        print("[+] Автоматизация остановлена")
    
    def get_campaign_stats(self, campaign_id: int) -> Dict:
        """Получить статистику кампании"""
        try:
            campaign = self.db.get_campaign(campaign_id)
            accounts = self.db.get_campaign_accounts(campaign_id)
            
            total_actions = sum(acc.get('action_count', 0) for acc in accounts)
            total_likes = sum(acc.get('post_count', 0) for acc in accounts)
            
            return {
                'campaign_name': campaign.get('campaign_name'),
                'status': campaign.get('status'),
                'total_accounts': len(accounts),
                'total_actions': total_actions,
                'total_likes': total_likes,
                'created_at': campaign.get('created_at'),
                'accounts': accounts
            }
        except Exception as e:
            print(f"[-] Ошибка получения статистики: {e}")
        return {}


class InteractionEngine:
    """Двигатель для органических взаимодействий между аккаунтами"""
    
    def __init__(self, db: AccountDatabase = None):
        self.db = db or AccountDatabase()
        self.automation = CampaignAutomation(db)
    
    def create_interaction_network(self, campaign_id: int, interaction_type: str = 'friendship'):
        """Создать сеть взаимодействий между аккаунтами"""
        try:
            accounts = self.db.get_campaign_accounts(campaign_id)
            
            if len(accounts) < 2:
                print("[-] Недостаточно аккаунтов для создания сети")
                return False
            
            print(f"[+] Создание сети {len(accounts)} аккаунтов...")
            
            # Создать связи между аккаунтами
            for i, account in enumerate(accounts):
                # Выбрать случайные целевые аккаунты
                targets = random.sample(accounts, min(5, len(accounts) - 1))
                
                for target in targets:
                    if target['id'] != account['id']:
                        # Добавить в БД
                        with sqlite3.connect(self.db.db_path) as conn:
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT OR IGNORE INTO account_relations 
                                (account_id, target_account_id, relation_type, status)
                                VALUES (?, ?, ?, ?)
                            ''', (account['id'], target['id'], interaction_type, 'pending'))
                            conn.commit()
            
            print(f"[+] Сеть создана успешно")
            return True
        except Exception as e:
            print(f"[-] Ошибка создания сети: {e}")
        return False
    
    def execute_network_interactions(self, campaign_id: int, 
                                    action_type: str = ActionType.LIKE):
        """Выполнить взаимодействия в сети"""
        try:
            accounts = self.db.get_campaign_accounts(campaign_id)
            
            for account in accounts:
                # Получить целевые аккаунты
                with sqlite3.connect(self.db.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT * FROM account_relations 
                        WHERE account_id = ? AND status = ?
                    ''', (account['id'], 'pending'))
                    
                    relations = cursor.fetchall()
                    
                    for relation in relations:
                        target_id = relation['target_account_id']
                        
                        # Выполнить действие
                        action_data = {
                            'target_id': target_id,
                            'action_type': action_type
                        }
                        
                        success = self.automation.execute_action(
                            account['id'], 
                            action_type, 
                            action_data
                        )
                        
                        # Обновить статус
                        if success:
                            cursor.execute('''
                                UPDATE account_relations 
                                SET status = ? 
                                WHERE id = ?
                            ''', ('completed', relation['id']))
                
                conn.commit()
            
            print(f"[+] Взаимодействия выполнены")
            return True
        except Exception as e:
            print(f"[-] Ошибка выполнения взаимодействий: {e}")
        return False
    
    def get_interaction_stats(self, campaign_id: int) -> Dict:
        """Получить статистику взаимодействий"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) as total, status
                    FROM account_relations
                    WHERE campaign_assigned_id = ?
                    GROUP BY status
                ''', (campaign_id,))
                
                results = cursor.fetchall()
                return {row[1]: row[0] for row in results}
        except Exception as e:
            print(f"[-] Ошибка получения статистики: {e}")
        return {}


# Импорт sqlite3 для использования в модуле
import sqlite3
