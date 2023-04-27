import os
import datetime
from dotenv import load_dotenv
import threading

from flask import Flask, request, jsonify
from pymongo import MongoClient
from nanoid import generate

from interface import TacoBellInterface

app = Flask(__name__)

load_dotenv()

MONGODB_USER = os.environ.get('MONGODB_USER')
MONGODB_PASS = os.environ.get('MONGODB_PASS')

client = MongoClient(f"mongodb+srv://{MONGODB_USER}:{MONGODB_PASS}"
                     "@main.hup8pvq.mongodb.net/?retryWrites=true&w=majority")

db = client.development
storemenus = db.storemenus

tasks = {}


@app.route('/get_menus', methods=['GET'])
def get_menus():
    """
    Get the menus for all stores in the user's area.
    """

    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')

    TBI = TacoBellInterface(latitude, longitude)
    stores = TBI.get_nearby_stores()

    stores_to_get_menus = []

    for store in stores:
        if not storemenus.find_one({"storeNumber": store["storeNumber"]}):
            stores_to_get_menus.append(store)
        elif storemenus.find_one({"storeNumber": store["storeNumber"]})["lastModified"] < datetime.datetime.now() - datetime.timedelta(months=1):
            stores_to_get_menus.append(store)

    if len(stores_to_get_menus) == len(stores):    
        thread_id = generate(size=21)

        tasks[thread_id] = []
        tasks[thread_id].append('Getting menus...')

        threading.Thread(target=get_menus_thread, args=(
            latitude, longitude, thread_id)).start()

        return jsonify(message="No menus found in database, getting them now.", thread_id=thread_id), 202
    else:
        menus = []

        for store in stores:
            menus.append(storemenus.find_one({"storeNumber": store["storeNumber"]}))

        if len(stores_to_get_menus) == 0:
            return jsonify(message='All menus up to date.', data=menus), 200
        else:
            threading.Thread(target=get_specific_menus, args=(
                stores_to_get_menus)).start()
            
            return jsonify(message='Some menus up to date.', data=menus), 206


@app.route('/task', methods=['GET'])
def get_task():
    """
    Get the current task for a given thread.
    """

    thread_id = request.args.get('thread_id')

    if thread_id in tasks:
        if tasks[thread_id][-1] == 'Done!':
            return jsonify(tasks=tasks.pop(thread_id)), 200
        return jsonify(tasks=tasks[thread_id]), 202
    return jsonify(message='No task found.'), 404


def get_menus_thread(latitude, longitude, thread_id):
    """
    Thread for getting the menus for all stores in the user's area.

    :param latitude: The latitude of the user.
    :param longitude: The longitude of the user.
    :param thread_id: The id of the thread.

    :return: None.
    """
    TBI = TacoBellInterface(latitude, longitude)
    stores = TBI.get_nearby_stores()

    tasks[thread_id].append(f'Found {len(stores)} near you.')

    for i, store in enumerate(stores):
        tasks[thread_id].append(
            f'Getting menu for store {i+1} of {len(stores)}...')
        
        menu = TBI.get_menu_information(store)
        menu["lastModified"] = datetime.datetime.now()

        storemenus.insert_one(menu)

    tasks[thread_id].append('Done!')

def get_specific_menus(meta_datas):
    """
    Get the menu for a specific store.

    :param storeNumber: The store number of the store.

    :return: None.
    """

    for meta_data in meta_datas:
        TBI = TacoBellInterface(meta_data["latitude"], meta_data["longitude"])

        menu = TBI.get_menu_information(meta_data)
        menu["lastModified"] = datetime.datetime.now()

        storemenus.insert_one(menu)


def update_menus_thread(latitude, longitude):
    TBI = TacoBellInterface(latitude, longitude)
    stores = TBI.get_nearby_stores()

    for store in stores:
        menu = TBI.get_menu_information(store)
        menu["lastModified"] = datetime.datetime.now()

        storemenus.update_one({"storeNumber": menu["storeNumber"]}, {"$set": menu})

if __name__ == '__main__':
    app.run(debug=True)
