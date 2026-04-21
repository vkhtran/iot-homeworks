import json
import math
import time

import paho.mqtt.client as mqtt
import threading

id = '<ID>'

client_telemetry_topic = id + '/telemetry'
server_command_topic = id + '/commands'
client_name = id + 'soilmoisturesensor_server'

mqtt_client = mqtt.Client(client_name)
mqtt_client.connect('test.mosquitto.org')

mqtt_client.loop_start()

wait_time = 20
target_soil_moisture = 430
moisture_drop_per_second = 20.33
max_water_time = 10

def send_relay_command(client, state):
    command = { 'relay_on' : state }
    print("Sending message:", command)
    client.publish(server_command_topic, json.dumps(command))

def calculate_water_time(soil_moisture):
    moisture_gap = soil_moisture - target_soil_moisture

    if moisture_gap <= 0:
        return 0

    water_time = moisture_gap / moisture_drop_per_second
    return min(max_water_time, max(1, math.ceil(water_time)))

def control_relay(client, water_time):
    print("Unsubscribing from telemetry")
    mqtt_client.unsubscribe(client_telemetry_topic)

    print(f"Watering for {water_time} second(s)")
    send_relay_command(client, True)
    time.sleep(water_time)
    send_relay_command(client, False)

    print(f"Waiting {wait_time} second(s) for soil moisture to stabilize")
    time.sleep(wait_time)

    print("Subscribing to telemetry")
    mqtt_client.subscribe(client_telemetry_topic)

def handle_telemetry(client, userdata, message):
    payload = json.loads(message.payload.decode())
    print("Message received:", payload)

    soil_moisture = payload['soil_moisture']
    water_time = calculate_water_time(soil_moisture)

    if water_time > 0:
        threading.Thread(target=control_relay, args=(client, water_time)).start()
    else:
        print("Soil moisture is in the target range, no watering needed.")

mqtt_client.subscribe(client_telemetry_topic)
mqtt_client.on_message = handle_telemetry

while True:
    time.sleep(2)
