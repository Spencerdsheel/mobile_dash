import os
import dash
from dash import html, dcc, callback, Output, Input, dash_table, State
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
from dashboard.utils import get_cached_dashboard_data, get_booking_data
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


# Offcanvas component
offcanvas = dbc.Offcanvas(
    [
        html.P("Ticket Booking Dashboard"),
        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Station", href="/station", active="exact"),
                dbc.NavLink("User", href="/user", active="exact"),
                dbc.NavLink("Summary", href="/summary", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    id="offcanvas",
    title="Menu",
    is_open=False,
    placement="start",
    scrollable=True,
)

# Navbar with optional Collapse wrapping the toggle button
# Navbar with no spacing on the left
navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Button(
                            "☰",
                            id="open-offcanvas",
                            n_clicks=0,
                            color="light",
                            className="p-0 m-0 bg-success border-0 text-white",  # no margin or border
                        ),
                        width="auto",
                        className="p-0 m-0",  # remove space from column
                    ),
                    dbc.Col(
                        html.A(
                            dbc.NavbarBrand("Ticket Booking Dashboard", className="ms-2"),
                            href="/",
                            style={"textDecoration": "none"},
                        ),
                        width="auto",
                    ),
                    dbc.Col(
                        html.A(
                            dbc.NavbarBrand("Logout", className="ms-2"),
                            href="/logout",
                        ),
                        width="auto",
                        className="ms-auto"
                    ),
                ],
                align="center",
                className="g-0 w-100",
            ),
        ],
        fluid=True,  # removes container's side spacing
        #className="p-0",  # just in case
    ),
    color="success",
    dark=True,
    #className="p-0",  # navbar padding reset
)


#Copyright © 2025 Ticket Booking System
footer = dbc.Container(
    dbc.Row(
        dbc.Col(
            html.Small("Copyright © 2025 Ticket Booking System",
                       className="text-center text-white"),
            width=12
        ),
        # dbc.Col(
        #             html.Img(src="assets/GSDS_Logo.png", height="40px"),  # Adjust height as needed
        #             width="auto", className="p-3"
        # )
    ),
    fluid=True,
    className="bg-success py-3 mt-auto"
)

end_date = datetime.today().date()


# Define the app
#Initialize the Dash app
summary_app = DjangoDash('Summary', external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
                 external_scripts=['https://cdnjs.cloudflare.com/ajax/libs/plotly.js/3.0.0-rc.2/plotly.min.js'],
                 add_bootstrap_links=True)

#dash.register_page(__name__, path="/summary")

# Define the layout
summary_app.layout = html.Div([
    
            navbar,
            offcanvas,
            dbc.Container([
                dbc.Row([
                    #Logo Column
                    dbc.Col(
                        html.Img(src="/assets/NRC_Logo.png", height="100px"),  # Adjust height as needed
                        #html.Img(src=dash.get_asset_url("NRC_Logo.png"), height="100px"),  # Adjust height as needed
                        width="auto", className="p-3"
                    ),
                    dbc.Col(dcc.Checklist(options=[{"label": " Today", "value": "today"}], value=["today"], id="date-filter"), 
                            width=1, xs=2, sm=2, md=2, lg=1, xl=1, xxl=1, className="p-3 mt-2"),  #, className="mb-2"
                    dbc.Col(dcc.DatePickerRange(
                        id='date-picker',
                        className="rounded",
                        start_date="10-11-2023",  #df['booking_date'].min()
                        end_date=end_date,  #df['booking_date'].max()
                        display_format='DD/MM/YYYY',
                    ), xs=12, sm=12, md=3, lg=4, className="p-3 rounded"),  #, className="p-2"
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
                            html.H5("Sales by Date", className="bg-success text-white text-center rounded m-0 p-2"),
                            dcc.Graph(id="daily-transactions"),
                        ], className="bg-white shadow rounded border p-2")  #width=4, xs=12, sm=12, md=12, lg=12
                    ], className="mt-4 mb-4", xs=12, lg=6),
                    dbc.Col([
                        html.Div([
                            html.H5("Sales by Coach Type", className="bg-success text-white text-center rounded m-0 p-2"),
                            dcc.Graph(id="coachtype-pie"),
                        ], className="bg-white shadow rounded border p-2") #width=4, xs=12, sm=12, md=12, lg=12
                    ], className="mt-4 mb-4", xs=12, lg=6),
                ]),
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H5("Fare by Coach Type", className="bg-success text-white text-center rounded m-0 p-2"),
                            dcc.Graph(id="coachtype-bar"),
                        ], className="bg-white shadow rounded border p-2"),  #width=4, xs=12, sm=12, md=12, lg=12
                    ], className="mt-4 mb-4", xs=12, lg=6),
                    dbc.Col([
                        html.Div([
                            html.H5("Fare by Station", className="bg-success text-white text-center rounded m-0 p-2"),
                            dcc.Graph(id="stationtype-bar"),
                        ], className="bg-white shadow rounded border p-2"),  #width=4, xs=12, sm=12, md=12, lg=12
                    ], className="mt-4 mb-4", xs=12, lg=6),
                ]),
            ], fluid=True),
            footer,
        
    
])

# Callback for Offcanvas Toggle
@summary_app.callback(
    Output("offcanvas", "is_open"),
    Input("open-offcanvas", "n_clicks"),
    State("offcanvas", "is_open"),
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open

# #Callback to autorefesh the data
# # @summary_app.callback(
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
@summary_app.callback(  
    Output("daily-transactions", "figure"),
    Output("coachtype-pie", "figure"),
    Output("coachtype-bar", "figure"),
    Output("stationtype-bar", "figure"),
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

def update_station(date_filter, start_date, end_date, station, route,  coach, username, pnr, clear_clicks):
    booking_data = get_booking_data()
    dff = pd.DataFrame(booking_data)

    print("The length of the dataframe is:", len(dff))
    print(f"Today date:{date_filter} (Type: {type(date_filter)})")
    print(f"Start Date:{start_date} (Type: {type(start_date)})")
    print(f"End Date:{end_date} (Type: {type(end_date)})")
    print(f"Station name: {station} (Type: {type(station)})")
    print(f"Route name: {route} (Type: {type(route)})")
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

    if "today" in date_filter:
        today_date = datetime.today().date()
        print(today_date)
        dff = dff[dff["booking_date"] == today_date]
    else:
        # Filter the dataframe
        dff = dff[(dff["booking_date"] >= start_date) & (dff["booking_date"] <= end_date)]

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
    print(dff)  # Show first few rows of the final DataFrame
    print(f"[INFO] Final DataFrame contains {len(dff)} rows.")

    #Updating the Charts based on the filtered data
    daily_transaction_dff = dff.groupby("booking_date")["total_fare"].sum().reset_index()
    updated_fig2 = px.line(daily_transaction_dff, x="booking_date", y="total_fare",
                           labels={"value": "Total Sales", "Date": "Date"}, title="Total Sales by Date")

    # For this example, we update the pie and bar charts to reflect totals by Coach Type and Station.
    # Update fig3 (Pie Chart): Sales by Coach Type.
    updated_ticket_class_dff = dff.groupby("coach_type_name")["total_fare"].sum().reset_index()
    # updated_ticket_class_df.rename(columns={"Total Fare": "Sales"}, inplace=True)
    updated_fig3 = px.pie(updated_ticket_class_dff, values="total_fare", names="coach_type_name", title="Sales by Coach Type")

    # Update fig4 (Bar Chart): Total Fare by Coach Type.
    # updated_fare_df = dff.groupby("Coach Type")["Total Fare"].sum().reset_index()
    updated_fig4 = px.bar(updated_ticket_class_dff, x="coach_type_name", y="total_fare",
                          labels={"Total Fare": "Ticket Sales"}, title="Total Fare by Coach Type")

    # Update fig5 (Horizontal Bar Chart): Total Fare by Boarding Station.
    updated_station_dff = dff.groupby("booking_from")["total_fare"].sum().reset_index()
    updated_fig5 = px.bar(updated_station_dff, x="total_fare", y="booking_from", orientation="h", title="Total Fare by Boarding Station")
    
    return updated_fig2, updated_fig3, updated_fig4, updated_fig5