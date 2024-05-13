from discord.ext.commands.bot import app_commands
import asyncio
import os
from julep import Client
import discord
from discord.ext import commands
import re
import json
# from tools import get_gif
import random
from setup import init_agent, init_user, init_session, toolset
from db import conn, setup_database, get_agent_id, set_agent_id,  delete_all_sessions, session_exists, set_session, get_session_ids
from dotenv import load_dotenv
import sqlite3
from typing import Final
from random import choice, randint


load_dotenv()

TOKEN: Final[str] = os.environ["TOKEN"]
JULEP_API_KEY: Final[str] = os.environ["JULEP_API_KEY"]


print("Julep API Key:", JULEP_API_KEY)
client = Client(api_key=JULEP_API_KEY, base_url="https://dev.julep.ai/api")

intents: discord.Intents = discord.Intents.default()
intents.message_content = True
intents.typing = True
intents.presences = True
intents.members = True
intents.reactions = True

####################################################
# User Variables

description = ""  # A description for the Discord App
CHANNEL_NAME = ""  # Name of the channel in the Discord server the deploy the bot to

####################################################

if conn is not None:
    setup_database(conn)

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    description=description
)
# Format the message to ensure it's a valid OpenAI acceptable message
def format_msg(msg, mentions, author):
    msg = msg.replace("#", "")
    for user in mentions:
        mentioned_name = user.global_name if user.global_name is not None else user.name

        msg = msg.replace(f"<@{user.id}>", f"@{mentioned_name}")
    print(f"[!] Formatted message: {msg}")
    formatted_msg = {
        "role": "user",
        "content": msg,
        "name": author.replace(".", "_").split()[0],
    }
    print(formatted_msg)
    return formatted_msg


@bot.event
async def on_ready():
    # await bot.tree.sync()
    print(f"[!] Logged in as {bot}:{bot.user.id}")

@bot.event
async def on_reaction_add(reaction, user):
    print("reaction added")
    print(reaction)
    print(user)

# @bot.event
# async def on_message(message):
#     print("message received", message)
#     if message.author == bot.user or message.channel.name != CHANNEL_NAME:
#         return
#     print(message.content)
#     guild_id = str(message.guild.id)
#     channel_id = str(message.channel.id)
#     user_id = db[guild_id]
#     session_id = db[channel_id]

#     print(f"[*] Detected message: {message.content}")
#     discord_user_name = str(message.author.global_name)
#     print(
#         f"[!] Responding to user_id: {user_id} over session_id: {session_id}")
#     formatted_msg = format_msg(msg=message.content,
#                                mentions=message.mentions,
#                                author=message.author.global_name)
#     print(f"[*] {discord_user_name}: ", formatted_msg)
#     res = client.sessions.chat(
#         session_id=session_id,
#         messages=[formatted_msg],
#         stream=False,
#         max_tokens=140,
#         recall=True,  # Recalls the previous messages.
#         remember=True,  # Saves the LLM response to history and memory.
#     )
#     print(f"[!] Response: {res}")
#     bot_response = res.response[0][0]
#     if bot_response.role.value == "assistant":
#         await message.reply(bot_response.content, mention_author=True)
#     elif bot_response.role.value == "function_call":
#         print(f"Tool Call: {bot_response.content}")
#         tool_call = json.loads(bot_response.content)
#         args = tool_call.get("arguments")
#         func_name = tool_call.get("name")
#         # if func_name == "get_gif":
#             # gif_url = compose.(args)
#             # await message.reply(gif_url, mention_author=True)


def format_msg(msg, mentions, author):
    msg = msg.replace("#", "")
    for user in mentions:
        if user.global_name is not None:
            mentioned_name = user.global_name
        else:
            mentioned_name = user.name
        msg = msg.replace(f"<@{user.id}>", f"@{mentioned_name}")
    print(f"[!] Formatted message: {msg}")
    formatted_msg = {
        "role": "user",
        "content": msg,
        "name": author.replace(".", "_").split()[0],
    }
    print(formatted_msg)
    return formatted_msg

@bot.event
@commands.has_role("admin")
async def on_message(message):
    # if message.author == bot.user or message.channel.name != CHANNEL_NAME:
    #     return

    print("message received before")
    if message.author == bot.user:
        return

    print("message received after")
    try:
        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)

        # Retrieve user and session IDs from SQLite
        user_id, session_id = get_session_ids(guild_id=guild_id)

        print(f"[*] User ID: {user_id}, Session ID: {session_id}")
        if not user_id or not session_id:
            await message.channel.send("[!] No session data found for this guild/channel.")
            return

        print(f"[*] Detected message: {message.content}")
        discord_user_name = str(message.author.global_name)
        print(f"[!] Responding to user_id: {user_id} over session_id: {session_id}")

        # Format the message for chat processing
        formatted_msg = format_msg(msg=message.content, mentions=message.mentions, author=discord_user_name)
        print(f"[*] {discord_user_name}: {formatted_msg}")

        # Send message to the chat client session
        res = client.sessions.chat(
            session_id=session_id,
            messages=[formatted_msg],
            stream=False,
            max_tokens=500,
            recall=True,    # Recalls previous messages.
            remember=True,  # Saves the LLM response to history and memory.
        )
        print(f"[!] Response: {res}")

        # Respond to the message based on role type
        bot_response = res.response[0][0]
        print(f"[*] Bot Response: {bot_response.role.value}")
        if bot_response.role.value == "assistant":
            await message.reply(bot_response.content, mention_author=True)
        elif bot_response.role.value == "function_call":
            print(f"Tool Call: {bot_response.content}")
            tool_call = json.loads(bot_response.content)
            args = tool_call.get("arguments")
            func_name = tool_call.get("name")
            print(f"Function Name: {func_name}, Arguments: {args}")
            execution_output = toolset.handle_tool_calls(res)
            print(f"Execution Output: {execution_output}")
        #     # if func_name == "get_gif":
        #     #     gif_url = get_gif(args)
        #     #     await message.reply(gif_url, mention_author=True)

    except Exception as e:
        print(f"Error in `on_message` event: {e}")
        await message.channel.send("[!] An unexpected error occurred.")

@bot.hybrid_command(name="sync")
@commands.has_role("admin")
async def sync(ctx):
    print("[!] Syncing commands")
    await bot.tree.sync(guild=ctx.guild)
    await ctx.send("[!] Commands synced")


@bot.hybrid_command()
@commands.has_role("admin")
async def ping(ctx):
    await ctx.send("pong")


@bot.hybrid_command(name="setup_agent")
@commands.has_role("admin")
async def setup_agent(ctx):
    try:
        if get_agent_id():
            await ctx.send("[!] Bot is already live")
            return

        agent = init_agent(client)
        set_agent_id(agent.id)
        await ctx.send(f"[!] Bot is live now")
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Error in `setup_agent` command: {e}")
        await ctx.send("[!] An error occurred while setting up the bot agent")


@bot.hybrid_command(name="setup_session")
@commands.has_role("admin")
async def setup_session(ctx: commands.Context):
    guild = ctx.guild
    channel = ctx.channel

    try:
        agent_id = get_agent_id()
        if not agent_id:
            await ctx.send("[!] No agent found; ensure an agent is set up before creating sessions.")
            return

        if session_exists(str(guild.id), str(channel.id)):
            await ctx.send("[!] Session for this channel already exists")
            return

        agent = client.agents.get(agent_id)
        user = init_user(client, guild)
        session = init_session(client, user, agent, channel)

        print(f"[*] User ID: {user.id}, Session ID: {session.id}, Channel ID: {channel.id}, Guild ID: {guild.id}")

        set_session(
            guild_id=str(guild.id),
            channel_id=str(channel.id),
            user_id= user.id,
            session_id= session.id
        )
        await ctx.send("[!] Session for this channel created")

    except Exception as e:
        # General exception handling for unexpected errors
        print(f"Error in `setup_session` command: {e}")
        await ctx.send("[!] An error occurred while setting up the session")


@bot.hybrid_command(name="clear_history")
@commands.has_role("admin")
async def clear_session_history(ctx):
    session_id = get_session_id(str(ctx.channel.id))
    if session_id:
        client._api_client.delete_session_history(session_id=session_id)
        await ctx.send(f"Session history for `{session_id}` cleared")
    else:
        await ctx.send("[!] No session found to clear")

@bot.hybrid_command(name="delete_all")
@commands.has_role("admin")
async def delete_all(ctx):
    delete_all_sessions()
    for session in client.sessions.list():
        client.sessions.delete(session.id)
    for agent in client.agents.list():
        client.agents.delete(agent.id)
    for user in client.users.list():
        client.users.delete(user_id=user.id)
    await ctx.send("[!] All sessions, agents, and users have been deleted")

# @bot.hybrid_command(name="dump_ids")
# @commands.has_role("admin")
# async def dump_ids(ctx):
#     guild = ctx.guild
#     channel = ctx.channel
#     try:
#         session_id = db[str(channel.id)]
#         user_id = db[str(guild.id)]
#         agent_id = db["agent"]
#         res = f"""
# `session_id: {session_id}`
# `channel_id: {channel.id}`
# `agent_id: {agent_id}`
# `user_id: {user_id}`
# `guild_id: {guild.id}`
#     """
#     except Exception as e:
#         res = f"[!] No session or user found for channel: {channel.id}"
#     await ctx.reply(res, ephemeral=True)





# @bot.event
# async def on_member_join(member):
#     guild = member.guild
#     if guild.sytem_channel is not None:
#         to_send = f'Welcome {member.mention} to {guild.name}!'
#         await guild.system_channel.send(to_send)


# @bot.command()
# async def roll(ctx, dice: str):
#     """Rolls a dice in NdN format."""
#     print('rolling dice')
#     try:
#         rolls, limit = map(int, dice.split('d'))
#     except Exception:
#         await ctx.send('Format has to be in NdN!')
#         return

#     result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
#     await ctx.send(result)




@bot.hybrid_command()
async def add(ctx: commands.Context, left: int, right: int):
    """Adds two numbers together."""
    print("wat")
    await ctx.send(left + right)

# @bot.tree.command(name="hello")
# async def hello(interaction: discord.Interaction):
#     response = await client.sessions.chat(session_id)



def main() -> None:
    try:
        if TOKEN == "":
            raise Exception("Please add your token to the Secrets pane.")
        bot.run(token=TOKEN)
    except discord.HTTPException as e:
        if e.status == 429:
            print(
                "The Discord servers denied the connection for making too many requests"
            )
            print(
                "Get help from https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests"
            )
        else:
            raise e

if __name__ == "__main__":
    main()
