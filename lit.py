import streamlit as st
import pandas as pd
import requests

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
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Main Dashboard", "🕵️‍♂️ Messy Book Auditor", "💱 Live Currency Converter", "📱 M-Pesa Engine" ])
        
        # ==========================================
        # TAB 1: THE SUMMARY DASHBOARD
        # ==========================================
        with tab1:
            if 'Amount' in df.columns:
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
                if 'Date' in df.columns:
                    # Group by date to handle multiple transactions on the same day
                    daily_totals = df.groupby('Date')['Amount'].sum()
                    st.line_chart(daily_totals)
            else:
                st.info("It looks like you've uploaded an M-Pesa statement head over to the M-Pesa Engine tab")
            
        # ==========================================
        # TAB 2: THE FORENSIC AUDITOR
        # ==========================================
        with tab2:
            if 'Amount' in df.columns and 'Category' in df.columns:
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
                st.warning("The Auditor requires a standard file with 'Amount' and 'Category' columns. This file format is not supported for editing")

            st.divider()

        #================================================================
        # Tab 3 Architecture Live currency converter.
        #================================================================
        with tab3:
            st.header("💱 Live Currency Converter")
            st.write("Pulling real-time exchange rates directly from the global market.")
            
            #create two columns for a calculator
            col1, col2 = st.columns(2)
            with col1:
                #the user inputs the amount and the base currency
                amount = st.number_input("Amount to Convert", min_value=0.0, value=100.00, step=10.0)
                base_currency = st.selectbox("From Currency", ["USD", "EUR", "KES", "GBP"])
            with col2:
                #user selects the currency they want to convert into
                # we default to index three which is KES in the listbelow
                target_currency = st.selectbox("To Currency", ["USD", "EUR", "GBP", "KES"], index=3)    
            #API call only happens when the user clicks the button
            if st.button("Convert Now"):
                try:
                    #the API call, injects the base currency into the url dynamic   
                    url = f"https://open.er-api.com/v6/latest/{base_currency}" 
                    response = requests.get(url)

                    #parse the JSON data
                    data = response.json()
                    
                    #extract the rate and do the math
                    if data["result"] == "success":
                        rate = data["rates"][target_currency]
                        converted_amount = amount * rate
                        st.divider()
                        st.success(f"Live Market Rates: {base_currency} = {rate} {target_currency}")
                        st.metric(
                        label=f"Converted Total ({target_currency})",
                        value=f"{converted_amount:,.2f}"
                        )
                    else:
                        st.error(f"Could not connect to fetch live data")
                except Exception as e:
                    st.error(f"Could not connect to the internet. Error{e}") 
        
        
        # ==========================================
        # TAB 4: M-PESA CASHBOOK ENGINE
        # ==========================================
        with tab4:
            if 'Details' in df.columns:
                st.header("📱 M-Pesa Cashbook Engine")
                st.write("Automatically categorizes M-Pesa statements and standardizes the ledger.")
            
                # 1. THE CATEGORIZER (Scanning for Keywords)
                # We write a mini Python function that reads a single line of text and assigns a category
                def categorize_transaction(text):
                    text = str(text).upper() # Make everything uppercase so it's easier to match
                    if "CUSTOMER PAYMENT" in text:
                        return "Income (Revenue)"
                    elif "MERCHANT PAYMENT" in text or "BUY GOODS" in text:
                        return "Supplier Expense"
                    elif "PAY UTILITY" in text:
                        return "Overhead (Utilities)"
                    elif "TRANSFER" in text or "WITHDRAWAL" in text:
                        return "Bank Transfer (Contra)"
                    else:
                        return "Uncategorized"

                # We use .apply() to force every single row in the 'Details' column through our mini-function
                # We'll use a copy of the dataframe to avoid messing up the other tabs
        
                mpesa_df = df.copy()
                mpesa_df['Category'] = mpesa_df['Details'].apply(categorize_transaction)
                
                # 2. THE STANDARDIZATION ENGINE
                # M-Pesa leaves empty cells (NaN) if no money went in or out. 
                # .fillna(0) turns those empty cells into $0.00 so Python can do math on them.
                mpesa_df['Paid In'] = pd.to_numeric(mpesa_df['Paid In'], errors='coerce').fillna(0)
                mpesa_df['Withdrawn'] = pd.to_numeric(mpesa_df['Withdrawn'], errors='coerce').fillna(0)
                mpesa_df['Standard_Amount'] = mpesa_df['Paid In'] - mpesa_df['Withdrawn']
                
                # 3. THE HIDDEN FEE EXTRACTOR  
                fees_df = mpesa_df[mpesa_df['Transaction Fee'] > 0].copy()
            
                if not fees_df.empty:
                    fees_df['Details'] = "Safaricom M-Pesa Transaction Fee"
                    fees_df['Category'] = "Bank & M-Pesa Charges"

                    fees_df['Standard_Amount'] = -fees_df['Transaction Fee']
                    fees_df['Transaction Fee'] = 0
                    mpesa_df = pd.concat([mpesa_df, fees_df], ignore_index=True)
                    mpesa_df = mpesa_df.sort_values(by='Completion Time')

                # We only show the columns they actually care about for QuickBooks
                clean_view = mpesa_df[['Completion Time', 'Receipt No.', 'Details', 'Category', 'Standard_Amount', 'Transaction Fee']]
                
                st.success("✅ Statement successfully standardized and categorized!")
                
                # Show some quick metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Income Found", f"KES {mpesa_df['Paid In'].sum():,.2f}")
                with col2:
                    st.metric("Total Expenses Found", f"KES {mpesa_df['Withdrawn'].sum():,.2f}")
                
                # Display the beautiful, clean dataframe
                st.dataframe(clean_view, use_container_width=True)
                
                # The golden button: exports CSV for quickbooks
                csv_export = clean_view.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download CSV for QuickBooks",
                    data=csv_export,
                    file_name="standardized_mpesa_statement.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ Please upload a valid M-Pesa statement containing a 'Details' column to use this tool.")
                    
    

    except Exception as e:
        # If the user uploads a broken file, this prevents the server from crashing
        st.error(f"Whoops! Something went wrong reading the file. Ensure it is a valid CSV/Excel file. Error: {e}")

else:
    # This shows when the page first loads, before a file is dropped in
    st.info("Awaiting file upload... Please drag and drop your file to begin.")