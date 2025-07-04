import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="SFF Validator", layout="wide")
st.title("🧪 SFF File Validator")

uploaded_file = st.file_uploader("Upload your SFF CSV file", type=["csv"])

if uploaded_file:
    try:
        # Safe CSV reading with fallback
        df = pd.read_csv(uploaded_file, encoding='utf-8-sig', on_bad_lines='skip', low_memory=False)
        df.columns = df.columns.str.upper().str.strip()
    except Exception as e:
        st.error(f"❌ Failed to read the file. Please check formatting. Error: {e}")
        st.stop()

    st.subheader("🧩 Select Columns for Consistency Check")
    st.write("📋 Columns in uploaded file:", df.columns.tolist())

    # Dropdowns for selecting relevant columns
    selected_manufacturer = st.selectbox("Select Manufacturer Column", options=df.columns, key="manufacturer")
    remaining_cols_1 = [col for col in df.columns if col != selected_manufacturer]

    selected_brand = st.selectbox("Select Brand Column", options=remaining_cols_1, key="brand")
    remaining_cols_2 = [col for col in remaining_cols_1 if col != selected_brand]

    selected_subbrand = st.selectbox("Select Subbrand Column", options=remaining_cols_2, key="subbrand")

    # Submit button to trigger validation
    if st.button("🚀 Submit and Validate"):
        # Normalize selected columns and ITEM
        for col in [selected_manufacturer, selected_brand, selected_subbrand, 'ITEM']:
            df[col] = df[col].astype(str).str.upper().str.strip()

        # Start timer
        start_time = time.time()

        with st.spinner("⏳ Please wait... Validating your file..."):
            # Filter rows where ITEM is not blank or 'nan'
            df_filtered = df[~df['ITEM'].isin(['', 'NAN'])]

            # Define special values
            special_values = ['ALL OTHER', 'PRIVATE LABEL']

            # Vectorized consistency check
            mask_inconsistent = pd.Series(False, index=df_filtered.index)

            for val in special_values:
                m_mask = df_filtered[selected_manufacturer] == val
                b_mask = df_filtered[selected_brand] == val
                s_mask = df_filtered[selected_subbrand] == val

                m_valid = (df_filtered[selected_manufacturer] == val) | df_filtered[selected_manufacturer].str.endswith(' MASKED')
                b_valid = (df_filtered[selected_brand] == val) | df_filtered[selected_brand].str.endswith(' MASKED')
                s_valid = (df_filtered[selected_subbrand] == val) | df_filtered[selected_subbrand].str.endswith(' MASKED')

                mask_inconsistent |= (m_mask & ~(b_valid & s_valid))
                mask_inconsistent |= (b_mask & ~(m_valid & s_valid))
                mask_inconsistent |= (s_mask & ~(m_valid & b_valid))

            inconsistent_rows = df_filtered[mask_inconsistent]

            # Vectorized bad value check
            bad_values = ['TO BE CHECK', 'TO BE CHECKED', 'BADVALUE', 'TBC']
            df_str = df.astype(str).apply(lambda x: x.str.upper().str.strip())
            bad_value_rows = df[df_str.isin(bad_values).any(axis=1)]

        # End timer
        end_time = time.time()
        elapsed = end_time - start_time

        # Display results
        st.success(f"✅ Validation complete in {elapsed:.2f} seconds.")
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
