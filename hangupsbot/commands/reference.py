from hangupsbot.utils import text_to_segments, remove_tags, replace_entities, bold, italicize, escape_formatting
from hangupsbot.commands import command

import requests
from lxml import html
from urllib.parse import quote

@command.register
def ud(bot, event, *args):
    """Define a word or phrase using Urban Dictionary
       Usage: ud the charizard"""
    
    phrase = ' '.join(args)
    url = 'http://api.urbandictionary.com/v0/tooltip?term={}&key=ab71d33b15d36506acf1e379b0ed07ee'.format(quote(phrase))
    
    req = requests.get(url)
    resp = req.json()
    
    # Format the result
    result = resp['string']
    result = remove_tags(result)
    result = replace_entities(result)
    
    title, definition = result.split('\n', 1)
    
    text = "**{}**\n{}".format(title, definition)
    yield from event.conv.send_message(text_to_segments(text))

def wiki(bot, event, *args):
    """Look up a term on Wikipedia
       Usage: wiki Python"""
    
    yield from event.conv.send_message(text_to_segments(""))

@command.register
def define(bot, event, *args):
    """Define a word using Merriam-Webster
       Usage: define tautologous"""
    
    query = ' '.join(args)
    url = 'http://www.merriam-webster.com/dictionary/{}'.format(quote(query))
    req = requests.get(url)
    tree = html.fromstring(req.text)
    
    # Get the simple definition
    try:
        el = tree.xpath('//span[@class="intro-colon"]')[0]
    except:
        yield from event.conv.send_message(text_to_segments("Word not found!"))
    definition = el.getparent().text_content().strip()
    
    # Get the word attributes
    el = tree.xpath('//div[@class="word-attributes"]')[0]
    attrs = [x.text_content().strip() for x in el.xpath('span')]
    attrs = ' | '.join(attrs).replace('\\', '/')

    text = _('{}\n{}\n{}').format(bold(query), italicize(escape_formatting(attrs)), definition)
    
    yield from event.conv.send_message(text_to_segments(text))