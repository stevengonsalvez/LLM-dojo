"""
This is a demo of AutoGen chat agents. You can use it to chat with OpenAI's GPT-3 and GPT-4 models. They are able to execute commands, answer questions, and even write code.
An example a question you can ask is: 'How is the S&P 500 doing today? Summarize the news for me.'
UserProxyAgent is used to send messages to the AssistantAgent. The AssistantAgent is used to send messages to the UserProxyAgent.

"""


from autogen_playwright.prompts.prompts import WEB_TESTER_PROMPT
import streamlit as st
import asyncio
from autogen import AssistantAgent, UserProxyAgent, get_config_list
import os
from pathlib import Path
import autogen.runtime_logging
import logging
from autogen_playwright.ops.log_analyzer import LogAnalyzer

logger = logging.getLogger(__name__)

# setup page title and description
st.set_page_config(page_title="AutoGen Chat app", page_icon="🤖", layout="wide")

# Setup AutoGen Runtime Logging with SQLite
db_path = Path("runtime_logs/autogen_logs.db")
db_path.parent.mkdir(exist_ok=True)
logging_config = {
    "dbname": str(db_path),
    "table_name": "agent_logs",
    "create_table": True
}
logging_session_id = autogen.runtime_logging.start(config=logging_config)
logger.info(f"Started autogen runtime logging with session ID: {logging_session_id}")

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
with st.expander("How to use the Testing Agent", expanded=False):
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
    st.header("LLM Configuration")
    llm_provider = st.selectbox("Provider", ["OpenAI", "Anthropic", "Cerebras"], index=0)
    
    if llm_provider == "OpenAI":
        selected_model = st.selectbox("Model", ["gpt-3.5-turbo", "gpt-4-1106-preview", "gpt-4o"], index=1)
        st.markdown("Press enter to save key")
        st.markdown(
            "For more information about the models, see [here](https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo)."
        )
        selected_key = st.text_input("OpenAI API Key", type="password")
        # Set environment variable for OpenAI
        os.environ["OPENAI_API_KEY"] = selected_key
    elif llm_provider == "Anthropic":
        selected_model = st.selectbox("Model", ["claude-3-opus-20240229", "claude-3-sonnet-20240229"], index=0)
        st.markdown("Press enter to save key")
        st.markdown(
            "For more information about Claude models, see [here](https://docs.anthropic.com/claude/docs/models-overview)."
        )
        selected_key = st.text_input("Anthropic API Key", type="password")
        # Set environment variable for Anthropic
        os.environ["ANTHROPIC_API_KEY"] = selected_key
    else:  # Cerebras
        selected_model = st.selectbox("Model", ["llama3.3-70b", "llama3.1-70b"], index=0)
        st.markdown("Press enter to save key")
        st.markdown(
            "For more information about Cerebras models, see [here](https://www.cerebras.net/blog/cerebras-llama-70b)."
        )
        selected_key = st.text_input("Cerebras API Key", type="password")
        # Set environment variable for Cerebras
        os.environ["CEREBRAS_API_KEY"] = selected_key

# setup main area: user input and chat messages
chat_container = st.container()
with chat_container:
    # Create tabs for Chat and Report
    chat_tab, report_tab = st.tabs(["Chat", "Test Report"])
    
    with report_tab:
        # Add run selector and load button
        reports_dir = Path("reports")
        if reports_dir.exists():
            run_dirs = sorted(list(reports_dir.glob("run_*")), reverse=True)
            if run_dirs:
                run_options = [d.name for d in run_dirs]
                col1, col2 = st.columns([2, 1])
                with col1:
                    selected_run = st.selectbox(
                        "Select Test Run",
                        run_options,
                        index=0,
                        format_func=lambda x: f"Run {x.split('_')[1]}"
                    )
                with col2:
                    load_report = st.button("🔄 Load Report", type="primary", use_container_width=True)
                
                if load_report:
                    selected_dir = reports_dir / selected_run
                    # Load and display the report
                    report_file = selected_dir / "report.md"
                    if report_file.exists():
                        st.markdown("## Test Execution Report")
                        with report_file.open() as f:
                            report_content = f.read()
                            st.markdown(report_content)
                    
                    # Display screenshots from the run directory
                    screenshots = list(selected_dir.glob("*.png"))
                    if screenshots:
                        st.markdown("## Test Screenshots")
                        # Sort screenshots by creation time
                        screenshots.sort(key=lambda x: x.stat().st_mtime)
                        # Create columns for screenshots
                        cols = st.columns(2)
                        for idx, screenshot in enumerate(screenshots):
                            with cols[idx % 2]:
                                st.image(
                                    str(screenshot),
                                    caption=f"Step: {screenshot.stem}",
                                    use_column_width=True
                                )
                    else:
                        st.info("No screenshots found in this test run")
            else:
                st.warning("No test reports found")
        else:
            st.warning("Reports directory not found")
    
    with chat_tab:
        # Create a container for the chat history with a fixed height
        chat_history = st.container()
        
        # Add a horizontal line to separate chat and input
        st.markdown("---")
        
        # Create the input area at the bottom
        user_input = st.text_area("Your message", height=100, key="user_input")
        
        # Split input either by commas or newlines
        if "," in user_input:
            steps = [step.strip() for step in user_input.split(",")]
        else:
            steps = [step.strip() for step in user_input.splitlines() if step.strip()]
        
        steps_formatted = "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))
        

        
        # Add a submit button
        if st.button("Send", type="primary"):
            if not user_input:  # Skip if user input is empty
                st.stop()
            
            if not selected_key or not selected_model:
                st.warning("You must provide valid API key and choose preferred model", icon="⚠️")
                st.stop()
            
            # setup request timeout and config list
            if llm_provider == "OpenAI":
                config = {
                    "model": selected_model,
                    "api_key": selected_key,
                    "timeout": 600,
                    "max_tokens": 2000,
                    "api_type": "openai"
                }
            elif llm_provider == "Anthropic":
                config = {
                    "model": selected_model,
                    "api_key": selected_key,
                    "timeout": 600,
                    "max_tokens": 2000,
                    "api_type": "anthropic"
                }
            else:  # Cerebras
                config = {
                    "model": selected_model,
                    "api_key": selected_key,
                    "timeout": 600,
                    "max_tokens": 2000,
                    "api_type": "cerebras"
                }
            
            llm_config = {
                "config_list": [config],
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
                is_termination_msg=lambda x: x.get("content", "").strip().endswith("TERMINATE") or any(phrase in x.get("content", "") for phrase in ["Test Summary", "If you have any further questions", "The execution succeeded"]),
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
                        message=steps_formatted,
                        max_consecutive_auto_reply=2,
                        max_turns=3,
                        is_termination_msg=lambda x: x.get("content", "").strip().endswith("TERMINATE") or any(phrase in x.get("content", "") for phrase in ["Test Summary", "The execution succeeded"]),
                    )
                    
                    # Get and display token usage statistics using LogAnalyzer
                    log_analyzer = LogAnalyzer(str(db_path))
                    stats = log_analyzer.get_session_stats(logging_session_id)
                    
                    if stats:
                        st.sidebar.markdown("---")
                        st.sidebar.header("Token Usage Stats")
                        st.sidebar.markdown(f"💰 Total Cost: ${stats['total_cost']}")
                        st.sidebar.markdown(f"🔤 Total Tokens: {stats['total_tokens']}")
                        st.sidebar.markdown(f"📤 Prompt Tokens: {stats['prompt_tokens']}")
                        st.sidebar.markdown(f"📥 Completion Tokens: {stats['completion_tokens']}")
                        st.sidebar.markdown(f"📊 Average Tokens/Request: {stats['average_tokens_per_request']}")
                        st.sidebar.markdown(f"📝 Total Requests: {stats['request_count']}")
                    
                    # Get conversation flow to extract the test report
                    conversation = log_analyzer.get_conversation_flow(logging_session_id)
                    if not conversation.empty:
                        # Find messages containing Test Summary or execution success
                        report_messages = conversation[
                            conversation['response_content'].str.contains(
                                'Test Summary|The execution succeeded|test scenario completed', 
                                case=False, 
                                na=False
                            )
                        ]
                        
                        if not report_messages.empty:
                            with report_tab:
                                st.markdown("## Test Execution Report")
                                # Get the last report message
                                report_content = report_messages.iloc[-1]['response_content']
                                
                                # Format the report content
                                if "```" in report_content:
                                    # If there's a code block, preserve it
                                    st.markdown(report_content)
                                else:
                                    # Otherwise, format with markdown
                                    st.markdown(f"""
                                    {report_content}
                                    """)
                                
                                # Display screenshots if they exist
                                screenshots_dir = Path("screenshots")
                                if screenshots_dir.exists():
                                    st.markdown("## Test Screenshots")
                                    screenshots = list(screenshots_dir.glob("*.png"))
                                    if screenshots:
                                        # Sort screenshots by creation time
                                        screenshots.sort(key=lambda x: x.stat().st_mtime)
                                        for screenshot in screenshots:
                                            st.image(
                                                str(screenshot), 
                                                caption=f"Step: {screenshot.stem}", 
                                                use_column_width=True
                                            )
                                    else:
                                        st.info("No screenshots were captured during this test run")
                    
                    st.stop()  # Stop code execution after termination command

                # Run the asynchronous function within the event loop
                loop.run_until_complete(initiate_chat())

                # Close the event loop
                loop.close()

                st.session_state.chat_initiated = True  # Set the state to True after running the chat

# stop app after termination command
st.stop()