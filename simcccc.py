#!/usr/bin/env python3

"""
Serial Interactive Meshtastic Cusstom Channel Chat Client 0.1.0

Usage:
    python simcccc.py <SERIAL_PORT>

This script sends and receives text messages over the serial interface.
It uses PyPubSub to subscribe to text messages.
"""

import sys
import time
import asyncio
from pubsub import pub
from meshtastic.serial_interface import SerialInterface

# Custom channel configuration
CUSTOM_CHANNEL_NAME = "DC540"
CUSTOM_CHANNEL_PSK = "OVRpanBCYjZ2WmVIZTRheVlSZDZZWGxUcElFNFRSaWo="


def onReceive(packet=None, interface=None):
    """
    Callback function to process an incoming text message when the topic
    "meshtastic.receive.text" is published.

    Parameters:
        packet (dict, optional): A dictionary containing data about the received
            packet. Defaults to None if no packet info is supplied.
            If present, it may include:
              - 'decoded': A dictionary that may contain a 'text' key if the
                          packet is a text message.
              - 'fromId': (Optional) The identifier of the sender. If missing,
                          defaults to "unknown".
        interface (optional): The Meshtastic interface instance that received
            the packet (provided by the publisher). Unused here, but accepted
            to avoid pubsub errors.

    Side Effects:
        - If the packet contains a text message (under 'decoded.text'), it
          prints the sender ID and the message to standard output.
        - Prints a prompt ("Ch1> ") to indicate that further user input can be entered.

    Returns:
        None
    """
    if not packet:
        return  # no packet data, do nothing
    decoded = packet.get("decoded", {})
    if "text" in decoded:
        sender = packet.get("fromId", "unknown")
        message = decoded["text"]
        print(f"\n{sender}: {message}")
        print("Ch1> ", end="", flush=True)


async def main():
    """
    Main asynchronous entry point for the serial chat client.

    Steps:
      1. Reads the serial port (e.g., /dev/cu.usbserial-0001) from the command line.
      2. Creates a SerialInterface for that port (auto-connect).
      3. Waits briefly to stabilize the connection.
      4. Configures Channel 1 with a custom name and PSK.
      5. Subscribes to incoming text messages (via onReceive).
      6. Enters an interactive loop reading user input and sending messages on
         channelIndex=1, labeled as "Ch1> ".
      7. Closes the interface upon Ctrl+C (KeyboardInterrupt).

    Usage:
        python simcc_custom.py <SERIAL_PORT>

    Raises:
        Exception: If the serial connection fails to initialize.

    Side Effects:
        - Prints debug/info messages about the connection process.
        - Prompts for user input with "Ch1>" to send messages.
        - Exits gracefully on Ctrl+C.

    Returns:
        None
    """
    if len(sys.argv) < 2:
        print("Usage: python simcccc.py <SERIAL_PORT>")
        sys.exit(1)
    
    port = sys.argv[1].strip()
    print(f"Attempting to connect to Meshtastic device at serial port: {port}")

    try:
        iface = SerialInterface(devPath=port)
        print("Connected to Meshtastic device over serial!")
        # give a brief pause for the serial link to stabilize
        time.sleep(2)
    except Exception as e:
        print("Error initializing SerialInterface:", e)
        sys.exit(1)
    
    # configure Channel 1 with custom name and PSK
    try:
        print("Setting custom Channel 1 config (DC540 + custom PSK)...")
        node = iface.localNode
        ch1 = node.channels[1]  # channel index 1
        ch1.name = CUSTOM_CHANNEL_NAME
        ch1.psk = CUSTOM_CHANNEL_PSK  # base64 for 256-bit key
        ch1.usePreset = False  # disable built-in presets
        node.writeChannel(1)
        iface.writeConfig()
        print("Channel 1 set to DC540 with custom PSK.\n")
    except Exception as e:
        print("Error configuring Channel 1:", e)
    
    print("Serial Interactive Meshtastic Custom Channel Chat Client 0.1.0")
    print("--------------------------------------------------------------")
    print("Type your message and press Enter to send.")
    print("Press Ctrl+C to exit...\n")

    loop = asyncio.get_running_loop()
    try:
        while True:
            # non-blocking input for user messages
            msg = await loop.run_in_executor(None, input, "Ch1> ")
            if msg:
                # send text on channel index 1
                iface.sendText(msg, channelIndex=1)
                await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        iface.close()
        sys.exit(0)


if __name__ == "__main__":
    # subscribe to text messages topic, using our onReceive callback
    pub.subscribe(onReceive, "meshtastic.receive.text")

    asyncio.run(main())