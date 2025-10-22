# user_app.py
import logging
from datetime import datetime

import pandas as pd
import plotly.express as px
from dash import html, dcc, Output, Input, dash_table
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

from dashboard.utils import read_range_booking, read_range_user, read_all_chunks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

end_date = datetime.today().date()

user_app = DjangoDash(
    "User",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    add_bootstrap_links=True,
)

user_app.layout = html.Div(
    [
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="/assets/NRC_Logo.png", height="100px"), width="auto", className="p-3"),
                        dbc.Col(dcc.Checklist(options=[{"label": " Today", "value": "today"}], value=["today"], id="date-filter"), width=1, className="p-3"),
                        dbc.Col(dcc.DatePickerRange(id="date-picker", start_date="2023-11-10", end_date=end_date, display_format="DD/MM/YYYY"), xs=12, lg=4),
                        dbc.Col(dbc.Button("Submit Date", id="date-submit", color="success", className="w-100"), xs=12, lg=2, className="p-3"),
                    ],
                    align="center",
                ),
                dbc.Row(
                    [
                        dbc.Col(dcc.Input(id="user-name", type="text", placeholder="User Name", className="form-control"), xs=6, className="p-3"),
                        dbc.Col(dcc.Input(id="pnr-number", type="text", placeholder="PNR Number", className="form-control"), xs=6, className="p-3"),
                    ],
                    className="bg-white shadow rounded",
                ),
                dbc.Row(
                    [
                        dbc.Col(html.Div([html.H5("User Tickets", className="bg-success text-white"), dash_table.DataTable(id="user-tkt-table", columns=[
                            {"id": "user_name", "name": "User"},
                            {"id": "ticket_sales", "name": "Ticket Sales"},
                            {"id": "no_of_passengers", "name": "Passengers"},
                            {"id": "total_tkt_revenue", "name": "Total Ticket Revenue"},
                        ], style_table={"overflowY": "scroll"}, filter_action="native", sort_action="native")], className="bg-white p-2 shadow rounded"), xs=12, lg=12),
                    ],
                    className="mt-4",
                ),
                dbc.Row(
                    [
                        dbc.Col(html.Div([html.H5("Passenger Details", className="bg-success text-white"), dash_table.DataTable(id="passenger-table", columns=[
                            {"id": "passenger_name", "name": "Passenger"},
                            {"id": "created_at", "name": "Created At"},
                            {"id": "passenger_contact", "name": "Contact"},
                            {"id": "passenger_type", "name": "Type"},
                            {"id": "passenger_identification_number", "name": "ID"},
                            {"id": "passenger_email", "name": "Email"},
                            {"id": "seat_number", "name": "Seat"},
                        ], style_table={"overflowY": "scroll"}, filter_action="native", sort_action="native")], className="bg-white p-2 shadow rounded"), xs=12, lg=12),
                    ]
                ),
            ],
            fluid=True,
        )
    ]
)


@user_app.callback(
    Output("user-tkt-table", "data"),
    Output("passenger-table", "data"),
    Input("date-filter", "value"),
    Input("date-picker", "start_date"),
    Input("date-picker", "end_date"),
    Input("user-name", "value"),
    Input("pnr-number", "value"),
)
def update_user_page(date_filter, start_date, end_date, username, pnr):
    try:
        start_date = pd.to_datetime(start_date).date()
        end_date = pd.to_datetime(end_date).date()
        if date_filter and "today" in date_filter:
            start_date = end_date = datetime.today().date()

        # Try aggregated user data first
        user_agg = read_range_user(start_date, end_date)
        user_summary = pd.DataFrame(user_agg.get("by_user", []))
        passenger_records = []

        # If user_name or pnr filters exist, or by_user empty -> fallback to row-level
        if (username or pnr) or user_summary.empty:
            records = read_all_chunks("user")
            if not records:
                return [], []
            raw_df = pd.DataFrame(records)
            if "created_at" in raw_df.columns:
                raw_df["created_at"] = pd.to_datetime(raw_df["created_at"]).dt.date
            raw_df = raw_df[(raw_df["created_at"] >= start_date) & (raw_df["created_at"] <= end_date)]
            if username:
                raw_df = raw_df[raw_df["user_name"] == username]
            # pnr may not exist in user table; handle similar in booking if needed

            # user tickets aggregation
            user_tkt = raw_df.groupby("user_name").agg(
                ticket_sales=("total_fare", "sum"),
                no_of_passengers=("no_of_passengers", "sum"),
                total_tkt_revenue=("total_tkt_revenue", "sum"),
            ).reset_index()
            user_records = user_tkt.to_dict("records")

            # passenger detail rows
            # if user passenger details exist in user chunk rows (passenger_name, etc.)
            if "passenger_name" in raw_df.columns:
                passenger_records = raw_df[["passenger_name", "created_at", "passenger_contact", "passenger_type", "passenger_identification_number", "passenger_email", "seat_number"]].to_dict("records")
            else:
                passenger_records = []
        else:
            # Use aggregated by_user for user ticket table
            if not user_summary.empty:
                # by_user has coach sums; normalise to expected columns if possible
                if "total_fare" in user_summary.columns:
                    user_summary = user_summary.rename(columns={"total_fare": "ticket_sales"})
                user_summary["no_of_passengers"] = 0
                user_summary["total_tkt_revenue"] = 0
                user_records = user_summary.to_dict("records")
            else:
                user_records = []

        return user_records, passenger_records

    except Exception as e:
        logger.exception("Callback Error in user_app.update_user_page:")
        return [], []
