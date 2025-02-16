import os
import redis
import altair as alt
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from streamlit_qrcode_scanner import qrcode_scanner
import qrcode
from PIL import Image
from io import BytesIO
import pyqrcode

# Streamlit Setup
st.title('📊 Product & Supplier Analysis + QR Code Scanner')

# File paths for products CSV and suppliers JSON
products_csv_path = "C:/Users/Debarchan Dash/Downloads/products.csv"
suppliers_json_path = "C:/2025/Databastyper/suppliers.json"

# Check if files exist
if not os.path.exists(products_csv_path):
    st.error(f"Products CSV file not found at: {products_csv_path}")
    st.stop()  
if not os.path.exists(suppliers_json_path):
    st.error(f"Suppliers JSON file not found at: {suppliers_json_path}")
    st.stop()  

# Load the products data (CSV) and suppliers data (JSON)
try:
    products_df = pd.read_csv(products_csv_path)
    suppliers_df = pd.read_json(suppliers_json_path)
    st.success("Files loaded successfully!")
except Exception as e:
    st.error(f"Error loading files: {e}")
    st.stop()  # Stop execution if there is an error loading files

# Merge products_df with suppliers_df to include CompanyName
products_df = products_df.merge(suppliers_df[['SupplierID', 'CompanyName']], on='SupplierID', how='left')

# Check if necessary columns exist
required_columns = ['ProductName', 'UnitsInStock', 'ReorderLevel', 'CompanyName', 'UnitsOnOrder']
missing_cols = [col for col in required_columns if col not in products_df.columns]
if missing_cols:
    st.error(f"Missing required columns: {', '.join(missing_cols)}")
    st.stop()  # Stop execution if required columns are missing

# Data Validation: Convert columns to appropriate types
try:
    products_df['UnitsInStock'] = products_df['UnitsInStock'].astype(float)
    products_df['ReorderLevel'] = products_df['ReorderLevel'].astype(float)
    products_df['UnitsOnOrder'] = products_df['UnitsOnOrder'].astype(float)
    st.success("Data types validated successfully!")
except Exception as e:
    st.error(f"Error during data validation: {e}")
    st.stop()  # Stop execution if data validation fails

# Data Processing for Reorder Trends
reorder_products = products_df[products_df['UnitsInStock'] + products_df['UnitsOnOrder'] <= products_df['ReorderLevel']]
reorder_products_info = reorder_products[['ProductName', 'UnitsInStock', 'UnitsOnOrder', 'ReorderLevel', 'CompanyName']]

#  Display Reorder Products in Streamlit UI 
st.subheader('Reorder Products')
if not reorder_products_info.empty:
    st.write(reorder_products_info)

    # Allow user to download reorder report
    csv_data = reorder_products_info.to_csv(index=False)
    st.download_button(
        label="Download Reorder Report as CSV",
        data=csv_data,
        file_name="reorder_report.csv",
        mime="text/csv"
    )

   # Reorder Products Overview
st.subheader('🔄 Reorder Products Overview')
if not reorder_products_info.empty:
    for index, row in reorder_products_info.iterrows():
        st.write(f"**{row['ProductName']}**")
        st.write(f"Stock Left: {row['UnitsInStock']}")
        st.write(f"Supplier: {row['CompanyName']}")

        # Generate QR code for calling the supplier
        phone_number = row['CompanyName']  # Replace with supplier's actual phone number field if available
        qr_code_data = f"tel:{phone_number}"
        qr = pyqrcode.create(qr_code_data)
        qr_img = qr.png_as_base64_str(scale=5)
        
        # Show QR Code
        st.image(f"data:image/png;base64,{qr_img}", caption=f"Scan to call {row['CompanyName']}")

        # Option to directly call supplier (hyperlink)
        phone_link = f"tel:{phone_number}"
        st.markdown(f"[Call Supplier](tel:{phone_number})")

# Bar Graph: Units In Stock vs Reorder Level for Reorder Products
st.subheader("📊 Units In Stock vs Reorder Level for Reorder Products")
bar_chart_data = reorder_products_info[['ProductName', 'UnitsInStock', 'ReorderLevel']].melt(
    'ProductName', var_name='Type', value_name='Value')

bar_chart = alt.Chart(bar_chart_data).mark_bar().encode(
    x=alt.X('ProductName:N', sort='-y'),
    y='Value:Q',
    color='Type:N',
    tooltip=['ProductName', 'Value']
).properties(
    width=700,
    height=400
)

st.altair_chart(bar_chart)

# Scatter Plot: Units In Stock vs Units On Order for Reorder Products
st.subheader("⚖️ Stock Level vs Units On Order for Reorder Products")
scatter_chart = alt.Chart(reorder_products_info).mark_circle().encode(
    x='UnitsInStock:Q',
    y='UnitsOnOrder:Q',
    color='ReorderLevel:Q',
    size='UnitsInStock:Q',
    tooltip=['ProductName', 'UnitsInStock', 'UnitsOnOrder', 'ReorderLevel']
).properties(
    width=700,
    height=400
)

st.altair_chart(scatter_chart)

# Exploratory Data Analysis (EDA) Section
st.subheader("Exploratory Data Analysis (EDA)")

class DataAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def plot_reorder_trends(self):
        sns.set(style="whitegrid")
        plt.figure(figsize=(12, 6))
        sns.scatterplot(data=self.df, x='ProductName', y='UnitsInStock', hue='ReorderLevel')
        plt.title("Stock Levels vs Reorder Points")
        plt.xticks(rotation=45)
        st.pyplot(plt)

    def supplier_activity(self):
        supplier_counts = self.df['CompanyName'].value_counts()
        plt.figure(figsize=(10, 5))
        sns.barplot(x=supplier_counts.index, y=supplier_counts.values)
        plt.title("Supplier Contribution to Products")
        plt.xticks(rotation=45)
        st.pyplot(plt)

    def stock_level_distribution(self):
        plt.figure(figsize=(10, 6))
        sns.histplot(self.df['UnitsInStock'], bins=30, kde=True)
        plt.title("Distribution of Stock Levels")
        st.pyplot(plt)

    def reorder_vs_stock(self):
        plt.figure(figsize=(12, 6))
        sns.lineplot(data=self.df, x='ProductName', y='ReorderLevel', label='Reorder Level')
        sns.lineplot(data=self.df, x='ProductName', y='UnitsInStock', label='Units In Stock')
        plt.title("Reorder Level vs Stock Level")
        plt.xticks(rotation=45)
        plt.legend()
        st.pyplot(plt)

# Create an instance of DataAnalyzer
analyzer = DataAnalyzer(products_df)

# Display various plots
analyzer.plot_reorder_trends()
analyzer.supplier_activity()
analyzer.stock_level_distribution()
analyzer.reorder_vs_stock()

# MongoDB Connection Setup for Storing Reorder Products
uri = "mongodb+srv://meetu40:f7q0FQQUmrzNuz4O@cluster0.1ez8q.mongodb.net/myDatabase?retryWrites=true&w=majority"

# MongoDB connection setup
try:
    client = MongoClient(uri, server_api=ServerApi('1'), serverSelectionTimeoutMS=50000, connectTimeoutMS=50000)
    client.admin.command('ping')
    st.success("Successfully connected to MongoDB!")
except Exception as e:
    st.error(f"Error connecting to MongoDB: {e}")
    st.stop()  # Stop execution if MongoDB connection fails

# Insert data into MongoDB
if st.button('📤 Insert Data into MongoDB'):
    collection = client['northwind_database']['reorder_products']
    reorder_products_list = reorder_products_info.to_dict(orient="records")
    collection.insert_many(reorder_products_list)
    st.success("Data inserted into MongoDB!")

# Query MongoDB for Reordered Items
if st.button('Query MongoDB for Reordered Items'):
    collection = client['northwind_database']['reorder_products']
    reordered_items = collection.find()
    for item in reordered_items:
        st.write(item)

# Download Reorder Report as CSV
@st.cache_data
def download_reorder_report():
    return reorder_products_info.to_csv(index=False)

st.subheader("Download Reorder Report as CSV")
csv = download_reorder_report()
st.download_button(
    label="Download CSV",
    data=csv,
    file_name="reorder_products_report.csv",
    mime="text/csv"
)
# 🔹 **QR Code Scanner**
st.subheader("📸 QR Code Scanner")

PWD = open(r"C:\2025\Databastyper\app.py", encoding='utf-8').read().strip()  # Use encoding if needed
r = redis.Redis("redis-14904.c56.east-us.azure.redns.redis-cloud.com", 13616, password=PWD, decode_responses=True)

qr_code = qrcode_scanner()

if qr_code:
    p = r.hgetall(str(qr_code))
    df = pd.DataFrame(p.values(), index=p.keys())  # type: ignore
    st.dataframe(df)
    
    # Display the QR Code for the scanned product/order
    display_qr_code(qr_code)  # Show the QR Code visual
