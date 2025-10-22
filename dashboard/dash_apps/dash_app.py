# dash_app.py
import logging
from datetime import datetime

import pandas as pd
import plotly.express as px
from dash import html, dcc, Output, Input, dash_table
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

from dashboard.utils import (
    read_range_booking,
    read_range_validator,
    read_range_user,
    read_all_chunks,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

end_date = datetime.today().date()

dashboard_app = DjangoDash(
    "Dashboard",
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    add_bootstrap_links=True,
)

dashboard_app.layout = html.Div(
    [
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="/assets/NRC_Logo.png", height="100px"), width="auto", className="p-3"),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dcc.Checklist(
                                                    options=[{"label": " Today", "value": "today"}],
                                                    value=["today"],
                                                    id="date-filter",
                                                ),
                                                width="auto",
                                            ),
                                            dbc.Col(
                                                dcc.DatePickerRange(
                                                    id="date-picker",
                                                    start_date="2023-11-10",
                                                    end_date=end_date,
                                                    display_format="DD/MM/YYYY",
                                                ),
                                                width="auto",
                                            ),
                                        ]
                                    )
                                ]
                            ),
                            xs=12,
                            sm=12,
                            md=4,
                            lg=3,
                            xl=3,
                            className="p-3",
                        ),
                        dbc.Col(dbc.Button("Submit Date", id="date-submit", color="success", className="w-100"), xs=12, sm=12, lg=2, className="p-3"),
                    ],
                    justify="center",
                    align="center",
                ),
                # KPI + Chart row
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            html.Div(
                                                [html.H5("Tickets", className="bg-warning text-white text-center"), html.H4(id="kpi-tickets", className="text-center")],
                                                className="bg-white p-2 rounded mb-4 border border-warning shadow",
                                            ),
                                            width=4,
                                        ),
                                        dbc.Col(
                                            html.Div(
                                                [html.H5("Transactions", className="bg-warning text-white text-center"), html.H4(id="kpi-transactions", className="text-center")],
                                                className="bg-white p-2 rounded mb-4 border border-warning shadow",
                                            ),
                                            width=4,
                                        ),
                                        dbc.Col(
                                            html.Div(
                                                [html.H5("Validated Tickets", className="bg-warning text-white text-center"), html.H4(id="validated-tickets", className="text-center")],
                                                className="bg-white p-2 rounded mb-4 border border-warning shadow",
                                            ),
                                            width=4,
                                        ),
                                    ]
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            html.Div(
                                                [html.H5("Total Sales", className="bg-warning text-white text-center"), html.H4(id="total-sales", className="text-center")],
                                                className="bg-white p-2 rounded mb-4 border border-warning shadow",
                                            ),
                                            width=6,
                                        ),
                                        dbc.Col(
                                            html.Div(
                                                [html.H5("NRC Revenue", className="bg-warning text-white text-center"), html.H4(id="nrc-revenue", className="text-center")],
                                                className="bg-white p-2 rounded mb-4 border border-warning shadow",
                                            ),
                                            width=6,
                                        ),
                                    ]
                                ),
                            ],
                            xs=12,
                            lg=6,
                        ),
                        dbc.Col(
                            html.Div(
                                [html.H5("Ticket Sale", className="bg-success text-white text-center rounded m-0"), dcc.Graph(id="coachtype-pie")],
                                className="bg-white shadow rounded mb-4 border p-2",
                            ),
                            xs=12,
                            lg=6,
                        ),
                    ]
                ),
                # Summary table
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    html.H5("Summary Table", className="bg-success text-white text-center rounded m-0"),
                                    dash_table.DataTable(
                                        id="summary-table",
                                        columns=[
                                            {"id": "booking_from", "name": "Station", "type": "text"},
                                            {"id": "total_fare", "name": "Ticket Sales", "type": "numeric"},
                                            {"id": "medical", "name": "Medical", "type": "numeric"},
                                            {"id": "insurance", "name": "Insurance", "type": "numeric"},
                                            {"id": "stamp_duty", "name": "Stamp Duty", "type": "numeric"},
                                            {"id": "total_tkt_revenue", "name": "Total Ticket Revenue", "type": "numeric"},
                                            {"id": "total_cov_fee", "name": "Total Coverage Fee", "type": "numeric"},
                                            {"id": "nrc_cov_fee", "name": "NRC Coverage Fee", "type": "numeric"},
                                            {"id": "nrc_tkt_rev", "name": "NRC Ticket Revenue", "type": "numeric"},
                                            {"id": "gsd_tkt_rev", "name": "GSD Ticket Revenue", "type": "numeric"},
                                            {"id": "gsd_cov_fee", "name": "GSD Coverage Fee", "type": "numeric"},
                                            {"id": "icrc_tkt_rev", "name": "ICRC Ticket Revenue", "type": "numeric"},
                                            {"id": "no_of_passengers", "name": "No of Passengers", "type": "numeric"},
                                        ],
                                        style_table={"overflowX": "auto", "overflowY": "scroll"},
                                        style_header={"backgroundColor": "rgb(230, 230, 230)", "fontWeight": "bold", "textAlign": "center"},
                                        style_cell={"padding": "10px", "border": "1px solid #ddd", "fontFamily": "Arial, sans-serif"},
                                        filter_action="native",
                                        sort_action="native",
                                        fixed_rows={"headers": True},
                                    )
                                ],
                                className="shadow rounded border p-2",
                            ),
                            xs=12,
                            lg=12,
                        )
                    ]
                ),
            ],
            fluid=True,
        )
    ]
)


@dashboard_app.callback(
    Output("kpi-tickets", "children"),
    Output("kpi-transactions", "children"),
    Output("validated-tickets", "children"),
    Output("total-sales", "children"),
    Output("nrc-revenue", "children"),
    Output("coachtype-pie", "figure"),
    Output("summary-table", "data"),
    Input("date-filter", "value"),
    Input("date-picker", "start_date"),
    Input("date-picker", "end_date"),
)
def update_dashboard(date_filter, start_date, end_date):
    try:
        # normalize dates
        start_date = pd.to_datetime(start_date).date()
        end_date = pd.to_datetime(end_date).date()
        if date_filter and "today" in date_filter:
            start_date = end_date = datetime.today().date()

        # Fast path: aggregated booking data
        booking_agg = read_range_booking(start_date, end_date)
        booking_summary = booking_agg.get("summary", {})
        by_coach = pd.DataFrame(booking_agg.get("by_coach", []))
        by_station = pd.DataFrame(booking_agg.get("by_station", []))

        # Validator aggregated summary (validated tickets)
        validator_agg = read_range_validator(start_date, end_date)
        validated_tickets = int(validator_agg.get("summary", {}).get("transactions", 0))

        # User aggregated (for NRC revenue or other per-user metrics)
        user_agg = read_range_user(start_date, end_date)
        nrc_revenue = float(user_agg.get("summary", {}).get("nrc_tkt_rev", 0)) if user_agg.get("summary") else 0

        # KPIs
        kpi_tickets = f"{int(booking_summary.get('no_of_passengers', 0)):,}"
        kpi_transactions = f"{int(booking_summary.get('transactions', 0)):,}"
        kpi_validated = f"{validated_tickets:,}"
        total_sales = f"{int(booking_summary.get('total_fare', 0)):,}"
        nrc_rev = f"{int(nrc_revenue):,}"

        # Pie chart by coach
        pie_fig = {}
        if not by_coach.empty:
            # ensure column names match expectation
            if "total_fare" not in by_coach.columns and "value" in by_coach.columns:
                by_coach = by_coach.rename(columns={"value": "total_fare"})
            pie_fig = px.pie(by_coach, values="total_fare", names="coach_type_name", title="Sales by Coach Type")

        # Summary table: add total row (lightweight)
        if not by_station.empty:
            if "total_fare" not in by_station.columns and "value" in by_station.columns:
                by_station = by_station.rename(columns={"value": "total_fare"})
            numeric_cols = [c for c in by_station.columns if c != "booking_from"]
            for c in numeric_cols:
                by_station[c] = pd.to_numeric(by_station[c], errors="coerce").fillna(0)
            total_row = by_station[numeric_cols].sum(numeric_only=True)
            total_row["booking_from"] = "Total"
            by_station = pd.concat([by_station, pd.DataFrame([total_row])], ignore_index=True)
            summary_table = by_station.to_dict("records")
        else:
            # fallback: attempt raw chunk read (should rarely be needed)
            records = read_all_chunks("booking")
            if records:
                raw_df = pd.DataFrame(records)
                raw_df["booking_date"] = pd.to_datetime(raw_df["booking_date"]).dt.date
                raw_filtered = raw_df[(raw_df["booking_date"] >= start_date) & (raw_df["booking_date"] <= end_date)]
                by_station2 = raw_filtered.groupby("booking_from")["total_fare"].sum().reset_index()
                total_row = {"booking_from": "Total", "total_fare": by_station2["total_fare"].sum()}
                summary_table = pd.concat([by_station2, pd.DataFrame([total_row])], ignore_index=True).to_dict("records")
            else:
                summary_table = []

        return kpi_tickets, kpi_transactions, kpi_validated, total_sales, nrc_rev, pie_fig, summary_table

    except Exception as e:
        logger.exception("Callback Error in dashboard:")
        return "Err", "Err", "Err", "Err", "Err", {}, []
