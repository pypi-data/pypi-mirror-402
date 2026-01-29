
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
        b'eJzVfAlYU1fa8L03IQTCriKKS8SNEDYBUVEsaEV2VBR3IJAAkRAgNwEVFVzZBcUFRVFUVFRQQEBF0Z7T2na615lq6XSZTr/ON1M7Xeyqbf3fc25AVJx/5p//+57v0yeX'
        b'5CzvOe/+vue8yZ+ZJ/6J4BUCL34WPNTMCiadWcGqWTW3jVnBaURHxWpRA2twUos1FluZPIYfvpLTSNQWW9ktrMZSw21lWUYtiWesMhSW9zXW8UsjwhbLs7LVJp1Gnp0m'
        b'N2Zo5AvWGTOy9fIwrd6oSc2Q56hSM1XpGm9r68UZWr5vrFqTptVreHmaSZ9q1GbrebkxG4YaeI3cDFPD8zCN97ZOHTtg+27wksNLRlAwwKOYKWaLuWJRsbjYolhSbFks'
        b'LbYqti6WFdsU2xbbFdsXOxQ7FjsVDykeWjys2Ll4eLFL8YjikcWuxaOKRxePKR6bJqfISzfKS5itzMZx6602yLcyS5kN47YyLLNJvmlc/ID3+YzVNoUoNnUgRVl4OcJr'
        b'CNmSmFI1nlFIY3VSeB/2nCi2gCPvkqPzExMY03h46zcebcfluDQueiEuwZVxClwZsWSBl4RJ3DR5nhhfRz1JCtY0CkYOQycd+YgYvBNXxCjQWVzBMtYRHLqAi/HlVPYJ'
        b'tjr1bSKB0IUFyvxf6JLmZMadLREB7hzgzlLcOYovu4mLH/AecE//53BfKOC+MtaSsWEYhxDNRt20qGEMbXwtnGPIwAvOOZ7Dx4QKjRWLrRgHhvG9MXaTbvn4NKExMUjM'
        b'wF+5PEKve9/TgWlidNbQfKZghPg7Jybk6yHr2A+WtTncXL2Z0VlBh0PwAfaCpa+dXUiy3x/9sl2LhGYv0z37PfZ/WmG34BP2N5fMIQ+ZXsbkCR0jVqLrwIVyn4Xu7rjM'
        b'J9wLl6Gmxe64WxQZg6s8vSO8ImNYRm9vFSxhnqK1ZR/S0wmtCZ2ZNFE/Ndl/ipoZg1GzH3A/NWUCNZcb7e22crCcb7KnNz9HwCHaPQ9QqEA7RiqjcAUujV4YHuEZsYTx'
        b'i4ofhvYsRuVoL5NuYYmPoN0rTUNhgh26PsMfdQFw1ISbUQ+TmzfORNabFhrgjy6S9sOheA+TieqnmohA5UeF+vvBX7QvIIpJxSWonTajc9rRuMaCYbyZwABv1IWO0E3W'
        b'5lgzsxh3YEayzs2YLDCyW+G06UcmnOjAqN2eoYw2ryuW5VXwueDHFV8k/2fymrRo1etp3p8qVOGqvyU7pZ6blpGmS7mbHKl6M03hFKlSOMSqmjWn2TND0v9THalayexO'
        b'DVdla3aLyxovnPKds7xCMUqeEHRvzs3Yk3Zh1ZdfsDk0ggn7w7DWrPcUnJFYD1y5xkcGBFLEmPB+fNjLA/jNgXIVi6W4Ep8xjiBjzqKtM8NHAznLcBWuEDHiGSxqdUbX'
        b'FGwv565QiAyEIwMeHDzuO89KM2Sv1+jlaYK58+bztWnG2b3W1JYlqVVGDRnHgx4wNm42rAMrZd3hZZD0gVCIei3yVDqTptcyKclg0icl9cqSklJ1GpXelJOU9NS6CtZA'
        b'ZMRgQR4ECrEoPOGtw8cSjmMlLHmKWclv5EmtCC4atkoZ7ukRG7sOVcaBgFgwznizeARuwg1hqdwACRQPItpgSvpFm6OGQgSizVHRFlFx5jaJ4ge8H8xI9gF/XLQlsSZi'
        b'PWzQeRGuYZN40FbGC292pxKpRLtQCa4RFeA6hvFhfJzxftqOruAutAuEzx93EfnzTg7Q/vXPmRa8N3Ra7Qv6IlknXnGjGtWii9VNNU1bW0smb7+8NeIQ+0oaETWbtE90'
        b'LLPvpjSgeqOCNY4kEPejk8HKSHRN54VLIqJjLRgZauXwYXfWzKHBWE8Z0CsT+Jymy1YZKaOJwNt4iIHFwGTrfiaLKdN6LdSaFK3RQAYZiHFScAMYyxmIVxvAXTJd2c/d'
        b'24NwdwzhF2pmKXeBt9SreLKMa5Z7khiIVMFRDfxkmRMb4I05ZsGNrGXPqTxMw4lU1EpQG28M9BUzHL6CrqYw+CSqE1R2vfswdvqmQA5McpbL1I4sSng33C0n41mGc56t'
        b'YXCTo5gOfn7RcHZW5HgRkwPQZ36SaXImND2DjhSQ0SKAviMzHfQrFvfQ8WfnuLAhaW/Cuxsb72heXUmBL8LVMHwa2cwGg57BZ5aMpINXr3dln5/kzDEhMHgjcqVWbLiT'
        b'MxnLMZzXymyAjPfiUjr620mj2fCUHywY+Y2Ny+w/Cza5QKMT3oOO8fjiVLJzfAxvRVsZ3D7Elc645jmWjZ6tEDHJAN/ni2Q6A11G3SY6wwJmnMEH0TYGX0ycT2d8HT2O'
        b'XZBoYcE43NhYm5C0kaKLG0fiDt5AlzBEwp7OoavoKh1fHunGLtZHWwLxN96ZMzuIjg+eiTtwu2kKwdcFHwczjdsDXej4zVMnsstmfygC2m90mfZrPGUW2pngTccDzmBt'
        b'T6F9sKHFK+iErtGT2FVpaRZA/43L0rqHmYYR0zqqkOf9CXi0DVcVMrgFVY2gwxcVKNjkRD/wYjf42pSPw+jwjaJJFDxwy8MaHWTwJQu0hw63M3mw6hVfw/AX+GXynly6'
        b'nfWFYDfJeEuGGzcTpAZfBoY30QmFEV5sxqIyFjjG30nITzDvH7el4Xbexpog0B2AO9gAtDmTTpio9GZ1aY0SJuQFvnadXm2eoMU9MgOVTjU+ik4yuGsVPkUnSMJ82Rzr'
        b'mxxwmXeZcStSEOdjqGiKDLdOpTh3O0KsJEJHeDohSuPPGp1ngVi8wN/xWzqSorwWd6yVWfsRjtmhcryPtTKgTsocZ3RFJcOdlDnRLng7y4JzOGuiXqJ2Di7jcXu+HcHj'
        b'ONC2gVXiq6iYToxbkchb2eILRM625uLrbCAYqyoqUqm4AZ2X5ZpwJ0MUgset7ETcjluo8AfZu/IygxGmoeZJuJYdExwtyGEdOuzJG3GXDLpE6DiuhMUg+BNEbtdaS97O'
        b'FggqQgdRiQUbjCtRF9WPENQaCl12LCMKRXVWbAjujqFzfKbh69CRS1S+0w9fYr1RA+qhc/goXmabgyrEjAh3osbxbEi6HSXsRBfURCSbqMIBdCyHgbihGB2gNHTBzbgR'
        b'tDxAwnCFy9LAJiShDoF/LZH4MpFAmBYIsgEq1zYCbaZoZaMzK4AAuN0eiIh70EncwgZY4CY6MQ+14C087hR6Y4bgM6y/FS5T2FNO/sf6AHZtIoZQAoTL2ZhOG19wnMZu'
        b'WCMDHQYBcvjVkTZ+Nm0GWzSmVQRqyt+Ro+dpo9vSIHab3wwx4wDCzHyQRRsb1s5iSwLvW4CC8rWSHRto49SI2WzFmmPQ+ALv4oiCaaOlQwhbHbacBdXkl0WvWyPYg7S5'
        b'7J6gZNBXEC79S1LaGB76PFs7p5voJH9nzE1Bs6ePD2MPhWWJmRxY3b/ZRBtLPCLYo2GJYPBvZN4xvBJNG2+PjmZPO4mI1ctcxvw9hDb+5/I49tyiXGh8IdMl7QYr4L5s'
        b'AXvBeQ2xeJnLNm4Q9rkvJp69GNglAXnPvFM4KoQyWGUNdJVZE6FA1yfbsCHoxGTKxDhcxcgMdrZEkOpiHdlgcLyHqbhE4fPuIKRd+Tyx4nsyQKKV67UCf3ehPWtAEcBK'
        b'EmnvMeA9rJtKpBBcwg7mJnvoufcZwDT/jvfChYKp9XuFPRqVTux+di3/fQpttFnwO/ZEwTxA/4XsO8sOJtDG+8veYE/7GC0A/ezasA9WPRV+W/WFEs8zTF8C+CjNYdKs'
        b'+kNx8T8Viqc9Ga84mF+PxyvBsdTjhmpQFSqPwzutJkKoWBoR441LIZ50ThZPRptHUQzGmUQ03ilicnWfTDDnPkVzhDSnaLHG80SeHWOiwcf2IFwa5ROFa9E+vDMOYjMp'
        b'3satQwcTqK5MKQhCO8B2tKOLJDxnl0PojXei8yZXMrcKfF+L0h0C2hIfCFts0tHOxSJ71IrraJTOoi2oGaaWpMBegpigEYyBUI9u5lU7C5peHZVv9PQK1AiNpgwhZUuW'
        b'pkcvXejECAFXN2Sebf6+zHOT4cNuRuUxzzSBtLdHp0XRaLmKJKhRqMoHdRREoGZ3lpEbLezwXnSFAhiOzqLN/gEM3mMPs/YwKZ4yk5xYsOYFzkrIvSC5hRymAVVDMhYh'
        b'ZoYoRPCxBu8QVj9jxUAGkjmO5CBgRg/hRto+ejru8kdt4kR8EHqOMLrZ/lTMcZ0fvubvz6BL86C9nkmfjA8LKct1dCzI31/iGQLvG5g10qUC/Mu4YaR/IBMH+KNaRi1B'
        b'p02jCZz6Tehw1DDcGAmJVXmswBq7HNF0vA/V0ZUkqNXRP1AM5qsWph5gNEHomsDSnahoRlQ0zPHBlUqWka3AVYs43JKvUnB0K6vUtv6BHEviV/C1aej8AqqIeB/k9R3+'
        b'gZJZjsT2M+moDbVRbZu7zIjLR+MiyGFiLBjxGBYdQ9vxBboNdAn46x9Ig0F0iMnA+1EFlY61EPgrCTtwaSxqFjM2wWibD0jHVmw20adRJ+70R50QSqDN8Pkoo8OHVVTs'
        b'xqHuKFzOoWPRkSQXEuEeFtVNx9tMcYJbOoO6+OiIiBhygFHRl3u6eys8QDMqY7wVXpw1atQAaU6iE+7uqMlZqUB78AnlULTHeRg+MRyd4hhUNtQBHV3krvvp4cOHo8cL'
        b'2X7O9FzPDMsRDLU/HGToNcqYEbFe4WJGHMKiM7gYdSqGChFmO76Eu3g1OmRrMBH7VM+Oj1sl+M0rkNr04HZ0BV2xEzo7WYXejs5TL8ObcftEVGGe1gM+tXmOQJEtuDae'
        b'R/WhMIlYtT3sWNwIukSYk4CqI3hUIc01WRM/3c3K3dB2upob2jKLV6K9uDMfXyResoIdh8pQGQWZiRrRIdw+zwf6bAnMVtYPN0gFDPahaivZUtRqJ0NVYH1XsCvdcGsf'
        b'b9pQN5+XZbTOJ/HMNXYUKgLxItPm49JRvApfhS6y2mZWjhtwiTDtWPpU3M6h00YDvgjIoR7WVQyKRBBIko7E1c/xuM0oAcNQz+CqyWgv7UGb8VW8VTZ+mtQWUg7RNDa8'
        b'AEScwjtrMIADuJ5tyrUhmz/ITsZ1kIcRuYtHJ2Nlq/3tbMAYi2ayEZBwmfe+xZEQHzLtNnsDxEkiO3ZaHmoXUL68JBa3T8dV9riNOBw3NlSCy4Su/QGono9Crbl0LdTJ'
        b'jhmLSimFcSO66MMDwN3WAs92A84nAC+q11UJ42SaYNojcmJ9eZMJzAyT6O2BawwsZMiejGfcYiFGrI9cjsrtV2da5+axjBjCDlSJ6uMpOhkL0BUZvjC7Hx/clUNDPnvU'
        b'hmsAnVOo/JEs4aO4XIjCmtARZx6fXPBoZ3MgOKJdzYF5MG9v/CNBQz0xlOL5eDfu5P25R3KmQHUKsSC87aMX4vYF+NwAHqIivId2TgR5rMal+ORAPqLzkUJwujU2CSLZ'
        b'rmVS8MomsBPoCos2ayBQJ6cAlrjFH5Xn4w50FXfaoFLQKFzCogNg3i+B+4ul1nCe0woZ3mv3SCD9/AXmVE3DNfwIvOeR0CXibkr/pNB1vC7gkZzOSlfYUYrGoYPLZBNY'
        b'ayvcBpwJYufjazqKPQBHHTwqmmem5z523FBr2pOKGqbxkFqcfKTSnIhuzNWAq2UTpVLKZWvWG28RovgsJ1QPit4tthFmtLCTrfOFLR9YjQ7g9jSxycZAehpBdq8azV1J'
        b'bjwIUI8d7iRRNz7CTpB6CEw7MCqDDwGP1imzIpF6G8TwVR7UrEOsewldkKFSVGSA7K1DTHnqjZrDBMdzbA4+IFNH9CsRvjZJ6LiKOoyyLE/cYZUrYUST2Rm6sQKnW/B1'
        b'tFeGr6EO0geBmTsbtAjtobJqQuWjeXQpAlXmCDlDC0hdscacujsF8PgQMd859hB641J2Em4KNJETEBUEBQ0gBTWoKg8S30qwRM2BqAlS5P0gxvuWwlrtLDM+UTwMn8Z7'
        b'BQ3qTMSnYMLBeZYQnTC+6StNC0hzB24DItXAxP2o5Alge6C1Gua0wd896ALqgrZqGFeMtlhZQcq8H59GZzPWcCSXPmqFDriiSoqzBh/ElTw0HhxAYbzFT+DLkaVTZbhU'
        b'PJC8VnpwmgLSYEovyPDVWY8I6QcZBe3bJUcnZfgyZPf9hAxGu02x0DfBYqgMV0aBHwyP8aYeS4krYyK9FuGSuHh375hIXB6NKyMUCeEQfiyC9Ooiv5Thh5HD0+ah0ty+'
        b'Y1QHtNfJZtEawR6VQ3bfBrp9IHSAkm6aQcUkZqaUKCGuGjZQC/FWUBeKYxuw5xqfKh3AO9N8wJFoML9hVVQQPuLt5RFJttwiZuwTRDp/CPeIBm9MsSOethJtRyeEyEKK'
        b'azm0F+hyhe6rIGFoFN4Z7hkZ5yVhZFHAr1bQoQm2VFNG+Q8B14bbHindItgfCRTWKNBlZWRMlFekqzcsC4EkKJUIXfBDB7RzJz/H8d0cw7TW3lm9ODhuWOjQa/7tD+Jv'
        b'ffTBj6XHbhw7WuJe5uZeMvatm28fneLc+faHRWlDXi9w0aWlfFqem/q9x5AhZaudlK4rUycevn7jzSMhoZq/Hnh/s/tLr989xL/14YOOuoR9TT63x4x490W3SePv/lx0'
        b'MXnEkKiEr3I4Wa++SnH8UOfJ6d/Vdvh0aO8Vp1vs59+59tX3Za/+NffByz/Ilvo1zfP+OvAF6+yXvOJXfL7l+BzVAc2KBxl7dti3BHne4P9wL9JyVZQ6f7VybXNX072h'
        b'4aJXoooDgt+NRH/PPCQqvbN+6z3x37/KrY8Wx764tfZP04YfuzB2W3HPvZzfFUy3/axm7o5ZfldjPnzrUtWoWzcv/HLQ7dP6N4y/X3mEvf/GX99yLmlOzn/LLehC+Mi0'
        b'cVV/TS45N9nL5Bu9wvaDUas3fPjxS6/+eVzDvjWlQ2fEvXysUDXT2BKz4aNt0ScXf3360wrFF4aET0tXnfMY4mL1VpvPFdGKy8Fv/ylwWP4X4/Jy/3pjT5DlFfGG149P'
        b'/PG3tsKHm9+YcnLx9C9XeZR11zkvu2dhDPoh8N33zw2NTvj81VXfvfRepEeVdpJjcFbJcZNjpvUXTu/9h21r6KxrmT8quy0Kh3V/NqJr7JqWLwN2XT/su7/Quy0y9uTu'
        b'fe0l57+I9H7Q9mBbusliWMvXtkM2N/3tFb+TZ86evl1/drff1NFpGqND4gt/uBVyuwAFGLcenxAy+8EnnzutfPWrFRrr2a6rRjesut80Or/9/NpRM26v3Xd8VW+LPjZk'
        b'2lfG56qMCxs+GCXOv7Xki+GXegtXLVv25+6FJS/FLh/fOvqPcaXZodPKD02RfWEoWf9p809ddef/Fpj3WeB1j5hbF42yJbWzP2s9WBz8ttd3PS/JSptvnf7qtS2pU65v'
        b'fOdnUd47rYlvlU/xUF+3fMtywwff2O/qfrj1xMRZD66Hxn397s4v3xyd/pD9If/wr6nDv7nGfXn0+Fvu638bfqZq7JtFrMLWSC/T8vA5XO4ZC6EqrvKEsBydnYyawbCi'
        b'thl0AD5onKj0jkDHRnh6KLxhDC5lGBe5ONEdnaQHxbjTGZ3G5fnPPXZHAFHjdiPRI9yKzqcrvXE32g9hcSksIUE7OS98GJcL08vBZl+M8nRH26zCQdFAf9FZbh2+IjPS'
        b'QH4rKrKJinDWxHjEWDISMSedZmUk+SYuHoOOkiNegInPzQD3X4GrRMyQmSJct15tdKQxV6a1RVJUnBd4szw21C3aSMxicA7arvQGY9uowGWeJGM5x/nPKTRSG1aPa/ER'
        b'XB7j5O4ZgXdCZwBnh8+NNZLkJwNy0V1R5GopKoLE9kAsdR7ewuE6tCNHuC5pnDBD6eEdDoZfQNVqJoeOrMG7KSXsk0dGgYECO+tlJY0kFw5O+JIIF69GxQqHJ0/T/92H'
        b'wupfm/Po9N5JOL03GlR6XiXcQ9ND/E/gYT1HykrYoawNK+WsWTt2KDytRVLWiZVCG7Sy1vTlQP/3fZLS93ac+TMnseRYyUMb+OzMOnBSTsyKJeQWyBkgSCh8rsiOdebs'
        b'oG0oKxZDf/9/0t/3hL/fOjnYAUwxzLRj7ehqsDo3Bp5OHH0BFNJL1nPgJKwL9Awlvay4CMZCr91v1mLAqojZLL5vsOmjhULUazOQBAOuJ/41yipYg20fbSn4uYz58mLU'
        b'9UEuLxTQYeUKYkIvLzqSUKWPArJNZWy0tyDiSgkzH52zhMSxc4SCFUJHDShQhGcECV7PukL8W1eAep46HiK7oCc30Qw9HiK34MzT9+Bptv3HRNw/e0z0fRYAt5YP+LeA'
        b'yBAvVz1euECrIdblaOQxi2cE+MqzDfSNn/djUx/7EGGUGzRGk0FPYOm0vJGASFHpM+Wq1NRsk94o540qoyZLozfy8vwMbWqGXGXQwJwcg4aHRo36MXAqXm7iTSqdXK2l'
        b'bFUZtBreWx6q47PlKp1OHj9vQag8TavRqXkKR7MWZCAVoJAxusdA0etJYVRqtj5PY4BRpF7DpNemZqs1sC+DVp/O/wPcQh/tYp08A7ZGCkXSsnW67HyYSQCYUgF1TdCz'
        b'QXgBDdUaQ5JBk6YxaPSpmiDzunL3UFMa7D2d58196xVPzHx6DvAjOTk2W69JTpa7z9GsN6U/czJhAUHz0XpzoEWn0RrXqzJ0T4428+rR4KhsvTFbb8rK0hieHAutKRrD'
        b'QDx4spHBB6eodCrAICk7R6MPouSECfo0FRCeV+nU2Y+PN28mS9jL85pUbRaIAmBKCDXY0FSTgVBo3aPdLMUnMgwm/aCjyb12EH0CTFNqBgzj4ZMp61m7TtVl85q+bc/T'
        b'q/8XbDklOztTozbv+TF5SQB9MGr0FAd5uiYFoBn/Z+Oizzb+E6jkZRvSwb4YMv+HYsObspJSDRq11sgPhks80Rv5fJORT80waNMALbmPYHXl2Xrduv9WnMxGQKunWkoM'
        b'hdyMmkY/GFq0LuAfYDVHo1PxRjr9fwdSAwOKoH53NtAX9du7nGze+CQAs2Ro+FSDNodMeZblJrzWaFOesWPiuYyqPuFaCp4LltLpniFh5kUfiePjaz1bNP9luhs04EVB'
        b'6YLkYGVg5CJ8NTUzRVhgsPHEFgHySZmaAazq2xCQQIev8rxG94+mGsHBP4OIZjhkxOCbfcrjRpn0ao1+cI9pXhZ85CC++vGFYcw/gpGe97jfnU+4jU+kGXmwVGkQxJDu'
        b'wSbmGIABYPNUg6+7wNyt0XvFGryftfvH1n5q34P7f7MgPBEDPDb5mfGAMFcLSw8+MWJOaOyzxS4p26BN1+qJSD1tQ+LMfSlUIEGB5WEGTZY6/5m6PhDyPyHQwvB/0Zhk'
        b'qMDbDGry5mtS8FVQ60Fswn/DxogaUD0jdu6xfS2Gnn+sbHpVluaRtTPHxXL3WGgeVE5NhhwaFz01I0FjyNfo1UQt1+drUjMHm81rclRBAwNrADAgqh9kxkq9fnWQfIk+'
        b'U5+dr38UdasH5gEqtRoa8rXGDBKkaw0kStUYtKlyrfofRfhBkEqrsojZhD0tzniijPvxiUHmPCcI8oLBPMPjox+7lyc5oD3z5L38YqFE1mQUaot9Jdv4NVOTzGXE04R7'
        b'bl/nmGl2mYmMyZ+cXpzCZ1EXKkftqCwQV6MOVIGu4p3kcPsMqqRH3dwU3IyamVn4nAU6inpmCTe0h/E2tGUuKkHtkDnPZGaia+gYXSY9TLg5901YNzoxLY+hB+vWcaja'
        b'Hx9RCwW0TOpSHb33HobacJHyqVx33FgLx1kjcf0EhS0dlo/P5eDy8JjoCC9EzptgXJSXhBm7TGzpiU9wk2gtueca1InLfSLJGB96hosro/COWbEWzBRcKVGKUIlwnd2N'
        b'NouUkeicwTym/5QXbVPQU2BcNlsb1X/ZPQPXmO+7V6BL9GzaeQw+/tilNoe22eMWWYJQilAzAjXjcnq0PgTv9eIYKb7MobJVeJuJFO1nZOAtBHoEIBGLKnGVTziuFDFj'
        b'ncRoL27DtSvHUHRwI+qY1jcOl8+kRY07cSmpbpigtJiFNgeZJpPjheU+A6DFCVUIsTEso8AnUC26aoEO4v24h9Yp4M2JuKtv9HC0iy5PSg1g+IRkixB0Cl+kdR3jR+Dd'
        b'Sm9cOV8OIL0jY3Cpp0LCuOI6MTq+KFJA86zjEKUmAQaRStoYXEZGDB8m9p0zlaKp98JnBuUs2o2ujoRZPbRuu2CVDU+rkBe5k2M9Uj2xlJyjwfhj6GjUkgW4Usws9bJE'
        b'e+VK4ZK/Jgm3+ONDdn6kRHs/o56IdtM9++Em1AN8bX/uSb7iBlwpFLqhs/icPzqOzvtZ0LqCDF9URC/V8BbcsAJ3m3CNcPGDD0wXRGGb47BHooCOuZlFwRJX0/5QfAZ3'
        b'PiELHX64ZTI+reCEa7TKXFzsj9pyJAwbzaTjWtQyDV2mSrE+DB/wZ+WojaH1GZlWKgpz/MI1ZvGBnTb0yw/uRCcVEgHmyVhc6e+fI2LYKAZtjwB524Gvm+8NL+Baf398'
        b'wYJhFzF+C9BFHu+lkxzRVVTs72+ASXEMarRA54HC5puYsrmTYE4bzEkAIcEdqNMWugi5w4Ey5f6oB+3xZ8mtOpMZuUm4Km/Fu1CbPz6W4k9oeZzReZrrJK8qnRlPYgAS'
        b'P0nPHbWIMZHyIVQbsolHO3kAMo+ZZ5hCR25lHch3WKb7StbMWh+/nFGIqIaiU+hgIL3fAaLiOrSz/34nDB2mJFLjbfhElPlyCF/AB/ouiDayFKFEVLMkipZ3i1E1viBm'
        b'0ZFM3GzmyDR0DNf3U+8E/G/ORucFQuzE3SAhfeSLQTvQxfzVVB9REwysH1xxNQW41gGVAHxqGjfbu/XRGbcYgc5F6JRwW1aE9s58ROhy2HcnOo7rqXKOxvWorg9+PG55'
        b'UuFheB2V1SWoYbY/bhjfxxDcZjJNJDs8buf5DFPAu1BDgHb40h2uQtdxj38aUMHMOnwQV1AsCxNRc7/RuY4PPmkhwnAtFYuFsbjOfzKu8BfTkqMMtAt1UrVPwbXpUWCC'
        b'zwMC3mAU3PvO6F1RsRg1OoGYEhNqAOCnSLWMwisNb4sQM1aWHNqJtgtVb0WW9swohnHxlYQxYb5RDF3SvnCKmaXxiHL0eTCoY6ho4SP4XJ+8gIvq6JcXfHIVvYlcj7rU'
        b'ykivKC+P2GWgsRUsY58u0sDgMrppg00eLd+Kzukv4ALCkUoh12gx2r0MPMckGDYGHOW5J+q8+ou80FnUbgeOs4hCVKCaWYLdQDv7nREw0gM1BqbC2MI0oU5heyy+SEre'
        b'wLZcn9hX8SZBZylieDOqQxeU7hEzzJVhA6rCZrrS696F4DFacbm5NilSRquTFnqZPMj0MxNQWR9ZlKgUBBaXRZPrmijQgM2ECn5ovyQiyI0Kp+Uk+4FXptwQsCr1aGe+'
        b'UMh1fBRqfbyESsSgZvt8P9BZFyEeaJ6Oy81lWTOWk8IsmF4kXEpvWR04sDZPtA6dsM/3oJRCh4GqNRCAHEaXibw/UUaI6wqorVwN4cb5GKUMgo14Jh4fxddA28h9zzi0'
        b'BVXO3GA2LDpwYERYlqO6CbKR4OMlpDAFQg7cqBBu+LeikhkSfADXsPQ7FrPHCxI3XUoLEn0n/bYqe4qbUO5n8dxcDM68He+3JHUfTNKkQMH8VqGr0Ix24Uu+IlKhxGTj'
        b'DiuKqdKEr+AaezvcgXcm4r2WjFjMLp6/1LSITLuegtoeu4AnylEFpjweHfPEJRHQ5YNLF5Db+HDhKn7hAtTmG78o3HOh4BPN/hCds3WI06MOKkPjWXy5zxSu8OszhG7o'
        b'EEXsvbUyBggi9ZU05r4hnsosBn7RG7geoElRFPVboONtoDKSJM4DXbamQFGT+rl++1o1vA9qjIhev9ugk7hfstCelf36lo8OUejeCxOUmxKfjg2SV9JN/Zpgw4DQuPum'
        b'/d79TnAqQ4M8T9SArpCgIw1ffzrqWLDIRL7MNx6XoYP8Y8QBypBvrnl7uYN4eZgL8eIJaUs8E8KJRFG5XUiIeGzK43S8XuCIKueF07o7sVaou/MNZPNDwC1RFVRPwxWo'
        b'HJemDiKaymyzQ5kXloLaA4iDX8iQgh5QnDO4lYrQdNUY0sUSb4LK3VHLQtY0lTqadABXg4Dpu/A+iLIHVpW0WKC2FHQE1y4ypqCOqSxQWrLcCrUJwleGLpIqWDPQTFSP'
        b'WhKFWircNQ9f6t+Jlx41o4shCrEw7Tow45p/YC64pUhm4nrUgrbhDqEqZwsq0vhvwq0BEhpRadDFAqGjB+9d6h+QBwuFMOudUROueZ4C80Obg2EdfIEhfiyclOiBQ1Kw'
        b'VMMUod7QNwW6wph4a1RfaGsit18aN3QMhB+82E7gF66KxxdsUWsAhCt1Uxb0i/sir4SnpB1s6BFrfFC0loLPQk3p+EIBOgub3cBscEMtVPFWoEY9OhuIWjmGc2ZA8zCk'
        b'L6hGCFXO4XNAplaIPM+Cw9vEbEJFzsA7wqAVo/AJyIFqzV/h80ZnsgV6HV6Xi2vwkZGo2YLUQkG8OwPVwCQa+x5xHtuvHZvBfpnVIw/tovqBSqaCWe/Tj7MB/frhiaoF'
        b'TlU5BuD2fNxJCiEdZuIuNmDlOoqH73O4iDcXxNii/bSeqRrV0mpl00ySXrG4WxYbgyu9cGVBgln4cenS8Mgl4YvNNG0CGxLj5R0bHWcBwRS+YI22oxZ8UvuO424L/g8A'
        b'an5mw8YlUVWu8xxa/l6//K21uvP5X75x0yE5/94E+0TXZVJcsPmGk1S8/bXPE1CZ5/K7Ll6cSVbq+O62moXTx8nWVbt9M3567isHcubkzPnUPudPr9+e+tFEx3EjL1+5'
        b'X3fwzPmz1/XD0yInrvbfaHjxs6Fhle9cMISqArW6lkMGlWPvhQWX37Qb1rvjsqE2bkmEi+i91z7jXHfu/OpiufrM+3cu/D718PeOqdOTX++srOOnDn9/5Fu2xs6sJXk9'
        b'Jc2frqgyNL7ybsCFM9/VdzreKjwyOzdAm/DLzfUuy6d+umV65wus+qc54/jRB4qds6dHaM/tKBRlMt03Y1y/XLTvA+mGg42975VoG8UzfXYVvrJ078OZPWvG37+SLNvy'
        b'IdcpvdvlxnXb3dp/Zf7Xi6suzXz78l+uvji6ynnqTwf3Xz2inO07pe1vmg2/HlfPch9RyLwnyou/8ED8wO7Or588aE8uFj+Q3BHd2DTsbugLPdwPb4dULfnh1pJPh538'
        b'omxpY8unHWe8q/GWsY4Fi+9OaX35pUkpcSUbl92NaPVqvZcSVxrs9UPFnflXv6wp/Omd0ssNqyrOZAYf3DGxVvOXNE+0vPC9M/WeW3dV/pwT+cdc093Vr59dmzQus2Vn'
        b'xx/eefVlycg7C+9GfVgVfOQbp+LU7995cKz1xZfffzH9s5fzX53qG/fDmqqWXvVzHk15r2wuxx998Pmm3//lDxVHqn/bmFX37RvBKb/o1qSV7NjdkXlZGpTxftjffx4T'
        b'Mc/qqnfmzp9rX7+tlNyaMVt2bcQnb5+oe3ntHKPlh3O/aV36y9cFd/9SIypMSTj3wpsj165e3PxNfOOWj3tvNWcO5zttl3iNC9MUznnoWnDfh/vg87e/unZ7yKXZtl5h'
        b'N+o3F3rf/uXui5/EHNz9fMvHE7+dsVA37McNkfi1Vx6i3352evMXt00+Vj+GX8re8uC1bvG+4bk/jN8UEWRxKU92utW38h2f7R4fyaK2j/xopc+vyz/87tTN27tvfXPm'
        b'3KaogL8rf3xRdFs1PDup5pf9xV4/nS+/Hlxx48urze9/Mvda/m+H39eu/C5zz58/avrG9d2ZltffzF5fqH7p4zM5L6455/bd2aKx367c/fMH3R9Hdn1c0VNWFXLTNf+P'
        b'IQ9GoyZfw5yYvEWXkr/6ZOy2I2uPfC+vfcN10+ysb5dXrO98rXze4WF56x27HT+/tPW87sqb6THdGTMXuJy7rau6mLd6+MYQnBcytuvm/VvXh/58KuOX13537/5ngRt/'
        b'9+vUW5Pakmozvrv+WrZsaWF9yuzKmWFf/cJ9Nzp0vzg4vmFZwevKZd0jmr+d99WpxHvKcT/dydlq09hTF/adrs326tnf+31x7/Cvc1587+Evsp+svxp3f3XpiaihPz5k'
        b'O5edvTkUK+yN4xjytaEGXKvEZyHrJvUoYEjNxyXDUac4HFdk0YIY3O4To/TwVuAy9xBI1qyWc6gRHZ5GK1rG5YLhKY/xjIAwuKK/IKYR1wq1O1tItqCk0MPxtr7aHnRc'
        b'SrvnkW+IRXm6Q26EW3BXf2nPtbH0C8ioKRpvf6L2iAOPVgWDd6J6WnMTNBVtU4aLRUKZz8AaH3xoDK0DWgixwknlRLzVO+KJAiXUjaqFspyLHDqhjI3xjDRArAtISNFl'
        b'Lh+dmkNrfmahIrwLoq0yn0hU5QUY5nPegPQ5WrMD6TC6HAW2nUJWgvsA4Pa+ovQ0XyPxDQluBULgpERd5rgpGNdQuKMhqipVErLicuu+OiNc6y5URZUWSiALGfDNWlQ3'
        b'FB+GzPKA8OXs07jBC7ejUytJtRFqzun7evYsMUT8QYph/7/rhZ5dv2L778N56qvBWcYZAb60quggKVMpZAqlTo9qfKxpnZCU1vVwrB2pLuJIDY81y3EcO/h/yT2pvZhW'
        b'INnQmSNZUl9E3rvQSiXJr1KLvl5hBKn/ISU33EMHjvtNLOJ+FYu5X8QW3AOxJfezWMr9JLbifhRbcz+IZdz3YhvuO7Etd09sx30rtue+ETtwX4sdua/ETtzfuSFkB9Iv'
        b'7IbLWQmsK2YdWBfWQWQH+7aBFUbBaqMeDqX1TA6c9UMJ/CU42rBCdRKphrIW0c+/Wktoz69iCWl1Ia0cwcQJMLC2IBVLhArkJeYkMELCSbgJpEXECRDNVVLWnA39NAp2'
        b'MhT6R7J2Qt3UQ+6htRjo8Zu12IbSWVzEfWvtQFYgdVs2AI+0S2BNMWew72OfQtQrJufYA+qg/n3BULAGhz7RoEu9RkSC6BWzeULnINVR1Gx02i0yf7UbV3lBjAPx5cic'
        b'qeiqCF+2wXue+oY9EbAQApeEjBrywy7MCk7NrhCpOfqTLaJeB3osT0uWDPMMhmzD/bHCQT0VVoO5Akmjlqv0cg3p945ViHulSUnkZiMpqdc6KUn4BRd4b5OUlGtS6cw9'
        b'lklJ6uzUpCRBAx49KMIkZf2MNR/ZSxkpR5Pglbg6XWaHu4wyK4Kk1wiZwaz7PviIxMID7VewYdoln/yHmJ8Hk8fEuga//Wos9h1qsWBm7AeX4oNO2GrqX+Y09Q0VGg9X'
        b'519uLBGfeZFrm5My1+390JSXOlf+VrPfbVzU/E1xt8u/iPuiuSHrsPX0tfOvvvfnmRUjjy//7vO/fWzj/9FfPZxCff7S/nDVu6rwyzYJ/h8tbBmfOHJ2sc1PloXJb+1u'
        b'/ynj9rRqu7VXfy1wbdyzuNNjPTdCPVfpdCk+YmKwaN2dhorXJ+/gyj4eNXFPhOWwNuv9d+dW3n2ZmVEyzuAy/jP3m6/kRlfX1LqdmjL3zZSdh17mlr/sdnmbpm3zMMOw'
        b'zGUvSwJbt2fdTR5ecOdl1i5326Sd3T/YV02PzSnzP/TnY5lhO1LKlFtHfnZ6buiB330zYcWlE2OsVr+rXf3OiDWG719SKJaEaRQHTp07qpuzd+/xVT7FmX/clvCLcveX'
        b'X0XvX2HTlVFsk5UkdvvEUdSd/u03w7v/oGvh3laIjSQU5/ChcZB9QI4DedDZ6QzemYuuUHM8HPKaYuHHMvAV1Gwa+GMZifiykTAOVyz2k3mQAs/SCVm4IqZv0FjULsbn'
        b'0SXcYpTDsI1ou5RHzStxQ3isV/+RmCOuJqfTZagTdIKqhtN/oUmX0Bzi2Q9qqkG+ddkqdVIStdNbCH2cOS6AlROb8ZBYCSnnwDlIOQmxoU+9iE198kVs7JMvYnPhJRFb'
        b'U9sl/RnMnWDRH4ySMoWclQ3rzhIPwY1wZg3DB9gjDvTqkTVy/K8hFWtw6VdYsjgxTrR60/vuM+xTGCTHDaicnBuSXzNSQ05YiqosGbsRotGoPF379Ydilk+DgQuqG0ff'
        b'nGK3JcRhxzuFafm2xpTtkyasn3Tet2HFzMi70bN/cF4bX3F+varhTFfCl50/3T6Y3XPq648/HOrc9PlS7f2k73/vhF4ZGrT+TZtV3+TlhLX8MTz6j+ten/uZ+5GW99Pi'
        b'vr/H3lS6dFusU1gKAUUrqpTTX8KII8d+uD44yhLijjYOIo1mfIgGW0shMz4dJdkY54VbycA4Lw4E86oINWzCV2iwhQ5OQecF3MjxHjqXBJk1wc1JNCbFlioROob250dF'
        b'mMu1J2RzUiO6QMOwxYlclPlnm573IEeOMgWHqzW4iPbOd/Lq+1GnXMtHv+l0zJ+WgS/GxS4z8E5lpAU5qYccfS8606cp8v+2WOj/VYjE/1DLtHqt0axlBFWprbW5ltpT'
        b'ROSeKRQvMYzol3u3XpFOo+8VkzraXgujKUen6RWTC2Pwz9pUeJJayF4RbzT0WqSsM2r4XjEpp+kVafXGXgv6myy9FgaVPh1ma/U5JmOvKDXD0CvKNqh7JWlanVEDH7JU'
        b'Ob2i9dqcXgsVn6rV9ooyNGthCIAX8aasXgmfTcpde621vFbPG0k1Xa8kx5Si06b2WqpSUzU5Rr7Xhq7uJ9ze99oKgZ+Wz54e6DulV8ZnaNOMSdSb9tqa9KkZKi142CTN'
        b'2tReq6QkHjxuDvhPiUlv4jXqR2ou0EBuID/DYyCX1gZyc2igJ/ck4zEEkAe9DCXyaiDl1AZypWLwIg9ydG8glxuGKeRBkhQDkXwDOSQ3kG+KGYiyGNzJgxzOGcgttYFc'
        b'qRgCycOXPOTk4UMe5ITHQOJ5wzTymEEeyn57QZhm1cfWyJ+fthd0xH1p388k9TokJZnfm03v/ZFpj/9inFyfbZSTPo06ViE1EGtEggyVTgfGkAoJOcnqtQamGIw8KVjo'
        b'leiyU1U64Mcik96ozdLQCMcws4+YT0QlvdJZQiwzm+3buZgRS6ScIIpDNRwNoP8Ps4WLNg=='
    ))))
