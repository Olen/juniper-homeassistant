# Integration to use the arp-table of a Juniper SRX as a device-tracker

Should work on all Juniper Layer 3 devices, but only tested on SRX

# Installation

Copy all the files to a folder under config/custom_components/ - e.g. `config/custom_components/juniper/`


# Usage

Add the following to configuration.yaml

```
device_tracker:
- platform: juniper
  username: !secret juniper_username
  password: !secret juniper_password
  host: juniper.host.name
  devices:
    - 'xx:yy:zz:aa:bb:cc'
    - '01:23:45:67:89:ab'
```

The mac-addresses specified under "devices" shows up as tracking-devices in HA and can be added to persons



