from __future__ import annotations

from .influx_client import pool
import logging
log = logging.getLogger(__name__)


def write_influx_master(secrets: dict, data: dict, dryrun: bool = False) -> dict:
    """Write measurements to two InfluxDB instances."""
    # Initialize pool on first call
    if pool._secrets is None:
        pool.initialize(secrets)
    
    statuses = {"ha": False, "mons": False}

    # 1) HA influx
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
            statuses["ha"] = pool.write_ha("building_power", payload_ha)

    except Exception:
        log.exception("Unexpected error preparing HA payload")

    # 2) mons influx
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
            statuses["mons"] = pool.write_mons("building", payload_mons)

    except Exception:
        log.exception("Unexpected error preparing mons payload")

    return statuses


def write_influx_evse(secrets: dict, data: dict, dryrun: bool = False) -> dict:
    """Write measurements to two InfluxDB instances."""
    if pool._secrets is None:
        pool.initialize(secrets)
    
    statuses = {"ha": False, "mons": False}

    # 1) HA influx
    try:
        payload_ha = {
            "measurement": "power",
            "fields": {"kW": float(data["power_kW"])},
            "tags": {"success": "1", 'charge': "1", 'user': data['user']}
        }

        if dryrun:
            statuses["ha"] = True
        else:
            statuses["ha"] = pool.write_ha("building_power", payload_ha)

    except Exception:
        log.exception("Unexpected error preparing HA payload")

    # 2) mons influx
    try:
        payload_mons = {
            "measurement": "power",
            "fields": {"power_kW": float(data["power_kW"])},
            "tags": {'asset': 'evse', 'evse_id': f"{int(data['user']):02d}", 'flow': 'consumption'},
        }
        payload_mons_status = {
            "measurement": "connector_status",
            "fields": {"status_code": int(data["connector_status"])},
            "tags": {'asset': 'evse', 'evse_id': f"{int(data['user']):02d}"}
        }

        if dryrun:
            log.debug("mons dryrun payload: %s", payload_mons)
            log.debug("mons dryrun status payload: %s", payload_mons_status)
            statuses["mons"] = True
        else:
            # Write to building DB
            success1 = pool.write_mons("building", payload_mons)
            # Write to ops DB
            success2 = pool.write_mons("ops", payload_mons_status)
            statuses["mons"] = success1 and success2
            
            if statuses["mons"]:
                log.debug("Wrote EVSE data to mons influx: evse_id=%s power_kW=%.2f connector_status=%d",
                         data['user'], float(data["power_kW"]), int(data["connector_status"]))

    except Exception:
        log.exception("Unexpected error preparing mons payload")

    return statuses
