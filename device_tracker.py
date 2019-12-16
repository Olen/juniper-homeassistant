import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.device_tracker import (
    DOMAIN,
    PLATFORM_SCHEMA,
    DeviceScanner,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_PORT,
    CONF_DEVICES,
    CONF_EXCLUDE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HOST, default=""): cv.string,
        vol.Optional(CONF_USERNAME, default=""): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_PORT, default=None): vol.Any(None, cv.port),
        vol.Optional(CONF_DEVICES, default=[]): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_EXCLUDE, default=[]): vol.All(cv.ensure_list, [cv.string]),
    }
)

def get_scanner(hass, config):
    """Validate the configuration """
    info = config[DOMAIN]
    host = info.get(CONF_HOST)
    username = info.get(CONF_USERNAME)
    password = info.get(CONF_PASSWORD)
    port = info.get(CONF_PORT)
    devices = info.get(CONF_DEVICES)
    excluded_devices = info.get(CONF_EXCLUDE)

    scanner = JuniperSRXScanner(
        host, username, password, port, devices, excluded_devices
    )
    return scanner if scanner.success_init else None


class JuniperSRXScanner(DeviceScanner):
    def __init__(
        self,
        host,
        username,
        password,
        port,
        devices,
        excluded_devices
    ):
        self.tracked_devices = devices
        self.excluded_devices = excluded_devices
        from jnpr.junos import Device
        self._dev = Device(host=host, user=username, passwd=password)
        self._dev.open()

        self.success_init = self._dev.connected

        if self.success_init:
            results = self.get_arp_table()
            self.last_results = results
        else:
            _LOGGER.error("Failed to Login")


    def scan_devices(self):
        """Scan for new devices and return a list with found device IDs."""
        self._update_info()

        devices = []

        for entry in self.last_results['arp-table-information'][0]['arp-table-entry']:
            mac = entry['mac-address'][0]['data']
            ip = entry['ip-address'][0]['data']
            hostname = entry['hostname'][0]['data']
            tracked = (
                 not self.tracked_devices
                 or mac in self.tracked_devices
            )
            tracked = tracked and (
                not self.excluded_devices
                or not (
                    mac in self.excluded_devices
                )
            )
            if tracked:
                devices.append(mac)

        return devices

    def get_device_name(self, device):
        """Return the name of the given device or the MAC if we don't know."""
        parts = device.split("_")
        mac = parts[0]
        # name = parts[1]
        return mac

    def _update_info(self):
        """Retrieve latest information from the Juniper router.
        Returns boolean if scanning successful.
        """
        if not self.success_init:
            return

        _LOGGER.debug("Scanning ARP-table")

        results = self.get_arp_table()

        if results is None:
            _LOGGER.warning("Error scanning devices")

        self.last_results = results or []



    def get_dhcp_bindings(self):
        # Not used for now.  
        return self._dev.rpc.get_dhcp_server_binding_information({'detail': True, 'format': 'json'})

    def get_arp_table(self):
        return self._dev.rpc.get_arp_table_information({'no_resolve': True, 'format': 'json'})


