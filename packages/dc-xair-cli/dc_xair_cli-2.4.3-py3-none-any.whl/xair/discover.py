"""Network discovery for XAir/MR mixers."""

import socket
import time


def discover_mixers(timeout: float = 3.0) -> list[dict]:
    """Discover XAir/MR mixers on the network via UDP broadcast.

    Args:
        timeout: How long to wait for responses in seconds.

    Returns:
        List of discovered mixers with ip, model, and name.
    """
    mixers = []

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(min(timeout, 0.5))  # Short timeout for each recv

        # XAir uses OSC over UDP on port 10024
        # Send /xinfo query - OSC format: address + type tag
        osc_message = b"/xinfo\x00\x00,\x00\x00\x00"
        sock.sendto(osc_message, ("<broadcast>", 10024))

        start = time.time()
        while time.time() - start < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                mixer_info = _parse_xinfo_response(data, addr[0])
                if mixer_info and mixer_info not in mixers:
                    mixers.append(mixer_info)
            except socket.timeout:
                continue
            except OSError:
                break

        sock.close()
    except OSError:
        pass  # Network unavailable or permission denied

    return mixers


def _parse_xinfo_response(data: bytes, ip: str) -> dict | None:
    """Parse OSC /xinfo response.

    Returns dict with ip, model, name or None if parsing fails.
    """
    try:
        parts = data.split(b"\x00")
        strings = [p.decode("utf-8", errors="ignore") for p in parts if p]

        if len(strings) >= 4:
            return {
                "ip": ip,
                "name": strings[2] if len(strings) > 2 else "Unknown",
                "model": strings[3] if len(strings) > 3 else "Unknown",
            }
    except (IndexError, UnicodeDecodeError):
        pass

    return None
