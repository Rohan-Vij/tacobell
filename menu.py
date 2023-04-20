"""File containing functions to retrieve menu information"""
import json
import time
import requests

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


class TacoBellInterface:
    """Class to interface with the Taco Bell website/public APIs."""

    # Creating the Selenium headless driver
    options = Options()
    options.add_argument('headless')
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")

    service = Service('C:\\Program Files\\chromedriver.exe')
    driver = webdriver.Chrome(
        service=service, options=options)

    driver.set_window_size(1440, 900)

    def __init__(self, latitude, longitude):
        """
        Initialize the class with the latitude and longitude of the user.
        
        :param latitude: The latitude of the user.
        :param longitude: The longitude of the user.
        """
        self.latitude = latitude
        self.longitude = longitude

        self.nearby_stores = []

    def get_menu_information(self, meta_data):
        """
        Get the menu information for a given store.

        :param meta_data: The meta data for the store.

        :return: A confirmation message.
        """
        urls = ["breakfast", "tacos", "deals-and-combos", "online-exclusives", "new",
                "burritos", "specialties", "sides-sweets", "cravings-value-menu", 
                "quesadillas", "drinks", "nachos", "party-packs", "vegetarian", "power-menu"]

        store_data = meta_data

        store_data["menu"] = {}

        for url in urls:
            self.driver.get(
                f"https://www.tacobell.com/food/{url}?store={store_data['store_number']}")
            time.sleep(1)

            plain_text = self.driver.page_source
            soup = BeautifulSoup(plain_text, 'html.parser')

            store_data["menu"][url] = []

            items = soup.find_all('div', {'class': 'styles_product-card__1-cAT'})

            for item in items:
                item_name = item.find('h4').text
                item_link = item.find(
                    'a', {'class': 'styles_product-title__6KCyw'}).get('href')

                product_information = item.find(
                    'p', {'class': 'styles_product-details__2VdYf'}).find_all('span')

                product_price = float(product_information[0].text.replace('$', ''))
                product_calories = product_information[1].text

                store_data["menu"][url].append({"item_name": item_name, "information": {
                    "item_link": item_link, "product_price": product_price, 
                    "product_calories": product_calories}})

                print(item_name, item_link, product_price, product_calories)

            with open(f"menus/{store_data['store_number']}_menu.json",
                      'w', encoding='utf-8') as outfile:
                json.dump(store_data, outfile, indent=4)

        return "OK"


    def get_nearby_stores(self):
        """
        Get the nearby stores for the user.

        :return: The nearby stores for the user.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }

        response = requests.get(
            "https://www.tacobell.com/tacobellwebservices/v2/tacobell/stores?" \
            f"latitude={self.latitude}&longitude={self.longitude}&_=1681443869531", 
            headers=headers, timeout=5)

        data = json.loads(response.text)

        for location in data["nearByStores"][:1]:

            meta_data = {
                "store_number": location["storeNumber"],
                "phone_number": location["phoneNumber"],
                "address": location["address"],
                "geo_point": location["geoPoint"]
            }

            self.nearby_stores.append(meta_data)

        return self.nearby_stores

TBI = TacoBellInterface(37.7749, -122.4194)
stores = TBI.get_nearby_stores()
for store in stores[:1]:
    TBI.get_menu_information(store)
