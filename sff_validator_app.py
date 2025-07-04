import streamlit as st
import pandas as pd

st.set_page_config(page_title="SFF Validator", layout="wide")
st.title("🧪 SFF File Validator")

uploaded_file = st.file_uploader("Upload your SFF CSV file", type=["csv"])

if uploaded_file:
    # Read and normalize column names
    df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
    df.columns = df.columns.str.upper().str.strip()

    st.subheader("🧩 Select Columns for Consistency Check")

    # Show available columns for debugging
    # st.write("📋 Columns in uploaded file:", df.columns.tolist())

    # Dropdowns for selecting relevant columns
    selected_manufacturer = st.selectbox("Select Manufacturer Column", options=df.columns, key="manufacturer")
    remaining_cols_1 = [col for col in df.columns if col != selected_manufacturer]

    selected_brand = st.selectbox("Select Brand Column", options=remaining_cols_1, key="brand")
    remaining_cols_2 = [col for col in remaining_cols_1 if col != selected_brand]

    selected_subbrand = st.selectbox("Select Subbrand Column", options=remaining_cols_2, key="subbrand")

    # Normalize selected columns and ITEM
    for col in [selected_manufacturer, selected_brand, selected_subbrand, 'ITEM']:
        df[col] = df[col].astype(str).str.upper().str.strip()

    # Filter rows where ITEM is not blank or 'nan'
    df_filtered = df[~df['ITEM'].isin(['', 'NAN'])]

    # Define consistency check logic
    special_values = ['ALL OTHER', 'PRIVATE LABEL']

    def is_valid(value, expected):
        return value == expected or value.endswith(' MASKED')

    def is_inconsistent(row):
        m = row[selected_manufacturer]
        b = row[selected_brand]
        s = row[selected_subbrand]
        for val in special_values:
            if m == val and not (is_valid(b, val) and is_valid(s, val)):
                return True
            if b == val and not (is_valid(m, val) and is_valid(s, val)):
                return True
            if s == val and not (is_valid(m, val) and is_valid(b, val)):
                return True
        return False

    # Apply consistency check
    inconsistent_rows = df_filtered[df_filtered.apply(is_inconsistent, axis=1)]

    # Bad value check
    bad_values = ['TO BE CHECK', 'TO BE CHECKED', 'BADVALUE', 'TBC']
    bad_value_rows = df[df.apply(lambda row: row.astype(str).str.upper().str.strip().isin(bad_values).any(), axis=1)]

    # Display results
    st.subheader("🔍 Validation Results")
    st.write(f"**Inconsistent Rows (Rule 1):** {len(inconsistent_rows)}")
    st.write(f"**Rows with Bad Values (Rule 2):** {len(bad_value_rows)}")

    # Combined download section
    if not inconsistent_rows.empty or not bad_value_rows.empty:
        st.subheader("📥 Download Validation Results")
        col1, col2 = st.columns(2)

        with col1:
            if not inconsistent_rows.empty:
                inconsistent_csv = inconsistent_rows.to_csv(index=False).encode('utf-8')
                st.download_button("Download Inconsistent Rows", inconsistent_csv, "inconsistent_rows.csv", "text/csv")

        with col2:
            if not bad_value_rows.empty:
                badvalue_csv = bad_value_rows.to_csv(index=False).encode('utf-8')
                st.download_button("Download Bad Value Rows", badvalue_csv, "bad_value_rows.csv", "text/csv")
