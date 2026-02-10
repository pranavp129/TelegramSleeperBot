import logging
import os
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler
from uuid import uuid4
from sleeper.client import SleeperClient
from sleeper.trades import extract_trade_details, find_trades_for_player
from sleeper.helpers import get_player_id, resolve_pick_status
from config.settings import OSU_DYNASTY_LEAGUE_ID

client = SleeperClient(OSU_DYNASTY_LEAGUE_ID)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a Sleeper Bot. Enter @Super_CTE_Bot to see a list of commands!")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query

    if not query:
        return

    results = [
        InlineQueryResultArticle(
            id="start",
            title="Start",
            description="Start Command",
            input_message_content=InputTextMessageContent(query.upper())
        ),
        InlineQueryResultArticle(
            id="trade_history",
            title="Trade History",
            description="Send a player's full name to find all trades with them involved. e.g. /TradeHistory Bryce Young",
            input_message_content=InputTextMessageContent(query.lower())
        ),
    ]

    await update.inline_query.answer(results)

async def trade_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Provide a player name, e.g. /TradeHistory Garrett Wilson")
        return

    player_name = " ".join(context.args)
    player_id = get_player_id(player_name)
    if not player_id:
        await update.message.reply_text(f"Player '{player_name}' not found.")
        return

    all_trades = []

    # Walk through all league years
    for season, league_id in client.get_all_previous_league_ids():
        roster_map = client.get_roster_name_map(league_id)

        # Only pass week function; find_trades_for_player handles week loop
        trades = find_trades_for_player(
            lambda w: client.get_transactions(w, league_id),
            player_id
        )

        for t in trades:
            t["season"] = season
            all_trades.append((t, roster_map))

    if not all_trades:
        await update.message.reply_text(f"No trades found for {player_name}.")
        return
    
    all_trades.sort(key=lambda x: (int(x[0]['season']), int(x[0]['week'])), reverse=True)

    # Format one message for all trades
    msg_lines = []
    for trade, roster_map in all_trades:
        assets_by_roster = extract_trade_details(trade)
        msg_lines.append(f"Year: {trade['season']}, Week: {trade['week']}")
        for roster_id, assets in assets_by_roster.items():
            team_name = roster_map.get(roster_id, f"Team {roster_id}")
            msg_lines.append(f"\n{team_name} received:")
            for asset in assets:
                if asset["type"] == "player":
                    msg_lines.append(f"- {asset['name']}")
                elif asset["type"] == "pick":
                    msg_lines.append(f"- {asset['season']} Round {asset['round']} Pick{resolve_pick_status(client, asset)}")
        msg_lines.append("---")

    await update.message.reply_text("\n".join(msg_lines))


if __name__ == '__main__':
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")
    
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    inline_caps_handler = InlineQueryHandler(inline_query)
    trade_history_handler = CommandHandler('TradeHistory', trade_history)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application.add_handler(start_handler)
    application.add_handler(inline_caps_handler)
    application.add_handler(trade_history_handler)
    application.add_handler(unknown_handler)
    
    application.run_polling()

# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Introduction-to-the-API
# https://docs.python-telegram-bot.org/en/stable/