
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
        b'eJzFfAdcVMfW+L3b6EV6WWDpLMvSFhAQKyK9CIhYYYVFVqpbbLFgbKCiICKLgKwFXUVkBUHsZCbFGJOAQFiIiZq8xLSXh9HEvOQl/mfugmLM+773vt/7f9/68zJ755yZ'
        b'M2dOvXPu5hCTPvTxv483o0sZkUrICF9CRqaS1oSMtoyeoke88kmlBZHaluf4nVwjgmATqfRlTGciaPxeGPq/Uh/fn01bxnImUhkTWPnkMh1nYtnzUZyIVKYrobedy/pF'
        b'pJ+2MHZeOqeoJFdeKOKU5HFk+SJOynpZfkkxZ564WCbKyeeUCnMKhCtFvvr66fli6QRsrihPXCyScvLkxTkycUmxlCMrQaASqYgzPqZIKkVoUl/9HKdJq+Gg/waYAaPo'
        b'IiSEpJAmpAsZQqaQJdQR6gr1hPpCA6Gh0EhoLDQRmgqnCM2E5kILoaXQSmgttBHaCu2E9kK20EHoKHQqIzIcM2wzzDJ0M3Qy7DKMMhgZJhn6GeYZhhl6GdYZRAY9wzTD'
        b'IoOZYZxhn2GTYZDBzrDKYGVYZtAyyAyHDKeMKQJOKmFNFOqWctIcXzCz1NmeyOC8+J7h/KLtRMzkzHR2RQtJf+WumJhGdyDEpF4+l8yZvIdT0H9zvGrW+La7ElydQl30'
        b'ZWAe3ecnGm5lFz5YRyOS5K6o7RadDffAiuSE+bAcViaDvTwurIxdkMJnEZ5RDHhjJrjAJeX2CDITHghfBo5KYxPhPrg3Ee4lCf1YGlCHwMYcchIFZhMUvI4uEVOEiArE'
        b'HQJxjIk4ooM4qIc4Z4A4Z4S4ZYL4NgXx1VxgNs4fMm2SsJXSEH/ISfyhvcQJciaN4s8rd/8pf5z+hD+LKf5EMlmEIUGs47pmG7YW+BKFSMaJS3xbhjLta3eCeOD5A607'
        b'YH3BYrIQq86vMgWp1iE4/rbfzxsKVAXWEtTtf2Q+NjloQnqNEc+cvrJ52+kxMUrIfVGHyQpQgRi9x2++lxfc7RfDh7vB6XSvuES438c3lh+XSBJMUFdsojcdNIJjLzGU'
        b'MUFyLmYonWIoZiYhoD9nGf3/I8tYf8IyA4plUa+ZEMqZEQThn+1TnrBRu1JdcBzWoqXu5cXnxMG9sCJhfkysT+wCIjA+zRIcTAd7QC2xkqkDm8E2cFFugVCAcj7sEoCL'
        b'DLNw9OU0sRqeZFEdJmyRAFxggC6gQh1NRAFseU1uiTpgBdjnLQgkxOAQ6jhE5IBWeELbcxAeFsIaJkH4IqBrhC84DhrCk77GXEwKl+BN+pqlbeMN/hqvI0nMM9UwpVtQ'
        b'M9E9oFNYnK2bl56rmxcizCW2hYbskbB2WghZLNudNiobeqRpjn+nsT2d3Zu+knhrm8JnsY3NWduhoxLuXc61Hwxn39Y9L8tT2cSTkTZ9IQ7b5xv+/fbss+RtQxsiP7Bh'
        b'n4V+s0Plh1tvD2/71bk5TKE3knzLsJHfc4rYtXmKb+1XXNoTLKHwEDzmZRAP93IT5XxvJC80eAWcJCzBLoauBLQ+sUMwc8FRWI/4vBvuh3vps5wJRhgJzoMroJrLGKV5'
        b'cSXGCOjFRYoZwCkrKxu1isiTlGwQFXPytHbXV7pWnCebMapPGdWsXKFMJDFFwDSMVYouP5cRj+aShKl5VfCeDYr5e7fcteL0OYf3LBhynjNgFdlnGqmxslfkVhcOW/H6'
        b'rHhK2bCVoM9KoJKVR2ss7BWi2uTyKI2FdV1MdYxCpJzTJFZZqqRtduoFPYKuxX0OswYsZpdHjZhzlJYD5p59hp6PsdSdJrisUeYaYaFcNKqTlSWRF2dljRpkZeUUioTF'
        b'8lJ05w/rw5uazcErlJjgm6YTF2zmpFjW/15GPI0kSdL8gbH1noIygzEak7QYMTDbE/aAYbI9UaNrMqJr/vMjJsE0nfj2ixTLRw3LlThu4EvPof2ZWuZhtaRhD0MpJjlJ'
        b'MWkv2TK6/UvKmEF/SQVpM+mUYr5y958q5nMKJikmU47t7wY30A1rSKIUHiT4BB8eMJVjTmTkFsIaOuGA1MKP8Js5jYIl4evgBFYYS6hEIYJvMkdc+hmbJp2F+r4qUGm1'
        b'QT87t5eYbTh7r0eC6ZoZFtfT/I+Hp0fs2LN19k7ncq4iVic2OIW5zaXPzVwViwWa8DvJai3YwCUpUSVLeLw4PiyPTUhiEqARXjMA52mwCTQmcOl/3EYct0zs4aiBViTz'
        b'CkuEMonthEz6aGVyLJ0kLO3qEqsTla5K6YAFrzzqnomFxgZJXJNBFXPE3E4RXDOjz9BZgp2iBK+Vy5Jgho0yc0UrxDIJNjESyz8RI0qOtGJkO3HhTYjRL0iM0pAY2f27'
        b'YnSQ5UacMPCjU7bz7mIzMohGeN2P/7jIZvOFIK0hLJ8KL0hlIf4MgrZiiTcBT06PoqDPTLUkQ2mETVXkSJFmvWGk3AqzdR44g4FJgiZiwKsEPI18zG4Kfm2pNRlBI0LH'
        b'/IaKMmUMdzle9mxTeBTD0wnaSj9LAraOm/Hj023JWYizpmaaTQo/IZ2yownGsEMqm4opKQ6CRwl4RgbKKXDGVDtyLo3gVLl+skkRJ/KS22CLVe0DTmJ4GkErAVdhPRoe'
        b'GacrFMbiAAcyhkaY9snvbsqURjpQE7B83KTwQjCmHmyzlBKwE1w0ocDtQpzIBBrh3xt8d5Mi5oYZtdj5sIFGwTMR/Pb4bAJeAIfStJGNgTOZQiN0/a3vbVJ4cKdSw4Oa'
        b'jYlSCTV8SRo8TsCzoEZAgQflu5LpiPOm4k82ZfKMnbT0V5oi5nXKA/CCQS1yGmgFnfEiCuNygBuZibifIh7clBkRRZdjoS5CXukGhYGWDA7B4+ASogmeh3spnHfMPMml'
        b'aAf6Sj/apAjZYqF1TmfBJbhXKhXgWbbwmAQ8lzhLu4a1XDIb7YH/nLelCpNEY2rN4KqdBzUD2jFweGoUAXuAMpKCz8vkkbk0YhZh/YnUJv4bOwoeHlk4g4LXQfANTqUE'
        b'vLQYXtUKRJwPmY82jWDflCroPA4Fv97EFHZKDfXRAmAXOAvayaBksJWC73fzJQtpRPYsuw+lGqu68fFvmDkbSCjpBCeR964k4EVjPwr+YmgAWYq2uFcCpJn5DQFyrDLg'
        b'EjgDTxrA88EYBe4FZ5JIOtwKd1Eog+mBpIxGpFSRH0ozJbZrtRpwwSrYQD8QbxtygkfCSL3VcyjogOAgch0lFO9JM+M/jdMSVA7bFxjAbmrX4A5YFkKSxgsp+CqDEHIj'
        b'jSjtTX5bmpmyeaXcGo9+PTNfCjvXGuMVH7WFl0ke6ACNFELXhlCyDElRqX+f1CbgkCe1YQawOVKqZwTVmJ4bObCJDDG0ocAP6E0jt9OIGML8rlSx6Ysiip78GUBlsFoO'
        b'u5GlgucXg0ukOwvWUvC/pUaQ5UjqlNa9UgXTay0ldeBGATwoNZDI8PAKsB2eJR3BUaCkMIIXziT30oj8FLsRaWakZoVWTg/D+rVSGbxogFEqQU84yYPH4CkKQ7Z5FlmF'
        b'5NR0DZTarNfZQHGUCdtYUmMjtMl0JuiBN8jpYhkFbeUUSR6kEZlV8welGkbeUspGoNgT6bGxkTFJ0PWsXclZKxO08jA7ilQgcZ618kOpYrq4lGInivNqUhDwasz9Hmuw'
        b'nfQF50Cl1qjozyMbacQ6tc6g1MZqSY5WoK9YGRsYlYK9DILuCi+Bo+Qse3iIgl/OjyWVSAHGzO8WKFaUl2qV+LhbOlZipPOlZAkB28AFoKbAYzwTSBWSZ2XkvQKbxI/s'
        b'teJwCJaBdmTiglgELY+fiywirIil4C0kSeRZJM/+3P6CTP8Kay37j8BqWInVERuVbbBpGgE7FsBzFIZuxnxSjSS6LOGDAoVZ1RJqxWZ6YL8U6XinCZagc+ujySCwD2yj'
        b'ENJi0sgLSJ7LRB8UZApCQ7UsasgslMLucYQzoEFGCuDuIgphiHibbKQT65Th99ZmzniUQ7nj2Jl+UgN9zH5DmTk5axFso2B/X32TVCLfmO04UKLxq5lDbW0GGzYbSIyN'
        b'0NZOgdvnktPBuWKtNqbfIk/QiVmmdFBiI1m7Xsv8OnA0G3bCi2uRk8XSvJrk+QVT8I6i26SKTnBKnUGJRleZSZGuGwMOI2VBRheL2kF4HZSRLhLPl3ITvYkQBMeJEXrj'
        b'yR7OTl4keoRA73mewvoP5il5fwiHHIhXw6E4uSN23ZvhSbAnGeWt+0WlSCISUWrgRyOsshmeoC798tcY+2sceCRRmS44bQJPofSkOd4vHu5LjmUSunA7bT28Aqsoyw8b'
        b'YQOoAJ1IGC/APXwGQS4ikPXsgjspq+cEq8FVnheK28v9ULxjuJLOhkdNVsMeOY5DZBlM0Ikit3BQHk2Ew9rQyxIc8SclSTDZ4V+T1BeUsOBQByUpLtR3SjdhDzwOrwn8'
        b'CaJgCQEOEELz1+S4myvbFE+lAftxZh4P9vvFgjYvE2RDOTKmMXJlrZS08MEV2CxAzNy8mgAHiRVgBzxLsQceFwWQsIGHElMqsUdZaiyDMOfSUbPGTeu4LgH1PJRvEfD1'
        b'eCrfQqZnPyWvcwzdBKCDQbDhTgI0E4U+jhStzuCoWCAgCK8NSMuIlSjGPEwRAa8ZgkMCAYtYAMoJcJRYFQy2UePAyjUGghAUXdgSQEHkWoEmOd5QsBPZxcZ4nEjuSdJu'
        b'hnFpCThPD9UDlRRp04AKtAhCGDieIZDXFsFa0EbhpsHryIUnIDQ/WMkjCYPFNGQQOuA5FGocpHYS7dox2AKOgYNwD8q2EpkEw5FEty6VUDTFe4PrghASLTgTha1EPoeu'
        b'dWu1fAkPsxhWJIE2BmE4nT7L3QRu36T1MSeRsKkEAPmAUFiFcluiEJ4H27XWYNdqW//lcE8CWg+doMPrJGhYBk7KEzFeayK8Kk2IjU3Ej2JQ9qzNnb18ud6Jvlw+TR+0'
        b'iKixT3h5gdNWPC4i+gTPAhy0soQnrMEpGgF2z/e0MAVKcN1Vq/AdcKcuAXfzkvgxDIIxi0TeuMxC21UJdmzOAnulRhI5NgZHSFd4ahZF43wkZoedQRvsNNb2dZPcGHiZ'
        b'QtsEzqfDU7mwcxztOnI+jSS1DRLQGQt3Z0sREmUuSCcGbKF64uHOQrjXUSrTX4sDh2skG5alaIWhrDAMnDbDPcgAw60kx2sxRUMquBRsag47ZRJ4Acc+10l7sAMoqOGE'
        b'KHE46gtaDXSNUAJPn0rGcMDrWvNfA464ohDrmoGxITJM9GlkLNg1T7spdYvBDXAN7JDqayk/QHLg9mStXoEzoByFrDVIAX3mwRrCJzmLsgNooi7QBvaY6K9eQxIMeI6E'
        b'atAEKucjkcXzmb0GegxgnYG+HuxAuxlORoNOeIXqKka8V3uB3dJxHh4incFhsdan7afB15fAXQa6uIuuT/pyYDVFZA444Am7Z8FOQy3SOdITqWyT1lWdg8r5C0A7Cu8M'
        b'JbizBXVeAHXa1V2CJ40XTJcaw24qkmgm3UAruKBlitpuIzzqjnyQgR6OSjrIEHh4ASX9zpxMsAdeRAZejgQfXCZJUAO2woPgKoW5sAgtpx5FJ7ALdjGo3faN09eag3YX'
        b'p1hTA9ilt5pF0D3JMMT6bmpLN89aBw4bUz3IhXmR4RbwiHYBr4NjM+FloJSCylJtgHSO5FpztHpxDLaixcUhKktNkO+GFaSHISiT83HfdrT19YjQGrB/DSKuEuwGbSHg'
        b'NAo+6kCNA6yBhxaShOtyhiXsWa6NIc+AKhNYo4OiadBRTPgjddomT8Ed5x1AHUKoQ5jlfxjrILpbheboQH8PAjXKn5XgIrpfhWB36cEz6LYKtOavouGoVqkH6s2QTs/F'
        b'9B10KQRbhQawMh6ZhJhEX0qBebAyMY6fCsuT07x8E+OQysPKWG5GDLKtqVCNkryFhNQSWbck0xnw2GItU7cKSdCZmpILj9EI0hwrG2ymfAY4Ugia0pBDcIWHgglXg6WU'
        b'GXoN7IyJ9+V7x+GZzzEIkwzXqfRCS3BWazh3IVNxFfbYYjtSqTWAulCBchs2uK51Y1f0VyP/FuMTl8xnEQbxtFWIyUfQossp6TcTLtsC6nlxifF8PAPyZGbgCB2o4d4l'
        b'XJrWZB8L2yIIQQxRzybAYSJvTg5FLT91lSCERehnEaABWf7zqwt/fvbsmS+DSQxuROo2K9tQNWs1wR03RJfgfh+wI3OSIQoFlymJ2Yis3Vmosp9siNAuVGjFaQ/sALty'
        b'cM72whZloLXjQaeCC4URYPskW4RUpV3L5BqZ7aq10tVyfZx3XkFWoB22U0goUAfnrKchEVwLL2BztJd0nkZQXfHesGxNKsob4AUjPOB5MhAcDdPKey5o5ZoaGBsgtSbo'
        b'i8klLHiQmoiEp5zB9eWTrB64qkcJOwtcRsliI+iYZPdY8BC1LDd4A1QVIaZMNn2xcFyVD8NjEinskMFKIxZBIr8K9/NJrSXtYcO9metf2ER4agmFsxSlyTtLLJDZWG2I'
        b'ST9MeurDbi3r24DCGDQlvrCWUAlPUV1ByPzvAkeyUNgqQbkS3Zic6gePaZ1fE9iJgh8VaECdsAPHni7kbH9wSEviViR1VT4S6WpqOtBNOmaDGu2O1cAGuB2t/PgkGwy2'
        b'TqdEKdVJFg53G1AddDPSvzCCyxgPWtfC5rykl/hhmqLt6s5EqQpiB7joNsEOoT5FpF8E4uNLpi3ED1m27bra+G5H2GKwZy3sNgQVyC/CchJecAb18ABo59JRrEXJyWXQ'
        b'uLyEPmljYeV0JPe4zx22p4A6+iTz5w9U1DY4TDEVwW2TrJ83aBYf3F/ElNaj8DKv5vPajPiSgVmmn3Y1LWwIir33t6lig6MfzqrptsiPDVXMCtrJ1zlIP7PY1LpV9U2X'
        b'zmaa2dIwziOd0Df0Km68kXXfz3/a+WXt1ywOw+K8lQ8b6ktWrrxWE7byg9KtQ+aVZjm+5oaZ6w8yZ9a9VxtkfrXtLN0kvucdr/XSddfeWvTdwkdfMktmfBAY8kHvkwBj'
        b'/ex3L33QcG/Fujy2iZnlORfHfXFvZr4Z675icN7Va9vSeVPesb77TrTvuo/TNQGMkpagkJ0l9K91G9iXvjSyf9YAtu891lXaEr8oYAfzk6GHirS4L2Vq/UW2bdN3zfC5'
        b'yT3seOfsAY+s3/YdDnqUPfvo5R0RD6efjrm8KPmb2ssw4IBNpv7Htol5J5tHLDr331zYbBY1M+rRoSD67ryqoIcnRlrPVw0f5a3/bS6KuT9xndJ4vb7P+E175+Qs8T2V'
        b'GbQRb455/9ngyRJP1bzvsvaG0du+73HYa9DaaPiA0e94u642AhwomGdr8o+kbz+g/3SxsuiLGZzl388JD06uTOJ/bP/drVMVGftt31PHdrsUebqZRZSaq7/yOJ7J/Ghd'
        b'xaNTc8/U7jkODuzfsPPpj7kmj4Nev+3BFQiqdCoehA9FvjGtRc89+rPfT3/h8VeHgwdm3/P/ovjK7PozVu/aJHMdkn8SemYtCnjwSVL1MdtTo97zuqqvn1q381uziyPl'
        b'zj+ZrXh/2oK3TtYO+2fu/ulCzmVe0t9qj3H7bT8te0tkLLLzFF/VSwv1hbR9PP/Kz71v3+/pvq38fTtkfWDU2N7/vf7tB4W9fEXL30Paim+tbtH5NvJesKvl5w8HvN9+'
        b'+svFDxKnRbbNMLJfUH3OZsoMn3ejP7nwsaq94oKk/Y76izzTAs4++Vh/tOTKXOsfP/twedP3Vz5xOTrN6DsXRUF2nfyX8/dyty109pQULd+0/+GvA9+eLhiUrplWe+41'
        b'J//Pln7stXZH6Fj/F61q3V/ZfGHW6Rpnh6Rp5fF/9UnU+VyjDH379yk6w+/0L43evuvojKJvXHsYR3+e2k6u9Vi9vv+KdEjwZGpk13KFUM0/yz8iUtODi2qZhy58+8GG'
        b'Mf7Y7m9/vbmnepbxRbck0ysjBWfJvb/+5eLN6F/ilw9kHbxlNb3uk9nVp/52LOL2wCLDb8KJ29Gm4e2Drh1L6tYs9/kwaO3G6T7899q7nDs2f/5jiEHIu4LV+lcyF9yq'
        b's78rZ32hp8qKniHgsT775PGnB01k5rcskh/+tPrvVq4fPr3mkBU+41u9104/NrF6mPnlVyYNH33xUNzCNXpC5UFVYC/YB/f4JKHAG7kllDGAVppNDDwHTsF2CsQUeZ3L'
        b'PN9Yn4WgwZvri4BgBUHYcBjLQQt8/Qm2PSiJOpMGXrd9fjSjPZgJTnqCjb9NdDbPFwUkFWh0FthHA+WGfFi9nuoDhyzB+QCHeB+vGORwkbtGs6+nSZ5Q9qjZAKVesYne'
        b'iToEi0GThehClS11VlQCT2xEFG7jxfh4o2FhBfL3++mE+TQ6sreNU7XYu9E/dXwyP9YUWeU15GywDVyjqAU7smEnz5cLd/tgz3SWBlRwpyAU1lMUyWFjCdyT6BML96He'
        b'IBR15hvDXfpP2FQcq4+oxAd98bE4VUHcyqXBdlfYkLmFAoA7QTW8igLXMzzviSXrTaOBZnCpgGLmLFgJd8JueCkeRScoXuLH+aD0zgz20OGudQKu7R+OBv53L1LMHc4f'
        b'PmUTH+3xhJn2eEImERZLhdriBAnKzrWnFD8zqFOKJ3NphK17FUNjba9IGLLmopaFjYLdZ+GhcXZXClusVeYt7CpGVWa1MQaJqd08bM3vt+YPW/vdsfa77+5dNVdhU52k'
        b'8fBW2NYkayxtFV61y4ctffstfVXSYUvBHUvBfUcXZUDTSuWKpgIEPKU6ehx4jEWwHZun1k9VBjVMr5qrsXNUrG7yrIrU2Ds1h9eHK3MaZqoCh+x9q+bedXZXMDUcd+WK'
        b'Fr3JDXuOcm7jdI0gVOk4wPbXOLgocxuXafyDlfYDbL7G0VUpayxSM3ssLhhp3Liq9BOJalGP7EKRhs1R2jYlD7MD+9mB6uCP2GETqH5BSrsBts/EV1+B0rYhGX8rHHQI'
        b'xGhWTQnDbL9+tp+a+RE7ZBzugW+A2r11lWLuBDTG5fkrrRoS0LfmZfXLmrMOZ9339lNaNsSPGRMOrs0J9QljBOk9m9RExvxIJ71jyScE6RBH3nfzbIlXuw+5TVVEaZxc'
        b'lbHNWxq3aDhuykUtJmraMEeglg9xIj7iCO5r7w1zQvo5IWr5MGf6o1iScPEYSyAJjgvasIxqwzEa086sijVmSLh6VplQq25OViQjVnv5tBufNlZLB7ym9Vu4V0Upmfes'
        b'7ZrlKsuzTmjRiowmQ+WCfhuextvvsMk9W696J40Nm7qbNWwT3GMxZDN9yCb4kRHh4IOWg+RFr3Zmn0f4oHn4fZ9ZvRa94rechnzmo822qk1QWt+x4GK54NZm9XnNGLSc'
        b'gfZXyWqKGLbn9dvzVPOG7QV37AUav6je3Jthb5UM+WUoGNRcGf02PmO6hKW9Il0xT2Nh94c/GYqYf/bnDns6dfWfDK5MVyS91Hgx3JiDCcUoDmHv0OxZ76l0U65v8Ruw'
        b'Cxy2C+23Cx2wC6/S0Zhb1oVWh/axfdU6w+ahQ+ahGkdnZXRTUVW0xjEaXRycmhfXL1bpDDiEVc27ywuoN1EwlUKNm/epuKNxKrlaps4bcJuu0Bvx4qliW40VRhp7L1XA'
        b'oL2PxslNxWrcct+L325w2kAd2eNwc8pQWNyAV7ySqfHiq3JUEpW+ekFPYNei4eCo/uCo3pybAQPBiUNeiUeZGmcPlccJpz9Bpvr6vMMHncNxr+FpQ3VaD/+m81B4/IBX'
        b'wlHmc5QBr1Alc8TJRRncsEG1bNApfNQj5OOouJuRH8a8G9O3YPEHyWN0MnQZ+ZggPZeTSGydl5P3J0nJX3hB6kUf8WbWxytm33PyrF+nCZvek3eN3SsaCku4OX8oLFnJ'
        b'UGa0GKoykahqXHmqNYOuwRrB1B5WV0Qva0gQrZyrsjqeoHHnq60/cg/VBIX2WHUl9FoPBcX2CeK0nUjWfGaRSNjYzsp5jTPvc7xVUWrXtjgNx+s0D2n1nC7xgPesMSbd'
        b'zxGrYWMyEhyk/3nNWZQ5GGTzn0SRhE/g42g6MneTTlwNRw1fso9/cub6r1hjQ2LidH+SAaaMLXWJxDC4Mo0646eRpN2PxP/ghLaexSVOGwTRudpnWsE6bvGxPrEoRyDg'
        b'1UgSpTyXYedLz7+NCOqZM+PxOtSIMBp//o0LnYhXS50ERrj6jnoOzvgPPgffjtKSWJT26adgbyTlCF+ui6OK7daXijiJ6WFB/pwSCdUI9NXXj5VxJCKZXFKMcQrFUhkG'
        b'XSEsLuAIc3JK5MUyjlQmlImKRMUyKWdtvjgnnyOUiBBOqUQkRTdFufpCKUculQsLOblian+FErFI6suZXSgt4QgLCzlpUSmzOXliUWGulMIVrUPCkIMwMUyhPlXeoe3J'
        b'KSleI5KgHlzeJy8W55TkitD8EnHxSimidfaLGdZz8tG0uH4wr6SwsGQtgsCA8hy0FFG4vj4frTFXJMmSiPJEElFxjih8fByO12x5Hpp/pVQ63reBi6BfhUM8ys5OKikW'
        b'ZWdzvOaINshXvoSAWYTJezHuHHSnUCSWbRDmF2KIcf69AIgvKZaVFMuLikQS3I9aK0SSyXRJ8SQvAFYIC4WIoqySUlFxOLV0BFScJ0TMkAoLc0u4+jgcQRMVaeeZK8oR'
        b'F6FtQNTiBU5058gleGXrX8y0EJ7Il8iLn0Pgap9w6opw5Tn5qEuKvsmLJlORU1giFU2QEVWc+39AwoqSkgJR7jgNL+1PBpIhmaiYoomzUrQCjSD736WtuET2L5C2pkSy'
        b'EumSpOB/iTqpvCgrRyLKFcukf0ZbGpY1TrRcJs3Jl4jzEJkcP61l4JQUF67/j9E4rgjiYkqCsYJwxkkVFU+QSVXj/BdUzhEVCqUyCuX/hsjJHiz8uamcbPOe63BpiVSG'
        b'kcZ3SCTNkYhLMdg/sy6Y/yLxiknUYKsoE05s7EJkFdGQhYWTdveV7X95zJdF4V/ikUSErC8S1HAO0jTUmwqv5hSs0A40AYN1EC0gq0A0iZUTk6FlFMKrUqmo8I/gMmT0'
        b'/8nix3ExxAtCXrHa8fLiXFHxCws8PjyyuX9i41+eAMH8EW/lmpdtdzTeAXgiTyZFGpqHnBbungAulSBmIf0W/vn4KePdomJ+ksR3MmUvzfEKTS98xfjm/MFfvITwku/Q'
        b'wovRFH8OHDtndtLLW55VIhGvFBfjrX1Vv5LH+1ZQwoAUgDNPIirKXfuSfvwLAvQvK1q+EFnBP1X1aNEKeBWpQvF/fFIsXpTMYv1+ac501POq4BYLi0QvtHw8BuF4JaHb'
        b'z+VCLimlfOIrUBkiyVpRcS4W6w1rRTkFExhSUakwfHIQg5AmRUfjUEuKi5eFcxYUFxSXrC1+EdXkTo6hhLm56MZasSwfB0FiCY4mRBJxDkeciyOl8FKhRFiEzQKaLz3/'
        b'D29J+OqHj8d84ZzZf2rJfPVfqqqwJ16tqkhLkuOgGzREeoM9oBPsDoFVoAvsxWdpZ0AldbJGC4BtoI2I8A2GZ5lACS7A09qTikOgLB500gh4CuwiphHT4Ll87and/nDw'
        b'Oi4xyAAXqBKDRfConIMxdmyBzTxuHNzLS0rw1T7f4rEIZ6d4cIBp502j3mOAKg7sgntiEhNi+QA/d0Ng8XwW4ZS5LoMBT8Aa8DoFJwIqUAn3+MVhML+4xHjYI5s43wqA'
        b'lSxekY+cenhV7Q7qJg6/Uha8OP5aC1qoQ4QwcIL1UlnCKrDPuJQeKgNV2gF2wIuwdqL6YAbcPV6AcI4PL1LHbwbzQQvcg597rQyP49MIXXiJhihvBx1yd5xMwD0IHU0Q'
        b'ixaShGje7xcDK+mEkxk4BpoZUIFrvanyj8WgDB6Kj9OBV58D41KXClx84sZjRqSkyL0wf9vg6zmTBkweLxk5B5uSEkmCC64ywWFQkU+NacgBl+PjZsDtk+bHZSEI0C2b'
        b'OWsVWqQzHvNIPqjgZcMDvrASjegblwgrfLgswh42MMDxSFgrp963AGfhJR4FAi+9lhybCHdjIGtLhj+SmVbqrQGLNHBUSpW6p3rhB5m4kGUhfmiYCOpQc0EKrGQQC/k6'
        b'oBZeQ+vG2VkKqAIXBYEMAvQABQHqiFxwxZMSJRcJvCwIZBJgO6zEh5D5YFuh9iD1UB5Q4ZNh2yzCH/0rGX/9AFyCLQIBSUDFdAIcIwpKorRH9QfhDXhGIEAj9cADBDhO'
        b'FM7IpHYXHAC15tqTVQdwfdLhagG8Ev41frFgvGZnIWgG16Vo5K3hRBQRBTrADkp8IuEJcHHy6S3sANdMMuiFia7hX+vgtBZne0namr8KWAXL42NBhRQ/IGUwSDSoClaE'
        b'S/AeSIIpQOpErAHW6wkEaLBmeBxX4+SDRiRtGGoLksaOeE+giuUn+SL+e008J7YHuxigRVZEnZvBHqj2wpUnXLjDiI8SXz0dGtgHzyeFS/ADW+qNCW2NFELuhrW8OH48'
        b'3zsJvwuUC+pNVtJF/rBD7oH794DL8HL8es+XCpPgfqpgxj6BgRhYDZWUSoIyW1j2JwVMuHwJNpszjdetojQCnAD7mFqVA/v8xlUTnoQnsHJ65zBBayno0p5sb0OKdICq'
        b'3iJAx/MCLj+kWtiggMvh4MCkaifQBQ+8qHjaOp9iekHSYrgnAewqnVSqg/4dluM6cLDVDlQ+P1gHFUg54e7F4FgCfuAfj9kRCOpYseAM3Ksl6HV4gT9+1p63XHvaDo9g'
        b'/R/fYM+QiYKixRvHS4pMAou1xR2H4VVnuCd+0/IXBUpgf6J23DOgDFwZrzUDh7jacjMTpLTawq7LEc7jdW/4pPSlwjcr3fE9pQrMtC/DjMscVWuGjCkoM8CH+0iH0oi0'
        b'LGNtrcxe2OaGXy2AZUnUqwXnBRJcbiDBjNUqzeGAWbjGQgeh+iKrTmSxoWJcnfI3gE5/OgGVXAKoiBJwbLxkbiPYFQdrTIzRrLU6SMDBkUIyHVmNdnkqxttuC/e+VF+B'
        b'pXd/Etr9S6vTYHks6vKDFSm42CJGW2kxPwV0+KelxvjgWqqK5wYEnDUyTZYiv4IZGwW3g4r4ieIwVtZmUE3z1jNPly/C67+IdOyq9KXR0FD4/S1fvhfitvd4nVYapqXc'
        b'JyMGc5naRCGonv/KxDdemwIqEfM6tGXFoG4O6AwqZRHkfNA6Dx/Fd2irrxYgB9CNu0iCTIXHc3HhTyN8XY78IlGU4oH8GFpuNTyEXOzkCpZzTNABtzFXpMpWgK5gEokg'
        b'a5EInJLPRmjTViQj5iF3sg+RD/enQbUROB8UkPKcVan8jFc4BffYwtOgWR8ejkzSGsnLoAZbaxYBdiEHvZHYyN1MGR2nCHgWtIaA8zSCZsWBZ5FQSoGawlmNdPwgaGUi'
        b'b5pEbCY2I5d1QVuKWCCHnWtnFsNuqp7iIhmUEkQxRhdczZXC7oWg7HkdUJAhVRkpD0eXleB6nEFSIqzkZ4xvBqxYGBOHNPn1BTHp2oWB00gQEvm+SQnJyG6fgmp9sGN2'
        b'KJdGTWxQmisAHZjvCaCVg5gL2klKrgM3r0IdaN879XDBYsFU2MpljRepcUwFglI6gbjaY4a2ygjUaccyjRQIoJqJNgq0IPcDLjiEU2MtN4ZKgUCCMJLXxBGgHe7T1jLA'
        b'Mx6gC6F0IJQM2JJIgO4I2E3VPySa0in/08am/A+4WKjVmJ1p8BD2P8i3d1P+ZynYPV6FgDURdIxTBl7fjCjT5Wl7mmRzJiiDO8FBRNk0a4SFaciAe5aP04YM9BFMXRPo'
        b'0aKdpAVOUJeCvCbotodXERplDs77gcPIjWUh6pAbg1cRDyiceuRhzhqgHTKYQ8DTyMGawtepeh+eBYPQJbJjGLOyfbiSUmJ8A0BzYOSE5K/1QzRborjQWitfh8Cp55Jf'
        b'HY835+w0LkNbINaIK7sFIasR4XHwBjIeqLeGS9FgCNTgsiCIRZjBvTgMEKGIoYqabGoKSxC0Bo03axam7TQKlPaO193PXIGmgmoCrRVsB4i3HWjAi9zxaporQjrqDsCv'
        b'2LjDaiQQGUsnGNGuh6ve0Y5cCcNvS62GLdqymAoUZPYg9WxDXbVCAtYToBXWwWPi9NAWmvRNBkFIf5zetvD9Evsoiy1Xvu1a+1t1aEXatH3mH8fW3Mn+7s7lqs+6+0xO'
        b'Oe154/biAu83HKvca+grFsz/Qpct3uHtvH276WdvbjXXObc07HEJ502937deXz/t1y8+Ca1UtdR/MnKv4emXm/a3W10nOgMPcn76dvfDU7Uhob291WPcz9POvxFbX+vy'
        b'ZEBnJhF6ZlHR6y2HV17uuPJ5oyasn1yVfShs1NKMPZS669ajO6bJI6m87aHc+B9Dkyw/6O8xzg7ZuarRoCblzm3uL6ff3bXR+tb7bt9VFY18vHr7Xackh/dv+YuebYp4'
        b'Nn3U8++/BMU2Jw5GrzidESzbcHSZg4/NN6u5hyxS/IcOLBq9k7mTHCj9KrQjVBL6Q6h+qFWpz2den8V0HU0rbbu3kPWM+bDe6uuI1sTs+IwztfuaH+boyRd5LAtsXPMP'
        b'9/e+kzR4bZs5ZZFz7n7Xs7nihT377E90HspvPfDO05gvwwOK6mQ5l+//XfDD00+3zPl9bflxzzBeVYnppfibzrG+Dfb58ysXAKuuIHtQ0N29xfpHsyMrFpzI2n8/uHPe'
        b'0pAD/7gz/2brU5eH71Y8vhv9l82Mdw3+YufSOuVbS4aErBZsV9EWmd4McWlgfx1f4xT2EZmxcqz6TbvPtr9/wtxlueuZwPeXBJUMbDz0peH704L+dmfjvrzKvKYv6/Jn'
        b'JD92fN9v4O4q+mvMaHvX2EvuYeGLpzrMeMvf+ml3XfXmJ80t+VL5V3M3veW7ffjBdz8+6ZRlfG7V0Zm0Rl3WOm/7tl0nm777efWb7e2SG67X33qkc0Pd5j9qIBG8k7xQ'
        b'Z4nx9UtDtBtR38YW/0NzK7bX8Hup58zNksXxCZ0HXS/Z3PM0dCv1lzSBn79Nky5Txuz+Lsea+/YPbu3+ru3ZsgeKhErJefcb4MHjB1kR995+tu5eX7foVk7lssOP3u3+'
        b'+dPKr1LL38up++2Wsi/pTOAHLtf/Wm435XRdRXCqyarcLLuN+9Y/sRM/mypuz85wePDN2vnNVuZJjy6/88b+3X87cupwWJTU4fjlr9r+ahirf+bb31cP1S4LGP45aUnS'
        b'LfHZVLP3ov+xqPLs3VsLL7h2C0vWHfnaq+fGzb8+fG/+73Xs4Eshn30f5Ssa0xF/PK277va66msOi7qSn6it1q0bs/htmu5l4qfHLT8br3F4qlsQGg/042FtaMtf12qq'
        b'FhzgippBV3xg7WcLzxlesfp++rG6pS2ahD3f/G20ROfezaxtrNSrkaPvNq5IeePHK0fl1T6/fflzZ7ykoy3aNvrrU3vvcWTPFBueKk5otvCsfrVm/riK9mPlom/EIuMf'
        b'37f5m8Wp71tZH64J6x9e5dWw4PjtG2rnRdl/23H32Jyn8/+yxXN5TpI8/rD9iMbP8uKp5N+bPt+aejvuhv43P0SsWjL6zEp8w/pCweP8Xd/qfSV6M6rwSMrDQ+9vMC9U'
        b'rrr43Xt1Vz6bsXz7tqdVq0QO8wvcD9+6Y1Dq8NcZU37NT6pYEC34Db5/rj/h6Vjrvu/yj5tdsbx7znHjWx88vhtQTOdIGlw/uz6T2Pf9lFW0r9QVz6bvtR8Uf1Mx49TV'
        b'3E370p69sTL5+6gzF1q65zR9V/1DzEn7paM/M9ZdXP1acuXVYzOjiwzeeW10nb7nXPbwg6hnnWrab/KZX5rMmW/8cV+ZyapPPw1KuPW90buFIW+tj654aLSOPSd5pCwy'
        b'tnkGffT2PL1wN64JVXNi4rVEW8WSJcUFJ+O5tjXoZsQga1pL1Y4ss7LjeftywTZLqrZEbxENtOjAM0+w/RUjk31qUmEJaCyhGYOrPKokxRDWL55cIwO6gJrGh5dLqXdJ'
        b'QSvYMx+XyKBktf5FmQxoSXiC49BweDH2eQVPCqwfL+JBWW4zaH2Cg1QPuM/wea0Mipq6JtXLoKyqgypNyUUpxBVc55MCD/2hzqcRqqk1gOtzvHlJiT7z5sbhReiCS7S1'
        b'8CRQU4tfOQ+eRTHpbj8+Wt5alPg00HwFsFtbZrTPBVTHI9Kfj4uc9FkTf/pKeAoeoca2BwdQSv8iNEXs2kHzDmBS/PEHV0DlpJIdI1hHE8BdoE1blqNKBefH37Z1AE0o'
        b'Ixh/2fYwPERNz0yF22AnVbWzH91uK9W+YE5YRjDoYRu4Lv+nVTf/3qEwTl3+WKLzcp1O2R9fJS6ShQX5S6KI8SKdBzraV4mzdQkLm7qZ1TMHzN3K52osrcvnaSxsyqM0'
        b'9g7lCRpbh/I4jZV1efRdG3YVY8TcQZGrjBo2975j7j1i76liDNjzq+ZqrO3rXqt+rWZTFUNj56yc3cSr0rlnbT9iwX5e2SBQpw+bhw+Yh2s8vE+tOrpKba4WDniEVidX'
        b'zVaI7luzlYyDm+7Zc0bYviq5evmQ39xBdpSG7dKcWJ+och9k+99ne6sSNGy+Sq5he6osNGwPFUPDdlfKNGw3Za4G9c7VsHmqdA3bR5U73uKqgjRsL5Ub7p0zZm/sbKdg'
        b'jjkSXt6HDe85uIw4+vb5zbtpPeSXMuA4v89mvsbWUenW6KDhByoKBmy8J77aOyrdGyM0c6Lf4b3Bu5kzMCe1nz1TEaX07sfUqBcN+M287xek5OLaHoTCH7T103j7KfIb'
        b'TNDXPpe4Qdu4+2y3owVq9x56l3ePqHf2tfybrpdKBjyS8CqYqtw2A7RSqo4jrW3DgFv4mA6DIlUfVyQkDdoHaoLClL4D7ABc/1M86BCkCQ5X+g2wAyfqgUKm9bkEDrAF'
        b'E99xdz878O/UEpocxlByYkexY4yOWpiaVWpLtbTLbsAjYoyJbo2xCAdX5dwxHdzWJRzclbljeritTzigTR4zwG1jwsEbDWGC26aEA081d2wKbpsRDl4qizFz3LYgHPiq'
        b'3DFL3LbSjmON2zZaGFvcttOOaY/bbMLBQykbc8BtRy0NTrjNIRx8VbIxZ9x20cK44rabtu2O2x4Yfg4WAgneZpdHPHRXwRjzxWyb0hSqLQIatuffseeP8ILVop7IrlW9'
        b'wTct3po2FJI0wEtWzFVa1Sdo3Dzqo+7z/NS6bTMm7rgrojQ+AW0JPZH9PjMVDMXifhsvjaOrKm7Ic+qw5/Q+z+k9s4c95/R5zumdMuQYqaAjBjp7qCL7OP7q+H7OTAVT'
        b'4+TWtGHYKaDfKWDYSXDHSXDfxV1FtngqInGJWa7SAIE4OinoaNSmVcOO/v2O/sOOgXccA9UiRGTkYEi0RotwOFIzXkwT1RXXSw54zak3UrBGuEHqjAFuJKIts95Y4ytQ'
        b'R7atQl+W9dvw7odMwzUrwyGx/SGxN90GQpIf0UnbIIWFoqDf1lsVqWFz+pwDkHxobBwUxUM2/GGboH6bIHX6Rzbhz4XeXWUxaM9Hqxh28ut38lPrDDuF3nEKvc/1bbc/'
        b'ba9OG+CGKVkjrh7KNcenqZ0HXQUj3uFjBBmRRGpSFv5IJyMycU0PbxGu6XFHVxbh7nM6TW3VQ3bZti7XuPmqmeqSIf95vRuG/FM1bj6nC3o8eqdc4/amD/jGIQWY6qJk'
        b'Kgv7OYIxw38Rc8AXyS8jFOMV3eEEPTIkPKeiyUMTSU1yBqIodCFVZZRJVRllYoqQtvgOsQPULkPsYHXhEDtymB3Xz467GTzEpoyB76AtsjuOzbH1sX0es3rdB9gxCvI+'
        b'2/VommpKu/Vpa/WUVrvjWViJyXad0zpqslVfQ2m680XP8549zp1Y2+WXigc8El9S6ajGGbiukH8HmbXAqUqfO2w/ylRMH7Sdft+Gjaf2GrT1Rs0Hjr6IWv9wzfQ5fREJ'
        b'aBH+iXgRTkl4EbZJ5H1nj5q4h7aO2ABvqd6ilA5b8+5Y89QWFx3OO/TIhwOi7gRE3bT40OFdh76Fi4djl9yJXfKZDQet3dJ52MKz3wIp4qAFfxQZaktbxZJBS68RCw+l'
        b'XLV8yDNi0AIXulG/MeE+aOGFpKYqSuPqXpWgcXavibtvz1E6Dtv7D9r7v2pIcd+Qvb/abMg+CHsHZ2X6oDUX117OrJ+pEgzb+92x91PPvRh3Pq5H2pncKxwMita4eVHF'
        b'bNLjycNu0/rdpvXM7XUdcJs37JbQ75ZwM23Abb4iasTdWxVwOgdXRPY4f+QeoSTHGAznBFITOBWJh1dPVK9zr/At92sJKndkSfQJdz8kLDld+loxce+lacWESeciMUGG'
        b'zs1LFXJihmZGZB83fMBtmsadq8o4uRzZU5Xt8WQUVHlMR5YIARkNu4YMuoZoQkKVDOUyJJW44NFhmO2nDhpiT/0I75+rUjZoy8O1jEuHbLyHbQL6bQLUbsM2Ux/8kT2P'
        b'ZrMIW4enc1mEqeWIqYsyWOU45Bo6aBqmMbWqM6o2UogGTd0emtuOWHn0ecYMWMX2mcbeN7ctT/z5yVTCK/AJQUMrHvGe2h8ao/Ga2es55BX7mE6GxVMKl0ApHLrSMdQv'
        b'VPGYxsB2SSjj41DnpbY62so001EGPiT7H1ak/WlAgn9kJfvPwg8q4qAu72G4GYS2Ui2NRZJmTwl0eYQv/265WhOLT7QZhNJfOrCbKE97jKPBMmIZ/tE3QkZLJWX0VJqM'
        b'kUqXMVMZroTeSi5z1JQ6G6TqxiRREkmJRPwXhP6Lk/bIkIqYJOM1YqJcjrCYI8JAvhT/krisUd2sLHxYmpU1qp+Vpf29NtQ2zMpaLRcWjveYZGXliSVSWaG4WFRcgm7o'
        b'ZGXlluSghmVWFi4wE+dkCWUyiXiFXCaSZmVRg2sLCCnOxUxcMGlSJmrsJL4wDKAg5G44nq6GhxwMjOFFmYEeiuuT+JLxiNYPNsd7spgo2K1K0m45OU/cEX+eLm1AQy05'
        b't1tevSTZfL7Fjqf18eJ49BG3cNKvTlssP6PkqNbd+PX92VmHPXISDm7P3fh4SGdLz2seTacZ003uvXuk86NPRzrXLDlf0aSpvKbZH38jt/1OnSqsShUReKCpovO3tL98'
        b'XH3zmycilzd2W5zqu1T/vf+APPlbjy+zzqW/e+rqrfC9d4xzanjPppqY/9zZHrr1Hwsuba1fMPrgze9kt4YXh7zFZy//9OmVr5sP1x8sGgop4sm48i96Gtdt7JZ224Xf'
        b'bvnxfOw/jqac/OGtFNHyRcfPLVUeLexQFfZn+PbP9x1Y8FPo8aVH25eKEtcfkn/Bon8RFlL78JLy6k33L0TnvNollWXf3s2+mVi8uqFqytqe96w+vvv5jGnf/VA2/af1'
        b'N10dpb3mR37Y+xC+vTWWvXzswMKrXxqVrH/n16N1PR9lvnP58hevf38pf9PHeryNN9fwo/6av/zx0n2r5uhd/ts7bV9vSY0e+qhwmYPRj+u+4Y64f3z+mtr4tPSgZ8i1'
        b'LTGD35d/6SBnTvO1rLjsKa94UJoWkrvs2Kez3o669fP6eZ1n19wNDgusvbeF0EzPtnu2lst4gp9V4qOna/gQpgqeIZETQ5kTPOVLJaAoUbsMjxnEg92gc9KvZGl/IWvJ'
        b'uifUkfA+sE9m4I3fLUAJKgaZA7opKCfQyYDt8+CJJ/hoLAmegaekoC0mif/8VGwKrEIJ4yk6UPsA9cSbCKz/8vL/+U2EWdSn7JWPNrtBilhYIsxF2pM+kdrw0PV3lNr4'
        b'EEaWYwwdPesRE7OqwD1rFc57N9ZLlYFKYQuuR57fuOW8m1rS49wl75nfta7T9425N81gzGBgwl0bO0WgQtgU3KCnjBuy8VVbD9mE9kUkDVkn9aWm9y3IGEpdOGi98K4V'
        b'R2lWU9xn6jZGJ2xQTKFPmFlUza61LJ/zlMHS83pqytBzGSPwxVCXo68xNKmyGqPjli1bkadteXBVIdqWIKSHpW3NiuzNoFr3KQwmblEYVIvCoFoUBtWiMHALuXYjU4Sj'
        b'o23bOSCs8banN8IbbwdNRZjj7dnkXBJhU990tdh62jaFPd7G2GpBD6uX3ptBLURhrshT5vyrNx+ZoGH6dNkoE8AzUPdfXMYMWC6o1/Gp6TyaXsiPBL6OpTAIfdMRPdMq'
        b'qSK4qmBQz+UpLZ2hZ/eUwNcx6vqYTui74ovpGIO6W6yL2k9opF5g43rkDvUCqc4f8I2fx5KNSb1YcsTM6YRhH3/eACd6wCymzzDmFym2p7sNo4yIutkCdH3LyDyKQ9ea'
        b'TYtRGpKs/5yf/FMpt/gT3/nCf6ZPXLBhkE4f959ckjTF7tP0J3z5d93nMVYg0WEwnS7uuXqPLi3Dg4v8O+fH5CbkxuUm5Yqzy3N0VzzJ9crWzdHNzuslAnz8D+m5bv9g'
        b'pXGecfY76bZvbj9xSG/Oe9sSVv6U+yj7/ZUHd2nePFQS/6HZ2zZvW7xt97bV27ZvW3rYeFh4sN9me9h6WHo4vG3mYX3S5mSuj82bLh9UweoPLW6fuN07QiPeXWL+1Vgw'
        b'V4d6iAUuwr2gY04x9cucydSZsg5hADpoUMVOpyA84Q1hfDIfnscAyXwaMlhXp8KtdHB0BlBQj3mKWTKwB5+449+1ANXgOqgE+3UIYzO6I2jPfoK5nVZq+fyNMnieR9MF'
        b'l/2e4MP9qZEsWAevxU/6qU8DLg1WgVMrqGdwW6wkYbDhlV8CdQLdT/AZyTq4bSnYu4IXxyTIeAIqfOBurvs/N6H/58+R/hvBdJ8wv68a339iisXFYhlSmGUTpjgaXf5R'
        b'Rjy2I5jmGiOLYSPHfiPHxnUDRl5l8zQM/V0JWxP6pjifCB1k+HzCcPqYYfSUlaLDDHxK4OuP1HUs15gwtChLnvRmhcsovVBUPMrAxf2jTJm8tFA0ysAVXSiuFeegKy4e'
        b'H6VLZZJR5or1KLYaZeDazlG6uFg2yqR+U2+UKREWr0TY4uJSuWyUnpMvGaWXSHJHWXniQpkIfSkSlo7SN4hLR5lCaY5YPErPF61DIGh4ulReNMqSluCa/VF9sVRcjIK5'
        b'4hzRKKtUvqJQnDOqI8zJEZXKpKOG1OyB2hK5USPtgzixtCQ0xD9g1ECaL86TZVGB5aiRvDgnX4gCxdws0bqcUT0UIKLgsxTFiix5sVwqyn1hhKiHf9n/zYfD0VqPZRMX'
        b'/HtF0mR0eYY+yICYkOQWOrYgL1+fUNd/x57gFOMNY9ZsR+INR4PZXPovuhO/rjlqigNgqj3uo3+xy3v5F485xSUyDu4T5SZxdSVJWIxQlCwsLByXIkkcvqWPGCyRSXHl'
        b'3yirsCRHWIh4myovlomLRFT0LtkyIRwv4udR3QhtYD5DsoPQZgfSBHQZo5Mk+YjGIBljhoSBUZnOD4wsHdJibK4JoTdlWNe+X9deETes63lH17PPZ8YbHtBr0CdOo2s6'
        b'om/VZy0Y0A/qYwSNEKZVNh8RdtRs/w8gAJdo'
    ))))
