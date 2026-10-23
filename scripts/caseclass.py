"""Listening classes of the case+radiator fan levels (Seb's scale for this machine at the desk) with the literature level of the 7 fans."""
import math
NAME = {800: "ultra-quiet", 1000: "very quiet", 1300: "quiet", 1600: "balanced", 1900: "loud", 2400: "between loud and very loud, a model point", 3000: "very loud"}
SHORT = {800: "ultra-quiet", 1000: "very quiet", 1300: "quiet", 1600: "balanced", 1900: "loud", 2400: "loud+", 3000: "very loud"}
L7 = lambda r: -167.1 + 60.2 * math.log10(min(r, 2920)) + 10 * math.log10(7)   # SW Pro 4 120 fit, 1 m
def label(c, short=False):
    rpm = "3000 (full speed &asymp;&nbsp;2920&nbsp;rpm)" if c == 3000 else f"{c}&nbsp;rpm"
    if short: return ("&asymp;&nbsp;2920 (full)" if c == 3000 else str(c)) + f'<br><span class="sub">{SHORT[c]}</span>'
    return f'{rpm} &middot; {NAME[c]} (&asymp;&nbsp;{L7(c):.0f}&nbsp;dBA)'
