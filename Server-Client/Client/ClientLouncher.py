import asyncio
from asyncio import create_task

from aioconsole import ainput
from Client.ClientM import DeviceClient
from Client.Sensors.ThermoNode import ThermoNode
from Client.Sensors.WindSense import WindSense
from Client.Sensors.RainDetect import RainDetect
from Client.Sensors.AirQualityBox import AirQualityBox


async def cli(clients):

    while True:
        async def safe_input(prompt: str):

            print("", flush=True)
            await asyncio.sleep(0.05)
            return await ainput(prompt)

        cmd = (await safe_input("Command (start/stop/inject/inject_error/all_sensors/manual(sensor number)/deactivate(sensor number) on/off/battery low/exit): ")).strip().lower()
        print("", flush=True)
        if cmd == "exit":
            for c in clients:
                c.running = False
            print("Exiting tester")
            await asyncio.sleep(1)
            break
        elif cmd == "all_sensors":
            for c in clients:
                asyncio.create_task(c.all_sensorsf())

        elif cmd == "manual":
            print("Manual data input mode")
            for i, c in enumerate(clients):
                print(f"{i + 1}. {c.sensor.device_type}")
            idx = int(await ainput("Select sensor number: ")) - 1
            if 0 <= idx < len(clients):
                await clients[idx].send_manual_data()
            else:
                print("Invalid choice")

        elif cmd == "start":
            for c in clients:
                if not c.running:
                    print(f"Starting {c.sensor.device_type}")
                    c.token = None
                    asyncio.create_task(c.periodic_send())


        elif cmd.startswith("deactivate"):
            parts = cmd.split()
            if len(parts) != 2:
                print("Usage: deactivate <sensor_id>")
            else:
                sid = parts[1].upper()
                for c in clients:
                    if c.sensor.sensor_id == sid:
                        c.ignore_ping = True
                        c.running = False
                        print(f"Sensor {sid} deactivated (will ignore PING)")
        elif cmd == "stop":
            for c in clients:
                if c.running:
                    print(f"Stopping {c.sensor.device_type}")
                    c.running = False
        elif cmd.startswith("inject_error"):
            parts = cmd.split()
            if len(parts) != 2:
                print("Usage: inject_error <sensor_id>")
            else:
                sid = parts[1].upper()
                found = False
                for c in clients:
                    if c.sensor.sensor_id == sid:
                        c.inject_errors = True
                        print(f"Error injection enabled for {sid}")
                        found = True
                if not found:
                    print(f"No sensor found with ID {sid}")
        elif cmd.startswith("inject"):
            parts = cmd.split()
            if len(parts) == 2 and parts[1] in ("on", "off"):
                state = parts[1]
                for c in clients:
                    c.inject_errors = (state == "on")
                print(f"Error injection set to {state}")
            else:
                print("Usage: inject on/off")

        elif cmd.startswith("battery"):
            parts = cmd.split()
            if len(parts) == 2 and parts[1] in ("low", "normal"):
                state = parts[1]
                for c in clients:
                    c.sensor.low_battery = (state == "low")
                print(f"Battery mode set to {state}")
            else:
                print("Usage: battery low/normal")

        else:
            print("Unknown command")



async def main():
    sensors = [
        ThermoNode("T1"),
        WindSense("W1"),
        RainDetect("R1"),
        AirQualityBox("A1"),
    ]
    tester_ip = input("Enter server IP [127.0.0.1]: ") or "127.0.0.1"
    tester_port = int(input("Enter server port [9999]: ") or 9999)
    server_addr = (tester_ip, tester_port)

    #server_addr = ("127.0.0.1", 5555)
    loop = asyncio.get_running_loop()
    clients = []

    for s in sensors:
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: DeviceClient(s, server_addr),
            remote_addr=server_addr
        )
        clients.append(protocol)

    print("All sensors initialized. Use 'start' to begin sending data.")
    await cli(clients)


if __name__ == "__main__":
    asyncio.run(main())
