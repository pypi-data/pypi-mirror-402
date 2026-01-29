
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
        b'eJzNfAlYVFe27qlTAwXFJE6oqOVsMSo4zwgYkEEFR6JCAQWUImAN4Kw4MYOCgiBO4IAoiuAAipK7VobudDpJdyfpXDrJy9DJTd9OT+nO153kdvqtvU8VFGj6dt/X73sP'
        b'vjpVdfa89tr/+tfa+9QnwqA/Ob2W0cu8iC5pQqKQISTK0mRp4lEhUTTILyrS5JdkpslpCoPyiLBdZQ58XjSo0pRHZIdlBieDeEQmE9JUCYJzus7pm06XqOWhcdodOWnW'
        b'LIM2J11ryTRoV++2ZOZka1cYsy2G1Extrj51uz7DEOjisjbTaLbnTTOkG7MNZm26NTvVYszJNmstOdrUTEPqdi2r0qzVZ6dpl0eFSR92Wg2m3cbsDG2KPnu7Nk1v0buk'
        b'm3J28OYSwmK0aUaTIdWSY9rtr821pmQZzZmGNG3Kbp7+nMG0Q5+tDTNkW0z6LO1yqiHQJXWcg0Qm0Gs8vTRMKll0KRQKZYViobxQUagsVBU6FaoLnQtdCjWFroVuhe6F'
        b'HoWehUMKvQqHFg4rHF44onBkoXfhqMLRhWMKfQrHFo5LH8+lqd4/vkg4IuzX7nHZN/6IsEFoFBOEfdojgkw4MP6AdiPJnqSYqZPHpTpOj0ivIfQayjqj4FOUIOic4rLU'
        b'9Fm9Xi6wezPSZyoe5M0SrFPoSxxWYgGWbkrE4lUxa7AIy1fpsDxq3eoAlTAtQoE9eAqKU2WDVMDL3kb8PzjgdC/bsGRFIg1LpGHJ+oYl8mHJDoi2YaUPHpYLvWKfGlaz'
        b'NKxri5wEV0HwnLG+feEn458X+M2vSBR8rKq/7FqdkCDdHC13Fjzp3gxV27Rp2cnSzeUblQK9a2es+GbXuws3CdeFLNbc+GneCp/9vyIRfTTtS/H+TNniCiHLmRLyDp6R'
        b'Za5I9hCWJQe/Z9o6dKp0O873jx5rJwSNF1d/KPtu4ycZD4VewepHCSOGYA2WYmnQmunTsSQoMgBL4Pra6StjsdI/MGr7rICVsTIh28N5sVG0jqD8O6BnQXSUf5RCUKyH'
        b'HkEGZ+E8HLUyNcOm0JlmvJ+Px/CYybLTaoZSKIIimo7N8hDsgQs6pXUMy1e1HIpYRpYpFI+aRMEZesRJ0DjT6kPpYXAduu3peAkf7pQJznhMnJaBV6yjKYNpGT6xp++b'
        b'hncESi4W/aBslVR/O9TusKfDBegJUVAD98UR5oO8fqweindt6XgPDmmxjdVwUgzKtfAxYk8SXDG7yqDnIH05I0ANdOJl6zCWdHIMlptNylgtfS4VoGgz1PCEWbPhlNnk'
        b'BOUzKKFcgJIovG0dyUpUYl0AtSasxgf07YQAZfAYG63eLO0RVmGTGSoUUAW19P2SAOewI8c6nOHY9sWUIo6j2gRsFOA8tuFDK9MxeDgFe8w7lU6sE5XUVu4a3u+teMTF'
        b'jHdU67GeEk4LcAIf2/oNp6BpvdmqXDuKjUGAUmxezVvJhUfYbXZTZcExSrkgQB027OC1QW0iVpqxQzEzhVJqqTa4D7d5IZ+8PDOUCdBNqIINAtRDKz7ghdbR5HeaNSJ2'
        b'IU08XqT68uEiLxQGR+C8OV+eBjRhWCNAhQqLeQppYH2M2YOah6tSoTMBAVxA0AKXoBA73BR4BG9QWqtAE3pkpjQXp8dBu8akxHsb6csNKjUyXErowq6ZUOoq2wrlgkwt'
        b'wC1XFW8oEDvCzdguGw+VTA0FqFRAB58lL6gajx1WOc1WoyTuU1gHT7i4nYas1GCbEs9lUsptmgjtQt6MH1xyMeeLw/hIqbKSTDzCm4E2qIVWMz5QrCGcwDoBTm6dYWWg'
        b'lAoVW80e4rZ0qY365+fzAuNNVuxQi3gPb1HCZYEWVW08l+dBPIQllKZcRnoo4DVqXY5PeCE1PgzGDosSK6FYaqVybyYfDFzFk3AYO1xV0BQslTqXjKW8wjFYFUIpMrwe'
        b'RCnNVB+N9BavMBaObsIOvKNIxBK2mknvV6RLqnAsg1S1w1kWxwV3S6BZabdwIYjT8SilKL1jJeE0Ui+kSa3NmEAJ8r14l760CdAEPf7S8nqCVetJ2CpaCUckpTsZ7c5r'
        b'WzUNH9Jsy+C2WirUmLpBUoS2uaRZHdgho3XQSWktJCQznOHjnYRX4B5LdFJwKbWyUZ0J5RKfNCuCJk8WOlzq97mc1dISKk2K0KhlRmyn+/cFuOKaIK3WK3gV6zTY7rSH'
        b'plTAe9QFvCbNEtwizdXkKfH4RqmROix15rXNztqvwfsKb7b271Aj3tjNS1jcVtN9FVyD05TSQbobQEuYjcdEPbxFaUrS/XtSO5ewAu5yAcWR2jeZLTIsZ7NXJMBxOELy'
        b'YgIKmASnNWaFn58k7TNQDj3SFN0LglaNiworrGwBkA7AY7jE8Q5uYYc7lM7BE3APypSCHBsXQ51sFWHOI96Z8TN8oTSPLGk5lCgFRaYrHpNBQepSq5aVvgAXltqSg3kV'
        b'rRtZLc5QLo6Ejkk6udT+SayBw1TlOSwlE5wj5EAxwbUHg0YsC05wiSZ7lyKk5OZZPRkdSV0YOz9axUxlGi2Wcus0ujk1EA5hNRbBjTlwXanHw5tioRwvbwuDpsRYYZZZ'
        b'CaehgUQ7nU3U5QV4xp75Fp7GU/zjLLiBpxWCNxz3wXKFc5yVZ3bGxilSXoKwZpY5Em7Z867ERz7wWCHHRx5WX1ZzWT5csdfc6lDzTZbbC5p8sEqhIuDu4Qwl3GUTVkfC'
        b'TepyX95g1ohCwKs7fQLk2BkUxnsBF7BuUV+XlXoa3FxshO5tGi2WQvP6ocJKrZMmI9bqT5nnQ435qeHFrpsDt7Gc3WthDQSYlDvxqLs1iNV+F9tG9PWkXJ5C1VPd0IT1'
        b'JEIoTYzFS1uESOxUEcy0KawTWZmS5CG8CN412PrPBKOIJ5jokGObPMI6n7JFTEx0kF75YLk0x7I2b1KWE7GqlFhhJ61e6MJiPMQ7RmM7TmhUzWqW2sgls1QkhyrKchqO'
        b'p5NK1Qsz8YISKtaQGWGi8sNHmQOmQJovPuht0OMD1XLsDofr1qkchw9HPksTrrPcgqcPFiqcllokITFGUtafuTxm9KAmuErM2quEOjnWWGcwhBuZ1KeUlK8bb9haoLzl'
        b'kgBYmWCsVMLFDXjKqmODPjwV7g9UObu0WOYhaT7YqlDD0WTerX2b8IFjGzwvVgVR0ZuSvLnuBdDyNOOJVdZAzragtX8oLawULcIVebuZTOG4FhpJoWLxsVMwdMIJzvVc'
        b'4Ory/vU1AUv1ko7gkcTpc6SOmeGCGsuG7ebdGuZKIqq2j9XerabFfUpo61UN9eoJYTFbPV4RtGTtM6fEY0F62xoO02I1V/JVeN4pEBtSrAFsQupHje5XWt5Q+BB7U5Lk'
        b'FEIgPFJuw2NDOEjAGWzQ24q0DF73aXjMZxqt5NEaKe8xaB3puDqlOW5lWVOGj8H7crwDT1L4YF2IExU6aEY6WacbA4pJqrFTCWeWQidf+24LljnqNftkX/qlOT5yOd42'
        b'QRfviQueNtgrvz1YGzzwsQ82KZyem2mdy3pdkE061t8TEkQNnHTEFwW0u8aGhkPrVMGEp9V4Am+SDWdrgchSSexAjKEJDtMqhSV4ehZcVMKF5+EaV6C0JWTs+kS/mHB+'
        b'0Prhqy0Ezyqhaoo3LzJ6C7HFPj0t71M8fkdOnXLbNlu2ZgheVjrNmzKWT3BWKp6LlvDhtF0r9A6wjsenCfFQ7kRcARr52t+WR6PpxzFs25liz08gJoTAPQIKOLRUwtQu'
        b'vLJu8AwHS11fgZ1j8A5NAhRp+XRNc7Xr5lLstI3Vhnc+cJjUBjqI4PJqj8AZ2YAV6Ti3NXE+UCjHhzNGWiezzMexzs8Go0sdsosMRh+QimHTPslmFRN5qX5aH2+xWrPg'
        b'whhCXLwdqpAyX4BuLLOpV4s9M9yV+uApMPW6Cy3xHKNyZvRPDNWmIq/JPou3HOzFTKxXEvGoXioB8x0o0jmUggcr7D1qdiy0QQknlNDCIYR6VYR1Dgv8TpRdx/oW+OoY'
        b'p/lO8FBCqQLsfr5/NhNXDIBb+2hCoEcJlcsz+FgWQd0kR0hI2DVHTLW14UlNdM4ZAkWzyfFc5hJHIFjC8RaOIhGcwXbYtr7wQbSPTo4PSKBdXCmxZoX+Kbxdj3V2SLcB'
        b'm1WZGwO1Uv1deJnctqem7obU/fNjsEuO7fgkloOg2wI4+0zw59lJ07t9sEfh7gWn+VQnkVqee1qJeSeompoxeEuOt5w8JMtyMWdLP4jPxWtPy9/faS52LuK5J4fnDjAR'
        b'jlKHSmzgitxjhKvWYDbKOiggwuAg/A0k1j7pQ0ciluPRbdiUKJi2k43fP45zFShcOHmAAQ4in8U2YKWXzbzfJOuIN7TWmWwMzcvhxlMUC+8Tab0/QPcCoFpp8SAMZYox'
        b'A474OzQTkOlg6R11/BKBHF6DY5LFvz1rQb8Eygdj3C3lztnEh47IVqudaNqVEgM8Np1c5wHd6/TkkrupTCEhxArBI5VkHmq2cxkroThwgJm0CZnPH/HhEz7QrlAo4YgE'
        b'LbfgQvqz6Aq3SuNpSrBEoZbNkQzYQ7ye9Qy15no0aY/PQjk+Xg8NfPJoadaTn9Cv1tDyvMM6cJRQtRIa1kCPLoZ7LwSQVRvI3XCZaPM2Ji+0siidu2yv2aIcsZgBF81x'
        b'zA4pkkA6EmTGu7JEQQpnVEzdyKsZsySExUwquXvGgiYJNm/8yN5pZigTFy6gz+cFaICuTKmmc8I4s0lhgAJKKKQlPAGLeIL7hiyzSQk1eNgWZIHWyTxhB7b6syDL4VRb'
        b'kGUs1nNHa2g8XiXHXnBDFkWpYDzvQYTkbDZjAz4yu4h5eEXq1+lteFXy9aqxAXrMUKLwWyW5oQ20hGuktLOZWMiiNiFQZo/a3MEWyQ9sDsAqs7sIR8haYz2NdA2USqVO'
        b'QQUeYfEcPOJlC+fMwzre9xE0HpYkHlxqi+cslNxKvJ0FpWaiFV3OtnDOaJR8ulgWhGABnS287yygsxkucmFvngHVlOJkcJJc/1Nai+TXFuPh3WarcrnWFueZ7CsFX7Bo'
        b'tdlNxWDMFubZjc08RYXX8RoL82D1flucZ79Bmp+CnUspwWklATmeo2Hi9SheREbUtsOsEZ3DbCEeLIR7vPlAKMBj5nxx7ChbSGSokVe1cAicNOcr3YdJwygnlSvnVQVP'
        b'wsMsUIIPA22RkrVQIDmUt/fnU4oMGuGMFGU6hUf8pQk4QUvhttlDhAuzbYGU3UOlQpdGYLPZQwaH90mBlAY8iyckRbjmyyIVahELptmDLIdnSKUeDjGyGAuZxmO2IAu2'
        b'eUtNXRuXy4MsFzbYYizYZAsS3vUfhx20DrA2XhJDzVg8z0erNC3HDlfFMB6MuMIauj1JmurCTUEsLEPE64QtLrNWJYVsGrFnIY/LPOaBQB6YqdsgpZ0hF6qG2mp3wuML'
        b'pSrrn58n9aKNcIP5905WuCvFBJrilVJw8RQ0TydbUyHiPWArqV1g/P86L6ekLhzCjp2imYdnSLqVcHckT9pHMFJFSaqNy6V5P4HtUC/p9wO4OJaHiPD8CluICEp22aI6'
        b'0xaxEJECOuwhovPYyeWRAeUsFKTE+4tsQaLwzVwe4zyIcnc4y7F+rT1GdG8Dr82XbNlZHiO6iFdtMaLhwyRxVML5pZQkg0I/SfBVeNw2yTvH0QrusCrJrb4jrb9qOJcj'
        b'9f3wDjb/eE8F93gokaRf5+nF1dYZykZih5uYqJa6fnH6Lt7xwPzRPBrVweXHwlHBy6WJvOK3i1KUbPhSzKdJHcGbEeG+isepiCWV2OJU+6GMz0g0dtNwWJxqCLTZ4lR4'
        b'0YYq46BnsQbbVHB3upTUMNwGA9OxAApZEAtuGWxRrI1QLC1RgvHTGrXKf50UQ7oMdet42Ct06G6NWjYLj9rCW542pX24HQs0FgUe95P0iNgFFktJ7c7wkAW+ZKQNUuBL'
        b'wG7eyiYsm6JxUU3ikSoWWjJCq7RwKkdBgyaPtIEr7XUC13FQyTswY7inJk81nRe5IUBt/mbJGDQ8j8c0ecpEaLDF0Kbu5VOQGKBmITQ4r7LF0PZt4fWo1ppZCG35AVsA'
        b'beZUKR74CCuwiAXQaHJO2gNoHRqpkeNk7Qo17rKFDFG7CbDd8nnCwef9Ne5ypoKkrgJZw3NQxQdinghtGrwjg2YolyR2iTwynrQErkCthvkRR5nV6aSpxtNRvM/D8USc'
        b'xlmchwVSM9fCbYhejtehSGNV4Bm1NMraadG8A4uhBVo0ZgXe8rAF8FSpfJirh0GBxuy0K0AayvkJ27k2UbfgMTmmbSq8kEtJj2mKF5M3T7AnsD2DZkqrhiJb7A5abSwP'
        b'isLxBo/30WpcC6XrhA1bVIy6R+kUvN6RvhFYGrMSy+SCfDThyxO2j1O+RZoJWXI0lsSoBHHrUHggC4IaI991MZIX7hYYjRVBWO6ngxaF4OopH04udoO0LK/hLTjjFxcQ'
        b'qRAUXtCwTAYtY8mlSGX7XPY/FVtsgm2nbJnAN+eUhbJCVaHIN+bkhc7pzratOEWR4oiwX7nHZZ+ibytOybfiFAeUG4U0eYLgfFSn+GiBSO611uEvjO20sr1VvtuqTc8x'
        b'afP0WcY0o2V3oMuAnAty9Sb9Dq0xRZ+9QLs20yAVsORoUwzSfq0hLfBZBVKMqQu0UenaDGOeIdtfKmXb09XqTX1ltcZstks7oAb2l5qTbTHssrA9ZYM+NVObQ5lMz2wo'
        b'NceabTHtdmzMYu+m0fxPtGNh29O22gK1sVazhY2RiShhVUDIzDlztKExqyNDtcHPqCTN8My+mQ25et4xX/bJV2sgIVv1FgPf7U5OXmuyGpKTB/T36bpt/ZckzifJNhZt'
        b'gjE7I8ugjbCacrSr9bt3GLItZm2oyaAf1BeTwWI1ZZsX9LWozcnum25/urtCn2Xmt5mQ843mQYMZsJGrpJdaGLyR6xm3gm/FXlo4KlwrJgtCcvK+0pBtgg1rTFgGpQwl'
        b'iYloN+FJPMVzV6tcDkwUCcs9k7OyFgdIu7n6jR7COnEewWNyVmDSSkHiGCULiIFpSI0NqzmdIiRr0nlI1dctgdM8bVQeTwuDTom038UbQeZ8OVU1j2+mLXGVLEKHzygz'
        b'i7pjlw/fSYO6KJ7gunke20cThDlwmW+j4WUfqYkqv6EaEw3dDG18Fw1KEiR0Py7DTk2unEXpyFARJalNIneYI9zFBGzS7GRJD0Yww3gWWiWmt346AyVXGZHESx5s6y0d'
        b'C6QiN/3ZDo6Z4XuLNzPNVR4ShzmYg01sV45VS3SNbcvNgENSoYJEQqcOKzW0dZi0K1c7UmI3ZavJ8mGbktkxOMb35aCVjA/rhO/zeEvDZON6kGH5eaIDHbwpES9Mxg42'
        b'WOJE1XiWyM10PCUxaijeaM4nOj3Hn5HgyqVwUxLoyVmRxGgFIX0yZ7REoc/r5DxpOzP/PG1GvpRWtk+qaxnUS82sEHkjs/NtmyRQhLVSK8T4WDNDyfxz81sEJ/Eh4+HM'
        b'YoRzHj52tE60iQFrRCnNOo8nPUcWmOtOC9RsYXuxgpBq5lux3nCFq1rIHKfMb2QkKm2y/8qt0wSpA0XYg90hMxTMgsJhqBZSFmGNcceDdXLzl5T+4Y92z359Zpx8pqfy'
        b'zd/9IW2us/ZKkborNK6gM8xlRPFPh9fE73qw/APf8PpZa+I8f7NVudPlRZ2nU/LL6q4/LKr8qic3Ua3x8B6yP1H14KVfx/t+9HjvZ+Me//r6nyvffT94wcj/+NUH//b6'
        b'0KyO0BXP3VkZe7Ui+J0i67YvIk4EfqxYvndb0ndpvy84PP5Xf/nbpG9/PfkD04tVqwyFvaXa3DM+meWTnM9tSZmw/dpQD5+Wn1zxuLR6+08f/fXfFw+70HLw+htvLS3N'
        b'KXnj7YNv3X6rpzTotWMr8vMCat9KTPhtcNroH7V6b9dsLC07Hfvzgh2JlzLq0naMzZ64Y+beb5WNTfHHP1mnU1rYVG7wnu4XMD0yQCR/qIsYsBigXWhh52awHmvxlCYa'
        b'y3Sx1gBfLAkSheFwLQIKFWqoCrVwL/0WMeQKKM3Hdgs5gA+srmpsw7tmJ2EktMvJOeqiNX15qsWba+CJJCzFYt+AQJmgosV2GA6LIal+FnZyIZUYaq1fYJS/ry4QK/3J'
        b'7Ra8h7pqFVt1K3TKXnG6jqmUMOiic37W3e+/sEM43wxflG7K2WPI1qZLJ5kCmQ1c0uvCETmJfWHZzOEMFQ8KgZ4yhUyUDZO5y9R0VdC/C71c2Wc5e1fRfReZWlSxq8x+'
        b'daU8rKSPzEQaL8TxpnWqXgWrv1dOVrTXyWaTehXMiPQ6JSWZrNlJSb2apKTULIM+25qblKRT/f0R6RQmxilM7FyMiam+iR12MjGuwdu9wEbCNh2FQ8InPtRHUebCr/zU'
        b'SnpeAnGaSPJJO2OxgqavUuJFw/GoHDvxoRctdn5qpJig/XI0pWFpHFasGgUFUUrBPVc+b/t8fuwkaCLUJ+Ct6Jg4iSLJBE2iSJyoDpo5xduZEGnnVSp4JAsatjNVPsj2'
        b'ONltzxyh79ySIl1hI0TyIjkRIgURInkfIVJwQiQ/oHAgRGueIkRkNpld7mNE7HiZ3n54jB87Y1aeUxh9Kp8RbbZ1RwojJQMqYhTJdzuxihyuJ77282+Mi5gMO61Gk2TM'
        b'cw0mYl07JNZhPwU30O6usptj6ohvPLVo3GGIMJlyTL68Mj2lpA1qPdyQazKk0kjS/LVWKmivWJvKx8e1drrOflKvv5vaLGOKSU+8Z0BtG4xZWYx1mAw7cvIkDpVnMJlZ'
        b'ffOeTROZoJicJKo4WHrP5Eg2aUolBov2WU0wYrkiS5+hNUqjSM0xmQzm3JzsNHZCkPFLc2aONStN6jmjPtR1vVmbb8jK+j5mFGFksu4nYsSH9drgAIs1lwiWjW7x6SLJ'
        b'TWc5/FlDur/Dk+Q2fR3Ik5zjrDsYGtZCcYgbFoW6wKEZrgo8BLfx5hosWBoFZ7ON0DzZi1yWI9CDtfPjsGksnIKqLCesCcO7SXjOQM58i8oZn+zdFgD3sRXboMIHj1qi'
        b'oTaUVlIn3F0BxfhALsKTkXgkZzE3dYo0+2m6M05dwxYIfG+bWNkpqCT/qFIXQEUq4SZWsUOEUbEyYcxSxf6Q2RKrS81XSefz8h5P/UvK88Ja4+qF/0tm3kRJL2z8jdsP'
        b'Z7of0noqXnh/ofYPc5+8ePydFz9rLD8dP+608UW3Nw5dWDm/7urYl2HC0eKPakoa3RM0F57caHIqPWKu/qToZ9fvxLq9f6V9ZXWG+WFD1Uevbbw1PmzE0IbkazonbnS0'
        b'o5R+q/yxRC4o1lnZmYsut2kWHuO/utrdE0+bowKmr4yNIztAoFOpYVnJdJRFOwlhWO8UsQ2bLQzBoAZbNOR+dVMiwZcfjZIAjcBMJYwMV/iG7rOMYrka/fFo9KqAKH+d'
        b'jvxLUdDAXRG7N2Ra2HFRMmA1RAkblmKpJC4mKpngsUa+Di8u4c3kQfOUfnFicbijNMkL7+EVDVfvjQ5cGesfhcfHEKbawHQ03FVkQ8Vonfxp7P4+G8UBvFfjsLi5SfKW'
        b'TFIaAfjfFKKajIwLmRovMjNqmcmj38woe9X2BdvrZFt6kp1wZRc3lkd06IjcxGLeJmYnpGzcfrAK33KwH7e8HO0HIwgGbMRCGrI1kQY9aMR4aYZ1AZPuidAcm6c+Mb/f'
        b'V2cx+qPQDmVw0V++JXoWVOwkCnsVHrsIKVjlhufiDZzkRe1epslzJ0qNNVgbI+ANrMNLktPdDXfxsCZvJ0ssgpKlAjbgmZ2cIR8k1vjAjPc9ghWCCEcPYJVsBJkjKUSJ'
        b'LQY8ag4mUclyRg4hFh8GFZwhavZCiSYvT0X1HcOecOI/cBxPkA1kHQkdBh12GybDAlkQHIJGHhzACouWOtA0ODywYb1EU+9mzfQjuyijnlRg91ZZGJ6d+5T563O9ljDz'
        b'J+cGUDqyKxaq09V9ZlDxD5nBz78vLsBh9L+PCnAsZrjNsv/3MYHvcdVZ4f/nnnpqFu+W2WB52jcf1EEml5zUVCuZnezUpztq984jVodqw4igmZhZCv+HT6g/VR8/se7Q'
        b'Nz2bFCs/bu+bELbW15/ewsPZW9iq+Jn0Tt3zXR68nCeEhfn6P1Wjw5jI8895ZoyBDZLLOVeKLFCtacxC7s4dJED2ty6Xlc2bGzgvcBev/ZkMKF8/kAIxgsKaeKq6nNyn'
        b'ydC/NoohE54VxXC3RTESI7yFGWQrjYZkn7vmg1Jc4suMocJkQYj8vVvy5t79iwTbMeMIrIFSAocMFt3YBKeDJde7CW5ugALssp/vFofKnPHCMF5T4EYPgejyvJcXJ7v+'
        b'cEkAYSwnv1A2D4+GCDvxmCDMFGYOw3bpdsVo6AxRhLBjmMFC8C64xCu5u8dT0JLv43MgOSYrI51VwjtUBnWGEHZcuIHXgvVR/DDhPOdY7HDC+8mCsFpYHRTG6zi03UUg'
        b'pFO/Oi7Z9d6IjWTX57gPV5jvU1L+rJcCYhe6wDLPc3VZ68vfWR744fxFhz1DdxgeKkvLT2cOP/YfAV5tv/eeH1fxUZbrz7r/9sIrv9lxzPW93x9xt2wa6b3wYfz0j4/r'
        b'3i8+5bfAy2dRevmLH8X9fsrbYT8NSsp9r+DfAvKHtXeu8m0envvKV7vTdveud/aSvXNzsvXge+n1z7uklry93jpi3/ujz4/Zqhi/tGnanbmtq/9W9dN3/3Tjwp7q70b8'
        b'4O1NGW2fbo7YkuHzmSLpZKBf4qKDkWmLXo/7TqfiBlZDPuIZmz86c0ifR0ruKD6BEgv38mtW4y27OzuS+Bi5s+FDuftJdrrUFUuZfa5ge39VE2aJ7njHYmEujhEPb4vG'
        b'crgAhdF9DqjHDHlGKnZZaD4ED4J4Bz8XnszBO67uzirBEx/LfbYaLMwUpI/Ew/0eLl6Fa8zDJT+3RCeTTK36n/JVJR7gLHmmBMqcBQRKLOCgoCDHVOHKHVMvmUokd1Nk'
        b'rulEennbXq7caTUNdeAG/Q5jr5zQ0YES/He+ptzB1xzWRxNY3V860IQTox1pAhPdGKJw96MlXgYVq+BEDLejQ7BQDmWh0KmT8bXlO9S3LzAP9djMI/PLsPKpR1z6XMVZ'
        b'zFaKZCvl6fK+h1hkf/chFpuF/OaLARgSL2HQ97gdEmQaJNPG/YhAbhzTc7KycvIp10A84vbLyHxOk0Frtubm5pjIb1ugDY/w14au9deGRQ4yuv9ClH22w/lUoFfxFEQ6'
        b'xVknsQRsWcB4tl80XS/RvBXHrME2iwnvyoWx0KyYmD/RygIj+ABr97JnZzZE9kUFogLWR/pjkZHWJ5ZF0RxHrYvE0qD4yD5etJY9uuQEj9ygW03kiR1scWMHW1g9ubSw'
        b'1rP8WB4tg6oIF2iIgPNxUHHABVoIOpPgkJPeZx3Ht4PxXgyyPVc6JfsMMy4SjJ3OmTLzbko5EfvO7NKF7mKoa9i5MmVj0/L6irBcr0zdpPrT0/MSprqNN1bI5hpU4YZ/'
        b'/13XpR9uqWnFPR9c/tXnGVPj4zsUm69+tS93ttsXM3xql4mtL904+mTKqM0Vf91S/1+Zb85vTf9jnG/Vz/e/mbxv20u1i1RfB6H6fFvXPuGbXeM/23lOp5RCZiehHQ/1'
        b'hcwmw8l+jFoOZyzsKF7Wc0oJR8iYlD0dM4M6quSShZ3VUk0gz62DyeQOlgVgURSWx5Iko2J32rAvGm5MC3GCNuyABxZmVJZ54RVydGQLDwpinixUhdUcvDZPISyyYZeH'
        b'yc0D2113uq1ZrBJ8JitEuHKQUOHvrPrvBSanDIOlD5bG2WFJpybQ8ZQx98TdBkEu9N1TZhrRB0PX5VK0qh98BjdzXSbl4BjDCo4nGDB7SRhzSPjE0xFlWAwqDW5gIRZD'
        b'DY0fyA1kEKNZI2KF89bvR5BgG4Kki/8EfmQSfrQMWGAJuVlGC6PX/RBBdJEWKbubbtJn8D2cQcveDjp67axnBiQGZJ4etmpd3Nr4TQw+IsKiE9bF+mupleiksFUcV8J4'
        b'elLcutjlEfG671/9ok0CA1e/Snpe702BxwN2hfon+/9qbLxgncdgOXi7DRE4GvSvZgVW6eC6C9TtdpEWKjsu0Qhn8biLeinckc6HHiGkqHIsb0cTrTvHExEfGn38fJTm'
        b'KMo9aeaYXyfH6CP1WYaqtGZDs/7z5B+kB1Xp6M629KyUL4SSyGD/5C+SNzu/+4ONP9qIG7NUp/SqH741IzA58Qeer71Q5y587urx3Mf/oZNbxlJ9s6B63sDw9TC4KPGF'
        b'Bm/OCdaOg4s2SoC38SwtOeIEbnBIChtU4ZWQ6CAqGDBdJcRgmbO3CJf24uEBzrP4zKXhQu6H2cF197KvjmVsPaj5yiCnfXTfijCNHFyZd5/6s1xzB6j/j9wd1Z8tvVmJ'
        b'WOUX6T+ayEdcvys+Ah4phkPbNp0U8H3Oax83sa2Uo4wFNIKgRFopow8qMl2g61+/Uj5SyAb5oo7GlocQs/U7uNdjXz5s4zPXQJ4TM75keyWLG5WtTdWbDYMXhj2wa3E0'
        b'yP/fG2H7Uhy4DBVx0gGParMLdpjxrpU94HZPEPG8bCJ07zf+QfGtwsywbqgx/dfJnydn/SQ6PUZ/Kk2d/mGWTPC+Lf4p4seSMonfr5muHLRJ7kzsXDdVdt2MN/k4IHSv'
        b'hmlvUo6JQfyzI0cE0uP6tJSVjRygpQ8HaCnjF4nYNlTCZ1JPKNjHwna0QGOVwnioUuC5FdD4/So4R1JBFhzp3xn4BwnfR56DQyL98Jtm5NOlN+3W5hstmf1evinHamHa'
        b'ZMxmkKznAfcBZHBAhc9SW+2Ax9n7ggWO2uyowQPV6J/TZseiA76E5umNWfoUsi/bDbvNCwaqfQB1bO0CW1CDlNpo0a416bPN6QbT4Hzh4bZ80jC04YYUyk2GaZC9CdCy'
        b'eMX35Z3pr/VN69vN8B1cdHnw8meWpPuDsyaEhdk7rjel9YVkBuWKC42NWMBjLRxn/r5lfDqwr5Ys4ycuPHKgnZiavOj45jmCdJy5bhvedLRtULeK09jV8QHrRSEojiwk'
        b'NEExd/eTc/AwlLLz+DyggFUpvGLnEB590B5wT973woQggR9viiQqU8BZMXsuPYDFwKM39HHjBjjL+PFKRotXCruhRw1X8Mhco684V85/5sCnSvnr5N8mbyNseC1d5/Xr'
        b'ZMWd7aO+nLzgzLZRC7y3edePKv1qpXf8mW3eLx76YurLo48rl93TvaYp+HJKjKZj9Znt3iOCRxxdtlHnqvNvjaladjLx5dEvfzzr4pJ33Kc2L3lZ6a8ZdXjUvBBhttuY'
        b'zo2vEO9lgKSakuxoaPG6yUZ6xwy1MMMWFE0Utn/rt2Uk84sFDbfS2AIPTVDqkYf3oTh/p+tOheDuOd1fhEdw393CzwCUwKkgRmsFEU7jbSK25B1wE42FUBlPriX91wYR'
        b'nxAUc2TQjUUHBpjo/zbQziDRttgdA+0HBYOr6CIqOJd1lflwNmua0G+zx35/7eP7cJHlXzsAFwdG0rV0d8fiXTQ+7SwoDuqbcSdynI8poBkv4Gmbi4ylJmgmK8+CE4qD'
        b'cHKuDG6Rv1DEGbj9T+GImYzBMQeZ/wKELF1pQ02R/9aDnFBT7ENNOUdN8YDchpoZRHPfGbBeYnL0aWbtDn1uLgnKLGFbWs4Og9liTO3bIuRnoPgvfPRhX7qRwMeca0g1'
        b'phsNaQOqTNmt9c3VWzJ9eSTUl218m/7ueSpjttFi1Gdps6gvZINtnRlQp4WDXb5tkzPXasoYHLcesPD5Mnxq4bvHSY+c1Cfv5AJfHYnFqwLWYxGW7pUFrYmEVizyJ2V+'
        b'TuY0F85DD99aWACPsd3Pl50AqtiTKOA1eOgm7aBXwm0zlkbx/awQhaDGx9gApeJKrNuuk/yXiNil0bS+yZG2zb47PJZvU0Vi+xIeAfTA03A2gTRqMtsFqZ+Mx0dwBPmB'
        b'1mvia/JIBjE+y4LWS0HNFXLvrH+TJbPzWpsjl7lL57V8x7IIlsDwBy5A4yZaYCXS81ZFUINn+5EMDo2LWcOQDO7HM5fdF88rsGjvSl51xWQXrzMyfrjL9Y5fptTe1BD3'
        b'3Jdl/HCX/3CPSYLxpbHdcvO7lLLzoiyg4vHKsFDPY2+89t2nU2eejvxS+yv/VuXtYyN63Q6rxE0PXDrKQ99dkbXv0PsfTPvS+F7pevMZc/rrG17T+A7/xedfLbrzZvEH'
        b'zbl3IOXFA2feWHe8sf54TP67H6sm/fbS2h1h1v0/Uv5hwdejR6tf3bBrUXpT+pfXRr1yK+Pj0S/9Vf/TMJRnnN0ywTrNq+eTv1y59fqUH9zcmfftVz1D86YeyL8a+r5y'
        b'aqA1uPalhTkn9ue8t21z88EVPer/nNX8+EV9zI+WVvxy4SsPr71etaEndMu97yYEvP3ntyo/HIE/C/rpnmXOITk6Dymo2I3Xh9tXJBRDEVuSi/EGDwdmQocVS/3jmGSj'
        b'lIIaqvZjqbgfG6bymKNsO3ZIqBmBJ62O4UyNP8c9uDEOK/xWxsbIBMW6gAkyOOcFjzjupZNT1U7VNvkF6rDEnwAYbooheCaCu/twHM+N8wskXS32t4aSOjGFonkcCfcV'
        b'kTPgkoVRsYlqPQ8J6F2fcXAH6mgsrRy6oQRPrIMHeJhUMyrWXxRUTqJ61lwO+3B5upWf2dkOp/qP7WgVWyOzuHRkeBtO5mObrS8M+ivEgMAwSXQVoQsI8rsd7AIZBTcV'
        b'r3nt7PF+cQFRUXABz8ZG+2O5TiaMwG5F8MLFfIjznbHbHtGAa+TKPHAMx+7dIgWDL2EtFlM9cNiJ2Y56WeworJV6/ggOr/XjwifBqPEhNuIjEU46YdM/HqP9O2ETB+vi'
        b'zqAqqQ8euYGZYTcwe1x5sMRL5srNjOQaitzcuPOrK9/lZfdNk/oMz3VFr4KhZq+SA6YDOX+mMboumtgDsqYpfTaJVWUaYJNODHO0SVO4Xd7OooDFq2IYXYeuvf2BPoKE'
        b'+UpogYqFT1mepzcy+397SNa3kfmP2B8WZul5hv15ik1/n6FxMC4DqvkfGZoBLQ6o7h82NB7PNDRD4zgG6zdP9IuMHTHQ0gy2M0+wi5NJTayWrIz3cEHGjAypboGVoYJX'
        b'Xmi/jcHuHEIcMjE+UKeT9uvxONyH+09bGVesjpTjVZ1oZVEY9pQGXjRz+Mf7zA2Fe+55buSSWvLWqfPcoQA64Bw+3rIXjsAJrIPjubQGq+HkUKhSZQjE0A55QRc2jLSu'
        b'YLWdUkDd91cWCm1bNuPFrAy4fQB7tGHzWAwPi5yj4EiIAKcOekEbNsIFbmSOzRa98+XsU3LMvuFrJcszJ2bEgT2kMoI22effIrZKN/+8QrnnZ3JPQViW7NoboxGsbKeA'
        b'OGIP3tZgOT8rQmS6MkFNnHNNJIfndZF43cjulsQSTqXuV2/G41jLpc1++SAQOmjhLBLgxKJFG2bqRN5M5VSvcU/spnfibqntF8RRWd9Ipnffjp1xAn82nRyB63GOroLN'
        b'uk6J6bevU7x0Ks7y9sD1EJv/T6BVhFeZ/78fKvkhhUg4HMJORBDoNbJTEUQGNkERT3oObsNVdiACH0exMxECNhzEDl6lKoEdsLWdh+ghr6VKNgKu4mNpfK2R3uw8xLYI'
        b'QZYjwINQnXQst8wliR2HIANwjx2JIC40G6/yMUL2qMzLNnpRl75OGnisYejmn4hcGptDtx8gdJTOaZyA0wbWY+qBrcPEkqSfTCIvpxHKWJe9d9l6vBAPS0GQ+1AGnfY+'
        b'k5Z1sT77J0vl7k/DRtZlquCJ1Gk4I/2KDX26PJV3ux5abd3GTrXxk41BSvN0gryln/1u8aqFcbjM89ymXzz6bvJxscAkd2mJtOi6BO2Uruxhl0ITtO8lv/JpzFCNsVQb'
        b'H3+5LeiFO/OcOmpy7/Q++F1Ixxu/mPv5Tx7J8ke2Tvgit3LJHypcI4YdXJF0RQgb76btLHi+s9Bpl/jyknEXV52afSoyfH3KHMUvl7wm/vbDr1d4Vegei59W/2S704fN'
        b'7T+uL/f13Jfi+Z9hj7PHGj7ZmvXkF3ffUC1LbkpwX2CIKdz754QLfzqdsOTDd4qHT7ueVhU9IeR+04++KdpRuHbtra/fnvNq0vIzrwV+Pq77o7s/q5j06tRTq5rPvOmv'
        b'rb+QdbZ9S+j+L3fe2PTXt/N6E9Z/VvTjqtY5SzXlvXfbC5xH/WbuNfNXSdE/NAeOzH3xz/tXf/e+Rp315vqWt4P21CgqTzz+TnblF+mvtyTpNNz84yGsGWInOHhtD+M3'
        b'2ChyFqLAY9n9/Gb6TLKjRG+MWMjpzQgy0YzepModjw8Tu5mLp6Sqz2AXHLfxG3w0hBGcA1DHTfdBb2jh3GbPFDu7gXPO3PSnYdF+RihG7SFKMYjcwEM4xKnT5J0j2C4w'
        b'PNKxjWC2Czwfj1nY4TjPrdCi8cVyP1bQ3jERzwvjoUOBt7FQOhXmCVdIg/q8UoLhO9wzZX6pIOcEZgfp6AnOiqAVTtuYkQ/28AH4aWdIrEcB1X3EJ1Xn8c8dWP779ON/'
        b'spnsxtmIOTUrif3cIicjMXYyclAY00dHZAqFgu/ieLIzzqK6j56w09DekkfMzzzb/r9xdXaVaSWiousjKia2CaBz+ke6OK2PnLDiVYycDLOTk0PC70cPDiXmb5tqZydB'
        b'xEqIo/Cf5sPG0MlYrVyIl7CBH4aMWhYY7bBHiTV+cJ1wABuwc/JS5fypeIjHz+Ei3oSj2AIn2GEtPBkdGCgXXLBWhMdL4JxOHhe3QidboROlN9kKY3XuOLmZCbDAv3Jd'
        b'lVPC0FDv4/k5P3M+OvqFDx6l3G5uTn5pq6B0+8ZbMUyRggut6j0jZ5U8vjS1pueXq36f3xmVHTxj4d4/Pv7dt/v+1+sfvB+eO+uz8IZl8RO/fTty762Xm0cm3ui+FZC5'
        b'aP4b1186+5rZec0v970tHmz1+pP2zVN/nPXz28dTnaNm6F5JO+vdXD3xQcPDo6HTdebsQm/1vUdD42XXWlYZFn19be5HP3r15t3wrV/Hhka90xZ++3P3z8e+tTC8s3Pl'
        b'te73p5wacqnBxfd6Y/3oxrfin1vccebHPp8FV37tnzyhdONrXjXtZZ/eTJ5yY+OPR7/TXqF6p6OgPCsl5Pl3X51zv+PIuS8a71yb8GnG3L3vRv/sVPvkb999Q1Zv/Ehb'
        b'OO+1IRWmsvUV5sPVDR/fjXs9t8b8cMEbyt7Mn69zGtkVfu2dLZs/c5n5sOvV2R8+/O2Od9Zt/tni9y7WLvmm64cBKu9fzglz/fXi5uohXu99dGvJlKuPR/x25wWnsi89'
        b'h5Y+l9Cq+7Q5Zp5ffcSGhGv6UTXBV240Je71v309+MrVV/70n/ktUz99c+m4s76+/p++lfZqzOnTFcHlKy5V98TdS/g4/I9+r1XfLbw5tv3Kb+74ZV34TeW33pPmj3tt'
        b'/49PrUnDsmvDl87eNH7urlc7RP3Xpj/e6QiecvWOu27qrtc1iwNavz3w78vz9/wmeGHKc/f+XLXht87tb76UlrgN2vbvfGn7B2VOX17PWNHypx/m7P6P9CVz9154o3vB'
        b'ty+8sjz964y0rkcRH49b8od//81XD7+uvfvLB1Mn5l3ZcqX4dkzXn11iJn2XOTGrdlvLoje+/vrl/FpNfcHHf/uvSdsnXxmW3vZ5mov7xzfVFX9zUq8f8vIKGbma3Js5'
        b'R3p5DktjZKvzBfK16VszNPJt56lQMZtBLVwnwBsItoTfjznuPQ+39P24B4+t9mw23Ds8W2qlEmqNdrxfOpHBfQiUc0CHa1g5KWh2NIPdEilqr4FyES8NgascEBOxcbI7'
        b'dEXH+AZKFWiyRLy8No73ES4uDINSqFzFrQWUz4WzUEn8UyVn56C7eQVY5UG9K8USrGS7V4pZ6fNlcEe1lyOy32Io7wdkYhFn+wAZD2XzMSZCjdnhWZS4ZYOcWk9f3pUV'
        b'2EnozvLlr+c5HX3H2bN4VXhk78GntsxVAjyx8D3zMiiSnNh2PEE+aql/FJaTEVJtnbpLnKTBEu7/Y2nyyk1w0W8l27uPiWPiuiPSFJ5bxeWJl2eu2a1m0ctKysBDBBq4'
        b'LRIGXV2qc/kf2AOvf6FxedrWsL2Yf+TCzYw6KYkbmiRuYXLZns4IURRls2Tj/iaK7KkZL1EtHyZzlytE+leJMtv/X1RuovCMf9m/6O63Chfezl9V6r42///6v6uK8+Tn'
        b'JdQyL7koc5f5hLCAwLDRLiKzvD5+IjvUNYJdvTz41YVdR/iwq/c4dh0X7CUz+doNv07eKyYlOQQJhvzfURGZya/PhrPG+dPl7syGfxE4+Oi4nxctIUID6bQ9FEPnJo4G'
        b'o+RjsQZqjPMn9wrmTMp4bW3g2B/OdD+8zHPFRwfTR764cuaLG898eK4bXty4MX75c1++9/wLsWtafjclyP9PP7m8ptTtSW9aU4Duv36eXfK3H7+Ud+PjR9aoopiXLv60'
        b'YGhGYqBl88zsefl7xl3eMEb35XvD9n/11h8ey2ZPH/X5X8p0TnwzYtcawgNGK1YxCIp2kkEtLcp2EZtn4EMJBR/lQlH0qgC8w3KtInq5e9kQ7JbDpTVOHKfGQ6lKGhrD'
        b'SCjH4pF8aF7ycc5QwEF2N16CtuioWN9pUBjrJKgUohrPxvAHI8ijebQPS2djZZBKkCUI2BSmsPCnXqvw5Dg/T7eVSkEWTdxZgS2chPvr4aFf3/MRQ9KpmEemfNsq7wFb'
        b'IOP/70HD/7niKP4ujrBAjA1HmOwEN3aeSDpFoRb9Jd46x+Tfp+0TeuVZhuxeBTvS3KvkJ2t6FVlGs6VXwXZ6exU5uZQsN1tMvcqU3RaDuVeRkpOT1Ss3Zlt6lekEW/Rm'
        b'0mdnUGljdq7V0itPzTT1ynNMab2qdGOWxUBfduhze+V7jLm9Sr051WjslWcadlEWql5utu7oVZn5Dm2vi9FszDZb9Nmphl4VPyCeyp/IMORazL1DduSkzZ+bJJ3uTDNm'
        b'GC29GnOmMd2SZGBPg/W6WbNTM/XGbENakmFXaq9zUpLZYGFPBfaqrNlWsyGtf0lLIx9vWsk+s7CLaSm7sM1EE4t9mNijGCb2+1Mm9vPwJvZbe6Zl7MJ+5NLEdtZN7Fyf'
        b'iR07M7HopGkxuzzHLqHsws5/mBaySwS7sH0lE/P1TWHsEsIuy9mF/fCUiR1RNbFYkimaXZb0wQKbJZc+WPhLpAMs8LRv1PaHMns9k5Jsn22W5JvR6QN/el6bnWOxhefi'
        b'dGr2AGVaTipJhz7os7II8fxtGsQ2fum+C02EyWJme/y9qqycVH2WudfV8fk7U6xdlA4XSQ0XSb9vv4QZMh40VTjRopWUL2KYjIHu/wYx4Avp'
    ))))
