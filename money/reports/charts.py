"""Plotly figure builders for the report graphs."""

import plotly.graph_objects as go
from django.conf import settings
from django.utils.translation import gettext as _


def _line_chart(dates, series):
    """Return an HTML fragment with a line chart.

    ``series`` is a list of (name, values) pairs plotted against ``dates``.
    The fragment relies on plotly.js being loaded by the page.
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
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})


def balance_chart(balances):
    """Return a chart of month-end total, cash, investment and property balances."""
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
    """Return a chart of an investment account's value against the amount paid in."""
    return _line_chart(
        [v["date"] for v in valuations],
        [
            (_("Value"), [v["value"] for v in valuations]),
            (_("Paid In"), [v["paid_in"] for v in valuations]),
        ],
    )
