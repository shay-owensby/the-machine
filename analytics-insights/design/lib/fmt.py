"""Number and date formatting, shared by the tiles, the tables and the charts.

One module so that a figure reads identically in the tile at the top of the
report, the table in the middle and the axis label on the chart beside it. A
KPI that says "$48.2k" in one place and "$48,210.00" in another invites the
reader to wonder whether they are the same number.
"""

import datetime

_SYMBOL = {"USD": "$", "EUR": "€", "GBP": "£", "CAD": "CA$",
           "AUD": "A$", "NZD": "NZ$", "JPY": "¥", "INR": "₹",
           "CHF": "CHF ", "SEK": "SEK ", "ZAR": "R", "MXN": "MX$", "BRL": "R$"}

NA = "not available"

# Figures below this are always shown in full.
COMPACT_FROM = 1000000


def symbol(currency):
    if not currency:
        return ""
    return _SYMBOL.get(currency.upper(), currency.upper() + " ")


def money(value, currency=None, decimals=None, compact=False):
    if value is None:
        return NA
    sym = symbol(currency)
    # Compact only at a million. Below that the exact figure fits, and a tile
    # reading "$12.9k" beside a table reading "$12,880.00" makes a reader stop
    # and check whether they are the same number.
    if compact and abs(value) >= COMPACT_FROM:
        return sym + compact_number(value)
    if decimals is None:
        decimals = 0 if abs(value) >= 1000 else 2
    return "%s%s" % (sym, ("{:,.%df}" % decimals).format(value))


def compact_number(value):
    """48,210 -> 48.2k. Only where space is the constraint and the exact figure
    is available elsewhere on the page — never in a table."""
    if value is None:
        return NA
    a = abs(value)
    for cut, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if a >= cut:
            scaled = value / cut
            return ("%.1f%s" % (scaled, suffix)).replace(".0" + suffix, suffix)
    return "{:,.0f}".format(value)


def integer(value, compact=False):
    if value is None:
        return NA
    if compact and abs(value) >= COMPACT_FROM:
        return compact_number(value)
    return "{:,.0f}".format(value)


def rate(value, decimals=2):
    """Analysis files carry rates already multiplied by 100."""
    if value is None:
        return NA
    return ("{:,.%df}%%" % decimals).format(value)


def decimal(value, decimals=None):
    """Precision follows magnitude.

    A conversion count of 490 is 490, not 490.00 -- the trailing zeros imply a
    precision the figure does not have and cost two characters of a tile. A
    ROAS of 3.46 keeps both places, because there the second one carries
    meaning.
    """
    if value is None:
        return NA
    if decimals is None:
        if float(value).is_integer():
            decimals = 0
        elif abs(value) >= 100:
            decimals = 0
        elif abs(value) >= 10:
            decimals = 1
        else:
            decimals = 2
    return ("{:,.%df}" % decimals).format(value)


def duration(value):
    """Seconds to ``m:ss``, or ``h:mm:ss`` past an hour.

    Analytics reports carry average session duration in seconds. Shown raw it
    reads as a quantity ("104.0"), which is the one thing it is not -- and the
    KPI table beside it already says 1:44.
    """
    if value is None:
        return NA
    total = int(round(float(value)))
    sign = "-" if total < 0 else ""
    total = abs(total)
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return "%s%d:%02d:%02d" % (sign, hours, minutes, seconds)
    return "%s%d:%02d" % (sign, minutes, seconds)


def by_unit(value, unit, currency=None, compact=False):
    """Format by the ``unit`` field of a KPI record."""
    if value is None:
        return NA
    if unit == "currency":
        return money(value, currency, compact=compact)
    if unit == "int":
        return integer(value, compact=compact)
    if unit == "rate":
        return rate(value)
    if unit == "decimal":
        return decimal(value)
    if unit == "duration":
        return duration(value)
    # An unrecognised unit falls back to the numeric formatter rather than to
    # str(), which would print "104.0" where the report says "1:44".
    if isinstance(value, (int, float)):
        return decimal(value)
    return str(value)


def percent_change(value, decimals=1):
    """Signed, with the sign always shown. ``None`` is undefined, not zero."""
    if value is None:
        return None
    return ("{:+,.%df}%%" % decimals).format(value)


def date(value, style="long"):
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.date(*[int(p) for p in value.split("-")[:3]])
        except (ValueError, TypeError):
            return value
    if style == "long":
        return "%s %d, %d" % (value.strftime("%b"), value.day, value.year)
    if style == "short":
        return "%s %d" % (value.strftime("%b"), value.day)
    return value.isoformat()


def date_range(start, end):
    return "%s – %s" % (date(start), date(end))
