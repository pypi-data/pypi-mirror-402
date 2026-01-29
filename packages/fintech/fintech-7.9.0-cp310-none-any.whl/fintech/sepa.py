
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
SEPA module of the Python Fintech package.

This module defines functions and classes to work with SEPA.
"""

__all__ = ['Account', 'Amount', 'SEPATransaction', 'SEPACreditTransfer', 'SEPADirectDebit', 'CAMTDocument', 'Mandate', 'MandateManager']

class Account:
    """Account class"""

    def __init__(self, iban, name, country=None, city=None, postcode=None, street=None):
        """
        Initializes the account instance.

        :param iban: Either the IBAN or a 2-tuple in the form of
            either (IBAN, BIC) or (ACCOUNT_NUMBER, BANK_CODE).
            The latter will be converted to the corresponding
            IBAN automatically (deprecated). An IBAN is checked for
            validity.
        :param name: The name of the account holder.
        :param country: The country (ISO-3166 ALPHA 2) of the account
            holder (optional).
        :param city: The city of the account holder (optional).
        :param postcode: The postcode of the account holder (optional).
        :param street: The street of the account holder (optional).
        """
        ...

    @property
    def iban(self):
        """The IBAN of this account (read-only)."""
        ...

    @property
    def bic(self):
        """The BIC of this account (read-only)."""
        ...

    @property
    def name(self):
        """The name of the account holder (read-only)."""
        ...

    @property
    def country(self):
        """The country of the account holder (read-only)."""
        ...

    @property
    def city(self):
        """The city of the account holder (read-only)."""
        ...

    @property
    def postcode(self):
        """The postcode of the account holder (read-only)."""
        ...

    @property
    def street(self):
        """The street of the account holder (read-only)."""
        ...

    @property
    def address(self):
        """Tuple of unstructured address lines (read-only)."""
        ...

    def is_sepa(self):
        """
        Checks if this account seems to be valid
        within the Single Euro Payments Area.
        (added in v6.2.0)
        """
        ...

    def set_ultimate_name(self, name):
        """
        Sets the ultimate name used for SEPA transactions and by
        the :class:`MandateManager`.
        """
        ...

    @property
    def ultimate_name(self):
        """The ultimate name used for SEPA transactions."""
        ...

    def set_originator_id(self, cid=None, cuc=None):
        """
        Sets the originator id of the account holder (new in v6.1.1).

        :param cid: The SEPA creditor id. Required for direct debits
            and in some countries also for credit transfers.
        :param cuc: The CBI unique code (only required in Italy).
        """
        ...

    @property
    def cid(self):
        """The creditor id of the account holder (readonly)."""
        ...

    @property
    def cuc(self):
        """The CBI unique code (CUC) of the account holder (readonly)."""
        ...

    def set_mandate(self, mref, signed, recurrent=False):
        """
        Sets the SEPA mandate for this account.

        :param mref: The mandate reference.
        :param signed: The date of signature. Can be a date object
            or an ISO8601 formatted string.
        :param recurrent: Flag whether this is a recurrent mandate
            or not.
        :returns: A :class:`Mandate` object.
        """
        ...

    @property
    def mandate(self):
        """The assigned mandate (read-only)."""
        ...


class Amount:
    """
    The Amount class with an integrated currency converter.

    Arithmetic operations can be performed directly on this object.
    """

    default_currency = 'EUR'

    exchange_rates = {}

    implicit_conversion = False

    def __init__(self, value, currency=None):
        """
        Initializes the Amount instance.

        :param value: The amount value.
        :param currency: An ISO-4217 currency code. If not specified,
            it is set to the value of the class attribute
            :attr:`default_currency` which is initially set to EUR.
        """
        ...

    @property
    def value(self):
        """The amount value of type ``decimal.Decimal``."""
        ...

    @property
    def currency(self):
        """The ISO-4217 currency code."""
        ...

    @property
    def decimals(self):
        """The number of decimal places (at least 2). Use the built-in ``round`` to adjust the decimal places."""
        ...

    @classmethod
    def update_exchange_rates(cls):
        """
        Updates the exchange rates based on the data provided by the
        European Central Bank and stores it in the class attribute
        :attr:`exchange_rates`. Usually it is not required to call
        this method directly, since it is called automatically by the
        method :func:`convert`.

        :returns: A boolean flag whether updated exchange rates
            were available or not.
        """
        ...

    def convert(self, currency):
        """
        Converts the amount to another currency on the bases of the
        current exchange rates provided by the European Central Bank.
        The exchange rates are automatically updated once a day and
        cached in memory for further usage.

        :param currency: The ISO-4217 code of the target currency.
        :returns: An :class:`Amount` object in the requested currency.
        """
        ...


class SEPATransaction:
    """
    The SEPATransaction class

    This class cannot be instantiated directly. An instance is returned
    by the method :func:`add_transaction` of a SEPA document instance
    or by the iterator of a :class:`CAMTDocument` instance.

    If it is a batch of other transactions, the instance can be treated
    as an iterable over all underlying transactions.
    """

    @property
    def bank_reference(self):
        """The bank reference, used to uniquely identify a transaction."""
        ...

    @property
    def iban(self):
        """The IBAN of the remote account (IBAN)."""
        ...

    @property
    def bic(self):
        """The BIC of the remote account (BIC)."""
        ...

    @property
    def name(self):
        """The name of the remote account holder."""
        ...

    @property
    def country(self):
        """The country of the remote account holder."""
        ...

    @property
    def address(self):
        """A tuple subclass which holds the address of the remote account holder. The tuple values represent the unstructured address. Structured fields can be accessed by the attributes *country*, *city*, *postcode* and *street*."""
        ...

    @property
    def ultimate_name(self):
        """The ultimate name of the remote account (ABWA/ABWE)."""
        ...

    @property
    def originator_id(self):
        """The creditor or debtor id of the remote account (CRED/DEBT)."""
        ...

    @property
    def amount(self):
        """The transaction amount of type :class:`Amount`. Debits are always signed negative."""
        ...

    @property
    def purpose(self):
        """A tuple of the transaction purpose (SVWZ)."""
        ...

    @property
    def date(self):
        """The booking date or appointed due date."""
        ...

    @property
    def valuta(self):
        """The value date."""
        ...

    @property
    def msgid(self):
        """The message id of the physical PAIN file."""
        ...

    @property
    def kref(self):
        """The id of the logical PAIN file (KREF)."""
        ...

    @property
    def eref(self):
        """The end-to-end reference (EREF)."""
        ...

    @property
    def mref(self):
        """The mandate reference (MREF)."""
        ...

    @property
    def purpose_code(self):
        """The external purpose code (PURP)."""
        ...

    @property
    def cheque(self):
        """The cheque number."""
        ...

    @property
    def info(self):
        """The transaction information (BOOKINGTEXT)."""
        ...

    @property
    def classification(self):
        """The transaction classification. For German banks it is a tuple in the form of (SWIFTCODE, GVC, PRIMANOTA, TEXTKEY), for French banks a tuple in the form of (DOMAINCODE, FAMILYCODE, SUBFAMILYCODE, TRANSACTIONCODE), otherwise a plain string."""
        ...

    @property
    def return_info(self):
        """A tuple of return code and reason."""
        ...

    @property
    def status(self):
        """The transaction status. A value of INFO, PDNG or BOOK."""
        ...

    @property
    def reversal(self):
        """The reversal indicator."""
        ...

    @property
    def batch(self):
        """Flag which indicates a batch transaction."""
        ...

    @property
    def camt_reference(self):
        """The reference to a CAMT file."""
        ...

    def get_account(self):
        """Returns an :class:`Account` instance of the remote account."""
        ...


class SEPACreditTransfer:
    """SEPACreditTransfer class"""

    def __init__(self, account, type='NORM', cutoff=14, batch=True, cat_purpose=None, scheme=None, currency=None):
        """
        Initializes the SEPA credit transfer instance.

        Supported pain schemes:

        - pain.001.003.03 (DE)
        - pain.001.001.03
        - pain.001.001.09 (*since v7.6*)
        - pain.001.001.03.ch.02 (CH)
        - pain.001.001.09.ch.03 (CH, *since v7.6*)
        - CBIPaymentRequest.00.04.00 (IT)
        - CBIPaymentRequest.00.04.01 (IT)
        - CBICrossBorderPaymentRequestLogMsg.00.01.01 (IT, *since v7.6*)

        :param account: The local debtor account.
        :param type: The credit transfer priority type (*NORM*, *HIGH*,
            *URGP*, *INST* or *SDVA*). (new in v6.2.0: *INST*,
            new in v7.0.0: *URGP*, new in v7.6.0: *SDVA*)
        :param cutoff: The cut-off time of the debtor's bank.
        :param batch: Flag whether SEPA batch mode is enabled or not.
        :param cat_purpose: The SEPA category purpose code. This code
            is used for special treatments by the local bank and is
            not forwarded to the remote bank. See module attribute
            CATEGORY_PURPOSE_CODES for possible values.
        :param scheme: The PAIN scheme of the document. If not
            specified, the scheme is set to *pain.001.001.03* for
            SEPA payments and *pain.001.001.09* for payments in
            currencies other than EUR.
            In Switzerland it is set to *pain.001.001.03.ch.02*,
            in Italy to *CBIPaymentRequest.00.04.00*.
        :param currency: The ISO-4217 code of the currency to use.
            It must match with the currency of the local account.
            If not specified, it defaults to the currency of the
            country the local IBAN belongs to.
        """
        ...

    @property
    def type(self):
        """The credit transfer priority type (read-only)."""
        ...

    def add_transaction(self, account, amount, purpose, eref=None, ext_purpose=None, due_date=None, charges='SHAR'):
        """
        Adds a transaction to the SEPACreditTransfer document.
        If :attr:`scl_check` is set to ``True``, it is verified that
        the transaction can be routed to the target bank.

        :param account: The remote creditor account.
        :param amount: The transaction amount as floating point number
            or an instance of :class:`Amount`.
        :param purpose: The transaction purpose text. If the value matches
            a valid ISO creditor reference number (starting with "RF..."),
            it is added as a structured reference. For other structured
            references a tuple can be passed in the form of
            (REFERENCE_NUMBER, PURPOSE_TEXT).
        :param eref: The end-to-end reference (optional).
        :param ext_purpose: The SEPA external purpose code (optional).
            This code is forwarded to the remote bank and the account
            holder. See module attribute EXTERNAL_PURPOSE_CODES for
            possible values.
        :param due_date: The due date. If it is an integer or ``None``,
            the next possible date is calculated starting from today
            plus the given number of days (considering holidays and
            the given cut-off time). If it is a date object or an
            ISO8601 formatted string, this date is used without
            further validation.
        :param charges: Specifies which party will bear the charges
            associated with the processing of an international
            transaction. Not applicable for SEPA transactions.
            Can be a value of SHAR (SHA), DEBT (OUR) or CRED (BEN).
            *(new in v7.6)*

        :returns: A :class:`SEPATransaction` instance.
        """
        ...

    def render(self):
        """Renders the SEPACreditTransfer document and returns it as XML."""
        ...

    @property
    def scheme(self):
        """The document scheme version (read-only)."""
        ...

    @property
    def message_id(self):
        """The message id of this document (read-only)."""
        ...

    @property
    def account(self):
        """The local account (read-only)."""
        ...

    @property
    def cutoff(self):
        """The cut-off time of the local bank (read-only)."""
        ...

    @property
    def batch(self):
        """Flag if batch mode is enabled (read-only)."""
        ...

    @property
    def cat_purpose(self):
        """The category purpose (read-only)."""
        ...

    @property
    def currency(self):
        """The ISO-4217 currency code (read-only)."""
        ...

    @property
    def scl_check(self):
        """
        Flag whether remote accounts should be verified against
        the SEPA Clearing Directory or not. The initial value is
        set to ``True`` if the local account is originated in
        Germany, otherwise it is set to ``False`` due to reasons
        of backward compatibility. Up to v7.8.x the *kontocheck*
        package was required to be installed.
        """
        ...

    def new_batch(self, kref=None):
        """
        After calling this method additional transactions are added to a new
        batch (``PmtInf`` block). This could be useful if you want to divide
        transactions into different batches with unique KREF ids.

        :param kref: It is possible to set a custom KREF (``PmtInfId``) for
            the new batch (new in v7.2). Be aware that KREF ids should be
            unique over time and that all transactions must be grouped by
            particular SEPA specifications (date, sequence type, etc.) into
            separate batches. This is done automatically if you do not pass
            a custom KREF.
        """
        ...

    def send(self, ebics_client, use_ful=None):
        """
        Sends the SEPA document using the passed EBICS instance.

        :param ebics_client: The :class:`fintech.ebics.EbicsClient` instance.
        :param use_ful: Flag, whether to use the order type
            :func:`fintech.ebics.EbicsClient.FUL` for uploading the document
            or otherwise one of the suitable order types
            :func:`fintech.ebics.EbicsClient.CCT`,
            :func:`fintech.ebics.EbicsClient.CCU`,
            :func:`fintech.ebics.EbicsClient.CIP`,
            :func:`fintech.ebics.EbicsClient.AXZ`,
            :func:`fintech.ebics.EbicsClient.CDD`,
            :func:`fintech.ebics.EbicsClient.CDB`,
            :func:`fintech.ebics.EbicsClient.XE2`,
            :func:`fintech.ebics.EbicsClient.XE3` or
            :func:`fintech.ebics.EbicsClient.XE4`.
            If not specified, *use_ful* is set to ``True`` if the local
            account is originated in France, otherwise it is set to ``False``.
            With EBICS v3.0 the document is always uploaded via
            :func:`fintech.ebics.EbicsClient.BTU`.
        :returns: The EBICS order id.
        """
        ...


class SEPADirectDebit:
    """SEPADirectDebit class"""

    def __init__(self, account, type='CORE', cutoff=36, batch=True, cat_purpose=None, scheme=None, currency=None):
        """
        Initializes the SEPA direct debit instance.

        Supported pain schemes:

        - pain.008.003.02 (DE)
        - pain.008.001.02
        - pain.008.001.08 (*since v7.6*)
        - pain.008.001.02.ch.01 (CH)
        - CBISDDReqLogMsg.00.01.00 (IT)
        - CBISDDReqLogMsg.00.01.01 (IT)

        :param account: The local creditor account with an appointed
            creditor id.
        :param type: The direct debit type (*CORE* or *B2B*).
        :param cutoff: The cut-off time of the creditor's bank.
        :param batch: Flag if SEPA batch mode is enabled or not.
        :param cat_purpose: The SEPA category purpose code. This code
            is used for special treatments by the local bank and is
            not forwarded to the remote bank. See module attribute
            CATEGORY_PURPOSE_CODES for possible values.
        :param scheme: The PAIN scheme of the document. If not
            specified, the scheme is set to *pain.008.001.02*.
            In Switzerland it is set to *pain.008.001.02.ch.01*,
            in Italy to *CBISDDReqLogMsg.00.01.00*.
        :param currency: The ISO-4217 code of the currency to use.
            It must match with the currency of the local account.
            If not specified, it defaults to the currency of the
            country the local IBAN belongs to.
        """
        ...

    @property
    def type(self):
        """The direct debit type (read-only)."""
        ...

    def add_transaction(self, account, amount, purpose, eref=None, ext_purpose=None, due_date=None):
        """
        Adds a transaction to the SEPADirectDebit document.
        If :attr:`scl_check` is set to ``True``, it is verified that
        the transaction can be routed to the target bank.

        :param account: The remote debtor account with a valid mandate.
        :param amount: The transaction amount as floating point number
            or an instance of :class:`Amount`.
        :param purpose: The transaction purpose text. If the value matches
            a valid ISO creditor reference number (starting with "RF..."),
            it is added as a structured reference. For other structured
            references a tuple can be passed in the form of
            (REFERENCE_NUMBER, PURPOSE_TEXT).
        :param eref: The end-to-end reference (optional).
        :param ext_purpose: The SEPA external purpose code (optional).
            This code is forwarded to the remote bank and the account
            holder. See module attribute EXTERNAL_PURPOSE_CODES for
            possible values.
        :param due_date: The due date. If it is an integer or ``None``,
            the next possible date is calculated starting from today
            plus the given number of days (considering holidays, the
            lead time and the given cut-off time). If it is a date object
            or an ISO8601 formatted string, this date is used without
            further validation.

        :returns: A :class:`SEPATransaction` instance.
        """
        ...

    def render(self):
        """Renders the SEPADirectDebit document and returns it as XML."""
        ...

    @property
    def scheme(self):
        """The document scheme version (read-only)."""
        ...

    @property
    def message_id(self):
        """The message id of this document (read-only)."""
        ...

    @property
    def account(self):
        """The local account (read-only)."""
        ...

    @property
    def cutoff(self):
        """The cut-off time of the local bank (read-only)."""
        ...

    @property
    def batch(self):
        """Flag if batch mode is enabled (read-only)."""
        ...

    @property
    def cat_purpose(self):
        """The category purpose (read-only)."""
        ...

    @property
    def currency(self):
        """The ISO-4217 currency code (read-only)."""
        ...

    @property
    def scl_check(self):
        """
        Flag whether remote accounts should be verified against
        the SEPA Clearing Directory or not. The initial value is
        set to ``True`` if the local account is originated in
        Germany, otherwise it is set to ``False`` due to reasons
        of backward compatibility. Up to v7.8.x the *kontocheck*
        package was required to be installed.
        """
        ...

    def new_batch(self, kref=None):
        """
        After calling this method additional transactions are added to a new
        batch (``PmtInf`` block). This could be useful if you want to divide
        transactions into different batches with unique KREF ids.

        :param kref: It is possible to set a custom KREF (``PmtInfId``) for
            the new batch (new in v7.2). Be aware that KREF ids should be
            unique over time and that all transactions must be grouped by
            particular SEPA specifications (date, sequence type, etc.) into
            separate batches. This is done automatically if you do not pass
            a custom KREF.
        """
        ...

    def send(self, ebics_client, use_ful=None):
        """
        Sends the SEPA document using the passed EBICS instance.

        :param ebics_client: The :class:`fintech.ebics.EbicsClient` instance.
        :param use_ful: Flag, whether to use the order type
            :func:`fintech.ebics.EbicsClient.FUL` for uploading the document
            or otherwise one of the suitable order types
            :func:`fintech.ebics.EbicsClient.CCT`,
            :func:`fintech.ebics.EbicsClient.CCU`,
            :func:`fintech.ebics.EbicsClient.CIP`,
            :func:`fintech.ebics.EbicsClient.AXZ`,
            :func:`fintech.ebics.EbicsClient.CDD`,
            :func:`fintech.ebics.EbicsClient.CDB`,
            :func:`fintech.ebics.EbicsClient.XE2`,
            :func:`fintech.ebics.EbicsClient.XE3` or
            :func:`fintech.ebics.EbicsClient.XE4`.
            If not specified, *use_ful* is set to ``True`` if the local
            account is originated in France, otherwise it is set to ``False``.
            With EBICS v3.0 the document is always uploaded via
            :func:`fintech.ebics.EbicsClient.BTU`.
        :returns: The EBICS order id.
        """
        ...


class CAMTDocument:
    """
    The CAMTDocument class is used to parse CAMT52, CAMT53 or CAMT54
    documents. An instance can be treated as an iterable over its
    transactions, each represented as an instance of type
    :class:`SEPATransaction`.

    Note: If orders were submitted in batch mode, there are three
    methods to resolve the underlying transactions. Either (A) directly
    within the CAMT52/CAMT53 document, (B) within a separate CAMT54
    document or (C) by a reference to the originally transfered PAIN
    message. The applied method depends on the bank (method B is most
    commonly used).
    """

    def __init__(self, xml, camt54=None, force_batch=False):
        """
        Initializes the CAMTDocument instance.

        :param xml: The XML string of a CAMT document to be parsed
            (either CAMT52, CAMT53 or CAMT54).
        :param camt54: In case `xml` is a CAMT52 or CAMT53 document, an
            additional CAMT54 document or a sequence of such documents
            can be passed which are automatically merged with the
            corresponding batch transactions.
        :param force_batch: Forces each transaction into a batch
            transaction with subtransactions for each TxDtls node.
            Must be used for documents with resolved batch transactions
            if the bank creates batches also for single executed
            transactions. (*new since v7.9.0*)
        """
        ...

    @property
    def type(self):
        """The CAMT type, eg. *camt.053.001.02* (read-only)."""
        ...

    @property
    def message_id(self):
        """The message id (read-only)."""
        ...

    @property
    def created(self):
        """The date of creation (read-only)."""
        ...

    @property
    def reference_id(self):
        """A unique reference number (read-only)."""
        ...

    @property
    def sequence_id(self):
        """The statement sequence number (read-only)."""
        ...

    @property
    def info(self):
        """Some info text about the document (read-only)."""
        ...

    @property
    def iban(self):
        """The local IBAN (read-only)."""
        ...

    @property
    def bic(self):
        """The local BIC (read-only)."""
        ...

    @property
    def name(self):
        """The name of the account holder (read-only)."""
        ...

    @property
    def currency(self):
        """The currency of the account (read-only)."""
        ...

    @property
    def date_from(self):
        """The start date (read-only)."""
        ...

    @property
    def date_to(self):
        """The end date (read-only)."""
        ...

    @property
    def balance_open(self):
        """The opening balance of type :class:`Amount` (read-only)."""
        ...

    @property
    def balance_close(self):
        """The closing balance of type :class:`Amount` (read-only)."""
        ...

    def iter_resolved(self):
        """
        Iterates over all transactions while resolving batches.
        Raises a RuntimeError when batches cannot be resolved
        or on other inconsistencies (number of transactions,
        amount mismatch).
        """
        ...


class Mandate:
    """SEPA mandate class."""

    def __init__(self, path):
        """
        Initializes the SEPA mandate instance.

        :param path: The path to a SEPA PDF file.
        """
        ...

    @property
    def mref(self):
        """The mandate reference (read-only)."""
        ...

    @property
    def signed(self):
        """The date of signature (read-only)."""
        ...

    @property
    def b2b(self):
        """Flag if it is a B2B mandate (read-only)."""
        ...

    @property
    def cid(self):
        """The creditor id (read-only)."""
        ...

    @property
    def created(self):
        """The creation date (read-only)."""
        ...

    @property
    def modified(self):
        """The last modification date (read-only)."""
        ...

    @property
    def executed(self):
        """The last execution date (read-only)."""
        ...

    @property
    def closed(self):
        """Flag if the mandate is closed (read-only)."""
        ...

    @property
    def debtor(self):
        """The debtor account (read-only)."""
        ...

    @property
    def creditor(self):
        """The creditor account (read-only)."""
        ...

    @property
    def pdf_path(self):
        """The path to the PDF file (read-only)."""
        ...

    @property
    def recurrent(self):
        """Flag whether this mandate is recurrent or not."""
        ...

    def is_valid(self):
        """Checks if this SEPA mandate is still valid."""
        ...


class MandateManager:
    """
    A MandateManager manages all SEPA mandates that are required
    for SEPA direct debit transactions.

    It stores all mandates as PDF files in a given directory.

    .. warning::

        The MandateManager is still BETA. Don't use for production!
    """

    def __init__(self, path, account):
        """
        Initializes the mandate manager instance.

        :param path: The path to a directory where all mandates
            are stored. If it does not exist it will be created.
        :param account: The creditor account with the full address
            and an appointed creditor id.
        """
        ...

    @property
    def path(self):
        """The path where all mandates are stored (read-only)."""
        ...

    @property
    def account(self):
        """The creditor account (read-only)."""
        ...

    @property
    def scl_check(self):
        """
        Flag whether remote accounts should be verified against
        the SEPA Clearing Directory or not. The initial value is
        set to ``True`` if the local account is originated in
        Germany, otherwise it is set to ``False`` due to reasons
        of backward compatibility. Up to v7.8.x the *kontocheck*
        package was required to be installed.
        """
        ...

    def get_mandate(self, mref):
        """
        Get a stored SEPA mandate.

        :param mref: The mandate reference.
        :returns: A :class:`Mandate` object.
        """
        ...

    def get_account(self, mref):
        """
        Get the debtor account of a SEPA mandate.

        :param mref: The mandate reference.
        :returns: A :class:`Account` object.
        """
        ...

    def get_pdf(self, mref, save_as=None):
        """
        Get the PDF document of a SEPA mandate.

        All SEPA meta data is removed from the PDF.

        :param mref: The mandate reference.
        :param save_as: If given, it must be the destination path
            where the PDF file is saved.
        :returns: The raw PDF data.
        """
        ...

    def add_mandate(self, account, mref=None, signature=None, recurrent=True, b2b=False, lang=None):
        """
        Adds a new SEPA mandate and creates the corresponding PDF file.
        If :attr:`scl_check` is set to ``True``, it is verified that
        a direct debit transaction can be routed to the target bank.

        :param account: The debtor account with the full address.
        :param mref: The mandate reference. If not specified, a new
            reference number will be created.
        :param signature: The signature which must be the full name
            of the account holder. If given, the mandate is marked
            as signed. Otherwise the method :func:`sign_mandate`
            must be called before the mandate can be used for a
            direct debit.
        :param recurrent: Flag if it is a recurrent mandate or not.
        :param b2b: Flag if it is a B2B mandate or not.
        :param lang: ISO 639-1 language code of the mandate to create.
            Defaults to the language of the account holder's country.
        :returns: The created or passed mandate reference.
        """
        ...

    def sign_mandate(self, document, mref=None, signed=None):
        """
        Updates a SEPA mandate with a signed document.

        :param document: The path to the signed document, which can
            be an image or PDF file.
        :param mref: The mandate reference. If not specified and
            *document* points to an image, the image is scanned for
            a Code39 barcode which represents the mandate reference.
        :param signed: The date of signature. If not specified, the
            current date is used.
        :returns: The mandate reference.
        """
        ...

    def update_mandate(self, mref, executed=None, closed=None):
        """
        Updates the SEPA meta data of a mandate.

        :param mref: The mandate reference.
        :param executed: The last execution date. Can be a date
            object or an ISO8601 formatted string.
        :param closed: Flag if this mandate is closed.
        """
        ...

    def archive_mandates(self, zipfile):
        """
        Archives all closed SEPA mandates.

        Currently not implemented!

        :param zipfile: The path to a zip file.
        """
        ...



from typing import TYPE_CHECKING
if not TYPE_CHECKING:
    import marshal, zlib, base64
    exec(marshal.loads(zlib.decompress(base64.b64decode(
        b'eJy0vQdAG8m5OD67qwaIYkxzlzsCSWDc6xkbYzqY4oJ9JwlWGNmAsIorbuciXHDv3T43zr2fy9mXmeQuPfcu5SV6eS+53O8ll9ylXfKSi5Oc/9/MroQAge1L/gitdnZn'
        b'55vyzdfmm28/Qh3+BPhOha9rEhxEVIkWokpO5ER+I6rkbcIphSic5pyxosKm3ICWIlfifN6mEpUbuNc5m9rGb+A4JKrKUFitXv10UXjZjJJMXb1D9NTZdI4anbvWpitZ'
        b'4a51NOiy7Q1uW3WtrtFavdi60GYKDy+vtbv8eUVbjb3B5tLVeBqq3XZHg0tnbRB11XVWlwuuuh26ZQ7nYt0yu7tWR0GYwqv1QW0wwDcFvhG0HZvh4EVezst7Ba/Cq/Sq'
        b'vGqvxhvmDfdGeLXeSG+UN9ob4+3hjfX29MZ5470J3kRvkreXt7e3j7evt5+3v3eAV+cd6B3kHewd4h3qHeYd7k326mtSWK9oVqc0Kzag1akrw5pSNqA5qCl1A+LQmpQ1'
        b'qWVB58tQ2EK9UFQd3NUcfEfCtyetpoJ1dxnSRxfVaeB8WLmAGvvSFli0Z6xu5BkGp/gEuYd3kG1kSzE+R64XzCLNpKVYT1pyK0qMKjR8hoI8scbpBU9fmvl1vHtBfq4h'
        b'15iYRbaQ7YVKFEW2CkWkldzzxEEGKzmrhfvpo3OVSKHg8El8PMWjo09ewU9mp7JnCnNJiz5XgWLJXnw+WcAP8A58Xc97+tNse8glfDM/YyTkySc7iqGY6IHkNNkhTMT3'
        b'xnt60yytTYhmyC2U7keRqyl5wghyLxLKoBmMs8gVF70bmw3QyHYOhefy+LqZHGYNJlfJenwogtyMJndceAu510huL8Hb+uDH0ZEI9R2sUJNdpFXPeZJo5vND8B2yrSCv'
        b'fyLZLiCBPObwUS3ZCrdpWaOH5OXjK8m5RrI132Mh2/GWYlop3JJWZNSr0MwZ6qZMfA8y94LMI3LxfnILqoRv4QMFxUqkbOLI2SJ8C+4nUli7TDmpeUYDvjOq0GjikDZe'
        b'CCctFrjLuv4y3jMjNceQoiAtZEsBbVYE2cWTq9PJ0Wquw2wb5UeBIxRT2+Mp+ndgqjfFm+o1eI1ekzfNm+4d4c3wjqwZJWMv1xwG2MsD9nIMe3mGsdwavizofBmdzx2w'
        b'l1a9byfsfU3C3kuvqtGnr8FtnaWgrzIDsYuXE3mUNDyMonTdwr4V0sUBfBj6adxwuGYxbBpqky7GVyvQx+Ohn6da6v6xUo9aUV04XL7TO0nx51i0/CP1h8M/4++OMCT/'
        b'GNXR8qZwh7jraqT7+eqajJ9m7JlVJ13uqfosel80l3w94xPui6Q545cgH/KMoKP3Jr5MXod5tC1tVnIy2ZqWA0iBW8uT8wrJToMJUOQJPphXyKGG6LDJgORnPNPhqaHq'
        b'GS63c+kSj4vcI9fJbXKT3CU3yB1yK1qjDY8Ki4zAO3Ez3p6RPipjzIjR5HTaSHwPX1cg/Hh+GLlCTuLdnlwK/QZ+q0d+QV5RbmE+2QlTeDvZSnbAdGuB+iQbUvBZi0lv'
        b'TMXX8EV8uRSKuEkOkt1kP6D6AbKX7JuDUGJ6ZGyZpx0q0SFQw5dip2ucn+gJNYI80HwzDOdqAQaaZwMtsMHl1whlQecw0DWhyJSi00AripwUA+y339+hcI2Hs7/8lzXf'
        b'uuCdcbff/8r1XTcODFR+/U3r3Hfeivn6/Hdu7zp94PQGO+dSV0eSaecNCbty0oWFKpTXENn3rTS90k1n7zCxGAZkK3TI9j54vYAU4zl8I588cNPpiB+TIwtS8UZy3wT9'
        b'tcXAIRXewRtHa9y0ufgQDObGVPccY3KOkYdbR3jjYvyEFZs6CD9KhR6+YSQtBSOUSFXJkStT8CF3An3wKN4xnGzLwVeqYxHiV3PZ+CSlFz4+Wa8XnLSxQQceDk/jJ9U4'
        b'HSttDboaiYGZXLZG6xSf4LGL9L5LBYfw6bFcLOdU+R/SK3xhDdZ6mwuYnc2nsDoXunxqs9npaTCbfRFmc3WdzdrgaTSb9XwbODinU8FJx9SppAdaXhaFQYl3zGMVz3Mq'
        b'jh4VnOoLevTEU6o+Bj9IhbbOqecQjw9x08mbZEd2NR8CVdiITqCowjNkUdQoAsgivBCydOJpFCfCOyFLzyJGNPHptfixi9zHNwugQaQV4QvkDDnImBF5uw++lj+XbIJb'
        b'nB4RbwGwADpGZN1ofIDcwvvwHSDDnBLhO/jOJHbLTg7jI2TbTHyK3pmByH58Bt9lxS0wkIMRdfgQMD2uB8IPgV0+lAj3XZhCW1LJFbye3puFyFHgqVc9sRK32bkq1bzK'
        b'pELcfEQurJotXb7A55K9A9NnwflKVEhaVnpo81YMBmTZqyK7FFTiMMD8fKgPY3fwVXxszEReOxqe3QT/A8gDVqk1/cjtVfxwfBaun4N/vJ6cZA3B61aRB/ihCp8vgVsH'
        b'4Z+8RW6y4SSH8EEleagiR/FRSN2D/7VRrDT8OANvxA+FaeQi3DgO/6MHSl15ZwZ5TOBGEe1W+I8E+D1ZWeb5+GE02QCEmZyC/xFjpZLuu7TkDZ6sI2ep0BQBBOqJpwft'
        b'YHwxskzAG4gXoeFo+JK+rJiRE/FesleNN5MbCKWjdHzbw4rpbSNPyN4mfIocBOzCO5E5P4ExZnx03kByy0VuLQWUJI8Hk4vcECBopxkFaUfE+GBaQ+WDhagJvQpcqolr'
        b'BmnTyTdxu/klwJvCFrKZxQ6tvI83pfu46laubaKyKeMLn1Rnd7mrHfWNU+bSIumdJOSZDD+znXX5QHE3kkf5ATEgh+zDt4AQbykuItv1+K6QkYG35YOcc8sVQS4j/Ig8'
        b'iMDX8WaNfeDnWwXXFijGc/nw6JaJUTg9JmvZe6pfxEwZe+r8hqk/T7ifWflxdsn0ISkX+C3f6Zf86dHXN3xcc+JEjfbtse5pQz/+ePxHxyJmay//zBozfY9hcIHj73vu'
        b'f3vC6y0fmnrOGmPe/Mony2bF3rztfHNnknvqkjPZcb9amX6w75wxo6/uXfuNefc//Mu8XpUrauc9W7001jTgNWfy2D5jZDJK3iA38fVUk55sBTFYhS/zqyJHjsSn3ZRX'
        b'k8tkC94FcgtpxieW5hYUKVEEvsGT43hdL0YQ1YNeIdsMIM+BNKl6jQf8ujB4cppbR9kAuTqFckz8Ro80shVENSjqcp4S9RwlkD2Z5Im7D8MkfBef8dNxIOL4ImmhhDyx'
        b'pBM91Ss6EtgOgxdha6h2iDYzpbCMtg6i2JGj4DTwAdr3hUZQcOFwruU0z2KEKPhNgpQzJojuci5feIPD7ALNodbmclKpwEnpU+fa8E461509AuSWFpPrJ7ex90OQWyoE'
        b'63WzAI3ye09vQyIF6k32KJaRs+Tac8gu49DtyO6L8eiQqkRnHh0mCWOvVPdEQ9Cu6mhk6Ts/e4QkYkWm5qBdaHkuZ7GklGSbUTa7+mhaDNKhQ+FhjZaC9aOqpKz9Z4Sj'
        b'OHTdoY6xaL9f8AqSiMxubvHIdODLBwAc3ouqRuA79sqNP+Rd8+DuNzYs+cTyG0ttTYH12zXJv/z1uuuHb87b+nnpoQ29JiQlpHu2GsSPxY8thj2qm70mJiVmJORPF0vn'
        b'liZVHh6SadgcNzsm/xgVGe6rRH7+mDIQFiag2KHxI4Rnel6SB/YryO5UYPfkJNnmZ/mgnNxx96N1Ozw3IdWUa0jRm0CcI1uS8E2Y9jrFa+QN/IaeezHs61Fda6tebK52'
        b'2kS72+E0y/w9ilKQSoqDUYACSYBzzp5B+CZU20WfutrhaXA7V3SPbrQXnfEBdKOlzA+g24UQ6EZVXHNDKpCrnMK5+CrZgXcUm0Bi3QJNTMMw4wo4NBkfVZHzuHlBJzUj'
        b'gHlMNuQA99pkQ47h3fOVgE54R2uu6YR3WRLeDc6JBbzTRfDIMunS6hQZxYaP6wEo1hirARTrbc5B5Z5oOmTNoyeALlwFmhcaMTeP5RzUqIDCm3uHT7UU/KdpFvLQGZmP'
        b'9+K7IxUoZSbKQBl8HctpmA+kBk01hYOy/PGEPMSYF3ljNV43kkcVGtCyR+bjsyzrCl4LHOBQVniJpW7Git5S1qy+ZNdIoHjkFmhjo8hNnl1Nxxs8IzlUQ66j0Wj0IPwm'
        b'K0A1LR4loxgP6CZNB0fGI1Z9K77iGQnC5XI0Bo2pi5YyjumHxqGSkREllr59hHFIkiXOk0szRgpIAwLAWDR2FH6L5T1epkNT0a4c1Ghpisk2SnkHYS/eMVKNFuONUNA4'
        b'0FdZ3r/wQ1EOsoyMnGqp2j2mRsqbMBekmFtQ/uZ+aDwaT47msLyV+cmoBFnSNBZL1YWoWVJrK9Uggt0CtWTDMDQBTciQsg6JMKK5aN3syBLLoJuxaqnYMeQhvgoDS06M'
        b'QNPQNHzUykqYid9OBl6Kb2eg6Wi6HbeyoRm6IhnEX9BR3gAxNSt3FbtoqCa3XRwa2IRmoBn4TgO7uLxmvAsEuTfIUZSNsvXTWKEluhiXgGLJQzQTALTgQ5LM0ooPkksu'
        b'Naomj6HZOfhaLquZhzyCvoQWZ48FKp07D29nl/mJIDtB2yxulIfy8BF8gVGrfJgTu8ktHpEjIOPkAxa92UcSr/ZU0AdUCKSZI6gAFYB0uZ71hxWkQC1KL1HpLIa8HkMR'
        b'q00RPkylAQ4Bm3uMClFhHw3LPD41AkhkbQYfY6lrWRyDWNmgY54FxeSWEpGbLlSEikgLvsiy/9w0DGBN7afRWar+OaWfRFGBVZ6ZRW4J1PxyAxWj4sW4leV+3CsVlaOP'
        b'HdExlkGNiQY596PBoIPeUiMQWO7CGJfY8BWWO6EkCYSyU5G8xTIpObJcqje+UTIggilKF9EsNAufw49Y5pNKDYpBP5+lBO3bNSdRwo9G/ASvj1CgfDsqRaWvkf0s6+H8'
        b'aND3v75AlW4pWJc4T8KPimV4P8xvcpzcgYlfhg8uYCXYyAa8J0KF5q+Bipd7yA5p6jX1huk19VUuxrLggHmMBMyDr9ZEcEhJ9qIKVIGvlbGss+L6o0noDygs3dIUnhAm'
        b'ZR1CjgyKgM5swW+g2Wj26vEsqyVuEKCbrikCWabN18XLc/8EudcUIaDoJiBnc/D9JpbVV5cAkvpbY3mdpelMTZmc9a5mVoQaTYDhn4vm4lPhLOuEqWloAUqeFZ1uqdob'
        b'VytnPYdvrcDbEKqbheahea++wrJeqBuFatG6eaqplgyv2y3xzJryDKCFP+8fhiylA5cmShcn5KUjC6gBXKNl2u3eIjABVqyWHBuGtymgDx6gSlSpGcS6NoVs5fE2Hij6'
        b'OuAL8xcAWn7+7Nkzj0IJRDEpSznVol3pWSYVvIsbg+pQsitMZyndvdCI7G8f6aN0DQQW8Ld3bk5+/xt5Qmbcpg9XXaosPNbiO3989HdvZbfc6tEkJA76+HfrmlOrp+77'
        b'TUWM7/iuK9uyvj7xczTl0IXFAyMHuONfUQ4fseVHcU9rU3sdSs2N4//eMMieU3bCpfng1uYx/zt9gKK+9lrqhF2n57k/MM31tfT3bZvi28kdIbp+OD1yxLQ/PW5pmvib'
        b'/xrxsx1/X4rv7bV/a9n5psm//aSX+Xtnpv4qvTjxes7B6wWJ2XOu5/3n9aKx13PvnXL3mXi7+dUH3tWVmJv81R6T3819df7WsmMf/uNbt0cliFWrU2e3mE8dM5V8P//+'
        b't3525Mdf/VGvuGmtTRMLz1qP16eYpulzLxefLDo+rs8/n50bu2RXc8QZ9/ecQxb89VeVH6zWJ0ae7f3oizfP/qzllbW7P/3ngKMRVavVXwGxmYoM+GpGPEi+RdRat9NA'
        b'zXU3QfO6xJOrRrKdCdb4jVfJwVRmYQD96JAsctxf4O7PkGgN2ZCwAiRBUL0LjXmGXCVQsrcE4sX3yAkmWjvL8X0QjLfn5+IrqG4GUo3jey2rdw+kRZ+AiXkUNKLLLnwl'
        b'p8iYTE2vZKeAepBdAgjzA/XKkMKKIpRkESTCRMkijKfaTAVpJr/cpggnKrgYXsGkaAXHP3uhL89/EfqraJ8W+H++0FfB/6Ptq4Cv5h8KFc8k+Dg+StBwMSD/AFyF9gv6'
        b'60wISFkCSFme6u6EK86ZGJCrEphU4reanAghVw2hj4zPYHKVJFQVwkEyWOtryD2yTglCh7fsOSIVtduiIJGKeyGRauOLifJqSaRaXEelF5RsmblMe2JUD1mkOjWTch+k'
        b'aYxfYtg6ZwFiNoW5gFV7R5JreGu6LKGDOPHQ3uPApwoXtWau2ip+Yql85/qu03tbN5ze0Hp4xKYRH+iOnm4evkmf9PV8a5G11rZHcSOp9FCmYcnmys1R7/ZWnZpwoO5U'
        b'7+8moO9GRl4Pv6jnmPktg9yZw2TxTeRiQBa/HesXtLtB0N4SgrrcTk+12wOSttlpq7E5Qe+TkFVLO2Sthtf6Re2kICRQuCBz91jQK4AF9MHXaZG0a9D6mGch8CCDTuTb'
        b'eNP0ACakmfSD56UUmvTGvEK8JS2vMN+YB8oeqM14N94aTtZH4dbnYkV7QfvFsKKTtd1feHusUBVJQsyG3kMinOQxPidQHR+BkPKwhmHGFWHUmvnC+9SQHrsrlUPZ9pQ/'
        b'jFa4xsKtmxrbJ5YFbPxvbFjCVYd/NO3dQV9EnY96t+bduPN1BwZ9Je6Xls1RqphXDq0f2XAxEkV8HqGOjQcFjJny1q0hdxk1DMMX5TFfirczK0N9Od4TrH6Rk8sk9Qvv'
        b'7yMPXtcokdRB7WqPEOESQoQlcJR6OXsHo0P1c9GhTwAd6INbgtDh8xDoQJfmQIA7Q7YEUYY2dSsYG1YsJUdwaxhpJuvQc1V+oYOl9cVU/k4YwYXECHVRORv4pUui0SH9'
        b'eFBiLIbYdLskJkRMVqD33fEUGwzqCpd0sXmWgA4l0i6zFKw2hCH7hc+OIVcBpP/61SkfgZL+qeXrVbU1l20fWy5ak6sNe35nmfvOW7sGbtIf5b5ek2c9YPlY5D8w6BrS'
        b'pgwvqUiPWZZ+IX3syK0j3RlxGc7zApr0rehDaB2gDTPmPsAPY/GlgkIDP3shUuRz+CbZncdY6Ej8cCBwYLIjrbgQRLwH5FpRLr6sQImlijE29KJae2SDbbnbLHpsZtHq'
        b'lnAmjuEMHx3OxcmWIwWvfcY/dfYNYI/Cp6DZfWF1NqsIT654jqWISgzO/gFsogXtbMOm2M9CYNNgOmnO4xP9yTa6CgnKnL4QtwDG3C3OpdLCUHJTWZlUVi0EDbEyGHum'
        b'SNijYCuESq+qRiVjkMBs9QrAIIFhkIJhjbBGURZ0Hmphhxav6oRBSonT/D1hJNrV97sULWJfX5Up4cpcQYHiesUyBLpQD7gy9sB63mWFO+Nza/ttvxG5Ll2r+NnS0vRM'
        b'36dZ+Yf5zMTL4eduXxpVs+26PuGHv/6/C67K5dYSQ/ieN/7zKzuy90aPGbNklml51pIt3zy+quKzny4vDVs7pPiGzfkHx/K/PDs66/pZ+3tL1xj2J/13DQdyGqU7ZTPw'
        b'cbZuN5PsUiMen+EqyCW82830rSv9ydF8YQzrT7agPZY8lOyem/FVvDcfpu4gshMebynmQAPfzuONaRnMnkTezsW74MYjAkOSBkxMUcjhJ4X4LQlrN+noOkMhKHSHzKBj'
        b'4o3czNGjuhPKVF3e6oiw2oW2DvjaW6JxvTSAp1GAr+HA+Hhew8fyICWpnAMCWKukWAuoShHRp6r2uB01wQQw5FQBbKYSp1PXHoNpoYfbMDjh4xAYTB+ZlImv5RcbZ0KH'
        b'SggsIe8AfEZBjuK3hnTNDKk7SWBpG9Uo/1UxKRK+8Z2Qd4CEvLtSv4X21V8Eec+iby6olJDXPHQgmrrcy6FGy4INjcOki09coAArVgjIYin430XZ0kUnKJNxWR8o4XFD'
        b'kiZLunimpicaMqoBGmhp2pxmkS4+dvRD49zX1KjE0vftqdOli+NWg0LoXi7ALHGeC6+TLr4+T4W0OX14pLMYZq7Kly7GqPWguveh0Ac5M6ZJF+etmYKaNDk8kO7YlUsF'
        b'6eJv4yah5Tk+HgDFfpCZJ128Om8Cchs+oM3MiCoeL13sOQf0/5xWFZTZdHF+kXTx/XAjmttUroDHp/WMkzvk7KAeSKd4oIQOKeg1vFa6+PuGqWjdKLcaLmYIIwvlFk0F'
        b'pXPIOR5apP2MWytdLO0JsuikDFqlgoGzc6WLzxpBx09Kpl3X9CO93HUXPGNBPf0bB23PqOy/QLpoWVuCTk0t5wFQ3kdu+eL85SL6etYrtOtqxlTLarPDvRB9O/2aAI9n'
        b'/4NLli4KcxKRQZOtgotNPQrlDtnSFIX69k3noOu0PcsHSxd/WbEK/Vlzj4MqLR3VoJO7bgjo58nDFJS8hRWtlC5+LXsQypo7H/DWwh9YMh/Z137n15IaPTj1esXuwiKS'
        b'HrPpvRt/+uirQwvDcheNC7/3cXw23xq7rbxq9Gu26ob/6LtdaIx4992Wb777xf88OvzHsl+MvJbwx3OPPvtFz5qPNs2ZOW79nGTDuHe0QzOjk2dOta3/3qTfvN56O319'
        b'z7n//P2HvR0zJq/bezH3L1NfP37kzqBNLcophZOOvl8Yu+zAr2Y2jp+ya+yW3uudv+TnF5374rVz28fenv7jV6vylfu/Xzjncsrv/vPskrWz//Q1759TLoYl/Po3OwfN'
        b'HvLrU4OW/di4Z1HajUrF8IuDl0X8avsXAz/f3f/GTy8Wjyw+nfbB9f946ztFyd/P8r43yjp27HuG+z1/1/O3v3tt1f80//e9DYtL34tYOFa8ev2zZVO+9Tfvt41/XP3P'
        b'zwq/U7Fr3iZ0vm5To/fJ02/+NezPf09z7F7012Hv6gW2SEQ2jcC32rh4gIPjA3jXGHJ6gLREtamSyzckjxmfA9ITEGJQs1dQHwd200OOm1Ph8RSO7MWXkcLDUQESX9NH'
        b'PoekPv/QDcEOtvtTglxlbVhsrnXU2SmBZVR5rkSVx2tAM9UIQ5gsEcPp2JpTDJMrYjktH64IB/ki3P8ROvyyM8WvtH218Jz2WThQdQ3o4c5BAZoOcuwKm9UZRMa74TKc'
        b'c3CAgtMirrZR8Ljvh6DgRrjTi5zH94CE4y1kO35SnEe2k214B3ND2Um2FMCAGVRoMrmhIm854jupIAr517UIDjbqGYgq+TAujBMj2JICD5oOLwobwyoFm0JUiMqNaANX'
        b'qYRzlXyugnO1fK6Gc418rrEpKHuo4cUwMXyjBq6EeQFcZTjzJdT61Jmi6LS5XEXVqqD6aFDQ+sM0ymIkr6mAF1WNRmY0qmYNMBo1MBoVYzRqxlxUa9RlQeddeTR01seV'
        b'Rcx0l+cm18rgdyAi28oG4ivDJKeY0nVxvMsFZ6ZlOf22jqCrw4rf/+hGv8RROT9wNzWr35+7MSNj36+21py0PtsX8Z3LS0cddVsXfU38vKjC2nSyeemVCfuWvDIn5u/n'
        b'frGl9dWd33VbvjnL9+Q7v/3lsPQBv79VkvQ4afdXxDMbtn24W7Owxn214LtVb+Wv+Cc6PqH/nZK7+nAmKJEbVZNhkgWm2FILTLKNRjbHFkxYRJdo8RvR8iotXaHFu/oz'
        b'KWou9vL+5ePKXnQBeaSyjC3ugnR0AJ9gPnRSqeRhDN7H4y1D+0neNBfwtTWpJiP1wSEPV6nwWT69yOGmskUFPoov4m14J9mZb8Q78U4quz2KSOCJl+zH15iQhi+Is/G2'
        b'Ypj7pCW1iezQ4zcVKDpMcE/Ab0qLfhcWZ7EMBtyqQHPJBZWG70U2kUeSCW7PcnwSb0sD+c2US3bMTixmNrhzAlm/GMRAKlWRveQggNsGan1eoZFD/XQRZBtP7qWs6izk'
        b'a16YtLSRDrXZ3GBbZjYzgtGfEQzFammJOoEtF4YDkVDJHwW3MlrGaZP8nEQCND6hus7FVgZBqbW7V/g0jQ7qxCDafCqX22mzuX1aT0Ob0aQ7XUXlHE7Pqf+jtNaYTA90'
        b'JdGZEqAdQ+Hwjzba0XtTZ9rRqa7tJD1O/tKp4KLzsQktggRIbVxRK+fTmOUFUThXuGx1NW2+G1LHaSbVWeurROuUSCjlT/S6Cq2M8UP033whkLUAUs/5lGbac05jAE4A'
        b'mDMNDlHwqDMddfA+6arMhVKZYWb/OHRZbvRLlSvXVW2WRrXLUmNCltpOvB6DJFsT0M9/UbCmfzzqSO+EInuZwsi56DwM//0fPsn6ueVjy7eramu0NT//NmT+jP/q1N/o'
        b'OUZecvHusLZ5CpMUdNxeZKdeQm8+5NSJtLuCzIABTzq0Fq0NT1gZ70eFdrkk5x/BaaKltM2BYADGQD9SL9tY6D5XEsNxtD7qdyGwPDQgoPb0Tx8BmGymjnxmsy/cbJZ8'
        b'1eFcazYv8VjrpDtsNsGUdToabU5AQTbr2CRsm3qjWJOp45/V5aq21dX5537H+dtKsU7KBllYQ6i1+q9ItmtoEK/kudhn2h5MogA9MUnyhcZvJ+S4yFZ9Qa4+z2hSofBF'
        b'QGqtZGOnoY6Qf127uDaOLnKVwj5hX/S+GPhG7ou28zU8nMkfkW9RhQlhgmigHD/IPzkGuC3l+WHAvRU2JfB89UYEHD6shQe+rxTDWTqCpdWQ1rJ0JEtrIB3F0tEsHQbp'
        b'GJbuwdLhkI5l6Z4sHQHpOJaOZ2ktpBNYOpGlI6Fm4TAbksReGzWVUbQ1IpUuerdwrM5akFT6iH2ZpBENz/ajz9qixf7wtFAZw1ofLQ5o4UWjbG8RRJ04kLWtB+QfxGAN'
        b'ZrBiIT2EpYeydE/p6X3qfZoaYZ9CHNYiiCYmk0g7D2hvRXmja8LEZFHPSoyDElJYCamshHhRKKMWmzSQe6oZ8Xw6PFwX9CdflbZEtLujV/kUdpBffQqKj6HQr6haHYQA'
        b'dOJE+ed7ESUjkgAVRjtQHli/Q3pUTZRMXtRMnNIAeVEz8qJhJEW9RlMWdC6JUx/2BkrVror0L7fB7rZb6+wr6X6OWpvOKjfIDozN2lBNN4R0fGRCo9VprdfRxk3QzbDD'
        b'U072aO60zCKdw6mz6jKMbk9jnQ0KYTdqHM56naOmU0H0zyY9n0wfNuim5U7X0yKSM6dPL64oKjcXVRROm1EKNzKL8s3Ti7Nm6E0hiykHMHVWtxuKWmavq9NV2XTVjoal'
        b'MPNtIt2nQqtR7XACTWl0NIj2hoUhS2EtsHrcjnqr215tratboUsWbY1OW7UVytGbdJkNUh67S8fs41A4NC5kWUuhU0XgfZ3rK/cfRYsJrOL0zL8tx9//oPQAf+vyYZmR'
        b'S8/LCejEsmLjyBFjxugyC0pyMnUZ+g6lhqyoBEmX7GikO3ysdSF62A8UmiNDhLPQNX6RcvzsWyrLn/ry5UlsWypNOv8SZXUy6nc2yUYUMfPxgKH4BDVeGkxkB9meP4c0'
        b'55PthYv7SPY3/IhcHsjMGOddO1FfDsVcG21p+DRsLvJQ4UAE+Xsvs2FGWkpIM5Xg08gWOCsuk8qpyKFrz4WFuYUcwlvJmTByd7ZkTXt/IvWEQeOSTRZDk2kFYnpkHn6I'
        b'H9P17NR86gq6wlMwK0cS3ancTvbocSsqy1STg/gt2aEm1cpTRWrqcM6iPeSYKZlc9g6g7gxo7v5Ci6FlIi+VTW5Gzm4rmu5yKgA9Feo5ixxJK80hWwtUaCY5pyI3yBsF'
        b'9qJnKxWut+Cxv7z9cOjOiVFEF5OVOHftH4ZX9FbNXjZl5tZjuooPsvM2/HRu3vpX9wwb9cn8H4/9ztQj3uUTtyeMqHrDd/nH5+Z9o/Xi47w3/9+xEz85+WHBUt/OP/Q+'
        b'sfCjmZ8PWjFzwJ7SuStbh/e78yT8ofPUq/3+X1rpp73/uujUk8l/fteRsOYXX534P9/J7DNYmZj+asPHV8ocurXR+36pH/7bSxrFgarMT7kfmXod/Yl49/DxmF9m/yHx'
        b'+jc+PbO19dz3tux9Q/2TX6vPrH5l82GjPpopMHg/ProiApqsL/QYU8jWNB7FYy85pVFoXiWXJcfGuzOHktfxyXaeCsxLoZBsZQaYRfg42T8Xn8835RUacnEL2Um7TkC9'
        b'8W1FA9k3XnJlWEfukuZUYzI+SI4EdkyMLXVT2QJfIpvJ9cCSl7+AeLIRVK2HAnkLH1AydWx2dDbeBrfxeXKYZVGSIxx5MHcUu5sJGuU5KgVuLcBPHCokkKMc3oHvWyQT'
        b'0H3tUPpwvh40MrozTUke8FzMKqkjLpMj0+BREd9owyimCQJernNTPkY2jydXqbLXomfb1KSmUjQetVqJUvEtJdmEL5DHDNj4etA8qTxakJXBQUVOcngXOUreZjfLyRsY'
        b'Sio2FfadRWt5lwNV9Ta5xfob5hW+ReuJb+NHhdR3g1q7oxYKE8gB2ZZ1DB9ugMdr3H5JK2q6kD3OI3lDHyObsujjI+sNeIfkGhyFLwpZY171r2dF/ctWrY6SNIioduCt'
        b'shaaJQvRmgyF5CjNU2OVArRRLZ8AKXaNLaaqVCou+MNzvP/8H+Eq0MYkkmbyFy8JrGGS9P0KPUxFfiWzg7jbJpu/sFatV0uFxLcvnZVpChTMBGJq9hkQLNkP+zCEZN+p'
        b'/i+s+bVSbZIKHV3qZwv8+lkbFL/O+nRoeUBCoawBGLifNyQ7bVbR6GioW6E3AQxBdFS/jFKtMFfZq7usktlfpadDaAVAvukW/gurq6wzmGDZFeSqAOTU7mWML1cBZyry'
        b'63UhgNsCwE3BAsq/Aj9chr+Ik/tez8Mcs0p6ooSkXdWm1m/N0Mid0Z348vKVqWGVcRYHJkZX9VhMe6WE9kraiwg+X7ZbpJrou6tJQ6AmxucLTS+LHtLEkGrRVQWWBBAk'
        b'vZypCgA72JamkwdWV8f2n3dZh3+b8eXpmU4S4XQq4bt09g7z1WWz1bO976BjMCG/04N0P7ys+pSBqgGtm+FxOnQl1hX1tga3S5cJreksgCZDk6Hh8ODSMaYMU7q+exGV'
        b'/ilRZ3t4uZ6T9uudw9fTUouMwLzvAr9TTOXwmz3j7PcvGXkX9bD627Z+n1i+XZVjTS6cbkuO/djy9apPIc1X/TLu3bjzr/0y6t3lKt3OgYfWU7/pAWHTG1r0Cma9Leg1'
        b'ivJSPyclNxdIzHTJYMmJ8tI0bTupZTiVkpngQoWWJ8OZWbyXhlyiW8TngAAQ2CPuiZD8B3aPxlvzmXTJv5aAT3Jpo8m57oxWamol8m9OklyT0NrwlQnAe1ZG+zmBnEd6'
        b'bHTHwtoMVHPg4G5noNoe0gzbvliQI6ZC9uc4HVH9HXT6l3Y6qgH89HZChzKbW9LZPXVuO2isMpH3uCStlEVk0Lmd1gaXNSh4Q9WKTgXRMiYwC8YESyHkgaLgx7rQ5rQ8'
        b'R0+if52NlLLryuSlO6j+k5S+cOza/4vqiTzU3S1+eDXTfl5A9xmGHzD1hxzHR+w301oE5sn33+8lf2LJsybbDLG/sXxsWVTzqfgbi+I/9Nt/YpgxbahWP3Vpz5KzG8af'
        b'GLEJcHfukpGRaNgfIjyDlXpeEt33C1Mj8sfO7CDeKzTkEW51UzayYIU7pETbSB4FRNp1+InssfS8VUyXzW32jw9j2AxJY2QkBYFQKYl+4dzKXn6c6vSMHxaTuCiede8W'
        b'xXKYAhhNN4KtCcbo2NdDYHTX0F9GQovqUPGu6P/WAP1nDOhFMdjk369FaUjXPlrMyYU5uFBrX8DJ5SU8tD4s4EIYywIzzuG0L7Q3WN1QR7vYFd9ssC2TqfkI04gQFoeu'
        b'zSyiZMtgzfd7YAIgk67UtsRjd8q9I8JZtVsn2qrsbldI0w6d71ADl6PeL4PZgZla61wOVoBUtNTBNTanq2vDj6daqtH0abnApu1LPLQ8kFySKUvWOf21Ali5bitl0s8n'
        b'G519JjVFHupcBxxhM96WX0RXxFlgiCLjrBxTHrmN78tOn6WkuWBWjlCqx625uteqnM419tfC0LSF0fUZLhZXQofX43PBloucgMNoKcI3yf4K4GD7uSXkjmZp7zlkS63E'
        b'MQ+TG4jc0nK4GW+C5EWET4zWeqjWU7nW6IryzM6hzugVpNkwmy3Tb8Ot5TkGCmJ7bgHZyoFafFa/HB8YQs6X8zo93Qd/T1tCLs7zUGHZoCcPguvU6C8QtOLNFSVzjLPV'
        b'qGStCp+1rrWvSv5c4XLAQ+NvLzF++yH155sxay0u/vOogncUWoxGXU0OM0xN7j//nfNz1797c0t+kztyhG/Fb3skVP5XS0vPAdr7/3s6f2pMYmHs342Hpk745tX7vf97'
        b'68NRq8dF/e7DWz9NacrvO/NJ4vtP/uRwKf9vXp/CHxxLG/JgwM+qsD6MadOJSZVApP169phBEQ08OdqD7HdT7wb8xszMiBS6w4LSR3JztZ+MDsC3FOTadLKDcfEEgTxJ'
        b'DQSCINt43jgwnZkkcvFdVX6QRSGrVBsjxJN9PdgSNWnG+8mZdvYXEGVOSkQ6qlrS9h/hS/gulR9AeJheJYsPCUPZ+nUp3o/3Bfs9o/IhzO05DD+UnAzXk+YmyRDBke3z'
        b'ZUuEEj9hd6fPIluZHUIF+PCmbIkg58ke2dnvhXxXKA1toxH+PauD2qh+oor5qmgZ7deyc/qr6sQH2pXirwKj7QE62B0zEIKytXGE1+DQwvl9HNfTT1wIZ9luavIyPEFh'
        b'BorWJSc4F+AEI5hq1kbuutNHXlId0bNaeLrW0y8GajExJJ2bXjG9ozE9RH2o21C901bjU7nsCxtsoi8MKLTH6QSpP7taEVRXalvW+glgnsSt2uJhIW+E7DmjrdHKvEvR'
        b'rATepQTepWC8S8n4lWKNsizoXOZdh7vlXVIsMEnMY2wgWLvpermHtktiAv5nA1sCujbMs16QnmKPQA/Sa1aq45l0060NVImyyveqFgE7C8nH6KISsJay4nFj0kew5SS6'
        b'1CNSvRX0qy7BBzp/gi67zrpQt6zWJi9WQYNpm9ty+BvVFfgGhzsEGKcNGtLgmqDL7Cg/W+TmvAAj7KzEhRd5qDGNHIivDGaD+ESZcRZplulyRQ5cLZUZG5cRi/fiveRW'
        b'PrmVh4aSs1HkyBq82UO1jjn44aR8kzElD+it/3FylJUQKDwnryKZRqPILSgC0Zuc66clF1MnMyk+i8tFuxBKT59xw7imqVZaxSDngAFu8gvyY6e2F+WNeYVlwZL8trIw'
        b'8qSQtLJ4H/jRfPyIbGN5QDPcmZpL+Wcq5aht7BpuXHflGPIKTLnGFBUi2/TaJaBPHmB7g/BhDdnRjrvTxlDQyUDSQVg36I0pyjwlWkkuhOGW/uSUXmD7c/olrwHA5BK+'
        b'lFcoIMUUDl8Sxknx0U7gK7Gp0tNQ4wHkpIYc5lfhK71ZFDKyGRlS80bUF8rdyKGewwVydNkc+09vWqT4I+mzl/f7bmoUSY9RvP/q2o+MESZTpPF38SvXxeTv7nv3m2GL'
        b'br49ff3q718tVE2yZw9uRe9FjJz9j1Nnq5b3m2e49mbNmwdLRvzX9//4T+dPCiNaplR5TxwYsGjNkZ575o9+lBv35ufn9Nn/q/9Bkzo+tu70hoa3byfWRLtbKj/V5e94'
        b'Zf7/vfd4e6Ij570Bk/+ZkrbhELBwFhdiJz4fn09ZHCItlXwVN2J+Lzd1iSCPx5CWNv7tZ97kLr4kMXDQuh4wRT8Bb4oPiAET65SIiQHkAr4hWdXfJGfwG/m5hSkgVvEo'
        b'nzRr8DYer3+F3GfLB034WJ/2yyjkPjnP2PhrIEpQiSsZJL27+bk2c2CnADlNbktrIyfIQ7wO6gjy0eWx9QqkquMHDcM3WdF50+ZR59aL0IIdxYC/ZGuhAcYkTSD7KwE6'
        b'rV06uUeap7mopaLdggHeUCtxUe2/yc4fQXmjTD0YlzcFuLxqHI1OoQnw+HD5q2W7X3hm3A//p0q5smcwn5XLkmqpkri2SA82eqhpz/DDXs7zViGVVBMQB2wBLlgLh0vt'
        b'ZYJBPwghE4Sq68vwYU2ggV3x4m8HePFAyjiArDI2EuA7wcZAvYJ6BLXyRVB0tj7BSYmTk9oZnNRWQD0BRUe12cwWJ5w0PBpbxPAJ1GY/lSZDrJP41H6rMrUFMfXZF9le'
        b'raUCVJBkVcueajdwPf5NC0pd4Z2T0tJedLzWIGrYVvBxChWneMbDWPV/xk9Qscg8vPDlfqMU2vBYjg+X4vuEK+I4PqF9jliFjuMHMAz+wsN2bh+HuXbGRe4sKSiShHsO'
        b'ha/kgVKfwac6Mb1w+df1RQd3J5GvVIhCpdKOKlWiolINX42orAwTVZXhoroyYp9yn2ZfzD6uRtgXI2paeLEYRKUIb0yNwByWqROP1hYpRoha5tIU1cJXRkE6mqVjWDoa'
        b'0j1YOpalY/ZF2XpIEYBABKN+NtHeHjUasacYR92SoMTYfVEAN0aMb2HO1Sxfjxrq6JQo5+gJZVIXJ+pCHQd5qMtTb7HPRk1lPNSNE/uK/eA8QewvDtiIKhOZCxOqTBIH'
        b'iYPht5f8xBBxKOTqLQ4Th8PVPswtCVX2FVPEVPjt51VBSQbRCHn6exGcm8Q0OB8gposj4L6OXcsQR8K1geIocTRcGySXPEYcC1cHi+PE8XB1iHx1gjgRrg6VU5PEyZAa'
        b'JqemiK9AaricmipmQiqZQZgmTodzPTvPEmfAeQo7zxZnwnmqNwzOc8RcODd4NXCeJ+bDuVEskc0xglgoFm0MqzSJCraYNMunyqxnvlVvtpOW6OSXbkjuVVKcWRAEacS/'
        b'hU7qkqOTxLfqFQFvnw4uM+2dtZxQQL3Nba/WUadAq2QUrZakULhABUsoU7Kr1K3QORokUTGUKKfnfSrzUmudx+YLM/tr4RNmVJQWPZ1U63Y3TkhLW7ZsmclWXWWyeZyO'
        b'Riv8pLncVrcrjaZrloP43HZmFK32uhWm5fV1epVPmF5Q4hNyKrJ9Qm5WqU/IK5nnE/JL5/iEiplzs1t5n1ICrPHDbWcJa7ck0kTpL+9SUhq8mm/mmvgNnMgtFlzRTfwp'
        b'7jRyxbt5kW/iExCNHNzMNwEyr+ZEoYlbipzGJo76EcJT3CmBxhsWVb0gXxKKQ2PRaq5BAffV9KwZ0eeakFkBpSpPA8U3q0QNG9ywD82htJGObmfyOLd5nXV8oCsZn/WE'
        b'pGFYpTLYlW5MWVKXTWC+XGXFxlEZI8YGo5EIikluDRX4da5GW7W9xm4TDSHVArubKhHABv0OZgyyX0uUUBb0FKe9ytOFYjGB3p5gEW01VuAvATSygKZir66lpdulfgJk'
        b'lOEAgnVu26/pmD+Ntzew9ai21gwf6hru40w+Lv3XlHH8+hn8PRVM6elFerUvpiNYuo5irWustfrCZ9OWzHA6HU6f0tVYZ3c76S4Kn9LTCNPE6UbMssAECMp9nGtRt5vJ'
        b'Gff9BSf7yirCVVycbPPQcRo+HGSkldESAry8V4CeY1XrUpj4W8AnwA8i4BJg7Ig0bOhWNNp0FhiSamD3daYs6ddiMTmz0Qu6k8vrn+7uqvWPgIzThzkmhEbETuB4P7gY'
        b'GRydw4v4iIAXu8AGxKexuszMBdOnsS1vdDSAhttlVZ5xckDGKPS0mrkKeOqrQEuGzpB7QddYZ62mq7BWt67OZnW5dRl6k67CZWOIXuWx17mN9gboNSf0pWixUDy1ios8'
        b'kJFmaF9K5/Xb9huHOBaqIRAgPLBxiGPG+xcK2fDh70KRnIpGKp1J5Ma2vLrW2rDQpnOyS1VWuuLgkJZsIZdV1+h0LLXT5diqFfRip8Logm6jDTjHdNq10Lhp1obFzN7u'
        b'cjtAdmTEoeGFCIFMBPxVMrMqWWj/etjEl8gMpUcBOzv0L/VODbGQR0O329y1jjYuZtC57EBR5WLoY3R1vZ2PaxdtlAuaQIO/T7DIDDbEimC3dpEqh4NG1dXVBBtgPGwo'
        b'xA7DEJJELrM5YZIuBe5oraJuAl2YYtoJmBShOm8ViypiZvglryalGnNyaTyM7flzqJmiL95BduRAqrgiOc+Qa1Sh+lgNeTJ6Aov0N5Oc7QeS7XVyZ1ZynpGGPd6ZWoTv'
        b'kDOlRnKePCFHeTRqpnLhPItkSDiGd5Nt5KbTZSrMI/uXqWJRND4omEaXeCi5JIdm4IfBpovkImNKvrE0uUopl52vBDFVgx/i6/g+20GQ6SBPXMly4Hh3pBLv5Mj1CHyL'
        b'Rb2ciPfhG2W4hRy3kH0VpIXsryjkkKaYI7fxtdhsKdrvgXjywGUaSW4U5imRgA9xeB2H97LnyeYJ8105klUjH19V0EhHZANUGF/GF4Yxo8magfieK5lFUnJblas5csWM'
        b'd5Tbszb+inN9De4bnSnxLZNLp1m1M/b+/uB7ZTdWt2z6ZN2O+Nrfvi82ZtdNnXn07Pph38pZmvf4d0W/uz+8MlLTr8ftXoue5u040E9xu/L0Vxft/bl+gvjWabSh4ps7'
        b'Xt/+yrUnLd+MvHbxJxMG/1B5ccXNist7lx7tO6rfjz48NrTs4Gdhpb1+u372jlWfL++VcCRh1/kY+9vbBxy/Ndnp+n9rvnlw7JFzjT99q379pcktqg8ffRT3P4Ux7+2O'
        b'OvoV+5bf3vIO/fTWqIYFz/7w2Ss/mpj01b8d/dbEgvcmPvnzZM9Nlb4Hs3jgW/g0Xasg2yPwtnyyTY0URg5fwdfnstuLR+vINXIn1Ui2ki1pOaRFQNpsQbUGP2bWjPQZ'
        b'arpwfJTchwwcUqRx+FZFgrQl7wG5nJ2aRzbjlsICuDWQw8cnrGWeEPH4KrWBFKYUqtEiclml4DV4N74jbR7cURsO1Wgk5wA74bFEDp+x43OSn8WGfh7Xos6GHNmIc2qI'
        b'FHHhGtk9PtVEHq3Rp/iRKJrcFFYMI7elADI7F5Er+bkj8ZWADQbG/ha7t0BFDkLh9eQqe05RxAFWPgljq0CkNQOQ9J6JGlhyDSa8JY1OKihCp1OQu+Qm2cmsTWZ80ZUP'
        b'c0yeYLglLc+Ab+DjdJalkEdK8voUfEpamD9ODuLLQ5LzpeBcdHpwKELkyVG8eZSbRmIbMmsO2Tcwv9jIIX4pl7mIHJC2Iz4qFvCemcGbLPkVeDPZ5KbO2uTyTHw8vzA/'
        b'v9BEthjyaaSEyXgfrWgK3qHE1/DdWVI/HMH3G8i2oqV50BMqpMji8NvkwPiX8JT8MjsV4yVKaG5P/JkZaSqlZGulT3hsjGxAoh6icfBL9y0qZONSFCf5lEpXqV8p/eXX'
        b'KbiVfWWZJyQY/1Yntinxy/iGctKjTJLYR5k5FOiiWCeZj9D63n8PYUDqtk5QJhUmu/ajYeFXWIgvkBC4oPArPHv9x/N9aTaCfPCjUPLBdInBydtgJLGQCjLAbyjPCkhm'
        b'sphAZQaXLOx3ZkfyqkIHOaODVBFaiujM3Mo7SyxWyhXbMXE/T3VQZk+XVFZQcaRzzazVtdJKfb2t3uFcwVaAajxOiS+72Ctgns/gO+pS7WXYIJ9Gt9W5EBQXf85u11Aa'
        b'AosoEob411D8ghQVf2yuYK3/OXJA6C3jGvnFLq9oUVLdCIRKLIYis1PaBtEwrC8aFzdMBRcnPRnWIF3cnXUPLedQ0juqqUuS4rR9mLPAbHIfb3ZFRvKolLrb70Dkymtk'
        b't2cm3FpYoQ4ieUym8C/W+BltOV3unwOEcDPwfLr+0uZFAJRpZf+YCTW59rKflCtdF6HAnOG+whZp9/pfvxsVw/ebljXp9UE7T72Rm79pwYffnVZeND15h/nzNVvrez/4'
        b'yQ8vzx6X+Uer9cayz/pOuDE440+KEd9IHrZVc+GnP85pnbV848DvT/vw4/f+eq7aQXSFlfaf3FWPK+tz9EfhKa+O/aF64dthB6f1KA7/1Xvvjh762xHf3zbovV+U7hx8'
        b'83s/fIynh835a+WrX4y8/55p1e7v352k0f8qvuq17046s3ottxSN2XqsRB8lkdK9CdP9K//kdbyNbmqoIYfYvclNfH6QuBE9tnS2UDe8ie14IK+bJ3XkFX4+kVYIJb1N'
        b'njBuqsI7+7N1KzWKw7dZ8CGBXGDkvjydnG5P7f2kvh+5iq8B426VGPJpsqcy3x+hqIrcxCdr8ElpXeMQ2UeOprK4GQuMLHJGBL7Jk0u98iSm/MA1E6D7wxNBlZ+AtCW/'
        b'H2MLOTkvVeazwC/JKfIAXx+F7zHXhqbxnJ9d7hzRgWOuIlfc9H1JZA9IcTeZhJoL1Q90h3kE7RAeKrqVM6dp8FkTPsOqY8IHBqWyZRYlUlnwiUV8f5AoWqVomser8ukS'
        b'zAC8s6O32/1c1tg48jZuSTUUgkQqx5GPXjIA7xWcY/qG2sT+onxNLWsLjJNlBHEyzQTKw1Ty3ocELpZxKxqSI4pxM8klIoq6QUTJfEIuqp0P3Nr2LKub2By8lLfN9+EA'
        b'HAwdGVXCByEYVYcKdFLGKXlhyjjdwU+VcfhSs1mkyLl5OBc2cAmQQeSDUyywxVN+qP2pYqgpowYaROvn05obHGZZUXb5BGuVS7KshFDafTHmwAq4ZIEs4uVt2loeepFf'
        b'meg3pnTI18lMGFh6pmHmmtnLHTbwzsFNHGsLWiw4dbRNzvgm7hRtAzrNreYaItyCyDWxNM1ZI0jGQzhX0BdEsDbyRU+HBzhmvd0F1aiuZbxmKJB6apdiyjI9gdFjXdDT'
        b'Xt9YZ6+2u81Sh7vsjgY2Wr6w8hWNkjWKdYpsevIpGWP2aSRbrsPZhXdwlLnRSR1/bWaWv4J2FhUnw5m/TRSNQsepnql4tu1c7rh2T4QceNZtLKYptX5CV1D75yKuhmeD'
        b'XEM7IFYqLZk20iA11bk6MKhR7WupMZsBptNstvCyOSYu2Com3esaBWNZTfxIKNeiltZCTdEMej0IdAd8UpvpHnsonZe3ScS04X7QrcAfPVf4AScx3D8FmCByp/nVrBOa'
        b'uMUB8NykVt55GsmWQjhnM/FkiGqozOY6t9lcQ2tBi6cC7crIQD3ovZeuhrQpAqrBT5rspKzU2doFZJvZvAiuOC/BhWCothBQA+NvCp42PfwTYjHviJHgL+IWU/MUu07P'
        b'pJ0zq/316AJhoTq2JWZzAy97s4cz2Z5/Fs4HVYzm6FSxgHlQy7qDAtUieYeKBKCL5jdAM93+4W/X7Q2hOuB53a7w0wBuSre9vhDGdFmIXl/4ZcZa6Z93/JTuxxp0DfOq'
        b'UFBtIWZYwLuddql/pstd2soFEenO85mavszmtRTSdRRkgPbfadfCdrLqkJAtTKQrOIgRXn4D728tl9oqtE0wRkr9sThOBq52qBzMeKsoms2v0yFnjINFNwya9ex2SMQP'
        b'wi9awdNcwNHP+aCrTqfEjZXoDdEZzs6wXqAzkjp2hkRtjE66A9l5P3SjXZ4qs3krrcNDWocgIkdvdN3cKFaFiPYNdj7qrrmsxJ1+Wq5tR8s7QxNQEFWhSnWAqqjdiFEQ'
        b'SMd1bDJb/xB8UUUOdy7wThvdXWQT2/CAdUNXe2bM5noPIOEeXl68CGdxkdohAcvwUkgA6jvurldYiYdCIUFnWO2QYFxwn8R0Roc+gV7qE3qWpLUhRhc9EgEk0Omxifal'
        b'ZvNROjHaaG84iAgrYwOVDWT78vXtHahv786jSmlY2vMrrAVmWedwOFlV3qCd+i7t1J6Berbd/fIVTQhUNCFkRbmhz62nmoXoMZsvBaoYhGKOjnNfEVy7dnJpj+DauWn9'
        b'6HI11KTtfAG/ml8tyLUUNtD6CtJZjZ9G+FTQIwAWJG9GNb+FgkmnX8GgpNOnXFbrqLNRJ956q71BtHUlYYabzVKZZvMtXiYX4UyRieGpaqN4trJHoMX+nF1LlVSWkzhN'
        b'BOt6GYv9kkMobsMini00mx/RLj7fvovZjReBFt4GbeHzoDU6XGbzkxDQ2I2uocUxaG4JEhdEvNna5ZF2Y9EVbFCOzGbsl1Zi27GtqlDQu+LhdKHWeacbSPYGEES+FiBX'
        b'bXDYjZeSFbqGE8YmqhUK/HoAUkzwHKa3nJtQCKtoYJ7QDU90ZixGTo0bNE7mzMGJgqigbCMRqrGazgiqxfHN/Glpjsgzgw23sujXtNCng9gSrr1hoa7RsUxaBB6RLjlD'
        b'eBobHTSczlM+3eTjRsBM2eofLp9micfa4LavtAVPIp8aSlpod4M+a1ve6FfdurQZQD8w4Gbzt/ySr4YF96QvlAvqETlTK+M2tFv0aR3c/px1cnmuOoebBuxqpumo9pZm'
        b'SNfU2Krd9qVSzGcgp3VWl9ss2VF9CrPHWeeksZidx+mhzYEwgJ8+TUBhj2CGS2nBlJnCmeLqPEoPjMq8QQ/n6OFNerhCDzRMqPMaPdykB/pGEOddemBy1Nv08IQe3qEH'
        b'xlYJPdBFN+fX6eGb9EBDgzu/Rw/v08N/0MP36eEH9PBTfx/rY///cUjs4OmxBA7vU4cC6v2gQQpBoVTwCq7tE8PHcXx8F96HSp7rz/HDNVwSx+vCuSiVNkIjwEcRpdCo'
        b'6K9WoRU0SvqNEjSqKCFKQz/aMK0gfRIEtmY6YhG+6yLbSYvkhqiZiE8n8Z7aoV3HUf1xBzdEf+TSGgWLo6phcdRYHFUaTU2Oo8ZipophLK1mcdWULK6aWo6jpmXpSJYO'
        b'Y3HVlCyumlqOoxbD0j1YOoLFVVOyuGpqOY5aHEvHs3Qki6umZHHV1MypUSkmsXQvlqax03qzdB+WjoF0X5bux9I0Vlp/lh7A0jRWmo6lB7J0TxZLTcliqdF0HIulpmSx'
        b'1Gg6HtLDWHo4SydAOpml9SydyCKnKVnkNJpOgrSBpY0s3QvSJpZOY+nekE5n6REs3QfSGSw9kqX7QnoUS49m6X6QHsPSY1lacoCk7ozUAZI6MqJKHXNhRJUDmfMiqhwk'
        b'TmXUN9MXTTe9lLdtJP3wescVIP9+y6BMclC3DtmoEwXz6Ki2NlC6WGWTvdbcdrb+4ve7YMHC/P5s1PVCWuiwtV+SkReC2rtaUIUoaNerhVJhq7RvR3RUe6iYHyi5XWkO'
        b'p79Au1uyiUmP+tdVpmcWlmfJJVi6cLZrl8itkf1GrLoqZsGD4qTlsOBduQYJpL+tskOl22mjHdKuPKuL+W/SyjFvjqVQkrWuTueh0lXdCsp32m33bfdwO35LtVZKcahd'
        b'3VXJUfbn1FAW2As18x7OqfWzQTczXZ7mVgsisDyzdFSwo5IdVeyoZkcNO4axYzgInfQ3gqW07BjJjlGiAMdodh7Djj3YMZYde7JjHDvGs2MCOyayYxI79mLH3uzYhx37'
        b'smM/duzPjgOAeQtmncjBcSC7MqiJPzX4NMpCr6aCoKtYrWxSnII5eppzbRThPBGtVjRo2TXVac65S1QDgx/apKDWwNUK9zBg+IoNvOuoe7ioaVJIRlt3Mr3apNwgcGjJ'
        b'0mZo16KoZpABXW/modcBMpOSwoqcP6TCwWgJ8TtNk+4nAuMO2T7O7OPN5qdK81DXUNfToR0LqbVSH6c2NynJXqr3aUuB69vrZWdElbQiKMX2FMx20ac0e2xuJ40EI21L'
        b'8EVLQcMDm9OcWZQv0RfIOqk24aSLLFJskvlMKmi/rxGkPmnpF0ps9DhBmrUBCCYRqJkR3W31qcz1roUM9GK6109ptkk/bOdfpP8x9qoveKi6li5bsuCyVrfHBWKJ00at'
        b'29Y6Gs6oocYBNWb9aq+xVzOXZJBEJFoRuG2td7c1yBdnrnNUW+va77SnwX1r6WKrC+rH5ioUw36loL++vuYOXQ5SLMxDOa8SzutdvnCopNPtoo7WTKbyqWFc6Jj4ojL9'
        b'IyONhNplc9MbepXkBMDe66davIy+VD0oTsEa9PwgCWw0P6IyXyWixmcN82Ro/9F0utLlh6fHGDnQexSzaURBWsGtTOzQAy8VQ1kKEuz8I0Jde3UmgJ4jOZsmdQQV8Dqd'
        b'VM6cBxoWt+2fNEgRD9wOec8pdfoTgUTba1YA4Q0iiC/hhMo0uOndVbaXv7JPh7WPjUVX2usd7raNriw45wvutmVwc7qD2zcAt31IrM5gaTTQl4Ca3x3UAe1bGxwOqwNY'
        b'OfLmvykS1qAAXH2ISFj/Kujy7kAPDYD+r0ydFJDV5amSt1IwB3MKT/Z3kcMtdVsvJiRJBbH1RCrTNMJjVB5hcWhCBHAy6crartXYbRSgLCBA6ZChzRsmQPtduhS5n1IM'
        b'cGp3s19/uKwUtnKYIsWsSnkJ/KjsrrMMgc4a1TkgSRf4mTltTmYaHGa8RNw0ICGfdVePtEA9JrXbDk/jfdiq2m+M71if6aUzstKyZkwrf8H61Ej1+VN39ckI1KeUjX4Q'
        b'y5Z9pPxO8x2cd0y6LBaYRHJVqltmXeGS94PrGmwLrVTvfqla/rm7Wo4J1DLFj+p+B6SgCsucWZdcNntO5UtQFoD+f91BHx+APpwRd4djMZVkpV3tIOA2NjroliUQiTzS'
        b'PviXCVzg/Et3oCcFQEeXB3agvDgIGSP/2h2IV9pTsHqYs9aFtiA0bKxd4aJOaLqSzNwimON1LzGwrZzz8+6AT2vftW1A6xwL28PUJeeXzsh+Ocz/W3egZwRASw54DaLR'
        b'7TDCTxvj1iXPeDmY0Nyn3cHMCcDsFzLSgi658MUByvjz9+4A5gcADpS8DEEkbKB7NeSpIkW/KKkoLXm5+fKP7oAWBYDGMhrHJGR528lL9eWz7qDMaqMJHSkXlaupZww9'
        b'T55WXJyfWzSzfMbcF6WbchvpvS6hlweg/74j9PbSvkmXDTRipg3q08DkQldA5Q4VRB2I15zc7HIaCt2gmzl7ukFXUppbmFlUXJ5p0NE25M+YpzcwT5tsijK1cpldlZZV'
        b'XAgzSCouO7Mwt2CedF5WMS04WV6aWVSWOb08t5jlBQjMDLDM7qLOpo11VhpmSorG8TKEh+uuCysDXTgoiKhLqpGEmFY2Ga0u6MWXGbh/doc2rwagjuk4cJIGZ9Jltm0X'
        b'yy3KLoYhyCqaSSk9RaWXqskX3dXEEqhJYjnj9pLaCEMoUtxxvOBckRfnld11dXUbjZcjpbD9hxIgW5v5J1gXeRkaxHcHvKY90WsjdtT7WkdtViGYit8jhC1/zJYBuoYz'
        b'dzUtWw5kflCNUfRc2qFKlzvgq9gARzPNr2TubWxvrJkdT6ngqD4NWNlGZ55OLJU8lKnlKiDjSCJXmw0ttEhm0mucf6DNrKeHDsGZmQ2CBhdw0kBfej4ognOHFaII+io0'
        b'uUi7IC8wqvgk9hYjquOquJV9OiqcQc90PVLUiiZy8iJ5uQQy1DDRZQmXIK+4gSbdSb0N+LR0uWMxSR4jp5ou455GdNl2Yds6HLRfzdE3LVGjREg3NY1ssDAvFeSaSzG0'
        b'QlVGyth1u+OCKiPFzhX9rmLM1OWvjVLSQ7rwmquzNZjNq4JrE9rIwPIV6QeHWqZixg+2sOSL6mC4eiWAOW1I0+DHF19ke7uVSjZbqWXOzd6N61PJJiulZLFSMIOVgtqr'
        b'WCAQn7adsUol26oUzO4U1cEqFRFslFLJ1ixNmzFLMiRFtTdWOQ2cjD7ONHo2gpM78YUCqTn/Fw4/pJahHyFpOSk2gs94yZAW6i6uK/61EBld/qpeLJ9WoQnXCFole6VE'
        b'DnmjPmJpZKNWn0e2pxYVmEYh6kROdgoopVaJr+Prq0IGUKR/bI9/29qVyG9E7K1/gqgIvPVPKZ+r2BsApXO1qBY1kFfj5Ws46W1/lWFS4IzKcBamlqcBNOBqBMsRLcbA'
        b'udYrwHkPMRbOI8WejJXH+Xp2QPoCO+jqiqDKKoJJAYsOxDEiDGTazNGVaDO/kIYNEMQAd1QwzcAXFngrL5zWO0RrHX0V26CO1kwK0Ry8auLyu3KM49hSrb8Qjb+MjjSO'
        b'rvBuFGT2JdkSw7mVfUPAebld6mz1v093DHBrwGwYEtqXeO+aM6s7eNv88F6Ghc/orsTtXZYYGHTqE+H3+2gLmm6ipWZ3WTTc2EGLvt5l53RJ67tz+oDmtMFsz2wZhdod'
        b'gNmRrcowGUX/97DVfRSWkeu6fTJj7ei7H3Cpoe+K8vtIucLcAFj2xmceXIsFV284Z/5Q7JyeKRYLzv5upbRABmnVKTV14uPYBin2gvKnxmDBt55u5a9qi48wvENNh7fP'
        b'Ljps0oZ1yeufhW3x74hjXALEohNInprSS9xn0rMcemBOJXR0gKU1NoK67Xf3jwgCwbJ24Y0lWEXxoF9KCpd3lIQzT5JOzJl1MeTvGnvCZezZEHD7bBvNDpiTDg+eEmSP'
        b'T5BLeoUCFlog6+AfJVHxJpSFNkizpZa+HbCj+BtwxKTbECj1fFVF919QeWY3v4T59UislneOoj27Rjqn88HHuTviYjQczvprH4dWGkPV3u1wW+uAINH1J9cUOKF03lHf'
        b'OKXLXvEp2TNvUCz/gM6okL3C8hTpozpKSG1eNwxV2rCkTZhgskUhJ/e/szggYDxv1Wk65FwvyN2nQcCLVSwcK68VNEKUoA2LETx0sbCKXCmOWEpukbeD+LPEneHiFgOQ'
        b'sCxyRV1AtpIHnZh0gvzr2s61Y9IwwOwjHFNWCtSxhLqV0Ff0ieGUBcMZsF7Kco9FVtIX8iqBGUtMV8l2vvbwxnp71SilGFXA1tVivJggv8BXLSbScxqPijmeqMXeLN2H'
        b'pcMh3Zel+7F0BKT7s/QAltZCWsfSA1k6EtKDWHowS0dBeghLD2XpaKiNBmpHY1ZpKmPg7jg7ssVsQGe5HVxlDNyNhbs0kpWmsge0g2PRrDSVsexcimbVM8wkjpcjcNG4'
        b'H22vMozyRntjWGt7euO88d4Eb6I3qSZeTBPTN4ZVxu1T70sQR7Rw4gQKB3pEEEeKo1gUsHj62j9xtHQPINEIWPR6gpjBZvJEn5Ziot8dwseV+LhivdLHz5zm43Nn+PgZ'
        b'ZfBb7uOn5/iErPx8nzBzWolPyC2Ds5xSOEzPyfYJRcVwVlJQ5BNKi+FQNoPeqMx3LmeUaGZuiT7Sx2flO8soQeNzocicUh9fkOvji4p9fEmBjy+F37IZzjksw/RKyFAB'
        b'dchtN9v9wc2Zs4P8JgEplpYiENpc8UKhzUO+ZrRzKG5FkYeu4eHrPfG1iAl1IJm6yZZiE2kppEFE2+KGsqCdply2e7DAkFs4KwcmRB7dfElfOTqFvB6Nb7vwW3Z+UprC'
        b'RaNpHEvZ8YnlN5ZkW/Ivkq051rqauiqDdcE7P/jK7V0jDq2/JXyiRAvfUyvjkF5g8Qsmz5gTgVsNOWzzIn7UlMajHuSBgK8U4QNSyIZj48ibZFvxDHKUbAXIdP//UX45'
        b'PpjN9jfOzxzf/nXHEQnOcJ54J5K3XoxKDJWJLaPM/l2M8l7GSSxsf1wwGrV/hbCybW3cSV+pG/rtqMDgWI5hgWwByHcFf9jo9cGf2K+F2K4Ysh7VmqBxpoDbRx3WBL2j'
        b'm045KehOW9RhTXMYoFUYoJWGoVUYQyXNmrCyoPNQb+um7er8Ar2+RSx6LG6Zgx/l+8MEAhIZjSYagpaFcKWjXVGyDG/MwReXEpCOyI7GCLLLzHmok+t8fAGfb3sU0K3Y'
        b'OFveQ51HWoAs78yfk0y2zDHiMxpAWwXC9wGFI8lb5C22mfuwTk37IGZqz2qDdaYSsRgn/AyebeXmSDM+yPZyJ+LHLPuPrWEoBqH0mIwl2ouoCnnoXs+8JLyvLYhLj0Ya'
        b'X77dzm41mlemXjGfnPdQHFxdRs7l5xbmG+g7JY6SexyKKOLJebrz1jMQ0UCp64XUHLr/m+wdmZ6ON1rITnwzHw3CdwT8GHsjWEx7coycK0wtoruBWwpZuPg5UruTTcZk'
        b'0pyWQkPtOvTkkVVDbuFmfE16/+yJIrwnn2zLLUhTIQBwTJXIR2Xikww/WY7R+ElWKu10o4rGVT+mwg/4MWPxYc9U2jFkP3k9VRqSUBBnJbMI6yXJUr3wphwN2SOg/nhT'
        b'JL6Hd1RIcfWvmsh511JyU4E4gezGhxHZaUxjcfXxm1X24FcpNi6NJxfIzfJkGMptBkNhhRRxX9o93xZXkpwVtGSnboxHR8t4UEWO+uPJk60FRnKVPFChnjMFQkNSbmCv'
        b'HWkkp0f5O++1yRUlxrYI/kGtoXB4vJVH+A5+EjG6xuih+Js7hqwje2eRXYWQWIkK8ckiD6XE+O1FYSAB3Fi2lNzGW5aRm+7BVSoU2YfHh/F2st8zEvJU9Z3mghuz6TsD'
        b'kvOMgAJAHhmc0uTAWBpjl6kQ3kveCgdkj2MxjiP1+HEq7QQa6TiN7CxLTgYK2JxWJPeIhGV4HW4dit8OgxnlYnYEsqkHWRdB7pLbLnJvCd6N7+KWZU7tEgJSUuJIAW9U'
        b'TGNxf2bScP7b6FtNjCbo13h8UYli8X4BX8Wb8SWG+YkLFDSQks4y02HoucqAPJQA4vsZ5P9j7z3gorrSN+B77wxDGZqIiB07Qy82FCugdJRmRUEBRRGEoViiAqI0KSIK'
        b'KBaaCihKtyDE903vu5umySZm0zaJm2aqKX7nnDtDkUFNdvf/fb/vtzHiMPfec8499a3Pk6VMgC66RWEhJWkJjqmPni9Vrib71qnbESHLvOIER+Okd2Sukszd5bGTnq1I'
        b'DJhXtKtmzZXW5rTMKscX+HKfpTWf8FfecU0z+kgZY5T3VO2d9ob6F7daDS1a4XX8JS3Q60p/0s24fXqpZd6qd4ZMHvrx9Bs1mcIbhS9JP7d465hVzfK02rrm1Jrd5ck/'
        b'nrc+/GXeoi13hsa8HlQ+/9ISLevyn55wbzFtmp2clDHm5d/fla7IkPwCcbrlJ45LLjo+vbnIx6tu5sLzQd5jwm2Hrit6tWz12ZKXGlyTftQ9qfXc8Hentsm74kfvPvbu'
        b'Qpcj909GLr1z98VOsxGxv9QH8YZxbyd86/PRqE/eunPA5e9udoE/H32985Vbtqd+9PzXsN8WfbMkZK/Z4dlP1QwZGuQU94qpWYPkGbNPx0U2xSl/iHx3/Mkbl1c77NT6'
        b'IXXnewbbZ++rfrWoal61yYcuXs/IRzutLV7f+Y/7b3/TOH9CwXsT3nvqrW+Dm43bOixPenz7u9Hkrv3fvZ6mmMBoJaEIT0JV74loPx7T1SciXIWT7MzDDL1osnpEfibL'
        b'URS+4KKAtXgKLjD0ZLK7FHJ9kZmhCvNVuADJKQw4YObcPZCXamigl4htSmxPMpBxpgkS3D8nCM+OTaKLYlo8VohQPDyeT+EX4uEghtscAKc3i8QMUshREzt5QgU7zaF+'
        b'O4qkmQcVmO0ZNom2rVHAaj2sE7EXroXOgDyjFGzfhm3JBkbYLuPkw4VNWOnKwA4WQsMTKmgJsqNnMb5MD7jECnfW39GX9WExlHKM9oHI5eUMEhuadpONws5PxgnQCuk7'
        b'eFd/XkRtOL4Iq8lSyyU7wsGwrRJO6sJD0wpoEumozmKmpYqOKgZK1/L2vlibxPhRzwcGKFP0E5Kxwwhy4aCRjoEeXjJKIWsO21MTDLgVMs5PKiMnUCOeFlGtTyQmWNti'
        b'vi9RXezhsGwl6TyoAxEbYySUUVHGEy7Qjbcc8nfzi+HcKhWM0dYVlLIiD857+gE55ewohPlIaJNiJl5MhUOkAja23XhexrgtKGlRni+0QD0RehYIeBQzV7BbfKEghnF+'
        b'qlc/1o3W4sx8pQbYDldFfo0LuA/PQJ49nWhaXJKHLFyY4A0HVNMLizaSa6rta+QGLU4eQA4KyLRNoiLMPLxI9n6RISyACIKtBlhIKiICoowbh7VScjqdwCMi5tNJzFjZ'
        b'h0yMvP4pFTXnPDM2ZvI1uqQq2mNkpk2ReQnDJyxiK2HUxCcYtretnb9vAONX5bmRWCHFVuxK0MJzTDi0grIppDPUB4cshecMgyR+cGgjq34vttlRqg9bIkX4YBuS+Son'
        b'uz+ehQYsZTAh0dhA+irA28YLC6aTA1FnlrDeIoqNiCHZ+NWXIDtArMHL1h4LBM7KUgvT50oZUJYzGZIGcqO/DeTYw2kD1T6uRfqiQ0sLrsE+cWXXakMla4xKkMBGmZTs'
        b'yY0SMuY12J1EBScdR9xHl0c/cRxyoNBe4T11el/N1JocKPkT9eCUOTSKuCKVi6I0Pwp1mO2rkMNZGefLaUOzdQrDF3Mls/G6OMyQEyASumFlooyotBLsngN1mkXn/xSu'
        b'OlP9meC9bYDgrbdQh1GmSgVzhiQqFcx4c15fkPIqBZ435o3JdT3yPU1q1blP1HlynV4zkcgEmdAbYCq6z3p/oz9N+J3DHhCm+3Ct1umpspvUEcdSahNLpH2WuJBqcfIN'
        b'EUk9wcMy5YZNUVujHh+xpE4nMZ5XFZXIaBLZo6z4RPorM2pv4/v20zXNasKEJzWoCZrf7I8Qj2qvU73ToOCmPfbs/pX9IUM2S85LepjR+fcev7ElIxhRp0aIrbNQQYj0'
        b'g4v/Y/Gz5F3l61TxTuseQmHDS9UNsdEUIRWj7G3bnyXTZF7kweqX9tQ/NpiFRtHAqH+LXlZBR3lDclJ8dPSgtWr31MrYTMndtuR2Cxqs3xukRVvCgp3/cDOYrdXyYeOv'
        b'19MAKxa0EBOtilLYSmNDSK9HxdEsk8g/XrcYHnZLf12flTxoMwx6msFCqGjAxEYKrNYTbfhnak8seNiAG/dUOXVw9OD+Ffepl22r/UlTRW+fqPNzNO9lN090fo7p/DzT'
        b'87k9fFCfzyLTkP+AYjWxug1O2DqN1R3N/0G6VspxREkiNALG9mP66R+OobRQbopPjo1kzK1RiQza2yJiYwQN4tBYVg9dkltsVAQNbrJwZ0ktdHhVSLQsNlCF0q0KC4rR'
        b'jGSrAvAODw9OTI4KDxd5ZR9crRRtXuXXZyh9GksSg8V29I3B6odFHh6+OCJWSeugAafkCzFGSnOz4umq2UATNyItqCk/IilmfQz1j9pZhGyjD6fMtJtlt5211WpLfFxS'
        b'/AbKi2ulsbBtpCS69aVGKPuhFatzgyj48EDQPvrfAKMkP2AmSfxjFqf8LlFSofz49bovwp9brxN9+yWOe9tZJ5fvaJ+h4JlkpoOnIbtXcrkG1aL0ohJdiAjVJprn+Add'
        b'R9LojVEMs+wuzYrvL3Rwe2UTd07qd54pN8SuY53R6xGhBYgFUopZ0RfSyy27j7yUqVSFadL/rObS9T8ZeFon0+QlmYOxvL/choes+4llR7FiIrQQyS8ngKpW0I6HfZhy'
        b'hpeww8AhDtIGB9SkfhbRnBwt+YO0tAOsfupdYMC4OW6fIiipyH10ZMIXImtr+MGNnhE6b30dfdtXm5vQITmTf4qMnwXdDyOgCfJ2r+sneqoHrxEaxcF7SCa5NFr5kGE0'
        b'nPIYw6hUDWOdtA/MvUbrrRrSak/PKO8nozxusFE2fkfDKFOpRB8Lkx81zFBBJvYD42ztT8e5aZSBK5yEMoXA7DSbtCDDJ3UjmwNSIx7OboerzBa3lyh253zGWbOnpM48'
        b'0Q+vQ23M/nc+FFmhozrmfRi5aaPnBt8I34jNH5zTan5nxN/KAsuCVqS5PjPywKXQkc+Yvunie0O/wpZrnqjz67gRahdjX8g9jen9Pd3MpHqqZgr8g2OjP8JQrifsNNM8'
        b'PuKICJrHoc8RmUMGYOhgA2D4qQaheJAK/ztU44+5ZlYkG/FKap44Hf0bXTMvrd8Urc9Wy/e6Q78R0OJXsl5oOyJx/67BtMIHdMJFU0StMASODRi3B2Ig2ChpWj961gNc'
        b'DSwconfbG4RZm5Y6adBhefMxXBoDwy7+E+LEJk1DMvD4kfoHxwzLe1OqpF//yzbIJ0KfnT5SbWMFb5Xb3CuoDThYmJN60A1JajdAKRNjPgY/SGh5Uwc9SP72GGqfhnDN'
        b'/0RfajwSBgqFZHpH252WsCNha66PdQSln1/zZGtRZfl2zpFxzk8ykxq9MV8hETFXO/GUD+bZeFHDXyfUUTb7tjD9JGrax1ZnrH74/N+KxQ+YRSQ8MxDthULstPaxgCZq'
        b'DbWVEdnhmgCHsMVrkIG0f9jKMHQcqF2z4KTBB5KWZzXoQL72OPq7WAPt4wHOvtHqjt/MMWcf9avrM5ef2rMuZA1hzr9+/vUsrawRzBE4MmtU1ujo0T3OQPljOQMHrCcD'
        b'rg/JR88ccPVn9ASTiDyWQT1U07CGOqmog0oKaaKDyoL8WO5gIU/ENmwzSqCG1eYkGZZiGWcMNQJexVP6jOTyib14nDlaPPGgFZ5XBMD5hzlcZBwe2C6HNmyPUchER1kh'
        b'XsAmJbZzUArlZFYVcXAQ6nh2EVugeAq2JMvwFBSSX09xZI7sw+PsrF2LZ4fIsV1LQtqBbRxU7sHrot8ryxcalEk8VM2gtMYcHIBKLBf9KFVQOU+ulCJlRsOLHJS5BDNf'
        b'0541vspUQQdqKBIwB7lYOZN5Y6QxMk6fM7Yzsgj3fX57FMdoKUfgNTxGPVBSzIYm8kQ1B0eJnNDKnJojjbCAvg+H+1Wvgy0Lk+kkxMPzbFlnqToodIe6i/BSUiK2Bnla'
        b'U1s46ycogjLd3VCVygYLO+YmOGORs4MUu/Agx5OewLTdi5OpLjoZT+LlfrScagSWZUuX4xFn7yBsmafNhWCZjIxm2bRkuoQsoGu4MyWlxEucI+cIHcbs6zXQjefxsIT0'
        b'4SrOnrPXWh770/3790ct0CIT6bKT0YLw2LaEbRwTj/E61kCtT09lmO1pMwzaqIMv3947xBJzSEOCLBVYuNzTi4pRB/2Y7BRIX08WZxBmBweYsxNL3ebSsAb1bdgdT++k'
        b'U4qKXPYBqk7q6+ylM6kBruljc9y05HA6z7He1oDcfghL4IQBpDnoaGFaCJ6UYUGwwWKTkTqugXANrpO+uuixcbtu9PAEPeyUpepArm6APlwis6rGAa/vUozD7Dl2eEwG'
        b'pW4KaJk3DcvNoQzSPJID6SxZGaGF6ZhuwOFxe0cdCVwKgeZVeEQGOZgFR6wgk3RKIRQEj4rZA+cwbRRc3zxhFHSQGb0f2qN3YabE0ZI0IX8cNrkP9duDF9j+wWbarFGj'
        b'+GnC5XB94/DdPxrM4pj7FMvMoILRvY4wXorZfeleex2TfRhfG7FDvmFrPCtw1U5KILsgWRIe7v3D6GVc8lJa4BVvqKbvUK67DtM4C33yOXTtFiiG82RRV/KOkIG1c5zJ'
        b'cBwOJ8v0PB4LmYrVq0ib04YFQ0YUZG/E03hZexN0Gu/AEkMWVzAF6heqOWn7NtHT1lvLZBiNSYE6Bfmf08JWsrQadLEDGqcHK3jRj3x8DKmcjD85OLDAy4ZsFrYyrBzL'
        b'DdeROkyCgmQah+aDbZDtQ8lrV494GH1tH+7aXIV+TNLmZHqgYlei3WN4dQ/BKerZ1SUrF5tI69jKO0cW+lGqD6RANc8JUMC72ZNGUWALByyH/daecN51BZ3cbA3Ye3vZ'
        b'BorBFAOc9mwWb6MbwNJA21CBg7wRRliLZ72TqYcbG5ZDmjwF25dBQ4CnqHqEWpIWF9hYevpBUyAtb/k2cbMlb5Hvw0Oxhx6NNCjYowf1ZLuZhV0G5CX3QyWbAdeHS4jO'
        b'qWNuxIXbNAbbk2OVceW4YjVe87Gz5ci0zwnwkZC1c0mAbCNIY1MECidNDgpQ+Ikg7iHLe8JEAqGoN1KEQq7XQxoZ3GI8uMYCGuAy1HiOh27P8c5wUcphM6abQDnWbmI+'
        b'ezwcOYZ0ZIsRnEzQ1cFmI2xJSkjmOVOlhGhZ7mJXH4ITJkF0x5JwzmSPO8+R+VebmEwtb3AMz0CHj8KWdEKOrz9pl+UDIYFnTCVcmIUOZJBbK9np4QnnlgZBfnBiNOZT'
        b'eh4tK55cy7Znu/T8DVApTzGEQmeeVHWU7ib7V7AzAve5Yw3m+fILMZPjZ3FYsNed9dtaOKKnDoGZhseteU6+SsDGoZDLLk+DxqGiB5Y6hatULliiOJ5nJ8woKwPqzISS'
        b'CBknrOXtR0CteMZdIs2vFoMCtPB8ACcdS06u7WtYCAueXBOqDrEYieehXsrpG0uGYRYWs7gDJZmv16xpfAvphFBtP4pdL3oYtciqTNOKXhkh0iN1x0IJ26qdZqmwubBM'
        b'gCOO0eIhXLAT91mLa2IFVPtrcfobJUYuI8RhaVoCbQyyPxzqVWzBRbiPXds1CVoxz9YfGrCOuQJlYcKwJTqsh5cu9sY86i4VoIOTzuChDnM3sx5eBtWz6VqWeBmxt632'
        b'h2yxHSVbyWlJOaoleCxBZIqGGkxj4Tp4BNISSCMNsYKtXTI/6eLV4sbDYS1dGday03AxnNhIlgBT1IGeUDn2qu7p1zn+kK5N3iLfm9UrTHGk0XRXsMxGQU4WXRcBasm4'
        b'nGd9RzarStLhLTS2o0V7Vxgn4AXeFquwPuaXEy8LyueJxBTi87FH0Itxf1tgemLE/PVzUm6d8av4buH7H/9mVSgIdXNmnA9PL7raGQyHql6oy12wwcy85rhHg3cYP2r1'
        b'P+a8Leyad3rca9O3vDKrbmnNLteNr8z98ZUTuqkmyzyLa7yP6LYPnf72FJ88yaH2H2ybrxx+e+uhFwuLK3zXfzzJTjdxfkPjc6bf3V9+NPTW5ys/m/GOxwXTz860t2a+'
        b'2h4a/EXdd4fan/vixriurvbFjXcunbYonXtonmTdxo0vpd706lxjNm9/7Uuxua0GF33f8ViwTFGXnms4s+2wT+KulFtuP2S2vxo2dNbkiCMfmB76xtPZcsrLr6xwftrx'
        b'1W+/a3wh5F7+8dHL/UN3Sv8eXJudGvyJ4YbGmJml+y7ePn7gq7duTv/8uzmrVzxb7vM3vHxx02xl22r3WsuRtc9diu86tHqm9+3n9spO/J4W0PBt/Mh1m/f9omXXeNlh'
        b'7v4Zo+/ufTJ1sWvFos//eqdyUeHZ259azfN+ddatU7OKPhtxeUfBM2e/mHT4Wafrrlfz/rK8qvlY45gXF354/dmhT5dcmftS+w+B30lW35lZ+PE1T727uybf+/aCw62k'
        b'8qnFMWH73te3HW0VaV/5ilbYqDc+2+Ua1LrpL9vbPBS1t7mVx8vinjzs8t1nQ+PM4+Lzjt7+65mP3abr31tY+8/Q3LPvRnemf5B91/pLF22Pg7onreeiYcoPc1oDT8Qb'
        b'rg0LOuK2vftMyCrn+KwNL73+suu/Ivb+8GTFr9xvjYUbnbK+195X/n78wblXs+9e+cjMyu61xQrlnLsNd9feKffvKnpOSDnnOPGA//uLX5Y/P8H8+Tcbn5j4z+If/CdF'
        b'dGUv913yZEP0rSe3PDn5dvJtp69l27S2Hx7z1Opb++8H5L/VnOe9qzvd5NethsYz/4JWXxf8MOSrxOztAcdP/DJ6fFzI/cUf/pA29uRzE8vfuHF+WOAvl99YusFuX/f5'
        b'1sLP2hJfdHj6aqOyITjwn69taru/osxl2Khbzqlnv7DPvP/ZuMAro5f4rlNMZTEdEizY2hvNgK2evupghqZtLD7AezQc8gmwhRxvkRSKiD9n2IXw4dhC97kIrBL3uQRo'
        b'Z+EPI8Owrh8t+WisU3FiZGAm0wpnk829nJneykiVRGMgUie0CSlrRosBENfxkES9AY/DCvUGjNVJTFmNwXZz1Qa8EU+o9l9dOQs5MCO6ywF1cA5kY5mnOjxnDmawkAM3'
        b'cmyeppLEFI5RemwWxupABYtTSXAdY21lRwSUSgXm2nCc7kqyP8BJrGStngldUG1tR1SBihGYY0P2QCgQbKGevDfbPrJ2B5DDFpvdetlXQiWxPFxhURvk3EkjheWxoLhs'
        b'qIbCgF5hWcaN85HiyVWuLDpk2nQiiNgpjEjzaStkcF5wJgp0p6ip7w+F69a2lnO2Mv4XGqBDjsKCJBrCSNpycKES8nWgGToSDLBZSQPnHoyakXF+2CaDLnu4zlhT4Krf'
        b'ZjyrGpBec7CJlwROQ9cuFdv7Pixm8yAAc6F4i6+Mky8TsCCOdCqNftgKNQFk5yTSClH03aDTlgmIVFTy8ktQ8aL4QIM2XDLZLoZjNExNSsUTPmJtNJCFxv8MwSwJORjy'
        b'8SwbzKHbMJ0yvuVCM56wt2WMgtqcUYBkkx+WsMnmCkeNrANsiDZF9CIshYvkuhy7BOzAVtzPBpWH+nA6LpVEUO8jBa2ZwTjP3Nxd2JG3dot44u1azPoE24mIfQrbAvqE'
        b'gqnjwBZikxhrdDyIBp7Y28Jl0js0gIaGzwSuYR0Cp7z9HxIOAoeNFapwEF8jFsbiDycgU4xAuuAwIAgpNRkOMb63MPJelzSExQiUCEiMi3GOZUMmx4pRZBYpNntb9/DS'
        b'pUnisRHyxVCwc2HBRJinXHA2cFxKzld5HCWDq8Zatk6IyoVpqjO6JV48oyfMYHMweM5ctRxzAspEQWY0kVdZyNEV0s8n1bKMB1FvVbIMkRH3sZUgh5oQtSgDV7F0oDBD'
        b'BrNDLKxg1h7Sxj4xSNi8jKzxA1ITr+XMOLXVjMZCkX6Gjscwz4q2KQVZLsOYwLMXK318vUiH1pLdLZC3gnN2bGhHkeVW42NjuQRP9OG8sxuqMPi3sVwVo/+LOLH/RjzQ'
        b'LaMHUDFFKxy1Xz5ohZsuE3QYr4sxoxSS8cJ9mvwlRgBReDlDFidkRimHyDcC+SO9ryOhueTkTgmlJ6KcMCIZkfhX/J0+S8swYRBzAoMmlpJnZIIJuUu4bywxkZipntFj'
        b'/5oIFP1bXxDjlQzF3yQsJkkQqG3vvlQQfpdKhN9kUuFXmZbwi0wm3JNpCz/LdISfpLrCj6Z6Qprwg1QufC/TF76TGgh3pYbCt1Ij4RupsfC1zhDhK6mJ9Et9M5kqzU2f'
        b'Uez1sxE+0HGiZVMMYhJDjVh22HT6w4XFL0Vt74166E256vW6DPs/G3+FTp8WLlG3MDG/p1HTeyKimDmVZlnZDmZOXfSyJjbCh3WVgmd5Z/6De09ZMg71n/IMK/iP+U8p'
        b'VfFNQUMcw8LoJMo4GBEbyxBR+7D6kgbG0JZFxPYDShVBtiIjRW97hEVcVOqAQsXYGMvw8KVbk7ziosPDLdbHxm/YorBTgdqqIyOSlVHRybE0PGFHfLJFaoRIgxgZQ5kL'
        b'BzIO921ETBy7MZrl/qtSPaOUYv6niGxoQTGaLGIilY9PMkghC2ZbeLH4BjIjlTEUOJbUQ2MdIiw2JCuT4reKxfa8mldkeLiCQtwMGtRB+kfdH/RjTByNcqCk1otIN6bS'
        b'zkzaFJHU09reuBGNJarejaHZsvAnikvDCqDYtv26SJ1JuzExPnkbg74bJI4iMSlmQ3JsRKIYf6JioheRGJQWljST3YZ0AamWAaXs2EZ+jUraYKdggzBI/Ant0KQo9bio'
        b'xp1Fp8U9yCapGv3IeJbHu43iIGsqs98APIKNkec0sTHq+Yu28qtYHa7KU9FSMCcAZg3rdQLg+TGjevMa+uY07FwDma7OyRT8MWS3o8osaqEjoVbXqwkOWAJnd40c6zl0'
        b'csJuvBgI++GCG5SsXuSVBA1E5rqkM9ffZgxWYCVWuMO1cTuh3tjBE4qY3WrMOGq55BwcopYtrNoi55KphDPWEzqYPSGI8ukW0pQYmnSkDe1wgZuwWUplrgj2+PL5YgaF'
        b'w4xxgsx7FxfzRXUHp0yhUtLWiZNfmGO4z8HY4y8zN9z9l9fzQtG5FmOzBXfdP5h2aGHdIsnLkcN/8N/nnpqc5CcpXnpuZepru79ZeMdv3zNxyu+W/6zt7/LUpR8+CTw0'
        b'5IXgqF/Ds/eF7dHLKy3E0JbOV3/0LHslv27JppWFX8ytLFu9flHLr/yqtJGvrdmhkDOdanrIUCKgQTFcVweJq3QqqDNkqpMDHIFaNc0uHvVdiGXuzNG8fTlWDOJoM4jQ'
        b'LMvEEGGUCqxzd8FFJTUQ21qqgS2ewBNDsEgCl/CIm5jKlwtH8Ko6S0fUufzMU4g0JVI2ZqQuU8XOT1zLsdB5PLZaDNHPHeqrDpzfzWOVxWIZHmYPrYcKTBMzBqb7i+qI'
        b'A9F4GDniPpfUfoogHDYRFcG10CpSLB93UYoib633QJHXhlRBjxm4ojfvQYkXy3Wp0CsKvLbQpXIkPirb8JYuTdpj65OJNzTZ7EHxhgg4CxnDryBl4oOhhIU606Dl/lEM'
        b'PUWpEx170DD6HOUDOB4F8Y7eI7WQ/HpeqqIlevBI5dJNNB2qgzSERpWS02UdOV76wRmo01t745HE5FZJT3Kr5LGSW2lc4E9SDedpUFScCue0P4h6slI8X6PYDke2Y49F'
        b'Xm5BfYDRBzuUotbHbFCu2xAbQ0oR2W/VyFDRFOlxwyY7doedB/3pxm4bDG+9T6mqvpnNYhhteoIYKS6wMoo1Mz4xkn5BtnuN27EKP37QNtgtDvENZ9hwydti4yMi1W+v'
        b'7hDNAYKJfeIM6UmhCu5VJsckiSjuPY3SfEg8slVubsHhNn/20ZA//ajX0j/76MIVq/50re7uf/7RRX/20RUeTn/+Uedwi0FEqcd4eFq45nhPr2iRVUYUbKIibSysVNPf'
        b'ql8kq4ZgWc2SyCABtBaLEyMYxPajYmU1N3M5lV3FXSHF2c6h32phII0isK24nEiFKTERf66nFgWHaGhCLzs23WPEdojLLUZDHO2ADGytAeLWUJH8+p1Y2chuiTlN79SP'
        b'2ujMMRksAKsgXSkXlEjjH05zUE5OvmoWaQBteAguYgt04QEHBwctTvDi8GQCpDM/yg6shSPW/nY8NLtxAhzlfdYZiS6bI9jlbO3vLWArnCVXMniarF/G3DKYgVlya38v'
        b'Hg7gPnItm3dds1ghZS0xhqot2DInDluMsFmLk4zk55pAFfOCzMH6KUiDFovwUhJ2sBRlfjzkYh4LHIDiGauUTonCTCOOj+egY5cra4gOFocrV+AZbDcip5qAZ3grPKdq'
        b'vX8InqKhBpw9R72I9pCOjaJMeg7PedAICg+oVEVQ2OF5hcBcNeNwP5ZhC3ZP69NIuDJX5J8hLaT+2ut6fRvpqmAvvh0u71KOITJCb1vWh7Erm+ACtNPW48FJYvOhfqVC'
        b'wq7pryVj0BIZ26e2ZQ6iX6gaWvAozaqDQ32r26ySrKvgKuyTY31kii6ZBxJd3h5yRHcbdhNx+IScPH7OgOK/SGz4+dAIXazCZI9AUmaWHrbKDXlOos/PN4TrySuoSLBs'
        b'iA+VeYMY/gP1ZBMhmNZT/AQp7yBmQieUYAdkQkUw+aIEO7EGi4mMXQKdJlp4ZL2WAfnhB/vxoKvFUCIomhjBOWjcGSN/sUBL+QGpYXadIuxVny2wwFj76/KbP3k+UWtr'
        b'es/DKvvU6be2v7FohOtTJv/8684EZcywNw9vrMx6eeb34z4c/9za6L1317t+WtJS/O3Ctecm2XvPjwxaYjXKJXf4nO9L8o7lNwXlfz371hvv7TU9+Klr/eXIZ38I+aVy'
        b'3963vlkV/g+X76ys8s++lvoP38k1t0cMG/dy8Bz7o9nr3b/6Xt+vPfL9pSN2Nc6qbjAoCnuy+KhBhPXbp5vWp7wx5Gq3scG/piZWr567P6FBefCVMbF/bda9w/l81X4y'
        b'3Ch19auXnn2m69S0C/YXlAVvflL++0+lH/6mNTsgtOrD1xSmzPaLzZvhdA+agVmYypEQPUWUhy/oG5AVWK/yJagcCaTDr4jJtN1YBLnWPkR4LWCe584REk7fRqKNZ/yY'
        b'VOyA+6CAyvGYD/uYd8QQLzD7oc8KqLe2hStieqcUMnly60VsZI0aS2Z2KeZhy3oxIVaVDrs3jl3dRa4W9Mjo2DRUdI0snSo2OR8K4Jg1dTAQ8RfOLCErL0+A9GXTWYsM'
        b'oGWaUo5t/KJVHI95dIVVb2BXtDFjAeRtmy7IFORKFlltQyBHzEXtiidlkkuy7XiSIjRwSGOvskWq+SY4o6AXeWzQIxdzOCzWhnPM9u7gRBSK3txSMa8UDmOaOxwlXUiX'
        b'vvW8ZGWKIQ8tOzkeznB4HCuHsEpDOUxTwkHIFkgv15CCizhsxQJd9hTmTKCPaVmkkqfOckQn6rBgyoYLVOJpsmHokz45QK41cnhinSAqL/VKvKpMSeDDV5ALZRweJPqi'
        b'mJY8Dy9HkiuCiQ+5cpTD3AjYz3wQ6/AANijhiFd/vUlUmmCf+yAJmA8LjFcSQZhpFpEaNQvjGGr0NBQJu+5Tcyg1olJzpvCbjlRgzBy9fygjMeNuF/T4/n+kRCMRqGH0'
        b'/s4h/SOrSf1qaBSWRKnfV5JOLOqnnLBYSfI6h3sUkqKerMdi8umFwbUS44satJLBmsKz4KfEv9PPwx9AoLolXRfg5X9Lvs4tJDDQw9/NyyNIROzsQaa6Jd8WEROnTomk'
        b'GZq39PrkDDLzZU9uaJ+Ezpz+CFYM0IqaL5nCxd5PbN3I/y9Z4ROXknadlagmkA5nrK0jodBqst8MZaZawgKilt4XhD8HnGkoNTYyFCiLmyCdcV9nrymvM8ZUFZp1EK5J'
        b'5CkGRnZ9LQ88N3KJNAavYPmAiGN91b9KJ74/rxuF3BLhtiqkKsAt8TOF3dIlf+hnfRX4lvh972djCsEVOZR9No0c1vPZLHI4+WzOPo+IHBk5KnJ0hZwyxmXJovnIMZFj'
        b'M3Uo9maJdgkfKS/RL9EpMaF/Isfla+tO0J0Y6ZhFQb1kRN+dFDmZgVRpM7a1qZkcBc6ibHL02RJ5iRAtkCeHkr/GJSYx4m8mpESTEt0SvWgphdYiZU7UtYl0oqBhtNQs'
        b'3SyDLJMs02idSNtIO1a6Lgv5lbEQ4CHRMgampUMxP6XcKjlLQHS+ZUIXixtjn2BgbdFRifec+kmcA29QEab1vemeHRFfZ8co42crkyLZv04ODk5Os6kUPHu7MnI2XTx2'
        b'Dg6O5C+Rr50VkltS/4BAv1tST68lnrekIYFLltbxtwR3D/JTl1a5LsDfd2WdNJEaDG5pMa3zlq4I0xtDPmpFE91Z+UeqdaTVShOP0xVXQX+coGtY6uUfJCI3/sGyXMjW'
        b'1r+sxLOswCD30IX3Fm1KSto2294+NTXVThmz3ZbqA4k0QdZ2gyrF0G5D/Fb7yCj7B1poR7QGByc7Up9C6C2/TmDAYYnRFA6RdJBvgNtC33VETbg3hTbabZEXayH5d2nE'
        b'DrrtBVKTsTKJFGrnMI38JJsfLayOTwwVERUraVv1g7z8l/h6rFu0MNjN8zGLciQ79fF+r3xv5gMPuiXGK5WLmP7Svwzf+I1+yo2sJEdaktBbEmngRVqW0QP9cW/k4C91'
        b'b5jGzlPI+5VCp1tis4ayXRJb6bcPFOLCCnFObKHXBq/c8Z71H3jTW9qRUdERybFJrPvZWP6/l94iqgvl/qNg/zw5EYtU8YhE3GqL+XnpUi2W+FJtFsoSX2J5TmqW78Ev'
        b'Ljj0kMSXWzqUrjWJTGsmdZhplDq4vdKlItBq/+3ETv3s4OkT18h7LCaflJYaxQAuXb9ZgyDwsLrqtMUje5uGczux5/Cm0/Mz2pZg/wFJF3rqrqVZfSzpohdjjeGrRev1'
        b'JFToPS662gcZ2hrsml5i3nHMzqg+1k2RMkh0O9FN+SHWzCA1p6/FNkbgwGQY5eyBN9paPLBwLCzdPRQPv40uvEfe4WJhaaWMoT6slJl2M6weo0hxLVtYunk++mbVmqU3'
        b'21g8qp7B9xMLS6/gP/SE40OeeNytgRbxYKMHMxyrjF+ilUhMKFeRRamJCAZ7kp6f4mMPTpttiTHxiTFJO0TEX0sreipTGi56LltptiVa0dOa3kPPTitqOLaih56Vwq7X'
        b'zTrDzsnOYbbqFs3F9HpkHditqlJ7v57BvhaLHuzFRPAK1atpgKYQ+2eqkqFTDNo9zG0xuz+mAFtkmoEmVJgAg7apF01idg/h7EDACAre0OOU1+Bzp/+Ra4wzkNrymQ2V'
        b'BQRERSTRCaVUM6r1wd+gLulBgAmoHZaUQxEAxPiBPkQWrHcsgqKi6Lsmx/YhadNYlNvCYI8lAYEr11HGoIAgj3WULCaItbLHdy9Sxw3aSeImJPYPI3dSwbmox02tv6ks'
        b'yJpd3b1WZeapEEvoNfpaPbCnWA0aLMBGaJu4TpUi8dwDW4yV+HbqWwaBbFAhcxAJVc2fuykizsIjJHAQ63icRVBqTNLOqMRYNnBJD2m8uCEOspbIgvFKiojdwR4cfIez'
        b'GnzOqiBFxAHpRRqhM181JD2oI6KjapA3ShJjH/pAgvd7Nl4DGsbjeg5I96jEKKV6+j5QruYxUXEx9tbLODDXR8XGx22kJT3Cwk6lEt0BcpSRv2gxr8LSQDzsgwVYJOGw'
        b'ZK6A1bwlnJ3ApKxVbrhPjcopwyaT4YLhTrwohjvQ63OgFDMoJOmqJCKFUUBSmjHIdGEZHIUcucGcFINtcBA7yJ8WyJFyBpgpYB5WT0teSAuZgEd9+qaphQ6G3OmwXJ0W'
        b'qeUtcNNhnyFmwv41CkE04FdshnSackBtwB6x1AqMTZibLPrjZ8FxOTMc43k4To3H66AmmdLa+JkZ+PgaYWkPTGtvU3qyeLYZGARSoFZLW/8QS0vMxYP2mGtD8ThFuFFb'
        b'GXnz0qFEBnVezNoCRViaxGBE9fA0xzMYURNsZ/4M5600PZJbUTs13Peg6V4ueS5tfAmcx5N94UU97bz9MIe8tj222QRitu8yT0kg5NDsPrwCtTsmc9AtlWMZnkmOMf05'
        b'WUtZRYoJfW/G5Jm/5DcZZizQP/DO2G2jHY7/ZPJKQewzN18uuzzt2O0UkykrJk3pjufjNwdkzfi5q33vLqGyIipCR9CbFfn1c8tf/WTOz9ujfko/4x73fPDrF5yaljXe'
        b'xKdD7x7Szr3W9dqElT8dj930yfCJ58Keue7nndk96rObmxfs+L577chxt0tPv/HCN+eSJnguV8T8dnTrvZWr4eaau50r/A87/TW0ftt9ofVju9O2OQoD0RjaDJ2QZW1n'
        b'K0Ze5y6DGsEhegcLZXCAAjzJkJArR1KjLg1Bz6F4yIaBEkeshwxmvk2G+nXMtqtHI4bVYe+k1HpmUYXDMeRWMRwfzi7rGzpSDR0MFhIPjIeL1OacBDnM5Jy8SzRWN8E1'
        b'bPOx84VK237x57ZwRiy72wNKWDgGqTpNHZIhxmOkhLMyPEfDIRagXr22n03XHUscxUiMbuyMVpl8Ry8LoD6K/sCDeMCelTQe0rUoViTUrlXDRYpYkRuxg1m5R61IUVvd'
        b'4QoWqyzvaVjOrMP+eNGDVEPXXiu5IX+dxI9fDCetmDl3OpyAZrLsfXnTcE5YzztaQ3E/eAy9f8sA1wOL5z6ILsXtNZFRM5xMQgNd9ShMHjXQ3dcRpLwYcEqDVw0FqTCS'
        b'hrje16wN9QW8S4zjNZmVlf0g6EIfpoWNrXpcLexPwNFprWP4e4NhZR0ln0QwOk0V9tAy2z2GDPwgkBw1VgV5Lgy8JaWkq7eklH9Voa0pplaMWKUBrLe0VTTdicBryNg3'
        b'Up8nS7mejH1RfdRXKZAGLDPfMMso2ugP5uVTNfKcJjVyYWSksj/RtPoY1WDj6xHABmqj0RazqXg4O7wHQCVcgy/fRiXO9CBw0UjJgYGlD5ImipzBVEvvFVKTaE8mqUT4'
        b'x1KOVGJtD63uo/QjkVVLfFYD922E0iI6Nj6CGg4sGMmrisVysECaiLh+jHEPUuYO1op+SoMmRtukqO2iRJzUQwK7VYzyHCRsk9wTE0nFud6u6OXdE9/BwpKRwdNXY+La'
        b'hMDFdnZ2ExSDCJpiOAQLQY6gs6kPFXRPySLXpSgA917XWF7PM73UlaopoArV6k9kqbEMy0CPxR7Ua+Oxzj/Eb5FHoI2FWi8R2T4HDe9iMceDs77GbxNjsB9SwnZNqt4g'
        b'9KoPKY7+16MJ0h5+mKKmijvuwbvTWJqay1uTTmdBesUj0H+h70D9TXOY8mPqdGryLbEreliQ6YRVzRu6LogaHMWIrsPD/ePj6E7xkPjt7Um9tTOOXNpHEbE0ZppuED1T'
        b'NzoxfivpqsiIQQKtY5NF09nGmJSoOPXMJ0szkob1WG6Ij1PGkO6iJZGOi2Hfkl4etGFiMX0NDoq+r6nihF6/OWpDkrgfaFZxggJmzXBwtBBZasX3oW2wUaGJqt6XWQDo'
        b'2iSbosZyopMT2Vpjq11kmx1UzxNPpdkWQSq9Ss0RT0PRd5BaYmPJ4otIFLUr8WbNe4tSGb8hhg1Cj5a3LTGeUr3TXiRdqxpsshDEaa+5M/swKFr4E30vYtu22JgNLOCQ'
        b'KtxsPfUNrde8dtxUVPO9jK30wLawJD8VNhb02LawDAgJVNDBoMe3heUiD/9B1qFVn1yBGYqBAIgPid5a2LPVP8B+9LCo0H7Kpo5GZXOciKEjM8cKH7juqdYoiToJpzCX'
        b'SUJMP1o3TbZtE8fivWKLp21WgflfxWZvFe9FASf3wwuGrosZRkBY5HwltmMHDapncU97xNAlKHD1pngzOkOkKrSZSZARzNTScTMnyjWopHDMlyhgXXiWQUuMJyI0ZY4R'
        b'iRcoP0ewCj7Bx9Yq1NPGO8TSDk56D8IuIQL3wEWPIUT4rrITFdT6sKmifgrNjmKYEuzH8uTl9NppPLngEbU9WFUvoc0yy9mkVqJBMkQNhYyb7WCKl2D/SFEZraVR4VT7'
        b'NSAdJEZO5WNe8g6ORrm0Y5YPQxyy9Q6g+q8lK0cLi3G/3uQRUKfXq3MuwHSsIBeqTMgn2A81wXA6chnkLNoDxyADGsifavLvgS3boQjOLFq/FnIXJcYsW7Z5beLkNVC+'
        b'ZZMxhwVzR0PFGrguYhfUSSFLju3b9OEApgmcgJ28PbStSabiM5yCZtcBTbMPVzcOc0ZAzgI4tJ50otgqsUn7sQpL6Gca4hVuhFkWHJxfNsQc9o0VsSouTXSQp+gqkyFf'
        b'DDGbg23JdP5iN1zsyZW2VoSqkIW2JSeTplQEY9E2AyMsDlb1fh87ATUP0CFScbv0QPBAOpzTYZFshphthheemMWIRNwSoEiN/6QR/Ik+E2zp4dh3RLENsgyWYBseYkBC'
        b'cIUz9+lLbZQP55eyaUMK9aFf0Ll0WEvpDbkmZIrn4uFAyAsKh1weuxMMlpAJcCLZl770ZTi6ZkBJnr36aGi/AmG/HEpMJ+OZYXAWas2GEZWy3G/IzCVQCxmjmCVjFJZu'
        b'7AvYpHopASuxhNTS6kpGJgMzMXceHBLj7KB4PYdZgfqBYbOSKUFgLDYIfWhzfL0U3rZ2mlhJaKNmEJ2XtMug/4oh/XUi2YSo4K2mbHlBrSFeUENcLPN83MI1lgxHZgd6'
        b'm0JnMh4XJ3E1XIFrKs4YKOemmmAhWQn5LFKHoXBEwRlIf4A1J2+TmjTHAxop82LMzpwXJMoyomiF6Bb4Lbse946D8RTFslbb5wtOnJrh9WzVrh/nLfiRW5svZJ25xA8/'
        b'bWI/1zY5Y83R04UWW8f+Kt2xz3+EU/TXx559bslivrnox9/e/eZLS4mXxwW/I3mLgl8a8v6B1TMPTCt/83U9y/KzNZZXXg+b8Wz9m9+OHXGu3fH86rCpxa8Mq634dZr1'
        b'v7qLL/zt4+zpUfIPu5vGD4/7PN1vZcvKstlHap5f9f0vv2yZYu6zO9T647OxDZ/tr+Y//7Hg9VX338i+V1L9jP2m+aeHHUp+40rky6dDOuJ+nrzTe7v5Sb2TEd+tGGlr'
        b'cl97u/3tjyfde+brvzd9P/P21L+UvnT3c8NN3bu+2jry46/S9QJLb8XfPGD+ffvfY0fd/mv8rAvtz839Z6K8ufS5Dy+9bPLlrk1ZC902ztmemqCd8/7Ty++7zf18p/k9'
        b'7Yrqz4e8m9W4KvzUP+bWp9yen/LExZvVH4b+srEpuX1aUuDG4RvSm2e87P71xGKfgHv/mLUl7F9PNR//V+qOsxd+P/tbpu0rv25Vph8KPPDywrwLuNv83tkAa62Pp/k6'
        b'W3+YdPGlTy/lr7zxpe/3F9dyR8tr3P2+Vpgxw9OcYMxT2SuhA+p6rENeq0TjUFY0NTzNhsKAB3KW8Bp2s0T5obBvuTpnafoTC81BBEWAky5DfeAEFPSSB7EQy6BVYo58'
        b'N1Q4ipYeDwt1hOUkaGK1ephAi8iC4m3XjwclCLrxkAgF0WAoYJ4/VPUYpEQwh1FQJWIX1EMWdPTNMorAqyqr1mZsZE0cBYWh1v6kyJK+iU8pQ/EYs+rNwLw5jIEpTqIO'
        b'1cSrWMeaL+zFbGvcB6fJIvSC81JOFitMwPoxzBTnpXBSsZas5bHD2t4HcsQ2HcN8PNQTGYlH8HCPJU0CR5klbctQsi31UHiQbQuO4Ol+prQd68Us/QK85ueD5WGqDV6d'
        b'TR+A5SK1SlsckLOwwAbqoHKrlJPa8ETsKCJNoSlYu7E7ri9nC5ZDmWiIC8YWMbOrdkKsNZSuVhs1awSHdUuSptIrpSPgsI+vF+Q8kEcv4RzgsowIIrn2M6GcdfF8aDJk'
        b'dktyokRhWwARIwzdJXND8bgIjdFORumYNV7GNhU3C8su08FCFruJ1ydZks7I1LL3s1WQRswVLIhgodB57CRmo/9OLN5BNRZlCRUQNZoC9Zbo84aCsWDI65O/MsGY/NWR'
        b'mPD6xjTEU3ZfTyJl2e06vJCmJ9DPNE9dUH3P8ugFU4kJ+deU/DUWZKp8eJpypq9Fk9BoLjw1NhpS0959fZpbL9BcdHpt5wQNFrc/mI3eazlLfLp/6trj93/fJPKnNWSS'
        b'a0giL9dSp99pMGdy6ZbvaTBoPsbbDh7cM4/a+6idTwwS4aJlPWE+kscN87kXPkCHCIyKI+qr8lHGPGY5UGkrVFeNUFqs8PN9hEoyhPwdO0AlsfFnYIpwBJojffqSRvai'
        b'5cUoGV5e3nLLAQgYWAEXDIbRCGuqVEjwGpT2HPL20eyYV5/xgXiaKSV6sTSyWiUpwCl3DguNdZMpZgk/ChvolSQ7shfYpRDJMyeC4uIJ3KS1WjPxItYybWfBxBQqQpDn'
        b'x67fTAEv03REGf+cxaKxy3t8eMyBZ4CnmEIlSRA46TQKQRAeK1trLXrtlgVCuREWMIBMUjueJOeLwzpWx0bsDmVJJlhkZc/ZYzYcEMOtDsnwtFyXyDU81pEWNXN4YZcV'
        b'S2WxHLHA3thaYUUOBOkOHtPjo9gTcUmJPvQ88dfizKBKZiboQz6cZg12hyIsDkIiglMCuzOUn60wCLPYNSPMnzJ+hgrVTsS0IyLWOdY4ORmsvDWB8p4kEK95zIdp7byO'
        b'yP2ZRL/qm2pTAydYvzvj6a0TbRiYnjojZWwU0waswyVE97okZ/yLpDar7VDHHlFOWoMZcFTtUKTa2rCIZJEZDEtMg4gEXRIS7EvOpyMUKE8ngMfWeGvW4XxCITd6xN+0'
        b'OYdwwyta60W1tnb6BM6de4N0a7iw2zlA/HJ/kCdXJJ0p4cLDrYIMXLkBvMk9a45OMcabLCerjDvNPcFHcpH8fmEEV6lmUKYE3p9RWz/lvVkYmegbExdVp+JQlsaSXx4k'
        b'gaYG/GgZx90V2OpI9mAHyHxrBu0uuh911YIvFtNMCSzHHB8+cIYLXsEcyHHB/SkLFkcneCXuiYP0MdwTTsbQhGet2LthsD5nvuJjbW5puM2nNmbiC9vpmXE2FvVaRLl/'
        b'4tVxczjG8DdmNceG5gGQQ7y6MQCblrMpsSeV6LMHoZIpiypFcQpmsCG0xFMbUrCWXEowIHKRKT9n1WRW2XNLtDl9G7lALQlOTxhyCoGNrC8cJbJOPZ7snUSuuqKGfooo'
        b'soVYkSTvzT8qg2I2l13d8AI0Uw8zeUybk0zh50L3MgXPZqUR7MMapT8VBQV58ETeYp3HvzWUmWQoE5+jW/3z9MeLPDeAwZsOXjsZvMSXyUXWD37TzMyNKRimkUCbPoto'
        b'RkWixnvUG4vlVB/B89i5iahs3iLb5WRboty36GO7Nllmh93n0YVWYpZMN0vMwOs75PTDtdhl3LIpY0U/eqbuXrmllTU2+ZIp7y3BA8KqxRPZAlwHuXuwxd4bO8glqDDT'
        b'gn08HpVBbUz7P2dLlC5koRfuUEaFeMWODjH+7f6Pd/52svypnH8lVMx6MXxOhN/oqVKIe9LGMD1z8njZolxuzAcnv3N3Of3+8GeKZPzITOm7f7WdFGfR5Kkz6yPZon88'
        b'uX+O5ZrbuZmztt0OSZ7ZfNjNr3vnxT2/Xfg8IDjbe/ffGyqCan65N33MEdcxo5xyDEMOjLldYc+Navit4CfDYUPDt6wZNjt4/Zedeof+Yv3Trtgb7xsEZ4bWJK7InRZy'
        b'b7bNEpnNJ08ErRxjs/gzm6j6Kcde2Lo/O/dC5hsf76z5h975Y+fcZ4Xi5uBjyyUtSS7nb65a4xO8omPy6vcvwl+vzDaf+YF+o+3q4Wtuhn44/qNNTx5r/6TNxKC1YPO3'
        b'YYXlWfvmvXHN+qMptzYv//mrjPcXuLXPq3L6xM1hVF1EWETu9bzQK/Wph1I/uW+41b2qK2O+98vOhkW5zz615YTjjeGvf77H64vIj1JXHvxmr7vvqBknnW/8+Pqd3xd8'
        b'MfTEpg8ODPlePmFGgqmBs/3dNQdmp68bFv/KMwGXjpre3tpU/+PZ5IzutKlN71z4ZsatJzf/eOqNsa//69IY83e+aTz08+z3Xl/wS9aT/qu1ptm9e9Bi2Fe+c0PPBrZ+'
        b'k/y3T4Jul32R+ffJnk+/dWbs+sWhT49OK34mzChqWsiTfy965fllds/arl16dnr+sl21E17Iv3v56Zoy86fek75j8M7EF2L3mJgn691Ze0l5e1biuNjuNyRjOvWSnO8s'
        b'mH3gmZig2alC2y+HLnVYfDl3bdTXZhPi/Vz+ov210Se/J454b2unzDvg2Kf2hkn2n5T/Gl/57sn3JyTufmXErlMrb7SOuNn1wT9vb7k14fInf0/XTw7+ruhCZfH3geYz'
        b'qjK2bk/9Ybqfd8Gpm3MiIPrtVXaH9Y7f8fm+407R63fDLl2L+HFBeenQ68P/Oe+lr7UvBr7ye7zDj3eHfy5seOmLBY6/z8s7+VH8rRMZS5/doYXjVoehZOjBpVvCr1av'
        b'eXaLVeoXOw4anjF3O3Vm68rf/C2efTdk+ue3nzrYXfSZ3OnTI44V99M9dxitf9poh9GLX43euvfZ5+qOf+l4ZdeHpz5SZl3V6fpgjHBXr2zJ5cabpas3b89KePGZvaPu'
        b'VAeOMr/ZYjZHP/SnV/6m8+6VzxINRr/0W+yYwqibhsrS51L1bu558epTP53Sm4nZ1yZ9/2ZSzjf2utfyhqR6fX7hM5MP7z8VNuGFYWHFr5Qn53yz94jdzRvk98/tXIpT'
        b'cyxbVp5wmpd76P6iHb/e//vol1unygpetb9z+AnJnY2/7Hlhhrb/peH/NL8z607M27o7cmY7tefsFSp0n0l90u4vwW+mv/r2lInvZEDDjjfb3x43K+zLZz596m+6763K'
        b'15u767M7CZ2vTs2Zc2fH24pg/nm9tdkVe3bKfjUrXRz40sVtLnj24s4b0Qkph59I+Xqte9js36e2335h5txRn7y1uH2YX3XXidsGx26MtH/tlc63ltX5f93l3i39WLLQ'
        b'/u6L+54Y96mr8VfvfTD3B4P7327dNGyY7e+ftTYfedvn9SEhYT8bffzFnGl6Lyi2ME0PO/F6kNyKso1QFDZ13MU4ovpWwhEpEUnyPJgm5z4dz/TD5nClWiq2Tmea3AKi'
        b'OYuaHDbDtb4hFSZ4lMVcGBA99ZIP5vsodkGr+gYjB8lGvMyzG+Zhg5VK54yGir7hHVcXM2C2UMwlAl5frbRXI8WjWES00nFwium4rm5wqofjEkuhkPJcqkguz0OjmFjY'
        b'aelE4RIZViKmR4pwidlzRHCQTmykiPJEfnUhx68q38gAuyULhg1NonEOWBCDuUo70gLbRH8FPdNbWFgNZZHEFrgyDRtkQfOhm6mQ3nBuro/aALHTTrZOsDLDC6uMTYQN'
        b'Pr5WREUPk+nyM11XsobFuwWRwbAnojLZ9NtNZFAoTCZtuC4G+ZT6zvWxseyBfZs+StgRDZ1Mj/Unsis5srNtKcqhj4TTxtY5yULAJihg9gwlP0e8OJvaQH2whRwqBpBN'
        b'zn1ycJ9l7bSJxUur4LKIlyuC5U4jT9NLk2SzxKdtvUjFekvwnLCcNxEtCo14FK4qrbywYBvLGS3018bLTpwxXJIk2RuzdgdCGmb6MJAU2vXLtfC6IEnaIJp3TkGOE4Xr'
        b'bIYjWEoxDS1lnC52UHTLU3Zi/FAjdBgq7RRQrcRcXaJTaHF6WCBgnpYK1w+6vWiWc7atLjQ7KSiYMekAA+iUDMUGuWiK2LcQT2H6fOu+Wa94FUvFd2gj8ncBHUNrO4We'
        b'pRXUSd3wOGdiLsE0PxAtNVizikhLdj7YrsA80gmGyzFbWA2t0CRCXx4kPdet9OdZQNzZeKJA4GEsF5t3IoiIyuTl6dCQGjBXa4IZN8RMAuURMxjAIrTiFajxYTShPRyh'
        b'oyBDSgb1KpzxxlbWBlMiLrYq7bzgIhRAjj65k+MMZZL562NF/tdTnnhe7m3rmwAXPMncVCp4bkSwdJbjEvJ65WKIVtYMuE6/57BriAEHV5SurOTx2JHoQ+G2raGWIm5r'
        b'kdVXInHFE17sDTxisJM03JsM9qV+iI1QDJdURLlJenhxudLLSkGEJSjhIX/eZhYT5baE9HMLGSyOl5PZTFbXiNVit1zCi7o+vv7QTG7oa58jEuNl0fhSH4DHpqrIqrVE'
        b'LMeYzaLxrQCurqKraieZz31sT1A2WbRNnST6RIPc0i4VyjAnwZe0Sg+PCXAtQczJ3QVnh9M38rPlOV3HJzwFKJuPxWwJ2prEyu0UVmSwSJt1YrAa8oUYKV4VUR+PYC1U'
        b'W5MRssNSbPIS0Z+NIF+yPmavaFbMgSsKUnECmQt4DC9pwVkeTw1PYfPQC4qxVK4gy4T1CLdWC8t4bLMMEDvxwDJhwnbRYqYyl20eLiaLH4WsxXjUnq4C8qYSzOGhGk+C'
        b'aMMi8nc5dPr4em1YT63vMk7uLeBZLCKDQufmMDg4lA7MXqxK9PW3IwvfXqIzbgQbHTszqGSbAYeXZ8MZstachos75EFr7LQnqlwLZYUgGjB08aNC4JA4MEdTJ3qa989N'
        b'XxWbJGqG7dZqwR3LdHgLsrhOiivoCDQ7U0PvXuzsGwU4PZa1cjzWTSCtnBivSPS15zm9BQLUwXUdtj4C8LqDksGo0jUKxeuo0YC22pTsuFjqhVUs0NENOyiNR4FCDxpt'
        b'sJ3u3M3kphHG0nl4wgpOz1HZXPNdSTmqi5CLXVqhPNm6mlLYElmOrbzadjoRynl7YQF7sXlWQdQNk4ItUqJ3Sofwa8mriiOeBwdn02syjoeTMqL6k/G9gk3iWzdPsIMG'
        b'Mpla7DHHkqwNPEluwnQQrbhkb6uyJ0229E61EjhtOAw11oJLWARLAk8gfXeaxrAGeOE1Mo8PkuOKzgwjQRJJdpc2VkEMlMRbW9rCMSxUbRwUN53M0mxxaymDA55KdkiR'
        b'vVW1N5pDg5RadR2xA8pUsMfHoFvc40mnOEOjFhwn0xYLpqmmvQJrWOdjGVSQLYx2nR62kVmxJ4xNJI/RUEFPXcrVHKo04m0VWM1ewoRSQivJeOtiTurIOPKBVTEUD0vI'
        b'3n9iibh9VkAWURYzkxgkuwjILpDuFU89KNeHPNEAC/Xa1AZrhvvZYLm44aGkZHmygS7p2fH8QuwQTxyqPmKLEg9Sp4ApWbz8ROprY1vDTszQE/d6m7FeCewWA6yTTN5I'
        b'hoQdN6VheLmHUoSh1JMzMluAI+arkhT0hnQ8y0zKFP7Xz0bh5Ue2bWbm1+LgApyZ5SqDKjiLB8Sua/clii4zQJMJfdjGW22Bxkw4lkSDE/Xg3CgW2yoCxj8AFp+LWWoA'
        b'2hBs1LG3m8jOrI1Ef++UszttE+iui4VQww0hS5X6jG3EfaF6025GgT2NiDSqHZZyYBtL2NxbSvq/hEwNyPBTrTkPAep3WYh7UQtWGHvx5DLb0I/yUOCTKu4M5e7+9GtD'
        b'6FRtJ9MlunBtkihSdsOFQGtNaPdTUtdR/Fx7FBEaIFcLGtTtp5XA6RTS/HYJ1MQTqYNOXX0skqsIAfoB7ZM9+JSWLqZhPtuMhpnA6Sg4LmfHoQQ7eDgH1Uls2wxyJt9j'
        b'rlom0uE84YSwDJr2skmy2RwrozCXbPbePHmwla1LIgzR5o2dCQX0JfW8sdTFj04X8rwpZEoweyMeZ14nPL11k5zMB36kexyH+4eiKlC6BU7EKP2xyZ5IEnS3prAVxpsl'
        b'kAv5KumTrNULBlC9CFts7OzollBODjYsUrIprbUTS+R0EQiK6XCZH0uKYAPuqTVL6etFuku394XMieAL+6Bj9oxFrCs2YAa0ym3ZC0GmjmysMBTTg8XTtgvSaZQCtT7Z'
        b'WtFZ3UYOsHMCOTv2WbHZkkQmbanS3goveSroVtSJdVAjePriNdaXO8nBXIUttv6iQeKIntZunoxEy1T21n4xOiowZLiKGWpSdoaGDNccVDvheGxX2nmb4aVkBdkMiBQn'
        b'CFCCpaLUvWsCFqvE6B3Q4GVkSXc6A7wicVmBp1i3bSBFd+sH90Zf09BrvGwiztcuvDrBx86PbNs7sIqIaK5S7GA7k5PhUhaSzQnr4bAj70gGIk2UEVrgIDaoAUsoWslC'
        b'BliCF4MVQ/47kLayR1xXwVGw9FlZIrPfMy/PKg1Yx+o/Os46DP+XohpTKEApgwSUCqbMDyNj+MY0FFz03tBrOuQu+seU3GPMC/cpcrFw31xnNC/c1TcyZuAewu9SKfXo'
        b'TOInCSPJk+TaPfKdgZShHZtIhF+lMim5KhOm3BfSDHnhN+G+sc5YWt7vshf15hgLlJudYh1TxGNj3pzcMVpmzJtSYBHJaFqfRPjZRNeY/U6/NTcwZ5jKluQz+U5r8NqF'
        b'+6O1zHlaLgMrYdjNpqRFOjLhZ0Nd2Q86cuE7vaeFn/SC9BgqMsVF1uctyM8pPK2btOV32l7hN9kvOqY6/M4RGrw3Yu/3ITZ8xNj1yUx+hYzWZBkZNoq2rtmJxKWb/UWD'
        b'G2nwhpDqWV78dZ4mHvv7K6TkB4sjr9N/ALckMZZj2ddBbp4efh5BDKmEZUuLwCXbetBGaDsTKYqx6Igz/T/BE5nT0000NkOX+toOcDTGTSoIMkFE5P5V0P7PfZK9JMw0'
        b'5HWMdBg+icCb3hfmiqgj5lJDet/vgkTgx97n9o7VYyiv/nBtfK/J3tas12gvcK6rZJhLzoncAVn1eqp/GS75Q2BHJJE6qs+6fT7rkc/ySH322YB8NlR9b9TnswqCpEK3'
        b'B17ENHJYH3gRSR94EbN8bd0RuiMjp/TAi4yKHN0DL0JhSbjIcZEWfwBeZHy+THckKXFqD7iIQbRW5ITIiRphRSiYSX9YEctbRgyDh5Fou0etj0m6Zz8AU6TP1X8DUGSW'
        b'mKjupBBuSd0CAj1uSRY5LUo8SWf7afqjin98ZI9ZYqal0x+CA1E9NOuPQ36oq2OJnY4U8iOxQczAqaQtP88ghgI9/AKCPRjUx6QHYDaC3N0DoxL6p5M7JDbSF36cWx17'
        b'8DDUDblnPlipPSAZ/dus0O1XBh2HxHf7Im2oOyfxPfpGf6eXBqvDMfEqvee/h4/xmIy8Wv7M0TVpKR50hXZlH/Q+o0XM0bUK8yBDnpLAcy5EZqM4ZRVwEQ/EOLyKWkqq'
        b'mjpLzClnuWfES9FW6wMi9KL/yX2b8VbKiFmrORc76fMlnyh40VB1ZTeRQQvC+hmqoBOqBuEkvaaOA6EC82ASAosGUVBug53mD6yyx8TZGEU6WunwkNOM4W3c1HCiDV5h'
        b'Jx3V1ymYBlUc/k/ANMhwfzBe9rhgGpGs1RQtgEbw/yeRNNQL4xFIGuqF9cg7Zj02kkb/tToYksZgS/4h0BYal6/m+/8AksWDuVpiWkFEHM0IoClXgyQQ9TymCSl1APpF'
        b'v3FWIV7QY0NEsSBHh9XguT6PgppQt+SPgE3ERP8PZ+L/PzgT6hWnAWaB/vc4aA/9F+1joj1oXMD/w3r4E1gP9L+B6Tda/sHJrhyl+epyEXEG+CcGIA0UY76viji4NwgZ'
        b'ujFLTuNrSmP2/WODROlGSvn5q4uUCP2ftzdFr3ry7Ruv37h5480b79746433blwtOnFo/P6mfRNP1u1T5F0xla+oypy8v668Kcdx/3hGl54Wb+Di9rJCSzR91ofCOeve'
        b'mFlHLHbACjNmIJdjGp5mSAD9YAAwE/ICJY6BeJUZQNfDlan9wVOxcjh1xqZiEbOopMCBVGpSmZzKsyx38prnRFtnsw8wgj0nP0X/NH7skqqjPf8jGfCa2RH65MEHiKGp'
        b'NGhVel+DFPKHk9zHP44INPZvjyUC/dFM98RuXi2Sachy9yEtE7PcB9TUk+I+YZCDbkBau+zhgbgbtB9YFHL1wvCkQpr2A2KanApq0XKVmKbNxDQdIqZpMzFNh4lm2nt0'
        b'gvp8VolpuzWJaQ9PVu+rPP7/IlO9P46XSvZRpW9vJacFzaP9X/L6/5LXLf6XvP6/5PVHJ6/bDCohxZJToC972R/KZX/IlvF/mcv+X83AlmgUAU3EDGw86DCiB9BrOBzB'
        b'bsHQGMQM7GRqUVlv7C/GSgR5Yk6AGo/Lk8Z/U/qw5RQKi+aaSi0mc1AMebpwNTqURXKHR2wfkFktm8TgvtbDIZHIoQnOQ5fSwABr4YCgQgyLhoPJ1CkAFdCOlT3O7GWe'
        b'dqbjNcJxCRwcxlO62IkFUJdMJQ39eGzpzRrFbE+bUOr7TMO85ZgtUrN6aXHrpuoshMrtydTTsdgU8nz6y76YuZqlwNpggZ8Y/hUo18Z8981insgV/Ug1zatXyFLYD9nL'
        b'bUOX0zRebz9fqAv2hAuefna2Xn6kEHsBmuVORFAN4sZChWHsCigRM9kboVCpdEocixmCSJwRZMlY2INhn26f0mnJNC11m1MizUVlieFSLnzCCsjThiPr4RR7yCgSrwep'
        b'b8VsKLRkQxUsPtXz2qujtaEWs/CimMjRgcfguDzRkHSjxAkLh/BzoW0sGx2/3XgKW7AjVUlDaDJIp3Tz1pC7lcXTB0+VLl3KGXPcgnCbMZuGcDFDMlJ55VPkSvXNgpDC'
        b'uSYZC/T3Hw47ure25Wuh9WTae7eO2b3hnX7NUyt/RebqJ/1eLpgx43mfrh+dhvq7rF9RYm/u/nHodyNnx+UWvd4YHX79szG/7sj2tP9pUe4U8xtvjF5poXyr0cxEG24d'
        b'GzH1u+E3J0U4V+aHDa1/1zfW5stoT8VvzbaHry0vd074aOpPk/Uypl61s3zLu7FmTeKFn3L3nvpqT/AV/00/LzH6cmHWe39JCI29d6j+Df0li18Z3hZy/uN3nF84uMH/'
        b'bd/NAXFF1+cb2Hq4fN6uMGbahCNk4uVePDoW8wPX4XwsVK9iSkPqXjKEef2SO+EClAl4dCZmiKQLh0dAO2V4bqdhkRRZbMMcVjaWD7dVE2qL+ZdYhicFshJOTGZu6Rmk'
        b'1A65Dnb05XoTNRJzzGNl+EEWnu+ZJ5RpGMoCKdlwGxxltdtojaHKDhzDy6K6A5X+zH8sYG6sT9/c0vVwjFKBd2G+GAtxFFvhEo2vnb9lQIQtja49jJdUBbW5iK9BV2qO'
        b'L080rmuSeXN8dT2YW38sdEClSHfMSY09Kdsxtm9il6KxFst8nLyxkrw3WfwXyWQ0kokxNVkj7XrMyDX2zJI8ThWQqwtXjK29/cRRsabROFdDpkrwOFZjDSt3HebO6VUi'
        b'12GF4ACHZ7FQXMiAq8tUyZfLNmpIv7THHMgeyC4n/w9mPfo+Qv3T20FzHymvL81flMmoj9iUeb8NmTfakP0ld6hyGHeOe1Bz0piqqPs4qYq9WYpagzv6tQfnttWQkej/'
        b'OLqnxRkNuuej3uu/mJS4USG5F/bIpERNStufykikXouBGYkT/RlEBO6HqwsHZCQuWCvmJD4iI9FgTTJdztCNOVwv6gBcCsUybr3bXImcm4DnJZgJ3d4igEEJXMEOmnyI'
        b'R9QgBli4PEmEUSn2hyL6vDXW06xDDoqCI9lpUKkUOOlSI5rQpg+pWzkmW0wYZY9VUNUvrRCuKliSFGbGbGJ5hdAC7facfQxeE5OKDkAZ1CkToH41jess4CDHDsSTCkqi'
        b'oQrPYVOf3MIpLmLG43HIglZ1eqHMTFgI1fpjbUQJpw6qQoKIuNKEXSzBkIPCGGxgRQbrz9sFZ/slF46DUnYpHrpW4zFM700GxAY4kMyifVZPEjP+4ABe6ZfzhwddWHdc'
        b'nlzAjVbUa3EO4f5pvCCmu80aO5Fzd3iCtCF80Zodu8Uvp0325IpmfUG+C/dOl3v/e0l/mx4vUwypzYVlinmJI97sJxe5UW3Itprg5Ye5NnhIFVuExdBCIUxoeJ8C2iVO'
        b'TqRXDhFhCYqxRSknfeaG2UbBgdDN3mfEFn3O3OGWjCb6TdU2EV/SeJIZZzP6HZbot8IsSATCwErIHKIx1a8TTwdg5R5xZDOGQbMVXumT0IfXsIYVe8Rcxunr3JBSMriC'
        b'+PmcgmdC1Rg8NZ9G8WLnEzSQl7cIwsb/iwQ8fR11t9L5sxsuQclG2NcnB88G61gDhy8hJ2siVIWzJDxKV9cWwl7WDTrhMsvBw+5FLA2PXDcbK669C+Ts6mZJeOnQtYxb'
        b'hjVQwa6MWaSjSsOzdqCJeMIqPG/LFnNC+OqeLDyagieHc3h0GZTGJHaGCsp0Un3DlnXJwV4BwxYaf/llecc3Mnf3j/gvJ3z5jwO/6H157XL6P25ZGb5w2y0na6zRvPwP'
        b'b3z0s/ZLB3OmDjX6XX4/LWdqwNq5I/2mfdPw+Q7ZtLGbr3ZdrD9Teu/qxJkvhH60/feu15onjHvR8osXV8QceW5pTZdk3cgRrc4prfLzSVOSJtQtG3X10KKnLjz3KTyX'
        b'+P8Q9x1wUVzb/zOzhYVdelERFaXI0hEVRUVRUTpKERsC0kTpCyp2itKkSVFQUAREURABQYqa3Jsek7yUlxijL5pioikvianGxP8ts8tiyUvyfr/fXz/Azs7Mreeee849'
        b'53tOUOwX09wPejfINWNj/a2vlJlY6CdEDyy2vLJ8+pUl73ssD1v0Ezzy8vO/LM7P/vjQgyX67s+IbuamB7BXZ7x/QeeH7ye98cmD+4vBpn9kT2yLfveF7rPSGItBx2e3'
        b'zdOfy8yPGBNwyavlioVzwDVX0fqbb+yZAeM3PiitM1n483tnjPrXnwhe/ZvpjvGXpqQE9VyzsUvPca9wm9PYPP6twYGu7JcO/dvJ27Jcmjfppsk4/R1R14uWP1fScXZv'
        b'44+hNRsapvz83NoxS/Sdznl8VLr7o8hnnOJ2jfv5Tq1G//XXF81e+dVPCR+deCdg2wtVc+/Z3f9HiWWVTWxnfkdux21vt466zStrPAVXZ0S9l9t8JavrhyUr4gYM/yVe'
        b'Wd7x5mvbTjTM9sw8c/D90pc+iP/m6LS4lG6zF/u51M5bb5r9w2R1Xsotw96EvrA3PkpfMzj41Xn7zg/K33z2XENXRN+aIt9N8z4/9fonxyxmZ861X9Ipvz9kF9xfZnPm'
        b'k8lNJbbfg/tvHjFpWnrofHjq3ZXLt0dd7PJY/ON39r/e/OrF9sjv7ht9NX/rot9uv3k3vl287NNJC/7p+VBv93t335K6X4ZdFl3NUeW/vPib4YOHVXL3GT4uv7V8IOzX'
        b'Pvf2oc8sLri2TAHXJ7c/q1m++/a6U3tS3l71dZCp/OHxnkkPN2748MOTgplgws8+E07eeph5c637hy7BDuVSlzdEp9dsjbiSdWDptfMbujfrn1NkVi69jz7u0n9/qdbt'
        b'lyK1+hSrRRapFTOuLzG9/VKs9tGziYcsbmzW/VL3WAZX+ez8oXHeMWP0smU/TvmhLG3w35M/Dgv7ZcKwX9erXXZdpx9M61V0FBzsEnx2Mjc86uyd9+/8diFl7grveVNS'
        b'c85PTm5vN92umwlXtpoYyt+s297/9Q8fGQ+dci28kau9aH5/tmjXJ6FfjvtHyact/za8GJZyt/zBveOZH3+5+s6Xe772L2w3zLzqOnnujGbL782ui8N+P/XZ+uTL3w+v'
        b'ftiU3Lb25pdDYQlXTt+Y8VFecGnB0qHNG1KNn9+iG1ExBcxZ9+y//K0nBiy+bCN7KJ5i+emi60flqVTc7lti8yiYDelbzSpxux6UEh+LBfBInBLNpgA1fMwV2BpIRONx'
        b'2+AeO0dYtWQkNAkFs4HhWCKtm23GAKpSP8TJo9SxbGBgBx/NGByYgO0nSJXvJSC0EQDamAmkBcuRAtSlwp9h8BnaBKscdNdQHE9dBDxF4GfYQX4U/gxWT8u0JYwfFjrz'
        b'ADS5L9pvQHEWRqwoQWhzQL4Y7Tl58DxVBc7B+o0qDJo4kgM9NrbOS0lbzEBnuApyhvFm4DDstoIHTcjdFXPhEA85S4d9BHXGZYP9cC/1VmmctFaFOXM1IqgzLkgIGonn'
        b'P5J+9qyntzPB8GjUGbwADhK/3ZnLbNMS1DFnSF08T/3MD8OOICXsbN1MDDzjwrVgJSl7IqyDJ0EZrB2NPKOws43gKPV/3wfaQbcSeIZRZyAPdArmgssUQzS0ZBVBnqmh'
        b'zmC1LWidYUatWY2gf4oC47XUQGeDqFkl22E3oZV5IWICOzMA+0bBzlDDLlPcThWahQYlbAxelGPkGLdmuRnVa4fdzNEue3EzSzexk+6glfQOHIKdjmDQ7xHUGMWMBcAB'
        b'MqlOjiBHF9SP8hTKQqNKTiRKHZ2kgQ4yOeo2aGYTkV7XOX086dXEaHMeUtKOxA91SAko9qGpzwdBr82TwGhH0X58YjcsI12zhK1LKBbtiMMIFA2eS8+0IF0LBVUEi4YF'
        b'bVgkx3A0cMGSZSYKheAcUqab6RSdgNVSgjybAQfVkGcbp1Cv9X60SDBOC03w0CjkGcxzJj1NBmWgLyZaHaeAhFNCWrqITgcw0GoLOI/RZwwYtl9KZ/4S3Bs7SnXnwEV4'
        b'HnZGBhHSU8BmcBop3UdGQc8iNenLPbBjld/omEdTQCGSsdaQ+wngRIbUxlENdQYr4TAYMkeTS8Sxcks4SLFnYngRw884cEhoSSoeh7FvSvSZ5QqMP+MSYV4aoTZTMAQP'
        b'U+hZm7c68mwhEvxo/qZ5MTzyjKDOLvvDo2v06UlJOcyHp0eQZwR31hCM+nxmM3mXm+MVHDIKeoYUmkukwS7LPEHPjtHQsz5wmC7SWnAk0Y9GfSO4M6PVsA3sM6Ae/yXg'
        b'tALPDDwE2kawIhyoos1tgz2IEHr8QV0WAaAxoNOBx5igtRIJC6xGoc9g6TSe66BVWJMG944GoIUuI7MOC2AHbCXC615tKrxa7yLNSbJEzMARUfQ+qTr+DHbEUzjAEOiD'
        b'Nbi5KjBMFWgG7bBqOyFpq5XwqAJ1qRS28kC00Sg0uHcFZXs9OoongtBAsdTWH/UIt8UfFdE5gkLDCLT8dFgMzggIZ/BxxnHki/23g04Sw8sJFAfSgTkNji1X4dCE+uw2'
        b'ULXODJ6hbL4IdoED+G6yI8Gi4WlvjKBz0Qo64FCG9iM4tDqwn7yq4ahEoTFSgkPjZoM60E4hZCeM4QABw6AFgw9Bz6MWj4VdQngZoEVZAM6TgR8/dgsvQ09VytAHfPiJ'
        b'TgWt5AztEmzhXQb6DcmgbwxC619ZLCZMLXCAW60BzuwUkHaZbYVNUoqjwTop4jZ7pghgPx2LfvRKn52KR8kSBHZrdYNnEiZmEQVPKMjWaKvJ497QCjgnYCbMEYJK0BpL'
        b'itgVslIFesOIN5AbAI86geNkHw5C6y2PRwWPAN6qcSbsRFBCwDpzLaMJ6M0G7MO4N9ZhvDN5dZsYnlXAUo84gnobjXmbQzP0mk9xA61z1PBuIBceIWs1HpTH0GonSNUB'
        b'arAfFJO5XAGPhKnO9EGhJsGocaBGuJYc0E0HffREVYVP8wU1IxA1Ak+b5EGxbifXgC5n25GBQoomzBVkosVzlgyjlQdeoVja0YTFch8edzQO5AhhT9zSYEgb5O1pSB9C'
        b'3RSDXhbJAUc4T1AK6mktLZtgKQGigZYMdSBaEDhNqGA2GAC9o85guQQkBxxeASrpTPeBIrB/EahVHoLiI1CwfxopPTMaFMMzoEWBag9CtFRuh9iuXrZgByilAQa3gtNa'
        b'doj6YLlfAOINtXi46rjtsCaTdNELnAH98BRsVODgoEVYgMS9ZBl9Y8FOUAkPEZAePDYbVj8JpecEO0bh3AhIzyObioKtoAXWr0I7oRrQjUe5baEcHwytA/swOleJes1C'
        b'LPXUPBva70HQ7wPPIK6khqv2g62UXxWDvVb4Bj6RGgH2om19PwlSgLhZGzyvhsWDe0CbGh4Po/FQBa1ko10ZAtuCQ9TxhDyWEFF7M+EC02AjHHgEjgcbHQkiT6SJFPBL'
        b'dK0XwErPnfCMOhxvpwaZqN04VYwKjofa0o0hedxybNci3Q0Ax3VBEexWR+QhMigk+Dd9sGeJIjASMVa5lu9oRB6SBVvJcpyGRGWpfAwcwqg8Bu6dDcoofn0tPsECfeqw'
        b'PCUmT0ynoRdWbk9Dcqk6JC+BtwBMRSuvSOobEAUPY1geOxHsSSes3hR0jnsiKA/2wiPuFsY0/fNwsCWPyRNP5LAZwXAWzCG1hm7zVSLyvNIJJo8DtUYwl9yMDwG9PBwP'
        b'nAoniDzO2wocoe0dnhapAuOJdiKyWA9rloJcugNVgAuI1ZYEgH27MSRvFBwvAVLEryuo3Klw9FWD4p0PR8ytjh/uaFCD1gof1uLMNHU8HiKaMkqBF2Ev2AP6F46G5CGx'
        b'souMWxbMgXl+jgGmsAfD8ti5xrCBcPUI2OjJn42lW3B8nnCRjVzn/x5mR0BQxKaw4g8wdjzSbgpF2umxQsHTMHaSRzB2QmJr0MIItgd6YiF535w158aiv6Z/AlMn0RDy'
        b'KDcZj3TjfscIOO6h+KrWzEdRdtzvBkI9goYTkpqxzQOXMlZigm0CnD0tF5UgFP+X+Lp3uJ+1Fqvj68Y+HV9n8qgV4r8E11Vie8g0dPVH9hAmx+SjJ1hEntIW1AKMRcj4'
        b'SImvE2B83Rssf0QpN/y/w8W9iSq9i+GDKcz/FC5OfJWz02ElIjUM3NQRDBz9buzDiZ4k8qJVOtg76jB74W58nM0yNuCyKDki5DHnWB3+r6LiEehbtUa1ZrVhPId/V+vw'
        b'n435v1r0b6IgXlAtieVKBbEOKnsTTn0jK9Au0CnQKzAoMI6XYQgcAZoJ40Q4d3c+E6sZq1XKrRajaym5lpFrDG/TJtc65FqCrnXJtR651kTX+uTagFxroWtDcm1ErqXo'
        b'2phcm5BrGboeQ67HkmttdD2OXJuSax10PZ5cm5FrXQKvw9cTybUeup5Ers3JtT66nkyup5BrA3RtQa4tybUhSfNjFC+ItYq1zpesNioQxbOxU2Nt0Gdj8lkea4s+mxAv'
        b'SwGxzUkKpOgdXTRW+mSs7GLt0RNjYgXEnuF4TbbIMyB0MW9cu9XHPeJZiV2b1J+gyDuVY05mKs4DoaDPzJhmT/+6kqwJ+NP0UYUpbXgKR3NPNZ9B3gWOwAd4Rzt0NzMu'
        b'gyR1SN2Mc9Vmjvb5U0/wYG8eFx2zwTwjLi0jThGXolaEmlMi9mgdVcLTvH5GWxJHXQSmYmcvn3hzkqRVYb4lLiPOXJG1PjmRuC8lpqihMog/FbodjX4yN2TEja48OS5z'
        b'Q2oscVRHbU5N2hxHbJ5ZmNkkZWO/rFEZLMy9EomLk42nnPfTTRrt+IX9o3jXQToRTvw8KEfc3txmoVz5WLS5Ig67sGXG/dEk4Tm0WSTHUI5oNTdB3kEvNSMxITElOglj'
        b'CngwMhoCjJd4pKMKRXQCQZPE0Uwd6Cnae/PYuDTEXRXmqbThxNfPhr+3EFNYcqpitMtXTGpyMvZHJrT3iF+hXHBNsDU56Zo4Jjo5c8b0a9L41IyYuEgyI4FLYoRqLAmx'
        b'z0fyaQn5pcIg5sIi9iLlGQyHFo5AlU9LWKiRx+wUbdPcISTGbRExaAt3iULUPvMuyusEfwJJNmphPd3b7GkOiKi71PdwZYA/7zxH0qiQckfmEc0YcTBFy/TJXqk2cZS8'
        b'nraG/wDhRMbaHQNVYqIRF4hCTYqiToC0MFUh6qT4lOQ20bGxidRllK93FCliok3PiuOXsyILrTMVO3kysmOUYy3NWYNXY3RWZmpydGZiDCHe5LiMBLWMNE/BiGSgVZqW'
        b'mhKLR5iu8T/OMMMPjxoJumMnYez3S3iVurdzYgqaoGha7H/KeEPbiViOevUE3USKDd26ODNJYZ6C8VtPLCoAo2/QoKigW6ohpCXzzCj2CZ18sn90/MjSjSHsW0FfxQ7O'
        b'SYpUCg9Do4b4eNzWuJisp4HyRrM7G1ucUEcFWpzt6PwE2OIoSUMb/YiYRx08JgQqsIZXf9e7582f7OTtmfKX5X0l8ne7cxScM5O4U9Jqsecefp04NabBBtAOemAl7Mdn'
        b't5lIc5ODPlAiR0p3N8hRIJXnMn4JKe7nLYiSEEriMSPVeSAVnEbV72Ik2bv8QQ31PDDj0u4K8Kcoe8kaZ4a4ZQTBc7agB22ycxhn0DwHngf1ST8/fPjwjL2IUVBvP/8D'
        b'C01w9FwcbQAcQlpnqQIW68CiLdSig3R5TVsbdq4bUrqrxXYsHCQFZ3vCein6ngFVsVwA6+YFG1AZNMiTCRhSWCB1baQULfyLZaa4i6bMgZXENp4GazSk5GtYGoZ03EEW'
        b'nPIHeagQ7G6ENLlWeHBUQ3xs0wPBIQM5PGfn4+eIDUsr4CGJGTgCu6nvaRsDz8Ie5U3JDM4MVqcYGckFWVg/zAL9djgVigOsdHWewTGynRzMCd8EymAdcQIBp0GL+8gD'
        b'Yka2iwMHwYkkMATLs4h5IN9q58gDLCPbzSVGJMMqMJSFzWAT4UVdkGtMU614h3rjJ5d7j7j5sMxiXY0x2ARDBFtYAXNAMVXYlzskroJ9RGE3BGUCcDQKtmVhBMxKv9Xq'
        b'jkLK7DSwyN/Pz4FLnwcazOBFUGwMu2G3nxEo9pPChnVasBuU+AaHMHHxem7oTj0hj+0LhP7lHPXvzLUyYrLW4i6VwrPg7BOqwH6yTr5hNrDIG+4PcYcHsJeqXxjsUlEq'
        b'cVMK8hEZWGnBvaBVJIIDXlbglJzx2mIEG9JBMRp3PC2RSI+/DHt00zLYybCY4eAF1hr1vZ9QkSvoMZRKMjaz+HhGyNqC0tnUa6kFHlDAHll6Bgsv2qCXzrCWcBCWUr+h'
        b'vTJWkYbDunnBQRy7Owrsh+3k1hpQBHoU6bBbxk5aj17bg1477o5oitrwwEk/BezDhfaBeoYDw6wJKF1OyDEFdMJmWmP0ZFoh6EKUhc/4166CpY9MPOzLTla4ZuEIJ97h'
        b'VuopdgIcfIPCyOSDRtBP3uAHFeyBPQw8moS9Ns6AWjlLl8sJeAHW4lRIvvgkC1Qa8yZCU3hAmI4YwV6yIGC1BA49Vs8y0GnlsIIWz8ADTCy8IGGmgHOJBWFjWUUyWvfT'
        b'60OSq/xS316g9+KW9764WvbV9w0zHcqDj1Uv9ZHm/6N3r99lTx2JZvWr7fprTm2c+FHvq2zkiYXelRcm538piGTTPy3TO7rHotDQ7fUrKf4b9ix6997DN668/saQztZl'
        b'3NToG2NBtcR2bPW0zy5kfr7qK4nHO8v2nPRie0DAIeviY/HF3lM/PV6x/FaYZInHEs/nP1lb2HLYZNr4kuMSL8uP3is7UXxi3ZIfX2quKfB3/cpG4+jaoZ2R+s9XtsTN'
        b'ETw/7dom2/j7uz+bfq5yss2yjM83b/7Va7nv567Flk0/Vk+1GBez1MdYVnmka+O08JBpHtvqX3x7pqvA68u6mvSFy1+LXvtC/UFo6tJ0fdqzq0NmH/3J4Waj8Zns7Qud'
        b'bitql/xLnr268dn2n2JeX7Xm/NzvXn/Z+Isjk2aPOXPJZu7a8DA2KDHk11fcQjKPcXN+kXrcK8q488ydXV9FGlT9KNsxsG/COcfcs8XfZSx8/h32378/96D35S2XFj1X'
        b'tFbU8/HqhV/kV7678bOeaVu2i4LWe6eHras6NxCX+V7H+JU/3X+p43bN+FkdTYuMXwnIXvSv5x5cMZx27IbGgn8MWcX0FL+vdS5iRmj/ufiv90S/1hh3qijq1WXvfBPx'
        b'rkbvlkmf7e12/PdLWxeU18/sfNjkssXjWENc9KX21buluUdSLJo0fyt45tUTSYlvPXxr+gsbGtfULwl8e0G97VvD45qzfxgTMKMtcU39CzE9KYIXb+yKehhoWvjL/uPb'
        b'3vvQWHr7wbMCnasl/9K4eefGfrN78B+D7HO/XondNimn/46LRsrvk9259im3il+RnrDIWv/ev9yuZ715xeVrDzvDX0WLP09qVqRqfDh8z6fC2uXysd+k1hqCw4rLchqd'
        b'cCk+xLZzDOCYCaCFAydZbDsmx9uLzXEmG2wM8IVDoBsTPE/tk5YKYUVsMrU458AhT1ACzmIuhHgTLOYYKRiWrEHLEhSAbmq5rEUXF+x8/DVwlNtODhSy80LhAE0fDU8Z'
        b'Kj0awAHYwNCQuvl8cFl2FbwMSpyIrRr0bWDEUdyUtR7UnHcCnNDAuaScghw4cGgJI97F2YIc0EwPOgdBC1q8JajJpQ5izWBGvI6zmA5a6AFkuwBW+gU5+Njjc3Up6EVr'
        b'twh7F3SakBPnnWhUavkkM/Ps1X05itKpif8IOAkalTl6Niaq+YdPjqH194OCSepR0bhFTt6waSsZEEtYvlF5CusfzpCIaKAjkBx+LhBH2PmADht2fCAjTGDhPlPQT21D'
        b'EebYjkCCpcGWWcrDWVN4RJg+xolWehzmrFSG5cQH/YexKx6ooJmuD0E8DyXOeLsI8HPA56iBfCGWsEY0ZzzMpXb8fUvCFLDUx1GOyiuAxX46gQ6w149jJi4Roq2+YQkZ'
        b'Q6EF9kL0geWa/F1tL24COAUHNFli9pyN9swCNHWBDvbw+NwAtcrMXYTY0x4cI2Ox0s9A/Tg5QIMD1W4whxofB0CNHSJCR98Ae58AltHZILACPbOi0IjgaTJG1bXTbZk/'
        b'Q9eeIQgCBRpL4SnqJXAZnltHjC/7EdfW0LFjxJqcDNTAw+TYfyo4mKHABhBYG88INrE7Ml0I0QXDwsW8BTkO7KNG5FhzSjl1qFv1vDEUEUwhbxAFF2Q0SCiSpdqJaQ9b'
        b'mOE+KSOC9UgQY+T0TP8AKEOilJ8jNw/0o1fbWXBUI4GMF6hcHDESq9QRtIlGWYnRCqMxldNjwDANGrp6ITXVgvOgjtzSEGQrTbzbQCWJNQoPiOhiOToVI4SCcIDSeHAC'
        b'VX2YBWWzYDO5GwUvgHbcqXI7DvRaoLs9LGiD3a7UNJMDeuGQMhYvA6onguG5q8lwWCF6OKsMmi1CAlMT6u8gx4JLESTWoQIcs6VRXdd6Yov6TAF1z6idF4in1cE2HZ5U'
        b'2tQNQKcAlqyfTE1/rajGIQLv4KNpgnoODDiDonXzKDXvBcdgD++3ZYIa+yhKAlSOoTRUmoI9XYnLhSnci/p2nkWrYhAcIV1fDfM96F0iKokZnViB0MRLlpyJoUliDxw9'
        b'fMtm2KudPiJ5gSJ4YS4od4Jl3gEO6JUQL4mOl5g67pS7wz0KOy0kCstZRmMn5w7qpiPiHKJ2uX04SrHCLoNSu0YcZ6k/bRM4Qwxl8ASoBftRl32wWTAoBDaSvIcixhi2'
        b'C/XhcT5/lw3Imy7FxdMiQDsXBDrnGeqQ+ZifCrqUJSAS1WB0AgXgdPqCQFhMmMuGhAiFL4kRfhwcZGE/q5fgTW6MhQObaVBKJhEx472gClSTiZCDi7Op+SsR7hllAWvV'
        b'JjtIIhI4D/MBrHFI2w5wcoKETD6ojTCkoVQ3buSMWIsJiygO5Dw8OBGUaEO0ocD9PmhpEsaAuGOpgLGAJ0RuaJAK+AjesEtPEShP94F5kba8eVVvgmA5rMrKpOlIN7jx'
        b'YakRhfSDgUWwio50D7iMRHYySH5rGAHYy25D7w8SkljuA3PtfB38HGwDEVPRTRDAKrgnGlyE5whpOcoC0BiOtA1DjIqcAkXg/ExGvk4EDq+AeYQ6wACalcEn0QcoD5qJ'
        b'pM85oFO8ZmYgeuYUXYUNiBtfoJ5X8JgW73wVBTppOPEeeGKhFN/MsgTlPDHrw0EBGtN+2M6PSCystSP7joOYQXImBytRdZWwHRZSJ8ABREN5fEzNoMWm6iY8fyu59n9v'
        b'JPtfykymCtHwDPr1x/Y0ZrdWhh6rw4lZLVbMmmHbE0esFb/piSTEsoTvYCsU96tEA3/WYU3RjxlryVqzBnxOMgk7lljcdIidygR9Z4L+63AG+Df5diK2Yt0XS0ye8J0Y'
        b'1aFDYmNi+xnNcYbtZnqs8AehxjZj9fO70VEj5GKK0rmDbUR38a8vRsN/ZP/V9AjVyhypRzXEyyR81LM/NoExOTbHn2AEe3K3/lQ8ioT/GI9iADvxk3gUo6tRBaNwUVoc'
        b'yJG9vXlcgqO5LT5ndHSe4aoMl/N4bIo/37wtf9S8YWXz7o/H7eCPr80TY0fV+Kdjc5xir0ki6cFY7FPrvKyqczIBkhP0dDw9T8Nnfn+55nhUs5y9ph2pOrWPTHx69UBV'
        b'vbWneVZKYnpW3BOiJvzVNiTQNsgilae2f9SE51VNsMUjoMhEQ0DOfVVHvn+3Gfl4xqf80Yy/pKrbMSQVB2lKiU8lkSfMo9enZmWOivn094ggA8fweWr9r46mOLUYRH9r'
        b'3jO8/6iy11WVmY5UttBn0d+b3wy/P6rrTWVdGTjD958vtOyPCn1H1QGb0CdEjlJGQ/m7S0aLBHSIxOEVntqE90ZPGInJQBft36IOOWYRpNbM1KfWeU1V5zg+fsffrFHF'
        b'GtZHJ2FjU2RqWlzKU6u9oap2Fq4WP0stIEnqZtVHA7787XHQUbUqJilVEffUZt0c3Sz88H/VrFHQVnyEWMAVMAWCeMFfDBiaIBfcErNPsvthWza2jRBbdnRS0ih7B7ZN'
        b'JcXxtheVhelJgUeCoxMVJHRMMOpQYnKcV0ZGagZ6PS5FZXWJiU7BgdHWx6lsOY+VgoPVpPDxahJTSDAQRSZaRYnodZuRWCGjTOyPFcKHCkpOVJCQPE8wEY6yz+AJxGZX'
        b'V0bdPqMV+BhuUKAkDyz5E9ygaCe7g93IKCGYhBZOsQQdLecTLnKZWx+lE2zfvSvh0y0aMFnYzAsr1kxSPCLGw0p8fOQAip18HTAaAanUcr8AJG8/AspUB2QiSXxYf5FU'
        b'noWjaqfDXhJBAJY6bfKn0TBGQlosg4VBIaNsDqBqttZuUCjMwpvCLE+Qa4e+plWjepd7+4L2+eTNRwDHIbACFjr6BoCe4GUOsFbIOCfrzIENY0le+TCknR/1Ax023gGO'
        b'PgHLl8HSUBvHAFtlCSvgZR61DGuXeyMtjAVFm2LHgFZwYpUcnDTZxDFg/w5dWAXK4KG/OSMZQm5kPkTYQvnEKbmHl66Y42OfwD3wkP9IABI8cjtWjozdIz0Ge6M0TYLi'
        b'E4s87wkUpej1uJ1feZWe0wHOeou+spavX3pL92fJipX6guD+FP2FcRuj/TUkizzGT62JGtzy4y8PFt7ec12477aFxxSX9DWh/3qtN3vms5aXVh353dlivXPIwRmGk+YM'
        b'rCj+4aRb2D+/vqSovv6qYu/u9ov1nwZebz/nUKrv12ww1WrFw9Tn79y48pLOc1sn7lxsNSnt2fs/il68K78WnyTXIHqlN2yGl/we03mFsJiZZCCEh2AJaMvEpj3YBntB'
        b'i587PPC4EspY2onmgm5QQ7Frx5zB+ccyscE8UKcEr5Wl0TOcY2lOGNAUsEsJaRLACxvIAdwE2ASGMZIqPUyFpWoHR0n5URFIjS6hB7+gUHkYAy+DKmbSWCFsB7lgDz1p'
        b'qwrK9AvWHpX9hAM1oNofTfyIcvJYrDwVCVzTxl49kUrORDRBLLxze/6TLsjsnpiNtTkxidKAMwEgfezhWE6H6HjcQ4lA+P0201Eaxaiq1LwJH2veiPugBD31MdadcHic'
        b'/6Q7MTl6ZU/Qnv6gEf/jEao3PClCNcs8agYXBCaubG8WKfBJzu8LvCZX4WjTkvib/hqMpIjtK8+W00R74IDAQQNUPHogVwSa4JmnhJh2UTrI4kOf/zyJzG6xdJvRI/pl'
        b'UlyKMtbik0JM4yruS/id+T9PCpMj+/EJ0/LESv9/TYgwMDRxIPwZgQJ/bSbL94uWxd/M6vdHK3MqazP86gjnfHzE+3i2nFHCPqZER0auT01N+qPBxG//9pcG896fOCGg'
        b'tY4aTdxqXDc+sFQEMkSmUsbmVoaCpH5WbIF2vA4/zlyhCI2zAI0zR8ZZQMaW2yUIUftMJa3R44yPIvHWM1q+mExDs4PLXnZrwUVqh6ZW6DWGxO1Cw0DISJg0W80FUbL3'
        b'PXxpWA0jmAsHwXm4T6GToYmfP846ghOGxGr/wEqEMwVZaC2ISkpYOYfJckFfwmYMDiNH+jRGD97J9oN9MX7ocyCOdxW8LNhhBcesW6ABmkBvGjE0u5hyeJ9AG0IZMdW4'
        b'GhFjjYixjRGB04jVt5LG21svApdhMzWwE+t6BDhMPCRgPWzCEFUl1qcGlClZ8sJtWfwBadPKMEtscMCmEUbowIIOWDeWRggpCkp3lKjF+tgoJW4VVj6gkD84JYfIdR66'
        b'CYI4mA8vh5JC9ZBw1EFOJx18YJdEyGhqcKBsF83wDVrWRs53oEAdoZAFR2FZCnUS6DVxwcY2uYOzh5jRnM2BVtg5gxToB6pBP8zXUwf6oo3yAo0u0gr2O8MSh0Bywil2'
        b'lkRwxrAhhQRdmRUI6/xgmY+9IwbwlPgHggPj7JXBhuzmiWCpPvsYUUqVROk9QpSjSZJVxST9s+T4WKYA3GPNx8jRMZAQndl4TEOM9yKvqKTIkN0MmWbp+J0qmKof7GBB'
        b'mS6oICM3Ex4GvSqMTwY8yoLSHVNIcvRNSF44a+cLBmC+ar7IZA2Afjp6/eA8yCHmL0awCWB8044UcJ4knZ64wlaBYUVcxjIJO2EeOEMmMEkGO/gMd+AibF3HOrmxpCg/'
        b'WIBTRKlAlZKtLDgc4k58eUAtbIAtI3hYDCfFWavKwTlyf1nccoqJhYOwWi0f4xHYSvyoKOm0pYHuEIzLPs8wk5nJYBi0y0Xk/ShwHNTREtbB9pECFoF8QkGTYbXGCDw1'
        b'DhRjhOpeeIi8PA10JdnBQtSbNidHdWRsVgiNgJJjByop5NZXm0fcwvwdJMQePAjylmIJ3VFuGwkOBTjKHXwDWGYK2CuazQZTL6RhrBv4+8jnwrMj+RWRzHSaLt8pCzBw'
        b'CvRrEY8rsYQb46KRhW2BYjbOzm3pE7OhEfRVDqwhPmByetavGeKEpoVYOTFHAcVkQViHizaBQtCWhfXicQmIU5Q8nikOVm5QKz0Q5GjACitwmYanOw3rJSrmAurBWTYq'
        b'ZSUZOFgcB4ZV7AWe45TcxTaYLL/YHeajGJiKfWFQGmZhw7CIjPA4bqMaC4J77REXAp2JlEVVIsI5rEQ6omkrYUHzJlBOmUYVvLhYBeuzRowbnJ5mSHyAwkAb6CJ8oQP2'
        b'Ud6AOMNucIrcRZVfDlbxE1CBTZ2nEJM+RigtWBSGCHkqZpfsLJwttBR0kYZ6wWFXO5JKUBiN8cmIKcJa0JdFE+LVgkOIyLwd7AO8l+K4ELXcDgO0aog1/Rjs9Obxbxmg'
        b'alRGOpEm6BpPKa1SJMIPBSEFUpWM0W0nGcxl6/C6U+NlaoxMF+QjXjZBQ87RRd3IopVVArs34/BR5ZvhSaRM6K4iXVsXs0MBz8F2ZzEOscCAiq2wnXB7cHwMyIFVYjEo'
        b'QUTJ2M+EbWRDmxsvZdCLzjljovwHNoXReEIPdAWYVy7o1o2SFU1PpF+62+K9ktmavjgq6aKpKR9eyUXGoNHZGro6yt9JT8EHYponwa6MUZ9ujEr6wXn84zGXiMSIf0yJ'
        b'EIJUSg2sUqZpxDIrEFdN52JVx5lECOLVSnbzIyrlNc25CXEpcVvTMjwKNXlOy+0xYbJWkmEal/i4tk8DnBONH304iNX8rdEqRR9WCdCeWWWAdH1XvfUz4SlwKhucMhZ5'
        b'bWbAoeXG6N6xRSRmmM80UIA9v9B6rHJw9CHYVN/lyxxWeD9hDsFwAujhtFgGccl2WRSsHEOJphDp29hGKQ+e4QCLR1wYGLMwITgzJznR/TcPkeJl1N2hS4q4kIGUDxbo'
        b'3YgoNpDf9Uh6+6edt3sbmvVkY74OFolzpy8pto/dKhrbnS+UOK8RBj5rvW+w17LCOqBiSqS++aSK+d4NTi99af/aS+mTv73ollrWYPVhz8mtzy35KPbkquqSVWB6+dyX'
        b't6//R/VC6Z0Nn80teMjVCfzTGwSOisnjHScb5gleyqn42lJalxEaOPDbxfG+E3d3bn62VKv9H667NPKfeSX0tUUJjUcu2a7/+t7D3gUDVzv+Ed0/mJm6xbMtoeFkTei4'
        b'iNTgFSdOHvWyc9fNDrM6fzW6zX9MxXtlV33Ctt+Mvl0j+2gbEB89pue2/0Da647HC+v2VzQNFb2f/c/gTvvnkxcbHvrBS1xorb+zxjPc8vo7n+8+KNPqfvBm5ulD42KN'
        b'hQEpbQ9cTlz12fR+S1n9K4HhQYqGc9c/jCl+LflYyallAafrfp+02PWaxu7nNLK/qdnUqO8m2fG+7P3WwuHa2SEl3fFZ+sUbX//5flboB01F5+Uzg+7af6cZPHWZQ7vo'
        b'7myfrZXfGN2yyvj3ZN2XJxwY9L/LfpcY3OYT0TQ8DpzOT9A8q9/Y/PUXG/MygiSpwbGNU9a4z5px3qRCtHHNVyfn/PxCzbH8hJ0J31fc0q69EnBojuUbEcN3uh0Tll+/'
        b'nrXjOafp276ubD4w29bNLLwy1eLg3K+uvLPz/KnTywI+e7Dv/pSG9HPQfmLRs6775z/jFn+nI67lRd1PM0CWQ0bT5pc/9dWdI9vl6ZDy0jPfj3+vYH6TdbhLgpuL8dzY'
        b'TS/9+EJdliS6cQJ81/29Ge9uB/c/2vngrS/udBQ3aWRtb17l9PGc6Vfeud/WciP5Muz9NeWFmQutBR+bfb1m84SSHQPyfo+b05euLO3bt3227vEdD7xTPui4mmyp4/aB'
        b'0SCr/cOhPvl9p8s7NT/u+ML6+NSfkzwNh4b3mayYn2fdO8jd2/KNcErG4APZlt/rItNviMVfhQc1/ZZ766cvvDdfefB15M9xLs/v/l0+mzqLlUbMwPs5OCnE/HlPGot2'
        b'+7YgPsP6hnlSWCyPg8U+mjZIgnYQM/qgTQCOxMAcYmGf6jRVivPJY6AwknAFjGQ8twI2gjLi8KO/Fsm9/o4gXxk2QhhL6swA+WPUQka4mrPjYQUcoB4dg5PgMeqRxQgT'
        b'0P5VzsJ9YD96nDDcE/5StdAIsXNZ0CjlM+wiBrIHFTMiF2mCC0gwigQ9fGLMOivUmSy53Cfd30kuZrTRY9aa4Bh1wtqbOEHNHYj4Am3ZqvQGWgl6afV9oGsRn0JYDi9S'
        b'd6D8COKYsdBkJ74TAjqVMR/WZZiRYTBfECElsFwOVliEsh6p4Bx5Q6KXgL18QGsSH/YESTt5pCuxHDhAYpPAQzPUkmKbgZPkRZlP+EiYj3AHHJSg0YuPhXAWnFX4oxkB'
        b'Q2Af5nl+IkZLxqFdsRwcpLFLJoFeJESFIqms2B7JPuAM5woPAOoxEwgvJPBxhGDFej6OUBTIo4cSF8DFSBybBHRZq4UnOQ8Owg4yxCnLYCNu9inYqQpuchRNyWFyNxpt'
        b'74fQEOMYQGiChLNBm5QF57bLydBagHpYqgyp4uNAQ6qYbSf3UpEUh5PK+/jAfj/ZdI7RSOdsPYVkLKTTlvLhLCyV4SxOsGQQV8LmOOwPk66QUFcjrXAODCLhs5kWGq4h'
        b'BafSAm2Iy4wI1LPw7DjQRrOUNruDOj4tceIMI9YCdvLuYKHwMmyQ+gbYiZEKMDh2NwsqddHwYCFtCygMxfJ9JKzUdPRz1MISz1hwXug2h8basUB938fD0JWhLvrAXoyO'
        b'L8UuMT2wl8LC+2GnjzITM41J4b1KFZUCdJOJmrFpmSqUAyhexIdy2LGU3IzbhQSMHofA3TOUuHNYg4T5PYTSYb8QnpQitTgHdFAsvHq8p35YQZY+B/o9ec+4Qdivnkh6'
        b'HiihvkBnl4N6ZUrnCfAg67nDgQxsWsxcHKME1CUSP0WRFwtLQaUGdchrB7VCVcyB8RksOJkOD5JVEg9y1ysCYZeWMsrSeAs6F3WwUYam2CNNGV1kiq4ORd77cKowBZtB'
        b'CY1SAArn0aW6BwwbqCIUTEbTCxphLkdWyZY1c2jSYBqfALZZK0MUIFHkKM0aPBiykqb3lUyRsxMjwFny5rwZrngG1/g9FkrAXQj30MA2A8YLpA6OoGopH0rAcD2gzNIR'
        b'5EgxbgNTHVLJLqBJ8+Mmw5aJlBFXuiEdUhXXwJFFahu4wGd535s8jXjtDq9ShSJzgM0m1AVpSBNWwxL7QFgELpghvQQ9IEXrFtHsQVhOZpP1R1OLn9iP/rbKYSGJwtzJ'
        b'weZQ2EUmZiU8o4ljFuGZL4MdoIldBg/R8ECGkaDNLsgeFq/0ILqDBiOFlzjYH7uLRscqNA6V2sIyNFSOQQHsdNCAGA2u1BgOgRMKf9SMA6NdRjV2Kj1fT83C3pvUm3kd'
        b'UHNo5hDjPwKG5Cb/23DuR7x5/vvgx9e0yEEzMQIS4foj5s+dqjO7tdzwCbqQxCrAv3U4a+JXZc/ashOJn5WQ+E/JWG4POQjET1LPq9+FAu43TsCJte5Z65qw1qwep8OO'
        b'ZcUc9rGiOYdN+OzDpsQbS4Z+G5BoAFrcWFaPlaAnx7I6Eh0kHOs8NONMBTp8fARz9I3wIf4x43CJMpKwx4TlYyxwYg61uXKb/FFXJTwKkY5ziWODwsNxZFSoIiG8ppm5'
        b'NTYuMzoxSXFNIzJz6/poRZyaV9bfSECElBNtVHaGjFOesUrRJ2vNv3DGav7K42esxK4H+pHSWf6nlJgnqTBIo6h3ZWbCOl1791VEM5uIlrmQ+WaXiIlK+jVmDMNrlKEM'
        b'GFBFwnOVYsMROAovES1FgCSEAnpzreGIeYgxBc1CUKIPL/N4LqSN94DekXh6h8AlUs4xpMvjcvTgSVDNlyN9rByYY0R1oouuO1W98xSCYhUeYY4QVoMjhll2hGst32CH'
        b'PYp5i6eu6fI0PEgkmxYOa8QyUcYSS9AFmskZDazRgrXqiCE2VbabSwb73LNwMBzEoPLBKT9Y6oAEplAvcJoU5jJjuTdfubulmJkOhwjwJ9MIcVGS0osm9ErbDE7DFly5'
        b'jdohyFpQL9EFPdrkpHc3rBmn6lQE0vQe6VVNGDlGRhJNXsZWWEvmW620MD4lBO5bqR/LxO+WICZdDGoITSem3P9CpChFH6NM3olASqLhcqOdqbffb3x+k8nUqr0OX+ZP'
        b'z7TJ1DeeYGNgUHl46tJh79ef0/FLj2Tzpi/Ks79r1Lendv6exn25ucXTJiT+vMf7yJZkveNdO3e8fvGziZNKIwuPxz9XO/aVhqMrKpwPfHuuxiv7k9K9P3ibfmjj8NPw'
        b'7wd+XFeybtMrP0e928sZmtVmJoI+L+tI35vdy+84fLfEOGKi33eZ2SFGr9s5v3LxC98p087qKbjVXfJn9l698OL4yan5V5bkaaz+cn6mxK15nq6v7OxY/6T2m+11H2+c'
        b'G6HwH3zjZEr1Dy6fDRV9P3DY5/p596CZ/oauy6vGWYj6nk169cpKr1euLNz+6qr6I62aYXWzZ9WefGfScs2O1z7+affNundXuk9UdJzy+8B+1m5n1yu9ye/fWiy7FDJQ'
        b'fnBV7I2d1g+PWS0ZPrwLTmz++p2pBwcO/jrwil/2oaXZDmOyL46/s2reT7ZdxpeGkvKmLHjL+MuHtgu1ptX5jJ/y1cZtq0O946bNa112el6cRfG+jJtfZJfMPvYLcPKN'
        b'8NH//kd9951OH3qXNMq/PnInOeh61x3tuN1w9vqEj7+xD7P5ebfU7eN/Tfjsww+zOiy3nnjrA6NDik6YGLSh5pehK29MK28ssZ2zrfz56Z5ZGXXtDfeq8gd9J4f9ACof'
        b'usU8M864EXr99GDyjb1v1ge+YDAu6B9XvK5nL3nl3ZO3Dczf01z70etWs55veDXq7E2PTRG6V/6pue+N820gYM70WwbRX4S6vfdD3XzN/uder002j7NQ/OQx5XmDh1LT'
        b'2+JLu/cFf3b7+o2gZQcbrpU0dN568Y0Dul+9umzicPPVM+UpZd8evb5q6yfvn0he7lcy1dvl56bwky9nl50bCvz8jQDD1fB2uPxCTtilCalSuc5xQevzO/W//l2cdUxc'
        b'bXdd7piJrU7wqD/iALzztGXsaPfpUb71sGMmkUhMwbAIHmN5Z37ek3/6HF68gg2BgdojmiNSG1ORbEr4z0l7WGXnRxzJR3mRXwqi79bJw81gvUrJwwreRSRg4cO3bHAY'
        b'Nqss7Iidtj2CMxDBfFKJOeyDB7G4rWm8bpS0HSEjAlwqaIcFfkFYgne13sx6bojjBVDYGMlL9qASlCLZ3gwOE0BAitZGFbjlWBLuM45yjkSWCbBGCHqtAc3J4JyJdDNb'
        b'DxxSr4zvnNSQg3lIrzlOhLWVa0ERhiqly5HojVrZt4WFRxhwiDoG7I+ALbwLPdKN9iJ2bwjaiZy1aLsdkg7BkAWJkYrxDFpbOHB6NtJXiFw5NC0EtDlRH3vqYZ89k0jO'
        b'SANrWY9EXTHDjVkQzs4BrQvJ9yYzYTGPFLAEp9G0rFujjPfY5TIKhJG9SydW4CUOoLeROgcug/4dJGYrQ6N15sIC0EDc5t1gLjyjiiZLdAdDmEvVB1C7mgzBeogjqqni'
        b'XvnAy1gFSXKkfvdH4lDPeY/5EX95O3hRaAALQqk4Cjq3KEVlQyMqKIcsoSOYu8RHFWqQSUTqAMgDVTTkZzPoWDYXbdM4Xw+GNwjAKRYx+wbQSE8IKgyQtA06saJfihVy'
        b'AehlQR04R7OQICXpgC4sF0gdAzLoE5lo9PSNBBtBJaRq13jYshRrjQSQXrtUzEi0uVhYvp1Ub7JMA/b4eeDAvGqhajG0ZhoN0HgSDUsvD/ILXA6PPoLxM3IgzZi7HiMB'
        b'wVmvRaNBfkgm9gf7CS1oZkdHZcMSP7qAgli4xxI1lmgRraApAJ6G/SodFWmoHunkLY8FsHIkunCoMJKz1fOkQLbDm8Fl2GU8KkgtPJxA9dETaLr28PA8FTgPtbBRuA4U'
        b'wsukb2GgGhzll08FeoPSBlkdY+OEU7zACYrIOO4sVTq4wI6VDCOZxa0HJ9D8YZEjFK3I48rbi6LURBPi/aIzhugV4xEbq0bEBXukiL7QROE4l1r+HKgAhxcQhx7QhwQB'
        b'jGYKjNLDaOMidaOI82qxIZqTokw5etIH9screaKD7lMgJYGgM4KehxX7JI0S+DQYRHtHdVYLXKbqUQehZlAE+4l8w9c6U2VLhoUi0CsEx0lR2qbgCC4qCBb5O9L8nuBY'
        b'so5AMBkOL6EaPjYpKwGVjBjpVes4C5g/T27wv6j//E9FdlOP3OakdEz585qQTF9G9Asx+dHjTDgzpL+YskboP9ZksLZCc8TgzDFYJ5FwWA8yYCUPJmpIMvBTYhJJTYIF'
        b'+YdIpH8oQTqLEONWHpKIW79znNbvYsFYpNMYoDdJHK6HQv6O+HeJUMLpiGUCLaJlGXB6BG2C65OIKYLFAOloBhxBoOwRshKBhGNyuFbhw8dBG0QT4rUeihEhasr/FAKF'
        b'13ocRw0481e0Hutv/gz2hHRDzgUukY/NwF5ZGdjnMgPXkZGEf2G4S8Zs/CsNe/kfRL+uafCIi2sydQDENak6FGEufhpbcjKS8a8F+NduBpuUVB7g1zR4t+xrMnVv6Wva'
        b'o72UsdMYcVIizjVkHOiw/x8fI6j5CH2G2rAAe/nkMzRInI0OJkhrjoungd04wf/NXz2hbIxMYC0gETYcx4Vj1YaVqCuzLDMOnhTGoT2q+TFvLKyxEscpPMkkoJkyUpNG'
        b'gSReovLN4v6Ub1b8o04aePeUMY/6Zm0MzMLuSvDYBHDQ1Xn6tJkuM1yRHt6VmZmxOT1LAfs3wXbYhYS0biRlnYPnYY+uRKalo6ktBeWgEOyHB2BNyDJYCQ+uEDGwEw5I'
        b'pR7+WVgEgQVSa1hitALbDe0wDBfnmRMgOaZBAAeTPbMoWvkyOIu9RmD3dBfGBXTDvcTXxwvJoOR5u3SkbJYLQG4GevEsehEemp2lx2BbubWWK+rFanB2GjPNZQKtsgpt'
        b'OXx9J5AkoHwR1+gD+0j4Gic4AIZdEfHA4zNcGddVoInq833wJKxFddo52U9BL7KMkZUAx5wFncR9BOZZg3ZXMcPsNJnOTDfmU/fAM4sDiV20xA7kR6BOCgxQdSXoRRdA'
        b'q4OnwEGk5WMBcc+OGcwMw8XkxYBg0EY7CPNAJ36RY4wMcYUXUIPIiwVzQIkrou/lsGcmM3M7r9tbLVfQDoLDLvxrLHpNDM+StyxgC+uK88B0T3BDUmQX7KLRZZoXxPDt'
        b'RL/KNEATGhYwgF40BJfJeMIG5xRXDYYJDp3FzIL5xuSgBPtfdNFmalgwRl5SXJU0nLxgsT0F9OBnQP5sZvaaTOJAAvatD+GbdxDmkAmfwk8c6B9PLfNHYDWSInqEeKtf'
        b'4s64a3OkY7Nh/xY7MmPggHWGOcdPGzzrSp3amlGJLZhuQS2oW8gshPlgkI+LE5dKe1YusEC96kVUiGdgRjB5EdV8El5WcASp2rCIWYQEt0HiNeGdBArsCF1mJwtA01w6'
        b'AVqwl0y46WyYr0DzvSZ9MbMYnATddCD3ozHNpUMJSxgdOyeN9fxIuk3iJ3xiOs6WDTrBMS/GyxieIb5LxmjJ7yFDif7vAbnoRQM6dbrZpL401NchhQiPSuQSZkmYJfGa'
        b'gedFSIgrAQVgH+khXki4CIFyOQxlkbcNxoN9CgE2nZxfyixFgjQ9XqqFJ93I40i36Ib4pxsM46lvQ++mgko6I/uRFnZSoYGXBOjyZrxNLMlkLp+nxU9IzXb65lxlra2I'
        b'/ol9Ig92hMEewkCm+iBJrw6NLe6urgjW8pMCTo/D9LOen9AFsaTSaYh9VGIbHrMNDPsyvkisJB0GNSAHcZoSL2+eXp2clHyjhCx/2EQ7DM+uhjiylCjIj/HzgOXUh+cM'
        b'rI0kjc6D3bif55HwjN+Lmk1Xcc+CRTgAL2MPWv0Z/zQfwjZA/nbszkVaC4/qk8FSrg/QsoG6D7akecEevIy7zAOYAIwVpy5TOUgVqaRk5I6jRKN359KJjQQX6atnPcAJ'
        b'2IOmVgJOBzKB2SCHvBoMTq1RUpIryLPTAMeVU5MMTpNX5aA3A/YI8IeWICYICcKXSD8tEcM9wVOTL2enMVm5yKqllOiPYJEd9qA5BU1wcBmzDAn0hICloJC+hqorgq0L'
        b'VQsNdYOyEJgnAWVSslJB93JmucUkssxSApIpJeWstcfUgJtag5sqI29lGIICqRBnU2wKRj3rR8OD6cB2HKgm85EDj23Br83lq7MF5ykFnUU6YDM+QwanQFEIE5KFGC7e'
        b'PgXT0FCWLE2ks8LvISoyaDYitfrBZm+pmERf7gllQjcgdoeJyBNU+WMFnNKgauEIlHPagVgHfn2ZCeyVssT8VR7GhMHeOYTtZcUEk8dBXgZjtBIMsKRGb0JBaCXWwnIp'
        b'mkzvpSuYFZKJZHAit8+hDXQOQl1V7lWIZx0iLxnCfeCIVICptiycCd+wjrh7bTPZTahbIGCMJke44ReKYS1pGBqu44ZSNHsa8OxKZuVM2EMIdT7AmBU6IOAo3CdAmtyw'
        b'coObsJiu5jYhUnpL8KcL5quYVfNABaXCQ7ACNagEzdFKwWpmNQtL6XSXwsqFoARNgJvDGmYNrN1JvnYEp/HhOurnLD1HxtEeNtMFVOcvIXn2Nu10Ypz8AXXaRXrsBVCF'
        b'UTPwMCzEzowF8ARdpoLdsAqVPdPDjrGDuSCXbt715rAvBA28z3grxsphAf2ye5IUVqE+h811ZpytZpNWb4M90bBKTEKF1dsz9rDanvayCTsjhYhwfpKz1ow17BTLtcjS'
        b'WJIAiymX3CYm4zOX38kHthCuP053M50qIzhoN7LvRuiSEQ72wSXj7+fDi3gt0/ElNFcI80gJIdqgmNLHXkPOnKXvwza0b+MFpos2tyJaQxClP8F6yg/A4WXkCT90jyfq'
        b'Ji87DZirYqs14AwVRppW8/MsmDcLcZhhnqPAxijSyh2giMoOiOscjyX8cb2yjGOggXAX01nZSkppQfSN1vtC5UofBEN05yxw28YvEI1FjOFi7NyI7x/TlbPkgQgTeMiP'
        b'pDC2BOU4/6kEnOVATggs/IyIlBUZC+RaxNKydgbHCM0L8bG8//Uxc3m/ujU4eZ+dBrMsKsllOp+h8PP1moyepYWYiYqyD1glpV967jRgLENXINqM2vGSeSj9MmuZkJE4'
        b'fyFkFkQlHTcyo1/uWqrLmEnuaTDOUTLWL4J+udZIzMjsn8eZ+5LyIy3ol/JF+ow58yzHpEUlWRnvol9emqbFGEWxLKMXZW9s6EG//D3QiLFBOhqqyOwz4yX0y9Msqn2D'
        b'Atdu/5PzeP7LcAEjjFqFKDcqqSsEfYkdnKvCTBj7UMTMzKPWDsfYImUxdAm58U0cKsJyjQgX8arPFPr0d+morWunC3Bbm1K9mc/q6/C/l+eTCraF4Z74k57cD5vDfOZK'
        b'/t2bT9nCQXAC0ydaf3b+qUzqktWUJ1XBo9lomBnblK3M1nmgjo/WSCSyLtAynScETXBandxmgVaaY3H9GMbeKAenU5z76mZz2tO8ucaMjezfuO1mflLvx50aVeEn8TlK'
        b'Au/USDMejmQ65EEd10SJKbFxWzPwrvKkVIeuSEPHEhpjwmR5EPYHBmfYBSL5F7v2EkfBAP8gtDz+CKV4FtZLPRHX6iTtL0xeyXSt/ByTmXvksrFoUgIDE9PMP2cUJ1FF'
        b'B9/+ufTAy4FGy432/bvj7rn6E0139J8bp/+ZZvoz7HP6CaZeTVavOC32LtT2eyNixgvroy2jT/tkydb0f331O/GlHLtJz3Q8dJAMZi7/8OJPRx7ul38e98OSZ3OG2vU9'
        b'q/dPDrSusJzX8pJ1y8vxsS+Z9B5Y1Vs5+5OXueJYzbjuCRM+0ck8MOdcyfXSeZ+s+3LNP8/0TIrYMWGBW7bevE8mm1mX37TJlr34suEsn0aQ+J3s2QXbXu753OKNW3Oz'
        b'2TEv71o7xeljrWxjwSfmnZWLLlxqf296yk3rlFszv44auyVd96dvGd352zdds5l/d+hSY1hWQvrL7+X8eGPfus07t7zrWb15TLmH+605026NTTb7UPu4dtza+VN0Jm45'
        b'OThTf7/slHHEBJfl8wM3tbZY2lYesZXv/6jo4j9vLHOJWu/6ynOn3sqa19KeWFWxVc8wfP1xha+BV9gK7Y6wr+Y07tO/Yf2yRPeVlgcXJlVtjfjgQXRmeeKBC9Nranz8'
        b'Mm61XWxe73rodvbSt06seutAvWLMLr97794RuYQm7doWcn7SR9H2vvNsd74S9pttr83Jn3QUsZaGz40vviZLfmNm8q78ebFX4b0jDcNe097KTd/8rwPXyla/WRJxXnt+'
        b'dNaau0U6/2zy3zQrJ/zDIxdrbmzv257Y8HGLVHCy8/P+vK3RHb/1vrPNZZzlc5s2VMV95vPBq32t2jHWU1clHt58aFNN8ZGGG584b/zO566/Z3dOwcEDqbOsnbL37wsz'
        b'uf1h9FWjX3Z5ZRW1lb7iV3kpS37uclJEwStZ8U7vRyjm/3N2wtvl8vZXj+dW/+D7/uv7fVbY+OrDprtf7GgzavGOyLn/mu3Dyp3fGk5t/M5w0ju94m+2ySeLvt55ZcXY'
        b'4M0Jhxxt3nbce+zl8LdSHhre/uWH8E/nHDj9ReKLtxp//23Jl47Ppg73Lf91xa+5dfo1R34RJC+SruwqlmvTE91zXDo+6EWLQMSIQClo2cFCxNV3U2++AdjoDktosCEk'
        b'IuYKvVnQA2rHk/P4dNgZ64fxtnY+4KKfgy3LSOFhARcC95Hz6rRNSNruwWnZke6xbIZAi3XZZkhPufvBfpkdLANnfEUMOKMhjGXBsLmUZsgy3IRDzcFWax97HyEj3czB'
        b'w+PW0/P/JqT4XcD+bYtgMTHgEv82fXCINrYR9gK08ZY52eLESU3CLBavaThATvfDI0HniPcaTlgunM2Cc6AR1JO3vWGOEQbrwEZw0cEWu5SLOXgR9tKwWNvRflvkR/xn'
        b'MJAHlgjHYP+eengxk0b77FvjF2pPzFWbWU94CQ5Ri0api5AkMZyAU6ypJTGscZGP/z8+1HrqAaTk7xwLX9NSxESnRCYmRyfEkdPhBf8xr4fyvzAdH1CS01r6w3G/q34E'
        b'3G+qHyH3QPUj4n5V/Yi5+0Kx8D75q8H9ovqRcD+rfjS5n1Q/WtyPqh8p94PqRyb8XiijXjiSb2X6WiSDCPat0WKnCGiuDZqbA+f3EHI66EePxFAy4Oj5th5rwOLjOSOB'
        b'HmtO3sXPy4gXEEc+aZG/2C/ImuRGx9fk6r5QMgW9b8kKv0L9+4W7hfronjGOUx55Cq4JEpMT1A6Z/8osmao8aHCBH+KzZHe8uf6Js2Qmx7TiCT40ZL/fC8oj7QLV9k24'
        b'h0Fcw2SdULI7LUagtovjurWUuzjGJashFlkeIMbFa/HnjoJCYR6zU7hNE0PBwhkcE55ldgl2CUPUPj/p3BGfOaqONlXnjhMDn45GxQffqA1cPPcX8aiPAdPwP+6xukWB'
        b'RERgLThm2BmPQJR/bFoak4VBvem2VlggDrfhoY023j4h+Chiv4+Icdu+TSi2QcpOd2Jc8CShAvvmTHc++kWUd/SVeJuP7kStfaarIqeyKd9l76m6c0Xn8iYfyrkR7TqB'
        b'SXlG/MbSbjlH7YAnl272UyLfxbB801xuDGyDF2iuSMTMMh8BvzNbRwIAHoS1SozIE07Cr0ljNsTFbIok0hZZ8DhsyJ9b8MxuiT91jds2KRInTIjEoYFGfMvUSlYSP5uo'
        b'RvrcKOI2UxH3ePRpNpbv5v5p4mZydM4/gbxxCIlIODgdB+CEiMwdvMF+HkPymFMYRi4FwDIxPqcBLSvwCcFYKWyAx+G+LLoNgQFwws8eNMBqnHJvv5ARm3JaFjb0sLEY'
        b'DpnYwQOB4PAmjuH0cdK5UkIzTrocgQpdkUUlWbMbcI5w4m1xGhx39fPHHqf7AjEqThLEKdbsJK+EryKQI29t/agk+5jtjAKL7OMTM0K009IFDFfks4JlFocT3cAunGCO'
        b'9NqWRskMxvkwSXh4bzgKMeaIWWClK3t/5Q+LtRgF1gXuzd0UEmb1TNYPWwSMQMRa7aZxtl9JJWhLmxrvqCTHXaaMAovblRu2fszFO2I0qPSqNXkuOUiDrEw/myhZ1PZU'
        b'+pzJuR8+FgXMxFBmnTevKbBoHp0T9fGn3KXDDGPNjP31eRIVY/WYBSFh2pu100IZ5uqQ2IGt7p6uwGJB21uFxIR9ygZ7ihiaWp4TfHJPg+xHBPv9+2DB27ovf9Zs/zJa'
        b'TRosN63vMqnX/r0VbzMpPyDKYeRX7oWS775dnPS2cMtVpNQwtpKF5Kuu1zaWsE2tSC9lIhZPJc1Lm/mPkjeZb+8yzEfMXrNc8l2e8KWSN4VNzzPMx8y+wxTcB1r8cMY8'
        b'H3sk6eTipeWKRhqUcL7bVidKP77JKE4jbhQ7U9Mr+LWUdxbI+hI+irUeulF71FY+7xuZWcWs0OHFdpO/PsGtWO3JpH97hLv2vuB4ecWwRnhjfvjNF1p/jLWa/tZz92/f'
        b'++yNsp9SdPvLKm/0V+yZHG29z2nW2tvxuf6uE23ezv/SLzTO9KuSgU83Zs5/aHXw4+1TU75zdU5cm/4bnGR+2sTtwxuitKv3b+1lXtRf/m1RvPfvitcsGz+YuOSgrcvw'
        b'rZrQnvEuy8WT1/207fDC9tbbVR3j/2W04+1JkSX3T93asWKWrrt3qdwnxlfuHXUNVIzZGTf3y5srF30YfGX6lweH/SeYbeivrMibbtEebLPKc6OmFbx6+R3PT4Jnn599'
        b'dbql7+dNBb3Bm42cTuvEf1HdEhaxTPeVy9M6NovfGdjQMB5a1b/eW38L/ntL8e37OgWuu1oeRqX/ujV9zf3CD15Z95r+0cMW68aUX/Oy9xioOnl9pdm1L4vdf3L/7fKc'
        b'af6/fPvx0Yc1hlqBmy7dVLy25qOp1yd8bHjpyLlZ7x/6Ivzu0Fuu2/Ijdoi3/HznTvhXb72+qSvlnzfurXP4svxXz/rLSf6uDY5rLDdsbz1z0H3ccNZ79Qrtb7+a1xBz'
        b'+PsvFXI9IqPqwKZAPzkow5Kmg42YESdwtqBoLOWzR+GAPpbrtggoOFECKrhUU3PqHjUAimANdkAJsGcYYbCJCwvOzMwm8mAq6IJtRIwcl+oDSzFCTQKauF3gxATiWwNL'
        b'wmwVmZvHhW3W1gFlurqwW5aONljYKAANoIo6FsyyAnlK2VkImp2w7AyPgWoic4+DfWE4I90ZsQN2Bc9nl64FB0iz5kwE3Xa+WjjIMxFixcGcEWg3JTJ3mKalUrYVwqKt'
        b'WLSFZf60q8fmRCCx2DOFr1FTivO11tJYKLBxK5GK42VyB+wGI47iLEC9LvUiq4FdMM/OEY3fHrkaVOUcKKL390lgMY7XU+iD03aDZmMp0kVggzcsp25MxfAQKPfzCYAX'
        b'YBM/yhFcHDydRl3qD4KBFYgVa+CIPGS7w3tdrhfVBNpA6yyM34V1oCvIX45mbw7q7ZHg/9JU/3ecmkfJzCO7H9lCG//CFqrjJyTROqmEaoJ9vokPhR6LZU8hkUexhElz'
        b'2HF7ZEhWFRIZVYc8K2aNcAY9IuPqEflUhp7G0ij3QCaSEVlVi534jtiB1qJFNuyMCSqJVHRNmBadueGaMDY6M/qaZkJcZmRmYmaSutO3xp8ZEEHGJFymOf41UbWX43pm'
        b'/dW9fGLfE/ZyApI5AY9FkWjaqo38ADiMl5tJgNAIXjaM4dTEONys0VHLsH2cVUUt44hd/G/E0lAW/mjMErS1YwuG26r5SNXF+HJ8DuojksxjDEC/AOYuBMcS+765IFTg'
        b'hXJ4p/MXUZ9H3Y3yj/4yzlhLi0SbGV8pCKkfpxbd5I9CBeGpGk149n+B8JjdMu2MySoyENJJMx/tAqMuonGPzi1+ORvPrcdfmFsmR+/7J8wuccSrdQSH6ciRCdYBuSrA'
        b'r9UiUajbhv+V6X1M/cD/BI9NryAw8YS4hSH5cm7WraNzlxS/Pvb4sHe0JP5mEstM+kkQf3L8n5w9xX85ezp6GVMenb1JfzR7k0bPHn55x9+YvW+fMHuWqIQYOKRvF6ia'
        b'PNiHrV7K2YNHRVHxsPzp84f1WBxSEKmRwnjhX5zBx4IK4dl7PNmRViANfXAGXmT97JFqdF5Njgdn7YiUm2Y2idshZLYum//97p8XXzclX/5qzHHriUoa5d/rHE7Pu9/z'
        b'ZPVCNXB0nOhJ8yda8TE6+sbqhYCOcDyXMJ8BjaBgInm62Ulj/VdYKjePkh3RiaCBdBRmsDzEAVaEwVo7bx8BI17FseDgtMTj3RcEii3ogecZvQn75+AAbosT3v2lULr4'
        b'I8lajdWvGFcGH6geqjnceks2c2rpyo4At21BqQu1bD0MZPLQFfHuOi4nY9/M3Buz9+1vLv12p+JTuc6YGB/3enubvMDzNfnRkaaT7K59vavs9lBRb8AHZisTH3xblvrw'
        b'E8HB9zS1X5i48MbbcgmRH8YaoZ3eAR4HRTbYlCMG9ZyDSE7PF9sCEpCkBM46+amJSuCYKU0M0QIuw3w/WAT2m9ljkSkIR8bYjwQXeCGQCDRiyVY/+/h1BNLKn/fpbqQC'
        b'Qh4s3ApO+yaPIbjfIhZntJgC28FFIpssBWeiSfAdC0fVaZ41vEwKTdi81M4bDoMiciAndGNB56wVRKzQc/LCh4Sz7JQgV3xEWAGOPLZC0Ur6Q8+xazLMddNi4yPxpkmW'
        b'7cK/tGwlhjqsDkfyy3JoV/9NItQhu3uGhdpijsU1CR+BXj3WVC7DEr8Tq2wbKWL3X1/SBl8/YUmTo4Ui2ALPIY4cDXEGdG8ftPV6k7GdBPOFaDNu1HyMcWryfxWmj2Yz'
        b'FVTLqjXiuViulCXHRdxIRKF4SawgVpgv4TOU4mylDM5Tymco1STXWuRag2QsFZOMpRI+Q6k2udYh15okY6mYZCyV8BlK9cm1AbmWkoylYpKxVMJnKDUm1ybkWptkLBWT'
        b'jKUSPkPpOHJtSq51ScZSMclYiq/1cM5V1KsJsRPzJSQ/6ZREJk4/j2lhy9jV+uguPh7TRDxtUqw5esIgdjKJ3GFxTSMgOgX7T953GBUZFKfbNE+mt2gu0UfSOLKEiT/G'
        b'SjWV/G4xw4dt4v0A0RDjbVFTxVSFf1bquZ/3HxM0jmrtSILGp+X7w4uGZmTEn8xJXj9SxLLFS8zjE5OekJVvFIVhMn/SyWAW9hr3QAparx0i0GOeNOdYkMMKHhkGOmCh'
        b'vSPLLGU13LYuoGCy/aASdknT0kPQLeVzoRJ8RgELA+B+PXiGRumKMZfIYB+sIxzbCicnL3HwBS2gh8TcYcHpOaCQguha/h9x7wGX5XkuDr+DDbJFUFRUVDYIDlBBcAAy'
        b'VUBBUdlLBGWLqCAyZO+9p+yNOJD2upo07Wk6c5o0bXLatOlMT1e60pP2u+77eUFQTIw95/+FXxTf93nuee2pGWzOCpuUe3oTTVPFNmyUXCdGWMwNCtdw1trcwxvGj1pZ'
        b'mnnwyE6dnVJsvoF3uatWMWWXp62HdaREJMYxEd73D+EfO+138WSDtnqIRZIw8a6AG0LDsfv44ITnYksY1UQLyJdg47ZbPF7guBGpsozs4sgBvMsqrbC2MdguPQxN+wVH'
        b'/jypwG2eMOKOY2neVpZsEI1t0sDwzXx0YzuW4c4tjmwrcuZwX3I9AMo4A03ATkVS4MzoW4lIKSMFWP9x0s2mBPY6LoFsVu5JVuspA8cl2I/VuoIV7Qk0+PBiEDU6snoQ'
        b'YmjOxAZuRXOH266stlY0zCuIJBfE1vRiqWAu69DYzMtnQRvW8RJapMzaB8uSF7FSV5ZBIat8dQzuSddec+Ymsl+rMBPZt70VnUO8Whx2irgDXGnTTT8WmwJPeCWthdOC'
        b'C1iNW9PSRc4ham8rRTNbHVPfdQ8ZsxJX2IANVqZmK2pckYZewF/9RJ9VBHrHTFkUYjFNVyusbN4X7vG6W0UwLNTeYoW3BmFGiMz0yWDJ3XgP61fU3bI8zi9BgjN4V6i7'
        b'JRYpp0p43a1CyOdWZyg+T4r/c8Wx8MmZxfpYUEOAx/QROsR+fEiwcv6qN1dJ6NrUsUN6fj/Wxn664eviZGLPorObs29UOSagjVre8ca72jtj/6ljLr//z2aOLhoVx0yK'
        b'1Da2GFU/fkvVTveXWh896P9VqceuX2t8e6/qp5u8f/0ru298pc778tdbLstv8vlLLLZu3P3G7GvVAZe73k9Ub/zq+vZKu9k9pzVDbl03Sgyzzv6W4ZXEH/5kNCbpRLf9'
        b'd0r/3Lr3122/Hv31k7ih/b/4k//YsfcMjP/L92ZDVtv/uL/nnD6W9Q3DS9HvhOVd3yn+j/RDKhl3/li6pWMhaaJs40H9az5veX+Y1vjfnZsdfm+n+OZXvvVp157aUK/3'
        b'PlQ9/YNr+yN+GGtz1ectr7c8/vOgd9t7W99ofPSHNNOLvz88+dbM9w8PVT9K+en5DxKmqr75ukuxSXDmu2eVVbc/1jus8nHRh60239U6+p67Xqxer8V3LT7psjj6r2PH'
        b'D5n8auv2T7sstD9c+Nqpt8+qjrTXHPvRWo9P+n70YWbb/9z64/vX5gr++VPFu5l1Zwb/YrpesGfcWQf1jCZVH16SSeAe9vGcNWtma/b0MrMSmKpqPLRDu4SEp0qsETJb'
        b'HkBNAK8QILgTlKCHhR1KbkA11glZQE2Yj/2LLbhkDbiw7CrrwUWUqkvoElQAD3CQ+Qig+viKGrkyJ4GTrAuV0zHWekfxGJbzimJMLsbbJHhxKKqHbhqg2HqJwqkm43CQ'
        b'BJv8TIR8txyotCZhAbt3C+7SgGBhE+VpV+k1D+8lsqcHVTCHbXL7N7nzaUOwmgGrry0WwW0PiUgaLz59De8IhqpsL5jjBVe1NnqxohHtYia4XeWy4jYstGcdlCAfy582'
        b'x7I/AyP8cPZCxwHu0yqlPY/7LlFC7X1S6PSGVm6w8tlDYo0vMYhumHaXUULt61K4f0iXf79mdwqfXkYLVU/C/HbaNPZBKV/D/tT9rNeQjByqbteBWQlRhTk6Nk4C8m32'
        b'sOJ6ObLubrIiER2Yz0fX9zzIR4dObFuiXxrK0hRpFpezz5/eRzuohXZfWfU+BSWJAd6BHsGu+Ag6ddmVFGKV8lLtPm3slSIR5L383i5ALovus5bREVUs1sJpCd7HZpwW'
        b'QLRCjmWg+nrtVJIRbfUjUtd9GjwT64Yz9Ata3fN1+LAO++VFzqmKWlgZIxj/ygKO8O5s0ILZvOQXLUc9Wrr/egBfr48+3mP3hZ3Q5bFEi7TtWQr9AuZycHGEVsIAFptQ'
        b'E/hU4NRWl0LflROm8i82QCm/ajIIE+C5JD/HRIyXluRVrFg1CDXuM1biljpeBULK6y/wHzUSqVX4NxKJulAZ4lNdRXWZHY79vfS58POJppISf0dh+Xef+w77JlNTJk4+'
        b'02ZHltq0aaVl4OW9zhLhVasVp1XzxZUMwx+sksz03JpfvgnGps9qWfIHWp/QQ2dphqX2OVt52xqZxPq0jcur9cu5I/RlULyYHBud8BkdbD5eXJAw/WIHG/ZWaEpq0qv3'
        b'qZC7GGYb9sJp/7o0rYlrfGg060YdmyJ0Hz9se3jpFF6tt8lF0WfcwCdLMxvyDhRJkRGxKYlJr9wnKOn3n3Xfny7Ntkk2m9AY6NV2J7tU5YuXEyNio2I/41pZrVxh3p28'
        b'W0xocoqR8FL4v7OA6MUFLHYEf+ECpEsLMF5agPDSvz27opC99+K5FZbmNlsErpRlqEVQJgzwyt1OFC9GRIYR0LxwBcpLK9jMsYo//eotbpaOfRFaXzix2tLEW1ZA978/'
        b'9aJl6YVTayxNvX25Gs1OflGHXjn9stk5l3s2Zka8FDMjKhTlim6IM5WzRNwyIObWANFNsd+y31fzh7BhnzeYK31GvM4rVo9nNonA5ywE7D8OgekxkbxnS0oMAd8yOEyK'
        b'FNogpbDOLgmJKc8bGZ4zNCxe1nM+gKQ2EwnvE2DT/8ZvQn78qxV9Aj41FQsi7yQ8OEuyC4nWy8VeJvLq+L2gbH3uYj42Y7UvL4WIbimYZ25e5HJLO30ahRMVHZny4nL3'
        b'bFYdVRbnx2Z9aW4uylFbhZ+nMicfTisl4JQ3aertQUwAxFrzpTN4pmsMVnvyUiCk7avCPOQ7/J/4d1ZtOfB8iBfdbcjxIxLu33lrwJj5d65YxEV9FFISzf07dMdb70v7'
        b'Rg7JekHEO+IQ3nF9RrNhV3zE6fO8P0l5r3rZ6taffdnJi5ddIH4m5KtQvHzy9a9y55rffcGda6So8SvHQfXPv3JSJ9iVm6nSx1U4ZyoRzEad2Ag5AjzIaYiBdV/tZyqT'
        b'kC7U7m8lvChnJ8aW8zAFj21iu5+8L5dsS1/bF5/8aURMtHu4V6hXaNxP7slP/tDgew2nGvwCsw++vj5//eu633fw+rJay1xBrGhSXun937z9XEjc6uFxSVEyWOEUSyL+'
        b'IleltkNdUUWSqfXcdQnDFz17QSsn1X6VC1J/dxUh+/kFvJguczecUPJftOSG+wKxlJ94P0daj7AowGRBOiBavNJgnGyUnBIbH2+UFhofG/E5tl+xaDUuo+Dj78oNcI7B'
        b'10VKsdtoK0ZpDbG1irG1tbbyyUxIvffDP/0m5JthJlHeoWpRv6TfLD5QqPI69tjUK8QpecKkIsJUO++PQSo93/2D82Ccwf6GOP39+s2NRf5x+nrjVhGiIhuLkHNvnECj'
        b'L1e81gYtb57q0fiu1LbeTiqa+Hhd6Z6LpkqCz2vUGZgXD0duLWmt6jArdcMW6Be04ymsxgaZhRhzfJlllVmIoTCd6/pKLJ9cZnWF2d3sa2Z2DRMLMedDV1yW0Ooyzi+a'
        b'jzdiG3/7mlcWN+c2Qcsye24qFAnlecqMWdMJaITCpcYTlduEqJp56Aw2Jww9joUhMCwnUoiXbMUerOQ+NV+4A0Oex2H4nKmFgkjOUAyTUg0Z9/pcZ5lSbPJFfrUchY5+'
        b'Uca2T44XV+T/S3hREbHcCrVxcfhlzYtWX9JThudIj25+FdzSfvOzFNjFlcjqset8TikO7rOLZEckZfob8xwnqUvYiS3qHO8qLQr/7yoIcvS7CoKA+67Sorz5rtKSuBi1'
        b'uDdh/n+/wfEycrSdfi1nGj+bhBXLUJMaiiXn/m8KYqjLaarqSYQk636swRycglwY9F60JqlAmQQeYRsWPcfTtWV/J+c/63pUqDGoEUVISpkzTqdAl0SIl3Y30hvMaaka'
        b'oXZHiTsbjWNFkUoy954SGzliTamYR8Gr0shyEeoRGnxk5aXv5EnO1YzQ4p+q8LUYRGiXSiK283d0+Fu6EWvvKNP3qvS9iD1Ro0g/BhF6pQrKOso6ETt4dQ95WQOWNQXq'
        b'BZoFWgXaBboFBlFrIgwi1vO31YTR6UepRpl2uaFUGrGTu1rluR+QdRNSL9BgcxasLdArWFegT+9rRhhGbOTvr5G9z9+uUYzYxN+Xl72pwd9aR28oc2cme0Od73IL2yXt'
        b'QxKxNWIb36dGhA43Upi8qy5DEforNDoy6Se7n+3/6GK08gnGHejvZN4Gcjm7YB7H0BSj0CRmt7maGpv0TOvGKJLu+fMR9FV4CtMHY1NWdGl8xjF5PIXYT2KSbKqlWUKT'
        b'l1Qp4lsJRqFG0bFpkQmyYROTrj0zjJWVUXpoEmv8uX//855PpqU9s8Eltnf4mL+LldHRxISdKUapyZF8B1eSEiNS+XK3rPT7yixxiXR+zyVlLDFwJo3JisDQtUfJL6Vi'
        b'SF8qFYNY+E/Ortqg8xm/7yIHv7y4pVdy/S6dKFPd6FqXX8OqOhq7e35lEVZGx7kxKyKRVsQaekZmxCansE/S2cmGyaxAkatIFbIFyZR1YU3PqfDpsWyR9E1UKg0XGhFB'
        b'YPKCNSVE0P9GoVeuJMYm0ITLjV2fI9KsqOGzJNKs8eEdNGJhUmF5HVV36IcRq0WzOYnOpV685Okpdy+fxYJssIAFqtjLqr6lMp4XERK8Yoil1+klmbE/DQu2OCjfwNwI'
        b'Loc7OsNdrCZR210OCmBWJL9TjA0kmldxt6kH5OAwyxvOELn4Z0CjgVDTZgF6oczPEvtwEnttnWJFUiuRxkGJMTyBbO6a36JB613W/gsascaEyUgnhL5f+0zloZLmaeEu'
        b'7xu4IGcuYR1QsOlMMi29hkt4hhukZ7dLhSisIxruolQz+nUt3Lvh+XRbWJjq6bWiw6hIdDJREbMTDgjxWY+h3jb5qrwoGvtFWC6CoogjsTW/t5dL/hp9Ozp9KrLMUR1s'
        b'1PLaq22L6/4p6k2595VdFQ2N9iJtaVjYXf2it3JIDrRKUdY5455QVK2sHDT7Px/1f2v2lx1TB0zX/+qYXuu315pr1f6yx3P444/rJnxH/L9bLD7pDa6/G74S9EulOjV/'
        b'2yJfx4ot9UM112K00txMjA27jT/++/rMf/w4tlAneuHuV2D8zO/+7jR17iubJXbhUTqNvQXNSd886P8EjP459571vh/t+8As0TdKr3Ln5aS2DVdG4u+p/uWthAEP3+H1'
        b'edKi/1j3qNNp48kvm+oIxSk7YMyZ1TkuJaFTCB9Yc0uwUCxAWQB3G+Kj5KeeQ+Y2PK4m81y6Rj5142+DHN61qVUQVXdDOfSau8virPAO1othlHV4498akjJfu8yviS1b'
        b'4iXYY3BaCB0bhQa15Q0HHKBZDBPrZfHl9Ts8PHm4BjRDBaueqawrIeVwCnq5C0mOBNcOLCZ5wIfuHDrwgYWZAgna09KTMIePuT8xY1O4uTUWkbgAg1gjUoB7Egu8fZ6P'
        b'7wmTLB+euVTTsFfwqjKP6lZoEOrnj27zIzGbTktuiwdki6F1jZ9wlhVp28yteMh70Hkh6H37diEDaxr7fXkd+LswA0UWPDu1xNNSQbQOZuXcYQyGZV0yNtMJynQDnUCR'
        b'go5kDbQF821dOIyjrDKiJ6s9KDh7tVgZqGgplCtiAb8zJylz5PkK2N6AtznGq/tJvXEESgVnaaEfqwKx1GrjOnaKoVnupHDlD7EigyXbKEPn8pKRchew9rRQ+H0hFR/z'
        b'XKmy9S5w11eWESXSo7EW4AGMPx+D9mJ/3GoOtrOM6H0RDeC80NBUjZdXZ6XWtcWG/2JB8Go8WN7wXyoSJZkjTFucuW4ln33GEya/zBPGmOhnhdZJhSdWcX0dehXdQXdk'
        b'Fd3hRav9Ij4K+c82FocsGoufm2zJHWa3xJGfZ8HL2O2/4R9Lyvws10344hKT7FlU23Lu+L9jrX4uvPv/mbU6hsDotviZTS2e1nPGR78dHYJheSr0NVn72XixSOmPmX3i'
        b'70WwBrQMQw/j2AaGoNCET7DsORQt2Pk5xuWkO6wn6o5ngCE5PP4iT9b8Ilbj6FeyGuetYkFk0AQtWHqL2xD93bgJcYZpfF6+llhl7rNsp1i3qgVZf5O6I8yd/P/ZfmzT'
        b'BEJ+QP2unzH78aL1uP8GXeY3RKKtc9J+uQm6SiMRi8pSxKYsZYHcPneTkxYvbUNOyn/ZO31Z4zCruiKENX+BqxXlaP59lcs9RqP4bsV8frfnLL/Y3XKLr/5h9eOYa2Mq'
        b'EToeFsIUZMvsxIrpGmLo18ERISSyKANnZVZikibb7VhNiyJsiv3qkREptxNbZoX9NCKv6iUsxQaiSUWlH+t/72XtxHfFr24nzlRXVZFk6r/oAj/XXMzmjnolc3H+Kmzp'
        b'hesgqsLMVi/GMa57SpjpmGmfS7qnhOueL5WH80nfc/qSWyRp/ItMaLk14MWa5uWkyChBq3suzGMVZTApMiU1KSF5v5GL0X4ebr0/RHYCIUaJYXGkn36OErc6P5H3SWVV'
        b'StNJBM/l4iqD/IATid5nLE+fWTU2GbJ3K8dJ8B5v4HFBtMXzGV0PCxOgZrlec0pVEUsjUmJ/93MLabIvvaRwM/U3IR+F/Drka2ExUYORzNQd+KVAHK+YCLx3x1TeZNvr'
        b'3/7GO19558snpP880nPJ4JL+VENOXNBkw1Rjsa5noF+D8+SeEg77pd/Qcv3VY1MFLlR64B24Z05/dLg/zatQgikhvC3nrIRJ09BFmFv8VJx2SxOKymfvUH0mOJFUDJKT'
        b'G5WAxGUuWO8i8fURC3GG7GBBR4H7N4WZvXBok4/nU/VWlSYbdQjhrPDMmVgW0ahwZLWARibrrsDal5FT31VluR0ymJEsQvQXQWVCZl01nrCpLtRFWP8MMi2bgM87IAvP'
        b'4vbgp/LoqkbsAYnw2FN51JOGSH81Wq27ShLeZ632xVj/nGD2BfLuPplZFd9Tng/mSIxazBT4v0d/F2HOl0T/1d1SJA1c+baGJJkhwe8zFn4TEvylb3+ZELGuM39L8a4G'
        b'j7dz7DaKrEHu+jAr8sGzHx/ZQBPPfsTyJWv3esL4EWyVy8RGKBAQ7kEo9rDo+0yiKzwAn4ffw0jaolNmdSZhscigbL8wTKsYK6wOG7LLEWbxkizKid6S5ZMWvBqAqv/s'
        b'JQFUtghTATveVUwOTYu8GJrs82IbKQtclHEpBW4lVXgFK2nYalbSReBl5uMIWY32lwJdlyVTd2RKKIvbChXiVi4nphHbY7XWF8f934J74R3ZYe1nxlRu5LZgFtTLqckp'
        b'zIIq4GFySmyCEM3G1MRVTaCC6rgiBonZuGnw1cyvSyjH1poUmi4cF+35czCNQfTz1lIVgdGqaLDyXUt89gVcltXnlHHaU45C4ZYqyMcScw+JyBy6xe4irE2AUV56ZNPO'
        b'r6lXCVVL5ERyjeKU7BRuhuy1lj+cJtVktR+9tq9NE/kn/ZZggZtHfbX9zX0lokN24lMibAqDnNjgD7bJJXfSV81vfxrw5i4ViYua/LfbI74foKmq+prqO9frLI9+21UC'
        b'enqjIdWxhndSLoT+vO+bZ03be9x/fKigep+jttvcx29EmOy2+N3wz6YPd+102FCjs/CLypJJ3aPvH9GKq9Ic/d7G/N/mKoWrp5Ykn/jOib+9Udl96k8NP3NtPnwypWrn'
        b'6UNF6xJtLpR4f3/mO/jbj1Ivnet97UxcqeflT2dKDvj/9uOx1IbzTg2/M50NzzBVEkxI1Vh/wtwd5g89ZfbYiNNCq9EZVgrbl/ULfZqTwPMRWmK4jcnoMFau5PeboZtb'
        b'FbPwoaxXK44CnTc2bhSMbGJoxSp7wTLYDW0R6snmZoux8soHJNCOBYFclti8OVkwsi0zsHlDCbexYfcGYYQmNVZ6qWgLKcjLMj0fBQktMA1hRDAMYgs+lBcMgxePrs5u'
        b'TRVe1kH6rqIsJ5TT1xNfXGawE1oAqogN/6Up5e0yxHLCJ/+Sk2j+U06SqbcK4aMJVxi2uHDgK/l8QYKUyqfPPpUmTtI/q16NWOutFtz9gjXTuXLbGqfWyksR0IIH24n5'
        b'wOXiQxOi/V3DFZfh/mJ2I8d91rycZzayNFIV7ptkHlFJgQb3ikoLtGVVyXSidGSkXbFQmUi7EpF2RU7alTg5V7yp5Lfsdxlpvym3Cml3iYhgYdMJkekrQ1iY90fwNAmO'
        b'sfDEpKTI5CuJCRGxCdGfkdZIBHd/aEpK0v6QJQUrhBNNxkISjUJC/JNSI0NCLGQB22mRSTwsgLtAnxss9IUuT6Pw0ARGypMSWSjBYqRoSmgS3YZRWGjCpRfzkxX+sWfE'
        b'sVW9Yy/kMp/FmdhBMPdd8pXIcL5DC+GUV+UzT8P1E1Ivh0UmvbSvbwnMhGU8jbtPj4kNj1nB8PiOEkIvR666gkQhyHnxHGIS4yMItJexz2dCoC+HJl16xk29dGnJRkLW'
        b'gJWRLwtbTY9NFlZAMkBMYoTR/qjUhHACD3pmUQoPWXWgxdWHh8bH0x2HRUYlyrjxUhqxAASpLBqb+ZhDVx1nOQy98CSXgsj2Gz2bUvA0zHZx3heF28rGCrMNe36U5YkJ'
        b'n/M+oxMkuvj5Gu21c7Dcxf+dSrSGkDAicvGqFsci0BegZPXo36ORUaGp8SnJiyiyNNaqN74z2UgQfa99nnwjg0y2lSukXdBvLyGdrRB7NJeTviWxx9SHVzUP8YCxZFu/'
        b'MOIE4kQR3D8M01ysUYGGHappULf/qlgkxkJW3n8001TM3zlkqmvuY5GGZazZXpn4CHZcSWX2UcjLxBLVtKsnBZHJxMrSBAutzY57Mzcz9kCf9akrOJlyWnDZQjuMKkMP'
        b'dm5N9RSx1nC50KaahrP0MLfmnTbBMiyzMHH3holTbMQz/OXFJp1QdUwF2rD5uA+U3VSBQcwT2eOTNVisY5vKimckQ+G1Fa5rUnlggGXyLfNdh19Qgs4jAVws+9uBNaJg'
        b'K9JuToRYjCVsEvHGpZfPkOxS/NTvbCIE31mYhmKFpYe8yNFcAZtioEJWkx46LVNYl4QqBZFYSwRtdlDLx24OUxC9sWM9K97hdTIwXaj/8U1/Yps+ukwOtOjT1xY+rDoj'
        b'EekeYGXyQiz+x01bJNgsmWmkFrslrJlCOS7QnxM4zQtI8Zf+205JFCM2ondCvCyV3USpB+jDXVDjwDLNvf3chVq8tIMScybOynaD3ZDnxU/bwsPL6rilmYIIi03Vrp7U'
        b'TGU2+0ycNH1OIC4x9fD2ggHIw3p/mUhsqsB6BzxQJuFrdIurqRI3paph3XUs9rqItz2eZmnDuL9wTpMwpeuJRQpxXkKWNmsfLmRp52iosv53RTRByWKWttJeoZ5eHo5j'
        b'2bI0bbGqSE1TuvYMjPIpMQc64C59nwX1Fku50tobhRTmal8Vliq9LE0aHsMDadgVbOdr2hCKQ4up0mquyixVelcEL2KxHvuSzU1w8Pn8RVmedNw6U1WOF27e+nTg4iiP'
        b'xcR+TaGnTdqJ60/T+r0wnwdt7j0oLKzJkyb2wJ4A75VZ/V7QyRdmthEaPG1hEns8FhP7T7jz6YzCoZW2q7dO5pmXxwE+3dFtBxbz+iGbAUuiBBvd9/JIi+vYkCAk9i/L'
        b'6g+BOulhKL4qpJzfPgITLBB0KQjUHhqkgWEwLoRZN4fdeprYD+1SHmIKzab85bV4W+Gp2ZFniW/DCel5abws0f7ivqXEf3jsJzM9PIRqDuY4cVONBYGcIsFcGonVtuID'
        b'MCvml2uHt338SBerCDhhqaB3QqRgyfq+z5zjCfoVYfKiGJN1HJEGdMUifm6qx6xpo9XYbOQrJ5KoiXBhIz4xVeFlwDzCsTpZPSkV87ADJ9RwQgOK8H4KnXyc9Djchnpe'
        b'kEgda44ka0Ire3DpoWScTpVnMCHFVqg246n0WAGd8CB52XPpKVeVk9aoK4hMpNYmcngbunFOaBfVCmWkL06l4nSyauhVtatQqpGUKhXpGEr3YWG00Hu5Kc4m+WqqCh9J'
        b'I8sUZ5SR0D2VPby4gEMXFOQvE+iyMY/BqCt/fhTmVqxSJ1LqomXLnzHMkC4NyReHPfpsfZtgVG6HhrUQLlmzcRd7CGaXTiQJp2ltx6T7PbCZ1/q1WoM19qeeDkUUWUGk'
        b'qSChuW8T+DGIDgqEeVWcTYfaFFqImvIa0g7W3JTA1Foo5CB0Km4fXeWJE3STsbAgkscHYqgkbauHr8KMjqjUzxsr/YhW1/pBKaua2USUu0eMsxYnORQnYzMM0RzYeeyZ'
        b'Oc5Du0AMqhNhLhlnAyBXg76TYJ/YDFughKv6J6EyDYuJHnpae3v5BjB2dEqm5Vt4Qi4jjiXHvbCI6ATcDlBOdsJOIfanAps2hBt4sqLn4v0irMGySL6edZfhPk65G58m'
        b'GuFpSajlIyfSghYp1Nlgo1Dr6fIGkebJOGLGIVl3T+4SyHbMdnPRnPcQ+zBsu/JJkdDhQvS3Q7JfTJxN5fjEWHgLhoAeFF2DYmP6owyahRV1JUAeDMkxal19TZQJdXif'
        b'GxIOZSjwKCtj6BNlEL3t5hTj2FrMQdanJZZud1QUex4bhA7X42+kS5Jb6VerT9+87OeZ+D1nzbbzB/5g/s2hy6f23VjImP1Snt8/VDN/dmKuXHPulP8Pcgb/85NTqrG3'
        b'/d/IO6c+++OvJ/5Y40uJt38wk2tvdOl1u3+8+dE3P8ryfE+/6hfG4ZU5t1N++/r2/oqPzm0fa8F3pkLDLrpJPv6ryusfFP20Kjzpg3zJZJWjbv0/TL7zsPpX3+m5O3tb'
        b'/LMPTpecj1urvvfjC1KTPNHsjz6uCW9a378JDlS2VPrOB3cki79mED765cOvG/3d4/bDiYILVofaow7fBetOpcCz2yOqsrZ/p/xv09/ocnqgqpG75Tdb/X+Ue+GA+Jvx'
        b'4Z5vf+m0InYNRZjGLZxJin7L6pN469q+7yY7j//9PyzF4X816Lk4+pUPFORCzv0iPLtVw/aDv8W6b9lj8o3X8mqzfrHpYV/BjrG0n34YHLV35qcfhh37Qa/7TZv3u8cf'
        b'bpssFqfDg7c8bw667vrZ+6c95/4nz3njpP2horczWt82K82+MXU2FH5Z+Z3fuCbqz8d+XPedH87tTv+z7sc1Qa4Wv7HYYNFscc5ih0L9L1y+P5z2jRaz9B1Ve4IH4j98'
        b'XCcNMbZx8jVLvnqidSTY0LXj6uVW0VfddX5yVa69//HCXPTvB+2++g2wvPbBw6LGuYND5oYGXzF/rSvp9QsfmM3uavqHQXK+5HXz4pP/9aZ6mf1g9F/+crX1r/mGk9kW'
        b'Ze4nf+F9Zdulyq/+0+2PRe9p9226Vu34n0U/dvzp12qiJ49fePOHT5wqf/eDt7/3qe/Hhvf7ZnwvyAXdO/zm8U/L//qH31ue+YN3lvZHiq/lqFzdkD5+/t2gc/J/2GJ3'
        b'vf5ff72SrjRX8I+MK2+H6Cm8duM1tVK1f7xz3Tn0suPwz09eL/f/3mPjN/u/2uQb9NV33Ab9ihq9PixFL6fvt0X9Ye5bY3/9mteFtz/6dOfpnoXEdb9zMGn79by+xsXs'
        b'v/5c46t+Sod+UGu6i9tx7LAl1ZxZj5pW+L21j0uhA6eNhCisHhyCBZIxdtnJZAwteR6+dRJasYVbyX2xyEsBehxEqiclWLYXZ7gByAGG8RFxRtXE5YJLDjYLzbarYWwD'
        b'a99qzTrhshqlQo/F495XLc3i1bjByhOGFGEcH8vzrr/mt5QYu6yyYIuEMj6pSAsLpFCCzTsEH9dt7CQuWOX6vKNLSRO6uNXe60yIua8FFvFqrIpb14tU8QmrwVBiyI1u'
        b'+6EWOxaD7RLdRKos1m4XjvJAgSzMC2E1Ihaw5ZnwMCkJkwU3UgQSYwPV5h57ti8Z1VL2C/a8CbgDObLANRa2pgRPJHZ7DvKhfTE3JR0nnjOrCXFr9yL42jXPkmA85PG0'
        b'GhuOwbBkKzzYKDR9KIZWW3MfqNtEJ6kgktsthoFkLOW3sSkB5mSReMzYRmS/VmJBYt4EX1rieh4GuGfbclPdBM7xL3c6wJwnybOyArTwGMsk2+CJrGNECwwbe5rDKC1X'
        b'QaRwjUWtSYzpgmqFUiUDSTjAK9/KivFuxVFejzcLCwUj5O21kG/uHmH31MZJFHVWGPveDtJPlmTjW1AmC0AM5evaR9IAu8biAzhmrUgKVJc4gITRcp5lsxk7Aj2Pe0KF'
        b'xWKSDTygNXHJYRhKYAaLLa5GkgjLILDI24IkFmsp1m6T9bIwZUE9T92d2HRR8HimY7VwyV0Esp6sRvliNOfmLL6oGNpmDQnezgykFuVu7LUSNjR1NXiZ2G2GdVzuToMK'
        b'fhZBeJ8V3KWlTj4Vu1XshJwmGhT7nxW8SXCThtkY8xveh0XQvCh44wKUc9Ebcq7xjs/nSXDqJHVK7oXCN95T5VfmbIxVbBjBmUvzYDbOY6U00ZiwgOtQ82Y4wmr/Wvuy'
        b'UoQ3zwZIzI5KUpiSR8hTvluQya4SZMxyqewqzqzBcbEt3BZbYJe88g7sEfxnjy7hrOfS+WOtpRI2SaBo014BmXs1YYC1IoEmdQYGd62P827eG1zloFXbQcjEWsASGOF1'
        b'D/cQorAGJb2K2ClRCgnlhXAyYRIqBa5ui0XE2uf3CKc5myohRMnHh8uKw4p0tknp0q9yanPVAQd4tZVjutZW3ljk4W1FU2ODHLSchz6hG3p9ZCqN38Qf87UgaYVuRyJa'
        b't0fuEJYa8XI/QVAewPz1Lcuqca6oxIm1TvzQbdexT2kdRfxGVOExaaalEuzEe0ocNgwgJ5Cb+u9a0Jn7nN8mMYQ2GBMAuh9n4OFSJK4sChcfY470pAt2CIg4tRNbcEoj'
        b'TaCJCtAvUsYBCYxAr5Jgr28nAkWXYWlqQvCzA8eUoyUwGQWDppr/fgbTM1Zvnf/tET8jkCA0ImJFIIH6S3dRWQp9DWJVnSW8iozQTUWP1X/+l6ZUgdeDXqwSrSbexCs/'
        b'K9H/hn/XVlKTKIkFdwKrOqPNO2gLAbL8N4nC8toxYrm/yamylLplP39T+EhpswofmfVJ0eNGfSVeV1qOOyZYrxOFvyiosV7emjw8V52vTFuqLha6pLDaN+t5rRp1HrSr'
        b'Tm+o8x/e9ftfKtJVfLnLjkxwaygLvoklZ0HSKeavWHITJPmtdHX8+ylvporCZE9H59PyGa2WFsB9JWfot5FX85XYPHkJx/aywzCVvqu06Et+mjcYLid6+p+C6FnnCHN/'
        b'CA4SZZmDRMxdJMxBIuGJY9JlzhG5QoVc0Q35TGXm5T4jypLnDhG5m/J+y36XOUfYuTxnrwy4IosXXukb4V6CUJmVe8kh/mKPw+ITK9OEUmQG+2VDWMjs9uGhCasac8OY'
        b'X8aINzFihtcXe2FexUHBXD6rzmq2uDwzI54KxG3Ji+sQPAPCkpibh5aeIFjjV3cOGB1JjIi0czAKC03i1mxhw0mRV5IikyP52F/M0c8PUObLebb60GpOGBp+9SoZMhP/'
        b'ooOD+RQ+zwb+RS3eq/f/2eyTymKN3I7Yez7tjn7yWU8/yTHly2LqykyVcQxLd6eyuMzDpFS0LTcHuzPTKBb6+pmQAPQYKwTbMDMMZ2K/MjPXBHNjVAjk4bS5B2ksbRIR'
        b'DxI4jlXcBtBoocJatSjZ7FBP99gaIbRqufQfp1irlk1vSUWS02JRsg2PgrWCKnhkDveYnF2I5X7MkuvtxTnzGSZ/e5l5WMCgv8yScSDOYrkhQxqwBvsisDuVtSsxO2p+'
        b'bCdvLewt8r5lIuS/V6p/ItKUiPRPnIiO1NdYUBWMEO80Ovvzr7+vdk70I5HI5kuxdXF/S/S+JXzt2uUs2DfCL4nfkog0x284nPmqorwQzUBK2H1tKHdgTdNtRbZJa/g2'
        b'SNkZhQfLTfNYaOnhjdXMFE1C5nGZ+4C3QPL0xomT7h4WHoL0SOJp+RqPYLjH7TiwEObzGSEbcP/MytjIdBgwlbWsuqOOw1wLPKCxJEgJNfbtMI9bkK5sO7isFis2kupX'
        b'Lrnuc5Dbxq0hly73BcZxfxMYwMmld0m1e6J8A26H84P6fQbv5iOyiRp3+1tksszm4xwnHCNuPC2aFomMfn+lMfMdh3S7pLWMYzA7v6k8z2w7vNbyOg4KpiDRNSBxn38c'
        b'6EeglacsyIwEe3OOQuvcsSy6g8p0IeEuw/oY73obpeYM3RaCHUgU67NV6FFr5cobY5TQn/dhmPSwvWIY04UhbtODe3Ew4gR5z9h2pee9CKK4Ejd2WSiv6q0F5Yv6w6hp'
        b'7LuDf5RL7mLNS1WHHU8eSPihs2brD87fPN3jVBNxoOi9PvUf9X9TPlhOHKx+21kSXCH50Tf2hhad3GKseGViOKmo5cv1v3ex9bR7PftLHz2+n/hfBz1mCgo/UPjo191b'
        b'fmvV+dXNJt73tXR+K+r/+Zc9TUuHr3/vfXdL7/L+qJbA1qyKHQ+/8t0/vXFo7i/dZo0nI3eU1fz5kkH2lqie351IsxEviHK+92tLOHJN9b1fuB11/3PAodcTND/67zKH'
        b'D7vVX996TS3f22Ig47d/2VT8z/flNhjWbgn3vHDRyePLZVHxY6FD101+ntvrcdVt5oNDa+/vjt73k7q4D40PXvrW4Mi+H9ywO34x66/Gyd93/O83v1bQ8qe/HDdYa/l+'
        b'lsXO9ze/l77nk48nvm/xOOKDyImC9+8cfv1OkGP6rdq3C9u1v/mgo+j70d3nar6cfLx54/S3vv6DJ1eb7DcbbWnfXf2XY6evbvGZUbtt8eDHk76tC9KcTRLb17ef71m/'
        b'+8xDNbu2iR8e/vo2/+Dv/OeXP339+999lBI2VLij0+JHY+/0XP/6WIzb77517RPVidBDP35n5MNb908eevtAR/NGr2rLer/0yr9kpf5s4V9Sk+natMP2pnpcZD+NeQY8'
        b'MQ/6vJfqjUKjkFtXhRNY9VS3VdbdCnVMtx04KOgW7UE4tNyKcZT5rLghAzvSuAqqs85FzZEXi1isFHHLXEiPm0xWYMi0DnJlqm8M1vJXbkQ5soQ6fGQqs0zAlIMQ8dhi'
        b'hp28c5k96/byXBBvvB7X/NZjv6nQq9J2o1QkdKqsucGVuRifMKFRJetSuYXQijeqhEZoE3TGooj9QkudTKygVbGWOrpiQfEYv5rEutQsdr/BWmyQQLVEk+vT23dCiTmt'
        b'hMdgKm9MiZNABamyXUJiZA1ppjOkg+WaWz6ti3/YhFtUaHedLODbggieBu1qhZ6PjWH8HhwTdsMosytZwz0vmTlHY680GPJUuQJngHMsNYKHgrLe9t5EP4lNmCuINkAz'
        b'6aHYjv2CcacmKhXmmaNEaPSpYCiRwwqs5re5QQEa+SBwD3NXqpsa8EhI+CsxwidCec9EaH5G4yQaWSRoetVYZb1C34T2EJnKWUsrYUvO8LnBnqjG1tVVTta0ncNnmuLN'
        b'JX1PORqa1pG+B49v/JsdfP4f6nZqywMyuHI3yljAF1LuRLfUzqpxVUpoLik0+WFlQw1J0RNKiapIVcRyEiXe1EdOvPi3nJi1q5S9KxFaUArqnqbsN6E9pZyGwp/UF3+n'
        b'P/X4XNr8T9I3Njyb5LFsT4L2pSCoPIFLahDTOpapW//7+rncssmslmbk6tZ5+mKv2mIJmS+kbpHCNb2KwvVZB7AYH+fMluMiWUXZYgIqF049RDz4nRVbEGrtS7jCJWUq'
        b'V5Taknol99LqlctqYcWL6tXTgvtLUcI8uPh/OSReeGex/Izw3iqVJa2MjghhRXwpLwiX4hH0TAejR4/7+drvtdnFdJ7LoSksKCY5JSk2IfqFSxDq3jwNEXq2rp/w/Sul'
        b'5yj5cEEQZpjzd5kkuAOKPztBB0a9XbnEtYGUibvc0Y6jB54WXEry5a5yFxhk5E9wtOM9bJIVcwo8xj2OJ4+x3oLcj4/lWSsK9JcYxjZtGpVPvkWPpdjfsizaogc2unJ/'
        b'TfzuYZecL31w0v0bl+Tu/1jl5NpC5/Nx7q8lFf+s785fB9N+8eYbA2/bbE3O37utaLv/9Y3/pdb3zzvxm6t9L0frSHd+Jdl58sf/nbHpKxkBO+PaDazfLfrBE93ioUvb'
        b'5Lz0Ej+ZSox/7czwk0uPPX8befY3m/TrNtspbjNNCTCVF5qn3MK2p7n+dTDBQoJvYzHnZUbYQ5rTYjgwTJks5dOXCMwjDx7B9HKhIgiqZEKFPdRyTnVMqsw5Jszvf8Yy'
        b'TlJ6Cbep3jBTZ0Z36zhFmc3dN3xFfs+/xT6WUXf1VI5rK+i7zyvQd6LwroIRTmgevEjjlXjjtsyNz5CflbOuoMArSdEyCvzF6l0TeeXvO6+ksZy8XqTPetVkLX2/KHkV'
        b'5Wz9yioE9rN3yKq7ZsZeYUaZ/6ueXp8MPB/DmxQeE5smK/cjK067osDQKhT0iGDviL/GDSSxl6/ERzITT2TElhdSW9nGni12Qx+/TIsT0ar0Ss4nld3XjkM4yB1b0Bb8'
        b'nN76NKArbJ1SLLRfiP1p4w553lZs+Ce5LKc88EvvfHm6YqJw7Jf9d0zl39AOj4mKD7MITYiKCftZvFiU92fFr/9xjakcF57VoSmIsB6G/Z76yOY9BI/SY+hJ5GpEmqPF'
        b'0xIdpShzdeWJbzKEp4/uP+MPJc26MoUtKHJjxIv8sFh0gbs0BEesDuR8bi81zVDhYhehK1myCD6vgLaRagTKS0U2lwyyz8yworh6yErEXJkt/PQJjmth9Ntrr45rmj2r'
        b'4NpLLTbpPbYeeR8ff1efpEsiLsJ9dpG6p5UyWIYxzzbkGV08U4CbwLlgxskH35dwKOv/r2XxL0LQk47Rr7aLlnpWvE5FVVss2fxc0TkNJYmuWElDXayioidWWq/AHBV0'
        b'xib/Et3SVrISaycYiZU26wp9sSAfWk15QvuKdHaJyESsv1M+De5AWerHNC8WXNMjhbDKMRGbbTQhH+/jo7X79kJ2OI4p7MdCqIQqJVLyWvH25jVQQayyA4ah+uhR6FKF'
        b'KigSb8AncB+frIHG/TgNZTAZSgLLgP8aFq+Vi2OOB+EJjLvDEzd6qhyLrsF9GIBhqyzo9oLRg1mkp/Yr4jgM0s/DPdBLKmxf9FXb7di4C7OxMwHa8A4yW1dzliMUQx/e'
        b'hYl1blcP+upB8TbMPnIjzo6Qeh7uxx7E/Etu6zeHrnfd7ykfZHvdyhe6gwyZvjdzEB6w3j9QkUAiTyUNM+sOsw6XzbDc9iKWcKvluA4JQh1QhV308wjrQo5g0wm7OCgN'
        b'xxEFaINZzE+ECazENj8cgfH0yyRTPLkBj7DeHyoNsOvSOZI6evatxVF3liVZQnuvhDKtozDmB7k7PWkBs9hkD2M3cOgkNIqxD5pIPqkhFbYJy2NI/W2CrvRNUlWogWls'
        b't7XAbpyNsVc5SFp8QbghZLtdhjsRNGy9Nzw2DXdN3OyKZbH4BJs9sDZIH0YyXHAOJumaxh0VoOGkaQDtuxhqIU9lhz9O6WMndtG/7ntDAbQE0mHUQr0F3rd32u5orKuD'
        b'k6fpg5brO8+ZYyMOaupgAcmcM/7J9GmluspWXKA3BnGCNOQZGBdhvV3kAWwMhmZbeKyN7eph3lAWneKE2aewfhMUX9yrhAswZ6gDc/GwsAHyo+n14SskRzbsMsSuiK2n'
        b'zzpaYzXBwRz0JYcSyNVhk7+aQXBmwoHrOG14fiM0+UCXwTkco/Opx3tKtJlpgqcm7HLGEiUoOIYPbega62DIAeYJPIphmNZ4H3ID6RbKLQ8RSBRlwOS6DVhEZ/QIO9Rv'
        b'SvEx3nUzJhgdSi0lwA8z3gatp1ygjOBejcTDqbVZznTB/ccgexO0YIOl2m5kIuQEtEmPQV946DZTqIiRg2KjW9bQa5+aGaOBtQSNXSQ5d2LJlZAzML82EJqcoQkmoAdy'
        b'Q7HFDOvNd+AcPoT7UhhXxpoNOBsqfwVbYTogKP0QNt/wi4chbKazmDehTRCI4EiC5wEaos0QmjHnRCCNXRUI9fugAQrCCPdyJA7eWAXjlvTMJN6DwRvnbuhoBt4K2+0W'
        b'jS1a13Zr4QjttJjn9M/D7T2EV3fdNnsZX9tB0FYOjTi8i6B8iKBzDgtDsSqeOGWx0TF8BHcVsdcJq65De6qnSyyO7MQCE1IvFrL2Wd2C/AvKfjCnv4lVSMN+LXu5RFwI'
        b'wUkJVmTohR7DOzClAiU33aEBcwzdoCwIsjEvQgPa4Z6vX4BtuPYOAxxwcVPR1baykd9gF0A41OqFhX50ww04qA+FRFSyQwkrBuDBXrrKR3Ab86SsV30lThhhiw8WBeIg'
        b'TMlpEQQWrYMu2gqjTXkXbdnpQiEOw3R6hgGUbqI5Rwiw7mUQPBRkaikRTkxFYQ0+yLLVhWo6xzt0P+NEu2aUotU9sN2ANIWOs6dJVaqBPLy/+TzMe3vCAvQrG0MVq+zW'
        b'B/kOkTh1Ge8GwrzVemYFDPaF+xsI5oaw9BRUeXpoBafjDM3XR8DQdg5yCIsWaGs5tjiks9PPeK0vC77CmSDsjafju+cLk6Y4Jw8NYcbQSTg2k/oWQeSejURTWk85Qjk2'
        b'X8JpGzVa+QNzmE51wJZgORq5A+8khELHVVVCz/o9JyygTzPEEwaceCfT23Tr9RsImp5AEW1uEsaOQ/45lrSwFefdnZwcscEDuiM0VTCPoLaX4Oo+3NkGTUZpBMb1Eid4'
        b'fE201+o4Vl9KMafLm4I+Ep6K4CFhTxWhXnPYufMJREO6LLA5jg78kYjAqYjgdRC6SU+sCT5GtHHBfN2ZlPMXoMObVtiDFThtQvhReWirbQaW6CrDg+VQSzhSd8KA1jGT'
        b'jrmWyrdgOoGTzRr1a9BI9LLPxWtv5pZwGPe5nqUnveAGxesgJ4o2tkAD9BF9yt3rRDDcoHgZSqH/IlSvoUseMFoD1fbY6A4dKfRIDrKdtGMbMaZ+yNaQYK4jUZLetYpw'
        b'3x4f6u8gcJiEh7b4RDcduxPWXpOLicdsqCWczccaDTqoHtpeHz6GqRN0n11aWBS0MYagLRcnnKGHjvxx8E6iP6NBGYYEwZ2XHbEihJhYvSkMpBNSlDCHWpeLLYH1XYJL'
        b'Yp7Buy/twUqTOLx347B6Ji0wF7IJlrtgapeRSUQoTBHJua+mi9X4EHPVsNAV2mz9CSSg8xotgDRxE5ghmBmC8kzsUtxgTIf8CHtcg6zhCbaouJrRhvOJTnYQ524+ClNu'
        b'0afoIqfgdnIQXWcj8cR2eJSJxWnQcF4xEusco9ysOFcv90whlpOfSnShgp6pO+i2LhDrofkSFEnS9KGF4JtOkOAb2s7G0SoXsF26PdHDFe8mrMHKyDOKGy/gyHqoZ5Bl'
        b'TTjd5apFlKch9XsSZuNOJlJNxDaByxiPccwcZ8XHNoVAhyI2nlIRC9k3ZYQ1DVCRApMiIrjGazF7Fx1wg+F1HFWEh9AT6WYCTUdgSIdYQpMBy9xRxxbFy4ZxBDRNGoSN'
        b'Dbam+CTAyh2aT17HGkMo8di0jzjBfRU6mydYrHgCBkIYroSKrwQziag1Acfw0fkzRC8YCR4mQkBCSOJeaNZxNj+ljWNBUBlyFG4fg4ea2OF26xwdTMe+6zpQ4ucVBAPb'
        b'cfrWxiMhRDgGWej0ZTqVIWg+d02Mda528MDf5rr6EcyB5sAsaHAKJ/Z8m665S1+Lzjsfe6SwoIVVAes01xP/K9KFivNeof6EuvN2J/fHExJXB0K1FeR66Vrr4r14GHYm'
        b'5CuMg5odePuIGLPlT8DDiMNQ6xoLU04+8AgKDzscOXZzPTYS9BNh7KX5CkSXiQ104YQCdBAa3NUjdJmkwyrHFluYhxIDwtKW7fDoBs5edSKobSBmV4Z1B69ilwtRlOyI'
        b'kxmQ75ZIGNBxA+purCW4mom4hgPR+thAVLCTyETRASw9o7UXCeArsMeNpCMC6V6jfbSGVvqt23lfhpsmMcaj62HKj+DwPkxf2004P4+DR0j7GiSKWwzt+zYxqSwJSqKM'
        b'djJYxErdQ5wWdNEys6EtFurCtDLTvLGFZpkmvKqHqlhazQDJBbkSkmTp6EsMrtP2momHDhHrTA6ETitswx593zV+xCn64/SwM5L5xAcJiB8FQ2sILXHUiRTGHix0gDvI'
        b'0Hwe6wJoiIILMWmMB2HOZQOcukLkZRLzjF3PquD4hl2uJzdqYlVqOcF1SApdb+sp2sGSEGGOc+LLWEZChKO9Ody3gfE0eehT3emgmERybIPraaw6TJuBDhe64nmaeyqJ'
        b'eU8YEQrcCvl2mLsrFFpp8iIYv3LdUW2TJ8k3Y2HYTs+MEv2ov7UZss1P033PydkTJayDB2Z7D+HQeeIitfggkqTMMuJjg8SmZ5DoWu4tS6zRJrgtPHweOjyw7pQz8daK'
        b'SGdoDDAjwaMHHu2n2cpIJOmAxxqE3q3QqYkD7lC2KwOr1L03R18mYpejSBjSdl3lIoxv33/US99xDYHYMNSqW26Uo1NrVdF2wOnNO5Skrnh7Cx1k9nY6mV6tDcTmy2jM'
        b'kWDMPQ81LqSUNDkRIyTqRGICPryILdh24CpRrFroJ17SQ9L+ON2T+ITlaSjenkCMuhmGfTH3LHYF74ciLwtvOrZcuHskboOv20kmyBSdvwl9YaZ4Oxyyda4bYT1xq8pz'
        b'OJtEsFN3EodCsNDSBuolBGjtXljgQuC1QGR9JPo86SUVRLrvGujTEU+HYPUBLID2RHs6+nu2kO9EUNODlbuCdKP2OviGQU8IziUGE13uOKChst1un66BnSkR9Wk1vKtz'
        b'1Gcn8cKF7dASQKNWrWE9Oy9D0anThCMPg6FjB/TpRuBEAk3YTNtsvUCY0Hsuci2RnyoYsYIxVTrMIqyPhrubYfL8lQvrDsFgPD00Ao1RRB4apXG0qmw/AvhpOyh3hPmd'
        b'xG0f4J1buvhEFI/N5lhnvzH1bYJJYxcHBpI5CRwi5wkiM3AoEu9dUyKZJ1fnOp1ezo6NJOBOG9poY7UmSZJnTmW6Q8Wtzduvp0J+qP6Ji2qniHl3sx/I3UN0v45oCL3m'
        b'yGSmLM01MJxBt/oQ208fUiVGOQsLGiHYi41xxGj75TE7FWv9I2H+egJ91QzlGmHnSZAZ5bIDkOzwCOZjCfSnwvQxL2kz9poQVHQR7gz5J2BllhERhxYm8MbQGgov7L+s'
        b'r0pvVBLhqKPTKPYOIkFv8IbfjTMxGVvVfJBk1m7s3UqUuz/YKUOdDrcYGOZWwFzCFSdtmNVIIRzJSSJ5oiLQx07ZGMfDfPA21PnRI7NwRxEH10Ri4UneO/U2FFyBJg1S'
        b'Vu5AWwZOXiRAHbdWM/cg6tQYq+kad82J1KeujYSgY0RrijeYyNFx1tqQtFmxThdqEow2HyNMHd6ID9yIbJWShjJN/PhhAksiwKqr27FvG+m3g3jnBjSZWBL1m1OkyXKx'
        b'z84t0i5jS3AU4XgO4UJuKqFBkwpU7cKyS3bY7LWdMGFKRys5DFn06uBZHDxPSNOzhQCwZR8JLPftoADnriRAdwopOIWkLK+z0SVqWX+ISPzUgW207IoYKCWJQR7vBRCr'
        b'LCQ4rXa6hDMBBpgnBzU4FknzthKsNYm2pTteOZusd4KueGKrGSFLK1RGpECLUwYUbcO78sFYHAeNB+nZSSBtilDu7mniEcUklrToeqlDu8eOW74En8M4mhkUT2JivZ/T'
        b'sX1MMyNtrdclySwY7hNUlXvDxPVY3SgiP40aBN7Tlth9MssNq13NCCJG123FHGuvuAA6O2KKpgpCJZQZKFTwhGmj4/IisbWItLt+GBES++qIx+V6ZpEmvZQ61eHII1dU'
        b'DbHXM9zGXCISO4uwcSc85B/vgHu7PNc4WiqIxIdYl9329UK+Uy82mGKxqR4Wi0ViDxE27/DiX+w6QSoace4OCzGPr2qDar9UN6lIlKiVQUdUjaWEFU3OanTiYzdVNp9T'
        b'hroDpzRCdYgjVVoRIHTRGdUyQX0H3jnu6g35cU56pkRk7mOvQSaxpU5oO67pcg6Zu6clDMtJUiH0xfa9zN5CmndlhlXqERjUY/LdDeiNDMUCVehMCiWEqYYFJ8g+cxJr'
        b'fegW6XvCxLxj9GsP9LMWBQUB2iS8NVvTZbXanjWmQ8vZSGrAhFkQjVsu8qU58yKJmI4R662mWyblJjYL8q2IrVb6Q8UO0hAmCRbO0u4rd9BRjUCVA2lIeSkXveGJJwF6'
        b'D7GHYgKpSUPSlnJJIyt0MM2CAjsS2x4SiRgnPtAB41tIDL4HjfaR9mlSLFeM1MAG90swsBfnksw344MLOHT2+FoYUMxKjfROuki0sxJ6lJnVABoMDTCHDnaIKFEO0cW+'
        b'4LM0VgmdZ12Qbhyh6wNaQsUe2mqf43qVGOw9o4Zt4SFc62qSYq4taTDZdDAjSER0wRZKpDgeZOZri3mBRNQ6D+D4DsKafjtzYDWfB6DiAIlC5bSl7KR1qXLElSqSaRs9'
        b'MH/0HEmS1VBkBm2KOByLFe5Qewg7AkiZKiGtZV5xLRaHbAk3PbIBh5WgNgRqkwhL5k3VU3EgPCkJ++in6sYaWvHdvacDSX8cIVJcaYeTR9yytKIiYMZkDcyqY7s7YdXt'
        b'fThifZwQewDykZl27rL6QdOQsx5aLhIRgLpD7md9ziWdObuOZKFCYuEP1tljTZK1HVGJyTQpEYdeGLbUg4XUGBzaR3pAhZkONq1jZJxYXYHNLULRmT0kKN5lxihTnyhi'
        b'pXDfGppTCKYK4P45KEgg7t0Dg0cJvUY8b8HIRdL12uhWRzz2c/vLYynxmPZz0aRH9UL5vnUbbpqTyDntw1QIrIyCR9hlQ38s4LyRHtRFJluk6JOsNeSEcxfWYM4afCyG'
        b'tgu3ztFCclP7mTmycOuRZ80yREJHnYycNdJwWE9hfTp2RrCQkzAiyhMnzmGRh66eC+ksC1CfRGeZr6orf/ai1ykiOxV26wl06mDMAPt26XtuOQhT10kTKAjU97UMd1Ek'
        b'ljZ38jS3z0z6bqZJmqB6Ly3ksQrtYDKBKFIXsZP5GJxNhVlTGIPig+aEGn3YkkD/KE/bDU3Ez4g8VTBQ7YYJMxi1SSQhv20/TkacY0WbvE+vY1ImEo3uPSMmQe8xIXWO'
        b'IeHPhBuxtzY5Q+w3J6o7hd06p+HeViKpZdDsnORF8nVbNEmduc6Msk5Azo14Euw3OJOQ0G2gwYxaXtifqX1EBQYvnyciXCKo/8nhhAEVl7bTsoiXYedNogQPDAkLWkm7'
        b'hX7vC6I4LDgcTySn5cLhaGIKU9gSyQrnpxAHzqU3SBrH1vAIGIs/sQ+n12nCk21nCRIadLHXxYqdiBkOrIvEB7EENEy+Jw0PHyfh/AX5g5rYuGEXVvleIZJWooNd2qR5'
        b'VV8nESobFq6SmDN9CAa0fE0O2RkT3+3A2iAl7HRLpENvNtmZusk0Vu+Em7YWdujcSt2/BvIPS3wI4AcJ+u5C300iBJ2pp92h+ByR2dvmMKcbSTj5mJBi9saZy8QmE6BM'
        b'ihP072GS7x6EphGxbXHMCsTeIEuiSk04ZAqPDl+Akc3bjxNFqGYXTJfwhIU7EWUY0aJtzOPCzRNecOcCjduzB6our3XzpekfbqAjeXQE5lyICBdclN96KEUCpdxeg6Op'
        b'pEf4YfGSWnuG5i+F+t2bmWYbdEpVDDPaWOgDYwqWMHJOQQ8GkIjg9B6CgzGH0zgPRVaxDgShldxYMrjVkugYM9E1allAHpE1AtF8GCelAJ+k+1qa0oUN4WMnFxgwhEYN'
        b'w/V0/CUwHUHI2n3ooAgGDIisDG6HRgfM3kKkbhKGA7E9AJptg4jqFByHlogg4gljp5lw0oWdQUk75aUxB7HOGnsz8K4VTG7zx9wEG+iJO0x8oYc23E8Sa4sr0Rt44IVF'
        b'FkHEOZrNCJvvWG45Q1R239qzSfjEh8CtjnhH3m5dJWiPS4BxIl5tNMO4jyJhwcIVX1LYKwliSqAnkzZN3Go99llDbSrxk3qfOIInUljqLdYkQJ6K0X4ccYjFBg+9y/AY'
        b'BlKx2QEeuiRhPZ1dOY6f3gQL/iJ7vLNGCRektMp877XwQJ4ZRbodoC9azx3qjm1Y70DKVhFtCUcOEBF/TEAxRlhwnyBh/iqpncM6dOiNYeEMcyRmUTEmRFVLJcEu0VfV'
        b'YOYc9sX5+sRGXSAhdVKdFtFEHHdIBSc9oTgc6k+brwPSLm5jaZxaKA77Q7mOc8j569jm4b1xF1ba4MTGmGAss5MwoZWoUB4p0O342Csji/UtD9Mk7tWJTzbJbYc6nVOY'
        b'Hx7oduGwtyvheIkj1ibbR+CDrUSRRulSi0knVLhI5GFYNciQkxhGtmvoKBvCd8MEzmw1JdxtwO5rhHJlMG5Cqk+xliIxyMErgWtp0uIInD9xlW6nFEk+qFCGWe0DVixA'
        b'/JrOLY2dhF+NRHCeWGDhRWjbd5nQcnRT6lEpS4nC2X0rIJv02lmpZB3ew0pnjSTo0VWI20k0t5U2M0EUsW6X2MP/OFOcwnEuHKfWEGrN0N47LQ6oY4Xh2Y2s1nET8e8S'
        b'kt6HM+m0a3f7KwfA6F5sCiTobiLC/VCV6eIwZBhAx00aNZTpYZ6fKxN9dGiwkYubodcWR46ZIckzHhvphIq3QrvVZla25CA0r6WjaU4mptMfCROBhgTnTZJTuzdAt4ED'
        b'ZIfBXWsSfB2JHm4OMN3AIkxjMFcZJiKTbhHfyoXpoL3EU6boVbNYJyhWTDlhBwNq++iQy7FR/yId0wNt7Ipei6NKJpkuB6+ug9Z9MOaVRYDVS6yvBxsNcDbFAwe0SdYp'
        b'Jy76KIa4QabKkSS6xTYapGqrfQr0HJDbhSOHjOGekwq2pOCwZtR5fejT0rwK1WuxxDOaBsqBGgtFW2+6UZIz6GDm5Iy8rzjvOxWHo1uJNgwQGrWEbMUFV6Jf9dB63MWR'
        b'db1ncjBJ30S6qmBWNQoL9hB7ZvEvR2B8vbKYiMH9i8FE+XrpUuZo1DyttWeIi5dCtxLciYF8BxywJBZQeDMNquyDkVnIu0QwdeHABiIpDyE/diehWr8+dFoSnjcSToyT'
        b'Pt0SomywBx+tg3p/e88rbsRB75H0PSJHr9yGKSNdB1I4uqHPBQblWbeNFljYvtaAhNlSM6zIwgp2NHfTYVJ6ZccB+rTyIHTtPIMPiFVinZbxQWNss4eGyECCnEKsSyLW'
        b'NJ9xDsd2HwyA3PgUoow1VqK90BeaoRsWRqceH4OPoDQMxq+S+FxJ0lspndbEfiKsecYOpBA+wIKk/Z5RjkQICrHouiUd7qSamGBvUI2JxnSRjRHJGTdgzpf+2Q1NXqSb'
        b't8PYFXccPcMZ4zQ+OnjOCepNiGmS7uvmiNMeJL2NqUbsIjGuIYhwY0ExjGS17K1E/npT5QiR0ogsDTBEymHlFAiT5vGROdHiBgLPWQec1idhNxCrVWKPwJAxNh+xhkop'
        b'cbiONewJR81YUhYfX492dydxINcjwMEI8zMTScCex34Xuv5JaFfGx3sV44nrDImx0w8fbr8B2aT21e5w1VD1w7oI7lobYQb+W9ehBh4yW1Y3PDhFeyQ86WNWIhJze6HP'
        b'XQ8br53aedaadleLgwcx5xaW4YwhccfCYGgPIGFrxlIhJtFWH8bdVQjxh+nBUls62Px4QoF5Dew4D3kkEYwTbynbhRUbFGmPvcqWOJoVQwJgflgG3HEktlwGHVKc1FfG'
        b'5tP6rvoEL8Mm8pobce5QAFSoOysR0XyI2W4kzgwxkrYHR0XEwGux3EY98gTknfM0sU+JU8F5zTOZO4nCk0zudPkElF/Bals/Zm+mtUw5xGQReNzdCeNa+z0JhTvXwUMV'
        b'mA28Fm+G97YT2bqPzZB3AR9mqGD+MT9CizxSS+4R0akklWULHXb9JmxVU5FGrcPis3Gx5y/aYZOnuviYHr03ApUKUKW1jtCtGu7HqR03t8bZTczoSXw7Gx6vh/vMc9dv'
        b'uJFUvpKwQ44ku7ftJppVQefRCaMbLROg0msbIUYZaT/JqdC4m+4h/zjOHFQlCf4RiQYtxzLXYZfaTXnaRZUrNOkoZxHOVdG/KmHBPCHkGrRtIaUyV9veF2b0oUVzn6Na'
        b'OquClGd4URH7/aEqBtpgiACp7FQQM5ZifyozdtHdPyL6O05sIhd7rLDw5sUtBKokB51mQdE+tKHbZ3A204qEM9KCHxCKzEOhalBY6lnCyXZg7IQVCdpL+1u4ATWbsCqS'
        b'xO6ZqwQxI+n6BFhDN7DgFtwlWk7Cx+1AmrliU+r7JCrFalouoYEzM0uVn2H5yVAfd8jolIYxVhAKnDG+Tl+3GESHK+tjj4G9Md3vAo5Gw7CiewhNMUsiUq9kL85ugAXs'
        b'3xenSvvJw44UYM7fnLMHoUoO6vSJmD9Ox0ZP6JLSr33wMJK4zb2bRBnLCZtq6DYqVTZhtwdR0iE6+BKsysIFeHRQF+/uhUeW2GXsjcXxzMF1nBmpIk7Q0eTtoNu7qyaH'
        b'g5HrCfCnrxkRmj/Y5ZtIENejY0trq7LRw7ptm02xeccxkhcIOY4QOMzrxuCMGjYd2IK9a0hrzAuG3CP4wBmGlDOIvFST+FNLpLmbtb15qACthu5Qr0oaQq+NBnS67IJG'
        b'OxIV8vT91+K9bbsVFLDw5BG8q4q3j5wgpfiRFUlYBQ44oXEFZ6zVPG2hyw6rXfY706FMQZMcoX0P0fr8zBAjTZbQ9YAowQPIMSJgHxGTXHYrbRfBWvUpyFPlIPHgIpHv'
        b'hUs7iB60YEEinVofowMzNiR5VEfFQLc9AXSHFTe/V2PROpzaS5pNZTQUKkBXjBHck4Mxp/04yzR0zD5JFGzaK51Y+hM7BZKtu6HEBHMt6GzG9KDrBtRrEXAUbmW+ZPks'
        b'hb3R/jR4zUF1rCPpQSGdyUC5OnsSSOEjmf42UYlK6NPBxqPrMlhchR8dXhM8vJC2HQYt4bErdJvKQ+MWkq+aA2HgEik9I9BteZEkIOLbe/cn7oaHHjuvYtd2aPCAPnOb'
        b'YzglT0yl/vgWUmtbcXIXsbgBhiKNftpH7UjGHrLChQBjIm71p0LUL97wXx9EsFOI2Xu8aI6GbY6bnW+ISMIsvIQERVgsa/uAzTi5JxlnhWpABcdZQSAHJW47MoT2w8m2'
        b'SbvgnqwGXiJWm0r5V95qOOGpASXMqmTPzFhDOCiUMMuGGW/PzS6suITYRkRH9RB6hYkeO7AyDSx/Bu/KicRH6LXENJ6OZWef5ik+vWgdI+CltXGr1vAVGPSEKWVfWoAt'
        b'M5y1RfAv1BUCiA9PYqkXveMgwvIobObTmxzDIc8DxMKXzGl3oIpGY9+pX2CBcSSjlJrSW74i/P+au/Kopq40/raEAGERqSKLiggYEqSKorJYUUG2gJbSarGGkASJhCRk'
        b'YauIorKFHVuLVVAUtFhRNhfcet5lXMaOttT1jVbF1rXqtHXaSqd17n0PamfGf2bOnGNPTn683NzcvHffzb3fd/l+v6+ZAiXsqcnBzmnwzNbQXVJuXw3O57SFVQayy6dr'
        b'Y98CR4f34UDxRBHOXU8ttFAbYuFw3B8D2xNjoHQUvYElfemg7bQVWDIQm29oOw7Opb0iPJJNLsQy2sTeBCaZh0iHKcLwKVMxEckWL5pMYje0tqhYcyNmBaeHNO9dEvvK'
        b'jdW+E/oYjVi8iIiHTbH8N/W9QiVh7ILTlZtrf0Hi6Xi3cOdvGr4NSum6zFd0KYLItOs/FsjqatZJ/ox/pNwwPiJmIJHaKOz/8LRo3CcnW1vDDK+WnPout+3+hQf51x5e'
        b'/+U132t5Mx67vKrdM07xa8inH0/YP232npR1K8+GRVz+3KxK2mPZ8UrzmPWXW891PLo4OHtJUErIiYBbMQU9dl8XXu3qLAs++bcr5ZfObP8ysX1u6PYj+TkDFrPHQOBK'
        b'j5uB+R71+KFJDVFbb3re7rm153z9rIAl6XO/X/vQOysiNOCMsi6qVu34dWCfuvuzL964kFzrqfXRXsx36+yrzF3g431SaUhfXhJ0xDdxQ5DB07S1fnP10sGu76YqT070'
        b'+uIrcHfujGsfkd4+T4lrYXcLSrddCsuSnDMd6HFqDZrEU9f45FvqNoga5I28KzXkLNH07Q55vd9V3XNpvKk9LH6ypN/zaP/oXMvU09PF7RFL3gsLro6JfqJYfRa/Hr3X'
        b'vP1I7o0ZBzu9sxrkZ8OFHSsm7ers0T7QlmzWuvDaeEfzt2RnR1Xke1yqenDB7VDye1+p055tnHdnY3ZjvL2Xi2rjopNPUvO18xI+E9WmFHXcF3YxR1uOjm6ZdmLhjq67'
        b'J9wt1hOmP7r77GqL84kp4Y/n36jkh2ijS5/+3PZ0gfKIz99bv+kvPGW/54M+55C4e/fm9T9sUiw8DK6VyV0DQ29JZkc59HiOeX/WitiWSWlTTibX3ihwr6Ee3wkdVZpM'
        b'dpd6Dxp+igr1e3DE7czibV86fbp8doNm6duHBnqPN7VQb3acmJ8RvGjmrkepnY33pW2bI2zfSUhQSHNOxcT/cMW3xKzZd674+p1l8pHJl0/YZ3eU/HJSYK8v9XK/Re10'
        b'bQrbdCnobPaFnVveJe/8Q3r1Q9XPZ28U/jpht58u53bboGJV17fNkYVP484NJFWuehoXcMNc+evthmN9Opf7r1+ZUYh731vE5PSLbNgYdMkr0fCHWUEfjeOmk6pgF45W'
        b'V5u04ncB7oFxw9GuHrksNwrFa4EtiOj2VsYLk1W0071sIjnoluzGbA121nZwibdAX7AGFJmFcHE+QGLu+ZTAHhxhSWZJC3NgLaQxwtXMAftzsuz4mMscEi4bWyj2W+Vy'
        b'szFbmGUGBxzocrrCQWBnA/Y5ZPMKfDGRPYV2J+njJhScCtZp6XVs1VfRrP4vtenK4balFJ8+ZKLb2QDgwmU+yEI4NtwmJgA7iQC4FJVzLXa/WWCkKwVZdvRGL9BphOtd'
        b'2QtaBD18+lhYuMkXXfpqtFfNabg812+phxP27zRcEvn/malt2h8g2vSlg8idnWT/KMDl/pbJNDq5UiZjg7HPQyDEBDENH49ERJ7xCSEuIChSgPNJPsEn7EknnpOTo7Xj'
        b'WEcrJ76zDTXSmXCJJiZMw7FCYgaBz2RTKlEkiskdi8rErvh8b1RGKEOH0i0RimD2iHhr9lCJq6frEsdw2DZJOErQp7wih+uKCT9CBJ9iQoStoXazZXxCwpbAByxrQfHW'
        b'/KfDgeECRwHugv/+ST2jnhoUv8U9k4Z76OKfx4EHvvyB8XJHJc71CBuHjfoJqWMa2Vznl16QKWw8hnjoqd7Q56iGlklZAugF78fRZXS1FWY/hvSA5bvUTZv6MeMoHMNa'
        b'E6ZOrzwd0zfHOUKmaqyP7+/aP6FopF+/38yC9bZZ485HJO117YvMoR/+OPph09siL13Wo1tHki+UFk8s+Nw3s69/cIT73luV1xYHJxdtuhi82bX3auCTg+e7W/au/CHp'
        b'k0abQ1MPVFW88Wl7zOV7vaIFxWN8i2f9aBd6xbZ9+jtXEr3r2356HJBwse3cttPHzpL21J7I3XMer3FvG2EbntAd5fF21WvLeD2KL7+43TBq4GhPR8eZs/3HP8/ZtnmX'
        b'aHTryNP+PX9Zcqkpy57G5gkqUuRCt5FxNz/5kzDk8nqrce8K9lU7Ws3sGzEBrl9TnDYPCO8cnFM+a+rSAZtLpxZtLXG72jx/fcjVW/j0wYDvfbR1j1c/7Pkl6uZfA56s'
        b'XLrOoBSNY3WXkt9YiEzYhAQraOAhHq4VZkt3EmCXGM7hiHG1Arr9+2IT/EEHqoVC10dAC7HXmYROUWcmWyWTN5a7E3BlM4IPpGjTB94IJ3IsdFjLORm1Jgd6Q2y0dATY'
        b'6Se1wvgUIYA2bQ1LH5kI2mcBSwA0VBMx6AHVge3gIH2Qo49s4/mKQdUkxCWuwMGhEMx6MgEdiw2vs63KxtIfsctkXhSSMovHoQv1MV3CSW9Ve05DMff+cZ5DQmH2oJyM'
        b'hz5JEcs1twFNAJ6RRIANC7C5+3L6YuO8uKVXGg0qRdEU5gTqVQISGtCH3LhraaTLFbExkvjpgThvLGYF6gg+3eTMfjjbAxTFTg2En4wdUkHzNNPbyBBQTG/glL2qoOu6'
        b'H1WJlnI17EF7CjhMTqEtkzkb4Thcrj8EFj9QBUrRdjuJUYtw+jA5RIt+R5KE+IDSQFAnwTBqCg797k7Qw3YlDlq9xP7QjG9NQuJ+mTg0J8rcuCSC3flCMdK4i0NfK4U9'
        b'Q2F0PV3tVkDRRSl0E9dp+xaC5lh0ZmB7GOwC2OmYrYgANcES7uyhJ093GdkKmyRDFWyiCXpfBtjB2hJ5KXSdLeh0AD1Gugwc0IPuLNoyClgc7KD75UVZ0WvpGu6rtiUi'
        b'GQkksTLRFzWIFK83EaB5VCJLJUz24KP0tOlg33N1Ruji15hQkmjQTn+8LJbeMynaHymSbYUdUMEKRCZE05UB8f4iPrYgwmrl/EC2KRG9lW62hQ1143TdXNhJtfBCwPsT'
        b'2O5cTK+bh6KppXQLHxHjeStxsGPZXJb0Dragfzx2sbyjAL+sIVMMes+1rmaKLp6dywkENC/HYKeXI1HEOMIM2jBrH4K2rHJm219gGyCO8ZdAR13qPxnHhK+QNnB4r+VU'
        b'FFrt4HCBdyV2MmJ3gmp43iMDhUhyuDEjj+2mMdCVPyaOkvitikVCzuh+gBpE6ugtZO94OHT/NoqRvxaLsfsqH9B1dNlwgie/lz+1/9+XilEvwUR5npc4G4LA3maIoYnk'
        b'1RyHjgSsEJqQFU8bOnpGrUYia8QzlIVYgOvJ/55kNvyglnJ0K9Z+kDCkRqU16OHixvBMZr1GxVAatdHEUEq1AqJOr9IypNFkYHipeSaVkaFSdToNQ6q1JoaXBm0t+Mcg'
        b'1y5XMTy1Vm82MaQi3cCQOoOS4aepNSYVfJEp1zNkvlrP8ORGhVrNkOmqXFgFNk8azZkM36gzmFRKxkZtVGuNJrlWoWL4enOqRq1ghBEc81Eqz4AtCfUGlcmkTsuT5WZq'
        b'GEGcTpERqYZnbJ0aGKTSIsUqxk5t1MlM6kwVbChTz1CRC+dHMnZ6ucGoksG3EBWcGZGpU86awaU/kSnVy9UmxkquUKj0JiNjx16lzKSDdqR2OUMulsYxtsZ0dZpJpjIY'
        b'dAbGzqxVpMvVWpVSpspVMNYymVEF+00mY+y1OpkuNc1sVLCJqxjr4RfwcsxaJFn13EzjOt/PsBIZcmsQrEJQjKAMwToEZgSFCDIQrECwHoEewXIEqCFDJoJsljiHQIMg'
        b'H8FqlnfLKtghQBRFw1oE5QgsCHIQpCPIQlCEoADBuwi0CEoQ5CFQI8hFoGJPA/HyStFRBQLTb3xDNL6sh+2uZS/I0MrWGBSkwWGkUqRPZhxlsqHjIft90HXo9Xi9XJGB'
        b'9MsQExa9p1LGiwQsa5CxksnkGo1Mxo1nlldojQYyn0s+a/gGlVQN28r/lgiaEYTCcWDWqGYjmURWVIHCKL6A+N9/WVihMytbKMT/CY3i648='
    ))))
