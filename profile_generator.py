# -*- coding: utf-8 -*-
from faker import Faker
import random
from datetime import datetime, timedelta

class ProfileGenerator:
    """Генератор профилей с реалистичными данными"""
    
    def __init__(self):
        self.locales = {
            'IL': 'he_IL',
            'US': 'en_US',
            'DE': 'de_DE',
            'FR': 'fr_FR',
            'RU': 'ru_RU',
            'UK': 'uk_UA',
            'CA': 'en_CA'
        }
        
        self.jobs = {
            'IL': ['Software Engineer', 'Product Manager', 'Designer', 'Marketing Manager'],
            'US': ['Software Developer', 'Business Analyst', 'UX Designer', 'Sales Manager'],
            'DE': ['Ingenieur', 'Projektmanager', 'Designer', 'Vertriebsleiter'],
            'FR': ['Ingénieur', 'Chef de projet', 'Concepteur', 'Directeur des ventes']
        }
        
        self.universities = {
            'IL': ['Hebrew University', 'Tel Aviv University', 'Technion', 'Bar-Ilan University'],
            'US': ['MIT', 'Stanford', 'Harvard', 'Berkeley', 'Yale', 'Princeton'],
            'DE': ['TU Munich', 'Heidelberg University', 'Berlin Technical University'],
            'FR': ['Sorbonne University', 'École Polytechnique', 'HEC Paris']
        }
        
        self.cities = {
            'IL': ['Tel Aviv', 'Jerusalem', 'Haifa', 'Beer Sheva', 'Ramat Gan'],
            'US': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Miami'],
            'DE': ['Berlin', 'Munich', 'Hamburg', 'Frankfurt', 'Cologne'],
            'FR': ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice']
        }
    
    def generate_profile(self, country='US', gender='M', age_range=None):
        """Генерировать реалистичный профиль"""
        if country not in self.locales:
            country = 'US'
        
        locale = self.locales[country]
        fake = Faker(locale)
        
        # Возраст
        if age_range is None:
            age_range = (20, 40)
        
        age = random.randint(age_range[0], age_range[1])
        birthday = datetime.now() - timedelta(days=age*365 + random.randint(0, 365))
        
        # Профиль
        if gender == 'M':
            first_name = fake.first_name_male()
            last_name = fake.last_name_male()
        else:
            first_name = fake.first_name_female()
            last_name = fake.last_name_female()
        
        profile = {
            'first_name': first_name,
            'last_name': last_name,
            'birthday': birthday,
            'gender': gender,
            'age': age,
            'city': random.choice(self.cities.get(country, ['Unknown'])),
            'job': random.choice(self.jobs.get(country, ['Developer'])),
            'university': random.choice(self.universities.get(country, ['Unknown University'])),
            'phone': fake.phone_number(),
            'country': country
        }
        
        return profile
