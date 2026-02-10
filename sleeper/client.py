import requests

BASE_URL = "https://api.sleeper.app/v1"

class SleeperClient:
    def __init__(self, league_id: str):
        self.league_id = league_id
        self.session = requests.Session()
        self._roster_name_map = None

    def get_transactions(self, week: int):
        url = f"{BASE_URL}/league/{self.league_id}/transactions/{week}"
        r = self.session.get(url)
        r.raise_for_status()
        return r.json()
    
    def get_roster_name_map(self):
        """
        Returns { roster_id: display_name }
        Cached after first call.
        """
        if self._roster_name_map:
            return self._roster_name_map

        # Users
        users_url = f"{BASE_URL}/league/{self.league_id}/users"
        users = self.session.get(users_url).json()
        user_map = {u["user_id"]: u["display_name"] for u in users}

        # Rosters
        rosters_url = f"{BASE_URL}/league/{self.league_id}/rosters"
        rosters = self.session.get(rosters_url).json()

        roster_name_map = {}
        for r in rosters:
            owner_id = r.get("owner_id")
            roster_id = r["roster_id"]
            roster_name_map[roster_id] = user_map.get(owner_id, f"Team {roster_id}")

        self._roster_name_map = roster_name_map
        return roster_name_map
