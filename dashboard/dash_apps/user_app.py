import os
import dash
from dash import html, dcc, callback, Output, Input, dash_table, State
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
from dashboard.utils import get_cached_dashboard_data, get_user_data, get_booking_data
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# from dashboard.models import dashboard
from django.core.cache import cache
import psycopg2
from dotenv import load_dotenv
load_dotenv()

#for testing
import redis
import logging

#Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# # Offcanvas component
# offcanvas = dbc.Offcanvas(
#     [
#         html.P("Ticket Booking Dashboard"),
#         dbc.Nav(
#             [
#                 dbc.NavLink("Home", href="/", active="exact"),
#                 dbc.NavLink("Station", href="/station", active="exact"),
#                 dbc.NavLink("User", href="/user", active="exact"),
#                 dbc.NavLink("Summary", href="/summary", active="exact"),
#             ],
#             vertical=True,
#             pills=True,
#         ),
#     ],
#     id="offcanvas",
#     title="Menu",
#     is_open=False,
#     placement="start",
#     scrollable=True,
# )

# # Navbar with optional Collapse wrapping the toggle button
# # Navbar with no spacing on the left
# navbar = dbc.Navbar(
#     dbc.Container(
#         [
#             dbc.Row(
#                 [
#                     dbc.Col(
#                         dbc.Button(
#                             "☰",
#                             id="open-offcanvas",
#                             n_clicks=0,
#                             color="light",
#                             className="p-0 m-0 bg-success border-0 text-white",  # no margin or border
#                         ),
#                         width="auto",
#                         className="p-0 m-0",  # remove space from column
#                     ),
#                     dbc.Col(
#                         html.A(
#                             dbc.NavbarBrand("Ticket Booking Dashboard", className="ms-2"),
#                             href="/",
#                             style={"textDecoration": "none"},
#                         ),
#                         width="auto",
#                     ),
#                     dbc.Col(
#                         html.A(
#                             dbc.NavbarBrand("Logout", className="ms-2"),
#                             href="/logout",
#                         ),
#                         width="auto",
#                         className="ms-auto"
#                     ),
#                 ],
#                 align="center",
#                 className="g-0 w-100",
#             ),
#         ],
#         fluid=True,  # removes container's side spacing
#         #className="p-0",  # just in case
#     ),
#     color="success",
#     dark=True,
#     #className="p-0",  # navbar padding reset
# )


# #Copyright © 2025 Ticket Booking System
# footer = dbc.Container(
#     dbc.Row([
#         dbc.Col(
#             html.Small("Copyright © 2025 Ticket Booking System",
#                        className="text-center bs-dark"),
#             width=11
#         ),
#         dbc.Col(
#             html.Img(src="/assets/GSDS_Logo.jpg", height="30px"),  # Adjust height as needed
#             width="auto", className="p-0 me-2",
#         )
#     ], justify="end"),
#     fluid=True,
#     className="bg-white py-3 mt-auto shadow"
# )

end_date = datetime.today().date()


# Define the app
#Initialize the Dash app
user_app = DjangoDash('User', external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
                 external_scripts=['https://cdnjs.cloudflare.com/ajax/libs/plotly.js/3.0.0-rc.2/plotly.min.js'],
                 add_bootstrap_links=True)

#dash.register_page(__name__, path="/user")

# Define the layout
user_app.layout = html.Div([
            # navbar,
            # offcanvas,
            dbc.Container([
                dbc.Row([
                #Logo Column
                dbc.Col(
                    html.Img(src="/assets/NRC_Logo.png", height="100px"),  # Adjust height as needed
                    width="auto", className="p-3"
                ),
                dbc.Col(dcc.Checklist(options=[{"label": " Today", "value": "today"}], value=["today"], id="date-filter"), 
                        width=1, xs=2, sm=2, md=2, lg=1, xl=1, xxl=1, className="p-3"),  #, className="mb-2"
                dbc.Col(dcc.DatePickerRange(
                    id='date-picker',
                    className="p-3 rounded",
                    start_date="10-11-2023",  #df['booking_date'].min()
                    end_date=end_date,  #df['booking_date'].max()
                    display_format='DD/MM/YYYY',
                    #style={"padding": "2px"},
                ), xs=12, lg=4),  #, className="p-2"
                dbc.Col(dbc.Button("Submit Date", id="date-submit", color="success", className="w-100"), 
                        xs=12, sm=12, lg=2, className="p-3"),
            ], align="center"),
            dbc.Row([
                dbc.Col(dcc.Dropdown(
                    id="boarding-station",
                    options=[
                        {"label": "Ebute Metta", "value": "Mobolaji Johnson Station Ebute Metta"},
                        {"label": "Agege", "value": "Babatunde Raji Fashola Station Agege"},
                        {"label": "Agbado", "value": "Lateef Kayode Jakande Station Agbado"},
                        {"label": "Kajola", "value": "Professor Yemi Oshinbajo Station Kajola"},
                        {"label": "Papalanto", "value": "Olu Funmilayo Ransome Kuti Papalanto"},
                        {"label": "Abeokuta", "value": "Professor Wole Soyinka Station Abeokuta"},
                        {"label": "Olodo", "value": "Aremo Olusegun Osoba Olodo"},
                        {"label": "Omi-Adio", "value": "Ladoke Akintola Station Omi-Adio"},
                        {"label": "Moniya", "value": "Obafemi Awolowo Station Moniya"},
                    ],
                    value=None,
                    placeholder="Boarding Station",
                    className="rounded"
                ), xs=12, sm=12, md=2, className="p-3"), #give width
                dbc.Col(dcc.Dropdown(
                    id="route-name",   #'Lagos-Ibadan', 'Ibadan-Lagos', 'KAJOLA-APAPA','APAPA-KAJOLA', 'LAGOS-IBADAN_LITS', 'KAJOLA-APAPA_BAT','Lagos-Ibadan_Afternoon', 'Ibadan-Lagos_Afternoon'
                    options=[
                        {"label": "LITS", "value": "LITS"},
                        {"label": "BAT", "value": "BAT"},
                    ],
                    value=None,
                    placeholder="Route Name", 
                    className="rounded"
                ), xs=6, sm=6, md=2, className="p-3"), #give width
                dbc.Col(dcc.Dropdown(
                    id="coach-type",
                    options=[
                        {"label": "First Class", "value": "First Class"},
                        {"label": "Business Class", "value": "Business Class"},
                        {"label": "Standard Class", "value": "Standard Class"},
                    ],
                    value=None,
                    placeholder="Coach Type", 
                    className="rounded"
                ), xs=6, sm=6, md=2, className="p-3"),
                dbc.Col(dcc.Input(id="user-name", type="text", placeholder="User Name", className="form-control rounded border p-1.5"), 
                        xs=6, sm=6, md=2, className="p-3"),
                dbc.Col(dcc.Input(id="pnr-number", type="text", placeholder="PNR Number", className="form-control rounded border p-1.5"), 
                        xs=6, sm=6, md=2, className="p-3"),
                dbc.Col(dbc.Button("Clear", id="clear-filters", color="success", className="w-100"), 
                        xs=12, sm=12, md=1, className="p-3"),
            ], justify="center", className="bg-white shadow rounded"),

                #Data Visualization
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H5("User Data", className="bg-success text-white text-center rounded m-0 p-2"),
                            dash_table.DataTable(
                                # [{"name": i, "id": i} for i in grid_df.columns],
                                id='user-table',
                                columns=[
                                    {'id': 'user_name', 'name': 'User Name', 'type': 'text'},
                                    {'id':'amount_paid', 'name':'Amount Paid', 'type':'numeric'},
                                ],
                                style_table={'overflowX': 'auto',
                                            #  'overflowY':'scroll',
                                            # 'width':'80%',
                                            # 'margin':'auto',
                                            'height': '300px',
                                            'overflowY': 'auto',
                                },
                                # fixed_columns={'headers': True, 'data': 1},
                                style_header={
                                    'backgroundColor': 'rgb(230, 230, 230)',
                                    'color':'dark',
                                    'fontWeight': 'bold',
                                    'textAlign': 'center',
                                },
                                style_cell={
                                    'padding': '10px',
                                    'border':'1px solid #ddd',
                                    #'textAlign': 'center',
                                    'fontFamily':'Arial, sans-serif',
                                    'minWidth':'150px', 'width':'150px', 'maxWidth':'150px',
                                    'minHeight':'10px', 'height':'10px', 'maxHeight':'10px',
                                },
                                style_cell_conditional=[
                                    {'if': {'column_id': 'user_name'},
                                        'textAlign': 'left',
                                        'min-width':'250px', 'width':'250px', 'max-width':'250px'}
                                ],
                                style_data={
                                    'whiteSpace': 'normal',
                                    # 'height': 'auto',
                                    #'border': '1px solid black'
                                },
                                filter_action='native',
                                sort_action='native',
                                #page_size=10,
                                fixed_rows={'headers': True,
                                },
                            ),
                        ], className="bg-white shadow rounded border p-2") #width=4, xs=12, sm=12, md=6, lg=12
                    ], className="mt-4 mb-4",xs=12, lg=6),
                    dbc.Col([
                        html.Div([ 
                            html.H5("Passenger Details", className="bg-success text-white text-center rounded m-0 p-2"), 
                            dash_table.DataTable(
                                # [{"name": i, "id": i} for i in grid_df.columns],
                                id='passenger-table',
                                columns=[
                                    {'id':'passenger_name', 'name':'Passenger Name', 'type':'text'},
                                    {'id':'created_at', 'name':'Created Date', 'type':'text'},
                                    {'id':'passenger_contact', 'name':'Passenger Contact', 'type':'text'},
                                    {'id':'passenger_type', 'name':'Passenger Type', 'type':'text'},
                                    {'id':'passenger_identification_number', 'name':'Passenger Identification Number', 'type':'text'},
                                    {'id':'passenger_email', 'name':'Passenger Email', 'type':'text'},
                                    {'id':'seat_number', 'name':'Seat Number', 'type':'text'},
                                ],
                                style_table={'overflowX': 'auto',
                                            #  'overflowY':'scroll',
                                            # 'width':'80%',
                                            # 'margin':'auto',
                                            'height': '300px',
                                            'overflowY': 'auto',
                                },
                                # fixed_columns={'headers': True, 'data': 1},
                                style_header={
                                    'backgroundColor': 'rgb(230, 230, 230)',
                                    'color':'dark',
                                    'fontWeight': 'bold',
                                    'textAlign': 'center',
                                },
                                style_cell={
                                    'padding': '10px',
                                    'border':'1px solid #ddd',
                                    #'textAlign': 'center',
                                    'fontFamily':'Arial, sans-serif',
                                    'minWidth':'150px', 'width':'150px', 'maxWidth':'150px',
                                    'minHeight':'10px', 'height':'10px', 'maxHeight':'10px',
                                },
                                style_cell_conditional=[
                                    {'if': {'column_id': 'user_name'},
                                        'textAlign': 'left',
                                        'min-width':'250px', 'width':'250px', 'max-width':'250px'}
                                ],
                                style_data={
                                    'whiteSpace': 'normal',
                                    # 'height': 'auto',
                                    #'border': '1px solid black'
                                },
                                filter_action='native',
                                sort_action='native',
                                #page_size=10,
                                fixed_rows={'headers': True,
                                },
                            ),
                        ], className="bg-white shadow rounded border p-2") #width=4, xs=12, sm=12, md=5, lg=12
                    ], className="mt-4 mb-4",xs=12, lg=6),
                ]), #width=4, xs=12, sm=12, md=5, lg=12

                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H5("Ticket Distribution by User Data", className="bg-success text-white text-center rounded m-0 p-2"),
                            dash_table.DataTable(
                                # [{"name": i, "id": i} for i in grid_df.columns],
                                id='user_tkt-table',
                                columns=[
                                    {'id': 'user_name', 'name': 'User Name', 'type': 'text'},
                                    {'id':'ticket_sales', 'name':'Ticket Sales', 'type':'numeric'},
                                    {'id':'medical', 'name':'Medical', 'type':'numeric'},
                                    {'id':'insurance', 'name':'Insurance', 'type':'numeric'},
                                    {'id':'stamp_duty', 'name':'Stamp Duty', 'type':'numeric'},
                                    {'id':'total_tkt_revenue', 'name':'Total Tkt Revenue', 'type':'numeric'},
                                    {'id':'nrc_tkt_rev', 'name':'NRC tkt Revenue', 'type':'numeric'},
                                    {'id':'gsd_tkt_rev', 'name':'GSD tkt Rev', 'type':'numeric'},
                                    {'id':'icrc_tkt_rev', 'name':'ICRC tkt Rev', 'type':'numeric'},
                                    {'id':'nrc_cov_fee', 'name':'NRC Conv Fees', 'type':'numeric'},
                                    {'id':'gsd_cov_fee', 'name':'GSD Conv Fees', 'type':'numeric'},
                                    {'id':'total_cov_fee', 'name':'Total Conv Fees', 'type':'numeric'},
                                    {'id':'no_of_passengers', 'name':'No.of Passengers ', 'type':'numeric'},
                                ],
                                style_table={'overflowX': 'auto',
                                            #  'overflowY':'scroll',
                                            # 'width':'80%',
                                            # 'margin':'auto',
                                            #'height': '600px',
                                            'overflowY': 'auto',
                                },
                                # fixed_columns={'headers': True, 'data': 1},
                                style_header={
                                    'backgroundColor': 'rgb(230, 230, 230)',
                                    'color':'dark',
                                    'fontWeight': 'bold',
                                    'textAlign': 'center',
                                },
                                style_cell={
                                    'padding': '10px',
                                    'border':'1px solid #ddd',
                                    #'textAlign': 'center',
                                    'fontFamily':'Arial, sans-serif',
                                    'minWidth':'150px', 'width':'150px', 'maxWidth':'150px',
                                    'minHeight':'10px', 'height':'10px', 'maxHeight':'10px',
                                },
                                style_cell_conditional=[
                                    {'if': {'column_id': 'user_name'},
                                        'textAlign': 'left',
                                        'min-width':'250px', 'width':'250px', 'max-width':'250px'}
                                ],
                                style_data={
                                    'whiteSpace': 'normal',
                                    # 'height': 'auto',
                                    #'border': '1px solid black'
                                },
                                filter_action='native',
                                sort_action='native',
                                #page_size=10,
                                fixed_rows={'headers': True,
                                },
                            ), 
                        ], className="bg-white shadow rounded border p-2")
                    ], className="mb-4", xs=12, lg=12),
                ]),
            ], fluid=True),
            #footer,
])

# Callback for Offcanvas Toggle
@user_app.callback(
    Output("offcanvas", "is_open"),
    Input("open-offcanvas", "n_clicks"),
    State("offcanvas", "is_open"),
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open

# # #Callback to autorefesh the data
# # @user_app.callback(
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

# Callbacks to make the dashboard interactive
@user_app.callback(  
    #Outputs
    Output("user-table", "data"),
    Output("passenger-table", "data"),
    Output("user_tkt-table", "data"),
    #Inputs
    Input("date-filter", "value"),
    Input("date-picker", "start_date"),
    Input("date-picker", "end_date"),
    Input("boarding-station", "value"),
    Input("route-name", "value"),
    Input("coach-type", "value"),
    Input("user-name", "value"),
    Input("pnr-number", "value"),
    Input("clear-filters", "n_clicks"),
)

def update_station(date_filter, start_date, end_date, station, route, coach, username, pnr, clear_clicks):
    try:

        booking_data = get_booking_data()
        dff = pd.DataFrame(booking_data)
        user_data = get_user_data()
        user_dff = pd.DataFrame(user_data)

        print("The length of the dataframe is:", len(dff))
        print(f"Today date:{date_filter} (Type: {type(date_filter)})")
        print(f"Start Date:{start_date} (Type: {type(start_date)})")
        print(f"End Date:{end_date} (Type: {type(end_date)})")
        print(f"Station name: {station} (Type: {type(station)})")
        print(f"Coach type: {coach} (Type: {type(coach)})")
        print(f"User name: {username} (Type: {type(username)})")
        print(f"PNR Number: {pnr} (Type: {type(pnr)})")
        print(f"\n===== DEBUG: DataFrame being filtered =====")

        # Convert start_date and end_date to native date
        start_date = pd.to_datetime(start_date).date()
        end_date = pd.to_datetime(end_date).date()
        print(f"Start Date after filtering:{start_date} (Type: {type(start_date)})")
        print(f"End Date after filtering:{end_date} (Type: {type(end_date)})")

        # Convert 'booking_date' to native date
        dff["booking_date"] = pd.to_datetime(dff["booking_date"]).dt.date
        user_dff["created_at"] = pd.to_datetime(user_dff["created_at"]).dt.date

        if "today" in date_filter:
            today_date = datetime.today().date()
            print(today_date)
            dff = dff[dff["booking_date"] == today_date]
            user_dff = user_dff[user_dff["created_at"] == today_date]
        else:
            # Filter the dataframe
            dff = dff[(dff["booking_date"] >= start_date) & (dff["booking_date"] <= end_date)]
            user_dff = user_dff[(user_dff["created_at"] >= start_date) & (user_dff["created_at"] <= end_date)]

        print(f"[INFO] DataFrame now has {len(dff)} records after date filtering.")

        #Filter by boarding station
        if station:
            dff = dff[dff["booking_from"] == station]
        print(type(station))
        print(f"[INFO] Filtered by Station: {station}. Remaining records: {len(dff)}")

        #filter by route name
        conditions = [
            dff['route_name'].isin(["Lagos-Ibadan", "Ibadan-Lagos", "LAGOS-IBADAN_LITS", "Lagos-Ibadan_Afternoon", "Ibadan-Lagos_Afternoon"]),
            dff['route_name'].isin(["APAPA-KAJOLA", "KAJOLA-APAPA", "KAJOLA-APAPA_BAT"]),
        ]
        choices = ["LITS", "BAT"]
        dff['filtered_route'] = np.select(conditions, choices, default="Other")
        print(dff['filtered_route'].unique())
        print(dff['route_name'].unique())
        
        if route:
            dff = dff[dff["filtered_route"] == route]
        print(type(route))
        print(f"[INFO] Filtered by Route Name: {route}. Remaining records: {len(dff)}")

        #filter by coach type
        if coach:
            dff = dff[dff["coach_type_name"] == coach]
        print(type(coach))
        print(f"[INFO] Filtered by Coach Type: {coach}. Remaining records: {len(dff)}")

        ##filter by user name
        if username:
            dff = dff[dff["user_name"] == username]
        print(type(username))
        print(f"[INFO] Filtered by User Name: {username}. Remaining records: {len(dff)}")

        #filter by pnr input
        if pnr:
            dff = dff[dff["pnr_number"] == pnr]
        print(type(pnr))
        print(f"[INFO] Filtered by PNR: {pnr}. Remaining records: {len(dff)}")

        #clear all filters
        clear_start_date = "10-11-2023"
        clear_end_date = datetime.today().date()
        if clear_clicks:
            start_date = clear_start_date
            end_date = clear_end_date
            username = None
            pnr = None

        # Debugging final dataset before visualization
        print(f"\n===== DEBUG: Final Filtered DataFrame =====")
        print(dff)
        print(user_dff)  # Show first few rows of the final DataFrame
        print(f"[INFO] Final DataFrame contains {len(dff)} rows.")

        #Updating the Charts based on the filtered data

        user_data_table_dff = dff.groupby('user_name').agg(
        amount_paid = ('total_fare', 'sum')
        ).reset_index()

        user_data_total_row = (
        pd.DataFrame([user_data_table_dff.drop(columns=['user_name']).sum()], columns=user_data_table_dff.columns)
        .assign(user_name='Total')
        )
        user_data_table_dff = pd.concat([user_data_table_dff, user_data_total_row], ignore_index=True)

        updated_user_table = user_data_table_dff.to_dict('records')

        passenger_data_table_dff = user_dff[['passenger_name', 'created_at', 'passenger_contact', 'passenger_type', 
                                            'passenger_identification_number', 'passenger_email', 'seat_number']]
        updated_passenger_table = passenger_data_table_dff.to_dict('records')

        user_tkt_table_dff = dff.groupby('user_name').agg(
        ticket_sales = ('total_fare', 'sum'),
        medical = ('medical', 'sum'),
        insurance = ('insurance', 'sum'),
        stamp_duty = ('stamp_duty', 'sum'),
        total_tkt_revenue = ('total_tkt_revenue', 'sum'),
        nrc_tkt_rev = ('nrc_tkt_rev', 'sum'),
        gsd_tkt_rev = ('gsd_tkt_rev', 'sum'),
        icrc_tkt_rev = ('icrc_tkt_rev', 'sum'),
        nrc_cov_fee = ('nrc_cov_fee', 'sum'),
        gsd_cov_fee = ('gsd_cov_fee', 'sum'),
        total_cov_fee = ('total_cov_fee', 'sum'),
        no_of_passengers = ('no_of_passengers', 'sum')
        ).reset_index()

        user_tkt_total_row = (
        pd.DataFrame([user_tkt_table_dff.drop(columns=['user_name']).sum()], columns=user_tkt_table_dff.columns)
        .assign(user_name='Total')
        )
        user_tkt_table_dff = pd.concat([user_tkt_table_dff, user_tkt_total_row], ignore_index=True)

        updated_user_tkt_table = user_tkt_table_dff.to_dict('records')
        
        return updated_user_table, updated_passenger_table, updated_user_tkt_table
    except Exception as e:
        print("Callback Error:", e)
        return "Err", "Err", "Err"