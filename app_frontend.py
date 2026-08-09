import asyncio
import uuid

import streamlit as st

from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command

from Agent.service import (
    get_mcp_server,
    get_db_uri,
    get_config,
)

from Agent.db_utils import clear_postgres_data
from Agent.nodes import set_tools
from Agent.graph import build_graph



if "chats" not in st.session_state:
    st.session_state.chats = {}


if "current_chat" not in st.session_state:
    st.session_state.current_chat = None


if "hitl_required" not in st.session_state:
    st.session_state.hitl_required = False


if "interrupt_data" not in st.session_state:
    st.session_state.interrupt_data = None



# RUN GRAPH


async def run_graph_ui(question, chat_id):

    client = MultiServerMCPClient(
        get_mcp_server()
    )

    tools = await client.get_tools()

    set_tools(tools)

    config = get_config()

    config["configurable"]["thread_id"] = chat_id

    async with AsyncPostgresSaver.from_conn_string(
        get_db_uri()
    ) as memory:

        await memory.setup()

        graph = build_graph().compile(
            checkpointer=memory
        )

        async for chunk in graph.astream(
            {
                "question": question,
                "messages": [
                    HumanMessage(content=question)
                ],
            },
            config=config,
            stream_mode="updates",
        ):
            yield chunk


# HITL resume
async def resume_graph_ui(chat_id, approval):

    client = MultiServerMCPClient(
        get_mcp_server()
    )

    tools = await client.get_tools()

    set_tools(tools)

    config = get_config()

    config["configurable"]["thread_id"] = chat_id

    async with AsyncPostgresSaver.from_conn_string(
        get_db_uri()
    ) as memory:

        await memory.setup()

        graph = build_graph().compile(
            checkpointer=memory
        )

        async for chunk in graph.astream(
            Command(resume=approval),
            config=config,
            stream_mode="updates",
        ):
            yield chunk



# Load post thread
async def load_threads_from_postgres():

    chats = {}

    async with AsyncPostgresSaver.from_conn_string(
        get_db_uri()
    ) as memory:

        await memory.setup()

        checkpoints = []

        async for checkpoint in memory.alist(
            None,
            limit=300,
        ):
            checkpoints.append(checkpoint)

      
        threads = {}

        for checkpoint in checkpoints:

            thread_id = checkpoint.config[
                "configurable"
            ]["thread_id"]

            if thread_id not in threads:
                threads[thread_id] = checkpoint

    

        for thread_id, checkpoint in threads.items():

            state = checkpoint.checkpoint

            values = state.get(
                "channel_values",
                {}
            )

            messages = values.get(
                "messages",
                []
            )

            chat_messages = []

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

                    chat_messages.append(
                        {
                            "role": role,
                            "content": str(content),
                        }
                    )

            # Generate title from first user message

            title = "New-Chat"

            for message in chat_messages:

                if message["role"] == "user":

                    title = message["content"][:30]

                    break

            chats[thread_id] = {
                "title": title,
                "messages": chat_messages,
            }

    return chats




if not st.session_state.chats:

    st.session_state.chats = asyncio.run(
        load_threads_from_postgres()
    )



if not st.session_state.chats:

    chat_id = str(uuid.uuid4())

    st.session_state.chats[chat_id] = {
        "title": "New-Chat",
        "messages": [],
    }

    st.session_state.current_chat = chat_id



if st.session_state.current_chat is None:

    st.session_state.current_chat = list(
        st.session_state.chats
    )[-1]



async def consume_stream(
    question,
    chat_id,
    placeholder,
):

    content = ""
    interrupted = False
    interrupt_data = None

    async for chunk in run_graph_ui(
        question=question,
        chat_id=chat_id,
    ):


        if not isinstance(chunk, dict):
            continue

#   usually false for normal tools

        if "__interrupt__" in chunk:

            interrupted = True
            interrupt_data = chunk["__interrupt__"]

            continue

        for node_name, state_update in chunk.items():


            if not isinstance(state_update, dict):
                continue

            for key, value in state_update.items():

                if key == "messages":
                    continue

     
                section = (
                    f""
                    f"{key.replace('_', ' ').title()}"
                    f"\n\n"
                    f"{value}"
                    f"\n\n"
                )

                content += section

                placeholder.write(
                    content
                )

    return (
        content,
        interrupted,
        interrupt_data,
    )




async def consume_resume_stream(
    chat_id,
    approval,
    placeholder,
):

    content = ""
    interrupted = False
    interrupt_data = None

    async for chunk in resume_graph_ui(
        chat_id=chat_id,
        approval=approval,
    ):

        if not isinstance(chunk, dict):
            continue

        if "__interrupt__" in chunk:

            interrupted = True
            interrupt_data = chunk["__interrupt__"]

            continue

        for node_name, state_update in chunk.items():

            if not isinstance(state_update, dict):
                continue

            for key, value in state_update.items():

                # Ignore messages

                if key == "messages":
                    continue

                section = (
                    f"### "
                    f"{key.replace('_', ' ').title()}"
                    f"\n\n"
                    f"{value}"
                    f"\n\n"
                )

                content += section

                placeholder.write(
                    content
                )

    return (
        content,
        interrupted,
        interrupt_data,
    )


def extract_interrupt_message(interrupt_data):

    """
    Pull a clean, human-readable message out of the raw
    __interrupt__ payload (a tuple of langgraph Interrupt
    objects, each wrapping the dict passed to interrupt()).
    """

    if not interrupt_data:
        return "This action requires your approval."

    messages = []

    for item in interrupt_data:

        value = getattr(item, "value", item)

        if isinstance(value, dict):
            messages.append(
                str(value.get("message", value))
            )
        else:
            messages.append(str(value))

    return (
        "\n\n".join(messages)
        if messages
        else "This action requires your approval."
    )


st.markdown(
    """
    <div style="
        border: 1px solid #555;
        padding: 8px 12px;
        border-radius: 6px;
    ">
        <p style="
            text-align: center;
            margin: 0;
        ">
            Forge-MCP
        </p>
    </div>
    """,
    unsafe_allow_html=True,
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
    unsafe_allow_html=True,
)


with st.sidebar:

    st.title("Forge MCP")


    if st.button("New-Chat"):

        chat_id = str(uuid.uuid4())

        st.session_state.chats[chat_id] = {
            "title": "New-Chat",
            "messages": [],
        }

        st.session_state.current_chat = chat_id

    

        st.session_state.hitl_required = False
        st.session_state.interrupt_data = None

        st.rerun()


    for chat_id, chat_data in (
        st.session_state.chats.items()
    ):

        title = chat_data["title"]

        if len(title) > 28:

            title = title[:28] + "..."

        if (
            chat_id
            == st.session_state.current_chat
        ):

            title = "****" + title + "***"

        if st.button(
            title,
            key=f"chat_{chat_id}",
            width="stretch",
        ):

            st.session_state.current_chat = chat_id

            st.session_state.hitl_required = False
            st.session_state.interrupt_data = None

            st.rerun()


    button_res = st.button("Reset-DB")

    if button_res:

        clear_postgres_data()

        st.session_state.chats = {}

        chat_id = str(uuid.uuid4())

        st.session_state.chats[chat_id] = {
            "title": "New-Chat",
            "messages": [],
        }

        st.session_state.current_chat = chat_id

        st.session_state.hitl_required = False
        st.session_state.interrupt_data = None

        st.rerun()


chat = st.session_state.chats[
    st.session_state.current_chat
]


for message in chat["messages"]:

    with st.chat_message(
        message["role"]
    ):

        st.write(
            message["content"]
        )



@st.dialog(" Approval Required")
def hitl_approval_dialog():

    message = extract_interrupt_message(
        st.session_state.interrupt_data
    )

    st.write(message)

    col1, col2 = st.columns(2)

    with col1:
        approve_clicked = st.button(
            " Approve",
            key="approve_hitl",
            width="stretch",
            type="primary",
        )

    with col2:
        reject_clicked = st.button(
            " Reject",
            key="reject_hitl",
            width="stretch",
        )

    if not (approve_clicked or reject_clicked):
        return

    approval = approve_clicked

    placeholder = st.empty()

    try:

        with st.spinner(
            "Executing approved action..."
            if approval
            else "Rejecting action..."
        ):

            (
                content,
                interrupted_again,
                new_interrupt_data,
            ) = asyncio.run(
                consume_resume_stream(
                    chat_id=(
                        st.session_state
                        .current_chat
                    ),
                    approval=approval,
                    placeholder=placeholder,
                )
            )

        if content:

            chat["messages"].append(
                {
                    "role": "assistant",
                    "content": content,
                }
            )

        if interrupted_again:

            st.session_state.hitl_required = True
            st.session_state.interrupt_data = new_interrupt_data

        else:

            st.session_state.hitl_required = False
            st.session_state.interrupt_data = None

        st.rerun()

    except Exception as ex:

        st.error(
            str(ex)
        )


if st.session_state.hitl_required:

    hitl_approval_dialog()



question = st.chat_input(
    "Ask Anything.."
)


if question:


    chat["messages"].append(
        {
            "role": "user",
            "content": question,
        }
    )

    if chat["title"] == "New-Chat":

        chat["title"] = str(question)[:30]

    with st.chat_message("user"):

        st.markdown(question)

    with st.chat_message("assistant"):

        try:

            placeholder = st.empty()

            with st.spinner(
                "Processing Work ...."
            ):

                (
                    content,
                    interrupted,
                    interrupt_data,
                ) = asyncio.run(
                    consume_stream(
                        question=question,
                        chat_id=(
                            st.session_state
                            .current_chat
                        ),
                        placeholder=placeholder,
                    )
                )
            if content:

                chat["messages"].append(
                    {
                        "role": "assistant",
                        "content": content,
                    }
                )
            if interrupted:

                st.session_state.hitl_required = True

                st.session_state.interrupt_data = (
                    interrupt_data
                )

                st.rerun()

        except Exception as ex:

            error = str(ex)

            st.error(error)

            chat["messages"].append(
                {
                    "role": "assistant",
                    "content": error,
                }
            )
