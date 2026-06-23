import random
from faker import Faker

class ProfileGenerator:
    def __init__(self):
        self.geo_data = {
            "IL": {
                "universities": ["Tel Aviv University", "Hebrew University of Jerusalem", "Technion", "Ben-Gurion University"],
                "jobs": ["Software Engineer at Intel", "Manager at Bank Hapoalim", "Marketing Specialist", "Sales Manager"],
                "cities": ["Tel Aviv", "Jerusalem", "Haifa", "Ashdod", "Rishon LeZion"]
            },
            "US": {
                "universities": ["Harvard University", "Stanford University", "MIT", "UC Berkeley", "NYU"],
                "jobs": ["Project Manager at Amazon", "Developer at Google", "Sales Associate at Walmart", "Accountant"],
                "cities": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
            }
        }

    def generate_profile(self, geo, gender, age_range=(25, 30)):
        locale = "he_IL" if geo == "IL" else "en_US"
        fake = Faker(locale)
        
        g_data = self.geo_data.get(geo, self.geo_data["US"])
        
        if gender == "M":
            first_name = fake.first_name_male()
            last_name = fake.last_name_male()
        else:
            first_name = fake.first_name_female()
            last_name = fake.last_name_female()
            
        birthday = fake.date_of_birth(minimum_age=age_range[0], maximum_age=age_range[1])
        
        profile = {
            "first_name": first_name,
            "last_name": last_name,
            "birthday": birthday,
            "gender": gender,
            "city": random.choice(g_data["cities"]),
            "university": random.choice(g_data["universities"]),
            "job": random.choice(g_data["jobs"]),
            "bio": f"Live in {random.choice(g_data['cities'])}. Love life and technology."
        }
        
        gender_str = "male" if gender == "M" else "female"
        profile["avatar_url"] = f"https://xsgames.co/randomusers/assets/avatars/{gender_str}/{random.randint(1, 50)}.jpg"
        
        return profile
