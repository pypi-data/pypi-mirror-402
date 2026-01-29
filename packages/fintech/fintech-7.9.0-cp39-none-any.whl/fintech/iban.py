
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
        b'eJzNfAd8VNeV95uqMmoIEKIPnVEv9KqChIQqEpiONJJGYkCoTJEA04QA9YpAICTRQQ1RJCFACJxzHJe1kziO7SSKvevyOXESJ3ESb+x1suvv3Ptm1ABvst/u71vpN0+j'
        b'd/u55/7P/5x73/tEGPUjo08QfYwr6JImbBUyhK2SNEma9LiwVaqTXZSnyS5JDLPT5DpFoZAnGH22SXXKNEWh5JhEZ6OTFkokQpoyUbA7rrH55r59ZEhwrHpvdpo5U6fO'
        b'TlebdunU8ftNu7Kz1OH6LJMudZc6R5u6R5uh87G337BLb7TmTdOl67N0RnW6OSvVpM/OMqpN2erUXbrUPWpWpVGtzUpTh0SGil9yzTrDfn1WhjpFm7VHnaY1ae3TDdl7'
        b'eXOJodHqNL1Bl2rKNuz3UueYUzL1xl26NHXKfp6+VmfYq81Sh+qyTAZtpjqEavCxT502TCIz6DOdPiomFRNdioQiSZG0SFYkL1IUKYtsimyL7Irsi1RFDkWORU5FzkUu'
        b'RWOKXIvGFo0rGl/kVjShyL1oYtGkoslFU4qmFk1Ln86laXtoerFQKBxSH3A9OL1Q2CQcVBcKEuHw9MPqxGHf/WgOSJrpGlls6vBpktJnDH3Gsk7J+VQlChqb2Exb+r7E'
        b'USqwe28tzfZaEpsmmGfTP6uwYzGWYQlcksZFr8dirIjTYEXkxnhvpTAvTI5PsGRiqmSUJrham9j6d4473dUyOkmxlEYnpdFJ+OikfESSw9LEYd8to8sYPTp7+sQ8NboD'
        b'4ujmzLERHATB5cPAA9H+qycJ/OZuiTjkL/JzMkMzE8Wb1Xm2gosg+H2Ruc9h9fq54s1N3gqB/qpve+U4/G6Bg9AqZLLmItzc5V+6CkFfjN0vOa/4mf+tXH8h044SdCHn'
        b'JPEz05yFoOSA9w33XN8Tb38V/SfnqzqP6dL4DyX/4V6x7AthQDD7UIJGEg6XSbxlWOa7fv58LPWN8MZSaN0wf10MVnn5RHqvi5EIWc52K7ENjpnHUxG4iCegKirSK1JO'
        b'gwiYKoHzpvFmNaX4qTONeC/fYMo1G6EMiqGY5mQ7XIezskBsxUqNwjyFsmELnIEb1pyGlf5SwQ6eSGdBA3SaJ7EM96Ac71sz5B7JkQh2eEI6z9OGl4+Hut3WRLwTBYUC'
        b'JZdIPbEbi83ulGFrWKI1PXDiCjnVfk/qBle28NLzsCfUkoo9eHs1VrDiNVJfvDZD42seR1l2QiMeMzpghQdpGJ4V4MzhGWY31rFeuISNRoOfnYL+KROgGIvgNi+zLArq'
        b'KQEf21BKhQCleH8MLwPHZyRRe1uxmVVQLdDQyrGKl8Fj62yMUImdWaQMeEmAJueNvIxmP9RQAjzZTSsHLwvQDDVw1DyBlbkC/UuNuVCCV1kfqlhLR7GPp3lAldaId6AG'
        b'K5SUdlqAajgBjbwtL0esNpqD01ihGoFm5xhc44V2w3FoNzqSFnSyQhcEOIc1UCQ21oLHsMGIXVjCFBvrqUZ8kmhmmh4wLsII5bHbWLZGARqS8baZLUB7XZJR5eXPOn6R'
        b'1XXRLIrhMjZgvzE/DTppqeIZgcbdZM8VCh9uzjE6U0vdgljorB/2i+3fgYZl2OUIRdjK2r8pwAW8vE1Uw0uToVplmAvVbEjtVEqLZXyoEw6QtMoclFAgESS2AnQegGre'
        b'hzQ87WbEu3PwEZvXWgGqoN2i1NjkCrXYZcaH8TJR5HXTxHbs8CHWqPD2ASxkDd2iyViv49WlQB3cNObjE3goFesrhW5RODOxZIoRe7fPZr0+J0BNxizeNWjPg14aa52n'
        b'ZWIbEhfyhA3YCh3YZRu+jCVcFeB8nEzs2L08Jd13xwus9RvU+jJ4wNsYF7gSu0xjsEYhtlF1xJZ3awnegGvY5QDXVijFIk1RpKRcnifssZEllcMNJoIWqg7vHuGLxowV'
        b'0EAzfQcvwhXW7Suk93Brnzh7Z33gKnbZrcdWVq6TpB9L0mJJ2XgNz1IStMIZi4Au+7nyQekiEijBHU4zkd4W4Aq0recJ20gvLlF53wyLytV4u/IOpuMprKEJZ3VKxEKX'
        b'Q7GbNzQLbs6h/nXh0ZksqY1klAy94rgKsXwhS8vDChtRT5qnYhtvKw6adtH0eU6zdLxpFdSLi/kMNDurbO2hj6XcE0hoN0hbmdA3rMUWFd5NgXusth7qBBTbiIKohl68'
        b'pco7gr0KsaFzXtgozlTzFriuwnu5C5n07lBL0BPPU5KgAvopRQGFbLxdpMUxO3h1OuwOpgSoh36F2NIlaF/D+x11CFqMpkhsYr0rFuCkKz4Su/BIjkUqoxpOyUVxn4Um'
        b'vCCqVzU82KeyTwxmzTwQ4DpWLTRP5GPFrjQo22O3CKuhB8oVggwvS+JmR5oni5hyJQ7KxkJJHtZRX0sVgnyXBAqgz4HjOpS5J0IZTwsQy2MtFCgIVyukE3KhXCPjCjkW'
        b'TsaRIXmMrTTf2aQYJ9ebnVnxJ4EHo6atp96mCCl+yzlKSH2wKgovY4+Smcu0HCw0z6HbWXg3hlSgGNoXQatCGwMVeHV3KFzZGiMsMCrCFXAae3aZPfjyDyTdZVkr8TrL'
        b'3omnsY6XXADteFouTMEKud1COG6eS9nXwqUQlttGTkv+HrSwzBHQOZgX+uWyjfN4zVux+AVe8QPsYBXfHFZxh1hxrVxJMi83z2MdKTmkw1MRwYehg/o8mDeAtUF5vWV4'
        b'H5uxhVeN1zZgs3V8nXx88Gi3ajxeVGMZtLwwVlintlFhGx41+7PsxaTTtYP5B+uGW1hBcNnLvraxVrwNily8Bh1mXwZLynHUH7E3FbIU1sZRGvSj3XCFIPjqbigjaUbg'
        b'fSX2wB24w8UD1w9C12Api2zkCcJk1gE4KcPb0IP15qWsU2Ub8SrNyzmxX1yYFaPl1BLDauqIUabECLlwyxYebFzKO0fE7TjZq1NTl7MWrPKSEfaW4Gk4mU7K1SD4E9iR'
        b'9TuGZ7mEN42Bu7yx8/sG2xHnrk2cu1MyfGQfavZkAzmKJYk88xUCuVFq0SrOXpHcBvoswjpIecvxAZYOSbliVCNcQRa8qIBzmqm8jBM0qPMTBtV0aFraedkF4swHYJUC'
        b'Lhqw06xh/bqx2IOXuLFmSAGtwhK7dVNuOxZP8Bb2k03ufaoBKtZBLRyLY3e5JnrTUjWqwvjIdbmkLpYibawIoep+JtMNpMYn1XCZtCsG+20CvDaZvdhMPMLrKtnekauN'
        b'tAQLt85fJPbJCBdsSTpn9vFO2cJVX2vu9hG6SISjelifziiMNvCQDxsLbfCWV6q12M3BJR2qxlNc4eOw2cZn9lhROZqxPH5Id4c1tIH0wiI2ueADfYrdk6DfPJ8Jtm0Z'
        b'YQ6VqZzMirU9hQLzZNg3FVrEzMeyCeNPRexxHaHoC9h0y0nZ78nI/JVjk9mPZb5vhhMzsHeUZrSO1oxcBSFwOYotyOEkafKpCFo31wYVnOW24oFMhrcy4YSlO3AKT7L6'
        b'bYNFUT6lFFfkNou3mAMo8xF8vPdZXeF35HDXISZ4DdycKxjwdKCrLVYHhXNEnRFyhJWiJVs9AnRC1QphAVxUwAUo38ilvygYirazhTBc/sOXD19tgXheQau1z4kjVCrc'
        b'x2GKWjGofOyOPzYuklHHHHcvlKxX2CyhVVxr9qZSC+CkOYoDBGW1KAb0KkfAfQJU2MwgCD4t6lHbWCaoJLwyAth4bgZngdBDiIH9YziazXEiI3QqIjxuxCwHiAOYjHdo'
        b'ChLhLBfPGrhuOwJgLcA3BY7twwJSHYLIcyJ2n8Ob3IRgH2F1+zOmFopk+DAJbplnsrltwCbtaESVMkTt3TOR1GxBKu/qYWhzY7kqvEZpZKfY19vU11U+HAaX7CAFId3F'
        b'h0yx2qxZoXtIs7rh0Rru1m2AUpdNyqctxwKr6nBR+GODApp1Bl4EH0P7UhLLU9JYYAV4scwmBVTrjHxW1FhwMJS414jVzXRrcHXHR9ssXY+lfD0lUE8L8BK5jyM07Obo'
        b'gQTCEwVUeSziCmbE2v0j8ktTLW24UBP3F42B4oXkgAZBXax9LNnku1xUEdgezhZh/aKRRtm6rDQy7PXEO3zc8Gj+wmdjOXm8vUOwZlbkQNsq0eQ/Vm6l6qcxzv40IEzG'
        b'BzK8Cw/2iDylGzqNrH57RlNGIb+FpzyRO83DIg4JajnlpfE2M7AfoWMdYt2dMuzEvijR2JXBiTgsmP0Uhg+bAC+bxfCEGDSrPGwS1LG8E6FwcKGOUCGmwU9iokTy0bRZ'
        b'/2zJQ9dWEs7x3Xhlq2DYA3cXknlPJY/Nm6v9kkXUxAO8+bTqtStcLea9gyyjPy1t1s407Js0qEHDTB0pHV7Fk0McB04pTORut3FlCsHzB+AunHuWireOUPFLBHGuWnFI'
        b'FeTblA0ZSSvCQRVWDS0QRe5CSbytzSLom8kNJXQvZMYYzhA2Fo/U2A5FCgkjRgiYoCAL0ImtXMwTdSm8jRZ4MmjCLGIW+SPclctjyMVmABBgpLYp9xjt6GHcFJWjVG6r'
        b'COdqlwI3iMCRWl8dP1qtRUVaLsP+pbZcPlNmQPcWOP+0Yo9azXhKAY3QdVATzR0puA43oMFowop1VrcD+smx535H9yGoNZrgshtzVUoEcsqfYIfod/SHTjBidz48lIgx'
        b'jsq4bNHH6iazc9TogI82WUMpIcS8JnCIOgMVRiJpl6CW+bzNAjQuxPtiYKRshc5ocItmDk6RAIwxdnBPKpxUosBomAK91gAMtHvyFJ/JeMZogBNwYTAAcyWSV7ZinDs5'
        b'/TPxPKu4khYN3jgsDughPoBzRnu8L5eKnTuN50N5me06lZG8+TbeA/JPG72JQbCE0Flw24j3bLHXGs2ZIgYx4JgrnDc6QR+vq4EGio3evJmN2AwXWTSnM8wa5oGbvrxQ'
        b'Fl6GAkqadcAa55lELJv5UvFw3s+Yi7cl1iCPnUKU9C3ffUa8Mx/qrBGeqEXiYK4S+tVSUvICGzEeUAclS3kZCQFZm9EcjI+swZ/0nWKZCqjPMjrK8Y418kMW5ixvf0+G'
        b'2kh+uNYa9dlria3ssF9B96FhK2ukiUY5naaTFTiyZLlRhU1YbA38TJ7IC0TjXaMxX4HN1hBJIhE3Pse9Zqg35m+EZoU4koqEFaIkz/gkGrFXprfGTmgZnRU97P65WygF'
        b'+sMlYtCpLpqmhQWW16dEGp33pVqDKttsLH53b7zRmbCUq+VVmkZoFT3yFdiCPdhl65JuDbeQp8O7lRMxk+5jtY013DKF6CDTV690Ek6XiSav0hpwIZCrEpfNMRJxHXG+'
        b'bgM2SEQBnLEJFmesLckRuxwmLGbDuUYtkT7zhMXTsYMSwgKsUZrlNBg+LRdIEVsoCS/uskZpbPfwfjuZFdTKXVu8ZSPW1jAbe0SpNUzJxS4nrFhhI0YFrthbgiPb4GoY'
        b'TVllHNaxwd5li7wYG3hTCdRSL3bl0mo5LRVlWrUrSRT2BSg+TEl4Vq0U57p6905e4UoiCUdZpMgTOq2Boj1QKC74vhwCri676TOscSJst/TwyMEgSpiGjdYoEdaT0eCF'
        b'qqn9E5QYI7dGivCWhhfKIGtFM6OCs9ZIEVQdFGM0psWUMAdbLPKuhTt4U6zuynhCty5zPhQrxAVH4L2OJ3mnMmbeQ0y0yyL1c3BWxpPGw609pPGH8JZU7PlFciHPWCYk'
        b'A7opbS6UWYNSjlgstnWWeFMfC1G2ZCjEsM+VjJWiUpwl/bjDolJOB60BKwl08WCbhwSvsxTyFi5aA1ZwAR+KGvPIe5IKb9sBC46wpMYNWbyxA1jozkJZeNMayyKz1Mvj'
        b'KZne61S2ULdNKUaRrjptFrt3TJpP989AiTXGRUrcJiaV7FutMpHLVWNRzFPYCc1i0gM4n6jCu5uhezD+dcaN922NPXSo7KHZYzDCVOsl6t/p/XBBlQf37Vl1rfQ/tEgs'
        b'dmMidlLKNShSipHaeqhLFRu6T2jcrsrDcp01muYADaL6FXvuU+E9T+y0RtOw00Fs6VRKLqXgcei3RtN2O4phwGPYvZUl1WO5NZyG5/fyjhNH0auc3COYHB4JZJtb4LEo'
        b'7TLoWK1ycnJmqveYliucEWtzJKWsU9EMluAti/QuzYNrYu/6omZSkgFPsVL3adLnwAWOgys2bFfZwbH9UrGdG2F4Q4S7a4tppOYMLLMEsutdtLyqievpvjEJC6zRPNKM'
        b'G7yq3AyoVBkD0BqEbJ6bKAqgHR7uIMHd1u5mAuin6fabb15AKVNpFbQzhgPFPFp3EBrIit20UD0o5tE/OXRtgLKNwqYdSrwwx6SRi3sulSFkD8ui12G5TJCR/3QzhXg1'
        b'XoFjXBhGQruyKCyNVgrSncR1Tkh8CToaeNFcLJgbhZW+WOGpwftu0CYXHFxk47EwUZyV+yvVnrHeEXJBHkS+0yMJ9aYQ6sNT2Q6Y9YcGIrCNKr6HFiHw7TtFkaRIWSTl'
        b'W3eyIrt0O8tmnbxYXigcUhxwPSjnm3UKvkEnP6xIHPbdT0iT8c06+UcspG6vHvYTyrZm2WYs355Vp2cb1HnaTH2a3rTfx35EzmU5WoN2r1qfos1apt6wSycWMGWrU3Ti'
        b'Bq8uzedZBVL0qcvUkenqDH2eLstLLGXZBFZrDYNl1fostq07ogb2k5qdZdLtM7FNaJ02dZc6mzIZntlQarY5y2TYP7wxk7WbeuM/0I6J7WdbavNRx5iNJjZGJqLEOO9A'
        b'/0WL1MHR8RHB6oBnVJKme2bfjLocLe+YB/vmodaRkM1ak45vjycnbzCYdcnJI/r7dN2W/osS55NkGYs6UZ+VkalTh5kN2ep47f69uiyTUR1s0GlH9cWgM5kNWcZlgy2q'
        b's7MGp9uL7oZrM438NhNyvt44ajAjtnoVDEmE0Vu9LrHhfLO2QTJRIPLtl7Mj86B5UYzAkRnv4vVxUKbaQ9+3CFvIzPC8cxNUAuGCbfWR/Oj35oWIu707UpyEKYLgnrxV'
        b'mznxcJDAl/sCvIZXjCqRV5ELU0Cc1VXjLEJBiVOYNSmSIPccOU6NIrT2p+BFY76414alRMMroSOXQ5EJ24ktCaLZLImFs1CTLVqsa2PhEdkyEaFeoIQLUEIOFxstnpu9'
        b'RmUQt9oSyJU965sm3q90cFLlyDhNMUIH1O+NF1d9MV7BR6pc0aCT31II56Fb4GWgOgj6ocyBb8+td4XODVvFPjfgtXnYZVRyq72ExlKbTXyYV/cwkbF4cd8OL+M9wqPH'
        b'cFE0MDdmMoNuFjfu1rJtuT7oFGt8hCWHyGSKlAP7x0LzC9gsiu58DDapuIAI2Z8sJgN8TXRaiG08xi4+ViJrnYegmjy/AhH32+DyTmO+DWfFTgHUiXsoOgZ4A44vMuaL'
        b'LPcQgW3poRc1IrPAkyT/XmtaApEt6MELlk1MPLp2sC35i1DtjnVifY/hITRZm1JshCo/d7FILVaSD4RdIjVf6ADVW2I1Up6Wn4aVgynY6wzVOjzFCQdzNLCf3C2Bszy8'
        b'geXQIIUarnYvpohnFNRjcrze9PAW1Q5KM6YF+smZvSVFwaMpRMoa9Tb1rgrjl5S8OfbdhT+MWicLdlF++KTN03d69feTX3PcfkCY8M8zXMZs/8tMl9cuZ7jHH3ghuCXI'
        b'bWmQW+DiMXEzmkNWFGz0fvst06Edxz75fpKHvvPy26kvLbrq8bb9rdOVG//ypdfUZb+5r6r62cZjJ3f+3u5w84eH8l/bdT9sa0bWktSSM28PHBn3646r8f9s7P+3U6vW'
        b'VGo/xG/fWV94o+VX06Kcf5oRVrfkwCdznDoOXk7r/UP66S9dX5Vdc/50yZ2r+Rd+vnLchYYj53705uqyf3F74vet/5MF3/qsyt807bM1C+vfKbn2ftpn3XOOjB/7C+nj'
        b'sFegvX3+Tu+3Sirv7p16q/cRZP5Z9Zs31/84K0ajMDHJLCPK3OPpPT/CWyooocFvjdR7wVITO1ugwYIsVRSWa2LM3j57PLDUV0q8skhu64GXTCzcKIWLZILL8vGuCSrJ'
        b'A3KwxdvYbbRxCBImwF0ZnMNGfGhiO3ZQkJnIDsB4ePtIqJVjU+CBNJAarjOx0z7EShoTPH0ivTw0PngWCrHKizxywV0t34mnJmkUA9L5GqZUwqiLxu5Zd59/YQd3vhm/'
        b'It2QfUCXpU4XT0H5MHO4asCeg3MS+4dlM65hAHlE8HGRyCVSyTiJg8SWrnL6taePA/suY3+VdN9eYitVsqvEenWgPKzkFImBVF6I5U1rlANyVv+AjAzqgI3FPA3ImT0Z'
        b'sElKMpizkpIGVElJqZk6bZY5JylJo/zuEWnkBkYzDOwQjYHpvoEdlDIw+sHbvcBGws9THRU+mUJ9lEqU/Cr9m1RK1EIi/Af7z8yOWY0ZP4ZoT0QMVtJcVjHmhLW+MmE8'
        b'Hmd7fr3YRut/KpvKu7Ti+6NYelksVsZFzsPHCsEpR7ZEC9f56vSCvilR0bGcQwXu9pQIqq1S7Nw3lqNlClH2Yiv1Ctoi8Z0npMpG2SQbq01aJQyefJKnyy2ESVYsI8Ik'
        b'J8Ik44RJzkmS7LA8cdh3C2E6ToRp/VOEicwqs9uDjImdV9NaT6Pxc2yMBXCKo03l06TOMu9NYaRlREWMQnnsIdaRzZXHw3qgjnEVgy7XrDeIxj5HZyBWtldkJdZjdSPt'
        b'cpzVXFNHPBKoRf1eXZjBkG3w4JVpKSVtVOtrdDkGXSqNJM1LbaaC1orVqXx8XJXna6xH/4a6qc7Upxi0xItG1LZJn5nJWIlBtzc7T+RYeTqDkdW35Nk0kgmKyUmkkqOl'
        b'90wOZZGmWGK0aJ/VBCOe4ZnaDLVeHEVqtsGgM+ZkZ6WxI4eMfxp3ZZsz08SeM2pEXdca1fm6zMznMacwPZP1EFEjvqxVB3ibzDlEwCx0jE8XSW4+y+HFGtJ8B4+SWfR2'
        b'JI+yizVnMXBrJSJwmzzsYHs46ucgx6O0AjrWY8HqSDifpYeW2a7k4RTCE6xfGotXppK9r820wTOh2K0j69imtMPHL+72hnvkf9+Gyil43BQF9cHYTPgK96E7HEqwVyaF'
        b'xxPIRVFxC9iTww/kxZ+SJ2eGTdko8PVNaEzASu5UlcabilRhSVx0ZIxEcMeGyavlh1KXiazvp+uVzHoG7ZybnPn51lxhg74m6rTEuIWS/sPzK8fX/Z2Oql3kL32wXP3H'
        b'xY9fPvney7+8XHE6Ydppxx8dvbBu6bnrU1+BGcdLPjpTetkpUXXhcfsVm7JC46lPin/SeifG8YNrd9fd33sqw/iwsfajNzd3Tg91G9t4c4rGhlsiGs3xJM84LyyVRa8T'
        b'5Bsl8GBcsIltO5h8WTDwxsFI7/nrYmLJOLBDZyqWk4xKeZSNEIoNNmHE126Z2GnRw9CwiBLuSYhbVHnSQEVcUwoT1sg9Zu0wcXZ4Yl1+VJx3pJdG84KnVFBBtxQfpSbw'
        b'8lgDF8krLBsSlIQwsVFwXi/bCN1bTGoGvXACu5+W5maoYNL0XGviMi93wQdRPutivCKhQgRVGQsAN06CbnmWDdZqZE8j+vMsF4f1AdWw1c0NlbtoqNIIyL+VS23J9NiT'
        b'AXIl42MrMTgPGR/FgK11xQ7YWNaeaD0c2MWR5ZEO64jMwEKRBhd2sRu0KqzCd4ZZlU7X51sVbtqvrFCMFgAN3g7q5VkLXMwM4LEMziYNc/NFH78VT8NxsjXlcNFLtgOK'
        b'oTVqAVTmwk24Dv32QgrWOmITFG4TOen5xViiynOitvHMYWgnWm8DTTwpDHqxXJWXy5KKo/Eq8UU3LOMsfG4Ij347B8gFKdZiPfZK3CRkw5ifs3D1SmMACU6S7ewoQO8C'
        b'rOY0cs14qFDl5SmpshPYv4Q4vj8WWw4MLZqdYLVrWKuX+C6ES/y00vwlcNwaUICijdaAgu9qy0nClOWeZCslxKYqWYhNEgqPDz9lEgfdtHBmEmXcKIoHgaVFtum2g6ZR'
        b'/nebxnQyjZ89L5bAofU/jyRwfGZYzrL/53GE57j3rPD/d+8+NZN3y6gzPe3Pj+ogk0t2aqqZTFFW6tMdtXr0YfHB6lBicgZmqtb83cfgn6qPH4sf1jctmxQzP9PvkRi6'
        b'wcOL/qxZw/6ExiX401/qnkdIQAhPCA318HqqxmFj0mYas58Zl2CD5HLOEaMRVGsas5r7c0YJkP1szGFl8xb7LPHZx2t/JivK146kRYy0sCaeqi4752mC9N8b+ZAIz4p8'
        b'OFkiH/8S7y74CfenCsnJ251njxOjGb9eO1aYLbyUIROSp2xaYRDMDBmx6MVgKKO6NrFoiDlFPJ54F+7jeeuRcelYLNJI7KAPe3g9dWksKqJWOfole7VM0RPoilGESnyI'
        b'nYEsvnBY8Bf84VwIByLokGJBoJwFrc8LAULAQjWvpVjtIqiFeD9ZTnJ0ozqJ1cLDM11w1IcqgSY8yWo5qBMrL4XjbthlI2DPGCFeiMcTk8Xz+MH2wjjhw3BHl+RMj/Rt'
        b'ZOx/1fWt1PiAkpZM+zfvmOVOx4JcDgX2HX3y9sl/lu2TViXPOHGn6+zPquO9Tq65cvrH5fV+yZ9qVjj9Kico4Ad/rXpFa25uTXz44/HbxhmrZsWqQvKX2+o2h/S/0vD+'
        b'ku4JuxovZy7v/3r+iZ7ahBhHw4RFTW0tW1ovGf6lq2Wb2w+Xrnj7zbqXr7l8+2rPqdcSqlaFpbTXbpifdHLtyVfHQ99XSw7GnI84+Kt3fvbFb5d/qfz31/9pbXbTe2dm'
        b'af9YkbvwRojyXLr79MM9diucxm7UKLlPCTfxqJ/Ve9XjnWHuqyte43zDfVoI83vxtJ3o+kq98f5YTg50ac5YRjZrArZgpSAoF0id8BheNbH4sNf60CisiIqHTnJWRUfV'
        b'2U+WAXf1pllsBvqwG28OOcV4JxjLHZzslIIL9sumEFNo59VA9yw4KbrE2AlPRLdYGjgZ72skogG2/Yf8WpEd2IleLOEy5wY+Ijc4IsjJiZU7cCfWlYw1uaZS5sbOpI+7'
        b'5SM6uIaxwxjDkHM5ICOAHEYU/jO/VDbMLx03SB5Y3X8aRh6qJz2fPDAeBhc3bh30SeO4bR2DRavwgYxowWmpRsKX2zj3acMj/afwHAv1n8C7Tz1RM+hXsueryHCSIU2X'
        b'DT4zI/m7nplhpnOXRv7N5yPAJUEEp+f4KCKW6kSbx50OH24107MzM7PzKddIoOKGTc8cVINObTTn5GQbyMlbpl4T5qUO3uClDo0YZY3/G+H32d7pU1Fj+VPYaRPLn3RK'
        b'1MBjxsk9aeVhSfR6vG0yEE/ujZQJU6FFPhPb4LQ5lKlINl5mz+lsihiKJHjCCe8XIrxY0fLIaCyN3BiBZb4JEVby1LaBPTBlA32O8AiKVOIpmFopMbzj83hdObToXmBl'
        b'aIFKoDbMHppjofKwPbThCSEJjtpod2Zz4Dvpw8BcEPx25slTFJGC3u/JL6XGPLpzpX/ywjJ/JwhykOcfyvqspbrzjVn77LrrOjWunqc/OK7+IPDDG+8XtLzQF/iLt77+'
        b'0GDa/KOK712KCX+in3muds6H25de2BEtnefw6sSWfaerFyeG1kcdqX9luqN5h//5/ISaAxdCHK/HtX5de6j624Dytzyd/mrzH17qsXPuaxQmFluZsElDqnvUClvDMAsL'
        b'onjILQQvLng64oYnodPGEnM7APdM/CRYXQzexy4mjDtY7k3OUQEWR2JFDIkyMibXUnkUEFO+nbjIxGYzaQP0kk8Ex3YSG82TBOfBExM//XcVj4ZZW5XnOxscnfGuQ66j'
        b'UpgyWy4lU3ecsOI7sOC5cGWToTMNgtU0K1hpbAmKXCTMlXGyAJM9/e8iMbgNglOrTIx3DUHS6GZaJWIOjjys4HSCA6NaRJ6jwicuz8cehirO0DKLyYKcx9KEiYQ8qvVS'
        b'rFTjreejyjILqqRL/wuYcpwwpW3EokvMydSbGBcfgg3ilrRw2d10gzaDbxKNggIrEGnVC54Z0RiReX5o3MbYDQlbGKSEhUYlbozxUlMrUUmhcRxrQnl6UuzGmJCwBM3z'
        b'EUFqkcRIRFCKjwy+mcjC8ckT7dTJ0T8PtxPMS+jmod3QHpw9HCiGFrmc3GJotYdz+y3LV6A1cdLeFh5DHz+MiheX4qWnQYYjzHqzfGZmrj7IpVthjKS8qb//9LfJ0doI'
        b'baauNq1F16L9LHl+qlethu7sTs9M+VwojQjwSv48eftrm9/YjJszlXVa5evv+C1280ne+prLmy/9XCr8erqz/t1JGhkPDaTjDWghwLnwjDXqgNUmpmgT8Xoopw+cO2w5'
        b'ROwhEG9yq49F0B4V5Utl2DMn3vOVgp27FC7ZY+MI31v6zNViT66KcZjn72pdMEFsidjyxUI+/6TBRWKYMLoy98EVwXItHrEi3nD6blfeH0rSPSO8PGKtnnwkVskEN+iT'
        b'j8czYWSM2dzsxAvkSnNzzIIjvlAq2u1JR/BstHyXPbT+z62fj+SSUe7scLPMI5NZ2r3ccbIuKrbfmqMj54uZabLSom2OzFKnao260cvFGi82DTfd/+vNtXWBjlyc8lge'
        b'Akmcuge7jNhtVghSbJbkYsNMKMZr+uyvLglG9jDVy4aQ3yZ/lpyZHq2tS7NN//BNos2npGUrf3Ztm6hi0ufrqwNHdxI7kzrXWKVVYxMMU4ZB+YCK6XRStoHZgmeHowjN'
        b'pw3qLisbMUJ3H36H7jKzacQOrBfhnNMNrKTlG6MQpkMtNjnIsQnuQM3zNXOVqJks7DK0D/EPMsaPXEYHW4awOk3PZ1Fr2K/O15t2DcUPDNlmE1MyfRbDby0P749gkyMq'
        b'fJY2q0c8jT8Yhhiu5MMVe6R2/WNKPrzoiH+C87T6TG0KGaM9uv3GZSNXgzd1bMMyS7iEdF1vUm8waLOM6TrD6Hxr1ljyicNQr9GlUG6yYqOMk7eaRUKel9ffS+2RNrh3'
        b'4jG6aEhAyDNL0v3RWRNDQ60d1xrSBoM9o3LFBseELeNRHA4/321Gn95GsBXNqDJZPI3hImgPVi4NE/hx6+n5WcPtIKe/8QlErGu9X5AKvrFkSreiGNDEYxvkUJaCpwV+'
        b'cCMJKnm1H+x15URYnb1nRbGjRuAHr7AgHAs4oWaP0OMZLPFmIfeoTcOp9TpGqtcJ++GJLVxbtUF/UfGmxJhJpZ1+85PfJv8+eXf9TgKNN9M1rr9Nlt/ZM/FPs5ed3T1x'
        b'mftu94aJZf+6zj3h7G73l49+PveVSScVQT2aN1UFf5oTrTq7x90twO140GaNg8brZnRtUM3WVya98vGCi6vec5rbsuoVhZdq4rGJSwKFhY6T75/bSryZP4PfHuLnr3mG'
        b'SYa+w9yhPxLsyH1trDd4W11tuLyVk+4Vi1yhzDkP70FJfq5DrhyvwXHByUsKfWvhATfo2IxlCkIPxopp1DckwXAZLopJ9dvDg7aw8C55N4J8kYQ8k0LzCGP+n0b0GUxa'
        b'FvrwiP4RQecgtZfKORF2kEzhVNgwY8i6T31+7dMHsZLl3zACK78rZM9UAbqgFJo4WDKiIk69jTCZXOpivC2HliXYZXG9oQgfQDuRAhYFkS/GdqiRQGcAHuOM3vojHw6l'
        b'QQLf0hVfZCFJV1jAVMpfWSEjMJVyMJVxAJUeJvAc+j50Cu6b90Yso+hsbZpRvVebk0MyNIqQl5a9V2c06VMH9yn5QS3+3pJBSEzXEyYZc3Sp+nS9Lm1ElSn71R45WtMu'
        b'Dx569WBb8obvPPSlz9Kb9NpMdSb1hSy2pTMj6jRxDMy37LTmmA0ZowPlI/DAVnh2kFJ8EufmYrjDJR8fgSVx3i+w1174+kLt+gi4icVepOVrJTaLZ8J1HqhMNs+ZvdTT'
        b'g2Z6q4A3Ypz4Vn44tjJvPZJtqN2Ee1geKBdsoUy6DluxTyOyvki8n0q+4zkW8yIf3aIMTtAvi4Dbm8XDPVfhCtnPq9icSCo3W5gNfQs5uExys3jZq1IDX1gqF+OoxZNE'
        b'IPPb+b1xb4Ttsxwrq18MN6DegcVSGTxttOGPZLnDiRFMH+7CWY5ycC+BhQI8sFmOxXDajtes8RMPofm5XTT0Zm0Qm5P5i4fQ/ObqJO+EbxD0X1Sdkxo/pZT5H+Z4x0at'
        b'Cw126WjO3un6/ROvveFt+gOcWJwz41jW1ZJd6ur6LZE/muusXfTx+PS8aTh2v/KvreNiJux494ONn6s8xv9015EGh59E2HhcX7Io8+f9v6haFRq/N/T6Nr/GlO7jv3td'
        b'8ZdNv7qY9L7ebuNP4/uXxXzvi7MhFXsbzu9Z8SjdM+/tG6s6Tv/oZ4snOfWV5Dt+Nbfvc1XJ9BJ8xeHCx79tnPWjhtcP/+Jbz9zUIt8f/LxkNdZtXPGj/R9O/mP6C68F'
        b'r/aZvSJ08eV9JR/73Nl249OkynEL1t7qvDJudkd81fmdEVF2v/km/f2LL34jOTY+JP1F0DjzUGdUCnYNLtOkbFqkWJVhYgTPbiocxTKvWJLyiUXE6RWCLZZJD0E71nB0'
        b'xIvYCA/ifJ8BrspAXjcW5jt7rouJlgjyGTRfHRJo8nIX91irdkg8fTRY6kX2Czqkij2BUI39PKaAJyOghj127ulDmlvCVJCpFk3qBLgnj1iDJ3i8IxqKXrREHsrhzIhT'
        b'RtYzRvfdTAwx/UlTeklFI2O8pILSRuqMx22hG69zA+GP5xdhu6f1jNHQ+aIV0MVLz8rbaOkIsw6V0hjs8SYZNIpe20W8FzT8+JIUW/Bx4Dry91jlIXBscsh+z1jvyMiY'
        b'KC+s0EgEN3wkD4AG6jbfBr6JJ7Z60mIbFhUeCglDtQ+X4zg8paRKJFjnJ0ihQRKDt7CUz5EEq7CILQEN9kJZDMnIFvukUDMTev7+KPF3hGiGGSMnBl9Jg5DJ7ZGf1R4d'
        b'cOCBmbkSB26VRJ9Tyq2TE7868N1ndt8wa9BOtcoH5AxJBxQcRIfx+2farlapgVEbw5xBE8aqMowwYdXjnm/CWGG8PpU918o25a2MnwcYGWQshUdOCmjLwPqnjNTTm6xD'
        b'b1uSDG6y/iOmikWKnzzDVD3Fx59nk4bZoRHV/Jds0ogWR1T3d9sktv8/eLJ90CaNFW2SMzTCTatN6kwdMksjbRKWWp4lerwMO7lNSobbzCxBr4e4gdaAlYssdonbpPDD'
        b'zCplh2gs+wId2OPwtEHCK3g0Ao+aNFLzWlbLw4UORm4r8B5zcaHHKc/RHrtMeRtt85yggHhOE/ZDIUHSOTiZA5VwCmrGQq1yx/YM9vDcUVd4sAHumNlJQBNeThmsi722'
        b'Z3R1wXB7x3a8mJmBT9ShS7CIulVsFwmFgQLUHXGF23BnBjdHEXkyn99J2bfkzJMzVok2qtzWLbZZsplYePLBiK3TxJv/MlnuN0lGtjso2WFMyDLBHEg3PbEUj6uwgnmw'
        b'jItXJdoScV0fwWxk5EbogRJO0UtjCMZSD9lun41HxdfGEIm/D+wpoRVCLlauwDNwQyPl7TROGZvcK7CHFJJXlB86IDae6+Lu8ktZMt1LnlIatEf0NjQrtg3ZYoLjuuin'
        b'bfHYNI2Sn5SYHUty7dquGgouzMxItjzXQoI+uWSl9bwGsXe8ihXiQY4TCVBBTKLNemJDwMYDa/mpQngMF7HPCNcPDh7ZkLjh1al8fJMOjsUeKLYc2RCgVwet4vGKOrM7'
        b'3Mca66EN0i1onc3HWJk30c8kFcd42+WQOPC/2I/d+aIojYNRXpMJNUVVvb1/H/YlDOvy9FDLg5JwK90XSob1NyVU7G8r3KQepfoO6y4pXSHnO442S6Agb6i78/J5bwPI'
        b'Lh9LgLrhvS2O0seYKqTGBYSA/W2RK+P6Yl8O+v5th+78Ux/M/upDe/n70+Pjg44oFA+nXwyKWJuxforrzAfzT3/gMmOv5Fhp6cxfa34/+Wsvj0c1xV57MlZ+8qq894RT'
        b'4R9y8zdPBrcL/le/d2pG1OvnD60ek/xZpvOxxUHVu7rdPsrNlfS9YXxpRtbCiX1Xi3w2Xru0wWtp5M9cqo/4R90/1hcYufTS5+7dzU5bfyr7hbLNe7JO/ZuX1XU7Htxc'
        b'+Sl6bz700y31X+UW/lhza5nus8o//P7G+7+9dfHyqxUT5u0MeP1adUn0zx09Jnj1uenfTv7Xdqeew/LcgL++ZmN7suuFQ87zp6/3v/x68fUxP/78jXcn9o2v+2v1OwPt'
        b'm/a+svLPNn8ueLehadnq4srfdBRsLln5m+xw1bsX/qkxY0WSx5+/nHjuyL+6piw0eH76T+HGmBzHf/v36T/4of586AyNijtqHmp/T7yHN60kiFGg9nSR4jSTxpVbSBBn'
        b'QDNphRMJwvNQL24mP46ErtEMqJN4L7Eg2TLOdQLg9DpPbIK7FiZELAgfQrV4+rkyjOz3MCIEJZGBeAce8pNkcdCFN59mQbNmMh40Dis5PwnES3B76JS29AU46k0svUvk'
        b'FwV2i1QeWOHJClMP8c5hsZPToUuOtzKn8EG4YfnOQUd3G15mvq7o58JxuMBbWQAP4MkwDkVrrsAWuhy5BP1CYkZQpEyNtw6KNc7/2Bns7+Yo/5U9b0dOWYypmUns7ZOc'
        b'sURbGcsRYfIgZ5HI5XK+reTCjm1LbQc5DDvg7S562fwYt+X3Gwc7B4laZDOaQTZjYA6Nxubv6eK8QQbDitcyBjPTymCOCl98x+Y3U4u1siWcwSQzDuNL9IWYDH9L4Ww8'
        b'pVg+frOZ0SLoXIC3otatwp4hjoNnPKF1vkSYvVqxFK7N5+/EGqeCJnbKDGuifLBsho9MsMd6KfTDZa1GFhsbrpGEa6TiH0m4ftLOQqlxOo025OfyjbVbsn8SNO5Exoqd'
        b'XQv2nlpm99fHvtc+j1efuFt/SK/ynp0TsUtWcE8ye8HhGadfCV7zsc3/mfHLesPvNq9v//Hmrxr//MHyhpojy1e/cfiV3m1THvm890uYtLWmxq3mh18t/PKtP//Zb+uY'
        b'n6bJfvim/+b9yr5xB15+9/u7H7z+UffXvqvemKT4IXw6oWGSq/e0h3/uqHGvmte9d3Wf14EDXy5sSH9J9vs7EVtqZ0zcNW1byvjz90KXF7yTfK0vfM6WVPdvXv2FW4D7'
        b'K7bhffDJazOL/O+/duXozHvJnve0y/OS5+VpF/8l2XfOX29Pt2lZVhy6pHzWhqnf95/yqt3b8/wrE8++pG/83pZG3P8bc+vDoC/DtoMu+mP7zo8nrTsL5vdfWvA7zbqs'
        b'j92yPnFqCgjeOS0/1/kr/0KbfcVr973fpFclfZkgOZ9edk3xg5+smLG/Y8fbDzMifhwVtWOSyfjH+lt/+95YzfZf2h3pWDw77KVDM3oiw0u+NB5+O//KafhJZeXC0/Hb'
        b'f717zbl/amt4a+y+ygm/jf36l3v3vnT9i7uz3pp9d/O7fmUPVn107qODb9o8+sGi27e+mKTa/PLkhr+c+eaxJrzp5KSEiZ/Wbgqfs6rgq74vOrHkrbot4/c5d/xifVv2'
        b'OkXT3yTvLgn8pMNNp9RNv/POj1bsSXT7Z+/Ed++UH3h/z8v/dsPp1fyZAbs36Eq+Lg8/6Pui7I+FxXXrxi6ckuv2+MM9by59e9rfzJ4F733cGJnxYcdfpt7OeLP1321c'
        b'jnxc89FUci6ZcdwDTyZjWXT8XlLgJQIpaj3e447R9AUzh4PmZLhk8RxVcIMflknGR/OHA9cgamEdXiPkioEiEUBPQx32DDqwcIOMKXRCQSDH7wVQnBDFwLOUGnPHazEK'
        b'QQUVUkLMSwSx3IHrgTtBUdEePhFeY6CVVaLKlBJ8UwVsqWEZ+a1tUAZVcdwCEAWpwvoYYpVK2VToWscH40Kc5x4ll5IzVi4T5EvZE84SuIPX8TLvxkKq5MKISCKhqwPW'
        b'EMBu32xisBEGPenPeFyGObKqVObKPoTjonNccQCaR3mLW7HfeoaIKIy4L1+Hx9k+W/56M885amNeB6Umy9NSFxywTAIPvCKxgmyLcqd0Fl5fw3sNzfiEsGGdNxZHRmNH'
        b'aiwT3h0pWbLbVJwf4T2P5/Oi2FFqyoPlGXMiWZZbUmzDaniosf8vwLzrf6PNeNqEsK2bv+fCrYdtUhK3H0nilirbAnKTSqWSBZJp30ql7PkeV6mtbJzESSaX0q9SKrH8'
        b'fq10sLXn3/5daTt493/Xb7cy1oWfnLCVuMqk5KRPCWTu+rhJ9lJm8qZ4StmhLzd2dXXmV3t2dZvCru7T2HVagKvE4GG1uBrZgDQpaZgLP+Z/ZhIlBs9B48kaZ/zDyFah'
        b'8LnPd+9Sw2Ns3MKWsngmH0qgCsrX0lKeKJuaN1P/3qo8mXEX5Zu75ydTJ7e+7s9OOIZ/dCR9wsvr/F/efPbDpkfw8ubNCSFr//T+tpdi1rf9YY6v15c/vrq+zPHxQNoV'
        b'b83ffppV+u0Pvp/X/nGfObI4+vsFYzO2+pi2+2ctyT8w7eqmyZo/vT/u0L++88d+ycL5Ez+bFaixETnmKafZ3JzHMfggh1UFd+HKi1JscYA2ji+JwotRcd7sAf24uD14'
        b'I46I3hh8JCMMu7mDV+GbRuyMD4ztXTKMghv2NDBX2bStIeJmxGW4fDgqMmY+lHgQeinlUttg4o/8BGj9RD/yDMmrSFyWJeCVFOwRg3eP4OF2z3UKQRKFTdjA3gBRnCBi'
        b'Zv+WPZ6Dj1j4LlipFJx3yXbPwfMjdjem/88t5f93NZJ/57pn0RHLumfSExzZOSPxKIWt1Eukj4sMXoO6P2NAlqnLGpCzM9ADCn66ZkCeqTeaBuRsA3dAnp1DyTKjyTCg'
        b'SNlv0hkH5CnZ2ZkDMn2WaUCRTjBDfwzarAwqrc/KMZsGZKm7DAOybEPagDJdn2nS0T97tTkDsgP6nAGF1piq1w/Idun2URaqXmY07x1QGvnG64C93qjPMpq0Wam6ASU/'
        b'UZ7Kn+rQ5ZiMA2P2ZqctXZwkngVN02foTQMq4y59uilJxx4pG3A0Z6Xu0uqzdGlJun2pA3ZJSUadiT1vOKA0Z5mNurShBS6OfLphHfvOwmKG1eyykF3YVqGBHdowsIN4'
        b'Bnao0rCYXYLYhb1d07CIXVgAxcBep2VgkUTDSnZhARpDMLuwtwEalrNLGLuw00EG5n8b2ClBAwt6GELYhb3Uz8AOthnYuR5DFLusGgQJNkv2gyDxdcRzQYLn/MbW+vDn'
        b'gEtSkuW7xQ58Myl95Ovx1VnZJksELVZjyx7UTMtOJVnRF21mJqGhl0Wf2O4u3benaTGYjGwjf0CZmZ2qzTQOOAx/pM8QYxXssIuolCvEd/CvkgiW8z1yG1rEoiqGjZMw'
        b'QP6/4U1Z8w=='
    ))))
