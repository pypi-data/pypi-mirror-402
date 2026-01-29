
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
        b'eJzsvXlc00feOP7JSSDh0IT7+iBngIQj3OABKnKjAaP1KAQIEA2B5vBsrVq1KKhQL9BaoVrFeuGNVVs70+1292m7ULQg2922e7Tb5+nu2tYe2z36m5lPEhIJ9th9nt8/'
        b'X146mft8z/ua98ynlrL741h+v9iAnI2UkjJRcsrEUrJ8KRN7OWe+KzXhT8lOYTG+aEtMnTtFBVFKznJeGJViictE/xvccHwuezk/jFJyraUaWctdwqjltlpCKSUvnHJt'
        b'kPK/fcJtTm7lXBXd1Fxn1mno5nra1Kih5681NTbr6Xyt3qSpbaRb1LUr1Q0auZtbZaPWaM1bp6nX6jVGut6srzVpm/VGWq2vo2t1aqNRY3QzNdO1Bo3apKGZBurUJjWt'
        b'WVPbqNY3aOh6rU5jlLvVhtiNMhT9F+KJeRc5akrNUrPVHDVXzVPz1S5qgdpV7aYWqkVqd7WH2lPtpZ6inqoWqyVqb7WP2lftp/ZXB6gD1UHqYHXIRkoVrPJXTVUJVC4q'
        b'dxVX5alyU4lVIpWryldFqTgqL5VExVN5qAJVfiqhKkDlo+KrvFVsFUsVpApRTVGEKilfSidoCa0IHp/gFjqQUoWOh1X0uD+Umhk6kw6naKpyQqyWyuYEU1qW6xYpq9Z+'
        b'XQPQfzEeMd8CCuGU1E0nQIFdVRyKi34TV+1l71zkT5WZI1EIXIZXV8A2uL28ZAFshTvLpXBn4cL5Mj4VPZe7BByHr4SAvVKWORDlNcBnwVPGwlK4C7aDaytLYTuLcitk'
        b'g/7HPKVssw/K4QnPRxcXxhfyKC6X1QJPgCNwBzxkDkJJM1Dtz+I0GdwO259YWcqjPOAOThk8AnpRaVx/Y2Y0aIM74ltg2+w5sB3V4gYussGlJfBZcwRKXw3PC1GGCyLQ'
        b'uvoxM7z4GDwMLogeM7MoX7ibA9rRWA6jruKs8HlwHW4FbWB3QnFVjiwWdxnuxmEXKjCCC54Khk/XsuzmLdA6b3uRkxOgRnOH1pSLVpRC6+iCVt0VrbcQrbc7WmNPtNpT'
        b'ECyI0Zp7o5X2RWvuj9Y8UBWkCLSsM6vCxW6d2WidWXbrzHZYUdZMNlnnCbG2dW54YJ19naxzAFnn38x3oUQUteaxiGpdi4eS0qH9S/2+3p97fyo16554LStww5YkXeWf'
        b'KB1GC4O8Lla/C7XmH3Oqk98zRAccZKLdlZ977vVkramq+oD1L7++RU9QY5Q5Hk9sB3xmPYKXtoQFMfmJMXBHQoEM7gAnK2OKSuHueHmhrKiURek9XaerVQ4TLLR22IQn'
        b'WGiZYJ7D5FJ4ehVC2wRy/4MT+OBGcXEygaIyAw6ZJcgRrdBVKGUqNsXmUEIEPofhwUrzVJTQADpcK9gUyg+vwrZw0BVEoj1gd1QF3AleUaK0RmpuAIdEw+fUPLgHIegE'
        b'qgi+nAAuV5LaQZ8IdsI9aIJkFNgIjsnADork902ZU1G6AO7kUez1rJXNQcIFZoygn4R7fNGst8cVIzjeXrIgBpyML1gID8vxTpXDkzywGfVmL9PkEbg5HlxEI8mhQI82'
        b'JyhRKw3vo4x3Udr1j//S1HnTDSRK8l85NlO7pNNjc1vljp62Q8Fm82PSa/O9snYMuMrPemz+1e9+/Y1kxtNNTe/kHZS+t/5Xv/j5W2nrNta5uSm2fbQMXrjZu2jn+e/Y'
        b'qz3eW/zq26zEp2okPotVv5m97C2+1C1/wevfvfai+dmP3opPWPyXW1m/XHA26t0Ni9I/Opwk/K+cs29J7iw/PNwyD/7ttXBD+ns14kPBb34srbr4+j+T9T//vOzSgTnv'
        b'N/1xfeDTxb+d9bL2zydXfeReN3X/nzl7wX1OwJfv/+WvC0fkJdM2PXPt0j9/cy6BPjLz13tifuuRKuXdD0bjmwuu8Ivhzji4M2V9qawIY6KpcIADnwbtcN99vMnhbp00'
        b'rghef0QGWwtLyniUEJxno9U9Cbfex8hzfktGnFxaFIexFMJRnnAjB1yQN1eA3aSBWY+BbiGe/Hmg04zwyo4ENjUFvsQBZ8TwwH0/lCO/APajpdoBd8N2hHEzWbHgKDhf'
        b'2iJ1H2PHSA0eGJH+NMeIKDRF0xvH/8Z8cuoNzes0ekT9CF2VI5qoWTVjzN2g0ddpDFUGTW2zoc7ghQqycQ1sBHHfbKQ+e5xF+QR0Re1Z1pr/XlBkT/27QbJOQQdrVOz3'
        b'zPRRelpHflfSnsK73qE9vB7jiHfcO95xo3RUn/e54JPB/caBOcPS3Dt0rpNcd+nwnrlH3exS+nh9qwej00e8M97xzrAkj9DJQ3Ryv2KAM0zn2NdiGvGOf8c7HmXrnd3H'
        b'O1p01NO+Jm5fo62mUTryhEevR9+qYTqNyfOHgPDBiNRr3IGF14V3ImYPB8wZlMz5LJgKlt8LoSS+BzI6M7ryh8Xhg6LwLzACOElJPcb4zASNuVRVGcz6qqoxYVVVrU6j'
        b'1ptbUMxPXCbsVDusk8ETJ3pZnZk4F+at/raR+no9i8WSfE0h50MP37aVG4X32DyW5K5walvmh1zPLaWjAs+7AvE3n/Eonpc19K0RY/pD/DjqlDCN44DXbLzgRoxneRjP'
        b'Lse8IOIEH60wcXyoZkrJMnHRf14CZeKjXxelwCRQuqpYCpaSjTGvjmViQhwcMrkRP5f4hYidYas4Co6SR8IiFEZEEoX5JOyudDF5qCiTp5JFuEG3Mb6SzHBZLceuk1wG'
        b'+Qq+aMSdZDGcGSIILEQC2KgyhgBwKuxY0RYuIgAcOwLAdUD1nJlcQgAmxE5KQTlOCACXUND/XsulBCIph5pVHS8orqPKtO5JT7OM9Sjp0oLIi2p9taDeo/oW99X4LKXg'
        b'0Uzx/C2Zu6e8nkB9UvPqbe9bu6Q+r1ez7/j+vO+piEdvtf6mnX49Mf/xz/I7mkoSpzzh5Xk2uasw+JdFU9TVHaxrWwLb/t5dfeWXnNJKfu3biDTS7lP+kCvl38csUzIY'
        b'mBlXbGVe4viUZw3cBo5z1mngEYLLjLHwLKIIh9Zb83AoUTzHBW4E/QSXIf6oHfYWw7YSxNRJ+ZQAnq4FO9hrpqfcx9zabGoapinFheAMfOYRiuJnsP1nLiBJ6nKEtNrK'
        b'EbtWFMmlePBZFnzJW3vfH0N2LbwYJysgXJ4AtBvhJTbYAs+BM1Le5FuCZ8VcZCeMCaqqtHqtCe03TwY85NYIgqWqKYKl7pnYVHziueknpw/43onLHfKK6eDuFXWtGJX4'
        b'HSjuLB6RRA5JIntWDEuS+nPvSFIR+gqZdmRl98q+aX1JXc0or3A0OBT9uL0v9rWU6eG+K4n8jENJ/AxTcOcwvZTyx7hGja5+jIsFijGXVRqDEckeBkynDd62IWAwqa7G'
        b'+5rZzTR2wpCzFKdioPs72s0Iw7LCfsRG/gID3D5+JPWCMJFTy3a2R+pse4TZIQq2ZX+wHRgkTqADU2S/V9BOYM/kkP0xIXbS/cF1sj845lgMVr3q+UK4E8HOLsQHwt0V'
        b'BQyELZhPGCZ65kzYy58CO0Cr9g/HbnKMs1GZ5b2/uahegTaOoF6Ets7+dpFICkSiZFHSm4nn6Z4VwWlbAsT5gsOvClKe4g23HwLUqpLz1QNyDf9tH+qT+fxdVTlSLoE/'
        b'xNpvA4fGgTqPL8AwXVR0fxpKBe3qdHgREe/dcLdcBq/Ayy0WKh2wgQu2PgGfIUQaHpsiYeAbXo+1ArgLePo+HvF0+Ay8UVwuY1Ez0tmrWLlg6xop2w6Y8SpZIRnRiwaN'
        b'SWvSNCFgnmoDZlscgec0CzzPwYDXZTqyvnv9bXHsewGRg1FZA5V3onKHA/IGJXmjvoEH1nWuO7Chc0NP3bBv3KBXnB2U8gx4fGNcvbpJ8yBs8ghs2kATM+oGGXJqraD5'
        b'7Ubqq9kcFsvvx4LmHn44dVQo5/z/jr4bfwB4cs1xKLAetIkmB8/V4DpF4BP0gp1lWkX1aco4B5W66XKCwezfB6B+b3JTtvKG9566W81P7ZiRjyDURG0N5F/qvyblEAgF'
        b'x2JibPBZl0IR+ARdiMHE6AIe9bCDUCt0PgIuEQBdAM4yUN4FjiE8TkCUS8+3QCi4GSzlPIhbOQQcx+HR6AQejQ7wmGSBx7LvgcdwhHAPuHW6daUMe9H2CJOAokGOG+St'
        b'UuvMEwDyQWSZih28DRopO2RZiiAy9EdApAFrLJwjSQKJHBuSxHIlpeD+nyBKnhNI5Jnx9lu4goU1HpWwVSaTLygoWghbyysY0a0ASXFyFmUqh93wpitfAc8R2EWU+KVg'
        b'T/jCQ9ArAd4WeLBMS//2Q65xDSqV8Vb8xTvdai2CXlUdgt/6ZHUNxTELftbxNrxFQy8o+GMyN6lr1l3/9lfb2SL9CpGIJ1KLXo1nlYj8bk3tSzvsX7f5qh9ntijuPcnr'
        b'iXwE61lbup8VGeiLo4OlNdWCD16TCOu3fLK3QVCjrP+ghEO1vi3yPDMdCV2YTzH5wk1YJooBuwscZSKfGIYP6WEVwDNgwI4TwVtiHegmO6I0FJy32xGgA7Tb4+xpQsuO'
        b'CAYvkQ2xvrTQirJhK7x0H+tCngAD8IV16TbGhHAlG2Z8L09i487H+OYWLDyNuVs2DRMk+2UJs18+W8yh/Kb1RPRxR3xl7/jK3sMSx8zhgFmDklm/DqI75iAE3pNyIrs3'
        b'+11f+Xsh0sHYGbckd2LnDofkD/rlI1AODrvHp6Z44y014hU25BXWE/GuV7TdxnJhNlY4dhx3lF2/XSgLsrfKFVicMMxCThNlkSsQuv96EUb396gfh/OZHWavt3FkQzhE'
        b'b0PUYjY8z6rg/Af1NPU/hA0p025eeZdnxBm3lkQQvF0zWCuqX4CgX4iwd1S715KnvcNUlPK/tpxM2+hd8Sa3SJg4cDIxcS/H7O2qvirdGFwR3z6l/kmWcSDP72JAxx/d'
        b'IzL8/+C3+RHv7676gw/+UlH/wZsUNeddoWCuEjEeGIqfhB3wJSsIw1Ow3QLGQUmEpZgTB65b8DUGTi7owgj7iIQkVsLn4HHYhtiNnTI+xX8U7olih8NzjxLIDoIH/ayM'
        b'OObCZ4Bn2f6ogbMIHn6AuInhgabtuGskzBpNBoT/PcbxPw4TWF7GwPK9Rg4VGNrl0xveU3diZe/K4WnJd/yTO/ij4dEnsnqzRsIVQ+GKd8NTO4sRWPsFHRF2C0f8pEN+'
        b'0r6IYb+Ejlwkf2OhG0FPRNpnfMovskc17Bs/6BU/kUxMCsiESNjB8TzsFCDHTFmIBJaPGxAcT/0xIJyA2+aM8aoIO8+v12p0dUZDhK1b7LJP/oUgXOqFxRDMTaGZcquq'
        b'Yo4gkF9UVfWYWa2zpHhWVdVrDUaTTqvX6JurqhiqJ6hFuKGh2bB2TGARFywtFFFW0YAwYam2/YkHN+aNV0Jt0tZWqU0mg7bGbNIYURtTsNJBbTTWaWtNtRqdrqoKySTu'
        b'dpEP0UWQWZxlp2XwtToVODUHz+LTaON8IPZtxQiqtWDU1x85PgGt80a9fVvzv+by3aO+9OK4x3/pxnGXfu3Gd4/52ovnLvuSQg5ZTqLbh0fWg36hX0RRKdyVUMRCEjK7'
        b'+vFlEygh/vviUYwrWHaahydMHKx1eNTLxFOylQIlR+mawDbxfaglFD5Vmu9JTfhT8qxnS9Zfk0DJN7kqXcIpxA26jfHn6hFTs/ZbyRxNjdbUbNDoE4oNmjrGayhGBT55'
        b'HYH8l91o1Yub9abm7DK0pHRMbp1BYzSi9dOb1rbQC/UmjUGvaWzS6KXZdgFjg6YBuSa1vs5pOb3aBG8YdHJ6Plr/ZlRW1WzQ/5B8zipbqUHQRefqG9Q1Gmm2Q1p2sdmw'
        b'rkazTqOtbdSb9Q3ZcxfKSnCn0O/CCpOssK7MIM/O1aORa7IrEZOnS8hdqa6T0/MM6jpUlUZnxKyfjrSrN65qNqCa11nbMJiyK0wGNTyiyZ7fbDTVq2sbiUen0ZrWqRt1'
        b'2eUoB2lOhbqPfteZ7YpbAzWrce+wxpG2dARFyeklZiNqWGfXeTpp0pTk7GKNXr9OThc3G1DdLc2oNv06NWlHY2lPQ8+DN3QmbQO9qlk/Ia5Ga8yu1Og09SgtT4OEpJW4'
        b'3hhLlNSaRs/TGGsb4bF6kxGPEk/pxNz0vBJp9lxZqVqrs09lYqTZhQycmOzTrHHS7Hz1GvsEFJRmVyAMgTqpsU+wxkmz89T6ldYpR3OEg46zhmNWYhiWlZmbUAUoqgQe'
        b'wyrelXjWmOlHkYV5uWU4TaMx1CO0h7wViwrzK2Wzm9HaWCaf7AWtvhHBGq7HMu0FanOLSYbbQQitRm5p0+J3mHdn8XjuHQaRPGEQyRMHkexsEMnMIJLHB5FsP4hkJ4NI'
        b'nmwQyXadTZ5kEMmTD0IxYRCKiYNQOBuEghmEYnwQCvtBKJwMQjHZIBR2nVVMMgjF5INImTCIlImDSHE2iBRmECnjg0ixH0SKk0GkTDaIFLvOpkwyiJTJB5E6YRCpEweR'
        b'6mwQqcwgUscHkWo/iFQng0idbBCpdp1NnWQQqQ6DGN+IaD8ZtJp6NYMf5xnM8Eh9s6EJIeZiM0Z1ejIGhI01SJq2BloMCCEj7Kc3thg0tY0tCF/rUTzCxSaDxoRzoPQa'
        b'jdpQgyYKBedoMTeikTHkLtdsxARlHWKAshfBY40GNG9GI2kAYz2GWOq0TVoTHWOhodLsJWi6cb4alKhvwPny4TGdTtuAaJSJ1urpSjWii3YFKsga4JT55CjKvrJxeixb'
        b'gnqBEEYMLu6QYCmPkiInFkievECy0wIKOs9gNqHkieVIesrkFaY4rTB18gKppECpmqHLZM7VZkQUG0icSbPGZPMgTGTzKuyzGm3ZmIXI0yBy3GAXEZm9RKtHq4HXn7SD'
        b'k9ahKEx6EZZ2CCY7BhH6URtNiNoZtPUmDDX16kbUf5RJX6dGndHXILC1rbjJAI81ICAq1NdpV8npfIZ+2IeSHUIKh1CKQyjVIZTmEEp3CGU4hDIdW090DDr2JsmxO0mO'
        b'/Uly7FBSqhM2hY5RWmbVaGE0pOOMkbNEC6/kLMnKPk2WZkNlTtLLnbeG+S5n8Q6s2ORjeEj6ZNzZj8mcPHnLDnzaD8mGUKWzbA4kIG0CCUibSALSnJGANIYEpI1j4zR7'
        b'EpDmhASkTUYC0uxQfdokJCBtcjqWPmEQ6RMHke5sEOnMINLHB5FuP4h0J4NIn2wQ6XadTZ9kEOmTDyJjwiAyJg4iw9kgMphBZIwPIsN+EBlOBpEx2SAy7DqbMckgMiYf'
        b'ROaEQWROHESms0FkMoPIHB9Epv0gMp0MInOyQWTadTZzkkFkTj4IhCAnyAqJToSFRKfSQqJFXEi0Y1MSHQSGRGcSQ+KkIkOivWyQOJnQkOgwHksX8w2apjrjWoRlmhDe'
        b'NjbrViFOIrti7vxcGaFWJqNBU4+IoB7TPKfRyc6jFc6jU5xHpzqPTnMene48OsN5dOYkw0nECH2lHt5oqTdpjHT5/PIKCwOHibmxRYPkYYaZHCfmdrFW8m0XNU9TA29g'
        b'Sv8A29DAxFu4Bmso2SGkyJ6POJPaRrXOrjDqIOZVWiwpWJScEJU8MQqJOTosFKtNmC+lK8yoOnWTBpFRtclsxGwtMxq6Sa03I/JCN2gYMEXk0JkaQGpXRIuJu7aOFPve'
        b'zE7qd0KUnNc9MWO+QWs0jc8OjZhv2sLykqmsx+mWSWb8yXZ+LBOa1pk0NKlmjJVNtJJlUvYnWNX97dSJs4iSsGbtW5F9wZNuhhKs6SvFThl2yinLmZxhPnYWYIUjz9ii'
        b'05oYraQSKz9ZjNIQa9Qs+kKV1XkCJ+Ri9fA26gOxFGsL/VsL8ImFZNBbPuolHvSOuefC9fNoLfjcjfIJvMdNnDKb9XUNi/KUbNd0zG5b8UUDS+ET0J7PKA2xhUogfB7u'
        b'MMJL8Dg2ytseD05yKUEaewM4l/sDNYc3LJpD7/+Q5hDbJLnl1tY2m/UmJOCMeeQhqGQEI3WLRkf0hobFyPnyhitFLWxieKjmRr2GrmjW6RIKEBLUy4rXYZXOeHAcrWYv'
        b'Kl5CM8Ww6g4jbKPWaGYicJp9mNnm87CmkREpmIbyFsoqaht18AYCNx1ig+yD2XkanaYBYRBzE+O16HnG/ckWkSzbOjIiYmAeVGPBJlY5kWb4MIu0Oa4Xs8iZRDrAEibK'
        b'jCDRRCQRSw2kOZ0WZSA+rb6+mZbRuQaTtSuWmEI9LvlAJM6W7Cxb8oRsCmfZFBOypTjLljIhW6qzbKkTsqU5y5Y2IVu6s2zpE7JlOMuG2JryisokFFHMLAxmrzUkMnlC'
        b'JArQpRqEoq3KX9osp8eVvyiSURtYtbFyGosIVkGf0fKOLyNdEleSnW/WryQ3LDSGBoQT12E8huPzFtIpmQxlr7dmwVpoZ/EWuGGSnFSYvYRIIHjghiY1TrSBiLMUG6hM'
        b'Viz5YcWcJzIg9JBizhMZkHpIMeeJDIg9pJjzRAbkHlLMeSIDgg8p5jyRAcmHFHOeiItlPqyY80Sy3IkPXW/nqaTgwwFlckhJeiioTJJKCj4UWCZJJQUfCi6TpJKCDwWY'
        b'SVJJwYeCzCSppOBDgWaSVFLwoWAzSSop+FDAmSSV7PiHQg5KrTDBG7UrEelajYivifDCqzVaoyY7v9lQN479EDpU63VqrM40rlA3GlCtDRqUQ6/B7NS4ftNCOTHCyzXX'
        b'Y02cDclZaSlKwph3nCDTMbn6dQwPjo8QETIu1ZoQadTUIY5CbXog+QE8PLHwOCZ/MM2gg1eMFjbBIaWAHCjVmxBXYpPkCCWRzSFsgjOxwzJSCzVHpB9RGsxv1hN+vQkT'
        b'eJNGi6bFZFNNFyLm2qSt165U22P/JUTytKms7dkMRl61O7q0Z5PyNYwwo9HW4KQStGr4LM7IcDak4/QSM7ZeoJkpQVVqkVBqr45G/UYtq3XmppWaRqvunBBBTCQNS6xH'
        b'/pi5xlYS3wZMXi/Kgi8+jXFJ0SrnvHKN1bmBE6ZbeeVwR145DfHKHUsdWWW/KTlfJ48zyumB43wyvrAYkwufM5aUwV0JhE+G7eBpY7EL5V3DFYGLUQ6ssruVVY5iI1ZZ'
        b'4mDg//txA3/EILuEUcgV4f/KEORK8H9lqJJWstNdLKxymIqv8lBJFBzGwF/HsprlmHjkwifPl1LylS7pFqM7kwuJFaBYV7tYAYl1Q7FCu1hXEitCse52sW4k1gPFetrF'
        b'CkmsF4qdYhcrIrFTUazYLtYd91nBVkrIlQMPh5FKvue/m9I73c0y9mkqjmX0XKXPA6P3dJw/9F+I/rMVbEs9ApvPsXbfdMtlW2U4uSrBJ/cFp6A2XJR+D7ThpYxAefgq'
        b'V3KrUEzy+FsuYExB8VPRGAPIGKfaeiNRBqZbhBpihsXHdxEVPGUQzmerWawMNklUlMlbySHGEpFjgjn4YtDsCtU6Xzerl2ZwKnO/1k3qMuamrluFkKehSls35lqLUJje'
        b'hL0eakZcqtIhHtTUOCaoNaPdra9dOybARvtatY4xfhkTEkuZqiaEWRrLagV2QIunXExRIuZWCufBq7jkLiCeLq7KBQ2KuQnIV7jhG8w6QYugws3Owsw1kFIJ7CzMXB1s'
        b'yQQzXYmF2YRYOwsztvkogiW3Qqbz2nUaI7mibJsXLbH7qMW3k7OQLKRuoscnJsty+RjhO6wNs9xutsyQWm9yw6ZYMXkILZmsSFEqp3NxfoRoamliLkubW2iExtPpOm2D'
        b'1mSUW5uxzbnzVphkpgXbGc73tJH6YBuOi5lFl5Bf3MS8hBJrqqVhI9MWJlqYXCBiI6crGxEBQZCjoY3mGp2mrgH1z2kpxuCFkWxRSVqNiqAw0x9a14yIl0FOF5roJjOS'
        b'b2o0pJTa0vkajWm1Bp9B0zF1mnq1WWeSkrvgGeNzZQHCLHq2xUfXYqVljO2o007ZKbWWsgJsFm1ZfaNtcvHV8mYDHcMYyqyENwzrkPRtLWgx88oiohVmQ1AxZo0suyhG'
        b'0yCnU5MS4+n0pERbMbsdkUXn4wBNArh4vVaPoAz1gV6rUaOGY/Wa1fgcdVWaPEWeFCuVu32vnbErubC0KHEKAnkqhmOsFimyNlDmbBQJrkwVwLbSuRpwej5sLYQ7ixPg'
        b'9vnYArmgRArb4stkYAfcXbKgAJwpKCstLSxlUbAT9Iiaaw1mTNl84BXwMqrgweKPgY0VBXAX3F6CSBXY/mAVW9aKqGR/cmkVPLsBHLe7tQqP+y8okMtii1Bl4CyXSlvG'
        b'N4LdM5g7t7jJFLgzx0mLFbAVlW+Lx1W0S1W21mLAfhYFrhmE4EIB2FWmrSrt5Rn7UD17thVc/HBFteAjUf2vajduqs6nd095u7aiTvARVZMv7vNr31V7tQvc6gCMdbRb'
        b'RSh30QFi2L/dH0ZEifYsPn/wtS11U41UNIefuKn7zedcRnhXtk7fKGxb0dX0ps9M/R8X62rzL+y8c3BBcOxzb4uU0b/yem3qrbYR3qeN8g/g79lRp/+lmWtgvTHHY2B7'
        b'/KyQ9777ls6US0LS3xOlafhvp1CsJbTpiKtUdB8T/zTYmwraEmw3vTjgMOilPCM59eBpi4n0zCweaCu3XzcWFQCfAjfgfu46+ArYSioCW2rhDSGabGmp1Q7bGzzNBd2h'
        b'gkBwhlRUADZFopoc1o9F+YRxEcuxWagFO8n1rwW6vDhZTIGMTbnCLXxwkC2D22D3fQRjFDy4AXajGizrCJ8R4aWcCs5y0EpvBluIuWtaRnKcXAp3xKP8p0EHH5xmK+Dz'
        b'8MB9/CBDme8G0IZvx1qXdLa3lE9NXcUBN+E5uPk+Bh14HDyL+9kCL1i5ItxVC1BQVCLcypeHme9jS2nhHD88orb4WHAUbpTjfHAn3B2H89FGnnsMuEzaBdumqXBGoogk'
        b'w4+RoXbBAQ7cCtuWk+kpT4Wn8ETbcWKIDQsAA/CUNxe0RZulbj/hQiimfg9eBsVzOTbFSnIc778NU4yN7ioXKgzfeXMfDZd1cG970XfFPp3Grqw9Tw6Lo/vCbovj3guI'
        b'GIwsGA4oHJQUjk6LQ3k9mTyZezYMi6P6ppB7HSjPvOGAgkFJwWiY9ERIb8hwWBLK6oGydpjwdSOc1VZd+nBAxqAkY3Ra7Al5j7yvZiQsfSgsfTgsc0IRW+35wwHzBiXz'
        b'PohOxd2MGI1IwL9ho2HhuMxoeGQH912HGyTujGnwSuzosINN1w167DRjh9jStlAPsx7GfHC15c/OiBjPq+FJ5HxCWcxfv0NT+XW5C4tVy/qKwu6PvWfby0+izgtzOA52'
        b'8SzKYhcfRLCxippPTfwjzBerTMoaE1aNsxBIsMCjJ4IFbbkQmaNTN9XUqWfYgYQ1agrLCkJUV+VIsOydYMYq91sL/bFUbOUVYhAdq5M163VrpSdZY5y65tqf1O96pt9u'
        b'VTaeZGK3DZux8xRyJCiS3BfDfTxSdbCK6WEo00OmCicd/Ek928L0zLPKkZN5WPd8Hacw6Z3gJKaD0odyP/92Vy2L71plZVYe1skAhzl89OCjTBf989RGjY3b+U/NnmuV'
        b'lRN6WJeCUaShA4dIV8In5Zn+zU41MJ0SVFm4rIf1icZraZum5QeXW/o2KV/2n1lDUZUdK/ew/oXjZRyHNfk7wXILrH0P+zdJP20XcLDeIYdtuYAzfgv4P3v95gfdAi7T'
        b'FgsH2EZ8F3imXyZzr3d+HXNxMqrdK+DFza5X3YIjkjS5V/H13Q83ctOTd0rZDP/wDOyClxCNzSmzUeJxMvzi7PvkVaJucBkchJfgNafEGFFieL1l0ju5LlUYJVRVjXnZ'
        b'kVcSQ6grbgDf5ipypfwCu1KOzOieMewbe7KiXzKSlDuUlDssy7vjmzfolTfh8q0zYsTcvcUEiIGDHuz0IieKNX6J5atC1x93iYXggWf406jnhTKO1G3MxYKZmNsnfKPJ'
        b'oNGYxgQtzUYTFnrGuLVa09oxFybP2jH+KjWR3IW1SLRqbmIkeo5J3TDGa0b71lArtFtiD8oim+/CAMZ1/kwWAjp3y71KgcoTSepuGAhVXkhud1W5KDwskrqwwsMOGEUI'
        b'GIV2wChyADvhTBEBxgmxdsDINk9HEOiWW1dnRKIhlo/qNDUY46B/tRaDTFpD7oGQp8SQaErkTDXdaG7Q2InPaKaMWiSu0sx1ICwZGzUmOV2O9psbRmVN+JBN29TSbMBS'
        b'vDVbrVqPRFGcFYmtBk2tSbeWrlmLcZ+bepVaq1PjKomkh81xjUgIr0N9QmgI7WpLFRbpFtfhhoqajVp9A0GetmJ0LFmUWDSCfEvvGrFaZmLbbjEmtaEBlamz4jicn8YK'
        b'WyOWHI2PmfHoawzq2pUak1Ga5faA1J9F5zqQOHopOYJebs2Ga8qiyRWVpd97UcVWigHHLLqC/NJLLWaStnQrmGbRWD2MpoYI6kvtzSJteTEgI5EeufTScoNpPJ4BbZTE'
        b'eEgd8XRhRblMkZSWRi/Feltbbgb+kbCeWykrnEMvtZybLo9ban9tZrzy8W2C1QlMgMYF7Y2zbdnRRkKDbUSggsDRWGvQtpgslAevK752RmArV2dsRuutqSOaDbQ8OBVj'
        b'fR15rI5Mtpyew6g3CEhOqzCpm5rwvVP9NJuigwAHWjjUQIsFtPCdMOxD07Bai6iJZg2acQvAyUlrZc0mDQNGBLg1psbmOrQzGsxNaCFRW+qVCAARUGnQ6Go1dDMivKQc'
        b'00UMVEQPY2S6rTXaNSmn89Gms24oUsoeDLGWBoEKfsyvVocGwLzjZ9QwOastT/c115KeMCc6OY0mU4sxKyFh9erVzAtG8jpNQp1ep1nT3JTAcI8J6paWBC1ajDXyRlOT'
        b'LjzBWkVCUmKiIjk5KWFOUkZiUkpKYkqGIiUpMTVdkTmjuuoH6FCmEg087PQAZ4wl0iKZvAxf04xb2whOIvk1ooLX6LG2zIxLJfPAJQX6TYKn4Vnk3oSbiKoF0bOrMcVW'
        b'OrUAtsbBnaVFMiW+sK2MwRebF8FW9NMJuuBuRMLAM+CcK9wH9oLz5G28YHgQHIIXkVCOpdYwcNKF4sFutgj2wjPklT4NeBl0w4tyJP4W4pvhqH7UgiwtjU2Fghe48CXU'
        b'oRfNM1DO9TPy4MVi2F66EHa0lEjBcXjONiI0nvmwFZFdREcXtiCnvKQI7uNScAcS/eGxGfA5M743WCQWRZqEcmkRuAGOuFGuRWx4BJyIIGmzeAZ4sRAVZVGe4AwHHGCB'
        b'jRVwmxlTx0VgB3xZCFsT5HA7ai4enCxCMn4r3JXFouh5PG5TAZlEz1lwH7yYEAuuVbEodgEr7cnGrLJPMGUuIyZDhfAV8IzRHWW6zDQELysFy9jzYkBvluEszsa8XAj7'
        b'wHXQjjO6u8thJ7xcAs/HIe7iLLzKoXzXcsBpsDfVTFiOnWgAfUI5qg5cFqOJw89+7ORQ3vAa13MD3Ku9f/kW1/gOyvnYmpqmjvMemxO9tp2TSdwET+15/TU/8fJW8VPb'
        b'Z3C14qjfz7ndOa/l3pTHq8/NezVfl/ftl81/X77b+C8uTK/eW7iya9eOr40u7o0xB94/fIi7eNNHae9/ODan8Rf3xN7G1b9pr5+RWvXIJ2d2NW9cpd95oOWNS4nP7/3t'
        b'0mf/+mr7rRdZC/cVhC1oj9heXzBlQatEHFmwI2ZWUeuOm4qrwqV3JVlfZr9mfOTJsl+d+58Nnz/7+T9e48Pli2GAaSjp05H1XyauSH0rYJXfdy2H/3U3dH2+4teb1z1B'
        b'rWGFfL7kipRPXgpKBZ1xDiomyjMStFKc+oTk+1GY4XoFgefWYqe6lgDYEafgwd2JCkbJdHKVgOiY4AF43kHPJFgJugiPB7rFyeOalssY9sd5PLCH6VJ0THZcmawQNdVZ'
        b'WFocD3dKWZQPvMFNXplDdEiRWrjdOKs4PqYAdYRFCcAp9lq0S45Kvf6dN9Sc6mfwm1wO73XZrlK7qevqqhj+Ykxs4ybHIwlD+bGFoSxxowLoHl6P6cQTvU8M+6d28EfF'
        b'/l0Jd8Sx74iTR+VJHfldM4ckcYyCJn3P48PiiB7TSHTWUHTWwII70TNui2cQbcrsWw13IkuHA8oGJWWj06Qd/I7VnZ6j0hTk2TDkFTU6I6+DP+ibNeSVPRoRiyLXDmFV'
        b'Swzyrer0GJUmWfPREchn7nR/X+w/GiPvM5zB77JlDkkiR2WK/rwzS1BoxpAkdtTHf8RHOugj7VrWwRn1khzw6PQY8ZIOeUn7wvsMw17JI16ZQ16ZA1HveuXascRTGJb4'
        b'KGW1OjyGnRewcxw7J7CDtbGGk9h5ETunJmGi7dYCN1A9/kePv9BguIydK7htzFrnIc93+BWRcles1PmaqHY+/9EKHnxc18fPoAaEuRyO1HVMVIctOS3s0pg7w2Rag3x1'
        b'E/nlkpciXC2H6bWaMSFmcRBjh03tmEHbxlvrZkd/vKy8Nhaqc1yc8dobySuYiK/Gp2Es8tSoqwofB+KnSMnzswovC7ft5sBtCxG3bXdOZs95I77abaaQcNsTYu1eyGSb'
        b'm3mO3LbaZihJMy/lIR51Lr7lwoRoxBigzYDYUcS8qO2f5cUMTjzdYGg2t6BUxPeq3Wqbm2q0erWVVYpFXFQs4RkYlgGrE2xmvLhBm3zshuXj/8feP4y9twfaLHxEx8TY'
        b'FFoPsPkOUM3kZ6KsBQivtvR7DFNt1TG7gqnHshEscQx7qm/Gag8DYUj1DJu5uhnzh9omtc7CsC59iKktYtudG9vaeoD3I9N+TXPzStw+jpHTpZbVUZMw3VyzAk00Eh6Z'
        b's0Y9Fh8y0hKTLLoiPPFIlsHFl46b2doasW33LHqh0azW6QikoIVZ1ayttUHjUjurXAcJyIIeHKeJ3Ahcam+pO0GGwdkfkGMc7D//D8SSPM1qTYPFOuf/iSY/QTRRpCUm'
        b'Z2QkKhQpilRFWlpqEhFNcKuO8gnfiXwSTM54N0/nUeiXvpVvFC3zraTMySjykfz64sJSuCO+0CZ8IJnDD7Y6iB1Y5HgS3HRNgZ1zCYsdAk+D3Yy8Aa9OQUyaRd4AbXIz'
        b'fqQrE6XvKJYX5TxSihg4h7onVAzaYJsrOAFeziHyR/Ti8oVwq7G8tNzyghWWaBbBDpR/N2xFYocb4tdRfSh8rWIZeBYcBEddKXAK7heWpRURSUwOnp5vLII7C0vLi/Gz'
        b'V4lcyi+vOJWD+NaXwDYzfoV3ARx4sohrjC2Fu2IwmyovBGdiWFRoA4+XFUpyzF4LO2rqhfAq2KUUwJ2yMiSOsKmpCg7oTW00SzGT2j8HbEaTYHtTGb8cBS4rwT5wHr+q'
        b'nATaeGtAPzxBOjVLXNUAX7B0qzBeil9olsCjHHgdnoC9Zsy1LKgDLwt18BRaukqqEvQLzVhWhMdWG4VkphGjC68WlATrUSVwD7yMBbE2cAqFSuCuAiyQLPMXzIPXHyOv'
        b'OIPDnuASvDgdnsMyEVVYGkWiH/EEPQpwBptvJaEu7oMvE6EKvAKei4J7PGAneWo6oRb2mzGDBF7OTMTD22kRTAviVfiV94SihWgZC2B7RYwULWYBftO9GB5FYiPi68EV'
        b'JR4/X+++HElU5O2XjJXw+BrQWwH3KYo4FAuepuBphdmMT9dKDHC3EE0w6ISb8CQrx9daYD9sy6DBWfgMlwJPL3R9ZHEZeVGcBrvzxsW9BTFwX4XAXqDjUI+DF2Z68z3g'
        b'C9Fm8oDeFe9HW+B5Y5GsvDQBr36ZRZ6Twi4koBe4m/GjStIqJCYzb9VI+VQ+PCAEr7Dhxfzl5H3z1Ull7Nf41Jr+wibdioWjQUmUeRau+jKShS+ivbEXXrTI8MRgAgMI'
        b'3J5QXrogxlKlyt7m4TA4IYIdYHMokZHhwVhwKg6B5JHH42NZFB/sZifMgEfNmOWFXeDcymzQVkxkGraBlQG6dWW6b7777rtKiks2+L3lTfHPJ8+itInCIbbxMGJ1/zp2'
        b'9YyyuAwmel0+fG44rXR41piba9ixCz2bed6xm+PouVf+4L5w0b4/7QraNPt+RtCuz1I8tH/+S2vd3e50xV/fuvj+heZpTwVOczFUTvn70gvwUfHdp08HqS4cc3/30/m/'
        b'+PSX7stN/1Ktz7tSm3f2jazEpFzNBUH2stJXgl/znqI7uz7w3W/eXzzd/4h656Y7894VlbGe29bi9rHLy2X7/kbt9Przpny58fcjy59qvlZ/4GS++7Dvgfc+ODIsNieV'
        b'/fqj5xb8ctOB8OZLYaeC1kz7zbzG99dl/Suk9eXM2p+/UbnovefyRKIlFZ2x3z6/b+ZRw72qoRc/7iss3dklq7/yS3fjSzMrb08fXlddk3wjbNqezrhffZr4a0FD3JIT'
        b's28vpZ4JB6duq5YrWhtWBenTrx79k+75v8fyE+Iy/1ux4YU/y9ZlfXyw9fyhheejz3211yV+687nfx3a99vtcef+p/nPvz/8zfMt1+Ry1czBM7vPHuB7H5jX/HNfzdWv'
        b'/vrPoMTHZ3695rmgP/556YEp8IZy7zNtrqd/tyln3eVz/zBW/Olu8z8qfnPndufdMs6usmbX9//J5rpXxl+NkLoT4wJP2AN22kvY4BIY4BAjDrTJT9/HB9oCeA30xFLO'
        b'pWwiYi+YSx7UA5uzZ8CzoRMtOQSimcwj5nvhuanFNlOahbCfS3mqOLpZ8FnyGl5qrhu8KYmLtdhguD7CBi/A59TktbEGeEEdJ4et/uAiQu4YPnexZaAV7iGWH/CpZLgR'
        b'day3uCSWT7GXs9LB0/DyfQy708SNq8Fz4FRJaTyb4hazwIUsuJmI6tnwPNyGsP1OuHuFgthd8B9nR4dwiHkGvCyNhyeetJhoTDTPgMc3ENMLcN59udPTHrAvnQvaHl/N'
        b'5HpxCRrKDXDOiPefDBMjos6YAjs4oH8dfJ6MMRfsR3TpZaWj9mANeFbq/Z9WHkyuVcBzRlseZnOiWvDAWoRx+WrM10G9MJ5AVAxFbEbFsEFIBUT0zO1Lwa8iD/tndvAZ'
        b'bULOsG/MsFjaN2ckfuZQ/MxbYXfiZ98WzybqhNxbJXci5w8HLBiULBidJmfUCUyx6cO+0mFxbF/liGzWkGzWraQ7sjm3xXNIsbxby+9EKocDKgYlFaM5hVjlkDHklTka'
        b'g/ULTwx5RdppJKLjsMoDhR4f8oq4Kw7uquuZPSKOeUccczcwpk8yHCjvmPO+byBjXnItfKDuuvROpOWJdlTYUhBrS3L3Zo2mZ3XkDwYq3pGkfGDxDklS7gbTPT6Hlo4E'
        b'JwwFJ/RzhoNTOtxGxT5dsbfFESfFfUtGZNOHZNMHaodlebeS78jyh6Xz3gi7LS0mbZa8se5O5CPDAUsGJUvey8i+Nu9W/huqn5UP51QOZyzEI0sZ8krFapLUbNxe0pAk'
        b'+YOwyBP+vf4dHqNi3wNZnVk93BE6aYhOui1OGo1U9KvvRKZ3lI36Boz4ygfRvxB5P/eq63nXgRmDPkUdHNyziJGA2KEA1L/Y0ZBpIyHyoRB5n/FOiKJj3l3fgK70nsw7'
        b'gbJhX3l/5G3f9PdCogdjSoZDSgf9Sj/wDexq6Gm4EyK/7SsfjUvoculxeccvZtQ/uMelj/eCx21/+ahUhmJ53R7ffBAa1cft0/RXDmTeqhkMKeyYNxqv6JgzIokYkkT0'
        b'VAxJpKNevl2ud7ymWVQ6Ue96JdlpccSMFucqdgawcw07L2HnOnawofsDCo2HK3Ae3AWYO3lQnWPT6LyJnbeQs8Sm0cFPVz7mxmJpiUZHy7pP3B+r0TnJz6SuCXO5nFrr'
        b'zVL8Z/kGieCLxylH7ctGSuWiclVxyVdI2CoR+aCPu4pl+xYJr8LO4riFH0ip7N42VvEddCq8mXyiaZkQO+khuzOu351w/Z+K8Ed7Gqe7UdUlRrqRqixjWIxLcr0R7BQ8'
        b'hvhP8CzF8UB8xPNglxnj2yfgacRCgZ2VcOfC0gXw8nx4eaF7WmIiRZUnBftywKYn1xIOGaHyXUEVcGclBS6nJsIdKYjPFjzGgj3wOXDTTJ5tPVAMtlhrYlG8WNay1eAg'
        b'Qt7PMTznbvh0A/7OCDjlQeVQOVnwOvNQYCsNDyFm8gWEs6IosBFu8tOB82by7PYecDG5WJ6YkpzKpvgbWGA3DZ5zB/uJVDIjHvbFFVk/ywEulli+zLEHPq+N3rOQa5yB'
        b'gIT3+vadldPLES80/TQrO7T0nZRL3nkLKwULXfb3CU9Wutb7zNHcfaM26rVPj9wq/zhPvMTgO6V4/9GPV//1t3/7NKf8lVtziij/hdezEofduy5tS57514OFkeVVnrLP'
        b'z/MXP3VN+cyKzE0Dv/pAKfz45h99vol57W8xn+TElR7Pe2n94ucPHPusZq7sl39QNruMZbu1tzUG/e5mwMLkHft21Wji4+5S7w70rB87N/ac6X8WNP5tdU1wsSq1YmT2'
        b'XVM170n97gs3Zv3qkc4n4Mmb68t/d/XrUx/dEDYmV5+4ti5vya968nJUr8Zv+MeZf3358eHbK5M2en72929Om7tPBr3RE/y7j2aY/uWxrJpjLk59U9TM/eQJVs7S8spX'
        b'G+//9bfT/zgoijoMhfnXWm7dDTrcGSK5t+OvM7ZlD075+Gf84Iom/+/Ol7303Rs+v/tVc+DC/GV0lHQq87o/eFmJv+EDTzYnuFBs8DxrYQg4yryyOwC2wZ0MkYfHQBtD'
        b'6OH2qQxjciIAkdttsJch9jZSj/iRVmK4AffDm/D4BFqfgsVFhtyDTRRhYRLhnhzML3HT7M8kOPVgt540lV4NthSXxcOt4ASSTnYngBe5lAd4mVMF20WEx/EGvZ6wDR91'
        b'8RSPU9wQFtoBh2EP8+DwfniwKc7utGOBFH8YAWysJ23PWoO/8QIH4h0+89KMhnWcsVF5Ae4D54ot5rZxiAVhLG59wBluINydQTLxmkBrscWOFrwEj1ptaaeu4IDTSGog'
        b'LN+yYHDeKb8HNnMZli9hJeEfq+A5F2wqjZjFy+C8xdSZT3mGcB4F1xD/iLsNNoLTlYjrAyfKbTbUmOubCi6SGZHGlTowPILyteBFsJHMCNgCTi+xfZamJQp/mAZgru0U'
        b'4eBAjxJucnyeOXvxmvwpJDGJ8xiWV+CucvLJhw423DGvOR5ulE79X+Seplq5p4kfUhlzqWI+b2Nv4MPEEGbpLMMs3VvsTvmGHtB16vboOziYK2noUR9e0Rc7Ik59R5w6'
        b'GkgfyerO6pgzGhR2pLi7uGPuaEBI5+wPAkOOZHRn4OjQI4XdhSS6Y/ao2K8rZSQwfigw/rY4fjQwtCfsMMp0j00HTB2VBNzjoN8PJH4HSjtL7/GQ/x6f8g7qyt1XNCKJ'
        b'HpJE33PBcQJL3IHyzvJ7rjjGzZYrakgSdU+I4j4TUd5+XZwjom7RYGTasF/6sCTjnjvO7EF5+9/zxD4v7JuCfVOxT4x9Euzzxj4f5CNN+OKQHw6VdZbd88eVB+DK3Xrq'
        b'MKc4fSh++mDkjDt+M4YlM+8F4sxBKLOlx8E4HIKyj0gyByWZ3bN7eOSLO2uG6YzhoMx7oTidJunpg5J0lM45IeoV9S0eptOGg9LvheH0aSj9Xjj2ReBu4NmJxKEoFH+g'
        b'sKOwK/deNA7HjIelOBw7Ho7D4XjSjnRQIu2ac6S0u/SeDMfK8ZATsC8R+5KwLxn7FNiXgn2p2JeGfenYl4F9mdiXhX3Z2JeDfdOxbwbyfTYT+Tr49/JYlH9gB+8DL+8D'
        b'ok5R9/K+tOHg5NteCktEV8WRxd2Lexr61C+sGIlKH4pKHw7OuO2V+fuQyI78UYn/gZLOkl5xj+po4LsS2WccKjTqA9/gA+s71/ekIp57xDdxyDex328gc9h37qDXXDuG'
        b'zINhyF4kcM6cshjHeEaT2mAa4yAY/3Hcl4eV+3qA8foddn6PnDMsy5Ph/8RPhruzWPGY7Yr/saZqR/gJ1DlhFseZ5aJoouUi63/BcnGLlP3tPjfmRqjJeqPLcoqisyh/'
        b'DRqT2aAnaU20Gh9y2emOyQETvVKz1ojytRg0RmyzzCidLVpxo+2kyqKBxgdFDx5a6RhVO66+Zq2JfJLSntcTOOH1REQhWYGE8L1IbN0PdoPtCDc/Ay6wfRaBC+A8OLUA'
        b'tPIoP7CRs74MHmK+8tYLzmfCPYWgD3G4ckpe+YiZXHLYIswknCFoW1QHXpbB/cVyOYeSgO0ccJKKIHxdHqpzpyWTC8UFL9TCdhY4AF9uHGNVERYOHK6ER+LkhRb9lQhe'
        b'YSd4ZZDCynWwE/GEiOIdGucLEVfYJyEftnMFB5bZlFvgNLiQUVdPqkwC7ZoKpgA4CfrZYCcrKDKFae1kUS3cQ/o5FZ7l5LLWIzLVq1X5zuIYL2Hgeu9DbGM62BBTLaj3'
        b'rL7FZb3ZVRM1f8nGV93fiG+oqY6Z6lYvrP5Zpf9rXq/5vd7ITj26MbNV2v7I0+5hVbdEl/YFV1QNdLiK9/7sND/i5lt+fr71Gf5/mKX/A31359r56S9tO/9a0p8Kwu6+'
        b'7fdaSfv1M35r/TYvBoufWtxpdmmpHfp5PWgd5Nx+tWy+i8uFXXRZeFpLV7/6xco6QW1K/W2Xg//92hts4QF2wcCWpBhFyxWK+o13YMe3X0v55HM08CDYB07Y3zqR8RHD'
        b'9ZTFFGInOMh8jqYdHDDbPQ8PjsIj7PCcx4jepQVszIqTl7JRuT4WuORajBiCXYSor2uG/YiHwrxAoQw8n86mhBo27CmEmwjzAQfmwitWlQpo955gQ7sDXCIftQOvRIMj'
        b'41+9exxstXJEr4CbUsEPptkCG822UWq1sQpvMTtKbYkhlPo2xVBqpSdBtohoRkpPlPWWjURkDEVkvBuR1VmCSG9o2JFV3asGo9IGOAMVw6G5HQWjofF9a+6EpiNfVOwJ'
        b'Xa+uXzEcNatj7p7yz1yoyOx7IlTPSETKUETKSETWUETWuxE5pKaA4C714ShE5P0CjvC7+YOhCf3i/tp3/bJG/UJ7XO74xYz4JQ35JfXH3PHLxlG8wx4jfglDfgn9/Hf9'
        b'0u+5cGmfjgJEtKPjTuieR40OReUNRCOHtOxJRU5H9NgvuEP0kyyHP8cO/jTdH+wth+d6/sjn759HBU+yxrgtalOjw7dS+FZ0jC/c4C/DkW+l4EvE+Auc+MNSfAtiZlfw'
        b'/4PfS6lHiPmiHWLGONSoXoV9Op09ih6/bov7nkUX1tOx2BdLI7pnZI4TMfLVrMFPDODTuVj5Om1LbDypyILlDcxhnhG/1FpnOyJUG2obtas0crocn1iu1ho1NsxOypAO'
        b'kexqur5ZhzjJH4C2BQRt0+CVjLgCtLXnFyCWvai0ZAkPnKwsAGdga7wc8dIFcJtLC3gZXCWfhIE98WBvMUIFRaVyuB1JNZWwFdzIwt9TRYy7LAY/kFUMr7iA/UrQxsjM'
        b'XbFJSG5+eR04RZS5HB0LbAa7ms3YlkS4PDDOhaLWUGCH+xpwpprgYE05OBpXzqZYCK3sUGIc9LKhTDv9d5e4RgECrZmNLocXlK4EsyTP/qa0vey3J2Wqn23oSdoXtO7e'
        b'wUPPLR0M2e+uS+BJJbcPSV5b6fnPD3+T+si0nKuyes+1Nw4fTlc0v/tN3tDeniOSS4tey4w79fMXv3jMVfSZT9aWzbNPdz+d/q1vc/1a99mP73dbdex3eVdi5j36z6vb'
        b'Sh/92181h34rLftoZujttNe3lW6f9uapT6+UzF71j09H1rzE+iromzdT9kzf8fhbhkdVUp/Vs9qniC789eOSXvDm1eGlY0e1Z19a+NXXr/RW/OOTpr/c8B4aPdHYsmLb'
        b'R29fdluWqim+8vvs86dX+/5pVtT9mz6X873Hfv+VOvlxqeKS//Rq5fqP3v1i24kC0S+f+9n1bulU3eJ//JNz+vXY0r4npJ4EvWpmg2NxPrl4BRHLks4CZ7ORzESk3cP4'
        b'SAzLgFgyw7IPB/bBNvYTYJM/yTANHgBtprXwIry02qKldwUn2OBoLeggEpkbkoaP4Qoq56AlZ1P8MnYQeGEtg3QHAuFV9gz87eV4eSFJFsJ+NryBxNDzRBYPic/KERTH'
        b'g13lzMeChLPYsAuh5OOMyLappQYXTqgEz5XLsDqFHYvEvaeYyreuAJswHZbK4W4yMs9EDuyGLzTA/XWk+FzYHkEoTuuTFqLDDodX4TZG0rwKrsJn4xLwybJMLmUjanCE'
        b'I1oAtjapybg2gOfdiOwL2/gJZTyKn8P2ZYN+ktaUF1VsA37XbNAlYYPeJi5D586DyxKsOyiLd2EmJI/tlwaPkOEugpvzYRsX7LL7dio4zwV7mI9qHYc3wG7cJbRX8Cd+'
        b'+KCPHQ/azVLhTxUxhZSDgp6hWFyMCcbcbeQKBwmt8mY+nXqvyIuS+BxI70w/MKNzRk/EiDj6HXH0ewFhg9OsFyfF3iR5euf0HsmIOOodcVRf8rmsk1n9dSNx2e/EZTtk'
        b'9gvCkt4hjw6eRdG8J2dEHDMkjunzGREnviNOvBsQ1hPRx+lbNhyQhUhYVBz+XMvxpm63Lu6oXyAu3FP5rl8ikjGiUz6Q+B4o7CzcX/xBYPCR9O50fLelL2IkMOGdwIRR'
        b'RPME3YIeybMeDpXcDQ7rmXYiujf6RHxvfJ+pv3J4WtbAnJHg3NvBubeUo0EhRwq6C3oqny37mkOF5LGGgnO/wE29H5yL8gwG535rFKHp+VnI1LkzXH42Q5jvKWQInytD'
        b'+L6chPo9uBhYa2sTUxiCiJGVwRU531mFFKwcXo8Iot/nP/K7RkRIOcCPpk4Ikzmoa+0U+Vba+CmLYRNusRU7u3GaK2PgqdUYDd04cg929mPSyjPgDz4aliPnE0wMDBrs'
        b'w/VL2eOvB0pFn2BRiBgsf4K/0DZeyuDBspQyeGJfA86CjQQ/wQD5iYjhGnD2Mc7chcoyplIv/MkaQZnlT8pjftjov4+zhyDxJai65tqqKuaisaDF0NyiMZjW/pArtz3Y'
        b'IcaWRD9PZMXPbQuCn5E04G/LSL0NlT9p4/3Es7RZD56jjUPKCquDRVqjjmX55s1nXLa71+cCysO7l3PSeCt76JFld0PC+jIH8x69z2F5VLO+5oa7R92jkPMFD4fv4fBn'
        b'RSwqYNpdL9moJO0+jx2Q0Vr0GZ/yD7vrFT8qSUUx/umthSgmJOquV9KoZCaKCclltZbhzyDRd73iRiUJKMovqbVgPCYTx2STGN/Qu16xTIxvdus8FBMYftdLzlQUiCoq'
        b'/krAcp/N+pyP+t1d0Ws8r3hV/AvF3WD6pPha+KuKX9Thvleivsvc81ifUdjFva9Evcf+zx9l4QGHn694NfIXLrdC7waGdJu6Ys9zUC0VQ6pHhtQaXEEDqqCc5Z58n8Iu'
        b'rqABVYD9X9ewU93zWV9S2P1Kz/J3D/48Dfcl/LZ7yNdsH/e4exRyEBbwCP0KB8ef+4T74Vb4jLEQUQ2jhwcS5yj3YDaiZwfhHmKJ76tOEII+EyanQmxzMn++jA83wV1U'
        b'UDI3HPauLXP2cT/q/+oLqD/k02MuzNHHsfmwOxv24W0QRoWhEe4l5zLLV4OzxXLQn5iKSsMrrLSYx+Au8CJzmnIBtCrGzzeEfrCPnG+srWWSt6TIYVthPLbDD4DtCi4l'
        b'AG3sIrhjUZk2JbSLY1yI5+92MHPbUlRdd6vzSSpqftaRpNawjf4VIX1t3lfl4vwufU/WqhJzbntuSVRJwYqM833q/OStucGxB8Hrt2jOpemtkV2bppxe1L3pIo96vVY4'
        b'6/X/kvIIgd3ABdutjzbgBxvANnhOgVigGwz53SElb3nYSPNcuA1R5+XJJHU6eHYJtimwGRTAp3JloBN0k1Q2uA6OMxrk9BlWHXIz7M1kThyuIm5hHzZj26VZTFKXszXg'
        b'Fbhn0vudohaDBskJmipibR3KsnzbHL9hiwn0rCmUxI+hpK1zPhD7kC9/zzlS1F10qGSYvGuLCG12Z3bX6j7XYXHyeHjNsDimdc77nt6jvoFd87pUHU90cFFaa7G9ODfG'
        b'xa2O8ZlL59/zIVbcN+KEse0+xPqkF4sV8GO/aOYAmbTl94tZiLTkCO3fAFOyLG+ATcevT6GdYv2kN3c5L4zCn/RWcpU821tafBLLR7EudrEuJJZ55Ytn98oXz/bKF8/u'
        b'lS+e7ZUvnt0rXzzbK1/jsfhwVYD65MV8PFw5Q8VWsJRTLD10t6ROZd71Us4kqRJLqicOI1HVTSVUcJXellgv5SwUy0OlfKwvZyl9lX6W97rQTCzhKjhKf/TLUwYgl68M'
        b'JG4QccWoXLAlLw5xyDtp46FQWy7a5gsjdWHfNJyX+MJtvghbaqQtLsoal+CpjE6glDG4rhqWUopzoN9Y+zZROM5aEvnj7fwyO79cmYvcBLuYRDt/kp0/2c4fbudX2PlT'
        b'7Pypdv40O3+6nT/DNrZMqy+BPZuVwDZNVfouF4dRy9FvfMA4wM6XUhP+rFjY+kizMtpSMvrHlkTteuPP0pPryfggX6hwUWYRKPIhz4oJCNTwlNkkzleZY/JTUSZ/pZg8'
        b'dJGHuD3E76vztTqNFgkllIPRgEVtIvjCQDFabDujAfxoGRfVjj97zLeZCrj8L5oKOPtqvYCYCiSu5FavwhdMZlWLPqz0pswYa8CNAN+Ia7OzcnUwsJpajvB5mwtV0SDw'
        b'Av2BWWWfYK1CWdnH1vYI6tP2v7qUY8SPqnx2/7WL6pWYANX/Ar+sVD93W7VKnB+zO3L3lLnbWFF7POt+nrREkJR47AtF4hsb15z1qfDzU27pvXHT54+zQjxbfaGbIrx1'
        b'yvGZTyX51WUp3jMdp6OCpQOKWYb42d+2LH9zVkic2273t2tZn49+mKOa3tGc4bVin3+Ggsq57l0T1SR1ZUTfqzPgNvKtTbjHo1DGoQSVbBO8UkDkzyc9wDnQBs6VlMYH'
        b'LUESZjR7CtwNBsgpaz18oQq8ADqcWNbBLrCJqGwjQM/SB+3QyCSVS6hIf15jRAGpKhdemgZfnM+8ZBQXI2Pyoan0DeLmLFrEGKs9uwruZ74JCnaSo/B2bKl2qHQaB/Si'
        b'ZekjF+oWg5uog7ZcpeA0hTLtq2zmgKN1WUTR4Ac2gpugLQFrjHaBa4WwnUUJ4A422OLSeB8b0cLtYMs00LYa1UG4K1QT2F2OqPX2crhLzqcyi/l5YCvYj5iQ01L+9zDb'
        b'BLQefKpoqm2LOL5VtJpiqO6yKVRoRAd3rxAbakkOPYK8bp+5UXR4T85waGKHaFQc2hN2WxzeJ+o33I7JHNC9UXt7xgJinZU9HJAzKMkZjUzCrwZNG50W1zf7BTl+y2g0'
        b'LJI8IGT5CaFxA6NhET28Du5+dzuyzAibYzxioT/GxReGxkTj0p2+ecxVq28xm8g7ss50sYz4aTkos3tJKImF0YvdGdnSKSxWBhY/M36s+HmQH0u9KEz9ac8IWZ7j4VXh'
        b'oU3y/Ij9GlkfD8pl27+WsuTgEuYtkqDxF/AnvD4iN2ylHvgI8I98XMa9yn7qJ3ssJRNFzGE7PMyT8E5wAtPBELsOTnw3SP7vvDLjVmUDhYd1bR7qmmE7ZUGB3wYXWgtZ'
        b'rwj92/2xPcWDobaqSTvpsze4O9gC1O4pHh+soKLrDc1N/34/6h37oV7zsH6UOvZDQvqBL4j9u72wvLPDrzI1m9S6h3VhvgNMLz241PJQUiUuaL14Nml//m/f09nyA+g3'
        b'h9DvQAM29duo5VLVJVOraEpbFvp7HkE7W0P/ZpX6bnEfE2UpBc/9dlXW3rKG+uoO1i+lCq4i5neDWiBI3VToUlhJJLuFh3gv/22WlHUfv9GjgrtnYNqAiMjZyekD2O8b'
        b'MpnIRVRCY1PsScD4ezqY/mAKUDeV8gs68ETnEz0LRnyjb/tG3w0MwpauKUemd2ND477cO76yQS/ZT39WpxStYwXb7nCsdupPOBxzpmMQ/F/pGB6EB2c6Bh6Bh9EVXMzN'
        b'+S0XbtR1NZaXElsO1zlttcOfUnhXsfyiy7S1cAHHiK8Z5cJHx2HkVQwjj1KK4zvobXS+OKpvRVB9X/6Hm24nSRUtx1mUz6s82ZX/krLvx6GS8DrcD288nHfIjgD7W8Bx'
        b'xrauHd+SwScPsTI5lvY3gwOz2ApwNHNSgd2zilwv1K7TVNXommtXjvnbQZJjEoGoWAtEtUylYuKxZXn/wjvR2SPRuUPRubfCb60eji7v4B5w73Tv0gx7RUyApzEeuYz3'
        b'PbK5EsvmFchZbC+bNyGI8v/RsvmD+MUXQ1Q9ZZUXCETxEExx/ldgqvEBmHJxAlMiAlPfzPh67l72qAs1v7rqrKuc+bA36AOHYA84hTq+jkKe/nVgN7xCjExSFWAHOIXm'
        b'Zz1ina+srwUDZvxaxIJieMFBpsAXsHrA1sqYMhmLSgHb+R6Pw05y0UrMxhet6GaXFrX414v/JySdMqejaLdFYLv1pde4mnT7q1YWuLO/YIWY5W43eHDpKkbTSPRRR+DV'
        b'ebCtMFaHNWY2dVmRhLlMNTuAG3XCIgyluYspreoczTG+gQp+/T9lF9V6tFEk1S3Xf3Vr/i2v13veplifvCkSJYt+e0MkerVkx6zHxPmta95LaJPOemRth85vNlUp8ecm'
        b'gdvgranb+jxqLsQ0VBd8yPqsZkFf14f/3a3+b4Vf7iqewqW/OmlfxTy3V5/6ZJb5kMcz61qzK5bNWpVbsvWkW8351o3XNwfrZ8Q9E9fFyUhaXs1+4Y+PDSRuDGw7dbf6'
        b'+O/e8X5N+1bdW1s+Ta/u+7xmwc89vo58Ric1SvcEdHy14Y1bt35B/9zrtd43b3WzqNQ8OuiftNSFseu8um6x9ZyvvMR60tcAr7gQ2WIJOACeskg79CJ7eQdN4E1CHeJg'
        b'f4HT3Q+36e2IA9znRq7zgKvrVwljLYKRTYSCr2SHgotceA5shJcJWgFPrcaXcMpxnQRMwOkisNOKVvhUIniRD1vhK0EBngxaeRZch4eK4+GxFocXP441k+QnQdd6NE4k'
        b'2l2zM0RtrgevSLlOhRi8DW2vgiKuYrVBa9KMedkhHhJD8M1FBt98sWoqFRzWMef9wNC7fjQhXXvW9ij2PtlnOvfEyScGKkYSct9JyL1V90btayvfC4kZlGYPh+QM+uXY'
        b'qFzf1DuB8cO+svOc/jkXXe/4Zg7Mvu07825gSJfpUGYf73ag7L1p8sGEsuFp5YNB5aN+QSN+8UN+8bf95Pgc0L3bnQn3Vdz2SxplrEl7po1IIvsk5wJPBvYvHpbOuCNB'
        b'/yK/8EY9tUN8fAbxcdWGBqNTcsq3Ij8L9nsUY78q5Cyzw35fm6f+hGO1vfwI6pgwgVNWy51I2ASMtQnLqjYhShOMDtkKrgUZch2sTXgIGdohR3vlCUJ73Jk8ggwnxE6q'
        b'MHH24hOfUeJfhqfFYA8HV9FIhYJ+uJl5ihpP0IqFuXFodswU6Gkyx8SSC77ran0tWJIFb6yDZz21J14/wjHORkkDhsGLaq1FMU/lil5981VR1P/X3XvARXVlf+DvTaP3'
        b'AYY+SJHeho6NKl2ptggOMMgoTQYQW+yKYkERBbGAFTsWDHa9N9k12ZQhIwEmJjG7SX7ZJJtgNJJNduP/3vtmmAGJm2z5f/6ffz7mMu++2++55Zx3zve8bZo3RRZwOTLb'
        b'3cHDHZq+3vm26ev8t4veuM/O1puwVm99y/bZe2zCFZTVRR3fFW+gy5oQr4NboGe5bSxi9rFNM0CLhShl05RdCQfUL7J4Cbmv0SJ3YvY+itxJDCH3AIbch2ZaUDYO/QKP'
        b'XoFHp1WXZQ9PIZjayP3E2n7QzmGITQkc/uzifoaLrZtM/bRoTUejoVqF9/IqZ/qFO5xMh2L46ZHjVoITFaNAquam/4GxWyxo2n0IcdPuv+fM1UfFjCI2HUpbRsfRIjYd'
        b'RG5YPqdHSE7nf0JyY8/fce906Qxt4Xh4HKx3LYHdoAn1w4FygLsnS7seWHJl+NPq1LcnXBZXIEpKKSw2qV/QKNYtyC7WLZ7J+X79nNQWwd1pDjGBx2TrsjmX1xSlCZwL'
        b'/l56L3VB37aAvmlmud4Jju2CesOCoILc4kdvowa06b31Bks9a7/hM6sONQJUzRCSAfnGoqImSy1q0kQTkopSkdQrFhTfZvdkRECD1s7tbp0W/da+71v7Dto7tXPbkhvj'
        b'BwWu7TmdCQqBqJGrdPM44ya3DpCbBmhRl/5voK6xzdbXENuI0EqKsy1CQYU2vc3D9Pbk99Jb6Fh646rpDX8+18iEyeamo9reuP8TWhv7jXK8u56a1rCotGgaJ8s3FzbD'
        b'016iRDbF1aHBOngRnJXeP5vGlU1FKerfe/WyuAwRXFJhsZrcCvSLd4iL1qxbkBDfflZvzwdhTm+3w7conYCMQneH0A2dQeyFtlRUNvfd3gVo28LzFhEKLqJboa3aanhZ'
        b'FbqM/yqdcdV0pjKFzVd5rlARmkCL0Ea9GcVvlo7Q2oC1U7voLPtUfJfbmdSe0D6faIVHjHxCbJ91rNw0Vou4dMcQl5JXLC6srqga98jU1aIqhqbKMU1VoGCpNk0txjT1'
        b'+HfSFCm9hedBdRqI2Eqd6NjYGTnp2YzhJTHBJMaY2CxTaaQRpi2WLFMa1VbUFJZIqsiABI5+DFIaFGKsTUl5taQqUPshSKlbJJUxIJrYplPJrRVXYzcvkppqcR3jrARH'
        b'G0rqCkvE2DUHRrjixM7IjCcQX0ouVoAPVOqroTKlRVpYX8dIimppdalEqYvdRuLESgP8Sw2dRaIJVi0pKUipgyFwCirqCFCYkltZUlEuUbKLxXVKrqRMLC1VcqQoi5Jd'
        b'IB0NYE5kJXjtYV0VxogTrTvmy48u2eepXH2R7v8r3LvdOKsvh3Ba3xeuon9kCbxNAsTzbkgqGU7LH7SBYzJ41aRqRQGXYsETtFcWWEP4GQ9wGnTLqmvjUtFr2G1AUzpw'
        b'P8u42KkGk1kwzfHGBl/nPBLT/JLSMmB9OjjnA3f6J2ckIu79mk+yP2Kh0KVcDd4Bm+YZxqbDTeTeAneXFsCmDHdM8cuptJV+REvUAZ5eIQoO4IBjsRQ9kQJNPLCDMH0J'
        b'4CboFrEo4XxKRIkwNAuBrsifDM+j9Cy4jaJoDwrsgdfhRUbr43YG2JmSmp5cw3wyoSmDuSx4Hu4B+0iBVRwDlBEV70DRnhRoFnmSLvPhsdmMAV8Ih+LCi4vgBRo2geNW'
        b'pHkF2eAwykXDHZUU7UUhXuK2MbFwqAI7QUOKH9hu7euHMWjSfOHWVJqyBsc40+bCSyRzKtjEQpnZ8HwNRftQoGUVOEKQNtFgNcMT3hikMolhI8oEJmA7uwBusmTMKlr5'
        b'ZiinTilN0b4UaNXLIDPnUJyC2A4fcErPlUNxfGhwHWyHzWRcJoDTQaJg0EWB3fAqRftRYP9Kd4ZHPQ0ugUasV5+G2GK9QNiRyAItbNhI2lhpMxFn41jAFor2p0BbGjxE'
        b'ssXDrhzGWIBoOW6Ca0EnywXuNWe49dtgE6gXBYdSoCGPdK7ZBTSQkYHdcH9ECgbdbMBwLtiuEW4FXcZgA3vKCnCe1Ao3wOvJKDcrJ4W0dV822ElQVVaDKyImb3pqupWV'
        b'eiZtwR4O2ArOwa2Mbe8dcJyHsvPAbnCENLsF7nBjhvZqEbylKoEZWrgXtBhXssMXRJNrz6rF4KQoKIAHj+aQdu9dOYn0VySGt1V0wEJ0cAmc9aXhnonwHKmxHB6DN0Qh'
        b'AZQxaKfoIEwIV2Ar05ibYbreKdiogqZ4UrY/ywZcRd0kOCs7wBprUVgAVbqMosNxK7eAO+RAZOW44OmPKEYEsBVcoCjDSWxTcDmbZKvJRk0MC2CBayyKjkQziXiEq0Q9'
        b'x5YHN6RgM4rTYrLMTnMoQ1O2JbzlTYYV3EmJEIUFU7AFHiU5W+frkHyxWLqCKsSYOCloOgsXIrbVDlwDFwi5ZYQsRdk44ZkUHYWqg+vcmOKawHkqJQWcpeJiKFYFPQ2u'
        b'SyYNNANrrVAGFtwJ2ih6EqIacHo2UT3KAPVmKXgT2IY/DvIsBOA1ll6MA2MufgHeyAOXA4K58IoxRcdQ4DBogmdJA3lwM2pbQyqaOAnsYFNseJtGpW4H7Qy59US74pzY'
        b'u8t1io5F/JAf3MmM8RW4HnPjW1N5cGcxxcqj/XWiGJX1/XAjOwV/zzwNtnMpDodGFV6FPdfTq8xpjPNKVlon2LkINnGpVwqx/VItPFyDxRE+YB+4Q+yPMxPhlhm+TvAI'
        b'hixq8EebXpoPWrQUNd1cxy4H3FJB5/YkjAAc4Y+iLaAH7mSBZndwnrkFkaZexsi0TTwKHERU5EP5wE54k1jL84KKUxaC62O+9qLdlUO5gdPcGhlYz3RpK7yoDxsysKU8'
        b'2gHM4anZ9HywTmWOfxJ2gTUp2XA7Z7ozYg5bKdjlDVoZg6wdQZNS4G13v+RRWFo05TaDK5WsVDevRxe2GaAj4Qpa4OhfANxMVqUz2DbL2ws0ov6nwR2JvskMNxjIodyz'
        b'uUGR4CZZWeZZaDdq06HAeStEiehfwUxSd02w1NvGa2xeFuWewxVNRIcDmeAmE5OUDF9eGmo1AXa6BU7DWwwVnmdFZKHDZnu2AzqtVtD2GB+MbGy7KtGGn4O6C0+C4yjb'
        b'cUwM29D5QfCZdudmEFQycFIbmYxGLHYDB15dPI3BtzqXy4NtRlQKmwI30b9ofwar92Ys3gt2oP05HW4Hd+BZ7yTfIA5lB/ZzSim4hmnY1rxXYRubgvUsCtxC/8C1NGaw'
        b't1WACyO50X54EedmodxtnLJVMeQ0rM1AB1cDRSWiE52SgvVTCBqCDtpl12G7jJHWYpAZEwv2ojiwgWnw+sVgIxYXgEs26F7gVOBACMgS7XI93gzqMaKdWfCyPwNGZg+6'
        b'OWgMWsA6Zo475oBdsI1Lhb9KgRvoH7gG60mDpGHTYQPqyEZ3ajG1GGw3IoTtBuqNUnx9kxLAGXDWIxlrvFtMY6MzdS9sJwWuhnfgDdhmSNnARgogurmiDy+TrOAy2ABO'
        b'p2h52kKrohFbigeYkvEzhwemyIyMWOA8BvPaQcFzNitIH5dM9YENqIc94BhVQVVMVtPwllhXdPlIhDukvokYN9qXtEdox0F0f4JB1GqQuNJyNiXg6k0r/6juTGU9xYza'
        b'qRkmWGgCLs1Ed4/loKMuXfp+mQdXtgZdoRfe9D+4N6VCMc30j/21u/+wLDjYaOOxDmeTuY7uGwvuNk5be3Xmx8W+c+y9DnvdO/UWd8nnd3e55G/+7g9/qPtjbq37YlvP'
        b'S5Nbn1cUh37denDv6q67z1p/2vJL3R+3pW07+Nnfr7w1e98PgrDMD629L7aKPo2pLUiSzHzW4PVe8yyXx5f+ufsry6CTTVMimp++WrxB6rd+2UOLeb/8wTdv6IzuO429'
        b'B1J9pD8v2nDE9jtR4fQv/nohIuOz7FmeQDnz3M37KeevPSh083j2xqKhqqvuNvOPdm88v7sv3rd/7unOrTX5sd+E2AQuKtGtWdelv2HrJrlQ13pN13Hns2Yb3E0TbEFk'
        b'dAl9T27qZ77BSFi6SHefLvj8ofegu66DcE/IhrR1cu668unznXXnXVuavVP4yju3jFetC6DWHXc21AMew5GvuOh+eE0vivNppOkJW2C0rtJCl230qVV05ZqZzZzXfvjO'
        b'KzLK6VI7f+nFDwfL+dlFz9cdmrQjqtNt5azXX+vpfPSXb5ru7Ci6dGPA7uezptM/PjT9lUd/920Wen0y89zHS3fN9z0kKKuvmXiQFdOXkTNzVtT5xRdfzf5LyMbV7OGp'
        b'ZxZe+Uj2emzwx9+5Pc799Lbp89VLL3oGix63/nG4a5nXyhWnQ4Jdvmj9co7YOsL7oUFay6ofd1RLam0K/DM+mVF8uiGn6eD3iZ9N/kWYMfXBqfjjq1xFO+//aHYztvvt'
        b'efVmjhYbtiQ/ypK8Z2L2uYXP6l+CT1U/P9A8xeX7lTveddo2tE5o384pyn8cu65yw4GOLsM8859mfSnluNg/7+e8vqguzfTjz85+6tux+o+fpEiy5Z8NrV2wck9EpdOz'
        b'hycDD/R91j2xxwI6ndogrw669Ze2ZR9wrrbYPXvvzhvmZwwMajwtiMYPO3MRaLAFd8bR+SEaP9msp3jVlLya5J2Oriab4BGKBfbTaXDXYsaqpQ3sXoluPehKDo7DPTyK'
        b'E0eDWzRN9ITY4Dra90wqDavgFbCdZ2BSa6THo/jgMLsCHAHHGbzsm4gpbzYAp3zQkQcvqIXqZvA6G928rkYRmxxDfOVSa+Dag9Mq+xi0AvcQPdrkGei0bfAnNjtcdBAe'
        b'BetKWeim7Ehye4O1xPmZSpiomwZuot2zCL4Gu58SYWi9AFxHC5sGGywpVi0dXbCYyN390I5zTlu1F23qZ1m+cEswMZ6aPDGBnNXRtipIMLgDHidqWKBtSYhKDQsrYYF1'
        b'oIllJqshXyU84C542SAFnF7xghrWctBNhiQ7Gm4gOlHGsGe08hQbdFSD82Rs4Q6/OJLIDG4dpTvFBkfBdc5TD9yOE2AtuoY3YLSS7YRXwPZUZBiky2jKO4KLLo3H4Fnm'
        b'48Za2DpbI3oFraB+lPi1FB4go1nnD25p7GW5lAxsJfaygahhxPzqFLhdwOhrqXW10OWAhbblbnj0PzZYGg2GwRYXFSmNNBIT9EjEJH0clW2tJeU4QQWbJep1CGWsdnrQ'
        b'33S5Q/rdOY36D/nWLbzDBq0GbUYKvnsnv98zotczoserzzO+jx/fSH9iwX9o6yJ3TbjPf8/mTRt5Vvaf7PtccxS2uXJ+7oCFQ7tVn8VE/LkiZVcK/o6BSmqP7xQpBP4j'
        b'T6dEnbVd0j7/aQrvaIUgRpMqtGviuak9MQrBVK04YixVqvCOvZupECSOfbEIlXE3SCFIGPuiWOE9uadqdPHkRYnCe+pdc4UgbuyLhQrvKXdplOPRb62jTOEdd7dAIUga'
        b't1WBCkH8uHWwFILY3/xCqvCednfCOEWRF86/1o/xipIovCf1oOZG/2qOsT3/1UEcKeqZr52l1eNISjCh3b3T6rhfl0u/dej71qGDnr6nZF2iHl5P7S3ju7K+8JT+8Ize'
        b'8Ax5Zo4iPFfhP6vXc3YLr6W21XjA2qGluPnVfmuvXmuvzqILi04temAdTr6oTVE4TpUjYrBzOjzl8JSWKZ25XQnn8nqK7pRfK3/gmzrg6d/FO+fYwjlg/BuSDDpMaA/t'
        b'9OhzEWG4uAQVibazTup06DzCH9+8ewXenQldGaeS+32myH2m9Ij6feLlPvF3Xe7WKgTpAwLHw/qt+u1TFQJRvyBPLsjr0bnncrf4fn5fwnxFTF5feF6/oEiO/hUUDQgc'
        b'OtjtCZ1T+1yjFMJJfYJJpAbVxxWr12wv2vbMUASm3kdDmDHwslcO7bz22uPG/cKwXmFYD08hnNqHVwdT/JQ+10iFMIrYp48tI00RmHw/mrT7V19puh2repWsCJzOrLLx'
        b'8qCVOePFjkxXBI6sgjHFpSgCE9UvRuVJvs9VBKbLZ2YoBJkvZktXBKbcn6UQ5AwI7IY8LT2tnlCWztZPKUtLAQZ/sdmXsjulPbSP77lP2xrDgJHn4gPs9+Gi4J30BVCU'
        b'w1i8246C02rxLv4mmmFJ07YYhe73mGwQ8W4rz5M6ZRA8WuFz5NNBCcVY4ZOPBlh8SeXqjHw0oEeJLf/bSmhC6kWxpZCILR9GsTgfsInk21DumUBpWGhQD3bCgwDx65Qj'
        b'tRrcdIS3wV5igx5Si5gZbB9pQxmttrGYRe79bHgc3BChIyiIqrYPgu3gIONCB14EnbaiYMSSbFlKgWaq0NuFxFeDiwtEwTws3jpKgX2UZD6fiCcKEW/cSJjQHMyTF0u4'
        b'tTS4DjvAZqZVa+EaeF4UEMChaFcKXtIBu2PjSQOCQD2t+lprZLIcHFZJ3eB2u3TYpo/dI1P5cD06+w/wmJLOWsAW2MbDGg6IOzMFr5WCPeRTcMFcCcRf6nwpdprvnJnX'
        b'04ktZjppXrUQ3oJNsHk5PAWbYTMXsVObKNBdBq6RoXEIAWdVX/n8DRxmVDPi0htgO+LiGFsvrLniICK6KzZwF+HIo2B7bJYvZttouIuGF+F5c9A8l2EiUWfBQZXF/37Q'
        b'UIfKOUmYSK4+hmZFP5ZRAnByGTefjKqlI2hS6e8gpnfjCnitiKweokvma2yDqYKmZpvRp82I2szPAl1zHluI10bpmZSlFIk0SzHlfM+ehuhwgWGEqScTeWOVYV0wO4Ci'
        b'Zi7wkVaXMZFNIfrFk9no1mW6wLCgppKJXGKvQ31Jo3uycIHPcMJiJtIjjxtuRxP9HJ/mMCElXfn8Jle2AY2U4l7zreY/pYNp/E0zKmb6FUTHHfOY4BUYev2vR7ZMiZMF'
        b'VF/7Q84s19KPrv3wxsqwk92iPW9P3eD+B7/9T6euvhPxWlHeTf+5g7K51y7Gv9GU8X36ldr6E69/EBOX+f7hB73dqT9mzegfLN48/56U2mFyxXhBVNBUx8sLP59Ts/br'
        b'qEHTyfP+9P2Kj94802IWdlX5B8/uL9568+tNc36gPtzxtyDl5t6gqewlVHD2wqy+ZXkfbCmBbOmhI2n6+8PCqtN/Esb/jbfZ8q1O9/ia+pMh7nVPonw/dfz62+AHIc8+'
        b'j1jwRe7fsk4+rzv98AOropbXfjDv+ujWh6fd58485zPwtXHtw/Ll3Mk6Zj3zL1s7yBv8bqzMLnf+6o/d5089WdFbdOYXy407Ix49K+x89jz3+b6fg7yicr7pz1xa/JV9'
        b'k8uJZPulT7KeDoV8t6/y4fpSXsxqeU1HgsfR1zcpImiFTcGms5Gnny4/mb7n879+evCR2fUVQ39zO+W0qS7htjOw/iKxZuL7Ex+Fn3lo1lg58eOKK+0ffKGzw3zBqY+v'
        b'egqeYqsbboEBaFjKB1tfohkI9oLtdYRT0AengohSWLqvF03V2erCbhZ6uwl0MZAC9WBTKWZfsGBGY96PHQ8xTNQWa3iAsYLwZVPgeDC26ZihZpDOzF5GLC3OwQNpWI6G'
        b'/V9hrL1oNjgPd5YSBig1vAKjqWMQvS00hkMIAbcnIG6tkTB5gbwpL1p16NBqHs8IbCTQiDkhmKMIBbeSvLEs9DwN2j0Qi0Q0lM6jwtZpKz6y4GlTkRE8w/hF2u4MTmic'
        b'dJOPEuAGvGI1m2PHCSJJ4MFly1EKvr/a/TYRXZu7scFZO1X98IZJgBbbxIoWmYEtUgZL6ADi2dag/JaIJfJ5gSkCm6oI7wGvWoHLKuYEsYetGnxDL8A44Ib1UxGD0jBj'
        b'lmyMyQlim2LhGtLUyYzDKHCsJtHHzw9/aUINhafYsAkcA1eZYtZywZ4X7V94xAJmgZTMqsAS8aEoSSxYD3ekcCkOi0b7VIcRGVALeBlc1iALoh2qhyh1TZARmxbEaR5P'
        b'/BcaZE7wqj1YAy8xPC5cP1XDAZvATYgJRhwwPAQ3MU7Fr8Dd3uNwggdWEA6PYQU3GDEI2+vtHbUYuDx4nrG3yQPrCLFlOMCeEXxtxMjfIRjbiWDdb7Ku0UI5UHKworrS'
        b'WMPA4WfCwXmwGdDnudYU37qxuimind4zZdDO4ZEpHyu/9pu69pq6tmd0si7onNIZ4NuSf9aqW24/37OX79nP9+/l+3fRCn5QV1CXSM4PQ68ZsMFOl16+bz8/VM4P7XLt'
        b'50+R86f0uA7yhe38k3Yddv3Ogb3OgV2BCn5IPz+qlx/VE63gTxkp26uX79XPD+jlB3SZKfiirpiuWAxm8fKqBxGfyekXePUKvBR8735+YC8/sMtZwQ/uyuzKkvMjyHt8'
        b'4W6awRTRiV76dGZ2opeBY9uNYam7XF/zu+jXH5TUG5R030MRlNXPnyNH/2bN+c9SYzzDLrd+/mQ5f3JPkNaYhPY6h/agHkX286f18qfdRX2Pxa/tO6tQN/v54b388B5z'
        b'BX8Sk8epw6lrgmYEYxT8qcwEjaoNw4B0uffzY+T8mJ4EksCaGQrEfjGXaAUaiwl9fN+XvhmhgKEw+0DzJ5S9p8VwOMW33RXa4qGwcHkaYW/mNhRJmVmqCeeB6URESszT'
        b'A1P3AQvrfgu3Xgu3TosHFj6PVMwSt5PT7xHV6xGl5gfFrSb9An+5wL8ztl8QKheEIpaPc8fgmsETNu0ZT/9A0c7xGLXZMoEe4qHa9hnsMmiJfWAqHNCuy9p2X92uunbO'
        b'SaMOI4W1XyNHBZ7Z7iznu46oPsr5bgOuHifTOtK6JvS5hvS7Tup1ndQzS+Ear9L/LsCuz6ztGg1eVPL4DZgj5J47CnLkJmYBbqHgWzUL8HfEAsyxpmlzrOHxu2wN3Ehj'
        b'lLr5jGa7rGoSLjweBzE0UdIj1mpVU3FMIg7CMcYHTe7cnvRf0TXpObGJ+WsR0y187SSAIlXYJfx4gCLpnrbjgYEwpmzYCXqVCAfYbrYqBLdBV216pP6F1S+IAQ5jcUGU'
        b'5ImuKNHfI0pVWAtGaZg/MzozOi0/e87M+CwlWyapVnIwdKLSQPUiKz47i+Gobo5GDTH8T1BDCNaMNhAIM23Y5zYJsPWurIulwv8Y5plgeA8UPJ5A8e0HTScO8IOecln8'
        b'4Pq4xzzK3nXQ1H+AH4xi7EPrUzUgHyIM8hFCQD5U+B0+GL/DTxvRwwvH+JAYS4dBUw8G9cMysD7+mS7byG9Yn2U0k36ma2A0ddiWY+Q/bMgzCvyeQsGwKdsojh6iSGhI'
        b'meFF25rVwe8okduj1ti3Sgb4Lh1ZA/wJHbH4V2Gna/tc8uOUS2dRe96on84dsZ2c9kitH44dlu3V7YZaMXathe2uLagIpw43FGOP01i0Z7fr4ypyOoPbU4ecTO0xVquZ'
        b'9RDFtzEf4Du0yobY6NcjlDlriIt+YTxb5w5Rhwyl9xvSwTG6lKUTU9CQHn7WpyxR6nZ+S/KQAX42RAPTKmsPblk0ZISfjSlLe7lD4JAJfjDVZDbDz+aU5QSmwUMW+Jmv'
        b'eW+Jn61QZqYfQ9b4WaB5tsHPtojX6WC3x7UsH7LDz/aaZwf87KhJ74SfhZSlbWtsO6clcsgZP0/QvHfBz64jnRng2zAJH0/EL9wm2hvXpw5l02jmWkUtKzuT+pxC+52i'
        b'ep2iFE6TFXZTBkytWtktqZ1WffYB/fYhvfYhCvswhSB8iMu2M65PGdaPoY28nlA4HE5kBRjZD1MoYCwb8K1ImFI+oo4v8SS4Y6bZ7LlgX+0oHl7twfvJXETtk8zGhYBg'
        b'VXMw9IAzhUJT9L+uiKX6pfVEIA+0n9lhOkzRmU7EuF0/11TEyeQw8ApqCUM1dz7PmcrkWlOZvEwdLeAI3ghwhI4WcARvBDhCRws4gjcCHKGjBRzBGwGO0MQakFhTFGum'
        b'FWtIYs1RrIVWrBHT50xhJp/0xxL3zR/3TYeMhAEJ2TPtqRf+y7QaBT3g9GKKsdAD/6I8699bno/2O1VcDM2hMp1z2Wg2eETFTT/XMNc010ykl2kzZlZMiQ8DEzJjtgTs'
        b'wExDAZl2YaoSCSgCJ9co11jEzbTH6UZKMM90qLbIpar5mQJilDlBqUuw0FLS46XO6EK6vJjA5KrjhIWlYplM6IF9eddKqmTi8iJ8kEgl5Z76+l7ZGHuR8a2HXUVWFMgq'
        b'SiXVjMNH7BSwtAJrGmKng5LKasZPJMGD9PLT99RR6omLaqUyrGqoNFD9JHqFuozbNezSvqi4VsleXI7iyiRF0poyFKdbiRq0tKKqqFBXayxVrh8Mn2Ar0hed3K9hhgQP'
        b'sUEuFw0vj+jxGokMVJCYullarjUr9eyoXC2HELl6o0RvulP1iEDuhVhtrGLxY0Sv+knl0mopMX9TARarh1VaLqsWlxdKNJiYI4MRqcLM1Hi/xDlVepbYuaVHjIRR6CRe'
        b'yz0ZP3PRQpUmLYNdLKypxFa7YcIi6UJptcxvTC2MH3hVPdhF50tqQa/VdZQLxaWVJWLf8aqKEBaWoCoKiSPNEUeUqpkcv0/MW6FHGqIXVKXaD/tLexQytkeIRBgfinEJ'
        b'ucJScYGkVOiBfmq7kfT0G+PQkUyKjNQyuilkLDyCtLriOVIRIsNIYSqBBcK5pvunjrjfZLqFlkmWuLAEO9QkdRJ/pmh1qBBLawpKJUWq5TA610wUVpQzrjhRTgJYip6Z'
        b'nqoWETMmSdUjDknFqmEpkFQvlUjKhcFCjyLGp6MnWX/hIw1XLx1mmJgnobRINaCisQOqXl8qR5aqJ2GVZKFUhkYELWO02sl0+ghrVMNaU44dTv4GZ+z6RAzdV2aGhdTh'
        b'MwMXpC5IY1OMl/XrARFqm0GVG4WZxGRQI3HJUBkNwnZ4gXhm2zjN0BR0TCGuCUPz4KGX5yd+09PBaW3fbocrDeEx2BNYg3Xl4XZwGXSPW4iWSEfdiulwH7Fe7AH1BqAD'
        b'nlhCnCuC22BP+rhFJHlnCWCbtt3jGrhTDzSDa2A/GQE2uM4ZLyes1wjF1JWvjlfVfdUAHPVOJmrExuCg1Xj5PdQyHnVmt0KS+To4YwDr4TpButT8lpQj60JlJHpSG9+b'
        b'bAwCDLmP9j2/Lnydnm2qs0C84JFpzuUJ7pvSJ7M3f7lWT3ezx+x7mXvuvfnzN3/6au3Ad2ZlkeGeNxu+SxT1HJnhX3K34vHX88L9764y+qYy5KGD5fBEy5zkBzlHylx3'
        b't3Q2xB2ab3D5/5yc3gxznZh8ovHtaWC1VUlt8wdhwb6LrspfSX77yRe+67sknQ/TYMiRr/Vf+/myZJb0w03F8ZM63lnd/RfvwBWF4WtOTHwzwGv//Uee+gRBJTBHFzTM'
        b'AF0LtMVzWDQHz0oZsVk33A/PGqQU1L6gkyBbReRvC2eDg9ryvRTYChqIdM0JtnDghdgCRrnBMAg0gDPw0owXpXz+AiLko2NhtzbUGttCtAreYtQmuhfDdVgM6s2mLBYx'
        b'Akgb2M5gsLWADSIicMOiNNjsw0jTNsQRcdwqVOdr6G3TCrjzBRkpL5GMAtxssAA0RC71f0Go1xX4FMMT81d4M5dPX3gZXpWB7XANvAV2YqlsKpEA+/KoNLBBB43ExSn/'
        b'mSLDC0wcWvCU0kx9Ao5GmbFmwFcf19lQLu6IJfI8Wq6YEIIhYgYtrBqr963etVphMbHT+YGFN4GUma6wTZTzEwdc/TGkjDNJ1G/t0ct4SYt+YOFLkiUpbJPl/ORBZ9eO'
        b'rE7B0fkKZxEGmmHKfHXXqwoL906zBxZeJHGCwna6nD9d5RekLQWl1GNSLtu1rGlKOyrVjXG4prDFspxH9k4kye8q3NnzpGOHo8I58F8ndXFr5HxgKnzRd8SfMDf8Ng7e'
        b'wcG7OHgPB3Ic9P5reyocjOeAHc9Q1cdYSIEugjLs/fP5j9iIz4amM4m7rszf5agL7/RHeEHUJYPJ/x4ozgigy8jd6NeQcTRkpQbGyUFd0IJ3YW5e6uvPOJAz/z4ojgpe'
        b'xTBf6271a/Amn2I8Atyy/SMtcxzTMnID0bTrP0OeUd+/Xtaeebg9GsQXJ6Y96gvRCwP1n4wRJx/d1l7WljzUlicj0C9z9s9h2mTHtEnrhvffGSBOPrrUvaw9Yjw2X9Pq'
        b'sfHQXP/EY/GLZP+9WVNf2F7WsqLRs2aLPy9o3e3+SxOml6++/72sLQtfbAuarZGbo/YqCxmRTy7BwQr8pb2QrVU3FgDaYUaO+PDT0zK95BEGDnsy0CN+/LAXP8zhGqpY'
        b'OM4oYL7/3BCTVZODGqMfXVSEHcmUS5ZqzzlaG8SlTDy68DMPmAEWFxWh6zG6VItV/A7xFIO9EPgIF1ZV1FQyPLBYWFhRViAtJy7I9RExeY0gVnn5CL20wbXQM8HvQokK'
        b'tDzfkxs+Uy12eK7hIkcKihRmVZRhXodhz7E3BRWulbigooZxfINnSFKk7gvmL7B7dQnuUpG0uBjd9dEOwHAZoxupGg/iDAd1e6HK90PRCJNSKC4nPMrLGMbAUC02S+ih'
        b'9jCvYbi0x4FhRl5YdEKP6IIqSWFJOXZer+IeiUcI0hDNvMhk0oXlZGoYF/JaBal8MAml2q2WIkZsocovvZrBCiSDHhoxwmfhkgM9fbAARFgkKajG5aIUhYhFkuKHQjXr'
        b'R6hAStLLJNWk7+ERaM4SsE0nEaCMJS2pRBY5MqeobGm1KgEzDiRmhI/0yKooLcW8Y4Wn0MurDDPTqPplXl4jXDhp0agSmChNEdNRd8t9/RPR7lr+sqIY9C0Va1ghIw1W'
        b'IXKNmx4TK5Nam3z9hGkjXCwh54qCRZLCaiEZQYaGsmaEhwYEqoRLWHbEUK/f+NWMspmNHMPt11ZICyUjBBMjKZUsLMbpPIXzAoPmj1dEkGqYayRM86TlpCF4FcTFpaXN'
        b'mYNbip1D4aZWipeVEVdSkiq89foIy9C4jPDEWhUGja5QNXzY0n70eOKY0RILhrr81ZRFqmUuCjGo0Zj2cR5UvChg/ourZ7FkmVr+okVmKBZRaLlMylRaUUxKFRctQjND'
        b'+oMTEH9Y4jr8m1nbjGRmVCIZERVJC0uqpQtxU2SFJaXwJtpZSj0jNXl8hWhesqolNWixjyRAFCAVqrqAVlgZosj4HN9scXWBBIvHilQ50XQw7mVKa8oWS0qqVNGiMdGk'
        b'NHFN8fKaagnambC/QGFuRZWMVKrKExwpjK4pLpEU1GBSRAmia6or8P64WJUgJFKYVF4krZWiyS8tRQlyymTi6uWyMS1XpQ4drwn/ukNh42WTalVb9vJqw8fL//J+RZCO'
        b'a4ZmzMiQIJuZaSzHGlPvCzOp3bziKlS7B+7rSJniguU1Cz0106edXBjmppnAUS8CI9w001TuL9ZMyehkoW6a4dckQ4M6Ur9WmnDt6JGqI0YlRvWObFgqK3q0YlS/yP6M'
        b'zmC0FtVL3SOL2SNHNliNUX6kMBY9CJkndGZ4pKBHSTn6H02rEO854fNfzBY0OlvQmGxBo7IRy35my8iNzvZNihN65GRVo794fwkZSTZi+c8kjc8hKxlHCD0QUaqmGA2r'
        b'phs1VejIL0S7Razql49Q66yLz8kUesyCx0qqEJGhuoI1VWmBCmgyj0SrKlVnlS2uqZJ5jjr+fu34JEen5iQcOcKiR4lQxz8TCKBBpDAd/xHOCwqY/+vJgphkQSSZZjTU'
        b'SAiqI1P1jK/X2uNMYBFQEvwHvZivr1kliZKqqnL/hCpxDQpK/fwTpOg006wK8lqzFnA6Df3jDJoFoJ0TUX18CTpU0FrWkD4pC505RUwx6sahU1MiqcY7L/6LDojQUedP'
        b'QUVdpBB/20H7fzE+JVEE6kPAqEQY1YFJJS4V4odRKQql1ZhgUDjq+GGgKPAb5gfJ6IPPdV9RYGgoGmlNHRgaAlWA/4yagWIxal0CIlrtSAIegUYA/xHOCw0YuyxUS0J7'
        b'htSIFZHCGPSLOTnnBYWNej9CWiTJaBH9qP6qcS5UKZnx0CxODGqBjpCY6HQ0HJoVUiAtRBmSYlFRiEL+pesxxju42StsAjY0ZC/2+crAU+WD42ihZMQi2gUeIEbRLNAM'
        b'WyyJerEZOGsA60E3ts9W22Z3z69qoFXoRCvEk2ET3AU2MH4lwWZwlbHvv4RVnVM05rwGoM0Y4zyADf41fhT2Bw42BHijV8lpcAfBFQdnk9MIOGA21vtuyKTqwE6HYL2F'
        b'YDfcQYxGxUkzWK/rPzagMDqgIHJSAlUTias6VDNpBB1QCxsQl5TIiCG14QHh9pQg0GroCZr56UQQJv327Ru0zBb1qPOx7cHMd5LhNNNDgx+V7nb/gj57JLrT+pSOy9wJ'
        b'uh+/0eVyL/bLaFboyS/MVgZ+8s7glTal+/JKYVfrP18tnvLM+RdOZkQeODHF9a7egXvmH7wlXGbwbd93V6cvcvrLV5df7z4SwP1+W0/kpttfeli0NcH+Jzsu2Ng9trYP'
        b'2vaPv88SGr7VWfphjdKz891lxQ4mT/UDs0s+/fu7dR+uKj7688rHU64PbXr4TcVHnd//HNHdJtvoFtW42mWez64/TxBUWW8796R8r97/BW1dsvwPd1YXVpf25jz4mRt1'
        b'x7Pxipfs2Yp78z5yCz4950ha2U9f/y1v75umu9a1viL7akbnj8dbhljvdmz96NymyItZV9ft5ue9UR5jcfXPGcED0/xmdNx7fhH0hfH2Bb118X1PXSJvngYvoDEese8T'
        b'xoEdLN+yyKcqm/ceeB3sL2PcgasM/Ha7Ehk2aAUH7L3hlhlJ4CyH4uW7l7ImmNYRCXhaXNYLAOsQERlHF94B5xndzgtF88YImrdljCtnZnEJlLp/dvII6iDYCk+PlM3A'
        b'DtpkMSqp+1aCLcvCZJg2fD1wWuz82ww2skGXL9xMLB2LIuGRlNQkmmLBHUsyaS9wMMzT5L/pqwjLPoSjvFZr2ZcoDUckkWpDvRRaBcfmSAl9+p0C5E4BnUswYLpdS/UD'
        b'C5dP7CYOTPRoMcSAWq7ttcd9utj91sHvWwcPTvQ+ldVl0VXUE9pdelfUFzq9PzStNzTtfqEiNFPhm9U7MbuF05Lbaoi9VfMOTmK8V++KG7B0bHd9YOlOCvZqwa+xI+y2'
        b'kQSfYSnzVIXtNDl/GnaF8kpnhNwqpJE9YGHVUtTv6Nfr6PfAwo+AHvbbeffaeSusfbq4D6xDHjp6yb3TFY4z5IIZQyy2ZeBgQESPqzwg/q6FIiAe634SiyCLXoHvEI9t'
        b'5ks0IV17+a7tWX1YYdT3fb5vLz+ki/OAH/LjUx3K3g3rEQYOOnp3xiocA+SCgJ+H2Cji56e6lMAZvTPzHbSd2MlW2PrI+T74nZnvTwTeDrpbx7lQcIpL3BTqdReDuCj2'
        b'6366caHs10O5+PcUg3gr9ht6uvFm7DfMuOg3Iz83YeTnGhkUtgn9XYZFY8hglOflUWZG2GXNIixFx18mMYpUhh1NB2IZeiCGwwv8PYqG2FnD+I6XCQQtRwVxzc2lcnki'
        b'zv/E+fJCT1bVX6kxXmqcxjm4nMjBNaeSQ+mavq1DTVuQ+pX3fAbSFTbD3dNlNRng0qKQALidQ6F1Ta8qh6cYIySCJnDdGDYboGEDh1JnUbPACQEB5wCd4CBoy2Jy0fAG'
        b'BZsE8IpjJDnPaHSWdWHTImxWFLVUkgXWM7Y0O0FjJbZEwmZIJbCpEOwG3enEbKc4FJ7BuooWcc6UM2jOZ5rXDvbAc6KAgABc5jEKHpgM14I78DyDudAILoM92FAJu4xk'
        b'jJWIqRI4UsgYHh0Am0tjqtWmSqiys6nEcicD7oY3saWUS1gQFeQEz5CeCniOxOgoAhzwpXxBC7xadZRWednKcoN3sNGRxuII7oIHQTfcqEveu8Bj8CS2LwKNIm1w3FfB'
        b'MUbNjGzut8DRNJmRCDWHBc5QZeAAirkDGol5Tle2KSVcsI9HVS4o/XZCBmOz4yg2ogTZUjY2+VmV4M9EmqfrU/yS77mU6YLSbQkRTGT4HB5lWPknHjb5eae0lDEg0wPd'
        b'4HDWzJkz0fDFoVvITbBWbMrMRAPYDvYEFWTNpNCuDE5QcK1jFQFWcQfnXLNmCvGEX7bk6cEe0IHGt5lU8lmWHmUad4eFFlnq2RURTCWp7uCqIajPwrVQcD0lhk1gL4PR'
        b'cr2mNGsmaPekqMhV6OoC2mAH3F0rnfreIVrWiIZ22KvsXPY76QBdFT4qlxp4eOjqGiUG1Dn/AO79KHvQUjloWPyXLRa9i53u9Q+JV4a9duXGlW9jOpUnBouLb1cU1776'
        b'7aDOK7GGZq8Xzfl0wZSHgZIn35QCl1XXufV/3b09Wh6R9Pms1l/mF8TOvkKHLp/5k2Xr5wMF02d+++2zCdSWyuLmc8Ved6zBZIv1e3SsTq0/e184OTftRl//O6K7DhmP'
        b'LyxO+ofLtKXeKbLdl95632H9zcvXN25+V/rTH+1yy2pNzD8K/uGm5F6d/nrfp4nrSp3qq0Mu3Ype/heHQe8obwOFz8KIvelJVgcjas337s75cu5p0z2fffl5OMh2t1nu'
        b'znZqCTp7+sfnbyye/YH3B5cO2c1defnW5NfOOXm/u+hVr65NUz74fMWeB7N+uhbQGvze47OHY39hrTX65s/LHvQ7iAIvDmTPrdnx2btzJlGcAM6ki2k3hG+Fusd8d+SH'
        b'hVXfPfun8C+3g49/YFxbHfrPY+uXDG22SV8c0T2bt2KxTYmj01vTBxeLL/zzoUyQ8It42Fs/as63DxV//eLAtKFnRjUx2R+9c9yT/xTfKuEReGG19lUhGuwjZkgvXhVe'
        b'ge0MJvIReAiexeDUdXCvZxp6rwtvsMAuaSrBLMiHp6ahO2oqTXGcaTE4Dw7Ogc3kMmRhvCzFxwOeq9EGIN7gzVj/XJPBw9oO0OhsCbgITsJu4mu7BHTCEyna5kXg/BIV'
        b'hoQwnouJ/zRzqbrKQsTHfOAnn/dvTQXtHHCV8YV2uCB9lIER2LlAhEj4GlFRyIJXZo0xMLKazbEFN+0E8CApnDMNnhttA0XPmQAvmREjKgN4gYPNaTRaCejWVa/STFgB'
        b'zjCudQ7AreCY1oVvDzgJLtk4MLAGu2CHX8oo2yPjGYVgPTsG7MpjUnS4gTXayAgmYCeaNexKfPerzDjuLfJO0bY7MgZXTFax44prmAIOwat1oGFEQQHejFPrKCRaMJY5'
        b'R9DSvT2iBsFh0SvhbqwGAQ+RCkwDQRM2KgKXEM+jQYqGBx0YU7JOO+yQXVtHAhyFZ1V6ElX6jOf0q+Dmq9pDDa4Wp2ipesAOcPDf8IuuuQNgd5oqn+jkKqjlEx3taAxu'
        b'gxPxiY6d3hgMCF37hQG9wgDGKLxfGNGYiFGl6w5P3j8ZY1U7CNst2+Z2Oh/Ma0x45B+G4arPrG6Mb/Foz+2z9e7l+zziOzFGJ+1VJ5d2LB0Q2A0IHNutDpoMCIT9Al90'
        b'I+tC17LgfsFkuWByD79fEC8XxN/lY7zW7JNzOuZ00QpBUL8gvFcQ3mOmINbnh02wJQjO2ilWCAK6zLss5IIQ/MK41VgFZJ2hEPh3sbrYckHwoMCuJbHfPrDXPnB0UT0x'
        b'PbFywTTy/nBaa5pC4NUvCOgVYNMiAWNaJAgf28xpKEePdb8gWS5Ivpvwa29L5IKSu4n9cTm9cTn9cXm9cXny/IWKuJLfn96BGYm8jrwu1KcwNE69aJxQv6ehceywaJ99'
        b'1KEPo3g7kJFV/cNdiiPKIsbtVX0Cr/GjUAEDAifUpKEQuwCrJ5Sdh/VwKCVw3FXbUqKwnjgcZmfp+diEco4cSqAppwmHS1pL2lcoHEWNBp9YCB65up+c3jH9V0edlPwr'
        b'U0W61O8W2uuGjZoEkWgcegXYqAnjSGjoQ00mQ2Z6vqh5em7Ww+aa5nV6/2Ch5xaKaM19V9oQnxI4NBq+CBb9cn0TAhY9dnlUWaOF8Blbywwn3ommzYd+rxmOGF+3n1Jj'
        b'/H7w1FdkAk/OVaGI4kuyDvmETIl4qosyaxR+73/uY5RVNTz2ojyehEeHOJcH2+AF51He5Ud8yy/M1niXv+LM3INvzRei0+IMusxqXMVPgM3kngnOgoNTGNNxo1fqePAQ'
        b'uR07gxMl3jOCYDOLorGr+OngSLo08y03WsZF4/a8Zc/2jLTFrEDTVUm5/WXeyq3/bJ//2iUdk7zhzK/mRE/ewPlzfOO6BbeSom8u/9IkbInFM1PF/oiilps3W4eLs6fG'
        b'hIb/A7bmNyVFv1W6wLvN5JHv6zNvbBIfnLfpR6+nB6P9LTabVtZXTKj48dx7GQMrTg7Wif7x7rxf2oR5z99cplyef1nPa/HGGul0/o+rLHRabm1/7FLZfnfGed3vfrwf'
        b'nycP+lPACp750/ZdHwUs5Jl97vzd4X8oN/5t8uzv8n+JWfjjrA8fSJuWTA3u/fq449bIvnXXvmk6e//Qt4OnlfOPTTj003PLM8X8XXqvmfzt05tP5XVPd4iPt9q+M2+/'
        b'c5+HxWX/j5qOD+z+bJjj4+jp4jdH5Scetrk6eScuXanxE18Et5MTxzUOXtP2Eg8bpsAe1iq4+RXmUD8I1k8i78/A9Ro38LeFRCUvdiq602r7gAdbwokbeLCBcTIfAjaj'
        b'GdV2Mc8TECfz8HwGObLtQ9BBqOUlPpDCfuIXGTBimmbPUuIlHnQYq73Ez0ogBVvB9eFq1xHYfHjEeUQYOM/oIh6IdSAu4jsmjLiIB62WjLrkPnRT6FF5iHcHnWon8WCj'
        b'B9hMxss7PZJxEX9tmdpFfOR8coIHwDtgr5aPeD7cD3azQEcp3MpcEbaji9Ua4ia+CF4d8RMPTqWR/laXG+F7GDg3Q9uOfBuH0ZFcA7v1cbP0Mdqi2kv8KXDkv+smnrjC'
        b'VnmJxwf4iJd4XZUwJ9l5HC/xnTEXpp+afiHtVFqPa7/P1Pd9pt6N+WPyveT71f1x2e/HZf//0jG8hXm8SOcNkUEC57/rGB4RHOXE0XYML/w3HMMTXwKeukqDfGyNKcYa'
        b'K7KqR7j8z3Dwfzj4Cgff4uAxOUtwYISzcYhkgjHEJMaZvJFzj0V+p3tajmuPaUVT2kaZv0Fh8w2a+DWqlpTJGAHSeA7Zzf93DtlluFfahpfai+EtWhVgAyEZtg9VuV/n'
        b'GJl+b0jcr3fEtiy7WHgv602Lu0mDNvbt3tcsrmX16L0Zi32RZ9DDnIlG7o+piYwj9gx6iDxn0mqLTOyI3SacWGSqvKVjq0270PoUjUUmds0uCCMWmRZ2g6buA/xAFGMh'
        b'qo/VxEzBMdNoEqXKFoCzBWmbdqpjiOf4xxTLOI1ulQ2RvxctmL9Ka7v9cR02/c5hvc5hPXp9zjH9zom9zokK52SFfYrScUJHRL9LRK9LRI97n0t0v8v0XpfpCpckhWPy'
        b'D2zaIYV+QtGCVPoxG5c1zKuhjXyfUTh8ooNjhkjMcDk7wshhiELB97W0xgE7Hztg5484YOerHbDjPT3AH7TLRlhlLrgG1lBGtix0KbhkxBAmnS5NmidiybAvNf8jb9Rk'
        b'pCzGIo93vji+5bvO3pKQ5e/4RvDn/uTirmjTXbvOckPd191Tb90odLT68NY7r74nzjsaY1Ustqz9lP9t2M0fJtyHgqqpFne/K5m0mj7wLnVGPyLm0oYvQia9eXPpF39z'
        b'XDb98b5k0ZLcGd80Sjev72x9/nlH4tln1ts537q31tdmGt+5VPPW5vc8L2W0dH93st4xKOVw5IOTZtulMVn7ew9YXTk+/6uOyZsb5l3Pqo8OZG3c8NkJq8ifnD56uyfi'
        b'lbU2S7y6YOI+4Zn3Uy7fm/SHf0SlfjFjW3Lf3WN+y7wk9yevO52UaHauJM2uStrGGyjc+erBAzlRr3CNv48u+KRM8umBn7xqjllaZ0QeKDq1ofa9xr2feeSb/PGbqFOr'
        b'Um4sOhE1mHOm/X2fPcmvZSYrT7oYzo5a9WXRo0qTeQPTbu/8VP7Q4txPlgds/5aT95ntu0dkP9FRf0m9d2nAk01QImFTXgg6nk5XI+6cDqfgjjR4gZx6Uj0fra8i8Hah'
        b'2rxAKmOwB+vBbrj3BddKYMsE1TeOfDtP17FLk/fS4H+xEfwbW4crc4BOI/+9sIWM2UywvXxphbgoP78K+10lhyo2l/8FHarBlJHlEEdHz3rQxLwxqGFpi/O2la2y9qB2'
        b'8fGQtuWdGQdWX3Ttqupx7q7pyeiuu+x3L+6+OUx8EJT6UGDbEtQiPhjSpteejPi0Lus+Qbh8Unqfdbo8M1uek9uXOeuB9ayHVsJ286Zyuakrdn8zmx7Sp8z5jdHNlvUx'
        b'w8Fmeq7DFA48Jur5DlMoGMLBcDY9Sc+2Mfcphf4Mv0q76tm2WD2l0J+hdJrSNx1mVXH0vIcpTfiMhGj16psOkZdD1XqUwL3ToM9aVG84zNPVEwxbVbH17FFyFD4j4dAi'
        b'HVJYJilGEz5hQlzY9+Tlj0PRAloviR40dzpmKPdNUAinK8wT5YaJP8nwLrHVMJ5F7YsWofANlkW8perLh4OShQb83/vS8b8hGnzJXDD6K9p4Rw+mERLYEkKhGE4xkKZN'
        b'8bcUreD3GCbgK8cZXhR1wyCax5aebCrnyi6gqJJdn0i2TdYH0/gb8p+ttrCMG5pY7xk3ec1exwWvGZidMP+0xgo80XWcn2TKOfn34hbxu0beH5QOXCp8b63LPv/rGbOK'
        b'lm8yMO/se3ryzN+vZwUOzWkv+efzS1lT54V02Xy8/fVDuW+Z1NS+2fBVVFPs1j9nNcoXtv0pe0uSS++q2mUH3P9su27dprXx3M1m7kO6LQWbIqxmF2y0XRxXKm9/3Srq'
        b'myXhHxzMl7vU3xrwfeNnu0cdE05+8wDxLfhr7ERwGrZhFmAGui+vBMfgthQdxGVcYsHOXLiNXObjQefSlBm+8CJONMMXtMow+OxNNuiYAQ4z1/2z1vAWaAA74U4sBwPb'
        b'+cvATh3K2JztmGlJrvtl4KJhSlKaV5oOOLqA4nFYuqA+keyIYHs1RLd5fx5FZ1GyyfDoSnCd+Iypnprkncyl6BQKXIdrYUskh/AlpTFgK8YP3wG32YJtaRh+x8CTBRvh'
        b'KdhD+AOxaZ6MeZ8fSF7rJ7FAF2yC10n+GnAEbE8hhyD+AHxhdhqXMoZb2enw8kLS1EKwrXZE+wHuLQCHF6OsuORF9jWI19rqkwgbiuBZws0ZWrDgFT8nMgrOYCuRHW71'
        b'qYQNFmi4cAJ9cJkFrixKI5s4vA63laEUlwxB/dIlNfDykjrYbLikhqas4U424uavsUkb3SZ7pxCwrCS4BqAjYgeFpmQ/Cx7hwMtPMXCIDJxKwOPtnwKPgiPoKNiBv2Xj'
        b'GB3KzpUD1sMbYJen128+Cv4/eTKMu/C9yGkxTf3fS84LzS4gVAfkuJiLgudoG3hiS3EtBoz4/UaOvUaOB+oURh5rEgY4+ptT16bKzZyPhT/g+HzIMUL/PuI4fcKZ+AnH'
        b'9yOOyzBvrikX7a6a8BkJh+qElCF/zQwt4Zazkl0qKVdysIq9kltdU1kqUXJKpbJqJQeLc5Wcikr0mi2rrlJyC5ZVS2RKTkFFRamSLS2vVnKL0TGH/lRhDTjssrSyplrJ'
        b'LiypUrIrqoqUPMSKVEvQQ5m4UsleLq1UcsWyQqlUyS6R1KEkqHi2rKZMyZNVVFVLipT6UpnaZlzJq6wpKJUWKnUYw3qZ0kBWIi2uzpdUVVVUKY0qxVUySb5UVoE1qJVG'
        b'NeWFJWJpuaQoX1JXqNTLz5dJUFfy85U8RkNZcyzIsCbGgpf/JxSOmRLsnEuGuZ7nz5+jQ3zYjKaXsPGWPDp8QsLfs0tj7vKeIS/anrpnbxA9kf2TbjFWyy8s8VOa5uer'
        b'fqvuEj/Zqp6FleLCxeKFEhX8gLhIUpTuqUsYMqVOfr64tBSdg6TtmG9T6qMRraqWLZVWlyh5pRWF4lKZ0jATa0iXSeLxaFYtYKmogaEL5gozqayiqKZUMqWqmMWY1Mhw'
        b'aUNsmqYfo65xhowpA6M1Ot9zSk1p/lCeM6Vn1q9r16tr15Lcrzvxfd2Jcp8p99yhxwOf5AFd00F9K7m1SKEfLOcED1KmjYIPKFtS2/8DKvz08Q=='
    ))))
