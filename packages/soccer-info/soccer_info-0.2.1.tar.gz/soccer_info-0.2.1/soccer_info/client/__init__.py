"""Client module for Soccer Football Info API."""
from soccer_info.client.sync.httpclient import HTTPXClient
from soccer_info.client.async_.async_httpclient import AsyncHTTPXClient
from soccer_info.client.sync.client import Client
from soccer_info.client.async_.async_client import AsyncClient

__all__ = ['HTTPXClient', 'AsyncHTTPXClient', 'Client', 'AsyncClient']
