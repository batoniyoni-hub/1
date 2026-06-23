import requests
import threading
import time
import re
import json
import random
from concurrent.futures import ThreadPoolExecutor


class ProxyManager:
    def __init__(self):
        self.sources = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
        ]
        self.valid_proxies = {}
        self._lock = threading.Lock()

    def fetch_proxies(self):
        print("[*] Поиск новых прокси...")
        proxies = set()
        for source in self.sources:
            try:
                res = requests.get(source, timeout=10)
                if res.status_code == 200:
                    found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', res.text)
                    proxies.update(found)
            except Exception as e:
                print(f"[-] Ошибка при загрузке из {source}: {e}")
                continue
        return list(proxies)

    def check_proxy_geo(self, proxy):
        try:
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
            res = requests.get("http://ip-api.com/json", proxies=proxies, timeout=5).json()
            if res['status'] == 'success':
                country_code = res['countryCode']
                return proxy, country_code
        except Exception as e:
            print(f"[-] Ошибка проверки прокси {proxy}: {e}")
        return None

    def refresh_proxies(self, target_geo=None):
        raw = self.fetch_proxies()
        print(f"[*] Проверка {len(raw)} прокси на ГЕО {target_geo or 'Все'}...")

        with ThreadPoolExecutor(max_workers=50) as executor:
            results = list(executor.map(self.check_proxy_geo, raw[:300]))

        with self._lock:
            for res in results:
                if res:
                    proxy, geo = res
                    if geo not in self.valid_proxies:
                        self.valid_proxies[geo] = []
                    if proxy not in self.valid_proxies[geo]:
                        self.valid_proxies[geo].append(proxy)

        total = sum(len(v) for v in self.valid_proxies.values())
        print(f"[+] База прокси обновлена. Всего валидных: {total}")
        if target_geo and target_geo in self.valid_proxies:
            print(f"[+] Для {target_geo} найдено: {len(self.valid_proxies[target_geo])}")

    def get_proxy(self, geo=None):
        with self._lock:
            if geo and geo in self.valid_proxies and self.valid_proxies[geo]:
                return random.choice(self.valid_proxies[geo])
            all_proxies = [p for proxies in self.valid_proxies.values() for p in proxies]
            if all_proxies:
                return random.choice(all_proxies)
            return None
