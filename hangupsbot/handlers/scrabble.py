import hangups

from hangupsbot.utils import text_to_segments, bold, italicize
from hangupsbot.handlers import handler, StopEventHandling

import enchant

dictionary = enchant.Dict('en_US')

@handler.register(priority=1, event=hangups.ChatMessageEvent)
def scrabble_responder(bot, event):
    """Handle clever replies to messages"""
    # Test if message is not empty
    if not event.text:
        return
    
    # Define some shit
    scrabble_args = ['conversations', event.conv_id, 'scrabble']
    word = event.text.lower()
    
    # Test if message is one word
    if ' ' in event.text:
        return
    
    # Test if a scrabble game is ongoing
    try:
        letters = bot.config.get_by_path(scrabble_args + ['letters'])
    except:
        letters = None
    if not letters:
        return

    # Don't process anything that begins with the command character
    commands_character = bot.get_config_suboption(event.conv_id, 'commands_character')
    if event.text.startswith(commands_character):
        return
    
    # Make sure that the word hasn't been guessed yet
    if word in bot.config.get_by_path(scrabble_args + ['guesses']):
        text = '{}\n{} has already been guessed!'.format(
            bold(' '.join(letters)),
            italicize(word)
        )
        yield from event.conv.send_message(text_to_segments(text))
        raise StopEventHandling

    # Determine if the letters given match the current set
    remaining = letters.copy()
    for letter in word:
        try:
            remaining.remove(letter)
        except:
#            yield from event.conv.send_message(text_to_segments("Those letters don't even match..."))
#            raise StopEventHandling
            return
    
    # Determine if the word is an english word
    if dictionary.check(word):
        # Add the word to the list of guessed words
        bot.config.append_by_path(scrabble_args + ['guesses'], word)
        
        # Award the user with points
        try:
            points = bot.config.get_by_path(scrabble_args + ['points', 'current', event.user.full_name])
        except:
            points = 0
        points += len(word)
        bot.config.set_by_paths(scrabble_args + ['points', 'current', event.user.full_name], points)
        
        text = '{}\n{} puts {} at {} point{}!'.format(
            bold(' '.join(letters)),
            italicize(word),
            event.user.full_name,
            points,
            's' if points > 1 else ''
        )
        yield from event.conv.send_message(text_to_segments(text))
    
    # Stop other handlers from processing event
    raise StopEventHandling