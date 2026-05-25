import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

st.set_page_config(page_title="AI Code Reviewer", layout="wide")

st.title("Automated AI Code Reviewer")

prompt_template = """
You are an elite Staff Software Engineer and Security Researcher. Your job is to strip away the fluff, weight, and general commentary from code reviews, leaving only high-density, actionable engineering directives.

De-gravitize the provided source code context using these exact structural rules:

1. **🛑 Critical Vectors:** List any absolute logic bugs, security vulnerabilities, or edge-case crashes. If none exist, output exactly "None detected."
2. **⚡ Frictionless Optimizations:** Provide 2-4 hyper-concise efficiency tweaks (time/space complexity wins). Bold the first 2-4 words of each point as an eye-anchor for immediate scanning.
3. **🛠️ Refactored Reality:** Output the complete, ultra-clean refactored version of the code. Follow strict idiomatic patterns (e.g., PEP8 for Python, clean ES6+ for JS). Do not include chatty introductions. Go straight into the markdown code block.
4. **📝 The Architecture "So What?":** In exactly two sentences, summarize the core behavioral anti-pattern identified in the original code and the structural engineering principle needed to permanently fix it.

IMPORTANT: Your entire response MUST be formatted as normal markdown text. Do NOT output JSON format.

Language Context: {language}
Text to de-gravitize:
```{code_content}```
"""

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Gemini API Key", type="password")
    language = st.selectbox(
        "Language",
        ["Python", "JavaScript", "TypeScript", "Go", "Java", "C++"]
    )

tab1, tab2 = st.tabs(["Paste Code", "Upload File"])

code_content = ""

with tab1:
    pasted_code = st.text_area("Paste your code here", height=300)
    if pasted_code:
        code_content = pasted_code

with tab2:
    uploaded_file = st.file_uploader("Upload code file", type=["py", "js", "ts", "go", "java", "cpp"])
    if uploaded_file is not None:
        code_content = uploaded_file.getvalue().decode("utf-8")
        st.code(code_content, language=language.lower())

if st.button("Review Code", type="primary"):
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif not code_content.strip():
        st.warning("Please provide code to review, either by pasting or uploading a file.")
    else:
        with st.spinner("Analyzing code..."):
            try:
                # Set LangSmith Tracing via Streamlit Secrets
                if "LANGSMITH_API_KEY" in st.secrets:
                    os.environ["LANGSMITH_TRACING"] = st.secrets.get("LANGSMITH_TRACING", "true")
                    os.environ["LANGSMITH_ENDPOINT"] = st.secrets.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
                    os.environ["LANGSMITH_API_KEY"] = st.secrets["LANGSMITH_API_KEY"]
                    os.environ["LANGSMITH_PROJECT"] = st.secrets.get("LANGSMITH_PROJECT", "codereview")

                # Set the API key
                os.environ["GOOGLE_API_KEY"] = api_key
                
                # Initialize LangChain components
                llm = ChatGoogleGenerativeAI(
                    model="gemini-3.1-flash-lite",
                    temperature=0.0
                )
                
                prompt = PromptTemplate(
                    template=prompt_template,
                    input_variables=["language", "code_content"]
                )
                
                # LangChain pipe syntax
                chain = prompt | llm | StrOutputParser()
                
                # Execute
                response = chain.invoke({
                    "language": language,
                    "code_content": code_content
                })
                
                st.subheader("Review Results")
                st.markdown(response)
                
            except Exception as e:
                st.error(f"An error occurred during code review: {str(e)}")
