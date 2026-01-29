import urllib
import requests
import getpass

import requests
from urllib3.exceptions import InsecureRequestWarning
import re
import json
import tempfile

from utils import *
from models import PanosConfig
from factories import *


"""
PanOS API integration
"""

def prettyprint_xml(xml_str: str, shorten=True) -> None:
    """
    Pretty prints an XML string in a tabular format, showing each tag and its content.

    Args:
        xml_str (str): XML string to pretty print.
    """
    # this method needs a lint roller... Fuzzy beast.
    def print_element(element, indent=0):
        prefix = "  " * indent
        if list(element):
            print(f"{prefix}{element.tag}:")
            for child in element:
                print_element(child, indent + 1)
        else:
            text = element.text.strip() if element.text else ""
            print(f"{prefix}{element.tag}: {text}")

    from xml.etree import ElementTree as ET
    # default response is always <response><result>...</result></response>
    # If shorten is True, only print the contents of <result> or <msg> if present
    try:
        root = ET.fromstring(xml_str)
        if shorten:
            # Try to find <result> or <msg> under <response>
            result = root.find("result")
            msg = root.find("msg")
            if result is not None:
                print_element(result)
                return
            elif msg is not None:
                print("Error Message:")
                print_element(msg)
                return
    except Exception:
        pass  # Fallback to full pretty print if parsing fails

    try:
        root = ET.fromstring(xml_str)
        print_element(root)
    except Exception as e:
        print("Failed to parse XML:", e)


def is_network_location(ip_address: str) -> bool:
    """
    Determines if the given IP address is a network location (i.e., matches regex).

    Args:
        ip_address (str): The IP address to check.
    Returns:
        bool: True if it's a network location, False otherwise.
    """
    # Regex for IPv4 address
    ip_pattern = r"^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}"
    fqdn_pattern = r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?"
    return (
        re.match(ip_pattern, ip_address) is not None
    ) or (
        re.match(fqdn_pattern, ip_address) is not None
    )


def build_xml_from_command(command_str: str) -> str:
    """
    Converts a space-separated command string into nested XML tags.
    Handles special cases like variables (starting with $) which are treated as values.

    Example:
        "show system info"
        -> "<show><system><info></info></system></show>"

        "show devices deviceid $DEVICE_ID"
        -> "<show><devices><deviceid>$DEVICE_ID</deviceid></devices></show>"

    Args:
        command_str (str): Command string.

    Returns:
        str: XML API Command string.
    """
    parts = command_str.strip().split()
    xml = ""
    stack = []

    i = 0
    while i < len(parts):
        part = parts[i]
        # If next part is a variable, treat as value
        if (i + 1 < len(parts)) and parts[i + 1].startswith("$"):
            xml += f"<{part}>{parts[i + 1]}</{part}>"
            i += 2
        else:
            xml += f"<{part}>"
            stack.append(part)
            i += 1

    # Close all opened tags
    while stack:
        xml += f"</{stack.pop()}>"

    return xml


class EzPanOS:
    def __init__(self, endpoint, username=None, password=None, api_key=None):
        # Disable warnings about insecure connections
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.api_key = api_key

        if not self.api_key:
            if self.username is None:
                self.username = input("Username: ")

            if self.password is None:
                self.password = getpass.getpass("Password: ")
        

            # Gets API key with credentials if api_key not overridden
            params = {
                "type": "keygen",
                "user": self.username,
                "password": self.password
            }
            url = f"https://{self.endpoint}/api?{urllib.parse.urlencode(params)}"
            self.api_key = requests.get(url, verify=False)
            if self.api_key.status_code == 200:
                # parse out API key from XML response
                from xml.etree import ElementTree as ET
                root = ET.fromstring(self.api_key.text)
                self.api_key = root.find(".//key").text   
            else:
                print("Failed to retrieve API key.")
                self.api_key = None

        self.panos = self.build_object()


    def build_object(self) -> object:
        # dataclass is literally dynamically generated
        config = self.get_configuration()
        return dict_to_dataclass('PanOS', config)

    def execute(self, command: str, api_type: str = "op", api_action: str | None = None, api_xpath: str | None = None) -> dict | None:
        """
        Docstring for execute
        
        :param self: PanOS Object
        :param command: PanOS CLI command string to execute
        :type command: str
        :param api_type: op (operational) | export | 
        :type api_type: str
        :param api_action: Description
        :return: dict of XML returned by the XML API or None if something fails.
        :rtype: dict[Any, Any] | None
        """

        xml_cmd = build_xml_from_command(command)
        try:
            headers = {
                "Content-Type": "application/xml"
            }
            params = {
                "type": api_type,
                "cmd": xml_cmd,
                "key": self.api_key
            }
            if api_action:
                params["action"] = api_action
            
            url = f"https://{self.endpoint}/api?{urllib.parse.urlencode(params)}"

            resp = requests.post(url, data=xml_cmd.encode('utf-8'), headers=headers, verify=False)
            # need to raise for status.
            resp.raise_for_status()
            # print(resp.text)

            return xml_string_to_dict(resp.text)

        except Exception as e:
            print("Error:", e)

    def get_configuration(self):
        """
        returns dictionary configuration, using tempfile for memory optimization. 
        """
        params = {
            "type": "export",
            "category": "configuration",
            "key": self.api_key,
        }
        URL = f"https://{self.endpoint}/api/?type=export&category=configuration&key={self.api_key}"

        # dump as xml first, convert to json then overwrite
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as out_file:
            # request configuration, stream output and write it to output file
            with requests.get(URL, params=params, stream=True, verify=False) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192, decode_unicode=False):
                    if chunk:
                        out_file.write(chunk)
            temp_file_path = out_file.name

        # Convert the temporary XML file to a dictionary
        result = xml_file_to_dict(temp_file_path)
        # Clean up the temporary file
        os.unlink(temp_file_path)
        return result

    def export_configuration(self, output_filename=None):
        params = {
            "type": "export",
            "category": "configuration",
            "key": self.api_key,
        }
        URL = f"https://{self.endpoint}/api/?type=export&category=configuration&key={self.api_key}"

        if output_filename is None:
            output_filename = f"{self.endpoint}_{get_current_time_string()}.json"

        # dump as xml first, convert to json then overwrite
        with open(output_filename, 'x') as out_file:
            # request configuration, stream output and write it to output file
            with requests.get(URL, params=params, stream=True, verify=False) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192, decode_unicode=True):
                    if chunk:
                        out_file.write(chunk)

        data = xml_file_to_dict(output_filename)
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


    '''
    Batch executes xml encoded Panorama commands
    '''
    def batch_execute(self, xml_commands: list[str], api_type: str = "op", api_action: str = None, api_xpath: str = None) -> list[str]:
        """
        Executes a batch of XML API commands (as strings) and returns their responses.

        Args:
            xml_commands (list[str]): List of XML-encoded command strings.
            api_type (str): API type parameter (default "op").
            api_action (str): API action parameter (optional).
            api_xpath (str): API xpath parameter (optional).

        Returns:
            list[str]: List of XML responses as strings.
        """
        headers = {
            "Content-Type": "application/xml"
        }
        responses = []
        for xml_cmd in xml_commands:

            params = {
                "type": api_type,
                "cmd": xml_cmd,
                "key": self.api_key
            }
            if api_action:
                params["action"] = api_action
            
            url = f"https://{self.endpoint}/api?{urllib.parse.urlencode(params)}"

            resp = requests.post(url, data=xml_cmd.encode('utf-8'), headers=headers, verify=False)
            # need to raise for status.
            resp.raise_for_status()
            responses.append(resp.text)
        return responses

    """============= PANOS Utility Functions =================="""

    def get_interfaces(self):
        return dataclass_to_dict(
            self.panos.config.devices.entry.network.interface
        )

    '''
    # attempt to resolve all routing tables unknown
    def get_routing_table(self):
        return dataclass_to_dict(
                self.panos.config.devices.entry.network
            )
    '''


    def resolve_ip_interface(self, ip: str):
        """
        Resolve an IP address to its source device/interface.
        
        Returns:
            dict with device, interface, cidr
            or None if not found

        """
        target_ip = ipaddress.ip_address(ip)

        layer3_devices = self.panos.config.devices.entry.network.interface.ethernet.entry
        ae_interfaces = self.panos.config.devices.entry.network.interface.aggregate_ethernet.entry
        layer3_devices = ensure_list(layer3_devices)
        ae_interfaces = ensure_list(ae_interfaces)

        cidr_tables = {}

        # standard L3 interfaces
        for device in layer3_devices:
            device_name = device.name

            # some interfaces do not have L3 configurations
            try:
                ip_entries = device.layer3
            except AttributeError:
                continue

            ip_entries = ensure_list(ip_entries)

            for ip_cidr in ip_entries:
                # print(vars(ip_cidr))
                # Skip DHClient interfaces
                try:
                    ip_entries = (
                        ip_cidr.ip.entry.name
                    )
                    ip_entries = ensure_list(ip_entries)

                    cidr_tables[device_name] = ip_entries
                except AttributeError:
                        continue 
                        
        # checking aggregate ethernet interface
        for device in ae_interfaces:
            device_name = device.name

            # some interfaces do not have L3 configurations
            try:
                ip_entries = device.layer3
            except AttributeError:
                continue

            ip_entries = ensure_list(ip_entries)

            for ip_cidr in ip_entries:
                # Skip DHClient interfaces / null L3 configs
                try:
                    ip_entries = (
                        ip_cidr.ip.entry.name
                    )
                    ip_entries = ensure_list(ip_entries)

                    cidr_tables[device_name] = ip_entries
                except AttributeError:
                    continue
        
        # checking tunnel interfaces etc...
        for interface, cidr in cidr_tables.items():
            for net in cidr:
                if contained_in(ip, net):
                    # print(interface, cidr)
                    # print(self.get_zone_by_interface(interface))
                    return {
                        "interface": interface,
                        "cidr": cidr,
                        "zone": self.get_zone_by_interface(interface)
                    }
        return None

    def get_zone_by_interface(self, interface):
        zones = ensure_list(self.get_zones())
        for zone in zones:
            zone_name = zone.name
            try:
                zone_members = ensure_list(zone.network.layer3.member)
                for member in zone_members:
                    if member == interface:
                        return zone_name

            except AttributeError:
                # L3 config is null, empty Zone
                continue

        return None

    def get_zone_by_ip_address(self, ip_address):
        # check interfaces by subnet, but also routing tables may be required.
        # 
        local_interface = self.resolve_ip_interface(ip_address)
        if local_interface is not None:
            return local_interface.get("zone")
        
        # the destination is not in the local config, must check routing table.

        routes = self.enumerate_routes()

        default_route_zone = 'default'
        for route, spec in routes.items():
            # check for default 0.0.0.0/0
            destination = spec.get('destination')
            route_zone = spec.get('destination_zone')

            if destination == '0.0.0.0/0':
                # skip default route for now, if no other routes contain destination
                default_route_zone = route_zone
            elif contained_in(ip_address, destination):
                return route_zone

        return default_route_zone
            
    
    def enumerate_routes(self):
        # local interface cache (more reliable for known configurations on host)
        virtual_routers = self.panos.config.devices.entry.network.virtual_router.entry
        virtual_routers = ensure_list(virtual_routers)

        route_dict = {}

        # check VRs first
        for router in virtual_routers:
            name = router.name
            # check static routes first
            routes = ensure_list(router.routing_table.ip.static_route.entry)
            # interfaces = ensure_list(router.interface.member)
            try:
                for route in routes:
                    route_dict[route.name] = {
                        "next_hop": route.nexthop.ip_address,
                        "interface": route.interface,
                        "destination": route.destination,
                        "destination_zone": self.get_zone_by_interface(route.interface)                        
                    }
            except AttributeError:
                # something odd about an entry....
                continue

        return route_dict

    def get_zones(self):
        return dataclass_to_dict(
            self.panos.config.devices.entry.vsys.entry.zone.entry
        )

    def get_dhcp(self):
        return ensure_list(
            dataclass_to_dict(
                self.panos.config.devices.entry.network.dhcp
            )
        )


if __name__ == "__main__":
    import sys
    # if cli parameter is '--interactive', run interactive CLI on target.
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        if len(sys.argv) > 2 and sys.argv[2] is not None:
            endpoint = sys.argv[2]
        else:
            endpoint = input("Enter PanOS/Panorama IP/FQDN: ")

        try:
            creds = {
                "username": input("Username: "),
                "password": getpass.getpass("Password: ")
            }
            pano = EzPanOS(endpoint, username=creds["username"], password=creds["password"])

            print("Interactive PanOS CLI. Type 'exit' to quit.")

            while True:
                cmd = input(f"{creds.get('username')}@{endpoint}> ")
                if cmd.strip().lower() in ['exit', 'quit']:
                    break
                if not cmd.strip():
                    continue
                xml_cmd = build_xml_from_command(cmd)
                try:
                    responses = pano.batch_execute([xml_cmd])
                    for response in responses:
                        prettyprint_xml(response)
                except Exception as e:
                    print("Error:", e)
        except KeyboardInterrupt:
            print("\nExiting interactive CLI.")

    else:
        # print usage
        print("Script Usage: python3 panorama.py --interactive")