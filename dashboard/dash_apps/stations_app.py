# import os
# import time
# from dash import html, dcc, callback, Output, Input, dash_table, State
# #import dash_ag_grid as dag
# from dash import dash_table
# from django_plotly_dash import DjangoDash
# import dash_bootstrap_components as dbc ----------------------
# from dashboard.utils import get_cached_dashboard_data
# import pandas as pd
# import numpy as np
# import plotly.express as px
# import plotly.graph_objects as go
# from datetime import datetime

# # from dashboard.models import dashboard
# from django.core.cache import cache
# import psycopg2
# from dotenv import load_dotenv
# load_dotenv()

# #for testing
# import redis
# import logging

# #Logging setup
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# LOGO=""

# # Define Offcanvas Component
# offcanvas = html.Div(
#     [
#         dbc.Button(
#             html.I(className="bi bi-layout-text-sidebar"),
#             id="open-offcanvas-scrollable",
#             color="success",
#             className="ms-2",
#             n_clicks=0,
#             size="lg",
#         ),
#         dbc.Offcanvas(
#             dbc.Nav(
#                 [
#                     dbc.NavLink("Home", href="/", active="exact"),
#                     dbc.NavLink("Station", href="/station/", active="exact"),
#                     dbc.NavLink("User", href="#", active="exact"),
#                     dbc.NavLink("Summary", href="#", active="exact"),
#                 ],
#                 vertical=True,
#                 pills=True,
#             ),
#             id="offcanvas-scrollable",
#             scrollable=True,
#             title="Menu",
#             is_open=False,
#         ),
#     ]
# )

# # Define Navbar
# navbar = dbc.Navbar(
#     dbc.Container(
#         [
#             html.A(
#                 dbc.Row(
#                     [
#                         dbc.Col(dbc.NavbarBrand("Ticket Booking Dashboard", className="ms-2")), #NRC-LITS Dashboard
#                     ],
#                     align="center",
#                     className="g-0",
#                 ),
#                 href="/",
#                 style={"textDecoration": "none"},
#             ),
#             dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
#             dbc.Collapse(
#                 dbc.Row(offcanvas, align="center", className="g-0"),
#                 id="navbar-collapse",
#                 is_open=False,
#                 navbar=True,
#             ),
#         ]
#     ),
#     color="success",
#     dark=True,
# )

# footer = dbc.Container(
#     dbc.Row(
#         dbc.Col(
#             html.Small("Copyright © 2025 Ticket Booking System",
#                        className="text-center text-white"),
#             width=12
#         )
#     ),
#     fluid=True,
#     className="bg-success py-3 mt-auto"
# )


# #Initialize the Dash app
# station_app = DjangoDash('Station', external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
#                  external_scripts=['https://cdnjs.cloudflare.com/ajax/libs/plotly.js/3.0.0-rc.2/plotly.min.js'],
#                  add_bootstrap_links=True)

# # Retrieve DataFrame from Cache
# station_data = cache.get('dashboard_data')
# print("Fetching data for station from cache...")
# df = pd.DataFrame(station_data) 
# df["booking_date"] = pd.to_datetime(df["booking_date"]).dt.date


# # dash_table.DataTable(sales_table_df.to_dict('records'), 
# #                                 #[{"name": i, "id": i} for i in sales_table_df.columns],
# #                                 columns=[
# #                                     {'id': 'booking_date', 'name': 'Date', 'type': 'text'},
# #                                     {'id': 'tickets_sold', 'name': 'Tickets Sold', 'type': 'numeric'},
# #                                     {'id':'online_transaction', 'name':'Online Transaction', 'type':'numeric'},
# #                                     {'id':'tom_transaction', 'name':'Tom Transaction', 'type':'numeric'},
# #                                     {'id':'total_no_of_transaction', 'name':'Total Transaction', 'type':'numeric'},
# #                                     {'id':'online_sales', 'name':'Online Sales', 'type':'numeric'},
# #                                     {'id':'tom_sales', 'name':'Tom Sales', 'type':'numeric'},
# #                                     {'id':'total_sales', 'name':'Total Sales', 'type':'numeric'},
# #                                 ],
# #                                 id='group-table',
# #                                 style_table={'overflowX': 'auto',
# #                                             #  'overflowY':'scroll',
# #                                             # 'width':'80%',
# #                                             # 'margin':'auto',
# #                                             'height': '600px',
# #                                             'overflowY': 'scroll',
# #                                 },
# #                                 # fixed_columns={'headers': True, 'data': 1},
# #                                 style_header={
# #                                     'backgroundColor': 'rgb(230, 230, 230)',
# #                                     'color':'dark',
# #                                     'fontWeight': 'bold',
# #                                     'textAlign': 'center',
# #                                 },
# #                                 style_cell={
# #                                     'padding': '10px',
# #                                     'border':'1px solid #ddd',
# #                                     #'textAlign': 'center',
# #                                     'fontFamily':'Arial, sans-serif',
# #                                     'minWidth':'150px', 'width':'150px', 'maxWidth':'150px',
# #                                     'minHeight':'10px', 'height':'10px', 'maxHeight':'10px',
# #                                 },
# #                                 # style_cell_conditional=[
# #                                 #     {'if': {'column_id': 'booking_from'},
# #                                 #      'textAlign': 'left',
# #                                 #      'min-width':'250px', 'width':'250px', 'max-width':'250px'}
# #                                 # ],
# #                                 style_data={
# #                                     'whiteSpace': 'normal',
# #                                     # 'height': 'auto',
# #                                     #'border': '1px solid black'
# #                                 },
# #                                 filter_action='native',
# #                                 sort_action='native',
# #                                 page_size=10,
# # )

# # class_table = dash_table.DataTable(class_table_df.to_dict('records'), 
# #                                 #[{"name": i, "id": i} for i in class_table_df.columns],
# #                                 columns=[
# #                                     {'id': 'booking_from', 'name': 'Station Name', 'type': 'text'},
# #                                     {'id':'first_class', 'name':'First Class', 'type':'text'}, 
# #                                     {'id':'business_class', 'name':'Business Class', 'type':'text'},
# #                                     {'id':'standard_class', 'name':'Standard Class', 'type':'text'},
# #                                 ],
# #                                 id='group-table',
# #                                 style_table={'overflowX': 'auto',
# #                                             #  'overflowY':'scroll',
# #                                             # 'width':'80%',
# #                                             # 'margin':'auto',
# #                                             'height': '300px',
# #                                             'overflowY': 'auto',
# #                                 },
# #                                 # fixed_columns={'headers': True, 'data': 1},
# #                                 style_header={
# #                                     'backgroundColor': 'rgb(230, 230, 230)',
# #                                     'color':'dark',
# #                                     'fontWeight': 'bold',
# #                                     'textAlign': 'center',
# #                                 },
# #                                 style_cell={
# #                                     'padding': '10px',
# #                                     'border':'1px solid #ddd',
# #                                     #'textAlign': 'center',
# #                                     'fontFamily':'Arial, sans-serif',
# #                                     'minWidth':'150px', 'width':'150px', 'maxWidth':'150px',
# #                                     'minHeight':'10px', 'height':'10px', 'maxHeight':'10px',
# #                                 },
# #                                 style_cell_conditional=[
# #                                     {'if': {'column_id': 'booking_from'},
# #                                      'textAlign': 'left',
# #                                      'min-width':'250px', 'width':'250px', 'max-width':'250px'}
# #                                 ],
# #                                 style_data={
# #                                     'whiteSpace': 'normal',
# #                                     # 'height': 'auto',
# #                                     #'border': '1px solid black'
# #                                 },
# #                                 filter_action='native',
# #                                 sort_action='native',
# #                                 page_size=10,
# # )

# # Define the layout
# station_app.layout = dbc.Container([
#     navbar,
#     # Top Navigation Header 
#     dbc.Row([
#         # Logo Column
#         # dbc.Col(
#         #     html.Img(src="/assets/logo.png", height="40px"),  # Adjust height as needed
#         #     width="auto", className="p-3"
#         # ),
#         dbc.Col(dcc.Checklist(options=[{"label": " Today", "value": "today"}], value='today', id="date-filter"), 
#                 width=1, xs=2, sm=2, md=2, lg=1, xl=1, xxl=1, className="p-3 mt-2"),  #, className="mb-2"
#         dbc.Col(dcc.DatePickerRange(
#             id='date-picker',
#             start_date=df['booking_date'].min(),
#             end_date=df['booking_date'].max(),
#             display_format='DD/MM/YYYY'
#         ), width=4, xs=12, sm=12, md=3, lg=4, className="p-3 rounded"),  #, className="p-2"
#     ]),
#     dbc.Row([
#         dbc.Col(dcc.Dropdown(
#             id="boarding-station",
#             options=[
#                 {"label": "Ebute Metta", "value": "Mobolaji Johnson Station Ebute Metta"},
#                 {"label": "Agege", "value": "Babatunde Raji Fashola Station Agege"},
#                 {"label": "Agbado", "value": "Lateef Kayode Jakande Station Agbado"},
#                 {"label": "Kajola", "value": "Professor Yemi Oshinbajo Station Kajola"},
#                 {"label": "Papalanto", "value": "Olu Funmilayo Ransome Kuti Papalanto"},
#                 {"label": "Abeokuta", "value": "Professor Wole Soyinka Station Abeokuta"},
#                 {"label": "Olodo", "value": "Aremo Olusegun Osoba Olodo"},
#                 {"label": "Omi-Adio", "value": "Ladoke Akintola Station Omi-Adio"},
#                 {"label": "Moniya", "value": "Obafemi Awolowo Station Moniya"},
#             ],
#             value=None,
#             placeholder="Boarding Station",
#             className="rounded"
#         ), xs=12, sm=12, md=2, className="p-3"), #give width
#         dbc.Col(dcc.Dropdown(
#             id="route-name",
#             options=[
#                 {"label": "First Class", "value": "First Class"},
#                 {"label": "Business Class", "value": "Business Class"},
#                 {"label": "Standard Class", "value": "Standard Class"},
#             ],
#             value=None,
#             placeholder="Route Name", 
#             className="rounded"
#         ), xs=6, sm=6, md=2, className="p-3"), #give width
#         dbc.Col(dcc.Dropdown(
#             id="coach-type",
#             options=[
#                 {"label": "First Class", "value": "First Class"},
#                 {"label": "Business Class", "value": "Business Class"},
#                 {"label": "Standard Class", "value": "Standard Class"},
#             ],
#             value=None,
#             placeholder="Coach Type", 
#             className="rounded"
#         ), xs=6, sm=6, md=2, className="p-3"),
#         dbc.Col(dcc.Input(id="user-name", type="text", placeholder="User Name", className="form-control rounded border p-1.5"), 
#                  xs=6, sm=6, md=2, className="p-3"),
#         dbc.Col(dcc.Input(id="pnr-number", type="text", placeholder="PNR Number", className="form-control rounded border p-1.5"), 
#                 xs=6, sm=6, md=2, className="p-3"),
#         dbc.Col(dbc.Button("Clear", id="clear-filters", color="success", className="w-100"), 
#                 xs=12, sm=12, md=1, className="p-3"),
#     ], className="bg-white shadow rounded"),

#     #Data Visualization
#     dbc.Row([
#         dbc.Col([
#             html.Div([
#                 html.H4("Group Booking", className="bg-success text-white text-center rounded m-0"),
#                 dash_table.DataTable(
#                     # [{"name": i, "id": i} for i in grid_df.columns],
#                     id='group-table',
#                     columns=[
#                         {'id': 'poc_corporation_name', 'name': 'Corporate Name', 'type': 'text'},
#                         {'id':'total_fare', 'name':'Total Sales', 'type':'numeric'}, #, 'format': {'specifier': ',.0f'}
#                         {'id':'medical', 'name':'Medical', 'type':'numeric'},
#                         {'id':'insurance', 'name':'Insurance', 'type':'numeric'},
#                         {'id':'stamp_duty', 'name':'Stamp Duty', 'type':'numeric'},
#                         {'id':'nrc_tkt_rev', 'name':'NRC Ticket Revenue', 'type':'numeric'},
#                         {'id':'gsd_tkt_rev', 'name':'GSD Ticket Revenue', 'type':'numeric'},
#                         {'id':'icrc_tkt_rev', 'name':'ICRC Ticket Revenue', 'type':'numeric'},
#                         {'id':'no_of_passengers', 'name':'No of Passengers', 'type':'numeric'},
#                     ],
#                     style_table={'overflowX': 'auto',
#                                 #  'overflowY':'scroll',
#                                 # 'width':'80%',
#                                 # 'margin':'auto',
#                                 'height': '300px',
#                                 'overflowY': 'auto',
#                     },
#                     # fixed_columns={'headers': True, 'data': 1},
#                     style_header={
#                         'backgroundColor': 'rgb(230, 230, 230)',
#                         'color':'dark',
#                         'fontWeight': 'bold',
#                         'textAlign': 'center',
#                     },
#                     style_cell={
#                         'padding': '10px',
#                         'border':'1px solid #ddd',
#                         #'textAlign': 'center',
#                         'fontFamily':'Arial, sans-serif',
#                         'minWidth':'150px', 'width':'150px', 'maxWidth':'150px',
#                         'minHeight':'10px', 'height':'10px', 'maxHeight':'10px',
#                     },
#                     style_cell_conditional=[
#                         {'if': {'column_id': 'poc_corporation_name'},
#                             'textAlign': 'left',
#                             'min-width':'250px', 'width':'250px', 'max-width':'250px'}
#                     ],
#                     style_data={
#                         'whiteSpace': 'normal',
#                         # 'height': 'auto',
#                         #'border': '1px solid black'
#                     },
#                     filter_action='native',
#                     sort_action='native',
#                     page_size=10,
#                 ),
#             ], className="bg-white shadow rounded mt-4 mb-4 border")  #width=4, xs=12, sm=12, md=6, lg=12
#         ],xs=12, lg=6),
#         dbc.Col([
#             html.Div([
#                 html.H4("Ticket Count By Class", className="bg-success text-white text-center rounded m-0"),
#                 dash_table.DataTable(
#                     #[{"name": i, "id": i} for i in class_table_df.columns],
#                     columns=[
#                         {'id': 'booking_from', 'name': 'Station Name', 'type': 'text'},
#                         {'id':'first_class', 'name':'First Class', 'type':'text'}, 
#                         {'id':'business_class', 'name':'Business Class', 'type':'text'},
#                         {'id':'standard_class', 'name':'Standard Class', 'type':'text'},
#                     ],
#                     id='class-table',
#                     style_table={'overflowX': 'auto',
#                                 #  'overflowY':'scroll',
#                                 # 'width':'80%',
#                                 # 'margin':'auto',
#                                 'height': '300px',
#                                 'overflowY': 'auto',
#                     },
#                     # fixed_columns={'headers': True, 'data': 1},
#                     style_header={
#                         'backgroundColor': 'rgb(230, 230, 230)',
#                         'color':'dark',
#                         'fontWeight': 'bold',
#                         'textAlign': 'center',
#                     },
#                     style_cell={
#                         'padding': '10px',
#                         'border':'1px solid #ddd',
#                         #'textAlign': 'center',
#                         'fontFamily':'Arial, sans-serif',
#                         'minWidth':'150px', 'width':'150px', 'maxWidth':'150px',
#                         'minHeight':'10px', 'height':'10px', 'maxHeight':'10px',
#                     },
#                     style_cell_conditional=[
#                         {'if': {'column_id': 'booking_from'},
#                             'textAlign': 'left',
#                             'min-width':'250px', 'width':'250px', 'max-width':'250px'}
#                     ],
#                     style_data={
#                         'whiteSpace': 'normal',
#                         # 'height': 'auto',
#                         #'border': '1px solid black'
#                     },
#                     filter_action='native',
#                     sort_action='native',
#                     page_size=10,
#                 ),
#             ], className="bg-white shadow rounded mt-4 mb-4 border") #width=4,xs=12, sm=12, md=5, lg=12
#         ], xs=12, lg=6),
#     ]),
#     dbc.Row([
#         dbc.Col(html.H4("Sales Table", className="bg-success text-white text-center rounded m-0"), width=12)
#     ], className="mt-4"),

#     dbc.Row([
#         dbc.Col(dash_table.DataTable(
#             #[{"name": i, "id": i} for i in sales_table_df.columns],
#             columns=[
#                 {'id': 'booking_date', 'name': 'Date', 'type': 'text'},
#                 {'id': 'tickets_sold', 'name': 'Tickets Sold', 'type': 'numeric'},
#                 {'id':'online_transaction', 'name':'Online Transaction', 'type':'numeric'},
#                 {'id':'tom_transaction', 'name':'Tom Transaction', 'type':'numeric'},
#                 {'id':'total_no_of_transaction', 'name':'Total Transaction', 'type':'numeric'},
#                 {'id':'online_sales', 'name':'Online Sales', 'type':'numeric'},
#                 {'id':'tom_sales', 'name':'Tom Sales', 'type':'numeric'},
#                 {'id':'total_sales', 'name':'Total Sales', 'type':'numeric'},
#             ],
#             id='sales-table',
#             style_table={'overflowX': 'auto',
#                         #  'overflowY':'scroll',
#                         # 'width':'80%',
#                         # 'margin':'auto',
#                         'height': '600px',
#                         'overflowY': 'scroll',
#             },
#             # fixed_columns={'headers': True, 'data': 1},
#             style_header={
#                 'backgroundColor': 'rgb(230, 230, 230)',
#                 'color':'dark',
#                 'fontWeight': 'bold',
#                 'textAlign': 'center',
#             },
#             style_cell={
#                 'padding': '10px',
#                 'border':'1px solid #ddd',
#                 #'textAlign': 'center',
#                 'fontFamily':'Arial, sans-serif',
#                 'minWidth':'150px', 'width':'150px', 'maxWidth':'150px',
#                 'minHeight':'10px', 'height':'10px', 'maxHeight':'10px',
#             },
#             # style_cell_conditional=[
#             #     {'if': {'column_id': 'booking_from'},
#             #      'textAlign': 'left',
#             #      'min-width':'250px', 'width':'250px', 'max-width':'250px'}
#             # ],
#             style_data={
#                 'whiteSpace': 'normal',
#                 # 'height': 'auto',
#                 #'border': '1px solid black'
#             },
#             filter_action='native',
#             sort_action='native',
#             page_size=10,
#         ), width=12, className="shadow rounded border mb-5"),
#     ]),
#     footer,
#     dcc.Interval(id="interval-update", interval=60000, n_intervals=0),
#     dcc.Location(id="url", refresh=False),
# ], fluid=True, className="bg-white")

# # add callback for toggling the collapse on small screens
# @station_app.callback(
#     Output("navbar-collapse", "is_open"),
#     [Input("navbar-toggler", "n_clicks")],
#     [State("navbar-collapse", "is_open")],
# )
# def toggle_navbar_collapse(n, is_open):
#     if n:
#         return not is_open
#     return is_open

# # Callback for Offcanvas Toggle
# @station_app.callback(
#     Output("offcanvas-scrollable", "is_open"),
#     Input("open-offcanvas-scrollable", "n_clicks"),
#     State("offcanvas-scrollable", "is_open"),
# )
# def toggle_offcanvas_scrollable(n1, is_open):
#     if n1:
#         return not is_open
#     return is_open

# #Callback to autorefesh the data
# # @station_app.callback(
# #     Output("dummy-output", "children"),
# #     Input("interval-update", "n_intervals"),
# # )
# # def refresh_data(n_intervals):
# #     global df
# #     try:
# #         logger.debug("Refreshing data from get_data().")
# #         df = get_data()
# #         logger.debug("Data refersh successful.")
# #     except Exception as e:
# #         logger.error(f"Error in refresh_data(): {e}", exc_info=True)
# #         return ""

# #Callbacks to make the dashboard interactive
# @station_app.callback(
#     #Outputs
#     Output("group-table", "data"),
#     Output("class-table", "data"),
#     Output("sales-table", "data"),
#     #Inputs
#     Input("date-filter", "value"),
#     Input("date-picker", "start_date"),
#     Input("date-picker", "end_date"),
#     Input("boarding-station", "value"),
#     Input("route-name", "value"),
#     Input("coach-type", "value"),
#     Input("user-name", "value"),
#     Input("pnr-number", "value"),
#     #Input("clear-filters", "n_clicks"),
# )

# def update_station(date_filter,start_date, end_date, station, route, coach, username, pnr):
#     global df
#     dff = df.copy()

#     print(date_filter)
#     print(type(date_filter))
#     print(f"Start Date:{start_date} (Type: {type(start_date)})")
#     print(f"End Date:{end_date} (Type: {type(end_date)})")
#     print(f"Station name: {station} (Type: {type(station)})")
#     print(f"Coach type: {coach} (Type: {type(coach)})")
#     #print(type(username))
#     print(f"PNR Number: {pnr} (Type: {type(pnr)})")
#     print(f"\n===== DEBUG: DataFrame being filtered =====")

#     # Convert start_date and end_date to native date
#     start_date = pd.to_datetime(start_date).date()
#     end_date = pd.to_datetime(end_date).date()
#     print(f"Start Date after filtering:{start_date} (Type: {type(start_date)})")
#     print(f"End Date after filtering:{end_date} (Type: {type(end_date)})")

#     # Convert 'booking_date' to native date
#     dff["booking_date"] = pd.to_datetime(dff["booking_date"]).dt.date

#     if "today" in date_filter:
#         today_date = datetime.today().date()
#         print(today_date)
#         dff = dff[dff["booking_date"] == today_date]
#     else:
#         # Filter the dataframe
#         dff = dff[(dff["booking_date"] >= start_date) & (dff["booking_date"] <= end_date)]

#     print(f"[INFO] DataFrame now has {len(dff)} records after date filtering.")

#     #Filter by boarding station
#     if station:
#         dff = dff[dff["booking_from"] == station]
#     print(type(station))
#     print(f"[INFO] Filtered by Station: {station}. Remaining records: {len(dff)}")

#     #filter by coach type
#     if coach:
#         dff = dff[dff["coach_type_name"] == coach]
#     print(type(coach))
#     print(f"[INFO] Filtered by Coach Type: {coach}. Remaining records: {len(dff)}")

#     #filter by pnr input
#     if pnr:
#         dff = dff[dff["pnr_number"] == pnr]
#     print(type(pnr))
#     print(f"[INFO] Filtered by PNR: {pnr}. Remaining records: {len(dff)}")

#     # Debugging final dataset before visualization
#     print(f"\n===== DEBUG: Final Filtered DataFrame =====")
#     print(dff)  # Show first few rows of the final DataFrame
#     print(f"[INFO] Final DataFrame contains {len(dff)} rows.")


#     group_table_dff = dff.groupby(['poc_corporation_name']).agg({
#           'total_fare': 'sum',
#           'medical': 'sum',
#           'insurance': 'sum',
#           'stamp_duty': 'sum',
#           'nrc_tkt_rev': 'sum',
#           'gsd_tkt_rev': 'sum',
#           'icrc_tkt_rev': 'sum',
#           'no_of_passengers': 'sum',
#     }).reset_index()

#     updated_group_table = group_table_dff.to_dict('records')
    
#     class_table_dff = dff.groupby('booking_from').agg(
#     first_class=('coach_type_name', lambda x: (x == 'First Class').sum()),
#     business_class=('coach_type_name', lambda x: (x == 'Business Class').sum()),
#     standard_class=('coach_type_name', lambda x: (x == 'Standard Class').sum())
#     ).reset_index()

#     updated_class_table = class_table_dff.to_dict('records')

#     sales_table_dff = dff.groupby('booking_date').agg(
#     tickets_sold = ('no_of_passengers', 'count'),
#     online_transaction = ('total_fare', lambda x: (dff.loc[x.index, 'type'] == 'ONLINE').sum()),
#     tom_transaction = ('total_fare', lambda x: (dff.loc[x.index, 'type'] == 'OFFLINE').sum()),
#     total_no_of_transaction = ('total_fare', 'count'),
#     online_sales = ('total_fare', lambda x: dff.loc[x.index[dff.loc[x.index, 'type'] == 'ONLINE'], 'total_fare'].sum()),
#     tom_sales = ('total_fare', lambda x: dff.loc[x.index[dff.loc[x.index, 'type'] == 'OFFLINE'], 'total_fare'].sum()),
#     total_sales = ('total_fare', 'sum')
#     ).reset_index()


#     updated_sales_table = sales_table_dff.to_dict('records')

#     return updated_group_table, updated_class_table, updated_sales_table