import hangups

from hangupsbot.utils import text_to_segments
from hangupsbot.handlers import handler, StopEventHandling

from hangupsbot import ggl

def _translate(query, to="en"):
    translation = ggl.translate.translate(query, to)
    text = '**({})** {}'.format(translation.lang_from, translation.text)
    
    return text

@handler.register(priority=2, event=hangups.ChatMessageEvent)
def autotranslate(bot, event):
    """Translate all messages in a chat to a predefined language"""
    # Test if message is not empty
    if not event.text:
        return

    # Test if automatic translations are enabled
    try:
        enabled = bot.config.get_by_path(["conversations", event.conv_id, "translate_all", "enabled"])
    except:
        enabled = False
    if not enabled:
        return

    # Don't process anything that begins with the command character
    commands_character = bot.get_config_suboption(event.conv_id, 'commands_character')
    if event.text.startswith(commands_character):
        return
    
    # Translate the last message
    try:
        lang = bot.config.get_by_path(["conversations", event.conv_id, "translate_all", "language"])
    except:
        try:
            lang = bot.get_config_suboption(event.conv_id, 'translate_default')
        except:
            lang = None
    if not lang:
        lang = "es"
    yield from event.conv.send_message(text_to_segments(_translate(event.text, lang)))
    
    # Stop commands from running while translating in a solo chat
    raise StopEventHandling