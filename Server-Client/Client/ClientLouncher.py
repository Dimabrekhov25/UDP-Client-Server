import asyncio
from asyncio import create_task

from aioconsole import ainput

async def cli(clients):

    while True:
        try:
            cmd = await ainput("> ")
        except (EOFError, KeyboardInterrupt):
            print("exit")
            return
        cmd = cmd.strip()
        if not cmd:
            continue
        if cmd in {"exit", "quit"}:
            return

async def main():

    clients = []
    await cli(clients)

if __name__ == "__main__":
    asyncio.run(main())
