
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
        b'eJzsvXlck1e6OP5mBRI2SZCwv+wESNh3N0CRHTXEXSBAgGgImMW1WveiiIJLBZeKrVWoWnHXVlt7TtvpdDodUtqCjNPxdmY607mdubS1dW7n3unvnPMmIRGw09753fvP'
        b'l4+enH19zrOdc573d5TdH8fy+/U65BymFJSeiqf0LAXLj9Kzl3MWuFDj/hTsVBbji7bEqIQolrOcF0qlWmKy0f86VDaPvZwfSim41hJq1nKnUGq5rQaaauC57JDyv9sk'
        b'mJ1TMWch3dRcZ9Kq6eZ62tiopuetNzY26+h8jc6orm2kW1S1q1QNarlAUNGoMVjz1qnrNTq1ga436WqNmmadgVbp6uharcpgUBsExma6Vq9WGdU000Cdyqii1etqG1W6'
        b'BjVdr9GqDXJBbZDd+ILRfyGeko+RU0lVsirZlZxKbiWvkl/pVOlc6VIpqBRWula6VbpXelR6Vk6p9KoUVYorvSunVvpUSip9K/0q/SsDKgMrgw5TykClr9JL6ax0Urop'
        b'uUoPpUApUroqXZQ+SkrJUXoqxUqe0l3pr5QohUo/5VQlX+mtZCtZygBlkHJKSjBeiJXOuuCKwLHJ1dFBlDJ4LKykx/w0lROcQ4dTIRPE1lPTOcFUPQtNOLus1n5J/dB/'
        b'ER4yl0BBAyUVlGmdkd8jgk1xqZ5MZ6q6JGGtB2UKR5HJ4dGwDe4uB/0LSubDVtheLoXthcp5Mj4VNYcLX4dX4TYpyxSIssLrTbDPUAhvrCqF++DeUriXRQkK2aAfXAe3'
        b'pGwTbnRN+oriwjhOWSGP4nJZ4GQkfMmEO7RJbkDxudpCGdyNivIod7iHUwbPwYOooD/K4AT3eIE2uEc3M64FdWgvqkAArrDB1aDNplCUHgd2LUHpl1018A5oXbvaBK+s'
        b'dl1tYlE+cD8H7AVHfFEv8YDgTbALbAVtYH98sSwGdxTuxyGwM9SJ8g/ngu2zy2tZdvPlb52vQ8iZ4VeJ5gwtJhctJYUW0AkttwtaaCFaaDe0uB5omacgIBChxfZGS+yD'
        b'FtsXLba/MiDF37LArAonuwVmowVm2S0w22EpWTlsssDjYm0LXP/4AvuMW+BAZoGla/mUK0VJloRXl/AFSRSJLCjnoFWn5nG51dr/yo9jIvfFO1Oe6PethuoSxezFTKTW'
        b'j0uh31l5RdVxL6/mUn2UVoCiO+ZIuA+9qFmjovU5dwXXEw94HGZpMSrpTuhm9Tv1y91mVSfd19+ddpIi0TT9lcchj/nZ3HkPWP+QOM96mRqhTHKUAG7Ba3AXWtw2YUn8'
        b'/OhouCe+QAb3gL6K6KJSuD9OXigrKmVROg+X6QjQHNZIaB2yEa+R0LJGPIf1ofAKpQhta8D9F65Bw+Nr4DRuDVzL9HgSTXh1QIc3aFfw4NkFsoVsis2h4AnwPHzWhKc8'
        b'wMVLwYavzqWoMCoM7Flq8kKR7onwqGIBm6Iy4Z5Gag54bRPZTXAbDV+DBzkFsJtCqDwe3lphEuP4DnARVXiQlZtBUTJKBo7APUzDt8CtFgXY7ls6H7bzKPZGVgC8BS+b'
        b'onDasSLYj7dWbDHaE7tL5keDvrgCvNNhewIlh308sA30hZBONm8IBlf4oTkUNY2aFgPbNcrnLlOGj3AtQW82db4qAAmSneUfFI/kr47OcN4mzvFJbzt2pa1Yroiastpr'
        b'+fFNgrUn324YXV3SJGrTnDl53PDa9x3a/+TEyHouH3iwUb7ko7I/3f9s+M5Wf97Lsw+GccLnd78NGv/euTqSlzL/9un2p+95uYt+d/poK/VJ51bXC097D/166Sdvf9n1'
        b'M3+/9qGjTZ8tAC/WzBn6sLjs+4N3ToT6/vp02G8DM0d71+cpzxd/+8r0wJCK+eU3EvdGPv/cjPdq72zZkzl9/va/fvZd4F+eCg1Ifqfi9IxHj55/54rh9B89Xn8nWnbC'
        b'S8p7GIDGJgjMKQansmF7LGwvlRXFIRzkBW9y4DNwa/ZDCcqwYmbZ8tWxRTLYWlhSxqOE4BIbnoCHSkjp4EXwWKxcWhTLYLiFoJ/ygFs4zeA0PPKQ4M8t61YJl8JDeNpN'
        b'CDXtiWdTU+ArHHChHG5/6ItycPUrYVsBWqU9cD/ci/ZtJgtcAhfARanbCDtaqsdL8xMdgxvZmlvG/kamTqvXN29Q6xDhJCRZjsipes2METe9Wlen1lfp1bXN+jo9hk82'
        b'roGNduTftlBfPsWipvp1RR5c3pp/PyCip/7jAFmncwdrWCTpnD5Mh3bkdyUeLLznHdzD6zEMeceavWOH6che74uBfYH9hpuzB6U5Zjpnglz36LCeOS8I7FJ6eb1rB6LS'
        b'h7wzzN4ZluQhOslMJ/Un3+QM0tPsazEOeceZveNQtlN5vbwXil7wsK+J29toq2mYjjjrfsq9d80gncbk+b1f2EB46i3uTeWrQnN43qDf7AHx7C8DqUD5aBAl9jmS0ZnR'
        b'lT8oChtwDfsab3893v9S9xE+M0cjTlVVepOuqmpEWFVVq1WrdKYWFPMTV8odOdUOS6WfghO9rM5MnCsTOf+5hXq0kcViiR9RyPk3d5+2VVuEo2weS3xP6NWW+W9cjx2l'
        b'w84e95xFf/uSR/E8raHvDBhVHePHUueEaRwHxGbjIQmm5R2mlmMOEvGPCpaeo2Drueg/L4HS89Gvk4Kjd1YIlFQKS8HFWHclS+9CQjwc0jMpfOLH+JmlZKdwFE4k7EpY'
        b'Ji4KO5Owm8JF797AdmmUCkf4C8isfq5AXSgjU13Lsesi14p7G3EXWQxXdxhXT5EGGALAqbBjYXVcRAA4dgSA64DqOTlcQgDGxU5OhDnjCACXIcIzNxMqSl0pq9aK83Ip'
        b'TWDdfZZBhWJa3u+5Uvvcu54g4M0tLrmLF2+tk4o63joOnUW/5PTVv1ER+OY+6dR3paxqwUc+7/UKP/hF64rmhLzoMOE7UyO7WlmtTot8wWmWOkKwdbnozfa3rpUkvCqW'
        b'fLC1IzmQWrLH9fyUvVL+Q8zMpM4EXbE23ieWH7+E8gBnOBvgvmqCxdJLNTi5bD6TgUO5xnGcwC3FQ8yoIW5uK9heDNtKEBsItsyQ8ilnsIe9rr6cSX6dDQ9jIlJcCHfP'
        b'Ahcoip/B9gW94HVSNTwLrxaAtvLCOLf0Qi7Fg8dZ8BWww5dgN7hTDY7HygoK4+DNBIRbneFVNtgBjiVLeZNvBp4VbZE9MOJcVaXRaYxop3kwQCK3RhAUVU0RFDVqZFNx'
        b'CRen902/6WOOzTF7RndwD7l2rRwWS44UdxYPiSPM4oielYPixP4cszgV4a6g0JOrulf1hvYmdjWjvMLhwGD0I/hE5GMp08P9SBwxyqHEEr3IhgD4I1yDWls/wsWCyIjT'
        b'GrXegGQWvTfOMNU2BD7ez9V4RzP7GLOz+jDkLMOpKcj5O9rHCL2yQn7EFv4aA9lhfgT1ojCBU8ueaH/U2fYHsztS2Ja9wXZgjjhBDqyP/T5Bu4CdwyF7Y1zs5BKIrQN2'
        b'e8MUi6HnhORpcBicFMJ2BEP7YFs83K8oYGBt/jzCLM2Ep/hTwP5KTZeaYhtyUSGXc/dXL7lSexRtHE8gQVvnvK+vxOs/JZLnu1Whb+wNcX1F6+p6Zq/n5piweVHCM+/T'
        b'a0oued6Ue/PfN1Lv/DffMOgm5TKwe2EB6Idd4KAFuq2gnd78kCwJuGWCL8JD8Aoi4PvhfrmsxUKk/TZzwU7YNeUhYbGeqY/CEB4K98bZQFxU+RAvOuIUXgK7YLexuFzG'
        b'othrWDkGcFrKtgNnvE5WWEa0okFt1BjVTQicvWzgbIsjEJ1mgejZGPS6jCc3dm8cFMXc94sYiMy6WWGOzBn0yx0Q5w77+B/Z0LnhyObOzT11gz6xA56xdnDK02PJaISr'
        b'UzWpH4dOHoFOG3BiRl0fj5xaK3B+t4X6No/DYkl+LHAe5IdRLwjlnP9z5D2Oe58QQDGPLOBlTwSbWUvtoTMvQPNWr4ZHgPP8TAtO9/yPbU8Gzlpn0bx44ZlPPPkmuvv9'
        b'u918avEq/mnhX6QcBnNuA510sb7QETQbZzwMQYlhSIDdPiFcwtfngp3rNj/E61kDX5cT3GsBy0Q3+EqxSsp5HKVyCAyOAaFhAiA0OABhogUIy34ACMMQnj0i6BR0pXzg'
        b'SdvjSQJ/+gTcIG+NSmsaB4WP48h07CDhhmqk7HBkKQLD4B8Bhnq8phPjRgJ+HBtuxKIklcL938GPvHHgxysjEvJseIBXjNavArbKZPL5BUVK2ApPrSlXMKJaAZLa5CzK'
        b'CO+48FPA8wxKvQnuRI7BbHrxJBj1WfiaZo1fINfQjArtu995pbYbQe35NxFKBXXvHjK+SfH9PPeE7Dy2NeTolHdVzvUpOy8rfPMkO32niX0lX0lyfXMXb+uSJGxJndck'
        b'mHd/kbiRH3vf9cw8/oo0Pn9H4X1XAS0aTih1/vRNsXDrqzlbQ05sRXyJ50nhv3+xEolXWP5BjMUNldBB+lm2mcg/MXArg6GPw2emW7EzuAx3WraBUkQw9Aa4V2e3C5Bo'
        b'/Io9ho4H3YTPaFaHkG0AtsCTY0xIK7hGUsEZcA7sImxIoa7CyoXMgVt+kAuxceIjfFMLlpVG3Cz7hQmSrbKU2SpfLuZQktCe8F7ukI/M7CO7jwWMmYN+swbEs34dQHfM'
        b'Rgi7J+Vs9qnsj3zk94OkAzEz7orNMXMGg/IHJPkIigNDRvnUFG+8m4Y8Q8yeIT3hH3lG2e0pJ2ZPRWDHcTPZ9duJsiB3qwyRgx2MuJooiwyB0PujRRi9j1I/Dsczm8te'
        b'S+PIeHCIlobo0Wx4nVXB+RdqZf4JxoNTpvk7P5tjwD1yTmojuPq9nl9JwPMI8qcifF3iG3JVHsvJCypwE53xf3iUXhj3Xc/VhO3PCDh50nmLtnqu8d82nPhWrq/q288S'
        b'50bvSDrHWfLaSldXBPCuIeeLXE+1rO1LaKmnqGJamPWbGsRqYCaBpUIcshWVs2IZKM7wI5iex8tD6LwH9IxhavjKBthKdgDcAXeCV9Fm7oCvxBXCdhmf4leywwTgLMN8'
        b'3JpZD9vW+2L+28p8N4M2BAz/hFyJgYGm7ZhpJLUajHqE993H8D4OE0BezgDyaCOH8g/umnoqrKfu7KpTqwZDk8y+SR384bCos1mnsobCks1hyR+HpXYWI5iWBJwUdguH'
        b'JFKzRNobPiiJ78hBsjYWsBHohKd9yackET0LB33iBjzjxpOHSaGYEAc7IC7EThFyTJSFOGBBuAEBsdePgV9M1aScEV4V4d759Rq1ts6gj8Sx7LLP/4EgW+qBBQ7MNaFJ'
        b'ElRVMYcUyO9aVbXapNJaUjyqquo1eoNRq9Gpdc1I8CeEzrkW4YSGZv36EWeLYMBUri+hrEIAYbbSbfsSj2vEGy+CyqiprVIZjXpNjcmoNlRV/RByslMTSKwOFp8NWXgZ'
        b'd1EPRD6tGOe0Fgz7+CJnql/r3GFvn9b8R1y+W+Q3nhy3uG8EHDfpIwHfLfqRJ89N9hWFHLJIjGbxGti6TlgUAw+Vwn3xRSzK2ZVdvZwaR9fw39cYCc5gTaA74Oh5Cq6C'
        b'p+DL2Xq+L7WECqUUTgs8qHF/CmfrqZL1V++scNG7NAiQKC4c4c/RIf5k/eebUMJ34tnqGo2xWa/WxRfr1XWM93NPso6fY0zwnddCtX6DqcHQojIZahtVWjWdjJJwd79z'
        b'LVEbNxjVdL5eYzD2sfWlKPLzt9EO+KbbC23qZp2xObsMLTMdnVOnVxsMaE11xvUttFJnVOt16sYmtU6abRcwNKgbkGtU6eomLKdTGeFtvVZOz0Mw0YzKLmzW6/6ZfBNV'
        b'tkqNII7O0TWoatTSbIe07GKTfkONeoNaU9uoM+kasucoZSW4U+hXqTDKCuvK9PLsHB2aMHV2BeL1tPE5q1R1cnquXlWHqlJrDZgD1JJ2dYY1zXpU8wZrG3pjtsKoV8GT'
        b'6ux5zQZjvaq2kXi0ao1xg6pRm12OcpDm0Mwb0O8Gk11xa6BmLe4dVjbSlo6gKDm91GRADWvtOk8nTpqSlF2s1uk2yOniZj2qu6UZ1abboCLtqC3tqem58LbWqGmg1zTr'
        b'xsXVaAzZFWqtuh6l5aqRgLQK1xttiZJa0+i5agQ78HS90YBHiad0fG56bok0e46sVKXR2qcyMdLsQgZOjPZp1jhpdr5qnX0CCkqzFQhroE6q7ROscdLsXJVulXXK0Rzh'
        b'oOOs4ZhVGIZlZaYmVAGKKoGnsXZ3FZ41ZvpRZGFuThlOU6v19QgLIq9iUWF+hSyvGa2NZfLJXtDoGhGs4Xos016gMrUYZbgdhORq5JY2LX6HeZ8oHs+9wyCSxg0iafwg'
        b'kiYaRBIziKSxQSTZDyJpgkEkTTaIJLvOJk0yiKTJB5E8bhDJ4weRPNEgkplBJI8NItl+EMkTDCJ5skEk23U2eZJBJE8+iJRxg0gZP4iUiQaRwgwiZWwQKfaDSJlgECmT'
        b'DSLFrrMpkwwiZfJBpI4bROr4QaRONIhUZhCpY4NItR9E6gSDSJ1sEKl2nU2dZBCpDoMY24hoP+k16noVgx/n6k3wZH2zvgkh5mITRnU6MgaEjdVIqLYGWvQIISPspzO0'
        b'6NW1jS0IX+tQPMLFRr3aiHOg9Bq1Sl+DJgoFZ2swh6KWMeQux2TABGUD4oeyF8HTjXo0bwYDaQBjPYbGajVNGiMdbSG90uylaLpxvhqUqGvA+fLhaa1W04BolJHW6OgK'
        b'FaKLdgUUZA1wyjxyCmVf2RgZly1FvUAIIxoXd0iwlEdJEeMLJE1eIGnCAsl0rt5kRMnjy5H0lMkrTJmwwtTJC6SSAqUqhi6TOUd8CeJPSJxRvc5o8yBMZPMm22c12LIx'
        b'C5GrRuS4wS4iInupRodWA68/aQcnbUBRmPQiLO0QTHIMIvSjMhgRtdNr6o0YaupVjaj/KJOuToU6o6tBYGtbcaMenm5AQFSoq9OskdP5DP2wDyU5hJIdQikOoVSHUJpD'
        b'KN0hlOEQynRsPcEx6NibRMfuJDr2J9GxQ4mpE7ApdPQCy6waLIyGdIwxmijRwitNlGRlnyZLs6GyCdLLJ24N810TxTuwYpOP4Qnpk3FnPyZz0uQtO/Bp/0w2hConyuZA'
        b'AtLGkYC08SQgbSISkMaQgLQxbJxmTwLSJiABaZORgDQ7VJ82CQlIm5yOpY8bRPr4QaRPNIh0ZhDpY4NItx9E+gSDSJ9sEOl2nU2fZBDpkw8iY9wgMsYPImOiQWQwg8gY'
        b'G0SG/SAyJhhExmSDyLDrbMYkg8iYfBCZ4waROX4QmRMNIpMZRObYIDLtB5E5wSAyJxtEpl1nMycZRObkg0AIcpyskDCBsJAwobSQYBEXEuzYlAQHgSFhIokhYVKRIcFe'
        b'NkiYTGhIcBiPpYv5enVTnWE9wjJNCG8bmrVrECeRrZgzL0dGqJXRoFfXIyKowzRvwuikiaOTJ45OmTg6deLotImj0yeOzpg4OnOS4SRghL5KB2+31BvVBrp8XrnCwsBh'
        b'Ym5oUSN5mGEmx4i5XayVfNtFzVXXwNuY0j/GNjQw8RauwRpKcgglZ8+zKFfsCo9TuySOj0oaH4XEHC0WilVGzJfSChOqTtWkRmRUZTQZMFvLjIZuUulMiLzQDWoGTBE5'
        b'nEgNILUrosHEXVNHiv1g5gnqn4AoTVz3+IxExTQ2OzRivmkLy0umsh6nWyaZ8SfZ+bFMOKapGmFlE91pWZ9AX4a1Y+XYmYed+ZTlqE2/ADtYCzjCM7RoNUZG81iBFWMs'
        b'RnWIdWsWteFCq4N1aoZsq9pQitWGvq0Fo3xqavywd/SXTlyJe2vBVwJqqv8oN2FKHutRDYvyEO9Wd+S1rfy6gZU81a8tn9Eb4sso7uA4uGOA7eBiRSzcHQf6uJRzGnsz'
        b'2ANf+j/QHeLbRYKc2tpmk86IxJTPb+PJcc9FAMbIOKoWtfZzb0ZziKf3O7/ZCOSaEB+D1eM0I2WhDaNBaA5lwdddR7iY39JXIu83t1GEsolhn5obdWpa0azVxhcg/KeT'
        b'FW/A2pyx4BhGzV5UvJRmimGtHcbVBo3BxETgNPsws8PnYiUjI00wDeUqZYraRi28jSBNizgg+2B2rlqrbqjDA2G8FhXPmD/JIo1lW2eCSBeY/VRbEIlVRKQZFswiaI6p'
        b'xCwiJhEMsHCJMqOtbCRCiKUG0pxWgzIQn0ZX30zL6By90doVS0yhDpd8LBJnS5ooW9K4bMkTZUsely1lomwp47KlTpQtdVy2tImypY3Llj5RtvRx2TImyoY4mnJFRSKK'
        b'KGYWBnPWahKZNC4SBehSNcLOVr0vbZLTY3pfFMnAslURK6exdGCV8RkF79gy0iWxJdn5Jt0q8iRDrW9A6HADRmE4PldJp2QyRL3emgUroCeKt8ANkzRBhdlLifCBB65v'
        b'UuFEG4hMlGIDlcmKJT2p2MSJDAg9odjEiQxIPaHYxIkMiD2h2MSJDMg9odjEiQwIPqHYxIkMSD6h2MSJuFjmk4pNnEiWO+GJ6z1xKin4ZECZHFISnwgqk6SSgk8ElklS'
        b'ScEngsskqaTgEwFmklRS8IkgM0kqKfhEoJkklRR8IthMkkoKPhFwJkklO/6JkINSFUZ4u3YVIl1rEfE1EjZ4rVpjUGfnIxI/hv0QOlTptCqsyTSsVDXqUa0NapRDp8Ys'
        b'2Jhq00I5McLLMdVjJZwNyVlpKUrCmHeMINPROboNDPuNTw8RMi7VGBFpVNchDkRlfCz5MTw8vvAYJn88Ta+F1w0WNsEhpYCcJdUbEVdiE+IIJZERfmdCicMyUgs1R6Qf'
        b'URrMsNcTVr0JE3ijWoOmxWjTShcivtqoqdesUtlj/6VE6LRpq+3ZDEZUtTu1tGeT8tWMHKPW1OCkErRq+BjOwHA2kzNq9ppo1G/UskpralqlbrSqzQkRJFwcvqbN8NX6'
        b'monZZLXVwayjIcPKJofZscnpw960I5ssmTLtUdIYk5zuP8Yj48eKsGtJlqGkDO6Lx09PduOrI0eLnSjvGq4r7Mx2YJPdrGzyp6hPM8Tj2WTEGPNDKeQK8X8FB7ki/J9h'
        b'nTOdgqggShGq5CndlCLr5fuVLOsFGz2PPPF08aMUAoUwk613ImFXFHYjYWcSdkdhDxJ2IWFPFJ5CwgIS9kJhEQkLSViMwt4k7ErCU1HYh4TdcE9S2AoJeQTg7tB70Q/8'
        b'd1H4ZgrIeMKUbMuIuAq/x0bk4Tgj6L8A/WelsC21ONl8jnX7Z7qgmsOVzO1A/PjPE9XvpAh4rH5PRQTKw1M6kyeCXiRPoOUxxBQUPwWNLoiMzsvWE5EiOJNleWTorvRI'
        b'4SlonMNWp0gRohc3OCFxJXLEeTZ+lZOnWPj571DSBh+BNUwz+I15HCvo4+mx5KTH13Y+xxdm9Brsw/dwiWwidf0cQ/Hn+G7P5/gG6Fh2vd6aXW/AziqcBb/8+xw/u/vc'
        b'FZd2GhGo6tYgNKmv0tSNuNQiZKUzYq+7ipGmqrSI2zQ2jjjXmtA+1tWuH3HG9/I1Ki1z62VESK7IVDUhHNJYVutsB9O4KXJrawtlvZNp/0qXPPVjoRXmKp3QfDEP/fgp'
        b'AsuVMucKgd2VMrRmSme7K2UuDpfHnHNcyJWycbH2V4VNL6A5EhQynddsUBvI62XbrGvI5Y5a/HA5C0k9qiZ6bGKyLO+SEWbDKi/Lw2fLDKl0RgG+fhWdixCQ0Yr+pHI6'
        b'B+dHqKqWJldjaVMLjRB2Ol2nadAYDXJrM7Y5n7gVJplpwXZQ8wNtpD7ehuNiZtEl5Bc3MTe+xJpqadjAtIXJEyYMiKzI6YpGRCoQXKppg6lGq65rQP2bsBRzq4WRYVFJ'
        b'WoWKoDDTH1rbjMiUXk4XGukmE5JkatSklMrS+Rq1ca0aHzTT0XXqepVJa5SSZ+IZY3NlAcIsOs/io2uxZjLadp5pp9GUWktZATaLtqy+wTa5+NV5s56OZm7DrIK39RuQ'
        b'nG0taLnflUWEKMxwoGLMGln2aLS6QU6nJibE0emJCbZidjsii87HAZoEcPF6jQ5BGeoDvV6tQg3H6NRr8WHpmjR5ijwxRioX/MCVYlfmOdLLXlMQjFOeVEt13ByvOZRp'
        b'BiY4vbBtAWwrBefnwdZC2F4cD3cjX7mioEQK2+ClKXFlMrAH7i+ZXwAuFJSVlhaWsijYCXpcmylwitR7inKlJBSVsHlFtWu+utlS7xHY1+JQ70a4xVo13Ad3lyACB3Y/'
        b'XvGO9a6UD+gh9bpEk5fJ9ItN1VrwlCtFruXDG03ghv3T1QK5LKYI1Q9e5qJ+3qDSlvMNM5eSB7iklhXB5CV0xnMh1XF+2bMo03QUCXo2TDjoJdWwFVXbFof7t1e60K5r'
        b'4JZeCC7DW/Cw5lTrJcrwIqpGduDtK7/Dr1F8wXOQ4oTsnRUUdvxnZ970BKw3956ZlygJfK8xdefWkE58ldr7TBYvrcsl8ti7EsBNecYXBkS6GroudcFtde4GzygOP2Fn'
        b'9y+e4wzxrm+f3ipsW9m14vzCP0jWXAq599bKX/SyvMtVNdXzqp3rPT59a1V29tG/PLVO+8e7nyrKwn+d89nqu7+sZX31YEY69fPVp0Zvqm4b+e9Ppc43Bv/99b9LXcl1'
        b'0ngvcBu0jT2E56A184jg1Oe6PKTxjBycXQjayvGiW1ecRfnB7bpi7gZ4A2xhrm0/JwMXhZIlaOqlpdab297gGa5zMDhD7mXDXfAwfAW08SvKHRaZRU0N4QrBXmi5vNo/'
        b'BxyNlUUXyNhgO3iG4oOjbJnn1IfBBHIiRagntmVFFe7iUl7gZQ5smwqfY96PXYZbQXesXAr3xFHwQiKq4Dw7WQyOkrHAvihwHLThh7O2pZydz6e81nDAHfBy2UNs4AKe'
        b'CADP4xFbmC2wG5wHu+B+CzggeIY7+XIW5yF+nuUND3NQXlRbjByPB+e/AffH4ny0gee2AOxjWj4HD6/HGTHzhluWwUM1qGFwhINqA3tIpkJwXm3XMOHynCg/cNMwgwva'
        b'FodJBT/hpSimnI+/EsULMjLFSq4cn8eZKeZO7xonKgQ/iXMbDpN1cD/0pO+JpnYaurIOPj0oiuoNGRTF3vcLH4goGPQrHBAXDofGorweTJ7Mg5sHRZG9U8j7D5Rn7qBf'
        b'wYC4YDhEejboVNBgSCLK6o6ydhjxWySc1VZd+qBfxoA4Yzg05qy8t2YoJN0ckj4YkjmugK3u/EG/uQPiuQ+iUnEnw4fD4/FvyHBIGC4zHBbRwf3I4Z2JG3OReAN2NmLn'
        b'KexghbZ+M3bI9dunqSfdNcYMdrXlz+7KMbmuuw+zQzjTNOR8jybyUbkTi1XL+pbC7o99fnuKn0hdEk7jOFyhZ1nxeADB40pqATX+L5xCfAqrTMoaEVaNMR9IWMGjJ8IK'
        b'bXktOU2raqqpU82wAwhr1BSWFYCoroqhQNkHgcxt3+8slMtSsZXLiEYUsE7WrNOul/axRjh1zbU/qd+NTL8FVTZuZny39Z3YOYAcMYokT8lwH09WHa1iehjM9JCpYoIO'
        b'/qSe7WB65lHlyAM9qXs+jlOY+EFgItNB6RP5pv9xVy2L71JlZXOe1Ek/hzmsPFrJdNE3V2VQ2/ik/3GX6q1dsvJQT+pSIIrUn8Qh0pWwSbmtf02nnKss/NmT+kTjtbRN'
        b'04qjKyx9m5Sj+9eAm2uVHRP4pP6F4WUcgzX5B4FyC6z9AOM4ST9tT2WwnmMG2/JWZ+yJ8L/2pU7jP/VSJ3QEcAwxKGKkXcM8+O150/P7SvKussQ3JKWCJ9J5vzLrPLjb'
        b'7U6938edWb1YyibU1RtsBdscSDBDf8H5YrhTDG8Sep4MrsePkWC4G9y0I8OICIMduZO+1XWqwvigqmrE046ykhhCWPErLPzqq8iFkvh3pZyc0T1j0CemT9EvHkrMMSfm'
        b'DMpyzT65A5654x7lTkSJmDe5mPowQHARO/3IiWSNvXf5ttDlx713IUjgAD+Uel4o40gFI04WtMS8VuEbjHq12jji3NJsMGJZaYRbqzGuH3Fi8qwf4a9REYFfWIsksuYm'
        b'RhHAMaoaRnjNaNPqa4V2y+tuXV5MMmdwJza8hSDOzfL00lnpgQR8AYZApScS912UTinuFkgUVrjbQaIrgkShHSS6OsCcMMeVQOK4WHtINE1HQCfIqaszIIkSi1V16hqM'
        b'btC/WstlTVpN3pcQ42RIoiXiqYpuNDWo7aRuNFMGDZJyaeblEBaoDWqjnC5Hm02A8VgTPoXTNLU067Hwb81Wq9IhCRZnRdKuXl1r1K6na9ZjxCdQrVFptCpcJREQ8VVd'
        b'A5Ld61CfEA5CW9pShUUoxnUIUFGTQaNrIJjTVoyOIYsSg0aQb+ldI9YVjW9bEG1U6RtQmTorgsP5aazRNWCB07DahEdfo1fVrlIbDdIswWPKgiw6x4G+0cvIGfUKazZc'
        b'UxZNnq8s+8FHLLZSDDhm0QrySy+zXKG0pVvBNIvG+mM0NUS+X2Z/ZdKWFwNyFp2HXHpZud44Fs+ANkpiPKSOOLpQUS5LTkxLo5dhnbAtNwP/SMbPqZAVzqaXWQ5WV8Qu'
        b's39SM1b52DbBWggmQOOC9he3bdnRRkKDbUSggsDRUKvXtBgtZAevK36hRmArR2toRuutriMKEbQ8OBWjfC0xf0cmW07PZrQiBCRDFUZVUxN+n6oLtelHCHCghUMNtFhA'
        b'q05DDO6p0DSs1SBSol6HZtwCcHLSWlmzUc2AEQFutbGxuQ7tjAZTE1pI1JZqFQJABFRqNLpaNd2MqC4px3QRAxVR3xiYbmsMdk3K6Xy06awbipSyB0Os3EGggs0D1mrR'
        b'ABjLgAY1k7PaYgywuZb0hDnymdZoNLYYsuLj165dyxg2ktep4+t0WvW65qZ4hnWMV7W0xGvQYqyTNxqbtGHx1iriExMSkpOSEuNnJ2YkJKakJKRkJKckJqSmJ2fOqK76'
        b'QdWLV5kJv9qHt8ExeMFQIi2SycvwY85Y0BeHiD/oFyl4jWBLoAljd3AjEl5JRp5ECjzLT5y+iigwjPW8xhdYiBjMqi75W6yaMmE7EHms+cWYeoFdYViGnA9bsaGqItkC'
        b'/NB7QTR+GL0ItuIfRNPAAXDRBR6e3kCu4cSC12EHvAL3VXCIBOtE8WA32xURzZeI1bypiIC+Cq/IkRxciB+To4qxDSx4bTGbCgYvcuEr8ZuIimemBu6BV4rh3lIl7Ggh'
        b'YwNts2zDmwdby1DRvcXKFuSUlxTBw1wK7gHbhPD0MnjCREwdnH6aXkEL5dIicBucFFAuRWx4EhytJ4ku8Dg4A68UZm5G5VkUBxxhgS3gcDIxAqgDt2CrELbGy+Fu1GAc'
        b'6CtC0n4rOJXFoui5PG6wvwmT01p4Ae6CV+JjwGtwH4tiF7DSgurItH6xnC/uwXorujqubM1GitgmjAe3XAxu8DC8VkjadF7OBteNc0F7pgmzDeAkPAxexxnc3OSwE14r'
        b'gZdi4QHVRg7lsx5xGNFghwkze761NUmzhHJUB5q5QjwhHMob3uJ65IKDmp6DHjzDGyjX+y/mNHWUem1LcN05+Cz7D2fXcd9u10kWaY+b8wYu69/q/d0+xTrunYv7t9zs'
        b'PaH5+s7pwqPP/eXY7fsH0mf8R/TyC8f/UjA981TOooCyspVOfxD9furwS97Fb9fML9/1zfGVLUFVs7dHvPKnj4LXf/Tm61+8OiqYnvKoNSdRISjqKpr37umcXVKOumRK'
        b'dMNL3xY/o0qWzn259cySdzP//KVQMPe8bNVGr9/+Pf32a5GL2tkH3/y38BMum+5knJ/58R+e/vTfn0qd/s60mXFXg1o3bJHyiVYoE+4Ah62qJcNmRrmEVUvwFnie0bX0'
        b'wiPwUPGYqoVRs8BT/kTTEpvMg/vhdniR0f+8vD4SvACvCcdrmeBecOUhPiabB3tmPM7j1YOjRM2yKphkAafBERF8AVyILZMVFpYWx8F2KYuaCm9zkxrBBcbGQO9McBn0'
        b'rSiOiy5A3UHLDc6x16OubpF6/k8MrE2ooMGOgyUv29trgaqurorhMkZENp5yLJKwlX+ysJUlAsqP7uH1GM9uOrVp0De1gz8s8u2KN4tizKKkYXliR37XTLM4ltHQpB98'
        b'alAU3mMcisoyR2XdnG+OmjEomkEUKnl3G8wRpYN+ZQPisuFQaQe/Y22nx7A0BXk2mz0jh2fkdvAHfLLMntnD4TEocr0Za1uikW9Np/uwNNGajw5HPlOn2yci3+Foea++'
        b'n9WLzbZlmsURw7Lk/pz+3N6lKDzDLI4Znuo7NFXatbyDM+wpPuLe6T7kKTV7SnvDevWDnklDnplmz8ybkR955thxxlMYzvgyZb3IeAU7V7FzDTvXsXMDOzexcws7r0zC'
        b'S9stBp736rE/esyggx5i503cNuawsX2E77G9kXIXrNh5RNQ7X/1oJQ++HdjLz6BuCnM4HKnLiGsdvuxp4ZpG3Bhe0xrkq5rIL5cYlnCxHLrXqkeEmNNB/B2+kscM2jbe'
        b'WoEdGfK0kqEOzHI7TcRyHyYmMhF7jc/SWMSUqYtyCmK/salTYtc2xdPCdAscmG4hYrrtTtnsGXDEXgtyhITpHhfrcKrWzHNkulW2W5g0Y0QPsapz8EMYJkQj/gDtBsSV'
        b'Ih5GZW/vF/M5cXSDvtnUglIR+6sS1DY31Wh0KivHFIOYqRjCOjCcA1Yp2G764gZtMrIAy8j/j8t/EpdvD7RZ+ICPibEptR7j9h2gmsnPRFkLEJZt2Q9cYLVVx+wKph7L'
        b'RrDEMVyqrhmrPvSEL9Ux3ObaZswmappUWgvfuuwJV3IR9z7xpVxbD/B+ZNqvaW5ehdvHMXK61LI6KhKmm2tWoolGMiRzUqnDUkRGWkKiRV+EJx6JNLj4srHruLZGbNs9'
        b'i1YaTCqtlkAKWpg1zZpaGzQus7u96yAIWdCD4zSRR4PL7G/0jhNlcPbHxBmHe6L/C9JJrnqtusFyi+f/SSg/QUJJTktIyshISE5OSU5NTktLTSQSCm7VUUzhjxNTaOaE'
        b'OGgtj3KencvDosbdaU2UCSPxhbAXnC0uLIV74gpLEDvdbuHi5k8kajwN7rikeMFLxEp4HuKX92BJg8gZ8Bo8YpM14AUixsAtYWnF8qJSuBtc4KPqn1Q1aINtLuBsALhi'
        b'wlS5HB6CRw3lpeUWg1e4iUVIsGlFrGQrkjkEiEnHAtI20I7ibimWg+OIQXzBhQLn4LPCsk3wVSKZgZfBEXDdUATbC0vLi7Ghy63w+vwELiXJ5cC9lXCHCfOkc6rAdkNM'
        b'KdwXnQSfxQeE8kJwIZpFBTfweOBghonGNW3LBzeF8AbYt8AZtstAP5L0QB+b8krmgFNzwGGTFA94Zwbiba9Yjq/70UTgI2wkIoBrC7Ch9UTQxlsHWsHr5DYYOAl2wWOW'
        b'zhVqVXFSbMpZDF/gwFfDk8mSea9lU9xpXYiiVrs+V7qKIjakwQV43U+IlhnsX1xBVZTCmyasKoRHwbPwJSGeLDSnnfBGARLK2uFBcSK8hkW1NnAOhUvgvgIssCz3dZ6b'
        b'UUAEUzoNjRpzXtPTC6nCBfAVYpIaHAK34pOJFAdeSqQS4YtcYjEabktbAA9ykBhkiKfiF8/V/u37779/6MWlnFs+42LQKm+0mBl/14lPuc47wMYy2NqVEsqUT6YIvgj6'
        b'8fS0W0TbgriF2Bx9fJESgUQB3KuIlqIRPAevLyootNqfl4LrZAL5OrcVaJTnGEs1B+L5Cng4uYhDsUDXSniegudhr78JP2nRwFdrhWidyuKmiEDfgjHIcR43P/AaeBke'
        b'4FLgGaXLErhDbJJRxNpaJ7g6JizOj4aHFc5YLFwNtlslQw4105vvvt6fCNaL4bPphiJZeSkaFgK754rjyyyyoRR28cBVeBZ2mMjp9i6NLrZIBO8Q+zpSPiXEtlavSFYR'
        b'o+p/qi5nv8lvdXVvUYl+vbhp9nLmwkV0Mlr1KxYtQBboYC5a7EUD2R1fXjof21XHldlfaYAnwFlXNPBD4CSZLjSlL4FtsfLCuJg0+AKL4oP97PilzUSQ9gN71hcTIQne'
        b'TmbrWRnwALwl5Zgwi527GfSQUmiqnrcU82hizJY/14CNbOJy6Xm4WE0DEbQrcgJji+LBQccRgq3guuaPz75PGZ5BzHd71K0XF5SWg1meJ/7yaGr0i+IpM71yC0bpDZ3C'
        b'/ItBpa+8GlUW7ndnuGr7928H//GLq8tky8oP3NX99lj3o3WDP3soOv06ldnxAvuLX73d975XXfC5pP9623+h4ZvdJ/b9Rjrs9/QNpy2b2P1f+9/v/DLrb59vVictpO8f'
        b'fq4u5fmnV65LyvqgdR6Mahc3s36za51w0UcP7z63Tztb6xG4urs77uWVm4NDjjS+/6enWn7u9vcDNwJWf1dV+ofO7H1LEzU7n7/xy5a0r57f/6dZL/zqtYL3Tny248yN'
        b'B4F9rm7Lkjpj1ly8U7no85iFD7OyFgyG5I/ovz5kqsteeP4vm9MTjrtOpfW+//jsl7v/EfX7mc1fff2N6NOoHV+HXjpx2P3TvvbfvZ3k/+LvW17Sj/6ytW/jf9092v7g'
        b'H5/RZ35T9O4tQ/GiWxmZN5a8O7rbmL34D39eV7Tf69s3NbHw3rfCjYnf/ObDD9uufPzX6av/6v9oa1lu2NVHEb+Jb53+4e4puV9wf1u0WfjpV2+mvy2b/of//kPpkN+i'
        b't86/8PyXWc+kP/iP3/bdnreF/lrqxtz9OAw61zleIPEAx8AJJOdneDJS/ovwwgqbkA93gu1WQX9MygfnwHbGAvpVpyyrhA/aNtgJ+YvgcXLHQ8eWF4/d7aE88sHhhRzt'
        b'FJSKASgYHgGvxsYwN0AolyVs1Jf94MUcsJOxofmiPiRWjmlHnDPYiWFyH1sGtgST2ycID24FJ4tLYvgUPAxeYa9gpSP89ixjObPSBM6VlMYhrAqPbihmgctwD+giHUoE'
        b'B8FZRGvaCa0JakSE9Cl2FGivfoh3Nxdugbcsd0QWgucs10Ts7ohEwi6SsR4eR313uP+xA/TbHT6VgyvMlZwuIWw1gAvzNxaUyTAxJJM+BXZwUPZ98AgZqBbeWeKgv5g5'
        b'bT2+giP1/ldrMCZXbWD8QFvMyU2g33DHqowxGW/Ex0HHMZZA9Bw5bEbPsVlI+YX3zOlNwaabB30zO/iMSmPaoE/0oEjaO3sobqY5bubdEHNc3qAoj+g0cu6WmCPmDfrN'
        b'HxDPHw6VMzoNptj0QR/poCimt2JINsssm3U30SybPSiaTYrl3l1hjlgw6KcYECuGpxVivUeG2TNzOBorOTaZPSPs1CJRsVjvgkJPmT3D74kCu+p68oZE0WZR9D3/6F7x'
        b'oL+8Y/YnPv7MJZdbYTfrXpWaIyxG5FFhS0Gsssk5mDWcntWRP+Cf/IE45YHFaxan3Auke6YeWzYUGG8OjO/nDAamdAiGRVO7YgZF4X2i3qVDsulm2fSbtYOy3LtJZln+'
        b'oHTuOyGD0mLSZsk7G8wRSwb9lg6Il97PyL41927+OwvfKB+cVjGYocQjSzF7pmJdTWo2bi/RLE56EBJx1veUb4f7sMjnSFZnVg93iE4004mDosThiOR+lTkivaNs2Mdv'
        b'yEc+ECTv595wueRyc8bA1KIODu5W+JBfjNkPdS5mOCh0KEhuDpL3GsxByR1z7/n4daX3ZJr9ZYM+8v6IQZ/0+0FRA9Elg0GlA5LSBz7+XQ09DSg7Sh2Oje9y6nH6QBI9'
        b'7BvY49TLO+U+6CsflspQLK/b/W8PouP6K+7WmIMKO+YOxyV3zB4Sh5vF4T0Ks1g67OnT5WL2DLVokyI/8ky0UyCJGAXSW9h5Gzs/w8472Pk5dt6lrAqkf1J39Djw46Ye'
        b'1yTZlEkj2Pk1cpbalEnYyOZqAYulIcokDeshcX+sMqmPn0ndEuZwObXW17L4z/ZtFHzZyV7xc5hSOildlFzydRS2krG476Zk2b6Rwquwuyqt4wdRSjury0q+gzqHl8Mn'
        b'Sp5xsZObyB8vcbgzEsfWp9jkAkBC/lt1/Ew/qoLEhlbysOF8OoHvQ21YWUgRLiMGvAJ6DaDdeTWH4riz4O2KDPjsJhM+b1+uBtfArVQFaK+A7crS+fDaPHhN6ZaWkEBR'
        b'gT4chO374EtEM98gr1fA9orUBLgnBdwCRxGj77yaBXvA6+AWyYBElr0ZuCIkbvTjylgUL4aFJIdXwR7C0eSJ4TbQlg2u8MkXURB9OE0YpCgDuAZfgC8i/BWJ5Br4sgRc'
        b'jCLnGHxwEQlQ8gRwGhxOSUplU/zNLPDclBbC67UsWjn2FZEoeNbyIZEON0354O/YhiQENxXF5vYKJOckuJo+SPt3n51u3MYtvXwn+aD8XGTIG93Cmj0Hg++2K/7h9r3P'
        b'2quil35zqWj+h4+++OMfM95d9aWb/JpgeMi4kVoUd/dwr9d3hoP5339aHvj9+rw/9X20PCQa1LKGevMeJj6iG6bIG3Jab685nHp803OdoqQ/eef/4rZyCevtZXPM0v2R'
        b't//9Z5853fuKXrZb+xr15+p3M0uO/vX43zeda+l/5z9KKi588dbi1JTKn5+9/HHx1zf85qwoipmxYf7f11eyPhz48wcPT8sjb7d1/tcXw0+l/2b9q/8YOqa7lug13yRe'
        b'+tf7yjXyj/zK8pb6iz713vFm1Lf7Vt0UHd087Yt+BA2KjfGNDx+d+yxg0bVpa/6QeXt++ht7M7LC5u76453fssV/cVEfcHr99XPf5oyeqDW/ztnfsem/qeG3Zh+hwqRe'
        b'jH3fF8AVQL4yFF8GbzhRbPA8SwkQT8BwAe1INjxiJfbFrCTEr1z2yyDfTUAS2hlw3UrrL4FeTMQxtZckkfsjK8gFU0TrYd9TtiuhdrQeXs0mH4IJA7eQMGNjmlwU1qOR'
        b'TaCbZNgIt8UUl8UhMWZ/PDgC74CXuJQ7eI1TFQAukl4ug1vADthWTL6UxQ1izULMy/NLFxAeiC9qjrVjxxBXcBx/v2Ex3EfqrloIDti+QgMPh6AKyFdo4EFwmFzWRXJS'
        b'B3y52PHO71RwgQvvwH5/NLjXiclxuHUVeLbY4Tov6mgbi/JayQHnXRHjhPcgONSoG3fCY2X8ymEv4v12GxjWr7cQ7bK2scu5tAZJAB5BnErwehOZfnDlKfiSlfkLBDsI'
        b'/4eYv2J4lbk+vEWajpieWRK7Yxt/C+fHmYu2ZJv9Z3PuBIJLJVOYE58t8ALYQ8zxbo21M65eGsmY3H0Wtq3G0koQvAT3leMPU4AOdjN8sUjq9f8j/+Rl5Z/Gf+llxKmK'
        b'+QSP/W0jJoawSycZdml0sRvlE3xE26k9qOvgYL6koUfVvbI3ZkiUahalDvvTJ7O6szpmDweEnCzuLu6YM+wX1Jn3wD/oZEZ3Bo4OPlnYXUiiO/KGRZKulCH/OLN/3KAo'
        b'btg/uCcEZxpl035ew2K/UQ76fSCWHCntLB3lIf8on/IO6MrpLBoSR5nFUaNOOM7ZEnekvLN81AXHCGy5Is3iyFEhivvSlfKWdHFOuna7DkSkDUrSB8UZo244szvl7Tvq'
        b'gX2e2DcF+7ywT4R9Yuzzxr6pyEea8MEhCQ6VdZaN+uLK/XDlgp46zCtON8dNH4iYYZbMGBTPHPXHmQNQZkuPA3E4CGUfEmd25/XwyCeB1g3SGYMBmaPBOJEmiekokXPW'
        b'9ZRr7+JBOm0wIH00BCeGosTRMOwLxx3A8xKBQ5Eo/khhV85oFA5FW0NSHIqxhmJxKI5UL+2afbK0u3RUhqPkeIzx2JeAfYnYl4R9ydiXgn2p2JeGfenYl4F9mdiXhX3Z'
        b'2DcN+6Zj3wzk+3Im8nXwR3NZlK9/B++Bp/cR107X7hW9aYOBSR96JlsiuhQnF3cv7mnoVZ1aORSZbo5MHwzM+NAz83dBER35w2LfIyWdJadEPQtf8P9YLPuSQwVHPvAJ'
        b'PLKxc2NPKmKzh3wSzD4J/ZKbmYM+cwY859gxY+4MM3aLADZzuGMY4RmMKr1xhIOA+sdxXu5WzusxpmsUO18i5wLLYtj8v7FhczcWKw6zXHE/9qLcSX48dVGYxfm/vTT5'
        b'3WEB82DVaH2GZjm80Vp0znq10aTXkbQmWoXP1uxU1uRci16lXm9A+Vr0agO+Ls3oui3KeIPtgMyi+MbnU4+flWkZDT+uvma9kXxi057Nc56AzWM+TfAa7MTSMXwWCem7'
        b'wSV4AFxeBC6DS+BcBOieD1p5lARs4WyEL8QzX7U7Dy57wIOIt5XD9lxKDtrBSaJS3hQzG7GASUXOq0HbIhl8tlgu51BisJsD+vilhHecbWRT77Cwrzrut2xf5l5HFtwO'
        b'Xie8I2hzUq2nuOBFFqL9L8LrI6wqwr5FZxqICosFT8ObjAprYwph34qawEkrZzkT7rTwg9RsUgxejIF7wTPLGRUXVnCBS7MYZdqRjArYU6RgeEg2aGcFgHNwB+EhWcXw'
        b'eIAKHiS95+SwNgbnaBYsKOAa8Dl3VVISvvFafbfjZ54g6M0tLtu6Et8qOYUN0bM4eVIRJ2/rPOdlnrFn3q1+u/rMvHxFr+/6995479R7r2jpqQNpa0q+mZJ7pmTe1CtZ'
        b'HQ9Ta6of1M+jbrVvr7sRkfObz/ze9XqPrV8eVJsQm/jXq6rf1zrXC9Vu9U5St0/ffv45eGjKqam9B0Rni+R1h9+4/7a2+vUrqpcqapwlBeoUVQp19DPQ+LbzN08L3vz+'
        b'lGuM63Ff6lfX/KUxz0j55MZFyQb4qjB/gqu3cGcZfJnhuTqD0xDVJ9bs4WW4j1i0d/F6iNc8FL4WnQCvxMpL2Wi6etEc3YxlHvtcaVKHwJcRG4XZgUIZmxKq2bAnis0w'
        b'MS/FEZ3Js+Dq+Bc1KCX2KcIM1YHb4KbdN/kwK2QE1znN4KXNUud/mlQ720i1jUCrDFV4o9kRaEsMIdAfUgyBXuBBUC6ilRHSs2WnyobCM8zhGR+HZ3WWIIobHHJyTfea'
        b'gci0m5ybisHgnI6C4eC43nXm4HTki4w5qz2l7U8ejJzVMedg+ZdOVET2qCuqZyg8xRyeMhSeZQ7P+jh8GqnJL7BL1R2JaLvE7yS/mz8QHN8v6q/9WJI1LAnucTJLoock'
        b'iWZJYn/0R5JsHIWk6yFJvFkS38//WJI+6sSlp3YUIFodFXtW+zxq1ByZezMKOaRlDypiOiLDksAO1590exlfidezkPN7+9vLczx+pLX+S6hgH2uE26IyNjp80sUmZmox'
        b'UuZZPumCn1bjb4Piz17xbZ914f9rP+vy3RU79IwxqUG1Bvu0WntEPfZSGPc9iy6sp2OwL4ZG1M/AnGViFKxeh+0g4KPBGPkGTUtMHKnIguv1zEmiAVuSrbOdT6r0tY2a'
        b'NWo5XY6PS9dqDGobfidlSIdIdhVd36xFDORjyHv8d0ydy0xYr1uSuiK2AG3neQVwr7SotAT0VRSAC7A1To7Y53rYXgB3ObXIEWrDmH4BPLqpGO3+olI53B0PXqqArUj8'
        b'mo8YdVk0tvgVvagYXncCz+YghE5Y/UtpiCk/iJBoN0KPWJfL0bLANiR+7SdHWfng4IJYJ/wC78V11Dq4FT7HnD1tBdcksT6ws5xNsRZQ8GjaOg2r4E224VuU+Nfh/Vdq'
        b'j73rCaZYsGduRqlvSJxbb0FoOicvJbZkRteUyJPvtsKKNc+XKOuoW3sOuvokhNzaEtvqP+j9R64i+oRTSmyrz42nPGeeWZ6QvOsvL89KvyRl/VJQ76JK3blrSVBtdF4H'
        b'rbuy03famxJJUbdEIjiU57t9R6IyP/pYUs5igetrXq6u92f59S4Q3+gWuH5+s2ZBgMI1OUDBfUMl310uG3Db8V9/4H69yPlVL/mjgtorYYdcPvtd9UJJ2+6Q/RGHIgqm'
        b'KjZFJ4PSN6pbxZXyjtGihnl1Azl/8+id0V64NScomlMhevtu9S/iftXx9jv32FQnHbXhxEmpByMbXQYnNseCNh1eMsSnpLPAy6CvnBFrT8Ety5BwdB5ejiuzfFrZGbax'
        b'NxmVRP5ZDO6sRKLv1bWyUCmjkXcBZ9ngBf8UUnXOYnALE0IkLaIVZlP8MnYA7NtM8Ks3PJSBvx4dJ0cC65FCki6E/Wx4O3AaI/VtBUeRsBkH9pXDc0rm80XCWWzYBU6B'
        b'NkZnvxuegefzjLia+HIZ1pOwY5zBHdL1JenwBiayUjncTwbmEQ1fSOA0wAORzLBfz3WeAnusxIUQFhpsZcTJ7bMRLYnHB9gyuZRNeYQggDvJATtXLCE6/7J1SeBQOZFw'
        b'48t4FH8a22cZYNTrXithT/GSMhu4u4jZ4BR8ZQ0hTLHgUq0JvIzVBJYJyWVLwEF4lhEmL4GXo5Dk/rTDJ1zR3J8mHV4J++BW4TqmW6hR0MuOA68ppcKfKkUKKQctPEOd'
        b'uHjXj7jZSBMOErrkwXzBdbTIkxJPPZLemX5kRueMnvAhUZRZFHXfL2Qg1PpGU+RNkqd3Tu8RD4kizaLI3qSLWX1Z/XVDsdnm2GyHzJIALMwdc+/gWbTJB6cx6vHeqUOi'
        b'BLMo4Z5fSE94L6d3+aBfFiJXkbH4SzJnmroFXdxhiT8u3FPxsSQBSRVRKQ/EPkcKOwsPFz/wDzyZ3p2O39L0hg/5x5v944cRfXPudu4RH3d3qOReYEhP6NmoU1Fn407F'
        b'9Rr7KwZDs27O/jAw5+6C4YCgkwXdBT0Vx8secaigXJY5MOcr3M5vA3M+Dsz5zoDNW7zl6TUnnvdWvGDODBeGvLkw5I3D+qc0w0Q7axNJGLI3FRfFLwS/twokWAm8EZE9'
        b'yVc/8ktLRCA5wo+izgqTOKhrxyjy4baxQxQ9vvOnP4Kd53CaC3OJVKM26Htx5PPYeZEh29jsxwhnjnJBGfnWiR5/5xUhfcuflMf8sNF/74ksS+KXUHXNtVVVzENj5xZ9'
        b'c4tab1z/zzy6Je+YyFVLoiIftXEHZK6IXUrx/8rZFeY8Hz+2Glu5ZquDDa4YNrGIiZ8vuWw3z6+cKXfvU5w+w91s85Ll94JCejMHciu/5LDcq1kP5uQPz1/wiBPmFjlK'
        b'IedrHo4d5SLvl0Usyi/0nqdsWJz2JY/tl9Fa9CWf8g255xk3LE5FMb7prYUoJijynmfisHgmignKYbWW4e8l0fc8Y4fF8ShKkthaMBaTiWOySYxP8D3PGCbGJ7t1Lorx'
        b'D7vnKWcq8kcVFX/rzHLLY33FR73vVpwyXEp+Q/Tz5HuBdJ/oVtgbyT+vwyOoYD2YrxxevPwRR+aWy/qSwi4eQwUaA/Z/VcnCgw+7pHgj4udOd4Pv+Qd1G7tiLnFQXQrz'
        b'wiVmlRpX08BC3G4VvjXLKWe5JT2ksIvrQQlc7H9Uw051y2d9Q2H3Wx3L1y3wqzTcsTCzW9Aj9lS32FEKOV9zKPfgr3FwzJYoPIpEyROGQrhTi5C6wd2dQ7kFshF9u8kj'
        b'zwPg8TR4XAh6MTHZK8S3RObh2yHgKrwekMQNk8Oj/6ffSR13QDL+EaRTGbl6I4SX4F5suHVFQwgVAo9JiTwLjoJj8ECxHPQnoBa4WaAbXmetxifJJFkNTsD9sUUycLbe'
        b'4fvk0bnMmUMtuALbCuMWPY1loWQu5Qza2EXg4kzN03NEXAN+plr2578yzy4lb76zhVVyyiivTaj1TD4zbZ5PrG7Fmb0Jv5ll+qLrz9u6ty14qbu0u+PDlpr5cFudYDu/'
        b'IqXTu25tQp4zR7j4rIDTIKR+2SUs+0ODlEdo7SwpbLXYbaD4tauw2QbwqoxRzp5KQcK3veoW7jGAS6C7mNHmHwRHUy1n+iyKXwcv4zN9eDifSe0AnWAX5hCcnrJT3XpE'
        b'WFmLWxHFhaVN8HVL4gq2GuzKnPSRp2uLXo0YdXUVuWsdwbJ89xwbxcVUc9YUSixhyFvr7AeiqeSr4LNPFnUXHSsZJIZyEfXL7szuWtvrMihKGguvGxRFt87+xMN72Me/'
        b'a27Xwo5NHVyU1lpsL0+NcHGrI3zm2fkPfKUV9404IWy7r7Q+7cli+f3YL6A5QKSn5ffrT1C9M4SPmRdLxK810eZgW8xbcZfzQikFx4/CxsUy2Xo+CfNR2ImEnUjYGYVd'
        b'SNiZhAUoLCRhFxJmjIvxiPEwns24GA4LUXtOqD1P5ovhiiQlK4WlmGJp3c2S6sWYDlMkk1SxJdUDh5V8pYtSkMJVeFtiPRUpKJaLSk21muiyGATDRsA4KdhcGjahxrP+'
        b'V4iIeTCBxc95zG9Nt/5yrfkf+308noQVPnKPBEohweWrWApfnI5+/ezbQGF/aznkD7DzB9r5gxTByKXtYkLs/KF2/jA7f7idP8LOH2nnj7LzR9v5pWP+x8eriJGz57AU'
        b'sXK23mu5KJRa7qWIw/C7QEqN+7OiSqulZkt+2T+bn7TibTEPxrwkFqQ4KeQEJqYS421OBAZ4ingS56NI0EsaRAgZpyI2CbHIqnwkLGsQH085nKrbtArYOBpW9dqdqmNz'
        b'ZFzUEv5iMd92lu70LzxLH/dly/GfmxcwZ+mpUdzZMuahYNye8FLmiqVuSjv9KZXApuZV6/rZUibyauim4Eb2KI9KUG38JiGCMuGnNYiiXFU6WFay6dOuIiJEbBHuh21O'
        b'lKLB2VMK9pOaBJ5hnjvZrRgl5f5RtZz6o7WXBJ9pfiWUsg2YE1TOGGVEcgk4gC0lvVfkGnL+zN55QcXuYXtcOSWRPu+411/1qqku+DcVdan7/JmEhHDBtnvvLfzDrDRG'
        b'Zl+bICxpiKl1fmd5/c1bJW+4vnE+jk6cenOl537vnT/j//ESa/0XLUGvznjnvwMSNmdxGrKoN6LFL73j0qqQuhB5K7xOgT8FC59biRgGDuVcwTaC1yAjeSamgjOgDVws'
        b'AbvT8WkwP4o9BWwDu4ngaqz1Hv8UDbwKexCBqXuIWVqwdSPsfNyiD9w/B27D0xXhy2sEW+FBoq0Mh624KUzhYqNlTEaUxyeA6wIuTwOtsI8cuSIh/hlE0cgXnEH7Zh05'
        b'Xt6LL38d44BTGeAA6ZkyDL5qzeO+EO4vBecplOUwB7wQwSJS+SbQA7eDtnjU0Fbwenwh3MtCAv8eNtgRPeshosAU3BIFToK2tagOwiqhmsD+ckSCd5fDfXI+hcTz3sxi'
        b'Pni2GV6X8n+Al8YbZZz9IS/bznI0QLSeYkjp8ilUcHgH95AQ33sSH1uCvIIvBRQd1jNtMDihw3VYFNwTMigK63Xt1w9GZ97UvlM7OGM+ueyUPeg3bUA8bTgiERsDCh0O'
        b'je3N613QI8cmioZDIohlIMtPEI2bGA4J7+F1cA+72VFbRrwb4ZFr9yNc/ApoxHVMntI1j7hodC0mIzEiO5GOkxH4LMdQdiaC0hBeimfbnUAtm8JiZWCBL+PHCnxH+THU'
        b'S8LUn2YfyGL6hFeFhzaJXRH7VbJaBcI38cbMoCw9upQxMhIwZjN/nFkRuf4Q9diHgH+kNSC3Kvupn8wKygwUMZvtYHEn/oPAeKaDQXYdHG8QSP4/MdEiqLKBwpO6Nhd1'
        b'Td9FWZDgd4GF1kLWdz//qv644O/VqquaNJPas8HdKcLdGbOxMxUrg+h6fXPT/7wf9Y79UK17Uj9KHfshJv3Ar77+RbPBrzI2G1XaJ3VhngNMLzu6zGIBqQIXtL4mm7Q/'
        b'/7tnvg0/TPh5DOH/BZ9D+nbSpbrEI2EVQ+Odypyw3UMqP6q6BIavpzQPXitmG3BbEb9eY5Xttrhs812y9TT/0BHwzt2O9yWgZ0fe03+/Jg2r8Dko76hQPXiPov6Rxkv9'
        b'pFPKeojN8fi7wUMMuagunpBgEGIB+sHtyUQrovoZmWJPFcaM52A2DxOFOi9KEnBkU+emnvlDPlHD/gH4LmnKyend+B5vb47ZRzbgKfvpBnQWoFVVsO2OoGq9fsIR1P+p'
        b'BuGf+OC5BTqe4fOIMNcTt1MrmZ4aRu5NrJd0fP4hLs+iWO98otGnqrkGzARufPaLMdjIlSzeWoeE/pKE2oSDUtGjyApv9zt/npV0Ymsyh3oEeLwj30jZ5Or/JvBsKQKL'
        b'KpfJ+AgCFsX+hNsCd+AdHVbyx4D+CJkcX87fxk7mZEwqjHtUkYeDmg3qqhptc+2qEV876HFMIlAUY4GiFi8qOg7f1+5XmqOyh6JyzFE5d8Purh2MKu/gHnHrdOtSf+AZ'
        b'Pg6MRnjkmd0PyN2LsNy9GDmL7eXuJgRIvj9a7n4cyWB+9et6yiptHGYMT1MpnP8dUBp/EmixIKs1PmJ9sUrCQcLE080Zayjmic9Z+DLYC86hzM1BG6gNsNWVeYS2ZTl4'
        b'HpxDs1MGT22kNvquJq+gGjOQoGEvZSCQqYj2di2TsagUsJvvDvckkxdjzh5cynl2GAe/GGPPaKHI46fTHPz4iVrXX/i1y68lpXPDKBM2vL4B3Ihn7LnmTreZQmFeQFlA'
        b'0MGU6ynYLYBH40DnmEIxIAGchm2F4BZ4Ic5BK7YrV1OUsoJnuIMyvTPn7Su1z6HdEf3eg9UHtobsDzmUs53FXtAlkTy1XiLJ7Tq05fkzez3N1fnnpLMyffk9vx9Y7Fnh'
        b'6stNfqMC/HIKt8+t/npMQ3XB7+urW+t3nVNv7StVc+95gYA3t701e+FC2kWx+89+K262eZ2g9SHvtRy5vGTOrKa6Z469ta8uzOAZdabpzLylrGdWbbt56WYHpz5GvuKN'
        b'89dLrpfQT1N57T5t06Luz511r+azmkgT/etHKRxO+sB7Rv77KdSMXwR8cufXUiciEsBe+Ao4QI7S1sK9ttO0BE5DUyCRKlbBNnDVXuLJ4VjNb3R7PSSPGA+Bk0stQkNw'
        b'7qTbfXEYYxL24mZXYUy83CIY2cSoYHCFCy+iqNOk0rVVxBwrro1ABjhfBNrLwe4KS618KgG8xA+YHcPgkB4VvFIcB2+vsDfdIVnFJF4wgotohCtSi+1UgaXTpdwJxRYM'
        b'5TbznoiLWKvXGNUjnnY4hsQQ1HKFQS1fr/GiAkM6Zn/iH3xPQhPidHB9T/LBp3uNFzf1bbqpGIrPMcfn3K17pxauuh8UPSDNHgyaNiCZZqNjvV74eqWP7BKnf/YVF7NP'
        b'5s28QZ+Z9/yDuozHMnt5g/6y+6HygfiywdDygYDyYUnAkCTOLIn7UCLHZ2xu3W5MuFfxoSRxmLmM2RM6KI7oFV/07/PvXzwonWEWz/hIHPGVN+qpHY7jMziOq9I3GCYk'
        b'mHwrnrMgOoyd9HXIWW6H6B6ZvH7CwdUhfjh1WhjPKavlTkS5yK0NllW/QrQrGPOxU7gWvMd1uLXBQ3jPDg/aa1kQhuPm8AjeGxc7uRJ+vPkmpzKC4gLAccTS4CetwVVg'
        b'FxUMt2YSA9MEz8HXwOWSWDQ/JhXop0zg6lwG/Z2XzSRIcYMBbkMI6lqTJjb5tzxDDm5gqPtKbbdVu/6UdptvXleepKQ75Pbyzzzr3XpLBPNMWYoEg/NBt7D/r7nvgIvq'
        b'yv5/bxp1pA0wUofO0JuAqEhVuiBgVxhggFGaM4Ao9opiQbGAdbCCFQuKXe9NMRuzYTLZUNJM3WzaYnQlm2ST/733DTMDmmSzu7/P55+Pucy9777b3rnlnHvO9zjHG4Y2'
        b'mBYHF2dJHqUZUCZ+BoG3jqLTGP6KsAN0RyP2HhsjAzRJGtPgtmSasi/loGm1CzSA6/DcbxD9aj2iJxbsI4iepBCiD2KIfjDTihrr2Cv0Vgm92206rbt5auHkJu4Htg59'
        b'9o6DbEro+LGb5xluj21Aj3mAHsUZ6LQ+5ZgXlns9f5WqMKAYLlq7vy7EmRahQDbMQ/+EYVisaNpzEPHQnn9kkxWiYkaQnHaHIyI9jh7JGSCiw+I8I0J4Bv8nhPfcyf5F'
        b'Zzc9AjsH9laDZtSHuKmOlGM9vCHrMhSyFPhKtv7k/MuFR8R9iJb2PtQc4TlFmzpbQoJXr+GtL0j6KD/fUEK/1hoSlyDvj2u5t3CsZOEa17PhW5fHBJuPfVj0EENo0lT/'
        b'B0ZnUsqGv9e/cW9qQGnvTRkSMiFXJRo6stajI10yIaYJGmKaZ0UJxu6chEin39ZF6dFu1Wvrj871/Q7OSu6BlKbEfqG7Mrd9iloY2sQd8PA+49FjG9RjHqRHV8b/Bl2N'
        b'braxjsy0YqoK/FolCir1KW0uprQnf5TSJoymNO2aUkHpC4/J4magWd64/ydU9hzQ6vPHumEqIxdoe6zAtWz/GXBPkkloEpviGtBgLdgENsi+MHLkKKJQlmPPDC8XHkKk'
        b'toshtYcC4MAvqrsfG2N4zDLzFcGfzCQ9Umn+6sdpLdX9QmGOMFJNfTyOC/pXo/WKqPUqwYFlxO6WNR8cXEJHgOO16ND9q0TGHSYyjSFpnsZzhYbKhHpUNuIJITQ/DaGV'
        b'aQmtz9ZZGXqW3ZHY6XEmrTtc5Rer9o7rcY1X2cb3mMfrUZbhKMoa4BVLCqsr5S/cLw31SIohKCx6kFejYIk+QS3CBPX4DxIUKb2F5021m4SyxWaM4SIxYSTGjNiscYCv'
        b'E5ktki4d4NdW1hSWSuVkJIJHRkMGTAoxWqa0oloqD9aPhAwYFskUDAwmtokc4NZKqrF/F2lNtaSOeCnBehwDptK6wlIJ9smBky6RnFh9PHjAeBjmUlakB9B1meSollWX'
        b'SdGwYg0TeQ0OanHwAr8zGQOG2HMkLnLABP8aRsUiyQSNltQXIl9OYxUUDHFTUFlHgMAGuFWllRXSAXaxpG6AKy2XyMrErAGODL05wC6QFaKIQWx8/LTcjJwBTvy06Yny'
        b'rfhLbaNHsWB4zDFP8KSKGjaj3EORKyWsRop3BirXOMzw/4QZe25vsH9u1hYyzNhfHJfT37OooKxQyYTXPcMponVe55KpgFfBBXjLTM6lWPAk7QP2gbOMquXhOrBdUV0L'
        b'r6bB42awy4SmDOB+1hh4sbQGT+9suM3QF1vbn/NOSg9ITs+CDRngnB/cEZgCbsE7WUl+KYGIs0Ln+GGwDdg81zR+PrxCdPbTwXVH2IwVg5Yhxo9Kh0fgXaIjDzp9QVdo'
        b'WJAM7OJQtBcFmuGGORp0CNS4/aEscFpEUaFUqBvcT9JTZ4Ij6IUViJ2nvSmw2xIcImsUH3Y5ExszuAODaKBDl8kcFjzvMJfUEwOOuaO3UPFKHkWLMWLBDW9GW+QQ2OfJ'
        b'GNGN41BceJEG68Fh2AxurSRDOZvnQ+VQlDDRMt9VzrajSH/AiVkpqDi4BctIfCiwF3T4EVSWmfA6vJMa4B+AgWnS/eGWNJqyBccz4SZOjEkYKTBOKKJi0LLwj1X5y4PS'
        b'2EyBijnzUHkF8Cqbov0o0AK2wzUMzEsXaErxhQ2gHR4PDEhmeBYzsI1dgFjlk6TApSwbCi1oQd+L8yeycwuYAjOgEp5CRWYuNqBofwq0BoLdDIDIfrgXHkbMj+8k4maX'
        b'40eDG6jV7aSsC37R1HJU1s7Q/OnzVvgw1rVgNzwLToaGgc4cZ4qiAyiwH25kjCfANdTWU1h3HnX29EqaMgpmgRa4ETLuX1aZpVK70ejXm+f7bMkt0RS3Bu6E63Bx+aAL'
        b'ffVAChyIXUDsKSzAtkWMfQBRe9zImgsuudXDtQycTRqx/M0sS8z3eye0hulnmXdeaFg4tk+kyMjtyYbdBJYHdDuDNakpYM8CbEwItzNWkmPAenY0aAYXy/Bi7j4ukkLz'
        b'ODNakj9940JSnt9S0IQKRG8cYpGu7ps7juB7QqWpTyrGEW3MGL7Lw05QzoBDYDcHbAFKeID0DnaDc0wRdybySOdawOoCYqDiAxsgahIf3iXFMN9yTBU7ErbCTaSLSXMt'
        b'KbS9mG/i5y9XL1nGdDG4Bm4KDQkCZ714pIt7a0A3mdCJwVwN4bIQ4V6i4SlDuDs5imnGOm+wI3RcEGhFaygdgu05L4IO8lp4JFjjm4ptMGiKJ2PB01FjYTvYT+bJAnAW'
        b'Hg2NCALdiei1SNz4s4ak8fAUOA2VvhhVdSo8kAy3gAsUZTqRbQ72oZ6TuXwJKh3xu5fS0dBFISrhgC7m/NAJ9khTyaCNK0ErxGkOZWrOto4PIJ1+r4T48qnrLssvq053'
        b'ZToNu1MXhUaEeYN2ipTVCjZJGIo7CJodUDMwJE8qIpJCFjicZI+vTRniuobWoxb0JuyAFxBxTUDNWJpLHpkuhVdSU8FZcB62URSrko6Bm+BapraGYrAZv3R0Dmr6RESQ'
        b'yxcys6UBbA9PxSvbVnw/yrNigc4EoyJ4l7TcO6Seeor2hCOO+eH3bCczyyy8vQRcApeDUAusuRQdh83Gr4E28iwSnA9GnBivPAXf2LLhHRrN4suMcdJYxynUVvTXwSvf'
        b'uHMhjxkGoSG4gssC7dloZYingJIvZVagi8vg1VS0vqwIRSemBXQgODSWFPPzQiGFmLKqy4vyHV5nVTBTbjnYZZia7Ay3YXViDodGTdoG9xBEJnDergo2c2dmU1QAFTDN'
        b'jkBRLQPbfMCZNJcl6X7Tk+Dmaf4zGFV92JDuh9YgippqaWAPdsIzDGnsBE0RWlAmNBfP45vkFhbYYwMbdd6W3lhB7PlnufHzy37ymcswMPbh4A5s5hnDa2juUX628CTR'
        b'0QvOnJ066soc7TccygOc5qZa1swEm8l4WoCtC2BjFjbZRyuZJQ3ORaEtJ5sBeOqqAydSc+A2RBvbECXAVgp25k5mMJe3ORcw2GI6YDGa8pjGRY3fL0PfmCHoHYiIGuAB'
        b'E3BsLLZTQ/9SHImgEo3eXTwZGgPT4fYk/xSGuw7mUJ45XHgANIeAfVGkz4eK7agwRCFfCPPnTRNYMH2OS3CDBwwSYBNWTUf/4qcxjVobX/5ckSzKM5cLj0wJhcdtSLf8'
        b'loC21Cx/cAMcQcsBhq26DQ+CDcykv47Xo+z0MVlZGAyMVU87wMNchip3gMO1qblw2wRwCA/GCQpeAUemMxXftsscBnEbNtLeAk7SlDNo5MCrWWFkNOrBEU94gA+Ow9Wo'
        b'3bfQPzQLyVLrBy6AK3h6ByRnoHeT/UM4lH0ZVurnlDmC80zTdsxC3+EAG6wDW7CYn0j6vcgWlx8Md414m0XZw7124ACn3B7eJJqOrivgQdhISWYglp+SKWA7WQrmWPim'
        b'ws1go7+f9hOaWbEXwqOWZJjr4aZs0MyWAXTYdEZ9OcojpOUBbk72ZcChEV0FMmBtDhCte2g3glv4aJUkE+xWcTI8wIVtoej3TfQProkmxTqBbeWwkZUM0OdbRC3KQ/nJ'
        b'JNiLls71qf7+yeCsdwqeZ1bj4foYNtztDE4yS9OhaDwEpuCSP4pcQf8AOiyQZSaDL0HkCNboQRrNYJfBDdXM2CktUhR8Ph9uQ4sTmn3wHLwAVhP64kYaU6i1MX+1zC8b'
        b'LzehyGjBG2n1sJGNxXGVVGUu2Mig2e0eY4POb0kYwm1r6jR/1MZwuJdLiew5sBPt6OuJED1jrAfdw6aoTueMivcjpxasZwT5YJsnG5zhwG40AsvQ8tABzslWbnlCKfCt'
        b'ygeNyj1752arM81fjZBl73flDmxZK+KefnTiY//2+zZZ1+t6DyaolhVOMXBuufP9o5tHYu9e8HIpaf7oa3lBSVTrtz/9cvf9SZPeL7/7g21cBPUvD79VtsqSc8ePDJWv'
        b'Djec0Lh8wpbdG4O8xTNn8R0OfdZxas/p95RHz7g2nHvf7l7Plku3FBTb9oyPiZfQ49begiW+sw//fYa777Mhqvbrf32Y/EHw+77HPkn4xTr4434vn9Ntl70n2Jxv/uqN'
        b'Rx3J/yo9a3vq1lub/xS8dG9zwq3zIZsXsyVrXdJc2ySisLFxJkan+OvFG6t4RiX89bKNQevWK3jAL74lHixlSw67XDE58ikrflYC2LWmR2Jo25R/I8t2LJB/ZN8FzAOs'
        b'oze9bvqRseV5O8P5G6vODY4/G7L+qw1GEUKQ7v5eiHlFKMfMaBEPOG6ssjUaEtxf5Djp3SpK4tE6e+XEdWD//hmR5RNC5uzaYvHP2t0ZD/7eZRrb/OCq85KVy7895/H0'
        b's5bDN9bt/bZ5Uvrfsn7ZdzYmY+h+2Hd/L7k8b1lxtdmMDx6GvJVy1yW369aX5tfWVD+0KbZK+WXHK+fdbh48WBd412Nj+O3GhCMDFdMnXJjqNrfs+/CLx3q7HP8lurQ4'
        b'UHWtODt377G/WP0dVr9e/vlXO66d3Xsi0OnEwKuvdl1ax3X9yib7jfAPPjr03oXVrl+HrPeKip34sv31hMjDn31l/aY6Y4Hg6089sl/1ld/JXt9r+hE/WfTtOkPhWtHP'
        b'BzKt12+d7HptUmLdj3n2G7/8yDG+z7cP1r/yS6zp7uzlYW8PbpYsfyXgzqNDP9yIWrPnxJtXP312VnnMyvWm76onk7+BG7c4rP7xE+cMv47DZz8QWxHhZk5+xPM6VRqF'
        b'KngHHioFzRVPCd3uBLvifDP8K5djO9v9dPqcKkbp97ChHB3BlsO7iIvhUZwEGq1Hq8FtYqwaB2+bgUazKlM5WiO3mdXyjXiUIGoCOMKuBJdjGPytNfAK7DRBx/6k4TsL'
        b'C7gH7R432OAc3BxN9I4VYP1SrLOci3guPSufzZZEpdlUSpzuERuferAaW1sdY4HGFHCVPDaBt7E2mEZwC0/J0Z6aziqC7RlPyd50oBocR7MYbsIQZqxaOhZucWG6tn8l'
        b'XK/ThQbbWUJwzj8+k2i6eZeAJrSx18NODbIJOrQdhFuZq5EuuA7vluBCmkbRDeyOtoibTcYEtlXC7ud03eCZTI4h2oGZMWk11OmcabXSSgVELw2uz2e01xrhaaDU5WL0'
        b'0lagT4hV08DBNHJnLIYbwG6iCncnzJd4GNiSho3DNEJs3/FccBXxJN3MJVK7FNuJPSfpBicdSjmggQOPEEuv6JWRvgFgt88IM192JVq3N5PnznADWlaxPhzWhQOrVw2r'
        b'w9kG/teGVyNxO9iSoqIBvk5AhaJEKnWfo7EHtqacXDUYX6Eqx/Bex9huFGTcm91k/J7AtoV3xKTV5ABfLfBsF/SKx6vE47t9VOJElSCxif7ASvCenVuP+5QHgjfHvja2'
        b'JzvndQeVe67abkaPYEaflaPS5m0rL3wplLozFd8WoZKUie2hamGgNtYR2l7bKVMFxqh9Y9XCOF2u8E6vjsndcWrhZL00Yu5VpvaNvzddLUwa/WAhKuNeiFo4ZfSDYrXv'
        b'pG75yOLJg1K17+R7lmphwugHJWrf6Hs0euPRv1tHudo34V6BWpj8wlYFq4WJL6yDpRbG/9sPZGrfmHuuLyiKPHD5tX68qCip2ndiN2pu7K++MbrnvzqI2qL+4W9vbfM4'
        b'ihK6Kj3bbdoCOt16bcNVtuH9Yv8ORWdoN6+79vqYe4oHrJ7I1N7ILFVkVs/0XHXkDHXgzB7xrBZeS23rmD5bx5binSt7bX1Utj7tRRcWdixU20aSm8totdPkHkQO9s5H'
        b'oo9Et8/onNKxoLvobsX1CrV/Wp84sJPX4dTCOTjmdzP0O7oqw9u9VW6hGNNuioZAlaxTBm0Gj/AFp69K6Ns+pTOrI6XXL7o7tNcv8Z7bvVq1MKNP6HTEuNVYOVktDO0V'
        b'Lug2uO92r/hBnmrKfHXcAlXkgl5hUU9BUZ/QsY2tnNI+WeU+QS2aqBJOJKVqrqtsrtldtOuepg5Oe4AGLavvtx45KnnK2rYxvaIIlSiim6cWTVbh+cAUH61yj1KLJqiw'
        b'/fzoMtLVwSkPYkmLf/WRrqvxmkcp6uCpzLx60TtoLk57viNT1cFauh9VXKo6OGn4wYh3Uh5w1cEZPZlZauH051/LUAenPpipFub2Ce0HxdZimyeUtYvtU8raWojxacbu'
        b'S92VqgxXCcR79Y1VTBhROT5N/zH0FrxqPgfdcgzLY4+j4PSw5BzfNWdZ07Qdxsn7IxYtRHLeyhNTHSZhIxVntVcypRSDEkAuY7B4l8o10F7G0CPEuv+tMt9zOjYiarRY'
        b'14sR665eipX5vshkUfmmTkEcirmhIdzKeXg4FjRz0e6/gnJCPEoX2Kq5gfZcDJoxYGgZNZYaCzqmEq6/FpzxDEV84HwqhAoxB1tJ8XbGWBAjzDDOz08zcJRTRNWmfoYR'
        b'SoyR8vLz/Z7GRTGsvHzRCvp71oMkoyDJhPQV0Zq7yNXwxtTQMA6+L/J3owqXODCylZ2xsDE0DCNO7xsDTlDSaXAdY5OQiL0vm3vxRflpcntDpuQva7Aj6i8Kx1Tllx1b'
        b'6Ma0gVtvjhIf8I1Q4vtpAUzOf/D5lJBKmmKQmW/6/eQsJidcgBMjpSjR7wa/ism5xwIzSXVjDMzz075huzI5P0rAiTFTaPN8v7+EeDCJtwJJk5aOEeX7mQesYGScWEt+'
        b'cnY6YqlzsQiCWwuujaXBjfFwF9O/9S4zQ4OCOCsRP0+7U2DXKrCHVFsV4kYlUMpoLpXPOm9koflQdxeBbnz3HwLWY04KngR7CYclDkLspjEVD3ZT4Cr6lwW3khecZ8Jr'
        b'8AAPnWRXUOAa+jcRniRc3szxsBk201RGPeVP+cNLqaTSoYlYSFpF8WLyy3wjfCkiVg2F5xeizHsy4uAeuIeLmMiN6LQXUcZ8tg6JBb5BBhudKEfK0QGsJ++ssMAsd7Ke'
        b'wtMsBSulXEpkAW7V4Eq2P+JTk8E+VNpO2hLcmEJKqwA7l/kaUO6ITa2j6sAJ0EZ6txSeTwFnsIQihVqKYh3gGDMc3fDUDKwIBo5aUvWIZe+Au8kKQj7Hy8GoYmqwzCQm'
        b'36+6NIaBdXo9YTOaLbUTsOj93nrZ59CfpahFc1g6eP92LoaEFiy/ecVwraFhg03bjK124w52N30xefDSBc8FyVvfu/VD6k93K1KX3P/ary344rU/Pzww1Pps/E8nczx3'
        b'8xSx/4QFj6dcebvSt5W35b2pufO2clOtWbcAvWnglPHyhYjb33H63DerxT1dpz0z/2Lje9Rr8dxbgR5ZafM+FP190adB54r+BbbMuXdt/ozgfdx315RlHXj1oknQ24Xq'
        b'Z3U5TxveW1Z/o+vsu4u/tfE83DHWsVo2d9+f976uPN54yHxJalngn2pPdMXPPONqvqrgUuSPez1Ct//s/8mc99mPfzZxZH/47M8mXXMfzucOLTn9492312xpKw40cNq9'
        b'H3aEbnLZtHzGPMf9iR8XhEc8XhqzatvnDVMntiQ+u3MhNsJ247js1y58wfPekPWDQDHw8eNP7zy9teC7C284PnrV7u6SxduilctsLL+WfPy1yyuPT3746pfF8osXLr3+'
        b'r/q/cv6VPHj3QffKZXU2Nc6Kz0ouPV3Ia/nbO71OU4q33X5r95fOkxcazH3tq4tiIdHQApfL4R19W5EgkxepfcloBnThzjLGmijD3wefsrvQlDjFAnsL0VGcyItPJ9hh'
        b'xskhR59v6oTbGD5lxwJwhuEgiLFOIehmVTuBI4xrpzsWcZhxSMeyPbjNHV6C29JoyjKWDc6HRRPOygycdcJo9hhlcDPikFbC/WAryxUeynlKvMivQxzkUdA4CXb9CodZ'
        b'Ck/AK8Ritay8ADVkOuxI9sXi3PM0UE6Du0kro+Ah0Ew0WTVqrKHWrFBwqZgBvFidD08Ou1QHdwUZzE2RzSyOfcUywkzFgg54HLN/GmjFhaCVCOwtPdjgLDi8kIzTfBe4'
        b'RY9fAx3gAssCo1OSIpLAJrmO0QJn2fp2QuPAaqLyB/bCLYv1sY/g1SmELwL7YsmA2uWF6xVyR6xnSOQPb5EsNuNgA2KckvwCAgj2/q3AFNRQ2MGGzRQ8x+BE3oWt2JhI'
        b'Y9xUkKBv3jTRD24i/XFMht0kzx7EX29P5VIcFg0OO4HLDGjGUdjFx8qJWsW9cvTdKivApqcYXaYeNoKNz2kJwu6qaSO1BHmggQE8OcFjD/PfhPmmCP+NVr3jhA7AFnCx'
        b'krRmU8yv8qDXfckopi7HqJca1pHwjWy4FrGOaHnbRQjFKbVeD5C8bgELnJgEz/9bVlN6aBEDHGx+MDBGxzriOOEdDdkMNvYcW0pg21TdPF5JN0f32Ts+MhdgbeZec3eV'
        b'ubsyq511waDDoE9gR/7Zas7ZvQIxOrv1CgJVgsBOWi0I6QzpDO0RRKDHDCJju5tK4N8rCO907xVEd7v3C0RKwSn7Nvtel2CVS3BnsFowrlcwQSWY0B2rFkRrS/VRCXx6'
        b'BUEqQVCnhVoQ2hnXGY+BQH670n7E4XJ6hT4qoY9a4NsrCFYJgjtd1IKwzumd2T2C8eQ5PvI3T2OKaEcP/dqnt6OHwaNbnN3pfi3gYkBvSLIqJPmBtzoku1cwu2fm7P80'
        b'X0SnR69gUneI3giEq1zCu1H7o3oFMSpBzD3U03j82KFdjjrVK4hUCSK7LdWCicw7zm3Ona668YpTCyYzH2JEPZGdnr2CuO4p5JEt02XE4DGHdjXqs2t7cI/A/3eeab/z'
        b'YIRDsOUTykFsNRRJCex2hrd4q63cno53sPAYjKIsrIfJ421zL0QwTOxtc88+K9teKw+VlUe7ldrK75GGKeO2c3q9J6i8JwxznZJWs15hYHt8rzAcsZScuybXTZ6waXEi'
        b'/ZiiXRIxirX1FIz3YGG9z2SnSUv82+aiPv1abO321e2sU3JO8dv4atuAJo4GQVTp0iNw1yqw9gg8+ty9T6W3pXe6qtzH9bpPVLlP7J6pdk/UKOwXYDd0tvZNJs9r6/wb'
        b'2CxEVWcENMtdzHDcQ8G3wwzHPxHDMduWpi2xqs4fsgnxIo0ZMMxjTBEU8lhceAoOptJEyZLYGMoTcEo6DibR2M0cOeGL6b+hw9AvxJLpb9iGRDz2RZgrjGkh8ZoeiYPx'
        b'OIjCpRsOm4IN/8I6MMQgirF5IfYKRJeXaFYSpTesqDRgmpcZOz02PS9ndmZi9gBbIa0e4GCgyAETzYPsxJxshjO7qwVn+a+EZc/BrGBXeyTAtteK1SwCszLEM8P4KSh4'
        b'7EoJHPrNvfoEIY+5LEFYQ8JjHuXg3m8e2CcIQykO4Q1pOhSVUIyiMo6gqGgAUvwwQEqAPmSKD07xIynWjv3m3gysinVwQ+IzQzY/YMiYxc+knxma8CcP2XH4gUOmPH7w'
        b'dxQKhszZ/AR6kMLh4zGUk0uboK20xyGw38mt38O7392r31Pc7q6cg/50uLUXKRfofrh7tXOUUcN/XDyV1UrT4ZiTi9K9ZU6/K4459Lu4K3OUxv0ePu1hyrTHzuYOloOu'
        b'grGWfQLHVsUgG/16JLBvzR7kol8Ye9elLbRNgbIGDBrgFEPK2rnNCpcwaITjxpQ1yq0UtKQMmuC4Kepyq0IZ1rJwkI/jYyhrhx7H4EEzHDHXvWyB45aUtWtbPG7joBWO'
        b'C3TPrXHcBr3cWogbP2iL40JdfCyO21HWTm1sZULLskF7HHfQxR1x3EmX3xnHRZS1XWu8ktMSNeiC4666524o/tgdDTnuClYTRZm+88KJHl4OYxAF5NCUg3PL8vZklXN4'
        b'r/MElfMEtfMktX10v9C+Ja3dRuUQ1OswTuUwTu0QoRZGPuay7cc0pA4Zx9F8nycUDoeSWEF8h6cUChjDEOKO9AJci8G+dcdeLuJ95eY57DlgF1g7gqkf9nv+BKOFRFuM'
        b'wsxgyTGeBMcV8eizzdD/BgQnwWxkLJs9Ks4Zb+BEZTsRdVGjXLMwTjaXwasYljTIufN4WqwNQ4K1geNGKG5M4oYkboLipiRuROJ8FB9D4sYkbobi5iRuQuIWKG5J4qYk'
        b'boXiAhLnM73Idh5uabZ1AG4rj/TMmISs6Q7Uc/9l2xAsB+fnn4zGcvidcmz/3XL89X4n0OF0tiiXRWQ9jCKfCXZ8GWaUPXbUiDJ+58eQ0bYjWBEWui+XbT+eJoq7bOxC'
        b'M4yb7YBzaN+1zHaUW5UIjYrFLgOGBHctNSNR5oKObsuKCQjvcJqosEyiUIi8sZ/yWqlcIakowgu3TFohNjb2ycGYjozDQOz/srJAUVkmrWa8WGJPh2WVWAcTe1KUVlUz'
        b'zi8JzqRPgLF8MYW1uAeMJEW1MgXWxxww0fwkapWGjEM5lMwuKq4dYC+qQGnl0iJZTTlKM6xCrVpSKS8qNBxF2URctZbSV5gfdilKLNTwyHLQmHLRuPCIcjNf61/CMEfP'
        b'aWiFkROVq+dvItdohNzMMNaISNOeS9WXpkkeoylmnFwhq5YR8z8NJvLw2MoqFNWSikKpDnBTOxhRGkBOnV9P/KZGzRS77fSOY5RbGbfsYsaDXqxIo2HMwCOLaqqw6XKE'
        b'qEhWIqtWBIyqhXF0r6kHOx/9jVrQ4+E6KkSSsqpSif+LqhovKixFVRQSF6FaF5uaL/niPjFPRd7piGhQlcOO5n+zR+NG9wiRCOMdMmHKDFGZpEBaJvJGP/UdZIoDRrmq'
        b'JB9FQWoZ2RQyFt4hel0RaytCZBglSiOQR/itqYFpWseiTLfQXMmWFJZiV6GkTuKpFU0RDRxqTUGZtEgzJ0a+lYnCygrGySh6k6ChojjTU81MYsYkuVrralWiGZYCafUS'
        b'qbRCFCbyLmK8VYrJJIzUNnx46jDDxMREsiLNgIaOHtDh+aVx0amJieTSEpkCjQiay2jKk8/pJ6rRDGtNBXal+bve5s0YEbLrUixfTeKwqvLT3nU3YPzDwW3wADzDGEnC'
        b'Bo1zhkxiI6lxAIF43yxsJQka4NFhD3EbYkzNwXnIyI53OlhT3lSpjVFM/rwrk+VUzSSUWDDH6rcLJQ7iGetLuHEBU+yRKlN43BRuJMWWrsLy3O9LuJn5ppLCEE1zLwPl'
        b'zBcWPCwtIcajekad3ajdx5JNQBsLniPlOvpjQW9PjYEo32/xwpUU8YEI1qaDcy8sN9k3myluZgFT4Gq4wwjsAYcNSWmhLlhwHjmbys8vq8heyHQe3F0Bul5UGmzQCKfg'
        b'ttGtvAouGJiAY+E0KXabOxZRd/oamOeXreRNp2owD2IMLsKjLyrWm5G/BKaMKPMGODOnxAQ2FM+V2V5UcxWnURE/bnba8OakMXEupgaD36XfF775yGjePIeJL9WXZYz5'
        b'8rvtx4astyWuTS+PExr/klf/0MxbZvLyO+x67t+P3nzEynm51zbyfqXqq9mO31J/Na0KefvAuJrA0+37T22a6PvpWM83a5eGXSv+vGJy+afR220dXo28o3i4/mHln159'
        b'mT/D8uy9WRcvz3tj0eWrfPZlifDtLqXrsZMZ21aFb13XZXH24awzF7rqPxv3Da9uBevOz+K/f+EvNmaUDzbEoG+uEZdlTIG3dOKyUtBGPMPTYB1s0jqNuwWu6nmN44Fd'
        b'jO7BxUiiejCC/LiUM2zhhEfCC1WrGHWCtXCXUE/yRsRusAOcY0Rvh2A3I4W8BZtLfQPEoBNcZRDrMF7dkkAGcfZGNjgEGhX503SCwQhwjLxIW+ILhWUcuEMn4gL74BoG'
        b'KjfZTU96SUSXdouJ8FIhIpJDO0PYrJW1YTnbAnCUEbXZwi4iBxvLr2BOpGJLf3gZXlUQQWwydtCKT6iI8NPBegNwiAfu/I9ZNYLpYzG8z46E9LFlMGUf142l3DzbCtvF'
        b'xyrUruMwGk+/lU1T9b5VO1eprbzaXdRWvgS/Z6raLqlHkNTnHojxe1xIpl5bbxXj4S1WbeVPsiWr7VJ6BCmILWrLbhcem692CcWYPkyZK3euVFt5tluorXxI5ilqu6k9'
        b'gqkajyYHUlFOIybn0p1Lm6OVqFQPxlmc2i6uRxD3yMGZZPlDhbuITzm1Oaldgn8/q5tHE+cv5qLnnWD8GfO8b+KgBwcqHLyFAzUO3v59Uzat+4tR5mxEQvARliygM6di'
        b'Ior98j22nBxL09OJz7Hpf8jbGF6kjvJCqEsmk/4r/CHjPO0J7NdAiHRkNYxBlIu6oIekw5zvhg9ZL0D3+c/xhzQYMqZ5eie4X0OSwej1s3DLOrQtcxrVMnLO0bXrP2pS'
        b'yTC4zvAp77faMxe3Rweu48y0Z/jY9dxA/TcYTZw8dCb8rbYsQG15okXZmb1/NtMme6ZNeufI/1V70NHxt9ojwWPzLT08Nt66Q6ZkNFSU4n/VKKO84WPhb7WsaORXs8My'
        b'f70T5H/bFi1M1PAp87faUvJ8W9DX0p5P9doiZhGRIyN81JrQZRSy9WrH0EPEho64IjTSs3vlEUYRu2MwIu4IsTNCfu6YMFOtFazB/9AKFrGKNbmoMcaxRUXYJ06FdIn+'
        b'V0ezg3jHSUSMBRPB3LakqAgdw9HhXaLhq4jTG+xKwU9UIq+sqWIYbomosLK8QFZBnLgbI3Ly0cKD+fiJfPSRzFCcgKWhTAWVlYtw1ZjZJ5wEUy12Ga/jVrUFRYmyK8sx'
        b'T8XIArBLCA2ImKSgsobx4YO/kbRouC+Yj8EO6qW4S0Wy4mLEU6A1gOFmRjZSMx7Erw/qdonGgUWRlhkqlFQQXui3GNPgcD12TuRdWUV8DpXpGDv9cWCYnuemncg7tkAu'
        b'LSytqKkoUWi4VOLWgjRE910UCllJBfk0AaSPegVp3EmJZPqtliGGDzF3pJRhRi6YDHr4eC0/h0sOFvthaYuoSFpQjctFOQoRKybDkcJhFpNQgYzkV0irSd8jx6NvNgWb'
        b'1hJpzWjSkkkVUdpvisqWVWsyMONAUrT8qnd2ZVkZ5lErxSIfn3LMtKPql/r4aLl90qIRJTBJuiKmou5W+AcmofW14reKYqDONCxopYI0WAN/9sL8mFiZ3PrkGyBK13LL'
        b'hJwrCxZKC6tFZAQZGsqeFhkeFKyRZGFBFUO9AS+uZoTpctQoqUJtpaxQqiWYOGmZtKQY5xOL5gaHzH9RESGaYa6RMs2TVZCG4FmQkJCePns2bin2c4WbWiVZWk68Yknl'
        b'ePH1E5WjcdHy3noVhoysUDN8GOZg5HjilJGSEYa6Aocpi1TLHBXiUKMx7eN3UPGhQfOfnz2LpEuH5Tx6ZIZSEYVWKGRMpZXFpFRJ0UL0ZUh/cAbi2ktSh38zc5uRAI3I'
        b'pCAiKVlhabWsBDdFUVhaBm+hlaVMHKV7x1+Evkt2tbQGTXZtBkQBMpGmC2iGlSOKTMz1z5FUF0ixGK5I8yb6HIyPnLKa8kXSUrkmOXRUMilNUlO8rKZailYm7OtQNKNS'
        b'riCVat4JixLF1hSXSgtqMCmiDLE11ZV4fVykyTAuSpRcUSSrlaGPX1aGMuSWKyTVyxSjWq7JHf6iJvx+hyJe9JpMr9ry36428kXv/3a/xpOO64Zm1MiQIIf50lheNqre'
        b'576kfvOK5ah2b9xXbZmSgmU1JWLd59PPLorw0H3AEQ+Cx3voPlNFoET3SUZmC/fQDb8uGxpUbf16eSL1k7VVjx+RGdWrXbA0YAZoxmh+kfUZ7cFoLg5Pde9sZo3ULrA6'
        b'bIQoUTyKiJgY2jO8U1FUWoH+R59VhNecyPnPvxYy8rWQUa+FjHiNACwwS8aM2Bz/5ASRd252NfqL15dx2mxaAAYma2Iumck4QeSNiFLzidGw6rpRI0dbfiFaLeI1v/xE'
        b'entdYu50kfdMeLxUjogM1RWmq0oP20H3sjZZU+nwq4pFNXKFeMT292vbJ9k6dTuhdguLHSGqffGeQNAlokQZ+I9obkjQ/F/PFsJkCyHZdKMxDEuh2TI1cXzA1h9nglGB'
        b'suA/6MF8Y90sSZLK5RWBU+SSGhSUBQROkaHdTDcryGPdXMD5dPSPX9BNAP03EdUnlqJNBc1lHemTstCeU8QUM9w4tGtKpdV45cV/0QYRPmL/KaisixLhiyS0/hfjXRIl'
        b'oD4EjciEwTOYXJIyEY6MyFEoq8YEg8IR2w+DCIKfMD/Ii354X/cPDQ4PRyOtqwODb6AK8J8RX6BYglo3BRGtfiKB50AjgP+I5oYHjZ4Wmimh/4WGgUGiRHHoF7Nzzg2J'
        b'GPFcS1oky8irgBH9HYYT0eRkxkM3OTFoCNpC4mIz0HDoZkiBrBC9kByPikIU8jvOLzXi+C4HbBP9hRGLyi87El9CEVNScN4pSmtOTUypQTO8zQJ74CWN2WdNBVaMzXQ0'
        b'iclPM6lfwqgWG8+2TE1mDLz58DYNjvjDKwwQuxEGiGgJNRLlT+wbl0fVmKFEo4QJ2ImmqRCbfa9YTrAwuPAw2KS1u54EtmpANPjwKinI1gXDisTUmAVJ5iqoRVQNgQm/'
        b'HJDmi7KngLOr0uH2aVhNEpxNSWfQG7Grq8bpVF2YUQlcq8FpzCU4jd6vLpdYvTurVLKQqsGSKHBNApTDgm1U4GKwSYvUiEtKYsSX+mCNcBtoNRXDNVIiPZNVvDuFozBE'
        b'7OZfP9x1KPP1FBgjmLQkZGnNWyvj5sbHLrkRlOVnvf68tcJLVGTd073wLsgbXHVbFnouqPiTe0FVC4Yernh4R/KPjeerJv7deNZa2anZ/VX+ST+aZv30+fg+2YHPO12+'
        b'ygya4P/2zprTtR6l7sZuEYujeJvsrO9PcLBmf7nrT/E/SI9Ed/t+9uOzOnGk07Lztw5vfrr1dM+QNZywS7b/+7f9at6Ibt+73P5DXv3p14pzP67vPVr+9xOvJvz8r1Pg'
        b'xONPP0q/wit9KNs7/s39kLfila6Hy07cbHd47UzHh6rluyeVVXweOj6y5c83d75f0XHcI3rxGk/FvK21PvWZtXuPzfhrhl9f85ft0HOW8tgvdW9dcPaoCSr6rFBsyFgE'
        b'bgWNk/UtAp2msfxngpNEVB0VDbdoHZ2LwEUaXALHYQPRWvSM9PCFm6clg7McilcW78ByBbfBKSKSHwOOwp3P2QOCkyyO4Wyw5mkA/qBN8AxKIrLoF0qi3cKGZdHwqII4'
        b'Coe3Ue3NJj6InOrBqRdAQoLzcANRbuVZwjsKTAn+3sSF+Q6s2NrkAK6xQSc8DXYTTCmwFWwoS01LpmGziGJNp32mge1is/+liyg8k/Ts+0ZaqwyYaoWWwyZ+KbQGLs+J'
        b'Evn1Oge1L8Yo9vYt1Wortw/svfq8vFtMMeaZu7K2za+T3WsbprIN6/fy7cjutOos6g6/WHYv9F5cT/jU3vB0VXj6g0J1+HS1f3aPV04Lp2VGqyn2yM1rnch46N6Z0Gft'
        b'pHRXW3uSon1a8GPs7PuANsOnWB49WW0X0yOIwW5n5rWP77EZ18Tus7JpKep1ClA5BaitAggyZa+9r8reV23r18lV2457z8mnxzdD7TStRzhtkMW2Du4PGt/t3hOUeM/q'
        b'raBErMBJzIusVEL/QR7bwp8oOLqrBO7KbKL16f+WwF8lGNfJUQvGff/UgHLweELRqBQn3/Z4tVNQjzDox0E2SvjxqSEldEHPLPz77bza2Wo7vx6BH35m4f8DQR+EfJsE'
        b'DgXdnROcqJc4xgn27JfGGCbYsF+y4eLfTsYJ49gveRsmBLFfCuKi34yk3YyRtOtkVZj8/pCV0igqGOFseoTNEht9+YVY3o7vLjHaV5Y9TQdjaXswRisM/iN6hP+gXgAJ'
        b'THYWAgnM0eCOc3OpXJ4WGvN/jj0uH6JGeQRyfm6D82A2OPN4LmXo3oUdj5jGWJgz9igL4L75ihoM27GNQ6FZvQAeolcYgKs6XENwDl4Dt0zQqEnyZ1IzXWAzQUIIAruM'
        b'spnXaHhzGmij4JWSGlJR64IV9PdxapRHMuFs8RIN1NB1uF+isT0Cd+EpSgqvgAPEImXcIrHGVikTbKUKwRm4m5TzYKkBZepuyKNE+WXrsyMYC6I/l5lToqBgDlWVX2YZ'
        b'XsNYp2RMQonVn+BEPzaXy+SsjedTQsFhDpWZb5rp7cXkDBKYUsJMtDNn5pd9PbaSyWnCMqEEnI/REOWnHV86gclZOM+YEjigfdc833S9QsQk9tTxKNPIm1zcpB/qBcxu'
        b'7x4LdmRnZmZSFJ0ArthTYA3tTx642oMLoUFBaGrQ8PiSORRcUxhIBsMWnM/IRtvxvkwKG8OfRE8ygZKB/2oOgF36Jk7wdAGGhToPbjI2TnvhJfNQeCUsKIjDGDktUDDG'
        b'QxuXgtvYBRk9D7sg2wNuafLnwDWhHKJE3xZChaBtYC/zXQ/C7bXYaokqcfCn/MFVcwZmZ99kPjZQ0poneYEzFOhKdmS+YgPs9M3OFLGxnYm1D9jDA21iNml4HNgMukea'
        b'KYGTsImVku3JmBHhkc6tMKTMExpZ+HpeKDJhBjUv3IgyT/Jmo0TTLB8XBuYiBBwuzF7gh0eVgusoCbhSy1zwB1hT3kGTWIiK570SzmKoGLZMAeey0RCK0S66AnSCjSaw'
        b'rRrcJXgr0+FdfwU/FA0XC5FWAziK9rbpYLcsQJnCVmB4Og+7X07kpE4DMeaH37966zMJvdSoy/IfcYPg5YQL8o8uwVdCjTZf+9nyws95Je8OfvHt2v4NPT2eKx4+HPrm'
        b'1uSf8uo2cPY2dZYnr15h9Obec98tMTyyfBIn6ft3dsR+Z/36p4HXV75Jh7vEnOaeS7yqLPk4OWCt+j3LptTKLFbdjFVpu8vnPk34i8s/gh80Vce90RZ4+xz9Qesz+dQF'
        b'U1Z/tq7oSLLPuyLen1Lg/az5j79OvXJwYOKMuGvltw0dW/a/Ns3x/swH3254sDH2g+MP5Mtd5eV/LZLZ7X3HIvWuqHGzw7tbTmRyo2ZwK0w+gm4/zUo2nNSpKvg6/+uF'
        b'dy9EL57+NOHrz1aE18wa9+az/rbi+78Y5by/Y9LXnzi+z85N/XhHGW/dqY6nbQ0eYy6uO/bZg2p4DN69+M6XSxLsC+PHnj7zdfo8tW/r1fSWsANFQ4qFA6+9e92/5tnn'
        b'tzdLTi+zKpmZVjLjotcmafXVgp0f/a1wcE+F+Pa5Qcns634HQt5XXnH5pDoCOJz+cNWsgaxT/Y1iwdNAiri8PYlIVndAmQNu/dptOeiuYxyO3wiHx33JuQc9w4AHm0pZ'
        b'YOesKnJgKkVnrDbflPQ0muK4xFI0em87uMXoC5yekZvqp0OkhrtjWUuNQAcpVZSB6FfPux1oXUiDi2boiIahx8rRBDg8Cg6pA5E9sUcSJXKN0vikdnBgIQPAwOgcLLah'
        b'gTJzIbGdEcKNqBCtNRLcjdaBtazQJXAL0Z4ohHeS9BUjiHIFOr9t5NjDVrBTYy9TDE7q202BveDESnQk3CskmglGzvGjtSYsPeBGZzY4O5sBn4DrpoMG7VkzBrbis+YN'
        b'F0bF4wK8m4/Zl2TYpUOPGAPWseNY4CCDTt4M9oD92FaJzx8B4cCHh0knJ88HHbgILzstssSYFewEWuMSyR1emjZCdcISdsjT2WjdOQ1bGae9cP0KYvHDKGbAOy40OIw+'
        b'6VnyBccKMNqanvlR4RJWJTxdwoBfIOLZPVp1wzIWUdVtNjjvOpZkSswzGKF+UhioVUCBF2aDPf+Bs3ndWQPf/GkczZMTp56jeQy0T4AlnImjeezxyKRP5N4rClKJghhL'
        b'9l7R+KYkDDFehxHIMXC5o0hpfWBOu0vrgqYpjwIjMHb5mVVNiS3eyhkqO1+VwO+RwJmxWVHKTy1pW9IntO8TOiltWs36hKJeoT86+XWi419Yr3BSt6BXmHhPgGF7c07N'
        b'bpvdSauFIb3CSJUwsttCTYzlj5hhIxL8UrtELQzqtOy06hGOww/GYC/0BM88Sy0M7GR1snuEYVhvO6nXIVjlEDyyqO647vgeYQx5fiS9NV0t9OkVBqmE2AJJyFggCSNH'
        b'NzCm27ZXmHJvygvTS+8l9SbkqhJyexMWqBIW9OSVqBNK/0hOR6bfC9oWdKIeRKDxUKEhQb2MQePVZqWcdcxRhaHbHckIav7hDiQQNZUxSnk73SP0+bVEVEif0Bk1aHCc'
        b'fZDNE8re23YonBI67axtKVXbeg1F2FuLH5tRLlGDU2jK2fVIaWupsl7tFNpk8oGV8JG756mpbVN/dZxJyb/ycUi3ej3CVR7Y/kkYhUZBJcT2TxjaQkcLwyQxaGHkj5pn'
        b'5GE7ZKlrXrvvYysjj3BEV5470wcFlNCxyfR5fPDf1nYh+OCjp4LcDhH9p2w9y51EZ5q2HPyjljvFuCwWPcqli9bvH8Gl52pgYDka7XHs2oWnhYDl/W8hYOVcetTh+3nw'
        b'ZoOMGuzoZK4jvOGLfb1nJqENC21LoCMnCfsrB5cFxGV5EtxoUAXb4XZyoIk3ArfRargVrcpniEobu4wGax2NycktHl6Ed30NwP4Milh27+GS5NBkeNh3Gouip1Ngkyfc'
        b'z0uSlTQpOYqn6NnmS12MYz8L7EyoJfjluMj0sS5+/PakLWPZAf86+9IX03I4X5V4pfhjN35eadEtFp5H/iQE1i9tk60V7/4ze7/1S41zoxucswNajGDtTOWBvt2ri7mh'
        b'mzr3x8V77Qje7ZJkfq0fmDoVmJqeSDOdPceU+6e2rbGgxcdtd3qryI/LyzPi8SpE/BzxlnfTuBur50kCtos3evyZc18SsHmafw9//U+fcZ7MNLxpGTCUVHjZbbfR55/k'
        b'2wgbN7vs8NjtkWSTvcI7FKTfz28QLAhoGkwpySzqif3erD16W/KaWCdvdo7VK/fyX/d7s+mVB608KizcM/wiV2zGWDCvB2thsy88BLuSiBMNTgQNziejnYRgWJ6bmIz3'
        b'AHjDTWM1YggbWSvAnUiyj+eAy0LyeDM85YQtezNYDg6hjHnzSXBnDt7H/QKSiVt5E9iJDryNLHgLnKlnjKu3LKtC286VJRrBiRE4ZSBhgWMR8CbTtFuJLql+2JJ1cxo6'
        b'C5jExGSwYIs12kPJHt2QDc7iCgKnpTv6o7pXsnzgrUJmA96wKJI4B9F4BrEAm4lzEHgdbiKgVBFwrTtqeDLctmAiOh3xFrDcjKwYM2MMmHiEcWjvHyBmJaWjrfsIG2yA'
        b'R70YjckO2Jycik8PgQsiMrgUbyLLFjS7kRaXlsPOVEy2AQsJ1RoJWKANdmlMa90D2Ki929BoLQIH8WjFsYQT/JjD2sU69Khx0SI9v8HgYhC8xojFLnIcSIvAwfEEbrad'
        b'5QcOgOb/Gu1pWAyg8/A+wNfuywpJLeMuhKURBaW4UAKbfRE7I/ZF74xWuvdaeamsvNrjLkztmHohvSO9273Xb7LKb/K9uFdT7qc8qO5NyFEl5Lxn59LjGqG2i8T2tGiB'
        b'Nm01PTAG7exWtozn4V4rb5WVd7tNr1WQyiqo385F6d7Obp+ntotqiu/z9D21qG3RyfJW4xYOWqnxy8qcd4RBj7HD+0cC233JO5P3pD6ydzwS0RpxJLo1ut291z5QZR/Y'
        b'J7Q7YthqqBQcHDOikH5HF6XrKa82r1N+bX7t1Z05ateo7oS3HWPvTe9zcDqS1JqkzDmYMcSmnOJolWPsd7ieDx1j33GM/UGBlYFe5lomunNfdjdODDXS97woZ/+uqiMz'
        b'8IyfxRHWm8RZPLYZdObowcXUi2haiP0s/hH/JMRHhNhwwCQPW2lKsEqMQv4JLv+vOPgSB9/g4DEOnuJgCL/BIfIMBsmcoJsbavc1FvmdIRa80JDTgab0rTn/DXXQBzTx'
        b'TVUtLVcwQieyBdpobTIt/odCT71xxyO9evR/zPi/QWsCbN6kKKOJ3eZjDodv/p0p9hDPbotvWXqx8H72a1b3kvvHOih9r1tdz+42ei0e+4fPwvbC0TH0ENuL7/mYQgF2'
        b'Do9SOTg+nR426AzHBp2RxKBT480eG33ahzek6gw6x2GDzghi0Gll32/u2ScIRilWoQ3xupRonBJDkyTNa0H4tRB9y9DhlO8MUQcGKdaYdLpVcdHqMfk1YGu/P6FtbK9L'
        b'hMolottI5RLX65KkcklSu6SoHVIHnFzbxve6jVe5je/2VLnF9rpNVblNVbslq51SUH8dU+knFC1Mox+zcVlDvBqa7/+MwuETA5wySFKGKtjj+Y6DFAq+q6VRI1rdVHyn'
        b'IZaA7ztIoeAJ4picn+AoY6NILpMugJ1grSJ5PLg9LIbnUnw7FuKmWp3FdIZsf04iR5GIlfQ+H5JmvVGxNsb8sLVN5k+21l2JL4dGfNGWfGDBDxx4MC1p/1Ov4PuL8pQX'
        b'eoa++bo61mr8Nw+Hbr7+5KTc59pbe2b+M3fQJHAd50+RGy7leTeZ/eWTiHs/+vZNqg2rnPu2xdM1qqdrj9a/EWz4ZbHlSlbVldD3li37m+XYHV+UfO5QlCL8uPRKpcui'
        b'Q1Ma35/yj7Zd73R8m71vY1ib+I3SDJM5b22p3f25y8ZFkdwa83jjhw3CzeIH45694WSQ+NcPvzEFfX813rR2q6HxgTk3/cNtyuQbxktd2yF/3pdZD8SFf7Po9wwu/2L7'
        b't7JU+pvvDE99HLxol0n95cug3UHqVL9wnrpJ/fnGpdO7Ao32HwocapSlR/+4odv8rvSTmfVXd/7t4/7wnX85O0s60LlrzD85harzFTeq7+SbTfA2EzvU/Pjs9uffBP7y'
        b'6LV+cOrLn3+iv7FJ5c+/JGYzrPgx0DIJNqaB22A7jYG04fZqsIHw2nADOAdu6l+dgP1ZGksFH3iR2CCYLYFXyC3IiCsQeHexxjHWOlrsPnpCGv5m8H8x/f+DBcOd2SFj'
        b'yH/PrRyj1hBsLl9WKSnKy5OHoIWc7JpxiFB/RrtmGMW3HuQYGNn2m1k2hTQuaXFpXN6qUIYoJW3jDixrzzqw6qJ7p7zb5WJNd9bFussB9xMeWMIkdUjae0K7lpAWSeu4'
        b'A0bKFMR3ddoi1rFnYobKNqNnek5P7gzV9Jlq25nv2YiUls0VPebu2HvRLHrQmLIUNMXutG6IGwqzMHIfonDg7WXkP0ShYBAHQzn0RCO7phlPKfRnaCXtbmTXYvOUQn8G'
        b'M2jK2HyIJecY+Q5RuvAZCdG0NTYfJA8Hq40ooWe7ico2tMF0iGdoJByykbONHFB2FD4j4eBCA1LYdFKMLnzChLiwx+Th94OxQtoome63dD5u2uM/RS2aqrZM6jFNYnbd'
        b'LbEOCdbUS9ZWCd6aSxHHARYa6//sEuT/hl7wCpY/8n7tRZsNJg8S2BEaoRiGL5imzfE1i17wR6wb8KHiDG8CddMklseWnfF4SiswWsKTpbulW5MbjhqDGEHCqmXfJnAt'
        b'HNYK7/+NdeMf1PsTCs+tX0V9VG984dGKPZzYzvALW3y+fK+z4I2N/hOeOUTK/3n0aqlYvS7GNn3VjdYLE6wnOXO3NP6Sd/XLkjPLzv+4xO3isT3fxR+a/93RG3/+tOno'
        b'9wL36v7PQ3IL3oqp3jff6eTO7nGxsfDe0bWQcqvjbA2+Lwh9eDFmm4frjNLMgnWOzyIdvnqnt9qs4EJt6uN/8m5ucq22uo4YErLqnEcn4Q34YJ9SPg3f0W9NNaBMwCUW'
        b'bAc3YTMRkC2Ee11Tp/kvX4lduk+bNs0fg9reYoM2tIqd0ZQCutJAI9iBCmjAOgrpWFxqQI2xZDvBM+bk0rUa7DVITU73STegeMIIDssQticza+J2LjwFGwN5sBNep+hs'
        b'Ch6bCJqZi9qDEnDXN4ULO8soOpWCLbHgMMPMdE0cn5oM1i1OR6zB1nQMrmMiZsEmeKmY8BXL7OA+RTK8Abp0GYyTWaDTFZxgQIMOe+WkJvvZWSf7a0SGY+AWdoYY7mMq'
        b'PuJKocc1M4dx8VfBAwyjdRqxWrcxH5w+2y9Jw6WZWrHgFbgLnmRAnDpixoFGuAVsy/Kr0uQwBpdZ4Aq87cWgHm3yIIBGl0zdskHDksU18PJi08U1NGULd7DBVpktGVRw'
        b'pxZcTEUFXAetcKtvcjoG2DcB+1nwKLgOdzAX43vhTngMj3xgKtoNtuMbbxwrwCJge3cOWAfWThH7/Nvbwf+Xu8MLVwAfsmPEDP/3G3uGbjlwHQ7IloHP37+g9eCJHcW1'
        b'6uMLevlO6NR0sE7N9149pY9jvCltTVqPhcvxyLc5fu9y+Ojf+xznDzleH3L83+e4DfHmmHPRCqsLn5FwsE5EmQpWT9MTVrkMsMukFQMcrK4/wK2uqSqTDnDKZIrqAQ4W'
        b'xQ5wKqvQY7aiWj7ALVhaLVUMcAoqK8sG2LKK6gFuMdrq0B851qbDbmaraqoH2IWl8gF2pbxogIe4jmopipRLqgbYy2RVA1yJolAmG2CXSutQFlQ8W1FTPsBTVMqrpUUD'
        b'xjLFsJ37AK+qpqBMVjhgwCACKAZMFKWy4uo8qVxeKR/gV0nkCmmeTFGJtbEH+DUVhaUSWYW0KE9aVzhglJenkKKu5OUN8BhtZ93+oMA0nv/b/4lEoz4J9rKmwPzOL7/8'
        b'gjbyIQuaXszGa/PI8AkJ/8hyjbe0+6a8WAfqvoNJrBf7B8NirOJfWBowYJ6Xp/mtOU/8YKeJi6okhYskJVINboKkSFqUITYkDNiAQV6epKwMbYik7ZhPGzBGIyqvViyR'
        b'VZcO8MoqCyVligHT6VjbulyaiEdTjqWEhBoYumCOMRPLK4tqyqTRcuyvEN/eK9JQMMimafox6hpncAxlwl9t8B2nzJwWDC5woYwseg3tVYb2LSm9hl4qQ68ev+j7ntBb'
        b'7ZfSZ2jeb2zTYxuqNg7r4YT1U+ZNwr9QdqS2/wfEdG7X'
    ))))
