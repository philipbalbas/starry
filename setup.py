import os
from dotenv import load_dotenv

load_dotenv()

from composio_julep import App, ComposioToolset

COMPOSIO_API_KEY = os.environ["COMPOSIO_API_KEY"]

toolset = ComposioToolset()
composio_tools = toolset.get_tools(tools=App.GITHUB)


def init_user(client, guild):
    user = client.users.create(
        name="",
        about=f"The Discord Server: {guild.name}")
    print(f"[!] Meta-user created: {user.id} for {guild.name}")
    return user


def init_agent(client):
    name = "Starry"
    about = "Star a github repo"
    default_settings = {
        "temperature": 0.7,
        "top_p": 1,
        "min_p": 0.01,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "length_penalty": 1.0,
        "max_tokens": 1000
    }
    print(f"[!] Creating agent: {name}", composio_tools)
    agent = client.agents.create(
        name=name,
        about=about,
        instructions=[],
        default_settings=default_settings,
        # model="gpt-4",
        model="gpt-3.5-turbo-0613",
        tools=composio_tools
    )
    return agent


def init_session(client, user, agent, channel):
    # A system prompt
    situation_prompt = ""
    session = client.sessions.create(user_id=user.id,
                                     agent_id=agent.id,
                                     situation=situation_prompt)
    print(f"[!] Meta-session created: {session.id} for {channel.name}")
    return session
