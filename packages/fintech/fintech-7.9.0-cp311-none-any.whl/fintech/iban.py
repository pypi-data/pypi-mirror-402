
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
        b'eJzdvQlAVEe2N357g272fRVoNqHZREBFxAVBZEfAfYMGGmxl7abBXVxpVpvFgAjaKCriAoILqGhSlZhkkkm6nZ6EYeKMsySZTPISZsIkmWTe5Kuq2w3dSmZ78+b7/n9o'
        b'L123qk5VnTp1zu+cqnv9DaX3w9L+/fIEurRT+dRmqpDazMhnHKM2M0UsJZua5SefeYlBUVcZurTELJ/FpEScS+j71elSlZTUbAsT3TfKZxuWP8JAd41Fz1FhUPmcLIq3'
        b'Q2D07YhJ4sqYNH5xab6sSMQvLeBX7BDx1+yp2FFawo8Xl1SI8nbwy4R5u4SFohATk7U7xFJd2XxRgbhEJOUXyEryKsSlJVJ+RSk/b4cobxcfk5TyhSX5/JWJsfSXcplI'
        b'skdcUsjPFZbs4ucLK4QmBZLSYtJcVmwKP18sEeVVlEr2BPHLZLlFYukOUT4/dw/JXy2SFAtL+LGikgqJsIi/ElEIMclz12OTB/pninn7GbrUUDWMGmYNq4Zdw6kxqjGu'
        b'4dbwakxqTGvMasxrLGosa6xqrGtsamxr7GrsaxxqHGucapxrXGpca+bUuNW4t1NyN7mz3EbOlRvLzeVsuaXcRG4rN5Pz5I5ySs6SW8ld5HZyjtxC7iQ3lbvKHeRGcns5'
        b'U86Qz5G7y60LPNCMcg94MKlaN8NZOsDnUUxqv4fhXXSHb3iHQR30OMjPorx/MK+K2s3aRFUxeMcEzLQ8fXmxRv9sMSOMtEKWRQmM0oq4KBWfxKTYVk9RRk7Kwz3RlGwu'
        b'uikFcnAJ1sPa9JQMKIeN4BgYSxfAxsR1a4KNKL9VbPgIXIrIY+g1YaNrogNdTlnXoGYIX9iIJ0aIZ1zEKRPEGTPEPQvEPSu5NeKmbYEN4QuSx1r2c3xhEr4wXuAL84Wx'
        b'Mw4ytXyZNW+aLzue54vpLHwZpvnyVooxdS0USRA/pyhg03qK3Gxcx6KKSkwozKy72cH0zXWxPCoywxPdywnaNaeCvvl0A5v67R4rilqRE6QOnUddoYpwtUKZM3vKhlox'
        b'abuH4br2+Pzt83cwingoY1fFacagMcVXbNwb9kHYHrEfRW5/lP1HyzZLhn+Zy/eMvzoV5R+iJihZMMpwBSeC0ATVz8vw94d18xKCYR2sdwdX1vonpcKTQSGJwUmpDKrE'
        b'krfUFrbL7FENULt0a3KiMRgNSmRTbIoBzkhBo4yPcnaCURspvFMlqSiXSUE9uAQUaP7laE63ssKTwBEBR+aMiqEWenx05SRMigceLc9jepuHyFwxeUXCDl1mOYPiwePw'
        b'IlQy/YrhkMwF57e48XT58CaFCtSaWTADd4LjhPhGcNRNlx3ORrTvlIJBpsO6IBle0KAR/T7Q5sPbcBDXbw4FJ5jzisCwYB4ZILwBL8SCm2ukZkguYQcFXsoCI/TQT8HL'
        b'BwujpRIOyqingBx17brMAeecCYLd4NE+qcQYZTVSoA4+gnUkKx/UgGNwEAygZjF1BQUaloXRLQ2xwbBwnRQ0Ie0MeyjQDes5MjssTO4bs0ELymCijPMUOMtGw7cn89UN'
        b'6iJAjbQc9+EkaigXdMqccBdOgt5KxPNaKbyJxBCeQqxE3bhDt1RX7oWGfksqw9WaKVBfCR7IsMjOsXYC18FlqTmuc44Cp/23kW6joY0ZwTPwuBQO4961I3K5MTJHlBXj'
        b'hJoZg5eloAEX7KJAJ7wBagm5dHgvcbuF1BT3W4moJSLWEXIv+WfAejSkKhZOUKAJ3gddNO+ugEeg1RYOSi0pulYH6Agm3RZ5gOoNQAmHzXEXrlPgnLm2nYXm8HIkqDYl'
        b'U3EVVSkSE8ZtB/fMRWgq6tHkMbgUuAHbdxJS5ovhfbGpFA7hSW3B3KoBR2jetIBh2C04AIdlLJrbbZ47Sc9s4V1YvQ4cNoWDuJkBNA9OqNO40j54PNwGHJFWMWlydaAD'
        b'jpFKXHgVPtwHzkrhXdzp0xRohufcSOdAU+Y8OJQitdTOaie8yCPUxHC4vAqcgMNcnNOLxAl2Mmi+1cAOcBrct0B5uA+XUR88U+ism4dgHbi9FQ5XcOiGTsJqZ9JQuTW8'
        b'OGcdHDYzoqt0wyuupM5GR9gFOpHgDhPh7kPU4IO5tHDf37gyAQnMMLyJ+30Byb1DPJ1z0sbMxRUO83CVGxToAaPgBD11F8GjPbCbi/K0DDpfCAaIkMBzsA8esQUjKA+z'
        b'dZACF1zgCMkD90G9NzyLxjYs04pdM2zg0iRvwptbstzQlDPoWucRA2jOglPgcDE4tgZ1cRhn9uNlt4FkOcErnrB9M84xpiXlLDy+jGbTbfsl4Bo4iiZR2/9uMGJLhMg6'
        b'G16yAF2mXJxxB43G0ZcMWAAGy2H/fFM4hIndRn0At3eQGhmg+hBo9TKt5NCtnF7gQBpZtRO0wFNAaQrvYObdxCxXFtAsrwQXQB9sRFl4rMNIiOHNbNJOCmjamwIfohwO'
        b'3U4PrCsjlby3ItFrR0uiAndNTiHZaIInSBeyoHLFAthhKmXTHO8IyCVzDodswMhceM/UBDczSoFLxftojXkPnD8A6mGf90KoALdBA4diwfOM9GKKZPuDDmOkrC8srYRt'
        b'SEXUcSj2DgY4nAbvyzDuAf3LopC2wHlhuuo80GiPVJMjkhABi278FrwfAuvRRJfao+VYCmvRVGNTjjTFw4Bk1NVcHqilcqNgDxkEvAiGQH2yEVaP562p/Bw0xZiOzeZY'
        b'a3hWb9TH4CWZP65wCaIVC1uhHFxdCK5whKmgEfbuRHp6HbiwOZWKkHLAqUpwk5avS/A67AOtoFtKlkYthRb7lTQCScoD0dRoydyAp2Dbys0kEQGuwlNsag5sZPPmbaPl'
        b'vhV0psJTOVJ4i0Er7qbUObIAlLNhDbhGEwF30NwiKkiFHU0AN6bJgDE2C4n5fZpQNezIT4S9MxYF9NnIBNjmg37YpuvOdUwoDbRq+3ON7k8L2ygINhA6IeCk/zI4hvQu'
        b'VhNnKdAFup1kfpg9V33gCGxNANcQc0h/ji4iZMJw9xCZYBYcWZpCa6H7C8BN0BUslWAJqqHAsYADhMfLHaKnOUMYDB7sNIWKZD5S3H3rbakkvrEpuAzkZAY3r4IDWUl6'
        b'pvBaGgEUQeAOfGDAYPrrAGx0RnoZfevHHQqWcMqzGKQ/dvCKGOmUWzO2MyVeFooxGuzeDZthz/S4Glm5dK/ABdiJZh/Uo5lPgCNGyJQfBnfJ3LsWoBJ3wSjS9JgvTcjU'
        b'gVpwWeaLUp7wHjypzyU0Y0iFnlzIzqSQfmPBwWB4jVbvoB2VuAUvSU2Y9JSd2suURWKKY2UH9Ka+cXriMsEj7cT1peIGrqUa5aZS5WCAC0a3IMHEZCtXg6PgKEcK6ti0'
        b'2usCx5JkISgnDFxbgHt2Q9szKGchjVILTwUj83SiAK27Tmo+PMdBdrMHPCJ8W1CG7NZ5Pz1YsXo9ESpw2gGtHH2hgrW2tHD208LZyoIPLMExQqY4Hd5MgH1SCzzQTiSb'
        b'cDiOkMlOlhjMIxrxkHaEV2jRrGEbgzHQQ8i4+WYX+ushGQQqWsgswmZwbccMoRmG6S0X0BkfsY8DTsM74CJtPTr5cBQq4AM9CBQEHsrmEwQI74KL06pgRsSuEuIRtMSX'
        b'ZoTBkxygBLft6DXYFQ3a/eDpGeAETmSSxeyL7Eqv4WqWILGTz9CaA6+zuWi9kYGuRByq3S/TQ1ke1rJ5GOhhQXy+V4jiNdi4AQ7hu2RFByMVK82Go4SYv+dScMYY0TKm'
        b'LXgbG9SQDGuEeq4kwCMzgM3NSxaEMhYVLtA10o8bQaZzD7I8J+zQvRN8cB6t01Q4ZhyGxOYKvdwHQU/4yj0zAG87MiSBKIMF6rwNFSpaWfDoZv+F9KjTwqTgHBc2wJt7'
        b'afM7AA8vAmcK9QChAwKRWHpBMxjN0tG6arDoN+bpjfwlJPqnd2qxNHiUdRBclNIWuxsJnsVCkrNIjJTMUTgyAyLB1SCioMDJsG3Tcj1tAmL5sJXoJ6f96fCscQh3H20E'
        b'jiMM0AlPz9XDaO3wKpkqBAodZ7SKXqeRImnXiQEb6dv7nJ2we5PWLQgGXb7gjrSKQ897436oICYlViDVEiMzAhpKDCyKHwtB3bt7abnuBg3I3Tor1EOHhfA2WW/rkZNw'
        b'00CH3wWP6EVyHRNyhXdY8KYTrCbdmQPOIDPSKkGEGDQIb9tCo1bY4AbvoNVzfAZngppEMk9+PsbPrcQrz61EeASORpRzEJq9Ukb3uBV2mqKy/VJLBo1Nu5AOGyH61Ehi'
        b'bqCzekE3TulsDosFBzLZhIon6HaBLXBAH+E2I42NbRfLzUvXqQFMZhUCoQaL7wLbWACqaRlsRuJ8ORiO6cHhjcaycJS1GJzYONvgyB02GDJLjYkD15mlcykJPMWFCi+d'
        b'69awCw39SqA+jL6eR1yqcHAXAYneOAQrCQJQYu3YBhvJrM9BwFvPXK6GV+gVFMvnUBFAyQHnkLt4lthKG1H4wUQEufGMX0RDB6eXEDEEZxLQGA3kcMZiapV1HCscnuGA'
        b'llA4SDiZEQyrwX2kn2bAPVoGo1qxBoOIx9M6CFEsPaiVSnKPhdhgvnMBI4NjHMndQoa/B3mJzeA4MjUzLsHiNKIYswPBfRYjmRgzROK5ZUdgVyZoNPaM8yauN7IOp5Ef'
        b'eBZDfho5X8QuzgMGIQZvg1sIBxmacmzDj/rFEjseDm5j61YfRFjm52vP3gaHLYxpkHshDsFRAnRG4qr01whsLaVFrp9eIjeRzJWCC7SKOboePHKogsO0DRlCuDDkABFc'
        b'F7PtBqYNkUBr/jLGAXPAEbReUe55etX3BDkB5QLknzHpVXYSnt9HD+jc6lJDdd8FruiLP6hhIbxxG3WGqKMOnz2gCWUNlxvR+k6B/J97Mh9im+LYz8GS/WB4IROjkrto'
        b'zeMoGb0Y72dYwIcZ+j4aWkYNtP/fl4tQtRL5CXqOGpJQrd6BAwvhnSw9Rw0RfUjrizHQBkfBYISep7Z/KY26b1WuNtBI/XCUVhY3aHYPInZnA1ojwdNrwJgAidKMU7fH'
        b'kuT4JSHP5lYuytCuopb54DxhIqhFgKxPq0SInLLAOZK4NaNEbsFa5KrjYaTuRMMbAJcRJQ6NM1rRmC8SnAFGbfkv4s4InS4g8gHbjOfDTg6S0Q4txL8q3M91Qfy8rV1M'
        b'p8HgGoIy4sEA8pmeExKik2bIgT7waP4GDprJHqCg/aCOtN2JaLUMmzPpKVAutCRyu/JgnKHlwppi2nIFQMWaFOPFZmm0qDxCa/Loetio7wSfKabBTx08Cs8b6oxpNKVj'
        b'Wj68FA4eccBJcIk2CeXgtgWiehUR5NDu6QXQZUSz7ayntwE5Zp62d1aocyMLrQHCFQsXMMCZFSZpYEysVcNuHIG7vh8Oj4B7ZKDgMLjopS8zq6MMtLmAhTzbc+mE+8w5'
        b'LDyD+k77QCVBOSwwFjU7wgv1mMETMk6ZG9LihPHHpeAlVw/k5BvRpLosmERN+28A9wzX1mE9c+cKR1lwKI1HaPhZBRmDBr04QTA4QQPqW06oqgFCDOMbeo2P2BYW8Kg2'
        b'LgP7DyCMbMo1or36XiRVh2kAU4sAqVy/Oyvm0irjGt2bGyx4A7avocWgHR4NQz7kkZn4BMq8SAjFO+x9AbrNiBO8H7cmyHgRvB9OL8xu5PKObQEDphVaC9Sa40fP4yU4'
        b'BPtz0/UiHZuQ4sPM4MVlI/R0fSaaAPuriGaelwLv5liYVmJSVzCMu2VOL+Wj2Ec3wKaFPIOljBXiIxa4Q8iELAePtu01rTSi43ft8FqlLAyTQRqgdXaBBMOb0Zo4thNe'
        b'QFq1fjMl2YVcK4pPRrIXXgeXDsC7M5EZ5E0MEo8U9rnCs7NphqtgbAvHRutaXUO+gj+y10SYLsCjMYExesEc6wTawDal+Rs6VtN+IOzOm3FuQSunAoxm0qr3KOwUwjPw'
        b'rF4ASAzqaf4PgdoyCwywpiNAYGgZmbRlYAzB+rocUws8+Q+wrjkmIZ1Y52w522iu6CmmdbBuPuzBEKSWdi8R9q1fAc4bzUzPC2jjBqd8AWMN13ihSQlxD5D2OwMPG4yW'
        b'zOY1DuyIz0VzkUqFOXJAQwVsIIsEtqesMnABkMK5rZ1/OpQBhths+BIN5TeWw2rDUTQjrtM9uU4vqTo2d34GbYZaQEOs/qrJ8jRYfUtYCBA2wpeIhizaCAdfVB2GirsC'
        b'Ds+HrRwEZR8AhYBLL7eHCAQchkcqTC2wFXxIgX5wEbQS28pDxmAUPgS1pvCmdi32wKu66E6tKeg/BJpQHq44gpRrRinJWZ+KENlxeMKUx6Tn8DKUJ2rjiGfsuaDZVKaN'
        b'a7cHxdBL9QwCRUdDD81E94xgJ5HJio3wIrwbbCrVLtSzG0AvrW4G8sDDRIitFdF9Y0jhrIuULaRn/SHiPjJjQK6N7oHrOi9FTqKBbDC8FtSvozZsWwS7jCASGDMBm8QF'
        b'YR+yH6dhfQpCLYNJsIFFseBDZAbiAkizJsgmHUuGdSlozV8xopjbGfN8kWM5B9ccBdfAzWTYNA82BgpAP5sys4I3k1n29qCTjJJNJQWmBYFTwQlsir2CgRg9DDvj8/S3'
        b'qPGmFdlRw1sMp4x0m67tlJwhN5Yz5Vw5RTYCWXLTAh7Z+mMzqVqj57b+OGTr77kNQXSH88L2HvsgR7v1N2ve9NZfgYD5qyg0myZ8vZ9YvC2NN6LJ1jS/oFTCrxQWifPF'
        b'FXtCTAxKRpUJJcJivjhXWBLFX7tDRFeoKOXniujNbVF+yGwVcsV5UfzEAn6huFJUEkTX0m6A84WS6bp8cQne0jaggH/ySksqRLsr8Aa8SJi3g1+KCklmbSivVFZSIdmj'
        b'31iFrpti6T/RTgXey9dSC+GnyqQVeIyYRVnpweHzFy7kx6SsSYjhh81CJF80a9+kojIh6VgA/hbAFyEmy4QVInI0ICdnrUQmyskx6O+LtLX9pzlOJkk7Fn6WuKSwSMRf'
        b'JZOU8tcI9xSLSiqk/BiJSPhcXySiCpmkRBo13SK/tGR6uoPQ3XhhkZTcxkyuEkufG4zBxjGbenHj2Cotnmz9ssudqFuFhXg/eGukTEqReHoVxFCrHn3bBLtTqU3rbEnZ'
        b'rwQm1O82IDVslWN2Q7qU3jv+zU5LSmmyhKJCc4JcCuZTZN1mgoewj4RWcpFlwtEV2AQ6BZZEyRjvAB0kDxlFOclcspisWAtwHOXgvbsS5HLg7TsKNNLhQ1AN+sjO3SZ3'
        b'sneXCy/ReukSHNhP79wZIz8Ib96lwRt09P9qQjbZubOcS/bu4E0/WpM+tAfHTctYGEUysSfaHgxoJ33BdtBiWo7V60kErwaxD90PemT4PEKRZBm921e1E+/3pa0ipEKR'
        b'3rsPh6WIrwdysKPQsgSMkZzlsLmQ3gYUbKM3AjvBLdoCjCBkQ+8CzoeXyUYgvINcNGwBkBm5B8/TG4E4VIv3AuF90KbdwVwO200xd8AdFjYOZxFrb9FZneB8KhzGgwX1'
        b'++EZ7PbdYNGjrVsOx6RVxhjprcbhtJOgwYPOuQju2tBhq44yErlCRlLAIrwDpwQZJIu1iOTYwjpSJ9d9A90MVCIfgbTTSMfXYa0xuE/ageetSTsBLqRvfmAEXNVG85qq'
        b'SEAPKnkCJt2HUTgYQmeu8Cd5Sbr90nPpYfTWbxYSErz7CwYWEYFzzTam/Pe647MOZofSmbTELlvoGh7KxrspJqCVyp0Dz4nNzcYoqTWaAc2qi40tj9JgqNXjd7//9fYJ'
        b'i+5q519U380R5vS/upuVedGiZNXVHznYQtnqa6eHpnxHV3zqo0iIk/R2Pfpl1ei7f305Pcfs/YYGe7Olt69l/XXz6Y/cIq74rVC9nPV4c+3KbXbvOvBjMhP9hrd/ANbf'
        b'3V5lde2Ib8SUxVcFvCX2wl1bXgs8tkrzNOnYmcoN/11R4OjeW/VK04Hgv17+IE/6i4G3VUG9b079afXXdx9Fph9Mf+3GksXfpb7Z9MqJoNGqp399qh62LP3s+9YLO24O'
        b'xUYFfNt9dKTlUcrDg3M+nMuaU/D5wbZA4xHxRzceRyY+fL279dxxL+a7Xyb29LKftnnNcXERx9/ZUtr/ZtJXolsHCjsHHr6bXPLBW47/dT9r2OdrAWcKz0wGE54IBA99'
        b'g/0TgpmUEehkBpvA01NuKMvTHx41TYYNglRZcACsm8ek7FMCQQ2bC4+D4SkSTVAkrQP1VXCoAjTBuzLY42jGRZDoFkIOjmCIBU4nwgtTWKZjUhDoqheAR7A2IDiEgdo5'
        b'wgzfDRum8DmMUti1NzAkMShAEAJPBsFainJC3iCfvX15lsBigukvkODF9z+5SC3QhajEat3Pt/bRBZLSvaISfgF9OCwEW8plEyZEb2fjxF6970xMZQrJ0TfV1ORmDmXn'
        b'NEkxzN06IpQRl6POR/VE90Y/cZ2ncp037jhHIZtksszdxiOWDSaNVKgj4jQRcWqr+Qq2YoeS2+fX5/fNU1s3Un3mQqqhiiz0/ZtvvnlmaXtqv8rSG336uGNmL6/VRCap'
        b'/PGHFBy3tJmkeOZ+4458xR6lrbJQ7RiicQxBlKw9x135HQvGHZzbxS1iJVMZq3bw1zj4K1jjto7d0SpbP/TpW923ejDuSuq11JGsJ0ErVEErSKVJI8rJA9PwG3f3VHoq'
        b'Y5TeXTsUq8ctHSYpc3PPcRfPc8Gdwafndc1TGCNq7ctblisj1Lb+Glv/ScoUtezojmr7rWGgq5Pu+szDp0M2ySE3jCgHl/bslmzlWrV9gMY+YJIyJrVUcxeqHPFnnBRm'
        b'UU6Lntk7G5Zkk5LKXSrH+egzXTDsmbPbOY9Ojz5HtfN8jfN8PRZY2tJTxFamqZzC0IdmnZWdIkORqchs43ZENFsqfZTlfdZKaa9AbRUojxm39VHZ+igz1LZ+GsSniCe2'
        b'81Rm86RmaPbPWYVSgybLWGOMZSy8fUgJzCbYWDQmWAgyTRhrAcgEGyOGCePsbImsJDt7wjQ7O69IJCyRlaE7f1tIcSs56EcnpRKs0yRYE+tL4jlctBldvsE/SBr3sRmM'
        b'uWio//LlmYWjXFy7q2FXtekkk8OwGze1kS+qXdyw+Bnbsjr5cOqx1OrUca7lONdWbvrNJIfiWBnerU6nf6UYSZ/lRVC3LGKYLGREMEKPQzr7RDIC9bA+DTalJ3IoizJX'
        b'LisSngaD5BSWExyGR5NT0mgMz6BMN1fBaia8EQKPExsQBusjMfhH7v9DGvyDsfA83RlUA2RTjQE8kwbwBL5TCL4bFbAJaGch0P4c4D7AJqCd9QJoZ78AzFkH2VrQPmve'
        b'NGgvRKA94wXQjqAdxo7TqB2fFxXqToOSc6QYiRKYLcwjgsQvkRXnYuBsQAjD+IBdCPmWEnkI0B1oxXhZIiqXiSU04CwTSZBnUEwjY92xVkNsmK6DjKgjAZmoRXGxaJVE'
        b'UioJIMSEKCf/udbjRGUSUR4aSX4QX4Yq6gjz88j4iHT6C3RHb2e6yS8S50qECJsbUNsgLirCyFgiKi6tpHF+pUgixfQiZ3dlMKMwn2h35nnuzYrjtdykazzP2tmawM5P'
        b'fJGwkC+mR5FXKpGIpGWlJfn4yC/2gaQ7SmVF+XTPMTxHXRdK+VWioqIfQu+rxJjXM84C8tmE/LDgClkZcgK0LgGZLsQ5f1wiCDck+BtYnjMLluelyYpQysMUtJhDeYwJ'
        b'qA41Y8NqMACvZcDDyxPBmRIx6POxQR76UWSH2xenwQtuoA20FBnDl2LhLRFogf1GPPhw385gcAdeh4OgaQ48VpG8H9aA9hhwGkG4W/GgFt5lMcFDR3g0YyXtD6Qy8Qr0'
        b'X2qaU/RXh1JK5oWB20U4BEZBPTyZC+oFwST2XpuekpjKoFyXsw+AO6m041G/wJhCai/hY0FO0bOFLtRasbn0Q6Z0H8pyjnrzzI/CuntaixmshQqwERx7Fswa2gD/3GAm'
        b'SBGYLU65beb7GXfBAjPB24JfpQa91XE44LQw97WwBWamGwc7373XYN3XYv1myh2XE7vXHxObjg9+8mn+J/lpwtjbvka/G9r8ePOltPe8XnJ57HIp4lLOCZfHOUbvRFDV'
        b'P3UUx4QKjKdIWKIO1oHhwPQgWMei2OsYyFO5grDqWTA4RaKQ55B/UyNNDPZPWlaemoaAC1JyJ01xcVgPG5KNqVjYabwKXo+Y4mNq50HbepTRBE8GIl7ApoRU2GREOYYu'
        b'iWMHuML+Kbyx5Q0vxCWnBycGCQRMcBVepkzBLSZ8sIZBOlQAO8VQj52MhHLKMoO1bmkGaQGcSTTHLAfnwfEXeW6zjxQqhledk0NAI7yUlBqUiP6eTCERFxdwi10COnkC'
        b'438ETxnTeGraSk2Y6umAvfoJApxOUTRwijemzO1PptalIrvjOu9p6Mo/ILwTx5ii8HWSXJ+Zual0n6e2Lh1RygODIrVttMY2epJimoeMW7m8b+X9xMpbGaO2mquxmquy'
        b'mjsuCFaYoK/jzt7vO8974jxvkDvi93KE2jlB45xQmySPU/gQxMQw9xp3dO1Yq9irsvJECEae/CVeTbQ1N57g6hTMhLFWVUiwAZJgACtxfpEBWlNNm2kMhw0GrsHFqrR2'
        b'Go1dZMRg+GB7+3cu/y5r/CVeXx28EOqGRTRLFo3l46458q2fD9FdgafAMTAEGoAyiLUtOQIeywBN5eA6Pnhrgjx3pE26jb2IKd6zFV4zrbQIAg+QD4xcc4gkdD3JCVgI'
        b'b5hWlsOmaJwjp2CXN2yit2qbwXlnKXJum6HCMoxNMWELwwGfutAezVgGT0nDJAxjJsUoRT1ESqideIzbS2CXaWVlPGg1QhSPU7ATdMMR7RnAUEfYQwKChzNoSAAvm9Hx'
        b'wGPwaKVhOFACq1n2aPG1a0+A1a4LRFjDfjmDYoImRizoWG8AJrg61SqnZqKBCExw5HQ8ED8UwJSbFHCnQcXzkcB/P6jAkcDf/VAkkBilvx8HJJYNW0Fc/O9HAX8gOIcr'
        b'/1+PzeUVkW5JRRUvRuOe6yDmS2lengwZ8ZK8Fzuqi8etWhPDj0UoXYKNfNw//ADPC/TIAz16fRPiSZGRp5ECsmLXBgShP3Fx+E9seuZ89Bd1L2Bl2EqSERsbEPQCRb0x'
        b'CYukpbNGFfEgCZ/L6FgiopqP8caesucYiH/WleG6lYtCIkN2E+qz4skqoSGgxHAPN/ECudKyF6Hl/37c0kIbt7Te5kSFUlRZUHHO/ig/AR2LtGXZUEgb7y7g5ewP2VdB'
        b'yazQTR9HpOTqqcoKitpEbbJIJwGubdsKQD1+bmRHLFqhtgxevCeh8FNHSwppkzV/XpZTtD8tjhIwCQ0LP/gwnIrNp6j51HxwmkVigs4I5vSHs83LkaeCfJVLvoTCgjQr'
        b'Cllbrrwix8zTT4QpYCsBG2E7vBNOMb0JjYNAThNexIHDxt6I3BpqjQR2EBI/CTKlkMZKuGGbY3bKVIqgUej1L5jSZyhLI/M91RxsA1aYHf9lwXcnVzIcRph+V/qzXzfL'
        b'/cSOHWn1Svh4f+fZmu+sTC5evOYZbn3ms6//OLSPt6ux5JnqRq7VeF6/3Zrkh7+W/3j34TnbgoRLj5vFXxwXDoR/1qZYVjNnnU/Q7UXFEqsPf1bzwZPWn31w+rO22itr'
        b'y+J8Nx1K2/XUf4HP1Zatr6q+3NW02+SEW+yn8a+EdDR83uX8xbZz8sD/6hTuf98sg7c3QHi42Ot234b6+vfG7kg/8Z0bmfV+4X9/HfiXHVsjPo3+/fj5nw1Mde9T/OHh'
        b'oSvpki9STXpDL9j94RNG+5GlC3x3CYxI/Anc8FoA7yx7LgRFAlCDO0nwKizvUBR4EKgXu4It4DwN3h7CE/AMPLYB1iOcA5soyiiCaYFAbR2hDY/DM97JsBGBuLPJ03En'
        b'y1BWIbxlPUUg7GHhTtACTszEt+BNMwueEWUFx1hz4GGgIIgNXIS1CQE++MmzmcgWVMJBAe+fC1Fh53k6PEWDKh7t9SPVvXfmKwFU27WRqDguZWU7STmZr2JMMo2sPSe5'
        b'lEdAx64+b7V7iMY9RLFasfqbp46eJCoycyHxkY4Fkyz0HQebbN0UUR15ynA66kGKDBqPsG6ZzZT+5pmjC0mhclmXN53f1LOld8sT91CVeyjJf+bo9b6j/xNH/z5btWOw'
        b'xjFYLxBj66AIV0ibI9siOyQtyxTLlHl9nr0Fg6zzxcrikdhHKfdS3rBXR6drotOVxdM1ytsWdmxS2c5Fnz7vPuG1uYOJqoCl6KMtoe2NVDlfmaEM79rdt2hgaf/SK8uv'
        b'LX/iEaXyiKKLubh1CJWMjrwufxyycuneqbL1R59xV/dzizsXKzNRb12DNa7Bt11GVmvmx6lc41R2cQgZKiJINOa4qTXVbOLBOsvw0MZ8TGlIiIVvgoUs0WzgcNbpNZ0B'
        b'jDOxHXwKQW9q/4gL1s9ARqExg4EDcv/K5d8a1OnihVFDFjEUS8CgtyhaYCs8CutTCvP0tmvXZxs8XjmtuPdiJMUij1eyEYriFLCmH6B8DiX9LzxAibDTt58ZWJdM2jr9'
        b'gHtPG1MRDXqIvx5CYFNBaVFRaRUqZWipCLIR49iORMSXysrKSiUVovwoftyqIH7M2iB+bMJzcOzfaH9nD+z8XeNpnEZOAqYs24nd1ECkXWFtClDCvgw4WCGBt1iUG+hj'
        b'e4Fu0CKLxRpObgG78IObGxJmwnjB6xOCcM2GxBRYl7guAdbPy0yGlxKmofda/NitMbhvDh7s2kVOSxyC95EbgOmUIYW6XhqOK8HGZAZoWWUCzqaBpoMmoB9B/WxQbSxM'
        b'A43EDIYLiDWnQtPcHVSxxpS41O1ztrQb3ZkqXFzctNQErLA6/st30tb/xJ8d9KDacej21qAsn/rjb0ccec2dP775Z7sTWSu/qjEze/uXX/8i5SvOyqLz3zk9W/Lx8scH'
        b'Nu58+YzkJ0nfhYYPXzltyjJZkLSTc9jmUHisY2fKSXaVsaZ/sXdkyJ9+nut7LGn7pt2f1T0qrti1DAjPHKgRtn8N3tw0upy3b/fBzM71Uz29n366NfWbhq++ZfX2+r61'
        b'ea2AM4WfAl0KL8K6Fw0YvLCIC28nkj0UZ/DgkN4eSh6yMoZ7KAfgoyl8UK0Sjh6Cw5hnN2FDMJQnwsZUxOvE1HJEuaGKEE8GV43BoCBkij6uAeRrk9ODkadTCWvgZUYM'
        b'rAbX6Y2bVngZjOmatZSYW8Ihs3Jz8BJQGFFzfNhM2Jws4P7DtgtPFBG+adNlXCiqIIZL94WYLewTY8WWxqPs3JHNyVfbemtsvbFnPv+pA1/prnYI1TiEqqxCx8OXDkaN'
        b'5KvDYzXhsWqzUPlqxcaO3X2O45YO3UUqywD0eeogUAVkqNZuUQdsUTts1ThsVVltfWrj3lGlsfF73ybwiU1gX4LaZoHGZoE8FpkUOr6AmlF5LkGUPVeqHWI1DrEqq9hx'
        b'S5tTxfRuy1MHb2Us2S9RsMat7RSZCqEis82xO1VlLUAfkt3H7LPuY/au1jgE4W0VB3mSBJ/0pQ2EkQS7mT9oFvAuMZUzwygJdsynmeSB9Ke0jBgAHNjnMhg4avE3Lv82'
        b'LY9n8BQvkLpqsZg1uxbfTdHBdVqLFzD/wzq830DJZZUViSuw8zujppEzhxQlvlsgERaSMxXPqV6d4hfyI2YNvhoU9o9NX5e2NnMTVuGrYpOz1qUG8VErydmx6US3x5L8'
        b'7LR1qStXZQp+WAOzZtHA2vcYvO1rRJlRCrY5P6foUHQpRR76KgDKaD29nDGjUdmwxRceEYArJuD0Hq3CxMdhT5hwufCIDLkUVMYBcE2/8rRCXwAuYZ0OhyzFN8MuUNJs'
        b'VDjBeu6Z0qs/iujuaV183PP4zVOJLQyjnc47naJO/8ip/ptkp18dMROkvFX94KdlzXMfp11yMTp2g5Ow01rZ6rxuQ3Ceed78/tG3f/fRe6EhOaDgvTD+dvOPOeFllxjU'
        b'yizbzM5YAYtoQNgL6kCraeGiF1G8K7xBNocXwUcQd/vUPj2kvhicIvh6TVhJ8jxUJ9jfCJ+Ng6ecmKAHFR8VsGdVRWyiinRqyKRMKJFqo5J634kyEmuV0X4e5ejaEdYR'
        b'0xHWtkOOtzs7xCpLP/QhumK52mGFxmGFymrFuJ1bR6HGbu77dkFP7IL61qrtwjR2YfJV47ZOs2kwW6f26Jbo5mVty1RmnnoagvODGkLK0SkHWjdg66vf7UVYPezSqYdd'
        b'vP+EZiBhxDZeANVvEYnhH3aNQOe89Qj8ITSAw83zQF066PGBdSlGlMsh9g7QDO/+P6dC8L4cm/FcCE0fCZJ9pBJhMQnW6PQKPqFVJhKWEGSIgCENBxNL+HlCqeh5jaHb'
        b'3avQR4v/zyPE2fQTO037lM0SNJfD8HiZFN6ScSgmPMvwAsdgo/gcP4opxSdxNQuGziANcri2p7WntdzZ+wM3FtzJP1FtF5/o1OrZcTjcjarewh5vfEyLPlNP1vEa1C1T'
        b'M2L/0AzgCdhrkCJL1VW7VHNMKDsPxZKOfWrbQI1tYF+8xjZcZRauv7gmTPFKyS6VYHv6jyyyBLzIDJpMMFhmqSYMhjNeUrNe/l3LTBKH2pt91ezHq4atXTU4DK3b0f7P'
        b'rRyr54PPM6Y0X0wkTCjZw68SV+yYiadKSmUVeAGIS7B5FZKNYgPnyoDgbCuNb/BepemwrP4C1F90hpL/zy1A/aoGiZhKobhImIuwwi7RHmmU4UoNRh1bG6UNH6N1KK7g'
        b'r5UIS6QFIsnz5eLitOXoYfDjRLmoNAIZz2GHYD6ODP9Q2flB/ID86V34gOerrgxbOWtNdP/5olmxsbqOCyX508Hv50qlxaSuiiJRbaIa/7kNaS6Ncl7PdqZCU6yNqJyc'
        b'/RUrZRR9zP4+eJBKIxXQ5kCDFeIVrskMXs+k5qWxySOcD+mo6b10eIMcRLWWbKI2wZpCQvhjL+QZ5uzBqzlawxZSsgiKPOV1wow4mfgdQ8HgMLyO92WTN+g7m0nYzUyi'
        b'9oBHXHAxean4Rro9W3oS1T7x5QO853y4dteentbbrSJnb606e1zkYLXtVVabKL79uuiN1i/yr3A+ye8XrjgV6BBwePjwR9SHV8edVJqI+e+FBq3IPN57dv7xPc62a4Jt'
        b'wQ0bh2N/YRYU3VM9XaNMaDhrd8LupfVzE0e4nR7Ou5zUf2Ga+V47KNxane/KDGL9+qdl20NZhabUKwE+Xr2U1omEtznw4QtOJLi7mM2F97wJSvJcAO/RIUh4CTbowpAC'
        b'cJccsKuCY7ag3rIS3gG1VeVmG/aVsymLICa4H7J7iuzC4ROnA8npoN2bOIuMmE2gaYo8UdIR4Iq30xB4pNgLTeBxBnjgCm8hL+dvO4RYDAy2h7F+1WqEvfoJot7HtOo9'
        b'3pSyspVLFUvUlh4aSw+l1xNLH5WlzzMHN0Vhxy61Q4DGIQA7Zs8cPJHjRZ99az7YdhCHApc/dfFR+S4a8Vb7LlW7LNO4LFPZLRu3sW8XtAg6VipZahsfjY2PPPapvXv7'
        b'tpZtynC1vZ/G3k9lH3N9MY4cjtiOZI4IRzIfOKoDYzSBMfL4cVus4s1TaJcxemSf2jNJ7ZCscUhWWSWjzPYlLUual7YtVZnx9QyQsSSR+hv+n97usR5/JJnYCOnzZS22'
        b'QTKdDRL9TRv077dGxB18iRdEXbOIwqCPvEurA54AY4EJCaCVxMrZixjgBngJ3iGu/QuKoFprtWoY5CQW/UY1qoBDLBdzlnensXiz2KIXN1KRdWIeZGkt16x5+u9O+/Y9'
        b'A52VUirMl/KLhWVliMVS2r7klxaLpBXivOnjReSMP3nd37T9KRAjAyAtE+WJC8SifAOSuXv4AWXCih0BZN8vAJ/1k/zN5wXEJeIKsbCIX4T6gqCbtjMGNCuIwanSHpAq'
        b'k0kKn9+lNVC+RrMoXwv6uWqWHxgMTEDztSYB1qYHr4dy/P61BDiWAK5DeRBSFKsZxovAdTBCn/gemwtGAwMYFGMz5Q5H4WXTPLKtvgq2p8H6xCBwEnZjdRrOprignpmE'
        b'FMoxJB54Q2UZuBicjBQsbEonCtcY1sZQFmCMleAGm4kaPwQHirKMkIM6QlE+lE8IbCZq/HAiCfBFNrBzoo1sN9B7eJ9bOuONvYQtBTlb60MF9PFuOAiPwDpkCPZFk128'
        b'SCfyNJgvbEFaX8/rLQNnQBMObN3JxEHIAHiWDeXgFJdQXso1wdtqTj+3y0lx8ciimztgSzb8QpnLc1JU9t6U2HgkjiNdgNagKur7xsxHya+G2h1M7JzyMznyu1/5fH7k'
        b'6L3Ibz0i3X7nYPHOUde9x233bGLXgOu/7rzy1uJPH318f+VAKu+32wW3fvn1h2+1f/1H30c972T3BL71cpZMbfXwqfTqb5K+ulYQ8t0rkZpN23bceC1dw/113OtPjzDY'
        b'gS9nmY/9/L/PCV0q0yHvQ7cf5ZzOfsX82vkFh2yzNoYbZa105g9njP/0R4OPJ6MEfuvUXy60GDjP/ov19oONK8oTWrpvRPsW//onOz/56lb+mV1PLgl/Wfj7U7UNvc69'
        b'kRL1TnXlUHSsOPyLhzfTPmhyHX0wtfe1+sq6D2uljglf3/D/ye/ilZrT7yz/c+/yR5Koru+eKDtPflSa2+aUN7Xil2ce/X7/szJVw4l9T2597v/aqpNmm9ZaKQ6s32f3'
        b'VWV6dMqJ/tR9A7/iPfnZ8kb3jA+KLwksiVmRwTZwhUgf0Rbxa8GNiHBirqqs7GF9UBpsmIvnLZFDcWE980AsODeFpW0hGBPpzN02J72AARgsmKLfiHYPdgYmpaYwKLYn'
        b'Aw5mgu6qNLLrB0ZBF2wJDBHAuiC0MMAIrAbXmOGwgzuF3zAFrxSYBYagRVCLT2vVbixAgookxBHcYSfAR4unyIOzXbAH9OpFZM24YAgeNgjJolUwRu/+1YFq2ISEPjE1'
        b'CO9AtqYaM7lwDNYRu7sjfo/uXHsdwjPas+189vZAbxL48FmNFCrdHWSx4S0eaGIGH4JDhPQSCtTo7Sq+lE02FsfADbJ/aYJGWhuYFpyYmJoMrucEwUYBg3KAD9hh7uAo'
        b'2b/MQchnQH/zEshh/8wGJji/fYo87OcO+6xjECV8HqaTkQpuwcOkfTY4z8YrCnRRglTEJC68zwTNoCNFYP4/P49vTmkDxnzthhgNEyywUsyeVsR7n0sTsPCZduuzzJSy'
        b'c2hb1L6sZZnSZ3rn0jySWOuFaodFGodFKqtF49b2CjtFfkdcX6TKOkJtHaGxjsDlPEeY447O7VUtVc172vYo2PjkvSfJIJc/4MsUZXBvtss333wz2+1ndk7tSS1JzSlt'
        b'Ke/bBT6xC1TbBWvsguWrnlna4QK+T63mvG/l9cTKS23lo7HyUVn5jDu5TVKm5l7komCPO7q2723Z27y/bT9JYIzj1lFx7lDnoT6p2iNc4xFObo3bzRnn+1w2OW/SY9Zr'
        b'1myu4HZ46++4lrcsVSwdd3E7J+gUKFf2sdQuQRqXIEWsInbc3kmR1WHbvLFto9KmZbtiO0FQC0ds1b7RapelGpelKrulBjuoT+349Gj6Vg9mqu0iNXaRCsa4u6eCofBv'
        b'NlWYPjVzeN9szhOzOWozd42Zu8rM/akrmZQkBn1FJOYKrgcNVmkClr8fEP8kIF4dkKAJSFDPTdTMTTxl0rFIbeWtsvLGk6Gr8yUWmFH7GBfWKy7sGHfjVzwZ6EqDLe4E'
        b'G9veCQ4xu38HdGFFr9uApVGXCKOu52RMgoHXPgK8yBas6T+GvP69wQCshwxg1fSpNPzK5VPGWljFQcBq5kW1lPZM2n8GXB1D4OrRLODqBXf9h1CUHnIyIPMvoSiDFg3I'
        b'/cMoarYX69qm0c+nHzsIB2aBUVoMBc8mExiFVOw1AqMiQGfGTlSDBlLwMvJgCYyyhP2LQRPoxFDKAEaNgG4Eo7Cvtx8cAzX6OGr7IWMaRoGL4I6AKYtHhfwrD0gJvoF3'
        b'cGQOv3GjeWuluQkcrqhcx620AIfBMH4PAzgKFPA0OFGGGm0FzbagxagQv1m22gaMRi4mpGBvObjwHDE9SjFgcNtWqCwqhI/4sZGwBnVJzksER8ORzxgDDh+yAYNwCFwi'
        b'IGrFQXIQnBrcnms2FL6aRla/5DlQyBJbWSXmRnOqGPTNilA2lmj+5NrCoJL8cIq8jWERuA2HTGEjOSKNfPWTWVzksCKsihEC2WCGdanITuaB2+YHuFsTUF8xr1cga3wd'
        b'DXcMXkcTF01FR3oJmKSV3+fTO8cqj8KtZ1196Ka3ryfAMpSfvG//kXnmFHmRiHlqlQF+1GHHAnBKBx/hYXBPYEROpm4BJ8zXeMBhvaCoCagm5yLWgzvggSmagCPwpekj'
        b'ssfhoPY9aydKTCvLF4DTujOySbbkEKwUXg/dkySFd6bPx0bDh+RwmeeKHGmYpGKR9nCsTRJpJRc+xG+fqETyNjh9OPYk6CUDjIvUDjA4Z395wBJ61GlbaVasWHhw/x8y'
        b'IigBh4wkEQmeEnU3n6frLJCDG/QjtUd5sBX1FlyM0fU2FB6ms/rgnUJP0KTf4fQKmqAVHEIdBq1wVHee9z58RLLcYC3AB3pNoFLXZyNwW7zj2RKW9AjSuR4/cWnMWpoO'
        b'Q62WLqn98qcLe1ZcHBp6+Y3qY3GrHQou/fHmHiav59bODNl2K7PmIS+HEymbfvTFkUevXMxsHQl41XFx3Re/uP/xkuxfjFkmfP2FsHjx0eCXLEz+OO/quE9nlGxt2NJv'
        b'QWTvvk9WSMQHfnZ81fxdbks4HO4oZ8s15e1rlXWJ/ueOtLYPjJm5w9jIw7VLP373PaePGl7peGCm+LBy33sfiF/3D3ETJfYU/baC+XWj5dVxzgfdgcbFnwQn9TY2Nffv'
        b'eF254Gjv0S5JbFZGef/id+J/0leQdGj4N+Ius8vljW/8d+Wq3ztf3vvwivuFgKQPjoliVxr/XBWmSpd9arPaf8OeH204bLLO+Hhzk/LPn1xQDb9Z9rjl4cKqttKY7qef'
        b'ce7NDei1Vk/EpH/86X2TD117mN5rdxz7/V9qWp6mqx+U2nnvLVz+6gfF38ocnn71J4+n/7X02l9v/taG8+P9mq6XC5Z1qsO33Z1/ZZszWvu/Fzruu/19y+NPVhQWfTTw'
        b'qPNa2Ov9l37zWTyw/2bgUdmfDp4x8RWYkpBPARwwBxdh9QxwR27+2WwCaLngvCd+3S7G7nrAHdwD1fSpunvgzqLpSBWorZrB7k5FU+Qd0JmVDDAwjd1BN7OKPqswkswJ'
        b'DJnvpwPuCLTnw+v0gxPH4dV0PdQOG7Y4TKP2aHh/in6RUQq8GxhcUjRzFBBcAsopvCuKIG1ziWkAbAzElbUxNHgJlfMAw2w4AM/ZkTibHbgArsJj8/RCZbpAWSi8RroZ'
        b'B2tckGpOgQoa8CO0jwgQvGwB2uYHhiTABzo8j8E8HAZXBI7/Y7z8LyBszBS+4Y/h4UJzgnukeUXZ+P8w2GuYJEj7daYWaZv9fxFpTzJZjhby1ZNcytpGHoPQdUdehwTh'
        b'WJNJysh8GbkgYG1n38FoXoVQrK1je1RLVHN0W/T7tr5PbH21T4AuUtmGoc/4HPxArJfSqytRsWrczlmxCsE3u/A/cSlHb5V3tNphqcZhqcpqqRbeez21cm63bLFUW3lq'
        b'rDzxwyYY3Fua25DLD4B7jOQXRt3dObTzZdubpbdK1VbhCpZibUe4kqVc2xc+yNI+1Nu8q20XOXeiw/hK1MkA9JkNvz+bwz+X1Jl0OqUrZdzVoyMC0WIpY3u4vdzTy7qW'
        b'zXZrDr8jTmmLftf2OPc6n07vSv/HKk6aG3uh8aHLKV6Hd7OFwmLShnKao6joTmw+1HZokmKbZzHoq0Hvp8+EevXN7/PqLbztrJobhT5P3eYqpV3bFfHjnqsQf+xxZXzt'
        b'4Iz7h/TJrpmr/DPHnF8Of1nyBuNlyauLNIuT31ilWZzZYdQhO23eYf7NJG+mRUkBpQvQmkoK8fcd1N+L0s5+gnN6GdEuBH7A57m104I9iDpq2oMw+yc8iP/NeO4Z3nzq'
        b'psVyFjkpYge7F848lQuPwv7EYPhSILjiz6B8lnMWZ8AB8moebhbswM/LwObkkBAWZQLbY8ANJhgLqRCw0tLiBYx4ATMtXhw6P5ojncOiqHPLftV4qib7JyvmvDYvdcu9'
        b'LWvUJty6fV+Mff1y7b4L7wZ8nrEhtXtHS53t3T77i03v/cHvW5tBxeaslncPSNu/G/v6fvLnLR/b96f/6SpjQd8JzaBLxlvZdd/99wPgOdW3vbn52BtDFW6KtDce/2ll'
        b'1oZ5c9SPtp3nZ37eVJTz2zW7fLq+z3K+WbbpC9l3DU0ff8EVnvlZd1mzSPAl78LniQkFFQMN2w5+DMtHX7fcfvX14je3KLzXld+7tD3hMbfmtW1jbcuuDqk+rnuQvPWl'
        b'qc7f/LlIfNlfstFr62tevz589t62d3p/evVaR7vXs3cj+yRTfZ2rWmtee+vXsfxDRj/flvrXC8weC8G6plAv/9Wr7ne1dXK+7Tl05hijz8c418r5tZwhk5/mm59Q3O7z'
        b'rsl12nTyV7/lNvisFkYsNsp7s9wpPe3lOInN3Nas0FNdJz4pjj/rfOmXKW97FeZZLHb88o0/xy93yPEc5da/6bsxKQRKJMd/dt/m6hs/3Rh747WoIcanb5oX/CW+yGtR'
        b'XvIZjTh/56vr79wVLhllLXlz23jq569sl3h81WpcpigKW33wja4vhMOOkSsfv62e89r8IefX37SNTDwLxH80e6eyMKrmy6LsFV0P5Mm/FW31HPCK2X505dzy7gfC90o7'
        b'x+6mvP7zkdg7z0L2WAZcifHL+mj4fmnTw5+qKpP6HrOiX/WOfmwbvcr17O19URfXrrG8xHptffwJ3zOlwY7f3fnsQ5fEqJYhrz9lZIgCuhLbvS4fXbXhXFa5/bVlo7dd'
        b'3rVf/KuFv99bHLV2rd+WDffc1875ck9xsaamLNtC9enbw2Ffe8GlL/34i/C/aL7ddTC4d53Y+nr0R4+vOgzINO+tD1C9NRD2dRR82vbjL/z/cn7LgbcPL/oqJPHr7z86'
        b'fPe9Pb37x77scfti0t1D0TQq9TCVfP/e/rfd3zMSZ1xvCv/Ef77t99kff+C3K+0e+1ZCyuOPHU5ej33jsecbl1WbVnq8+Wn497+DmkM33/d7q2jq8ZLGx13fbM41+9WD'
        b'1+8eOXT8DyEXNt9eH9v+he8vLr/+3sVM14TLr1za4Dzk++CBRc/ub6e639lUVbdg+A/LMx8c+OOfhV+w1P4Pgg9RxyV7FN80a8OioBGcESFwcgTWIxDEiKRgU5wLCU+C'
        b'DtgFW+BY4iyPPODDUjisF4/A9YnnwcyWaSwDrloSoJJdBVoDE8BtrxkQB2t8SIzUFBx2T8ZYqg61kspB6cZD2UzY45tDgpLg1ryc5JSAEBr+mRZZspj4bbsp9CMZA/vx'
        b'IzMn0wn8QyM5ibxTo8Aglht86E4gIrg+1xFl1sFeeB2exIfD2YsZ4CboAbfpzcyjIZXPAawF8ATGWAimtUyRF6+2bgQdBgFYEnxFDFNOB2AfwaYpT4q8Pegs6Ctd8QNP'
        b'aZxIIwgQ3oYDrjOnXVMQxKUPvNKHXZHP3Uhvd54H14Nh/UJ4ISgRNiKMabSd6Z1YTA+s1jsgMAmfu01Jw0y7CUbXMWE3eAg76djyOTC4ORk/3ovKEGxsCgZ2wTom7Ed+'
        b'+CmBz7+A5Lj/4OV/D0b6GMDIFdqf6hd+aEzJzc4mpjB77/Q3giS38LSvq9A+2BBEmdtPso15juOWNnKpIqy2qqGqw7Nuv3x/h7RDqgxTCnsXnN7btbcvo/NQx6FBH/Qr'
        b'GfG8JRvJuLX7ZsitkJfjXo57w+aVhFcTnoSlqMJSnjq5dIR1CLsWnOZ18ZRJaqeQQUe1U6QqOk3tmKbKXKtat16TueGJ4waV4wZ8Ss+muaStRGXlg98gspExaULZ2Cli'
        b'2uzlK+Urv5k0ZvASGeM2Horgi2aq4Hg1f7WGv1ptk6CxSVCZJWAYakLZO7atbk9vSVeu7F19Of18+u0Etc9Sjc9Std0yjd0yOW8cAebV7SktKUrnvni1XbjGLlzOmzRC'
        b'9eS8Z47OcrNn6JvJpBnlPHfcyXf6M2nNc0b4FF3k5pNORi4Yq2ovcotJO8rGedzaadzaddKYjcuxSTmLVIa9ybiZlcrGd5KFvz8zs1LMm+Tgr6hJc2uUMCYJLp3gkYQJ'
        b'nTAlCTOUUNn4T5qTlAVJ+UxakpSVNs+apGzoarYkYUeygiftScqBpHwnHUnKiS7oTBIudMKVJOZoy7mRlLs25UFSfLqgJ0l4afvhTVIUufrQBXxJYi4pIJj0Iyl/bW8E'
        b'JBWgrRxIUkHaVDBJhWjrzSOpUG3efJIKoxsIJ4kIOrGAJBZqyy0iqUhtvxeTVBRdcAlJRNOJpSSxTNur5SS1gqElEsMg6ZUMLZlYOh2nS69i6A2avsYztN1eTecl6NKJ'
        b'dDpJVzeZTqcw6H6k0sk0bTKdTq7RJjPoZKY2mUUn12qT6+jkem1yA53cqE1uopObtcktdHKrrl/b6PR2bXY2nczRdVNIp3N16Tw6na+rLqLTBbr8whdZsoPOmz8ppvN2'
        b'apvaRSeLdNwuptMl2uxSOlmmTZbTSYk2KaWTFbp+yOh0pTa7ik7u1ib30Mm9ul7uo9P7tdkH6ORBhlYMDtHpFUxt8RgmLQdMbU9j6XScLn8VnY5n6uaeTifo0olMPXYk'
        b'MSlbr3Eb33EbAbl66j6+k5uYzzMPKaStTMrV59y8znlql0CNSyDSKLx55FKbJI9V2CON9L5T4BOnQLVTsMYJP9JnHkQuzWwFQzEfObXnzDvNlcI+a7VToMYpUMFRcMbt'
        b'Qgbt1XYL5avG3TzObe7c3MdRu4Vo3ELkiYq82jR5GlJJJlbjPCu5oyKvQ9oXO5iv4i1R85ZoeEsmmfN5oZPUP3H5A3JJolFN/NeqwWGSjTOQwGhb6PBWSgfZKt4CNW+B'
        b'hrdgkunEc5qkfuCCaSxEpaZp4YwIytG5fWfLTpXnWrXDOo3DOrnpM54l3f0spXdf3KD9oGxk/cur3vBVBa5R8TLUvAwNL2OSKcBU/4kLbjWTgapON49z1jNmmKXiuah5'
        b'LhqeyyTTjuc4Sf3ABdd3RaWm6eCMoFnJmPO8JqkXLy9QwBnu0zzNUvE81TxPDc9zksnlRUxSL15wTS9UYJoCzrCblYILulB/6/ICLZwROet45vDwpuE/en1hmCQrelbK'
        b'83g4kvCvX19oi2QhTcdzlFsoJG1V7ftb9isT+w6pHZdrHJeruSs03BUq7opxrr3cXJHbVthe1FKkXNwnVjtEahwi1dzFGu5ile5DnlVtiFm+0p4C9i4r52mfVbWbYGZn'
        b'/1Mxjn8BIOKdjRy99+oZAEJJDQ6PTGNB7JhI71HaQ20CBsMKRzn+I5d/6+Owvbwo6p5FDJcl/viDdKb0KLpV8+6uMwG/fEfzzgfvPHkn6u3Cbs/j84971vS81HNCyPBm'
        b'OawBR3Lmsfo3mm9Y99ZGOFLtfOas3Vy7bSkrtqWEunu/Gv9SSEHojydeY1762b2NSzqixqPGl0QuYS85FnVsSVzUq1E+UR1LeqM2Rv02ym5JW9TGn7CzOrZE3uuIOn3E'
        b'OfIn1Ntn3bs+dBMYExeNBTvBXfIfoaZj/0sELiQbI1dkiAn77CqIC5YO2+D55PRgeBMXQo7M0XTkP1rDByzQU25DioDrHBfs58GT2EfU+nkZQGnDcveH9eTgSKoPOJmc'
        b'mBqQalxQQRmxmchJs6BD8V3gZjGsn2dEMbJw7P0yvADG4G3a9x2G98D5wCQOxUim1nnDDtAPm2n3qh3KPQOnX56EaltuCN7B2gn7BQLfv+MS/efD6//w8vAl/tPsPtPs'
        b'DhTe2aYdKPobcaB+Ts2878+F4thWp+HfcXO7983dn5i7d+9Wm/trzP2r48fZJjUpR1JU1p4XI9XsIA07SMUOGmebVyfiX70vWomeZJcbcaImqf9L1wJzysyuOl3v/Kzn'
        b'BKtIVDLBxm8vmeCQx/Qm2EViacUEGz9qMMEuLUPZLGmFZIKTu6dCJJ1g55aWFk2wxCUVE5wCpGjQH4mwpBDVFpeUySomWHk7JBOsUkn+hFGBuKhChBLFwrIJ1l5x2QRH'
        b'KM0TiydYO0S7URFEniWVFU8YSckjAhMmYqm4RFohLMkTTRiRd8HkkVdDicoqpBPWxaX5ixdl0w/v54sLxRUTptId4oKKbBF+jd6Euawkb4dQXCLKzxbtzpvgZWdLRRX4'
        b'LZATRrISmVSUP6OZpTiSkfO3f/h8WqMqdBf8f/NKlzD0HOvZf5DEWDMYMhZWg/9/uf7btDk2nK9Y8GJ8qFd8LGLCWN9ydW+DnbDKztZ+11qvb10KDP8bcX5JaYX2AEqa'
        b'gItf+ZlfmofmF30RFhUh06vQLmn87AS6b4JESVIhxY/JTBgVleYJi6QTZvqvXpTc1C0DekHgCf+WG03/N+XLJKMUPoWDZv0AukyyGAwGHjx7ksIXC8rUvNp4kn3IiGE3'
        b'Seld4ywonvX7XNcnXNeOJDXXT8P1m6SYjAWqoGUvz3157iv+r/qrgpLQZ5xrNW7iIA9SOYarTSI0JhEqdsQ4ZaWirBROaspFQ7modB/Svf8Dpi9Qlw=='
    ))))
