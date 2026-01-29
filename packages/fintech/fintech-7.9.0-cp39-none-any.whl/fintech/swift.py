
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
        b'eJzVfAdYVFfa8L13hqFXFcHGWGHoiBUbalQ6KCJ2GGCAkWEGp4io2FABaSoWLBELoqCgFCk2zHljeja7ySYxpLvpbdM3m83q/55zBwRL/t1//+97vk+fuc9w6tvLOe+d'
        b'v3AP/JPgJxQ/hun4SOOWcxnccj6NTxN2cMsFleSENE1yktePSZOqLAq4dZzBf4WgkqVZFPDbeZWlSijgeS5NFs9Zpyssf1XZxCeGz18sz9almTQquS5dbsxUyePyjJk6'
        b'rXy+WmtUpWbKc5SpWcoMlb+NzeJMtaFnbJoqXa1VGeTpJm2qUa3TGuRGHQ7VG1Ry85oqgwGnGfxtUj36gD8KP3L82FIU1uGjkCvkC4VCSaG00KJQVmhZaFVoXWhTaFto'
        b'V2hf6FDoWOhU6FzoUjigcGDhoELXwsGFboXuhUMKhxYOKxxeOKLQI13OkLfKlxdxBVz+yA0um+QFXCK3aWQBx3Ob5ZtHxvf5HogkQ+QzFJKY1L5U5fHjjJ8BFCwpo2w8'
        b'p7CK0Vjhd/0ogZNyXnmOXLJdiDyNM43BxslwHWqhBIpjoxZCEZTFKqAsPIHUKeL8ZJznPCl0hcoVvGkoDl0HTdGG8Ggoh9JoKOU5cpVctAkXyCUVn8o/wFqXHiCWU9rw'
        b'SJ3/C23SXcz480USxF9A/HmGv8Bw5jcL8X2+m/HPfBT+Ix/CP1TE/1KsjLNL/sqCkydrrN0TONbothiJMv0aTkzW/KQziY1z8q05p+Q/81xysu8Nw2ixUeVjwVkNmyTj'
        b'QpPtYjymcnWcxgabP4lzk/7owoV+O2DZxq+FtqCO+ct4jTV2EN8qPior3RHHj39nfNdYDceav7D+3vGXdX4eQtwH/F23zlUtXDdn8sMOZML+afgoCZA7L/Tygt0BYX6w'
        b'm9Qt9oqIhgpf/3C/iGie0zpazyA7Rz9EcMserKk+MWJz6ZJekvL/Mkl3PIqkvYv3ktRWJOmYHEe3b7gpHBeYrAlb7yEiMsKZ1CEepT6RUArFUQvDwn394UZ4Ajc+Mn4Q'
        b'2b+YlJADXIaFJVTD/g0mKink6qTZYycHk3Zcn9RxaxOtWbOnR1JcSDBppa1Pclmwa6GJQqGBy74DfILH04kHuVQ4D6dMg+gfZbCVtEOlBcf5cxbkoD8ch8MMTN1oG+En'
        b'iReHTNVcT/QT+Vm9xiUlVgjDb8nDhugNnHrPa/slBiVlf/DbXyZ/lrwmPUr5Urr/Pi9lmPKLZJfUzHRNylfJEco/pCsWhSsVcZHKBtU5vn5AxmdpEcoV3L7UMKVOc1e1'
        b'T7r7zKWzgXOWlSqGyZeE/DDnmZhah/l7Op+yO+bHLc4cdDfmmEIwjqAcv0yKHWC31BYJpYg2+XkjzwVuECmUWi2CK0Z3OqQijpQiMXdDBZRKOOhcJZ3Kk6bNFgq+W/BS'
        b'KCR6ypI+DwEfv7pOT9frNqi08nTR+PkbctXpxpndNsyyJaUpjSo6zmDHTJkdb8c78Va8F6+X9SyhkHRbrFNqTKpuy6QkvUmblNRtm5SUqlEptaacpKSH9lXweiokegv6'
        b'oKuMpusPo+u/7yTIeIGXsafwmyCgSPHcXfqXaQj252uCfMJ8vckJ2xhSFhvuG27BucI2qbvH8PmpQh9BlD5CytG09Eq5wAyHBKVcYFIuYZItbJbE9/n+OMPZs0F/KZfF'
        b'mAZSwTrnAgegkqfCmeHH+ZGtpETsqIWmuVCJ+gc7oSiACyAldqJA18BeUs9EcdBGf85fN0Q99Pw43uBP6VG09Mvk5Tf3kCrSuqeusq6gKWzUzs6C8GP8c+lU6Oz2TE7/'
        b'QMNzh+qtQsMrFbyR2l64tokU+kT4QdFg0hYeFWPB2ZImAZ60INvM/HqUIDB2dNuKXE/X6JRGxnYq/Zy3HS9FputtelkuZSzstkhTpaiNeuYxqMFSCH3YLOipx+vDazrd'
        b'p5fXb/4Or+VU0+aQBspsymnmdHx5zggHh2ZLyV5SQ66bBlNcjwZBk8E4KVDKkXpyUEjhoNYTrjGKz5gSTHt4DrZDh6DioC51sjjpEKldTrskHDmOpMng4PwW2MYMwwgo'
        b'DTIYJ9P1tucJWg7qQ8lBNoucgoPraJeAw+0FHT5JBZjBuGKEKgO0TsTdsn0FUsBByzo4YHKlBmUabGNdFhzU+AlkBwetsWNMbnTafrRCOw16Og1O+9I1L5D9ZLuJqXOH'
        b'lJyAFlMQhaXFUkBDCC2wDZpY7ybogmLWK9BJHQKaN2iFjnkMC2jyI2UGQzBOTXEXtnDQmEG2iljU8blsmoTLJTsFcgT32UhOMXAkpMGX9Vly5BrZIZCjaER8SBuj5vAs'
        b'b2gx2NkI3NJYAS7zE4Kglc0i50kxdNrqKQ8i4KRAajloh53WYudOUplvC00TsRMOuwgYC0igmuxlS0Kh10xbm/GIPOkYIMBB3nrBLEay2aSDNNtCG0U9EK4LsJPnV3MM'
        b'fo0jFBmgJddB4MhhaBPgJO/jD/UMa2d/csNgbQ+XUPviBOjiJ0F9HlvQJxQabdeaoA1NSJgATfxYOInsYaxrgNNQY7DVG3nOnpwToIofsYLsFPtaXKDBYIR2W+TPwWwB'
        b'yngfaAkSPcgNcoRcNDjYI0XcyQGJBT/D6MoUehFpiMV2B56LHiCx5kNNSgYDHFkA1di+VspNRXmEDt5/JNnBusgFNO/VtvY5pFTKyckJyWg+1N1d3KZQR05TCbHgRkGR'
        b'kIPwemeLBqWMt0YhniBDckcJ6SjeC5zFjW6QSivKfAsueAuTxeZoKGMILc0nlwzQBC2OKDVNyCxo5CcMCBHlrZIcgmYDtLHeLXBJgHo+eDo5p5AzH/jdrAH8BGG9uxB3'
        b'M/u2VYTo1H0lg/gpglWCQyA2yp5zYY1XVg/mpwt7soScm9lLJRfUrNEY58aHCp8FW3E385faZI1jjTKvofwTwpSFVqE386s8Nz/BGtuihvNhwk1XG/nNfLdEtyWscfN0'
        b'Dz5KWLrCPhlHJjgtYo2F/Eg+TghcLXO6mX9bl5rNGkvCR/GLhXNaWRw2rp89kjWODx3LLxVyhlkHYuPyM4NZI4zy5FcKt+c55OBGUXETWOPzy734ZOGDAJ67aXBbszSE'
        b'NdoneqPj+GWmjHvKsDT0so41/mbw5TOFD8YJoTcNVYrvp7PGGi6A1wjfDrQNxZELSkTcLYVAPkdYH2IrxzU9Vs9hjUETg3mjMCXNUf6U4faaryayxmWDJvDrBS7QKhnX'
        b'9OyezBojV0/mNwkdeVwyjoyTiRhNnjaV3yrE6aVONw1Lo/ZascbZg6bxO4RvUzmnpwxVdk+MZY3BE6fzRYLVHKs43F2nH8AaL46YyZcKS4fbxyGcU+cpWeNeq9n8HuH2'
        b'REngTcNt98BM1ugyeS6/X6ia7BCII7OKE1jj+ZXz+CrhswFIOkOVQ240a0z0m88fE6ZstMvBkU+Mt2eNgnc4f0LokArczazbiy5nsUZPIYo/J1xSSUOx0eMP+axxRFgM'
        b'f0F4LhVJl3U72G8Ta4wNjuMvCYFZ1vKbWUsj3k9mjd3ei/hWIS6Ckz+VtTTtTU8W6qXHQJnB1gbVbsgKiR0fCrWbmJ64rSEltnoHe4GbAV0SZ34GXMgXBf7CIriEJrU9'
        b'14DRUgG5QE2Gjys5xBQvCRrnoqFBy41uyVaA/fyoJaEKKds/NOhZ/pjkl9VczlO5t6P2zBOxn/Ucf0IyJc2Ou6mrcncUxaHZ4wW+RhKaZcs9pXPj3hH1Y1bgy/w5Caey'
        b'D72pux3/+YCHAnTrnugijAk5C9HvZ0NcunVvsC79l4P1h8IYJ/OnfxgzI4Y5X9I+LpCUxGL+VgHFpBX2hUf7QzFGnK7JUs/pUMTw+AmdCJ0YOjXV7sXZghgqR2it6LKB'
        b'yW6pUbE2yzkWt0H9DGiPDIiE8lgM2axw0W2wQ8jLIuWiHyzUkJNofVpJC2mlMTy/DG3i6PWMTaSNlLj6eGHEWxSAsYxdhsQFtjrCwaXM2MJJ0xLSYkMuICAhXAi05Okp'
        b'BUUFdcK9MPcOlG7UPJ2TIzaGhFpyGMs6OeVmRAXGTuLYKr6k0js4EL9kJZF9nBI6cljCuwYd2aFIFlBX0FQ2klQEYIh9PZw0ePGc3GjhoI0XTW6FE5QHT2AunVST/VwK'
        b'RiOXTMOZo74x0QczNJYIY8IWLuUGkFMjFBIolaaIzvqgA7nBUpR1UEqzFHKWHBad9RVSCduCSTMiB5fSSTXmM/ugjYk7OWpFSoOD6bdyd3Kcy/D2Yu1wjBxMCA7GuHqU'
        b'nJxEFArWsvbQOC54EjVlGD1VcWkYc14z0TgMWmfOjfQhdREUuhiRQQ45kimI+gETPR+YsGpi8CQEIGM2OcypjOQs4+g02AE7I6NwQgCU+fCc7XJBOhMa7WCHQmD7DSPN'
        b'9sGTMFgkVZEYZaB27mOkjhkLO4IxM+Y0+RhfZMwj9YyCzqQDE1pMbqItOGk6uT6CJ6fmDjCH1BtJQfAkVBJK1WNcZhQ5zkAntaTI5EOZAcUxpEHK2c3A4AJ2Ok6FErbX'
        b'0g2GYII+nwuHneQEp3EfL0rjVdgaASVRETRNksD1kXCDJ0cxoCozRWG3PAOuGqLCw6PpIUdvZurlr/CO9lf4CTbeieSMCsP5WlLj5UXqXH0UZD/U+Awk+10HQc1gchZD'
        b'k90DnTB4O71M88u9e/eshkhFOZyUE1Vh1HFm9714hk+MX5iUk2qgMJQn9e7eioFiVxfs1xns9SYJJ4zTwXF+9LowMR45bz0EWhxYB3r5WmjjFUpSLAYK20l5JLSIs9zC'
        b'ESUfNzElyYeOlQacxHPCTGrHPDyggaldMNSQGsNakw32kPOwj1zl5eQ6yi3b6yLGgDUYDuRCqwUnOKdi6DYyf74o7tcXjcIYDFrtceZkNKJN/PjlyWzaKnIWbtg62JIK'
        b'gZMEk4rl/AqyHQNyFuaUBZFig9EmV4rg73Yl1/lhZEe2uGIn7M2gXbgVsqcLtvHyFINoHKrhJBpiox5aKdqnoInc4IfGrRY7G+Ac6UAIDhig2SjjeNQEqIiey0RwZMgQ'
        b'Wyt7GxrYlrtP5sMWoawx1CrICXIdI921dgg/7F8JR3jP6asZsUbDaXdbBztrOuni5ml8eA6INgqnVMNFjI30GHpKhkOrAz8ZDpIKUYUrF7hiFzSjl5HAuU2j+NmyZLbe'
        b'kJlZhrVsnywdaeNHoOE7KwJRPWWLwYZxi+whV2AfL4cjmGrQSVZr4Jwt65OQCxoXPpA0OIgRc/t01LtKNMlHUYN8Od8kqGKrbfRDB1biSG5E2Kxdx3NSjOtI2foBjAwL'
        b'5bDDjNLUAMRoFKoPM6zXnMjOXnE6Co1UnMg+5D9Fab7U0wweXIYCCl4+KRQpUQOFI3okDTPXM1TWSMMKNm0j2U2azNKWaKLSBvs3KqQMyJVZZE8vI8mxuZSPcNSZzYsf'
        b'RLryqLvtw0U/pq0DoTyFlKA5uojhNuYcaB/IFZ5sC50rGoEi2LaclOSiYJRAmx0pRoWCIh6Tg1Mp6PJimHhNhz1kb49UbiSHqFReyxJZd2JOnFnw3JE5KHcbMcWixPaE'
        b'0zN7pLV2DJXW4csVDoyk05VyWxtraKYMqlodwi+QjxDF+BppG2sQKRqNmnCQHxluTiwXk4uTzTqtJ5eoUpPiOaJanISCkbZWjN1wklyx4f2XwxVRSE6koGK22LFpmfbI'
        b'VU/SgArPnMNWUqtCIbbTUx6dGQJneM8wUsr6gjIxE3KANsxphGmkAKr5MUiQZtFQ7I/ehGpti/IgxMJ5aOYnrYxnjI3CRMpWj+y+jCijaJxHxvqj+RahPEoaocasT46k'
        b'HPWJnFkiQlmGqVCXLVy2XivjJDGk2pOfCmeNbLd8qEpgPTwl1XQvPmQKpu50wYmjlxhIWQ7NyYS0hYiaAlWsTkTtXIgPgpjjKEM49qKdK+bHDYbLJnp4ELoKtyvBZKVi'
        b'HfraMhS3hkmkDg7AIdSLg4lwYxjPjV4tHWSFftKZ2bHVblAZKFhiTILJ5NEEUwxtrbINg8p80ozTDpGiB5baj617cAvau59cIugK8e9DpNAa6rHpHDmfuQaNfCc5YU0O'
        b'zzYrTDQ0ju+hq2saJWsIiJyCq+lkRy9h1wVSsq6By+go6bwZwXN6SEcuk7NIu9HkHKOQqz/Z1Uu7w/AkEo/U2ZgWUQaTYnLOFsqgYE0k+r+waH/mrnygLDrCbxEUxcZ7'
        b'+UdTHwdl4YolYRh30Fi31ZDIGQbRQ9WGgT2Hq07kgIvdNDRKTLXrya7IXhWdyjMNvYxWaSiLRjZ7iYqY1FcPUS+7GCKbFnn0MA2u0LiRH7c6HpGktiYik5RE+vH+ft4R'
        b'UBZJGqWc4xKJhnQmMB22Wk06qZstE2MJK4x6dkCVgFk17BG3PgtPwmEMH8N8I2L9ZJxtpOBMbsDxtbBL1LtaQ6ZZ7ZaiwqDaoV06Ik49PMvCJyI60o9ujPGji9GbHJeQ'
        b'S2j01aZ7UyWGFzBGaXxSt2pxZOzA2U6Nm1/65g9fRS7ctsrZw+tG4jynsVkpVgvu3CqxDJu+WJ7+8rhpTo6104K0UZ9M+S5zyks5k35zqhjxm8Vd2V+e/8X0iq+zw7uv'
        b'/TM/ISkxMSF20dsnFuu2tKQVzSu8kPP+p2nSFx2a0n5yT0q+8tdPHVT7X3tvnOXYT77yyY+49W3W87aNn4y6G+ftNe7i1netv8xd+WKNc+fN4u2DYp7xj5//yXYgzwYV'
        b'xWi6Lr0QWji6Ys2F06/OcX/5p22lW9wsPp5fPb8w9Ejo5ryahFFfz3a698zfXgqtSQkgX3wlD5v3zq01LyiXjhz/hONPK4vIl++Ebv8878wPZ161qGjYqLnydPp7o19Y'
        b'b/vcV4qd5e3vxTrdu/3u9RUbVv64/k7CJzYvfTzo9jYoXbfUJY1PGr/hyLHje+e/smdh8DdvzFyy9J7vkukeTvoLS8L3Jk4zHWpvXHfoH08nam6m+Vh0zX77Yvbri1ts'
        b'kl6+dbC5OyLzxcXPZM3/+7KjXO4PG8/+8bu97tk+0Fj3wW9dY5d/92liyQ/xQfr17XOLv31vnPOt93Jdvvr78updkWfKfpy0wKIyIW/k4Lp3pkV8pKi2eDr26p31K5/t'
        b'2NZUtNaQ+JXLy5nvhxh/+Bq2dxUs+37VrNhN3wxv3cO/mTdT0vncmqlvLV/08pwbujWdpRP/FmU/tfE7yVChIuqznKGHn/vbnQXVnqovxz1Xf27M4qcmuWQPSVUerX3+'
        b'w9Cz3ncl34ysv3AnYL7Kpj66PF1xSBXwyj8ST64fkdtoqICVV15wePPDvz33j+HD/7Fz5/s5zu+4NJ+589cPvvDsOHfpmY2Lim6ZVhhOrBxm/V3qLz/lZBih/Fht0y9j'
        b'7l78dDPcKteubxmb/WJb9LTX16aS1NZxEwOzF3e9/GJR7LMBL17x3ei6avoxSfudzlePJoY8V7Fx8Gc2M9bIyz2PLzgUe9cv3OLL7wOCXK9t+GDNDwPXxF/a/Enwwms3'
        b'J2aeW6jbcazrVM6nHspbnl83lyvsjTTrEBbBDSjxjcHIFSp8MTwn54V0cgoaSSHZzkYMgmuePv7hvt5wDk4r/HEUFGOyLJeuJhVb2H0COTAAY4Le+wSpsyO9TiCNTxip'
        b'qVhDKkmZj/90zIeKoBi3kJFywW+CL+uE7dHQGunrFYY6h/o8fDlunzcCOo3Ur8odEyLD80hbtHe0JSeTClaDSbGRJZ3X4coseuSL60Ex2oMKCeZKFaOmSeAoOUeeNDL3'
        b'9eTkaIx92yNj/dC5reNnY87UamRhfSnUwnkff9IG5xSw25dDkC4Iwc6w3chigJmLoSQ6ntzwDYdy7JsgOLiSRiPLgS7LSEEkvYeKDKfRPtIrTUieCEcHkP3sSN0Tukb7'
        b'ePubMbWG49A6TcBE7wBcYLczpDWEVEai8UL76xdBryVc4PIm6JBAIalbqHB68MD9P30orP+9OfcP+F3EA36jXqk1KMVrbHbO/w4+uDk2vBUv4wfydoIVb8c7CPhNQttc'
        b'eBueXv1Y8Tbs48LL7knpR3DCv3r+43fBQfwu2FjKeOGeTLDDv1wFJ1xPKpOyyyNXfMrwvxuu78o7YMtAqZTv+5/29jyl38ucXNjO4mwHtr8N7jsCny70I9hgK/bS3bCd'
        b'rmzDIHalcPAOd+2kNrzerocOCkm3XV/0+9xe/HtUVfB6+x66suXncj13G13DHn+34Y39Dp75TM73QFcMKQtQYCbqE4PhFxN6Hxm3gFywJPtJDSlV8MzBqeDSvMhw33Ap'
        b'qtZwKQbIR8kucvChgyMKDzvPiePYwRG9RucevkhPt+89QBL+pQMkCbvtlf6UjRvYyPv8i6PSZJAr+1dAsLKKvByVPHrx1AmBcp2efRnv329qvz/CjXK9ymjSa+laGrXB'
        b'SJdIUWqz5MrUVJ1Ja5QbjEqjKlulNRrkuZnq1Ey5Uq/COTl6lQEbVWn9llMa5CaDSamRp6kZk5V6tcrgL5+tMejkSo1GHj8vbrY8Xa3SpBnYOqr1KBGpuAodo+m3FLvZ'
        b'FEel6rTrVHocRQs/TFp1qi5NhXDp1doMw+/gNvs+FHnyTASNVpyk6zQaXS7OpAuYUhF1Vcjjl/BDGqap9El6VbpKr9KmqkLM+8q9ZpvSEfYMg8Hct0HxwMyH5yA/kpNj'
        b'dFpVcrLca45qgynjsZMpCyia9/ebgy0aldq4QZmpeXC0mVf3B0fqtEad1pSdrdI/OBZbU1T6vngYKCCPHpyi1CgRgyRdjkobwsiJE7TpSiS8QalJ0/UfbwYmW4TlCVWq'
        b'OhtFATGlhHrU0FSTnlIo7z40iVCTqTdpHzmaXomHsCeuaUrNxGEG/MuU/TioUzU6g6oH7HnatP8FIKfodFmqNDPM/eRlCeqDUaVlOMgzVCm4mvF/Ni5anfFfQGWdTp+B'
        b'9kWf9T8UG4MpOylVr0pTGw2PwiWe6o18gcloSM3Uq9MRLXmAaHXlOq0m778VJ7MRUGuZllJDITejptI+Ci1WRPA7WM1RaZQGI5v+vwOpvuFFSK876+uLeu1djs5gfHAB'
        b's2SoDKl6dQ6d8jjLTXmtUqc8BmLquYzKHuFKRM+FW2k0j5Ew86b3xbH/Xo8XzX+b7noVelFUuhA5WhkcuQiupWaliBs8ajy1RYh8UpaqD6t6AEISaOCawaDS/N5UIzr4'
        b'xxDRvA4d8WhgH/K4kSZtmkr7aI9p3hZ95CN8df+NcczvrZGxrr/fXUC5DTXpRgNaqnQMYmj3oybm6JEBaPOUj943ztyt0vrF6P0fB32/vR+C+9H+3ywID8QA/SY/Nh4Q'
        b'56px60dPDJ8zO+bxYpek06sz1FoqUg/bkFhzXwoTSFRg+Xy9Kjst97G63nflf0GgxeH/pjHJVKK3eaTJW6BKgWuo1o+wCf8NgFE1YHpG7Vw/uBZjz+8rm1aZrbpv7cxx'
        b'sdwrBpsfKacmfQ6Lix6asUSlz1Vp06habshVpWY9arZBlaMM6RtY4wJ9ovpHzFih1a4KkSdos7S6XO39qDutbx6gTEvDhly1MZMG6Wo9jVJVenWqXJ32exF+CCbVymxq'
        b'NhGmxZkP1IP3nxhiznNCMC94lGfoP7rfjT09/nDlHryxjxUrcVxsJZwx1wG/JUcdGJolXnYvWS/l9gx04bjQZI3b+nGcid5xG93IDlJCWiLIDbJ7Euwhl0kpPfmuJ2Xs'
        b'HFwIggbSwE2HCxbkhAvZw248lkIzjmsR6M3vdajhpo1MYztkjrbk9tPjInly1FcWIZx4N30eyrPNRbcu47nUWHLANJJdZ8yFfT5itmvj2yffHelhMYTshHaFvYlWyxvD'
        b'MDMuCYuOCveDkhmEHkDhyEg/GeexVAo10+CCidaMIkg19IQqICLcj+wOYIe8K63FY94gKJP5ZESKR8A1GxPNR8AHnjCfArMz4GRH8Qp8PxwlFyL734BvJIclUzINYqXI'
        b'xQxoj4yaNq3vdTc0cvZseeiEk7ZQIp69Q22gwFlBp0B2jySnzVgvSaaLhyMKUDsUE36oCAiDMgnn4SKFqvw8VmtADpJOUtkzLgaeJO208LEcimnVwxgfi+mrYkzjGNaj'
        b'oOX+eu6sPpKVKMRE85yCXLMgR/JmMjr6ZZMne1fcQM7QnWkJAo4bk2wRSmqHMgBDPGG3jz+U0YUOQa1/RDQU+ypk3FA4KiWnteQEQ1O6Yqh5UHgQXImG3XTI4EHSwEVz'
        b'WcnIJFIeZOZtwrIHeAtFUGsKoMDvcIQKA6teXuRFT0BoVUUiFJF6OMV4nBAHZVIu0c+SHCA1U8Xr8O0mUho8nlZ2H3KFBi6NlLuIfK1dD/UiY0f69uWrg7048Txpjgoe'
        b'b0EvrzbDk1xmAOlkd0IJcH0gVNIboWXrucAYUmBih3gVpIjsfkAMoGCsZAo5QWrFy8atpGhgZBSUkIr+oiAjVQqBbTqLHJ4ZTJpzZByvhrYojjRucBfvbqt9p2MHXeX4'
        b'SlLDZelJtViOUGIzv0d87Jb1SA+0k0aFjF2smLxJeXBwjoTjoRbqIjnSAPtcWU9ArjQ4GC5ZcPxwcmURR1rJVUSR2ojRcGZIcLAe55DLcC2WIxfJaegQb9dqcO0OnNeM'
        b'8zbAlSUcabOEJlYx4T4rODiYZ8Wu9VDPZS0VWQCnoW1jcDCl5OnRCzkNlJOtTP2j5a5cYO5qqv6bmqYLnMkRG8MHexlwjXmwV8vNC5ewgTkxzpxRugC/JGtub3TmFBJR'
        b'd86oud6bn3HkOI/Y04sfUhcs9l+Uk8LIftdGC8lliQb2ixe7pIBcJ1WRrBJ83nCplCfVqaTIfLMGpQbYIRJuCBykdCNFvHgjV5tLGs2U08NpSjk4TppNY9mWcIhc71Ww'
        b'EtL0oMbOIMfMzJ423dFM5BaykxJ5IZom8Up0LtSZSUxOwDZKY2hYyzbwhzPQdF/RWxCD/ooOW2E3k1O1rbeZG1vgMpe1ydWkoDi3rofanvlkOzQ8ygKQC1DKbHE2nEkw'
        b'c460jeM0m0kVsw0W5HRaLxDkSNSDtmGXik3XkkpJcDDVveonJnOZ9D0MsfBT5sBZuU5lb3O8PwF3HchMSTxc8ooM94vxj89GA+HVc4o/lBRKyRm4DBXsmnFBcD4tq1H4'
        b'hZMjU6WctaVAymE3KWc0dZ8BXSJDyZFcxtHIdUxPkOm6XlmBa9E9spK4TFSjsqAgnwi/SD/vGPrGkWMGnCc3JCqyn2f2dfYyqOot5RoPZayaCylG64aGRknJPjg1XzTE'
        b'O/3I3j5FX2S7I637ul/zBed8RHtxbjUcN/uVDniyrwGKJyXMQ1kh8KJBIWgt2pf3uYf0TrVAN3k0lDkYK9KMSIv1cWQ/KaA1cjuEvHH5JvoiWQoCUddbQ/ZEprmKjJaQ'
        b'wQ1ykQEzHiW4+UHbdZacRuNVjAaU6VJtNpRHRsWn9zddZDfZIRLwNDSM7CmLgiOkWsLqoqTQJb5z1AxtpKiXAaQYdQJ2R0EF2qpDVFOQ6OPJIVk42Wu+lQ2dYIcYTQ65'
        b'f2kLx+1c2F5xsIu0+4SPJGf7VW85rtjIZi7mNvcUg21YIqW1YOh4rjLZkcJpax+vcNLepyDQES4mimWLO8eQQ711i+GJcKpP2SLZo2eL50FBmChg0AB1TMLIOa14/10U'
        b'BnvNohlAtppFM2k0s43Wk6HBFgOgeFdSh4LeQY6Icw67zu0nd6QoRKIyTkMTQY3hpDlLmTF0C0GDWDmLiXgs2ethS199gbrN0ISufxRpNdFaTF87R/buiJ96JudH6h0Y'
        b'3zSkzO4+2S879cg9VE0VK5ZXWHGlYWhZkpM13pGrOWZkMMArWdcrxR5Q+ZC8h5kLx+wHLMPeQ5bUAcJ2Zy6JdJG9THqDl4p2ikkvOUdOPyi+acvE2/eTlnCQtARKqE7A'
        b'yVWcDukvvlIwhtTlQaVjIDnmgNp/wJJDci8mRcNM9IJiEVz1sqV2vaeAgdoLdKxl8VAUju0BUBxHSxnCxDqGhXGkOTB+UZjvQijKILv6hAvkgr1TrI0no9Y8lNyKBzwG'
        b'nJRo/OAko9bPC224laP96ftddks9tdxi9ETUYqvCUQMR7itkr6gcsiTBO2+6WCnVyo3sv+S60RJNNGkQw8fD0BF8n0Fd9xl0KoiVgI4ix+f3hE5w1bdP6ARX3BlQW2Ls'
        b'OafRk1Evkn3vjkjgmNpDgfUg87Rk0v5AVLYpwpRIITtJTikM/eiDsVZJwEIvfz8v1A9vcxVjPCVtke+SMKoZrGRyIaMjjWz70LFrozP6gZKhrGxxho0Fp7EZRJMHO/8N'
        b'U0SgtjiRJ+8r2Byo7KNgcXDW7BfnkaqxpGUCDYLg+vCF6Hn1sUzYQlcOp+08esU2sgP9buM4DK0mMusURrZBJUHO74WDmIf0LcpptJgAV0lzyiJjCrk8kUdiy5bBcdgv'
        b'1p0gKBfNq86Bo3RRt3FipHOZXIQuMyARrhQOdDPnFVIxPDwShIybtBbdtze5GoHTgi3FCqldpG1w8AQZDTjhsJJToTJtZVOGyklV8IR1uBHsTg/lSB0pChZ32qechvvA'
        b'JQ679kE7+vtmHTlrvr0j54NIFXYH0d7tcfMxAoT2DNMTtOtJr3G0jqcEKVoSABXoQO1J04SguF6hX+S3RJR5kVGwnVxmzEKtrLaBI6vgGnPUK6F4DjmPMG8iNaORJpcw'
        b'+6DIzDJOJOcnkSaBlXSVuHJQv2oOiy7mrZ9PzmNgsJk0ZXKbXUm5mXmkyzRYfDMS48RqfF4hx5kyKzC67EIWNVhQoceYnEbYVbAH51HNi3VCDeqnJSi7nRLNaChiaoBe'
        b'rAl23PfgO8jhHk3xi2EbeGeRdlpX2mbPc9FQL0A7PwGdTonJiwYy8XD1Ed5nuEdf3+OBpstNjOXrSbW5HGmeVqDFSHAVjjFAV2Jyhd6lHOlR2tc3rYA9zO4ZMPvcyqKY'
        b'odD6cBiD/q2AFZmbpjGvSUrgkm1MNJT5LTHrHhQnhkUkhC2GS/7zKDdJHdqxaD//mKhYC1rLdMmG7NxMKtXPNAySGl7CpTIWbDAlRFcMnefU8M3htmeTrq5+++rQQm5u'
        b'2JyDe5yEMSPdyIKlyQNGjhnFvzr/Ttwoq9POI04POqF1CAqTnJ3aMOWXDzrlO6acHja63GrtJ0VOs7ZKPGOuNX6n9W36U+a7r+vqz69OuP75y9vdB/1oyqkcFjR1Z0Kq'
        b'/dLOQNvGuNWdC3PHBb+RtubUayWHLzzRln5q2M/BCU5v7PkppPOPR74benpK1ksTLN8YGOL4WsAHA3Keu51t2Xin3r85odHOtOHt+gmvrFmy9nLsgDPPverbWv/twTbn'
        b'1+5VH336T60J379Y8FF5wl+Sgu8csX/T6cODws+jT73p/E/HoSP1qaE3b1i8MeyLlWcKO1Snh29/vdV5/WWbyw0ftk+Q/+bv6FX80TvNxzY6ftp9J3/+HwfNbt+6Tnq9'
        b'8qmjV6OSPp/51KL8O+/FxU7/R8I3GyacJ29c++Lr4juX1fKfLr749xUuPzk1rxbeGKxJvAQ3Y7irsUvvyW87Jw9P/ptjftKsQV/xga8+n33CUbB/1bAyffGwV4JH/PHW'
        b'rc2/Fnoc+Xml/dk7M1+O2lZUleN+6yWfkhfXvOH8pzd++Wxrx5dfhA/9GdYnjWo6XxA/fMaUSX++WX76rKnr5/ynHd/66Ne/VDzhaf/XjKEzR1XfHlm47PYzq7/5rjH7'
        b'q40TX3gvJGdt1bHsrzf+c+U3vzj/ueG19zWRf2jVz/j1D7Hr7i6Za+r267SqXN78cvGnJr285Y59XcMzFS9sPv3ShPPfKjJHcQ5fd6guVBRPOrHwXMsnrx8+nzZg+Cy/'
        b'4ffeln2Wz32Z+1HD94cF76gtb8UfysoY9PYzw5bcyrBck78ptmFZ5tua3/b/9vRTP/v+6MJvFH7uLP7E8yz/3vSJ8u/emXLzB/XhtZ/njvg1c9Tdndd/eX7580cD7vzV'
        b'/UOPvLvhsp8PnWgLzB/w/pqnXxHe1FosW5I+8ceokRXtUSf33FoxdCc5vO3NtlfGDdkcY+xQhEzvuvfx1my9i6760C9vP+98+9Ctu3J1wbu2bWvgb6bn/7hkVeDuhhfg'
        b'u9gOz/rfRl0ZXPs+NP4QuXPIsynXV5769s/nnvplyPygdbsuhn3U5XBjnqtufPWtjfLXukomP/Ouw4e2Vh/51NcM+nD75x+P++eAdfD2hcIPN73/4z+WlcQqX/9ham5z'
        b'iM9LVwryqqy/eWno+x3ffFqY/ey6k+N/25D/c3jll52fZUeU7/zx+UXamW8nfFR9Ie/QgU9/8h/761fbYz6uPZw10H314TUvnXj26AdZ17pPvJb48ebPvsvavmrwV6Z3'
        b'HNONM6babLR9/eh3sza9/rbk4m9+kvlvrDyxVfaZ1xez/H56dn3iF6r3vrxV/vw178/fmKHV/nbRrUtyL+vVVRtK1iTdtbRaWfWz3E3haBwtRtMHSLmPWDMExaQdw2Tz'
        b'IdZg0iYNI0WhrFRqNOy19vH2pwVLNP3lrJcJmCntUoklWGXkCFRBSTSch73365ZmGYzU6awZO8HHPwLz+j4FWLAr01y8tWqMuQBrLZyiNZXnhTwMwc6I9Uo7yAmcV+JL'
        b'DpOt/YrEoHHLcnNJE7kRaS7GwkCntx6LFmOtSGFDNqOd3MtqyBQjYHu/ErJaYn4nvROOevvERPtGQPlc2EEznU4hF5qsWUlWPLTB2ciAvCjYHYAphixX8Hcl13u2v0LK'
        b'IhH83to0RwyXoEuSYQ21IopbyQ1MhNGOF5EL92O2ub6sGoxcwsz6CC1Qu96nGAzpKFZ0keOb4IBPhBU55ofB5v2XpMmhVCONc2RwSgUttCCMNORggnCq54376VJMixYr'
        b'Bv3/Lul6fJmR/X++zkMveGcbp04IZIVfGlpDtAX/u1j1KcGyYYVeVqzsSuAdeBdBLMCyEQT+Mf9/kDnSMfTXAezYfDdW/EXn0IIsh3/KLGz4vv/F1RzE2Y9fl/7/UjbY'
        b'gZfztJyM7uAmceIdWImalB+Gz4G0jExwumfDy1jhF65tLgoT7skk7O9/2sjYrv+0k9FWKwnCJNgJtLDMRYRMsGHw4EegpW0ygVZvjRIEnC8VoRWL0wSxFM4Gd3bjB+KM'
        b'IWwn2T1aKudwVyYVsXMQegrnnAQHXIliK+OtBD1NCmN6KtGk9M6gTwXaf85rBa936uE22+tFymWqUtxWrn3M4+vSRrDUuGKL+Z17qPCjcSjNXoqG5EigM2PtQ7+CQEUn'
        b'lC5P02MV/VEebrmQxi+XpAniz4N0O7GbEFYlpp+n1+v0v3qIdyNMDPXmoi9Vmlyplatov3+MQtptlZREL5OSkrptkpLEX9/B73ZJSWtNSo25xzIpKU2XmpQkyvb9B8Ob'
        b'hrcfIXSsttFKEM91bjiQ/bYO0G60taYo+ulpxn6AaXUAVMsswuG0gp+v/rPjdQvDCJz8aXHyjIrOGAgdOC9D49nUEhBz7NKu/MJLutmn/iLx2up/a+/RMMXNQS72bRNS'
        b'x9yVe7w4Rf7jkdyL5e9d/+uL+R6fH/F/2mVq2/vHW4af9yxty7jyw/m142Nzn7sV7O9yb+V7gwcK2zZW5+0a+vbF02F3bn0fP7M4PHG3xui0bGDq4c6AlEXDflsVZvtC'
        b'/MTXrbIj9g+YfLkzPu/jna4Ja4oPhfxZ/ceanbFHHfhVG14KekUo8W2Kqh60ZFnqk/aT3ko5OnzdW6nVEoepKYFfn92XGjPl49If6iqXR3jV+VauDHrL9LHXrB87Pnj1'
        b'o0+N8YNNKw5FFZzXqcOe+Tj2wOK39iRA966X6w5+n+C0pOOTcWtbqmfu0M600rqP265Me3adb/y29QNX/yKxfnGpIdtBIWXFvKREYoWZCs/ZkVp+CofGuGOm+IMlpaTN'
        b'hv1aCdlm3/8HSzAvMrKT1u1QQEptvWkygO6ld5AHaSH14VJM6spJjXEU4x2mWq0GX0zmGsJi/HoDcmfYI0FDXw1FKPZM+l3+Cw2xjEX9j38wA4uyq9Ep05KSmHWdQ9XE'
        b'lVq3CfyIe4JAS1/RlgpOVk6WfW2h9O8yO7Ot+4fMatgWzlpAi+FF7bK7wOsH94g3qpSAMn/fYDj/16DK6916lYluTr21WNr6lf/jTQh1nPkSDFpK6FET/Z0oUkwqLDmy'
        b'HfY4uEuGZ5Cz6qiJn1sY0qnPURcMfybIYXuo064/bUnPtTemnBk3Zv24i4FNy6dFfh4282fXnHj7ixuUJ+uXJWX//N27Ry7eOPPtvXcHutZ9kqsOadyw5rlvrZVpNsNn'
        b'ZMj8pyRq3wkvjZq+eu5HXpFvai6f/fVjy2fC3d7ykCksWYW3f7qU/YZILK1lj7TkJqXZkmaBvslDOlg8MHWgZWSsHzTRMeTM+Fg/AYXrmoScXObHxHmxAXaJaNFjSUQR'
        b'0YJGUuPgIhmxYAkLx6AJs859keHRanKhp7R9Fhxn+0/GWKIkss8PYmXk2CoEjJ9qzSXo5Djsy+37i1nTSCP7wSw5XGKK5jKP7PSJwPSxmrTwkRxGhTcG9wi9/L8tGPl/'
        b'lSfp7yqMWqs2mhWGosrZW/XUm0t8t7DgJEHv3qsCo7olGpW2W0orjLstjKYcjapbSq/S0ZuqU/FJq0S7JQajvtsiJc+oMnRLaaFRt0StNXZbsJ+26bbQK7UZOFutzTEZ'
        b'uyWpmfpuiU6f1i1LV2uMKvwjW5nTLdmgzum2UBpS1epuSaZqPQ7B5SUGU3a3zKCjhcDdNmqDWmsw0jrDblmOKUWjTu22VKamqnKMhm47tvt4sa6h216MvNQG3ZRJgUHd'
        b'toZMdboxiTm9bnuTNjVTqUZHmKRan9ptnZRkQMeYg25OZtKaDKq0+xov0kCun0K/09e/9b70Qa2knt7A6Olb6HpP+qByq6c3Rnrq//T0EF9Pb5D1ND/RB9EHjZT19HBG'
        b'T8vS9fQ3h/RUi/X0xEVPz+X09BpfT821nr4+rqcVBHo5fdD7XD2VXT1VIP1k+phKHz69poMyzbrXdPw94rGmg4381arnN6i6nZKSzN/N1vTXIen9f5xPrtUZ5bRPlRaj'
        b'sNJTA0VjAqVGg/aRCQs9Feu2QebojQZa0tEt0+hSlRrkyyKT1qjOVrGARD+th6gPBBHdVtPF0GMmDXNYiCOlKi0KpGogQm3F/x+X4RIZ'
    ))))
