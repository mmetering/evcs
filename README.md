# evcs – Electrical Vehicle Charging Station

This django application is an extension for [mmetering](http://mmetering.chrisonntag.com) in order to model an
electrical vehicle charging station, where users identify themselves through an RFID chip mapped to their apartment.

The energy consumption is then written to the corresponding apartment.

## Installation

Just clone this repository into your [mmetering installation](http://mmetering.chrisonntag.com) as a new django
application and add it to the ```INSTALLED_APPS``` list in your production settings file.

```bash
git clone https://github.com/mmetering/evcs.git evcs
```

```python
INSTALLED_APPS = [
    ...
    'backend',
    'mmetering',
    ...
    'evcs',
]
```

### Docker Compose
Add the following lines to the main ```docker-compose.yml``` file as its own service.

```yaml
  evcs:
    build: .
    container_name: mmetering_evcs
    privileged: "true"
    command: bash -c "python /mmetering-server/manage.py runevcs"
    restart: on-failure:3
    volumes:
      - ./mmetering-server
    networks:
      - main
    depends_on:
      - web
      - db
```


## MCSP/1.0 - MMetering Charging Station Protocol (not implemented)

Below is an example for both a successful and a faulty conversation between a charging station (client) and the MMetering  
instance (server). A user identifies himself with a RFID-chip belonging to his apartment, the client box then sends a ```START``` 
message to the server containing all relevant information ([1]).
After checking the RFID-apartment relation for correctness the server starts a 'session' and allocates its session id to the client 
(see [2]).

![MMetering Charging Station Protocol](https://github.com/mmetering/evcs/blob/master/docs/images/MCSP_example.jpg "MCSP")

The evcs-clients and the server communicate by sending plain-text ASCII messages. The client sends control information to the server which
then responds accordingly.

### Client messages
A message coming from the client consists of the following:
    - The protocol name plus it's version number and an action keyword which can be either ```START``` or ```END```.
    - Content-Length header field
    - The name/id of the client device
    - The RFID key
    - The Session-Id (optional, only on the end of the session)

### Server response messages
tbd

### Error Codes
tbd

