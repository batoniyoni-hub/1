# -*- coding: utf-8 -*-
"""
Campaign Automation Module
Автоматизация кампаний и управление действиями аккаунтов
"""

from enum import Enum
from datetime import datetime, timedelta
import uuid
import sqlite3
from typing import Dict, List, Optional


class ActionType(Enum):
    """Типы действий"""
    LIKE = "like"
    COMMENT = "comment"
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    MESSAGE = "message"
    POST = "post"
    SHARE = "share"
    REACT = "react"


class CampaignAutomation:
    """Класс для управления автоматизацией кампаний"""
    
    def __init__(self, db):
        self.db = db
        self.running_campaigns = {}
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Убедиться, что таблицы существуют"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()

                # Таблица кампаний принадлежит AccountDatabase; убедимся, что
                # он уже её создал, и домигрируем колонку `config` для старых БД,
                # где кампании были созданы старой версией этой таблицы.
                if hasattr(self.db, 'init_database'):
                    self.db.init_database()

                cursor.execute("PRAGMA table_info(campaigns)")
                existing_cols = {row[1] for row in cursor.fetchall()}
                if 'config' not in existing_cols:
                    cursor.execute("ALTER TABLE campaigns ADD COLUMN config TEXT")

                # Таблица назначений аккаунтов
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS campaign_accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        campaign_id INTEGER,
                        account_id INTEGER,
                        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
                    )
                """)
                
                # Таблица действий
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scheduled_actions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER,
                        campaign_id INTEGER,
                        action_type TEXT,
                        target_id TEXT,
                        action_data TEXT,
                        scheduled_at TIMESTAMP,
                        executed_at TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
        except Exception as e:
            print(f"[-] Error creating tables: {e}")
    
    def create_campaign(self, campaign_name, campaign_type='organic', 
                       platform='instagram', strategy='engagement', 
                       prompt=None, config=None):
        """Создать новую кампанию"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO campaigns 
                    (campaign_name, campaign_type, platform, strategy, prompt, config)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (campaign_name, campaign_type, platform, strategy, prompt, str(config or {})))
                conn.commit()
                campaign_id = cursor.lastrowid
                
                self.running_campaigns[campaign_id] = {
                    'name': campaign_name,
                    'status': 'created',
                    'accounts': [],
                    'actions_count': 0
                }
                
                return campaign_id
        except Exception as e:
            print(f"[-] Error creating campaign: {e}")
            return None
    
    def assign_accounts_to_campaign(self, campaign_id, country=None, 
                                   limit=None, min_trust_score=0.0):
        """Назначить аккаунты на кампанию"""
        try:
            accounts = self.db.get_accounts_by_country(country, limit)
            account_ids = []
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                for account in accounts:
                    if account.get('trust_score', 0) >= min_trust_score:
                        account_id = account.get('id')
                        cursor.execute("""
                            INSERT INTO campaign_accounts (campaign_id, account_id)
                            VALUES (?, ?)
                        """, (campaign_id, account_id))
                        account_ids.append(account_id)
                
                conn.commit()
            
            if campaign_id in self.running_campaigns:
                self.running_campaigns[campaign_id]['accounts'] = account_ids
            
            return account_ids
        except Exception as e:
            print(f"[-] Error assigning accounts: {e}")
            return []
    
    def start_automation(self, campaign_id, num_workers=5):
        """Запустить автоматизацию кампании"""
        try:
            if campaign_id in self.running_campaigns:
                self.running_campaigns[campaign_id]['status'] = 'running'
                self.running_campaigns[campaign_id]['workers'] = num_workers
                
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE campaigns SET status = ? WHERE id = ?
                    """, ('running', campaign_id))
                    conn.commit()
                
                return True
            return False
        except Exception as e:
            print(f"[-] Error starting automation: {e}")
            return False
    
    def stop_automation(self, campaign_id=None):
        """Остановить автоматизацию"""
        try:
            if campaign_id and campaign_id in self.running_campaigns:
                self.running_campaigns[campaign_id]['status'] = 'stopped'
                
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE campaigns SET status = ? WHERE id = ?
                    """, ('stopped', campaign_id))
                    conn.commit()
            
            return True
        except Exception as e:
            print(f"[-] Error stopping automation: {e}")
            return False
    
    def schedule_action(self, account_id, action_type, target_id, 
                       action_data=None, delay_minutes=0, campaign_id=None):
        """Запланировать действие"""
        try:
            scheduled_at = datetime.now() + timedelta(minutes=delay_minutes)
            action_id = str(uuid.uuid4())
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO scheduled_actions 
                    (account_id, campaign_id, action_type, target_id, action_data, scheduled_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (account_id, campaign_id, action_type, target_id, str(action_data or {}), scheduled_at))
                conn.commit()
            
            return action_id
        except Exception as e:
            print(f"[-] Error scheduling action: {e}")
            return None
    
    def execute_action(self, account_id, action_type, action_data=None):
        """Выполнить действие немедленно"""
        try:
            # Логирование действия
            print(f"[*] Executing {action_type} for account {account_id}")
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO scheduled_actions 
                    (account_id, action_type, action_data, executed_at, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (account_id, action_type, str(action_data or {}), datetime.now(), 'executed'))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"[-] Error executing action: {e}")
            return False
    
    def get_campaign_stats(self, campaign_id):
        """Получить статистику кампании"""
        try:
            stats = {
                'campaign_id': campaign_id,
                'total_accounts': 0,
                'total_actions': 0,
                'total_likes': 0,
                'total_comments': 0,
                'total_follows': 0,
                'status': 'unknown'
            }
            
            if campaign_id in self.running_campaigns:
                campaign = self.running_campaigns[campaign_id]
                stats['status'] = campaign.get('status', 'unknown')
                stats['total_accounts'] = len(campaign.get('accounts', []))
                stats['total_actions'] = campaign.get('actions_count', 0)
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Получить статистику по типам действий
                cursor.execute("""
                    SELECT action_type, COUNT(*) as count 
                    FROM scheduled_actions 
                    WHERE campaign_id = ? 
                    GROUP BY action_type
                """, (campaign_id,))
                
                for action_type, count in cursor.fetchall():
                    if action_type == 'like':
                        stats['total_likes'] = count
                    elif action_type == 'comment':
                        stats['total_comments'] = count
                    elif action_type == 'follow':
                        stats['total_follows'] = count
            
            return stats
        except Exception as e:
            print(f"[-] Error getting campaign stats: {e}")
            return {}


class InteractionEngine:
    """Класс для управления сетями взаимодействий"""
    
    def __init__(self, db):
        self.db = db
        self.interaction_networks = {}
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Убедиться, что таблицы существуют"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица сетей взаимодействий
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS interaction_networks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        campaign_id INTEGER,
                        interaction_type TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
                    )
                """)
                
                # Таблица взаимодействий
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        network_id INTEGER,
                        from_account_id INTEGER,
                        to_account_id INTEGER,
                        interaction_type TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (network_id) REFERENCES interaction_networks(id)
                    )
                """)
                
                conn.commit()
        except Exception as e:
            print(f"[-] Error creating interaction tables: {e}")
    
    def create_interaction_network(self, campaign_id, interaction_type='friendship'):
        """Создать сеть взаимодействий"""
        try:
            network_id = None
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO interaction_networks (campaign_id, interaction_type)
                    VALUES (?, ?)
                """, (campaign_id, interaction_type))
                conn.commit()
                network_id = cursor.lastrowid
            
            self.interaction_networks[network_id] = {
                'campaign_id': campaign_id,
                'type': interaction_type,
                'interactions': []
            }
            
            return network_id
        except Exception as e:
            print(f"[-] Error creating interaction network: {e}")
            return None
    
    def execute_network_interactions(self, campaign_id, action_type='like'):
        """Выполнить взаимодействия в сети"""
        try:
            print(f"[*] Executing {action_type} interactions for campaign {campaign_id}")
            return True
        except Exception as e:
            print(f"[-] Error executing network interactions: {e}")
            return False
    
    def get_interaction_stats(self, campaign_id):
        """Получить статистику взаимодействий"""
        try:
            stats = {
                'campaign_id': campaign_id,
                'total_networks': 0,
                'total_interactions': 0
            }
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(*) FROM interaction_networks WHERE campaign_id = ?
                """, (campaign_id,))
                result = cursor.fetchone()
                stats['total_networks'] = result[0] if result else 0
                
                cursor.execute("""
                    SELECT COUNT(*) FROM interactions 
                    WHERE network_id IN (
                        SELECT id FROM interaction_networks WHERE campaign_id = ?
                    )
                """, (campaign_id,))
                result = cursor.fetchone()
                stats['total_interactions'] = result[0] if result else 0
            
            return stats
        except Exception as e:
            print(f"[-] Error getting interaction stats: {e}")
            return {}
