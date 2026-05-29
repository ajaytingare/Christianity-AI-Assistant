import streamlit as st
import requests
import json
from datetime import datetime
import time

API_BASE_URL = "http://localhost:8000"



if "generated_images" not in st.session_state:
    st.session_state.generated_images = []

if "conversation_id" not in st.session_state:

    response = requests.post(
        f"{API_BASE_URL}/conversation/create"
    )

    st.session_state.conversation_id = (
        response.json()["conversation_id"]
    )
    print("="*20)
    print("CREATED CONV ID:", st.session_state.conversation_id)
    print("="*20)



st.set_page_config(
    page_title="Christianity AI Assistant",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #1f4788;
        font-size: 3em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2em;
        margin-bottom: 30px;
    }
    .answer-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f4788;
        margin: 20px 0;
    }
    .citation-box {
        background-color: #e8f0f8;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        font-size: 0.9em;
    }
    .grounded-badge {
        display: inline-block;
        background-color: #4CAF50;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        margin: 5px 5px 5px 0;
        font-size: 0.8em;
    }
    .not-grounded-badge {
        display: inline-block;
        background-color: #FF9800;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        margin: 5px 5px 5px 0;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">✝️ Christianity AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Grounded, Hallucination-Proof Bible & Theology Q&A</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("📚 Document Management")
    
    tab1, tab2 = st.tabs(["Upload", "Manage"])
    
    with tab1:
        uploaded_file = st.file_uploader(
            "Upload Document (PDF, TXT, DOCX)",
            type=["pdf", "txt", "docx"],
            help="Upload Christian texts, Bible passages, or theological documents"
        )
        
        if uploaded_file is not None:
            if st.button("📤 Upload Document", use_container_width=True):
                with st.spinner("Processing document..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                        response = requests.post(f"{API_BASE_URL}/upload", files=files, timeout=1000)
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ Document uploaded! ({data['total_chunks']} chunks)")
                            st.rerun()
                        else:
                            st.error(f"❌ Upload failed: {response.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with tab2:
        if st.button("🔄 Refresh Documents", use_container_width=True):
            st.rerun()
        
        try:
            response = requests.get(f"{API_BASE_URL}/documents", timeout=10)
            if response.status_code == 200:
                docs = response.json()["documents"]
                
                if docs:
                    st.subheader(f"📄 Loaded Documents ({len(docs)})")
                    for doc in docs:
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"📋 **{doc['filename'][:30]}**")
                            st.caption(f"{doc['total_chunks']} chunks • {doc['file_type'].upper()}")
                        with col2:
                            if st.button("🗑️", key=f"del_{doc['file_id']}", help="Delete"):
                                try:
                                    del_response = requests.delete(
                                        f"{API_BASE_URL}/documents/{doc['file_id']}",
                                        timeout=10
                                    )
                                    if del_response.status_code == 200:
                                        st.success("Deleted!")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                else:
                    st.info("No documents uploaded yet. Upload one to get started!")
        except Exception as e:
            st.error(f"Error loading documents: {str(e)}")
    
    st.divider()
    st.subheader("⚙️ Settings")
    
    top_k = st.slider("Retrieval Results", 3, 20, 5, help="Number of relevant chunks to retrieve")
    similarity_threshold = st.slider("Similarity Threshold", 0.0, 1.0, 0.3, 0.05)
    use_citations = st.checkbox("Use Citations", value=True)

st.divider()

tab_ask, tab_image = st.tabs(["❓ Ask Question", "🎨 Generate Image"])

with tab_ask:
    st.subheader("Ask about Christianity, Bible, and Theology")
    
    question = st.text_area(
        "Your question:",
        placeholder="e.g., 'What is the Trinity?' or 'Explain the Gospel'",
        height=100
    )
    
    col1, col2 = st.columns(2)
    with col1:
        ask_button = st.button("🔍 Ask Question", use_container_width=True)
    with col2:
        clear_button = st.button("🧹 Clear", use_container_width=True)
    
    if clear_button:
        st.rerun()
    
    if ask_button and question:
        if not question.strip():
            st.warning("Please enter a question")
        else:
            with st.spinner("🤔 Thinking..."):
                try:
                    payload = {
                        "question": question,
                        "top_k": top_k,
                        "similarity_threshold": similarity_threshold,
                        "use_citation": use_citations,
                        "conversation_id": st.session_state.conversation_id
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/ask",
                        json=payload,
                        timeout=None
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        st.markdown('<div class="answer-box">', unsafe_allow_html=True)
                        st.write("**Answer:**")
                        st.write(data["answer"])
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if data["is_grounded"]:
                                st.markdown('<span class="grounded-badge">✅ Grounded</span>', unsafe_allow_html=True)
                            else:
                                st.markdown('<span class="not-grounded-badge">⚠️ Low Confidence</span>', unsafe_allow_html=True)
                        with col2:
                            st.metric("Confidence", f"{data['confidence_score']:.1%}")
                        with col3:
                            st.metric("Response Time", f"{data['processing_time_ms']:.0f}ms")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        if data["retrieved_chunks"]:
                            st.subheader("📌 Retrieved Sources")
                            for i, chunk in enumerate(data["retrieved_chunks"], 1):
                                with st.expander(f"Source {i}: {chunk['source_file']} ({chunk['relevance_score']:.1%} match)"):
                                    st.write(chunk["content"][:500] + "..." if len(chunk["content"]) > 500 else chunk["content"])
                        
                        if data["citations"]:
                            st.subheader("📚 Citations")
                            for citation in data["citations"]:
                                st.markdown(f"- {citation}")
                    else:
                        error_msg = response.json().get("detail", "Unknown error")
                        st.error(f"❌ Error: {error_msg}")
                except requests.exceptions.Timeout:
                    st.error("❌ Request timeout. Please try again.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

with tab_image:
    
    st.subheader("Generate Christian-Themed Images")
    
    col1, col2 = st.columns(2)
    with col1:
        style = st.selectbox(
            "Art Style",
            ["realistic", "artistic", "symbolic", "abstract"],
            help="Choose the artistic style for the image"
        )
    with col2:
        size = st.selectbox(
            "Image Size",
            ["512x512", "1024x1024", "1536x1536"],
            help="Higher resolution = slower generation"
        )
    
    prompt = st.text_area(
        "Image Description:",
        placeholder="e.g., 'Jesus preaching on the mountain with a peaceful landscape' (min. 10 characters)",
        height=80
    )
    
    if st.button("🎨 Generate Image"):
        if len(prompt) < 10:
            st.warning("Please provide a description of at least 10 characters")
        else:
            progress = st.progress(0)

            with st.spinner("🎨 Generating Christian artwork..."):
                try:
                    payload = {
                        "prompt": prompt,
                        "style": style,
                        "size": size
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/generate-image",
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()

                        st.session_state.generated_images.append(
                            data["image_url"]
                        )

                        st.code(data["image_url"])

                        time.sleep(5)

                        # st.image(data["image_url"], caption="Generated Image")
                        
                        import requests
                        from PIL import Image
                        from io import BytesIO

                        image_loaded = False

                        for _ in range(3):

                            try:

                                time.sleep(2)

                                img_response = requests.get(
                                    data["image_url"],
                                    timeout=20
                                )

                                if img_response.status_code == 200:

                                    image = Image.open(
                                        BytesIO(img_response.content)
                                    )

                                    st.image(
                                        image,
                                        caption="Generated Christian Image",
                                        use_column_width=True
                                    )

                                    image_loaded = True
                                    break

                            except Exception:
                                pass

                        if not image_loaded:

                            st.warning(
                                "Image still generating. "
                                "Please open full image manually."
                            )
                         
                        #####################     
                        st.markdown(f"[Open Full Image]({data['image_url']})")#
                        st.success(f"✅ Image generated in {data['processing_time_ms']:.0f}ms")
                        st.caption(f"Prompt: {data['prompt_used']}")

                        if st.session_state.generated_images:

                            st.subheader("🕘 Recent Images")

                            cols = st.columns(3)

                            recent_images = reversed(
                                st.session_state.generated_images[-6:]
                            )

                            for idx, img in enumerate(recent_images):

                                with cols[idx % 3]:

                                    st.image(img)

                    else:
                        error_msg = response.json().get("detail", "Unknown error")
                        st.error(f"❌ Generation failed: {error_msg}")
                except requests.exceptions.Timeout:
                    st.error("❌ Request timeout. Try a smaller image size.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

st.divider()

with st.expander("ℹ️ About & Features"):
    st.write("""
    ### Christianity AI Assistant
    
    This application uses advanced AI and RAG (Retrieval Augmented Generation) to provide accurate, grounded answers about Christianity, the Bible, and theology.
    
    **Key Features:**
    - 📚 **RAG System**: Retrieves relevant context from uploaded documents
    - 🛡️ **Hallucination Prevention**: Ensures answers are grounded in sources
    - ✝️ **Scripture-Aware**: Understands Bible references and theology
    - 🎨 **Image Generation**: Creates Christian-themed images
    - 💬 **Conversation Memory**: Maintains context across interactions
    - 🔒 **Safety Moderation**: Filters inappropriate content
    
    **How It Works:**
    1. Upload Christian texts or Bible passages
    2. Ask questions about the content
    3. The AI retrieves relevant sections and generates grounded answers
    4. All responses include source citations and confidence scores
    
    **Safety Guarantees:**
    - No made-up Bible verses
    - No hallucinated scripture references
    - Rejects adversarial prompts
    - Maintains theological accuracy
    """)
