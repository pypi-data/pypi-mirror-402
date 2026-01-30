#  Architecture

## General structure


> **Mission statement**
> 
> We log building electricity consumption and PV production and allow users to **charge their EV conditioned on PV over-production**. Data for informative user dashboards is written to an influxDB.

### Logging

We need to log from the algoDue load Guard to get the total current (positive or negative) to the house. We also want to get data out of the PV inverter to have the actual production data. We want to know the SOC of the building battery. We poll all EVSEs to know their current state (charging / cable connected / etc).

We also want to know when additional EVSEs come online. Need to think about that later. 

### Control

We want to set a max current on all EVSE:

- lift current limit for immediated charging
- time-dependent current limit for night-charging
- set adaptive current depending on solar state (SOC and/or actual over-prxoduction)


We also want a watchdog to restart the algoDue in case it stops communicating with the master EVSE (timing issue).

### Software structure

Decision between the following general approaches

- One service fetches all necessary data stores it in a state variable and bases control decisions on those. It also stores the data and a heartbeat to the influxdb and controls the current limits on the EVSEs.

- Serveral services
    - One only fetches data from buidling (algoDue, inverter, SOC,...). And publishes those via MQTT and/or influxdb. Maybe I sperated this into two more services yet
        - building stuff
        - EVSE stuf
    - One only controls the currents on the EVSEs

I like the one service approach better because it requires less inter-process communication. But I want to get almost all the live data out to my influxdb instances anyway. So, maybe that argument does not hold. I like the multi service variant better because each service is less complex and there is a clear separation between data gathering and storing and control. One thing I do not understand yet: my EVSEs allow communication via modbus registers. Reading via port 502, writing via port 503. Can I separate this into two services, or exactly not? Another thing to think about: the master EVSE provides via it's port 502 registers both access to the EVSE details like cable connected, current charging power, etc., and also the data from the loadguard. Maybe the service which polls the EVSE has a device class which knows the attribute *master-EVSE*.



