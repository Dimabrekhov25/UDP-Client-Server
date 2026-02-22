import asyncio, time
from Utils.CrcUtils import make_packet, verify_crc, parse_packet
class Sensor:
    def __init__(self, sensor_id, device_type, addr):
        self.sensor_id = sensor_id
        self.device_type = device_type
        self.addr = addr
        self.token = f"T-{sensor_id}"
        self.last_seen = time.time()
        self.connected = True
        self.ping_attempts = {}
        self.corrupted_packets = 0

class SensorServer(asyncio.DatagramProtocol):
    def __init__(self):
        self.transport = None
        self.sensors = {}
        self.no_ack_for = {}
        self.cor = 0
        self.count_bat = 0
        #11
       # self.force_low_battery = set()
    def connection_made(self, transport):
        self.transport = transport
        #print(self.transport)
        print("Server started at", transport.get_extra_info('sockname'))
    #1
    # def set_force_low_battery(self, sensor_id: str, value: bool = True):
    #     sid = sensor_id.upper()
    #     if value:
    #         self.force_low_battery.add(sid)
    #         print(f"INFO: Sensor {sid} is now FORCED to low battery state")
    #     else:
    #         self.force_low_battery.discard(sid)
    #         print(f"INFO: Sensor {sid} low battery force DISABLED")

    def datagram_received(self, data, addr):

        obj = parse_packet(data)
        if obj is None:
            packet_size = len(data)
            fake = {"sensor_id": "??", "timestamp": int(time.time()), "device_type": "ThermoNode"}
            self._corrupted(fake, addr)


            self.cor += packet_size
            print(f"AirSens: {self.cor}")
            return

        msg = obj["msg_type"]
        if msg == "REGISTER":
            self._register(obj, addr)
        elif msg == "DATA":
            self._data(obj, addr)
        elif msg == "RESEND_RESPONSE":
            self._resend(obj)
        elif msg == "PONG":
            self._pong(obj)

    def _corrupted(self, obj, addr):
        sid = obj.get("sensor_id", "?")
        ts = obj.get("timestamp", int(time.time()))
        print(f"INFO: {sid} CORRUTPED DATA at {ts}. REQUESTING DATA")

        pkt = make_packet({
            "msg_type": "RESEND",
            "device_type": obj.get("device_type", ""),
            "sensor_id": sid,
            "timestamp": int(time.time()),
            "low_battery": False,
            "token": "",
            "payload": {}
        })
        self.transport.sendto(pkt, addr)

    def _register(self, obj, addr):
        d = obj["device_type"]
        sid = obj["sensor_id"]
        s = Sensor(sid, d, addr)
        self.sensors[d] = s
        print(f"INFO: {sid} REGISTERED at {obj['timestamp']}")
        pkt = make_packet({
            "msg_type": "REGISTER_OK",
            "device_type": d,
            "sensor_id": sid,
            "timestamp": int(time.time()),
            "low_battery": False,
            "token": s.token,
            "payload": {}
        })
        self.transport.sendto(pkt, addr)



    def _data(self, obj, addr):
        d = obj["device_type"]
        sid = obj["sensor_id"]
        token = obj["token"]
        low_batt = obj["low_battery"]
        payload = obj["payload"]


        s = self.sensors.get(d)
        if not s or s.token != token:
            pkt = make_packet({
                "msg_type": "INVALID_TOKEN",
                "device_type": d,
                "sensor_id": sid,
                "timestamp": int(time.time()),
                "low_battery": False,
                "token": "",
                "payload": {}
            })
            self.transport.sendto(pkt, addr)
            return

        # if sid.upper() in self.force_low_battery:
        #     low_batt = True

        s.last_seen = time.time()
        s.addr = addr
        ts = obj["timestamp"]
        timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        prefix = f"{timestr} - "

        if low_batt:
            print(prefix + f"WARNING: LOW BATTERY {sid}")
            if sid == "W1":
                self.count_bat += 1
                print(f"Low Batery Counter WindSense: {self.count_bat}")
        else:
            print(prefix + sid)
        print("; ".join(f"{k}: {v}" for k, v in payload.items()) + ";")


        remaining = self.no_ack_for.get(sid.upper(), 0)
        if remaining > 0:
            self.no_ack_for[sid.upper()] = remaining - 1
            print(f"DEBUG: Suppressing ACK for {sid}, remaining={self.no_ack_for[sid.upper()]}")

            return


        ack = make_packet({
            "msg_type": "ACK",
            "device_type": d,
            "sensor_id": sid,
            "timestamp": int(time.time()),
            "low_battery": False,
            "token": token,
            "payload": {}
        })
        self.transport.sendto(ack, addr)

    def _resend(self, obj):
        sid = obj["sensor_id"]
        print(f"INFO: got RESEND_RESPONSE from {sid}")
        self._data(obj, obj.get("addr", self.sensors[obj["device_type"]].addr))

    def _pong(self, obj):
        sid = obj["sensor_id"]
        for s in self.sensors.values():
            if s.sensor_id == sid:
                s.last_seen = time.time()
                if not s.connected:
                    print(f"INFO: {sid} RECONNECTED!")
                    s.connected = True

    def set_no_ack(self, sensor_id: str, count: int = 3):
        sensor_id = sensor_id.upper()
        self.no_ack_for[sensor_id] = count
        print(f"INFO: Will NOT send ACK for {sensor_id} next {count} DATA messages")

    async def monitor(self):
        while True:
            await asyncio.sleep(5)
            now = time.time()
            for s in list(self.sensors.values()):
                if now - s.last_seen > 15:
                    print(f"DEBUG: Checking {s.sensor_id}, last_seen={int(now - s.last_seen)}s ago")
                    pkt = make_packet({
                        "msg_type": "PING",
                        "device_type": s.device_type,
                        "sensor_id": s.sensor_id,
                        "timestamp": int(now),
                        "low_battery": False,
                        "token": s.token,
                        "payload": {}
                    })
                    self.transport.sendto(pkt, s.addr)
                if now - s.last_seen > 20 and s.connected:
                    print(f"WARNING: {s.sensor_id} DISCONNECTED!")
                    s.connected = False
