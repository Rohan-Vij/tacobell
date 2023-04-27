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

# Loading DB environment variables

MONGODB_USER = os.environ.get('MONGODB_USER')
MONGODB_PASS = os.environ.get('MONGODB_PASS')

client = MongoClient(f"mongodb+srv://{MONGODB_USER}:{MONGODB_PASS}"
                     "@main.hup8pvq.mongodb.net/?retryWrites=true&w=majority")

db = client.development
storemenus = db.storemenus

# Global task dictionary to store the IDs and status updates of ongoing threads
tasks = {}

@app.route('/get_menus', methods=['GET'])
def get_menus():
    """
    Get the menus for all stores in the user's area.
    """

    # Get the latitude and longitude from the request
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')

    # Create a TBI using the lat and long
    TBI = TacoBellInterface(latitude, longitude)

    # Getting all nearby stores
    stores = TBI.get_nearby_stores()

    # Creating a list of stores not currently in the database to get menus for
    stores_to_get_menus = []

    for store in stores:
        # If the store is not in the database, add it to the list
        if not storemenus.find_one({"storeNumber": store["storeNumber"]}):
            stores_to_get_menus.append(store)
        # If the store is in the database but the menu is over a month old, add it to the list    
        elif storemenus.find_one({"storeNumber": store["storeNumber"]})["lastModified"] < datetime.datetime.now() - datetime.timedelta(months=1):
            stores_to_get_menus.append(store)

    # If the number of stores not in the database is equal to the number of stores found near the user
    # We know that no menus are in the database for the user's area
    if len(stores_to_get_menus) == len(stores):   
        # Generate a thread ID 
        thread_id = generate(size=21)

        # Create a new task for the thread
        tasks[thread_id] = []
        tasks[thread_id].append('Getting menus...')

        # Start the thread
        threading.Thread(target=get_menus_thread, args=(
            latitude, longitude, thread_id)).start()

        # Return a 202 status code to indicate that the request has been accepted
        # Plus the thread ID so the frontend can check the status of the request
        return jsonify(message="No menus found in database, getting them now.", thread_id=thread_id), 202
    else:
        # If there are menus in the database, return them
        menus = []

        # Getting all the menus from the database
        for store in stores:
            menus.append(storemenus.find_one({"storeNumber": store["storeNumber"]}))

        # If there are no menus to get, return a 200 status code 
        if len(stores_to_get_menus) == 0:
            return jsonify(message='All menus up to date.', data=menus), 200
        # If there are menus to get, return a 206 status code
        else:
            # Start a thread to get the menus, but not with a thread ID
            # This is a background process, the user does not need to know the status of it
            threading.Thread(target=get_specific_menus, args=(
                stores_to_get_menus)).start()
            
            return jsonify(message='Some menus up to date.', data=menus), 206


@app.route('/task', methods=['GET'])
def get_task():
    """
    Get the current task for a given thread.
    """

    # Get the thread ID from the request
    thread_id = request.args.get('thread_id')

    # If the thread ID is in the tasks dictionary
    if thread_id in tasks:
        # If the last task is 'Done!', return the task and a 200 status code
        if tasks[thread_id][-1] == 'Done!':
            return jsonify(tasks=tasks.pop(thread_id)), 200
        # If the last task is not 'Done!', return the task and a 202 status code (still in process)
        return jsonify(tasks=tasks[thread_id]), 202
    # If the thread ID is not in the tasks dictionary, return a 404 status code
    return jsonify(message='No task found.'), 404


def get_menus_thread(latitude, longitude, thread_id):
    """
    Thread for getting the menus for all stores in the user's area.

    :param latitude: The latitude of the user.
    :param longitude: The longitude of the user.
    :param thread_id: The id of the thread.

    :return: None.
    """
    # Create a TBI using the lat and long
    TBI = TacoBellInterface(latitude, longitude)
    stores = TBI.get_nearby_stores()

    # Add the number of stores found to the tasks status dictionary
    tasks[thread_id].append(f'Found {len(stores)} near you.')

    # For each store, get the menu and add it to the database
    for i, store in enumerate(stores):
        tasks[thread_id].append(
            f'Getting menu for store {i+1} of {len(stores)}...')
        
        menu = TBI.get_menu_information(store)
        menu["lastModified"] = datetime.datetime.now()

        storemenus.insert_one(menu)

    # Add 'Done!' to the tasks status dictionary
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

if __name__ == '__main__':
    app.run(debug=True)
