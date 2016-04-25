from hangupsbot.commands import command
from hangupsbot.utils import text_to_segments, bold

import string
import random
import asyncio

@asyncio.coroutine
def _kill_scrabble(bot, event, seconds=15):
    print("starting scrabble timer")
    scrabble_args = ['conversations', event.conv_id, 'scrabble']
    scrabble_opts = bot.config.get_by_path(scrabble_args)
    yield from asyncio.sleep(seconds)
    print("scrabble timer finished")
    
    # Format the results and update the leaderboard
    points = sorted(scrabble_opts['points']['current'].items(), key=lambda x: x[1], reverse=True)
    for i in range(0, len(points)):
        points[i] = list(points[i])
        user = points[i][0]
        user_overall = scrabble_opts['points']['overall'].get(user, 0)
        user_overall += points[i][1]
        points[i].append(user_overall)
        bot.config.set_by_paths(scrabble_args + ['points', 'overall', user], user_overall)
    
    print(points)
    text = '**Game Over**\n{}'.format(
        '\n'.join(['%s: %s *(%s overall)*' % (x, y, z) for (x, y, z) in points])
    )
    
    # Reset the game
    print("resetting scrabble")
    bot.config.set_by_paths(scrabble_args + ['letters'], list())
    bot.config.set_by_paths(scrabble_args + ['guesses'], list())
    bot.config.set_by_paths(scrabble_args + ['points', 'current'], dict())
    bot.config.save()
    
    print("sending message to chat")
    yield from event.conv.send_message(text_to_segments(_(text)))

_scrabble_letters = "e"*9 + "a"*9 + "i"*9 + "o"*8 + "r"*6 + "n"*6 + "t"*6 + "l"*4 + "s"*4 + "u"*4 + "d"*4 + "g"*3 + "b"*2 +"c"*2 + "m"*2 + "p"*2 + "f"*2 + "h"*2 + "v"*2 + "w"*2 + "y"*2 + "k" + "j" + "x" + "q" + "z"
@command.register
def scrabble(bot, event, *args):
    """10 letters are chosen at random, and you have a limited
    time to form words with them. Points are awarded based
    on word length.
    Usage: scrabble [seconds]"""
    
    # Determine if a game is ongoing
    scrabble_args = ['conversations', event.conv_id, 'scrabble']
    try:
        scrabble_opts = bot.config.get_by_path(scrabble_args)
    except:
        scrabble_opts = {'letters': list(), 'guesses': list(), 'points': {'current': dict(), 'overall': dict()}}
        bot.config.set_by_paths(scrabble_args, scrabble_opts)
    
    if not scrabble_opts.get('letters'):
        # Start a new game
        letters = list()
        for i in range(0, 10):
            letters.append(random.choice(_scrabble_letters))
        scrabble_opts['letters'] = letters
        
        # Get the duration of the current game
        if args:
            seconds = int(args[0])
        else:
            seconds = bot.get_config_suboption(event.conv_id, "scrabble_duration") or 15
        
        # Start a timer for the current game
        asyncio.async(
            _kill_scrabble(bot, event, seconds)
        ).add_done_callback(lambda future: future.result())
        
        # Display a message about the game
        text = '{}\nYou have {} seconds to make words!'.format(
            bold(' '.join(letters)),
            seconds
            )
        yield from event.conv.send_message(text_to_segments(_(text)))

def hang_reveal(guesses, word):
    reveal = []
    for letter in word:
        if letter in guesses:
            reveal.append(_('=={}==').format(letter))
        else:
            reveal.append(_('\_'))
    return reveal

@command.register
def hang(bot, event, cmd=None, *args):
    """Play a game of hangman
       Usage: hang start
       Usage: hang e"""
    
    # Firstly, lowercase the cmd
    if cmd:
        cmd = cmd.lower()
    
    # Get the hangman settings if they exist
    hang_args = ['conversations', event.conv_id, "hangman"]
    try:
        hang_opts = bot.config.get_by_path(hang_args)
    except:
        hang_opts = {'word': '', 'guesses': list(), 'tries': len(_hangman_levels) - 1}
        bot.config.set_by_paths(hang_args, hang_opts)
    
    if cmd == "start":
        if hang_opts['word']:
            yield from event.conv.send_message(text_to_segments(_('Game in progress!')))
            return
        else:
            # Pick a new word
            words = open(_hangman_filepath, 'r').read()
            hang_opts['word'] = random.choice(words.split())
            bot.config.set_by_path(hang_args, hang_opts)
            bot.config.save()
            yield from event.conv.send_message(text_to_segments(_('New game started!')))
            return
    elif not cmd:
        if not hang_opts['word']:
            yield from event.conv.send_message(text_to_segments(_('Start a new game!')))
            return
        title = "Current game"
        reveal = hang_reveal(hang_opts['guesses'], hang_opts['word'])
    elif not hang_opts['word'] or len(cmd) == 1:
        if not hang_opts['word']:
            # Guessed a letter, but no game is in progress
            yield from event.conv.send_message(text_to_segments(_('Start a new game!')))
            return
        else:
            # Guess a letter
            guess = cmd
            
            if guess in hang_opts['guesses']:
                title = "D'oh!"
            elif guess in hang_opts['word']:
                title = 'Whoo!'
            else:
                title = 'Oh no!'
                hang_opts['tries'] -= 1
            
            # Add the guess
            if guess not in hang_opts['guesses']:
                hang_opts['guesses'].append(guess)

            if hang_opts['tries']:
                # Loop over the word, replacing letters with underscores where necessary
                reveal = hang_reveal(hang_opts['guesses'], hang_opts['word'])
                
                # See if we've won
                if not '\_' in reveal:
                    title = _('Game won by {}!').format(event.user.full_name)
                    hang_opts['word'] = ""

            if not hang_opts['tries']:
                # Game over, man... game over
                reveal = ['=={}=='.format(x) for x in hang_opts['word']]
                hang_opts['word'] = ""

            # Save the game state
            bot.config.set_by_path(hang_args, hang_opts)
            bot.config.save()
    
    text = _('''**{}**
    {}
    
    {}
    {}''').format(title, _hangman_levels[len(_hangman_levels) - hang_opts['tries'] - 1], ' '.join(reveal), ', '.join(hang_opts['guesses']))
    yield from event.conv.send_message(text_to_segments(text))

    if not hang_opts['word']:
        hang_opts['tries'] = len(_hangman_levels) - 1
        hang_opts['guesses'] = list()
        # Save the game state
        bot.config.set_by_path(hang_args, hang_opts)
        bot.config.save()


_hangman_filepath = '/usr/share/dict/hangman'
_hangman_levels = [
    '''     \_\_\_\_\_\_
     |/      |
     |
     |
     |
     |''',
    '''     \_\_\_\_\_\_
     |/      |
     |      (_)
     |
     |
     |''',
    '''     \_\_\_\_\_\_
     |/      |
     |      (_)
     |       |/
     |
     |''',
    '''     \_\_\_\_\_\_
     |/      |
     |      (_)
     |      \\|/
     |
     |''',
    '''     \_\_\_\_\_\_
     |/      |
     |      (_)
     |      \\|/
     |       |
     |''',
    '''     \_\_\_\_\_\_
     |/      |
     |      (_)
     |      \\|/
     |       |
     |      /''',
    '''     \_\_\_\_\_\_
     |/      |
     |      (_)
     |      \\|/
     |       |
     |      / \\'''
]