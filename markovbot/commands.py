import logging
import random

from markovbot import utilities
from markovbot import markovbot, datastore

log = logging.getLogger(__name__)


# TODO: I wonder if there is a way to extend the way the context is passed in, and we could add our server
# context as a property on that context object.
@markovbot.command(pass_context=True, help='Generate a Markov sentence based on the server chat history.')
async def say(context, user: str = None):
    server_context = context.server_context

    if not server_context.is_ready:
        await markovbot.say('I am still learning from all your messages. Try again later.')
        return

    if user is None:
        log.debug('Bot issued say command on server %s.',
                  server_context.server.name)
        sentence = server_context.markov.make_sentence_server()

        if sentence is None:
            await markovbot.say('Unable to generate message. This is probably due to a lack of messages on the server.')
            return

    else:
        db_user = datastore.get_server_user(server_context.server.id, user)

        if db_user is None:
            await markovbot.say('The user {} does not exist. Check your spelling and try again.'.format(user))
            return

        sentence = server_context.markov.make_sentence_user(db_user)

        if sentence is None:
            await markovbot.say(
                'Unable to generate message for {}. This is probably because they have not sent enough messages.'.format(
                    user))
            return

    await markovbot.say(sentence)


@markovbot.command(pass_context=True, help='Mock the last specified user message.')
async def mock(context, user: str = None):
    server_context = context.server_context
    targeted_user = None

    if user is None:
        members = server_context.server.members
        targeted_user = list(members)[random.randint(0, len(members)) - 1]
        await markovbot.say('Selected user {}'.format(targeted_user))

    else:
        for member in server_context.server.members:
            if member.nick == user:
                targeted_user = member
            else:
                targeted_user = server_context.server.get_member_named(user)
    logs_by_user = list()

    # Get messages from user in current channel
    async for message in markovbot.logs_from(context.message.channel, limit=500):
        if message.author.id == targeted_user.id and not message.content.startswith('!cancer'):
            logs_by_user.append(message)

    # Get latest message from user
    if not logs_by_user:
        await markovbot.say('User does not have any messages in this channel.')
        return

    logs_by_user.sort(key=lambda message: message.timestamp, reverse=True)

    targeted_message = logs_by_user[0]
    sentence = utilities.mock_string(targeted_message.content)

    if sentence is None:
        await markovbot.say('No alphabetic letters were found in previous message. '
                            'Make sure {} uses letters in their message next time you weeb.'.format(user))
        return

    await markovbot.say(sentence)
