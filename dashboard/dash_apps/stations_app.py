# stations_app.py
import logging
from datetime import datetime

import numpy as np
import pandas as pd
from dash import html, dcc, Output, Input, dash_table
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

from dashboard.utils import read_range_booking, read_all_chunks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

end_date = datetime.today().date()

station_app = DjangoDash(
    "Station",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    add_bootstrap_links=True,
)

station_app.layout = html.Div(
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
                        ), xs=12, className="p-3"),
                        dbc.Col(dcc.Dropdown(id="route-name", options=[{"label": "LITS", "value": "LITS"}, {"label": "BAT", "value": "BAT"}], value=None, placeholder="Route Name", className="rounded"), xs=6, className="p-3"),
                        dbc.Col(dcc.Dropdown(id="coach-type", options=[{"label": "First Class", "value": "First Class"}, {"label": "Business Class", "value": "Business Class"}, {"label": "Standard Class", "value": "Standard Class"}], value=None, placeholder="Coach Type", className="rounded"), xs=6, className="p-3"),
                    ],
                    justify="center",
                    className="bg-white shadow rounded",
                ),
                # Group / Class / Sales tables (similar layout)
                dbc.Row(
                    [
                        dbc.Col(html.Div([html.H5("Group Booking", className="bg-success text-white text-center rounded m-0"), dash_table.DataTable(id="group-table", columns=[
                            {"id": "poc_corporation_name", "name": "Corporate Name"},
                            {"id": "total_fare", "name": "Total Sales"},
                            {"id": "medical", "name": "Medical"},
                            {"id": "insurance", "name": "Insurance"},
                            {"id": "stamp_duty", "name": "Stamp Duty"},
                            {"id": "nrc_tkt_rev", "name": "NRC Ticket Revenue"},
                            {"id": "gsd_tkt_rev", "name": "GSD Ticket Revenue"},
                            {"id": "icrc_tkt_rev", "name": "ICRC Ticket Revenue"},
                            {"id": "no_of_passengers", "name": "No of Passengers"},
                        ], style_table={"height": "300px", "overflowY": "auto"}, filter_action="native", sort_action="native")], className="bg-white shadow rounded border p-2"), xs=12, lg=6),
                        dbc.Col(html.Div([html.H5("Ticket Count By Class", className="bg-success text-white text-center rounded m-0"), dash_table.DataTable(id="class-table", columns=[
                            {"id": "booking_from", "name": "Station Name"},
                            {"id": "first_class", "name": "First Class"},
                            {"id": "business_class", "name": "Business Class"},
                            {"id": "standard_class", "name": "Standard Class"},
                        ], style_table={"height": "300px", "overflowY": "auto"}, filter_action="native", sort_action="native")], className="bg-white shadow rounded border p-2"), xs=12, lg=6),
                    ],
                    className="mt-4 mb-4",
                ),
                dbc.Row(
                    [
                        dbc.Col(html.Div([html.H5("Sales Table", className="bg-success text-white text-center rounded m-0"), dash_table.DataTable(id="sales-table", columns=[
                            {"id": "booking_date", "name": "Date"},
                            {"id": "tickets_sold", "name": "Tickets Sold"},
                            {"id": "online_transaction", "name": "Online Transaction"},
                            {"id": "tom_transaction", "name": "Tom Transaction"},
                            {"id": "total_no_of_transaction", "name": "Total Transaction"},
                            {"id": "online_sales", "name": "Online Sales"},
                            {"id": "tom_sales", "name": "Tom Sales"},
                            {"id": "total_sales", "name": "Total Sales"},
                        ], style_table={"overflowY": "scroll"}, filter_action="native", sort_action="native")], className="bg-white shadow rounded border p-2"), xs=12, lg=12),
                    ],
                    className="mb-3",
                ),
            ],
            fluid=True,
        )
    ]
)


def map_route(series):
    conditions = [
        series.isin(["Lagos-Ibadan", "Ibadan-Lagos", "LAGOS-IBADAN_LITS", "Lagos-Ibadan_Afternoon", "Ibadan-Lagos_Afternoon"]),
        series.isin(["APAPA-KAJOLA", "KAJOLA-APAPA", "KAJOLA-APAPA_BAT"]),
    ]
    choices = ["LITS", "BAT"]
    return np.select(conditions, choices, default="Other")


@station_app.callback(
    Output("group-table", "data"),
    Output("class-table", "data"),
    Output("sales-table", "data"),
    Input("date-filter", "value"),
    Input("date-picker", "start_date"),
    Input("date-picker", "end_date"),
    Input("boarding-station", "value"),
    Input("route-name", "value"),
    Input("coach-type", "value"),
)
def update_station(date_filter, start_date, end_date, station, route, coach):
    try:
        start_date = pd.to_datetime(start_date).date()
        end_date = pd.to_datetime(end_date).date()
        if date_filter and "today" in date_filter:
            start_date = end_date = datetime.today().date()

        booking_agg = read_range_booking(start_date, end_date)
        # try to serve from aggregates
        by_corp = pd.DataFrame(booking_agg.get("by_corporation", []))
        by_station = pd.DataFrame(booking_agg.get("by_station", []))
        daily_trend = pd.DataFrame(booking_agg.get("daily_trend", []))

        can_serve = True
        # If route or coach filter present we need row-level data (fallback)
        if route or coach:
            can_serve = False

        if can_serve:
            # group table
            if not by_corp.empty:
                numeric_cols = [c for c in by_corp.columns if c != "poc_corporation_name"]
                for c in numeric_cols:
                    by_corp[c] = pd.to_numeric(by_corp[c], errors="coerce").fillna(0)
                total_row = by_corp[numeric_cols].sum(numeric_only=True)
                total_row["poc_corporation_name"] = "Total"
                by_corp = pd.concat([by_corp, pd.DataFrame([total_row])], ignore_index=True)
                group_records = by_corp.to_dict("records")
            else:
                group_records = []

            # class table - if `class_by_station` pre-aggregate exists use it
            class_records = booking_agg.get("class_by_station", [])
            if class_records:
                class_df = pd.DataFrame(class_records)
                numeric_cols = [c for c in class_df.columns if c != "booking_from"]
                for c in numeric_cols:
                    class_df[c] = pd.to_numeric(class_df[c], errors="coerce").fillna(0)
                total_row = class_df[numeric_cols].sum(numeric_only=True)
                total_row["booking_from"] = "Total"
                class_df = pd.concat([class_df, pd.DataFrame([total_row])], ignore_index=True)
                class_records = class_df.to_dict("records")
            else:
                class_records = []

            # sales table from daily_trend
            if not daily_trend.empty:
                daily_trend["booking_date"] = pd.to_datetime(daily_trend["booking_date"]).dt.date
                daily_trend = daily_trend.sort_values("booking_date")
                daily_trend = daily_trend.rename(columns={"total_fare": "total_sales"}) if "total_fare" in daily_trend.columns else daily_trend
                total_row = {c: daily_trend[c].sum() for c in daily_trend.columns if c != "booking_date"}
                total_row["booking_date"] = "Total"
                daily_trend = pd.concat([daily_trend, pd.DataFrame([total_row])], ignore_index=True)
                sales_records = daily_trend[["booking_date", "total_sales"]].to_dict("records")
            else:
                sales_records = []

            return group_records, class_records, sales_records

        # Fallback path: raw chunk processing (when filters require row-level)
        records = read_all_chunks("booking")
        if not records:
            return [], [], []
        raw_df = pd.DataFrame(records)
        raw_df["booking_date"] = pd.to_datetime(raw_df["booking_date"]).dt.date
        raw_df = raw_df[(raw_df["booking_date"] >= start_date) & (raw_df["booking_date"] <= end_date)]
        if station:
            raw_df = raw_df[raw_df["booking_from"] == station]
        if "route_name" in raw_df.columns:
            raw_df["filtered_route"] = map_route(raw_df["route_name"])
            if route:
                raw_df = raw_df[raw_df["filtered_route"] == route]
        if coach:
            raw_df = raw_df[raw_df["coach_type_name"] == coach]

        # group table
        group_table_dff = raw_df.groupby(["poc_corporation_name"]).agg(
            total_fare=("total_fare", "sum"),
            medical=("medical", "sum"),
            insurance=("insurance", "sum"),
            stamp_duty=("stamp_duty", "sum"),
            nrc_tkt_rev=("nrc_tkt_rev", "sum"),
            gsd_tkt_rev=("gsd_tkt_rev", "sum"),
            icrc_tkt_rev=("icrc_tkt_rev", "sum"),
            no_of_passengers=("no_of_passengers", "sum"),
        ).reset_index()
        if not group_table_dff.empty:
            total_row = group_table_dff.drop(columns=["poc_corporation_name"]).sum()
            total_row["poc_corporation_name"] = "Total"
            group_table_dff = pd.concat([group_table_dff, pd.DataFrame([total_row])], ignore_index=True)
        group_records = group_table_dff.to_dict("records")

        # class table
        class_table_dff = raw_df.groupby("booking_from").agg(
            first_class=("coach_type_name", lambda x: (x == "First Class").sum()),
            business_class=("coach_type_name", lambda x: (x == "Business Class").sum()),
            standard_class=("coach_type_name", lambda x: (x == "Standard Class").sum()),
        ).reset_index()
        if not class_table_dff.empty:
            total_row = class_table_dff.drop(columns=["booking_from"]).sum()
            total_row["booking_from"] = "Total"
            class_table_dff = pd.concat([class_table_dff, pd.DataFrame([total_row])], ignore_index=True)
        class_records = class_table_dff.to_dict("records")

        # sales table (with online/offline splits if 'type' column exists)
        if "type" in raw_df.columns:
            sales_table_dff = raw_df.groupby("booking_date").agg(
                tickets_sold=("no_of_passengers", "count"),
                online_transaction=("total_fare", lambda x: (raw_df.loc[x.index, "type"] == "ONLINE").sum()),
                tom_transaction=("total_fare", lambda x: (raw_df.loc[x.index, "type"] == "OFFLINE").sum()),
                total_no_of_transaction=("total_fare", "count"),
                online_sales=("total_fare", lambda x: raw_df.loc[x.index[raw_df.loc[x.index, "type"] == "ONLINE"], "total_fare"].sum()),
                tom_sales=("total_fare", lambda x: raw_df.loc[x.index[raw_df.loc[x.index, "type"] == "OFFLINE"], "total_fare"].sum()),
                total_sales=("total_fare", "sum"),
            ).reset_index()
        else:
            sales_table_dff = raw_df.groupby("booking_date").agg(total_sales=("total_fare", "sum")).reset_index()
        if not sales_table_dff.empty:
            total_row = sales_table_dff.drop(columns=["booking_date"]).sum(numeric_only=True)
            total_row["booking_date"] = "Total"
            sales_table_dff = pd.concat([sales_table_dff, pd.DataFrame([total_row])], ignore_index=True)
        sales_records = sales_table_dff.to_dict("records")

        return group_records, class_records, sales_records

    except Exception as e:
        logger.exception("Callback Error in station_app.update_station:")
        return [], [], []
