import pandas as pd  # pip install pandas openpyxl
import numpy as np  # pip install numpy
import plotly.express as px  # pip install plotly-express
import streamlit as st  # pip install streamlit
from streamlit_option_menu import option_menu
import plotly.figure_factory as ff

import base64
# local imports
import dataprocessor


# setting favicon and browser tab title
st.set_page_config(page_title='Retail Forecast',
                   page_icon=':bar_chart:', layout='centered')

# setting up Page Title
st.markdown('## Retail Forecast')
# --- VARIABLES ---

nav_menu = st.container()
st.session_state["selected_products"] = None
# --- UTILITIES ---

#  To set background image


@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# To set the background image for the app.


def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = '''
    <style>
    .stApp{
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }
    </style>
    ''' % bin_str

    st.markdown(page_bg_img, unsafe_allow_html=True)
    return


#  To read excel file
@st.cache_data
def get_data(filepath) -> pd.DataFrame:
    df = pd.read_excel(filepath)
    return df

# TODO: set the background image without effecting the darkmode
# set_png_as_page_bg('assets/Jan-Business_report_1.jpg')
# set_png_as_page_bg('assets/analytics-svgrepo-com.svg')

# To draw scatter plots for comparison


def draw_scatter_plot(df):
    df = df.copy()
    df['Date'] = pd.to_datetime(df['year'])
    df['Year'] = df['Date'].dt.year
    df['Quarter'] = df['Date'].dt.quarter
    # st.write(df.groupby(['Year', 'Brand', 'Product']).agg(
    #     {'Total Price': 'sum', 'Quantity': 'sum'}))

    # Convert the 'Year' column to datetime and extract year and quarter
    df['Year'] = pd.to_datetime(df['Year'], format='%Y')
    df['Year'] = df['Year'].dt.year

    # Group by Year, Brand, and Product and calculate the sum of Total Price and Quantity
    df_grouped = df.groupby(['Year', 'Brand', 'Product']).agg(
        {'Total Price': 'sum', 'Quantity': 'sum'}).reset_index()

    # Pivot the DataFrame to have 'Year' as columns
    pivot_df = df_grouped.pivot(
        index=['Brand', 'Product'], columns='Year', values='Total Price').reset_index()

    # Melt the pivoted DataFrame to long format
    df_melted = pivot_df.melt(
        id_vars=['Brand', 'Product'], var_name='Year', value_name='Total Price')

    # Plotting the stacked bar chart using Plotly Express
    fig = px.bar(df_melted, x='Year', y='Total Price',
                 color='Brand', barmode='stack')

    # Update the layout
    fig.update_layout(
        title='Total Sales by Brand and Product per Year',
        xaxis_title='Year',
        yaxis_title='Total Price'
    )

    # Display the chart using Streamlit
    st.plotly_chart(fig, use_container_width=True)


# To draw trend line chart for multiple products


def draw_trend_line_chart(df, product_column, date_column, quantity_column):
    fig = px.line(df, x=df.index.year, y=df[quantity_column].rolling(200).mean(), color=product_column,
                  labels={date_column: 'Sale Date',
                          quantity_column: 'Quantity'},
                  title='Quantity Trend by Product')

    fig.update_xaxes(dtick='M1', tickformat='%b-%y')
    st.plotly_chart(fig, use_container_width=True)


# --- SIDE BAR ---
st.sidebar.header("Welcome Team")

uploaded_file = st.sidebar.file_uploader(
    "Choose a File", type='xlsx')


if uploaded_file is None:
    st.write('upload excel file to see the insights')

if uploaded_file:
    # df = get_data(uploaded_file)
    df = dataprocessor.get_raw_dataframe(uploaded_file)

    # -- store the dataframe in session for the future workflow..
    if 'df_excel' not in st.session_state:
        st.session_state['df_excel'] = df

    # --- Navigation Menu ---
    with nav_menu:
        selected = option_menu(
            menu_title=None,
            options=["Key Insights", "More Analytics"],
            icons=["pencil-fill", "bar-chart-fill"],
            orientation="horizontal")
        # -- store the dataframe in session for the future workflow..
        # if st.session_state['current_tab'] is None:
        st.session_state['current_tab'] = selected

        # --- UI under Key insights Tab --- #
        if st.session_state['current_tab'] == "Key Insights":
            st.markdown('### Key Metrics')
        # --- Three widgets: 1. Total sales 2. Unique Prodcuts 3.Best Year of Sales  --- #

        # creating a single-element container
            # create three columns
            kpi1, kpi2, kpi3 = st.columns(3)

            # fill in those three columns with respective KPIs
            # KPI-1: Total sales so far
            total = df['Quantity'].sum()
            kpi1.metric(
                label="Total Sales ⏳",
                value=total,
                delta=300,
            )

            # KPI-2: No.of unique products sold
            products = df['Product'].unique()
            kpi2.metric(
                label="Products 🎳",
                value=products.size,
                delta=-10 + products.size,
            )

            # KPI-3: Best year so far in terms of sales
            grouped_df = df.groupby(df.index.year)['Quantity'].sum()
            kpi3.metric(
                label="Best Year 🎉",
                value=grouped_df.idxmax(),
                delta=49,
            )

            # styling the kpis
            with open("src/styles/style.css")as f:
                st.markdown(f"<style> {f.read()}</style>",
                            unsafe_allow_html=True)

            st.markdown("<hr/>", unsafe_allow_html=True)

            # Selection box with product names, by default shows two products
            st.subheader("Sales Trends of the products")
            if st.session_state["selected_products"] is None:
                options = st.multiselect(
                    label='', options=products, default=products[:2])

                st.session_state["selected_products"] = options

            df = dataprocessor.filter_by_product(
                df, st.session_state["selected_products"])

            # creating new feature(Year) on dataframe
            # st.write(pd.to_datetime(df.index, format="%Y"))
            df['year'] = pd.to_datetime(df.index, format="%Y")

            # create two tabs for charts

            tab1, tab2 = st.tabs(
                ["Sales volume by Price", "Sales by Products"])
            st.session_state["insights_df"] = df

            # --- Tab 1. Scatter plot to show the distribution
            with tab1:
                # TODO: this has to draw scatter plot of different product sales in every year
                # st.write(st.session_state["insights_df"])
                if st.session_state["insights_df"] is None:
                    draw_scatter_plot(df)
                else:
                    draw_scatter_plot(
                        st.session_state["insights_df"])

            # --- Tab 2. Trend line to show the YoY growth
            with tab2:
                # TODO: this has to be rolling mean of each selected product with different color on same plot
                if st.session_state["insights_df"] is None:
                    draw_trend_line_chart(
                        df, 'Product', 'Sale Date', 'Quantity')
                else:
                    draw_trend_line_chart(
                        st.session_state["insights_df"], 'Product', 'Sale Date', 'Quantity')

            # ----2. Fast selling products

            st.subheader('Fast selling products')

        # --- UI under Analytics Tab --- #
        elif st.session_state['current_tab'] == "More Analytics":
            st.markdown('### analytics')
        #  --- Filters with options --- #


# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
# st.markdown(hide_st_style, unsafe_allow_html=True)
