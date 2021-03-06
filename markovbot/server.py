import time
import asyncio
import logging
import threading

import discord

from markovbot import datastore, markov

log = logging.getLogger(__name__)


class ServerContext:
    """
    The Server Context with the client this server is 
    using to communicate, and the server itself.

    :param client: The CancerBotClient the server is using, doing this
    could allow for multiple clients to be spun up in the future, but
    we are only using one right now.

    :param server: The server this context is pertaining too.
    """
    def __init__(self, client, server):
        self._client = client

        self._server = server

        self._is_ready = False

        self.markov_manager = markov.MarkovManager(self)

    # TODO: This is going to be temporary till
    # a better way to handle server initialization
    # is determined, cant really do this in the
    # constructor since is it async
    async def init(self):
        if self.is_new_server():
            datastore.update_server(self.server)

            log.debug('New Server [%s]. Downloading last 50,000 messages', self.server.name)
            await self._seed_messages()
            
        else:
            datastore.update_server(self.server)

        log.info('%s data has been seeded. The server is ready to accept commands', self.server.name)
        self._is_ready = True

    def is_new_server(self):
        return datastore.get_server(self.server.id) is None

    async def _seed_messages(self):
        # TODO: Figure out better way to handle channels
        # This will just get the first text channel in the channel list, which the user
        # could not want.
        channel = discord.utils.get(self.server.channels, type=discord.ChannelType.text)

        BULK_SIZE = 500 
        bulk_data = []

        async for message in self.client.logs_from(channel, limit=50000):
            content = message.content
            author = message.author

            # Conditions for us to insert a message into the database.
            # 1. The author is not a bot.
            # 2. The message is more than one word.
            # 3. The message does not start with '!' (This should weed out most commands)
            # 4. The message is not a link.

            if not author.bot and len(content.split()) > 1 and not content.startswith(('!', 'http')):
                bulk_data.append(message)

            if len(bulk_data) >= BULK_SIZE:
                datastore.add_messages(bulk_data)
                bulk_data.clear()

        if len(bulk_data) > 0:
            datastore.add_messages(bulk_data)

    @property
    def is_ready(self):
        return self._is_ready

    @property
    def client(self):
        return self._client

    @property
    def server(self):
        return self._server

    @property
    def markov(self):
        return self.markov_manager


class ServerManager:
    def __init__(self, client):
        """
        The client that is using this server manager
        instance.
        """
        self.client = client

        """
        A map that represents all connected servers for
        this instance of a server manager.

        The map uses the id of the server as the key, and the
        server context is the value.
        """
        self.connected_servers = {}

    def get_server_context(self, server):
        return self.connected_servers.get(server.id)

    async def add(self, server):
        """
        Create a new server context object and add it
        to the connected_servers map.

        :param server: The discord server object.
        """
        context = ServerContext(self.client, server)

        self.connected_servers[server.id] = context

        await context.init()

    def remove(self, server):
        """
        Remove a server from the connected servers map.

        :param server: The discord server object.
        """
        if server.id in self.connected_servers:
            del self.connected_servers[server.id]
