
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
        b'eJzFvQdAVFf2P/6mMswMvfdBUBh6ExBBRRDpICr2wAADjCJlhrErNpDepYqgWBABESzYzb2pm2wWBSOSZE3ZzSa72QQjiUk2u/nfe98MRd2S/X6//x+7vvfOu/3cc8/5'
        b'nHPvm6RSM/5YqvvTfeiyn0qg8ik3Kp+RwDCh8pmbWPGa1At/CUwfBv3koHqTpkVRllQCaxPHlvJRvVuA/mXw8ftg5iauLZXAVpfKZGzSsKU2TdViQyVw7CjNw2LuT0P8'
        b'iKXBsaKtOWnKLKkoJ12UnykVxe/Mz8zJFoXJsvOlqZmiXEnqFkmG1I3PX5UpU6jzpknTZdlShShdmZ2aL8vJVojyc0SpmdLULSJcpUIkyU4TLY0IoR/ylFL5Tll2hihF'
        b'kr1FlCbJl/DT5TlbSXMrQ6JFaTK5NDU/R77TRZSrTMmSKTKlaaKUnSR9uVS+VZItCpFm58slWaKlqAY3fqr1DAbZoH8CzNP30UVCSRgSpoQlYUs4Eq5EQ8KTaEr4EoFE'
        b'KNGSaEt0JLoSPYm+xEBiKDGSGEtMJKYSM4m5xEJiKbGSWO+nEq0SzRL1E3mJGolaiexEnUR+okGiMFEz0SSRSmQl6iaaJxomchK1E00TBYkWicaJ3ESjRGYiI9Ey0TpR'
        b'z9smgTKhsni5NiutpucmV2RBJdpM04mi6WcbarHNYpEdJaJWvfBWRi1kWVEyhma6mJE6UyT00D8DPGKuSorsKDE3i4cIHXMm9fFWLEXJLvfXe1OxSjv0rG8PjsAyWBIX'
        b'vQIWw4o4MayIWB0PmvmuXMphGRve2SpNZcyoX19d/0F0CdSToDbI6Nlo5FzEGR7iBx+NX4h4pI14pJuoh3hm4K2vGj1jJXvG6Jlo9IwZo2fOGidjMZOM/oW3U6M//B+M'
        b'/jUy+ss2GpF3KFOKEiW7MDP9qSy0IKj7W83Yk+mBIor6xOFb5hXP+4JYKgtz6IlLE8NQkKxDLUn2+lA+L30D/fp4yLc6pySuNsz4jxn/WFu4Op0ap5QuKME/1g8xscx9'
        b'haMjLHUPd4Wl4Nwqx8gYWOVivdAtwjUyhkFl62gGwVPwotIYFQAtoBGciopwiWBTbIoBa6WgVWOt0hwl7SkARQp4Zbs8P08pZ1Ka4A4T3ISVdn7xSluUDAthe4YqfQ44'
        b'oVSAMlAMitHMbGR5g0OwTmmJ6+8wgzfUteQxKE1YyASHwaBDPqAzwIrlQep0eJFCGUqYoDjAGZxEGRCbKKXBWnW6Nxv14gpzvr2xMTyuxOsL3siE51TJ8DLsx+VrmKAC'
        b'nnLPAkVKI5zlMKwH9QohEh4TNmyiQAO8wCBjh+eXgWaFnENRG+A5WEah7g/BRqUJ7nYt7IbHFHIN/Ag6YAUFSmGrH13hVdhFoTbRow9shtUUKGcGKw3xjIOedQpQyaao'
        b'NaAXnqBA29Isusgx0G6MUpjocUABT1LgOGVCUkCP715FHuoCGMiAVagV0A366DIn9ixRwItIgMD5LfAoBarBnXySMg+WpCmUqAysmwtrKMT3ZnCS7nY9aABnFVqoEOLG'
        b'NdhOoaQBIRltJrwOryrgIOodbJfDRlShBjhD+i2FZ3MUoBwvBHAGHkNCEcWlpaN4J2xXCFC3wTW4H3ag6mDnfNKJWHgOHFdsR8ZC5gUbKFAJa+FJmq3FoHybQgc/dYAa'
        b'XKhpAygk/VsLjqM3g1qoD2g4JbCXAu2wdR/pBKyBJwIFeDbgWS94HpVaJSEJ4BisSwNlaAIZKeAGjwJ9wemkIV9Yu1MBBxg4y3pYS4EqcABUkobgJW9wFg4qUfdAgzNm'
        b'eD3qViHp+fpceEwA+1FDEeAcvIDmAlw2UuLVumiRULEdDfYVeBBXVwoq3OmpuJUKqhTwKu52cw5spkCNTQzpwmIkHccVOphBp8AB3E4LOL6WJL2C+F8HB3kozR22wVMU'
        b'aF0Mqulp6oc3kVAN8vC8X4TH4FnUCV2VdLWsgT1wMB8lbYvHTVWJQAVJ2eKfAgeFWB4aUA5UpA30xxAOaYDb6SgJMWIbEsguVJkgh2ZD29I4OAgv4jmvtoCdqCg4DW/Q'
        b'bD0Iy8VwUBOVWj4H9lHghI8tPellKeASSsAzcQStHsShk5YapAtb9bxQAmIqYlADWm2gUxNeoCf9JCgLRAzH3btqjQWvBl4NI1zVtFuJphw1k7kCFzkJr6fTXKhD6qQY'
        b'dW8QpVnIYTfikAXsoftQ6hGPU9D6gwe8sJwch6XbSXVO6+LR7OFJv+2Ku90WF0yKLEc9ahfwUAK8A3rQ8gSnwa15RIUAJId5AjiAV3MPrIeXUS8Q/8+R+raCOwsF29Bg'
        b'/dC0oIaad+rSK/OkbagAXiGiimT/ImrJfB3duYFccBgl4VXWjMR2EEmx6S569k5LV6MUzLrBGNzOiZVgP0kxgKXwoiIf9/uyHSymQFE8klUi+BfBibUCBWoodjVmdlME'
        b'bKMra9yzSMDHHG3dCa9R4AxoBddInxmIc52wDE1EDpUGL+WACz5EZW/YJQJlvrAaXAblHIoFqrbAk4w4cAhJPi5mvhQMRKF2UjBHDqSgFXKFFItcDAtB2TakJytAKYdi'
        b'K7ZnMpA0t8I7dAdPwwp4MAp1JA11GxSmsUG/UoQTapHxaFOV9FI3qwkqmJSJCTgUpXQk4gSbEM/r0Po77wvOcSQxqJVLvvDU5hDQuT6G8lFwwFHYYk6GnAjrYxVY9uEB'
        b'pOUoBAnqYLcSg0pQvlqorqQPHoX15NEHnIdH2ZQl6mBxEFtzqy+pxRBZHQW8hHidAK9gBV0JGlyUYlzLWVjCp6sBV0AXricc9E1VA24pYRObBc8G0LkPy5ChVDXaO6PR'
        b'HrrRWnAils0FLcG0wOwv8EZaFK13GVpkx7HeOqQkfV/t6AvrwpGqR/pGXYkXbh1V4go6pSw4hOT7LFkVKaALaXA5FrszSOkeQZ0AhbCDsBIeNdw8xQOakTc3C0SwDHQl'
        b'GlCRufCOSEOQC28pXXHmA/A8MlUvsAxcgBX41o2bdw0PkXPyhCuV7sRKoRIHpnpawUqhWwCdHCPYgiYMlKH5CodDXGRcinLIWogH7aAFKWECCKxhJbZGxUsJolsC9oOW'
        b'6XFTuTSv2QmUBRxkwX5wKp9WROdcHBV8xLbgrdg8H4Vn4FUl9hV0seafMVkVz09DVwzoyYODvqAnhpsSQ+WBCzxwDbQ40NVeS9ipAKWIkfYKrI+ObQKtNGOaQfla3K++'
        b'qflgIXtfAo+CIjGVjoS4hfKE7RxQuRaZVSwH3lZgYJYY0DLTTctMXTAoYcGbSAOeo5ftTXgxU6GNbcJRBmxBOncXgiJk/tp8TF8mw+docTqSAY+wNWBvAZkN0JyEFM9U'
        b'7ornGicC6wRafHZzQHMKPEyXGVwXNbXSpmf8PCntQ0scWg9esIoDOjKzlU6oTNhasH/2ilBzl+5VLywpYPPAHaTccRMmc+CJF5pAJXvoHpKV4Qp7jZAiUSSDLnplHM4C'
        b'nQjLIP27KBPbtHpwxl7pjFJMde3UlXXjypDZ2InnARSJwEkk0zEmlvCWhheCsVfI3KGV3I0W12xlcnMzPLTe0ZfucJCHArTzYLk3mg03VGI+OGamzn/+hUWg6u4xJDYN'
        b'HIUnjdbmgttKBbE9GUhftKEJdADFRBBWgKb8KUEgjWM1FiKCdWQFhiJre1zDzQBcoGfjJmjCgqNeT7O6QDObTbnZrAA3OJvBwRiiov0CYZViO1KAbFCFQV+F9QoiOlJQ'
        b'naSqqfsF7eeAqutmwRtYb80j9g52S2ZqHFpkenFmC3glx4EFLzI20Ha7AbZsQtAG6Uob1NdjGCidjyGcC9kF+56Tv3PPyZ85KPXJ44Ame3CHFv06iUyhg01wXyBGPMdA'
        b'Ieiku1QEjtrOXHT4Sa0DWSFI515IAA1EIOFBcGWFuuELLwpkZz68zNZAUO+c0hvXfD5hz8u6Sd6wEfqNCQ4FvfMoOTyaD67yYHXoPjJyyaIQhDCwkYDXIzBKbUCAr085'
        b'F1d5ZDe8/YKiDRFxKB/Q4QsrOKDdypHGMMfmIw4OCjHAakGW7jSy1QHgMuGfMSgSzp78mWueKI+Qvd6wlYOUT2mY0pPg9636qnYRvO5Ul5uecRYaj9bm+YwVHA1/WAlL'
        b'aIVWD2uSonA7SJxnCudSeGvKzCaACg1b0LiEjH0TNlBo9BgRRRjjXrfAIRfCfSQ7N1Gx2UYA17IFVhH97w0uI9WILB8NrdqRwr8NB7UxtirKwfilE1ltWm8illzXf14O'
        b'veihW8CLe1Dt8AK4BTuJwo4Jw2iQOEm8fciigDO7c4j5XIWEp2WG3gTFyDlT2xJLcBBLfh+opbHZ8dW6cDAP1bEJgVckzlUIwdJyhTy4c6Btlu6aKYTgiEcSC15H3akk'
        b'suwOD4AmVBXGX9djsRqoXr5GOYfgso1Z06PaHUvXw8R27SpaWcnwNlmy4aAq/8VF2EcPvh+pjA40+s3IKBFBug7qVyAVy8Ad78HiWItmqISMXwkuIjRNr51udU3gknrx'
        b'ZKxlwUuwZjGN+MvRAE6iijgY/OzHTihqyIpIF2wHPeD6ywxQ3wxIsANe8YQtHHB8qR9t4ZXIOR6ElxEfrGAH9jua4S0zWsEd3zbN0L7pMXbNqA5NcInnGg6odl9JK5zm'
        b'cIDcIi00QyYFGL93gCPgLC0uQzsXz9aueNVNadddoD0+WmPBUrUZPxyxevby6n2eN+5x3uAOB1QZcsiMmsDOaNQydrquIuYiRN/pZ0MGYgfatGbVxUxVta6LGh/y1QPF'
        b'8xmgdYkn6OXHahvQuPaMddgLqE6tpMSwDPax4FVj5GzhuIx3ZNw/tctqI1QIu5Sc3M3xZB4lGFsjP4dwvR37JcfgVaRYCBSu2bTgRcE6TwvWNTBgw4IDVsjVJDy9apv3'
        b'Uuuuws13ogvY2ljSlTigJhalCnhY4PsysPNyKi6exi1dqIrKFxdyD91kH2wJY8E+/hbaRnogn/55Az09i7A1NN5Fw88QnCaLPtweXBLkY7TbhdwMpIjqIlTu18F9AsE2'
        b'Nra5hfAcglKgHzk/ePhyRfQszDBrNSBhOrOBBe84bCQDyvIHxwTb0IhSXHFIoXG+ttILvQ6FbQkvn28wuB75Eoc3w871lHwL5hqGlMeSafRRBE6FvNQJ4YBGJ30VcuxB'
        b'2Ap0pJIlFwM7+S84ENNglsbgKHsdqOPkwwFwnHa4SjThFYE2Nk1dAfAm4o0gmlaRnrBPoI3cPjHq920KdKeDelrtnQC3QbUAmXUEdxdj5/cEKPYmsr3UXvByzDndA38D'
        b'T3gCGTUE8o7T1Q368VBlqCFdZAiH0EKB5ZC2arA4LnKa/bPNmhs4jJUJJ28+I56n4QuPb6ansgse5ws0SZBkBx7OWXDVhsjKcgVoeAFYgx5OSp4cTUQM5WXCAeVoPk7R'
        b'9dTHGQuUSCSy6BXRiFyjIwRdbNKdjfFUIkG7aWAgzZrNDod1RJYDwC1w8WUM6aUXRKlXNpsHD5rRPkRNJuwRKLBtq47GK+K41JbIIMT48cxLlj+9rBa+4sSCt1ZYEWYK'
        b'YOMcBA3wUkYmtAXeQmwI30Rr5A5txNoXFMNsDYpE+rwnrOOAYyExSl9c6hrYb4hqrAPFKp8d9KrWAigm3j8bDK4CvdqgbDW1ZhMXcasO7BezSW+0wWV9WBYdCctZFAve'
        b'Zhhng9aUHDLazaAP1EfB0mguxXzFVcxwz4BlJD6wg82LgpXusMJZjOxpCehmU0JdlhEYtKDnZVAI25xjXcPZFHsJg7ETQfSztrGpaKKm/nDQGsFb9tNt6CGQq94B2U8l'
        b'MhI1EpmJvESKxOtZiQJvTbzTlMXLZa/kzojQcyyoxBkR+0TOrFg8ezGHROhfeDsVoc8QMyVX0Orgh+AdILznQ3aBROk5ctE2SZYsTZa/043PD8iVyCVbRbIUSXaAaFWm'
        b'lM6UnyNKkdJ7R9I0N3WmFFlqgCgiXZQh2ybNdqFzqvaURBL5VH6RLBvvEvFF6C81JztfuiMf72NJJamZohyUIJ+qMDVHmZ0v3zmz0nx1F2SKf1NfPt76UtXgJopRKvJx'
        b'n/EwV8a5env6+oqCo+PDg0VeqoJp0ql2FdJcCWnUCT85iaSIIUpJvpTsmCUnr5IrpcnJs/pC16HqD80dwkRV30QrZdkZWVLRMqU8RxQv2blVmp2vEAXLpRLUplyar5Rn'
        b'KwKmahblZE9NgQt6GybJUpDXmDnbZQrU0VmbK2zqxc0V7TB6wZ6JzQZlyOGEFRS1jlqHEOXJ61/iAl/izLHEx1oHi7aQoDaCWSlzQDMTIT68NDJgE7xCAsCwloJnQTVC'
        b'jEMmtEY+qZ2iip03Utk2KKk2I0COt25iYwO+ZGKrxJ+q3xWhtV5vD2zU6qh0pxRDcEusQ1ZKGLgEK9RNwxpP0Azu+Kqi/QBvOOB4OmygRAtBJezLo1fXBXgtRBVOp5Yv'
        b'QZi0A1ylU05pI6hNoulIHWr7I7t7M5Z0NwocoehQ+nlqIxpJkwfsp8dRvgFeF+TiVrooZ7TeG3fQQZhV8KyeIA+/76eksBC0hsBDZDAR9mCADr7zKC/YBfrcnEiBtfCG'
        b'DhxUYKWGMOYRBqidm0H3qo0Pa+iwPGJjoCGoAq2+dONHrXl0TB6epFZ4gfogMKCy9QW+dEQe+Q82ONZ7ATaTlEwN2CwgTEEm7RAO1VeBM+otlQZDOEgG2UqtscRTkkl6'
        b'DGq5MsV2DTJVoN4LVLnpi1m0dDRngD71BINzAaBUw5S2dz3xWVN1gWJwElTD1gJ6bwQMOE/VdscdVK2EN8VM4vtsggdh6ZRUwEpkQKuRUbhM+rcX9oIeelMFuSHwqhi0'
        b'zAmS5Tx+j6EwR6z5zXcH99Z6xkEP3cL2Ov8+g+q1S06ePrlaw/gN4dZPNPpFc9r9nM6Erz6buOn6txo//M4/9q9Dmq9GGT7e/fjWh39cve/QHwxaVn7E0Pm8Le3t4YWv'
        b'/3gt0Ey60dnIuGn/t9eeGGa8KWZUfjU0PGb/3rXuR1cvhyz/a+8bT4dOX1gbPvdr771j0ee+fDXCcIXiL9C7+4O7K0r3fX5ho+efHj195YzFO9aFP5Yk7bPRfOw8uLnv'
        b'pMezVy6V/vlNp9cKRrx3rfvNvk2vux04+0etmLffeXSzQFu3Nnjp+7Y9Grw91dXbec8KDN4tCjicHLLm+GaHc8EP23qjjhYNzi8If6sh8vCD/m3hjq0hf9PsuvetVpE/'
        b'nCdvMTS6sDAoZfONv07ox11Mlf9NUOrj67WyUsyZxFOyazHsd3Z1DHdlUlzQwoRX0lxhZegk2TIszfUSRMFycYzS1QmWujMpI3CEnQWLeQz/Sey/+/JgDSjbDgfy0TK6'
        b'qkTwtUHIQy7XJWTJTcAACzRHgp5JPIVe8KoF3nV2cnVjoHYOMhEO8E4Gtyfx5qICmeseZ7cIFyexG6xygSUUZSpig5KcV5B1viTWHmc6iuUYZf5PLgptdMHaVLRf/Tdu'
        b'FJguz9klzRal0wcc3LA5WjTOJwo3CRNyLJpY7Sg2ImH6YT/1bD2HMjRt8unwORtwIqAzcNTC/ZGJ5QSTpWX1yGfRUP6IT+g9Xc9qdgdvgkvpGtbvGdWx6+LdFN5d9cA/'
        b'ctQxEmV+rKP/yETUYdCR8dDE7b6J2yML0ZixWaOsRtbB7AgZMXasZo0ZmBwLHDVwOLe8P/R8zNDKUZclKNczLmVqM2Zt22HXllm9/LGO8Zi5bbtrs2ure7UGKtG4uGZx'
        b'h89DA8f7Bo5jJtYTFMMhnjFJMUzjGZ/Y2E9w8APqlLF5Y1JNUseqh0ZO942cUMbheb6jJr6PUBYWZer3sZHZc+kdW0ZNPFXJXh+bWbXbNNt0mTw087xv5ol69VjHoInd'
        b'ETtq6oXGNqZrWJ1wlNfkc1Snw75DcVr8QNe5OPiRgX3HihEDhy6fewbuw0L3HyYXU4bWqGtaVuOIeSx0/0mBt/JPCpZ5UK97CJYtZr2+iIGu5yixcJyNZ2KchWDAuIbK'
        b'8I6zsQUd10hKkiuzk5LGBUlJqVlSSbYyF73513IgRJdk9KcWBDnWZWSeyaUd58FR8Z/RZO9mMxjzvqPQ5RNtk7It+wUTTA7D8JFAv2zBJ2ydwzFjPJ1HPIMfnnAojq6a'
        b'+kmBjx8c47pQPQI/FtKIZHu+BLTZRiEwCMtiYWVcBIfSzmWx4/zhYdiitMJrrQcWZUZFxxL4hzz/SmcGJVjPhH3gImgg6tZalqrGjOnwMsMdVjqkqo8QzbDW7KebMfRj'
        b'0tCPAD8KAT+uN1sF91grZ4C3XDaCe6wZcI89C9ixFrMJ3Hvh7Sy494jAPQQ6MJKZwnv4UI9EfWSHHPbBWIgAN0kqmUZRtnJrCoZlfAwAnbYgjJVDlp6T+qQRRmNyaZ5S'
        b'JqfhT65UjnDkVhqDqc8bufHj1AAGNeiUgGqWbZUuk8tz5E6kAglKQWiSHyrNlUtTUS/TXERKlFldgSiV9J0seEex+uzTdHdEWbIUuQShPf4aWVYWxmBy6dacbTRC3CaV'
        b'K3Ad/tOgFg8Wj5UGts9zYAoNqrhA53qeJTOhb1iWJEMko3uVmiOXSxW5Odlp+AwVRsCKzBxlVhrdKwz4ULckCtF2aVbWTAy4TIZ5NA0tERqXiLxc85W5CD6qwCRhLRq9'
        b'I87hgisXP4cIOS9BhBrKHCzg12GTuRYsDuaD/R5CNtyP4FTPCnhgcQRozZaBLnt95BsdQo5v44JY2GkF6kFtlgZsgCdBRwi8JMXnQLia8Pbuza7gCuyF/aDSEh7OjwKN'
        b'wQi7DYFLYaAEXmUxwW0TeCgQ9saSozHIrzy9AjloVWJXlIw8JnieFxcdEcOgLBaz98JTkrBVMusv3VmKnSjzV86vD0pkybx0QXLaXSpY6BntcUWzfu7vdN/Ufe2Lt1fd'
        b'1YXadYJUXgo/xVdSNDF64iSj9MtaodBryTUqNrrus6ZoU8nnnIuHPf9wcc67/I9fX2Xzrv67lq8xB09YftEw50RyYlOM2EXUCgrLm+vNgOlRM/8N1Kk12jm2DLEGMbSg'
        b'CPbucI5zgaUsir0aVHowwDXJrkkcMfVBvvIxRYSrY2RMLDJ/SEtUCXBGZDHLozSoENgC7oB6jWU+6ydFFDnB0QjaUGIlrHKGJXGwMjwGVnIpk9C1+9hOPp7EeCPedIOL'
        b'UXGuES5iMZOaCw8JwCUmvIltLcmwKBYOwjIxwuUq5sVFMyidFazVObCBbuYOKFw1k7sJoHqau3O20JlKQbNhlFtkjEsEqECm/xCson1ec3CJna2zR6zxn9hmDdo2T6nj'
        b'ccGMJSmfq7bBMorY4IkwDUrLqCqmJAbZOAv3Dz2WTiITEsr4TGj1oYF5U0DH3n7pQ4PA+waBY7rmD3Xt7unadQSP6s4bE7tW8/HdzO6hmfs9M/d+3pDDXZ8Rs/CSyOJQ'
        b'ZJbHTCyqdw3r2iJjWhz1FAu8HENMscY4T72mxzVUK1WOo4dy7LXLLV4cjMq+0LZlrvoyqrYtf0O2RcplMOzRABj2v8K2PMW2pYE7jzoj8GQpg/AE1MH98LY6SjGYNh2o'
        b'OAePgsPIqSgHHS6sTVE+oDIP9IIz4BafSoG1WrBNSh/v8QeVmwTbtJHngdbjAXiVwvvZ2wm43g0rOYJteTipGPYm4J3rZjM6jl4Nu3UU8IqOF5tiwlqGJWwxBvWaxFLB'
        b'KskChZecSTFy4MlAClwtcKHR/01ZgWDbNi6qrRCt8psUbIEnjJCFJAH1q/C0VG3gQAdoRBauDwzS1rMOeYwHp0Ij/eZTkZGuTcR5sIVXwZAzMp4MigkqC8SMkL25s4wj'
        b'T20c5dR0XAQZR04iHRnBpxiZiXxv3pSR5P4vGsnDyEhGM2fERIjifnlEhGh8bBFwlpfHQ/5J+AIX+D+NXqRmkSYV0vwX4xXPNY7HlpOaqkTGKjuV7oQ6YrEsPlgUgrCa'
        b'HBuw0P/4tC+pg5z4ndEHCWagkhxXdloZssrJBd1CQ/EtJC7BE91RN5yWei0lCSEhTi6klhn9lWQpcl4aX8EDILzKpaMqqKY0bD935iKG4EpW5+L82/zc/N12kBpfil+2'
        b'S2YDGAw7cLWkipxcGr7830RqNMNon793LjwD6hAALaPoUE0bKCRuNTwLTiCTrDpNyuTBagOGJrzKleMg4irke+viTJd91i41xPu/npQnKPRVYpgOa7d7IetS5Y3a9aK8'
        b'ouxUmZkhW8ExbVVmWL6YaAMzcJapjYwa3uePp+JBDTgr05i3hqX4EiVuGWs4uiJIADwMb9r/vVb74KFD67vzh1+9eOjk4pN/WOBfH1v46anW84s/OiVL3bJkwtX2m68/'
        b'ulWlmGQWbmjqenaXH1V9lfHkWPNXrD+cLwhf8V7MG99mtBSsGNvHsAga51VEplW/cmYy68HGP5UYuLOPvXXj2cSq6PNLeiY2fX12+cO6g58IV+8ZcrrVltd3UnKn9vIY'
        b'SF72xU9vJS26yQ/b/I8Vn428J7tkZpaZ5XG0f2GEVlKpbftrNhY/dd8S6EtHf1n/OMZP8tXmxItpf1cuXu2TMGr+ecOWel+Lju8vZ5ee+ivT7LOiuvDc1LrPteJ2O37y'
        b'+ImYS4yu/gZQoXapk22nnWoerHKdJHr1jAxcov1xERwkLrkruOAzaYaZBU8hTViGTC0+/1PkT3F9mNoIHlVPEg/iCHIViqJgRRTxosGNMOxI63iwMsCJ/Emyn3oUWfHm'
        b'aYcdXlwE2oXamshRhbdYlhTYT5oBN4M01L46PMgm7ro3aAc9Ys1f53FjOZrytmm7rkm71kjJyb3UVv1n2qo/C+VRugYTTK6e7RMeZePUZTdi7Va9/AkXuYpNqR3eDw0c'
        b'7hs49GsMsa4KLwmR4/lEhDzxZ1aUqQVKXnl23Yl1nRtGrT1Qyscmcx6aON4zcewyeGjiet/EFb17ZGBcrajzb5LXL+pI7bI9nd7POrV1KORO9LXot4weBsbdD4zDjjjK'
        b'lXfUt2ndqMG8LrsuSe+8/ohRpyDs5iJkoejwbtvR5Xch6FzQ+cWjNgG4gLlVU2qbI3bAzY9tHkWet4V1+4LmBR0JXQYjFq6XzIeWP/AMvWcROmwY+sjA5IdJB8p0DvJ8'
        b'9WzHLUTI89WzpT3fMl6oBfWahSDUifWamIGuNPIQ0DADL9dxFlLALwMcL+W9YBqETDu5XurLtzOBiESDwbBBXWLY/Font4XrRHUL5rPEDKJQ+AiYHp+55wFqGaCVJ571'
        b'PcGUm5qGLTGLfE/ARlaY481S2V7GStb/6hcDzF39/ARaw/4TF4pW9lLamBL/yI2Y4PScrKyc7SgXn7aYMuzfyqUihTI3N0eO/MgAUegyF1HwKhdRSDgy4f9DmzDt0P5b'
        b'5c5V2iNiThA8iX0EZ6RRYEn0CtifL4eXWJQFuGQFuthzENzrVC6jdcOlOfiDhTXh0zEI18RwF1ywPCIalkasDodl7gnhNMYCN0LEoHtVvCuX0gA3tMBNBPPPKz2wcri6'
        b'BXSSmnKRFknEhZDGMbNHc72MD47Hgsp9fNANC6kksF9DsiP+euyXWFJiZY6S7WxFK3qceF1jUJKN/LDVabx0b0kaxVLyXq9+D94VQYTopMm8lP3n3koWpi9/f8V74G78'
        b'a2tPWb6hC9krt2rWR+lxW+/y/Q54lgcfqWBo635uO8lYHW67it3vnbzfY17TbWaDh/HQlsJ7G98xfLfooz6PBlPtIecD/suoHgM34zcO7trxFbPa6jdLLorS01b4GITe'
        b'i1myukJmnSGgdBeaXJq7RswhmtQa3AAXpwKfoHfetJqWcCcx4+1BpcOMwOdU0HMHuEPHPUG3cBLv4i43mYe9LHd4EZa7wuIIWBGD2BsRk0cHVMEAHKKiwHkN0A+rwdAk'
        b'HfC/4IvcNgYFmmAvcxsjeBm8TdT3GjZX3aaOXEsHDgjztLiUJSp62Z7NBPthr5j3H+tmPCnqaCitmjUypPlEMQepFXMXrZifxGpiFZz20MDuvoHdh8aiDusRY49hXY9H'
        b'3kFDaSPeIfeEHsXLm3aM6RgfyxrVcfrQWDzstGJ41YYHThtGjDcO6278UN+6afsDfYeH+s739J27wkf05xeHPDYwRnUN2y4cSntgu3TEOGRYN2RMR79+66gOasSuI+QB'
        b'joROIPVvUhw5waH0jaoTjpocixnVE5PkLubp5Q+MXXCw1Lg4Uo63p2mdyZVjZ+Ofakq8lUIlTw+cjJdcbJCeUmA18iMO/fEYDP1fqxDruHZUp8CN9XKNl0LRgTla43kz'
        b'/0/0XTrSd7v4K3OzZPnY0ZhWaQiAI2WD36bLJRlkpxCpLLVilIh8XhoM4juGxK2OXZWwDqu4ZSFRK1fHuIhQbVFJIXFE94WQ9KTY1TFLlyWIZ2su1ks0FycgVo5DsLFK'
        b'fzwZsdRMBRaudvG62bBWDM7xQfNOWqvgzbV9FGiFRXwebOAT9QdPgz7k+KLyEbbPq0Ba/3Uny8aDAVOxEcuFr82gZDPSO9opwzUp+w8xizyKkudFhXGLDK25XLMi07Cm'
        b'aN1Ozfq2V03fNSw66by/mcFie8NRk/THHkWe3SHLRu7FSJc2mb9herdUVqlZn5j+cbQGldHJ/0vOYjFrEn95iBTfJVA4c8tEg61SHOA07JjEIjkPofFzCMQhf72XADka'
        b'xZ1D4Asnw+PGsDHKPQsWotKujlxK05SJYHo3OC1mv3Qhs8lCVi9iPnLVFKqwSYh6HSfQ63hijyZlYtHkdTSzeDlaq02yUR0HsgIXjxgvGdZdMmZo1ZTxwHDeQ0OXe4Yu'
        b'XatGDL2Klz02MJ2x4scMTBsDawLrFg0LbWesOM4/XXEKjnqx0WstRH3xm7HWvt+i+evWGomC1HLnUCcFrhh8YGEAXaAR9NDoAwetQDW47g5K40hEwbyAnRkLh/4fL8u3'
        b'ZsEQEhDOlmwl3qt6oeKN/Fwp8noxLEGohMYiEdmiVIkCZ+Srw+v5M+GJ6P8lPHnZImfRZ1aPbtaDgwp4SQkKgzgUEx5nzIE9sFp25u/aDAUWn6ZfOgYld77FqzIeoQEf'
        b'hAYOibhWYq5/fPrH71JU8BDzi54faSFjzpAqLNZqkRcSu4WYiXkpX64WemNa6J8k8ylDm6bdIwbOXWEPDLyHhd4zBXdcgJdKUo6cWL7/QICXqy/hMwU4hs9gmP0KAZaH'
        b'ooIvl8Z0LI1slTTi8NT0zs3/OjCW7Mc7N9MmIE1GJlgi3ynaLsvPnI7XyHOU+VjOZNnYLEjIpsks0Mx/meCKZn3YPRXqmSnPohnyzP+18hy8TSLLkqQgm7VFulMRwOe7'
        b'ooZWBahCTEh8ZfmiVXJJtiJdKsdpoaGqNLorolBpCsqBDByyW64iHDH6Z+meLiKntKndIyecfanX0pfmRu/FpCMh6o5I5GlTAS+UEhscsyyARLLI6v/3WF+DfM9cHG5K'
        b'IQDu4WH9c8apjB0UfTyuApSAqpkWNFcbXsPAPD7BNZFJucciO+oWRII2rjZ6K6ejQKDYQY7PuCmxdMBWcEWXgHr8NbMr3oGIWqOC9gTYRyID1A4uwcJIaie4g4xZWo7M'
        b'Ivw2R3EUlY5e0ENvrKzeMxctYk+8iP2zy8RCoXijUOglfPXdt7w4wtuRr7pwhK9GlwolQo8VGPK7Ce/r0YBfmDosSd3PavpJ2LGD8mZxiz/TTvGSHHxkCJkGOslvrirr'
        b'/6hFL/uOy1v7dh4MONSkPOWxafVd0zeKRxxcXnXx3wNM75bIjqgt8gdVhn8s+DuC8nghzw+OnHWCAVwIoO2xz1IS64BHWODOzIMJ4ADcz/ReFE3b8zuwwRaU6WyDV0DJ'
        b'9jxhHv6+mE1puzCRhzBoNokVxAJwaiGC6+DmPgaF0brQi8RxYJ2xBw5YIxhCsX0Z1rAS3PSENxA4/de4HM/7rI0QrN1Uy08er1ZuVSrlFoY8F4PqhSM6Nh1zRnXsPzG2'
        b'atoyYuxUw/rY2LaaRU4ZNO6r3fehuf3wXL8huwdzg0bMFw0bLhrTN2oU14iblnawRvTti0M+NLJu3FSzqcN7xMjhoVHwsFFwzwIc5RgyGEq4ZTLiHFwc9tjAjICFwKHd'
        b'D2wjR4yjhnWjxgzMGhfWLKwLGhaKZmhVDXk49S8A+IxdkhkjJYMjl1UMVXACw3Ap1qx4l+TXqFeCxeu59tQpgTvGB9gWrIGdsMQ5nJwuYfsxNGAv6CtwTmXOWHwcauYO'
        b'OhtvEpD9c/qHDihvjkoPM2f9pAHLYpbunblRgDQuczGL6OEX3s7cQd91hh+dI0lTiLZKcnPRRCtozZmWs1WqyJelTm0ok3OC5Jc0pjRrugypP0WuNFWWLpOm8VN2ipxy'
        b'JfmZTiRK7oTPRMj/5TlDWbYsXybJEmWh9pG9V3WAn0/U6nbVdneuUp6B9x9mqSqNl6gqAX1i/4ofuE1YHR8OS+JcE2Ex/qmEcJ4U9MJiF7TQljM0/Fwo+jAs7ALXnZ3A'
        b'wEoGxVhPwbOwLUiJpUakDVCxCLIf6s2meKAMdIDjzEhXcB5NKflRgkPwtAYOeMLKOKKzNCg92K8NbrHCYYVZLNF63uCg20oupYQHKXvktpdtUX0KuQgewKoQ3gQXsDr0'
        b'AsfoL1HPgGMkvjGtUOGAzDwfXEnAwRAneJyNBtMDTpMgucyp6j5HEYbk9YPv7fYmxEVBD8OCiJZLlzlHF1hu7g0ZPhQSZGj57l8mPQqrl16BY24hH23lpa5ZXPmDOOa6'
        b'r6vWVoXmN3//xx9vLRqxCWdpf/9myaYoyP5rztWdf/RmD+1f4KrL5L9mEqnzU6lt9d2DgX/cbHcpdMPNuVHh8je49rkPv/faa2+5t3ajbZHZp/u8j2u4rvf/rvQP57Mb'
        b'An2+Ccr6/HXRE72bPztx5vy+MqL1xtcWR45vi/8h1cI9c2+t88l7BnNPmbalH7Hi/mB9dp/NqXtrd8DmBP+3f3b8ZvyrZaK1B5+WTwb1PTn0SeyThZc3Xa/VXjv3wKOe'
        b'U8Di2NE2rfPvPhnd1vgVo/zGwrbIP4V9NK+AWrQR3MwY6l3oGDTq9rX3w6cnE763Pz/vsxWDKU+O308acHn42aLG3L5P+F//psDqLz/25AlrIjt/Z3rrVmU4e8sfCn5m'
        b'mTC8dXVzxTqTqs/2jxtKYdX0akVLFZyio9y3YSnogGUuscTv41A8WAYG4DnmXlgdRHakwVF4GXbN1PqwEh5XuWHGcGiSaBt3vySpc2RMNINi2zJAmy+smKR/Z6Bxs7Ob'
        b'GJa6IL8M9DDhne3eHLtJfNhgIRsMOLuh2S/BIonFzRX2redSJuAKOxxehzUkMgTPU+nPRYb8kCBNn4gDPZvIiThkusvykORGxLgwKa4GE3ktl3hWoIEYHngCoCZmHomT'
        b'wl5yKu4VeBtcJaYrE3avVvUHW65KJqyBA65x4BrhoRs4AGpnnbjba+OtFUx4CIoS4AHnWNeIiJgoF1ghhhdBLYMyhjfZXsv2Eh6abfSauU0g1NYEbVaqbQLQCY4SXuGv'
        b'+kCDcwQoi3XF+64tjJhF4DZ9+OAisqPVzmQO0LLhwRvgUiYT1MAieFys9T8/y6dFqaJX6uN8tLHUxlosaUpbylPU9nIBfXhvIldAGRo3+tX4NS6qWdRhT28pELPmO2Ls'
        b'N6zr90jPqDqtKbTL/6GezwM9nyHmmIlZ4/aa7XU7q9nPWJT+/I8NTRsjayLroh8aOt8zdB4xdC1e9icdww91LR/qzrmnO2dU1/4DU6tq9piJReOuml11e6rZj5HTnd9e'
        b'0FzQpXho433fxvuRoeWYyP4s/wS/U1ijVc1Tb03k1QeNmVu1i5vFHUu7WCPmLjUhj4xMmwzq1nbo179CjLjvkMGDuYEj5kHDhkFTWw8fGoro3nQt708YMfSvZoxZ21Y7'
        b'1gmemFBm1kjatEweCi3vCS1HhdaPLRxQgXniHpf+7Q+cFj90CrvnFDbiFD4yL6Ke3+Q3omv3lEVZOj5zQGNFPBjW8/mJnJh7laEXpst5Q1cQZqtJW3neOBtbmnEOMTL/'
        b'xtpjg5w8y9ynTF3U5v4nvBchQJb+ya8093KsuWdZ8qnt/lxsyTVUlpyDbPn0TxZRU5v9//v2vEplz1/wff6Z4RZNG27+f2W4Z7XC/5eG+2W/mWREvp6LAIWwa8pwgz4w'
        b'OG28Z5pu2ADK6Y8Mz6KVfsrZiUHBo9G09W6Fl8m3LDawBdTT9ttnodqCMyP9oNp6r0SOCjLdFdGgb4YBJ9bbAdbHBsR+SZ/0x/tVdkJ4WwAryJEn5JVUreQhSL4iHJsA'
        b'ZMcP0psXsDQGacLUvbyN8LolfUL9KDgFToJBrhR5ToFUYDpspz/W63NBNmO2kVeZ+E2gQWXlQTkcJCdTCsDBtXBQsR5egpeUqjDGblhFH7U/YeiNz87EbMenZ5D2nw8O'
        b'0OdjutD/ruOzM3E78ekZfI7+GLxBb7wfsgLdCngFFi9XH58xhhcgfd7eHPZb4cMzYGAHxcjBX1BWwWukLW/raHJ6BgziAzT4o99Od+LDiZnKCNxki8UyBRkIvEKCLpe1'
        b'KVC4TYsPB/O3reZt00YmYRC0wVvgEKiGzaAoF1SCOlBjAGq5Gdhs7tcH18AAuEVvGfWCFlD2XH3btOKXTVUXDPo3bYQdWRnwjijEHx5BM1isGQEOeVOgvkAf9MfB/WIm'
        b'8V0fh+oj9EWFf6eVbJm4by1FXob5mWGHVndXevKen4w3UGKO6seiwB1wG/M0e7mKp/bwOmFNDDwBBzBL965SsRR2yZRky3oIdMM6xFJwElZM87Tan56kY7s0MEvt5qg4'
        b'uh+ofn3qmFE6Zik4CI+reXodtMhcNr7PVPQhveSxjbN31Tux+w3AEsNbIyb1V+KXbDTt19dys3+iV67/4Z+5MS0yr35Rvyfj0zO2ttkf/eS6r/DJ4h+MvxneFjA8HOvV'
        b'9t61Z8f+FtlemqTrs+etRbdbbgkqd9sHbHrDT2HRoWkQdLGjeq1LeO5omE5k19IHR5q2LklP6+15YDaZUqVr+kNhT8NdzQc//Pl1oXV5SY71lWe9lm6F108EFMan8h/c'
        b'cDhXKHB/VvyX6Nbavj+UNOzqa1GYpm62eXbtN84+Nzmmm+IrkoXWNxfMOwZO1e6ID+luaR39/tbF3t7WtT9+B9dbe3AUP3z0ebWF55vLnp0cW296/mu/gUWXql/7rsRq'
        b'/W/XPD7fPpwe5nZHb3T8bmjYpfE3R3bvzYktffcL89qrb7W39FS/GRcVzPlTd6n5669FZa5jens3ufYncBXsdGn/wN2v9n41Hn4Dlmt/DRdTv/+g4/cNAY1jqUcaHvFj'
        b'et+8+MWyCu97pYGt4iqfOKsfrbeIHx3R7j1xX+v4bzoryoXFX+ypG9yx0PJG97fNR/944V5665eb6r+csNu18q+W733s9Hdvx42SkpHfL7W6ffztv6R3XEmOePf1xX9i'
        b'rzB/ukUsIMjKD7anOYcj4WiYho/I/T5I4utIqV0PpOEj/xU1gGTuBYP+NDQ6pAfvzP7mwRccINAx3XKSfA/TBc9bOkfuFE1hxyR4jg7d30C66JAzOLJzBoD0Rmqgl+BH'
        b'XdC49jn8yKVWwToaP54HjQRUMVfAQ86w2Xf6iwxXA1hLKsjzhwcETnj7EB7A5ad6aAMG2fACYx4NHQcQnCuZDlqAHj9hnipm4Q76yBYjc6Fp1B7YMA0+eVqb6KMfvexc'
        b'Z3gYVM3Ela6ghCU2+R+Dtv8C5pnMgHkz0d4U4NMigE+RmpWEf0hSrlDjvQdqvCf8v8B7E0yWiXbx8gkepadfHDxmimBYO7+Jj0CfoVET4+gyhL8MTBoDagLqAh8azEWu'
        b'Fv70we99A68xS9uOOU0R1cseGZo90aTM7CaFlIndsF3giHHQsG4QwZFmjTo1OqO6ti9BkRg3+gZc3Xxx812DwZx7ut7VrCbvjlX9LNXnI3VbqlkqLNnhN2rg9AJi/NjQ'
        b'vCm0PbI5sjV6zNCs2ecEqyOkk9e66DnCvDn0hEHHqk6z1rh/nm1CS2OOfr1mk12d9hM9BDOfzKFMLY9FNBRM9aFJ3oCP2sw5nXHJ7P15AR9azetQtL1SHfaB7bImzpij'
        b'W6/WQ8eEYceEm2Z3ve/KX/d7sCDqrWUPFiQ0cVu1EAidE8Z4qkGZOjxbzngRi4Y7cN5yEIT7a6qPyWCEI8dHSv7TEzIzj8lMiRUNTRXqS+0saCpEqHTyv4lENXPF1DmB'
        b'D4ucWd8GGgtmfAjiChucwTlHBmW/eCvo5CxYnkaCH3AgA/biA62wJsrNao4bi+LDRia4tQXcokfMio0NEzPCxMzYMNnfT8WxFBUsinr9cPzRo0d2fxBqWRSXWPQs8tPX'
        b'8o69ltfq5pe95Wps65X4pfy5c5vi1nToMvmF83T7Zfs9rndIv7n17Pe7v/mlPG5NVIzzj5+c+/nmN+uuP/Z/u/ZmkIz722ozX7v00fLmPO+8jV999RbPrs0gbKBH8/Jv'
        b'fwhrPOzv7x6alJoeZrircHBB3vXSD85+Kv96yOy3zu+Uvpb0/fHu+CtO0Vu2pQ3uG+b3nq0Ca3Tf+X7y4LZdVUbvfbFVuUA3cVO+Q+frfQvPSjcGbYmw27DVoK/XPNdm'
        b'i76Z3KZVu31v7PdrcxLnfr5oHmf8N4sWXnA0/rv9koOZR2wY+va2+kV3xq6bmusVR8uKa01L6tgRtdr3I66Hl+bXWdfOu2Uf8lN4w2Qdwytcnlb8h7f5A7XCutVp89eF'
        b'vF+rPLXk/Tq9BHuLt8IGSurDm7PmbQgvLK/tTbMwa72/WTPrTe2vXtvpb3OjdNcmZ37W65xB8zfybIMOfJTPNrlnkqqzV3Pel47f3/fcGBn3idf10ndkdzs+q55ctDHY'
        b'IXdu22ur8zW+H2kb2vX+nxUV3Q8LZQGFW77Mfnf44bqn4Z/t2sWbF1Rm8UWg9rBf9yOjoZJFxQt2zf38S8mH0RcSnlxNPnDb6OpvN3+WePZBV16B1p8n/+of6v6p9k+x'
        b'Hy5z/yT7J+sPoy6sdk46+97VjvSHny3aFdr7uUfl8PK88kWVf/tSI/eg26dpnSOHdhT/zWLC45Ze1XDVp567DKzPtt+ty9eMuxd3/hvp/IVnnBYdyvjyTxOBt8zchzdM'
        b'zNm04mH2qt5/zHXevhG+M3ZozYTTK/AvO1g5n7rerNi6Q+ObT4NuVumU/iOv19hzzoNLf7N293tjaOzWmuK5v//rkW8T/tb+1io7+dI/PyhfKP/l8NPRL+qClrJD79w9'
        b'kuDusvvrP1/3jP/trkDF+q3Xn/6jNPyxx5tvn1tpVL6vs+yb28HfRXzSGfnOOf+fXRdKw8OkYW9IT44WxV1//WBB8ODDLVWXJwb44j3rZTdPTOg8fTrXZtHT985f3XnB'
        b'sP0D517O77p+5tx+bc0P5o9zXR8HbPrH0eDvS962bm44dOzHvredQra57kmSjWa8svaNqIB9/fKNZit+V8773RfLf/fDkMEvIwM/mH5W8H3phau739iwJnDT5lfdjwel'
        b'xL53YVvl9fdkjxwG3/2p9+3L3/u9HfV29uffd3+17eff2y8U/f2aYvedXySPz32fs0CU9rHllp+/7DtQ9TSlutOz3mDkvQLx+t/9w69l5I3JnqaHTIdfWG3soB8VaWId'
        b'Ymt5UdthGYIKDNAArvrjr1e7NOkYSaEZOPTc55VO+RhpmPqSUBKC60fgLWLxibmHLXNnW3xHhBkw4DGB3aBiRrDsAjgN+tbBKwSV+LM2RGHIUYpa2uYXw6EEoIIJTziA'
        b'yzRoKTTYFhXt5BbuAq7DM7gGQRYTnioAHfTnHY2wxg+Ugao4Em4DFaAK+WhcFhwA9VY7wQmCGlaCOleUXIo8lXIWxV7AALe1wcV58CQZJzMdgRsCRyxT6V0U9Q5KqXwS'
        b'/35dmvbyGREzK+vnPiGFN0A7QTYSJbz+XFSKS+kayXFQSg6b6SOuzSvSXnZIyt4FnmYz8Q8o0RHGQ65SBAIjYAXCYFxQBLpfYdqFi8lonK3BgHMkPqwVbcaKxfy6yIRt'
        b'sagkAYiNVsIo/OENygDLX4FtETjHBSaagpMeYvv/Aulw/8PL/x3Msp8Fs5ao/va/8EdjLl5SEkFdSfJDarj1Z2TlfsF4y4XSMppga2iaPNLRr/Yq295kW76nWdHh1SE5'
        b'Pb91V9eKYwUX7fvlQ7aXlUMrLu8YdHs19C19GD7qFf2hqXmTV5OkbX6rZkfkA1O3fpMHpv7DgbEPTGKHE1YNr058kLBm1GQNPoqiX5c9rEs+Rl3LmOBT+obVwUeNipdO'
        b'cCkjk8blNcsb42riOpaeXX5i+dm4E3GXwkfsg0YMFxVrjiEkiJOja6I7zLrCRgy9izVJoWLNj03MioUfoyf+hJDSMmnSGhMav3CZ0NM04xdrTZhyzfljQt0JFr7rG9N3'
        b'U0v6bj2Hvts70ncnN/ru4UPffQPoe+AS+r40jL6HR5P7x6heDr6jeskd1UvuqF5yR/WSO6qX3FG95I7qJXdUL7mjeskd1YvvaJxaehMa9JOBifrJzEr9ZGOnfporVj85'
        b'u6ufPOern/wWqp+CghnqxxDG8qnnCEaM6pmHm9Skn1CTqifUpOoJNal6Qk2qnlCTqifUpOoJNal6wk2qHkmTqmfSJHnm4yYF9BNqUvWEmsRPxdoThpSWbrXJmFCHvphP'
        b'aLDJlGrHMIzwnA7rz51g4Wc0D9XuExz8SFiHCA1C8GhCkxB8mhAQAgmO3rC+44QWobQJZT+hQyhdVZoeofTpYgaEMCRJrhNGhDIm1NwJE0KZ0hnNCGFOExaEsFTlsyKU'
        b'tYqyIZSIzmhLiDl0P57YEcqeTppLiHkkSTzhQChHVT/EhHJSdd+ZUC4qypVQbqpy7oTyUKV5EsqLbsCbED40MZ8Qvqp8foTyV/V4AaEC6IwLCRFIE0GEWKTq1WJCLWGo'
        b'KglmEHopQ1VNCE2Hquhvl9F0GEPV1eU0Ha6mI2g6Ul0+iqajGXTbMTQZqyLjaDJeRa6gyQQVuZImV6nI1TSZqCLX0ORaFbmOJteryA00uVHdr000/YoqOYkmk9XdlNB0'
        b'ippOpek0dXEpTaer2ZBB05k07Tkho+nNquq30GSWmqtbaTpblZxDk7kqMo8m5SpSQZP56raVNL1NlbydJneoyJ00uUvd8900vUeVvJcm9zFU011A00uYquzBTHq+maqe'
        b'htB0qDp9GU2HMdXzTdPhKvpJBE1HMklz9EInV/HUM3k9fUEvn6wjpZCR2MikLOzb3Zvd3zd3LoksDhkznfvQ1PmeqfP7pq41bOTtm1q1azVrdUhGTJ1rOU9YlJnbx4Zu'
        b'/UYPDH2Ll41Z2bSvb17fxRmxciuOqE4ti0Wev4UL0hB83UeautWpTYqukP60Uc2Fz5iemh5PKXxB7l4gvuhOsBGJZ5RkbrLrUPSzRzXnP2OaapriDL6qXIhE683ErHFz'
        b'zeZh21UjxquLBR9r6uAGVnbYdYX2G/UrhxLvLntr7rBz/KjmimdMMaqAEtO1JDBU1SAai66qZ6Oa5t8zDTVNcKKFKgcikT6YzvAdU0tzzswMiEQKie7uylFN2++YPE0f'
        b'nDZHlQGRSOtNZ3jGNNe0nZkBkUhBTDfxjGmpGcl4QuHrzJYwjdTFzIzumisZkxS+zsyI6SdolWiaVMtxcKdxT82ejoiughGTxaO8JY94RtUpjRk1GY1ZNVkdC7pkI8b+'
        b'7/MW/DCxUouhGcF4pG9zSjjsGjYiWj6iHz4sDKe/1ykXxjOp5mBvdB1mGsQbqb7XMRxnImD0a0IQ/wVew25F8ozfMZmFzwgqIxccTlTgc+34HI2YwdB9RqHL9/jyayMY'
        b'J7le1IAgiCU78Xk4R1GA3ny8+NlgTVxaZFpsWkTa1uTiVF7KZJpjMi+Vl5x+l/J08WjQtEtZdtgtWZgqTH5zldlrh081aC59JyQ64+0M7kjPjy7JLa7t88vF5a7lQeXe'
        b'0R7RjtH+0fbRLtFzyhdEO5XPjXaL9owWlz9Y61G87pjtEbt2cVNE84FBDuXtZPi37gyxBvnlGDfYzSH/MZM47HtEaWC3AMHxASbsWguvkyygbPXGqDhXhM874EWcM86V'
        b'SenBmyxwArSzSZYt4CgsxU4OrEJOkqVVjMrN0WdZ74SH6KjvbVdQFBUR4xSjEehNcdlM3jIwSM5/JSnwNlRLmjuXYqykYKfbCrpAE7gMepzjwaFIDsWIQrQeKKL9IXAE'
        b'1DnTn/c7wiHUbVRUJ5O1OQNeEM/9N47B//9B2P9YKucSL+LlnsPL3Qi8hYlWS7najYikyK+uPDWnOAZjWoYPtazvaVkf2zGi5bg/bIzNPxJ9IHpYz/aU/yjb5QO2Fvm/'
        b'wTN2HpcT8IzC1+/IdSJdixIa7o+bcSDNdpyVJc0eZ+Ovd8c55DOHcXaWTJE/zsZHXsfZObkomaXIl49zUnbmSxXj7JScnKxxliw7f5yTjtwddJNLsjNQaVl2rjJ/nJWa'
        b'KR9n5cjTxrnpsqx8KSK2SnLHWbtkueMciSJVJhtnZUp3oCyoepZCuXWcqyBHWMf5MoUsW5EvyU6VjnPJN8+p5DcFpLn5inG9rTlpC/yS6I8k02QZsvxxgSJTlp6fJMU/'
        b'ZzKupcxOzZTIsqVpSdIdqeOaSUkKaT7+zZtxrjJbqZCmTaseBQ42Jv/rP5GIVhnl6gvecVXEocsvv/zyD6Q19BgMJQurjdnXp+T6a5QICdsKucGW1KuWgmAH1k889U8u'
        b'jesmJameVX7lT+bps/97U6LsnHzVPnesmId/9CctJxWNGT1IsrJUEoQFCp+nRe/5iL3yfAU+wjzOzcpJlWQpxoUzfxZG3qsWDVpIaIEMpP97VovklxGJz2YrotFlgsVg'
        b'MJ6gMbKRyRZo7df4ll3AZRhOhGpTmnoPeRb3eBZNkQ95Dvd5DsMui16dBx1HXSLHeLqP+MbDJt4jfJ9hts8jSrfa9H3KnLT2/wEe9sLu'
    ))))
