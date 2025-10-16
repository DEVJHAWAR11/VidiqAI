"""
Quick test to verify all packages are installed correctly
"""

def test_imports():
    """Test if all critical packages can be imported"""
    try:
        import faiss
        print(f"✓ FAISS {faiss.__version__}")
    except ImportError as e:
        print(f"✗ FAISS import failed: {e}")
        return False

    try:
        import langchain
        print(f"✓ LangChain {langchain.__version__}")
    except ImportError as e:
        print(f"✗ LangChain import failed: {e}")
        return False

    try:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        print("✓ LangChain OpenAI integration")
    except ImportError as e:
        print(f"✗ LangChain OpenAI import failed: {e}")
        return False

    try:
        from langchain_community.vectorstores import FAISS
        print("✓ LangChain FAISS integration")
    except ImportError as e:
        print(f"✗ FAISS integration failed: {e}")
        return False

    try:
        import fastapi
        print("✓ FastAPI")
    except ImportError as e:
        print(f"✗ FastAPI import failed: {e}")
        return False

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        print("✓ YouTube Transcript API")
    except ImportError as e:
        print(f"✗ YouTube Transcript API failed: {e}")
        return False

    print("\n🎉 All packages installed successfully!")
    print("Ready to run VidIQAI backend!")
    return True

if __name__ == "__main__":
    test_imports()
