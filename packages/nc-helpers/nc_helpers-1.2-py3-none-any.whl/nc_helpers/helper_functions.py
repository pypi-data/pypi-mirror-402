import ipaddress
import re

renaming_table = {
    "mgmt": ['mgmt', ],
    "Vlan": ['Vlan', 'Vl', 'vlan'],
    "Ethernet": ['Ethernet', 'eth' ],
    "FastEthernet": ['FastEthernet', 'Fa', 'FA'],
    "GigabitEthernet": ['GigabitEthernet', 'Gi', 'GI'],
    "TenGigabitEthernet": ['TenGigabitEthernet', 'TenGigE', 'Te'],
    "TwentyFiveGigabitEthernet": ['TwentyFiveGigabitEthernet', 'TwentyFiveGigE', ],
    "HundredGigabitEthernet": ['HundredGigabitEthernet', 'HundredGigE', ],
}

def convert_interface_name(interface_name):
    
    match = re.match(r"([a-z]+)([0-9\/]+)", interface_name, re.I)
    if match:
        items = match.groups()
        # print(items)
        for key, value in renaming_table.items():
            if items[0] in value:
                return f"{key}{items[1]}"
        # print(f"{interface_name} not found in lookup table")
    return interface_name



def expand_ipv6(address):
    """
    Convert a compressed IPv6 address to its full form.
    
    Args:
        address (str): Compressed IPv6 address
        
    Returns:
        str: Full expanded IPv6 address
        
    Examples:
        >>> expand_ipv6("2001:db8::1")
        '2001:0db8:0000:0000:0000:0000:0000:0001'
        
        >>> expand_ipv6("::1")
        '0000:0000:0000:0000:0000:0000:0000:0001'
    """
    try:
        # Use ipaddress module to handle the expansion
        ipv6_obj = ipaddress.IPv6Address(address)
        return str(ipv6_obj.exploded)
    except ipaddress.AddressValueError:
        try:
            ipv4_obj = ipaddress.IPv4Address(address)
            return address
        except ipaddress.AddressValueError:
            raise ValueError(f"Invalid address: {address}")
