import asyncio, time, random
from aioconsole import ainput

from Utils.CrcUtils import make_packet, parse_packet, verify_crc


class DeviceClient(asyncio.DatagramProtocol):

    def __init__(self, sensor, server_addr):
        self.sensor = sensor
        self.server_addr = server_addr
        self.transport = None
        self.token = None
        self.inject_errors = False
        self.last_payload = None
        self.running = False
        self.ignore_ping = False
        self.ping_counter = 0
        self.waiting_for_ack = False
        self.ack_event = asyncio.Event()

    def connection_made(self, transport):
        self.transport = transport
        print(f"[{self.sensor.device_type}] Connected to server. Ready to start.")

    def _send(self, msg_type, payload):
        pkt = {
            "msg_type": msg_type,
            "device_type": self.sensor.device_type,
            "sensor_id": self.sensor.sensor_id,
            "timestamp": int(time.time()),
            "low_battery": self.sensor.low_battery,
            "token": self.token or "",
            "payload": payload
        }

        raw = make_packet(pkt)

        if self.inject_errors and msg_type == "DATA":

            raw = bytearray(raw)
            raw[-1] ^= 0x01
            raw = bytes(raw)
            print(f"[{self.sensor.device_type}] Sending corrupted DATA (CRC16 broken)")

        self.transport.sendto(raw, self.server_addr)

    async def send_data_with_retry(self, payload=None):

        if payload is None:
            payload = self.sensor.generate_payload()

        self.last_payload = payload
        self.waiting_for_ack = True
        self.ack_event.clear()


        self._send("DATA", payload)


        while self.waiting_for_ack:
            try:
                await asyncio.wait_for(self.ack_event.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                print(f"[{self.sensor.sensor_id}] ACK not received, resending DATA...")
                self._send("DATA", self.last_payload)
            else:

                break

    def datagram_received(self, data, addr):
        obj = parse_packet(data)
        if obj is None:

            print(f"[{self.sensor.device_type}] Received packet with bad CRC, ignoring")
            return
        msg_type = obj["msg_type"]
        if msg_type == "REGISTER_OK":
            self.token = obj["token"]
            print(f"Registered with token {self.token}")
        elif msg_type == "ACK":


            if self.waiting_for_ack:
                self.waiting_for_ack = False
                if not self.ack_event.is_set():
                    self.ack_event.set()
            # print(f"[{self.sensor.device_type}] ACK received")



        elif msg_type == "PING":
            if self.ignore_ping:
                self.ping_counter += 1
                print(f"[{self.sensor.sensor_id}] Ignoring PING #{self.ping_counter}")
                if self.ping_counter >= 3:
                    print(f"[{self.sensor.sensor_id}] Responding to 3rd PING — reconnecting")
                    self.ignore_ping = False
                    self.ping_counter = 0
        # new data after restart
                    if not self.running:
                        print(f"[{self.sensor.device_type}] Resuming periodic data sending after reconnection")
                        asyncio.create_task(self.periodic_send())
                else:
                    return
            self._send("PONG", {})

        elif msg_type == "RESEND":
            self.inject_errors = False
            print(f"[{self.sensor.device_type}] Server requested RESEND — resending last data")
            self._send("RESEND_RESPONSE", self.last_payload)
        elif msg_type == "INVALID_TOKEN":
            print(" Token invalid, re-registering...")
            self.register()

    # async def delayed_pong(self):
    #     await asyncio.sleep(40)
    #     print(f"[{self.sensor.device_type}] Sending PONG after 40s delay")
    #     self._send("PONG", {})

    def register(self):
        self._send("REGISTER", {})

    def send_data(self):
        payload = self.sensor.generate_payload()
        self.last_payload = payload
        self._send("DATA", payload)

    async def all_sensorsf(self):
        print(self.sensor.device_type,self.sensor.sensor_id)

    async def send_manual_data(self):

        payload = {}

        for k in self.sensor.generate_payload().keys():
            val = await ainput(f"Enter value for {k}: ")
            val = float(val)
            setattr(self.sensor, k, val)
            payload[k] = val

        print(f"Sending manual data for {self.sensor.device_type}: {payload}")
        await self.send_data_with_retry(payload)

    async def periodic_send(self):
        if self.running:
            return
        self.running = True

        while self.running:
            await asyncio.sleep(10)

            if not self.transport:
                print(f"[{self.sensor.device_type}] Transport closed — reconnecting")
                self.register()
                continue

            if not self.token:
                print(f"[{self.sensor.device_type}] No token, re-registering...")
                self.register()
                continue


            if self.waiting_for_ack:
                continue

            await self.send_data_with_retry()



