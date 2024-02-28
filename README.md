# Servcy - One For All Platform

[Servcy](https://servcy.com) is an open-source software tool kit for all your business needs. We're going on an Open Source spree of creating business solutions.

> Servcy is still in its early days, not everything will be perfect yet, and hiccups may happen. Please let us know of any suggestions, ideas, or bugs that you encounter using GitHub issues, and we will use your feedback to improve on our upcoming releases.

The easiest way to get started with Servcy is by creating a [Servcy Cloud](https://web.servcy.com) account. Servcy Cloud offers a hosted solution for Servcy. If you prefer to self-host Servcy for your personal use, you're free to do so.

## Getting started

### Setup

1. Poetry should be installed
2. Python version 3.11.1
3. `cp config/config.ini.example config/config.ini`
4. `mkdir logs`
5. If you're in non-debug mode you'll need a new_relic.ini file under config directory
6. For google service you'll need servcy-gcp-service-account-key under config directory
7. Use sql seeders to prefill integration and integration_event table

### Installing Dependencies

```
poetry install
```

### Running server

```
poetry shell && python manange.py runserver
```

Open [http://localhost:8000](http://localhost:8000) with your browser to see the result.

You are ready to make changes to the code. Do not forget to refresh the browser (in case it does not auto-reload)

That's it!

## 📚Documentation

To see how to Contribute, visit [here](/CONTRIBUTING.md)

## ❤️ Community

The Servcy community can be found on GitHub Discussions, where you can ask questions, voice ideas, and share your projects.

Our [Code of Conduct](./CODE_OF_CONDUCT.md) applies to all Servcy community channels.

## ⛓️ Security

If you believe you have found a security vulnerability in Servcy, we encourage you to responsibly disclose this and not open a public issue. We will investigate all legitimate reports. Email [contact@servcy.com](mailto:contact@servcy.com) to disclose any security vulnerabilities.
