"""Publish simulated Cucumber sensor readings to MQTT (node 1-4 -> /cn466/data)."""
import json
import sys
import time

import paho.mqtt.client as mqtt

BROKER, PORT, TOPIC = "127.0.0.1", 1883, "/cn466/data"


def publish(readings, repeat=1, interval=0.5):
    """readings: {node_id: value}. Send every reading `repeat` times."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="lab8_sim")
    client.connect(BROKER, PORT)
    client.loop_start()
    for _ in range(repeat):
        for node, value in readings.items():
            msg = json.dumps({"node": node, "value": value})
            client.publish(TOPIC, msg, qos=1).wait_for_publish()
            print(f"published {TOPIC} {msg}")
        time.sleep(interval)
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    # usage: publish_sim.py <temp> <pressure> <humidity>
    t, p, h = (float(x) for x in sys.argv[1:4])
    publish({1: t, 2: p, 3: t, 4: h})
