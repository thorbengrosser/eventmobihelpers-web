import aiohttp
import csv
from flask import session
import asyncio
import requests

def get_session_uuid(api_key, event_id, session_external_id):
    url = f"https://uapi.eventmobi.com/events/{event_id}/sessions"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    params = {
        "external_id": session_external_id
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    if response.status_code == 200 and data.get("data"):
        return data["data"][0]["id"]
    return None

async def delete_session(auth_token, event_id, uuid):
    url = f"https://uapi.eventmobi.com/events/{event_id}/sessions/{uuid}"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {auth_token}"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=headers) as response:
            return await response.json()
async def delete_session(session, event_id, uuid, auth_token):
    url = f"https://uapi.eventmobi.com/events/{event_id}/sessions/{uuid}"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {auth_token}"
    }
    async with session.delete(url, headers=headers) as response:
        return await response.json()

async def handle_session(session, event_id, session_external_id, auth_token):
    uuid = await get_session_uuid(session, event_id, session_external_id, auth_token)
    if uuid:
        response = await delete_session(session, event_id, uuid, auth_token)
        return f"Deleting session {session_external_id} (UUID: {uuid}): {response}"
    else:
        return f"Failed to retrieve UUID for session {session_external_id}"

def fetch_events(api_key):
    url = "https://uapi.eventmobi.com/events"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
    return response.json().get('data', [])
