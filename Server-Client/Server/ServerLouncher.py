import asyncio
import random

from aioconsole import ainput

from Server.ServerM import SensorServer

async def server_cli(protocol: SensorServer):
    while True:
        cmd = (await ainput("Server command (noack/exit): ")).strip().lower()
        if cmd == "exit":
            print("Stopping server CLI")
            break
        elif cmd == "noack":

            if not protocol.sensors:
                print("No sensors registered yet.")
                continue
            print("Registered sensors:")
            for d, s in protocol.sensors.items():
                print(f"- {s.sensor_id} ({d})")
            sid = (await ainput("Enter sensor_id for no-ACK mode: ")).strip().upper()
            if any(s.sensor_id == sid for s in protocol.sensors.values()):
                protocol.set_no_ack(sid, count=3)
            else:
                print("Unknown sensor_id")
        else:
            print("Unknown command")
async def main():
    server_ip = input("Enter server IP [127.0.0.1]: ") or "127.0.0.1"
    server_port = int(input("Enter server port [9999]: ") or 9999)
    server_addr = (server_ip, server_port)

    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: SensorServer(),
        local_addr=server_addr
    )


    await asyncio.gather(
        protocol.monitor(),
        server_cli(protocol)
    )

if __name__ == "__main__":
    asyncio.run(main())