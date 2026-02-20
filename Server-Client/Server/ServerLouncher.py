import asyncio
import random

from Server.Server import SensorServer

from aioconsole import ainput
async def server_cli(protocol: SensorServer):
    while True:
        cmd = (await ainput("Server command (noack/exit): ")).strip().lower()
        if cmd == "exit":
            print("Stopping server CLI")
            break

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