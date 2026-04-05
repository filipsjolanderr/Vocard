import aiohttp
import base64
import time
import re
from typing import List, Dict, Any, Optional

SPOTIFY_URL_REGEX = re.compile(
    r"https?://open\.spotify\.com/(?P<type>track|album|playlist)/(?P<id>[a-zA-Z0-9]+)"
)

class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: Optional[str] = None
        self.expires_at: float = 0
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _get_access_token(self) -> str:
        if self.access_token and time.time() < self.expires_at:
            return self.access_token

        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()

        session = await self._get_session()
        async with session.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {auth_b64}"}
        ) as resp:
            data = await resp.json()
            self.access_token = data["access_token"]
            self.expires_at = time.time() + data["expires_in"] - 60
            return self.access_token

    async def get_records(self, url: str) -> List[Dict[str, Any]]:
        match = SPOTIFY_URL_REGEX.match(url)
        if not match:
            return []

        type = match.group("type")
        spotify_id = match.group("id")
        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        session = await self._get_session()

        if type == "track":
            async with session.get(f"https://api.spotify.com/v1/tracks/{spotify_id}", headers=headers) as resp:
                data = await resp.json()
                return [{"title": data["name"], "author": ", ".join(a["name"] for a in data["artists"]), "uri": data["external_urls"]["spotify"]}]

        elif type == "album":
            async with session.get(f"https://api.spotify.com/v1/albums/{spotify_id}", headers=headers) as resp:
                data = await resp.json()
                return [{"title": t["name"], "author": ", ".join(a["name"] for a in t["artists"]), "uri": t["external_urls"]["spotify"]} for t in data["tracks"]["items"]]

        elif type == "playlist":
            tracks = []
            next_url = f"https://api.spotify.com/v1/playlists/{spotify_id}/tracks"
            while next_url:
                async with session.get(next_url, headers=headers) as resp:
                    data = await resp.json()
                    for item in data["items"]:
                        if not item.get("track"):
                            continue
                        track = item["track"]
                        tracks.append({
                            "title": track["name"],
                            "author": ", ".join(a["name"] for a in track["artists"]),
                            "uri": track["external_urls"]["spotify"]
                        })
                    next_url = data.get("next")
            return tracks

        return []
