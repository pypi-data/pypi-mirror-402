
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
DATEV module of the Python Fintech package.

This module defines functions and classes
to create DATEV data exchange files.
"""

__all__ = ['DatevCSV', 'DatevKNE']

class DatevCSV:
    """DatevCSV format class"""

    def __init__(self, adviser_id, client_id, account_length=4, currency='EUR', initials=None, version=510, first_month=1):
        """
        Initializes the DatevCSV instance.

        :param adviser_id: DATEV number of the accountant
            (Beraternummer). A numeric value up to 7 digits.
        :param client_id: DATEV number of the client
            (Mandantennummer). A numeric value up to 5 digits.
        :param account_length: Length of G/L account numbers
            (Sachkonten). Therefore subledger account numbers
            (Personenkonten) are one digit longer. It must be
            a value between 4 (default) and 8.
        :param currency: Currency code (Währungskennzeichen)
        :param initials: Initials of the creator (Namenskürzel)
        :param version: Version of DATEV format (eg. 510, 710)
        :param first_month: First month of financial year (*new in v6.4.1*).
        """
        ...

    @property
    def adviser_id(self):
        """DATEV adviser number (read-only)"""
        ...

    @property
    def client_id(self):
        """DATEV client number (read-only)"""
        ...

    @property
    def account_length(self):
        """Length of G/L account numbers (read-only)"""
        ...

    @property
    def currency(self):
        """Base currency (read-only)"""
        ...

    @property
    def initials(self):
        """Initials of the creator (read-only)"""
        ...

    @property
    def version(self):
        """Version of DATEV format (read-only)"""
        ...

    @property
    def first_month(self):
        """First month of financial year (read-only)"""
        ...

    def add_entity(self, account, name, street=None, postcode=None, city=None, country=None, vat_id=None, customer_id=None, tag=None, other=None):
        """
        Adds a new debtor or creditor entity.

        There are a huge number of possible fields to set. Only
        the most important fields can be set directly by the
        available parameters. Additional fields must be set
        by using the parameter *other*.

        Fields that can be set directly
        (targeted DATEV field names in square brackets):

        :param account: Account number [Konto]
        :param name: Name [Name (Adressatentyp keine Angabe)]
        :param street: Street [Straße]
        :param postcode: Postal code [Postleitzahl]
        :param city: City [Ort]
        :param country: Country code, ISO-3166 [Land]
        :param vat_id: VAT-ID [EU-Land]+[EU-USt-IdNr.]
        :param customer_id: Customer ID [Kundennummer]
        :param tag: Short description of the dataset. Also used
            in the final file name. Defaults to "Stammdaten".
        :param other: An optional dictionary with extra fields.
            Note that the method arguments take precedence over
            the field values in this dictionary. For possible
            field names and type declarations see
            `DATEV documentation <https://www.datev.de/dnlexom/client/app/index.html#/document/1003221/D18014404834105739>`_.
        """
        ...

    def add_accounting(self, debitaccount, creditaccount, amount, date, reference=None, postingtext=None, vat_id=None, tag=None, other=None):
        """
        Adds a new accounting record.

        Each record is added to a DATEV data file, grouped by a
        combination of *tag* name and the corresponding financial
        year.

        There are a huge number of possible fields to set. Only
        the most important fields can be set directly by the
        available parameters. Additional fields must be set
        by using the parameter *other*.

        Fields that can be set directly
        (targeted DATEV field names in square brackets):

        :param debitaccount: The debit account [Konto]
        :param creditaccount: The credit account
            [Gegenkonto (ohne BU-Schlüssel)]
        :param amount: The posting amount with not more than
            two decimals.
            [Umsatz (ohne Soll/Haben-Kz)]+[Soll/Haben-Kennzeichen]
        :param date: The booking date. Must be a date object or
            an ISO8601 formatted string [Belegdatum]
        :param reference: Usually the invoice number [Belegfeld 1]
        :param postingtext: The posting text [Buchungstext]
        :param vat_id: The VAT-ID [EU-Land u. USt-IdNr.]
        :param tag: Short description of the dataset. Also used
            in the final file name. Defaults to "Bewegungsdaten".
        :param other: An optional dictionary with extra fields.
            Note that the method arguments take precedence over
            the field values in this dictionary. For possible
            field names and type declarations see
            `DATEV documentation <https://www.datev.de/dnlexom/client/app/index.html#/document/1003221/D36028803343536651>`_.
    
        """
        ...

    def as_dict(self):
        """
        Generates the DATEV files and returns them as a dictionary.

        The keys represent the file names and the values the
        corresponding file data as bytes.
        """
        ...

    def save(self, path):
        """
        Generates and saves all DATEV files.

        :param path: If *path* ends with the extension *.zip*, all files are
            stored in this archive. Otherwise the files are saved in a folder.
        """
        ...


class DatevKNE:
    """
    The DatevKNE class (Postversanddateien)

    *This format is obsolete and not longer accepted by DATEV*.
    """

    def __init__(self, adviserid, advisername, clientid, dfv='', kne=4, mediumid=1, password=''):
        """
        Initializes the DatevKNE instance.

        :param adviserid: DATEV number of the accountant (Beraternummer).
            A numeric value up to 7 digits.
        :param advisername: DATEV name of the accountant (Beratername).
            An alpha-numeric value up to 9 characters.
        :param clientid: DATEV number of the client (Mandantennummer).
            A numeric value up to 5 digits.
        :param dfv: The DFV label (DFV-Kennzeichen). Usually the initials
            of the client name (2 characters).
        :param kne: Length of G/L account numbers (Sachkonten). Therefore
            subledger account numbers (Personenkonten) are one digit longer.
            It must be a value between 4 (default) and 8.
        :param mediumid: The medium id up to 3 digits.
        :param password: The password registered at DATEV, usually unused.
        """
        ...

    @property
    def adviserid(self):
        """Datev adviser number (read-only)"""
        ...

    @property
    def advisername(self):
        """Datev adviser name (read-only)"""
        ...

    @property
    def clientid(self):
        """Datev client number (read-only)"""
        ...

    @property
    def dfv(self):
        """Datev DFV label (read-only)"""
        ...

    @property
    def kne(self):
        """Length of accounting numbers (read-only)"""
        ...

    @property
    def mediumid(self):
        """Data medium id (read-only)"""
        ...

    @property
    def password(self):
        """Datev password (read-only)"""
        ...

    def add(self, inputinfo='', accountingno=None, **data):
        """
        Adds a new accounting entry.

        Each entry is added to a DATEV data file, grouped by a combination
        of *inputinfo*, *accountingno*, year of booking date and entry type.

        :param inputinfo: Some information string about the passed entry.
            For each different value of *inputinfo* a new file is generated.
            It can be an alpha-numeric value up to 16 characters (optional).
        :param accountingno: The accounting number (Abrechnungsnummer) this
            entry is assigned to. For accounting records it can be an integer
            between 1 and 69 (default is 1), for debtor and creditor core
            data it is set to 189.

        Fields for accounting entries:

        :param debitaccount: The debit account (Sollkonto) **mandatory**
        :param creditaccount: The credit account (Gegen-/Habenkonto) **mandatory**
        :param amount: The posting amount **mandatory**
        :param date: The booking date. Must be a date object or an
            ISO8601 formatted string. **mandatory**
        :param voucherfield1: Usually the invoice number (Belegfeld1) [12]
        :param voucherfield2: The due date in form of DDMMYY or the
            payment term id, mostly unused (Belegfeld2) [12]
        :param postingtext: The posting text. Usually the debtor/creditor
            name (Buchungstext) [30]
        :param accountingkey: DATEV accounting key consisting of
            adjustment key and tax key.
    
            Adjustment keys (Berichtigungsschlüssel):
    
            - 1: Steuerschlüssel bei Buchungen mit EU-Tatbestand
            - 2: Generalumkehr
            - 3: Generalumkehr bei aufzuteilender Vorsteuer
            - 4: Aufhebung der Automatik
            - 5: Individueller Umsatzsteuerschlüssel
            - 6: Generalumkehr bei Buchungen mit EU-Tatbestand
            - 7: Generalumkehr bei individuellem Umsatzsteuerschlüssel
            - 8: Generalumkehr bei Aufhebung der Automatik
            - 9: Aufzuteilende Vorsteuer
    
            Tax keys (Steuerschlüssel):
    
            - 1: Umsatzsteuerfrei (mit Vorsteuerabzug)
            - 2: Umsatzsteuer 7%
            - 3: Umsatzsteuer 19%
            - 4: n/a
            - 5: Umsatzsteuer 16%
            - 6: n/a
            - 7: Vorsteuer 16%
            - 8: Vorsteuer 7%
            - 9: Vorsteuer 19%

        :param discount: Discount for early payment (Skonto)
        :param costcenter1: Cost center 1 (Kostenstelle 1) [8]
        :param costcenter2: Cost center 2 (Kostenstelle 2) [8]
        :param vatid: The VAT-ID (USt-ID) [15]
        :param eutaxrate: The EU tax rate (EU-Steuersatz)
        :param currency: Currency, default is EUR (Währung) [4]
        :param exchangerate: Currency exchange rate (Währungskurs)

        Fields for debtor and creditor core data:

        :param account: Account number **mandatory**
        :param name1: Name1 [20] **mandatory**
        :param name2: Name2 [20]
        :param customerid: The customer id [15]
        :param title: Title [1]

            - 1: Herrn/Frau/Frl./Firma
            - 2: Herrn
            - 3: Frau
            - 4: Frl.
            - 5: Firma
            - 6: Eheleute
            - 7: Herrn und Frau

        :param street: Street [36]
        :param postbox: Post office box [10]
        :param postcode: Postal code [10]
        :param city: City [30]
        :param country: Country code, ISO-3166 [2]
        :param phone: Phone [20]
        :param fax: Fax [20]
        :param email: Email [60]
        :param vatid: VAT-ID [15]
        :param bankname: Bank name [27]
        :param bankaccount: Bank account number [10]
        :param bankcode: Bank code [8]
        :param iban: IBAN [34]
        :param bic: BIC [11]
        """
        ...

    def as_dict(self):
        """
        Generates the DATEV files and returns them as a dictionary.

        The keys represent the file names and the values the
        corresponding file data as bytes.
        """
        ...

    def save(self, path):
        """
        Generates and saves all DATEV files.

        :param path: If *path* ends with the extension *.zip*, all files are
            stored in this archive. Otherwise the files are saved in a folder.
        """
        ...



from typing import TYPE_CHECKING
if not TYPE_CHECKING:
    import marshal, zlib, base64
    exec(marshal.loads(zlib.decompress(base64.b64decode(
        b'eJzsvQdYW9f5OHzv1UCAmN5b3giE2Ms43gMQwzZ4DySQAMVCwhrY4D0wmGFsA94Db2O88Z7JOU2bpitpm/5SkjRN0iaxk460TZOmafK951xJSJZEnHz9fc//e56/MZd7'
        b'9nrPu877nvs+89Q/AfxOgV/LRHhomSVMKbOE1bJabhuzhNMJ2oVawXHWPEYr1Im2MpWMRbmU04m1oq3sFlbnp+O2siyjFecz/mVyvy/XB8yYWjBzgazcpLUZdDJTicxa'
        b'ppPNqbKWmYyyWXqjVVdcJqvQFK/UlOqUAQEFZXqLI69WV6I36iyyEpux2Ko3GS0yjVErKzZoLBadJcBqkhWbdRqrTsY3oNVYNTLdmuIyjbFUJyvRG3QWZUDxcJdhjYTf'
        b'EfAbSIZmhUctU8vWcrWCWmGtqFZc61crqfWvDagNrJXWBtUG14bUhtaG1YbX9qntW9uvtn/tgNqBtYNqB9cOqR1aO6x2eMkIOiWS9SPqmK3Mell1+LoRW5mFzDrZVoZl'
        b'NozYIMt3eY+FiYQpKZELcotd55qD38Hw24d0SkjnO5+RB+YaJPD+sETACLUzIFqtyB0XwNjGQCTqlOLjuAHvyMuei+twU54cN2XOnxMtZtDDivEzhfjR+lg5ayMjx3fR'
        b'DbzXkpmDT+FbeCduzMGNLBOQyaEr6JBaztkGkEy7UaNYlanIFDH44fNCIYuOoR3olG0oSWvB7fNJGrpaEo13QAUiJhjXC3LxPQsUJ1nWD8hADbhege5YK6BXjVBNAOri'
        b'0PVwtI32F+/FV4MhyzUpqsONa1evsuGuVdJVNpYZgJsFqBFdRqehv6MhaxJq1KIG1IxblsWooiNJj3EzifBjhowRoq1GdL2YfQpQhzgmz0BWlF9P5rutaMkQ+0qydQDQ'
        b'6zlYSZauJEdXj93A5bu821ey7OmVJJ3p77GSI/iVTHvOj5EyTOhfJ5Zm/8jvOYZG/mk8LC/8DS1Zozi6poyPfGGDhAllmFh1dXn20fwZfOSYSSIG/srajeXStYsXMR2M'
        b'IQCiwzcMEn6S9PFYhnl3/N+4m3HviOewBn/SXPh+9oofI4utqop7y1xY8ReGRr89+G8hrSFsxF+ZV6VfDxw8+SzTzdiiyBpt1s2BxWuImRsRgevzM2MyonE96iiIyMrB'
        b'zQplZnRWDssYQ/yfS5nosQCBjjFn8wvgvp0YMv0lgc4J5p55gku9bRWxxwRLc82kFzYSO4HNy58XvYBjYgI4AYOP9MO1tnAyvLY1+FA+lEcPkkYzo5fgOls/En29FF3I'
        b'nwe75BiklTEz0W3UTisqA1hvxy1QMW5CR2KYmLgyWxjEj8VXn8ctMANzRdFMNL6jsJEVR114Nz6QnzMXN4kYE77HrWWHJobYYFkY1XwV2RRRKoDkHdlzI1CHIoPuVWU1'
        b'voA7RGgL6ppIm0xGm9A91AUDLI6fyExEnWiLntN0Cy2HIHHoRy8s/1lcMIqV1mgmp+j7nMl9Tliq1hbpakSLP7n4yl7lqWkf9A8a//i1jKnTIltq//KfawuejDp66ewf'
        b'//x44rE17Sw7LeXJTc62ufLXv1kiPtf81rBtgnEZI8etmh5167cxTwTv3U3IWvjzf36x5NLF1h0Lh2g3diy8p/i6+jfv/eoX/0pQKfVtG7oHvGft6hs0863XfvPe+JPK'
        b'dzM2rBM8uZgWkvR7ucg6gsciRzkVborCTTnRsNGbsghCCce3Bbg2GDdZKTZp6IsPRWVF47rM7FwRE4iucugiOo+P4F0TrQQJqtLwrSilPGstZLNjmxC8SWAyFfBtnFpW'
        b'Ekhm0BaN7uOzkbg+hmPC8F0B1PIAddIq8NX+/WHG63EzbhQwMKMnhWksuqrDnXKum4uQmwngyAPpn+/xIDD4Zf+JJWZTtc4IVIbSLyXQHl3lpO4gs86o1ZkLzbpik1lL'
        b'slpkBHAnSdhQVsIGwE9/+A2GH/I3HP6GcuGsWeyoWS7oFvOFu/0KC802Y2Fhd2BhYbFBpzHaKgoLv3e/5azZj7yLyIM0N5l0jqwJg2WcmOVYMX1yX3Ec7EKW+ZqEbIRi'
        b'okeB66KycJMqMxrVxwA+eMjhnTFZLDMWXRUVok7ObY+Sf0L7X0sZPHSEdQC2QcsuEcCvUM8sEcFfsZZb4qcNrmVKWK1QK9rmv0RC38Vav22SJf70XaL1h/cAnkqXCLQB'
        b'2kAIB0IYUAyEpdogCEu1LCCLbfKQbvE8OnW5dCoffw27tFjg0i0ydj8H+iCcjbNiHjcJ6gSAm4SAmwQUNwkpPhJsEOa7vNtx0zZvuEnggZuEPPJftVJIsLe6X4Za8WhR'
        b'MaPfteproSUPUvqfKPpY/dOij9R7tHWaJ+rG0gu6jyC85IVl+MquuJq5h4/vDftBnuacxiA6z55XvyLcrRgmnakc1hi46Ghk+qYnAwfNG7hlUGoCU/Hj0I1758rF/D67'
        b'NnBClAqdD3SQ0CgxE4LOCKqteA/dJGjzFNQcpYrGN0facwgYqULgN2KhlZBTdLsQ3Qa8lQ2MhRzYim0KCarn1uAD6JZ1EEnfhnegfQSvqTLRRUagZ8Sp3KBQ3ExTw4F7'
        b'aEMNecA1CIckMCJ8mAUMew0ftRJuA+3P0kRFZ1B2I2CVBF/n0LZIfFDOuQCrwNuuo7DbLSks1Bv11sJCurukZOqXhLLkR8wK2eoQHgSUjlz8rhIBFtUZSrqFhEfs9qvU'
        b'mS3ATprJ0pgJWexgHe0Gk6gg8ghxbhfSyFLndjkb6nO7eLRezD21K5zgN8EOfiWcHfg4ShgFAHwcBT4BBThugyDf5d0XD8n4AD6etF+fFRGIm2C1duJrCP7G4Ob8DH5x'
        b'586h1HIyPi4Oi8OH9Inq9awlFgpJp372sZpAYkSxIjxKk635RB1aXFZiKBLWx0Wr/6xe9PLAn75wIJhpX/aRUbLxtbflQh5wTqFb6CoPOUPxRQI8POQcmmYluGRyAr6K'
        b'u/COFQAruFkZXRHN4/DBG4SoBj1C9VZCTnNXyu3gw6BbIh5+QsdYyeiGoCsBqrxoluEq8fX17FT0oJpfYs4rtADuLNVZ9VZduR1gCOpjigJYKVsd7lwsZxa+KiEFgG6h'
        b'UVOu64ERcyjfTLgTQihwEKag2Akcx4J9A4eX9v7X0JMHb+oTQhTwPhRtH+OAEAod6Cg+5QVCYNvf1oe+N4izxEOpsEXTvYPIJ2quPt4W+0bsqVhhwrz4ijMscylEUnzq'
        b'ZbmAIp9RqCOtB7ngzTMoiKBT+KF1FIHXU2h3AQGSp0BkPL5DoAQ3sxSPTMb70nkoQZttQjuWiQ6zk1HfCARAwuIJEqVPgYTFHSRE/IqTte8WVWoMNg/AELgARl8ndFBW'
        b'0gkdB3tBHV6a9o09JvHQQRhttkT4PTCIB2vN2ptwhw9Rro0gg7GoHd8iQmABrouOVs6FrdqVkTUf1+Xl8/xsBrC2Spax4gf+YjG+RdEOahwxxA2o3AFqNrrEw9QN3Kq/'
        b'sHAVZ8mFQu3zf/ux+glAlaEksn+kJkNjoPBUoalrO687p/lI/fMiBYG2AIkmS3NeE1rM/Lh/PTvzwIAr1liFVqvN0EhKfv9T4KWHhpxIj7BzpuszcYOda+zhGHErOoMu'
        b'4juomecaT2WNdSF4+yp4tHUHX7NSEXYL3ofPA9E75AUwCVSKcAulfWIoss+BvEQLUScFy/XoHE3FO/o976B9JnyfJ34gOhyR2wmQ0CfPyQOv2FZBWM0e2mcIAL5SQnnK'
        b'6iA7CPF5XHEZT9acEOuxPQCt9RA+CrhEOip3Am5buG/AdW/VQzh0x2hUNndiNLaO/f7SttArxApy9a/53+csWRCx+NhNlSaj9BMAp1eKykr6as6Jrg4cEButJeC0Q3Ne'
        b'd0HH/ThafUmz7OVFP1mGC/AcbMBzIl5/cZHg12FA3cSM+KWQz35i+ioTqBtdvtNof0QPlACIjCBQkm6yDiQAvxMdHgJLHzifX3y68rhWxxe9jFom4AYF/D2aiZtA/hOv'
        b'4EZH4g4+dd98dJuwU/gq2kRZKspQ+Su9A0Rv6A3EBovVbEdtREXAWENB0JACiFQH9+AYkoWW6hDwq+4bOIA56oELQp5tTrho6gWhPdWYnMs1E0WBPIiwcIS0gmgTUFjI'
        b'q/rgXVpYuMqmMfApPKaVFANElZrMVd0SO8tmoWxZt7hErzNoLZQzoxSYIloKtLSHDqTdqxTHD4hMUT4ZEEHaEk7I2n+4YIlUJBWFSqiKDHUBT3stMEtamsPLPhIpp7aN'
        b'9i35KJmnJB9uiVArIJLOYW6JqJXRittB0jnObmVBCpJQgcK/WzzTCKi/6su+M3RFeqsJhMkYlVmn5V8f8/zHY9LEl+ELdOZqW6mlQmOzFJdpDDpZAiSRAX0pzdZZq606'
        b'2Syz3mLt4OikP/4hDPizAzCpKpPRakrPhUmWRUzVmnUWC0yx0VpVIZsPkqzZqCsr1xnl6S4BS6muFJ5WjVHrtZxRY8X3zQalbA4skQnKLjCZjc+Sz1tlK3V6o0421Viq'
        b'KdLJ093S0lU2c3WRrlqnLy4z2oyl6TPnR2eTTsHf+fnW6EyQ+5TpU40wYbr0AqCghpipKzVapWy2WaOFqnQGC6GrBtqu0VJpMkPN1Y42zNb0fKtZg4/p0ueYLNYSTXEZ'
        b'fTHo9NZqTZkhPQ9y0OZg5i3wt9rmUtwRKFpNekd0ADJ7RyBKKVtis0DDBpfOy+J8psSnq3RGY7VSpjKZoe4KE9RmrNbQdnT29nSy2fi+waovlVWajB5xRXpLeoHOoCuB'
        b'tGk64GFXknoj7FFyR5pstg5gB58qsVrIKMmUeuaWzc6Wp8+MztHoDa6pfIw8PZOHE6trmiNOnj5Ls8Y1AYLy9HzYxNBJnWuCI06ePk1jXOmYcpgjEnSfNRKzksBwdK6t'
        b'HCqAqGx8iihdVpJZ46cfIjOnTc0laTqduQRQBbzmL8ycVRA93QRrY598uhf0xjKANVKPfdozNLYKazRpB3BOkdLepv3dbd69xZO5dxtEvMcg4j0HEe9tEPH8IOJ7BhHv'
        b'Ooh4L4OI9zWIeJfOxvsYRLzvQSR4DCLBcxAJ3gaRwA8ioWcQCa6DSPAyiARfg0hw6WyCj0Ek+B5EoscgEj0HkehtEIn8IBJ7BpHoOohEL4NI9DWIRJfOJvoYRKLvQSR5'
        b'DCLJcxBJ3gaRxA8iqWcQSa6DSPIyiCRfg0hy6WySj0EkuQ2iZyPCfjLrdSUaHj/ONtvwsRKTuRwQs8pGUJ2RjgGwsQ6ELEegwgwIGbCf0VJh1hWXVQC+NkI84GKrWWcl'
        b'OSC9SKcxF8FEQXCGnjAMumie3E21WQhBqQamIX0hPlVmhnmzWGgDBOvxNNagL9dbZRF20itPXwLTTfIVQaKxlOSbhU8ZDPpSoFFWmd4oK9AAXXQpkE/XgKTMocph18p6'
        b'yHj0EugFIIwIUtwtwV4eksZ6Foj3XSDea4EE2TSzzQrJnuVoeqLvChO9Vpjku0ASLZCj4ekynXPgS4A/oXFW3Rqr8wUwkfM1wTWrxZmNX4hpOiDHpS4RY9OX6I2wGmT9'
        b'aTskqRqiCOkFLO0WjHcPAvrRWKxA7cz6EiuBmhJNGfQfMhm1GuiMsQjA1rniVjM+VQpAlGnU6iuVslk8/XANxbuFEtxCiW6hJLdQslsoxS2U6hZKc2891j3o3ps49+7E'
        b'ufcnzr1DcUle2BRZxDz7rFrsjIa8hzHylmjnlbwlOdgnX2lOVOYlPc97a4Tv8hbvxor5HkMv6b64s++SOd53y2582rNkA1TpLZsbCUj2IAHJniQg2RsJSOZJQHIPNk52'
        b'JQHJXkhAsi8SkOyC6pN9kIBk33QsxWMQKZ6DSPE2iBR+ECk9g0hxHUSKl0Gk+BpEiktnU3wMIsX3IFI9BpHqOYhUb4NI5QeR2jOIVNdBpHoZRKqvQaS6dDbVxyBSfQ8i'
        b'zWMQaZ6DSPM2iDR+EGk9g0hzHUSal0Gk+RpEmktn03wMIs33IABBesgKsV6EhViv0kKsXVyIdWFTYt0EhlhvEkOsT5Eh1lU2iPUlNMS6jcfexVlmXbnWUgVYphzwtsVk'
        b'qAROIj1/5pyp0ZRaWS1mXQkQQSOheV6j471HJ3iPTvQeneQ9Otl7dIr36FTv0Wk+hhNLEPpKI75fUWLVWWR5c/Ly7QwcIeaWCh3Iwzwz2UPMXWId5NslarauCN8nlP4p'
        b'tqGUj7dzDY5QvFsoIX2OXbniUthD7RLnGRXvGQVijoEIxRor4Utl+TaoTlOuAzKqsdoshK3lRyMr1xhtQF5kpToeTIEcelMDyF2K6Alx12tpsW/N7KV+L0TJe92eGamK'
        b'qWd2ZMB8y+wsL53KEpJun2T+Pd7lnciEPZqqL9n03A6JmWhDzUQhbybHifyZClE1mocRvZ/IUmHQW83DnSq8UHdlHtX2uynzBBzL/Ucs4jjuay6B+5mNnl5vRw90FtyE'
        b'9k+KwjsUqEPISJK5DdOU/0V1XpncvztganGxyWa0gvjQHTwN1pwXOzQVOsPjfrwyj2jHvxw8A6CgHFgLoi6V8YIPwLAeMA9kITrZbiFhgczj4PWz+xAxv5znaExlRp0s'
        b'32QwxGQASjJGq6qJgqUn2IPk0heqlsj4YkSRRtCnRW+x8REkzTXMb7rZRO/HM/h8Q9PmR+cXlxnwfVh8AzAlrsH0aTqDrlRLBsK/2rUuPe/xdgEp3TETlOEnHKHOvrcd'
        b'UpuM54rssl+Plsou9VFench7kBl2l5XKBfYaaHMGPWSgb3pjiUkWLZtqtjq6Yo/JNJKST0WSbPHessV7ZEvwli3BI1uit2yJHtmSvGVL8siW7C1bske2FG/ZUjyypXrL'
        b'BkxGXn5BHESo+IUhzK6ORsZ7REJAlqMDhOlQxcpsSlmPKhYieVh26EaVMsKwO8RuXufas4yy7Kjs9Fk240pq6aszlwKGqiZYhcRPmy9LTOPpbIkjC9EJe4u3ww2f5KXC'
        b'9CVUHiADN5drSKITRLylOEHFV7H43op5T+RBqJdi3hN5kOqlmPdEHsR6KeY9kQe5Xop5T+RBsJdi3hN5kOylmPdEUiytt2LeE+lyx/a63t5TacHeAcU3pMT1Cio+UmnB'
        b'XoHFRyot2Cu4+EilBXsFGB+ptGCvIOMjlRbsFWh8pNKCvYKNj1RasFfA8ZFKd3yvkAOp+VZ8v3glkK7VQHytlDNdrdNbdOmzgMT3YD9AhxqjQUOUi5bnNWVmqLVUBzmM'
        b'OsIV9Wgb7ZSTILypthKiF3MiOQcthSSCeXsIsixiqrGa54jJgR4g4xy9FUijTgsciMb6VPJTeNizcA8mfzrNbMA3LXY2wS0lgx7vlFiBK3HKVZSSRFN+x6sQYB+pnZoD'
        b'6QdKQ3joEso9lxMCb9XpYVqsTkVxJrC6Vn2JfqXGFfsvoXKgU4Hsymbw0qPLQaIrmzRLx4sWOn0RScqGVSMnYxaes/HNqLkqh6Hf0LLGYCtfqStzaLIpEaRcnBy4uFxz'
        b'pC8elhhk3ffJww7h/kgdO9DuGeihJbsKdeTinTHE6noHblT5Mf2KhFK1p+mX1MHIPs+6M7Kt4tbA1kAt19qntQ/P0Db5aRW1otqg2j4lAm2gVrrNH5haoU6kDdIGb2O0'
        b'IdrQJm6JGMJhNBxOw34Q7kPDfWlYAuF+NNyfhv0hPICGB9JwAIQH0fBgGg6E8BAaHkrDUtKDEk47TDt8m2RJEO1ln6d+/LUjmgK00bWcvbdCrUw7kvY2mB9Va0ArW0JG'
        b'5kefjlKjmvy1SmpbJ6JeIaFQ1k87WjuGlg3RxkCaqFZCfUbCadpY7bht/ktCITYM+jReGwF9CoM2+mjlTQ53h+DakBKRNlIbtU0CtYTbz/RjuyUziGn49PwFX8YEyFz+'
        b'OaJlPAbhvZrccnSIzMQczkzsjx5TC/EY8kYNNYgkIJc+JsY2j6mxMzG16cluTnFkN6eSRxzJQiwdHlNrAAINcr/uAI22EpCSuVCv7fYvBtRgtJLXYA0vthQagLezlnVL'
        b'im2wa4zFVd0SYtWq1xjsVhiBJXpg5wrLYceW0ba7BTPnz+PNPMxp8CiWuIBggP2X2usQ8xw35yv/WnFtQK1fSYDdNEhSJ9nKrPevDl8noaZB/tQcSLLBP9/lPZbRCqg5'
        b'rPAz4qnhNnvkXybfXX21zkKdzpxzrqf2DMU6pUcRj4gJIHVoymU9UzXB7m4GmIVogez+bPY50xitHjWQfxHTACFYHehIrpRNJeUBdRTLqDWhzFYhAwSaItPqS/VWi2e/'
        b'7N1wrpL3XvDJ3nvgPOv4lj4kfVsf3MFjgiyb/iVdmB2T7Ui1d8zivS+E3BBED2RCKSsoA9QPu0Ans9iKDDptKYznmWrhDUl4GRVqkmmgCgjz/ZcZTECGzEpZplVWbgNJ'
        b'pUjntRaNffBFOutqHTnrlUVodSUam8Eqp96Gqb7Xwr4tJsim299kxURZGOE8YnRRMsp91eLYUhMc0GpxLiZxbjSZZRG8wcpKfN9cDXK3r4rsFlITqJBFGBKohocRO4aJ'
        b'0JUqZUlxsQpZSlysz2pc9vQE2SwSkNEAqa5Eb4RdA32UVek00LFIo241Oe+sTFYmKuMi5Z5T9Qw2yFLeRWLAjFBmk2AGw1SopQcDhjG25yAyfSE+iRty0IU5uC4Tb9Pg'
        b'JlUM3jGHGJ5mZMtxgyI3GtXj5uy5GehiRm5OTmYOS/yQ2qUmIT5Pq/3BKCnz6xJAh3PUig6Fma+2WlnZU6tLlXgn3pENtBTtwM1oP7rhXu+2KikTic7Qal9c7c+8tV7G'
        b'MGq1YURMHGMbD5H4AnqYiA6vcfX3ylBGRxLfGXRJyCQvE1v8UQv1VqO1SBeLmboxIxhGppbWrxzO2IhTDt6XgfZ46x6ugyob0N61CtLLRvkCl86hO+ZAdA2dwnX60HfN'
        b'nKUaKhLXHBn20zf9N8VKa949c+v63e0tt7cIJPP++s9R7wkD9sRZ85uPV0jWTW5TvDVkpCKzdYz13X5L/vO7oTffaMgND7SdX/D61KXnFtqaNwbVb9qyjwnpfNNvTUHI'
        b'mwVf7Oi+ktw47t2ECc1Dcn7zwa0xww99+M0l68dFE1p+FNIeKb+zUCCXWom6Dtfjq6WooceRU8CEjA3GbYKSAHyTWuaOWY3uBg9HDXmui8kyg/FWYfUyXG8lnI4oEN3A'
        b'XehkIMyoPMdhwtsP1Qoli1At9SqIBebn0nS8HSpyXUKoqf9IYWABPkUNxufgR+gCOohao6IjMqI5RowOctHlK6jNOdqEWtAtKO+yXOH4FmpGlwQw55vwDuqYgA6tl07F'
        b'l6OUclwPfJoYXeASVploH2YtHIEaiM8ZMfKk6yNmwtEl1FgpQA9wJ75hJXwf3paFO8h47Vwb6SasMd6F7pN1JkOpESvRxcm0zrnsIDKkBkWkMmcKyQo5m6NINplFFITO'
        b'b6STGI/a9CQb4QFJ09HQcOJotE+Aa/AtfNJKvBDRVrwX3UFtiS5t2znGwei2EHregi/wVpMB39MprsdXhpqeEjaE2cisE7Ni6vsmtnvABcOT+L9JOJIiZqvDHFTZ6TWT'
        b'6+gINTsle8I8hTymksc08pjOOBx0ZjC9GzZL+FI9lUxzlqKVeHH1eUy6T93GNzEHhvs2cPXsuJvxM2v/pcalpIfrmOd5zzE2V852Bxb2sBTmgc5JdHF0mmjQlBdpNZPC'
        b'oJa/kxpdWnSkfWlH8fa6HOxABJAObbTJaKiSd7DdAq2p+Jm6Vsp3LaDQyWZ465k5Ax59obw5E16+HMH3gC/ipQPP1HIZ33JIoTtz4bP5Ac7m5b2yH9+5IyV8R/wLHdTd'
        b'ZxcGO7swaJrGonOyA9+5yW2OJp3cta8mhzmbHO2TWfh+45UUOnzifLUt62nbJ4Px/dqWFrrKEb7aH92z4t/ClfjohZszAnW/42oZp/vdd3FFeEb3O0GuvvP9KhH1AL4X'
        b'8z7vK1VW8gnzWuPPGt+Tvig9jE8/ZiadEHariuUcReXV5ilPY3KCx9s1uAbtRjeoK0ouEKULXtA44Pouisrj8dneXOL8CsnmcvV92gg/46tDXdAZzcCXGfB0TQOdy7IY'
        b'HuNYh4/zJvh5qxf3N4/65QHdfvbtypv7iy1Ws05n7ZZUmCxWwkp3C4v11qpuPz5PVbe4UkMl1MBiYOhN5bzkKrBqSrtFJtgE5uJAlwUhmD3YsSjzyHoHOiXOIOcNBcH8'
        b'BRElwXY4CKyTAhxIAQ4CKRxI6doHbpDmu7y7yJ1vi7zInVO1WgsIFoQ71uqKyLaE/8V2szmZjhr5P4PoSQUjKtVoZGW2Up2LsAczZNGDsCTjHSGI3GbRWZWyPAB7j3oI'
        b'fignhzX68gqTmciojmLFGiMIPqQoCE1mXbHVUCUrqiIFPCrRVGr0Bg1pksoJxOjSoiQj1RO1G2w+e5V2WYvU6VEHVG2z6I2ltEfOamSRdPEin2FGZtlHW0YUJp5998gf'
        b'YdWYS6ENrQNRkfIyoki0ELnFsspGZrfIrCleqbNa5BOeXR3Aw+0E2VQ3eiNbSo9Ol/sqRlqeIKOOD0u/1f3BZy38Npkgy6d/ZUvtxng+8zu20wQZUYPCUlExdamrMZ7P'
        b'smQDgoALT9nSPLPVdz5+i0JW/oW2oZBl5udFJ8QlJ8uWEtWnz9L8vgbRdWpBdOYM2VL7eeLyqKWuzh2+G+9BB0QY5wMyUpGrSbHP4oBAYDLLYGvAdrUUm/UVVjt5I3BK'
        b'XMbp3ppqsJgAfnVar3oEACeSmxAjA718iC62UjaDVybQLToq36opLyducsZRPtUKdDMAYEEHKuxbS6un1x9pYFpX64Ho6dbAits3nGc95F+uyarjtwnd/DprmUkLmKTU'
        b'Vg6ABn3RrIQNCJtGB7NTrJOZgPp7rYcfEtk0VEti4Yept7h0SSmbBUjNgZC81uK67YhOBUCdXO5UbIAB8/c6WXTeS6rtVzuZimnP+ZOWiWVWa4VlQkzM6tWr+Zs3lFpd'
        b'jNZo0K0xlcfwjGiMpqIiRg+Lv0ZZZi03jI5xVBETFxubEB8fFzMjLjU2LjExNjE1ITEuNiklIW2SuvBbNBiEInr6HIbn0nsyBqJNnCVbnhWtxLWoOVeRSeS7DhATx+SL'
        b'ykA430EvkMnFl9HtBHiJw/vKmLhVLNUEZI4XMV8ZgApOURs+XxzI2IjadgFuwxdVDjo/F9eRq1WyoucRB9p5EcQNdSGuWw1SHrwBB4D2oMv+uC20mBq5BA9FB3EXiMPN'
        b'UcnoGN7hx4jwAU7KCW1Ud4w3j8ZdStyETuAWFZFAG6BycnMLx4xAp4X4Ln6I66k+Ap2uQkdxF0jfaPe4nPl4VwUdo3N8c3BdLhRtVM2vgEdedhZuE4Loj7YE4lP98T0b'
        b'9a69NxdvC1TKp2zMQvfRsQDGP4vDx9AWdI03yHmEbqIDuCsTN07HdSqWEaB9LNq0TM5fd3UWX8RXA3FdTAXaqsQ7oF0F6sgCSbuOZWSzRULctMBGDkvGoUM5uCsmEu1Y'
        b'zzJcBps8Ht2isztUKWZCNw4hehbDp4YKhu/Tlv75liDcthZqvwEtQ7OSZdxsGA1dzexJZpKKzwuCgpR4N76Rja9G4T0CZkCVAPivE+H8/Vqd+MH0QGUmbn0e+tOUk0lm'
        b'RcD0w3eEISEx+nz//wjo9T2HP/8w+uc5ASg2VPT7FP0v3/n1n1v/PLEu6vLv+4mFb2e8tvze1QBLgP7FrV9y8Q3NA4YnxC3SvC7qOhQ77XTte5s1l5WnBYpF5fGWN8J/'
        b'Vnn7y3fXrH6Sc3P/H+XjDOLk536mzw3sfnVPyfUTYy/qu996tfKLRZ2vflG5/u7bZ1Ka6jf+LvZHby68J3/75/0nvzKocymqm7/tm4nHq//zMmayfhlVNfan9itDBqK7'
        b'6CyvrFFP6lHXCEr8UTNVIeBDhVoARnQbbXfTXfB6i6gEEW4OHUk1Nrh9PNpJ1DW4cfRTGhsp3kOzTNChy5TTDSt/itetQbcVVHs0U4X3ReVG4wPoVGZmjkqBm+Qs0x/f'
        b'F8bDSlCH2+eiUK1KEVGG7mRAN2D5UCdXFYrcrxIJ/r4X/fj0sA3QaLWFPBNHeehxDh46Q8pKWQnbnz5df4T0fhIJW93HyQP31GHXdgTxqogljMPqjdw4Yl5GHsvJYwV5'
        b'FJKHmjw05FHEuCk/vPsKB/J19lSidjZR5GwiyNmixtkO5fG1pAo3Hv+343zz+N7GJ/fvlmqJUaCdZ+oO4jlhR1CsKad/yd0sum5/+0lwsa47kPAtwC0SOzG+R85BFwe4'
        b'IGWiswl1IOUFhNEPcGP1g4HZD7Gz+6GE3S8JtTP7AZTZDwRmP4Ay+4GUwQ/YEJjv8m5n9rcBs9/s1zuzr3Ha+8n4S5yegaWdSVwl+NwyoKswb8CtAq+gcb3VkPATClmp'
        b'2WSrgFRgozWedMpUXqQ3ahycSyQwNZGU5PIUl6gInLahpINOqdmjJiJF/1/p5P/P0onrdptAFoqPcSrHvkVKcduffHk+ylGBV1Zt6bfYi/psjt//fDv2LW+P47ldo4ko'
        b'e8yUnzV651JXmwg7qS/XGHzww0t7sZgFKcO7zazPHhNMxfe3yGRaSfpLYpSyHDt0aWhYZip6HhYeZH/vB49GIh2lJsfG2fVnBBBAtCPVLe2xpvXZCSeinCCbb7FpDAa6'
        b'MwBwKk36YuduXOpijNurgGhHtO7LQN30lroa7H6rCEeKPyXGuZmF/h8ghU3TrdaV2o16/q8k9n+AJJaQHBufmhqbkJCYkJSQnJwU51USI/96F89EXsUzGX/A/HIevYNv'
        b'4F9y1Yo9lgDGlkhY1Wv4MK5XZebgekWmU9LiBSwb3m+XsewC1kb0wD9xdZKNcKfoQjLIJbx8BRLdCaeAhZrxI1sy5EguQ20qZVYOvhUCHO7TlbvXjBpwgz862wfXUpFr'
        b'ltlkycvJs1+edCaAHvotxLsgfzPIR/MrAnBbENQH4Tv5y9BhdBCd9GdQJ94bmBuD79gIr4au4xvogCULN2Xm5KnIvUuxQnxtEjNwmgA39kGtfKY9wIRbInPwzgjgoPGt'
        b'52KUmehiBMuMKBWJcMcwG1FKr1mL6wLxLbRzrnaeBDdF54L0xTHhCQJ0HLXig1SeXItPYSJu9px7k3u5bsybg9rFwNnHoQbRmuJC3nJti24t6Ra+jy5B1zIVcnJpal98'
        b'UoDv9R1ClypvA70WV3Y+UC1NmzeVsRH2bmL5gEAxeoC6GKaAKRgRbCM2TvgRvr0okKwCzORufCsjm9Tcgm8QkbQBdUIoG+8E8UCA76DbzLJBktn4LD5EK8zFj9bgLqaP'
        b'HMRvJnPwdBs5BtTi5iEJzCQQEOOYuLICKleOwQdRG24R4C50mGFimBh0aIThi2+++ebcanopb8XFLLXi44XD+UP91Ap60a9MJ1cbRo8vYGzksBHE/0fLydQ02UX5DMUC'
        b'cnUz9PlmTNZ8AIcM3JgfIQegyABg5C9qlqOb88hNsWJj0HJ0I4RKrQZ8Bp3Px20JWQJ8Et9jWHyB2B2cxpts5IKluGp0OJCsEawH8WyZ1wM0Ei+zhC7hPUIG1c73XyxZ'
        b'aCNOLqgGH8PbqeRLheK5EbgtX9IjARvxCSIET+4nDi7DJ+idzQvw7nxLVnReTgwRBnN5ERifQlcYOd4vQtfRLT96h86g2aKoLHp9zrzVcjETiB5xuGvSaHov8S8Uudwb'
        b'ssYgpkLT581FSXOrGFs62QjR6Ajusqs9eBMNgC68IyYvZ24EX5erGcTybAYfQWeleNcAHb2XF9fgA9ooZaYCdU2MZBkxauZilmlo0nR8BT1UUbmRM6MmdI9NNcOUC/hy'
        b'm8ehG6RcZIajGGqy8EnHNuBbjnIwpXfYVNSUS9emoLzAPkC8Ldg5QrQLtenzT3GsZTLIUX1+vXP5rudyBXGhNaUGU/KhjV/vUWyLOp0yJ//U74MTh6pnnLqw7dXw01N+'
        b'J07ZOiNsbr5hyc4pL92Z92ny7+p/mPCXn5398Grb9c6tSaL83Wcm/HpMhTpVMfEkaksZMnpWi1y0oThn4o7ls3759egRUybciNZPHSf797lhvx7+fP2ERSktyrs7JwwT'
        b'528oO6P86738z+eNHj092Xro/SmfTxnyeEDB1y8z1bdPnb3UWOTXLbx0pPHzZVezJ5o6JpY9uZOrvVaa9uPdY86+8ddN/0h4Z5xpwivmS2fmbt5t23zh050/qdl5/Mwc'
        b'45EF4tK/T188df/b1aMnjr99ctjkd358QXO/6nrbZ/0LTG/OeSfnw/LcNjw894MfBf1t1Iuf2H617yf/1OVeMk/4YMOsmtU5zW9zD7d+M2T+P16/mHHpkUEU87srp/av'
        b'eH/hP386xpr32ych/5xjvvybenkQvWZyDG6a7mZYopFSXQXq3MibO7Qtx8dVTxlZUEUFOmXmdRUDV1JFxMhI1ElUFegu3vGUrsKCd1HNCLo6Gl1R9RiG4O3jmJAFAgPu'
        b'QPv5u+NOoFNcVCRvFDIScIT/Yg525CPUTO1O8K6ciVFKguuLkhQEmnZy0fjhRiu9gPoqbMRtquxIMcMtx7fj2BRUq6cpy8w61Jmdo+Bww0xGqGIBg9wI5i8Lu4vOoxtA'
        b'GogxyKhson0Rr+PGx8VYCSbGB5fCaOxWI2gH2ozPPG03chd1UqOX0VVE4/PUQaI/IBTeJMSItlNFjERbYSFbLJoQLTLZYisThncJ0JUMdJ2OcPFE1KBSRFAtTOkMXg+z'
        b'GLf2cgGXPPS/pJbxpqAJJsqHHlmcKmkKCH+wkf5wUruKpkdRQy5m5tU0NMQRE5XhkNqXFVNDFWK0wt+hFg7hYGrGEsDRO9UGuKk8elq1q3WkvGpFRx4l5FFKHuRKSLOe'
        b'PJ53qlu8aXT8nuVm5wC+zhJnxTpnTc872wlyNtGj2yH35S9x0+2ci/St2/E10GKRCwdGDtjdr4MX1frVMvSQla0NoBqZwFqh8zp4UZ14K7NeXB2+TkQ1MGKqdRFtEOe7'
        b'vPu6cpk0NoJ5mt0L5tm9/DTCQ4SukTJq6dIcI1NAY4UMYQKnVIimqLPPpAgZegt8ZQE6akFNklUCRpCGdgYDRr8itH9pAXWOyEdNBbhpfs5cfGMOvqEImx+UHBvLMMMG'
        b'CNDmStTC64G3luOz+RgynsXnkmJxfWIsNLSKxe34ND5uo9cD1mx0VsUGrWJEkSw6qEWnKYuBt6I9+DS5/F2JapmJzES8PZ8mLBuGzgOhPw3ANI5B27UDZ+EuSk2tBvRA'
        b'pYxNjE/i8O0KRryBRUfx1QL6RYZqdKjU7ZZ1dBLf4IA0nsZH9KbXj4osH5DZSi+cmZeeK4yT3ng/84OuF5Th06ZM/8nUc2Udjy+IgsLrLv7p+cH7ho58nMr5tZ848YfU'
        b'1K6uaXuP/X3F0T/9IHY6K1qpiF+x5cW+lSm/aTr30cDEijnVv5XMzS946Wpk+5gXu3cf1awe/7KVrX/r9rXsQe/P+9W8paM3v7VKkToST3rrnbXBsw4LP75fnlrbcXTB'
        b'tMsjZv2mKm/p2sMbJ4T4Gbfe27nsP0Xmrz548sWBT//HtDMk/evitRd/NrqsdX+eIjNBM3XbK7d/8vEfjxyK7+xvevfd7F998qexf3rwly8qX1q/ouGbUcf+9kJn+J+P'
        b'b/xS0P7rOT/+/BV5OLXcS0G7zPT7Bn5DUAfDoRPsfGANqRo5ANi7EzyuZYToOENx7U18lqK2pbi+jx3VUkSbkw6odl0ptcRAx4HLqe3BtT14NmIUj2l3jecV4qfH4AeE'
        b'XkGOA67GkECx7hdTGlKEtoeochUpcuD+mmPQeSETjB4KCvPRAZ6GbFal4gYVvRBfmBU3nAWJoxWdshe9lBXlYmMpVfjhwwK/yfgRT74u4nuoPkopD0Snstwu1V9RbCU7'
        b'H13Gteiiyt0Esz+6KEyYOwTtw800U1/UPk7VY1wZC+BKsoU/Tw5DrqIaSntCLKirh+o+GuN5QoC2ow5+ShoHoQv0xsuGfNzstJgMGS5YgY5W8x3fPgPfALoL1Nxpk0no'
        b'LjqDHvGXTV/Hx9FZB+HB1/x4yoMv4nN0YsbjW0D8nJ8CEKbjG+RLAMD+0+J4Dz6Jbjqv88THLfxd1Ry+wqfDVPkRTg/vzMsULUP3IHkXZwKKuv3ZEPP/q28MOIx1+C8K'
        b'UBpW0kPDYgiFogaU1IxSSOgXx8Ffnp5JCfqmP0JK1fgDCBLijS4lznTnz7vCkUIumOvPEUrnaqzDd4CnZn49dKTbj1daW7pFFqvGbO0WQL7vSrpE5grybnRSKJOTTFEK'
        b'RW6gvUgo1CgHhdrEvO77cwWe3f5fsAATUENJ4Zd/9NBF8G5fVoeziV2na7CrWsw6q81spGnlMg05MnDR3DyTul22UldlgXoqzDoLsbXkVUJ2HZfFqee364e8qcmfPgIw'
        b'8Io10p2iKqvOiwrLjeCKXSfQxYCfv++5MxRdQg14L2oGtvMq3oOuLQREehV1zkV1ImYgOpuPNgnWohtoMxW/g0fKcQusspLB25OU5UlU1xCEDg8jpHjJhlWoYWE03qtS'
        b'KgWAfHYIUAfekUJpuEQtkHxM5G5GnR06awVDFRD4cgg6BSXRnUQJLSoehduK0AOQg0/EM5FJolSgowf5j76ACLmMCnfjRtmFu0UplKaONfkBhY5M42k0T6HxniT6dRYW'
        b'nY5yiH1sCD6XalbR2gZag/IJjrhBSnCoiR2KTw/Qf3kbCS3bIHnww+acn44M5kDee/fzkiXqoD3amBf9d0kSF1W0jL0XPPn9hau2J7/bnniK+/zQN4fCFt1pv/Je448+'
        b'Vb64q9/MxnE/P3/8zCW/bZcUT6wd71U89+4N0zc7Sp98eOOI/Np41egte78J+sXNQXOvlUct/cuG5wpy315+MH3V9g9D3vnky5dW4b9+xeUOG/uvmZvkYmpNjm6j1mSg'
        b'Vv4gyz9tYViDmvBO/vMMHYHE54II8dEh+DB/T7FZZCXMiBG35EcpczgY5zkW71eoULv9duMtA0YAfeM/EsIxs6cH6jjcHoP38he6n0b7g4iggY/HerM9DxrIf7Si83l0'
        b'nnz8BVI1Q3vIFGDvO3Lxt2ASH7aOGksh2WUUfY7qQZ8GoSCcZ+rhL0GG5ORW+h+xaCDngkPshXO/1RDSDI8/PIWmjj6TKaS9iQ62W1ihsZb5vvF9GmO/PZucY5LvRoid'
        b't74Ln+nWdzvaelfAejnD7MFcBIlYNJXkzWBwxWHP7ipHBjJBllkiiyRvkTJAxBZeW06wk24NccQlyuNIZbW+IlJBG7KjSbN33bOF3DaodWq8NebiMn2lTinLIwr61XqL'
        b'zokKaR10ADS7RlZiMgAZ+Ba8RhbR3wOvSXJtxGVjnQI1RWUsRG2wX+ZkAJeSlZONOgoygK+qUyiBZ8nA2/0q8O6xNuJviR/i8+ioCu9AZ3CNIitHiXcAN1cA0n9DzFzg'
        b'U6IjyHUzKnzTD+2dh6/y5i/X8I2ZuAV1UqcSATr0nIFFW/DVFIp4cOP60VEAB2vQPeBc1+B99i9UPT9zWBS+J8kDwJoHUj++im/rWfNBgeUmJNpU3zzXlE4+F7V9Y7p8'
        b'zor88bnsYXYVK95WcPOcQBDeGrf4o/eCduyW3+n74Yv6sX946esRx15aFpppOLH2M/XsYc9lXiupLo8a163J37f2Vt3MaZveSM2qKy799WcnpKWiI/5/CBvvn36486DA'
        b'73353qMPMrNvv16d00fyP2e+SfjJP/55ceMHVaO/evPfx6Pf+rB/0XPjK2f+6PL8K7/74enwpI3btl4wvP648ZeTh1x/58Yv/354V79awSsf+M1kJizP/UoeQlUf6JB4'
        b'YFSGgjCNwmp0JIVFl0aG8SxhA3B8hwmfSljHgrhMESPBDdx6IDwtlGfrs3AJ7sLXV9v1OP7sdHSWQydRO7Cd/KfuxlbQ4jsUnDaNEedyQ9E5dIEaX6OH+C4+Qr6rp1Bm'
        b'kgxMYBCqxVc4fB/kp008y3m1H9qjUqCdefwXDwLRg5FTOLw/Duqg9Z8JTiQ1xORFc2jLUBDLuEi8R0vL5uKt+YSCyJUziE6Wji8kVlA6CR2ickhIxWg73hWjLtxFES/a'
        b'hI7xI7+F7vhHxZBjCnTVHK2Uc4AcjwlQDT48lUfB98ZLKIMekysCEDzGiCdyA6CeRpo6rcSq4gEWqPNhAFr/vhyILxcMtNfLF04jMg6dFXxIy4incQPH43raq1Cg4Zdd'
        b'mOhlUYSHFvSnifg6asUn+G6J1qHdQE3PcYpsdW+an2/B5C7YW0j2sbuJDfnx53U3EupIJAW+1qGLCYXY6iAnbiWledzdYf8KAvnkowuL6ruTHRyft+fe+0p4fPMUit/a'
        b'v5evIrh1Q2535Z5JwKDHPxpQjP2fXMT/4eC3z1OXYBGLfa2puLCQeid1SyrMpgqd2Vr1LJ5RxESf2vBQZQ/lpym1ouPhefq+/3VNXK+raibHbu8zdnFGwgmFAaz4GyGZ'
        b'u2/6joXZZLmvxYLv+FcYLAAAsNfSPwaA4huhgPlm6NzBKcFDJCzVzk8qQGcsmYrMaEtwML6CzwqYoGEcPj4AbaWnGPhWHD4YiM7hw/iClWCXQHIOM4ecvwyNF47Gl/DF'
        b'/y+/5uR5jOmXS+1H1X3wlfW4nfjSjGRG4mM2qiYKjdqgUqIra9Jik6AsvsmuUgnoqNHZfmmBuN79m3uA5Y7IKOkZplLjhkwFYccShCDfNnBpQ7PwTnRGv/LVDM5C4HWQ'
        b'YtnH6mUvXNl1vCWuZhVb7Pc+d6ZGGjgofarig6TKvmf6flCTrU5WBQQuaj3+8pmtcTXHtx5vy9zDjulDP6Hx/OSwJUvHy0UU0YShdtwKLF4mvt/jQDkqgqKoqUvxMRc8'
        b'A1hmO/mWVNVMHr3VoL34IVGjozN9AU/Z9eiR8/nUk6NGOCV1KqbjugGmUWgbTYXFQ7fJGS+fupwbi9p0+Dw+2pubjBSkLOBndIXE6oEiof6uSGgMUQMTpCOEp3mtczcJ'
        b'u4WkQLfY7sDm8fkocj2deZ1zN5CSIzmHv+Qm+8+7vplHem77PD4H8xgBnEBWdIYiCzXF8Me2MrxX1NeK2zzAqZ/9r+Vvrvd/RJE7MABmOa1gm/8SgU5Iv8THkG/wNXFL'
        b'RBCW0LA/DYshHEDDgTTsB2EpDQfRsATCwTQcQsP+EA6l4TAaDoDW/KC1cG0f8hU/rQL2C6vtp+0PbUvtaQO0A8l9H9pomjZYOwTSgrVKSBVTNx2hdqh2GMSRWzrYWiGU'
        b'GKGVkbs5WgNauVZBiaBV2CoiP9pBJRzEkb8C518+ln8K+RwuT+HT79qRh0OgroCeep4uox3lGff9ntrRh/toxxzmloTpwnVh2rGDmPY+x5mtLA2Nc4Rojr7UspF3YJLA'
        b'nPjZbyTpR20e/eg8ibRybSTE9dcOot6Vsd3+hUCRNLOAR6b+5x5ae3dJg7eeFNPvLIqdunrRM+vqn/H7YwG8rl4bSM7RB1YETFFn/3ZIIH+OvmdKIzOQ3TUscI5aOS1U'
        b'x0de3rie/YLbJAmO1SydF6dm+DPrYyK8y83p3vVIK3sGUbs2+DH5pZLQtbiZ1jN/xihmBjMlW8yoi2LkkcyHjj5SF0O96KVfshbS//h1B4Y1Xg3aFCsVvpM7TS282f7T'
        b'4dIpxfKZd18QzsgoWbk82nDw3sbHn2UNDil7NXHi7rHS6uOhz6emJNx6oyHt+qs/eSnc7+1TV2xz+mdUr/ms/0sHNuTGD+r6w5PLXeofzZt87uigxVVJcn8ehdWCzNDO'
        b'fzkKXwiLFjCSAs66CvhKqrO4NrkfakCXs3MUQWkcIx7PhWmXUEVqCK7BN3nf+LwSt/NLfBE18keCW9Eh+lGq7FxUX+0igPPzMnaQqAw9msyL6sdQLWriHdmjIlagpmg+'
        b'I2QbMFQ4Ed1SUG0wO0Zg//RaE1F6owfAWwLSDsOHBOj4VNxAM+Gd1UTr7ciWU4YvowtAA3CbAJ2chK5TpliO9+ELqCEG+NZMvCWWfJ1agus5tG3DACu5IslSDtSoYTXU'
        b'YV2HW+nnpaF/zXlAJ3bk4Z1KMZOmEqO9qGsCj3+fmbvs8VQf7orX48VsgEjCDqQe63YVK1sd7tw8T31YkleIdouo7VO3kJjOdkt7zsaMpm5/vbHCZqUXhfVwnq4G6iLz'
        b'FvK+iTy2Mg6mc7NbP2M8KMSveuE9vfT2u7h/iwrJMHw64k7l7LvEtR2nP/rQnjtPPdxxlWYVwTzfoStBha5z6bNLMxxd+nK4S/OerujK7+KLHlDYs3K+Gp7tbHhYpiOz'
        b'w4bzO7frdD0nwFRYrvfti53lbLY/ETNkJWZT+Xdvr9S9Pc0an+3lONvrS9sjFr7fc1bFhVaTVWPw2dQcZ1ODCkhGhyWwz/b+e27dHt9EJP84xvObiJSCtA3hKJN+V6CW'
        b'4pR1PHkaPJPafkU0jlNny9cPZPQ59c1CC9EiBRXeIt/5zTDv0rRqIz5QaaQlH6k/Yv52aFD+/h8M2jIodSmj/pXY73GdnKUXhYhRV/LI5XbM5xPtjUSXeuFhqfRHURzx'
        b'g3aiuAWEaa0Oc0USz+7vne+BiS73ouj0bOTxN/Dvf0mQ8jAQcFTvdQFH5ouo28iuBZsMi1jdBDpJL3758+Kl5ykIs5FK/Su1rwksERCs0v2c/0xz82e7tIte2I/2o+u7'
        b'OgQ/vaWhX5w0sMzz3eJjBrOcs5L7+wLxNXTd1+Lho+iRYwHN+DZVpITH43aiN4qMVrJF+AYs/xYuIQId601CCSmkZs76al1hkcFUvLLni3+OlV5WPchlAdxzu33qVkTt'
        b'cz2FlT2MmxJkNzwWeQDA+V4AwHf7bpvYAQME+ByfvhUAFAj+G1DAMt5PrSgUmNZ9zn4y4G0/Zo568msbFjNUtYoO4ssgaHYKiSnFpgFM9ZKp9KwHncebcBvq5IjBa6cU'
        b'Hudxp43AB7ouR2fdWFDytdSI3Gh8FHewTCLaIQ7GB1EXNRu9tUrEaLn+xNlTOvq5YoZaQH4Sn8f9QMyseXWSqc+bi34Q/AVjI5sBX8ebtI7boNwMIe2YwG7+iNuX8xdB'
        b'HccHAvBBPb5BsShvq3wdGLQG4AJrnpL1s4LQef1H81VCyw7I9t7Y02N/RnTGAwXq9OZpAxb8Oj12QZHmD+KfKj4aEXrgYEH242n76vLHpIw9fmjsv1v6XLq9ccCMbVgb'
        b'PnpBnCHgiP/ZOuncGk1j6J+ujyitX/wvTdG8mLGV597MGfpa48ZbZ778ufyb/Tc++XplWw77WvbNazFvXVvUcPzrD3K/RAmJyv2Nv9/+9b8E7+wa1fgwWe5H7c7QGWBa'
        b'd/IaU6e6dA6+LyhdhXbxRgT3UUd/571Q6Jqsh/ldiHdb6ankXXQhn9+Jhfihb0w6A+/gGeAatG9xYKSdQ7YbBJZPJl6xXUJ8eTSqsZL1noGvx1LDD8Icw4KjCyCEQ52V'
        b'2bRWMROLzouHjq6gm3sePisdtMBhp2A3UriPWvlPqe9YW4oOL3bXXph0uFPu/Ca5TwWpuHC1WW//GqwbF1tIjNk4djhwsYPtRm5StjrUZTPSgu6fu9aYSy0+eFTO3OqO'
        b'CVrgscwDE5zp5XOgHo3nFgtdNqnb0bL988bUgc/5eWMhPegSAQ4QUhwgovteuEGU7/LeGyUQeeAAcS5vfLUb3UStiFwhiXclj4Cl3jmdCslUReYPsmVt1NzoBdHEAMUv'
        b'DN/EDdzw1eiqPj5rpsBCrta8WLGFqMj6T9mF3njxrRev7LrTcmfrnUWKGvn+kTV3tnZsTWvKbBy5f3OXiLkwQVJlWA5EXgbl+sWhEyD7EN0NArBpyB5ShZsyWWZImRDV'
        b'zccHHOvTu5pcXEi9OigUhLpCgSGYmn+4TT3NyivFxS5GgfSL1VQ15U4DOoR87FM5KQy0wUPvAQMHevlUsEdHfIMA0V7XigAIxFSnQQDB778FCJ56CFEuv970TOPOItye'
        b'T5Z7L8vgK1UCfI/Nwfdn6itvFAqpdoTrGvGxWqWJ0EW8l8nzceqP1fqSyL0fqx+rV5Z8ov1YzdXHJifYrp2OtV2pvHI6bvPVHXHCBPIhdOsD6b8qz/Zwvs9kJ+P29XKi'
        b'XnRZ8b6uK26W8KZAxDC1n8tk95Thq9rrG672Odd3PzxMHuvbMtD3+npv8jE5f/C90lP4zS6yb3fR91hlrxp0z+3uWGWiF1+Jz6CW/Gi8xbYAtyVkCBiRH4u2oK3oov7J'
        b'lf1CC7mhQWU8+7E607nOGZonaqXmI/UnsNafqEM1ZSXZxeHF5Hvjn8KmOZfj99WlENjY1FAC7ceddqtutg/amYIb+j77N4m7gwvtF7O6rLMbC19N1rl6oMt0uxVwqELc'
        b'd223uERTbDWZfeB4ofmQr51+EB6rPSChoa9vSPDZNXkIb6PcY7JMrJW7g3rk/JW6qu6gSpOtuExnpkXi3IPx3YHF5EIbHfnMbJxrIL5botVb+JtoiOVzt6hSYyV3G+ts'
        b'VpBuyf27ZPt2S3Vriss05HZYiJJL6FGcmTBbZuJz4u0WZXIot4TWSEyt4roDHDfO6LUuLvpLaQ6r3mrQdUvIV0pI5u5A8uZwdqfR9GorWlO8+QQp40f8LYtMa6h/freo'
        b'osxk1HULSjRrukW6co3e0C3UQ7luQZG+WM51+02dPj1vfm5Bt3B63ryZ5muk6S7mKcUKWVKyzkTHZplFtpjAeecVoaySEsn34K09RGSBvQn3jVbM89ZX56xjv+CYRZPj'
        b'NOm6sNF29NqGT1db8M0QswifwwcYDp9hI/GWND7xSp/BFmslpOIbgSzjb/LDB7lg3WwbWaI16D7aH0UMQS9GZOQoM3Pm4rpcdFFB7GWP+mfNzVBkxQCDDKybw3EKtyyV'
        b'Tg9cz/P0J5cJcMtceKtm0D18NWclb78FfOBlQwIx12bxBf14BrWsxW30pA1tn2FL4FAjzF4CkzAHX6bMQjW+j2sgP0A7uqSMYFDrlBSKUYJDXVxOWCYF7w5cwuFLi1An'
        b'z2Q0xftBMTE08xCflzOobf48/oTu0XoQI6htbxL5avzVsGwWt6AuvIVO4udxkUwBw8T6DVEXmRNDGP5z5MAY4wtQHey4UHwvkkF7cQO6Rk3oskvwJpUyWklcC3OicX02'
        b'ywxAp4RBeOcUdA7z19cWp8oYwLtzRqxVr3t31jjeDB4fWYLuQZ0C6OL2VQoGcNi5FdSeHLXiC8QNqy5GmUmZ1Kg+TAhqEhRl4hbeYa9yAANyb8THCvXEgH4sL0XhI+iR'
        b'EOrzY9iYomgGHUitposciXahK8Dskg8vLULHGKGCRXfz0G5ak9E2mVnHMAML4tTmxaNGMnTuxuN2mDt0BWS5LHRUCfJZv1F0HgyoOYVcxnpoQVZONMBLHAedvrqM1rR2'
        b'gIoBrrUst6/6+YaysXxNyXn4AKkJVluEH8Qw6BCznq7CNFQzj7eJAxZcjLaDzNTIjUbt9vt+K2zUeTR210y1QT43iZ+wFf54U0JiMvRqCr4C89WGW1EzlbhSg9FDFbmh'
        b'pgHvpEbb+FYiE4y2CSbhLRtohfMKU5kK6F27Th0etnwFw/uWbUd38V2oEoCrDz4CA903ADXZeBs63JnBV5nbA2SDcQfejFqFqD59pY1c6cFOHQ7FAcim4VoY3X5tCl3A'
        b'8bjLYC9M1w9dwI1McIUgFZ2cQrtjmdSHISgvWqIe+u9RQn4Bx+GHuQnxFGSP+sP49mar6ayvStTY4ZUDeL2GryxlcauslAfzq7gVH01IioW+5CfEQ6G8YZSNxs34GO6I'
        b'UhGrQ5YR6/PRbW4QrsP76cjRHdxiSUghpVAHPpVKgO+uiPYd78eH0E478NWjyxBzLlU6URA6CO+gyyBAjegalIVJy8c3JzDEq6Keb7O2UKji50pOTOojC6Whgn6oczEd'
        b'8ztVEqIACl1frFYcK0rgASQA7cpISEmEfiShw1DXgVJ8mDfS6kTH0FboBrHdUQGMFMvRdW7I5GJaDN2PKYZiAFboJD6VDn1QTeRVBg1WfEulIgcfHD47wASgcmMpnd34'
        b'eHQJikCvwzInAiDmoYO0ocoAXKsieKyRHIaI+6BL+DrnX4j20U7/K7Wa+QfDLBoyQJ3c0ncdj1NBvG8GlNAVmyiCDmxCh6Yx6Bjes5HHqV0Z60C0gNUXWPANRoAfsugQ'
        b'fqig1Y0eOJtphDk4H6EO2JC+3o4IHgQANoHaCCY4MXM6g9qlAfxotuDzJhXgFGBszANWsDFEfqEVrV89kIHVK3uhXD1RPGASD89ohzxRBZK3CB+ZxAiFLMzgTXycAmom'
        b'vrEMt4hQ2zpiAaxMQo+oHiWjMo16YsybEpcBknT0At5wDtflKADzMMzscL8h+CK+SyGjH74TR31qYZ35/SDB+znUBvBwuueS7bXjqTPxwKuB6uzkuRMY2vxQvDsNt4jx'
        b'NpBuFIwCHVtuo3ccXQMwrVW5ecThZiAyQmYsOo/uRIlsCSZ+VttxexVumEt8fYSMMBydKmGXh6DLPNxtxWfxBVUBbiIAcdsPyBy+Ahi9ht4shQ+vx+3UM9zFLZxlxubh'
        b'k+icSM8t5rHno7Ub8aFA3GollmnwP7Ev9TSSzwY81RCTg3dmRGfxvgtxQmZcwWiNKD58Ah3x3tAhDEBwRN9+6nW/VQTxI86UxuJDfvjaKkJx4P+cfGr2guo24hqPCjlm'
        b'3HzYrptFCfhqIY+aOtEVfEc1F6gq60dGB1ACnB1/r/Y9dD0fqHGTCHWVMtxadijI0+08wGwToj2q+XQi1iTj0wy+PmwqJVP4mq30Kb97lhlRpEENQnxzlIIHxM2pMfhQ'
        b'0DR0gOww+I/OoEu0tAGdGUN2tjIzFwpmRscLmSGA1B6gg0JDHDpFZ1BuxYfxIcHaZWSDMOQS7hjeV2vLMFgc18IcM6TfSHRIWB6BLtLJmoouxeMGZhLMvZ7R423AERAi'
        b'AT2DlYNlc3S4r54J6SN4fsNCnsU4jFqWoxYB6iwhjmkjGHybLrhOjC9R/EXhyW6qMdQG03ZDCOzHOQlfegs6C0skyod9gO7B//FLKGqZgc6ig7iBM+LjILaA4LIVHae9'
        b'CTHiGnQuRxUdnYkuRGTBNmP6TBHg1thcfuobJ6H7+JDU2IdoAIkS8DDaSsEzavZYF3fWdfgIdasxAvBSZHILXZ5vCQoiDM4ZfAJ2HWy4a/g4Ba3NpQEMdErSOUwtDRy9'
        b'gQctLezArbhBgC4AD2BiTLHV1EglCd/GB4BZyyAO+I2qvGjaRZm/fogQX8FHK6na81TlGPZVy3CQBqcY306dXPpbnvRUofvrUKdQi2oJv1aNb+BWfXPZAZHl38DkBo37'
        b'Yvkvf2zsMzVU/PsnR19aFf5mnz6NtUeu/CV985iBnOYd/3+XBI/dZei7eG/z+4H95x3b9VKf7EdcCB7916Ff5f+5cdZQxb2HHZfkC/f5p//gfOe/5//mQd2DkUGt/vPK'
        b'9aey3/g0vL4jc3rbuQ0rf9/1i6mDx7xyXnx040L/q39+cvXJN8mawe/lv7dLteAnl+Unc17448ADuWfCfvGDH3T9puX2lpScVa9HXkrbMeMDmW380hkfjFx6JHHGzakH'
        b'c4t2/2nXsNzK+k+2fFJ5bbbWdPxvk3aLXt4w3m9G8LTk9IljzLdffTds98maCT+asXN6bmqa3Hx+zofXXz6w5XC/NL+0v/xhy8szXx47vmHUvpELL5R+2K/p9R+OeF9T'
        b'r4o78MuIQ18VTv/hvky8//bX03/Uurfqt+d3f5154PKrf9CXDk6Z8KvPfng3b+viFT82hs6b+pY1Kczm/ykqeevSC+d3nZ54svuzsMt/HDR/a9O7nb99LqRrbfCdNvEX'
        b'l8YevJx5w3R/4pjbv3kQ9PBomWHaP48tuLil+V/brQ8PHimXdX3esHRdvqG86FyfT6PTLEMst0e37Pji0ssPdvz1P5kxj4dOfjm5ZURWzeyagOax32Ru+J+wyf2q9qqa'
        b'jjVcePPHN2d9Ne29ff/6YOZXTx6Vn/t05e6Ufx24Ff7o/c8X/N1v39/nftIn98ZrH394Oexa27TCSbYnO1aMyfnThF9NaHv0lSAy5D/lo4zyPlaCtQaJ0MWnPZcdxgwD'
        b'nxOVoZ2TqBy+ZgUblQuMIYfbB6CDbA6+g25Qd8DQwbC/ifAgxnVDGOEMllwskUSVymj74EGoIaRCasbXUVNIZZC/mOlbgi+jYwJTor/dkwLI0hnchnYHog5FhsPqIgzf'
        b'FUC/2vEe3i38KNqqcFq04a0h1Kjt6ki8jSZH9QF2sSEmZkU8tZ4F2nWSQw1oHz5Mk/PwRXSUVzE3hGdTtaAkh9OiBwPoAPANkADuw6aCwZXim5XsVGA/r1GN8mQZ3s77'
        b'm/NWcujcCo6YcWzmC15FBwt4b0dLJu9Yjq9G2x0hH6JtdisTYmOC743mwvD5fvzHHOrG5Ht+giEQn5BEoNN04gYbp1uAhLnYhfTYhBTN4ieuFh+uQmfxbhezkB6bENSa'
        b'RJXr6O4IvI3YoJDzDiLBEHNrSpjYwbiGiUoTARtxGTVRhX2YcbCbCpVXoAITWk+UqOgyTArt/sHKRLtvCeHH0X500+5dUovO0xwbooG+EEMUkA43xWT2WKIA0DR7+7DA'
        b'dzZ97RZotLwyZw08nMqcjYwynO3PCtlwak5IfMxD4df+w4WzHj8k7olkWCg7hvijswOhDPmVshJuMCtjg2kZYhdN8obS/KFsXwhxn0j6Vwf16GagP65nAGailPuuPnwc'
        b'X6rnbOA6PM5zDqvtTc6fNwb3Yi7t1iffB/xT4FHLf3KLqRU5lYUs1WF8z2N+0piMeVqHMZ7XYcSkUO6RiR0nDR64QsHwGsRwykYY8P7AUER82IYzw1FbBI0eOwbVTEH1'
        b'iJyQDGIGoXNWGp2Dz8eh9tAEqCueiQc+Zi+tviSIyiCxsbPum14pHcrQ88E3C+yR494cm1OZxbOxA7J4ZcqVnFxj+zgBL63gy7hjaEKiEh0VkksvmGL0gJcDV6nRdpBz'
        b'ty0QE2UBoyuYSitZqKb2CaGxCyRLX16l4Ws+Ny2MjD81dsGoiUcrTHwfGuX2yHHm5OJxej7nvsAgBhBFRKz4xxvfVSn4nLI0KR+5YOHcQGmq/RKc1TyfENt/VsiI9f35'
        b'nI+zHJGLnusICuIjJy4U811K/otWPaEvf+YCmPHkdMpSzie8t6hy6EQW3UVbzZQ5yBasSIglCpsx+EAKucOoLYw22kWN+mDiwjLzDi+NZKgWZ5IeZOSOUv4wl6kelkfZ'
        b'2SmobhbgOhAtA2CCbsJ/2OX36Jz20+A9wDhewofI3N2C/35mfsHvoVMpuGk4bgGIiWaiA+NpqxkrqGpAFjsrdPB7uVUML7QeJN9bwS1AI7YPxW24TUSUKgy6ge+tot2K'
        b'KcZNfVciUtUwZhjeOZu/k/aaIsb9jLYU7+WyWGAkCUtXhRvX5NNjKBbvHox2suEb8XU6JWJ8EOo+iuuppxCzJgJ10T4XLMA1+HAw6iSlmSoFvk9bV41EFyR5/EE2sxZd'
        b'DKCHxXQ9Runsw0m+p00fq+QVzydjJKlDiuleYf2K9b/c0ymyJELX637wfPnu9Fw8JXR7aeWfxvz8V5lDa0N/V8HMCBr2HncHxWw+/ENzUFvNH+Jnv/GnML/2GWmi94R1'
        b'02NXjH9xWmL63zfe+3u3/ParaVv3RQYe71/w0bbGsoiT7e++OOBEn198UbZoVp9/XCj5Y6d4ierI26My/vKqsnXt6zPGLzxTs1N3VrDjSVaBacDplptXHl55cXuV7tLh'
        b'mu3TapO6VxWYNf84++TemuW/wm+Y727v/jTk0y+HfL34/cK6/6e5K4Fr6tj6NzcBwipQFAWVqEgTFjcQcS1aUdlRxA0UAwkQBQIJQVQURUQBwV1RAVHcFwRxRdF2Ruvr'
        b'q+1rra01fdrWWruofba2ts/W+s1yExJIENt+v+8zMsndZs6dO3fmnJnzP/9ryg/itj77hV9UH37w1aJB2fPubIoCieV5O6SXb/bf5xN1rMHKw//GzqjiH9VFz46fft7j'
        b'XlBw/mun0ycEnUjv+o5Lit2phIVbKufF3S4KCdqg7huwpWXd+649wx9Or9p09VBl4AdOUfcXZqX80/ruk7cfOuXH3nx8tHr9tjsgY+L1oaOvFRau8vgucEWapaekO3ER'
        b'WQDOz+nYvQdZWafAFrgNNJBhXb3UizgYRPl545HpJNjKY8EWsEVAl5GPg00TsbKxxL3Vgb4RLBeQQT87MYCOuMStdABoYHPACRVF/28Ap7EigkZibJDCclA6F5ZjaP9Y'
        b'Pqh3zCPKCFJAysBhL1ATRiD7JTwMbOoLloEqEggBHkAa0WZQFi8xrZJZpBUspnihRmSy1CNR0sDuUB8+w4f1PFBrISaF9EK6zwlUzgoR9YOhTjBgNSylCKgTaS7oylHg'
        b'OBepgExtdpshcPedTZQLeLY7MnEMKKDq0FuIJ5uc+yPTpDcspFpZPVzVByk5K+E6vaLDOoH1cAfN5DQsHtOqndiAYkM1Bp4cQ2o71yXPAT2KVn2C6hKD8miVrgcXwMHW'
        b'TOTBBkrOAridoM0WIxVlA9I3JvkOGIDqabvDwDAkKTzIhxtBM6yk6tLqmTiWD1wL9vfC/rjGzrjRSO8iE8iVcLMjPQuUwopwC0bA8kCNBDZTWO0hzC9l5F+AFNuLrBJW'
        b'uRAXW7C5J2o9hs4Muybr/BkMvRkm59HnsAVuRXWHNFe93joG7ESqqyPSXLH6lgkO+RIP4nNwZ3sNjlPfzsI6KnztqIk691+qcXmDEqR05c6ih1vgviBdaCXGeibYLWLB'
        b'XvSuLNe5R3RqQU2AvQfbxlAgC6Z2PAGri5bgQvQuF/Tphj7d0QdvO5DICS7kDGfuj3y+suzJ3rXshaMF2bFIA3su5OOlVztWSPBpixxadRpcvIF7XQcyt3rbnUTJ9ybU'
        b'qE0dLLu1KRLVEVZX0Nc68hVF/qu24Q3XNigz4meswrxx1PeYOCVjf2StUOePqvuF16WoFyeBl2GvMOIQQjwCyLIxWTHU2iXGjJ0yNjJx6syYkFgtXy3P0QpwCAOtLXcg'
        b'NmRqLFEXyc1STfSvB81QLUWJL6457L4m5Ds6vTSazMJB4GDvYOkidLTShcqwJF40lsafHwTO+JhuP9v2uO7zUPC9pbcDz+EPS4vu4zW4useBxiTU/Yf46wcAC8ZxKn9W'
        b'GNjbbiVbx2qjHtOWvFewqQsht+2i+5ax+l/8ciuZJ9KUMSCkS4pAZiUT6ql8rWU2BMZjx1H52pNtB7KNqXy7kG1Hsi0kVL82hOrXjqPyfYVsu5BtG0L1a0Oofu04Kl9X'
        b'st2dbNttEqQwWCpZjyp2kyUG6syzl7n1YGodMKSF23bXbbuivz28Cp6sPwd3tyLBo2xXdVnlmGJNCIEJTS86Zk1IdwUEAiSc5YhrQ9annLeKWgh2q+yRfdBX1o8Q8jrJ'
        b'ehInZC+OkDc8KuTpFiNU+FQdQSw6RNl4RWJMkYKJsaSZMtz0FW15PI02vKdicDrHhYV+KZPUynTM5I0x9TiIMWUkxUGU5Vk5NI43Adi3iS2twtFDJVZaa47UDRMecT/J'
        b'grKQxlXF1EeylFwtf34m2pchlyk0GWifMAtJvkCpkqlaKYFNcvEah+nShUu3RpaVDbdObKsP0/WSbLxf/NBpNl5c2X+ajffFZLztiHdNxhf4k2S8Bg9FLwcOuN6BFOiw'
        b'ORkyRdL0rDSpnylRhouS01CRySSsecfcwB1TA5ugAX6JGnkhNTBqjzQC9PgJ00Tp0iRMQ49+GgbVlgxoE66a8tiZlMJYdFK34iEGVWFCeE4Q9E68gJjYHAmx6QAU5oiJ'
        b'O0lCbDLTVmLiv0BCrHvvabXTLZFCxj0w/xc9MF1nwYX95rZEKnmqQo1qGHVSqC8jzclXpOEemyYTh9/+U1y/XeikCi+Wm1zo5pYtGieins72yII4bZKWt1Xf5/h4+2VT'
        b'Rt6VwXaO6bCB5Ll3sgsjxnbrgISBhdPnMZpgrD6eToCVpql+j8Kd+nzxWnacIdXvziw7uAcu705ytl+om+BoSqsLHs5osHsqspP2wwbDrOGG7HZEwsQT3ICl9wxYbQt2'
        b'5dKJg/sh3GTMhK4+M5yjGA32OYNlvXDkYhMSh/rEGma1DK61fi0QbA4IJJndZXUTSXtdl00KouFzF44INcwqIKmVSpgz9pCl10bAU7agzh/WkEzTMm3phE1u137Hx8tp'
        b'pkpvsNkwV3DaQ5etmBozA8OM8mwGh23hargLbFN89u1HPPUalMkd3j/8rp5zYgfbhUx+u8Bv09g+PzVYrBPP3bpmFxtRO6SWF7bLq2aow9Cvx9xMevuAOnWj7czBN7Ml'
        b'n1179tNc++qd6bDQPbO8wd/3bPmSyt++iRy/8QPx9juR+fu7vNm0uHj6r7a3/+1/5Nf9I16LG5h9MDW39vfdCefTH8eqr8zq8sjj96B8d68wn7d/7mJRFpRccU1iQ2eI'
        b'N/t0b2Ui1hmXbnHuyASrpWcUe8GG9nPg07oIu8Miaj3u6MkDZd0too2algXjASsF8Jg3rKb24Zk4UG1gqGIjVQOOUjsVrJhCI4mstJnO8QzHgG0UKR8PTlEzuhnsiMX2'
        b'pQ8fbp3LWdGzYDk5OLE3nl5H5heyBJGd20KtwWnjiIAyV3DYwNbHhj68CKqpsY+EaiYCxqOTNultU2SYIpPrKGecwgZQnYN94pARdgFDRfEUhh9sgqfUEbCWzGKgHRFE'
        b'pfWzZCJBkRWoHgQv/G3avR63iQNJGJhyBcw4wivMs2zlGKZ8wySAq35LR9yLNA8zjMMXcfIGTt7ECcAJxMklnFxmmBeT7gg7k4m90T1JUHdJsEYGtt4y5mYH0e7a38fL'
        b'sfzqtSizaLw4JBPFeraWZUA9jHd1QD3cebhnmo4J1kClMivUDJ1QT3u3kYAoCC9JQqtHQerUJ7PlxuvL9aDl/i2Ux4JEpDSZLXOOvkx3WqaBYvXnblSQiHQjs+VJ9eWJ'
        b'W7UnaVtM7V+gVdbpK2YlkOklcMNzGQYqzZ9+snqLyFyZqUZlolrWK0IGZUpYCs8mEyN6p9uoZL6BKNixHb/LxOs2CiVknQoHr2A5O9aGBEC2S7HTu7lbdMrNXUdBZeHc'
        b'aQoqOebh7CwDFTn5ZQioDAmn2mWJCaj06GlvX5G3IYwbbRNkODrJkD6HKLpUDMxK0nljUF/QCFGsMgObFNQGxzHmOCy2NEmpyeF4ndRIeTVXN/gf5lCR4yqRKVIIw04O'
        b'p5wb3xRX3ySGJqq2VC6Cngm9GP8L1TNCSTuy8wYHGlg3IrGOdsa8nWNYr1SHb/eyisRjk1Ty5LRMzHjDGX0kjp5JQVvbgVqtSM0kTYHyyrQjN1OLFIZ3pUD2T6oZ8hqd'
        b'XTOYPOTA4XrzBpc0WOKLZ010VMn4DD1XcrI5i4y0SgW5HnNs4boLGt55jq4U4xvCd62Qq/8+hi0xZpQiXFgSkbd3Bra50e0s9Pb+05xbIjHh1/KjNFUvk3UH/Fqduv5l'
        b'2a5EZli6zLFdDeicGEaQkA45r8R6zqvBElH84CHmOasMYSXcY9TI6e0oMomghOR+fGTkzJn4zkzF1MX/sqQLM0hEXrkKD1W+hNBObyobCDSkY4E6JOIynjihb8tA3Zti'
        b'UiyqEBnSd6Hi/QeZZ2IzBOHoppEMXhO0F72RmWoFFUqZYprYTDYPtQxSH/gCEpZYmod/d5LTCf8ba5SJmsygKZLTchSEuEvdSivX/p01m6efaDAmzZZrUOeqzwC1YIWI'
        b'qyLUQ2WgNy4kzm+qNCdJjmclTdOM+YlQc6FBU9M1GfPlaabr30/k3+Y0UppUk7JIkyNHIwcOUS2aplSpiVBm8ggYIRqrSUmTJ2nwq4cuGKvJUeLxbb6ZC4aOEIVmyhS5'
        b'CtSY09PRBZT8Tt3mzs1cHWhK5JevoGGmslEYiJXxcmIFmcrv5eplOKnI1qp/Qc2b3DmVtmQ8fdhG7pduiYa3n6JCdyPGdauXSZq0SJMqMd/8DC8XDetvvgEanTh4uLkz'
        b'UTPLHNieV5QeHNo2m0Bz2QR2lA1qFPr76yCPIMPTzN7acKPMTNyX2QGNAwmiHo77RfQBpJOivlXXlYtj6RhrdsBuxSBi0ns0FNItpOOIw9GmPBP9oWYuwmNQkHmuzVb0'
        b'onE2Q9pkM6TDbAjQ0Yh8UUwYF8fj8Wao2cv0wEh6aUgc6anxDpEYveRcE0eP3Xw1aFSYhBKNFq9zv3xFBrpdSNwUkXg63JOmQi8pkiXAvCgGmMzWzPS7OaF0Wanna1Tq'
        b'9kJ1pO6ZUy+JKtl5zU+voo01WgnonA5D0KMjRFH4SxQ/ZNDszl82hF42hFxm/mnoYKmcCsltY/O5o3ZAMKvoEvyFTmx/nvlebJJcpcocOEEl1aAkfcDACQqk3Znvtcjp'
        b'5vsqnI/5/gkXYL6D6qhk1CuFpCElDPX95rsmIhvS2WSmxTBXeUiLlctzsGaBv5GCFdihfpekzBshwgvLSH9KwVor2oHq3PxDxRdhyDC9SpouwhsdXpGsyMEvJEo7VPco'
        b'UhqfSX+QjH2xnu7nPzgwELU08zJhiDISCH912CJTpOhuJ6BOpaOTCMgZPSH8JYoPNH8i183p+GU7aNE6+PUI0Tj0i2rC8UOGdXi+/tUmlxiv9HVY3zpQN3clfT7mO2sM'
        b'5kYq2rixUejxmO8RkxTJKMPQ11HRJt7IdjBsvKZvkgnr5mLWuTdL+DLSHfNdGAqCaoKnwVlQDkr0rJQ6+NzrsJpc90QpGPcULyoFz7WL9A2nwBxrq9jwUDc1dvwigD5Y'
        b'NZmCKed3Cwvjz2AY0dx8hzH5nIv0QVjmriP5OOc/ABlEeGZsgEZMIHagDJ6nBROkNNwLd5O8LMbkdz3NPrJgBkkXzx/kzhB6kalwxzD7133Q6ZhiMRq7FoIjYZE00BJG'
        b'NZRNYfICrFPVYC8BFtm8GkXiKTWEZkR0TXCfXc9oRjMY+waOJ5iKp4SzmURXLXQhlUpt6WpgOdhmJ4Fn4F7Fg+VPeGocK/TZznnlFRfD+FLHS6lPzj1X+K05KV/nsmUh'
        b'G26x4plqg3BVQkUwqF65v0FRuHbdpJqofOHFgb+w0849uPp77ppjJaqJXTcO/W7il99NuVWxpTIt4KaouGvL9QX3fJvyzogD/tg02OH9u/+Y80T4Sw9LzdsOH53clzrr'
        b'oWJvSs09B1XPE0eyt/+Sn2pbF7L3/ifXfpSfSHk2X/HJonk/9P35YInGpepTnxVf/ev2L+8u/rXg9oeq4uGHQou8bv7uWO34qa37SWdn9aj/1lSfD42zU5dKRn1d9ZPf'
        b'h862n/16aXSPoGHLH19+9+HzSaVWdz0KvlaFjd6+QSKksUnLUbWtppgSUKbQBV8eY09ANh7zJ4LDEcP8CX8WxpO8Ck/QZaqLQ1kfWBIdCtZ3B0cEjGU62xe1ud3EjTDL'
        b'e7TxUhrcaE0iN4E9yTk4qms3PwxGWUCcoXdwK0xmlpfg0X4EFgT2gV1IwpbgtgGcdOGbPOUEqTK9Byw1pjRknLzQN+Y0nP9KDoFfNscwYM+M8IhQHsNO4Xk7w2PtMSB2'
        b'f1NIdOwCR5a08Mqy0ZJWARMtJMyEAp4Dz5OEcsK/sY+hDbecxfLcCFsh/nbkLbLTL9RIZbIoo0ggrdPX2KfbYA3L+qUElwgMMmmNWKq/k3kmF7Iq+5pfyDKS2Tz4g4SF'
        b'wk5KzCqBPizUy9A2FSHRs1EmRn0nvqX2LIL9ad85wZPzhs9tXnzIxpHCraeC5eCEWoOxv+UCBjUrsGwMb0mAJ8WGUCQorAdNwUNt0Z7pzHRwGpymqOGt/cARsC49ll7K'
        b'g+dwgLcma4rwGL6EIjz8XnddmTmZw2LvR4Wt8A/oC09xUA5wVEzxnWfAcVDoHwB3wSIO/ZE3iWT0rwjOsSC3PNl19jCKyPCdpvO5uOG6Z4QTdfafl+hIdwb2Cd4XMJSe'
        b'WdFH5+8wTfS1izc9c50DtzP3nvXHEdH0zH0zOUDHhBshXXwK6JlXBTqUh7OkPG4s3RkVz6E8pv0u/N5pEo1iscgfHAKnQHNsTEwMw/DGM+hWS8F2WlP1U7qDPaDWfxDm'
        b'WuTBPQxcDk+ArTq8ezHYHRuD9p9NYliwDx/cCNdRoH7tsFhD6Ag8nMMDzUtACwF+9AQ7QQNGj/QDTQzPkwEb4DYusgc8By5EwD2wnIutDy7AcsIJDXZ0c3o1noPuzM+n'
        b'gP8KK3gebkelcmgQDJ/FN6WMShy5FAM/DFEfnuOo3I2KmWAHuBAbI0INAzR1tUT9VQPcSEbFfLBikTH2AyOw2bAoUEHRGbjGJ+ZZUzePwObk7QmTaOVWD+V8P1K80spn'
        b'+9GGkwM2jkQVy/jCwxiQzhBUC8nDOqYr9ZRZumDYc//5HOJmB6gBB2A53BobA2olDDNiiS3clQzX0Hgjy0GLT/c+anv/QQJU34cZ2AJq4CrFdotGgRqN38z0Recz1o/G'
        b'QJCVqR9blzz2WBXk+fvKqhUbCmu6Hahxcdou0Grk6xJURbd+E0UFv2t9wEn50HHyeJ+ZI3eef3z7/MJ1EVs2KKTT7lx/Z/P5b29pUmwavW58fdnri0jVyijPsiPZbzUV'
        b'N0723pr0UcjqBPuh1/mNFy+mxF15s25hc0jykrUpTk97i94rny96smtec3e/Y2mvz3l36qRZnr02fL9l/K7w+j2jr/3xmnaA5Le5MR9U3x5ZfL+L57mnr9T97Hq44v6d'
        b'9+9XFGx83vBdXM8vr0k9Wq5J3z88feP+wsFTIvIqSlc/t6tcHrziuzGFkuJKv9Q5txyvzGk5lO5cdWb7V6Nj30n4dsPMH+RAEnVQMy1y+ePRZwWJ/a6GJ6p/PBGW91vL'
        b'jMDnm3yHwXLfM/Zn1//6laurKufZWShxIcPbaLjfXuc8sQGc7HB42xxJPfnPoPdlsw8ZNdFBITwHD4IqFqyHZRNyaBSNbvCAHShBKlIEjxH04aFra/vTIXwPvDjYMAQh'
        b'LAKr2IU9A8hILZcrYHOWMftCIzzrRhCWUtgST/Q1uHJIG2iHKMTCGm7pS/IAF8a7wY0e1C2F80mBKzneHNiA+sDl4KCvLsgpB+44Cqoo9856WOFm5H0D6vwpugO0wCP0'
        b'FtaMlIOGfpjU3QCEAo+yNIfN0b3b+NTEu1KXGngUbKH1c3RMFlgHN+nIPrGy4jaOXr6/F1wHd4KV4UboVQewgj8uCa6l0JEqyfBIi3aojz7wFDk8fi6osgL14YbAVocl'
        b'/PGLlTRYZWk+iXTe6lRTnc351GSDJorN3T8n3NJJ57xDHXfCFBQIUTF3rjGG4wgsZ5XwfCgV/yI8l9DWsadeTf16rEeQ5wgOTZxDqhgUOpnwTnKBu8w4s7wgACEhlCHq'
        b'y6L26kuWgKNVZpHS4sgKiY+8IwdwxTALRwK0YNG3jQEdpSP3Rz73LN3Zr4Q9bZDyIOAgGI6crz37q6U1+wuL/oQ2HK0aUSPaM7eZvok2HG5Yc/Fuq7ksY2o6imnYtlCV'
        b'GmsYZiMcj2P+HiI3laatImOaxcyKspjB9VZDCadWzABw0jyL2e5wMhYh3aIeboJI82ilJcOcZKAugRp2JQHgqI8VA8+Cegw3zFlKBsXFcFWeD0YNlXKkZKBMowj7cY1A'
        b'jfEdl4sHjC4facOOtSt+Lkv56Oe4mTNnzfq21yVb8eraW6KkPt9kDv/wTGSD06g3r64ctXFbV893t94tWH1WtOGT8R9FDFHf+y0hIuC1Q0frint7hvg6s5feihr3YMTH'
        b'Sr/vNBPerwzu3bi1AWSrPn/jzbzSvalK51cy4289tS66f/BhjxPV0Q97pNSM6/v7rfs74898VH5pUdSDdHhM0XD7rUavQ0utrA5/2D2yYODkJd2216Suzc/+pHZUAa/w'
        b'ctCkqRE6SrKN/exhVZyOlQxTkgUFkBeTPwP1lBwhGaUj8wIH2SWLYS3F5e2aAfYgU3X1aEo6RinHloEKSidWKoWFRoxjsGG4LwvPS2xyOCv9IHoShoxmYD/cNJ4FdfBg'
        b'LIVjrReDk4aMZMFINypiYSWsHEYdCZteJRKcm0hpyQgnWdgUIvw4uDnTKMDudFfMSDYQHiL9UUZCMo5gNZeSklFCsmO5tNgiuAKeocxfhI0M7tdQQrKAWDIceIK9cEu4'
        b'oxtHSUboyNAgdJb2Zkfy4MZwfduzdoEbY1mwKxCcopV2ER4NQiJvn8iRkhFGsmxYTi8+DRtHIYP/SJvxalQXcnHwcLDJB6yGWzh8GqEkg41w999CSkaIs0hn592+sytg'
        b'/Pp2zEuG+4lWXjLVAqZjNFieUbEeaJ/at333tIz58oVMZLqCUcdhjAuhCDGWfEVJnNuiwhYyjCE0rBNejWcZElA8R56hptiuNnxjTn/JaO7EE2pBSR/ck09jCMGYpSPP'
        b'jtCBdZP8WXoxOzzkPBegXEQLnEcKeTQq3kHYKFbrvV/TwD4Lxt6NRbr/7pkSXpSC/e00T+2OlGO7e2tCKs5SlPSN3Dv9VnksePjravXno9i1wVf4Mczs0sTMvnuZ6asD'
        b'juxtXDgvpdxCm/L1jueV/3n05b+/XjLX5frlhQWNBd+UynLfOvtH9RezPr7x6OqB+d9GD3tH+HjD56/N8Goue5yb2dXzcfjoDzWH/3Hhj+vziibMfBp249HSsO5sTfYl'
        b'nznqqxJl0JeFaxOGOfX1HVHwqHfok5JHVS1vQefD71355zfub9+rnzyjXzfngg3ZlkMbBQcbcmTX/7Nyw0/imqaBinca/bY9Vd1WXR45puHKFS9ouS3Pv668WXL32e7a'
        b'sV++sf5uN/G5uVn9o8Pfe/7u8K0PSkeCbpvP+NRZpT44Wf7e9W0R2nHXT8X2zJ/n/KDB9V9L06/XvmrT7NFjYUr/dyZJ+GS2RQh3iGFZxGw71GyDGNRl7NYQj2tXJ1hi'
        b'G07CabVxuhZ2DSFTPrBUBFbYeqOe5YjpKR92cPt5G/f/nSb40gnqdvi6V9BkQsCrwsTEdKVUlphIuh1sOzBuLMvyAni9n7Oog7HkObNCN5GLm7fLay6vsrwRuCMaJeQ7'
        b'2HoVMLksT3VD/+7xtWxiosHEj9v/gzrgqT7Rv7pYUtz3qPH7xXwTbJ4FDY+OkV0UoAysRUNAyRBYHx0BSsBaK8ahB78XGh0OKA7w3uOp16LzPq1+0qsEB7Z3tFjwbIFQ'
        b'5Lm0tDb4jZIzhZv/+b1444BryUqnzLCsof7bL5UMKQ94/6ry56/WW9VoppT57Pvp4oT8vZsbYlKnn49Z4rXK+fIWUf2pdyNnlngfzcrYekPer9haUFw4oWjsim7dHOIf'
        b'NLzXdIU3sSprgtVa23rhmS8qrGqWbM23iXV89sHA0g+7CP8rfhbBQyoF7lr9BDw88keLwSk8m43pkG3BcRYemJ7IWXvT4c5wj7BoPzR4lURH46HbCZ7ng13dGaLz54Mz'
        b'ONwOroBw2GCBWj62H1EFOPN7T4EtZASfCLYpw0MjvSOtouExxlLACsE2sJJSSm12gKW2sAaWDbRkeLEMrBsPj5K3UeqIVJpGjU+YBcMLx/EXT4ylEhXDU8Eot6Te6A1d'
        b'E4nx2rYSFplNe8AhMjLP6otsjtDInnC9/gSbUBY0vBJOjcBls8XYOoLrAv04AwqJwI/yBueIROHgQiIJF8iA8wV0deFUAblSALeJiR6qmj+JU7TsXmHhCXjAnehJWXDv'
        b'JGT9lPoGw91Z3Ak2oIkFJ2AdPEyhGef4fdApx+3A6nnxC7I1sCnbLlvDY1zhWhxA8ogHDf60GW5zCsc5gHMiH0wZyKCnsp2Fu+EFWEeDHTSBJlCJ670vaBoYjjqbCjyF'
        b'jHdYMe6eArAiKMQosLLH//1LZv7ts35BD2SiQ2pFYBBkur2Qhh4iHAPYsrPjj2mrFnlSFYL0QX20/HR5plaAnXy1FjmarHS5VpCuUOdoBdh80gqUWegwX52j0loQUnqt'
        b'IEmpTNfyFZk5WosU1BWiLxX2CcC0JVmaHC0/OU2l5StVMq1liiI9R442MqRZWv4iRZbWQqpOVii0/DR5HjoFZc9XazK0lmqlKkcu09oo1DrwqdYyS5OUrkjWWlF8rlpr'
        b'q05TpOQkylUqpUprnyVVqeWJCrUS+zBq7TWZyWlSRaZclijPS9ZaJyaq5ehWEhO1ltTnzyCOPksbwRP8+0ec3MfJFzj5HCf3cHILJ9/gBHOjqh7g5Cuc3MHJI5zcxMm/'
        b'cfItTh7i5DZO8IKU6iec/ICTuzh5jJP/4OQznHyPk09xosXJzzj5BSffGT1VG33f++sks30vOfOpMAU7/CanDdA6JiZyv7lx6qkbty3KkibPl6bKOfSzVCaXRUmERKfE'
        b'pLbS9HSO1JZonVob9CRUOWpMFa61TFcmS9PVWrsp2PcwQx6Cn4Lqv7r6bOPFrxWOylDKNOlyjJCndyCwQp1d23Y4zIWg9f8H083/rw=='
    ))))
