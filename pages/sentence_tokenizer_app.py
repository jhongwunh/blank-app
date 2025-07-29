import streamlit as st
import pandas as pd
import re

# Page Config
st.set_page_config(page_title="Sentence Tokenizer", layout="wide")

# Title and Intro
st.title("📝 Sentence Tokenizer")

with st.expander("ℹ️ How to Use This App"):
    st.markdown("""
    This app allows you to upload a CSV file and tokenize sentences from a selected text column. 
    Optionally include a speaker column.

    **Steps:**
    1. Upload your CSV file.
    2. Select the columns for ID, text, and optionally speaker.
    3. Click **Run** to process.
    4. Preview results and download the CSV.
    """)

# Upload CSV
st.subheader("📁 Upload CSV File")
uploaded_file = st.file_uploader("Choose your CSV file", type="csv")

if uploaded_file:
    with st.spinner("Reading CSV file..."):
        df = pd.read_csv(uploaded_file)
        cols = df.columns.tolist()

    st.success("File uploaded successfully!")
    with st.expander("🔍 Preview Uploaded Data"):
        st.dataframe(df.head(), use_container_width=True)

    with st.form("column_selection"):
        st.subheader("⚙️ Select Columns")
        id_col = st.selectbox('Select **ID** column', cols, help="Column uniquely identifying each row")
        context_col = st.selectbox('Select **Text** column', cols, help="Column containing text to tokenize")
        speaker_col = st.selectbox('Select **Speaker** column (optional)', [None] + cols, help="Optional column indicating speaker")
        run_button = st.form_submit_button("🚀 Run Tokenization")

    def tokenize(text):
        text = str(text).strip()
        tags = re.findall(r'#\w+', text)
        clean = re.sub(r'#\w+', '', text)
        parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', clean)
        parts = [p.strip() for p in parts if p.strip()]
        if tags:
            parts.append(' '.join(tags))
        return parts

    if run_button:
        with st.spinner("Tokenizing sentences..."):
            data = []
            for _, row in df.iterrows():
                sentences = tokenize(row[context_col])
                for i, s in enumerate(sentences, 1):
                    entry = {
                        'ID': row[id_col],
                        'Sentence ID': i,
                        'Context': row[context_col],
                        'Statement': s
                    }
                    if speaker_col:
                        entry['Speaker'] = row[speaker_col]
                    data.append(entry)

            result = pd.DataFrame(data)

        st.success("✅ Tokenization complete!")
        st.subheader("🔍 Preview of Results")
        st.dataframe(result.head(10), use_container_width=True)

        csv = result.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Tokenized CSV",
            data=csv,
            file_name='sentence_tokenized.csv',
            mime='text/csv'
        )
else:
    st.info("Please upload a CSV file to get started.")
