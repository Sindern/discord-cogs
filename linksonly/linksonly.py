import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from __main__ import send_cmd_help, settings
from .utils import checks
import re
import os
import time
import asyncio


# Links Only Bot
class LOB:
    """Remove non-link posts after configured interval."""

    def __init__(self, bot):
        self.bot = bot
        self.location = 'data/linksonly/settings.json'
        self.json = dataIO.load_json(self.location)
        self.link_regex = ".*https?://((clips|www)?\.?twitch\.tv|(www)?\.?youtu\.?be(\.com)?)/.*"

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def linksonly(self, ctx):
        """Manage Settings for LinksOnly."""
        serverid = ctx.message.server.id
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
        if serverid not in self.json:
            self.json[serverid] = { 'included_channels': [], 'moveto': ''}

    @linksonly.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def toggle(self, ctx):
        """Toggle cleaning of non-link messages in current channel."""
        serverid = ctx.message.server.id
        try:
            channel=re.sub(' +', ' ', ctx.message.content)
            channel=channel.split(' ')[2]
            channel=re.sub('(^<#|>$)', '', channel)
        except:
            channel = False

        if channel is not False and discord.utils.get(ctx.message.server.channels, id=channel) is None:
            await self.bot.say("Channel not found on this server.")
            channel = False

        if channel is False:
            await self.bot.say("Usage: toggle <channel ID or Link>")
        elif channel not in self.json[serverid]["included_channels"]:
            self.json[serverid]["included_channels"].append(channel)
            await self.bot.say("Added <#" + channel + "> to enforcement.")
        else:
            self.json[serverid]["included_channels"].remove(channel)
            await self.bot.say("Removed <#" + channel + "> from enforcement.")
        dataIO.save_json(self.location, self.json)

    @linksonly.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def status(self, ctx):
        """Show current settings for link enforcement."""
        serverid = ctx.message.server.id
        message="\n**Link-Only Enforcement Status**\nEnabled in: "
        for c in self.json[serverid]["included_channels"]:
            message += " <#" + c + ">"
        message += "\nMove to: <#" + self.json[serverid]["moveto"] + ">"
        message += "Regex: `" + self.link_regex + '`'
        await self.bot.say(message)


    @linksonly.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def moveto(self, ctx):
        """Set ID of channel to move messages to."""
        serverid = ctx.message.server.id
        try:
            channel=re.sub(' +', ' ', ctx.message.content)
            channel=channel.split(' ')[2]
            channel=re.sub('(^<#|>$)', '', channel)
        except:
            channel = False

        if channel is not False and channel != "clear" and discord.utils.get(ctx.message.server.channels, id=channel) is None:
            await self.bot.say("Channel not found on this server.")
            channel = False

        if channel is False:
            usageinfo="```Usage: linksonly moveto <target>\n Target may be: Channel ID, Channel Link, or 'clear' to unset```"
            await self.bot.say(usageinfo)
        elif channel == "clear":
            self.json[serverid]["moveto"] = ""
        elif channel not in self.json[serverid]["moveto"]:
            self.json[serverid]["moveto"] = channel
            await self.bot.say("Messages will be moved to <#" + channel + "> after deletion.")

        dataIO.save_json(self.location, self.json)


    async def _new_message(self, message):
        """Checks if message is in a links-only channel & moves if needed."""
        user = message.author
        serverid = message.server.id
        if message.server is None or user == message.server.me:
            return
        if serverid in self.json:
            if message.channel.id in self.json[serverid]["included_channels"]:
                if re.match(self.link_regex, message.content) is None:
                    await self.bot.delete_message(message)
                    if self.json[serverid]["moveto"] != "":
                        movechannel=message.server.get_channel(self.json[serverid]["moveto"])
                        if movechannel is not None:
                            await self.bot.send_message(movechannel, "Moved! <@" + user.id + "> in <#" + message.channel.id + "> said :: ```" + message.content + "```")

def checkfolder():
    if not os.path.exists('data/linksonly'):
        os.makedirs('data/linksonly')


def checkfile():
    f = 'data/linksonly/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})


def setup(bot):
    checkfolder()
    checkfile()
    n = LOB(bot)
    bot.add_cog( n )
    bot.add_listener(n._new_message, 'on_message')

### NOTES

### Send to specific channel:
# channel = client.get_channel(12324234183172)
# await channel.send('hello')
