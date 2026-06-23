import os
import datetime
import pyotp
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

class MultiAccountManager:
    def __init__(self, geo, count):
        self.geo = geo
        self.count = count
        self.date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        self.filename = f"Accounts_{geo}_{count}acc_{self.date_str}.xlsx"
        self.wb = Workbook()
        self.setup_excel()

    def setup_excel(self):
        ws = self.wb.active
        ws.title = "Accounts Data"
        headers = [
            'Platform', 'Status', 'ID / Username', 'Email', 'Email Password', 
            'Platform Password', '2FA Secret', '2FA Code', 'Token / Cookies', 
            'API Key', 'GEO', 'Proxy', 'Profile Info (Job/Uni)', 'Checkpoint Status',
            'BM ID', 'Ad Account ID', 'BM Token', 'Business Email'
        ]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        self.wb.save(self.filename)

    def add_account(self, data):
        ws = self.wb.active
        next_row = ws.max_row + 1
        
        two_fa_code = ""
        if data.get('2fa_secret'):
            try:
                totp = pyotp.TOTP(data['2fa_secret'])
                two_fa_code = totp.now()
            except Exception as e:
                print(f"[-] Ошибка 2FA: {e}")

        row_data = [
            data.get('platform', 'N/A'),
            data.get('status', 'Unknown'),
            data.get('uid', 'N/A'),
            data.get('email', 'N/A'),
            data.get('email_pwd', 'N/A'),
            data.get('password', 'N/A'),
            data.get('2fa_secret', 'N/A'),
            two_fa_code,
            data.get('token', 'N/A'),
            data.get('api_key', 'N/A'),
            self.geo,
            data.get('proxy', 'N/A'),
            f"{data.get('job', '')} / {data.get('uni', '')}",
            data.get('checkpoint', 'None'),
            data.get('bm_id', 'N/A'),
            data.get('ad_id', 'N/A'),
            data.get('bm_token', 'N/A'),
            data.get('biz_email', 'N/A')
        ]
        ws.append(row_data)
        self.wb.save(self.filename)

    def generate_2fa(self):
        return pyotp.random_base32()

    def farm_account(self, platform, token, proxy):
        """Логика фарма (имитация действий живого пользователя)"""
        print(f"[*] Фарминг аккаунта {platform} через прокси {proxy}...")
        return True

    def solve_checkpoint(self, platform, account_data):
        """Логика прохождения чекпоинта"""
        print(f"[*] Попытка разблокировки чекпоинта для {platform}...")
        return True
