
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
        b'eJzsvQlck0feOP7k5D4kkVt4kDNAwn174YHcqOCFVgwkQDQEzOGB1XoTxQMVCypWtFhR0eLR1nq0dqa72+22W+Km2yzd7rpnt93uLt3ad7t9+3b/M/MkISGJdbvd/b/v'
        b'5/MLYTLPXM93Zr4z32NmvvMbyubDMf9+tgc5PZSMqqWaqFqWjLWLqmXLOf1cyslHxn6ORVGXWJZntbeMw6bkvOeQ/5I11XpK472CjcL5Mq59+h0sFOomn1AKi5LxqimP'
        b'XSL+l1s85xbWzFtCt7TKdEo53dpIa5vl9IJN2uZWFV2kUGnlDc10m7RhrbRJLvH0rGlWaCxpZfJGhUquoRt1qgatolWloaUqGd2glGo0co2ntpVuUMulWjnNvEAm1Upp'
        b'+caGZqmqSU43KpRyjcSzIcKmrpHo3ws30CfI6aA6WB3sDk4Ht4PXwe9w63Dv8Ojw7PDq8O7w6fDt8Ovw75jUEdAh6BB2TO4I7AjqCO4I6QjtCOsI75jSEdFD6afoQ/QB'
        b'ene9m95Hz9X76T31Ar233kMfpKf0HL2/Xqjn6X31YfpgvZc+VB+o5+sn69l6lj5cH6Gf1BiJusV9SySb2jvFvqm30B4Um3oy0j4UhdD2ISxqa+RWupqKdhm3gdrIWU5t'
        b'YHk0idiVDbadHor+Bbgh+GZMqaZEnpVKd/TUEMahMKKk8p9duXBBGKWLRg9Tw9fCTri3qnwh1MOd6fBAlQgeKFm8QMyn4udx4atbwTkRSxeOUsK7nDmakgp4EO6vgPtZ'
        b'FNgGX/IsYYPhFnBVxNYFoyTgCDwNXywrSS7hUfAKPM7lssBpOKAh+cHdjfDZ5eAOjhbDvagUHuUL93Eq3eA2lB8nqQQHKdAJ9yW3IZj2o0LKxJ7gOhvcWA8u6KJQAtGS'
        b'cBR/DRxZ4Q30G9bp4PV13ut0LCoIHuKA/UvgVQRrDIb1GnxlFugEh1LKxIkYYngIP7lRYTFccAw97AxnNbBsmi3M0mwXkXMstAM1HeppLupnCvWuG8IFD4QFXggLfFDP'
        b'+yEcmIQwRIAwYTLq/yCECSEIE8L04Y1hpPfR0NnrNqH32aT3WQ69z3boYdZWtrn3ncZZe79xYu8HOen9KUzvS4vcKG+K8u9apfS+7TGVIoFzZ7EJSqzObFfmPbmJCVQK'
        b'3Cl/hCb+zeuUv01pZwJfDudS6JeepdtU3rNKSl2glJ4o+JpHMPdhADVrTLCJ9f6y4mVfz+yglB4oItjzOGvYjaJTN8npn6cvivucCZ4X/plftx8rYYwK8fo6+O/FB6hR'
        b'SifG2PEyvJKDer0zZWFCAtyXUiyeOhPuAxdqEkor4KFkSYm4tIJFqfw8psPb2XZd52Wp8z7cdV7mruPZdRuFO67Ry9o13H971zgMTDcnXeNdqcZtqwvEDfA0PLykehF4'
        b'CVwRL2FTbA4FT8Vt1uEsSxE676pmU+i98DLYH50Ez+qEKFwMDsO91YvYaChGUc3UPDTWtpEMc2eBHngUEY0UKhKcSIFd4K7OH3eKUgiPorYTU0rYIQ6bpcP4Mgt0gO3V'
        b'FeD68oXwAI9ib2aFw264WxeP4qaWoNGChmJSGRpCe8sXJoALycVkcpDACzzQCw+CHeXwsC4ApU33XQCuo8pNQ6PxyDRwG5xR1FR8j6sx4hdP//nJN6ef2r73zNHrR9eG'
        b'RHPgGnrPNsmVgNyT21lP/HR31H9t8hZw5ojniBt8GjgrPBvil/rs9FnwXEdQc+h8n4b4v6X3f7Umrvfg1J8Jnwv9Pq9YENk4dZanxtPr4seJ2V2nFgje7o+79uzxN/yE'
        b'H16RztWFrFxK1wStiK8OFZyolCvz1908kLXbZ3HOz/fEDfq81fxc2bZyt/r12rC2m9oQY/jTlUu8e0rZ0PvHc9YFFfj+5MdPD0df+DV14u2df/Zd8Iez+zLTnmuTrH6t'
        b'0a/9LbeMthcpauhy8Tz33SLeQzxnNcK7T5XBA/DCkiR4oEJciue+AHiTAzs2qh6GoASVPvBYUqkY6kvKK8GZQh7lBa6y4Smd9CGeqxOaYHeSRFSaBPeuosmc6Ae3cVqf'
        b'BH0PMX0D3aiPb3iBC+lFycU6NJftS2FTk+AtDrgMLgof4mkLDIFLNOqkffAcvAwPwf1ols9jgavgXJTIZ5SdIFLjrv+WjsYHOTS9bfzzZeC0RnVru1yF6DCh8BJEneXr'
        b'Z4z6qOUqmVxdp5Y3tKpl7faPbFxWE0K9L7ZRY0+yqMDQrpreuMMru1fqiz4Ij+1vNISLjeHiMcrXZx6LcQ+7d7G6skyC4K7pJnpqV1Fv2uGSrhLT5Miu2n5ev8YwOck4'
        b'OWmM8po0j2Wi4wYnPz/l4pRhzc25BlGhUVRooAtdZvEgWaL7Of3zzngOeE5IN8gb3DASn2OYnGucnDtGudknfo9Ov0+nD2fc5BjoaUZ62sSXaA2Tk42Tk8conjXfnP45'
        b'g7wzpQOlZ/wG/Ca+jDvYbPMyDskUe973rO/gegOdbaSzLRl+Fxo9EpN1k4v+Fr/sdcfLEDPHEDrXGDp3RDjXJAjsyT2S21tkEEQbBdEj3tGf4SlHjeccke8on+mDUbe6'
        b'OrVOVVc36lVX16CUS1W6NhTyLRHDF5MNO8xQT8KReCqY0Pkzcfpe5HyBe38zi8USjlHfhfPAN0iv2Lt2/9ptXmNsHkto8grQ5+zN25/3gOu3rWx7xa6KbRUmdz+Tu0Dv'
        b'9cUYj+L524duq2L+NJg0nfLIoK77FrI4dtO2lfOux9SF10PJMd+NuG4Zq5aD/rkKqpaHfvkydq2bzENPNbJk3F0ete7Ex9vlXsuE8ZHPE9Ehlp7dyJG5oScvwkxy0ZM7'
        b'evKWsRBX3STyHOUvIo1WSXrvo6/RmGng2ADEtdCRrRggFsPr9uCCKVI0JnGIzd87gc3fwiUkjuNA4rgOZIyzlWsmcU7jrCSueSKJ4zghcVyG+7jkz/W/xkaIM2t1cvaT'
        b'oZTiZx8r2ZpGFPPh0rdOvjnt1JmjeZ0sfv7ymF99EhxHn857ZtL3n+ddkO34NDA1YzUry/tH2z5eCj8fSF2yPXGONn3qH8ulg1KlfLaJc4Mj6fH49dV78t59rxccDxqu'
        b'v37hqMe7cUX9L7+2+q2fIQlmizCnpV3EJ3NlGjsuycoRJvEpP/AcZxbsaAcDiWQ2RjzwMBwcT8KhvP0rkzluHC8SDW5ubSqDneWIQxbxKXdwCF4C+9gbwWkOmekT4Sso'
        b'CJHLshJwmaL4uaBrBjsE7ppHYkPARbAHdFYh9pdL8WAfPAzPsuCtVM1DTIU3ycC5JHExYZ3dazLhDTbYJYN9Ip7rEcizTM1k4I2619UpVAptXV27H4NBEksAmXx1FDP5'
        b'atlUcurQ9JtBxqRCg39CF7fbu3eNSRjcXfaeMPa+MLZ/jUGYZhSmDRcahFldLFPE1L61g1MH0wan9rWixF6mKZHox9MkCEJDcFIcytlTdqSsn2sQxhqFsSOW7xgHRZIU'
        b'aoF1KuKPcjVyZeMoFwt0o27r5WoNkv3Uk3GCQGu9MPasXo3nFmZGmYpnlIl1WoFTqsmcQmYVDZvFisKTgmvnu5otPsMI3eMhpi77FnAa2M7GZrt1bDIjs5FNxiXbCevJ'
        b'8XDCTDqOVDT22Fs55nHpNM71uLSCZTcudckYo1+IAIe8EPvSiRC+MwUeqi5m8HvhAtAH9i/CrOhMeIY/yQ88r+ioXMnVzEW5st3KTr6ZmXYdjdozR9PQuH0zuHNXae+v'
        b'Vu4Rfr9yT2I2f498v7f3pRDp2Yr9s6aXp/6CHfO5+8je5+J7t1/nUV/8xeul4mMiLhkVS1SVeESBu1mWQYUH1A149SGW9xbBF+AFeB1Ji4dCdPCQRNxmZoFCt3LBbnBg'
        b'zUMsdm6G+ynLwIIXvdHYQuMK3i16iHEKlfAs2FtWJWZRbHAE3FrPKgTHnhKxbQYS7kLLKEKksUmuVWjlLWggBViRzhpGxlKBeSzN5VDC4F5t3+YRQSL6fhAaOxKXf7PG'
        b'EFdoCJ1tDJ09IpxtCgrrbu/ZemRrv8wQlGQMShrxT7IZETw1FsJHuSppi3ziOOCRcWAdBlhKcgYR7mqNkhkJCKY5HBYrGOO7U+c7HQPHPJKoS755nP8r9MnFOBDhdqaA'
        b'3vkwWJU+Pgh08KriPHxIkUGwefL3GML1QuA3DoJT5bOeKE/dGr/Tp1g8J5XT5EV9Uu75p5c6RRyCwOBYyQo8CtC/zSgo3krGwFxwFMljZAyMjwA1HDYPgpVuTBG3g+D+'
        b'5CYb+oLGADjtJ+JMJBscgu3j6K5xgu4aO3TPM6N75WOgezSmKJ69mQZ/eoR8bad/guxqCX4xb71UqXNA+YlTf5Y9zlvBaqbsZ/8KhPSRGMFdO98V5qvj0Gudz/oE4znW'
        b'WR+rIKhG7n9w5t81EeN5TjCeV6lLxQhzAbwEurAyrgbqxWLJwuLSxVBfVb0aPMNI+cVI4JewKC2868EHfZN1SSgTQsFXljgfJ4sSaes4Ac/Aw4qNN5dyNAqU6WsoOPlm'
        b'+qlneFj8f/no1aOKEAGjAKj/OqCIn1ssXcn/7eU9nZlp69Nvpb7+5k/Tjanaa7LXvvcjPKCWHX6Y9m5qzdW01P4//vkw5+P6PZ8GDaeuZp1qXp+ePpDKJRK5qE94MSwM'
        b'SeSYSysvjPbCNVgRZC8wr2wgFAecfXIZw8SBo3XWwdaGBG482uAxeAPsYYbb1DUOJKcwhuH0AuCrVorz8mIzxbkIbpKxKAR7vDEvlwvPEXaOMHPw6Y3fyMxZpahRvq4N'
        b'i9XtPmbcZx7JaNxiHo3LOFTw1K72/phBriFIbAwSY26rkPUBlhNnGkJnGUNnjQhnmcLpMYo9aT6LcbvmIoLUnzlQMBIkQd8PIkQjiTPuCQ2J8wwRRcaIopHgojFUbsoD'
        b'f2G353v+Uff9o/pjDP7xRv/4EcvXZkS7MSMaq1wnDGWbqrlRZjpmERFn4FFtX7MWnHA9ZSFiSx9JxL57csYMalutoj0rxyFaRaIONpMwrEXk/Nu1iI9FwjiVirx/aLka'
        b'PCkmvZ6OiVLU7qhTh9FoO3dUjAjT02npqUONuz69uCwkeE3Itr+2HeaVey+7l06v8vnw5Sslqa9ffJ169930n6ZHnby7LeTkL0KLagrWHl/buyZ4TW/Ltk8iFvf/97K1'
        b'Iysnv3UPyVND2cJ1n0ch7g3LU2gUbAu3lYguwrN4NMHbnmScwD21aJ4hA0VXbKFK8Gl4g4wTeLkJ3IKdySXwgNgTHuVT/FXs6CfgCyTSG+yDNyzCFHhBh+Updkj1WoRz'
        b'j6GdwDhH0zbSkRuiHlo1InK+49QEP5Mh1WoeUs0cKiyyN7A/Gv3JBtYapqYbp6YbQtK7+Kbo+IH896Iz7kdnGKKzjNFZeDjFEedwWdfc3lhTcHif13vBovvBosEYQ3CK'
        b'MTilq9BEx1r1PUExXVv6lxiCko1BySP+yY5k0eX4IUTRZvjMw8NnQjWwdKdpo8wqliY0fALwAHHtfGcjJwVXgV2pxt0t8sFSKOZl6+pGPevqmMU+5Peuq1unkyqZGIYB'
        b'cG9Aw76pVb1p1N0sB2rUsWTqa1TIlTINEfsI00u4ADJpkKp/0yxqo4vCeNRu1qdU4/jXmY62/D0QBOnxhKgvNgWFICcwVD/fNDlIXzTG5fug3nXl+HN8kscoJ44nx0eE'
        b'fQ6OJ98nAed9hOPP80FT+OM5BHvIkttcuF/mVVoBD6Z4gNOlLMrdm70anAJ3HNgA/PlsNZ7MWBOUWOxarowj48p4fexaHpvqpmT8fj7l5CNzs18Ktn+qdZO5k4Vhj1H+'
        b'PBVi1DZ9KZwrr1doW9VyVUqZWi5jvB/5E4z5CE9lXwYskavbdU2aNqlO09AsVcrpDBSF4f3Su1yubdfK6SK1QqO9wCYI9tH30Xj9/HgARZW1qrStBZUIoeiEQplartEg'
        b'dFJpN7XRi1VauVolb26Rq0QFNg+aJnkTcrVSlcxpPpVUC++olRJ6AULHVpR3Sata9TjpnBW2Vq5QyelCVZO0Xi4qsIsrKNOp2+vl7XJFQ7NKp2oqmLdYXI6BQr+Lq7Xi'
        b'ElmlWlJQqEINJi+oQfyuMqVwrVQmoeerpTJUlFypwVywkrxXpVnfqkYlt1veodYWVGvVUnhaXrCgVaNtlDY0E49SrtC2S5uVBVUoBXkdankN+m3X2WS3PNRvwNBhHS5t'
        b'BgQFSehanQa9WGkDPJ3mMia9oEyuUrVL6LJWNSq7rRWVpmqXkvfIze+T0/PhHaVW0USvb1U5hNUrNAU1cqW8EcXNliMBeS0uN8EcJLLE0fPlCHfgQKNWg2uJm9QxNT2/'
        b'XFQwT1whVShtY5kQUUEJgyda2zhLmKigSLrRNgI9igqq0YSFgJTbRljCRAWzpaq1liZHbYQf7VsNh6zFOCyu1LWgAlBQORzASvO1uNWY5keBJbMLK3GcXK5uRNMi8lYv'
        b'LSmqEc9pRX1jbnwyFhSqZoRruBxzsxdLdW1aMX4Pml/rJeZ3mv127e4sHLe9XSXSHSqR7liJdGeVSGcqkT5eiXTbSqQ7qUS6q0qk2wCb7qIS6a4rkeFQiQzHSmQ4q0QG'
        b'U4mM8Upk2FYiw0klMlxVIsMG2AwXlchwXYlMh0pkOlYi01klMplKZI5XItO2EplOKpHpqhKZNsBmuqhEputKZDlUIsuxElnOKpHFVCJrvBJZtpXIclKJLFeVyLIBNstF'
        b'JbLsKjE+ENF4UivkjVJmfpyv1sHTja3qFjQxl+nwVKcidUCzsVyHphHzQ5saTcho9lNp2tTyhuY2NF+rUDiai7VquRanQPH1cqm6HjUUepyrwMyRXMyQu0KdBhOUdsQg'
        b'FSyFA81q1G4aDXkBnvUYGqtUtCi0dIKZ9IoKalFz43T1KFLVhNMVwQGlUtGEaJSWVqjoGimiizYZqkkf4JgFZKHXtrBxMi6uRVCgCSMBZ7eLMOdHUbGOGdJdZ0h3miGD'
        b'nq3WaVG0Yz4Sn+m6wEynBWa5zpBFMlRIGbpM2hzxJYg/IWFa+Uat1YNmIqs3wzapxpqM6YjZckSOm2wCYgtqFSrUG7j/yXtwVDsKwqQXzdJ2j+n2j2j6kWq0iNqpFY1a'
        b'jDWN0mYEP0qkkkkRMKp6hLbWHteq4UATQqISlUyxXkIXMfTD9ind7inD7inT7inL7inb7inH7inX7inP/u2p9o/20KTZg5NmD0+aPUBpWU7YFDphkblVNWZGQzTOGDmL'
        b'NPNKzqIs7JOrOOtU5iS+yvnbMN/lLNyOFXNdh0fEu+LO/pnE6a7fbMenPU4yNFU6S2ZHArIdSEC2IwnIdkYCshkSkD0+G2fbkoBsJyQg2xUJyLaZ6rNdkIBs13Qsx6ES'
        b'OY6VyHFWiRymEjnjlcixrUSOk0rkuKpEjg2wOS4qkeO6ErkOlch1rESus0rkMpXIHa9Erm0lcp1UItdVJXJtgM11UYlc15XIc6hEnmMl8pxVIo+pRN54JfJsK5HnpBJ5'
        b'riqRZwNsnotK5LmuBJogHWSFVCfCQqpTaSHVLC6k2rApqXYCQ6oziSHVpciQaisbpLoSGlLt6mMGsUgtb5FpNqFZpgXN25pW5XrESRRUz1tQKCbUSqtRyxsREVRhmuc0'
        b'ON15cIbz4EznwVnOg7OdB+c4D851HpznojqpeEJfq4J32hq1cg1dtaCq2szAYWKuaZMjeZhhJseJuU2ohXzbBM2X18M7mNJPYBuamHAz12B5Srd7yihYYFau2GR2ULuk'
        b'OQalOwYhMUeJhWKpFvOldLUOFSdtkSMyKtXqNJitZWpDt0hVOkRe6CY5g6aIHDpTA4hssigwcVfISLZvTOykfCdEyXnZjgmJimm8dWjEfNNmlpc0ZSOONzcy40+38WOZ'
        b'cFxT9SWroPKCu7oI6x/nY6eYMq95qkuwU4p1nDxNm1KhVZdhTRiLUV1iPZpZbVlB1JaMDg2v9mgWT1RbirDaMkRfPManAlNMkxPG3LjBvmMUclCYJxUY1rV4jJs6aQ7r'
        b'b/Usyk+4T941Z++a/Ws+bWJlBIY+pJCjL8J/jB6R7Hw6tBXu18ADSXBvMuxaAS5wKfds9tZqMPj/myaxSeQx6lnY0NCqQy2hahr1nY3QjZF4pG1y5UeTGT0i1qF/GToX'
        b'IWAL4mqwTpxmZC40fBRo0kNJ8Pa+US7mvtQ1yPv5HRSwuIVhplqbVXK6ulWpTClGs6FKXNaOdTvjj+Pza8HSslqayYZ1eHjm1ig0OiYAx9k+M+N9PlY5MrIF86LZi8XV'
        b'Dc1KeAfhnRLxQ7aPBbPlSnmTDFeE8ZoVPuP+dLNsVmBpCSJrYGZUbp5WLAIjzTBkZrFzXEFmFjiJmIBFTZQYDWwtEUnMJZDXKRUoAfEpVI2ttJguVGstoJhDSlQ454RA'
        b'nCzdWbJ0h2QZzpJlOCTLdJYs0yFZlrNkWQ7Jsp0ly3ZIluMsWY5DslxnyRB/U1Vdk4YCypiOwXy2nASmOwSiB7pCjuZqixaY1knocS0wCmRw2aKWldBYVrBI/Iy6d7wb'
        b'6fKk8oIinWotOVIlVzehybEdT2g4fPZiOjOPIfGNliRYHe0s3Iw3TJSTAgtqiSiCK65ukeJIK4o4i7Giiqts6Y/K5jySQaFHZHMeyaDUI7I5j2RQ7BHZnEcyKPeIbM4j'
        b'GRR8RDbnkQxKPiKb80icLe9R2ZxHku5OfWR/O48lGR+NKK4xJe2RqOIilmR8JLK4iCUZH4kuLmJJxkcijItYkvGRKOMilmR8JNK4iCUZH4k2LmJJxkcijotYMuIfiTko'
        b'tloL7zSsRaRrAyK+WsIUb5ArNPKCIkTix2c/NB1KVUop1mtq1kib1ajUJjlKoZJjhmxc0WmmnHjCK9Q1YpWcdZKz0FIUhWfecYJMJxSq2hlmHK8losm4QqFFpFEuQxyI'
        b'VDshesI87Jh5fCafGKdWwhc1ZjbBLqaYrCw1ahFXYhXpCCURE37HqfxhrqmZmiPSjygNZt8bCePeggm8Vq5AzaK16qhLEJetVTQq1kptZ/9aIoJadde2bAYjuNqsYdqy'
        b'SUVyRqqRK+pxVDnqNbwop2E4G9eMmq1eGsGN3ixV6lrWypstSnRCBAkXtxRxcZXqZc7ZZ7w1vN2GcbyD4xdNZKGjbVjoHNNk2ikLHTxp2t/SbRnonDDMP4fZ88/4oBbc'
        b'uQRc0ZRXwoMpMilho+H+Mjdqcj3XG/R62vHQ3hYeOo6NeGihPQ+NuGZ+t1e3l4zdLegWYG56iPccYnEvuVmye6A/WYyep/fRCxo5Mq9dHvZbiGq5+JC3zHsXJfMZ8n0O'
        b'veOSdbdiLZ/E+aE4f4c4NxI3CcUFOMS5kzgBihM6xHmQuMkoLtAhzpPEBaG4YIc4LxIXguJCHeK8cf0a2bKwXe61PuY2EUz48xgKf84T5fK0a5lYPdvcNlzZFIe28bW0'
        b'b7dnN6sRt7EbcS0lRjyHRINLHuMlyuL0zF5OfPLXH5XqJot0KNVPFo9S8fTu5IRwAElF7/Ko9Udhk1AtolAtJpE3C4am2ss65lPGvnq/Rp4sepf7hJIDiCTUKEoYdZ+L'
        b'j9nNqV7yZYonbfOxBNPMNMqcobdLcYGnXoDHBR4CH2FxTL0K+/AObiIOibw/wuB8hFv/I7w7eDy5usmSXI13l6lX4yS4vT/Cp24/wpgschv1lMrWo5lZXaeQjXo0oPlR'
        b'pcVeXykzBOuUiMHVNo+6N+jQ1KFq2DTqjs9wKKRK844fr0YF4mnrWtC01UzePcqZt3gRs6VIjXeQNrhT4x/8erIF7mnKst3W9rA/Of3LQkjA1buhhmXO/vIbPcmuPYTG'
        b'ez0n7NrzILv23B127Xk47Mxz3+ph3rXnNM72WPbn+PStXS/gTwlTbUW7XENMJVj7TkH2pTTIJQ5ZHALykQgnbaHHmzzfbCQBTdNYm2e2wmBue6lK61AC/iTMRrOr1jK3'
        b'iyR0Ic6P5uEGmmzMpnVtNKJGObRM0aTQahzhMoNh7W3nUDDRziGwrll9AwxZ3wSDPZrl0+XkF4MwP6XcEmsGTOMcFky7MdVENFdC1zQjOopGk5zW6OqVclkTqs9jlcJs'
        b'CGIEflQSLUVFoGcGflrZimi6WkKXaOkWHRL76uVOS5GaK18v126Q4zV7OkEmb5TqlFoRsZGR67ovzMMrn55j9tENWOmbYF0qtlEWi1yVYhma+RZs1Vg7E5vkaFXTCczG'
        b'o7XwjrpdrnRZkHlXXz6RWDF3h4phcMQ8UyXImyR0VlpqMp2TluqyGJu5IZ8uwg80ecDFNSpUaNQgGOlNcikCLFEl34DXrddnSzIlaYkix6b6xt3x3sx5xeIV/ksqWbMo'
        b'qm11MicuhtLh7YdtcDe8BDsrwNACqC+BB8pS4N4FeM+8BrxcXC6CncmVYrAPHipfWAwuF1dWVJRUsCh4GPR7t7rDc6TcuirvVf+gUilqwWrv2x5KSofPxirgdnDYWbnF'
        b'8CDcW464CbDXtlT4DDiDS961yZuCB4JIwW0yj9UBbBrvtE4G4fkUOb5PV9fDTvAsuDN+gr9YIk4sRa8AV7hU9kq+BnbBc8QIASnlfoSb8AesYJRztTJ1dj0DHngJ7shx'
        b'Bh7UozI7kzGI+0VLMHRscMdcbfCy2gtcA3rYq3jn7h9Zmn5U0PTkqgOHCjzZaf6zmv76Tu3GXL/hitAPil4X6N8On6V8abQx5aOBN4pn6Lf7/yLmzvxVPwlLOHL6TPLs'
        b'uOSBbeF/mXXzU2XPpgqPoKPvvP9pwB3VPG7Ju89HFO/74Jbm0mnVdO3JH19eytn5wqe/ePXVz64vU5/+at7Nj0bn+d268sfRpLhXb706+orCK+dPqV9pPhn9Wcjrrb31'
        b'ZzSvnEzM13tU+p+OhGszCvZEiLwfTsH1PQyPrAKdKTanQP1iOQ3wYCO4GveQxin2SNaDzqpysL3GptdZVCjcyW2Hz7HJ0f2NYD/s8ULNLqqwnEOYDDq4cM9cd7At4SG2'
        b'WAOGVs1A5dj1MosKjOK2zPYCe73J+bUKcAg8l5QVJE4oFrMpPjjBFoPOPHJWAVyAV8BlUgA4ZNOvAeAKB3a2gN3kZGn9U+B8kv8CiQjuS6ZQAUPsDNAJTzAlHJ4DnkNP'
        b'h3JX2nQlnwpYzwF3YRfoeIjRSAUOTMPVxcytGUwzGlBUKtzNh5dDJfBi+kO8YzdnHXgBQ9SZnCjBCeEBeCgJJ6Q1PPVWHyU8RGoeDw9uQsmUYIdZ5by3XIxeC3o4cHcN'
        b'vEVaOSN3M37rk6Hm95pZ6lBwkws6ZfCwyPNbHFvH3MPEI+vkgOkkCzG2PzbrY7ZZsN6NisJHm3xM0eIurtGfNgkCuzK6NF2a3vzDT3U/ZRDEGwXxg1H3BUkjgqQPQmNG'
        b'YosNoSXG0JIRYYlpahLK6jeeJe/w1u6tBkGcURA3OOm++TQVyjLfEFpsDC0eERabokTnI85GGKLSjFFpKLMvk1lrzWb7phxDaK4xNHdEmGuamtgvGax/LyrnflSOISrP'
        b'GJXnLLPtO4sMofONofNHhPMfxGfhqsWYYlLwb5QpKppkjo4lNXY4z+XDbFzHu+fVeO+5eh128LEstQY7mLlTa6lH7W3H5iVWmz82W9xd9MhHOMsgxRz7+sJ89qvKjcVq'
        b'YOFN7d+d+50aFnjWI4962bfQjWN3wIRlIT4BhPg8Sa2xRhGOn1UpYo161Y3zeUjSxc1NJF2aNNOX7tOU0pZ6mXSGTVtZgiahdOT126jeGuMU8TaK9NyXZhpsLtfCryUg'
        b'2i4Tt6qUm0QXWKMcWWvDPw+sZ52VG3SEVd1h36UWMIUoCTlMisHsq7NAGclAyRToBMh/ArpdDHR+dfZ84uODGGTfkmkWGEWPZDT/NWg96izc3OPDGWrXlKssYIbMlmrk'
        b'VubwW4LVZAHLwh4+PlhTUBJ1N05AwIl2yVZ+K8DMuOdeZ2Y3Hx8uGnertbmesDRXtEt29V9pOO86Gz728WGMxl06jnoSK+p9AyPsAlTr6bGNyDnGNh9qs1gn+M8caXOw'
        b'WebiSJvK51c8DV42Px264OSbmcR2FHPO2nKcrf/KV9f2m+SXtuX2bs/woUr2u/sH/EnEJmwIuAL2tmA+xMJdgBNg0MphwFtwz0N8aBEcBM/DWza8jZnHWAHOMmwGuBTn'
        b'0lSAWx2eSurq2v1tCBUJIZxDIsVwDqUeVHAYovmZfTMMQYnGoMTB6sHqYaExrdAgnm0UzzYEzR7xn+1gE8AZzWRMAmA6yWDNAMYah7fHYcReS5nPgpV4/CeOgZF5p9sj'
        b'kbrom8sReY66mWdD5qwXX6NVy+XaUfe2Vo0Wy6Sj3AaFdtOoG5Nm0yh/vZSojLwakGTc2sKokjhaadMorxXNEeoGLxuE8bUgDK7+Ma5za48Is33MZ7Dd9X56tt4TY7re'
        b'X8/Re+jdGn0JxnshjPedgPHeBOO9HDDe2wGrvbZ6mzHeaZztqezPP+A5UQcVymQaJO9joVUmr8dzIPo2mHcl03Ky/+MxNEJEX0GUDVK6Wdckt9HBoPbWKOqV2GYmPlOH'
        b'1SkauVZCV6GpwaEcPBm34AVpRUtbqxqrjizZGqQqul6Os9IyhVreoFVuous34QwOhUjXSxVKKX4lEd/xnnaNBNdUgZcW0ARlLtKsAsFlOpSBitZpFKomApG1GDqRoELi'
        b'Y7RIkbm2zVgf6gi7Q/oErVTdhN4hs8z4OD+NF0s0WJ2gWafDrVuvljaslWs1ovzH19IxoyCfLrRjDugVZHvIE66y4Tfn0+Rc2YpvPF3mshRm0OXT1eSXXmHe6+wyvWVw'
        b'5tN4qQd1FdEerbDd6+wyLx7O+fQc5NIrqtRa1+mYAY+SMh7yjmS6pLpKnJGWnU2vwMs7LnMzs0Q+vaSwRlwyl15h3jPxRNIK27Nzrl8+PrlgHRnzQOOCbE9suMyOpiPU'
        b'mM1oaKDhqmlQK9q0Zj4B4yk2aUTGVqFS04rwVy5zqt5D6IRTY4KtJJZsSWdL6LmMjo8M0anVWmlLCz4Wr5rqUttHBgNCLARAm3loyRTElq4UNesGBWIM5BtRj5sHnGM5'
        b'+FPZqpUzw4QMfrm2uVWGZpImXQtCNASLdC0agGjQyFHrNMjpVsRkOS2HqRIeNER5qWGqqdDYgCShi9CkZpmQnJZiO+ywqhOhOrYU3KBEFWaMBGvkznOuNtsJbm0gkDOr'
        b'ydOatdo2TX5KyoYNGxgjhRKZPEWmUso3trakMKJFirStLUWBOn+jpFnbooxOsRSRkpaampGenpYyNy03NS0zMzUzNyMzLTUrJyNvxuq6b6FYDKjU0egpaA18WlMuKs0D'
        b'd8WSSnz0PQlcSKaomGpeM3gFdOswYa+FlzZl5M9CvjQqDR6CR4hyLnEej5hg7Q/TKre0t1E6bIYI7IDnwPmycnBstZmFWQj12BJlqXjRgkXiJYsSsCWLpVCPfxBnA46A'
        b'5z3gMfg03K0jJ/gPwOfQw3V4kOhp3OAeMcWDx9ne3FgdNooATknAaXhdAg+UlWC7H6hobOYSnAE9bCoSnOPCW4vBdqIehfvg8+DEzCZ4vQzur1gMu9pQPW0quQDqK1Hu'
        b'/WWL25BTVV4Kj3FRJrDDCw74pJNdiGDnE3CIV+QlEZWCO+C0J+VRyoan4WXYSw47ryqGXfB6Cbi4ARXAojighwW2+YC7xJJxaS244AX1KRK4F70wGVwohfuhHuzPZlH0'
        b'fB4XvAovEaup4AA4FA+vpyTCYSmLYhezsotUpH1/STEWcvvjn/KezG6hSPvIYD94IRde0vigRnuhhLzXfSV7/ix4gFgaLoQ7wQkc6eMjgYfhC+XwahI8Aq+AIxwqaBMH'
        b'DMFdATqs8QpHvOYZLwkqAbVfSfJ6+AyCkkNNhi9z/WD/VMXNHxlYGoASSmIDW0bKPMEsb/4DWcSWmfdOPfO9FRt39/eHia6Ues1rO8zRv3/l1qdHnouesu4Ps36U8z/x'
        b'IfebPmfzhnJ/95X3j04I760Q347Ip3/+pXZ44Pcpm68av/9X4VB8d+jDKV+vv//+SW3SXzqPf6BU/fQlXvrQ+wlDd6PXvvz2j19aF7OvL2DhJzX7AuKTSk+lL/y9bO7L'
        b'1R98UvT2zbj+X5/Zer24dmt1ovuOAXWJbt7Fzd0hD48c4C9Z0nH+wTsH1n++MjWK/Rrr/m/cju9I9XznIxGfKEBRXx2dYatHFcHjRJXaiJqy9yHus2JwI6Fsol5Rsopo'
        b'FpMyePDQ3BWMSnb3mlarKhVbobFoU939wDXGUOpV1RJbfh/z+mFLCLdfBS+RQkIQJm1PqhSXlFSUJWcgGA6IWFQgvMNNB7cCGNMwp+FAZfrUsuSEYgQH6mhwib0JdsKz'
        b'Iv9/xYiqU0UkduzMZ1pNVXhKZbI6hvtrF1iZ+/FAO71kuScVSvcG9vP6tQNbDCFZxpCsLr5JENKbYsQqvnSTJK2rqHemQZg0rn3MOfxk95MGQYxRENOvNcbn31xoiJ9x'
        b'XzBjRDCDaATn3GsyxFYYQiuNoZUjwkrTVFEXv2vDYT+TKBN5thr840wzZnfxR4LyDf4FpphEFLjJgNWFCci3/rCvSZRmSUfHIJ/usA+CCBvLyDUlSAbVw6xB9RA2u5pn'
        b'EMaaxBnDhcOzh2cP1aKQGQZhoikwZCRQ1Luyi2PyF3b7vucvuu8vGoweVBv8043+6e/55933z7sZZ/AvNPoXjli+NgLUJEaAwkw5s/H6PHaw3lB9ATvYxrcas+vqIexc'
        b'xs4VFyKXTY/hzlk9/qHHzfWob2JBzFlfibAsBikbjaVZaenx3Sst/+3KTCyEXfQopKjXKN9CX47IY9RbhnfJm7ncUR9GdrE88qUt5Bdbe5SPepj3JzXIR70wp4n4e7x7'
        b'mekHaxc0WDdzoI+/hYzinjzm5kzQ6yGWvZFQh9f7WcQwu4d+EhL6sOF2YsK/0Z+Iep5ORD0vIup5Ooh6Xg7inOdWL7Oo5zTO1l7P54fcHi3qSa0bk2jGPO5jCDTz8DlE'
        b'JjWNuCqEX0hWQZyi1PaCBMxNJtNN6lZdG4pFQpTUkUtpbalXqKQWvjURsbSJhOFi+C2sjbMevMAAWvVKDiVhPdP/k03/L8umtkM3H3cUE2LVY3+DjGo31pn8TJClAKeM'
        b'+opvOBHh8nXMXMK8xzx9mMMYWUfVitWhaiLNqJzLKBtasTChaJEqXUhDKx5xJgTJmM5PhbiEGM96DLz1ra1rMbw4REJXmLFLSp7p1vo1qOPpVueCFUIQJBvnZqemmdXQ'
        b'GBGQYI+LWzF+XsQlENZJN59erNFJlUoyMhDirG9VNFhH4wqb4yaPVA+YJ237biBn4FfYHkn5RgEeZ58gxNsdfPhfIIPPlm+QN5m3rf4/Ofx/gRyekZ2anpubmpGRmZGV'
        b'kZ2dleZUDsefRwvnfMpROKeZXT/J67mUe3gbl5q1urwraiGly8RizElwe3pZyfT2CrgvucQirCx0Jlw/Be56ZMKr4CaRVldKdONyNRGq4dBT3lOW6nJxqbvhEHy6TFJa'
        b'geQVUiq8DZ53WTLohJ0e4DxrkW42ypwPO8CLmqqKKrMlTvwGOFixFElceiQc6ZGE7YkkUlyoHr5cvRL0gRPgWQ8KXIJPe1WCy2A/2bMMXpkBntaUwgMlFVVl2IhnKhc8'
        b'PZ8Kns2B++fmMBfuwLNgSJNYAQ8m4B0fSHzdCbvB5QQWFdnE4yHhWIclK60WnveCL0V6gIOL3OEBcSWSvtlUQAYHnJmiZNQIw/D8GtQa4/uQSmJAb3IJeGERvk0kDXTy'
        b'NsasIa8EXeBaOoLqNrhDICtJFuF7SYTwWQ68DS+C26SrgrdyKO7GZ7iIJfdW10kocgVJMjwKhrxQv4LrK2qomjVwhw7bjoMdzQu8cDOhVjoMXyouR1WGR+ELWBvRCS6h'
        b'J3CrvRweLMYC+coQ9/nwGbCbXJgCzm5OgdeRpyW8hCqJnEbegmKP1GcgjwLsS0Ogv5JAlDaJYQJy5wroDkyhUsCJFuUX//jHP3w3IZSa9Vts+F65cz6X2WZV+SSf8l4w'
        b'mUXRq8tH/DZRpFPjweAC3DgHzEqc4uQlqPcOpJQuxrjQD58phvurE0QIK4qttzCJwIuk/fgqnycqIsl1LvgeEHE1PJZRyqF0cBcLDlFwaK2KKIvmei72MnfPIgZXwK2F'
        b'GF3cnbQOuAKPcCnQsdhj+SJ4TYcFKXgEnG8Y14QsTIDHqt0ZvUcN6GZUHxxq5mS+LzgBnyZaGXAWvWSPplRcVZGiI7uGKkuSieZDBHt54IY3uEEGy6yykqTSijWr0egq'
        b'FfEpL/AqG14HV0vJrUFHvCrZr/OpjcMlLa2fLVstCGc2psFX4TEKXjdru5gNcwi54N6UqoqFCcQoXqloCRiMt92Odwqc94Zd4DB4lVy7A68miJIkJcmJLIoPDrFFdSnw'
        b'Gtyjw5IguAgH2GULwXWiC2CrWbnwRoqIw7Tyfni21CYffBa8mpIRRW7fAbfBqxFlbq3WbLPSiSopEA2/Q6iS0Xy7SsLzcEgBnjZwNFuQsHh+MffyorJKmOr/ec7en9Sd'
        b'CCwVKXOL3l1Bq1LPLkqKEiYGHrsubfovvU/nlVu/OlLel39g58+kIsPJT0/+Muwp2eldk6Lfvrc/5/VT0dG/PZl3aSh4y1fqoxGiX4zs+XB575nXZv3ti1/u8wz6e2X2'
        b'BY/Uo39+VvVJWNaFuHtL9SfX/HBmjSDOY0nZ8Imhi8e9F8oM7gvvXNRofjCvTv3xxabuH25p2RfxZUfR3//+y2MLU7ye95PHfzy245RoqHdUUv+Hlj8mTnpoKBi8UxWw'
        b'x/f9vqunf0UXP7j3RtMxYXpFXcnVIeNPH9I7Fx6P5P1mk+a9l3+48+OqTJ+3b4b15S2buePC3qc+e9Kr6ZXhi+Veiuean6gta/l1Y9yeJb9O/vkZ9RcDZ43edaVrjh9t'
        b'8ry+/kbjoTu/PdGw8uMnB9+Z8/5Pv5r2lGhIzb7ytVH2ygu1wmc/GDr3Q11d9erfsAM/TFZ9+MIv//zVj399MvD8khU/3fqjH47pLmZtfz9llaf4q1eS9vzyj2eq2PM3'
        b'NPZz35i+8I+Rdzy2fsZqEfmQK33ALXhiLlFcgb4K2z2AjZykh3g2E4I+eMmit4J6cMh+TxzRXC2KI2VFwLuxXmXB4O7EfYDuxTKic/KMLyyTiBMb/C279/yWcJTwJbCD'
        b'MevdEQO3JSWaN+95LA8Cd9jgXOV65raK42AoPUmCiUQyRsODbITdt8SbYfdDgoc74asryhJV5Yl8iv0EKweeqX2I8XqdWwu4VF6RzKZgXxa3jAWugWeCmAIHwDNLsQ1y'
        b'8549/pNscL40HhxrJKvl+RVoppywtw90gruW/X0+K+EpotYD5wpYDovqs9FMZF5U74YvEqWdCBxM0sBt7nh4ivEsRxp6EuzigOGUJxgLsxdT4FFbhRx8Htxmb0K/p0ST'
        b'v2ulnGttHW43wkps2+ZMZeeLNT7jgn17kJ0qaDyCqO5eZDOqu61eVGhMb2j/vMHMoemGkDxjSB5W3Vm0dNMMQQnGoASDQGQUiAbnGpNn3osyJM+5L5gzIphD9HSF98oN'
        b'sQsMoQuNoQtHhAtNUyVmPZ21jOmGIJExSGQQJBoFiYM1RvGse2kG8dz7grkjgrmkjNn3njDELjKEVhtDq0eE1aZpJVixl2vwzzMlYC3eFoN/rI3eLz5pYAvyP2nwjzEJ'
        b'pnTl98r65xgECUZBArY+nWIKS+idPig0hEmMYRJiaxoHz2MxuxRvRqM/2cuiOyJDrM3lRfFJ1hJDeguP5Hflm3Lyu4pGwjIMwswRYeaD8SfTFLq3uj/w+Iq+Fe9NSbk/'
        b'JWWYY5iSaZyS2eWJKt2bOCKIQd9BAfqrfU88/b54+s0GZpfFvXSjuMggmm8UzX8j6r6obERURoAqf6PdELvcEFprDK0dEdZ+kFtwc/7N+feK3ljyWpVhWo1xWo0hd7Ex'
        b'dzFulUyDfxZRZLImTTNlFWCg0gzC9AdRsQMhXb4mQVB3fj/XSKfdF6SNCNJMsRnDUkNsTlelKSgUm9uOkAxzb3jcnDESWNrFweDGGEMTGVP6poipxgjJoMYYkdE1HyXH'
        b'Str+PGOY2BAkMQZJhmPvB+WMBOV8EBE/klBuiKgwRlSMBFc8CArrbepvQjnvE2vepqSUXrd+N0NwwkhwgilkSr/bIG/A936IZCREYhKJURzvuO8XDxKSh2vu1Y9ElKAv'
        b'eltyRtdcozCmv9ogFJn8g3o9jP5TzTrXOIN/mtE/bcTytdGxChgd68vYuYWd29jBR+3Ud7HzCmXRsT6menXiiMOvmqhstepb30GOy0FWi3WuP6bsdK5ouK3zZLEURCX6'
        b'n3W/U/XrJY9CFvUay7fQj9NgscWBP9ZLEI9Q9qrSHkrvpvfQc8k1iGy9N7l0ykfPMl+GyGNTeyccfdrCJ2pRnoNalO+g+uRt5ZvVok7jXO/5ciaD+TIy2Bs85krK1KLf'
        b'K+aIyqkaEvrhMmbtMzXwPWp+iy/FMGE9sDMEPA8OacAB93UciuPLym0C+3R43zFib2+DW9XgQA08sLhiIXxhAXxhsU926lMlqRQ1JYgDtoOOlUR4iQXPIGGsFz5dDQ/U'
        b'ZKXCfZmpiGVfx4L9hfB5wpvOjF1gKYhFFUTzElmIvb0AXiTSAHhh4bIicNF89eE02CMmq4xtcHgj6HkKPgvPoek+jgqG59qZO1LP54DrZZLUzPQsRIDP1fO3shAA+xgW'
        b'cVUdeNFyV2AqfMZyVyDcB15SPNi1kKOJQrhdLlx9qvq2CqZ6D8SUbf3+oatztv1X3Ze8P/38QDEVVLz94PaHLPYtmfut9r8eOZ38k5/u+11pxJpt/pV3og9d00pmvtbI'
        b'2fXK4V//uovl++KNydcKXmr6yWFBR9UXd69XvNO3Y5I6Dx4OW9ec9VbIrt97p87WrPhb/ejm/7mQlDVnXfKVfdNXq+tfL4nzjXpnccqzIZPfHnjJ++3lzcHXRo73h//w'
        b'f75X8eBZAZzX9c6TP73+Z69X/RLf/v1nf/5i4f9cLt3/1z03Nr6/6oUX924sf296/pavZ9790ytTFq+a9+XMV5M+WzLvrYqvnpz9KTfuZzsP1/rq3ojc9Ms/yN6OZv1g'
        b'Z2/g9TMef0pRzQm7cvuT+kvzN76cs+Z7ikvvth845PYWfObhr6/4PNF2ll32j8kz5rzy3+z7f2uJe+vPogBy8AEcA/picqWoG8UGZ1lz4dnF4aCT8EDw1gx4KGydmQ8i'
        b'TFD5BpJrNku2CXEidkxQfNRcwvfVwB2IRbLhgMBJJCXZnHDwQe/cTvg+JBMdT1YtcjhG0gh2hhNeq2mVXLmprDIZyXKHUsBFLuULXuHUIWZyGwEwcVr9Kg/YWUauhORG'
        b'sJAcdVfLcKddgfDZ8SvK4E5wmEN5J3PclsMdhGWKWQv74M2nzLdKjt8pmQyfZ06vdILTKsTJdZSV251eCQSXuWFg4ElyQKMFDsObZeaTKeBWtuVwSsAaDhjKqn+Ix1gZ'
        b'OFUIbjku4I4zwfDsVMLozRaVwhPwZWzO3+aUiV8EZxU8AweYayz3gUPTwU63MpuDLJgVzgfPEz5ZiOSwI1ZGENzmkMXZQNBBeo0FL3HL55NbMMdvwPRKJTl5YDt3/I4C'
        b'+Dy8S2788I8n/RC8EewvQ2XCg1UlPCS8wyvuoIvdGgiOiwL+jQwlnjrM2ikHbtKtjrk+0XZrJxNC+Md3zfzjMh8qKLJHeUR5WNWtwhwF5sea+qV9awYTDYIsoyAL314Z'
        b'aQqj+/IRLxYe1VfWNc8UGtE1p2vOg7CIvlwcGNlXYg40CYJ7M41hyfcFySOCZFNYZH/UcZRkjE2HBpiEoWMc9PtAGNxdMcZDvjE+NTm8t7C71CiMH3PDAe7mgO6qMQ/8'
        b'7GlNEDfmhQO8qcnBXXN6Oae9T3iPxGYbgnOMwTkGYa5RmDvmgxP4UpNDxvywzx/7JmFfAPYJsE+IfZOxLxD50FuCsD8Y+yvHQrA/lHmBZ78Ms8vTR2JnGIJnGIQzjcKZ'
        b'Y2E4QThKjOGdgh8iUOoRYV7vnN45/Txy4+ZGA51rpHMN4XnG8LyxSJyIJolySCLOee+z3oPLmGs5DeE5xvCcsSicaCpKNBaNfTEYmoqxWOyPw9CU9BaOxeOnBMuTCD8l'
        b'Wp6S8FMyeYmod25fxZgYB0hwVVOwLxX70rAvHfsysC8T+7KwLxv7crAvF/vysC8f+wqwbxr2Tce+Gdg3E/so5HTxx2azqJCwLt4D/8k93ke8e5/ofWIw2zAl3Tgl3eCf'
        b'YfTPGPHPsMRVn152Yll/06B0YI0xLscwJdc4BUsHRv+8Ef+8BxGxmBuWEKeryCQM6Sk/Ut4vQH9LzoQNhBmEYqNQPEK+pqApPZuPbO7PYmSS94JS7welDgffzDMEzTMG'
        b'zRvxn2fDXvoy7OVlMhyYhU/NKE+jlaq1oxw0FP45XtLXwktOYCN/S9nvn2YG2WXMP/ZZ+Ud8HY0Pi5WMubl/3fnONlxjvdgZjxzqJd9CHud/3S7/ZhH7y9856OEZox5a'
        b'y+l383qm0rzMoJZrdWoViWuhpXi53GbV4rGWmum18k0aVE6bWq7B54aY5RDz+o7GusZtXhtxtkQ8cflbySwqYXDqNyHAv2Hjn7tTvpZcnTULDMJLoBM+DQ6BveAqPAIH'
        b'YQ+4thRcA1fBpYVAz6OCwTbOZnBzPaNFvLkMnIRHefC8gqIklKQF9OjwyQZ4BtzYSBhe0LlUDJ8uywavSCQcRB/3csAFsAscIgyzdjVho9tep1YruXJP5rIQmaTOnNON'
        b'4voiXuUcC/TAq5NGWXWEoWaB0yyrUvM0PAoOsVPgsD9jIPAA4gNeHOeDERecsxmcSITPMbvqTmvhHkRHJ8WYlZ5l8BXyTvhSI7yNWOvFs8DzFfgOxgOscLADnCK5FmxS'
        b'w6NlEjAMO1AVOIWszQtnKar6DnM0WKb0eHjr2OHp+LxwUVP639d9zl01T3x3++X1O4eXjL45cH25f8FV/6jdAz8rOzE52yuga0rwkfKNkYd+eyViwc6O70/pf37bgsHe'
        b'W2+fz/okcAXvgeHS9/mLpwYv9ygqDf88o6p8dtP7fwoNGnzdY98+0dW3L7BnX7qxqueH1YceTts6/YWcs8vf+ezA/OyGt06/scT7dlTUEknv1IK9P7z0ve1lNZ/3nPh6'
        b'0bTNy6su/vfxT+ibPwh9/c6ne/5eUckOG5REbruWOvPsWhGf4bSGo5F4YrMrrbzOegYFPI3YMTyLyZ6YY74DiU/xp+WsYkfDl5eTmFmoB7YlSUCXpIKNGm6QVQaHNzNb'
        b'687BVxEWdaZgTqlEzKa84BA4J2fDfnAM7jUf7a2h7XRw4GyEzfnZnJkMm9oBr4TZcIpwt5BhFsHJZpH7Y3Mz7lZuxsrDSDV1ePjaTK/mEMLDTDZvX1vkRwgR4iZiRQOV'
        b'78Xk3o/JNcTkG2Py8WXYhSzGPVyOyHqQKTLq9PoT60fism9yblYbIguNkYVdxabIZES4I3OQLy7xvPKscjjjppshbpYxblbXvN6Ew1VdVaR0Y0zmezH592PyDTHTjDHT'
        b'MGs0h8W45uJDp/RK++IIdxQcepp/gj8SmTIsGG4wBOcbg/NHyNcUHNnvZgxOeC847X5w2nCCIbjAGFwwElyAI3h9vu8Fp9wPThnmM8zNCPmOuXHpwC5sVCg+o182gAAc'
        b'iZuNvjfjmV8LmA+Cwru8v9U5oM/s6Zi5oX9rdw5ont9/5Dqoc+h9F1ij3DapttnulkSryL8DUyWe+ZZEbPvGTe9O7sjlW29KnKBN+PfclPgrDsvJRq1xEoWphUa6HvuU'
        b'Slti9fhGWnAj5NMljXQi9iXSiL3QMFsCMBmSb8T2tPAKeaKkXdGWmExeZKaHaucL7Bp8X4HMuqwvVTc0K9bLJXQV3oWwQaGRW2keKYNUgCSX0o2tSsTcfAMBc3NCwNwZ'
        b'AgZuwKHYpOLNoAfNZAuKkQRXWlEOLtQUg8tQnyxBolUx3OPWhpKd1OFru+DeBnC0DE0rL4IbyaUVErgXibk1UI/k8YVIiBMnYBuzZfBFN/C0fxUhMRJEFPVozrtEFjs4'
        b'YH+ikoVIxTYwrPND0RxJVdJ60I1A3EhtFBYQAlKMZPCrSVVsirWIgrt94Ilm2KtoSmtgafCY+OK1v5xaWOALUr1fOPpw/t/Ly4df4wXfZOWs3lY6LJ/l7b2NO+fW8Lz6'
        b'eUPHb/32SPBA4Lm5a3Y/6/3i6Zl/+fukGYU/2JzwNr2xPP7hat73Wo4V+P74tZwkw9u/GPnojRW6vo9N+pmN10//bIpg2w88v3zxr+qP14LGvr1PBv9wbYE45A8L4hf9'
        b'oZ9+5cVf9z3LFuS8s/ze+hvSXU15S5sD6nbX7wvadXVoP/3zH+z6c+bf5ncNa1NOfXnx4zWn92h7VGExs9c+d+mI6EJgXsHnXx0Vajb96N7nH3Z5xZb/cunljVuq/r5J'
        b'F+v3EbexLSBo/e9CVvpHPZsgurM1qeeTVYG/LH7/3ddEfox+o8OtIqk4GQvi3PzqHBa40gZfIitKy2OexEJ/djkWxsntlJ3sLXCQIkL4U3BfFbwOb2wwL1R5+JaA82zw'
        b'bAq8SjIvgLfxDefJItBfiSgam+JXssPh3jZCS/wyWKjMvcmSEhLlBfqL4TAb3gFD4BkialfCTnC7LBkcrGKuFvWCxwpmsWHvmjZmresk6GnAJSyC51OqsLGLrezEReAW'
        b'Q6iugx0NZfByMCJ4Igk8RKrml8ppgteWM7kvLkYktTNZJjKTUkRIwR5UaawCmDsPXExqoVLwDg6xRMRGNO40B+xWi4nyAO6Gp5LLEJ2cgXC0koeoMDvIHR5kbjC8TYvK'
        b'MIaDjqUEyT2EbHAmGR5mNozfwps0OhFn9Cq4a26R2exgzhQG5ttwO9hro5QA18EtrJhYBzqYwm/BbeDVpBQZuIghQ28Gg+xkxJWJvL6tXsGLsluoYogxF08D7T5WAoEf'
        b'CRm+ZibDpf6UMLA7p2fGkRn9MYwpCyzS5X0QGjUy1ca6hGAySjT9yPR+IWNIgiQaTH8+/2L+sMyQVGBMKnCaLzgcC/3Hfft8u3gmQVBP/pH8w9O6p70nSLgvSBgMNAhS'
        b'jYLUMcpzUpIpNKo3vj9mkDO40hCabwzN75pjiks6v/bs2jMtAy2o8MlpxDnu2cvtlZmCw3DB/TWDmYbgVGNw6gj5moRBPSVHSg6XdZd1kb8HYVP6ck7PODFjMMYQlmIM'
        b'S8FlxJsQmXc/4d4vxID1+tq9hz05iTjm90yJ6q3pnzoQfz75bPKgdrjGMDXfODX/5lzDlELjlEJUWkjSvUWm8IjTxSeK+2uOV/ZV9laOcVAoiSLOp9h5SNmFOXOQyOk0'
        b'eIxjgYkoj74XE1jE532fzy3y9Pi+Dwu5DNfgwXANn7tgHSbiCxYjrXIxw024s/D1rHbI8g/MSmyjLNezbvZ7vOtZ/033jh/3SKGe953OEZkN2+HLL22sxSGCZf6IeMwP'
        b'G/0LJphkx8e3Za0NdXXE2Mioe5u6tU2u1m56HHMm+OAx2fNPFqKIGoHwYKTpRML/yIo0pn4TF6PH+1CGnHarycDf4AzlHDsLmGNcto8/QifkuFO+k/VL+zmDmnsFI8tX'
        b'miKiBvNGZq9C+Ou7moXQFrkPiftgXpFp4aIxTjS+CPNRzqe88UxjXBxayqJCp/YGm/zFI/5ikzB7jMcOzf2UQs5D7OhLEZMeEtXrbvLHt6OahFkoQUgOShCS8xA7+hKU'
        b'ICKud5mJrESahDNRgohCBB52HxJXX4nSBNNdG03+SSP+SSZhCkoTnIaSBKc9xA6x9mmbIA8nKMAJCnCCApIgKLKr2eSfOOKfyCQIwgmCcIKgAv18lCAsujfB5C8Z8Zcw'
        b'YIQRMMIIGMjVl425s3ywcPFIl09avbe6XzOccU/wRoZpCj0ouBl9L+MNGW75GtLyNaQRa1gPFi42LVs5xhH7zEb5H9fF3WApYYxLwlexmM6OHq6+F/uG271IU1hEr7Y3'
        b'cZiDYKgeWbJ8RCrHr28ir28imZswsHX4PAmniuWTPkZ9exdDZC2US8Lr2Vk+RQjgf9lVsUJ8poxRrpxspr2jR3wiDD4RRp+IMXagD5pQv9H5lEP5RjqmH787AbwKj4EX'
        b'NeBKWAliLzS+vhzKZwobnglaQ458rt4Az3qBQS1muLzw1r0FC5aDXYhFCU/nRoMXwpxfJk/unWZZL5O3qO/+MxfJP5aRDrdKoqjKBHdAH75ddwa8FEVFgZ1gP6MwOoZY'
        b'xfNYuZPaBs5noTLgi6x1iCXbQaJD2KstK528UPi8eaUT9IPdOsw7tdCgA3aWJGO1RAaSKa5yKXfQyS4Fu+HLitknj3I1T+Cq9/wO2wY5c3Qdi5M97K1fCjc9sV+03yv4'
        b'6gXOx01Th54KWfCXNTe/lhT1SxqVtxb1LurtYb294u1dZ4+KnuZdqg30rg7ZdzM/pDo4P6T2eExIV4V744O3KKr868k/WxRovk4ecW87oT4Jb8ECu+CAxYbaWtjBbFC6'
        b'UQ7wwtY+Gl6zWXuCx2EfE39tLhhgNmmBPviMeaOWGPTCncS+W2BKgGX5acNKxI7jxaegIOZ+7IPg0NIyjDFVJeBaGIp8gi0Phl0uLZJ4t6nlSPKU1+FN+O12T4Tdw5Zp'
        b'MP2eNYkSBluYMP3cB4LAntwjub1zT5eeKD1e3lfO7DnSz8WsWsGRgt4Ngx4GQbpRkD4etJHZ9YMC/CbjCS3WFBTWO793Se/87i1dXJRKX2aryhjlYiBG+YztpQmMCaPO'
        b'wEwIQ7wEmAGxgz4Kga9RUhb+4yl/FisU8xVOne/0amu7UeBv/v3sAbbc7GVjuTkd2xpBQ5S9ywPbcJZzZZxdFLHdbG/XmEfi+CjOzSGOT+LcUZyHQ5wbifNEcV4Oce4k'
        b'jrH3PDHOg8T5ojg/hzhPBLMbgtl/l3utlyxDz2pkyQIQ/N7mcAG2vSzLJOGTUbgv9uv5eg+9ZyNXFohC/GRZKISL0gZja8fdnt3sbk4jp5vbzcN/MmEjG4XhX471lwll'
        b'XC6TwsblTvTLQvr8FJQstJt3lCUL6/ZEbrilLOSfwqRFvgirL9Lqo2VRyJ1qfY62+mKsvlirL87qi7f6Eqw+kdWXaPUlWXy2dZAl97HPsWTiPja2+SwPkE+SSUKsKNQv'
        b'oJx87CdjewvR5jJS/pUyCDRCs1lkxiaOZ6ObLBX18GRi39qN9CpPloZCAmVCYlgre9SjDnGQ0iKFUk5MhNrtOLLq8/QUs8pks+MIG2DmondQerZZq4f3Gbn92/cZNU0k'
        b'WxzKkWx5MvuMDq/lUkp6Et6Yn/xh9FPMxvx3t+ynnizMYlMLVku26vhM4M7kLawHwr/yqFRp2FXJVopshc/zcsf03HqcwXavKzwKj5QhWtDpRlU3ufvDZ9WknA9aoqmf'
        b'U53It7p+91Q+9aEFSjJRKuTaSJYGK0fLQnacfDMbEbWrR2OfYfF7g/OPFyzvYYxe7WX9LmThb0MW/O42IlmLgq+/9kl9BH1SdJL3uiSAd+349eOvKb8OWHIz1luUPBiX'
        b'mZafs36HUrrn/Te6QRcYfTPG4z1Wt3z7H/mfLlu4UdkWEdb1A98Pr57f+eQPti8Ie+vecRb1o4HwZ9UrRR6ENK2EPR6gswozNRxEmE7JatjauR5EZSIJgC+ATvA82T6T'
        b'n8OPZ0+CR8Ewc1hfvzSWOay/ar3djmd4Exwl+4OfgF0hE/cHM+2VBnbEhvCafdYz5rl2wT3YPBemq0kJoAd2i5m0KGVQOHca3slCdqssTgR3GUjBAbIveX9ZMt5IfJID'
        b'zsCBCLIgsga+CHrGE1WAIXAWnqRQqmMcbCO3hFD7wOpZoDMF7k0pgftZlHsQvA73sREcOyseYoNeaTJwHHRuQGUQdq4EG5OoQhzC3ip4UMKnouFQXhkfPD0NDov43yDA'
        b'YZR0sEIaYB1x9mZIsf08TPlWTqIiY7q43V7MTljh8eV9y9Gj55gnRUf3avqnGSJTjZGpXd4mQWR/1H1B9IggetB7WH0/IW8kIe+m8o2G+zMWjsxYSPa+FhhCpxlDp40I'
        b'p5li07CJz6mmqUmDcwYXDc4ZkBCDpVGxxACo+SeCJm+OiunnYUuoXejPhsYziodRHjnhNcrFB4RHvcd3ZapaRz0Uqjadllz44WxRg1FFmFfpH90mKZgf2EnZLNGvmMRi'
        b'5WLy/9jOd7oS3+eRTl3zLaT+GRufZlOPvDrcVK5sAtpU3mIUsJBta7iwdpvZJmD4+I0XDlYAJeq9KMk/D5tPnW0H/hMwzmXb2cxMsQAZYQOko1VPyT9vWNGzzopU/wR4'
        b'8xF46gOWqffLKSWWMixna78lUFbrnXgQ1LUoXJqjdAJTKYZp3E5mIFbe0I3q1pZvC0yzPTDSjf8EMBX2wAgJMPjM9r8ECr9O26qVKv8JOBbY4foKCxqF1OByLAfAXQL1'
        b'v2EnzGPxJDyGJxmRIumRNuFDjeXZa4UM+zHsxqe86Zk8fFgQJiVTira/p3I12Sjm3JvPM9JvWicr9Ev+ouDYX31S/5zw+6v5cXsqhZN/FBwSvCQDvJuxmPXD1fwfa6l5'
        b'Wvc5t8Qi1kMRylwyB1x9BCVLWkwIGdipcyVtMtYnJ9lOzuPGL9Mohl7JAqjg8O4t/QuNQWRFYYopLLw3jTnhkNlnPp4yWGgIwmrBb28D0xGKarbt4ndDwH9s8fujf6DP'
        b'/1WVjhkPpxfwiKw7q2hXg2lj4XKyge7Fw2cbTv+VFMwyqBUXfvEDNsHCWs8ujIV/fouxzpofEvOrT3j7vZfN8mzw/El6HH/Pu+Vt0xO+bJm1JnhHSG4GtW+ee9MvvhKx'
        b'HyagzBtncx2QMBJ2jeMhwUJFJNGHxIsUeHkwUSxhUfBVdz7Ywc4AfWDIpT7Er46c8Ve0y+vqla0Na9tDbPDEPopgbYoZa9sCqITkgS3Di43xBe/FF96PL7wXfW+DIb7K'
        b'GF+FOZ9eucE/ZoR8HXB2lEeOsX+DimMOVnG4hmaZvb6jBaEvPnbk3Plu9R0T50/M7X/2JGWR8XqY25CoRs5/EHcd5lBn2xTMN3d4efwX6xMOFem3YPVTHesDKXKOW5Oy'
        b'BlziUsunU+1UO+zaRBSX8BjYuQFcYlNicJnaTG3ebD46khK81U60KwE3wCvJJTUJlWIWlQn28n3V8BI53F2j4lLuVK4nliGH5yF5EnM8G2urLIeVvXtUv5DXUjo8TBrY'
        b'tOUODbsDy2ZMJ9dneOdabs84A497whNlLYySmWz737UMbhfAO1alqFkhCl8GNxVdZ2mWBi9IPfVhz8k3pyGSYNgd9V9F4jk+c9Ia/JIEc+KrfWB6ERqLs7xZov0/S6Zv'
        b'Lbu1R8riZHeBXRefXXZjT9TuvJMhr0t+nSItWvTDHRev7Z0ka4jXBApW8i7FrMy6WKtUXZqtrjvs93py5nvX5RmFH7x28Le+67UbtOkpq1/7/UvyWXdCf9wgm7X+j+wl'
        b'Q2de274m++Izwp96PucZ9/919x0AUR7p3+82OkhZZKUuSFvYpYuIiPTepNiVusAqTRaw94ZgQUFdFHUxqKuiYg12MmNyxrRdsjkJiYmXy8XkSoKJKXfJXb6ZeXdhacbc'
        b'5f7f//tknd33nXnnfWbmmZlnnpnn92xx2pj/YNt73LSgY18H+LkGegS+T70/Y2oWHgxkzHepJd4+i8JKBfpk6RgGZXBzsu4WP2yBL5FtflkSjfO2A14Eu2NB82jPGgYC'
        b'0TN8UAWeXQs60KgCr8DL401vZFgpdCdmDCjLCz5ozXjH2EuzGB3M1glcZsMLQA6PkdUf3Aw2eRP7j+lwM16HIgYBnUlglzZnPcoPnNGzN84g2/vFJfGgGZwaASe3BzTR'
        b'y2SMPH0eboAnh8wPiPYXtoJbAvaYa0bcIQe9JCBxanm1pEa8ylxnHCF3yGDG1HqusKQcnPHe+kwSNMX02Tnh7W/nPh5fMxHvXdmyUh64b33TekXNhbVn1nZnqXwj1b6R'
        b'Tet7iu4XgqU9Sx85eioF01WOYWrHMCUvbHACV1iq7YRo9lbbiLpY6C/mouEVQ5XNtO7oXpuZSpuZeHcpUFbTOq1tmoLTaydS2okeufgofdNULulql3SlfXofz/4hT9jL'
        b'E6p4Pmqej5Lng+60mdL3FFkqnr+a56/k+fdh0wO5i5Lrhj5qrpuCe8HujF3XXJUgXC0IV3HD6RgVCQestcXVGZ/16PGZnV9dIh1TstDTjtGaQToND9KjKnchHpuXDY7N'
        b'tZb/s5vfBwyFVKdZKCutkD3WZE5O1zG02jiii8MjNrOYTcZr9hin6zhkvGaPGq85o8Zk9jqOZrweM258WWMsQFT9NAKbARvXzQIYN8MpBeynnBZQRNVITOvWgn3wgDdq'
        b'hFqDcqoWXoLH6aPGbaAJXsPjObVqEdxErXKD5yVtn+zmSCNQ7J6bfz78IECzJdQE+l7/8PWuna0b86cEpnQ2Xm92jbouE2wVyJy3Xm+WBGe8WvYa98B14SsmbSKq4TMT'
        b'y9B7SDzG2iJ4yq4ENPoCGbyWCM55AtS7iQURg7IrZYP6jBXP6aEbdHoowdIZxkTkDumhmFzMQhlW1CSHhzzPXp6nYmKXdbeeijdTzZvZxOmzscdCs2OfnYMsYICFfj2e'
        b'7C4PVHDwHzYpNvfR4W/9IZuJajzjVONDtiPlEH2KVrIMSiLZI5mc0CfBTL6C0ihYMGChFYOBj/v8UvCbCSOGiK5hLD445xOFM1uHxfURk2NlsyFhdP3/QUYvfTGhmmZp'
        b'LuF2NH11gWZUuKWwyYFygMeTJB6vnKIdlC5LNjn8IBzx7rmNgqcxW/1lG3e0W93/smjea/d6umzrneUyO8+3e1+/ttPC84GB1d8KWA0BjJzA42e+LPhL0ZG3+l4PPuy/'
        b'VeIjRdOlLTVvjgX/9AdazniBAyX61OCBEpp5jcnWm4aDrXU4ZOg2YeMsDRsvtKK4k5pmEGbts3FuWiV3U1jRcwPmYo8+eydsatWa1JbUFNvHc5WZyHMUcSpeoJoXiHjd'
        b'zVOepXDDf0obP6W5nw5nG70AZ48sjtEQow+qWOdgXh+7JJWY4bfrMPyCF2T4/xb/eyJav8DHeIZ1gsGBdAulu+tCxnl9zUjP+b/ZAcaSzLUdAK/hckAz7MwSzYb7AxNY'
        b'YBeX4ugzwCYjW8kH7zCZUozqc82p9PCDUN5J1A1ObBSgTuC89XTz9S17GWYyXuik6fMOMGJnw9jpk87MncTLeLVXdqaPRy8sP203erf9NTR+E/OZvdnhyWC/jRb8pBwq'
        b'0AJtXObnaJlfg+eRq/FEqeF+ng7PDIshHWCKpgOUDesATvLAcyxFrCK2y+10SmdKd7BKGKnyjFJ7RildolU20UrzaB0WNxjB4v16xfmFNZXVYwoqBjq8TXP2QszZ41K5'
        b'HDP3Wh3mXvprmPs3AzDAZB8y9KO6zMJZggk0WASBjSAAEhhKot90SN+8VLyy37SusrawVFxNSuE//DKg37gQeywQV9SIq/11LwL6DYokUtrVAMah6OfU5ddg37Ti2pr8'
        b'FcTvKT7V128iXlFYmo+9cuJbJ0lKbCnm32+kdRUgKdLBDT5FUtRIasrEqL3wUcNqrOWsxmqmsXzmpvUbFORXLMVZ9hvjX1pkXHKb+EEh7wuoLmLgA4kYULGgcgXBJ+7n'
        b'VJVWVoj7WcX5K/o54vJ8SZmA2c+WoCf7WQWSQnShHxkdnZ6Tlt3Pjk7PjK2uwWNiLWPEEh7XOT6G8s02SgsMcZAiW8DY7ALPmFS9UbHB/+BiftSQYTfGkFFIL+b5C9cw'
        b'fqjYyaL88qdnhLrTQwjcCC4XSeEG0AGvTajmUEx4kuFlCGUEQcEcnAVbpDV1KApeNWZQ+vBiJDzENIOH9GunofjVqfCcNzYvP+eZkOqTmDoL1qeBc0K4xzdpVoIwyRct'
        b'zdEiUIOrBjuXU7B5gUl0PjhPo4XtB/VIJGyehX6vokA93JIKr2ZppFJ4CdwIxOARDA/hEgo029kSARccBRcCA5kYj2B9IBXI9SQ5Abk/uIRSMymG53q4gQIt4Dy4SIow'
        b'CWzBtvmazVEGZZwAmucz4XlTeJAmQgb3zkKP6lEMAXpsK8q4Gh6oxSvOSnA0nJFNwwZMYVMceJEBm2E7OEpqc4qJN5Wd9x6TMs8rWL9cSEskPLDHEmXGoBhesfAyBQ7A'
        b'BhE5tmYEboIjyT4iHwxBmIpe2iiCDSkMygZ0sCMyoYJk6TODT0WElehRVXlh1UmLaLndG252QlmyKIaQkU4BWXYtrcE4APenemOE/kR6tTtBAmVgF6sAytkkszojG0oY'
        b'8i/sfdR+x/wsmj4WuBKFMtOnGCJ4F9ylQGtlFGEDAWiHLyW7o7XAbiE2JWELGeAGbC4jWa03mEmtqbJnU355llcNHWi8ENABtq4JDAJdiCd9UEPupcAhcHwxiTMSkDNe'
        b'SakiBtwVQBn6M4EsHZ4kmX23Jplq4d1DzJVn5JNYQdHocNdFtjgv1Ny+JVkUOIyo20zzZyM8Cw54pNA2f+RU/zbmZNd0kte5tWzKgBfJpCLyTDjOi+m8MkGHWWAQGvYZ'
        b'wlhwHANXnIbNdJ2dWJWTjB0ZNMLdNBYE4mRvsIUVnlNJ95DIEKoq24WD5oNqvdn+dH4pcDdsRBki5vKB52IpcBBe19Naj3aDm3SOaSlpYrTC0nCZLWhhg4bixaTSHcvg'
        b'TfQ84jBfNtiDmnAtuE3oqYCtYJPmcboRzZLh1ipWCLy8ltDTwbeiXENUaAjKC+tmZlI0s28Fu8CdwADMskJXnOEBeG4pqff5cXAzJ0jDsUzEsZcYsMU8mCjoJjslBU7x'
        b'Q7USsDQLP/IyPE2349UigOojyTsZ21QyKD0JcxJo9aAxYS6gqjoZOBU/FgJf1kO0g2NwH+lYUhTZrWHABnCBokzg1oQwljk4aE436T5/cAY9iqotdB04ibhjCdxL+lUE'
        b'OCFJpmtKgLE6TMDeZeYsa5dkUub91oaUucEj3AYpaT58ug3ywI2pgVODEBmh8BrchvgWHK8kZKBfLWi0aIPHES0YhDEZsUgh084KttEjiSLbEz2JGGs6PFWEqIDHIkh9'
        b'mMHr8GZyMuhEI3ClpyUjYm0AeSBpkgSlR1SHwU54HdvR3JpEKsNg7SJ4eXkyHtN24uMMelZMQ3jDgRBtbbqKelbzOh4MghvnG2gaaqMeWp1c9gviUIwocGwx9ohwNYqm'
        b'+qYHGvkaUcU1piThY44seIeBXnUDykh+Ttnx1M6MVUzUeb0WrzGgO2+8QA/nhkaC6Kl4zIOHwUukKBK4LzQZDSdIOFucbcnwBe25JJe3F/MoP08lE1Vl2BfFEg1Vp+HZ'
        b'ScmgKTMR28iw2QxwDJyPp3W4B8ResJmDrc2sfSgfsBPcqcWaump4KJqAu2QmwB3pSNysB2fWYMszWJ8qRMMPIs1S3w7uA1104VoWgsZB8E1GAjxFGUAZE+yXFgw5R360'
        b'iEWxE35AL8sTvpFhqqFtOyrTMdiMQUfr4RkhJQSXQCNxDeIPmmYmjzjjguYaNrwKNlBu4Ayn1qOGcBfYDprAwSR4CTbOwgBEaCyzZCyC7Q706eLdcBN8OTkb7kIcgbrf'
        b'TthCwS54EG4kcKnwbPlKXRhZUoBAsIVyS+dIEPPvI0OyyyIveNiYovLBKXCHAnfiDcjDteDuCm9ULalwd4IoidZw+LPhCTvKPZsTYAyukYL/7GhHBQX9gFll4edxljR/'
        b'w13m4Do8rI8hNJfgcfkuC+4gE8fC6fDWqEyZAhPKPYcTCJtnENZMAw3gcvIsERoRYCfYBbdT8PYyeJUeQE8jnj+cBQ/Foul5F5rgVzPs0WS/ibzXdFFmcg5dFydmWVPw'
        b'CrgMWwnUKLwUCxvwcVkM05sLzw9OoE6gkY364G0kItC2cSmF8LApAcKpB7cocKsOnKOhZ9vhBbAbd3SfxDS4C5yFcu9EUQCbsgOH2GW14CB5PgTuiICHWWQivgxuU+A2'
        b'2FZIAHV9YQfqzdrHE+fhh5no4cPscgd4jVYAyMEpNmwkrGsioSSgGdykWbAtCrYlo1YcJHsC2FpjxVoyP1njtgbeDCWKMvCSuxMqUz2QE6KXxi71pt3eYEhW0OmbSPB5'
        b'7cFVNmyA54CMFho2w0NgAzyMuBecLQE3UX9eDeoJbxiuhxdhIxJQhJFLqaXgJMqXHFxu54CDyZz1IlEi6PRMwl3PKoIFW+Lgy/RoudkA3oGHTSiqvBxcweaht8EBwrHe'
        b'y+HWYTA+YDc4N5tVJl1CSFkBXwadUlNTNGDB3WBXEAXPwTOuhNP+vsyI4vKMMael/N3Qix5EwFbYjKbXRlzjd6MrkZDT5Uhc6jjAhiVIkEvAyL2oc7VZpIsImXw7NuyS'
        b'RJHdmCO1boydse2ITSMqHoW0eEZRtNbx4swFRINYBy+solZF2UueTD/Hkm5AtfBo4qQTv4+v/MCPS+Xt+7qpLfRa1vKO1a6Ppj9KbD65+kKNr83n0cb3D0YNtPt9mrzR'
        b'sUawSrDqvddtfn493O2aa8Caie22fpZJ6U5OgkN71v/1rrBqYfA/qMrGzy94RKz5Y963c3/XUHmpx4zz7pp//ODgKtotcpz5x+6Ljy9/EXJmQX7n79Z++VZd2zHvmE1M'
        b'Ljx+fsKxNype7vju2eYfTe7N/9ddUaV7FdiXBv4iflTrGXl9T/qEmOIO0dwMk7KqfU/vX+eFWge5W7KCny07rzf7M2nOGqtr373d0aavNnk1VBDMXfYg48OEhtTYD4s8'
        b'K9xfFTV0v5fR5v5qeUP3o4wPIxumWy872N59mPv9p2sCVycuO+by5VRuScKy2Rapc35gZIbJpFudXF6F0548NRA45twr3PbJssywvVLH9H2fnG77RJIZ9lK9dNsn8zLD'
        b'TtU/MX3VuGPFLAvf1wvu7jj3meLVSV3W21avNfz+izdeD3fI/vSfjw5DnvHdP713pqmBvTB1ZmyvWdZVn/3v/dT956eNsZ9FqS8U3dxf5PjhDtXPf3vv4oqraZb38yLP'
        b'tfwQM+XtO+07fWov3J44K2fy/Peyn33KE9x56GOeab/xmzk9N+coDvVbZcduj/1nK+OPS2/85c6GE3+4z37zj9OenPFtaUg9d0w8zeOC4cNtJRvFXl993rFprRB8m//p'
        b'rmV7ZdJFH3yTGnBqwYNDd25/Oee4zVdNnzx66vJh88cFfUqv7x/uMXM0efI4//y0FTHFP4Vcrv7iVY+OH4Ky1OdFK+IavCeVxKzd9k7iV7GfTUvyvfPTnv4zTt94Z645'
        b'svTNyoSvRLeaTVdUyv6o3/uTYueNE53fpef+5YFnx8Tfhd+VLl+i/i7WZvnv3jlunbvjTP03f3LqeNO30stYYEV2peAVuDl8zEOS8CKop/ApyQBjourIBburvfHeJBMc'
        b'mlnJSJ0PthAbYN85WExznYHXN3oUO4YBbnuEEVwKdjS8CRonVJlUo+ETD3MHJ9SZGupRXHCMVakPN5FEaOi4Bc8ZAwxwe1qYoN0Ss4A3WOCcBOyhDWBfCkiBjWAj2DYM'
        b'eWtKCLF9CIUH0FTd6Evsbjmz4E00q77ExJCxtmRDPwnKI8l2GtGsW8IjlEEqs4ht8oyMlOe8QXtyOi5X3ZRqRiTcChX0O3cw4TUgmzwM+VZUCzaSQ6vgCDxhC85SdkPI'
        b'bqC1hBxanQv3Fq8EtwbPrZJTqy9H0vuKnRSsH9pT3K2zrQiuTiKHTJeV4/Oj0+ER3XOm2lOmmVEkDTguAhtAo1GOzjFT7RFTeNHomQcRX8sX4TOteBsYL6mwPXQjPAI3'
        b'0vsL3tM44JoA7iZ+bGPya1H9aXYgwB6wZdguBLwFzpNTq97wLmwcBvhWsxyjeDhPJO1gWIph67SnWkNCUTOQQ61XwEv/saXxcOgyVn5R0SrTIT0UuiQqsj9wNHgf1pSj'
        b'i9rBtyuw1yFY6RDZjYK0nnlNRo+4NjK9Y8aHjFtN20xVXHc1113BVQumdXupBbEqbmwTo8+Ki9XIcxiPbCcrXePuc9+Z9GCSMiv7dfs37VWuOSrb2Wrb2Uru7D4rB/nE'
        b'XisPlZVHH5d3MHlfMjY/RjnLYxWBKp6vmuercwP91XVJ1L4RKu9ItXekihel5kUNxQd3eXTO7I6iN2R0bhOL5zKVd7TaO7onU8VLUPMSRkYvobPsCVDx4tS8uJHRxSrv'
        b'GWrvGd3Vo95JoktV3jPV3jN7LFW8GDUvZmR0ico7XO0d3sOgn378695drvKOUXvH9BSoeIlqXuJ4lPureLFqXux472aqeNFqXvSvjJaovCPU3hE9LmNnro12fn65x8lc'
        b'rPIOU3uHdaOCRap5kb/w9Mha+4UmGZH5U5Gd9cRnFAoGRgShFM+laZXcXTGxw6drssomWG0TjLfc5zH6BCIFVyFVSLsCu/W6626Z9UjvM3uk6pDkhyGzekNmKTNzVCGz'
        b'1SGzVb5z1L5zlIK5Mj1ZXatZn42DrLhlHfYeXdS5pNcmRGkTQvbkw1WOM9WOM5WIO+2c2sLxW0IUs7viOhd3F92q6BWlKEUpfQLfLr1ORxm7zezFEjm4yHLkwQpP9eRA'
        b'DbxynKYryZmn9I/rP8Z79t69PG9FXNesM0lKYXh3oFIY2zO5p07FS1Pz0vp4jseMDhnJZ9K7O0re4m59FDu5p/h+rjpukSpqsTpqsSpksZJXpCwo6uM5yFnoL04xU+06'
        b'XcUPU/PDVLww8hbNpujEl20v2Xanq/xT1P4p91EDzFLzZvX9cgIHuZ68rsPsIX9qL39qt56KP1PNR0TNHHpluNo1VMWfruZPV2EUn5E5pqr8k9T+SfcjtQX7hQRDVROt'
        b'SZCk8o9X+8cPjhHjPI/GmHQ1L310oeNV/jFqf92+OuIFySr/BLV/gk70sOeT7nNU/mlq/zRlxiwVL1PNyxydRZrKP1ntn3x/joqXo+bl9PHsBgTWgolPKWtnm2c4QL+s'
        b'ec9wMEACIWU9qSm5JVkerOIKmjQ4CzrbGcb0dgaex38dVB+eVUbh9DUSRIJhs8oZvKXRQGlPYcyyfp5F4POD33R/47ChP3XRbOZwO4DBXbt1FI19RPbrsBKeqtfX7Ncx'
        b'xlC+/1dw+YYr3/nUaOW7B618b5lBIOTMm4zzhJKsKEpnF3sjA7SDZg68LaEoR8oRrZpbyDm73BJ4AjRTRukUNYmaFE8RHU0ckIENgWwKXqOoACoArUJfJvm/VGeIT5lW'
        b'3ZTkCb0zDShypO6iL31TvSRP+N7UclrzkrFsDeMHJuX5r9B8u0XiIDpbcH6GQ2AQInDmarCfKgQtsJMQVw5b4JXAIFSeanAWHKTE8HBSGWbKn+OIf1fe5855JquTSMax'
        b'EgtcAwkO0rwUJ69JNAnr1pnjm1XTqvKEeSmraRKs6kwpJLKW7luYlzK7KodO2RFDbmZMnJuX8srkGXRK52C0hkWP356UlzLfzY9OaScmN83X2OSl/IuTT99cM0cPE0R9'
        b'4Z1nEpDrSZ/zw4fCwN4srPnIAefYFAfsBe11DHCjCuzSuCVxgu2Bfn7GYA+bYrhSYF8sOEAbquVPpmJQ9+lh5xVwHWfQbRUMr8ENaKkLDsDNeNNiFQUbSIQ1bPKEh43M'
        b'SlCW19AHNeIWer19x8AMHtYrgQfR75fRxwScpWt8JzwP7sBmhtE8ihJRogVwG3nvZ5EEnJsKTs0z2Zq4hiJKLU/fbNgM98P9E2E73M9Ba/1tSPIFTeG03u4y2JoHmhlr'
        b'AGJXB8qhFhwiqoMkuDdP94SjGRLWsdX3rnBSdiG4PjtLBM7D0xFYAbQXrRkuriScZ24Cznvrg71FBB3KlUlW+cxla9FKAF6C1ylqJbVymRu9PYGE7/PgLHPJHAof+1wH'
        b'LpKBizTJXz1JUUIEkXkmfzVMoqFDzW99XUhtrSYnn7/5g+Rq/QBDuhL1b+GzW+dakis2R5hsK9FLiDr6KUOy784HhVdux5zPE1iWnfE5W/d+rFlG7RsNpgc7m7flh/G2'
        b'nox1Ya/78fDH35WG3/Ztvze7/FGK0d4//lO6MUX95d+PR5x79fe7jCM7Ql+7FbEpyfrHK2dDHm/azj71g+XNQ3+6OEn0RrLdve3zSx3mic7VWj55/O76A8pX59tfmr0g'
        b'/ruAZweX7pFsX3Qz/qG78Of6r+78aXXG00WXbsTPjW6cclzY+W7gjxEvLZVtfNX+8psfXZDNvpvXmzc7+af+hx8y3jiS6fP27Pcubfv5XqbfB5L9M4J690a+NKPo25Xv'
        b'NJsHPzBtXTjVzOSfbKOYKd++ffGjwIG8ZbK1877p/qFkL1v41t//5WY1u8pMVSz+22XDBSrOruOLmrrf6RUc9pAsXlu0bbnPmyEnC9NlMwofXo9x+5T7acyJw0U/33s7'
        b'N//JhdRds5/1X/rx5eVvX1grXbKr6o1j73+2Mv39r2JYf0/4+Ku/fl/90Rdt367LnVa566/6P621WvqHyjuM9LK9dS7XBTz6OGbn2qDxTBhmgHbtMU9TeJesG/3msMm5'
        b'3jSRF4MysAQKeJUJDiwDR8nicFE8PEVDNdWGDK5jw3LImtIY3piiYwi5wSGbWZNhSMMsvrwaNuPVXCo4Dq9iLSwGysRA2ZEsxKcbZ5CFriE8NQc7mkKvDwC74Q4GxrZy'
        b'WZRGVvpGNtLhQI1b0NJMaxCJ1/nwLjhJlnnT4DFwAxMCt4GD3lgFf54B5LAbdtDI4FfRzxb6iDx69zUfvDTGZ+R3gRs0HuVGtNbfh18mgI3p4K4wjd7SmziXbYfWxa30'
        b'EvYG2FKEV+W7I1II+rc32WSxdGOBTrDPiAbbOpRrTi+jfcAmzUoa7ABnyZoVnISHwBlMphjeHr1ShnfdaGCE0+7BOkvWODQ+0MiTndZkRb5GzwbnAS4XjFpJ+4I2Qirc'
        b'B3esQwvbBA94UOjjgzdxEaHwNAs3CdhNGsgbHIOntSakUF473IIUbs8krZ8OXiZrcrg7qiSZQ7GZDHA0AB4jfFMTCdp1jugWgCP4lG4mqi7ChKfyoJwoMYYOBKfmjzoS'
        b'DJoLSRvpzYDdgxoRtA6/Ak4RlQg8A+8Qm9cJldJRygHUCLGOWtUAfJki54cRL3SA/brGquAc2EQW9msKCbuA7WBj7pDzIHgldx4TnIAdcMMLGafqYEL1s7GJ1SqzIREM'
        b'X5OV/QIaVmhgvg3FtWkKbKrZO61lmpyxL7wpnByEeWzObTF9aO7aa+4qn6VgXtA/o9/HtSUfG3ymN1nNFTzk+vZyfbsYKm6AmhvQFdAV2BWo5k5F0VgNMLkX40cHd7kq'
        b'ueHdrn1cflOKnNthp3b27/JXcaeouVMecqf3cqd3R6q44WpuuCZXr4dcv16uX5eFiosyC+yK6oruilZzQ37xpTZN0TK2muel4nqrud4Puf69XP8uZxU3SM0N6srsyurK'
        b'UnOnaZK1Ge1Nb0l/yBX0cgUKlEao5goVmYosBUrjP4z+rC7XKz4PAxJ7AxLve6oCstQBWUruPOWcef9GqqldbkrujO4AnboI7kYFCVVzQx9yI3q5ET2o1Kiw0XQKe0U1'
        b'XcqH3JBebki3pYobpuaGaR936nIZVo9RNGY63UBDbw3pcldyo7rjyH0bbQUYq3meaA2AKlThovBXuKi5oheI1TDAwFR7f8unlL3A6hkOvg+huLb7gmWeKqvJaqvJT6fZ'
        b'W7ihCAu3ARKEUhbWWk5SmXuozT2U5h6Iv+h7KnN3tbm70ty9z8pGbeWmsKKB7B9rFq4cBfuh5/ReT7zGazOW5x+aoOT5KqKVvGC0FGffMn7KYghiMTIRCp9SDGcSWsfh'
        b'O9YYYoiEeoiCg8b7jGXRKnO+2pyvNOf3jX6/je3BFftWyNkdprT7niY2wc2XOyu5rkPH2PtcPTtSu1zUrlMeuob1uoZ1z1G5xqpdY4mBUQH2p25j12Q8+ojYC4C6kfNh'
        b'wzDdMBzEyO77JV5CYZs0soKaZ/M8E7n/lsUc9qohYJCVBfoKx/Bp2FK0ei7+ZTMCso2Yg1cb43NObjhwx4EHPjploLW31f7Ch6aIrSmN1YbNrchxfnLcmZwDJUfm+k1y'
        b'MyIzI1Nzs+dlxGb1s6Timn42BhHvN9ZEZMVmZ5H1J6nC/0xbOgqlzQa3yhDIhhA3iD97OEyb3gSMqfbcwIXi2jeF9JHu0McNGOAwuUFPKRQ8w0F9DGJbe1cZSuCrNPft'
        b'4wahBPbBKIF98DMc1KeMwF4LxNhrUzD22hSMvTaFYK/pwqYJMWyaD4ZN88GwaT6jcNW8cAIhTiDECYQkgbVDU0KfuafS3JNGZrPGyGzWGJnN2r8+dsCAZeozQI0XGDFN'
        b'MxgYru45oYGx6cwBarzAlm3qO0CNF5jomfoPUC8YmLNMYzA09S+HZpSjs5wrL1Xa+/Y5Tu5z8+xz9ehzFyhc5fPx12RFkXzx0A9XDwVbHqr9cnaX18hNtFcoH1fZ/D4X'
        b'fGWPMRiy5UZ9bl6KIHnKgJO5PeqXOHDhTrLs4zrIpAMs9Osx106WNcBBv3D1O8sD5VKU3mdAH98xoKyd5FY4mwFDfG1EWdthSAlZ0oAxvjZBDSaTyoNkSwZM8bUZZW2v'
        b'dPAfmIAvzIcetsDXlpS1izwaEzpgha+5Q/HW+HoidgZSiEswYIOveUPXk/C1LWXtKGfJY2SrBuzwtf3QtQO+dhxK74Sv+ZS1rSxazpaFDjjja5eh+Mn42pXUuyypz96J'
        b'JPLAN6nBwM3D3myAQgHifTQi2DvJAmVrFIlqp+CHTtN7naarnGaonWao7MLVduF9PDsZS5aimKi293toP6XXfgrt+0PFC1HzQgY4LDuUFQrqkweMohimXgPUfxAmMP1M'
        b'7QeoXxsMmQm6V9vpLok4lHk2Cx6dMh8oQPswxY+x5vubxRjLykIHy4qBEaxa2C0TWvSLmSjUfBcxtb86WSfRhHRWX5uVIVXkRM6fG9ZPKGYX6W8xHK6Dms9mUmKOBtnK'
        b'aAzUK06RMYozGRWnT+JMUZzZqDgDEjcBxZmPijMkcRYoznJUnBGJs0Jx3FFxxiTOGsVNHBVnguukiI/roMimjYmuEOUY8WqJqTZNEU8Ho8mMGuPf83GeRuQ26T/JbdWo'
        b'Ox2M3Ywi53om0TzSh3+N6yfUmxcbFtmNarEJKJVhvRlpT/stBvPNaY7odBieJ7E4YNWb1JsWc4oct4zwJDffosiWgD+49NNQpMlpsf84MAyAHDvt0EbxC8vypVK+Z0al'
        b'tKZOXC3NryjCk7lEXCEY9sywC69sjINeXFldnl/DR78qC6SVZeIaMYFvr6is4ZdV4gPe/PzCQnFVjbiIX7CSxnL3Go6EXl1MYUOZfsP8ojqJFB/87jfW/CTntw1oP+Xo'
        b'NquouK6ftbQC3SsXF0lqy9E9gypE+fLK6iIiydBnwfH58EIDneYa9NEno3QNmLazt3O2623XJ5bVuHXYqF04qE71iEWHqcZTH+L3HUYj9MOGRD9sMEo/bDhKB2ywzlCj'
        b'Hx4zTtdy7w9PWWPg4idWSGokxEJd47xF22iSCmlNfkWh+MVR8QdrOFSDqq8BgqksJjlrDsnnY2CPKPpoPkpQLq4WjO3tPZKvsXWg/brwa6swUMlUfpGkRFIzBlj/cCpw'
        b'4w7SgX4/jwoUPR4NFfz8sqrSfNFYpEzjF5aiVxaiLMYnR8teY9cJHcv3TEVcjUgSV/wbNTLll2oE8XUo3SHjZvPL8gvEZXxP9FOUjF63SiwpLEUd0YefI63NLytbSciS'
        b'0EwhHZOK4aSTuvUM0KmKMYjXEIL6Vig/hSBF4lzifVO0zaGpFjRIZOUXli6txFWBaEJEV4vRGDCOz4TagjJxkWYQGJ5LBgorK8QVmpyIywR0TdeUZugYu44Ta/jltdIa'
        b'fgFiFU01F4hrlovFFfwgvmeRuDi/tqxGQEahkHELqh0/6Gqnr/iSIk2DBf5Sg2kHHfpx7RW/WlwikaIaRoMdGhMJOwn5tZpmq62olYqLfsELxFjmuhPoTaHCYLI5EuIX'
        b'/Mjg/so1FDGqmAdeKtCCG2gcAGYQdIMyZ42LQdiQMkvXC/vWCBNzA80+kL6FNeWJfXumrUoEleup2nBMAjjvMmaWgxniE+M5unlih0XXq0xgx7Q5JN9TKSZ4d8bTrzjC'
        b'KJ3nROcL9sIbAWNmrPF16E0wH4ayBXsTQDeoNwbt8BRdBV96kH0kc7+63KRyMw5VG4Ruwi1IvtLmuzh+WM6J3lm6GW6AewzBfrg1kOTWjVbraIXo5xeXqWe33llD5Z1g'
        b'eHwsKmF96qCOWZdKB0zkNWPwEjwN95N896WRHScDv+DV1TFsP6o2DFN5FDSAo2Nl7JmgUaAOayY5G9wAZ41hPbhjJDmxMY8pvYZyed9FuWvPDOxWY+uRnztiP6mylydv'
        b'Y9p9wi6bRhWI/9yb/Iki7+ruE5avJx37+h/hd0t+ZpqegBc57hy/PwpLzibZrjv27YTcXk5Ryew5C7764GnF7/bfZ86rXDQhh1u85EDiIbGt/7tfp/z5+PIbGQ8OLi0q'
        b'qXN5OHXRmx9sqnJva+VWO/xxX/GH/OpCWCv7Yk5r8o9d74Z3iTb99c3ED48vvVa//tqencmHlq3eu/rxh9K3Up6ZeST8Uf/K3+NzE1MERvSxtr3gLDiq0YGDi/CYrhI8'
        b'FTTS/pUa4R5j+jQY2ACuDkOZiDEh+bjbijWZrDMY5EcO5QRlbHjBBm4miRaH62PV8D6wTYe7tLr0BthClOkOaaDbW6OkBbeKCLowvAt30xjA57jxWA1OtP0H4Qai8XeA'
        b'l2j/EafhadBF662x1jp+HtZbT4S7iHbcdFIcjsqAZ1NH7kuAeniSLuiGNMQTjb6wGx5KGKFCD7B/hv24gAZfS3pJIYKX4TUp2WVBVymwMRSjYCSK9KhUsEUfHAFyj99Y'
        b'QULw/yy0ssZwSMRlGnyLFZOoye7yyfJCeaFC0F7RUaFymaJ2mULwC4kj9JqW9bRLC4Vzr5W30sqbgB/Gq2wT1LYJSm5Cn6svBj901qQe8rke2WslUlqJSPJElW2S2jZJ'
        b'yU3Ca28reZY8S8FrX9SxSOUcqHYOJPiImreto31jKCx6iW9v8nicyjZebRuv5MajFemxxEOJrcltyeghQ+1DK/eGt4TL0RvdlFZutHd3lW2U2jZKyY16bO9Ekv6HL3YW'
        b'nHI87qhy9lc7+/+Kxya74drBqk70Ge2i8SLWjWE/ItWXcXAFB1dxcA0HL/+yofagc8YRxtrjtL0ASadS7E5c17d3+iQGI5P42/6tw9/scAg+jN5hGErdMIs0+DUokYM4'
        b'h4Ni83jweUN1pUXPy0F1pQNzSAvtWsl3DPzFX4sSqaHNJFdHmH5x6uZi6o4OUuc4gjoiMA7R9u+gMGqF6henCe9m6eAeOtE0aWXYURX26+uKnYvE7BenZzGi55tB/MN5'
        b'GzR02dF06Qjq/xZNxVqakMT94jTl4zpSMrR15DkkqeePBPeU/meEGeZqJeQXp65oeAvaYuW6jmj979EzCKWpFbJfnJ6S0fSglhsU1nXoETDJZga9rTFozZ1WyNIhEx8X'
        b'Iubc+1Cw31AH/0GP6A6wJz3DeqN643oTrDuoNys2GUSDGIm//dujQZQImN9yLMfQHkQWFWF/rhXi5bo8gvrUC3l2jUVrPTox1vDkFxWhlQ1aH+VrlsrEQSt2eSfkl1RX'
        b'1lbRSp58fmFleYGkIh97kB2VJWJWr0HgWC8h30sX5xZdEwBdlKigsnIpJhUroshijiajZmXVr1B4DL4olJ9VWY6XzbS+Crv+0+DN5hdU1tL+ajFniIvGqxv8L66ymi/G'
        b'VVIkKS5Gyzw0MtEL0OGF0tQ38WGLqq1E49hwjLUf/ofWs4X5FWQ5+zxdhn+wzgqe71lZRfzzlo2/ltetV3qdOmqQ4HtGFlSLC0sraitKpBrFBnFvOCahQ3wglUpKKggr'
        b'+JA60clY4zGaL9EtlQSt8dF6fsxctWt3f9LIwdMGl/D4Tf4CIdYw8ovEBTX4PShFIVpdS/BF4XhaB8KVEvK8VFxD6i5k2gvwTBzGtiAazZFdRSKWhr4wzyFaJTWaDOh6'
        b'J3cGVSCeWZVlZVjtUSnge3mVY70SKs5KL69xFVSkxMNypG8NZRmPqrdC5JuAZqSKX5M1DeOr0WJUSkmBNdC+L/Q87pz007rd1YefOqigId23smCJuLCGT1pw7D6QlR4S'
        b'7Oev0SZjZTHdO31ejIxhWCWhIxRldZWSQvEgw0eJy8QlxTidgL/AP2DRi2QZoGnGWjFdHEkFIRT3+piY1NR583DJxvJpjf9V5a8sJx6xxdV4GhTyy1E9D6qDdAgKeD5B'
        b'mubBuEnD2wvfGa4cpHuLr7anjEkWLeRFoULivo/zQK8P9Bv39cPQYbSqUp1ugu6iHlkhldBEVRaP+db8oiWIM0h94AeIW/D8Ffj32GPj2ErWYZlIiZZYUlhaIynBRZEW'
        b'lpbBW2gkLxOM7rPj5iniI77JqhHXosF1MAPEwRK+porQCFWOelxsjig7v6ZAjDXvRePkhNiF9mVbVlu+VFw6dv2L+IEjkpG35dcWr6qtEaOZo6IIsevsymopIWqcPIJC'
        b'+ZG1xaXiglrc9dADkbU1lXh+WzrOA1NC+YkVRZI6CWLmsjL0QE65NL9mlXREycd5Ongskn99BU0dKxuJDlnlv46skLHy+3X1Mo1U5FDV/0LNj3kzm+ZkrCIfQfev5kTd'
        b'4hdXo9J44rodpCm/YFVtiWB89tN9nD/VbXwGHJbQf9p4KRGbVfjmj89Sw7MJHi+b4Odlg5hisHzPySNEN9m4RZs2LLMxyjXuhKZBr0IjnOYXkQeQTIrGVu1Q7plFz7Hj'
        b'TthD4Fih/Gh0waevkIzjmYwuxRXoP2JzPp6DQsYdcnVgtYZnEzAim4DnZkMQuOgpY3Zktigxhu+Zk1WDvvF8M2XcxwYRu+hHY3PISI1v8D1RJ9ewOGr28auhthqJyIVo'
        b'tojW/BLydWS72JxMvucc2FFajTopoiVofFJ0wMKGMhu8rSFKm5V0aW21dDRRzxP3xhMviSj54pLfoIgWOWy368VkGAJ/FspPw1/8BQF+i178sQD6sQDy2PitocVV04iQ'
        b'mmu8NH8eHxDQNfQI/kIJR6cbfxRLEFdXV/jGVefXoqDMxzdOgqS78Uctknz8sQrnM/74hF8w/gD1vDejUSm2FAlhaOwff2gitCGZrWhsMsarPCTFisU1WLLA30jACn6u'
        b'fFdQuSKUjw9hIPmpGEut6Aaq8/EbFT+E0ezop/LL+PjiuU8USmpwh0Thc8U9GsIPp6R/kIyFWE4XBfoHByNOG58mjJ6HCMJfz+XI4nxU2jg0qDwvEcHfQy2Ev/gLgsdP'
        b'qBnmNEPc8zhaiwwYyo9Cv2hJeEHA1OemH+za5JHhu9nPrW8t3qDmSbp9xh+sMcogEtGiItNQ84w/IhZIClGGidHo1WP0yGE7ygbUuDvKFl4sAptbVVdm8tMifQ3afes0'
        b'2EkDMi2EpwgcDg3IBM4sIE91phFDLX6TVaHJ/egpNPBc9Iry6WuSh1CiMuNIWvsYG0pIUeZo0RPWlJhLpwUn4ZVE2AwurORQlA/lMzWUGKC5ieEmeBCc1cXfw+B7OSYk'
        b'q8Qla7El4lwqunbBiaR8qhblS5nBNoY33GiKUidhZ53YcgdbgcxKQKRkU/AiaMykVgQZloBLkwkoTY++1kXAW3MHeLPyUzS7s9eZGMdhpJOAKHA6i+SUQI70iWbr7tDu'
        b'Aq0mAnBqDdmTkfw0OYopNWUgkt6Unth7MQ1GmGwrf7IvKFXe6ZC30SaiM4zjYH4zNnbvmT/X227bwtjxyqQbzr83aheuTWyTdyzPmSpcOXDkqx/X/xh+2df8ctRr/X6J'
        b'3XqrfT/bGqIw3ehqeak1yqm617xn9z/6PypN72h9cP+roscDm7/7duJuTryp14Qf+09VysUfXbvhuNr/2ZyuW591S9eqrju+F3f8bxFVL6k+dChJ+bpv1ztPW344+tFF'
        b'tWniT7zsuceLjN/9uFP1ds13F1d/dvdPT6VPXk37Wj0rYYK1ZUYa//2F1neenj/yYf6Bvi/zVq4zXHnt1MKNM84mfHzkQM39QsXnu4yEj6es2PDJnq8sjpSbXZZ+13H4'
        b'X6+YHv/Xxyb/ap/6M0fklMziPxIY0LuljUDhSYOGlMILQ45Yk4kFEAsqYIsLvExQwzTAIfBoKW3upHBd4A13pCdi57agk03plTFdauBLtB3OnuwVw50ReDnRuCFN4OQz'
        b'7CsQ7A2Cl+HNsHF2UXW3UMvhRmJDVQN3VA1zR2ADGnQ8EojgFtoAatsEcEiK2UHkSTwP7mHBi1mUBWxiga4MFwIPA9tL4LZkcKEgJZFBMTMZXiGFggm/pSfyCdQwIJAR'
        b'ZtsmgxpxLRbIRc3GbYYjxRcqnfwUy7C7OjtZjZK4q+uzw56CrAV9Hp4yExpH2lVe1yHsYqlsgtQ2QTgyh9Hn4S2vwXY2XVZdRd3BV8p6AnuiegLVwfEPg1N7g1PvF6qC'
        b'M9XBmSpRllqUpfTIlrFls1tN+uyc5HptYWo7YVNMU0yftaPcVWntjj6at3r3eXjJcKpjoYdCW8MGU/4Jb4rOVNlGqG0jlNwI7Ox2oWKacuKUJlaf1URZkdrRR2mFPxrP'
        b'CGo7b5WNUG0j7OL02kxR2kx55Oil9E5TOaarHdOVvPQBJsvav89vWpdht6vSL7bHCgX0B5seeSqsVDyRkif64ZGdKybLfyjoc/SWlSuiVY5+akc/Jc8P74AOsFAE/maz'
        b'LER9XFFTjJrrKs9SY8MbkZI7BX262PT34OeHRzZ8jKciGgr6bD1kIgVLZStU2wqVXKEmawsR+pb6YVZiW0RPpOBEo2g/FuQbR3uzoDcH/w7ixZhR98yMYjxZ93jGMZNZ'
        b'9yZz0G96o3gCvVE8tLeBzdx+FSrACGYb2il+LrMtwTvFcmoI9XiWHYOBK/G3Cn4zK5jPqTEc75DpkjjeYWscl3HqqXo9jSOH/xnnZcUCZvWfqRFekJ3GmMvd6LncYQHb'
        b'fD7THDtVNfkppIiGSCyY7SutxcCGu8BFBzaFhi/G2tVSGk0AN10saFhojNpqDuVYMQduBLdpYMWT8GXTLPwUm2JNZ8CbFLxSkUPewlu4Jj2HGiAOWefaSej5HO4Gx+cF'
        b'BjlYYCTGg5S4JJhkng32iwKDim3ZGH+XKswWkhyOZOm7ZrB4GGnWZJVhNm24/9dwcyqeGYEkkbyUqHUc2iCcWm8Rup5Fbpb1lRXRKePKTOa/xUQ9IiMvJaAuik7Zb2u6'
        b'7iMGuSms50ygUx5dZzS3kOGJoWNNChZm0ikfTTKy/ZBFbpadK9YgBPTX6UXZUoSkFFCcpAFZ3BMLtmVlZGQgpoctjBgKbPTkEIxEcBRukAb6+aH3JcNmBuyg4EZ4Be6n'
        b'LfhPCadkZaDGZJotACcxYPJeKxpk8AZsKdBiC8CToIFNcTC2ANhkSAM7nJjkiDJlUwyMjIuxBRavWmXGybHAGP/OlCDTWTKHmNvHucBTgWyM5wBOLAlIcKZxSMFuuBti'
        b'3wYifM5uu0gKj2uwQ9eCFhoNAEMBRID9NBoAbC8gWAGIM27CQ1kZfIxuuBdcB5et9UB7FbxFYiXwauQgJoBDkMbv0Qpwmjbbx9V8k2dgf4/Jx0NDWcZqb7pG5XMNF55i'
        b'0Tev63PpGl0Ct8OtWbhCMWLhCbiZyvenoUd/FHGTwqkMzLthplFGNGSwMzzon5UB5AKcHNwMXWsM2+FxAYkrjQd7pKaBqLZMwQEmBhq4Da7D7ZJLdjfZ0ipUC48yzE5k'
        b'X0dCmPmRRR9ft/dwfVzFubN530z5SbvXzQ951qhudNS3bNJTOc+p+Kl5Z+qtB+d/77rtatnSJyuk72z/p+E7TVFMwQfdxor013qqqlcZr7y5ffm/7me+nV9ofLQ5zvnq'
        b'4veDOz+X9+4998Xh+ZtKfuriMO5vvVrH+PKB3RvCZrP5reUdH3z+U6nxnSrX99aeFl4IWZW8LXzlFxmfnv9Uf9pT4y8WfTbpImuKT9TAibg89eelrZ+73Ho692vDdinV'
        b'fsr5WQ674d4He7L3V/TYl8raLS5/YJT1hqlZzpvblsRk75rFqry1c8e7zXU/xt30OPMo96Le37qqLv2lOSNTL/7bHUdzfxckEu/5hH1qRdI781qll4I6r9sy31KuC/7g'
        b'jcKdFm/va539xv3Psz/++brXiY945RvObbX57O9WKfvTWje8N+fdK5nsyV80Xr/gc/X+efUd8Jef0/9w/kHh68eccv50fVvoual7fvrY9V+5X4vOrE1cPXCtf8MA9cq7'
        b'Uy1fr8+9/WcB95kv6Rqgoe6XZK2pcBc+sbYd7CbS3/pY2OlNhDiRuEQPrTVuMsHerDQSBzegHE8i0T4FydttGWxnBjjiBs+TOLApo0jj3wnKKjUunvSLafPrjsXo9Y1a'
        b'YLwlFgRSAHTD6+RsYI2nm3aRAfbn6jpB5sdyDNOmEOSBNZn6mtN/FZG0tT9aAt2ixdk2eAXsp639F+Zpbf3hSTMilabD5lT0JNgfN3QClz7jWAZP0mgBHXNRuWhQAnAH'
        b'HNSiEsAT4Ao5GxhriA3n0zUnF/WidM8uXjYgEIPC+djqnwjM4HoWkZmTFtN4eieM4O1kDQgeaPCkEQDMwGZWFHzJjSbgNthkqUEAANfcaNw6jAAwDbTSCTblw62DedyN'
        b'IggAZmtZMXDnCg1oHxqmNmEAAKGPT4BY9/CiPjhLRPdlwQ6D5yORfHyMWPYbguukhTzRgLVZa9pv6KbxvwXOg2YiXS+Eh0ADwXbA5yfBXanuEco0UwIvMAeeydOcAxWa'
        b'+448B+oFDgsMXli2IXjefN0zcN9Q2DnPkFAjzS2SFNYQKXqCxu4+04maZNfEwc6Zjfv4rmq+Hw12peJPU/OnDVAuFoKnOGhKoH1xrWid0TZj0P8X8SJt3Tq/bb7CuXVx'
        b'U9xj36nYAdjp9Z3rm2JlnvLZKltvFVf4mOv0kOvey3WXV59afnx5H8+uj+con9g6AeWh5om6rHp5QUrejG6ukhfbw6V9u2R3zOtiqHgBal7AQ15ILy+k20LFm64mIFtt'
        b'Ex7yRL08kSJfxfNT8/y6LJEYb6XmTcFxZhrfX7NosL4uJvYspuYF0YZ4CWp7/7Fy7Y7qju6OVvMiNMnaUlU8LzXP6yHPr5eHUQAIEpkGBYAXMozwiG4bJS+pJ270zdKe'
        b'BHVMzsOYxb0xi5W5JaqYUnVM6Qsnc9DWxOIuVJipat7Uh7wZvaieULEjCKmOciv0N7fdocNBhT2fOZCqHfqgksS0JbaatZnJqxUMeTUq0PMjHPt4Toi+gSl2fhOfUnae'
        b'Ns9w8H0wxXPcVycrVdl4qG08nk61sxZg5DoBxqtD/IF/hVBOLsdKD5XKV6scA9WOgYidrHgDlLFF8GNX91Pxx+Of3zZOz29WUg9qNwxTwAtV80If8iJ6eRimQAPjN8RQ'
        b'Wr4asDAUoSIYuqEioOB7y2FFUHg/tTJ0C0ZM6r43dYBL8RyaTEb7wnr+yVPiC+uXu9uneB1RS2ns5GOd/odN5DPwkukZFsJ1ncrqUboO3zgavx5sjWkfdi6rN+jTY6Qb'
        b'oP+Kc9nq76kR64SxXAHpp9USF423QfN07wQk0mUkoEkXTa3gdHYCEknrhT4CPbjbjEqA2/SrwEEgp6XdLrCPn4vmqGZwlpyTZ5UxwKaZYhqW6jaayDu89TE6FAZ/mgTl'
        b'5H5pYD54CXZ4pzMpRiYFD62ECknXx4ZM6VMsB76xatesm9iG4UrzHSAt2GRad6/HaUDfQW5ZZsFisfivNAnL9s61WHrS55+JJpmNmS5XdwfcuyNd86TkGbPZXm7S+Nhw'
        b'cvUDm5y/hS0P6TR9EhS44777n841wcYfctxuvDf90G7TtWurb8R+26t+GPdWiN2PfvveK06aJLtv8HqqrLnheObxWRtTD/0875WKW26ngt5d2G4dvq2g4ckWgVe8haNV'
        b'1PJDP05OSHi0qG5t591Fu0t9bwcnbPl90sMTmdWiuuI//7g+8833RKzvb7MdFD1ma8q+7gw+9dPRG82/+5I7scrs/F9fC+x2iYqbV73im2Vpf/1Y/0BczOEgwQSCqgta'
        b'KqZELyFVj5aZUxngfDmNEcuA8kosKGjMhmErvGIAG5lrwdGVZK6Ecn2wHUXeAjtRoh0Y9CeNaY/m3+v0VLwByLDJ8Q64Ha0+fBJJCmPYxYS3BGA/bWtw1xFNoJfRKuWS'
        b'eLlGVWYITjHBS2Aj2E6IAHJ4CZ5KFgIFAwPf7EhBYo1xBBPKcqbToljTUtABG6vN4Q7fdBETyytecE8UebYInAStw3yHro8gnkOb15FnwyzgAdgIbrkJE+EuJATqLWZO'
        b'BieribRkDLaBfd4ElEfkI2BiFw0NE+AxFtjKBWfI0wal5smuSLxHwpBvGofSC2PaoBVqF4mbZwxeTtYyLzVnlSGXCdp98ugS3YLtYCt6701wB+7SVFwUkxcPb9MoSArQ'
        b'CveBzWDzkKRI5MSZi4iExZlh7x0MWjV4QXpAwRQuM/mPQXu12hN62DMg8IqDw540v472IHpco6hLcqa4E1umHgzfFy53pU0psL5omiKqM/5C6pnUbleVcKZaOJPc7In6'
        b'XRJIul+jislWx2STW49snZUuU1W2IWrbECU3BMOqmhwywXMXklusbA6G7gvdG9YS9tDKs9fKUzFRZeWntvLD3ju9+2ydZR5yVwVLsVBlG6q2DW2K7nP3PrX0+NL28o7y'
        b'IaVYq5GMLStCswjOWJ6tCKLnHyX59HFtDibuS9yrQalsSn5s59A29Vj4oXCFq8rOV23ni/Pw6OPZHjM4ZCDnYsJkZsPew7T2JoHmPQ7Osmy5S4fHKeFxoaKmK1vlEqp2'
        b'Ce2OUTlEqh0iUW6TvHsy++wdjyUcSpBnt6a1pcnSBljoLokiwVMcPKOG3RsrwCq4sW4PsLQ0SbH241XribFTOa9OZcdON3w1nIFCeh40pOfBb39xMqTZA29ODOrWxmUO'
        b'J7Twl26gtNibq/m/6AH1v+QQlTiJFLBHGF3Tl6T4TPI7TWA5EknGiEHpwsm8gBHLGQbx7V0jLpfSeDDfaGtHYPEbatN1GgNX/4aR/+hGuYAbZdCm3hkLKO8wh+PGsNmm'
        b'5hjaxHzAhDKzrp8jZ8mjZSu7Cnuy7lv1JPZNspd7d1t1Z3Ub3o9GrGk2C8MdofAZCQf0qPAIxgDLA0PM/GLwlKPzJBvfzWQMA5QJxoAyIRhQJgQDyoQQQBm7yTLPPnPs'
        b'w5SGpLHDkDR2GJLGLrg+eQSgzBQMKDMVA8pMxYAyUwmgjJVdE8qBQC5x/VECq0CUwCrwGQ7qo0ckCMcJIhg4RQTjGQlJGt23+OG3BOC3BOC3BIzCtRkjgQGpXdQTzVIZ'
        b'MmmXFf2LDjGCU40sRhYjn6R2ntptqHaOeuic0OucoHJOUjsnqeyT1fbJfY4usiL5NPXkad3u6smRDyfH906OV01OVE9OVDkmqR2TnrIYDsm4eXgpuJJRiDr/4DsG9GoZ'
        b'pqIB6rcJn+rjPJ/p5lzBmmbqMED9clDHIFUhm6w0dVSZOqpNHQeYXFM0SP1i8JRFmTmNTj+EaiIFG+ElaTq4NKjT4VCmtkzYzIbbBIw0yXuxEqZ0PuoUwW/Yrd3zVtrm'
        b'DPOtT6qvVwn+6Vve/u2pa3Yf39s1fY5Pqnu337L21KB7FSlWegufLLb7eENqbu/GzPlLhK9zAp60Vb79z6OvBQQXWi+46PAXpx+WTMuL+MTjrRSq7IcyJ256wM93wsty'
        b'gjYdYcenzQutfH/ahemqn3z3r571Xonbk1XzUqm0imsur1ZOf/BzravR96+8JvrqxOWW1Y6hta+dqtpd1/HWk2849bf+UHDabN+uVV/LvvH56g+pTdHlf551TC+ow2KX'
        b'QD7prWibR1fTrjKm9tz4nfRYjaLr+u/7Hpi4T5rea2T0MMez660lT1gBX949/WXTof0fiW9/H3/w9dg/NH34aofe9VsXFwR9/SAtPPWLnW9/sS/oragJP745Sb2gaE3w'
        b'e4/mMG93WM1LmRPSHvyV4/kjap/vPD/76qu/vLul7OSNkII/d6elnru04KMHXqtXin0eF33U+O4Vg9WfS8ND3n8Q0c168tTm7dTaDeflAhbZTYye5QgbUxgUA9xaFELB'
        b'3SJ4jEaN3ASuLdVazMIjwyxm4XZ7sqlpBWSmI3yswxMFQ27WtwQKXEeOhAbPDf4b4+6/MVK70lJVBPk3asgeMXj3G+TmllXmF+Xmrhr8RcSt37MGjRrR+B1EmVoPsPUN'
        b'bfomWNZLmwJ2LN+5XObcsKZ+jUwqk8oD5PkdU1pXta1SzDq0Xra+yxX9VXc7X6ntnnVlxUWfKz49MT0x9y1fSbiX0BuQogxIecSzlQXI8tumtBq2GcqTVDyfLhsVL0QZ'
        b'lqaySVNmZitzZqsz5/TazFHazHk0kS+33FvRUqE0dx1gUby5jAEjypLbFNliXR9VH/XDgD7DMJHRZ+nUJDphohTFqfjxan68yjJBbZmgNEnAMkuIhaHrAPWbBJ4ehmh0'
        b'+rXBUxw8G7qXzQgztB2gnhc0zX6Kv54N3V3HcMU/nxfIJj7FX8+G7qYxKCPzAWY12xANY/8bw6ckfEb/ZiFid07UkFtjSPHcFcYqm8B6kwE9A0Mkro0XTKxmGdqj/P6r'
        b'4VMSPtO9v0Sf1G4mKc3//fApCZ/Rv7V1OTKRFJvtNUTOjLKigJVtlEizMe7Qz8zN/Tc3wv87AxleC+cNP8oxlvhpwcTip3bwwtoB6RNKox/zZzDMsZD/vy/4zUy58SL6'
        b'nGEki3qFZRZpwZK4zHvClF5FN/dMfL181zQjZqR57Orc4mzzV0yXMWdN+NRaL/VGYPRbW/4x2+dknPvi3vyY2K59uXv+sedGdkdCs3Py7jBOQ/bCWNHSvfdm2d9Lbei2'
        b'mnl56sf//CjI8djvZzl+mvqzdMm3hadfy6zcd2HPtsLDBxrda6vfv7yk0n2r/ftPetrFhxsWXnrd4feim+q3ZtRlRkTCnuNbovVnrGA/8+8xn7zT/xVuYMybs9p7mMmd'
        b'XR+lLV1vVPZO3eRPvjSE2X7bd3sJJtDamd1LwTWswEnH59d2JutToGGiMbjEhAp4xZskMYHb4KnkdBG8iFNh/csKeNMC3sKgzs3LiBiwAh6Bx8DtStAI9mBXeDtT8eab'
        b'PmVmyXKE25hEBeUIO4OSE1MdVnml6lN6bKYBuJhCNrv04d61sNEXtMBjehQji4Iv4Q0o2p13s3SGd1LiYg7FSKagDLwEzpMtopRSeB67/NuN3oQxkIPACWMBEzaht5+k'
        b'9S+XuTlSnQRw0zKjRCbo8gG36dNbR8HLoA3eNkwmouUOjY/VBlaaAThHNDDJdfQmFIeCXaCenCvUSyYv9+ShF2F9ZIJWaVZfYWLFhFcy4G6SAL4M5GLQiFJUaVLEuxiB'
        b'y0xwJXo+AXtGdXsVYgCPS2mLTUD98mW18PIyk2W1DMoG7mGBnaAJNtJbYbf44GQygS/HhaEo4QxjcIgJj8MTBiQncMImHle6bzL2XoVPguErfcrOlQ2uoTbYDK4YCrxe'
        b'WLD6XylnjTlkeRHZK0L77znS19D4RaAlDIahieQzdBAl8DhmS3GsNqThvz5T7kNTx15TxyMrVKaealPPDXF9bKPtKZtSlBbOJ0JUbKGaLVSyhX1s0w2J+E/nh5Ny+KeP'
        b'7aEc69PHFinH+vSxJyuHfwb05ptz0Lzy/1S4gk+ZcDek62zQOPezysQV/WxsSd3PqamtKhP3s8sk0pp+Nt5z6WdXVqFolrSmup9TsLJGLO1nF1RWlvWzJBU1/ZxiNPOg'
        b'r2pseNHPITbP/azC0up+VmV1Ub9esaSsRowuyvOr+lmrJFX9nHxpoUTSzyoVr0BJUPYsaW15v560srpGXNRvJJFqUez69apqC8okhf36NGCgtN9YWioprskVV1dXVveb'
        b'VuVXS8W5EmklNhTtN62tKCzNl1SIi3LFKwr7DXNzpWJUlNzcfj3asHJocpfizeK85//j84fYkwRG+MHpwzhzzH+IXS0YjGUsPM39/xL+ZrM1lr1eMTOMdKVecTWLDGD9'
        b'w6AYW4IXlvr0m+fman5rRJl/2Gqu+VX5hUvzS8QaCMn8InFRmsCAqA379XNz88vKkORG2gkrFvuNEPdU10iXS2pK+/XKKgvzy6T9JpnYKLVcHIs5pzqKqeF8ug/gdv6H'
        b'QVh5ZVFtmTi8OoFJI1BI16JggMVgMHCZ2QMUDswoY9MN+gPsMnMGd4DSCRc7U4YWDw3seg3sZEkqAw+1gccAxWRMUQrDe9x73F/xvOepFCahT5+BeZ/RxHqh0iZQZRSk'
        b'NgpSsoP6KHMlZd7EU1G2aspWqf0Q8v4PcPSjIg=='
    ))))
