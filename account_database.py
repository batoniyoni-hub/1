# -*- coding: utf-8 -*-
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import json
import os
from enum import Enum

class AccountStatus(Enum):
    """Статусы аккаунтов"""
    PENDING = "pending"
    CREATING = "creating"
    VALID = "valid"
    FARMING = "farming"
    CHECKPOINTED = "checkpointed"
    BANNED = "banned"
    DISABLED = "disabled"

class PlatformType(Enum):
    """Типы платформ"""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    TIKTOK = "tiktok"

class AccountDatabase:
    """SQLite база данных для аккаунтов с полной статистикой"""
    
    def __init__(self, db_path="accounts.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        """Инициализация всех таблиц БД"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Основная таблица аккаунтов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    account_id TEXT UNIQUE,
                    username TEXT,
                    email TEXT UNIQUE NOT NULL,
                    email_password TEXT NOT NULL,
                    account_password TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    birthday TEXT,
                    gender TEXT,
                    country TEXT,
                    city TEXT,
                    
                    -- Профиль информация
                    profile_pic_url TEXT,
                    profile_bio TEXT,
                    job_title TEXT,
                    job_company TEXT,
                    education_school TEXT,
                    education_university TEXT,
                    education_year INTEGER,
                    
                    -- Аутентификация и токены
                    access_token TEXT,
                    refresh_token TEXT,
                    api_key TEXT,
                    two_fa_secret TEXT,
                    two_fa_enabled INTEGER DEFAULT 0,
                    
                    -- Куки и сессии
                    cookies TEXT,
                    session_data TEXT,
                    user_agent TEXT,
                    
                    -- Прокси и антидетект
                    proxy_ip TEXT,
                    antidetect_fingerprint TEXT,
                    device_id TEXT,
                    android_id TEXT,
                    
                    -- Статус и метрики
                    status TEXT DEFAULT 'pending',
                    trust_score REAL DEFAULT 0.0,
                    action_count INTEGER DEFAULT 0,
                    post_count INTEGER DEFAULT 0,
                    friend_count INTEGER DEFAULT 0,
                    follower_count INTEGER DEFAULT 0,
                    
                    -- Бизнес менеджер
                    business_manager_id TEXT,
                    ad_account_id TEXT,
                    bm_token TEXT,
                    business_email TEXT,
                    
                    -- Даты и время
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    last_action TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Ошибки и проблемы
                    last_error TEXT,
                    error_count INTEGER DEFAULT 0,
                    checkpoint_type TEXT,
                    checkpoint_data TEXT,
                    
                    -- Автоматизация
                    auto_farming_enabled INTEGER DEFAULT 0,
                    auto_posting_enabled INTEGER DEFAULT 0,
                    campaign_assigned_id INTEGER,
                    notes TEXT
                )
            ''')
            
            # Таблица историй действий
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS account_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    action_type TEXT,
                    action_data TEXT,
                    target_account_id INTEGER,
                    status TEXT,
                    result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts(id)
                )
            ''')
            
            # Таблица для постов и контента
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS account_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    post_id TEXT,
                    content TEXT,
                    media_urls TEXT,
                    post_type TEXT,
                    likes_count INTEGER DEFAULT 0,
                    comments_count INTEGER DEFAULT 0,
                    shares_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scheduled_for TIMESTAMP,
                    posted_at TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts(id)
                )
            ''')
            
            # Таблица для дружбы/подписок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS account_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    target_account_id INTEGER,
                    relation_type TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts(id),
                    FOREIGN KEY (target_account_id) REFERENCES accounts(id)
                )
            ''')
            
            # Таблица кампаний
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_name TEXT UNIQUE NOT NULL,
                    campaign_type TEXT,
                    platform TEXT,
                    strategy TEXT,
                    prompt TEXT,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    
                    -- Параметры
                    daily_actions_limit INTEGER,
                    interaction_types TEXT,
                    target_audience TEXT,
                    content_template TEXT,
                    
                    -- Статистика
                    total_accounts INTEGER DEFAULT 0,
                    total_actions INTEGER DEFAULT 0,
                    total_likes INTEGER DEFAULT 0,
                    total_comments INTEGER DEFAULT 0,
                    total_follows INTEGER DEFAULT 0,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            ''')
            
            # Таблица лог-файлов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    level TEXT,
                    message TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts(id)
                )
            ''')
            
            # Индексы для производительности
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_account_platform ON accounts(platform)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_account_status ON accounts(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_account_country ON accounts(country)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_action_type ON account_actions(action_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_campaign_status ON campaigns(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_level ON logs(level)')
            
            conn.commit()
    
    def add_account(self, account_data: Dict) -> int:
        """Добавить новый аккаунт"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    columns = ', '.join(account_data.keys())
                    placeholders = ', '.join(['?' for _ in account_data])
                    values = tuple(account_data.values())
                    
                    query = f"INSERT INTO accounts ({columns}) VALUES ({placeholders})"
                    cursor.execute(query, values)
                    conn.commit()
                    
                    return cursor.lastrowid
        except Exception as e:
            self.log_error(None, f"Ошибка добавления аккаунта: {e}")
        return None
    
    def get_account(self, account_id: int = None, email: str = None, 
                   username: str = None) -> Optional[Dict]:
        """Получить аккаунт по различным критериям"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if account_id:
                    cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
                elif email:
                    cursor.execute("SELECT * FROM accounts WHERE email = ?", (email,))
                elif username:
                    cursor.execute("SELECT * FROM accounts WHERE username = ?", (username,))
                else:
                    return None
                
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self.log_error(None, f"Ошибка получения аккаунта: {e}")
        return None
    
    def update_account(self, account_id: int, updates: Dict) -> bool:
        """Обновить информацию аккаунта"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    updates['updated_at'] = datetime.now().isoformat()
                    set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
                    values = list(updates.values()) + [account_id]
                    
                    query = f"UPDATE accounts SET {set_clause} WHERE id = ?"
                    cursor.execute(query, values)
                    conn.commit()
                    
                    return cursor.rowcount > 0
        except Exception as e:
            self.log_error(account_id, f"Ошибка обновления аккаунта: {e}")
        return False
    
    def get_accounts_by_status(self, status: str, limit: int = None) -> List[Dict]:
        """Получить аккаунты по статусу"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM accounts WHERE status = ?"
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query, (status,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.log_error(None, f"Ошибка получения аккаунтов: {e}")
        return []
    
    def get_accounts_by_country(self, country: str, status: str = None) -> List[Dict]:
        """Получить аккаунты по стране"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if status:
                    cursor.execute(
                        "SELECT * FROM accounts WHERE country = ? AND status = ?",
                        (country, status)
                    )
                else:
                    cursor.execute("SELECT * FROM accounts WHERE country = ?", (country,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.log_error(None, f"Ошибка получения аккаунтов по стране: {e}")
        return []
    
    def add_action(self, account_id: int, action_type: str, 
                  action_data: Dict, target_account_id: int = None) -> int:
        """Добавить действие аккаунта"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO account_actions 
                        (account_id, action_type, action_data, target_account_id, status)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (account_id, action_type, json.dumps(action_data), 
                         target_account_id, 'pending'))
                    
                    conn.commit()
                    return cursor.lastrowid
        except Exception as e:
            self.log_error(account_id, f"Ошибка добавления действия: {e}")
        return None
    
    def update_action_status(self, action_id: int, status: str, 
                            result: str = None) -> bool:
        """Обновить статус действия"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        UPDATE account_actions 
                        SET status = ?, result = ?, completed_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (status, result, action_id))
                    
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            self.log_error(None, f"Ошибка обновления статуса: {e}")
        return False
    
    def create_campaign(self, campaign_data: Dict) -> int:
        """Создать новую кампанию"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    columns = ', '.join(campaign_data.keys())
                    placeholders = ', '.join(['?' for _ in campaign_data])
                    values = tuple(campaign_data.values())
                    
                    query = f"INSERT INTO campaigns ({columns}) VALUES ({placeholders})"
                    cursor.execute(query, values)
                    conn.commit()
                    
                    return cursor.lastrowid
        except Exception as e:
            self.log_error(None, f"Ошибка создания кампании: {e}")
        return None
    
    def get_campaign(self, campaign_id: int) -> Optional[Dict]:
        """Получить кампанию"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self.log_error(None, f"Ошибка получения кампании: {e}")
        return None
    
    def assign_accounts_to_campaign(self, campaign_id: int, account_ids: List[int]) -> bool:
        """Назначить аккаунты на кампанию"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    for account_id in account_ids:
                        cursor.execute(
                            "UPDATE accounts SET campaign_assigned_id = ? WHERE id = ?",
                            (campaign_id, account_id)
                        )
                    
                    conn.commit()
                    return True
        except Exception as e:
            self.log_error(None, f"Ошибка назначения аккаунтов: {e}")
        return False
    
    def get_campaign_accounts(self, campaign_id: int) -> List[Dict]:
        """Получить аккаунты кампании"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT * FROM accounts WHERE campaign_assigned_id = ? AND status = ?",
                    (campaign_id, 'valid')
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.log_error(None, f"Ошибка получения аккаунтов кампании: {e}")
        return []
    
    def get_stats(self) -> Dict:
        """Получить общую статистику"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM accounts")
                total_accounts = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = ?", ('valid',))
                valid_accounts = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM campaigns WHERE status = ?", ('active',))
                active_campaigns = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM account_actions WHERE status = ?", ('pending',))
                pending_actions = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT country, COUNT(*) as count 
                    FROM accounts WHERE status = 'valid'
                    GROUP BY country ORDER BY count DESC LIMIT 10
                ''')
                by_country = {row[0]: row[1] for row in cursor.fetchall()}
                
                return {
                    'total_accounts': total_accounts,
                    'valid_accounts': valid_accounts,
                    'active_campaigns': active_campaigns,
                    'pending_actions': pending_actions,
                    'by_country': by_country
                }
        except Exception as e:
            self.log_error(None, f"Ошибка получения статистики: {e}")
        return {}
    
    def log_error(self, account_id: int, message: str, details: str = None):
        """Логировать ошибку"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO logs (account_id, level, message, details)
                        VALUES (?, ?, ?, ?)
                    ''', (account_id, 'ERROR', message, details))
                    
                    conn.commit()
        except Exception as e:
            print(f"[-] Ошибка логирования: {e}")
    
    def cleanup_old_logs(self, days: int = 30):
        """Удалить старые логи"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cutoff_date = datetime.now() - timedelta(days=days)
                    
                    cursor.execute(
                        "DELETE FROM logs WHERE created_at < ?",
                        (cutoff_date.isoformat(),)
                    )
                    conn.commit()
        except Exception as e:
            print(f"[-] Ошибка очистки логов: {e}")
