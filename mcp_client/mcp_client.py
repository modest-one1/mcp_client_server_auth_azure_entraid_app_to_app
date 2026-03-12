# Streamlit app for MCP client with Device Flow Authentication
# -------------------------------------------------------------
# This app initiates device flow authentication on access, acquires a token, and uses it to connect to MCP server.
# The rest of the app logic is similar to the original webapp.py.

import os
import asyncio
import streamlit as st
from dotenv import load_dotenv
from msal import ConfidentialClientApplication
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from logger import logger
import traceback
from typing import List

load_dotenv()

# -----------------------------

CLIENT_ID = os.getenv("CLIENT_ID", "<your-client-id>")
TENANT_ID = os.getenv("TENANT_ID", "<your-tenant-id>")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "<your-client-secret>")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = [os.getenv("API_SCOPE", "https://graph.microsoft.com/.default")]

app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)

if "access_token" not in st.session_state:
    st.header("Acquiring token using client credentials")
    result = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" in result:
        st.session_state.access_token = result["access_token"]
        print("Token acquired using confidential client")
        print(f"Access Token: {st.session_state.access_token}")  # Print first 50 chars
        st.success("Token acquired using confidential client!")
    else:
        st.error(f"Token acquisition failed: {result.get('error_description', 'Unknown error')}")

# -----------------------------
# Config & helpers
# -----------------------------
DEFAULT_MCP_URL = os.getenv("MCP_URL", "http://localhost:8000/mcp")
DEFAULT_MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable_http")
DEFAULT_AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
DEFAULT_AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
DEFAULT_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

st.set_page_config(page_title="MCP LangGraph Chat (Auth)", page_icon="🔒", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = None
if "tools_info" not in st.session_state:
    st.session_state.tools_info = []

# -----------------------------
# Async builder (with token)
# -----------------------------
async def build_agent(azure_endpoint, deployment, mcp_url, mcp_transport, access_token):
    client_config = {
        "RAG": {
            "url": mcp_url,
            "transport": mcp_transport,
        }
    }
    if access_token:
        client_config["RAG"]["headers"] = {"Authorization": f"Bearer {access_token}"}
    client = MultiServerMCPClient(client_config)
    tools = await client.get_tools()
    model = AzureChatOpenAI(
        azure_endpoint=azure_endpoint,
        api_version=DEFAULT_API_VERSION,
        name=deployment,
    )
    agent = create_agent(model, tools)
    return agent, tools

# -----------------------------
# Sidebar settings
# -----------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    azure_endpoint = st.text_input("Azure OpenAI Endpoint", value=DEFAULT_AZURE_ENDPOINT)
    deployment = st.text_input("Azure OpenAI Deployment name", value=DEFAULT_AZURE_DEPLOYMENT)
    st.divider()
    mcp_url = st.text_input("MCP URL", value=DEFAULT_MCP_URL)
    mcp_transport = st.selectbox("MCP Transport", ["streamable_http", "stdio"], index=0 if DEFAULT_MCP_TRANSPORT=="streamable_http" else 1)
    init_clicked = st.button("Initialize / Reconnect", type="primary")

# -----------------------------
# Initialize / Reconnect agent
# -----------------------------
init_required = (
    st.session_state.agent is None
    or init_clicked
)

if init_required:
    if not azure_endpoint or not deployment:
        st.sidebar.warning("Please provide Azure endpoint and deployment name, then click Initialize.")
    elif "access_token" not in st.session_state:
        st.sidebar.warning("Authenticate first to acquire access token.")
    else:
        try:
            with st.sidebar.status("Connecting to MCP and Azure OpenAI…", expanded=False):
                st.session_state.agent, st.session_state.tools_info = asyncio.run(
                    build_agent(azure_endpoint, deployment, mcp_url, mcp_transport, st.session_state.access_token)
                )
            st.sidebar.success("Agent connected ✅")
        except Exception as e:
            st.sidebar.error(f"Initialization failed: {e}")

# -----------------------------
# Header
# -----------------------------
st.title("🔒 MCP + LangGraph Chat (Auth)")

if st.session_state.tools_info:
    with st.expander("Available tools (from MCP)"):
        for t in st.session_state.tools_info:
            name = t.get("name") if isinstance(t, dict) else getattr(t, "name", "(unknown)")
            desc = t.get("description") if isinstance(t, dict) else getattr(t, "description", "")
            st.markdown(f"- **{name}** — {desc}")

# -----------------------------
# Chat history
# -----------------------------
for m in st.session_state.messages:
    role = "user" if isinstance(m, HumanMessage) else "assistant"
    with st.chat_message(role):
        show_message = True
        if role == "assistant":
            content = m.content if isinstance(m.content, str) else str(m.content)
            if content.strip().upper().startswith("CONTEXT:"):
                show_message = False
            elif len(content) > 2000:
                show_message = False
            elif content.count("\n") > 30:
                show_message = False
            if hasattr(m, "metadata") and m.metadata.get("type") == "retrieved_chunk":
                show_message = False
        if show_message:
            st.markdown(m.content if isinstance(m.content, str) else str(m.content))


# -----------------------------
# Upload & ingest files (calls your sync ingest_path)
# -----------------------------
# -----------------------------
# Chat input / inference
# -----------------------------
user_input = st.chat_input("Type your message…")

async def run_turn(agent, user_text: str):
    user_text += "\n\n the userid is: sanda_vineeth"
    st.session_state.messages.append(HumanMessage(content=user_text))
    result = await agent.ainvoke({"messages": st.session_state.messages})
    st.session_state.messages = result["messages"]
    last_ai = "(no AI reply)"
    for m in reversed(st.session_state.messages):
        if isinstance(m, AIMessage) or getattr(m, "type", "") == "ai":
            c = getattr(m, "content", "")
            last_ai = c if isinstance(c, str) else str(c)
            break
    return last_ai

if user_input is not None and user_input.strip():
    if st.session_state.agent is None:
        st.warning("Please initialize the agent in the sidebar first.")
    else:
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            try:
                reply_text = asyncio.run(run_turn(st.session_state.agent, user_input))
                placeholder.markdown(reply_text)
            except Exception as e:
                placeholder.error(f"[Error] {e}")

# -----------------------------
# Footer
# -----------------------------
st.caption(
    "This UI wraps your async ReAct agent with Device Flow authentication. Ensure your MCP server is reachable and Azure credentials are set."
)
