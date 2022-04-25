# ha-emfitqs

**NOTE: Not maintained.**

A Home Assistant custom component that allows using the Emfit QS bed sensor to determine whether you're in bed or not.

## configuration.yml
```
# Emfit QS sleep sensor
emfitqs:
  hosts: !secret emfit_ip_address
  scan_interval: 10

```
