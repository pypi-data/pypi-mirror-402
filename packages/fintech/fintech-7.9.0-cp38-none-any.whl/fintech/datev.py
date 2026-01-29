
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
        b'eJzsvQlcU1faOHzvzUKAsIoornEnQMK+u69AWFQQFRcIJEA0BJrFhVo3UJBFVHBfcFdcUdxF7ZzTmbYz3aad9+2UttNpO9OprdNpO29n5nWm7fecc5OQmMS2877f7/t/'
        b'v9/fyE3Ovj3n2c5znvsx88Q/AfxNhT/TRHhomCKmgiliNayGq2eKOK3gqFAjOMYax2qEWlEds1JsUi7htGKNqI7dzGq9tFwdyzIacT7jXSH3evycz8xpBbMKZVXVGote'
        b'K6sul5krtbK5a82V1QbZbJ3BrC2rlNWoy1aqK7RKH5+CSp3JllejLdcZtCZZucVQZtZVG0wytUEjK9OrTSatycdcLSszatVmrYxvQKM2q2XaNWWVakOFVlau02tNSp+y'
        b'EQ7DGgV/I+HPlwxND48GpoFt4BoEDcIGUYO4watB0uDd4NPg2yBt8GvwbwhoCGwIaghuGNAQ0jCwIbRhUMPghrCGIQ1DG4Y1DG8YUT6STonkuZGNTB3znKzWZ93IOmYh'
        b'c5zLZ9bJ6hiWWT9yvWwRTCBMRblckFvmOMcc/A2BvwGkM0I6z/mM3DdXL4HfB8ZzjDCkD/KUZM9crmAsYyAyG10twc14mxHvycuehxtxa54ct2YumKsQMxNmCfGDCXPk'
        b'rGUo5ETH14tMmegIvp+Dt+OWHNzCMj6ZHOqekiTnLKGQA19C+1arMjncGJUpYoRCFnVWo0t84X0peI8qMyoTnx6twNuguIjxx02C3GEyKEzmE7XloOOoGTehjfh6VA30'
        b'qQUq8UE9HLqWVWQZDVmih4RAhqtS1Lj6GQvueUb6jIVlBuE23DFXgFpQM7oAXSWDwj1D0SUIt0WrFBGks9NluI2EvZihY4WoDnXklbFPgOZQ27RpyBryK8j8tDUsH2pd'
        b'O7YRQPg5DtaOta8dR9eOXc9Z167iybUjnQh1WbuR/Nr9Kc2rfCg7mGFkJdKxMWaGRh4XCyZXceRXSXZ3BcdHmtZJRtzhZBBXEhWrnshHjjOJlt9kAmEDlkgLCycwXYze'
        b'B6KfMw4W/lcwM/XLAWvZdwe/5795UDqr94aE5wv3s91eTMz43JK494wfCOQMjd4/++uAjgB28MFFv2e/W/Su95+YPsYSTSZ8F+rFHbBmzdHzphjDw3FTdIYClrKrIDwr'
        b'B7dFKTMVWTksYwjwnoQb0G6Xyfe1jXsmP/nOm4chU1/ua59c7qdPLtkYYpfJleYaSeuWQQT+DlaW5M/HV/ARRSHHcAIGH0Yd6KQFJo3JL1TmQw1jGNzBjkHHvCykmoX4'
        b'BL6ePx/iK1UCZha6iNssAyF+Hm7CLbgdKo5m8Dm8IxofR3sswaQDuC4Ft8PYFczqBAU6D7WTlnEDPoL35ufMRw/m4VYRwz3LDsPNgZYJpFcH0GXURDZDpApq3ZY9Lxx1'
        b'RWXQ7anEXSJ00wdtNq2yhEDe8VDjbtQDw5zIeKHrE/E2tFu3J2yfyHQIUnWaXy17NdYfxUi3qN/NLGroyg/4Wdjg/YsWq6eFSrMvpp323Rlhat7a/l+VY2Wjdr+M5aV/'
        b'X7945R8b80YcfW/Sob0DWmNKp25K//uSaX9k0j8dcpE71/abkfXca+Gz9cdDC7+4Wvwbr5bPX4tYKn/3v64vTe8Kvpi079tTy5ct/tc3Jz95K/q/4zMPr08brH6/4/iW'
        b'xoBHQ77qWZC7RrjhWcFDYcqXLcfkIjNBoWg/TOJ5FW7F3Vwkbs1RZBE8EoxvCXDDeNxopoikO3BpZJYCNy7GpzKzc0WML7rCkaXCd83DCI7AWxMjlfKsSLytFu+meCYA'
        b'bxRUoweo3UzwDL6PLjzji7rC10VlWAA7NEVzTBC+I4Cmu9Fl2oY/7kXHYc7JOrbBp0XACFNZdMULd8m5Pi5cbiQQJPelX//GgwDj49CJ5cbqWq0BiAolV0ogNdpVk/v8'
        b'jFqDRmssNmrLqo0aktUkIxA8WcIGshLWBz6h8OcPH/IdDN+BXDBrFNtqlgv6xHzhPq/iYqPFUFzc51tcXKbXqg2WmuLif7vfctboRX6LyIM0N4V0zp90Dss4McuxPvRJ'
        b'cTXuXI93RmbhVlWmAjVFJ6FeQATbo7NYZhy6Iiqejxuc9if5J7R+myrhoSXMATAGGrZIAH9CHVMkgm+xhivy0vg3MOWsRqgR1XsXSehvscarXlLkTX9LNN7w24enw+UC'
        b'jY/GF8K+EAa0AmGpxg/CUg0LiKJSHtAnnk9nK5fO3sPvYH+WCRy6RYbrZUMdCYyNwENFPD4SNAoAHwkBHwns+EhI8ZFgvdCKjyrd4SOBCz4S8sjeJ13EJGgGUmzdmTqV'
        b'0XW2FbOmPEj5+p+Gz0teKf20ZJemUf1ZSUvFBe2nEC56finu3hG7Zd6hY3uCXshTn1XrRefYcyW/FO7crY0aLp2lHN7iuyh942eDw+YP3hyWEs/UvBy4YU6yXMxviW58'
        b'IiaSksp5qI4AfaSYCUCnBbXoGN5nDoMsqejGHMgRhRspPcVtAkYaJfBa9qyZsBuobTo+pMLN2cA5yMWMBDVxY9D1NRJ8wjyY1F8/KoWgMFUmughYNF+cwoWhreiimWC/'
        b'uBJAs815wBoIGQG6K8KHWHzHL4Gm5Y+ZGanIyCRYQIKvceicHNXjliw55wCUAne7i8Jon6S4WGfQmYuL6S6SknkvCmTJR8wK2doAft2Vtlz87hH1CU1afXmfkLB+fV6r'
        b'tEYTcIlGsi5GQgO7WFu7BPKNfuQRYN8WpJEl9m1xJtBhW7i0V8Y9Afx2KIuzQlk5Z4UxjtI8AcAYZ4cxAYUxbr3AE81jPMCYJRJ+K1EPPuoLqLYZ1rM5GrflZ6DthICT'
        b'NZw3dz4hglPwMXGQb67uq28/Y00xUOjw+rDPSwjAvVQeHRypzlY/KgksqyzXlwqbYhUlX5RkNix6afArz+9nmc6fSZ41D5ML6fqX4i1lDtAxFda+iVtjDDQTXg0Abgfq'
        b'xD3AFAKuVSpqrDh5yPpR+JoQbUlHN2klEVq8xwYnACT44kCAEwZdMhPSh89mlqryFPgYTAm3ip2GN6Jj/HJybiED8GGF1qwza6uswEHQGVPqw0rZ2mD7Mtmz8FUJ6WL3'
        b'CQ3qKm0/PBgD+WaC7dBAASEIHmV2QOj0dwQENy38v49xPEJDBPwOzlL2w8IgfJyAgysoAGd+S7denCWkAHp7abR7YHhUwjXFWWJ+G3MyRjgsOb7mNMtc1EmWL0mXCyh5'
        b'xZtRN+61AcSzaTzCWINO411mQjoK8Xm0sx8g8AV8rB8oACKkGyhymLkMN/IAMRt1U5gAgMh8xkoDPWMFWHuT69pXPLH2Jue1F/FLSxa5T7RKrbe4QIDAAQJC7GBAZrvS'
        b'DgYHAt2Dgb0xzyghiQcDwhiz5cKfgBZcAIG1Vu0MCKJcixJ+r8KXvYiYVoAbFQrlvIysBbgxL5/nOTMAOtqBBVWyjBnf8xYzPhR2tKjxWWdE8gTk7B1IgAe3hesuNpk5'
        b'Uy6U8Tt84fOSzwB69OURoRHqDLWewk2NunH3Oe1Z9aclr5W+QqEq62+x6nPqwDLm5dAmdtb+Qd3mmCiNRpOhlpT/Xs8yiesDbifdBvaRkLFn8JESX9JTnq0zAhdp5ezQ'
        b'YXSGcodoB+pB9x0p1VZ8lQJfm9ksgwxxVUtskDdK7IiMAO5g8J08PduOujIA9J5Bp23oCECvaCAFS3Q8dmA/0To4n9CteiZObiUbQo8cIQ+dYksNYQT7KZbeB7g+CeX4'
        b'av2sEMPnccRKPDGyg6QL/AOC6idXFDKJqFJlh8zdwY6Q6dyOi7TmjJuooGzHTWwj+4PSmYvaQugWJAW5OvWr4zhTFkS8GipQqTMqHgHI/LK0sjxEfVZ0ZfCgGIWGgMw2'
        b'9TntBS33sqLkknrpS4t+tRQXLP0Uz8V6PDf8P362SPCboFeef4djxB8HtM5+z0qTxtewVjBAl6RWnmVNIdrKL/AF3JjvQGzYEj98B11azDM7rfgaPo+bozJxK0hh4uUc'
        b'Opw4Bm3CJ81EfJ+sH9/P6wCnMxz1hq1UuV/3p6Ep4N1NZqMVRRFhnTEHArcvBUio9e/HHCQLLdUl4BfXMwwA59K//KSrFvvytzohpieql3O5RiKgy/0IR0WoH0gUPsXF'
        b'vEINfkuLi5+xqPV8Co8jJWUAOBXVxrV9EisHZaJcUp+4XKfVa0yUUaJEkqJICo20TzZ0+1ThiR8CmZR8MgSCbiWckLV+OH+JVCQVBUqoUqosD232LcSbbOKHRMqVxI/1'
        b'LHwQLOgkfHBFQo2ACBuHuCJRB6MRHwVh4xhbx4IgIqF8l3efeJYBMPjaxyEztaU6czWIcNEqo1bD/3zIcwgPSROPgwu1xlpLhalGbTGVVar1Wlk8JJHxPJZma821Zq1s'
        b'tlFnMndxdM4f/gLG+81+mFNVtcFcnZ4LcywLn6Yxak0mmGGDeW2NbAHIj0aDtrJKa5CnOwRMFdoKeJrVBo3bcga1Gfca9UrZXFihaihbWG00/Jh87ipbqdUZtLJphgp1'
        b'qVae7pSWrrIYa0u1tVpdWaXBYqhIn7VAkU06Bd8L8s2KTBC9lOnTDDBh2vQCIIT66Gkr1RqlbI5RrYGqtHoTIY962q7BtKraCDXX2towmtPzzUY17tSmz602mcvVZZX0'
        b'h16rM9eqK/XpeZCDNgczb4LvWotDcVugdDXpHZG8ZdaOQJRSVmQxQcN6h87LYj2mxKWrtAZDrVKmqjZC3TXVUJuhVk3b0Vrb08rm4F69WVchW1VtcIkr1ZnSC7R6bTmk'
        b'TdcCl7mS1BtujZLb0mRztAA7+GS52URGSabUNbdsTrY8fZYiR63TO6byMfL0TB5OzI5ptjh5+mz1GscECMrT82EPQye1jgm2OHn6dLVhpW3KYY5I0HnWSMxKAsOKXEsV'
        b'VABR2fgkUXWsJLPGTz9EZk6flkvStFpjOWAK+Jm/MHN2gWJGNayNdfLpXtAZKgHWSD3Wac9QW2rMCtIOoJxSpbVN62+neXcXT+beaRBxLoOIcx1EnLtBxPGDiOsfRJzj'
        b'IOLcDCLO0yDiHDob52EQcZ4HEe8yiHjXQcS7G0Q8P4j4/kHEOw4i3s0g4j0NIt6hs/EeBhHveRAJLoNIcB1EgrtBJPCDSOgfRILjIBLcDCLB0yASHDqb4GEQCZ4Hkegy'
        b'iETXQSS6G0QiP4jE/kEkOg4i0c0gEj0NItGhs4keBpHoNIj+jQj7yajTlqt5/DjHaMGd5dXGKkDMKgtBdQY6BsDGWpCObIEaIyBkwH4GU41RW1ZZA/jaAPGAi81GrZnk'
        b'gPRSrdpYChMFwZk6wi9oFTy5m2YxEYJSCzxD+kJ8stII82Yy0QYI1uNprF5XpTPLwq2kV55eBNNN8pVCoqGC5JuNT+r1ugqgUWaZziArUANddCiQT9eApMylKlnHyvrJ'
        b'uKIIegEII5wUd0qwloekca4F4jwXiHNbIF423WgxQ7JrOZqe4LnCBLcVJnoukEgL5Kh5ukznHPgS4E9onFm7xmz/AZjI/jPeMavJno1fiOlaIMcVDhHj0ot0BlgNsv60'
        b'HZJUC1GE9AKWdgrGOQcB/ahNZqB2Rl25mUBNuboS+g+ZDBo1dMZQCmBrX3GzEZ+sACDKNGh0q5Sy2Tz9cAzFOYXinUIJTqFEp1CSUyjZKZTiFEp1bj3GOejcm1jn7sQ6'
        b'9yfWuUOxiW7YFFn4fOusmqyMhryfMXKXaOWV3CXZ2CdPaXZU5iY9z31rhO9yF+/Einkew1PSPXFnPyVznOeWnfi0H5MNUKW7bE4kIMmFBCS5koAkdyQgiScBSf3YOMmR'
        b'BCS5IQFJnkhAkgOqT/JAApI807Fkl0Ekuw4i2d0gkvlBJPcPItlxEMluBpHsaRDJDp1N9jCIZM+DSHEZRIrrIFLcDSKFH0RK/yBSHAeR4mYQKZ4GkeLQ2RQPg0jxPIhU'
        b'l0Gkug4i1d0gUvlBpPYPItVxEKluBpHqaRCpDp1N9TCIVM+DAATpIivEuBEWYtxKCzFWcSHGgU2JcRIYYtxJDDEeRYYYR9kgxpPQEOM0HmsXZxu1VRrTWsAyVYC3TdX6'
        b'VcBJpOfPmjtNQamV2WTUlgMRNBCa5zY6zn10vPvoBPfRie6jk9xHJ7uPTnEfnephODEEoa804N6acrPWJMubm5dvZeAIMTfVaEEe5pnJfmLuEGsj3w5Rc7SluJdQ+ifY'
        b'hgo+3so12EJxTqH49LlW5YpDYRe1S6xrVJxrFIg5eiIUq82EL5XlW6A6dZUWyKjabDERtpYfjaxKbbAAeZFVaHkwBXLoTg0gdyiiI8Rdp6HFfjCzm/rdECX3dbtmpCqm'
        b'/tmRAfMts7K8dCrLSbp1kvnfcQ6/iUzYr6l6zKbndkmM5JTYSPSjRnLGwx+GEJW7cThR+4lMNXqd2TjCrsELdNblEfOP55x0eQKO5b4ViziO+46L5161kKorkvAxE9qF'
        b'unBrJN4WhbqEjCSJW78Wn/pf1OeVy737fKaVlVVbDGaQH/r8p8Oi83KHukarfziQ1+YRJfjjITMBDKqAtyDqUhkv+QAQ6wD1QBaihe0TEh7IOB5+ftMLEQuqeJamutKg'
        b'leVX6/XRGYCTDApVLdGw9Af7sVz6QlWRjC9GNGkEf5p0JgsfQdIcw/yum0MUfzyHzzc0fYEiv6xSj3th9fXAlTgG06dr9doKDRkI/9Oqdun/HWeVkNJtM0E5fsISaq2b'
        b'2ya2yXi2yCr89auprGIfZdaJwAeZYXuZqWBgrYE2p9dBBvpLZyivlilk04xmW1esMZkGUvKJSJItzl22OJds8e6yxbtkS3CXLcElW6K7bIku2ZLcZUtyyZbsLluyS7YU'
        b'd9mAy8jLL4iFCBW/MITb1dLIOJdICMhytIAxbbpYmUUp69fFQiQPyzblqFJGOHab3M0rXfuXUZYdmZ0+22JYSe1ptcYKQFG1BK2Q+OkLZAmpPKEtt2UhSmF38Va44ZPc'
        b'VJheRAUCMnBjlZok2kHEXYodVDwVi3taMfeJPAg9pZj7RB6knlLMfSIPYk8p5j6RB7mnFHOfyIPgU4q5T+RB8inF3CeSYqlPK+Y+kS53zFPX230qLfh0QPEMKbFPBRUP'
        b'qbTgU4HFQyot+FRw8ZBKCz4VYDyk0oJPBRkPqbTgU4HGQyot+FSw8ZBKCz4VcDyk0h3/VMiB1Hwz7i1bCaRrNRBfM2VNV2t1Jm36bCDx/dgP0KHaoFcT7aJphbrSCLVW'
        b'aCGHQUvYon51o5VyEoQ3zVJOFGN2JGejpZBEMG8/QZaFTzPU8iwxOdEDZJyjMwNp1GqAA1Gbn0h+Ag+7Fu7H5E+mGfX4hsnKJjilZNDznXIzcCV2wYpSEgXld9xKAdaR'
        b'Wqk5kH6gNISJLqfscxUh8GatDqbFbNcUZwKva9aV61aqHbF/ERUE7RpkRzaDFx8dThId2aTZWl620OpKSVI2rBo5GjPxnI1nRs1ROwz9hpbVekvVSm2lTZVNiSDl4uTA'
        b'xeUaIzwxsVHw6PXIxA7l/miREeOCdrwLNZuWopPZuXh7NGVlcYvKixlYKpT64OsurKzUxsquYJ1Z2Q5xh2+Hr4brGNAxgGdpW700UQ2iBr+GAeUCja9GWu8NbK1QK9L4'
        b'afzrGU2AJrCVKxJDOIiGg2nYC8IDaDiEhiUQHkjDoTTsDeFBNDyYhn0gHEbDQ2jYF8JDaXgYDUtJD8o5zXDNiHpJkR/t5YAnPt6aka0+GkUDZ+2tUCPTjKK99edH1eHT'
        b'wZaTkXnRp63U6FZvjZKaw4noXYxAKOulGaMZS8sGaKIhTdQgoTc1gmnaOM34eu+iQIgNgj5N0IRDn4KgjQEaeavtooF/Q0C5SBOhiayXQC3BVAyol8f0SWYSm+wZ+YWP'
        b'o31kDv9s0TIeh/C3h5xydImMxJTNOJac4VPTbHJN4iE1ziCygFz6kFjVPKQmx8Smpj+7MdmW3ZhCHrEkC7F1eEgNAgg0yL36fNSaVYCWjMU6TZ93GSAHg5n89Ffzgkux'
        b'Hrg7c2WfpMwC+8ZQtrZPQoxOdWq91Q7Dt1wHDF1xFezZStp2n2DWgvm8oYcxldhNSBxA0Mf6Rw10pjNPXHLybhA3+DR4lftYbYAkjZI65jnvWp91ErsNkDe1AZKs917E'
        b'aATULE34Dbkj4TRr5F8m301drdZEL3XZ51pHTRnKtEqXIi4RaSBvqKtk/VOUZr3OBTiFKICs98Wsc6U2mF1qIP/CpwMqMNsQkVwpm0bKA9Iok1ELQJmlRgaoM1mm0VXo'
        b'zCbXflm7YV8d973gk933wH7M8QN9SPyhPjiDRZosm36TLsyJzralWjtmct8XQmgIigcCoZQVVALSB+jXykyWUr1WUwHj+VG18DYkvHQKNcnUUAWE+f7L9NVAgIxKWaZZ'
        b'VmUBGaVU67YWtXXwpVrzai055pWFa7TlaoveLKe3+VI8r4V1O6TJZlh/ycqInjDcfrrooF+Ue6rFtpXSbNBqsi8muTxYbZSF87YqK3GvsRYkbk8VWW2j0qh4RVgRqIaH'
        b'EStmCddWKGWJsTFRsuTYGI/VOOzlNNlsEpDRAKmuXGeAXQN9lK3VqqFjEQbtanLUuSpJmaCMjZC7TtWPMBuW8hcVDOsCmZb50ximpiTqo+TFjGUyyY12p+LmHHRhLm7M'
        b'xK2qaLxtLjEizciW4+aoXAVqwm3Z8zLQxYzcnBzcgi9n5rAM3omOSqvRrXRa738lS5lD8iSGmVuiXzpQz1jITRMRbkdbbBWjJuRcOd6Ot2UDLUXbHGqnNdevlTID0UVa'
        b'cUqxhAkRjCOX47KXLVIyFoKL0a1SoMDkihW6OMV6yypDqYggl1fQJSGTtFRsKsuiN8VoJd45YmbuoGHkLl52yoJEftR4mxnfW8G6GzhuhDqbo0j/WuSFDl1Dt42+6Co6'
        b'hR7ogp6fxJpqoZ5BRSeGv/Ku98YY6ZYPT9+8dmdr+63NAsmbXtHRo3OPysJmJH+TEOK/6S9ndm2ZM6Z+3LZd9Ybe6Qen3Hkr9Nm3ZpUey/2Pc2mVAd+c++KbzmlBc78c'
        b'8nu16UVh22fqTt8H84b+59Zfj/3XV0df7itQfXRlbdfqE++Gxu+b+P21hUcj5XdySuVSM1HV4QbVetRMLk6iC0tsdz0CxgnK0Q18gNrI4pM50OfmPMf1ZJkhuE6I7yhq'
        b'x7HU0lY6Se+7Bu+E6ZTn2K5ZDUQNQgnqzqSXvaRKdAM1z6jKc1o5lgkdJfTFe9ZSW1rcVT4gUhGO9+DWDAXHiNEBToFOjqcNTMZ3I1FzgjjPYaWC0SUBbg6dSA0x8UEd'
        b'OhOplM9jcBNwZmJ0gYuvGEMthSX4VCJqlq8ld7vsKyNmglcJ0L3IMnM4ZFmPWtADMkgrj0Z6Z11UhonBW0ahZrFyDLpjJiQbHY3CZEagrgglyRkPNbfitkiSWWYS+ZnR'
        b'djp1NfjaUtSsQgfyeA0mtKyAdtFeAd6CD6Beav9ejRuXObRs5Q6HoFtC1ENYx9oRvJGkz7959az/pgq1LSUDYDYw68SsmN4wE1vvmfnDk9wyk3AkRczWBtlIsf0GS66t'
        b'I9SulGxS41TymEYehE0wzmBs12PIzc6nGShL+FL9lUy3l6KVuLlo85B0n/DgzEZm/whHC1bXrjoZMbPWP2o9Svq0jlnBX6Fhc+Vsn29xP+dgHGyfNoeLRRP16qpSjXpy'
        b'ENTyV1KjQ4u2tMdWTG6ty0b1w4FCaBTVBv1aeRfbJ9BUl/2orpXzXfMptnMT7npmzIBHCJQ3ZsKPxyP5HvBF3HTgp0xKQLEzD+Gx+UH25uVP5TJ+ckfq+Y54F9uIuMcu'
        b'DLF3IWy62qS1U/1/v0k78+ypyeH2Jsd45Al+YuOVfOOSYtsdNE9ty/rb9shH/HuLLi12FBM8tT+mf8V/gPnw0AunSwX08hvXwNgvv/1bVwps1bpcKQgo7BDQG7UHyjP5'
        b'+0uV/yotf8T8uuXVlo+kP5MeUjCTHwj//nGCnKN0Ctfj3qEEtzsi7JphPMq+LqMYe7xXuhuEjfejAwRpN6N9yqddRvMqJlvK8TLSBvhMqA10QGI0A19m0JM1DbYvxmLS'
        b'F5hYEzl9A6S4kXnP6eKZS41ynz4v67bk7fbFJrNRqzX3SWqqTWbCGfcJy3TmtX1efJ61feJVaipo+pYBf15dxQugArO6ok9UDcBuLPN1WACCs/1ti0CucTT42gVHP/sV'
        b'f3/eu0K5v3W9fRulsN5SWG9f+3pL6Xr7rpdaxcd6EB/fF7kRH6dpNCaQDwiTq9GWkm0H/8ushm8yLTXT/xESJJVvqHCillVaKrQOMhvMjEkHMo+Mv8lAxC+T1qyU5QFY'
        b'u9RD9n8VOW3RVdVUG4moaStWpjaA/EKKguxj1JaZ9WtlpWtJAZdK1KvUOr2aNEnZfWI2aVKSkeqI3gw2l7VKq8hE6nSpA6q2mHSGCtojezWyCLpoET9iRmZbR1tJ9B2u'
        b'fXfJH25WGyugDY0NEZHyMqIJNBHxw/SMhcxuqVFdtlJrNsnTfrxUz8NrmmyaEz2RLaFnn8s8FSMtp8no1YUlP3iBwWMt/PZIk+XTb9kSqzmdx/y2bZQmI3pMWCoqbS5x'
        b'NKfzWJZsPJBT4Slbkmc0e87Hb03Iyv+gbUTJMvPzFPGxSUmyJUR36bE0v59BAp1WoMicKVtiPRBcFrnE8XqG58b70QCRqfmAjFTkaBTssTggDpjMStgasF1NZUZdjdlK'
        b'vgickivYdG9N05uqAX61GrfqAAAnkpsQGz310UMXWymbyesE6BYdnW9WV1WR62yG0R61A3QzAGBBB2qsW0ujo16C1DCtq3VA1LRrYMWtG861HvIvt9qs5bcJ3fxac2W1'
        b'BjBJhaUKAA36ol4JGxA2jRZmp0wrqwbq7rYefkhk01Blh4kfps7k0CWlbDYgNRtCcluL47YjqhEAdeIDqUwPA+bdH5m07kuWWD0gVZfRnvNHJRMrzeYaU1p09OrVq3mP'
        b'FUqNNlpj0GvXVFdF84xmtLqmJloHi79GWWmu0o+JtlURHRsTEx8XFxs9MzYlJjYhISYhJT4hNiYxOT51cknxDygiCO1zvSMYnEt16vPR7VwW3TFly7MUylxyMy8SdYHQ'
        b'NzZfVIlP4SPUi0sBvuIbj44Wwc9YJnZ1KRXm14wRMvAteyO7KjtzfABjIbpPdHY0Pquy0fN5uJF4I8lSzJ87X7EctxXODyc3RBeCXA9fQOnRLnTZG+/GJzZYiGSKt6Ob'
        b'6BzuAcGWSIBeS/EWRoT3c9J4fIK6J4rzwg9wj5L4xiD3ZqFy4uxEhro4ZiQ6BVJ0chnVKVSjs+gs7gEZOmcB3pEYV+M8vLm4MReKtqgW1MAjLzsL7xaCrIs2++KTaPta'
        b'ajGDm+LRPV+lPAv1ok50G+/xYbyzONypS6JumUCcvG/BPZlQnmXQVnxPgPayaCM+jI7zXjyaQ5f54sZoJd4GjUahriwQmBtxC7rEMrI5ImFYAvU8I0N38HncEx2xlmMZ'
        b'LoNNmo3P0dmVzxGT44vAkui12R2+8xneF1QTuqox+cGEXYeG89BBaFuylJsTh27Q6fFDN3AdSffzU+Kd+Ho2vhKJdyWmCZhBawXoAr6It1qIpiJmJGrwVUIVMHvEs1Sr'
        b'ZaiAGYhvCwPw4UxdmkQjMh2AbOfiExWv5figmEDR75MzH3/wae7D1+pufe2zXD21e6hc+W7O+ZgzO0Invpl/NlrW8481H8YOqBtY+P6VW95jCtLCHxtTulQPpb+6kLQ4'
        b'Rb/t8ZjHMUuP5Na9zDa/UorKf1F+NPVV3bShRfPzIovePHD6Vb9W/OLx6e/e/PzNP+/73bUF//rr9tvPrbNMOfXuer8T73XfThx6ZduXnQsLLo/MNEaurqmVi6nGBd2e'
        b'ARPebPNVhdvwhRFWlcu5ZKqMQAfxzeds8Ajj3++sjoiMF+E2VIfO8dfr6yJrfB31LgVWzUvVHDNxVobqZ6G7/QxtA6ydgxZiDjrOq4EOjKmNzFVkZuaoonCrHF3Bp1gm'
        b'FPcK45agy9QlyNSlaLsqKjyD6F4uoCOwhug8txZdmOHknsP/33WS4/FirI9aoynmGTnKMY+3ccwZUlbKSthQ+nT8CKnPDwlbO8DO//bXYdVh+PEKBoIceNs14sXDuJQ8'
        b'lpHHcvIoJo8S8lCTRynjpNJwf8XXl6+zv5ISexOl9ib87C2q7e1Qjp44I5M7cfTvjHfk6N2NSO7dJ9UQYz4rp9Tnx/O/tqBYXUW/iYcTbZ+39QC3TNvnS7gV4BGJeRff'
        b'B/swy3wcUDHRvQTaUDG5zk9do/Uz9v7A2gdYmftAwtyXB1pZex/K2vsCa+9jZ+19KWvvs97XgbVv83o6a6+2m+fJeFdHP4KBnUWuNvC5ZUBFYb6ANwXOQO3o6o9wD1Gy'
        b'CmO1pQZSgWlWu1Kl6qpSnUFt41MigIWJoASWp69E4LfbcpIO2mVgl5qITPx/ZZH/P8sijtssjSwUH2NXdf2ATOK0L/nyfJStAreM2ZIfMO/02By/7/l2rFvdGsfztoZq'
        b'oroxUu7V4J4nXV1NmEddlVrvgftd8hQDV5Ap3Ju4euwxwVB8f0urq1eS/pIYpSzHCl1qGpZVl66AhQdJ3/1poYHIQilJMbFWbRgBBBDkSHVL+o1fPXbCjiDTZAtMFrVe'
        b'T3cGAM6qal2ZfTcucbCdfao4aEWwzstAr9UtcbSv/UGBjRR/QmhzsuL8P0Dmmq5dra2w2uD8X7nr/wC5Kz4pJi4lJSY+PiE+MT4pKTHWrdxF/j1dGBO5FcZk/Knwyski'
        b'boWAOhvVf7UmhrEkUH4SHV2pyszBTVGZdsGKeAh6UpiKwTs3oHveCSPQUUsYlWAMyn5ZaqSSF6VK8W0LcYmE7qBG3KVSZuUAL/vUijeEMqgZN3ujM3GZFnLUpEeH8D1T'
        b'Xk6eGDhg3n0RaWIh3gFF2nAjiFU+IINAlRC+nb8UHUIH0AlvBp3He3xz0fYhvNvaHg4/MGXh1g1jM3PyVMTvUYyQGTxdAIz8mRDe4GszsPd3TBE5IBheyAgnXLsyE10M'
        b'Z5mRFSJR2QQqaaEOtDvPF99E2+dLcKsiN4pIgzDufcHxAnQMH0Xd/Fn1FS3aAtFWd6CDhNnziKshdH0+8Qgai5pFa/CZSbRneF9iJOkYdCszSk4ciyaNDcEnBPgu7sB3'
        b'6Urt8OZmY4Y6kJUWDVjMUC+l3mPxCV8xiMsM6h5VAF3vtBCVvI+f2pdMEczmTnwzA6TNVtyOrxMJtBmdh1A2DO/iLBAHBMzSMMmcijBam2ZqJO6B70yYt0mZuBftoM5T'
        b'8c6xeFc8lcSnoO5YdAa10Xh0Dh3PtTpPTZgUDVVf0//j+++//zRRVFPPUpiK+nbhCv4gfnKWOGIJQ53iZlfJ1jIWcmQ4Bu/wJnPTahXdMwYWRBUSv8bRWQsAIjJwS364'
        b'HOAiI9PmxliObtDZExv8luHdqIc6ZWVBht82BvXk493xWQKGxRcYfCFFYkknnTxdOMrXukjz+8FF4mZ60CW8SzgI3WVQwwLvxfKx1MkWvop6YngBGJ1cRoTveeF4d77E'
        b'UdwVMFMGiv3xeXTXQoS2Z/CJ+AXojClLkZcTTSAol0q8AkaO94nQNYuGSvtitAOdjSSebsai89FZcjHjix5wuKfEi7rvfWtdHveCmAl8tFo94N3BdWtmMJY0iF6u0OEe'
        b'q4aDt6UAyMLbovNy5oVn+T9L/eY42S0ATJyR4h3DLbz72gvoSlqkMjMqgsX1g6EPbVw0OryYd6p7jkUXYVOoWNSNOxnOyKagLnRALuBLtuF9AMm06IQxfEm8ZRn1ojue'
        b'QBMtWYjb+IKtwy28D69QvIsOEt1H1x1GibaP1Q0rnSQwTQaBicWzlu2YlIunBm6pWPX2qkMbvts1GA08K59f4zXEP8ZnftQozfxjFpxUNzNoXn6KYs7Rj5Z2rXntzvF3'
        b'9v/9kxGvvfXuOwvePOKfHJKdc+BhRvvzmz7s/vJQ1sL39a2Dc8pD/tGa+NXYVQMz/9m2jnn4m1UnRfs3Djt6+uxzv5FabukmTDJ3pQ0X5T9XeUn55d38v78pGzMnybz3'
        b'46l/nzY0rKPg25cCa68dP3OkpcyrT2g4lP23pT3Zk/bqLG+8Ymp/yfy6cb4sM/fKh+zDivuq353+pfHS6QWbdlo2XXh5+/lTuUfL5xra/0Nc8c8ZazP3vV87pld26+Ph'
        b'Uz54uVfbu/jdvlrfc8Wnj95/97V3N69omHQoavvQEO3mdz5fJdv7/q8OLR1ofuXbFp+/HBh+d9w6r++Tz316/tmxt7+7mti7BjeV1tYVvxPf/sakP34+5YvLxpPm38n9'
        b'eMegGxcRVQGvmYAV7Oi3BsEbhdT0QQQQvmndMJVbOwmqmFDN4xUKhyYUO6klGHxlANVLeKND1LFW8hy8WcVbc8wPpPYcAYUCPXTgHnXKlY068Y3ICKU8Yxo16PBezKFT'
        b'w/ABqoxgAXN2RCoJso9iZ6FjAEzbOcVS1GUeSJG0/wRVdoQYQPU0wy1jk9FZtIemeOF7icPnoPPZOVEcIwQwvYqaFvI+wJpZXyAKVisOfKGEEa/jJnjlUKeVs4LwJd7e'
        b'A7Kc5W0+nAw+1CbeMOQaPgh7sjkve67ZjTlHM6TdooYhAeiawER2mIJQLTLLqDWRCcI7BDDtZ/FRag6jX6EgCpcpQWRb8OoWQBhnnuItSx74v6R+caeI8Scqh35JnCpj'
        b'Cgh3sIF+OKlVFdOvkCHOi3l1DA1xxMBkBKSGsGJqZkJMTngXZ8EQ9qdGKD4cdXk2yEnR0d+qVX0j5VUoWvIoJ48K8iCeF4068lhhV6u409x4/Rjvxz58neX2irX2mlbY'
        b'2/GzN9GvwyEvBShy0uGcjXDU4XgaWpnIgeMix+POXtJFDV4NDD06ZRt8qObFt0Fo95IuahTXMc+Ja33WieyaFjHVtIjWi62H5vVPHpqTRkYyT7J1/jxbt4QVUJ6vZtjq'
        b'7DGCCKaAN4YbLqL68xpVZXaRvIShPteC0GbUakKtkmdQs1bACPzZFNw11UJ3xInCAfmJuAm1FuDWBTnz8PW5+PoCv6SYGIYZPkiANk3CN6l2F29C22X5uLUgMQY3JcSs'
        b'xfVCRvIMi4/iLXiXhezQMrYsn1ZTi+8vALIkimDRAdw9lPIdeBfulaKeWgF1hz5xEt5IycpCdIYo6vEpQD+nRjPjmcGoYQJPqm7EjFApYxJwS2FcIseI17PoCJBmyoOi'
        b's6aF1On4DK2Dz/Ey1KEbJsaM6U+QZdx/e8/Ku5criJXe+Fj1xZmpzfVz392y2wsk3fKeS28uiDjeE//+RzvnZCSN2OT16QsvvPTx75denr5nyp/++fU7uSEDNI1Hd9f+'
        b'wi+85Yt/nH11Y5DfMvOj0cMLuVmxUT4zg898M/XZf1xMmewbd3HU6IWnX8kXT3k75u2iTFnio/jtL9X4//XmnsPBXj+Lu7z67zF73pr+6Z/zM4d+3qVq+yr64y/Q9fi3'
        b'd3dNGI+rlds7vTf8+ZPHVz+e8rhh0Z9ltV89nF1XMKZ8ZnjLwWuHPrj9y/Zz33kv/0vpvt6L9T1/F3xw873Tp34b/aZide9LX4j6vgs4+ubcF/1flwdTVA14thNdpP7+'
        b'vdBOfJ7h0HF2AapDddT0Lh+fW0hxKnqAOqx4NTWXmu2Fo9N4bz9eBTzdiu4DYkW78E0eZR7B15U8bn1O7gazolN4M0+cOvGdFY5q80J8zqo2b0E7eWfxveZZqtwo4PTa'
        b'ooGzbC8SMv7ovqAY3U+mCHUwPinCzeR8BXeGixjhCBYdR+0lfNlWfG0mdYp9dJ2jy+uF0DwZSCh0dL/V0zxUkDbS6mged6HjFKVXhkLVzjaSqBu1hqKLwqHoBK6nVHHp'
        b'Ap2KGkCmLeg3gQxeIUAX0BnWPJ6f6nZfSl7RpgT3FDYV3aWVzR8OIk2zg0njzCIxEzBCsBztQlf4dbvlh3tVdovJCnyYJ7LrllEqijbhhrGExPg+109i0Fl8hs7WmvhS'
        b'6hS/DbcI0S6rT/x5z9DZWo5OoDO8Q020D5+1eQFfMwAf5w8lDuTgjYSdw9tluC6P+EZFO7hqfBXf+HHY93/kbN9mZ8O71qeEqryfUEUTMkRtHKmlo5AQKY6Db55oSQFH'
        b'8x8hJV38aQIJ8XaREnu6/fOhcJSQ8+dCOULOHK1u+A7wJMurn1j0efF6aVOfyGRWG819Asj3U+mTyFhDfhvsZKjaTosoGSLOXi+y1ttJlAxtZP5D5sE8iO/o/6KRloAa'
        b'aQkf/9FFscBfuTLbrntYFbR6q97EqDVbjAaaViVTE/2/gxrmR+nOZSu1a01QT41RayJmkLx+x6qwMtmV9lZljzud95P6fD2vJSPdKV1r1rrRRzlRVbHjxDmY0FPvyfgQ'
        b'uo43I+AixXgPakPb0BW8C11dCIzoFXR+HmoUAYnaKHh2ViUvH99Dl9F+3A4rqsRN6xjloAIqH84BlGkluAsVeI9KqRQwIVDZUVwvQF14e5T1DUACJtyPHN+UZBdOCOPf'
        b'AIS2PCu1FxWPxrtL0T18Eh+fhHrimIhEUUq+kRJ1dBc3lBBhLVIfwfLCmhR3UPpYinu8860UndBhvH8okGJUt5D2eTzeP0g1G1+iKIVIcuIsSr9xHX6Qmk/KAMp4AEmo'
        b'lR1WjJt1o/8WIjRtghw976tyXhnlPz02sP7D/e+HrhFnfq38mfcOSYjY1/BX7vUPVz83sKKyOmtGRE179nd/2TL1w6Zfbo0f8eJd4Qyfc4NzDuXMyFkWIFFc+Mys+6hm'
        b'0of3/qId8sfre+VXJ6jiN+/5/nan3+s39s/rqRr6z999+7ff3JKu/vMXb3YGNKx75r2YSQ+urRj7aQkjF1MbwIABZv7AFF1Y94TVNmpH+yh2rEgBykadAs9CO3i/wGPw'
        b'kbG8e/oLy/C+SD1qUuZwMMyzrGpCHO+P+jTaOA9oGP+eDI7x1eJDuJ3DR3VAH0jLJrHBrSl4gRdID+PXUdy6Dt3Ae/opEaVDwysF1RbcKxf/ANLwYJGoNhWTbUYx5eh+'
        b'TKkXCoJ5Jh2+Cd4jJ67Sb8WiEM4BeVgL5/6guaIRHn94AiMd8WCwaK20i+0T1qjNlZ4dpacxVp/U5PyRvENBbHeWLnyqs3Tr2eOHAtbN2WM/kiL4wqReRX7p9Y7o6sff'
        b'SyMDSJNllssiyK8IGeBaE6/lJohIu4bcdyVK3whlra4mIoo2ZMWIRvc6YxPx6qexa6rVxrJK3SqtUpZHFOurdSatHevROugAaHa1rLxaD5j+B1AYWS77/T87CpPkWoh1'
        b'ggjfmBqZAbtibgZuSUAd8qycbNRVkAEMYmOUEjiBDLzVq0Y8lX9T1A10Ce1UwS7KylHibegqbgTWrAC4nOboeRm4VRFOvLqo8A0vtAc3jaSseYg/iLnt6DwV+wW4K1XP'
        b'os3cBMrn++Wjg5FejAztYtYwa9BttJdGL8Adz0bmcQwbig/NB+5jhkCn3RfEmc5C2q9mlU3KSfVHMYGHlqVPvTVz596ZH3mt2zh3alBa82ZOPlWXfPId/227VnybP2zO'
        b'8YPPvrD02NikN+/VXj1xZPnYuvKrhc3z0o//wbjKVzGae+GzsdPPvDb2bVVfTeEbB6eOSGv+7YdLrw9LGZxXVPu38XHHVg44OCfQkPPdYunnbXmPF/s3fln9dtmSlD8V'
        b'lk6as2rW63/J6f7dZ2mK0191/itoyaNf/77+i89rpq79b/bN2uTC4+fkAVQRoca38SY6vwDpoehKMosu4XO4iSIQ3ItbMwmLSfm+NryFep1v5p5D7VIewzRlojbcg3eY'
        b'8bXVVsWLNzrDoRP5syje0j6LdtAKtkUp8D4QfHK5YTNxC2WxUUMaceqP2+MgVZkJD0BRuJvDvUCebvNs8gkZvqCai89Hoe15/MsBfKdyeB86OYOylLgDd6eRF8xFk9dz'
        b'AD8JkhUXgZpqeLawYUUQ4QrRpjVyJW6jYwyIEVSgjiDemX4TOrDM6mo9CN3nsWq2hc5L7QJDZDRumuEdlalQyjnAep0CtGXyat5J+05gsc9T1jo6F9clixjxRG4QAN9O'
        b'mjw5Be1X8fBZgw8AiHqHcOgYiJz7rD78h64kMgqZFDk+C32ezg2Oncp3uRXm86SNEQYuGPf6Ekb4GZBfKA990Bu3k45FZSaiG9AuOstF4VP4wdPUND+Aph1Qs5BsXWe7'
        b'F/Lx5hUtEnpnRwr8qU1xEgixtX52NEpK84i5y/riADPjpArx3Mkujs/b70N+FTy+fwJ/14U6vUjAqWG59VL0LIZco7ffNAY8Yv0nF/FfHPwNeMKjFDGT11SXFRfTqz99'
        b'khpjdY3WaF77Y64dEbt4akpDdTGUE6bEh46A58ZD/tcVZU9dRyM5E/uYLOMuhvoKEPqwwBow3PdCjrFx3d+HjONAwOC+Ewt+4rfQXyDl63uyTqg1NFrKihmH1P53z3w/'
        b'bN6QZP+hEpYyaPNjNaZM2F0mf38B4zeci5HgY4Bw6i2EM1m5BF/yRWfNBPH4krOUuXMVYnwzlRkWJxzjI/xffrmRi6rKVq0zRfLKpdgf5NhWfDqfYeLWMaOYUSPQdZ7h'
        b'vDgf71MpUXdMIhTGN1i8W/VMDr7OW0qewGeDI7OyKhS40UHJMwk94I06t+Fr/rg5M4rwWPFCQLJ7cRNq5rLQZqXu9uOdIhOB6jP7N39esvT57h3H2mO3PMOW3bvh9TF3'
        b'eovUNyx9WtQnIadDPtmSXZKk8vFd1HHspdN1sVuO1R3bnbmLHTuAvqFixbKgNQHD5SKKhLLw3hnA1dkvL3olx+Pt6CiPhK5A45fsSAhdnMJL47ilgOLGMehAqE0bTlXh'
        b'gPl2KBbN5klCBzqOenhhnJfED8yhwvgDdIzXEhxCPYA8yaLSdLxVuIzTwgQdedo1FikIWMDfaIuJ9QLFUERqsGOosUShSzCSEJ7GZ+0bT9gnJAX6xNZrZS4vViJu4Yzr'
        b'7BuHlBzF2WrfaP186Mg2UvhENytiI8OzFBlRWag1mp63JqGbjAzvEYVswJdcgGmg9dv0taOXjUjiaQIgldMI6r2LBFohfescQ94318oViSAsoWFvGhZD2IeGfWnYC8JS'
        b'GvajYQmE/Wk4gIa9IRxIw0E07AOteUFrwZoB5I11mijYJaxmoCYU2pZa0wZpBhOvGhoFTRuiGQpp/holpIrpLRqhZphmOMQRXxhsgxBKjNTIiAeMDp8OrkNQLugQdojI'
        b'RxNWzkEc+RbYv/lY/inkczg8hU/+1ow6FAB1+fTX82QZzWjXuH/vqRlzaIBm7CGuKEgbrA3SjAtjjg44xtSxNDTeFqI5QqgpIn+/SAJz4mX1+zGQGil60XkSaeSaCIgL'
        b'1YRZvX14FwO1Us8GJpne9XZRvzuLGLy5o5i+U1BsV7qLflDp/iNfzOVjfRVgNDFP/52AmVqS/c/pA/lz77T1LczgqhZyPd7wG//n+MhT1evYf/iPEzMx6vQ3S5MYetIc'
        b'VAFcjcPLQzOcJEnAHc1eTH4FujhVEshZTbbXasYwMwt+BYMtKX133QDmT7Y+0ht+umFjNwpMpP8xv702vOWK38YYqfCD3OklpQeEN46+MkI6tUw+687zwpkZ5Sv1B+5u'
        b'ePhN1pCAyjcSJu4cJ609FrgiJTn+5m+bU6+98aufB3u9f7LbMjc0o3bNN6E/378+Ny6s5w+fXe4peXH+lLNHwhYrJ8q96RldeMVkYPr51/EoBIykgDNrplE0twbfBxGi'
        b'GV3OzomSgkjAiCdwQUm4m+LImfjOQOcDx0liet5YO50qVtFF1IOu26RrtBk4Vad5GRcmqlRN4m+8H06ahpoJqo0MV/BZIAPagk8MGiacODGTf5HdHnyPvBkI9fJdRa1U'
        b'cw0sYhA+SGw49qv4C4W9lmLc7defKQddgJXCuwXoRCk+wOP3m6i5YjrqRM3RwMBmklctS3ATh+oXCs1Ua3SseClqXg0VUPoL1aC2PLTdD+jBtjy8XSlmUlVitEeI63kk'
        b'+6P5y/5r4SMckXecmPURSdjB9Hq4VVnK1gbbN8wT71DkVZt9Imqo1Cckdq590v6DLUN1n7fOUGMxUydc/byno924yLiZ/N5IHnWMje3c5NTPaBcy8JYT9+mmfz/lrrWo'
        b'mHTc463XaZx1Tzi2Y7/8Pazfg6jL3VelUUXwy0/oil+x4+x57NJMW5cej3Bo3vXet/KnXTnvXytPDc+xNzw805bZZmL5k9utsF26JuBTXKXzfPE5y95sKBE0ZOXG6qqf'
        b'3l69c3vqNR7by7G3F0LbIwa4/2Zr4mJztVmt99jUXHtTYQUko81Q12N7//M71G5fIMoxrm8KpHTijTSOeRRK9m1JVNDYTJ4IxS0XMzNFI+lryo9OMDC61JNdQhNxm7Zj'
        b'3pHPS15J21Caoe7QhH+iUkvLPy35lPn6YFj+vhfCNoelLGFK3hJ7vbZJzpqJHzXUOyXQBcNZ0RtqwW02FIf2ogdP4Uqp6EfxGX3PmQ2fFRI2tDbIET/8+BvW+S5o57KT'
        b'0tK12offw7//byQi62pZVgrplY0a/436wUPWVtDpKAv0L2OiFxI4ZUX3dY9LI4QmotDLHbyPf8vwjp4uzaLn96F96NqOLsErN9W29y6u6BN3vjhFzpkVkD0MtxNK5X6t'
        b'lGL0AJ/j14pEWV8IjOtHEKVQhELJMooAMdDu+Ono2tPEi4Biamusq9UWl+qry1b2vxfPtqhLa8McZt45t9MbXEXUSNZV0iCiuIN6Yyc8Frms9TmntfbcotPmtC03gSzb'
        b'G10FsOCC/+mLPN2dK9EFn1L7N/aRgAmXsabiCYNzedNODp2oRufxcbQRstcytQNW0AOaSfgIOWwqIlj8WeZZ3IEuU8UuugGi4hGQM2868ZDk9aDhuQqWSUDbxP6jcB21'
        b'0GwM5Q1BYgYZpLfiZzDU4nDKsrzCl4SNfkyNesC7i8KzJNb7lffQUaHNVZKT5aEVaAozVi5y8JMEvJMPPoC3jaQYkcrjWnwUtzvI4yZ8WkLF8R68VXe2pFlo2ga5dh55'
        b'cdyr6f4oZrCgJL1t+qDC36THFJaq/yB+JerTkYH7DxRkP5y+tzF/bPK4YwfH/bN9wKVbGwbNrMea4DGFPoe9zzRKv35x3hZ1S+Cfr42saFr83+rS+dHjVp19N2fYr1s2'
        b'3Dz9+DX59/uuP/pu5e4c9tfZN65Gv3d1UfOx7z7JfYziE5T7Wn6/9bv/FnywY3TLsalyL56vu4r2zCeSt1XbOR5d4xWeMgsVzSdWhNlZ1vTkfqdJeC9qMhM0ml0a73mn'
        b'wS7DbSaCFI8sorYU+BY6iLb7RlgZ2xwL6qy08sIjUY8QX16Dumm16RvoS7jpiyvJKpMLfSqQm211g1SBzomHeU2jKs41wNbutV79g9W5qeFN0e6V8arXu7hT0K9dqJrG'
        b'n/Q3owdy+6uzPao3xcWrjTrr60+dONBiYjfGsSOAAx1itSeTsrWBDtuPFnR+U7PaWGHywF9yxg7n3d4Oj6Uuu/2004sxXZrLLRM6bEing17rC3vpnTj7C3uF9AxKBPtc'
        b'aN/nIrrPhetFTxMQRS77XGxVde3RFSBiLz0Sn/aFx6F0Krzy9rXb8Yn1kfMUhYr5GmJO6RXEjcDbZukyb3wgNBG3krovVxB11Y7q36Df/uy9n3XvuN1+u+72oqgt8n2j'
        b'ttyu66pLbc1sGbVvU4+IuZAmWSt6AYizjCFHz3eHgmhClCpo2yB0L49/kyrLDK0UosbxUbZVeLoqW1xML0nQtQ50XGu9PzW1cJpumpVXXIsdrOzom5aphsgZm3cJ+dgn'
        b'ctKV3k1G7rLS+4M9rTRt2vNCT2SoMR7TIKa6BbLcXj9huX+k5xpRLr+upM+zGLQ/X7EIHylUoD0sI8B32ZzcEJ33h1sF1DnnP2+EfV6iUr/0SfhHmTyfVfJ5ia48Ys/n'
        b'JQ9LVpY/0nxewjXFJMVbrp5avTPG0r2q+1TstlhhfM0NhjFX+w08/WU/R/qjbE+c3q5NtHkOKxviuLJGCW9eQyw6BzpMcX8Zvqo9nuFnr30d98Gj2mUd2wc7rqP7Rh6S'
        b'swDPK5rCb12RdfOK/qer6bp5batJ8OUGdBpdzFcU4t3xGah+rIARebFoMxDkLp34m69FJnJLwrLx5uclmfYVzVB/VqJU78z4tOQRrOujkkB1ZXl2WXAZMGevMMxZ1uux'
        b'YTBsVdLmc+jCLFV2BN44Q8xbPp+Y9uNfsdvnX2z1NuqwoE6MdC1Z0NrBDrPsVMCmfXDehn3icnWZudroATULjQc9bV1yn3+1y5I3hzguucfOyAN4u91+M15iwdvn1y9a'
        b'r9Su7fNbVW0pq9QaaZFY52Bcn28ZceiiJS9KjXUMxPVJNDoT74mFWAOTl8SbiWtercUMAiVxI0t2Zp9Uu6asUk2cnEKUXELPv4xEn2gkF0vcOQEmJ2FFtEZirxTb52Pz'
        b'uKLTOFxPX0JzmHVmvbZPQl6zQTL3+ZJftmvfNJq6dKI1xRmPkzJe5AZiafUaeje9T1RTWW3Q9gnK1Wv6RNoqtU7fJ9RBuT5Bqa5MzvV5TZsxI29BbkGfcEbe/FnGq6Rp'
        b'crvHhdklK0sYHhPxY2F1EyymBstsg6Rc8hPYXhepVGCt2nlHlfFs7zzROrWM+VJEtKB/UxVY6eCVVNRqwjdQa2gAwBGHT7MR6N4sykcuB354u8m8Ct8IwNd9WcYL3UzG'
        b'Bzh/3IZPUV61UoWOR5Ij6ovhGTnKzJx5uDEXXYzCbdFZ8zKisqKBewX2ir9DlITPiBncvkQ6A+3xovbGuAu3oC7cPs+EiXRRy+TgUxU0ZSo6hffGJ8QIGXbCOLyTQe0D'
        b'0RlK0tegxgXxAOTxDH6Ab8Xjs4NpgWi0fwPk5xg2PBrvJqc4l9AFikGqTKjVfgGDZXwZdK2Iw5fQ/Rl8H9rxsVFQUsyw8iJ0j0G78aZq3v3HYRnRDxMD2ER0PJ286/wK'
        b'C9n3oU10NkUpEYtMzFniwGN6t9d8hq/uArpTCtWB0AiziA8AC1LqT43Q0G10b6VKie/jywoluXWXo8BN2SwzCJ0UTiUOLmmlhRky8WZuI3Eau3TK8EKGehAJwvunQ50C'
        b'ho2CQTFoH25dwJ+71aM7vpHEBUkm3j4eXSAsZQBqFZRORbf524bmQSMSuUVE5bD0k+KZfHWr4tAdqM6LYRVz8TEgl3h3AQ8Kl1CLBThT1MnR1wcJo1h0RxhOa7qyevKa'
        b'6YJ/MExMSfAC2WSe1pbjlqz4BNQN4paSHP0z6AC5+UTqSh+JbhKzqxwQhbxjxXg3h/b5oAZa1yM2S6Njw1mYuRU3ihfxdaH9AfgMqQzWPBrfQ/UMOqiaS+vSousRvH+5'
        b'zNylxGhgKzcGX4mndd3hhBHbOP7uW96kYfwIgUNvHBGfAFwmzNiNcFhUQSQ998IbYXR3VMRRSzPergopoSZh/qheMBm14+28jn9qatZO9vfEDe78zwxmvnewbFvwBaiS'
        b'I0M9L2HQXhO+bHUDs0KLm2R8pbn9kDYEdQhREzqOeylkoMOo+RmoAAAteixqhVVEe+L4w7gmkCMPWstD/06ic2Qh/WsEKegc5qes1xC86DuW6L5Kln48Oc8KbBdN+GJ8'
        b'HIHdqNGwCmgP7hpq4cUMDbpmg92d+BoHwHuVxR1F/P0xdAGk1s3xiTEwQXEZq6DgGNxNU5ZF4PuRKmLEhw6HsIxYx4Utmc6X2YJ31sQnkyIpciUBwluojUKhFHZinRUK'
        b'm9BlErEJHZ0oCFyFmvn7jOdnDYKSMHVpgNMBRu6tpzusVIG6VPx0ydE5IZS7jhoCBQPXokN00CaV94pgRkZWQn8u2ZcfNOpF2/C++OQE6Eha0HKAG1TPgwm6k8tAN8iN'
        b'Q9V8dBUApYwbGm+gXShDnb5QBmArXTwculCJdtH4QeOEKhU5YuCqR6Kr7FS01Y/GC8ToGOSHLk/EvSIAxQA1NeY0Z+IGFcFqLbillPCX4gGcN96BjtAO36isrXyD+ZQA'
        b'dhI7fBZjveYXhR+gnpgEEcNOR50AjZ2A9jr5c/VuAKs7REA4p84ipyECfJ9FB+VoF61v1eo5q5Zzg1nYviuqJpfxoOiFrotJdYAOZuTiyww6ihvRZb6pS7gD1asArwA/'
        b'sxx1o1uwlY5H07rORIetyGJKyGROLCkfxus8lodMVmWmCaMA3IRCFnUWqvgFuwQ9vMkb0jIFecp1+Di1x0V30IUwendhfgaIvopC3jINN+ZEAQJimDnT8KVgr6FjYXIJ'
        b'YMwUoFv226bkkGYf3pnKod3oCt7X7zG6UihISeHoPVv91AXzGN6Ud++0YtwOjGcUg45lRwFg3KY3ZGLQ3QDVE+d0QHFi0S4hMw6dE1nQrVA6Fb5oL4ub55H7MXjfFMBl'
        b'weyyIZi/vgqo+C46rCrArQAPeP9soCXdgaid7uaZqejekzem0QN8m2XG5Yl0+Ci+TaGwiIVpP+gLdd1nWFSP7uPN6C6tIBTXiSJhVnLw9gxFFi/7xeIOqZAZXyCKA+Df'
        b'Qkcd4jckLV5QSajHxPaRWh6218eg7fggsNroAUFVh9CD9egQpR4Z+DDudKm2CtdzzPgFovhlJVa8N2mFap5CTG7kemkYwKLdk+l0phiy8nMCl8wjF525Z9lhvugAhaXF'
        b'qBNtVC3gJ+LUaHyGwdcUU+jFbJEMNT5xJZ1lRqLmDWFCfAPvmEAbFM6B6T3oR3YlU4DOEj9aS+j96rVGtDmfeOfaDlghF8pmKuKEzFB0QKifhPfw1OYE2ozr8EEBUXmR'
        b'vm4GgtkRTSGHqx5owe1OpTkofVBYVZrI32DauAT14mb4pWMsQl0AusJ7z7qP72iI/STp8RIz7XPAAMEKXDfLEgTpNYvxRV4hAAgsf6QyhU7uEPxgOdq4PpL35QUwxVtE'
        b'MMPQdSFgtK51dA7XaCfigyKCW5lAKboLm/4ErTMVPUjHzcCSrGRGzFpZg0/QEYQV43qVQpGJLoRn4cuok2yxAVMFuCMEX6DViS3x+KCU3IIEIec4upaFt/BD2BmXY72E'
        b'EgMrYL/puQ9t5SnRdjG+YfLzA9SEt88gM3cR9w6iMDUxxyemlgsnMCUNMFustLAe3yjDzTDmagafxUeqZ6IddNS+c/E5YNwyAKCIhzRFFumibCjaESUEtHQL76RKymqv'
        b'sezU+WcAJqca3l9zcOEjfn9ORWdz0XmqKEUH0LZaE27WGV+oY03/BGZ3xtSAZW++Y3hrbqD496kvbn/rWs5HW4NLV/3y/l9C+oLDO54782jJrcHe8mkLQv745u1RssOR'
        b'mq+Eky8/j7+UTPR6MOHMnp/P6njlT6kfv3wodtreRd/819Ff3Bl5Nfn4sbhTBUuGRA4w39s3esWvM36+4o0Rjx+Z5Iqf//Lc+CMb8mOvfPFwpt/6gzK/L+Wm57Xn//h2'
        b'x69Pv7Bbsj/3dNDrM1/o+c/2W03JOc+8GnEp3XvWJzK/CUtmfjJqyeGEWTemFeWO3vnnHcNzVzU92vxo1dU5mupjX0/eKXpp/QSvmf7Tk9InjjXeeuPDoJ0ntqS9OHP7'
        b'jNwU47pUufHc3D9de2n/5kMDU71S//KHzS/NemnchObRe0ctvFDxp4HjVnzc9lXMz081Zq89lPPd5VEf/+qkOvu9fxwbkxXZq/+PRd+ffGVh5dfX0luHHn64dtuIN2r2'
        b'LLw6tL4g6ObSnJmTpvd2h60+1z1EI3/97DfrXli5dvarJWX/WLHq9ROPjggMZ8ate7vs1bdP9i1cnmveUHf5xSEHd3x7ZsH533t/sOO1hT09OZq/bXjmYHXTxRypZfr9'
        b'cRWGMv/VmrhRHwy8nRx0f8rDcYc/9nqn/OsZXV+enfvhlT9MefkvaX84M/p1Y9dfTTst6e/8547ijH/FfdC7o/jbm36W9Yqvx0/5a+FHq//1uxXf/d44uek51OVf++2/'
        b'xs28Mf/TX50xjPnP5pNdb5UUnfnl3zdEKL5t1r4vH0B1qxbUMOdJ03xiODC7jDcdIMZZ1Pgf1cWgC5FEX86hAyvxLTbHK5v3br89HchEc+7yQpAnxIxwJovuoUvJ/OW2'
        b'K2hLjHg6ag6okRrxNdQasMrPW8yEoE5BtS6JZomaC9gZdUVlEPOGm9FUqxuE7wjQRXwNb6eK2uX4fAjpRxTeaTVWJUZiqyGVstbn0f51qDma2qoSM68T6AzeyaFmdGml'
        b'7XZCN9pI9cK8ek+SU4i2cBrgFBuocgHdzp4M2wpGtgpv9GGnoQODeBVwz2LUYrU/wzuA3vPXsaWong48DLWgRqCxIAEdtt+7TjPzk3IQdZE759SmoyCGN+mYks7356B2'
        b'gq8KXw5wealAjJzqJcuBvT/Ub1ixbLWj/QWH99J5mz0juT8L2lPhYH4xD2+laysurSTmHkl4BzmcIEIMMW62TkJkqgjd8N5AHT+jewEpaCuxIrEqQ501oWj/eF7tvw1t'
        b'zrTe0FiO622XNATVE0P5lWgq0zmbegBHS8w90JkV7jzl/2Rz0z6BWsNrb9bAw6692cAog9lQVsgGU7s8cu06EP6sHy6YdfmQuM8kwwPZseSKNjsYypA/KSvhhrAy1p+W'
        b'IdbHJG8gzR/IhkCIeyQJrfXrV81Afxx19UaifPupN944vlS/Dv8aPM4R9RA5ZLSrhzYyvx3iZJTs1AvPh+hUDci/IoppENnVgCxVWjz9KN3tWZ2MeVJpMYFXWpxSckzJ'
        b'AqJXK5Ge1WQzvG6QXhy6jw4qEGFSR7D4OjMC70QXeebxNnAWrYgcWoStxweZsIXDqY/TIQPR/nioPw63+TBxC/xp/RuCJIxsOf/Wk29Ffgw9r/vFVAkzc+hYKnmcHVvC'
        b'M6oDJz3Hvrf0G6I+eTZvslXgj1KDCAZyBciYDD6Ft5ehJrybP3w4Go72xieICTPLeMm0Pil8e7O8mDf8hlO/LB3LB/NV3zcHMiHDZhKxX5rgK+U7cXNcEPOH5dPpC2T0'
        b'ZiGf8/mRUualSPr2l6gBi/35nN3Tod/zY2hkZ8hUPufsHF/mjaERlBs4WD2CzzlwoQ9TkKmgke+Vz+cjf5MsZv4xI4waJtwul/OaV9SIr4Tn5wDLuABdFAqeYUSrWHQH'
        b'GLZLvOx5ezDaEx9DNDRjUdNYBu0qQsdou19ZxjBjc7eTBSuVFhYxlElanQcyIeUX8IXJTO3gUZSXmeQPnMZBH3KYio+jG+TrLr5C6y9MIgw2mbyb+PRC8ryHt/Or2zoL'
        b'ZIp2ABqFEXUyCrRrBG23OFnILPWhmoDsY3kLbaMg8lA73k0+IIDhrcwKHbpuBmaKCpPtmBziksqGA5ffxgxPQXsp/xYDmOho/xHqJBC0+CPUTrSJQl86IOgz+QrCn7F4'
        b'Z0kkGzyugg41BGTrrZGwUdb4zGPWJOFzPDT0oBt6dB5+rQ2KY9aiswqej+02DCP3Pphnh+J65tks3ElPcemyXM4VMienhVLVRop6AK9cDv51J9k7bNnPGPZ3n+j+NDeB'
        b'NSWw5Pa3rGpnOnHpsrVi1cdjX3src5jXgN/VMDP9hn/E3UbRo1Jb/zjk3MY/xM357Z+DvI7OTBV9JGycEbM8/WfTE9L/uuHuX/teTn07Uhy9IHSqIvxt77Bfz5097QSb'
        b'15g75Bcz3oorOloxcNDlA5XRllW+U+7NmLDwiwW+7++OqzIr0v+sKsg7/vhu+GFzvV+9X+R/hhsvLqqUmQtOLJszbtAvNpy73/x2/HPZUWeGnh3+fWD13K9eH/L99H3r'
        b'm5V3h42uWZY1aVR9V37+GXPwv1bMfFe68jVl7BJT7ZZJaxqXbUgLe/n1oL81/+67in0fM7/+9r2rYR+/cXVBVP4+798aHy4uPff/NHclcE0dW/9mIQQICIi4VuMCEhZB'
        b'BVRcUUGQVXFfipEEiAaCWdzqviEoIooiVnGjLuhDLGpRQduZtn59T6312fZ76etiF23r8trX9XXzmzNzExJIENt+v+8zMsnd5p47d+6Zc+6c//lPXdbR/+OEGyduJnw/'
        b'dmxmQei5zEWTI072qTk8bt8733x0zS8wpeN/PTzyXt8fj569N7v7zso7KG/C7aiRN9f9cqzXl5PXb9g7StGFRdMUC8iAthle0LQxeQwzx9vGsxHpNC72o7P+qWHBgjRU'
        b'Qwalc0K0m3SYDXSIz0rAa21AMMMEnng/sWbWoKN0GO+7uK8lYDMDXaQxm8RFKKUBkKhIhgphfE1J8RgKFkIJLgHUe6wI1aaichohMgW/hE5CWimANRUR+2GVMUnYp6+K'
        b'Rm6OxhtRDal+Ea5zEM9Kja8GtJ+hcTaiPYEgSQi8eKgVAHXUQeL7X6Fbo6X4lDUMRUI06gFi3gyOQdVMzv2Tiddi4TlCtaievc70nyHuTlZRYyIbvxQCBhLgjHyTqSBw'
        b'KQGQp3iDCz3JImLSbOANGjBniBu4WegjQMeoybIYXonRpsJnZreKGe2/lDb2VFwWQM0HA77SjPEU6fJ8qKC9lwGVEqkCncQnWoaUdu3B0u+cwTXEn9sSnhDqsWLAAHh9'
        b'TeTEJ0R45+jB1JbBe/BazibKFV1Zwge6QpAr0W1naG4HtD9rAN1rW5ILJxYKXFJR1YwR1MwZTU5y0DrzD0YPQ/mvQC8a+5PtMW46+yCDlhEGsxIlPZKm0lZTqUOspile'
        b'g5vAPCWm6fCVNCEybsTHw0EKx/ZZHK4kLXIMv8j68iFU69ZsXqELuJ6PppVG084qWaGDvEKAtPDF5SyxEKpys4QrtGumTAxxedTCyrW3sPQygVhoySHgR+0rP/LxJ58u'
        b'5APLXjSfgB/dw5f/o5/PJD2En0qegUQ5MqG7wI8TP5aKYPpUJpRSvNdyr2ZbBgSwiV9rQ+rmcLZzpHjkwGAqt5tRa3ES0i5goJCv7fQrlf7XV8JC5xaoLRqnqwdiMxa7'
        b'S4N6IZ7XLLVEd1p+wZQTi4mkcC2IvqJBGXS+nk720uk/sywzPXZybErmlJnpcRlmkUFtNIsB4m/24DdkxE3JoKYgvTxmZf7x9BH6VWAKCS2ILZG3z1Njsly8xF6eXhI/'
        b'qberJWmEhEaySOw/X4t9YZtlvbDldsvnofiRJNhL4PWbxKXLeDqkLwW4JdXx6GQgr+ZdOO8polmJnVtNS1uYWmi+NDteWXF5B8q72sHyrRJaf4lKXFX9iFEMKIoO2WKV'
        b'q0pqZZl1U7lT7IuMZ5n1pMtedBlYZjvQZW+6LKUstO6UhVbGs8x2pMt+dNmdstC6UxZaGc8y25kud6HLsnJxNgdSqbruE5ZLAN2ywFPVrSt30AtwIPxyd8tyZ/JXIdwm'
        b'UAXw4HBXmjrJo7BDoXe2G+WqpQyyZJsb5YMVU9yMdJY3tIaqd4mgkDkDskJP4gr0UfWlXLE+qh7U3A/kuWKTUuN+2m2HpZ5i4TAlmxhRrDwI6D+A1EmZr4K+r2lJNWm3'
        b'EDwFIN08jxP5pZtv0GmBZhqQ6JCyl5FmQspgdYGRZa2msPQWmZT1EJGkcDW78YRkQOLD/6STxVKWRRTofFTZi82ihflkXZ5apTHlkXXSAiL5Ep1epW9mq3VIE2ufpMqS'
        b'FNyNOFHu/BywhzVJVXuIYnMU4jtft5soFhr5dxPFPpknthUnrEM0/u/kibW5GVY5IK14G1KQzc5kyJcrtQW5yjBHogyTZ+WSU2bR5N1t09a2zVrrgKH2KVrkiay1pB+y'
        b'PMfj46fJtcr5wI1OftqmjlYMaJGUmXGvOZTCXnTatkGDbJrCgfC8IORZeAJnrjN+XMfpGpxx5raTH9dhpc2cuX+AH9fyvLNmZ0tyjYq/YYOfdMMsSoJPbs0vyfXqHI2B'
        b'tDBRTkSH0e4UKjfxt82UD0mmfxcNbQf2/uSexhtergyN8N8dnhOXy8cYb8KbNY7oWDmthYmW2I12TLEbx8i8R/VmsQDJnbggiGbOvxLwxioxZxoJVZ6KDmyL2RYXU6oW'
        b'mypHDMQHCmS4eiCuoNXeHyODfLVBEYGBIQv7T2TEthiCvS5ZKiafSofMtjT22iYougFt9kCHokQsDV9fV0q0EuE/UXs6Q8KZokDeQ/jsMocCJ4ZkkKpQbbS1tjW41A3t'
        b'QhdiaXW1C6UAF4iIiO/c85/Jes4EQY6oMWiJpbaoFfYMtykpFkeuhYznPdARfM6f1poS4c75EdspYtrBpACFG2tUXI3r0Q7r1VeiYtuagxJCmbNiV+1FdNIDb+6EGzRn'
        b'1Uhg2EqqOVa8I+zaJR80RhY3SfN4UHms5ETvbz8SJpTPy5F1qvOaIokco7j96uzrm/YaDmjPqG5fqH+j5NQebUP5D982jJg57l7n9+o+2jS77wP3pPysXndHLe/4liqy'
        b'+OjSjh9+Me6rB1V3Oq16+fnnNnV6POXesS8DBnQqzyzfUpG3asGjGffdflt/oPDDwqJbE/W/CFyODV19J03hzoB+9fgEaVJwIMcQ35Lvccx/HIpLmVtW2gmdoyHfo2e2'
        b'4MktmmYMgFY/jo6iLTZ0u0dwGetoLlwvvEdM3OpNUQyleAFVRvHOqNUV7YGOUG/UiMqo+5asmBuyEl20wZUPxod96SYTemEI7ypP6AHOMjqIigdTDykRHZ9qdfoWdSdu'
        b'H6rCp3tSPhlFPipm3nyzL49rURP154kTv4OR3FTMpHBGy/0kd7E6kvmfyUr6jgL/JaIXez0RRlru/CCBgb6gIMvJ1I4Nk3ApaIMr2p+AtvxpRr0V7gigDBuvbTU3lnLf'
        b'CiTNPLiME5emKbUuWahmid3hhBX3ChQvQ/EKFAgKDMWrULzGcU+mkJG2pxJPu2tSEGVpAC/Mxqlbw/3DLt1ba8mfhpbUPdNqNTkFsU0lUjCIZPO5bOhxYVUb9LhPjZKU'
        b'ZdqYUE6FmmER6qeeLSSgBsHvI0p1y7SYS07PO9t63l7svH8KLa84kxhJTs/5rPWc3dk5bQyppzxftuV8xBZyej6l9XxBzdaSsiUU9empf7MtrWyxT5xKoLJK0A1eWtiY'
        b'ML+b+9fq+Tg7Z47dOUkrWw0fm3MqhAzHTN+AWANnU7NENqJAFDo8vTRyNp4UdOoJMjsIeX/Vnab5lWXLrDHpLm3GpIvoAyv+zsW33YRKauCQbC+fEt35aeiUbOmTWlUJ'
        b'dEpWsHFwqDzYFvVMlimQmuxkSwZDDVomBnBstN/ps54oRp6hywPXgfnYkHmNhy4r5+tMRp6lyECMVGdtA/+AEUQNTaLSZFO+GCNvhNtfFN/eNIkkabYcPq+cA/sX/iVa'
        b'+Y2UbflzA6NtvBh5kIVExbk/Y9uuzFZv9ZDKg2Ln69VZufnA38I7dzS7nENBm/uBwaDJyaddgbGktKLqMsg1tlelIX5OjhMqFov/MpDe5OhhVjcGzjRQEQpvRSw0v7CH'
        b'lec3y5nnRXulhh4PjFHQdkOHtZ9xKtv+guCqNWrDn8cXFQT8SJTZSSEPDs4D35pczrLg4N/NICUPomxRYYx06WmqboMtql3HPy13k9wJ55Qz7qYB7RPDDs7RJoNTkJXB'
        b'aaBCPnvgIOcMTLaQEP42mtTscjT5VFBKwD4+JWXmTLgyR0ll4V+BclkeTUmr1sMQFUrp2awusY1Ag9oWqE1aKfsXJOxpCbc8KQ7FYoaQLRkVOf3gCOe8YrYAGsvrIpvH'
        b'hKwlT2S+QcOE0mU7pulSLSA9g7YHHEDz8iqXwu92MhTBv1i7Sgz0TZkmK9eooTRUhmaStNbPrNM6w+QDgfBZbSLK1VoB6cEaOd9EREPlkScubmrYFKVxvhrePjomzQqT'
        b'k+7CUolqTXkL1bmO2z9MPrjFbvRsSlP2cpNRTUYOyM0sn6bTG6hQTuqIjJHHmrJz1fNN8OiRA2JNRh2MbwudHBAVI0/MV2kWa0hn1mrJAYzKzdDiyp0cHe1I5KdvoCGO'
        b'qtHYiJX3dGINdVTf07XLMNqQzU3/hJZ3uHIK68nwmrCF3E/dE20vP1tPriYI2tYqk3L+clOOwnn3sz1cPiTAeQe023HgMGd7km6WH96aJZNtjGpZTbSzaqLbqoZ0Cuv1'
        b'tVHHUNvdnF7aMLvKHFyX0wGNB/gRDcf/ovYAsUmJbrWo8qAMNsY6HbCb8YNA2E6GQrZEbJygJLKozid/pJvLYQwa2gbnuxV5aF/NoBbVDGqzGgpStKMSDKL8geNhvIly'
        b'epgV1MgOjZtKNTWskAeRh5zv4uS2O28Gkx4oFYG0nv8VKrex7eKmTpYHTcfVuXrykBJZIp2LYoOnbK7MupoXylKVYaFJb2gtVFvmnjPzkpqS7bf8rCZarN0b//bZMBT5'
        b'GSNPhS/57EERc9t/2CB22CB6mPO7YYGU8iYkvwxuc1v9gOJNySHwRXZsvZ9zLZag1uvzw+P1ShMptAPC4zXEunOutejuznUV1ONcP8EJnCuots5MtFJcLjHCiO53rpqo'
        b'bMRmUzkWw1njEStWrTaCZQHfxMCKbtO+m69bGiOHiWNiP2WD1UpWkDZ3flPhIID7sqOUWjkstHlElsYIDyQp2zT3GMoZ9mQ/aMWhYKeHDR4YHU16mnOZAF5MBIKvNntk'
        b'tpJcbTxRKm3tRAHK5A7Bl3x2tPMdeTVnYUtto0dboNMx8rHkF7OEZw8a0ub+1kebHmI/o9dme1sA2fyR7P44V9YAxCYm2tjYVHJ7nGvE+ZosUmHiOHJqB09kKyh167Tu'
        b'PN/TsETK9+T99w7ztAFz+WBTKTqPLlgBb6uzKeRNiHa5iukxK7xpEiDOPH5eck1IPgtinoO3P5eU2CncCsFDZ4R077k6fy6U1Pl26LwV05TD2N6j0Dl0Ee90wU3PATRv'
        b'ALqCzzMk8B5c7G8BxqGj4wHpTGHODTxa+fnoFYIfhVz6zxHK2YGjfTkTjXy8hJpGoct5IURc4AxMgyBBdGpiCstjBECLLZO5pZFuOQs6UDTQrEhKkri0LjEvVGXwn7aE'
        b'TX51RE1u1oxFqBGtsclaBBUlsDkKO5rEElQpUwxCuzWLz3qIDHegkdee2LhtZCpO996Q885jr6iJy2s27x7Q/2Bcn5un57y6Y2PP2tDhcbJbR4uGCib2u7FpqORfX3uN'
        b'qZ/18NqK4a9XzFlWXZz4/KUJn9yfvLNv2JC3jC4ncxb9sHuGZmZjUORzFZ1u3PwFzUyV/uB5+OInGx7Fbxm995uz8UlpSTf0RbP+0X/W9REFG966FVg59FbNXLP/o6vF'
        b'dddvX+z0w9s5F6U3lJq6mq8vv/nV9eHx+XVxL6W+dS/v4eWixM13/up/ZMOr/ksu3+v33DI0OGZ04f0933huuZP1+pKRZWsLurv1Mt5/3LXYdYruygfPTKhdFa2Q0ug9'
        b't8loX8gAtAE32eQgDsMHetOEnvPQxkh0Mnkk3m1Ff/hK6DzTmE54LcRy1o1OS0SnxJxEK+yjwnU01DILXfbhkyPhojm2U2X4IDpihHSnqLpTT8sU0hnSX+rxeWeTSHiX'
        b'iGbtxEXh6Cyu9rRJkmSXIakX2s6iI7fiGtxkT9HH+aDDeAPl6EO1WoqIgdDGwsW9k5ITBZxwsiC4N77QGsAh+5NyiEOMG528giQLdpNXq7k0KWXaEwu8BP1oviT4DWGD'
        b'7vzElZAGH3Yj3/5AUiSzTtAoVapUu7wdza+tITrbZrbK7akEV4htKmlO6Wm9kgUOp6z29LGdsrKT0jlyg+ZegrAjrlBszb3UHoaiXCLkIuhrtloShG/NihfAtGQ1RzSe'
        b'NkEAZMfbORNHIdQL8UlcaDABNLdEzHVA20hHEqxE5UqG7KDB8mVRUzwAF1oaNp2bjreiRpaifBfa65XBjhPgS2PRbg6f7YUO0HP1D1gp+NHrIaT47S7rLmYwRdItS3AT'
        b'gDAGTgYYhnplIl2fNwLSS4g53GAA4EYW2rWCVnI6yJWTicViTj4vNDmlDwNSrJvqw8nnfOXKFczTzsrwZsH5ZT28ObnUIAJwxthpfIbHcUpPrktkNxcufZ42RhnL9vy4'
        b'D1mp/URMVsoq3TRsz0KJO+fXJQeQ4snG0T5sz0neHpwfdx/AGaHvzHVhK+/kSjhZlwoq0hfRbgx1ktcdX8lIT0/nOMH4LHyeQ2sH4EKGbd4/p+fgCCAMFOBqvItSBVbg'
        b'Sgq36I734saMdA7Adkc5VDUdr8WVsxiR9BZ0AR2zwj241HgK95g4k96PrH4+PNSDSyJjwo5pz9BW9EAN0TAxhK/gS7253kSlb6I4GxM+HQA4m/FZg7hBuHgkw6FW4jrg'
        b'7yH9chIuD+PCeuC9dNTsJ6fZ6poRGhPRMY6Mcwc86XHPLuqXkS6HzlDfafEiCTqE1vWmIieHonM2Oe7QehUFaPguZwgK6O+KMCnnPSfTlZs3TyZaQpvzuMqN8y5IpMie'
        b'7+WRbFidgc/5ZkBrcng954r3Kpfi7fQ2vTWjExck9nElHXjESW4EnwtiT/iUjHR0UMFxMSvHJ3jgQ2gPvsBaeCWuMXgOJk0lRCcnoDION3nhFzRT9kYLDGRI5vZ8+Upe'
        b'GU+8+45b0Te9Cof2+2XjvvU71lX5H6/y89krNpvU2+foN7z/szx1zHW34z66h96TxofMHH4ge1njNx80LtuevHuHRjnt49t/29X4xfumbPczge/eey3wTop+Y2q/LacW'
        b'vV6/6cyk4Ir5b8dtnuMZdVt0Jnvq1VeOLLsYl7WyNNvnp57yGyUL5d8fWnCxS9jp3HHPXp+SMKvfMzse7R5/KKm2euSt30abByh+npf+1v4Phm+636HfpZ86Hvmu88lt'
        b'9z++eX/b6p2P676c2uOTW8peTbeUN09O33ls3cDJyUu3FW9+LNuzdsz6L0etU2zaE5bz7PveV59tqtH67mvY+9nIjL/N+WLHzK/VSJF6wjQtZe03Iy+IM/teS8o0/Pvs'
        b'xKU/N82IflweOgSXhDZ4Xij78bPOnfXGX5XPKPxo/swg0jN32UQ+4AORzkat5Sy9/6hQdDGEDoVky8JIKb4kRGW4YSBDUJah7egUMXaSBZy49ypcJSCj3eZujK3lAtqO'
        b'D1pT92WgAyx13xa8hsEltuehA7awjuEdBegMOriSjpXL0SW80SY1ATo2zIq6kMe5uAlRMZVgJTrXuRlzgU92hEwClxWMD6bBDVVRzAWqxRd53IVwsCSJhuqnei2hkS7o'
        b'mMg+XmYGXk+REAXheAOFhaCGORZkiLAP5DpgITellC+rOQIGn8NbLYCMuEwa5jIiFXhoeMJfGS4Gzt/DSTRIxWPs3CTg1T7RrRmI4YXWi8bis+gEFT9lWAIAMbrmhdji'
        b'MDqgchbkUogbRkINC9FLVhiG10rReHwRl9A9TLm4sjkKBtX2taIw8JoExj1T0nWJDb7CN0eAqsJRBd02K3Vlc2LFvn48haKWXfqJnh52YThodycLqkaLqmioTmCwuDmQ'
        b'KN/dPowIF6NzTgJQnpDJj3KpUENkeWtDpEDME/4KifnhLZTScHZvHmcKKAhvioMQkm93Gw5Fb/6Pfu5Kugs/k/ZwF0iEYh4h4c2HxQt/lLgJfxCSP6k7TxdGzYPWHGSO'
        b'L6IFGxnYID1a2iBruCr75IAtT6M3wAjiNL/vH6Uk05tamiSO+bhcGaWgG+maDVZCLsVw3OCQkCsZ7aYmhwhX9W5m19J2wwcFaB0u1DMkYhWuRoco1C8WFXJLPXAFn3Zy'
        b'+rSQtA6keQVAr5WJGjXdiiOFhhqybfHciSNLRrojMgJ8eC3/9o+FG/vXnfVrXNs5wn1W7kvedd6HFUu6/10Wva7/nqYTz4sfXL7aqKva07381fjltdXq/P+c8T9y9Jg5'
        b'ZsHncTs0/j7yaa4+Mcb0z/fVnuv3btfYLOGyz4PmF97/N1q7/uvqCzm6Ph1rsiZ+IkVNny8OfP/u8IfJs/v88jBF57GkqXLGm2X7836sl74ze/+x0hOrkf9zfkOP/BTT'
        b'Y3vF6GEnotLPTVR0YI/caXTW38KwNUSHSwSoljwQTGNWjoH0t6ErcE0qD6eg/Fr90SZ6rA8+RgZ9xp81W8/os9D6BUwdrA0QgaqzUGe542rGnoVr0IsMGF6aWUBUvpWZ'
        b'a8Jyxs0VjY7R7eMWmJKaibXAgqHkWkSd1NKzR+H6BJ5cKxtd4rm1/iJluWS9ABdqTTULeWbRTqkoB1UjRieOqohiYtxaXdBBxq2lQRsY81cp0WAHGI2VhV0LHwdM2kb0'
        b'0kwG8i/BlzvyDFtoPT7NKLbQLryHoa4247N64Ng6S9xA1u0YyVY53sxiCmcKLRxb6Pk0xrElQbvoADcCb02wHYY6yMgw1Jt4ebTRiomyqmOykTFgLc+xhYpw2Z/CsUVZ'
        b'oag6C26tzlZzYX3aptkCvdBMs6VfwrUNxlpqd9peYkvi2zUtPp84INaynIqoCHtUBgNoCelXqsK3JShrGcfZIrPaEV14gaN5s43qPAODVrWgz/L5Qy5tO+5JEyl6g3ae'
        b'z1G+LIk35beS2PJXPfZX/F6+LBkMKY/FpC75Et/hUgHNU9Mfr5MZLFaZwYXz7EZ6rC/RlacXKwSpmrfe/EFg6EpMXmHZ9LhtF/LXAzC5c92wFdzdiFHregXM7SmP23fj'
        b'tfBuSQN8a4LyX0wQLfvymm957vP7db9lXcalSQd+WDspffq9X7WPb3Z648FWw6/D8blTp+9UTnr31oH83T53A15ZfTbZOP3ew1vBCXcrlh96b1rZyl9PvC0tefHbXfl3'
        b'lk3sIqxa9GrIs4ZrCt3QT9aVzhni0yc0ZvVXVQnfF321r+l17HvyxtW/fj78jbuHJs3o6++7esciSdQZ8Yk6o+r2vzbu+Daoqj5c87czYZU/6T/QvzZ8VN3Vq4FYUrl0'
        b'8JGSiyGf/nr4YOwnL5d96h90aV5BQFrSjcfXh1U8KB6O/Hc1hBxxzXlwruTG7cpk89jb5zN6rFjg+6Cu86geb67S3j6Y436xV/yy7JQvNipE9EkPxJdRPXmcd+EdxCIR'
        b'DIXExC/gl1jQ8lqiR573WAFmTcusHugFfIC9fFm3MKLVC5rgpfwrGnwcnWr9kqX7/06PfOqC6B2R5Yl0WFD4qDQzU6tTqjIzqd6Bd1lcN6FQKIgU9HwsJBpGIvAVSrvJ'
        b'/boF+4326y8UxIAmGiEVeXkEruYWCwX6d62PosgszMy0eUvT7f9BGwj0/219kkFSUEUskeznY2yJu8BIxTuIrwmsPqVE+xehOlycloyKUKkr59VV9AzeKNIcnbxBaCiF'
        b'uoJEzxRBendvlyW/LpHK+60qPjjm5aKGdbv++iho54BbWTqf/IkFUYP3vlo0qCTy5jXdd5+VuVaZJm8JOfrtlfgVL+yqS8+Z3pi+MrDQ97Xd8trz11NmFgX/pSCv4l11'
        b'301u4k3r4jfErvf395r9oO6qYMK+gviT611LPWqlDXe2uVatrFjhnuH961vhxX/vIP1P0K9oCDEnQG10iUfHYVCWRqXB22Zg7PVALwrxcUkED8Wer0pKgzeURWlpqAZt'
        b'TQuDzD2NInQodgDdI607vJaGBkiKNJAeD94guXxfUU+0eQxNKrRiRO+kxJRgVNwvxZWTiIVSXJltBMMscfxUvCVcwgkyeqmB065iLt1/GGocGTLRhRMk4cvLiHtPHLJi'
        b'NpgeJB7h1qTEHp4pwHKfAvlnPBRCvN3Fiw7ji/3RIUMifgFtb97unigkt+VypsWlPIWqwenReYbxTpEXLhalDp9AH34RJDFNSsRrcaN1AmAgbmTH7ho3HgzPmFWhCbxx'
        b'JesoxGf7o0PUCnkGrR+KwAy4greHFvB7uKN6ITqLd3ZlqmFTNFHIW/CLMrR5ySITrl8kW2QScJ1xqWyWCG3FxVPoZYTEA/38Fqkb3hoCvHbwZmevEB8mlm41Y4OqH8c6'
        b'XXgSUS/kSlE98eZKYY0r172fmFg4xajSLk9xr//7B8v5E+f2BK3jQAk1gyEotainlCX2oZn2wWGTiUa1tIX6MSuC6p3eZpFWnW8WQxSu2cVoKtCqzWKtxmA0i8FHMot1'
        b'BWSzyGDUm10obbpZPF+n05pFmnyj2SWbqD/ypYdJeyDoKDAZzaKsXL1ZpNOrzJJsjdaoJgt5ygKzaLmmwOyiNGRpNGZRrnop2YVULzKY8swSg05vVKvM7hqDBQVqlhSY'
        b'5ms1WWZXBpA1mD0MuZpsY6Zar9fpzZ4FSr1Bnakx6CDI0Oxpys/KVWry1apM9dIss1tmpkFNLiUz0yxhQXk2eeaFrBN8D7//DcV9KGCaR/8RFHeheB+Kz6EAtk/9Ayg+'
        b'g+JjKL6C4h9Q/BOKL6B4CMUHUAD1mv5bKL6G4lMovoHiX1B8CMUjKN6DwgzFd1D8AMWXdnfV3apvf0yw0bd020/SbIjBzcodYPbOzOR/86PRT934ZXmBMmuhMkfNA46V'
        b'KrUqVSGlhiQQsyq1Wp6YlZqaZnfS9nqjATitzRKtLkupNZhlkyEcME8dB+2u/4+lBVsE1JulI/J0KpNWDaB05ouLXYl+a9nzhvhRhPz/AP6NTaI='
    ))))
