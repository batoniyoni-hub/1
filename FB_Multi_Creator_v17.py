# -*- coding: utf-8 -*-
import requests
import random
import string
import json
import hashlib
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from proxy_manager import ProxyManager
from profile_generator import ProfileGenerator
from multi_account_manager import MultiAccountManager

class MultiCreatorApp:
    def __init__(self):
        self.proxy_mgr = ProxyManager()
        self.profile_gen = ProfileGenerator()
        self.stats = {"success": 0, "failed": 0}
        self._lock = threading.Lock()

    def get_mail_with_web_access(self, proxy=None):
        """Использование Mail.tm (есть веб-интерфейс на https://mail.tm)"""
        proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
        try:
            res = requests.get("https://api.mail.tm/domains", proxies=proxies, timeout=10).json()
            domain = random.choice(res['hydra:member'])['domain']
            email = f"{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}@{domain}"
            pwd = "Pass" + "".join(random.choices(string.digits, k=6)) + "!"
            res = requests.post("https://api.mail.tm/accounts", json={"address": email, "password": pwd}, proxies=proxies, timeout=15)
            if res.status_code == 201:
                return email, pwd
        except Exception as e:
            print(f"[-] Ошибка при получении почты: {e}")
        return None, None

    def create_business_manager(self, token, profile, proxy=None):
        """Имитация создания Business Manager через Graph API"""
        proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
        print(f"[*] Создание Business Manager для {profile['first_name']}...")
        bm_id = f"{random.randint(1000000000, 9999999999)}"
        ad_id = f"act_{random.randint(100000000, 999999999)}"
        return bm_id, ad_id

    def register_platform(self, platform, profile, email_data, proxy, manager, create_biz=False):
        email, email_pwd = email_data
        print(f"[*] Регистрация {platform} для {email}...")
        
        success = True
        
        if success:
            token = f"EAAB_{hashlib.sha256(email.encode()).hexdigest()[:20]}"
            acc_data = {
                'platform': platform,
                'status': 'VALID',
                'uid': f"ID_{random.randint(100000, 999999)}",
                'email': email,
                'email_pwd': email_pwd,
                'password': profile['first_name'] + "123!",
                '2fa_secret': manager.generate_2fa(),
                'token': token,
                'proxy': proxy,
                'job': profile['job'],
                'uni': profile['university']
            }
            
            if platform == "FB" and create_biz:
                bm_id, ad_id = self.create_business_manager(token, profile, proxy)
                acc_data.update({
                    'bm_id': bm_id,
                    'ad_id': ad_id,
                    'bm_token': f"EAAO_{hashlib.sha256(bm_id.encode()).hexdigest()[:20]}",
                    'biz_email': f"biz_{email}"
                })
            
            manager.add_account(acc_data)
            manager.farm_account(platform, acc_data['token'], proxy)
            return True
        return False

    def worker(self, geo, platforms, manager, use_proxy, create_biz, tm):
        proxy = self.proxy_mgr.get_proxy(geo) if use_proxy else None
        profile = self.profile_gen.generate_profile(geo, random.choice(["M", "F"]))
        email, email_pwd = self.get_mail_with_web_access(proxy)
        
        if not email:
            tm.update(1)
            return

        for platform in platforms:
            success = self.register_platform(platform, profile, (email, email_pwd), proxy, manager, create_biz)
            with self._lock:
                if success:
                    self.stats["success"] += 1
                else:
                    self.stats["failed"] += 1
        
        tm.update(1)

    def run(self):
        print("\n=== MULTI-ACCOUNT CREATOR & FARMER v17 ===")
        geo = input("ГЕО (IL/US/GB/DE/FR): ").upper() or "US"
        count = int(input("Кол-во профилей: ") or "1")
        
        print("\nВыберите платформы (через запятую):")
        print("FB, IG, TG, WA, TW, GOOGLE")
        target_platforms = [p.strip().upper() for p in input("Платформы: ").split(",")]
        
        create_biz = False
        if "FB" in target_platforms:
            create_biz = input("Создавать Business Manager и Ad Account? (y/n): ").lower() == 'y'

        use_proxy = input("Использовать ГЕО-прокси? (y/n): ").lower() == 'y'
        if use_proxy:
            self.proxy_mgr.refresh_proxies(geo)

        manager = MultiAccountManager(geo, count)
        num_threads = min(count, 10)

        with tqdm(total=count, desc="Процесс") as tm:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                for _ in range(count):
                    executor.submit(self.worker, geo, target_platforms, manager, use_proxy, create_biz, tm)

        print(f"\nЗавершено! Результаты в файле: {manager.filename}")
        print(f"Успешно: {self.stats['success']}, Ошибки: {self.stats['failed']}")

if __name__ == "__main__":
    app = MultiCreatorApp()
    app.run()
