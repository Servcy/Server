# Servcy - One For All Platform

- Save your hours, and effort. Manage all your clients from the same platform.

## Features

1. Passwordless authentication using Twilio & SendGrid RESTful APIs
   - Supports Whatsapp, Email & Phone number as OTP channel

## Getting started

### Setup Prerequisites

1. Poetry should be installed
2. Python version 3.11.1
3. `cp config/config.ini.example config/config.ini`
4. `mkdir logs`

### Installing Dependencies

```
poetry install
```

### Running server

```
poetry shell && python manange.py runserver
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.
