
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
IBAN module of the Python Fintech package.

This module defines functions to check IBANs and BICs and querying bank data
from the SCL directory, published by the German Central Bank.
"""

__all__ = ['check_iban', 'create_iban', 'check_bic', 'get_bic', 'parse_iban', 'get_bankname', 'get_routing', 'load_bankcodes', 'load_scl_data']

def check_iban(iban, bic=None, country=None, sepa=False):
    """
    Checks an IBAN for validity.

    :param iban: The IBAN to be checked.
    :param bic: If given, IBAN and BIC are checked in the
        context of each other.
    :param country: If given, the IBAN is checked in the
        context of this country. Must be an ISO-3166 ALPHA 2
        code.
    :param sepa: If *sepa* evaluates to ``True``, the IBAN is
        checked to be valid in the Single Euro Payments Area.
    :returns: ``True`` on validity, ``False`` otherwise.
    """
    ...


def create_iban(bankcode, account, bic=False):
    """
    Creates an IBAN from a German bank code and account number.

    The *kontocheck* package is required to perform this function.
    Otherwise a *RuntimeError* is raised.

    Deprecated, use function create_iban() of the kontocheck library.
    Will be removed in version 8.

    :param bankcode: The German bank code.
    :param account: The account number.
    :param bic: Flag if the corresponding BIC should be returned as well.
    :returns: Either the IBAN or a 2-tuple in the form of (IBAN, BIC).
    """
    ...


def check_bic(bic, country=None, scl=False):
    """
    Checks a BIC for validity.

    :param bic: The BIC to be checked.
    :param country: If given, the BIC is checked in the
        context of this country. Must be an ISO-3166 ALPHA 2
        code.
    :param scl: If set to ``True``, the BIC is checked for occurrence
        in the SEPA Clearing Directory, published by the German Central
        Bank. If set to a value of *SCT*, *SDD*, *COR1*, or *B2B*, *SCC*,
        the BIC is also checked to be valid for this payment order type.
        Up to v7.8.x the *kontocheck* package was required to use this
        option.
    :returns: ``True`` on validity, ``False`` otherwise.
    """
    ...


def get_bic(iban):
    """
    Returns the corresponding BIC for the given IBAN. The following
    countries are supported: DE, AT, CH.

    Up to v7.8.x the *kontocheck* package was required to use this
    function.
    """
    ...


def parse_iban(iban):
    """
    Splits a given IBAN into its fragments.

    Returns a 4-tuple in the form of
    (COUNTRY, CHECKSUM, BANK_CODE, ACCOUNT_NUMBER)
    """
    ...


def get_bankname(iban_or_bic):
    """
    Returns the bank name of a given European BIC or IBAN. In case of
    an IBAN the following countries are supported: DE, AT, CH.

    Up to v7.8.x the *kontocheck* package was required to use this
    function.
    """
    ...


def get_routing(iban_or_bic):
    """
    Returns a dictionary with the SEPA routing information for the given
    European BIC or IBAN from the SCL Directory. In case of an IBAN the
    following countries are supported: DE, AT, CH.

    Available keys:

    - SCT: SEPA Credit Transfer
    - SDD: SEPA Direct Debit (COR)
    - COR1: SEPA Direct Debit (COR1, *deprecated*)
    - B2B: SEPA Direct Debit (B2B)
    - SCC: SEPA Card Clearing
    - NAME: Bank name
    """
    ...


def load_bankcodes(path, clear=False):
    """
    Loads mappings from domestic bankcodes to BICs from the file specified
    by *path*. If *clear* evaluates to ``True``, the initial loaded mapping
    table will be purged.
    """
    ...


def load_scl_data(path, clear=False):
    """
    Loads the SCL Directory from the file specified by *path*.
    If *clear* evaluates to ``True``, the initial loaded SCL Directory
    will be purged.
    """
    ...



from typing import TYPE_CHECKING
if not TYPE_CHECKING:
    import marshal, zlib, base64
    exec(marshal.loads(zlib.decompress(base64.b64decode(
        b'eJzNvQdAlFfWN/5MpQy9Vx2KytCLYi/0DopYo+IAA44iZYbBEjVigRGkSxMRsIEiSlMxtuTeZDd1XxCzImuyZpPt2QQNWROzSb5z7zODgG7J+73v//vPZoc5z73Pveee'
        b'e885v3PufR4/YyZ8eJq/X2+FrzomjVnPZDDrOWmcQ8x6roy3VY954ZPG7eCwvxR6aTwuIxN0aEryGaXeK1y4Ikzja+sc4ACtIxu/h8PsEuhtkQif9etHBQfFi7dnp6ky'
        b'ZeLsdHHeFpl4+a68LdlZ4nB5Vp4sdYs4R5q6TZoh89bXT9oiV2rrpsnS5VkypThdlZWaJ8/OUorzssWpW2Sp28SkSaVYmpUmDo4KYX/kqmSKXfKsDHGKNGubOE2aJ9VP'
        b'V2Rvp92tDIkVp8kVstS8bMUuT3GOKiVTrtwiSxOn7KLlETLFdmmWOESWlaeQZoqDoQVv/dRpE4QxHf4vIvK7B19FTBGniFvEK+IXCYqERTpFukV6RfpFoiKDIsMioyLj'
        b'IpMi0yKzIvMiiyLLIqsi6yKbItsiuyL7Iocix6JpdYzaUW2rNlPrqnXUhmq+2litrzZXG6j11NZqRs1Tm6jt1BZqgdpIbaMWqe3VVmqh2lLNVXPUDuppatP06TBrunun'
        b'c5kjjtoZ2SvWY7jMnulaGn6Ltb85zL7p+8QrGZeXXN3B7OStY3Zw9DIk3PjUibNvCv83JwPm0wWzi5EI4zN14bdrGI/hMxVbOcxmgzarhYxqJlzEJ3EROohL8JGE2BVY'
        b'jUsTJOjcTFwatWq5l5CZFcbHd/BJTipnQgdm2g72w1eNaRF0QkfPh5ELQTK6IA99GL8ByMgIZGSiNgWZmaeb0dHDajvCHx89l46eM2H03Anj5OzjakY/5er46NOnjl70'
        b'wuh72NF/GasTyOfZMIx4c2yezIWhF83NeeHFDPm1OXbVLjv24qtcvfQxRgzXNsd+n5HKXuzZzQ+V80wYZtnmzK+TrJjzTKY+XO6wtuGPmTHLRs2/W/eQe9XPYOZ3nEyi'
        b'ktv9GzhdOozY1/ZLg6/8WxPeYOhlU9+vjY8Zc9xGmWaXP9s8dSpnRhiVNxRY++ITMAslPivc3HCxT6QXLkbnk9yi43C5p3eUV3Qch8kyRvX4mt5iHbxfZQW3OKNe25go'
        b'zyiYwFY+zCwHNTrgwyoxmdWDVrhJia/uUOTlqpSoBKmRGq6+LjLbwAuQoosSgcoeqs3AnW6aWvjKCpWCy+ihO1wXXIuLaDluC0QV2gpnUb8ql8Po4cPcWRl5KkcoRydR'
        b'm7YBf3xdhbsZKD/C9UDF+KDKGmrszorTlK/ZpArgQ/tXuVYOlioHcnfBa+6aQlQVia/gLnJ3JdcnAfdJfFRkFn23oStKA1h8uF48jUG1+BqXDt0c9+HjSoUACkpg9RYw'
        b'MMCCnSpL0mobqkWlSoUOlJWimjkMKg4NoiVyVJsP/ZFxVaAr7gw6io5voM1l6OBDSlQGSwa34tPoPIOa4lENHUAUbkNVUMaFslORuISM+QK+prIhXR3F5bhLmUvYKEdn'
        b'0VXoC5/HtbRwBcxmlRJ3C6GwBvWiYgZVoGO4jY7LzmmaUkVuq8RHtzKoBJfn0Os+hqhEaUhuacaHohjUsMKAsr4Hd+1U4l7CYJ0f7oemgnEBLVEkoBYlOkoGdQL148MM'
        b'Oh4cpLIAOgLdAOZEhPGWrBXQFirzpgUW6GK6cgf4FVyL2oIZVLYevU4Ltm7BR5XGpKmWRaibQfXooBPtJMwJV+FeQ9J95/TpDGpGl7CaSg51our5IjoRHfjKKnLPdaRm'
        b'5y4WVaISmDyOLur0ZtClFCW9BR+XBSlxD5nUKlS/iEHl+AhuogwYueEa3KsirJ3aMJ9Bx1ahInrPGhDrHRHuIv1cxk0zYBbw64YsB0UzcaNyBxlmVR6qIVNQj8/Q5kLx'
        b'oVVKfI2w3bBMwgA7patoAbq4FNcojemcBqA+kNnGCDppsDAaYCC9uqToDCoxZlAjLkBn6YBWG3pCCWGhDV3aDSzs3MRy0Iya0GXcm0eKGsLQDRjSbl+NeOLxQdxrQGa0'
        b'bSG6DQvLG8RDFhYC/TwPRUQO7StAc2BhqVEhy8ZlXAjj6MXdhPfTqMcW1j6wTCcDX0uGEfbqkRsv4UsmDGqN8GfX42XUh65BESumEnSCQacWgEAJ9wt8AqCEiLYrCLUx'
        b'6LTdq2xfh3D1bqjDLrrDqJDI6QrqpIKaIc2AeSc9dYEgGqA5Nye2q9O4lgcM9pKyC+iqJxHUOXyJFe9NcQYpIyrYaZ8GI4uL0eimOy6DaaSsp6I6EIIbq9DL1uNmkS65'
        b'fhWdQvUMOgtiP8eul5Zt+IYI95DWrqBWEPwpfGcOK4pCCSoS5ZPhdqJTfLLG29JpyTR73CbCV4n4ulcCc03oCK5m1eI1VAglZLi97oEwebjLgRbE4mPzoUBAu2lwBbHu'
        b'e43t5eBGnjKP8KbG7biXQYXogJLO4R6YwdsiJenlMmrHMJ560KkuduoLcTUqE+mTjq6jcxkMOheBmljD14SKrVFJIK7Ax/E5EPZRAcPDpzgJuGmryo6IfbsJKsnHx0xR'
        b'ASpFxQKGv4UDPztxH7XumfgoLBVSAZX64wod3MC2oYdKudZLcLmEx07DCXwjFJfAlGcz+CaTjQ7C8iLoYCMvPwZ4TmGE+GIKPoUvqojSC3FZRAxwm8Y4K9N8reiiyUN1'
        b'btqh92+HMeknqyTski9FTbgaq1FHIDovkMahUnxmawg6vT4WVccxs5UCVIMLwQlQAV6IS1NS7TiCr6HXQWUDUD1FHyKnPG0jl0D1j9Gfs1EHruFvRrWMAy7l6wVqzEYt'
        b'OrBUifs4VEtLFWC3ROi2yp0daAcRN7kbXYWJgJYi0SVNQ4a4nHFAt/g8I3SQbanBEfdrvMpGfAxUC6xWg2oWWTbobKKWoc4JDF2EdhzRSWCoii+01KHNLIclVQSml0tB'
        b'VC0+BHwsWk7FA6rXjrpwdSS6CNIZb8efsMbHJxWMgxcP9+MyQ7qKcB0s+jalgiyjIlTLZdAh0IHjbEu3QPJl4zKigkY3t4rEuMR8AWpfbc5Ei3VE63AVK+jadHxM6xZv'
        b'gv9QL0JlKh+Gzt+V6BdFDWarlPzZD0v0AvDGeCkE4Mkv08k3QuWGGj/qh6vAsAZspm2hRj2v8bGV8lJYlsAiHIclgErWxzGRuB8dWisEPTqDqiln2/GV3WD0CSdl6KQP'
        b'uLxAdFPlAnS4EW6bKCkycfxExg4ft8e9PNyFrwSzs3YFF+ECpT4Rd70n6mJQjRTXq+YShs7rojMTpr906vS1x5HmL8YJU+KYXHR590pddJ23ljV/5WCDlaiYCL8ZPDTY'
        b'4ROoD2wFAWUglQJrwtyl8WnkoSpYxTWoMMkmHbTuOOOHmwWoDFT6Bp1MP1DKc1qUAVbzDoEZt2LpOsU3URu+PWl9scv0Al2mh2CZVvPwzVfRZaq//ujiZqURGe9xfDIW'
        b'luk8gBZupJ1LSsHL1AZY5LuQ1Y6L+DrO6CqV27a14B412AbVERveJMRHVF5QFID69z1vRys1lcdE7WFmvyoAn1jK0CWxlheoxUJ8O7DrDrhR5UeXcBIgJ605GGcpE6aj'
        b'gzY8my59xh+XC1CLC25nDVQXKozUwKdMYj2Lw1ewgmrEN4CjSQqtnUpoxiMehtjJ110Klos6o3JQ4BvjWOtEDOAjXAogzZ8U9mO1xQusQasXKWNgSs9Q9Wa8wNAq0U18'
        b'QWP08ek50CRZ/g24IAzASO5C1omVo+NuGvSWD7Aa0Funs8qTLpeodG1PF0hP4Ep3kbWCCsUusAxOgbrG4Vs6/qjEngogCLcmaeBevIJ4r0p8nM5MjieYh0nWFRi7hTq2'
        b'4oPr3QJZWSpRsy4+ugudYbkiRqJIixFT7EEEtoGs6pfp6Gvb6nhB84+9oh19rUAJZvQ4O/oDG0BdqQNvAgfRCovPIIKWzN+DyjWgUoIuEZ5LwSvRSTsUjFrGF7fGJXCd'
        b't4aEiMETElOVgE/qeOOCELqUcLWnswa2+aFmmPsoR5bdIzA7l5/bl0lso6vOAJPo8L3RDcFWHXZKZnBRj3KHgM7+UdzBoNIAVEUNOj7sT5iijV2Y6mG8GIdZPFhpNTxW'
        b'hMdDhFq4aJEMcwdr4BpVOHQYHV451UjNJsrCz8BljD2+ysPdrugOtQDhfFQIzXAoIj+DmmDlIDW+wxqxI1HzNLgTEAPAs+MgmuusVb29CwzGZG2EvvzBsU1Sx1wBgIyK'
        b'JBZjNHLxSaUx6eoM7lxGHGEDuqiaQRAzKmEmWi7yi/U/EWmMA48H+LDBkWqPGz4I6qKFvAcIHG4E132djnwP7gvUMnV5ihqijnzQw9N8HdRnxY6uG1dYayGyD9hAdNIa'
        b't6rmkKKLBtYvDg6W9SlNk3zUYxAXFIo6ZzIKXKMLojiYQxvNBOvXpwXXoBWgVOW+01jb3ZuMTwPQpJigZS/xCbXoOsQSRADrQUxNLzjOELEAsAczG7UIUPOGAKqFmSbR'
        b'4APItJ+V4nYYPWoUUfNvnrh18joEY4tu4zvjUqAuMwA3ClDV1uUaxUHF8VrAb6IEY7sWN9DGDDNBaONmiDZ3QQIgXytTHgjAcOsczgqBzry1Qjq+NICbPdoQAXxRFwl7'
        b'ivA51jdVAzvFMdSxQSOTtI4CsTgmEZV6vKLjhO4AkrahgV8DsNzLQumzhjRYxMX4LAuijkMg1jTFr5OmBFbUpwegK+Dn8FmoTga6MsMO9xqRhi4vQNcgHkCHcT+rLN2o'
        b'J3WqsvhTWQkEoCvdZO11osMs9jnvsAn3si6lBzWEA0oGyHNS5QplDoSNSX5Ogw1exTUO6ABoLlfGqkEL7l6Ge3NJIydmkWxAOT4uZPFTz4Ilk4z/cz1A59FF6KOIh193'
        b'hzVDG7rilg7tCKnZO0P0s4IYB8IMhFyViVNHxU1kdgvt8TXQflDy83RE+s6oezxyw+eCyZo8iFuozdu1w1sbuE3bDAHGSnSN7RcCN3xYG7jF5EOIYwdF5JaFUhdt2Aau'
        b'A+TssYGVcpExLPUXTNIlImV0GMTcBWJW4G46WRwQ8XVtjJcWSExbjSfbc/kmQCS9KqpBKRsZVAXr4ByLMupRDcwaa0MuaLuACJMIT28HNSJ9vriOjjoNjGEttEMG0ArW'
        b'4yaDqvGBRGrZvDkw4S/AlRxUO1trCqge+eHjAnRyVh67Lq5CVAks4ytUk1QgkgYVLqftueG24BeWBbDdNVuL/dj21ghQRQDYHyIB4xCwjb2GZIVcckdnYMmg+iWs27oe'
        b'HjzZa4GrbcA9E/zW8lid+bh7ARu2l6QDb9qYuB3Xwlyh1tUqXyizAoRVM9liEJB3UzRJdKBJdwSoPAu1Uc6icM8iaI8IrtsOnySaVLWUgqpY3A4LeWJz3NQYXKQxZCbA'
        b'XH+gKVLP4aDGZfrxKoBidEarDOaNB+b4VA7YsxjUTZ2hu5PzCzEJa8rzcBPjIOHha4AAjrG2tQ4m7fB4FJ+LSkmC4mIEtT2oyRnvfxHuabCeAQSnLKZQCXLQTTGbQkJ9'
        b'7hD5k9nszCYpkhNWqJadgGYwch0vLmXi7vCNPbCUr/OgRhX4YmKtcWkSrtLmEGLWAy8ec+h61bE3eCliJO2g63JwVXf4RrhURtmJQM2JIl0hDSvK0WUGnbEF/SVCQh3u'
        b'hi9aLzIedHQeMHOJhy+h2xa0lVdxcbAma+GOLzDoLITYh+ig5Ea6U/EbTOztiYvKU2cuPgTVqds4iepMRXnUBykJRq9GpUJ2Olt5nPHkR/s2stqqQBWIaVi5a4Y2vVCQ'
        b'C4ZzHi7QSEgfXxXlk8bO+4GZqQmGgI4aw3bcuWASQJ2wLLdzWGN4B1WnqkiKf2uotSifNN8h0GFQnT8qoovcA19ZOmVRhuFyzaJEvevBZB/aik+vZxTbIMryyKQs5UD0'
        b'fl6TqME30kCZfVQU6G4CH1Py0hSAYC26YqaJsC5C0DAXDCLN4sIirdGmdvbiI7AAVs9nEVTBPuMXgvfxgBBf1/hrL1QtyPPDV2lr/K2oXJsNisaFJB3UNo9V9IP56Ko2'
        b'H7QBw4pthdCvmEWKxZn4rMiIQ0O6A/g0g9pjI9hAqNYTH31JnH2amT3u9Vlj1woAxBIV0LtQAapDZ5/PTOlUaVwS5M7hLNdFrQE6gWBkStgkTAsqmf9CNIkuClJwmTPM'
        b'RBzjby1ARw1zWDVrQlUuk+IAzeSTpY3rwIc7oB4+H1X7sZkQS0CBL5kXgnlnA0pywMV8XecwlpEmXGn3EstCNbgPHWQcFvLwrSx0kB3sDXwIq1+0HoI5U+w3rhZALN6b'
        b'K9FldeQyvuUnMiKu8DY6AdDqwiKAVkRHLJxQtQh3Uz1MwNVkphogkCKzaIeOuUARuakfFyBqXg+iYtbHnIHR1Iv0iFO46Q4hLtk6AB9DFmwWOIGzIhXNeLuA1tUtRuVU'
        b'6VBn7lZNxi8C4sz6fegSu1xuowvTREpWT68TY3AS9Wj3CZp4aRAlUuN3C9wkRDtn0FXcoQqEQh7I4iKUViN1PmpaQXJ6qBh1ahQUqQPJZgUf9SahklXMmo1C3IzOoQMS'
        b'Ph253249XBIbjY/OYnjQ0m1wBbjNi45goy4+HoNKbXFxrJDhbuL4+OB6yg0vZWYMLvPBpX4iDwm6wGcMTHiWgJpogysz8H6PeK9IAD5Qwl/GQReycWUq2UzTfsg2Ft1h'
        b'y4OvGqF2S7WOUXPUOmquWlfN0A1AnlqUrke3/Phc5ohwfMtPQLf8+BO2/AQTNvf4+wSaLb8pVydueH66AOZMXzzhE0I2l8l2Mt1gFqdnK8T50kx5mjxvl7f+pJoLcqQK'
        b'6XaxPEWatUCctEXG3pCXLU6RsVvUsjTvl92QIk9dII5KF2fI82VZnuxdmm1ssVQxfq9YnkU2pie1QD6p2Vl5sp15ZBtdJk3dIs6GSoqXdpSarcrKU+ya2Fmelk258mf0'
        b'k0d25DWteYvjVMo8MkYiopUJXgF+gYHioNjlkUFi/5c0kiZ7KW9KWY6UMuZOfrmLZSBklTRPRjf4N29OUqhkmzdP4vfFtjX8sxKnk6QZi3ilPCsjUyYOUymyxculu7bL'
        b'svKU4iCFTDqFF4UsT6XIUi4Y71GcnTU+3Z5wNVyaqaSXiZB3yJVTBjNpw5jPTN0wNokPp1u+W2NsGItlKWQfeE+/p5CharUZwHwbxNYMsw5ClQJm3U58ntY+P13E5MjB'
        b'HJps9nQImsPuGl/UM2a2rFzAML6bDX7rvp5hDdnFLeisJocC0eNVMFa9oRJjqn8L0I212iKwWBeg7CJiIWzgnCTNrh1D9uQhFruOa6hNShdaabbtSDKqGdVvYTdVgNUO'
        b'qXbfDkxhJ2pG7Wm0sWQwtGWafTsGqxfAPbiQvakWH5wvyiEdQSx8ehd4pqvoddpPYCAqEOXSWIRZxwdTU7qRXrecgcs0O32AyWLRJT0J7SQeH/XCvUpi9lohvkwA5NLj'
        b'qQmTOXLtHiCzCu4uN8TXqXzNfQB5arYAmW1gJ4/tWEMLpqPX0W3tFiBj44tOWhmxlvckRF+XRVQ0VxlPqHYS1Wv2jpJJGNRLh9lIdgYbUIUDtE7HeR31GCl3EINdRzAo'
        b'hL926Crt6hUDO01misElW+C2TnRIs6eCK1HzLm1hLAyoeIEXy0UXiLd0vC+Yn1uoYocH62gKcQtq1/YFXqYFlSO1PzurqCZcm7VjVpOA8zQ6J+HSshB80WK8DFXGoAq8'
        b'P4DNtBRBdFak3fdlQvEtdDxZly65388SMv17bck5B0/VmiB21crBiRwL8IWWELjHAt8U1Kcjz/4uhqN8SuaJ93hvxeIsrp/J4eZbgembz7f3bE88ZL78DyZJkZKI4r48'
        b'oUP1YZNOY98x06LhmPT8dSJTcdY/nn7YOPeroniTYqVT68ij9Cv49jruoIPBm8Hngv/2xu2FYqeGtJWDm/+o+HhWyoPh92+9ufLp1gWGj3PPu7s8Nlv/6o+//ftXqn7V'
        b'G7UlsY4//HbahYDb/abNe6OHdz/+YnjNPKFe5Yx/zG32Txpq+vL0RcePvHSaHsV99FXvZx61xzYuSpu15oukB9+5rF5pN7zkrP9WfX/7Htcm05o/fP9x5VszblxYOqvt'
        b'Qaxd3bZdV3cJVu/8xa/Sf2/9FtpcevDBZx1rU7P/9Jl1xJ6wnQFWEsEYnTl1xAoPL7dILy4jhCiyCZ/jeuFi0zFyiAgVzpwpisFHJXEqL3dc7MNlLFERH3CgWjcOnxoj'
        b'iQH/TbD8SnbgnjzQyGsqA13chfuUOrgYdTHWqIeHGtzWjtGIqlu5hZyzcffy5kBPBwC8cQNQgdmYHQ0AIiw9vKM83SXeuNwTUC1jI+b7793krScxGuG6SRRk3+7/5ktp'
        b'BF/U+u3Xfp5ZLkpXZO+WZYnT2dNc3sQpLhnRpyY6mRC7J/zmklbCQGW/3c88Xi9gLGzqZ7fMblvQuuD0orv2PsPWDqNcnqHjg9lL+vOGZocOmvhV8Cu2tOi2zxoVMiYW'
        b'x/YMGru06940eCNpcF70oFs03PDA2OyBtbjFvCXjnrX3sL142Mq2Tl4pb+G2hAxZuVXwhs2tTywaNJ91PqIrtCOuf+Vdz2VQ67GQsZk+PM2pxaklqH5LRcQDY6thO6dm'
        b'rwavRp8KHbinbmnl0pbZ98zdhq2njTKcWcs5jxmOzXLOo+muw5a2dcmVyS1J9yzdoXRgZuCgdeDwC9dbtg1a+5HLto7N0xumt1vfs/WDnh8Ym9fzW+IHbfyB+WETi4oV'
        b'FYkVuvWzK41bXFty201bJIMmHuqgB+auLSuGzGe1zx409xkw8Pl2bCljMe0JwwHpgJR48PeZkkxKg2HIfAbP1wsV8N7ic+Cb7LYxEoMRPhH4CA8wx4iOxoOP8InLHdFJ'
        b'TlaospKTR0TJyamZMmmWKgeu/OupNyB+Cz7auVeQ8E5BLPfE+W0mVefD1z/2M09f5XM4M8cY+PrUyLpk237RKFfAsXggMiuZ/ynf+FDcsK7xA13zbx8LGIGJlnqmJPan'
        b'UejBdIgCeWAwyREhfG4N7o8BhIpL4nEZqEpvQpSAMcrhzUN1TnSzexbajytjYqHU0wZQqQeHEa3n4ksr8GEWcF/biKtjckTjOHZffqr2TOQk/72FwFEuC0cpGGUAjArT'
        b'+RSC8gCCjgPKvXwKQXkTICh/Atjk7eNrIOiUq+MQdAtA0BUvQFAAKgQJjWNQcoZRqj2hSM82ElxFQaM0lc6qOEu1PYXAwEkNEVDqvg1wXDadHHftIUuC/hSyXJVcwcKn'
        b'HJkCcO52Fudpj1pORjoJWgAEjLgnQo/y7bIwhSJb4U4bk0JJ2pTeQ2U5ClkqjCTNU6yCG7UNi1Pp+OhScZNoj4M+Z1OcKU9RSAFpTmptjTwzk+A8hWx7dj6LWvNlCiVp'
        b'b97LgTkRFJETC86nSu+lqFQjTfaOqaJ9WRcEyodnSjPEcnYUqdkKhUyZk52VRo6hEkSv3JKtykxjOSdgE1iXKsU7ZJmZ/wyLhsmJrJ9DX4hApGJ/rzxVDkBaDcCl0wWS'
        b'cyM1PElHkn+BTAUvIFO9eFUOUYlDZKPaEKuD9NF+XwM+3o8u44srcMHSKNSYJUftrmYQTh5Ed3Dd/Hh82hEdQ1WZOrg2BPfJwHddEOrh269u9QJcdx3C0E7chcoc8KG8'
        b'GFQXhBpQP+oLR0fwNR4X3bbGB41wC8UVxgKeRRh7VNLzyMwNDN28x72o24scX5N4wS3lgI4ayUHSqDgOY7+UvxdfwcdZLP27XGHKdoaevjT4vYeQSZJnLtkpUCpI0dt2'
        b'je/5N7VWe5VUcnhnfGt93xzuaPUML7Q4Z1HocG59oVl+/QbDEH2l/vtb03Uvrz1V6FRiXiK/2GH7aXrXR75v9TqPZTxOufBV2p/T4qUHG+wOfMrru1PbXXu++or6bGF3'
        b'oaRUUt9a6FdfEGDI/GGzhc87X0t0WIdchkuS0K1kjwRPXMxj+Ks4II82dGSMpEtyUVOkMsrLbTe+Gh0XDx4ZLFi5iNQEH340RgfA2XGdMHwTF405UfgX4wwFZbjcAwSA'
        b'yyLjcJmQQZ3rrEP57vh1XMh6+aM+qCcmwSvKV8dTIuEyItTHhSZasXqMngsqlpOjuBpZHlkjTIjlMMYreKtwz2tjVNxduNp7grgP4uOTxF0L/YgpbAn2ivGOjvOMMsaH'
        b'AZWWkxQBDyKAPn4W3Ngt0flPEIMOixjGPcaIaIIJ2D2RoNCAnE8HaDAarsMYWpbHHYkD12vv89A3eAwcXijnMwPHh+Z29Qta9nbJ7pkvGjaxu2/iMmji0hJ0z2TmsMSr'
        b'Qp/8tXW5b+szaOvTpds/643ZQ7aRR6LVoRWuABSGre3rkyp2D5g4gYdXx3xNNIR1lzojulqjMaKjUX8FPRtJZllh++KoNL6Q9YMExE0aDTkorpwNX9+DI5QJORzXn+ED'
        b'vyarvUY4gzkr8uWplgCRjc+R8IgmeJ5nd8ju5yHUg46iFk/expjZqCwXAohz+BIEG7f0mRRcZYib8CUXGkDMxCdh8aFq3JhvBFEWiQA7UOFuGiRAGOopgpDnbH4uKVJD'
        b'PLBcpTkZuVKlxFeN/dEdCAG5uIpjFYUb2c33O8CK0sbCX8FlONngY4VsWIiaZ6BGUcCK/HwhtHWYnDw5rwJPzp7b9EEXYtBNCEm1rpiDj6uIeI0cZrApJXusfp5Twofz'
        b'aKNmqG+5xwLcDR6ew3BRGScEl3hN8uG6WkuXwzxPKYEPF6jZpBI5Uc5V66frjvty4f+YLz8EvvxP/yydRH3Bv08mUYdCnA+p/u9TSf8kw0Nu/n+e4EnNpGwpZXkvpnSm'
        b'MEjkkp2aqgLfmZX6IqPapE7Y8iBxCCBVBfGtof/xsxwvtEef7ZjAm5RMioo+mOK+MiTJ3RP+hIaSPyEJiX7wF9hzD/YPpgUhIe6eL7Q4YUzSTGX2S1NTZJBUzjlsQgpa'
        b'TSNuflfOFAGSz6occm/+XO953jtp6y+FcTukk3EcQVmkixeay855EdH9bye/jDTJL2c7W3E8ZzOxlYsWBAax6aw/ZpvN28NEEgu6Z+5qc0ZlAj/Tdyax+TBGEbluAaqn'
        b'CYcw2Tby1AHuJCekGK45R2+TA23iOtfI7DF3Hs2IvT4jmZFwWZR/Dqq3BcAvP2YravXDF2LoJhRqCEFHAoA7f4jT5f7oaBZtZdsiU93NzDKGydkc+2XCCtIKMe7oCr4y'
        b'i20k1slvPqpjj5ldwGdwId3IXA4uOWM5Dx+grfw5WD9xPceNpOxiCzMDAZS8KjjAVX4ARZ8ZnSldfsvogK/J7U0FVg/yfB+1H8x+dHBe9w7fLktu4KDOvB2fhYxWTRO8'
        b'xdfJlt95/+n9Jd+IIh/MFvL1dReeuc/Z9+Vio6jKL3OGh//0iw+OZdfkoBmH8kMi10aujZ178vdHVB/MXHEo5tcnfr1QsWl2tkFtxK/TD4X/vWHm6M4Pd239cxrKnvXr'
        b'0E2n7dotXP624qHBxjMfP8mSnTKI/PGjfWlLXd9dn+CZ/5vcxs8j7Ge/ObYtoPkfC+3mHYz5+/LXhnW6EpcZxffl1Mzvc759k9MQG2D0eadEyIKCdvQ6bpqUzUDNeD/N'
        b'aOiiK6oxYuQN0WnU8jwbstCH64WazMaIkQ8C6HMblwCowGUMI5yNz6MrXKNpuIzNlDSCi2uIwaUx4xkMY1+eKerNQIfRARa9nAOguv95rgR3GxjpCZEa9TEm+BbPIQqf'
        b'owmZTfi436REyQUnbsCuWInez0t4kH2K8WQHC2D02GgXzPXu5z8pePmGBS+PQ3UZE/NRrtDU6bEuM9293WVomndFxGMhxO/1qS0B98xnden083oMhu3Fo2LGwuaxI2Nj'
        b'DyUr29a1rjv9yt1pvlDyyNr5vrXboLVbu/k9ay+SNzC3qlBWz6tXVC1pSW13ak3v4p3a3h9yJ/Z67DuW9xYlkNQHVMmtDKxfN2g+s92lXXp+ZlfUoPtierNdvbLFr2VF'
        b'/c72uZcXn1/csfTu9AXkFjvHemkLp96NJD3sTmwdNHcbtp/WPL9hfktiu/mQvVefXX/EoF/ogH3ogEUooKZvx2YxNs5PGI6p0wPgnwd/2TzEYd3ghQxaqBeiw8NCDnyz'
        b'wErEoiiyLkZ44BlehqdeKnrRc4z1PN9ADmNOEPsTRpNuIChLqsPhTP+aga+fm25oEEqY86LZPAmHbm754qrl7I6YIe7Vbomh0oWTHmAbt3opBG7w6ANsfIAagnTe+CNq'
        b'vP+xR9QyJNxnX0wywYmsCf8noSfrcWQsMqCxpDfFFunZmZnZO6DWZHNO3b+c5B0UMrFSlZOTrYDYfYE4NMxTHJTkKQ6JnIJZ/ged1MuTDv/Gw+jEq0jElBGoTyIpD7BH'
        b'+Ej+rNgVuCtPgft4jCNq5zs7oiZVKNR6ZTNg4hJcsiZSm0JKiPJaHekZQ3enj+KjUbG4OGpVJC7xSYykEJTgzyTy7KIOumGIbs5FJ+ixBXROpkMaMgpekwP2ZzW5A4wV'
        b'B1WF6aOT8ahsnz74icNMMtqvI12Nr1EHUbLMjIHwwO2vgs173p29mpGn+zpwleVQcl6klpUtNkK+BoebHecKLFU+91NkRw+9NRxu8M6mYQXzllO/q+nsOI9Fa3/87pPe'
        b'5i8F4VurXjO/7afKvbR/mexZS+yVmgWizb7+gW3qDRZz7b4f3hHquXv1w8XLN7qft1Hcvvqt6PeosT32h79Mr/vHrxNmfFn7G5sbI+cNerHkPieobLiraM73v1nz9o9P'
        b'OOpR8fvTXSUCaoRxWZRMY+AhsGiakLLWTcZN1AjruKHy5yY4Zd14wlqTrM5AB8fIWWZ/3Eqe7wEhdeOjW1y8sDoKl8aBeKPicjXtxqAOHdRlj+vG6Nk2fGkFhLaA8Dno'
        b'RD4nCNXOGXOG68I4fETT4Q1cgMqMFYbGuMcg11DIOLjyuejUUonuf2zTyaTQNTZu0nUyZHnUoGt/UHPeqTHn8XrEcKfdM3d5aCVumTZk5Ttg4vsgYHF/2lBAyKCBrzqi'
        b'Yi2YVethY6sTmYPG7g+tJAPuKwaSXhl0f2XIasOAyYaHZtPqdwyazbpv5jFo5tEeOWQ2Rx0C9hzaG3Ba2J826BQ8ZBUyYBIybGx2bPugMXTk0hIySLLXo+A1rNXRowLG'
        b'zLIisUJaYX0ibtBUQiu0c9tNWyIGrTxJkttKHa0gR1ZZqytUENDyT20t2U5jNj+XgGIRsava0U/naGLX7/Yzf39Vl8Mx+7kGtUrozJwSefFebjE3M2ySlbWY6dz/JXt5'
        b'YZJBWZmTKc8j0dhzkwjRBRglcjVdIc2gO8VTzJzWyErFs1+ahJtU2S0kYVV8UuI6Yi7DQmJWrorzFEMvMckhCdSOhtDy5PhVccFhiZJ/bu14L1g7zbPXpQKdwC/Yp48N'
        b'bpglMvS5lYztG56bwNgVz+0XH1dJ0Hl91LCLtU26e/fRQ9n6urgGVbLnUYv27Xl+8yLcOMWA4m50Tr7g7RM85SqonaZv1/je7KbW6vmHnQ6vKG6tbS1srT5/tFt941Al'
        b'Rz+xfnXIg7ijTbFzDKqWrbYK4An/lFZ4vkN2UeoZHlhgKw02TLXyOPeJHu+j5QvqCwJ4zBqu8VucvRLeGH0IuGc1ujURVjrGa2wOPmdEkeNOgIqVeL/dBPDINUJF+Cwt'
        b'tRPgQzE+cJ+XG67F54SMng0XtRqidgn/pTaAT22AVv/1IW5ValJSE35TK5DEWoHRPXqMtX29f31QxRZ1BKh6vXzQeBZV4KVDVssGTJYNWzjWZwxazLxv4Tlo4dmeNGTh'
        b'rw57YG4zwWgMm9vULapcVL1kwMBpgrIK/qmyKgVaPWXVNISo6QQO507Q1G+26f08TaVZpkqhE9Mq8iTQRwykL7rqyUIfkiH0QcUJNE8jTbV7jb9lPj7x/0yhSYaFz5mS'
        b'YZmIgWh2P0u6ncbyWi0np0ByZNIsiokAErFAKCpLnCpVyqbqr3bPJW8iTvr/PTZ60Vrw42m+zwZitRu4VzlTF/epBAwXn+Q4o2ub5d+aD3KURPtr494i+lzyesGR1urW'
        b'6tw5LjybM77R3Hc3C3+Vx0SF8/2Y37MLlDthRRKl0OqNAXUYIHgi992TKKo7VqzuPN6sz1hMr391yNyjPXzQPGDAIGDi6h8RkaWcnK0gvuc/0QKSO5jcW+REPYjT53Bs'
        b'f4YeKAhGfPnCTiMLm69Z2CSRqN0K/J9f3CZT04fPfU+anC4CqWKXeIc8b8vzjJgiW5VH1qg8i/gjKd1hm4T8JzX4MmUQT3pJynhibaKOTNSLyYvz5+nIxFsnEUH5Unmm'
        b'NAWc6zbZLuWCycrkBYwlLdAkAEFV5HniJIU0S5kuU0ytFxqqqccOQxwqS4Ha4JWnOFsvMcnt/bO6fp5i97Tx7Uv3qbcG+we/9E64PrXqypAQLeNSRdp4+nJKrfiguLAF'
        b'NC9JrdfP2cnTZWFBaIQN47v8QwFEyxua/Pcy9Mml2ahLOREXbHOgEcvyRK/VXMYnHsAB7gmi+S7LdRtp6g1dFq5j1iXj2+xemx5ELfO+h0W52cFnG2ANkhHD5+2caSBF'
        b'3i7iRbazYtZoYiB8K5qGQdEkAIpmdqE7uujsHHRTnli0i6M8RFzLKj2yRUeMzZVqGWts0m/4+lrkcsMaTE9dMdhl1uR5RXwFAITvYMptMzdRu7Hbprd/wdRtS7kofScl'
        b'/Q1GclTyQUfD5nO1XW+81Tvs95Fz5oXNnrWbXduL0ALAJGH6l9pquwtN3z68LPnU9Qq/EvOhEyzaMGT+cttxp99uCHGIl0uFsK8S0MYNXDP1WI4uXLxEM0hz8InZzzNI'
        b'04LRAW6AD75KG8B9HuQEtXE+voqO7Mg1yEWH0Ek+Y+TJBZN7Ah2lwcxi1MGHYMaCPMbHhWCGj+rpliHPN55sdIB5bkSX+Qw/kINu4grUCaD9XwcuBLRP2kojJlBjA3ZP'
        b'JKjxPaoxvuEixsS8YuGQ8fQW57vGrp9aOdZvG7Jyr+Q9snKq4NGjM8f2PbRzHZgxt99lcMbiIbslAxZLhs0s6ySVkvrgFt6Qmas65KHltLqNlRtbAoYsZ921DLo4nySR'
        b'+s37E/ul/dZDHkHq8AfmthQOLep/ddApesgqZsAkZtjctm5h5cLqxQMG4gkmX0cRxfyL6GTCHtuE4SoSidmfOMykCVb/qexnWn0ap1QLXZjTIm+CfsiUm8WgOx6RnhBr'
        b'1sWCF5jLQZfgf2doOPiCGm7R+IYiDj0owr62iEkXUP/AnfSCIp7eJOs/casJPAF3H0/jH6ZcnRTN/HqSZYjNlqYpxdulOTkgByVrxdOyt8uUefLU8dMP9EAtfUPWuJVP'
        b'l4OZVebIUuXpclnapCZTdondc6R5W9zp/og7ORek+JeHc+VZ8jy5NFOcCbwAhtEwM6nNPGrWd2jOb+SoFBlTd7MmmTjhCybOKJ4+HKDCd7zoxCyPxEcSvFZjNXnJUSTq'
        b'xGrUh/d7goZGcHTmLo2g+wAyUaKHO8cTH2U46xnchhuRmr6JaCNWQ/gQRffhA/jkyDyji0q40dNwBSwAR2oYOnAhyT/jsgRLZ2rgdBgjdIsX6YRa6UZF0lqnlcCmKweX'
        b'M662uI0ay7gZZozDenZLw46zmN3n+GiuLZPJoSd/N/TtsWXoVoQCnfbVHPw9ZcqsU+Fa9qGaFlzuPdFcE2ONriaSFJQ7Pokb8SXg1xRV05Y940XMBxu8yZaDQbBxONvd'
        b'5/ONmQrzJWRPxPNyQBwjv+H1Bk/pBiqyGW/du+LDaLzM5OSDL7KOz3Q7W3z1d+8eLJ5l/Lu3T/usGPjNgX6BsbzFvVf3E+58i6A96m8r4jPnSn7hOj8t4Osfvtjz9fnb'
        b'4nKvvun2fdt2Jf7uWZ864Pcdwr3fOAo+x4v8EP+3PQ/dNhTwuPZXv3nvw/utBX/xevvZ9E8Nt98rvZZbXvuOzp831d5TfpGfahr5EP1QvI4j2Fu2aqmjX/q9X9j8/o8J'
        b'3fNkH/S/8seyWXl3Jb+SnDqeMfaPow9SE/N/mv7DgMEe//jFcT/m4O/mKHdc/fubH6/58OQ3qyMbWo+0PRpb7a2zfdbd8m+MNkQWB1fN3eO9xDWtaE7v3MFfFFQvLnrv'
        b'63fWHJ/256izeQ87P8/+7bdVP956//Ah63kFMWsfJYo/GDb/QiU9/PbY/Po3zU4XTY98FjJzwRyJMbX7UtSD1HSxgQlAZc7ECszAxfTsRRi68hou8YwnUxUlCLNidHEJ'
        b'dy9uQf00ihWgC5aT90ZqNF5lOr41RoK8bTxU5xEdF8uBpm+InDioSWAxxj5DuRiXeHhLcLEn6MF2a3SRG2A8hybkHJz2enjDaj1CFi5Zkl7ChAzGGl3lR+aj18fIK1Dm'
        b'owbwIC8eIM1FPZqUHC5DPdT7bIWY+QKs76g4Ty4jxMfwaR2uriW6PUY0JFWACyadIDXkkDOkm/AdG/a0y9GtczW8kF2VPmtUxvVCag4tnKME3/l8y6VuA/GYG/FhNqt4'
        b'BJX5esR7RUXFxXjiUgkHH5jLWOGbfH/chprHyAv2UHtS3NSNnaQwdlsHH/ccM6MIxDEcWuGslTBcdJwTF+hG+U4ES3DGg0reS0gebYeJucFFlaghVmL4f3/s1ZDRZAzF'
        b'mt0I1v8aEcuXPG5td0+hqRcOZ8+6juaIGAururmVc+uWVC5pcb1nzuYOAoes5g6YzH1galmRVh/aPu+e6exRhmPo1M8dtrat21G5o3pXBf8pD648srCpi66Mro69b+Ex'
        b'aOExZOGlDvvU2OKhicN9E+dBE+d7Jq7DNo5PGJGhcwV/2Nq+bnfl7uo9FfwH1vb1ec2vNbzWrrw3PWDYwmFY7Nqm36p/2qDSsEK33kW7rZRbtXjYzrFZ0iBpCW7nDdl5'
        b'VoY8sLSpN69e22JWtYnig8B+88EZi4bsFg9YLJ6wb/TQQszy1B7RlThkMa+CMzzNqYJT4VYlGrUGdmBxGFrfN3AYNHC4ZzDtof0scog1mgM3zpRc9OzaMei+9L57+KB7'
        b'+JB75NDMqGP69XPvmrg85pFKT2fB0B8TiTyjG0K9pmEOvLcdBGEzdVgooTvCJ05rRED91b+BFPTg2SRMISOYYsq8KTiaTaVnZFNJBLACpuTnRZTkUdJJqGH8cEoWQQ06'
        b'GtQgANzw/GWHjOZoyv88drjzEuzwQsz3z0DCBGAwqZn/FkiY1OOk5v5jkPDiyxnN41UexP7g123+CUjw9EaFqJcFCbgWn6cwYRU+JgacwHDQSSOCE/RQHX2zFnnMAZ3B'
        b'JctRmRYrsDghHoHdUhFThc+hgyoNTiA10K00LVBAXahXwlURMDAH1RoqqSPHV5W4T4WuGOUb6uPevPxVuvlGqAD1oiZ8C5E3ZzSgwhxUhqqtkRpVmqMqYQaDavB+M3Qd'
        b'dSSowoh1vLIRd7y0tb3oBm0wCHVt3IBbMjPwHXHIPFwEjKn1otDBAAYde80Mda1E9RQpdHJ4NMPha+WfXrhkHgsflK9aMeB5THyn1WxIzItkL87zEJCVK/bNFzq/7zaN'
        b'URGwja/gi6hNhEvpUUUI/spX6kIctCKSOkW6i4aL48A/pKLXUc1e3Q27NW90w+fBs5ahrp2oFxDUImYRbgiQcGlHeTAhJCXlm/UNZ79vJtt7uYkt4wvXfDf9zZKTMJNh'
        b'X1nQs2jNBKCErplNwUoE11XiFomQHipDrbjSBvcqx1Ng+NQGZ2CilHLkjZuXijSn4XBJPoM70sLZR4tKcS8j0hyGQ7d2M/iETwb7GM61jBX0PBx7GA6VuVrhW7idvesK'
        b'PoGPKNnzcC7BDLo2A7WwTwiDkysQaQ7EZaYz+DhqYY/IdPFs2EEucQg+td6LHfnH28xYcey7ofuqjh0jEbBn8favxle0/PqiZnKA7/ZqtugqdH1RyzFvJzCMa9i32CWC'
        b'uAonsLxwtpX7QnpTbhjq0XCLu1EZ8EvemECL5Cm4WcvvTtRKGO7GRfJb1sf4yp1gHwsUPXsT4xIOLjNpKpAVJLaMlL8VePLmn95+6+Dc7L+Ubzl1rVQndlFf3CuNH9fv'
        b'dFGMptwcm/7ozW9FTV4f31UzBRv/cGvXwpsNxl+Z393H/ciju6M7ryK1u1EY8MtQwfE/eayv+Pvdgq5DP7z9pBPNcKuo6F91a88Nd4uWrx663zbd5Pv4r99FDbTI9CIe'
        b'HPCY6XU3ryiH9/SPFjtczT+JDqjPs/sI744dUdan5M/0Sjzo1FQ4ei/dt2RH1rdn7eUZdxtVBlV5f1WZnglT7cv+S+bF+M+S3ty/9gf3mL4P/rzj82u/e2/VySerYgQX'
        b'vHad9m77xDE660mY7y+j+u7L3kvO/d1XP8a/Hrf7jNWQUry4Wvprx9/dd+5c79oeNvKaqemlXX++/fmaMU/DX+2r/9WfanPxzKeXf8p12r1I8PHjtYrj53bqyv6Qbhb+'
        b'/SwH+fSQQadO0785274X+cvaeaWmf284XPsL/cL0rL8sTK/42H9noXm/+AfBh/frz/E+dey9dnZxoeCZ8Z1bv9nyyd8PSEQULeLOTbFaiDqXsxfXoUvOqJOe/8XHppEU'
        b'jQO+rIWpGpDagRrYCncSmCmPI23CXQSk8mMojkMtJN7QoFQnTjruBDN1Cp2nPa8yQi0UpgIEJEiV4FShH8Vve+d5T8WpAD578QGCVIVLWMbb0NHV5GgQKk1gTwdxvZaJ'
        b'6B4vOu5tInLHpR7k3jjcYaFlbzrq5ePLuIBLMfZGfHEOm3nZYMnmXrR5l5v4JAXw+AIuFlOEi06uIyAXAC6ql7NjK+auZJnEN9MphgUAOxM1Sqz/r1HifwNXWk/AlRPh'
        b'5TjCNKTIRJmamUzeaL17Mknx5V+1+NLgfwFfjnJ51kbqiFFdxtRMHQTwsj61XlGv/4QRGi4BkGlhWc+pDAO4Z25dt6ByQfWi++YzBs1nkIeW5t419x92IE9XOddHVYQ9'
        b'sLAd1YObxgwYa5cBl0VDVosHTBZT+GpbZ1xpfM/EiYJXY0OzqeCVINbABde2dm99w7w3e9AkoIJXkVQf0MJrSWoP6OJpnvaq3lbB0yDZlrmD5u4v4NVHDuLm6IboxtgH'
        b'9tNbeS0hp3Ubl0z86SBuNW9JOm3bmPDyCo8NdZzNjunVu1QZjZoCm4+dGRuHE1HVrz1h+IYrOeO91yuqyfEs53a/low+27szFzx0nNmibNhUET7sFAbA13Ilp14w7Obd'
        b'rjpveNct8abtGwFvKN7hvDF3cH7MO2GD8xPrhfWq44aAfqHmYx3S9tMIzlQQHGHI+6WhIMJaR3vGKp2sqQzm3yXVXn7GanzVsZg4H76mLLWqSZDYANDw1z8TElPsXS90'
        b'Y9pFATwV0XfctQlXxUw4kYNrPdB5N45PEOO6VDAfN2XRlEwWuo1uepDHvioj8YEYb28eo4/ruOgWvoRvS3jx8eESTriEGx8uFy7/I1dpx2OY63/j19SUrLFY5fDLobe+'
        b'+uIL74Xfb7YOzSmwPOQf8LeoxGifnuBYD48hfsmzq28lnu/Sz+xdd+hXHwQnuO4ZeN/5w41/S/5i4f1br877Vc6iD0589/D606c//Phl9pfXA3rvbQnrrLe8Zrb6Vk1f'
        b'4mrcU//bNPX+nLvxqevMn+wP/MTjrbSfPl7Bv+vQ8Xae7V+lmY3FTv2rPw03SVx8/lefdyx2WvQdOmyybk3OVy6COPe0Jffnm77/1/f0Qnalzzld23bvT2kK6afzFYU7'
        b'Mh1lHyysLe9YOKdta8lfZVG7fxlbsHZ+y57UFFf0/iPLsJv5M1cHu3SvKHj21/XnOVFnBvb/wvJWe6leZvDQqcIPt8x8petw7OmazJCFDW+u7uE1fR6YV/nxzv17TH7z'
        b'blHXwT02C9+N6Cp5WBrx7i9H533HP+naHPxfpxb+15D/b6eNVf3Xo3UKn79X7s1y+K9Pdz0R3Iy8fWjfE9kXs5IrB9c8tpu/n/e52Kjq8mcmu9b+5bdvNH7+yrye9s7X'
        b'A26V7hh+zTri3ac5RxeVPX3X3Ma5KLfqH8z0KpeeJ+Wff73P8/Qbs9JWrw4oTnjX7/N3cveE7yvzeWflvI1NfzaYOdwcenJRifJzi3Pv2lq84yOtCtsTdrLuafL7f5rr'
        b'/5nn7Rl/zCm4qVvS92nFjOv5X/c8E9y/caHV8befvvqP/dMfm+/7hbN3Z+jqK4ko6vO7nziuuHT1+7dH95uEPLR/e9mKuVe+3/LKhZHNfml/uR7Y3GQ1O+RK0zmfMwe5'
        b'Mec26d5Y3OZS9zj3T1sjFuoFDPwyX+rrdqJzz6tzFzY9ybz0j0SjTz56dPXjtF9+sfvGh/EPDB/41v7RYFXz1pjHc778w3u/V3zz4duOu2/0cjY83l0s/ekvOatWrSm+'
        b'9GHxtrVvXv7W8E4Grlm6NeAfGRHzI+5+ktL2t/jVT9sSVH41bYqNvz83K6utZ8GPx0t2jn1z+xm/+bPs6aoL5zZtPB2f+EP5mo0Xv15146+NvxLm4lmv9fyhf933itf/'
        b'evzqb/5msPinZxe3pzkm9H4cnNyR9+tPa8uHdHUDelq/2rDub0vmVP/ip/3yTLeItxtTw/Pej41fs+TMMfUn38ed/OjcN5+lRAeE/6QTGLr2Dd0AiTHNovgZSXAJeHfO'
        b'vChv8gTTkQSKDAy9lRpgMBuXTtwT2YJK6QNK02Shzz00cc8NMyd4aBHuoD5eJsLXKThZ5KFNol/GTTRPk4lfx4djCEIo9jCHruIEjAiVcnFrjhf7bFO5L9iEWHfvVUjN'
        b'whtRJhefCYT+2QwR7nRBJag8gSIbfEWOSlE5BF5CniO6vpWeBMnLmgeFxbgcDEtRCkQ68zmoGx1GzZSBxTuNWPCA6+wnoYfE4LEZFISgNqOpibRmdHLC4bb0DXQLyHA1'
        b'ap+QrSpcyias2HTVUlRJBUZeJGqhrfX80Jq+JT22BmiIApZ4fD0Kl3hG+QPbpQCahJu4LuhkDCuRLlfc7RHthdX6+FBUbDwRWDcXN9nvoGm1UFSOOmPII2NeyagNcA3B'
        b'eyJ0mQsg6KCTxPW/gUx0/8Ov/z1Y5DoJFi3TfPa/8GExkm5yMvVVybvHf1Fk5ACu8ScCjTwZQ8tRvo6e9QNjswr/kh31TsV7GpQt/i3S1jmNu9tXHH+t27VL0e/Urepf'
        b'0b2z1/vN0HfMcORd/9iHNnb1/vXShjmNei3RgzbeXdaDNvMGFsUPWscPJCYNrFo9mLjmrvUacsDHrDprwMR1lMfYrOWM6jNmFhVBlZbq4FEhY2ldF1EZUZdQmdAS3BbR'
        b'GtGW0JrQFznkunjIYolabxhAGymOrYxtsW0PH7IIUOvRm9R6j6xt1QaP4Jf+qAFjO3PYZsb4f49N9Wz11YZPbIR2+mqjUQvGzHbY1GbY1B4AAykYNYrjWOoPG5gMmM0Y'
        b'5ZHfjwxMKnxGBeQnNG9oCoQOJXRZQo8S+iwhooQBEANmbqOGlDKilOuoMaVMNGWmlDJjbzOnhAUt8hq1pJQVpWaMWlPKhq1oSwk7lrCnhIOmniOlpmmo6ZQSsxWdKOHM'
        b'8vHYhVKubNEMSsykRZLRWZRy0/AhoZS7hn0PSnlqKC9KeWvu86GUr6bMj1L+bAcBlJjNEnMoEaipN5dS8zQcz6fUArbiQkosYonFlFii4WoppZZxNI0EcSgdzNE0E8LS'
        b'oRr6SRhLh3M0rEawdKSWjmLpaO39MSwdy2H7jmPJeA2ZwJLLNeQKlkzUkCtZMklDrmLJ1RpyDUuu1ZDrWHK9hnyFJTdo+drI0ps0xcksuVnLppSlU7R0KkunaW+XsXS6'
        b'VgwZLL2Fpf1G5Sy9VdP8NpbM1Ep1O0tnaYqzWTJHQ+aypEJDKlkyT9u3iqXzNcU7WHKnhtzFkru1nL/K0ns0xXtZch9HM92vsfQyrqZ6EJedb66G0xCWDtWWh7F0OFc7'
        b'3ywdqaEfR7F0NJcxdx42mzFsJqHfTtr/ZjxZR2uAMdnAZexdm30afIbsPCBW0fM5Eq0OqbAEK3LfxmPQxmPIxovk4z0r+RWcCj+IwpoNGwxbpO2mQzYelQLyngnPRxbe'
        b'XZaDFoHqsGHH6c3rG9a3C4YcvdVRFanF8aN60CRYB32TB3omFan1yvaQrrR7egufcv30fB8z8PU1APZF5MtklA8kmU1aud6lRdnFv6c35xuujZ4NqRCoqQUk6BrEp1sr'
        b'tw44JQ1ZrVKLHukZkw5Wtri0h3ZZdqn6V78R9s6MAY/l9/RWPOVK9GweMxK2lUSOphmgybLVcHZPz+4broWeNSm019QAEmzB8wpjXEM954kVgARjxLK78p6e0xhXV282'
        b'KXPWVAASLN7zCn/n2uk5TawAJBiH51085TroRXMm9kFoMBITq/joreQ8Ycj3xIqEfgy6oWddoSChe92eyj0tUe2vDVkvvae77IGuZUVKXUZlRl1mZWbL/Hb5kNW8j3Tn'
        b'fzu60pCjF8V5YDb9jMGAV/iQOGLILHLAIPIZfaPH0SCbOFvmQ1vzOE/N8zoWI9zk5J8VRf43PDx9CdaEt8hM8uiKQhKAjjtzAimVixn2lIeEwzF5CqGnyTfk6+fGn61C'
        b'P6ZbtIgnN5X/yFPugStmRQkQbOkfXGbDf/TTlSXR5qbdatc171nWWlT5n81HZb8pKRqt4tQte0N+W1K47ntx0EHBtcqMhOzjW84E/flY+Q8jv3r3SMS0J1/fff+3q6tO'
        b'fLLtttdfWkvy68N0ggodZrhvyAkrFXpZOBrMffh4/6urNv3R+T3nBPc/+qx75ihYw0h0NDujc/bRfzorgWDWGB2Abz1m6DQXt6ObWE1xbwS+iq7GJHjhblyPz5OqJHlm'
        b'im/yUGsQqqbNOKEjWE2wMS43Q5cJttZgYzPetARreiApLhgXxkTFue9bFafDCPlcXcO57N5zL3qdPKaRMs9HyHBWklcO96F+ul89G9fgcg90xS1awHBiGFyvg/ZTXOpn'
        b'wfVI8PQGdMy+ywDuNN7C24rKFktm/Bsw+f99ou0/XpczKPJ8Odp8OfQk+1ss9GR/UegZzdAX4HxtxwjMhw0t7htOGzScdmLnkKHb/vBhvn5RbEHsgKnTmXn3+J6/4RvS'
        b'/8yf8nOFggVPGfI9Rr9H0w0ZA4v9CRMOTjmN8DJlWSN88uTwiIA+kTDCz5Qr80b45JDoCD87B4p5yjzFiCBlV55MOcJPyc7OHOHJs/JGBOmgUPBHIc3KgLvlWTmqvBFe'
        b'6hbFCC9bkTYiTJdn5smA2C7NGeHtlueMCKTKVLl8hLdFthOqQPM8pWr7iFBJD3eO6MuV8ixlnjQrVTYipM9hp9I3J8hy8pQjptuz0+bPTWYf1EuTZ8jzRkTKLfL0vGQZ'
        b'eXPMiKEqK3WLVJ4lS0uW7Uwd0UtOVsryyFuIRoSqLJVSlvbcAilJILX5X3/EYtZylGu/yD+rpkyAr59++ulHsBumHI6KRwzH5O8n9PvnmBFiNN8UCYPsmTftRUEzec90'
        b'te+9GjFJTtb81liuZ3bpk/+FQ3FWdp5mJzReoktew5SWnQpjhh/SzEwwu+WaVUVOgsJ1fRCvIk9JDv2OCDOzU6WZyhGDiW/gUXRplwa7SIgQnukuYv8FxSWKfoZsB4Mk'
        b'yHE7cOUczmMYIx/ctchwv84T/mtCjsVoqBGjZ3pf135Q174++p7urAHPJW/OxG6DntHDuiYP9K0GrAOG9GcP8Gc/YEwqbD5i7GhX/wdl8M43'
    ))))
