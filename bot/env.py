import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.bot_id = os.getenv('BOT_ID')
        self.bot_link = os.getenv('BOT_LINK')
        self.customers_starts_2 = os.getenv('CUSTOMERS_STARTS_2')
        self.matin = os.getenv('MATIN')
        self.token = os.getenv('TOKEN')
        self.admin_list = list(map(int, os.getenv('ADMIN_LIST').split(',')))  # Convert admin IDs to integers
        self.admin = os.getenv('ADMIN')
        self.database = os.getenv('DATABASE')

settings = Settings()
# 