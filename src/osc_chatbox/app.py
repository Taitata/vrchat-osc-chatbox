
import argparse
from .config import SETTINGS
from .osc_io import ChatboxClient

def main(argv=None):
    parser = argparse.ArgumentParser(description="Send a message to VRChat Chatbox via OSC (Part 1).")
    parser.add_argument("--say", type=str, help="Message to send to VRChat chatbox.")
    args = parser.parse_args(argv)

    if not args.say:
        parser.error("--say is required")

    client = ChatboxClient(
        host=SETTINGS.vrchat_ip,
        port=SETTINGS.osc_in_port,
        max_len=SETTINGS.chatbox_max_len,
        debug=SETTINGS.debug,
    )

    try:
        client.typing(True)
        client.say(args.say, press_enter=True)
    finally:
        client.typing(False)

if __name__ == "__main__":
    main()
