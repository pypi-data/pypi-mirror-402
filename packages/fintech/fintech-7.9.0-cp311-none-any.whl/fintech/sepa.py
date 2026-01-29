
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
        b'eJzMvQlAk0f6Pz5vDiByBRLuK8gZjhAOFREPRJQbVPBALQQSIIqgCVGxarUeBEENihI8arzxxqtqrbadabs9drvETbf5sttd3aPXd7elW7vbdbvtf2beBLlsbb/d/f8w'
        b'TiYz8848M/PMzOd55pl5/wgG/XFt319sw04nUIIyUAPKGCWzBZRxVFwTD4zyp+ScZAA4y9h/a1yUXA5Q8U9i/9mBVKuA1mURB4c7KHlD0z/L4FBH1bBcGKDkzwWCWqnD'
        b'w6Vj5mYVZ0iWNyh1dSpJQ7WksVYlKW5qrG2ol8xU1zeqqmolKxRVyxQ1KtmYMSW1aq09rVJVra5XaSXVuvqqRnVDvVaiqFdKquoUWi0ObWyQrG7QLJOsVjfWSkgRsjFV'
        b'0kEVi8H/nUlr+GKqmkEz08xp5jbzmvnNDs2OzU7NguYxzc7NLs2uzW7N7s3CZo9mz2ZRs7jZq9m72afZt9mv2b85oDmwOag5uDmkWdIc2jy2Oaw5vDmiObI5qjm6WdoJ'
        b'9H76YH2APkwfqQ/Ve+oD9U56R/1Yvauep3fXj9GL9C56gd5HH6QHeq5eqJfoo/TRerGer3fTh+j99b56Z3243lvvoPfSc/SMPkIv1XtUx+D+clofwwEtkUP7YH2sAHDA'
        b'upihoTgkdmgIAzbEbIidC8IeG7carOEuBKsZ3D+cwqrB3JCM/4tIoznYWGgukLoV1jnhX2vWccFf3ATYV1FnyS4GugjshS1oP7qAWlFLUf5spEc7iqRoB+zKyyktjncA'
        b'UVk89JKXWMrVBeK0qGX8hrycuJx41ILaCvjADW2Hm9FObmE+OqLzJQluouvwRXQEvkCS8QGPx8DDU9B+XQiOFKvgaXQHbY+lTxfkoB3SHB7wRHu48AV0q07K0fkTeu74'
        b'lCQK8pKScXwe2lmEc3EP5U6Cz66kJMAudNMD6atIgpwCNt4NXeAmwh5fnANNsqsadmhJJC4GtTFgzBx4NocDe9Tomi6cJHgBmuBRZ3TZHV3T4vpfX4GuroSt7q4ABIbB'
        b'a9E8xxgHKaPzwUkneGehy+gias3PRW1cwEV3GHhAXoJjo3GsHG6B+/Pg+WjcItvT/fNQG2wpIjTBHQmF8VIHMCvLcR06uhAnJ1VbCO9gmq5gqvKL4DF4kw/46xh0HHau'
        b'spWGjuc1xubGxxXEyxjggpNs8uKOWaDGsaRe1YFwZ2x2XAxqySe1chbBs8jAQRdgJ7pUxQxigRQ7C/wWO3uTmzEbYO7lYa51wNzthDkaYN52xrztivnYHfO1B+Z9EeZr'
        b'L8zLPpir/TBvB+DREIRHRwjm+lA8JsIwp0fgcUJGgFQfo4/Vx+nj9TJ9gl6uT9Qn6ZP1Kfpx1SmU9/GM0uI8jPc5lPeZEbzPGcHfzAaOjfdHjRvg/S3DeT9oFN4vZnn/'
        b'78ARuAAglFd7Cn7fWAlooE8pB5ApVV59oekfFVls4OsxTkCIw+Qz/3cNTJ7LBta58QD+lsir5xW8kDYXnAZ1Y3DwCl9f3gNPMK1f1MT8xjcmJ8HxG1BHBtgHXl2MxEHh'
        b'DqZVJP026Wj579ng6bov3MWVsSGc4nvMN75vz4egD+jicURuHeaLVtSaMDs6Gm1PyMb8NDcSni6Jzi1Au+JkOfG5BQyodxdMRh1ory6TMPHhWeiGtlGzaqVOC3dkouuo'
        b'B13FvPo8uoSuoSvuTi5j3ASuznAX1MO2JHlK0vjEccnwOuzh4SG2SIDOc3W6bDqmQ2FHXn5uYU5BHtqFJ4A2tB1zaQvagamJjouRSeNj4UXYDc/NwU9fRp2oHe1FBrQv'
        b'PQftQR3zcSvKXT3HRg3hQNKohKG/WEc4kEPmbsyDDOY7fjWXcgheiVp4wziEKxilz3EIdwQXcDZwbRwyatzjOYQ3CofwCjWki9WfK99htLOxL618woG30g+Fbl3JcMf3'
        b'vnmjrX2TYlxYW3nrXJUr4sysC/j2D29vXDPu2ebKPk4kTFvql9blI6/SBcx1RUkmwdn7J5WXDJUaObfGARxe4ak7+KKU/8CPdFkzPOmLe3k72rUyn0wnvIkMvISOzGFj'
        b'u3JgT6wMrMd90BLHAAe4kxOPjqDND+jMuhfuRFdj49G+ldHZ8Rwcux/HXl31gDQzPDpuSmy8Gp5HO/IT+cChjEHnBWjrA1LTwAkOqDUbngdgErrFWc/M1ARKeX2caKkG'
        b'Mzl45GhJ00g2btz40Cu9WtOwVlUvqWbXdplWtUIxpY+rUyvXEodDUi/BzlcbQf9MDhB7d07YPcGY0j65Y7J+hlXkxf48nLY/rSv9YLpZFG0RRb8nkt0VycwiuUUkJ4l8'
        b'OtN2pxnV3WKzSGYhn6T3RKl3RalmUZpFlNbrkvYF6S6NI3akDn2CesVylRZjDFUfT6Gp0fY5lpdrdPXl5X3O5eVVdSpFvW4FDnlUGdK9FRUSXB+NBwn0xA4lfgaJXUmI'
        b'/4qQn8VhmKB+8F3OPTcfvbplWduyjc79HD4jtjp76ie0TGybeI/nvjFvU8GWgo0FVid3q5NI7/xVP57ThUNDNxax/74gTLZPEAfOuaVxZ1ZxRuPKDWS4cG3DhUcHjEM1'
        b'b2DA8P/jA6Zm+IAZM8qA8SzUkSC1B7qpzeeDsGUAnQbw1Cx0VudFuPEW3BichyPKYScjBagZnoPH6RPwRHQTulLEB2mZDB/AayLUoxPj8A1roB614nA5Os5kYV5HJnf2'
        b'gZsr0QlnjDSgsYbxwDmv2cCG357tH4uD8eLZzMwG6EDpOhqOTqA9brEyBxCewiwC6FQq0utI189Fp2agPXhshy0Ea0FBKDqm86BDTteE9jisgrg94kDcWKlUwGa/9emZ'
        b'kzi5cBPOcSv+wBYBTS/V5T7NQVtmkYLwJ1Sp8yap29ALq+EtB7gD3sYxnfiDDuTSKHTAU4xojAn/uI4/8CV0jpYxZzw6Bm9xl+FQgA7hj3gNDeevQjfQLe4zcDcOv40/'
        b'S6RsKWcb4Q14yx224zGBTPiDtqFTtHYYvnVnoGMcZAghgNlZUElzimqAz83l4ibC1YgCUUgPDbbGg9fxcrHHcW06XuaAXAJ3seDtDNyPm34P6nQE6DI8gYEUKHdAL7LQ'
        b'5NmUWrQfHkFXtOjKKgZwUDcTXlRDZ84RUz9lmGDCy5iPa8A6sARDgnVMC2cVuOiwjmnntAmIaEFHNzvEuX0cmbyPqWJHLxGD8NilQ/fhmPQ6tbaxqmH5iilrQ1T1VQ1K'
        b'VTmZkWTpdQ1VijrtFNmjBAvI08Hs1NTrO5H9GFd2e3Qv7Q7pDjF6ELc7REPZ90FlJ0d7Dvv6rZMOvJV06Miea8bTe8YZQ7cmpm3aKt06cWvE1nFb47dO3hq2NXnrMrea'
        b'+OINeEHocdHPR01Lzh2Ky3r9huXkioQq3pnqGd2F9z9WxldF7+Z8UvHqmc2O3c0C/FnyS4fT/tv4+dYHphfe2Bo6L82h+8K+S/sEnfHj2sblf/T8gzcaL8dXvP5J5O8K'
        b'57lM+Dy+4pWTz2+euCNx60tbj+15l/+LJR+FZiz+yiF5xfO4XjPkzNXptqUEtQO0L1YmRdurYE8cwMvBOU4yRt/nHlAMfXS9H8aRSJ+TX8iH27yBM7zEQYfgZp8HlCv1'
        b'zkmoNQ4DbLjdE4N8h6c4YbVND0JxlHcC3IPZ7CjFImg7hs+oBZ7L5QNRChftXg3bHwSQDK6poAGdYdi17NFKdgN2SR2HrSujOVpH2sFktWE7uc95UMeuHfyDLjZf2xab'
        b'YrzYeOFJ2dXP6uNrcLIGhXaLe0peFj/yBIb08zk+of0AO/pZ/Q7Aw7PTcbdju6BDoM+wuvv1A65rvFXs1Tlr9yxjZnt+R76BsXr7GxUGtUFt9fU7LNgvMIV3c82+cRbf'
        b'OENGPxf4BLCxOLPgiMNL9i/pKj9YToiQUqddYOAZqkiWObtzjEpTplkcbRFHGxicsTDgPWHEXWGEqbpbYRbKLUI5JkJIKRrgTvwxZWDH7DvRgl1hmkWYhlOJxGQVbZ/Y'
        b'MbHXJZDyKztQHPsYbd+Y+oZyLRaia1VaDelQjc9j2phdAm1rIBF9hrRtDkm2CtjXwiK8FgaQJe97nJ90QewUxIPzbpO4T7AeEgDJH7Ie/ucB5AjxejQAKWBFjEOhnoC0'
        b'8TSnisVhE9JYwUFcnwMMZJrV6GIMPolgJg09pfYAEgBSN06vcflaHMMmzS11Bng1dDIFKl18vOsBXRozRHBrshyXisflNgGoRM+i/ep5H0xktI04NvR/tWTm2tRyZM/N'
        b'PSv9wrhoqWTbRvHrdfIlP99Vuk96gD/DJ/GE3DG5MUlW8bLDPubzpakXWy/tOZ09TxvYvc/jQF9hZEnA9iORp3qOy68m5Yy1JJ6UH+8Z21rCrIx/wz1unEvtBeXb1Rzz'
        b'Ky4H1WBvuH9L01Qph2LOYMYpNp5CUXgKbaJwFO5FxgdEUh2PpeFYWU5cjPQZeFSGBRjUAoCvhPfUGGiU8h8/LfABC0Ftk4JHVa2qall5lUalVDc2aMox/hwZRCeIFtsE'
        b'0cgBQpFea0huWdO2xhi6fZ1+nVFr1JqSu9YcXNM9dv9643qrT6BBZ/X06pTulrbHdsTqM63u3mQkBxm1hzfs39BdYw4ZbwkZT4PYxEKRIcMw3TC9w9EYZqw0rjRWHowy'
        b'C0PJKA3vFYWbZptFURZRVHfKXVFCr0vCkNHKrVIr+xyrGnT1jZqmHzBY48hgHVnbRUOHrBYPWX8yKL/H+amGrCYKPG65X2sbqlTX8EjOY0YZpj+9JmAEbOWPMkxnsMPU'
        b'M11EhmlqilNF+l/4StuI1LsLyYhc8/s1FS61i31ACQsQTxTIkwHcjP2JIHEBMtG0Z+qpMqC4fVpF3K9nhwMWVb2AzsKTybwMhId7EkhCWxJp4msNXNJI037lXpFf6FgM'
        b'aL4Rc+DlZA46qCT6uuR0eIQm/STJBWAgtmDnwor8mNA4NinUz4TPJzs8lUT0Oimwaw2dFuAhuA3dTGa4cB8A48A4+CI6TPPgjvUC0bh2BXkVgb+IcmPzqPGFLybzUTPa'
        b'j8cmGB8mpUmz5YEgFVfj7OyKwJp1PkBHODFNl5LMVcHnAJgAJqAti1jtxzoJmAbACv/VFekopMRWYdMMtD/ZMQHhXkkFqVAPb9HEO7jhIBuAaG5exViNSwVLATqoQK3w'
        b'CtCtBmAimCjj06Rec6SgGM8MW2sqpv9WwrAUxBZPhld4cGsGJgakLVbSlAtWxAEM7tYcLqvgfMhdxaZcsSRByxsDLwAwHUxPh8/RkvxnQKOWU+0KQCbIhLfQRZrUXQBb'
        b'tA7w5jMAzAAzxItp4GwhvKVlnPEMkgWykMmfxfgYHrdr+YSdZoKZ8MxcGpoF90u0XNSJUTGYBWZlJrB9c56HLmsd0R7cONkge3Is7Rt0SVKGrmDxBm4DIAfkoB70LCud'
        b'nC3DU+QVHrozH8/2IBedskk5e9Bpb3SFswheBiAP5EFTDYvrdwqC0RWHiZgn8kE+lqNaaFu01DsQVZZ8ZXxF3d3SIltvbJ+2HF1h0B05AAWgAL0IO2ji+sYxZFGR3/Wr'
        b'cPkqLNXGU0dAIbrC58NLABSCQk4COzA0kbgcIG+PreCMS45m23iWPB9d4arhLQCKQFHRUzTlNocYUII7ZbVnRaX3hgRAqXWFJngDXXGEe4MwU4HipBCa9pUIP7z6geIJ'
        b'NRXpX8/LY9NOQwfcnYmctBn3ApjNh3to2g8mUdWb782aivzj3gqWgmw/nTOv7GksMYE5WL67Q1M2hbkDvNJMWyqviHuqKRPo3MkEqhA6cwLQLizvgbkuLmxnmNCep50d'
        b'cGd0AUxzCdqBTrGtqAogilKn5KCKwLgiOZtDdOkKZwYexUJvKSjNbKAJX54bDLCgtECdWpG+Z8IStgWnLp/jzIcvQCMA88C85UhPk85aPxazF5B/417B+fmkUMCKw23w'
        b'GrruzMVo+ygA88F8dAeyyddLfbDYCaJXSivWfVmbzzbNTLijwdkRXcPjYgFYAA/DSzRtTV0CWIxXx19OreBcn6JjO12CLsHdsBXXshmAhWBhKdrJ9qQwBdQSlsysmDPn'
        b'mQgWXlRLk/A8COTnBRWaPO1MNpCpkYMKPH5n6CrGVvlNBlIOJUIGz2K5sZW3Hjd7GShbgm6yDNyB2lWwlRODl4FFYBF6DrbVffXtt9/uj6ATom/3rIr8M+FJbNYta8aD'
        b'Olw775gKjSh3EVDnyV4D2tl48WjiuW7dnVMEi4U/q/ndMufu7hvHbjx7I+Henao/TOifcfT6t68Z10zzdFE3rO3+fGabj/vie7Cz8WFx6+uvdr5Y/kXaF/97NXn9uw3H'
        b'39j1VeGelrLLv3Fed3bzspyMJbs/22g6XPK32Hzdw2XjVNfvFP1jzLx7v/7nt7+t+XBbBTqdOFY/puojz1WZzk8Lff5+tMi6a8sKsBmGujjPkscEJtffvfHH1w/J69+6'
        b'sef1Q2MWn05e/he/ql/6P+2mVjh8AeO8t7Qu8JRVZd3YPu5+2vgtByoUbk33vZ/fOsnq9amifM3GzPseO5f9tuLgPXHNZ2deCQ79ZGXbW6u++vfJU1vfee6bgy/zl3x4'
        b'Qdx+Kv2vMcfP7swP+/Plhve+LP9345cXBc85zhwnK7rXee7tC8ot16Z89uGS+g+b9jXcmufbeT12y6l3nrkva0+OOqlJOXfgyO7XSo5L5h1xXHJ8jKN21+QN4HZjze35'
        b'X2KhkMCuNHSnFLVq0aa4QrJHsCuOwYLfWQ66kIlxGZHw4XPeY1nQBo/CazYd4k7U84CIzOgY3Oeeh3bEPhWBdhTE55L9G090g4vnnWfRcfb5G4sSsczXlpcDzwN0NRg4'
        b'pHL80Nl5D/DKCZLRYXhFC89nQ72mMD6abPKgXVzggQxc2LMAbZY6PYFkyKIhwj4SieQRHOpzsyEhXVU5EV/WDvtNQWA3hwWB2dzBIDBx+3o9C/ruibwNGiNj0HRM6Jy6'
        b'e6pZFG4RhROYF2j1CTA0DsGEGCX5uRHgN7ufS3y+AUabTxJmsvmiY7ttPnlyj82XOunGHNaXMePlStaXW/CGhvXNnde7oIz1Li7vVVRR7z1aCp/4aCnUR0uhPloK9dFS'
        b'qI+WQn20FOLrB+QnLYpGsEVRL1sUTYTlYTEuzJH1+wUaB/yh4aY5dn9MfHel3Z88vkdj96dPfZmx+2cws5g3Bn7lM0VMb/FAZiXMfIYUb/u5hKlgCAn0pxMhYU6/gPX7'
        b'Bxkr7f6wSJPG7o9L6OGwfsAGpKW/PHZQAHH0Of0uwMtbn9XPcXENej8kulvUPbe7snvuOV9zSJIlJKkfOHgkUqd9FkbwjVYfX2Niuw4/7JV4zzfIFPBeaNLd0KSeFHNo'
        b'qiU09UaSOXSy2XeykW/kk9YJNvl1pxwPMfvKSYg1MNQ0vSvXILCKgo1NFpG0e26P57n5d0UpvaIUa4DEOK6fC8TjvvqzKJCKDo8cynwGXT8X+zFsvyfyMaRo6Zo9IUMy'
        b'wx+86j9mRjT31SgGu3aFNxdz9uOlBardHiQsjMfO8CGhJAlXACIpED03l2E8iCjweOcnFev3CmLBWbeJ3O+VFciuJBgkK3D/47JC9ZOI9I6srPBMLkXk0XIH97L1y8bY'
        b'ZIUrAaygLneYJnsjbTy7FqMdcthuk9TdPbCgvi9d/c3UXJ6WiGxHr0aRHaUje5psCsRrRtS05Of5LofaDv38bd9NR9vkZiq1v9oBxS4pRPd4ZG+O5wXnaGiAbXFz+K9e'
        b'c5l2xbjUt/fnlW/axfGU+x5rb3KkDNXpYaR7foFdINf70am9aKWUN+r8at/qYedWf5ZxtI0aXVWjDsua5RpVtUqjqq9Srf2OODrnLgTsnDudB8S+ZEunPb0jXT/D6u6J'
        b'J+CUlqa2pkETsFWIJx/DHMOcDidjiolj8jBxDqaahWFPIEg79PG0uOQnHxLpZEh8B/XPDhkeGTyG8SSj4PHOTyZCY5Hr+0Vo3jAR+j8/LEaI0NxRhoVDISuYPLswQrjO'
        b'WYOToHMAdmlW0HFhcRlHYKfEmFGRtFCzDMxU34iex9MSNaOeW8wOgJWPNOht03Q+oM1qOSGXcbdf3Pa21+fJiY1JuqMtJ+WqKxtVXXOMm/02xvj2lvKo/lvs5F7UabRp'
        b'nxY6B9iYHXM6ugUvYCBzDJ5/QCwAoAHthh2s/kmGdi1wGlA/JcFWKXc455B6DowF32Eal0cj4bExdBwU2MZB8bBxIPIhUMOUwm6C0uWgO7M7s4d3Oudczg3OmcLuQnZo'
        b'iOJ7RfHdSrMo2SJK7nVJHsr7VT+I96cT3n8svS1DOL/ov835T6Ln5euZ/xf1vI6FJZTPX8hwA39aNwnLUhV1gZm1rLiTks4DdWm4P6ZV5H+TtZANfFXIAY0b3Ej/uLwc'
        b'FwXU3yR8wWjV+HfI2uep5nYP0d2e3pPYyjjsS0ySn6ve8vlSvzS/Zb5v+baWpPn5vJzV/kqS5CnXD0/IVZs/Hvtc4QfiD2JkDttk1ZJWfsxbxp/9/k2nq+0RW/3efS5G'
        b'8mnlX1Z+pnSpvlfHgA+X/e5Dsfk+luhY64Ij8CJ8CV5Gm+DZ/II4DuDlMfDyM/AglRy8klEXao1DOxOKCtCOwhx4jgd85lS78cb7cX6Awta1XrWmsVypU5UrFY2qtUN/'
        b'0nGy3DZOFvMcXGOtAXG9AXHdJecWmgMmWAImGJzweDGu6RVF4U/3jItFZ4rMcZMtcZNfZu7GZfTGZVgl0u6MI66GHKuPxJS4e71hvdUXw6sAo9qo7ma66g7WmX1iDLx+'
        b'V5x5vxseifq8IcpYHqGjT1CnUigxSU0/ZPOEmMoMq9AuMEQXu4j3vaYEP6k9AauLtVuMkj8HO89uIcOJx1pM4gHF0TvQzRNHvVO1Ax1U3FGMCXiCUYYJDuGNGDjcDTzb'
        b'oBo17vGDSjDKoOKzSGvd9GSqnfjEoSJp82otO3y2ePGJXiH1xVkVdfK8WqCeM7uJr23FMQkffXLgrfF4PVk+sJ5ccxnn4uzbUvwz65tlygVwu+EzZYFi8eu8EsQTtTCX'
        b'l3Yt7Zo0canxzMavZTv9t8VVG+tcteMXrPYodw0TZUbNH/OrJNPts/dXzd+0XHp/hhWUvLYQWd/ctNR5QUf0hM11Hyt/dpVfynv3Qdk+/30VDu+4gE3T3P41dtUhYtxD'
        b'd89PokvwPN03dQREvj46mymFm1ZSdMZHJhWxiIQX0CWbVSR6UUz3UmEzbM/MQy1x+NEdRQxwQm1TGzlwC9wURfP1WIyMOEqfEI9uovN43BYw8KV4eJI1/HkJdSxGrQXw'
        b'HO4quGUMbGdmweYEqfOTitrD+Z6Y29ol74Fh7VKjGjSqh/xiBW/boF7BA6KAzrjdce2yDpk+0yry7kzdndqe1pGmn3HP3asf8FwT3vcJMlabKs0+UouPtJ1nYAyJ1sAI'
        b'PHgLiGTl3ZFqXLl7smGyNSDEJDWR0R53PM4cIDPM+LOP/z1hkMHVqDTlmIUyi1DG/qw6XLu/tmvpwaXdE7sn9pScnnpuqjk4zSycZBFO+lzA93V7ALCjz8ayojhQXzRo'
        b'PhCQ+QBPArmkjg5VusaG6scvsmzzUNtZ27xgmxjmkIlhSJt0kZSb2HmBNEsDnhgiyNB/YucnFcX2C+Sgx23KUFFsYH+Errz8AVGMGIiCav5/EXeOMNHzHmWSCGEniZ9V'
        b'vQ068BDpCW/IuKqy6RknTqKbE6lyt1SfU1HpbODJSQLWiNP7ZOIh9wVs4LEYm9wWeWJGXv54NlBQSLeDgLw+dZlOmcsG/qoiiGyNRMsL8wNrsyawgWnLqFZVIm/KjmjM'
        b'lrKBU0JtdqUziyrm+fLZwOCyaLKvIZczS5LPRCvYwAuSKWAdxqHyiesT29bMYAP/Jy0drCEFSf/+dDOHxwZOr0kDjYTOhWNlM5WNbODKlb5Ejy6XB3vM/hMmjgZ+4R9P'
        b'tkWi5bNrwz4NymYDs9eym8tyb26FOELABpbMngY2ksCch/PfnzOWDXwtgs9atXqbF+2ZrmQDZxTbZN6ZT899dtEcNvCTMH+qLZfXj0k4HOfEBt4kLUPqLliT9+2KiWzg'
        b'pfpiYCIFZX20vqS6gA1cVKIEb5CCwhymM1HzbR03rQb8nDwu+gqsWrSIDVSv9yY6caG8cEnxPXEiGxg5z41o+33lDobomJz1bOBHoWvBA0LSoj/VnVxoWzH+tZouI0A+'
        b'8cvlB6baauSzMoyo5YFcEVN/OyUUqJc+/BVfuxiPh1uN3L1zJ9UjucuJiLefiZr9MK/vnYlZDe2xwo+Epsxtbg63dbP/cXTZybiFa1/dvd0z5ULb0STe7M/ad4kFzxiL'
        b'iu+dfOdT0UbuZ39ce/2dF96MrXOesHJV07MK13cq70o3BhcfifzIBXyyc2I+/x/7BGs+aLj5s9idOT36151OLbj5l6TnU/Ydf63Z87O5TSknxMs+/+CKoGb99sgd56//'
        b'4tKzv7u3Zc6lN756etvXM99ZcaG9473ntj//y8N/7Eh667VvNnm3eT115LhnzYGSF3qu/fbKPAtP9NLtDz79eG7nw09OuAbvfyvUx/cbmZ9n9bbX/hz+9f+eedn1ZLiO'
        b'f+2fxfH35ht33XvP/JcJLyXzPljVcTPg/NJNafvf/0PS/n9vKHnTtD0mfoX3a78xb0hvu8c99GFTl2P54WvBjsl13f+TUffXppB3MEgLubJkdvL4l75duv589+8iEp9Z'
        b'KntXVFH05fXLX71Z/k24/5f+b11v2PuPPVNP9kq5D4jVPzyNboiHYksGbSXwkjcedaxl7ZU2wwvwhbw4tKsmOhvtyMNDHJ7lNFWiM3T1dJoMT8aineOfSYhhAE/HoBa4'
        b'E52Uev7IRe5J1kEi5UoG/w1aDj3IZF+pqF9WXttQpyZLyNqRQXRh/B+bRnoFH4h9DMmGRmLPo5/R7wCEYsP6Xvdw/LH6hJtKLD4xvcIYop71MnLbnamVkEFhDG1XGRXt'
        b'alOG2SvCLIzo9uiefdqrx/O0/w2OORqvccRQSOhhmG30aC81zm5faEo0i8PNwnASLDZo2onNk4fIoGj3xln5GzWs0QJ+Yk67ozHRxOmaYJrdPfbIfHNAXI9HT+UlH7P/'
        b'RLNw4pCn9NOtHp4GpbHENLtrodk7stvD7B3TrTB7JZg9EtjISmNSe43Jo32J2WMsDvEkRUdhj7uHYfr21frVVr8goxiv2xkmTff0I6vNfgkWvwSDg8Hh3qMIs1+MxS/G'
        b'4ED0w14GnqHEmGhUmIUSi1BiFXob/Yx+psSuwIOBuBnw75FB4uHPsAFJpNJjLcKxIwJIY/vQTJK6gg4GmYWR9kwf/9uexUrckBZhKO2v0Wkd/kyisZJ95jsIG5HrdxCf'
        b'7E8xTeqIpLjvPEV2DGbKuOsZ0esZYRV7GQVGgSm0y+WgC2YRA9PPBSLx8GT3XMS7irYXGTPMLsEWl+Bel2ASUrC9oKWorUhfdG9sjL7AGG52CbGKAoYgKac+XpNKoflu'
        b'8PRoa6di8HDSEP3oKAPoAklNNGIUQy3kf6+a4j+gsKAS1mBsYj9/9wWBvKyqTkXO54EyDIwEQOlETbY51VwlZ4ugjJzC4ym5W8DQk3VlfBrOGxHuQMP5I8IdabjDiHAn'
        b'FQ/LdtxqjtJxi9NQkFUm0IM1TNmYuQADLEGfY4ZSqVFptYVVDoNqQ/qCIq2dwK5+sZ+ww3CQnBPiULmRnh2qdqKgENPYMmYYKHSkoNBhBCh0HAH8HDY42kDhqHE/TB3D'
        b'Z5WR8GYQ2txQNhd7Q0EoOoTa2OMcz7+4kNHuw7512UG6nYluUO6StXx+zqFPF+tjV4B92y+UKl6Pyne7x5X8On+hJmdxeP4ift6lB7u//eLbPeXyDI7gben0bb/OjnYq'
        b'/vxtJ7ja8/rBWT+3Nva3HYv59fpjtyfdf+mgvqvsH1lF/zZfertf/btxT7vM+jKs7qlJn2eJzp6ofu/r12ZZ/9czJ+TjTwrud6wNm1d5zKQ83S4TnpxQx4twDfm9dAwV'
        b'79Tr4N68uEer3iJ0jdOEti2i4t3Y8XB7pHKYlW3K06xC52ZjVizci04SI+ABC+Bj8BorVbatR3voyTQ2Y3QLbkIdHNjirqZL6ti5rrFo31xZPKtCPc6Ro4Ook90Hvg0P'
        b'oW7YCnehXXnxcBfc5QicOWO8Oah5FjxCk3jB59FReBz2wNYivK6jHbFSeIYH3AXcxly4mSWgkxi9w9Z0eB0niYOnecDBieMHT0ED3S2G2yPwMt6agAVbWQ49xgevw2bg'
        b'iU5w0Sa414vFBacXuuE0MmluQTwDnFHbbNTKQdeR0fn/LOFu3DhYwnUsL69XrS4vX+tuGygyWwBdxl8H7DK+xhEEBBkcrSI/PM14xFrFAZ2FuwtN483iGIs4plccg+fF'
        b'fsDxSDQ20i9rQPDh1P2ppgWmp3o8e0p6ym7M6Q2fZg7IsARkGGbYH085lXY07Uj68XSzWG4Ry3vFcqsohBSQaE/xKOZ9n0DjfFOV2ScGI4b3fJLu+iT1JN9wNPtMs/hM'
        b'M/CskigDr8PVGhSKv8ZYQ6X4y80aEoG/XMget/OgOdu5j1tVp9XISPV5VerGpj6nFQ3EjF6p6nPQNmpUqsY+F139o72TxyvLSJNW0L9BCrNl2BnRnMSQW7sfsKIxKx3r'
        b'HBlmGkPm7f+b+1NN+lTGPywYB665ZXCHCs2MfRLypJPQOrB0IArPs9VSpvA00+dUbjP2lDJ9PK2qrlpLHpOwZxmc0usUyyuViilrhfaWsYe4MrbVcSPonnGuYCOgffUD'
        b'y8dl8stJZ0oZDbEPHlS2Rkc6ZESxbjjFF7Zixef8f3SxgnI79zxx0e6Dii4599QPL7qGLdqxnGXXJy5YOKipU86lj1bwwHqDhXN6gJHdk8NL7f+PG9Wj7chxC9W/WSBg'
        b'tJE46MxlrwNvpVBr8CNDdhSe9UtNBn3uDb/hvTblqpRh59ad8JgLnb/ZyRlLYD14gh4DT0k5g8Y2mQAH1Ptq7aC91LVe9nYdEkxnTLKykcFd6wR8Aw2NxhkHc80+URaf'
        b'qF5h1KA5iE87bLSJhe4sDDq/R9RpjynQk/QmmW3odKJw+m8gQ8q2HYIYcMYtlYuBCPnDM6oTnuYUy1Xl5X1jysvZKxCw36W8fKVOUcfG0HkRT7WahhUqTWMTnX81ZFdE'
        b'U0+cBntl+1zJwUaFVlulqqsrL5fy8AhjAwafc3y0nT9tYOJ9ijSVHfD9g8S/YWsc+7/+MWAaM4OxJo3v57q7BvaD73fGAp8QQ21vyET8MXunWbzT9LPwamdI7Q1Mxh+z'
        b'KMUiStHPsOJUa3olk/DH7JNu8UnXZ1u9ggwLeoMn4I/ZK9Xilaqfec/Vq5/DdY0mh3GGO59zgZt324LHxlPu0dFDSN0T0W1tfo40N17mAMbAO/DgUoxR0DnYOmTUONu+'
        b'v3gWs+Zej0eIXckQhN7B7XDvEOL/rh3uak41B/ts/85xTuKBdnYAMVOEH0nwPUbG9vPzQoyLeVsEw9A3j9y/QZC80uGc40lc7tmBbU+K8vlKJxwnGBHnSOPG4DjnEXFO'
        b'NM4Fx7mOiBPQODcc5z4ibgyNE+I4jxFxzjTOE8eJRsS50DgxjvMaEeeK22AMngy9tziVubFtqMRyyDmfoRIKbSkXLA35jpBP3GnufluAyl3pj/PHc9vZgb2sMqGtX9zP'
        b'BQwtWRmF8ySHgLjKwBGt7kHzDMIUB4+g2JPGheA4yYg4kb20DscOp2puB+9c6FB6lNFYCuLY7k4g/e6md68WKMNGUCCmpYTjUiJGlOKl5NL7VKRYGquiGOFh1JjBKiZb'
        b'KHs9ypAYYgKgxtJxH49MIqPNGYVVjuDRH9lwpgvFQezsdRp6dQpeyQR4LePiijADV0CQRgV6B8zObnSFcxxFzHMSjCK44RCnEauY4wYn2wo3atxgm5P7/riVh1SW/OXU'
        b'qxvVijr1WnJLTK1KorA1jRrjUUV9FblmZvgjaSsUGsVyCWmmNEmWGj+loY/mTM8olDRoJApJUnyjbkWdCmdCI6obNMslDdUjMiJ/Kvb5aPJwnGR6TqaUZBGdkZlZVFpY'
        b'Ul5YWjA9aw6OyCjMK88smpEllY2aTQkupk7R2IizWq2uq5NUqiRVDfWr8MSvUpLbbwgZVQ0aPFGvaKhXqutrRs2F1kCha2xYrmhUVynq6pok0UrVCo2qSoHzkcokGfVs'
        b'GrVWQo0+cOa4cqPmtQo3qhLjw5H02tqPMFgaJZz47Jf92Nu/tqFOifnvcQ/bkC/7vO0HbsS5RfHJiePHSzLyi7MzJEnSYbmOSihbkiS6YQW5N0hRN0oL2wvF1bGViH2j'
        b'U/wk+djxK5uX/dePz48FpWxurP9H5DVkJRvQ1wzCf86FujD8a6EGbkStiavRjjgZufcmbz7S59E7ekLgUR58EZrEdCvEOXcXCMTz87KJFW63PSKAbiKZPNBmtIvuIhcj'
        b'PVEYJKAW7Cuay+ZRiraijdnwfHZhQUFOAYNFd3RUgJ6PQcdplsJVdAesdmpURRwveiLQkWubIkOwmN6K2mLzyAni/NnZj9QEaLcUns6tBXMzHFHnYtaiprWMHpLKFrpX'
        b'5JcudWC3bdaK6e4UuFlQUbcgNQno5PgHMqAD6BDOuhk+9yh7pCf382B6E+Zko+35DmAWOuGALsGLLuqwG8Uc7T/xk4Ev/GvH7slEDbT1/eMfF2283NPTs0J04eXtr3q+'
        b'svFVoe9vtv7ifY9lp2S3wwtnZwaVPps9+4v/2bCh/Vc1n3MY32P1YRt3flD495p3/b9c3vQPl4qxT32uz+7cmhYmu/Svsgt7j3ifeP/BQ0nVH1oP9p4tbjBp/lE4W7Hp'
        b'nzlXn/1b5Ru/CYrZc+72Hb8vH17Yt+rDN+sT1a+WBH2Z+16Vv+6DO9deiClxvF/oVTr+b9cbzr8x4bm/x2/+5pVW5f2S3J6znt+s1F1H/5ztupgz+w+Hxs3+JMdT9bt3'
        b'Sz9oSznmd+yf0x6UPfjk3y9FfnX7X9a6sc/fu7TvpOWfObM/42tj7lxt/vprh7x7BbeuFUjdqUZmGbyd4IzbqzRSWqCLj0HbEzjACzbznLyeoTZA6GJ2Gmp9dHQgEu1k'
        b'Tw9Uo5vUrm5qSmyeLLcgLgfuQLvofUhFaDvwh1d59StsNhBXsFSxyW6Yt2wDPV/QhtrZjaDO8Yvy0M5s+bgCtBPutGUBvNAWLroRtsim1IL7smGrPY6/diLaz6AX5kXR'
        b'2EZ0Ep2FrXBHShHtZC46wEDMV9dobHgqPEIeZdmeD7vT0QscBl6ppMTPRxdI9CB1lW4uVVihbejWg2haf7h5FtFI7ZDSC6rYeiJDNZthLLzCR1uz4VFWeroBT+gwKS/N'
        b'wDnmM5iUwww0oG3wAlXc1aMWovwat75IVkDofJ6BB+B2L9rOCegU5kxMaAE5SBGXw0d71wK3Gm4aH7F5o5PwQiQm1QZtm9BR4JbJnfk06qbPJ8OTqeTxOFz1wvhsHtqo'
        b'AG6wmzsDnWyUuv+Um2DkRNSAomywugzLOWq8QpeXY9manctk9hAq/h1iWPGvQgB8wwxPm1LMPtEWn2gDz+pDjpB7jHvfP9z0lNk/xeKf0itOsYq87ZtjRs3uKYYpf/YP'
        b'742YbvbPtPhn9oozrSJyitVjMj3KO6Fr3cF13Svvhsh7Q+Tvk4STzP7pFv/0XnG61dvfwLWKggxpRqWptDvFlG8WJVpEif2A7yG95xNgzOhY3fnM7mdYcrA84SW1hoS/'
        b'FyLHufWIexRXfW6E31j5YpQ5ZLolZLqRZ+TdC4/uEmBPFaa8c+3ute3rOtaRagS+5xN11yeqm9ddZfZJsvgkEQLTKTlpZv9JFv9JveJJuF4kONLqH3RYul/aFXsw1pDZ'
        b'7wKCx1L1XGAI/hLYlXU21V1kjIFnEYZZAyU00vYlCaeRkiiTo1UcYBWHGPJMPLM4wiKOYH84mcVSi1jK/nAwi6Ms4qjPBfxQzwcAO+RhXG4oUQS6GvC/QTK4ByuDtxFn'
        b'B3FGk0i/f2NnOO8QPqkYpBQctOFjAlQpM4xxQogYfx4MqAYJ/zyNhfmpRHD/yZ2fVFt4UpAOXnTLGPNDtIU1rLaQX04A6+M1V7ZGsmuuFj9SmRlLDpbZNFcPI0oGgC5B'
        b'GBgH2iFGtEalUMY31Nc1SWW4OK6yoeoHELmFJZJXXqmuemIay4fQuNBOYzihESPp7yTxB9BWa29AglOfmLhKnEJznMRTomK/G+j+WNpI52o0ZHQ9KV2qIY22xN5ossFA'
        b'+seSGDiCxKXMIGJJQ0o5eE5XsCojOvafmPBaxrYBwBJuCUrYOLhtvwuS/18J30IJ11wDtqnqiWleNpzmZDvNCU8C/X+aBmfpbvghdNcPpzvRTnf89wsZ/5dRRml9YjJX'
        b'kjF2GdjHmLyESt2YrMG7SRIbt0nq6AWxjyXv/xFF/MOjI0SzTCJqayXqYdOZVqVaTq+2xcI+lbZHPEiuu7XpIOZimR+3TZZO0yApVjQtV9U3aiUZuC1GSoLRuMFws+EH'
        b'V42XJcnk0u+WFUe7AINfSC4uJWfS0QuT4PGlSbEEPwLeNAaewcBXHZwWydNOwtEBz98lGwnsJoK/ZZKftzypgplWmp9dV+07aetK118lSRrGJU8fH7zQ52DQz1/+H/HH'
        b'HHBwobNT19+kPAq3Merf0TSAUpEhmRREUSrcu4TeNDUVGiqJODBcGEB7UDcWCEI8WCz83NIAeBRuGXoBK5Z1D9FtbLEU9eTBPegclQc4TzEJ8BLsfOwGhiPZOCA3TLnb'
        b'edYWQFErOUVJrbWcgdi3Y3KvKNoaLn0vPOVueEpPydWFL/NedXqjsTc8xRxeYgkvMczoKMCgsGN9rzD8R21pvAboBulQQhqHbGaonP8rZi7PsqOboL8nOJ5DjIQZPAL/'
        b'm8dztuAR2DyC4eeqGln1oK6uUb1c0WhbynVaVgFGr5SWNGoU9VrFoNunK5tGZETySKNq17SKApwGZ4W/FDUqTcX3qGRG25KznWiInbqTqFp85VF/qnecygAdOf6kRVvh'
        b'9ceqWlaVFpSOVLSg23CfuvvtYK6WGLFWpHixl9Wdnr2n5YgoO6FKWbHA9VVh72s8sWqGT4Hi/Ns/r2bMWV9HrEg0Re8/E2m6U/jBmi2ybRUO73gDww63bbuvSDlUkowS'
        b'zCYKAVYdcNT9kUYAXp3zgNg+lWZF2gRiIzIMEooHS8Sr4e3vOGU6yGpSq2ost3cUBW1r/ezMPyKKjscc23ic4YLHY68ozBoQaZxkajQHxFkC4gwzrD7+Bq0xpb2po8mU'
        b'tHuDYcP7wdG90pnm4FmW4Fm9vrPsolQv/Qw+B8QO0R2PGaePOQD0Nhmuj6d4AzPkMFATHrm+ZJR+j/Ofu5jpiYwV3IZW4omX+O0ErhLRhyARS5B8CA550tEow/M0uftY'
        b'MwEMO8g0sHg9Cx4ZpnUCejqBbMTYTyj8144x3c9nRtmlGJh/GjTqGnW9ohHXUq18HACrV622rd6JssRRVL2P128rWSUybUD7eU5ckEwyR7VSp9bY2leJfVWNEqWqUt2o'
        b'HVWnTmY/TIG2YbldqFBj6KWo0zbQDNis2S6qVmm0j9e466pYijKn52BQp16pI/lhwBxNAJxEY6cKl5XTqCCQ7rsn0dGM+5wKdZPxL3R6EXoxrxDDCfZy7ML42dmy3AJy'
        b'XKolYQ7S58/O5s6R6uAVeDpH8lSlRrNB/ZQATK9xX442hlOFMdwjjxuiiZa5wq6BHAC8jPaWYqCyl1mJrjnNT/Fh8VE77MhHV1wiFjJkoxnA5+CFCbppOGYlnu60buiK'
        b'q25eNjFbK0X6uHlIT/Tn8HRJdhwppS0nH21n8Ox9XLoG7gtHJ0s45P7m6y7FU0N05GI3eHMiujOYqBVu9uyK58fPcwTFz4BsB3gcvgg3q9/SHGC0nfgpRd/pA2+lkZnf'
        b'fH1PBEZm27/KM94P3CZ+XdXm4nLWT/F15OuFJ/n5LgtepidGdYmJiY2cXzjsd5mw3K/490tv/K7yiGdh+NPGtK4z1o1Le5dX1bdx9r8yRrTw5W2/+FRcXbL+ta+jq69U'
        b'7M/tCDG2/mzTBnAmKzng3ffPHfr5gvddHzSlT2r7/Zsuf1r58pdy9kT2O89FaT//q1RAkVoB2pWDFzbUlgeP6+jl/871HHTAEx18MJZUeWei3DkG7WAv/7frn0Mg0Rhv'
        b'5qGLLulUcZpfDF8YONh9Dt6kGuSXFtlOCYQ65VH9LboK21mTQxch1yu/hholzkM9ro+Ws+0J6FakfTl7Hm6hKmLhOvgSRpJwF9o8CE0motOs4eMmdB5uGTg3jvkjC3Wx'
        b'B8fl8DzFm1ObsmFrEbwoGqT0LRXTqFnPjCfq5XZ45ZHKd3ry9x2e3ThsgXw0k5DbDocsN0Oi6AJpti2QtS7keMFUgkbX4VXFawHzfnBMb+w8c/B8S/D8Xt/5QxSQtlO3'
        b'c3vCr8aZA6ZaAohGzCuPoctn5stVZmmOOTjXEpzb65tLNLNTrQEhBye+F5BwNyChh2cOGGcJGEeeKGafKDQHF1mCi3p9i4aVIjVO6Q4zB8gsATKSPJtNPu3lZPPgRdqm'
        b'BGW/DPjfYLNydqEeWCMev1pTq/Ihy/X7I5brIe23gyzX68DAGb35LgxD7m15IucntSLqEiSAi26Tf4jucEAth5eGJ16yTxCpnKxx7EqdSLUzjxaT71Ib/GCtgc0mkEcu'
        b'o3liAruHEjhp1AUmszRz+PbxKKRKuX285RpVdZ+DVl1Tr1L2CfDSqNNosHg9s2rwO3Rc7NXYDcidNXZDCQo1nAasfBi9K73TkqN3q3ahwIOHgccwQ4j1fMEoUAKH8EeA'
        b'C94Gvg14jBo3WO9wv+s7gQf7Xh5WYqFr+GBVxOONJEjbsCu4/dmB2yEev51NW5J9ij6Ce4GEKYg6RybJVNQTjYfCFle5FGORUUEIMcXAuGBuUep4eSI1wiAGEkqivVLX'
        b'1zy2+IEOTJPMrFPUSFbXqmwmHrjCpM6PUtgr9bji6xsaRylGo8IVqdemSTKGi4IVtup8D4oZOH0/CMWMKdQRmQ3dgSaXoSgG6W3bf6XZOGiODdQwSZ5wD9yDruShK7kg'
        b'AnWg6+i4G9rfhHbryI026NLEVXmy+JhcvJAOzmIg6+zc0mjbxd84P9jDAHQiyAV1oy4JFUr/FptNriMudlJV5P4ibgnQEaUHhj87Vw8IpfBYwBC5ND63YO5gobR1rgC9'
        b'lIAOUHwG21GbCrXSNGgn2hWbQ/BPLEFEbbATnh+0/58dl5svy4mPcQCoVeqyEhl8dCm0cA+0A+7YMASjkUqR0qPxOovFzThpfC4frEWnBFj63I0OS7nshfU70RUfWjhs'
        b'Qbe5gDeFgWejkZF9j9BBtE8dyz5fgGVucm4YdXGebgyi1oPT4ZWQ2NwCW1uiHVhAF0Vx0QF4erb66K1gPj1/dOG3C7e2syYDh1KnFmx/Ff66aiXYl//XbalMZeKkSsVH'
        b'lojOVzN/kxLavS/utV//67nlf9at4d4M3ncjuOGGt/DVcHB0wSe3Ks4vRveuvf/8J5/vao6bHG6I3LOa67a0+v1tpVO/cP3VgrvceQuWdJ19Y+6kz99JXGLW/H73L98t'
        b'mnpWdWRKe8i4kso/tBnWVL9W+/e9794qwBIEuvLXO2HjXtkgXy1Zrb476d99fr/9o3NI4fhwUTAGYvQmqJNwIzqPrhXmUZDCqWQS09CdB+RdT+g5+CLumZ3o0KhQDMMw'
        b'dDGFIqVUP9hD0RzcnZ33CM1xVrG3zx+vXZeXUxCDETS6vJ4DnGArB25yQmfZjX6DEG52zpsJTY/AmB2JHYGb2CvoTyW50AsRdrvY7kOAe9FmCgE9YQ80YNqKyC0kUbAb'
        b'ONRxxhZPoadG0EF4AtDDpEXs/fRx6Bg6ibsugYv2KuBWSt2sBnSLqB5DEu077HR73X+D1OX/tB1OFouRe+HOBFvYZpy1osGAwxZIoVq8bUd8qSvRLaaSbeE5zPv+kb1R'
        b'xWb/2Rb/2b3i2VaRT0c6iSlgTDOO51vCJ7A/aLI8s3++xT+/V5w/Yrf8/eG75T7GSY8UJXdFcb2iOJpmltk/2+Kf3SvOZvfIq01VZlGMRRRDykm2BsUYl3SPNwclWYKS'
        b'DDPtSWrNogSLKIE98RIUdnjR/kVdSw4uIQn8jDMO5+7P7co/mH9XFN0riqalTDP7Z1j8M3rFGex+daDEGhz+XrDsbrDMHCy3BMutoTH9jjypZz/AzueAFyp6QBy6ST0G'
        b'+AZ2rBuqr3FnYeAHxPmQOB+BH7Ml/cimYeimtA0wfklAyWj9R8xZtSZg25jGfTjXlWFiCRD8iZyfDE4ShcwRwQRw3S2D/0PxpJScXLHV+Ikh28+H7vSEEmyAV06KFAag'
        b'xeCtHSmPWMqf5hTi8mZKvTWbybPkthrNVsAew1I2VJWXUxMBDXkHIrVL6ONWqqsea5zQ52jfuCQadaqn63MdotaiwsAgMeJL+pS9sh7/mRPkHsNmi0Gsth1QC322Mf0I'
        b'e5Vy6fQwYKDP47gK+wFxnICbl36+MdnEN1V1h3dre0OSe/1TbiS/wcXiVje3J7Ofy7hN/Bxg5wFx7iVPsKZN6eemukb0gx/lfM6359XPI2GNDBAHGlKtQnJ4wyqe1M/n'
        b'iCd/DrDzgDj0OLsowBBtFUb2CiOt4jScQJSOE4jSHxBHn4kTDM4hg+SQyZAsMpkH1KWZkBMGViE5CG8VzyCv8ZhJ0mD3AXXp6zzYfBJ6hQmPz8dXYlhjFSb3CpOt4iyc'
        b'xncWSYPdB9TVZ+M03sGGBVZhYq8w0SrOxGm8s0ga7D6grn7mMHpmEnqyKT3ZlJ5sQo+TE2mzxzlie9fxjLG9rpFm10iLa2Q/R+CKh/1jHHL6IWoglRgERRizrUJ5L/4k'
        b'ZbKUBlFKgyil2NUX2FlEZAobVIqXq6QffJfzqCgSEjekC2eRLswh5WD3AXVpLw5OM5ukmUvTzKVp5pI0NlrCTNrulB6n3siJL5f0uuaaXXMtrrn9nGDX8H7w4x1Cch4z'
        b'kNOUIT00gfTQRNJBE0n/TNTPIv/Y4yIUD55CL+q0+YWsASADxiTOWctBO6fC50e874r8fVFITot4Dj0touSU8ZTcMr4alDkoeWWO+L+Tkl8mUDqUjVE6ktMUHfwOpw5h'
        b'B1PN7RCecxp2dkGOJUlnvbCaqxSMODlATlu42k5+uAw7OeBG41xxnNuIOHca547jhCPihB1uKg/b+W1HaurvrveodlJ6DD+NMYwWzw43WhPhOc9h5zmIDEzy8qjmK0Xf'
        b'k4sI0yXeMjxUTN49Wc1Rem1xKvPCbcHQMyTeSp8toMxH6YtdX3IqpMzPls4fx/orA3BIgDIQu4HkfEdZkN4BPxmM44L1APtCsC9EKcExEvo7FP8OVY7Fv8fa8gnDIWHk'
        b'ZEZZuC0kAodE2PyR2B9p80dhf5TNH4390TRHKfZJqS8G+2KoLxb7YvUC7IvDvji9E/bFY1+8MpGemyf3ACRsEZTJlDy6yib1OWQspwc/zgwRJcmyyUawZz/YF+JiKZm8'
        b'f69GQ6z8JaxsW9U0cIBgmBX+0JMkGpzBclWjukpCjpkp2M3PKlZExwFE6sZ5sjsGdU2ShnpWjh5NzpVy+hzKVynqdKo+Qbmdij5uVumcwofptY2NK9ISElavXi1TVVXK'
        b'VDpNwwoF/krQNioatQnkd/Uajar6kS9eqVDXNcnWLK8jtxxn5hf3cbNLZ/Zxc2bM6ePmFi/s4+bNmd/HLZ21YOZpTh+fLdjJXu6QXaIBc3hiFbeXi2ENR+s4GNqwm9Pr'
        b'hr3YWMkso7loxes4psEg6TGMrPVs5D+KU3LWcdZiCX/kK5Rb+OuYoaHrGSV3HbMKo5Z1jJKn5FNqGNPgOjzKlzuMSge/R/QMiVmLp6i1fHIbISmhHpeqdGT9xBhmOA3r'
        b'QPmAwgvXd1BNHldf/MTAkTelE7UBEtwvH00NNfyUjo2HHx3SGf7A45Q7tJdZ1ZKCzYOGfMcGFMsOafToy9yi+JSkxAmDh4hSJZPkVBNNj0S7QlWlrlarlHGj6oPUjUR7'
        b'hOG+/TwOLdmuYmSHo6KxUaOu1D1Go5RGotMqlKpqBUadA0OkQrK6Vl1VS3JXs+2EB5qtHDx4RtbtY8IXD73U9dRq6FFtoiK0UQ8ZWR8j/5hM7R9/i/8ecmVyeaHUsU84'
        b'vFhi46KoW1Gr6Bszj9QkS6Np0PTxtSvq1I0aLu7FPr5uBZ4CNDyGXC3LilbkELiGHMceDmIJI0gGadVNgNqsLB9iufsHgmBfAayAK8bwi5p4W0PCLCEphmxWXF1DXg5q'
        b'yrgriugVRXQveC9+8t34yeb4qZb4qTiAyo3pN9aYB4uovgFGrjGra8zBMQY+zsQYYUg3pFvFfsa5poxuLv6XdTHvTN4Nrjku3RKXfmOOJW6aOTrDEp1hDs8wB003i6cb'
        b'sgxZ9/ADpe2FhixrcISxxqTqqj9YjyVNZ2uo9FTw0WBzaKIlNJFck2DA/37oAXRWcKLN+jiZyd5YdpHpn0MMPRcN2TgfzPuUA5tWqCQVmLOqsCxTJ5vBfldUyDQnfzid'
        b'pxm2y5+Qzq+H0Gk/nP8wgFoajz7ihhDEsRM0fQRBTzLpLh1AMc4DDc2lfNrnpNCW04N8fU6qNSsa6lX1jz35P7xS3xJO9WcrpTy49L3gxLvBiebgZAv5pPcG2a8CeFhF'
        b'7YJ1yytVGtIRth6QrKhTVBFjRUWjpE6l0DZKkqQySalWReeKSp26rjFeXY97TINLVVZUkKGuUC7V4YQkwdBchjbXwFpGr251GnhlNxh4ZfcY2wU8zCg2D/8Rk8f7n442'
        b'55euIEIzO9+r1lTVKuprVBINDapUEFOPBtayEadSSFZoGlapidViZRMJHJEZsXtcocKwJBN3ogY3zXRF/TJqpqBtbMAiPZ2d659oJrbNwnaSyilJFaR3dHTmZed5siAM'
        b'mCfg3iGnKUexBsMpMXqqbXgEkeIkWjVe0mzZkMeICeuQM5mPqaMto7RqXX1VWoUNvY1iVvadOxKVDQ3kJceS6sFbHzraFcph3TDqGrVapcHTyyoMvRSVxBb3MZsg32tB'
        b'6laoIxoYtA8dqImNz86JIyrkvPlkewDtzMbeolIOuhSdG5cT7wCWezqhl9DGIh05XRW3Gt2BragHXZsdnRsvoxYTN5jYQngNHZ0Tj7DkkjKLXxNRRpXzzyA9vKFFF9EB'
        b'WUEu2rvawRO4w06urBhuouVnwdNoM2pdN/3RlkF0YXxMXvwce955fCwQOcFbsBu2sbcF7IDPP6Wlb6UpQB2wk5wQ28VgejbPofGJCyLmFo2HO1BHKdqB9pYWMMCpiEFX'
        b'4cnGmez7d2/D0y6YJg9MEh9woZGBGzNX64jhQCi87KvNZrcS8uAFHsDVPuGBCYbn4tFV+vpcCa6GlrQLPAhP4bLXM+g8OhpXoub/5n1G64xH2ivv7Npx7IvZlwqRXLzu'
        b'l5cOpeYEzPuGP34KeLXthQWSveclJz/c+os58199eDLunzl/2f6qrmdG/MLLRas/fPrDix8EfL3tyNW4nU7y++tm9S963fNX159OPKx1nR/xje/fr/52cb6kVcB7xffg'
        b'qdeCMjZOuLr2NYY5ezTzWuXY+7/pvzOx6o2Dn7fc+eMLf8qqfVd39+N0vwk++TFfv/zBM881rF6e9tmtrPL/6XvTZ8V2w79271r+N/Wn9z6e8k5dQe6njR/1CBYc6CnN'
        b'G1e67tezy45rI9+9eCpkitNvJuZkzHoY+Yft1zs/8tjpHg7bUNvXD7v0n3qnvNBsWf+GrvRvv/jXv36V8WGKek7ImuLE+3998zPrnnW8L77m/vGrnAOBmVIPuhEgWJ2D'
        b'WmH7KsxWqNUR8OIZeB7eKaami1PRi/Bk7GTYFo+2o5aEbLSDC1xmch3QS/AIPYq4APfBOdiqQRcTcBIG8BIYeAVed35AXgqWmegTu9wvtyAfh4cy5LortPUBfVfXFXQE'
        b'XiRbGwXaWY7AgcdxalxLNyxc4In0vIZ6+vYj/JQPA4+ioxrWtOVwCDoz+oYKNHDQxZl11HwlHV6F+lgVTyaNYdmQD9zRZW7T9Im0aHROQwwr77jTDQu6JVK5lI3pzpka'
        b'6xFre4ZXyMCe5Qy7HbJRgw6RrY6cOBlsSSADEj8rkfB4Mej5VHjmAbnYdibc6Z4HjW6PxijckcCO0Bj0Ih89C03etE0j3eGJvFnoNvuGJzKsGOCs5KADlfDsA3ohJrqE'
        b'tuUVxTOAs4pJz8tIWk6bWhGZw95gVgR326/uhGdhCzXzFoSuzIOXkgvy8gpkqCUuD+4ookTGwJ18eNHFdsNn4jPwJGothDcK4fk4B8CbwcDbmRKp8CfXyhLHPtsN3cfx'
        b'YqfT8qEryNpAG4QYNZZu7ey1be0sFgIPn07n3c69gePMwvEW4fhe4Xird1Bnw+4GU9XxWrN3gsU74T3vlLveKWbv8Rbv8QauVejd6bLbpTcoqSfTLEy1CFN7halWbz9D'
        b'lTGsvbajFqfw8e9cs3uNydnsE2fxiRs4QpnBbgtNNftPs/hP6xVPswaGvxcYfzcwvlvZM+Hc8htl5sBsS2D2e4EFdwMLzIFFlsAig8AaFnVq4tGJRyYdn2TgkusqfQMs'
        b'vjEYX/sFGxys/oEGsl1zOH9/fre3OVBuCZSTtyfFU8cwAyN6U54lRI4xfcBY4wRTSrfj8cnmgERLQCKxxg3sbNrdZPJl7ybrVt71Ser1SbKGRhgdiCVuljG6vch+oVmq'
        b'WRxnEcf10o9VFGjiWiRJd0VJvaIkqzTJkGkRR5JjkTOtknATz1R6quxo2ZHFxxebJUk4XT/gekRSBxPiE2Ja3esjwx/yfqZoYxEt8CurT9CQQ47OmjrwY/aM2KvNhh9g'
        b'nIx7/LsZg8uxv5SWcEam8HtfvvRY5yczEC4FFPwTKW+Ikf+A2QK1teXbjPx59B0cjhh/2l8ZQHQpw654/M8Y+t//9Wi4M5MFTrbrQFhBicBrjGMIFhqQRGzwk2BRrU2K'
        b'HwlzbHYiw/DrMLQ6OjodCZpKRiJhBUFbQ8ChHas1EBBJjGSaCMwdSZmiqpY1nF2uWt6gaaI2PdU6DYv3tIqaH6BUeaQkGSqzDTrZ1qjQ1KgaB1J+p1VM/YBZDMv4dqsY'
        b'O0AnsFqlHayq/FFWv9RKpdPTlb2CnGmIY0Rr2OsgYqLp62qji12aAnflLmYDU2OfB2swv5iiP93gu8THgUI1dCwD3tS6unKAHF5n0E6AzofArbo8slZvQs2FeYOWwito'
        b'WynBZXYzHDuIKyGGuPMxlCRGNY+sevHKtTZYmIY60X614E9/ZrSf4ExnvNyxdc5k51O3oFx4e/HT50Nu6CU7v+E6rn5my+azmRk9i4TNu2X1H8oudL3woGit68kdR8MN'
        b'hqd/+/Rnn96Y9XdepPNLhWHX/3psUuLKDfOmyC49PU5zx/EV8x/Hrajec+Op8y4fHZPP3eWrkr4T+/5Z992HXrvi/OU7v/fTvfO0OO/DM9fTLx+7sb1k4t+/XTr26z/9'
        b'onxFfdTKO5+IT045k3iwqn1ffdla0VGHC7kJCWczLn1l3BBxe4LntcmauQ6uWyZyb+5Pm//J7V/nv6P45s/TntFJi48V/sJ06N+fpP+l41cz/340aBXXIzVxzptRd5o/'
        b'/5i/+ffTzEtOSt3Y104cg3dWPnr/0oJYTjw6Zb+9oN23Is8BHhgEh93nceuqUBc1QYmoh8/njQZF4B54nYUjzwWxdiwt3MW212lMi+bAo0wphn+bKeKS5qFDeSMhhRc6'
        b'TVFFMU7GWsIshUdZAxDeWg596cZGtJO97OIyPDgtlr2QXIu6yPtunOFlDjoLj3nTKgbC447sazc4gIfOrCVv3ZBhREWruMUfHR/AY/jpbQSToRfQYYrKpHBnhB2UdfGG'
        b'4DL0vAxde0BMwNEuaIA9VIbKwRVgW2QNOmtrFA4mcDtTnuAEjzc5s3drHEbbs2KpfTMfOCyFpoWcYFzoAdu7O4O8Btk+o81L7RY36AImmpzI81gJj8Y+A4/FFWChCbXA'
        b'c1iKcYd7uBq4CW6RCn4YjBKAQZeo2s7W2UTbtW62hdH2m2KkQhtGqvMAgeGHp+yfYg6ItQTEkhf+BBgbD65njVSsASGGPKtvoMU3FkMS7+DOut117fUd9QQFBfYDnkci'
        b'G9lddbH2TO3ppeeW3vVN7fVNtQaGHM7bn9dVcLCgOwMjoN7A+J6wq9E35lyO74kngCZnf05X3sG87nBLzCRz4KQbVXcDM3oDM6xi3/fEsrti2aObV30DWXWjT8dkU9Zd'
        b'kbRXJKWH/Lqzen0S8YfaMC/oXVRuWVRrltaag9WWYHWvr5qgj6zu8HPxlvBUc2CqIYtUTHeXvtaOgBRdr08c/tgfrzJLq8zBSkuwstdXyT4bfbzIHJiMH/QNOuy2383U'
        b'eHxtz2Szb4bFNwMThPHMKqPKtMDsI7NguCOUDX6PCavEpfrbJ7iBm32HyZAruIsIoBnWb3EEwmwE9gNNpR4/wED6J7WS1vwOPO5yznVguG5x3aCj1qtwSyiZwZs3OHZg'
        b'82XYpooDUZQqOT8ktaBWyi18yIlQP+RFyJKqpTzaBX0u5fUN5TZdn7aPq6jUUr3lSB1ln7B8wPyV3WFb62NXrQ+LIJvRWnJ+cCO4R3lzhiV8XK+IfPCgORFmUh5feiTh'
        b'eAJG4/8fdW8CENWR7Q/f2xv7ouxrN5vQLA2CoCKK7Dsoi7sC0oAoAnbT7hpNNOKOiqZVjK3BiDuuUaOJqZolk2Qy3UzPSHiTGZJZklneDHnjm39eZvvq1O1uupvGhZd5'
        b'732Cxb236tY9dWo7VXXO+Wk9Jw8FhJzL6hVcdjxTRhpVQJLWk4OTszg9M2ExDTJgWP0aw51O7eZbHiIrlmxmLdhruuZO0RQ55ixXBGxmNebSpc03rU/JWsLazbzXydnN'
        b'vJOsnGf+xkl6kmZxLzhlZ30GR1KYzrq2kDuqiS4s3ehtkg5XNykJW+tWULlqIz9VErnRLpJuOEZ+w0ZKhVwNejStbmtuqmtqr+b6grKptYX2kUGHyg1t3JEKV6ecte+g'
        b'kAqhg/bcYSuJtDTykJiMfgddq9sU9UQ+q6+mr2z0Mla4xeMqqO5dDB0zOT28es08nUes3iN2mLGbEEWGw66tvZ6Xg/p9UrQ+KaQJ6AOSyADpt5AdCJeeLzlb0hd+K04X'
        b'PlsfPludo875dWiMRjoQP7V3fe/6u54Pgu6Sn/eFH7m+T36G+WzcAvYrhg1byD6hIem9QQvZocCQ7iIyHPkEdjqPPhcxbQ7OgtZDVgxy2Jdmx65lQ42a3/NPCWkNCUo3'
        b'2nNsiIrcKIiMJZXCi5QqwCGylMeNbSZLbsmIByLCMAX12G08jeIe1ADvwhmDPtVAfGKvsm/KrdQLL11+qZf8PBJ8x+UR+dH6lGrdS0cXzGTQCw51oVhjjS4NPMMoAABG'
        b'39jBCCCJUHJUj+7qdtXgsZaQ62oil97DUkwJgzYh1Ueiye4p7BPcctGGzdL5zNK6z+Los2mTnctwY5+GsfVvMytnLTvyFtac+s3sKvqXVgChn027wFPAOTrXrg1sX8Qa'
        b'2W4ohqi6uhncPrmYSgG3DSTJn8O5QvgGPvaN6SdzdE5fks53qt53KsxeAV0byXTqI9W6S/+VRWINRQL4gG94aTMV8mcVpt6yMOR2pe3CTNH5TtP7TjMWpqqfIrY8pTDw'
        b'TcOwSoau3TyrYVVi0a7MhrZVNE2rm2XRRq65+ArLWY81PqUnZVwjFIwU28ooe2Q4IiyoX2PBArht4Y1YX48afngTstiBoJDuRb3Jl2f0B6XAaJHJDoRE9AT1RdyS9YfM'
        b'JiOKVxY79HQ+mc4HjQeWxjI4mxzoUOHmKZXXYll5cAvSJlXxJYQHiDXJJ2ZqfaK07lH/ykYnMHCeNjp21jPbXKNlB4LbdSSJooE16NH+i+gUGuhspJ1j1rM7R6Mlf+F2'
        b'ExC60kTomAMnzAhPnw9GTqVdnzHOw9mXxTjPPXgJqhq2x6GR+gTYcjJum5ErDPSNn5WASkP3w/ibYU4zpbN8yzg1sDEX+CNDK5UwLPqmK2vZN41FJ1NGrVxuMWXQe3Bj'
        b'/edphoLbHG5hEaOp0tGNXcPCobJnqc4nSe8DWrGjeWOqOzhcexpnRtUh50dAselpTQnmaq4kZnM1fbALigIHMrQKX9t8eLMmh9s/fvrY+i1UoeNzViHtLWycYuMLVJtS'
        b'tdxypof7PdB1Ntvs4yb2JxjY7/T8FUDH+63PYj9HkRn76YODZsKHX5BaCK4RNSqdT5zeJ07rHveUCljOPHXNYNdu9lIFY8V64XOynlqR8gddS1vbC4hAXg/ekerlZr1I'
        b'aKs6bIrdpFJWq5otKoXeHwYOgB2brZmOnRD9aYBU6yn9n+xQKziVoo5n1ShXHLMapQ/U0Mi2PX0i6Xp63Un+G53KyUZtOz13bUNHi+c62vPXrBOZ9BWqennTWsKOiSZ2'
        b'mJ6dhCFm4Rg1LJwwbSBQ8jgwvj8wvk/Yp9QFztAHziCLngBxd2qvUBcQp/WMGwqUdBf2eukCZRARok7RRMDSi4Os1npO/d9hNc8Gq3kvMi3x4l+Y185E1G9ubVVwzPYw'
        b'MXvk4RvQn56T2+26wDR9YJqR2166AJnWU8ZxO0IXGP9/idsiG9wWvdAMEvGizLajCCKWQxbcQ96KAza7uGlR/uUIJ4SEEwIrTsS8CCfazTaNzMu5mbUu6fOmXELbKXXe'
        b'I6C8G9lls0hH4/ljxzfwDMPGoIg0PsIcMj9TOeuYpbAlGuH5oHDditbmevAHsLq2qUVeb75VY1B2NdWAY3U1ly+phAmmSjA+umnaH7XR1EUTZpk39fW6wNn6wNmdOZ8G'
        b'hGjCe6J763UBU/QB4Pv415FxvfLLK+9G6CJn6yNnAzhjjnr6QGCoOleTDBvKusBp+sBp3IPpJOlqrtuQRVbgLPCrMesp4EVgX21LFHeyaMujWuwK0xpyLLGc4qU1WjRO'
        b'ev8ARtsAA1PoTNnevVG9qnfK5Zk6n+l6n+la9+njoNfx6fTueB5621qVFvTS+3ehM3XbXM+YOlOxGVHtZiksSLKYxp86HKzgVFkrLdvoUwivXW5JOL1H0PrEZow+VQcN'
        b'63hrd2tv++UtOp+Zep+ZWveZ38Y6jTaHtc+gsqml3YJKev9doNLDSCV119adeuilrpe07pO+Dcoan0mZA52dajlX5WbzFTx532IFGdipApfKnGtw45aBwpsda4y9yBiM'
        b'TsiYye2lKdzMm4ecZ8tERM6XCzgReOOoAm2x2CAdYxudt1tkNULznzVOUkYJS38L19+EUt3kppZGSVvrOk67eXICZyihamtrBWSSb3gJskF2MhlNA4yNdNB+jaq2pb1p'
        b'Yz3XXDkXeoN2JKfGpnblIL9+fZvVfDbiRo8bU0cqhFJgUSGGJx9ChSwzVIiHv3ru4RmdM6htQIHOv1DvX6j1LBzwDupsVMs1db15Z1brgqfovJP13smdfCqjG9bCWX1B'
        b'Ot90vW/6U8T1C1TMhuqVxluZISv+aiBU2dzaDnBbYKI76Gqp4UPuGxrq69qb1tZXg2oHEY6aa5Xt1Zyix6CgWqVoVlQARxZAoIF8qUGzqc8P2psOiZyoZgWnKUy1i+hp'
        b'g6IKAjqjLYOgFgJwFK1ogqAZAnAJrKAOd6HtKdZBAItxxUsQvALBTghgPaEAr30K8HykOARBFwTgX0ZxEoLXKZ0QnIWgB4IrwJ9/Nc72KCtpw6kky8JJG9dItLAGihRY'
        b'WkmLBGAlDYEj45fQUTAkDtc6Bw4EiTtKB4JCSBAg7ige8JjbkT0QkEOuQiO1zuIhF8+O+eocTZimURsgu+uhdZmpc5mpd5k5zPNwSRxmnhaAAeosU9JoxiuoM3/AHUYL'
        b'zjbXi9rmelHbXBJ25JiskWO07jEDnpPBGjkJjJGTwBY5iZoicwnStO5pwzzWew47LOT7lpN8IHxCQ5LMkXH1GXDxHeZFuAQPMy8aAN1++xbDH599C4cF8LyUpVkCM+q0'
        b'LqE6l1C9SygY1saDre0zAsgpjKQ35QgRs0mO3sM8gcsUqJQpJiQ3eODs4BIEFs62A2/WpQyOnWyHItYFXJQZAxHPJRps4w2BPQ9sp02BvQCuxgqcWRcp5GIInpEVC5hz'
        b'NgIRH4poI3Bk4V1T8LR04BPNGIiMLLMZOFtlKnKZRgTMMQL3/06snQuRKMcKJrIuqUDBqED0lAiQUEcHJCISrkYFIsvqMasoIXDjBYIRu2/wtHhTCf6oqd03ejuBsffl'
        b'qXLwVdvI3v/ggRqkpd03dTrK7xA0COS8HfYGdD/+DkYuuCy0ie4nInF2o+LszJD/rOPszZD/rOMczJD/rOMczZD/rOOczJD/rOOczZD/rONczJD/rONcaZw3ifMZFcdh'
        b'+vmSOL9Rce40zp/EBYyK43D7Aklc0Kg4DrcvmMSJR8V50DgJiQsZFcch8YWSuLBRcV5mKH3Wcd40bhKJixwV50PjokicdFScL42LJnExo+L8aFwsiYsbFedP42QkLn5U'
        b'XACNSyBxk0fFBdK4RBKXNCouiMZNIXHJo+I4e/kUai8/Fezl5dNIGCKfDrby8lS6mpox6AaO5SpHfPV+1sda6eQaHdKaJTIAF1olA3MpartVV9sCYubyeoOBcHsT1Yg1'
        b'WlhRGDuj6TAYWXGqp/WWSrIG1VxLoyo4SzBzLFwDQm0t5xtP3lqngn1jU84WubUqjBk2tXOaG9yrRk3XrIySymxDDjVj2DVb3BQ0GCzEaiXLqZ4JyY5TUDZ3fBzLfdJY'
        b'VoNdfruiHhhikV+tkroBAOKo3dZaklNtc7NEBVsXzRtAjLfwqGzxssXiCjY3YL34581klXBUAOsWhSOsXUbMzHfbq9hnrWHazVYlYyn6WK1q+HJmM796BEsT7gQWd0KL'
        b'O5HFnZ3Fnb3FnYPFndFzBzNaUZ3EOlmkdba4c7G4czXd8cmdm0Wcu8XdBIu7iRZ3HhZ3nhZ3XhZ33hZ3PhZ3vhZ3fhZ3/hZ3ARZ3gRZ3QRZ3wRZ3YtMdWUNWS0x3LLkL'
        b'sUgZarzbzNOEMTb+WfI8m1naTnf6BFuEmwWacFtvyIWWbUUpkpO09HhV0BIy5lsiy7cUzuQtZmWE8f4ku1lwkj3F3yJoLxl5i6yQrfZBlRPby8xytSNftuHYoX2uZR6b'
        b'hZbYsCyzT0VanMNm/kpTy9lthf2q5BWCehqH/2pfqoBvfJPMDYujBtGnD5NUKyJ3kK0e5FVXfxNh/faKWjByHbGTpd4DpNJB53KyiGpabXAHIOJU9zksan51k3xQWK2q'
        b'b1cACBDnlWrQrXp5bcuqapNfUMUbwGnY9FBcg0AJAYWw+Zihem0W7nUH7ao5Gw2SY5tK0daqrCefoCtjO6rR2F47KKperWykn14FrlqF1fXcH+q41cX4WjXYK5CX6laA'
        b'fQHFeq9tVynJ8lxRD6p5tc2AodXS0Eoopgxtamiqow5PyIqcm0JM0bWr20cKNOhZ3dxaV9ts6QGf0EtW+YpGssAXVdMhnGRD/1ZzfAmstmJ5dTUMz4a0QnK9WjnoSIhU'
        b'tCvBjQvdWxi0I/UCdTLommGsGa4m7JT17RAhdeQslGBoGBStWkdIUJrBFNjYWuHWzzDocaP9yLoZanWjjxWZdId2XXX1L2GP5XesUW0CTjlrWHW7JqN7nVY2SyuGX2pZ'
        b'tkznX633r9Z6Vn/qE/Ta1sNbNXXc0XynAPS0BV32JuQ6DpwuMgbgFsKNTw3IdZZpwCHgGYceBwuoO+NfcRh57DwgCaWxhhcNDylknpPxoeWfCCm8H2pMavhDwe5cjWmM'
        b'xIVHwd8Q031sAvyVGugbCg6jnwmP4FIZU4dJz6edTTszqwfWQhPiaXCoqDNbHUFYcTr9RHpvki4gXh8QD5CCswbEoZrK4xsBPnDAL+i0+IS411PnJ9P7UT/Y3Kb9QHTc'
        b'5dje2LuCuwKteKZa8GlAqGYKSWZyl72U/TQ4VhtXqZ2/WBe3WBe8RB+8ROu75FPPAHW2JrxXqPOU6T3hwIz8DviEdG7UhPfE9ol0PlP1PlO17vTXZyooxji9qFcLznuz'
        b'ArNje4vwtW5dRg8L3nwLYAgTQFVaJTXKalk14mk4loOGaG81eHgGI305EbSaGjYQ8clMrHlhdxd0W/gsMw7y/fiMOTzcJEtcPTByWt3aPuJ5muJDvzCeluLCeEgLBNJG'
        b'3GNbwumNpgwwq18Ysu7qeAgT2+CZOaSeFWUGCOkXbI9PRdMbk7RQIG3EP6XUBpret0Pdg/FQF2FJ3b9lSDh8cqVqucENGHUgBCQZzB4NkGlPJZ2uzLiMqOkALKTayGuw'
        b'CKJYSTZA2GSSipFnDU318EHDqoTkThKMGEWaJAulJNrAyuhYctnUTv8asfOiqVJ9NAdJF/3CPeSH4+FnLPDzRyZ+ThmNRTNGX8nInJ8RT4KcF+4xhMbvjGeYjLckNc3C'
        b'GT9gudQvt3TLb01yVnlOdnx2TmblC5Fs8Ff03fGQnMg3dwi0xDiwl9PmZiaBGmxzje6LrIxGZZJsik/Dmcg2r6vdoDR4lpe01DfWwnHKOAr0vfEUKMWy+0Ubu5/RNtas'
        b'TAZZVBJVMW/+ovFw/PvjIXC65cAaSafQ1tZVsOrnvOwrJLVtba3gJZAsEFScX/4Xx2lQvD8e6tKAuv8wHp1/41Zp8p32olQYePSD8VCRDlSIWYsRfjUZsGob6816T9uK'
        b'DUowxJbMySgoJQNc8wvRZ8DA/GA89GXaqMMRuppbGy3JkkQVlefkvrBEQcj6cDzU5VhSx5myt8jj2lvjyJ8RUU0SlfOiZHH4xoqPxkNWviVZQTaBKiRRJeNk1Q/HQ1OR'
        b'pWBrQrkN4cz/yRKwBVx7GQYKDqxkTlX5nPFMKR+Ph8BSy/44kU4pdNFscGT2ogMDqT3deAiZa1l70dYTBKzGwbgRrqMyy8qKCkrzKnMWvNhMZuBU/3gIrAQCPzNx6k/W'
        b'BFpuI8gkuWSczasnJLfQFYzStMXLzRcG/wdQKOjXURXzC3Irs8qyc2IlefOyYiVzygtKMkrLKjNiJVDMopyF0lhqf5gL7XiFIc+xcssuKyGDA5ddbkZJQfFC7rqiKtP8'
        b'trI8o7QiI6uyoIymJV+g287rmpTgbqKtuRZw3ziElRfvMD8eD5cXWXYYmbHDhJrNs9z+DNdbaumAU6skWbw4hT8aD4VLLXtMinU74HaaZJKMEY+MBaW5ZaRGs0vzYPKF'
        b'xjuORqsdD7E1QGyYiVifSioUcjtgpNHIobW2vlAfN0xrj8dDTZ3VtGuA5KH+Tjla6kfOQMyX8i8uFujHQ1+DZRcP4rhlnDnAb4wEznZsiAIm/S6gjrMxGaFK2Wph7Oxq'
        b'oeVqYRvaJjKPo04beZtZcx0tcm06BbHcUd7MVDNmqUynI4oJ5nfmdFXbfKoxnaSY/yMpTGcqlnvdrI0W8s2Mcs4DDJxDmWR5bhUyciJme5Uik9orENTB34B4AHIww3Cg'
        b'W8eA1aD4BwmkfG6zkyaiG5vADZNNjVNjfbtxZ3pjgHWlm0U2kdeUcH7w9TYGDBC3gNZ5Pgsa5tO0ATN7PS/79WXfytdGzdQGFD7y/I5fZ/ZAeIwmrze7L/yW9G7lgyW6'
        b'8EJ9eKEJ3Bm24tIHJiffClILul30vrIBT9+ukseeSf2eSX3Z+im5Os88vWee1jPPAgvadjOnrm0YOWtQW67kLBxHt23Q4hrdto2Gb8CaP8ObBru3pyhSLmCs+5XCcyzd'
        b'b8vTG0tt7kbbqpdSnuIT8mxQADvgNoye7Q1749W2CsPFrIUKi+YK4+Gj9wiHDel4Ul+PA2L7A2K5/VCtp+xTnwB15qH1Xes73Z7CYKO1jVl5nc3vVpqVgFYDWELQ0xhj'
        b'UYS0Gdk24G6ubyFFsbGxTiM2QUmCrUqSRE3zY/UBiVrPxAEf3841lPpSaZgtnUO6c0+1BAddrU5faMeg/WikC/2dMfSeQRfLwxeR4ezFziCOKsCWd1BkOHcRcscuAnrq'
        b'IoBDFwqtM+hsceIiMhy4COjhiavV0YqT+cmKyHAkYz9yIsOdhrhanrgoAnmGxq0IgatwHjWIGFM30BIfU/EW9AprxYSfwHHGH6zQU0QOoBcIgbfMJXCYeXYgZ5ngSWoT'
        b'Ikj5sJAXXAm6fCR8QsOOUisUkzRAH5kF4COzAHtk1ovjoNjMwRzSIh0gLTIo6EgGBR3J4EBQRtIM8wRe8cNCkU/CVwwJnkBAkriaAYcMeBYCakgxRQ0ppqghxYAaIrJI'
        b'AyUOoiUOoiUmIU3D4aSA3f4wj/WaPizke6d+xZDgCQQducP2FhTPBoozKcWZlOJMc9gWrtgzodjpUOx0KHY6LfbIdwY8IwCPJRLgWCIBjSWSgrGYq1oCX7woX7woX0hI'
        b'VS2f+RXzBCmQYBokmAYJpo1KkAQJkiFBMiRIpgkCw9Um/BlAHAkExJFAQBwJnN5RbFWQKChINBQkGgoSTQti/glglydllydlFwnpV0ba4jCP7zWXHRYKg0ElFMInNCTN'
        b'0ZkJCFOT1gbegAY8p5GsAkjVkOAJBB1FVsQUAzGlFOWmlKLclHIoN+b6qXGgnxoP+qnxoJ8aT/VTn4fz5p0H+BYMfAsGvgUnE1LHxMnxZKEHmgIRH8BpTIEj38UPrqwD'
        b'TrkPzvtXooetTmtd2pylhfPRu3hfTGmxDPxy4YN8JnqFEPXhXeiShZ6fcVb78zGG04MZ0fPbwSzi85h60PGzmu8WCelz/qjnIvpcMOq5nVxIcrPv4DWwctEO+0UOcjty'
        b'7wioIA08uT154kTjHMiVcwefXDmSKxe5E52TnAc9rIa54iZluwVwKc845c3mpjzWQmjkkTsTMWAaUG0SRRtBvDRTxjHuAgro/tagQ7VcZVBodwB7s9rmpvYNg6HWh95A'
        b'T7W5zpXSaBsdw6Oa7cZM7I15GK2kJWZAAoE2cjWhCuyA+TSCm08Nh7ghUnqka/gziR7Ohmnp73g89yv+/pSlhU3ajMuLPbC8WM8wNsyGnmsFOJ03zg/vhQ9vGv+HU8f7'
        b'4X1jf9gkbcbSDz+fidSIBCkBUWCGbbpATBizlVD58QDfYGG0jQERMVsfGK/zSdD7wKz2bfmoIIRR+sawMaJyzKhViYFKKhoe4hvs7EfMoIhUq/OJ1/vATPJtrRjGYBS3'
        b'auiCCgzmGSvQ3BOYyfzOzGzUhgGt0lI1kLXhfWtkzDGreAPaTgCJN18s863inagpqMDyqcKt3aS4Z0sdkbxhWuRqzHyIjfyzNrFnuTGvEVy3xZnv9qwGmIblI7gbkVbc'
        b'jLRMLm+t5+AEOH9iFLHJ6FeWSr9k8buQNQyIVABXpMHVTAioXRW0KSKqt7XVt8iNjsSczD7BJR3TPphfK5ePWozQKicRr/HNjFOpdkhM70s6n3S9DxhRTKhiP/UP04ZX'
        b'6Pwr9f6VWs/KAY9gvUeYpr1nQ79HgtYjYSBgkj4gBiwJ+wPStAFpAwEQSW6maAOmUIusSp1/ld6/SutZNeDuSYbhx+7R/e7RvTN07lP17kYFFPepT+mDoKM40gdtWx2a'
        b'uwAa1e/CoN/52eIAXcQBzhJFYRzpdYc2dG3QukueYoGaYEYUSASbmWyrlbGNIYJXaruEgHvwGp1xl7qCPzpbC9FDvH1u0LuNRY2ESje4xAEODbLt5r4fFLDC3Bhnq9Dt'
        b're21zWTABqU25SxyATJD6+q2WT3ACMhrG6MNmM799q5RZ3Tnd5eaHpj5kxzLllJIv2Cb4zTqDfhQqBnHuaz7skmgC5iuJ6FPqt4nVeuealgGu1ovgzWMYQXM9ZuRLmNa'
        b'MXILyAKeoQEowDUiET5sLSChVkfWj1OhudgSrLYD2b9hRtmWScH+xhA4U7ldG5hEfnUeU/QeUzqyB8jKZ71WMoP86nzS9D5pHfk2Hg0LWJfJIN4aAhHrkgBXowKRlSxs'
        b'B3Y5YwUTWZcQSDcqILnMgKuxA056hj0XfJNvZ5CezUVnfBPvjpWxTDa+YueMzhbjoxssRGijwvKfQ8FUxt9chCY/PPrD7xYu4gPmmVwkt5Pbyx3kjnInuTO5cpG7yt3k'
        b'7t0uiwQdvA4hEYcnENFXSERjYceEjokdfg1glmJPRWs7ucco0dqePueMU7xtGMrYAZSg3HdUnCON8yNx/qPinGhcAIkLHBXnTOOCSFzwqDgXGicmcZJRca40LoTEhY6K'
        b'cyNltTeAErrTdLImMuTUu1sONT3sAXaRO0k7kaQNJ2knEH6xFLhwIr0C2EIPB0YebwB5FHaIACmow4mCPbp2uHW4U556dHh2eHV4d/h0+DZ4yaN2OIB5TJddl/dlqRXq'
        b'XAJ8jdQBXx4zCqLSi75jfzl29DsU+NA6vbc8mg6PkwedodcZDSkG2TmDbJlUOMjLyxzkFeQM8nIqyN/KQV5W/iA/u6hokJ+XOWeQX1BBrvLLSZCVnzvILy0jV3OKSwf5'
        b'5WUkqMiBiEVFCntYtvDzCuZIXQZ52UWKCphWeQUky/zyQV5xwSCvtGyQN6d4kFdO/lbkKObTBFmLSIIqQkPBqImAmklsY0AWAm/4u4hERL3hM2TJJqC+8Pk2fOELHGx4'
        b'tydPBKP83fO3Cgy+8G3GmXzhg+OQUWtXOrGYeUwXlKryyF1reT305Ha8u0yG95fg/TFz80tJZwb/2XNxB+nesgLq97k4tqBkbj7p4IUlMrxjEt6NLgiYWfhlN3QrFr3b'
        b'VPeTm5yj2UnfU578IPHUmSMXjpzpOtPx7o5DrGu572vshkufhZbsiyi2/0SY3yz4Up75E4+PHu2Z/AmPSb7s8N7FU1I+dUhtjy/UOKELsflGNBT8Gt47Ad/noytKvJNz'
        b'wX0V30IavLcM7yG0AG7ISd5MdGg9PogeUBz5SHQcXUF70UF8sCgOd/qig+igHePkzSOL+ivo7HMN+lQX2tO8+RkVoaE3KhMZAyx7EOPpo47Vekwiv1Q2KtP5z9H7z9F6'
        b'zrFSfzZ6JuPmSrsRtW3FL2BisuGAmRrBGyDHn0XVHZiL1jEc2DghrCmIZcXgTvkZwbeGIQ4rDrWDjLnqmsavM5nbMOCX0dD4TjBGnIhdvF38XYJdwl2iXXakjziSPgJj'
        b'kB0Zi2D8EVG4WNcGZ9pnyLi928mqzzjQPmM/qs84jOoX9lsdDH3GZpw5bpllnzEBq5n1GXGpKoXcuaPL6GARPlZmBAUmHSUuTjY3v7AKd5RVREHzrZqzDu3IR718Bh9o'
        b'c8KdihWq6cCMRXh7kek10p3K4uYZsAIK8X4yjR4smh+Fd8+3J31SwKB70SvRNScXfH4CBS1YHWAH7HTXLq111hUGMypoPuXeeJfSxQVvx2oew4EWhMynyesaHBjSjhI6'
        b'c1udq/wruLk7QCABnB4j/JUVcAE+ybNjFlbYbchEhyj+VH3+jKKCkqJYvF+Kj0xkGadSHn5zs7NKQuIq0R1hTH40PgMgB/hIUkIC2lFTxISi23z0Dj5TrQKhuGIlOhdT'
        b'Cl7795dUmWEjRMnionBHfHRBCYuPJTCtUnsiPuzHV2mZ8N7Z0UV4b0FxvGgTvsOIfHiuWwJpx1GBZRO6jnvRoRjgc5wIX1nNiNB9XkqalFKcju8si+GqIAi/bsfYr+E5'
        b'puMDKkBwx2fQWdRbkSoYRcTcKHwwFu+eE2Ui1Y5B3eiI43x0oFoFWyPFqHdeBXpI+MNEMVHoDu6gpG5F1+Yq1+Ib0ngBw6Lj4J//Vp0qA6jsJHXSTZi9P1aGDwA0kt38'
        b'NpKyMoqUc29sbElVPj5QZgSQGAGYxj18Z3ywDl9Ugf3VBnwisYiLkuJrk/Ce4jgR45HHx6fw3XZqqLwF38c9Jhbje44M41TEQ8eCK1Wws7LZD79aQWHT9qILlWYlpt/F'
        b'D/A2hilzt2tDN9ArHArGMXwSncFH5qYh0MbZyJSge+iyCkbWIrwnllTT9XVryRC8Gx2cvg7faBcxLgE8dHwiPqsCPzzoIBuhxG9EkhjStGPnRRXGkdZDpg3ugyMMJuVA'
        b'R/BdRyZ7miqJvDgZX8ZvxwBvCLf2xuODFVFRZBLoiC81MApaj10m2sOgbeiCA5OFt6lCoKe6oetO+A6+pcRvrUH71ymc15C7DsI8nyQ+2hGzjGKtkQq7WIr3kmZfEicr'
        b'kRF+C5mJ6CgfXUWd6HXaXx7kCaDbS4YUm4pjJrYzHHzbWxvQEeWaTXiXEMAXGLQHHUK9Tct/Vc5Xgj7sHfe/H62414Jmu3/6n9t9En5jr06an3cyMeedUPHsm+WenWff'
        b'l+x5f8rccuctXbyQe2c/i0xy3/DTVSmHFv7gp2l/+ujB/1v70+p/TL3pW/lI2Ng4+c73v1j3w987fbyi4J2sW+fj/xT4s/Cb137qenpmyB8+b7i/IHLpdzY7375wamtB'
        b'YEVZ23l9TmLTS4u2/CTp/KY4bZnXjo/DP/3kUN3PRYe6HL9sabpfJPl53++yH6a/xISc+uTQzItnPA6uTDv31dGi68s/+fTPW74X+8WP47U/eux1bf1Hyo8/GDrZ/d2f'
        b'/WzuPHnV4+s3JPk7pPPTdSom46Nz1wLjNniuXLTSvfmu86Pvr9vy+9f/vev1teUpK1d+eXxuxxcLCub+UZTiNGP1rz/++MC/f/mPXzh88uWKy9eXBj68VR954cS05Yu/'
        b'GBi+cuRxJB5YdKP34EezNvQ3DiT/yP3BCvufL9ckzj297BP+jyqlf837eEZv5PaCt2Z90jRz/56f8XtL/Jv+9nmBy/cD51aETP+y8feLPO06ZPafnU5oOnI+qyEvK6Te'
        b'+z9e8VrqVSad9W+NB5f7TFi4PTH0hGOXu0vBn9x1HX9Jy35tR3bGzy9N2TpL83vPmUHa/f09Lf8h/udP8t/1WbClaNMfDh1N38r8sbX799/1l4ZysGgP8Q10wiB+lKET'
        b'nATCSR/odXyYA/E4l4wOk/6LDsSXxuWHrgUAkGs8fK6ijgowqegd9K5TURR604SqYYLUeDmfyidT8Dl0Ae1d50rGsZ0ujgp8W4nvtLuIGM81/Iot85/AtOOB7hUXlcXx'
        b'cS8FTcsIQ2/Qr6PONHQV7y0mCy8ytexazMfvsOgkPo44eBJ0rXk+oY1IcFLckY86VUDdVR5+IxhvownW4w60C+11W4vvtOHbKpeZ6IaIcfLhrcBn0yn2yULcN4tDaMGX'
        b'UQegtPDiYmvpuyvQzaIYGdqBXy2IjZbK6IDJML4SwbIJizl4l6PoGDpTJCvBr6F7Ioa3gU1Du/GpJ2B/moKvk4liL95DBiJC+ooqwXQWXUe3V9HiRi8qIGMLWTGGkdeW'
        b'sfH4QsqTOPK8cSZ+W7nWeY0Kv+VGet4+N3sXR9zntpZ0c3xn3RoXdL5QxJQIROjeJtxN6RcXL46Jw/uLJ7NkJN7GiBay+PLWZfQjPCYP781HV+YtIddb2Fxv1Euh5lrQ'
        b'jUBExElCnBxdzi8hNB+UFZbwGX90W7AOvb38CRjJTkvBZyHVAUDb21uMXqskMuVsHj62eCOt+Cp0VgLoLXnoNW6QoUOMd7HABV1EVykUiz2+KEZ746F9CdEJdIIR1fBC'
        b'Bfhlmn+ulMxOe+MNw+NUdFfIOJXx8FH0Wj4FwCHDzjkyhJMvkKZXBqIC+QaZwpsaRIwYnxPgm+jlZZQSdARdmGxICG00GXULGFcii5CFOX6LA4W5ge6Gkq8Bp9gI3MWI'
        b'Cng+DmgXbZ92yx3h7RJ8SRwnKy0uQ/vxwWKW8cfdgjXleA9thyX4XXyVsMM4bW0JYxnXCn7JIhkFjZHgh/EkVhZHJJwitB1d5ZN2uIeHz5MSXKFtZUPrOpKgMLaAMHTn'
        b'fMKbabzl+FTDk0ig7jjalmWKvYcfoI4y7jMFcTwmOkqItyMNyQesfNE51IcukcSlsWh3vGHCQC+jk0LClbeEQjLBXaSdG93Du/ARSlR0ocjOADE0kZBGKv4tkgjkszLU'
        b'gw5A9yBLolWoY2RVBLNdvOV2RwyZv/aHOaLT6Di+8SSevB2D75J03NtWr6ILuKNYim62iZhixo7MtafxO7SyYjIWk3qowq8TRqLdpJj5JfiAiPFm+PjddOm/EMlwtN8k'
        b'Dcz2XlarC+5QjS56Sjh1ieH2IMY3tHOjJrJ3KucbC7aGC7it4REc7iGfYPALzPlFgxT5LN0AztX55+n9QfNpyAfWIBNKWAr5Hf9YnNQvTurLu1X8aOKjkEcT9VOyH9Xr'
        b'xMV6cfH40cCHfILA9Xwh+UZkb3K/OEEbXNonv7X6UYE+pVQbXKctr+vMA7f0Sx8HyfqDZL3rLm++m3l37t1MfXz6Ix9dUIE+qKAzd8gvqDvosV90v190b4rOL1Hvl9gp'
        b'GoC82QlFXLlmP0rRmfsbE0ec3nhiY29kX6JOnKIXp3Q6D/kEvLbx8MZDm7s2dwoGPHzUazWN3S9pPWTkl2ShjtZWzDf8Lqw2/EbU6Pxr9f61Ws/aIQ+/xx7h/R7hmiqd'
        b'R4zeA/z6TChmCcOKuCtKRqHOv0jvX6T1LBoKDD1deKJQs0kXmKQPTOp0GPAIBF5ksxqfnsDe5b1repfrQybf9dOGZJJfSsFARIxmnmZeb+W1hRcX9m3QxWXo4zK0cRnD'
        b'fHZSFoB9BGQD2AcJQcGNhGTSEmtiuTL0rbu1iSuKNiL70VpdRInOv1TvX6r1LB3yCAYa57CaGT9JKdaGwa+BazN0EaU6/zK9f5nWs2zII0SzROsxmfySrKNiz288u/HM'
        b'5p7N+sipjyNn9kfO1EWm6yPTO7P1nuFaz/ChyBh6OSSOoLa7oVG9AfrQZHLtZrID5mKMFrkGe+KgkNOLTiw6vqR7CU0UFtmT2jPrcdjU/rCpurDp+rDpkFoyIImkqQ15'
        b'GIx8J0VyZsfh8VyW1oDwxgPmAXEIR5S0J/Zx6PT+0Ol3w3Wh6frQdKCv082gkcbtB7gZHOMZzegFcJakqIT4KbDv5FRX226yiBcp61bUr65/buQm8EVRY/hngd/0lB7/'
        b'Nmwo3GK4DYWvDbsKyiCWpe61/kXht7UbQbGqzjnMYN52zXDgvzDgPXgLoBwe68jbkmXGs+6/WeiFv6hSwamnHLHb/t4/LPXQo0BZ2eS3hiuAxIBCJIlS1NfK41pbmjdI'
        b'x2UWTZjiVG0wkKpukr8YoazAQqU/bpuB4lhbVldNypFCmFP9wrVIdYhfjFABIdTMtC+4ktpagaWVyYBy/BRJoV3VqdpbGxpejCo7gUU9x1MLHVV7HMlIAr45RqzCgFJq'
        b'LD9OMqlNsvcLN0RHIHBEqz+aavU3NRjU+FeDlQap1foW8EUk/2+y0LnabCR8MTJdgEw3oyoDZ4EFFgeNAJhqMtUcH3XUDD70hRucO5A0Yp0RaYm4akQf46zCzAkzo2vk'
        b'DHotw6lhgM+5Bh7dPIXzaCuY3S0s3TxlRm2esqM2SJmtrGHz1Gbcix04iEptn5xTqtldJBn1MAZUg9WD1YHIFp6DDTpGgwgTytitPAPVNuMsIIPBzHAU2iz8Mxim1FMf'
        b'XJbmCUqJckWrqlkOSh9keG1qaAKD+MZaMGqwmVe7weWZJKu5vhZMqSTZ1CkPNLtWBSiDcMb3MPE2kR7MWQ01KW1mpqyn+MU1NZUKVT2ZzpvM+75xlCK9zajZTVGBbebE'
        b'maZtMLf44gzUTJ/IrW1WwjfARJg84KysbJPVCr29DvzPyCWgPFDb3rS8CfT3ZJKqNnh57VTZNNl6Smv0qtaW9lYyP9WtiraZWRvJCaaEdbVKCg/cpOD8fRh9GzWTYWQ0'
        b'SDD8s2iFph5r1gr5pU2rBAcFSljDrj0TcPKDaafOHAnZy4pe9tP8+7QfM5N283556S9S9gl4qsLdLeggtyYfWZqh6/gotzwjK8rDpLu7G7u7Qd1B0NBY374x3KK/K+ua'
        b'q2mBR/QsIBVdVoH3JxCu1kqYQEl3utbT/JzIoB1pKeTRs6oao5WL4h4oKDzX9zzJi8oGxgAvXi9h2YkgeFkH3+qh0BEHKXPBdSrfNvYCIHFyx6X0sBT0XPkm2HCrY85/'
        b'AWz4c41cpM18ev1XPGUMeZT4HdXJD9JObd995siZI01+YXy8UvLqttLvrfc9EnK/bGeIenuSC3NYIuy9ftLQiNArvrDbF2+1vsc70Du0EZ1Ex6R8a4kdyDC5vhY0KJ+r'
        b'QSkNDcrP0KA2S5jIGI28N/nMqp5VndldZZ3kx6xtGfANXMc6fgQWmJ8+vvN87YyQIYZ2toYxYsBuIg3ND1rW2MG3BvoKu1tSngpKmSVYV1RUFseuljACNxadr0cH6QkR'
        b'7sO3UHdRTGkci3dOZQRJLLrpjl9uupLnLVDCScTxgzEnP5hyavuRM69I90/eeX3nG97v/66mtG7nJ4W1vBt+q3xX+laov0gQJrXdYZj33nRY/lWQsbeOdbI8on/nYOLZ'
        b'Rm/bvKSVWMxV4oDAfni5xGECWezbCLzZCYmwrrYZDEnCe+VanyTtiPNyI5W2atuCSgUAHIxFnwfU7kpDI6sjdesAVWgz+Naq9T5vLM279YYRhIwfAiJB8P4HJYjnHT0u'
        b'frxPqATV4R+vYGjDIqPHJtmZI5PJvHNscmLC5YYdX73sR2af1k8EeO8nZOAATYoF+EI1t5mITuH91huKY+xFhuBOKc+sVnl0IDHTN7bWHqCKxhbDRm4I4xtgU9eYaz5C'
        b'W1PSiKqp2YAx9gfDoQmtYgwTUU7IGBPRtzobKV5mxmpD/2sy6ArrFmRLZhGUVjZlXzgrUAK3ozOjQGj55+KQnZPJZBPEuL7Lm4euGRW8rYQRTsHbeoeH0+ymle5kqPRi'
        b'UumBBpvQ55c8npJ7pIWoUTRWDf8PDBD/a5U7SqfERJLl8FAWt1CoBMtM1V/ST34ge4uIpKA1lep3Y+iBsNh5waNEybL9Q2zVtVd/b98wVMxnQgZEp3/yb1I+PfBaTkRU'
        b'Dd4bWzAlPo7HCGaz6HY6uvEEjuLnVqTZPo2QLmJsDx9L3OhZFMnyDO4EHRFpSZyIscdv8/D5BHRoAt5jo41Ra4tRu4jUzIK2sTCujf1nObQxamrxODClPzCFQyiyxPd5'
        b'/rb3lK9GW7S9uf8jbU9BNW7MFZ8CjbV9Hxqgl03FJ1C4dKVe4o0ql6IOD6oMZVK87PDr8O+w6wjo4BPpOLAjqCO4IdCkGOXyL1eM2vE8ilFppVRXglc5owjvdcX7QXGH'
        b'au0gDbrP6e3AwWL4KnTHSYFv49tua1DvQjjEBfURd9TDw/fnyFQzSJoFqE+AbvkrQX0kn7S/MnT56Tok+NX1Tug2vozekYpU4C8Z7UBnZisxEc0Y3Fk/kUH72GKqqhOO'
        b'96JL+KaKEI5Ph0Uz6JAbPkMlxXp0KtYJ3wENj9s1Sxh0pmE1zcoV7UNXlGC+gjsKqxj0ajO+SLNKcBU6QXvE1/AJdJlBarQHX6Ax1fj1GiXg8uLD+OxShjy/R14Dpp3y'
        b'EDFfBwQRKasm1nlaAUNlUXfndFCogazewBrUxaBj+FW0k1PE6fbzMpYDb0N3SUnQ9joVyAYzS1EfZVEUfoAuWnIH97Ur8K2K/Bg4a+fUbDqR2mELVuMrKpjk0cuERadr'
        b'8a4k3JmUIGBYfJrB2zZjjQrUGskyBRTRzHXEjCAIc+fMx0fRuQVJhRV2TBVWi0hVdiMNx/XX8T50jOrxkCLsZSbjN5Uq6Khop1cGPkIko/iyNCbeCZ1q/vqf//zny40C'
        b'ZmgDYdjsmubvb3ZkVJkk6SQ3/KDI9DHckR8LynH74wurovBuQkVFlBQfnJ9fUALqVCWkcaA7Jfh8ORRR1OKyFG0TqNJJNrPnEgl/L95rnhLaEinV7vgyA5cqy81V36Ad'
        b'XUJvO+MbzckqQBISROPtLuSFQy5oW4K9EG+rwq+L8IFKl9yJ/vZp5eht9BC/jq/lNK53aPBZ44gfiNbZoz0OZc6oD7+CexLww01SMe6YIcMnRGF89FqWFN2cNQUf90Xq'
        b'1aQNVdFqwN3ztqD9QrydfIuZbM9HfVXoxiJ8VIR2413oaDTagR/ig+hAZUDTVtSLtwWghytDA9BbpB3sRHcaNuEd/MlRhIz9Ynw926OE9IJeOgzR5val3J/1jFolYNxr'
        b'gi4I+QxVgEubg6/gvSXo8hzcUUDKHo93z6E6i3BwfsSHU7ZCV/JLS0oKSlgGXcVvOdUlzqAZXl1SwGSLI1myJoz+kaicUc2BQmzD91EnFOG4AyNxJhfzlq1Ch9FlfB+f'
        b'YSeTMp6bkUQq40gN9FF8oioSv7GIkLytpNirEr1cjzoasQbftVuBHrhvqEKvUgXLIrQd3zKR6U3a4wil+XGFwoleoH6MLkjJL/SwSw74rcTySilLR5lcvKMBqp/Mc/hA'
        b'wRb3WDJYkPr1sRckoOPoFVUqbeSl+HJR3FamsKQiH1Q6YgpAiTFmHlV5NrX7A/mxhcWygrho0jz2SJ2b8M4QVTK8fpdUzbkRXTWk5o2hrmbQVSPJXyHk0VEI3ZZvROdB'
        b'YY9leOgAm5WG3lLlQ64na1fG5BPW7Svh2n98YUFcOadOatBXXBtopb/XBoPAnPK4eTwG7fVzw+fw8SxVEQzj+L7UaS2+Q0tBugEZKQ7gA7FR+SXoejnkNr+NG2L3ks5W'
        b'xKLDOXi3uyN6vRQd2OqILuKdzDT8jgveuwG9S2v/79l8Rh0LVzXNPf5KImtSVczSuvgiTsujOI1PBIU+HupAt9AD2jgk6Dq6XlEmLUH7ywpiC6rmj9aTRb2pZFzdjS+S'
        b'hrQbHcb7lkjQJXQX9eSHoHfzQ5LQNQGDb+DtE9Hx+C20etFJ3MWSMfOmm4M9vuGGL8Thm+1rVCzjqeSXJcVyK/w9m6ZNW1GBjyYV8gknLjNkengDvauCHRyXwugiaRzh'
        b'wO7iUkJTlHEh1eZgNABfKrEn7fYifkMFshC+tRK9VYH2V+L9VSX4HXSbZYTRLDqBD26hAx8+VYbPZfk5rXVlyaeOkXHERUIreoNyE95bTB5OIw14J2lyuA8dpBqbMa34'
        b'Ugq+XTSi8+m0iIevonvtlHpPBXqnptCo5MVpeKE7M+hMZZe7TOoFqlIGPamz+C43V5xylW8lYw9VcBQygmAWnV3oSb/W3ES6SFe9UYkUXRQwzu58Lzt0RQWS2RT88gTS'
        b'kkkDlgIDSmILQN+Hy2YS2iZsmFNA+YAe4O3rTaMzPufIkupW89DRDb60JeBDXvgQPj83xtALhIxzI9+tbCllkmILehCVW0QaAaFNwKLTaF8BNxddRbcJeXvj0Bl0qpTq'
        b'GYmW8rw223PKl+eb0ckIX7yXqmMJUlh0Ab+8nDKiabV8KX65KI5GkNK+MSmHMi8S72DQKfQWyZJGzWJJe+oupwrLoEgUg3pURhJJs4SeKmRC0BGhQ+NUFSjxkL5cEIt3'
        b'kJ69u6yUzGm740H32ZozpWi7He5che7RssvRPnw4RlYQSxqWOkDEOEznoXNO6ALHmKvxKTwAEwIN1Zt2DA9fYePQ/ZlNKVG/4ynBP+B7abn7590XFLX+eLb7z28Hpf/H'
        b'1imqP6/48aTSRZo5jue27fjaozt6zZIcdOjyB7vLK6/ES1xP8l9z/M/fVch+e1B+4jt//GPDhOtd+xvX/ebkfzU0rv37+S0HF/wi7wcedT3r7ScNLslacSYiacJyr/Sj'
        b'3+v60rNk7pelsR9/wMjDDrWU7PjNtnfyZ/7tUbhHrfYH4UnvHB8MXf6Pfn/pvJ7t77507XeVb3yT/9Jmt/iFEb85u37jb4YX95SvmHNqecd/bVv5Hf+4ezsm/WT3w43i'
        b'+UKZ60+qnBdUZV2efePzv634dUb2+9cvOrJ/sLv8u39r6kIb/9Cr7nzQ6+XXM9tlKPFcbnfVIs9sp/Jf3Xhtu2/qlLAmdVjWe2ezXVTBf1sS+t6mWRt2qUubJsmacebF'
        b'1xMP/tfBj4ISDgbdxGcqT332RV7uR/9Wc+ti5+Gh8zfe++5fHfMPTf8zU7/rxOffLLh19YOfvleXo5f/ovbVDYcKVibFa/PjEi9c+Hj3gjfWfPXP1EM/eLC671jzX351'
        b'99jNk8cHF/7p4fu3rw5sP9AtvnHplmrqjZ8t+FN5XcxfH5b8NeK0qCltync/nf9HxSr8jt+dBUrFcE/Sd8uvvLWwYuHvt7zbnf/Z34+d/2HZPx7si125vyzoO4Nrcuo/'
        b'PK0qP784496uST8/cnVXZtAbMZ6+U798e+vOloTbKGn21QudF4S6P4X343fU03/70QzNsT0v9f3owOf3HU+1f/3+1NWTl7eoq/9y5cPwX9QG/WbxRw+/9yv35T8rqUub'
        b'+J8NLUNXJ4gmZrr+ZlPxxVsLzz6M+Wtdyx8uLsjf8kvRleTMpR/Ma1J8vOZP0fd/KVD32MWdDvgp8/rMz6/8UfCbDJ/3/hm69GDzyldWJx06r5j5/7yqPim898kDz+nv'
        b'7Qz88D9++tu//nvXzW3fu995cktVy/uz9d1Z12T9M2Ypvv5d6Pd/v/gnk6I+uBEt/TkqSb8k2vB+9uC6rZG3P86szJkX/HlrR/ecv7oeabzM+6VyllLy7tAmh19VdLpN'
        b'/6+I9/O6/+b4K1nk6evR+65dcPgF07bR9fYql1xn5Rcf7fzKpe/LNd+0XuD/Urjq0dcHGmofyEt8f+H0C9mDXW6/+mXQP/a/Ebii5+HFf9w5e0D/2YYTYh+JR8TvZv9Q'
        b'9UXbibj2rcl/jFmj0MToI3On/Oiv5z+O9P2vi3vsCsMX/3HRib++3P1ZdXRIGr+/RBpJ1RMXh4W4lJtpaxpUNdH9iCcwHMXhPa3oYRBsDlPtWnQe36cR6D7qjWdSRgZY'
        b'9MZ6qtCIL8iFTnQ9rIIx11ytd5odXTMHE8nqjFENPxUdFTL26DZvLRG1j3Jr6pPo0lQyDPRZD/spqZxm70Pcg3sSnS3HfXwSH+GUOt8mkoQGncgxqR4bFY+JuH36Cbev'
        b'XYivEeHlXCvQKWREK3nBKvQaVficjw8SgSVaJsV7YhvQIYZxWEiGKJeIJ4ZB+AGRSGTobhLMi7FkDEYHeHH1jhzhh9F+SZFJWBYwbvPwy6H85mK0n9PWfBVdjsZdRLba'
        b'S40MDpaNiN0iRlwkwK+jc+gipyF8MakgRkbeeAUIYch3LvOSStfSuLoN+E5MHDqyDJSPOcVjvA2feZJAmZeBepVov/0aF3xDCcYH1prAIqYE33ZfK0Lv4IfoAGVZNr7m'
        b'7bQgxvLgZWIBn7BxO9pLS447sirW4FOkIUASqHSnuTx8IHvCE9iPkeCTiSvQFTJyEyHpOt4XR4VmEM4KStYYmkARumSH+tCr+CzVMl2GLoXinRuLuM+Boi5kOgHv4pMp'
        b'Yi96hSpSB+LXXRHJck98HEwsRXaMWxl+cxJ/RSk+xbU2wj70zlb8ZkxZLFnF7aVpnPA7PPzWZpbWJynDVYlB8vIpM0peXkquIdwlje0QOuVrNuHW4as0a293V3QX37ew'
        b'sTNouL8bRbPOwBfwSULeNHyEqgdT3eBqdIEqZDek4Wsk6bWnabkaVFwL26l2NT60QkG1qznV6vgMC+XqHtTJnZKdbVIaNX45bd9a0iHMFH7dRJyC+24eJi1VWhhDp2Qh'
        b'44a3zcbH+a3onohTz9/ZIG4m4tveErC4geI7tfDwyTx0grJmC7pB2vObILWPyAeyKRxPbzQq8dktFjIUuoPfor0gFh3mk1XXSWsxSoLOU/Vs/C7eFRMDS7HeMeQodHsa'
        b'bSJKIu6+SugD3Wp8eLZRvdobvyqYSBj4gG7+o2ux6NUxNu9Gtu6u4KMW23fNq+kohncuxT2T8J2i4gIyvpWz0fhYItfcD9Xgd4vIIoD0ZG98A2wnL/E2oDNKqfRfh9X6'
        b'vxAopYwR3sbwbzRWrJX286CbFRoc5xbFtLdoFUs3Nj8QcZvni0IYSXj35sfi+H5xfJ/d3Yk6cZpenAYav8Fdm4YZxwmL2QGfMM1m7jTu0+AorbT4/faPNumki3TBi/XB'
        b'i7W+i4eiirWeEQPhUT3F+vDkvuV9a/qW68Ond5YMRMT2LOkL7ZvcF6qPSO4sHfAJ73Xt90nR+qSQqPPVZ6t1ESn6iJRhPuM7dSA1X1u8VJsKvwMRiX3y/ohUbUTq3a3a'
        b'uVX96VXa9Cr69fz3Z+mkC3XBi/TBi7S+i4Y8/NR56jxN7vGy7rJ+jxitR4xBmXqtLiJH55+r98/VeuYOBEnUFRrvnkBdkEwfJHsclNwflNxXpwtK1QeldjoOeHiro7Ue'
        b'4eR3QCw1cIOvE0/Ri6f0levF0zrzOX8a0w5t6dqiWdPvE6X1iaL0zNFWLNVJl+qCl+mDl2l9lw34BHW91DtJHz1T6wO/j6K+L0My7dxKXWaVPrOKPKGvlWrnztfPrdFJ'
        b'a3TBtfrgWq1v7ZBHUGequrFX2CvXbOY8LgwzLhNiuS9PBeVrsy8P89igHPYrPk+cC27JSDjM8PxyQa85PkXnGdNZqskbCEjWBiT3tegCcvQBOaD3XMPSry/TBVfrg6u1'
        b'vtXDfHgITtEStD6kBeh8pul9pg0zAq/YAWmC2nUgNFxtp7YbksaQ65D4xyHJ/SHJupCp+pCpj0Nm9ofM1IWk60PSO10H/ENOx52IOx7fHd9pN+AfoY7RNOr8ZXp/Gbml'
        b'KvDrDqV1pWnCOBV4Wklm9UNTbNV5TNJ7TOqdaFaR5Tr/Cr1/hdazYsjDh9AFSvcjrk00iYe3dm6lZcrVBefpg/O0vuCXVL1Jval3yt1srThDJ87QizP6fTK0Phk0YZEu'
        b'uFgfXKz1LX5+3W6frlnDjNOEelbTeL71bKtu0lT9pKncE1Lw7pjOrIGAYOBayDCP7xcyEBp5Pu5sXJ/dLWdd6Ex96Ex1ljrr60/FcLztFzISDARK1NmkCvxCvv766yEf'
        b'f8iB5CgOP/3SiZd6lXcFD1zUL+nEuXpxLqSXs5+Gxmrjlmirl+vilutC6/ShddrAOshADnXoJz7tesJVG1mpnb9MP79OF1mn85XrfeVaXzl1ezfM8CdM1aRqUntX3OXr'
        b'wtL0YWn00YA4Rr25N7+35C77KPw7MVpxqU5cqheXduaTdu8l7lykse8N03nJ9F4A1ATpY9VbehcYrAPyB2jDXdFrr/OYrPeYDFkuBauF01tObDn+UvdLNBu/MLW/Jr9X'
        b'rvNL0vtRu4ulnN3FYp3/Er3/Eq3nkiGuXrtTNet6NvdVapML7y4dCAghfTu9N69v2Vd81hdwpiHsFJA6IUnTtB6R5Jfr8jr/mXr/mVrPmUPgjTQMGksuS92RxnRmd2YP'
        b'BQSrk9Tt3Rt7k8hPuz4+UxeTpY/JAvsK38fS1H5p6t1pOmm2XppNPhUI3QrCTuol0bdrpian30Oq9ZACFlj2QFCYZvnxxZ25nblDAaHd6fqAePIF30i124Bn+DDfw2/i'
        b'MGMMhsBn7bAQbkVMULg6b9gOru0Z0nIC1YHDDnDnyPhJup3UTsNOcOdsjHOBO1fyVneZumzYDe7cmbBofehUbejU4QlwP5EJDFWnDHvAtScTFKMNzO9zfWSnjc/XBs57'
        b'f/77hV8Pe0GcN+MfqvYd9oFrXyZA3B2vjh/2gzt/xj9Y7TkcANeB3HUQXAdz12K4ljChcZqA4RC4DmWkcZed9VGZ2qjM4TB4Es7REEGuO4XDseQ9vV/sY7+Efr+EPk+d'
        b'X4reL8XM6mQgKEEbRCL61j/y1QUV6oMKO3MH3L1fczzsqE7WROncY/Sce8bYRGqPoMnWuUsH3D27nB+7h/Ub7vWcl0efwE5niqn+Qbp/kT/zob9jUST/w0ksCbkTOTF3'
        b'IqeGky7qaigKglhqmlC/3qSQa+Z459l2Cd/6rA/bg1Z2DrYR4v9s8g831vweB0eInqyl+cP8EJatoKYK//8MvzXzCtAauO2Q4cS85+Sa4ceXstTrUqltFb+tJDjKN6j4'
        b'sVTJT2Twh/I/o+TXIOV99gnPhqJvRkN7vUJSV9vcTAFxwfTAABBMWkMTNIPaZgucXA59SC7n1FFrJS3160Zlyim9R9XUzFndXtDSQFri8ubWulVSmQHT2Kg6rFLWN6ia'
        b'QX93Q6tKsq62hSrdypvWNsnrR2VqQURTC03YQN0jG7zG1Ss5V3IcJJ4E0GAkTXLlaC3ZUQ9S22oVtasl4NU5VVJAFYBJT1Y2AW4w+Q4oA9dK6lTK9tbVXLamohXIa2qk'
        b'gDgxptYz4Y+RH3DZ1AJqwImEFZmEjeuAme0rattN1I4oVtvM0VA2CmZM7R4A+oFmANDGFiwyOuVrVLSq2igI2RiKxor2pjpVc62CU9BWttXXmZxVKyVR4Io0lrCAfJb6'
        b'/9/QRm7r2+tkUloJYyhoA0Pb6431Yqh3atbSQmhWEUaS/KHVbTDWvryVugRsAxhsW3laVMDoOn2mkoljKd0bR2/hWw7gVwMfxBeMR/QLORdy1JVC5cRN5p4U0CvTqDMF'
        b'gycFf3SCHi1tikdnDIeWEns+HI3eX5OAu/yD8z0i1mzB18rJOvlKFupanFnQji7hM6jPfmZbZWlsEO7GZ3B3NnpbvBFddE/AF13p0ZL/3AKmk2ESNDUbo3/HJjIqcAXX'
        b'vERMt/1TkyuiwNgZPHaAexQ7JnSlAF9C9xzpuzschdRnwzBTX6yZu4RpGqj4OV8JGI7JX/2Ec0Q0fS8r8k5IrGGl+6TFH6p9feclvZe90q9cvcr3A989D7bfXyX87GzO'
        b'5xF/yL+/YJsiNmGZVwAfJ2p+e+mzlCmT1yZ6r1p3I7bmuw1fJEqWuXxRf/29pe+XLlD5aH8VOn3Sq6VvluZWzqhYcPM9WfTn8ROyFdKANz909K3YFuLxIweP38uv1nz0'
        b'+cu/r7n2eX1NfsOevI4EQVLbm3wmf21o6LlGqRPdpgpDD9F1c8vyk/icYb9SifZTy3VPfKPAuFkZhU5nNKHrT+A4F+2WB9vYJJiGrzzFWlnTTj+7vBnvV8JRb1yU8eBr'
        b'Au7kS6eivkp80Lg7ho4atzSFTATaTbc0mUl0uyQYdWE12NqrnIons5ylPTqNbz+Bw69m/HYDNbanpvaZ+GxuBn5I9ZWm4UOoKyYuav7WkW2+u8WUpGbchW8ZdlnjotFF'
        b'DzPfCZdYbjdJLcKdZttJxs0kx0DYTsJ7F1Gj8ClbMulmEr6ADpk2lMx3k/ChDc/yID8CjDvoAC6WaHe2Uok1PafbAR8x3HZAW8QY2wEDI9atZHWl94kG2Ncy9tfBkWR+'
        b'ls5mBzJzvxNDpGYpuNtmxWUgO4upbaRfGTsUIIbk04j0KwkH0+Ljm7s3U7Pp5H5xsk48VS+eqhbQ5R07IQWWShrB8YLugl7eiVJ1KZHtNdU6/2S9f7LWM3kgLFKT1juF'
        b'M3J199S6h4F8uEYH3rrDLH0jG91VmZw0jynYGdxVUcGLE7P4/FFKxCaOXQYBC1TzONGqKoJlfUFKeUbwrelswc41WOSRabiazMO2HdtS0YU1OXPjXLnxTa7chP9yV24g'
        b'unwtsCG6VNS3GMA96cRlsphUKTlRpp5OJmTmy8ksyKowAa7IHMea/+uXN9Upq+uam0guqdQcyYja0gA4gXUrZDSFLAfCLJqsxizbMXI1cDeV2lPFmgyqALtXWU/JbFXI'
        b'4QGZWW3OfKkNqpa6p9Agy60qrqGoWKq25tZaubH0RobYNlZSmNk8waRsMKBUqprawUbRjCjb8/EzqcrKqqyJHe+rVeN+tWDOeF/NWLBo3F/Nzh7/q5njfXVBTuL4X02q'
        b'kYwhtT7Hy1NqbNueFTRQIc4gQ9bLYyXRhuYfbWFVZ8Nwz7bQN4YxnyRXUUthsJ9lt2ebzPmwTOBGhbVJsgSL3kLh6ThwVa47kQ+ubaodH6cyK6tskJDKIcAouTGGo4Pr'
        b'bk02bPqeqXnqVUrFwAPlnGe8hEkzXHnFHpxnPNSHD0YqnUAXU4OO2THo+Ez0gNMPOiQDhYwEdGlpQoKQ4RUw+HV0z43TOXmlBXfGlMpAOesYW4YvFuGdeDvVYmnA9/C9'
        b'mNJCHol6mUUHN0wr30SVUaL9vGJK4awFdbATsTptGj4mFXDKH7fw20TcuIlvqgrd8A0hw/dnZ6JbrpSMaXZ8EtOHuxe247fITIGPsiG414F+K4EI0ZeUiQoew7YyqVPQ'
        b'W6h3GUf7XrRnqhLfkaFrbgpCO36TjUaHllE60DV8Ab9cVMPpWzLx+DCnflPhHWlUJEVv4k4G7aubJ+VRAut9tgJ16By+O0LfQ/w2R/3OFfg2JXFfyAiJ88M49r4cak9y'
        b'nek8QsZNV8rCQtwjNpKO30WvE+LV+B0pn75WJa6BD9ZNNWNHBPe1+4S4V+FzfvNGvubVyLkEPI4OypzWBjk6KAUM34GNR6+h41zMJbKued3JJR9vV7gxDD+WTZ+3iGao'
        b'yKbZ3SL/e5xcWYbvzKYTWbeHej7Fmny/IlhSVFBHp6DGR9YYDD6LDm8mvN+Hd6AHqAt1t+BXKsl9F36Ae/BhsoTpQg8mChl8DPU5L1i7gOP7W0TUriCMZZiV+O1VTEFE'
        b'ItVumojvkSIdwRfmVoJiYQWhDu1mMyZOafrLH37BU/qyDBOuXQAGhWeOJJNlyg3f2suer3p+b96kgrvFcVmRi/mLXbIcK1I8On7x3Z/+YF5l/w8Of1fw+L3uHzqf3ZtY'
        b'sWBbZ/LOuJ1bXD/kNYhimRWRTvseOk+7tuKLlXcf3t6XvC+nRRrotGDNl3WvXF/l+2O19kmi6oas5vtvtvq5X8v9eue9I/WsXYoquTj5ow+3zVrk8v+qErDge2mqHe/u'
        b'VW/bvEFy2uODg3l/KXKc75d1KErbXvqHq3mq1oTCaT1tWSWC334RmpXudnhry+dPvvj3zMnbfb7cmKWxdysWNHvHH2qpXfgo79VL/9W55Idlr27dGv53nvzLPFdVRuKT'
        b'sF333dd8U6SfcEPKe79pY0rdHsmN385+Z45LZ/eHr67M9QhrTGWUgcvfnLta6smd9x6zR0csNSbQfnwdX61Cb9JVyGS0ew1ZNOGrMnNtuW1ONHKdU0NMUVw0HKfD+sY5'
        b'lu+PL9pJo+miKgW9gi4YV1Wbc8ii6gZ3en4dv4leiUEXJs6PzRcyArSDxa9MnkpXRPHe6eAmLByrOTdmnBOze+g4p0dxDb02MaZ0YYxxxUSXS/j+Mi72kCg0phBdKMP7'
        b'i2AhYo/38tB2Md5HF0wtlfi40gnfBiXCvYw7+UBv2WK6YMKdleg+2tuWDO49dzEu+BXc2TyXkuqM7kVAjIjEkKZ7cx5ZW53Fu7iD8P24G87p25Ihy91QrAek/V4hS0rQ'
        b'A0A3Q/BOj3VmbsIMPsLQNnyC++7r8/FhJVVrRG8y+G10DJ+M8abfzS+qUKJ9qAMo6mRWks5xizBzB/faO3UB5C0hees8GcUOkB7zNlZzXseO4qNoOxkzyFDNoqvgL+4e'
        b'PjV3DT20jtiIDyjXroGvqRl0qxTva1/OnWb3uk8mEeRb6BiTjDvxnqgWbi14ahLaRZawuAedsl7GwiJ2F1m2PMeuMSxbYK4ZsbdVEuF64wRL40fyiC7yYN8bFiyzI+ki'
        b'Ty9O6JvYF9I3US+eAgs8/870AXFMb3u/OKkzb8jDf5gJnJCoJsmS+tb2i2dqxTMHIqL7cgbCpX3Jw3w2KJWsaoJSf5E6837YXfmDpnuyB7JhPuPlP+QTCKs9siYMm3R+'
        b'2tlpvZWXF9+N0MbO1oVl6MMy1PYD4rDTm05sOr6le4taQD5pWG3a3w3XidP14nStb/pXdpDBsD3jHaqp7PeSar2kn3j6DniFGO8AenCDNnyK1gd+RzIR6MTJenGy1jd5'
        b'wC+o20/T0O8Xq/WLHTtBfb9fjNYvxlYCUhr/2CEvv66F2tBUrRf8GgAS+V4ptl4YsvUVeF8zqd8rSusVNRAQ+Tggpj8gpjdbFzBZHzBZ6zn520oQ0e8VqfWKtJXg197i'
        b'zqaBpKm3ZvSRn0eC7zg8Ij8DSel9gMcWkmEBXgZ+tjLZUbbWg87myyyFgD/ayIkzuq4xmTkFwhp6dFv8AJbPCsbk73nuJJaVwgp57OBbXTob7Q1B+FJcBb8nPlaQDIOC'
        b'6rKC0kGn6qyq8vKc0qyCnAoOp1ADAQUrdGqrbWoxuFpSnISzJMcRF0PcWZPJA5biBATU49W7lpAOFOEBTnTofgNlmNT//4AOCgzCz1A6UcyBgygLL/fnwe9WvRUwoSsT'
        b'EKyp6OPfTXpUp/UoJL8c5l+gJrlPeLdqwDuAu3g/wnQ5bCcIcB1mSNBRNOzMd4kBBDTbgeMsFzJMMC8YzuYZcOTgAPErPhsQA47hYjqKhryCRtDjZgF63GyKHjebosfN'
        b'5tDj4BB1wD1O6x434JlJ0vhnQxp/8C4HYUehFaThFAAITIEulgI9LIWiA5rD1OXAh/Loh/Loh/LYUfh/AJvnRWHzvGhHJSFFoTPHwwNwvgAA5wsAcL6A6RQPzxzrDgAC'
        b'fQEg0BcAAn3TO/KH7V1dpgwzYwXBjF+I2l7rG09+NdM108/M6JnB3XUUAMiHbVQPW9AeZiAfrAvMHKMDeyaDzWKH+VtYl6Bh5v9kuJXPuHp1zFeHaV2CdS7BepfgYV4A'
        b'4KU8LfiKvCQ2JU3lcqjUuoTqXEL1LqHDvBkuMOraDuHlMJupOEwT2HsWMnZGIIQIfNqwlc4y/nmCJvRqssU61Nnw98+byfBz1BMsi0eQTBbxAcWEQzDpFhgwTLhrQDJx'
        b'ID9w7WzAM+Gej1y7yyfIJ8o96LWn3Mt07S33Ide+9NpP7i8PkAd2Oy0S1As7RA2sPGiHlcknoKB02XWxcqcu5y77ronwczn4TTJoXzKhXTmQH3ms4TyWLw8bhcNhx2Pq'
        b'hfLwHYw84vIkKyQSey7/LqcuXgOP5O5B/rt3TWzi7iaSr07scuhybBDIIy9H2fhuHGC4wJc7HDpcOiZ2eDbYy6NHUeBA0UlEFJFkQoNIHrPDHsAQ17OLnKjPLdngRBg7'
        b'sxT18qZ2is7TUK/4JtFiG2F0Agnd2LRI9I1MpWhJbVK2pirb5fRvYkJCYmIqbG2krlfKU2GmkiUkTCb/k2QJSVL+oKC0rLxkUJBfkJc/KKgqz5tzgR3kZeeQ0AE+WV1W'
        b'WrzwgkABEuygkG4lDjrQDR1FE7kUNjTXNipf5LOT4bMCxSSY4yIhiOLDJFtQWsGhu71gXtOlQqu8FIk0w4rseRnfZK5ob29LjY9ft26dTNm0Pg42eRTgWS6uzuDDSlbX'
        b'ujpeXh9vRaGsboUsIVFGvifljeR/gUfRUxQN1LXcoENxWVZGcXVmQdY3k4DorMwCSiH5O6d2A8yC5XDkqmwnmcoSppCQSBqQ2QVWMY9D1IsFWp0rCkrzinOqMzMqs/Kf'
        b'M6vJUj5Hl6nI30y1ejFL0apUZtJNKcs8ilsbS5SNNKfJkBNvJCfASIS83Kz48Y3/2IX6xssm86ROFrlAc1PMtJH3dEU6PLXKZDrNJEkxC+LG/vjkb2JeoKSDdvL6hlpV'
        b'cztlP63L/2O+Fka5YrHtSIPu1uDLfp5tiWYGew2eTZXs/8fee8BFdawP/9uoS5XeF6QtsDRpAtL70qudjmBBZQF7F6VYUFERURFRiqgIqFghMxo1N79kl5woMTExvd3c'
        b'QGJuTDP/mTm7sCjE5Hdz8973/d+Ez4Bnzpkz9TnPPDPzfS6zCV8jyJHCfI191fJ8jV3LJuFrPFDOLFlaVorGA+3IcbygcZZFjkdtODAMzWrL/iDuIIotcxY5yTsiFOSh'
        b'B9EOfwX0oF2J1tIPTaCqHx7V1/Eg+RxTzlLjxwESVGVNRFzqsicBJIz5hiF+YQpUR+EHav92+AHqVe9vVppg+S2aRvUVrc6XW4TLJQ1Db0TBn5nfWHRLKVu2bGkJtufj'
        b'0SuFtYp8n79RwHtGFPDsw8L5v30bFiUvvGM6z95BVIR3tZR7O3s5/I4kaenEsw+NevHNUimEb3biveg9k0tInn106h96wu03nvi9wg4n8WymJ1vflK7R0IsZNIMxLz+n'
        b'dGmJLGbSlVGsEdCPPdttlpUULS0pKl1FuxO1d8B6hgPKENY0HCZe8nLA+ge+B2sDDnh90wF/xh34zmMbr7yc3Z1dfaW3TJzM2B4tV3KrNNWxy17kMp30ZAWjCbfSok1A'
        b'qaXrx05EQLWTVg/ZI+A7HsNJBtnETFkpRnPSPI0hY+mM0eP1WfYr5qyObtObYBce/g/FleF1dbzkTJb6yBbB/OxS3KFQoVY9i+LFm9QmYXni5UKUDoZm0jsK8aNS2Cip'
        b'HV5Kfj4ua9nifF52KdIcc8pKJ85WaHBqeGRC8qzMxLTkxISU8MzQhLDwFJLL0d18hCs6wZZAaSXRQoiun8Tg6HgZQlrWbjLzk3Shc+LNb2OLn2RBnU5hbG3S4RmZ4jDp'
        b'9kHSQsvocSoilfjMs9Md6NLJbpmEciqF6CKdm14vxRsGi3nhacmTLOIW81JWFJWuzi9ZTBqu9DcyTwvEScYSGjDRpdmLV5EHJ5dwDpP3WSn9l26QMSgw7vnSJhkFBNP7'
        b'KSYpUSm9G1LO3/C4Z5dOAJD9vQvcqHqkiqFI1n2fSXfiNiHTIPmREh0SHM/LyV+8tHgBTukFC8EqE+h2WjSCaB48GWlsAfcJ4S5Yy2aw4AmmvZUC7TWsFjSV017F4CGw'
        b'nd79CA9Op7c/4nmaOtzrIVIHHd7qMk9qiXzCnMj1Ah3YOgB2gF2r4CX0fw+o4qD7t7JgTfJ6YkCIh+1O9CnZCk2aKoPX/5rxuc/94DRB6+SWK6XQII9ceOk3fI+hvO6E'
        b'l1RVUm35LJIxH11DeBSvFffKljHTOSQiMCcHXIZnuOqylU/YnVgWjyMWzJTzMzdGuhklcCxTV0/GnuYyVtkL4tPs7WE13OECq52wjzDae5oAryod1GEGg5MRZOV5Tjjs'
        b'F5XDo7ARdo86O9s0iyzA31AnC/ArK22y1BjLQhiE5eTAF8q5P8uIco6Jg1WopC7JsDI2KYqdDKowkwdeBidX2cBToJUB+jlcWB8K6ooMU7ezRA9QIl76p5ckXlcFrlo3'
        b'bvYW7U1PTBR/OqK+lnHQJOzSxVKteZztIgMl7cYrT/bO56rs9NC68/FPd7//OPtYIle5xvqtdNbak/0/qImZCXtO7JgSc7e22NOx9zbn8sXaGZxfHjbx3hg4efUIJ8Pz'
        b'k+opdiNfGrzUYf3oiyG/OpPY15o3lcwzYJf5fnSDs9DdZSRd4P1km35GsMa0e69NPWO5Iob59PKCtlOFd/8RcnX9Kz/ffLL51ds7Li4/P4evffFnkZKJ4cYf4s5u3vyt'
        b'34ZPtgo/+WT92YKkdz8ILPr04ZKeX5nblb1SSm7w1cmCmZ43PO/oLIgSgMuz8YbIFpZrLtz6GG+CBVvhdlTHNYTHdhkvOeLT31XYnaVGMtsNHkolZ1PjQQPcNbZPE92/'
        b'nT57fjCG9mu1GRwAMudF8ALYK3ckHp4HF8lyqCM4ky9MgO3wkPRQ/EpnkvgGeLhE6IzecFr+BDh7sQ+4QC8kNsAu1uimzfWwf2zTZnwRvYZ7qagArzOCtvjxS40zwUna'
        b'tdFhWBFBTo+35o93biRzbQT7FtCn4DdPxZUl9T/lBVtHXVCBBrCDLDKuBm1g2yq4afw5eiUXeg32ymzQBI6AblBDhnEvio9jRnAiyUqjMujDdbMr1DsWVUEO0w1cceWr'
        b'/UuLANhWKH8URc7vxoSTOXl/OwlMmptX7sjQ1hfr27dZS7RcKC2X+1o+g1o+fQYD1ncUxYlpQ9PDBgruFI6wmdoz8Y5RFA7ToSLD2LzRpFZxyMiiyUtsxK9VGLKYOuE5'
        b'VR0DuZNZBlZNi8UG7ujnobl9/cIhH/9r6n3o/4HygfJhNtMhgexOTSS7UxPJ7tRE5iMDE7GFi9gA/+BzlQymA9nPinLlEEnujyL3R5H7o5iPTHjDDJae+5C9oJ7TqD7k'
        b'5FbPoQz5j3QM8YGzKGZ9xH1TwaCpoC1fYupBmXrQVx/pGtaGDemZ1s1tsmpya7Ki9GzadDuNxHru6KfP+5of+vWMk6FhNkN/Gn0D+pGbdKvLnWj67fnrpBte1RnPnDf6'
        b'na2bjqfqbYzxh4uKHP5z/akQ5x0nVKYzLmsEK/0RfyqFtOsQhUw8l5nMNcJEVSVzkHAAVVUJdkNJO0hw/h0Tpmc9nWBbbUpUcPIDTlh4SOoDTmhyeBhfaaKjbCWPZb7j'
        b'HyjlFmaXLMgXlWSxn8E6asoKjJt5v/KkWEcMdVSq1KhUJPYLTYJv1KrULtD8C+GN2H7RNpH9IjgvDynV8mdmZPrbBObyUc3/eTNIAc8Xz0t8s0bh0FkT7HV0kurRo94S'
        b'8KGd5884obfLZygX6ek5aD60tKx0bHZUilulVDp3/F2zcul8iu40v2Ninr1k7Fn57NDXedkiXsHipdnY4oZmVkXoSnHZkpz8iScx+HXFo3YgrBLLNlUHk9Qm2h9J52Lc'
        b'bFU+G7K5amn+SnoqhmuF9hixhD5wNMkJInRPUR6eR4xVRUk+OUKGckaXgWePMlpCikbmCVbJEc7Ozlb8SWY49HZRchouG/cmUWlJWW5pGXbWMJqyMy9CtttaLn7C9Eaf'
        b'IT2zbNnifFkXkG5lR1MqXFg061uCqnLCNOyTwyPC8W6D8Mz4tLiQ8GQnnmxCnBo+M5U/aX3nk+NvuLLzi/MEpUsF6Jdc/dgvXUYfB/yNFFZOZGNAV/NL8DFCeRvDbyaH'
        b'/xs1QeAa/i0LgfQI3KhvkglTK1y6OA+J1AmNCTxUK+HJ8cGxzxsOJj4x9zuNCXll+Zn49BxdFdiBCP4X6bDSfoPHRWn+AtQvUAfJyopfWowlxW8cJVxZOvZ2nBhOBc0d'
        b'8fE9LCBGu25BydIlqKrysic587e4jLbZLigqzy+W9Xw0NPPwtmf73KXFoiJUXTglVHFF5Cqq5UkzRicjb+niyxeTzurSnIX5uaW0PJh4bp2S4OPl6kY6N2ocUh6cByep'
        b'RyxpeYnpCY9NJBQnTKegrISMNTLayTHGyQ0M9BfOl5cindCLeCsKi3ILyanIVegtixejwZddQk/r6Zsnli0i0dLcItIIo+aFZSVL0UAmh1FQ1UobGw0EuttPXJljUs6Z'
        b'F78UidplyxYX5ZIDGdjSQ8aT/CnPicdOKC0zsqVCEb0df/x59ijkO/GwCsCzT0hL5uPGwKoAzz4kPH6Sceggd2zVi/+8s5rf2N0ePCrqcb5Tx7L9W6dmXmjlsIgn+4rh'
        b'fjfYJXWQDnbCWtqUcQ7sI6otmZCfd1FEE3KxN4eXFasiMKN3xKuCcyKRujqLkYs3tWIDB2wxiSCLYmppWiJQ6SrdJc4AO1Rm0dvhe+e6wx5HeF0KKWagqWQPK5XwFMFu'
        b'TR5tFnnGJtIOr8Eaq8Iy7MQC7gG1KrBG6n8cO7ZPlTI3hQKH9CinmLSJLCGupvJuws+Fa4OaKaCXFMIDVKNZ8ZgtJCsrMEO/bCaK0QKX4eZxr0Kzwu0vfh2BvjpHoyDJ'
        b'fpS/yldk+Lrqwi5TsJEmbB4Fm8HBUUuLPj8QbIFXyrD7CbipZK2QgKkFMQnY4EKnogD3gm5XWKFqYwTaVcdsHUHEL/xe2DwFVICWVNCUlwSqQtajvG4Gp9H/J9DvbYtW'
        b'glpwKiRnPqgOKSlKSlo4v8RmLji0qFCLAXfNMAWNsM+cVEf+jOlceHGZGovBgteYUaDXBR6PowHDOzdgQ9hE+UKZglVGoCoI7MkBFeNyUwGbYR3+ey/sggfWgoosTbid'
        b'xwCdSdqGmXAHDXuuj1nHLZfuxOeBjS45oKcsD0c0qoGzo4YnfnqUowFoJxzqZWVlqbB2mbom3JsqrXY5sxS2RuG2oa1jY6xmsAm0KZMXacBKfXgGnIH7yoJwlR8OC/xN'
        b'RrhyOd5rrCJKHdei8ALYrh4JTtiVheNE6kAbrBHGY7MKfi+GTW8IA52JpJeilIX4Eu5P+xREMaB6Curi1XBfMqgB1UzYv1w9MgRcIp2cZfFsOiiVKGzHSAigLRnp45ID'
        b'FVxQp2sDT+mBVnBSX4/NAIfitMFJcAT0lQUzCO7vLNwjRXxfh9XjCseCx2EdelmvP2qmzXArqmByLAHszWHA7clqyWCPBbEC+oBj8LCcHTA2mh8jcE6Hleblz1WYLGvq'
        b'40coqrMjZVPAHrjflnSqRfAQvCGDo6IUn0/7t1NOXy+fdnKMLrhmn0vMi2Gwx1hUjk2LoAmepM2L8KIb2WJKjoTDfcHwuiM+7oE7yA64b5qrK9iaJWRYgQts7HY9ms+K'
        b'Ty2y9FdUED1Ak0x94yUVqVfjoatuWeOKfR7rrAWCSqZiVsgHGVfO61qeDnVU4AvMaqdtvJlVfrOBL9yw923b5R/cXCIIf2XdEdHadV9l/qqZfVPx1fz0bdoPXjp4rszi'
        b'Z/0nW/I/D8l5+fWAU3Xpr/zyXbju5lsdnOD9s2cLdy6wal7/ocq5WN1PGitzgiQJohQbdpnfWdekQ3O+qihMnffozJTTYQm99i2qbulKjUOn6utv9cc4VRqnHvf53tpY'
        b'lBz68sGXLn14b05knmNHWU5Kb/jI1i++HHn5XFkH26875ku2Ydh3mao3lxz9SvfHfzBvGyx7J/1Iv8ZM768a7//8YWRY1ojqgav6wku3PtDeUOZzf+arf/ecdsJO78im'
        b'E5nLPRyUBBoLPq9LD309cfCMQ8Mxz+oFj8qEX3/KfvPL8uNPrwSoaH3/ysod7fey1K07TXd/9rX90eQzuyy/ShwK21Tcz7r/t+wvvqn+VGeNRfSP1McdcV0/T92fW/X0'
        b'i+J0w7OPAreVWwZ/qHPkn7V5e6pm6px+VbhDeR9S0YpP+yvaWd6Y+nnQttumK89v67z946utEQUhFbNenrJvFdWoueofq8oOqpftdj2x6/G2dwYWGXUnGd9ZdnOObc7m'
        b'5q5TlQmqlzev8vz+jWnfL1x+SXu7ytGrevfU3qrZYDHj1EexdXx9Gpl5YtVMobMAtMJD40yT1k7EMpkE93OfYYDCPhG2efaBq4+xvULdikUOgMAGWItNni70SY1lhZxx'
        b'R07AziAWPJsBeulTDDu9MMtxzLqoFwkOg+triYGyENbDraBmxTTYrqGuWgIviODFUnVFhu5ydsoCf2JQTQQHA8ZDPFW0McbzLNgshT/GM7mwolxmUh2zp4LGuXS5L6Iv'
        b'i+xgvshu9KDJcXVylGRRqpIj8TFPzq6AjcvglpU2xNQcUejpiEZuNOjkgK58huJilhVsEBLz77ypuTT1NBZuIuDTbQX0MZLTsTHkkEhByjjbraHJY+zRCPbBy3CTzCv9'
        b'IvKJe8Z26wtqSbn9wCGwcTw+EeyGDWy9BeGkXi0CYR2KdgLtHAbHCaknSNO4AqvW0VbmQ36Kjk7wqsz0O2r3hR3wKDmTUmYCTxEzOgvsAG20HR0eC6INzCfLlwpjo0HV'
        b'M1AENgNejHcFfYou5aCCNH1c7ErSZZAI6kMfpASkfWiEsWcIk2hC5CZwEuUeYzHdmOCyHw09CAih+8U2sB99IGpc4gR8VgZsZSjOYPEiYRXf4P/E7nNcJTK1cnIGktUE'
        b'preJSIefSl2/rxTQrt9t22wlBm6UgRu2NPsNmU2tT2+KaAvrjJOyACMeTWJo5lm3qFE8NynOkOdZqz5kaS/njbxW45G1PWXtcd/aZ9Dap89MYh1JWUeKtSyHdIzqAts8'
        b'xe6hYocwsQ7+eWRlVyusFQ7pWTXlDeo5iPUc2tYP6A66hItdwh9Z2eK4YUWGtVtX/ODUEHSfseUxlwYXibEjZewoNo7qUuzVHPAcdI2qVRrmjXNjTjsxR0Wz9cLGb+4I'
        b'm2kbRryfE3IaCjEFMJxJI82mNykO6tiKdWyHTKyGyaZyqQE8mNi9Q4jdO4TYvUOYj0ym4mddh6batfo2+x73b/GvV37yaPzpFJJMhiyZdJJMBkkmgySTwXxkYI5uH+Mn'
        b'jmEkMQWSj/fGG8ulaGCOU4yQpRhOUiRoNkI8ZBpFMDF/zQ9nLZmGGyZKzJMo8ySxYRK9OJAmdpohtg4Q6+AfvCXetG6d2MC1K2OAc1N90DNO7Bn3iCfo0h3keYp5nn3W'
        b'lK8Q/RYnzkEh4e2lSazSKat0sWn6I3z+p01BbCBAP12OA7pUcPKge7LYPZm8WQ5LifOtrB3KbFpD/+5ad0dj0Dtd7J0+JMtuPJ3dWIl5HGUeJzaMGzKd2piAi4tuV+pV'
        b'o/+SFjyEFDyUFDyUFDyU+ciU1xhLmbpKH0ntnUt5RrzwqWFV3PR+93X4gzr8NhuJjiul44qZfVZDFrYY1ffIwrI26mM9Y7GJoK1UoudB6Xnc1wsb1AsbyLhTIE6fJ87M'
        b'HQpPFCfPFs/NQ/1LvwAnj8JaFqpclASrjosrXvoGsYOfRMef0vHHB4vc0JAZZuPfTq6d0X36g06BYqfAIQurelGTh6xXSSxcKQvX2pC6KMLxs25TE+t4oJ8h+2m1YZSu'
        b'zRBp1Vixjiv6GbJ2rA2ri3tkYFSrIrdEMmVS6NuYpbwk9/lDTL9HPuHP7/Ostj8mmg7hdZSXGePXUZY6MZnJZP3jrwr/1FWWNpUAxg2NYLXxqyyKMlvARhTsVyQbbOmt'
        b'8UqVypWMAsXRrbbPMkn+LW7Nfsx6znSRnF+cl18ietEaAjFYSo0k2ESWLeLNjIt9gSXEnPG8JcQxnsyT4DFwCrYLpfQjsD+bzEWe8ehSk2H/HAwJNoIz6nr+RYR7BQ5M'
        b'hTWOo7MKcHSG/MTCGjbR59OPgk4VpAJsoWcp0hlKVTJxo6EJL7vh66XOSF9zLkcB0jMPxeCDvtbzFbzBZXCWnjrXFptrpuC3oBTM0T+ngl20fWFbehjcx4mX37kyM4bY'
        b'cgqRAshZ9jMeMU63nAoZ5P6ohKBp8OR87MIJe3s5ygD9YKMacbkE2+NtCQIAdBW7MFzWeJMHlqLJc10cuMJVKcFOUdoZ8Ew56CCZSmOyHEE9l++AsdermHAT3E170wB7'
        b'c0G1EJ6FZ7A2Gq/AUNRnqS1Xk0IUkOJ3LAXu5KD7LjDWL0La3ElQT+LmIkXoXIpjmLwHlqXgdBke9dNztbkO4PLolhWRAnFTMh9sXIWeuoR0vq6x0/+gBRwgKS5IiYc9'
        b'cDu4DHtGwQFssJfO5ZYseIwLz8AuNMPkMNALHVDW9pOipc7zhT2W7mM7Z8DJKWVYo7TLhB0pYCesS4M74f60OOzO5IZzAhP2moIbpNq/n7ebYTpDm8NwzXIOs1hH29UC'
        b'DKwYYbHZSEJlWaXbG9AX46dGMWrtg9hIosXcLJwxfnO8kqz3YkPBfuZBxgLGWsY8i3XMKlYTY6L/1jLzGHnMCpbR6JVTKL3To2nuYe3gpTCIe8HPIxj4VMQDpeC8ktii'
        b'4nw+uwTvuHjAWYz+QQtaDDYa3UWOR9JqwQSStYQM3zEvvv6Li0Sl2JF3QAEadN9i9DsSrmKXAvrnjm4X85JKt0qfdZ9ogNUnusaXuIZRrmGjN5CvCKmbjhA1pKifVWIk'
        b'ZsU+DHKhL9ok6jOcYv+uxOBlrW1y0KLdwwXBygg5xz7Eq4+dBfHrA5rAJbrTXUcjvok7V3/M5OUC97rTI6iuLJUL2xfDi8vV0cxMl+mH3SuT900tV2Somd5VQO+LnaHv'
        b'x5Duq5o6H17jFoOa0b7oKDVwzYYN5VxwVV9m43IpA4dpc+ge0LwI9igpcNXRN5Jty5yBut1ZqTMkeBi2wSPwHLwiisdzURaXyQNVYOdf1h1KNuOP8RZ8HoXuCCUVbNkH'
        b'91/tBxfl+8G0IvrnTmpX8KXo7ui+vIFpAyED064VSTyiKI+o0RvoA3a45ZRhM6jgwsvK5fCiJgtXqg+oAJdphEedLzjLRWKJgSXFZg1wCF4upS3dTfAa2L8QzfJ61OBF'
        b'JSRK9qF7BEhm4nLwwUVjfKwC7MpJQtP9jZlEkkxHkmkb194BtINuR3g+Fo3sGNZseBreoB06HfONQ91sF7zsEgMvoVgFsIWJhPVZ0FVkp3SKI/oVCTQr5a+uz5y19O0I'
        b'rfnJU/hJSjaZ1Tm3IzX8io60TF99MnLw5bivp103+f6dB+rq9Zt1nxyfeUOXP9tg1R2hOIOpwNH9Qrjx58NPtz6t2qUrunWy4EDdw9SN77//97XveV/96DWNVa//ePKf'
        b'ftPe+sfj4uuLXO9t6d/ef3GN8MGO5aFmv9wdOrPmm45c949ux+npdOnWx6rti7AzgfVg+FPduYq3Pk5tXKrac3Oz2qXmITP9vPd9HU+oWn35/dSS40qu04uV9Ds/4Lx+'
        b'u+T8S34qkvTPkm5vOK1y4oKqm6dNpsn/XGrKufywNtftzWt3lCq+6rl6Id48l7WB+e2K98+1vr/DQbHi4Y/GV7/sPMfZtcw33j0zUfeA/dOZin+7kobmCFc8yr1ssmsG'
        b'N/5NvyL+UH1+xfDV+kyf+XoZ7DD10GULrItZaZ1r9h1/6L7qfNHw3mrdiKofygYSjvvmz/R2PLr/ZuyJetXO1+1t75dz/M8v8fuR89OvjL+pvewunlkxc1V/31XPobin'
        b'U7I0tHvMIjIuvXp9Vkb2vQt7Fle7/SO4d4N2n4naD5t+XdZ8ytFznrgx0TN3hVP14XdSMpn731pO/dASn9u1zSCoyPnxQPU938iXG4+Ffdl7JbF1dXc6823/l21nvq17'
        b'6F6RYWbQbbOlbr1+wpmcY4P5ksWmdUx3v+rjAxvUvrt//cPjXx3h+Zxw+9vxj39Vb3Q0bM16ukpBlJxzgClycNM0et3o2NO3Wjq+q3wtt/q1D6t83c1LC3p91914M+zG'
        b'G9o3fP9Hae6CKZc/8r0t+vz+2cxFJoqBpX7neK9tuzf7Z87G1W/u8zzNXXPB7ifmnY9VPA7O/tT0/cBj9T8p+K/IW+G98Wurl763fmnK67/yrV5vdQssVT+Y9Xcj1rdO'
        b'e7ju3u8+2v75GtO37y+p+DC58MJZ5XuzGQ8/nVJmY/uyv+Znn35f8+4/Mv5ukOix/NcfOi9Wf/GPFWcffu3yOuPbmrAbJ+z2eLb12TZGieIiP3r0655TCp7fuB+fufW0'
        b'VYB+XQV7XUbxLwWJn3//VfMH816a+sPPR1e7GYvYazeZpF6ap/HriakxKzL08rtPr64a7o99ci5nfeJ8+K3iTUfOB7ML4eUAv+SH+pYfvDm8ussuc+rKvNRlsxY/PN7z'
        b'+d0VCllreSVdV78+/fDGr3ZvCmZ0BHwe9FAMNBa9laQ57GL7OOzXyNbmsxfez0wpddm36Oe2b6rOPfly6ysm9RZH271D317D/e4V0aNzNhf+eftL4Ru1C1RnZ2/8bglr'
        b'zsi7Kl+9dGTNwXr2g9BwyQPVmSPv7uvZq/fWe5x3v1eZ8bPamqGKvZ8qnt33z3eitsSvZAXwCkLPvJu4+7Og/fV1Zm2boyWbPhi5i/4Q4j9++jpI7wa7vOmJ7z6zzyRv'
        b'r1I4/57GY98Df+sza9sb3aGR+u2OdYazn04X/1R5Z+oPqw74q7xiIby+/rsftopDvyzVPdLlEhg+Uvwlc8e6iML18U/6eT97v3z3iMUbZ2uEay/5m//01Efh5y8LP6ra'
        b'umK7i1vdsjL7JLPP1lVYnfbN69n9k69e/HWHl9JULKY1nbjeU3b/sihG1/e9rHfeUXxz6Xnt4Q3bf/zS/PabjJEZ2zauXx3z/ZtJ3657zfiXe6d+cF9wQmJy8+9PD7uY'
        b'Q++AldMq76VWPlD7yuyTFeH6Dh9apD588FP6daPgVjRjXjur/IqjuOqo6ff/o/7uWmH1J5rH33RyeHr4uN6GzO8Nll8r+DW/9Kfg+/9z62WPT7dLMt8y2rP7a+6er1fO'
        b'jP9CtPqIntdThfBv5rDZn/MXEa8ssFNnLtcBu3vDHk3KBGAnaKLtkRaghwPPmcBz9LbK3ZkrsDnSG/TLgW/AKdXH+LsOd4MKE+mmTfQhb5S33m0EG4l9LxG2w0tCuFM4'
        b'atzTXAw3u7IXwGZ4gU7lENyycjyuBh6EvdgWCSvBftoV0RHYBY/IrJG0KRJuA13y5kgDsIW2KN6AV/XwrdhFi8AZ7l0eFYsUXP1Yjno2i5RqA+w2dQwCV5zlnSLhLwfZ'
        b'1TonFRwRjVFXmQx1WLEB9rODssE22iNMpzG8LPJd4YzeLiiJ56ugOUgP2cELq9gMD3haMSV5PW3PPe0HrwlBDaiS2ZwVM1kOsBeeIlbqmTnw9EprYayDIoM1j+mdD9pp'
        b'y+xZRzdH0AFvwCoXNNfB+dvNsoH7wFka3rp5LugWOtkvgR3Y3YvU10skqk2ce7h3kT0XVgpAG7yMXRsJ2Qwl2MtKQFXa+Zh2s4hUnRv4FhINe9CHUn3lElCJVC4FcJy2'
        b'eB4BB7CrWLDdYMxBXxmKJO+vLhOQx7tQDs8LolEGVFkZi+B1kvysSLBP5BANdy2D1bATqUy74e54JYYW6GKXgj51knwW2A4vCsE5WE/cAjEYCvA6i62+ji7ARrg1E/YI'
        b'YXcCF7TDc3n2igwVeIkFTrKknoKOw858EXZ4peKcAbvhTgWGKtzFQrltKCKmethhB5txDlX4GHCGakAdaZct4BpbxxLWEpsyb3WxI+hKHzOmwy1wB9hEm+m3glYn3KCO'
        b'znxVtwysbnAYUwzZcGMKaiBiLb5aDNq4zkLzXHiRD2tQBWiw5sCtmjRlqhJchFWieCat81Qao5aoQ1XHw3H7Ud1fhT2o0LjyHc3BBVwOBYa2PhscytCms98Ge32E8U6g'
        b'ykXmcdG8gGECNnPAqelGpIewjGCfyDkanFNDdzDQeNmmq8gORIXspjdT96OW6ePGCGKXgzNRqJeK+MwAuJ1hlMqJNJ1KFgxsQYMCuoqpTqjGwUk0jT0FDpDSCbmWQpln'
        b'TwWGBqieA+rY/gsW0q2zD93bO85PE7isADeyl/qrkeJPQe1wTgSugKZoBz7SBkEdE+zUCiAvNYbVi7DPLQUGk4u6EewG11aBTtKp0pcsla3MlMCeUceZTbpk/3ZRpies'
        b'McuWc9+UuopURFK2pWzhAZWiRua7yQOJDRzNhS3aXHtUActjYftclB1V2MACV0FlAN2Tr8MGf1QWE9gQEydgMlTcWKAeHAQXSEl8wcVwrjNfz8MBtRXKs3IRq0gNHCbV'
        b'EA/OAyQ8K12co2lHk5pMC7CTnYNSpAcJaAB7DbmgDRy1d14ej1XRViY8Bg9bkHytXQ3PclV0+WhwkOpQgPVMeAFWoCGKW2AV2Bwl5CM5NrpmgupzB2gklQiOpE8XLQD7'
        b'nclSCxtWMcEJz3wSxdcxEZLVWuMCZ0UGN4YFW2GdHinMzMJoEWqQkljMP1Tno5yzlRXAIbJCBA+75BIxwIB9jJB14KyvJVluWuFoDHu00HStBG+nZ4EbTJNIY1o+bDRA'
        b'/T4INMrvxM+BW0ljecNehyC4U26mdMqelobNsBP0jXM4tyEpnb24JJh2R3ccCZ0DdC7hVhMXJkM1iIUkQAW8RqhgSywsRdhjGj000ahEHRDnWhdJXXiQBarJyQp4A1zx'
        b'F8FdfFVw1glexDK8OxYP73MMIy2OQz7oofNyDe4BF2BPEkt6B0MhnYkkChrhBIF4GPaBvmxQMeYw0JxHF33LAhsRPBsPu0vLYQ9qHG3mfDS+m+nI09nT4QlQKSLuz5ng'
        b'KP5EVqHOSE7ZRCBp1MNZ7gKr7NHAgEdRvCrsJ91lLgdsRpm2B3XTY1Y4sBhKYB9rOvpqnCZiA9TBnWiiVAPRmMQ7KEiv0ASt8BqLnQcuZZEkZsGT4KrUASo4lip108qH'
        b'V2nJc5WPhiX5VmGpSsSiETjMMASnOW7gRCZdKVtLQA8XblIgHwcygTqMem05bCaCMQRus5TKRSR2j6iiG1ThBdQvUDfbQ5o+tHyNC3YxR/yesdKZAnDSjPYCdwWJvasi'
        b'1OwqsGoFKs1eLOHxK3TgPjY4ZgF20Iy5U5wFwqWwZ8z7K3phLYnSh41BKOWrTLIMR9bgdJBYJbPMG4agmwsqg8rUVVDNWjKDU8BF2u3jRn+tDLhPBHfgsy+6zKmgI4gW'
        b'kR2wHmWblCZ6OYlWB83rYTvbhgk307ecZGHNZQfcCbpAN/35ph3jovbYTjQBtscGlKX+rATsR7A6zokfjR3hCWkvjT7+iqB5NmwhrWPnYkqWH2VLj3AzOBbGnuEz67E7'
        b'/c3oh13koMykvmkTYAdKNA2eVXZhw8t0DnthyxIuuVOw3NCVCFxtNFZRre2CrfTH7DTScfajV48te2u4WKWw41C5Oki9LlktQP0CjTm+Lx5y4SzQgfU7Yn6rBX2wSQQv'
        b'26IbsCw/wAS7FrhJx0FxCP0ckSirwj3ZKkgoXiLNncKLchxfADa8KucxTxU00B27Eyl/22UlWAjayXu04UU2aAHH0NeMKCwHGBpyjn21wUk5377WqbQkbzQBXVxwHRwn'
        b'H0Q2vMREn92L8ADp13qoSNu4sFoAt6L6oJUiZQYrKTGCdB9NcMCEu3AN+qYx0ZO9aFhOhYdo1fQUqF6LS6kaE4d1iB7yqC7YyoaVa6WeRb3VwDkun8FgGqNPmg6swLoe'
        b'/fBm0Io0yXh43kXVHpwFNxyIxNZayAbVsNaQ1LA12JOGUj2i5uTsjGXCIfRpy4IniViOBV2wbTrczMVjgcVnmk9VJa2usixGhKQ8rFLBJSKlYYYwDGEtxzcf1NPDaH+i'
        b'ExeeA5sEpFCK5iwd0G1PS9ktdiVYiiKtviVe4IC7NBrCB1BJa0m7mi6bIXJxCIYHYFcUHwuiayxsPj9Df9yR2NwCe2anCuJpA8s6Jty/Ppd8ErWcNaW+DxNEQeNcH+4s'
        b'ptuowh1sFDnHlPFVwDX0TUZqG4sF6tJZpLbiwG6k5NNqdLSmPZZw6mHgOrzMng6PglO0YtwNL/iiUXIIqYByh7xgqxYtBo7BzsJFYIvQOQ6J7FVMf3gM7KS/me0W6Kvf'
        b'vRTpCrIDYJelIlsNHlJyRN+j/AQ5difctYhv+O9Zw1d+4S0inK3ndqwGybs0VKSteauNJjX0kcV9XzUpNCTejWFoInMKh1f2Y5kPjW3FdjESYyFlLBTrCjHu0eS+kcug'
        b'kYvYNVhiFEIZhdQqDukb1y26r+80qO/UlibRn0bpT6tlDxmaNnLvGzoPGjqLXQIlhkGUYVCtwpChidgwuonTwr3P8xjkeXSlSXh+FM8PXRwIH1DBN5g3Wbc4ig0F6G+8'
        b'UCw2iGnLFztH93Eon2gxP6aW88iCV6s2ZGFbv6KpnHhGUxvS5dXGNum2WEh03Shdt1rmIx39YYaStt2QsUm9ZX1Yo1B6mixXYupOmbp3uVGmnhJjL8rYqzZ0iDe1Nro2'
        b'+pGxyTGHBochQ6P7hg6Dhg4SQyfK0GmEzTLRxyA4/drQYUWGpXVTcIsiutncapiRxNI2GSFhbcTQVH6rf7P/8YCWgNpYlJ2mWImua23sw6m2TeWta5vXHl/fsl4y1Yua'
        b'6iUfPWRme99MMGgmaMs+V9hRiN59TLVBtcmrxU9i6EIZuuALyg3KTXqHNBs18T+4DdymsJYYsfX0Li+xdVhfhsQwnDIMHzK1qFcSG4Y0BbdGN0e35XXNlTgHS6xDKOsQ'
        b'aVSYNKqga63EOVRiHUZZhz0yMhMbBTWlNxmjX9iVW9AwQ8PIeCD79kKwcMjSuj5DbOaPz9d1FQzy8cqzmfmA5W1H4DjEs25RaUsf5E0T8wL6FMW8qAFbVFGhTHNUUyhE'
        b'FWVuJTbzaUptmdVlO2jjQ57ty+4vvFI4xLNs5TRzRqPENqF96WKbuIFyCS+e4sWjdAJxMoHmw1oolcZZbbaDZq5i04Su7EuLuhehDFgD64Hyl5xuOkm8EiivBNR89ZFi'
        b'08w2DmXvg373JfXPvjL7DvN1ziucO6lU3DxJ1Hwqar5kRiY1I3PERCOSafyYgUMM5jM+pt6g3lTetKFLD/V3OyFTlr30lsz7NjMGbWb0LZTYRFM20RJeDMWLGWaz7MKY'
        b'jyxsGjfct/AetPDuU5VYhFIWoSMKbCOULgqGlXGyig2KQ6Zmx8IawlC3NKUs3SWm0yjTaUOjmw2UzMy7ki7N6p41xLMV8/LbPDr9KccA9NeA220f4HMn7NVYKjZTnJUr'
        b'zs5FIRWbJwnNp0LzH+HbC+nbg9BfA0m3M0DGndRX51JxOeLcAnFeAQqpuAWS8EIqvJCkHtPmds67w7vLo9efmhY2kDKQM5BCTYuWOMZQjjG4xIrNik2lLWspOz8Jz5/i'
        b'+Q9ZOzSpinkFo8s5+CcpjUqaRyXlo78lLgWUS8GIupIXaioUjCio4dKjYNgYlx51Ymnpx6XuI+FNp3jTUROb4SY2MycjCreefxvznEKHQlte5xKJvT9l7z+iooBTRMGw'
        b'Gk5RpUEFpxjbEIvaW8zLQPerd6ijPrGge0Ff3rXFVECCODFJnJwqTkylAtIkXumUV7rEPoOyz0Cdz3I+85GjC64yv2E2kz+P2aYv5sd1BV+K7I7sC7sWS/nHSjziKI84'
        b'Mb9QnJR8Pyl9MCldnDGHysilMhZIkgqppMInQ8Eht/WBvrRnoW41h4qaIwmeSwXPHVHi4BKhYIStiPONAtR9jc3rTZp0hnGvaLM8Z99hP2RmKevQZhFdBV1LBxTEpsl3'
        b'sFtKszDU96ybNFHOeCFdXr2BqEc54h7laDyyiDndBQkhFIwwppsbPMZBbcRwOZNhYYPEEFMPiyEU1rNo74wljasPBTYGtmUPmriITVyGvHx6F6L+Vx/fFtkW+UjgVh8/'
        b'ZGvfsrBLu2VJfeQjQ3MyCLJblzQvwXUc2RCJW02lWaXNqtNWwnOjeG74glqzWltyZ4ZYEN6nLuFFULwI0rmi2tw7fdCvPma/4hXFvpJrKyU+UZRP1FidoBY0txabxbSF'
        b'tSmjX3261PQYsWfMMEPZzBw12v3E2YOJs4csbVqM2goGLT1we1n1WfY7XnHE3nCju/QHrb3F1iF9EWLr2IEC1Hv8rFDv8bPCvceqVblZecjapjWsOYwcBfaKEPPRT+od'
        b'j1eni/nzxTPnS6wzKetM9JglfsySPGZD8VxRL0IjcHb37AHmbQ7gDKRS4WmSoHQqKF3imUF5ZoxoKidhiYbD4SkMMx6RYk1IcnrQ8ky73/iKMa4Z1WZVNMI8Ojy6OJRr'
        b'kMQxmHIMlvBCKF4Ieqsv7uq+uKubmR8LbwiXPeDeOZ1yDL/j/up0SjivSVXCm0/x5o+wVXGloQANJCvbJpM2HbGpQGwa2WV5yb7bvs/9mp/EPZJyjxwyNUfiRGyag6qd'
        b'e4U7EHw7DITdmUJFZ0nCsqmwbIlPDuWTg+5qFOLdUKgV6AVbaUMO2Tg2ZbaVia2TUUXbXbEbsLrpeNNF4ptM+SaLrReL0zPup88ZTJ8jnjufmruAmrtIkr6YSl88Vokj'
        b'bI4bbl0382FVXLCIhgiZ6ExumUPZeEp4XhTPa4hn1cKleNOQvENtyuxXuaKCZIvYekFbSecayiUY/YU+N4Wg8E7Jq2uohGxxTr44Nx+FVEKBJGIBFbHgEb59IX17KPoL'
        b'DT+lV5TEiclU4hwqMU+cXyguKEQhlVgkiVpIRS0k6ce1LT+3omNFV0nvGso78g77zpQ7bMo7VuISR7nE4e4S0RyBWsAPiVyJdSBlHThk79yEPqtFowuX+Cctg0rLotIK'
        b'0d+SaUXUtCIk8aaj8qMASTzcUGqkoVD5YxpipOUfl7qfxNqfsvYfV2+yUYHqzaJRiBQRsWkB3d1RVeSBPNQl/ChhniQin4rIl/gWUL4FuB0TxKZxqA0VuxW7ll8q7S7t'
        b'C7mWIPGOxaVyjaNc4/DQjWqIGuI5DzO4llZdbpe8ur1wZmKbY4fs+ec4HZwhJ8E5YYdwyNXtEqeb05V+Xq1XDWVN4IyyJnBGPVTgd98pfNApfCBP4iSknIRip3lkgKYP'
        b'JiJxOFeSOI9KnIdEM98BiWa+AxrYfAcit4sl9jMo+xloyNjYohFjY4sGjI2T2DoC5Vi9W71vgcQ1gnKNGNHjeqB6QAHOo9ewPsPWrjWjOaMtQ2LjiTrNiJE6rh0UjKxg'
        b'RjPtkPzD4QgKjUwek3CYhPSVEW0s9YYL0FzQ+L4Wb1CL16SN9Jyo5qghXb2DkXsjkeaXINF1onSd8IXovdH1S+qXHFrauFSi60zpOssu5jXNlZi7SXTdKV132bWCprUS'
        b'82kSXQ9K1wNfi9kbgxUwTgOnPrVxLmXmLNPQTBvVKEN+m1WbW5sVZSjo0u01Ehv6DjNUjcwHPPtWkT/GPoZNTKTd8tvCOmMppxl9OX3L+3Iop2DKKmQgd9AqWmyVfqdQ'
        b'bJUtnp2NWsPGFnckadu1pSDBS+9ODBcLZt3RfdWUip4lsZ9N2c8esncU2yd3cXrVkPhBfyGdIB2k3wl/ad7NeegzgpsEBSNKSrgTKuFOqIKrGQUjSup66MuCghGujs2U'
        b'xwwUjDB0tHUe42CYBPYMbbNatfoUiZYlpWWJt+IaGB9cvXc1dqU93kuYykQcw8knMHi72+jeP3pfwmNMOZx8umKjiB7bwJBOVyLdJmEcThr8afBDEYsw3Qn+M4aNyYbx'
        b'8XwOCggvoF3tGRZ6yU8MwopMCY0KjwtPIfRzQnSkYeiHRgnmuPwl23Fd6pVU/jvmlRO1A54UB03OKJ+K22QCzq4K3n3ZwaIbYxRVzmGpa6HPIwrUGFbJzCEzzyFLpPc4'
        b'DqsoWKNGwIEGHTFjyHLqhBHhJMJifEQBihAMWQroJxxwhMPoExNGxKAIW/JyXxThgiNcRiM8J4qYQyeFIpxRRBDuNCTUYJgKhvTdh/QFw0VMT0ONYQYKKqOGi5kMDf1h'
        b'FkFbjwswcFp/x0w6ypyGVWeIHRPEM+cMmVi0pfTpDIiQIqoRi3cWo/AxCR9FxAwFhw+z/dSjCJ76ReGIwtizwxxyfTWToWta6zOkZSfWshvSDRtWYOlGYOC5LvFvj8LK'
        b'MDRBoTPUlt8V0TZ/IPeOpzgpVZw2Szx7njhmvjg8c8jYrG1a39S+3AHrgZXi6YlDZtNQQhqeKB0Nz8c4QNIpgonqMTphmB3JUjceZvyr4YjSWNrkajInhK1uPcz4M0N6'
        b'NxI5EVIBbzgR4LdzDOj3xlwqFdm5NBbDf7YirN4QPG4TKlf6+9u5mPqt8wLqNztPWfq3itzfquhvbp4a+Vsd/a0hva4p97eUAN6oMkr31p2U7s2Wo3vrTUDZthylextP'
        b'Qvc22crIM+00+9/SvTvNTyGRfFpx3FutRtne6gUKeRYvpHrzxlG9t/KnPtAkHhGKSvJzS8Pyc4pKf3R5DuktF/sv8Lx9aKqqO5/1gBOakBz+gB3iHlLCx1LYEQcC9u8H'
        b'a/vQWED3P0Tjlj7k88eJ27LXEQqhGyZul3jRG/8wG7vEGwOyVZPD4xJSwwlp2/oZynVKWFhy/vLx7FPXkum4wL/nVrdRHLUsIz8aTpbqKKN6fJ75KuPSwO1QwubIga5l'
        b'lVOigK6WcHDUZO9wKwnHpf5PxVMXPounZjGe39KuQCMMMxiwUQQvapYowBszaMdq8PQ6evfpVqsQLvGRBCtByxq8iX0f2F2Usvg4W4T3v/xcNh3Dq4/vs6xhKiYb9hwK'
        b'KtVOUT38Toprdawre4Ex4/CAwpsrtPlMYuOH+8Fu0EMfFQRbwB7pDgdwAZx6nnRNA6gNnxl64wnXPAZ9Sqzc55lzUbx6T9rXkBbvf4O9nvStJkryzGuRz1/BvC6Jxh3t'
        b'J8y0xq6G/69jWmOXspaKv5dpnUdqHUN7Mc/kzwRay4b8C4DWMpHxwjt8fjfQerwUmgxoPZkw+w3C9ISCaeL7/wBQ+llyFQ1ZyS7GfBQMoJoEpzT62ER+NZ+DUI9rZyl4'
        b'Gn8QaZg0+ig6TE4+ehHxWZaTP8J8Lir4L+75/x3cs2zETUA7xv/9Hujy+EH7O6HLEw7g/yKX/yTkskJ8apk/+qcSPKw2MecX7oU7Y2kIyCgpBOxdycRbD7dz4clFmUXA'
        b'qIIpykSpfDNL4fArnkeOb93D1PA18p1+wM3NtbNgc5VT0N7w5NvU3bfu3rv7zt3Bu+/evbLDrG2Lme3tO7Vg6K7261sTD99SyzX49uAyq9jo7NmKHus837nD2Gb7su62'
        b'LMXXPBhTlmmd41N8BXqJ//D8ZTQlgKGYiZQeDAk4Se/1YS8txqRdOcruFHCCBu2CAyr0nsvzoMNCbg8yqNGU4hBgPegg2zE0w+EpIdw1BzRKtxA4K9GbcHYuglu5QtgI'
        b'G57jOqhb8VX/F3YbrGtMSJZ9Xl+Sx8oW0VradyG+DG392qVNpRItJ0rL6b6W56CWZ9eCvtKB9DtpQ17BA153fDBUNo1AZdMIVDaNSVZPajl16kMG5nVr8LUo5nPIVXyR'
        b'jvrrgKuTFtpSaQLa6gaf/1zaaskc9jMTmBdDVkvm0U6IJgSsPlc1MrqqEFWNHF3VahJN4DmiquJvnwnPVZLLO3ecRqwwXiNG+rCKVCNmSUmp6piUWsAlGrHSBBqxMtGI'
        b'lZ7TiJWf03qV1itLNeIJ48ZRUtdNpBH/NiVV3gLx/wQidbznEqmaKeWGLkEfZgxw/C819b/UVN5/qan/paa+mJrqNKkyuhh9T+gZoqwh/gBE9TdExl8JUf3L0Z9TaPQn'
        b'qAO98DzN/jQArbQXE9AJW2k3JtjtBtwGtoJ9NKEsJSoDHoJVCYJ0KVoxBu7E5+KEGdj5hzLhJYC9oEYFXIG9YBeN9bwY4MjF+MSGCdCeNUbqhBea4z+dkERd1KQg0Woh'
        b'8XEC29INyW54pOszV0/qe4TFQDk8pgKvlaiVOaPH5qJybRkjFcLKKCea3AEr49CcgpwxyrTLgNuVg2GDF3kkBWwEFUI011iNphly0w1MX3SCu+LoM2PJXCUMY1QpC8C6'
        b'SDi4BmukCaYlZgjSMzA/MiYuFrSnRoEzUXHOgug4lIILC3Rz3UFNsr1vCsMcNGosBs3ryFH19QxHkXsJiwGbYQVzKQNcAu1gW5krinE0MEVpRzDkU8c0xGXuJRiBSKCk'
        b'HEYWqFEC+1GDHScPOc2akiK7kbQQmhk1JEWl0g+NFn1OgRI4idqpl5iB7TjwErcENoLNGqgi2drMGXA7vEFO2RvAc8qwB17asGKFCENE+pmOoBb0EwiCzjoFRqoVUqSD'
        b'spwqiucxipqz3mWJmEhbvPY9c//eGVzgqrXNpejw+jmNnJfCfw7/0cA9al6LnlL7luJPnc8eufI4YfV667iFCjOU/2fN9TX/sLnreYOptEMS2fo+Q3Amoy73Fb+6BNF+'
        b'1tUPvnlyu66j7F21u9aXru7a2Fy+baHJ7DPp+Re56rveELekJ/hN+zy9a3tO9fpPE1YftrvctSa83yD8H0WBnTnXZ63vv5FzObFjZn11/EDGT86n5+1QXzgcfWZne+Zd'
        b'79ezc5JCGsz5ZU1V7Pm5J+OFKXqiksOFyY/Li779cMOT/GN3lCrvat5MXfOR+0P36b4lap8dnrf5YWfu8Zr2Xxq+UFNkKVx/mxO6w7VtZag39cWc2cF9N9jfxMT/GJrN'
        b'16LPhF4Fm6eOO3mUDg+CVvZisB020zPAPlgLdstcqTRbyXlSAX3r6P3lm2fDdoIVBKdhFcYKqsCNZGN6otV6Gvw3D3bK2H+Y/FfLJvZ489mGXKEt2Prc/JBZROIXq8B6'
        b'uveCE6CZ9AtuMQsetoQN5IiBUqA5vXMddsNdeOqZj+akZEP89gQ0PPHgAv2hMqghC55VjHmMTdiwHVaskz/mS78anHSmT/mCSlhBMpBdkEnnHw/wKvQiDXiVN5cdqwzb'
        b'6cl1Fx/7XREohJFzOQFMcFoZnCWVwg8AHUL3GKSLwxomPMfAJzVP0SdEGuIgXoQAtQy5U5bd7vQ5wtNgz0LHGHghIY5uFZR1HTs2PLwS0iewcsD5tWQ+D7dZS53nzObQ'
        b'Z4lOZcXQzL8cpWepfwT5t3YRX+NP2kGBnVvyxnH25EBWFs/OviYC7F2hfb0Mp/v9a4A9TGazOLhh7waJgT1lgPFl2uH0/DxUYhxGGYeJdcMe6ZiPsu68egMH8genCcXT'
        b'hOSuEIlxKGUcKtYNHVZjmFg1utQqEXocUzuQxM+QGAdQxgFi3YAhHeM6PxLR5N3i12Xd60S5hwxODRFPDSGHBuTuNDC/b2A3aGAnMeBTBnz8TA59sCBJnDqHSs2S2GVJ'
        b'jLMp42yxbjZJVqzjIDUvsPUymE2lLau6wgftpovtpj80dxA7ht9RelVN4pgqMU+jzNPEhmlDZtaNczANLoPZlto5q89mUBAoFgSSmyPuGLxqKnFMk5inU+bpYsP0RyZW'
        b'lImT2MS7S19sEtznVav8yGRq/Yym5bXKHxuY1me25UkMplEG0+4bhA4ahA5E3kkXp80Vz88ZCksQJ80Sz8kdYTMN87FRBIW4MPnyVg6N38NMe/EOKdKlxuPR/kCXiscm'
        b'jzOMMZMH6lmzfJnMaGKp+LPDf5/d4z8Je7aVz/px3guxZxMZBf405plVfFkolmxHTDEpdRQ98ALe2SVwfBzzDH1wGmiecqWXixz0rIuREzqDzWVYwU4FIRtuXQbqibbh'
        b'ZjgtGrbJM8/AGXiRYJLg5aXghp2OHM2MySGqRm4yi6y6u5b/VNKWOJMmloHzsGfRNAIsi7aSIsu81xKQz1rlGeCQiDDLXBgu62EjIYWpr4DHRctRh/BdhVQ5UBU+h6YF'
        b'nVHY4IhZZaBHTYoru7KIdvHXAo/aCU3hfjlaGbgOq2mU0F7YAHZIeWXNYBu4wEBf8gOoKCRze6Pg/hTCK7NWlhLLZpuX0cfZDoCDeK8QB94ApwleDHSDSlpX3uUCjsth'
        b'xGAtPIhRYpgjBm7ATaQ2YM4uhimTYei6oFlLLaScRmDpGVoxwnAVLW/WXWNnTl801Yxm1KJrrmXdMyM1I/4akNjWP0yOcnhW/kyOjYLYxLiNLTUxkkJ6JKszUGvZu9qW'
        b'ihJD9OiLvZb6DCcGQ8t1ffy88oD5DFK7qO9WlcIGg2epYDQT7GwK6YTaSPfi0swvI0L9MoRVJMl/FhGfhFqu+lT+DcEiBp9JWlpkBraADnhS7uT5YbDt//6aVkNlLqmU'
        b'1TQZKSpKHC7BbSFdtYsgt+AJPxIzNxdcI8At0JCN+jo4BDvQNIboY42x/uAammTKA7dApUUZdnyVvTRoIazDJt0kRlKZPU3f2+GzhGvvICVtzYNbY1izg+FhEremQAX2'
        b'hM0dD9raZFSUtsqFJVqNBmL3xV+vz5wl0onUendeUdnKDEcLEOF1Uc9ZKcfV6zLP+hPXBRq8d7LYKnBPxUzn6bdCF/7T5mNd+1tsl3b/4e601M/D/T95L/EHlyL+uyOv'
        b'dawpv5+6bP8rZ44+vfEPo69iN/Rs+OTo9A1F2+6ZLk6ffeXUhfe/fe+9hT8YZC8yfuNjyXuPC27pvbc2NPRpvWWuv4Bpu36xzkufzT2XYTNX8Vb+VJ8th+YrfpJWcPlO'
        b'lP61Xwbq1f2/eWKhcd/kDa0Po2bFeSya/7J7j8PLVrPiildf/vjQqQ8/dbUd/tRtAzdgicICnxMHF6Xr9x68dfLS/KOf/hLifyzjkdH8Jxc46YpatziVVq9/k2Ow5+Pp'
        b'/bvra8KfLHn19W+LVY5Z8kzVXlKdsTzfI/fWV5p/3/ZStaPvl/v2zL104UflR0pif/3OeOfZ+wfUmg1N7rUqsSWhhRW7Mi1/npP4z72vvr0v30fdpPN15dcoeFUPQpeM'
        b'W9oPPX2Vfz6xqTVA3SmXf1qnMK1MMHR3yfnDm5aYJH25MusnnZkcUc69rL1tNyJSfw3Ouvq2ymvLXt010NGv8NqRz0x7f2zc+paN61Vmj99FDe3XPdKfPmyKP33UPyX5'
        b'qGbut5Ur77xx7tU33n9b52+XvG96B33LvB95fm7OkRMXSsu/E3266TXF+6pTcny79Js/dSutuPiZmuCzwiWSN5sOrCsU7Oo/Nvz6zXvrGefM3lqT9uiwzZNPlA8U/qJU'
        b'5Rv48s9iT004ZMf5JKVZP694cWXaZ+/NfHqx22H5Wv2ZO0/MXRQb8u7rud+qxm5dxRJv96qZf5T1OFs37ueni2u+2ZFyLDazaQecsTxyMJXz1EVlQ8eh6C+/S8v6jvJK'
        b'WGZ+6+cvAuwD7/Lv6T2Ofvvl29cCjiqV5Tt/9V3nrvmfHFijtjtv6u6rl03SfQq01x79av+Bv6k93R5prZ7xwbqWDt/4JwlaTxVe1TyU8EEZ+wPdTT5mQ01Nza+3995r'
        b'upcQPW/D/ONrn1p4ah15wygnfgH77RnbV9/i/1Cw6PW7TzyTfvDe+uuc5m1fh138FlwJeu2jHNUDX7MX7Zv96ZTq6rZP9d+59eCDAP3PQw6smd519cHXqi9Htbe6zn7r'
        b'S9BjsGBk4am32ZnMn9KsHN+FiRdfXn72jPE7TT+p7BI+SNjb9J4o8HJEXsetewn28/i2xwf3u6rUOZtbnCu1mcs6WXN76fzPY9Z+3VY6Uma7v7jsDM/S63TpudwLLWlX'
        b'km2q6s5+YHRVe+Z3s+6s2Nd2Qn/O9kdVd9cKP/qysawmLKC3p0Li9lOJyq23d/Zn/91rz7ca7/cLn2yISvEzSTtbE3ftY5N9H36h9+hX7Z3v6IsiL28/3neGsj9ZHLDN'
        b'6sSV5JCzpcu+13n/o6X6a3uG3cw8Pq75/OAtg1+HG39lfFhgm7eucufGX7W/ONcX+P5bjPdzlBN72R0rdlZ75xk9XmLwXbFTTUSgbUFG6C9F73Uufscp+PD211MrV08Z'
        b'Srjw46Ivbs7eYPKz9VbhwI3s8yPfmWx6yTYoOOHUVx8vu3TxZGOg0r3q/R+VK3Rc2/ahnp/LiQcqr5gc8D/1menqBfnb+4wear/z+OD5ho/sHu9NX/vE5fEym5mnzvCX'
        b'0i5Wr8JNofKT3+SZ8oQrcC2XTKHDbWDNmIdVZXgCNmPElTU8R2bGuqAWdBPEVWDAODy9dSSZxxqpwSNjdKttsJUQrlzZCxRBDUlgBo8rY1EFLhI4j6KoQIUlOVKvDK6q'
        b'OxbDzeNYVDHaNLyhQgvWjaGoYKUGoVH1s4MWg9bH9uiOWUHwuohwqBKml/BjnJdHY1iNDEXlB7Yqgh7QClvIq5ahSfc2oWLYOBbVuWxyON8FXAKHHOPsxyOnmsAuMv9P'
        b'L1MSOtlLaVMZmZg3Batm0XsNL4BT4PooTorNUOIzCG9qmyOxq5TCSj052BToNsW8KUKbKoKdJF+ppfACrMGgKaRIbqZhUy6QxhEs9kEaGnmcgKaWgU2qrAzYokLqJx0c'
        b'2eAIu0dxU3KoqeVSSsU+eGqD0AgelgdNzQInSNvx4fVyGjTlBXu4oH0UNMUAPbTVqBOVrZKgphbHqTiPkabgMXiSlH4FuFE4RpoCu5wwbAqDphbySbUWR8B2rrNQholC'
        b'3+JejIq6OI82q2xPAB2EFAV6QQ/+Wrfx4DWajNGOVKOdGs5jrCg5UJQepC0svrB+vXSXZ8tUmYFlI7hCMyA6wQk/rsH6eIEaHxUcnGDCs4UBpE0WwVOr5GgycK8eAcqw'
        b'2HnwohQhBa+UJs8vG0+hkjKo4IFsqfFJFfVOKYUKZXE3JlEpsgOjTcn4W52MugVGUBGDWhUfHAS7CYmKYc7hgPOm8BLdf5rAERsZbwqezyLIqTq2P9hmR97iVWYzSpsC'
        b'rbEYOIVpU6DRnZQyB1TDPZjQwQKn50kJJWZxdO1uhfXeUtwU7FrFxcyfzSzyUmfQBnbTdrOjs+TsZlZo1OOKZRGIVw0hloCD5TRyChyIoflj21DKh2jsFLgCamU+L9h6'
        b'02mRYgUa5hDqFDipuzx2lDoFT6WQxNcUgx5cJEKccgI7MHQKXgNnaeTKEQW4kevMlzGnZkUUsYpsjUmuk2A/3D4KndJLxtgpAp1qXUlX5XXQDq5ywWWwaxx0ag/YQuN9'
        b'NpflcBfCq89gpwRwM83nOAUrgqR+OmAd3EZzp5aAOjr2ArgMz4kIdSoKHJSCp+AOBbov1KHKrcLwqVXwUIxARp9aDw+TIs/RWCZlxYAjoBHzYjAt5rAKDUzblI2ZaJg/'
        b'tQYeh30McBZUwo30+O2Fzeh/GkEVt5qGUIGTJSRLq+FxUCf117IEbpFiqHzBcRr906OvzAG7xiYDsIeGbxXbgs2jpuBKf5lvmQjQSMPddtpn48zCWpuS2FEiTmsuGZZx'
        b'oHXFKIRKbZWj8zgGlcpKGkF1ERwtQLPEa89hqAiCSh+2knyYg71oRPSwC8YRqOB+0Ev2GzmjyWmjqeoYgGpmDt0QHfCqligS43HkCFRnYbtM4O2G3TzYII+g8kYiAUcq'
        b'OSTCHoKfCsSzBkKggkdhFd2EzaiYuzCEiiZQ2UVjBhUqy0a6UNfBQTXs8ovgcNDIwYsYF1CuDWEXxxHuBVvp9zfC8x5jkwbLQjRnQB1yN90k7UvhtWyMHJdhWESryZDK'
        b'g93uXJImbLSKw18DJGnBXhboZAcTa7CJJuzkcgPsaYQOmv1bxYIKKYsPHAWdmA+UlktLKYy9Co2iM90Jj2mK6O+iCsr8bnhVSgQ08+OAPWB3Dp3GEdjC586ZNR575cyg'
        b'93ftQ/nvoUlRiQv4pKVo7BXYgcqFczcFNsHezHh57tXFMDoD7ai59ki5V7CZuQL9JYe9mgmr6SFQAa+IhBh6BZvUae4V6IMHaXGzzz9ujFMFdmdiVBXmVDmCNjqDB8Eh'
        b'0C5bmiOQqjp4gwZVXfcjnKo8K4Bd+Wx0nhxUlV1Ay5BzG9LX5oxVGZplw83sUnAWfY9xgewTAlBmycdJyFeB1fxo6WffCGziRMIrcCfdSU8nz6LvIaVVEhjCRlbwUqlS'
        b'BXfFZIwhqcLgVUylSmHHgTOmtMOgYF16OcSubGwxBFzl0K6OLEEtrMF1NW0xvRRB8GtEX0LN5Aq7QbUIvTYBdajdjkj6aq1irwVNHLp77vWFpxxR90MaGbbmWPjCQ6w1'
        b'7FU0I+3G8gzYANGw3RGHWgspjrhoTIa2HnsdvAyvPHbDtY06J9j4G6guBmikSVcE1SVwozWJvSGchCIZ6EqOcgVPgg66C5z2X4LZd7AqjhY7mH2XPovun02gCykKmO+l'
        b'DQ9JmYpg41z6M1c9U1uK9ovSx6LVha0s0CSNVea70vE5jhjN4IoDPQoFU9JJB4ozAFuV4FFZ7uQxYttAC6Ez2QTAejkGF2oyOQbXmgS6BN1IMLZyMYDLF16TMrgWOxPh'
        b'kp0M93FHcVVI6d2vwWAloeJvlKKhQCc8z8WwqvWwRwrhAq2gi1ReBN+OCB2kqcfEjWNwIWlEC5ZjsH0NgXBZaRrj0dQGj9BqTEu0OuaQSilccgQucByNPVx/AjU32IPx'
        b'W+C6gpTABfZPpZO9Cq5wQX/UKIEL1JcSFKG2F9wEqnnPYrhoCBfoRwMTiwX1ArALaR3XxyBc8IAtna1+WA120RgumsF1CW6iOVwnkAKIa6wMieZ6kYuDFMMVigbwNVYU'
        b'2AzoDyNSj0yRNn0BbJRHcZUEkQpzdU+mUVzgUnRsgjyLC+5YSy+/9cLLAsziQhrQJjSOZTAu0A/ryA3TtW3GYFwK6wiOC7O4kEypoZWJbitQgYaBlMMFGwmKCxxCOj1x'
        b'SAoP+sGzoGaMxdUId9EAsh1ISnRj5BYN3AJN8CCBblnP4ev9dZAtnMnxVnp5whZ9Xl1/YhsdWdf7RVV6OKnA/09la5mIDf2ep2jVKgwrMniW/2Y6luOgoaPEUEAZCn6L'
        b'jrWOielYOJyUjjXZ5d9JxdI9pNGo8adTsaSvk+I0mpJaU5tT22yPz22ZS9cOjhA2CNuYhMqQ2jmrXbNTU2LqQ5n6SOk5TREtCRJTD8rU44+xqZ5BHmk0aDSVt2y4bxc4'
        b'aBc4oCqxE1J2QolhLGUYi/P4X8LU/+8JUxo433gk6EsM7SlDe9wt1BvU5SpGCkeSw4ikds6lBDMk9gGUfQC+ptKhgrEwkR2RXRHtCZ0JqOow3QUFIwoKmByCghH2BOQQ'
        b'NhdnAwUjSUwPjKfywHgqD4yn8iB4qsU0niqE4KlC/nU8VXFz8R/DU40osHFmUTCs/Ofgm2IaYppKWlZRdsEDJTdXUZGz6mMkprMp09lSoYBTU29Wx1Ue1RyFsjOHEgRR'
        b'gnCJdQRlHYEvC5uFXaxeLuUaSrnG3HdNGXRNEafOl7hmUq6ZEussyjpLdpeSxNqHsvYZUVLAda+A614JFwcFw1oMM4vfg38ys2ic05gpNvPuCu1SGmYooFIn9c+6Mkta'
        b'X48cBZ1+nYGow9rMZTYVNC3tUhDbpPS59Xtf8R5wv+l3M1Dil0L5pYhtlogzZt7PmDuYMVc8L5OaV0jNWyzJWEJlLHkyFBR8WxEoDiy/XQpK78RJImdTkbMlQXOooDmo'
        b'/nHW2TjrCgEo6yhAY+2/tKj/0qL+bFrULKYvhkX5YlaUL0ZF+WJSlC8GReFAG4uf4aj/VE7Uf/FQfwQPNYm6vUdJng2V6f9/mg2FCQElahwpG4qN2VDf4UV/3b8C7CTC'
        b'89KJmE50PT7B9fgsZOULDNea90Kek9NkPCenyXhOE0YU0BGCIbPw8dimqHHvEOAIwW9GYDaTK2YzJTH5mM3EJ2ymdJrNxFa3HGaMC0bZTPiCqgyFFDAw9XeQmWwIe+nF'
        b'4XgyE7keP57M5IPJTL4YzOSLuUy+/xssE85nMslnMnlXMvNRePSQH/qeB6rjnYl/LMR5lqUzzCHXQ1iLWRid9GeG9OYU4nRzuxfYSBBMsMqpPCcmznl5dBysdmIy7EG/'
        b'wpL1iuP2w2lIf38bi3rofv3x8CWCK1Kp0ylg4bBOQ/q3nvS3Kv27iF3ArlPuZJ1Cvf80W5Zwnh05fIiPHuKjiGqV6pUalVqVUyr1CtTyFJ6DF3EINklxKyNPqVP5GWyS'
        b'IolTQXGqz8XRuCUuilN7Lk6ZxKmjOI3n4lRInCaK03ouTpXEaaO4Kc/FcUmcDorTfS5OjcTpoTj95+LUSZwBijN8Lk6DxBmhOOPn4jTlcFLPxmmRODMUZ/5c3P/H3HcA'
        b'RHVs/d/dpXcFpfe6LLv0DtLr0qsiUqQoShGWYlesFAsIKiLqoqigoCioqBjJjCa8xCS75iZuTExMLy8FP01MeUn+M3MXBDXve/nyvvf942a4Zeo5Z86dO/ec35lF7pmj'
        b'exbP3JtN7lmie1bP3NMlrqJ6xZxC6y0qWXoNisWsQht0NIcc2aKjuQ0U4iwH5VNqUGlQR7m1EV9nEb7aofv6hZxUSnUJ1+GuRlhIfFq43Frzw4vsp1xBsS/W9BwM3tSU'
        b'J1F1hcWK/CoRk8fTzYn56459ksiRx4zKJo1CRQKLkGlOjnKfPQItIfcMRHeri6ow4IVFRW1RFTqb6aQ4zd5X5GRRlF+w1KKqaEVVkaiofFoV07wosTPvjBr+yE1ppmnq'
        b'jJOECuydFlOMRkfsXuuKqoosRDWLy0qIv1VJ+TTEDuIAhm7no/+rl1YVzWy8rKh6aUUhATFAfa4orS0iRrQ1+Fleugo7kk0foMAiooT4ZDmEcOUuyqUzPdWwQ5fc15Fh'
        b'hLOcD5MUd7JwCOVOZsu3EBVhn7vqon/GJMxDhzAuhvnIn+bXKPcorKgqWVJSnl+K8SbkmIiIBBhL46mBikT5SwjSSBHGbCnF7r3M6C0Ki1agxYvIooLpOHFOdJDfC8US'
        b'VlYhmumjVlBRVoZdsYnsPeUIyeXc5awsK72rVJBfVu3pcVe9uKKqoCiXcCQhskBhmjrFxnzEwrEDJXs1Jr2y91Ny22o1pBLV0eRh1CGeOBSaOqxibWJxjZRg41OKcZ0i'
        b'sbhWeMbiWvEZq2qF9Ypyi+vn3puBVJTD+ReQimZMzj92sfsjr0tEMsbhcn58nNxjEE+XfFLvE1lAXCdetWiqP98V16GIEdE/0gP/BEGH8MsPA6EU5CNNkoe6lMd4PjKV'
        b'TVUyXZzzy5/vtFxYWML4ycrbnSHOWPAra4rkKkFUg+bqlEp6PnLIDG/iuqUlqASe0fk11RVl+dUlBWQClBVVLZF7Vf4TDJIqNNNXVJQXYgozemLGHP8j8kwTYz/sGY2d'
        b'nYm+m+7iXVKOGJTPVPt8f9hpmUk/kdqa3jxBzyHVpq0Mry4VWZRjfKDnVhWP0V0QUaaggaZIyNQsV2iFzxnk853Ci59M/wLyCBAxRbFXd6mogoEfQlRDz4KilUUFNX8E'
        b'+jRTZTo4lhfVWUyBYvkKXJ4DizVjlTVl+DzN68AsQYS/Fq3LTx+SPuZxT1VzU93+xr3YzH37fL2IKlmnctyWZlZ1TijRAb3wMBiCrfAStnip5sL9C7FZz0XQzIX7wHnA'
        b'lAHH4T5v8gEmjbiTgpOlsBecVqSo9ZpO1HpwFGwnNtxr0Rrnx0iC+xH3OCKAIpnL4FA2GEKPaX9w1RUlYrC39Mfff//9t3BF6hZHHzs4lq70U8JRnvFnbY8wuFkEm7Rg'
        b'I4nFaAmu8HE4IlVHBxblBtuVeHAH2ERMyd1LQ9TRyQV8hx3P8gbb4ACqhDjJNYJBcHxaNXw1nLAoKz/FCtBuhYZ8mUQfBidBJ9yjjm/C7XAnjhV0hQX65oIuVBMXZbAJ'
        b'8p9eTZXGwhjHygQuPMeLEQqwPV4G7FAxAZfViNeCoTK2HUG34BAcILdVPNnlKfA6l0OiGYOLsB2OChPgDj5sdXfxZFMa65KWsZfDQXty3wLsBRuf3FaiNNbrwVF2KRwq'
        b'J/XHw81ZT26zKI0NehS7zBpcqHHEtQ+CTctgM/EcTovG2ZKjYWNiPmifCnsZrq2sHwsayZIebuSDQ8ngKvPFM5kPL5LvnbpgFwccwaHJamJwpdvgWRzn6YkDiwOxmExC'
        b'VccJhXx2ZSB2cbkGmubA8/C8UA80CdXV1sFj8Dxojk1JpYqKdbzhFdhPJMQhWZH6ZJ4eZrrGyupZVM0CdDHfDO56TgPYNdg5Nt0BNkbDHamwQakY7hamw0G5pDZyifdM'
        b'YozibFs1uBUcV1SElyNsQR+XiqjTg4co2I6oTgK/da/Uh0PaK6qccpCkwBGW3XI0OCLIbYkq6ipVtRaRiPMKLEcwks/4l+zQnguHNCqrsuElXKSfZTMb9hKpq4W98aIV'
        b'CeAM6F+lgGPU52UpMMHOL8WAS6JKeF4DnFqGC21k2awHWCLxt10vRI4+EbxYWQXOOKO7YJQ1F25DjGNMRUA7Eg3cINw8R97gksoauWXaIGyYyfQN4AV2GbjsW+OFqWe0'
        b'Ft9l+A4b4vmxienR8uwL17h4yskJNsIhCh4pVUdTHnGDy2J8No6zwT4hKhmLTQCwQeVJU2xTaQT3KFSCJi4Dv7sX7of1zzRCUdZrFNaCS9iuDOwj8pkI+0B3Kmlwozdi'
        b'IdJRqix4LXdNicUHb3JE2KfuZfOICxnCijeDdXLeXXW58qDPa0OsLLOBlWH1KWk6Jvff5+i3OJjMTz7XatUerrL3wpaRMr0XVS2TW6pesc3+aUOchtl3Zy7V8OpthUNX'
        b'P1j78LVbq6/lxuY2xoenD0esWqzrtvXxG28ub/qso8NsWfLCYXst8aGl5bJvvbRu+Hu03WiOkK7OjyiQJM0u60z3VNiiG/xhh+42jY93uGaUs7tSPzn+09yYBw5Lzcq/'
        b'Zp0bOveaxOzzuDjdlScjc/2imuljDz84NPbR2z5Hvv214euvAzaPcvxXjOhmHbDwnygIsA84VvN191GpZ8SHFzvLgt4oW/Dlh7PY6xZ9l/m61b3/+uIn8dxjX2wyenBM'
        b'cZHT0ajDnx/Q3ylbW1h/QnFHW9vV8djI6p+o4SPh1x94xt0cHzF4Z9DbWHy+M7zvQL32Z5o/XrGsit8ZJwy4qrwm5rYVb6lJS6ruwMjcEaeIhb6bPtiTn/C2JOGtFeyB'
        b'tqWH/PYZ6cLzya/Fnup8c+khV7eu+CKfJY8W7izt3C7NusXO/eqkeEz9xFdKgrqdh7hwbeynhhkv6B5ede12nvGns7MS1qYr1s4zqj/xVp7WD2U73zinLu2vff2nQzvq'
        b'Lx19uOvt8L8fuunycUt60/GPHlts3l+bfUS65PDm1YvaR42zPnXurvFdoPzrbio700NwZ7zm++jsO1YL36wOPC/e88EmK+fzNdlX69+OD9tx81LPY1b7a5vfGPjkSoDw'
        b'dOWNLec1//bxRcuEAd2jaz4d9G848W2O7ddjkbduDi7+9fvB4oiLjTvq9rw36F90o3h25fzM+9pJBt+k2m4PMdc9VDNwpkbz9MC3tjXVXyfQvwe5JttftNn9KMHCyP/c'
        b'HJHrexW/n9M1CPtKYdnKQON7EcMf/KJ46tuIgoeH6r3ohLHGBzlZZV/ZR6488igi4uohekvQCxUfZVbMC7v+99+LepuPZ1585XbdluvLNdd9CNevNFq5Mfu+2Wu/lZZ4'
        b'z9q95uXXTl/v/+SCTWbxB0fLDlR+8HNrTNeY2cq8MtavFueXlB+zbw+wG7pz71fNXNpQx2w7N5iYnkRhW23eMnBFEM9GGqCXJbSniE+3CewEx7Cb+tQ8RKr0FDFuNo9S'
        b'gC3wEthCbFTA3hAKNIOzWDUihQmb2JQ6EKNqR5HKgHtBC7EynA1P2/Bi1GPilFErDazAJfAUschxWA9O8Z7YpG8FJ7BdeiW8SmxmouAuL9DszITPVcoF1/LYVotYjBnh'
        b'KXBVD839RudEDMUGmuDAerYjeAEeYQywdrjBAWxVAnfylSgl2ATactjWfp6MqdsZOAJPCxP5MU7YQko9A/SDYTYchachY5CdAOq9UJZmeczpaeb4YeAkYwy3pQ7UZ4NT'
        b'6sJnnO3twB5ip8QOLyR2NXCP1VSEOy68THqfBTeCLjg0aVODFNZebFcDmlIYm+o2f3iaFwMGHGDHShalsIQFty2eT7zSTUAb7MZmYUwIPGx0Aw7DLagWI9iF9OMgPEsI'
        b'Xl6j4ATrp8KtgjNLrAlfwSZ4HeN1OMfGC/nYOCZBbrdjA/cqwjYDf1u4m/FrGDGF9SK4MwYbhAu1EvhwN9wLh4VsyixSARwPBx2MidFecB1cw+bju1VRHnxfMwLWq7Lh'
        b'ZRN4kEgIbFwJrqAWE/hO8fIGt64jbVq4KsDjkTaMqdBxHEqaidtH7ITgkXBsKgSvykNbgiM2aIXXnCiIjXeKiWdRWkvX23J8bOAWUnwWWiB2MssGuZGUpic4rMhRNgDX'
        b'iEQsWA76iDndDvRsUaaU1JersjWqQDtD8F2R4AURWtNZgxPosbuctRatMa4TNubCJmvGMFhZXx6dFnbJ7clAhwdaiRBT1yJ4eTLYKtxYwohZD7hSSow1SfRaRXgIXoKd'
        b'LHhlLjjL2DYdBFths7pAKACjoA8XP8VCy5y9YC/hgLJFENgHh6cFo51hBQwPOxATqNVpeSLUytZphrjqmkz3ekEH7BVNGfAmwmOzWDmzwSAhSK4b2IEneFMcaK1QQo0f'
        b'ZIFd/pC5mQM3K+OB7ebpw9O4Z0MscNIK7mMs8K7DLQuc0DN2MsYy6n4TIgm+t3hJ0qQfiiKluCIZXmGz4NUAxpjsMGiFZ0WIfPufWEvvBweJIFXgwWH28udETcFnzAZn'
        b'OLDZELYyJl19oC+AQGc4h89iTFBBJxs0gu5QxrDyulnBDBiK2rppnji5ToRc5Xnz0HIYrdd4Vjis8QUWOKORw0jghTjstTi1llOitAqx5yInwmPZIz6FTaX3FoDmulo4'
        b'rFnJrA214R68PMRYj85wV3Q8HxVKjVDR8pQHslQAHRoinhpayurVcVmU8jq2ByI6Q2KwqQhuE/GquPCCD5F45SK22yp0Ew8lAsnBLjC0Ao02BptUJvKw34kiNQeeUpgV'
        b'AS4R/pb6gXp19BrAjYD7mRrAKXYgaJlP7iYGZkyWRgKqTGklhHpwguGJDQzIyKWVKSK4Y30s9sJhoSWlTro8JjHcCK+Cs6IFk8FGt8J2wNjTas5VJwaOYCR1po3jwQ2M'
        b'U0E7H26Gu6B4Mio5mtEbYSfRR+DKPEok8p4KkKsNdhCTYXAOmzejjqKOxKC5SdSRczTcyaGs4QlFuLPOO06L4f7BHLSYTeBWwgsxjPuRkEXpmHKSrfSZOdyMQWyQLp2M'
        b'Nw4ug55gQuqgVbBdhNUKRO9WihQHbGWtRsvbJuZRsUk3lxfLF/IdE5BW0V4Ctitx8uFmD9I9k0q0kCSdA13q8v5h6JZGbAHOzVEEB+HG1Y/wm87aiDkzZWNSMBJXgL1e'
        b'aI3sD84oJaDF6Aih1XKkJ44Spxp4yH0StcSjgIlEew5s9FUn91rrJp8ts+AVDhgADeAqQ40BMKrIw08fuAf0xqOHnAq8ykbzqyeEeUAdKgQHfd0nQ6XOMM48bsA1+U8E'
        b'hvmXPzbi2TdjT+G5Hx3FWNnNmb5XNxOXdESRgUAJD0Mq0qzFr6NA7CnV5dK63AmKMyuKJTMyOWLXaSexDBwRjYVJjaJpo+iWsJaw+5PXA0YWj1lLjSJpo8iWMJmNc4sC'
        b'rWMpm2vYUtBh3VHdWt5e3sKRmVu1KLRryEwtujKPLOpc1OsuNXWmTZ0HWbSp2x1Tn9umPiO6UtNA2jRwZDFtGoIyq+GofVmMRSKTGV+8b+Evs/CVWYRNKCsYzp6gUNKi'
        b'OKFGWdmfND5q3G3aYzpBqc4KIElrTEtYh57Myq5ViA7m3tM36xCJwyYRWhTnmMnMrbtW3zH3uG3uMZgqNfelzX0nKJYhX8Z16gjvir1nZisuQD01c6bNnDs49ywdenV7'
        b'i6WWnrSlZ4eSzMC0Q3FCHVXzvRZlbCux9ZMa+dNG/hI9f5mhSZdRi5LMmtsTQFt7YIJYyGx5vSE9C3qyaVsvfMFKZuPY69oTQ9v40TZBEpusMa9xyxu+dFg6HZbFkNCC'
        b'L9bsLe4vpwVyuyiC/2pq3ZVLm7pKTLMGM0ZChheMrB0vlgal0Z7ptGcWQzdrcUjXgq4c2lRAm7rTpj4o70jkmOtozGgCHRBPB6TQAel0AJPZxErs2hXTlUCbONMmfrTJ'
        b'PNokTGKyYqx2PP/GqhvraWxYVERHLaejVqD8qtMqd2EqJ1yxtO9l9Rj2mNGW7rQlvqQlMzNHf9RRfmzz6k6SlgiZsUWXX1dgSzg2zFDt0pIY+Pfa9HP7nWhH/zGFG2q3'
        b'9WMl+rEEQGa+1GwBbbZAYrBAZmnXYzRBsecsYzFph6KMWLTVdK2XGgtoY8HgrNvGbhJjt3tWAonzUqlVCW1VIjEpmeBQJu739QxahO1CsTv6V9OzujuoJ0iq54YvtQhl'
        b'FnaEplbOYv6g0mDlsCrtEky7RNEuceOFUqtU2ioV3deWc2IwpX8ZLQiiBZG0QDieJrVIoS1ScPn7xpZiyy7frkAsdgKSoJmgb9ReS+vb0/qOtL6zxD1Goo9/Mr57b8Zg'
        b'2HDUcNyY9Q37cbsbzlJ+Cs1P6VCgDRzRuLoCaWP+4Nzbxt4SY2+ZiYXERECbCAatpCYezCGW2g1YTotZMoF/b9lI2GjkqJAOiJME5EiSUumkDDppAZ2UI8krlAqKaEER'
        b'NrNhpFWTMohlTehQjoKWcFrP7lNja3G4OLx37iC736jfjLF8kxr70sa+eBDOJHl6JINBEv1Q9JMJPBBJUoczh7PH3G94j3vdCJIKUmlBKh4I77kDQRLmPOgmxcZU+BAP'
        b'ZB0eSCFL5uTbGz9iPWo3yqP9YiV+2eMFt4pvldwql+QsljoV0E4FaBDxU4MIw4PgOeNB2MtMzYkg6xpOUOqzfEnAizv6vNv6vN5Yqb43re+NEYoSWffM7CUO8VKzBNos'
        b'QWKQINO3JHhPNlJ9ZzQqDHnkKLO0P2l61LTbvMe8QwnNcFP7jqxepUG9waJBDUY54aocZVYOYgN0G5tZKszxJUkHR2bm2FHa6z4SLjELkZqF0GYhHVjtda28Y+5229xt'
        b'0E9qPo82n4fHm8u6Z8UTc8f1bhmOo3+StEw6LVuCfk6LpFY5tFWOxCRH5unTodClJnbvmSc1cJMYuE3oo9GRIU5oTbY6zcpnNmPl041DthzFyTGFf93o57950GBQmGmI'
        b'SP/q4yVJBZUdpORwSOgRsyiUxWI5YbOf/53k32VLRGygelT9qCtaISqcPwEJveW/g4SeSahJPOjLGELkCR606+SXb/Lp2MmiaInAwhF/qxK4eLpPQvo/Cw/9Z/t5lP1n'
        b'+zlK+sme7Kcx7qf8M6tFSeGMHv2JzhSjzvSx7qrkMp9gCv9cn67jPp2fop0lQXAlsKXFzDcd/N3pf9izJahnXNZdzdypb9C5JX+yewB3T3GKZHYhFjXlJZU1Rc+BM/6f'
        b'9XEL00eN3Mnvi3+6izdxF7WnuuiIKSiqRiQk3y6nPlv+tW4SsHS1Py1x4zNnhiC1Age6KC+uIJDSFvmLK2qqZ8TN+CtCWHWU+rP9e3Vm/4yfhI8hcR7+CrH6/nRnXsed'
        b'OT3VGaMnnQmNCfsrc6DqzJ/ui3QGYarwU+DPNmrF+rON0rhRa9YkARzSnhP9YxJm/S/ICZpuagQvOhejN/+5Lt7Bz0T8/Wwj1ZHWlbtxuuAQUGhGef0FweFiVUp6V13x'
        b'5/p2d6YqNZQDjP+lHhVPqtDF+aXYPCS3YkVR+Z/r1r2ZKtQHdwvXwlgzlE43s3oasf4vKn6tqV4XlFaIiv5ct+/jbr9Bzeg2ruYvdXsqpN5qiolztp9qUGigGhSLOf/B'
        b'sHpbuOwPlVjPsxDClnPYioJYzuWXls6wjMBWLKVFciuNKVuU5+Gyp+SXiAiyfgoiR0lZUURVVUUVKl5UPmWfUZBfjkP0LC6asvp4phaM5V8uh/MvKSdY6aJqpAtKUHGH'
        b'J1DqMwz6nqlEHkmhrEREIhY8x5hohiUHntru1ExLDtWEGTzkTPLQjGQhGHeq61hrWU9EsJW9Qw2LIVna97EIoimXTWDr7rKrV2JTd8rCYhpenWCGCGIDxtxJsjwPs+4r'
        b'rIXwXvpGSsKLYH4jVr2h/TFTp4xpiTdKHMFxuGcKwOAJzneGQQzclQQbElOjn2zdsSjQ5qu2ATTOrcEoi+AQOAAu8tCNWD5GmuEK45OjCdpPksNMdOBU2AIbBLHxYCgl'
        b'iQ/3KehpUC5lWv5mYGsNRgMEe8AueEIIBhyi4wUx8clJcGeagyAetM1znFkPD+5Ljoa7nVmgcXmhPjgOTizggt65y9kU2LFWG7aBbu7/kBtLCTeqtBSf8EIR2zL9dXY8'
        b'nMYOp1jmN1LUm96fPXX6hB3wImgALzyHH4Qb04homoPISIGteapzo+DJEt/AAQXRJVSBZ8NbB1/5+rWxcZdD3W2+zSylDgO/BSkGCzcuFmi8uvEfb604ULQj2Mx6R6bi'
        b'jeB1K9Z7uTc4feScv3V5XnR+aJ7nW2/eUHHzrE3nh2mGzXWPG14qkCScMPJ42HwzOW6x0ld59e++tu3bTrvI0mLq+7HXNl5J5NxMm1s4xydu47udL+14LUes5tU+WFDG'
        b'+gqY1yZdEv/csrNFO+TES+ffcnvbZZtr3JLCwi/yv1uQAamiswn5KsX34zhU45h30cqTXGXmS9w1cBm0CZ/Z9y4Hxynz2QqwAzTrkE9+1uDQwmnZprafbXjgChhQDHCF'
        b'JxkY7k3m4PAzMNxgn5P8AwgckeM5savhBWEsGAbXpqFVseBVsjGtGwa7GJQsZdDHgGTB3eAi6UkcOAa34O1wXA40JMoRvkA/HKDMDRTgKT9n8mFriQM8JGRZTYcKITAh'
        b'+8y4in/8cq5IhG/yffyu5gxpW230x5JIdn8jMQD2F9QX2OckKYpF6RnQujZikVjEaIExBZRIeRE0Su0jaftIqW7kuA0dm31bN1uim01c6cOlRhG0UYREL0JmZDZBacyy'
        b'JElLqEzfsH3lBKU+x1JmbtUhErsdqOuqY/Z7yEbdfMnCRfTCxVLnxVKrAtqqQGJSwOzrVR3w7vIWL+6puG3sKTH2JJlzZW4ew85j7uhf1YveN7zHQ29FSVzTHnBYLunY'
        b'GcM6AztRoBQ1YJrBum9s2uXby+nlMNNnrAolUqdYGqUOQtpBeNtYKDEWkpqF44tvLZE6p0utMmirDIlJhszWHvfSgSQdETIr+w4h82+Cgy8rUeaWHSrMvwnDyfFO24tR'
        b'+uceVyL8bMibFkjLEPHwn3HqY6wfKim5j1VYFOs/51XlQ/1/F9R3ydNBfafWctOeuZyEkv/av51DtKq+WtmT8LybDH3epOwaR/PZH5+14zJWEaHgvAHzgRRNu5Klkx9I'
        b'YeOc5wTktcFI4HpPbXiVFpXLP6dgC2/MpSo0mQxM2tdIdKz+ZOzdP27gZywHSybloPIP5eDfGnj3/zPuF/8r3FdISCu5s9iXI8I0vqt9F7PfcqurhV9H/ZAipfUeWzTh'
        b'wzDkWf7WsZ6zobm4oqJUzmANOYNXEga3VP9J7v6T6n+dwd66/wP2Ym8v/Jn04R5q0j2BvGAoyt0TWPKwcYx7AtWgXaxFWM9GrH8qNNw6jupzmImucJ5hL3s9R8765977'
        b'Y9ZjVjy92LZIIMadyuBQFTbhNFHTkFtwzq4kxsophYp4kW7hovRVoUlsEQPYDLeYqIq0qoxAsyrOfZQlAC2axMz161ny7F4pnN8dc6gabNFQCxqUiGmJPCDHLLwI2yFE'
        b'hwk4Hk5KUgo/g03lBCuD7lVqxPASboVNlXg1ApvgAdgMdj0xJFKkHAsUwWl42IAxWD2GVsx7RSsSaqqxKQc2S2WBjhoGYfAqOEkWflyLGQuEehMmRtFGL3gQm70I4d5C'
        b'bK2jwGeBgVC4m4xxHWiI53EdwVFwMF6RwW8Pt2Xg248Uaso/5YMhG2zZoL2EU7TBKI3cjQSXYvFAHcO5/BgFSlWZDXaBXniMsXdtUQOdwhgnc9gfgypVwIY422E96c5i'
        b'FjjBE8TANtjjxOUrUaq+bPQmcRBeId2psOXg9RK6IsZBS/CCKZ0xvQaXlmGbZTgIm/gJ5Pu70iL2HD5oqsGYql7gIMDwjjGgEw7g0KdxsJmQnQkxwgtUhDvBEGyfIdfq'
        b'k3K9A8u12gy5ninVkyEQ/zMS/Ux8erXnSDQ/gQju62FYElXWKwfnabCT6xhsf74D2EjwNTG4pgvoYiHebDRkBGk/OFBLUMkwJNkq2MoCO531GVv5g/q2coZjboN94Bzm'
        b'uCG8Smyp/eFFN2zVhU26nANZa+FhW3I9O0okwuBnsDmLrcIyhRfgZWb2XNctY4AQg8BpjIUIt4E9RDxc2blyBEgM/xgC9rPAQbg9nPQvqExfjuFJKZiBvnAWOApb19Uw'
        b'CHTw0hoh7ITHmEfyFITnBmPiu0BiF8Aj4IX1qRRVuIGypCxD4T6uImNmfRGMZAiBGM20mYWr4VlG3MWlKXIgTUrBCdQjEoArQridlA6GZxOmQDyRSBfAkwTFE7TCw2Sw'
        b'KuUrJuFB41erYnRQJXC2Br/18aLhVvymK+A6xgu4/Nh4FpVmYAW2Kvqizuxhmr5WAZuE0ey4GO4TGM4y0Etu1sH2YDnKGxJ5FTZsAvv1s0FPjT0ebS8Uw87n48XBq3Aj'
        b'2KhYDE5mE2UTnZtKgATjiNke1kigicwjO9ADzmcqLgfb4FaiyHzsorAxaKJq3fOw8pjqE0C9Mnqt3FbKhJ7oXwQ6iNU81k11Sqw8dzsyengBg/tPwzmE+0ETo59gVzQZ'
        b'A+gCTWAv0YKMBgQXwJaZWhAx7zIjAvvQi94oo8yIJgNXKpEyQwWHGbj8HaAeHCSgjFh8jsMtLHCsDukI3ElfdjaDQUgpzFugxQKn88BWhv47YT22UH2iVzzg7jkFjgyg'
        b'fhe8Hsq8wyF9tDwVaSTQCS4R0TdX1AO79JAssyiWD5LPdfAUEWJ4FFxW4MXz0SRTyIfX45BS9QZ9zCTrhz2gHglaNN8JkRG2pquAfey1xWiSEezJLYhi+6eh9jHyhri8'
        b'n8D2BeoTcfNw9eCp1Uxh/GL0TEvtyUfKfnANa0K5Fsy3eloPhutx2aSbKeC8BmiG52sVKCHYxIK9FDxZ6y93qQDd6dZeInhOCZulUqAFHo0mYUD8wWZF2KZELQNHKSfK'
        b'CZzbQJ6IhQI1So9yqFDUyXPyKxEyYSRqAhHNKB2+CpXn9AsrQh5qw1ABaayNqYrBeaV6NauYi3aJGpQBdd9POSnPyaHQgLkYOluF0qEkS5Tz8uLGTTRnLkrYkzrRAiVC'
        b'pELxdu0iFbxHs4JVSGVQ+1ksaodq4dRnHLIWk+/QsGqn7878rBqwpKi8aOWKqnmrA57+Zo3fuHKfbM+Qc7LbOG3LZrJ0gypaqmGZZl6dJeF5+JeaNpY8tmDcRn467cds'
        b'34Rgeo+ARjQlmiE2qm3jC2JIrLnY5KQMuJGfEf2EnVPMBENsNTSdDsFTGnlR6NmKtxRgK9wsQCqcy0da4ol5rkm6Amh2QJK3HzSU+Ay9qyDK5FDU3G3Xr2UKE98N1snx'
        b'bzR9edV1i/otEypn983rXhH81dYw2117W1YHB1arn2pN+jQ6UHzPeHvWcf5+tb6TJqeyb4dtWPxy47Uf/HQHe9NsJr6+5f1wnb//+y3mn1kmj2tW+il/kuX/2yuNb36t'
        b'+/US6nrYuY+a3jzxyoGv7tY2nco+rnrYJxHkzslQjXSKyGuL6/7btvFvvtRJ/3Xvr022B2JT9fOUDXiW/T2DKS98f25d1K5tP4Z7JZ5rf/N89YZvvrH622yNdtEc+viv'
        b'BoNLZ80Nm2+YtuC9UpGb8c8931194/f3Zt2P/2W0++v+wSqVAu6mSJekO8FffbaueXnckNrSnJde87fNVg6XPjZv+XjR4eIvW9S2dv46O2T9J6suHIz7br9r9shdqrjW'
        b'4bMMy8w1jpVfnekMDvyiz6LJ87Tfl8ffWa/5Kd3/s83de+rhxRPjjY6nm4eWj1vH/X7IOPh4/sjVnx70Sdip1rqiXw5kSk3+8Unz+N+Uh7x5/VfthmyG7b7t9uzcvJy/'
        b'26fBdmNG6nzR0aMvhfLKXWBOfmTSy+UvDt/aEnhLvHfjGurxraT31iT8YuX50ZnV7z08WrWtqH/ueWtTyQWJDXjl1bLEkDu21eu2vD5ffal28ehS5Z2vr5be5MZpNvZ9'
        b'2L3/hPjg7Ctfdu9P/szX+cqmyM+vLdXfeXH0t/6mL4yO9jpYvi2NLTt7e9t3H3/W9/dcg5/il6cWBuq8Df8WG/Dq+R/2HdSvznvlWvvOh9uiKpxi/rav4sVrl18TnZsv'
        b'qn/7l4ncbzZuippdMW9uxW+5qz68t7DlQOEOH97iwB/WvbjgIZsnHvowYXlU59uvv/BYY/RO06+6/3Uk7rM3byaWP2re8V3Qzdro/YU3R1XWdBZEvCPc/0Zk4siappXO'
        b'fYbfvF5W81uw6ZXZt3/QOG34k8c6bd97Sa8/NPDdXrXr1s8JNXd+KdhwZ93Rzsxrv791ZfDxN1d9V6leN17Dzfiv7yD3muHDtWZRMPakxZpWwUtfjh+M1v+4+jfbT/oV'
        b'fWmTh487zwdlDGz75XXJ98Ivfnpx4Lv9Qd9/vvz1tRuUT8d5T/wkLtv/+XrqyETYA+7ZlonHVE5x0d+39m784M18harEh2oWtbM27E1f7Xj6rt/pwa8a1U55XRs6UmNk'
        b'/4qy5CfhTycmjKz7f6hN7D1r2mocUV8RmfkBd1X8jlev/8PT5358MdeXQd9XBpcx3DjoRcsJL7BrGQuMsuYQa1J/uMNaHaPwqjqgdwPYK0Sr4FngJAc9CI+BPsb4tzse'
        b'itUdufA8sb6vYKsYszNMquTQ2xZwDzgOeqb5I6TJYwsiJdIALsiht7F9PapzP8s4FfQzNuwn0OpsP/GFwI4Q8FQuC27DMRUZL5AToB8pCQZsGpvfg31p2AK/MYap+2o+'
        b'PDtt3bYBe1IeBHvk4RTBcDHYSIZVGefMVaLA3gRNlNNueTGxwV7t7DvD9l4UNs36Huy3ZoDho+EeBgNbDb1tEev7ZeCKPOTCXrhPNA0+22pODtzlSoyswXZwCXSoO+Cl'
        b'myc8zE5jzTPQIxXOhh3qSWidNc22fh/cTmx+U0A7KgMazDDo+3TE99EShswHakIZ5HQMm+6A0W2PBcMuxhnhOuzBtvejeXGYRUgfCxUpNQ02EGvOYgh9AZF6lMD/O1GU'
        b'EuhnO8CL7nCHJ6k6LpA7FZkBnndSwaEZ0sE2Qsa4vGL1mVjv3fAkvFABB8lQC2LBLvUnQPFVs+GRVHvSpAC8UI0IjAMqIP4o+MJTYIQFzi2hSJOiCrjzCUI9aApSKWGX'
        b'JGwgO9iG5ctFsCkmBl4Ssil4VVG5ku0IBkALQ4ad8cunoMHBTnOVWHbWenB8MgzAAGwQxYArcAe/krHyV8tkgyspRQxC8B6wcb466FtBDNUVQScrKQSeBRvtyFBCNECv'
        b'iNyJA5uwFTu8DNoYI/JL0eCkemw8Twm9o1xBr207WaBVG+5k8KL7NBHpscewQChQw6syA3BBYRYc9oYnNJlvAdhppU+O8wv60BvjIFrdMQDEOznoxbMPMgDJc4uAWA7z'
        b'TTC+Dy6dBvO9lvOIWflfIL4Zk6jY4GyMMobFRq+TexhW70WSefGJ+9E6liU4BPeurCJzvRQczJsWSQNlWAA7mUga6K2IMT7vZ2N34sveTLyIJ1DlbCti7L+uEnap12iq'
        b'oilpuXwxC5Gtg6FS6zwPjPxO3IQUI1gKaJG4E4jnMGw7Dk/DLQTXGYM665SyQG8dYilZnTahBf/hWWDLNM+CoUxG72xHjO9TfwLZvhoOWdmlMRP8OLhUOQ0PejG8pkKx'
        b'k2eB3Ux3eqPAFoIGjaGg0TtaC5rAxvAymf2r4DFwkOBBYzBocHrtdDzoE+DMI7wME3mqENBmNW0C23yWURyacFT5uZjNOKCbX+4qMiQF9FJwSn0Ks3kD2KELLxiQfuni'
        b'GY9dvJEcovG6JysL2ZawK5PcdAwElxggaQZFuhEDSfehqUjE9yKsByO86UFelinxF4MthLPJeqAbvXcchMNOCViN70ZZ1NFMhmdQqU4iX2hk22A/yjQI+lGmHVzYQMLM'
        b'nmEjclw2YXRXTx5ow6+WFJXIYYNuVpI2vEQE3Q7siebBAXg20QnNavzKo0ypwxfY8FId7CCSUVbOUneEuzgUonY/O57loanCcKoD9tXNcN/SiNX05CjrziXdQmv+daAZ'
        b'NMQ95WdIfAyvp3At/++dGP4V81NL6mkw6Oc4PDBfv9SerNpXc//lBT7Z141RfvIlLDaGRTl5TlAVLFOnByQVK8tsnU5mH83uzunJEbNl1va9bkf9xH4yvrs4UubkJo4Q'
        b'R9yfOpY5utKO/mLl+9a24mU98ybQhI5kDWYO5zBHMp7boNdI5LkgmhdG8yJpnpDmJUl4ayVpCyXZiyVFy6XZy+m0Ujqtgk6rptPq6LS14nCZPa+3un/VbXsfib2PzCdw'
        b'pHZQsVdJ5uROOwWMZIwVXc6hneJop0zaaSHtlDdBUfyFbEnhcrqwWlKzBp1uYIWzH1BULfrziKKKWBHMnyTmTwbzZyFbzBZ7dqvK+B6DGSPF53JpfgTNj6b58TQ/RcJf'
        b'L8lYJMkplCwpk+aU0RnldEYlnVFLZ6yiM9ajgl7daqRgfy7BXw1DJSX8gvEoSVrWrUQ6LoeOK5DncnQdtOt3ph1DEF1dvDFCYgi649utKXPEpHZy70/E6L6hLCZFo3dw'
        b'6lft1R5MuWM/77b9PKl9MG0fPEGxbENZMgfns1qntAarh1dJHUJohxCJQ8iPqNZBVI+gd1V/vIzr0m9Kc/1R3/oX0fwgGU9w1ueUDyrXr0U7+KPsI1UzTiYUOZ52DyiO'
        b'k/0jnDxWohz4R2u663rqJpQ5Tt4TSpS794QG5eY7YazlavWAQskjnDBDmDCjvOeNLBlXks5LoL0Saa9UGoMWL0Q88A5hS3KLJUvKJZV10iV1dO5KOncNInweKwQTPkhq'
        b'4S7zChwpHq6gvaJJ2TTaK5P2yp68GYAD4xa9mEgHpNEB8+mAhXQAZnVgBGa1pFQkqV0jLV1DF66lCzfIuSxmS6wxPvN9RAVzmjuP5oZKuMljS24sF2MPFURDyxxWb3H/'
        b'cuZI5u6LZNNulDdWO158Y73UPYN2z5AsWCR1XyQOFa/sjrtvL+hZK1aQefvT3lG0d5zEu1CSlCJJLaCTCnFb7lILD0RpRGeaHy7hp4yzx71uqU1KhyuWjZAnZwtpfqD8'
        b'TODWv6y/QiKIG5s9FnXDGF317lbHeTDPJPz4Mbex4ht+8swM6HMAOvPoVsGZFvTnyG85u/ev7t+ATny6Ne57BgxnD+fSnjESz8LxTIylnUvHo36K50kt3LBgmCEquLgx'
        b'nEMTGHcIyW0UzY8Tq8ms+Zgo8SyZjZ14VU/8HRuf2zY+I0Z3fGNu+8ZIfYW0r1BqE0fbxEls4mTOnhj+NhKXSGQxqThqZkn9UZM7vsLbqJRvPO0bL7VJoG0SJOSH285m'
        b'WmNSpEVmlJ0z+vx2cdMunoOKg4tHDIfLpC7htEu4fDh4eDQ3EI3QO3B41fB6ifei8dmSuGw6ZtEUp6xtJXZetLX3A8rYMpc1IvckSVokCVgkDVg0oUM5u0pcQ2hB6B1B'
        b'9G1B9LiuVBBPC+LFUfcd+b3WvUv6nPqdRmbddvSTOPpNzsQqqYMf7eAncfCb4FA8wdPZkAT1VvasvmPve9veV2rvT9v7T1DKaCaPKY+zbqjdCU65HZwiDU6jg9OY62jC'
        b'hbJiWOOzbhiNZ0rSM25lSRzm9SoPsvrUBqNGQs7Fohnd695b1xfQHzDiepsXIOEFyNz9Lvmf9z8XOBzYG45OaPcI2j0WkZaPNEZgyCB70Ouc2n17R7Go17t7bc/awUpG'
        b's46kjqSO6eOmLueO5kqSkm8HJksCk5E+GWENq91xCb3tEsoQGY1tXgpLFpMkSU65ZXQnZuHtmIXSmEWIuMyd+64+I7OGjUaqbruGIBKOZY4n38i6E5F5OyJTGrGAjliA'
        b'LsqCwkdq5LtE83NRKg3Po1EalEcH5fWyJTx/qUOAxCHgvoMAU1bivRCzksAlyxn5gMPi5mLTB5ROMKkSxXPrFyA16ujaz+sX0I6BEsfMMf0bxnRICh2SSW7Qjn60YxA6'
        b'tHbE4iZk9S5h/sp8g8fsJT6xaLKvk9p43nfw7tWW+ERLHBLRbzyU+StWvO/iLVbs0ZTZ8cTq+F+3+kQuBz8omYfm9Mjcd1WrVxYWVeeXlIruKudWr1ycLyr6K44p8hjd'
        b'05/+zKfVXGxG8a8/9e3wHl4nRdxT0DM/JobFYlngD6x/Pfl3faF9iB1RDqt6UMNaIWwO2Sp9WMJhQjzbXVU/u3gFBlsirwFH47WFkbBheiQ9cNCagYYZis8WPmV8RBml'
        b'wh5wTAE0G4rk4DoZsWHCiMDpFZTBnUy05XPh4PizNcxfTCqwXEwyhVbboLXmbrQ8juGDpkR5PeaKZv4KsL0KNhKYKngGtMzhYTd1bMhnG41N+VZg79/kaHnsIxaVN0cF'
        b'1zTK4Cw1crH9lhwzx3Q2Qc1hl8FNcGuNHbqvFQ0bhHAnvxiedgB9aaQuV0+5jSFF+dkoUeDi/BoBrmpULRrH1cP7q6hOcBa0ZzJtO0z7GJsNOlW0wS5VBn3qPMrV8Lxh'
        b'hcBuPK5S0FHjgmXPCLSLUF3gONw9vb50DGzkzAwObwIUb1BB7x1nvcjUKNEdzVYQqXEoSiX20aGMV5e9G6x3qLVogfa75039d5k3tr1w5JEy+17hnaLupKXR3M3COSt2'
        b'mISq1s3lb33Ftt0p67zqzeaU0IfWv/bnvHo72nqn5jcbzxVXv3758eHL1l+u+V70sWH3J5vilM0aXzbzvfP4rA/ro+SSb/a8+eVLcdZND9Q33Fn8kqc4x/LwqtVrb36R'
        b'P/6Detwvtw0CF2xyVGnf1fvbubYb+RGen9NjJi7vLm99ENUUbb3bxDvk4N40T5ewDGqn4dUfz7aW6F64NZqxeu9ev0bjjt8vTJTc9eFvW/bZt5sKfk3NyBDweLfPfXyh'
        b'8aXx1oM5MZdLnN8LP6ybPtQY/WFfZsaKV6oUxwfCXXmnV37cuaX3s1mjOi85F1rvED40aNzsczpy1qLulNTwapsthz+6Ouu64Fuv8Ll+X7zfGVr2k4Cuupqk/n3N2b7e'
        b'8yoRH9RbHT6VMTr3++rlJVuumOSfqU/+6rLj2zfTF2Zzu0LKrT9SU/L+7HTjq23eeT+efXHCK8Px+Hd1v3HeSbfKLDavvR17I2k3T+PtTcUStbc310rUf37RYqnCu2EH'
        b'B9a5rYqpOmO/1uWc+tWRunURhcbffT/WXmc95D3326+L9/Dc/MSvdlTOcjphvu3Ke0rGbyxtW5iX0NlQHv9umJqXVdZ+o6VBX2a+cq7tRV9Z00/HeOlmvSNfHDtUrdT2'
        b'7YNUq22RYoXijKDUevfV2hd/r30/PyZI/PcTl/gBydUXv4j++vfjATf/1vSG+tvDc4pPXrNOvleUfihpnizmqwU/3nwlL+TAQO7cLQUnPungXePefecxy6/W+vBr5bNv'
        b'5hm7fd6V8LMs5FL4Ib3qnPqmVw6IvjLu6BatWEjnffj1ro700atque1ZYZoHHmcUDHb+8uB71Qe/93y+LPJ87mhTYMr3Zg1XvD++J7P+5YMR428beGtcW+9988n7F888'
        b'TspT7g71vHM1X/BCP/2a4867JfwT9lvVVwnfeHOCN3ZyifOLD8xunh56Odz1k7O6/ZW/zDlslfNxTe8GyQLtZfYP7YcOfhF86uqbP+vUPnhH67XahUGfb3+4KTup6YP4'
        b'JUETjw+2fn7D6DdFxySlgmMbuIJHeK7awW64/fnAAFmgfwZohA96i8YaMNzcD6NQzMWR8iYhKlLl9xaiyobxJu1Cb2ablgVGV4IB8g7tnw5aRAlcW7PKGfAIoL6O2UMZ'
        b'WmSE91GVwVEHOaYMG7QShJYkAeh9xnCUMgcNAmI4qqdN6rf1tpi5iWUJBsEFBW/zCgIllAH64QVhIsZ3gDsFtawQ0GbKhLeqt8PAdwT5AR7Q0mNZB60izUbAi4sm3/nx'
        b'1204zMTMY5fDvQpgODue2ePd566g7hjkz2MClKJRqeuy4WbQYcTcPojD0qmDc/CiEO6o5LIoxToW7AJXvMiGgwLYvEjEZa3xkkNCzAaXSDEhbJklwh+mY0g4V4zOoVbH'
        b'BqezSpldpfPgHLgq4qo6gxGMrEEgI0TzSJVB8BhoVxcgrrFBj2smy98+QR5dD+MeiRJY4DIcke9SgUPzyI7ZfNif9gRaBHblEnQRTgQ8HEd2dULCYD+OL9tpi5UyiS+6'
        b'CeAQjXjfxhB2rpm2IwdPwstTwW2V1EnbZXCjFxyqNpkepSsG7iO7Mk7VSOs3x/M3wGtPQ0GYaJLSHq4LyHbTkAqz44T3m2zBHiI2AWBvtboPaJkWExF0rmH2Ea9WxorQ'
        b'aHaviMN4HRzQxwK7wQA8Su462cAGvH++E/Z64W1uDhhmgQOW8DCDT9HqWaMuIDEYq3Am0FeNGp6lx1kGj8i3/uFAJNiC92L9YDOzU6uiyS4EF1JJBWvgtgIcVXcz3AjP'
        b'J04Pq4sBCxkIo33OsHMGhpX8SQ6vYQgrPbCXwSdqy4PtGMIKtfPs7hIiN6GRoV4SbBaSD/db8fxJZMGNSWAzM7XOgVML1GPj4WAUswHMAq0ZHoSx7vAE3CSEF5KmR0PO'
        b'hTvIzWQktaMYBISCx6MnQUBWwR6yjauSD45iq6P+1KcwqPJgI6FAOTxuOW3LjESsY1EG6W5FClbzSplttT5T0IUNtsF22MKMXsWHvdhDPu9nw7M5z5pzU+Y+HGzMDfex'
        b'mU8HjS42cIgPtsEOJF2IRjgcp1ocG7SYLiC713ZojE21G1BNeHkDGqebhLlkKenCK2jSETTIA/rwLFGGHV7PAUqZQkmZu4KJu+yIw8BNLVnAHh+wW5nSyuK4LgJXHtkx'
        b'25XnAEEiBM1w01NNO8IGRTAM9vsyoRHPa0Ixri0RNsYJQCM8VEtq43Asl1kwgDyDUbAV4q/Ok7BhOWxrX7D1f3V38b8PIfcXdxefCuLAvGBYsp/n605eMMgW4hcYSmVy'
        b'D3F9FIsys+paNEEt5MyyeUDSlgg5lkUWZw66hNMORZmlw0mToybdZj1mHUoYICOINnYe9Lpt7Csx9kXv5x3hHeEyUyuC+jGYcdvUX2LqL7O2wZc/xfbrUeO2t5zp2Byp'
        b'c47UKpe2ypWY5N5396Hdw2n3GIl7yXjGG1mvZEnmL5XGl9DxJR1KEnNnqYGLjOfa6zVoO8wdFozZ3uCOR9KhqVJeGs1Lk2QulPIWdih1rJQaOMi4AprrT3ODJdyMsciX'
        b'Y0HseK00PIMOz0AZag9oyQTu/WUSQdhItYS/BPWET8dmS/KKb8cWo/urpQaOMp5Pb+DInFHjUTPaF8Nq8FJpXupk7Vb2PXzayo228pZYpYx4jgbS/vG0f0qHsozr1Ws6'
        b'WDemIOVG0NwICXfB+FxJ0nw6ZoG8XZ5Lvy/ZA5LwEsYUb6je0JLXed/CtkeLtnBHlOUK8AZIgISbMqb0shpQG/eSBqfQwSnyKlBGddrCBWU0t8HG/j69ioN6w+a3HYIl'
        b'DsEyG8eTsUdje+ukNt60jXdHhMzRGZWrO6CNiDs8j3aPpt0TaPdk2j1jkqT3EXNNCDAE3lMx956glAzNRiLJn/sWdj3qpF8yfISaRYe0hc+TMz/aIgifafRo0xYeEgvh'
        b'iOKo+qgW7SOcUFX0MeuIxDs2Jh4TWitYhug1+9+aFnIoW8eeBNrGt0NVZscVF/Ta9vNpxwCJY8IYB/2LeVHrhpbULpG2S+xQl1nb09YeEuuMEQX0L/2y+qg6OhlbI0nP'
        b'ABs6VGTmxH3CSebI6xDeN3eYoPQNY1j3bdzFiRKPcLxnm8kaj5YFY28KdMhckCWmTz/tiMCBjtw6IrriO+JlphYdqWLDAzldOb2Vt01dJKYuI3q0byz6+6mNQ69Rr5HM'
        b'gjvBYTuGsWSuvjIn7wlFfDxB4fS+f8j00wcU2zac9YikHRGkGTO7CUoD91DgMZiJNyCzxgxvmNEh6XRIVkek2PtAoozvPhjZnyPhLxxZNbqeDsqggxaiO14HEmTWjmLv'
        b'Xr/BVRJrIfqNRTJ/0YTlOvXq9i7oM+s3w1BCMjx6mYUL6qVtoMwnYJwn47uiftkGom7ZBt739H9ygjqlQvG9mLEzM1xqFU1bRUtMoic0KAubrlV3zN1vm7sPxkrNg2jz'
        b'oAeUuWEm3vaxd6LtvCV2wSOeHVEyc7uudbS56wPK2BSR19ldrNijIfMMFivSFm73fYNHzWnf+PG6W+twQC+fxfiyJxpNTyBt7TmiN2oksQ5DP5mjoN9xMHN4Ee0ZRTtG'
        b'i8NkAr/egv5SiSAc/UYymL8TlB7hHE572TJnt17RoFtfXT929uGms+65zZMEpUrd0mi3NIlTGhqDixvtHDxBKXA9mczufSv7V45Ynlrbu/aeV6gkbKHUK5v2ypa4ZE9w'
        b'KJeA+3xnmj9vpJLmh4yl3ci9zU+T8NNkTh73/YNH593xT7ztnyj1T6b9kxH9uAtYTNon7A0ftJU5e/SuG9OSpGRIgvFPFhVzY40kNZOOmj+oOKw1Ui11Cf9R5sDvVfxe'
        b'iXL2l/inSwUZtCBD4pBx38y6Qx3/O6D+oEYJ6+oJDlbijEKftsOlw5j95yv+E5+fP/dM0nlmh+tfeARReD+rb2o/ax32HzDG21H/9uTf5oDwAyYfOyGSa1C1GY9uC062'
        b'4uQXnIhxsg0nB7D7tyWHou4qy1FC7mpMB+W4qz4N/qLKGefGpt5V/8DJTpxos1Bh1Smv/bvKchf5uxrTPdPvas7w+CaeWcQhh/htEOpz5/6HP39ikXpOSKkpkTiigERi'
        b'RiyVYOxIUsUhfipPIkpp4IhSODFhIh7Zijkdxr1Fg2EjeiM1Y6kjy8c9JSmZkvkLJcnZkpzFksISybIySUG5xKdCwl8hs7TFgY/scdwjexyuyH5CoYCl6TtB/W+lODLS'
        b'jJbiODNiOUXhWE4xWKOj9BFJG8KRFjSy6jCQ6fAlOnyZHtaxRu4oi5H7I5w0xKIM+uYtS2U6jhIdR5keflbo+6IM+r6PcNIQhTKY2HSgVpwlOs4yvQCUwWQeymAy7xFO'
        b'GuJQBmPrDgeZjkCiI5DpBaMMxqG4Gyh9RNIGIcozvavhuKuRpKuRpKuRTFen58Fd1cNd1cNd1XMnGXSNW1BDdhIdO5meC8qg64Yy6Lo9wklD2FM14AedHnnEofQRSUkl'
        b'BhYtK2U6PIkOT6Y3D+UxCMZ5UPqIpA3RKI+hJXpw6zhJdJyYnhjinhjinhi6N8Q8RTRnTDRXTDRXTDTXZ4iWgImWhFtB6SOSErqZ2nZEy3RcJDouTB5TkseU5EFpQ/yE'
        b'yhwcL+yfJgKWpjVSQ88mSixNE3z0TKKUzcFxsP4T6bQ4W23aQtHk/lUwGJxykDeEvQpFYHPmDCNn/EJDvNiwCtyrQhzrcAylycAwqg1qxSpTbnYK/wmIh2d9rZ52sytJ'
        b'qInHI+0JyXZ38XDzcvV0B5fAYHV1VW1ljQheigqFg3AYnocX0av2BTikraKhpqWqqQ52gwawA+6Be1OT0Lvj/gxFCp6Bl9XV4dm5xLw5DL3YniU20s08jKYLd8NmEs8A'
        b'va0f4sAreuBkjTyy/GVwGhuHoxfZXa6UKxCH1BDbsdYSf1IKJY5wlAM2VVG68CwqCodViXV7PjgNxO5IdYIh2OZGuZUbkYLggm/NZLPgIkdeELcJ9zqTgi7BYLs7G7+V'
        b'+7pT7uAgPE0+wMxeAF9AjeFyHBalF77CFpWpsajBKjwTW166I8LNEXlQHvN5xNPEZjXcPjnEWamo1GzUUDNpyJs4uID6TK47C4f2EHtSnqBRiXGMOL0WNDJDc64AF1E5'
        b'NqWni4otCiXdA+21HHdFvOW514vyApdQ9/C4VsIue6YtZ3gNHmOKsXBrreAYKRgFR2GbO3po2MPj3pT3SrCXdFOfBzfJu6kMujEx9qEil1HJmHVkcDwzQ3dl4pd/0Yfy'
        b'0bQgPlzwgK4e00lla3AYbmXaCgbXSVPLEmE/GMKd7RX6Ur7wgidxIQmFbfCFSeJHgD5EDSs518CZDczoToMtAWAIsU3Dx4/ySwYHyOg84DVwGbWH2WXBRmVOIckgTOuE'
        b'zaSXseFc7IhpDA+HUqHgogYZmzIYZkzxcVFr2KQj5wDYDQeY5o7BAXAEexCkp4chqdwez/DgUCYc5BG55IDuAEqPAy9jFoBLSaQYHICdbtjLO84hnAqHR+HVGsZKTBjL'
        b'kBK1CE4ggVJejIQa0xJ0IT4RwN9rFDiH3VExSEEEFWELDjHeJA1ZSoSguGh7rbPybIakqYmMM1S7QB8jAYCz1pFUJDi8nHy+Amc8mUgPcsHEh3ga7QSjDFU7wTbSKmwC'
        b'F2xFiPdlYEsUFQWG0fhxj11ZLqQM2IQm8VGwEZ4Ho0gEwElUuAJcJk2blIJmkTLxyLkSTUWbRJGSbkC8lGEIKrnHBhcMmOTlaXCWkKncEF6HWAzSQVsMFcMDxxlPomEn'
        b'uF/ea9hcDg/xMJkIO5fBQWa43aqV2DqYitOJpWKjYR9xqQHnrPOm6OvsLFcaaB4PEq5ykCgQF6YRuBUiTYK4qi4UUkI0+HYiDmHgdA3p82Z4vgq0g87JCdkMOxkyNQtQ'
        b's9hP5gQ8F0fFgVNeZLAhoN9kUow2INWFxlw1yVisH7AArlmwAQ4hvq5dF0/FrwZtRG5nwV3gmlyQloMhXDCA4WsYbCM0EoDRLDiEMR5gfQKVoAS7GBodgV0BU2OlkpXB'
        b'0Um+wKt2pLM+iPBI5yKmwu2CRCrRD9WIJckRngQnJkVJ2ZLSVUsibFklJA0mJsIeOIT4qQsvJVFJhuAcmdB80AQbmSKheIaZOBCGsBcy/Oi1AXuwkyXcZpdMJccXEHqG'
        b'gkZDRnzqcUAZ1MEyT7AXE6XZhRTzZYFmdQU8n3JTqBRnOMp8bd4OO0ELYQQph+QGbEEUJ/P5ANjCsKJxjZE6m4T9uZRKpYJW0MWwYlXtlOgwigSJgH0lw8cdOaRZywh4'
        b'SF0J68SmNCoNjuqSZucleU4RVK7HEQ0GrORszGYGegrusVbH07NrUTqVbmfAeI61gyF/UgJsxu+ChINei0kJ9gZwWV2RWJKfy6Ay7GIIE2DPGpG8e6AeK9WWDYQJOg6M'
        b'FjiSDvepc7CADGeix8cWsJ/4cbmBXa5EsjmcWnCB0vNGReL8GIKcM4EvqCsT/Pz986n54IIFo3R64CU1OUE48FgGOEqmMKEmaLSuwXgF6TxV0Iz1st4CakGOEaP6RsAF'
        b'F9CMuJMEO7OoLBUB08xeeN4BNLPxh5qUhegpc1WbUXmnV6NnTRsaaHKWgBLkoQc0yb5Tuwi2oYFogR5nyhmHzmFqb4HtDqn46VFmSVkivb+FTBLtVB/YhuoWmvIoXhxo'
        b'JHVog/OgM5VFEF1sKVvYBjpIHeqGSrANK54h2OBCuaDZL5cMQyjGfmtUILzgRDn5gnqGdUcNweVUPJMEdpQdvGDBVSNzMATWL2aUIycZXMXkQVMQP7zBRXCJyHF0EVrE'
        b'yBciW8GxJ49cXaQXMI1tzUgGou7Qc3CbXE0yz5L+FcwzoxM/dwnH2RZogYC0YB95ZpyOZtxW91gyD3WcCjegsosZOUoBg6SfyfCAhpyPPLAfNCnDTZMaNbmMaeIcWlZt'
        b'YzoC68k4fFyJMsliRgou1TLCDXeHlZIW5Br5OthFcqyC5IEonz2zgRjNdrmseHszgnsgQXNyORAGByLlo8yBe7gsksEcXAkRwkYn2BjNZ1Mq8KQDOMsG9cGg63Oyjmyp'
        b'CuaqEUuWDUjAFebHc3CMsT1sbcYTcEhFkzIoHFakkvKcLlr7MBc741UpnaU/sai8PCfDUEPmIhU1m7Lx4CAByMs+pezLXFxfokCpeNgqUMF5TjEGZszFj020KJMAVxbl'
        b'kqfxgY8Fc7FljjKlkdbOoizyShPU1zMXoz10KIv571HUijyNuSsEzMVNfmqUXuEZFqWT53Rw7hzm4gotPcohTZONGlr7yQYb5qLMCLf+miK6GBexJpW5qGqPhpn0DZLf'
        b'PA1+ZgVFnLmvifQpp0JjJdS6icTXmuKy0yLJje4sVIWJFQeH1foETTBy8Ugg6mu2kyLK7dTnNo/6vPMA/u9vQaQBV74SGkkWhe5qvM8zpD53J/89DGJUycgaeAg/CCmt'
        b'jAqqAi3G2smc10825iHa+VErqZWgYZU8Jhx5cdkGDqOVtlzU4Cawb5qogQFwjbT6zrK5lFMpjekXEOrqx4z1VzamSjKmSvbvesYz/Tjx1CNvEAEUxg6RY23pr2M1ssXU'
        b'8/5DLzSo/OmpOlrZOwymUNG4rLuKJeWFRSu5HOLpWYXll9kwwZBeU3gbBI/LTFSQX55bUobjgT4Hf8tdDZXC7x0/bqQkzqnMb8x1UPGS+nn1kZBzWsNaU5fJCx4Z7Ftp'
        b'86lBjS3KSCqNsnLL8EZWQsmCD9o4Ii7qwevBx3emvVueGqV3yPDlSx/7JJjkfnwje7bD1pyll3NjhTGv2gZn7WkfvhkxoH8mtkflgH7hN6s49a3mVhEN++cZdH9iu+6+'
        b'8s/2v7a9MPh65dc/+ijfaC1e9cOt95efPXDtZefFiULnOY8e3s5VU+qu2Wm5pXFWeKPrjUat2TfybRqto2dFuUbGFXR1hOzrCDs8/8eE4Faf+tmVs1NvuP2g83ixeWXQ'
        b'iTueD2/dpwY2/9iwUsVcV/tjlQe6a2P/oXFEd/dH6h/t94kM2KV7o80nImCn+40hn6iA3Wcb9Cc8Hxhn26xvFt5YsPbSGW+PF14uyn4xPRuanPlYqXyxWdA/vildenrH'
        b'sm/L9h1se5z++F2P2LIDZ753eberdPmcCc9XD2Z/8NU3gc7er5bpftLo8lPYor8fMf/V8L2RX9CR1p2Bi9uyP7Q4E79r4HBRGH09SqPcc/Z7D788Fza/I335if+6u+3L'
        b'C0dymjWjuKqvJm1+71sT4Y99BWUpH2QkHtN/fCPytzSvr24uC3rcfyru3Y7wd1stds7e07B0f/pizbs3Tb+fN3cgy33km0+v5H9869Pgd7Yc3F1wJPzX902/v1r93jCc'
        b'vffDQyZe3AdXLr2kklvrf36ZTUmUDbdxznf935/f8egzxcpNb2y+GXKvMGZY0LD506jPWrk/rPLaE5seli46nLH8sJnaVzFHtsfHnDLVfOWjs06iHoNfhoLeHrhY591X'
        b'f/Wnm6e7r/92bM+e5H989Va+xznhzbB7P+/PfnNzdv0/6t77rWq76d/fevnBL1+fitu3t/JnnnUB7/2Ke+L/Cv7Yu+7O1ZMm314sCKlz64AnFhz7cft77yu77yp4p9iG'
        b'/7EnTKD3qogK/Q4VuM8//47P5dKE22X2DdrXhW//frgs4/z8u/P6cn7VFnm9sTco4CX2EtNv+z/5ew13pfeBH5bf3TWQkt795vfrTDMWPHB7S/9y5vcdTUfvNo4NueU0'
        b'/Vrz8j3WwKq/FZQfTD5r1tr1SeDrJu9cbXq41va7Nw+sPvK6d/NAZvn+QN5bHhM+dr6131ddP/FO/V3N6vevKX3Qc6gle43PFzte2xM3+vffj8+74G98IS7mpe8y3dOP'
        b'pf8+P2ng9zvVvIvFWQ9NEn29khYmPbi7cFGHzesVj7majEFKG3pybsVf4+PjEhXB+VhKcS0L9oAhFfKVeSFa8aJnLBPiRCEV7IlmoRf3E/rETMQIPXDbhBhfkCcMBe18'
        b'RxalDg9y2O6wnxghmIHt4CiqegheQi9JnDWz1ViucIBpF61ru+BhHlqI98diW4I+0FDIQu9HB30mA4YchLtx0KsYuA1/4lag1GvZ8GCB3HVotj44OOXipwIugCPYxw+O'
        b'BBCfHxM/OIyqdkYdUnA0rWHBRnNwjvGou4jqPTbNjQ8tItFy+FwiPEnGa8yvIwgdoBv0O2LHfyU2vOYMjzMmM8Ow00lIPIVQxVEu+ixwtBL0MG5G9QZgJ2NPlAhbsT3R'
        b'cbCXMUgYAXs0hdi/bdIsQjsJnHbhLAHDOlyb/3s/nz//ZV9kQ/2RZ9DMj/hy56AnT4HV047Jp3v8PkA+m6xNYFFzQlkNERNsHQMtmY5xR+oEBx9Z8XtFzJFH0JguObpP'
        b'7iriI3KXHJG7+GhCiZplgu4rM8fWApRDfuwZzEKZyIkKk0mVOSaZ5MdMJnKixmRSZ45JJvkxk4mcaDCZNJljkokcU8wFJie5osXk1GaOSU75MZOJnOgwmWYxxyST/JjJ'
        b'RE5mM5l0mWOSSX7MZCInekymOcwxySQ/ZjKRk7lMJn3mmGSSHzOZyIkBk8lwalgGlIv7mK7M1KJXNPPPhPlUHpw0RE9YTUW36fGX6jrTus54c9hONtd4/7I9y8S6rRXt'
        b'FS0c2ew5+3l7eB34A7hjC08625Oe7dkQJjMx74pujG+IaPGSzTHYv3DPwtZF7YsaIu/P0mvRbcnoKGxdJJ1lTc+ybgiVGaGKAzQjWA9I2qKEP0mYd8zpqBXnH1j5/8h7'
        b'D7iorvR/+E5h6L0XYegMM3QQpCOiwACKYG90RRGQoYm9o1iGogyIMiDKqKhgxRI152wSk7hxxkzixMTEbJJNTzAxm2w25T3n3GEcionZze7v//m8Ml6Ye84997nnnvLU'
        b'7yPjyCqO6ytcgvqD+vMH3QaKFPYxSvuYIWqSOb4CH8UJKgcncaJqgptkljSsbWEHDguxjiAHCUNl59hp0G4gnShzlSUd9+5POM5Xuk9U2IUr7cLl5KPio7ph1rg5fJSY'
        b'qrhuEh2Vu7dET+XqJbXG6I6ykK7antp+1661CtdQpWvoEJKmAshBkqBy85Tm9nhJEh+6+A9RrAkBOLpiVb/5cVFfhFRPqveQ7y/VU7m4SZe1b5Bs6I8YrL0bMk0eMk3F'
        b'9ew16jaSZXaZ9phKTVW4GqrN9ZTmSfWl+j36qMQE/9WF/qvcfWTm+KcnApFlx+00bjduM+0wRdS682WJspmyxJ4Y7EuAgSNx6pbarpiemP5ghXuYwmWi0mWihI0rTkFk'
        b'Te2f0h8mS1O6T9L4HniqnDwwTKMbet0+bSs7VspEMlF/xPF1fesGRYqAyQrnRAnrSWeEddX11Clcg5WuwfjqJAZ9RF3hLZBlon5y714v944ZdJd7T7lpKUmSurYlS5JV'
        b'Lq6dNe010qq29R3rETl2E7QeguvWq9utK9PpMukxQZ3v5iHRVXnyZGHS9CHKxh6/G3yUTFF5+fUzulZIpqnc3CWJQ0zLCUkMlY+vVEfl5dtb3F3cbziYpfBKUHolSFkq'
        b'dy+ZeXe4NFzlwVN5+0rZKh++LO+4Hq7MkyV0LUVVvHyHKD1XP1lVv6hfNBg6sPr86rsB8fKA+JvZtzzlMzJf9v7LIvnseXeT5smT5ql8A/pdj/OkiSp+yJnoE9HYm+Nm'
        b'yOC8a6a3LBT8NCU/jQ47FHWvka5R+fipBEH9U46nSZPwH5OPp0qThowpb/4fuCNaPTz9SLSOhqFGn1s6t/JvVdzKv22AvigCspQBGk+keQr+PDTa3H16Y7tj+z0H9c4H'
        b'KNwnK90n42gV1FX8wH7Lfrd+y77I/sr+ysFpA+vOr5Pzp8g9nvoZ8sZ9/EiP8vR9ZEpeRRyZLPp47g1VItGcK47Wsu4b3mcVr1z6xw37IqwP07Lh0+JIH45R0dp83sNG'
        b'+12UevNZk8FgMMyxjf3fOPxpVvlZiJx8lpYgZjAsuRH4NF0Mn7aD2UppwQIy1RBqVJEBMVKxmNROzigjFVt/HEA0dIY9xhDFWs9WG6nGLXs6Euh4edQnZIyPYFmLn4VJ'
        b'I1jWs4uY/5cIphoQai26dTKIlOkZwaSyw8lYMrI28KFILnPQyAASrISZ40NDEGb6JKdk4eiW3SlwIziuQ4Wv4fjMA0eLv5qbzxBhgfvO868efCX0UFdvVbPrtqCDDPau'
        b'lih728Ac1qsba8M6Xro1A+wWC3Pnv6jXUrj10UG7KPvN9hEh1Ic2+m0Ns3hMmu0cAAcpocP8YSRlTjTTNgwcplGUD7nCjRpn+HLQqOUPT1CUt4KDPKbW7MBc1zBjZpi/'
        b'rDB/xRIizte5LBEVlucuwUk+nsjqWhUIuxZE0SCc5ZlovlqLVzWFicNUVtat05qmNaa0pIhTCDKxVkY2Wzuxntak1rnPKB5vShM0ZTJp6el6Hk/X36NoElYflFDqOVyW'
        b'ieawKZ6R4x7+tFm6Gd2QKIVjwUZXoSAD7l1oDXezKY4D0wBs1aGVP5I18Ay/NBI2ZTAppjmD8p5EBlWc6XAQ2YzFW2eHUjwGgUfLANvXCtMyMjA0nd50JHFtY4qQKHSE'
        b'VphNxrhflF7gxAu2k9OKKRHuoBc2pC1YmmVcvopFMWczKN94oq9KMFWDZhZ95mKhl0+V4DA2VZAOhW9CTf0i+ue5K/hJdF6p7/5ZkDWr6rutf61hUSwdhieLxt10KmLT'
        b'TUzNMBCnBdFBf1WFz21o+ADbbSjDmWdJvQ8LONg0bRZYdM3/A8cEul5DUljZ5g90MJ6pyZY5BJK3sdbjg48OLEDXelF2zTdF2BD02P1u1izjauPy7FleFMXxY7R8BIi3'
        b'TU/MUpLD+LhPajrL4yRlOcD6sOMVIpqIcLfWbXvwuunLgpdTdChdxoNSZvCr68h9/TZ/teH71/H4oniPTLPJuZ/f7fvxzuuos30p33vO5FTCTCfV5Aa0KC2iFpmlE/Ji'
        b'jT9rUPwV//U3alv2QXIutcykQbHTGl36AbW9dSOtfu2CLSGwIYVAg4WgLgINFGxhpk7OK75/HjJF2CTyxisntmUPlL4daObJe9nN8629Fi8VX6kubTB690fbT5t+Njsf'
        b'lmO1fKPVi6v05N1dirBPTrzcEPJx1o8xMXdn56dmCxI2VtbVfP3VgwkuZ5e84FIddyXgtM6Qy8yQnPaD35QWZSy3uZJ2+e+7V9Z++5xv+rxvGQwziymOPMmkz35srlp2'
        b'zOyUzltJ+Z1BfreL/e5nfrmte+/kf4TFHFz6i6pj/c6DZ14qSI89+Ov6k8DqZs5QVkfcmh7R9zde0Unk3L3TEpKlfDl38YQHRt9n1wcxL9zW++iN3vxXE8xfnzHlVuA/'
        b'Hq33jwzS8RK/PSj54p5UN2Jj3lc/nTieaHxJ5nf/ZM15qG8XdePI0T3ifxRuK47i+2VOjq75+o1/tfp2f3J0z3qp/67e/Tz+WwX5HfdOLLyWlNIc/Lzy+3L7VyecMwo5'
        b'srbx9W/WeRy1qv3sk9vfXPjY2jr15JF1lRkdvrfsc69/Eahg75dcPmFwd48qdvD7SMMXhnp3vV7UZLDhlPeJn6M//6n/+zm/vFX62arv2C+df+/nmEj9725VzXvtgf8s'
        b'03WRsOdUyIfCNx9nf/cP3WOy+WtfqcqPerD4VPnFt2dct4vYmvjr+nuzkkQfVpl/uEan2WZJ3D+cjjG+CKxf96Cdf/Jbn61fVL/5bqzp0oafjK/mvPe3BY9iruRd6jjH'
        b'P3vf/kRRaNsHD1OcXusTWbz+aayJ69WgxvdeCL3w0/yFd98THov9mZW5YHCK5/c8M6JMsIEHQZeQB/f4gQHQ4sOhOEuZvlXgOaLBWD0ZXsBaARp/UA+IQVsYs8wFDpJL'
        b'p2bAbeBMMI41SReg3TMIw9bvB8eIEsMIDMJtQnrX2YPx5/RAF9jKYK6vqyKRJGi0noQnRJXV1cYmYK+pKTw7GfQZrdJBBB1mgUNwqyet+tkKW+AWO9ij0cIQDcx5sIUE'
        b'DulYFsCG6kXpoA9tu6j5aYl2tOamEXuJ8LFJfTc4BWRCBsWZybTyhjdomBqJC9hdbqZRk2AlCewER0ihD9i+gqSkIPfTN1wxnwmaYctkEnk1NSgPXcXzi6nBkR+cHKb7'
        b'fGd6A+wEB5YTrCcgNVfDPYWY1RJqCuEgvIGbrE9JywgEiM8zBANMeGhhLE3N1Q3wlDAlXd3Li0BfMbNQH5yhCzdVVwvJrgqP2Kk3VkTadlJYzQTXCUhnGtgzk4feXRTT'
        b'CtbDczzb/4MICgKo/ZQ4CbWS5clmWaf1N9m1n2ep98jSTAbb2H6IetrBgLK2r09SmVrKTV1Uto6tdU11Ug8FzkDpLWbjE2ua1kjDFbZ8pS0fn+CKV0utGje0bBCzH5rb'
        b'i+0kHlIdhbmX0txriBIYO8jcVFZ2rSlNKZK8zuL24rYVHStkQf3ZyrCp4hSF1TSl1TQxQ2VpJZ4pzhXPbAmTTLtr6S63dFdZuYiFUmbj9Jbp4umIg2itbqpurG2pFbMf'
        b'2DtJMqVsaVWXkcLeT2nvJ+aobFzFK6Suvd7d3jKf/qkKtyilW5TCJlppEy1mqWxsJSxJQpuOJF+i31KCTljaSDybosXR0gRpvsy1q1CW2M84niRd0ZPRX3jXI0ruEaVy'
        b'cBUnqhwmSA0UDr5iXZWdfaduu65UV2ajsAtU2gWKdVSWdpKgpkniSSonb4lQxjije0K3n9VfogicfHMqneZA4ZSmdEoTJ6kcXHAeT+y+ax2OZff5CpeAfg8FlqN/eOjk'
        b'Kk2UJsp0u9J60hROgbi6p4Qvze0t6i6SZfV7KrwilF4RCodJSodJqBlL2yHK1jxK5egkyZJkS7I7wsVT6MQNlW2TSNaFwuOGCsdQdBaxZMlNyZJs6ZS2BQorntKKJ7fi'
        b'qbge0souQ3GCuFBcJC5qTBnBuakcXcRTxFMeotZnSUMk8zqi7zn63XX0UzgGKB0D5I5h/cGoYVvuEGViHUWrNriuRNhmyYqPmw7aKLjxSm48zhHLlQa3R0oiVR6evVO7'
        b'p8pC+63pWI5BV4VHFJ3YAYnc7An+Ki9v8qzZ/SEKr3ClVzgWtj2kWTLzrlmyEOm8nuj+sLvuEXL3CCx6DwvbQ/roUjRWPb2k6P1Ji3vSUJsevN707vR+r0EPhUec0iPu'
        b'qafSutP67RQ4+28kOmFm3qrbpNuo36Iv1h+ax0CDloxccniED4+pEefGO/zwww/jls1nUGZWQxTL2GfETBlnHo2eaaZWclMuOi2ZJcaJDNCbrxcSDuh5k5QwoSnrVVO2'
        b'0FL3VRsGOtKMtdF9dnlu5bL77ILcytz7+ksLK5dUFleW/DHAB4Kxr51vlGbGXySy85M1JQLz3QcoOr8oWlVWYs4b+4L+Z4c/jUPPQ/TmM7XEPI3suZaiZU8CQ66D5GdK'
        b'nb+LOY5z5/8AdlxD2IgcCkgqwEbVDVmFwuk4SJBY9VN0TJEUaAEuseDmRNhT/OumpSyChBs3sPbgK9GHNu3sau5qPt68yviDYC/O9jfijRjPG3UUU+ULdKBpS+ub9DBh'
        b'jX7jWAJ+ksMGD5sn28jIr2QnwfYMIv9lqZOWF8iK5ZYRCssIpWWE3ChiRDKWl7AT/8tPic6gk7FoiXy38SgbecvVeKBVUMORFWVZaJxNwGPl6Yc/bRBhFuD/yUE0JhvD'
        b'eIOIlVH8VsE0hggrLcpPBIwYIPaWk2ew4HLudmrqdqvtOZzXKqlyP5103TvPNEREI4eIaMwQcVEPkWo0RIxt61PFlZJshZGb0shNPvwZO0puPesouUNGyYi7rh05Sqrw'
        b'KLHDg+Hph//BKFlP0YkCyShh0B7lRez/y3Gi8QPRGicGGbSX6xVwqJjoMsB1JGeotRmwDfYTYd8mxCW5nfODHlX+/obB3ClCcnK+IbNgOxP/lSPwm+xO+2aIdBm15zkU'
        b'qpnrMperRxE3vcWwH2zJAqcoLHJQwRgbE1yBA+QC7wm6Hq0MO+xEU9Kiu5DWrMDT/FVZfvAAPzmFtbyG4sxjMiqApHjpF2VsEX7mz94Sr5sRZQADrV5f88tW565LL9vf'
        b'v5B/UzxQ6fsPxjtdCz5dHln7cpP7Pwrrt2xZsOX5sz3fb138455lFvO9Xz1kUGc3Vdl99EC1VPBr1vvLrcpDDr6Z/7Ap6jYQrTrpPvFUInffihvffnJf9H6Soypr5l+n'
        b'vPjtA2ZK+Lx/BQS8fP1y68vHPjq1xvzLM+xFocLNP5d8qthb/UL+pevdFR9+mugd3cr5ZPeWfzG7e73Xv/U1T4+GHegAO0Ar388n2RFu8WMi4aWdiQWg5mHMzwFKIwYm'
        b'gmNYEmSWrYP7aHO12LqaeHUhOXA6Y3EUpQd3I1kM1INWWoI5Xr5s2AzOBFcognRrCk7The0lSFY7SQQ1nRS4E8lp65luk/JpyIhDBUIkNiXPw9ko1HZusDOK2LJrgWQS'
        b'P5mYqtnhDEd3cBqenU2LjLvgDnBFGwWXAWQxYCBsMk/3WRgMPOfV+JH0emKEF/zygqIlmHupG/GNrCZK9WqyFm84dq2RTZGN0S3R9VNUZhPExpKCzhXtK2TeCudgpXOw'
        b'wixEaRZSn/CRmY14lcRTYcZVmnGl5koz9/oElaU1usbCEnNjQR/ZTpDk0txYI1vMEAepzKxaDZsMEbuc0Db3npPgrpNAlqlwClA6BSjMApUkcGZIl7IkzFzQkB5lbL4v'
        b'bVfazozdGfUZKiOzfcJdQomeNLTNVGHkozTykRv5qCxdxMEt4S3RUrbcUiCtRAf6g8jA3JzWEqhb8XfcE+zfxOciPZejnbzsPl4JR3TYBrwQ1mgWwjXPsBD+uashZkdG'
        b'LDn66t/fvshAq6FxK1VIzWcUUPOZBYz5LCbVwmoxatEtYvYxRzqc1VPEtKGOv6k3LNIrYG3VG7nazWczqUKdAvZWqkCnj3MMDZaTmnV4PoeU6aIyvTFluqRMH5UZjCnT'
        b'I2WGqMxoTJk+KTNGZSZjygxImSkqMxtTZkjKzFGZxZgyI1JmicqsxpQZkzJrVGYzpsyElNmiMrsxZaakzB6VOYwpM0O9ik0ujlv15puTes7FaCcpNB/Ztz2MvYz55qgu'
        b'NjTpo13LCdW3KJhA0p673NdNzy3FUZw/+o3IyZqVNCOBu5Iu4pLEuiNztvIYZK8fsV3iAUL2pHqKDr/SJAjSvHzCYOlrNs7R1q0/f+PcymP+uGVsit3S4sri3JLiukIR'
        b'yWc94mmLS0WVOHrV32DMdZHluRW5K7l4fkZycS5i/Be3soybSzcxY8pUblFxSeHv5LfVdJTW5u2cQdK76CwtIov1DJwO1m+2GvkMnIrxhvUCfwY1jaEbDq8YkcQzYCPH'
        b'yLB8VRaqtIMrGK6brYeV8bA+neTEwNl3uHpGRgyCThcLduM4DpLVJTedHcsAJ51CSWiCCHbG8nHKjH3CdB6Q4KxYbcw1UDaPDui6BHYU8VPT/f18rUB9KonAs/RmwYPw'
        b'KNxNZ0DZtTIB9uUJg1OZFAOeoeAlR7CHTmwkngyOT4Qn0KaYxqCYeYygOtBF56i6sSpV6J+aLkhJx75mHW5lTMSltMBzJDrDDsrAc2SrxHjRDWmoznQgNYGdrMnwsh5p'
        b'YFGBrRCcSkZk4RaKQIupO2suHIBHiDM43M0FB2iNYEY63A67sW/ZJfRQh+FZGhavcT3cKUxJ98U6wzNgExNbAphgExxMpeOvjtqBeqEmzZA93IYzDYFtcXS8wt7olGF8'
        b'f7B9FgteZ4CDHBadNmpT5Ay4A3bSCZ1wNifEivWSIkPEP3UM52xixrKdGaA735jQs3QqaBVq51uCbbVmLGt4FDQRi9B3RticM6POOD6nxMVqBZ3ByQ8MJGdhxqSCcqVc'
        b'wYmldMa1qbjqQ1xVwFkfhG1TBPmovhbuKY8YlWCJTq+034ZcWbIAW7XqLQ2pnJIfV2RSdMqf8wk4uxOd7gnutWMLGOBKjToqDj3aIez89yTfE2z1Ivme0DggXbUMSMBx'
        b'OuGTuSWDIgmf+PA0nYGnBZysHZWSKQW2qLMykYxMu31p5/7jdXAHHi9EhA5gUotBgwmUshbBc/rFf1cm6YjwpvOzfdyp7JjpMNAsJirj7fMmn9ZkmcVtf++m6a08V2VX'
        b'YkLaV+DvGYL6sCz7V/Z9aLDrS2G71+b5JyrvfPz92pp1r615zHBKK+h5veHTrybdZGy4scLS4bKOTtTl19I2zCpJfO3hX4Ir9v1L9+DbKeD9lRHTXxbdK7Q+8tac7VX/'
        b'eKXD7xP3gG9qr91+Xbr56NWw14Db1BcYRdtenel/+Eurge3vnHztakBfed2ejoxtlmEVV6wzOv+RCT/PXJxUKE/1XD6j8VT2j8a+q8zv+Rr5dvAPRnX3ZHZ9wT32luPb'
        b'Pb5vfqEzsXPuBlnblYrD8S0Rj2+am6ZUf/hP7/gvb570f/TaC191OFyNcDncJ+o+9jipdNKbb3ZFLjk3M5xxapruW7defOeGdUh+QIh3W0r6G4+Vyhe8Fr+VcW6e+amv'
        b'fwlPn2K4eebmA+++8+iQ8xcLvvv4qzkH7rz/l8lHP78SQCXGfroyc0pcqfDU1ENvl6b+uk/OfFDdUGr55srNt6e1/N391tq/zLt09N3Lrw6mhw6mL1Su7L7wdkmv9aWf'
        b'V7fX27CPsg+JFnyWN2fenrf/svrSqS/mHKr8tNrz3aU6Vu8kPv7B+POlZ2zrG3gOxFIQt26imj8VgH2IRQWn55gQlhcx0PCkMM3Xny41NPMoYcIenSk0M30WdJXABiTm'
        b'YMuJNRooaMlqYK6Du6fTiQ82LrE2RKOIl14FD6xUm9GtwQ62niW4QjIKgzbE9l4BlxePBz+Hze25foSMjCq4H6cHQnMFzVwZi4hTK2E3IaMEnIIXQUOAeunEoPZXbERM'
        b'2J7DJw8XBk7ARnAmiHYmrWYkeIOdBKgfbgViHMQVgFfVGnDYl15VbeBhdiTohTS4F7gMT4BDoGE6XlZngF5WCWP2hA1EEjFfjOGsppNFFfRasmAnAzV4AUpp/LIjcBda'
        b'zKYPr65cV5NlrAhw2JNA2luAk6Ek4RFZWwXwJL28WoSzQJcfvEqEA47HBHQ9WV3BFWuywFqsYYFL7mwa0up0ZAK5PVldiaswHMhEzw2OgU5aVDoevx7VoJdXJmW4qtaT'
        b'CaWTYAftEnwdXIAX1dkChOAMnTDAD24D7cTPFjatstZkkyWrYf4MU31WJTwAT5KucXUDMlIBrUl+aMXi6DHtc6LpRAJnwVG4Hb8UvCTNjqYXJQt4FAf0HHKnE4fAzvmo'
        b'hjoJnSHo56PBAy+ZgAGa+D0Wfqj14bUfHOeZJLKm+sP9j4nnyHEodudn+I1M9nbM+Em+t/gqXfPlQEaPxAF92I27W7MjC8Euk6WsSNAKL5AaznALBkidTta2MnCWXt4s'
        b'IljgWqw9qVECuzYgcpNT8FPtDKEnhIUJC82QE+k8kz8JJAPb1Qm3MgocQ4oOdWZqRhFDpSD2SY3W9SVLnak3e1iHKJ2isOQpLXlDlL55MoMYIjTWiAkd4Z1x7XGyUIVj'
        b'oNIxEJfgU7HtsTIP2jSBbSvxjAfOPnJerMI5TukcJ7eLUzn6SGJkVgpHf6WjP2kOV0tG1Xzl/KkK52lK52lyu2mqCa5Sr46FYnaLgcpFIFkny+736VuscIlWukSjk0bY'
        b'f9i716fbRxalcAtXuoWjk6YqJ25ncnuydFbb9I7p6IT+2BNcP6mxrODMshPL+lcr/BOU/gkK7mQldzIqNFa5+ksnyCrP1J6oHTRQBCQqAxIVrlOUrlNQoclvF7q4d9a2'
        b'18r0FC5BSpcgTOBDF3f8S2U/odOu3U7qo7DnK+35Yo7K0v4R5WgepLLlSqfKbX3R56G3v7RGNcFdOrVjsWx2f1LfIrlTlMrJTTqxIwP/mqR08nuky/ZxeEyhg4TdYTRk'
        b'QvECZKuVPpMG3ZQ+Mfd8Eu/6JN5MvGVOG7kkxio3ntS7v3qwWBmeLHdLUbilKN1SJLoqflA/T8mPlugq7XxUPmH9eagJiW6HsUowadBVKSAFPJVvYL+90jdqMEHpG4tK'
        b'TVWB4fiuSjs/uZ3fs1Cr9TVS6eSPf0conQSPjHXxQ+iqH8KMsrZvSbtnFXzXCqd/CFCGpCqshEorodxKqBKgEdWSprTiPXT1JF3s6NIZ0R4hTaXHllhPZemIOzIUd2Sy'
        b'3FaAPg95gTJb1QRPaZFygp+sdlCnb4PcKU7l5CGdje6Of89TOgWgrvTFXemLqcA+3rwg9Lg+UYOTlT5x93yS7vok3cy/FaTwSVf6pA93Ze1NfWV4qtxNqHATKt2EuCtD'
        b'+lOU/Njf68rg/klK35jBXKVvPOnK4En4rkq7ALldwLPRq/19vtIpEP+ei3oV9SZ+Dl31c5DezLhnFXrXKrR/7mCZMixDYTVdaTVdbjUdo1bxUH9mKK28VXR/itGPlq7D'
        b'iIZseunfgmxSm6dGu3aOv9S0YGWImBpWhhRmP6My5L+uJRFhUa5DP5g6a5JAsUb4SGpSalsQIW8ttVxTNJxjkckkybNxL5Lk2XR+xYqqEX0QXZK7Mq8gN/YR6oOKHlyO'
        b'W/3RDYufwyKrBsWJ61NRmFvgV1ZasprnX4El4z9A01ZEE49xX3eJqHhpaWHBM1P2GFP2DWMEZYSssiIubiq3sqpiJGV/gKhlNFHsJXnBec9M0feYopOavvKZWpK7lFtc'
        b'xC2u5BaLkLA+OXiypu/+TbpwZ1U8pP7AC/xxJFFOuJvyKwoLiivLKrjFBf9JB1V8wf4DhPyMCTmrIcRZTUhuZXFZKfc/6ZOl9LvSX7KyrKC4qPgPDCGcXLrCXTOEvDFJ'
        b'JbmiSi7dUv5/TtvWYdoKawvzqyr/AG2skbR5aGijW/qTOk2XBkt7drI4hiNmne/wGK/UWhfQYKdb/Y+JKyjMQ8P0mYnTH0mcC1kSSBPc3Pz8sqrSyn+XoqLh9zg8dZ6Z'
        b'JqOR79F1xPz7D6laNkzVsPr+makyHUmVp7ZWEb/KYZXiSMq0CHtipaymsC27lapn1rPUrvgUk9o5Sp26jkGUrNQYJStjjCKVWs9QK1nHLftjrvicp4QQEKoZdAhBEeN/'
        b'G0Dw49wxilr8j0ylmmWFqP8r0EtAs0hrQlWgSV+BNttKLho2pWWVY3W9Y/S9mrEz0qi/88i3lAgLozWe2w++EnGoq9k1rLqBwSFBA14NzI+yLvEYBG7bEcgWqVUFWE8A'
        b'z0HZsK4ADiagsWY2PNbUbNRljHDpMjzWNCQ/8bwvWlpYSQQ47CSNearlcxmUE7cjTm7lq8XisWkWbyR3hzGgiH//H7iXJRrmoqWU2nUxfy5i4CwwJzb68KeZr64wn9Hl'
        b'g6pn/E9dPsaAwo03WdDosJFMY4n46NSuwstPXD6K7d1ZzRLs8LEx48Vau2bXba6STed0qKZYnRd3K9FwIcqVY2kO6uEyM19bsZSU9NseIRXXf/dditTjxkE9birQuPHm'
        b'SwtkYV0relYgeWG6GP2McAohQ8iE8YxOIc9EgoPhCDeRVXg82eMB9PTDn+omok4YZJ4KTgixag+chF0U25QBekE/vETbB2Tw0GohPwMVXoUHKHYIA5ybBo4WMx49Zosw'
        b'2t4ryfdxMNGm5q4tvD1B2wa2HbG59VlORn5qLvNsBct+hd1yuyzJx4E6IeVFFPX8Lv2ps6cPT8rx5Ck8vp/04ifoUGc+phfJq0unX52KrTeUM5fBNucPUeMcTBjmOJBz'
        b'/MNDroesQG4bgj9mISMWjPHe8TPRZoHf6Qr1sMrFb1Qfv7hxD3/uMjHuvkSWCTbZl9jEdkqpPX7+N7vTMrQ7pY/ZWhJxwJSIZvPQXjTSbiniiiqLS0q41bklxQW/Y4Ic'
        b'z8+Mk5E9ldiAQkrqKD3Gw3W6FLdaFbCRXex02YIpwtO48aUHB18JPvTgTlezJ9qpdrXNtNuS4LY7sNGtmrtP/zU8dl8NgVXlzNUCu2/KG5kTC15fbi+xi2xbgf4fYPx1'
        b'4Z7AOT3bcxl8lk2/Uf2cEO7jmmD/HPe+09u7djVscm2Y8OL03NeKEgZNP5z2WiUV3+rwxbc7eHpEBaoH6l34RAGKtZ/wEjyDAbEusqaBrepk0KvAxYl8jSI+GLbTNsxu'
        b'eIXodD3AsVKhRmENpR60NbDZlCic2eCKD394gwWHYYPGxLkpWJ2k2qNGY20EXcUMClsbp8JNRM+/epKA1u2y2QvhNQboLIJb6HAHSb4lH+6cngL62BRoquSUMN2CIe3T'
        b'AzYnwx1CVCLgUGwn2J3MAARujqfzdLUJdvzScrnRKxYtIe/7CWc5fIbM9Xb1fJo8j0HZObWsw7OXq3J0kYSqbB1b1uCvrtKCnhXkD5UjVxKGz68nX2UefX5Pzj+0smtJ'
        b'l1sFSrN7FmBP/wniSEmu1E5h6au09KWr2dl3cto5bXodeuIEHCyQ2pTamNaSJg1SWHmgSrLsu5ZBcsug4duIK0c4zozDaYzrN6PlcVThz9HmqYef3AWvJNXUcDzwU5mN'
        b'/xbvQaxG9GNZ/g4mN/YWqsCgXvdZecF5FdisX9Gog1/ssAx9X29YYr3PoYW5+xxalLqvNyy+3NcbljvI4kq6hWf8nxsEjKlRqNl0rz/A3krDjiP7sG5uPnMUTjYT42Tj'
        b'A4fGyQ6RVEp85caeCmNPpbHnEHMew9hriPr3j49YlInXk5aqmSNAnCMwiHMkxnCOxBDOkQTB2cZZPFdlxpOb8egKNriCDa5gE1k/dRRONIZ4tiQQz5YE4hkdCVS0dp1g'
        b'XCcUVwnFNUJJBW2I51AM8TwRQzxPxBDPEwnEszaQdAwGko7DONJxGEY6jqBIa1eIxBWicYVoXCGaVNB+EAycbUOAs20IcDY6kmfRrhOG64TjKuG4RjipoH0XjN9th/G7'
        b'7TB+t92kMWTgxAp2MbhCDK4QgyroGRiHDlFPO9gQLGw50VhLJ0kndUX1RNHf6lOG2GYYU/oPHGg8aMzZZsN94AQ8p7GkGdiCy2AvE1yNKB+xvVmof39bjgbmfocxvmqc'
        b'FvsWqo850qMK7fKW9VZIGPgT/dOw8xOSxfW36qn90RyIj9ao9omPlh5NV5/BKP85zH0YIrrYBYZj6NJ/yjU6SJI2GlPbQP3k9n3GI+kscCT3sCR3Md2qP+o6Q3Idha9s'
        b'0UU/9n1mx9AKc5IzXEMf/RQ41TMI2jbt6GVcb1JvVm9eb1FvVW9fZFxgOaZVo2Fq0I9ei34Rq8/qGBJGTmpAEwomEM9BHeI8ZlhvhFo0xTTWW9fb1NvW26F2zQqsx7Rr'
        b'rGmXtNqi22czpl0ddYumpDVb1JJ+ge2YlkzUvWs3undRPzEL7Mf0r2mBCdE0Ot83US+O6Ffu0sKK90PRxSMYsgTuyBqYi0O/RdxcxMBps3XYQS23kptbgbX8q6qK0Yo/'
        b'oqGisgq6fgEqyq/EWrbiSm5lRW6pKDcfKydFo/zYUioRm1hWob6V5i65Io2qCfGXpdxc7tLi6sJSdbNlFatHNePvz63JrSgtLl0aGTnWUQ5rsUY9oIY9nZyUneDPnVJW'
        b'6l3JrRIVkicorygrqCLkuo50M2TS5iUJcxSahsb/HUfw0675O2jVF0bTwF6GOhoMDZ3/OoZGEY/5/vzRr5h09ihHw2FefeVwp/xbvoaad4KVVGhgaL/IcbVRePSQl17g'
        b'z00hZpCCMkRRaRlWYheLKvGZGvxu8tSWgMJx5Ac1QWpNKU3TGP1pTTEmEpUUVaHmcgsK0EB7Ck2lBeg/N7e8vKy4FN1Q2xbyO8ILhxorvBhnVGGEDiu4OVQrP+2cZI2/'
        b'GGyCe9JIEtmZyWkZw/nm4D4BuAF3GMKjmZZVwRR2OupHEsPoFp6DPXQr6Fq1T0g13KG/Dh4E54i0vx5eF8FmPuiEWzL8ktmUjjcDSnyW0Di9++Eg2ISBQmtr0qhauHUe'
        b'cS8MDCnI8oPH4Fl4NJhi+VOm0VC8kOlhvLjKhyLg1NsmYiQ/Puws1eCTYM/QGTP9ZjOpcJ4OaKwDAwTydym8OImPpogo0ZEShYDrRIq7HMakapdiFi6n5GFAAUXy98Lt'
        b'sR5qHzpwHQzgJ4L1aZk496AA7k2n8/RllunCjeAoPEpDfZ+1WiRahSYc2nvbwTEK7MqyL874y6dIFkFDPvRDxv6ZAxkw0Ora0pcyXmduK73982aTny04yuMNvdwgsx63'
        b'FoF1w9U5i0KSkv+ZcvjEi4/Dpvbsdfvoi6s1Xy++Fq5be+jIghceL9Klphkz/KpqhbdnbSiftW/FN+WLvesFZUeLlm578S9hGeHvJDr+KONmV9dnPfoi/ZBJroXV2pnA'
        b'827Vzl2pJ6YNOLyWcqXjzuPmqCt9n+7d15dce+j2QHxjiXLH4tzErdZff/PLpWTJC9GvGu7L8/pl73cX33vpQMZbd5ddXHW79/1LxrLDRg/f+enOqiMvDS06/vkxUezn'
        b'M59zyrrx8tW277469t2nP06U3fzkdOLikPZfun+K9Vhd77kqf96hN86Vb/cuWBJ34eSM8Mo6niXxSQpF7+s6aNT2dQX7eTRuYGsKaFf7oz1xRisPZOvVTSLiZRDYGEr7'
        b'moJdsB/7m2JnU1hvSmeABFsi+cnwPGweDuQAp2HXHKLt8wNHwIDaTe4qPEJc5bCjHGz2JmJxPtjpg4M8wFlw7kmgxwAXyIgQajoPbMK5JesF/ryp5hxK34oJuuClPCJ0'
        b'T4F9aEg3IH4rAw8ZX8TNg/Ol4BQrcyWg80jCKxHwMj8gCbTCXZgj4wAZU2AAL5LC+bBxlsZHb02e2kUvYPZjPC3yMz34qYKEdNRTbFcGOFRUTUel7PEG+/j+YA/YwUNN'
        b'qgEC0Fy8QVThdVxwVe02Bndi1yuhH2K6wcUUU3ZyWjEtVp9DnXMANAQIPGlHKY4l0xjIConfXSE8BjbidJFCnI4R06VDmcOjAtDKAvtgz3Ra1u/krMTuX5plwiSLJ2Cl'
        b'W7mTl8GJnQkb0iLBNeL7Szv+WsJrtN/adbCJR3BPtPJmrotmL544nPFz/3xwFNGGw7N2Tsc5eOFexK5Ts+pY8AY8DJp5es8snuFZzlV7UGi5T9iO3HlHOmz505LaUAba'
        b'r+xcaA1AMuOBg4fcc6rCYZrSYZrcaprK1rllAy5JoEviFA7xSod4uVW8yta+paZ1Q9MGaaXCVqC0FYjZtA9XdHu0jC1bqnCcqHScKNaj661vWi8toCOjkVyAWlNZ2bQK'
        b'm4RStsLKU2nlKbfyVNlPkFhJlslYCnuBEqfSY1hPZvQzVXYOnXrtenLX4P455xcoXOMVdglKuwS5XcIQC9eg69HHR+T4mBp9/mlHEuL9lKKH9o4dtp3O7c4yPYV9kNI+'
        b'aIjiDPdCxGCoQqsrHo6lPB5T7sztXNq+tK24o7izrL1M4RygdA645xx51zlS4RytdI4ezFQ6x0lY+DniGfRV9PEROT6mRp9/2lH9HOMVPUQvcI00/64tT27LI950cQrn'
        b'eKVzvNwuXjXBlbjIufKIjxTXm/ixufF6BPfcJt11mzTooXCLU7rFYe84MfohAKHA2TlRjwX12IlGutCUgY5/MYpLsmW9YMtOctR9wZmBjrTGQ0/LKwizbU+PgiLhhiPC'
        b'oH5z+MZhrc46ShOpvmYeg8FwxZqbZzn8acqdd6k/5FSjtlfr/KZVePQjDxuHcwxH+PyEaNjAsXyfFo/3HzkBEXeS3t9wTHoarfmG2l4lFTacUeFj//dm6meyvP0/Z6ZG'
        b'skXFReaoznyKRdncf5BNLHMfXJyntihje/Lub+0jXqe8djI/GHqTxyA+0osCa7B798Ex+xDehTaveZpJ2WvUyxfllywhIG6/YVleuOA/siw/4y2XjjAwCxf8/9fAPCZW'
        b'/CkGZv+Wm0xiYFYUfD7SwDxsXjZSqA3MIROoJled4x6b1aPHzw6Ix+FhHJai0bMYnnsWI/OzvNbRtua8Bf8NW/MzUlIx0uScu+B/b3Im4XStDnBAKJweC4/6MWiTs00N'
        b'iSyLR0xxl5CfMQ+cwiXY3jwF1hd/vm8jk9ibk5tEWvZm97UjLc7a9uaLFPX8Mf288P3Pbm++gXvS7mk9OdrsnLyAoY/tzOMcbP5rZuffJrFI2/qcsuB/Z31GSy02Ao1Y'
        b'SjTarY0UbYRWR9Jy6hn1uhrdFnMc3dafv5xgN6ljY/Qx0worubnD/Ia2vvLpmqyVFYVFtNZojNvyOMqmisLKqopSUSQ3gRtJ4o8jc9SvLodblre8MH8cx6vftXDrZBAd'
        b'jwE4Nx82RCxWmxFmzZjjN3vOqIBbOtwWCeX6yxeD7STeFu7z9xOO0idpFCdRcDPRncw01IV75oPTxcDxdYaolMLOLMYHX4kky+vl5qPNfmhHPhAUFNhXtPnRcvvIeeYV'
        b'hnb2/RsdthfGP3qj/HJel8XsrSUG+d5Ca0dWe7vXVOlf0z6JXIGm5zlJbrT05Nyckq3LJkpm/WUJ2FOga3nl07Ddzxt1vMYrpupes3lgFsTj0GbnTaAVSDS4D2uJwqBp'
        b'IpGwp9mCFo1UTmTyArCZuW4eOEgW9+JasMlQCPdh4XqEtoKtBxvBdSK7p1SvGtZxmE1hBNnBzbTj0aZyuENIxObIMCI4G85nwtPwCtxBsAy5FJCNG20XCS6y4RlwIP+P'
        b'IE9oAeYZYugE9bCqcxg1x7XKyEJUq57ldWg7sfMQr5VOkXn08RS2oUrbUAzgNUZyZZgLaQlw8s1shWeKwiFV6ZAqt0pVObhKvKUebX4dfmJdlaVDS5TUo0egdAu+axks'
        b'twwm8LkxCodYpUOs3CoWCdUjwifUghKxAP+22VuPehIqQa9lBdju/RvPWYNXs7WazWrFgj8SMPGnLW+ip7JIdRTNTasBdSi1HPA/88D78cK4K1rlWDflsqLh4P7//gKX'
        b'QN/zGRe4p7B1f20oYooE6NSv26YRsOrmYgZrovzlwd2Nm3LD3HcveXVG400o1vmY3ujfecxZI+nmMYlyLDsV3iAwZXBfui18btjK6gAPsevAATBAlo8ScAL2CLlo7VCH'
        b'dtJR8+BC5vh8n2YDdmI+ZdCq+5pMTjf15Jy/kEE5utxz8L3r4CsLVTgEKh0C0SSzdW5ZLzfz1Eahfuo0onGon4gTv3f/HXjSrNRMGuHC35w0f9osicBPwaRxY3RFudWF'
        b'S3JFGSOMXRp7B8lrzNYYu2h2QA8J0lQR539s7sobz9w1PIewJbFAnUf9mWZQgsbqWViZi8MpcmlX65Vl1Yi/wLnmh9v9s6YffY26uyOxVYzYOwXYFLaySlSJTWH0ciCq'
        b'LC6l40+w6mVcWxatjhnhro/Nnajx8exompmPaa3IraG7Cz3zv2H2MqA5Gq4jTtI7mp+Zlv4UjgYecadxKnZawlN8DNmRTAEJOAv3QyncT8ApP/s7I2uWsenkauNyNsVu'
        b'Y1QeqSdWpQwOe/FPTDS94nNK/D3iqGzaOYOIJgfhVvgcfzpqbiaVjf5uh0dLil2a23REt1Hx8tcT988IMgGBRtFR6fd37dnTZhsYOGRyLHW3OYvFSvI90aSz09U0vq/t'
        b'yuPmnuSV+30NLwarWq82f30qNmfwdsqcxYGzX4q/80HB+9/Yh5V8u3WKfWXue9PnPnf9Vfs3Piw42f/Dtz0P+4xCX1q/Zm7wh0mv9Bqe6fR61SHxpbWg6sILJlVvDiVm'
        b'L6ufsc3v+f47M0/M/0TwZsQjaek288Ve9sHXXzA4dS3Vy/J82OJrbWVzA40dFb+cXvXCl4EFfzM45B3ycrOJE9/il/SP6r/5SUf/8cQ3L/Ty9IjBBzalhPCrYV/yE6sM'
        b'qHckhoAl4Apow1wWOAb2POG0mOvMwFGy1oJmcAGeGWMSYsPD4LReDjxJ3AoLIuFefjw4kaqxkvik0QH+TQ5Mvq9/IGoDm0IYlH4UE3Sugc/RRoaLsD9iPCsJO3VtMtgI'
        b'LtNwZZ08cBSR1sbQRgAbANtm05adE6j0Cj8A7hLoGw1bdoDYm2fwb3iS4ewXeEBroxzrqvGu6mzGWZPRebIfbGbQ+0Htwv+UWbO2F2dLPKRshbWn0toTV/SUWagcJ3SG'
        b't4djyF3xlCEWOkcKyOERPjymRpwb70Dr4ceWcShnt84F7Qtk9v0JigkTlRMmNhqI2eICDBE70oJi69Ba21QrZUszpTOlM3v0FLY8pS2PgMlKChrXoD8sHYYoprk3bS1Z'
        b'ii7V2By8NcYSqVWbSYeJxARbFrxJETlgs4L3Y2rEufEOanPC6NMPbR3FhsQG8LyhdYKA9byAnRCo+3wIAx2htU1iOAuGsxOjdGEsAx3pPVlfa09ezvld/laf0kKqpffq'
        b'aszgPmVc4CTJos2UxhCQu/CPGAL+XGsATvPC49CGDrKD62siXmlXzAAOhoMryS1dmj01X1drNbccXs3xVrvfmN7Ud7B2sHfo7OCgzR27UWGoSSPiSmVab4a2e+xOZYm2'
        b'e6t6dj1Vz6q3LrIk274u2vYNR237emTb1x2z7euN2dp11+upt/1xy7Rd0t9fzx5n208oKMBRtaWFNSM90rGLB+1OQnu/5JdVVBSKystKC4pLl/4GWBbajCNzKysrInM0'
        b'6pkcsqFi9qKMm5OTXVFVmJMjUMfzVhdWEE9Z4ik1prHcp3pGcfNzS/E2X1GGvWuHA+4qcyvQOOPm5ZaueDqvMcIJZpTEMK4LzFM5kN/iWnBHYB8dUXlhPnlCAd3L4/Ig'
        b'T2LAS6tW5hVWPLNDj2bA0mQ8idiuWVacv2wEM0SeqDR3ZeG4FJTRwafD/bCsrKQATVot1mpUaOrK3IoVo7zZNC9NxKWD0P2503EUXk2xiKYA8YfLygq4kUVVpfloeKA6'
        b'wyJvzrgNDVOfn1tSgt5xXmFRmZpT04Db0YOgCkfJYle03HHb0R5DT+1JTShLJHd0xPmTqMHh+z4telDdVl5w3thWtOPWf+d6vOIgtjZrOndiyCS/IPK9Cq2iaBIWFA6/'
        b'quG20NCnR8n4wYxTCotyq0oqRcNTRNPWuG/cW8QlX7HL4BjiRvC+6pGJH6UcCcDor2fg3EewxJpFVIsl9skgHlmFcCO4IQquYMJtcJBilGEQu1bYSbs0bZ8lNKxexQiE'
        b'fRQD1lOwQxjMYxCWOBwcD+JnwL0M2LmBYoK9jETYCC5XTcJXnQJ9UIyuywQXV9NstY+/nw+sD/BNSac9y8rh2crZtIMW6ASn9UEPYv/EVUJ89cAKW8NqeBFVJAaT2T5w'
        b'L9wr8ElOBwMzcWtzyMW4GQwAC5qSDMDhDLB3vQGSt7dRETF+8DrOGn4VtFVhq40uOFxL+6nViNSearRA/sRFLX+xHuiaB/oI476KbUTZFbCZ1IwcI9ZyM6rKi8LIbEcM'
        b'MXPKR2xo0WziY0YH0Ah4fqk6VAyfA9uzs0mfLYatxWHr+LCJg5gbChxG8kInaXi2C84e9Bgn1k7zKAqmsYNjZ7MpvRxrnMW75O3CCerE4kImxQ58B2cbTwsTMCk61fxV'
        b'cAoJJGgDhduCDCnDSeA4yatBrjBYrE+Zcb/gIPbAyJTjQVVFopPpZYYEwzArmWSrTYG70QNgOYc8Bn4IsGcB7mVBapp/ip8vh4INPKNVxbClKgxvyRwk5IyWlXbzEIsN'
        b'jmer5SQehwKb4GV4GfTqgyPwks9Unh4BV54IjsEL4ADO6p2m5f5jBE7QIlDjDLCJoP4VgJ0E+G8lvE4g9GBnjE0aBjSkAaII7h/YBmQ0ZHNDiQ+4Ag+MQP8zY1nPWkvG'
        b'5PL8+fCQ0zD+HgHfi4A7aQzD0+Aih2DvgXqBGn6PYO/xJ9Poy+eMAzHy3lRYj4GuCPReyXry7hPhFTBIkPf2gyYt9D0t6D17cINnSNqZUwtOMuCAGjuSIEfaACl5sqIc'
        b'sIMOu+Km48ArEnUFjprRiIPdSbBLE1fFx010qeOq+uBpWgi9Do5OwcCR4Cw4oQaPjHenu/Mo6F9LFM3wyGziTwe76MhL+yrUl61zn8BHYuzIyc5VBP/rEjgUrkaOtIfH'
        b'1eCRBDkStIHdpMctZ0wmwVzgOdBOw0cS7MhL4Bh5pqoQHh0qBpqx65saOVKQRwMRnkAv7iy+9VrnYSxCGoiwfjG52mUauIZxJX3CtfRjSPoilMN+0ALPZkHxLApsqcNJ'
        b'36hS2JtJEB7tE9CsWVhAZs3H8WU0gHYgPIbnffN0NtgfRTGNKHgjBlzhGVRxcWs758aITCqq4IARHDCFJ9FyswteqmRQlstZKbArTD3LDwIpqgUHwV51TVxLBM9XYeXe'
        b'MRY8BPaWVWFQvJUb4p80B3bVVK7SrzA24VA+LB1wmg03g+sWdB836QnguSp4XrTKaBXYg/P+mFZUsShLJ1Z4LbhUhRWQ4Dkbc9idJFpVZUAaM4UX9NH7P1+Frxi+fdxi'
        b'jo4IHiEPg4jaDo9p6sNLsMuBrmVZyErgLiWVEjz0KAtNHQ2Bzog8LzgAeqqwAJyVDXq129kGL1dWwPOIviRWJBpwDfRDHFuOH2C4KXDMFq3AHMqMg20WfS4E3dIHHJ5n'
        b'CC9WInqN9I0rdEzBBcp4PROcQ6uylKZ6n/fSrHTYmAVPg71wD9yfBfbgpGLtDHgR9MNWepBvR9P9ctaMGdT85ejGW6hceAJ2kOE0Jxz2a9/BjqO+wS7QTV970ggNmdOe'
        b'InjRtEKHYsJjDF/d+Cps02UuYsAGtAAKA9LTps/CG89Mtb5HgJfC3SlpcBdaEcDmWZ6gUV8EdoOzZDHPY4GrcAs8JMSZwBmRFGzxTyfETIuqheeS0aIg9EMLaQYbnFlB'
        b'mYMOFjigt4GsyDMZjlRowTkmZZbjtLZ8Br1MC6P5VLaHPeq6nDy+kzf1Mb07/xCn/sMnnscmiz3ab9C2jCWMaHBhNbUaHp5Eu0gfAjvhNnASSRdR5XVU3ZoNpPoGeATs'
        b'xo7TaIRdr6VqF8GtdPVjYJ8LbMCdF1hMFbuCy0TuLE5ens8SxbMoKtIu79RsYZllkNnF8Dt/Lfr2ixUHS+4+fuHIUaZHBDfD6QdWx2D5N4yZvBMTrZP2z9mc6vQO62+b'
        b'I84nx0oX3nV5uST1uYshwoqcIz6vfRH+3u3a6A/+qfgl5S9vit+JUWxbZvzpgxuS8uDYyp1zW00SnG/+/as3LeXty9uPvGgyya9XtcjiI5/Vwqn/DPmG9/2BjsyMbvcc'
        b'/5zbHfXVHwbWTW4TNR/c+N3xb3Leifwuy+NVUcXi818ukWf6XDm7ddW5zV99f80//W8zD+/7fPuF7pXTjK4/dnKb+MLNtTD1pXPv3VIG3Pl0x3uffmx7U741etDg4/ag'
        b'OPegj7Jn99d6DR06seHuAmbWot07D3n4ftWfKna77fQxNWD83p4NXZKaWO/m+3t7TO+0ybZ+V/iNsNAYnjtxKDz+zcyeAMe47bKklwrif2iXHL6cVb647uy2b7LeWtxX'
        b'tqDw3L62DalT3zVZPfnFf4Z8fLGuaX63/pUD1o7fzv35ZPP+1ldnbBVfnWXe/s0H8wrn9l7M7ZwvX2jp2qGyfqH0B8ePkwLWec/JNP3Wa0XBm1VZW+cuarC+vH1gXu8l'
        b'6l3j7nWLxZ83KCrygziR5ubrFNslbxwwCZ8l2FYYcSAx4R8Ltlu/cdKIl3R0Qvb9pKOuvl923Y31fTAz9tKZV+vmvFFmPrfmfNWcBTvuX+k99a/79/ufn336ucH6aU6t'
        b'5e91e/nf6L798VH+j3zb1ofRNUYtn/06+w7/g38ZLDx57fabd5cLay1T7j5f9MWptIw57+23b4566cN3gws7rs8s2nHuK0eZwcpp03fNLlVGNt+58ENwhckbZ19bXvLB'
        b'FYs5UpPEiH+ydu/T8XKZYhr+qeBvBp//9ODq9llvH243vrJqFlshMr+1cvcD5VWjKeU/zm842v7Vo2nLqzpnsD/JfpS9z873QneN6teH22Bda9vXSeLT+Z3/evWd7wa+'
        b'NvvKtGb/nTUuemd+OvaeT2BthWn+w9jPz/nNPvjhJt4ZyfKN77005FbA+sr4a57jlg9fW/p2ycdFNcxvH2T/tba8t+6b2OXnXjwxr+aNtM8ZpfYJsVMal92JP2864+td'
        b'opDu9TcmdEe++bPNPeND02QZD5T2NyqaP/3bMnvBbT3dQNENoXmg6HvB9NZzqQG3Ux4072vdaVayraz+X7+YekeEzL57khdE6yilC/34I7x8wDW4h7JIYQEpEMNTJLVc'
        b'BryWRVgeuGsdYXmsFhH14kwXuNMVniT2pOkECNkwk4nakhgR3alpIeyJEYxko3RsHgfgdbl3FuK9zmFOeADuxtng4J50xD2kpK+iFaVgNzxFCcFJXdC/Al6lQT93x8DD'
        b'QppKsJfcTwAPUOZwBwvsDrIkFNXw5mv0rSsSnpi1o1cS63USUwSkk/nTBXAXyXenSxnC60x4yRvcoD3TD/LQRrkRdj3BhMY++jZgK1G6lhaDxpGO5bATHkGrJ/YsB9fh'
        b'UaLRtYjNT5vMf6LPxeDdxGJfDLvBeZIXj/Z5n7GBGQIu+RC7uSk8gHgsbX2uI9w2rNJNRrfdSx4gDl5NUKeIoBNEIGIbmG7gONxHUkGwQd+8+CR+BupLDsUOZYDjYAvt'
        b'0g76ZsIBouqlFb38ZUwB6MwnquZgeA3stMW83wg1MdeVvMYVhh4kzx+d5Q+NBaY7B+wjCuTIVNAg5IPTqCs5FGe1PahneoAGuJVGRT0GzuFACdxRKxG9w6kPmev14GVa'
        b'ub4NngWd66P4Wtp1wzU0+O81VyilgxaAJB9z6yRqAWwCB2jvBzRKCcENAbqBcADJcd2MWfZTyXCtBdvzA0KGg/UZoNO6igQWIE6wSw82CBAPjQfernQBI8efsgxgIfZ4'
        b'Zw7pCaYVGpQnHYVP4gKIe8Py+aR3JyJJ5gBhVtHwvEq4Vf0FdEBCixW8AOv5I5j/dfAGeRY3ROpGeC1qNO9fC9rJsxjCs0xz2DiC+4enJ5JOtADNoIlw/7B7ojb3DzrA'
        b'IN0Tff545PBS583T8P+w142kG/aEfW6Y/wc7ysdn/2H3UvpdnSzl4DbgHtBOu26g28CNrDK4BWwk78oabgIXcYLFgOk4K8p6ayum7xzvx5j5DM1BjDThFOEua8Ismq6C'
        b'F4xhPyMYbGYIYLeOvjE8TBskTk2aICSdD58Dx9ALQLJEOxPsSl1L3tAEQ311ehSAGPOtM1LAKR8G5TiVDQ7FgB10Cz0rYDtJvwKOLQ5Dk4PSRRKDnhVsJO++zGgR4THA'
        b'JdCOuAx4EkqJsSYjE+xS4/nS6bnmhFCW7ixE+OYasrqAwyvhFrqGfzrcNX0RkmjQraGEDTrYsIuGRL7kR4MCTxcg3glKl6D3wqRsw9hxqF9JhyMmsBkeRHVYM1BDGX7J'
        b'aKCgCSXEQ98TdurkhMPz9O26bdGouAKbSbqYXfQrMQR7mLALTfYLZFAtCYT7iRfPTiRJczLgpRVMJ9gLOwgtlfCEMx224wxbn0TusDLRKO8jw64qDG5Kg5vgOdNqtfFJ'
        b'Hx5nglMO4Ajdk2itgUfRy/Dj+cAtPnjsLEUSWjA4ynP/c+CG/2cHERZsRquRNo79p3Ylyi0oeKorkVYZsU7t49DWqSmLcUabltghytC8kKFycO3gixNVjs5DFNvadYjJ'
        b'sndVuXn3+nX79eueN1K4xSjdYiSJksQfHrhgx0Z71ycHlRNXgg1R9q4//PDDQ1sH3AJq0cWjc0P7Bplo0HJwwk1r+aTptzwlGxQumUqXTHzZLMYDN4HcL10+I0vhl6Vw'
        b'y1a6ZcudsnE7sxhDHMrepdOk3UTunS2fs1g5J1/hna+wK1DaFcjtCjSxPnHEaqblr2TpJLf0kWXJsvrtjy/uWzyYe9cvTu5HV1MnspRbTVJZ2jZGq+xdJXZSjx7/fg+F'
        b'fbjSPnyI0rX2HwxWubh21rTXtK3uWI3pV7gEKl0C77lE3XWJUrjEKF1iJGyVq4fUUpotc+2Z0+XU4yThqNw8pe7SfGm+zEO2qs+7q6SnpD9T4TWRxmy+5xZz1y1msEjh'
        b'lqR0S5KwJZltutj+hdN6MtoMOgwkBhpzWK99t70stMulx0VhF6S0C5LbBanLRla0wBW7HHscFXZ+NGDxkCkinzwDOTzCh8fUiHPjHYgJbZwyM8rJGZsZpaEyhsxVxuqZ'
        b'pHD0Uzr6iac8tLSVREmipJUKR4HSUXCXpBUiPTxN4ZCsdEiWWyWrbN3H2D0trVvCW2ObYqUeCktvpaX3b9g9bZxbS5pKGktbSsWsh05clbO33HmyLPFM8onk46l9qfcE'
        b'8XcF8QrBZKVgstw59WaBytUXjVyVo0tHtNKRr3Jx61zXvq5tQ8cGFde917jbuMu0x1TF9VA5uz/kevQYKblBKhf3jrVKlwDV8Hd3755opXu45ruHT0+a0mOSys0Lu8eF'
        b'qXh+fU5KXuKQub6rzRCFDzaUq0+PkcrFq2ONiuuN/nL37Ymj//LgKz1CcXySv4oXqOTFoqtc8FXowHO2sxii0EHMHoqlXD3J3cTGaEi2RCstCXjNAoYqMPS8kTIwVU4+'
        b't9Jvpcs95ovTEZHodbD7jJQ+0Qr3GKV7jNyMqwqNOJ+mDE2W05/U+fIFi5Spi+Xo470ElUstFGYeKldPqZV0aU+ZwnWi0nWi2EQVPOl8QD/6uRkrn5mtTJwlRx/P2WIT'
        b'SYXCzO0h3RshKs9glY/gjP4JfXnwZIVPotInEdGgEoQoBQlyQebNOX9ZiJ86WuXl21vcXdxvovCKU3rF0efQ4/PlbhP7rVWu7kPWhjbosdFBzByyo6xwskTzuQxVyMRL'
        b'0WejbxooQoTKEKGcfG7NuzVP7jVHPFm8pnG6ysZBXNBY1FIkZqlsHcTrJFVyW38ZBw8nWzRQzT0wYHZke2RbdEc0Tg/r+IZ7aH+20j1Sbos/JI5s6i0rBS9d4ZyhdM6Q'
        b'22UMsSi7KLTAOLl3RMuYMnMZE42Ze45Bdx2DFI4hSseQcdpBw0XCfmDrI7NSottXqg35JG1q49qWtfiLm7iyZY3c1gd9pDPp3+i0nWOnabupjC1bMRg8WKGwm6y0myzW'
        b'UZlZtho0GUhCpcEyyz7rfovjDv2iwQKxgcIsUWmWKDdLxDWMm4wlhdKEjmUKM28lDRODzpo2mUrZCjNPpZmn3MwTnzFpMpFU4tEcqDALUpoFyc2C0Ol7Zq53zVzRZNNc'
        b'bGPXsrS1rKlMWqCw4Stt+LhLsS/CuqZ10izafj9E6Zi7DTHZ1m54oTFsN5QmKux8lHY+cvL54YGj2xDFtNY6oOWyowZPN1kWjQqP13Y3lZMrXsjdyJchFqqH1xkOZW5F'
        b'PzedHA2PXmKqD0IbU7ODP3XaIIp1hRHFgtaJYdNsWC/ZsKc56L40gYGO9yys5/hQ93w855qxVKYMdKTt9ja03V5jza6owcZ7jR27ovZ3bfl/bGPGTeXQ/0btyLQXwJnx'
        b'3Fy19uBT2BMAB+T9oP6HtuI5ixgMBonn/D8//mko4+gxqZP6CQzqeYZJgimLx7qvN+xe9wRBKp9NPfmnMYxJ0WG/2bB3AXEa1FX7FhiqfQuYxLsA+xZQBF7liV8Bm0nt'
        b'HOUTsE5HfxwHQXRGZ4zvAHu9jtqvYNwybX/c97OY4/gVzCpXhzaOdCsgBvZctYFY42f4dGP9cI2RMBqValu3VhMCtck7P7d0XDtoHnZp4BavJKbPit9wYPh3bPvYW2Lc'
        b'u/oOk+fLJVAZxAw7TAdtVKdJwh4SiPRS2pA9vl2dm1hWUBgyiZuXW0EMwfQDVxSWVxSKCknbf8x/knSg2g1iNOT7eP4LqPnx8XLV1vFh3wBsjv898/EfNRbrUWONxS4Z'
        b'Vdj/Fl6YD7cjYWu6P9Y0bUWC4R5+5m+Ehezl6cMz4PzKKrzYxiyKG7ahYuNjMjYrwvrpWdqm1GVgB5I3e/WxhG1NdNjG2bCDn5o/iThfIlHu4HSiSv9kiiFlpRdMUWY5'
        b'guh1cZQIL4SuHQuzjMtXsahfTzFnM6jA56umobNgcC28xAcyrBLaDLchGvfhXHC709OIVDkHq4vSfFMF4ET2eEYB1ixjeExn2CJ+FPS7wHMMYoTZm06lgy0iGgwyd9KP'
        b'lBmTsuv3WF0oiTpaTqv0VW3x2aQ4LGkB9Q5FBcav37w8wqNkAl08tTuelPI3rGAoLRayKG5OVIFxIJ2yDEm956aEoNXKNSCYCk4AZ6qm4F4Ep4S0PXsVOEgbtGG9X2o6'
        b'bMYW8wC4JyVT/RREOZeZnCpIVacbuwT3GaeiJztNXoeJ21pt8y48sOQ3o3sEy9TJ0XRmxAjhMXBWO023Oke3O9xOZ4QbnA2uPoGY1INtqXzmGht4khhj4JacCO07g/rK'
        b'EbZlH82FYBO4rr8uAWwinfS1DZNil2CMqZy0ptQNautJ/HK6C62s51DnkfxaXt1eN3d+Z21FO46sxyU8Hbo7e0BTObGpONuvplbPsyTDC3XKLj5RdqTB/XVUXWQBnaev'
        b'BY3uc9ikAuuJSQUeg/2kmahCHBWEq3SYFFPFLBPavnwi1wnrdVDvNnAodO019kQGOAOOwjY6+Vt3GLiATaHgGugYYQy1gAeJ9WoKGIAbhzVfhlyi+0oXFteFH2WL0INT'
        b'Ptsj97Q8V/p2oNlLKZlnr5cIB/4akdHtn+AiTbx0PamXmmBqb8HdYsXdluD/4JPnPnklpeFbrwc/TokxuFj4yjdHWt+0MDp47V+/flV77ds7/wwoOrCv5Ne5r9W/1OL3'
        b'VZnpxaJ/WHw3++Gxhfvsvl23vjwr7G7aKWm93/qLO944VreYc1uQVhh7njF/83NHX1v16yvZsWuyvrzWsCn8q7eGOmplMfxzvXtn2767esv7KUEHhVmbh87983Zo1m1n'
        b'3j67rjsbPzn+erHJ7edid577+Ke96/LSf3BYa/v9F/tF1fuudvDe/Smo+Vhtm9PANO/woIGg/S8MLa6SMg+K//li7+F9n67/zjjkjck7xJ8k6yfXzGqe23rZwDUr71DI'
        b'xb3bYzbvyja8lWkNVFn6EtnQhP0bg3wP+Z5olayaWti31cBlc+6bUye6NN6YyWqIen7qZ40Ob1jsnDRvy6dvveFbP7jedL93jceXkjzjyHuzPgbJogd3+t7jR/7ya/TJ'
        b'Hzq/3b12+eGgb9JeEN/460/1D770jpylf3uObuqXIbahlh9/JxO9F3XBfcOq965dD7lUncpL29nrkGZctPZI3v6OtNfLzu/+2a6dX2q4y+juc36/LChJurNReOi40ZrQ'
        b'iuf+HjnrY98dH51uCBmsWHE+Ys29lz+5szIlacamho3nnWaX3fN7szjqM/euzzZnH10fFnXHfp5jSu1rKUXM8J8ngJW/HuQKljHf56Xcqf2k+MM5B2J/0tHhXVrxWibP'
        b'hugVw6AMNKsVwKYC2sH69HyijF3IAa1CjbeGvhU4OwsD1+yqIeqteLdcbdfqjDy1qh+0ltB60QuruBpYVk4JE+7nuIEzUURFbzYHSGj9sCiGaIiBOJa+aD9sXkbr7sEx'
        b'2ELr73eaERV9WCBv3Mg2eDqdDc/A67CJVgVvgWIjtAglY8OrLYedzMCWZLCP1rk1gdOuQuLUIvTzJUnVUmArizlNSG4fYwjPoMUH9KXqULrgALuAAa7pget05N0lcAA0'
        b'8FP91OX6ht5gPxM0w2ZbuvyKP1ZA7wogz6U/AZF5mgnEcAfYQpTXcHsYPIDzWquTWrta+TF96ER1DcGI6AbQHa2tGlcrxtvgThp6F/YxsQIbyBbVpKm93U0nshbmFxPT'
        b'CGiAEiOiG4X70ldkooUbbVB8DuUIDrLBIVBfQV62CTwNbuCL09Om61AcJ6ZZNJsRSxNxphRK+fAykGlraWkdLWhFROBXADvRl4tqLS14riQd7tJS04KL6FHxkmWO1rle'
        b'LUVtfcBqsI9W1IYuJ3pa5wx4hW4mwy8IHByjpkVr5jYyBlfA1mJaRUr0o2AA3GCCswuBlOfyf6/2fLrYhVXM2lzSU3WhRtoOlnWOo2OntQqJNvQzdTK4KXkM6v9r7z3A'
        b'olyyvPFuusk0sclZQXJWFAUUkZyUoIAikoMkCYoIiiIZiUqWnIMgIEFE7j1ndsLO7Ddwh53LMM8NO3lnJ3BnnPBM2Pmf6lav15t25ru7M9//Wbqf4u33rbfeqlPn/M45'
        b'9Vad0tJ5PjE/dVPTbkuTbeymclI8QOX5RuqmafCmTsiWjmijKU39XQ5PxWlb37g3ujO641z3uUbvRu9tdcPG6D6pMd6muvWWOpvqzrJYtseMOW/qO27pO1IWURDiZHqE'
        b'mt2WmugRVtv6e9mc+46Y7hiWQbv9RK9/p39HYHfgW2rmG2rmohoc29Tx2NLx2BB6iFcFmPed2FS32FK3EK0yHwt9viqgz6HjcPfhMc23dO0bPdnigFeWorPFAY7PPm2h'
        b'+ofJ88UBH1vJzkZ2dai6ukZsln2YeC+7U5sGoVsGoRtaods6hr2WnZZ9kZs6tls6to0stKyuQa9Vp1VfwqaO5ZaOZaPntonZkG9TUKNXu/P7+nuotZp67fnNxY3F4iHV'
        b'02MFswXjJZumbpvG7lvG7u1S20Ym7ZLbxqZ0pKnfx28uaSzZNtrbx+vzGouYPT1+ftPEddPIbcvI7UWu51lZDV22DYx70zvTx0xnpcYMNg0ObRkcaue9z7bi46k7bps7'
        b'jsnNOo0rTSl1CNr57SnbuqLhCsftPaajlgOWY2H9dkN27Z7v6+i/1gZNXUaPIDFnBGzqBG7pBG4IA18bD/r4AOhfsfDDwKo9c+zE8okNA49NA48tA48m+UZ+Y9K2mma7'
        b'DBuy/9Qbjc3eNnZ4y9hh09hpy9iJ7olsUtxW09jlKKuYbgt12kKaQ/p8xxI3hU5bQqcNodO20LgxqM9kjL8ptNkS2myIvu/rGLSbdOzr3keNFWqK7vHouzRmvCm03hJa'
        b'bwitt7X0Gj22tbTbvTvk+iI2tSzpl6ZWu1PzlcYr7G0Ad1tPv0+yw29MalPPln5RIX7Nfu0JfafGjMcuzXosH2/02xQe3RIe3RAeZVeDmoP6TDeF5ltC8w2h+YuHntgU'
        b'WmwJLTaEFuxMcHNw3/4xua29TrPeW3uPbApdt4SuG0JXuva20PQtoSnRVWi1JbTaEFqx/P7N/u35LIy30GRDaCIeaBLNxLHT8VTnoTrfU1sa9biUfmQkaVaK80qM6y9w'
        b'6OjTRpI+DmbikaR/YSNJnwVgzgpUypc4z4eSCMTS4rhcLgts/j+YfGHLUkoIiS14Yso7sD5wlHptgIhtvydyhpspuSf7ygARr0q6SuL5hu3iQSIOGyZKVng5JPT6tu1f'
        b'/JAQW2Hq8UkrTF8MCX24a/vLBaOidaZf8CJt8T0vArCL7/uEvb9sjTzFqwhEVfmU1RGiNd1s3Iiy+oWFHHK2d2DjNJlx+WwOfF5+blpWyqdWQRz5/cMVAa/vSiS+/jeE'
        b'xJAJFvmuMfLMw/u0gBgu0Pqa1wyPZL3Fk2Ef4zp0vbINuxLZZK0ekdgLNaLJsEexQ0I0l9bgot3LmbTQlSqegTmYHPXRPd7ZNF18gEvHoRLr0vDKIC+PcckPeOl3gh0U'
        b'bx1T7j7yW2W+rmF8cen6rvyZqMg+Zyk5wb9s6353MvX3Q5MqsrdPHPxOfPLllB/1HL3g8ZXb31F8Z79Gamalpf3PH12wdzDV+eF3Zy5HGsTMFOEP9BLy8w506jUctfL8'
        b'4Le39/zW/E6D8z+fufHzt+/GD7/tJKeJl71G/tTtmL8ia3oiLEj3ncVf/tmvb+1QtNevvE81vrd+4w+rbYOXvxHghb+QMjg79Bu1kX+3av1WvoWkeErNYACOi10X6C5+'
        b'HrKz+6zIXI7yMWGv7pVw9tWVodgFY6LpCKeyDJnzgqPFr8XfyMd6kTl8Au+cxbu49tHpKmKbHNthVVyBISdoF8+B4UicJNN4gBsRDaNf8G7BHzcaFQtEMvrSbNR/DXU/'
        b'ellkOP6K83zRf9L/7SJPTZPGkr7wTU3LLU1L9l5Lt71gQ82EvttmVo0n2nU2xfpLXWRyum5rGjcW9ZmPeW5q2m9p2jM758j2Xvs+t1mtzb2Ht/YebpfZNrN728zlLTOX'
        b'TbMjW2ZHnpdBhuWGmum2KStTqyl4e6/VqOuAa7/7kPvbe4+8RfpU9EKRLIboTWWjbWX9RoFoY2Rliy1RTH7x95UgBkqvLJh8idd/o7oUBV57TReKleC3mRL87O4YZmqw'
        b'/xU16JP0BavBL0zH/ZYRjrsjXZSWw0bh/yFjsbFdfMY/vl4yNyE17fLzCOzPN2j8SMz3T1BfnuIB8oyrohH1tMycjCT2TiAp0fhTVd1zwrwePZxOf8pri89VFvxgUSAk'
        b'CwL9NnKHk3UIvD59BU28pkyam27ahcUf8/KO022+7msszpw4KKGG/Smh4wXu/cCvl35v8t9yvY6bTsl8R/jl4BFLZymp8ANBdaY/kznw9dLCA7zj9fOSnG9ny7+54mfB'
        b'F69MX8HH0Gbla2Pwyrr7QRRPgsTBw3s/HBfCVhwVzw0sxznxNK1KuIfVxfEfX3kvIyfzzJJy7PM9xCafxnh/2vTT51NPVS59dqC7HeU4cUe/EK68l/uavXyX+VoGERq6'
        b'P0fDyGQuR6jxfJ6H2Ycb7TyHvqNvmL0Kfe9oWIjfRG8oW308JN7bn4InHwuJ957UK9uvfVo1/0nhI7HwfJIJI5gf9xnJFxoLT9S03AdcNgYeHBzuHZz7B9ZW5c/ZbOfD'
        b'mLQsFpwoiJIoKIxotbnoZbPITxDhpIgQFjr/AKM1OpzXNuH5BPfmIOu11zadcGQvx2t4r23MI8s25mGJhnhjnr19VzYEdpsCuy2B3a6EvoBFEP6slG28Y/9hXveP7Lvj'
        b'x/bdCWC70VD6TJSKtt55dVMcttmMJttsRpNtNqPpUuWzK6PI9o35tMTgM/aSeV8gZG3YEBhsCgy2BAa7EgKB4S7nsxLWAMOXWQ2eU+GVEmTYHkMfST68hZ0RviBc3obA'
        b'alNgtSWw2pXQYlvVfG7CCrJ+mX+/uKAzY07Le7cN944JZ9kgkyLRhpJnLHn/2Ilt12O7PC8JVsB/b/qB5Iun7vJFZ4P54voljPFmw5aFy6kb+302BL6bAt8tge+uRAiX'
        b'3fk/nTIK+nE/rMA53vPeGFMbC5813zA/8saJDYHfpsBvS+C3K6EhIMT82xP2NH/uy5Lcxc8K2xAYbwqMtwTGuxJyAmu249HrCbtxz8cziGPlsCHm01ANSy83MsJH7CCQ'
        b'zZ02N5PE+1B92Q3qC37DFsU+ggGshfvQ7JaNXfbKUIFLuKp+0BlKE3BG6jBWQRM0y0A13sdbhgJoxHLogyloOXECBuShGWq4uviUnvVUAB2HcQHqYS4OHuF4uEACH0AZ'
        b'zri5wlOY9YWnPpSrAWuuwhKMw5RtMQwGwgPXYnIzRqVxFibo8/gADJOmHUm55GiKHQ5Yiv1Z0IO3cRznsKvYDWphBKvhoabPJdcQDajdi6WeJelOeAfXYCnNFSsu+ugY'
        b'xul4Hw6QjHK8ZhsCg1F6NtCCj1xhBUdhHhqzYAKbqJhFX1h0ybTEBsdYrBPgSCLOqpEX2QfNOECfVWy94ImdJ53S4U4CTktBDyxiRTY8xCbsCcNpmL2SiUPwtARWsS0c'
        b'mrRx4OJZbIWhg+r4wBdW7aGO2t4E9SonYCYMyswCqAKL2HkIZkpw8hR0cHEEOvEW3oVu+t+QCmPYCQNXDHjycBcWsNfRGgdxMfWQnCv1UGWCHpT6ZMLtRCq2LQieWCR4'
        b'Zxt6Y30aPsUuf7wXpQXThR64DHPUTbNuUtB+yiKC2l0L96Bcbl84zmthPw7Qr6UgMlC6I4kY96DNGpd0YfWQu6mbiVAN507Tue5rZmetsAMnlNWwEhvhUXgenW1SlNuD'
        b'63TTBD6EGarRLAfbnJKOYMc56HKEJ6rYqxgfBPUp+e5YGoptBlAb6yxDnvuynhosZ8C6LlSk0O1TbCVAu4MeDiTuOR3tZoctxArLMJIXR1zXip3hCtrnirKOXMMFvRh9'
        b'6AyGAe2zOEMkasMxGWrPArFUJw4cwzoZqPTCx/bUk60w6UINnaL6LUFZJHVCg81R4oiaQpjT1MUaItEq9ile5+ETrPYxIQ4eK6gjzj8CtVSj+6EeUE+MrwBPcF69+Bj1'
        b'8KgXlBpAN7bbKOzHB9RHD6GH5wUjCXF7LaAxlQ+1RjfsYPhQQVGqEvnD1SRAY0TdupwLZ2BNPRI6j0EnPIQhKIvDbktss9qHy2RQLvFgVhbv6uJinGQOyeBCRNSVo9hV'
        b'EpYBk9hFlFgzp2YQj+B0VsARKqJHD7rw5slIKrs5EtoOQjtUxpPw3ZRwCcJmmLWhPHM4BhMlZ0vUlCNvxO/3ScFulav7VXCa2lpLzFxGcnHrAAlWtY9hoMnVfcRuDdCB'
        b'Uw7E5pPEnstYFYfNGfCE2uSFq1AtjcPu2HwNegsCPNJw2gwrzbEK14sP2t6AivOyYbCsZcB2jcFRlUP8bFy/gHMS2FioEeeFt2FeDuqu+0I73tTzgfooKMXyRCXohbGQ'
        b'sAjHBFW4Gb9PG8c9fOSEqrb2krpOESRH9wOxKoy6uB0ntKCKgKU0DkecqS9X4RaW87A5GJrwoRF2B2NNJE7APF+F2K9GEwaoJQybymMdGXGhCqdg4UqhNtwxoEdOE1eN'
        b'FRJDVBapyJBMzCfjXVwpdhRCC5HxNnXPLGHXI5kURX/s1YYH2Bd9GidJ9MpxyTAG1oICYB1GZU2gmQU/GIEKlyScz8TqSFiz1WHvYM+FAMnOFJvJEwrNAf4q567gI7a+'
        b'm3ih5yzcJBFap2bddMRJNbMwE/UQuEk0fxSFwxlEvbEQmLPAZUlojzeB/shDBW8RQypQpy4SQ7pBA2NIqvWKFSwUuGD3OT6V2oe3s+Kg75I8yWXbgZPWMKJ8IQDG3cMj'
        b'oQ4XiVpPsE2XWOkp1FDT5mDGDyrOstgOe3DN193dDdv9YTBRWQ7LiWWHiamW4PZe6DS6TDzcJuEOT65ynG39sOVivhX13DyMkJNTQ57YKjaT1HXFn43JIgQZsMaudCL3'
        b'Kod4qYaYdQIGoRXvnvMiZFy30jyTH3Me+oKojkPYiAvmJBxNR/c4FmKdUBZWXmVZEpDWk9pUj0dXsMxG9gbb+IWB5l3Fq9BBaDniEehcZJwAs8HXijV4532gVhNuJlPD'
        b'1qmAEYKmMmd3YuB26Uy4A6Ox0CKgLh43EkDLIezwhb58ynITWUt6sYfU0iiUKklgmRuByLC6NCwdwsda+1hUOnjsiE+FV3AwS/0qPzUDS9mGSliBd5WIUEPUvBF8AvMn'
        b'qTcHVLAmSj+VeK0MHx6DISL5k3NmpJweRBXqEe/2Z7ph4wVSYW0WMH6FJKLOlrpiwMORUK6auJJU57n9Fw9gk3k6jpUcVyyiCpZBKXHyAMw7GJknxsE84c2SghBb8DGW'
        b'KWCVN/Q4hhNHQP9VqkA1NpjDI/I2J6GhCAekdU2IyKs45B1lB0+xW87bkhpcQRDZR3q76wTM+6SEUkfOw628KOrODtKIvbBahLWXoT1GOglb3ZJ9bEU6vSEgnxRORQGB'
        b'QiPlaXX10YzENui6CDUSl7Wgm7ibKEjcDT3R6VTLdezlmWb7e2N1lgCbks5I65/HaR1oY5xlR9I84K0SplLwr8zCaLwexWA2S2RePGFzDBa5XgYXoE8aO0LluOLwJPUk'
        b'MO3QmA9zHIJaE3UsdSDqtutdwwfS8BiGknzModMTJtVIFXRqs9AmitgtnamXThzTqUSC2O5ogU8jbH2h69Q1vKsHdf4GB0kLLMkRYZ5irfRJGL/ABCWOm3OO2UP3s3AG'
        b'V2POEFQw8J0iDCD7I9sZutSOWYWq4kwUNF04Abe84LEy9vncOEtU6Tt4TQ3qwgKjYNwUF27oe14gzJigzpjMJJJMQtfZq1xs9XaClXD7a4qeeBO6oN09gfTyLerhAS0V'
        b'InUFDvFgXQWbIzSVddgsKiE0xgTGhZPUrjmdOpxB8tsSCS22UBYotBPiWAZMHSO5q0qHu/vwlicXSyVPwuPE43DPOw3m3YNhFaqOu3h6XdfBDmJ8QsRhel4lJ5PgfwAf'
        b'SkEfSUC1BknKHJGqAbsdYQ3qtElAu01htQQXL7kTw7aTkqvHVtdLOOBBYFKaeKoQKnyyifn7SqC1RJ1Y6lHiVRxP0cJ2gr9+QoiaI3jnjIozEq834pAPmUXEzcNGB6kO'
        b'9+lo8NjBQh9lUogndGA+jFhwCRau7idxX8MJT6xjQS5I3fUeNGDmWC7UJRuZMTbEJuFREQwMUDVLoScNWuNVii4HYTc9ZYFEqg2a06g242xXKrIIyiTIkCXi12lfoyZ2'
        b'kf6cJLWZFwn9ttiDQ1ohgjBSE6PpGtifhPf8qI9HcPUc3L9A1XzgDg9IiKtc4DYyKV/D1ggqovJ86mWmgPBmpjbO5xC6zGG5iXe0HM7qOnif0icKPCxoYpzdT+1cJt6m'
        b'hry0IaxwmZuJ9WRDuB2ygiV7mL0sb+YinUtGbLv3aWw+Tg2CPg/q5jV69nwuFbHIMChyD1Q4YZlDHNynh9fAbM41NwWDAFjDmXjspTwPCD7abhhCqdVp6vNl/iECwlZY'
        b'sXQ+ipMxZKPdw5UkMjHrSYlNkIp+hARrZTds8K5quirxbtXxGOjzx9bQY6RaG5OOQUeEJZkdQ7B6mJ5XTwZJHzxRIvm+D/3KOO4L9Q6F2KwYZJiSSWh3U5qkpOeaXCzM'
        b'mh4+EajlJiBGm4J7ijb6fKLbfTlVF1ww3CfD88ZbxkTKUlNi/mEVXdLw9VTm9Dksi4G7HkDY5E56kOCJjAR8HIvd2HPkEkHWPRglZTJExv4s9RT3pM1pqDXNoi7ugqkQ'
        b'LIvGgXOHoSbQOogIVwbVnum6IT6nmBlTE3MdRuIt8FYClKpdM8I2UldNZ3Exlzio9RROXsAqG3tokyB26w3ESg9isnXC9emUGHJLGgm7q7W1iMgLF7DlCFZCb/YhIv6Y'
        b'I1S4E98MYZNDlDDZ2SUkHoYu4HL2OQLmviNKcqZOB4XaThaE6gsKWK12ItiMlOG6KXRHUKnNAmKup5lQE3qaWOTxOejbByPCRHyYRQ/sombeP0/yMHw2SZ0gqBmmbWFG'
        b'nohZg20pUG0IczE55zWPwkQGZZqGjmQCiQ5eOtWqNIzYfsEJGtxgzYzU7QreviHEp5wM7LLC1mKya7cl2K7f9iTxxJQ3s0Q8uUY8WYiTSTh2VYasnjK1a0TAm/v0ycJd'
        b'0LNXxRZlMiXPhBb5QuMNQ9NrBVARp3UyViGUFPgg+0DZARaSiMCEbnNjVlOxsgCmCqljH2Pv6aPypCwXYV3pAg5jRzop21FJLC3Ae+FJsHYtiy51xceQLfNAZDwAGQ+r'
        b'sJZGzD8fr4XluYY4bC4KXvIEJ8OzsKnYiCCim5m7qVSBqvOHM7Xk6Y4m0QS0aagNiiI7b6IkrORMauEehWAki3UQh/cQeo+ecy9UZGFqgcluIyxrQ1tWjrsqLCrlk6Dc'
        b'zCWbojEy2EnWBGfjg/EWtIZRrkW4LY0TgiSsOmXFptfdgsoc6FQiz+A2C4A1F0u8OmunYOVPMNWRpuydftWdHKgBfZLSGQKcWl1zPpHznj3Zm42aQribZWToReI6pY8r'
        b'PoRfd8hBWSCd/DiLRTnA5kumOLKXPNwJvF0CneY2BIPL0vSwMhxx8klyKjQ+l0yCfpPEoayAJKFTDpodsP6iE3YFmpIwzKup5MUTDD7BiWiciCG5GTImHuw+SEbLkhNU'
        b'4nJOFgzmkxteRe6ypr2QYLPtKGH9/JG9VO3GVLhDVoMkjkWQxqwiVm1xv4iPIrSxnA93cSaJnnuf2K2Ts/eKW050nsZJ6uKHeyxJXu5DU2I+dLsXQs1erJY8h7Xp0OFK'
        b'eedggYzONqw+TYhcS6ZJtzBQEXr9990IIRadwgdFURlkKraFuXsdZM7ZpAsMe+RanoMl4qqGIHh4LU2YTAjUoUQcvmCDg6eKfbDF25KY4oHmHrxpF5gewWinaCElmnic'
        b'GOgT4CfJ4dpx4Ml1rCl4EQCnHB4FvAg3E8+sNwKgddEdMRmaAVYSHO4xToYrCWYL9otDV00STz1hUQ64RzkEGl1kgbTYigtrxsZr7NUml8P15wRRK7uwPkZUWEGOFNZa'
        b'c9mk+lyS2B7bjAI/HotXRI4Fo1IL3iHB6DymQESfuS5neFYWWo+EKsWpkWZqsiVeGCAy3WP2+j687ecdBBXp7hoWBDVLOKxdROqpH3r8lD3OEn43Qnc8NpDNQhKMvc5s'
        b'0IV876ZC2wJPmNBgZl4JDCfFYaU89OfGkdi0wLo7lJ45hfeCqSPpOgljuRcdDsEoh/C1MkKVbLguO+qv+47RJsR2N/XJG3hoGUXlNnBC6JnlSdT2GVLDLdTR5OGkFUOF'
        b'LanXpnBo3EeOwhyxQzRRt2kfUXIaml3ITSrPjw2CpwHE60OkJGqJq+b0yGUqI7esysWiGCqdyIB7TCgxS9qgD2aNyRoeg45DSYcu87BBOkkJ230vwrgzLudaGeLKeZyM'
        b'9lOHcenigqSg3FjRkvQhWTZuAO162niTCDtJYHST0HHkXDSVVUf0bI0SppPErlAVGg9QU0fcdOTOKGBPwgWR39XJwzJH8mJKiSrTSDi67gh1PJyNsgxxxPJIArX+Izi7'
        b'j6Rm1MkKWCCKcWg8QjZRA7WnNFezgE+KqTGP2jAEayfOkkHZAjWW0CONU2nY6Av3jmJfBDlUdeS5rEmrY+0F4wQLT12ckoF7F+BeLknJmoViAY4n5ObiCH2aSwRU3Wrn'
        b'05HkQU4TFDc54ZynT7FKciI8MhfAoiL2+pJU3TqI03Z+JNjjUIFscKdaifz3BbipA92xBALQetQ3Ovhs7ploTTKKqkiLr2gewru5dk6EEnOXecSTwzBlo0GikIqTB1m0'
        b'QEs17NRkME7artL+BonoowNkxVSz4SiL4GTSprBkB135xFCVsHQWKrNIgQ/BxAkS3umAGzAdS/5eD3XptCNO+R8WjcA84ZGa6T2bQu7UMDQc1NS9bkXm50Iw8ySwKRlW'
        b'ccCeknVcM9KA1qQ863wtsrkm3XH5vABvCvAJF3rO3zhrAlUF40yFdZEZVvH62AzB6AN3o2NKl3FKQ0rnCvYnknTcjCdgfnjyLNb4CzU8yHdZh7ZcomeFvFAyOjYwlKCn'
        b'0UmHeKcVZrRxxEErwBj7rrrC/DXyCyojtUJsEjykSbMtnzotGqeZCzGk53RCizMR5okctWIui4BpgBTLWiouFsCiBcxArasViccIdmfRj4bL+6HTmi0qgUbGrmSYWsID'
        b'+2wy+nsO41ziWSJ2RdBpTWZxIkH18BkuGX1PSLBv6pEMPfQhRdfD18NRKwLfeRxUOw1jewhz6qHrWG4gWZs9KWSBlh07LTJ5b5ZkkKGve4zAZ1BbiQ1vBeJokaqnHExk'
        b'xhAW14lHAvISSAoaL5pStUilYf91QoMVPRKG++TowmjQeU46Vh7PINjpPn88hXTDPHYnUQ2b80kXl9EdZJ3j/YREmMk4eRAXNJXh6d5oYoh2IQ572DKKWOK4ZhKupDEL'
        b'mNozQT7Ek1xcOy/pqowdug7YHJJDsFanhgOq5Ie1XCNjqhTWLxFSLhyFcZUQ86NOJqR++/BelAz2+2QT0bvMzQoMLNI0TvqoqmCf2o2CwwKoOC4RTHw/QUxYDSPXCQz6'
        b'C077Qu1ZgtpbVrAsTCLRfEKysVhyJpO0ZRbU8/Ah/Z4iS28l7jIBbrdbcSQOR9kQMnXipAWsHj8P04amfgQMLayDqROeErZ1EEBMq1Az1nD9+slAKnToADRnqvuE0LMf'
        b'67LYmJ6w7EEoXBkruedoPiyrFHyLuFUoSar0fhjWvvRwz9DD70DbfkPm5EaFynPhkSpWBcOMlA1Mn5XSgHEkFFw4QEww43Ia16DGNs2FOLRJNGgysceGgIyN03WoWEM5'
        b'4RrxZwXMkneAT6+E2FhQb03iE3cPGNeDDiU9HaJ9HSwkksAOHnXlwLg2QcuEKXS4YKkxwd0cTEVibwR0OUYR8lT6QXdiFCmFmdPMQBnA/qhcM0leqiu22uFwIVbbwtze'
        b'cCzLsoeh9OOkGIaowaNkuHZ7E+bASiDWWEeR6uiyJHG+bWN8JhWHD6pH5+LTYOK1VlIe5fuFMtCbnsWC0xFQDOBssDSJwHpOCPnuTcQudTBURI0mdaWDI3Zwr4AUSltw'
        b'OjETeS5t1oIsKJczOozTLmnY7q+RCU9gvAC7XOCxR64FH9tYvCGcPW0A6+GcQ3hbIIPrPKpnRZA6rEiy4ZFBFxhJ0fCFVi9dHRfyu2qoUTh9hKD8CfHEDAnBEjHC2iXy'
        b'QqfUiOwd8QlMcJJTzQlZ70ic80i5pACPzuJIekhwWvJ5slXnFKkSnaRyJ+VwLgBqE6DttJUmkJNxC++kK8ThVDg0qB27EHMNe/yD9B2wyR4f6qeew3onCWa7EgqVkzfd'
        b'i08CC4up/bXxyqS++vGpAd8UWtVCsSIh0uf88SBvEvA6N7yXdygRV/YQHD2gTq0l51AqlrBhSj5KT4QvDLrvEinbE/bDQ3y0x4IEtx0Hr5K81cOsORkztSrSpCEnciLV'
        b'2f7Kibh2kq16u4NkIDTKwqLqEVsCtJ6rajeUzEi4OghtnlpjVSz0HMyERbeCAk8es4Jyol/ha+Z6i/zbRZ6EJo5h0zGlXBgSSqWbEerep+Y8JEBsdeD6h/sxDyoBlxNw'
        b'XkCS9Yha3299RBEb9aL1+cTknaTC68iMnyoiet/bHy4bAQ+csTOS+LuToPuxPHPLYVIvgghOnjXUa2B5mDezftSosOlYQxh2xGkvSySTxl+faFS7B3ptDUlA77lClzoR'
        b'pyuP9M5oEjyM1CNO75QI3a8Lg9ouUBoP1XZk/roRHBpGWOgSUDSnYpksPEzKvUGqqwwWopxJq8wnMQyvlc4/6QTjCgeJyA3YoRVLZFpRxYEUdXwgY17k4XpJE+4fhJnA'
        b'YmKrYdJ9Q9ihjYv5/jiuSsZOA2nS1VRSBUVynrnUiz1USPOeQ/kwdITvgNNHTWDMXQ6783FKOTlGC0ZUlC9BizrWBaRQQTfhrrW0YxD1KNkaRJZlvlFQzrGDoen4YA9h'
        b'wziJUfeFPbjuTeDVBvf9PNw4JBk1JJhkgRN0NcOifDJWHiD9TDxa6wmzOrJcAoOl2HMEe8PUJctUarmK+hnS5HdgUAZup0KFC47bEP5XXb8MzYfOIRsnH+DA/PkjutT9'
        b'j6EizYwEbVQL+m1IzjtIJmbJre6+IKt9AFc1oS38UECOD6nPMRjDaT7dcgvmjYQu5HQMwogHTEjqkSx1w7qpujZZs3cssbEYGxlpqq/AHC9n3xE62+QKA2ZncIX0JLaq'
        b'mLiaYM8haE+KJL6pwtZc0ktrhWdxZr9rBJRl5BMy3rVlUXPjCoXx8UT1jFRchTvxMHuJ7OcmsuDuELUeHiZgLTdxIb9wBStzDwckuxEMVGHNNRsi7pwClzhvQoHZxtSR'
        b'HYl5hSWwHEI/B6EzkFz0XpjJ8cUHZ0RacQFXXc+6Q5s5aUzyf33ccMGfLLgZ+UQHMuXao0gy1qXjyV4r3XNaoUCCTZQOJo4kObpJrMwEaQ1XrQiI24kzF11wQYtM3Uhs'
        b'kUvzhEkT7PK0gyYe6bY+AcvhppxG3uKTaym+vmQIlPlHuBhhRVE2mddrOOpBfT8HvbL4xFk6g1TOJBf7w/CxaQmUkt93b5+3knwYtiaKXq1Ns1H+G9fgLjxmI1qDsBJK'
        b'DSQRGWFjRWTnDsOIrwZ2XA01i7ajpt3DCVe8eQPr8ZEe9JDx+QCqzkFvBFlbj2ykUrMdtWDWV47kfooy33EkylZkkAysKWFfDPliN3GWlEu9AzbqSlM7h2Vt8EFxKpmA'
        b'FfGFcNuNlHI99PFwTksWu05reWsRw0yZSyrr4/LRCGhUPCZDqPkYS33ImJlkmHYAH7BAvvewwV4x6SSUnw0wP5SfLodrymeKzAjgyTB3zzwJDTnY4hhGTjWzQ+ddUouJ'
        b'P6rNYFblcADJcL8mPJaDxcirGZY4ZkqoRX4dlJ/Hx4VyWOEVRnJRTo7JGGFOEzktxkTwNgO8ryDHS9bE2uj0tJhYJ+wMUOR6adB909AkBc0qmiRvLbCUruBnZYeLBmwI'
        b'lBR3KTzRgSX2/m5UT5+cvrr4o25Ew579RIt+eKBvkwVNgXtJKurJ98krgI791A8VfvjIVZ5M+FWyC7q9ijRxQOG6JLWg2Rs61WSLSeCa6VcTrFtlXbgKPcbkUpapHgqB'
        b'R1rQrXzQTeEK3vLHcr1YaRwNh+ZU6rZJYqT60Cg2bIqjBWzAi/p+laB3lnREGQ7ZYtX1WGNS02QBnaa894OpMbfO4GKRLZllMEzi0kKauko+Kr4gmgSyF5guIWt0yJna'
        b'tl4Cdw2wOYls7keXiGOmr2gRY02WYOUNqCYYJ8vjViS0WQUXvEtmkiX2Gr4Ug2NsXKrhDGlggq/0o0ahSibYSCJwxuQaXe7WTkmQ1cIh7UMm1Lfr+CAFpqR9L9AjFsk+'
        b'GpZwxkVdWMfRg+ny1J5y7MsH9gL4ZrQrNPOhVYtw/MkV7AiAAR4djsDjJFI0Y9cJFhtImu5STzTJGeCgP8HoJBG+DpuLcR1WXYVY7QyrNjhgEoS1Gewtlx8bqEo8SaQp'
        b'30eAUq3Ax4kkHWL6hatGJOMrDiHZxG1Dao5Ut2Z7DWzda2iBXfu8yFggwfAkVlgTpuIjBew8YozDAnIby89BmSeuHINJ2ULClhayfe4RLg+yme6PpeC+ni+0yZNvMGyv'
        b'BP0eDtDhRHZCuVa4Oo7t3S8lhVWnPLFaHm95niSXeNWWzKtKF3yolIOP7BQCHGHACVs8Du+B9WNEl3no5JPkDxHWVxRdMFJma/lXCAxW4KYR8fo0l+yyG5cdiN1aQqFc'
        b'XsQVK7EE3+sX9xEkdGNlNhFuhEHBI3uyPFqSU2HwEPEzG4hvwRpNnHcmn6YpBaqkYCDVCMb4MON+GBeZf46lpwjBFgKvkDZ/6iRFVvUg1JljmTXRZkYDBkqgTYXYsmoP'
        b'e5ssWSzlnBJOJd91VcRWMhykrjADqEztQBZ5e2TN3yKEaIIRNew4oVnIplaEEfE64fH5y6YwYQNPvGHQQhI6jMm46oqE8Yvk7kzDoE0smT+ktJ0PZ++Hx/5ml3DAFNr9'
        b'YcTK3gvnyW7HNj9j8mvv45wD6bdxJiIdYaonnMjAnrTF9QgTAra20AuKsSXhOlHEO1VYeiCQntG+183wWAlbsF51EcexT9ZCQjRyJGOO9a/EUYYGY8s8qBOPNzVQ29mG'
        b'ARxuNqHpJAeWuFhjwRNFIiYoemAYwMaVDnHsifCtJnxRNG9ioCdspn89h8O151BjHmCdA3aLI32Xs6kYbPU8n8P15GjTUSt0G4rX4beS8A49HyjDtXSsSYHeF1v8lkGj'
        b'cwDbRsuRk0GwWENeWJOoFvHkXmFtIN3kwolIwYZouCVaY0Ei1AErL0bXKHs9CdEA3KUC2YLmIpjTx1oLui2EgyO6OJCMDeImzxF3rGFtkGiM7RQbvcL+JNE9emwq0PNh'
        b'OUWC7w4T6LTgiuoXoggNAf5UmhWHlFoDOVd9sCq6wsOeky+H5fSJC7vwno0F19uCG2zBFUUz+Fo+TzSz2N7bwOZpQjTHgic6LW8mIT6d/Euf97LixFGlvTyen5T6k2FG'
        b'QQwn2EIimIoSxT5I+0tepmQen7T3P3/zW/fufiVb7ZTyl3uvvPPt+u8vf+Vy94+evXvtl/oyZop61nc0uKrSs/yaZvmaZ8lt51RUf9Ad8J9+T2PsdL8bqhef9vWD2T86'
        b'+MO133xTe9x/5pnfusJX+7YSfSuSWuq+mqx9z8Zx3/cdjVscTb/luPds0ukfJZ5f/NqtjL+YXn928bjKlwc2r/xY5XsGZ37o09Mw8Zs/hU5MNTf/ecnkp64RX/k1v8cu'
        b'3e1rf4y8+8OAp9FdqG2+qmGsk/zb2N/nKJ2L/OWb8g0/j7n3EP6oZzOp5PpWuvZ7btExivO/DOs3dz1dbvf1pxNfPZmZ6Pbjrj94F//m5Ha44F7nVOc3khN+Wta1+oPy'
        b'3KumR8PfiPAweD8vpv+rBRsZo7ysiuvDk8K1b39DqH/c5leW+fL5dREBnv/0/v2ct7930m9saK21tOZbKvmdIf0tVd/4lsMz/o/jPgiVa/3GtbgfXdD9sd434aeD+7/3'
        b'Vs225s/KSvhNHf9h9Egn5cpPfvDuz7/8THu1vi3ij0YNOXVq7wfm1KQUKh6w+UDD8IMOg0FrmZUjkh/UHHE79zslp9/prH65819+nSf9u5wZ7H4/bSui3+bXhw1LCwe+'
        b'YqEUf3ZvvP57fwluP3WwUjPijy7/nPeTJU7oH518gxQHv/bgp1p5P+P0z8ddUTG7KF2poumRfWp19dBvJxwfKiT/dmPU7WDWV0oHq796SvMn7zzKd/rZN969GDLZciAl'
        b'+vu/ePKjzLfq/8Xl7ZZw/vBXZN7+RVzMvWj9A1tVE2Zjmt94atZu/Lu7v3cpfffaO+/6XJ0b+X7mu9K/0/rB/t+UuW7kDHB/sRg86rmN7vw0ZbOlO8HLVfeMDX4kOTX1'
        b'E64OuGS/efDAGza/h4r+uf/zR5k9cvlyB77cdejfByMvFoy+P/nTG83zX11I+3mdQb/D1sF3Z5/2Bfz78WGv3+mO/+yyVeq//nEtruW7y29Uvv/jVIk/fc37T1YeYfuD'
        b'nPYH5O0PkV+6Hj1kGj2iHj184OzMe5amd7595Uvffe+Mwc4b84XDd79ve/xc0cR/jh40fNfw1yvhp3PW/71/2izyu9+88HPXN3dKpC7+Uvbb//mX+az/bCy02f9nu4ua'
        b'l5ol3rGQEwUucNMmZ6I2UARSJHqNWG95RhQ5VeUKPPmEneaGcFUGWk+IFs/fEJJD8jKAgQvcfSWGAR9nruP4MxZGE5cUFORzBbICgo5aJTKoa3MLFEjrL/E4ekV8GSQT'
        b'ULRCSYD9l17my8aqK7h45ZJAiqN1jAcPwmBEVBiMXDmTd1nhUgEuKUEN1CnJKEQJ5HBW6bIkx0KRj1NOEs9sRYAoNH6Rj9pVLc4rzgl3XhQdxJeCFbJ+REsESnBUV17m'
        b'RWEyMOWKoxJ2YReesQgxxmQF1eXBHZlLVL08olMnadHqTygRH0mx2Qn+z0xZkebyL3c8uEE+3cfj2OIjH4uw1+dwy/wDJX/3yex//yQvjCMKfnDsM/4+fbb958zD35GJ'
        b'jc3IjkuMjS16eSRa0rEo/2GMuk/8K+XsnuZyBOq7fGlZzW0l1aq8RsfqK3VX2o1riquK2/Pa8/oc++KGDnQUdReNneq80X5j1oQ+ucvGCwXLpxYKH9ou2L5x4o0TX1V9'
        b'0/dLvm85Bm44Br6jpdPu2B7XfaBDtlu2z39Ty3ZWc1Pr0IZr8KZm8EZo+EbE6a3QM29pntnQPPOOhlGfKosRuqFswmI6RnJ35TiqwkaPu+pVx6uO/35Xmivrx91WNWy0'
        b'GVbYsPHeNPLZMvLZVPXdUvXdUPBlUQ7kOJpuVfLb6kYbe/031f2r5HZJ3C23NA9WKbzPFtCf2JAxEB0coYNdKZ7skV3OpyVyyrL6u5zPT0ykZe13OZ+fqOrJau1yPjNx'
        b'lWSZPzNR5Mvu3+V8ZqIgw8r7/ESoLKvHmvBfSvZxtHWrBLt8by4781emoRKGsua7nP9a0pj0Afv37MOzJ7gcOeVdiTwJWZddzt8//UCUPhMf86hqdRrPK5chSb+2ZTV3'
        b'Ja7zWG/8o6QfiNJn4mOqsVadwYuK80W5jstw9Aw2ZLTel1USVT9FQlZ7l/O3px+I0mfi49ceKMoVTpTS2pXYw4Ttr0g+YMkz0ZG4VHER/txYSVkW8fL/p/8+EP979tFr'
        b'J+RFYhEjLWuyy/lHTPv0PhD9fyZKX4qKKMMxJVHlQyVZ5n+stD3jA9H/Z6L0ZbVFGdLlRNU+K8Uy/6OnH4jSZ+LjF80QXS5WOMOVNdrl/F+nuRJHmTr525LjElyGqZ+Z'
        b'SHFl97KjT06kBKysz0+MRL0WK8E00v9c+oEofSY+fkF/0eUTkmLRlZK1JlH5fzT9QJQ+Ex+/FG52+aTATJq/G87dR2koV3xsTunp52fYcZoUaR4JkX6S2PWVsaBTkR/J'
        b'+npaIHWCL0M3iNIAmQAZffrB0g0Z7d1IZY6qMTNrvLjitMpjW7R5tICdYGkj9x3LI8seW5buy/lblif+Vdm4z3hL2aTv1KZ44ai68X9jbr2/IvcuT5RV6cO25LFAOX0e'
        b'R49bcMBCx5P3PFK2c+4TLue/MaDR/2NJnjMlFz4xktx/yXHK/SlbwPzSZ2L7m+YlsZ3fmWMUxuVyldki8v9NPpJ8YeHFGYu/KSXrocd5U0/Rw5KX5vyjAG5eGNH/T357'
        b'M+v9QiQ8lMtXU97brohTyZHvNNc5sGyadQPUrnwvrbPM+M2ydwN/Oginrnz/XovmX4Yya1X3xFT+MuIPaxNF/9FkUpuR+1XThmI586GqeP+xY16Wpzos74bec5w49ecY'
        b'hR+e/MH3vFxrO4RW725H/UTp57//U94lx6Dk3058YyPaP+pw0p8v/yplEL0828I8GyY7L//CqpenPjtz/P/Uvf21verzo6qXf/wdia9UeNlqtS5nRf6oc6TrTPg/h0Z8'
        b'x/m63TfD7+wdLJn+Dz1/lZ++VdJ4MLzFxsI76kzdH2u7rnxp8Oh7I3+Rjv9B4Jda3JTVXPz/4rL+S9Wv295X+HVret4/BVb/qj76x28Vf0+qzXjzmJrGty8MSkpn5r8P'
        b'uG9xVmDIfSzzsFbm2raPkoNiThVfUu/ftMx+MljldDenXv7cQJ1c6Ll/04lIXH7T5hcnPf/8b/la61I/C7x/TcW9mPutzoxvZcdZGIpi/Bx25rM3AyEhotCS0hx5aCiC'
        b'OQkck4IJ8RY+ujgZC3MBITb4kOVji4NV8AkP+vfhLdEYmwdWwyjUQoN40yb2Jl2ao6jKZmDyDLDFVxwrow77YY3tRhqEg7AkzZHiS8hAm5ZoPyTocWHRg6Q43LA4HOTg'
        b'YI54w6o0qDlphfXmLDxmnYYElyNrKwGdAUdFcYU09WEGa4JebATFD+bCrBy0iYNv9DqJVzTbPL+qiDXY48MLdton3tNrwsZNFbtf2X0L5uCheM+jYewLxAVNcblBfnjH'
        b'wo/PUcUWHjzGh0Wi20tcqHR/6+ADTrawxuVIY7OElHShiFz7sEq0oKYpwNGJ7g14vhmWMe9IMayKKI4TJbgIlTjHcvgFiTMo4gOeQ8FpUatTYAxv8nAIay1ZDFYeh3+K'
        b'C6uy+WI6rh49he0yLFhVkDWHw3fgwhR04P3nsZ6u2kfCHSsbvMP2dcvkwjKWYb9oYPUE9uKKFdvfjM0kDWSPDaLm8zm6JXy4hQ+gXFQ7U1zB+wGsWtR6rOMSQ6zxLSSw'
        b'0Yp6m4WAUGVrk/JeySAnk+QnAbPpVqLHqOGcjjzOKeGjPKjGpRxcuAS1SgIOR28vtBbzpbXNxdFPJmDMRrTrmhUrikOPeVgCnRI4ABMhIhpn2RcFs5XJr+7Lp2f/jEEy'
        b'WwEMYwEwbU79W5PGqFwn2howxA/u2AXbWEhxfLyki3Gcqiyi2U2okJbHWVzgcriGbBItB0eU8YHoOYeK/NhC1aDAEDlcIXAq5uKQ11lxtNf7kkXsms0NqGC7a78Iu6JT'
        b'wKcT1b7ilqyS5JQTyWvYjniB2LhfgiO7T4Lk4TYOiKKz+mEp3LXyt7EOsrHlchTYvGd1nlwCVIruv4jthhczA6hnAmypBBIiqr6aEw97JHFJ1CVwM9HNytfakpXOOuQ8'
        b'9mMjWzRfilUi8cE5+m3F3oQFwMgZDrbvO2Xh8fcY9f276/8v3J7woORTxmj/WtOijyM2LdKy0vKfD8fu5X3qcCzZG3ocSbXSYPbZFgjfFhi8JTC4X7gpMN8SmJd6b/Pl'
        b'KgNvBW6oGA8f2uRbb/GtN/jW23xBqR/7bPNVSoPYZ5upYPbZ5jtufPp3m2+18UnfV27/+IHGxovvNt9245O+23zTjY9+t/mWGx/97kpISarvSvBktbcVjDc+9v39O0o6'
        b'zM/T/jDZVtCqCnzxIUtZVltEsR/Ka9BlKutlsq0srJJkH8okqc72MeMbbHz0u8033vjo9yUNd6VKDksy8/t///2d/l0vILgUkmFoz1BQXeq4Hgd0uccdOKCneNyGB5YS'
        b'7Niay45teOzYQcGTw4OjXErF/pH1Di8jKSu3g8RtRzK/ICcjaYefkZaXv8NPTEugNDsnKWuHl5efuyMZfzU/KW+HH5+dnbHDS8vK35FMJi+A/uXGZaUk7UimZeUU5O/w'
        b'ElJzd3jZuYk7UslpGflJ9CMzLmeHV5SWsyMZl5eQlrbDS00qpCxUPC+vIHNHKi87Nz8pcUcuLS8tKy8/LishaUcqpyA+Iy1hR8FLHD4tKO4ilaSQk5uUn5+WfDW2MDNj'
        b'RyYwO+GidxrVWDbeyTkpi+2TsiNIy8uOzU/LTKKCMnN2+N4nT3jvCHLicvOSYukSC+a5o5KZnehyMDYhNSnhYmxiWkpa/o50XEJCUk5+3o5A1MrY/GzycLJSdniRQYE7'
        b'8nmpacn5sUm5udm5O4KCrITUuLSspMTYpMKEHdnY2Lwkolts7I5iVnZsdnxyQV5CHAs4uiP74gc1pyCLbZTyoRuax/Zdv/Bf/jMy+hAiRYksK6OK+zkvq14HTCUu96ok'
        b'c0n+N32RfrG+mYmsx2HOm4cVj8vw/iCTTDKSlJBqu6McG/v8+Lnb/Aed57+NcuISLrItgVisQHYtKTHYQkYUDm1HOjY2LiMjNlbc6aKAad+lDt+RyshOiMvIy33KxjX2'
        b'kxCLg6yJIskxJvmDjCvxd0FGknvuIWkW6JA45TolhPFc7q4En8vf5bBEgSMvKJXe5ccd4Qp3Oa+kvlfIj1B5W0b3LRnddv9NGbMtGbNdjgT3wIa1+xv73tj3pvmXzDes'
        b'/em7LaO8LadRZb2h6bQpt39Lbv8Gf/82R3mDo9yotcnR2eLobLz4iur3/wGiWHIF'
    ))))
