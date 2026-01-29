
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
        b'eJzFfAdclEfe8PNsoyy9Ln3puywsZQEBKwrSmxQ7sMJSFBfcomLvgqCCWBZRWAUVrKsgYseZFHPJ5diskZU0cql3uVwwMTHJm0u+mecBa+57777ffe+7PxlnZ+Y/859/'
        b'n2f+z35CPPNhjv//3WpUHCByCQURSijIXNKVUDAWMeeYES99chlRJF0TjLdIuaiVuYjtQ0SNt0xGf6UIdhZjEceHyGVNQMjIRSY+xKInM/CJcrZZmZDzs8w8d27K7Dz+'
        b'8upSdZWMX13GV1XI+Nm1qopqOX92pVwlK6ng10hLlknLZWJz87yKSuXE2FJZWaVcpuSXqeUlqspquZKvqkZDFUoZf3xOmVKJwJRi8xKvZ/bBR39cvPURVBQShWQho5BZ'
        b'yCpkF3IKTQpNC80KzQu5hRaFloVWhdaFNoW2hXaF9oUOhY6FToXOhbxCl0LXQrdC90KPQs9CrwNEvme+S75dvmm+Sb5rvmU+K9863zzfPt8i3yzfOZ/IZ+bb5Dvks/Ot'
        b'8t3yefncfPd8p3xOvmM+I5/M98j3yreN5GOiLzWV8/M8nxJS7u1J5POffs/3flrnE/H8eG8/wvt3WsuIqUwvoow0qxAyMkueZZ8t+rPH22ZRHC8nhCaZVaao/vcCpqqF'
        b'iWvFwS4yHqEORFVwFd4Gx2ADrM9Kz4F1cHcW7IZbhXB3Sn52CIcITGTB2/D8CiGpdsejL4H9cECZYu6eAffAxgzYSBLmKQyggzc4JeQzSNhNILEFFdNsCxEiiEIEohob'
        b'UcUEUdEMUY+LqGeJKGaNaGeLaGsfaTdOIzLvGWGTMxCNyGdoxHiOGmQ8g6LRS61PaFT239MonabRvGQTwoI3xCH4xRblAiZBNT5ewSBY6W+zMOFiGJPoRqsNZoRN8Sk2'
        b'UVwcvGyNim50ELAJ0/TXSGJGcfBwxmyih6gyR81LpvJYj+wE6Wzi48BvGf3h7ckXiCqseYFuGlK3qsoCjY94X2EfL6Wbf/P8znq//T88Gdmj5K+8L/1ziBFCHYo63OFu'
        b'cAkxqyE0RyCAu0KTQ+Au0JMnSM2Ae4PFKSGpGYgJoF9ubTYV7IUnn2MJa2LPpZglTIolmB1EJPMJ0Zn/QaKXv0h0k5eIzqWJ/rdSK8KdGEhhhhVXlbpbEGoxFrVj4CQ8'
        b'gvbaKEqDjbA+PScZNpalBKfkExFpuY5gfx5oAGgWtgnsYCxWOyEQeAjchI0ScCUB9qA1QA+xAg4Eqh1Qlx88YCUBfZbwLO44SizbCBrVWEhnw7PgkCSiwAUveZAomZ+q'
        b'xjiCNtgALsAWNrEqmhATYnDZiUL14kxzwoHQhFrbFAe/kedMc/2guT3hR/zItSKKp1wWMYjKfb2zSOVG1LO/al1vSfsfbED3Kzag6g93Cc6dxoK3f/7MwqJ+nYWFPttW'
        b'y8s17RW7MZnpGUElpsqw3nwuc2tIJycvw8eeuZUxK4w704/tAw6/bmMeWeQs2Pem+1tOr7y1idx0MpzV27up4ofi2WF/5L11B2itV+WLlab2l0T5vBgDuSPFlnMiQMh4'
        b'5IGwECMlP8lN44A+2CjMUIcEIclhEI5gJ8vU0vSRK97ujSXwKqL1LrgXNjIJVqwn2EWCi7Vgq5A1whAIFZZo0NNCiTnI37Rp04jTlDJF9RqZnF9Gm3CxclVlmWraiDll'
        b'n4tKpSqZwhoNZmCoGlT8uIl4mEASNvZNUQ1rNDkNG9934g95xw3k671nGpxmDdnMMjq5aUqbq4adRFrVsJOkW1WXZHRw08ias+oSjQ7Oh5KbkzUy7Uxtjqay27F7hc62'
        b'21WXPxA+kKNbMOQxw+AQX5f4wJ6vdTTYBw5ZBH6HJU+BRU/IGWGvlFapZSMmRUUKtbyoaIRbVFRSJZPK1TWo5YUtcrCd5ONNKqxwo/VE4Yt7I1Hx0ybi8SySJO0/tnJu'
        b'WLaJO8Zgkw4PuHYNsR+zrLdlGE2tH5ja//iQTbBtJr79rMTy0sLxJTq5YmYJ4/fUswyrJwP7K0pByWcUlPGcVWR6Pqd++cznVJERz6QU9KXWf24Vn6DwREE5mZT2wD64'
        b'FRyHe8NhC7IoIUQI3OlAq8nZathBIMFpQXFGKBG6ERym2uHAtASwuRLrD9YeuB0erPy7eidLieOGznu5tFI4vHJ308k95BaXra3prfy/LTppM9uye7WPKHtP7LYUZ5+3'
        b'tax71ebvXgCDrVaEWS6nSS8Sko/cKHyy5KLUEFiXkp7JJrizwA5wkQGPIiS7hMwXGYkjoAkujnBpuSyrqpaqFM4TghlMC+ZYHkk4uh7KaM7Q+mqVBgdRXeKH1g5GHhK+'
        b'Vm4T+4G9qyaqZdqQhbfC5qlQKbAvGWGXypZUqhTYoijsf0eQKEmiBcl5ohBNCNLPSJBykSC5/ruCtJ/jR3RxQ5mUFTostiMjGYRgNGDKSg1n7RS1I6ZUy/qFSlU0vLU6'
        b'jEUwlhAQ2VRParjjVEcyhkHwRp1ObpwnhrZqHh5+CbF5JwIAHeBUGEkwZATsAe2TKIjEuU7kFAYRM1pmWKJxEMdTNncJbAF9GOCsIoxJMMoJeKYSnKXGf5TpQs5A9B3d'
        b'sHqNkTiYQ9voLfCoQqmaBJvBAEZJTsDT65XU+OSVrmQCg+CPyr9ewgtKllEbsFkHd6DhAW5hDIJRjWZHfu0CNbzA3oNMZhA2o1bbaoxW7wZTG0A+42atEvZFgd58jD/Y'
        b'SsBeOBBKQdjO9CLTGUTYqJXf8nnh92eoMRf4QeAsBmDDpjA2AtiGpf1MOAVgH+9NZjMI01Hx43Xzyr8NpTBCjqkH7FMqoqaK8AoIp7M+2dTwwWgfMg9zQF63RlOjT6NJ'
        b'uhnUwzbYqw53h114x8hpwd4kEwripKMfOQ8zYdrBak1O9nIa4lYoaMAAS6biTSOvBPtAHeihIDYsCCQXYSZkGjbOU6+RUEQFZ+BpcE2plMDWErzERgKeD5xNjY9VCMhi'
        b'zISUK5VGIsyVWiEK3oCdeAVvU8w0cBgpLDgBNlMQrpwgspRBzBit5VXx/BMt1JSD6A2HZzAEcosHw0wQTBuBPMZpsJ2COe8bTFZg1gkX1PCKXKU0VkeBBuyBvUqLONIc'
        b'bQReJiOry6jxxVwxWcUgikdjLaVGx61TKCsTXJXJVUSbVVNEOknAK0vAaWq0X1kYWYM5XZm+hrfKPIriGxechT1ceDFqAziDIVAoygQDsyiAG3kSUsUgskfNLDfMS/42'
        b'nQIAA1OAjmseAbtAB2YcPEiazQUn1C6UmsCr4BoX9ofDk6CFmm47Sc6DO6iNeHsmKGHvKtgIDljhfRwjReZgHz1pK+muNLMEh8FmqMOT3iajYf8CCqxsHTjAXaFmIAHs'
        b'R4YGXiT9HeElmsXnwGF4SclVIEY3qjCchvTMAdeoOVeAPoFSBa+gsHwzF/ftJkWgOYKikToWbFJaWYJ9eYiiTDY5NQ7U03p1AB6EZ3FXnaMVSTDNyBlh8Bwd+ziKcfsO'
        b'cHkF3tgAKU6fTy00E7aBTVzLGnALbAeNLILpS86AHQtpwzFgE4FkPBPWYa2owRhfSKKmW6eOxPp+QhzJIVC0B3tgz0ZqOtiwGrQjIQQ7IilNQqp3CTbNpOQHHgGdcLsS'
        b'XkTEaAH7rTEZz5ORoG0lveUFsEkJ+2GvCWyn+k6TEhG4JbSm2NknjCJXY711ia7meZNxVKNqUjS5jkHUjNbuWclbuzyCatxqGUNuwgrrMnf1PGv5UqpxRvlkchuDSB6N'
        b'TV7Bm/KWimq8HDWFrMO6Ov9jqTFnuzstaMxpZCODqBg1k8uNkzamUI2m5AyyCeuoy9V1PHZiBtX48ZSZ5H4GMW+09mQFb8lXtFRHxyWQGqybQvlSjc07uVTjUUESeYRB'
        b'rB6tzCs2cvpoS+TOTCG1WCvV/uXG+LNrqcaVhRlkN1YitVhuJGcvoxonr8wiz2JNYV+t0DCjIqnG32ZkkzqsEGp5OS/olB/VGJabS/Zhofc3UcwLswmi2FhoAQ4queZQ'
        b'B45jqbBADD6US/VUWsNGrsLKClyyRJJkS04FW2AHLdNNM2wQm66sgi0ByHtimRbJ4VZapxsmqZEuKKcrYB8Wzf2kD2yuELIoDDbPeZ08wkRbFdUt4ynuLaIahfPeILXI'
        b'B49OOr2RN21GNW33kv5AdjGRjQncXK2xHKmiGvdlvUV2M9H+k9as0Fhfn/bc6cVsIjbBQeQ0s/EDJT6/PD1MEpFmT04ynP+fx0cb4sVAaXqm2huTZ5fvDNCQhc7Ge2F9'
        b'SoYY1qNA26kY7AWtrEDQBK9TG31fis6TCa9Q58mq9cn0IaIh05SwqfIjUaxQ1RaXTVB2qRapV1poGtyTlYIOlnAb1IUyakEPbKGt1lm4pwD0BoCLoA/0sQhyPgrIkH88'
        b'R7FxYzC8JRKgYL8uNDNsHZuwKGdag4GVVHwmyFkFetH68Dq4EkfEIR9fp8BIUJiEx6G1qnLZ+BBrVhtEN75bwiEs/CwQbYqDr09bQdCucCfYbSkJw7V98Bq8Rkjh9SS1'
        b'D0atV7gxjTpO7MUPCtLA3tCUaVADzglIgq9iW9lVU7YkqhjqJDgEAvtBMzxPLNkA+9T4yJLqCa6L3JahMy71lAEdeFNYhL2QCRsFYDMtiZfMQZskAtcOwm3gIlECtKB9'
        b'XEgd4E4JuISPeh3wPLhKVPHRvHjjEh5bIsFD2s3BdaIcbEdyjds9zWCrRMKhvPttObF0I6yjdrjaBQ5IojGABpmwK0Qp6EKLYAzhtQ3stFSMGrLhRzJpFlnVMGPgXnCO'
        b'DoKPKDiSaIxEazQ4QshYoJOyhVORr+lIS0cgoXC3aC04ShLcBcgcKicJGdSZVJriLYlG1gF5lfOgjigTTKbmWw6vuEmiOdThtB82EuXStdR2p0lBHWxAh+QMNgHro1me'
        b'JDhuY09b8bo0cEwSjR8KHAHa1UQFOA2Pq3EIPQecny9KQfyA9ZngHDgAWliExVSm9VRwnfYnt+AWUC8B/XjvWnOwiagCh2sp55UCm1FA05Ceio+KbAcmvEWCtip4TZ2F'
        b'x3YCFBQo01NSMvDjpCeHd4FYGJQhFoYwzMEJGYrSToIugQD0OImEYD/sEjmA/U6OsMsZnGIgJXKAu2baIHa2BVb9+Ntvv+2wQAKZUI5ikuKqgsASghIdx1jYI8oMSWYR'
        b'U0tZM0i06rFioQPtiPbCOrBZaalQMwnQImPAdtKXDzfTnnePrTnstaK6muFOBuwnhWAfOEIDtsCDc2AvBZihYqCNieBxSHt6eAtcBqeVCJJEUWYKNn1e8fAqTay9UJeu'
        b'XKE2R12Xkee7TvIjgZYCy3BWIse2CvaxCSQ653CY4p0Ie+gwjAnP47iizxLBIZnAIUJEAXLouHMBCslucK24YC+iyAm4m7mAXAgPAQ0lIRHlyUqV+SoWwecwwE3SvSSK'
        b'YrcCOfQDuINNxMYy4GaSD27aj8dv6AzWB3tVyG4ziXzQwwC3SDcUn9EbL0X82KoEneXwkopDkKAdb+ngdFqbupCab+GaWpoTRDa8yZxEJjORiaEemLSDC8j/96pXWCDn'
        b'Ak8y4GEyEPn4PRTgesT5fVwrC2S6YQeXOZlMgfuQClDEbKxFB4FeawWKp+B1eIJpRU6C1wNpmd0ObkagPogdU8kGpg8Zv0BAkUSKIsptyhV4McTuRgboJz3hbnCVPqPu'
        b'2CBTmmPO8TBb95F8ko5XwDYn2MWlemzgHqYdGSaZp8aHtji4IwO2cLBMVAcTwYviqT1lIlu6GzRYm69YSaJQ7DQLxSlgtxAeopE7BVrBLXpToGMS3pRsNoVc0ArQNS5Y'
        b'8DCspwXrOOiiBWQgB5yhsQNdBIUd2JxKk+I4OJw5LnOr4FlK6MDh5HHUExm0xPnDY5TEMaYIWbSTPpc5Y4KdKi7NzQ6wlZbxY7BLrATHK57hJnJBbZTiu1mB28hiXUFn'
        b'HjWyF1pQxwLXSBS+XlhCSUoqOLkKNKyC/RagnkVkgAssWEeiTW9eI2RmZtJE2BkONk+I5oVSLJlcL2qftSZom5T8gS2ghZJAb7h3nOXgGjqjUFIrRWqOxRZ5NKEVtdMF'
        b'th5cczN4CRGvO5MZRybBNkcabHvWLCWtrrfBFhy0e6OzUDulBaJUO1rJ49IoHS/woOxk0oISriluToUapjkpzoEa+mzYGYKPIxa4ywU04wA0EOF0mdpTRE0kkmMLBWIC'
        b'gwFPoJ4LSBFxj4eFv9IK9qMoHRwhGbCD9IuEp+kJr8lykHJzsYBfA5sY8BKJzsHwwvjJAG6Zy1XAy/Ayi0DUxIwVRyjpvouwAx1eKJWCDfAW1imwbQ5FiZA1DC68bLaC'
        b'Q9Qi3gaSsbA9nwa6YQmbqS6SQLH+eaaARBKcRCvidtZqJdhdgw8asB+cxHsTgl3IVeIpC/wTEZo11ihet2PAejIA9vLVIZi4h6NRNN6A/vauRIjr4H4k+rvAuWgUYhyA'
        b'h7A5nEsSvoUsR3jKmqKtDbgNT8AWEwTbCRvCiDDbcMrss+DhGWj4IWSh6lY+P81+1NqElriE/t8PdOAKamtC43aaoaChEZ5Gzd3gTMVSBraBWjPQGoU0Gm/YCxxdP05e'
        b'dHjYSZFXhmwLdZ44BK7CSxPkBZ2OFHnBNXgF+VAsifHzZONkhDuQWCE6oqV30cp4PhgcHCekdzlFxlvgijqRit/AGbCDC3enIc+YnCGmnJgI7s5IBf2zQ+bAuqxcgTgj'
        b'FTk/uDtFWJCM4pI5iGx9yrmE0pEAOzJtpjHEtNVsAf0oxkKu+sScbAZB2hPrZ0L6kTPo8CNykXtPh/t9CV8UsbVSEDUuyOeOazRomUSptE82pbMJ3vDSMzrbBQ/QOjsb'
        b'9FGgzCzQOc5hc9BHs/iyO6KEO20NdvukiUOCQOOGVLyz8yzCuoBZhezuTmp20BQHjmI3vRvHIySKMzUpoJcBDoRXUXyoXQv2oBA0OTg1K2Tteg7Bxdq2IJM2NbvAKbCH'
        b'VlAHeInWz2PIPXjiiXsC4UERPA26UjPSQvDamWzCDrQzEStuk5WenUNsZSY6GmS17tmdP7/aMMPmw8tH4VVDX8rC1IXvtPgmLXxny9opm/gf39m25pKA4Z3T0z2Ff2bO'
        b'9h+5vxBNTT+SpvUdg/Yb68o/1HisnZRZkh3y4MOjR6v/3jr10vTeO1Xb1ecKj4Z3mHGm3Kl59bM/lG3Z6v24eFPlG7nLmKu+De3xLLfPCvylesdvhuDj9uaxwfFzfr1+'
        b'47eCtPDAEzNOw9c/O7L/wV1Xe03i9bSIvfyv/QNOmJ3vOlbknv7tkM37aa+Oue5yrupJ9AmbduNQUqMwW1LatPTjoFlfnNTxv7LQA7+Rd3Yc6Xv1aFKK06e+jxj64fpC'
        b'1QaOatEhd5PO/Z3q1i+5fe37HrUEJU5OWXGp5GzUgctvvuVhc95OH5sRV2S/PmDmBbt/eOiX/Vf6V60397Xv3dbmW8s7EH/CMzZJ+J3fP0QrFjdULOb/PCnldupnLEG8'
        b'+pNfZ06VFK60Yw9vf3fG283r4buc+cG3NUfD1iz46z3Bcd3qCvc5id6T1iikhdmJVzee9/xevCqtUbbi3YMa//qdsunkW1lBLo731+7q70r4w5uvr66ZlbJ279GaX09N'
        b'JpZH912O6sn4JtswZvuZKM12sc97W9v7fulq8HZI+aCWs0aR0M5al/L18qVvvVe++R8Rym9V2QGWiVfn9LHc3th8LeH79w5v3PXjpNnuheGvvXngTY/1C5qM8yxFDon3'
        b'//zz4ldXWX6kXjdpwY1Xi7+bt6Ha0+SLK2PLBpf/HPTW0TLyO5vptuAtQduNb/32nk6aPrW79gBvr6vPB+Hin7a5/M3176umLN8VmV/suuDWbruyAH+L24IbHbYuhyNC'
        b'QdDqL8sTfcR7jLlftr32GcdgXB879aNvfaz7vzP77uHW1e/d27jw0q4/n/RY0Loz3Xfrh0H1dxoXvvLTUuAj63XayVzovWXaV9Pjly/sOvdz0fIfBvo3MFe8t4bT+nBk'
        b'Sc1nG/8ydDFMGN35xv5V07QHZWevzTl6Z4/OavXmO4srXiuoe812bnngsR+qf1z9xc0jBt5Rk7/9+Lompe+HX64I9qhLvd9pVv1WP7Pvh8Tma1dNry+99dfzRsuftsRe'
        b'y1i0dl/Dp3G2b0/9afkbk9cdXL1WunNhzd6ud/LM/v4oPv81wUDO939cdbuSf99Mnj98InUkMCMgp93wKNb0T0Xsd64fvO509m3N+h+cdXvfkt2oFFpSz8iRAdKKYENw'
        b'Joq+4d7gKj46ZYAzyDEss6WufNbO8haJU4KDhGLUC+sJgsfPjWIV5sDD1J0ROlLsA/1Pr4TQMecWK5ZER81T8PIj7HNClpmKxCjErw+m/FEHB+xhhCAfcOYRNho28EJW'
        b'WrAgGSk9sijgjALsZ9TmrX/kRIW2V3LSUjKCMkxQ6AU0HBbDFAwEU8vCTUkxInDKOjk4CE0M65FV2ssk7CczYZu/6SMqJtq3gpkG+tZnhZAEYyUZj6IuHYVP5Gp4XCQW'
        b'wl3BaFAj3MUBZxkSfBJ/hA1VLNwphQ0ZwSlwD+WbD3IiGVbIOj3ChgpFxnsXpeG7xrQUfFxBFmw7IlcpA7blgTZqP6L53qKgie2aTQ6HyEB2LEoYv1+rm5ZWGISMJ/IU'
        b'IanB6CBoBweYcCeKVPqFLi9cSPzPFkpMGv4Ln00TH/pSxI6+FFEppHKllE6xUODUD+puZJRF3Y08SmAQLv5NLKOzmyZd7yxENQeexn3IIcDo7a+VHnPutu0O17o3sZrm'
        b'NVvhQcnNG4adQ/TOIcPOoXrn0FH/oKYEDa850xgQpHFpyTI6umgEzYXDjmK9o7hbOewo0TtKRj19tOGt5VqpdolmGRpu25w0PnyMQ7h7dkxqnaSNbJvalGB09dSsaA1s'
        b'mmV08+qIa43TlrRN7w7vjhhyEzclvO/tr2Eb+f7aJdoVWjO6imakqm58bULbVKMkRutpcA8zevhoS9sWG8OitG4G9xCjp69W1bZcxx5w6LU0+gm78zozdLIBVe9yoztf'
        b'69KaNeweoXeP0EXdd4+dAA2N1Loa3IMnvoolWpe2LPytyuARgcGcWtOH3UP17qE69n336PFxH4vDdf5nlmoSJkZjWFGY1qktHX3rWNy6uKOotWg0KFTr2JY2ZkV4+Hak'
        b't6aPEWRQPGmclfyQSQalkI8I0iOVHPULPJam89f7TdIkGr18tSkdG418P+38Y9Y6hoEv0an1/Cnv8iWjdNswP1rPj9aph/lTH6aQhE/AWDpJ8H0Q2wqaLcYYbFe7Js6Y'
        b'BeEb2GRN7flIFiK2IPiCVY+VTmkQTNY7+DclatkfOru2q7sdz3ihDWsKWi20+XqeyBgUetj6IxeBxsvIc6daiwy8qAEHPW/qu7yoh5aERzDaCpIas+bpQwFxBvu40eAZ'
        b'gw6DlXe89ME5iN1Ozela53cchFg2hM1FQ4JpBsdpiMNaTuuUYTeR3k3UPXvYTaJ3kxhDEwdL78beqdaHFmhY1FoFel7wmCnh6aOZbfTwflL4apJfKEbcp45g1tPd2jxN'
        b'5pP/JsAeelhThOATbh4dga2BWj9t7bFQg2vEsGuM3jXG4BrXZGK0dzwU0xwz5C7WmQzbx9yzjzF6emuTWpc3JRk9k1Dh4dWxoHVBt4nBI7Zp9vui8FZrDVsrNfoFnUo9'
        b'ltqt1ql0ZQa/qRqzBwJRd8oZK42l0U3QHW5wCzZ6+XVz2jaOCkIucHu4ulkDHndt9bGpBkGalm0UhHSXdCu6zXX5AxEX5w9HJeqjEgdL7oYbojL0goxjbKN3QHdAp9fv'
        b'AFN9Q0FxBu843GvRY6HLHQi5662PSzMI0o+xn4AYBDFa9gMvH21U25ruxQavuJGA6PcSU+/O+lPyG8lD+QvezhpjkjGLye8IMrCQRELpXUiOPiMHn4oidfPvi6a3pmni'
        b'P/IK1Kw2xk4dKLvqPijTx6bfzdHHZmlZ2oJjFt3zkCgafUXdKw2+UUbJpAHOxSmDHL0kSZvQ7dSZbvQP0Tm/6x9jjIwZcLqYPuisj0wZkqTSnUiagmeQSJzcvbWz26aP'
        b'BofrvHXx3akPgqKQxsYPzNRVGoJmPGQzQz2xkh3JwqLhqy1rL6KU/Z57yKNEkgiO+DYJnQX9n7nPtRixeM4O/s6N7r9idS2IieyBZwwtZVSpYhYeE0uM5xAwSNL1e+L/'
        b'4f63lSMkeriRTCFJnxAb4Vl4Li0luBjuSGERLHT0b4O7pM89R8fYUY+ucT7gNMvx5+g4KYt4OS0r0vLJ83TWf/B5egU6maSgo695NvY7Sr70+Tw+KjmwtkbGz8iLjQzj'
        b'VyuoSoTY3DxFxVfIVGqFHMNUVSpVeOgSqXwZX1pSUq2Wq/hKlVQlWy6Tq5T8VRWVJRV8qUKGYGoUMiVqlJWaS5V8tVItreKXVlIclioqZUoxP75KWc2XVlXxcxOz4/ll'
        b'lbKqUiUFK1uNxKEEQeIxVeZUAgndU1ItXylToB6cjqiWV5ZUl8rQ+opKebkS4Rr/dIVafgVaFuc7llVXVVWvQiPwQHUJ2oosztw8BO2xVKYoUsjKZAqZvEQWNz4PH8X2'
        b'ZWj9cqVyvG+NEI1+eRyiUXFxZrVcVlzMF8yUrVGXPweASYTRezrvTNRSJatUrZFWVOER4/R7OiCtWq6qlquXL5cpcD+qLZEpnsVLiRd5OmCJtEqKMCqqrpHJ46ito0Hy'
        b'MikihlJaVVotNMeBB1poOb1OgqykcjliA8IWb3Ciu0StwDurfbrSXNhVoVDLn4zAKUVxVIlg1SUVqEuJvqmXP4tFSVW1UjaBRqK89H8BhSXV1ctkpeM4PMefAiRDKpmc'
        b'wolfLluCZlD9z+Imr1b9C6itrFaUI11SLPsfwk6pXl5UopCVVqqUv4dbLpY1fpJapSypUFSWITT5obRl4FfLq2r/YziOK0KlnJJgrCD8cVRl8gk0qWyf/wuWM2VVUqWK'
        b'AvnfQfJZHxb3xFQ+a/Oe6HBNtVKFgcY5JFOWKCpr8LB/Zl0w/WWVS57BBltFlXSCsXORVURTVlU9w92X2P/8nM+Lwr9EI4UMWV8kqHF8pGmodw68UbJsCT3RxBisg2gD'
        b'Rctkz5ByYjG0jSp4Q6mUVb04XIWM/j/Z/DgsHvEUkZesdppaXiqTP7XA49Mjm/s7Nv75BdCYF+HKVz5vu5MwB2BXmUqJNLQMOS3cPTG4RoGIhfRb+vvzZ493y+QhmQrx'
        b's5g9t8ZLOD31FePMecFfPAfwnO+gx1eiJX5/cMrM+MznWV5Uragsr5Rj1r6sX1njfUsoYUAKwJ+tkC0vXfWcfvwLAvQvK1qFFFnB31X1JNkSeAOpgvw/vigWL0pmsX4/'
        b't2Ye6nlZcOXS5bKnWj4eg/AFmaj5iVyoFTWUT3xpVIFMsUomL8VivWaVrGTZBIRSViONezaIQUDPREfjoxbK5Yvj+PnyZfLqVfKnUU3pszGUtLQUNayqVFXgIKhSgaMJ'
        b'maKyhF9ZiiOluBqpQrocmwW0Xl7FC291iM3jxmO+OH7871oysflzyRnWxIvJGXl0mvnhMGZCIP3+Q/o3slI6r2H6Btbq10gU/88otvg+MZxQh6NGSTLoBg2gF+yKhk3g'
        b'MmjEdxmnwW5U2UrdbjDC4TlwjpgCz7KBFhwopJ7rl7mh/l4GfjkmIHwy6Ae7qRU+qeaImxg8nDmRrvTLIujE2Vugp0gSoZYRdNo52OdCJZCgAH6nUCRMhY2izHQx/fxL'
        b'xCFgZ4y3F9vVEp4WWtL5Fd0ML9iQnJGeEgLwEzo0MC2EQ5SzveaxYBc8BhvUfmjYDHAVboYNoal4WOgzT+HD4W4O3C0Wgc5COpuhzQ72iCYGwC6rJ0/qrWEPdUsA+53B'
        b'DTrhIRPuWWYzke6QBC5T/X6gE3SlpadWj+c1jCc1wF2wjrqimg+OrYMNolWR+DYlhEGYwqsMsGs2aKL30x9XiydPQfvIBLvh3tBkuJtJwJvTvOxYUAM77NV8TKqG7DQ8'
        b'bJL3+ECcalMfipD1E7GnWCvU/mhQAOiRPTNXFp2GkplBEkJwA/blsMHhfDZFHnAeHgQ91KY2Bz1ZGieboMF+xewZk+FZal2/RUAjEsPdaDZxagasDxZyCDfQyYJtLNAJ'
        b'T89V4/eOYCcvBA3ah2bFA1My4C48ztmRFQY7YRvN30slYM/L/FXBa5i/4fAk9e4DwmEXOKOkEvXnCPCzUJxDMxfuW4AfQKJqfjbczSLmhpiAAxmrKOGrKAZ7JBHwtjXO'
        b'NzlElE4KorhSCXd6P2Er2Ct7wtbCcPqGeXcO7JBElMFGNs4rIZBl6aNTew4Ew63URV8YAY7AnjC4E8kUvk9ySQDHn8jBfLjvSd7LNVBP381dA0fXpaUr4OnnRSFNNJ7f'
        b'wvBMl4BLNRzCroZMR0ywFlG42AlBI2ovW4iXbyeWwVOwlxa91hX4TRBRIdzxnPBYw04hhwK1go3xEkkNE2ckNZJpBDgn9aWv4Q4kgA6JBOrYBNDCg+QcAvQtsaRgMtdA'
        b'jUSiQELWLiSzCHBhHtxL3w82whPRCOYSmxDBerKAAP1MeJ1S2zzYAc9IJGVCnFFznFgGrljQqT67isFRiSQWNGEydhJVKT6U7rdaODlMZszDuu8ussskqLwDsH+9qRJN'
        b'kIgvPLsTl86lhtpNto37npxBEDXFVds3zCGETPr27jw4DBrTYKOa98z9HAMcgLdmUsQRIGG5ga/3EIcL4fWn13t76HRleN6pNi0FP5NmscAJAQk6QOssxAiqbxM8m03T'
        b'7Qw4SNGtNoCmWzM4HU3TDW4Deyi68SIp9QKb0IpXf09Z22Evpa3gfCVaANMY2XOKxODWPIrEsA/soh9VaMBmeIUmMujxp4icgSwJfrkCXIN1tnh+Bjj2e2oOezdQYgSP'
        b'sIBWIlmzapwZcjN1ADbDKqj95+rfyUTqD7p4dM7IvmVwv0QSDS+Psw3u8KHMURHs86VkfAvY/nt2wdyZ4qSJR4BEAhoWU4lmSAVdKGNhCS4HpKWEZIqR/gsmrjDcvLPA'
        b'TsQAeDuCUhJbeFUgSgPXkPloFIaksAgzEwbYAy7Bg3R2q9y68HMiBmlfcRUxn0VQTCkwBwcmWAkbQD3mZZecst/IX/WDc0hMwMklL8jJ9XRqQTdwGXaJUkPSQoLCwZZM'
        b'/OaedTlTBrtzqfcAYxHHzz+fsYeIBs6xCDckggPpLLAPHAUHKSNm6iB/MbePSuyDB6xwbl8ym2JjMDJj4wlye551PUEla0A7GwlcQwydRXHFEx5PC5UveprmyKi1ASfp'
        b'fbUE2YmeyQIEDRkTiYBkAiX/HGRuWiey0ZjwFjwH95GgDZyGp9X4DQtwBvbMe3K7DeqRtMJd6fhSKw3TIAIc4kwBR1JgO2ikX3HsgqcAcoF74JEN1JX3+IU3PAm76FSq'
        b'2wofUcqapRO5c3TeHLwFbiCVxRvKd585kY7H8kRUv0iC46AdbqahL8B9sSIBuAS0dGomnZgJ60Mo2YH1M8Ah0JC1DhmaF5JIWYHrwFZK7OBh74VcFGfkErC5IBdcm4m0'
        b'DbcvDuCP25UDvES4F7RQQp4XM5WrWABv4kSnHpwseQCxERutCCQc/eNv9CjgkZANsIGSvUCFqRWH5OO3VoIXx/nT6XZCuNcFJ3gEZyGXAPYSRarxxBl4EmwnQG8Y2C1n'
        b'YjkkqkH/LGqraeAsvAxbrK1QecAEyewUsI3Mg82wX52HAa+Ci0HPpVpgZdkL6gHyG7tzYV0K6guF9dk46yKZTrnIyQaXwnLnJAfnPOcIwVlLmyxwBUUa2LakOZqO28PM'
        b'8ifmcFICrVci8zJfUkAQNsVV8RvjiDzEM8rmb0UuLm3CXXGKTJWMoHAG7c5ukcvG50NM0T6ZMdWNjpy2eFCKFwZ0LyjeduQPqdtF7RR4AwUGHYgOLwYGhfMptO47WhTe'
        b'ZoYRRHZx8J7SUoIyQkijB6pfjjrqkAHGYQdoCVfPxcOuw6Zk5XP0QcTBb4iKQwRIwoLGMzFzMXnrgguSsWBRqZ85ydEvUfL2Wltk686CrVTm5WqCZTWHQUXHwZ9slBO0'
        b'jF6uhl1IRkF/ycsyKgFXx20/vBLmAnojkZuHPWvIHORbVofQKV09WcjxoR6SCIVXsWtBUSK4qsa5vP7gKAe2gDqcY3oQRdrPJhOdt45jg0tL5qiWgMtRJCI5B0UfURT7'
        b'fMAWhBI1JTwRSk1ZA4/TnG2HZy1pPLhgO4UHuBEiZFGdU3mgVRK9Avmus+AimYoxuQF1lHcpArsDJJESJw4VT8lEQEspja8AtkkiV5JELNyKvDXoEfpQaiCDumi0CtQh'
        b'ixSC3dmlbHBTSNJJMv2ITtdQLzpbIBt/kpyNMyf7g9QzcWedYh3SAtiAxjSEwr25UGcJLkaGZz8R+TkhBbTEo7DqGVYhu9phDg/bK2k13Aav88EZhO06/JLUhXWooDN5'
        b'bXyQSp2JBhcZxNJkhhMBT4OBcUPivzoInEGubwOyojc2wC2W44YkvhoeGH93L4QnrkSaTlGyFR4JRcw5Z0sBwVZkW9NKEQhlqC/CHtA3rifLweYnaoIs7nZaUc5ArRXi'
        b'2mp4/AVF6QRnqCMCE0Xj13FCbL8lfrfgCmhBpjwS9K6kc9w2gaOwbyKRDdajFY+SAXDbRipzXY3fLIQnQL0pNzMD7g4pGNcBWD83OTU/OY+mKuhB1iQjRAxvZmSmZ6HQ'
        b'4xTUmYPtM8D2yuMXN7OVq5Env3DD61xBWvV7s20Kp0UfDxb1p7/5rWiDYOXfIpv33y/wTN3/6MAf1uvSY/wGfSq4ZKqiso6oHMq1jn00xIoPXW499YcCh697Dv26qX3N'
        b'X2/fPTb9eC/8bJ9TjzEkiOz99ErvR1NWrjw4fOaj8I16w7y/Dx/4ZOurVg08XTLMeV1PhET8I7HN8sc7exsT3y+SX9r0X9zFUwsviuZahbz2yw7NV6m/1pm8Lwl4D9Ta'
        b'Pzq4OoLZPtbYNHy1cZGb558usJk/vR5s3fhxtcXXa04w1tvv/7Xk0Wcf/+OueWrNcefjrx+qOXDyl6LEtmVf3ub4S2Pql2xlvyX6opUZ0nnMxEn3y204uHTuJ4usLB5/'
        b'cm+ke8v9v2ZwPhusOpp87oN3h64Lv7XSj5nlrRTMfMz5s2GbLzuP+dXpR7E680/OBzTuVX8sOvK+d4d09rdRTZNrz3s/Dn74avQyuy/q/mT792NXToVNcjIOpocv9UkK'
        b'+2jyjI9kG2zPbV0esfFApLq7LUg8r8Jt/0+zX3vb54H+g9s2RX8YfdPuN+bDA+niAv9fJ//5lOkks6KWH0PrLnDXaS29wlZuvsPRZUUZ93tWDqVPnflL5B/lze8H1O74'
        b'1OoN8zcW7ytPuTXzW783XPZ9kdwe+MDngdMl+IpX3PJPTjod0CtyS9888+ljYSz3tLlbo7A6VnZNqBj5Q15p9g6DzxJdp3CV+UfRtU7LZ+d+nDtylLtklc1HTqt/tK/i'
        b'9nUU3BAvdV69q3GJ37SWA2OV2eEuN4JWBhy26vCYtMM2iOP46rfpeenbHia8O/bTxVhd2ysjYwvmfB+fr/iV62nb2Rv9mr/ug5TApKV/Pb1s9Mex7d2/jlXn/0VmPP6d'
        b'38rKPzl8U/7pf7XX3T/zea206GjyVt6XpUmSH/tEfwr4/igozM1c+8cZygvFR1cJ9xWteHvw8G+Mjo7cBAn7YGjAmfyCaZOvVSf0/mp+/+OzcXfUl/Y9Opf2yfo3i+xG'
        b'Bntv2pcsOFlV6LQv7m7wIu+uQ5/ane+3vHc9QMGP/WHPp1+WR/lB9Z3RX9M//OCuOr918eqjn7rZS5afaF15G0y5nbL+L+IPki5vWXdzu6jUL2f3LxdqV25ubx87PbDr'
        b'+3tfpzQ7ffU34R67G0e/HvSxvyernqOu+eueFYX3H9Yr/ib+5JfJDo6XBqJvWd57L1L2Df+XdUVetw/4lBTHlf3wmvv6hCvynFdvtp0ZsPrLfa7qI7dhj5D0e+unv95Q'
        b'bvaPa9tFj8A/Pm1tKYnz3Txo4vDNDxtvf9P7UdLdnzPWrNm74rbX6YQbHo0/vu36a2x427uL7n3UIv9Edk37+FbiHwO7rj6KyKg+UbzS6wtZvoc+8PNf1I25nfLwU2e/'
        b'O//Lt70P4q0v/y3qiGXVtZ6axsmxssFdn7dMC7od3r0zKODUuZKMP8Gdf00bXRYTGvSg0nd4ygDj1IXXGiKHj19d1pj/ykNWu/IL+7/2u+1caVI0enBGz3d/Ng7/V9xP'
        b'ry00Xvdy2av6+eTo24fuST+Rv8f/4I2bvguXvf+TdA7b9Pavp755e9Zj//nXj/ZE9r8a/eDou6WyessvXgna2Dv/y/nXvvX8yu2rv7UX3PrNWnEzysICCq0f+VFHSdAE'
        b'+kRidDDootKNkMkff7rjDPpZySi+baIymiqts0VB6Fy8czznyWw+A5yYBw5Q6UolYAfsfZLvxIkUwF6GVVUkBThfMO1J4hYH+aMOsIkRshDeprKoQL24KC1YDY8/Td1i'
        b'1AINPPMIB8cb4I4E2BCcAE6Mp5VNJJX5Au0j/AzEFtyGJ0VPs7dm4KdT4wlca8BhahJrcG0O2l9X6vPZZ6xC0B5G4TAzFBwQZcJ+0JMRnIrxNwVXGas48BKVPQZ3Lc9C'
        b'ceGu0BC0sVXwmDlDXAgG6Dyu3fCCdxrCG0+LIu3t1NTWYcxyOAA2U5sXgC3zn4nzwHa4iRGkgG3U1IuSwc2JFDIOOJu9iCHhQxppFBTdzBSlIrfT9OS9c+ql87lgF7V2'
        b'OA9eQiRvBI2wPw1FVzUTP7MwhcVEp3mf/9UssH8veQEHny+mjD2fN7bpxRfql6tiI8MU2AdTSWNvmNAv1BebEg68Q9Obpxvs/eoSjI7OdbONDry6RKObR1260cWjLtXo'
        b'5FyX9D7PvYn1wN5DU6pNHLYP0tsHPXAL7GYZ3EKaEozObofWNq9tWd/EMrp6a+NbRU0mHzq7PXBwf5KBI9HlDdvHvWMfZwwIOrX02FKdvU5qCIhpzmqK18hGnd21rJb1'
        b'H7rxH7iLu9W6Qn1owj33RKO7T0dGa0a3/z33sNHgGGNopFEYYhQEGwNFaBZjcJgxJNwojsClKNQYJDYGix+6WXm7athjnoQg6LDFhx4+DzzFQ6Gz7zrrQ7MNnjlDvByj'
        b'i6fWr83DGBKhWWbgBU18dfPU+rdNMc5Mel10R3S3xDBzjt59uiZRG6R3D0EYzTeETh8NjdQKcR4ZAgkxuKAVQzUVbdbo65BPqsEl9eOAcJ3/AGOAqQsakA3GX62463u1'
        b'2hCQifOBpDpGN/eBH95cjm5F9xqDX9xDExaFqjnOj8k0uEUYI2O1YoN7OM41kxs8Io1RcdpQg3vERO5Z9OQhnwiDu2TiO+7Wu0f8RG3hiMcYw4nvanQXdkeOMVFt1N0P'
        b'UdlRt2LAVudqCJgyxkaNYxzCw1ebMGaC66aEh7+2dMwM180JD8TMMS6uWxEeQWgSa1y3ITxE3QljtrhuR3gIuh3G7HHdgfAI6S4dc8R1J3oeZ1zn0WNccN2VntMN190J'
        b'jwCtaswD1z1pHLxwnU94iLtVY9647kOP8cV1P7ruj+sBhH+gMVBoDAr+VoS+a1hjYkwy29YYOuFs2C1E7xbyQERnFUl1Swej7trejRicrI/ONIiyNAk4v8/oF9CaOCoK'
        b'1Zn2TJto8dckGoPDe9IHZumDp2tYmgV6nsDo6dudqg+cNBw4dSB+OHDmoK3ec5aGiQjnHdA9a4gfpkvT86dr2EYvv9Y1w17heq/wYS+J3ksy6uPfTR4L1MzCqYylWi4a'
        b'4umlYaL5WpcOe4bpPcOGPSP0nhE62cWlg7MM0UnGCYAxJoEmezrIMDHo3eikiYSvxIupg6RBMLPVUsN5IIzUFRiEsxDG81qtjGKJLl4n7V6Kvi7W80Sj0ZPp3Krh6BR9'
        b'dMpdP0N01kMm6RKpcdAs07sEdc8yuvOHvMOR5Bh5Hhq5nhcyzIvU8yJ1efd5cU/Uwb/bAak22uWwV6jeK1RnMuwVo/eKGRWKL7j1uOlyDcJYLeeBb4B2ZedknbfBV/Ig'
        b'KG6MIKdkksbsuWi9KfNw7ploPs49859PPuQQ4nCd0wB50eVMoTEsSletD5s9uEYfNueBOHYgYND2qnAwzyBORUoxyUfL1lbp+ZKHFv8tjEGcgCBiMMTyd/iRCCJwElow'
        b'JoM0ZhUgLGLmUhlw86gMOFQi8ffRivXu4TofvXuUrkrvPmvYPVXvnno36l13yjSIDS5ho+6eHSmtKUMBMwb9De7JGvJjf0G37QXnHmed7RnXziKjQHjBpMdER54xf4B0'
        b'3vtK4MXAAe9erPXqq3JDQMZzqp3YNg3nsoa8g4xYxCRt8DvuoZTJmGpwmTrKc8eLCgwuQaj6sacY4RkWZ5w6c2hKOkI/LAOj75WJ0XfJJEe9A1pSP3fxxOZ2Y/NGrXLY'
        b'WaR3Fukcrnhc9BhQD4cn6sMT7zr8yeMNj6G5C4ZTFupTFv6Zx0e7dvQedgjUOyB1vOcQMoLMsqOLZqHBUfDAIUCr7i7UB0655zDV6ED/ror/PQcBkpGmRKOvf1O60du/'
        b'JXXUja/1HHYLe9ma4g69W5jOTu8WiR2BtzbP4CzEKb/TW6d3S4bdQvVuobqEK6kXUweUvVmDUkNkktFPQOVXKjuzhv0m6/0mDyQM+hr8Zg/7pev90u/mGvxyNIkP/IO6'
        b'w3tKcArugPd9/ylacozF8k4njRGTkEQIBhIHvQeld/yvpnf7I2NiToRH66QDpM4cy4b/IDnIGKCkg80UIulAts5P0B3dOc04bdaQMM7gN9noL+wuOFGIjGq3S2fWIw8i'
        b'YCoyRmiQ5bBvtDE6RsvSLkYyiBNsPQzuobpIvfuk+5hzvlqVwUWEs2cX6XlBw7xwPS9c5zfMm/Txi7R5GM8hXDx+SOAQNo4PbHy0Ud2eet+YezaxRhunQ5bNlhrZPRu/'
        b'z+1dHjgFDAUmG5xShmxSRu1d6jJ+fDSJEER8RzDQdh8ETdLHJBsF0wcD9YKU75hkbBqlWOmUYqGSiUf9TCUz3ptuOTeWNRzrPs/RhM6UtBlh4Svb/8cMyd8NPHAaZvHv'
        b'hRlUZEEVb+Jx0wg6czKXQ5J2jwlUPMTFv5s+eZQTQpzjxjCfuz6eSJb8Dj/7O0Aswj+WSCgYuaSCmctQsHKZCnY5y6xcyB6xoe6pqRxGRaJCUa2o/BQB/+xFX19TcZFi'
        b'PF9RVsqXyvkyPEhMUS9TyBkxLSrCF/dFRSPmRUX0bx2iukVR0Qq1tGq8x7qoqKxSoVRVVcpl8mrUYFJUVFpdgiqORUU42bGypEiqUikql6hVMmVRETU5nc5K0W3aRIFR'
        b'U7JRZQfxqUU4NYK6AoU7I2u5VvCKimuWjI4cm4ODMkMU46FrKOzgsJ3hCSE5u/LinaOkUo4m+SDWTtY8Pwtk22z/YmXn/vVJedGP2QkhAkEdV/ynU4/ru157xd+758Kv'
        b'5G9bfhuunJXzyfof5V+8Hdvy1l8EX5nPXZE/V6ke/vH4ir7UzGspex44OrjX3THRf7ft82+yVRsWq97VvveJ/C+nuF9fee2bGdZnZhT5H3572c/TDRUr6pPf/C16oU82'
        b'y379N7mNN5d+mRipuln31yX7ylPTTsruF9ieGXrrUeSUu3V9VewVt9vNsr6xsUueZt7VVFbWJPu8qdwpu/Rgdpn4GFj0mrnSMb/MUl3GzPjc9X6rm7FULm27unXx554/'
        b'tIb0tZp8OWqTFLNjt3hNzB3hz7xRiy94S+5lZmw7NcooWfRn8+Hlf8w90bQrr3anX3Vz87VgY877rDZe5tv1K95JDHz7vfSft1w+2Pgma1nu2fvzlt+9EXz30tHBc9/8'
        b'5e1e829WKRSyP29UzPV+P2t361/C3jz/89wv6ictzT56RNFy8mefFaL0XwJ/Oragc67tP37htC3L/eS1bCHrEf0zTmAPbMV3PrXpJPJBBNyzMYY+8lzIht1c2BmX9tJv'
        b'u82BjY/4aMjsTNDGpd5OQQeyJ0O8vBJBLwtesLJ5RF1MbwXtoEcJziXblWaGPLm2soVNTKCDfXDfxHsspv/X4v/zeywzqM+mlz70WQQpVFW1tBRpQerEQYSNyl/RQSSY'
        b'sHQcY5mYOT+wtmuKaFil8W5Y16rURmilx3CWe07bxot+OsWA90X1QM7F1b3iOwl37WCyISL9fZ6rJkIjbY1qM9Om6nlinbOeFzM0JVPvnDk0J28ov0A/Z67Bee77Tnyt'
        b'XYt8yMYPRVw8FA2YE3YOTfHNjnUzH7M4ZoLHNiwznzECFxamfHOjhXWT0xgT11zcNWV0LUDYHU3XJNEDHLo2Y9ZgAVUbpSDYuEZBUDUKgqpREFSNgsA15JotbRCMCV13'
        b'9UBQ4/XAIAQ3Xo+chCDH6/FkAomgqW+mNLQZXaegx+vBEQOcwQKjrbOmrDv696rfWqOBQ6buKGK346EW+t9DLscHtXo+tpnNMIv+nsDlWDaLMLd5YGbTpNRENS3Tm/k8'
        b'ZuSxzFwfE7gco8rvmIS5Ly5sxlhUq9wU1R8xSLOII7XIXZlFUJ0PccOPY1lWpFkK+cDOq8tiKGS2gZ9ksEseskimndiuePcEG+IVG/sEXybtxBxGGEhc/nMu7HdF1+F3'
        b'3NpT15Y6UeAnEMqp465NSJI22LPZ/ICLf9ezHedEEJe4U5mVyfVvM5UbUMuayo9lu6eab53BS7g9Pepkrshy2+7V27r+SPYpj6YaU8fe8dF9GPDYUmrGOvJ5xkNN7bXB'
        b'+C2ctS3lWfZfsw4fsJr/9bDnEZ5afzXmcOGvi1JUH6mPVr3lc/3R/iTmrCbvpHpJ0L0KbYX+YwZ0nPTo8R8WJl3I3Z/ICbpi/WqB/cUTp4Um1Ity5hl++Jdm4UFJVhZ1'
        b'A2tCcMElBuyGe8BV6jFLTiRoT8sKgRdhfVZWVggDGaAb66KY4NgGeIUaMGVOLmjAd9P4gtWrBuwGe00IKzumJ7y+lDaVW+HmDeNvF3JY1rCdYbpgI2UqwWacwZQCmsGV'
        b'p79eyxUyYBPYDy7Qs2eB3cqUSrj5hZ+3BYdA+yMsINJZXvPAWVEqmyDTCKgB/eCU0P+fG8b/9Wc5/41k+k8Y1ZdN6j8xsJXyShXSmNwJA5uEil824WiJbW+0dBi29NRb'
        b'eh5ZbbAUbJptZJnvTN+cPmTr3RVzjxX8AcvrPZblY062CTviMYHL76lyrNSKsHDYlPXMWzg+I8wqmXyEhV8DGWGr1DVVshEWzv1DMWdlCSrxawYjTKVKMcJeUosinxEW'
        b'zgIeYVbKVSNs6tcdR9gKqbwcQVfKa9SqEWZJhWKEWa0oHeGUVVapZOjLcmnNCHNNZc0IW6osqawcYVbIVqMhaHqmUr18hKOsxm93jJhXKivlKNSSl8hGODXqJVWVJSMm'
        b'0pISWY1KOWJBrR5BJ1OOWNIPwyqV1THRYeEjXGVFZZmqiAr7RizV8pIKKQrjSotkq0tGzFD4hkLDGhTJcdRytVJW+tQKUQ/giv+bD59Pm4/ciQL/QpYS/xbDb+iDLIg1'
        b'SW5kYhPyfPmIKv8dg4It5x0rTrwncceTGy9k/mw68WOvIzY4PKXq4573Z9ey53/Lmy+vVvFxn6w0U2iqSMBihGJYaVXVuBQpZuAmc0RghUqJc0RHOFXVJdIqRNs5armq'
        b'crmMiq0V6gnheBrdjphOocPmaYq1BB25K9NRMcYkSfIhg0WyxiwIruUmk29ZRSakw1iCNWFmO2zqpjd106QOmwbqTQOHgqfdCYACQ3Cq0dTmgbnTkLPEYB45xIp8QNg0'
        b'8d4lXKnV/g/aQ349'
    ))))
