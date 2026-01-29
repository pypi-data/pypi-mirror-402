# pyninaapiio

Wrapper for the ***[N.I.N.A. Advanced API](https://github.com/christian-photo/ninaAPI)*** RESTful API. Designed to work with Home Assistant and the custom [NinaAPI](https://github.com/mawinkler/ninaapi) integration.

## Functions

The module exposes the following function:

```python
ninaapi = NinaAPI(
    session,
    base_url=entry.options.get(CONF_BASE_URL),
    application_enabled=True,
    camera_enabled=True,
    dome_enabled=True,
    filterwheel_enabled=True,
    focuser_enabled=True,
    guider_enabled=True,
    image_enabled=True,
    mount_enabled=True,
    safety_monitor_enabled=True,
    rotator_enabled=True,
    switch_enabled=True,
    weather_enabled=True,
    api_timeout=10,
)

ninaapi.nina_info
```

This will return a handle to the NinaAPI class.

## Setup

```sh
pip3 install .
```

## Build

```sh
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Test

```sh
python -m unittest -v tests/client.py
```
