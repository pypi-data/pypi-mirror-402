
###########################################################################
#
# LICENSE AGREEMENT
#
# Copyright (c) 2014-2024 joonis new media, Thimo Kraemer
#
# 1. Recitals
#
# joonis new media, Inh. Thimo Kraemer ("Licensor"), provides you
# ("Licensee") the program "PyFinTech" and associated documentation files
# (collectively, the "Software"). The Software is protected by German
# copyright laws and international treaties.
#
# 2. Public License
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this Software, to install and use the Software, copy, publish
# and distribute copies of the Software at any time, provided that this
# License Agreement is included in all copies or substantial portions of
# the Software, subject to the terms and conditions hereinafter set forth.
#
# 3. Temporary Multi-User/Multi-CPU License
#
# Licensor hereby grants to Licensee a temporary, non-exclusive license to
# install and use this Software according to the purpose agreed on up to
# an unlimited number of computers in its possession, subject to the terms
# and conditions hereinafter set forth. As consideration for this temporary
# license to use the Software granted to Licensee herein, Licensee shall
# pay to Licensor the agreed license fee.
#
# 4. Restrictions
#
# You may not use this Software in a way other than allowed in this
# license. You may not:
#
# - modify or adapt the Software or merge it into another program,
# - reverse engineer, disassemble, decompile or make any attempt to
#   discover the source code of the Software,
# - sublicense, rent, lease or lend any portion of the Software,
# - publish or distribute the associated license keycode.
#
# 5. Warranty and Remedy
#
# To the extent permitted by law, THE SOFTWARE IS PROVIDED "AS IS",
# WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF QUALITY, TITLE, NONINFRINGEMENT,
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE, regardless of
# whether Licensor knows or had reason to know of Licensee particular
# needs. No employee, agent, or distributor of Licensor is authorized
# to modify this warranty, nor to make any additional warranties.
#
# IN NO EVENT WILL LICENSOR BE LIABLE TO LICENSEE FOR ANY DAMAGES,
# INCLUDING ANY LOST PROFITS, LOST SAVINGS, OR OTHER INCIDENTAL OR
# CONSEQUENTIAL DAMAGES ARISING FROM THE USE OR THE INABILITY TO USE THE
# SOFTWARE, EVEN IF LICENSOR OR AN AUTHORIZED DEALER OR DISTRIBUTOR HAS
# BEEN ADVISED OF THE POSSIBILITY OF THESE DAMAGES, OR FOR ANY CLAIM BY
# ANY OTHER PARTY. This does not apply if liability is mandatory due to
# intent or gross negligence.


"""
SWIFT module of the Python Fintech package.

This module defines functions to parse SWIFT messages.
"""

__all__ = ['parse_mt940', 'SWIFTParserError']

def parse_mt940(data):
    """
    Parses a SWIFT message of type MT940 or MT942.

    It returns a list of bank account statements which are represented
    as usual dictionaries. Also all SEPA fields are extracted. All
    values are converted to unicode strings.

    A dictionary has the following structure:

    - order_reference: string (Auftragssreferenz)
    - reference: string or ``None`` (Bezugsreferenz)
    - bankcode: string (Bankleitzahl)
    - account: string (Kontonummer)
    - number: string (Auszugsnummer)
    - balance_open: dict (Anfangssaldo)
        - amount: Decimal (Betrag)
        - currency: string (Währung)
        - date: date (Buchungsdatum)
    - balance_close: dict (Endsaldo)
        - amount: Decimal (Betrag)
        - currency: string (Währung)
        - date: date (Buchungsdatum)
    - balance_booked: dict or ``None`` (Valutensaldo gebucht)
        - amount: Decimal (Betrag)
        - currency: string (Währung)
        - date: date (Buchungsdatum)
    - balance_noted: dict or ``None`` (Valutensaldo vorgemerkt)
        - amount: Decimal (Betrag)
        - currency: string (Währung)
        - date: date (Buchungsdatum)
    - sum_credits: dict or ``None`` (Summe Gutschriften / MT942 only)
        - amount: Decimal (Betrag)
        - currency: string (Währung)
        - count: int (Anzahl Buchungen)
    - sum_debits: dict or ``None`` (Summe Belastungen / MT942 only)
        - amount: Decimal (Betrag)
        - currency: string (Währung)
        - count: int (Anzahl Buchungen)
    - transactions: list of dictionaries (Auszugsposten)
        - description: string or ``None`` (Beschreibung)
        - valuta: date (Wertstellungsdatum)
        - date: date or ``None`` (Buchungsdatum)
        - amount: Decimal (Betrag)
        - reversal: bool (Rückbuchung)
        - booking_key: string (Buchungsschlüssel)
        - booking_text: string or ``None`` (Buchungstext)
        - reference: string (Kundenreferenz)
        - bank_reference: string or ``None`` (Bankreferenz)
        - gvcode: string (Geschäftsvorfallcode)
        - primanota: string or ``None`` (Primanoten-Nr.)
        - bankcode: string or ``None`` (Bankleitzahl)
        - account: string or ``None`` (Kontonummer)
        - iban: string or ``None`` (IBAN)
        - amount_original: dict or ``None`` (Originalbetrag in Fremdwährung)
            - amount: Decimal (Betrag)
            - currency: string (Währung)
        - charges: dict or ``None`` (Gebühren)
            - amount: Decimal (Betrag)
            - currency: string (Währung)
        - textkey: int or ``None`` (Textschlüssel)
        - name: list of strings (Name)
        - purpose: list of strings (Verwendungszweck)
        - sepa: dictionary of SEPA fields
        - [nn]: Unknown structured fields are added with their numeric ids.

    :param data: The SWIFT message.
    :returns: A list of dictionaries.
    """
    ...


class SWIFTParserError(Exception):
    """SWIFT parser returned an error."""
    ...



from typing import TYPE_CHECKING
if not TYPE_CHECKING:
    import marshal, zlib, base64
    exec(marshal.loads(zlib.decompress(base64.b64decode(
        b'eJzdvQlcVEe2MH5vL+yr7Hsja9N0szQgmwIqyI6I4hpZG0FWexF3caURUUTUBlHbvVXUBlFxx6rEcTKZpJv0jD1kkpDlZZLMZIZkzIzZv6q6qJCYvPf+v3nzvu8P16K6'
        b'qk7VqbPXvee2H1ATftjjf/++ExWHqHJqCbWCWkKX09upJSwJW82hXvBTzjpDU9QF+ulnqVU5m0VJuGdQ/cKzUaspmdVSFmo3KedMHr+VRq2mkh/NQlPl3ALKfDvf5GuJ'
        b'RcHCjLT5vNr6ckWNhFdfwZNXSnhz18or6+t4aVV1cklZJa+hpKy6ZIVEZGExv7JK9nRsuaSiqk4i41Uo6srkVfV1Mp68Hg2VyiS88TklMhkCk4ksynwm7ImH/lliQoyh'
        b'oplqpptZzexmTjO32aTZtNms2bzZotmy2arZutmm2bbZrtm+eUqzQ7Njs1Ozc7NLs2uzW7N7s0ezZ7NXs3ezzyFK6a10U05RmilNle5KayVHaau0UDoorZTmShclpWQr'
        b'7ZSOSq7SRumhdFVaKj2VzkoTpZOSpaSVXkofpX0FD7HAbCOPRbV4TybrRl9zikVt4E1uRS2+k1toahNvk28B5fezfY3UGvZiqpFGJGfllk1ksD3654CJYTIuFQUU3zS3'
        b'xgx9MktgUctSLFCtOHssNIhSBKBqqA3QwlbYkpedD5USsBe25fFhW8aCuUITKiiVA+/Bg0DDpxUeaCw4WA2uyTJy4B64OwfupimLjBnwFAtoq/zK6Ak4THmKgwoVB+yb'
        b'ER6IbBQiJReRyhSR1hyR1BKR1BqR0RYR1B4R3KFiCiEckrCWH8njRhYhHP0TwrF+Qhx6E2uccC/se0a4yv8K4XIYwv0l3ISyQvRLExZbDSSnUKTRoZ5FIRXjtVHFofPC'
        b'VjGN3cvMKDuKcv2suji0xpRmGjclcCn0d1FAdnFor2gqdY6qwUxoXu/GeTyFSh5zWEtrQ69FZIQq6Rpz1OEf0kVrTSleeNXVyD9GimQNFGlmUV/YdtrSwWOUzPP7Rbkp'
        b'ttQIpQhDHbAJbgcDiImtYfnBwXBXWLoQ7gLn5gdn5sC9oaIM4XqwPzOHpupszadHwBOTWMV5uut1mFVswirMJqqC/YwZ7P9xZqz4MTNMX8AMS4YZrlm21Mu2MygqvDj7'
        b'PcdFlCIcNUbAu2AHosBuQRbcDVuy89MzQjMWUJFZBU6gE14Hd+eDVnCAWsE1hcfAbXhQ4Yjp1pW3WAyuc0BvLJLtc9SqHHhD4YQ6+BvgHjEY4IjAXdRxhKqGO2En6RGt'
        b'ha3iSApcgp1YHagy2A3uKrDoVNMRcD8XjXC1oURgEHYRZLfYWlKOEiFF2RXXfCopZeShY/kU6mWPXFQr3jBaFU1VwTdeYcnWoM+n3647/GrikS0tx/f37V/r5seGK3k7'
        b'mxwf1FTYveQ/n+XC3hWpiFzYFxGuPl/L+jS35PUK+sKKzBJ+cXbJRYmmhDrP3SWPeMXjrFaYHMmmm266zjMu7fLfl2oscNXPdi2IbU8d1i8becVKnuRw85ttbrFvUoIt'
        b'7q/2N/BZj73Q8mAL1MRbIgrazuPnKIQhSJRYlBNo5piVgd7H2ALATnAZ3oWtfHgW7oJ74W42xYmjQd9a0M/njLCC+VJrNOp5IcPyxWtqavraObFCWr9OUserYHyASNZY'
        b'VSGfMWJBDHxReYlcsm5CnYWBm1HxpIkam01Tdg5KWXt0y7rd61T5uzYrN7/tzNP5xg8u0PvO1DvPMjjP0tnNMjp7qMo7anTOArVc5yzWyJVzjI4eKsm+PGWq0dHlUHpH'
        b'ukqinqnOV8/sqdI4aVZp7TWyXnftgsGIwfxB8cASnVey3jHF4JiCxjvw2qernfQOQQaHIJ1V0N+xVEqxWPJNRrirS2oUkhHToiKpoq6oaMSyqKisRlJSp2hALT8iABbg'
        b'Yh4mgdQGN9qiYuJG/fCgBrxRvNNZNE07jFG/VIzauCirWqp3VzdZjrG4tKPRcopyWkvc7rhRjm1T1pac7TlNOUYzW6OZg9LyyRiX4tpNbm3KY35lWBQPmAuoCzZx7LQy'
        b'1ouMwgY8hIVdKjEL9DOzwHqBjWabv0DRUQv7J6rP2sQeNwsv7Pt55/YMsQlmwSRXgSwulbXMAe5Hls1mlpASwj3FRMPnIS8F96NACQ7Ak2FUGDgNmxTYO8GroA2oiMJO'
        b'NRNRIi9J1elT9RxZMupbsWkTVsLj+6todkw7UIGB3S1bSqIdsk+1ntvfp4zecWP/OYvXyko/5oTyP13+wGw+NCtweG2oy4YaSbAMFbnw6cfuWJk6ZsDzgswkTyFUZmTn'
        b'cilL0MeCR8D5cj77x0KCQ7mnEjJiyQhHRU19iXzdxA9EJ2LHdWI+TTm5H8rpyFH7qWV6R4HBUYCk1tYRyYi1v9EViX2XZTvX6ODePk0VvW9G5wydla/U7rkQS7HRGuGW'
        b'S0qr5FJMEqnDCwSXSC4juC5YcCeiI8CjVhHJxQgVINF1xxL688W/VHQPmodSvTbxbGJS59s60DWzqznU3KFalffpZIUzakxaD+/J5DHhaXAbh2KVUvAMaAGHyPj9BU60'
        b'lULKocKHao2ZhgQyHlx3ScXj4Y11NMWSUPAcbAb3yPiF3i50ctFGDtWA5s//1lqBqQHuzoU3CEAfvMOmWCsoeMEbbiMA39S70R/TzUhghzYuSvh+PRHHDNi1RiafFr4R'
        b'XkII1VHw/IolZPSTcnfaMGcXh0oe2mi0/10U8TUzEsA9PDoMbmFRrHo0+Tywnwx/K86TppIPcigemtxyapHCDYt0RwNsksGB6HConYvwB9soeAW0AzUBKS3ypoMLuzhU'
        b'8dBGVcC7aQpXvIHtjuYEAmwHB7kIZDtSFNDrTCAKfX1pqh6dIuwQRHJ1HCER7FwDm2XS6HBPeJAmSPUuAH1k/L6SqbRu4wXMgo2L4jrryApBKH48BK8oIsJhexXaM/LB'
        b'CKm9HIaotf703IwrmAkbVRtAPoFYIIU7CEAg6EHbRj4W6e51uItA5NoF0k8c72E2bFw092E9oRO8CLtAn0wmDs+Yi5bYTMFLFevI8JeT+bTK5xXMBJmrz/qXyALR8A44'
        b'QFYAJ5ciroFuCg7CszICMZgdQn/LeQ1B3JcZU2+aED7TS5FjJHvoTzZFAIcpeGMO7CAAy9ihtMZejzknUy18ICYA8BpQw2PwiszKwtoUbQJepaNgdzYBCJodRm+YZUQA'
        b'92WuLIunZIU3/CylMeGr4G1MpTMUvF5eRcZ/4hBOx0Z/iHktU0kKaMJrO8TX7ZawD3GuGd5EECgYZ4OrsJmAvJksptds/BSBoE2YpFQpsGZDTeVSS4vI8Mg0xDfEPPP1'
        b'SUQmHWYvtYTXIsL5iXiaHcjBwHOMPG0Fh8AJGbzSaAOOrsO7OE4LwEHQy/S20ajT3BpqwSk4iKe8R8eAfrid7GcWvAOPW65SwGsFqcgHwD46YCk4yCjZsVK4W2YplcOz'
        b'UzGYivY2hScZcbwNB/1lcnjdErSY4r42tOBucIjgDy7LXWU21hZwTxqLYnPp6cU2zL52KRSo3UYBztEU25xODrNgSHp2HdiKOlZFwD14Z4O0yBb0MShcATfDLa0bwG7Y'
        b'H8Ch2H50MugoYzjXiSLnLizggY5IIRqwcB2EaiJnSwvZSNmjgKbBhGJVYOtwBirJhDGgFxzCAgiaZVxG8/rTKEInExSct8mQgbhiGwHuYSpeQrKwBR4hByp4G2pAqwxe'
        b'Q91IL+7i/vO0GB4APXxbwstf1UfR3+Z8jvVWtkh825E0+jlMozWrvkGN92WLisNjSOPhqjh6NJLiIn2VuQbwg0mj5eYE+mO+JWpEI+vvbmD0zn86zfOawkWaKjNK9eak'
        b'cXNkEi0vdUeNSGgqVyWTRtMlyXTTKh4XaahskblzPmmUSWfRnqIw1Hhfplofu5k0vuSTig4xYi7STJlrBCuaNL4aN4d2DIxDjWjOmCmFpPF9mwy6yW8O8rxD1YuKIsNJ'
        b'43qTbLo9fi4XqVG1yq15MYO8Xx59yrcINd6vViX7MPqTsGEu3RAm4SJ9qDbmtohJ46xZ82jVlFrUeL/addHWBiLZyWBPjczSwiYfnECSYUUnw+4UwkgxuAEPWkptrGPA'
        b'CSRL9vR0eGQTkUATuL0eXoHXG2VgP+xlE6kWLAb7CFhyQyPSBmQvLSyxcHbSU6GqnM+YsncsH9CxWbGmaKeNqowcxvx84/6Q3pCchvztUL0qfDZzfMle8SrtWpaLGu/X'
        b'G5f6MlxeHfhb+qHbAlO0/fpFyx9WTjqimT8NevB9ngPm46dpfEh7fpKmKsyfHddM/v3HNTvqp3FZUq7CG3N2I1KOVrA/LQ/uQQeGlowcEWxBxwrnYk5Q1Bqy+wJkXThW'
        b'/ii8Ka5hrU1jDklCc3PKjrfEFMUgoa+uiqGYGxC98DTYkxWWBffkASXclYEO1nA7a20SuEAU0dm5GCn3ANgKm9DxjaIXI4jY2YyqqTYCtSAYHWqUYblIwbZwKasVbFtw'
        b'HGwhEWEpvDYXIF9EuYKmeCoedKyXYjQILmkWHMrMMYpNJRdbTZtbxzRejDWhrObXo+NNcajSXUQRmfNbBJViuA/uxIdS0EGV2ICzChzizwiF2ixyZNqL755kgb1hGeAi'
        b'3BMTTFM8OdcmBlxhAtMr7ivFoD8pCsN3UqUuJYSKxfCuuQAd7cl9F3TOz+BQcAe46sBnw91zq8gBFG6PWCCuto+kmINpyDJCkTpwG/SL4R7QB/o52PpSNZnIEpPw5QTY'
        b'D+6J4TlwRIw/HqVWgLvwAmNtleCKjzjJXowYCo5TK0HTXLK/DWAvvCYG3bAnBo9SUeU2hQRBcBIeBteyMjF2uYg7iDM2yHaebGDHghNrmOP2XXB2vRg028VgRLooCWz2'
        b'UHgRd4lg72ZlI7gw2CZAU12lKcslyFSuBKf5LAJsFwaOiuEF2BKDxAS57Aq4y4qx/5cLYYvYAVyMwagepla8NIvsLikS3IKtGXAAHWdzuBTHG/kreNuLEDlnXbK4EkEg'
        b'LQM9VCXsYxFbDTo85ggQV4JhSy646DifQ1lNRxIyuJlgwBNsFMchp3gNj1RTNUjMThOwSLALnoStiK2D2Zn4RMyGd2lw2C1RkYfxay0HO2TZGRk5+VD5/P5EsIgfkiPi'
        b'C1nwSqQFOC0BZ1B0eio4GJxzFvBBJzwlcASdzk7wlAs4y6LALkc7FFJshz01T3744Qf/QiSP4TtNkDxmP8hNpwins6eBSwJwHu7OFaZzKE4yDc6ngnt8R2K7ZK5c2Xx4'
        b'0lqqwEbtKO2HPNIxAjYd7PGEVxzcbJiuazQfne/PjIeH4BRixhXYFTsOeJcW5EHGj8Mm/xkycAF2IkDGHPrAi8sIpZyrYKtsIWxdpbDAcegtmjczhkzYCI8i51oyF15r'
        b'hANcErX4opD8IrNa78Yw5ANbQQ/qtKZJ1BBpD6+RKfOzfCxXgNM2lmAvsthL6KVQG8z48hZXeE2GJO2c3KIRh053aM8CNyIBBbHIHYOz4ATqwYttoXnI8W4hfWbw6nR4'
        b'ZRnQyKVwAAeBd2kPHANgRELnYJfcD3aBi3ITikZ6gXT2Gmxngs1DoHueJdw738zagqLY0+j0atBEMFkO22IR/k0CxSorjH03HQTOFhAgcA42OVsiYp6wsULWnJ1AZ6zL'
        b'H49SwGVwHJG4xdxWaoO2ZkNPKxISoMaoYDTdfrDNFvZbo56pdEpgFqOEftPQvhavIuuAa7Q3uBHBIHcNabosh2XBcKsDbViTSHrqsHZaoljkMOljT6HDZXVEF1IdwWW4'
        b'H+lOoHUoFYoi4duMLlzIBKdBqy2S7XMWq1bTFAcFLqDNbxWZztQUXLBMhJeebQeJSichLC8R3ETb6QTHnwuUD7xFoNyjgmVyoH6OHbJN95iw6xbUojD/ysyo54K2HJxk'
        b'iHcXBezXZHzhc0Gr2cznEDhnsMUSXonJnMBFeBqF6phKrgnxiIvy3Gc8BFuKFZ7ExIJjkaAVXl8OTyFvrkDGAdykUYjfBi8ye7/lJAWtjfA2CoytQAtSJqikQVeRLZ+d'
        b'm0vWdYVHUW8QOD9BIAfALsLSmUvhoAxoQddzsbMGg6TLBunLFpkIap7LKtw/nW9DOu3B3nxL2OJsYQ77EYfi6Tkosj5OulzQAWefDF6wGqfpQdpXAi4zRrUzOEy21GOC'
        b'Yl9dSjoWzAE7LeEOSzPCbwtaBJqWENx9wXlwFl5hw9NWDNAlOigH7iELRfO4WIRtFVZS3HOaDoIq2MKw6KptrgxFzEds4DU55sMx2h8q2Qp34lvRMe+UDLnebnjN0hxH'
        b'/P10DLwE9jOgx8Edd8tKcFAKr8KrHMJe0XxfYr6DwhALA2c+06Y8tC8iyjvBEdoyATH/qvkqE4odRMdNW0l65sId9Zbw6FrcgeK6YDreHB5mziTXwNHlMnhnI2hrgNco'
        b'sjU+OhWdIXDesXCXbEkRvNZgi+J32EIHAmRD8E0MAby3HMnDfrB3NRLcNqz4MUhlD3iAfejwuh8eXEhTfss5TnCfK+NyTsKbcBvcb4r94flwKnxpEDH1XLgdnYD2I5hD'
        b'QDl5KnSuOATb0RL96G8nko7rQFWEmtvR0GZzeB61asCFypXI1N8AanPQ5Qu1zJ4uga3ZMtCHNOQ5ZYEWNhPKuoP+DZZgW+hEwgrBBeQzCd37arF+9MATz4kI25lj32J4'
        b'BPZYmrg8p2JNqGIWo9rtlrAtC7nB9BwR8VoC2JaTKZwHlXkFwaKcTNiaDc8EwbYMfmE6CkXmYdWVLaRkThTYmWs3ozqFLFC5BhwAV+aZmcxlUbQDtREhMUjiFLlNQAH2'
        b'4WfAVj/KD7YUEFylvqAJYvk5P0GXqViisLkoGmnCClsFzk1S2AvgNhHbufmgQwYPyyfyto2NqEACv+No6b1ZImFIJt7WJQ5lC7YmFLJrljqQ/lif+dgnt6HQYwPYKaCR'
        b'b1CxEO630amU3MfbuhAcRwFnemhmnhA5mnsmlGUWUjWrGsZtdeDTmwzuX/NcOYEGKQ0xNWp4G6gEmTlZQrx4LpcqdZwCjrKBNoqu0i/dxJUlshGpdicdKczJMyS7Hv1k'
        b'4O3P+n20Q/28rWf29r9/nace/dW68PdOtAQ9Ngl6p7wsZnFHqdn9rtaW5sDpf9mxhtq/01W07Ft6+W2PPd97v5v7m7oVPdE7c868NUP8xt83vZZQv/7jjb4pG4/IP7tY'
        b'tLWBJe9Y9i2n7ViRXe79T08W09/0rH0QvVr83d9O2kd8l7uq58ujq1tHHxv7hNPu/nn49Wk5rd0DvMZdTxbXv35s+NvyZMekVf8Iy0po3xu6P/7s+fiPtrJ+8+GD96NK'
        b'086cjrxf8J3yQPi78uqM8D0zZqZ0XbUXVFo9qHVdmZW08ZD48T3Xb3xi7ML4axa/36pcOJK7663wPx585y/On2/yf+VPY3e7R7+X9+zLvltbtiy7rbWjwSM6zembsuHv'
        b'bd7/wGL5/idzXg76x5T1X2YZE2Z+X35+aV96+PnLKW/zqz5JuHT7xJpw4ec+f9yT/WDg1ezYZYUVTxJc93o6mF6SfjOUeumjoOt2h+xfXnjf8JevFV+6Vfzj4nc1R/q3'
        b'TfF9q+atzJVRvS/VNbbf+GLG6w9retmPtrNnD57/ffwf1gVIE11uPHhy6UL34dBLeSUlsw8mPegq+o+Yxoak30TCK12uHeJay2nL3r9U9GbFS8L3l8W8P6a43frdH4o5'
        b'QsM2e6cFX+eleXxU2pZb8KbmxIP+m5GvupXVaSL+lsv53Q8Df2xfGygc8ZjW8NoHgy0fFLZeM/vjjJbLjbkdX91ac3X06O3lDX/1ObTqrIkiQPLP+Xknb7cc//3Vh6YO'
        b'+1bs/oZ+49iJ3145+rboy82A9cZv3F+HJ8bal4av+49PluWPcv/wwYmBCpXr+3viPlgzL6KurejlN6c/aF1iK/p8ypraxT98H/eF95mgbwNWfLR89/eH1A1Ny6u/zvjT'
        b'kfx3bK0qIn8XUf57dt6CzNw1K9h3Fmfe6fr67LSjvz78usUXh/455a/Ub9g3Ptj2WdVXZZEX1r0RejXgrWO/+kNJct6e4MStO2gnTd+qzz64vGfXxhMfbRoriTx58jPh'
        b'6hPXD1fmd6buWPjttPgkWZG3nLU2dfURi94zCfm/y/34PMh+xyxn2b2Y4u+W/HDXaXO0IeADr7/+bn+nfui8/m5zeGv07KuXbT87PPpJ3451bwzbbFbueqMgdc5Hl7pe'
        b'75F/Nub50OTzJZuphu7wc/6ZfOvHWNHiwCVkS1tDc1FsDfeG8pPRAQJcQA5AAE6TAVHgCl8Ad7BFGaEhfBEaAluQG+dxltfAJnK7Hl6V4wNDDorGJj7YksLjj4kdPgC7'
        b'KwQIsAJF8S2hNGUC9rCE8IDZY2IEtoA9G7JCg9Nhm09DFjIhaO21oM/6MYnxNOB8VlbGRnAmJyTHlDLhsMzSwMnHPNy1DdyDxwTpoSFoTtiCzNBeNn64eNAhgQ0PN1CP'
        b'sSWthlcXZuWBuyuFyO2uplOQS+h6jD1aubObQOQGBvhwVyiFEOpliRXpZEm5ZyXaSgy8EJoB96CuKJYNOnMSQiyGWxZl4SelWRn4JAK22CJSlbNQfHjKjdnprVWgXRAi'
        b'wvt08kc7NU9ggWNr4F6GjoGgOQsd0pBLEGaGolMeFTUFDrJhM7gcwnf70XONf28hw9jzfvTT9PSHebYyhXl+IZeW1MlKmCSTdS9oI09aykzGnz6yKLeAMSqVZR3zOSnb'
        b'OUYXD1W2wYWPao6uKk+dY6DRN0BdcspFY6+J0Dic8mzntC/aZ4OHpXdueuQiHHYR6l3CDC5hY1SE/YzRgJD22SrXfbnGQFxx25e3L8/o5KYK7lz+yEk07CTSyPROYoOT'
        b'eIwSotHeU9URPSvUJepSdWlPNQKw3zdnAuSYCeXpfWxa9zR1VNf0nunts43u3qpVPUHts4wePsfiu+PVZV1JPUkIsUhNpMFDhAb4ov34O834HBcqrpEXgKZepS49Zc58'
        b'ICuRDx489ezu6arpRnGsarbaW+8ZrvMMN3pNVZd3v6R6yRgejVo99J5CnafQ6O2nlnfXqmq13EHHfmuttdGfr5l/Ikedo5UMyvtrtbVGT57arSfvkWfksGekNlrvGWfw'
        b'jNOR6/mUYVFoSne9Z6jOM/R5q0iMWt268lR5uK1G5xWJLjyfc0/2I8+wYc8wLVfvGWPwjNGR6xnkqChCU6YNOLeyd+XEGZhZBeGozbkrW5WN2o691P1SV1FP0Rhl6zZj'
        b'NCQMdTl1ZamyxmwoL79j2d3ZYxQdkkIbZ6V/zqZDMujPKdork35MyjFSjvoHaQKOZ2kD9P7TVKlGHz91Rs/mMYrtNcPI81cvPmWrZel4YnQZeGKtQs9LZD7pyTXKDHnE'
        b'ixnmxeDe6QbedB1vOqqM+vgieSrcZzXG4rpPaTcZs6L8gtptx8k5RpnYzyAFYmxw6GWb8zZamT44wRCcoHcMaE9VidVco4v7GMVBvFaQPxonbaDGR+ODycpRFfZYqRfo'
        b'XQVGtGdbla3RLRhtx2mG0dWTdBXpXKPRZXCNHnTUu05nPuldo58YHVxU5p1JusB4nQO+RkOThxyHql72MYTmI9l07sxWu+gd+TpHPpZtfmeRLniGzglfSC7VJj2JjzwE'
        b'wx4CTZreQ2zwEONFF9LGsNSh8odxL9cbwgrHcSvUu4aOmVHeU1VpRi/fZ4WfKv3Hhed0HbmMREyJpDJD1fNVuc/+PJ1izMvWfQriNiEpj/LwOhbUHaT2V689FaZ3jzS4'
        b'Rz5yjx12j9W7xxvc49tNjQ5Oh2I7YnWeIq2p3iHW4BD7ORVoH2P09lXP6aptn2P0noMKL59jS7qXaEy1LnqvOINXXHuaURAxRk11QrYDFV22Kq5KoS4x+oeczTyRqVFo'
        b'5doKvf90g/90lbkxWKBhazLO2fTaqKyNHsGaiGGPUJ1HqNHHX2PSvVm1eTRYeNnyvKV21qDXQ3t9XKY+OMsQnIXYGyzUlGmkmrJeC+2CwciBxY+iU4ejU4fKHkboo3MM'
        b'0Tn64Bw1F43zDdQEnvBR+/zcRGSILiRe54svPMrqvJW2YFD40Fcfn6UPzjYEZ+NRz+D1wbGG4FgE5jNVJVNHd63rWad5adgnXucTbwyM0ZHLmJo5tGBowcNZb6S/mq5b'
        b'sOTXea/lPUS/Y2w69iWsRkHLsRqhEomA73J6dJJU/ocgSrtYL0gyCJKQkLtl0UyJNDNFtcboEzRGcb2yaGPc9MGK255DEkNc9sN8Q1yemqMuPGWlWaTnxRj9BJrVw37R'
        b'Or9oo3jaoMlA4pCJQTxHPVvjfDxbnW0MEGpdhgNidQGxxqjYQeeB7CEXQ1SGTpzJjHiCjWBad5IqaTQ0QuurTdH69WYaQ6I1AmTXUgZnDs4cqNKHJBtCkse47DBvpO9h'
        b'3oyp6crDYuunruguUhU9t5VffTWWxcF+hPEpEx7KW41YTfRCL3os/1/xg1bU05STCa5PGoyKF/k6fOiToSBhPAGF9Z8+xf83PuM/bB5B9dkksfk0OeetNAdbsjJCM8B+'
        b'Gw7FoWhwGByEHZMelmACkCcReEcHrMcfluC0Q+qniYcV1s8emnD+xx+abOezvqxF6FlMDE/mYnbIeCWTE1xJ1uzaBgkvZ35cVDivXkoqkaJJoJM+ZMh5UolcIa3Dc9VU'
        b'yeR4itKSumpeSVlZvaJOzpPJS+SSWkmdXMZrrKwqq+SVSCUIpkEqkaFGSfmk6UpkPIVMUVLDK68iQlIirZLIRLyUGlk9r6SmhleQOjeFV1ElqSmXkXkka5BElaFZ8Jia'
        b'SVORVClmVFl93WqJFI3Ceb2Kuqqy+nIJwktaVbdC9gt7S3mOxVpeJUINJxRX1NfU1DciSDyBogxtXRL/81MIEQ3LJdIiqaRCIpXUlUnix9flBacoKhDuK2Sy8b51/B9B'
        b'/hQG8aO4OLe+TlJczAueKVmnWPGzwJgFeJvP15uJWmokVfJ1JZU1Px49zqvng7Pq6+T1dYraWon0x2NRa6lEOnEfMozIiweXltSUoB0U1TdI6uIJORFAXUUJIryspKa8'
        b'fvL4cWRqGVxmS8qqapEooJ1iQr1oaJlCiim09jk2C+GpSqmi7oWjcdZbPCnRnIqySjRMhj4pan8O67KaepnkKdqpdeX/D6BcWl9fLSkfx3mSvBQifZBL6sgeeCskpWg2'
        b'+f/de6mrl/8XtrK6XroC2Rdp9f+lu5EpaovKpJLyKrnsRXspwHrDm6OQy8oqpVUVaFu8MMbq8urratb+W/c0bgSq6oiWYkPBG9+apO5F2yI5fL+wq5mSmhKZnID/v7Gp'
        b'ieFJ/DN3NtEXPbN3DfUy+Y8nGJcMiaxMWtWAQX7OcmNeS6pKfwZj7LnkJU+FayHyXGipmpqfkbDxRZ+L4+S1fl40/9t0l0qQF0VKF89DVgaNnAdvl1WXMgu8aDy2RWjz'
        b'RdWSCax6ihAiQQ28LZNJan4JVI4c/M8QcXwePOLFyP7E42Yp6soldS/2mOPLIh/5Al89eWE05pfmWLF6st+dg7kNT1XIZchSVaAgBne/CLBBihiAbF7Ji9edO94tqRPm'
        b'SkU/h/2ktX+C94v9/7gg/CgGmAT8s/EAA1uFln4xYMbMlNyfF7uiemnViqo6LFI/tSF5432lRCCRAvPSpJLa8saf1fWJM/8XBJoZ/t80JpUlyNu80OTNkZTC20itX2AT'
        b'/g2IYTUgeobt3CS85qOeX1a2upJayXNrNx4X84JzUfML5VQhbSBx0U8gCiXSRkldOVbLdY2SsuoXQcskDSXxEwNrNMGEqP4FEEvr6l6K5y2oq66rb6x7HnWXTzwHlJSX'
        b'o4bGKnklDtKrpDhKlUirynhV5b8U4cejU2lJLTabCKf5lT963W8yYPz4OScenQte5Bkmj56UpWZL/TRLbT6TlXcok3mZK8m62EobbctkeMkyOfi9LV58cnFohX02pYjA'
        b't8e74Em4E7SCK2BXDGwHV8Fu/Iz3PGgjT3xZLhER8CK4SCXCXi5Qb4S7mMf0arAF/bvCgmo5RSVQCY1gO1njRIkpfrWsQRVaHPrIwZfJItsM2rzEkSQ7ZCtJ5koGxxTk'
        b'eUEPvDhbwM+EuwW52aLoOuaRgcCE8vXhutdCLd+aJJsBDTgKumFrek52hhDsgnvNwW08NEtoQvks4sBTvt5k3HTQhl/+CwMnKzPxwLAJDyojYJuJYGo8SdCygScTyUNM'
        b'uKN2vJt5igm1CDH8WGA6vCbPygT9oGViAlgDOxbuqyEDwJ0UeOZZihdO7wJ9vix4CR4Eu5nHtPtDwVHYyjxrZlGLodoM3mAh5O+WEVxXgX64BeeXZaB95II2CnbAvWHp'
        b'sI1N+UzhQBVoTVFMReP8wADYNmEcTjtsCUMY+ydClYCb+BJLEYiX6wNbciutJw0k2Xm5OTTFB7e5oHsBvKjAr5la+62dMAyNaQ3LQIP8Y+cVc5PdHMiqQAVuge0CEWxD'
        b'E4kyc2BLKN8c7jOhPOBhDjiZD68SQmZK4Vlm0MLSvIwcuCuUb0K5OHHC0T5bGA53muc+YzBQwb5JLGa7KkLxan1r/GTk9ax5wfjZEU4oXIif16C/C+bCNg61UGgK+zaC'
        b'A4krx1Pv4L16cSSHAnfBZQog2Y8JZtL2LoPdVoS14DTom8TbeqghsOBGIOgSR3KpdeAWTrCrBHtqSebQBnADp0eYwrNIy8Kp8EWzGU5vBTvg1azMcNDzI1mgZ5KUBk/P'
        b'9EmC4AUuIUHwAMf5LJKosQYOwF4x6G8woehsqi4YXCpAqJAnaQfmwDbUQyGyKnHCYjVogsfJU/oN8Dzc/1x8NoEBRnyi4vkmBFtZ9gaxuIFN0VmUSSa4KEDMJTkSLfCI'
        b's1gMtVyKnkdhCQQDcGcxk4NyxG+NWCxFMHlULLwGLsN2pM74eR+8hVSzC4H1I7BCnMuwE1yrQKgQgt2JgPvEYpoCe+A5CpygqhfVMvMdBK1wh1jMpcAWVwqcpGryQTux'
        b'ApdKnCnE2OBefvGyo+sdKPJG03rHJBkNNNkUlUqlwvYVZGS9sz1+3zk2sbG45pCfgOKzmUSDm+AAOPI0jwGRNRFuZfIY7JwYrhwHp8DtLBHC/PyETIhCdk2VHYPcHic4'
        b'2Ih0NAM/1eNwaHDMRjiefCmH2zyfEg9NgwxelIRhyO6Z1DPiwW08pHuHwB3yXjEyjTvggQmKEwAuTFbYE3AAzU+S+HaBzpCnlIbnkVBehtuF47n6y+HAc0LvQWb32uI1'
        b'xCKkpoALL1R0cAzcRZoOtD4EexpxdC/hx0A+YQc8uVIRhFFsTrZDPLnxS0Zg0XgWWjq4B05g1sE74DrhHbjrStBYirivfqGBSIe3kYVwBj0k7yVNtEQs5lCVWCaOUZU1'
        b'UqLvuQ12WRnCXBEyBcGMqoPD4BKb8gDNHHDah8mvWgbPASXOHOULM5AOd4Wam7IQKU6CfiITyYW2FOKx3W8iirNTTXMoIqLpyE11wS3w6ASGIoFsY6Rhl53lBGFBdkY5'
        b'nvVyOotJerlazhZkIo/VLcwShuTid71tV7AlC0E3oVwq7EeSMimdGRENXIRHEdqURzYHdCCL2McIwj2wGx6cPBjsy8Lpz+O5zxlwGxkJVHUIqotisojBnonuKKSMi+Tn'
        b'DjxHtNZPDjqZLHC0NXAziCSBczYRivrBS2VPU6V3gsNP06VJqjTQwCYyQZofGESGBLZOzNjNK1SE4LvMiGrbMXW2xDAEQk5tbxjclY3TArIwKSLBIZMM2B5IpooHJ8Oe'
        b'pgfh1KC5RSx4NGklk69+Dh5d8jylGCcUwwNubNtYcAEpLobOnQHOgiPwOGydkKfsYMVYmbuR9NOMdZytHgd62bZQk84kTe+siwWtJKk+J3pyWv1aJg0XxQBnwX5Llgg2'
        b'UyjUKUDWqx8pHI6CzLP8ZbRlFbEshaCfZLUlzmVZSk0osN2fwiJ6EJxQEMPpnlYJ99NwK+ylKCEl3AD2EKFzkpnjtH87t9LimuHSaIpoSRiSsWacAWeK4iQkV3upoiBr'
        b'0iMBPUhProSzKXgVHkYRClXPyWB22RwxF+63tUHtB0wpDuhM4dDzwYCNYh5FXpC5u2BSOhrWkr25sK0AKjNQexhsmQuVefD40oJ0nJjWlpE/F/SHF8xLD82f5BFBr7Vd'
        b'HmiNZ7LqjvBnZonmOE+2hI7gDtla4GYLChEwtsyl2CrGdC41f5xXSPxulmU9dVwmLNhZxApZEkh2wcqEd7NEU6onz4j8NYltWr0sJqjbRtDEaFsJaCNeeAk4Y8OEBShO'
        b'uzspMAiCLQSn71ysKLROuHZ+cc1o7EZK4Ysap9Cek0MOcAIcexpzgF5wV1GIRm0CB2CHbBJxEGXwdwWIhMFItkLGU9MLMGmVoYXpcE/RKhRyYLHN/wkZ7623B23zkBDg'
        b'RPTPokiEbJY9q9iqwsWCIvFSgBPaByOZluDMZNGkweVxn2ILr9eBK1HYyedT4cg9XUwXEjkUsSS4ncYuhUJu4tK0TQr8fgKyLQfM4H6A2L4PHkSx9sQUy0tc0F86T14K'
        b'rkbTiNImsGX+YrMNxIOsTi5+Nh/ogIPgEuhCbhwLpXQhvPEMB9gdBy6CazF8DqM9LSlh4phVyCVlUgswVNX4iyKhsK1YHIUURVuMIymJtQkZb4Usd7s4ajVaJ5lajHzk'
        b'OVYjkYw1cBu8jlaBWoq4sJvgCA5lncefac2CN11QLzpa0GkUHHBDWquB+0gqZjWysqeR8MPWQHgNkbM1DO4tgFpr0BcVMfeZtM8TFv5E2JH1PGYBu/03Mi9z3IGnZoEL'
        b'JuhIcBFFStQGng1j5PuRwVeDCzGgj0WxnLGyoegAXoF3CFgNuLUAXODCw2AACRG1aQbYh3hHXlK5Du8uh/u5tvWIXZQIdBSTnfqiMLMXcegilzIHW5AFoJDJPgSwl8fL'
        b'ecMdoizRYtA1WUeK4E4mhFE2sCb6pIPgzrhPurCGSeANhPci8uCVRniNvB5wnY7a7D1uQjzLkW+7KpuQAIq20Ube4FHEYaGyB02WuTmwTVg4LvuwZWF65oL0+Qw9wbm5'
        b'K5DdUuYIRbnZecinnIVaC7Aj1r/qcfccWrYanQ0dYoIuuuTUe6TKK1Y/eufLkT0Ov7q4P7Dt7xm+VV+l84s+Sqj96oyTS3t3wTF3dceC37en6a1M/W3S0hbNNDP/atTy'
        b'xuN5q0zWhZjWjZk+ob/liDZ+c/ta44Nb/hdXCt4Q/239O4f/+c6HzWBv74LP+k69QX//tvtf7577a/grTfw991ibhaOv1i24vijoyne3pJzq32aeVfwlWd3pms6d8f7e'
        b'rD81+R201b66L3fvle176xy+qrH75r1XD+buv/7G1ZXT9/mbOo/oQhv/Umx7cVHLH2Nc/7iwPU8yv/BGpGXXn7fbftphWv3xDxm/9k0Qf5GfYLmi48u/+As69q6y+ITl'
        b'8cNfwxtu7dhUnrD6ZMjaK8rVgtGM9UllS77ddXLvjYe/6pXrE+55HzWu/La5s0S6Yfbi5q3yxsVz99dlOlrcfEcw9bHbLsUXXoFTj2zet+P+X/MG5o54GY/s1jbaJexY'
        b'FPV296/EB7dsFKbZz7Ly+az45t+OH6U/PJccJ9px8yM7gXrKrz6dAfsupcYlzHh8zv2rx9zSFTuNfzD7hl+aV9l3uDX4rfSuvcE2+blpnVnpiz8uiE988qWDSXTxu7JF'
        b'uxM/1Hb+1fcLocM/Le4v2FrN8fH92CExdSx/61770Ck9vMHchm2jVVtXzByEICzxnaubPnp1Vt7BtOWPe071/PlLp16rvFHXr5YMy/qSVos+uS919Qm+sOxk061XVN82'
        b'XTsldf31stB/5j3+QOl5Qf6G9L2Vs205sdPWzP/7pmDBd4M+Yx+KCta+/M0/G4fP+H2nKiy6d8zCT61dUv7ejKsfKdzWrJy7vt9u8Xrq4nWXjqvvLM+7UL6tyPWO9cLz'
        b'mmXnf3viNQ/Fn+5bSKbe5h4eEY4VC0/UfPr5p5KO201X0pL60k2/DIzecqEgf0XLl8Odr3/SdeQK9Hi31GmG1yv/LKoqSZ0XuvXd8JA/zN78+idLth7bM2K+wLxMMfPg'
        b'7uUFLaH/WP938a/vuFWJ+zm5S5LM1ueHLnxj5Xd13gHHWvOPPZJxw+TCzsuPvvnj8SO/Nb3299KVeZ8tXcsfGH5y+PWvpa96DkvNL7/8+8ve3WWPXlt1stVtk3XCPw7F'
        b'/sfb/m5rvE4PKDUZu2D5G1kfuty09ptZNe9B9Y73Dzy4VfXxa6BwWG5Zlin7dIN8mziq5OuIS/ru/hFV6lFLV/Y7mtFPp17M7Nw2rbxw5NHsL9YnL/a6tdHlXWuf9w8H'
        b'3XB/J+p8CTtO1tJT/0nPbzND/vTWzlz9qpFLjny3xgfnR6rC0k3fuV9wdK3qb71PBE61y37/pfcX1zLvvBlbctGYoO5xrzp5mPMD7+xmx1y7R59sv+8TvC9p1+zL7Q8V'
        b'zl8NfNP48t1pO/YtpnLfrn917LdxyV7Xd667ZvzHivN/iYgL+E1f15Zb33/Ymrcw+u1FL1Uce6Mt9LJW/Sp8dUn2Gzu6ug7XvPG18u0PP9gfsk7hXvDq2A9vXxqy6Nn5'
        b'z1Knj++nLVJ8Vq3cnPSPf/x9NOq9bblnNrIbrxo/WzU6T3l88c5760vDZoiPbHzt4YI/n1dfLzvzndc7XfcN3XO+h9+8v+ZA+ci9b39o2/jwh9PaM3n/EO1dXOoT/rcP'
        b'1v9WqucuOM63fexDTlOFQgFJyYT7ynCm6PjdHBdwjZNetPQxDk9WLo4WhIiYZND5YeaLWeA07IaXmQTVk7AlDrbmjOeDwmbQG8WysRGRznB+JDM3TmtdgU5EOLN1F7xI'
        b'OlHlAhxkcluzaCo1jOS2ivxINuh82IeOcc/SbknS7SZwCB/nIxm8j8FdZkx+63zbZxmuJLsVHEcrkMPIRW6FQJQRCrfYT07NBQcbyZfOgP1wi1yQmxOaiZFHuG8xAzdY'
        b'jWjlDpKxClq90AkMRehhQry3C2B/I0uELHgH8z0c2/zrslCQdHZl1rPZbcPZK7grmP212GY9j+my4GEU08EDUEXyaM39wwTjFDUJisMJtrBznC6rMjcLMid8tUe6ggWP'
        b'1MEz5It0YIdTJHJAu7MyPN3AxYan36STyGGDHil/6v9qmux/L5cI39z66W1x3oTsoqYff3FJrTwuKnzdxA8knTbZgkmnLTajHF0PJXUk6R38DQ7+ytlGJxdlmtHRVZlq'
        b'9PBSZhvdvJSZRmcX5Ryjq+cYlcy2nkd/zvxp5xgdvNrjVeXqVL1DiMEhZIyi7UVGjyBVooaj9xAaPITts40uHofWd6zft7FzIxrv7qtO6RK0m6JWPNjL6Oj5LJFPrJ2v'
        b'd4g3OMR/Tq1l2c+jjYEhZ1eeWKl10JboA2MNgbH78tpT2hUqyaiLp5rTsbF9o9GDN0ax3CKMniKdp0ij0C43hM3We6YaPFN1nqlGz6nHcrpzNAF6z3ADyT8cDY01hkUZ'
        b'+UJjcKgxSIAWMIaGG4URRlEkLgVhxhCRMVQ05mHj6z5GoULFHfOmgkNUVl1WRq+pY5Scdsqljd4iHbrC0h666MPm6r3zDd75Otd8o5u32r/bS+VlFEaquKpqvWsIup63'
        b'enirA1SJqkTjzDm/EgDBwzL9zHmGmfP0nkmqVHWI3lOI8F+sD0tC12hYFGrj6z1D0YVnEOrcwtCFU0K5qsou2y5b1Kqbmqlzw9doYIS6WhswyBpkD7IHQgYlQym3Kx/6'
        b'3azXB+YaAnNxOmKJlqUp77U0+ovUOMsxX7tKW9C7Tu8fb/CPHzPl4O1yyHYtKE9fda7OIxJdxqg4hIZI7xmBLpymW6fzikKXMToetYfpPSPR9Tx9NyZBlaqbitrE6Hre'
        b'/GzwV+O06PIaYznz3I2efE3UGBvVRj391SvVK7VO2lWD9lrZgLs+MNEQmDjGRX1jJpSXn3r2mCmum1FeAeryMXNct6C8gjScMUtct6G8QtBctrhuR3kJNLPH7HF9CuUV'
        b'rHEcc8B1R8pLqCkfc8J1Z2YeF1x3Zca44bo7M6cHrntSXoFq+ZgXrnszOPjgOo/yEmnkY764PpUZ44fr/kw9ANcDqYAgYxDfGBI6JsCfqaeFijMmwgS274llsm0ZLRmj'
        b'uG6BRkG0Jp7kMJYMzhpYORT90P5h5EPHlxP0Mbl6QZ5BkMdkRxv9A1WpqtRRQZjWrHfG07YAVaoxNEIb0Js9OGs4NEnFUS3RuwaTJHBNpiFomi5o+mCKLmjmkL3ee5aK'
        b'jcjqG6iWaGapqwy8cG2Wjpek4hp9/NUFPese+UQM+0TofcQGHzFWr5DRqQEa+niQahZORi9Tl6vLT1mi0d4+KjZeYFbPykfe4cPe4XrvSIN3JNJrtxC0D7yHWcMxc3Qx'
        b'c4xPJxhjU2iN/xzgaUJr6qDfQOYQrQ+eaQie2WWtMlFzjfwojYe2cHCBnj/LwJ+FNrqoy8YoEmtTtCXaWb0rUcNLelfBaEzC02zQRzEZwzEZD/31MXmGmLzP2bRblMoR'
        b'6adbiGaW0ZOn843AYuzqpaozuAofuUYNu0YhS+Qab3CN17nGo8oEHQ7QOA57CHUeQkSrRz5hwz5hWlO9T6zBJ3aMmuK1iB7liy57nPfQFuj5cQZ+nNrE6BeoFqtXH084'
        b'laD1HfYT6/zExpB4XUg82nUisiVzFyKEEhfhvFvBYpx3i0rUFYBKE0oUoSnQOg/SA27nlvcuN4ZHa+sN4WlD6wzh84yiOE31YOCQ/W3+0Hy9KNMgykR6PA3ZKFSoueoa'
        b'PU88ZvVfnEEvmm0QIR3jxGL4WAxfq+dF6XhRaAokO4ExCKXYHNqYV4iwjV1IsoQXkSzhRSRLeBHGFmm8yOAZoZ1q8IzW1hg8Zz3yzBz2zHwYrffMN3jm68iFaSnSuYWj'
        b'a9TT+1hGd4YuMHkImeh0g2e6ih4NCFYXaOwvu5x30dqfc+91P150qsgYzL9set5US5+z6LUwEmPnez2oP2jQty+EmDvFzTp9YI4hMOenpiy1e4ZqBn5dIlUtZF6XGI2c'
        b'hj4gyxqm8wwjZnS6zg1fo66eGLtgnVsIutCnUWLo0f7C443TZw7N0SVmo+2H5+Dt++Ti7aMSS28uPeob2J65L3PUzXuMEmDfhbze5o7NapneRWBwESA1cvLVOl736vca'
        b'VOgjUg0RqaTpoeMbXq966RYu0WcsNWQsJW3vufIQMZ18HzkGDTsic6R3FBochTpH4R+Qr3RyUy3VOQWjy+gYqHMMVCs0yw1BiXrH6QbH6TrH6UZH5kvIAvSOwQbHYJ1j'
        b'MJLw9lSjX0B7ttE3gODowVN7GzzCcYL/vJ91ZuODtFMMHlHYifuq5w+78PUufPwSS1J3kkas9wgzeISNUY5usdrZ1zP7MwdlfXkDeUMlw1FzdFFzjP7BJKVedjzvVN4j'
        b'/4Rh/4TB2UN+ev80g3/aI//sYf/shwV6/3yDfz4yXQEh6gWaCE3Z05dDBn31AYmGgETkhb2YQk2PcTi+2bQxchoS5+DB1CHfoZL7AbezNQHq2erZT94OikDkQwMmlsaQ'
        b'aRqhLjYdXcbgpKEgfXAG4mBcFuYdKrHSZROlyyZKh0o2Bnvy5AnyNREx2pJBWls2YMGoSsAQPcQaYj1TFy6bj9QFFWouGu0frIk5MUM9wzhjlnq2jh+v90/Q+ScYA/ia'
        b'whPL1cuRd1TP1rgdz3vyuRfeEg8DWBv8sGZ5xRljYtUc9UtIZ/FbJF46IpsGzzBtlN5zGvNJTy6jGzLow24CnZsAvxCyzOAa8sg1Ytg1Quuvd51mcJ2mc52GKqMv5uoo'
        b'/j46lnWA0W6qzm6qOlrjbfCL1dvFGezidHZxRjvnQ9Yd1iqJ3s7fYOevs/MfdXDD31+XSRudA3XoCkrXO2cYnDN0dhmoS5lDUtuNvg6LojnG6KmLXUyZvHm7EQ7OHfj/'
        b'mC//wrgXP4ArflGUK02knn8PHoluf4PHn6DGE+gLTGh6Cs6E/1cW/7KkevxdQsfMo6mrNils9qTkiKdJ9H/HNzMPURL8TdLUElY5vYRdziqgzCv57BE7kpdBctalqVJp'
        b'vfRrHyZTg1BDOp6CLinnldTxJLhflMvnjJgVFeHUlqKiEYuiIuarnlHdqqholaKkZrzHtKiovL6sqIjwk3kjghA7CRP7J8t+iJCV4fNZ07PfUasI3dOLwJPH8tHgaqCl'
        b'DdRmwOtyS3N0DM0VSscPY2HwmAk3fyWfTqtafvoGV7YTzXlluGrjvl9ndS2Gya6vrIjMyF5SPa166dU6xblv7v7tm63T8rx3zEnm2C6Za7H8VHtG4q41n/xu+ac+n7hc'
        b'uMZfybuXUfHO+nenicMiDr+1S1jzu9/XfHdgeldggcph1e7IFb0z67+k7015Z836/Jd2dHy/vNQ68/PTiQGS4cvbvz70mzdn/v2Njf/x4RdJ4t3fLV0cVvnyma3/rHV8'
        b'cvbmpdLovwX2uFxNVH2/e05djKGh7c/ZB1ddhvOXX5CZfPv6g571q17/66DVQ+Xuxaz7J947H7svJ7KYb+aUs/BWeWXKky6/rcERO2P7nMxLPTpedhx+ebXcLmGf7+rj'
        b'h43blpf69L+8ycrONGL2ayWq2K3577s+aHFQ+eeWuItVr3h+1NeUGlriJlj0ivvv+7b8dt6TtlsW17RtXn8pvXzq5kzpufSUt6/P/SH/3K+3S0qP/UOdsCq+Rf3mR1FL'
        b'X/1my+ZHw2/VX7HaJ8iecWDDzZoD5l39M2ND3SXD81de/9M364uXf+EL8/e9F3v5Ue7N7H8usL93a5nN6gfZf2aLXNfdrn+TzyFvt4K94Fw5bM2mUSRQGEbhJ4fwBLmp'
        b'sDgRnsePLyd9Ry28DrUcMwTU/Bg/GrGB18FlyxBzc/yuagvc/WyoD7jCgZe9ipj3by+sBB0ycDE9Vxj89OaEPWxnrwPHgRZuW/b0jVazXyz+h99oTSY/TT/5YQ7dSLtq'
        b'6kvKi4rWPauR4zb+YoEnzA+ySqGUtdMYx9TcxWg7RSlrj2xp3N2o8t21QblBJVPJ1JHqklPMy1v5+D0zrT/6lQ76DigG8wfW9IkGREOzh2Y/nHI//eX04chsXWT2267u'
        b'qkhVSU90l3mPuTpT7yrSuuhdY3WJuXqXXN28+boFhYZ5C4ddFupcFr7tzFNP2VfXWYcMPIrHXVHsZkFNcWxP6XRSzlTOfDJmSptn0MYpPu3C01Y6YZqeN8fAm6Ofkm6Y'
        b'kq6zSie+0cQ8eIz6xcKOY45jyV8qrMx4FkYr23bnMTauuXmqKphaIF8Tw9TEMYMmTC151lAhqY0SCC6uEQhSIxCkRiBIjUDgGoqmrO0QjClTd/dCUOP1oBAEN16PmoYg'
        b'x+sp9GwaQZNPZgy0OVMn0OP10MhBk6FCo72LqkIT86LqmC0eSD0tdGae6Lg5xRX1MdeYpclU1IUKnZn3mF0ayxyFA/+ici6HsrAzmtspXdplquj2ap35VL35VAOiO2s+'
        b'xxwFyf9T5edsysIPrYP/2u12HuOQrjoz9GmMRZvj495PiiNrP8d/HuPiKdzksSTU2JWSNNOBAg7uM4VsJtRwHGEhL/WvCzReqPaOLwg+ngcgGdgnPlN27AZlN59GH3ya'
        b'tsMRw7+l+JdGJafM46mbNilm7Cqp8R2ObBtqmhl2rrbtnsXWuZ47Nv/gWPvmGauX151e/t4U62vRvw/84wdvw9/9+pVDr5k53BcfYb/7q7ULj95Z8+Xv95XNib7zccb0'
        b'N9O8rz0umfogyWngd8uvewYJsgKzPnrl3TkXP/PmfvTuek8rq5TtrvzVD9vLbF+huXvCO2Pf2/DbnuiM9kJR54P6d2bk5HktPavmmz7GD+jhRRd4mPwvCXkkCcSUsgT9'
        b'88BRFtTAM/7klu8CMGifBc+k5wlxzl5eXp6QhVzJbTY47gu15D53jQBeAK04UwaneoA2sNeUspkSn8n2rqklHg82WaVnZTBfEpEOr3NYZvORx8N3wBuhOjVrwv+7YMkv'
        b'ELBgO9gOLpB+68Ksyf8tA/KH51j4a4bcyVdIwCMx4I4gc6U/F6dwQRXoByf4AT/v2/7X7zv/JwoS8NQv/tQr/oyPrKqrkjM+kqkRH/kWNe4jkea4U1yHplz8a7R2fGTt'
        b'PWztfWSN3jrYYB3clGbkWDRnb83W2fuejtVzQg2cUB0n1Mjx0U2+jBzrpgz8O2Yy15SL7Mj/UlluQ1k5NuVNeLN46gi7RlI3wsFvlY5w5YqGGskIB6dPo5NTVRkq8ZuB'
        b'I2yZXDrCLV0rl8hGOPjlkhF2VZ18hEu+7nuEKy2pW4Ggq+oaFPIRdlmldIRdLy0fMamoqpFL0IfakoYR9rqqhhFuiaysqmqEXSlZg4ag6dkyRe2Iiawev/w5YlElq6qT'
        b'yfG7ZSMmDYrSmqqyEdOSsjJJg1w2YkVWj2Ry2UesmWNWlaw+NiY8YsRSVllVIS8iR4sRa0VdWWVJFTpuFEnWlI2YFxXJ0PGjAR0mTBR1Cpmk/LmVJk8xiv+THx6PMa/z'
        b'nhbYKslm0s/CqJ/9QdJjS9Ob2dgo/v+r/JdZeOxM79uZpwRS9wNtUqLYX5s9/W8gRuyKisbr4x7ta/eKyf9NEK+uXs7DfZLyXL6ZdDZWaXRgLKmpQa6YsCsFN1kgmZLK'
        b'ZfjtgxGTmvqykhokTvMUdfKqWgk5NkrlT/Xh+Qnza7NE5kg6Q4r/BxR8CpZtRMUYm6bpMRaH5qDYERVWlKV1k+kYp8iUdhyjJpSzbSlz+0dmHsNmHqpMvVmQwSxojGLR'
        b'0brQGUOBQ4H3g18O1oVmostoZme0cFaG6lzEeosog0WUjhNlpOx0lF27q55yN1DuuqcXQe//APdAE3k='
    ))))
