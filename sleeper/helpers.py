import json

# Load once at import time
with open("data/players.json", "r") as f:
    PLAYERS = json.load(f)

def get_player_name(player_id):
    """
    Returns full player name from Sleeper player_id.
    """
    player = PLAYERS.get(str(player_id))
    if player:
        return player.get("full_name", f"Unknown Player {player_id}")
    return f"Unknown Player {player_id}"

def get_player_id(player_name: str):
    """
    Returns the Sleeper player_id for a given full_name.
    Case-insensitive.
    """
    for pid, pdata in PLAYERS.items():
        if pdata.get("full_name", "").lower() == player_name.lower():
            return pid
    return None

def resolve_pick_status(client, asset):
    """
    Determines what to append to a draft pick message.

    Returns:
      - "" for picks not yet made
      - "(Player Name)" if the owner actually made the pick
      - "(Traded)" if the pick was moved to someone else
    """
    season = asset["season"]
    owner_id = asset["owner_id"]
    original_roster_id = asset["original_pick_roster"]
    round_ = asset["round"]

    original_owner = client.get_owner_id(season, original_roster_id)
    if original_owner is None:
        return ""  # future year or invalid roster
    asset["draft_slot"] = client.get_draft_position(season, original_owner)

    # Safety fallback
    draft_slot = asset.get("draft_slot", 0)
    if draft_slot == 0:
        return ""  # pick not yet made

    # Get draft_id for this season
    drafts_map = client.get_all_previous_draft_ids()
    draft_id = drafts_map.get(season)
    if not draft_id:
        return ""  # no draft info available

    # Fetch picks from API
    picks = client.get_draft_picks(draft_id)

    # Find the pick that matches round and draft_slot
    pick_info = next(
        (
            p for p in picks
            if p["round"] == round_ and p["draft_slot"] == draft_slot
        ),
        None
    )
    if not pick_info:
        return ""  # pick info not found

    actual_roster_id = pick_info["roster_id"]

    if actual_roster_id == owner_id:
        # Pick made by the owner who acquired it
        player_id = pick_info.get("player_id")
        player_name = get_player_name(player_id) if player_id else ""
        return f" ({player_name})" if player_name else ""
    else:
        # Pick moved to someone else
        return " (Traded)"

