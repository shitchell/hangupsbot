from hangupsbot import ggl

from hangupsbot.utils import text_to_segments, bold, italicize
from hangupsbot.commands import command

import re
import requests
from urllib.parse import quote

@command.register
def search(bot, event, *args):
    """Perform a Google search and list the first 3 results
       Usage: search the meaning of life"""
    
    query = ' '.join(args)
    results = ggl.search.web_search(query)
    
    text = []
    for result in results[:3]:
        text.append("**[{}]({})**\n*{}*".format(result.title, result.url, result.snippet))

    yield from event.conv.send_message(text_to_segments('\n\n'.join(text)))

@command.register
def img(bot, event, *args):
    """Search Google for an image an upload the first result
    Usage: img puppies"""
    
    query = ' '.join(args)
    results = ggl.search.image_search(query)
    
    # Check that we got any results
    if results:
        # Upload the first result
        result = results[0]
        image_id = yield from bot.upload_images([result.url])
        yield from event.conv.send_message([], image_id=image_id[0])

def _translate(args, to="en"):
    query = ' '.join(args)
    translation = ggl.translate.translate(query, to)
    text = '**({})** {}'.format(translation.lang_from, translation.text)
    
    return text

@command.register
def translate(bot, event, *args):
    """Translate text to english. If no text is given,
    all supported languages are displayed
       Usage: translate hola mundo"""
    
    # Display a list of languages if no args are given
    if not args:
        languages = [': '.join(x) for x in ggl.translate._translate_codes]
        text = '{}\n{}'.format(bold('language codes'), languages)
        yield from event.conv.send_message(text_to_segments(text))
        return
    
    # Get the default language
    lang_to = bot.get_config_suboption(event.conv_id, 'translate_default')
    if not lang_to:
        lang_to = "en"
    yield from event.conv.send_message(text_to_segments(_translate(args, lang_to)))

@command.register
def translate_to(bot, event, to, *args):
    """Translate a phrase to a given language
       Usage: translate_to es hello world"""
    
    yield from event.conv.send_message(text_to_segments(_translate(args, to)))

@command.register
def translate_all(bot, event, cmd=None, *args):
    """Translate all messages in the chat
       Usage: translate_all [on | off] [en | fr | es | ... ]"""
    
    conv_args = ["conversations", event.conv_id, "translate_all"]
    
    # Get the chat options for translating messages
    opts = bot.get_config_suboption(event.conv_id, 'translate_all')
    if not opts:
        opts = {'language': 'es', 'enabled': False}
        bot.config.set_by_paths(conv_args, opts)
    
    # Toggle the enabled state if no command is given
    if not cmd:
        cmd = 'on' if not opts.get('enabled') else 'off'

    cmd = cmd.lower()

    if cmd == 'on':
        if opts.get('enabled'):
            return
        bot.config.set_by_paths(conv_args + ['enabled'], True)
        text = 'Translating all messages to {}'.format(bold(ggl.translate._get_translate_lang(opts['language'])))
    elif cmd == 'off':
        if not opts.get('enabled'):
            return
        bot.config.set_by_paths(conv_args + ['enabled'], False)
        text = 'No more speaky in {}'.format(ggl.translate._get_translate_lang(opts['language']))
    else:
        # Set the language to translate to the language given as a language code
        matched = False
        for (language, code) in ggl.translate._translate_codes:
            if cmd == code:
                matched = True
                bot.config.set_by_paths(conv_args + ['language'], code)
                text = 'Automatic translations set to {}'.format(bold(ggl.translate._get_translate_lang(opts['language'])))
                break
        if not matched:
            text = 'Sorry, but {} isn\'t a supported language code. Use "translate" to view supported languages.'.format(bold(cmd))
    
    bot.config.save()
    yield from event.conv.send_message(text_to_segments(text))

# Recursively get all of the route's steps
def _steps_to_text(route, prefix=""):
    steps = []
    for i in range(0, len(route.steps)):
        step = route.steps[i]
        step_prefix = '{}{}.'.format(prefix, i + 1)
        text = '{} {} *({}, {})*'.format(
            step_prefix,
            step.text,
            step.distance,
            step.duration
            )
        steps.append(text)
        
        # See if there are additional details to append
        if len(step.steps) > 0:
            steps.extend(_steps_to_text(step, prefix=step_prefix))
        elif step.mode == 'transit':
            text = '- *{} - {}*\n- {} to {}'.format(
                step.transit_details.name,
                step.transit_details.short_name,
                italicize(step.transit_details.departure),
                italicize(step.transit_details.arrival)
                )
            steps.append(text)
    return steps

_directions_regex = re.compile(r'(({}) )?from (.*?) to (.*)'.format('|'.join(ggl.maps._travel_modes)))
@command.register
def directions(bot, event, *args):
    """Get directions from point A to point B
    Usage: directions [mode] from [origin] to [destination]
    Example: directions walking from Atlanta, GA to Windsor, ON
    Example: directions from Los Angeles, CA to San Francisco, CA"""
    
    line = ' '.join(args)
    [(modespace, mode, origin, destination)] = _directions_regex.findall(line)
    
    if not mode:
        mode = 'driving'
    
    md = ggl.maps.MapsDirections(origin, destination, mode=mode)
    
    text = '{} to {}\n{}, {}\n'.format(
        bold(md.origin),
        bold(md.destination),
        italicize(md.route.distance),
        italicize(md.route.duration)
        )
    
    steps = _steps_to_text(md.route)
    text += '\n'.join(steps)
    
    yield from event.conv.send_message(text_to_segments(text))