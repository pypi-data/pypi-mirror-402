
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
        b'eJzsfQdUW1e26L1XBYFEMca9yR2BJHoxuFdAFGNwCdhBAkkgWwisgm3cjW2wAWMb3HuMezfuNTkn703yJj1TEpLMZCaTSXEmbSYzGU/K3+dcSUhGcpz57/31/1rfmMs9'
        b've2z29n73A+YR/4J4Hci/NrGwkPPFDHlTBGrZ/XceqaIMwgOC/WCI6w1XC80iOqYGsbWp5gziPWiOnYdawgwcHUsy+jFBUxguSLg4cqgqZMKp82RV1bpHWaDvMoot1cY'
        b'5DOX2SuqLPLpJovdUFYhr9aVLdKVG9RBQYUVJpsrr95gNFkMNrnRYSmzm6osNrnOopeXmXU2m8EWZK+Sl1kNOrtBzjeg19l1csPSsgqdpdwgN5rMBps6qGywx7CGwu8Q'
        b'+JWSoVXDo56pZ+u5ekG9sF5UL64PqJfUB9YH1UvrZfXB9SH1ofVh9T3qw+t71kfU96rvXd+nvm99v/r+9QPqB9YPqh9sHEKnRLJySANTx6yU1wauGFLHzGVWyOsYllk1'
        b'ZJW8wON9CRNoVAhyyzznmYPf/vDbk3RISOe6gFFIc80SeN/GcKNKWPKmVa7OUTCO4fCaVpmMGwvxFrwpLzsfN+DmPAVuzpw9UyVmRk8T4vt21KRgHQMgJ2pV4W22TC1e'
        b'kwPZm3JwE8sEZXLoYv9+Cs7RG3LgC6XogAZvnZOpzBQxQiGLDqFDEscgSArHd9BpDcSr8CYoK2JC8GYBuoQac7VoJxSXkwYahqI9qBFvRvX4urIaN+ImqCYIdXDoCjqL'
        b'T9H+4jv4ag5kuixDDUsWO3DHYtliB8v0wW1a3CJATXPwWejvaFLddXwdb0SNqCVGo4oiXcYt+DbaQGICmAEjhKgOXcRHythH4HSAa/4qyILyy8n8vAU1DnAuJNsA8LyS'
        b'g4Vk6UJydPHYVVyBx/sSAtePLCTpSO9uCzmEX8iXtAGMTFYrYuRaZdPYuQyN3B4hYITzWYAArWzrwmV8pLFQwoTF/kLIaLXKIWVD+ci7BSJGkrhCwEzUmvEiFXOKMQdB'
        b'9JQF/YR/C2cmftlzGds37VpcmjGVMQdCQnbAbvZiACOPVVxLfTfeHPklH51j+Dq0LZSN/HLm/vAf+uYPK2E6GYcKEjIG5cLaNcbkR0bizTEZKljQU4WRWTl4L76CW5Tq'
        b'TFVWDstYQgPHjUPt3aZf6hp1Bj/93nuJIZNvlLqnl/v3ppfsE3G36ZXlWkkPHBEEem6PHlowSzWnpJJjOAGDD9TgjY4ekKDpYS6A4gVo33BmOD6MNtBYdGAl3jhEUTAL'
        b'kiqYacMDHOEQG1CWg1uhSrRVEcPEoAv4Po2OQtvjcCsMfCleo2JUo3GLoxdEL8BrEwty8nHzFLxDxHDL2YEa1OEYRaYab7CT7RCtASDelJ0fiU4pteMz6C5V41MitA6t'
        b'wx18R64HJqAOGFtA4lhmrAHtML3120FC2y5ISmZfWfByXAiKlW3QvZP5zvoDv1sjuNjxnCgsWiI+kz777Tc2KFuKE1NGsoGK7MH3/vHLj98fdv/dqR8O/tg67pfZCQFz'
        b'al+7MWej9MrR21MG9B3/XzfyA+9c7H81s/b0nRfvbQgd+OCVdeIXr/1YdH5AZWthhX3AK6vWzyjovfrusyseFv+g7Dx2KHf6oDnHPlZ83frrmN7qrzZ996V465zkNV9a'
        b'FCI7wan47kKRBjdH4+YcVRbBH+H4hgCvQe24Hp+qtBMkgk+E40PRWSrckJmN2tGxXBEjRZc4fAAdQUfsBO/hdYlB0WpFVkJ+tBPPhOI1giq8XsFXcAG1xUhh8jIcgBE2'
        b'x3BMD3xLULwEnRuJLtgHUvQCc3kM5nozIIumQnQDNtUYFhBVM76r4Dq5SIWVgItCSv/8Gw8CeQ97jzVaq2oNFiAqlFypgdQYasZ3BlsNFr3BWmI1lFVZ9SSrjSBGyfgw'
        b'VsIGwU9v+A2BH/I3HP6GsWFcEGsVu2pWCDrFfOHOgJISq8NSUtIpLSkpMxt0Fkd1Scm/3W8Faw0g7yLyIM1NIJ0jG0WOxRzHilnyFLLiH8jTQYhifpwjOgs3azJVaHPM'
        b'yBmw/7fEZLHMSHRJVFKMz3jtR/JP6PxL8a6B8AfAG+jZIgH8Ck1MkQj+ivVcUYA+pJ4xsnqhXrQ+sEhC38X6gPWSokD6LtEHwnsQT4qNAn2QXgphKYQBlUBYpg+GsEzP'
        b'FhACGtopnkUnLJdO4Cc/wLYsE3h0i4w4wIUqUhkXjYeKeBwkaBAADhICDhJQHCSkeEewSljg8e6PVgu64SAhj+J3rxaa25kw4Jq0Su0UEWM68tYAkW0mWYm37j/QvlT6'
        b'sXa7vkH3qbap/KzhYwgXPTsfX9watyF//5Qvj+zs8Xye7qTOLDrNntb+l3CbcpBsWtSgJum89DWf9u03q++653YnBDOXBT0iZjQpxPzWuINu5kW7CWW0mAlFxwX4ckwt'
        b'asq094McRehKdleGgrkCRqYUBIzCz9CdJ8TNaJ8G70P7cWM2cBAKMSNBm7mltWPthI4VDZ1OEJgmE50DzJvKrcQX+/U12fuQlttm4ruoMQ+YAyEjwvvZ+Qn4VpXZ3hfS'
        b'8vCdgOgCtE2VQVkKCb7CofUBqE7BeYCmwNceo5DaKSkpMVlM9pISupdC4BFWBHsGwFUIu0f4Y20ov/hqVz5+F4k6hTaD2dgpJCxgZ0CNwWoDbtFKFsZKSN8p1tUyqdIa'
        b'TB6h7u0hg0exa3uEnei+Pbq1WsY9sg/cAJfsBDgj5wQ3jpI8AYAbR8FNQEGMWyUo8Hj3BW6MH3BzRJM1aJkeLcXNsERbgHDD6mbwq5g/c9ZIfFA1h2Mm4CPiHvg43muq'
        b'jloossVCoX8Uv/9AS2Avskz5R7UuW/eZNqysYu0Eo7lUuDlOpf1cO++Fvi89uyeEOZQgsU/QKIQUjgrQ+SwNrb4YX3fDiRxftxP+Dl3C7fgo7gD03YJb1KpqgqifwpsA'
        b'V/dfJUQbcN0YWgtqTwBM7YSagfgqARx8C18fZScU1iBN1UjG5KlYhqthJ8GgTvALy/mEEsCQ5Qa7yW6odAIKQXBBpTJWxtaGu5fKnYWvSkiXvVNo0VUauiDDGsY3E+6G'
        b'CwoShDKXuUAi5JAPkPDRzv8ZNOQXLqLILG+oFvmAC3xuKgENN1ygA0+bzN8UsrZ4KHPsV7/1ARYAFJ9puc3xjti3Yts3VccKE6qvMczZzyU185YqBHRJZYPwObxniMYb'
        b'gQxDp+1EzkIXF4U8AhYAE0vRCQoWA/FWijACgid6oBK82Q5AgXbjdU7q6B9TAAzYusNAuQzQhMfa2LxhQMQvMVnsTlGNzuzoBgkCD0iIcIMDmesKN4bY+1hwcDfpH0mk'
        b'8eBAOGXWKPyZiGL9owDBOqv3BghRrkNNIuV4IxHjCnGDSqXOz8iajRvyCgg/mjE7A1hTNYsus4wd3w0Uo52jKAz1w5cz3TCEz0Z5o5cu3NKYaNrw+Q7WlgtlIgUZD7Sf'
        b'AhSZjVHCmD8rdRk6M4Wgal3Dh+cMJ3Ufa18pVZYpt0fqsnSndWFlzIu9rYJpe/pctMcq9Xp9hk5ifD87gImLDV3X+B/AYRKGJAgfxHu8uL9p6CBhANE5vA5v4dFKA2pJ'
        b'dUIgE+OCwVJ0jMJgGLqLNj8KhGNVTtQ0EZ+jdYzoP5TCIFoDpJMnaYCZrqB2ntxtCZ0ZTejZWLTZTdLMqxROkiL0yzXycCp2VBNm0U3PgswSyhvKWO7HMK422Ak3fC5P'
        b'TMWTKjd4dtsLgLS6iBmFUiKTVLqgNHyHDyj1bq2bKOeNr6gc7cZXbAP7RKJbxaPgKfQJnoJc07TBi4W2LLKGXwdqdBnlnwH4/FdphTFCd1J0qW+fWJWeAE/Dh42604az'
        b'Bu5Flfa8bv4L8345HxfimdiMZ77wznPzBL/q8dKzb3OMMD7UunIjUCzC25ShU9UeWKkCWB0ACtyCblOcg9ctFLiRjgBIFFlvtGcwXW60GUSzDbhRmYmbQVoTz+jzNDec'
        b'HUoLrkQt+IwHW5SF9qVy/QRJvoHgcdgLmH2b3erEXESYD7OHA0gEAWjUhnShEpKFljol4NfZPzgAi9MFCYSDc7jxVbMPSHikEQWXayWCvCKYsGCERIIgElRSwuvh4F1W'
        b'UrLYoTPzKTwClZQBDJVXWZd1SpwMl40yVZ1io8lg1tsoX0UpKcWfFDxpz1y4+LEyFz8QMjUFZCCknIQRckKW/wnhZBKZKEwUIaGarMi0GCkVWFKlILJIZJwW38RH/Iss'
        b'BDV6iSxckVAvICLKfq5I1MboxYdBRDnC1rEgvkio4BHYKZ5mAdS+7GHEVEOpyV4Fsl+MxmrQ86+f8IzEJ6SJh+FzDNZaR7mtWuewlVXozAZ5AiSRET2UZRvstXaDfLrV'
        b'ZLOf4uisf/KfMOJv9sCsaqos9qr0XJhleeQkvdVgs8EcW+zLquWzQfC0WgwVlQaLIt0jYCs3lMPTrrPofZaz6Oz4jtWsls+ENaqCsnOqrJYnyeerskUGk8Ugn2Qp15Ua'
        b'FOleaekah7W21FBrMJVVWByW8vRps1XZpFPwd3aBXZUJAps6fZIFJsyQXggU0hwzaZFOr5bPsOr0UJXBbCN000zbtdhqqqxQc62rDas9vcBu1eFDhvSZVTa7UVdWQV/M'
        b'BpO9VldhTs+DHLQ5mHkb/K11eBR3BUqXkN4RkV3u7AhEqeVFDhs0bPbovDzOb0p8usZgsdSq5ZoqK9RdXQW1WWp1tB2Dsz2DfAa+Y7abyuU1VZZucaUmW3qhwWwwQtpk'
        b'AzCji0i9kc4ohStNPsMAsIPbjXYbGSWZ0u655TOyFenTVDk6k9kzlY9RpGfycGL3THPFKdKn65Z6JkBQkV4Auxg6afBMcMUp0ifrLItcUw5zRILes0ZiFhEYVuU6KqEC'
        b'iMrG7URHsojMGj/9EJk5eVIuSTMYrEbAFfBaMDdzeqFqShWsjXPy6V4wWSoA1kg9zmnP0Dmq7SrSDiCdUrWzTee717z7iidz7zWI+G6DiO8+iHhfg4jnBxHfNYh4z0HE'
        b'+xhEvL9BxHt0Nt7PIOL9DyKh2yASug8iwdcgEvhBJHQNIsFzEAk+BpHgbxAJHp1N8DOIBP+DSOw2iMTug0j0NYhEfhCJXYNI9BxEoo9BJPobRKJHZxP9DCLR/yCSug0i'
        b'qfsgknwNIokfRFLXIJI8B5HkYxBJ/gaR5NHZJD+DSPIaRNdGhP1kNRmMOh4/zrA68CFjlbUSELPGQVCdhY4BsLEBhCdXoNoKCBmwn8VWbTWUVVQDvrZAPOBiu9VgJzkg'
        b'vdSgs5bCREFwqolwDAYVT+4mOWyEoNQC15A+F7dXWGHebDbaAMF6PI01mypNdnmkk/Qq0otgukm+Uki0lJN803G72WwqBxpll5ss8kId0EWPAgV0DUjKTKrL9aysi4yr'
        b'iqAXgDAiSXGvBGd5SBrZvUC8/wLxPgskyCdbHXZI7l6Opif6rzDRZ4VJ/gsk0QI5Op4u0zkHvgT4ExpnNyy1u18AE7lfEzyz2tzZ+IWYbAByXO4RMTK9yGSB1SDrT9sh'
        b'SbUQRUgvYGmvYLx3ENCPzmYHamc1Ge0Eaoy6Cug/ZLLoddAZSymArXvF7VbcXg5AlGnRm2rU8uk8/fAMxXuFErxCiV6hJK9QslcoxSuU6hUa4916rHfQuzdx3t2J8+5P'
        b'nHeH4pJ8sCnyyFnOWbU5GQ1FF2PkK9HJK/lKcrFP/tLcqMxHep7v1gjf5SveixXzP4bHpPvjzn5O5nj/LXvxaU+SDVClr2xeJCC5GwlI7k4Ckn2RgGSeBCR3YeNkTxKQ'
        b'7IMEJPsjAckeqD7ZDwlI9k/HUroNIqX7IFJ8DSKFH0RK1yBSPAeR4mMQKf4GkeLR2RQ/g0jxP4jUboNI7T6IVF+DSOUHkdo1iFTPQaT6GESqv0GkenQ21c8gUv0PYky3'
        b'QYzpPogxvgYxhh/EmK5BjPEcxBgfgxjjbxBjPDo7xs8gxvgfBCDIbrJCrA9hIdantBDrFBdiPdiUWC+BIdaXxBDrV2SI9ZQNYv0JDbFe43F2cbrVUKm3LQMsUwl421Zl'
        b'rgFOIr1g2sxJKkqt7DarwQhE0EJons/oeN/RCb6jE31HJ/mOTvYdneI7OtV39Bg/w4klCH2RBd+pNtoNNnnezLwCJwNHiLmt2gDyMM9MdhFzj1gX+faImmEoxXcIpX+E'
        b'bSjn451cgysU7xVKSJ/pVK54FO6mdonrHhXfPQrEHDMRinV2wpfKCxxQna7SAGRUZ3fYCFvLj0ZeqbM4gLzIyw08mAI59KUGUHgUMRHibtLTYj+Z2Uf9PoiS77q7Z6Qq'
        b'pq7ZkQPzLXeyvHQqjSTdOcn8e7zHO5EJuzRVD9n03FMSK1GXW4mK1UqsrvizEmKGYSVH0p0iW7XZZLcOduvwwry1eUSpv9KlluS1eZyAY8XfcyKOE8dJXnZQm5BtQ2fa'
        b'iGHJJiU6VYJOCRlJMrcKnUdb/hv1eRWKwM6gSWVlVQ6LHeSHzpDJsOi83KGrNpg/6cVr84hG/GH/qQAGlcBbEIWpnJd8AIhNgHogC9HGdgoJD2Qlpj/f3IGI2ZU8S1NV'
        b'YTHIC6rM5pgMwEkWlaaWaFi6gl1YLn2upkjOFyOaNII/bSabg48gaZ5hftfNIIo/nsPnG5o8W1VQVmHGd2D1zcCVeAbTJxvMhnI9GQj/6lS7dL3HOyWkdNdMUI6fsIQG'
        b'5+Z2iW1yni1yCn9daiqn2EeZdSLwQWbYXnYqGDhroM2ZTZCBvpksxiq5Sj7Jand1xRmTaSElH4kk2eJ9ZYvvli3BV7aEbtkSfWVL7JYtyVe2pG7Zkn1lS+6WLcVXtpRu'
        b'2VJ9ZQMuI6+gMA4iNPzCEG7XQCPju0VCQJ5jAIzp0sXKHWp5ly4WInlYdilH1XLCsbvkbl7p2rWM8uzo7PTpDssiaohrsJYDiqolaIXET54tTxzDE1qjKwtRCvuKd8IN'
        b'n+SjwvQiKhCQgVsrdSTRDSK+Utyg4q9Y/OOK+U7kQegxxXwn8iD1mGK+E3kQe0wx34k8yD2mmO9EHgQfU8x3Ig+SjynmO5EUG/O4Yr4T6XLHPna9fafSgo8HFP+QEvdY'
        b'UPGTSgs+Flj8pNKCjwUXP6m04GMBxk8qLfhYkPGTSgs+Fmj8pNKCjwUbP6m04GMBx08q3fGPhRxILbDjO2WLgHQtAeJrp6zpEoPJZkifDiS+C/sBOtRZzDqiXbQt1FVY'
        b'odZyA+SwGAhb1KVudFJOgvAmOYxEMeZGci5aCkkE83YRZHnkJEstzxKTEz1AxjkmO5BGgx44EJ39keRH8HD3wl2Y/NE0qxlfsznZBK+UDHq+Y7QDV+IWrCglUVF+x6cU'
        b'4Bypk5oD6QdKQ5hoI2WfKwmBtxtMMC12t6Y4E3hdu8loWqTzxP5FVBB0a5A92QxefPQ4SfRkk6YbeNnCYColSdmwauRozMZzNv4ZNU/tMPQbWtaZHZWLDBUuVTYlgpSL'
        b'UwAXl2uN8sfEKuFxxy8T20/yoYO3fsLt2bbsXLwlhrKyuEkTwPTCTehWqVCGjuAb3XhZmYuXtbPevGybuE3aJtVzbT3bevI8bXNAoDgwSK+sF9UH1/c0CvRSvWx9IPC2'
        b'QoNIH6wPWc/oQ/VhzVyRGMI9aDichgMg3JOGI2hYAuFeNNybhgMh3IeG+9JwEIT70XB/GpZCeAAND6RhGemBkdMP0g9eLykKpj3t+chPoH5Ic1CgJFCiV9Vzzh4L9XL9'
        b'UNrjEH50bUFtrJGMMIA+XSWHNQdCOTU1nRNRF44wKB2gH64fQUuH6mMgTVQvoQ4e4TRtpH7U+sCiMIjtAT0brY+EnvWAVnrqFc0u74SQ+lCjSB+lj14vgVrCnSf8sZ2S'
        b'qcSue0rBnIcxQXKPf65oOY9OeA8krxynRNZhBDpGkON8at4dQ96ovQYRCxSyT4i1zSfUZpnY2nRlt6a4sluJ3Y01jmQhhg+fUNsAAheKgM4gnb4GMJS1xKTvDCwDPGGx'
        b'k9cQHS/DlJiB0bNXdErKHLCFLGXLOiXEVNWkMzuNMqRGE/B2JZWwfSto252CabNn8VYf1jHwKJN4AGOQ85ca7UxnHnGUCqwX1wfVBxiDnLZBkgZJHbMysDZwhYTaBgVS'
        b'eyDJqsACj3fedO0b4l7hNXPkXybfVVOtwUadw9zzbaKWDWUGdbci3SLSQPzQVcq7pinN6RYGKIbog5x+Z8750lns3Wog/yInA2awu/CSQi2fRMoDDimTU3tBuaNaDpg0'
        b'Ra43lZvstu79cnbDvUK+e8En++6B+9TjJ/qQ9FN98AaNNHk2/Uu6MCMm25Xq7JjNd18I3SEYH+iFWl5YATQAdoBBbnOUmg36chjPE9XCm5TwwirUJNdBFRDm+y83VwE9'
        b'sqrlmXZ5pQNEllKDz1p0zsGXGuxLDOTUVx6pNxh1DrNdQb0CU/2vhXNLpMmnON/kZURtGOk+bPRQNyr81eLaTmkuaLW5F5M4IVZZ5ZG86coifMdaCwK4v4qcxlJpVNoi'
        b'nAlUw8OIE7tEGsrV8qS4WKU8JS7WbzUe+zlNPp0E5DRAqjOaLLBroI/yZQYddCzKYlhCTj5rktWJ6rgoRfepegITYxnv6bBB2oPRaycxTLVWGRQUxDjGEZ3N2ZAZuDEH'
        b'nZ2JGzJxsyYGb5pJDE0zshW4UZmrQptxS3Z+BjqXkZuTk5nDMvgYvoq3ocOyKkZOq3UMBkTXM4lhZmrN7+lzGMd4hhrjrQ/sXu9cvBOqJj6Q2UBc0aZH616/TMYo8C5a'
        b'7x8jJczZ6YBntVplaVBvxkFQrlG5ytM9K0OtiiKeL+i8kJFKk+eLbahjNnUto1W8sSKA2coNYBi5VlbfK5JxEKfY5SnjuncMH5icVwB/mmDQpHNNijke/UI3rVJ0GW1a'
        b'aGLmLWVtq6CWF7YnDXrpl4Frvv5dbNi017NXtX78Sohy0kWB5iKT8vbJAT2iZ/Yp2FjzqU0yVvzKyO0bRg9fP3LT9vXqO5PP/H4f7r389czSI7m/Pp1WIf3m9OdfXZjU'
        b'Y+aX4e/rHMsDWj7VPZBOyB/wm42vj/gu7vCLnd/tfL7sr9/9fodlwUsVX3/Plq2K/NdHyQoZ9aHKRadGoMYup0sBEzoS7VoqMKpxh11OVrcxfQVqzCNriZviXMvJMv1x'
        b'nbAWPVNMawnArbNnLJTClCpyXPa6vVC9UBKD9vAG4S34Br7ZLwFq8lo6luk9VChFDT2o/aUd78UnolWRGSqOGYP2i9FeTqXAG2k/UvBBdBuKeyxXODovQFfQUejZ8WLe'
        b'IvhqH9werVbgzcCp4R3FYnSWS8BH8HXaCT3agfahRuIs5l4jMRNeI5gGNd9Fp8LtxBVVKJhAxgvcGzrWJ8bZUecyM0ws3iBWo2Z0hzpALLbiPWRIjcooNcmGm3FLNMmG'
        b'm+bLbaJgvMlMrZnRMXUJyUcVm9CwCppFuwT4diTeEIAv0wHOlw12thsX5sE39kc3hKgxB+/mLSeD/k03ti5vF2p2SjYCs1q8QswSbzX+SbzVJNRjDWI4McQGsbU9XOT4'
        b'Ea+bIN7ilHiWWSeSxyTymEweUxiXh81U5vFWzBK+VFclk92laCU+fHU+YZwGoczawbt92LZ276+XpTPr/KV2paRnK5iFEADuhM1VsJ3Ski4WwtrXPXcePkpjzbrKUr1u'
        b'fA+o5a+8Z6pHm67Uh06k7qzNxQBEArHQq6os5mWKU2ynQF9V9kSdM/KdCypxMxa++mYlPrgRUN6aCS8Ph/A94Iv46MATtVzBtxxa4s1O+G2+j7t5xWMZjp/dEef6BJa4'
        b'6LnfLvR3d6HfZJ3N4GYA/v0m3by0vyYHuZsc7pc9+Pcal5S43Nn8tS3vatsvS/Ez23aCm6zEU2rw1/7wrhX/CT7ETy+8fA+oBx1Xz7g96J7U8+AJPaUEuaaYfc0cddQ9'
        b'MaqJd32qMH7GZG99venlpj/KnpPt/4QZ/4yw81WVgqOoezm+h/agw3G+0PcGZYadiFOWFbjDibvH4nvdkDc+mPw4j7aAErKtPDyZmNXM6ojRtWEeqIxm4Mv0ebSmvu4F'
        b'eQoeo2BybSSKWcusDen0gSK71asI6gxwblDeul9ss1sNBnunpLrKZifscqewzGRf1hnA51nWKa7RUQlUWgZMe1UlL5kK7LryTlEVgL21TOqxDASLh7iWgjgM1UvdEmWw'
        b'+8KAEP62BmOIc+WlDTJYeRmsvJSuvIyutnSVrMDjnV/5b94T+ZArJ+n1NhAcCPerN5SSTQj/y5wGcnIDNed/AtGSCj5UatHJKxzlBg9hDmbHZgJhSM77PBC5zGawq+V5'
        b'AOTd6iHYoJKcypgqq6usRAZ1FSvTWUCwIUVBKLIayuzmZfLSZaRAt0p0NTqTWUeapHIAMa+0qclITUS/BlvNWaVTliJ1dqsDqnbYTJZy2iN3NfIounBRTzAj052jrSDK'
        b'kO5975Y/0q6zlkMbehdaIuXlRGNoI3KJbbGDzG6pVVe2yGC3KdKeXNznYTZNPsmLusiL6RnpAn/FSMtpcuriUPyTjg5+a+G3SJq8gP6VFzvN7vzmd22lNDnRd8JSUTG0'
        b'2NPszm9ZsvlAgIWnvDjPavefj9+ekJV/oW0o5ZkFeaqEuORkeTHRcfotze9pEE0nFaoyp8qLnQeHC6KLPd04/DfehQqIsM0H5KQiT+Nhv8UBecBkVsDWgO1qK7Oaqu1O'
        b'YkbglPh20701yWyrAvg16H3qCQCcSG5Cesz0EiC62Gr5VF5ZQLfosAK7rrKS+MBZhvlVG9DNAIAFHah2bi29iV5DpINpXWICEmdYCivu3HDd6yH/cqvsBn6b0M1vsFdU'
        b'6QGTlDsqAdCgL7pFsAFh0xhgdsoM8iqg9T7r4YdENg3Vgtj4YZpsHl1Sy6cDUnMhJJ+1eG47ojMBUCeXLJWZYcD8/Uo2g++SWucVS1VltOf8kcrYCru92pYWE7NkyRL+'
        b'Sgy13hCjt5gNS6sqY3i2M0ZXXR1jgsVfqq6wV5qHx7iqiImLjU2Ij4+LmRqXGhuXmBibmJqQGBeblJIwZry25Cc0FIQKdncqDM+l9xLhZ3BDji1bkaVS5xI3vmh06il8'
        b'A6TBEQWiinn4qoNo9NGN0ZMT4G8cExAZh+6UUUl/QbBoppSltziYH6RPZxxEMYqvOfA5jVOVP6N3dD5uIJeeZKlmEW/YWZHEu3QuCP3wB8g92o4uBOIdeDO6w9/C1J6F'
        b'jqKmp3AHCL1EMAxgRHgPJ1OjE46RkJ4J0ute3KEmF28Qp1uomtyoshq3c8wQdEyIb6GT+Q4iHuG6qVBvBwjYObPx1mo6vvRS1wiVM3FDLpRt0syuhkdedhbeIWSgG+uk'
        b'uB3Xof3UtmYKVyxVK7LQHXQIr0PXg5jALA4fQqfQGQeRnfENtHME7sjEW6ZAHSwjQLtYtCYctdELQoSls6W4IUaNN0GTSnQqC2TohngJy8hniIQSljrixeATqA53xESF'
        b'4gMsw2WwyegqOkon9/ryAG0x15eqUT7OGsrQe6bQZbR/pS0YBnY1kzYpmc+hA2jfDLQBb3EQxgq3oPbJJEdwsBpvw1ez8aVovL1khIDps0yAzj6NLjnodTRbZGOlaqgD'
        b'Zi+TzImA6YVvorO1wtCn8VnTK5+tYG17IN/A/otUr+QEodgw0fsppjd+PB19TPPFHwYJ76KJk1Jmfap+b976MdOXF5RMNH71FSobJY4+W6tdnDCssPb9PZG/6xv66axb'
        b'z6779Shpver1z9afGPJqa0GV9flhQ+J0CRc/MeXail7buDPxaC+VKefNP2+s+eDXaRuulfz2xDsLat+c89Wr6X/+u+PN7/dbys+0xGttixremvrtq+mn/xAQeihqc8t2'
        b'hdhO4GVSak+XLsYIgOFUxwiMMXg7VTesxFeKNNkVqc6TJS/FRHSCCLeErqb3gwSiNnyqmzZGEyOUoAsBNIcgJ+FRhhYfHkV5WkE57UsO3lYTnavKzMzRKHGzgmV64ztZ'
        b'aKswvmIOvSRkBm7J1igjM6D9jDBYOnSGWzYl1+uuj5B/994dv66zQTq9voRn3Si3PMrJLcsyZKyE7c2Sp+ePkFy6A3/7srU93VxvVx08Vx7M6xmKGJdRG7kPxDqfPBaQ'
        b'x9PkUUIeWvLQkUcp46XZ8O0DLOXr7KpE626i1N1EsLtFnbsdyszrSRWezPyo3/pg5n0NSxHYKdMTWz8ng9QZzLO9rqBYV0n/khtTDJ2BzvPdMkOnlDApwBoS6y++J+7B'
        b'lgV5YGCiiAlzYeBZhKMP8uLpQ4CrD3Xy9WGErzeGObn6IMrVS4GrD6JcvZRy8kGrpAUe787TopaAx3P1OrcFn5y/RukJeNdpxPuBzy0HAgpzBmwpMAU6z2sECeOglJdb'
        b'qxzVkAr8sq47QaqqLDVZdC4WJQq4lyhKW3nSSiR/t7kn6aBbGO5WExGO/78Y8v+yGOK51dLIQvExbp3XT4gjXnuTL89HuSrwyZMV/4QFqN/m+L3Pt+Pc7s44nq21VBEd'
        b'jpUyrhbf7OiSKsI3mip1Zj+Mb/FjbGBBnPBtBeu3xwRL8f0trapaRPpLYtTyHCd06WhYXlW6EBYehHzfJ4gWIgalJsfGOdViBBBAhiPVFXfZx/rthBtJpsln2xw6s5nu'
        b'DACcmipTmXs3FnuY1z5WEnQiWe9loJ53xZ4muD8pq5Hij8hrXoae/xeIW5MNSwzlTjOd/y9y/V8gciUkx8anpsYmJCQmJCUkJyfF+RS5yL/Hy2Ein3KYnD8pXlIiYuCv'
        b'PLbmj2nPF9UyjkTC8IMsdl2TmYM3KzNd5lH56EygL1lqNbobmKhDFxyE/UEtFRM8hajYWCJGaRc5iNEMXoO343sadVYOMLNd9foU0BrxXXQQNwaiE0sZx0QoPHYqumjL'
        b'y8lz3nlE6p+Lt0KBFtwA0lQQiB5QIYRvFsxH+9FedDSQQWfwVXwS75TmLrHxgswufDzLloWbM3PyNOSqpFgh03eyQGnGTYZBVHyyoz1GW1QO3hJJ+HV1JjoXyTJDcDs6'
        b'WC4SDV1E8+D2rMVSfB1tmSXBzapcELI4Jhx14HMJAnSkvJDek7siEwTcDo/TaxB30NVZ5G7ROEg5gRpFS9HZ+bQ+GT6ucnYqU6nAzSImAt0qxEcF+DZqR7foMr0zi6Nr'
        b'GNu70fByHwVDxWMpuv/0gkFSMcMUMoX4ajRduxB0BN2QkimCudyGr2eAkNmMW/FVIng2ojMQysZbMorHE+lrfj/JjARcz1/OeglfRWcCSL+JyAtC75pe9GZVdPpp3D4n'
        b'mhfE4/BJtJVeiqovkWTjdfQq1hgmZiA6Zv72xx9/fDjKCU/Tf5NmLorhD+fftYoJLxoWa1wp+Dg1h3GQ88MpeaPJ5DRTIMANGco55KbkmKzZAAsZuKkgMh8fVgBQZGS6'
        b'rkZWoGt0BsWW4AUgLa/jQa4B7ZldgHckpKI1WQKGxWcZfBadF1ADAHRSmip1LtKsLnCR+JgedB5vFzKoftKg2YFP4cvoIn/tLt46qkvyzY/EOwokniKuYC5qYCb0Eoeg'
        b'Y1CCnNbi7WgjqrNlqfJyYggM5dKVRwfIdCvwbhG6MvhpBzkbmCIojubv71SIzRPJYnK4wzCFXgN8ZVEu9/zThSFMta7nO31LSwc4LTjurazFHU7FBjXdINCFLtjwppi8'
        b'nPxIZ3We9gz4ADohw1slaB+dLZi2jVXR6kxlFMuIR6GbqIWLQZtRO13ovujIWNgWIOBz/Sdb2dSnqxQCqjBA9/Gh5a5S6LKDlMrV0vt1xWhtibMMqse7oRQ6ZaVNLV01'
        b'zj2+gdHO8eF9cabgpvUCWypITGf/9fKCreNyBZNkG/7Sryp5X07Gt5rL3727Znj78enPHO9gRoZP1kxNejO2WXGD4RQ3ReOS9m+6/va5ij+PW35w/KtvvfAwef4s6zbl'
        b'9W2GTT2P4v9KKMocV5zu2Jmj+Epa3Dvj+2dyHq5+UTriP1bs+luGMWPna4PtzMtHsMH2Zv2DPW9F3nz4RlDr8xdKv7aLprPJn24ZnhG6tebml0XnT957feinr68bPPUf'
        b'RfVXNHd6DKoaczmXm1AwSBV650X7ZcN7Fya+IbgTu25V37Svb5WfnfHnvVFx836hbX6QMgDn/cGwZ0Z9x9t5a9/+4jnFq4F37/4i70DSP5577+HHdTNK15y63ywuyY94'
        b'qc+BL0bNPXP2h6JdtW98P+NvV4Z9ea+45X72ks/PLrz27Zu1ds1nMz7PeHXCiqkXDDEnP7RcrFclKBYULP4xIHymJeudcYpgqhuYMR+1eJiEtPZwqSHwFdxqJ3orvHmW'
        b'1aUU69JCTMN73YoIFh+ghiGoNXv2I4qIAegKsQzJT+Pv8L0+FLdpnEYdeCc6RQw7QucIzPggbxMy2YIPREc5TToCxbj9KQ4ds4+ld3LJ0Llp0WqC3ZUAQHivFW3hVPji'
        b'PDshScPRsac02VFiAKAb6OICNkW+hCou+oZHoDPZObgN1SsB+WlYdHkEuk7vDrP1ehqogMuGQwy4eNcKbjT0ao+dbsFbZfiST3MPOd6AN9lEwaHBNCM6DKjiiPNE8NHj'
        b'wCsjUCM6lkQtUpLRXbTDBrsK75iSqyLEiup8euCtAnQR7ULtVBWDmsnl6E5lC8tI8MU+RNuCduLLj7lJSxH236R+8aWICSHahi4BnCpj5hCmYDVVx3C8KqZLIRNErzcT'
        b'UmUMCUm4EHYwpEZAHLE2IfnCaC6SQ8YF0ZLcGvIWztb28dJydLXLK3BkvBLFQB5G8ignD3Jno9VEHgvdihVfupuAJ7lROYiv0+iu2OCuaaG7nWB3E11aHDM8ijy1OFHH'
        b'fWhx/I2vTOTBb5FTcu8L10X1AfUMPTdl64Oo7kVaL3RfuC5qENcxK8W1gStEVNcipvoV0Spxgce7r0slSUPdL1wP4Rm7X8ULeI5hukLb0dPBFNJY9WChk92bXVaxsJTh'
        b'PzFArgPfZ0PNksXAEqQIQtjUPugApWboPFcxA20rQM2FuHl2Tj6+OhNfnR2cHBvLMIP6CNBatJ2j2D62LKpnvwLcXJgUizcnAl8lWcziwwvH8N6iV9D5UFcdWryBZURR'
        b'LNrb38lJoMOzinFrKL1hfSwzNs7CE52TZrwfH8XHAHZG4Y0ypi/srjqeisFOR3c16tjE+CR0bwHHiFex6GB8AlXmaxQz+evMYa8fyO66znwdOmOqyVkktH0GmWo+f6my'
        b'ZVKWMG7B8LBpZ7bnpn2SP2PS1ND3c8auPb/gqZcmtkSG3AibNWB5wTv3JlmZLypGjmtqUH/94KOPvsoMNEY+Kz+QigaE7X7ph1mooen0xuB+12KGTsopXMSZW7etupL+'
        b'1u9HjVge3FR82DI958y1868POjDh1tMHcrYKbq7r+UrGl/+qmGJOK9y+4vTvLC/1Kiz6fuF/6ksOPZ/12s5Vptf/9FTPv7a+8NrHrX//e+61l0OL5o1/KW9k7o8//OG+'
        b'LfTdyrULrP/MXvHpKGXDzKqIrx9efG+Z6dSN9KVNnw0Y0Fry1vWYzcsO2L9YMUlwbvOyNTf+Kf60n3ZDM6sIpwh6BLpWBkxOM/2MQABg22fY2ehCIMW1vXqikwTZAqKd'
        b'hi9RXIsPD6O4NhXtzCYmhai1C+ECsl2C71ASY1wBWK8en/eNbgHVovtoI6Ugo/GeGLwr5VEjRoExGLdQ9KmMx/tD0WZNrhI4vpYYdFoIzOw9QckKwPrUaHATPYZp1NA7'
        b'6IfgXcLBLHpmDNpNU0vQMUDgtOppDr5ycpX2jGT+Ivz7wPnsBkA/Rm6y97rHHu0voXZ9aAcQtY0a3hjWxrrsJ3ujc8IB6DjaRmkuuj6uUOOyjDTFOW0jwxcK0NkeM+xE'
        b'zY2O4oMyF9FFV2f40P6r0HnaqcHFs4DbJmaRnnaOoYMFTwPDeJzOPlorx5cmDNd4WFMSojsU3+CnZC/Q8u1OijOUc6r38ZYQuuKLCx2uS/cFTBRaQy/dLy3gK24fja67'
        b'7t/EBy3OS1mXoHu0qCaCCEgw0rxMBToGLD3aylXlDHoyJPy/dY+/y9aGv7WfEqx2N8GSxIQQlEzRMrlunBArjvz8KOS4HyQC7nuJkPtOIuL+JRNzD7kA7p+chPuWC+T+'
        b'wQVxfxdKuW+EMu5vYcHcX4Uh3NdhodxXYWHcl1wP7gthOPe5uCf3F3EE95m4F/dA0pv7lOvDfcL15T7m+nEfcf25P3MDuA+5gdyfuEHcB9xg7o/cEPEfhENDuN7QSBgh'
        b'fx4WO3z3eboX0EVxOgN4pbatU2Sz66z2TgHk+7lETmQln8WxWty0rMpN0CgtI/fLniO0rL+TljFr5W883sCI7+7/gMEXEK2HH3bTT/DOXXaXJ4lTz2t2ql+sBrvDaqFp'
        b'lXIdOUbw0OY8kQpevsiwzAb1VFsNNmJWyauJnHovm1v379QZ+VKdP3osYOaVbaQ7pcvsBh9qLS/SLPacPA/rfAdxXAvFN4FrbAQq1gI47RJIjJfnosvoEjqTjxrw/cEi'
        b'kMTWCJZLVvJy+S20uQavzcCtsLhqRo2u4vv8p3024N2BlGqjxrkqvFODz0vVagETgTYJ0Kne8yjBv+diA3of7P3r5DCGnmeDzHgR3SFFJ+M9tLR4GN5Riu4CgnwmnolK'
        b'EqUOS+NZgyv4boJb8mvhFs+KKcJnqfyKTmgkLppOCfrMWWjv7CxabBE+CYwwLxZaWXQbHUwdhW7QJFU6ugd8wuxM1JZDhMZmdiBaO9h0/d0HjG09pF9NuJnz0tAQNDFs'
        b'wx/+YaxR3GXaB+NBW99lpJY32h3f9qs/+UfZ7cAAw5Q576/662opN2BuxJz5X6X+bmTfy0caXn/+qaRf/eqbNa81Tzugnj3wfJ+x9TXHVx18Z8+w5ZcTh864X/HP339p'
        b'vh048p2Zb9f++OCS9fPPO9/dIx27+lvjb/O2DPjP3/aJEY08E3BCIaYmhWJ8fpHn6Su+mea2KMxEl6loMxfWr6nrJuKnuQrFcHQaX7YT4Zgci/eMVudwMM6TLFqLOzQ5'
        b'Dkrr+uE7+AKQQv5bHhyHTzBSA4cPoyN6KnDEzAahxlMusYR5GCo6gPiSWvLQMdTkJmhqdNdF04YWKsQ/gUT82DjqbCVks1G8O8yNd4XmcAExNw9nwwUE48roj/j7viIh'
        b'54FGnIV/0v7RCo8/eSOokH2PRVDOmk+xncJqnb3C/7Xt4xnnrdjkVJN840Hsvrpd+ERXt1coBH8QsD5ONLtwFkEfNl0NeTObPbHXk3vAkUGkyTON8ijyFiUH9GvjdecE'
        b'LxmWEkdbokqOUteaqqOUtCEngrT61kTbyHWCerf+W2ctqzDVGNTyPKKuX2KyGdxIkNZBB0Cz6+TGKjMg/5/AaGThArthNAmP0fA9tM8WnQGbZGYGMDFZOdnoVGEGOocb'
        b'lGjzYjVwNRl4Y0D19P70wxjaiUM0sKOyctR4E7B5hbiBfNgKWBhVMToQSS6T0eBrAWgnWlvDs/tHQUhvwq3ojFFJ1QsCM4vWhVU7SF+ok1JbdAA6XcwwS5ml+PIoijbH'
        b'4FuZ0Xkcw87CuxUM3otO4JOm3wx/kbNdh9Sb8/84Lud2EBcX9u6M3C9yX/1d59NfSs1nlWbl1NfUOxqqD2pbE/+zNH310H8WpPTQz3vrwNt7etybODUu8Iu/1CnFK47o'
        b't0hT+mz58/VT2mtZ086V7ni2bndqVtgvds5e0GicNzzsraN180a/9ezNcdtGvxpS9sELi4etX3Vq7j7mOTQ4680RH4UWV+79c/Afvij57rvJH17o+UHktnPcyrSq/ZsS'
        b'Xv7Vj3XGftO064vvrvvDw8LkD06++YW14K8/cC8PT41/b5kilLLrqAGtLY7OKLEpCU8pTGHR+SJ0jqIEfBvXDQN8VIbac50fe5PgRm4lutab8n1FvWNxB76yxLHKqecJ'
        b'RCc4dDQRr+FvVr+cwhD+FyjEMz1BGhDncgMLcSNl4KsiUT1UuUmJtuC76kx44RgpvsjhO0sjad2SiXM1kIhaAvLoVwsY6UQO70a70Hq+7t1LgOg1El1lEF6jIlIbFzWq'
        b'ijKyK+egdUAvUodoFGrcQocVGisoH8/y412bZuBxbCJu4tHscFbE61wORxdGx+TgI+SsQqVWcIAADwnQBrR/BV/0jGUMZdhjBqJNIAyKx3J9EpNpm1FKvFaDzg3VApQS'
        b'EA2M4ADO2vEpmoqP420jiJYJ5mIZWkvmYjLXtxLGQvVlR9BOfJFw16ghiWewKXeN1wFvTwd7ZzraHx0DvRpbCGsgRic5JTra93F6oJ/A2B5YWkg2L0XRSjeKZlbLAokm'
        b'R0J9g2RsGH0SvUwY1e8M/JFbI/yxNtiNUkkd/L31zm8Z2BkvfYv/np7i+Lxdd9nXwONHgtAHuhE6s7b3j76+buDVvsLpkT2NIe78bjdnQCvOfwoR/4eD356P3GxFDPL1'
        b'VWUlJdThqFNSba2qNljty57E2YlY4FPLHar4oRwzpUp0JDzXHvHfrpZ77KJayeHNB4zzU13kzoIgIYg4P3IwexE/ciPFQHZhDgU/72+IUCYIctbS+0dZTBh5Fwz8sX9+'
        b'SIpkQH+WV8+cBvHORr4jaQsJETDB8fj2IA4fQetV9OuQqA5dwLel6CT9XJ6UHMfMnCnEDbARB8YLh+ON+Mz/qW8tdT/GDMilRxcVs/CuAujqNnyfGcoMHYFb+MOhnVMN'
        b'GkAow9DF2CTyPa1r7GL0DN7pIHA6Dz2DGqOzVOgmsNQNmV2qohy8n1pa5qPdqAM3ZioJd5UgzB4EYnAjlzU31xRas05kI0CrXXX6gXb+sxe3HmmN27CYLQv4gDu+QSbt'
        b'lz5J+eeI4xF/3pCtTdYESee1Hck4Xxe34UjdkR2Z29kRPV96do+YqfjnRlGPsR99rhBRVIX34FsR0Wq7iNehU5/ICUbKZerRkURelCe6Ddfn845m0kR0ThkarUZnbC4F'
        b'O9GuM+gSL+ffQzvQaZcsL0odyYvylWg3RVMV6FIIOeglaXhXMSNZwBnwnvTHucHIQKgCJsZQQgwfKBLq7YGEJCNCOPKNDCGgHCFrXe7eTsJOISnQKXa6pnX7uhO5dM66'
        b'wr0dSMmh3CMoJeQ9H9/FkzP08PJWQXRklipDmYWaYzLRuXx0LJJl5HinKAJdHdINksKcf21pnMdNHmPJHRYAqpxesD6wSGAQ0g/iMeRTeM1ckQjCEhoOpGExhINoWErD'
        b'ARCW0XAwDUsgHELDoTQcCOEwGu5Bw0HQWgC0Fq7vST6mpx8H24TV99L3hrZlzrQ++r7k1g79eJrWXz8A0kJICNhb4oYj1A/UD4K4UP0EiBNCiSF6Oblboy2ojWsTGAVt'
        b'wjYR+dH3M3IQR/4K3H/5WP4p5HN4PIWPvuuH7g81MfphbaJWVj+8LQieI1x1wftIPi+8jXK/jXa/ReoV8Ixyh6Pdb0r3m8r9pna/xbjfYt1vce63ePdbguvNcwz6xP3c'
        b'MVaftJ8r6mEIN/TQJ/djDvc8wtSxNJTiCtEcEdQwknd0ksDcBuhT9WNg9ntRk8kAOt8ifZo+HeJ66/vRTydP7AwsAZKmmw6MNfVG73YU4C2a8MaXYvrZRLH7AED0RAcA'
        b'3b64Sv51d54L4g8Ads50nsT33jQmbtkY/iT+ZE0z05dlImOXPNA9mFPBR2ZMXsF+yzHzLo57dspsYvRNbmrEl9FOlZcDvlMYHYi38udkwPY0BjAF5ZKwiVJaj33pMIZQ'
        b'19geX9neVy9nPnL18a/kYZo1aSdnI0cx22NUg5qeC14TKxMcSDx2kc04bHpvM/vt1D++XqLjgma9tbft1QOqp5Lj39Y+V/pg09gjr0vrZj0Xd/tmxsufz5z88ugzibde'
        b'eP+B9uxr3375xr6K8u/GfPx+9t6//5AWNSf7HwGtmn6jWv5TEch/RGjjoAyQotFtdIhQNwEjKeTsxcAp81LFQPKtZHSBqr3Fo3FHJtfjabyR1xdvqyyVanBHbjdPedSG'
        b'j/KHq/vRaeKmzgvpo2Jdx4f8tIzsJ6oYj49TYd5EzwgbcUspIiYhkSo+H+TqM1A4Fm1N5F3vj+ajNfwnj1AzVaI3kRPGfYLF+Bywm8d7046li+jRpjNTDjrLQJ4dginE'
        b'vz6BoSyxSalGjTHA5dcD15tJvigtwZs5tB4fLrSTG5OS0C68EzUuwdvToRpK1KEy1JIH9GVTHt6iFjNjNGK0M7Mnj7mfmC/tclsf7EERxPFBrETUl7qvu7S35BuA7m3z'
        b'iMc6ry3tFFHDqU4hsbvtlHUdtVmqOgNNlmqHnd4b1sWuehq0i6x15H0teRCdEs+prvPqZ8yjtKX3q74+Gde9l0/km1vO++aKSkj3/TrlToIgdcr1bMftmz6w6+rTbq65'
        b'aquG4Jqf0ZXgEs859Nulqa4uPRzs0Xx3t3T1z2k7qKRrxfw1PMPd8KBMV2aX4ee/225gCQGikkqTf7/sLHezvYlkIjdaqyp/fntG7/Z0S/22l+NuL4K2R8yCf25rTm9/'
        b'cYm9yq4z+21qprupfoUko8t82G97/4Mu3hzT/duHlGYMmiFg2h1kQ2qVodXJPEF6qp+YSZ0wiHghKZdPCWVMsrkLRDaiaBr14FXyod4MXZs+0jg2PU8nM36s/Zj5el+/'
        b'gt3P91vXL/VNRjtM9Mf3VylYO1E1oQ3Z+D7gusxw1PA4XDcO7XoMz0vFRffXAV2ILWgO+d5tbQ9PFPHk/t8F3XjbM76uyehW+Sc/wr//AXnLJ3PRXd5yLtu48SLKQq+J'
        b'bTXPq5w+nU5MfdyAMuZ7RICWfSPWVDr3NwJbJJmF2ln815W36uc9uxsdf7gbXdl6SvDSdR39pORLDLPwnriuM1nB2Yk+o2cPXE+WzN964TN4L1kztAetoYJT+gh8DjeG'
        b'9sSbolRqIv+s4xKywh4nw4SWUFtoU62hpNRcVbbI/Yk/19oOnF/bz2PqvXN7fatWRI14u4szrYyXhmQ7POZ1W3JfNib+2/XarK5VJ2Dm+natANZd8L+77izj++iKrvvf'
        b'o//Ofib4Mj90prbkZWCjeBXsBXSdnF4JGXwijallaouGOYiqJWKEAJ2BMQ9kljPLV42hhrH98VW00YutJB8+jcwFXmqjimUS0SZxSCraTm1JY5cTY5WLupCJ2uwX5+Uy'
        b'1DTyk7xc+d+EDcHUNHLeCFMV4yCfah2Pz+tddz3xBpKL0TmnjaQTdLyueTqC9wThvQBKm6xroDivB9mAbpS45P1KfD5ByAv8BQLTy9eqWdtGyPPj1OCRL8eFr4uNEL52'
        b'Zf97h4R/4tKqpdFS1TfC39Tcr86eNrlff5O16U/H19nTO/5lTPh86TjjiOdr2l5avyGr6oO4IxOPxYcELrwTiKdeld5/6aWvezi+v/XefwTuC/ztuadWfjBy/+ijf1mt'
        b'+o85YfsUuaE7ls/56LUL94+9fv5rrm7A9Pyxr99d7Xh+6MbENxS8dyDaim+jOiLca4Z66U3xFtRB2UXUEos2P2LYtxD4ScLIXh1MUSS+X0r4YJ/77bipC0UWo8PUTmIo'
        b'7pBJo5zcrrvWIahDyE7CFwZl0j0MG3IL5WbplziplepZEMxd21jMxKJrsei0eCA+oKaKiHF4xwTejmEquqJxGjLkVVAdRj5q6evUYOBTeGOm0xxhAr6ncH8z3K+uVFyy'
        b'xGpyfttV7rHDJSVClmMHA1va32n9JoM34d9rwzz2Hy3q/WlqnbXc5oft5Kw7vDd9GzzmP7rpw57xddL1aKO5ZUKPPel1nOz8MjF14nN/mVhIj7dEsN2FdLuL6BYXrhIV'
        b'eLz7Q/OibttdzKvVhqN9vVAr3pUJrMEQZkgYuktlXHr+a0VrhkXnq+ag9eiYihimBPTgBg8tMr312aucjdyP+XLx90Q3thW99dy7z13cerP1Zt3N3ekbFLtLeg7dcLPu'
        b'VN2Y5symobvXdoiYMyaJ5VAl0Gyib8T70IYCkGCI8T0CaKE2KiwzoAI9gw4LUQPeEORakserycUl1LGDLn2Yx9KHmIVUP+U16zQrrw8Xe1gI0u9LU9WUN4Y/JeRjH8lJ'
        b'l30nPEyPLrvPb/1264D/VZ/IUENCpl5MdRFk7QN+5to/4eU7olx+kamrOFo3rUA1R4V2soxABBLlbTZnaG/TPza+JLQRvXre+ikPtOePa3SRhshSDc+NaR9oTcaoP3+h'
        b'/US7yPiZ/oGW2xybnOC4fCzWcbHm4rG4TXHChOrjLLP4iuxPbFsX5/pExi9eXxcnCkWPNY7w3N5W3jqIGKjW9vKY5q4yfFW7/EPSbveKEqf0qkdXtG+LjxX13dQn5KjB'
        b'/9qO5Xe0yLmnRf8d69p9T7vWlR4THsDHjOgSPg+Li3ckZAgYUQCL1uG16LJpZulWzka8PbaIBjzQZtKlndBGFjdD96lWrftY+xks8GfaMF2FMbssvIxn4U60Bvw94m3Y'
        b'wqTRQnQwz2nTXYfOL2BTlrk/7v4ECxtS4rxK1WNtPRlvSa2QeIr39ZhqrwIutYX33uwUG3Vl9iqrH+QttO73t5/3wWPJo6sfUe9j9f12SRHKmyN3WScTw+TO4C6ZfJFh'
        b'WWdwTZWjrMJgpUXivIPxndIycjWNgXwaNs4zEN8p0Zts/J0yxMi5U1Sjs5MbiA0OO0ii5KZcslU7ZYalZRU6co8riSqiOYk9VFxnkOtOGJPew5++mOawm+xmg0JCz+Ws'
        b'hPRY08nDx83IuZ0S8lkRUmWnlLy5/NhpNL2eirYXbz1Kag4g7pSlVUupy32nqLqiymLoFBh1SztFhkryZVyuU2iCkp2CUlMZBAImTZmSNzu3sFM4JW/WNCtxUrJeYR5R'
        b'gpClJOtLYJwiKOdtyGJqgc3WS4ySn8kfd7O6Fjir995cZTx/vNq8kv229mOGidUVvz9DwyPRDLS/nw1fCwVo4vBxNhRtiUpDJ/mbR06WLrfZa/C1ZXhHKL4qZZkAvJcL'
        b'wXfwMf5ek9vopiyaWH6ei8zIUWfm5OOGXHROiVtisvIzlFkxwOoCK6ZA16ozqW8Ubi2WTUE3p/OmY9vx8XzcGoiu5UOolslZgS9Qr51irSSB2GwQQ212NINa0T18lBbB'
        b'R0H4Wp/AEbcvfQKTgHfhu5QVeBodMSQMXJAYyzFsJIPaSlP4AewYHEutXVX4BLFUYhlpEYfP44t4C20pDt9FmxPQVjYxVsywCshfgI/Q07UaB5ByYsybiA/lJAkZEb7E'
        b'4lZcb6MTOWVRFFM48XkhE6YtFdYOYGhl+Ai+JE5YOi8xFiTMKAbtxIfwDXqzCKpTxmrUKjXxH8xR4c3xeH82y/RB7cKJaN8YWmNYxVBmYvY/hEy1duwLY8fxNVaQW1cS'
        b'8EZUnxgrYFglg3anGfi7Sk4CV9waTe5SyaTHY0zoNBBzmgWluB3vpzX+dVBvRikUihm5duA7prkMncBAdK8gQYfXJ8YGMKyKQXvwJRt/b8s+tAtdBCZWSSxchErWjHej'
        b'WzK0k9b1z8rxzAo5IIVYbfznocsZ/vhyC9qIGhLkeGciugiSmZpBe1E92snX14y3ctHoINqjVmTlgOwUGMeh3ejcJFrfD6s1TNv8bA7mL0gdn8IDohJdrEqAHu2B6mDh'
        b'Yxi0z4L2UNkHXUOb8RZi6LYA78CbqMnCRm74UryeVndgFchCEa+KmYla2berRvGTh04MRAcS0C18LDGZoZO3o2AlnTw9OooOa8jdM414C2+vHYK390LrBeOr8Cla453K'
        b'MUy1eb6Y0WqtgxbP4SVJdBnvjUsQ9ElM5uhod01bxB9BP4P3zObry3UeQ+CtaD1AW3/UJkSbg/EmOvk90R3UnrBsfmKymA5vdyXaRc96UfvsZGd5fjFD0DMl1YJUIHh1'
        b'tDt/sYczI+b9E0iydsXJ+BJ+gKvQWrwpYTo6E0+AF8a3E9Wl0JUpH4D3UOAdi/flJHEAvJdZ3NZzOQ+mTehkJhS7nxQL0xIPxXLxOd6c8nhqSLRGOTodJF+WEZu4fugu'
        b'uunyspyboO6XQoqkQs9Hj+Rl0hv0KiOAwjhDJt6MLjCMbKwgrAat40XvKyvKEyK0KWRXphHoOBTAF9sNcKahEzUV7wP8cFrIyMIEvYwRdLSLQZQOM1sDYPLNZRMA2kgP'
        b'8JpSaUKEKiWRoXXtccgpnKHbMKnXoQvws43DLRoAjTJuQJxzS+6Kw6cT0M3klESAqHToQhLid/5yfDVHg2/31JAzCq6KnQi7ZzvtdDm6FpcQ40hJhE6PBRhErQIqUeCN'
        b'EXgPCHo5IRGwUk0wQT25wLKZtMdN2uXM32S/CAB47p1aPJCHZ4Cys/gq6iiSxCaKGHYygw6FoBba636R6DZIDlnkEEWA77ErQOjdh5/Bd2ltB23TmSb9PRZ2btT+idH8'
        b'UArRxTmoYwC6HZsIqGAKgw5L8HV+2epR02gN3jMOb84GnuZpNgbQRj2t6XRyX9iyL4hgJucvLhrP92sqPrVMA/K0iBEKWXQcX0KHeuP7FEI1o4HLIpa8ICEfUjNqWNLj'
        b'vAndVXRdTH0wZmWAjKyaw1vF9ZiCG3KUgIEYZkZ4wAC0NZyubz/9KA26hQ65HGjJGc9uDu3Ire66EjswgmOE9t8LiWo1PXAWv8gicndVq5jYzU1WMkq8bi7dYPj05ECN'
        b'lxec3Y5bgNIImZHotMgxAdU5nOZlp/BJ3JifBPjxeCzeDJgsnF2ATqK7vFFwO97VQzMV7y7EzQAPeA+DLwbisxQpzHhqgKfzN95Yzvd8ZJ7IJCvjfYpnL8D7pAwzLwPd'
        b'Y9C97CT+rrBj4UOjYTJy8JYMVRasKtpjBZEwTsiMKhTFp8TQ0ZaE92cSlUtEACADkwbH8cgYZn472o/3wbaelozuM+j+/IX00x+5aH9P7yqfGUKq5JhRs0UJ6H44D9zN'
        b'YahZk16cD4SVOhbfxbdH8ymNg5YUADFuBpK+nEUt6M7ABWreWLFdMkQDk3NzNj8Dx4gN9VV8lTdT2DOnVsM95e1ZzzJDUKMQX8Nnh/JQvRdtxMfxvmByNfYSdIdBdxaj'
        b'NuetaagDHyT7Wp2ZC0UzVfjGwnghMwDtFZrz8T1+G11EF3Eb3geAgE8AabvLoLscvkh9zQvwBXzKs/x0dCKeg/L7hJWAyej2TKvBh3EjHeQyE2MC+O2ga98jG90hdpvu'
        b'bodORh09BQtZXEdBazA6FoeIO/j4uUOYIUDc6iho2dEF3B7N30kGcEXEemBvGiNZZiC6KsSbXa7JqANtQHV4n4gq4jaj2wTzbMC3ecJwDNXrcCNHpqBoEbNoMLrNe/Tf'
        b'w+vTNCpVJjqD2tHZyCyy6XpOFOA2dGIIT6RaM9FdvE9Gd1wTusKgK4uz6B5aiDZXeDnWoN1FcwRmtLuQTmM5vowv2tDt3sHBgKdgA0L5DryVAtvEmVImwr4RmAqt+fxw'
        b'C7+1pLDM53EjTIBgShVTNRtf4b8yc2JKX40F7yTeo1syyLVvKtpL+QAhcElN+AZVa/5r+Ej2NSgqX6IufH3p8dIZfJ0DC2EuzgiJkQ+ur2Vqx/UxbfqdmbP9A5jegPNT'
        b'FrzxVNWbE8MCvnzb8dmIytYbR9bfGnjk3X/8evLanTsnF3/e8e7cpd9qMl7URHz4+rKh8r/0/HTGl6ui74mHMJu+WrroqbFTX/xubPrBz5oCbwl//WZdvP0+VzV1iuG7'
        b'qcX9o3va7+4etvfYts2/PjxOeUQ44asyw+zGQ6vnxk3669u/H5XB/dDW47D56nen+1auKBz+ii3+ua/0U3dfPvh80qo8kePMa9Xhm7M7Eg981mOP7u0H7SMvtxh+kzki'
        b'/heXf/8iu61OWb//yrSQPlGvNg7Ujfn0T7tfWLzzvZC8hv1K+9KsP9mPvNJvW4fyo/37+9ycedKW/6dZk9SN83VPVV+OtO74cG/ryG0PlClny8sj1l57cemKxpTh8R9e'
        b'GvxdnD7L+qpSnrj604btUTvP9X9Q0vYwyJB3u+fYl188mPJt+n6UlZa+ZVH6wpmOb1I/7fGLb967UVB2puOlD/t98/SmD2oO5qfcib6x45Wlba+kPrvwj39dMvw381oX'
        b'Suf9Lv/7ae9uSaqa9HD1b86V/v75QZ8sHzfunT++9EPvOYvnmocnnO9ZWvCK+atB77YWBy4u+dOkUUt3f7M9+4P8W61Llb0ORkSN3fFd+T/3TxnbRzFq2TaNIGbatcpr'
        b'p4Y+nfld2u9vhVX98M568e823/nlq3d2fSsYX9Scp/6o460+43/9h6fvr5KOKVZ8fmbqe8azuzIKTuzJvfrwgyGfffJwwrxNip684x2woe2PuC6jjQM9zA9wwzg7RYJr'
        b'n14WPcCYqyLuFnvZHCC4W+m5icoO2KCRiBNiRjgVkHUAuivhXR8CgvFR1BhaLbPiK6g5tCZ4WnagmIlAhwRVaD1uoNpnfAmkkzVSdEqZEZfs0gP3wLcE6FyIjSpuE1Fd'
        b'WJcHGjFauwdM9SV0PJ+3Vb4wF7BEY74thtjJUkvloxxqRE24nbddW88CYWlEN3PdSkBJDqdHF/tS7wrAEYcJMtskySNDq2En1aLtVJmMW7Mjib95Md7WZRGXkU/T8tCF'
        b'xU5XR+LneBBdRpcznM4c8qVEZ40uZOM2jjcK4XoALm7mVenrFuImD1X6WLTNZROC9wyns4bPrRhOjTOMsY/YcKAjyaiN5snBd1ATzZSCd3obcaCj7FK6tsDu3l5IDEbI'
        b'SQZIM9loS+lU9xxEjxGhayIjNRpJ7GF6RFOK22dTZSlRlB7GB+lEx6Ib+IaX42MIxKwRVKlW88791yLEiHghggjnZTKC1g729TWAn23c2inQ6Xk9zlJ4uPQ4zOpwdW9W'
        b'yIZTl3PiQE686Nw/XDjb7QfiJJ+GDBrhvC0wiP4S9X1/Ts6G0HRi+EzyhpHyXBgbAe8cK/ksvHdtcJd6Bvrjqde3El3cz/XD4/hSXfr+q4Qh5Fz2L2tdP/3f9GUI7dUX'
        b'/+fwVDfIfxOLqRe5dYMsVV/89Gl8ha/jPTnzqPpiNK++MM2n18ws3RCozW4eNZnhFYZUPHnGBIDbKsqCcoOZwQHoKE+XrxdFoFYQzNFaYEqZfhEgjxP1eIG6IkGI9+F7'
        b'DBPPxC/qQ2s/GyMhh8apOyu1spUBKoYe8s3MCiSRko9M2uz4/pN41nX1It4irX68Lv2ZYYOcosYmtAtvTsD1AYmEIO5gygLRfl4KOoEu9EhYmpgoJnf8MAbcLKHVjB1P'
        b'752p6DNKqzwm1vB1/3JmGJmAvuparay0KIPvxexQGhn70RKt7JNJ0/ici2qCGUALfYvmaJVL8vrxOdlyGYmUPDtba/7UXMzn/GgK8AMQObmvVqlZtZzPedFOIysSB2pl'
        b'z08v4SMj2QB6FY4jSpv9a4WUocLK6CB0lXKTsx0jCcstqmGBud+HT9DRBcxALQmxuC6eKGtGMGi7IZw2ujtuODG3i73Earma+CB+nVbie4DDzgjxnhVE41MrW8bz5WvQ'
        b'VhCI9gUBY7SFSPtE4N/Xi9Y/dn4G3ifG64j99HX43xdd42f1anoJbmVlwIkxKkaF1+F22u4XFdSwcGLuRK1sQnYeQwXsKMDzDbgV74CfI1a8A8QxvJFBV8npEA9Ad4Dr'
        b'u4pa2WWzGWYQM2jGTF5QbbHGuI5ce+FDriPXStTB88K30cHJBSp8PIRwaCzexobLcSuv3GqS4mPR/6u564Br6mr7NzcBAoShIio44mbKEsQtCAiyBXGghUACRKYZiloH'
        b'igMH4kIFqQNFBVTUioirPad2923VDpvWVlvt9K3aWrW2lu+Mm5BAgmj7/b6P/Di59+bes+4Zz3PO83/+FuAQPEKAP6ACLiMpKS1Re6jDaVcyzAJmwdD5pEmG+UeBOhbs'
        b'RN11EbModRzZ9yXvZMJM4hTBfm5Iquj6yMl0sfnO+l7pzI8fEGOGpMvykozdjBK7+Zy+uiJ3U3QM9LZfOXbelSHRS68ERFjePn27Z8HaV5gHg+Lc4hwskxrWlinYa5pJ'
        b'+9xL4RuW8pXXrv02blHGK2O7T60d9FGSY99bYYlu3Sr895fHFdzwjd9ZPfuBaK/d/WFXnyTZDa/9Kqm7++M/nFZM1iQvFhz4uC87MenPXf636uO3HzjBO+lzMuK9Xc1J'
        b'EVETa67ynaa/e8r7z6u/l1fv7SvJc7m44s7jgZO+LR/f515myB/WP795W7BX/c7THcI3ki4lHfb4MnvQ7JV2Hr/G9n49dM75wznvXhxSMOvPJ7slJd0GPYqcuHBVwsSw'
        b'rhcnfBi0quJtoebij5URxX4vpWdYxoY4pAR+OL/p0KlNJVm/DZjVN+m1yZ9d+OPBBzF2qqt3fv56bPeFRe6juyV99s3UnOKWe/xHvy25OzTGtSfZCc6ExxPb7i4jPbyi'
        b'rQUOLIeVZNaHxbDBnVgIxHj2n+SGp6JTLCgHa4IJLkcGqoOoTOEHd+hs4aNgI5nd/UFdd2oeCatAGWfx6epD5JVCcNEDT6rRWAXFHpzZNIzdD+KDo7HTyfy/2HcudpCF'
        b'0u5tDUt4GKA0AFSDWhW2YkFKXhPc3CpxoaZ5qq3FJ9gCzhHRahZvHs4GPJvtjtcfjvKQqFIrIQVQjYMERuXmaQYPas1V4HJQQaZiH3DAmqNx8ohBU78yH/sgmC5wBlUS'
        b'Ij90AQ1gjR49EyxJhAdxOQbzQf28XhSUivrqYWraCmv7cIKMGzhCRAYROFdoYGZantIqpSBdtZHKZs1J8IyeyDCwD0WWwl02VNSp9OulZ4c63LxViIG7wFlqRHsQrsFc'
        b'UF7hHsOGwY1e0ydNRvmEh/lwiztsJpkhI8ZOyvWkM4w93EtrG+viT7FYR3lYUEQ3lU4GZyPNGAGLJLdIsI6WNgDUaM0DzvXVWgf0siPGrlFgBxIpYz1BmWlLhFrz3jIk'
        b'nZHGV7IEiZXriEBqE60TSZPhHuLcIaBggqFYRmUucBhWagUzlAeKENsMDodjO1wkUGGvGK1muE19SVPNFMdQf0n58BR2mYT9JYESK61JQ6d2ygTYlI/IVRkGcpVIIeCJ'
        b'WOIZAck/WKpyQB9H9OmJPvjcFoUs+WeJfNSV+lFAH8Ft896CW1Z9hKwVz4p14AlbrPjYOELIYngZklxsWyUXnLyetVsHeW41fmtEwS/thSQHY7upbZJCdYMFEvS1iXzF'
        b'oKMKfNSjDTSMWPgqFuKAWP0Sc2BsCawRai1CtUd4v4naURJMGLbTInYbZBefbPyS/T+NKCUuaEpQdErijLjQBA1fKVNpBNjLgMaa+yEhNDGBSICkhFS4/OeeMBSYgc4D'
        b'V1cTg7e27Plsl+eFgNmaoX8bB3N7odCCvmNzYvBi3uYjuM92EXC+NKz0fGkIzdknAgv2D6GQfSy0ZB8JrdiHQmv2d6GIfSC0YX8T2rK/Cu3Y+0J79p6wC3vXvCuK7b/m'
        b'v9i62aL0e5r1DCEiwjh4ZLD+TGDG2Cfy0ehRPDN2cLvtay0xjXJCW6ZdwVY7wkBrp/2Wsroj/gYLS4F0EJKWMVrDLkMgtZAKday7llIrgtURcay7NuTclpxj1l07cm5P'
        b'zoWEldeKsPKKONbdbuTcgZxbEVZeK8LKK+JYd3uQ857kXLRVIB2M8yXttYvdao7ROHNspE69mD22GG/CnTtrz3ug//28Up50CAdetyDuoqxX2622z7Ak3L2ESxf9ZkmY'
        b'cQUE5yOcaY/rQ9p/A2811RJEq22QjjBAOpCw5naR9ib2wkM51tzImNAn5QY470Qtkyv6iVLmil0w1wnms5LkSXEfkbcl3DQ4cUvEcHOOwgod5acp83Mw9zZGyWMnxZQ6'
        b'FDtJlhWoqJ9uAplv4ztagS1XXS00lhwXG2Yt4g7JjrKQ+k3F/EXSjHkafnYeupYrk8rVueiasADlfH6+Qqpo5e01Sphr6JhL6wrdEmlXVtw2sbXOMVdnKXMzXPk373ea'
        b'MhdX9AtT5j6bMbcdO65RbwEvyJir90J0+cDO1DvIBfrZVB7yxJKcgiyJp7GsjBSnZ6Ek04nL8o4JfDvm7zXC1fscNfJM/l7UFql355CwJHGOJA2TxqNDfYfZrsPauKKm'
        b'1HNGc2GYdVK3Lr56VWEk81xGUH94BnuwKaZg4+4kTLEHd5Ip2GikrezB/4ApWNvnabXTM7Fcyr0wv2e9MO1Awbn05s7EClmmXIlqGA1QaBwjzclDrOZemzoPu9Z+IUJe'
        b'O7qwcmUYWV8IfK1AIsofO4HaLIPdcdiHgGlGXiRiEs5cj0CtN9eVE0T2oKI73RJ1d2CQYiK+EZ3dO3iSP0MJaM76wJqO4yTkNOGFcIuel9jdBSK8mmxLIjZXkSUOlxs2'
        b'Sz2Geg+gvmeR0lE9Thuxjdgg6lZdxIDjFzSBNdZgrwi+QqK18KNegF+LyxCd8U9i1L7oYqh8btvcdhtBIo1wT9CPaxncaAm2DQUlJK7dU8mqkfdHw9Q5VqPjaNnBUXAU'
        b'b13R6GDpdP1MwjU6va9tJhutQbUUrCURv+xlRVZy7qUrPD4rmEV5hEHZS3CZNl7wClytH7ELp91MNoi1GdRZwzUsOCJ/L6qUp9yAYvm07qzn+2dt2CBRaPyiv19ac2iZ'
        b'k0uRozDgyze6sr4hZqKi95bFLEiPzqr6M2fd4Or/VEUHnEhTvHXgr/APNbfhOn/VkpM21nlN/qC04VbAQ8kv1SO6RIcpgxPOlXz9YGDhvA/vWY2HlYtWdW9J/P7gT4OH'
        b'dd/q/u6l9wLG+8+vV1tcBI9gPgz5MfjXP/g7hCOcGxSuVlQnhkVIIdLTN6N4Y+YQfXMk2EgVvfVOYIeBBTk8M49b9q4GF4kf1Wh4GruijTVoYthF3w7MqrgSHosCp0lk'
        b'2Xi1HSMyqzz12gynvPoHUc8ZK6e2cgMjtTIR1LB+Y4YStXp8LliNtU6sVIMLzkSv7jWLbhY0oFe7hiqJWEMEjbAOa4leSpJyHiwCdfjXaeBCa0Pg1P+hMnJPD1APV2CV'
        b'rQru075UrcLqD+qpYfthGxWKptYOy7Ge8CRsVBJ7eXRG3CRGeJoz0aDYAlQtLvjXdAAdrhL7iGjV8piltsG2HK5SSwhsxdEC65/p6IGR6GGcHvg1HLyOA4ADiIM3cHAJ'
        b'B28yzLNJdISdicTGoEiufK1NflHrR2xssbx99p8HKGeVopOeTILlpqK8UChma1p6LMH4UgcswZ1HYxZrSVv1RCmTmZquzdSTvm1yQASDFyMJtkzRik0m003WpduPpvvP'
        b'2Ik5NKYgBQlLJtN8SZemM01TT6B6MWJcQQqSiUymJ9Gl59IqNUnaQl6fnwFZBz3VyikmcyDV5cAJr3LoiTIvWGDLFJ0WZCrNTIM0US3rBCC9NF1ZipomqyY6O9uYdL5e'
        b'VrD9Ou7DxNB2MgrI/hT2SsFyuqsVcXMsyhDprNnNOmXNjimlzLp2mlJKhgk0O8soRW5+HkIpfQKpdlFiQikdsNnNQ+ymj7BG5wS0jW7Sp8Mhwi3NBmYZ6bwCqEtolDgh'
        b'PxerEVTnxl7iOJi0JC1freJ4mpRIYDVVN/gPc6LIcJVI5RmEMUfFCeSGheLqm/i/RNWWyfnAMyIL478IHcOTpCPdzidAT6MRu2hpZEzrNvr1SuX2dh1V7BKUppClZ+Vh'
        b'BhtO0SOe8IxmtLUdKJXyzDzSFChPTDuyMqVYrl8qOdJ5Mk2Q0Wh1GR/ykgNG6lQanJKPqwdeJdFyHOM7dCTH6aa0MNIq5eR5zJmF6y5wZOc5tzIMC4RLLZcp/z3GLBfM'
        b'EEW4rVzFbm65WM9GxVng5vbCHFpiF8KX5Ulpp54n6g74sjr1/POyV4lNsG6ZYq8a1rlsGCBAOuSwctFxWPm4ipN9fE1zUOmjSLjXqJbR4sjzSEYJF31IdPSMGbhkxvzh'
        b'4r8CyYJc4k1XpsDTlAchqNOpx3oZ8u04Qx0SaxkultDe4qXtKUazRYUhfToulLyft2lmNX3MjXbpSK+boKuoR+Yp5TRT+RnGicqkc1DLIPWBHyAuhSWF+LiTHE34L8gg'
        b'EiVZNZOnZ6nkhIhL2UoT177PmozTU+yD2a5lajS46iJALVgu5qoIjVC5qMeFTvVMlKjSZHgl0jhtmKcYNRfq9jRHnZstyzJe/55ivza3kdQk6oyFapUMzRzYtbQ4KV+h'
        b'JJkyEcfwUeIgdUaWLE2Nux56IEitysfzW7aJB/xHiSPypPJ5ctSYc3LQA5TMTtmm5CaeDjCW5eevoBHGopHrZSv3+bIVaCy+56uXkaQiW6v+GTVv9GIibcl4ybBNvp+7'
        b'JeoXP0OBSuOC61aXJ0naQnWmq+nmp/+4eMRg0w3Q4EafkabuRM0sz6s9Tyj90b9tNAGmognoKBrUKHTl6yCOQP3bTBZtpEFkRsplckLjMIFohOOOiDyAZFI0tmqHcpcE'
        b'OseanLBbIYeYrR5NhfQMyTgukehUlof+UTMX4zkosAPCex1Y0TAa3zbR+HYYDcE1GpApuhAGxRA83/ibfEyHg6SPhk4lIzW+IHZBnZxr4ui1m64GtQKTSqLZYiJ35CHW'
        b'k+1Cp04Ru0yD+7MUqJOivAw3nRU9CGZrZLrLXKa0USmz1Qpl+0x1JO6ZEi+JKNl5yU8nogUZrP53ToYhoNJR4hj8JU729Z7d+cd86WO+5DHTb0OLVuVESO4cq84dtQMC'
        b'ZUWP4C90Y/v7TI9i4TKFIs8rTCFRoyBnmFeYHEl3pkctcrvpsQrHY3p8wgmYHqA6ShmNSqFZSAhDY7/poYnkDclsUuPZMFV5SIqVyVRYssDfSMAK6FC+S8svHCXGG8lI'
        b'fsrAUiu6gOrc9EvFD2GMMH1KkiPGJx0+kS5X4Q6Jwg7FPQqMxnfSAxKxB5bTPf18AgJQSzOdJ4xJRhnCXx22yAwJKm0YGlQ6uomgmtEbwl/i5ADTN3LDnJYvtoMWrcVb'
        b'jxIHoyMqCSf7jujwfl3XJo8Y7u51WN9aFDf3JH0/pgdrjN1GIlpwUAx6PaZHxDR5OoowYiJK2kiPbIe8xnv4RnfYbBIJ0cWEOF6qx9uJMxgKDzoOTsLTkQYouVx4iAXb'
        b'wN5M8phtBCXE8g9KjYofzueArTsnwt0UwLfEG0P4do/l9rC2+fVgPBgmfK9Xau9INwdqc1sYNRduMYOrRhB+DsxGRwBNs12cIlsxXtYzWT44D4/mJlHcoHoxtnAOH+Qr'
        b'Gf0g5CVGjTcXeo2B9e7obkybGIutCkE9PO84OZo6ScJotnVTmMLhlpmwOJ6ghlYExrBvmDOFDRGezFc9E7wUdL8KU/fVG3pDoq6QcDThdJsiSRygTxO5AewUuYINsJks'
        b'GMpLT+eyys/R0YbmRHXp6zEg1b4482HLF1MmpJ/LVt1ndo1Z6HvT9d4N65xBwcv3B9hXfLpiwzuKH/2W3Q+6fuXk6etV+RlvNVm/221q1EOXvuv7JdgMnTln31xz59NT'
        b'3ve89vbmm/s+upWcETjxqnXyjx993aPnx/7OOXf9z9aMXaCpLh3jueu2b9ZxUcXpv9Jsqi999lFDze2fmzKPn6zfPfOnwoGXTkSprmz5ZMPrv25Tjp8FWkYmKIt65Nwd'
        b'8O6DxzHDgxMvDzn1wPb3pwm2Y/Y098nKL//xwQfJf58YeL2u8M1Prj+9+59pS08WBt9QXnYVUoO/1XC9Wys3IShl4U6ZJ9wMKsmGkyUP7uTQImD5FEKMBS68TLmX6sB2'
        b'WOEOS2IjQL2AMc9hu4LTA8AOb7KxNgtcmNjG7xJYDXePEQjN4D6VN0OQ9odBETWI0ttIGoheTru9JLAbbKWMhetAKVhu4H4JFMfoPDDBY8GglNheDrBQKCfI8QtuS1cI'
        b't8BdFBe0fxaojoR7wJqoCB7DTuG5Rfm1R3uI/iX35tgyjuxhheGuvFT/I4zF+A/sTG8QwXJQ7zzE/pDsX7E8J/ItXMa2sGxv3fFCkW6rRgfn4Lx+tK5fY1tuvc0ry+fK'
        b'v6tALxISpyHYY46xHawBm43sYBlk1TTag/h2whZJzGqBzrfTc3heVMxFERgMmrgY/doNmoPpoHlQRUz5hRujUqOyUxIoelk4YLRyMNynjvf3xhBW1Kh4i9W5rVAQWN0N'
        b'lFnzhV0YlJlpcBs4QiAGluZsAn2CB45gj/GY9q/BjNIXexM8h/DAOEnyCesFHDj3FWwJ7odBG+6wDOM2vGZQjPRYUO6HMR6wVIRhHqAKbiLRbJ9NLAgKPYakiq6O9KfY'
        b'i4iXu2DTivBHC1M9TihnUpN+aS656PLWvNSo91z70Tv7Kwmew6VxVqro41kB9M5jbsTYIXzkS6miZQHu9M5tw4gVQLhjj9SoUfNn0TsfFBI8R8/GHqke3fv50os7GILn'
        b'ELZ4pYoc46ScG4PNTGRCXFwcw/D8bUMYUOQjITWbopzr542pE3mgGJ6F+xlYFAo2kDLHDXFKmAQ2xjEYpFeDfpgNmjhPPaAWvpIAGicQgIgOHjIRFJMHlfFguZ8tOOWt'
        b'RYd4gHXkNbnMAqUJjD/YhArO9Id1YCO5bCmBm/0EAXA5QebAnXA7ybIDLAdn4BaeJJqAPdAwUUQdJzSB3XYcroOAOjbZEFwH3AtPkDKlw/q8hDgxHwN44Zpu3c3BXgtw'
        b'jHO6AI6g+9a5whNaH/oU3QFreBR9geu6rwsx5Uh9Mz016rv4CbRaV9kRqND0n2SpImVhNvU4lgmWweIEuBw24qpl4ApGAs6DRhJLUUJ3bAzjnTs5ddaAUYm0JfPBTngy'
        b'IQ7scWWYUbB68WJruLdvIPWegWZXuE1p44eqjYUXwQVQx8DzYKujvPu1UJ5yMOqhwgeLczdFYqTHqsxd+6OfRM2suPKr252bAo8zvOx540Mc+h+QrLzVUFKmECX3m/JN'
        b'Vu/93+4P8XCL/PSv3Xf++P7+5MGyRMWRRum1K/yxT7fWDjni9vea+ZtCEn0KIw4c3BafNHzrwynNQz94c0Xmy4+FvS/Pcd7zqGZt8oPfRhefek8zMdH16iRplVV0cZFM'
        b'FPT1nNBg8+Cw4Dctvjnj0d26Slj1dzVcNbnvG57//euVTbe8dqif9PntnL2/b/qu6b88PnjPK35LefrlxMBL+w9/9IdZ7veukiKHyJEHTw3NT9vJK6r62Wd59671J0/J'
        b'ttx4/4SsZnax8tvskshPE/9qjnjn4s4HBf1jtufaNY3y7T7tk96VNbUb7r1adffmhf+A8f08F21a/OXbw37YtC/Hrih4LnvA0dVBhX3/qMAOcKDdXIbOZoDK9nNZPXXA'
        b'fXCRnXscPE9mSfSzEJ5lwabsGZTUoHQJOIcEoSgeI0BxV/TnoSdXg8106m0AZ/pHwsqhOqpdQnt4REwMSF6WuuqBTuHRGRggsnSBChuFwj1icCESrGcMfB1QAIc41Mwy'
        b'mxLOTINl2Vo7E4cQCt9YmUaBERfBMrCeAjgwegMWwUaM4AClc4h7xAw0r5dxtjCgGmzkrGoohqMZXCRShyWsDeSQJgRnApp5GGpyGNSQOOCFabBUD+OxGIkOOjOZZLiB'
        b'glxXoYo+p4WyOjKEtLMilxrtVITaROo7Eoc1sJmxBSv4waiXc8wQO0DTSD2ER8p4ivAInE3hrvtRdMcj9RyNO8OVjO1ifggoA3UUAHwOVrvr4B0MqG41l7GYSd5iMDwR'
        b'2mqSkwnOYYucMLCbil670OBSGgnWpWvZKShyY3gPUobFQnBaD64Tj/q9zmAHHgsn4tCCdIJzqQNrjNkewWOora01Ya/yDOeBhA2GyCvz2skrggIBJ5eIePaskEz29hx2'
        b'FWMs7AnKgiVEyazu04q3ICiL78ydzW9b9UayDkvxF/bELh/b7AseCy2FjwRWHP8ZERraMasZz38bjjW+lsWtSP/TdbtJrjX9tJR4dP/fI1rLRNKKuq20YpxlzCJGjbE8'
        b'zmjOrDXKMgYOh3voWMZAQxrRv7y62sMtoB4NFnWtrGGwKJl4GumXO9fdAlSAtQQ7WACXU0zhCtTRz1HaMGaJGHUjcECe/0GUQIktICbbtoyNPm8FJohiFIcbP7GyHVdU'
        b'WXmyLrBp1Jo9X9h8I/7Yatj8dd+XfTCtaVGC0vPtSTcif3265kxQyM3i67N8D77fz9rnsujOO478C/Frpw+6J+49yfKba5uXjNj3UrZg+f0fxOWWjQWHP7z1jvPq44pb'
        b'UQOK5x1IrmJeB7wnNRFfN1+tkWcIl7Yo7ln/3hx2LX7Ae0UXNmS+NbdmZ+34OY7uy4OS45q2Z/9w1Ot8xi6VZnFe7bjxth8HBD6tc7Ujsr5gKTjlHpob3koYNqoPdSF7'
        b'Ag9luOuMAaf1CcNgLVKBcEvzjgXLhGg4JaxgHCVYPFhJuvDscD/CCDYMNiTrE4LNCCJjSA+kZ68ndGOeoBJU6ROOgcaplL/rVT+4BbOGxYKqwfqsYU1+ZCQeiA4PJWZS'
        b'2jCOMywwiDxqPg2cwrgvrefbPFhGnN+K0ChKZolXYXEqPDNMn51xIJroD1PM+xlne8LPRVjD4C7YyDGH+aNyk8drLKbCeuyQCLOHcdRhcBmooJC0c3agLhK3PWVmK3sY'
        b'3OhGfs3yhsvQ2FzL8Ydx5GFTwXrqFmEcEv/WgS2oNa7V5w4r60sH5uXoh0Mo6gPunF8Eyh5W8++whxGKKzKyebcb2ZilAzw7RSCGxwkdgZhiPtMx+KvQIO1+6JpyULtR'
        b'iSly/MIkYZg2PTTsGQI86Cnn6hsfx7h2bQsGW8Aw+oiw15hn2ik2M8Szt0qWq6SQrjbcYF3+kVLciXd0AQX98eg9naFkYPbmIkLd5djCur4YFZhIgOcYQYugRczvOl84'
        b'2olH9IuC2WCVUie2mTE2s/o7sUjgb4RbXXkx8qfp13jKHkgavpT3amjp6LwVE5A03KPh9Ws9ve3S79zg77/X5cptxlVRlDK8fMqgxPgvpZvMFT+9n7Y1q7Iq/++3/qof'
        b'5zVxnCAsaHbVxkl/rj4anpFZUfmn6LMTe4syh8yetLQ5NGx6uaDlHd/LGdtmVz2KPCje+fVP275iQx/afB+TLtt6YP7dnveWTywtfM/n4Llv11uPm3t1lfD4L08vLxry'
        b'+VCgfDjTzjnk/Ma3f3B+57u9U68NcOy6dNPcMP+TgsMNqrThHwdHLHTw+nz7qx98XP7+4pF3z3zD7/f5twmVktVR53ZeDrvu8Ktk9keH5t6KU1hvXezdvPng4O9bvtsV'
        b'Oe9Sn7SNk7/cdrna73dNWOYvURm5/ed84Wo77rSl7aFLCbEbnB4EB7VYs2qpT2WgK1+Ftaq8vtiJFI/hvQyPBSK91SadDICO4BAsa7sMtCUDG0/Hgh3E2zFY5Q92tPGn'
        b'DRvidAs6lqCk/aKM8/9O+3vuAI06fF0nNBYQlKowJSUnXyJNSSGjDiYXYp1YdjhPjNd6WsxZvNYjdnJycHBzGM8OHcUja0JjbPlDrJml7LxAnuKaruPxNWxKit5yjtP/'
        b'gzrgKT7X9VucUzzwEF/EE34wwlaG557RC1VIat2Ixv6S2ChQAjZaMLa9+DaT+kwHu+UHeh5nlGXorv8ud+lTMtoWeNubzX86XygetGTtngmvlTQt7x5/rY/sSv+xDx1v'
        b'1gim+VVH7HK5Gs6P/mtKSt8FNyKG+p9Nm9yS/ca0mZZ+6nmXrD/JVLjE51h+M+eLL7euPHTF6rN5C2YkvW6btmNCqktWSM/hWZKbDW+aJ99peIs3SXUv8Ob6ZdZHm25+'
        b'Nf+dg/ds941/EnT/D77wusvNz8yQKIHbdBLciOYmNB+PB8ti8So15iW2BidYeKg/EgvEuE3vF4IjkbGe8DjGWB+C9bF46u4Cz2GE+S6wlsQzVuVJKwEL7FhdRJXQlQ8v'
        b'+veFmzkHReAkC8oiI6LdkJSyPtqCMRewwhHh9KfzYA125+hlzvDA2YQEBlb7wVXEL5AYNIIy98l4saII1EYySILYa0Zn1vKYJZER08dFoyl9fTSGZFujqb8MVvQnIsGC'
        b'oWCHMqI/2NP6u1UEi+THEthEdb+K8BGRZKws4XxaruWDg/BszNiBFLpQDcqRqoPUvFqd97/dLt4UD15njzUVuNY2yyOcE7RE3Vj4KljtROqjXzZAOh9cCyrhTo8C7g4r'
        b'XAWv+iOhA6PlkyYR3vATIrBm/lw1PDlXNFfNY3q4wh1wIx+sd59OS3lm3pBIuM7XEa53x9R+DHo7FSzclz+HqMC22Tm43r0i0UhTiheG+4Fj+IIF4zxIAFY4gdMGfpH7'
        b'/d/3MNNdz/IZw4+R0agVTIEB/UIbK533f6zCiXjj+G1FIsEgKjyQAai/hp8jy9MIsPGuxkylLsiRaQQ5cqVKI8BKk0aQX4B+5itVCo0ZIYrXCNLy83M0fHmeSmOWgcZB'
        b'9KXAe/2YOaRArdLw07MUGn6+Qqoxz5DnqGToJFdSoOEvlBdozCTKdLlcw8+SFaJbUPR8pTpXY67MV6hkUo2VXKkFkmrMC9RpOfJ0jQXF2So11soseYYqRaZQ5Cs0NgUS'
        b'hVKWIlfmY9tEjY06Lz1LIs+TSVNkhekay5QUpQwVJSVFY05t+fSc3bO0ETzCx5jHTXEHB9/g4CYOMMmb4isc/IiDWzj4Lw6+wwEmNFXcx4EGB9dx8BMOfsHB1zj4AQe/'
        b'4+BXHNzGwQMc3MPBDRzcxcGXOPgCBw9x8BgHPxu8VSvtwBv+uP3AS+54IszABrzpWcM09ikp3DE3OT1x4s7FBZL0bEmmjEMvS6QyaYyrkEiRmHJWkpPDUc4SOVNjhd6A'
        b'QqXE5N0a85z8dEmOUiOagm0Jc2WhuPYVT7T12MYiXyMck5svVefIxuH9AOIPQcAILIRs2xboMIIlLfR/AHrQ0Sk='
    ))))
