
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
        b'eJzsvQdclEf6OP5upS196QIvnQV26d2GItJRwRLUwMIusEpzCyqJvbCKBUQFrBAbWFGjotHozeQu5e5yrJgTueTOXI3fy92ZxMS7XPvPzLu77Mpi9O6+5f/5/Eh8d95n'
        b'yvvMzDNPm/YryuSPo//9ahl6dFIyqpSqpkpZMtZmqpQt5yyzocb9ydhnWExIaSPjsCk574w+polS2SxmIwhfxjWk2chC71ZyYx4WtZpnUy3if7vGNjOjZNYCuq5BpqmV'
        b'0w1VtLpGTs9Zra5pqKezFPVqeWUN3SitXC6tlktsbUtqFCpDWpm8SlEvV9FVmvpKtaKhXkVL62V0Za1UpZKrbNUNdKVSLlXLaeYDMqlaSstXVdZI66vldJWiVq6S2Fb6'
        b'mdTIH/2zw41wDz1aqBZWC7uF08Jt4bXwW6xarFtsWmxb7FoELfYtDi2OLU4tzi0uLa4twha3FvcWjxbPFq8W7xaflkktvi1+nZTWV+ulddFaa6209lqu1lFrq3XVCrQ2'
        b'Wg8tpeVonbRCLU/roPXRemrttN5ady1f66Zla1naSVo/rXOVP2p66zX+bGqbr6FZ19A2FJt63d/wjsK0Icyi1vqvpYupIAvQldQqzivUSpbNZhG7sNK0C73RP1dcYS7p'
        b'9dWUyLaw1hqFG0PZFIYN+azKP73WgdKEohd4tDYXtsJtRflzoRbuLBLBnTnz54j58CbYRoXN4sLbcCdoF7E0uNgqWw9VTgHcBXcUvI4y7WBRtjlsMAA6lCK2xg0lALey'
        b'5ublROXwYCvoprhcFjgqXaWZhGPWTwdv50VXoEgx3IYK4FEOcDunELaBmygz7qUSeAAcBa1we1QjLhxsiMjhUbbgMhu8Ca/BzZpgjO4A7IebUKJLAqBduUIDL68QrNCw'
        b'KA8VvAR3c8AO2NGIkCVJj4FbXqAV7I7OE0dgnOFucOAVDLCifIK5YBN8o7qSZdJwPoaG24Me+7xbUOOhPuWiHqVQP1qhXrdB/W2H+tse9bEj6m1nRAuuqM/dUE97oD73'
        b'Qn3uo51U5UP6GQ2ObVbGfmaTfmaZ9DPbpEdZa9n6fn4Gauzn6mf72WNcP/sy/fxhGZ8SunlRFF0eJfJxomqtEPBoHJv6XO6IQuW1ujySbpOvDUW7BCBIef4PKrwpApTP'
        b'41Ixr6Nyp5cL2q3SqX6q1haB3ad4cZ+4UNMHGv8Y9iX7auwJj++zajH/iFB2swasKDrGq/6V3sbA6nSKgBc4fOm415EV/phal//B4h/4aKlRSiPGnfxqBurc1ui54eFw'
        b'e3S2GG4H/SXhAfDt3AK4O0qSI84tYFH1jjZTQDs8a9Y9dob6KnH32Om7h2fWNRTunCo7Y/Nz//ua32pc8wsKlbgFyUDIBD3gQvE88YK1s9gUm0PBw3NBu0aIyfI8OFRU'
        b'DG+ArWwKfTII0XOfxpVEOBYUz2NT4Ah4m6qhZsEzszUuBB7aCDv4cBCx82gqGpxO0DgjcEMhOAU7kktRE4kpMTxfTwp5Dd72LS6YC3cmLuBR7NdYk5rSNGG4kN2T4D7Y'
        b'qgQX4I7IPDQWtuXPDQf9Udl4rFMS2M8DGxvAKfJBLljvDS6Da6/wKWoyNRmub1ZkrsjjqH6M4n7jnnPwgymHN2zr7bjcsTwxiOOpXrFv+isCgfVcj60jhwWC2HyB4Irg'
        b'yo7EHfa1oh2HlyQKkqZf95vaYzMpccfhj89006dbg4u7lnle7vKKmW6rsrXLn+/m8x6/z4s/J37k06rH1KzB5Z5Syfoz6i2nZb+X5VZuPLM/Y/7Oj+p/Kkzqah5UpM4Z'
        b'7vo01GZDPruiabPCs76m5b8qHslmKTeFD/3k7KLP5e8O3b652VfyQ1ZCq5XUI7yk/PPQLPetwg+jCntm5cc7x7r+6M4DNnXtk/Rz3xaLeE+wpFizGG7Igzsj4U64Hp4p'
        b'EOci/kW5oPaGLVLw5hPM+HI8lPAm3BqZK4banPxCHmUHLrLhYbAr7glhbgfAObAzUiLKjSS8Dfa58ihHuJ7TIPd94osSzEa8db8dbu95aBhEIMpnU87wBgecK4S3SRGw'
        b'C+6yRiNjO9yNeucCPMChuKkscBFsAKdE9qPscJHSCSX7Fx8qe/Sg6fVjf9+6T65SNjTL65HQJOJYgkSpvGnqqL1SXi+TK8uU8soGpazZ/JWNy/obevx5PfXF6yzK3bsr'
        b'tGOJNuvjSSE9VcOTxF9SDvazWO3Wbay2xBFXz7YpI3RgW1ZX7J6cB27+Pbwe1T23yBE6tM/tgm+/74BqMHNYlKGjM55N8oAO6pl1zNYE3MfrWzkUlnzPLUUfd5+O09Fx'
        b'A/GDnGF6sml+9T23KJSmd2Yf71juMUfTMrh9NUwZI3TIKYdeh76mYTqJSfBr76Ch4MTr3MH5b9npgmcOe2cOCTMf++LaPPajhB6dKe0pXVnDrkFDgqCv8PBX4vEvchjl'
        b'Mw0zalVWptTUl5WN2pWVVdbKpfWaRgT5F3vLAbNps+5S4iGvxKPzmR6ZhtOnosdf1lNPX2OxWMJvKPT41MGjdfl6u8dsHkv4wM6lNfVTruPmghFrxwfWrn/+gkfxnAxv'
        b'36ow0zrAj6BO2yVyzFicUX8sxxyX10nJsfaIdEcZq5SD/nEVVCkP/fJl7FIrmbWWqmLJOJttSpkQd7N1qQ0J8VDIFvFmlpZdxZHx0ZsdUZe46M0KvQlWYzXGZpQ/j1Sp'
        b'kLRtJccEE66B2VZhTFiMGteJS6RImZjfI211m1FbXcMl/J5jwu+5Jpyds5ar5/fPQCdWqzjj+D1Xr1aJuBT6pWNCf5UcirpIYfvpIY5qKYqxDtl98IPJh3s7UltZrupL'
        b'2ez3PUPp1tQjzqGldvN+vLE/rdW3+OxWaWJJmW2lW3Z0UNMtkSBxxzx6cVd5YDftt0QeVtzuNCcs2T057nu1pX8tl/VxZ3yopn7t71zNfV/EZ1jPYTcFvMaONOo4kXzK'
        b'EZzkNMO9YU+QDkCVimvGIjmUIBQei+JYgU7NE3cUW5Zvlwdb85HSJ+JT1mB7bhZ7FSuPZIyBx+FBrIjl0fBkDjhHUfwUttcCeI7EwrNAC1tAa1HOolejcrgUDx5iwRvw'
        b'zdwnRC8JTI4UZ2NFkLKGb3qDg2ywGXTEingT0zzPwKEIqY9al5Up6hXqsrJmR4YqJAYA4UHlDA96rGZTUTEXpvRPGfTQRWbonMLbuHsFXctGhJ6dee1594UhOmFIz7Jh'
        b'YexAhk6Y2MYa8Qs8urx7eV9gX2xXA0prN+Lrj35sH7h66PP0cD8ShjzmUEJPpatxnPNHuSp5bdUoF9sbo1ZNcqUKmSZKLOmV7sYq8PGwLccDlxmuAXi4Pov+YpwyAT3+'
        b'up76RsVmsQJeYqx+hQluLz+YOm4XzalkWxohFcYRwoyPKjYZHWwzbYhjY6brmI4UNA7Yazn60fEM1Dg6ap4dHcbPm4wOTSSmk8vwgpsdEq2tiAJbo+Hu4myG3ubOQdoR'
        b'm5oGe9eBXXxn8Iav4rdX/k6ppqJM2ov9Bz9IQAOntyMWDZ29sWec3b/YFwNXIY1CML9WIDjjFfC30KweiXv+0lc+76o43Lj0e4JDXtQ5la2X1z0Rl8jsOrAn14y2wX7Y'
        b'zl4FB+c/wR1DZ3MRbq3wBJLYu+FuibhRL5e913LBlgbYSwpZhsyKfkzlEnBijMxBJ4rGXbzcpS6vSMyi2E3g/DpWRsgCEduEpHH/GOgZiYVquVqhltchknYx0oQRRqg6'
        b'SU/VmZj8utRHX+t+Teca8bF3yFBo2mCJLjRj2HvGkHDGiIdPZ3N7c+fa9rU9smGPyCGnSBNa5SkD8Qe59dI6+bMUyiMUaiTQKEygFpCpNNDot+upr2dyWCzPl6XRPfxA'
        b'6g07Med/mYu/GJ2KUDgjL+tZKk2AZ8wJle+cBS8r7m7OZhEq7bNeR9j7DRcjnVqg0h8UhvZMdc9fcxgpwpf2bLjMo/7Ra8sXOYg4T7DBiYjyODxlTqeHw9mrQsHuJzSK'
        b'jxA0IDI1kCg4tMaUSlXgOGHGiKjhaUylUTko+3YDmXIkIs6zbJZDaHKMKFUWiFJlRpSxeqIs/A6iDEK8t9O23bYr4a4Tbco7CT0qsfE3ymuS1mrGUeWzfDPBnCyN6NRQ'
        b'JqyzAJGl/0uQpTIEZbTMMgk5cowsE5uUVBX3v4FtjlMqeOPIkVeoiUZhfzjol5eTDzdG5ZRArVgsmZudOx9qi4oZoy0b2W8SFqWGt2z48DB8m7BagMj1xBgRh8yzxGz5'
        b'znAXOKA4We3MVskw6YQfOPhBHDHorndc7FAkunI8harOmLjpGba/Whb+1raLHTpd25aABbs29O7v3drbEdK6jcVBlB7/jfW+AaCJ/yim5GJsDP2jctYjGbzX/f1top/a'
        b'XDvY3rtnQzyH+uvfnJfnBSI7C6sqJeAK2IiNoOiV2eZGUJQrUUaaZwQbBkKsPRkK7FWxMsKtJ4PbjSbjwGQQXMkEW0DvLMKtWWAAnAY73JihMMat0VjCWkkguArPMHoJ'
        b'N4hoJkgtcRF9p1ZiVMBH+ZpGbCY12+uJk3klw+RVZph8sYhDeQb2BPdx73mIP8ZWxbRh7+lDwukjk+gvKbbzbFZbJuLfPQmn0nvT73pIPvYTDUVMvSPURcwa9ssa8sx6'
        b'zMOJHvMpZzc8mu47BeicAnqCP3IKMxlTVsyYCsIP88FkgrsVpWf2BvNhCm5jc9TrqDFO/3ThS3J6ZkiZ+mjMtRAO8dEQB5qeu2OfDOc/5pN5Ae7OKVS82jHCJaR+/WgN'
        b'5tcBWwIOtyNyP9EhRjz7bNXmoflnsc9iemJ+17JLiy5+tumuRHDxtEAQO33plR1X8kf+8F7Fu8Iz0s0PlvxwCSyBc2AtR/a073IM9ckHpZyVC2M41d7UDo2z6o+LFwYg'
        b'3cMTD8UTQQsRKUvgkTG2zl610JZRndvAbStEovAtlQmVBoENJFYAroE+2BqVC97OgTvFfIr/KjsIjdmrpOAAAewlztFT8O08o1Je34Qo4gXsSkwRNG2iZSOrVaVWIubv'
        b'MMZt8TuhaDlD0Y9rOJSPf5d7b1CP7NTy3uXDgXE6r7g2/khQ2Km03rT7QfG6oPjhoERM3aHteW2ZXSEjnpOO2nXb3fcU6TxFfcHDntFtGcjmZkxtTOChX/Apz5CeBcMe'
        b'UUNOUeOFxYQ0TUSFCUlnYpJ+BnmNgaaRSfxNNaJpl5ehaQlGg1346B+IrkX22A7BihQy7G3LypgpChQWlJWt0EhrmRhGtFlXouFU3aBcPWqtNw9UymDCM6oU8lqZilgD'
        b'ROMi8o0MRoL+d7EfE/sfU0Cz3kouxvGJuIs2Uw9dPbSYq2izRzy80MPdWzt7xM1Dm/U1l28f+sSJYx/1xJZjL/rGlm8f/tSJZy8mTa7BTHEpOAOu2+UWLEyAu6JzWZS1'
        b'gF0O3/YcJ6bw31fz8LBmPeMIYJdyZRwZV8Y7xC7lsamF1AAl4y+zp8b9yawME0WG31Kr1dZoGCPTf1Y9EvKrvxVmyisU6galvD46TymXMcFHTqRPHuFR/a3LArmyWVOt'
        b'apRqVJU10lo5HY+iMIbfCvLl6ma1nM5SKlTqfrZyFgI++gGi5a+7XSgqr6Fe3ZBeiLqMDs+QKeUqFeqwevXqRnp+vVqurJfX1MnrRekmL6pqeTV6qqX1Mov56qVqeFNZ'
        b'K6HnoA5vQHkXNCjrXySdpcKWyxX1cjqjvlpaIRelm8Wl52mUzRXyZrmisqZeU1+dPmu+OB8jhX7nF6vFObJCpSQ9ox41mDy9BOlKtdEZy6UyCT1bKZWhouS1KqxB1ZLv'
        b'1quaGpSo5GbDN5Tq9GK1UgqPytPnNKjUVdLKGhKolSvUzdKa2vQilIJ8DrW8Cv02a0yyG14qVmLssGeK1iOCQBK6VKNCH641QZ6OnTAmLj1PXl/fLKHzGpSo7MYGVFp9'
        b's5R8R67/npyeDW/WqhXVdFND/ThYhUKVXiKvlVehuBlyZP8sx+WG60EiQxw9W45oBx6vUqtwLXGTjk9Nz84Xpc8SF0gVtaaxDESUnsPQido0zgATpWdJV5lGoFdRejFi'
        b'CQhJuWmEASZKnyGtX25octRG+NW81TBkOaZhcaGmDhWAQPnwOHYFLsetxjQ/AubMyCjEcXK5sgoxHhQsXpiTVSKe2YD6Rt/4ZCwo6msQreFy9M2eLdU0qsX4O4iDVUj0'
        b'39SHzdrdEhy3vVkl4sZVIm58JeIsVSKOqUTcWCXiTCsRZ6EScRNVIs4E2bgJKhE3cSXix1Uifnwl4i1VIp6pRPxYJeJNKxFvoRLxE1Ui3gTZ+AkqET9xJRLGVSJhfCUS'
        b'LFUigalEwlglEkwrkWChEgkTVSLBBNmECSqRMHElEsdVInF8JRItVSKRqUTiWCUSTSuRaKESiRNVItEE2cQJKpFoVomxgYjGk1Ihr5Iy/HG2UgOPVjUo6xBjztNgVldP'
        b'6oC4sRzZyIaXRiViyIj71asalfLKmkbEr+sRHPFitVKuxilQfIVcqqxADYVeMxVY/ZCLGXGXoVFhgdKMVJD0hfB4jRK1m0pFPoC5HiNjaxV1CjUdrhe9ovRS1Nw4XQWK'
        b'rK/G6bLg8dpaRTWSUWpaUU+XSJFcNMlQTPoAx8whc0qmhY2JcXEpwgIxjHCc3SxCnx9FhYzPEDdxhjiLGeLpGUqNGkWPz0fiEyYuMMFigYkTZ0gkGQqkjFwmbY70EqSf'
        b'EJhavkptDCBOZAzGmyZVGZMxHTFDjsRxtQkgJL1UUY96A/c/+Q6OakYgLHoRlzZ7jTN/RexHqlIjaadUVKkx1VRJaxD+KFG9TIqQqa9AZGvscbUSHq9GRJRTL1M0Segs'
        b'Rn6YvsWZvcWbvSWYvSWavSWZvSWbvaWYvaWafz3G/NUcm1hzdGLN8Yk1Ryg20YKaQofP07eqSq9oiMYUI0uRel3JUpRBfZoozsjKLMQXWf4a1rsswc1UsYnr8Jz4ibSz'
        b'l0kcN/GXzfS0F0mGWKWlZGYiIGmcCEgaLwKSLImAJEYEJI1x4yRTEZBkQQQkTSQCkkxYfdIEIiBpYjmWPK4SyeMrkWypEslMJZLHKpFsWolkC5VInqgSySbIJk9QieSJ'
        b'K5EyrhIp4yuRYqkSKUwlUsYqkWJaiRQLlUiZqBIpJsimTFCJlIkrkTquEqnjK5FqqRKpTCVSxyqRalqJVAuVSJ2oEqkmyKZOUInUiSuBGOQ4WyHGgrEQY9FaiNGbCzEm'
        b'akqMmcEQY8liiJnQZIgxtQ1iJjIaYszqo0cxSymvk6lWIy5Th/i2qqG2CWkS6cWz5mSIibRSq5TyKiQE67HMswiOswyOtwxOsAxOtAxOsgxOtgxOsQxOnaA6MZihL6+H'
        b'Nxur1HIVXTSnqFivwGFhrmqUI3uYUSbHhLkJ1CC+TUCz5RXwJpb0z6gN1QxcrzUY3uLM3uLT5+idKyaZx7ldYseD4saDkJlTi41iqRrrpXSxBhUnrZMjMSpVa1RYrWVq'
        b'Q9dJ6zVIvNDVcoZMkTi05AYQmWRRYOGukJFs35nYQvkWhJLlsscnJC6msdahkfJN61Ve0pRVOF7fyEw4ziSMbcIxT9W3rPTCfmtlFvbwzcaPbEo/X6bMwY9c7EXkqRpr'
        b'FWplHvaEsRjnIPah6R2DBcQxyPjQ1uC4dINjUIQdg17a7Md8yj16xC38Cyuup4M2+0tbyt3nMTfGeSbraQWLchRuk7fNbF32VTUr3t17WxbjHsQO2JlZjSq4M1LpBLdF'
        b'gX4uZZ3EXsul/we9g9Uim1HbjMrKBg2qXX31qMMMREKMFSNtlNc+cmN8g9h7/K13JiKqOqSpYG8wzdhRaEgoECNDSfC61FEu1qiUJSj49U0EmF/HKEgNNfVyurihtjY6'
        b'G3G4enFeM/bXjL2O8cz0hXmlNJMN++UwN1YpVBoGgONM35kxPBu7ERl7gfnQjPni4sqaWngT0VIt0nFMX9NnyGvl1TJcESaod+KMheP09la6oSWI/YAVTLmeVRiMQJpR'
        b'svSm5JjTS29EEtUfm48oMRqsamJm6Esgn6tVoAQkpKivaqDFdIZSbUBFD8mpxzmfAeJkcZaSxY1LFm8pWfy4ZAmWkiWMS5ZoKVniuGRJlpIljUuWbClZ8rhkKZaSIZ2l'
        b'qLgkFgHymI7BurOcAOPGAdELXSBH/Nfg2aU1EnrMs4uADC0bXK0SGuv/BiueceGOdSOdH5mfnqWpX062T8iV1YjhNWMmheEz5tMJqYzYrjIkwS5mS3A93TBRFgpMLyXm'
        b'Ba64sk6KI40kYinGSCoTZYt7XjbLkQwJPSeb5UiGpJ6TzXIkQ2LPyWY5kiG552SzHMmQ4HOyWY5kSPI52SxH4mypz8tmOZJ0d8xz+9tyLMn4fEKZmFJin0sqE8SSjM8l'
        b'lgliScbnkssEsSTjcwlmgliS8bkkM0EsyfhcopkglmR8LtlMEEsyPpdwJoglI/65lINii9XwZuVyJLpWIuGrJoruSrlCJU/PQiJ+jPshdiitr5ViX6VqmbRGiUqtlqMU'
        b'9XKsZI05L/WSEzO8DE0VdrMZmZxBlqIozHnHBDIdnlHfzCjYeH4QMeMChRqJRrkMaSBS9TPRz/Dh8ZnHOPmzccpaeFWlVxPMYrLJbFGVGmklRjONSBIx0Xcs2hT6muql'
        b'ORL9SNJglbyKKON1WMCr5QrULGqj3zkHac5qRZViudSU+5cSs9LojzZVMxhj1GRe0lRNypIzlopcUYGj8lGv4Yk2FaPZTKyomfqaEd7oy9JaTd1yeY3BMU6EINHiFiIt'
        b'rlC5yLJKjNfZNpsojjdxfIpBLQ4yUYuTR9xoc7XY03ny07gxpTjZZ0wnxrP4cCc8Bi6q8gvhrmi8b2Qb3JFnRblVcDlwUAAGYJ+ZeiwwqMd8NlKPhebqMVGI+eifHf4n'
        b'Y6OnK/6HVeazvDNWTFYb9J+M1vK09lpXsmbexrAippSL92jKrDdTMpuztmf0y9tK+QRqh6ACE6gVgdojqIMJ1JpAHRHUyQRqQ6DOCOpiArUlUFcEFZpA7QjUDUHdTaAC'
        b'jG8VW+ax2brU3qyert/xz+as5xlbk5oHaNn6unNlXiZ1dzBvPfTPFv1jVRla0coYMi/d+4yNoXRZoJZZ8oc39TmhL1jJfEy+4CgLQvE8rTXZ9udC4idttil1QjBnVDdf'
        b'VDdnIxauZ/0Mpot+46CD1rGKJ/PfbG0s0WU1H5k0waPWmXi7zcziBd9G29ImfwYwzfBDZuOrWYp+nnIOJnBsbT3C62GUeOnZI7zqltg1IsEjjMQj3A+P8HLPseTKakNy'
        b'JV5LqSzHSXBLP8Kb6x5hShVZjdpKZU2IxSrLFLJRm0rE6OrVOOggZcZSWS3SVNU1o9aVGsQD6itXj1rjle0Kaa1+wYtdlQIpp2V1iP/UFFZamwwF/CmyPmstZVhxabob'
        b'l2zoY6HO5mqtUOMx2/n4VbZk6Rgi0222xqVjNmTpmLXJ0jEbk0Vi1mtt9EvHnoGabuf7ugM1jlnL4r8cpiqKZrmK7Fk29oeCLASplEvGZRkHSEP2lbSOHmvGNP1uZcRD'
        b'sftMvx1a357SevW4EvBf+AzE+tQGxiuS0Bk4P2KSlTRZRUtrGmkkKpJpmaJaoVaNx0uPhrEHLWPBRFvGwDhJ9B04JH4XDuakk0bnk1+MwuzofEOsHjGVZVywYMUiDQlE'
        b'CV1Sg4QcGiFyWqWpqJXLqlF9XqgUZgUOY42jkmgpKgK9M/jTtQ1I4ColdI6artMgm6xCbrEUqb7yFXL1SjmeJKfDZfIqqaZWLSKb1VMm7gv9kEmjZ+pDdCX2soYb52ZN'
        b'vLOiiUoxDLc0A7WqjJ2J98Y3KOlwZqXPcnhT2SyvnbAg/UK1NGJOYtULFcPQiJ77hMurJXRibEwUnRwbM2ExJuM9jc7CLzR5wcVVKerRqEE40qvlUoRYRL18JZ4obkqS'
        b'JEhiI0Tjm+o7FkgLmF1XClsn6vjiWRTVWC64tnAZpcHr6WB7icxuMmwtAGfnQG0O3JkXDbfNwcums/NFsDWqUAy2w935c7PBuezCgoKcAhbKAnoEDbAV7CPF3q8WUNkB'
        b'cRQ1pzzq2OIySoMX+oMjr4EbFkoF+1KKs+EuuC0faQFg27Mlb14toMB+Htl+fXqlDZVZTvZa16bMIVtywRvclXgpp2E7brZEHJGLCgfnuVQS7CtZwleB9eBNsqeY4Obl'
        b'aEV9Fu+P93XnH0+Zw+AGN4Fj8JKlKkMtKrc1CmO3Q7RgTboJauC60g5cSgXnFBr/EraqB5Wzt795ze5YBxAjmFV3qr+jpNFXcmfKDVnAJ+tZC975JYd2UD3S5e3JHrS1'
        b'P30i/Nu/fLPui8ibGTcfW5dufKU3gv3oqxUbv3pa8CftsPPDyUvOfZM1708bZqR+P0F073hX6Ikz8/K/HLp3dtpvVnRHcD8V/kMd+X5hi1v/hexvtnrM0B5qOpj5qvNT'
        b'n8z7n/82siJH9V/ZnR9d+n3/qk9n25/+48Oj/g9/HpX6m5+LBGSFd55bMWjFG/pBr5NhS5tjCKeqyp7slih1ABdAa5FpZ7Mo/nRvuInbDHaA/WTLRbBbhR1qc1EBHIww'
        b'rEN3Ay1c61T7J3hFNbgBrr2C1+fingUd8A1D77Io9wCuHTwFbpHl6uAQuBwRKQ7PFrMpvl0lOMAWgwER2VIM+2C/GBVh7NI1YAeXcgHnObB1Zg1ZyesBNoLdkRIR3B5F'
        b'UXwKtICz7PhZcN8TfBRCQdhq0Ep2Ahs6UAm38CmXJg64BU/FPwnHn78WH47rqtdCMYao+2ELuI1JAO/f28KXwPOLn5BjHs6Bs+ASrlQrOOEbFSHByVHq3ZE4Ka3i2aNq'
        b'7WBwPzw3BifEii3+uHiZGH0ZdHLgljB4iqzGt4F7rEw+rVeA14FT3mCQC1p500S2/8KuV6wdPLvjlWyhczYIYfM9gDqKWZ/cZEUF4H1/9iNB4jbuPSf6gat7u6orrWPd'
        b'sGtYX8Bd18iPvYOHQrKHvXOGhDkjgZEorSOTJrVj7bBraJ/zXbyhBaWZPeydPSTMHgkQnfLr9RsOiEVJHVDSNjXebIWTGotLHvZOGRKmjARGvCHpq7gfkKwLSB4OSB2X'
        b'wVh21rD37CHh7IdhiRjJ4JHgaPwbMBIQhPOMBIW0cT8y2zhjz6yFbsCPRvxYgR/49AOlCj+wsqVUU89bLo3d7OX6P5NV0xO06iOcZTJ6/BM169MiKxarkvU1hZ8vu524'
        b'hx+DFPJ0jtnmAJaBl08ivPx1ahk1/q+YQroZq1DEGrUrG1OgkH2H24LYdzSpw7fWk2uldRUy6VSTihhAziidCmuz66mukvu+Yp2veD1FWvZbvXzTF23QhcKR3JSJG+pr'
        b'V4v6WaMcWUPlv4R5FYO5bZlR5xqPuHKreeMbcBaiJF/Z6nE+WtZdZsDYn8GYKdICwv9OGzuWmWtmL46uh3kTx+p8Yw0Ii56r3f3bqNcwqNuUGZSpF0fa26yNX+1+1YCy'
        b'1wypSm7Uzv5tFKsMKBo0tRdH0RclUXbgBASxoAk1vP8MitZleh3wxTGkWQZejRtxafdSQyMGTahF/meIVVBmomi+OL5BuNPHKFWi85UYKfU7lNUJ8DZuMypHj31s/S4n'
        b'w07r/+wep6oX2uP08/RBtioCAfr/GHnwA6/KBLKhj9mVinc4zXHLH5xfwlpB9iol/IwPZ7wnYhNRjrSQjY5IloOtzmMS3yDvwWZ46QkWM2AA7MwxVTYOwA16qc+IfHCL'
        b'N+HWZ6syzF3KypqdTCQOgRAxjjeR4Y1zuTaUp09XwtGp3VOHPSL6iweE92MzdLEZw+IZOo8ZQ04zxu1xtiT3mC3OWNYxRHEME8W4D4eyxrYIfZ1j83JbhMgG53Z+ANVr'
        b'F8UR2Y5a6Tkcsw+Ir1Ir5XL1qHVjg0qNjbtRbqVCvXrUikmzepTfJCX+FLtKZGI21DF+Fo5aWj3Ka0AjXFlpZ9LbDobe3oFJjWv5/DJEfvb6favWWkctW2uLyVHrpOVo'
        b'bbRWVQ6ELO0QWToYyVJAyNLOhCwFJgRot1agJ8tnoKY7Wb/+hGfBf5Ihk6mQgYytPJm8AnMq9H+lft0sLScrFF7AhUIMfGKdS+kaTbXcxGmB2lWlQEY/zeyrwv4HlVwt'
        b'oYvQOB1XDmaZdXh6VVHX2KDEvhZDtkppPTLgcVZk/Cvllera1XTFapxhXCHSJqmiVoo/SexdvOpaJcE1VWBHOeIW+iL1PgNc5rgyUNEalaK+mmBkLIaOIF0e8QItkqWv'
        b'bQ12Co7HfVz6cLVUWY2+ITPwYpyfxq5/Fba/VSs0uHUrlNLK5XK1SpT24m4thtrT6AwzwU4vJosdlk6UDX85jSY7nxZ/5/6nCUthBlcaXUx+6cX61bgTpjcMwjQaT1yg'
        b'riLulsWmq3EnzIuHbRo9Ez3pxUVK9cTpmIGNkjIB8o0oOqe4SBwfm5REL8aTFRPmZrhBGr0go0Sck0kv1q8AWBq52HR318QfH2Mi2KnEvNC4INM9BRNmR2wHNWYNGhpo'
        b'uKoqlYpGtV6CYzrFp52QsZVRq2pA9CuXWfSHIXLCqbH0rCVnMJLOltCZjFOMDNHAYrW0rg5vOa4PnNA9RgYDIiyEQKN+aMkU5BRIKWrWlQokpeWrUI/rB9z4cvBfYYNa'
        b'zgwTMvjl6poGGeIk1Zo6RGgIF+lyNADRoJGj1qmU0w1IAbJYDlMlPGiIt0/FVFOhMkFJQmchpmZgSBZLMR122DeISB2fcVlZiyrMHG+pklvOWa4/4bKhkmDOzI1OrlGr'
        b'G1Vp0dErV65kTuySyOTRsvpa+aqGumjGRoiWNjZGK1Dnr5LUqOtqg6INRUTHxsTEx8XFRmfGpsTEJiTEJKTEJ8TGJCbHp04tL3tpT5xLITm2EVzkgwOq/IUlolyxpDAq'
        b'B6sH/VEUFVzMq1GBcxoslZdGqOMpCp7Mp2KpWLCHOX9QYY8PTqpJcZheni+xm09p8PEnfolAm2dQM+ZCbSTcWZArnofPL5gXjvf/L4Ra/JMXFGdFgT3ggg3cl7pMgw9Z'
        b'y4St4Ca8DHeBvXAX8WxYUTzYzRbAffC4BqsZ6+B6uBFelsCdedhV0oqPfNs5GxwpELMpf3CCC2+AU0sZl99xsP91eDkP7iiYD9sa80W5sDfRpHpzoLYQZd6RN78RPYry'
        b'c+E+LgW3g4128LhdmQZv5AbbpoHbdhJRbhZsATfBUVvKJpcNj651I9tu4X4X6QJPeDkHZWdRHNDJAuvR1zTYAQUPvAoP2EFttARuQ9+LAv25YdhJqGVR9GweF31mG3My'
        b'4A0/AbycpYyOYFHsbFaSVRJpV3s/PiWgBssFdLngU9UUihzdWVcgVNmjhrjCfNAa9IHjS9izwS01mdL0KIRHcLy9vQS2wyv58CLonRYJ93Aoj9UccDa3gbRwuAr02ElQ'
        b'CepQ1C05uDE4lBu8znUEgyWKzGgBRzWIkn18SlU39GOHjTEC6mFT5SbWOeuNC9e4756a62r/86FNLtk7rk1d/0XAqpy8gFVdeVfX/P4fN26dcfQshxta+b+MO3Ddv8cK'
        b'HP7s0Xv5U7Xy6ogrsvRfXlr76DcJrkezrnZ8o+TWnDm4+JjNzz785zdvt537+OFJn5HWmxGuJ07vDC9OnTvnN28s2ae1nf9J/fXQHuU0+e3uyhKXzwbvrtC8eyajp3n6'
        b'+w/eTU0O2PX1qtJ1J0X/+NGFhoxV01PWsf70s0hR30ERn/gHV8CjTYyT0eBhtCrGPsYoeIwowyrNKnh6Xd4zjjfG6RYZz4O74fkAxpPWnxtCPI3wDXCmwMzVSMMNxNcI'
        b'L4BjoN3M3cYH2+ERvQKOCHKAHCBYDvaCrZGF4pzX4J6cgrwouFPEotzhTW5cCbhMPKM24By4nBcVno2obTdCB/fxGfbqcHhJ5PTvHB1o0VWHH2bn0xlPFLCVymRljJrX'
        b'7GpUu8eAROX/TK/y59tS3nQPr0d9ak3vmmGvxDb+iKtXV7TONWLINW5EEtuW1TVNJ4xkfHXJHa8Puwb3qO+HpenC0gbn6sKm3nWdSlxrM+9U60IKhr0Lh4SFI4GiNn7b'
        b'ynbHEVECCqzVOYWOTJ3Rxh/ySNM5pY8ERyDgah32u4WjUFO7w4go1pCODkYhTbv9A1evkXBJn3KA1YcPIUzVCUNGxPEDGQMz+krR+1SdMGLE3euuu6hrSRtnxEnY6dDu'
        b'cN9JpHMS9QX1KYed4u47peqcUgdDP3LKMLFanBmr5QRlWN57Ej9O4UcffvTjx2n8wFq38ix+nJvAzjHpDNzu5WN/9Nh5Jcpr2Pqx1A0ibADNQLH//Ct29dlgJ99T4ur7'
        b'4qUdfngy/RQ/mbpml8HmiGxGBTK8EFqvJo7aM8q/4ZUvrSO/+CQ1+aiNfrlKpXzUDqtqSEHGi1mZRjDWv9LWRA45GeTQLmwRWVmyiDrJMbDI+sEzySxyUq+N1hlZR/gk'
        b'X3J6c5UTsYlszWwiO2IT2ZrYRHYm1o/tWju9TfQM1Mwm2m31fJtIalyPQjPnN76A5j8LbyljUtNI/UCdiJR6pFJJTc/AxmpXFF2tbNA0olhkbUjHi/OGugpFvdSg4EUg'
        b'3S+CaCaMYoKdS8Y19BhBozdkXEnYO/L/jLj/PxtxpkM0DXcUAzE6a7/DmDMb00x+BmQowKJGu/g7FsJP+DmGZzDf0bMJPYwxCuobsBNPSdT+esvK/MoGrHUr6qS1E5gN'
        b'i5+zFQAZY5Y3A0yIMeZuDL4VDQ3LMb4YIqEL9NQlJe90Q8Uy1PF0g2ULBBEIMiJTkmJi9Z5UTAjIAsbFLR7bJjAhEkbmmkbPV2mktbVkZCDCaWpQVBpH42KTXQbPtaP1'
        b'zNm8G8h25sWmOxG+09LF2Z+xds3Wu/8fMFZnyFfKq/WrFf+fwfp/wGCNT4qJS0mJiY9PiE+MT0pKjLVosOK/51ux/HFWLM2sJ2nLRsbokp/w8Ln3ZxYFURp8tBI4CHaB'
        b'W3k5BXB7VI7RKDW3RfcLiDmKp79v2SQsBJeY6w7O+1tjU9TEDIV9cI8A9INDGrwKlYMsrP48SW4B0vrHFw1uRY9ZusjObYWtNuAUaAHHNNOx1XBkHuxTFRUU6Q/7wx9Z'
        b'CNtQ+t3o39VMZJXaIlsOlYperxcvAYfAAXDMhgJn4H67Qqd4ZhXrcXAZbFDlojK6pTkFRXn4nMAYLuU5g4OsnpPwlIbGqTZo0KciCuCucGzjSHLAuXAW5R8KT1XzeLZw'
        b'F1PUxWhw1Q5eA7vmWcOdYnB9VSEyWtmUSzwH9IIBeIiYtSudylGTjK13wadVXpmHz5+PBa08bsmqCg3zSa0L6MN4IaRywD7YHSWCO3mUEB7jwLfANh7pr61KNsWVVfOQ'
        b'6isoiLWnmCP0r4FTsNMOdTK8zSqhSgLhOU08gs8XKu1wM6HmbIfXsvNxnTscERpXsBHfCs4gQD7clY3N2SVe1rOV8CQ5Y18IDlbCy4xJmEPlrCpmzO5bdvA2LjYCvBlL'
        b'xZbBNgZ8Ew6AvRCvKgxoiKaikxJq//zPf/6zMx97Od7kIMLKn748mlnKM2OyFSUQSDl4KU96GJ/SZCCgd7Q7bpqdes9HdtQCfCNHdO58RBDZcEdxuAjRRHZOAWrQy+QO'
        b'DmRZgqukAfn19kuz6smGvcXlkcVw5zq4Lz6XQ7HgWQqerQMHiFMjBByCl+xQB+HemWegl7z51qZtMxN0kOaBV8B5uIdLgZb5Nq/AQUTXeH5J6bp6zI0wNxzuK7Y2egwi'
        b'4RYp9hhMc+M7UK+SOzjASdALz6pyxUUF0Zh8CnPA1lmM20AEu3jgzXDwNnFPzKtH5i0aDLuic9PyRXzKDtxmw8ugFewl10mwCgrZ70z9kTXVKHX92aI7UbHMeq8I0L4C'
        b'Xta7iMgyL0xacFt0UcHccKY00QJm3RMcaGZWZR0GpwSwbSXcT74LzyEEz0dKcqIiWBQf7GYjAtoQjeiojVzjAG8vAFfyiDXNroBnlawUe3BBxCENDbbAXnjNJCsdEZ3z'
        b'OqHDyCCpPhML9qFMoCeNcAV4EaLxr68nf/pYPQ/CVkVn3V6OqgnZZT/n7j4xb0oRjHG6crgorODASVGIMDTrHzPe/Ycg60z2tnfaFlhHVEvTm94B0z47+uvP7/X2w8zj'
        b'7/zutZV/OnL0q+41zll3NnGr3C4eDfr9TxfML3j844C0u65NpRc7Hhze6Pd4cYO14u6t+9VemVb/vPb08IzgbY0/9XzqCtYVNAbc7HL6JbeoYL0gqGx28Y6Nmnf/8LOP'
        b'tVvDCmIb39vpWKDtFg5K//nwzsrvP1CfLxr6lUduypdZzcvoX3qn+pTlx3T2fXw5bJ7r8v131Ate//WT4k1XS2R73m77bUZquMJtd0n1ydIffVDXHF89q/4vyZ3qvuaj'
        b'noK/rJk7vXHXQbd90U/e3/6DTeyVC5vfPXNvwXDcj6qb/P4UeO3yaFhR3M0/ZT/9sOzRrrmB+3/1+Z66wz9td7jklrR9at0PnB+FV5cufOuz7b/fUCT/uzbil3+/9PRR'
        b'VeOF84v2ZZ35xR++Pvzz3/95QeUHj+Zfuz/C/mfUPzLf+eTa8I27f8/bdzqx+bTy+BsLc973+fRn/sULleqCfpE9cf7A9rnwbXPvj6M6PYRTJakiC6nAlQiw5VnfD+xA'
        b'vHzM/+ORwFzpcBpulTErzTRi8WQT78+CDMY/dAkgDp9nsu7PEWyFxxZwapHY2Uq8OnAfkkG7IyMkVmAzs1TM5hU2OAHaeWQRWVRudqQEi4koTIK72GB3mRgR09En5KaR'
        b'W/Bt/7z8CD7FBreXLGUlg45K5gDKnSXgLSQLusBgfkEU4qN5LHAJ7Ie7mE+emAM2IbFiWBzGf52NeFsYuCUgHisXcAaJE7yQbNwqsvBQFc9+NTzyBLs5MuENWzxjXAe7'
        b'zZeJMRPGQthKkqHqHctU4SEqDgddSOxsYxrdGbZxwACSHn3k6FY5uL08Lyoctk7OHvNtRUeL3P7Trq2JfV6YHxCFYv16S44vB+xcGTPvmz3MvC5jEcQBNoXNOMDW2lHe'
        b'wT2z+hLwEfbDXqltfMbXNXnYI3zYVdSXeT9qmi5q2p0AXdTMu64zibMr406+LmTOsPfcIeHckUAJ4+xisk0Z9hANu0b0ldwXT9eJp9+J1Ykz77pmkmwz7izVhcwb9i4e'
        b'EhaPTM7BDrEUnVPqSDj2fq3ROYWY+MvCIrFDDr29rnMKfuDq2yXrmXnPNfyBT3ifcNhH0pb5wMOHWQR3PWhQ9pZIF6K/MQPl1OfCjryMPWkjyWltWUM+8XeFCQ/1QZ0w'
        b'4YEv3eN+cPF932idb/QAZ9g3oc12xNW9K0LnGtzv2ld6XzxFJ54yWDksnnEnTifOGhbNfi/griiPfDP/vWZdyCvD3qVDwtKPU9Kvz76T9d6C7xUNTy4ZTpmPq5Wgc0rE'
        b'HrzEdPy9WJ0w7mFAyCmvXq82hxFXj8609rQe7n06VkfH3nWNHQmJH5DqQpLbCkc8vO96SIb8JAPcazYXbQanDrnntnEwWsH3vSN06H/XiBG/wPt+Ep2fpE+l84tvm/3A'
        b'w7sruSdV5yMe9pAMhNz1SP7YL2woPH/Yr2DIs+Chh09XdU81So4KHomM7rLqsbrrGT7i5dtj1cfrdbjrJRkRiRGUd8DhYXjUQMmdCp1fTtvskaj4tsz7wmCdMLinWCcU'
        b'jTh5dNnonAL1LsbQj5xiTbyKroxXETveldfx4wZ+vIUfeM+T8hZl8Cq+oEPxWcLHn3rWvWj0MH6IHhPSeqnRy4iPF15hy2IpiJdRwfqKPF/Wy9jHT6EG7TI4nErDmQP4'
        b'z3gxVDNl7hHspLRWWhstl1wNxdYKyKUj9lqW/oIoHpvaZtxBsoZPvH88E+8f38TPx1vL13v/noFOfLb3eFPDgTE1tpQx97DFhE5v+th9EVVCoL82XCOStdj9eHQmc40U'
        b'PMdxUIGd1is4yGDYO8eBlRIEGGU61LapGOwsgTvnF8yFV+bAK/Ptk2LgwewYivL14IANC8ERDZExLUjp24U0wpLEGLg9AewGV5COb72CBXvgxTQyUWXnALYaymJRvAiW'
        b'7SxwAO6BV4kuA3bDsxmgvRRcZq6DmgL2k3uswG4/a3gMnkCcLJQC+xd4NsMBMrMFroDrLnmSmIS4RDbFX8sKtUOogDfJp+D5xeB0ZK54xjKze5Qq0xS/axpgq5BlQR1Z'
        b'MXVn8Q8LkfbzscYl+QJ/u9PuBdbH/2G77k73z7bnZv2yzfX05z4eeUuap7+e+c60S1vejHhQMCv4hx9+/uHnq+rWlRx1UrXQb58/yvHUzj9rc+Ev0YVpX7Vea131yx2/'
        b'5skmz2+cGRocrXJMa11xmBfwRWjShx98Fh95pXt27k9/s6CSt7e+TaXq/uGq21YL/Xb+dPaxne6/cdj3+brQyr2aNQ0rv+IrYkb+1F16ecXvKj96r/nea1/KfvrNgHf1'
        b'0pqIqau//43LtVOLv9ym+HnY3b/6L/iibMGhv/950PtrqVN46qJjl847L6o8rxCkn94Z7XPXbfOPqv+Ytezx2pNTfdNmJ90fuixaec3lk1+0p3t1fHDx7ZbZhY5N93T9'
        b'1/Y8fTt7g+25t3/xi8RrJZM7S/7w8z9yhA2/SGmWFfxzvsjlCaaQEnB+Dr5QjQU6oq2QoH+DNT+jiYj/wFB4EJxhBLxaikU8m0tkabhjKGwtjzUV8GE+YBsRx3CzL2ec'
        b'cAdnXA2rxAtCGNXmUB24PqYlOa00rMNXwjMkwXR4oiavMApZzrujrZHleppLOYC3OWXwPOgnmgu8vrAEtuaRiwC5SH+67scCb8BLQqKCVJRVRuaJkU7SN3ZvTRTHqgDc'
        b'YO5M2Ax7rIy3bbnDAwX627byXiWr593AIDyZZ9gEcN1Rvw/AHZzj+oCroWTdmxPC/1weKn0QqVxjGzhYlMsyDjgLT/k8Idem7YV7qsa0vS1gq4XZvmtyMkVXAPY44P0c'
        b'hiX78EIaUvAd/Tivwo3lpM6CXB+DspdZR9Q9pOrBAR9SZ9ANb4HTZALPoOBYg/7V8OJMpsXfKiQnf5P7wTgUFxwGLfh+MNgJbjGK6xXYCbeYXSTBRg3VucrXnZQfAI9w'
        b'sFECdxXhW3lAGxtuqWtAptxWkct/o9bkYtCaxl9nNWpVxlxlZbo+j4EQJamXUZIeL7KnPPw7a9trO+rbOFgbqe6Rdi/ri7jnmjjiQx9N605ryxyZFHA0rzuvbdaIt1/7'
        b'zIc+fkdTulMw2P9oTncOAbfNHHH17Eq47xOl84m66xo14uPfE4ATPWbT3i4jQu/HHPT7UOjZWdBe8JiHwo/5lNukroz23PvCMJ0w7LEVhlnrYZ1F7UWPbTDE1pgqVCcM'
        b'fWyHYF8IKDfPLs5RQbdgKCRp2DN5WJjy2B4ndqDcvB474pATDjnjkAsOueKQEIfccMgdhcgnPPCbJ34rbC987IUL98aF2/bIsHo4RRc1ZShkqs5z6rBw2mMfnHgSSqzH'
        b'2Be/+6Hkd4Wp3TN7eOTWs1XDdMrwpNTH/jiSJpHJKJJzStAr6Fs0TCcNT0p+HIAjA1Hk4yAcCsYI4HYJwW+hCL4npyvjcRh+Cze8ifBbhOEtEr9FkeJFXZlHC7oLHosx'
        b'SILrGI1DMTgUi0NxOBSPQwk4lIhDSTiUjEMpOJSKQ2k4lI5Dk3FoCg5NRaEvpqFQG//xDBbl5dPGe+jk1iloF3Qv7Usa9o275xSvB3QVH13Uvainuk/au+x+aLIuNHnY'
        b'N+WeU+pDv5AvKZazpC1rROjVmd+e3+vas+CYz0dC8WMOAj/08O18rf21nkSkXt/3iNF5xAx4DqYOe8wacpploog5MIrYWULazHydapSnUkuV6lEOIuuX07ocDFrXMwrX'
        b'ryjzBa3MgDnH0l8D93d8j4M9ixWFr4GLetlVrUf4Euq8XSrnf3O587e/GefCZY4BUBu25Oqnwmr1HmqlXK1R1pO4OlqKZ1pNHN4vNEtJL5evVqFyGpVyFd5kwXjS9VMD'
        b'KuP0qN6tbml28dmZ01pmPgKjU7FaLbfg+TfTFa0t6IoavMnLKxX2gVa4H+lt2xCz3wMuLURi8SI4Mxdo/WbxKE+wnvMaOOXNqGR9U+B6MGgDO5B6LKEk4CzYxiwougT7'
        b'YS9RJEHrQnEebIH78yQSDiUE2zigH16AWqKDrprOYTTTqtbksmAZRXS2uKI4cBhu0ue2QqLnBAt0xoMNo6wy5rOH181c+qqJIyw6NVmD5Z07eGuFiWJZAa5GsMCBZbNJ'
        b'rhmvgxt6Jxk8AncrWSmTy4lfbe6r4Hwxk4UNe6eDnaxJ4LwPUYdL0sGbsINgznGCb2SwXuPA44oNi+9RqosoeusnO/a1TbFlxzptFGdVh6576482N7cuKm3mLOa1S6Uq'
        b'bvek8ozP35nx+efKHFdtqYxXED9zVcfNBol6C4u948OZa26e/lNF//IRMXWV6xQzVHOr/5Ws0O8tetVm+76+Yz9e+u1PPrrZM+f43U1980+fOvFh049/0fTXilObnH/c'
        b'fMS+7cfRJ5NlkVuXHvniE+4nma+3b1t+W3nZ8d1PPuHPSm09nPvzX1EVfqt+sPLLTYWLR6b/bBpr9+YIhyCxiE80hxI2x3wFEOUC3lpNFgBxOERlA5ts4OZc0I50i7FL'
        b'QTJSiJ4HemFPQqSkgE2xy5tAHysPbhIwatIAvAg3Iy0NKxw5YjZlJ4edc9iwZ7KCWfrfq3h9bE1/rdjcQYM6iigea+HtBKOuBc7XG3QtpGP1iaxfWA+wNuoBRukvVZXh'
        b'gWrCzPQQIv3/SDHSf54jYelIFoeIThX2Ft4PTtEFpwwHp31JcZwzWO35bTO7PEb8A442dTcNhSYNcgaLh/0z2rJH/KP6Vun8k1EoNOJUbW/tQPyg1XDo9LZZXeF7ih5b'
        b'4cyPBajQ+8EJuuCE+8FpuuC04eDJX1JWzjMNxXr7dkm7Q5FC4el9lN/NH/KPHnAdqPzIM23E07/HSucZft8zVucZOxB+zzMdg3jdDvc9o3We0QP8jzyTH1txafe2bKQg'
        b'hMX3yBgcdKEzBsPQQ4+GI/4YUgA8fdsE/9L+hi/NxYG+BX9tur9hluNLXoFyHGXsZ41yG6XqGrMbs4wmLd6os4+nvzELH3SBr2DGlw3yjbdmGe3kf/vWLCQTPuWwLKyr'
        b'GRMLmEOrpE04VFtrKiBe/LQGXNk0OqeKjsChCBqJVRUzg4tZv3wVPvUGT2hGSJoVjRFR5EN6GaS0PB+qwieFy4yzsFJlZY2iSS6hi/Ck8UqFSm6UM6QMUgGSXEpXNdQi'
        b'of4dQmP8DdTWzF124AoNLgtjIrMRN5mTDXeIcgvyQX9JNjgHtVESZBtkw61WjbBzvgZfR9Ow2hYOavIQ78ktkMBt0eB0CdTiG7qRISIOx2c+5sGrVmA/fAtcIGw9sAEe'
        b'QhbbGeyOVoMrFKeWBTbCt+aRKTMlOygSIbaKQsxq/Sp4OYCZmNuu8Y8sYlMsuP2VeRQ8AHalKOp+8T2e6ncost3nq51zL9qCGKdbefOWiwNvuAfO2572F57DP9Z/9nnU'
        b'Z/tFx9xOt0X90qXRbdob0x71/sA2dlncr1c9/eMnn/zwxArez0oe+n9/zY9C3aa+UXejdVKErne2oOb7ZVe2luz72yc7b2mW99+7cObIhQDeRw6/m//uT3L+8V/Xy8t9'
        b'ktpB1kfDdpu8S5LPprQU8Aeq3pFtXV4y5eiZ7t+6vfaO9e+WUF98Ky3YPPOzljj/M1Mib5TsW1dJ/+3jqgUNM+vf2ZDKP3qj5rdX97a3nizf7L7s118lXji15+lff6tb'
        b'0mZV2TV9Q8jMRc5Znyl/snBOhfIGK42Vejl5usiRsPK6ZifSMXgmagPFTWaB88ik28LYcJetQSe2WskVT92+5PrUVvaaJnCGCApwfmkEvAzfXKlfSgq6gNYGnGKDY7Cn'
        b'iJQet3gtyb8NWf38QnYTODQJ2bfHCSefJgDXUcHboiQ5JB4eKLKDA2x4MwQeZD6/G3SG50WBXUXM9XLgVo3ddDbsYsOTpPBosAlTBp5fw1ve17JBq11ESjJzD+1VJ7gR'
        b'y3ORBO7G1aMcYzjw6pxquCucZIYXXctMxVcxvvJqYx6xTWvs4NXIaDzJLpaI2Ei+HOUsFSNr+42lJOtquI3Gpvq26EIexZ/MdoD9HjbgGuNH2OvgkccQts1qRNo2Qjbo'
        b'XQAHyEQHeBPctsJTGfoGmcEGnWme9XA3Y3HvLQGXjSY1uOqpv3H79kKm5ONwZzGDFfoq6GMvgUcQ+oMiu3/VFrajzGYQGDHIxcO+2d7IwfErEYB4syoWgLlOlNC9M7k9'
        b'uXNq+9Se4HuuYR97BwwFGvafu7qRuCntU3qE91xD++IupPWnDcjuRaabJfOchI3Rgw5tPL0PvGPyfddwnWt4n/s915gH3gE9wX2cviXD3mnITg6NxBd9HatDRpFbbLdt'
        b'F7dLNuLpgwvoKelL+MgzBplFbrEPhR6dOe05+/Ie+vgeTe5Oxjv3+oLv+USPIGlp3W3dIzzkYFIU2y2SKeqBb0BP4Kmw3rBTUb1RfeqBkuHAtMHMYd+MxxTLK/LOvJFJ'
        b'fkezu7N7Sg4VPuUgCAF/wUH5n7INr9+SvcfvpLjMcuN93403y8+GEZw2jOB8MoH0fLZHsFPZaGExAtWKhS/JM+uOfxqMK+zFfg1JU0+8SPal70Tdzw+lTtrFckTMAU6j'
        b'nFnz5xWSS6qUCoy7daH+T8Rjftjon+sz5wLj3ZSyhsqyMrKJf9S6UdnQKFeqV7/IMQF4LyRZEky89sSSJPoDqbNI+D8yi4Y11mcn0MYaH1/T12w8GgsjqKpjkSPbvuCy'
        b'7Z2+tKYc3Ho5/ao76bpXljzwC+hLHZrx6hMOy6Gc9XBW1sjced9wguxDv+JhwGMuCn6Ry6K8Ax84iUeESU94bO8Ube4XfMor4IFT1IgwEUG8krU5COIX+sApdkQ4DUH8'
        b'MljaQnw/Hf3AKXJEGI1AnrHa7DFIKoakE4iH/wOnCAbika6djSA+QQ+cJExBPqigvK+tWfYzWV/yEeLdxb2qi/Hfc30//oEv3e96Peh78e/LMPIlrIdz548sWvKUI7af'
        b'wcLYlyDscfjLV1m4xkEXi78X8r7VHf8HPn7d6q6IixxUSrFuwSs6qRwXUI3viyzDS7g5RSz7uC8p/MTloAguDj+tYCfaZ7G+ovDz63qWl73vl0kYpaB79n5P2e72kV9x'
        b'KAf/L3CIOeeOeOuPwX6wHl9SKK5QqRwcOJS9LzLJopcyi35OL4VH7ECfGgsru5wCuAu08ebg1SiT4rhBPuDg/+37qa0KyaqdaVNz8E168ADcE0AFIEkwSHQcCWyDJ/Mk'
        b'YCAmEewBLagAeJW1wpHFLOM4ANthW2RuJOgQm81jZIA3SO6lKxWwNSfKfxG2meK5lDVoZecGgnMK10/72Co8+MsCTzI3XMe2trM4Z7feXbpDtOOVH3V9OX3p2UHNuarN'
        b'j/inK98t6QR7wc0DNjn2YS5/cU+Myj4ZI7zYFHcyRh2XveEjq/jGq0ifeN1ZtCROxKwHANsRZteZU2Vgixxp7PhUmXk1jHhfn2Vj4kFGsu4svIbk3TX4JhGznrBLql9N'
        b'AAe9mQUF4gXF5KybmRGOWLgnp425jxtkUxjBfioCDublFOTE6OOWsuWwfd2E28EFjUo5UrnlZXixaLPZG5F7CyhG7k13poSejKTSZj50de9MaU/pyjya2517MH+YnGuO'
        b'BFl6e3rXyj6bYde4sfdVw67h2swHjm4jHj5ds7sWtK1p46I4bZ6pgTXKxR8c5TPnXnzHPdmuWCaYYRrANrkhe50Ti+X9sndMmpGnk/73q5/jMyLtTM6IjMYbu8kYscGn'
        b'Rcq5MvZmSsY5yzWes8gjUB6C8k2gfAK1QlBrE6gVgdogqK0J1JpAmdMiuWYnQHL1p0WOQW0RPlYIH8fN1qV2shgtq4olc0K4CfRwZ3zaoyyWwF0R3AGHtXytjda2iisT'
        b'IoijLA5BuCitGz5JUX9qIz6pkVPFQU8u+scz/JO5kDMcbfVhzjNhQ7zhl2tI/8zvs3DyLnM/5KigZB44fwdL5onj0a+X6TfQu7chHwr7mIQnmYR9ZX7o6W8CoU3CASbh'
        b'QJNwkEk42CQcYhIONQmHmYTDx8LP1lcmOsQ+wZJFHGLjsynlLnJnWSRm58vCqHF/Bv5pOLdSnz7qRdOTrwj1hzYyBxDYVlnJxIgK3MjJmlak53kyCYK4r3ZBnDl+1KYM'
        b'SXhpFjJ8zebxjd4FrMVgP7PJPD4+F5KLCscXxfONs/dW/7HZ+3HHbHCoZwWGLTN7vyQQsThqOsWZXi74g1UCs56T47WD8mRlLxbMKZf8adYyBqhd+zrrz+yHCx1ipOmD'
        b'1XmUBg97cBj2N5od+2Z2ipYK2dm7YasVVVxt7RQxiZTzVBRIZVIxUxFLYke6T6J+Z8CR8DNF2/4WrgovfRjt2nfwgyQkUy52VH8/5AiL3+WZ1p3+ysL4Gaume2UJvfhd'
        b'+R4zw2baVia5cmbGerR9f+8fwJ05wZQstvog55WPQ87GrBFFxUwp2HGYdu2Wxh3OFwlEZ+fRse6Dy5x2u215l/+7i6zVnzf6vZb23m8mxawN4VSnUV0y7xL7KJEN46Xs'
        b'gm+A/eTybZ51jphDWZew1c0NjCm2yR4cAK3gQj7o4OE5aX4Y2xn2gh1ENGVWzgfXYgxr5UxWyuVFkC2Xc+BF0bMHjuF9li64qUK8eDXwRAGZv/ZH0FugG55jjk+LDBcz'
        b'aVEyj0ncyZHgFFl5V7JSw9wRDnaSOe4deMHZQXYqB/TWgA0kyWuwP2ssTQE4S6Ek+zJe5YBjK+A+grXCE/SD1mhkl8JreFcsC1nreNK1Flx+Qvww2ysxIitRGURJmq9C'
        b'ZYHdRUgEbyuCuyR8KjWPD/avrBbxv0NrxkNj3LFoLsZhZH4u2mqKEaBLnCn/4DbuXju83Ep48BUUtP3ClqKDeiYP+8e0CUZc/XsC7roG9QkGlHfDUwdr36u8O3UuWWOV'
        b'Puw9eUg4eSQkFp9RFjgSGNk3s29ejwSfnDYSEEIOLNP/+NH4EyMBwT28Nu4+exMZy9hiozyy6n+UizeNjQrGFgfVN4zaKOobNWpy9rclVydjnemnwJ5f8Wi2yfzXYmcW'
        b'KwWbaCkva6J180VUv13Cv3Zu2WbmmCJeGa7pROcTmeBuOKAog216oFJpd+l6/fFEk8ZOrx53IJFEqaWeuXz9JQ/Qsi8z7YuXwDeTbXb0F17DZ8DYzwTj8SeVSf6dZrUt'
        b'MxLLS+A6G+GqxGfnMPj55hjKMOyj+rfRM571hcm8rE4x4UlaFrDLxdiNHfbljg1fukrZUPcfR0u66iXQKjBHS0jQwnv2/l2k9JTHL1M3qKW1L4HRHLMhsrh7sYHgvEpw'
        b'SYbNgBMi+D85hT3O9hyvSvAYVeKjyXi6tcuDTZVHKVUNjNZQxrOiBFRKLY8uj/qv5Y2U4ncDbLYqBsVINmYYbEaWrZvr8Zhc9vsVP8jNCt1aOGnZgvgZH8XNZ71fzv9Q'
        b'QE3+i9WryX4i1pNIlA0eBW3wKhZDoI3SSyKLcsi/biKbjTlFy9mU7Y6d34UlHRY3MhfKc1LnmvY1PXPveoSN+EzCi2MTjk7pxquS+zJ0HuIhJ/G/fobX+K8Xs00muSpd'
        b'/oVJrv9FD8ULnOump5LuaTxiH05PyncbWOe+hKwMYf/kUuXJD0mxrAu3FOE7gjiERmZG/8pII67quGz2+1FV+d3CHwhPfpQ/Z/7DrpQno9T7ufwP3SlVpJVi+Q9F7Cd4'
        b'DigQHnqNUVRgG9w4MYmg13bGd34c3E7CUwERYgn2FGwE++ex40E/7JzQ7ncsI3suFc3ysorahsrlzV4mPWoeRegqQk9XjS5UeBRejz4wXxeWfj8sQxeWcSfozsrhsKI2'
        b'bqd9u32X/K5T8DjCGuWRHYXfYdnPwJb9xIgsMjXz6xCJeb20mf8sG8KK8lfYz8lYOJ3M9QNUFed/gsjGTxnqj9Pe5f2U9TmHCh+Y5jf1G2u2fjvd5gJ4uxZcA2dQ8maq'
        b'GV5/nSzdgNet4aZ54ATAXoHXkKZ8DF4i5+vAneAAPEWsm5mm2/xKwgvFLCoBbOM7xK8gu+JsVvCY1c78N1b8cUozRXZ5lToWsd9RLrZhdnndbnhAadJwqYdS4ZuGE64j'
        b'4c6a5LHtXnryXGB6uHUv7LaFB+AWuIFxZZK1EEf4C7BLzuCQy4EHsE8OXAZbFNe/YnHI+pG+N0oOfjAZDR6d7q9bAprCODPFM+1nxlY6+rjODCu2h8uy+DHZ0h81ScvD'
        b'3c9I39u4nd4kDO26UbHBe6vwt7Uq/tbAP7pUDU62y397m7OsPkzlbudevChkQ3B+yOm/z29MFqbOyF//1g7xYk6tT/rHk5o2100/mBJbV2p/wstr4K3gVp/W36eUn/zl'
        b'3X2g9Hsl3+N+yYnZu+rieyqwhrO3oKqw6hLr0mtNl2NK4hqrKOpdeVjFkV+LrJi1oZfgVa5x7g1cz9VPv1XD23OILQP2ScANE+vKH2wxGFjg9GvkNOk5jeUmlorJ4LcH'
        b'G8fGf3MmWTnyOjLcjttF6C0xo8XmL1kCLnPhhdTFT/DgBTdVi8vhTbKcGNtgiBzA2Vyw08BU+FQMOM2fBLpcGd/lG68uGFv+agfa8BYfHjjO+C5vgjfhGybrV63gJuyD'
        b'hMesRFyLJhOmcOOJx0jlWKlUqOXNTiZDnUAIq7miZzVNLpRvwJeUrfO0tswHPv4jnjSRYR2re+L3rOtTX1jTv2aw+F50xh3Ze5Vg+cd+4UOi9GG/yUOek42yrs9F5xM1'
        b'7CG+yBnIvGyj80gdnHnXY9oDH78u9cHUPt5dH/HHgZKh6MLhwKKhSUUjnpPue0bpPKPueUrwFJ19tz3z3ld8zzN2hFmL2hM4LAzpE17w6fcZWDQsmqoTTr0nDPnCDaFp'
        b'wvX4DNfjSpXVKotClW/gfIY7IzHrG9ceS0w43jcal39hmquDH0Qds5NwCiu5lsQbWTrCMjh3iGsHs0B2FZcwQK7Z0hEeYYBcEwbIM2F13LU8PQN8Bmp6zUfhd5xipp8H'
        b'8AfHG0EHB5xfjMKU/wKwhxy8r3HElNnqpYxkCUrQK6WxmUF4YzW4IUd8EXZkEtYINsBuxWtBVjxy8+aRZT89+EGcwbt/PKYpbmXc2aqtj290pXe3ekV2z0O/VRyXK/Kq'
        b'+JMDP5LbVD3M51Dx123vrxlGShseYYFwz1K+CLRG4/3WAI0WsqybRfnUcIEWdoAbz6H69SZUT3bzm/UygRCqj9FT/RxXysv3vme4zjO8z33AbZA/7DmtjffAY9KIj+9j'
        b'DuXp+2lQ6GnekIdkyEliQnBWY8tdlXizvNKNNU6dU1lRjAlvFLjFz1IdwUdhoLq/4dOIXFms0JeRs9aoTDNiM4o54knkmhCbFSI37EW0ISRn9d9Aci8w9cT7/5p7D7g2'
        b'jvR/eFUQiF6EkamiI3pvxphuQBSbYscVCxAgmxYEGPdGbNzBFdwQBtvCFVyJ45aZ5OLkchdkOaEkufjSk0vBLc7lkst/ZlYCgcGx7+73fl5fbtHO7s4+M/PszPM88zzf'
        b'J4PmLVzqshK0g92oAXYUmmiv2MFXHKQ/nODoyHDq1++8pAffiUZ8dGZd966mzW0Wt78tnPOXNyjOm7YxZoHn92Vcfn+b6Worm8b32Dmv62Ur3/zg7ciD3bvLQgv0VfO/'
        b'RKpAMDXT0firG42aEXuODVpdaniDlmYiA7LhoeYkS62RGykm7BSuZqf5FhRvcuNUxDwDVo5yV4XFXSufAVsHuc7B1MbEAb6LPFeRpOIHIQ5z9Tjp2mvl32vqr8VW+s/B'
        b'VmNp1h/hsmET2SzMaOOTW6ExFmFum4e57QH1giznMZblhieWUkrbeE3mN131DKfz/wW7PS3iadgNL7JJcGtpts8suDcomUXp6DLgJrARrM+TSU+U2jFkWNo68PO5g+9E'
        b'Ip47hngu4JXO3a/WNzH0m/mRk6fMmRX/z8OGuacNDf0XWmdb2rDi/bENOGMed//7iUWWaOoi0mFjHugQpYGGKhx5vIARNhseRDL5hAyno2E4dRxtnjrDkJrj+FpDOOoK'
        b'YTpvNdOVDjNdv5WDPOg0qzOxy/VUWk+o0jtW5RHX6xSvtIrvNY3XYjS9MYw2yCkSF1RXVI27eOppcRjNXzi2cWLilmqz2BLMYkMvyGLklfs57tQJg0CW0IQO6CShnSTI'
        b'E4d7DhqNWPCWSJYNGtVW1BSUSKoIBQGjTwMHDQowFq6kvFpSFaB9EjioVyiV0SC2OFZ0UKdWXI1Tf0lqqsV1JAUVdiYZNJTUFZSIcYIkXHSM3In94wMG9TUgtNJCLTS7'
        b'4+SOaml1qQT1NfZwqcJrf9USfMB74GNSkmUM6uGExLjKQQP8SwMZR4oJkjZ5X2BVPgP7wWAEovyKOoKaN6hTWVJRLhlkFYnrBnUkZWJpqZA5yJaiJwdZ+dICdKIbGx+f'
        b'mZuRM8iOz8xKrKrCswo2PY1S0HCfY3HzYTmlCSXdT5F9LezgihcNqkG/SO//QFV7SlKxeeo7LqBVtWDxyuxM5pAO5S+2sbdeSJGgSxMROCiDl03gMdhepUMx4XGGZxxc'
        b'R+s+N0ALJauuhUeM8B2XDBiULjzANPYAJwkUjS1UgE4vjEBwxiM53TclfSZsyJgyG5zxhjv9Umcme6f6we3pSNjXoI3A3fMM472ziNzk6pcFd8/Eb7k6azmVHgj30iqi'
        b'ohxsCJrKCPZnUwx3CuyG7QxyP9ibOjcIfRxBFLwKdgXB+mji2Q9uloYEzYdng/2ZFMODAnvAcXCMYI6CJngZXsIxeM3gOL39w6AM5jLh2XJwmY4/2LcMbgqCp+2C/TkU'
        b'Q4hesVxMwD3AET+sjeIgwxA2Bc/xdWA3A+42BttIRyYu9XRpZyJeNV3EjE1fTnck7EFdeDoInCwM9mdQDE9UO9gCrhNSom3zRb4+vkiN6QAX4M50H7gljUFZgQ52jO1U'
        b'UmWqlWPVn1hrcVaqlesXMNVBvF2JcH0Q2AsPBfuzKIY3BZr1Y4gjScEM8IoXxnlNobUaE7CdtQa25cNToJ7U92q11aKXmS/hlE9Rbskl6voaK8HeoIXgYrC/LsXwwZGD'
        b'62LIlQVZuUg/8p65BHvtsr0Z4Gqauq2Vs6LtP2T8TFH+iwInSdWEZYMdFkEG8HQw6EL86Esh5f1kDI1t0gx6HL2WmvsKU9OR5s4NYCKaF5OavioQZYSy0PpnuijVyqCE'
        b'zhLvBk6AK0GgRR9VhQbcjwIHKbiL7tAGv6V0YANW2yI5YCPTGV6xIXVZTNLJv8pCE2zMotJqt1UUzTrXwNXgIA+f4FCKdNZeCraS3nKC51xEqTjAEu6gA0eNQT0LHvaN'
        b'NptOqgtxj/D+gXUPz9RZazKm0AJWkDMnCGyggkOZpIn7wXo2cV9a7FFKV5YBXoHbNDuLDMoa7GGDLfByEWlYFDgCGoPgAbgxOJRDGtYMD5sQ76gqsIujroEePeNKlm1C'
        b'uOFsQsuueRalN5jYY2/RfD3BDLrDgQLshEeDypMDMad6Y966MZX+Rq+AY/5qVmVSQO6iA88z4B7YCtbSnbIFrs0IitQPQUI7IxA9CA/l0dHWr4H9k7xEOG4EjdMcjpQ5'
        b'GW5CXc8jo3IDyoOWe4bhh8LxoG5k0qg3J4tNMd8lggbEelvAOYoyjGKZQsUymswOlmFQFLwahj/GSMwW2+FZIj7ku4YjBvOLYZDZ4CSbMjRlWcJma9JkwTK9hXqUAHe/'
        b'90pDHt3908BatyATeDgMSfe4rhZzU1ITeKXCB5GAIYhEOlQEOM4pYNqA08to9tsCNrwcBG46hQUjbpqCKWiDpwltS1aD8yJ4CBwT4R1ZZgUjxgPepKneAs4uDQL7zMKC'
        b'EdlRFAbVKSXvmqMXI8Iz2Da8RQuPr+JYMLmgBzQSqnP8lidsZn2N+bn2s1JTmmqf0CXgwixP/2AdihFHgdYqsIUME2K9bpxtLS0VbAIn8bYxC95ggIMe8AJt0V813e0j'
        b'is9A36vn2wulNEOvwiguF1zhJf9g9PnHo9FNyyDNhGeBok4EzoGNaCJBstJChh/Yt4ZUZD6HX+XNWoT7MuqeUTYtvIGj6J1nRCne8Cg4ihiOzWaAVnCYRSC2Zaw8ddwX'
        b'BQ/5ZmSS8LE1fmiWxTHgWclwc6bPLNqxHzake6MZh6Kmm4MrIbo2JSm0W1uDMTwrKoMdGhAqvJ/dzAR7wSuykSx0Q6Wsud8yiTxUOq/amaJn9Q18eBDu5lCUN2UDTnoH'
        b'FxH4JzfQYSAas2mfAc5UgEY25QpO6tTAZn3SE7mpBnDrTIxQwKZKwHa2OWPBVPTVEzfsG+GgUwSPwy05cDviBtiCJtRo8Cr5iMHOOLh2LIpaBrjKoFwzdaRgcwHdz9fc'
        b'4GF40AAvhRS8KUALYhO8SLDGrNNAuxfqk3S4I9knldayA8RGbMotRycQvppHmrzX2brkLlWCF4qoxeWW9Kjq16Fv+aAuXrqol5ngJuLRzhraBeF6zFNVRoMWJuWWqxME'
        b'dwEFYVfZbHBNBF4FiploRSU4XdczOITc+YjHNmSnz/StxrBnzBUMW3gM7CWXijKzRcGwK5fuiWMUvAg3gGu0O2Z7NUtUBnaNBqtjUA5gKxteBuvpCLpiuAd0wYNG2DpH'
        b'weYCcA1cWEBg3OEVX/Aq/rh9U8Cp6gz0bIpPIBuN5gF2aR68QK+0RzPQQBxkoV/XqURncD0UHqIh286CHfAY/TTcPUX9NBM9fZBd9jJoouewfeAMPAO3op9SqlZfioah'
        b'k3xVljmwHcefDNNsYsGCm9MXw5tFNLKaHK7jAAys5kD5gUsOsuWE4ohyphcNki6F1xFv+dHYdLbgEhtuoWLpdx7W14UHdfA8ib58eA68tjiCvtCGem4D3IpEkSUUPA33'
        b'LaktIXOjWMIW+fikgNMeqdjx3yIGroUNLLgnZRHpQF80p66HBw1xcAHiTXAKXHRMpKfwRiQUtI1Cc5rFymeXwg4+eXIqaHtJZgmvGhnhOJgdFDxTAq8S/roTaxD9PeWB'
        b'+Sttq4xDT0FTwsAuuBW1uQJP/jcqwK5AMs5mfhiR7Ci8Cc4kY8i6baJMH0KpwIYNu1bAk8SUHidzZfSihwVL/1o6UHdu5jtqi/4pcDxSbc53Al3LV8MNUte5bzFleMvl'
        b'MvfXvfvmVFjEGr5V7JZ+IL1k8HhbY29WKmvPv47HiERtHz1ZZeGSFDd4zWdZcvtfRG/++YZgoamDU555xcDLR7d9PMfJ1XnZr78PHDl86eGU41G/T0844vfdzn1/SXQc'
        b'DJyRVfL+vk8+C1FZntl2v+HB6g8+ePyup4Xfe+8NLGxTgIoTgoTZGwOby5bxlyYU/+bU1rix/+3H38wLrP/u07Q1nYsM8rcPpHbtsHj8xaOSzO+/bprt9E7Ssu9zdb99'
        b'uUT/Xt623x6fXVg0/b2A8JspYGFg06OeDf6vm7o1zag1Pc6P0+G+Zlcv3dily11hV+8Zr3AUt27wh6ZFTV2fxDYX6OlmtX4eFR/eUK+j2/ZXU2PH12vajYPqnTsr7jrF'
        b'hx/4xXZHQP1nyeF/Fxwq1DuR1QqlGyvdQv7uHR++qf6hMdDZWGnG3W9b77qxcjJ3tmHb7H9eSe0Wyou/kOsu2L5iRo7/x56KDVNZnyi/33H5+qm/Sz+on5b4xkv2P9RO'
        b'Szw9d3PL5sFz/ZGKwsHLofsFq7tzE39Jvbliw9Eir/WBs2J+CHM8Je99Il3Up/v7ZN2d/RXlhvdTi3QzStnf9XHcY2YrZUnnsmQGK78qXaJ4NHd+YmDe/t3/XD41Jzzv'
        b'6xM3y89TEi4vbNfkS9HN4ihHi09P3mipKzVcEVP0MKF+XtrnH9b9+IPhR/O3VO53/OgC95fov53Qibu/yD/vN//Oz2e+k2oftCzKcUVgYt07pkea2J9G/OMrw7/r3F+z'
        b'/p17ru1rEjNKtgz9cvM4MxfabBwKlRj9yP9txW+vezyePt24lf+n4tNH1y399s9XuO96z3Gt/PDOuQ/rZ9TcW/Dvk9aSggHe33beNJn5eHX6VKEFnZVyixcBvx/r17UV'
        b'XIYbaceuJNj+CHNukQWs9wItUXgjiQkOMNIrzYnPmdk89DkiGe5MFbzpzaHYCQxwHexZSbKBggtgN1ozt5pUGlbpgwZ4EWw3qTXicigeaGVVLA4lMVVp1vC8Aej0Ttbs'
        b'YpjBq2LQxQJncsFNsjHhuBh9bsRvOi5W4zndnQfaaLS0k/DAJLC1Gm7zU4cK6cF2Jti6IJ6Owd0LutEcuxW9+8iwEVcvnVnoHfYIT21laO0/K/KcnImbVcuITa+lEdoa'
        b'haB1GNkNXk0lvtigy5BgvoDWOUgDQct6Vp0GvW2+D7miVxFAfOywg52zM3axS4WXSTNtFoEt9A5QmcUoDzu4G+4hvYUW8PWJ43jFwR1hLNCmb0mqCS0petopDmxfzALt'
        b'8eE0ZMolsM4Se99hWEasIeFwMtxwuMsBtd0rQgdcDoKbiLdeKdyeq7Fxt4EDY+3cdmAPjZN3Cs127cNByOoIZNQ58gq4NYIMA18kQO9s4WBnPC1PPAF49b8O1xqNWcIS'
        b'FxYuNxox+6BTYoi6wVaHK1tS9k5qYLMgpV3oHbvYHnTIuDWnUf8jnlUzp9WgxeCgkYrnpuD1CSOUwogeT6UwUclLbGQMWPA+snbudUm6zXtv8tuTe7Nz/myrdMlVWc/q'
        b'5c3qt7CTT1JZuONNIVGTCO8WoZrkiYogFd9v+KwzSFHbJVX6xai8YlX8uJG7QrvcO6f1xKn407TKSKhYqcor/laWip889sJiVMetQBU/aeyFIpXX1J6q0dWTCyUqr2m3'
        b'zFX8hLEXilVe0bcY6Il7z/uOMpVXwq18FT9lXKoCVPzEcd/BVPHjn/uCVOUVc8tpnKrIBceJ2jFeVRKVV1QPIjd2wifGtnzCThyu6rGPjeWk+5EU30nuppjU5tvlfNcq'
        b'dEDo0ynrCurh9NS+anxLdpvZGy7qC5+pDJ/Zm5WrCp+l8pvdK3ypmdNc22Lcb2XXXNS0us/KU2nlqSg8t7hz8R2rcLJtGa2yn9aLeMHGoTX6QLRiVldS58Kewpvlr5bf'
        b'8UnrF/p1cTrtm9mHjP/whgE7J3mowkPpHIRR/JLU3ClnntBt072Hdze9lHwvRVLXzM7UO97RPUF3vBNvOd+qVfEz+vn2rfot+vJpKn7QHf7CHt3XnW8V3c5TJi1QxS1U'
        b'hi+8wy/szS/s59u1seRJimlKlykqQZSSH0VqVW9WTbpi3W3dk6kKSLuNemxm/7Mu2ck58to24z5BmFIQ1sNRCaYp8cdAVx+Ng/8FU5Q4jH9sHemqgNTbsYTiCS+NNDVe'
        b'fSlVFTCd/qjGewZ9iJlPN2S6KmCY6cdUJ1IFJGsujHom9baOKiCjd8ZMFT/r6ccyVAGi27NV/Nx+vs2Q0FI46SFl6Wj1iLK05GNsnsn7RbtE8lAlT7hPOzrGgDaNYzn5'
        b'xUBr8JT5FGLNZhJROWrKPKkxj+OIypmWDIY1BgR8kRgaYh5v5nhQCoOg0e66wzsxRRQNUkD2YLANl2rQVe/BMEbZbv9bj7+nbLcCaqzt1p223SIdTQ2wIlnAXDmfGtkH'
        b'hJdyxJPR2olVeHvKHi1m20g8fY4HOMBaArA35mRqsjPYRmtEp6KKwcGyIFRXIBUINoEjpPq0uXrYVczfv3Z72kdBQoq42qwN49KFnAfcH90YtBa/eA6OTaBe6rKrCb1Y'
        b'kanW4us9FwQFozoL0sBeqgBuzCCKizAJtAUFI90erflHwX5KAg7Dw6SWW07YV5Ey9S+qdr4onEdXbVBnijsg3D80viTU1J0m4i03daHbTMnv1ln0nV+sMqKQgOXhP8ty'
        b'eWv5LPrOT6eoC2sXu+RVhtB3XnjJgELcqOc/qY/h68+j7/Scri5M2ijKeVld2MVSk+QWncb0YdKGE1s9AdKnkbAxazo4w6Z0ahngKjgEaUUcS5szg/zhKSdsq3bBScXk'
        b'qbRpaKYzlYBHi7Fu6SIqjiIDUpMI9kH5VI1P1CJf2mBkwgVX9eFBfRwJj/4DW52ImrliNdg7H8jhQdx9V7CZbx+fhlVsBFdTisEmiPd+fSgfsJm2NQh4aseoUM7y+QXT'
        b'KdoGfhg0IRV3N9yL/6cDT8B9SIXcSIFLq2ErGTp3cAhcLJaod5LtQoDa9H8UtmDweNrxKbJQE4sohucJeTPBUb1sH3BgAVZXGbCJYa5bTFrJga9Uzy2gkRzqwBV4jDax'
        b'bYbNobALiZj4S1hGLQP7wTW6Oe1wAzw3a/WwS9hWTzKfkDHZXqxuU20zIyrMnMa2uma91vh8AfmYGBtCpOm/l7BleFMmOSjj0t7YDBDD2/hJmnC9gMlkJibcVSjfOGaz'
        b'YBn73NDRlNdO2QQvp4y7Di2KSvD75mLL5CW/mEwu+O5o+t9+f6/vyc2Wiw5/d0+Z++caH4uc+d67ZEdzrinmpr3vZXwyZJL3Z6Z3WWdfVoTX3JKunWvg/+3lCz7HhcK5'
        b'Nj3WbxspUzuyTMNmfxqxpvxU4brPvre7VSLJOjVV8W207Rs3io9c/suF9oeCwVu7P+i++PGh4+ab6uL+pCtcIPpmr0d7XtZ39T0/dmc33bb77KTzjlsnp8IPVnhd//rC'
        b'mqNfHVl3vzxcIrv1dXmUpNZd/+S9vyc9Gdr02iQ/+VtbbznvfPdfkQ+b4498nb2+yu9UyL/sP/1mz7+vHnA+cv9r4fmv7vOqVy/KCVr3adohxgn/jP3O7bt+OJS1/Nxd'
        b'A/lfc387P3f2+153052+f8Pk8RtW/Ut2Xf/gZnHOo4ar4Q8y3xY9mvrWGnb8qqVfe/8w/53ueS2KFSuN9uy+s5R/9lruk7Dl8i8/s3r86qq/8dKEfOInXAja4Dphxfhe'
        b'YFouoB1qiEfQJQO7ia9fhs9SqPDEMvclJrrhFDhO9KYCcJkzHG8Kb7xEK07WM4mmEp/MoRUJS3hcHSm0JIRI+9mUE1Yf0tPhZtC6xhun6MOwjLEscDYQXKW9T7eBnaAd'
        b'w/ZjvMXNS50YGI3CaTFseITdEMEpvvV4WmUN7FRHC3XDbYRET7AZtGA6vFhCeIViwbMMIC8H7bQSdjEb7lP7uII9YCvxc2UGWVYQkElYj9TLbvwaGmeS7AVNMgJHXmLb'
        b'gD00yCT6YuthG3aA2wE3p2UtJMTgxrhijMlNYC15jwQeQ3MQrbbBdaCDjo0So17E60h+OnZVxD3Fgk2jFDOklRUBOemQ2RHUCEbTxRINRlM13E1oRePUNoeuZL6TtuaG'
        b'1Dawg6KHs13fBeliyd6+ulW+eOMPkQk7WXA3uFFGCFka4jVOUBW8BnfYsqPQMNF+ehtAK9J18X07RDrwBnyVYjMZ4IgXqCdttQVHDNVefFAxWRNJDJuX0a7qVwvQWjaB'
        b'v+BZ8bDLILzoS4bPzTAOkYz1bk/YOqx6r5hMFNEquBbc0CiioEegrYtqFFF41Yf0XwI4i3qehHKluC0c0R+XRtDBa62wB7Z5eeK4aiiXaFDYs+OfK3BLC11ikI0jFJYb'
        b'jwhD+JwokHosGhJ8rhXFs2qs3h0hZ+yK7rexu2fKw07OfaYuSlMX+UwF85xup24/z5r8Z6WWt/t4QiTD9fH8lDy/LoaKF9gV2BXUywtDl2lUSoWzkudzhxfa5XKHF93j'
        b'MsATyHknbNps+hwDlI4BXQEqXkgfb4qSN6UnVsWLHq7VU8nz7OP5K3n+XWYqXlBXXFc8BhN59ksHkJrL7uN7KvmeKp5XHy9AyQvoclTxgruyurJ7eRHkOhb9d2fSVSjQ'
        b'RW9FlgJdDBhLcXaXyxXfbt++wBRlYMptD1Vg9h3enN7Zc/7T+8K6XO/wpvYEavVAqNIxtAfRH9nHi1HyYm6hlsbjy7aKKtSoPl64khfeY67iRdHPOLQ5dDmN9FecijeN'
        b'HohR7wnvcrvDi+tJIpes6CYjLY8W3lWozU6KgF6ezx9cGx7noTDbAPOHlK3Q4kk4xbNuCm32UFk4P4qwNXMdiqTMLDXscdfUHTEMfXbX1K3fwqrPwlVp4aqwuGPhfU+t'
        b'nOko2H0eU5QeUzSqp7jF5A7fTxF/hx+KVEv2TYNXDR6yGMJEnAzQMZHxiGJYJmGICTPL/QZNBs3xd00F/dpvsbLeX9dUJ2efMGozUln5NrLVKKpyx16ey7AXay/Ptd/F'
        b'40R6W3qXk9IlpM8lSukS1TNb5ZKo9uPPx2kZrWwaDZ720nkOLBeyJTUKyqUDKx5jvrUfNJrHP5HmMceKwTDHjjkvFDmClxghg4juQsY3SL75nYQ1fYOd+oVWY/BaSMRi'
        b'lQH2NnHFB5x5vsodO7DoaQLGNL+w6woJjKKBWnBoAnHSJT6TxJ+NOB0NGubNiM2KTc/LmTMjMXuQJZNUD7IxgOWggfpCdmJONtG6SA/8dwawpyBarHCnjkRwe+P+rGES'
        b'jJafOCZGbvedKJ7tgKl7Py/wkQ6TF9yQcJ9D2boMmPr184JRiW1oQ9oIBEsQhmAJIRAsanQVb4yu4quNt+KJS7xJiaXdgKkHjcliGdCQ+FiPZeT7WJ9pNIPxWM/AaNpj'
        b'a7aR3xNDjlHAEIUOP5myjBIY940pe8c2XltJr63fgL3zgKvHgIv7gJtQ4SKfi/50OisK5QtHfri4K9jySM0fRzd5tdxQc2bvKHdpnjvghM9sBxxd5Dly/QFXT0WwPO2+'
        b'g6mt+ZATb7J5P8+uRTbEQr/u8Wxasod00C+MJOzYFtQmQ7f6DuniEj3K0qHNAtcwxMXn+pQlulvOa04dMsDnhqixLTJ5cPPiISN8bkxZ2vbaBQyZ4BPTkYfN8Lk5ZenU'
        b'Fo9pHLLA57yR65b4fBJ6uKUAEz9khc/5I+eT8bk1ZWnfxpInNC8fssHntiPndvjcfuR+B3wuoCytW+Ll7ObIIUd87jRy3Rmd33dBXY6bgv0+0U0P3HGhq7utMRr7HAZl'
        b'69C8UpGidAjtc5iidJiicpiqsoke4Ns0pykmKW39+2xDlLYhKtswFT/8vg7LxrhB9EQ/jmHk+YDCxyfJTH8j2/sUOtABHlhFci1AYlIPuKQtvupQpjmsuXPAgVHKuYH6'
        b'70MnjLVhpoW1wcAIG2oEChP0f12CqWAy+qyQOfr8NOuULl0hlyq0Jd6e3AaTInYhu56rsRfMZTMpiY4ao0N3FEaHTqEeKuVqleqSUn1UaqBVqkdKDVGpkVYpl5Qao1IT'
        b'rVJ9UmqKSs20Sg1IqTkqtdAqNaRbXGinaVUh7xCTlHHIkWBzLLamnvpXaEkwIuyevvI0psQz65n0vPUs1/rdwdjBKLRvYBLLDu2bZ4ATvRZxC/la/W6CrnMbjMl4TK7X'
        b'm2s6Mr6nrTV1Ee9cFk4ZW6RTaFM/nBJirtkyK26R0GGQBqQSZST+sm8UIiNGDtZcEhSUimUygceMCll1raRKJi4vxLO6VFIuHPXMqBPPHAwMSed2xKldK/JlFaWSajoh'
        b'K05qWVqB/S1xUk1JZTWd15WAW47JNVqFTV1C3UGuuLBWKsN+mIMG6p/EnVKPzrOHilmFRbWDrCXlqKxMUiitKUNlepWI8qUVVYUFelq9P5xVYy2l7UOvybNL4tZw97NR'
        b'x+ugzuMQN2cjdW4NxK6bhzPpruISA5ueloGNq2VK01vNVRvYxpRqG9j+fp81DgJoSrm0Wkri9dTQ0JrRkJbLqsXlBZLnx/8c7rpINX7oSLJaXLPaGRXnnvWIo11g0Q1l'
        b'kirh+GkIYwVqf2AaNVpQU4kjqMMEhdJiafU4sKSjqcCjNkwHztD7DCrQ5YloKBeISytLxD7jkRIhKChBrywgeXAnzPOq5pvx+4S+KvBIR+yKSJKU/wc9EvJHPYIYlk4Z'
        b'mpA0S1AqzpeUCjzQT+0srELfMflNCVPIxqViNOmkbz0CtbpiHOLVhKCPJlKQRuCicC3T/dKGs+XS3YK+/mxxQQnOb0toIumP0cc9ATpsTX6ppFD9dY+uZQY6VpTTmXJR'
        b'TQQcFp3TPaWeE8bv45Tq4fzFYnU350uql0ok5YJggUchneJUSKaX8AkbqpkY6G6nzwTSQvWABf3RgGlmE3WeWPWZoEpSLJWhHkazGJrsCDt5C2rUw1ZTjvO1/gHe7dOx'
        b'Wya0Vb0vXW1crhXY/Ytyo2qwfG8CDrprgkbVCTtmkJjREXvNTBw1GlumjhuFr8QYmqbCQ6TKK9487JAj8DduXfX6tGkUyZ8I97wETo5b5wLYPVwt9uHM1YpHha2VhrCj'
        b'pIrUOzXGkLZuF10J+EVgQ9VMo7AXGxs7MYxTL7Eb0VajmSNVwkuwk0LCToMBzq64mt5Z4HJou3dtmSwzUpcieS/B9ZBArXrBVeuRqlO8srWDZtfCnVywN472Pmxfpd4y'
        b'CHXQXThrLk0lPA/PgpbxyIQN2FhHW+q0yDSH+zCVlw1AO2x0IhWvstOY7B0ylyyfQtXgaDnQHFE2XrUeyd6+vrQL+kjTm2dT4Co4ZQAb4ClwTXoiPJwhw+EGid5pr7wn'
        b'MmY6GnLuPTi+aNumB/YXWtI+7Qkq/+jqZ9Sf4utSlMmbZqxP19sKfr+082c2V/h5u8U19spTH3HdPfbm9dd7DXmeK345mjn/09y9f/UW/ei767b0fIpotmpD8Jt3Hu1L'
        b'CvrzX9999NmJ/nX5zfmnWt7fcvhmzC5ph3+j7e6Vri2HkmR3as9eOLzk3d9uJRRtfOfRmssPt1fzk5tSXkuPXHXn9lWGb4XN2inBf94n1Cd+FLAjHsqHjYfwzFy1/fAl'
        b'tk1qIm1fbBGDVk3MLmgDG7V8NvxBC7EvSqaKwNYEqGWDpP2iHWAzG54Dx7h0TYrpJhobpNoCGZqptkEehkeJASwLtIKtNG4gNv6fA4cwcCA2TBIDWD64ADtoO+kauFlt'
        b'J4Ud8DJt9Dtsja2ctM0PtINttM0PMec1QsDycNChMemq7blCeIg26cLtDjQY/TlwEWyhDZC0+RE0g+MaE+QR0E5wCpB8f9WNFvF94AV4WUYs1OgsjQj8PhzvFCod1OuC'
        b'w66J/2O9lyAPmWkEjNGIS1Y0VO/9usmUs1tbgULYXq5yCsFgSQMWkxqr969pWqOycFc43rHwIvBK01XWyb285H4XPwyv5Ehu6rPyUNJJ/2LvWPiQ21JU1qm9vFSkaLZl'
        b'K/jtC1SOQRhyia5zddNqlYWbwuyOhSe5OUllPb2XN12d8eagCN3Jpe9c1rRsd7Qc1epK5w9UWcf18uLu2TqQW16ockfhCfs2e5VjwB/f6uzayH7fVPB0fpRubJg4jw8X'
        b'8OEiPlzCh8v4cOWPo/2GM6OMifibYISESHCURaFrv/+Mg0snMxhZDJwcJeuF0s/h2auNE0B1G0T9Z+hQJRoYo2FBcyL8m5EmaOBvclETtFCMaDFXIyuOA7T0n2NDqcGW'
        b'DPO0BNHnp/MlTOfhYTrtx9BJhK0RKv87XCONaPr81M3D1I3AGjnQ1Gkkwac68T8ir5gmj52HxNbnp2whouzhMLzRnJY5a9U02tA0aom+/5vuY+chafb56RPjnutlaHrO'
        b'Y0QKFo/F+5L9r7qQm6eRQ5+fzsLRI2yNjZRaAuz/jDKNUPv8lBU/TRka12HhWIsyIZOYh2lD8XCUYkYBS4sWDL5GwhRJxkuuVrAxh+jkOBcHl2S9xDkvjRqMiwyHQ49H'
        b'MDP/29DjeiHzsY75OFp5bGEhzsJULlmqzR/oK3uufEyJSIeib8YmEXFhIdIYkN4hVqugJK0STprhLSiuqqippK0iYkFBRVm+tFyM8z49VSViVM9h9DhPb4GnNvIdOifg'
        b'euim/IqKJZhUbLkhShJNRvWyyhcwJAy/KFKQXVGG1VHawIOTh6hB58T5FTV0linMAZLCifoG/0uqqBJIcJcUSouKkPqE5ipasRvdKHV/k8xTqNuK1alRxtGp8D+kJxaI'
        b'y4ma+CwbQUColmYs8KioJFm1SifWkbX7ldb/npogBB6x+VWSgpLymvJimdpgQBKkjEvoCB/IZNLicsIKvqRPtCpW51oTSLVbJUW6M9KTx61VoxMHkEEOjRhWjfGbAoTe'
        b'2CQnKJTkV+P3oDsKkNYqxScFE2nzhCul5HmZpJr0XXjEc/BMEo7NJibAsZ+KVCKLfG6eQ7RKq9UV0P1OSoZNCx7ZFaWl2JxQIRR4epZhew1qzjJPzwkNP6TFo2qki0aq'
        b'nI66t9zHLxmtS+UvUjWN1ae2DlTISIPV+H3P9Tz+OOmntT9XX0H6sOGDfL4V+YslBdUCMoLjfwPZmeGh/gFq8yu2rtJfp+/zkTEq1j5yjAGqtkJaIBlm+DhJqaS4CN8n'
        b'FMwLCFzwPFUGqoexRkI3R1pOCMVffUJCevqcObhl42Wiw/8qxcvKSB47SRVe+LwFZaifh80sWgQFPpsg9fBg5IzR44VLRhvd6K/FT/OljEsWLQDGoUbibx/XgV4f5D/h'
        b'60ehG2hMkFqfCSpFX2S5TEoTVVE07lvFhYsRZ5D+wA+QZH7iOvx7/LlxfOPlqEpkxPoqLSiplhbjpsgKSkrhNTSTlwqf/mYnrNNHgPgmu1pSgybX4QoQB0sF6i5CM1QZ'
        b'+uISc31yxNX5EmzRLpygJsQudDas0pqyJZKS8fvfRxA05jbyNnFN0fKaaglaOXAmScGsiioZIWqCOoIjBbE1RSWS/Br86aEHYmuqK/D6tmSCB0IiBSnlhdJaKWLm0lL0'
        b'QG6ZTFy9XDam5RM8HToeyS/eQWHjVSPVIqvsxcgKH6++F+uXCNKRI13/Bz0/bmEOzcnY9DyG7hfmRO3mF1Wh1njgvh2mSZy/vKZYODH7aT8uCHOdmAFH3RgQMdGdiM3K'
        b'/cQTs9ToakInqib0WdUgphhu3zPqCNe+bcKmRYyqbJx2TbigqdFX0Ayn/kXkASSTorlVM5V7ZNNr7IQL9gi4S6QgHp0I6DMk43iI0KmkHP0fsbkAr0HhE065WrAwo6sJ'
        b'HFNN4DOrIQgy9JIxKzbHJyVB4JGbXY3+4vUmZMLHhhFn6EcTc8lMjQsEHugjV7M4GvaJu6GmConIBWi1iFf/8hZoyXaJuVkCj9nYGo8+UkRL8MSkaIHdjFQ2XKwmSlOV'
        b'bElNlexpop4l7k0kXhJR8vklv2ERLXbULtLzyTAEvidSkIH/COYF+i94/scC6ccCyWMTj4YGF0gtQqrPsTL+LD4goEHoEfwH3fj0fRPPYsmSqqpyv6QqcQ06lPr6JUmR'
        b'dDfxrEVun3iuwvVMPD/hF0w8QT3rzWhWSixBQhia+yeemghtSGYrHJ+MiToPSbESSTWWLPBfJGCFPlO+y6+oixRgrwUkPxVhqRUVoD6feFDxQxiNiX5KXCrAJ898okBa'
        b'jT9IdHymuEdDUOE76R+kYm8sp/sEBYSGIk6bmCaM/oQIwn+eyZFFYtTaJDSpPOsmgh+FRgj/EcwLnfhG9TSnnuKexdEaZKtIQRz6RUvC8wLDnnn/8KdNHhm9S/zM/tbg'
        b'ZamfpMdn4skao2QhES0uNgMNz8QzYr60AFWYEo9ePc4X+QfprNU7tRZR6vinJAevXHE5RRAXLEDHAtEozJHJoIcJ9uZyyTP357Dp6JEif2f7aRlqmKYDSZkiDFd9Du7R'
        b'AKEch6fIAyctrShvvBW68JYgdL6Yjm2CJ3UFcJ+LJjU27DElmCcBcN0c0QhYBsaVugrWwrNwozrEKdZ1FR0otcpvecC0LIqkTIUH62K90AOp6diPHcern/YpS02nsY4p'
        b'2A22ZlF1wdxiKFfDMXw1OZP5Boeq60o5k/7tS/rMbvWGcivsxntsw9DGw8DGuKJkek9rFjy8QHs7eTtoMRTC0+Am2VWRhnrp6siYDIpasX7a3hmvZcAY00NTW/Mi3KcG'
        b'8zrkR4+1fe7+9exY/mbQ/WnC+ezeM1urG+yVc351/mq3n9BX+NI31Xf++tfvvls5Kc/0+rFLgfed/B8f2PuGTU7m0b4t7Qu9kn0D/uFFBTrw5ueKPsz8LmjXsj2v3w9J'
        b'jZtxyDC776EJf87O9i/f8M29/Y+h1e91PpR99mvh9X0d2+Db4l/8FM2RU5e/fX2/yeLvv9h19uiOubuOvhv3w8aTuiu++C7q2711P9UWBwVciigPOOETcTrO5c2tHz9I'
        b'v7n5+m+n54oK7Mt/Yf5QNbdez+pc6FsOkabiTfPuvjJ9n+LLw+e3bJ112DYg8tJso5D+pPdKvv5928rHujmnEqYAZ6EeHZJ/hQFujgTPH4V7SfQ8D7SQVGYzwE3YRUBx'
        b'wvPU0fPg+HTaz38baJnsBTdnpoDTbAocF3JKmU7gBuymoyjaYA84oN6SFYHdo6Lozxk9wnDf6eAVsPmpDUpYn6e1R6neoQQXPeholcvwANg2Ck0Z9ICDNKIywVMGe6aQ'
        b'TeNY/SwZZoQseNXHA98Ld+JAkEYW6GK70Rl4DoF6eFUEDoD2tBQGxcxieMITQC40+V+mcMSQuIKRuPgxgZ6Gw7ZvTWh8ijqR6Qx7SuB9x8Ff8TLOPWPTXK20cB6wce93'
        b'92g2xFChLvLaNu8u1l2r4AF3r87sLouuwp7Q7tJbQbfiekOn94WmK0PTbxeoQrNUPtm97jnN7OZZLYb9Ng5yTktUn4230sa7KaHf0l7uorR0I/V6NuPLrZEtkQeHb/gc'
        b'71FOU1nH9PJicH64+YqI3kkhjax+i0nNhX32vkr0n4UvgXPus/FS2niprLy7dO5YhXxk79nrlaGyz+zlZw4xWZYBA/4RPS69/om3LO74J+KABxKWa6Hk+wxxWGY+/Tyf'
        b'xoQ+nouS5yLPJnESPkr8X0gXW8UL+fmRLmXrSvKrDth7KeJV9v69fP9/kbyq/3qkR/Ed0TUznwFrdwVLZe3dy/PG18x8fiGovSBwUryQglyHBCYFhdz4aSwYqBcfyYKR'
        b'Ouj3G0xuAp/1hoFeggXrDQsd9JvefzWh919HdhecqReM7x3DBCMbsM9kgsUsLSzMmTYMRsATCh1exOUep7waP6EHQdJnqxN66DRQDRw1kPT/NqlHvZBZ9Q01Jmufw1PL'
        b'nCu9zCWI2FTOSnOMa5c2tKqEzqapD06D3bIajHK1HezD8aPo02ascpyrFQR8Bq0+Ow1Qf82Gx6qo2eD0Chr4ax24kg0ugy3Z+GEcqfkaBS+68snLfndayXjX/SeMB7li'
        b'yCpMjTTXDC+CfXTU7v5EcJyShMJL9BW5KbxJonzB3gywEUfpwRukoi8jOdRt48kYbNBwcW4MHXm7LNqMipqUhBEN0zKdX6IDOg+lmlI/z0nEhaVfTq+l7/zRwIh6twqx'
        b'54xFhtIIDn1nW7kRJTcnhd4ZKab0nTEMA6rSl+AdlRalzaTvVJQZUCuDfHGh4Uv5XnThiRoOtc3QGpPk7cqMoMEGMTzWDDHsyJ4xYwYaqATUPfCQK7mUOi20Br4S5O+P'
        b'Ee9gBwXXgWOgk7R7WU5s9gyM/3cUA8gcR5fyYTMtS+wu8KfDg8GZADN1eLA0l4gNji+zUW2gIVgdGhzrSort4CUvnDbUEckKByhHuHYRHUB9kYI7SFD2FLCVCnSHu8iw'
        b'Zi1BkzWJ8wUdYB06HphMhtV9NdwgmDUc1qsO6Y22pHHPNoEGe3gEHsueIcCAWxcsOWgBkvNJXG+dEewcTmcAtsLj6rheXbidDrvF3XydqUd5ZwsIHl9z8Gy6R0sD9Kih'
        b'TEdcWPqumZlamtqcCy+g7sT5svHpBkoMtsNuGpwq2JLSM8vFvLxyWnw6PQTRLjloFW3InoHWFoqKXGUA22ar+7kuDewGe61lRkH+bNTRpyh4vYIn/eD7SIYMb2Ryb759'
        b'OOftDOhvajclJezqnVd27cua5Bi93nnNrZYPY28n68iW+OV+0SA7Zt8jiD66ZuPdNYsO/YnzeVtq8rGX7G4+CfzXip8Z7zXeMjTv9hUOOVj+fLms9m9IHPuVndxRX6P4'
        b'YtZ33xt0SzsmdU3ieS13X7fP85d5maxUu9Op1NIvW2dIHLauOxn4gWn71N03ZhT8IPK7QokC9jO7rvEMZLNuv9Vw9GzQz9/OKrp/pf9Db9/8K7+teF8SHrJ/q3N9v/+K'
        b'iJaat0r5bssWfNl+MXzWsW9y5k7L4ejkzv+8P9Qz4vzHb59fdYj1oet3yfz323bmOG/8+MK/eVkOVrlvrf7Ay4LzflS/1yfLdq7O3PzNrO8+ozK/Dgt+LPit89y9n4MT'
        b'A3ixnwpr/Y+8efbo7G1rnFcsyYzNvj7wytqC8jsXu3oSSporfl7m8vvZVV4fziz+6z82f+MR9fvvaZKQq+JG1YaQA5GHGUnnvrHv/hfbr2jvyn+qvtnRblfbUu5Xt/Zb'
        b'lZXRL9UfM9cJeY/88KhuA+cngUZ4/Fn+U2rZpBpsIJ5d0Uji2eJFJB4fjMnEQdL5a0zQ5AZ2EHljKmhCo30Z7EKicBqDYjsywGFn0EqupZmlq9M55IUgqR5nc4DHwAkS'
        b'uJnIAQdtZo9ORtsNDxURVCDjJVVjQQORhL3HQ5cSJOpwwQawhdQ/zQB2cGxopzSNR9o50EB7pPXAdXA/2BOknaKGGQS3gGskxnj6QjDsfQfPuWSMeN+hL3QDLUVuAgpw'
        b'De4sGQ4zpoOMBRk0ttSlYgvwKjw8xrFOE9rLJiSy4elEcMSYCJtqURO2wU10To6j8CTcLBqFtmSMGndhDitOzCEhuTWwQzQG9Qh0g4usCnDAhdBovshCpI3FZLwKbjdk'
        b'JcDDgbTAeikWNKGuWK/tVqd2qZsH9hMSs5bDTX5xGuc92nEPbmeSa3OKwzQZN+b4a0J1z08m5JeBI3Er2WO8+tQufedcSRe5p3qAMa6JU+AJjXdinptQ77mlDYKMINB2'
        b'9sJ5y5ebjogZsrxCaQGdQPgsUw3F5EBNtmnUwRkKDfoFLn0Cf6XAn4Z/UQkiHlJOZsLGZJyZo+7QVJzqw04gtzw4V+HYsrAx6Z5fGM72cWpNY2Kzh3yW0tpLyfO+x3Og'
        b'YzzlVSeWti3t59v08+3lk1pM0NN9fB8k+XUh8S/4Dn9qD+8OP/EWD6Pd55yY0zani6HiB/bxw5X88B4zFQGZaTVpMaEfUohVfP8u8y6LXn4IvmDcYqxOAjJTxffrYnax'
        b'evnBODoquc82QGkbMLqqnrie+F5+DLnemt6SruJ79vH9lXwcscunI3b54WMJjOmxusNPvZU0bnnJreS+hFxlQm5fwkJlwsLevGJVQsmL3GlHt3th28Iu1IKwPv5UJeoS'
        b'1MoY1F9tFvKX2u2UON+JHelB9X+4AQnEddFYXqVg9PI9JypElfTzcXKWoRAb/0kPKRsPqyehFN++qba5RGXl/lOYjaVwyASN7lASg3Jwai1pKZGvUNkHNRoMWPDvubid'
        b'mN42fcJ+JjVPMDikWX2uoUpXHC/Mj+zjxyj5OF4Y40GN8IKGJYbMuD6IPK6r1RPzEfIUXvctuK6hiK/cmtKHeBTfrtHw6awaz/aAJFk1/vhr+Jw1kiDtSaLDC4a5ZmIV'
        b'4SE1JkvacJJeksdFR42QzlZHYeFsaZxhdPSRLAf/A3T0qp/Git9PZzrQzagheVf3RnO8kpFwNCMZrVxoZQKdOcngDGzw9gWXUoQcKhlu1K2UwWN0lvtuH3gc7gan4BYX'
        b'sN6bolilDLAeHGMSIJQkoKikYVDQRNpax68jQo4xWmm2eGUyKUYK2JtFIQX+JmiQXvriV4bsS3R5e8HtV2Z26wN/0+ui/CU8M7OmoxlnfY3/vfbr7+b3+mQnWZ5s9P3U'
        b'vNJy2tFp34htLPMXB35e9+RvH1//89Tla8sWD+38MrpIsk5S3ayTsz3y/dVpJ3v2KaNTN3lWf61TJrqyasHM6xG5vYcrFy797VD+j3P3HFnCCT2f9fKHHp59Eda91yvf'
        b'tPxuIzUvKW2fbMPVH5Ecdm2RZFuliG1aYXp2c6Xxb2/2vnXj30enn+zYsW6o7y8PPtt42Uz3S/5v3+Y3yzrrt05qNHB+9MZXqoy/ZXf2/TaoTO01Pu6/iVVk6Oi6rfcv'
        b'm080tl2LZui1hL0hOyA0IUaTSHADnEHdDU6CAzjxFDuMgdaAZnCezk11DZxFoiJ2cqdDMvWAYjXcylwF6hcQc8wyz2hydbM3E7xWR3EymLZx4DRZxZkysBMv4N6+Kfgy'
        b'Bc6GGcAuJrwmiCD2ELCrGq35F+DFpWpTzBTQwQUnmKCdCTbRckBnFXhN5I1hHzanISnAaJlBDBPRtgd0EDkE1hfDw/gVfpk+TLAlD6/wnlngNXKRW20xnFRLnVFrZmVx'
        b'Ip2tipMBFIjuFLjdh1OB5HbOQqYzPAKOkdcus4dNXgQO0sdXyETrdivLFTaBV8zhRtpM0w42g00iLDj4ZehUvUxxophWWYa03LELXgEHRTS7Il7lGgXymEjyP07nUV6p'
        b'C1Fvwu2kw7jgNYoTx+TDy/ACeXG5L+igpSr0irUjktVudJ0okm2ecCdNmQ5scEdSkYLpDdbH/9cgiRozAD0d6RLEr+HpSCaupfNsGaktQamOFG/S/rCmsP3RTdFyl7sW'
        b'7oq4c9M7p59L70zvcbnrPe1W3Fupr6ferr6bkPORtWOvU5jKOhwDT6CZ2bDF8KAxWtUtrPZHNkXujuqz8FBaeCgm3bXwH7B2lLsoWIr5KuvIxvh+N68TS9qWtJcRK0uL'
        b'fjO7uRBN07gCeY4i+H2+P7G23ONZ7U9pStkrumdj1xrWEtYa3RKtcLlr49fPt27Va9GT8w4Za1XFtPSiqxqwc5Q7nXBvcz/h3eatqO7KUTlF9iSo7GKHKMZkr1tZ/bb2'
        b'rcktyfKcQxlPWKiEFN9noeefMDWnv5A0um/4mCfq67ypr5NowdXOnFz16A9XAnoM6DzJo6APxhkBB7YW5toKAYPBxymSXyS9F0m0JGQTewWdwYNk9dAbXryY5HeG0Hws'
        b'CII+g9JGQniOEICTDJLCsVpSJqOhDB5omiU0+x8aM7V6Effb2rH/6N48h3tzOArYES+rCxgE8uA+m21k+sCQMrZsY7XFNy/rLng9+22LWykDk23lXq9avJrdw307/hGL'
        b'YTwT42dExzCesNyN3B7qkAI2+nk/i6HBQgjFWAjhBAvBxnnA1JfGS7AJbRCNYCGEYCyEMIKFYGEzYOrWzwtAJRZBDfEjJdG4JIZBitSP+ePHArVBFTQlD/QQ7UMU0zid'
        b'0SLrtrhPfg1a2RxIaJvc5ximdAzr4Sod4/ock5WOySrHVJWtaNDeqS2izzlC6RzR46Z0ju1znq50nq5yTlHZp95nMexEjIcUg5/GQMyO6nrCqWEY+Tyi8PGhLi4ZIiVP'
        b'ylkRRnYPahno/S3Od43snzB5Rl4PkRLkcB//okP7yQK9dlWmDGusBRTRWXUoI2sm3D09WMjIkDqs/pOOLAENxrTWdZKm9zI2xJj+qXjdK8cerZEanHl/8Mb6zUv9ojc8'
        b'4VpVDCa4/pR/wP/ewM+m1wo3fe9blmVcf7jixicrp/zqY3BlSH/Oz4kzFGt+/v6VezEtez6eu3b1jGvRzGvTDp/8umP+kpDZS0xOl53e+DfJ9Hb5RfePrw+2WNyyfO89'
        b'15sbrv1z1qu9dgf6wj85enjJYf7c93bqzct4/1jjL8FHA9JLUoMOZKcuGSw0S9LNFeoeWfe4+R/czrT8J/Ku2VPc79hfXN3K/U62asjoUsvsZWcCCyXVbT1fnPlg/pHv'
        b'Zm5y+tLk8a/9LsklKWEXj07JuvjXfNsgcX7xB19Gr1j3csTtVW6p82e0uqebiC1LLhd++c8kro/Hoqz6ILe/+HQ+SN/ltqEi640/1cGm8ydSXo8eLHJO629ZKKm8scjg'
        b'6D+LPzxcGvZx98Hoil9Vq9aZmBVN/+zW4nfuRglZJIMTOBG2EG5F6hxOGtFqCHfkw4N01No5cBme10okqd7+MF6iVxNMdHd4Sgd0a+9l1II9nlpbGVEeQpexX5/eMw//'
        b'F9/6fzA7uNDrXAz599Q0MWbCGNTLyyutEBfm5S0f/kUWwKmIUf+NFsBgyshyiK3LtRowMW8M3Lq02XHLyhaZPFAubgs5uFwx88Cabpeuqh7H7pqemd11F3xfT7htDpPv'
        b'BKZ9xLduDmwWt4Qc5MpTkRLVZYX0wN6oDKVVRm9WTm/uLGXW7DtWsz+aJJCb7y7vNXXBCfxeYgzpU+a8xtgmy4a4J8FmXJefKHR44uHO9XlCocNPOYwornXjrEcU+vPT'
        b'aoYL17p50iMK/RnKYFD6pk+YVWyu1xNq5PiYHNHXqm86RC4OVXMpvpvCQGkV1GD4mKPH5T+ZVMXi2qLb0fExOQ4t1iWVZZFqRo4PyJFUdp9c/Hkols/gpjAGzB06DHt9'
        b'klSC6Srz5F7DZHrB3BLLT9Cj3tCzSLBRb23YDTLz8v7DrYz/G37Bn8ui0Ztk460sZky8smh4BMt/sjiKVtgCGAxTvFFCH3DEmumLBKxhoeAkJ5K6ahCrw5JWvPtvhuwM'
        b'KrrM3CbZNkUfzOAlfPK7RYhgfavguGlNbLljh96PNfsGuUuvXe/RC+t00Ys7HhH0rv97B3jSwMK3m07ENG3ZX1LovKtn86mvL/K/yV/9g4/u3z7PrV19rfTuJ7OM9sDX'
        b'/t6vqrp/LMN3xaxVxVm3m1YZ2/5Smt3kXvpgT03rggNf7DrMm9Hr39V8S7zF3J4h8+4a+PwN/SWlM8RbG+wW8/o/W+ucUfb+zysW/aur2OxDkxO/+iqP7UEaBhGnF4FN'
        b'WEjPxHvt2wTWIl3KAJxnQgU/kUxLCXAtbA0A10WZPrAb34aEecoMXmOBtjousVblwS4p2OqMtLSdcCc2RGG7py5lbM6yT4ByMukVcpPgKWyQS/dM16U4bKbemiJywR5s'
        b'nge3+nEoRja1wgq2gxOggX5iAejwStWhGCIqCjYgreIk3EXomYxUgyuoIiTfozd1T8V4cgZCJmyELeAoDbb3GrxZIlPfsRAewHfopzBBVyWgQ2r1YCfYLgK7JMRSS5v/'
        b'jOEWVoZDFJ1kbx+8WIhtfzoiHu3+4GZCamYvz8CarDdxHqgFF5HGZWjBhBcRSTvoaOD2PHAdIB3Bu5KYNa/DvegefXCBCS6CVykyi0dUwJPolvOGoGHpyzXwwsuGL9cw'
        b'KKul4ArcyQLbylBVuJ2z4WVDEUGARC25itSMHRQamANMeNQXHCQA/0gbOVMJtoKdfiK0XOzAO9ZID9qMS3QpGxc22ADr4U6h53OvBv+/XBzGnQA8yYIRo/n3jCVjZDYg'
        b'Eax6o0KL56LD72g6eGhN6Vj0G/H6jOyVRvaH6lRGHmuT+tn6m9LWpfWaOXaE32V7f8g2Qv99zHb4hO3+CdvnY7bzE85cUx00y44cH5PjUJ2AMuStzdQyPDkOskol5YNs'
        b'HOw0qFNdU1kqGWSXSmXVg2xsSxpkV1SiyyxZddWgTv6yaolskJ1fUVE6yJKWVw/qFKEJDP2pwr6ROPN6ZU31IKugpGqQVVFVOMgpkpZWS9BJmbhykLVcWjmoI5YVSKWD'
        b'rBJJHboFVc+S1ZQNcmQVVdWSwkF9qUwD4DLIqazJL5UWDOrSIDiyQQNZibSoOk9SVVVRNWhUKa6SSfKksgocyzFoVFNeUCKWlksK8yR1BYPcvDyZBDUlL2+QQ8c+jKwR'
        b'MtzZi579TyAYGRdywDGaskw8JL//jtbxJ2YMxsssPD+PPj4gxxeZrfGy9roBJ9aGet3GINaN9YteEQ5gKijxHTTNy1P/Vq8Sv1irzwWV4oIl4mKJGipIXCgpzBDqEWVr'
        b'UDcvT1xaihZFQjtWxwb1UY9WVcuWSqtLBjmlFQXiUtmgYRaOpSiTJOLerIpjqrmB5gvc9l/0osoqCmtKJdFVyUw6VJKkpkW6M4NxHzWNPWRMGRit1X3ALjVl8IYWOlJc'
        b'sz49G6WeTXPqXT33Xu/o192gh9I7tV/PdEB/Uq9VkEo/uJcdPECZNvLfp6zJq/4fA46btw=='
    ))))
