
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
        b'eJzVfAlYVEe28L23F5ZmExBxwxY3ml1AVARFRVmaTUBFNDZN00BL0429iPuGCsiq4q4IKCiyiIDgrqkz2bfJJJlkGE1iJsk4iZlsZplkXvyr6jYKRvO/+ed/73tPPq5N'
        b'LafOfk5Vndt/YQb9E+DfSPxrDMePbCaDyWUy2Gw2m9vBZHBqQb0wW9DAGiZmC9WiYiZfbPRfzqnF2aJidjurtlJzxSzLZItTGZscmdVPatvUpbEL06QF+myzVi3V50hN'
        b'eWpp8jpTnl4nXajRmdSqPGmhUpWvzFX729qm5WmMA2Oz1TkandoozTHrVCaNXmeUmvR4qMGollpgqo1GPM3ob6saZ0HdE/9K8a+EoL8KP0qYEraEKxGUCEtEJeISqxLr'
        b'EpsS2xJJiV2JfYlDiWOJU8mwEucSlxLXkuElbiUjStxLRpaMKhldMqZkbIlHybgcKSXcepO0lClmNo1fL94oLWZSmY3jixmW2SzdPD4dswgTu0MmSFQNcJDFv8PwrwtB'
        b'Q0i5mMrIrBO11vjzZiPHOHmQT5l2E92LGPNE/NFrxkwoh7Kk+EVQCpVJ7miPDCpjFyf7iZkpC4RwA11E5TLWPBoPnQHdUGyMTYAqqEiAimjUxDK2sRzqDBmlYgeJ0HkA'
        b'gUTCBxZz4v/ChxxnC61sqQDTymFaWUorR2llN3NPo3X8r2iN5GlN1YgZO0zd1AmZ8ZPTchjauDyYY/BALydJZvwHYjXf2LXGhnFimDyZKtN3xPBcvnHBCCGD/3e/kJjp'
        b'u2TcSqaF0dri5p1LRwrvOzOFkdydKd9wvVMX5L7Iam1wxwtWh9ka2xxHJjIz6FaQIbKCoc3vmL51FOoCxnHJH7K/uKOwb5h+xuyLO1CHfw5me3nAIi8v2B0Q4we7UUua'
        b'V1wCVPv6x/rFJbCMznESKrOJyFQN4a3VAMGBhLeEr0yO4CH32H+Ne1a/4p6E517OeAdmDGOdKQ7M1GZOs2fM/gTnq0Y4iZGu8JFDBZTFL4qJ9Y1dzATJU4ej2jRUjvYz'
        b'uSK0c7EVnEDt8WY3MqUkEE4Foz4MH+1DpaiFWZ2LKs2uuCt9FuoNRj24Rw/d6DiTj06azER10fYFk4OD8Ic5Y9ABRmW31kxQnCODEtgnYlBXJOPP+KM+VE8xLddIGFfm'
        b'RYHYKVNrFR7NS+8jlQszkXnP7MBkhgfqnRlNQmkwa1Tinp6baz7PvJu5Kide+WqO/14vZYzys0xnVV6ONute0OjMOOXrObKUWKUsWa5sV59hz7rk3s2OUy5n9qpilHr1'
        b'XuHups7TgfOWVcjGSJeEfTvv+cRmh4U1l561O6Zh0uKGf/jc72WcaSwhomE9XJZgPskSzH7eWMIcM9wMu1CJ0HqdwTSKjLgMdegMZuduqIYKwWp0mRHOZNF5MStj+zkv'
        b'mUxgIFIZ9ODw4ye38ByDfr1aJ83hXZi/sUiTY5rdb0v9kyJbaVKTcUY76pTsWDvWibVmvViDeACETNAvWqPUmtX9VgqFwaxTKPolCoVKq1bqzIUKxa/WlbEGoicGEXkQ'
        b'KBMIfAcC/wMnTsxyrJg+zWNwSxraBft9Yny9E1ElnBuRhDVExLjBNuHISakLVZxF94RPUGTsKB4qMkfdgAArMkcVWUAVmdsssChy7mBFHgA4VJHFiVSZskdNh31Y1deh'
        b'cj/GD1qmU2UqRO0C2IfNCRWjYwFMQCDs4FXvDLrkRrSMiZuBlcxbpfni6j7OSJRfN1n1eWbGzRp0CPXUtOxrKT4f47nzkv2d4thj7Is5RKPscj58lWEOVllPZDHPTMRh'
        b'osoFW3zi/KA0Nn4zbEsUMRJ0noPjqBSOWUTxJBlTTvdLeIHmaPVKE5UoUWzG244VYnkabB9KU0il0y/KVmdpTAYyyEA8j4wbJEHOQMLSIDGS6T4PxfjuEDFKccsquIi6'
        b'LWJMouHBl2VGFwjRQazDe9IjzCMIdU3oyBSjKTQQ+tBxIcNlMdAMpxXm4QS4L/SSLi6cZTg1Ay3QAdupSzCjFnSAdFkLBAyXy0ArdKCTVCyhYZONpumBAnQJQ9MxcDaa'
        b'9yJwaSTsIj1TUTPHcHo8xxPazdSKdqNLcNwIPdMC0U5UixdDxQx0h6LrFMWpE6CUduZkinDXDgZ60C50haI4ETr0RsO0QCh1ZCnQtmlwkc6SYV9WBt3mqYHQIsGoYMcG'
        b'3Z7jeY+2Hx2cQfuM2NA47KGgZ1wW7TJCMRw1GoMD0f4JeNYWBtN88Rl+1mUbHzpJX4SJRkcYuChDVWZ3QlyxXQjtQpWozgp3HsX0QsNYnsWV4+EsdBvtbMfADrwcXGBD'
        b'oNGO9sFRdAxKJIbQwEUGgmQzA32+UE+BSuEiXJTAeUxdM+UmVLCCVaiMTlwK11CTxDYoEJ3IwJTDAdYGe+xLlClWTqhEAr0YUUcyayfLwpkk80iCSgscghYjdBc5JMMR'
        b'gksD6wMNeB4lsIHD4cHGHjoD0CUC9AYbasurghldgT2S1WboXa5gcM95dlJcKg0Bmagr1igxmMYkkxmHWI/F6BpP9umlW4wm6JPYoAOkq5L1Qe3oOF1pITqPzhod7G3R'
        b'WTjIMQIRGwGt4+lKsdiXHsZdDqgEDrKMwIaNXCvleXUd1aNzuGs1lCUTwi6y/lAr57WrdFysxL4QVUAdNAsZwQQ2Et3wpwBh/1JoJjqSLsLqU8hAOxx0oD0xJmjCShyy'
        b'Bh0WM1wOVnC0bQYFVwjHo4kSBEWIeGXsglOomcfizPJcI5yHbkd0TkM42MGGLITjPMkNmMKdRujFvbMiSedZNnhjtkxKA9qiVc5s+Pg8IZN8s+CQ4dsltNEnwJX9yqNI'
        b'yATeLEiXnltEGys93di0KRuFTCEeOaEqiDZOsR/Jviguxr7g5qb3NlyfRxsXrh7F3s+pEjKRNzelb+yJoo0/OI9lO332CxnpzU3uivhcPpfa4sEWptQJmcybmw65LEug'
        b'jS+lj2fv5jQKGScMM6CLpY3Fwz3ZjSlnCJ6b0kXj42jjrtyJbLzzeYLnpvTQb820cduEyaxr0A2C5yb3kGlTaeM7Mhm7dc3zBE/joRHBE2jj3tXerN2IV3Hjs8b0dBOf'
        b'oBxz92Prfd8kyBvdl6+PoI0PrALY8KW3cCMe6bl+PW3ssAtkb+Z8SCgyujvfkNBGlgliP0z+AjfikSscFtLGWI9p7D3594RMo7vX4Wdoo8huOhsT/AtufNZ4iLVL5xul'
        b'M1lhsFCEaTceympypo33N4axayfa4UYMc84me9pYmxrBTpztJMIMMb4nmc8jf2fmbNY1YixuxCO1v8yijZ+MiGRrQiaIMJeM7lLzfNq43Xoe+/EsH9yIV0+xTePTeLco'
        b'Nt4hUIRZZzxk/Z2Sl+byaDbbYQ5uxDCD/jqFNt52jmWzXaKxy7+Zf2hlkxdtdLBLYCdGJIsw6/LTo2dm0Maa7CT2baUCNz6bn+54bSRt/JNVMptOPKcUTzdFzaGNhimp'
        b'bIh8FW58Nt89omUBbygVqNHPKLF1QPtSseHZYRM6mUh7cKJWMVdicLCfq8fGOoyNQG3oPO8yTk2biTcUfUXGqCQB9Rg+a7H7Ir5mGtoOp7Crwa4batFu4gJqWU/YuUEm'
        b'tGjU86xv+hwrTGxReuH0tbRRFfUS+3ufKBzkburfk4615pUn9GXWyzsBNz6rT9e9wZvDuLTX2MCpqVaYA3p3e+ehCbbNQCpB9qCWLdyjjQuTY/Mw2Rb+ZrKdNzhHcbL8'
        b'Ds1RZieayf4Fx9qj0ag8CW+rqqEsFp1GFxP8oQynjG6ZwilwyJ0ine3EMb5hBLtM7UX3aXyi+/k0aybPDe89MzN9FWueYSj3oAkH5FJ5gByqkmIVqFPEWOPgsW7SJj7e'
        b'7MiEk6gb9ZDcmzVzyxgskRbURHd4cnQOTvh44Yy1NACnK3a5AhxgOxyhERpogrSGhWOoGxMQBq1KJmyGzkBYRlFJXC9k7ttiAiMz49WOlm2UYZ2Y6dHgPbI0M/45szXD'
        b'K0uZpyyYZH1oL95PdDBKVIK6aNphCFkvp/lwNdliRrrIUXVALGr3YhmpSeRg7UOzBLkGHQkOIdNr81ADk5WC2s3j6J9wHc744O0U3Z064//LA2KFjItMABXLC/mlL0MN'
        b'dNHdBTqAmsIYFRzneG1sRo2oOBh1ka3KCbRtHqNFF2ZQopOnKoKDyZA6ERxjchPzaWs6XN4UHCwmnnvGFGbVWr2ZbHuj1huCQ8nYQzgRrmWyNQYz2Q6Mgja4JI/D26by'
        b'RCIVEeNQiNrWCGagTrhKYyE6DgehPjiULH+4ENoZdcZ0muFA+/IV8ng8KwAqfVhGksGhPfOgYxUUyzi6JOz3lQaH4lwQHYHOxUyOTMaT2oaqxwSHEgSP2qI2JhdwZs5r'
        b'QCOqwxItx7uTBBETNFPowaLGXKiieEyB007BodggcHKxBw4xeethFx//u5bP9iHCgLJE1C5k7CIEW2Y4LkG76bRYdMotGPWScfUB0MxoBVBJNQq2o91wDcrjMfECBucL'
        b'1wVwnUVHUUuBOZ70nxAsNsbHxiaQ44eHO0uvMRv9Zd4J/jI/zhY1qVEzTmNOeXmhFjcfGZbzKR9XVOs2HE6NQKc5nAO6OqH6YbBD++ODBw/2GUWMdtIwooe+2fMzeJXL'
        b'joBSn0S/GByttMJIFp1FZeiozJVnVBOqWGW0N5gFTJA/B3XsBKhcR2Py/NlwBbodSA9GrpWDXlbmhs5Sgj0LJ0M3nZTqw2GKfALRDapIEVCJaox4EotTlcPEcY2ToWo6'
        b'J2iltXG12ZZlsBJ2cugKK02JohJBp3EOvAcH/yLoETGuqILka+PD3HnGn0PVCpx2QY89y1hBLcmggtAp6OKz2CLULnGQoGqO0UKnIINdDgeUPNAGdBT2G022OEOAK6iW'
        b'Q9fYMavRTkpaHpxHVaQP76h3LedgGytFnWg7rx87Ud8W6DYZoEfAOKI9HLrOjoa6GNppBafgpBG6TGKGhaq1qI6BauytKyjt3mgPOiqxtrelEaFOgEMnapjKO6UKnN+2'
        b'40R3tR2mf28SB0dYrGtwno8SF1BFtMTBDrs3qLETzGJj0ZUJFKQEFcMOnBMZHLCgK6BD4MBOH5NBaXAdi6XS7Qhd9hwD5+CswJOdCw0pFOBo1ORhXE3W8kKVHOplPVBb'
        b'KM/OGjgKfUZbKtUT6AQHezHtJ/EOkIhoqcpWQrucUZXAmcUbQ9RHzX1G1nDYh43JFx1fwfjawDZqnIvGY+0pd7RdvQYT1QBbhTilw3T2YH9GXJVZBPU8VZsXEaLMqJYX'
        b'TTNcsLNoFtqO9lLNise7DzJpkm4Fj93UJRQ3aJBSkpziTRaNwzGxh+rc/LG0R4ZK/HmNC4c9VOOgg+c6lkcV4TovS1S9kMrSDY7QeVFwcNGAKDufoaKcGsXPKxGJUTlm'
        b'E/SYRUwqKhWiyyzaNiWdbvJRFd7DHkTlRdBrh8qwdrXKhFDKosPRUEO5CI0z51iUsmAU0ckM7KOJNAvQLh2vdbAVKxZRu3nQSucECOItunoAKqmuZhtkfLKN91x1cRJb'
        b'G+jCtB+VCMLY6EkhvNc+iDP7NiPPyJJIspcZH7GJsjEozIU3aivYS63aJpJPwutRL97WWZOufFQmsMU7gU5o5pX0MDrzDHTbUXA9xHo7sJJWAr/zQO0xC7AC2+GYNwlV'
        b'cdCE+/YIeKClK1CF0QF6TSyTSPb4J9iJqHkBJWz8ZLwz7JVgJciARg662ND8BKoFRSOhSmKAC3BByExEZ4lE/dEJrIgE/WEeebwhzUbbiR0J8B6CIlG63FkCF2xWixm0'
        b'FXUKprAzhXCULqSZi1poF8u4rhF4sWFZqJHH7uzSqUZUWQi9NB9rJWTJYjfRPnYi7MboFTqK8faR+LgydjJqn2v2I/NOo+K5WA32oeo1WOcqcS7QHor3gfvhILpBjuPg'
        b'wFKWmbBSONwNb8ddqJXDviDYh9OtQFQ2nQlcgXaYySEwwjvh5Xj8QTyz9DFYtbi1Bq/Rhf+vxU6oD7fV4HElNnjrexDOoNa8VahxFDb/S6jeBh3OnsETdRBdQSUWzsZL'
        b'KGMD0T7KJOWwmAHGTsPKRBi7BHXjeElwXI0qwy0cDJxK+LcghbJPauVq4Z7Kg3APDsMN8yLckSGC6xKolOPYF5PgTyOVD1QmxPmlQGlSqpd/QhwOb1AZK1sSgzOOFKxN'
        b'PcaljHE4ORJtdx04GkVb5zqh/c52I+Ewr9SVOrhs4fzwHMp3fw+MIo35lxTQKvf3844jy3YIGcclznBOoGVmmT1Idw2UoUMkVFaSpADVaFic4h3isJ20ohPURHGaVocu'
        b'4QwwxjcuyU/MSOQcpqcPb3F7R/K73tPr4RhvONBtQw0HXVDz4DtQXYpPXILcDxO2DGOAM0Fn7M1xrtIIZzTNwlqB8S7ON6p7Op5Jm5XqOtfp7+tu3X5/teMCocOwcdK6'
        b'H4Xj6utsFkRGZu5/dmTk/rkjauvMi/ucnF51WptxYZu6YKTLvVHu6b9wgqys+RME87fs+OBV/1qnV7VvvHv7g/v5oX+8Mudk5s6sa6vzXnIqn7zszvU3XrQ+kJD10meC'
        b'6zdNf/4yIc6r6Yu/rnhxaq5Cm+q7XmG49mGKN7p2bO7UdeJjielfFtbETEjZNlrkc6sitbEiXnQweJxP1vkrOUJP19GvLBlZuPq5/JCP43RNFZ82dNhtGSn6ftXRnz7Y'
        b'+vbWf34XExE96vY833nbTc2ST78YFpMbESrQvKescRpnYLZ4R31a1OHTsOybFRNmvruuun2dNuSF5y8vyDwa+XzS1JBr363cYSfu4FwuvSCq3vK9776Rn56V3GuFijXp'
        b'aTG2G9+8u8iwceGoiIULKy9d3dTW+cvx2PDF0rQMv72eb6zxPuhwbU3E1bcnX9dK4nsvvnL4NduCqz2TUuN2b5w0/POXV/k8G6Aa2THqk6IC2xffODE2+q3o3B6/7ydX'
        b'QOvMjPtTa7vcs/50bs2t4y4Ju3f88MC97N6907YeGy8kXNt5a+H6o8Xx+2rXhg0/f2t26ceyE5qPI5d/tPa1zGfgyHOXq975aHT4C9P7Qibv+vGPB75Z0ndefv0vP0x4'
        b'48rP5rfRa43norz3SieNjmo69eoP8TUvB364zqX+fTbgvaCvdstm3VoSePxE/HNJf92gCFaXxI+XNXRn7low7Q/NYU69OatW/P2z9BL4/e3odxf/ePtM1LZLz+9fHaee'
        b'fTv1l3avunnfzw9/4/rNT9IuJ/5w4M4PN38e6/Hz/uAb7/uaHBdNH/7LNt3dHR17l/1lv+x3HzWf++Ni/6rSH4f989M905tVqVV/iLzq8uCHNT98kfjOguo/rb3gX3A7'
        b'NF5Q1z5B0vbTojnxgu7ff+jm+fado1ej/c49t+KHyQ1Hv7186+hfj5yp2SA7NOy23nyrdcV9tzk1m355t2x3zbcPXoj86g/XP39T9dUl79lfv/Ni89ey9LQtF+b/R33x'
        b'5hv133w65589ARee2y+zp0f60VAyGcp9E3F+CtW+OBMnjvQozrE6UFMeHbFuKfYM/rG+3jLszvb741FQxjDuUuFKODGZHvrjsWXYdQ4c+jO5afTMPwLVm0j82QwVi338'
        b'cVZThuHDSa0Yhxk/uAoXTcTjKWD/OLmvVwy2SF+cMDDWGIF1s9W0Dw7PUMljE8hOFzvmRrGQs8a562WTlG6M0BVoJ6e5GC5qhRtQhl1HtYBxmSWAo+sYEz34S0Jn5Ul+'
        b'5AC1GTWtwZnULrhi4jM3uBzg4y+D3b4MMwEuilEbFww3UKeJ+pG96EQYlCf4xkIVzo4SxCGcw3wvevqdswx1ysl9kTyWZPWYY9kc9MyGo6uKTCT+qTeN8/HmqUXXV7GM'
        b'zSwOnViG8xF6gXI9A+rk2LthT+v3zLQ4co/gDBcFULICtcucHj83/3cfMpt/bc6jc3pn/pzeZFDqjEr+upge17+OH8w8B9aaFbOurB1nzdqxDhz+hDMOa9aZdWDJ5Yw1'
        b'a0t/XfGPE/5/4Ad/5hz4z5ytlZgls21ZN86Zs+aEIiGe7cS64TYx/hmF4brRFlehkB38Q2AL6Rj8mXOm6wnx05V1oKvack6sB+3Bv5wtbhVizOzw32LWHffjdvI/7hmF'
        b'fw12A5TLBP12gwkedO3wr/FRxhrsBzhJwc9nBi4lbowZfCnhjVvS4+CS5U4iQIa3kz6J8f68KvuImWjUlgdHrPDmsBWdk7H8meoFKEd18ljfWFTvI2SEDNl3HrAfctxD'
        b'lqenMlEMPe4h99TMr2+qc+wfHvtwTz32EdA7VuF3BRiorXTQv2SiIkapcmj5AK1JWFeoliakzQwJlOoN9EOQ/5CpQ/6INUkNapPZoCOwtBqjiYDIUurypUqVSm/WmaRG'
        b'k9KkLlDrTEZpUZ5GlSdVGtR4TqFBbcSN6uwh4JRGqdloVmql2RoqR6VBozb6S+dqjXqpUquVpi5InivN0ai12UYKR70WC12FoZAx2iGg6IUiP0ql161RG/AoUjVh1mlU'
        b'+mw1xsug0eUaf4O2uY+wWCfNw6iRco0cvVarL8IzCQCzCpOuDns6CD/Mw2y1QWFQ56gNap1KHWZZV+o115yDcc81Gi1962WPzfz1HCyPzMxEvU6dmSn1mqdeb8596mQi'
        b'AkLmo/Xm4RatWmNar8zTPj7aIqtHg+V6nUmvMxcUqA2Pj8WtWWrDYDqMBJEnD85SapWYAoW+UK0Lo+zEE3Q5Ssx4o1KbrR863oJMAY9LlFqlKcCqgCkljHrSUJXZQDi0'
        b'7hE2S+FUnsGse+JochMdRp8YplmVh4cZ8V/mgqdhrdLqjeoBtBfosv8XoJyl1+ersy04D9GXJdgeTGodpUGaq87C0Ez/s2nR6U3/CVLW6A252L8Y8v+HUmM0FyhUBnW2'
        b'xmR8Ei2pxG6k0WaTUZVn0ORgsqQBvNeV6nXadf+tNFmcgEZHrZQ4CqmFNLXuSWTRC/7foGqeWqs0muj0/x1EDc4gwh6Gs8Gx6KG/K9QbTY8DsGiG2qgyaArJlKd5biJr'
        b'tSbrKRiTyGVSDijXUhy58FJa7VM0zLLoI3UcutbTVfNf5rtBjaMoNrowKfYyeGQKXFXlZ/ELPGk88UWYeEW+epCoBhDCLNDCVaNRrf2tqSYc4J/CRAscMuLJyP4q4srN'
        b'umy17skR07IsjpFPiNVDF8ZjfgtG7pqhcTeaSBtO5ZiM2FPl4CSGdD9pYqEBCwD7POWT1022dKt1fokG/6dhP2TtX+H95PhvUYTHcoAhk5+aD/BzNXjpJ0+MnTc38elq'
        b'p9AbNLkaHVGpX/uQJEtfFlVIbMDShQZ1QXbRU219MOT/hELzw/9FZ5KnxNHmiS4vWp0FV7FZP8En/DcgRsyA2hnxc0PwSsM9v21sOmWB+pG3s+TFUq9E3PxEPTUbCmle'
        b'9KsZS9SGIrUum5jl+iK1Kv9Js43qQmXY4MQaAxiU1T9hxnKd7pkw6WJdvk5fpHuUdWcP3gcos7NxQ5HGlEeSdI2BZKlqg0Yl1WT/VoYfhnfKygLiNjFOaXmPFVMPnRhm'
        b'2eeE4X3BkyLD0NEP79nJSYYb8/g9exJfdsHOEZBCwZgRTGb8fzgW8TfURTNFpNC30CUhM75nkSdjDsCNy1EZuo7KUTfaHQo1YgG5niLH1WdRJT285qZCO2pnwqFNhOrt'
        b'iug1rNkKby67uS1hDDOLmQWlqJLCvzHCitQhB670ztR+7R3B0LHTR+ssd9BQNZtR+cI2M6kfnwPn4YAPv7WFTrg2aHs7fpxoFFT4yexpxcDMjLVQHpMQH+tnROcQOUvC'
        b'4+R+YmZcuhBOeaOdZlKjmQz1HJQHxMX6od0BcQnOsJuc6NLj3KlQKfaJhYP0rHjJTNTNH/eiG2uHHPfunUKvRUJNbvI46Fw05PpaMGOOgD9q7sQ/BwddUY9HZyUZHHQk'
        b'oD56BZwGhyZBOX9kDlfgCsdYwyUO7V6IySbUoCrUqCaX47GYCAlHKkerA2KgUsCMcxbCIVUorVNHB1bhvTwdtX8SHkgrE6ugjNQpTPQRhaPL0GL2Ivg0BqGqAXBwAHXR'
        b'kbSqIDGBZWToqggdcce0k7X1Mhc6lEGneJh4WHlALB43MVMUGQ0VtLTAFR2HTh9/qMSQNsT4xyVAma9MzIyGo0J0cpKMXvH7O6May5DYBNhN+kcMT4azwkDUoKPijUXH'
        b'oO2ReG88Jt5FsJ/eukQlo1ojrRlO8SJndlUYsaXk/hmVUTEvToZKIbPUzwrtV23ir9tOwo3M4CAhvQ9rQD1MtjmaF8224WJeskZoHCxZdE1KZ+aiytDgIBGpEYhHx5g8'
        b'3NPIX+Q0opJY2GflC1ex8jKBqCObv/q7sH4uZthWKHlMGVCHPxU2uuoNOwcpg8NCqgtwHLXLOHrxEYZ2bQ5GXYVihpWg0/EM6ghGLdQsXLThuIMAqYMbI5j8sRn0NiTO'
        b'mDSgPugaOjagPrNRpUzM104cVLkGBxcKGBYqoUXOoPaI5fSSQw/Ny4KDoVOEe9rRlRRyqde7kr/1P50zMjjYgOcooDWJXLL3oW20JxWvvg3P6sKzUO2aJQzqzTZSpgRi'
        b'5TgdHEyKIxrTzUz+XHSR3g1vDDYHBxMmnpxsYLRQnkotX+88gvHFVtjon7nxzXkpvOV7wiFUb2ShMZBhFjALoI6vm7uTPIy8PRLosjbTV2aczMh400JdsAv2PLro2Wk/'
        b'cNEjXktZ47x6ptwfymcMvikSaLEW7OEZU4r2JMlpDbYkSChk0YnsZRYpwFkoR5d5ri20JzxbBWdozygrVG5h2jB0mfBsGNZMYiwFGlQ/YFiekx63U3QlUWappdllgxp4'
        b'5rrCWcJcuGC5voTS6ahlgLkXHAlzoSycFv/Yh+dR4LKlT7BuBSqmIggeDkcsEoBdU5l8dEBrnkJ8DLoGFwdwW7j2SSZP7uUojOFQK7DICzVoGW041FMEbCdGUwixqOkJ'
        b'vsB/Nm8Yx7Bp1AcH0zIhpzFMXqoLleC0ZPLGBOP0ZXCm73dsNiNzpZ4DeteHymP9Ev2XWWOf4DVw8j4alQhRU6yMuldvaIHtpPJF5hebBV1CxsaKQ1VQuZ437l3zVvIi'
        b'dF1PRYgOyKilJaKDkQ9VI3rLgGZAF7pBwfqjWqFPXA7a7yf3806ECpZxzBWo9dBNndGGONXDUqvo2ZheRJhFCntGxwvRXnRDbZ5EVr+BRbdjUFGWF9QMrcoKR7up/4NL'
        b'MdBguTW8ioEN8jZj+TeN0PmJaDtfBIWqAiagNn4wHeitEqHWCdiDk4sBO9iHmiz1a9Dpaqlfm6Hh12mcF/6wyGuUeFCN1xy4zN+eVqlF8rgpUP+Yi3IeSbsj0dGMQQ4K'
        b'DzpGXdTa8fzsNtjp8bBe6XQwX66E40i1mVTMw87lqPWRRZZhE0BHUB/sjic3OnLC5iB0UBzLoXK+kuL4FLtH17AR7uQitg52oIO8t6xbBnsGV1XNQmftIgSO0DyfnmBb'
        b'owqPgUKtZHSdVmqhc4v5YoWeZ9CgWj0WyuxyBY4eqIfaKoexOveoqPBhQSGcDhJOgTq0h9p68ByLe0DbUT3VrlQ4xeN9yhqdtyglFsc+i1ZqZvJlbtg46iWcF6koSMUe'
        b'8+o0HqUDznDeJy4AeofonHYKdgxOVJe5KCOLri+lzs9FSmHFr3CUkPdKoCUNXcZh3sOdGhpRgkuwj02EZobxY/zWQR9/O12Ziq4/EkAlXHl4+X0RtlJbTFhpTaotZ3yu'
        b'y/R9b7GeodmQ2hudfajHy71+pfHQNpm/l2/HiV8nqVWwwn9UR4QzivQkCkELlxQP1dcVeh9XX7TLj3et7SPSUHcgeb3kDHmZRI9RK+H5c3maG+xzdIALsN+KIfw+APvT'
        b'ULHOnELzINieP6TQgPiL6kRMMZTG4vYAKEsmJQcxfL3BomTUFZiaEuO7CEpTlg3KDVCbvVMSuoFlTKxpFhyNk/vPWjk0Rnjzdb+KleT1KSbdZ1hmvDRLxqThyENdeJnn'
        b'GvmAiYgV3IIo7zHoMDWQeehKAg46x7KGAlyBrtDugDmo9qF4RKh8QDrTg2hI24SOp/wqTdoCVcLAsCyK0dgRdgxGe4Z5Wab2TvAYhrpR54JxlkkmqHks/8rAGp+Gxyya'
        b'DdXGIZzBSRN5wc7fzwubiLelxDCVMLXUd0kMsQxqeotipjxDeDiYgzc2DEOVq9fTisJP1tJ3ARnJ3EztAi8PHiO0M3PBE8wLbV2Czatj4kCU3T1bjrpDSK7jhLYtwsq1'
        b'zlIqh5Pec3hbgftYhjWiAzjOdoTMN5NdQUycD9Z9LPE9cADvNgbXy3SIFLAddWWlmLLQhWks5rN4GVTb8KG1UQZ9FoBTUC8BiDoXUVvyzFNbsEAHwwgWWQEyoaUWF8qt'
        b'g0NX41CNzonjyJxKvvAOHVmHQ22ImCaV9aicUeMwdYKGpHWjjMEha/Ay0Dc7krwY0oGaKDSv9VZ4HejEey3sfk7h6N6Vv1jG0j4b6FLgzqm4bwsqW4hdnwM6a55HetAZ'
        b'AVZ7KMfMLA+A6lTotEfnQ6YmP9TzFL8lvJpTEZnQPl5K2BBP2MIRp/nUj6ShrVmoVTwOWnFGxmxER+bwNYnLoQa1hqLz5G2d6yFuJPPZLqVsGYPqo1GryA3hHHczs5k4'
        b'cEuNkHJcArZcdBq2MfRtw2q0iy86Ou0yHsumXURu3NdDMYOt/hz04lnUm1/SWsn9Y9Dlx9KxY5aiHHRtM7r6yHXtR90DxhHLX1jOzsexobsIenGeB01uHPSxIdCt4d8Y'
        b'bciDHUMDD5zF2dPjgQfrzDH+9vOsHg5aCoxYdIVWGIWjVh6TZpzpH3oUl1DrZBqY0A1oo+kB2ucQT/MWvPHt/XXmYouu0cpvcxglew70ShIToNJvicXkoGxpTNzimDTo'
        b'RLX5RJioBXuuBD//xPgkESl37bRFO7OiNTrVRYHxXQzpi9+NNqfdqB69wLXu8O1lX/70wvE3vr99p3BidOD4g4rIrcKqT6LnWTsl23o5J+/9TFbW84fPrjbPODVyR2BU'
        b'edR50eKPkbwy+ZetpZ/Zxu1I/sxVJvOSffva8g+ecy5Z8v3Vf3z62oYPrv7w2sfvp9V+ZPXlgc7tO/a7D19Yfeq78syfM//+jNOCwmu55o7K1z9JV6/uqPCQl/8j7QB3'
        b'MmnV4vQP7r55Gua+f8j7mwr/xXdyiz78y56kQ898q83MDw2ZZuu8//b0oJ9l1RWnMhQVTa4L4zdNkOfKXPb++GWRPHmGZvEYScDtqYb70f5eQb/Yem702XZ7/v2wxjlB'
        b'4z2nZ7Faru3wmXk5+W8HKZ1vrjrqdDWj6Wrzh31Okn8GPO9pv+4Dzy8n3Mvv/kGz8KD7NbseuJvooP9s748rvxP5/mnE2/K33zuvaO6Y/+0o7YJXXveQZxxeu/GXxe9v'
        b'KTk5e2fb0Zs/VdxW32M6J9ysy/njjaBecZvg3uHfvfPd6Ocdtu+J+1IQIXz7ldCWl700mw6sPuH9+rtvbbp/71TuhHsZX5a3+A8bNraj8e6fXvpj61ttno1ldwt9z+R/'
        b'rhn9vTH9XI15udXpsFWBMa6df1301uXRP/tnxV1OXr68bd+ub4PtR+ypmritIOv9916LuJw/asPKyrO9biu0+T+71/yx7oMv36lYefOlxd8f1HzdsaRh140VwzqudJtF'
        b'n8iuZM435T8b8kLVn9889POC0Ruvl1Z9vfHky6Eaif3dGaY7bMnme57Pu7Q53nW1rTw2T3J4ZdQ7SYZ3Hkzz+OzLZ9eXXp0Wtnhe2Z9OXLHt/iI8sOB+1uFN13dlKW4t'
        b'1v79aKjmXdm75s5NNkdstl2z+/l++ps+Lo4+557fHjH9+683Vv684h/Hty08UrplzfTNl1O+bn736w3F/yip2nKk+D8mu/41d+lqxfz1Lhe75C92hVQmB5eFv/6Hpii3'
        b'3IJa5w1Zp/UHK83/dMv/Oij/61ff/4L9832vJR98+mNtx7ObS75o77Ff8+WRI1/rz+5uaFmmnxHY9VX0jTvtZ96cmfbGG39/tuOtf6RUibXXljZ8lTajeE2uu0PgW6Zt'
        b'Ex5ceyAPetB4yff1k7+fMO3BqvAWJ922F6bLXlz/qui2j+l7x3u7umMn/aJ93/StprxKldY9u6i36JuwWNOV4qq7U1e+/vmc/r8vtYp/wdQQ/M9Zld/vdO7NBZ+Lf7n+'
        b'o2F8y4RP30i5GKCfrfz04ib/FLM5sfWfH71q2j3myyTXn35/svzDtm6rM5ujxn01682TjiOvPPte9Nop978SB3k8f895lVOF66Z7997724O9Yp+Tb9gm/e6Mz9nCva2F'
        b'tvn7V+UMP3Huz4VbN0y+891zD65+5P9Kwb0fd7T6znZ5s6iajdUflyrDZI4m6k12ecEJS2ETlA0cVo3AnqUKu5MYODWNVhqJUd8GH29aaRSODuLAsIzDW7FKaDDxKclw'
        b'54eFRuIQToYqHGxj6ETUgK6uelg4RaqmoAId8VNPoRPV0BdqqZvysLeUTUUGmUgyiTFowKneoKquLU60rqsDp/zVJuoq61ylltqpjVFDKqdSFtJKpbykTL7o61HBF96c'
        b'nhGuRBeghFZ9ZYbAAZ/EBN84HOA60EmS1l/iitBpdJ7WbqH6KDiJk7vdAX6YsCJuNtruD1s96NS43DlynPccR2fkD+E7BgpypX60hAq1oMOhg/M042pvvOk/wTPskpPz'
        b'QN0WKdpaAseDPRdQsPM1QZb3knHyCrtQq+XF5FYbnuaekAToJoVbqL1w4PX1cO8NQkFSqGz4/+/aq6dXB9n/+3B+9UJ1gWlmSCCt0EohdUBb8I+z9aCaKQdaNWVNK6U4'
        b'/Jczx9dM2XIc++QfazrCyVKjZcu6c+R/MoPUULlytuzgHx6SAz/3qTB5uA6slBVzdhS6u8CJdaBVZELWA88nNVxOnJTWaGGoluota7qam4B/CnkcODuOVH65c7SajK6P'
        b'fzlCFSmv8uQ4PF7I40Z5IOZsaXWaLTuGdWfd8PhRGAMhS2rEBuhx4vg6NvKJvD9O6BLj9Q2O5GxioExMSE77B5WH/fsSlbEGpwGZ0rVeIbIkTcxWpm/i4KIxYp0GScjA'
        b'1xFU+5GskmFGFQo41A2XhuUN+Q4Bog2RBBZJJtXki2eYDC6bzRBkc/x3Z/Q70QsLWsxlWGAw6A0/jeOvMKhmGSy1WepsqVInVZN+/0SZsN9aoSB3PgpFv61CwX/DDP5s'
        b'p1CsNiu1lh4rhSJbr1IoeHV99KBEkiPGjzF2tK7QmuPPZXZJkiQO0GeS2EA3aiMU+hkslhoAJ8Qi1Aw7ZexCTWjcZIFxLJ69QyCLqL6UCJGuC3K1U853ByQe69y16YMi'
        b'a+ex4yLn3k0Zc6mslruV/PtMefDCjxy/OV8hmHdu3Q+f3b398/VbP+zp+Ns83z2qnwsOfZEeoeyJeOu4onLfusvz/etW7/nxr99cr3eyvlXyavCt9zaPXeAccODEN8vi'
        b'L6dknyx+sdH9lVc3Ddv30VdfzstIrjvbsjAvtfHYxZbXrr3sE9BzJkV+9e2GxOLJfhv7TdZ3/6CqWuc269n07DL1T22dL4/6XNv5ktuf73W+4vHzmMIXh73w1mbvmXdq'
        b'g1+/dCispWnH3peDXhq+75mlVd/Mr5Z3xG9OnG5e1Gd+KeTiLwd23U+L3W+/bFpbwXvHVskUIuXO0TqX6T//bf7dT09+WDXX0z1qjfaFoOGlU+5MmuM3Iv1iZpRMaCJc'
        b'Hja/CG858MZmxuQVDFRtcKYOHlrk0Gb5Lo/xsgF3SL7KIx52m8jJALoghz6JN6lWxQHi4Td+jEPdvm5COIez6mMmehrYCnUmI2qPSZTCdb+HOfUwqBGgzihHrNpUw53/'
        b'C12qmObtT39QV4lVVqtXZisU1E+SHJ9xI74qBPsjUnNKqlCdrJ2shng2kcVrCcZsYWzwWOJZR9mxhhED2owtiMMq/sgZDPuvIZE1uD+0HbI4/W4GWlN6z3+weyAJQDa0'
        b'zkXl5CSIfAUSKkPVVozDSLQNXRCMDcvXmD714ow5eNxHxS5jn5/qsD3SadebW3KK7E1ZTZMnrp18LvB8xiz532Jmf+9WmGp/br2y4ewyRcH3X98+cu5601cPbru6tXxa'
        b'pAnrWL/K5oBUmW07NiJX7D9jqe5WbEV8+Mr5H3vJ39VeOP3TJ1bPx7r/KaxOZkUVbuxqvA0kX7qRxG/tKhkrRoK6ODgzDrXzJd1l6BDslCf5wXkyLMmPw0p0Feo3CVAD'
        b'9MEZCkY0H2/eKG3kABFVUtqcodJX4OHjRIu+l6BrLpaqcbGQC4U+63lwnmYA0BOOOuUPv+rJE/WyjETGQc04VEwzJ2iHYtj36MugMKa7Ld8GhbYvM9E3sFCX2CcO5xf1'
        b'LCtn4FAUHBjQcOl/Ww7x/6pEwt+0Do1OY7JYBzkQYeytWT5iWgt8t9CcYrFh5EO99+wXaNW6fiEp9u0XmcyFWnW/kNxq4/CoUeEnKdjsFxhNhn5R1jqT2tgvJDU//QKN'
        b'ztQvot8A0y8yKHW5eLZGV2g29QtUeYZ+gd6Q3S/O0WhNavxHgbKwX7BeU9gvUhpVGk2/IE+9Fg/B4AVGc0G/2KgnNbn9thqjRmc0kZK/fnGhOUurUfVbKVUqdaHJ2G9H'
        b'Vw/iSwz67fmESWPUzwgNnNovMeZpckwKGtj67c06VZ5Sg4OdQr1W1W+jUBhx8CvEoUxs1pmN6uxHZs7zQGqYQT6T96gN5DjDQPYFBnJSbSDvchvIJY6BKJZBRh7kvsBA'
        b'bkMNk8mDOFnDVPIg2auBBnZSEm4gX81jIK7VQK5+DdPIg5yhGUiQNJA3sQ3kTXMDMRoDudo3EO02kNMaw3TymEkePg/9BRGazUN/8Y+4Qf6C9v1kPfC9S/1OCoXls8VZ'
        b'/jQqZ+jXykl1epOU9KmzE2XWBuKHSKRXarXYDVL1IGbSb4vFYTAZST1Fv1irVym1WBIpZp1JU6CmaYZh1gAbH0sN+q3D+YRiNvmLJi5CTshZ8yqodiXumP0/vG+bRw=='
    ))))
