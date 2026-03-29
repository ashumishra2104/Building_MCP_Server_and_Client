import streamlit as st
import os
from logic import get_realtime_info, generate_video_script, create_did_video, CSS_THEME

def main():
    st.set_page_config(
        page_title="StoryForge", 
        page_icon= "📚💻✍🏼📓", 
        layout="centered",
        initial_sidebar_state= "collapsed"
    )
    st.markdown(CSS_THEME, unsafe_allow_html=True)
    st.markdown("<h1> 🔥 Story Forge Agent 🌍</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Search any topic - from world news to research trends - and get AI-powered insights & video scripts instantly</p>", unsafe_allow_html=True)

    if "refined_info" not in st.session_state:
        st.session_state.refined_info = None
    if "current_query" not in st.session_state:
        st.session_state.current_query = None
    if "script" not in st.session_state:
        st.session_state.script = None
    if "video_url" not in st.session_state:
        st.session_state.video_url = None

    query = st.text_input("👻 Enter your topic or question 👻 ", placeholder="e.g., The latest advancements in quantum computing")
    
    if st.button("Generate Insight & Script"):
        if query:
            with st.spinner("Searching for real-time information..."):
                st.session_state.refined_info = get_realtime_info(query)
                st.session_state.current_query = query
                st.session_state.script = None
                st.session_state.video_url = None
        else:
            st.warning("Please enter a topic.")

    if st.session_state.refined_info:
        refined_info = st.session_state.refined_info
        current_query = st.session_state.current_query

        st.success("✅ Insights Gathered")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"### 📚 AI-Generated Summary: {current_query}")
        st.write(refined_info)
        st.markdown("</div>", unsafe_allow_html=True)
        
        generate_script = st.radio(
            "🎬 Generate a short video script?",
            ("No", "Yes"),
            index=0 if st.session_state.script is None else 1,
            horizontal=True
        )

        if generate_script == "Yes":
            if st.session_state.script is None:
                with st.spinner("Crafting Video Script..."):
                    st.session_state.script = generate_video_script(current_query, refined_info)
            
            if st.session_state.script:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader("🎥 Video Script")
                st.write(st.session_state.script)
                st.download_button(
                    label="📥 Download Script",
                    data=st.session_state.script,
                    file_name="video_script.txt",
                    mime="text/plain"
                )
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("---")
                generate_video = st.radio(
                    "🎬 Generate an AI video from this script?",
                    ("No", "Yes"),
                    horizontal=True,
                    key="video_radio"
                )
                if generate_video == "Yes":
                    if st.session_state.video_url is None:
                        with st.spinner("Creating AI video via D-ID... this may take ~30s"):
                            url, error = create_did_video(st.session_state.script)
                            if url:
                                st.session_state.video_url = url
                            else:
                                st.error(f"Video generation failed: {error}")
                    if st.session_state.video_url:
                        st.success("✅ Video ready!")
                        st.video(st.session_state.video_url)
            else:
                st.warning("⚠️ Could not generate script.")
    elif st.session_state.current_query and not st.session_state.refined_info:
        st.warning("Could not gather insights for this topic.")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption("Made with 💖")

if __name__ == "__main__":
    main()
