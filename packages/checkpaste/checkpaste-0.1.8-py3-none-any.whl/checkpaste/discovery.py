import socket
from zeroconf import Zeroconf, ServiceInfo, ServiceBrowser, ServiceStateChange
from typing import Optional
import time

SERVICE_TYPE = "_checkpaste._tcp.local."

class ServiceListener:
    def __init__(self, target_name: str):
        self.target_name = target_name
        self.found_info = None

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        # Check if this is the service we are looking for
        # Name format usually: "Instance Name._checkpaste._tcp.local."
        friendly_name = name.replace("." + type_, "")
        
        if friendly_name == self.target_name:
            info = zc.get_service_info(type_, name)
            if info:
                self.found_info = info

def register_service(name: str, port: int):
    """
    Register the checkpaste service on the network.
    """
    zeroconf = Zeroconf()
    
    # Get local IP
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    try:
        # Sometimes gethostbyname returns 127.0.0.1, try connected socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        pass

    desc = {'version': '0.1.0'}
    
    info = ServiceInfo(
        SERVICE_TYPE,
        f"{name}.{SERVICE_TYPE}",
        addresses=[socket.inet_aton(local_ip)],
        port=port,
        properties=desc,
        server=f"{hostname}.local.",
    )
    
    zeroconf.register_service(info)
    return zeroconf, info

def find_service(name: str, timeout: int = 5) -> Optional[tuple[str, int]]:
    """
    Search for a checkpaste service by name.
    Returns (host_ip, port) if found, else None.
    """
    zeroconf = Zeroconf()
    listener = ServiceListener(name)
    browser = ServiceBrowser(zeroconf, SERVICE_TYPE, listener)
    
    start_time = time.time()
    try:
        while time.time() - start_time < timeout:
            if listener.found_info:
                info = listener.found_info
                address = socket.inet_ntoa(info.addresses[0])
                return address, info.port
            time.sleep(0.1)
    finally:
        zeroconf.close()
    
    return None
