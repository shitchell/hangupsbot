from hangupsbot.utils import text_to_segments
from hangupsbot.commands import command

import re

@command.register
def clever(bot, event, cmd=None, *args):
    """Turn clever replies on or off, optionally setting a chance of responding
       Usage: clever [off|on|1/5]"""

    if cmd == 'off' or cmd is None:
        var = "clever_enabled"
        val = False
        text = _("Reverting to normal bot mode *beep boop*")
    elif cmd == 'on':
        var = "clever_enabled"
        val = True
        text = _("Mind if I join in on this conversation?")
    else:
        text = ' '.join([cmd] + list(args))
        print('"{}"'.format(text))
        matches = re.findall('^(\d+) ?/ ?(\d+)$', text)
        if matches:
            [(a, b)] = matches
            var = "clever_chance"
            val = int(a) / int(b)
            text = _("I'll try to be clever {:.0%} of the time").format(val)
        else:
            return
    
    try:
        is_set = bot.config.get_by_path(["conversations", event.conv_id, var]) == val
    except:
        is_set = False
    
    if not is_set:
        bot.config.set_by_paths(["conversations", event.conv_id, var], val)
        bot.config.save()
        yield from event.conv.send_message(text_to_segments(text))