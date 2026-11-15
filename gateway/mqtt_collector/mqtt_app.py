import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import sqlite3
import json
import math

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe("/cn466/data")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    try:
        payload = json.loads(msg.payload)
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON object")
        node, value = payload['node'], payload['value']
        if node not in (1, 2, 3, 4) or isinstance(node, bool):
            raise ValueError("unknown node")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("value must be a finite number")
        values = (node, float(value))
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
        print(f"Ignoring invalid message: {exc}")
        return
    conn = sqlite3.connect("data.db")
    try:
        with conn:
            sqlcmd = 'INSERT INTO data (node, value) VALUES(?, ?);'
            conn.execute(sqlcmd, values)
    except sqlite3.Error as exc:
        print(f"Could not store message: {exc}")
    finally:
        conn.close()

mqttc = mqtt.Client(CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

# Initialize here too: the REST process may not have started yet.
conn = sqlite3.connect("data.db")
with conn:
    sqlcmd = ("CREATE TABLE IF NOT EXISTS data ("
              "_id INTEGER PRIMARY KEY AUTOINCREMENT, "
              "node INTEGER, "
              "value REAL, "
              "ts TEXT DEFAULT (datetime('now')));")
    conn.execute(sqlcmd)
conn.close()

mqttc.connect_async("mosquitto", 1883, 60)

print('Starting MQTT')
mqttc.loop_forever(retry_first_connection=True)
