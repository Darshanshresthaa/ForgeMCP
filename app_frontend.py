import asyncio
import uuid

import streamlit as st

from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from Agent.service import (
    get_mcp_server,
    get_db_uri,
    get_config,
)

from Agent.nodes import set_tools
from Agent.graph import run_graph, build_graph

# retrive all thread


async def load_threads_from_postgres():

    chats = {}

    async with AsyncPostgresSaver.from_conn_string(get_db_uri()) as memory:

        await memory.setup()


        checkpoints = []

        async for checkpoint in memory.alist(None,limit=300):

            checkpoints.append(checkpoint)

        thread = {}

        for cp in checkpoints:

            thread_id = cp.config['configurable']['thread_id']

            if thread_id not in thread:
                thread[thread_id] = cp


        # loading the contents

        for thread_id,checkpoint in thread.items():

            # actual thread content
            state = checkpoint.checkpoint

            values = state.get("channel_values",{})

            messages = values.get('messages',[])

            chat_message = []

            for message in messages:

                if not hasattr(message, "type"):
                    continue

                if message.type == "human":
                    role = "user"

                elif message.type == "ai":
                    role = "assistant"

                else:
                    continue

                content = message.content


                if content:

                    chat_message.append({
                        'role':role,
                        'content':str(content)
                    })


            title = "New-Chat"

            for message in chat_message:

                title = message['content'][:30]
                break

            chats[thread_id] = {
                'title':title,
                'messages':chat_message
            }


    return chats



# Session define

if 'chats' not in st.session_state:
    st.session_state.chats = asyncio.run(load_threads_from_postgres())


# if post has no chats
if not st.session_state.chats:

    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        'title':'New-Chat',
        'messages':[]
    }


# current chat

if "current_chat" not in st.session_state:
    st.session_state.current_chat = list(st.session_state.chats)[-1] 


# invoking graph

async def run_graph_ui(question,chat_id):
    client = MultiServerMCPClient(get_mcp_server())

    tools = await client.get_tools()

    set_tools(tools)

    config = get_config()

    config["configurable"]["thread_id"] = chat_id


    async with AsyncPostgresSaver.from_conn_string(get_db_uri()) as memory:

       await memory.setup()

       graph = build_graph().compile(
           checkpointer=memory
       )

       result = await run_graph(
           graph = graph,
           question = question,
           config = config,
           messages =[HumanMessage(content=question)]
       )

    return result


# ui
st.markdown(
    """
    <div style="
        border: 1px solid #555;
        padding: 8px 12px;
        border-radius: 6px,6px,0px,6px;
    ">
        <p style="
            text-align: center;
            margin: 0;
        ">
            Forge-MCP
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="
        border: 1px solid #555;
        padding: 8px 12px;
        border-radius: 6px;
    ">
        <p style="
            text-align: right;
            margin: 0;
        ">
            Your MCP-powered GitHub assistant
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

with st.sidebar:

    st.title("Forge MCP")

    if st.button("New-Chat"):

        chat_id = str(uuid.uuid4())

        st.session_state.chats[chat_id] = {
            "title": f"New-Chat {chat_id}",
            "messages": []
        }

        st.session_state.current_chat = chat_id

        st.rerun()


# listing chats

    for chat_id,chat in st.session_state.chats.items():

        title = chat['title']

        if len(title) > 28:
        
            title = title[:28] + "..."
        
        if chat_id == st.session_state.current_chat:
        
            title = "****" + title + "***"

        else:
            title = title

        if st.button(title,
                    key=chat_id,
                    width="stretch"):

            st.session_state.current_chat = chat_id
            
            st.rerun()


# current chat
chat = st.session_state.chats[
    st.session_state.current_chat
    ]


for message in chat["messages"]:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])



# user input

question = st.chat_input("Ask Anythins..")

if question:
    chat['messages'].append({
        'role':'user',
        'content':question
    })

if chat['title'] =="New-Chat":

    chat['title'] = question[:30]

with st.chat_message('user'):
    st.markdown(question)


with st.chat_message('ai'):

    try:
        with st.spinner("Processing Work ...."):
            result =asyncio.run(
                run_graph_ui(
                        question=question,
                        chat_id=st.session_state.current_chat
                        ))

        outputs = {}

        for key,value in result.items():

            outputs[key] = str(value)


        for key,value in outputs.items():
            st.markdown(
                f"### {key.replace('_', ' ').title()}"
                        )
            
            st.markdown(value)

        content = ""
        for key, value in outputs.items():
            content += f"### {key.replace('_', ' ').title()}\n\n{value}\n\n"

        chat['messages'].append({
            'role':'ai',
            'content':content
        })

    except Exception as ex:
        error = str(ex)
        st.error(error)

        chat['messages'].append({
            'role':'ai',
            'content':error
        })
        






