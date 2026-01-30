# Various ToDos


## Poller

- [x] [influx_writes.py](influx_writes.py) actually need the wifi checking

### What do I need to understand

- [x] [aync_tools.py](async_tools.py)
    - Creates a pool of threads for asyncio
    - Defines pool size
    - relays `*args` and `**kwargs` to passed function 
- [x] [config.py](config.py)
    - Reads in configurations from a file `secrets.yml`
- [x] [device.py](device.py)
    - I understood basic principles of hirachical loggin
    - I understood that `@dataclass` just produces standard `__init__` and other methods for classes that are mostly data (think of it as dict+)
    - `poll_modbus_async` can check for wifi and has exponential back-off implemented. Hopefully not needed now that `ceorl` is in ethernet of garage. 
- [x] [influx_writes.py](influx_writes.py)
    - writes messages to influxdb on ha and mons
- [x] [main.py](main.py)
    - defines logging level
    - defines the functions which will be run in the loop
    - inside the main
        - Creates a list of devices
        - Creates a list of tasks
        - Runs the tasks in a loop
- [x] [modbus_reads.py](modbus_reads.py)
    - knows how to cast binary stuff into readable messages
    - Has functions that poll specific things. 
        - Building power / currents
        - ..

        Each of those returns a dict that [influx_writes.py](influx_writes.py) will know what to do.
- [x] [wifi.py](wifi.py)
    - checks via `iw` if wifi link is healthy ( `iw` must be present in system!)

---
Overall: main.py imports devices, devices have the connection as member, for a device there needs to be function which unpacks that connection, "*_reads.py" and "*_writes.py" will use that connection. 

## Watchdog

### Algodue watchdog

```bash
curl -sS -c /tmp/algodue.cookie \
  -X POST http://ALGODUE_IP/index.htm \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data 'user=admin&password=admin'
```

This stores the auth cookie. Then 
```bash
curl -sS -b /tmp/algodue.cookie \
  -X POST http://ALGODUE_IP/parameters_change.htm \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data 'addressingType=Static' \
  --data 'host_name=ETHBOARD' \
  --data 'IP=192.168.1.249' \
  --data 'gateway=192.168.1.1' \
  --data 'mask=255.255.255.0' \
  --data 'primary_dns=8.8.8.8' \
  --data 'secondary_dns=8.8.4.4' \
  --data 'logical_addr=01' \
  --data 'chbSyncWithNTP=on' \
  --data 'ntp_server=europe.pool.ntp.org' \
  --data 'utc_correction=%2B01'
```

