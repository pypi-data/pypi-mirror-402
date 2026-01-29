import asyncio
from concurrent.futures import ThreadPoolExecutor

from influxdb import InfluxDBClient
from evse_hub.ops.heartbeat import Heartbeat, HeartbeatConfig, make_influxdb_client_18
from evse_hub.tools.config import load_secrets

secrets= load_secrets("secrets.yml")


async def main():
    hb = Heartbeat.create_with_influxdb(
        host=secrets['mons_ip'],
        database=secrets['ops_db_name'],
        service="solar-hubd-test",
        version="0.1.0",
        username=secrets['mons_influx_username'],
        password=secrets['mons_influx_pwd']
    )

    # periodic heartbeat
    try:
        while True:
            ok = await hb.write_async(alive=1)
            await asyncio.sleep(secrets.get('heartbeat_interval_s', 5))
    except asyncio.CancelledError:
        await hb.write_async(alive=0)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested")
