import streamlit as st
import pandas as pd
from io import StringIO

st.title("CSV Joiner App")

st.markdown("Upload two CSV files and choose the join parameters.")

# Upload first CSV
file1 = st.file_uploader("Upload FIRST CSV file", type=["csv"], key="file1")
df1 = None
if file1 is not None:
    df1 = pd.read_csv(file1)
    st.success(f"Loaded {file1.name} ({df1.shape[0]} rows, {df1.shape[1]} columns)")
    st.dataframe(df1.head())

# Upload second CSV
file2 = st.file_uploader("Upload SECOND CSV file", type=["csv"], key="file2")
df2 = None
if file2 is not None:
    df2 = pd.read_csv(file2)
    st.success(f"Loaded {file2.name} ({df2.shape[0]} rows, {df2.shape[1]} columns)")
    st.dataframe(df2.head())

if df1 is not None and df2 is not None:
    key1 = st.selectbox("Select join key from FIRST file", df1.columns.tolist())
    key2 = st.selectbox("Select join key from SECOND file", df2.columns.tolist())
    join_type = st.selectbox("Select join type", ['inner', 'left', 'right'])

    if st.button("Join Tables"):
        df1_key = df1[key1].astype(str).str.strip()
        df2_key = df2[key2].astype(str).str.strip()
        overlap = set(df1_key) & set(df2_key)
        st.write(f"Number of overlapping keys: {len(overlap)}")

        result = pd.merge(df1, df2, left_on=key1, right_on=key2, how=join_type)
        st.success(f"Join finished! Rows: {result.shape[0]}, Columns: {result.shape[1]}")
        st.dataframe(result.head(10))

        csv = result.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Joined CSV",
            data=csv,
            file_name='joined_result.csv',
            mime='text/csv',
        )
