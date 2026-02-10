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
