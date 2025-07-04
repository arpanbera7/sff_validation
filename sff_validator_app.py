import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="SFF Validator", layout="wide")
st.title("🧪 SFF File Validator")

uploaded_file = st.file_uploader("Upload your SFF CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Normalize relevant columns
    for col in ['MANUFACTURER', 'BRAND', 'SUBBRAND', 'ITEM']:
        df[col] = df[col].astype(str).str.upper().str.strip()

    # Filter rows where ITEM is not blank or 'nan'
    df_filtered = df[~df['ITEM'].isin(['', 'NAN'])]

    # Define consistency check logic
    special_values = ['ALL OTHER', 'PRIVATE LABEL']

    def is_valid(value, expected):
        return value == expected or value.endswith(' MASKED')

    def is_inconsistent(row):
        m, b, s = row['MANUFACTURER'], row['BRAND'], row['SUBBRAND']
        for val in special_values:
            if m == val and not (is_valid(b, val) and is_valid(s, val)):
                return True
            if b == val and not (is_valid(m, val) and is_valid(s, val)):
                return True
            if s == val and not (is_valid(m, val) and is_valid(b, val)):
                return True
        return False

    inconsistent_rows = df_filtered[df_filtered.apply(is_inconsistent, axis=1)]

    # Bad value check
    bad_values = ['TO BE CHECK', 'TO BE CHECKED', 'BADVALUE', 'TBC']
    bad_value_rows = df[df.apply(lambda row: row.astype(str).str.upper().str.strip().isin(bad_values).any(), axis=1)]

    # Display results
    st.subheader("🔍 Validation Results")
    st.write(f"**Inconsistent Rows (Rule 1):** {len(inconsistent_rows)}")
    st.write(f"**Rows with Bad Values (Rule 2):** {len(bad_value_rows)}")

    # Download buttons
    if not inconsistent_rows.empty:
        inconsistent_csv = inconsistent_rows.to_csv(index=False).encode('utf-8')
        st.download_button("Download Inconsistent Rows", inconsistent_csv, "inconsistent_rows.csv", "text/csv")

    if not bad_value_rows.empty:
        badvalue_csv = bad_value_rows.to_csv(index=False).encode('utf-8')
        st.download_button("Download Bad Value Rows", badvalue_csv, "bad_value_rows.csv", "text/csv")
