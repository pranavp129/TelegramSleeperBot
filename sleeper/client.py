import requests

BASE_URL = "https://api.sleeper.app/v1"

class SleeperClient:
    def __init__(self, league_id: str):
        self.league_id = league_id
        self.session = requests.Session()
        self._roster_name_map_cache = {}  # {season: {roster_id: display_name}}

    def get_league_info(self, league_id=None):
        league_id = league_id or self.league_id
        url = f"{BASE_URL}/league/{league_id}"
        r = self.session.get(url)
        r.raise_for_status()
        return r.json()

    def get_roster_name_map(self, league_id=None):
        """
        Returns { roster_id: display_name } for a given league.
        Caches results per league_id.
        """
        league_id = league_id or self.league_id
        if league_id in self._roster_name_map_cache:
            return self._roster_name_map_cache[league_id]

        # Users
        users_url = f"{BASE_URL}/league/{league_id}/users"
        users = self.session.get(users_url).json()
        user_map = {u["user_id"]: u["display_name"] for u in users}

        # Rosters
        rosters_url = f"{BASE_URL}/league/{league_id}/rosters"
        rosters = self.session.get(rosters_url).json()

        roster_name_map = {}
        for r in rosters:
            owner_id = r.get("owner_id")
            roster_id = r["roster_id"]
            roster_name_map[roster_id] = user_map.get(owner_id, f"Team {roster_id}")

        self._roster_name_map_cache[league_id] = roster_name_map
        return roster_name_map

    def get_all_previous_league_ids(self):
        """
        Walk back through previous leagues until there is no previous league.
        Returns a list of tuples: [(season, league_id), ...]
        """
        league_id = self.league_id
        seen = set()
        league_chain = []

        while league_id:
            # Avoid infinite loop if something unexpected repeats
            if league_id in seen:
                break
            seen.add(league_id)

            info = self.get_league_info(league_id)
            season = info.get("season", "Unknown")

            league_chain.append((season, league_id))

            prev = info.get("previous_league_id")
            # Stop if previous league is falsy (None or empty string)
            if not prev:
                break

            league_id = prev

        return league_chain

    def get_transactions(self, week: int, league_id=None):
        league_id = league_id or self.league_id
        url = f"{BASE_URL}/league/{league_id}/transactions/{week}"
        r = self.session.get(url)
        r.raise_for_status()
        return r.json()
