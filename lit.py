import streamlit as st
import pandas as pd

# --- PAGE SETUP ---
st.set_page_config(page_title="QuickBooks Auditor UI", page_icon="📊", layout="wide")

st.title("Finance Dashboard and Auditor")
st.write("Upload a CSV/Excel file to instantly audit and visualize the data.")

# --- THE UPLOADER ---
uploaded_file = st.file_uploader("Drag and drop your CSV/Excel file here", type=["csv", "xlsx"])

# --- CORE LOGIC ---
if uploaded_file is not None:
    try:
        # Check the name of the file to see how it ends
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            # Use the Excel reader if it's an .xlsx file
            df = pd.read_excel(uploaded_file, engine='openpyxl')

        # --- THE TABS ARCHITECTURE ---
        # This creates the two clickable tabs at the top of the page
        tab1, tab2 = st.tabs(["📊 Main Dashboard", "🕵️‍♂️ Messy Book Auditor"])
        
        # ==========================================
        # TAB 1: THE SUMMARY DASHBOARD
        # ==========================================
        with tab1:
            st.subheader("📈 Key Performance Indicators")
            
            # 1. Calculate the core financial numbers
            total_income = df[df['Amount'] > 0]['Amount'].sum()
            total_expense = df[df['Amount'] < 0]['Amount'].sum()
            net_balance = total_income + total_expense
            
            # 2. Display them in 3 side-by-side columns
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Total Income", value=f"${total_income:,.2f}")
            with col2:
                st.metric(label="Total Expenses", value=f"${total_expense:,.2f}")
            with col3:
                st.metric(label="Net Balance", value=f"${net_balance:,.2f}")
                
            st.divider() # A clean horizontal line
            
            # 3. Time Series Visualization
            st.subheader("📉 Cash Flow Over Time")
            # Group by date to handle multiple transactions on the same day
            daily_totals = df.groupby('Date')['Amount'].sum()
            st.line_chart(daily_totals)
            
        # ==========================================
        # TAB 2: THE FORENSIC AUDITOR
        # ==========================================
        with tab2:
            st.header("Automated Data Audit")
            st.write("Automatically flagging anomalies.")
            
            # --- Audit Tool 1: High-Risk Transactions ---
            st.subheader("🚨 High-Risk Transactions (>$5k)")
            
            # The Pandas logic: Find anything with an absolute value over 5000
            high_risk_df = df[df['Amount'].abs() > 5000]
            
            if high_risk_df.empty:
                st.success("✅ No high-risk transactions found.")
            else:
                st.warning(f"⚠️ Found {len(high_risk_df)} transactions requiring manual review.")
                st.dataframe(high_risk_df, use_container_width=True)
                
            st.divider()
            
            # --- Audit Tool 2: Missing Categories ---
            st.subheader("❓ Uncategorized Data")
            
            # The Pandas logic: Find rows where Category is 'NaN' OR explicitly 'Uncategorized'
            missing_cat_df = df[df['Category'].isna() | (df['Category'] == 'Uncategorized')]
            
            if missing_cat_df.empty:
                st.success("✅ All transactions are perfectly categorized!")
            else:
                st.error(f"❌ Found {len(missing_cat_df)} transactions missing a category classification.")
                st.dataframe(missing_cat_df, use_container_width=True)

            st.divider()
            
            # --- Audit Tool 3: The Duplicate Detective (PREMIUM) ---
            st.subheader("👯 Duplicate Charge Detective")
            st.write("Scans for identical charges on the same day to catch double-billing errors.")
            
            # The Pandas logic: Look for rows with the exact same Date, Description, and Amount.
            # keep=False ensures we see BOTH the original and the duplicate!
            duplicates_df = df[df.duplicated(subset=['Date', 'Description', 'Amount'], keep=False)]
            
            if duplicates_df.empty:
                st.success("✅ No duplicate charges detected!")
            else:
                st.warning(f"⚠️ Found {len(duplicates_df)} potential duplicate transactions. Please verify.")
                # We sort the values by Date and Amount so the duplicates sit right next to each other in the table
                st.dataframe(duplicates_df.sort_values(by=['Date', 'Amount']), use_container_width=True)

            st.divider()
            
            # --- Audit Tool 4: Subscription Price Creep (PREMIUM) ---
            st.subheader("📈 Subscription Price Creep Tracker")
            st.write("Identifies recurring vendors that have quietly increased their prices over time.")
            
            # 1. Isolate expenses and make the numbers positive so the math is easier to read
            expenses = df[df['Amount'] < 0].copy()
            expenses['Amount_Pos'] = expenses['Amount'].abs()
            
            # 2. Sort chronologically so we know the 'first' and 'last' are accurate
            expenses = expenses.sort_values(by='Date')
            
            # 3. The Magic: Group by Vendor and Aggregate the data
            vendor_stats = expenses.groupby('Description').agg(
                Charge_Count=('Amount_Pos', 'count'), # How many times did they charge us?
                First_Charge=('Amount_Pos', 'first'), # What was the oldest charge?
                Last_Charge=('Amount_Pos', 'last')    # What was the newest charge?
            ).reset_index()
            
            # 4. Filter for RECURRING vendors (let's say, charged us at least 3 times)
            recurring_vendors = vendor_stats[vendor_stats['Charge_Count'] >= 3]
            
            # 5. Catch the Creep: Where the Last Charge is strictly greater than the First Charge
            price_creep = recurring_vendors[recurring_vendors['Last_Charge'] > recurring_vendors['First_Charge']].copy()
            
            if price_creep.empty:
                st.success("✅ No sneaky price increases detected!")
            else:
                # Calculate exactly how much the price went up
                price_creep['Price_Increase'] = price_creep['Last_Charge'] - price_creep['First_Charge']
                
                st.warning(f"🚨 Found {len(price_creep)} vendors that have increased their prices!")
                
                # Sort it so the biggest price offenders are at the top!
                st.dataframe(
                    price_creep.sort_values(by='Price_Increase', ascending=False), 
                    use_container_width=True
                )

            st.divider()
            
            # --- Audit Tool 5: Smart Categorizer (PREMIUM) ---
            st.subheader("🧠 AI Smart Categorizer")
            st.write("Analyzes past client history to suggest categories for missing data.")
            
            # 1. Isolate the rows that actually HAVE categories to learn from
            known_data = df[df['Category'].notna() & (df['Category'] != 'Uncategorized')]
            
            # 2. Learn the habits: For each vendor, what is the most common category?
            # .mode()[0] grabs the most frequent item
            if not known_data.empty:
                vendor_habits = known_data.groupby('Description')['Category'].apply(lambda x: x.mode()[0]).to_dict()
                
                # 3. Grab the rows that are MISSING categories (from Tool 2)
                missing_cat_df = df[df['Category'].isna() | (df['Category'] == 'Uncategorized')].copy()
                
                if missing_cat_df.empty:
                    st.success("✅ No missing categories to predict!")
                else:
                    # 4. The Prediction: Map the habits to the missing rows
                    missing_cat_df['Suggested_Category'] = missing_cat_df['Description'].map(vendor_habits)
                    
                    # 5. Filter out ones where we literally have no idea (no past data)
                    smart_guesses = missing_cat_df[missing_cat_df['Suggested_Category'].notna()]
                    
                    if smart_guesses.empty:
                        st.info("Not enough historical data to make smart guesses yet.")
                    else:
                        st.success(f"💡 Generated {len(smart_guesses)} smart category suggestions!")
                        # Display just the columns the consultant cares about
                        st.dataframe(
                            smart_guesses[['Date', 'Description', 'Amount', 'Suggested_Category']], 
                            use_container_width=True
                        )
            else:
                st.info("Need more categorized data to learn client habits.")

    except Exception as e:
        # If the user uploads a broken file, this prevents the server from crashing
        st.error(f"Whoops! Something went wrong reading the file. Ensure it is a valid CSV/Excel file. Error: {e}")

else:
    # This shows when the page first loads, before a file is dropped in
    st.info("Awaiting file upload... Please drag and drop your file to begin.")