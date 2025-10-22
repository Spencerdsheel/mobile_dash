# summary_app.py
import logging
from datetime import datetime

import pandas as pd
import plotly.express as px
from dash import html, dcc, Output, Input, dash_table
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

from dashboard.utils import read_range_booking, read_all_chunks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

end_date = datetime.today().date()

summary_app = DjangoDash(
    "Summary",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    add_bootstrap_links=True,
)

summary_app.layout = html.Div(
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
                        dbc.Col(html.Div([html.H5("Sales by Date"), dcc.Graph(id="daily-transactions")], className="bg-white p-2 shadow rounded"), xs=12, lg=6),
                        dbc.Col(html.Div([html.H5("Sales by Coach Type"), dcc.Graph(id="coachtype-pie")], className="bg-white p-2 shadow rounded"), xs=12, lg=6),
                    ],
                    className="mt-4",
                ),
                dbc.Row(
                    [
                        dbc.Col(html.Div([html.H5("Fare by Coach Type"), dcc.Graph(id="coachtype-bar")], className="bg-white p-2 shadow rounded"), xs=12, lg=6),
                        dbc.Col(html.Div([html.H5("Fare by Station"), dcc.Graph(id="stationtype-bar")], className="bg-white p-2 shadow rounded"), xs=12, lg=6),
                    ],
                    className="mt-4",
                ),
            ],
            fluid=True,
        )
    ]
)


@summary_app.callback(
    Output("daily-transactions", "figure"),
    Output("coachtype-pie", "figure"),
    Output("coachtype-bar", "figure"),
    Output("stationtype-bar", "figure"),
    Input("date-filter", "value"),
    Input("date-picker", "start_date"),
    Input("date-picker", "end_date"),
)
def update_summary(date_filter, start_date, end_date):
    try:
        start_date = pd.to_datetime(start_date).date()
        end_date = pd.to_datetime(end_date).date()
        if date_filter and "today" in date_filter:
            start_date = end_date = datetime.today().date()

        booking_agg = read_range_booking(start_date, end_date)
        daily = pd.DataFrame(booking_agg.get("daily_trend", []))
        by_coach = pd.DataFrame(booking_agg.get("by_coach", []))
        by_station = pd.DataFrame(booking_agg.get("by_station", []))

        # daily line
        if not daily.empty:
            daily["booking_date"] = pd.to_datetime(daily["booking_date"]).dt.date
            daily = daily.sort_values("booking_date")
            daily_fig = px.line(daily, x="booking_date", y="total_fare", labels={"total_fare": "Total Sales", "booking_date": "Date"}, title="Total Sales by Date")
        else:
            # fallback: try raw chunks
            records = read_all_chunks("booking")
            if records:
                raw_df = pd.DataFrame(records)
                raw_df["booking_date"] = pd.to_datetime(raw_df["booking_date"]).dt.date
                raw_df = raw_df[(raw_df["booking_date"] >= start_date) & (raw_df["booking_date"] <= end_date)]
                daily2 = raw_df.groupby("booking_date")["total_fare"].sum().reset_index()
                daily_fig = px.line(daily2, x="booking_date", y="total_fare", title="Total Sales by Date")
            else:
                daily_fig = {}

        # pie by coach
        if not by_coach.empty:
            if "total_fare" not in by_coach.columns and "value" in by_coach.columns:
                by_coach = by_coach.rename(columns={"value": "total_fare"})
            pie_fig = px.pie(by_coach, values="total_fare", names="coach_type_name", title="Sales by Coach Type")
            bar_coach = px.bar(by_coach, x="coach_type_name", y="total_fare", title="Total Fare by Coach Type")
        else:
            pie_fig = {}
            bar_coach = {}

        # station bar
        if not by_station.empty:
            if "total_fare" not in by_station.columns and "value" in by_station.columns:
                by_station = by_station.rename(columns={"value": "total_fare"})
            station_bar = px.bar(by_station, x="total_fare", y="booking_from", orientation="h", title="Total Fare by Boarding Station")
        else:
            station_bar = {}

        return daily_fig, pie_fig, bar_coach, station_bar

    except Exception as e:
        logger.exception("Callback Error in summary_app.update_station:")
        return {}, {}, {}, {}
