
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
        b'eJzNfAlclOe19zsrA8MmoqKijsYowy7uW2QRZMd9NzDAAKOss6C47yCrooBsKouKgIjgDmpzTpKmSdukaW+bkuY2Tds0bU1u0uW2N2mS7zzPO4Mspsv97v19H/wYYJ79'
        b'POf8z/+c53nnl8KQLxn9BNOPaRm9pApbhXRhqyRVkio9LmyV6mWX5KmyJolxZqpcrzgm7FKa/LdJ9cpUxTHJUYneTi89JpEIqcp1gn261u7zew5RoSHxmqycVEumXpOT'
        b'pjFn6DWrC8wZOdmaCEO2WZ+SocnVpezSpev9HRzWZxhMtrqp+jRDtt6kSbNkp5gNOdkmjTlHk5KhT9mlYV2aNLrsVE1oVJj4R55FbywwZKdrknXZuzSpOrPOIc2Yk8WH'
        b'WxcWq0k1GPUp5hxjga8m15KcaTBl6FM1yQW8fJXemKXL1oTps81GXaYmlHrwd0iZapXGdPqZRj9qJpEMeikUCiWF0kJZobxQUagstCtUFdoXOhSqCx0LnQqdC10KXQvH'
        b'FLoVji10LxxXOL5wQqFH4cTCSYWTCz0LpxROTZvGJak6MK1IOCYc0OxV7p92TFgn7NccEyTCwWkHNZtJ5iS9DK0sPsW2JVL6GUM/Y9kk5Hxb1glau/hMFf2dsVcq0Huq'
        b'ZiHJtzDVJFhm0psL8draDXgMS/BUQuwaLMKyBC2WRW1Y7acUZofL8TGc8kqRDNlxN1v38f/kGtPcrCuRFElpJVJaiYSvRMpXIjkota7k+NCVONBP3KiVtIkrOeBsJzgK'
        b'gmvg+D0rVqomCfzND7fx5QmBEQ2ejvE68c2mefaCK70XuGDMkk2JY8U3leMUAv3WBC7IXRASaRGuCZlsuIaoifI/uQnBmvBPZ/9BemdOQ9YqIdOeCmpCz0u67QSNJr4g'
        b'6GfGLDul+PYHC/7ocs5F4vXWto8lX3mE7asTBgSLPxXgJV0GCbQkYI2XFxYHRPphMVyLx8vrvaLjsMLXP8ovOk4iZLvYL4da7LeMpyZwFC5Ab0xUZLZvlJyWIYF6aJda'
        b'mFJh4xasNeGd3UZzHlRILSYogSIoop3YLpsLVXBVq7BMpHrJULR2405rRYtRKtjDY+lzUDrd4kGlMYvgoURvK82TCPZ4Qjp7dpDFk41+AToSsBbrbeV4U6AKp6Q+e10t'
        b'U1iFXmzFKmiIs1WYK6fu70jHQym28xp67MOjeHO/tQLexm7WxRlpQCZcsLizdRzOnWlyJFXC81CeJEA1VqRZ2PZmx2CZyaigghKoCBagKGARlwnewI4Mk9GO/iqD+uUC'
        b'FEMf9lkmsKK22bE0EvvrNJyFYoHmcR3v82YSvAqtJignXcAm6PUXoBELvUUpX1TAIyoiM8Fm7IMOWrldlGUc66cXa+aZ8tgsKrAXbtFoE1UWpuxrw3NNeFNJBVVjdQKc'
        b'Xh7Ml0OSv5JgsrAGZ+b7ClASDafEafe4Yp/JiTW4uAKOC7THpfBAFMFN13AT9rKZ1ewxUF/YPZ+PvnElnDRBKavS4A+VAtSlodiEtvrOJJOazfhSMA1TC1f2cRE8jw/h'
        b'kmk3mSRWQx1cEaAc6+EebyTHy5kmF66JUGovwPkpcIIX5Miex14nNv516I0neUCRmU/AC25AiZpvQgdcWU1N8H6ohUFJwHw1lNC2SVTTFgrQNW8WVycoxAf4yIQ9bD8r'
        b'8RTUClAhhztcE6ESL2Ax9lrY5JqhC8sEOAdn8JEohNt4fasau9lYN1Ytoy1QLRWXemsyXDHtZkutjEulDcAzU3mBFB94m/Aum3atwzQBzsA1J17gvhlumVzE3awbR1KD'
        b'wjRRP5rIoGqwV8XKWtf6CGROfXCDTx1vkqa3UBmbwFU8iSTuC3hjCt+8aCgiReo1s7JaSwgtirS6XVSe8rA07HVk+3o1Gc6TWsEDaOYa7Eh7T0VMFm0rF1N36xy5VGO2'
        b'B5Je3WQTbxkbyFS+Cx7ykuUbSS167VmLLnhM5gZNDjJeAt1wDY5TGZfP9lABmrfFiirapmfD2DOpdkN9igAtch9esgsOYznJm+tc/EYmoesHuYSmOKbShkt4iwq4S53F'
        b'zeASgkZn7KDJ9bKydjzOlK5+7TLeXfREsnf6ZpZ3fS6pyYXnsEPcotIFRto6Pm2sCKBekg1cAutfkKtV7O070ADXBbi8aj0X2j4XbFBjD+vpNmnbbZoAXNbyJnh4KTSr'
        b'89kyr6c4kGar5vLRd+DNF9R4hwntJpQxxW703MZLEj3hBpWwVfZOwE5SX+wO5MNEwmVopyLW2e1krCZxYudEXuQ0AxtMZja1IoKPkwKchGN4U9zRRke4ombehaCmH1tJ'
        b'6yXYzBdqhw8D1A5spPvbpgtwBcqhiEMl1sEJPAElCwh4bkMp9EOXQpBhsyRhrZQrP6nXoyVQko/naPLFSjuFIM+QwBHDBAtjB8uxUYln4Y61QpDYi4LAtEw6IWCvVmZh'
        b'Zqv2mGRJwxLa6BwhZ5vOQh5M8HTeugraYmiyyUKyAlu4ceIFuAvti1xilMxBpqbMtsyidzPxItzFs1i0dDV0LIBrCl0clGHrzjBo2RonzDMpGHalW7yYCO7YqVhNVq8L'
        b'q/Ac/3MedGCVHHs0gieWye3nEHp4U2ULtMJ9sTatoI1Vj4Qua+3nsUHwhIdyGelil9j3OZcIW9/Xh/Tdyfq+FEF9V8qV+7HaomWVj2EhHMWzkdBJMx6sHcSGke9NFjz9'
        b'ZHiPVPgm73oSjV87OG++PujfqdaQB2nbiG3asUK0xk49LdXiR5Wfc8eLo9cIN8ir0K928muPFsoFP6Miz5UAjLUIUIUOzqRsyhZZstg/tGAdiRFKSIqReE9JKl0J5y3P'
        b'Uwtn2sjzQ2ZfPluUjXytMBl7ZWR996HNsohtWenySUNkWDZUOo9WcQG1xbFuOuOUyXFCHtxQwf0QqLL4smEOzs4hd3aWdW2Tkozg9hQt4mQaqVKdMAfJyZXj9cmiWAvx'
        b'vHrYJog71s724BaU0JadlWG/i4TXjo2EnmdpA40kJ/AqpS0rlNulYYMlkBOOh3j6afWyEUNwFbr1vDBvn4L2qgZqLQFs+edX+NraPN1mqlwmLp0axWGXEIQVCri0c4/F'
        b'h4vMH48P1zvrxFh1vIYXaWLX5Soo2sa3b9+LbqOGoIad4hRJ/WbraL+hWGGCrnQu18QwqLc1aWdNCEILmEzhpAaaN8KxXWOFOHxoFwQXV/IpkTe7vn9wEJsC4rGtXgv4'
        b'pDYaBBNcVGHpPJW47IY0bLLV7xilhDSnORFsTtU0p3Yo55OCe3CenJht8watOExDCNK2cSzcWiAk4AU7f+jcyhsYMic+VdthA1nFdoRcvz/0KXYKOg4U8+DUFGuL9hHG'
        b'f2Cf4DlbRhzpfjBXja1wjHodYp7iJl9nmnEinZT8jozg+iJe4Qw4C9lww1Xj2gjVeLRPmJengPOrZHwuC2mGF4dqNvtLNP9lRPA8ZTK8cWgMx6El2DXG1vmNEdpAjuA0'
        b'aUOL3A6vEIWaS9XD09CKFY4Zw2fD28mhxzEuZCVcnyUYsUpFhvzgIAcZrEojdjASZMI0CrgOD0h2lxS0XqJNfMV2ut3DZT/Ufpi1qQOEuVivIGM9SfgYyPmtHd57qqhl'
        b'g8pHUVi9kf6T0cycds6XrFHYLXKhcZgiEY48hMcxHCCobtEMooHDtINj/Foos5tO3qleBGIia054Wvl0ghzReG2GZXPhNkGGwotvNMnqJo7a6SC+BrgK7bTVN2krEgss'
        b'M1gktl0+BDAytw+iniccJe2xYL0IQ6f10D3MJp/ursFMlQtlxCc7sJRHPMtM456OD8etUCplUHqXtCxjmmU21UrwhtbRCtnFptl9kKp20yzxwURRAm1Es85atavdVhtu'
        b'iQDSEcnV65aDju/L3Hzzs0Cwa3CH5PBYRzhbpyDeeArOigZejSc3DWsmzqftaau9i4U5mxRE+jvgiCiVe3AicLh9MwWz2ffKIGF1rN3iLDzJR1BKxRU8VbHrIxZykIBz'
        b'LjxWEGm9vc4yh7MVPeE2a4RnYm3tpCnWgVxpnHsLxkDRfAo3gx3i8ZKeS9YDO6eN8sRW82rCRsFTK8O7u5eJ6z4yDu9/I6BzHX2EDwjaLIpcqHfiu+GNdyWjd46DwhkK'
        b'bCfjfRn2YOcLXEjTiQ6XPBP8WQMPLRn7Y7kzdifydMaWzftHqy4jHHYq6rdLhl1+6/kctmN/4ij8fgqtzfuE1b52C+3MHHCwAY+tHOYfhqrPpTRRgR/jUXcu9cB1oo/u'
        b'xLOrRwkderdiGR7fiS1bBeMu8u0ridMwr7VoeTjcxtpnsjGFm9W3d5JXpHEr+DhwipCoYxTFesorGLe5Nof5lbMK8xJsFXfsot3UZzv5QU3dDPU0VhPh26apfG7Y673r'
        b'6frLjBROjbQORd58yWqV3YJ5WXzbAgxjidB1jKIe0KlIJhHECUETFARQN+bz3dixLX6Yc7SKlzNF8oAk3x45McxG3jXRW4oun7EC5oz8oIs0opjIwOldnJkdgtp5z1Bm'
        b'pjx7lwieS2X4MD+A230QFC0drcnDTBhPLyHBnFVAw0S8pY3locIEqPexBRhHHFl8cWU8D7HciUxVm3goeQpLWbxSCEeIBfL4+Thx6TsmvCXhKYwaPE3x5Xi8ZI35x0CX'
        b'NVWC7VspbvSaLBZcHz/eBKUsqL2wcYFAoVbJQTGS6XOnSNjIIplCClgpGD8+CcRIBk54OdqyKzfyqG+8uplHU7pgLLRmV9Yiy3dQ1FkmxoZlXtQb9rCNL18GFJyWkGGe'
        b'5CNl0cwbTQ5Snsa5C70CVOH9PDHovkGBlwmK2Swukpd7TBNMgzrebM96PDuYsKnCFookF2IJn0fswUUmZymPrK6wNtVwhPwA69DJF1oGEzld+IBlcrpIgGxZBXNybImc'
        b'XUCR24Xp0GXNZJzHU9ZETnQGyyL0w0UxMVM9L9iWyYHTXiz9cgKaeG9eUJJFRUwYtbI9FLngRXdxTZ3kcK9Z0zzQl0yioFWX8ZEOJEGhNc+D7VDKcjP3ZvGSTVuxxZbn'
        b'wZPpNFIS3ONB79L4eJMYWDdCcyIt1mU2TzJBWbRgzfL4OVFPs8SIN+bAHmtChALQFrZHj7CQz9ghaJdpt4IvpSmKmlM8XsebZO6Gm7ZkCYXBLBfwII+XzHbFEiphatUA'
        b'V7GQljlxPu8sl7a+zppIWU9Rfd0+fCwmkmZgucmFtWjFm/60n9FwVFS40qksfSDmV4C2VID62L28KE4sEbMrd5xYcrENH/Gi6dhCcZ41u7JKybIrj+EqD5vnUyhbi72i'
        b'QVyCU1jDNKETKsXUx0UZuZFeR7aqy7PhMI3mOpV3+SJpRK0tLbOIEffGg3hVnGMvcdYaW14GOjbSVJ6PEM2vFxvlNBpPTFyGTl9aMx6m6I8PdhivL8ReZ1Z2Q5oqUNhX'
        b'aeQl2gXYj72i2vUofQRS2GsqcazjSWOwN0/KZXuU/DBUJGIxl+HMefFUouRb3mQmXZiEh3lvoUsIZmzpoQPuLD10ei3vbRqRuvu29JAXnGLpjBshvCgFzsywJYfwDIVk'
        b'0IyN7uIcbuEJe1t+KJjcBbTAZTtRjR/B+UxbgoiC1oukFvNoftwsjmGFkcq44PXzWPauGlp5s227CMJ6ufI3kZcnAzxLEV8dF6GMfMB5mv5tLnm84M30v4R8GVvabuwL'
        b'x14nJo6u6bkCXCIT6RFncgbvUHhqzUlhC16mFWSOEzNzV+GRAxUpeOqnDZvYCm5Br9jwAsn+2GDGamYB6cBqeCCuvHLy/sGEFfZmMp3rdxGxrIfAq0KN3Wya18diN1fi'
        b'x+LKm7FIYUtnxWEzxxcR1F1puTfUKtbo9t5QAVpnQ7eoHBegdYIt1XUeWarr0CYRaJvx9nK1masoXnMjWQlL+DCzyK13DCbBCuEMVbVEir2VBkKRNc+0H0tIoVywmzdy'
        b'VWOvOp91do38yk0Gs5VWvcHbZOzt6nzWqmMWM5SaF8eJMjpGfqbYmlMjD9bIks9NOWJZDxzPsuXVKO5geTU9FPLBduE5eGzLrDmSv4WL6VZfhPeg3WkwszaXNJEIFEOy'
        b'ELztqnZmcujXkmW1ZVDox8VwAbsPqZ2ZEj6ye06A9gyrI9qER/eq8aYouUoyhKbYSN7TbDxTQAWsxb01ctrz/NX8/dxkPKy2ZzrUj2eCBbg6IZWvPykaGtQWnsTG02SE'
        b'NbRtpbzFC4uxxprP25ogwPn1WMnfj5i8V23i4sdbkWyG1XpRAe5vg4ukH1w5HmLNeNro56fwoJEQ8UYcI55QZE3lwXUr94MinvxLy5ND73oo2SBs2qHEi8tUWjnXYgc5'
        b'6UVJLLQERmOpTCDgInYdQ2ECnyEBb0UMFseGEyJIX5QEzM6yTKb3fYLxfgyWBzBXgmU+WmiXC46usnHjQUw+Y7nW7BNPUPXIL1IuyIMlNJWL5ogUduDFvmgBAjuT4sdl'
        b'7Dy2UChUFEoKlYVSfionK7RPs7eew8mL5MeEA4q9yv1yfg6n4Odw8oOKzUKqjJ8oyn+xhMTuoBnyFcZOVNkZKj9V1aTlGDX5ukxDqsFc4O8wrOaSXJ1Rl6UxJOuyl2jW'
        b'Z+jFBuYcTbJePJfVp/o/q0GyIWWJJipNk27I12f7iq2sZ7canXGwrcaQzU5jh/XAvlJyss36PWZ2dqzXpWRocqiS8ZkDpeRYss3GgqGDmW3TNJj+hXHM7Bja2pu/Js5i'
        b'MrM1MhGtS/CbO2fBAk1I7OrIEE3QMzpJ1T9zbiZ9ro5PzJv95a3Rk5AtOrOen2onJa03WvRJScPmO7pv6/xFifNNsq5Fs86QnZ6p14RbjDma1bqCLH222aQJMep1I+Zi'
        b'1JstxmzTksERNTnZg9vtS+9G6DJN/G0m5N0G04jFDJ7iEmqwk9YRp7iu8RH8HDbmBQ8hUEO6m5S0/1b684KIHzew3wwlnC10bxG2kCs8ymsvMKgF9+3zFIJrkmP0FF/x'
        b'KNdhv4vgOe99iRCY5Ng5cYPAAUJyKJK4FFQRbJJL47wMD2tdxOOVNvI6lVQ8PchauBGr+MAR2JJn2i1zgEpGFYmOT4YqsUkh3M83uQhhcENsch6vqkSHdRKKmBN0kmN5'
        b'AcMjdqJ2FY5zSqfR7lcbFbvgIYNpaiTz5G+bIyarcym+ncdICYFX/jIRZ3snHlTnyV7A48wvsvOqWomI9vccoZmdwK3YKkhUAvHgS9jJS8ZD9QTsNSkjiL0LzFlWZhAO'
        b'8jOIZlrzWXY6B/1wndFH4iNwmcgup9WEQbfZ6RzFCmytzYzvHs3gffpgm5qdzcEjJ4aihJVJ1hMRpQar1LtleH03A3Aq2AO3RQ97hjhoCfYaFXqoobJ6ojjTUYwWFuvh'
        b'vmm3HVZQfCMwT1VBHrDKGuTMxEdEbrezY082wWLpNq2Mt8qG49OphGjlJWsRBb3icegLhKVsKOhKsA4VMlYEyHPYQyHGbrsx0daRSFI9vM3GWDjP2Lh+qlhyGqsmaKUi'
        b'cTjpoWJFxEuvWAsDCHFZq8mrPNmJ7BI8xTgd8cMAaOQqF7TPTnBUZUkETVLmPFJojuvEyyvw5NxAuT+1Jc+f7KE39L53VTD9kQrPT/x0/vfn7JTNcVW8deOnn3V9PPP9'
        b'5FOfOe1XTbh/7KWoM2tPhLwf2lcW0h6b5Oi/X5jQt9B+cfhr2tD40xNPaFzrrk78SvXtE92fHh7TVHx99zbPbddOJHxSNbfnjXMd6Z5bI/4DlmV7Ptn8c7XbXgfLz57/'
        b'nVZ34q2XG79UfRDXEPzRyve+Sjj5+tkbpsyIJV8n7Gjtcb/5s5jfNn0y69Mns3NuQe3xLv/fZfUZXpF9sdf8WdhrC+v+lD238OoH6/4c8Ofaz9M/s3x2//OKzxs/3/3Z'
        b'iftvfdTV1VI5kPF6ytHYsIJxKe9J74TD2+373tzod2bLrKi7/+ly5M75jw9J3N9c87tFL2sVZs4DHfCWj5+rwivSTyoooU7qh6VLzPxGQRnL96pjsHTpNm2cxc8biwOk'
        b'wjgolKvmOpuf5wSjichfyW7sMRNhvGtxVBEDqiHrvUWufAL0yKB2nNTMNDARSlaxCyzbsc/bz19CAx2VznXKMzPHCucMWO/jHxU2x9db648Vvmw/PTTyF8dM0SoGpF5a'
        b'FhoLI1609s9695tf2LWbz8ctSzPm7NVna9LE+0r+zAO+MODA8TiR/cOqmVYyXDwk+LtK5BKpxF3iLFHSq5y+HejHkf0tY7+VEhW9o5Iq2avE9upIdVhLTwmL3IV4PrRW'
        b'OSBn/Q/IyIcO2Fk90oCcuZABu8REoyU7MXFAnZiYkqnXZVtyExO1yr+/Iq3cyNiEkV2LMTKlN7JrTUbGMvi4F9lK2KmkcFj4pSfNUSpR8leLhsm8NyacyExkHJbTzlXE'
        b'ch40Do9vg0cyvJehIjNnR6kOWBlAcUVpDJVjSTyWJ0QpBOdc2aI84sCTuU3neMXExlMo9JBRozIfiaDeKsUuF2wSbb4fTmYyMoWN2CbSKSxenSIb4nzsbM4nSBi8rSRP'
        b'k1uZkKxIRkxITkxIxpmQnDMh2UG5lQmlERNaM4oJkb9kDnmQCrH7Yzrb7TB+r4y5d85ddCl8MzTZlqxkxkaGdcS4kfcuohM5XEW8bRfcGAkx6vMsBqPoxXP1RqJbWSLd'
        b'sF1zG+5wE2x+mCbivZZGNGTpw43GHKM370xHJakjRl+pzzXqU2glqb4aCzW0daxJ4evjCuultV3FezpNTaYh2agjwjOst02GzExGN4z6rJx8kTzl640m1t+iZ/NDJigm'
        b'J5EjjpTeM8mRVZpii5GifdYQjFFGZOrSNQZxFSk5RqPelJuTncquADJiacrIsWSmijNnnIemrjNpduszM7+JEoUbmKyfMjAiwjpNkJ/ZkkvMysqz+HaR5LxYDV82kPYb'
        b'CJLMqqfDCZJ9vCWHUyE4Bo1OWBTiAIcDHeV4mMhR5xo8siIK6rMN0DbTjeKTY/AYaxbHY8sUOAeVmXZYHYa3nPCRngL5dqU9Ptq30w/uUKzUDeWeeNwcAzUhjBLBrQg4'
        b'hXdlUng0gQLHwsXcu/18s4zdoovskiRl3t0QJ/BTnlRsh3YWR2v9qEkFuyoYFScRJlNMXrRCfiAEDouE7ufR/F5ehswvyfGB2l1Yb2h9nCoxbaGiNbmvO31njvNhjav8'
        b'W+8t1Xy28NHLJ3/88ofJvp3n/tCWuUf5t/Wvf2fex4Hm7eOdp8c63l3vbjm/9a9/2jFl+WbPhnrPVQ3xZVk7P/Kv2lC3rP6Hvz7nmP6q8cuwCWMbz4Vr7cw8o3MJzm/w'
        b'SfDFYhlF1XvlGyQEG4cpzmT5e7g3NtwU5ecVHRfvy3OxFWo4gQ2sNvmN0hg7IQzr7MLh9jgzv3HXwi4aUAmBl88aqKH1imimFCaslHvHjzVPoloHCHlIjqdiEvyifLVa'
        b'qaCGW1Lsj8RLZnYndCN2L8cSLbRi5aDQJILLGtkGCljrxXFuEhe5+wy5Jj9HUsVORzO7MhKowcoY/+g43ygos4HppFTyn7fk2XByk1Y2Gru/yUdxAB9QD7Fw7pLGiy4p'
        b'VcmdjiO5GqXEjZyMSmJ0eepkFAMqm80O2FmtT/QSjuzFidWRDpmGzMhuqBiZlxCrce/BOvzREO/R5TbKe9yhIPu0uGK8uHjIotmKN+oty5noymSjo3N+Wgg9UIqX5XDJ'
        b'V7YjZh6U58F1uAIPHYRkrHQiR9EKJ0XaWgNHsFWd74x1WCURJET5sWPbDNGxUIiA59T5eXlhrKSICOBavMopf94GaDbhHSKbJ1yC5IIUKyXj2YVDkQV2LZtnCjLC4UNS'
        b'QZIjwN1sqZgChFY4ps7PX3VQSd2dELDOHEFOkIUDL2KJmbmw8R6iAwufIrq+fhqfJwT68obmA6BuGZ/hTmjC4z7kM83QLxGkUC4J2wztw1zfYNy1hLk+GXd+4iVdaaEq'
        b'TTXoAuV/1wWyZMBH35QM4BD6j1MBHIcZZrPq/zgR8A3xOWv8/zw8T8nk0zLpzaMD8hETZHLJSUmxkMvJThk9UVtIHr46RBNGvMzIXNLKf/r6+aj++HX0IXPTsU2x8Lv0'
        b'3uvC1nv70q+VK9mvsIS1c+g3Tc87NCiUF4SFefuO6nHImijcz3lmYoEtkss5V0wnUK+pzDsW5I4QIPvakMva5i/0X+S/h/f+TPazWzec/jBywoYY1V1O7mgi9D+XupAI'
        b'z0pdOFtTF2pfDyFQeMfikJS0vz9whpiMuLvKTZgpdEfKhKTtP/TIFriBJ6Tbs2wG+c8rwhZhC5xJ45Cw3XGr7R63dGyas8Q+Ec7yTjySnAVPIWOaJDDJt3K1hTCVQ0vA'
        b'LDw/l7p5jN3CHGEO4VMl7x7LvcfMlRPU6IQgIQguQgPvpXz7GEEjJMkccpMcGQZTLwyN4fBquEvdZPnwTk6LNzEPYamRJc/3QpewWlhNoXQb7+TNZWrBXYhcpHBN8vVT'
        b'jSN3fuS2SWG6y4Qx8Sd+cUudjwa7NtbuGB8SM3nvm78Y49v61tvJbiVxXuMnjb1elNp/XOKT8FLeosLeyCsFX4+ZkP7ef94t83hp/LTcozt3NUkuFk4JXfaq2/c1Gxta'
        b'/U781vkDh7arbZsSX8p1dX+SJ+TAnHbpcnvnzYlp1S/rZyU0jU1dJ7y74hOn2XW/+9C9p8v4ux1fbuxf21Aw4YXeVbr1ful/aQ396R92bd9b8tWMpld3pr/96+OnPr60'
        b'/UefdclfrDm949AHvssW3jBoldw3T8TuleoIeEzR54jYEyughceU/tgLx3z8KHBNgxu22LXMw8zAd9Ok1VjCvFM5NOI1QVDOkzp7zeWkQBZsicGyGHiQMRhsugTK0qFi'
        b'H/fl2VhsJLdVqLZFtXjT0dleKbjiQ5mn2c4snmj1BbNolkJZlxXWYNawRysRvarqXwpKRYdvL4agBMPc3fuL7v6QIKcIVO7II1A38sAUV0pZDDqDfjysP45EAtwlxrFD'
        b'aMDTyHBARng4xPv/o6BSNiSodB9kBKzvPwxhBKcnjWQE0dCzbjCeTCBnqRTG4HFiZ4UyKF0HLVqJmPU6vhtuY0lsat6QxDuR4LZhz68MRoTsyJ9cIbnGNNngEyqSb3xC'
        b'RcafVJJ//mQYXKwV4eYbogsRHfWiF+Phgj/3g2k5mZk5u6nWcOjhrsrAQkujXmOy5ObmGCk8W6JZGe6rCVnvqwmLHOFf/wcB9dlx5bBErnwUGtrF8/BAPQ4qGI/2IXvC'
        b'U7FrsNtsxFsys1KYAm3yGdFYbQmhalG7wthTMZsin8b7fhsjfVmj0qhYLI7aEIklAWsjxVifKM+quPXsMSQ76HOCfiXW8UsvGri0nXeTiz0zsMm8kTUik5NAZbgDXIiH'
        b'8oMO0E4kKxEO2+mwR82hbGGCm7B+WxT9lbT9QeJuwXBgwgW5qYD+/+KdDfNLljpLQxzDGksVzS2hdeVhuW4Z2ufqqrzy181ymmYolyzUK1fqf/of95u+s6P6Ou7999bf'
        b'fpQ+a+3aXvn2K3/enzvf6UngZ4WeNcGvdBx/9PzE7eVf7qj7W8Zbi6+n/THeu/InB95K2r/zlZplyv8KQNWF7vv7hc/3TPswK0ar4FiUAGeIGw5HIpZkJjCSUbTG7mNh'
        b'cTq0Dc+E8SwYCe6yNROGl6HUzG7qbN5A/LmXieQmlvphURSWxZE0o+Ly8Pxz1v5joMMOuqE2z8x8ggGrZBTDSLQ+gjRfEjL2RTNn4Y/znGxDuhidXLDnYIRjnpNS8Jwp'
        b'lwIhqeLv2fk3QpFdut48CERTbUCkVRHMuPLYw9kKOg70v6vEOP4p8MjERNRTuBkV+EjEGhxV+DE62b3JTUSVw8IvXYfiCgNrV2h0ppXjPQucEmFFvUZKsPJA8mzE8Lci'
        b'Rpr0n8SL44QX7cMMal1upsHMmPNTSCAmSEbJ3k0z6tL5mcwIM7eBjE4z75l5hmGVvcISNsSvX7uFwUV4WMy6DXG+GholJjEsgeNIGC9PjN8QFxq+Vvtsa5daVz7c2pXi'
        b'w3f6JUr+8N1pB2Pmj52VgmWxwO9MlFMgNQQErGacNoPFLliphWsOUFtgtVAB6vGkgwrv6vkdre2zsPkZACJMwT7iTQQhxGuaDHHFH8tNzIS3b7r8+6RYXaQuU1+Z2qZv'
        b'0300YVnSa2kBlVp6b2daZvIToTgyyDfpSdL21za/sRk3ZyrP6ZTf+VGgf9LW11y/+61aifCRk0uk67taGc9FO8gWjzBA6MFbzAIL8AHPLlBsfh/uik7/HK1M9PmSlWb+'
        b'uNNpuArXYgKoqZ+XUrB/fqmHFJpmYM2wcFj6THtwoLjCNCQUd7OZRDAzAhU3BwrDPf6OGUi/wQJYm4XDLOAN56EWwDMQnXgW630ifb3jn8bZ46EPO+CEfBy22JNrZQi/'
        b'Dk8wiGflLF2BR6ICoFg0mUmH5BlQ9eL/nMX8Qi4ZEW4OdbI8Q5ity+KBjc2M2IFmrp6CI+Z0yeeKnjYqW5OiM+lHGogtb2se6oj/v3a+NpMcbo7yeH5iF7zAB3tNeMvi'
        b'4qoQpHhBMgMeSA2vvWMnMbFEwqri079P+ijp4qHMtFjduVRV2vuxMsHjjPTH13pFNZR+s3I6crAmgTN5c/VU2tRzrXHSEJUcUDMFTswxMmj/RtWcPKiarG3kMNV8MEw1'
        b'2U1eO2yHc4TOBM2cL2A5mWhc/h6FMA0q5djIbjE9W+mCRKVjGY+nqf5/pHgsz+E6Ms/xFHhTDXyDdMYCzW6DOeNp6G7MsZiZ/hiyGRjreAZ9GO0b1uGzFFUz7AH0wQzA'
        b'UP0dqrPDFedf09+hTYf9E5KvM2Tqksmz7NIXmJYMV3Q/mtj6JdZMBamxwaxZb9Rlm9L0xpH1Vq601hOXoVmpT6ba5JJGeBo/DUtCfFPdOb4a79TB4wnvkU1Dg0Kf2ZLe'
        b'H1l1XViYbeI6Y+pgnmVErfiQuPAlPIHCkeWbfeLoTL1K9InmCJYOEAIDp07QB++OE/g1erg/IXqoVyPCat64eq3fRqkQEA/n4DG5xQlYJWYOm7FlvQJv8osP7NbDo+m8'
        b'47EuYwVmDYHZS2Zj+nbBMl/glxnvz+McmD1e7scy2jGbhtJgM3ZHMw4cLRTAYxVchrNQZzh3+ScS0y5q3vl6j1/JS04Q6Crf/eb3jylnZBxNC7Wf/cIZVyi4sGJm5KaT'
        b'7xn8HR7/4JPS2TVVry8OcTsU8ZuXxt3oiDmB3T0/m9Dm8er7AU5+2+OWfxW+Ncj8aNps7byvfzU+5vLNZS2Tt381Zdsn53N/mj9fO/lHLn3EcflDkz0TVnAPiy3Bw+Pt'
        b'RG/uQrEWby2xBr085MV+qJDOTZnI/fM2I96DEpd8vDMVW+HU7jzHPLng7CuFvjA4Yua3J25J8HYMlCwgHstZLPatMYs3A1OmsTQqtE0gjybIF0igf/1wYPqH6XKGglYz'
        b'5yDoYQNBvaPUQSrntNVR4smJq3HKUE89ebinfuZIw4CRtV4/DBiH58eZLw7KJyhkuEiEA+uWWvffTpiMJ+TQho/hETltnuGug9aZPpF4Hk7zRIR8oQS60pw492Zf8qGg'
        b'OU/g56PiJzlI0hRW2JTyz2yQEWxKOWzKOGxKD8qGRMQ/HmYwsTm6VJMmS5ebS/IyieCWmpOlN5kNKYOHfvw6E/9QjkHwSzMQ+phy9SmGNIM+dViXyQUa71ydOcOb5ze9'
        b'2Sm28e9ejTJkG8wGXaYmk+ZCbtc6mWF9mjna7bYeW+ZajOkjs9GDls/scPBu3ZBMIH8QcCv0pRJ/wlOrI9kxUT/0+m3EIvbZD5FwHYt8SZ1XSewW4hmoFq+9HA5T+HhL'
        b'BMlWeAzl7Mpr3yTxMxiOwiXGgqP4CdVcB7NcUEGJNBruw2XaUJY9isDD7LMSSJ8T+J7DTXxsJzjDQ1kk3MYmMcPXrtixzh4qSJ1mCjOhfD6Hkc4CNw4juYsO7f9WfJqY'
        b'rnTbL4LW+zN2eeYfVFgvslSs49d5+p1FIHLE4/wJjdVQgzdGohncWbvaD/pXKAVvvCDHIrgXzHv+bDJLHAqqb3kYYq++6C4O9+kultgUPFz3JjvOcRojGD788iuJ6d+Z'
        b'UA9/6lexPBpDXF/5+ZP0r6Jin680Ly66fPuSMrnpvcMZwd99EH76p7NC3ol40rk74P1a47knoe0F3+2v/Ut9589Xe9VHX6xZM2dKRsIWPRbPr5/25dIYV/cdZzKcXp3y'
        b'yWeqpmTv4qwdVWOyW3weHe1+t+TBS3/c9HZzX8tPunfuffnO2r++k798/bJrqZXfm/mfwU8WeP/tlF/Kfy5r9/7pX/6r4IOFS/62sD3kybgltZun/vFX2/xOb3+joWhf'
        b'+LvHf/Bp8isl91/Nvx3RcGFL9Q/mVxeYXlw5O/tIUMfH0Q3Fu76f8vWHEnzDfvOs0BL7WK0LR6IXsHIjVxRmiPgQj5AxmjfzpGFErgVLfOOZdKOgDBoVggpLpAfwygqe'
        b'IcBLB+CaNUDBa3uHpSvPZvHO50M1tPtEx8VKBPl0V7grgUZsjuDQqoDKXB9/rIfDWiz2pcAFOqVz4SRU84RkBpRtodIiPEUzex5KuV75KYUJcEceOXucmT2ZidfhKh57'
        b'mn/Ain2DKQhb+uFsLo+T5kMb9JN+wjm8FhXnKxWUdlIVdkWK6zhqxmM+/lG+3lo47D30Lg604B3ePgOvefv4Q/t8PiPmCcqlfngtSDzirQ7dwnwENiY8veYDVS78nk82'
        b'lDj6xPtFRcUdWBjji2VaiTAe++VBh/CR+Tk2ePVBMs6na+iAzqG5V7wC5808z86eTqGOyI2kG6BOEifVix6qwknw4Xvgh0ehXElb1CeFMwlx/3xG9u+kTIa4G2cGWomD'
        b'QMk9TqDN4+x15IkSN4kj9zsOPEKUcv/jzF/Fb1ZinPbUE8kH5Aw/BxQcOv+hR5IaWWxo1Ay6JdaVcZhbOu0+kq9j89qDbHdmw92EWBtpF5N8BA+LFdA+3muY6xl9Pvn0'
        b'Q4Qkg+eT/8gBEW///PEzHNAoPv1NnmaIdxnWzX/L0wwbcVh3/5SncXmmpxkbz5/uXgpn8dJTVyO6GaiAlpGuphqPcSjfgSVO3NVgrWQre0ajIounvUzsMZESCbZaXY3V'
        b'0RQgIw7MUOPxXOhQP2OXifWim8HbeFkrtUQL/HGoXjxu4l4A2ZNsFrjtnO/kgL3m/A2qfGc4Ar2EQg/hGJzGWjiZC+VEQ8+MpbjtkYcynT3QcNgN7sdhmyWMjTk7Y3hf'
        b'0Oc9tLsQ6N6xHS9lpuNjTdgiLKSJFdlHwbG5Apw75AbdE7GZe5mGdP4pUJtn2CfFZk0cJ7qeZN14gUSoueeftH+jw0rxzZQx/FOgvLbHJ8WOPZQq8GcAx8XFqbGMX/0g'
        b'Ol2xTkWkc03kvhUcm3l+GovjCJhSDqi2E9aJV0Xh+C6ogl7lXLwkCMuEZXAPO7RSPshXvpy/Z2y1S/L8MGK+OPLZVdzxBj9MStquXuEh8Off7fB87jP9qxLKplv96+aV'
        b'WiXfQhJtM1aJcT9F/dCTxQJ/bIHHfOeXQ6VEne8s2RJsvdewz178mCH27Lk6P09igjrrvYbINPEibDOeDjHhHX6nocDMbjU4wmVxde3QvdoUZKRRxou3GrIieG8bxuNp'
        b'dX6+EmrtrbcasMaBL/ANH77APSn6JM8/jLMTV/1cJucgkeEkigBtFMEhP8CcYnJhU10abZ3qSvHJtwjoXcVmCqUu1pnCvXA+1WWJcM82U+jDO2yuW8TPZLKMMbOJsuc5'
        b'+ESxHRvE5XVhNxTyyVausl3BmGjYoP1UYlpAwOYZ5bp89cN4DHR9YempxtaspOBLjyTJyV1Lpk8VPjrtrJnT4BFpV5n2Wu7d1dMLvJplY5NzXzzy7Q+0i1bNKPnyv75Y'
        b'/EXv3Dffr+p9OHDh1qR/i3/oXbOoZNJzpT9vqTh65Furlnd7S34x/pMkp9b9PzuWcPzfzuceP/nLT4rnSQcWLi/ctefe+8eTY988nBKtvPvbI82vz9v1dnPwpzcfHdm7'
        b'I3TXnMnZG7+3qf7zTjvFe7MNtb01i8NeePLuxYE3tN/u3/SXaqdt8Yt/2TB72fNz75WWvPbEPd773b9FP/eLhOnfnTXZbBe/7sHZC7LXI85VZAQ1G4IXfbEgKzrN/nZA'
        b'07v37lX19z/J6+9o+1PIfHXQ2197/WnnD1+Xz/pV6687+15OiWowhcz1/jB3dcAXl7784jeu71zyC+9YqN884RePNyVMO738S0nyd3etSG/Rqvkl3/F4bp2N2WCJC4sy'
        b'PGeJl2+boN2AJTuw28pubMzmooYzAmiEsu0is6HQt2NYZOi7hXe+EXqg2spsUudMJ2ID/Qv4CW3gEjjl428lNQuwmvOatgzxZtUFFTRaeU0sKf2pYbwGi6bzHpTYgUX8'
        b'jJcd8F6xZ2e8cDuL8wU9dMNZtTeW+bCmtqB1mUqYBr1yYsInsIHHphtC8JoYm7LAVKcfDE2xC6tE2lKOh/cSlop8iPhdEXGiUGznU1g412SdJuMzt/MZ39kM1VqXf+0C'
        b'8t/nHf+dM2MnTkNMKZmJ7EMSOQuJtrGQQ8LkITxEJqff7D9HogOqQV7Cbjd7iLExv8MsfnvInCUakZ88N4SfiFyDs46n5MTun1nbKK7Cuq1kXMXdxlUOC59OGpn4nuYG'
        b'V8TPPKQ4mlgKEZYo3yi5k0KYiWcVS8e4WDhpPJG4b8jtZD+s9oFrXhK8Ol6YuUKxGC7jQ/Hj8VqhPZzdxsIK7MEzMf7+MsEBa6TwcBN0aGXx8RFaSYRWKv6SRBjif+Qm'
        b'N+2kpX+t+96GylNrx4a4nkzPN4ZqGiT9r3zx8hcrwxUJ693HrV791puaSxrXceZNfkc/UZZ9cKBp1tT/+NXcv7rHV153X78px/L11z/54fy+pdvGjPP8j3yI1/ifke28'
        b'tXxdyo9U73VkJlb9/rPUeVcdcpa98crKC3/coPrbhqPBYRE//NnhSb8tjzqat3j6uy8n3XavzW1PUSryatcsfTkppG9f6Iz3z/2l49zsL/706n5DbXX1a/kH160+v8D3'
        b'B7P3SpccW6JW/bol49V310XO0UV7XS41erfNDB33bz8KrPgv36TpJZu/61a99o2g6t6jVZ3J83dtfmPJj3uPlP3o5qnvZep83n3n+875PSXvPdEF/PmhxX7FF++8KZmU'
        b'du75xa9Nd/5h5NhVi16fU246enaeqfiHDU0negcWr/L5jcVypOTWD7o6nP3zauPf2513osP8Q5zfJVv4p8yWrua6T34968Cf5n7LL3vua667PdJW/uZ0fsSpvJp9e2Pu'
        b'/rju3psev1z2/vRZ4yvS6sbu7HxlzbXVW+cVd70aj0G+8zfuit50KuOVlIK4Ku+g5Vc2Pd4036/w69v2U+u9Z/j+ev2V4riq6vKgsr1NDx9nwbVch8bIBaHLovZGvqu4'
        b'c2t5/rWPe79cM23sy7OP1d6oC/xDZtF3Wj+4OmtXszKhoPo538Q0Wf7WWS/7/nj6S+5vFjQlxPzufuKdt86+2PeO87tjrj/8VVVfyIdXzsdHx3ncCWjf87367wT/+M/f'
        b'zav6979V7+76jenhX7a82fHQZf93C6oPldfc37bod78Ye/G9LTd+fygq+uCuGZk1P/113V9fL91341u+H1TMCs0/cyW6p+Fizv7d9y9NfO3rn6x4O2J7tE75x2jvq5qt'
        b'4d1/WaH6eCzs7qQolBmEkxTZFQkihYugHmsFLHfaw1N00+UHRp6BFeL1RXIV3MjggLgK+qaPxENCuctSGyJ2eIkZt2vQn+0TuWzO05wT1ObyMeDKQo8YgrqDBVjMkvkK'
        b'QQ1lUmzCGmwV/cUR6IfumFhvL6jxFz2KOlOKrTOIBWq4v8A6eOzEntmEigRbvFxhJzgrZVPYZUjGjTYsl1JJMTmKK2SOpTJBvlgCN+EBdvE+xkEZFQ4iNsdrbIVLDLPh'
        b'It4282Dm6n5oGX3iblw4GPCemWGewVnwePbJiaOv82DDTIoqG/EurxaagBeGn6azs3SsgLPieXp/sHiSeBbu7sUS3ygs8yNCrxSUL0qfw9N4gZe+CI8yfaL9QuOxKCo2'
        b'ngnvphQbE/Ey96Uh2MkfIcWKHQuoMXe2arghxXbohBqtw3/Db7j9Dzqh0T6Jndn8My/cHakSE7lDSuSeyIGd+4yXSqWSeeRN2LMyblKVzF3iLJNL6VsplYjfKsV4ifjt'
        b'oBD/t5X8//WtkrpJ3LgXdZdJKZL3nMtievdJDlLmQz19pBLPCVLJJFf6UUslU6dQC4nHVPY6NchNYpxpc91a2YA0MXGICx3zv7N5EuPzg/6WDc7s3sQShsIT/6Geltm0'
        b'bs1CZq1rlOL9djjF7XWibIre1xAY/JLClE6Vqj74tynfmcOuE0b84lDahJejA18Wxmw+/35jP7z8+ttuSyq//e/SnOLVBwIKdE0Vs8q2fvz7FfWZt+af+PrduJs/3/6k'
        b'2/vg5prjr61vuPfW23mXf3My79sFgZ/OfNgXeeY3VzJ+EPObAtn8lZPkLl9q7TjM4OWZ07jzT2AAEWNHdtIj3bgV29J8eFIMW0Ohkl0MucnqJPhJsRYfCmOwXwZNeH4P'
        b'N7doh0VsWXA2gz3PXRpnxSE32VSshxsca1+ch1cS1DFRcd5xdoJSLlV54RnOaTfgYayEc+wRgwCKVNYJ2GJUmVkwtCsIi5Lxqk+0QpDECHg+a7n4sFy7Hdb7JGzFe7Yn'
        b'FqidS4ZsJ56GY8MOM6b975ns/73ayP+ufbNUitW++QMJTowlircgVFJfkXcuMM4a1PXpA7JMffaAnN01HlDwezED8kyDyTwgZ6e1A/KcXCqWmczGAUVygVlvGpAn5+Rk'
        b'DsgM2eYBRRrBCf0y6rLTqbUhO9diHpClZBgHZDnG1AFlmiHTrKd/snS5A7K9htwBhc6UYjAMyDL0e6gKdS8zWbIGlCZ+yjrgYDAZsk1mXXaKfkDJb26n8Gck9Llm08CY'
        b'rJzUxQsTxUuYqYZ0g3lAbcowpJkT9ewRrQEnS3ZKhs6QrU9N1O9JGbBPTDTpzewpvQGlJdti0qc+NWhx5dOM7CFCYzB7YZdvjOxjnYzsroWRHeMY2bmEcQF7YRfmjCy/'
        b'ZmSfaWBkGQ7jC+yFnU8a2aMxxoXshV3PMy5lLyzTZGSHjMYV7IWdpRtD2Qt76sLIbpgZ2ccLGNkHMRnZwYCRZW+M4exl0SAosF1yGASFv0YOAQVe9rnK9pDkgGtiovVv'
        b'K8J/Pilt+Ae+a7JzzNYEW7xWxR5oTM1JIenQH7rMTMK7WVYNYoe39L4DbYTRbGLn9APKzJwUXaZpwHHoQ3HGVTZRDnkR1XCZ+KnyL7D/eLaTORSVqHzh7gyqJf8HxDcz'
        b'Rw=='
    ))))
