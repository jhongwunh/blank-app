import streamlit as st
import pandas as pd
from io import StringIO

st.title("🧠 Rolling Context")

# Step 1: Upload CSV
uploaded_file = st.file_uploader("📁 Upload your CSV file:", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File loaded!")
    
    # Preview uploaded data
    st.subheader("🔍 Preview Uploaded Data")
    st.dataframe(df.head(10))

    # Step 2: Column selection
    id_col = st.selectbox("Select **ID** Column:", options=df.columns.tolist())
    text_col = st.selectbox("Select **Text** Column:", options=df.columns.tolist())
    speaker_col = st.selectbox("Select **Speaker** Column (Optional):", options=["(None)"] + df.columns.tolist())

    # Step 3: Window size
    window_size = st.number_input("Set Window Size:", min_value=0, value=3, step=1)

    # Step 4: Generate Context
    if st.button("🚀 Generate Context"):
        st.info("Processing...")

        df_sorted = df.sort_values(by=[id_col]).reset_index(drop=True)
        result_rows = []

        for conv_id in df_sorted[id_col].unique():
            conv_df = df_sorted[df_sorted[id_col] == conv_id].reset_index(drop=True)
            for i in range(len(conv_df)):
                current_row = conv_df.loc[i]
                past_window = conv_df.loc[max(0, i - window_size):i - 1]

                context = " ".join(past_window[text_col].astype(str).tolist())
                entry = {
                    id_col: conv_id,
                    'Statement': current_row[text_col],
                    'Context': context
                }

                if speaker_col != "(None)":
                    entry['Speaker'] = current_row[speaker_col]
                    speaker_history = " | ".join(past_window[speaker_col].astype(str).tolist())
                    entry['Speaker_History'] = speaker_history

                result_rows.append(entry)

        context_df = pd.DataFrame(result_rows)

        st.success("✅ Done! Here's a preview:")
        st.dataframe(context_df.head(10))

        # Step 5: Download CSV
        csv = context_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name='rolling_context_output.csv',
            mime='text/csv'
        )
