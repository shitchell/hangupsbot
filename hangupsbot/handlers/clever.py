import hangups

from hangupsbot.utils import text_to_segments
from hangupsbot.handlers import handler, StopEventHandling

import random
import cleverbot

@handler.register(priority=1, event=hangups.ChatMessageEvent)
def clever_responder(bot, event):
    """Handle clever replies to messages"""
    # Test if message is not empty
    if not event.text:
        return

    # Test if clever replies are enabled
    enabled = bot.get_config_suboption(event.conv_id, 'clever_enabled')
    if not enabled:
        return

    # Don't process anything that begins with the command character
    commands_character = bot.get_config_suboption(event.conv_id, 'commands_character')
    if event.text.startswith(commands_character):
        return

    # Determine odds of replying
    chance = bot.get_config_suboption(event.conv_id, 'clever_chance')
    if chance:
        # If we only reply to every 1/ X messages,
        # see if a random float is greater than those odds
        if random.random() > chance:
            return
    
    # Grab or create a cleverbot client for this chat
    client = cleverbot.clients.get(event.conv_id, cleverbot.Cleverbot())
    
    # Get a response from cleverbot
    response = client.ask(event.text)
    
    yield from event.conv.send_message(text_to_segments(response))
    
    # Stop other handlers from processing event
    raise StopEventHandling