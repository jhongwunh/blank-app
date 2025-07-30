import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="CSV Joiner App", layout="wide")
st.title("🔗 CSV Joiner App")

with st.expander("ℹ️ How to Use This App"):
    st.markdown("""
    1. **Upload two CSV files** using the uploaders below.
    2. **Preview the files** to ensure correct data.
    3. **Select join keys** from each file.
    4. **Choose a join type**: `inner`, `left`, or `right`.
    5. **Click 'Join Tables'** to merge the files.
    6. **Download the joined result** using the provided button.
    """)

# Upload first CSV
st.subheader("📄 Upload FIRST CSV File")
file1 = st.file_uploader("Choose the first CSV file", type=["csv"], key="file1")
df1 = None
if file1 is not None:
    df1 = pd.read_csv(file1)
    st.success(f"✅ Loaded {file1.name} with {df1.shape[0]} rows and {df1.shape[1]} columns")
    with st.expander("Preview FIRST CSV"):
        st.dataframe(df1.head())

# Upload second CSV
st.subheader("📄 Upload SECOND CSV File")
file2 = st.file_uploader("Choose the second CSV file", type=["csv"], key="file2")
df2 = None
if file2 is not None:
    df2 = pd.read_csv(file2)
    st.success(f"✅ Loaded {file2.name} with {df2.shape[0]} rows and {df2.shape[1]} columns")
    with st.expander("Preview SECOND CSV"):
        st.dataframe(df2.head())

if df1 is not None and df2 is not None:
    st.subheader("🔧 Join Settings")
    col1, col2, col3 = st.columns(3)
    with col1:
        key1 = st.selectbox("Select join key from FIRST file", df1.columns.tolist())
    with col2:
        key2 = st.selectbox("Select join key from SECOND file", df2.columns.tolist())
    with col3:
        join_type = st.selectbox("Select join type", ['inner', 'left', 'right'])

    if st.button("🚀 Join Tables"):
        df1_key = df1[key1].astype(str).str.strip()
        df2_key = df2[key2].astype(str).str.strip()
        overlap = set(df1_key) & set(df2_key)
        st.info(f"🔍 Number of overlapping keys: {len(overlap)}")

        result = pd.merge(df1, df2, left_on=key1, right_on=key2, how=join_type)
        st.success(f"✅ Join finished! Rows: {result.shape[0]}, Columns: {result.shape[1]}")

        with st.expander("🔎 Preview Joined Result"):
            st.dataframe(result.head(10))

        csv = result.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Joined CSV",
            data=csv,
            file_name='joined_result.csv',
            mime='text/csv',
        )
