
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
        b'eJzsvXdcW9cZMHzu1UBMA554yvFCgMQeNp54sTEGbAcPEEgCGSFhDWzjbYPBDOOB9954D7xnck6b0YymSUdCmzajbeIkTdOkI03b5HvOuZKQjCBO3/7xfr/fa5krnT2e'
        b'5zzrPOfcD5HLPxH8TYU/y0R4aFAhKkOFnIbT8LWokNeKjoo1omOcebRGrJVsQhVSi2ohr5VqJJu4jZzWS8tv4jikkeYhb53C65s1PjOm5c+cJ680aWwGrdykk1vLtfI5'
        b'K63lJqN8lt5o1ZaWy6vUpRXqMq3Kxye/XG9x5NVodXqj1iLX2YylVr3JaJGrjRp5qUFtsWgtPlaTvNSsVVu1cqEBjdqqlmtXlJarjWVauU5v0FpUPqXD7UMaCX8j4M+X'
        b'DqscHvWonqvn60X14npJvbTeq15W713vU+9b71fvXx9Q36c+sD6oPri+b32/+v71A+oH1g+qD6kfXD+kfmj9sPrhuhFsOmRrRjSgTWiNvEa6esQmlIdWyzchDq0dsVa+'
        b'ACYOpqBcIcoudcwrD3+D4a8v7YSYzW0eUvhmG2Tw+/lSEYK40GJxsaEpOA/ZRkFkflglaRqzjGzJycwlDaQlR0Fa0grmKKVo3EwxeYRbyCMFZ6N1LpqeZEnLIltJcxZp'
        b'Hq7lkE8aj6+Qu7hDwdsGQAZ8fQ3pyAgmh9Ii0iRILObwEQW5ZxsKScWk2ZIB0UqyBYpLCvE5FEAaRdlkM9kJpem84QZ8aCJuIo0RVaSJNKfhh/iIBPngDh5fn4v32EZD'
        b'HtJIaofjJhteT6754Ybly2ykY5nfMhuHBpJWEW7GZ3Eb9HYMHVcgvoibcGtkhjKM9pm0Qt1nyEPc6oWGjBbjTeQ4OVfKueDjEMe8FVPgCaBDPwx4uiF2oHENgLdreAAa'
        b'x4DGM6Bxa3k70MpcgUYbH9ANaCMEoD0O8EJ+CAVGzSsYFp8sQyyyoYRBEkXpfhZcX8YJkaJ5MhQIcVHzFiSvTooRIt8aIUbwLY+aZ0t+dqQXOosMPhAtMQ1KueH9MUzU'
        b'++O+5G9Gt8znOYM3JGz33cddmf+KP5paHPMb87dT4hGLnpDzZZ82S58Qfs573LcL7tjqUCeyqSDBnI/bAVxNkbmhoaQxMlVJGvHZ/NB0ETmRRVojVGnK9CwOGft4TyKH'
        b'yTG3+fZ1DHmqMN/uCwXR2db5OueT73U+uy0Cabf59Ms201Zt/eDhTdp98+YqB6+cxyNehMihIvzQ1gcSxiwiN/J45L8CjUKj+k6y9adItwNfw3V5c3myHVC5HM3EV8kR'
        b'WzCkrMUb8CGyU4S8IhF88Jk1NtpmJdkYTnZyaBW+jJRISerIAdaqj2R6XlZuAblMWiSIX8UNJYefsY2FhMXk/miK8+EZgKdbMnND8dmx+HBEKluGKnJWgjeSmzyrm+zB'
        b'hwGxO6RIjHegiWjiArU+9s+jecsxSNxydtHi10YG4KmBde/v0996d+a8v/Ybym350cio98bGtyf0b7iofu3DAe/WbgqMqy/x9X75g7H//O2Raf5DvtZFXt6+uyLjzIu5'
        b'Y/e/3fHmOwEV2gU5Qz4Zkn/4/Y1+yf1/GltxTNu2Oybx5f6vW166F6wu+HlazGrlL2adD31n887fvV+8+8dFkaGT/xO7ZsDFD3NeTFHOy/jZ3PfC//Hahp+/Nsbw+0l3'
        b'PvdfPXvCSXGAQmJlS/36OnI1g7SEk5YsZTolFsHkNrk5SETqYWXfstKVSK5MzQlPV5KGtMxsCfLFV3EtvseTQ7PxeesgSC8ImRGuUsh90sMFkoL6kPUiU5GflZKbNeTQ'
        b'HF98NiLVBou/MZJHQeRukJ8IXzTg/VZKy/Bt3OENU95IWhXDSTOspvEcNHGHHFPwnXyowkzRRuHLvv6LB8XAbwZM1JlNNVojcArGg1TAP7TVkzv9zVqjRmsuMmtLTWYN'
        b'zWqRU7SdLOOCORnnA58B8BcAH/odDN+BfD/OLHXUrBB1SoXCnV5FRWabsaio07eoqNSgVRttVUVF/3W/FZzZi/6W0AdtbgrtXADtHJHzUo7npOxpo/1dgu+WhqeTlow0'
        b'JW6MTAfGEKmMTOfQGHxVUjSDdDiXI/0ntn8zxqilvB74vIYrFMGfWI8KJfAt1fCFXpqAeqTjNGKNpNa7UMZ+SzVetbJCb/ZbpvGG3z4Ca9WJND4aXwj7QhioB4T9NP4Q'
        b'9tNwTDbo0ymdy+Ypm83b42+B/JSK7F2hg/RyUIko5ODXUIlAckQNIiA5YiA5IkZyxIzkiNaKPZFw3k7T3EmOWCDhxwaJramUNE8tjrhduBTpj5yrEFlyIOWZlD2fFr9a'
        b'8nHxjqQ4TYP6k+LmsgvajyGm8LlF5Mq26Lrcg8d2B/0oR92uNkjOceeKfyLeHjHMb6ZqWLPvguT1nwwKmTtoY0jSW6jqxcA1P/dSSBlyDx0oCndyvXAp6oNPiyIW1czF'
        b'W1lyAd6V1JUuQn4RuMFH5JWK71hDaDK5UZNBmjJBDFBIyZbRSIYb+RXV+K6wcB7h9UCNgFhlpOGLQGdHLE3iQ/BZcoIVJhfxJvwAN+UArxcjSc5KcpAjd8m1MrZmyaaU'
        b'uHBlKhUP8I5AJCPXeVw7At9X8C44KPK0mBhKdsqKivRGvbWoiC0aPzrxhYEc/Ug5MVfTRwC2ypFLWCySTrFFa9B1iqn41ulVrTVbQNIzU8CYvQWkt7dLEd3sTx99nKuA'
        b'NrLQuQrOBLqsgm7tlfIu2O5ELZUdtXS8HbF4xstEgFg8QywRQyx+rcgTL0M9IJYtDH6nJup9SQsAYyswYNKalyqALXfOXCUwtinkmNSCO4JAsKrTfzTsgJhh+ScRhz4t'
        b'pij2ki4yOFydiX+m/qw4sLRcZygRN0Yriz8vXvDSoFefe4dHR96V7TGXKMQCOb5KLqmdaMFwgtwiR1fgfVOsVPLNAy65g3QALW4lrSplFaO71kAeDV4rxnV4TwlDjyxf'
        b'csmOHDlkPZIw7MA3yXor5Y9yshFvzMhRcojsHcJXc9Pw+vkCDHmP6AA0r0xr1Vu1lXaMoCQLlfhwflxNsBM2zixCVWIG4U6xUV2p7Y4EvDnIiQQM/rBqUakT/kcCXOHv'
        b'oY3/GXXRPTUSkDN4P9nlEQ/GTOvChKDZwfps40tiSwyUaax9wQ0JnCjwWXGqmW+MsUW9HXUyShxbdVqELi6VFdW+qBCxFRw2YREggUbnggYrSAfea5VD4qyFpJZ0DCBH'
        b'3bHAjgPecutAyORHGkLtKDCu1I4Bq8gOO2Pree0DsC3dgV32BLAt7sCWCJCkMO2UVKsNNg8gF7mAvK8T7lS8K3fCfX+gZ7g7m/O89GMEuFPBltOJn3L5u/EVzl6lO+Ql'
        b'2bZI+J0Di/I41arySYNSqcpNTS8gDTl5oVTwKUgFQVLFISt5gBsyvaVT8DFbOMWWg+Thot6JBm5PlAbhZp3+l2/4SSy5UKhjne+nxZ8Awhh0YQPC1KlqA6DKhTmfFFep'
        b'G3ad07arPy5+veRVXeSOUHW6+py6dWpgKXp5YHrtph/tG3jFGhWh0WhS1TLde6+CZFYcuEP9H5ADqZjGkT3jmZg2ZZ6LoAZiGt65hKFbQiznRnPMowDdGvA9JkWGhSQ/'
        b'SXAA1bRkI8W2PgutVKUKIevTKbbNnMD4EcO2GVMYJ5PF4st2ZkQ5ET6KLwA3wvvIXQdmiHuU7QSUlNqqqEjXxYwMPnb5LZCr8bcjiZDHlfYIfKYLD59EeiBCXZyIISMl'
        b'jpVOZNwV7IqM7u24KVju9Ieps076wzVwT6+gij1ioShbf6DmAzETZJT33s5Qp5Z9Bjjyk5JyXT91u7b9Df5ayMAopYYiyRb1Oe0FLf+yqviSetFLC15ZRPLJHFJbayBz'
        b'Qvu+/sbzC0Q/7//qc/sCUNY3gRXZG4DpUBCNIxfwToYAO7UuBGcFucKwQ0la5uGmlXPswobATC6BfkDpDDmFD4eSJtzRPyKNtIAeJV3Cj1IpGBvCZ3AbSCVN5ESmU44B'
        b'KSZ7gmeQ90aWQAC3WM12kkQ1a2QN5PoBUQKyFNBFJ2gWB4nz/x7wcy6Qp/qnzQn5Fjcy9ET1Cj7bTFVqhT+Vkyh7A7XAp6hIMHXBb7+iomU2tUFIEWiirBRwpsxkXtkp'
        b's8tFFib7dEp1eq1BY2HiD+OBjCAyRGR9cpDXXjUgYQh0UvLoEGhhGS/m7B8+QOYn8ZMEymwUJBLcQPb4Mi0iHZ9Uc0jmxxeTA2SbZzWCClVuagRfKNaIqNpwkC+UtCGN'
        b'9CioDce4TRyoFDKGz96d0plGINcrv+k3Q1uit5pADYvMMGs1ws/HgWzpPaZNfBM8T2uusZVZqtQ2S2m52qCVx0ISHc43fplaa41VK59l1lusEEl1iscvwHD/tg+mKMNk'
        b'tJqSs2GK5aHTNGatxQITbLSurJIXgA5oNmrLK7VGRbJLwFKmLYOnVW3UeCxnVFvJfbNBJZ8DADJB2Xkms/Fp8nmqrEKrN2rl04xl6hKtItktLTnDZq4p0dZo9aXlRpux'
        b'LHlmgTKTdgq+C/KsyjRQolTJ04wwYdrkfOB6hshpFWqNSj7brNZAVVqDhfJCA2vXaKk2maHmGkcbZmtyntWsJke0yXNMFqtOXVrOfhi0emuNutyQnAM5WHMw8xb4rrG5'
        b'FHcESpbT3lHtWW7vCESp5IU2CzRscOm8PLrHlJjkDK3RWKOSZ5jMUHeVCWoz1qhZO1p7e1r5bHLfYNWXyatNxm5xJXpLcr7WoNVBWooWpMgKWm+oPUrhSJPP1gLukJM6'
        b'q4WOkk5p99zy2ZmK5JnKLLXe4JoqxCiS0wQ8sbqmOeIUybPUK1wTIKhIzoMlDJ3UuiY44hTJKWpjhWPKYY5o0H3WaEwFxWFltq0SKoCoTHKSmisq6KwJ0w+RaSnTsmma'
        b'VmvWAaGAn3nz02blK6ebADb2yWdrQW8sB1yj9dinPVVtq7IqaTtAcUpU9jbtv93m3VM8nXu3QcR0G0RM90HEeBpEjDCImK5BxLgOIsbDIGJ6GkSMS2djehhETM+DiO02'
        b'iNjug4j1NIhYYRCxXYOIdR1ErIdBxPY0iFiXzsb2MIjYngcR120Qcd0HEedpEHHCIOK6BhHnOog4D4OI62kQcS6djethEHE9DyK+2yDiuw8i3tMg4oVBxHcNIt51EPEe'
        b'BhHf0yDiXTob38Mg4t0G0bUQYT2Z9VqdWqCPs802ckRnMlcCYc6wUVJnZGMAaqwFZcgRqDIDQQbqZ7RUmbWl5VVAr40QD7TYatZaaQ5IL9GqzSUwURCcoafiglYpsLtp'
        b'NgtlKDUgMiTPJyfLzTBvFgtrgFI9gcca9JV6qzzUznoVyYUw3TRfCSQay2i+WeSkwaAvAx5lleuN8nw18EWXAnkMBjRlDjOrulbWxcaVhdALIBihtLhbgr08JI3pXiCm'
        b'5wIxHgvEylPMNiskdy/H0uN6rjDOY4XxPReIZwWy1AJfZnMOcgnIJyzOql1hdf4ASuT8Geua1eLMJgAiRQvsuMwlYkxyod4I0KDwZ+3QpBqIoqwXqLRbMMY9CORHbbEC'
        b'tzPrdVaKNTp1OfQfMhk1auiMsQTQ1glxq5mcLAMkSjNq9NUq+SyBf7iGYtxCsW6hOLdQvFsowS2U6BZKcguNd289yj3o3pto9+5Eu/cn2r1D0fEexBR56Fz7rFrsgoai'
        b'SzDylGiXlTwlOcSnntKcpMxDeo7n1qjc5SneTRTreQy9pPcknf2QzDE9t+wmpz1NNiCVnrK5sYCEbiwgoTsLSPDEAhIEFpDQRY0TXFlAggcWkNATC0hwIfUJPbCAhJ75'
        b'WGK3QSR2H0Sip0EkCoNI7BpEousgEj0MIrGnQSS6dDaxh0Ek9jyIpG6DSOo+iCRPg0gSBpHUNYgk10EkeRhEUk+DSHLpbFIPg0jqeRDjuw1ifPdBjPc0iPHCIMZ3DWK8'
        b'6yDGexjE+J4GMd6ls+N7GMT4ngcBBLKbrhDlQVmI8qgtRNnVhSgXMSXKTWGI8qQxRPWoMkS56gZRPSkNUW7jsXdxlllbqbGsBCpTCXTbYjJUgySRnDdzzjQl41ZWi1mr'
        b'AyZopDzPY3SM5+hYz9FxnqPjPUcneI5O9Byd5Dl6fA/DiaIEvcJI7lfprFqLPGdOTp5dgKPM3FKlBX1YECa7mLlLrIN9u0TN1paQ+5TTPyE2lAnxdqnBEYpxC8Umz7Eb'
        b'V1wKdzO7RHePiukeBWqOgSrFaiuVS+V5NqhOXakFNqq22ixUrBVGI69UG23AXuRlWgFNgR16MgMoXIroKXPXa1ix783soX4PTMlz3d0zMhNT1+zIQfiW20VeNpU6mm6f'
        b'ZOF3jMtvqhN2Waq+4ZKzFTIztYmbqXnUTA2ows4HNb+Zqbm1U2KpMuit5iFOAx/3pDGPOVc47JHMmCfiORnP8+Jo5iOGd+IGss9CXTu2ROCz5YvESJbAr0W4/n9kx6tV'
        b'eHf6TCstNdmMVtAbOgNSANiCvqGu0hoe9xeseNT0/c3gGQD+SpApqJVULmg8gLx6IDmQhRpfO8VU9nGz4t2H+IJKQaIxlRu18jyTwRCZCiTJqMyooQaWrmAXkUuen1Eo'
        b'F4pRQxolnxa9xSZE0DTXsLDoZlO7nyDgCw2lFCjzSssN5D4A3wBCiWswOUVr0JZp6HiEn3arS9fvGLuClOyYECbwU4lQa1/bDq1NLkhFdt2vy0pl1/qYrE71PcgMq8vK'
        b'9AJ7Daw5gx4ysF96o84kV8qnma2Orthj0oy05BORNFuMp2wx3bLFesoW2y1bnKdscd2yxXvKFt8tW4KnbAndsiV6ypbYLVuSp2wgZOTk5UdDRIYAGCrsallkTLdICMiz'
        b'tEAwHaZYuU0l7zLFQqSA0g7bqEpOBXaH2i3YXLvAKM8Mz0yeZTNWMD9XrbkMKFQNpSo0PqVAHjde4LM6RxZqE/YUb8cbIclDhcmFTB+gAzdXqmmiE0U8pThRpadiMb0V'
        b'85wooFAvxTwnCijVSzHPiQKK9VLMc6KAcr0U85wooGAvxTwnCijZSzHPibTY+N6KeU5k4I7qFd6eU1nB3hGlZ0yJ7hVVekhlBXtFlh5SWcFe0aWHVFawV4TpIZUV7BVl'
        b'ekhlBXtFmh5SWcFe0aaHVFawV8TpIZWt+F4xB1LzrOR+aQWwruXAfK1MMl2u1Vu0ybOA03dRPyCHaqNBTY2LlqXqcjPUWqaFHEYtlYq6rI12zkkJ3jSbjtrFnETOwUsh'
        b'iVLeLoYsD51mrBEkYrqhB8Q4S28F1qjVgCCitj6R/AQd7l64i5I/mWY2kJsWu5jglpLKtnd0VpBKnHoV4yRKJvZ4VALsI7Vzc2D9wGmoDK1j0nMlZfBWrR6mxeo0FKeB'
        b'qGvV6/QValfqX8j0QKcB2VXMELRHl41EVzFpllZQLbT6EpqUCVCjO2MWQbLpWV5zNQ5Dv6FltcFWWaEtd1iyGROkTNJMHaq/V9Q1j6OPXgTdUHjc9yjohrDTCuTM3EpL'
        b'ZjbZGslkXdKcQY6Q7V6of4nYD++2uEm7fg5pdynnLu22Sdt823w1fFvftr6C1NvipYmol9T71/fViTS+Gr9ab5B8xVqJxl8TUIs0fTSBLXyhFMJBLBzMwl4Q7svC/VhY'
        b'BuH+LDyAhb0hPJCFB7GwD4RDWHgwC/tCeAgLD2VhP9oDHa8ZphleKyv0Z73s+8THWzOixUejrOftvRVr5JqRrLcBwqjafNo4HR2ZF3s6Sj3T4q1RMV84CTtKEQhlvTSj'
        b'NKNZ2T6aSEiT1MvYQYtgljZGM7bWuzAQYoOgT+M0odCnIGijr0bR4jg0EFDfRyfRhGnCa2VQSzDTFMoVUZ2yGdTlenrevG8ifeQu/xzRcoG+CCd+3HIoJGYKZjP1bXzM'
        b'PK+p99RjmaBeONUFhd9j6nHzmLkXU5+brlLmOEcpczx9KGkW6gzxmHppPKZIofDq9FFrqoFymYv0mk7vUqAfRiv9GaAWVJwiAwiA1vJOWakNlpaxdGWnjPqa6tUGu6OG'
        b'r04PMl9RJSzrctZ2p2hmwdxs1kNzEoRLZXbs87H/MSeeyeiJ80ne9dJ6n3ovnY/dP0jWINuE1njXSFfLmH+QN/MPkq31XoA0IuZPIf7bThiw26TRf2lC9/Q1Wgs7h+Wc'
        b'aj1zcijVqroV6RYxAVQRdaW8a2om2E9gAbmhpiH7ES/7HKmN1m410H+hKUAlrA4apVDJp9HyQE9K5cwVUG6rkgNVTZRr9GV6q6V7v+zdcELFcy+EZM89cG6AfE8f4r+v'
        b'D+7oMEGeyb5pF2ZHZjpS7R2zeO4L5UGU+gPvUMnzy4EfAPJr5RZbiUGrKYPxPFUtgneJoLhCTXI1VAFhof9ygwl4k1klT7PKK22gvpRoPdaitg++RGtdrqUbwPJQjVan'
        b'thmsCnYAL6lnWNiXwQT5dPsveSm1IIY69x1dLI+KnmpxLKEJDmy1OIFJz/uZzPJQwYulgtw314Ay3lNFdqepCUzzolIKVCPgiJ2whGrLVPL46KgIeWJ0VI/VuKzhCfJZ'
        b'NCBnAVqdTm+EVQN9lK/UqqFjYUbtcroJWp2gilNFhym6T9X3uA37CYcSLgwMRHKEpp43F/sNerYY2SZRrrZrWQRpysIX5pCGNNKSEQmcbWf6HOpVmpqpIE0R2UrcSFoz'
        b'c1PxxdTsrKy0LA6R7fion4mcrmbVvp/nj4Dfys/lF/tt0w5FNnrAk54FO+FSb4WE1ixUS7aSLZnAQ/GWJ+utXemHqoJZrTune9PzE1XvqIszW3RKZD81dVHuemoqVaUM'
        b'o+dR8CUxSiCN+MwiqSVkCjv0JZyPE7GTdKm/G1VsaBqyHNkoEZy8Fm94YsSsX6QBKm2KoH1rVsxj3SJ15JTQNXzH7IuvzSD79d4hh8WWGqjnq5OPh736a+/1UX5175++'
        b'df3u5p23N4pkc3/0SlND39DUF97ImrQZj/ziP/nXqky1V0bn7nijbn7531ZZ3i6JnJAW8fOzhQVelceW/GLSt/GhvM8SfuIF44j3cicZ8t4ft5R0Ru2vnWKMe/Y/vzzw'
        b'ux0rDIe/u/fmxabHmcOnHFUobu97VSEceSJndKQFN3UddxQ964P6jBHp8IFA6zPUNNeCT5HduCnHCUj8SANzzqHBZJO4hlwczhz98b1KqS/MqCKLueSKZkXyqD+uF8ti'
        b'FMLZrfv4eirU4gq3MZlQy4CRYl+/BMH38gFuJtvClaGpSh5JF8jwfl6J232s9KgsuThqEW4ix7Q5LuAKxpdEpCkUbxSOiRzV4kvhKgVpjEBIWo334wt8LL48hg2D1Ped'
        b'DeUPk12k1QVEUhRcLcIP8FVSZ6Wy3ZzJM+hQ7QIa7aQdumgy3oqiSJ1UhfeSw1Z6BJbszvOiI2qKCFPRnKSFtIJMhxaokdwi8cfbyE3W9YoIsg03pZfkCOZNaFgJzeI9'
        b'IsCMhjWsKtw+lDx0aZhsWUH2g3DohQbj22LchA+tFgROn//yVFnXqRTmcUoPxaJ1aLWUk3KBnMz+pIfHZOwAmYynKVKuJsjBh52nVbIdHWHepnQtmOlxL/NU+phGHynI'
        b'cRRmOurdZVUmlOqqZJqzFKvEw6Gax7T71OcSrUf7hrv6tXbvqtOrmbP/MX9S2p/VaKngrcxlK7hO36IukcHhRsu7zVynbKJBXVmiUU8Ognq+onW6tOdI+8ZOxO21ORh+'
        b'KDAHjdJkNKxUQGMijan0eztWK3TMp8gpRHjulzkVHv2ozJYGP74ZIbQvFPLQ/Pe2Wy6026fIXXDopfGBzsYVvQoXP6gbdrh4Fzn4di8dGOzsQEiK2qJ1svr/rkEHi++l'
        b'wWHOBkf1KAb88KZlRXahoJeW5V0t9yg4/ICW7UjmV+QiR/TS+qguSH+PrOGhD27nCtjRNr4eOY+2/aBTBY7qup0qSLnxNxE7Ept4c4dwTKlc9xn6WfNrzR/4Pe938PHY'
        b'EjT5uLjzCz8Fz86ekUvkUl9yk9ymRLwbacb7FAKVP7AoFjLgFnLGTW93kuatFb0dNvMqomvI9ezROviMqwl0oVYsQw9u/nwPHv4L4DEWZtdCHeyBFq5Hv3E7ZNatfoVP'
        b'p5d9TQpO/FKL1azVWjtlVSaLlUrDneJSvXVlp5eQZ2WntFrNlErfUpDJTZWCsimyqss6JSbAdnOprx0atFcBDojMosD1dSqJ/s7T+QHCXQi6ADvQfRv8AOh+AHRfBnQ/'
        b'BnTftX52VVEHquK7Eg+q4jSNxgK6ABVoNdoSut7gf6nd/U2uZc76T6EtMl2GKSJqebmtTOuin8GMWPSg38iF4wxU1bJorSp5DuB0t3rowq+kmy76yiqTmaqVjmKlaiPo'
        b'KrQo6DlmbanVsFJespIW6FaJulqtN6hpk0y0p86TFhUdqZ6az2Bl2au0q0e0zm51QNU2i95YxnrkrEYexoAV9hQzMss+2nJq2uje9275Q61qcxm0oXHQIFpeTg2CFqpq'
        b'WJbZ6OyWmNWlFVqrRTHh6TV4AU8nyKe5MRH5QrYFurinYrTlCXJ2gGHh9x5j6LEWYVlMkOexb/lCu1Ndj/kdy2eCnJozAVRMs1zo6lTXY1m64EAnhad8YY7Z2nM+YUlC'
        b'VuEHayNCnpaXo4yNTkiQL6QmzB5LC+sYtM1p+cq0GfKF9n3BxeELXQ9p9Nx41/Kn+rMQkNOKXF2DeywOBAMmsxyWBixXS6lZX2W1cy6Kp/R0NVtb0wwWE+CvVuNR9Qd0'
        b'orkppzGwK3QYsFXyGYL+z5boM3lWdWUlPc5mfKZHSwBbDIBY0IEq+9LS6NklPmqY1uV64GjaFQBx+4LrXg/9l22yaoVlwha/1lpu0gAlKbOB8k/7oq6ABQiLRguzU6qV'
        b'm4C1e6xHGBJdNMywYRGGqbe4dEklnwVEzUGQPNbiuuyoGQRQnV5RVGqAAQu3E1m0nksW2y8oMpWyngs7JhPLrdYqy4TIyOXLlwt3T6g02kiN0aBdYaqMFGTLSHVVVaQe'
        b'gL9CVW6tNIyKdFQRGR0VFRsTEx05IzopKjouLiouKTYuOio+MXb85OKiXowOlPt1PysYnG2jGhSXR5osmYp0pSo7Yn7/NKqZnQUdb3SepDyF3BUuOLlB9uI6vGNELASi'
        b'UTRZr2ba+4FM+0U21T8O/CpXg2zUuDkWH0/OcHDzXNJALxRJV86lR1nnhtKjofPJttWgysMv4PN4B77sTXaNwcfYnUR4K+7A60kHaLJU3fNCErKPx4fIFj8f4VoWfA4f'
        b'hsIdKnrJBT0yC9WTFhE5lgVq7Qh8SkzuZuEHzMIxRVJDOkBrziog26rsA7QPbw5pyIZyzRkFVfDIySyXpJNdYkQa8UZfcjKGnGKdkZEd+KavSpFOruM7oGMf8UHe6Tw5'
        b'Aor0GRtViqetIo2kIw2q4BDZWCjCezi83kIusXuRcDtuxh2+pCFSRbZAuxH4bHpsDKjHDRySz5aI8W5yj83u5MLRpGM05AvjEJ/KJcwnO9ns3lznuGXorZhTXhGI9Ske'
        b'XyT1Fn/QtG+khUFltGnZIp6q38dsVPCKHaunyf7+KrKd3MgkV4vJ3XCyQ4QGrhThC/jicAZ0crV/H18V9ByAk0ZnRYQSC/uTO+I++DLZr7+PcySW/ZDPZBMpX8/ywVGB'
        b'kvcS9d/8rvPQm4e8lv2h/328viRx7qLTQzZFndk2YGJ7pLzj6xXvR/fdtGve74Le3Yh2BTWe3d/6ydwJz5srMp+pV/7ss/Uv//SjM3mma7Pb9uy9sq/jsX6ab+Gbu+fF'
        b'nYi/WD79rT/u/vtXL9bUVZsST4/d++s1NW9l/+WnyX/8/C+/UKfd6viF150SS8XwK1u+ODLw57dGpM0LX5j/W4XUOgw6GI5vkzO4jXOzsgg2lo3eVoYx6+PJzgxPVgc0'
        b'jDSHx0pIqwQ3ssPy5AoGvHOxtETyiLThRmZrIVvCBcl2I96UB9N9AZ/yZHQ4gpjpx78ffhSerUxLy8qIIC0KDi3DtwaQ++KYyXibYFCpx7fIpYyI0NSBYugPQBGf51cW'
        b'5boJpQH/7WU3PZ6N9VFrNEWCGMek5rEOqTmVHo+VcQPY0/UjZpd5yLiavk6pt6sOu8HCXxCen0WOTb1C+qB3dJgX0cdi+lhCH0X0UUwfandZ3PMpX1+hzq5KipxNqJ1N'
        b'+DtbLHa2w+T4UibYu8rx74x1leM9jUjh3emnoQ59djmp01+Qfh1BqbqSfdOrS7Sd3vZd3FJtpy+VVUBCpD5eQh+cwyz1sRNiamQJdBDidCrM+7iJ8wEg0Pexi/SBVKTX'
        b'BdoFeh8m0PuCQO/DBHpfJtD7rPV1EehbvXoX6NVOFz25cFXRU4itM+mxBiG3HHgnzBNIpCAPqF3v36MyQ4S8zGyyVUEqiMrq7rzIVFmiN6od0kkYCC5hjK0KXJXq904/'
        b'TtpBp9rbrSaqBv8/DeT/zxqI6/KaQAElxDitWt+jibitR6G8EOWowKM4tvB7fDt7bE5Y70I79iVujxMkWqOJWmvMTGY1epZEl5uoyKivVBt6kHkX9uLdCpqEZ//WHntM'
        b'KZPQ3xKTqYL2l8ao5Fl27FKzsNxUshQAD/q95/1AI9WAkhKiou3mL4oIoL7R6hZ2eb722AknYZwgL7DY1AYDWxmAONUmfalzNS50cZztVQm0E1Z3MLAjdQtdnWu/V02j'
        b'xZ9Q1dxcOP8v0LRStMu1ZXYHnP+nbf1foG3FJkTFJCVFxcbGxcbHJiTER3vUtui/nlUwiUcVTC7s+24rliCN30B6GZ1fVdwMZIuGyHFBqRlpWaQxIo3KrmPJRaZPuapR'
        b'Dh1qHX7gHWcYYGNbhffxUZBxOybNd1Oh/PCxDKad4QayHe/JUKVngeCaZpeK8UkQVj1WDXJukzc+kz3RNpUWPoIvSCw5WTn2u4po/aDNQe5W0gC6lA/oHVAjhO/kLcIH'
        b'8X58whvh83jTJLLbN3vcRKZ64MuWOEt65ljSkpaVk0FvOYoSo0EpIpDcH+DjgiPXeX9yzBKWRbaGUlFdlYYvhnJoRDk+VSaR9PEVNJiGeWt9yS28da6MtCizI8xQ+iyP'
        b'gmNF+NjquYKuWBtJ2kmHXu2yHw3KDr4xl97hGY2bJCsq8HkbVSPGGast6axHaREKvLWE3gbaj5wQkXtk1wAGozMreDS1gIqqxZnb5o1C7LLRfLxb6SuFb3IHd0CobpaN'
        b'qsgzC8gFXzo/MIvbReQcuZWaCbWTneQGVTub8HkIZZKtqVTvWhQim21KtlGxMHroUNIB32nexSiNtA60UUEXH5TNZHo33h4FqvelFKY05oIivItec4oiyf00FFmM9xm+'
        b'/u6771ZmSNDUSQyVMpVFecIu+ySbF5LNhnHKi/0+XmBDDJhxaVI6KS12NT01Yh69ajgyvQBQIJU054UqABFSnZcLK/BNNm06fFtq9F+8bjW7IgZw5wSuzSO7YtNFiCMH'
        b'yS1yAZELs8psEyB1ecJCXwYcfHauE03I5WUFMsfkuMwMvkR2iBGuL/B+tlJuo55ZI8nBags50V/QdkHVzQ0lu/JkTs2WqbVT+ksDyDV8RLiLuB3w+4wlXZmTFUkxJ9uu'
        b'2yqSAAh7Jfg6OTuU9XuFluwOJ4eDhMttFFLkix/xpCM1nN2si8dm8z+q+a0/qlL3/fWCoIKDgstEOt4I2nGH3aAheEoAVpEtkTlZs+fnhtorm+fqMHEIn/Ej26Knsltr'
        b'V5L9w8K1ZKsqLQJ0fSlu5SOri2xsd34zYNDRDKYI8qRhpZlLwrVkq0LEUoPwBXIzfAK56FKQHMsXLniuBzy4Zi9ZSG5CSXKqhg0S35hH6sOfeXKQEYF6/egXecsU0IxO'
        b'1b63eNukbDI1sK6s+lfVB9d9u2MQ7t+umFvlNTggilfsDow5+8ZdtUK65Znjp6sKt0798Z25fzlom9kR++fXztzqOH9y0rBLir37497aPnaDiKjfH7/r0t3OQdH7Xw39'
        b'Irzig7TPwnb8fcRKrzfP/inVN+aP6dz4qVm5/2oP+aTq3eyaj+faJvic/uaNRYvfW37m8zvTZm01fKx6ccPnmxJiQs9+s33kX8tntk4KeTHguvdvkvZ9dlu3r0b11tLL'
        b'+z4au/3x1j+0T90xtJRMejNn9Z77abv+kJ91nh/1qd+zO5XzMw5Nfe3obyac93/97/Vf7oi69/dZK6ZVvbhw7d3tK19ZYTFVfKpsX7tv4zfGZJPvuWF/r7qWZJjT5q2L'
        b'PLDh4PJIizn3jZH/iA27X1H98e4vhv37d+3HL3++4fdfvvLLLz7wD2987L9W+2Jmyq22R//hPn/NjG9rFf5M2R9NDlcJBgh81OBqgxhDbjMbxAyyN9qzCSKc7Mcd1AZB'
        b'tiUJvhib80i7iwkCnwfKb3f3ACmEHei6k0mOZ1BXDXzWYvfW6DNPZBgSwG7S8iXn8MHwMLuvhvcyvO1ZHp/C9anMDySKHMdHw1eYVJTGR1Bk2sor1yy1UvzEjZG4IyMz'
        b'TAo4eBu3LuYSyb5wIWX32kB8PjMrgkdi37wMDl/DuyVCZ/YH5wIzaMUbHS4aSLqaH6fGx6z0ym/8YDFu8eTIgeR4G75DXTlOVQh7gXXBgyBjKm73uBUIBOIYM9JAsZ0l'
        b'FrrElJRZsbkOwveB9mwT4StrEoRetVaT89S4YjetbAdyeZ5fiQ+s6+WCLEXg/8jc4snwEkBNDF0aODO+5FPJYB378H5200uXAYZeWieYX1iIp94jwyG1HydlPiTUnyQY'
        b'wvQ6YhkfwDxMfHgarhnoZtjoatVurvETTCYa+tDSh44+yuiD3q9o1jvNKE4Thoulxutpbi32EerUOivWOGvSO9vxdzbRZbOpgEehm82mPczVZtPT0EoldkmL7oS7X2Mu'
        b'qfeqR2yDlKv3YZYW33qx8xpzSYN0E1ojrZGuljDLipRZViRrpZ6ufqWVj0BPinEBghiHZthvgB8Q7v3Adw7KZ7FTkN1IrruHUvPnIka1h5O9uNaCW2TLRPjUWiQK4JIW'
        b'4HuMh8lglRxSk5N5uCWftBRk5ZIbc8iNAv+EqCiEhg0U4Q1TpjFRj2zGzfhqHmnJj48ijXET1oIcJVvGkaOaVcK5z/YqvJ/Wgms1tCIOScI4vN9CNjEJAtcG9yFnn6XX'
        b'ltM7y8lWfIzdiI7X43PJ5AQ5xffHbQiNRYMioxgXKp+Nz2eoovBhsjUuJp5H0rUcPjx2FGuL3B+Q4HIz+AKyBV9lF4Mf1DfN2iSx/AnyLPhV8cycB9miaL+bOzM+PzO1'
        b'KX/ktrCrX8ozL/hlGuaFLx4TeGjC228ph6+s1XwYtAKNPb11zdCDnxa89OVHq4sm/3pLyUY/vlAvvy+qe/5Pw68/zn3jjS2jxn1b+fycfuT4+hXVhf9Y63tv3Kwvb8lT'
        b'dyneapucGZ99Y95Ptw32CfEanVT3z4WvZE+a+UKM6U/G4tAzIf/6R+TfOhfkLK7pO6153ZDlZZcO3VFl/mek6euMHy8b9JfyxD0fDfvu6sM9S0XBSSfDWxb57w06FrX0'
        b'zdU1Hz3T+snaU+8HLdkTPHv5K3/5/bc/av2F75wDfzRMSfvVz38Wca+sPHHdRwNybxwqVASzuy4Lx5EOkE6Osev4vRCPj3MFy5SMpIJE0tFXoKlDS5GY0tTcRIF4teB7'
        b'eijRQrYsdiGpeLuSedsFk52cO0WtDHXQVKCnA/EVZhnPAYnrSpdZPBHvcFrGd40X2jm6NCMjOwJEvNbIqlR8TowC8ENRETndj3EK/IC0ziRNdAdFsnolEg/n8HFf3CLc'
        b'1nhzKb7udmH1mOERIq/MbMbD8D5y4NlwlUK4Bx4fJVscd8Hj2/iowOZurNBluLqvcgvJfjQAXxQPWUU2sywjydW+uuwMN2dUDgUvpdsYtf0E7tIWleSRr5IrwxAz7ZMH'
        b'CcxFMg9vIDeoZ6rDOxE3DAeJqM9w0RJyE19ibpbeZPvsDLsHJNmT5GCroFI9Ekz2J/HuFGAq+HJqapfJ3jqYyQBzcDvZKNxeT5pF+C5utN9ff49cYdPpTXb2o/dmzg1z'
        b'uTZzpJrVHELqAqgI1x+q2JpDLz/F23jTuqVPR2v/j67Ed3jSCBfgM7ak6WJLkZTpMHdF5rQopiyJ5+FbYFF+QJGFj5gxKmGvgIYEF0eZM93xkfJiPoAfwPsAG3P1oxGa'
        b'F9iTVxdj6PQSbM+WTonFqjZbO0WQ74fyIonZRH9XOlmO0cl3GMsxwOMiZ78Nk7Gc9egX8h4cfoSO/g98r0TMS0z8zR+6GQ2Es1RWx2ENu/HVYLeJmLVWm9nI0irlamrb'
        b'dzGxPJVdXF6hXWmBeqrMWgv1ZRRsN3ZjlMVpkLcbcjzZs5+01RsECxjtTslKq9aDrcnJQaWuE+biAG+jHsIZ+EYsiHq7cSumDMRKX/MxH2TNq/h8Lm6QoEF4vWjVpBCm'
        b'F0eayR2yU4JvzkRIhVQrvJnpYCzZjq8yxoqb5ivJ7gyVSoSmFvbDW0T47LwaxpElPoxPV33hX2x4tGoYErZrN8zFN50Fpc+QA4jsKgEaeJIcj0Fh8ZKkaANj3UOXk1Ph'
        b'TkUM9Fs+Ej+KEzjyVSM+4eDbwG7xJTPluPgerhdY6/kUFV3mw0g7KGugqfmT04y1yv3JoTyhEI9buEFk11B8lezQb/nDSt7SCBkWn3su61X7W0QSY+9NHdZ4cs974l0f'
        b'72/c/8HYrHZS8GrSj8Jev7IqL0Ez892MJd/+WfLi5NGd286+t+GjNepxH9W+mv6TWTMXPZqVn2msSmv78Uu3rzyvee5fE0qLlg4rnPTLCSuuHz1Wv/OFE6W5OZPMP7cc'
        b'uxv53bv9Cw88KFh18ad79k9+PSrz48lTRrWPS1l3SCEVpPD6qmo31z7gNQccm6DDyEFG8rhUch7oreOuX3I/lB+Ft0rYxfI2ctU7XJWFr8Ca53E7l0GuT2SEdCq+gzcA'
        b'3yJncbPwKgse+Wp5cpRcUQn+3CczQVl29edmagK5LrU7DW4JYhUtxifJLicXypIAulwSuJBIqpB+D83oweFQbSmiq63rBSECmTSIRf2YPN4PvinRo5upwUDmXCiHvWj2'
        b'D/RFXAaP3z9BnA734I1ob0LBdYqr1NZyzxegJyD7xdN0m5G+A0HqvARd3OMl6PbjZe+LOA9bjF30ipIOi7qa/jIYXCnX0x8wox2fIE/TycPorzA5kFuLYMymNEm7gp5p'
        b'pbbdMFWNviosgjVkJ45mz6ZhC724T+M0SKvNpeX6aq1KnkPt58v1Fq2TALI62ABYdrVcZzIAse+FmlEQOQ/wOamZLNumoOTgYLRPeGoEuUIPsKSCRp+elYnP5qfii6Qh'
        b'QgUiQCrZ7FWFL+fZIihabyooyaA3tJyXpWepyJZIfC4fdPSmyFwQNpSh+KwYZZCbXng3uRMnyNy38KV1ZCc+T91WyG2oQ2Tg4Nf9hcyYWIJ3rsan5ocD4FegFVNmM4Nl'
        b'7DR8LjyHR9wYfH8uIvuXxOu1r7+OLNTqGJnw4aSW5AA+2m/Gi9kDFqw9/raoShow9ccS5B26Piw4WBJ8pKRpRorhw61bO+8oXn7mZy1lL5h+dPDY6IQ3L9ZcObF5yeh3'
        b'Yi8m9j3x9zNzf1JZWB4UJJ+XHNRpG3sqJ82vTNLinZ8z6frAq88d67S8VzxR//idAy/VfrqsyfqPUbI9WffiX/L9R07nYN3M9o/W4c9mBxoPjLp6eNS94+//Y/QCk+1g'
        b'++NS3/ox895+/9yzl3MPPzz//rii8bv/IFb0Ec627I3Dl2CmuZlUCBYncvgS3ow3MCqA1/cjF6iYyV5gRq+V76Dnnvg15OhyJgWTfQtGQ9z15XaHD298hh+3Cp/oa2Si'
        b'WT6uX86Kb4kAlSebJ2cWDwURb49Q+YnZM6DeLRGqNJbuS67w5PY8cp9cixBOAJ2MIo8yIvDWHOHqf9+p/DTcDMpfM7nMqgfV4MA0WkVkDj2Xs5YH0nY6zFgkvOBjv46J'
        b'hQoVaY3A55jBqE+UqCyDNApSeAvZQPa6UFh+dv4ofIM0s7ZzcAfuCI+kOwhKFdmALyh4IH9HRLguTcyUE3JyTjoTryNBZ5NO5Cvw0YFDk4R3xlySx2Q48dR7grQfj4/h'
        b'nXgXS63BtRFUP7FPSgqP75P7gybgjWxCF+HL5IogCSu1zvc4kavQLar3SPHVRKFX0Chu55eOjei/ujerzPeQahfyLKZL192thX68BbuKjJ2/AboMIqpgJwmG2Bp/J/mk'
        b'pbPd3gpgdqfRvXSSF/J20W0rPL57gm5vGuD2lgC3hh2Hm2fAI9s8k/6k+zVAS+z/FBLhi4e/vk+cpKee8BpTaVERO8bTKasym6q0ZuvKpzlCRJ3dmacMM70wYZgxHTYC'
        b'YTb6/c/tYr3C0Uzf0fEhsrvIyMRinprCENdvNG/XKb73yQeI/ADYiBug8uP68UPnDE4MGCJskLWCPldPbo6y0FcfWgICRMh/GE+O4eZsGzvL9ohsxht9cbuVEgzfyhK6'
        b'AzKH7nwMjRGPIkfItv/RK4Vqnzx30X170CubEe1ckIB30gMmI4EiRI5MJruYIKokx0ZnqPCVqHjcroPi5Ca3bIiGWf5XFxe6WGN88SFmjYklHYJh6MDgItKUFkHFolgx'
        b'wg2ZMtzEp+OrFfrMXaskFop8y2f5f1q86Lkr247tjK5bxpV6fcifrvPzDUmeFvHHfqf7/bEuszghw8d3Qduxl05viq77bMyxTcd2pe3gRvdl7ylaujhoxf2pColAnh9N'
        b'myIcHcRnjZQAXOBjh5JNjP7pZwU5lWYgFEBAKa3YmyQYKE7Pw83hgqWaNPe1G6vxI3yI1TuK3M+k5FFQmSuymdI8q1DQ1bcOkdHtU5ZE9pF62WJeS9oreztO4gcKEQgh'
        b'2iLqScDIyABXMjKaGlkp2RDD07zcuTrEnWJaoFMqnOfy9AKjlTRqhRO/admRvKP+9fbP+65SnYCL52AuDoeHpitBirgwKB23RApboXKyW9KPHMdX3RCov/3b8qXrnRbh'
        b'9F4HwEpeI6r1LhRpxexFboi+wq2FL5RAWMbC3iwshbAPC/uysBeE/VjYn4VlEA5g4T4s7A3hQBYOYmEfaM0LWgvW9KUvgdNEwIrgNP01A6BtP3vaQM0geoeFRsnSBmuG'
        b'QFqARgWpUnaIRawZqhkGcfTmCa5eDCVGaOT0vok2nza+TaQTtYnbJPSjCdHxEEe/Rc5vIVZ4ioUcLk/xk781Iw/2gbp8uup5sozmme5x/91TM+pgX83og3xhkDZYG6QZ'
        b'E4KO9j2GNnEsNNYRYjn6MZ9A4XiPDObEy37LRn/mLejF5kmiUWjCIG6AJsR+t4Z3EfAU9SwQZdkRazebuLsCIPgcStkr+qROS7ikV0t4N4rV/aSYj2AJv7YYBC1U1Zc6'
        b'NEwYYX9B6iurW9Ag7utyvznFRnP/RULkn0ev4b7miwf1iVIv/MDqg5go7D2pqOsQOd48LjM31f1al1bS5IXyymSBI0uFN6rmjEIz0Btib1TMN5kt6CNHD9mZOv36vf9B'
        b'7PqXuj9zw5qv+q+P8hP/buv0YvHNo68O95taOm27KooL2vHO4Po/fn4isKjmwfaXpb4DFub83rtlyaA2n9d//NrMpdX1wUsfLjj1syxpkVdp3Qv1H/12RvKHP53mVfam'
        b'9a+/yr1a0jml/VDIglvXFd5MRArFN9i+F2UyIkTuklOyfN5K7q4WCNtm0hKIm0DF3YMvs1016Tg+CD8ix5jpdiwou/dSYt0dkQUn5MsFVmatuBo906kCXw11n5gxIZJy'
        b'0ryU2T3zQ9T4+lBoCghseKhSyAV5Bg4VT1yBzwvHxx8E9BO6CgJlK2nBu2ZQahxEDojwsYFSlicHn0FdebK0+Dy+gCDLLhE+QW4Ms28FTse7qea+JTKNNHNoqZeMNPK4'
        b'dr6PlV65gm/098VNy6EKxlrTQsh6mKLWHKD+W3LIVpUUjc+QQgXnyCWBsD614Nd19nq4K8GOkXI+Ehk3iJ3BtpsxuZpg5xp54qWEgtmxU8IchTrF1M+0069rg8lo6vTW'
        b'G6tsVnYDlmfFXWJeS3+vpo91yCEPrnHrZ2Q3wv+Wm1jooX9Pe7RYUkQ73csx02m8fUm4tuI8YT206w7PbodNVVBrBiUpT3nk1r/IdeZ66dIMR5e+Ge7SfPfj1aqnnQSf'
        b'IieUeml2trPZYWmO7A73xh/UqvN0M0Wbokp9b2eM052NDqCyv1xnNlX+sNZ07q2pV/TSWpaztX6sNer4+kPash9hlhZZTVa1oZeG5jgbCsmnWR3usR5b+z87rNyNBfGo'
        b'+4v4GEvYlGHfjJX6T48yZQvc5voIx5GatvT7/Fyk/8tzJs5CbTVRJ3/16eV3i18tSVW3aUL/mKH2031c/DH68kBI3t4fhbD3uRbfkDxu+b2CE4jZw1TcSKkZfgjKsJ2i'
        b'eSJnQ0J6ETmZ8sUIF3uXmINwzaMyZk2QKyH4b48x53WjNpfdjIfdG3n8Hfz7H+k43d6Y2V3HsYNLHiJhJyOmJuwwLNBciWETwl+JKUVzAil6cvPi9e//sx9noZfAvbXi'
        b'uPCK3m2aBc/txXvx9W1nRa/eUqeqZbve072X6YWWPpBuPP0HBc9gRW5woNMJnEc5qkdIAS9uZbxb1I+arcmWMPwgTKmiWsdGPpa0kWu9KQ99iphXr75GW1RiMJVWdL18'
        b'zgHVRTUhLpPtntvtPagS5o7qSY/YitxsDC3wWNANwOfcANxzm84l6YAx1akc70UVAZRF/40myyHP+zsMytl9/s5Fhf7aC80pXjcmMhgJjgh7U8LxechaA1r4TVSDb6qF'
        b'3ZJm3E7q8HkY4Kox5C5a9Qw5xrZqZgzNdLtjiL5tMzS71KDkUBzeIg0ACaWDOUOaksVob84A5gz53IhnEHPu+5cym/+RFEUV2dR9fz3oxdCZiPkqVuOTcxyXDrl5+NmR'
        b'xO7Vhx9NFq4bOkb2+ZD9IJ5uZaSPKdb55Gp6l2KNazOQoFg3W/T/sPyWt1B4fazaMOY1ZTCO6id+b03klDn1pTXemuhU4/qp7x8ublg6N3f74KUxqdnbftNWe/fQO/MD'
        b'/6P7yIT7t/50Y0PVoMrjDbtqDwacafB7P0XdEPiHthFjgx+8eSB4zNqrex8aE5fNiF1rzPrbL6/uSXv580d/vOAre00z6l8pCweUvvGr3xlOhVs3Y8mJB9Orpv/j39xP'
        b'zo/6z4N3FV5M3kzFl3CD3dC4kRwmrREOSyM5M1LY7rlALokd8ig5TR65yKT4IVlvZRbsU3jzKlcJr/sqm44vwkI7TPYzT4ZyWFS3fcPs0qtD0iUngtEI3CEml0eEC/V2'
        b'QP9OM5cHKr1SneAC6MKOmgGW+NyoMOlQfIvsZAt4Db5C9ji8v8juhcJGfT45y0wDHG6tdpoNJo8V9trj8a2ul8/2aGCUFi036+1vF3UTNYsoxea54SBqDrY7cPlxNYEu'
        b'a48VdH/dsdpcZumBjPPmbe5LvRUei7ot9dNuL5/s1lx2qdi+Kt12Xe2vwGWHzpyvwBWz3R8JLHIxW+QStsjFayU9cV5Jt0UuzWYbswV+eD+mnskj9HFoxBRyi+miwoFZ'
        b'L7I7PFc5T4kvjcUPxcgriB8OGLdBX/PiRc5Cvd79L3xL7U7b8NvP/+b5K9vWHLyz886mOwsi6hR7R9bd2XR20/iWtOaRezd0SNCFCbKV5f8EfkxRyZJHTlHV47CFWkgw'
        b'4AV7RS2HhpSLcQNgbINj7ns3IUuL2BkEBuFAVwgbApiPg9sks6wOXaXLmY29sZiZfLqRcLEQ/0ReBuHt8NB3g/C+4J4gzBr3DGBqOK6XAIilzFZAwez1lGB+ihedS7IF'
        b'gDIfoTtWXDeiJI+CdDeHROQel9UfH9BLLzVJLNTQvOzN/E+LM9Qv/TH0gzRBpir+tFivC9v9afFja3hxhe4zzafFfGNUQqzt2qko25XqK6eit0QLb7m2zvX7etaOLonz'
        b'qbw93F5PTe1yLgDt5wpQs0xwZ6H+kv1d5rWrzNNB1vPB1V4AvQMepm6A3jnIFdCeO/RYAwU8gzxOWNMS+6qW/O9WtQPcbLeqcc0SgDXZFZsqQhIvfN6bwxtL8Rn9tQv+'
        b'Ygs9pbB/TP2nxWkA78bhAsRT1Z8Uq9QfF38GUP+sOFBdrsssDS4VXjzdznl982k0rGAKGLKTnMcHBe/jxdnkNJe4aMnTv9K2M6DIfomnC7zdhOoaCu+aQS4T61bAM7A7'
        b'pTp1qdVk7oFMi827eoJyGzyWd4NyUz9XKPfYGUUfwWm2y4eWQr7Tv0unrtCu7PSvNtlKy7VmViTaPRjT6VtK707R0jeTRrsGYjplGr1FuPSEuuLSl7Bb6U23WptVvYLd'
        b'zkq3iTr9tCtKy9X07lCIUsjYbpR5PH1QccnTnbp0X+pZViN1JIru9HFcbqLXuJwFL2Q5rHqrQdspoy+2oJk7fekvxxlrFs1uTWI1xZgP0jJe9NhfiWkFOwjeKakqNxm1'
        b'nSKdekWnRFup1hs6xXoo1ykq0Zcq+E6vadOn5xRk53eKp+fMnWm+QJu+iFwMGBSAFKp0U8hCh2S/dVfKvIW5eplO9t+8HV5kr9J9EZUK8u9fzKu5pLV/k6AodfJx6VKB'
        b'hpKr45ZYyE1yEbf1AdzhAfXDEvAhtpEzDzdMDxRZrNXkZh9yw5dDXmQ/H4BvLbIlQ2oV3oxP0wswDpoygOulZqnSsnJJQza+GEFaI9NzUyPSI0GUBfnKcXqH7FzoNx2E'
        b'rVp2HoXUka1Lq6DpnfSN8jUoCx8hV5nsTeqUK2LjosRx5BLixiG805ccYMydXJ1KDscCXsemVqJYsi+NbUXFrMF3IDsPknct4kIRe5X3XnZhRR98D28nGwOdbpoc8i3k'
        b'ySUQBA8y8b+6AjdAWanGC3EKhHfhHXLBmapxGOgDR0HyZC6o8fRt4lc5sjMcn2BzuTU6HJ3kAaSBxc+sG7LYzo8a8vFtqI3DW/F6xIUhkDYvkU3CibE7kSEZKqWKHm3L'
        b'UpKrZBdpzOTQQHxSPHXtWlbnJxPlKHBAHcxs8cRnvQE+dJaSyVnSBnWKSDPeh7gIUFhs89jYUpbgm+H0go80YZ+pDwi8m/BNUUkk2czqO7JkIApdtIQevFpdPbgMCXpN'
        b'u38BVOdFtoUhTkmdZTdLGXUdj8+SKyCWjsEPI6i7hziCw3fJvhVCVTOnoAVV/0Yoqjjm4/ETBDfyXHx8bmwcvoLI5fGIUyG8n+zHV22Cs+q68dT5aSE5nwWKkXc0j/eS'
        b'k/guq0w/KgNZh0RwMHc+jwsXCv0qWFxI6xLjvSsRF4nwAXzSmyFhDmBI43QvwdOL7dpv5keR4/giq6tBIkZtyUFMyfrjoBRhzvAtXKeKjUtAE3E9m7Jds3E9c9DTJ4IM'
        b'n079cMlW5lqMAnAtuUhOiCaTe+QMq3LP2CT09oyPECouDr5bNlqokjzCp6ZClTxg7WU22D2iRTY5ZYTqgUKN2QzHRkBtFM0G4zYxbkwg7WyqyLmJ+BoUl5Lr5Cwb395K'
        b'cpGB0Zccm2ivQIBjQBU+QK6IkkLISdaf9SP7ooPL6WZ08dCPvGcK/Rk1HjfGxkRJ8T3SxIa4mxwYy6beGEhO9w+zoy0PaHuNI214Q5L9vFYFPhIbH4VgwSIuhhUju4VF'
        b'tz1k6vTZ4RnUn45DUj0fEpTFEoYayLnYxCjU14S4JOg4uUzOsZ6TJtyIt/nQo3AMCxvxZYT8JooCyY5BQmvbyR58FcoCVZmCuAmAISvxfgbVWHKfHJo+PENYlQrq/u0X'
        b'KOo/uS8b8qu8NzpZPZqCwFAZXSwMecxYfCw2MQ6RE/gBq2wf2fOscNTsOnmIj8fNhX7QY34ZgCSl/JAiUsc2sL0SaP/jxOosxCVDF+bMZ50rxHX4QEYGvoBI7TDEm7ip'
        b'5Aq5I9w4dCQWP4IifFBfxE0EXLROEQSQK/PxjqzxGZSqNdM9Bmlf3ht3LGN9/mJJDYrg/kSxet5d/xChz/PwAx3uiIqT4NZ8xKUgIHHrZYzABJET5BGoCfgYrk2nGx4i'
        b'8pADwN/F+1h17Wtmo6TCoRws3vSJC012AvMQZvwerVBE6iYibjrCRxeR9azTFlyblwE0RZq6EPFLuEgv0sQqil4YgrY9o6VzOfQnKauEpWtcix9kpOGj5AB1hBGLOejY'
        b'g2XMc4scSfEnO0GKUPktRKrJ0cw1NgZvK2CnBeamgtarpIc1m/LyIoHcZ0UA+UFodrDXkOGJ7DSrDm+ihIQd7mwEAkpXg4zs5YG4tqzpunz5zgARak6kniDFET9NVQhH'
        b'WleSM6Se7AThMqKPBEUoyBF2lpbcwCfx/YzMgeSm+04cMBsxGoPPSWzjgM6yKbrRN5mcnkOacum5FCBjwdzivuQug0YevjQuI5+0iEn9SMSRfYhc8RKxRVwDOlpdhops'
        b'Gut2NBl6PiZHoh+ZLZDOE/guPkgO+FJA5PeHx9AiVnpOSXg4LIb7CyOzyNZUZbqg/UWL0dh8SQy5NpONd+yzg9GrxUspx1hdsWSCYH16Zp6RHAAxGj9aVA4PUkuO2piX'
        b'6cMK4DWkKQ3fda+TR2MLJLH4GrkhULozcbKMXKWUXFgIA7pA71k+OFLg63UAo3t5WVqyP5eeJ+ZXcUPJwYUCdT6Oz+P1GQV0Jg6nQMFTiFzHW0vYFU6l3Gx28pvcH+U6'
        b'DyNwk5jcxHfIPoFanIcSW8gBf3roe2UePIqzGVGoMQbTRa1Ky4ZiadmDlDFiNATvFxtIm46VrAKMv0QOiOjOX/gEes5jwxpGm0W4FZ9zKUtavZQxPBQ+IK6cTDaywrHQ'
        b'JqwaSsnxruFID0t2A0M60uxN9lEHRmeH+/TFzeSIaCmpW8zwWr08RLALrBuFRphJg+B3faYE14cLt2QBQkWmARhbmZPDUHxDDOh7EW8TCPgtWJuXyQEJvQ8bPwBR4R6p'
        b'LWU4i9tC8DbSBFJJhYQ0ooqR6YIE0Tx1YYZSmYYvhKavJIfoOus7VUTaSGOOMINHSSsA34+Sr7jl8BhBWgXPyva1mRkuV2H3mZdHrooM5OZ8BvLh0D2Lvz8/mtwByG1F'
        b'5GIhuccw7L7NF2kmKSmGRcQkSwUMC6bbv00wbhNejw8gUzm5zuSR0ky8HcS2VLJ1uCWVXkOmTKddlA8RkytFA5itcsu6MdwbIpT6wGuq8d2kP0jTEBPClk/BZwWLacYq'
        b'WDi7TPqPR3wmsvwLRFtvRcHiN98xvjUnUPre+Be3vHU964PNwSXVP3n4536dwaFta858tvD216fSo88dD93zun/Qm3dSBuS895XPRL/W5yxRhw8WDhiYG3Pko+Zxlhe+'
        b'nrSx8a9HA97t815LeXvm+F/sfuEnX0+KPL2tM27u1cHWzWPa5mS/cvXauR//9NH5vUdHHWp/3vThmcnrwr7IvVq4Niuk8iftmw8+1uz/cN+2qIpJWyr+fVrx84spJE0e'
        b'8+Kb1mtZmsPaezt3vxSw++bOOZpxr6jG3Zv59yuf2a7laNYd+5LbLtm9KTtgy1DdO5980fDSz1LqX5yxdeAnBwPHv2z+ycv67bF1E8pmvt7/9/dfkuxuylZtWaS784Em'
        b'9/dhr8R/+s7KmVs6/1068fAHc1NPx7w+9rtfbVO8fPKdqeXfvjHyVEHEwvhfTlF81X//xD9lfdXy+owlx73iDv44vXpTRPzWX18amzl2dtCy+1f6L68w2Hafmnhi+K6k'
        b'Ja/EfrI5UfqrjlXDtf/47MTO3f+8F1Txm21Lf3fl4MffjjW+sD9x5L9yzs+7Ou72mEOXdWULD77zXV2AseliVvOn4tujyj7/cujnL2v43wxcGRU08eBfd7z+fu7NfSsi'
        b'+h/uFzZx17/L/rnYa4Xqy2f2SJc0Xvj1yzelK8b85dPVX/H3/2kaMnhF+JeqKV8t+aDP1+Xxk+8c/GlJ0df5e1b9525Q1c25v5m/pea1BZE7Thv7Xs/+Rcu6sMD/GEXj'
        b'FH2F42ExdDMfr1/owWWCegYkZjB124QvVoZnK7l5eDvi8X4uC++NE7y1rpO740AU0g4CNUKKxDM4IBDXBG+C9LJVuKlPlZ8ZSE9Ln+oCstvfW4r64SMiEzlC6pgxGdcq'
        b'I33x2YhUmzIswJeZiYPIXRGs4yPkOjPPDsXtS6jTF97m7/D7ogelTgczp1ct2UB3ayKBda2rimAeuyd43ERO49uCv+7FVWQ7MwZnkh3zmY1PlsVronCjlSkoB6sjYClx'
        b'uTMRX81Nm2NiNl8vctJCbkeFu516XkA6BD/Y24X4EPDWUbiBHXCmR/EG+7OkWUtKgdhsxU0ubhoR3myc5HR2pNNDI4EcdzGIP1rEbooLB4G2rctpAm9S0jsHnY4VeINw'
        b'6dxm/DDaJdfZrKwu14q5eDc76DbCDOJ4Ez3l1wKqS2MmdSgGyeXsSjb+8PESfLN0IQP/YHyLXIXp6zKD4ib/LksofpTCZjnEWuNyNIIeixhE7gMUz8EsM8nyODmRLPhy'
        b'VOAm5s4hOHMMJ7c93TX/g508O0VqjWCloX6mTivNOqSiXrliLpg52vkwb91gx4cP5rp9IG6wVyA3mp6C5gZBCfrnx8n4wZycC2AlArkAljOQ5Q7k+tHa+Rr/LvML9MXN'
        b'8Zfa1X7oMTNeKNVls78Ej3PUBEQx0GkCWo/eHuzmBuzWC8/75My6J7xYCdVLnNY9jhkmnnK3nFYsR08aJsYJhontITzyW0t/FWf+KtSEBJMf25070IdsxVQaHV6oQcNh'
        b'3Z52qGMbyBG8k+IS3g4qaAhuThQuLNlEzoG8D03ELJqMYqyRrIX5oTL0dcJYKgRHzKxcjNgG3YUx3qghfySNzAxZ218QS7euXMNNzfiKGkmG9H12gqCcQpVblsfGiceT'
        b'DdDCLlRK7tnsShNuWBIbJ13iA/F7gHo4xPcRaVJUnD6c6t6ZuWNGCnV/PDgI3Y9KoQq+33dZBqEXj/sHodXDp9LIiCUJzwg5/zXPDz2H4kG0LPbrBzIbyzmOB+jmJ9LI'
        b'COnwFCFnlQaYfoDA9N8NWSLkHAGRXwwJZZFcvkKInOfvhRoGhbB7WF6ODxA2DTOiSV1eFkiIBVSSllRzaliEd0HM28bGF4cflsZGRYkRNxq0OXwf74gvYM0+mvUM+vpZ'
        b'KogV8xvDZwrS+0SQ0g8JooGqENUkkGuC3NwSP5scoDN0U42vwRNfDGNQDBxGRSopVdjJIbKeft2KF+C7ixwGIrAT0EaJ20BuUS7DW1jDXjIx+nh1P6rwR3wRPwcxWWv1'
        b'EnyF7IRCu0BDaie7JCAZbQZVoBjfFkS0C2MqMK1smD85h4bxIDQyb+xmfGiuiy8y3S8NJhvSvcgpQU4+AzrmwzwllcI4sp0jdbglOIGcZ/KkRuPPTreQ2wD4FT7RgubY'
        b'gc/Mx+fh10q8ezhaOQ/ftes1d2cJe8kB+DhaNRdvYPu2DC6fpInR0DWB7P6l1QUDBMOxquiXdO1wylOIy5ynP3BtMW+JgwGE3N1YuT2ZXpmyuaz6T6NffyttaH3gb6vQ'
        b'DP9hH/DTPr+DIzccfMHsv6vu9zGz3/5TkNfRGeMlH4gbpkctGfd8SlzyV+vufdWpuP3G+E17wnyPDcj/uLa5PPTE0fefH3i870+/Ll8wq+9fL+j+cF5amHHo3WdS//yG'
        b'qm3VL2aMm3+6bqv2jGjLJ+n5poGndt688vDK85tXai8drNucUh/fuSzfrP7rmU/urVj8FnnbfHdz51/6/OWbId8++2FRw5umnxXsEdVeyjg7rvb/a+9KwJo62vXJAgQI'
        b'GBE3XAiuYVMERUStYoGCKGrRumANgQSIhi0hAtZdFFwQRUTqirivuC+otf9MbW+12n0xrVattf79u9nebv6/9c43cxISSCL2733ufZ57jUxykjlzZubMmfN+Z773e8MK'
        b'Zt6pTkbKiuJNqkvXe+8OTm444uYf8fG25GU/GkofHTv9uPO9qJFzR5zWxUed0LW/4pspPTW9pKZ25qSbpXFRVYYeA2surHmnY9ekbydvrn5rf23ku22T/1GSn3nZ/e4v'
        b'b37bdm7K9Z8ObVn78h2U89wHg4a/t3hxmf/XkUuyA+8FdiqEgD7EaNpMTDgHK8R9UaPFFaMBr6S3oWH4FYLXYbE/OTQIbkEnhfhICMlwAZfR+1gKaiCXCvMgfxnXNqGJ'
        b'QxPojV9PbJ3VFj9MyUQhPjWxMBQ3UjijwTWoDG6rY8HkhEDCXZ8DinmMCB1Ge70Z3FiIy5UQsAm448sFBDetcp0v7JGLNrGoJVXoRJ/mZEQAW16pDG69NJwCiY7dh0It'
        b'8nKD4TnDYQGqI52xlXFttqHd5MIBhxPwNpkWRP1N0Pp8XtsnleS1KATBI0tcQTBbhyniLtG4gq3Or+vgYSX/g5ejkx2hHb1FxPg/ii8wOv/egajUAmS6jAEog4+XUCzT'
        b'eUS0tQNogb4JpnhOZWhnbX9yEihiqEloAg2iPLQO72Kk/4oxM6w8RAcYm1AM2hRKsyjwYQXBFAkh/frhyv54pedoUkm8T4TXoTJ8mDalr6FjC2fVkego9VfFZ9F52pRu'
        b'6Mwsmmt1H5ckF04sFKCtc9BKer7c0fLUJlIArO2Df1Cekpwv8PMyDp1mdiRwE9t3JXDtig7hKoaCdqDNBKdSMGqGovjkMLRyGtpMcRleNl9BcVkBGSfW0KwJlw2bypxj'
        b't3iSsdLkHAtoaqoAleb2Zj+XhuubYvZMFaI6XI52QWAr89Jxq1bBxOByR1FVmi2q0ksFYqGZru9LMZUveXUgr07kBdvelLrvS3P48H/wMkefkQo9BHIhrJhKhRLKqJrj'
        b'3YRd4MAO/NOc0Kas3dUaSPKdHbhUbbNm1uyQpAQRK2gVfUum//UASwI7NtcbBfdb/WxIqEsu9dUFN12TxOy8af4Ei0rU7ZHRo8Bxh7pg0FV6uoJLF/hMUuX4mOdjxion'
        b'Th0fl2ISGTSFJjGw602e/A8pcRNTKBCkzWMd9O/Ha9CDvFkI9BW0QSKStW0VJ8rFW+zt5e3qK5G5mSMzuNLT62rz8hCx0862hM1+Nb9kLt4CX1GnWLa2sgmdRethZscr'
        b'g82TuwsnmyiahlfMtFlhNgubGJ5prrwqrm5DlUnbmN/VQssnUYWbuhcBwMB8aJMpVrupJRYdVne1B+WrSHkdVi+67U23QYe1Dd2W0W0J1Wn1oDqtUl6HtR3d9qXbHlSn'
        b'1YPqtEp5HdaOdLsT3ZZWizM5qJW682ZhtSswUmZ6qf06c3XewN3gt7uYtzuSvw3C1QJ1b55y7UbjEHmWtSmTZbpTNVeqsUp+c6eKqWLKdZFMk0FvqAMqBGUM+EvLvAjs'
        b'76HuSdVU26q7Ul+NPryaalJy3MMaG5byRLPMJ/mJSanKFaCaAUJIqlw1jHJtczVGm42giUCW5pWPyKe8dEOeDkSageMNMW+ZriTE3NXkF7Kwz5Tw3SwUsbVoazP51UA3'
        b'kzsv5wVKOPxHuhwsYcE5QRNHnTnbJJqVS77L0ai1xhzynSSftKcoT6/WN8m7ttBVtY0BZY6x7U5MKA9+ldfTEgPqScqqpYHi2w9arawKXf6nlVWfLKzaQkTVLuv9Twqr'
        b'Wp0ESz0gSreTWpCfHdUhV67S5WerQu1VZYg8I5scMoPGwnau8+pc5tWOpOtT9MgTZV7J+GNhg2PjX5DrVOmgM04+WkdiDuzXLMYxUy6zWwvbqtO+VYRbdYWdyvMVIdfA'
        b'E0RmHQnK2g+L4EhktpWCsnYLbRKZ/TcEZc3XOet2tiXXqvkTFvGkE2aeHPhY0fyWXK/J0hpID5OpisxodDiFyI38aTPmQszmp9ZtbcOenvynEnRbj4RI89Ok14tGcdQ5'
        b'Ay8KBDfyljKmCU1Qvl+kjbrq0pFSGdqI6mih26PbcwouO0o6Mq2rLjyeSaMSxLoRb6Cldih2WC4VPbEueFu+FO/09aXlxs0ANdj7wYLxaTr3tDkstGlwMD5vt65NNoWN'
        b'EKynKzqDyj3RdrxrDC11va8rJ+VeLZDK03S3csZzRpjq++Aygp/tFZsYnNJUGtrRmUMLcaU7Wl8cTEubpAVt2fLJwrS0MV8lG1nb0Ta8vMS+LqzFfrOp5AhcTWp5yhPt'
        b'SMPVtNxD7h6cL5fv4S5L0+WOULIThTY+i7fZK1fBGyqjbU5SbQlqRAc8cfksXKU99xInMgDy7B7/fehb57yEMdK4CS/9MUOxZNR9laf86JrZb8rah4n7ifzqfGfeqRi0'
        b'3fjd8dCaVdFFkWfXtF/XbcOPoTfGtfnond/fjAw5c/sjyVBc9eknZWcrb8YO7Fzx3Y36wJuvFT2UDTuXVbz04q2rw/GKBft/SvnZZ4PH5f6XL12JHDGo6ODP3OO/VeLT'
        b'qvoTVdMfuyyPUi2MDPRgD+L3o/NutpZjFt5HDcdn59EcOrwP7bZhGaa0YY+w2+BFzLxtQOtxraUQb/QKP7xcOH9cK8YN00dTs02NDuO9NiYotT9jekKwthX4FWro9iU1'
        b'qrdoyKKDQlw7JALvxNXMQu6AV4L9iKufsdjIIW3ZksT+icRIpgZf0DyzwefvRe1jvGxkRxsTnhrwnXoRE56YvqXMeL0wEW1tMjyZ1Yn3qInh2Wt+YX/IUYaXoC3syUQo'
        b'Po4hEhSqBGOWUg0SQ125sYI0VOpGMu1FF/4yHG8hLsLlYmWuLeBGUalYgWuTbCyTkKWBPy1bZmVWAjkciMiehaQRknOQnIfkAiSvQHKRa4Uvq6Q1hXjZtCmQzJUGsGut'
        b'7LiF3HWboGota95a+puH0gKWnNDSJpE6MLJj05Gs1GThK6dqsq3jO2abhT6tkJOTSk0xV+ph92Y1oEjg6RVG3ZVmjOTkqKmWo/qzo/55FVv+FIiVBBc5OeIMyxG7sCNa'
        b'oaenb6RYScCPk6OpLEdTNAEkVXM66dPp5FqolmY44uT4asvx/eDphBVm+RMCwe5KM2ZxcsQsmyOS/rXgHOsxLGQsZPqgw+IBm5wh4isCHuRwtVIXWPDWp+tLEIZByBuq'
        b'HjRYrjRTavEnd3HoTy6iTRD/7OLTahkiDegttlaFiGZ+GhEia9GhFkWCCJGFKBwUIg+y5iuTbUqAJpmsJVQobmXVAGWK1tt2lgNFy1PycsBCYIY1BDLjSceq9DxjIa/t'
        b'YyBY1FHfwD/Q0dBAl6i1mVRlpZDH2raN4vubhmck3ZbFh2mzA3PhX6JFFUjlzGwbEGllrMgVZukRx2aLdb8ySN7iwpQrYtL1mozsXFA94W04GqzNbkWbxoHBoM3KpUOB'
        b'aYu0ELgyyLXWrdIScybLgYCJ2UwZQE9y5BCLtQJHGhAYAo9CzJK4kMOiiZvhyMCio1JL9wedJei7qCGt12nKtG0QtFqrMfx1KksKUBWiekiB8qCgHDChSXNKgoL+tO6S'
        b'XEE1lkKZVNHTFO1EY6lV+z+t4pHcgVKTI8Wjfq2rhg0fw6nukcKiezQgUJ46INyxbpE1p4M/jUYNa442l1aU6pTHjh07dSq0zF64VviXryrJocFeNXq4MYVQUTOL5WtV'
        b'oXDnFXIqxmT7HIRdLf3NV4rdajHYYy3hRA4fEeZYjcuaAWN+KmR1mZBvyRWZa9CySuVl2he3Us8kI4P2B+xAI96qiuFzK3V94F+MTSEG+kBMm5FdqKXiTYYmabGW16zD'
        b'MkPlA0AcWWMkk6ulADKCtXK+i8gMlUOuuLhJoRNVhekaeMhoX2oqVE6GC4vMqTPmzNJk2+//UHlEs2z0aCpj5hxjoYbcOSDasfyFPL2BVspBGQOj5THGzGxNuhEuPbJD'
        b'jLEwD+5vsxzsMChanpir1s7WksGs05EdmACaoVnLHewdaa/KT99Bg+0Vo7WqVs7TVSvKXnlP1y9DaEc2df0Tet7ulxPZSIangc3q/dQj0br5mXrSGgX0raVOqvQ5xqxA'
        b'x8PPenf54N6OB6BNxgFDHOUkwyy3f0ttSfbjoObFRDoqJtJZMWRQWNrnpIwo62wOmzbEpjA77XJ4Q+MZemSG4z9RPEAwKZlbzVO5IoXdYx3esJsIgCBuTm6FbItgHEUS'
        b'2dTkkj8yzOVwD4pyoo9uoQ7aFhPerJhwp8VQlqGNAJ+Cqu7Fwv1mkMPdLKxEtmvcJDpTwxdyBbnI+SFOTrvjbjDqQYgQBN75TyFyK2wXN+l5uWIy3pmtJxcpqctAx1Wx'
        b'IkQ2FWb5mq+UuSjDLKPe0LJSzuCeI3hJoWTrkZ8FosXYPNhvHYah1M1oeTK8yVPDw15s/W7hbLdwupvjs2HmhPIQ0qx5T4xlZ+OAEkbJLvBGMrbM53gWS9Do9bn94/Uq'
        b'I0l0/frHawm6czxr0eyO5yoox/H8BAdwPEE5OzKZleKyCQgjc7/jqYnWjWA2tf1qOOo8gmI1mkJAFvBOAFakU3yXnlccLYfVYoKfMgG1ki9Inzs+qbAT8HXZXiqdHDac'
        b'7pGhLYQLkqRO4R6jKUNO9oEWHAI4PTRiQGQkGWmO6wT8YFIheHM6IjNVpLXxZFJxlokyjMkZgjd5aqTjjPw0Z9YYdTKizdznaPko8okh4dTwwU7zWy5tuovtwp3T/jYz'
        b'qvk92flxPFkDk5pAtFExyeT0OJ4R07UZpMDEZ8mh7VyRNpzollHSedWkayOFwMWe0sEtTXdh0lDmFOuGTkst6oQCTjLMhdHXFirpPg1zIb4kJ0sYmaZ71G8OY9ThoyWd'
        b'kvBBXJloYdTNwutpflmXjlwIx41f2D9t+tbho5lLceIQfBIEJOpwOVWQwLvQOkb/OZGE9zfxlQPQRUZZVjNBp/ci5gp+E3KyURGq1CvcDM4IDg0Bqapgkhmk9saB+x86'
        b'OHqsAi9nwYk48Mh/nise6J6FdwoZs6c7jUJU/Oq8+e0+nSJIzGbrcGGTYu0FIYJCEvBKvBNvg8UIG4XBCvSyNBCtwTXateM2igy3SCl/3A5aunrsaNEEWemBh1cXTE86'
        b'VtR+2KjkWy+ENeZlrl0Us/X48rfO5PtGb7rl3kvwdp/u+Ne5bvnvD5z0oXLDg6Pju+9Nf6/9H9d+OzGxqK59n42H0q6G/PGly+ubJ9X0jdv++7mD+Ys7ZF3Tx34wOOG7'
        b'1e0eBoc+zn7mnWmHhFe33N18fmb+tLfnfinZoTm0Keq9r1/8aP0fb1w+c/WD3e0eD7rbWP7mo/fSjF302x6kJqz6LG3l/C0qRePrC9qtk73d8VSn3jN0GVfqLvzH8O7v'
        b'lJ29OKZou+r6ssPPhfscbnd7yfxHI54tWPnw244PPkzw8LsTKGHyEj27BaMtqNaG1BHpw7wdVySgWnQANfQbY+F0ZOFddB1qxly8LxhtxFvw8nGJ6KCYc9UJe+CNaDVb'
        b'LGqIE3uiXbiqZfRNXSRzY12LTs12tlbkji5wY+likf9splN0GtejSoh0hI7ieptoR3yoI7yFLWfNQnUTeHG7qZkWeTsqbYer0T5K3UnPxFuSxiTm4gMCTvi8IAgtB6XI'
        b'5qs20r8oGDc4r9ElKliDtVmiWsCNk1CFOrHAW9CLhj2Cz+Ad6MEvTwmpb6Efee8g8BHMkVoWYlRqdbJNyI2mB9XgfG21JuX+VBUPFFsV0hSC09KSmXYXpmp7WC9M2dTS'
        b'PiGDhlACfyKuTGwJofQktZ/M/3tqP3BKWurl9WYzv99kMouL27gBkWDVoL4cL1qaiCoNRuAOV4jxaTFHLg7BvP5oD6OkgN+/NhAd8CRbL86bzE1GO1nIczIRXMSrUmA3'
        b'vC8T2ALnyETeE6+hhyqIInN2EKlOmCq1PtqDD8RQoYTADpMp25lyR1YkM05vzYTYiIFoMbkyebJJPW6g5QyVunHShCwxMDiEoaGMABI/tC0njwpyA/7IDl064xTk95Bx'
        b'cnkYkErGPOgzguWcJPDiOuWfEgKp5NmAJJazj17KdYraJSBf6mJFc1hOwQwPzjesrSsnS9PFeylYzmsdyZeK6/DlGO8+c9mXITpSpcIYV+C5eBnC+EA9W3EZakgZP378'
        b'AFxDSovl0CJyazxH2+0yOzYiLCwM7ST3ZAHeyeFFyVNouwV45TMp4zlyM9kAQkS7yS8lOsopRq/gDVozSwXvw3WUqYIayax5ltFFTqbiE6TUaBDxBapKVSGuoXSgWHRh'
        b'Hqx0ke5cEcAFTOpMz2F/HS4FilBCQjgXPgOtYsFF9id3pYwTP7Q5lAuVLqAckageeD+jluD16DxeYaaW4D3uLMbBYXxwasp4uQhtnwjB4tq7ou2CbBYfoXIwXmShl6DD'
        b'aBejmIzWo2OM/gF9nap252SSTq5cWpr0fKdw1q27fMmXvrkC+HLMiClsxGgL8W7SqajKCIUv4VT4aCotYnMfX07B1QvJUJ77vdKDAZIovE6SMh7VBU5L4LjoeZ54OzqD'
        b'zrDzs4Tcsw4YvCLCPIAiL0QHOHwBVxVqj1094mKIIl3w3Oc/5azllXk/mu3z1YgBBQm/efpuXly1okbo7u6+ve/U0tfdvS41Hlsz/Z7k3OAVMre6e5KJb5n+Vl8eMnX+'
        b'54e/unq+ZPcqn8vFOO/XpdOqVEkfn7hdtmlM+52TrjVsODDlFUXWD9Xh44J3HMxWfHupMG5jhdvbv/3QNqr+w/CRX8Qd8n93zLZ3gqZ8HSm7d3lg22l7pvWJ/TTlo/Do'
        b'uqJBPQNyAl4MuNDtwfT1m5f+stT7j3eTE3d5L2t/6NGpTrv8O3380HPCw9D9s+ZEHZn+k39sl+R57z76Wrzu2BuCh5rKawP2Zla6t3ut9rJhSrE+SxEo++T373rWqkpL'
        b'woF0ckz3srb9521XVzTEaQ72/vTnPVeS/uh2pVffO7OnjV18fPj1M9d6hFy+1gF9EfTljX8O0z4q0V5frftyVOSo0759Ln6gn625mx7oyxw6tuAD+LjVTToWNdjx6aA3'
        b'6VDcQHGB/wuoPJje9UNj8FlXToLPCdHaULSS6pbI0SF5MCj4bPQRcOIAAZlw6toyDZczaMWLfLjBQaiC1wXs7c+ECBbhRk+zxMGsuTw9JS6cMkRRoyu+mNSCOzI03o2T'
        b'x7m4dy5h5W9CW2TgGhMckGn2jMEL0Xn2YzU+5sLII/m4whyt1K0vxTKBCXgpkIHr0qycgKgHUD5uZAo2J9AytJLnt/RDm4HiAvwWvAldoIAkFpW3t3XsaYtrzdySLf1p'
        b'1+RO6EdDU+A9aAePtTr4MB+kBjE6mUS6PMyTUUuAWOKNlohGDcNbGW3kHFqF9gGzBJ9HS4OtqSVeaA/TityN14+FQlA92kbJJUAt8Z4nisXH0EbGkjnQHS+y8vDJwcfM'
        b'1BJ8CtXSnpqCa9Ae5kWUpMWlvBvRED2T2lkyNNZMGyG5NvMSjCBExw6wfQCutPUzQmd68lwhHz9KvR06E3D+OBs3PLR6itlVCh2f6zBYnHMIVmCGYLktIVg+QC5edEwo'
        b'EzJffxlPmgV6h4xAMABgMgLJmnQYZfwf8/QHVQtXoZinfch4n3/wO+LVxSgYci5gZr9pLaTMAH91bY6/FnJbbeMcNj8oKQf0df5iRbPM/1c0a4HY7CuauSUbg+AqqUMr'
        b'UH1wQkhcL2eSZsPwKWpID4NgAlSgjIqToaV4IwiUNeJGRi3ehhejHUDhROfwvmKuWJdGv++Gl0xGxKSjQmWgUpYQoB1fIBEajpAf87YtA5UyFCaLzfrYWza//hZXXlUl'
        b'Gl8gGDlaUXdcoVgj9A38ZtnA1Jgk7ee+Q9fevzkz62Z5I1p3f2Tlrl73Xvt1vaIhes7MZ70uJIRvc4kq/+UC9/ngrhdPvnZ4wuL4Ifs7dpgvO3KpZH76G8lTfzyrOSBs'
        b't78+9nyZoDT13dwK042iz/z69vhg00XVjc6ln96NPfHlq/GD//XykJyTd923xc/SVYd9oqrsuT/vjujHK22EjYNXb+MC29DJZwZeNQW04Kg+GUFi1aBRVoP20h/b4zNy'
        b'K4myeB8JCJRNmMBEvg6i3QQb8BJk+GVUAzJkXd0y6PzdLcGTFyBDBwc3aZCdR6+gXcycPZZFQBPTNxuHtlgkztAOtGwuPUAff45XKIsN4jXKcC0BKIw2KMI7s836ZFA/'
        b'uDsEdZlDJ81cvMqfhg0mYGxLP6uwwS/4UZfO1IgZZnEyTReQJ+uJN+ITtN5JUXg1VQHDe9GyxNB+Fm2yeFzOeJd15Aa7zixPRhDgVpAo64grU1mv1MX5NgmUkVvIRXeQ'
        b'KGsrY2y6vWTYHbRIlA33A5GyTugiWscm+0pUSxCtle5QdDHIDp1B++n9LCVFxCuU+UyiGmUhArzrL5Eoo6JadCoPajmVL+BCezhXKYMZ8S9XKfMXm6MZL2z2+sKOXpm5'
        b'CuTgtuQbxsMT0rfkQJ/m3DtAzFYEvFZ4lIImoclFW6jJMTAGXTNVsrb/1gOOVpyr0yQJEPFPPiSuYiG5rQo7KFovQgZnsZNAXuQzlE6H3dC67uhUnMHy3MiF8/IT4nUT'
        b'gLSo3b9fKTJ0IXejb748H7f6LEH+t31ly7I+nn2nZ9m3v5Ubbg3z6NZmZMz95/8VHrfT95br8oG6nUdLZmZWtD9x9drgxwNG3P5q35Vzryr2Hv+p4MSC+yvUs5ed/WPT'
        b'7WkfffjDW3Wz/n54k7pUm/iDf2i7G9dLRpz0qPr90Iz7x15QK4uyB43aETJvV1Jx13YPF/bt+mDxhq6Gy8HXztwa/vHYUsnxTZ+/NK7XP2OLr834QrX60tU30P3gN+9t'
        b'nzClRwefBWsL5gw6Jt53pDDtg5ylVf+p2Hqsv/an7aGd/6mfYbjU5ebRN/7ZB3u8XByxo6Ix6O6Ng3UzMt5Ye7eDIi/m+9FbazY/3mTod719UemgoILJ8b9ee2dWly1H'
        b'IzqfXLo3Z0/Ub+/0+iQteOu37+yNedv3/CNh7GuZ/WX1gSImnb7vmQTg2K7B2wQQEY9MEnvUDCqeQQ2owdqlHdXP45/edXBllN0j+ECAJeg4Povrmz+KO4pOtnyc1uW/'
        b'Z7Q9dULmGpH5arObUB6wRKnU5anUSiWda0AzgfMTCoWCgQI5mVtcBT5CiZ/c1y/Id4Rv32Ew8wyXiLw9+yzgZuvft1xgIpNQqbSaWPz+F7ReoP/Acn1CTeG6YnF+74+0'
        b'lk+DaakvPBUnxk0lmeWXjxuDlqNKt55GzruzqBsxDvdpBwXeEBggznrV8ve7LaeYwqXoUZHktSvyXvNX1I18dfmZxe0nfNJN817A8F863N4tnhyxI3Gz4v0E0dh/Pa/s'
        b'XnIrse+gc+mjH896bfI09wjj7EueH2bpFRN07ndmfvpZ9dK973l8PLtk6gvptSPTFNmxnQZmq24fed019ZsjbwieK/wh6vaqhZ6Hz9y+WfTmnh+860c8jHnwu0hyQ3E7'
        b'aCnBDDCYJw4kd2Fy6x0HKwrEMjyPtrpxnuiYEO8NQJtoFtdQtDsJlaF14yCgKckJKqJt8XkR2v4sWkItlza4cibrBGqPEBPYrRfew3n7iLoTw7WaXlAaXGFMShw7AFUG'
        b'jXXjyEwnweXd6S/DO5KZamV/Vw4e9tSmcHjHi+hAIaC0KLSjIHi0CyeYjM8lcQQxNE5mgGMx2o5LqfYeOR5eNbArgRSBQnKxrkVH2a19kybAYPkd12YLOI9EIToyeQwt'
        b'oC9ehhcm0UmS6TavQUc5b7xClByB99IH4Bl459CktoVN6zzRaAdFFfHowjAKNxMolHoOH3bhpO2EBIVuFND+SgjkiBG3IiSfRZ/Yh4+4cB7ouJCYwRvwSiattb1XAclz'
        b'EdXgY1JUXlRgxMcLpAVGAUfAh4ggjeW4gR7MiGtGJdHYFNCWkXgdR07ORiGu74NOU/JMAtoD8Z9QZf8kMsGshmf5aOXMNHICuC69xGiJHq23iSbt/z9/fTm+8NyfMO3Y'
        b'mYWa2C1UjtVLwgIzUXsTLFSp6JnmAKgXgwh0+gkwiXSaXJMYXK1NLoXGfJ3GJNZpDYUmMZiEJnFePvlZZCjUm1zoc2iTOD0vT2cSaXMLTS6ZZP4jb3rwzABFlXxjoUmU'
        b'ka03ifL0apMrMY4KNWQjR5VvEhG7y+SiMmRotSZRtqaYZCHFiwzGHJOrIU9fqFGbPLQGM6PX5JpvTNdpM0xujPpsMHkasrWZhUqNXp+nN3kRo8+gUWoNeeBJavIy5mZk'
        b'q7S5GrVSU5xhclcqDRrSFKXS5Mo8L5vmV9Zqf/2P8Pk7SEDGTn8Dks8guQPJdUjuQvI5JPchuQ3JTUi+geRDSD6B5EtI/g6JCRLQVNX/AMm3kNyC5HtI/gHJp5B8DcnH'
        b'kHwEyQNIfoLkns1Z9bBMu78lWE279LeHkkxwtM7I7meSKZX8Z/529NCP3yZWccYsVZaGp5Kr1Bp1cqCEokQQsyU2MC9mS3GkyYP0vb7QAFazyVWXl6HSGUzS58HnM0cT'
        b'B/2u/9ncg83YEibJsJw8tVGneQbYDvTRg1hIJrjmI2+wL30S8l9HXM53'
    ))))
