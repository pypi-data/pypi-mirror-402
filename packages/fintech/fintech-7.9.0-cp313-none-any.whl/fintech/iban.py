
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
        b'eJzFvQdAlEf6P/5uZdml9ypLUVm6VAsWBJQOKtiiwAILLFJ3WXvBTpEmKiAWsAIiUizYczO5xHQ4kogkZ5JLLneXXBJNTL2U/zPz7iKoV3Lf7/f/Q33Z2Zn3mZlnnvJ5'
        b'npn39SNm3A9P+/vr9XA5yCxhVIwvo+Is4dgxKu4q3mJ95qmfJdwgDvvJXfuNXALf8lYJXJgg7Tez4F8W3BvOXSV0YZbwdXcoOKv0XJhVYxSkTI5AP0cm/HFAHD0/LEFa'
        b'UJSlyVdIi7KlpbkKadKG0tyiQukCZWGpIjNXWizPXCPPUfiIxcm5SrWubZYiW1moUEuzNYWZpcqiQrW0tEiamavIXCMlJNVSeWGWdH50OPuhRKNQbVAW5kgz5IVrpFny'
        b'Urk4W1VUQLtbEh4nzVKqFJmlRaoNXtJiTUa+Up2ryJJmbKD1CxWqAnmhNFxRWKqS50vnAwUfceakcaxxgn8Sws134JLKpHJSuam8VH6qIFWYqpcqStVPFadKUg1SDVON'
        b'Uo1TTVJNU81SzVMtUi1TrVKtU21SbVPtUu1THVIdUycdZFIcU2xTzFJEKXophin8FOMUcYp5ikGKfop1CpPCSzFJsUuxSBGkGKXYpEhS7FOsUoQplincFE6KQ8qkFNNA'
        b'J7KGeaJCp2THx+tSKJ3EpDg9LqdIH3+WMmFOYVI3xvkZ32Yzs3lOTDZHP1vGTcgcLw2m8M+cTJlPBSiHkQkT8kXwOaaIxyQvMoJP6QbfWjgwGiItaDc6hFtwFa5IjFuE'
        b'y/F5dB1XJ8pwdXRKkreQmRrJx7dRJe7M5IzrwkzXxQ64zDFNhW4oB/gweyFwRwQ8EQMPDIBPRsAnkxRT4Jt5oJmWA5xk/jgOcIEDnHEc4E6YKyeMSznw1LdjHNj1JAck'
        b'T3Ggj+VA7WQhE7jRDiikx70f7MTQLz/35DI3rFm23J7pyn653E2fabV1g+/SvXatzmS/dJ4nYLIMTBhmXnr+iax5TAeTL4avI/1t+I/MmHkPzDdw3nVonBa8QcPkEzVd'
        b'sqaJ06PHFN+an+7/nv8bcSvZr5VpXxsfMOYU2yd9wPll+e9CU5hRRuMNFR7oFL6Kq4pn4CrfRe7uuNI3yhtXoo5k95h4XOvlE+0dE89hCo31Z+OWaRpruGMxvo6Px8JN'
        b'PdFe0XyGz3BQiyOq17hCHd6BD+Kranx5naq0RKNGVfgcuozKUTms3ypeAG7Fl2UCjT2RgR34KL7JtpyEL5VoVFxGH93mum6aobEl9QN+qIKttnYo0ZRwGH28mzt1iq/G'
        b'gfTTIUDn2NoEwxIN7mWguoLriTrQdXp7kB8+xdaj2iUlmgA+EL/MtTI20RDtRM34COpi6/FlfLIEX8I9hEQ91xc1Fcp8NZbQyn4VblAbgAxK8W3cxKBDqBJd1VgQpY4J'
        b'V6sEdBLAOwYmWLWNVqBz29B2tUqPYYpxI65mUOVUrsaKVFxFF3Av9EhkBdfhOgbt43pTfs7Gp3GXGtWA4OCDqAu3Mego7oqgQ8Bl8Vyo4oKVRXvxCQYds0I7NUTO/CxR'
        b'pboExrDZANdCP67oLDuCatQUqMa9QoZJDMcHGVQ3yUtDdIcbLVJroP1qfAHXM6gqTk17RxfQgKnaEJrjPlSLjwNv0EHM0po/rUSN+/l0WTtxI9DSn0YrhPjmTDXaB5/W'
        b'4np8hEGH0/RYai24HR9TS2DAuDcStxJO70KXKQvs0JkV6nXgavBefBMfYlAN6sS9tAp3oW7UozYmFC6CQYD7mtZlUg48h/vX435DGESGHz7PoOO4HB1kb7qNbqFLErIO'
        b'aTC8c3APPlNMx8dF3XgvqoK14+Q4iRjU7azl2ubkaWrcB0u6WYX3M6hWgQZYWqcjgOn9GjK6a7iXcPrAtoV0SiX4AroqwT1kucvQbnwBFgFd4LGrWhGAj6vXwWxD0TFC'
        b'sBKfRpfouKOtn1PjKzDshegmbmZQPbB3Nx3cMjSADqiN4aZAdIn0dDhxKb1FiGpFuF8EFXoZ+BTh5XlUTceQBFNrgioYA65yxGdhCHg7bmfJrbDA/aWk5mgu6agWt6az'
        b'gzu5vBT3G8DKoip0ltx0FFfHUjYslYIB7ieinbQVtwM1b3N6ixGuisT9uBeGvQEdxidB5nNAoWyIxcXNaAD368M9iHCom0FtwKoOeh9Yg2KoIyzag24TFp0IQ7WsRJSV'
        b'rIEqwtgz6ApoGTqJjuDTdMKZ6HwuMB1GGONGJK8eVeB6WrMoxB4WHfrCtbHknhO4Erexszo1pRCG2A91wYtxJ+FSDTpEu1IHTyc1oHz4CuojwnIMBGs3rcN70BnUBMsI'
        b'9wWA54HhHxXgSlbJWlGluUREZnaBaCg6XYobtFqLd6oluA9I+oHSXoKBKHAfZSHqtimRrIUZy/EJ0lWz+XJKDN2wXCnBl4GDcUS8CdP3RtKFMjNeCBVCojNduB8kWQii'
        b'Qli7Cm3HB6GKsK8B3SDdtOH9eAe9C3hcn6QuJazY54jLgcHZS2lFNN6fIVET5dzrRTjehC7nsdM5kRUjEROFrse78FUGJn7JgRpFkQk+BrJwXBiM69AltE/A8PAJTqLV'
        b'asoiM8UCVLVm2lp8AGxIpYDh53LQdr+1Gmei5onoGqqiVf6gBQd19+ujaq41mJC9Mh41MsvNwFRWwWIXFaNLTBE+mK4h0GA9uhQUS1R4Db7CZOArwfTbqdn4aiyMM2sh'
        b'vsFk+aFGVhU70E1Uzs64Ygqd8TR0QDMFqgzBlpzCDQIwreXoXDDqEMjjUTU+lReOTq6MZwLVAnRwhhm7DO0cTzXVij4w8BUMWM8jvhR8zAlyxw1w/45NhEQ3+KsDlFog'
        b'OocP8hkHXM3XJ9pKV9lEzVXjixxiUc4Sm10jKdR4kEE2JKJySmY/OEvi49oJoSjUPUYH3eTzcNlUulZ5bgrqSBAYJepJ8PGFdEaFnimUSjuPDOb8uMF0sYPZzxemmNDl'
        b'sQBrcByMLpdVimMMOoKOoz2aqcRy8N1wQ5QRakNdwJUxKv5kVEDFm4cH8FHUQDlj4YV61SpYDFRui/cyaBceQP0aGXFEStDdBnwzl+VuN+UuupEnkeIq1L7UnImR6klQ'
        b'D75O55S9EQ1QJ4jPESwH5NabaXwZol4n8DHcgBqBQ+UTeQw+sJr86iTD8lYJSlBDACW2Au80p25TBAwlbhMP5FNiYHWOkFFFsTOr5mWwY0In8fUt+DCsPaqCpY/CA0J8'
        b'SZ7KqswVtHMTmHn4GJyPa8D8Fflr3EjFGeDDuTFi7IJlovZg/mIG7A0P9yStZFWoPw2dUYuB1TGzyHodBHxQrpkONY5qsCwNuEqPzIcue/WTK9ceT8h3xQsz4pkSdEEE'
        b'RqRpOR2YKTrsrkaVwPulIMdg8I4ULKKzREfm4Q4yru6x5eMBIyoAD+zJBk07zEzDx9GFPAGqgf5qqDwU44u4jwUU+MISCijARF2l8uCPd7oRucrF28dGx8pmJyubDTx8'
        b'Q23IzrViCupTG8FczUE4D4NwqvEtKuRoezZYJiDjAL7rCV3pYMVzL18P92BWsHw9URULYxbB+lEUc301xZiJaLc5FXNK5DHDNq8cpzCBmwSoeR2uprRMgGonC3yKjCju'
        b'mYxuaaYRzwDKf0NH7LGow2IMoJ2UdiAr9f64VoBa9Y1ZVNSErxpTuGQLDpLgpaQMNhTZv0ZCqOWYPNZi3TqyUzzPF6GaXBYQ4l50ksVWUXYUW6Hjco0fIbMHZKsaN2Sn'
        b'PzEwoNnFzpgqtDcYVnUhKqfkclEj3gfkQOzRcSviuw8oPNg1acCXplO0Ji+kYA3YVqbxIR1dx9eVUF2Na9meOklP4Do3EFlBe6ToBChqPL6p5492iVlT2K+PrrII7zTe'
        b'SRGexVyW2Hl0LHmMlzp1nwnuaedK92CWAWp0XIT34ctgPaypp9+H97OgEPXCwhFQiHauouSSJwHUaUCX5NoVeUrttSw4JFDPxrXsRNt9AawSl20Lju4oCB/IDusGemGO'
        b'NRRJLlrDAslDqEPjSYZ9mgtj0w77vM4HoDLv8HAp9E8sVSI+puezFZ2iRnzJVHyOgrT5KylGQ1ezqNZNRbsicIMDqtEZlwmjZqWBz/ig64I8wJqdVJASEnCPeh3x1B1B'
        b'RAKq0S47qnJrhCDTDVGFsFZd2lWZ4Fam8vD1PMTiHtyJLmaz6HA9PkTRoX8O9QepuN0RqCTBXMeZKCBynhCxx5d5uDdKxS5r3TJ8C4gQt3JxGgHhBybl0TFycEUCxZeo'
        b'BdA0AZhuQiqlACqaIWCZqIm0kxR0ZrwqlghQ0wZ8lEVO2/EtgPTGpJ8dqJcA0yPoKo9OGvWDt26BAc8OHTNdhI7O8fB4AJ4vF9LxLuCiOhbdbkUNFN76owt0PWEcF8H0'
        b'wLBws5gVl6e08CQYmgF0g45oPizyPhYNLwadJ2gYLPQNDQnV7SKIgX96guSbJbgjmI/6DOLDItD5KYwKHxSBxTypDQ3mlPizOHoTGC6Co6UOFJ2By9gOTrKfwgBc4U1k'
        b'8dBSgG7EfNigK+gA7a8VCI13muFSAeD7VgH46JPASbIuWagiGFA3rLrcGp8myLVrARVEUxCvG4993JitneOqZQK12gG4RQBO4coyOlxj61wW3JuAphBsX8zSWoqObXxs'
        b'HqvHTAT9hgfO69BKA8O8IM4igd503FHK6lp/ii0bDkBMfowGBE5oOzXd+EhIcSz1Z0BknMKhC1FjuGsxqtZzBnu0nxKzSoXorp9iZrAap8hEDwfIWIfSjG4XPeHLKRXi'
        b'wgMgGLqCdoGLs8VazL4PX8nC/UaEUjdYWAC5J93xZVbyWjGsZ0OUI5jkrgmS18lqSi+IXiyLnPB1dBpkqp+6k1ngP/oAE9sZaCYzJHJsXPNYXlgi6ABqJJDAAe0ApXVA'
        b'FynD3VGNF+4vARKro4m21c4WUdSEr8dhKgK40WhM3MYrAdrLA9vWzILztJUg6f0lJCg7FEgMXh3eP4WOBJTiPDBxIjjxSg3mEmxyBfQenwIXSDjMI3zShmlTkmiUhm95'
        b'U2EFchVg49kwbacdG6WVA76j0czeyDhtlNYAPpREaevxRVplhm6AZ6FhmgvcT6I0Y3yAzg807JAFDAv32j5hk7pZTvcApwGJsehdALBvFxvToTZHGtQFafGBEncZQQ2R'
        b'sg6YKqjR/uXBdOr5JR7QQQLqJEakU9cBGIUxK3JxZhZdymgYZQUQIXNomkxARgPoziGKDKZnOE1YSVZ3cA/q11kCKhrT8GEBBIbH0BVWvU8Dsj8B3LxEhtwIsSkoU3Nu'
        b'HvVoz3lonhQOmHfzHB3sYwkuE4APPA0xCmHAJGD4RYhdCUwvowvQio4Zs0HD6UV+E90W2Al8DR167LeS4vRmWKBj1FxsRVXbtEFwRyENgiVFVCfz7FZMNBYUTCXi1vFc'
        b'C0C3Bah25mbWV5zWnwKkgGt5MFsISk+uBKAVQGoIkDg/gRw3k44MlaOOvHATGNhAsCkqD+KglnnihDmYRZ+gygMQzrOBuJMVDcQtUAuVmFxg7jFCsi90Yjyis+YykGB8'
        b'FZ2gC5CMKtA1bdwOgOQcG7f3si4avONODgRbEMU9BfjGYwqNgOTbztGhCQG01kGkTwDPCViN88Rh1dlq/Wu/J4wsCjqaKMvnWFm+ysN9fiaU/YsCrNl0Ae6V03TBNFTF'
        b'KvwZvN2WKvzNpKdAozaGvM03EruwrG+2wQ0SEQwmR0Ii+1MQW5bRsSjBiVXCYOSOT1iwLnYs3TzcXbyCNdCnIJa6RVMUViDxJEWxEnezNrUnBZzykxhuFjo3Tqi89EIW'
        b'oF52OK2oc5mklMC347DuYJwbOLm0jxW4z5xNdeB6H5rqwKdwJTV909FuU5pRQNsTaUIhOZ4lNoCurpOsBWKhwbiDhEntiB2VG+qlXigF7xjzQBN0mhjF2+g0PkUJuUB0'
        b'0y5ZCz0YBpBEXiPo7E2NP1nMKHALz5LOCtwJjqMf5BjvysMnVzKqNRBplaLd7Mj2A845S/MzURtpemY1bqfK44sbXZ5hJtA5gZk20OrCnbYQOYDNrmPN5nHUsZ5N6eBd'
        b'cTSlw8Nt1OSgAZrUakC3pmjVegJ6HBfrogZBKa6RsrpTocQX2FQQvo730FzQVnSQ9VVXcZm1NhdUDVpCckFOqIdKpNdyd4kRiIAZiN4NBujvgDnRYfTiS1nPmtQNXDMO'
        b'BBDb1waAZMs8ylp0GHWBMDXo4ojqCXfjnaiX2HhBSRAnSaQXDOy4zKK1Stw+ecyMjS1slyADViOe8bfGNy0FaB/028JGWJUhNMbAA45j+ForCmyOA/Xx+fhwCmsi9+PW'
        b'JbQ1+IInZ3Oe1a1KCMhurKW0k9eBPwDXdODJzIdOEWfxAIyUx1D0axRDwpMn7UggBoM40Z7jBgE6ss1PJqKitFqOT0iMwDHaA2C7xYCT2o3YVGQMjLZNgnthSdbCYoFW'
        b'tkEYT5fKPA9fhRq4qxhCzwEwuPkh9B412os7JfoEnFetJqt4Fma6nfXdnagMl0k0VM7g+/NED1ohhqHOAEzZNZruy0lhs317WdMeiA9FS9REa4/DHxCXY5Goj94SpZkF'
        b'WIOYQScbfJNYnnKlJoR0VAsGt4sgblSuzfah81olReVyvJumB/moPxlVpTDLVgtBO1tQm4xPN27wDYDbV3AVeLmLcTF4Hw/wyC1wDnJ8hg5oHqx9TSyujBNCeHuR4aZy'
        b'fA0TNHZEl3F58gxUH4trfHG1pwx18hkDE54l2h5Db3TGh709wRtdTfCO4jP8eRzUabo8k2yn6X7IRhbdY1tL8LpQt7V6kEnhpOilcFNEKQzdBOSlSAL1tdt+/GThuG0/'
        b'wSQmZdw2YIpgwgYfP0xAt/2e+nZs2y9HxpVfhvUWh5OtZbKZTLeXpdlFKulaeb4yS1m6wUcsnlksV8kLpMoMeeFMaXKugm1UWiTNULCb0oosH12jDGXmTGl0tjRHuVZR'
        b'6MW21G5WS+WqsfZSZSHZfhZL4SezqLBUsb6UbJAr5Jm50iKoUI0RzCzSFJaqNownWqobglL9b+iVkj11LQUfabxGXUrGTKa5JNE7YFpwsDQsLikqTOqvvTFLMdavWlEs'
        b'p516kE8eUgUwRCMvVdCt+PT0ZJVGkZ4+YSwsDe14WO5QJmrHJl2iLMzJV0gjNaoiaZJ8Q4GisFQtDVMp5NCnSlGqURWqZ45RlhYVji2BF3y7QJ6vpl8T5qxTqmGgEzZs'
        b'+cyTG7YmCQvoluuf3GwYMBjTv0pPX1W1dCZDM9uoLxFtR1WM2XPgKpkVLriatq30kzCgbKJ3HNO9Iks92D3bAitjxoFh0nOmp8ftXBXKaDPSAGuOkISGx1KGJjRQn6HM'
        b'mN1MOGfkQ2pWgkWgVXGWbCazR8knW2YQg9YxdMvMYSOtUKDLz5Htsni0i97QFIDqWaRwGbUJ6X4ZeO/DDN0xkwfRGSx21yObZeHoIkM3y1yF7LiO2KMdkmLopHcNQ2K/'
        b'Rtw7j9Ykgd4fkJTwmLyZDMGfLeiq1l+jfqkN3V7bhm5xyP4aBFfdrP/aDZYQELpaCBiF9AQQfb/SkM5y9SwfuvmG6uwZuvvmFEKppZp60q03uG+AoVtvqPI5Ok3DFbiC'
        b'br3xHBm68QZ2ht4StQKsIWFMLbrAEMt7LAEAA2XZcXwNglmY6LYMBrdAZ+lBtHd8Kh0NqNfpMcs2MCRtVZvCYTm2G9UnkvQQ7l/BsPmhg/iQjEdvMjW2pVWNs7VVbYXs'
        b'TRfwJZgo6QZdncv247GR3hLuZEJ6mTeZ7QWASgUd8nQYWTPNnMVF0ao6OWqVcSnX3CJRG62CwTSzlagHsXujVuCoDtDNVqNFDN1rhaD6EpUz42w9xoBhbFZ5p+d/I01j'
        b'KAOS5sgC/PgA34AzqIHJQB2oTPn3h6N8ugNh/ZfVWxbNTsR+JlsS3tB0FzTVjeTKDLz2rahMz0gPf2XGkrNRKc2V16TZbr9wf20MqG4oD1zf+/MXW468WfuT4ZtXpnf/'
        b'6LDx68m/rrIzWDr098+M/6z8+e1V6M2lr/jafTuLo6ce6O5pa79m3J0z72DpcoG9x5Qf17/7yVzlLxGzz6+LVL2QUfBucWzI3+PNol23Fen9cPVa9s8JNz9P/XB1S3p4'
        b'ZJSX/MuZN35Jfu/nEHOF+uWpPx5+4YV3PCWpf7p29/ad8mD7IVXic/tyz7qOrkjcVLLyXMOvJwumzC26uer78OPfba3T5Ekjv9zBe3VV+dY3iz4+65lsMXty2lxeyACa'
        b'UlFhpBF79SaddZz0B8HaPbe3MtZWAbsFZTLBI7qWh6PTPb3do3DffG8uRA+Hud6oefYjRyLnLU6LJLF4nyxe4+2BK325BJSdtUR7+aIc60dkS8EdVaHrqGod7itFNfiK'
        b'xkCEe/BFtVeEHmON+nioGV/IeWRDvdtBsu9Y4eENznWHDwc62sENWLD6ETk5BEQub/L0ifbykPngWi9cQXaJW2yk/FQAsuUyo1Guu0xlAg3/Jxc1OW5CLK60TPczahma'
        b'rSraqCiUZrOnq3yIy5ozKqZGOY0UVPTsALk9A8Tn+zLm25UCxsKmKbA18OzMtpknQ4ftfUesHR5weYaO9wLnDJQOB0YMmUyr47eKHggZE4sDm4eNXdtFNwyeTx6aHjPs'
        b'HgON7xub3bOWtpq35ty19hmy9hmxl45Y2TYq65Wt3NbwYSv3Ot6IufWR0GHzqR0LeyLOxQ8sGfaaB62+FTI2TiOTnFudW8OacusW3je2GrFzPu7d7N3iW6cH9zTOrZ/b'
        b'GnjX3H3I3H3EetIDhjM1ifM1w7FJ4nzg5PZAQD7AsKzsGtPq01qT71p6DFl6QMPBKcHD1sEj0ITH2IR8YGn7RH3rmmHradpq/w9sHY87NTu1W9+1nTZkOw3Gdd/YvInf'
        b'mjBs4w+zGzGxqFtUt7hO1BRYb9zq1lrSbtoqGzLxLA+7Z+7Wuggm1R44ZO47aOD7/aO5jMUkGB6wDljIg98/qsnO6HFJRCjzQqg4Up/3exEHrmRrjJEZjPLJkozyADOM'
        b'6mm9NCg2uNtRvbQ0laYwLW1UkpaWma+QF2qK4Zt/LRBgO5h0+NFJhIr0TRecXo6TNjPg8lMZ890mPocz5RsGLh8aWVetKZM84Ao4FvckZlUzPuQb74ofERnfE5l//1DA'
        b'CEx0pR/VxEodEXoxXZIQHphULX7sWhoLwBFXJfia4ZrEaAFjVMybPhU3UBjsgOv8vHNi4xJYmMhhJCu5uNs6kXU8N3E3nwWXt3wptvTENzN1xxcnuPU8ghG5LEakCJEB'
        b'hCgM5GtxIS95HMor5AMu5I3DhfwJCJAXxqe48Klvxx+Ik9+juBDQCYE8Y8CQHCuU6w4N0uOGBDRRhCfPpEsoLdQUZBD8JiZI0WMNgLEiqn8eurOOBLapFCUapYrFScUK'
        b'FQDOAhas6U48+ogTdUgHOvRYDJSVBYpIlapI5UEJyKEGYKc4QlGsUmTCKLO8pBporCMgzaRjp1rvLtOdvnw8HGm+MkMlB1goXqbMzydgTaUoKFrLQsm1CpWa0Jj+GP2S'
        b'yZK5sgj4SQ6MwUYtF9hWT7JkPEZekC/PkSrZUWUWqVQKdXFRYRY5xUmgsjq3SJOfxY6KIEMYllwtXafIzx8PFiOVhEePMSjAdrnU37tUUww4U4s6KWth9u6khRchLnsC'
        b'Ogqego76CZoCivH0cZ8hLg8TozI/Az4uQxdw1yK8fW40ailUonY3M4i5dqLbuHFGAj7pCEBnf74ePhSOLyrA0HcK9fGtTXne6DI+j3sA6+FdNmhPaSxqDKPptosLAExc'
        b'4XHRLWu809uNQoAwJ24CgWCgyHF/Wath6PE2sWssRHe1Mm9oX0sOWUZv4MRzGPu5/C34ENrBotyvNuuZ/IOxoecSn9efziQrF72g5KrVULXl58v9mc2vmCCrF+4kfl7G'
        b'2WF7sjk9f4l77HbnJlnT71pktc6HHadYv2LymsNrGa8YfKicF7nEbZ5/2JHlrymCFLtaXrR6pQ5X+snKrZdsEcWK1H72r/20uDVWvGv+cvm3btzfu+6Ka0q2mW+bYjN9'
        b'mFP2q5H334dkeqwvPmEW6pnohSt5DD+FA0DsNrqqVD2ieYQbfui2OtrbPSY+ATyk4zKwILUS0hbc6r5YPSYcH9aL9Fj4iJ5DrESN83EV+NWduAbXegITcE1UPK4RMtYR'
        b'fA9Yge2PSEiKr+N2dWyidzTujfGSybiMBF3k4hvb8CnW/1ea4Eu46jEjOYzxIh7ujktZgU49ciEEthfnPMFr1IMParkNC1xDHXyGKe6L9YmJ94omCde4mECA0hA526GL'
        b'/MKEYJnef+K+9Vj3PWaoRyXjFFblonPTSoa66QcL9BhDy9r4inhwgva+7/nNfwT+JYLzkYHje+Z2TTNbt/Qo7pqHDpmHjpjY3TVxHTJxbQ17y2TKiMy7Tkx+27retfUd'
        b'svXtEQ1MfT5w2DaqIqY8Ajz3iLV93cZBE2fwtuWxXxN1YJ2T3qhIp/Gjelo9VhFAqiIIV2Xz9GS0nof1Oi66y1s6r/MP8DoKIYfjBhPguP0Gr/M1Ee9DwinMGck0nmY2'
        b'FApWSZ9Kd3Tgg2gX6kP7UKsXb3VsIKopQefRGdyBbqGbYiYD7zfER+GuRvYAwX7PbMlaI46DGcOBQAyfQ1fd2ezgbkPcLllbwtFDx6GqHCA6qtnGpmacItRTQ/FlY38+'
        b'w8X7OVaoEh9kY5HK1C1qfxV3DdrBcIoYdMVrAyU2nRy9lKxdK0S7rIDYbobuq8jYw4Z4PyDNNur88M006vzm4kPUZ7pMcp7h9VRe5fZcdqcQpNkTvCknewvDRTWc8Ofi'
        b'J3hMkc6aqZjHWRXwmIIUNq9CDlZzU8SBojHPKfxf9Jy54DnjuOMyKtSaPzufQt0AcROkybOzKf8k+UFu+D/NfWTm0y7VitKnsx1PdE7mVpSZqQEPVpjJDkKX74hMCpOG'
        b'A3hTEa8W8R8/hEBp0AcRxo1BThiooU9ReCwJT/bwgl8REeRXeOLiafAbhuEx338+rQgP9/CiVMaNV56vLnpmdoZMgPKqmM3JAKUs4lQ3FANDCJGUYtJ+bYjPdJ/1lOIz'
        b'Qc06+URUQ7AIIUtJFBWzmOb/Is9jpM3zGK+1JXmeRZL0dIdTnils7ubYdHPGjWlV6jPpDl9uNmJzN/gYasMnUBV8avQk6R98EB+jRyqTIM7eAVbiCtrPHnPnmnP08XnU'
        b'R4n9oG/EODCiBQK/9PxAtRMD4T6xfoow0wC6p93LTGOmTeKwOaCruMwwAAL3PasYf8YfPF8jpSGJMwGdicrkFqd7fZIn09FwwddXApEFUwkJdEjM2pVy6TaykQY+sY9J'
        b'IseGHSmNv08VMxbM+gSeSXrc6wGh4OuDLg9w1e9BlVPj4er6eKMdfha79lq533knwnrBg5wPBSPpj0weNTf1uEz7YMGVYy/8Y3TOL4G5GSHxZ9+P+8vplz7QXzwr8Nx7'
        b'TGzddWHFW8qLs+4E5ESGedidPuv6QVbhjZDPM1ZdWrLQbWOeuGGBS6PN+Yt/7N/74Uh0whfVV9te/8usj2+HvO0yq+XIC1+tHLX5vM+/P6b7xauj/6j3vPjm1ktXVt6p'
        b'4Hi2pYx29x0veeOFiH/4RP0yQ/nq+24vu6TJ/jo9Ia34/b/GprX98QtrofHDrneuRjqeT3p0Y77ymlv565ssjfwX/HnXXesH3pP38rtlwkcEDuFetBc3sXF8AF8XydMo'
        b'Hu/H+2l4jvaggzNJFkCbAgDXcMwbdTrRSojYbxTjKvDeuIZhhIFcD3zAqATtoBDCB3dvjMXVsdn48ljwbuzHyzGQPCInZ8G/nM4dSxDUrsFXcK+BkT6ExvgmzwHtnPmI'
        b'iBE+hSpQOZsf0OYGcEV8QOIymf5vi/FJinwsvmdhgj4bzIPxVPnqQMIvLEj4NkLEmJg/4ApNnR+KGCePdtfhST51Cx8KISxtymwNuGs+dch8ao/eAO+KAYS5D6QQ+X/r'
        b'yNjYQ+WSsyvaVpx8bniSH9R8YO1y19p9yNq93fyutfeQtTd8d8/cqk7dML1J1TCnNbPduS27h3eyYCD8dtzVuDuWd0MTh0ITSeAPrUrqg5tWDJtPaXdtl3dM6Yke9phN'
        b'gmqAKerWaa2Lmta3h1yY3TH73Nxhp5nkFjvHJnkrp8mdhPx2R/KGIda3n3R8RvOM1sXt5sP23hftBhYOTYsYso8YtIgAnPL9o6mMjQvE2abO92AWPPjNxtmVonAZg2Xi'
        b'8GAeDuLAlYUyEha3EM0f5YFpfxaCeSb3JY9RzeN42ld3+Wo8spHrcThOjwDZOP3WePqw0IPplATxZByaO0wOwccA6dYVjN+M2Wg74dmpMRuYRVw8jz47xQf3LgjkjT0d'
        b'xftffDoKnPrGHvFi1nT/k4CN9SIK1kvTaMyH+vbsovz8onXQSsy6YiWJplUKqVpTXFykgqh1pjQi0ksaluwlDY8CbPA/dDaPw+d/4zX0ErRPOEkWkYDDk5yErIhbhHtK'
        b'VcD+k/gij3FE7XwXwQZNBNH7yqA10K5qWRSb6iCJDu+lUYDS9i0Bq7MvOg5XRqdE4SrfxVFjwC2ZPP6mh64bohuoA9XTbcstzqspnWKwIEtJe7A1HLQ/Ukxy3jXowuSt'
        b'YtQJUDENlenJUaMNNfi/n2rGuMfHEHF0+CIlj1F+9lGkQH0IyoFL9vZnHoPYrvMFE5T9yh1GaGdS6by7ZbuznceLz5u8JmpIVEgWGcgXLk17BT2f9PzyVodXTF7nLykw'
        b'PBD7Me/TnN2f5YgVg4rM9HlNO5IcX2EWW73wRhlnfnP6p18vn7/iA5+Pwkts1SL7zpfbvIYcihuZEpc7U4vrk6yWtm/wmLfWL9xPIuEd3jgp+RuTINHqI97MplYr1brP'
        b'ZAIaJpGDOOYTEq642p+11PPQAZpwBb+4l/dUwjVcT61LuBqjnY+8oGERPjoX9xN+9eJ93rg8GlfH4+p5uZ7R8SVaFxCLzumhHkdU/Yiku2wV02IT8bVJ3hyGu5YThtoL'
        b'aCiJLqAy8CDaHo1Vhsa4z6DEUMg4uPnN5HPxYbRTJvqP7TNZHF0OljXPejmKUmqcp+uMcxdrnB8m6BMznHXX3HXI3PU9K2nrpGErv0ETv3sBsweyhgPChwz8yhc2rR8x'
        b'tjqSP2zs8Z6VbNBj0WDyc0Mezw1brRo0WfWe2aSmdUNmU++aeQ6ZebZHDZsFlYffN7cCWoPOswayhpznD1uFD5qEjxibHSgYNoZOXFvDh0j+9QG4AOvymAcCxsyybnGd'
        b'vM76SPywqYw2aOe2m7YuHLLyImlaq/IYFWETazmFKqI0/9ReqoVEIh9Pns6ZXpzAXKkD4cMPJNco4nDMfqtZbBC6MiclPrxnG74Mhs0GsoYvkPt/YvaywextFC8pzleW'
        b'kkDmsWUDgA82h3ybrZLn0H1MsFw6+yiXBj4zAyV2D09MSUhevIJYusjw2CUp8V5SoBabFp5ITWA4rU9LSImfH7lYNtGA8Z4yYNoncmPn0k2j9ZVT0w0MHfMY+ljDHIsY'
        b'MDJn0YnHhu2xVeLj/TLUIUbNG1ibs5UcXd0jFk3GZezJxTa8G3fA/XsTn7CLOpuITs5VOt8P4Kifg+bB5xb0Zx4GC+Twmslrd1DdSybwOev1O8/X3Xn9eRPDU87Sppct'
        b'XklQ2JsYyMWKdEHfjiZbv3migLjVkzLdTwqTAwVve2XvWtG2L6yr6UzTfKWl8A0D5qfp4uZvzWU8FvDV4V2oWYJurpiwd0PtCOqMpZguHzfizseYbtWUQK4RuoRusGmh'
        b'XQvx8Vh0xtAXbvR2FzL6NlzUhrpRg4z/TLXmU7XWqbQYgkK1Ni8zR6fVyaxWP9isz1jbN/k3hdXlli8E3W1SDhtPpRo5d9hq3qDJvBELx6acIYspdy28hiy82pOHLfzL'
        b'I++b24yzACPmNo2h9aENcwYNnMdpn+Cfap9aoFM8Vu/m6C4h4/Tu2zX6v03vaKJlv9CFOSHxJnCE4F0ZOZdeRbAISYv5ospEXM0lOQvGbhs/NwVd+n+sn3cmwBKaji6U'
        b'F9AwWaex5LxBsQLCawJTAKWw2CS6UJopV5OGYl1yv3Q8XJH+v4QrT2s7P4E93lqLr4Nm9q8nT21c1AgYLj7GcVk2RfmX3Wv5auJQTT6oYtWxFQBBLgEE6zt+t69r3uLd'
        b'2wMcGd8vuC+8WciKF3ecPBGR1om7AfVgwEnCSNV8ncBbsQL/MB1iT6emTcPmnu0LhswDBg0CxovsqISoSVqRivrA/0B05+suUeNFN17M4dj+BtFVzYUbny2K2UQU+VpR'
        b'JEmwx5tG/+soWV5GNo0eO4IsJV1duWqDdJ2yNPdxVkhVpCklQqYsJM5BTvdrJiBo8bOkVjrhrRZjCaXxwiwdJ8zi3yrMYWvlynx5BniuNYoN6plisTd0lDxTm8gC2VWW'
        b'SpNV8kJ1tkJF6iIitHXsUKQRigxoAW4OvJe3lOSl/ln9NC+pR9bYxpUHaT7ff/4zW8P3MjqQcN1A5KqssbQa1CSExUfOpPkyqvr/bm9HxPrNv6TTU0F+fnOyCgO94xh6'
        b'hjd03SoSDEzH53V+j8L0pMXeS7mMbwJ4TtSAztCnXfPAK11wsCdJJJJBYlIo1cg5JN0EZBMa1yl9DBn6EEsu7o6gmJ+8jsEbV+B9scsA+eO2ceg/hoD+GGYDui1Cp9EJ'
        b'tEvZJL4qUNfC7UFLY3bX3BSjeSa7bscHvxL0TvAOvsT+1TX8LQLnK8tOm1l0faF8tMXy9aMZJmdtbT4puhDSpZz2DTIPu7xs+syeH5ckOlid0T+30mXF6tvlwwY/hm0q'
        b'Tf5xY/3ru/40M/bUOVvnqPYtB/+x6fWNIY6b3m+ZJTunXv7L64IdedFTK776SJP54zcrZ4YUPuJdKG6c9ZqjRd7+vwO2J69sSLJAp8agfTHqeuyS8+1oDgR14GNbSAoE'
        b'd20by4IEoMvmdCtmgQvqRFXGa/FlVLGuBN/aaFDCZ4y8uOg6anF5RFZskmxxbCIF7/jUCsDvtbiB0p2KuvGVWFyD2ub6Ahhh+MEcCK/OoHJAq/8arBO0OmHDhRg6rSaq'
        b'YnV2rkZr5xZIGBPzulnDxk6tLsPGbh9aOTatGbbyqOd9YOVcx6MHHhq31m99z85tcHLIgOvQ5NnDdnMGLeaMmFk2yuplTfNbecNmbuXh71lOalxdv7o1YNhy6l3LsK4Z'
        b'JPcxYD6weEA+YD3sGVa+4L65LQUMoQObhpxjhq1iB01iR8xtG2fVz2qYPWggHWdf9VThzL8A5OM2Y8ZNlM6NXpI52pQFgeUKYmPJZsxvMbQUmx8QujGnJL4EI5BBLJsG'
        b'wBLA1skomi3jh3AAWrXilkzusxQxT2uPUzl0G5992wsTKNDaZO6E97rwJk2wuOO3JsD6csN41CY/9e2EzMUZcVyRPEstLZAXF8NKq1krmlVUoFCXKjPH9rXpuUb6SqEx'
        b'K5utBFOoLlZkKrOViixxxgapR7G8NNeD5uU9yLEM1b88F6ksVJYq5fnSfOgfHL92AOJSamLXaXfdizWqHLLjMcFsCZ8yW0YJ9GkFKW4M8iR8TopKxedwRaL3UlxO3vUS'
        b'hc7jci9Qs4UcvRAzfJ5NILcsj/f04DCclUWokcFnw3EN+7aW8+gKOomror2INQrgMyJUtXQLN2YF3gNrSjH3TnwKD5BEKK7Zgg8nUqulxxihm7wo1MmhJnAFblm1hJx6'
        b'PxvvxrihJidqAkOCwATyI/gkV9GVa8Sm4X2W2TJ+m5u4THr65slWxgzNecsTcAW1n0kFYEHDQ6gJxidw40Y2IyNNemyD0eXFJJnigY/xcfl0F/atO8EARbLsOYxJej5H'
        b'uoXtqVdtDKH8TiHjl55fbDmLUX77++8ZNXk11RHn8i2L42Oxn83W/YGfXzOK/MS6suuLE3f4izYWt4YMvWqxf4/hWrvcm5a+f/J9OOWXpe93x3aeK9iU++OtN5fd/3jp'
        b'Vpdqi09rzb5ZORq7/OrM1SnHXNN9CtIC3t0mV66LWv/6pcH7lz64I2/dcS2778dP4k6uN0/95aUmf8vgj1LeOvH74Zr4gZEzu2ZfOfd69lIDvO7OP9Z/73LL78Tr1/86'
        b'6+fVZYPPaS4e+mx45eD9KY2xm2+v+PloEvjt6btKxKNOb5Ynerm+/cbc1O1fjLz856/+ll7tuG9u+c2Hf+ma7/rmFpVmavapLz69E/7Fr4fvpv7x1e+tvzjwVXpw0H39'
        b'81PenxcRcOTLWYWfdXkaH/7BVnw3/LmOjS/6cs+dzJ7ccvuroF/832x/7evKzH2d/4j5676XbJKmvjh7041rprwsr9e2MvYrfTtevCIzfsTuZB6a78mqtw+6wGp4mTu1'
        b'5CAnB1E9rvJKIKsWLWBEuArdxru4W2zwdtqiJBnt0LqKmasmpOvr8WX2nMABXFvsGRMfx2Gi8A2+MwcdtcGVj4iZky5B17LQdk8fGa70Ik8DdXEDcKuaJuNjVeiqpw/I'
        b'fwWR415wqERKQUys0WV+FC6f9IjEs/h6Grrw9Jk+mmCabUTO9HWjc3QYG6d5QljYASIfHe/FZYR6XJEnvk69TmH+FvZA34Ji3a4AOc/n/xyNPifjC64FuFY7FuLqarje'
        b'qDyQRp+oDF8HZeteP2E/ICAHXWKTZFfxbXzSM8E7Ojoen2NivXC1jMNYARv8pfgKPZWADvrhQ49ngM7IJmw69OEjNONVnO4BZMBjosPo7DZOvJqhg8sJW+xJuQ+MEcFQ'
        b'Wi25sF7dKpnh//wMoiGjzX/pjiGyntWIWLy0McuqWq1zrkHsocMHxRLGwqoxpD6kcU79nFY3dmOCOsHgYauQQZOQe6aWdVlNEe3T/2AaOMAdsbZtXFe/rmFDHf87HmMW'
        b'9IGFTWNMfUxD3F0LzyELz2EL7/LIT4wt3jNxuGviMmTi8paJ27s2jnX8EWv7xo31Gxs21/HvQ5Reenxb87Z29V2ngCGngHsWDiNSt7PiNvFJg3rDOpFuf6OkYfaIneNx'
        b'WbOsdX47b9jOqz78nqVNk3nD8lazhlTq7oMHzIcmhw7bzR60mD1u9+I9Cyk7nvaFPYuHLabXcUYmOde5N0geWjO2k2AtDK3vGjgMGTi8ZTDpffupcMMUWZdXz7ohj7l3'
        b'PRYMeSwY9oganhJ9QNwUMmzi+hWPcXD/birM9h3TwB/pXsQl00h/3u/9xQs4eiwcEI3yiUMaFVBf9G9gAT1VNAEXrB676HDBj2QrQwKQ4OFvxAUqYrsnOPyxcwjFxOHr'
        b'aR2+AFz+49e7MWOnEP533T7JDNRq3f5T4dI/8+/Sx/5d/F/59wm9iP+lf3/69XLmCfQRqBhcKdb696ec+5RNWve+Bdw4UXh8Zj3aRfy7D4ezEtzw2lz6YM5m3IZ2WuMr'
        b'E/07N8Y0EZw7PZ+826uIde1o/8IJrh3vwbUyrobsNKCz+DDepaa+F18m2QZ0yWitoRj3l65NEa01QttRPzqKbyrQRbQT1eFmtKcY1UB8VG+O9gtzyOODZWboahhq0Sxk'
        b'6MsLjqGb/5xcGOpZvQq35ufg21K0C9eFT8d7YWTl+tFoZwB5fZcZ6tHDh6iP7/bgQnz/IYEYcfGe8azj1w+xZrxK3+Iz0vRVX1ktZb9c4Q5zz8ICZl66wd2IAoY+JDsN'
        b'd+ImCa4Ge1xDQrDaJSKIQxZFUf9F93BwZbwXZxE+w2RuEa0Ck3ub4h3nQhvUD3jHDVeGMqE56KKMSztZvxwQT1QUGU6oI28a23OWISCe6V16oHKhaTwD9k2JEnyCbgvv'
        b'Gx9e6qANOoGvU3iTKZIJ6WkE3I8q03D/WKYH78BnOC64PZmeYtiCKt1j0EFyjEl7iAnXa9gHPIOC7N3IISbtCSa834x9UrEO95qox04wOaEBjpUYVbMnovo0+FjYNHKM'
        b'iT3DZITLtW9JuYJ2hynJMSbtGSZHfJVOsSQXpri+VkimKMnZwM57cyQwY7k3lzBj7bRtjEzAPvaA9uGz5JGTccN1X0KrTHG/tyG+Nn68DbiFTXd1QXzY+njE3FCOFbBw'
        b'D3uKYwe+mop2oNOPxzxPnz1WXIlrSgPx9nFjnsNRfmzdyVVXEwc0krFlye8SIKA+WnBFcvqigJM4xSLjhJ5f6sakHctulmVfsW8pdln04K3ih64/Mbd3XH+45nurHNlz'
        b'nZcKGv74+a3mK0V/if/y0+Mm30y3cCq0+u7EcN2pc6/iN6p4PT2BPuUvpkW/5Zhxw2+X7K/Vynlcs/Xn79hO+mSXKKko99T7nFDzwsaX1Gd3vGqyNEN8KEkpzamerzep'
        b'u+T9/clvveSxI+bc/j96v3RqxqKQhUf7Tedt9in7UwUn9JpRZ+r3K4L+vipo5bWMV32Wdp3OXH/2pyPMqe3Xbn97zfNtj1B1xN9mhh+0+tIyICJ8zcaFvsGfvf5Sdkvg'
        b'5HNZOUMvm7gNN6PmD/L+9rNq0owXDdR99q+utPz0u5yPM9ddrL/UHfDoiPNa2R/cI48sPvWDtekXlrN+lN4T1PQXMX+Wv2X7SegfbP/6+5+O562/8rDt04Lf7/z5k+FV'
        b'a9/xDLu/7uXkv5ktu1h3qdbT937HUdnLmx+l6H0csDjbcvLsoBev3/wkrHPDtwfeWGPz/F+/33biFctvs53qmS9e3jwr6B89Lt++azxkGNPhmi6TUJiH61CduacugMRn'
        b'3QnCbM5iT1P0FOHjc6wmQkzulnQRRZdF6kwKLkG4Dz25NzCdwjo/T28WW/Kd0TlUBeAS7Ucn2KMgLXi7PzqNr0zAlwlO7FbhrU3oNovp8A10gdjSCfjyGuplD5vcAFs5'
        b'gMvCxx048V6Ab1KMGuOC+3DvaokHxMjk9rEhOqF+Pr6Q5EtB4LT1+AJNh1wBMEhTImP5EHxgyiOioLleTvhY1Hhsum0WZd3CZFymkU7Ens4QyFn/j+HdfwEIrccBwvG4'
        b'cAwaGlJoqM7MTyPv6VUV6JDhCzpkaPC/jgwfcHnWRuULH4gYU7PysBEbx6bMJlWLGOChhWUTpz4ScJq5dePM+pkNoXfNJw+ZTybPdIS8be4/4uDc6tIUXRd5z8L2oT5j'
        b'6/rIgLF2HXQNHbaaPWgymyJO20bjeuO3TJyfgTcJwgyeeSWvN+958/6iIZOAOl5TQGtyD0/7dEzDmjqeFnW2hgybezyFLT9wkB6PaY5pibtn79TGaw0/KWqZM/6jg7TN'
        b'vDX5pG1L4rMbPDTUczE7oN/k2mD00BQg6EMXxsbhSPShbWP9NqkOktM8Lu3TWnMu2r49ZeZ7jlNa1c2pdQvedY5sEoy4+3QY3nVffMP2+YDnVXc4z4cMzYi9Ezk0Y3GT'
        b'sMXwax7jsoDzlR5jM/W7hZyJQHWhB+8lD/HCGXq6IzipRETSmH+XvHr2EZwxIWJxa4Husn8CbjUAyProv8lnNQtlTIckkKchwVbM3PDYGFdw02PHPPAhT9ThzmHc5gpm'
        b'oD3oKE2hpK/Bh2bidnISF9fH+vjwGDFu5KKbuL5AxktIWCDjLJBxExYoDW2OctW/gIgb74o+eEBvmXmYxe6cFaIOt7IF8/WdR4LK7d4aec5Ccui9fYar88unLj1RkfHl'
        b'ze/ub/ryl8gva+6156tCvzj285kbm96/EZe9buPBD4ND99x9YGu5532RzcHvXnjt056ovSdcVr99Rl8T1rJ5Xvnr0fUtC6Ntc75etDpyqt/oo1mVf5gblM1XvBP1Nzy/'
        b'9JMX0bFh049M/jyt/8t9ypg2/8P3DSdt1Lwqafzzp++gH+KaO0vDX3HOX/aK4rjniUcjf5l5c+mbK4fz+n/f9/3n6sXPDy/N+GFl5PGG2qpa+/s/fb5G9tnX+0zbl3cr'
        b'PD5cyBxszxvqX3luXpCwVGlTLp0hCsoSXcpy/PRl4a6XF0TcmRLxcrbBlL3p7jMM8MumNtE1KNd/j5XKYOXLvTYLaxbeeHXV2fg/t5RVfOzmduflpvkJQR817fnbxwav'
        b'ueXIg2foqV8+VfkG3tznKLmze3mEzwK9qxF/a8ywverQ4eOt7OafmnFoeVj3Cx6qoHfqji6P7d4ZtlY++2pYyq1FP9+P97hm+8ePrVLijS/vf3cwtvAlI/+dXlfNr6s8'
        b'v5GHvLSpp/G9vT9/zHFwM/7QbwN/4cuZ0xOOJf3c4LExRhFaHfDxiiOub37E3WDaeOfVvC+72z+9cPj+qT0bV2HNe8/Hv4cK3vvdH61yFr/6/R9uJd/Z6jKqKriUW2Sd'
        b'4fTmi93ZHT+H274ma1ic+Pa9g+f2/xBwZt1bog9NTbdvWlw747Xm0szOtudffuvroq7EQwaZ7/Y+aAxwTDD++F3HRetMvjM//f0UvajarjqNv9TzI6PQdsubb6S+3jmY'
        b'F3B/7o2w0Li/fp+Qo77BrxXP6qtBb3/Ym7L6xZ+XvTF1fWXO+hrrrj9N/vrXusLuDxqD/N1cj2xKOeVfe1BwwdzOMdW2/LP1mZ0Fo5VbVzp9tu25JNs7nu/LTh9/5bvd'
        b'B+59tTVGHRL+cPFm96a7x5dti8vNMw7vSw1O+rXjzpyZBTWtDhHLzn918CO16fHYmSd//W72PzKOBn3mVCn6249vOqR9PmNjRMOGb08sGlqRLfvwi18///ydM3+rzqj6'
        b'5NMf9A+lCiXYWGb8iH03K947G1eBL+a449vTGVCeOm/2mcnD0YABJ27w44pA6sc7xDQNsiWA+5QbnYz2az0pqse7qLufthV1ea6dOz4ZXY/72E5uQ8xysgRdjCUpo0ro'
        b'LV7ASFA1FyKm7R40WxOK9vm7oxuxcR4+LAVJPhefQmdwG6Ug4s5FVag2kQAR3GIcjapRLcROQp4juoEPUAoiQ3weV6G9qAFX4lpyiI8/g4N68fnnKF6xw8fQEaDRI9Tt'
        b'foy5emUJxR2zlzs/I12VhW9qj0QV4N3sWdR6XInqHjcdSwptTyV5oaxS2ipuNheaQDR2+OkTT3xuKe6hIGKzK7oIg+6SekXjakA4wlSuK77K4i90ZnPabAPPGHLqKi6B'
        b'MKyXi4+isnS6EYQuZglzpsWS53KgAYVnEnSBizunQyjp9l/gCNF/ePm/AzFuE0DMPO1P2VM/LKIRpaVRTJOm2qIDM2bg9H4laMaLMbR8wNfTt75nbFbnX7Wuyblqc7O6'
        b'1b9V3hbUsrF9Ucu2Xrce1YBzr2ZgUe/6fp/fRdwxw1HD/nHv2dg1+TfJm4Na9Ftjhmx8eqyHbKYPhiYMWScMLk4eTFk6tHjZsPUycojErKFw0IQ+yrqc80DMmFnUhdVb'
        b'ls9/IGQsrRsX1i9sTKxPbJ1/dmHbwrOJbYkXo4bdZg9bzCnXHwGcRarj6uNabdsXDFsElOvTm8r1P7C2LTf4AD6JHxgwtlNGbCaP/X1oqm8rLjf8ykZoJy43emDBmNmO'
        b'mNqMmNo/1OOTigdG8RxL8YiByaDZ5Ac88vkDA5M63wcC8hHIG5pCQY8WRGxBnxbEbEFCCwZQGDRzf2BIS0a05PbAmJZMtHWmtGTG3mZOCxa0yvuBJS1Z0dLkB9a0ZMM2'
        b'tKUFO7ZgTwsO2naOtDRJW3KiJSnb0JkWXNhxPHSlJTe2ajItTKFVsgdTacldOw4ZLXloh+9JS17akjct+Wjv86UlP23dNFryZzsIoIVAthBEC8HadiG0NF074hm0NJNt'
        b'OIsWQtnCbFqYox3VXFqax9ESCePQ8nyOlkw4W47Qlr+KZMsLONqhLmTLUbpyNFuO0d0fy5bjOGzf8WwxQVtMZItJ2uIitrhYW1zCFpO1xRS2uFRbXMYWl2uLK9jiSm3x'
        b'Oba4Sjeu1Ww5VVudxhbTdcOUs+UMXTmTLWfpblew5WwdG3LYci5bnvZAyZbztOTXsMV8HVcL2HKhtrqILRZriyVsUaUtqtliqa5vDVteq61exxbXa4sb2OJG3cg3seXN'
        b'2uotbHErR7vc29jyPK62eRiXXW+udqThbDlCVx/JlhdwdevNlqO05YfRbDmGy5i7jJhNHjGT0auz7u/kr1bQFmBMVnEZe7fjvs2+79h5VsSUh4P5uGvjOWTj+Y6Ndz0f'
        b'wi4bx+OGzYat8mEbz/2ChzzG1ucDC58eyyGL4PLIEUen4yubV7YLhh19yqPrMqsSIASz9wJrIDa5p29Sl9mkbg/vyRrSn/Udd5q+39cMuQAKDyUXkwd8KJLVo42bXFvV'
        b'Pfwh/aDvuDb6NqRBsLYVFEG3IIjMq88bdE4etkopl3ygb0w6WNLq2h7RY9mjGVj6fOSdyYOeSUP6i77jyoAAI2OpLOZoyUCZiKl2ZEP6dt9yLfStSaW9tgUUQfcfN/iG'
        b'a6jvMr4BFMH4sMNdMqTv/A1XpB9I6ly0DaAIFu5xg++4dvrO4xtAEYzB4y6+4zrox3AeMuQ6vidSBtMwvqGv/hLOI4Zcxzck5YegEfrWdSoSZTdurt/cGt2+bdh67lui'
        b'efdElnUZjTn1OY359fmtM9qVw1bT3xbN+P7BEkOOfjTnnpnTKYNB7wXD0oXDZlGDBlE/0hcU7AtziDdlXjc1j3fTPp5hMcoF3/lbosL/wqWTDEr6uFdlTHDh1HHTC32n'
        b'F3nElByQkHE4Jt9BPGnyLbn81qDyhNCf6ZPM5ik/3WTPVW8lkeUcF8Vrs8VonsULD698+bnLwSln9lVGVX6/feHgO5IRxc/L0Dsu+YUfbeGt4DsP/3TG5pOtUYe9frC4'
        b'Zbb6wN59OwymVN346cIfV5WUDrSl+pz8peDSeq8v57ybf2fr5Vc4p0+caVO8vsd71rc2jseOmeegS9XvvJxz8JsOa+V9c48DFpenp8r0KIAV5rnS/6knkUDTWHQQXdYD'
        b'vNbHxe0AICsoQl2PygxiE71xL2mW6M1l0C500BTf4KG29a6UyOIQfYKCyYvr98VrIbAZakOneJMCUCNF+qjFICA2Ot4jXo8R8nH/Zq4oG5+iiSzcIObgKt8V6JiQ4Sxh'
        b'8MlAfJxW0FfItXrGFNkLGE4sg5tkqIeFmOdR/wzPsWfDfYWMcS7ejbp5edK5ssn/Bjr+/58E+4+FcjLFmc/Gls8GmmTHCZRljw5oko2an8qYr+0YgfmIocVdw0lDhpOO'
        b'rB82dC9bMMIX743bHjdo6nxq+lt8r3f5hvSv+Xf8EqFg5ncMuX5Drw+yDRkDi7LEcQeNnEd5+YrCUT55CnRUQI+zj/LzlerSUT451DjKLyqGap66VDUqyNhQqlCP8jOK'
        b'ivJHecrC0lFBNgBi+KWSF+bA3crCYk3pKC8zVzXKK1JljQqzlfmlCigUyItHeRuVxaMCuTpTqRzl5SrWQxMgz1NrCkaFanpIcVSsVCsL1aXywkzFqJA+O5tJH0lXFJeq'
        b'R00LirJmhKSxD8VlKXOUpaMSda4yuzRNQd6VMWqoKczMlSsLFVlpivWZo/ppaWpFKXmZyqhQU6hRK7IeWx41CZfS//WPVMpajD26C/nfm9SJcPn1119/AaNhyuFoeMRq'
        b'TLx+Ta+/xYYQY/k7A2GYA/M7B0nYVN6PIt1LfUZN0tK0n7WRx4922RP/OzVpYVGpdlsyQSYib5PJKsqEOcMHeX6+VoKIQJETk/C9GNirKlWTQ6qjwvyiTHm+etRg/DtH'
        b'VGd1osEKCSuQoex/1zZHdQGK5PStOg4uD3gcDuchzJEPzlpiWKb3FX+bkGPxIMKI0Te9K7IfEtk3xdwVTR0STR30mvO7Kdh92CtmRGRyT2w1aB0wLA4c5AfeY0zqbN5m'
        b'7Ghv/x8fJNtS'
    ))))
