import streamlit as st
import pandas as pd
import re
from io import StringIO

# Title
st.title("Sentence Tokenizer")

# Introduction and App Flow
st.markdown("""
This application allows you to upload a CSV file and tokenize sentences from a selected text column. 
You can optionally include a speaker column. The steps are as follows:

1. Upload your CSV file.
2. Select the relevant columns for ID, text (context), and optionally speaker.
3. Click the **Run** button to process the data.
4. Preview the first 10 rows of the result.
5. Download the processed CSV file.
""")

# File upload
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    cols = df.columns.tolist()

    # Column selection
    id_col = st.selectbox('Select ID column:', cols)
    context_col = st.selectbox('Select Text column:', cols)
    speaker_col = st.selectbox('Select Speaker column (optional):', [None] + cols)

    # Tokenizer function
    def tokenize(text):
        text = str(text).strip()
        tags = re.findall(r'#\w+', text)
        clean = re.sub(r'#\w+', '', text)
        parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', clean)
        parts = [p.strip() for p in parts if p.strip()]
        if tags:
            parts.append(' '.join(tags))
        return parts

    if st.button("Run"):
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

        # Show preview
        st.subheader("Preview")
        st.dataframe(result.head(10))

        # Download processed CSV
        csv = result.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name='sentence_tokenized.csv',
            mime='text/csv'
        )
