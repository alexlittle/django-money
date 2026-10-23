"""Month-end balances for the summary graph, calculated from a handful of queries.

The rows are loaded once and each month's figure is worked out in Python. A month
includes everything dated before the start of the following month.
"""

from bisect import bisect_left
from collections import defaultdict

from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from money.models import ExchangeRate, Transaction, Valuation


def _latest_rates_by_pair():
    """Return {(from_cur, to_cur): ([dates], [rates])}, ordered by (date, id)."""
    rows = ExchangeRate.objects.order_by("date", "id").values_list(
        "from_cur", "to_cur", "date", "rate"
    )
    by_pair = defaultdict(lambda: ([], []))
    for from_cur, to_cur, date, rate in rows:
        dates, rates = by_pair[(from_cur, to_cur)]
        dates.append(date)
        rates.append(rate)
    return by_pair


def _rate_before(by_pair, from_cur, to_cur, boundary):
    """Latest stored rate for the pair dated before ``boundary``, or None."""
    dates, rates = by_pair.get((from_cur, to_cur), ([], []))
    idx = bisect_left(dates, boundary)
    return rates[idx - 1] if idx else None


def _base_rate(by_pair, currency, boundary):
    """Rate used to convert ``currency`` into the base currency (as ExchangeRate.at_date)."""
    rate = _rate_before(by_pair, settings.BASE_CURRENCY, currency, boundary)
    if rate is not None:
        return rate
    inverse = _rate_before(by_pair, currency, settings.BASE_CURRENCY, boundary)
    if inverse is not None:
        return 1 / inverse
    return 1


def _monthly_net_by_account(cash_accounts, tz, last_boundary):
    """Return {account_id: [(month_start, credit - debit), ...]} oldest first."""
    rows = (
        Transaction.objects.filter(account__in=cash_accounts, date__lt=last_boundary)
        .annotate(month=TruncMonth("date", tzinfo=tz))
        .values("account_id", "month")
        .annotate(credit=Sum("credit"), debit=Sum("debit"))
        .order_by("account_id", "month")
    )
    by_account = defaultdict(list)
    for row in rows:
        by_account[row["account_id"]].append((row["month"], row["credit"] - row["debit"]))
    return by_account


def _valuations_by_account(accounts):
    """Return {account_id: ([dates], [values])}, ordered by (date, id)."""
    rows = (
        Valuation.objects.filter(account__in=accounts)
        .order_by("date", "id")
        .values_list("account_id", "date", "value")
    )
    by_account = defaultdict(lambda: ([], []))
    for account_id, date, value in rows:
        dates, values = by_account[account_id]
        dates.append(date)
        values.append(value)
    return by_account


def _valuation_total(accounts, valuations, by_pair, boundary):
    total = 0
    for acc in accounts:
        dates, values = valuations.get(acc.id, ([], []))
        idx = bisect_left(dates, boundary.date())
        if not idx:
            continue
        value = values[idx - 1]
        if acc.currency == settings.BASE_CURRENCY:
            total += value
        else:
            total += value / _base_rate(by_pair, acc.currency, boundary)
    return total


def monthly_balances(month_ends, tz, cash_accounts, invest_accounts, property_accounts):
    """Return one dict of cash, invest, property and total per month.

    ``month_ends`` is a list of ``(last_day, boundary)`` pairs, oldest first, where
    ``boundary`` is the start of the following month. ``last_day`` is reported as
    each entry's ``date``.
    """
    by_pair = _latest_rates_by_pair()
    net_by_account = _monthly_net_by_account(cash_accounts, tz, month_ends[-1][1])
    valuations = _valuations_by_account([*invest_accounts, *property_accounts])

    running = {acc.id: 0 for acc in cash_accounts}
    position = dict.fromkeys(running, 0)

    balances = []
    for last_day, boundary in month_ends:
        cash_total = 0
        for acc in cash_accounts:
            months = net_by_account.get(acc.id, [])
            while position[acc.id] < len(months) and months[position[acc.id]][0] < boundary:
                running[acc.id] += months[position[acc.id]][1]
                position[acc.id] += 1

            balance = running[acc.id]
            if not balance:
                continue
            if acc.currency == settings.BASE_CURRENCY:
                cash_total += balance
            else:
                cash_total += balance / _base_rate(by_pair, acc.currency, boundary)

        invest_total = _valuation_total(invest_accounts, valuations, by_pair, boundary)
        property_total = _valuation_total(property_accounts, valuations, by_pair, boundary)

        balances.append(
            {
                "date": last_day,
                "total": cash_total + invest_total + property_total,
                "cash": cash_total,
                "invest": invest_total,
                "property": property_total,
            }
        )
    return balances
