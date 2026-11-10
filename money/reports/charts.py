"""Plotly figure builders for the report graphs.

The builders return a JSON-serialisable dict (data, layout, config) that the page
renders with plotly.js, via the template's ``json_script`` filter and ``charts.js``.
"""

import json

import plotly.graph_objects as go
from django.conf import settings
from django.utils.translation import gettext as _


def _line_chart(dates, series):
    """Return a plotly chart spec for a line chart.

    ``series`` is a list of (name, values) pairs plotted against ``dates``.
    """
    fig = go.Figure()
    for name, values in series:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[float(v) for v in values],
                name=name,
                mode="lines+markers",
            )
        )

    fig.update_layout(
        height=400,
        yaxis={
            "title": _("Balance (%(currency)s)") % {"currency": settings.BASE_CURRENCY},
            "tickformat": ",.0f",
            "hoverformat": ",.2f",
            "rangemode": "tozero",
            "showgrid": True,
            "gridcolor": "rgba(128,128,128,0.3)",
            "gridwidth": 1,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        margin={"l": 80, "r": 20, "t": 30, "b": 50},
    )
    spec = json.loads(fig.to_json())
    return {"data": spec["data"], "layout": spec["layout"], "config": {"responsive": True}}


def balance_chart(balances):
    """Return a chart spec of month-end total, cash, investment and property balances."""
    return _line_chart(
        [b["date"] for b in balances],
        [
            (_("Total"), [b["total"] for b in balances]),
            (_("Cash"), [b["cash"] for b in balances]),
            (_("Investment"), [b["invest"] for b in balances]),
            (_("Property"), [b["property"] for b in balances]),
        ],
    )


def valuation_chart(valuations):
    """Return a chart spec of an investment account's value against the amount paid in."""
    return _line_chart(
        [v["date"] for v in valuations],
        [
            (_("Value"), [v["value"] for v in valuations]),
            (_("Paid In"), [v["paid_in"] for v in valuations]),
        ],
    )
