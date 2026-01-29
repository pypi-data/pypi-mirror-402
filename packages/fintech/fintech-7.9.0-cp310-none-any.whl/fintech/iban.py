
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
        b'eJzNfAlYVEfW9u3bt5ul2URFUNR2SaTZREXcF0QJOwi4L9BAA63YQC+4L4iyL8riAiIqLoAiIoi4IDN1skwmmZlkMplEJjNJnMm+zCSTmWQyWf5TdbvZJPky3/99z//r'
        b'Q3PpunWq6tSp97znVN37Z27YPyn+LMcfw2L8SOE2cmncRkmKJIU/wm3kNdJzQor0vETvnCJoZHlcDmcYt4nXyFNkeZLDEo2Vhs+TSLgUeRxnk6ay+rrbNnRFYJRyR2aK'
        b'KUOjzExVGtM1ypjdxvRMnTJYqzNqktOVWerk7eo0ja+tbXy61mC5N0WTqtVpDMpUky7ZqM3UGZTGTGVyuiZ5u5KKNCjVuhTlitAg8SLbpNHv1urSlElq3XZlitqotk3V'
        b'Z+5gzcUFRShTtHpNsjFTv9tbmWVKytAa0jUpyqTdrPwpjX6HWqcM0uiMenWGcgVK8LVNnjRII1PwZzL+KKhWsvCjgCuQFPAF0gKhQFYgL7AqsC6wKbAtUBTYFdgXOBQ4'
        b'FjgVjCpwLhhdMKZgbIFLwbgC1wK3gvEFEwrcCyYWTEqdzLRpvX9yIZfH7Vfusdk3OY9bx+1T5nES7sDkA8q4Qdc7OZt0lTQqefAU8fgzCn9G0w4JbJriOJVVVIY1Xh/f'
        b'K+XOpNG+JmZcO+jDmabj5QG4NA9KoCg6YvUWchkKoSxaBWWha2J85NyMVQL0QsX8ZMkwK3C2NLH2J4451dk8MkkhjyPjcWQSNjKejUZygI8bdD3SyGzNP0NHdl8cWXCW'
        b'nLPjOCc/+dyVW9e6c+xLV1cpR2/0W/svz1mbbLgMK/zj5942nBN+5xe8Rxa5lt0HU2Uc/lb6ye3dns0K5pq5DNrQH7LdhC+cOadC27dnfM53zdq/dSeXYYMFkxSnJTes'
        b'8H638jlv6U3y2+LXe+I/d6x2lHj8jfve9mPX56NruD7O5Evl58fBfVRxyczVHh5QPDPEh9wn+VBMmuM9wiKhwts31CcsUsLpHG2WLAowudAqrVCwLzzUe054qIBjkJA6'
        b'0g0XTNTcyAXSNcsAXTv1xmyTgZSQQlKIE7IZbrhJ50A11KtkpvFURLf0Kctt5NZuPc/ZkF5+mh+5Z5pAjSQDzliKoWBXtoSzgaP8DHIKulj5BJ+l/cWNUAXtHN5QxHtB'
        b'4wyTK+3G9anhlhvmus4RUHoX77J/rsmdap7U7TYXwq1ZcBVu0NrH+ZmkZqJqpmkc7d5N6CG1Bju0LJJHLsApjpwg9UEmOr05B6DboJdxXHYGlHCkEG44s+/XyuYa9DiJ'
        b'qlFQxpFiqCfVprFUVkXSDGwOr1bAHTjGkdJYaGMlY8gRaDKQcjQDKHGF8xypn+oq1jkHJzZgCS6YJRFwgSNnodbJNAZLpkKVoyEbW4dTOPIKbMhzEasyaVGyAdrlWNBL'
        b'GqCGI8eCSSkr2Qt3yFWDCevshwdwnCMl86GKdXnGap3BHquQIyQXGjhyekocq7EkJtIAHdgtcoeHkygKTpNjrHlyaMkyAymlV1cT4QxHaue7s4JF9qEGBXYX8lCh51AU'
        b'VFmxNgC152XYietyzyY4wZHyjY6sAhyDTnLe4IiXM51ojVMOo1nBhnjSCh322LoOyqCVIw0ZU5mk5Cy4rqCKfyoAruL9zhYF34SLHqQEJ0viSG5Z4+STzm1iyenNiwxw'
        b'k85iMdRAJUcq3CawRsJ3pEGHCTuVOJ+qt5qUQK3YrbYEuKSAG9jM9g3QhprPWshat5YuNuzEAZLDJI9KKo5fJi6Gu1CgMcBtOomVcjjNkeOu0MuqRCyaYXDEKhJykTZS'
        b'CyWRrFvk4t650GGNJXvIHbjIkTodFIh2dxJaSB2WYfMzSA1cwfbXkU5WRo6TStILHUY6+bfcaEsVcGiOONB7pGsCdNjhXE7eSmvVwzWVWKubnMChdzBTPgOnoQlFekaz'
        b'shjSthc6oJ1ONIqCRrTyJKhgw0on5/TQYYO1eFIN1zlyHm0wnxUFkmZoxjIZNYdZVEcXwuGUWeGJ27FESk3KBdcVaSSl25gunPZsQIVT82y0p6Z2nDMxfSviUBX22Azc'
        b'0NMKF8id+aKoVvko7FwHLWpbBS2oJaeJ4pCuLnOjJbjWUCMnqYmcNcIVc7eP5+DsYaVYXAXXqSJ6yG3RdE+M8ldYY4k/tONyJJd2QR6rs+gAaVHATRQHl6EcbtFOHJaI'
        b'nTg7Bo4pcuhIby6gDZ2OI4eZtMW+jgroEqi0Swg/pN6P3GK906+F+1hCR9qEtt+B9kt6oIiVOe5jZXQCqb6xpfOIvfmsqRU499UGI52mEpymQo7k23uaqCsbn/GUgvoU'
        b'0sZTZZ/iFzJh9lAHJQpbunx74Qzc4chlUk9OMXjdTurjSUkAHCO3SKkM8jdyUrggiSY3oxh84vT1wBlSkgPVpIwUy6BOxgnpEpK7RW6aiOUhMTPMhbOpiK3jUQhCaBk/'
        b'jtyNV0lN1IcvgisqHaJfCU52JpdpnMS+TXOB/Kfgfjh2N4lLIjW72OSTInITrvgrwuXUMabAddIuqrfIx8iGDAXT2IihC0pMT9KSFtReLSJ7IbkaQJpl6khSBhe3BZHG'
        b'vcEbIzl/g4zUxK1kMxGtgXYDXRSkahMUcaQA8ieZVFRGJVRLLSKuQ40jXEcPRP/yJ1ehRuDcoUywWYBYSMXMz5lsgE7al0NINBCmy9eYTB5Y4AO9AaIU0kWaoCYDjkN1'
        b'CLneL4X0CFJydLwZDXyhiPmNKXBYdBu95IppBhbJydFIS29aocZ3V39nromdqRTkBvKAiSGlUOCBOEsBtRHN9Syu3eyprDtwG5pxNFUh5BoqBmpSyA2zoNm0dyjIRwrd'
        b'qTFM8XZ73A16ajqXyFEowEW5dT/rC1QFTu7XDFMuub9NoYQS0rR2NLkwkQtTWimWxzDFqMjtXczfZaFemMMrWmWaSTtZNQcuDtKvuRukDcrorxbsDPWanI9elk2OxbIZ'
        b'n7AcjjEvuRW1SN0kOUPOiTykN219/6jKpElin0jjHtKFhnBxGynBeQ+BbjncgktZorK7BNKI+I6X4xCdynHlkHv7TFPxbysoWTegI3G+hFgOMXIsNEvhRmIOW1rG1fEG'
        b'W1SyYSOdqxprKDTNx68T0nDyBqa8zDxlcE/bP2dNkVT2tUh5UiSXTdqsyZ0AuCT2qiJ1h4EUU39wA/83UNi9N52NkVwZi1hQRTsjditWA4VSUglFUEPyU3Gx1nKzoEFG'
        b'ytF2zzNpLki26kT6gC6LsgechQaTJ22olLRhtwZMCklbq8U0W0TTrJLC/Z1z2TzaTSKXDA7Uoiq3QC1aJnRqmEUpyJ31g6bRZkb/IJtFwywQrHD1FTApStLkI1IWkreJ'
        b'UZZUL5MPFoyNTRoQ0q+xwQvFf69sgQyJQQdcY7Ywehl0iRwHjsoYyVlKzphmYUkGwnBd/+IfsKyrTLC/aOezoUKGNtJNzoXuZV3bQZomMWpEru5izIjk82yA5NBM9NKD'
        b'ljBqsn8exSG2Ctaxo0VMuhyy2UykynSMRyE6irNX6D/6sU6hwGvicOkqJo3JnA8CqsG4hAlzIKXbURj1VC3Z1GNX26M3pytTBR2khZGyeBPjZGGJJm/mcexxAZlbaaGt'
        b'oK/cTc2D5CvJhbWjIVfHRUKP1ez9K0SoaIfbzozFQX4kI3G4YE6yKSFVy5YOhVBcUZC30SNAHLaBNFijs6mEUqgfw4Rt10OZyPyCkZtS5ofGWyqu9tpo0j8nVx9b7XT0'
        b'kKvG0Z+QGcLQ1Y8TOV4NqTYwV72XFEE9xcOLYr/XwE1ySqSMF1AwpYw50C7q4AwcW9Rv1/3YH6SEKopPXDSctSJ3SZsv5G4RdVAHF0Yzdga5roycoScvE7t9jzQtGMCV'
        b'IZ0XjUGYvYnzJfdk2+AEoi81JA+7DYadODN+uDLRAMqQtl9jhrRzMlwzy8Kp8UdFD/UnM6RwD9G5g3VqNakiZ0ViSDpcGTFMRr0wDG88QB4MwNOUcMs6aaViJkCXFDH/'
        b'PClickJGkRIUQ4lBh5JS7mqkFT3iuM96YpxEKeYKnEdGMc+SGhFOW2LR5w5dkM3DF2S2TKPAmOqotzhb95KgxeBIXeA15E0XKXA1wBnRYVSSQ5MGIVcVRhJMlMXpSKXQ'
        b'ppjLTHsaNG0X6e36dYzdxo43edHetmDX71n61MZmoXX4QmwUrFaY4xZS5zNTpMKxOKGUCo9FXzGXY/1rDR5hcBcs0CWQm3aRgStJ65OcHhDWjy0gjUxjy+DBBjOFLvFn'
        b'FJqUk3yRVh5CCQWITpQEzIuhFnnCCyeM0hFUZQWaVL/HTDtoXk1BShnnT87JkOQ1ThTxo5lUBSHfxmmfEgmXqG02+DJTRPuq0w81xQGvaUbsOQg282ag3TWtZdJsyI0I'
        b'kdeTw76M2G/FRUIXt3w31mQdigzrl9fSL0+KGrDfNleyWmY1f0qk6JguQP4aMRIId2VxAI6+jgmLCIWL4cyhoYBBy24rHBFZF/reWFJmNQUJd43JDWukkvuUgzPaTM7B'
        b'UTrSWpzdS8xc1JlRg3w53FAmWfgb9eJzyC10cVLSyro1ZkkSdDhQ9l2IZBgJbiNKKzNznU3Ygf51QjoGrK5FXCntaHZuCtF8uxeNRVCl/oTcxoHcREIMrSvE+WvcoRvC'
        b'VMx8wJ0cxion6bItBTFMgK7ZwdCRjVLWbaWrrcIHKpm7xTVTT64McgCBq4cuAVIghbtoqY1sFUwVqIaycea2plDgOzZpBWMmCdC0dzgz4SkzuZ0FNbjuR20WR3PEIcAc'
        b'm6EzvM5iM1K8kBnFU1LEUhabxUwTQ7Mqs3mTJlKxVgzN0A7ustjMNEZcTaVwdpo5Njs3l8Vmy8OYljcpsNMDSr4ZZAGJ66KOb6CO0ZkeFsXkJqwRA7lgtCcayM1CpkIH'
        b'PH7BMizATu3S0rVTSUqcTE9QNA3TmYED58w3QBROOgdwo5P0cqz3fnCH3EMZ1IXfwCWH7KJKLzP5YZHJhDHRY1TT37L4mTXMglqZlEerbiaXRD3tp/Ey3KKr5/5YunpO'
        b'c3uZOCTlh7SPGYS/heuJ4tbJYtF7HIMicpGJSyZFDhirUvsqfJLq/Zwb6WXIBo1e5O5Qh0Wxod9hxURYYYB9eQE5vYsNNAxDtQIx7F1gYlEvtlvFQCJkiXYoRPSzKIvK'
        b'5pBe2QRyDtfuKbgqQg56cIyI7VFvYdY0GG1ciVH8bEY4J2IkNVgen4xt55k76IT96w4YRQrnSkjdctsoKN3O0mcepBYt3Rx8NyNTpNG3DWlma2nHZO0gazkjH4bgKinc'
        b'XofxHTViL2ibYInUz5E7LFKfhB6FsaljM5kfGZnjiWyqGnmqj0mWtVsmWvd9a3sM7ul05iM9aaUOqn0LAxxyjdwYP9Atn1VDHN0EuCNFutHLM3WtWYpxM8sRTEAjozkC'
        b'cnmy6KFueUPeYKKIxLx3eMzYKzjAEa24SBvgCpQprGmP6jFkwID+ImmOZdEnupNeFNHfpackFrS4JnbpuhTj4Gskl6FOIM5zL8tOwIUxLDvB24uocwIqYx8jcYNMy9sK'
        b'O3Zs3sbpYo+6XMhVhVFg85ZLQbkKL8wJpAfQRBrFTIcVGg9NdEDnFqaT/RHkPsslWKG/oqkErFXHQiSbRaRUkYMCR42HZoyREqNEkz/uPkAHqds5vmfYyqZwiLEv0kc6'
        b'd/pQKkbO0li1NH13ElneIcb2g+CWMMxGvcaYx0k6NkIZHNkGjRs5/XaMshCqLrAer99N7omZmcNalplBID/C6GNQFvZr8Np2RN9jnkKZsznIuiYj5+SkTLSr+gmkSMzm'
        b'wFVEW5rOiTzA+maH/qdmcIg1QBwHgtzb0IO8t0pmhFw3cRZ6BSgWk0DkxGKWA0Joa2aNCXJywpwDOopBDs0BTYU2ZgT6qVCjcKA20DkF7lMw757N4EpObniMhH7NQ9Dv'
        b'vIzcckAiciKAIYmVFzU/ywQNpRukeisFT1n2XEmMtVUAyUNNMKOtdtw7dLS969ikXpMl4VREcrPHyUipEmmYaJsYjRYMjgmOB/UbgZjUIDcFAbodxTV6JNFl0Cj8tvaP'
        b'o1VcWcWCtR85L/LNBiTX3QOrZ1X0sGW4SAo9TrNEkKvERXLscSgZBudQJfNF/3wGY2KVNZumUbgeUOHUIx7FGXqADBXOoBExmzgVDYcV0E5n4/BiuiLPz0VeStERuTm6'
        b'YiyjFYuXQTdNc9bh9DL6cDzDTWGDPsIXDQnn8AopiWLrSAIdGxUmNLF1XtRcT+73Y1+Ta1McWHbPZitL7h1MYNY9M1ClMFBOdB1Xyy1K1eqgSXTA3dCSiGyfwuC4ULQ8'
        b'cjFunskfS2R+JBcLqkihOa9HWs2MkBSSBoFlAwXSEU9K1nDrtshRxeeiVALLF6K7xUIoiQiDxnlQKuWk8ABdwmZyV2zzbPymcFLiA8URco7fKpmJbrqbVQyMJxdIw5xw'
        b'KJ8JZV4q0iJwdk7SsalwSlwIh6FroVeUD8rvDBE4YbmEtKyFkuBkuvNl+SenKMOZ985WcmzLTlYgKZAX8Gy7Tlpgk2pj3qATCoU8br9sj80+gW3QydimnHBAFjfoWtyg'
        b'e3shzoKtctC/ILoNSzde2VasMjVTr8xRZ2hTtMbdvrZD7lyYpdardyi1SWrdQmV8ukasYMxUJmnEzVxNiu9IFZK0yQuVoanKNG2ORuct1jJv+CrV+v66Sq2ObuEOkUD/'
        b'JWfqjJpdRrrhrFEnpysz8Sb9iA0lZ5p0Rv3uwY0ZLd3UGv6Ddox079oszVcZaTIY6RipiuKifebMCghQBkbEhAQqZ48gJEUzYt8Mmiw165gnvfJUalDJJrVRw7bCExPj'
        b'9SZNYuKQ/j4u29x/UeNsksxjUcZpdWkZGuUqkz5TGaPevUOjMxqUgXqNelhf9BqjSa8zLOxvUZmp659ub/w2WJ1hYF9TJe/UGoYNZsj2LqI13YQdtr3rFBXMtmh3LXHl'
        b'/Oiu7VIvz3PLnDmTE345OYHc3OpPSvByA7dBN5nd+fO1Cg5Rwtovdb0vEfaLO8GPjI6cO8e5+gX/esb4uHhOXHIlJC/MCQ6LGRKaHSHn56kcGWbovaExymWgZHMQ+zpq'
        b'vmfkKLbTxvbZyKFgMeyrzER8P7uMbbWxjTaSh7EO2yatwpAZke+euN/GNtvQJ3WLSHZ19XRyfjnbcWP7baHktAiNd6HCGf1tgyKLtoWB5ElyPJ31elQcxlENcEGRTUuQ'
        b'2NaRRmsmzYa0OZCWbHGbju7RZWLYwNC0GLqgEyP6Sugw0CwWsv5KPYgMHsrCIH96hriHx/bv5KSbxZ+kB06hF2mCXHEfj+3iYeNHGO6Ek6a55Dj2g23ksW08qKShEFMB'
        b'3EXnf0DBNIXAfvZgpghWjaRsFeQj9+lgY66j6a+eeawjW0kbuXjgCcNOisknadrgKlwz557IYaS2Z7PE/BNNPk2HoyqpKPI4eoHT+yF/oBApzBkmct9SZDaNBwc1Bg+W'
        b'iT28ZA8XoWb1QGsYJrCpvEyujE8i9WKKjuXnUsg1lUhrp5Bqb2ShrYMKF29i1RaTi1C4CErFjVu2a0sOzWS2NzrGSjyakPOnOZCwh2OGtJrcOkjKlszxo6mrKi5p+mjt'
        b'jaVxMsO7WFbU9/zcX7fr+Fl28reWla+ufrt8+yLTcu93JOv/bVfqbbfmUtgnxz5xCvpUuBT29HKvFze90aP9JH7Nia86Wt8k7S4uk/wu/KPdRlfSFnyZjPvyWbeHml9+'
        b'J/t3/sv3XqnK61n3+hujbJZMdFpXtCds/VtvPfrlwsPdo2Y43Y358psZeY5jvgm5/X3rrV3ho17YctLtw4DDP1N/HqR4I8Tj7NGPZ3/795+pF979asoYz1/tvl327c1d'
        b'rQ/iGppvPzO5ZN6HDR/u/PC5RzV3Xnr/riH02qO5gds+SQj/Va1DePSpTabJr7csmP3C9A9uvX3+kk/qm73rbkbKpQEqmZEqTr7PzUtPGnw8Qnx4JGG1vA8GDKeMdIvM'
        b'TwUV5E6WIhxKVZEmH08onslzY0mBYA233I306EogNGwkJTtJqTXcNJJyXHJ21nADOtGtjyM3pbigr4UYqSnDafJgC5RApQcUefr4SrClw/ycqdDJGnLyIa3bSbWXb6i3'
        b'p8oXKryhCLFCKWyFG6RLJevjPVTUgLhhHyqbkb794Q96NOfrsYtT9Zl7NDplqnjGyZc6wKV9tgyOE+gf9DZDBIXEg06+goSXjJHYSeQS/vsxvCARJLb4Y4ff4bXUDj+t'
        b'8RtricDz39lK8TfeZ8tbftM7BYk7ftL9ILEHKnmfQJvpk6In7bMy+6U+gTqSPquEBL1Jl5DQp0hISM7QqHWmrIQElfzHB6YS9JRb6OmZGT21eD09YaSnnIM120AHROea'
        b'y3V/JOd5HAz9FCTy7+iniZ6fSrA9iAQnJBLKFzvhRFYgS0KKNBaOSKGbnAzGtU6PlWxEZnY8HIugJArKo6HNPlTGOWRJ58P5ieKZl0I4PHXOzvCIKJEtSTjFRh6uK+CW'
        b'uD/dZo241bKkn2TtJJeSpcOckJXFCS3k+o82CamCmR1JC6XIjgRkR1LGjgTGiKQHhLhB12Z2tPoxdoQ+lDrpfnpED6KpLcfM2AE16vIZn1Ens6lR6kw7kihDGSKI8iXP'
        b'7UgxMpndeFpOylFiotdkm7R60bNnafRIwXaIFMRyXm6oE462+GbsiGcstqjdoVml12fqPZkwNZakDGt9pSZLr0nGkaR4K01Y0SJYmczGx6zYQ2U50zfQTWWGNkmvRhI0'
        b'RNo6bUYGpSB6zY7MHJFQ5Wj0Bipv/sickSqK6knkjcO1NyJhMmtTrDFctSM1QVlmcIY6TakVR5GcqddrDFmZuhR6lpCSTUN6pikjRew55UHYdbVBuVOTkfFDNGmVlup6'
        b'gJUhOVYrZ/sYTVnItszci00Xas6D3uFNG1L9CGmSmm12KGmyiTLp8PoAaSGn7aEw0JYc8rMT4BBpg2urIXdZKKnTaUnTdGcMZPJIL5xcEAWNE0k1qcywghNB0KlBptAi'
        b't4EHe7f5YJDYijhY7g5HjOHkZCBpJjUIrN2kM5gUwW0pTx6MgzwfCfN1r/qLJ+6OLTN6d+6exJmUrB9d5C5GTTdlUKHywUoV9LBhaKSEm7BM2B9jEhne4SzRTR57Qh9R'
        b'Givh4rVPPLVVatiIRa1dG+yfb7c/pHSSvfT9Xw89bf/Gz3LTIzN8+9ar3ln98G0/P3mG5zsvbO9Te7uvOOWqa/b40O/W3z64t3DPjfnz5y0on18//g+/e2mL51X/3QFX'
        b'XlC5/br0na8li14dveXKeJWVkRIkHbTrvKK9oViKMeBVTlgjQQpxm3QYvUWC0QHNhlAfj7DIKHQNiD4Vimg4m4b3o0spDbfigqDWahW0Qb6RjpfcidmKBYhiXnj3lT3R'
        b'IrDJuXErBc8UOGSk50OckGgcDo/2CfVWqXhOQTp5cgny4T6558bKk+HYfijZkDCgMAnnuFq6Zha5yxqBB/NkpGRu8EgqJQXQZaSoSi5tmBQ+HTp8wyK9Q0mZBVbHk05B'
        b'B2XeKunjSP5DjovBeZ9i0ApnfsqV+Sl5CgL599a8HfoiucSZeSVBonfs9zmyPmvLou2zMi8/0WnY0Q97eg8/qB9SPT3poqckX7yNORMq73cDzsS5dQRnQvP/5BrcTw1/'
        b'fNDkGqnHgTejN1hCVZi3csuwYB5Z2zEx6XqE3CSl5Jy3dEu4PynPxqLLpMeWS4JKe6h3hwIxgjg9mdQrMlNzHJBxY0QAV0nuMka5FXS/VYETWpSTTcsKkRPiqjnJKGsi'
        b'aVptgC5HaHCdLXA8VEpc4Bg0icS0gzSRdoNf8GzUnCSTI7dt9oqBRCHy8cMK0uWSkyNHiUc5qEVacwldo3iWixyFznAfZOgW5xYyTUw8lO0hPaROMTyBYPBmewoTd0KX'
        b'l1ssOkwJx5NySZBg/5hL7I/LVlCXKGVOUTzpyxdYp1r3u0bhJ7nGNHSN7/9Q4oBB63+dNmD4TLGc3v5fJw1+IJanlf+fh/LJGaxbBo3x8eB9WAepXjKTk03oinTJj3fU'
        b'Er6viglUBiF701NXtfInn29/TB477z6ob2o6KSZ2WN8zLije0xt/rVxJfwVFx87C39g9zxWzV7CCoCBP78ckDhqTOsOQOWISgg6S6TlLTD2g1BTqNXdnDVMg/bcmi9bN'
        b'mec733cXkz4iK9qpHkqLKGmhTTwmLjPrcYL0P5vmkHAjpTkczGmOIhtzmkMXHtksSRaTF1vGOnM02vGLenWjYXk2J573uwt3UtfOsSQ/MPwUT+oitOdYzoRPjuRHS2wm'
        b'QwsTkzTFnANJ3b8rbv8mzhzT0nNwyLjb4dgc/GsWNwuhrkA8VnwLyrGkCB7MwY7O5mZPX8IE3Z7hxKELmu8XkBdV4TieCmJp1mpPOEsuBJvFQLV4to3cQyQtIMXL2R5V'
        b'DBdDin1FMSm2YqLGZVHamKBp6PBLXr0iM9BjWA9XBvpE3bMlMXZLnu/p+Uf7HdOop7L/Pvkb7uXANxamONk63L504f34I1+N+6Shdukv9FsXFOV375aZwuz3Z/18/9ur'
        b'374z9QvD0ZfcHJteO6eF7G/z8+3eufuaZvebLfmxb3iqbv3ufFb2ax8Vn6hZ6PmlNPxr3duH/xwYuln+2TRd/fQTC+1Uzh/VdAbv9l88Z3HbqOi852bN2zHl7RdOt3+w'
        b'duknkV9X1HhlLqqZO4M8WvTnbVFln732r08ct86ZN/355Sq5kT4aQqrC4fyQoJUcDRfjVl9oZ0Fv2jI44yWGvFugU4x6G9awIg9Snw4l6LmgnJ5z2yX35x0mZbMw1QVy'
        b'7cOhLJyFqOjLmmiY6ugnTUPnUctIwXRyKAnjYXMwDO12DjbyBNKOZKNH6k5adrJYmDRCJRylT3ywSHge6WHBsP+TKonofK3/o4hWJAY2YvyKsMxowWxGC7iDgsBL7AQx'
        b'fHWm4auT0+cYwuLVVHTWruYfO6QLNKDVjx4gDAMhZZ8UIXIQT/ivolHpoGh0TD93oKI/H+AO4ytG4A5UyaR5trM5EiUYYVJfOgoKglOkpHSpTCVhiTF06yXIpUsiwjyC'
        b'BzL5IVD+2GMy/bEkPfKIzhKdZ6q0/0EYyU96EAbd5dcfDwGUWBGQfiAuEfFTI/o5Fmj4Mk+ZmpmRkbkT7xoKTsyZaWlQqtcoDaasrEw9BnYLlStXeSsD472VQSHDPPD/'
        b'IOSOHJE+lhYWHsNLqyj26BJpme5CKbgXrjYoilgNN4x66MR4pVLKTSRNwlQ/uGGi2x1qqE2HdtJCH8JZF9KfQAj1WRviTeuWhkZAceiaECiZGRvSz5Pi6SNQVuSePbk/'
        b'n9w3UWCDKigj15mYLFxma2kNXJISUrnKlpyNIuUHbLGVo1wCOcQnWKlJLhxnYLfT6MwdEaIp+VucO9eO0+pifssbdlIz8bs994V2e8AI7WcHi492LOd2S19z+/m0i5Gq'
        b'FK4ua1WADZ9ut/eVEJvNo77/8lrTPsNEu0t/HHf1i29eWu43vRK6s90ii+dff39C47TkaF+roC2vNe+/8sveu7W69brfT2/898TrslXLKj/ruPOHh2fqXvi7wjEibv3k'
        b'/Yb9KhkDK7gHVz0fy7CRHo1gHQ01xmlUye3TyKkBVLGk2DxXWZJs7uPEOCnPNBojJdRHO5T6QCGpnBwKZZGoytDIbLPscHLVitywSzdSh+FlZ48BEBTOQ+KZIwmMJ7lG'
        b'xt7rssk5S3uOentHuGmXbf8E5Mo59+kCHwq1iA4/svp/EKOs0jTGfoRSmhHKWmUtcUL8sZM4mJEIQxep03dOFI9cLAKapWJiawCFhrfTLBHvYGBD602WWMKjXC7X6e0R'
        b'4IaBcS+6h/sJqAdSJKKNYjUP5ZFZPwwlAWYoSeX/QyBJRyBpGbLS4rIytEZKugewAkkkrlb6bapenca2foatfwv6qJX+I6YuhtzsERS9Jio+dgPFkVVB4XFrIr2V2Ep4'
        b'QlA0A5ggVp4QtSZyxapY1Q/DAG/WwlAYkIsP/3UelHN2/s/xnDIxomNjGmeax9EA+qiani4dBA8DK1uAShVptiWnd5tXLT1DmG9rvWiciZr8FA+MC/srboMGC7SYYUVF'
        b'irXcK8AbQvHm7oR775/5KDFCHaLO0FSmNGma1O8neiR7P/LCb7alZiR9zBWHzPZO/Dhx8y/Wv7Ae1nvbV6vlz//Ozzdx4y+cXvzZaTn3l2LHqdmI88zNk253OG5aOULa'
        b'm5wIMNL4McrOn/RSMDPTBMoRyLUtRpYBrUZmcAyOQ2v4TKzp4yHnbFx5cj5QOyTA5kdcIbYYkhgGRffO5kVit5wuCwcW11tL9OP7a40bLsu1fw3Qm+YNXgMOz/9A7ncD'
        b'aV3vFeLtGUXuBwzE6y7knjAWKshRlTmoPwRnJrPt81KcnIqZpFhcL+MPmsh5IZ3c8vzfWTJvC5Jhoepg98uyjjr1DhYUWdYR3TjN0mBgRd0xemPRB4fqlMlqg2b4CrHk'
        b'go2DXfT/927ZsiaHrkchim2GpcE1pEgdBuj03mWScTyclUzdtkq7KUuQGGhu682PNB8lvv+b7sSM1Ah1dYp16lsRVpxrJf9a3jHRrPgfNlE7BuKodap0ZqRyi5HG6t0H'
        b'8LpPQa04IVNPEX/kLBNC9qR+c6VVQ4aYa/cI5krBYQl0+YUvhg4G2YxKQDmu1UgZN5lUClAfQC7+sCUuFC2RplAG9hT+E2t0Gp44GYDjFC2bNbV+t3Kn1pg+kAvQZ5qM'
        b'1Ki0OgrRapaqH8IShwgcyXqVQx6Z708pDDbqwYY81Jr+M6MeXHXIH4E5am2GOgn9zXbNbsPCodbvgx2LX2hOfaBta43KeL1aZ0jV6Ifft3Kl+T5xGMqVmiS8Gx3VMP/j'
        b'o6RZjR+6d5a30jOlfx/Ec3jVFbNXjFgTvx9+a1xQkKXjan1Kf+Jm2F1RgZGrFrKMDIObH/eUj28JWIueMiDGnF+Y9KzT4Y3jOXbadIktaR/sJhmxjYn1WctzenJqZhQ6'
        b'S2gTjxisJkdGwzk4ZUk7wB3SxgTP2z5azFH4hiVt01hx7LTUPAxRbzCuTJ9696Gp8/B1q6FqMGkOo3Q5jNtNeq3JJXLZWvsX07OcIQNrv3hM8lHip4nbECNeTFU9+jRR'
        b'aN/u9vmuhae2uS103eZa61byTLjNVtfYU9tcnz708ZPPjs+XLb+lelGR+/kTEYpT211dZrukB65X2am8WyMqlx/f+Oz4Z5OSzy39vcOTTUuflXkr3A67zX+Fc0uc4HW+'
        b'HNmwkmOPDxyDS8zzkjv+w/ace8h5tllALpCiMf3h85MyFj2TJg8x457rBEdIiWMOXIqALlK0M9suW+AcvHlyj1STk0aWcSlAB3YSKd+S6SLzhW5ymDl21H/7JpqnRZLB'
        b'CQHrn5KQ+6TDZ4jn/i9T9BQgzSt+UIoe8VGDcTdPma6dxN3MdfVT+itP/GHhk/tRkt4ePxglna+NgJJUlYFwSM1Y7cz+qbfiJsDRTDsBreJ8Dnp1KmMhFE5F3w/0OZoi'
        b'jPTmSTC66oEzjKRb/gmDEZS+eoTG0exlE5JUmRlDefZaCSliKM8wVMpwkz8gjRt0jRh6BEnw74esnohMdYpBuUOdlYUaM4hIl5K5Q2MwapP7txrZwSr2TpF+JEzVIhQZ'
        b'sjTJ2lStJmWIyKTdSs8stTHdk2VPPelOuv5HD2lpdVqjVp2hzMC+oGM2d2aITCODvp3mzdIskz5teK57CAxYcyPnGdkZ1B3znqBKL4oJgaJon7VQSF9NEUJaodAbTZrc'
        b'VD0lsZpHzkETS+xpyGlyzstzmb2Ek2zk4IrHBDELUglVSVASyrbE5uyYKXDWpIQPM4Th1LLQsg4OLaD5KiiHO8nRZhNwID3SECjcxA5wucCtSXFoWCuhcTo3fdFeBiWa'
        b'GQglY+7hVaJ7nDpBzIF6TXHj/Oyq5VxiovuHQX6c+U0JKR4MiUgduU2ToLdIjXi0tdiXFAyHNNIVS+N5z0BPOCvgkE9FM8knPRTcmJRvec4pMePjTG+xuayFDpx7jAbx'
        b'LDHiu6xwTsvLe3nDW1jS8HmQT9QLYUKg3bUvDKk5X3h8/KuE9f9sOffWZI/Cc29NUd69caPDfm9ogvuRB4W9L317JTWm+NjUNaEtrzvGe15/OTskX3s52vPy/ICMh/v/'
        b'0DArKGZH0OWn/M4kdR3Zf/vnn32+8ogseuOKV+fGt0XF+e2IbWr3MRgKTn6U8Yzv17+9MuGdiWHh/w5+5RP11fuZuwIeahJCvolwz0nd45RgVf7G3KpvD3yz7tGvo9pq'
        b'O8YdzH3i6q5Ju/6h+f0vApddn34/aN6FXUWPrme9fvmzmU/Z1ibHv7bB1vn3Te9Fzry4+vDdqNK9X2T2Fv192ecpOSpH8cBMBQLWWWYk9JEXgS1MUgSNLESBC3TTt8Q7'
        b'iuo4FLrhjIyzhhJ+P7kDR1gYsjlrhSJcNfuxEEbFMaCj57PveIVFRqC1HYEKYYqE1CdAHSsb6xBHTsNFL18VFHvTg9nXEF6rg4wUe+A2ad/t5WuvxvkrooZHjQondRzp'
        b'EkLgHtSKGYuLo4MHEhaTZj12Kqh4j5gJvYrlzWjHuWijoZHePCe34q3h0FhxkHd3wHEvX1JLuoefC5q/gdX3S4c7EZDr5ct6Qw8VlfM+5DjksdJdW+AcOYrKKRl85ogc'
        b'3iomXq6Qo+SGVxS0knqf0NDIcG8oU0lwRdwXZmsVzBvt24GFJTtJ4awhCV0xmxsEZ0VnUjtrkleUDzoSlHic1Eoio0kPmwLStoK0eLEo0oe+vECOU3SPJ8dXjvvpGd4f'
        b'ybQMcjkOFLYS+qGSeR1/i9fZQ/MrthL37+2Y9xEDSZ55IQf2Sf/bsu9dJML3+mkW2c1Cn0BBtE/G8HMQhx/RSzXzekpm9E/0OysmabCzGlM+grNir0I4ixN1UnwJkoXU'
        b's/zgRjVFjAUy0jIPDj3mkx7fFh14AZKkf1v0p3ommp7pHcEzPca6f8gFDXI7Q8T8t1zQkBaHiPvJLohu1/cfOu93QaOj2IMNW+EuOf24E4Kbof1+iDmhep14LPMQqSfV'
        b'XqRhq6fZC0EZ5Itnvo5DwzSLH1plPcfsh6Ar2+yIyEVygjRRTxT0FD01NsgRrSF1Kt70FJVyOoK0GpibgC6MXE3klkOOvS10GHPWWOc4kFzSwV50ksfe1JOfRcpJFTmu'
        b'Sx5NKuVpHKmBQ87kjp2faRXKWgDFGwZEdZDqx8QFkhtbNsO5jDToVQbNhwLsU6FNKMmbw5Hqg87kBilZxfzQ5vX0PM36ZQ5cYkRHeqzonPrSXThvLh2jtkR3Hecsflk3'
        b'hb7DqkluvzzR7rlYF45lq0nhykkKVBQ9jIKUuyLOOge64CrUrA5hyM0S3lAcidiVvN96Myq5mr1iBLoktqRDjlrP4RZzi7OXqXjWyL+cKMufv1zBJW7OiQ4VW/48hMYU'
        b'52Ls0DV/rk3mxMdKL7rjNI7sgTeEmj1wPuSq5GIatGwvaWAZA3O+AMHx6lRoEE8GR8X7KugRC/rEqfmYRbORbVHaLIGrCnrCwm6eeMYiboX4HFZVOBylRyzM5yv8oMcl'
        b'gfQw1rDcijQY6OmKRVDMDliQ9gDxhMWZ7eSCgp6ugFxyyHzCoor0slFqJyAB4f4WapWYuDg0MFAcuoOa6uOrUKQl+17ltAiXllcF9ZhYj6eQfLHDYfHiMydwO5D1F8qm'
        b'ix1OgaPmFwUVksE9Js2kxWWl1PxsyG7oZl2eSq6wLo8mJ8Qt2uZpDqzHjuYTIdM2a98+f0Jq8EPcm55xc0n0kvCnlzvVP4zMmXfH8ZlHf1m4KVyxKLy9fcz90Z1OckE2'
        b'605WwJyywNeDv5G62Hxn+33uM996pEnzNQ9vZ/7p/ulxf5xmdN1fUXdz1hGfB+oXG2cEnbjp+O8FYxPfz3A87KX8xRedLm8vOPOzd9//uHfsqN/eefmF1zVLjHc87d9J'
        b'ej702fxD39zbQBa84TP9vVIyxaPBceNr0j/4/O5kRicfOiO45+8fdn4Wb3cvcf8fj1x//xWh0Xfch7ONV3YaElr/sS724Z9bx83YenhM7C9XXv5YXlNyYkuJ/8Mkn9qY'
        b'f8mmp/2zedKU8Q6t706KmXVBv7JqVOToCw9PbufvzWn6/aztnetuL5z03osNET3JV+58GXv2yfQHW367vcvtk6v/XP7u4j//y3nrgdHft21e8Sh2Vf3BlszDXh6TvuOU'
        b'72j85+SoFEaq0yfnHDDzHiQ9blHk+vypzJ/6K9EDmzkPXE8MNVMeD1LPDmwl5qxX8GmPJ213maM+A5xwFBkPsh1lIsJZMRSygNIbcu1FtqMhV8yEB9fGXcZlkPGUQpkX'
        b'eZDkOyLnaUZKRsV7WHmxHWUJ6TWfo4bGBSIbqodOaFN4ohQost4Npf39m0w6BGgjzTIxdL2KDK+axa6DA9c0OEbu7YKTrKt43b1RJEvYw0qRMJG6aEbc9kLZRjMXSoQi'
        b'Mx0KD1M5/mfHpH+ckPx3NqftGT8xJGck0Nc/MnoSb6YnSFAmDCIoEkGgm0FO7Nw0/521YKEs9By2q0QMnuW8rcTy3+5rOxt3dsdUCX9I+Eav6m+apkNUVj+lpzP6KQut'
        b'XUkpy3gzZeFyx38yAmmhsgW4MMlCWWaSQ8lIWJC7hHqHCtx0qJItggZSxDLnAVPC+89Mk+ao6FAfOOFFmj0k3PRlsgX0xXTizvdp+lxmQCJy0nI4Hu7rK+Vs4SRPenDS'
        b'81XSqKhglSRYxUcFazX3X5cabuIgk+7Kt7xSEDc60FX2tz/+Id56ZXPSM38au3dd/Mdb4r3PXfiNR5I0ubfD6Qvf9Iym5MDImI97/v3mv3SGqtXvvXvA8OaBzJ2Zc06W'
        b'/+2h54wPjzg739wwcfJ7S6HJ6VrN9Rc65u779FScw8EV7z2aelJRbS28IFvx6qeuhl+13PL0HRX1i4ANM8qPXMqaeSX6jeVbV9xtfHjn+WNx+2Iu7d94cPGx425amy2y'
        b'yNxvStVFT77s+mjiu/UFIZ96vv/5vHf/Os7j4xPPKy+8f/RPHh/Gnshw9ggOvbJS9cv0BV+/ZPvFpW9fanD42fKF1jVGv/yXzrsGFyQLE4tWG/2ffand9annkvn6Qs+F'
        b'NlUfjIn4xPjl6cuv1ZW7GZ9MffnhqaD37u5/Efbd5V41TnF5+Zmm8+HGnaoTL7+zPnBd0tgtZXONrb9ugz13JRMWaSruxfkEtP+p1KfTYdMHARlXFsVET7hR9SnR9TW9'
        b'ua9i6V+3/lH2z5dPHaj7dv7yui+XZx0L+LPTktJpX3iU715061zNP7Kf/sDmzMUrWbVnf75hj8OTt7LObn3pN+NMX1Zubbe36St/4QvbjA+VoYu+yNy5pvfbuTt1FSsP'
        b'XsyaOC9r9O2sCfXdr4z98HjoO03G6dO2rQzS9KjdTsy+tO69jn9uOBB3SRHR8MF7J8/rfnli4xtz15y+UR1X6+u/JnjhL/3ftc1Zu+CJqAdxl9usP7207yvtew9/+8+H'
        b'PZ8cmlgqy5rs2AefvnbKX//QetLlMQdmbRg152/WWx4eGZv12nN/Lo0o7r0Z/bcx2pSXfvXq2ew/ZW7Kuvymb2djjttzZxuf+0Ngatrbq8Jmq1/PPUXC729z/OD6Xxuu'
        b'P/p122fPfiS7/6dNf/x7x5cOf+1Y4vVV9G+WbPJ/F6z2ffHu1z3fXan+XVpx36qcWaMbPntm0br3e1c+7ZvYcvLXss/Gvnl/8+t273xX8+ac4BVh6nzDtGU3pzndmrrv'
        b'LceE9pjXbewwvKUYnwJXg6EEsRj9rGY+B+V2ziwqcyF58eLGG1zdOXTvrYdcYtvT++gzCAo4N00E1MfgNF7OzvEshwKSR/1Inrw/seX7BPMUS3ZDawIpDqdoXizuHChI'
        b'GQ/no6yZo5kDl8mZSDgaHuHpKzoiRQYPF+GElPWRh0YknyWkIppxOFLmvo1UIJ+VSyeSlgMs9NxMStdjYTFUBJJaupkmLJCQdiv0VFTAxP1QORzmUd5xntyDWzbMZ3im'
        b'wgNS4gGnhu/6W0Joh30sRF20e5Yl0F5KDg+NUKEKWpjGlqw39G/nI1kvtWzpi/v55DKcMIqvPCXVo9DBhkKZj3yGkpNv5act2MHcjjAtdCdc9wrzgcLQiCiqrnYe6jPC'
        b'mTojtfHrN9MkUwUWo0JocRsPLdA6VmX73/Awzv+D7upx70V3g37KB3Nc1gkJzHUlMJ91hr4p0oXn/SVK6pG+l/N2Emt+jNRBIkgFDK55OS8R/8u/srbjbdnVt7wVfRaI'
        b'Ph8kSPlv0aF9I8j4fwty/mvBiv+XYM1/JdjwXwq2/D8FBf8PwY7/QrDn/y448J8LjvxnghP/N2GU8FfBmf9UGM1/IozhPxbG8h8JLvyHwjj+A8GVf19w498TxvPvChP4'
        b'dwR3/i/CRP7PwiT+kTCZf1tQ8m8JU/g3hanyPwnT+D8K0/k3hCf4PwhP8n3CDP6h4MG/Lqj41wRP/veCF/+q4M3/TvDhXxF8+d8KM/mXBT/+JWEW/xthNv9rYY78V4I/'
        b'/6Iwl39BCOB/Kczjnxfm878QFvDPCQv5Z4VF/DPCYv5pYQkPwlKeCMv4nwvL+Z8JgXyvsIJ/IATxPcJK4T6/yqIn8b91p1OUEzsE4izhUZvuEn4OfcLKdjzPu9K/vOjx'
        b'NN6FlTuyT1uarODdrZET8JOsJZMkzrNdJHpPi+9XSfv4hIRBGYtR/zvmJNF79VMH2jhdRgYa4/h+PAJpoFucE/hoCh3seYHRHDIHBh1u0omLSIlWHXpGMKThXT3Hfjfx'
        b'+VkOh5c7Bb99MHXc02Gznl5/6q36+2TlhPCw90PO7lV0qxZ4h/2j5y9Hjy6t9d/W/vN1dRmdTxz9vi/ys947r+vW7Lvta3O8eX7Wo4gXjpZ7PWv/XtRv8r7YNm3V2boL'
        b'bWcXPpg3d4bbewWrVFaMeMJFpKgsTRYdPRqD5QoWnyvITR6aniRnLOmydnI12ZkeGGqnN0b78NwouC8l58dBrSimc6xBHBtiKukkV+n7LejonKWTfMkpI9XLnuiE8FC4'
        b'nB3pGWnFyZHckVY5K3CbOANKMIrvmSnnJHEcNM4lxcxTwGFybonXUugMk3GScA5OqfaI5yxOSOAke2YESjYEYY+xomO6dNv05CG7NZP/98Dk/958hB9FHpoQMiMPtStr'
        b'e1vz8ShriTcvcmchQO/db/NT+qQZGl2fQA9q98nYyaA+IUNrMPYJdGe6T8jMwmKpwajvkyXtNmoMfUJSZmZGn1SrM/bJUhHo8JderUvD2lpdlsnYJ01O1/dJM/UpffJU'
        b'bYZRg3/sUGf1Sfdos/pkakOyVtsnTdfswltQvNRg2tEnN7Ad5T5brUGrMxjVumRNn5wde09mz51osoyGvlE7MlMWzEsQT6ymaNO0xj6FIV2bakzQ0Ofe+uxNuuR0tVan'
        b'SUnQ7Erus0lIMGiM9EHIPrlJZzJoUgYWtjjyyfoweh1MP5bRD/oCNT3NgOrpfr+evuVET/et9PRgkn45/VhAP+i5FD09n6inbwjT0/eQ6OmTKXqakdIH0g96kla/iH7Q'
        b'zJKeniPVh9CPIPpBkzx6mn3U09eR6OlLf/T0TJI+nH4s7QcHOku2FnAI+epxcGB3fG1teSi1zykhwXxt9kBfj08d+lJ+pS7TaE4WRqms6ZOjKZnJqCO8UGdkIPp5m+2I'
        b'blfj97Y4HXqjgZ5M6JNnZCarMwx9doOfN9RHWhQ66EM0xsXim/+XSixDEDjBytpshGMQzmlg9n8Aq+XVGA=='
    ))))
