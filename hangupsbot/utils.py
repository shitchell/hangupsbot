from hangups import ChatMessageSegment

import re
import string
import unicodedata
import html.parser

def text_to_segments(text):
    """Create list of message segments from text"""
    return ChatMessageSegment.from_str(text)


def unicode_to_ascii(text):
    """Transliterate unicode characters to ASCII"""
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()


def word_in_text(word, text):
    """Return True if word is in text"""
    word = unicode_to_ascii(word).lower()
    text = unicode_to_ascii(text).lower()
    
    if ' ' in word and word in text:
        return True
    else:
        # Replace delimiters in text with whitespace
        for delim in '.,:;!?':
            text = text.replace(delim, ' ')
    
        return True if word in text.split() else False


def strip_quotes(text):
    """Strip quotes and whitespace at the beginning and end of text"""
    return text.strip(string.whitespace + '\'"')

def italicize(text):
    """Italicize text"""
    return '_{}_'.format(text)

def bold(text):
    """Bold text"""
    return '**{}**'.format(text)

def underline(text):
    """Underline text"""
    return '=={}=='.format(text)

def link(url, text):
    """Return a link using the text and url"""
    return '[{}]({})'.format(text, url)

_regex_tags = re.compile(r'<.*?>')
def remove_tags(text, replace=''):
    """Remove html tags from text"""
    return _regex_tags.sub(replace, text)

def escape_formatting(text):
    """Escape hangouts formatters"""
    return re.sub('(\*|=|_|\[)', lambda x: '\\' + x.groups(1)[0], text)

parser = html.parser.HTMLParser()
def replace_entities(text):
    """Replace html entities with appropriate characters"""
    return parser.unescape(text)