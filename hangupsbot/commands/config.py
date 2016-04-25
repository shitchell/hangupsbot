import json

from hangupsbot.utils import text_to_segments
from hangupsbot.commands import command


@command.register(admin=True)
def config(bot, event, cmd=None, *args):
    """Show or change bot configuration
       Usage: config [get | set] [key] [subkey] [...] [value]"""

    if cmd == 'get' or cmd is None:
        config_args = list(args)
        value = bot.config.get_by_path(config_args) if config_args else dict(bot.config)
    elif cmd == 'set':
        config_args = list(args[:-1])
        if len(args) >= 2:
            bot.config.set_by_path(config_args, json.loads(args[-1]))
            bot.config.save()
            value = bot.config.get_by_path(config_args)
        else:
            yield from command.unknown_command(bot, event)
            return
    else:
        yield from command.unknown_command(bot, event)
        return

    if value is None:
        value = _('Key not found!')

    config_path = ' '.join(k for k in ['config'] + config_args)
    text = (
        '**{}:**\n'
        '{}'
    ).format(config_path, json.dumps(value, indent=2, sort_keys=True))
    yield from event.conv.send_message(text_to_segments(text))

@command.register(admin=True)
def set(bot, event, *args):
    """Change configuration for this chat
       Usage: set [key] [subkey] [...] [value]"""

    # If we don't have enough args to set a key, return the chat, do nada
    if len(args) < 2:
        yield from event.conv.send_message(text_to_segments(_('Not enough arguments')))
        return
    
    conv_args = ["conversations", event.conv_id]
    config_args = conv_args + list(args)[:-1]

    print(config_args, args[-1])

    # Set the value for this chat
    bot.config.set_by_paths(config_args, json.loads(args[-1]))
    bot.config.save()
    value = bot.config.get_by_path(config_args)

    if value is None:
        value = _('Key not found!')

    config_path = ' '.join(k for k in config_args[2:])
    text = (
        '**{}:**\n'
        '{}'
    ).format(config_path, json.dumps(value, indent=2, sort_keys=True))
    yield from event.conv.send_message(text_to_segments(text))

@command.register(admin=True)
def get(bot, event, *args):
    """Show configuration for this chat
       Usage: get [key] [subkey] [...] [value]"""

    conv_args = ["conversations", event.conv_id]
    config_args = conv_args + list(args) if args else conv_args
    try:
        value = bot.config.get_by_path(config_args)
    except:
        if not args:
            value = _('No settings for this conversation!')
        else:
            value = None

    if value is None:
        value = _('Key not found!')

    config_path = ' '.join(k for k in ['config'] + config_args[2:])
    text = (
        '**{}:**\n'
        '{}'
    ).format(config_path, json.dumps(value, indent=2, sort_keys=True))
    yield from event.conv.send_message(text_to_segments(text))

@command.register(admin=True)
def delete(bot, event, *args):
    """Delete a configuration option for this chat
       Usage: del [key] [subkey] [...]"""

    conv_args = ["conversations", event.conv_id]
    config_args = conv_args + list(args) if args else conv_args
    try:
        bot.config.del_by_path(config_args)
    except:
        response = _('No such setting.')
    else:
        response = _('Setting deleted.')
        bot.config.save()
    
    config_path = ' '.join(k for k in ['config'] + config_args[2:])
    text = (
        '**{}:**\n'
        '{}'
    ).format(config_path, response)
    yield from event.conv.send_message(text_to_segments(text))


@command.register(admin=True)
def config_reload(bot, event, *args):
    """Reload bot configuration from file"""
    bot.config.load()
    yield from event.conv.send_message(text_to_segments(_('Configuration reloaded')))
