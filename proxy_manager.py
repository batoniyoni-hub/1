# -*- coding: utf-8 -*-
import requests
import threading
import time
import re
import json
import random
import sqlite3
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple

class ProxyDatabase:
    """SQLite база данных для хранения и управления проксями"""
    
    def __init__(self, db_path="proxies.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        """Инициализация таблиц БД"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица проксей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proxies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_port TEXT UNIQUE NOT NULL,
                    country_code TEXT,
                    last_checked TIMESTAMP,
                    is_valid INTEGER DEFAULT 1,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    avg_response_time REAL DEFAULT 0,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    protocol TEXT DEFAULT 'http'
                )
            ''')
            
            # Таблица истории проверок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proxy_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proxy_id INTEGER NOT NULL,
                    check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_valid INTEGER,
                    response_time REAL,
                    error_message TEXT,
                    FOREIGN KEY (proxy_id) REFERENCES proxies(id)
                )
            ''')
            
            # Индексы для оптимизации
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_country ON proxies(country_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_valid ON proxies(is_valid)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_checked ON proxies(last_checked)')
            
            conn.commit()
    
    def add_proxy(self, ip_port: str, country_code: str = None, protocol: str = "http"):
        """Добавить прокси в БД"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR IGNORE INTO proxies 
                        (ip_port, country_code, protocol, last_checked) 
                        VALUES (?, ?, ?, NULL)
                    ''', (ip_port, country_code, protocol))
                    conn.commit()
        except Exception as e:
            print(f"[-] Ошибка добавления прокси {ip_port}: {e}")
    
    def get_proxy(self, country_code: str = None, min_success_rate: float = 0.5) -> Optional[str]:
        """Получить рабочий прокси для страны"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT ip_port FROM proxies WHERE is_valid = 1"
                params = []
                
                if country_code:
                    query += " AND country_code = ?"
                    params.append(country_code)
                
                # Фильтр по rate успеха
                query += """ AND (
                    (success_count + fail_count = 0) OR 
                    (CAST(success_count AS FLOAT) / (success_count + fail_count) >= ?)
                )"""
                params.append(min_success_rate)
                
                query += " ORDER BY avg_response_time ASC LIMIT 1"
                
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"[-] Ошибка получения прокси: {e}")
        return None
    
    def get_proxies_by_country(self, country_code: str, limit: int = None) -> List[str]:
        """Получить все рабочие прокси для страны"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = "SELECT ip_port FROM proxies WHERE is_valid = 1 AND country_code = ? ORDER BY avg_response_time ASC"
                if limit:
                    query += f" LIMIT {limit}"
                cursor.execute(query, (country_code,))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"[-] Ошибка получения списка прокси: {e}")
        return []
    
    def update_proxy_check(self, ip_port: str, is_valid: bool, response_time: float = None, error_msg: str = None):
        """Обновить результаты проверки прокси"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Получить ID прокси
                    cursor.execute("SELECT id FROM proxies WHERE ip_port = ?", (ip_port,))
                    result = cursor.fetchone()
                    if not result:
                        return
                    
                    proxy_id = result[0]
                    
                    # Добавить запись в историю
                    cursor.execute('''
                        INSERT INTO proxy_checks 
                        (proxy_id, is_valid, response_time, error_message) 
                        VALUES (?, ?, ?, ?)
                    ''', (proxy_id, 1 if is_valid else 0, response_time, error_msg))
                    
                    # Обновить статистику прокси
                    if is_valid:
                        cursor.execute('''
                            UPDATE proxies SET 
                            success_count = success_count + 1,
                            last_checked = CURRENT_TIMESTAMP,
                            is_valid = 1
                            WHERE id = ?
                        ''', (proxy_id,))
                    else:
                        cursor.execute('''
                            UPDATE proxies SET 
                            fail_count = fail_count + 1,
                            last_checked = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (proxy_id,))
                        
                        # Если слишком много ошибок, деактивировать
                        cursor.execute('''
                            UPDATE proxies SET is_valid = 0 
                            WHERE id = ? AND fail_count > success_count + 5
                        ''', (proxy_id,))
                    
                    # Обновить среднее время ответа
                    cursor.execute('''
                        SELECT AVG(response_time) FROM proxy_checks 
                        WHERE proxy_id = ? AND response_time IS NOT NULL
                    ''', (proxy_id,))
                    avg_time = cursor.fetchone()[0]
                    if avg_time:
                        cursor.execute('UPDATE proxies SET avg_response_time = ? WHERE id = ?', 
                                     (avg_time, proxy_id))
                    
                    conn.commit()
        except Exception as e:
            print(f"[-] Ошибка обновления проверки прокси: {e}")
    
    def get_stats(self) -> Dict:
        """Получить статистику по проксям"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM proxies")
                total = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM proxies WHERE is_valid = 1")
                valid = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT country_code, COUNT(*) as count 
                    FROM proxies WHERE is_valid = 1 
                    GROUP BY country_code ORDER BY count DESC
                ''')
                by_country = {row[0]: row[1] for row in cursor.fetchall()}
                
                return {
                    "total": total,
                    "valid": valid,
                    "invalid": total - valid,
                    "by_country": by_country
                }
        except Exception as e:
            print(f"[-] Ошибка получения статистики: {e}")
        return {}
    
    def cleanup_old_proxies(self, days: int = 7):
        """Удалить неактивные прокси"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cutoff_date = datetime.now() - timedelta(days=days)
                    cursor.execute('''
                        DELETE FROM proxies 
                        WHERE is_valid = 0 AND last_checked < ?
                    ''', (cutoff_date,))
                    deleted = cursor.rowcount
                    conn.commit()
                    if deleted > 0:
                        print(f"[*] Удалено {deleted} старых неактивных прокси")
        except Exception as e:
            print(f"[-] Ошибка очистки БД: {e}")


class ProxyChecker:
    """Продвинутый чекер для проверки проксей"""
    
    def __init__(self, db: ProxyDatabase):
        self.db = db
        self.test_urls = [
            ("http://ip-api.com/json", 5),
            ("http://httpbin.org/ip", 5),
            ("http://ifconfig.me", 3),
        ]
        self._lock = threading.Lock()
    
    def check_proxy(self, proxy: str, timeout: int = 10) -> Tuple[bool, str, float]:
        """
        Проверить прокси
        Returns: (is_valid, country_code, response_time)
        """
        start_time = time.time()
        proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        
        try:
            # Проверка через ip-api.com
            response = requests.get(
                "http://ip-api.com/json",
                proxies=proxies,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            response.raise_for_status()
            data = response.json()
            
            response_time = time.time() - start_time
            
            if data.get('status') == 'success':
                country_code = data.get('countryCode', 'XX')
                return True, country_code, response_time
            
            return False, None, response_time
            
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            return False, None, response_time
        except requests.exceptions.ProxyError:
            response_time = time.time() - start_time
            return False, None, response_time
        except Exception as e:
            response_time = time.time() - start_time
            return False, None, response_time
    
    def validate_proxy_format(self, proxy: str) -> bool:
        """Валидировать формат прокси IP:PORT"""
        pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$'
        return bool(re.match(pattern, proxy))
    
    def check_proxies_batch(self, proxies: List[str], max_workers: int = 50, 
                           show_progress: bool = True):
        """Проверить батч прокси"""
        print(f"[*] Проверка {len(proxies)} прокси...")
        valid_count = 0
        invalid_count = 0
        
        def check_and_store(proxy):
            nonlocal valid_count, invalid_count
            
            if not self.validate_proxy_format(proxy):
                invalid_count += 1
                return
            
            is_valid, country_code, response_time = self.check_proxy(proxy)
            
            if is_valid:
                self.db.add_proxy(proxy, country_code)
                self.db.update_proxy_check(proxy, True, response_time)
                valid_count += 1
                print(f"[+] ✓ {proxy} -> {country_code} ({response_time:.2f}s)")
            else:
                self.db.add_proxy(proxy)
                self.db.update_proxy_check(proxy, False, response_time)
                invalid_count += 1
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            if show_progress:
                from tqdm import tqdm
                list(tqdm(
                    executor.map(check_and_store, proxies),
                    total=len(proxies),
                    desc="Проверка прокси"
                ))
            else:
                list(executor.map(check_and_store, proxies))
        
        print(f"[+] Результат: {valid_count} валидных, {invalid_count} невали��ных")
        return valid_count, invalid_count


class ProxyManager:
    """Менеджер проксей с интеграцией БД"""
    
    def __init__(self, db_path="proxies.db"):
        self.db = ProxyDatabase(db_path)
        self.checker = ProxyChecker(self.db)
        self.sources = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
        ]
        self._lock = threading.Lock()
    
    def fetch_proxies_from_sources(self) -> List[str]:
        """Загрузить прокси из всех источников"""
        print("[*] Загрузка прокси из источников...")
        proxies = set()
        
        for source in self.sources:
            try:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', response.text)
                    proxies.update(found)
                    print(f"[+] Источник {source.split('/')[2]}: найдено {len(found)}")
            except Exception as e:
                print(f"[-] Ошибка загрузки {source}: {e}")
        
        print(f"[+] Всего найдено уникальных прокси: {len(proxies)}")
        return list(proxies)
    
    def refresh_proxies(self, target_geo: str = None, limit: int = 300):
        """Обновить базу прокси"""
        proxies = self.fetch_proxies_from_sources()
        
        # Проверить и сохранить прокси
        self.checker.check_proxies_batch(proxies[:limit])
        
        # Показать статистику
        stats = self.db.get_stats()
        print(f"\n[+] Статистика БД прокси:")
        print(f"    Всего: {stats.get('total', 0)}")
        print(f"    Валидных: {stats.get('valid', 0)}")
        print(f"    Невалидных: {stats.get('invalid', 0)}")
        
        if stats.get('by_country'):
            print(f"    По странам: {stats['by_country']}")
        
        if target_geo:
            geo_proxies = self.db.get_proxies_by_country(target_geo)
            print(f"    Для {target_geo}: {len(geo_proxies)}")
    
    def get_proxy(self, geo: str = None) -> Optional[str]:
        """Получить прокси для геолокации"""
        return self.db.get_proxy(geo)
    
    def get_proxies_for_geo(self, geo: str, limit: int = None) -> List[str]:
        """Получить список прокси для геолокации"""
        return self.db.get_proxies_by_country(geo, limit)
    
    def show_stats(self):
        """Показать статистику"""
        stats = self.db.get_stats()
        print("\n=== СТАТИСТИКА БД ПРОКСИ ===")
        print(f"Всего прокси: {stats.get('total', 0)}")
        print(f"Валидных: {stats.get('valid', 0)}")
        print(f"Невалидных: {stats.get('invalid', 0)}")
        
        if stats.get('by_country'):
            print(f"\nПо странам:")
            for country, count in sorted(stats['by_country'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {country}: {count}")
    
    def cleanup(self, days: int = 7):
        """Очистить старые прокси"""
        self.db.cleanup_old_proxies(days)
