from sleeper.helpers import get_player_name

def find_player_trades(transactions, player_id: str, week: int):
    results = []

    for txn in transactions:
        if txn["type"] != "trade":
            continue

        adds = txn.get("adds") or {}
        drops = txn.get("drops") or {}

        if player_id in adds or player_id in drops:
            results.append({
                "week": week,
                "transaction_id": txn["transaction_id"],
                "status": txn["status"],
                "roster_ids": txn["roster_ids"],
                "adds": adds,
                "drops": drops,
                "draft_picks": txn.get("draft_picks", [])
            })

    return results

def find_trades_for_player(transactions, player_id, start_week=1, end_week=18):
    """
    Returns a list of all trades (with full transaction data) that involve the given player_id
    over the specified week range.
    """
    trades = []
    for week in range(start_week, end_week + 1):
        txns = transactions(week)  # this should be a function that fetches the week's transactions
        for txn in txns:
            if txn.get("type") != "trade":
                continue
            adds = txn.get("adds") or {}
            drops = txn.get("drops") or {}
            if player_id in adds or player_id in drops:
                txn["week"] = week  # attach week info for convenience
                trades.append(txn)
    return trades


def extract_trade_details(trade):
    """
    Returns a dict keyed by roster_id showing what each roster RECEIVED.
    """
    roster_assets = {}

    def add_asset(roster_id, asset):
        roster_assets.setdefault(roster_id, []).append(asset)

    # Players
    adds = trade.get("adds") or {}
    drops = trade.get("drops") or {}

    for player_id, to_roster in adds.items():
        from_roster = drops.get(player_id)
        add_asset(
            to_roster,
            {
                "type": "player",
                "name": get_player_name(player_id),
                "from": from_roster
            }
        )

    # Draft picks
    for pick in trade.get("draft_picks", []):
        add_asset(
            pick["owner_id"],
            {
                "type": "pick",
                "round": pick["round"],
                "season": pick["season"],
                "from": pick["previous_owner_id"]
            }
        )

    return roster_assets
