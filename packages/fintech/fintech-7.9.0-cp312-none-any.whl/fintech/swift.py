
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
        b'eJzVfAdcVEm6b51O5JyhgSbTQJOTKIoKkjNiFlpoguQO5oAREFEQQyOGFlMrhkYMmJ2qCe5EWhxtmKSTd2Z2LjpOcmd3XtU5gOg4e+++3333vcfuHKur6qvw5Trnf85n'
        b'YNwfe+TfHxbjyx5QDOaCUjCXKqY2grksCXuxAfjDXzGrm2JKUoNiNgtIuN0jLUuAzGAeC9fwijmjfdZT+LeeZIyGAsu5BhuFvKcSw9xZyTPyBFU1xYpKiaCmRCAvkwiy'
        b'lsvLaqoFM8qr5ZKiMkGtuKhCXCoJNDTMKyuXjfYtlpSUV0tkghJFdZG8vKZaJpDX4K5SmUQwMqZEJsNkskDDItdxKxfg/4zIZnX40gAaqAZWA7uB08Bt4DXoNeg3GDQY'
        b'Nhg1GDeYNJg2mDWYN1g0WDZYNVg32DTYNtg12Dc4NDg2ODXwG5wbXBpc94BGl0aHRstG/Ua9RsdGk0ZOo1mjYaNVo3GjQaNdI2hkN5o3WjdyG00bnRrtG40a+Y22jbxG'
        b'm0ZWI9Xo3OjaaFEiwGzWXy1ggSaXURaudjMALLBKMPobl91GyxRYI1jjlgs8XlK7FCxjzwFLKYMyISujaLy4LPB/VmTTHFrCy4FQL6NSn3BiBQuQulqzZZVLpkQBhSf+'
        b'4WCCbqJm1JSZlo0a0SlH1JIpRC3JM7NEPOCTwEE3vdBRIaVwxF3RVlO4VZacjrahrekmM9FWChgms6BGISmixs1vOTp/Pb7ssmjAa8CsAZhdXMwOPcw+A8w2I8w2E8wq'
        b'M8w0C8xUqxJLmjlYe5rG9Gs1i2YONY45rHFsoNawRpjzQu0Yc0r+c+akMcxZItEDxiCYayIoDFhsagToyl9C2Jhj/V6GoNBY60Mxlc0V+sAcDLNMCgvTnhjkMpUhLA7Q'
        b'B0ku7LjCtOzgfHACVBri6vdS7a3zDL/2AuChz2PWxZD6WY+oSmJin+QoKY0esLdLLgz9UKqqCwF09ZnCx2Y7zSggLnhA/XP27vJgMAQUItzgkRiKpdQclO3ri7YEJYnQ'
        b'Fngibxo86JuSjrYHBCaLUtIpUG1mEAv3ocPPiYMzuuNFRBxsWhxEFKCEPcZw9n8bw0tfZLjeHxhuxDB8i6kZ4AMQ1zSpME20MJPZJtwcDvvwRrf6p6KtqCktOyk5IHkm'
        b'CE3NRYckNnBnHmyGu0ApVw8dnCBUWBOKm+govBoGL3FAXCWAJ0Ad21dhQ7S1y1ccBs9zADyEmgDcDyrgoXSaxBDT9IWFYpmjUwDuBkVIvYomsUfd6CRq58LN8AgAgSAQ'
        b'bUdn6cVeTTEEmFSQ6VAYEGWexMj8hMQKYBOK+6tJ4fwjRmmg/EiHBUe2DLeEGkd2vjlp/7qmQ+097csjPNj2R4JLOsOCrR/tijsz/9c4i2MZX/pF8njKLd6qb6y/rLTj'
        b'bTZ83d17xmbr3YavLzJ/Z+5bWQjkGeUNvLYP7n7t7XqqPsYhR3c0LnyloYeyJO1h66Kkhg8+ec1YbmYFY18x3lcOTPl2/QXnhawnfKIs6IK5EWagUG6RrhD5YYVhARvY'
        b'wNFPReufOBDe7EMb0BbM5y14h1uxjk+YH0fBntgkIWeI5SuUmuA+zy4yIjpBfX39U9tJJdKaFZJqQQnjrgNlS8tL5JOHDGlfXFAslktWjCuzCHEtsaN68CieAuZWrRHN'
        b'K5TZW9Z+aCvod4vpm6l1mzZgO73ffLrO1klZ3FZ5x9ZfJb9jG6aWNybqrJ2UkrbMxgSdtd2epLYkpUQ1TZWtLFfbqOs0FmpHzcy+kL5szdx+57gB66mNCYNWApXNgJVP'
        b'v7HPD0TzpET1hLwh7hJxpUIypFdQIFVUFxQMGRUUFFVKxNWKWlzzwk55+FIoIHuVmpJKM3wZvyMP0ikcX36tBz9NpyjK6qGpXXNFvdEwi0tZDxpZNk94yDHbmK7TNxvU'
        b't/rlERdwzUd/PZURpdnBcwddRiJ2EetlNlpMbJRFIhVtpdSYlbKec4tsg+dsEJfZ4+yRtYY9YqUv1P55zBhbwJiV8jIUxFd6ZUMNasf+RATgjZWi5UBhSSvYNhfUjlOJ'
        b'IGBmG4Qa0AHasNCWKrQb2w+xHdgKdwUidVa5z40FlCwatwatsSRGcahd2NxGsY8Ef687Fny6ZL3mqjLGoXl2rnJix8lbk7w3Z6jOvJ+1ACv1X0HWJgP1V3VC6okdJs+f'
        b'keFfWZQiQo3JaRlcYAR7WGj/VKmQ/aIMSYYzKsAhI0Z2JZU1YvmK8T9o3QxgdHM4jwI2jnvS29JVHirZgLU/ViYza5091r8Oo1buoJWjMqJ9cr+xm9T8mV5JCXuGuMWS'
        b'ReVyKWGK1OolukQrE6NLZBPPLcF/VJmeYmXKxcrk+O8qUzvPAxw2CmTT7sjE2JIKZwFf8+C3q2bH3OAqbGlLhy2FMnlkMAegs46sRQAdS0Iquv8/Um2oaBawf7DkfpX9'
        b'yryZCnviTnvgDriZEFAAbpjAkgB0ArvL64zLdrWlJrFAdK0DpuCYZCloX1IPTyKagg3QedjLKgWoG3bCzTTJX90cqDjM60L7d1YrS0sS6UlQC1TC7TJ5FF4V3B7Aqgbo'
        b'JLyA1DTFvRpHKp4FBLVL/rJaGWAQw2yjD6nWEAIWJl7NqsFTUOgm3b9iDp9KYgFzlcHrq5VT9sQrCJ/RxpVeMnQ+Au8iFe5iwQ0A9cK95TRBqJMrlcYCwSDn3dXKQu0s'
        b'egIbrOY3aQouiJ7EghvxXsT6dP/0RW5UFgvo15beW62sSsqjVd2maKZMSoYvX0ZWcwoeRcfo3vPMPag8LIXgyHdXz55skEhnTnBLBXa1vYoQIoZGdJqFgxhe0EF0gKYp'
        b'qfGiZmNJZOndWz27umstzSRDHIoO0DQsQM1i4TiFzqMOtJWmWB7mQ83HkhgOHFytiy5xoPcQNLtIJgsjU3RBNWstQGfQAdhC9/+10JcqxGK4pbgjU87RLqH7+6+Mpsdn'
        b'g/k2LLiXMPkqukr3N5zmTxWzQJymFspmz3mSTfefBzfioEwo9ECWIQt2AnR51Wq6/2GLAKoMC0216h2Zfc5Md7q/QyaOp70yY0MWYKHrLHSBCuejRrr/kF8QVckChcNu'
        b'r8tmWy6KpXeci5MapZGU6CpsgzdZ8BhAl9AVZ5riRk0wVYvFHKf3sUy3JnwxLWY5PAUbjVBPBCZZBS+xcErKhpdFNEEkK5TCVp4V7PimTBlka0GLbYUlqjcyDMVyy5vA'
        b'QrspA7jOldF7VX6eEbpIC+gAPMxCmygKdcBT9DQOaCdWV9S71JQFZsMrLHSI8oe9+XTbVGxhG2UGJkhDYVPJY6GbVCTcYMXo+bUs1GFUp0AXcXkzamGhHsoLnV9CJxtQ'
        b'7eknM5LKMdm1KhZSUi5JsJkmM0HXPWVydMmIIua7g4VaKH90FW5i8p3GcH+ZqQnmKeyzY3OpWKiRjTQsWo0bTClgjfawDag4F9RKrxCew/a4HzfVYb5eQftYqI8KlOUx'
        b'bRvNYIuRSS3civd9DKrZHlQcaprNePMLohVEx7kAHl/IqgXodLwhY4yb5s7F9h7OA7AdL68E79sEtdObyi9AB4kOckF4MG1156bAA/RM1XAn3CtDPajXjAVCUlnoDBWe'
        b'i84zzL+Imgxl6CLdhprhbhY6SYWZeQnNaEmyM8KpZdhgzbkfy5TUF3JGgyZHUatYoFZTMSSzD6xg0ZWfpkdT9dhU+3mvyexNjBndFC2cSG1kgSSNB8S6uTacrtzGiaUa'
        b'sZmqXO7JdNzlbnTlnjlTqK0sUFbre08222ajBV1pWhtHtWLjNI/8QGafmMelK7dGTKN2YmUAdh/KZld8uYqujM6Lp5TEKKd8KNNlfOtOVzbYzaD2scCy4cB7MuVS4wom'
        b'cxQnUyriFSe9VzHb72Y+c4Rgp1FqbEOCooEKe26yJ105ZWUmdQobisZ5oEKZaK5gnKpHNqXBtlBf+EGFbuXaJOYAw82lzmN9F8S8XqF0W2VFiwruKoXHZEaGWCuQGvWx'
        b'jak4MTxHi6oY7iwzkpqaYEXagNaxLahYdNSHJspEp0xRL7q0FIdSG3SDqLS/iz0jqXZ4E2BLwJ4Sj7g3mYV2Uu7oyiQhh17DypWvU/vYYJnG7fZS+5QvCunKxfq3KRUO'
        b'ylkG79XMjtUwrP6V9yZ1hA3i4thv1cym3mLIj/DeodRsIDAXvlljH1+n99w5xmA0RanGl10GI8dKcpJ5dqQEJQZjZxre/7lDpDl4MVuakqEQ4LIFPI0uwuZMfELejpqS'
        b'0wNRE069bQs5sCfIB7b60rtcpI+P4QEfYo4Upq118mTOEl9NNADmnqvZOGOojJ4VC2ibyZhgkhqUirZlJnOBPtrIckKHl8NLS5gI151sDHvh+UR0nRxyqDkA+8J2DnNQ'
        b'b/GBN/x9cebfiC6jE0E4XTIuZZvBdVWM52mfhoNPL148vAQ3xIAY/GuHlKyCXson8/BseS56IK7QePcqc6byOE5njPUPc4CgMC1XPgswR6ymPHQ5LJgMuQP7H3hOjHZE'
        b'Kzxodwq3habSx4vt5HZBKtwelAxPT5/iSwGBnGuKDqcrCAfRVU94NozkQHAnSJIvyoQbFeQEE2Dl5I8PumhrOo44zUHJ2HNdiLESstHW5BV0BgobTaTkCEfOb/AGpyio'
        b'hFnRqZCwMHiObO0gQBsUlfAGXEe3JMMudDEsjFAcAKhzeSnsgvW0nysjTjYsDKdr8BDIQ+2L4Vnn0dzpKloXFklolACug8eLp8EdCidiq/DagtQUsrYMRjym+qi9lh2N'
        b'bqTSy1udNz8skqyiA3jlSDAHmmjBpFbBG6lpmCQInnJDLf4UMJqLPeFS2CJk0fyA7TMEYZHYM5BwrMousYbdjMiOhqPesEiyxk68ZdhZCrcpmBijRuuzUDOAl/GBL50L'
        b'OC4U7JqFbtJb48F1XmGR2IrgPoBascGjfXPo9S8Tcf2xPHxRExZbawY8zQHGsWwznAEwPIHboiaHwYu0JAE6Yl8JL0cy0x2HZ+uwiz6fk5ZCTo5sdIOCneaGigzcOBFd'
        b'KZWlJSenk1tJY0d430ChX3pgFdwkFLEM4VEJPIYjzRFfX3jC1l8Id6Ij/tZwp60NOmIHj2NntMXaHGvPHriu8pfff//dJooD9PnfYk9RGADZLoAWjC9qdvKHZ+HBDFES'
        b'B3Dw0fXkarRLaD2mlIdlSREmUgUb5x0HKA+4z4k2mSqohvuwY1sHTJm2i5QQNgroDS8VLcRW0GY3QnWD8k/j0w0hDui6bIkCU1CAeDvXMrh+NFNuQFdlUIU0dQpD3Aiv'
        b'UgJ4Op5eYTB2BLtlpbXo4lJ0ngtIYuI2hUOvItgah7te2CnFLSZkzB4qFDWtYMbcB3fBQ0aoCdWbGsHtLMCeS82bBnfRG6uDGhxBpT5yw6UcPNt1is9Gh0fyDFvUJ4Nn'
        b'UTNuI7OtowQ4VWxknEEPrIc38Iw7I+RSdB7vDt6gnNAFdJbJALB8d8vQObPZch6giG1sxypxltZic7QrwGiaRN/EEAfhKCopZwIz3b6V6Bzm43l4SVFnTLawl/KxQJ2M'
        b'pnbloC4jP3jB1Bh7bPZEKnkV3MmY0xm4Bx1HvWvQDjMpzqTYplSUgyXjzPbgI0Ej6uVhFTyHIxLbnZoKjxbSbRHwGOyU1cADdfRc8CLlAk/CqwwdDkewWbYKNhsycttB'
        b'CWbBrYweXIF9sNMIttjRbWxLKjgH0GdadEhujtqxLa0sCgAB8GQyw/szokrYbGZYtwRHtlMuHJygwJZF6CStBdnwZrQRurxobFOwayLDvsuZ+MjbC7tjxulUlxW9AgVq'
        b'cJGh7fxna4PbFzNhuQF2VaHeKaxn6obWTWcsb1NNgmyW6TN9c4VHhByGam/GfNS7CGnGyTEynVn8VbgtG0sRHVzxTIxb4AnmhLZb7gab0SUctBVcMK2IA69QcF0p2ka3'
        b'LlsaA5uXoovGsAl72Y2TOaiRgh3wWraQnZHBcLID3iwyWjX5mUqmwd2MsLEpS2RLfZ6pHdyeyvDlOlLJcEqX+Exb0Tl4TmhKb9IzB7YawdOLDQ3QOSyaGCoxVcxM1YzU'
        b'VrJytHeEm7spt4xYevPp+Ii4WbYSp5pjdo126jFEh8zRHiPUaK5PC9qQCvSB+5h0FHZzUW9RujFDc4byQXvN6V2vRXsgkdsOdE1hLCWNRykfeAY1M5y+hjYtlgWITdFF'
        b'ORHDQcoTdbGZfB9eJ/k+Pi5eNMK6wELnqEh0vYAxtS50DTUZLUYnpdi+LnBoyQaibfAaYwBb4Bl4EVv33DGLgucMGUZeR9vzjIIV6IJBHQ+wfagJHMRsYb48wQgehL2k'
        b'hQJsXyoGs4E5VHZgk7kuQ5uwDbTUkjMG2aEQHqqlebyqDks8YSG6WGvGwy1NlHdapSKAdlze+Vgd2uH2Jfhc04LV5HQkPIF2oQ3YMe1B7Wj3LAp4LOTYTMExhg7SzXCL'
        b'N2rXA2AS2hYMggXotCKbDHQYbsJnzHZMtAc2vjDYTlzbiic5h//dWQA7sfO6hKtbcdcGA3y03YPUsLtsMXb4l6HKAO/lBrZp2rtsDEetsny4axyDsUfqYfS8azbxjyf0'
        b'xzM4FLbi8EmzsZMNDxrxVzxjozs2YLplA+qYY2QY/oyNqfh4NAPQt6quG6GWVBwNk9ID6djlj1rSU0Q5qDEz1zcwPQU1p6GWZGF+Es5EcpAGnZfNAjIbfD5CnXBzhvlk'
        b'2IdPP4TlpngbOLHKQQfdsvCh3QqsFhjTHHTFLKnPxWE9Fl30AB6wCbtEooV5aC85IuNEZ9t437xRTgtYtha7vjG7xVLoZCw3XI/mBQ+r71kZ6oN7x8kYNigwL0iInwMP'
        b'o4upgSK/FLK5Mxxg5gDP5bMr9dEOOsUyg6fQDhKiW4LoTEQfKVkhOLzvgkdT6QHwhIfhAZx+JgWkOMATmSIeMMLntgOojUuzdFkSnt4Y9j0z1VB4kx4aHUU7pf4p6aki'
        b'MjfOPmOg0hIeYEPNsrry3x2FHFkAzn6rJvBbZqZmWk81/77jwOq3b2xeMFu3QGExTJ3p+gUk9CsffPbgI6P5R9rfHyw2a3ZrjLWraX97XfNDwcKkSRa/b266CX8v/I1a'
        b's6D3o6t9h8Xtfz195uTZhQve/8dfYovFVRuch0//x1ZuWqj4fQff1Oxv0+bC/JVio4+zckpNJv54tu/GazPW+Pzj9/3rkxxWS0Sn1ezuv3+o+tV3bnHG08iVNp91Gt1T'
        b'Jc2ofKfx1EHHC+6iKu7y2etzZ1w8/1va+jOnFZu6f/N9lffBUy5nz3CA9MEEldTzizsWv7476dPU1G1Jhn471LzqusZ57t/z+xaWWn1ore7JYM/8yzo/q7PUya5l10++'
        b'2ej3qferbyhW2TYvZIVN/rx0/W/XWJdiXt3v+X1F7fElRd9eCJvzO4jf/511pe02s2JNv6DTIvxdk+UxmR9O/+tvZ60WLUjeb77aqHvNmrxZ81vfXeNob9Vy/pVD+u87'
        b'1i44vHBObtfl0v/Ibog7flsX+ckx06Y1By4fuOn8U74k6nTtp4taLQOSKsKvFDofCAv9zM7K/YB2SaT2jXVWuv7XGrUz5Ne+Sk48lvXrpPfL9rpv/eqWwZ3s1GNLT5Vp'
        b'k+54N799IsBlYt5SL4O3NF9uklw/+0bptGUh3eevGs24xPpojujH6xtvfyX/fOJRzY4y2bZvXhna/Wvgw6tb/8PwRndV9zuv/tYz125b0a8Rpy6WaU+G3N+eoi57vPGn'
        b'ilMej946HHNl7frK6C+2+3xeN70k87s13j+tc65qTug4Wv2XLZ3rjPIiXumdGMed0IE+Kq2KjTh+e8O1NK+ZJvu37zPOSb+9MUC58phvM/xbpWrKzWk/2L5ze8fnyVGm'
        b'XQFbPlxj6rC44lH6wKuiNxLa363yM/CZ39JY2vV34xu7b9//fO2qy8dXK+bFffRxS0jTGsvgL9YORtk8yGt7ZX/2d6cEZ7z7ij7dJp8879Mzs9O+425Y9+71IOH1v5f9'
        b'I3bKf3zDK/LbLtxUZtXGO3qr3aXkLWdVmcjk54tPyixje/ifyI99tefvcx/tv7f+9S136q97He7tundxxbrFR368nb26ruBg3G8p7kUJA92Sj3frJUZmdT+6anOa9WPr'
        b'qQ90sYcm3X96zs504WdfN6CPw35+x/VHffv3XvlcaEI/2EGbjKtQc0AGTqtdcLDaHoAPELAbu30cbJkO29BmG//A5AA/YSBuRk0A2As4s9HJhdOnPSFGvRYfHi6RJ4mw'
        b'/tnDHwr2FKEm5slQA2yw8g/E+XsTHhxtzePBbSwR6phA34OfUocOpQb4JmGrxg4Dz+wycbkdbHxCx8zjOBIpU5PT/dL18A8nHoelH2n5xJmOOEUW/kkBfnhMnNpuRdvZ'
        b'YM1Eq4ls1OmE1E+Ig5RZw8OpmTil3iXC8XYJNXVW1BM6xh1F9Wi9f6AQbcGhC/vN3Tx4ihWWgFro1RrjiNWImtMDktE2klWhBl44y9QcNTDM2IDOFKeSp4mpySTFwacR'
        b'zK9iFupcMIkZvRPVT/f3G92twUSWFQ7WB1GHC71sdBNPeDMVe0ccD0QpAfiYJ8qxRH1s1FCZL3R44bnD/+xFRrYveOGvfvSPefZhyTxrkEvF1TIxg5tY8ZI6+kmIMZd5'
        b'EhLPAg5eP4AElklkK0dn56RM09oJccnaXsnvt/bWuXmpxIfs1BbqEBW/ldM6u82UdEpqW3PfTqS1E921C3rg5dcar7Rvy9B5k4JDe6bOxkHp27bwvk2g1iZQLbtrE/bA'
        b'xV0V0lGqEqsWKStwJ4u2xLHewzzAdzkY1RGlCu+MbY3XOboo6zp8WqfrnFwPxnTEqIo6p6hD1KH9ToG40c3rMfC0mazk6gReqkWqOpUBU8QD00UngSp+b6wuLFoZr3K5'
        b'ww/WOburivcu0AVH4AqnO3yRzsVDJd9bpeH2WZ8z0XkK1Xld6RpJn/xclY4vUDl0ZN7nh2r5oZqI9/kTRomDwjGx4x1+wGhFYBiucNibSX5Xap1DCaltR9p9fpCWH6Th'
        b'vs+PHOn5MDBE49W9+FlvQu0fjH/b7k3Dvw8u6Fiwr+CBXxCusdmbOmwKnD0OpnWkDQPKbyqlm570iE35JVNPAOWcQj3w9FF7HUrVeGk9o5QJOlcPVfLetTqBp2rOITMN'
        b'a0AQplFoBZPuCsIeMHX3BZFaQaRG8b4gdjiZwlwbTqOAwB1LMb/NeJjFdbRs5Q0bAw+fVrORvT8GPIvJmMu+AWdNT5hqZAO+E7XWXq0JyjAVd9DOsUOhttF4n3Al++co'
        b'8zuMVTO19v46v6AOsyEHX509n64rGLCP6LPW2sfetY8YNsED4l1hbTJom9LvHaO1inkQEHfL+lb5K67agGysAbZtaSq7O9ZCojTCtoJ+38lam8lY9ipex6T7Tv5aJ3/1'
        b'jLtOYbqghFvFtye8UqMNyh+ZPF9rHzCsD1zclTN0zm5jFw9l0guXIX7sEFEFplmVp8wY+2eU7JGzGc0OAXByPujT4aPyVC0/FDTgGHrfMVrrGD3gGNOqp7Oy2RPdFt3P'
        b'D9To3bOK1rm4qRI7qloTdS6J+OLsenBux1y1nsZuwHlC6wydf8gPwN0mssNMyVUqVGKdp9/xlEMpaoVGrikZ8IxVGgz6+quTu02VJjonX3XIHacAnaunmrd37QNf0Vmj'
        b'E0aa6X3Oty20E1IGfFNVXJ2vSF2klqoNNTP7Qnvm3I9I0EYk3Cq6HTIQka71TT/E1bl5q727XF9CTLf1+8Vo3WJIq/EJY01un+i2mzYmdcA37RB3jGTANxqL2dVdFdG5'
        b'Qr3gjmvMkHfkUELK7envJf0lqX/m3Hcyh9lU9ALqB0D5LKSwirotpB48pwqf+4dr5gz4T8F65JBKdaQqpyqXDbn66CbE9pVc5t+SaCek3c7WTshUcVT5h4zVs7F66jz8'
        b'1UvueETowqL6eD2TbvG0YYmqeLVtV5rOS4R56RWtC4/us+1Ju2WnDU/uD0thGrFi4RmwZvHdVDP2TnkQEKJx00xVpwz6RWBrnto3TVM+4Bf3iMsOciHG15lJFMVDVbKv'
        b'YMQVDPBFjxMoLKBHiWzi/MY96TUeMh7vLl/2rPe/4rCNwSi0YJyPlvoC8lDqj055OiGZAGigwc/TWRTliI3+339ArOT5ArVRGFtIMSfQZnwEO52aHJBMHhI6cAAFO4MD'
        b'nrvNTtZK39tegi+7TEZusxPkFvgjdqvEZOx2O+e/7Xb7RiHrxyq8DMPxoS2LcEgmED+P96NBhMtrJYL0vAnhwYIaKV0IDXyO9LkfyXKBVCJXSKvJWJXlMjkZYpG4ukIg'
        b'LiqqUVTLBTK5WC6pklTLZYKlZeVFZQKxVIJpaqUSGa6UFD83nFgmUMgU4kpBcTktN7G0XCILFEytlNUIxJWVgtyErKmCknJJZbGMHkeyDAu5CI9C+lQ+NxSNUmF6FdVU'
        b'L5FIcS8Cc1RUlxfVFEvwuqTl1aWyf7G3qc9WsVxQhpdG8JUlNZWVNUsxJRlAUYS3Lon58yFEmIfFEmmBVFIikUqqiyQxI/MKfKcqSvDaS2WykbYVwhco/0iD5VFYmFFT'
        b'LSksFPhOk6xQlP4pMREB2eaz+abhmkpJuXyFuKzyxd4jsnrWObWmWl5Traiqkkhf7ItrF0mk4/chIwt5eedF4kox3kFBTa2kOoZmJyaoLhFjxsvElcU1z/cfWUwVs5Z4'
        b'SVF5FVYFvFPCqJd1LVJICYeWP1vNLHSkTKqofmlvAjiKoa94TEVRGe4mw78UVX+26qLKGplkdNkJ1cX/Hyx5UU1NhaR4ZM3P6Us+tge5pJreg6BUsgiPJv9/ey/VNfL/'
        b'wlaW1EhLsX+RVvw/uhuZoqqgSCopLpfLXraXXGI3gkSFXFZUJi0vwdsSBDFeV1BTXbn8f3RPI06gvJq2UuIoBCNbk1S/bFs0Vutf7GqapFIsk9Pk/39sanzGEDMWzsbH'
        b'ojF/V1sjk784wIhmSGRF0vJaQvJnnpvIWlK+6E9WTCKXXDyqXLNw5MJTVVb+iYaNTPpMHZ+f689V89/mu1SCoyg2uhgB9jK4Zw66VlSxiJngZf2JL8KbL6iQjBPV6IIw'
        b'CyrRNZlMUvmvSOU4wP8JE0fGIT1evtg/RNxURXWxpPrlEXNkWhwjXxKrn58Y9/lXY5QueT7uJhJpoyMlchn2VCU4iSHNLyOslWIBYJ8nfvm8WSPNkmpRhjTwz1b/3Nx/'
        b'WPfL4/+IIryQAzxH/Kf5AENbjqd+OWHytKkZf652BTXS8tLyaqJSf/QhmSNti2iFxAYsmCGVVBUv/VNbHz/yf0Ghme7/pjMpE+No81KXlyhZhK5hs36JT/gfWBgxA9rO'
        b'iJ97bl15uOVfG1u1uEryzNuN5MUC3wxc/VI9VUhr6bzoDxT5EulSSXUxMcsVSyVFFS+jlklqxTHjE2s8wLis/iUU86qrF8QIZlZXVNcsrX6WdRePPweIi4txxdJyeRlJ'
        b'0sulJEuVSMuLBOXF/yrDj8EHRXEVcZt4TXllL7z99DxhzMg5JwafC14WGZ7v/Ry+yQy8iG/KY97ZWBVB3iBapm8CCitvFVYy0KC/VnCBPhBUs+MKA2ITo4EihL53ugBq'
        b'YDPshTvhebglErXCC3AreTh4ErbQjwpZIeg0PA0moVNcqMqsYiCHx1bBY7CXBWBXOpgIJsKLqINBHk/jAWMwmzIQFBrbxCwE9FM1H7gnf/n0URRQEdqBWhRu5EdvDGzx'
        b'F6agrXALUvlnpAUyd539ecDNleuY6SA0oV99iofroRI1J6WnoSaoSRZBckMc90wV8YDrbA464oqOK7wAeS+kA15BzUEppE9QSnoq3AHPjz7bCkEtPH+ALtFPvvSWZo5/'
        b'7mUJDyTADjbUoG3wKP3Erzog/zncEDwQbVrLjs5fQz9ysw4zSUW70UEaIvQMHwS74CW6He61QRdQM7kf7YC6U0QsoI8us+CW1bBP4U7kwzcnoyejneg83kcGbEHbg5JQ'
        b'Cxu4WnKQEnXH0wwyT0brmH50HwJXayIgMc9VaLM/d1JkhsIb97Isg+3jeqGW7EwG0JWRTgEhvMaFe6fA9TTcCx1DZzPH991OQFu4m2cZulDIjYPrwmh8nOtKe/9A1IKn'
        b'DEzhwcvpqClAyANOqJMDD6Pr8IDChQzWBNvg0ZF+yeloi9iE9LKz4QTPgM30OGGZcDMj4NPw/B8EnLtIEUjGaUPbZsjo119yfMnTB4JDQztg7yxyvx+XZ2ahFg6YJdKD'
        b'u6ym0vdHAtBRPOtp2BcWSsBbewhIEnUrnOmmerTtBdnCLnQUC9dFSitvODqBDsFtrLBQLg3TKkMnyumGAngCbiTPz3HzORAMgtH2QlpbpsLz2c9pAzqOLhJ1MIVbGVZs'
        b'h5fI01s1uvCCSuD/3RCymJs6GpFdGDxXy0PH9QGVBuAZuA6zkjyiFcmwOW2BO3AzoIFvFbBpPv3wOMdmGaNHqKPsmR5JKSGPNq3VqBu1hoXVsnMVgEoF8HSuGTPXSWzR'
        b'p8PCkIY7DY9J5QB43iafBgvV+dWEhUnZJtMAlQngWbRuDk1hPB2dwP3PcdEpeBlQ+QBejIX1DNhtgxnaOBN2hYURhFoXqFiwnPEC52H3ArQL9oSFEU4eBpWFDJb2jJct'
        b'CADmMUBQOP+mjxuD5kmHHeYyCmShIyABJASPAORn+1gAARguBbWFxr6zeEDIZgzoVFLiyDPvw2jX2HNvuGtqBM2W0sVzxz8y108yy2dXsuEGZvNtbmgTuXnGBRxOHdxJ'
        b'wYPw6AosBRq3swOeLCQcg4fSGJYVV9GAEUd0vIJmGDoMDzIcQ3vRHlqPbbwo2mpS4YaXmKvMe2RsUwMCXZSyJ2A3RzMXnpQwKJsG2J5Fc3cpPMkwF65Hm2kj94PHc19q'
        b'5N5wNzbyumJaBmsC0dZEeGFMBGys7sT40W5YP3kcuajqD8YPN09ixKiJguumGo8Jyx/upd0rOg4Pw+sv9QrweCLxCp0ZtOYkwRtLVpA1MLDNsvlT6A0oYFNkarIoIxBt'
        b'CcDud7vv6LNDJ9jAgUez59AsSEX7rAjSULgadoiSOcBAjwW3JQfSSmAeaQr4oLVKL7gwYCpvBgOqhbu9po8KEW2EB7EU0SHUTtsbbMBq0TuiIBdqxukHWg/30xoiyydu'
        b'QJQq8ssgL8B6zjYrZUtSYQftBw0zYdt41Gs1GxKWEXilUxoHq8gBDsOa7Wgv3DbSsyBkHEJ2BB8rRFsZHO0V1LeQcRFwG448sDN5zAH5FXFhtzSNXlWIAm2kocKoBx4Z'
        b'hQsvX2BBa1k8Ooi6X4DTWglxjLjERlt90A46MMF2eMYcNY+hOuH6FRTsrIJdCiFt3OjGGFYENmE1xaPdzE8jT5BTCR9C4R5esg1k8IipcI84FZ6Ip6EjY7iR0Cga1eKe'
        b'Dvf6wyN6DPx0DHoqhQewjdIr6YT1Lqh5FM66Bp6icABsQFdoclvsz7b7Y7fYQOObR7HNZnATvVd4BaojnkNgn0sZBWH71GAZ0uDhDajJ1YhFXtu5AXJBrpMEGxqNDDwc'
        b'H499iXAmcSXwKlZkYn4sqJyKNeWKkZSHu5zAGsSqorvHuGHP3E6BIisgAiLYJaW17kAOeT84mG9YWFgJPdIYyCpqL4CnFNEELKWHF7AdFODJdzGe40ixHtpHoEPBbPJa'
        b'CKixiGDQjU16QtRuZopD/i54yVcPKyyVJ1xNY6/QAajMeQ62RMxjewZqyUWNybg+CDVlEQBTEoNeys6C54Jzc5ICrODx7OfiHzxlYp45z5dmvQ/syh/v/9AZM+IAHRlz'
        b'WmRLvwQbwDIvrJxnKwF5WGBkb54VlqlMcILX0D4K8ApYfsELaX87DXYsGT8g3D+XDIjDQweDFLqGDesYo1mLMHOeGVxKJGORB+FN1rhcAJ1fMpoMQFUWvaxXrY2BPVBH'
        b'c7IKKwMMjAGdCcFD8IzVWK6R9WKucQXtV8wh3brgfrhT9hyPCKIgCLPzJOoKFPliFfMbATTnEhY3BuQnEeWi4dPZSQEvMPPmSgvYApWmNHj5G0fyUniWv1lcYdonljmA'
        b'1lAp3IoznPEaeh67l1EVrfUciepWqKMO9objqH4EHgNUNg4oZjgroHVpu1UUaaKS0Sk6oJxB61CTIpxW4NXwBGqHWAXacCK5czwsT4KnPcOF5xblyBfBCxEU5jpvziK0'
        b'nlbC3CCcn5MxoQYwY86bRTfMRDez6HW4pTCrgBv5Qg6dXdTAQ25hkXVsb3gNUCkk71iPRpCOx3HmooZHAsPCeXQeJYHXsDGRaGHhKAgLX0Klw/2AigPwxEScGBNlj3HG'
        b'8bE3HGkAXu5GOpadi0AbhBQD3zuEc639uD0ESIoANQPnMlNmKOLppGaCCbYD1Iz52RyEtucijQnsCQ/JwoqPnfleRrA5ovycF2WFXepBQ7R32eiLVfVQFQi7eQRUvBms'
        b'Aqv04VXmNTa4A3XB7kjYwwqdCFi2OAmyQldpR4I65VGwm2DzCsEasCYfXsHSoxtO8VLIi7A4OSTvkRuMZP9wMzqL5bEbR4V2eJpLoLUAdqNTwSOYPaROwBFznL1Uo13E'
        b'XgLxGonzKy6ezdgKzifG2QrsW0Hz0DkR9aHepegijSu/lIj2U+GJaBPjTPajC+QltlGooDu6SnlXT6Rf+1BMxBd9uDffKCMdtYjyRy2gaVZSysykPIaj8AT2J+kieBRd'
        b'C8xIyyRvhSGNIdyELq8qb3zvI44sG4fvzZTV0fx3auYlmH/y0Vctn/R+9qprHX9icmd0hlPZgrIFvpuGnVWrct3c3C4c32b5MGnypMN3tyzZ9GD91lWajfXNmUnqhsa1'
        b'9Ua/GyzNqP307e+WffLUYsp9/cryJUuXLFny5aUfHt146x+3nlZUvXtsTemS30r+1ljOS5Pxudtcavd/c9ZZc+ja2k0hIu6393d+d/ZA06Om/sSMhL+Edc9M9frg4++c'
        b'aqdwP737dk7Kkl9Vg58sfqt8+XDW8etFX28qUN2Tr88z3Hc39trMoK/P/zTT0Xbbz/0XnbY0OJV9wn3NbUFE/mz/CbmnnNO+zZ3k7bbTrPLp2ldvuX7xur7J9XcjXrs6'
        b'59ph43Up+wPTvv9ly2Fnh3Mep1edF1zNvCF/83aB5z8lt4W/b9zk9Gbmk0C7v17x2VqlOZ8ZCUPLLfdPSa45/9T5xy8zuz4w3P13J2nz7evNkdVdiV6FEZs9opbd2tLj'
        b'Mc38ssT3ffuUrgSBar7s41vf3PYo9v9+c8RK9N7t0zHV75z8Rbo2/vsVb//d5K3fXX7t3DzF+mHrkkDd/snfzz/i7LLmscMGUeEnUt3Fe7XqzFNT/2n6t8jG7y2vxz8J'
        b'1QZoY7syzVfv+NpSK+ma1bjQa8hzxTv9HiX/HL57++9N34KaM05Hhgb/+nPTophT0U5e4nlRvgde/zSdqym6tnHHu/LQvqEzr19W7J/qGfrEPdOJU1u65+Oh2987rtne'
        b'sD6sNfbjiM+iN5z7cueb9+znTxGvsJg1uPzikqNvvp5Rmh5edn5+kefJDz8cWOPJjfq66lu/0gv/6P7BzTXvvfIHG1ZIn0yc8DCUn3j9yOotn3td+PrTyHreIclC1cyw'
        b'b1OXfBT6zwuygaGHx94SbQ/PWvKNZN/fBgMOb2mb7bU+eZf94wyrz35yePxF2+Pg9TUPv6t4Uj7h4b3Sw+0PH13bd3/5E9mCLxbwdif/0Hfvw5iCitZ5M5e3PvIrPddm'
        b'vurdrGkis0tNP6za6Hwt+HFW9dq1AWL5+S+/WRYSKI64Vhwud2lTBGXOnNbsfW3ak/c7bj+1Kp5Y4H7mrHjBhFdNs5PivlHsvLjwa9bgwrI9lp/HHxn4dWfAVyvsl3cE'
        b'DEhj7tSan93P457cXpPlGZAlcSo6lyyb1pc7tSlK6/Ox8NPvRHu/0O+d6Hc6p+HTVXraj/udftsS+6XpkltHGld8kJDH9nrTwPI/4i0/gsZNS/ebfle24ebOpFVODs1P'
        b'7wqyLD+e/nen3y/cfP1maNYnPya98Xb10+328M3vWq4m/PKWcfF8b/HBtr+9+ZlnHN9VtW/a5W8++3zoW4OrUXWfzHhl39bArlK7dbkL7T766PHba4KcNX9XPrxiHTwz'
        b'z+sb8+ht3/r/+t23u9SvD1Zn/PhO+Yq1nsG8WQ/Ydhuo+RF1UWXuP09HrwWdsX3U+erN/aE1v+qduaS/0sC1Y8LMOP7KLp/bpsu3RDxZ93Nc1tndbFet6/1rM3d27n/v'
        b'kbJtw/7P96T3/P7j/s0Lmp583PKa4d+Vf9O8F+X+K8+o+cPCi/uLX/n8w+n3fpgsMVte+0tUFjgY57dAaPaEvqVzLRKqRmCJ2IVjJy6B7eQ+jR28yEkSo3oaDpiDOuFx'
        b'f79Aoe1yGi9oMIcFj8JN8NgTGlh+qHbOCFbQB3YAQKCCOPozpNNw2GwZnWC9E05iaNzj+VU0UBCdxl67gSAfcajeOIZ+XJ5a9YR8bghdxtNcxfGmE+6iwZnjkJlw13x6'
        b'Bzjh3xv7AgjSaiKu7WWjToLkfjJyADmK9owBOGFz7iiGcyG84E3jLP1mGvhnpAegG4EpBPSoDy+zltrnMuDNdXAPPoDg3DxIFIAjKeAtZQXiLe6noZ8SdAXH/JbUMWQo'
        b'6nU1C2aXeiElDe60cZg2msadqWSyOLQJ7WBG3o4D/00GhzmTT14sO8UKg1vhdQbfeRDVo8v+6CI89sL3GZahbmZfXRU4ivbSSMzTtSI/eIzPfJVkEoedlS10/7+Kpfz3'
        b'cDwku/zj/W/BOGRP/Ytfn6iSTwgPXjH+B425/EqPwVwW6gNr+z1T2qYMWHk2xuts7Bpn6KztGxN0Ts6NaToH58YUna1dY6LOnv8DiGOb5FCtnEErZ2WxKuGuld+gk4+a'
        b'M+Akao3X2TntWdm2sn11K0fn6Kaa2uHfqjdo56Sz5o8h1cI0ee9bxei8/Y4vPrRYY6URD3hHt2W2Tm1VKCUP7Pgqzo7Vg06CQX6gWqFZqA2Kv8tP0PHdD6Z3pKu97vKD'
        b'HwRE64LCdUKRzjdA5+OPx9EFBOtEIbrAUHL1D9L5BeoCAh85mbo5KrnDLsDXb6/xoLP7oEtgf9CM23baoKwBl+x++2ydg4vKc6+zThSq5CorBuz9RiucXFReHZN00xLf'
        b'8H/F/3bRwLQcLX+KMkHlp+WL8JrmDARNeRAUjiuEA/wAQiTSOuBZg/AwZZ1muKLfPUXrkPLQO0Tj1cfqY2v8+iS3pl4uu+1xuWbAO4PA5sQaltpo0JNsMVtTp14x4Bnz'
        b'SI9DL9iQwMcytE6huvAJeI7AAX4IAWlWa53DdRExuCZogB86CtuMnKhM6HcPHeCH0TWdC8Z1IbvpdB5m2QocdXyhOnyYjUsP+J6Y6Taauj4LjeOA96RhLq4c5gFnD1X8'
        b'sB4p6wNnL1XxsAEpGwJnLNhhI1I2Bc5+eBAzUjYHzv7q+GELUrYEzr5q62ErUrYGziJ18bANKdsy49iRsj3Tx4GUHZkxnUiZD5y9VfJhZ1J2YdbgSsoC4Byolg+7kbI7'
        b'08eDlD2ZshcpewMvH52PUOcX8Ngf/1ZyhgMJ5yw6ohmE5l0n0aA/A7wTaxbfirhtcTv01kRtZMaAfybBunak6Ty9OxIe+Adp9E9MHq3xUiboArDcTqT1TdcGTFFylHO1'
        b'9r40QFedovWJuuMT2zf1js+0WxZal+lKNuacm7dKop7eLwjWpPYLpii5OldPVW7HivuuIVrXkLuuYQ/cvdTUIR/ldAIJLlIVq4xwHxdXJZsMOr1j8X2XYK1L8F2XULzU'
        b'6T2Lb02/E5moG6UZZgM83Fiv95/1GohMHAVJJvR59KTcogZ8p3WYKHkq7qAwXJPfN3NAOB0vf3aHqS4wTDNVI1Yvxj8XaO39H0ROZNCI9yOTtZHJtz0HIjMfsSmHcKW1'
        b'skLr4KeeruML+t1CtFiJ7J2V1Vp70X37cK19uCbvnn3MmJV4qa3vOInwdu+7BmldgzR6d12jHwgDzzqdcNLkDggnqHiDHt6qJYcnatzueIQN+sUMA2pSBqXLmoUnmzSb'
        b'QDb95xDIptcc6hEPBIZobPuoHofuhbrgCE2NNnjGrRXa4JzBwAl93rcsLgtv5Q0EpmAjiXJXcVWVWkHYI+P/lGYgMB5TRBOKqjuCcEzhE4UnjE6ndJn5eBXRs2jg6Gwa'
        b'OIqv2A7cVYFafojGXcuP0FRq+dPv81O0/JTbEe/zaYcRqHUIfsB3OZjckdzvHXfLa4CfpKQeevmqLc7anbDTWHQ7Hi7Q+QrP6p3Q01DdhoPYB7hd8unx6XPrJV5Acbl6'
        b'wDv9OVNP2DuZQMMTVKI72LmFRuFSwB1+EO1GYrUOsQ/s+WRiXywYXHzoEojXGhyji512K7F/UhreRHA62YRrBtmEQwb1wM17R8pDBxfiide2rVXJ7tr5a6wvOfc49ynu'
        b'hiTctn7P+S/O/bPm3k2e99BegLds43bf2kdrjY3yrrVoEDtqGwflPK2N76C1t0qhXqj1mXTXOlZnzXyayOuutS/WjtYEnYdXa5rOzWtHygMngcrljlPwHx0sadA6BWss'
        b'tU7hJDS4qfLu2AkJhn5KxxR12F2nIE38pZSelD5Zb+Yt8Z3wRJ2nLw1Ilh3OvO85Ues5sS/+lseA54z7nmlaz7TbuQOe2cqEQS8/dciJIoJh73Mb8Jr0GJg6T1JRwxyO'
        b'WxqlC43CCuHbl3DL7Zb4Fa/LaWov7FQMQUikRtxHaQyJanjdom6x+mjl4LKFWDmwz/P0VUd2TdZNnq6K7xfG3PGcqPMSqvMPL8QeVhWvdujKfOyMZ8GOCXc0ueMRqYuM'
        b'VnFUC7AaEpi68wA/SBOu5Ue9TwSHfcUdB38CPZ+vtfe7bx+itQ/ReN6zj3r4IoeGp/LoWPoongfMbQbN3VURahetR/Rd8wk6c9s9Jm0mSsldc8+HVg6Dtt79PkkDtsn9'
        b'5skPrBwa0395EgV8Qx8DFt70oF+UNjpJ5zvllo/WN/kHNjUhlbauNNq68JVNej2l0b8DNiYzozjvRznlW+ox0GLzIQ55lvu/CSl+aXpCcMuFL0tGpJPAs+9P0UnIW6T/'
        b'ZMBgjHN5FGX5M8CXYXL5d4HG+3gB4JRRFPu558ijuOIfyP72AAn5ziiYyyqm5rKXsww2CtlD5vQDbBrcK02QSmukT12ZR9r0MqUjWF1JsUBcLZCQ9sAMIWdIv6CAYAAK'
        b'CoYMCwqYT4TisnFBQZ1CXDnSoldQUFxTVFBAM5pBc9NcmEK48IdpP8dLlXFx00bwqXEI3Z2+jShEuwqMTNEluZEBTt0zFs8TSUe+pxeEDvK44eiakJpR7ii248pq8RCC'
        b'VyslbcmZKNh6498q0++srll3btfqgjdv7Dk6bNW33d08qpGT9+l6v9cMEjf2PXnzxG9JC6flxn0+/NpPncsvvlHj0DBxh8fELYdjhiauDDH2Don64hvnd9eb/Vayoefq'
        b'05/9joSe/nGxNKs7+7T9PdVv+b/YqB8GZM367vutPWv/cf5Yytbwf/R8/Pk696+/mlhz+CI/RrzxQGn1k6fLrgQnpBQHOGh3fy/sM7cQz7VcJEK5Zx0+Tbom9WxzP9bm'
        b'VtLm8WW2wDbbfbc28bs3QM/6qZ+ab27ysPfKD5nBf4NTZ5n7avnb5qUhifveYNVZpM5+3TA/Gzne61mXXil2mqh7zeWnD/5i9n1y9K2fP3HblvVG3bxHxa9s8iyOWb3+'
        b'3YO2J2/P42V8bbq386jx4epXWubc+ap8WcWdTnfvT49k7pju1uAtdQ9KyeeXiq4PvCP8bUrIzcwNh7SLoi9dCH5j22+zvnqUmC/5cO2lHad/uhOJVq/NWdsaNBgbdeYG'
        b'sImte+PVASGHPhIFwouwntzDvQB3UTjGALQtEh1hDh77yWus9McQRz6FOHn2yMcQ4QHDJ/TDmAbYDjuM/MjB5yi8QQ5nY19NdIW9HHS2Ioc+woWg67BbhlpM4emkDNHY'
        b'4ygL1Eqe8B9EV0ffCdP/l5f/w++ExdF/9X/4Y04k2HQqa8TFBQUrxkr0WeQp1t5/4rNIADCxGeboGdgNmlm2hjYvVbptWdUhU4WqxIfIayDZe9f2eGqkfW49ir7snmW9'
        b'ga/E37ZESXdC0z60d1SGKsUdEZ0GqhStfaDGTmsf3T8pQ2uX0Z+T1z8zX5sz647drA9tBSrL9up+c0+cX9njuG8ILK1bp7bZNE77icMz8P3JnGPgPmysLzDUGZu12g6z'
        b'ScmBryxhSt5CdSRTCovs4zGluOm38unSA5qCS0o0BV2iKegSTUGXaApSwiHYxBzT6DFlR2dMNVL28cN0I+XwKEw5Up5KxVOYmv6lz1AbMGWaeqQcENrHu5Wvs7BTlqgj'
        b'X1Z8bIY79uvzcX5uaY9rmP8/MuK541qXn81nsAwinwByHc7iAEPzQQPzVpkyorXiroH7z6w8joHjz4Bcf2ADQw9yMR/mkN/D1fq4/IRFGYTuW44DkUEo3fiIVPwynGlK'
        b'GSRTg5auR4z7RTMGBIkDlkn9xklMeNoy1T7eELxqaBXvzGbCk/UQCzvQ/77g9FKltX5JwHoWtJKJux5TVWLsstiRiCWkKHMSsMx/JJd/N2Ad4oWAHqNJ7PIbd++yZKtx'
        b'ze1pXpKWWMMNcfbxN6dEDHXkJcdtnfXYsJkKWfDmEaslH05eph8kPMfhHF+eO6lkzYXSoIXX3/lcp40reJp1Vn77g39WPbytav9pUCs/J/PacUnh/N0uzpe/7OSxp7cK'
        b'EraxvP526t2+uLrXTJba+03qlx/tfWRdvGP3468MH4idjr6zVahH30maC/egTvpzzJnk0So8BLem6gEjeI6F1LBv5hMBcWmn4FXymHkPupYpQj2kb6aIhd3QNTbu38qm'
        b'B4JnsXPqhs3k+TN5kgpb4PZYQz1gasl24aIrTwjX66ahXfT7uqg3SA+Q93UrvOg7RWmo1T915DvPsJtDnu8aCVmo1REdoNvRgZnlo9+Bhjcdxz4EjbaI6bd54dHEOf4p'
        b'XEClwjZ0BSDlCkOh15+7xv/r93T+Ew31GnWrf3Sqf+Jiy6vL5YyLZUq0i03El9/qwQ+OgGulM7G+b+KiNXHZt2zAxLd+ho5j2JC2Lq3fwu1I9F1OwEcc1w84Jj/zsvS4'
        b'oT8Dcn1CX4eLTYGxdX3muLfT3IfYlZLqIQ55DWqIK1fUVkqGOATvh1PL8iJ8Ja+yDLFlcukQd9FyuUQ2xCFo6CF2ebV8iEt/h3SIKxVXl2Lq8upahXyIXVQmHWLXSIuH'
        b'eCXllXIJ/lElrh1iryivHeKKZUXl5UPsMsky3AUPz5YpqoZ4shryttKQYbmsvFomJy9DDPFqFYsqy4uG9MRFRZJauWzImJ49lAFfDpkweWi5rCY6MjhkyEhWVl4iL6BT'
        b'vCETRXVRmbgcp30FkmVFQwYFBTKcBtbipI6nqFbIJMXPXBJ9N67wP/kTCBhfkjN6IZ+Sk2Xiy+/4D3sSM4payyau5PnrD/T133EsxI2+YsKb6gxecTaa6st+qj/6oeQh'
        b'84KCkfKIL3vqWPL8N+8F1TVyAWmTFGcI9aXk4SbJYsWVldgJ02ufSqoMMYOlchnBjg7xKmuKxJWYtzmKanl5lYTOZaXyUeV4lvY+1Z/E5MmTpSsAk5jLiGsdZlMU9YjF'
        b'oTjDxsDIpF7vMadAj7IejjcDBhb39Z20+k7KlLv6Pv0Bk1/xRr7agBSdvvmgoW2/XdiAYXg/J3wQmLfavw8c6an+Fw2mH/Q='
    ))))
