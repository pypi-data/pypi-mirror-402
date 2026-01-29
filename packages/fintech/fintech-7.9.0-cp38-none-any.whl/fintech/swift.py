
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
        b'eJzVfAdclFe2+PfNDAMMHQER29gZuoINGxaUjgqCscEwDDAyzOAUsTdUulhQ7IIKCtKbDUvu2ZhkY5LNlqxL2qZsmptNNsmm7ib/c+83NEte+7/3e8/5zedwy7mnn3Pv'
        b'PTPvc4/8E+M7DN/G2fhI51ZxmdwqPp1PF+3lVonU4ipJuriaN4xPl6it8rlsqTFgtUgtTbfK5/fwamu1KJ/nuXRpAmebpbD+QS1LSI5cnCjP0aebtWq5PkNuylLLl242'
        b'Zel18sUanUmtypLnKlXZykx1gEyWmKUx9o5NV2dodGqjPMOsU5k0ep1RbtLjUINRLbfAVBuNOM0YIFONHoD+WHzL8W1HSdDho4Ar4AtEBeICSYFVgbTAusCmwLZAVmBX'
        b'YF/gUOBY4FTgXOBS4FowpMCtwL3Ao2BogWfBsAKvguEFIwpGFowqGJ0hZ8TbbJcXcvnc9jFbZNvk+Vwyd16UwG0bk8/x3A75jjErkVVI9F6FOE41kJs8vl3wPYSiI2Ec'
        b'TeAUNnFaG/zcHS3msE0+zSrVzz19CmeeiI1wCOrlUAJF8THLoBDK4hVQFrliqb+Um0Ruzw+XwB2oJI0K3jwcByfBrfXGyFg4sAZuQGkslPKcLFJEWkiFRsU/IlTXXjSW'
        b'U67wyJd/gysZrhbK+UIxUi5Cyvk+ykWMcn6HyEJ51pMoH/MY5WEC5UmpUs6e45xzJ6bF7Bnjx7HGd1MZOzhuaK7flpEhQmNguA3nzHFBnH5TTIq9r9D4zEIJh//LfzMk'
        b'x370QjuujtPKsPn1icMkX7tyEZ/z7076UtQ1ef70DzmtLXZMsTnOt1hz8iDNqvFvGvapPhCaG0O+cqpw4r2/4H7n/pOnr9zI9XBmP+yYCXsnoQhKApeRfLm3NxQHRvhD'
        b'MalL9I6KhXK/gEj/qFie0znZzpm44zE+W/cSHUL5THnMZYj7OMn/m5zMeBIn+4D2cdJO4OSHkxw5D/EM5FBqTPiSaM4cQAfMgFOIf6lvNJRCUcyyCDgIjZF+kSu4KdEJ'
        b'7qQikZSQo1ymlTWcg1MBZjec4g27XeA47A4mV3EJUsdtyAgxD8UOsp80kcKhpDOYdNCeM1w2uUT2m6lWz1iyfLFX8BQ66hingsNLzVTJ4BSngCNWHBeAKnsrgFxTMExX'
        b'T5MlhXHeKPVU+3/kOAiSnPDMkG2pfAR+Sp3doI7kNDP2ekqMSvzbxz30YerHqeszYpT3MwIOeysjlJ+muqqyMrRpf02NUr6SoVgeqVQsPaOPVjaqL/P1QzI/To9SruYO'
        b'qyKUevVhSXFNy6WgBc+UKkbIk0K/WnAvrtZx8cHrz9qfHsYlxri/p31OITKNxHVsSGWmHfJJEWv29xlKalDYIs6dFEhsFsABkyf1hpuhHblZDOVQKuagwU8ykyeti0Yq'
        b'+B6Rt0IhNlCZDHiI8PGDx+wMg36LWifPENxcgDFPk2Ga2yNjPiwlXWlS03FGe+a07Hl73pm34b15g7QXhELcY7VRqTWre6xTUgxmXUpKj11KikqrVurMuSkpj62r4A1U'
        b'SwxW9EGhjKPwHSn8d5xFUl7Ey9jTTKn2GUIu+kb4+cSRsnhUDCtyPprzgN2SYaSadC9WiQaon+QJOo3+o0+nRcw7iFGnRX06LWY6LdohfppO9wIerNPSOKZA1n5GOAJd'
        b'0IKa78/5k5aJTEVJ507SCEfWkT1oZoFcIBwlJ1gHdJGj5DAcmUBqmNYFkPqhGqX6pMRIjWHBH+Mfpq66e5AcJx0H647U5bdGjN13PT/yNP9CBtWvoIf2GX+OEXOVpTZj'
        b'Tz2v4E0jKMg60kjafaP84aYRCiNj4qw4O9IqgjNusN8inSeJnTG/x06QcYZWrzQxIVNN53zseQmK2CDrE7CECazHKl2dpjEZ6CADdUsK0QChigw0kg2QLJ3u2yfZPz4m'
        b'2RA4HOAbkTVXkC0LJH48NzxHQg5tMZjdKW2VI8hZo2lakIQTSULSOKiFS4ITCN1C9tAOnhNFklY1cmHFbLMHdoyMJi20Q8yJxpGzmRxcIW1kD+uKgKtwy2iaTqHBXmcd'
        b'B/XBpN7syZxCCBygXSJORIpIo57OqyVFzK/IyD5y0QgdU+lq5MJ8ks9B+9SNbOI06CTnWZ8VAq2dSvZy0GFLuhj602fDOaOBTUshhQizQQOnWQ9pnrAJ2s2TKSppVujh'
        b'oH2Gq9mLkrwfbpOrrA9xWQBV6K+gAy6Sy4zuOYkjjMZggYIdOzlosiUnGSJr0VEeY9OQ8sxnyEkOriHeZ83DKNCqSXCFdVpzovHkFDnFwXU4RUoZX+AkHCC3oN1oL8Ml'
        b'PedCJx+C2QyFCtfgwlA7AxOAPdwhtRxcJfmwi/FlUjy02EHrVNpJOqAKY7o4F4osvngnVNrJpjCWnSQn4BhvGwzNrA9qeWi3gy5GPZxJh3087wUNbEFXBHTBCO15johK'
        b'LHRCNe8L3aSGIRoHxe5GWwdqbSJpCtzhp5F2qGJ82RxOrtttMEMXx4mck6GVn7DMjs1xwyFFRjuDCefAATEc50etJ2VMCE5hSLMJrtphV/p8KMOVmtMFjpzGfGaf0dEB'
        b'GSKekmXFz0Gful9QPKghu7HHkefE4RNs+TDYnydQfIkU22DHBkrUKXIdrvEB0JUh6HE+OWxj55BLSiWcOBpqx/FhYyawWd4+0EJVBLWHFJD2XA4aSSUpELBojoBy1OUQ'
        b'KXa2BWegkuuhjE2bKyLHqR7gtNFwgSpkG0b9ZobhNtE4I7RCuxNycLQ7NPEh1vPYpBWu9kb0VayDtJJ6qOeD3aBNIWfxzegwhA9BY3898W6OZ9TXS1njrQ3u/AwRt7Rs'
        b'8t2cB8np21njpqEe/GwRF/TSNhy55LONrFFhHsaHibiI7xzubl+p0q9hjSHLvPhFIi6scOHd7ceHlDmzxrINI/gIEeetC7y73XPJfS/WeHLoaD5GxM0gadjoma5kjaEj'
        b'xvBLsXHdyLvbH+h8YlnjKxvH8okizrMpERvnhFmxxsLN4/mVIi539FxcKNYxlzWuc5rEr0GU/rwNR/optrJG3QRvPlXEycfZ3TU+2FC2mDWOGe2LEYJbelX6rPH4cONK'
        b'1ngx25/PwtVnzr9rPO7c7cka8/wCeC02Phv1rHFl5rsxwvSkID4XYaaOv2tcmbV1LWvsXDWFR5+6qXMCwozcmsYaT28M4Tch7d+lIsxlpfascbHLNH4brh6WgSOjywV+'
        b'usyaye9CitKG4cih/HDWuFU8i9+LnK/wwNWHh6eyRrfY2XwhMiR5Na6ecX8Eaxy2aC5fingmpDxrfBDvGMEa1y4L4w9io00wwpzXqWON38Qu5CtEmLnOfdboOW97CGtM'
        b'zVnEH8eRL2zGkRG2gji+1S7hTyM/v96IMMcfS2KNr02P5Ktw9WPWd7OPu1cIeEatjeEvo9zXht/N9vRaNZo1mvVxfAMuRKKfzX4wastMQevylvItVMHG3M1+sPpPkaxx'
        b'+7DlfAdOj/d7NtvT4f35TK0NJrQ7Oxm1O90Se7S7c2gL1ExIG+yJszM4OqCtkhNiFzTWTlIhuPU95MQMTImu5hnRK5LKOPQZvmpyinlachlj8Qn0Nei+qXM4SAqggh9L'
        b'6kYqJAwN7ep7/Gkx5zxz87N5D1xn86zx7NIX+SoxlzvK4a5+5aqZ81njVe7X/EUM9fk2z+o9jX7xrDFr7n3+Mk4vXXxXf3zL+jWPpd+2vVlFGMf1bv36tzhchm1fKi75'
        b'N1PxzEfTFmfLe3DaMjfOTLegIeQsqVbuICXxcABzxaLI2AAowmTSI1UyaRTZxdCv2SrscaombvU7P10rJMHf5tiyPc7BjG0xHy4yccyvjN6UHh0YDQfiI604Dxcb2Cva'
        b'jJw9KPj6i3BuKGknHTQl55/hSEU2aXD2EDzmZXIme1Owr7e/DxQGYt5inyl28jWZKcqbMa1qJu0LJyEKoVwoqSNXDZRnDIsTC63YpuoLhTHGw80sNG7YZs02akv9d2jJ'
        b'0C0cS/tHTSRVdm7BQXS1w5wyxV7YuJ6PIDeiWZpcjgwojSbl6A8LAiNJozfPyU1WjqQZqhkeVjsw6lUMDabZJKng0sidEMZB0oDuer+vt247gqHbWdyCRUq4IQoxlI6B'
        b's4L/roKb5AjmNcf7Nh7zSDHrkkF9OLriY8Gkje5UznFaDDhtTM+1GI6LFpBdwcF0zlkucw2cZx0zyQWym5wODQ7GlJlUc+vDyD4WXYamkT3IrvPB0+iM41w6boNOs023'
        b'n7dHdBTFLY5KhxwjV604x1zxjBxSwqibCkehZPus4GkUiROcejxcZqaxilQFQCUfHYPzAqHMl+fsVomgCfaIFCI2kVxN2LCSHAyehgEDU42MuaSD5cNJiXB2+5rgaRTD'
        b'U1wmlPozOxyDCTBuTKIdMAMrjbXiJKN4cp40TGfoe8BlcsIaqoOnoYGQ01wWuUhaGfrB5AaUpUp9qVygKI40Sjj7OWInOEkKGRdXk06oJXdGB5MuilMVpyVlpFJIo4pw'
        b'qSooiYl3iaJ7ITHc5jHvqUS1jKdjj+DEOmNMZGQsPbro2356Byh8YgMU/iIZqVGTWhx00dub1Hn4KkgFXPR1IxUe7nBxKLkk4kixm3M8OpgqNenQfvfzzz/neglaGZSS'
        b'GRMxW8ExFKfDcVLgG0d2kW7/CAknCeNJ/YZchRvrVJJCcsXokEBqDGb0T3CWH2dPDjFhp5OTc6HdUTNX6OniFQHxzGiSab4P7Q5QHyV03eZ9neCMsLvYrY8zOq5dYjBT'
        b'f1bBj4abQWyhEbCHdBs3bETqZTQhu8nLlXBEUNIuuGjAtGDxyjzooDlsKT/Gd6qQ/J2FvXACc7GEYOhwoCBb+Slp0CqkNBVk/ww7x50j7Ug5Ot5V/Gq4sVToKSTXo42m'
        b'ZJ0sjyaGt/gRSD7r8XcgJZhw3fCU5dGVdvNyqN0puIImqFsD7SaoFBugg/rq2/zwqJUMQ3FAmBHaTFKOR2sglX5os2UgcAmaSP5yOxu5iwPuNcTT+Qhv3O5TeMslaEXt'
        b'ZtgFVzbYU8xP8pPg5naB4hOkihTYOU7NtUcPjBE1Es6DkAmvWT0B0yNc4JIB80+xIz8dykgtg7gQGVWBnbM3QhuNNGP5+bixOCdALEJF2WfcAPkhbDXSxY/auVzo2oW5'
        b'3zmjLAUqBXEd5uXmMYwbnuiEr9jJSCscoV1iVz5IG8isKBEKfdGgr4jRjPw4P1LsIjCpK9aHlDilqWQbNvKcBDM7VPcTKjZl8lS4YOfoNL6XJM5bEOE53BTcREUauaZP'
        b'kdDm84XA2bFmnVFGOklzH2rkRKiAdvcitJ92h0DS1qdl3lOZ6Sc5DzM6kirPPiWboBdi7SlymGqmiRwa3S9DdTyDF0wuwu5+KfpLoHwTMnYYm7fWkZTA1VXkCAZiMzoH'
        b'coMnuyfOYHtE2EUuY2ZbkgenxkOXPSlCG4JCHjcUe3HHwKioJh0j7BzhDibyvao4yUVQjzvrZUaTu75P3eyg3LL9ihlpNGVAVZ+KSmGvwpHRt2LESjvZemiwhTYUSii/'
        b'ZOZwNmcWKSWXjY7DRgoMOcaPCYOjglpDiY3RAY6Q/D4z3vqMYAqHUP4ddjaOG5mEZbgjKHZmWPuT0+ug3X6HTpjShOp5lQj5zHixFaou2Qet9gbaV8NP2gBNQsrSgUGx'
        b'E9l/meyCLralOcePx02aYF8+0DUMTZnc9rBDNRBBGz9tS6wgnGrJdDtDNLmJO6pOCZNnALli8TXI43aznc3csF4rCoMKxooMcn22HXTGbbXdIOXEk/iZvhLWPm+bFzbP'
        b'WmO7AZMxbz50BelkCjoDGhYaSZlLTC7bhyFVCnIebgiJwA1nqETkZjjlOuF+Bor4ieQamp0Pi4zkylbUgSOkfCP6lTJSTBqz508jdaiqlWgIx5J5btw6ifscHdP1bdBA'
        b'DtKAF2NNj1uD4pTmOGzO1JNT2FoJlaSwD4wA5KwCbbcScBImi5XY14Jb7KP4N261bKEemy6TK1nr0alfJ1W2qFwXnRnSmSI3umPaA619DMUN+XHBGk/MHmZnIFW5A1g6'
        b'jhRggGSGtx9XqEQuwdWUXu5BA7Qw/s2ZbY8908f38s8E+8zLWbLkvtoOndtROBWNIS8iNoCFJ18oi43yXw6F8QneAbFRGNSgLFKRFIEpx3JogQ5jMmd0pweljW69B6bO'
        b'5KirfRqqEVWosFXQjGQMmdnP+SZSj4jSGEsOkFO50QH+PlFQFo3tF0idhHNKEmsTZjCVc12jp7GxTEgDMBxcsoHjInLUWcGsNw/2B2D2UYbpX4RfVLy/lLOLRgtIGGLJ'
        b'v2W4+aa2WddnNRi/2gXTroEzMt8oqJ0YG+1PV8cM0JWcFZMWaNNoUg9ekBhfxvSiouHNtYkvxbnNd2tMfjXm2/tBxbL7hd+FuSxb5hy+IcZe+Unc0AD5hg3v/6rjRLpX'
        b'Uq3P5LiYLX+KVq00fcX7lY5OW/Od1Y786Pfr3nBw8Vixdvsrty797cqsHG3R/b9uMxLZ4bXvXtw5d0jS4U9lyy/Oe9/2/tebPy9e45b2rZWV+4efZW9f+etDL777x+LK'
        b'xMD0L6uX/2b8Sl4/qeGdhHHJSR6u06N+e22Y/npX/UG3Y3PPzjcZPrr+O49Qt8nrcw/42OU4TFUd/WeH168bb3uO5DTi719+YdE+03vy7/M/OrEywzCdfKIdkT7lk3dD'
        b'Ppl82nnY+YItY9SfmAOSUo8988m2GtPu1th7tT7a0Cb+DekUY1T1S69vVbw3+sc3tx59PvxeQtIJ/8kpyak/jmq/p9IctDa9eFLx7j8a2jJWrZzzWfuHK5X/ujL7tTXy'
        b'papbAR2pnQnXu7+6dfPNoabnrMavafzg6q9eyU6++o/uxcl21xvPbJD1+CS8uP8P3cOHy6fv+Fa29sB9r+Th3zS8+r1+3+vf/bRl886JS0Z9bg73+dMbtW3bPorcM2ft'
        b'w5J316svPPiwJf3L0JeHTkm4WVAX+pfg8u+eCxvV/HDl9BaPFl2a/2/9V51/Q5wf6WLKrPrTpwEbw1/qHr357TfOhY385z83jJSdmC5710szx+mT2zluPpM70oZfNuUn'
        b'rbWZ3Vb9/Nr0cWdfKF/j/9nJaS88/HhS4rNdy1WrVZ/0dMUqtVPKfvDcsmvdww9K/nB9//pT54ctu7z+/EffvfGbkIL7pzoWKKu37Sw49cVq1Z3Pn9+h/GT6Gu5b56m/'
        b'e9Ep9+UhaxJXvX/lt4XPvbpm1utzDyT+Ztx3jfLM+79aPXXCvS+P/PPOla3+o2dlvPdyl2FIk2rWiciJ5Zsaii7EPXDMqFpYUvjq+Ob6v/lNKXlm1Ct7Vqc1fVlbE/Dp'
        b'+3cc7+8fFjv2gPlDp4Ob/1EQmT0j+efi1ovP/3h7enzVh43Tr7lmj/gsIevj13pspu5UkGfn2e1VpO7+XuHAzmwXwGF0MrWzocQvDtNOKPfDDJtcQY+5daFpFLWNA0PD'
        b'yF5o8w2I9PNRBOAAKMKMQS5ZB2egwkQNU4d2cpAe9q/ASM3O+9lhP2maaGJHfpfhcp5vgC2mY1CE4KXkgMif7CWXWa+/E5yO9vOOQKvjOVJErtvg6pvJ3pkm5toKSA1U'
        b'REeS7sWxPrHWnFQisvGEbnYJAVcmjPWN0Dv5+SBYTHxKoVzMDZklhlNw08PEwslNaJobHe+P0Wkjv3nRfAxaZSYWqS8Ej/UN2GFQQLEfhwg1iILhWjIjBgNl8QIoiYVj'
        b'pMEvEg5gd4jIEU6TKhN1Umvh2vSZO6LpRVF0JM3UkV3pIlyy1Z8hLJop9fUJsFC6Ktd2loic2wxHGa9Jtc+WaCgbIqNu1D/KDzeprnBNDAXr4KTC+dGj8f/qQ2H7H5vT'
        b'fxTvKhzFmwxKnVEpXCSzE/k3OaowMt6Gl/JuvL3IhrfnHUX4SUzbXHkZT69kbHgZe7vy0p8l9C1yxr96X/hZ5Ch8FsmspbzoZ6nIHv/yEDkjPIlUwi51PPApxZcnwvfg'
        b'HbHFTSLhB77oGhI2Bv/6UursylYWZjuy9WW47ih8utK3SIat2EtXw3YKWcYw9qB48I4/2UtkvMG+lw8KcY/9QPIH3DP8x7iq4A0OvXxl4BdyvbcQd0YMvIVgycd+X7hu'
        b'uWAKVOBm0Zc0DIuLCRB021fKLSEN1rj7qwlW8EJSVzTPPjrSL5JmoiUTMJ89Bd1ujx3uUATY2Qu9MSzg2f019/gNdoZD3yGP6BcPecTsbkpCryM5mXzAv6VUbYxy5eBi'
        b'A1bBsDlXLY9NnBkSJNcb2IcpAYOmDvoj0iQ3qE1mg47C0mqMJgoiTanLlitVKr1ZZ5IbTUqTOketMxnleVkaVZZcaVDjnFyD2oiN6vRB4JRGudloVmrl6RomTaVBozYG'
        b'yOdrjXq5UquVJ4QvnS/P0Ki16UYGR70JRa9CKHSMdhAodrUojFLpdRvVBhxFayzMOo1Kn65GvAwaXabxF2ib34/FZnkWokaLOzL0Wq0+D2dSAGYVkq4OfToIf+RhutqQ'
        b'YlBnqA1qnUodallX7j3fnIG4ZxqNlr4tikdmPj4H5ZGaGqfXqVNT5d4L1FvMmU+dTEVAyexfbwG2aNUa0xZllvbR0RZZ9Q+O1utMep05J0dteHQstqapDQPpMFJEnjw4'
        b'TalVIgUp+ly1LpSxEyfoMpTIeKNSm64fPN6CTI6AyyK1SpODqoCUUkY9aajKbKAc2tyPTTJczDKYdU8cTe+kQ9kTYZpVWTjMiH+Zc56GtUqrN6p70Q7Xpf8fQDlNr89W'
        b'p1twHqQvSWgPJrWO0SDPVKchNNP/blp0etO/g5SNekMm+hdD9v9SaozmnBSVQZ2uMRmfREsCtRv5ErPJqMoyaDKQLHmg4HXlep128/8oTRYnoNExK6WOQm4hTa17Elns'
        b'Xv8XqFqg1iqNJjb9/wZRA/OI0L5wNjAW9fm7XL3R9CgAi2aojSqDJpdOeZrnprJWa9KegjGNXCZlr3IlY+TCpbTap2iYZdF+dRy81tNV8z/Md4MaoygaXagcvQyOXA7d'
        b'quw0YYEnjae+CIlPyVYPEFUvQsgCLXQbjWrtL001YYB/ChMtcOiIJyP7WMSNNuvS1bonR0zLshgjnxCrBy+MY34JRubGwXF3CZU2XMwwGdFTZWASQ7ufNDHXgAJAn6d8'
        b'8rpLLd1qnX+cIeBp2A9a+zG8nxz/LYrwSA4waPJT8wFhrgaXfvLEyAXz456udil6gyZTo6Mq9bgPibf0pTGFRAOWLzaoc9LznmrrAyH/OxRaGP4fdCZZSow2T3R5S9Rp'
        b'0I1m/QSf8D+AGDUDZmfUzw3CKxF7ftnYdMocdb+3s+TFcu84bH6inpoNuSwvemxGktqQp9alU7PckqdWZT9ptlGdqwwdmFgjgAFZ/RNmrNbp1obKV+iydfo8XX/WnT5w'
        b'H6BMT8eGPI0piybpGgPNUtUGjUquSf+lDD8Ud8/KHOo2EafErEdKrwdPDLXsc0JxX/CkyDB49KBbdXZfyT16qx4vFLgeCBVuzIM2ztzZ7mMpFY6RCQXAQUlrojPm+3Fm'
        b'ehUMB+EMKcFXOymeBgdJJykNI3vpaXU9KWNn16LJ0EgaudnQYEWqdkIzOzd2lkAXKYezpB23y7O4WWS/B1vj9WyhRjlo4prM14flcOxUXwI3oLr34lkxVQXd5Aa7upZA'
        b'Q5Iv2+jGxWhy+/e5Y0ZbeZHrTgoHMy3HJLUKUgIlEbExkf6kGMoX0joBKI32l3KjV0rgogdUsnF2872gJDCKDgqEK/qo/rPcyVAm9YV6UmNmxzA34bK3r6V7BWnuP+2d'
        b'tZAdB/tBC+zqv632g/ORwmU1aYROdlQNl0gtOTb4UjpqLTTFkMPCElWOpBVKhONyEW7OORu4LkLki0mpQFOldhpdIRLpiINdcICUQXlgBJSJudGuEjjuQi6aaVW+P5wO'
        b'6RtHSxMPQFFgnNXKBdx4X6vZ5Ax0mSfgMK9F5FzfsHQUI45kNQVxsTynIN1W5GTeZPN4uvA52Ac1A0DiqJLAyFh+KGnnxqdahcHRqWZ67pepCfENgDKEFBAVC0V+66FK'
        b'IeWGwykJuWC3lg0hJXOh2jIoMhaK/XDAUHfJltwgchURo4Xs5DjcjukVMezzGixjqFWY/XHUGrLb0+jvA8WBy70j/HxYIUQyPUNzIxfx44qlUCbhkv2tyVEonsD0D5qh'
        b'2SZ4Ci0WqOT0onRSu44xXgvV5FivbE0B/aIlZ2azGxvn9XAzeIoVKwogNbKsvFVCmey+VajM+aQdjgg3OdmkgQF0tVf2awJpgG6LKsANsofdSvC+5PpgRfAmB6CJ7I5U'
        b'iNghjYIcgUvBpC1XyvExunkcaQogtcJtV/OYIOzgWHEFHIGW7JDFTL08YR+50ac+nkm92nOc7FNIGf3JaZ7Bwblijo9GY63hSGOShC02fyw0BQdDixXHL3eZQG/pWki9'
        b'QGEh7JoVHGzAOfGSqRxpHkdaWMd2FdTilDackjRkPke6yK4NwozzpNg9OJiWQpznoGNENsn3Fo6dmuEq1AQHUy5e4KBUrCVlC5n5140byvlR859bvTIiII4TStuLyK7t'
        b'LrlGBBTOhaNq3GRjP1rpTL90MiNIuj7xveRETiFmxkfqoY6c6r/oiUK9FO55RsIdxvFNPi69t0RzUWhNwiUR+qNdAlfLTAvpoZgVJ5kIbRKenJu6HEXBTpOL0HDrLYxD'
        b'hrch4+ZBt3Ar2Igu8Fov70gHKUDujZnHrJC0LDL1mcz2sY/YKqmEfbgAXXsuqZxi4TEc9EImk+Y81rF2a0Yvj2c5IY/RsV5gBhKHOtX2BAvf6scsfHgeE3cm2TepVxIb'
        b'tmajgtWz8iFywyqy343cdH6C3fujy6JCiyBtlDxBZuR2oBZOk07mElaT3eTSEzwCqQkXPEIplDIsQnPWBgcLRUJwS5kFt0kNk+T0KY4c2opnUMa8NcVeWziFG+MaLY5B'
        b'24j0jwtA3+BNLX9YDj2jH04KJAic3BEqgq/lkqu06kXhHykhRSrO1lpEDiST8wztNQGkxSLNZaSeSnMI6WBGMhWOmPvVRAk3LWoCHbOZmujJbVLoG+Uf7e8TF7KIfsvH'
        b'KVOsRoe0l1E9K2vC4LorZBopgD20tGd4jIQcnmxxwcHJ7gMHRsF5Uj6gPms4+gGqt3PhFOzq9TxTJgzwPPmkWHC95c+QG4IzIQcCo9LJ8f4I5aOyIldIm4OgpqVTZ/SW'
        b'sYWSPRyrY4tJZSETTkI3nPT17qv1kqn6qr3gpD3zWfxGUtTvtKaRU70+ay/Zx1ijMGAIGFxRlT8RfVZbuHC3fxPKx0JJjKVcqXiyULF0g7SzY2oFOQyH+zhPirwxLJYH'
        b'QnEMvfuJpoyeQiqlkeToJnbz6jRhyqAr2ZnIZcwbJjFUl5EaaH2kqgrq4bqTFt0Wc2guo6AkWijVgs7xtFpL7CXca++D2vGDKvZSocNpzEwWmqAiK/BJNYUJiklk9ySh'
        b'WuMSyZ9mUS3SkUZVi+zVCyrZtX5dr0ZKoVrQSHRjFWZaxxgZgFP3zrLDzCcBXxuEjOAcqYZui7rN2dSrbqgUF9E3uDK2nUDHuRtOWhxh3DqhvqVhDBTb0e+eQB2qCLSR'
        b'YwtBKGEj7X5whSYSR4TvdGSPZuIRp87u13tyk7PoPWlyYdb4Q4zw5a+gjDbez32J5QtyF2zhyGP6Dp2qPnUn1USoX4dDk4BVL1hTleXGDEsJG86SDNK5A8726y+G/ROP'
        b'KLAtVAs0lZFb80h7kJhWVnJwZ7yeNJBbwj18w4p0OOLkCJ1wFFqhwJqTSPhETK0TaWc1+sUjdvT6v7fmgLoNRLQsAQojsT0QipbS6oMIofRg2VLSFpSwPMKPls4VYTp0'
        b'tC9dIA0OzvFwy8zUDGrhelhv0IDz6/qCRitUM6bdSbfjkHiboInDg4ZEBnGJGI0oJYtFEdGCmYy25TlpisgHBXSUiWEJJs6FvTDXpvSBLLVnCpEV5d4vJbg8tdc77Ub/'
        b'w24vC6HN8/HkaevSIFIkFCS3JjhwyDLvII8tMZk7Z3BC4thKykjFoMzMn5zry8xIKWk0JzNnA/lxxkFcwhVLApd5B/h7o8X4WMoNEyiDC/2SIqipMENcZuFmLyfJzekc'
        b'ubPVhZRNhHJWXuiVbNlIeExc9q/kBZxZThe8PTvySRZHmrwnIR8KLBESzttYkfYQmgwtMyow/lpbvtoybB7ZRTt4Gn2r4TItxOsgV9gmZS00RsERghpwCI6higwsqmmy'
        b'Im2jXdKWm9JI51SM6qXSZzZjvGJ+dA+5nNsHcw90IkxnqBNU9BapH9aLiCu5g5iQbgeFxFJFh2zeHTxtAwbyKH/SjfPIrpGCTV5ycQ0OkbK8Eyo2qm1ShFzpADltDA7Z'
        b'iCuFQQXPkboh0UJaUUROm3EdaEG/nLSQdHCkbQs5q+AFH9RCajdh72TsXDxSi3kg+ujdZnpJSLqXwMXV2bQIpwSZWhII5QnQ4kBaQyYv7dP+5f5Jyx8RF4fWeU6Gsbd5'
        b'MsMM40gNuYW8vYJIb+O2kf1whXnWSRu2kivTSKuIE3mQaxoO6n2wx03QsRNQhcnLXnIF84Ud3I4hQy1ODLlYT3blzbZ8VTFgyTA2I3jZPJRPoxUtaeTiVBjKihbjDGom'
        b'y0mzT19RTxky0mIns0YJfvNmuEe/nawghyx2EtnrShpJuQHa86CLln1KZ8FVPiR0qJl+mQv5UmMzIA5hvnr+SYFoBqoDRTJ+zmojdFkqjwy0+GiCkG5DI9QuG1w2dG4F'
        b'xqhWcpnZHO7PzscPymOgNKg/kSGHYC+rCDeHMrlNXGoXFwtl/klQ6AKXmc1BUXJE1IqIREGApA59WKx/QFxMvBUqFLTQr3UVOWoCz1zgjC8jpD9NP2peEV0+PNw5esjf'
        b'nv96073ytc2fvVW2kBsiT7e1dZbbKuWziSh678HCXy0cXrSwaJG917uTF9iYjYX7QiJGfOj2lz/nf7TH+b1SQ+mM84XBSxy/50/PyH3vodfn91xLFp9t+qn2xqcP65vf'
        b'2He2JGrbpWbZpIgZRcuUvx+/dunHJeftmzvOKEqn7jtd/8811Q0nogq+X5MkUoWtT7h29+SLs95f9tpJ39++nlhv/6X+zxcU8vsbO+3WQnjXfGX9l6uTPlS7rI4sqz4e'
        b'pWg4bp2U9PbyaWP//s5H9VVZr9d9fzT0Zs5fPogb4931rHTsmsq7OxZ/PfH8z5pxi3QTRA9iUz9LPDpl3qKRw2vGNHSV3b2S8OJaqztHF/351slCv/fMV7r/pmp42Pat'
        b'YvEfPd/ie1Rfb+T1nx75LsnBym+mW0jEH37fnnLp9pISqTb84dtno3qOa97+eWLznVeWOY15uDl14T1d0EbPB5NTv5388JznLFGD9V9/+v0f/+F7bxQ37uhboh/kS8+c'
        b'qw29cPG1se/zK9Y0Xdr5cfWf7j63cqpX8fU6Z5eRTReOP/fK4n/oprm8ds8U4vL7vJcb7H5Ubms+dCh7T8KQqZvGr7g7Kjz21I4RPxSeO6z4w0fnWuNWvf1q17ZFocf2'
        b'O95qabz15pHhXZ2f/6E+++Hd56qNXe2f/yN7zoXnW/RHf9bN6q5NqP+70+32kmZZfYLuufCPf1+cEz+n+X3bb4u7Nuknz3nlq8bQ382+OOQ3e6WOn11bURrfMq1q2eXg'
        b'bz71U3eVFZ/7oPhn9dT1zcp/7e52CF0xf9/3+q2fGt4a27H2a+WZ7bf3rjr3ZkK2y4OAYe9MeGdDy3bZlqJdcxx+/DrxteDgssBXJ+6Zc9Xxi20Htq758czuuT2FOzcG'
        b'7uha9lWt8bs5r/5z3KvzfO/+NPv3Hh98/l7D4q9FuX95/aA6Z9SFDNfN3WqfIr+3e+rHvz5+3Rtzh2d/F/76u9MefnH/pxf5N/464/btX/09r31cS2DLdv+He956qUuZ'
        b'H5/48m+mnR5V3uCX/2LgtUleX8vqh34wj+h+e+Xo6dIHWxoXv1vXYv3+t0GjlBkfj11ye+sX/m3bjnzv97b4xE/P3J78txU2k8K+Usi+KrxetbXmxc+JbvOpRC+/D3Pm'
        b'ncv7WLK482Njc9bhRc1bPy448d4r3V/eerhz+4NvtKN94I2HRu+KXPHQW+W/G1kYmPTbiWPfriDzwn8cFfjqXxceqnM6VvHrvJcX1Lzw9x9iqu3EPVLVkXfmf6bakq8v'
        b'5G+9+EB9723ioLxX2X6hJa9lZ/D3p97+ZuN7nXdUd1882b6gRDI13CrOYNWd13g8vLMy+95Iu6+ifzbmvf9O2pcu/wzcsP25rWNvfxPY9OaJpGkihZOJJe7Hc5J9hcIg'
        b'9CCW86uhpEuSSK5E+IlZLdQwmp75+gSwsiRoWsHZPiPCBLkqiBUtzSK1I6AklhYl4a5TqEuyiWFVR5NJ8xgLcFI33lJipR7BgE4OJbd7C6zgErRyrMAKjklYPZNmZdKj'
        b'pV/o0e5A06bRrGYpOASqaEkKQzsibUCRVfwCVh9G9rqPf6w2DHPWxnWYMtcx7OKHk92+cbF+UXCAGwEXEIHrojybKKHAq4TcIRWY1xUH+k8ge5GqPFHAKBHDzRFKnaIR'
        b'bQaZXMesFKE7BYkzN+UJcw+vJnss6VnMWkt6dnqUUHS2dxXc9GWcJLXkVm+R1x47oRLrIuYRZfSbyv1fU06DG3BmMpwTqt7q5auhndZ4kcZcdjIl4txnS7aS22Jy0KRw'
        b'//9drPX0AiKH/zqcx75knWOaGRLESrq0tFhoJ75cbQYVV9HyKhtWUCXiHXlXkVBaJROJ+Ke8vpI60TH0+/j2bL4nK+uic2ipleO/pFYyfuBLgOYozH46XPp6KB3qyMt5'
        b'WihGV/AUO/OOrPhMwo/ApxstEBM5/yzjpaykC2Fbyr1EP0vF7O9/yaRs1X/ZS2mrjRhxEtmLaMmYq4CZSMbwwbeIFq1JRfjix4pEOF8iYMs4IxUJRW4yXNmTd8MZXogR'
        b'nUGL4Bx/kkoE6hxFvSVxziJHhGTP6rxsRAYn5Hdcb42ZhF4SDKgt+6/LWsEbnHulzdZ6iUqZNnG7uKvjH/3eu4xc9fKNGJXFSs6g3J9mlxznlSuG60ljH/vtAaorYRQe'
        b'zQTV9BduuFWidH6VOF0k/JhJjzO762B1YIZwg0Fv+GG0cPvB9M5gKetSp8uVOrma9gfEKSQ9Nikp9LooJaVHlpIi/JQNfrZPSdlgVmotPdYpKel6VUqKoMz9D0Yo/X7d'
        b'B4gdK1O0EQm71ZvoL+7YOcJVk50tranzNwh2nEGuc4FwTmoVAUUKfrHm5oiJEuNInH2+231O+fU4CHMLz9ROam0PjDvdsn/7O3k2riNHh83/ePmI60UVojVjXkuNDl78'
        b'ntOXraXiBc2bv/3047d+vP3mt4eaPlngd0j1Y87xz1bOUXbM+d2ZlLIjm28sDDi74dB3H315u8rZ5s2C+8FvPtgxMtw18Ni5L5+JubE8/cLtyvwXznu+dH+7y5H3vvh8'
        b'waqlZ+vrFmclnD99re7lW7/2Dey4vDy6+/fVcfkT/bf1mGw+/q3qwGaPlelF6h8aWn7t9VDb8qLHG39teWnUjyNyX3B5/nc7fGa+WxH8yvXjoXU1ew//esqL7kfWJh/4'
        b'cmF5dFPMjrjp5mVXzS+GXPvp2P6vEyOPOjwztSHnwen1ihQr5b7huiHTf/xk4ccfXvjzgfljPRdt1D4/xb1w0rv75gWsXnnqb9sVEhM9AvROl+Heg/eDRo6fweG+5Iic'
        b'1eJ6QT5c6/tFEMpmN7PlB0HILZMcR2TAxWQ7H3S6NPYJg9ZL0KuOJu0SaHaPYIPINah3NJJGOECORsT5e/dW9brAQTFpGT4S1Ztpuet/o8OVslz+6Q/mSFFltXplekoK'
        b'86Imah0e1IuF8KN+Folo8Sr6TJGzjbM1bq+EF/+f+vS91N7iBX+U2ozYydmK0Jd4U489TMQbhvbaAdqeCI2j35W4/Pcwhzd49lkdXZzmJUI5618DBjoXdvfTQY6Tqxjg'
        b'6ZlTUXwM7tDKrd3hIuc4TDwS6kiRpmhpM2fMwKHXSn8z8t5kxz1hzvtf25mR52BKq5k4ftPE5qDXbVtXzYr+JGLuNx65CQ7NW5TV9c+k5Hzz97dONt+u+eLnt9w86j7M'
        b'04Q2bVlvq0yXjZyTKQ2Ykax7M7I0Zva6hR94R/9R23nph79Y34v0/FP3RwprpqukICmW/cRHvAZusq2iNSYAbSK4rCT5QmX5rblJ0fG4Ob/pD610YLy/CHWwW0yqnbaw'
        b'/GDzJFIlUEbPJnFfW25tJPs4R1fxKNIqY8XnGmi3j46M9Ykll+2EwvXMtSytWQq1tAON5xA5Z/kBKjuFCA7mzmMV6KsN9uznqbyjB/06VQG5aqKOd+aSJF+oFUVZcXw0'
        b'ZpWRUNNrFfL/sazkP6s+kl+0KI1OY7JYFGUg52DTW1Iu9tvJspQVhmF9Gj+2R6xV63oktLa4x8pkztWqeyT0Eh3DqkaFT1of2iM2mgw9VmmbTWpjj4SWGPWINTpTjxX7'
        b'nZkeK4NSl4mzNbpcs6lHrMoy9Ij1hvQeaYZGa1LjHznK3B7xFk1uj5XSqNJoesRZ6k04BMGLjeacHqlRT0uAe2Qao0ZnNNEKwx5prjlNq1H1WCtVKnWuydhjz1afIlQ0'
        b'9DgIKZjGqJ8xLWhyj50xS5NhSmHBsMfBrFNlKTUYIFPUm1Q9tikpRgyYuRj+pGad2ahO7zdwgQdywwz6mX4/20B/g8tALywM1PgM9Gvihkn0QfXVoKAPegthoBeuBnom'
        b'bKBnG4bJ9EHVzkA130AP+A30F4AMdNNi8KaPqfRBz+EMNLAa6He7DfR77AY5fQTSB02qDVS5DdPpYyZ9+PZ5Cio02z5P8X3UAE/B+n6w6f3Bpx7nlBTLZ4uD/cErY/Bv'
        b'3sl1epOc9qnT4xQ2BuqBaHag1GrRATL1oIGqR4biMJiMtHyjR6rVq5RalMRys86kyVGz1MQwq5eNj6QTPTazhSRkLk14WLIjoeYrqKDaDbG24f8fgCyy3A=='
    ))))
