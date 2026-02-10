import requests

BASE_URL = "https://api.sleeper.app/v1"

class SleeperClient:
    def __init__(self, league_id: str):
        self.BASE_URL = "https://api.sleeper.app/v1"
        self.league_id = league_id
        self.session = requests.Session()
        self._roster_name_map_cache = {}  # {season: {roster_id: display_name}}
        self._league_cache = None      # cache for previous leagues
        self._draft_cache = None         # cache for drafts per league_id

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
        Caches results in self._league_cache.
        """
        if self._league_cache:
            return self._league_cache

        league_id = self.league_id
        seen = set()
        league_chain = []

        while league_id:
            if league_id in seen:
                break
            seen.add(league_id)

            info = self.get_league_info(league_id)
            season = info.get("season", "Unknown")
            league_chain.append((season, league_id))

            prev = info.get("previous_league_id")
            if not prev:
                break
            league_id = prev

        self._league_cache = league_chain
        return league_chain

    def get_transactions(self, week: int, league_id=None):
        league_id = league_id or self.league_id
        url = f"{BASE_URL}/league/{league_id}/transactions/{week}"
        r = self.session.get(url)
        r.raise_for_status()
        return r.json()
    
    def get_rosters(self, league_id=None):
        league_id = league_id or self.league_id
        url = f"{self.BASE_URL}/league/{league_id}/rosters"
        r = self.session.get(url)
        r.raise_for_status()
        return r.json()
    
    def get_draft_picks(self, draft_id):
        """Return picks JSON for a given draft_id."""
        url = f"{BASE_URL}/draft/{draft_id}/picks"
        r = self.session.get(url)
        r.raise_for_status()
        return r.json()


    def get_drafts(self, league_id):
        """Return drafts JSON for a given league_id."""
        url = f"{BASE_URL}/league/{league_id}/drafts"
        r = self.session.get(url)
        r.raise_for_status()
        return r.json()

    def get_all_previous_draft_ids(self):
        """
        Returns dict: { season: draft_id }
        """
        if hasattr(self, "_draft_cache") and self._draft_cache:
            return self._draft_cache

        self._draft_cache = {}

        # Ensure league cache exists
        league_chain = self.get_all_previous_league_ids()

        for season, league_id in league_chain:
            drafts = self.get_drafts(league_id)
            if not drafts:
                continue

            # Sleeper usually has exactly one draft per league
            draft_id = drafts[0]["draft_id"]
            self._draft_cache[season] = draft_id

        return self._draft_cache
    
    def get_owner_id(self, season: str, roster_id: int):
        """
        Given a season and roster_id, return the associated owner_id.
        Uses league_chain from get_all_previous_league_ids.
        """
        # Find the league_id for the given season
        league_chain = self.get_all_previous_league_ids()
        league_id = None
        for s, l_id in league_chain:
            if s == season:
                league_id = l_id
                break

        if not league_id:
            return None

        # Fetch rosters for that league
        rosters = self.get_rosters(league_id)

        for roster in rosters:
            if roster["roster_id"] == roster_id:
                return roster["owner_id"]

        raise ValueError(f"No owner found for roster_id {roster_id} in season {season}")
    
    def get_draft_position(self, season: str, owner_id: str) -> int:
        """
        Returns the draft slot for an owner in a given season.
        """

        league_chain = self.get_all_previous_league_ids()

        league_id = next(
            (lid for s, lid in league_chain if s == season),
            None
        )

        if not league_id:
            return 0

        drafts = self.get_drafts(league_id)
        if not drafts:
            return 0

        for draft in drafts:
            draft_order = draft.get("draft_order")
            if not draft_order:
                continue

            if owner_id in draft_order:
                return draft_order[owner_id]

        return 0