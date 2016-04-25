from hangupsbot.commands import command
from hangupsbot.utils import text_to_segments, italicize, bold, link, escape_formatting

import re
import optparse
import requests
from lxml import html
import transmissionrpc
from urllib.parse import quote

import io
import time
import socket
import zipfile
import asyncio

parser = optparse.OptionParser(add_help_option=False)
parser.add_option('-a', '--author', action='store', dest='author',
                    help='filter results by torrent uploader')
parser.add_option('-m', '--max-size', type=int, action='store', dest='size',
                    help='maximum file size')
parser.add_option('-s', '--minimum-seeders', type=int, dest='seeders',
                    help='minimum number of seeders for a torrent')
parser.add_option('-r', '--results', type=int, dest='results', default=3,
                    help='number of results to display')
parser.add_option('-i', '--show-id', action='store_true', dest='show_id', default=False,
                    help='show a torrent ID to be used with the magnet command')
parser.usage = 'tpb [options] query'
parser.epilog = 'Search thepiratebay for a torrent'

_filesize_multipliers = {
            'B': 1,
            'KiB': 1024,
            'kb': 1024,
            'k': 1024,
            'MiB': 1048576,
            'mb': 1048576,
            'm': 1048576,
            'GiB': 1073741824,
            'gb': 1073741824,
            'g': 1073741824
            }

class PirateResult:
    def __init__(self, el):
        self.parent = el.getparent()
        self._parse_text_content()
        self._get_magnet()
        self._parse_size()
        del self.parent
    
    def _parse_text_content(self):
        text = self.parent.text_content()
        text = escape_formatting(text)
        text = text.replace('\xa0', ' ')
        text = re.split('\n|\t', text)
        text = filter(None, text)
        [
            self.category,
            self.subcategory,
            self.title,
            upsizeauth,
            self.seeders,
            self.leechers
            ] = list(text)
        [
            self.date,
            self.size,
            self.author
            ] = [x.split(' ', 1)[1] for x in upsizeauth.split(', ')]
        self.author = self.author.split()[-1]
    
    def _get_magnet(self):
        self.magnet = self.parent.find('td/a[@title="Download this torrent using magnet"]').get('href')
    
    def _parse_size(self):
        value, unit = self.size.split()
        multiplier = _filesize_multipliers.get(unit)
        self._size = float(value) * multiplier

@command.register
def tpb(bot, event, *args):
    """Search the Pirate Bay for a magnet link"""
    # Get parser options
    try:
        (opts, largs) = parser.parse_args(list(args))
    except:
        yield from event.conv.send_message(text_to_segments('Error parsing search query!'))
    
    # Query thepiratebay
    query = ' '.join(largs)
    url = 'https://thepiratebay.se/search/{}/0/99/0'.format(quote(query))
    req = requests.get(url)
    tree = html.fromstring(req.text)
    
    # Get each result element in the tree
    els = tree.xpath('//td[@class="vertTh"]')
    
    # Format the size if that option is provided
    if opts.size:
        # Strip the number
        size = ""
        s = str(options.size)
        while s and s[0:1].isdigit() or s[0:1] == ".":
            size += s[0]
            s = s[1:]
        size = float(size)
        
        # Get the unit
        unit = s.lower()
        
        # Multiply into bytes
        multiplier = _filesize_multipliers.get(unit)
        max_size = multiplier * size
    
    # Parse each result element
    results = []
    for el in els:
        result = PirateResult(el)
        
        # See if the result meets our criteria
        if opts.author and result.author.lower() != opts.author.lower():
            continue
        if opts.size and max_size > opts.size:
            continue
        if opts.seeders and result.seeders < opts.seeders:
            continue
        results.append(PirateResult(el))
        
        # Stop after we've gotten enough results
        if len(results) == opts.results:
            break
    
    # Make sure we got results
    if not results:
        yield from event.conv.send_message(text_to_segments('No results found!'))
        return
    
    text = []
    magnets = []
    for i in range(0, len(results)):
        result = results[i]
        result_text = '{}) {}\n{} {}\nSeeders: {}\nSize: {}\nUploaded {} by {}'.format(
            i + 1,
            bold(link(result.magnet, result.title)),
            italicize(result.category),
            italicize(result.subcategory),
            result.seeders,
            result.size,
            result.date,
            result.author,
            link(result.magnet, "magnet"))
        text.append(result_text)
        magnets.append(result.magnet)
    
    # Store this batch of magnet links locally to be able to grab the magnet link later
    magnet_dict = dict(list(zip(list(range(1, len(magnets)+1)), magnets)))
    bot.config.set_by_paths(["conversations", event.conv_id, "torrent_links"], magnet_dict)
    bot.config.save()
    
    yield from event.conv.send_message(text_to_segments('\n\n'.join(text)))
tpb.__doc__ = parser.format_help()

@command.register
def magnet(bot, event, *args):
    """Get the magnet link from the last list of torrents searched
    Usage: magnet 3"""
    
    magnets = bot.config.get_by_path(["conversations", event.conv_id, "torrent_links"])
    if magnets:
        magnet = magnets.get(int(args[0]))
        if magnet:
            yield from event.conv.send_message(text_to_segments(magnet))
            return
        else:
            yield from event.conv.send_message(text_to_segments("No such search result"))
    else:
        yield from event.conv.send_message(text_to_segments('No recent torrent searches'))

rpc_client = transmissionrpc.Client('localhost', 8001, user='guy', password='p2p')
@command.register(admin=True)
def torrent(bot, event, *args):
    """Start torrenting a result from the last list of torrents searched
    Usage: torrent 3"""
    
    magnets = bot.config.get_by_path(["conversations", event.conv_id, "torrent_links"])
    if magnets:
        magnet = magnets.get(int(args[0]))
        if magnet:
            torrent = rpc_client.add_torrent(magnet)
            text = "Added {}".format(bold(torrent.name))
            yield from event.conv.send_message(text_to_segments(text))
            return
        else:
            yield from event.conv.send_message(text_to_segments("No such search result"))
    else:
        yield from event.conv.send_message(text_to_segments('No recent torrent searches'))

@command.register(admin=True)
def torrents(bot, event, *args):
    """Get a list of torrents being downloaded / seeded
    Usage: torrents"""
    
    torrents = rpc_client.get_torrents()
    texts = []
    for torrent in torrents:
        text = "{} {:0.1f}%".format(bold(torrent.name), torrent.progress)
        if torrent.status == 'downloading':
            seconds = torrent.eta.seconds % 60
            minutes = int(torrent.eta.seconds / 60)
            hours = int(minutes / 60)
            if minutes > 60:
                minutes = minutes % 60
            
            times = [
                str(hours) + "h" if hours else "",
                str(minutes) + "m" if minutes else "",
                str(seconds) + "s"
                ]
            text += " *({})*".format(" ".join(times).strip())
        else:
            text += " " + italicize(torrent.status)
        texts.append(text)

    yield from event.conv.send_message(text_to_segments("\n".join(texts)))

def _send_file(client, filename, data):
    print('sending file', filename)
    ok_headers = [
        'HTTP/1.1 200 OK',
        'Date: ' + time.strftime('%a, %d %b %Y %H:%M:%S %'),
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Length: {}'.format(len(data)),
        'Connection: keep-alive',
        'Content-Description: File Transfer',
        'Content-Disposition: attachment; filename=' + filename,
        'Content-Transfer-Encoding: binary',
        'Expires: 0',
        'Server: ur mum'
    ]
    not_found_headers = [
        'HTTP/1.1 200 OK',
        'Content-Type: text/html; charset=UTF-8'
    ]
    headers = '\n'.join(headers) + '\n\n'
    client.send(headers.encode('utf-8'))
    client.send(data)

@asyncio.coroutine
def _single_serve(event, filename, data):
    s = socket.socket()
    # Bind to some socket
    for port in range(4500, 5000):
        try:
            s.bind(('0.0.0.0', port))
        except:
            continue
        else:
            url = 'http://shitchell.com:{}/{}'.format(port, quote(filename))
            yield from event.conv.send_message(text_to_segments(url))
            break
    print('listening')
    s.listen(1)
    s.settimeout(60) # We want this to die fairly quickly
    try:
        (client, info) = s.accept()
    except socket.timeout:
        print('_single_serve timed out')
    else:
        print('got client', info)
        _send_file(client, filename, data)
    s.shutdown(1)

_subtitles_cache = dict()
@command.register
def subtitles(bot, event, *args):
    """Fetch subtitles from yifysubtitles.com
       Usage: subtitles [movie name]"""
    
    movie = ' '.join(args)
    res = requests.get('http://www.yifysubtitles.com/a_mov.php?reqmov=' + quote(movie))
    results = res.json()['movies']
    
    if results:
        # Fetch the result page
        result = results[0]
        url = 'http://www.yifysubtitles.com/movie-imdb/' + result['value']
        res = requests.get(url)
        tree = html.fromstring(res.text)
        
        # Get the subtitle zip url
        stag = tree.xpath('.//span[text()="English"]')[0]
        atag = stag.getparent()
        href = atag.get('href')
        sub_url = "http://www.yifysubtitles.com" + href.replace('/subtitles/', '/subtitle/', 1) + ".zip"
        
        # Download the zip file
        zipdata = requests.get(sub_url).content
        file = zipfile.ZipFile(io.BytesIO(zipdata))
        filename = file.namelist()[0]
        subtitles_data = file.read(filename)
        _subtitles_cache[filename] = subtitles_data
        
        # Start a server to serve a single file
        asyncio.async(
            _single_serve(event, filename, subtitles_data)
        ).add_done_callback(lambda future: future.result())
