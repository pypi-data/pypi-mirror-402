from __future__ import annotations

from influxdb import InfluxDBClient
import logging
log = logging.getLogger(__name__)


def write_influx_master(secrets: dict, data: dict, dryrun: bool = False) -> dict:
    """
    Write measurements to two InfluxDB instances.

    Returns a dict with per-host success booleans: {"ha": bool, "mons": bool}.
    """
    statuses = {"ha": False, "mons": False}

    # 1) HA influx (building_power DB)
    try:
        payload_ha = {
            "measurement": "power",
            "fields": {"kW": data["p_total_kW"]},
            "tags": {"success": "1"},
        }

        if dryrun:
            log.debug("HA dryrun payload: %s", payload_ha)
            statuses["ha"] = True
        else:
            try:
                ha = InfluxDBClient(
                    host=secrets["ha_ip"], port=8086,
                    username=secrets["ha_influx_username"],
                    password=secrets["ha_influx_pwd"],
                    timeout=5,
                )
            except Exception:
                log.exception("Creating HA InfluxDB client failed")
                ha = None

            if ha is not None:
                try:
                    ha.switch_database("building_power")
                    ha.write_points([payload_ha])
                    statuses["ha"] = True
                except Exception:
                    log.exception("Writing to HA influx failed")
                finally:
                    try:
                        ha.close()
                    except Exception:
                        pass

    except Exception:
        log.exception("Unexpected error preparing HA payload")

    # 2) mons influx (building DB)
    try:
        payload_mons = {
            "measurement": "power",
            "fields": {
                "power_kW": data["p_total_kW"],
                "current_L1_A": data["i_l1_A"],
                "current_L2_A": data["i_l2_A"],
                "current_L3_A": data["i_l3_A"],
                "voltage_L1N_V": data["u_l1_V"],
                "voltage_L2N_V": data["u_l2_V"],
                "voltage_L3N_V": data["u_l3_V"],
                "lg_connected": int(data["lg_connected"]) if data["lg_connected"] is not None else -1,
            },
            "tags": {"asset": "hak", "flow": "bidirectional"},
        }

        if dryrun:
            log.debug("mons dryrun payload: %s", payload_mons)
            statuses["mons"] = True
        else:
            try:
                mons = InfluxDBClient(
                    host=secrets["mons_ip"], port=8086,
                    username=secrets["mons_influx_username"],
                    password=secrets["mons_influx_pwd"],
                    timeout=5,
                )
            except Exception:
                log.exception("Creating mons InfluxDB client failed")
                mons = None

            if mons is not None:
                try:
                    mons.switch_database("building")
                    mons.write_points([payload_mons])
                    statuses["mons"] = True
                except Exception:
                    log.exception("Writing to mons influx failed")
                finally:
                    try:
                        mons.close()
                    except Exception:
                        pass

    except Exception:
        log.exception("Unexpected error preparing mons payload")

    return statuses



def write_influx_evse(secrets: dict, data: dict, dryrun: bool = False) -> dict:
    """
    Write measurements to two InfluxDB instances.

    Returns a dict with per-host success booleans: {"ha": bool, "mons": bool}.
    """
    statuses = {"ha": False, "mons": False}

    # 1) HA influx (building_power DB)
    try:
        payload_ha = {
            "measurement": "power",
            "fields": {"kW": float(data["power_kW"])},
            "tags": {"success": "1", 'charge':"1", 'user': data['user']}
        }

        if dryrun:
            statuses["ha"] = True
        else:
            try:
                ha = InfluxDBClient(
                    host=secrets["ha_ip"], port=8086,
                    username=secrets["ha_influx_username"],
                    password=secrets["ha_influx_pwd"],
                    timeout=5,
                )
            except Exception:
                log.exception("Creating HA InfluxDB client failed")
                ha = None

            if ha is not None:
                try:
                    ha.switch_database("building_power")
                    ha.write_points([payload_ha])
                    statuses["ha"] = True
                except Exception:
                    log.exception("Writing to HA influx failed")
                finally:
                    try:
                        ha.close()
                    except Exception:
                        pass

    except Exception:
        log.exception("Unexpected error preparing HA payload")

    # 2) mons influx (building DB)
    try:
        payload_mons = {
            "measurement": "power",
            "fields": {"kW": float(data["power_kW"])},
            "tags": {'asset': 'evse', 'evse_id': f"{int(data['user']):02d}", 'flow': 'consumption'},
        }
        payalod_mons_status = { 
            "measurement": "connector_status",
            "fields": {"status_code": int(data["connector_status"])},
            "tags": {'asset': 'evse', 'evse_id': f"{int(data['user']):02d}"}
        }



        if dryrun:
            log.debug("mons dryrun payload: %s", payload_mons)
            log.debug("mons dryrun status payload: %s", payalod_mons_status)
            statuses["mons"] = True
        else:
            try:
                mons = InfluxDBClient(
                    host=secrets["mons_ip"], port=8086,
                    username=secrets["mons_influx_username"],
                    password=secrets["mons_influx_pwd"],
                    timeout=5,
                )
            except Exception:
                log.exception("Creating mons InfluxDB client failed")
                mons = None

            if mons is not None:
                try:
                    mons.switch_database("building")
                    mons.write_points([payload_mons, payalod_mons_status])
                    statuses["mons"] = True
                except Exception:
                    log.exception("Writing to mons influx failed")
                finally:
                    try:
                        mons.close()
                    except Exception:
                        pass

    except Exception:
        log.exception("Unexpected error preparing mons payload")

    return statuses
