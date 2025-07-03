import os
import time
import dash
from dash import html, dcc, callback, Output, Input, dash_table, State
from dash import dash_table
from django_plotly_dash import DjangoDash
import dpd_components as dpd
import dash_bootstrap_components as dbc


from dashboard.utils import get_cached_dashboard_data, get_booking_data, get_validator_data
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
# from utils import get_booking_data #get_validator_data, get_user_data

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


end_date = datetime.today().date()

#Initialize the Dash app
dashboard_app = DjangoDash('Dashboard', external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP], #use_pages=True,
                 external_scripts=['https://cdnjs.cloudflare.com/ajax/libs/plotly.js/3.0.0-rc.2/plotly.min.js'],
                 add_bootstrap_links=True)


dashboard_app.layout = html.Div([
            # navbar,
            # offcanvas,
            dbc.Container([        
                dbc.Row([
                    # Logo Column
                    dbc.Col(
                        html.Div([
                            html.Img(src="/assets/NRC_Logo.png", height="100px"),  # Adjust height as needed
                        ]), width="auto", className="p-3"
                    ),
                        # Checklist + Date Range Picker in one row
                    dbc.Col(
                        html.Div([
                            dbc.Row([
                                dbc.Col(
                                    dcc.Checklist(
                                        options=[{"label": " Today", "value": "today"}],
                                        value=["today"],
                                        id="date-filter"
                                    ),
                                    width="auto", className="pe-1"
                                ),
                                dbc.Col(
                                    dcc.DatePickerRange(
                                        id='date-picker',
                                        start_date="2023-11-10",
                                        end_date=end_date,
                                        display_format='DD/MM/YYYY',
                                        style={
                                            'maxWidth': '180px',
                                            'fontSize': '12px',
                                            'padding': '0.25rem',
                                            'whiteSpace': 'nowrap'
                                        },
                                    ),
                                    width="auto"
                                )
                            ], className="d-flex flex-nowrap align-items-center justify-content-start"),
                        ]),
                        xs=12, sm=12, md=4, lg=3, xl=3, xxl=3, className="p-3"
                    ),
                    dbc.Col(
                        html.Div([
                            dbc.Button("Submit Date", id="date-submit", color="success", className="w-100")
                        ]),
                        xs=12, sm=12, lg=2, className="p-3"
                    ),
                ], justify="center", align="center"),

                dbc.Row([
                    dbc.Col(
                        html.Div([
                            dcc.Dropdown(
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
                            )
                        ]),
                        xs=12, sm=12, md=2, className="p-3"
                    ),
                    dbc.Col(
                        html.Div([
                            dcc.Dropdown(
                                id="route-name",
                                options=[
                                    {"label": "LITS", "value": "LITS"},
                                    {"label": "BAT", "value": "BAT"},
                                ],
                                value=None,
                                placeholder="Route Name",
                                className="rounded"
                            )
                        ]),
                        xs=6, sm=6, md=2, className="p-3"
                    ),
                    dbc.Col(
                        html.Div([
                            dcc.Dropdown(
                                id="coach-type",
                                options=[
                                    {"label": "First Class", "value": "First Class"},
                                    {"label": "Business Class", "value": "Business Class"},
                                    {"label": "Standard Class", "value": "Standard Class"},
                                ],
                                value=None,
                                placeholder="Coach Type",
                                className="rounded"
                            )
                        ]),
                        xs=6, sm=6, md=2, className="p-3"
                    ),
                    dbc.Col(
                        html.Div([
                            dcc.Input(id="user-name", type="text", placeholder="User Name", className="form-control rounded border p-1.5")
                        ]),
                        xs=6, sm=6, md=2, className="p-3"
                    ),
                    dbc.Col(
                        html.Div([
                            dcc.Input(id="pnr-number", type="text", placeholder="PNR Number", className="form-control rounded border p-1.5")
                        ]),
                        xs=6, sm=6, md=2, className="p-3"
                    ),
                    dbc.Col(
                        html.Div([
                            dbc.Button("Clear", id="clear-filters", color="success", className="w-100")
                        ]),
                        xs=12, sm=12, md=1, className="p-3"
                    ),
                ], justify="center", className="bg-white shadow rounded"),



            # KPI Indicators
            dbc.Row([
                #Left side column for KPI indicators
                dbc.Col([
                    #Row for first KPI Indicators
                    dbc.Row([
                        dbc.Col(html.Div([
                            html.H5("Tickets", className="bg-warning text-white text-center"),
                            html.H4(id ="kpi-tickets", className="text-center") #children= f"{df['no_of_passengers'].sum():,}",
                        ], className="bg-white p-2 rounded text-dark mb-4 border border-warning shadow"), width=4,xs=6, sm=6, md=4),
                        dbc.Col(html.Div([
                            html.H5("Transactions", className="bg-warning text-white text-center"),
                            html.H4(id="kpi-transactions", className="text-center") #children=f"{len(df):,}",
                        ], className="bg-white p-2 rounded text-dark mb-4 border border-warning shadow"), width=4,xs=6, sm=6, md=4),
                        dbc.Col(html.Div([
                            html.H5("Validated Tickets", className="bg-warning text-white text-center"),
                            html.H4(id="validated-tickets", className="text-center") #children=f"{df['nrc_tkt_rev'].sum().astype(int):,}",
                        ], className="bg-white p-2 rounded text-dark mb-4 border border-warning shadow"), width=4, xs=12, sm=12, md=4),
                    ], className="mb-3"),
                    #Row for second KPI Indicators
                    dbc.Row([
                        dbc.Col(html.Div([
                            html.H5("Total Sales", className="bg-warning text-white text-center"), 
                            html.H4(id="total-sales", className="text-center") #children=f"{df['total_fare'].sum():,}",
                        ], className="bg-white p-2 rounded text-dark mb-4 border border-warning shadow"), width=6, xs=6, sm=6, md=6),
                        dbc.Col(html.Div([
                            html.H5("Online Sales", className="bg-warning text-white text-center"),
                            html.H4(id="online-sales", className="text-center") # children=f"{df[df['type']=='ONLINE']['total_fare'].sum():,}",
                        ], className="bg-white p-2 rounded text-dark mb-4 border border-warning shadow"), width=6,xs=6, sm=6, md=6),
                        dbc.Col(html.Div([
                            html.H5("TOM Sales", className="bg-warning text-white text-center"),
                            html.H4(id="tom-sales", className="text-center") # children=f"{df[df['type']=='OFFLINE']['total_fare'].sum():,}",
                        ], className="bg-white p-2 rounded text-dark mb-4 border border-warning shadow"), width=6,xs=6, sm=6, md=6),
                        dbc.Col(html.Div([
                            html.H5("NRC Revenue", className="bg-warning text-white text-center"),
                            html.H4(id="nrc-revenue", className="text-center") # children=f"{df['nrc_tkt_rev'].sum().astype(int):,}",
                        ], className="bg-white p-2 rounded text-dark mb-4 border border-warning shadow"), width=6, xs=6, sm=6, md=6),
                    ], className="mb-4"),
                ],className="mt-4", xs=12, lg=6),

                #Right side column for Chart
            dbc.Col([
                    html.Div([
                        html.H5("Ticket Sale", className="bg-success text-white text-center rounded m-0"),
                        dcc.Graph(id="coachtype-pie") #style={'height': '100%', 'width': '100%'}
                    ], className="bg-white shadow rounded mb-4 border p-2")
                ], className="mt-4", xs=12, lg=6),
            ]),
            
            # html.Br(),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5("Summary Table", className="bg-success text-white text-center rounded m-0"),
                        dash_table.DataTable(
                            id='summary-table',
                            columns=[
                                {'id': 'booking_from', 'name': 'Station', 'type': 'text'},
                                {'id': 'total_fare', 'name': 'Ticket Sales', 'type': 'numeric'},
                                {'id': 'medical', 'name': 'Medical', 'type': 'numeric'},
                                {'id': 'insurance', 'name': 'Insurance', 'type': 'numeric'},
                                {'id': 'stamp_duty', 'name': 'Stamp Duty', 'type': 'numeric'},
                                {'id': 'total_tkt_revenue', 'name': 'Total Ticket Revenue', 'type': 'numeric'},
                                {'id': 'total_cov_fee', 'name': 'Total Coverage Fee', 'type': 'numeric'},
                                {'id': 'nrc_cov_fee', 'name': 'NRC Coverage Fee', 'type': 'numeric'},
                                {'id': 'nrc_tkt_rev', 'name': 'NRC Ticket Revenue', 'type': 'numeric'},
                                {'id': 'gsd_tkt_rev', 'name': 'GSD Ticket Revenue', 'type': 'numeric'},
                                {'id': 'gsd_cov_fee', 'name': 'GSD Coverage Fee', 'type': 'numeric'},
                                {'id': 'icrc_tkt_rev', 'name': 'ICRC Ticket Revenue', 'type': 'numeric'},
                                {'id': 'no_of_passengers', 'name': 'No of Passengers', 'type': 'numeric'},
                            ],
                            style_table={'overflowX': 'auto', 'overflowY': 'scroll'},
                            style_header={
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'fontWeight': 'bold',
                                'textAlign': 'center',
                            },
                            style_cell={
                                'padding': '10px',
                                'border': '1px solid #ddd',
                                'fontFamily': 'Arial, sans-serif',
                                'minWidth': '150px', 'width': '150px', 'maxWidth': '150px',
                            },
                            style_cell_conditional=[
                                {
                                    'if': {'column_id': 'booking_from'},
                                    'textAlign': 'left',
                                    'minWidth': '270px', 'width': '270px', 'maxWidth': '270px'
                                }
                            ],
                            filter_action='native',
                            sort_action='native',
                            fixed_rows={'headers': True,
                                        'Total': True,
                                        }
                            ,
                        )
                    ], className="shadow rounded border p-2") #, className="p-2"
                ], className="mb-4", xs=12, lg=12)
            ]),
        ], fluid=True),
            # footer,
])

@dashboard_app.callback(
    Output("offcanvas", "is_open"),  
    Input("open-offcanvas", "n_clicks"),  
    State("offcanvas", "is_open"),
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open


# Callbacks to make the dashboard interactive
@dashboard_app.callback(  
    Output("kpi-tickets", "children"),
    Output("kpi-transactions", "children"),
    Output("validated-tickets", "children"),
    Output("online-sales", "children"),
    Output("tom-sales", "children"),
    Output("total-sales", "children"),
    Output("nrc-revenue", "children"),
    #Output("daily-transactions", "figure"),
    Output("coachtype-pie", "figure"),
    Output("summary-table", "data"),
    #Output("summary-table", "columns"),
    #Inputs
    #Input("auto-refresh", "n_intervals"),
    #Input("initial-load", "n_intervals"),
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


def update_dashboard(date_filter, start_date, end_date, station, route,  coach, username, pnr, clear_clicks):
    try:
        booking_data = get_booking_data()
        df = pd.DataFrame(booking_data)
        dff = df[df['booking_status'] == 'BOOKED']
        validator_data = get_validator_data()
        validator_dff = pd.DataFrame(validator_data)

        dff.head()
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
        validator_dff["created_at"] = pd.to_datetime(validator_dff["created_at"]).dt.date

        if "today" in date_filter:
            today_date = datetime.today().date()
            print(today_date)
            dff = dff[dff["booking_date"] == today_date]
            validator_dff = validator_dff[validator_dff["created_at"] == today_date]
        else:
            # Filter the dataframe
            dff = dff[(dff["booking_date"] >= start_date) & (dff["booking_date"] <= end_date)]
            validator_dff = validator_dff[(validator_dff["created_at"] >= start_date) & (validator_dff["created_at"] <= end_date)]
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
        print(f"The length of the validator dataframe is: {len(validator_dff)}")

        #update the Kpi indicators
        tickets_value = dff['no_of_passengers'].sum()
        transactions_value = len(dff)
        validated_ticket_value = len(validator_dff)
        online_value = dff[dff['type']=='ONLINE']['total_fare'].sum()
        tom_value = dff[dff['type']=='OFFLINE']['total_fare'].sum()
        total_sales_value = dff["total_fare"].sum()
        nrc_rev_value = dff['nrc_tkt_rev'].sum().astype(int)


        kpi_tickets = f"{tickets_value:,}"
        kpi_transactions = f"{transactions_value:,}"
        validated_tickets = f"{validated_ticket_value:,}"
        total_sales = f"{total_sales_value:,}"
        online_sales = f"{online_value:,}"
        tom_sales = f"{tom_value:,}"
        nrc_rev = f"{nrc_rev_value:,}"

        print("\n===== DEBUG: KPI Values =====")
        print(f"Total Tickets Sold: {kpi_tickets}")
        print(f"Total Transactions: {kpi_transactions}")
        print(f"Validated Tickets: {validated_tickets}")
        print(f"Total Sales Amount: {total_sales}")
        print(f"Total Sales Amount: {online_sales}")
        print(f"Total Sales Amount: {tom_sales}")
        print(f"Total Sales Amount: {nrc_rev}")

        #Updating the Charts 
        # daily_transaction_dff = dff.groupby("booking_date")["total_fare"].sum().reset_index()
        # updated_fig1 = px.line(daily_transaction_dff, x="booking_date", y="total_fare",
        #                         labels={"value": "Total Sales", "booking_date": "Date"}, title="Total Sales by Date")
        
        updated_ticket_class_dff = dff.groupby("coach_type_name")["total_fare"].sum().reset_index()
        # updated_ticket_class_df.rename(columns={"Total Fare": "Sales"}, inplace=True)
        updated_fig1 = px.pie(updated_ticket_class_dff, values="total_fare", names="coach_type_name", title="Sales by Coach Type")
        
        #updating the table
        summary_dff = dff.groupby('booking_from').agg(
        total_fare=('total_fare', 'sum'),
        medical=('medical', 'sum'),
        insurance=('insurance', 'sum'),
        stamp_duty=('stamp_duty', 'sum'),
        total_tkt_revenue=('total_tkt_revenue', 'sum'),
        total_cov_fee=('total_cov_fee', 'sum'),
        nrc_cov_fee=('nrc_cov_fee', 'sum'),
        nrc_tkt_rev=('nrc_tkt_rev', 'sum'),
        gsd_tkt_rev=('gsd_tkt_rev', 'sum'),
        gsd_cov_fee=('gsd_cov_fee', 'sum'),
        icrc_tkt_rev=('icrc_tkt_rev', 'sum'),
        no_of_passengers=('no_of_passengers', 'count')
        ).reset_index()

        total_row = (
        pd.DataFrame([summary_dff.drop(columns=['booking_from']).sum()], columns=summary_dff.columns)
        .assign(booking_from='Total')
        )
        summary_dff = pd.concat([summary_dff, total_row], ignore_index=True)

        updated_table = summary_dff.to_dict('records')

        return kpi_tickets, kpi_transactions, validated_tickets, total_sales, online_sales, tom_sales, nrc_rev, updated_fig1, updated_table
    except Exception as e:
        print("Callback Error:", e)
        return "Err", "Err", "Err", "Err", "Err", "Err", "Err", {}, []
    
# #Callback to clear all filters
# @dashboard_app.callback(
#     Output("date-picker", "start_date"),
#     Output("date-picker", "end_date"),
#     Output("user-name", "value"),
#     Output("pnr-number", "value"),
#     Input("clear-filters", "n_clicks")
# )
# def clear_filters(n_clicks):
#     return start_date, None, None, None, None


