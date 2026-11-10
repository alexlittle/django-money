"""Financial calculations."""

SECONDS_PER_YEAR = 365 * 24 * 60 * 60


def xirr(cash_flows):
    """Return the annualised internal rate of return of dated cash flows, as a fraction.

    ``cash_flows`` is a list of ``(datetime, amount)`` pairs. Money put in is
    negative and money taken out (including the final value) is positive.
    Returns None when there is no solution, e.g. all the flows have the same sign.
    """
    flows = [(when, float(amount)) for when, amount in cash_flows]
    if not any(a > 0 for _, a in flows) or not any(a < 0 for _, a in flows):
        return None

    start = min(when for when, _ in flows)
    timed = [((when - start).total_seconds() / SECONDS_PER_YEAR, amount) for when, amount in flows]

    def npv(rate):
        return sum(amount / (1 + rate) ** t for t, amount in timed)

    low, high = -0.9999, 1.0
    f_low, f_high = npv(low), npv(high)
    while f_low * f_high > 0 and high < 1e6:
        high *= 2
        f_high = npv(high)
    if f_low * f_high > 0:
        return None

    for _ in range(200):
        mid = (low + high) / 2
        f_mid = npv(mid)
        if f_low * f_mid <= 0:
            high = mid
        else:
            low, f_low = mid, f_mid
    return (low + high) / 2
