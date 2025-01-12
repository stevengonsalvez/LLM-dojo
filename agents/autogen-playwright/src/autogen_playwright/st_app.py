"""
This is a demo of AutoGen chat agents. You can use it to chat with OpenAI's GPT-3 and GPT-4 models. They are able to execute commands, answer questions, and even write code.
An example a question you can ask is: 'How is the S&P 500 doing today? Summarize the news for me.'
UserProxyAgent is used to send messages to the AssistantAgent. The AssistantAgent is used to send messages to the UserProxyAgent.

"""


from autogen_playwright.prompts.prompts import WEB_TESTER_PROMPT
import streamlit as st
import asyncio
from autogen import AssistantAgent, UserProxyAgent

# setup page title and description
st.set_page_config(page_title="AutoGen Chat app", page_icon="🤖", layout="wide")

# Add custom CSS for the chat container
st.markdown("""
    <style>
    .chat-container {
        height: 600px;
        overflow-y: auto;
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("🤖 **Synthetic Testing Agent**")
st.markdown("""
This is an automated testing agent that converts plain English instructions into executable test steps. 

Format your test steps either:
- One step per line
- As comma-separated steps

Examples:
```
go to google.com, search for playwright, click first result

OR

go to google.com
search for playwright
click first result
```
""")
st.markdown("Start by providing your OpenAI API key in the sidebar →")


class TrackableAssistantAgent(AssistantAgent):
    """
    A custom AssistantAgent that tracks the messages it receives.

    This is done by overriding the `_process_received_message` method.
    """

    def _process_received_message(self, message, sender, silent):
        with chat_history:
            with st.chat_message(sender.name):
                st.markdown(message)
        return super()._process_received_message(message, sender, silent)


class TrackableUserProxyAgent(UserProxyAgent):
    """
    A custom UserProxyAgent that tracks the messages it receives.

    This is done by overriding the `_process_received_message` method.
    """

    def _process_received_message(self, message, sender, silent):
        with chat_history:
            with st.chat_message(sender.name):
                st.markdown(message)
        return super()._process_received_message(message, sender, silent)


# add placeholders for selected model and key
selected_model = None
selected_key = None

# setup sidebar: models to choose from and API key input
with st.sidebar:
    st.header("OpenAI Configuration")
    selected_model = st.selectbox("Model", ["gpt-3.5-turbo", "gpt-4-1106-preview"], index=1)
    st.markdown("Press enter to save key")
    st.markdown(
        "For more information about the models, see [here](https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo)."
    )
    selected_key = st.text_input("API Key", type="password")

# setup main area: user input and chat messages
chat_container = st.container()
with chat_container:
    # Create a container for the chat history with a fixed height
    chat_history = st.container()
    
    # Add a horizontal line to separate chat and input
    st.markdown("---")
    
    # Create the input area at the bottom
    user_input = st.text_area("Your message", height=100, key="user_input")
    
    # Add a submit button
    if st.button("Send", type="primary"):
        if not user_input:  # Skip if user input is empty
            st.stop()
            
        if not selected_key or not selected_model:
            st.warning("You must provide valid OpenAI API key and choose preferred model", icon="⚠️")
            st.stop()
        # setup request timeout and config list
        llm_config = {
            "config_list": [
                {
                    "model": selected_model,
                    "api_key": selected_key,
                    "timeout": 600
                }
            ],
            "seed": 42,  # seed for reproducibility
            "temperature": 0  # temperature of 0 means deterministic output
        }
        # create an AssistantAgent instance named "assistant"
        assistant = TrackableAssistantAgent(name="assistant", system_message=WEB_TESTER_PROMPT, llm_config=llm_config)

        # create a UserProxyAgent instance named "user"
        # human_input_mode is set to "NEVER" to prevent the agent from asking for user input
        user_proxy = TrackableUserProxyAgent(
            name="user",
            human_input_mode="NEVER",
            llm_config=llm_config,
            is_termination_msg=lambda x: x.get("content", "").strip().endswith("TERMINATE"),
            code_execution_config={
                "use_docker": False
            }
        )

        # Create an event loop: this is needed to run asynchronous functions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Define an asynchronous function: this is needed to use await
        if "chat_initiated" not in st.session_state:
            st.session_state.chat_initiated = False  # Initialize the session state

        if not st.session_state.chat_initiated:

            async def initiate_chat():
                await user_proxy.a_initiate_chat(
                    assistant,
                    message=user_input,
                    max_consecutive_auto_reply=5,
                    is_termination_msg=lambda x: x.get("content", "").strip().endswith("TERMINATE"),
                )
                st.stop()  # Stop code execution after termination command

            # Run the asynchronous function within the event loop
            loop.run_until_complete(initiate_chat())

            # Close the event loop
            loop.close()

            st.session_state.chat_initiated = True  # Set the state to True after running the chat


# stop app after termination command
st.stop()