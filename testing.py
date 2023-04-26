import requests
import time

menus_response = requests.get('http://127.0.0.1:5000/get_menus?latitude=37.710459&longitude=-121.8805183').json()

responses = []

start_time = time.time()

while True:
    task_response = requests.get(f"http://127.0.0.1:5000/task?thread_id={menus_response['thread_id']}").json()

    for task in task_response:
        if task not in responses:
            responses.append(task)
            print(task)

    if task_response[-1] == 'Done!':
        break

    time.sleep(1)

print("--- %s seconds ---" % (time.time() - start_time))
