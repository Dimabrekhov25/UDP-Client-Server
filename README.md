📡 Async Sensor Monitoring System

This project is an asynchronous sensor monitoring system implemented in Python (asyncio + UDP).
The system consists of:

🖥 UDP Server

📡 Sensor Clients (Sensor Devices)

🔹 Core Functionality
Device registration with token issuance
Data transmission with acknowledgment (ACK)
Automatic data retransmission when ACK is lost
Packet integrity verification using CRC16
Corrupted packet handling (RESEND mechanism)
Device activity monitoring (PING / PONG keepalive)
Sensor disconnection detection
Low battery state handling
Transmission error simulation for testing

🔹 Technologies
Python 3
asyncio
UDP (DatagramProtocol)
CRC16 checksum validation
aioconsole (for manual data input)

🔹 Implementation Features
Fully non-blocking asynchronous architecture
Retry mechanism for lost acknowledgments
Server-side device state tracking
Automatic client reconnection
Network failure and fault simulation capabilities
