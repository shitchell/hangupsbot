from hangupsbot.utils import text_to_segments, bold, italicize
from hangupsbot.commands import command


@command.register
def note(bot, event, subject=None, *args):
    """Save notes with subjects. Delete a note with "-"
       Usage: subject [body]
       Usage: -subject"""
    
    config_args = ["notes"]
    
    # Make sure there's a notes dictionary
    try:
        bot.config.get_by_path(config_args)
    except:
        bot.config.set_by_paths(config_args, dict())

    if subject.startswith('-'):
        subject = subject[1:]
        try:
            bot.config.del_by_path(config_args + [subject])
        except:
            response = italicize('No such note.')
        else:
            response = italicize('Note deleted.')
    elif args:
        # Save a new note
        content = ' '.join(args)
        note = {
            'content': content,
            'author': event.user.full_name,
            'timestamp': event.timestamp.astimezone(tz=None).strftime('%Y-%m-%d %H:%M:%S')
            }
        bot.config.set_by_paths(config_args + [subject], note)
        response = italicize('Note saved')
    else:
        # If no args given, display a note
        try:
            note = bot.config.get_by_path(config_args + [subject])
            response = '{}'.format(note['content'])
        except:
            response = italicize('No such note')

    text = _('{}\n{}').format(bold(subject), response)
    yield from event.conv.send_message(text_to_segments(text))
    
    bot.config.save()

@command.register
def notes(bot, event, *args):
    """Display all saved notes
    Usage: notes"""
    
    config_args = ["notes"]
    
    # Make sure there's a notes dictionary
    try:
        saved = bot.config.get_by_path(config_args)
    except:
        yield from event.conv.send_message(text_to_segments('No notes saved!'))
        return
    
    if not saved:
        yield from event.conv.send_message(text_to_segments('No notes saved!'))
        return

    # Get all of the notes and their infos
    response = []
    for subject in saved:
        note = saved[subject]
        text = '{} *by {} at {}*'.format(bold(subject), note['author'], note['timestamp'])
        response.append(text)

    yield from event.conv.send_message(text_to_segments('\n'.join(response)))