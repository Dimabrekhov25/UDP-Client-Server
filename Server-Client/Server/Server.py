from datetime import time

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