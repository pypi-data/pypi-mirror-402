import streamlit as st
import ollama
import sys
import os

# Allow running directly from the package directory
if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from reasoning_visualizer import visualizer

st.set_page_config(page_title="Phi4 Mini Reasoning", layout="wide", page_icon="🧠")

# Custom CSS for a cleaner look
st.markdown("""
<style>
    .stApp {
        background-color: #f8fafc;
    }
    h1 {
        font-family: 'Inter', sans-serif;
        color: #0f172a;
    }
    .stChatInput {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

st.title("Phi4 Mini Visualizer 🧠")
st.caption("Experience the reasoning process of Phi4 Mini with a modern, clear interface.")

# Helper to render streaming content efficiently without re-mounting iframes
def get_streaming_html(text):
    import re
    
    # Define supported tag pairs. Order matters.
    tag_pairs = [
        (r'<think>', r'</\s*think\s*>'),
        (r'\[THOUGHT\]', r'\[/THOUGHT\]'),
        (r'<reasoning>', r'</\s*reasoning\s*>'),
        (r'<chain_of_thought>', r'</\s*chain_of_thought\s*>')
    ]

    thought_text = ""
    answer_text = ""
    is_thinking = False

    # 1. Try to find a matching start tag
    for start_pattern, end_pattern in tag_pairs:
        start_match = re.search(start_pattern, text, re.IGNORECASE)
        if start_match:
            # Found start tag
             # text after start tag
            post_start = text[start_match.end():]
            
            end_match = re.search(end_pattern, post_start, re.IGNORECASE)
            if end_match:
                # Full thought block found
                thought_text = post_start[:end_match.start()].strip()
                answer_text = post_start[end_match.end():].strip()
            else:
                # Still thinking
                thought_text = post_start.strip()
                is_thinking = True
                answer_text = ""
            break
    
    # 2. Fallback if no tags found
    if not thought_text and not is_thinking:
        answer_text = text

    # We use a single line or unindented string to prevent Markdown from treating it as code
    html = f"""<div style="font-family: 'Inter', 'Segoe UI', Roboto, sans-serif; color: #1f2937; display: flex; flex-direction: column; gap: 1rem;">
    {'<div style="border: 1px solid #e5e7eb; border-radius: 0.75rem; overflow: hidden; background-color: #f9fafb; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);">' if thought_text else ''}
        {'<div style="display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 1rem; background-color: #f3f4f6; border-bottom: 1px solid #e5e7eb;">' if thought_text else ''}
            {'<div style="display: flex; align-items: center; gap: 0.5rem;">' if thought_text else ''}
                {'<div style="padding: 4px; background-color: #dbeafe; border-radius: 6px; display: flex; align-items: center; justify-content: center;">🧠</div>' if thought_text else ''}
                {'<span style="fontWeight: 600; fontSize: 0.9rem; color: #374151;">Reasoning Process</span>' if thought_text else ''}
                {f'<span style="font-size: 0.75rem; padding: 2px 8px; border-radius: 99px; background-color: #eff6ff; color: #3b82f6; border: 1px solid #bfdbfe; margin-left: 0.5rem;">Thinking...</span>' if is_thinking else ''}
            {'</div>' if thought_text else ''}
        {'</div>' if thought_text else ''}
        {'<div style="padding: 1rem; font-size: 0.9rem; line-height: 1.6; color: #4b5563; background-color: #ffffff; font-family: \'JetBrains Mono\', monospace; white-space: pre-wrap;">' + thought_text + '</div>' if thought_text else ''}
    {'</div>' if thought_text else ''}
    {'<div style="font-size: 1rem; line-height: 1.6; color: #111827; white-space: pre-wrap; margin-top: 1rem;">' + answer_text + '</div>' if answer_text else ''}
</div>"""
    return html

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history (Standard Streamlit Chat UI)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # If it's an assistant message, use our custom visualizer
        if message["role"] == "assistant":
            visualizer(text=message["content"])
        else:
            st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask a logic puzzle..."):
    # 1. Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate Assistant Response
    with st.chat_message("assistant"):
        # We need a placeholder to update the custom component dynamically
        placeholder = st.empty()
        full_response = ""

        try:
            # Stream from local Ollama instance
            messages_payload = [
                {'role': 'system', 'content': 'You are a helpful assistant. Please wrap your detailed step-by-step thinking process in <think> tags, and put your final answer after the closing </think> tag.'},
                {'role': 'user', 'content': prompt}
            ]
            
            stream = ollama.chat(
                model='olmo-3:7b-think',  # Ensure you run `ollama pull deepseek-r1`
                messages=messages_payload,
                stream=True
            )
            
            import time
            last_update_time = time.time()
            
            # Accumulate and update component
            for chunk in stream:
                content = chunk['message']['content']
                full_response += content
                
                # Update the custom component inside the placeholder
                # Batch updates to improve performance (max 10 updates per second)
                # USE NATIVE HTML for smoothing streaming to avoid iframe reloading key issues
                current_time = time.time()
                if current_time - last_update_time > 0.1:
                    placeholder.markdown(get_streaming_html(full_response), unsafe_allow_html=True)
                    last_update_time = current_time

            # Final update to ensure catch-up - SWITCH TO REACT COMPONENT
            # This allows the final state to be interactive (collapsible)
            with placeholder.container():
                visualizer(text=full_response, key=f"final_{len(full_response)}")
            
            # 3. Save final response to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Rerender to solidify the key (remove the 'streaming' key)
            st.rerun()

        except Exception as e:
            st.error(f"Error connecting to Ollama: {e}")
            st.info("Make sure Ollama is running: `ollama serve`")