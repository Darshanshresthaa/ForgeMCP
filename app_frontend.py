import streamlit as st
from Agent.service import (
    get_mcp_server,
    get_db_uri,
    get_config,
)

from Agent.nodes import set_tools
from Agent.graph import run_graph, build_graph

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver



# retrive all thread


async def load_threads_from_postgres():

    chats = {}

    async with AsyncPostgresSaver.from_conn_string(get_db_uri()) as memory:

        await memory.setup()


        checkpoints = []

        async for checkpoint in memory.alist(None,limit=300):

            checkpoints.append(checkpoint)

        thread = {}

        for cp in checkpoint:

            thread_id = cp['configurable']['thread_id']

            if thread_id not in thread:
                thread[thread_id] = checkpoint


        # loading the contents

        for thread_id,checkpoint in thread.items():

            # actual thread content
            state = checkpoint.checkpoint

            values = state.get("channel_values",{})

            messages = values.get(['messages'],[])

            chat_message = []

            for message in messages:

                if hasattr(message,'type'):

                    if message.type =='user':
                        role = 'user'

                    elif message.type =='ai':
                        role = 'ai'

                    else:
                        continue

                content = message.content

                if content:

                    chat_message.append({
                        'role':role,
                        'messages':str(content)
                    })


            title = "New-Chat"

            for message in chat_message:

                title = chat_message['user'][:30]
                break

            chats[thread_id] = {
                'title':title,
                'messages':chat_message
            }


    return chats




