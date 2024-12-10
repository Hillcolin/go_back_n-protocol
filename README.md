# Go-Back-N ARQ Protocol

This project implements the **Go-Back-N (GBN)** Automatic Repeat reQuest (ARQ) protocol, simulating reliable data transmission using sliding window protocols. The sender transmits data in packets, and the receiver acknowledges each packet. If a packet is lost or a timeout occurs, the sender retransmits the lost packet.

## How It Works

### Sender
- Divides the input data into packets and sends them in a sliding window manner.
- If a packet’s acknowledgment isn’t received within a timeout period, it retransmits that packet.
- Every nth packet is deliberately dropped (simulating packet loss) based on a configurable setting (`nth_packet`).

### Receiver
- Processes packets in order and acknowledges them.
- If packets arrive out of order, it acknowledges the last correctly received packet.
- After all packets are received, the receiver writes the data to an output file.

### Protocol Flow
1. **Sender**: Sends packets based on the window size, handles timeouts, and retransmits dropped packets.
2. **Receiver**: Acknowledges received packets and handles out-of-order packets.
3. If the receiver sends back an acknowledgment (`ACK`), the sender moves the window and sends the next packet.

## Setup

### Dependencies
- Python 3.x (no external libraries required).

### Usage

## Example Logs

### Sender Log:
```
Sender: sending packet 1
Sender: packet 2 dropped
Sender: packet 3 timed out, retransmitting
```

### Receiver Log:
```
Receiver: packet 1 received
Receiver: packet 2 received out of order
Receiver: packet 2 received
```

