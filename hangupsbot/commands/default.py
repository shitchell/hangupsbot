from hangups.ui.utils import get_conv_name

from hangupsbot.utils import text_to_segments
from hangupsbot.commands import command


@command.register_unknown
def unknown_command(bot, event, *args):
    """Unknown command handler"""
    yield from event.conv.send_message(
        text_to_segments(_('{}: Unknown command!').format(event.user.full_name))
    )


@command.register
def help(bot, event, cmd=None, *args):
    """Help me, Obi-Wan Kenobi. You're my only hope.
       Usage: help [command]"""

    cmd = cmd if cmd else 'help'
    try:
        command_fn = command.commands[cmd]
    except KeyError:
        yield from command.unknown_command(bot, event)
        return

    text = _('**{}:**\n'
             '{}').format(cmd, _(command_fn.__doc__))

    if cmd == 'help':
        # See if the user has admin privileges to limit commands displayed
        admins_list = bot.get_config_suboption(event.conv_id, 'admins')
        if event.user_id.chat_id not in admins_list:
            command_list = command.get_user_commands(bot, event.conv_id)
        else:
            command_list = command.commands.keys()
        text += _('\n\n'
                  '**Supported commands:**\n'
                  '{}').format(', '.join(sorted(command_list)))

    yield from event.conv.send_message(text_to_segments(text))


@command.register
def ping(bot, event, *args):
    """Let's play ping pong!"""
    yield from event.conv.send_message(text_to_segments('pong'))


@command.register
def echo(bot, event, *args):
    """Monkey see, monkey do!
       Usage: echo text"""
    yield from event.conv.send_message(text_to_segments(' '.join(args)))


@command.register(admin=True)
def quit(bot, event, *args):
    """Oh my God! They killed Kenny! You bastards!"""
    print(_('HangupsBot killed by user {} from conversation {}').format(
        event.user.full_name,
        get_conv_name(event.conv, truncate=True)
    ))
    yield from event.conv.send_message(text_to_segments(_('Et tu, Brute?')))
    yield from bot._client.disconnect()
