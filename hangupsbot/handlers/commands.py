import re, shlex

import hangups

from hangupsbot.utils import text_to_segments
from hangupsbot.handlers import handler, StopEventHandling
from hangupsbot.commands import command
from hangups.ui.utils import get_conv_name



default_bot_alias = '/bot'


def find_bot_alias(aliases_list, text):
    """Return True if text starts with bot alias"""
    command = text.split()[0].lower()
    for alias in aliases_list:
        if alias.lower().startswith('regex:') and re.search(alias[6:], command, re.IGNORECASE):
            return True
        elif command == alias.lower():
            return True
    return False


@handler.register(priority=5, event=hangups.ChatMessageEvent)
def handle_command(bot, event):
    """Handle command messages"""
    # Test if message is not empty
    if not event.text:
        return

    # Get list of bot aliases
    aliases_list = bot.get_config_suboption(event.conv_id, 'commands_aliases')
    if not aliases_list:
        aliases_list = [default_bot_alias]
    
    # Determine if this is a one-on-one chat
    conv = get_conv_name(event.conv, truncate=True)
    is_solo = bool(not "," in conv)
    
    # Determine if using a leading character or bot alias for commands
    commands_character = bot.get_config_suboption(event.conv_id, 'commands_character')
    
    # Treat all solo chat messages as commands
    if not is_solo:
        if commands_character:
            if not event.text.startswith(commands_character):
                return
        else:
            # Test if message starts with bot alias
            if not find_bot_alias(aliases_list, event.text):
                return

    # Test if command handling is enabled
    if not bot.get_config_suboption(event.conv_id, 'commands_enabled'):
        raise StopEventHandling

    # Remove leading command initiators and parse message
    if find_bot_alias(aliases_list, event.text):
        line = event.text.split(' ', 1)[1:]
    elif commands_character:
        line = event.text.lstrip(commands_character)
    else:
        line = event.text
    line_args = shlex.split(line, posix=False)

    # Test if command length is sufficient
    if len(line_args) < 1:
        yield from event.conv.send_message(
            text_to_segments(_('{}: How may I serve you?').format(event.user.full_name))
        )
        raise StopEventHandling

    # Test if user has permissions for running command
    commands_admin_list = command.get_admin_commands(bot, event.conv_id)
    if commands_admin_list and line_args[0].lower() in commands_admin_list:
        admins_list = bot.get_config_suboption(event.conv_id, 'admins')
        if event.user_id.chat_id not in admins_list:
            yield from event.conv.send_message(
                text_to_segments(_('{}: I\'m sorry, Dave. I\'m afraid I can\'t do that.').format(event.user.full_name))
            )
            raise StopEventHandling

    # Run command
    yield from command.run(bot, event, *line_args)

    # Prevent other handlers from processing event
    raise StopEventHandling