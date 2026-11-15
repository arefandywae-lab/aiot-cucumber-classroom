"""Stream realistic (noisy) fake Cucumber readings, so the AI lessons work without a board.

    pip install paho-mqtt
    python3 devices/scenario.py normal            # 60 calm readings
    python3 devices/scenario.py jump              # calm, then temperature jumps (like a hair dryer)
    python3 devices/scenario.py drift --jump 4    # temperature rises slowly: the detector misses this one
Options: --count N  --interval SEC  --noise STD  --jump DEGREES  --host HOST  --seed N
Each tick sends node 1-4 to /cn466/data, exactly like the real board.
"""
import argparse
import json
import random
import time

import paho.mqtt.client as mqtt

TOPIC = "/cn466/data"


def readings(i, n, a, rnd):
    frac = i / max(1, n - 1)
    shift = 0.0
    if a.scenario == "jump" and i >= int(n * 0.8):
        shift = a.jump
    elif a.scenario == "drift":
        shift = a.jump * frac
    t = 30.0 + shift + rnd.gauss(0, a.noise)
    return {1: t - 0.4 + rnd.gauss(0, a.noise / 3),
            2: 1010 + rnd.gauss(0, 0.3),
            3: t,
            4: 60 - shift * 2 + rnd.gauss(0, a.noise * 2)}   # warmer air reads drier


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("scenario", choices=["normal", "jump", "drift"])
    p.add_argument("--count", type=int, default=60)
    p.add_argument("--interval", type=float, default=0.2)
    p.add_argument("--noise", type=float, default=0.15)
    p.add_argument("--jump", type=float, default=2.0)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--seed", type=int, default=None)
    a = p.parse_args()
    rnd = random.Random(a.seed)
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="scenario_sim")
    c.connect(a.host, 1883)
    c.loop_start()
    for i in range(a.count):
        for node, v in readings(i, a.count, a, rnd).items():
            c.publish(TOPIC, json.dumps({"node": node, "value": round(v, 2)}), qos=1).wait_for_publish()
        print(f"tick {i + 1}/{a.count}", end="\r", flush=True)
        time.sleep(a.interval)
    c.loop_stop()
    c.disconnect()
    print(f"\ndone: {a.scenario}, {a.count} ticks")


if __name__ == "__main__":
    main()
