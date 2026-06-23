# -*- coding: utf-8 -*-
"""
FB Multi-Account Creator & Automation System v2.0
Полная система создания и управления мультиаккаунтами
с поддержкой автоматизации, кампаний и взаимодействий
"""

import os
import sys
import argparse
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import requests

from account_database import AccountDatabase
from proxy_manager import ProxyManager
from profile_generator import ProfileGenerator
from multi_account_manager import MultiAccountManager
from campaign_automation import CampaignAutomation, InteractionEngine

class FBMultiCreator:
    """Главный класс для управления системой"""
    
    def __init__(self):
        self.db = AccountDatabase()
        self.proxy_mgr = ProxyManager()
        self.profile_gen = ProfileGenerator()
        self.automation = CampaignAutomation(self.db)
        self.interaction_engine = InteractionEngine(self.db)
        print("\n" + "="*60)
        print("🚀 FB MULTI-ACCOUNT AUTOMATION SYSTEM v2.0")
        print("="*60)
    
    def create_accounts_bulk(self, geo, count, platform, threads, use_proxy):
        """Массовое создание аккаунтов"""
        print(f"\n📝 Создание {count} аккаунтов для {geo}...")
        
        # Обновить прокси
        if use_proxy:
            print("🔄 Обновление прокси БД...")
            self.proxy_mgr.refresh_proxies(geo, limit=500)
        
        # Создать менеджер
        manager = MultiAccountManager(geo, count)
        
        def worker(i):
            try:
                proxy = self.proxy_mgr.get_proxy(geo) if use_proxy else None
                profile = self.profile_gen.generate_profile(geo, 'M')
                
                account_data = {
                    'platform': platform,
                    'email': f"{profile['first_name'].lower()}.{profile['last_name'].lower()}{i}@mail.tm",
                    'email_password': 'Pass123!@',
                    'account_password': 'Pass123!@',
                    'first_name': profile['first_name'],
                    'last_name': profile['last_name'],
                    'birthday': profile['birthday'].strftime('%Y-%m-%d'),
                    'gender': 'M',
                    'country': geo,
                    'city': profile['city'],
                    'job_title': profile['job'],
                    'education_university': profile['university'],
                    'status': 'valid',
                    'trust_score': 0.5 + (i % 10) * 0.05,
                    'proxy_ip': proxy,
                    'device_id': f"device_{i}_{datetime.now().timestamp()}"
                }
                
                manager.add_account(account_data)
                return True
            except Exception as e:
                print(f"[-] Ошибка создания {i}: {e}")
                return False
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            results = list(tqdm(
                executor.map(worker, range(count)),
                total=count,
                desc="Создание аккаунтов"
            ))
        
        stats = manager.get_stats()
        print(f"\n✅ Результаты:")
        print(f"   Создано: {stats['local_stats']['created']}")
        print(f"   Валидных: {stats['local_stats']['valid']}")
        print(f"   Ошибок: {stats['local_stats']['failed']}")
        print(f"   Файл: {stats['filename']}")
        
        return manager
    
    def run_campaign(self, campaign_name, campaign_type, platform, geo, num_accounts):
        """Запустить кампанию"""
        print(f"\n🎯 Запуск кампании '{campaign_name}'...")
        
        # Создать кампанию
        campaign_id = self.automation.create_campaign(
            campaign_name=campaign_name,
            campaign_type=campaign_type,
            platform=platform,
            strategy='engagement'
        )
        
        if not campaign_id:
            print("[-] Ошибка создания кампании")
            return False
        
        # Назначить аккаунты
        print(f"📊 Назначение {num_accounts} аккаунтов...")
        account_ids = self.automation.assign_accounts_to_campaign(
            campaign_id,
            country=geo,
            limit=num_accounts
        )
        
        if not account_ids:
            print("[-] Нет доступных аккаунтов")
            return False
        
        # Создать сеть взаимодействий
        print("🔗 Создание сети взаимодействий...")
        self.interaction_engine.create_interaction_network(campaign_id, 'friendship')
        
        # Запустить автоматизацию
        print("⚡ Запуск автоматизации...")
        self.automation.start_automation(campaign_id, num_workers=5)
        
        # Получить статистику
        stats = self.automation.get_campaign_stats(campaign_id)
        print(f"\n📈 Статистика кампании:")
        print(f"   Аккаунтов: {stats.get('total_accounts', 0)}")
        print(f"   Действий: {stats.get('total_actions', 0)}")
        print(f"   Лайков: {stats.get('total_likes', 0)}")
        
        return campaign_id
    
    def show_dashboard_stats(self):
        """Показать статистику дашборда"""
        print("\n📊 СТАТИСТИКА СИСТЕМЫ")
        print("="*60)
        
        stats = self.db.get_stats()
        proxy_stats = self.proxy_mgr.db.get_stats()
        
        print(f"\n👥 АККАУНТЫ:")
        print(f"   Всего: {stats.get('total_accounts', 0)}")
        print(f"   Валидных: {stats.get('valid_accounts', 0)}")
        print(f"   Невалидных: {stats.get('invalid', 0)}")
        print(f"   В ожидании действий: {stats.get('pending_actions', 0)}")
        
        print(f"\n🌍 ПО СТРАНАМ:")
        for country, count in stats.get('by_country', {}).items():
            print(f"   {country}: {count}")
        
        print(f"\n🔌 ПРОКСИ:")
        print(f"   Всего: {proxy_stats.get('total', 0)}")
        print(f"   Валидных: {proxy_stats.get('valid', 0)}")
        
        print("\n" + "="*60)
    
    def interactive_menu(self):
        """Интерактивное меню"""
        while True:
            print("\n📋 ГЛАВНОЕ МЕНЮ")
            print("="*60)
            print("1. Создать новые аккаунты")
            print("2. Запустить кампанию")
            print("3. Показать статистику")
            print("4. Управление прокси")
            print("5. Экспортировать аккаунты")
            print("6. Запустить веб-дашборд")
            print("0. Выход")
            print("="*60)
            
            choice = input("Выберите опцию: ").strip()
            
            if choice == '1':
                self.menu_create_accounts()
            elif choice == '2':
                self.menu_run_campaign()
            elif choice == '3':
                self.show_dashboard_stats()
            elif choice == '4':
                self.menu_proxy()
            elif choice == '5':
                self.menu_export()
            elif choice == '6':
                self.menu_web_dashboard()
            elif choice == '0':
                print("\n👋 До свидания!")
                break
            else:
                print("[-] Неверный выбор")
    
    def menu_create_accounts(self):
        print("\n📝 СОЗДАНИЕ АККАУНТОВ")
        geo = input("Страна (IL/US/DE/FR): ").upper() or "US"
        count = int(input("Кол-во аккаунтов: ") or "10")
        platform = input("Платформа (facebook/instagram): ").lower() or "facebook"
        threads = int(input("Потоков: ") or "5")
        use_proxy = input("Использовать прокси? (y/n): ").lower() == 'y'
        
        self.create_accounts_bulk(geo, count, platform, threads, use_proxy)
    
    def menu_run_campaign(self):
        print("\n🎯 ЗАПУСК КАМПАНИИ")
        campaign_name = input("Название кампании: ")
        campaign_type = input("Тип (organic/paid): ").lower() or "organic"
        platform = input("Платформа: ").lower() or "instagram"
        geo = input("Страна: ").upper() or "US"
        num_accounts = int(input("Кол-во аккаунтов: ") or "10")
        
        self.run_campaign(campaign_name, campaign_type, platform, geo, num_accounts)
    
    def menu_proxy(self):
        print("\n🔌 УПРАВЛЕНИЕ ПРОКСИ")
        geo = input("Страна (US/DE/FR): ").upper() or "US"
        print("Обновление БД прокси...")
        self.proxy_mgr.refresh_proxies(geo, limit=300)
        self.proxy_mgr.show_stats()
    
    def menu_export(self):
        print("\n💾 ЭКСПОРТ АККАУНТОВ")
        status = input("Статус (valid/all): ").lower() or "valid"
        format_type = input("Формат (xlsx/json/csv/txt): ").lower() or "xlsx"
        print(f"Экспорт {status} аккаунтов в формате {format_type}...")
    
    def menu_web_dashboard(self):
        print("\n🌐 ВЕБ-ДАШБОРД")
        print("Запуск веб-дашборда на http://localhost:5000")
        print("Для остановки нажмите Ctrl+C")
        os.system("python api_dashboard.py")

def main():
    parser = argparse.ArgumentParser(description='FB Multi-Account Automation')
    parser.add_argument('--mode', choices=['interactive', 'create', 'campaign', 'api'], 
                       default='interactive', help='Режим работы')
    parser.add_argument('--geo', default='US', help='Геолокация')
    parser.add_argument('--count', type=int, default=10, help='Кол-во аккаунтов')
    parser.add_argument('--threads', type=int, default=5, help='Потоков')
    parser.add_argument('--proxy', action='store_true', help='Использовать прокси')
    
    args = parser.parse_args()
    
    creator = FBMultiCreator()
    
    if args.mode == 'interactive':
        creator.interactive_menu()
    elif args.mode == 'create':
        creator.create_accounts_bulk(args.geo, args.count, 'facebook', args.threads, args.proxy)
    elif args.mode == 'api':
        os.system("python api_dashboard.py")
    else:
        creator.show_dashboard_stats()

if __name__ == "__main__":
    main()
