import hangupsbot.commands
import hangupsbot.handlers
from hangupsbot.commands import command
from hangupsbot.utils import text_to_segments, bold

import sys
import time
import random
import requests
import importlib

_eval_globals = {}
@command.register(admin=True)
def eval(bot, event, *args):
    """Evaluate a python expression
       Usage: eval code"""
    
    code = ' '.join(args)
    
    try:
        # Hacky, yes, but I like this name for the command :p
        result = globals()['__builtins__']['eval'](code, _eval_globals)
    except SyntaxError:
        try:
            result = exec(code, _eval_globals)
        except Exception as e:
            result = e
    except Exception as e:
        result = e
    result = repr(result)
    
    yield from event.conv.send_message(text_to_segments(result))

@command.register
def stfu(bot, event, *args):
    """Silence the bot
       Usage: stfu"""
    
    yield from event.conv.send_message(text_to_segments('SPEAKING THE FUCK UP!'))

@command.register
def coin(bot, event, *args):
    """Flip a coin
       Usage: coin"""
    
    result = random.choice(["Heads", "Tails"])
    yield from event.conv.send_message(text_to_segments(result))

@command.register
def choose(bot, event, *args):
    """Choose an item from a list
       Usage: choose item1 item2 item3..."""
    
    if args:
        result = random.choice(args)
        yield from event.conv.send_message(text_to_segments(result))

@command.register
def countdown(bot, event, *args):
    """Countdown from a given number to 1
       Usage: countdown 7"""
    
    start = int(args[0]) if args else 5
    while start:
        start -= 1
        yield from event.conv.send_message(text_to_segments(str(start + 1)))
        time.sleep(1)
    
    text = random.choice(["KABLOOM!", "WHOO!", "PARTY!", "GO!", "HAIL SKYNET!"])
    yield from event.conv.send_message(text_to_segments(text))

@command.register(admin=True)
def reload(bot, event, *args):
    """Reload all commands
       Usage: reload"""
    
    # Load any new files
    importlib.reload(hangupsbot.commands)
    # Delete and reload each plugin
    for plugin in hangupsbot.commands.__all__:
        reloaded = importlib.reload(getattr(hangupsbot.commands, plugin))
        del sys.modules['hangupsbot.commands.' + plugin]
        sys.modules['hangupsbot.commands.' + plugin] = reloaded

    # Load any new files
    importlib.reload(hangupsbot.handlers)
    # Delete and reload each handler
    for handler in hangupsbot.handlers.__all__:
        reloaded = importlib.reload(getattr(hangupsbot.handlers, handler))
        del sys.modules['hangupsbot.handlers.' + handler]
        sys.modules['hangupsbot.handlers.' + handler] = reloaded

@command.register(admin=True)
def ip(bot, event, *args):
    """Get the current IP address of the bot
    Usage: ip"""
    
    text = requests.get('http://icanhazip.com/').text
    yield from event.conv.send_message(text_to_segments(text))

@command.register
def cam(bot, event, *args):
    """Upload a picture from a webcam. Store a new webcam
    by giving it a webcam name followed by a url to the camera.
    Usage: cam [webcam] [url]"""
    
    cams = bot.config.get_by_path(["webcams"])
    if not cams:
        cams = dict()
        bot.config.set_by_path(["webcams"], cams)
        bot.config.save()
    
    # See if we're storing a webcam
    if len(args) > 1 and args[-1].startswith('http'):
        cam = ' '.join(args[:-1])
        url = args[-1]
        bot.config.set_by_paths(["webcams", cam], url)
        bot.config.save()
        
        yield from event.conv.send_message(text_to_segments('{} saved!'.format(bold(cam))))
    else:
        cam = ' '.join(args)
        url = cams.get(cam)
    
    if url:
        image_id = yield from bot.upload_images([url])
        yield from event.conv.send_message([], image_id=image_id[0])
    else:
        if not cams:
            yield from event.conv.send_message(text_to_segments('No webcams saved!'))
        else:
            text = '{}\n{}'.format(bold('webcams'), ', '.join(cams.keys()))
            yield from event.conv.send_message(text_to_segments(text))
