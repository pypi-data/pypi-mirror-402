
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
        b'eJzEvQlAk0f6Pz5vLm4IEO4rXEK4LxURDwSRG0W88IBAgkQRMAkqeB+VAB5BagXxCJ7gUVHqUbXVzrTdXt9dELsi6+5at99u2/1uV6vd7rpH/zPzJjERtNru/v6IYd5n'
        b'5p3zmWc+zzPPTP4ATH64+r8Pl+CPPUAGisBiUMTImC2giCPnLrECw35knJMMG1JaybgcIOef1MesACqr+RxMEch4hjSbGPxsITe+w4A6vlW5RPB4ifXMqdNTxMuqZbWV'
        b'cnF1uVhdIRdPr1NXVFeJ0xVVanlZhbhGWrZUulgeZW1dWKFQGdLK5OWKKrlKXF5bVaZWVFepxNIqmbisUqpSYaq6WryyWrlUvFKhrhCTIqKsyyQm1Q/D/21Ii3FVQANo'
        b'YBo4DdwGXgO/QdBg0WDZYNVg3WDTYNtg12Df4NAgbHBscGpwbhA1uDS4Nrg1uDd4NHg2eDV4N/g0+Db4NYgb/BsCGgIbghqCG0Y1hDSENkj2AI2HxlfjpQnUjNL4a5w0'
        b'3hpLjYUmQGOn4WkcNNYaZ42txkrjpvHRAA1XI9SINSGaUI1Iw9fYa/w0nhp3jY0mSOOqEWhcNBwNownWSDSO5WF4TCzXhnFA4yhDf68NtwIcsCbM8IzD4YYwA9aFrQuf'
        b'CQJHoK4Eq7jzwErGaouEk1dmOrbx+L8z6RweZYc6ILHPq7TE4WO5XEBoMeXjar7jzga1gfhhvWg2akaN+TkzkAZtz5fADtiCtmfOmh4pACFTeeia60QJt9Ybp0T782B7'
        b'dmZEZiRqRNvghWm5fGCPmrh5JXBXrTtOANvQtekkAR/weAzaCE/Ag/A1dK7Wl0TuqYF7wsmbubmZaLskcwzaxQNOqJULL7v7STi1PiRRJzo/ITsuHifIRjvyM+GbcAsf'
        b'OPhzx8OWHFoJ2J2FLpIUmbk0wal0UonXubEzUIM+E0e4E15VkXi0uxAXh7YxwDqTA3uQBrazbUavIa0NOueAzqtgI7pYg95YDpsdSorsAPAO5FmI4VsSptYVp7QUVKLm'
        b'nCy0jQu46G2Gq4Ady9AWHEm4EZ5Ms8yGp0NxhzRl4x5pzKdV2h6dFykRgGmzUdtUizXwHLqszwzucV+JenGNcvLnJPIBfw2DjuSG4EjSeelwK7wQnhUZUYxeyY2MYoCt'
        b'C9c6EnXgaC8y6Ogyej08IyIMbqlCjTmkTTZIy0GvJ8WWMSaDn2AY/Hfxx+74BswAmD95mC8FmH8tMc8CzL02mHvtMKc6YM51xNztjDnXBXOrG+ZbD8y9XpjffTD/+2G+'
        b'9sdcH4h5ORjPBMLjEk2YJlwToYnURGmiNTGaWE2cJl6ToBldnkC5G8uKRhsjd3ModzMm3M0x4WNmHUfP3U9Rn83dPsO4O5/l7o/mWqRP5OCuFJfk+C8oB5QY785xOgxI'
        b'qMT2CmYgSnwv1co2hyvGtJLKRZJIljg9jW/9mCMEYHJJ5W6nOtANKq3JmK125z1yApPvO9/2+RvnQuw87nVQSQTq0ZI2/3NMiQNOH3dHWZCay5KbKh7GRvqE+nGm32X+'
        b'7f4vHy4YArUROKIIHgB4ojVHzwgNHTMRNUVnYK6B3YWhWbloZ0RUZmRWLgOqHKwmlMDztVNJyfslSpVauWJ5rQpdRD3oDXQOXUBn0XnU62Bpa21vZWeDGV0Dt8XFJMSN'
        b'iR0dDy/CHh6Ab8+3gufRHnQaHYc7ajNxTtNWw83ZOVl5mbnZaCee5dtQE54bjWg7rk3oqtiIsChJZDg8A7vgqQKcyTn8cgvajbR4lrSiV+cA4BZj5wS3wC4zTiP970YG'
        b'QkY4jUOkMOY1BvMXv5xLOQGvIo08IydwrczGGYe5JmPOWcfVc8JTVCMnLH6aE3jDOIGXpyRDqYheV8FVZeCQC5jb8VHyfv9XYptbGK467vWtTb++N30G0r63TXLZMz21'
        b'Vnb23uyZH/d9uO+9OV/seK/qmOfWT3Om/8u77du/fWJbfjfHAkS9bVf0G52E/8gDZ2cxFou4Ztx7O7FAQF1YzI1j4FnU6f2Iir9TfJdwqCuMwl3cGMEAAdzBiXRE5x55'
        b'ksjDOOHZcKSFRyNDMyI5OHYvJxJ1w+5HRDSUO0nDx8gi0facWD4QFDF49DrR2zQKnkZnkA41Z8DToAS9BThrmfQ0RwlviBMqUWJ+BU8+VKQnxBs2bHjsklyurK6XV4nL'
        b'2VU4SiWvkU4c4tYqZPXkg0NST8cff9sA7qdzgMh1z9iWsW0JrRM0aYPOLuzDwaT2pI7kAefQW85R/c5RA84xJNJtT1JLUpuiSzTgHHXLOa7fOe6Wc2K/c+KAc1KfbdJD'
        b'MjJKC/whEQxZVUmXyVUYAMiHeFLlYtWQRXGxsraquHjIpri4rFIuraqtwZQn9ReQiVoixk1QOhKiE/6g9U0jsUS2Pd4A/jqVwzA+n9m7NS/dYHOfw2dEt22cmsd9xnPY'
        b'kjto6XDb0vlvD7B0FRqeHj8kTNEqCASHbaK4ZZyRWKic8DBXz8M8ysWCcp6Ri/n/MS4uf5qLrYdxsWNerQsOo62oWQp3cFU5fPzQDeDxYvhGrYjEHIY98NXSUdk4hpEA'
        b'1IA2CekrPAaehr2YQ3vzcQwfYDnQ6UtfyXQfDTfBHaiZREwFaHcubKglvRsY6rAiyQav5IwjgFfgebiNLbwHdqMDFrAhnETNAKgDXfKjOcGLaDM84z4hPEoAmPkAC5lu'
        b'ppY0ALbBIxPdV6HWGWTQQC7aFEZLcIrELWkVALRPBiJABDxpLbFiczoghKfHc0A0ehWgV/AvPFxK10nUAi/Aq6s5AL2FGgA6Sn7hFTZqEzyJy7+Cs9vlC9Ae/AsbltHy'
        b'sTjbYI1wzAJvgC7i37ELaDHz1uKXrnAB2ouuYgyDf1evpxEluKM6EI6JtsMl4d9YtIktRMPH/XjFAcC3SL10+HclOlhLODIjD76NDnNA+mqMP22WodO1hG9D0aExM7lg'
        b'3BIQAkJK0Qlan2moaSxqtQDoKrwMYkCMCLXRrl2KDqHe9aVYtO7B0wTuBMWVqIlCABXchCVLrwpq4X7Uu4IBHNTFBC0CrFCLUb/JVb2FQ28vn79WG2sPY2yn+oTkzi+a'
        b'G/7N9dj6za+rTwQf2VYYln3urPvUKbaaV7y+0j3alWZZmMZdlPzPP/6luvhTu7nff3CZcdoSlDljyt6Cj0KPvzdhZcpYTvnotx9nqs79/l2PsPQHx7pkE66/bX1km1Ze'
        b'8qDZ5e1zJbt+f2VpRfiGZW0qKL1z27q5tbc4/O7NIy287F/7Wc0edTD+1NLEj+1X9km91CGnZaMnR68p/1/+2s5N9z5Xf/fD70dvdP1VI/fzX1hs3x+Nzi3FkpQsGslj'
        b'4abwKAlqwkujYDm8Bk9x4tEhGRWV7qiXh4EQ0mTm5PGBDTzLgQcr0H50tJq+Cs/CnWWoOQJjRAxRBYLkRZzAXPTaIzGJeyNrHl1kUROGfXiJu7IYnsriA+cELtqF9k2i'
        b'+aN94+FVKsZfgUepKGfleMZ8ieVTAvWZHyoyJGIxkVR6WTVkI68qq5bJi4mkrTd9oLL2JitrH0zHstZl0M1dazno498l6im8LnoS8PZ7wOe4+Wum3RcAR6c9Fi0WrVaa'
        b'lNsOHoMilz3TWqa1pbbmaJlBV882aYti0N3joFW7lS6oizvgHqFNuc8Fbl5t0l0K/LJv8MGF7Qs7ir8FjJ2kxUrL05aRLDJbMttkutQBUWgLc5+Lo+4KvW4Jg/uFwbry'
        b'LumAMEaTMiik5epSfu0+rm15l2PXkhN+ex1vuI8bECbhWGcRWRpax/XZev/9Wy7wSFLZkm73skoFljCYhz9Z2W8xxKiGrKuqi1VYo6uQq5RkXindRuhIC6PI18t8Mo5m'
        b'/ZdpIvu/z8ey3+tlZf+rgiBwxCb6RWQ/QTB8M9n/n0MwFT+OYKxYLHtnmrPrt1yCYEq8dxQVsgg1fWXmil6OmMHdFTZ/bRFIp9SvHIRVv2MmA1BTkuO1WsImXbzEJucL'
        b'TigAwpLKyuQsQGWXct3s+BieBF3DA9YKSuPCFL/5ewVPRYwG/3j9aMdHcfs3Nna2vtm6fHQg1/1ITHl8bIxIdbgxTn4lJubhWFHsbM5753SlH5SMfvWb0v+ThTlxTkjf'
        b'Lxz4kBd/2r0yzzrberOIqy3PkO4u7eI03dp0BxYgcHF35PzNG/3bNvbywbT3XPpvb5dwHhEhCHeicwvC9UhokYpgIdegR0TRmYu6loZHZUaESaIwLkaNADZEAncxb9Gi'
        b'BAn/2fORD1jko5+MjmUV8rKlxWVKuUyhrlYWY9gznEQnZol+Yqo5QOisjW9e1ebftKZdpYvvWNUVsHftoJv3oJPLHkmLpDVck3rbwbVNdXBd+7quxTf9xpA4/E6KdorW'
        b'oi2wrbRteVtIv9Afz1jnIN2MAeeQroR+5+g+22glGWTDxOCWKWRDFmXVtVVqZd1LzItQMi+GN2K+6exQ4dnh+RKzQ0m04WGonrJkqX5WUP3xCaZnzGbEz9XuhmF6/rAZ'
        b'kcbOiEg/ZxCE//YpVi5YO7FSz/w+1o5ADEDi5GnLbd+pCQOFdDlGVzJmxK9X4VAsiJ0Bz9OkMWo+0QPFYmZZTre7Pzsl8FLcExBvDffj4uJAXEQJTfrrGaydpCd6caVm'
        b'bSSodcAPXg4T4jNLOMS8Eo905TThKIUdwAt3qDZRmbPUIxiwOGg7vMSPh9vjBEQbT0BX0V6Kg9AZ2BEcL7PGvT0ajEavwy6ah6eXCOChFV+fuji5rnQlW68pYfBwfHow'
        b'7o0xYAw8hQ6xU322N0jExU1eWOIdunIJW1wc1tYOxKN29DYXgLFgLGpbSBOvWeMPsFRI3GCxes2HhVJ9e18ph5fjYXcF5q5EkBjH9uKM0GCAZY14Mn91wFeuc9n2hlnW'
        b'wt5qIoLGgXHlqTTh9WoJwEpDDJi3MiA6JxRQGDUTnpmNQedxuB33WRJIQs3wGE09Rh4B5uLqikNqAwbccTeSXghGB9FlFbxYhxNPAVNS4DEWvF3F8PGUyjoad3AqSIVb'
        b'MTwlFV6IEekFFTwQgzszDaQpEmkmIfAC0qqkqAP35VQwFV0No1VexPVTrRbiTksH6TXoCE06nejCKngwE/fONDAN7lCzg9GK9auNKnS1BPdEBshYGUyLW4YOQQ3qLSRo'
        b'LBNkcj1pC4vwCLSjXngCHce1zgJZYfAqO9Sv4mHci3pR5xJc72yQncGhuWNd+bVS1Dt3PK51Dshh0FbaIfdWWgC8XAp7VtTb/k5qx/bzijmWqHcqBnsgF+ROYPtZNsMa'
        b'4IItYypKbB08ItixW5QVh+twxAG3Lw/kVcAOmvSIfQguAgjvFq0P+MekySxPoANo72rUOx524Fbng3z4uitN3FePpwjOtyRjfUDwqjhAZ4tg4kLUuyoW98N0MH0GPMWy'
        b'Wq47HmYQU7N8XfJXISns2PHC0WEbtI3g+xlgBryMdtG03kutAM4oRjdNnVORnsDWdgY6ChtsUlAX7rECUJDHzqwdjAPwxghv+rz1tg9E0WzS+MzxNlg9PoW7cCaYORad'
        b'o9TlOUKb+Wgz7sFCUIgOwiaaQWGFFzFxWU4PUqwReoaz9QpDJ7NtIlAn7sNZYBbmv1a2a/L8QDIuTCtWeyfPV7GtXbUCXrOxScWdOBvMRq8raEo4KgAQDVMXVcl5K3g+'
        b'm2tc1mwbeBRuwV04B8zBLKClaX8T6YrVGCDsK1+TLPFLY5sQA/eh121Q7yTci3PB3NqJNOnQimiwAFfgvmx1gKaYpxcPrVJL2OyJdQKsmoB5GPo2sLMlazSowJNQuETq'
        b'NLNoNLuOt0bHAWJe2bBaEdcQWMAS1ZIYUILnb4lfKefAmLFAwjJdxTKstDTDowW4x4tAEdpawU75i+q5sHmmM+7d+WA+Omxd+bcffvjhTTselYZg8SrbK0Vj2Iz7U3EA'
        b'N+360nVO7yavBYrACnu+ajLuVvnMK7X9H+ZxUoSCuye+at84Y3kxWGkx9t217/jkrLFyeutfjY7VGZtS631Lto0tvbqq5av/fTe7KME2Nvavn/3pyJV/f6P+7vjjgOZD'
        b'aZ+vaPsEXBM1LvGe22Kz6aOC89cerlY/fhhuseLz2Z/+4PKXb+Lf2fib0iCtaIJtI5p+z7LgXuj77y7P0bS2OR2PDfxlaV5OR+X7st5R46vP2Yy6UnEu+7en7vRW3ggf'
        b'9daSG0vvv+f96/fsKpvmD7o+HHS0GXT5vifad8N7qd6Nv0h0zF8+ynV51KK7BVdhbfNvtnndOfRo2flxQUGpf+365t2/jFkYvljyzR8nTPii0TfiUJ/17gt3xy78qrpI'
        b'9Xmh8/p/HPv0bsg3l3f/z6tBf0e3TsmjUzfv3pS7d/XoTp9xQ798VBW98o9/c5hgXXnw6w//9sj7U9HMVzgnU6pPTLH764F1YNZaaYnd+1jr8SNjr4WXYAvWXfJQI2xP'
        b'zsEAh8EKzkkOeh0dRlcpMprCuGNc5IcOG41EpbCBvo1eg81B2Wh7ONqeG5kVgZoyMvnACV3iogbUgzZTGxTW2/ctwLrNtmx4ck4mPI2ndyLHY+6KR8QEn8JBe1XwdEZe'
        b'ZCixwwdhFX8nFzgiLRf2WLv8BOXHCE6G7PW4pLasmOD2+qeeKdJawGGRVgbXgLRimwi+uuvsqlW2Mdqxeya1TLrpHDTo5mUCuTCM8bAnMGvGfS4JuXu16UPiQJ0+FBre'
        b'pQ/FxPfoQ4njLxWwoZS066VsKCv3AyUbmjm7b24RG1xQ3Ccto8G7tBQ+CdFSaIiWQkO0FBqipdAQLYWGSCkPaIiWQkNsKTTIlkKCRLcT4XIs2LCHd5sx7B+kKzCEwyK7'
        b'Sg3h+DE9SkM4edJ1xhBOY6YxHxifcph8pm+6MbNCZg5Ditc/LmRKGFIF+mhJqlBw34oNe/q0lRrCgaN0SkM4IrqH80AfTkq+HvAtCWsy79sCF1fN1PscWzufO36hXc5d'
        b'M7tKu9wH/OK+BQLH2JZpGBGrsYrbFrur9q67j87rln9cv39cT8KAf+IlHJrQ7z6hnU+a7qvz6Ero9Ot3j8HPdvjd+/bAJ0A3pT1LazXo7NtW1+8s6ZrZ49Q954ZzwqCX'
        b'GKu4otG4MiL3vz3iA5EPUW99brt5E13W57GKitegFJvUOIDirFInctEEBn8arJFczI3PxtvU9GgCt+Pwx9NsTEQxxdp/J1ZILsM4vqwmuksQAA7ZRHJ/FHOTHRtggrm5'
        b'/70dleFaqAWLubOybIG75UQMDEoitqwU6TF3S64NBievUt3yrnAaCwJRC9qbHm9tG8NjlUu0FR1TMHPb+KqZJNN3dcQM39k6jpjhT229sfCTHNv92/Z/crJzSYF7b7u7'
        b'e5N7eHtS+8y2me5HNjye6V7QdtR/nfuJDefO207+NGe0bc2nEbc9bW3fsd3nAd7dYh8T6yxhWGPQGSzxDhoUSR58hQjMNekS3ohyy2AeZ2WWJzu4KrWytkxdizWqYqW8'
        b'XK6UV5XJ658TR2UZ2aAhpvMpPMyMxCDemqxJu+3gpE1ortOLtUEhnuXaAq1lW4KOo3NsS+wXBj5XNRQM8VS4lBdn0UTCos+p6SZTdk3hMYzTy6iG5MUXYFNz1fC/yKbc'
        b'YWwqYA3laehtOxslF11AmzEjngKw3RqeoKy6e1bCihymj+zpxf3FJRekK+LjLzKqFBz1ysadLEvGGlhy2+S68py/i97/dPrCqXcwe+bsr1lnPfOCzfRXP/n92V0eob/c'
        b'IHQov/sJRqYLbSO0o/WGjBR4aIyB/QIRZb8Mp0d0L/sNuAMeDY/KhJcWPbFmUFOGR4iE+/TgkuYZWdP9KTX/CWM+M4ay5Wg9W043ZUuyZYNXVl3CTefQ7tQe3snMS5wT'
        b'eZhDbztHdskGnOP7bOPN2bDspdhwImHDZ9ar0ZQJ838SE76I1Y6vYf5LVrsXkJcCVl5+YM1qNzFjZhROU+ayoNqmgkXaMa7la6RZ61ji4Dq9J0Z6elLc7Eyg+JXTDp5q'
        b'EaZccr1JLXGtxBbXjbmTcT5VvqXvPBaXo23l26ZaT679ZO7N2NaUr0TvV44SbA34Xd4XomNhUYKtUeXiZo+I9z+xSgh012y8cPZIzDs5r3PuRb3vG/JLW1A74OT87lbM'
        b'tGRYR8MmtB+ejELdObkRHMDLZuC5uNksyDwK96ZihIp2ROfnou15mfAUD7gV8OAR/phEuPslTHB2VfJV6mJZrbxYJlXL680fKbcW6bl1AQ84u932iugqPDOve96A11it'
        b'JebZtlX9WEymncnvzh+ImHCduRGRMiiWdKV02mkzB93Euthdawfdfe46u2myMS5w925XdDEdlf1uYVrefTucoZnRjUcKHbKqlEtluPy6l7FHE8XwqdrvBCY2t/m8l9uN'
        b'ZG1uBp8t8iMwMFQl4Wke68+EuZqjEVB7tIXGslxAOZtrthfJszLjWxzmmfAwdx1Pz9lPUZ9tfbMaxtl8lrNz6rEeKg7EfVMSZ10rZpn4ijOxqAkYLF1z3nApBgqPD9/k'
        b'qMii8+rD3R0fjcHCNVIvXM/bjrad98mqzz3Gz2uuO/Aoa6703v5Tkm0n28X/5y5e+HHhx3c+nIEK+Z+vXA7+pxQlnNw6bvzWjZ2aK1tb8CwIf0Ux+uaEWSUPsxOlX284'
        b't2/0tv3eMQ/fWXP1dW77rQ93VPpus4s//NrRrcFtG+N9wGZX79wv+7HCRffOW+qKyH4QfDUo2gJw4CFmlh/qfEQQS3Z4anZmRHkC66wED2Ic0UQN0HXildmoMQK/th0d'
        b'LslngCXaxoFbYAc6SVWsIvgW3IZjNdEzYQMW+7xcBl5bglrocuAFL89GzbnECHEKjwjcwkxThkhsXlSzepoZiY+bQdEyTizbxXKTeWX2RKfVZv20qsHTymtPREtEa5Qm'
        b'ddDZdU9iS2JrkibtMweXO24+beW60gE3SQtPy2hjB72Du5j2XIK6abK25bsmDHr5deLpdjii3ytKm/a5m+dnQp82mS5zQBhFQmUHK9orOpZ0j+spPDmp3zdpQDj+oRXf'
        b'3V6TgfUDkbcm32T+WZH5hyddOqm+oKxWXV3+7PWFbbkVnYYlJhtsyjwyEc2a205SjsMf/8DzsBrPw+AHAH+8LCjfIwgBx23izEG50RJNFxq+EZQTNypQzv8vIJ5h09F1'
        b'2HT0Y6fjl8s/Bq9ixuxJiEtsXGfDTscFXqzBN8b+Y+sGuTtL3JPI2uZiBMkL2rxXsMS/LdebF8dc97GydWGJt/KdqIE9pupW/XqniSxx2XofanGO8a0qTBPLWGJyDWup'
        b'ivFYZncxNIYlRnkLqG0zxnV64p9WWrDETQmh1F4c4z/Vz9MymiV+MX8iWENWyXH5s+t4/iwxZ2EyWEUKylzuEppfzxInp48HalLPcUvG7568gCVen8laJmOiYuNuzo5g'
        b'iYfnsabmGMbdXhTgyRLvF7GbAzGCt0OGFhSxxN8tnww2EKIinP9AzOiJuezeQMzsfXYLvaL0bZ/AGvdjVmxblrVUyBI/CvOk9seYdalJ6231xKRRY6ndLKbOf6KV83iW'
        b'+GnJdKAjBck/jR7nspgl/jBWBj4gBZWV1UcHjGOJTNxi8Al5Pf5/SzfWZLBETjZrZoyxP1m2KmohS+TF2bMAIz2+Zu3UVSwxxmY1eESqNP4PkccL9MwQG8waDmM8Fk3/'
        b'Lk/NEre7BFIzZwwTuOAXWTZA4bxXxVVhCQdcJv52e+v4KhRju1Xx8bf/aH9714XJO/qPllVrw4WWWuATp475ktv1ZdEj4duyzKkrOL/hL3E4NPHbHyT99y/+m/HLke/9'
        b'Hfcfa8Yci/1fi31vSHJ7pee4A7pbj4GPbmeT7lPQVfRLqfhO+tCDvm8CPp7561Xu0UuC/tirurHVW5KTkWlXd2HU+QQdiO/+YvTKpWO6MqXSsrUTU46fPTI54MYKv4Df'
        b'N4/ftjjo9/Vz7i37x7S5MzJa3p2TUO46v2GL06md1eD4ruOFmj3C7q8/rVu08PGBy/sOfT7F5w8rS4JOvb+q7Y23Ur/+MnH9V39642Tzr1u8tpV/vuLe+pV//nzwX5zV'
        b'c7+8lD76QXVN/IP1C/oUj0Iuj/61c0HEnS8U6emfrvtUfvjbun1L8/7+znfX1tVfPJT09v1bQwUTD3496fzvbr12bvPeWzMmXqq77vK4OuTDj2ee/f3DsBOVFh/+263l'
        b'9KaAjTMkXNYbYT9qXkOxFOqFTeZ4agy6yKU+ZVhlvQA7syNC0enVGWh7Np7W8CSnbu0iukpNQb1R4WPHYzQWxgBeLYMa182SOP3E5eRFVhwnw4pj+DFZeByJ7C2VVi0t'
        b'rqiuVBCJXj+cRJeguXpTXw0fiNy06tZxmrT7AoAV4rX9DkGDbkG6QozT+oRhxBbm0sZtsaGOB1ppm3+LnPg26FL6XYhbQpdj14xulx6nbs9LnP7QpH7qgyB01M5oc2yZ'
        b'1TajZZ4utl8U1C8MImSRVtlihQOOzlppiyvOyrNNSbdjyRsFLRZtsTpO+1jdjK6Azjn9XhE9jj2lZ936Pcf1C8eZvaWZMujopJW1FepmtM/rdx3V5djvGtYl7XeJ7neM'
        b'ZiNL2+JaFuscWxb2OwZgihMpOgQHHBy1U5pW3vYgC2WKTtk1pXPlgEd0i+AzA2XAI0wreGCJW60tbIttkw4IxYNC13YPXWyHN24vDps+3sZtMiRjw3FtygFhgGmYdKEb'
        b'fiOuw6dfOIp9e3jY8MbyAaH/A8Hw4k1TxbaV4lQjlWf69gg1ifcky/+DRNMEuGednFkQoku54RQ8KHJpt9L5d9jicdMyGLg7iwyxA07Bd21FO/Mb89tSbtr6knBuY+62'
        b'/LsBYZrctqB+W79BZy8zXGE5xKuTS5XPhxJPTNYlptysnEPgxHD+fd2AKbC++v08PtZX74OXVFopwDddyHn6vw+bgMFyIicHNEARxgxWQGZBHQ451I5iVUSOY/BknC3A'
        b'cNyiiE8pXBOKgFJ4JhQLSuGbUCzlPKxCcMs5MsEWSwPmKLLSgFVMkfVMYFWO+88iRSZTylWqMoFJdS0NuGMFMOjYhvMVGAQRH3IO1UuoX3m5JYVCuEKN1kYoZEGhkMAE'
        b'ClmYgB7BOgs9FHqK+mwvyeF+Afw8djttL2ofT2yM8Ch6zR/4l8LTrLvc9c3NPNUOHDr12dcdH8Xu99/f+Vpna29Gz1Z/6gusfH1rU1ycWimKrz3nOu9oTHls2YwPZ7wz'
        b'95N37+g+0HIKuWVHY99R34orHXtta2yzy0z16G3pg//DX+E/3nX1m8ITWYl3D32yv/Kte5P3nt4qHe180y5n//+NznlQWTP61GTfO+/m2YsdOg86f/CHLVd2SahiMnuh'
        b'33n7HRJr6oOWBXehi1joZ8A9Xk+EPtoAex/RUw6n4GZbo6cxQHvQMdbVeAc6yq4aOnRBbnSgq4AbqQPdUfQGjfUOkNJzCXADfp/mjq5wYKM8keooBeg12B0eFUltVqlF'
        b'8AgnJr2U3Z/ago6h87AZ7kQ7syPhTrjTAti4wlN1HNSATk9kzVrHfNBZ2JyPl6S5sB1tD5fAEzzgYMVVT4ZH2T2oM3MENEEE7OYBAexgLDkeaBOgRUxC2+Ae2IxOzIrG'
        b'GlRUJjkxQXaxjnLRxkVwK9u4K5njYHN0lCQrN5Icc2hGW+dy0MUZK362IrVhg6kiZVFcXCVfWVxc76CfBVF6Al3DiJJP1KhVFsDLR2tx29ljUOS1J68lTzfmpijstrNX'
        b'u3rQy/dgYnuibu6hRT1OPYXnii4V9AVNHvBK0aYZ0iYcT+pMOpx8UxRz29nPQCSPd9y82+boyvrd4nriL1kMuE3W8gbFIVreq3aDPv74j/WgvwT/sR/0C8Z/bAfdvLQ2'
        b'JqLPZohbVqlSkoNQQ7wyhbpuyLKmWqUmuxRDApVaKZerh2xrq56YhZ9t8SB9U0J/TKwei4l0fLpf/kmSj8cf/8aysdaCYSYzDwH5fAnpSCXxPkEEOGUz1lzjYgxz3JvO'
        b'8TVgCRj+g+XWFgmT180MWRbrfagkzBBPJa8sV5EMxLT6jy2TK6XLSmXSifVCQxsMFDucTEW8rjeArrQzud25GwDt159UlwpcF1w+v5gMgYRR1pAeelIP5XLSjcOqYI9T'
        b'PNRXQXTGs9vz51ShnK2CVbFh/F+4Gg4m1Sg8s6h70c+pxha2GhbFLPO9cCWEJsORcCa5O3mkShhNriWAPWvCbj3gpe3/l40Hbp4i4Cs5owrAhDeiy452dnyUQJ0nO40G'
        b'23ds90WCZXt5Sb+dIWGoVEPnLYSmYrE3l4jFQ+i8hGMyGYnoMVpQFSqTfZ16F0PXmZGprCJineDtCkvg7t2WdjCrPWvALaRPGGIiMfh0QEYSA9Rya3LqYi0ZqJFLc2Ke'
        b'WPO/k1q+HDCixpYWgT/otIng4gWc/GBBZomli3SZvLh4yLq4mD0eisO2xcXLa6WVbAwVR1jCKatr5Ep1HRV7SgX5INyoXGqo9ZAdOVcixXhGXllZXCzh4WnBEkyPmTzZ'
        b'DJxslHfEFl1vQEPfk/gC0sot4L41mMykMYNxY77nOth5PwgAbn79fuMGXJM00/Ai0O8dP+CcoEm7jani8QNuyZqM2y4+/b5jB1wSNel37Vwecbh2oQ+5wN6VhuiA1LL8'
        b'kCFR5WRKsiKjBATGnLBegpfZTLTBjPls9H8fJuCB3u34BDjKGAIU54AeLv7vgP8L9X/tyF8Fp5yjfzb7f4pzUo/0KPAMJrAT4znDiUAhRnO8LVZGsMgjJ4MJqJQJTlmc'
        b'1O/DUPDJl1liqpUJ1YJSrTHVxoRqSam2mGpnQrWiVHtMdTChWlOqEFMdTag2lOqEqc4mVFtKFWGqiwnVDrfGGksF1y2WRfZPekeGQfApNwMwpi22xWDb3QQWO9D8PLYA'
        b'uYPME+eot88XCc362OGUl6Es2SicD/EU58q8TXrMkebjg+vla1IvJ0r1w1SxCdXZPG/83wL/tywnFN4pf0MdZCEYa3P0pzfJONlrHMqtZAEmpYpo/oE4/yCT/F3quHh1'
        b'CMUgv4wulY9DrE01ez2VPXRtFkP2ABVYKxrikek30mzLK7MwYVJ7oJeQW/DHbkvzA9lYVFthYc3FVWeMx05J1wGNADOcPRXhFmbqg6WVmXKAw5YmwtpinaVehD9FNVUf'
        b'PvPEvWfWKPKTWaVQK6SVinpyxrxCLpbqu0CBgZK0qowcUn/6laQaqVK6TEy6I0k8VYHfUtJXM6ek5ImrlWKpOC5SXVtTKceZ0IjyauUycXX5sIzIj5x9P5S8HCGekpkq'
        b'IVmEpqSm5s/KKyzOm5U7ZWoBjkjJyy5OzU+bKokaMZtCXEylVK3GWa1UVFaKS+XisuqqFVg0ymXk7DypRlm1EouymuoqmaJq8Yi50BZIa9XVy6RqRZm0srJOHCqT1yjl'
        b'ZVKcjyRKnFLFplGoxHR3F2eOGzdiXitwp8owBBpeX33/EUZKohUnIcNVAYb+x8q3TK585st6oMe+r3/AnTgzPzI+dswYcUrO9IwUcZzkqVxHrChbkji0uobcOiCtHKGH'
        b'DYXi5uhLxKGRa/wi+RhgGZuX4emn58fiKzY3NvwT8jJbY4z6vhHg2OTVBuMwvIa6XclGWEQU1jy3Za+Ae+YgTTbalssHfvAQD15Fx+yoadlyzE7gHbsOgJgS+3X5KlA7'
        b'FhOlYrQZNefCU9ORhpzoj0aNOJQP92fOZHOZlUG8EXNzM3MZAJvQISt0AV0V0ww10RbAVjyeC8QllTslVqA2GpCjc+2IbL1tC88mp7tyZmRgLVSvgqJdEtiNrsBOMDPF'
        b'Au2BZ9CbrM+zBRfwSt7DTSvJ+WK9fv89bRwfWE635IHJJbaugZNAbRRp7Wa40dI0d6QhJ/9xXaMLMlBTjgBr5S1gGjoqQGd9FAqbDU1c1df4vY++461tuWa/KUb4/s4p'
        b'f5+pTWy/75739oadUngjZvK96QtzSpaPX/GH1Pu7fF9xDV+y53dnvv/uytK/tEzayAhCBQ6PvuY3Zdfvt5pcP0r1fYZHdNaHewM31N963Oy69vxA/epRm7+43/nH5kVT'
        b'xq5w8v+Fd2uTXeVHXROUHq6iTyee+nXMX05c7/niT8m/3d6kuOX7/vk/Lt7xz3ff7zpc6fOvv34zri7k91fn/+mP/5x79eoJ/vllnx38x1yf3ht//R1nRsVSy4DVXmsP'
        b'Df7aY3djKuy82fmJ8F9xudPy97fnjT5qv8zW7p0FE8LH7iir+lKQ+R0nr/rfl1IOjx0rcWBNACcr4WUb3EmS3NrIMNQUzYkrBy6wgWc5GzVS84YlPOLKurkSH1ehvcHL'
        b'NTaUdTI4FYs6s6OyciMy4XacQM3esOAJ3+BVzUTt1EoxDjaB8EjU6PnktHT9KmpWH4OuVWejHRm5aAfcgXbSd+PjgAvawkWX4AlP9rz1JdhWBZvRzlzYzubOR3sZdLkq'
        b'kbVRdKPdcwgax8M6yRVwUQcDcW5x1KlsYv0c8uYseJRldT66zGH4abTtXjJivsh/wnfAAV1DW6246qXo4iNyRsedgcdhM46W0Msu2CbSjBh4CoTDXj56BV6Br1OlYAae'
        b'Qu00vxxGCC/jihxkoFaNDtBauudJcFxUrgBq4EUcd4GBHXAf7KD71EiDdhXRFuKZSS/dsM8uXsxNgtsns/E9aDdqwe8bMKY92jAmlZsOd0+iNibUbrGcvB4Bd0TnRWbw'
        b'gL0n7IVd3LRi1Cxx+E/uKZBjDkbTi6kBBiN/BV6Ri4uxWsjKrigDhao18Qyr1pRYAfdAXcKAW6iWd9vN645nkG7RgGdCnyjhtrMr2V5oU+6a+LlnUF/wlAHP1D5R6m1n'
        b'z3aVbmzHmq7lN/xi7pCY8QOeyX2i5EFXTy33tjMxx8/qStDl3HSOvevm1ZbSsnLP+pb1N91CB/2CbvnF9PvF9Ih6pGfdLgVdWv5myIDflHbe3aDQdqs2XlvZoJvXnvqW'
        b'+tY1Wt6gm/ctt5B+t5AuXlfZTbc4WlTSgOf4PtF4XLdBT5+DknZJR7g29b4t8A2gdh1vP/zHymDl0dt8RoVpeTeFgYPeYhqp/yMOIpG3xSGDIq/bIj8db0AUTP5aDogk'
        b'5K9gQBTy0Irv70SS4RL8g7W83XYmSp8jq/RpyAfxxBpRc/px8/nTI0pGr8TEZmRiVt8HqJb/1HD6Eb2ROIr9sAF8vxrrjZO+B/iDbNdPelnj0WFBPOi1mfjTjEflrPGI'
        b'X0wA3bONFPrqG4wUC55YStoKDxa1F+mNFI+DC41QkKzBGCkZFuFQpVwqi6yuqqyTROECubLqsp9sYcLv84pLFWUvXN9is/rOa59nqG8QqS/Gnc+t7k+q52JDxxJ898IV'
        b'LcUplDoST6sX/nyA+PNrSXpTWYXDL1xDuVlXLmxfaOjKKFMw+lOrG/Oc6i7hDKcZ7H0cLDulrLGCzuYXbk4FmYhCk+bc8onu94neYDoAz8O7/70WKc8CvVR64cYsHd6Y'
        b'+H6feENjol8EcP+3G7T0ZRpUNbxBsf0+sYYGRf445v+5E4Q1rtOqv3Ctl5NJTPZN2VrGFFJ1GFfQdP9BrGdXcSW99+2ZFf1/aeotl3AeHxqmG6USXVclVjwlIVVy+TJ6'
        b'Mx3Wtqm6O+xFclud3ggwEyvduA+m1iqrxdOldcvkVWqVOAW3ebgqFoo7BncPfnHFmKi4qBjJ85W1kXZCCyUM9YSv90Y7wymW4012IUjyxAp4VpF+fx9HRc4KbLhbQAzV'
        b'rJE64csVcbLYsiburN4SFzkS5UoXoDf2ehwL8J032tVrs8fotYkDjOdDa4/pQgmPRe074esTsYa13xw1EsgIm+Ebj/xJmq3ZXkZsbjFWj8712Bxrg/sprk2Aby81uVZt'
        b'MnyLANsLNezVAFjftFkKt2YTbA44i5hodC7omTZyC2KeJjduOBi4Uk+gAJLsVVFXSBviDz+hZUKfc+hgkORWUEJ/UEJP4cV5Z+dd5/3C8h3LD9R9QQkDQYXatFdzCbxb'
        b'27K2Txj0k6zn7wC6c2ZeG7Wp3Vxu85IOBevY2UgA3As4wxMfRQbPmP+GMzyZMQ3DGHSmXM3a02or1YplUrV+Da9VsRYjeoOjWK2UVqmkJpc9ltYNy4jkkUTtkUkluTgN'
        b'zgr/kS6WK0t+xIYxfJNG77r8SsYO7xxuIgfElER9Z+ECaslMiMT635YRTBOmdgl42cvcNOGFLihOft3NVU3COURXlBA//c7W7hk7GjudM86Uy8DmqFHig47v5Es/+eHc'
        b'CmlJ6L2ojd9uDKh5c5Tuct4Xqy7lBHMXe4IlYbblF1MlHKpNSuBm+JaZJg0vBLCqdHTeo1FkNlytsTPRJutQr4lCqdcmp695znknE/ctlVxdbBghCtPqPQxsOizK7DhJ'
        b'mi2ePn3Ogbe9RunUA14R2rTbbp5tCa11urhd6+74hvZJ0gd8p/W5T6NqzKfCQFPfe3biND5j9jzD6f4XZBI9u3brDNOJOODX4enk/rMuvXhJLG5vXpkXXiebCJQk9+WQ'
        b'1f2WT0y/T4zZyv6isycKS0Ny/6SS3PRpdpLAuDgsAU88d/YA6rRM9hAMjsv/2XMExNyew4xgbjfKhWqlYrGiSqrGrVHIngVdquQr9atgbFTsCDbLZxtqZaw1lHaU4QQS'
        b'LihKXCBfXqtQ6vtRhkNlarFMXqpQq0Y0DhOphGugql5mQPYKDFWklapqmgGbNTsU5XKl6tmm49oytkapUzIxCFIsryX5YQwaSgCPWGmoFS4rUy0lEOj5wm34iSPLvNpk'
        b'QG46sYaHs/OoUZTcLJkXOSMjKiuXHF9ojC5AmpwZrmszuAUS2J0pXlSqVK5TLLICUxY7LEOnvWrJCVd01LfIzKD65G24Ex0A8BzaPQuvyLuZ5ei85RzUBSjQKIUn0EXU'
        b'65Jvi4cdE+EB+Obk2lQir3bCNnRIZV87O4O49syKgq8hTcRspEE7UTPsLsyIICVty8xBTQyWq0ckq+BrQehYIQeg3fCi7fR0uIdelwl3e+F3TGpWY1+7Bjbpc50+J3K2'
        b'BZi+XgCP5MIDisbfzuWqiI0jVvt+x0dJRCr3H24NxihHtHxPDBqUbDsJ0zz8T416P+9YxOycT092qt2cnVND+gp17ZVzC2NTvix92ynv0u2c/TmzJp/PGBMz9jH4TiX9'
        b'+lf33hNlS7d+FfFFetxu/u3kq1HlgsvuXYIq63O/mTu+vf+O4NG85PE5b7d6fPCHDQ/CPBLng6og8XHZSYkVa4TctYzc4pc512iis6nioI558C1Wtm9GvajBJowc6SfC'
        b'nS4BaBNsjeYAP9jLQ2fQSXSSPcjSi/bOCQ9GW0wuj8zOoIWUotPoZPb0MBOTpK2Q65KJTrGuZNtssk1WmFkWOHO6wAhRB+uXsDlzrOkdt4vpWZceeJUFfQfQIXjI5EKm'
        b'XnTEcIzRGm2jlauflqk3YVL7ZSQeaK1Uxp7PbYJ7c1gbJrVfVljADhU68GPHyDY8tWo9kR/kJiezdcEsiq5a+/WrVoUtcT6eRODcml1r7viG9YXPHvCd0+c+x8QsR46d'
        b'zewJuhhxNuKm1yS6lqVeL+uXZA74ZvW5Zw06u+IcvPwOjmsfd8srut8ruod302s0TZc34Jvf555vlpmkK/CmVxSNnnw9vt+4LuptfuTPbitTD1Z2dTRK82cvkdSB1WyN'
        b'vD1sjTTri+2MyeGYObYM400cWb1f1l/jNcEocMwm9me5avGKsYx+4WXyKFEnjwODOhlLTRJPpPrzNN+fofjq3ah45LD/C1e1y7yq40eU+amzUp/emhyh0hLuEG+ZUl4+'
        b'JFApFlfJZUNWeLWqVSqx5ljGM6mqraE99fhjt5Vhr50u8pZGVw5GY0ev7eJo7Mtt6ZLPw0u+cUd9Ld/KbEHHYb7J4s5bx9cv+U9RTc8qfdb+3CWfvRiexfB09TRVpp+9'
        b'z066gF07De8aTxI/e0eUdhj7Fn0FdzahSYnhIUqcKq0iOrtUH1e6BKOAEZd/spuPV+SZ+YljYmLpPj7ZY5cRiwtW559ZvHGcksTpldLF4pUVcr2XAG4wafOTFIZGPav4'
        b'qmr1CMUo5bghVaokccrTylGJvjk/gh+MB0yN+ME6r3YKDttjyW8OH5BGv1bNysCkgoyoBWgvhQRMnBNsha2oNxv1ZoFgdMQe7UXHIykMgYeXo73ZUZFhWXgFMs3CmHVG'
        b'1qxQ9kpPpW0eVqnQUR9b1IWuwXNUSQuXZAItADX/t7gk7NI0Hqgl2F5glzVcRUMNY4mWFpmVO9N087h5phW6ZgUv1ibhF6fALXjhbKZp0A60MzyTQI5wAkIwnEhQGfeO'
        b'MyKycqIyI8MEADVLbJdPCaOYaAHUwrNmoIi0hWiHoXiNw6pXhCQyiw/qJ6xGx62wLrYhRsKtpYvdYbg3AJdbA1/NIlftT2TgSdSurCWr9Eq0byk8Ay+Hs1nkEp/sds5q'
        b'NTpMr3cfE2UVnpWr70EGOKPN8GAIF3VUwBZFjFrJUx3GiZo/W9TxUTxGN/GmyIbgmnTdEteIEy5nmxefdYxpt5LGYXCzNMRr20G478+c2R9bzfl40+fW3+0eo1tSvuXr'
        b'SlXC+VOhX5xTK2uVZ8o3Df2KEUn/8vmm7i/vbTpRsumk8MvPP7r3vvrvSwRt9rol70csuhMWc+eXW+/5bs0bo7P756XvViqP9PwKo6KvPt/2xw3d131/+Y7tPgWILokE'
        b'Vhcx8CH40AZuQp3VHtkUE3BKmVi4Ax56RPSuVHhmMexBbz6FeoyIh48Os7uXR9dgqNFsAE55K1johKHoORqPFeed+N8rsuzM3DAMVznAEjZz4MYs9Da96wjppqFz09Ap'
        b'M+WaBT55GBmRSrpWzMrOhPvQ5gjDGWB4OIDdHW6DB8eE24Wixnx6XktQyQnAI/Iqe6rrmgK9SU915bMXzUbg8XJCe6O5GMFuRHvZ4i+io/AEMZShg35PNmjJ9uwx9JbE'
        b'9mftp1IVcthmqg1BAHr5Uu9sCgv0RAqOhgALjpbYEYtY4q7EO56j+kKmD3jO6BPNIDdFJO9K1qUdz+nMuRU09kbQWBqdPeCZ0yfKMdlsvWOy2Yrfah9P7QI3nCNoxLQB'
        b'z4w+UQbZZi3Xld10DrvtE9Y1ZsAnTpvO0ipuOkcP+gQenN8+v2OhNn3Q2YN1Wu3IueEcSrOYPOCZ0idKIVuf3uJB36BbvlH9vlEDvjGD/mEPLHgSp4eA5+9Mtz2tgbv3'
        b'njUta/rM7A4OLLK6Rz7+QD4+Bz9lq/PJDrb5Zqcegz0gsGCkzj5pQF//xOhrph3DhJMNz/CXRV8HBFHgdZtxP32vU0Ic5fV1emFY84m5Qd+fLKx42aHLrHFdNrXgS3jE'
        b'l7ebk4fLS5e4KteTdzeQj42APWghqy4rLqabw0pyQwDdkR7ilirKnrktPWRh2OAiFlVqERqyMzO8UARsgp0f0LcMjXX87xyQdHxq8pkww1ZAfYjZzvQgDNBKHBi2gAc8'
        b'jp3wW0tg79Ie38nvLOsO6lb1+cX3eSa8Gf8h97anTzf3bOojLmM/7m782MGkid9zE+2CHwLywcfE+zwceqBmgMj7tjBkUDT+EZ8jmqBJeyAAzl63haMGRUmY4pysScUU'
        b'fZoUkiaVoYnc/G4LwwZFaZjkls5opulTRZunchffFsYPiqZikvs0RpOBSa6+t4Wxg6JUTHKdymjSn+SVTvLKwHl9Z2lpF/ytiDZNx2sLv2k36juOlV048XgOuU9CD0TA'
        b'J/i2MKYvLpXNygdnlcv2hnNnIH7hrxwXO7H+BRx6EGFo1jTSrEyGtktPmkFIMzGJzSCwU9WdcNayb9S4dwpv2mV9z/G1C3oE8AfJLpu5T54fTDTUeiyp9bjGaawTNpk9'
        b'BegAPKvKyWOVZ4xL3kZN1vUcjBo2uQ67ph/QOUf8sJ3M/bBlnCKejFvEV4AigYxXZIH/W8r4RVYyQZG1zIJ4MM8BPXzi26v302aoj6/wlKXRmzgaQ3YbjbCcK7My8esl'
        b'Xs52ep9qW6Nfrz2l2mGqvQnVgVIdMFVoQiWl2csd9af1LKgDroPGsdxS5vjE+9lYnhNJbayt8JST0WeaqBLkfcdyvsx5hDedcdmiLU+eReR7Zso5MpctlkUuuF0M9cl2'
        b'lbltAUVuMnf86U68rYs89Ok8caynzAtTvGTe+NOb+FAX+WgE+E1fHOerATjkh0N+MjGOEdNnf/zsLwvAzwH6fAIxJVAWhClBekowpgTrw6NweJQ+HILDIfpwKA6H0hwl'
        b'OCShoTAcCqOhcBwK11jhUAQORWgscSgShyJlMfQcJDm4GbXFqiiqjodlbuyQIGUZdbc+YYbKiRBlI1iPa/bLrbDCQb6hY7GS+NyKWTWhrM7ozvuUT6y5/7YSZ7BMrlaU'
        b'icmxCCm7s1LGajuYQBQYnCdr9qysE1dXsSrJSCqDhDMkKF4hrayVD1kVG2oxxJ06qyDvcXKFWl2TFB29cuXKKHlZaZS8VlldI8V/olVqqVoVTZ7LV2E17UkoUiZVVNZF'
        b'rVpWSe7dS82ZPsTNmJU+xM1MKxjiZk2fN8TNLpgzxJ01bW56N2eIzxZsaSjXzKRtdE4NYohJGy93HJXtyEseu9e1xvg1ZTJm6Viyn76Gs4Q7PLWBVVX2ar6BJuOs4dRj'
        b'bcn0i88a+WsYw/NaRsZdw6wAyqA1jIwn49PymCUWYNiPjGushYBY2QxP9ViQ1PPJjUIktyqct8yCDZOd7SclrQHFRq0f198GDPsx1B+nNB7erbO0qpBYfVY8kmb+tO+7'
        b'nhefuL4//cKz9F06Wqy2LWXzoJTnWMPZYU2iDuUz8yMT4mLHmrK6DCvpmeVE+RWrauRlinKFXBYxooqsUBOFGsMsg5c7LdlgXGGnFdbZlYrS2mco2UkkOqlEJi+XYixh'
        b'ZPUSrLUryipI7gq2n/CE0ZeDJ8Hwtn1FOOqxi6KKugI8aU1IsCrkMRM1xMR8RUTwVz/gn8fcqJiYPInFkPDpYsn2tbSypkI6ZD2btGSqUlmtHOKraioVauUP+P0hfm0N'
        b'nspKgvkkAhbSkhvElTbMcGhC2EBsYiCkrngO7DgbPfHuEVzyKmAdK0V41R/0C7zll9Dvl6DNIAB/VesEXcoN5+CuubciJ/RHTrgZOYkC8uRLq/qNwN7dq21qh7WWP+js'
        b'2hbckjwo8mibqUvp5nZNPZPdnX2JOxCRfKmgP2LyQGhKf1BKv8+UftGUlql3cbJZLXnaqbd9g3XyjiqM3m0G/SXHfTt9B/xjtbzd9j/3ICbts2fBXENPGFDu3808u7Aq'
        b'YrYZZ8ralMHqauTiEsw4ZRiAVkalsX9LSqKUh35qnfW+NnRsX7DO/zSr86J2w5HNx17UEXHkyWVWOY6hcnnPqdzz5OUS3vA4G+MJUC5lzyFLqaqYnooZspSvqqmuklc9'
        b'80To0038gTCoN9tE2cEl7Utu+cb2+8YO+Mbf8k3u903u8zEcEX1cRt0Fa5eVypVkiPRjI66plJYRFyOpWlwpl6rU4jhJlHiWSk6FRGmtolIdqajCY6nE5cqwUofnuFS2'
        b'pBYnJAnMczHvPONiRG9qszR+ux4wfruetf4+BMZsh/U/4Kj02TcjCfVZNUTXYQW6fFVZhbRqsVyspKRSKdlArmb9kXAqqbhGWb1CQXyNSusIcVhmxFupRo7xQyoeLiXu'
        b'ginSqqV0U1SlrsaaGBW/VS8kavVi1lClYlqlEjIKtVS0soKcSHzjZigeBXIIaQSfEPKtoXJ1RfUTLBMhVinwmqXPhrxGHMzMjjI9o436jJLI944mlehh1gjOJc+1wpZW'
        b'V5MvLxOXm5p7a+lQyJ4ahhEXoZVyJRYwKzBGkpYST7lnGH5/xO/LPo/ulKKdUVPDIzNsazIjiD0tew6xi6IdGTiYPys0KyIzUgCWOVmia0g3it1a3YjDPbAZ9aDzM0Kz'
        b'Isn31ZFd247wPHgeHSqIRMc4IGEaf7EUvkWNk+gyvByuisrNQrvhcXh+pcAJOMA93CjY5lYbieNr1idTcynSos16k2loXmRYdmSBIfdsPtZKLOGVHLiTPfvaIoQ7VPQW'
        b'coBeJUcs4E4G9XiuZL8qdDd8Y8xMuB29KnCfhbaj3bOIuTSfQW/Ay+hEOt2BriiPIDXiw1PLARe2MXBDPnyD/Q7RbclVqgzWlJoNX+cth53AEVcXnkJnq9nv4Tw31luF'
        b'ewZtVWXiotcy6DQX7ilUHLbp46os8DQbjLi2dnpuNjdWuP/D8t6O364TT+nUbLoGm5ssfti4+Kvg6e7Vp1ftXXCV/9ewf2v+nRl/3mpKqSoz7i9v1T384uQPW2NCttxL'
        b'TN53wlKakvuhJferc3sLb87qGfjzewOzk11QSvAc/jvKb/64ceP7Tcc+tJXd2fmXh9u+3LKm1F0xb4nHwiuuxzJfVy8vX+Lymvrvk3y3/g/4e+7JXV953ap7i//7uBuX'
        b'dx3Nd56E/vSH6oBvgxa/8mXunXS/9Zv/qby3w+vyic/jGt/57W98rue92b90R+WY7wuWffV4n7W0/sb1sGOXJHW/2DG7L/d33Y92Ov/yXvLFowHLvsy/3C4rRX+2+Gb5'
        b'1/JzDWV7FI77v7MZ/LND0qWJFvP+LHFkv9dQm5hCr5RHzRbz4U7Ai2TgabTZmtphR62Cb4RHoibUGA33ov0ZaDsX2KZzBehwCLsFfhUdQPtgczROw8iRBvCiGdiLzsIe'
        b'dl/7QIZPeFZuDoNZ4Qzg+TNwPzqaSs2zkfBcHjHuWlTmWgABj2MJX4M6tkJnxxMHKFIlxjId8NwYeAhdhAeogRk2ieExG6hFl59hYZ4eyxqQOwJU4VESAHvCKB9iJnRA'
        b'57h1cE8wuy1+EO2CG6jdFr4FD+gNxG/DV+m+NuqC54rY3Pmwyw3w8hjY42NJDcTo6iL4OmyWwpNoZ2ZEFGyMjsyg5l+xmIcujJ9Aqxm+lNzRb5yocHs0nakLVCAMXeWj'
        b'TUvQbuohht5EDd5sWzN5cBeZXQywkXFQB+ryoP00BmnhsWwl6s2PZABnBZOCjum/DABeyFtK7pghV8AIvPRXzJxEh2kF8GTdgHZn52Zn50ahxohsuD2fVLJ6LgiDO/jw'
        b'DGpfRls6H50uQM158HSEQIpeBbw0hnhr7pQI/+OWNfJhEH3mpm0XVrYWmy8n9d565DBiLLV2FzD6G2aFwNFtj02LTZ/36JvCMYOuPnuqW6p1ZccrOisGXKNvuSb0uyYM'
        b'uI7RcgeFrntsW2z7fOJ6Um8KE2+7erQFtlZgupvnnlUtq3Q2A24R+kNIo/pCJg14Tu4TTR70DrrlHdnvHdkl6xnbvexS0YB3xi3v3H7v3AHvfK3VYGDI8XGd4w6P13Jv'
        b'CsWD7l633MP63cMwfPbw1QoGPb21FoPe4oM57TldrgPeMeQW/UhtGsbluux+vxgMy70CdAldFp0TBrxiMd3Ne09dS53OfcAtrEt2wy1u0D+4TUA876a2hbbkG+6YSfxU'
        b'FEHu1I+8bw9EPjruLXFcvzjuhnPcoCROm3pTNIocQEq/LQ7SzTpe1Fl0eMGAOO5bwHUcpc0YdPPTrbzhFjXo7a8LbcvH+bcL7lvgqPuWwN1Xa3q+yEZZAX6KWZ29dObp'
        b's0PjGOLD/LxR5XJMbudKFTKMI7mA5mWu4VeSr6/BWJQoUGbOtMZNUuo7xzd+Fyif3sALjHfwEiOD4D/pUPvZr0dCdqksNNGfU2eVEQJUMVIgaMOI8PUAj6A9lV4RHg4k'
        b'9LvPTyHEp/DgyPhvOCwpHI41pQTPmMEvAxqqJjCNbL3XESA5vGbSsgrWEW6ZfFm1so56CpTXKllEpaLfG//j0OxpO4O5LmRy+EMtVS7GSr0h5XP32quMm+0sQxr22g0Q'
        b'mABXucrUavcTvPjo7vcNuZ0okBNDvmch57cT9LeXtk/3me3PrSHE5NbALJaoDbgIVmFuEYdMXz44LzSe/brSrSq4XWVnxwEM2lEiBug06oCd9Juf3V1he/ZTcNCwsW8A'
        b'SIXEmW4OcbaLnmHinZfJR5fgSVDvK0yygXsUytD5fBXZR2v7XlPbMoF8++gr+99Q2Li4iDf+7U0Q6FUZsW+D74ajM89N1XRmub1buuJd//rMO11Tp2SeS/voH7/rLbvW'
        b'6qDT2u4b+Ov32brrhco908eD/4mN3Pho8FOv62nHPvt8q0ffnG/Lo8raPkF5U3/7pU1sa8zM2Oz9mkZ12IIT977O+do3fpzN4unVqjmnf/H5zlPrs94N+L/FC+GNT72+'
        b'OVjhcpJ71PdfJzaOHzj5m8fTLP5aEHIz5Vq/RfydDQf/tOnrOysCH3/kJbqQ9WDO1FVOr9Q2/3LZpTuXv/r3wbI730oF3jFxhatXSaSP/smptEya98FViT2LTY55oY2w'
        b'LS7cxOfOw58FD2/ORef0Dg/o8BwCM4HDbG4lbA54RC/RDUVbzVd3dH4OC8XZ5R3DELq6OuFn4iBBL6eG11AvMwuj3E00EwHcgdpNF2jUBK/QRVq/RK9EHWxFD8FDqybB'
        b'N9lNZvY26+Mu1PuvDkOGy+FPbh61geeWw0scdHIR6qToQQYPzy4Io9dZG+6ydqrRH5GGWx1h5wo9ymEhDnxFyG6CvznOlexuP4Vv4KFADHHgawmPqKLRnpQYTuMwuMC9'
        b'UQC7nnQIB52DTUxxtCU8ghWRVlqZWWPQQbg/MJzu2fOBYAnHtzyXhUHbbWttsuEpx2G7+eiMBR2SDKiFF8Mjcoke0hhTR7/21QG2cpXrMyVWLwdErIDJZXH6YyZ6TbHe'
        b'Xr866Z8pygjTo4xKR+AddHBi+8QBr3Byhb1Xm/rg2va1N5wjBr38tNmD7t633MP73cPxwu/qu6eypbK1Ssu97eZtjOgqO1PRXXFyyQ33xEFvv4PZ7dkduV0pN7wjewIv'
        b'hp4NvVRwLpIAhcz2zI7srqBbYeP78a/3+EtlN7xTBkXut0RR/aKom6IYnOFB63Zqn3Mjp150U284S/THWrqm9rvFUgfFuX3zi2/Nr+jHv5KKAV9Fn7uCrPhTu4LORHZH'
        b'9gcl9nsnaqeSZtTeIN/K5Ker7XeLMLxa1i8pG/CV9bnL2JdCO/P7veNxenefg/bt9jr18frO+p4JA+4pWv5tN582uW7ugFtUnzDK9F5w1qBJbZkvcIcneye42SWe2QQx'
        b'PDUmEQaMQA4HzHJkGO8HL+n4qCReEiOfSnsVPNtqtmbE84ArgNJdxjzZY8CpBMNTGfcHBMQ0KOO8XHqrxRJu3mNOsOIxLzgqrlzCo306ZFtcVV2st2ephrjSUhW1zg23'
        b'xA0Ji43ubuw2UL2bwW78VEQe6V3iZbUB3NVzV9qtoNH9+Nd5NObzI4E62fElnUsOR/d7xfaJYu96+R9J7eKdse62Ppzf7xXfJ2K/bMRsk8f4xQOWZJOHswewGyuNXMM+'
        b'pnLFGuYZXT4ClWz7KGeMPBxKb5wTfzh95JyebPxUSdTGbR4Zs4bTwcg4I7/TQTeJnhHD22/xZHMJp7IcnmotptMh5efVuxpx3jKFCg9DWQVFSPXcJHFIvUUINc6FPGZC'
        b'JHx2xJ0Vy2oqFWUKdTE7GVSK6io6SYasCutq2P0FlgfYA21DfAonhyzZHUQcae6ILTaeaxuyL65RyjHSkhfTV+pdDAxiRp5F2IO0HQtE4usj182+ieUf1lnWtazrEp3x'
        b'6fa54TYG88ktr/gbXvGDQZLjuZ25PUEXI89GDgRNbp/6vwHhQ9FjL4mu+Vzx+YD/K/uP7e9zmci55KLJwHnMfcD4zGPuevsT4YiFjZu31nb4poHRVpaDP3ZjGC8j5ljm'
        b'+UOsH9ARWIYM6H4+tXDz8uot2XaHhtTzQiLwKHBCJEor0qMcVpoZjyiKn9xygXtISe8ZNezFsATydbIqYiX520ZwOzquJ+Fi0tmk0+uv835hh+z63PL6hHnDG2c86UYm'
        b'IWnaywijco5eYJBbDh9bEGEhDlax9R8uFSyKydV/uOL2xorT5zJDvTcA8k0sacezOrN6eBftztr1BU7sd5vYJ5zI1nvEw4rpQC9CmWHVA2sYGWOY82uZkduwhlnK0Qs9'
        b'3AYmuZujnMvo98UMgzCbMQyCvimC4uJKctGInbEl5LEcJ3kYyDbEuAhP7YkfcB+LF0/2mg8dXjAlfULJf7dFnvpdLNwiTvIEZcmPtUVu3hb8uGTktiQMuCc+acss9t71'
        b'57TlADBKYCzFGjlGCZzwDD4bUdItDQVYUVF6MM/gQ/zWCFTy1sxnLa4MG0u92liG5T3pn6cOPT6RWriv5MvN+oo8VhEGJt9tbC6lfPzJ3R5do8+M7x7f7zPmWyxspjCD'
        b'/sHHfTp9eoIvRp2N6vefjMWRSypz98c61LjPRipFmINtgK3xFgqKgJ4zxFXmQ0weCdykvoh4iL38dKPbJ/S5hfYJQ/+7rJn2RGAwE3+UMxebzzLyuBInUdKbPv6r9Vzw'
        b'pJ6ciT8+hRab9y95XE0qWm6s6IhSl3gqkiXlxxcU44FRM8k00vJA9pPMlgeWsJ6j/0IGwqVuXsPudR25J6v0Ffw5fUnOllBDF3cNWRNH2PE15GHkjPBu7hMxTMGI2fy0'
        b'Zsznp6H1eImRymRmSwx93kSkWQLb9hFEM6vg4NlHzKiselF4fGHnwgG3+D5h/PDeMQ4fOXf37L4xGTr95vzK53ERWdnZ2pus7JTQQKpPXUUBPX/WskY3deDHRO9/ZOSs'
        b'X2LkyunIRSpXvMRoqWpLzQEBeW4iE2fViDPc2POh+p63+fG+J3cJKet/rOfZmpj0PCXsJJPGme15D582PrnWS1c74BbZJ4x8Tt8TM/aIiodAbUw885mLGfHoeuFep64q'
        b'3CH7vGp1JkbrcnI5iFxmMm/4I43EiJgcj8ey2kqz8aDPu0gnkLMsZuvbHS9Jn0jy/2DuLGadcbb82AiydTcZQUpoI8y05vnLhQlKMR8u/581eWyeO8g2Lz21otmp9eID'
        b'aoMXeWWtXKZYgTvGydgxRloHkSu54Gng4i2+5R3d7x3dw+9RDXiPx4qRl9/BpPakLn6/V2SfKPL/Y+49AKJIsv/x7knEAZSchyQzMGQwYEZA4oAEXV1dQGbAUZITxJzW'
        b'MIgBjGAEI666ghGzW3Vh090N4p7I7d2ud/e9vXzo6u6d3wv/quqeBINr2Pv+f4ae7urq6tcV36v3ee996SfCa0eHe49fdFPaQ9+gtjBGFuv1HaN3G/N/X9GcF1Y051Ur'
        b'mhPzyjXtiLj/qtpaFVPVrsaqNiUew4PohXWt6fWbYKpr9x7faL1btKGuw1Ce/yfqWvDCuha8Ql0zAlfYq1a1DXHrbjlL4WtcsmqL1YFulOB/Z6oTPqoTnrFOxC9TJxrj'
        b'JpP1b1tJm77u5fPOJf2TONHgkVqztj/H5iV5uC/OU8Fh+3G/AHU8VDVoLSas1E5LfkpgqvF+fv2C2ioFNhKuLlPWyBXmGzcsDtRY//YlJUy5qAlGGJvAkHQRd3NscDNs'
        b'N1/a6zelKe1z1JNDT0W0R3Qoen2x783fhkd1yM8vPL2wO6w3fAqO55TWMu6hX3BbErOD3Os3Fl+NQ5mqT1ejoYIkJ79JAxTtPukFER6wWeqL+WuHYTqzBUtqkBGH47pJ'
        b'7JdKiz5Jrm/iCdaHrQ20NmqOLG9d3rKoI/H8xNMTez3H6V3GvRHx5/jfSXzFyxBfV6u2IJ5c38EDqsWq/GIcUAVmJGqMOYYhyghGfymWRpVv2V9fQH7ZfEvyyTXgsMhP'
        b'pu4PljP97UBth+b8qtOrej0n6l0mfl+iGeExVd9BprJGY0Emuf4hhzUDI2T6tCTi2X/XGr3LqO+Ltg3fSZsdWajKGNe5ZksXTvnQQmz0YxyW9g6zUWDsF20Ua16BJlC8'
        b'v6ZyMPUOOce0Z40nYjlXzmOY3uVmhK8aZvvU6m47p0FgnKa5LzNJkmrhy/6Az58HE+iusqZSVFdbz4B/42IZAwJtXV0t9oP/nBMb3U/HoanU09Ar+20Xa8tqNMrlCqZ/'
        b'Mq6p+m1QSZVKjbqfq1haN2gpM7mnYiZUU/UTCiyqn035BFd/PlP9fa4+LTN2jicA+sxenyy9W9ZDD+x7uLxjent1T0Bir0dSE5flyFkZd1qnf6/X5OE489OEs8ZhWCQx'
        b'g8wsVd+ypKmrajU44Ik7/mYnSwANuq6oUJRrlEuYELqID6oqU2tKGLxGP69Eq6pS4ZCgqiJ8MBlsGod1v61Ro+RAABIMpJaAd4iqQTUDH8gCNgcf5uFDGT5gX6oq7IFU'
        b'hZduVTU+1OED3nQmorZqBT6swYd1+IBFCNUmfGjAB+zTRNWED3vwYR8+7Cd04sNhfGjDh9O4fv7bYTKHWIGyOsl/UVgtx3QLPRZ7amnGClTAE7oM2FPesbrMLwND9Y5+'
        b'ff6BOlmffxA6+AbqcvpcZ+hS+3zT0FlwuN4x8NdCt9a09pD2Sr1v9DXX+8KJ33BchfHYsnHSAD57HEG5+z90ETNmle5ptC6NteOM7HOLw3acCcSME6dMGODQHvn0Uz7X'
        b'qwAbd9pTTp59Qq9vOWHCgCcUOuBivfHBc4CHLh/LaHTajygovy8MxnaVMfhmCJsDXQ5MQTk8HnN4wkQS3mYAnz1ztBP6P/WghXn0EwEtnPxEwBFGPLHlCCOf2fKEkU8c'
        b'aaHElPbUlhaKnwq4wsQn9jS6NJxFP0NVlYgzRz4TCIRjn7mYDjbCSU9H0sLkpwL2MAkfwvFB8q2AL0wcoNCBsfDEMAZ/cKQee3zYxhh42npxsuFhrWCs9QCNWCGwh29p'
        b'3Uk8p3F1vAoclNGWjYnD3UDJeWf5g2LiCFCqjVmqjVmkHFOqrVmkHFOqnVmkHFOqvVmkHFOqg1mkHFOqo1mkHFOq0CxSjinViaR6oFRPs1QmCo4XSvU2S3UhqT4o1dcs'
        b'lYl044dS/c1SmUg3ASg10CzVlaSKUGqQWSoTtSYYpYaYpbqT1FCUGmaW6kFSR6HUcLNUT5IqRqkSs1QvkhqBUiPNUr1JqhSlRpml+pDUaJQaY5bqS1JjUWqcWaofSY1H'
        b'qQlmqf4kNRGlJpmlMvaqo4m96hhsryofi45B8nHYVnVZMmLyxvc7Yx85RSbHfo866UFAQINXO7NMbLieQdmwFQQxySgvq8HL4HwFa9inURIYnsFwggR1MZj8YdsJBu+m'
        b'sETmsXhAS1sJvK9p5oWwFC+6ZYybH3ltuRbvYhlLtiitVmUoUKlhlMzMowZ43bSpuUWpbAmlw9gjWlxkVrCGH2Wi+UQljopjUJHmXhKlzCsN38raxWpUClwhFuWVqYkZ'
        b'LiaOmGMsQSWVVVWJtFiuqlqG2QwL94sWD1uwe5h/wV7Tvp6CGL89PMxNqWwwR4UR5Q22Wno4rkpj5JusYxOMPBZXTq3klhhFVXLFs7jiW1wJLK5sLK5sLa7sLK4M9u6U'
        b'OdoVpTtY5HK0uBJaXDkZr7joytninovF1QiLq5EWV64WV24WV+4WVx4WV54WV14WV94WVz4WV74WV34WV/4WVwEWV4HGK8TJloiMVzS6CrLIGWy4WslZOJ0a8sdQ16nU'
        b'PAW71cBbxV/JW5g5NK+cb+gXaoEc5SFqG15N8DC5BYbcqhFyLIZmDc1zgF7JO0Af4q7iaXKNdHJXGrdd1E6aPGN5NuiNFsbSmhnmz6zkGyKY0dTWSh7uSXYruQuNdWr6'
        b'02CMWabmZGFcDJfIlLYy1VFU9vMkZmobMhG+eKojCtb0frqkn1NS8jxs8NMLyrD9mcmEjVjuSiT9jgWIbVNWs6a4Agbzy8Qf5JYo5f38Eq1Co8Lu9xk/H/3OTPxoo5sy'
        b'1RFcwyfxAbelqhYfiCv4jykCo7Hw0oekTAbcjUqs06qQGK9AryC8uA0BXGnK+gUl1epK8upF2EEcv0TB/BB3cULDYyUk9qtNSfkCDEwmgTjLNFo1EghUCowEKqvCUS9q'
        b'KmoRxaRClRXKcuI0AMkAzDJgvF1WrTF9UL9bSVVteVmVpddbHH91AYZTqxF9ZBpGxZBfJi5rv1/JoCpH4jOaYtm8fHRere63R0SqNGrsCoFIM/02qF1wm/Q7TTW0DNMS'
        b'NmqFBt+Q2DMmB3jw9wsW1SMS1GYuhq2IbwzHjic0ZsY2ceokyK3nIDINwW5/g+W4Y7RR+6ppm9par4+e1BM4idh+vNPrU6J3K/nc0x9Dm9rKez0jmngY6MnbbWsM7kLi'
        b't/SFR+LgLqGGVDa4i0Weh6LwY3YWkWAMv4EhJP6vKNg8NjCbSCLKOBgSLX/CJPj5YENW9gdHiNntZMhjICxUjH+DjNfSWPwrYWn7MiCEvCY0jMllyB0iOTWhfcKxSU8o'
        b'mxExzdlNqS1heC98cuvkjoT7vjF9gcFtRa3LW3l93v5HAlsDO9w+847ui4g6L31Peo2nD5zYwvucWLa4EZeZUn1UkX7W2z1Rb/cGzNV7zf3czbcltS20g/+ZW/SAM3rD'
        b'YxfKK7gt9JS0XdopuO85Ru8yRu85xhQY+U3sxu/Qw9tgew3uIAZLZQ+uhT9n80gNE4qITUbNIpP7Qinj0VlTy3qHxFawcsTyKCuWIUbGjMF4Q4tyFVYjvPK3eHMp80As'
        b'oyzj2mBrh+pajcl/JYlg+AYhJlQnXodIP0ykyd2mZTCboTTi+Iqv7wxU9d7rkBhopR7NA9oMopENfPjfiWUzLJHBmEiTfy+JlUg23yOdpDK7X4fOMEs6fzFVxETaVGvn'
        b'sy50iNMOTBxrJ8XGGHnhRxCpiimIIJqxEFSHHsMCDAliYCVqSbSo0JRWoVTgF7ISBSodZTBZURk5CrUogq3UCCk6VWrIryEeTQTB7kYw0Vwi3qAHfPQ6NSvFNfuJsWYT'
        b'h7qfH2ZMTU2ZNTUGHdLeIEwUovbu68y3MZZET7BwDIwdvCvmW7oIHkz8tIK01JjUtJSiN5i5ENUfvA7x8Vxzzx1zW+calooC0h3NOFPW2M/gc2SQFVq0KJU4sGds7qrq'
        b'y5apWQe4ohpFZRne2H2jlgGv83GjLQdqhGGgGszuzL6O5VZF4sKZs+a8WTvA1yF1nOUEHU4W6traRVjKZxwEI+G/rq4We+VCwoSWcSn8RnT+4HXonIDp/KtBl/fcucjo'
        b'7ej16WGZnR++Dj2TMT2+tMWaUY0mvrJKhdmIq1uwTI0tQEX5UzNlaKKseoPOeJpW/eh1KE2x0sImCqtqKy0JFImzC9LS32w6+/Hr0JlmSSdjV1sjj9LURqEfE+MoEqe9'
        b'PoEsjPHD1yEww5JAf6teuUXi3DejDpH10etQl23JfZtHsQtiTJSRtFmDHfmwMw7jjT2/uCD/zaj9+HWolVkO55Fk7SKSOuvA6PV5K9S8P3kdkmZYNm/E4HUIbwZg0y98'
        b'Lk7Jy8vOlE0vSnvrDRfPn74OqUWY1F8aa+9vg0m13M+IFqWjSXy6AhFfQ4QwtXG/2FqkdrQUzcpML8Lx1qWi6TOnSUX5BZm5U2V5RVOlIvzB2WmzJVJid5WOu/wCtszh'
        b'SkvNy0VzC1Nc+tTczJzZzHlhcYr5ZVHBVFnh1GlFmXkkL3oD2cOuV6qxwXxdVRmORMN4nn+T+v7Z69T3HMuxFd3jH20YW8Fmazuza8QMrDIyZZWpUSlv4KxY9cnrkDvP'
        b'cnCNHtw9mJ2waNFUkzu3TFl6HmroVNl0vODj3v1GZH/6OmSXYrIDjWR7FhGWldmrQ71Kjrtz7RsIh2hi6H0dusoHLfVsVAPiH5GhSmHSvZhvXLxJDepfh9IKy3nBn6lB'
        b'w8qE3WWIsHbJCiNixL1goDELurdCn/qYdUzLUlrlRQ8HFBzG8m4prXYc7hniL46zkraOgUGpVuxEDbvrK6kS85z2Q3OqfK2nW//mEv6L7y8UDk1DOZ2Gpho0A/QL++nz'
        b'8QWM0w2shTNKO4zMZtIHWpfpoiW2qtu4/f+OP3NQmGuy6Y79hqueo4OEaxYLm2wJ4/ozmjY4VCo0hj395b6DO5zZTSV6TI33qv++lsJWYKt2rsK7nmNbx97zndjhdt77'
        b'tHdn6tWMrgy9eOI936y7bj/2/sC7KfVhaGRHamfoVUmXpLvoztxrc3tDs4zRJlERcUlX/bv8W3hHhK3C+17RfW5e+3Kbcx+4JfS4JXSmPkhM70lMv+82fVBwSos+jf+Q'
        b'Po270D5qGU1Mc4oYS7OhQwufDx1aBuMjXDtfk1hM2ILlBci2Amr44a1ysY7SNSi5zFG3leYIODaC7mcopZ+H1QZWrFNtWYVCibWPYO4swW3F2kS6ej5wDcWODLDtsbTH'
        b'V9pL4Nqfe/q2pOxa2uT8gj3krBd9oserhAZeRjz+MHotw/fxSbeybn5bpahB32dFRUFurMCfJxrm8x74xvf4xuvd4vs8vci3ySQh1hBjRAtCMF79ToM0WWSokJFlGlT/'
        b'oNjx1C+0VGQJWD2WDctvq9JwJgGrw+IzKiwe0WDxsAKLhGbod7TQXglY5RWPKKKcBqmpHMy1VAJWvWVr0m4xmiUnS+2VyovD9nWVPz4TcQh2fVhkl2X4MdVFPEgGAzU+'
        b'w6qhZzSL6rITunzrES30eyynqYBRxGN+wVM+J6CI1slMDvknYFf7k17stN8sD+uxfjL2WD+V8dlPkgY4PPeYp3yBZyxKc2I86/e5ZWG3+jm0LhdlY5MwCf5FTBL24y8Z'
        b'4NDu457yuR7JuvTHtoYXTMEvSDEFBUBUTMRUTCZUkAf73MJwAIBw4v+fBZxhutynMoCzoY+xKaNxyljzlASckkRS/EJJBALskt9vnC7H9DIxflkEeRn7FKbRLYWJUkAq'
        b'eIDDdZ9BP+XzAwpwHTtSviEPXdCUORZl9E3WZZsKy8GFyZjQBSwwLgoD42IIMM7Kx7ANiAkNSNLJnjLhDWih3xMBVyj62p4r9GawZWEUiROzCVxxWCKsc5Rkwa2Rspxo'
        b'7CwH7uBSEQv4s8EW0OmzdEiYWvznazzeMEDEBDTbQM3hcigFBpkZZ8I5fJLCNUsRkBSeWYqNnI+etdVxKmi5YIPtHDu5Dbq2x67pKzhyW5TiQO7ZoTNHHRed2aMz4TIH'
        b'u0qJY7/roL6do1RbBhzjGGbBScwsSFvwGxx0ZZwzMYa3xDjvVWLOxDi9L2MndR7Z1Om3K5FrWQSqHbYGKatSapb1Bw/WGWNqSsxhR2qDnWI4h0BRDYXYGsowWCyKzHxg'
        b'+1kp1egQewOeRAOZSZRViwZJiJKU/RklNsW0ff1t+n+8gL+1Sp8xaizmcbER4usTwO5SJXFek4RGTEL9G5HAcvmjX5eErcOTYOREogkJL2vUYNgP5ahwSA/VGOuU4TVj'
        b'2P5DeIztXKPBKeYlUhmzmV7PWL1L7PdprICIIzQOYxJAFrYhjCtLKeEWmjGhGEFlsFt44Bvd4xvd6xmjd4l5GW6y4ju5yWEqiuEod+Mm9OEYmtDc/4/RgObflHUTOLU5'
        b'bo42IY6s+5Gw3vAkGIQYPWFdZrMid5EnnImJlxX5i3gZctCYEHFmeD70hOPQJxY6D00zGc7SzBzJlT2PMt+8qMaOyeebfNCHD6rjcMvs8loF41ib8RZEgowY/D8SBglJ'
        b'TMU0O4ESHk01Fp+NwwdiKoF7GeLm6uoUNXKDmyAHs1cwWYe19uOWyeVDOFbSEdCNfbgP4jhPpA8GtUV2rLnvOflznxB9aGGvT5HerajPNeCBa0iPa0ib5tSy9mX3XGP7'
        b'fEc98I3s8Y1kzIDu+U7o88V3V7Wj80RiW1HU61Osdyvuc3F74BLS4xLywCWixyWiY/xnLmNeMAQxYtA0BAfNCxb+OYYMtkA82LytfSRh5tvwZwop01DbtUzvIhpKitHn'
        b'qNxECuptqdQOupxTSZVz5nkx/qBeVsJo5mz14aHnVpmZY5dzaJJSbxSrQnADEqcUjEzcT2usSMR8Ta2mrMr6V5Jbx/BXhhq/sjP1577jOha3TD2S0ZpxRHZAds93XK9n'
        b'st4l+R/ojKzLOn+prUziNFgMMVmZkE5p6o9Gjp1h4NM4bNWrMjnEY4E1Bt4i6L0qATeUNR5nHSYeoyQRD/9EwBNKEBvp5tfjl9DrmqhLfegZ2CMa3+s5QZdhdvqERwvj'
        b'sKVBLDZu8HsmsBGOxcYIQc/Q5XiGL8ThyCqVtgxTyK23YAvhRdggjaapVHjOJgd0gSMWvKEBwPp1P96S8jHnDdFfDvnLPcifw8WRZ+QCuY3cVm4nt5c7yB3RmVDuJHeW'
        b'uxwUzuHpODo+4vxGIC6Pj7hAvm6EbqTOuwKbBtgS/tFG7mrGP9qSFMZAwMPCHMEGh2uSe5ml2pNUb5TqY5bqQFJ9UaqfWaojSfVHqQFmqUKSGohSRWapTiQ1CKUGm6U6'
        b'I9pt2aBOLiRHlBINEYWLYf/gOL2dnuOCco1EuUJRrhHoy2kS8mkkOcMBn1ztKHk0GwCLrxMYY+QKdU46Z50LqR1XnZvOXeeh89R5VbjLwzfYYeOEWVSnDfrvcVZsjOUT'
        b'g9+F6pIrjzAL0+VuzGt7NtI8LwkZZcrnsUyClvLYfkfcHw2Q9346v5/Ok/D7OdNT+jmZaf2ctEL0W9TPmZbRz03Nzu7nTk/J7+dmFqKzjAJ0mJaR3s+V5aGz/BxZP7cg'
        b'Dx0K0/CNOdkqHuauudMz8yXCfk5qtgr760PFoSIzCvo5OZn9HFlePyc/p59TgH4L01QFJMO0OShDMaIhc4hlKwG0M/4xmGjD+yjiFJlCUgWPuETmWrhE5tlZODw2jzNM'
        b'U6u5q3msS+RBqUaXyHjTaojQRGZJo+NcnkyL92RqwFp4AY80DWzIi4bbcuE2G9gQOcMUd5aEfI3OJE5Bc6SZuTMy0AjMwg5VwWkeNQmudwaXwAF4WRn7TzueOgmV6TsQ'
        b'deDj+EPf/G/7rtO72ne3625saKbtC7xmTXuYuzUsJ7ZHOlPgqP+IV+j96d1WJ6opyDaQ+4mES4Kl+4Ir4JgDOC3NMLgoHQGvgzPgBBecAzvHE4f46eAkJi4PbsmqBu25'
        b'aDawBQc4S0GjOykiFXTAS6AR7IA7sqNIiNMd4KoN5eDBgZttwZmXmvMIrNXNvI8ZMK14YKnxDEVCgPpTbp4t0h7XUWT9zev1yde75ZvjWQ3uapi10MYEvFX9Ak/HVlx2'
        b'ElNJNlDmdxFzBc/A2MUPDlCu9KfpwFeNjrlHEEadcIjllptzZ8YA2UTE5hsCZG/mbeZvFmy2QZ3XHnVePBXYoCkBTwMCi0DZaDpscDB2ZjvSmW3NOrOdWbe1XW3HduZB'
        b'qcbOvGBwZzaGkDF25kCZFnGSFLgC22FXtiEWIeq6UVHROHAyiTyMO1Vxfj3YkDFhOejgUnB7nQNsKgU6EvF4CTgLD5geRZ08L2om69IZuyhuQL1plhg2zLJFg4VHgWvg'
        b'vFbjIFwBtxK30jNtbHC1ucQu+UHlvwpCKBJhA2xMn4y9Ss8A27BjaQqeA53JJPuoSbYUauzY2CVfrjzHL6GYMCQHFyywCJps6WDahgNaqNmFNsvAdXCTRETmwtsx2Zm5'
        b'2VJE3xGxhKYcZBx4EpyB57RB+PV7I+G6yAy4Fbw3GpW4KyE2FmwozaaCwWUuuA3XTtXG4Le2QF1YpAy7Fd6WW2zmyVocHSWGupgIHB3aBuyqldjCiyEOWtax8b7sbNiY'
        b'mRMj8IFnKYEnxwnsAxtILyeBnGFnXWYkrvEoAbztRAnAdc5ocK2cPD0WXgXtkUxz2PDALcp2McceHi7W4skjEpydWDiEghliuEMKG/LFBjpBS3a+DQUOgl32s6alaLFM'
        b'hp7RLQN7QWMhokJMieF6cIo0A9wxylO9BF7ggRYXigatKGFlFQneDbtRPWxGdb5NGg2348gvdShfkRfcIUZV2iiV5hZnwO15BoffZkEuj3Md4Q7QrCUhMIUauCubuSWB'
        b'W3KiBJTrdN5MLjwEuhJJQ4EWf3jBUMfaEcUU5ZDNQaSuddNin07zp48pxDFeYCM4XWT20fitKakFFJXnYlMXAjdrca9Hzbl/Adw1gwI7nLH1eG5hmBZPe3Czgx3ijrrq'
        b'l6DZr6EeXtAIKKEvmgV1HNDKm6Qdi/NcQi+5qkb3UNeWzhRnRaGugyZz8qYCY+Xm14Bt6CPALthtT8FjcD0J6g1OgTNZkbheUFU1xsAdhWIxmqN1MTK2kkgnpeAuV7AW'
        b'nLZDEq6WRBPZLAPnHeAVeEkNry4G2+pVjovhFQqeEVOeCVywQQQ7SSUugpsBanXU93OjolFV86mRYI/vLC54X5hDxsy8OXw89EWxgs12C8bOZIfYeng1QL2YDzqX4oam'
        b'wBagW6VUuybTaowx3PLLB3uKcvPAFJdfVkuq26O+CIzqWNrr0BC+Zu3kDZ+M+uPOpQvsZhRG/2rTjcdT/s7/Z+apPfOu1Jwrc94wZlXC337y6ZUjv/KMs028u77/A9E/'
        b'MvdHZm3f3AMf/8eG33ggdbxN8EVpq0I8W6ZymHT+T62ff1be0aM/tjU2ITgn+fPk31+z255f9vMnAf6XPni0eiOcsvgtm6/8J0om3fot7Tfz7V+5PMn6jUfY75PFj+dv'
        b'Di0PFYR9+vCfHyRfvbr7w1/dTIhYDv6z6eQl/RGHd7ru7N5bXCr8udvHvlzOr3rGzV/9C2r97viYP63J/c37R383rfOYlNq2yHnN2yuyD0X8bU/HFX5IwKOi58nH6g4k'
        b'/2dJzx51bGHC7TMHLzX8qjLr2Tt/vf4zwcrjXx0/2XHz2P/2f2Tje/JH+38wImJb9udnDnj961e8vscufy4O9fr99P/Z8UH0k9kti37S/sMYTVSX/+rTk8/0j/p74xXd'
        b'rb6zawu3dKhTpPZr4q8HC+jga7Pvjr/R9Pani4T2C8SteyaKCv9KfbF+Web0r+ol3777xdg1I7J+G7xz/Nrkow1PJ0xN3POzqtR7SavL33t2HH7lOM/uaUv7w4+yHwqj'
        b'Vs06+etRpf++rLs94ts/+I6K1AUv/kgSTJywK/zeGsIUnI9APAGa1Ynv8lAxmvobpWB7jCwKtpRkYD/t5znwRBy8Q6KJTyyAe3Egc2e4e5D3czTvtxIH6eBaRD5orHcS'
        b'2qtCC+BlNbyiEQoot8XcwuXoJWSG6RbCO9l5UfSyWBImBrE9V0mkGzSLXKqCjTlZjvBduJWLJ2YaHACboglDAjeCllWIOMRSSaAOdMMbhLz3OWhoXQEd5APhHnAnFjQ6'
        b'L4FX6uBlLdwJd6KXO3hyFvDsiId6G3hew7jRBy3wAuNK/52ZTPmd8ADciXi0MaBNGiGJJlMlRXmJeO+ATniE+IVHS+OFlOzoXAHsBBsozjJ6giNYy0Tpua2Ap9GY3gJ3'
        b'eJdj4nnjaNAFz054imcbPw9wIxvNaQKwp4TivEPHzF7zFG8SggsRcK16ieNiLbzqDNf6oXG31dlWaA87nZegMQ6v1C9G9OfyBOCaP2giX6D0BNcjo+C2nDjaYy4lmE3D'
        b's/DOTHJr3kQpbMwA5yh4E96gkKCdDtaBM0wwokvwNg4Dn4cmx7MZubDNGaClODorl0v5gMu8etjiQioQ3BGBBpxtOwlsVB+Vg1i+KRy4FzSsJj1Ai7lI7HA/G7TCDtMs'
        b'45HDE9YmEjIyvDigMQb3Mz44D/ZQglJOsEbLtM+umAh0j5kh0cx/OJdPOeRx4J5wcIPQ6Q4OOODSURfMw8wCKh6t4QLYXUAFwhM8eDG9nJABNoOLoJ3NiTqrqBp1BifE'
        b'j6TCTeAS05v2g0MeJN7Tthwa3AGHKUEmx3Mc2Pw0mCmgaxl+Hr1BBvcuyMkDiKAcmvKBB3mL4QFwigwIuCe2AFUHu2T5gxNo1XIq5OaCWxHM/S5wA31tXnQU4nTibLO5'
        b'qEdu4cBTruAWCasQLxqP7mZJMxHfUom6k+1Yzny41osJq4AW8Ev4Lmx2xxmALo9Z/TKjOFSEmA/XTV9AaIW7BIhtb8yTSUFDDLtY8LPhXlQlV/lozoZdpHLFfrWEEkO8'
        b'MTTzvx+QzYWNY+H5p9gNPegAa8V4dJjLKZGovXfEWGqNIgXjUC8C20LswRF4BBwnQRQm1mRafxachroccIQvEVA5iMW5ABqznxLG6QDYiP6j5s5BI2E7aECfh7redgHl'
        b'gYb2nRnz/ouhm4Y6wyD6F/dB7D+jeCHCCHayhiORavyxcVd4x5j7nglEHGFDjX7pGYA9ON73FJONvvRen+l6t+mPPANJ2NKYnsCYB4EJPYEJndOv5nTl3B15N0ifmHpX'
        b'0RuY8/LhTB95+vcFhnck9QTG3guQdcqvVndV383sGS27F1CuLyhvmo4dA89rnccA4Trqz688vbI7pXuGPmbyXc9e/8ym9C+9/Y/4t/o/8I7o8Y7oGN3rHd8keOjpT940'
        b'5e7oHoPzl77AMOxPqiO8M743cHSTI+tFeNfKJl6fq2fLkrbK1jU9rtG/9Am9Vzjr3uwSfVhpr0+Z3q3sS1fvB66hPa6hbcX3XSPRx2ZfyCalZ/X6ZOvdsr/0C8ZO59pW'
        b'9PolNNk9dPVr8zzl1+7XMb9jsT4ortu7JygFFdofFtlRdH726dmdy+5HTR3g0qOmYb/qvqnYr7o7OqIVI7ANSYTRnfVXV1xYQd6QendJT1hur49M7yZ75BrQNv7+6Jye'
        b'kBz228b3hMl6ffL0bnlfuga1ze1xjUOFiKU4+MOxlQ/Cx/SEj3kQPrEnfGJv+OSm1M/cQr8Mj2xKvY9+A8OIQWKwuMO3JzgJnTsbjRuZOwYzQ9aIknHOfGAuyRISfiq5'
        b'PfnUpPZJD0LG9ISM6Q0ZhzOL+kThJDNbBGu4OCqcMaUMjWFKNIs5y+r3iKFlEEOQBFsYPgge1xM8rju0N3hyE2+Ps5kY7Mx6DTLY//LwrrwKO/xRxeKtFIfyMo3RlFeg'
        b'Ll+gqFa8dIgLrCAoZf9YBLp4wTi6geXoCej+f9BA+laNBOk8+lsKH19BnlZjJvWoIJ664DCR+wZIc2x3TD55OC2f5TcY49paIDhf36yw5QX6Retv/rcldlSMIYRGfxbM'
        b'p4jYQAoisUpRJo+qralaJnkDI03GtqHfoYQ1nyhRyl+NZJpngc6N6vGPWsuSL7VmlqFUm77I/BPexDLj9gvU2dap5iGqzWyEAoqIMQY2xTDaZ70pbQzkGdvAazW1FRWv'
        b'Rp8Nz6IjxBCEvlYThQoSYYcAJgMSTDOx7f1eKlM18pX7rD0m1QTQjSAAXWUFi8itxnBs1OaKGuzORP7mVDK6+37HErOZ7dUIFmKCHQyqX8Y+A8OIK3HIN6NF2PdBpyrg'
        b'lTumCybOBMMOHz6StiWJ5m83KrDfoRgFNnYZVcEhG4pEqWfcUKTJhiJltqFIm20dUqtpdkNxUKp5wMDv2h0XyKx7pyS00SRoNXZOZAhTbdypf+Mw1RsknEcYCW816HG6'
        b'ebBkSxSvWqReUKutkmM1N5prlRVKbHlbWYaxv1bL0rB+kUTTqhRl2ERClEq8fuDuxEZTJuZUeIFUotHKwP6V1qMxqxUksmJpaZFKq0DLrtJ8nBvmJjSeDHBHEq/QakmM'
        b'yckyc0sOxvDE+Ir0sio1fge2K0QJjMGEdbJq8Xguxw4u5KjzVdeVaZTzlRjhFC0qrsMPLxkTPTZ6KaE1YlFtjaYWLVbliyKsFlaHSsJLQn2Z2iLitsF5Cg6gPTR8If5j'
        b'0deMI9HY17gy5Z+O/ZOrxlKZ55qIAx+Pzfr5ofZdQY20Ky+h7iSXGn+f89uT/yuhibA/0RZeYARRk1hiF8IIJnnwPTRuXQzjllVC8yoqFZrloRYDV11eVUK+FQ1h3Ejq'
        b'SdE4F5En8PNYubFERPmJsCsKvZu5DoMFj1lyYkR9UmrQe6suYZXxS73RjcdqMP6xlnqqENH0yFfVYDQJRFSbQyTXukNoggrgsJFI+QTQxzXGIDWqz76PGKTfNaWgZv54'
        b'dQ5HjVGP7SseH/h4wqF1De272ncpk0K4XprkxfE/Srg7JYxb6UPJf8aD64pRg2NhVAh0cMOgFge3x7KyKDiokXAHs8D45UZHm7wK9Us1v5ptftYt6+OVIio8siPp2KKm'
        b'1D15Zu3PulC2H059hQEZ5tqray/XF9DrAw194fla6psVqC94v0rAOaxZkHAY5cMtcHJadnYePLwoiqZ4zjQ4Bd6DO5h758A+uCc7UsaBB/HNBBpcdAS3lCu++T1HnYAy'
        b'uK+ZceDjxEPrdrW/K9kWd37Mxq6Nxzw+/GOprDyrjHPBe5HXQq/Clq9i+Who0tQHOrvUqvGGgTGcXtGE7LEzfvpyD+tVQtqA9eDbx7N9Ol9kNyLymQc9Iv5LUWiHvMfk'
        b'x9TwVmuNYPFW1XXcBMO8z9VQ6eh9z8pRpdu9SqVf5gznx7mUHXgkADDFruPf71r5coOuLITDVePNqEe/3Hbg44UrE9lhF4fm17MVG/QfOB6Moqr385JDP0IjDqugkkrh'
        b'+y+z2fRWXqSA3WsKmivhmFU/hwxAM1DhYO0tQROSpvZkh1t6EOXlawVQyLQy39qka8KOmQ234V8XajbVPksLerWpVrWaGq6l/y94Ist2poa0M09WpLz1VRRPjfe6jwoz'
        b'0CK6ZcOh9p3NCVzK/ijHO5lrAF0OWh0Z0OXgXQEGbUnax45pn4Ec1D5+r7gMvqDscPN1L/tVG2P4Yfdfb4wh2vihMZnRoEvSJNIEJaF/+tMDP/P/eOyhdowBSfa+0OIV'
        b'O8Uj8mTfQi/hZ74E//F5CT8oeKeEy4TMfRdug+tgoxRvJfPgXtgxhQaXs+KfYv1+Rg288VK7wOCWl2FkwlsBBDQCW8C7M5iwuFECyrYOrIM3OKAZXp1jpVMQyPKQrSKC'
        b'VSadQsR0iqcFuFMY8MoP/Eb3+I3u9Rtr5uP+5fvKC14ZYd5XZrxWXzFHd/gZGgxvv+xxt4ruwOAuJ+K11wDvEuhcCeLDCPLSeet8dDY6Xx0XcVV+On9dQIWfEf0h/L9E'
        b'f0yQkSDeoyXJLCQB4xHATbDDaQ24xkAScINxwa5kBxW8DC87YzU0vFAFt2kElAs4zoHXl8L9WqxpUIIzyx1iiYY8A/WVPHD2BWpy1JHgpqUO4DLcKZcIiHZeDhunq+tt'
        b'4BXc5ZoosHWELQEnJIRK4UV4aq4WsUfwCAWabYCOCT1+GbTbOQSA3fAKH19RoB2cdCNljUKJl9QTQzBuG+oosGlSHSnLxivQAepgF+5B8DwFWmj4HnlgNGyYrJ4Kz+Fo'
        b'cXAnBbaUyYnmfDZiyhwpaikVVio9GrqKIi9OyQNN8KIQ7IRduJxjFNgLG9zIrVnwIrihHgfXmz4DdIkIggB0RIJWVD1wB1yrGVwzsFOjgpcKMyKxMpFUD2gCLXarSsE6'
        b'LVE1rgsGugTYlBDLo2jYAbpQTcC1+bBZi1WKyxbaWaBfDB6nZ+TPgns84YmErEIbqhi2CFATNntr8ahBFG7zSqCUqHaoOCquXkvqZzLYHAB3cdGXNVBUDBUDz8G9VX//'
        b'z3/+E1rGw91nSlxOaVVkvZIiGBCAcjZlG18GdRlSjPvZFpNVLIYNiIpCsQTumJXhn5+ZizEiuahbgCsF+OsENcJ5daBVm4pJOQZvo2pphI2zMkwZcSdCc1JDTB5bReaY'
        b'Htx9zoAb8F2w2xFe8IOHtaWooDVgK+wSooeahWBtrC0fruXAvcXwsABuLxKmj/SxnVAAboBb8DA8n1a51K7Cc7E9vCmotwVb7PIcQSeaQI/HwlsrJIFQNz4a7heAfdMk'
        b'4OKkRNjqBVrAoTnaIkxtswgHUV8H1wmpOFsu6CwGF+bAPQLQADeDPbChNgJsgLfgDrC9yFe5GnTAtb7g1sJgX3AVdYWN4ErFCriBGydGRGwLhF2prrnwhEyFuxrpb67F'
        b'vnQih4pd71060TGBQ5GRtQy97SZszAVn86EuE1VBzKgI2JBPoFlGHAk4lyHLzcWII/A+vOpQDjvgHlLkjeIMqgkNfml5adZ8zduUFvtQDfXn429otaNEjuhk5juLwE5w'
        b'Fl6H7XQcWA9PjE9A7bGrFI3Ps3B/cTg8NgcRvNa9CKxXoJMOoKuEbbDbZgG46bLsLbCRdPDCatBqQSVLY0ZUFn8kaASt7hj4CE5L0D80wuAZO3gV3gTvFkloAmNxrK/A'
        b'nQCtSXB7phTNFC5vo3b2tOXFalZqx6MM82aBddlRWbmFGVhVHZmJOsjWyJkEZWns+dszpFk50ZlREYIZYAMFt0gclWAHOKLF8gm4DG7GDA/DyQGdBiQOA8ORgVOINLzs'
        b'gLZieB3cAlsxEommOGA7PQ02J2mzcYc4lAfXR2ag2tuaywyDmKzMqAIGNDcEjUW6ch2eJPMLomZyKNCIRK6t3s7wBDz9DsGVwqMFEQ5L4BXyMWg4zBQjardLxRm5oKsA'
        b'lzerjplj0Rdsy6bBzjR7cFgGtieXrLZHstpGaiy8LcQq/xkMXm45FzMaIhdBadUfHOIwtghPKLaLwcZsosHO5lK2c4SwkwN0YDu8oMXKpCkJsLkwT5ILtuVlSjOLZ0Fd'
        b'1CSwfjAikEJ9/j2wFrXqTrh1rgicAd3geEYQuJMRlADO8yg0qNeNBK1B8A6BWc0aPw9N5Bed7WzhBWd4UbNYS1NusKVGzc1DXfYamT9BB09cCPckZHEpOgSch2cpeNZF'
        b'TTB+YEcauJItiUJV0JAjQ1SJjaxLe7bB8nGeyBas96QY6FhToX8h2FYEtxWjUcFfADoiaLAfXIfnCP5p3DgtmkP2OyxxotGUuhdPKG2lDBFnImEnqsEr43PQrbEUqv99'
        b'4DLpo+h7D42AJwuyTYA2hzkc+D7cD48zL92D5vczGNBC0CyT4BECaJmOXoon2BmwG14CZ1QEGEJQIStZ1N9RfhUD4eJTvHC4KYAGR8GeZcxL2xxGI/atxQCUA+/xKEcX'
        b'rjsaiTu0OC6eH7gCm1HHluBqyJVmYlgDKUoAjqC1cC2/Ap6CjVq8TQYuFFdnm0UkSEXEtnDAHtDsSvpFpB04DW+mRxogB5RjJdcZtII2skxWl6Vmow6BSJw5h0eDIzzQ'
        b'THCJAA/sw7AxSkbwFIJ5HHAry30Kn1SnEp52h40Ed8JbBBtG0+gNG5JJGyxHaxMe0ejOJHgKffOx1fA2KZGPityFCiT3FoOdk2hwBq1ebQSeORaehrcNJKI+mgqOYhgd'
        b'nwoCu/h2YJtMG0vWzJBwNNQb8mRwK2iIGVQ9VeAAqWwZWGcDm8ABcJ68dwHs8oiMzpRK0NRjVws2juOAE/Ag6CKNWxqG5vaLGI530QZNArcQQefoKDTHX1Qq7Tfy1Nj5'
        b'l/uGOxtn5i76xRSXX+6RP3wya/74rqof/2Tf//xAee94Zm/oiRO7R2a1P71f2PbjH+qTukU3Mm3PZLdvjjvhlvKHHXWr5dOvhGb/KvePcM7hbyt+95M///njNfvX2F0a'
        b'1zx57r7qrfHVZ3OPTOSE1Xx48AP3Xv610Jrqlu3/dPy0ufnamFFB5cmr/i2b/fGxDz+JuPRb9zm2Cb4/6M3/4b86ohPbv5XZLf626aro6x99cHWR7bz8ksv6t64/mJqd'
        b'9XvpbyYLt3RlSdvDi6fNDsn/i6r0of4e/Hf34h1+u3cFfPjF+viSog67sTePdogDjx7+wB5MObeqbEDBv+gSP7vrr18XtizOPR585uH4I73doq3/eG9p8fatP99flRY2'
        b'PviHswLuHWzZlKbVnM4+8+Xd0Wfrj7Wqv/1X1t2G4l//rTra44bbmQ/+sXX14XEq/aLMlqD4BT/4+/+k/uhj6ZUDnB8nzFb89mnSzMc5Ze9FOH61efL1wK9z6gKeHPr9'
        b'mZ/E563+8Zm5+/886+bH/7Phj5dnV5+NWPyXt6b/carNn5wHFi3+d+rsQ5/9zedRQIZ/ScNj3xp3H/iZy43jDZJFKeU1H/evnPfXxv/9zeTKZwee/+7xveCJC+bw9t8M'
        b'O/bHFcHJhb//01+PfnXl0xHK+w+b/1K/Axx2/GZ+8ftbns7d47ty1jcVixamLS7Jurvk3EeZnUEf/+75jQucb5L8F+zu1BZdPZV/dcST6UvuuP2gb8t8uf7e+gWj05fc'
        b'7UjfOrLvn1O2++ae+2WJ/cq9xyb9dtPmGasONHj/pe3jkHH7r9vkOy9cFFe5fMX6dxNqZDNiQuK9/vLWNzdyZBXj45Th8V9Edfzl8GeTb5d8/dt/13yd4G339Qejvvnr'
        b'ia0XzzXFjQY5f3w4/xe76vM3jYhxUMy8mVn240/+FfHNn/Z8+rvz7knyGZUjPG48dSjzb752osomq3vSzG/9muc9u5bygzUrbs8IznNZdib1mxHjZgXb5P/o2enY86cX'
        b'5QcPrP7zwu7fJP/0Ru8Jnf/6bX8a8c3vDsWDhLJHyx21c480St8P19999vTwf5wX+lf++YdR/0q75bf81qylkn/TdpHX454ETx5YcVMkncA9UL6q4qtAt8Pjfsv7irfo'
        b'p2fU9p988c4zzdc77FdXLJml+zz8XvC08B/4/br+2/X//Pnq1beCHzznXzs689vA5zN9vkzoloQTmNV8uLG8dKUJl2ZApcHtEQRfB086TIfr0JKQF0UTTOGYJAavd0qL'
        b'JJj3w01TrB88QcBSBVVpDkSMJShGcA7eNiAZ46RE0kVJpyMNYGM+ZQu2gVPgMmfJW+8wSLZOeGc0Stk6ePYHW5OY56/C7Ug6Nkz+qLgrZPaPCCEwSbgJbIJd8NIKA9zS'
        b'iLWcD48yMnxjAdzNiNp8SrCQUwubAuAJcIRg7OyXLYiMiJbALWg1tBsFt81GU5NPNQNJO4dmqa7IaLw2StH8C7ZzwOXoKHARnGMo3w72zMs2wcQQo3eGcp7JrYLrpjwN'
        b'Z3jwraADY+MwA5bHsOGwGXRiVlxABWbz0GLTXciA7BBnKI9kCRGAsxyUsDEBrA8i1T+3UMCALQnQEjSPjwJbxhLgYxknXA222S4WwgtqDLQGu4ut4B7hZQG4DRtdCOSv'
        b'KIOKtNDXUCMjkKDKBW3gAthFqJkROxJsnI86Ac6EW9xhBgcR30U9jcK07p2ejmZsxCp1wa1RhC/FTFpm7uKoiAloOcBY1mxwxgZ0Iv6ZNNJ8LTiSzeoKtjMljpDXw81c'
        b'sDVETSrTQ4AYSVTilpgovKBk24A7Gso5j7sA7PNkWqMRbHK1nxaZJ0XSXCPOQTnA2xx4dRWHkJwMDruaeK9gb4b3agXdT3H4icRKMbvGFtbhNTZjCXmrExIBtlkieWcu'
        b'gddRJxu9kvQd0O3ja4A+YtgjWmU3e9qDgwTI5wabRg3Z/xGONWH5DEA+d3CV6E4KFOCOETpqhhvtQBLUZV79gkVPMeNhC5vgWQPY0RLLCJqFGM6I+IIbDMp0uyYWdZqs'
        b'SLII88H6CsoZruXWosV1Fxk8ozFwdOx0JEGgGiMV4FDDgQfg5YWkXy2DulIDP1ACrmF+wGYyM+pOg8sjjLwTPA72YeYJsQgtpF5iC3hgZ8Jg3ql8KcFjwvMLRlljnOAB'
        b'cJrhnMbYMsDGNns0xBoxcpSBjYImeABVtAfcxBuJuMqjT0fjXMcdwl+0zTYGHDbhLdlttrrFDEL6CNgLz/qtyc7JRNNZAR2hAGdJb1mNuOv3sxH/j7l9VOMdkeAMZ9kI'
        b'JNpI/nsxxv5/OJBNTwvt79AYZ4MAnv3Og+ICMT4AjNuAg+6SDch0PrMrPSeIEoUeWdm6kgFydtp0j+wNnIBRkQH7Vuxc0ecZ0rayxzPh8wCxXpLzoeZnKz5a0SOZ0xvw'
        b'tt7r7S/FOXq3sL5Q8amc9pwHoUk9oUmd8zsX60PHNeX2hUlPzW2f2xncGacPS2qS9XmGdjjd8xyN00vaS+6Hje6O1ufM60me1xcW3ym/F5bcvVo/o/je5GLyqowPJ/VI'
        b'ZvcGzNF7zfnS1bt1elv6gbx7rpEsbnRJT1har0+63i39ob+ozQPDLHv9ox/4J/X4J3WW9/onN9n3uXq0RPS4hvYFSthP4/YGJnYW9ASObcrA9uBjd61qW3zPU0zel68v'
        b'nNcjmdcb8I7e650+T3+Md+0Y9SBiYg/65znxrvjH0R9E62cU3U9h6JPpZ8x6MKO0B/2TlPYGlOm9yh65+rdUdvA75G0r77sm4jeM2bXS8IYBDu2fRn/N5QSm0wMUxzsd'
        b'4zxjRve4RTbJ2qY/9E3qrLnvm0aKfqc3oETvVfLIEzXGfc+xfZLYFqe+4NBWmy8lkegsKOZBUFJPUFJv0JgHQRN7gib2Bk1ucurzCToS1Rp1IKbJ5qFPWFtlr080OnP1'
        b'aKrfNaEt5J5rGKk4Q52h9NW9rqM6RhpqtKDXp1DvVvjI1ZO1lG+L37maUJPeGzBd74VdnrWu6EjsTr0fOPWe51RyK7s3IEfvlfNiPKrnvkk7J7VVnqptr70/agwmM7I1'
        b'smnaQ9+AAQ7XO6gvOPxUVHtUp81Vxy7H3uCJLdgTk5dvX2DokTWtazrU3bw7wmvCljX3A9M/D5bqo+bqS+b3RM3vDS7X+5V/6RVwxKnVSR9epJ/1zoNZ5T3oX3j5fS85'
        b'cTTUntyxoJt7P2TCw8DIjoz3crvpu6E/jvwg8n6grDnjoXtgm21HyH336IeB0o63MBA4AwfeXdBhe981ri8w/Miq1lUH1qCM3iFtGR3y+94MIvrtXp+5ere5jwwhR9vq'
        b'T61sX9lZdC8pq3ten29QW3rr5I7pne98zaW90ugmHqoAlHFC64Qe13Cm7/b6TNS7TfwSuwpD7RJCXIVhxwrNqY98A5hQt6cTOjQPYlJ6YlJ6I6dhVLTXA0lyjyS5e2yv'
        b'JBWV7JdON6VinLDXvonNE9vS7rlKcMyT1D7/kLb5rW83p3/pG4xhFw98Y3p8Y5pSH3mF97mFPuG6eo985Ok7wEe/2EdV6IANOhuwpVCj+O33G7DDV/aUt+iIw36HAQd8'
        b'5Wi4J8RXTuiZI3n78wac8ZULFRLxIHjMveAxAyNwiSMpv+ABV3zHjfKPvOeX0el010Yfk3HPb+aHsz7M+vuAO87lQfkED3jiXF6Ub+CRmP0xA9443YfyCRjwxWd++Mwf'
        b'nwXgs0B8JqKCowaC8FPBlCTqvONpxwfilHvilIEQfDcUvzkMnTXxB6TomQfe0h5v6QPv2B7v2E63Xu/RBAj+0B9ddC6969Xrn9WU3ufisc++2b4lqU183yWyTxrfxGPc'
        b'VrSl9rhI+lzc9jk2OxpScBgWT78mx78/XUNTooQnFO0d1O8nGuCi3+ckDuVHEb6FYqpXbFeYxO1NpNGRUdwEMoqbXRh2Rzw+hOKDmGCUFUuNSD4zdwvfDVD+3lccvCs1'
        b'CPBsParmX42OeIZbW6KwpimDYnHQs4JoupDgoC2Pr4KJxq5dLgimcqgPOA5ThVwJTfxTyKyDdSooHECXBevQBK4jYO3jv1+4TqWE8+ghxwrKbmqFRqESlZdVVZGQdRj3'
        b'y4bwQzWlxFVUVmURyY6JISCXM1iwMlGNon5IoQymVFxaml+tyaypQK00v6q2fJEkmo06aMDtadWKCm0VBs8tq9WK6stqCOJNrlyilCuGFGpBhLKGZKwgDvtYJzUKNeO5'
        b'hgmVI8Ie2kVKuXooRG1IQnJdmaqsWoT9DCaLMgn6DvVytRJH9kPvwUi8MlG5Vq2prWaKNX5apry0VILdOA8LOUT1Y6gPfKqswRi8eFQVKaga63FlahaUaYzUmlCNVktk'
        b'v42EGyQAY+xCmRSAgw9aVJHBB1ClqlZbR0KNDIPyU2mU5dqqMhWDjlTXKcqN7hPVIjH2lCZFVYBeS/zjLqtDlwpNebSENMIw6EhcoRqFoV3YdieY8hpEsxZVJCof97pl'
        b'htaX1xIPRHU4UKW1Mi0aYGibfoeG3l7GKASOLpyYDRvdYKdBa+oE3gfbGZUpFizAe+DiEgd4BZyfPsh8l7HdRcLEeS2OcgebFGA9q08S2XLh2mJ4fXEs3O0TkOEatngV'
        b'PF8ANoJz08Dut1MyNeAMbAedtnC390SZ1B8ehO3wYCq4EbgcvOcSC87Zkh3/+TMzscInNjZpfOLlAhFFbIlHFNJkD7ZQjE3ssJU4Nsu3odzB8eCFPHgmCp4kD/8qy2Aq'
        b'HKsauWYlpeStaqfUh9Cd00ePYd8U7bvGNdKu8rjyLSdiT8aeq1jfuci7oGWR18deW/659vns2M88Mnd3wmdd1Gd1pe+d9vnB/PLSt35iWzYmbkm8xyLNBfni8vfeFqpd'
        b'nT3qn/xm5hf8xIsZWxuwt4sRFXn2i6446LWfh62ve9AVdKN9fVdLQ3MQ3yvi8cFY90Ofum+dHdzyzfHOWY/jY0MTfqj+IDXCe2wCVbgkIEFdK3Egkjdoq9ByFg3dM3KD'
        b'DUTIKkNC9PnsPEe4m90zmg1PEHyEw4R6JLehJjz+EoZyrOCmgR1PRejZxfAMvK3G+rco2LRGbFBFjIBNXNA5H54jQuqKyaDNtLMEruba4o0l0AG3MhiL43Av7IyMAleA'
        b'jth5Mlae4EQ12frJQUVego0ZanAWnKMYM8+DLkQuLgbtkyKjKkGzcc8lytGBbJ7A3bHgfbLhBfbKLS13l4HrxPQSbgK3/UEj2A1ODRX1kZg/Dlwjcr497IItoAmstS7r'
        b'E0G/YcF3eTY1Bb/rt8NOOMigHoSuM6YzBnoUI6zVhVkX1vpYsy/EpT/wjLjnGfHbgPABipZMoftS0jHP+5hLS2TYzCwwD5uZeefRj3wDEQeJSkP85oGVBiu+pJ7ApN7A'
        b'MS08JAm0TmvjHcjs4OyXIca1raTXJ0nvltQXEn50QkciY+dFPH3dQwzS4h4X8c9Z74wGPyWE7wl/EUfD+ikxhXRX/XsozNBYEWfNsJ3fFofRtNerYFhwK2OrFLRClqAl'
        b'0rrjO8I90Eb/Oox3Ha7Ruw7/+/Su8+jvPCvcQ6Giho2iZRnTV6tmuAkFmc/R4pOWkjmt0CxO73BLsGK+slxdUl6lRKUkEzi+wbl3BQ6uU74gmuSITsPHaSTbcOF/zUpl'
        b'azGZ2BNIjQYFOKyeWkHIrFXJcQJa3KwuPmw442FpiE4vzikl0R60dVW1ZXLD1xsqxDpYX2WG+cfrImsspNYqNUxQYSNR1pfE76Rq2rSiUunrPlr82o9m5r/uo1PfmvPa'
        b'b01Nff1HU1730bfS4l//0YRS0TCM40s8nFhq3fYis4LwUSwbp5BLRRFs94+wsCqxYrhine8axphFlK4qIxEqv8tuxTqZszCnzswKSxKiYy1GCwm7wkQpY4YTeuESZdnr'
        b'1VRKUbEVEpIZt+BqZo5h6GCGm9KKTct3wPHcZYQHcyoUUI5L73EpUanUY1UY464FnpKAgyXgghpbssE2CrRmwuOEF3WBt9Dfi7GxsXyKkwluyih4OALuZ5y87IO74Tlw'
        b'eEKkLBrjVvbS2c4JBIkAdJJ68G5MpCyLg9LX02Nz4PtaLNHbv237DjgZKcPb0EBHT3g7UMIj0ACwE7TXEwQHvMCnuD7YHwM9sQh2MQCG9+YWoJudGngVLQxwT9ZIOgis'
        b'5RHYwBLQBtozstXxKg5F1yLuJ/ZtBsF3DPG276vhFWcVIh2eVETTEXVyBp+2wc4R7kKrVWl1DBUD2rwJ0YG1cM/bsEttQtcpx0s4DHU3wGXanLqrcA89MRWcIncrFiK2'
        b'zIy6ULCbDoJd4AKhffEIcM1EBbhdQEeAHSwyMCW7xgkeNZEOjr4l4TKYvCPJ481eCG/AtfRE0A32kDLzqsB+8zd6raaDcuBOUsXOC+IdltipeRTXDt4U0TGek5km3g7b'
        b'4CkHocqZorjSNBt6Mji2khQ2rgyxhxfhJQcnmuI6FoK16NYJsF6LXUjCPTHgBAbA7CgkLucwtAnx9xQ8CnauRPW7dTRohxvATcTkHSxC17sRD3wc7kTCw25wcySfgntB'
        b'p+Nb8JKE1PBqcGtaGdxeiCqXohZSmeAa3EC+FqPY4K4ijLYqxP6zdpaBBnoqeG+psk9+kau2oSlKc8MJ2+a070oiEkIZkhCOx2bF3Y/XXEjq/Dk6VyyKjdV0aS+4uy+5'
        b'IO8qnfGzg9U/vZu/ezfgbDgrqZL8Wf3Whb64z+h5d9dJru8fkfIg/uexslJpVvajD3/9o/f22RRe2hS3ze79I3YdmwIb/5F/fa/375dPlVbEfhZ7ftOmlFjup3fScly9'
        b'vnZbO0EWGxNw4xeF3Ugo4a37nX25Ou5TxQdjVx4GwtG+x0t2S/81ofRfleue//Cjez9z0NwKyJdxCp3+HKHknLwg/2inIibw8y+eyP/w1eY/zQrNnhz8+Z6P7v0p6Gfc'
        b'B+e3lKxpSJ67g/rGbcKBuDSXG1FTvNt9ROP2CSvecQ2pTKYyNbMOz+mRuBGW/q1KuJ1RFM9Cwp5RV+wHNzAc/6m3MdqNVRXD2/CylAYHUKtsZjS2W8UukdmIZ9+OePQ7'
        b'jEThKOXawNOw6ekIMhp5HN/xRuV3VBRTahd4F7YSD2F8igc2IAH0CA3fBZ0ZRD5KQ/LDTcZjDeOvBl4G79KgazLYTXRli0QCeBxcN1eBIyklLZ8oosIywR54CXRGYiUy'
        b'5vttYSMHrIsLII+6gi64EawHOrUDvIwRVY0U7ABn5hMhJQ+cc8GSamNdEhpGcDMau3U+RLIB2+HZ0hVoikK3BOgW6rfNtaHkoRS4nsMPxjdwcQ0U3AkuhzKK9K5JctYP'
        b'DJpZtjGadOIJBlyQk2fhHl/wfrxcTcBd4CQFD0iRpIXvJHI1ApUabAU6TEkTBS/FwksMcOA6OA91CiV6iI8eOkXBg29zmDuH4NZReRSaIhwRSwvep+AhkYAIlJPgPt5b'
        b'YKd6yWL8nhbUbM7O5IYG7n6HU4rS0VvAXgpuAcfiGJdDZ1fOxsLiQrhOFjVIWIQdnkiAeImNSyxA4PXEZKqmRgz08hGWhkooiUhROOoZlqKmhBulqNiewNjOkZ1B+sBE'
        b'LEX5NE3uC4zs0PQEJjRNf+Tq07KSdWyy5F7gxL6wiM60vlBJZxKSpvyTv0ieeC2kW35HeU15I3qAS7n7/NrTry9k1Kmx7WM7is6/ffrt7jC9dEpvyNQW277AkCMrWlcc'
        b'WNXCQ+Wzwpttd2hv4GS91+Q+96C2onvukoduXoZTHGFmWfMyfWhij2ei6RFeb2CS3isJx/L2bvVuq7jnLR32puKed+TQm+7e+2Y3z9YHJ/e4Jxui3gzO9OUwT7WNuucu'
        b'7vMNZx1Bp/b6xund4t78Ztg99/AhN//HI7AvYczV8RfH3+X92A7aPUyYPMDnBE1FQiyOlTFAcUak0EOMCvsdzQUe1X+Gip+sdWGp0WzCEy2uVnrMxwZx83/XUt/MGEXT'
        b'klcVNw32QpiVUb2HLeI9B/lc7ueV5GXK+h1KphUXFKTJpmWmFTKBYIy+mPsd6sqUNaw3D9VerDawN3msYNQKGKhKvJ6o9uAD8XJy3dJnM3HhjDfviYRNPlni8/+AqhtP'
        b'1d+h21Zl4z0BC2e9p7CvlWIm8suAE+Ub0FbYye1OuFve45qlw3oxT7+2pE5+d3Gfhy9z8mGY8fSxDc/XSZf9zJErjPzWfpJwCupK+Ph4CodEMJF8zaV9I3XZj3BcEkmf'
        b'2yQcvGQKE7zEJ/ihS1SfWwpK8kmldVmmEDGJOILLaBLAhQ16koafm06bx2vBIVTcU5gQJ2ywFBx5xXccCZbCRkbBEVy8Jusyntk6CRMfB1DeQT1eMe3jjo1HP7rMZzxa'
        b'GIudX/vhQ/KALTWVnkZ/y11FC/2/pUzHx+T4ZDWXcnJvDbkvDPiG4ytEn0Y5BQ7gsyfJ+EbRfWHwU854YQqN74Q8JqeMB228vGRqZJZ+fdHa7TOdl0EpQXusBQtvcLP/'
        b'9QbsNdsNG4+Z/GbP4WKf2Yy/7IM81mM2c479Ztuhv/jckfWezaSbzl3kI+Qj5a7k3E3ubjz3kHuicy9y7i33kfvK/Q46zOEp+DpBBS3332A0GMLetlnP0LTcAR0dsY9o'
        b'9H+k4f/ZgDM2TF479FcezuqNuPJAM7/RNhxKwZeLNlDyoLPBRu/Ytqay0X9cOqeCw5bryv664F+lKX0kSwP+tUP/7St48pCzoRY0iLH/cEyFzk4n1I3UuVXYysPMqLEj'
        b'nrQFxHv2iAoB8bFtr6OW0nMciBMOSf9IPGSmkcjcxOt6hUL1PN5CEhuagYnhaZHpeTQS65KV6tpktUZOfuNjY+Pjk7F0mLxULU/GE1R0bGwc+o/kzgQJt58nyyvI7edl'
        b'ZE7P6OcVF0zPP033c1LT0NEOv7IkT5Yz+zRPhdmDfj7Zjem3Y4K0K9Epv6KqrFL9Kq+Nw6/lqYKwE6FgfAjh4rk1U1bIBMp4xbLGSfiDylJFkQILU2dOfZ6yQKOpS46J'
        b'qa+vj1Yrl0ZhOVmFHdFElbNuMKLLa6tj5IqYQRRGI2k6Nj4avU/CMZV/mkN8f6vKiP+ZfrucvGlTc0qQ+Px8FCZ6WkomoRD95pctw5NfAVYcqTWo0OjYRHRECwwu7DSt'
        b'msEEJgnHtDoWZsqm56SVpEwtmpbxkkXFSbgMXcZPfj5m0IPTVLVqdQqR6y3LyKmtzFVXkpLicEkcU0k45g0uy3lQfTz3Gf6jnrtbrTyJg0UpuLupxlope5wqGacOKmQc'
        b'KSRBhYOPv+Dlcc8jX+FL+23kiooybZWGVD9py/9XzGopyorHdrLdcAE22mN7Dy94x2DycShTmXO5iU+sn8Uh8w9ge9udzQk+P/en7Ns5Xrebh7F+7rctUdVqNajbM2Fv'
        b'LOeTaMNNS0PoCMrL/xWNW6dxDYF1hnkDxrMZTVwzI17DxPW0DcNP7bbCVO01cFYWdrD2hhrGpu0M7MCKHazJzznxcV5hb7Rxdfw+bVwfrbexolDIZJzvKJcrzNQK5aQK'
        b'Ge02nvVfoEYo1NbV1arwDmUdiYVMGFF18tCMUaJBI1MkTk2TvDgbHtnfmWOcSByhVmJV+ZIx0aMjXqJIZrIQiadlfHdmdlLAmaWi73rP8BOWSJxZ9EpPxL3giZede3AR'
        b'g4keTmPD7joz27OMVyW5Yr6mVmUM4jrck3iBZh4b3G3qVMpalVKzjAmJJI7Ay34EIggv/BHWN/EjMDuA8+DFOQJrbCLwqhohiTahOUZHx0fHJrNZrBdjAn7Ekqxsqabk'
        b'0SSZKXq4D2P807GfZsXHHFM/4WriZm7Y6iG6yWRLx1pkkFn3A8c6xhqWJpNzN4YwZrwO9tKG/aAZsT9WoD34D7qnxZpCrEQjyguCO1KUaXCHQh+1bLAjPYx8GcY7F1aA'
        b'oHKwGywGpmQWBJjUjqhQocDfqq1SiMo0iJGbr9VYJ2va1KK06XkFs0vyiwvy8wrTSnDc9UJCpREiRDyFWcEZsZXETEJM/eRPzZQZPEQa2s0gxrOqG+uIGpM6h6gImRJM'
        b'2paIQXNKxLCYJNJCdcw4VZNKHPTsuAjm6wxZhvFbxjq5QywwowHCKKQaUVpxwTBqqRpRYb1Ss1yhqiINp3kB8cyEOMxYQgMmU1NWtYw8OPwMFzF8n2W98zENYnLah3s+'
        b'2yRGB36MhniYL9IwECuzmGkWz9ZacQn3sio7VD0sn6Y2dN9B5VpvEyKVmI+UzJSpMtF8RVVtTSUu6TtUW3ZDWDAXGTGvnCmuIwEfYBOXWoRtYo7RYnAKbGRUSDd4sNnM'
        b'EQViz444rcxlQFX46Vq4FR7GYUEocAIcYuKCwB1wExPF4Y4bPInldrAVXkV/L4IGHjXLTQg3cGCjrJZI9pOyp5isoIqwtS64ORIe5YKtS+BlJhDKJXC9rPA7g2igjNvg'
        b'VXu4DZ61A41wvYRDNDjyRcCop1kCG7mO9OTRlYZoC8cdGdWOBr7HldKT80AzsbWGV6WJRE8ALi5jAqiYKDSGYakTCgtwCBVxlKxYLIZb4NYYuEWKY14wwUCi8N75Pld6'
        b'EViXzgDUzvJSSeQO7CajiQndsQRuZsNBCOaeplCFikqlYZNWU8S4HrTBTfameB4zONmzMqKzcmED+u6YAqjLmZHBLQAN2CUDvAZOLAujwB2eA2yBnSuVTp9M5Ko/RYV8'
        b'8qihuinXHsS6bKxc2J/Y4J7afNRm8V8yP5e711dLivq3dXt/cKJbfLhtX+KJpzY7H4YmfLEClk964sDfmkZ/NOZqTEha3EY31z81i371eF1wU6LjweV220KzFiwPuPa5'
        b'bf1J7q0/rn/0RduzzB2bfvlT6mHa5qS9TYe2yIObv+g5+rvQOf/sctr8ETfzD33XxzhcFWmvjqvMFf4jPXvnrEnK59EB4z+5GvrpT3fN2PZ2/Nk///LTXx2jb0365uq4'
        b'7k9HZZ+L1Ga+79Gwa9wivrvuq8Bjt2J676kkQqKgKAPNCZHRUQy46jiHBjtjZ8AbBPgFWuA6DInC8ZJwWCVpMTyJAWM2lFMBN26FDdGLjAbX/CNlQbSFRgXuyGa0PIfB'
        b'VdVguNqKHLh3DdARI0fQAi4sJUqeRNiB9Txpzow1VVctaGS7MrwEThLf79ig7x14hKhI7EQjzWwdGdwX+ruRZwuP2hBdkP10cMToTH8kOGPUoYyMJpgvuBOuR31nqGN+'
        b'KgfsYhzzg/dGEaTZKi94BhtNm0dQADvAJt47qFpOM0ZaOinYbFB3lcMtTJwHeAU2ktu5aEDfRO/CA/cSF73bkZtLp4ObsJU0ArxdFoNmjRwaRw/az5lPx4GD8IDE8Y02'
        b'YfHmnTnq28zXtVWBy9xzPIdRqTxdEkmN8NB7iDtCe1zGdnveDf1QoM8v7huXerfiwwVPufSIt7C9i0/AEd9W3yZBn3dg22i9t6SJjxUjVmyPXD1Nhg2ewW1VPZ7xvwwQ'
        b'942dcEd4Q/jBkgEuHZFH0Gz5BM2WT3/p6atHZXjGYFMbio4gwLfHKNt0ki2DZMugH/mK+sRRLbyDwj5pXAvvvpfkkatXS/oDv6gev6gOxX2/xC+xDsZv39zmuW3BbXF6'
        b'97AOt/Pep7173OO7x9wZf328uQP8AS41YTqtd483k2WFZnj/FwqSw6PicMhKCzT+SzbITL65C3JlBHY+/uxVXZATh5htgliq02H8G7kg55dgqWA4J8DWvsPgCngv+g5V'
        b'G85KXAFHv4ToMdglON6ELMyYWtDPS01LKernTStIS5XYWLPCUP3NEOyy36Z8QZmqUqG2EPGdDV+tQ4c9tsO6usKOrmx0TkjEx8K+M3Fp5aIbUeH8X3BohW0POqwJ+1Pl'
        b'csSBmqPWDcyOla1eI5s8dM+gQpSMmfjkUqOPx1IrUCcpy3QanQVj2PxQKwP0dnOCyhFTOx8JD7VajUmU0OCK17CC1kuJsKzwwfSLl5Biy6pNz5qTw6SLytSiiqraMryR'
        b'hMQQJUqp0VbPV1jn+PHraoybJph/NGAqp5LSrMGjGCosRDtzMgyCnUaxlJFbcK0wDpOrGcj/MBh+lEcpx0y3qSpUCmLEgShjvkEkRoSqyKcRpjq4ID06OjpYMow4wKDF'
        b'iD1KGe5Nao1KW67RYl/FxpKjRekGsKXZfavlGZ8hPVNbV6UwdAEWyYrkD/yxSESqRlVptQxxQVp6GlaQppXIinNT0gqkIoP0WJT2VpFk2PpWEAMUXNmKGnmUpjYK/ZjV'
        b'j7i2jjHIeUEJS60J5ChVocKGPOYC+QuLw3+M8jqu4ReJ06wRitE1t9XSFtRWydGsaVXyFqFaSSuQTc0ZKmVbt1l5SclbrlWUYPsVpiqw/2x8RTos22/wuNAoKlG/QB2k'
        b'tFRWW4NnihcY8yzVmN6OC8OlIEELG9DgCcLYdStUtdWoquRlw1jdVGmZDc5K5RJFjaHno6Epx6hHcXltjVqJqguXhCpOSVJRLQ9LGFOM+baQxPwzGVJr5y9UlGuY+cC6'
        b'IFqYN3Z0bBzp3KhxyPdgGqRsQAj2e8k+DR6baFK0Wk6FVkXGGhntxJBoeGmcWcSSRYWs9KsW1S9QIoEa2yUtQ2+pqkKDr0zFyMBMZutzi1pdW64kjWCUxetUtWggEyw6'
        b'qlq2sdFAYLq99co0zXLRIhmSysvq6qqU5QSPjbdFyHgyt7OyPnamMXNGGTsporfj9V0kRkeJVIRXeZE4r7hAghsDr/YicUqabJhxGPH/sfcecFUd6cP/LfRLld6LtEtH'
        b'QFBQpJdLryKCdERAhCs2YkelWEBBQURAVJoIiFIUAWeSWKKRy1VBNxqzSTTVqJiYmBjfmTkXvBjNbn67n/29//e/7gYOc86ZM/WZ9jzfR8hwbDb7j6z2P1FudZsS9W94'
        b's/4zpfl/sCWgS53K5MIzSWTRny06aUm1BVaSWSVZreZLiy1Mo1arWXedV1PasPYzYRvZCMCbAMloxd8OT2VOrnxhFWjlrskVQjBWw/3kteVo2dADu9dEviY3RgRH5BOH'
        b'W6fA6VjWKibcNX0Hgdo/QKusTfkB6DGdEHAOlgocTmKHphECDBkn28/SLMrXwj/yT7YNCNixw0sBrXTqwE6SfaMCzI8SqHbCelFpumsQ6MiPxnMw2IJpMm/7mKWZLex+'
        b'x9deux0ONZ3C0rHFaHNtlGAnPDib2o84Cso3ClRNDZUs6K6gDrbmr8V39qN7WziE12npH4x3JKhoRNGKcJuUkTpokXq9D7AAboaH0I0jM8A2cDQC1KeEgmL3DeAg2ALa'
        b'0P8axQ3Q1fbMNaAMHHdPigcl7nkZoaHL4vOMFoPqzKXyNLh7nhY4xIEHKTXe7aAD7GXBnhXSDBojHa0fB+jWaFndkB+F73aCcpXJpIEzcOcfkgeL1UHxAlCeBLZNS9c2'
        b'eARW4GusE5sgB3fooYYSqqAGekAlqYdQ1Eg2C7RyYR/skkSfLXLJT0S33HJACSdANkkA/WFHCTCdK/LzI2DZChk5uDdCUPZCezd4ywZXkMAT7hTNEmwGzRLkO7KwSAW2'
        b'q8Ga/PnoKyw5z3fBU2FrAeEG4tciptUpWqDvkPEBp7PyvXAbPkcz5Ai7n94FToSQduMLBzXhTg4Ow+1pnyjXH5TMQC28BO4LA6WghA6HclFE++ApwodE9Vfn8oeofCd3'
        b'AQ6jsi0OwEl9HSXYxgIVSkbwuDJoAsdUlJk0UB2oAI7BQdCWj5dn721cSzI4HX3K4GbDBliBDdxcUPVsgYWobIluMtibRIM7wqTDQJciSVTBHLhJyM9wgB/b39Lqbe5Y'
        b'J5Mkg7OuBtpf9xpUYrX5M0A5KIO78iPxosR1xiQjLtT3L8UNS7jTe6QYLcxfCQzAGgZ12lwH2/OoLTi8/WYOG+Gete5EKy4fb5rYJuVhD8NT7oXXWU85GAbt5mxGUERG'
        b'9aoLTO5NtIZs6v9+V8RHQdBG/nRtes3Rr2tG90vJi5fdv7pL9/4l8QhflR0RrXqWkdsOMYtKzXM93/PcsHdX7A6Rc3sWjz66+vHHd879IrtR3m3g8vpHx0WK029tKWKV'
        b'ryq84XMqSj0owuXUDbUPKi4NiLgdbr/MdVhbpLG+IuHR9wskv4qUm7iwosTRSvrRK9dvzzYa2x2+xLgodmYG905K1Z19nMKkAwrfFC0Ry6d3qaUZ/lpXdd8qpHL0WkHx'
        b'5/KN2TcLt3iZS1uGfJJ+64SjHPe0VO3NmyccnebdviguFhTe+J1kR1P9V8pKL93jnQoenGnuvvuL2aHdvc3i7i+/qFvXXq8zsiKPdegcI/7Tb8/qr7SuUlbNr9nmYv1N'
        b'61oj1fYw5UqLH9Q+2LPpecRvL7fHrPNcaX8l/YjYicErJZJ2nN13jHw04padT+vN+eZHz5tH4h8Gyy1PkLypkqRhd+8juskNy9qHIfzNck94OpWNYdFnd91ir+5d8Tzy'
        b'28rWjB6DueHJzxamfSAmN6PAf6lr18OHMx4q3/v97I5e8SXnVDomxOSqa+dm2ueuGT6Ua56uG7+6bOz89hjZ1ct5tMEe7Xu7TkZs/8SzRWz50/U3r0tpg8XOtw13bWWE'
        b'O3IzjQNejB+wfeBSf+WhdeJQ1Xc9FWwVspUXlQSLhNBceBcPnAPHs+A2eJboXc92W0K2CDMzptm0xi0guKigSLB/UgvcIsgNtMVQlrDHwX4/1FmQ2K2ZxipjryJOKrOd'
        b'TaaUz6NyKKerbXAz2TuUVgQtAneu8Ax3Jjj82p+rpSbZrgsGezIIxAy2aAhzzDR0yMYoPABaYaPQ/iM8C2snbU9hmRaJw3MjPCRQNIe7F0/tjJ4BR0muDReBrkk9dtiK'
        b'UleI9diPw20k+aAQbPYyR/3WT0kdnBChiWUxDEDpLKJ6DQa0jafgb2xYYQ07vahN0xMeOGOT/kMF+52gp8BzljLZ8gTlarDlbTueeLsTjYrFSGA2pVHlux1WyRKo1G5F'
        b'Ya4U6FGkfMN2wQEMnbIALSIoA2hwtaCDs6pgK9kwDUmCm19vmIIjoHfS7Swaoc9PKsb3ieONZ3vYLth7tnENJMlcD7fDo5wAP1D8hmkyk2YD+tCToMeaFkySEQOPpJLG'
        b'g0aiYDT5kPVkRobMA1tcSCkuBhWexK9sDCydNDnWBbsonfd6nwhQah1oqarKRp+fx9BbCarYqv8b2rI4qZNzynfjOQzesrX2NgCUDpNyG7HGEjv9NG42vqFqe1t7Zr13'
        b's2dHYEsgZih533/79qyeYZN0g/SYni1Pz5YAnvQcymTG9U2FvF2Wyd43NB0ztOcZ2o8ZOvEMnfq0+YY+I/L644rqB1zLXZsdRmZ5jJh58hQ97xuYlHPGlQ3qU0aVzZo3'
        b'DCuNWnvdNzAu5zwWoxnadgbxZrqXcTA4yLramq9hPqrh2ynWK9clN+zAs/EtE3+sN+kvs2v1JxqGj2l049l4p5jVz3rCpBt7EueaXsS5phedgubMKZ9TLzaqaHxb00Cw'
        b'X+xGtondyTaxO/0zzZkC55aNLtUS94V02F+/EUXeiCZvRNPvq+qg+wKW1CQdS/g9VR3Be17kPW/ynjcdg3qcDzpTCCq+TuiIWujk5nfkiMW8EcP5PMX5KNFqWgfWl68f'
        b'UbXpjB4WuShzQWbUIfC+nmWn0qieQ5/h2FzO6FwOLySWIJIi+QZRI1pR2K0peqdZlKdq2Wk+rDTmFsZzCxudFUY+JkBrfaaq01DQuf6S7Khj1LhQWgL4OoEjaoHjWjMx'
        b'7wfTmU5JCzLgTjLgQTLgQb+vpVcXUB0wpmUzqmXTGdG7uGvxmIP3qIP3W59+LIWL37nceUyRzVNkNxvdULQZ1zUu972vq1/m+4WyxoimZfNKnrLncPSltJGouJElyeNe'
        b'ISNhi0YWp0ww6Spp9DIGKg1d4zJGBQsX1FRUI2bONxRdbuubotbr1+LXpzJq4Xpb16DenqpFvq5NmXuFL6EuYQ+uzdI8RftxUzvsBdVoXFDiATyUGkPzMs+KwPuq6mWS'
        b'Qtv6M96J8Xm9gZwXx/yTbf13d2s8ev2RvvPXenQ13vvHLHqy959jQaeHEdROGP0p+flXTgDwCvWYmAPtDMuNNv0IQGxy7boU/agUI8qMlBqyeJFEES1NbEqtUfTfqdb4'
        b'IuEPS+qw1OUpqXncf7S3TTbSBIt3vHWTyNVbGBjwD1boOrQ3V+jsoPwFeCw7KQH3c15rw4e+yV8vjcaz4KGUNzAZ8BBol1HWTSc+JEQcwfZp8910WDY14YW9EWTOPGMZ'
        b'3Kmw/vWkGU20d8PDhPkskwK78Y2VVrDE2moVWqI1oQt/bIdmGC/qKGNKInBEi/0DaJawB38ExaFDA2VahgTeDM+DU5FTygdY8wAtMdpMQ0AP2WYoWMGcwWTgqwTpK7Ys'
        b'isoNti5bRLwuoOqBh2nwtAIYioBVxFIS5ftIHDFRtaaBs3LWoBs0UhP/QWcPUOTFksxjordasI5CKdxHxdeaA0+as80wqHItHWzShZvBHlhIlBvSQTncC4pyOHjaFCRK'
        b'E1NhSMNjoJparu/zlA8nThtEMMeeBvaAPhsSpSOssJkkpsMTNCXQD09wwR5iZzrPOHXSmpRe4O4KjkgTBjg8iNK6X9g4lQ7PgSH9MHiEZCDJY52QXSv2o35qnmISsYa1'
        b'pS/HKhZojUyjo6mLmQhaL5LpzllYKf7aQhWtJmGNK5oDNRCAuYazVjjYBSsi0VSvEsPYJYLpWbANns6F3aTwneJ3Oy1kImFik7C8JiuB2vhZFmxgEUDH508JSY+U5ajA'
        b'GZJ+KtJ0PTqSHMtgYgwVyFWTmW9AR5UUkmAxb2E2FfhNmEoQh7EQ7xst9nPcQHkyMQS96/4IoQfnwSFMoa9eT9nhVszmTO5AwAG6Jhiw9lKl7lTB/eHoVq4MmjYr0eF5'
        b'Gec4bfI1u1RxxhCT0qmIlhfF/tRIIzlED5qqAtjj6eouMCsGPZagbtIImO7Dsg6Up3RgWhhoMdyN3hGnMY3pxnDPPHgKHGPTyVtRoC7bHJRzg/BCgcGi682ZSRHrN4M6'
        b'2Iy9BsgxcHyw3dfJ34q0AXBu0XxWgRdqizTUPEC1tAZ5YxmaXw4piMBuadgjjlrOPnRX2Ysyvd6cAQ9g+lgoTQacDo02ohDvh2DvBpapmTnsCkAV6JTpz1gE9qK2i1PN'
        b'0l4PzibCbmt/2IvuioKtdLjfIzjj63tVDK4nktEDOb+fj/k1UytSaXD1T+e7a9Z/cb7L+I5xT8mWpTUqCqyeCM+lDVtMvct2ei43/PvxD5vtTEUrfW8U7S8pqtc70rZF'
        b'SUG53MBM6kjR/U8Nft6a/uhj9O+XR3P5t76ztuM++mVw4u7FTwo+/q7/t7WJxe3F7S27lV70Lq+TfFS4IuX6uqjlgWxOZ92V3JrkH0MO+26+Uths33VK/0rel8ezrvuF'
        b'X2UseLhuqXva0RXtJY9nBenYZUlYcyy97rl/JdbQvbL9q59TH3lcndN0/8uM0z61Sc1nF1xPLmxe4flV+MrUX+dy+rw8ri+rTz+mc4cd4NPvv/yyecf33NLWC6Ep2qJz'
        b'/76uqPGjbyp7j+8u1i74Wv7u3062f3htacffH9y9Yhd59qO6aumZd5bNdXu/NXZFm0bsio+WiZl9ymzvHl7WNkc+fHvV+YGbbJ87D9c6X7vK6B1d13l0xXeB/Y+WmOvv'
        b'OPFzdvJoujPtSGTG0acKgaGvNDe9ktgVdMPVR+GlMvu9T87mBi6/on1b5eCP3vc0PNszngXqLcvOD32e62b3ibSP6GfftP0Ku1rEk/lqI/Mt0lQLQi4OiDZbtW4trrxh'
        b'4L9s8960YL8flg3vFhuf055i2zIj3f5j3Z0TiXcfQi237LFv1XqPfWV5v/ji9ykeu/9G7/5q944ayc8/pQ9k5VfE3qz95MHODz5XfLVzwEJsdKXWUrNWxU/8k/NUi7iO'
        b'vV4PtPUffTb7pc61b2znSj772W5NxMGfg/QHf9pwbdXBXqP03EK7e9/sublC+blsaO6SJOVN2yIC3o9YGfND8NUXtJTaLK+xC2FJs202rs9/EeiSonVsR9/3VWuyU24v'
        b'Uvjo1qhIbfDMo18mPvpyt/THH35766eI/Tb3fE0uLZsbNX4gdZN1q099/rZYmTu6X86GQfaND9OVZ7nOLjz26daLDbdMNt28flslfyC/aO2MVt9x1/Qr1cu74kcHJ47k'
        b'bnfsa1/v33FnbfvTr99fRwv3vJB77afvKhNia4yM9/R+7vD56fE58ktE+xMeHrirvXXN4a1zd9Q2r73t6nbifmFtQ7rrjsui16PzuYpz6Ycdn59Mlptf4DB2/JBd7zPH'
        b'u2Mv73zQ3tadNtB9MfrGyeQO8Yxr62Q6+m+t+Kpk/ZbFvV/fkq5+yBp5MeP0cnpm3PmsW8FV0XoPIpfLzKq6Nby8YMGLe86XnNfwP930G03hYz9j8Omz9IgfNCO533u0'
        b'L6l5ejXumpW1a/rAOo/CfJ2lcgYfb7HIc+Seuyf9yw+Pi/Wrv1RI/mnjlw4/PryvlTJf7kT+jyq9rb2KBVsmvtnXf8/vg9UDl34R/8ml5Ils73aL/B+tcmTSf543LG4X'
        b'eRV6d5289zD+q0N6otnt95nNtNorvE8+XfPIKFp+zvMHgQ/j183uPDlfZOC4rTdvewRT7H2jaKbYYMXNBXkqi2XUHrPbNn9hkdFKZ35rFMW8/HAPuvndowimLv29kmXD'
        b'9fPcHB7rmr9KXt7IOxt5/UFTSNzT5/IrmJF1bqJ37/7EbaYdiqsS/85Sldbj9uTejSeDm54MFt7qqP+x5mhJbWbVWbHfZm/I/uLbVR5tv6ms+V70x7+tXsDZ+ouDx73S'
        b'4SH153KDfio3n3ucLxi7cr/76KGNv9adGO/q3ZOyLTbKddOgUtFLk+H4CFeuearl0IrMHxekfLjxy/aInJ0Xh4I0hz57ID54+eDgJypJ8UNuL189VLWMmBN+98bTlxsf'
        b'Zs999ZL3asjjhz2qxxJdpX7vokln5P/844Fu671j18VjfnI/eCX6IVD88MorueWNpmmvXPvbX2kfi119rNj+C5lr7396dM3vGvMvBsl93THm13tj445P9r5gfSV7sulr'
        b'6b0vtNaZ5UUv+kU1oCSIZ3aEnfUMH1SsUIDbWWZoGkaY1fmWsMOJ0vDSBd0isEMR9pPtleVwE+wSMuQ3wphsxipwKIjshfjAk4tf70D4gNrJDQg23ER2DuhrRDlwF2dK'
        b'o0vOhsnWSVeDlcSK3RFWgl1/3Epph4WeWJGQsLUTwGmH6Zsp64S2U9AovBVWUHp0RaAREwAo9rallW8ALAT9aAqkEiAiA6vnk/SIwn5/W3BsGuPeEhyAR8iGCig1AZu4'
        b'wgabMnCI6QPOLID7QPcz7Dk2Qdmea4W+b5kXxJZk++ejz3cTrT1YzKTZwzax8PUoMjyaOZvBHrjbijO5bya2hGEGWsOIQl7iangOloMGToCZGI0RR3d8z4kkL8kaHgZn'
        b'YBmqFWs0Mcbp28MwyoBbiRKgmh48LYTwHgClmOFtqUe2kqxBVQYLFlliRD2HSRNHHy+EpxnBoCiU5C3bNHLqNuxGw6sMKGLAs+AcHHAB58hmkYQMyo3Axcpsuj48gCq7'
        b'35tSvDuNSuAQFYGlH/56z3IpRnQKKhU8rYbNYCs4yDXzg7tXECzEniDYwRGnyYNO5kr0Zi3ll6AJ1U+lHzjFIfQ3XBvnGUyHRLJdiPflzsNuDjwVzAItpmI0SdibCfcz'
        b'wDEv2EKesEBT4G1c7DFAEtWPKE0KzcGr4W4GLLVFHyBNYAhl5xhOpSQbdpJykAEDTHyEpIjdNVFZ2Yke2/QabkFngBKU752oxeImbQ52meEqNbdiS5magRb9KBHaDDUm'
        b'3MQEJ0kujJzgThaq1h42LEUFkQ06ZRmxcbBpcr/tNBjkgq4lQXRqqtQMWxeTxg6KA31htx/2KkBihyVaYKsoTUGFCaotYAP1TLcLLOYEWYBi6ynXOZpw2xywRQQc1zSi'
        b'4Bw9YIs618oPdEijZ2g0WTFmDtzmGgz3U2SIU4thGcvfMiAXtPuihspl02nqoBVWR4j4BKN+R9YBrfaxXG94iI3TOEhDk/0zoEjgAgKeW8aZdNkkivpjBZPp6IK+OUha'
        b'UT7ohN1CAH5C30f9rC0Hb2VSm6qtsvAs18+MjeaQoIIOj2xEffysLPXhuplLYHcwXuyJ0ugsGlo7FTpQ7iBOg4qgaR4x9JkMeHJtDokTdsfZT7H5deig1gocYcNaag91'
        b'MzgRPB3MLwn3MJVhjQ25nxaEpsimqCRyA1CSpOBB7ASJgRrKKQ4V9yE4YIWzFGhJp0kGStkyQNVCUE3uJXrBXpYV2wxVGUqwhIZ5BiPDEBUiqYcT4lHmqIqs/CivQXJg'
        b'F1M7KUkSUs0ENq8BbXAn6EDfzg3Cs9kmOqyzFSE3I+UVXCJZbNRRunHEorCKjqqgx5KijlTNWDi152tBD0wEZ9ks8poskoplqAfgXDJhMT0b9iKZty+evGbns55DHTiJ'
        b'0Vj+Jqj0mmJmkhJQlganuAFseIo4mkAdRxqWhzNQXLvtqB3tM6iz7MBVlheAAU8y1kwUcYkESv0AiVpvBhiA3aA0LQA3mD4aOAn2zyW75A6z9dHyJw9r2zLAIN0+UNMn'
        b'mmpI1fCksRCYhg77YQeoQV285Zng5HjvcvWk12sQVC8V1JtHQfGiN44ysjZmwaNwG+Wh4ijoW0sl1ppOk1pQoMtAcup0NhktVEEhKiHsLoPqw4TXdC4jAPsIK2ZCJOjh'
        b'aSIqQkCTKhfuZkuBkxZIVCJxfwo9pB4G2uVFzGClK9UoBzRh20IXFIXgvmgUHZasA2ephnNcG56Be7GxwaSPGLAXFJNEOoC+NbBkJT6pXAW7UT0q0OPxypySs2CHiA+s'
        b'wDfFaHRwmAb3hMASwRdBJehASyBYbIr6DzxM14Zl4PCcdSRWFTS6HUGpNvVfbcagicuA3WAfY06+CwXqPAgqo7COQTDeUikmzUeOwTQyTkF39lJtshPWwc3CXrlEFJhy'
        b'sSmU4NhZYM0lgxqSvwLpqQaOolGgTcTWQpuqm4PKqGJL1KiBgKzRalCrhmWobkga2sA50CAQn6TEpFARnbZCbcMEtpKhb0OGOqzagIdpdJcRRbdckEyGkCgVcJiLalwS'
        b'Fq9Gv2AX6qFD6BFF7EmyLhsJX1x0GqvhJoGrLx06E00fGmEjKKe6Ta2Mp7EBOWwQHDXEwQHKKUapNGhn5ctIohLVp3MWusGjFoJX5ETg+Tgu3IlPvpToM2E/aCVjzZy5'
        b'sIXKhl8uuSsDW5h24JwRbEBihyjdD+mAk8I+0DzmERdoqEEUk/MVP9glSnyfWMOSQAu2XyBW6o+xFrjlcXIRA0cMYRmpdQvTxDePV8DxeTZg6zNbIvBnwHriVGeaEzI2'
        b'aJrubYQWCU9KWIOKOJI+EVASwCIPWuaizmIczaApoG4KGoPBHgp/tEME1qDPvpa5suFMNDT2B4KtHtRIudcIbkJNQtDTvOAAPMQArR7gDClW32B5fBOL+f10WzPUGE96'
        b'kY6xBGwCR6n3iDhxYEbRJGMDKHuAOkNwAPtKAV0oujf8pVC+UsB5C5KDwAKFyQyguMKCcAZ6mKj7V6EcEO7sQCasEnLghsRSs5AHN9Ry6ymJcR4UgqMsMloiyUaXBeXo'
        b'wTJXQZP2hJtYsGRy4iQB+q1ojFBUND1UL6/SASfQGOCPFWtO01FfOgkOR82hmvsh0WScTyn/QNxYQLUMikAJFDJhETiiS9kctIIaWMtCg1QhG01yNGhwWxw4TM02izNs'
        b'uUGwyxrNM5BIhy2gSIQmv4wJsObCHmos7RN1ht0WVlZYFlTT54MKcCQf7CTFL4+eK/SSZ+HOwGDTdVDb3Uydm5aDbWwuGgpgseTrfKmBztWwTGSuH3W8CVu9N4LBEJYl'
        b'yZmYDkNxVjI1GKBh9hjxAxtkaYYneoXgCDzDAPtT4Q6SJj0wmMO1NoOdvqjqxZPtwADD1xQOkYbMwH4aD8Fa2G0ZRO3hrKejTlqvRbr4WpSUfmHvN7AU7Jv0fgOHQCcl'
        b'ArvBYSQKrPzz2UgWoNGKYS/JABVS6lTyWgqcBDNuPzlTLONkYD8TNqrPkZWlCrw20/S1CQgzkC6xxptlRQ65ObBwlYkmxyoQCeu1dBdYOIe8QQdnwaAErKdMQ7BZCNyF'
        b'BnEC/IOnN7wGlXnB84RVlgxPsdX/d9E/OHFv0c0T9mojlkd2+depv+X8g7pFDjLzWNRBZpAtTU2zyr5i7ScaxiMm/nwNzogSB9OwNKs1x9SteerWIzZufHX3MrFxFY0D'
        b'meWZYyoWPBWL5ki+il0Zc1xNq45VzRpTs+KpWY1Yu/LVFpSJjqtpjqr51Ys0sRpYY3r2PD37zki+njMKG/YalsT3deoNm8wbzEfULNFf1InbqKp/c+qolV+fyJiTH8/J'
        b'b4TtXyZyX1evTPq2rnH9qpqN6EJJr16pSbdBl69kW0b/TFHltoZmlWcdp5ojMEVJ5mvN6rTlaTnwNWaXeYzrzSz3u6+hWWdWbTaupj6mZsZTM+OrWUwwGZoqZR6PxWj6'
        b'hvVuDWJlfvd1DCZooQwFzTLv8ZnsJpcGl8b5ZQHj6HMBPCWbsoBPZqIUYI8ljRv4M2cL3xnXNh7TtuRpWzYndixtWYo+UydVLVU/u8m5wZmvZo3/lqiWqFeukcOXqKTq'
        b'PZv8G/xHDed0zh419OyL5qt5jWvpVomPqrnXuzX5Nfg1p3Qu5lm58Q3dBeGegvC0zvd4Vh58Q8/76tqj6gvqo+o10C/s8mQBz3rBBE1WXWM48eKyC8vG9Q2roke1XSgb'
        b'nM40HtvlKY2hrTOsj5nW43qGTZINks1RPD27Ub35fWKjer7DxqhMPOg6qEh0DEa1neojmmIaYjqNeUZO5M2+xKGl/UvH9fSbRBpEhG6OGnn0RY0aBQ6v4usFoShcdR7L'
        b'oxjqYqpjmo152jajWsGdib2ZXZno04YXDIdXQQv+7GBUL1U+o1pLmkXGTJ14pk7osi90aFH/okv06yKXRS5FjAXG8QLj+L7x/HlLJjRlfegaj3Vo6hp1MtUy9auObOxU'
        b'fkqjm3Dok+mJwp6Rxozm8Yzm9S3jG/nx9fyfMhkmnvT7ukbYHc6YriNP17FPiq/rMSHKVNd4LIEjE6sWG9fSrvOs9kRtSqtBa0x/Fk9/Fl/LbnzqbJanZTNBE9fW6Qzt'
        b'jemKGdczHtVLbbbvcGlxGTOfzzOfj/4ctr3odMHpkuf1gMsBYwFLeAFLRhKSRxKTRwJS+B6p9/ErSydfWcAzX4D+HA69GH0h+lLE9cWXF48FJvECk0aS00ZS0kYC0/le'
        b'S8lX/JttOxxbHDvte126XMbsPHl2nsPhw0kjdn58c3+cbbEGsfqVuEGOmTjzTJz5ei7jhmb1UqN6aSOhkWOhcbzQuLHQVF5o6i3rtEtKnfReyS7JPsM+7jCjj33TxnPU'
        b'Om1CRny2zoSoNCoODVwcqNUKiuON+J14Jk58vTmodrV1SJfBdefSTO8QbRFtTunIbsnmm7pMSIqiiKRxRJLVkjgiVIKonkf1otGTMi0yqBmkd6X3pQxl9WeNzQ/mzQ8e'
        b'CQkdCYsYmR/Jnx3FN41G7Uw/nn7f3JoqK+dRc+fHTJqZzSg7sNOt16fLp89zKKA/YMwlgOcSwLcPHGUvHQkNGwuN4oVGjUTHUm6MxqLTedHpN0KXjru5X1S5oCJoUKgp'
        b'xfLdFk+Ii2jrTDDFUErlaRo6BzXrFZ/SUHto1u8wbTEd19Z/3W61vTvTTuUMi45qhV3yRq1N2xO1NsMjcs0qo3runbN7XbtcUVMy15jIpM+xVpmgzdFRLfN+vIpO0zVC'
        b'goSurFnFwG6J8ggm3rU5cVTTeny2U++yrmU8LbuqoBaf+5a2VUHjxqZNyxqWdSo0ZFf5YK9MuIEnNmU3ZOMS9Kn2wVWB+6pBh3GLMV/PFv8t3SDdHNYR3RI9aunVJ8PX'
        b'8yYtxrd5VodTixO66KMPifWL9eUNrelfw3fyJZlGNaNjOKrt3+zZLIF+9SmNzfHnzfEfcfB/SpPQ1kFVMRayiBeyaFzfqEm9Qb05jadvjyvEoE9/yLzfHLsqQxKoU4Vn'
        b'6Dhq6N7nPWoYMJyGWoSzAW4RBk0SDRLjhkZNng2elMwZme09wvYeZUdcsr8+5/KcUXb8yMJ4vuES9Io+ecVoTM+Gp2eDmgfqW4u6Fg3TL4pcEBmOGPOK5HlF8hdE8R2i'
        b'J+QkQpFImkHT1iNCqN6TUoyhJJLCkEa/Bi4PqQYp1FvsW+w7RcZsFvBsFvDN3fh67uhTc3F71dap86r2mnxwVsecljlj5l48c69Ls3DSxjhxPE5cvRRfL36CKYVKSoNm'
        b'YHxEs1lxRMtyVMunU7/XtMu0b9aQc78zf5bPuJbOmJYdqsJRrSRUzqx+1rDbRc8LnpdmjPkl8PwS+J6JfKck9BQek+qCq4Of0lDpU91PUHfjRuZHljTnjxqGobI16TcZ'
        b'NsBC+aL1BWv+3LBRw6yRqOixqFheVOzI4vixxem8xeljizN5izP5UVmk9CaYIrY6j6VwvryrvSdFYFhTbEPsmJEDz8iBrzd7XM+AGnrtkIxHEgzVI31Isl8SyYhRw/Tm'
        b'vI6CloIxazeetRv6E40ZSy8svZSHXdSNBSfyghNHklJHklNHgtP43un38SvLJl/x4Fl7oD9RtxK/LD4SEjYWEssLiR0LSeGFpIykLh1JWzoSksH3XUY+FNic27G6ZXVn'
        b'Xm9BV8GYow/P0ecS89KMEccAvnUgbi7eDd6oQpxbnClpyjd0HTe1qkdjY8ZIZPRYZAIvMmEscikvcuktu4xLEUgK+HX59aUM2w2792XctPcdtctAQmyOARJipN5QifhX'
        b'+wtK5I34nXnmznxDl8kS1CYlqEvNHBzQfGFUK41q6qg0Ui6koLbhfNl5jJPC46TwvVP5c9NwnaL6HNUKRLUp1iXWmdu7smtln/tQcH8wH+XIJhB3Wd9q33E9q6c0lr5B'
        b'p23v7K7ZOBkBDQHjpuwOkRaRcQvLDk4LZ9zGtlekS6QzqlsaJcjSCrVSS+cxCy+ehddwCt+CM2oRR3pkFC8EibbF/JA4JF7ZZqgTs82I1F3ON52HeoeRMeocRhajht4o'
        b'TTJdMn3pfBvvCWWWvQFOwezHKjRjk6bohujmaL6Rw4S6DBJ+q+l+dBONn2h+dHXNpwpYUD12Y+CJz+M0EZqCxpi8Hk9er14BzTh8G3zHlZQP+JT7oBkWyjlfyQL/7Vfu'
        b'V51dk8NXshL8VZVSv5inY8tXmjUZkFb/Hk/Hjq9kjwP8y/3xxEekWqQqom5x9eIxbSuethWZGWnVSVdLj6mxeWrsZoNmWzQX7FTqVe9SH1Gb+5Qmpa4z7NC3llwIxqXb'
        b'evpo1shuYDd7dgS0BIxZzONZzOtL6ssdsXDjGbgPJ/MM/EYNoi4tHTVIHFmUiErVyBi3AUHhN4cjgTmpauXFc/AatYy5pHRd67LWmF8Mzy+Gb7po3NR81DSsUwQ71aNk'
        b'CfoTDddRF6IuecE4JPGNjCfExXETkkSFKS6jrDLBUjSa8YymqKD4xJSmoF0VfkNef1xV48C68nX73huRn/nLUw8Rmk06/ZenCQya/TI6MRsfNdRcI2H1jbnmGhkbSlFK'
        b'8m0sr3evArCuUcK0WX/eQ0z6eveU30gMvTaHRjhfz31s6fQZT2h/EfaF9R/ZYoRQ97UsiikiKCiILYJ+5C3CJD3pNyitec9phHMW7uHrFegVTrishEdGYVorptiqOOV5'
        b'W3EpKOcV/qfWUXgXaMG76alYy3PdW1CQklhhbCMdFWMh7YkIQ0YedUqDMPq4tsO4PppBmD+RFDXEDv9I2Lxx/ZlvhnmRMN2psDQUZjmub0k9Zzb13Jth/ijMmHxjLgqz'
        b'ngpzeCMslnoXhVmhsAV0HKhlOa4ya1zF8kkG3UFNtsj38XI6TVZlgkGX0cYAU5XH+OqpDkabRo+YB/MWxt7W1G0J71e8wH3GpMsG0O97+4+7ef3EdJbxpU+I4pDHIvj6'
        b'yTo6TUnrtrzJuJLnM1GGkje9yPOpBImnJbXLuzn+QvJlB15oBC8yhrcobsQ/fsRryW0N7Ra7/pn9yRcML6wZmRMyrm2HXpV1QN3Vm45y5Bf8nOnDkNGYoJGf4uQWvnwe'
        b'JuLOlDH8kYZ/UrRVvK+UCdphNeGtUrgRyUmDCgbNZZEY7FgPSwLA0DRNNZbg90QKxq4q/gPsKjNFQnAtKXQtha5ZKdLkWgZdywrC5YSuBQjWQ5JTeFWld+BVmW/FqypP'
        b'Q5tqT+FVVf6AV1UtpKWonVD/d+NVT2i0iQmlQGcKriqTJpqi+SdYVa03sKq6d+QIiTgjLzV5pWdqUsbKF9Z/YKoK3f0XgKpOFEdvFptxR8QjOMzrDtN9lnueIZYxxviH'
        b'KfOfJ5s6USCoWX8Jhyp4yemvI08nP0e4U7YYeZpni0mgTAInzZuFCaVSYV6BwRFeBHVq+AZmNNzTMyw1dzrtzibPHmf4n3nUdooHOpmQF2rvinUKEjo9zWzJaXHgesh7'
        b'LkwanSycvF9wjn7Gt971Ddu8BfiZ/20+aPqbfFAG7U09V1EKTgUr4QFv7AdkBtxEuQKhm+GzNqIwlznLn0Uo/+SUvAgrtxaBzoyGAjqTa4Lu68DRmrMMjA/dp19KVzxq'
        b'k5ZpY6NkGzUr8YBc2v0AcdoNf9Hzlgw2ndqgP7kA9uKTbLgLFAtOs+FWUAab/4gapRigam/0sOmIUXwMhBGjq5yE9fzHNfUmgfryev8T8Og7P6opLkQd5Tr9D6ijeZ7M'
        b'/2upomlsxmf6Yv8sVTSFlA/GJmIj+X8nUnSyC/4DpOhkF/6HTzj900jR6VLhXUjRdwmXP2F8vlVQvP35v4D0fBOHQlnuJy7HRveYavIORsfUa2/z1fQHDOi0ehagP/EA'
        b'ReE80SBl9m6cxj9ibk6m5K9QNzPS/gvc/H8HuDnZ497Cm8T//hns5fRO+09iL9/agf8Lvfy3QC9FgyKIAQ3YgUb206/hisJoRbgX7gqgTMsF9ufH4GZyqA+G4A4WPJYN'
        b'mzIKf90vwg1CMf34RX7NFYfahkK62Fz1uXPW3d5sH26SbhJrwjXhmBSYfLtsVZHFzCXHPaSSTXxcFBc7hKtoMsVMH1h9VtgVXhVl574wcGel9CF12uoEmXNfdrFFyTGq'
        b'PdyJdalqhDCHNstMKL28Q6ACbhZCHE7yDRPBPqatWDalj9BjCfvfVAbNi2V6gnrQQb6gCfaa4UNaWAcPUAe1KJ4K6iy9Dg6aElNh2Cw/3UttAdzFlvofbA3gicRbsX5/'
        b'nM4IM/28qTnUM/e5NAWVspz6lTx5h870vpXDUZcix2e7Dc++5ISJfpF0sv9dJlIhM66qc6Bgb8EbbDy1mf85Lt47c6QvLgzF2+j0P4Li5UUy35i2/xUYXl405QXhrSC8'
        b'PyR8koLHQQkXouAZvGPk/QP5TuzPjRSTxYUSyJo20xSdPtNE80xJwUyTIcDayWCsXRqLzDTFp800JchMU1xopikhNKcU3yAhmGm+ETrNIe76t800/xxpJ7zS/n+CZzed'
        b'yS6Yvgkgb9lowMO0rf8i7v6LuNP7L+Luv4i7f4y4s3jnJC8LjRvUymuyIv4C8e5PRMZ/knj3H+a0zaA4bdGwEhQK0dnF1WVt4CkKzo7J6RbYzSZRGw/3hcXBllEC8BUm'
        b'VBfDPZxozC+XIMbDYC8olQwEx8HZgATCQoL7Qq1Yq9Lz34ZeS1xGPu8MdsPzU8g3uAtsg+1m4vl2eArZmOQ5pc/7Lnw6gwb2wTrJ2HVwQBQO5Vvh9wqTMdhrEvoEi3wt'
        b'KGt2WBSINS/BOWJJscREwg006eRboFdmw264jSM0eU8Qx9N3zMeygLsDKeOYMBYKjFmS74onbpagHZbi6FBckSHRllHRGPDlHxgAWiJ8QbtvoJWlXyCKwJoBTrFmgdKw'
        b'cJoOOCQLN8/MygCHiRHxArA7btIBcTDcDnp1QS/JOCxeAHe8ETtGVq2ANatm5WFUFUHHidASQKk4qIR7wK58a/xeLTg5K3zyaUE9RayYlcdeHkblnWQ8Nk0cHJsH+0j5'
        b'm6IpfgMrT1YGK7TuyVagzwM74HZi/asJ6qRRufSu5jJpDLMwOEQ3B/1gH7GLrnYVoVUZoKcWJGTVK0rQMnSXqDK5r9Ad15dbavdeLwE28h+mh33/yuxIUdHzH7+4+fn8'
        b'9wfdFx69F6ZQ/lN9r4JLiRzvwCehf1u0+lRn1UeF1p/mDPpdMjq7hVFyaWZTxIolt8uUd1QaivYvG/t6lVr1yS/W3qk86N2+7CQtL/z6aG9rzGlJjY/ZT7qcjzz6olPU'
        b'zuj67MpHJw/Qjl87G7xf0eOyUtXnnIPPDfMCkv2qtsU9PPCV380HJ45r2Vf/znkQMuPauYBFEcP3yp89ivup99ddxx4+zh67Jv5pkkG+9r305U0+PzSlb2y6uvHY+68C'
        b'qv2vy+5yH7ks2x37vXLJb8s+df2lJub7Rlmjh8EnrV79VMWQunw9Mublx9YSUa6hn/tsf1DFlicbwctgowcxmQCdrkJWE7A9nayOEvFe8zRAfCQ8RvBP8BRsJLqxqins'
        b'Sf4TOBbsFgT3U9rRXbDYhTCaqCXZbNhPMZoMg6lFW69WwB8I8SIpsEwC7AggCrsxsBzUTLUuURo8vp61nAFrQC3soCxBGsEBpSnd27XwtC0skyIf54JjsUImQbAyk7Cn'
        b'0FryCNH/tgVD2sI2jK8NGEHvDNiBVpuDJJ6oeRupLHASYSO2jUCfkoXnmAHyVhRlqR60g62wlLIr8IFn5tNBG2gGm4imdLaTImeWPxYYHTQz2A973cBpogg9D4mCo5N2'
        b'ZAZgD9l8X5FFGQfVhkWY+8OzhoGUHEHJVzRhwhoRbUqv++i6RULrZNgG99uAlmyiIZ/uYUtRmUAb3PI2MpM1OAPa2LL/phNwfISvN42IJMRO0X1zffU2FFIeRbF/EuX8'
        b'V1FIGM2je2Bj+cYbqqZk+evB1/AcUfK8r6hDkESUht1w6qgdh9x252t4jCh5PJamaRpgnlGZOCYD4Tvz+BrzR5TmjytqHHDe61zviPVuOw17Lbosxma582a5j850J3rN'
        b'k8+p6oypmvBUTW6oskl46EhE7FhEAg/93ySBr5E4opRI4ip3HlE0EyzQ61c2rW1Y2+k1ajLnEx2zEXOvS+LXpS9L88wj+DqRI2qR49qGdbEHY5sjOmJaYvqMRi1dyWPe'
        b'l1SxdgnPPJKvEzWiFnVf02BM04KnaTGq6dipMqrp1je7TOK+5syD8+pzyyS+UNWqWtKcwlP1GPa5FDUSuXgkPmncM3gkNGYkNnmCSVdLxTAghVRh572y/wxe5x/rlJCm'
        b'MJ2k8xeaQhDeKsAuQF5toj2PmUun+9F/ouGf/9JOwf8GMyedzXgR9w+ZOW9bPP+bgDl6QQTliQ2R/zEvZ2f6/LfgctRn5WMJGbsWtrzG5YBOWpLHPCaLZgBPMJVTYSFs'
        b'Ax1kWA4KkeGikfmEEDIHnFWiUCL7QWUg3AcOwsNTLByww5IMy+NxTHwEm3BHNiGAEzyXRuJSgvuX2MGyhPBJ3g0YArVmFH/mONyKxvt9TNAH6zHxxhoMGhEkSdp6eJSb'
        b'S6exbGho7gOKQe1KMmlRZmWZs9VBmYB1AzfbwnIKJLLZBTRyOOAImrpMgW7AZgcKkNPDgFXhmHIDtsNWAemmTZN68XgB6AmHlbNh4STtBp6IAVUUAeUoPOfMWgWO+Aro'
        b'NGbgADxHJpdgmyc8Fg52gUqZ6QgaTBw9Topjp94emhadtkBxVoLs/ch1FEDmkthMmif6vVQ8weB5aj4VuHO9H60MFZxvZoJUhxKTCvyAI40BxfKX4hICThvLUIE/iqjS'
        b'0JRRoss6wSXeYAbFn1GBB3Kn+DNgE6yaYtBwmcEqsISCxjTSFrFgj+w6AWbGOQUeJFF+FiaOXQ4veGWVkFVsqEZj00nebRNgKReehu2vTTL70dSRaNhIwQrWqgSRSTCM'
        b'k1YaCYfHU9ew8pg0KbidwsJIrKDKuBeeSYLdJqBCiAsDzlpTL/XAzeAciwYrQC+mw4TmJOVTGMH2RZgME+9JsWEwGaYeHqOoSwMxKM5ua7iPI8yGAfskMyzW3xfhHkOt'
        b'8FutA+cX/lr6SYTSx9cC0tIe9vPv3l6Vbmm+NKPN1PSDRW7vdZpJlYxu2WJ1ZFdH7OLUqO9bHUvkKi5sO7lQWaFUSiV/kaeSkufRIvTPtMjg5441eSaXU7iDmjnLMjf4'
        b'Pb3LHZy4+7z/+Y9XanZ/K52+/Xz5imfdd9ZYvMjTWvL+VxNJ4/tOQp2vc6+uTu4YZt+P9B8onJGZ1KkXcC/yflzQQNynLP+IpoyhvQmpL36YEburwHj24Rlba082unjc'
        b'ECtatOv8+pz51yJDK+vP5g0+TSktULhDn3tqXVHyVY2IHeeN0hsHT3x17viyU5k/yR6P8Auc5xW6dUbMx18svBUZc/NMakxkqtw3n0jx1m66laL7/ozi66vivxkL+7J0'
        b'4NCLzxbvHr20Ytvnwe3FNx/HBTt52lnUKOv/ba3eoq13ju0drej5lP5dzY25lYH545fbJe7K8Fj0ZPMH/rnxKd8Gtufa+tA/N9rUZWzt8Ku3ZW7/4ZyCPu3KuPrYjBx6'
        b'+yaTtvyIIKef3K5Fr4iIv2w7JLPoM7PmHzWaf1wkn16cbHvuwufrdrcXy9guvJG9euaIYs93N8H7qxX/rvndaJbjxKwClU+fOL/0i/2yrc/I54PsW2Y0VkvVx81q3Y96'
        b'0+bRYs69fObUd/egzLNPPWsP6x9Qj/1adrflHB8N8bvih7Y+eqrV3iUzmmfSG7br2vknrecG2wPmuyUrfV8+07Hlo1mPn39xV/78jkax75/n7bzW9ESqq/7Xh/MvvbdR'
        b'9qOjYnJu7TtoGmm0gvyBHQ3XZ4ZsS335m+XvAT7X627uXVVxYOe830wvivV+E3rOo23xmVvMqjCpk/ysPXWSPZVeSXOvfvSk6kn67RdXo2+abF5iHfn76Wx7d2bRom8d'
        b'Tl+00+J8XSB7amg4dDD6YuP4uP+1a6/cwm+aZk7s38NbbX61K5IzuDTq4XXtO17JyzRi73rxtq4aifn6xbMPZ4f2jIcGesx+Pstzh/x60XrL/uW3guf71F8X82n8JHt/'
        b'u/xnJ4b0TeRum1xdO179cZDxj+tkbHq/CN19xfGE5YV1a5Mylx17j2Wz9ml20SCzUYcZ+qno+K9anJsvt756f71WQo/6Jz7DVpd/8jm2cz1nw9Xv91390dAa3tZ7kPjN'
        b'CtamM1Xe6/ze//XhjkUfmYSw7jDbG6Vlm5cGsR1zfE6ln75dXtJdu0376/BL2wtUWq5dnpDRaap9qPmz1INffrJwuu74s+rVie9jSr74RewWH139uufhL2KfvjK5/kr6'
        b'Z9VLEzJ3LJ/+tlH9lzruzkWZex5ds66f++taib7NrdYNW55ovFKOoP208Srz1v6OzTk1f9e++WRw85Mgt2exRRvS28Y//fDGmc+0v/kt5a7OyjNXftgcqXvo6gbaojtX'
        b'T+57/LvEd84xBXfmfXjL9ctFF3/48MFGt9sTLwpSUS/5Pet2aOQvds2lPt8N0VYF/34l9MpvGz5f2npx48NjFf05l+9d08hR41RrerzXsfDjhS/pP9ZdO2e20vi4oq/r'
        b'6Vf7DsxT2N0UDjqlvFY/GO5Y+uzxb3+3LnxY/9X+54e+Otp53vdefbAC98N9vy3RajRN+3VAMVUtY3WX75yJUxW1rt9dVX+V/pO0wu7RmMjqq1qR5RuZd3kFrt+7uP8w'
        b'f0f4knC535k/N4nMX3mbvYLQV2a7zJi2cJFEw8xr+AroBANkmeCyyoewVzxyXjv98gQUxkI2lDXdWRboDMDkldAocjsUdJly4K5Ih2nslXQ4uJ6yEW2Fe+2EWSloBEWL'
        b'oA7MSkGDYCeJY0kAPG9uBXeCcmFaCjwNjpBlVaLpejRF0ZaaTktZgFZSnc+wLlM07M4TsFLY/la5fmawyw2UTMFSnEGhGOg2TCQ5VQAHwFm0CJyp9BqWAk+pUcuzPrA1'
        b'CRXVQlgpBEUBbW7krsEaFmaigELQSXFRMBMF7oXHSRpXFIAGAfZkO+gRkFFOM4LhcQ0KuHHYGmxFD5jCpjfRKGjIaSdpi0BLwQFYaqUGjwvQKKAFtNoQ02Kn1PlU9GC7'
        b'EeGiSDGiYStoJYWsvQFufs1EQaV4BO4JmoSiNIBaKnfF4KA7x18LnhRiooBBUEdWz9ZgB+sNKApDOh0cA4fhXvK6uaH5dCQKAzYlw1I/isIQZWWNkqc+bzoPRRFV/AHq'
        b'41vywT4CM4F1CyieiSwjFu7XI6b6tihbPdwgOi3HhkKZhMRSh61Hl8GjQigTUWeUAAHJRN+G4qAc3AhOobWxZ7LFlF6ahzcpzoWwy4EV5J9vKc1GuQWNdLSi3wEpm3QZ'
        b'WGaKD7jnRU2HGKSgtTxl3BwNdsMtAkIKLHlvCpJCCCmgdi7JVi5s9+RagcOrhSEprklgL9k2AMWwbwYhpOAJNSxmo154Hm7CoBQdERHQ5QCLSSxGro4cdgY8Pw2G4mIE'
        b'm0nNxMHdNqhzdOdOZ6HkwHJQStkxN3FhFzcItbrjk0byKO218DzZVchE366i6B8KhoSEkmJF7Rw0wi3e00AoDAdHeDIMUBhvvN0J2mApZx4SGZM4lCOwP5G8bJ0pOZ2E'
        b'wsS278pwmyxpDsagR2kaCoWBGlojOKcNSig+xFF4FnRgFkp2IqGhYBYKbNQkX16cG0tQKCfBaQEOJYORAQZAMUVhOWgBtpvDopzgaUCUJFCtThpEWo4uy3QJ7BJioVjB'
        b'SsqkuwH00FlsMXjyDR5KJaSwFUiiNGBKthQ4PAlFAWeXwX0kWfqwHQxxrdBk8PgUFwU0psA2KlllaMa+S4iLwgD9aMXQ5AU6KPkAtnOmo1EYcPt6NO/s1qQ2alo8WNyg'
        b'VE8hloEkKNEjG1cMWE4n4gIc3yCgolTpU8yAznXgDJqS6xZMkVE0QWUM1eVOg+JgWBqAlkAtU3AUUMMwIl1uuSVs464BW6bm4GbKVKvYhrLZw7HK15rORbGLppK5z1ZU'
        b'CNTAgJ0hoNU8jPQYDXBK5Q0iCkpzUiAFRJlvRgGczofBY1M8lFZFISSKvIhZoIAGBloywQlMQ8mGPUJAlNlgO5WKQbgJHObAMrcpIAqsgYOk/pNBiRUXLVb2Kr0Gonis'
        b'pmTFaWtQwQWnA4R4KEuNSM0nW4M6Mu1H0msSiAIO+0RQJVkFe2YTGgooX0OAKJiGMhOcIkLKFOwHBwicIYi7HHW2okB4BiVYDXaKmAe5k9hnwr2gFi85AlGFT645xMFR'
        b'iv/ezwK9HHg+fIoKEMWhhoxeeCCRFSSIEjdXKbCXAY6hij2hDRsEDQA25bFMYbmvGWmUaHFqAAopprs23AxbhRksTNC7Wg50qJJke8qGcanRUhJTWJxYRGprO4vgQTiB'
        b'agvH0GLqBJLreSuEISxgC6UUrC9D6kiYwMLQ9gWD4WrUdmuPZiIolVOZ4q+gJXIpyRjD02QagAW37CE5ir+yDA0YpIoPYbc4HEskMwQQFtAYC3uJ8BaFu2wJmmE/rJ7G'
        b'TTECuyzJE55IGHZQZyzBSNYQbAoFTamDhRQeZDsaD0tBafCaFcLglGnUFNsoIjYUXcA+QVGBQtiMigutneEW5ko23EomWRvQ+IUbK4ctCUvAPrCd7SdgYaiDzSI+oMiY'
        b'kqibV2VQj8HiRSTX4vAQwy1yJTUixYPt1M554TRQSiCq7jry/poFKkLb26zlDB1JWIPEbi8pbun5EbDU0gE0keLCG8vw6GJSTxve0+ayYVcwakp7QHW8OZLI8muZ7+Wj'
        b'JoSj1Z0NT5ljZac9sEWKg7caYDWjgAlbSDOJioD7udh/SzGeRXZFoH62E01+FJSZ60G17TN8PJO/UvWP0Bi402HxH5kxcCugogU1NuDgFHRFC/ThkYuirsBjtqQFKIEy'
        b'YfoSw3AjaHEEnRRPZ4eFGdcPDs2ZhH+BXdnvka7mEZyLbnSDbUKMKQnQkUMqXSMSdJoLkvcHHAzYC0+lgQ5QTWmSHUNVuG2KawPK083Yk2Ab1DL7iDAD52TBfiEuDNwd'
        b'mviaCtOKpq9qZJLQAnejPlphP8mFQfO8SlSp5NyjJgcMCagwA6CbIsPQGKGgdg6RDvHxDJYVOCc2iYUBh1dmUdKhEbS6CDFh0HtrwGaKCWOPRBMuJjHU4BtYbCy2YSFB'
        b'wrgIyh+enQ82TzJh4HlQTKQHxYSpNSHtYh5KUSXstgA9oHOSCwOOZKHxjLCaQbESKxsMTkJhVliQYmPBFrBTgITJBA1CVBiMhMlaTwmts+BMAMsSNZahKSgMLM6naEcn'
        b'4jG6BR9GbAC1FBgGQ2FgEaCaK3prjw7BwmyAA4QMg7kw4LwaiVpGD0kGy8yNwlCYLXAXlecyuIMrTIVBT4SJEyYM2GRGuooGmgFUCxNhGPDMelBhgzKNc5eFRFg7AfAU'
        b'waHpYJg5qL/tJ0kQ1UkgWJh+0SkyjDcoSyK1qQm3gEoO7Jw9iYaJEsy29HRAEeG/LAebCAKG8F9gvQ5b5T8MfMED5ZvbyH+w+1R5c49eiPOiJ0Wd0qS5/GucF81RNec/'
        b'IF3KRB+L0fT0/42MFnOemjlfzfIdjJb19HcyWt4e+M/hWZRqZP99eBbBRwT24PWhTRENEc3GjYtRvnEYKolmOjFIJudFbXJ8LScB7qHeuym4IZivZf/XCCmv2Ruy1bL1'
        b'q5o2NmwcM3HlmbgOS/FNOHy1AJyi/+JO/n+MO5HFKcUNXYWvZopbg0y1jFD2BfgOIVv5iI7FLYvHLOfxLOfxTefjUMkWSYwv8Gnx6fRuC0bFwzabEBU1Mp5gTtnDM1nq'
        b'GhOhdHsMRLEnQJQsCoji/i8CUZY3LP8rQJQJUSaqO4l/mRviX+1fn4ePfsdM3HgmbsN5F9deWDvmE8Pziany52stEvRmHJlMgwwuQd8GX5SU2JbYMcsFPMsFY5ZePEsv'
        b'vqE3vsdp4HQyelldrDEbD56Nx5iNP8/Gf8wmnGcTPhIRz7dZwjdMmHxOnG/oNCEuigsW9cfH8jRt3X+GO6KtWxdbHVu3pHrJqLZjp0en+FOaKMpy6FBMf4ygpO6bW2Ii'
        b'RodrqytqbyaWR3I6RUeNwvtshxz7HYdnXXS+4HzR9YIr3zl81Ch7JHrhWPRiXvTikbglY3FLeXFLx+KyeHFZN6Kzxxe4XRS7IDace3HlhZWXAvk+i/gLYlHB4ySLzsfA'
        b'mf8CSv4LKPnrgJIY+lzMJ5mL8SRYbDxeTcdj/uMNzP/b8CT/36aS5DMpKknYayrJxzaaXBerB4aaK+lW/1YqyTtmp+XiQkiSJS7/ApLkB4wkwRRggiRhYiTJ19h4ROk/'
        b'wRPhEh3Ld5JEvsMl8Cb94BtMYwl6C0bE4i0YEYu3YETeDEujwizHtb2mkCG+0+KzfFcYpoPYYDpIKJ1N6CBRFB2EKaMvoIOgq6dShOrRPP/CzHewQYyE2CD4+knQFBvE'
        b'CbNB5v51NAj+QBj9vpffuLPrc6arDNaAwj/xZ8LQZ/D1c3dGFgNTQfBPigpCdgIKQzwJFAQWW/gHWuX6BcISCzrNFAyJhhtmg+bAaZo4soLfExKoPVWqTMeBTKE0MBRD'
        b'keAyJAUYDdlpocrT/pJ6/VcGMw0DPiROMNqY1IdSjIl5EDYOwsZC0kUyRbJF8kUzipTTpFNEhMAaIgTvIVpISxE7IT6F9xAjoRIoVFIolEKBSKFQllCoBAmVRqEyQqGS'
        b'JFQWhcoJhUqRUHkUqiAUyiKhM1CoolCoNAlVQqHKQqEyJFQFhaoKhcqSUDUUqi4UKkdCNVCoplCoPAnVQqHaQqEKJFQHheoKhc4goXooVF8oVJGYXCmlMVMMCiUWKRWJ'
        b'ptFTZqIrZXJliK5Uimio/JnoObEiiSIWeloOlb4CKX0jdF91LVNyKdvkjrSHW2CEp0DH67MexhuGVtjSQfgJiloypae/Mgc7j+dSzzjMsqB+2xFX6/jKflpkk6pkXCs9'
        b'NyETIoFFDDGIFtjdoLsrU/OIJ/icVal56K/pJkDCXuEt9FITk5fq5aWuyEvlpi4XikLIRgmbxE2L4V1GANMV2qb9EZSDbT/80lDuiLbc6tS8VD1uflJ2BrFmyFguZGdO'
        b'zCvQ7UT038qleanTP56dunJpTgoxvUVpzslalUpU7/LxkJG1FptpTHN7r+eVQSweTN3YAkO/rOl2INhcQmBJRFWEtaAeJkvcQs/UnT35WKIeNxVbtKxM/bNKwnVo6sHG'
        b'xumJQlZDAnudnLyM9IzliVnYSlrAjUJFgC3A38gol5uYTuzjUzFpIAsbz1G510tJXYHGSK5eDpVwYvpjKrjnjltYdg53ugVIck52NjZoJG3vDTMjNvMOc0121h2x5MTs'
        b'lQ72d1hpOXnJqUtIjQQliwhJQjmaQCdxE/pRKT1p2niAJlC8lEJSi4V6DiWxcK+hoX5DT5Mj6phIWhVPya71okQdU0RIHVNUSPFSZIOoQB3zjdBpGI145j+B0ZjWB99t'
        b'p/Iu0yVUMpTV0sLAAIHZDe4ViSTe11WOKpeYpqEe/XZ7NtNUqiW+q7v/Cd6BVMtcbKWfnIgERgJKUgJlPkRFNhWJcKtNXP52y7+UlAzK2Ezw3WmtFrfv3PxUQc/n5qMu'
        b'OSV53m7WPs0kb/XSDPQG7riJ+StzshNXZiSTdp6dmpcuME36EwP5PNShV+QsT8ElTImDaV35XcUj1FrnYvNCbDFIxJqwnWTGclRBiVS0bzcqE3qYpBNJJ+HPE7QDiTZi'
        b'jefKLK7ecgyveGtUgRg9gAplilsxVYRUzAK5lfKWTL7dsjLtdS9PJpKeS72KTSOzuDkUGwOVGhL5qWtSk/PfRSSZLhlNzZanrtabIrbMsbJ5C7Nl2kRInPamSrJOEBef'
        b'hl3Y0NfNe27Obl152Yt9md1Tyr51ajOXlrFe4phSAzXtskQ/IuAZWAe6YTnsxYoIK0HdYuKwoAeUsuF+cApQ74BjYCvYQnzZR1D6wadAF+gGbXCXhCiNtoG2AXSAY0Rn'
        b'lR3PILCn+hVLs1KT2DSiSaoIWmLQ493voRHZmeYMB+HerJ9fvXp130uUhl7SK8takVWv5Yy9KGLXTaCUPo8LS2Rh8WorK1AJCrFmUkCQlaSZKZ02C1aImVvCFqI6qwYH'
        b'4BmWmel6eIJOYwTSHUPADhQJPlSEFbAU1k9Fg6KQAh0p+DedZjBX1GC2DIkhxCCahQKNcy3x+dBZOmjJwMkwR7eUjWSFX8/zM8sNYsMucz+OFT77fI9Ji4JVElpYE4IU'
        b'Sm56AOym7jJpEjOyHBjL3WlsJnGYqZ0AhjjwTEIQ3GkJy+1sHBg06fWMzFAV4jATHoV7PDhwa+rUbTGa9AZGFjiBoiZHkLAR1nDcwZmpB+g06Y2MbM1lJKVgAOyBtSi/'
        b'xLDLFz8U6guLHRRfa3x5yomrgkZYT2bb8OwaUM6FreAkOWkKtYSUxpUi2M0EdaBNOd8HPRWvmiOs1W5KtNNCULwBHI4lI3ceqNWC50GJMjwFT3GUQAmHBcvAQSl4CpT6'
        b'h4XTUtPkHVFNV5Nm8fMSqqbl/VOlpTdo0PJj8cwPlMHKNz6xShp/BBvYWftHmsJiX7gzHBu2cSJhJ2miuH0SpfpgP9EZRlJwGzgmKgr7vYxAC5vmtVoJ1oIzYC8qdly7'
        b'AWIFsFtuRVJmHmoesI9uDPs4pK5EQfl8lkRePmhYhepdhG4Ga2A30W5eoRsPu6VzQSHoJi+doBvCA4DylOqBUsVdEQTauFitgylNT4D7YQd5TQsOxnBzUVH0hkrj1zbR'
        b'DUEL6EBNiZzY7Q4GtVzYkxsMa3CsYICuAgdcKUs7sCUKfxHukJr8YAo8QHlu7Zaw5cAhWPxGtcNdKvlO+H6tKaq3IKyph6seFgVa+gdH+lJPwzIaekFQbWAT7KbBuiwW'
        b'aAYNWWx6PjkCbQfNJhz0ppe7Pz5+FTj70oB7RXJXwXbSVFThuajpX1iFqjc4kkabWSACK3wWEj3yxfIi4YL2gYQS3A03S9Lh+SX2GZ/585lcXby2f7n6WvS15Yq28j2O'
        b'NXWBPX49GRt6ykNElfRFjrgvCHXTCpHTkq/XkXcXNbPJzg0t3Nss9cFHm2va4hV2AMVC1ftb1mjGb708o6B3TVi/V6WvbFd6+mDOhxPt37/X+p6xbLndKcs2jx3v1z3a'
        b'mZXrv1Ou8Wr594kPrmf13m0JfPyRjeP3Jpmz3jv5clO7wd8s2sYNDCRcVt/guq35+P0vdMA+zd2hMfMPfRE+Mv/eJfGqU99US69VSDw4K9tDu9yz28Dcti5w/WXPiJD4'
        b'aq0zAYdPyp+SUvYOqlCoXvOF9+0N9S6iCicX7dG5mxl46UTancLGb779ctu+j+V89sje2Wf1henXP1t9PZa/PnXbb+XuwRrGqytU195zf3rIIbssJmbiwYcv56Zqxzok'
        b'Bf/tA9ml1kf9bsRkep+/VT9mfGPtPauwdnW9ryoLvyq9dfvWvqwYr5TV9+MkTNJv39BqBaKFkrEPzW+pW442Ni458wy2LWt70jDgKP+3GUnnUi9mhrZYfp7t7N28MmiX'
        b'3Jfnt47vb5/z8cLcT858WBOdvH/H7X4R7Z/6dTvNlTwvRJmUmwzMNM2VffH5y5qen/P5Z89IpMe3vFpwLcbhzITyzx52DLNtL03MwL0QVa/BpHVfhZuML9r9/JnNNtfa'
        b'++fK+JueFhi779x1qu0rbaeW+Ll+4j9tODsi+tXlbUre4atflhe/rztzdsrdvXyNEeuX2x4Fei6ZJ/YiNfXm2o5qhc7fhxJeco68v0RPS7qrPfZB2N908jPpy2oYzwLP'
        b'mX6y79rOp8E3V1l++erDWXUvVA653F13YsZul+erjicrL80a+VmR37Ha9VFU8Wr5e72r+nd+ukCL2R1jLvlIR/RAJzPzxg8tCin3RubG2tne/LV+Q3CI9i7FiIthV145'
        b'ffPVzOuVc+1nN39e/fXzJa0eP4iw87+aG78nzfFmgNjdH0Ju0xLdHl090VLBOPd7QXa20bm83/aYlvFf6IbqMXWqfb/ZPqS58srnVdsPxa1+Fjd/5laZsyxe/eXoej/d'
        b'gSsg/XZOw+DaX4Hrugfnf4l40L3m+18rzuR+t/7FzcDa3Pnv59TEy/964fTuOKeT4QWaVmvFl+RMOPb8Kl/xgSl7AaXzcxbJ6P3mVoE6sJWBxEQznZPpROl9NYBaP+Kl'
        b'CA7YWAt3V10fEVjmJEtZefYrKYBS0IHlJ5KrM2NhCYPGAgNIqqTLU+5kejeYmfsFwCEFcRR/EX0e2Kz3f5h7D7goj3V//N1deldQeq/LsrvASu+9F+mIAtIURVBWFBt2'
        b'A4KCYAFRWVBDVcAKVpzJiaTvC5pdTDPJyUlyTm5iSWLKSc5vZt4FIcm593jvuf/79+NneffdKc/M80z/zvdhIIWD+TYz3hZhPzxDMMReXuRMPicWDfD1QuYKJTwXpZLP'
        b'tgGnC0lELryNkUmwTpjEZ1M+8JBKDdsZnrRlMDujqOvYiY/64QG+CiUoUMll28Jd8Bb51RQMwe64JH6MC3c57ONiUS+x4Q33AgZvUF+4jAe7wMgc9DSGTqMh9zBBO6wE'
        b'x8ApzSyz311sVUt3J4JvXgVPPfeBo6VLsA4XakjukfC61Yz/G3AxmqAd4DnQRsBuBlmggRcDzqGOtBVNO5RWsOA+Kz3iuwxeg7sxSxJsxOCil2bjIUzgCaV1xMEPcXHT'
        b's30bknUPvDXjj40LJESfFWBkMarR2IQ4PoYtJGqAfYok7OARZT+V7QSkEhcOTojhgZiFzhg6HKeTyIeX4tiURaQSOJsNbhMEjG0MRmMuLUR/1BW/a0ew4egCeJVIWwkk'
        b'yKzqhYngMmzhuyTg3BRZWbkpwbOgAbQS8EYKuOHGYDfALXBcgd8Ah9fAS+TneUCyHtSbg0NJgtgEl5gEFqWzkuONDOYso60WHjwnBjtAP5lTKGAr2h4cVdANrjKoxNsx'
        b'4BCBOjWgUUeVClZSUWdrwV5U49j4V8N2DXF8IridJEBj8mrWVnAbDpBfEnxLsfO6mKIZkGYWKhyx2luszcQJW9aSGdQh7AfHGePrTc0m/ssIfLPYShkeZyHdDZkzyjmd'
        b'r6spiBNpEGxOHwt0wF3gIqmyLDiA3bddRKP7b+GYCu9059gk+xJVOIq9wyF72DuNiIQHwDkGmlQHj4NjM57l4HnQSbzL7YL9JHIVtww36P3gTEm8ChKhHcOOh+AxIt32'
        b'MrAbF6xRn8XD8l1kgW6/jQzK9gisxcBXuDvyuXfGQaREXGYfZXh9+rqAMqXOUYbX2CzYAxhnfqipnmBhV37g9EYGtuoATzJwqMNKqKnVJwnASPJz5Op8cJ4D68FxFikQ'
        b'26aAIOwUftTgQbQuOM4GdYbgMKk2cCsG7MbXJXRBz++vesNBlO150iqNhVVopsxFmr/GIIEvs8B5sSkxkmUOcB+8mL5uZrKnQukUcSJAn863mMQBnp2PrXnjBnhJe93z'
        b'qSPmKRPCg9EJfG7UAhUqNUJNB7yk8ComWAQPi3kaaB7PxZDBl8HoNvYiOJA27cevAzaJeZUMYkkVnltRzHa3AgMEsDQfKQ1TnZ0DFzCyHHW6PHxDQJlaAPuU5hlpkfSt'
        b'E5w1ceJMAmi9shf0sQMs5zM98r5SNJWs1wcnmASQqapSOomcYNSzjDBorlPmTmJkobAddccUC15l6SEVnmP01ZMDuzXhTXhj2ieZO9xJmlssaAZ7MAANzXdbFI7JpgFo'
        b'9YYEYuYJhjLEjtoz/k39t5MRYAk46IEd6YEmNuNLTxu+TDzmOiLzG0AKRrLE4Gkl7iRsQZcwGh7gULbwZWUv0O/AgMyulMAWMVoMnVUht0UIpFHPnLMYNFJM2zqM2sgZ'
        b'sTVsfe659FwSU9xDempi1MV0Ya9yyhQH7GVtBns0GGxaPagFV3jgwMpYfhzfORH1MborOMvXRn/LJW0daePaHAEx3LNOCE6AgURltPRUBu2wG+74Fi9twRnwMnxptqXM'
        b'ByeeG0uSJ5pL+4HzKolgAHQzuTfBOi9C0ruDes7R24FMwZxibpxma6JfjUuip816HrzGQZPo01WkeaxAKrnAI0MRGurUoISC19ngEKqLWpJCyLIAVMCeqDkAOgY+d6GS'
        b'a/b/LU7tvzgjw1qes+3wh2dlhJNuweztvLkUexJlBsoWHoY6TovWQonHPX2u3MSsw6HNQWodMCIeC5s0iT4U9nD6lf9IwZjtpElkU5jcTtikdE/Pemqhcatt6/qW8iaO'
        b'3NKmSemwltzcqiOzLbNjWduyHtGkuXCIRZu7y8y9aXPvEf1J84CRAto8BAXUwA6ClrQtYfBkKCB+99DKT27lI7cKe6yqZDy/SfmRBmXj2G3aaXra/AmlPs//UExTWKuB'
        b'3MbhUBx6WPi+oUWrWBJ239BJbmmLoTAyy0W05aKh1HuWPnKuS2v4idj3LewlhUgQC2Er531rpx79npJJa49WlSkj80e6KEXUFE3tpfa+kyZ+UgM/ubFZh0mbSZOKAv0m'
        b's11E2y7CJbWS2/N6Qjqzu5d2LpXZe9L2nvitjdzOucetM0Zm50vb+crsgmi7oAm7JWOe49Z3fGRh6XRYuixsCR22hKksK35PyWB5b7lMEIIxb1ahhLbQ3BZDTGTmbrS5'
        b'24T5kqGMkZDh7JGt4yV0UBrtkS7zWEJ7LGFqzFYS0pbdkduWyxysy8xFtLmIqVwUcyRyzG005nbiaKLMP4H2T5D5p9D+KTL/dNo/Xea/hPZnUjGzkbi1xXQktiXKzIS0'
        b'mVBm5kub+crMAmmzQJlZGG0WNmG2dmzD+PI7m+7W3KmRRS2ho5bIoorpqGJZ1Go6arUsai0dtRalpT5HIlfa3HW2RESh1o49rE7jbotOC5m1iLYWyay9aWv8k47cwhL9'
        b'0URJPKFU54maIuSmVh2+bb4dAW0BTeEYMKDepo4heBNGfj12g9xe7qBLr4vM2Y929htTuqtxR2PCMJYwQ2RNWmRLjbLl1g7dJp0mTyj2glWsVuUpU4vWqo6atppJU8HQ'
        b'vElT9/dtBFLhykmbUqlZ6SNlHOiRCrXA+Fhcc1ynSFLVvblz8+kg2sD9aNwjXSTQIz3K2hEraMpGOKQytG5YnUELyFyjaNcomWs87Ro/XjRpk4rC6BLVDqX0rpIJgmhB'
        b'kEwQSQsiZYI4WhA3njZplYLTeWhqLbFu88Hlw8YsQK3I0OTYhkMbGAoNmaEzbegsMxTShkKpKGbCMGaKLxoKw+C1q/HD8WO2dx3vOI473BFO8lNale4ZOctNLXBaMlM+'
        b'bcrHDBhecjMrmZlgwkwwZEObLbpvJsDNYvvx7VMCv5Gw25GjkbfjRuMYDNyEf640OZXBnMiSs+nkbFlyLp2cK80vmhQUo5aTpGghgkfzKWdBU/g9A4c/m9p2hvcsHGL3'
        b'mgxa9FpM2nlPmvrgogj/k6IMBU0Yhk4JUKO8mjmciYEZY6K7Xne8xj3vBE0KUnFJeP+kJMIJM+GQO23mcd9MiEuy7fi2KRefEdvbDqMOGLsj842lfWMnfJeOF75T8lrJ'
        b'O6Wvlb5T/lq5NLdg0qUQFSFBUQQhKgJPiIvgKDfHRqcxpW+soGKXGfJoQ15P7D1Dr/ctHKVOCZMWiVKjxClDa4lDj909Q6Hc2rHbvNP8tGWbypS5Y4/KkMFQ8ZDWPfMA'
        b'uY2TxKhVRW5p/4RSWuDTypmycO4RjYTfswhpxZ1hR3VbtczSnbZ0H/K9Zxn4gQ1v3OAd4zeMpWmZsrSlE2lLpS7LJm1ypWa5cg/vViUCpBV1B3YGThi5P1ZHKT7SpQxM'
        b'ZtGTzGfgI4eV0McR/HFU6V9Hk/wXAwqekMziK/lXh5FkNRQXE2v9fQf1bFkoi8VyeUahjyf44wWQJ2K8Cdmp4kYNa/pz/lsUpyv/K4rTuQWY5jcdRRnP4jd1mz6DJoe4'
        b'LlbFKwRWzvg4SeDqIZqmhP493el/S+IVWOKT7BeV+AaWuIM9LbEpllhx9GlVWjRHtv+2WL2sB2p5zMlJ0YtJdxtLd36mPq0JeyGh7CthjmLwcdH/WEbMZ8tlPdDOmzkr'
        b'zit9QUEBFpQ1U40OIVZV5aXrqor/gNTz31GjSFqtvOmjwhcW9k9YWM0ZYZ1xrYrXo2olx5AzJ5D/ToErVV7YMsfntiVBagWmVi8vqSBkq1bLCyqq1s9hav+fS1qCJT1F'
        b'vaikb8yV1PS56wLCMf7vEevsC4v1Nhare0Ysk+dihcaE/ZvU2vfCUtFzKqtygPpv9nekh7ZgvWj293D2lqzpSnFK+wNe+mmi4n9XU9Ug3Kt5mAn1xYSVqU0TnlOtaXhW'
        b'v2O2iRGKVaY7/B9LupKRVI2RdH3Fi8n5YG43bawg7v03yVYy3T0XLC/D2JG8irXF5S8m4Adzu2dvLCBOhYE6lM2GWv2WE/rfJr/OjPyFZRXi4hcrwENcgDeoOQXAyfyP'
        b'CjDjpqmAYnzyHKNqlWqpWuUSzv+Oq6aPVVh/BBjCeDkMqiB4ueVlZXOAEhjUUlasAG3MQFP+iOs4ZXmpmLBVp6Bil64pjqisrKhE0YvLZ+AahcvLsTuJguIZEMjvUsH8'
        b'2OUKiuzScsI/LF6PeodSFN3pOT3xHBjf7xJRsJOvKRUTFvA/wBbNAXbg6SqmfH0O7FBNrPJEz96wAbwcJ1ozw387m4s2GdYmETbemWN/0OKjsT0kvCoCRQU34TVwkYfe'
        b'x/IxoQY3LmFxNDlESnaaS1+ZCptgrSA2IVgFXExJ5kO0DnBdo+MHToFbVfE4pZNwGN6OA+ecohMEMQmLk+GBNCdBgvPcVHjw6OJo2ChkgbrVRYbgLHg5mwt6Fq5mU6Bh'
        b'qy48Fw9bTOHFKg+UILwebRX3h0WaDy8nK6SZkQXszVdfuDm8VPet7Wzx+yh6W4p1++tfvTU27nqys8WnnqXv6rb+wnr3667fiuxEZznrXCw5Yfww7bCF+i8/qIsPYLsE'
        b'e1zW6je2tkkP1lp0TDl1zRUfTti8jep+DR1AbXLyFbULwu9d71noxN+MMN15vqBv53spLitDdxbpJPvXa6YmLTDlcIBK2i/B5v7eS3sOFLmLNlQZlSwfDjhgfL/mq49V'
        b'Nf5mopKfJbLZ61Gobfvh0L6XTOU3x63vhMZH7/iqvni3XHRgna+tbZiuqmbYOztNVJy+cdIMs5daRK69cRRmNXymtbrtDWOfHEpSENjyYQpXleFC6QJ74KW46a3PLFe8'
        b'f8hszVrOV4Kt2Yr9f9AQazhTkyylcsW9/RB1Zoe+GeyE3XEU3P/bPdREZcqOp+yfCCTkSr6GdvRz3iN4vWruRj5SUAtzXrlzS2Wce1rsLEYcrQqGf2AnuO4E6wUKIp5I'
        b'OAJ64e5IcvaVBvtBC97HxdFAbanbzJmCpZES7Ksu4Sr/84WkMu4dZ9xiPNDG2Nq86ba72WROXznnN7IjqY8pUL8gvtOSo1iUgZFM347Wt+sUjym9y4sYsekJHYzpj5ng'
        b'RUw6RtL6keN2stildOzSCf2l5BZu+KRJhNQgQm5i8YTSmmfdFCo3ND5W3Vw9ZWkjcT+xkWwAZUlzlslyCmj0X1gwaVMoNSvEO0WV7V6Sgu6KzooJUw8SLk/uvuiqcFh4'
        b'RzRWCb3GQ9+Jei1K6pb2mMNyTWc9pVi2GZhA1DyD9dDUvMOnzaeXM1b5rkvsSHFP+uDS/qUTLrGTTnETpnEksbjxgndWvLaCFqZP2mRIzTLk9o5oiWzs1Boht3Fsj0OJ'
        b'Gjs9UqEsrdvVHhsjyX98oky5RLJ+fDKf4sexfiT7vbvnh5uxjuiHz9foCbVFj1BTP9xQC1oEomdmg0DlP79fIsYkoPmzfJaoImX9Zyr5FM9mcPv/cQf1fVgU6wVvk2CH'
        b'dP9HXgb3/NbL4MzQP9NhcxJLV595RUmMjwbmnXdpn/EVqLSlWbS2hKL87rM/+7aFyyJHKh6bYSs5XAO7QL/igI0croGOhD/wEWiFmV4NfrNlUlZcrth4x2GwjVciGzcy'
        b'O7bl0Bapns0LegT851n8NEtt3657YbVd/v+Rc0jqd2pTSkwrfbKxkUM8Dv/5pBXRW/Pr+w6JOJRGF9sYtWRShb/XCX7+3TZWQUVFmUIpGgqlVBOlvKA2/pPEf5mtjo3/'
        b'c3Xg2zXYaJ9upqYx5WQaqKzAlLMUDnMYTDlVq1uiQ1TFRqqacY2zjaM+RxHomTNLKewajkJVv3k7G00+V1X4ytvcKZFVIkMiewScUBaAVgy/m8be5cI+gjA9Wa5kJKX0'
        b'CB89S5NFEVRgTAZocMwQ61Sq49BdLEEVaCAoxc9dlEta2CS0Fs88nKpyx8n3gQZ4g4AA8MBaB3bDa8QFQEMcrItPxH4BUpJT+BlsKjdYFXQqg91VeKiNQbOl83i8hvXg'
        b'IMF5rIaXCNRDmXIuVAb95aCdwQa2ZG2EJ0A9BhZOowrr4AECDAXn4wtRpqAVnleM6Irx3AqcI7hSeCAZ9MHWjRinQDAVSnwWOJcLm5maOboRNoNR2MPjzvDyhsBTJOZK'
        b'MTjEI8esoH1dImbr013BKa4Bh9IYItfDsBsc5sWpw6uwgcuPUaLUVdngIBwxYvh3W0AH3JkNzzBkOkpKLNBhrUkyTS7CCCYj2BjjwuWrUOo+bDT1G+CRmlePXay2+fms'
        b'APRWgfMkvWB4BIMt+ImwUaMgnkWpLGMv8JxH0MBxgq1x8GAMdqUWD+vjE0E/7HKZplnnBSjDA7Bl1RwD1pw24PXYgDXmGPBc85328vTvNd2VvzVdzd+ZLj+RmGfqKiU0'
        b'1ZdYYfPsi1tLETDletgKz4nN4KnEWXR0EriHVFTuGlgnDgL9Mc+Ze2pAN1EZaNxEVGoDbuDD82mVqoJ6xhiuwyvwlhh22RJeHwKwOQYPM3juvcpglzge7gCHhKhNqLHM'
        b'7WBbFcMUBPrBaBzc76+uYAoDdVuJAYFLC2A3rOeA3fGz6NHmw2OMYZ5e7IOM8gjYG/ec/Q40wy5G1FtqsGsOAV4mGNTjLLCgCMi8Cnd5m4BEJxVjXNdQ1pS1EB7lKjNx'
        b'r8L6ZXPigktsFNexhvHquwd0w/1x5fAsPPichG5jMAHULgadyTxYKwxMmMt9NwiOMnU0DDuEmFYvIcNvmlbPBNwgaNk8cBDcwqsnAWpMAi4/FhyBfQksygZVno++N4MC'
        b'XrnhOYUdHOTEslEVtUQx9dUGb6prFqH2RDiRkI2rsQ3hfjhA3KLDU6iXOfN7cqVAgYJeqQSehjcJVzgY0IXthHQrnkCpcA8E9sNGfjhqOA6ZyquXcojbDyS7JsblzaWV'
        b'msPbpIGa005VtL7aCS8R81oJB8FpMQ+0z+qMJDlMXzQA94GD02uLYOeZvgi0pDCw/d1rQF0casbHZ/d6s7u8WNjI0E63wFNrUIhjjrN7LS8zRgcvgSvb41CHd4U/w1ym'
        b'ougmwIEECtavgOf4MyxdIriXGKpDphtKsSEMdyGKDiSUx3SwXciwUUWcBD3PO56idNIhIc3vjoD1zvAmisPypuDBkhySnCGqq26et0cCH7UzpeWo44SHtYnwjtZmyPqi'
        b'+S5wGHQTstej7K0l8Bpzj7XbCw7NYbRKAqPzpymtcuAVUoxAa84sXrkKlRUc3RIgIXawCY6Cxrgl1Oweb25vh8xwL5dNhNSCdetAPbxgo79BiWLBHgp221NMs+2sSRIj'
        b'XQ7DYRXs6ZoCTRYChtW7LxL3mCoU6CylXCgXcNGEjH3H+BqUAdWUx9HLj38QUsyQmqup4NscUmcNKj9+LNGVeamsh7H8I0vwKNlnrMe8HA3HnOhGqSrJ+VphagsVnOib'
        b'1dHY25Olnp/v8rFXwNxpBme6U3TGnTzqQ/GG2TI0SdrG2sqqZonZLKqIOso6xmJRDVpKqNM8xyEzOFYiM2tiP2ALXB+wNojx5MqK2TD7Sd1/RXF5cfXaysDN/r89UMQr'
        b'jzyBP9nwFgcyKxGyDfT83UzsWnU0p8LGQ9aKE+H50tS0scUge9wOZtPh+T+S2dkuvfmsqhBi+WGoi66HGNrYwhfEEI652MXJ/IzoaT2CNnBpli7BRbYGC/VtsE8rX4Q6'
        b'RWw77vZQwosNiOBz+XD/LJikWboSGECt71gpTf3IEW9AFUcvi7yfmZOkH2Jwaqr8m7OHP5ScPfz65V3WrxgVxodJF626Z1RYu9hmVdEeVw//Mn1h0V8OHHM48HHEj5xb'
        b'6f84veLKRfuh7nbuDwWW166LPnp28psTAaLJX6MDrQ+faE48F5NY4Ke5J3qCK47d2nHqVuyDXvcHffqf7Gmz5y9s7gwzvcWv1lAH/KDMB7vcrytt/A8Dq7IgUKqek2X8'
        b'hctWpWcad21rtBqtC9X/Ic98kNv9SrBwb8Nyb7t9WvVrV+zr/kVUXlw2b36ydmnIFeMglRMRKm9fiH7lRpvmyS8/KzB4q2Csvd7z3ne3Nwc99P3L6IbvuvVyp+QVdae4'
        b'xhfGQv5+Yvd+S1tbG9D/6mb1s1eTigyyPIK6YjZQVoU2nnaa9fOP/vnprz4Va66WbkwM/9Fmvvn9r77ctqv5630JLhNc52POOWtHiloz98jeanL5U+biX7VFtzJZ+QMH'
        b'XpVfvBG/u6+bDg/f3vgdeGBe/GWN4dC65drXfln1QVan4XdvbnEXn3ccvn/pYMOyNfaJWs56P91doLasi50t0/7Ya96r/KKvPP9q9dnX18dPNNSPpBquc7mWutPDve6d'
        b'Ou83euM3//T3r9IawfmPbny/RbXuiJ56jeHjhkx+/JHcO8s61t6/dmDejxFvCa/9Xekj1085hSkizwPGqcfXbQ9vtP+P4TM/vjXvx+K3hKt/5RTenTz+eLx1Md1w99UG'
        b'41/+csqmYUWJc1PpAZ3J6vKvzvSdvPHondf/fCv0zWu1dh+FLsqzKRx8s+CNw9E+4tiPlv0irzui8aD/ncTz1h9e+aVw7S0wan2Xffrg8vK3TqyXrfnsL29Jx78cG/+y'
        b'P2LfydJ3J5+VqHzT+OhqreeEY+XShkbp7l/uZ0z2n3tXmvnd1tCTMsl3H8bXL/t5wKjdov0bm1YfobBtZ1l3xKtbSp7y5VUnjQ/dcX6jecWR0E2XNOOvPHz1ly8+3/Ld'
        b'hiusy190fc9J1g043D26uvd65PaixcuEI1mV/xAP7Pp598fXKsHWwYqX/rTnKvzZPWM48Nuon38VvLlGe9W8w5/dDOHvcr6i0lO8tyDm7Advb3pn58CJvxZnBO3b7LHt'
        b'g6+/m/o4thvk1CzY8MGNv90o/9ven975+uD+v18/kn3osw69t+gNq5fCtVeP+jy0NCl4aiO7Ev5h3f4T499kN32+/+u9vYmljRbBf7n9xUZnzV214Podof7iH2KSuPaO'
        b'w19fSLh1KKhTuKjm74ZfuXtc+j6d60O2tjaoRcWBc2j0PygEPUpkOLkBuxnG5TJ4DPZqwv3cGHUntDpA819w2WUe6OaAE6BnKYGL2sBanqYzZrJtWOeA2QpN2RlwN7xA'
        b'gJM1aJbWBC/WgLoZxHgAuMTs7LV6Y0hyB2hfP4usdgjsY7hZd7pu5ZXB8zHg3DRaXRWcYKh1D8Mr4CUU9Ra8JZzFzgq7MknCGw0wTTAadutmT+TAS84M6e8tJOlNXCQN'
        b'MBCzLl7IVaG0UTAHOOpO9hTVLMBBMRpHm/8JVhoN9kMMVvs82FsqRqkdgkdm+GPRkEUqNTw7Sgw6wOlptDRGSmfCEbLLuAa05Gg6gZFwPJ1jp7EC0XxmN7PLeBb2Eu7Q'
        b'22ufQ6Hb7AiQ2BV2F83mUO5DAY+zwfX1zAalqBQ2ikFPsmAWGTHYtY0B7R5Ot5lDNgyG4KAWG0iQohmSwhx72MqDHRswLN8FE0UOsEVRoF9BvgtO6WKqczTONq6eZjoH'
        b'J8EuBjyLp8GNmmpgkDuXRhke8if1lA6HlDTB8S1OsyiYkbaamEo8WoVv+plqYhwy1paSDwsMz9/OIFhbVEEz4X4eNjWfZn6G18Fpho62H2tJDPfHxKBJ6IBTHJtSXcdG'
        b'C4XjTMoX03iYYxdV0wFyYQGT7FqCPURo92pwE4OG1zGIbA20It2XyQbXwCVwXkFQrgwvaq6NBL1rCZ2sMjjOQvOPQWfm1sm59BwUPU6bz0COYTPcRVQb5AsaNeFu1dgE'
        b'ngpazlxjgUMJQsbuDkSaiuNRuVsSBeqCOIEGnroZgctKXgnl0wyjZ2zF8AyXYcvEJLzkyoEBmtHDltxAAmvXLAXHxOULf8OWy1DlwiExg+xtR9OkGwpm2WEN2DHNLItW'
        b'mntI4ZahOjyCAgx68WcRY4rgJdLmTbZUYGp5ITj4W2J61HY6masALVlZc6h+sbiXUQvOKyb141gIhjShhKrSVket05oVAq5UM42+BbUKMWwB++BBJ3K3QzmCBQ9oJRGV'
        b'bQHXsjXBFdjm9JwZFfah/oL0CC+zwTmkbXh7BgGeCyUMBrsWzTJva/KLnZ6zHmfBFmIlcdvhYQWfKiYIvq7gUxWAWpKlBjKd3ZpG8ILgOaMqaiUXGJX0O8P94nzYOIdW'
        b'leFUhftgK2HOhocWhWnGWugqiE9R2boZTwc34PVEcbwtuEH0+Rvq05B8UlFGJWC/5opE/gzvKepPFBTRh3PwbV1kf15KqMCqcWxreAncZky7BfRhL5MlOS7PmVhDYQ8p'
        b'8FpwC+zjbQEtgtnOE9B8rZ+5GCEBp5B91Lskov4cNqLfNXNRev1stEK5hRqlOVlpHQ8mIRq4sDZaCS39DqwF59nwNKgD14idV4Hdi9DCEzRZCnHwTlYylFiS7O2Mg3lJ'
        b'LkhNeAdHldIEdYbwFhtezVJnTlh6S5GmnEEbWnNw8BXnRXDnFhLRIqlKHB8TD2/+5rbNpTJGF60u8Mysu2DMTbD9FeQymAsc4Vr/38PM/xXgoDX1ez7V30HSmbMgjedT'
        b'+s3cf3n2T/Zmq1VnzoViY1iUi8dTqoJl7iJRldu7YET26VwJW27r2OPe5SvniySRchf3zoiHiidJhNzZjcENS1Qf2tpLVnUFDmVezb2QK+e5D3mORA4H0bwwGS+S5kXK'
        b'eHE0L07GS6Z5yRO8rdK0HOnSAmnxanrpajqtTJZWQadVyNLW02nrZWkb6bSNsrStdNpWSbjckdezfnBT76YJR2+5d8DIhiHlHhW5i0jm4k+7+I9kjBWP5tIu8TKXTNol'
        b'U+aSQ7vkyFzyaZf8JxTFz2FLi1bLitbTReulVVseUdR2Vjj7MZrJMH+KWRHsZ/hPMvMtmfmWwXzLYL7lMN9y2BK2xKNTXc5fNJQxUjKcR/MjZPxomh8t4yfQ/AQZP4Xm'
        b'p0zwa6QZy6S5RdIVa+jcNXRGuSxjHZ2xTpaxgc7YIMvYRGdskmXU0Bk1KDXPTg2SWm/eNAtjGM0PYxKd4BeOR0nTlryWJIvPpeNzZfGFdHyhIpKz25BDr1DmHEI7hyBN'
        b'uXoxjGshtGsICuHTqS13xhp0EQ0m9SZhAs9QFqpIJxfMjdmnO5QicwykHQPvOwbLnYSDOr06Q+uvbhredN8p5JEyDvtYhXLzlrsIejb1Jsi5roPmveYyrh/N9UPSDi7r'
        b'XSbjB9H8IDlPMOjd661IQubkRzv5TTiFjFT+/s0jZY6Hw1OK4+L4TIVy4ndWnd74RJXj4vVIhRJ5PdKi3H2+NdVxs2Fkf2RBeQWOrBhXoQMTac8kmWcq7Zkq88ygPTNk'
        b'njm0Zw5SrFcIW5pXIl1RLl23kV6xkc6rluVtofO2IIXls0KwwvAflF4QbSWSewYgfVXIPKNpz2iZZxJJNI32TJN5ZtKemTLPpbTn0umw/tirYfGdJNo/TeafRftnyfxz'
        b'aP8cmX8+7Y9NKiACm5S0TCzdsIUu20IXbZUVbaeLtj9jrElhVBK21NabtvJ5iGrPstdSxg2kuYEybijNDZ3gLh5bcXf1ndUSlSlbbk/J4Oq+1VMinxGCux7bMF5yp2ZS'
        b'lCHNXkaLlklCJdWd8Q8dBZjxVaIk9/JjyB9lXvG0V/yEV5E0OUWaWkgnF+EMRbTVIqQhRjsyfjjND5/gp4yzxz1f05i2NrfBPGxtITQ/5PkrQgOKGVQVrwTug6t6Vw1W'
        b'9FZMCOLH5o9F3TFFv3h1auLAM/qf4CeMuY+V3PFVxJpmiPWnef7o1aJONRw8uzd7MLc3VxFGKBrc3Lt5cHvvdvTCu1ProYc/xq1fzRvOk3nE0B4xEx5F45kMAW8enZAn'
        b'SyiiE1DhJIG0lTs2RYteC4mK3NWdMRXUDzHCM+0miuZHyfjxND9eojFly5fbOUg2dSbI7LxpO+8RE5lPDO0TM+kTd88uXi70YGg4I2lh5BOKZZ3EkkTNDW9422zUTOYT'
        b'R/vETfok3LdLfMTBwZDJChZhzlkcK4GFesA5sRZg0taZnO7bxeNYCayPXT2GCkaMh9dMuoYrRGcKI+MG0NwAVCSvANwEr9YM10x4LRufL41fSscsm9Gqrb3UwXPS1mtk'
        b'1j0DafKyCf9lj/QooZvULYQWhMoE0bQgelx/UpAgifrYmd+zot9lZN6Es+90K6+85+T7mEPxBMwvk86+yLR61nVuljn60I4+9xz9xlTHWXc0ZMEpdHDKveA0VNhQVgxr'
        b'fN4dk/FMaXrGa0ukToE9qkOsXo2hqJGQ4dgplNbGfv8Rtwmev1zke9Vv2O9iQE84epSJImhRhEwUOyGKlQeEDLGHPIc1PnZ07vE6vXVoHerLR1PHDHHC1/OkyYsnAhaj'
        b'XmyENawhcw2lXUPvuYaPG0oXp7xmIovJoWNy7sUsk7t5j8wbNhmpnHALGcscX3xniSwik47IvBeRPRUUTofnS7Py7oXnTwbl97ClPNTv+D90EuBiS71ycO0+Z05VVO63'
        b'HBY3D+uT5z4o6BWg/tLZbZDXy8NfZM4BtHPAhHPmmOFd0zumspAUOiRFFpJJh2SScDJnX9rZV+YcRDsHSVSnbJ17V8h9gsccpd6xqM1uo+08PnbyknpH005J46HoQ6L8'
        b'0NVLonxGW+7AO6P5OI+Dx9gfCSHj7mjlfCFrXD3FBP15YBepif4onKY+UF9fXVS8fnlpmfiBat766oLl4uL/ya0EhfvU2RMI5ow1EcMV/vWJgwPeI/TFu447qGcxMSwW'
        b'ywo7UrV6gcPXp3iXtF2FR/VrenLIlumZZI5OHxs/5ccnKnMxFw0uqupKjzgMl+nWngHaeINbZNtQvwTsi1NAaTCQJn0pOSc0AaeVQD1sA+e5HJJEOmjSxuHEOjNJ+MJL'
        b'5GjDNMJldgrwuuWsJFhqJIyK8So0m2xcMx/NgWP4YP8M/YCfEjycUE3ohMBlMezm4bvD59Dqt9+PgMPW4guYi6MVXkJYVP4CNTtwCY6Sw5w0XlCcgtwENmdP85uAm1BS'
        b'xWWWZs26cfAA3wn0ppGE3DxQUsfACUXuvnYq+KiyiTh4R0vZJuyUCm+44q0IMBqXyeTuNOskYik4rqaLysicpfSCllJcLjNw7I8Klgt2krOUarQUOiX+TVrpClfqW+EA'
        b'Lh12alayXQ10BcYTyy1NpF9hi705eE2VczPzg9WTyQa3n3l+2eyw5sH5v7277d1O933jyYsPuW1zclILrN0vOS2UdRl/a22cele9R+3llGKhb1PAT55bF/6S9/c8/5gW'
        b'F5HX1399JdDuyx9/OPmRz7MT7e9ptese8fqufU/zMvesoZjvZdZ+f/puQag/+5USn5987k3eOXyu5Luf6Q8Kg/+jIKNidbZxt2ncHm/ltz989+fV2x9m1v7d4Nuc9xfN'
        b'H3VuHD6w4ef13/59f1cH9/NnDdc8YndMHd2R6Rap9Gp9f/WKImnwV31mV+TNjZcfXbM895rk1rl9Pzz46/jpX3Wr/8b9cPOe9/QKXGO9Pzy58K3heeczuVnCVzy7jr/Z'
        b'WZH60M++bsWr94PfrHxl40/fPHYd9HwLth6BjzSW5+7llNf2TTQtX/3KpfluJw2trpxt8yy12Ndz2uhqV089u7Fll79B8leTE2VPtvQd/2vvqvGQ4WN/XhuwIO0ue8HG'
        b'vs8GPE/8siTx3hIzj7Gx8csfFW2PtPLjNV3+LKvw0maDhB1fLeBsk6p/7eXkm9e5ctDM9qj85/e3h9ywOlDdsMpBtEmr4dT8wbqgr73+rn77y6SfRL8O3H4o+2XD4Ct3'
        b'81Z/mJW4cembr/trr9hq8vMPF9brmGh/f91Y+smt+J9S7359y+bb4dCOhU7Day61fLF06gvJCvVYwafaSapvrZF89kr+hajOPT/VBah8JdqWFMBxMvqg6NgX24PeZB/a'
        b'xV1iIF7b3p756YrIfK1LeY9bXBp+9XPyEe6KWX2o6P6in49LQpsnO+L5X5tGFcR+nfbYYk96q+7T5UnRadyna4vHvjrlPb4tLad8l45DxdcLmv+66qW+1WfetmpR7dYY'
        b'KI8a+2ZzxqvdBYPmfw0EB28cumx8c1vI49eTj577TKfq3aabdMCRtNC722Pu63151Kx565sWUK3u3A3LjL9tyLgWccKy4IB/pTQiV9lvtOCj11b9uPR9TfMLv6rzzw3Z'
        b'DlRHvP/tX6+krIh849axCHF750Z7j1I55+0UjcKfnLTOKzWIP6w5pndA55tdyz8yLPqHFa8+6S+t5u/+zfpU4o2+zN0P4o68E1xVP7I+K9KCvUjt8yQzdbDJRMD7IYH2'
        b'WtD8eoXnkY7Hh75O2f+RDrwyf+k7vD/7/JhSHfvd3SDWAk2V1fve4ArIVW4BatRdoH4jOKH6z6/9M5f+U5PJgl83BAyYwJ2YZOA5wYAjvEY2RoLM4G1luC9u9v6tcSSz'
        b'N3fSCe4XJ3LXxSwFHbMvtlsDCVmOc2Ev7OWG8GZts5o6Mw6RDqOfOtFK/SbY+0ee7uEgHIXMVfIacCNYHK/Y1gIn4OjM1hZ8uZrZIzkYbBiXBM/BYbxhtoEVol3M7OnU'
        b'WuaJYQN2WqTYSUNd/Gmy3k/UTxXHi8oZ7g1cbHiJ8UgFjyiBSzx7pnw9YI+rJrwChp15jFNAVD5NfTbcvWIbqTjxetCgGQcb1qFCXOWyKOWNLHgCnNAihAIubmIxc58f'
        b'3lSmwGjZSsYX0XHwErwkhnUoT7wp2ZiIiRY0NrJBP+yIJxtOJeAkOANHE8QMSQK59A8v2ZJU9QugRFOwEpxEKmRnsvzC8xQO3cClbDGzdYUyHKVADxoWmP0W0Jviyuh2'
        b'PRcMg6HnLBGnwCmGI+MAqEWxrtgRt44Ug6LYVZbBbI00weNZCmeTDXGw3WfWlh3cCV5idt5OoF+HGX4YJ5/pPT94Pk6xuwK64bHfOMNZCPfBo2uU5sOX9UgRPMFpEzHc'
        b'XwTr8LaUYlNqgx9TvIYCuE/TyZkL68HQ9B6clwazW7gPjpRpYb9RdZhOhIOk72WBRnAO3lKcILxcoBGOXcUdwDviHHCJBdpWgEPMbv8ZeNxHU5BQCeuXG+IA61HG8ww4'
        b'q9bYk4yVYG85pjGoWcts5apps4sS4R6Gw6UPHsXkOrWZcx1ZgrPgJOwhwGDYCprBblCflBGBxrzf8RCB+hyyawZvLjFGpnki5Df7T3jzyQdeYKrgpWitKDAC6+OYxpTE'
        b'gjvgwGJmh7ILDK5bAI9rztoYhkfNGM10Wroz+A94CO6Y9kFaD3aSylkODmMCmGgeQ1akYHEY9WU29vu2ZfF+QycEJelKuUif1wg2eTncBa6Kn1PYoNqo8yXNxKhYyQa1'
        b'PUaEvU41qA7AOTCgKL2aN7tgKTxD6mgpHA5Fv2qB0dmTqhl8M7hgRzSlswbuQvalgi0M6RI7vdOIZ4MmATxMehTQA/eDGyghPEECdbPRFK5LVOB10K4PjxR960Ka4Fp4'
        b'6g9ZUTqrZnNdwJdgL2NiI7oJeNpD5jxhQWA/aFSldJZw3OblkiJoUSFxs7JdDBqncRywVhnN3g4mkmYQDAbgKE4nCdbFC8AoPIp7ZJQSh2MNO+Bt0mnZoH5gF0MBZefI'
        b'V6EwBVRpwP/q/qPa//b+42/445n1gzn7j+4xk/UD2WR8Ca0vfmQ2GWuiWJSFDeaweErlcObZNUUoyAWeUks4C+xaleXWTtjrz2mLVhVMWxDUFiQzFdKmwiHPCVMftBBu'
        b'C5eb2zyndRjKmDD3k9vatYX/GcPBo8bt3xG+JpTF5tLovzB30iZPapb3UOTNOOuRiWJoUcyEqHQ8450laDWbtXIyobRVRWoppI1cp3huQ/ZXucPcq4JhwZj9Xe4d7ngk'
        b'HZo6yUuTZubQvJxWldZq2shJzhUw22EybjDNDZ7gZoxF3o29Ezu+YTI8A4XZ0KYjF4iwA54JQdjI+gn+CiQU/zU+g6iX5pfQsSUo2GbayHmKh7cMTEdNb1uMWsh84mkf'
        b'THzAS53Oycaxm9/Jl9m40zbuMhsv2sZrwiZlxON2wGiAzC+B9kuQ+aXQfimtqlNcz6GNY0qT3IgJbvb4QmlyFh2TrZCF5zro0+vzfHNmgpc4pnxX/Y76XZ07OoqcHlrZ'
        b'd+t06jB+TpASuAJmd8Kf5vpPcFPGVDArxLjnZHCKIlEUnvhFcaWtXFuVpyztepSHDK5aDltOOAXL7Zyxb6qejZN2Xq0RcmchirOxTRdp4WrgcKBMFE2LomWiRFqUKBMt'
        b'pkWLZaIMWpQxrYaHyB6QAZD7/1IHzwlLr9HIh1YOOLvnIsqZF0z+zCuZlTdt5f2bH3xpK1+ZVRBtFYR/0OrU6tbt1GXcgk1YxY0oYw81t3VGdWTecbR33CN1ZW+L1ki8'
        b'6WK26JnOWpaxy3cU/nxUxKHsnbsTOxNldj60nU+r+pQDt8d+kN/Llzn7087+E86JdzhjMVBn0iGpVVNu68jwm0zYZowqjaRf10QPY1uk6Rl3treqTVk6yp15rXEfWzp9'
        b'bCeSLgp/RLHsM1nj0fJgfF8BPcqT0pmH1gjs0cS9NeJkwpS5lcS4Pbdn3YS564iBzCd2wif2z3ZOvSZyK+4jDts5jCV385G7eD1Wxs8P/UKYh6cU2z6c1RbxWIWycHgo'
        b'WDSUiXf1lowZ37W4YyELSadD0mUhS+iQJa2REq+2JDlfNBTZmzvBzxnZdLtmtEYWlEEHZciCcuigHBTCsy1xyta5x3doE20bNxaJPlrDp7guPdn9FpgSZsoOKcYVSWMf'
        b'IPf2H+fJ+W5ICvuAhx5+5C8qjhrF98TFYVrrpE201Cz6kRZlZdexqW2TzFJEW4qGYu9bBqFyO7rIHLxoB68Jh+ARj9YouaVDx7a2bTJLt0lLN7lQJFE+oyX3CJYo37Ny'
        b'f+gTfNty1FLmk0D7JIxvfGfba9sUDni8C3AAD7mtc3dAZ4DM1oO29RgxwLt0tG2Y3Fkw6NzrPJR5ddnwMplHFI3+O0dLwuQC357CwbLeMloQPpKBPp5QBkgbPewpofuQ'
        b'+8DG990DpUGpk+5pUpc0JLyru0wYPCEMxr+K+qtHrPu2vu8ZKg3LmfRcKnVdKucLZfxAmh84so7mh4yl3c27kzfBT5O7LHroF3w7cDRQ5pdE+yVN+i1+QrG52azeuJ7w'
        b'IXu5cFHPtjEdaUrGRHCGPCrm7pY7W6SpmXRU1pDyVZ1hHdSxuIY/UsYRkG65gke2WMRvnSihn9QvfVKQIXXKeGhhe0LzSZUK7lkfc3B3+yNxoLInSyNbhSXX9UKfzF6T'
        b'HoPET1b+T265vNjwofe7vaZ/YbSg1BWsF3hnaRtG9Jti1gtT7G/F9EWw/U9wodiJkVyjyu04zx34Yyf+eIY/MPFG5S78cRjfhDXjUNQDVQUtwwOt2dwHDzRncQtU8nDo'
        b'WhzvB/xRhz800Uz9gfrMteYHqop7ww+0Zl/SfaA958oruSFEbpqQCw6kTv5PPDb+gTuYGUU1KyFFzXEtEYxvXOzAV8mwOxgtbb0nZthTin0np9W0t3g4bNRgtOpO6sjq'
        b'1zzolEw6K0e6eCmdW0AXldKr1kgLy6XeFVL+2ilre+wwxfGZUiFL2+cZhT+xpxTHR+TF43jOtD+WKOyPJYZVG44s3MRmSo8vN3BDr0xEtbHojaHllJ6z3MALvTH0qY1C'
        b'b8zspvSEcgN/9MYssDYevTG1ndITyA2C0RvTUFZtHHqlSDscpx3JpK14hdM2EJE3+qZTeg5yA1f0Rt+9Nux5mBAcJoyJZmQ1pceTGwSiV0bBrNpo9MrYekrPhUnJWFQb'
        b'81xKIZbSbbaUiVjKZBYR09x+Ss+VeWWOXiV8r7ZA2/pbAUvb9lsVlrbZM5WlHG27ZxT+fEQ+GSZzPBMNWVgk/s3sl0UZwx4lNjhYDI4Wz4Ge4ukhufVThj6OqJELR9i7'
        b'yLTXBPVajRK1metHSv9714+0qN9eP1qRWJWEnufBc+C4yHWRu6ebhwhcBUPr11duWFclRiuFIbSwvwCvoNXJZXhRV01LQ0ddWxM05q4GtaABNsMjqcloXXQsQ5mC5+Go'
        b'pib6vEqqaDU844rWbCswUJUnxPdzG2E9h9KHJznwWgAcrcKrcdgeAc5jWK4bpbrBDS1BRsnurxV2rkwioA8O2FWJl+0dcBDFRCINE2QxOA73FYhQSdwpeAYcdw8A56vI'
        b'an0nWj9ems6ViWzI5JpqxqCwD6Jlw0ERGwOCwVF4QwRGGDz9etgpRhmSeCyVAjT8oEge/lW43YL29ctFKhS1CClmkR2QEJD6vHIRweEyWc3HhQtBhYTXXOA5cqvACPTB'
        b'dhEyBg8K7mJ7+Jsx2PbrjrCHKR6Ox6YMwG1nfRQtGlxnMtu7xFqE+ipPKnC1pxj0klghsAHsZTJTxPIHl1koFnjZjWQGdywrEaFO1YsqAke94N4kcgkBDHCR+hgpVUFn'
        b'ZZErpQ9GUbSwDJJXMjy/VYSGI28qcbm3O3iJufXQB0+XMhKGgS5VW8oAZwQl8CBTg1fQ+m8HuIgefSgd2O3DBs3M1j44ZT5dH6gibFCNdGPn3ljKdnCZgYS3cdDC7SLS'
        b'nC9VCod8WaCVqZWDdvCyQt9WbHgEDMwYSwspH7gFRs0wFDqUsuKH+oFjjKitRZEkS5TjPhuOLYqENbAaDjKingEX4R6M2g6jNEFLGNgF9jFXRs4n+fGIWXJAp78b2EUZ'
        b'YBWsc2Lq8syiMnzBNJyCEtAazrJiKMxbwGV4hqlMXEjVApRbfxqpTnBsPiNlMzxngYeXCEroEwEu5jNaqIMXLUiFknjzKYNQcAjXaTlLYc1xyPiQyiMxfOhMpA+8QPwK'
        b'bEIt4TCsLzMmBWSqlWlGpE6bwU6ixHgTcEGMVB9FleRHwZ2bq8hOWXMGao04ONiFWfPBDdQUtm8D3Sim5kIirCXc6ypGyo+mQCNoj94SRppQuqYzowcmlj+lr43KTVpf'
        b'nz+Jl+KMmhhWfwzlDZpiykyJBlnJ+KYIVLRcXDlW+USDC8EpEs0zXgujLalYCjSti4V715CeonBtNaxfSjwoTFs3U0SsRziyhtHjrkBwHl5kY/A+sqmBOLg/jug/FBxZ'
        b'TKTdjUzmCLxQqYgYxCc9zAZwNRteRJqMp+AVcbwR7CWaXKgdqJCUFBNHasH2hXO8CY8RnQSB09ilNlJlAkUtToC14DDjP6HNHzPONk5H9qcMMiKxLkXwEoloEIMBfkiZ'
        b'iRTK5EIi7AlmFHLYGvTPWI8q6ELZegqIPqpgI4mqXQYH4EWkySQKdsGLSeBWLNM4DnPA+Wn7UbUGLSbTJnA4jTGgJhW4F15EukzG7TN5LbxNzHyVgz8TJ9SKHeaiaFHw'
        b'ZXiI2A1strPF18UWU+AGd3HKIpKXqxHTf3LATmwAlctgH+oyjqB4pvkkliEcjtNEakxBtmqYstKDWLgb3KlHaoRE8ofXqhWZOXgxzX54E2jBpE+peOPvTCo4lki0r24n'
        b'hvW+qJHWzzQPfPmEUWI+2MWME3tBF2zRRGpMo1ampVmBG8wdoNPwLDY5zIGrqFVF963o40A9bGdyvwUbYD+eNaZTC8GudD5oI9WzHDYvJRGi8EZjJdPPoRa3j2S7ETSt'
        b'10R6zKDAKbAzAzRvIxW02BR0Tg8vOyvBAdAyrYyzRVXYR5K1OzyoiZSYSTlmZKqJSE6+gfAiY9ujYBcHzba8cIQO1CnOJx3uRiVNpLwsfAWuL0sE+pgO52qQu6JiOKCL'
        b'NGDQVUCqFdn7bebyzVl4mwvq0VM2Jt24nA0OwRNMoc+BLiGoR5paQuXDQ0vAkW0ks+zVoaAeaSKHAufBQA4c8CCv08CuUNiCiitA5pYsSAU7SMuDN1GfuR+2oPIIKR7Y'
        b'LwTnqxmTu2EEr6bi4iI7MrEGI6jLxa3cw7MStqDkeXgT/RbPvJTpF49n6aSi+renxN72cB/oZBK/Dncthy2o5K5UJeh3BY3IMnHwtHRbfG2IcqHgadDvEltMRMyEtzip'
        b'SEIHJGGGAxiCB7gair6uCrQqRh1cUahNomqoxwM46HUiWnOPhKdmpiJk0G2Nwz0+6IY3SLfnAm9ZPu8SmMq+7UjscI0buYwVsQXcZoZsKxa4RTEjRjbSA24AAXawbXrk'
        b'Q5HQ9EEDnsTmlMYiIiaowH0zfSPchXpVMAyPE7spBNeIBPDlFeAaIwLciQpRCHcpRt4ToJ2EyATd2xkrJ0VFXexKuIekYQkaSQj3/JTnTUk1lNIPQLMG0uhPggZiibGF'
        b'yEyY1rINXFINU7S1RTVcFtPXdLrCo3GwzgXWRfPZYEcEpQYGsX/7veDE52Qi2VQZzNUgAIID3mx2PIcACFxWZmczF7G6bLU2bGW5oq4oP/5NO1/F5a4l6kYSjhVen5aN'
        b'pomYl+mG+jZ9rGgc3f+TrWbMS7sqpcRvOORedLxG9ibmZbOFTqAj2xvZSb5W/0oH5uX6GNVFj9lIM1b5Zbfm6TIvO83mFQxygilqbb5Ldk4Q89LMV7PmFMeJovTyy5TV'
        b'IpmXh0sM8stYyTijpSWL3ZmXlaFKGbEs5g73s4U85uVpC3Z0AIsp5tAmJ4pcpx2JNqSaUYtFufu/KV6Hlr5pkeSHSwlKdmpMAcqOJfgxoZPEqlmHWERWrQ8TSqnPj7fh'
        b'f68FMfXIUnG5yWF+pZerUJ+LyL+nQUwTr0W9QiceFKkKChyqqYAn4bXNOqVWiTzUcqoplfXVJanMXVYyBb64LmCupcERcJZYSWIsyU7L0TAxlkVEN4vYsIgp5BbHBZXf'
        b's0l1bG0t5DMvv1+QFd7AymchtfkWx7rh9X1iKXS6yxY7IWkM/VbvTXuj0jTC4D/KY67kXrF74zQNh5+sDZ1vwQqNVttpJ/ef/3nEfH1VG6svDqc29F9oMvTue69/IDwh'
        b'nTL80741GX/ZfqE4YsH2O20WB74K3dWz6u31z25+/u2XW7Z8u/p7L+U1959pqPSaH1jk/go3Xv/i+LynTnr1rdZvd4W7nA49EXbEW7cxa3fSwOmQsq6IpWOsT2wevLLb'
        b'O9y/wdbv+M8uHzutuPtI47F3ol7SJ+mfrK4++YNK4ryPXsl55eq64z/ovK330Z+yP/G5EeXf+KzO8BHrcdhSu1xQ/ElUlsP5h5+a/7L0U/2t+99Zq5w5vH/1yEHTkbqc'
        b'2593rO4/YGJmcklVle3x63sej7f0g+pV/oErv/lr9beFW6Q67p8ajzf5eNz69e7ndVcKS+6KLFzLDyS4LWl9WPbDldKfgpy4738t4q0rFI1c7KpxPykyS3L7VE309fdP'
        b'Y187XPTTt8YHhvcJP5n6+lHZwVTHFT8datp9IfuuqO4v+//q4trcUuYq+jpqwp3vMNG8tOPpvgfi0+kjrRkjUVUf/FhvsqnPUFLm9mDnO8tfcxgdfmPbltyiXxuKih1S'
        b'Ll1s/uazLuOn+67LJwptL16xu5jyvn9/2qD12Y9X5mq03Pjk61Mi9/qPS7n5294ra4/8aseJ8r7VgrULcxN5kQvSUqcuHN49sf3ZrlXFJR82up8+P9JyJMrx54l03y+T'
        b'I15PuZN5vuAISN4W99LtpsuX7v507NXdPW/QhZ9HXubZ0dvSny69r7HuflF5y8bSnGcNGV+U/e3cF79UGVQ5fjvVXrHr9T2nDh5ec+TIwK8fvZbX59pY9beY9L94af3y'
        b'y5eLbo7UvwuPn/usZ/m2XpUPR3RuHVny5Kb8+L2hhSd7uuHprMtVb1v6nlSJGi5I+OvNnyfWftfrYGH2uUrAok9y/nLtgyn/t+8Xn9/2eWsCvTPoY7uimIsxjbaWVb2F'
        b'94e/+9T+8dmvfwg8Mt/ru1NBdNi6LlVzwUtJy55t+7DrO4effxi479GYJlufteW9+QsWOXivtn8Q1C6NE713MEP6H09v3xXUWl5ycD3i8tU/ErfkXhAtc9l/bKCiVVDx'
        b'5q+fH9TIO/Ojx0vb9RPkldWCc6es3h46Z5lW/qnl8lfmpW034OowB3nnwHkBvqeQEA+6A5OUKeWtLLR4PTaPOYU8Dl92gfVV1QzRklI0C82Kzs9jzllPw35+HObR4sXx'
        b'nVmUJuyrhu0cdjg4zJxA12VZw4vJ4CBK/SpaR3A0WG6wDvYTGAFfE3UE2xPgQTAQq0wpFbHADfsqkmU+aDHCHlFiXGKUKM0VZhvYsD0ZNhDEPx8PRczFojgWkIDdiptF'
        b'103J3QixL7zGE6BEhUgcpSoWrEtIIGn6KCXA+lQ0h5p9ZWhxBTmc27RQj2GBwDeRK5VV2Ghy0blk+nLVXqO4tdvJzQSUoiELdJXDU8y1hG5TuBPJyYKH0FwLIxTgbgsS'
        b'yxm85EFixOBD23MUpeLNNjZZTuAHCbBuUxy+ZjN9+qrrygHD5Zg4v49r/39/2eC/u4OIZ75/fEfhN1cVFPcUxIXLy/NK1yxfUbx51jM5I9RhKPMfbU1kUQtCWbURj9h6'
        b'RjpyPdPW1Ecc/GTD7xEzT4uCxvTJ00PyqzJ+Ir+SJ/IrfnqkQs0zQ7+rMs+2AhRC8ewRzEKByBc1JpA680wCKZ6ZQOSLBhNIk3kmgRTPTCDyRYsJpM0840CPFc9MIPJF'
        b'hwmkyzyTlBTPTCDyRY8JNI95JoEUz0wg8mU+E0ifeSaBFM9MIPLFgAm0gHkmgRTPTCDyZSETyJB5JoEUz0wg8sWIBHpszDy7isb05eZWPeK5f55Y6mHP3I9tFF4Puv06'
        b'/e7pC+ULTY+tOrRKot9S0cSRz19wjHeI11rYY48PX5p4k/M9asPkZpYd0W3RdQm1EU2e8gVGx3IO5bQsq438eJ5BU0Zr0aFlk/Nsa0PlJsKnlL92BKtJBW8JW7ZukCxv'
        b'q+5R6ansVact3YbchgpHbIZLJo0DnlI+81CwELmJWVPYlLmNxKMdQ7YXeLey5EamhBLcs8e6J6LXcSikl0fbet438nrEQb8/5Hk/pTwWRLBadeVWNq3KclvHVrUpa4dO'
        b'cY/odPWQdefWSetFTyhNY2FriNzGXrK806E17GNLgZwn6Fk3NK9X3OvdqfaQJ5CoyS1tJCuPbx/yHqmeEEXhE1OtTq2exWd0UVAUxMpeUnBavWdxp84Z9UeGKD1UrXbc'
        b'3nkS71Y1uZFVh3ab9glduS2vJ6wnRRKAjw1tOkWS6tMBQ+60rcekpWerEv41HOUZORQ+5CG19WHOFs3sUN2gvJ3a1/SKh7z7t42IaWEobRHWymHK4XF686S1O6ZJQ6UM'
        b'kTu6ICGqh2w7ayYcA0ZsJxzDx/RbIyTWx6NRhaAgDy2tOza2bZRUtdegLI3MFZJZ2XSrdqr2KJ/WQZVkY9eqKrfn9nhIEp5QC3G64XIH/hCrc3VrlNzGtjVMbuMgd3KW'
        b'KMsdnLtLO0uHNEdSJx1CJBy5rUPPvC4vuR1X7ugsUZI78XoKetVwOG5PSOcKCWfKwbmnalg8sujipglh8FjauL00efFrjneWSTOyJyKy5c7CIeteriRMzhPhI+4RpZH0'
        b'MdGI7vj8SV48c3tI3LVF7sSXu7gNhffGSyLwQ2hvrCTisTaFfv1naU9GZKP2Zs+f4gnGlccLxyvHNd4Vpo65DSlf1RzWHAm5rDMhZKAB2TQvG2nb1glTzA/Zj6gNC+/Z'
        b'hsp5rkP6QzY9vsPrR6IubpPywmV24VK78EeOlK3jE1VcR0+CsJ09UceW+kgVm/WjzSzKwOrHJ6qUaxqLsMq9oWkUb6PHHNJpPuCUrlnx4udzYryvkv+bzrjyOAZ9z+qF'
        b'P5pGdf+4g3q2JZHFYs17SqGPFzl2W4yiFypcx5N/mPqL7PMTRiJVxk3zMWoWpRZbwUpElWiQgwe0HK5TmTl4UFKfwzc0200zi6rh1CgpDh5+8/afk2n93nGsWeIfc7Ll'
        b'Y4nZDCdbrVIJ+3+Ble13fEmc30mnnEjWPiWrOdT6cnWsx/itDiZUFVo/UnAItGEfc7A+04kwdMUvdoqOSY3Gs5AYZcpriwo8U+600KpUk1/KEXuhGNET5e2vL8J0fHvd'
        b'2uvKA3d2Rl9rcas/xOIM7Jto0LJ/03XY4OX7yUcSGk5q3dE68SWV+FhNLxattMjMLgx0rYlTkGaiZVwbpeLPNswCXQQ4ZZBT+Jw4k+A/QS9snsGAxsK9XPYsk8Rj/vS0'
        b'QLNwZXHh6rzS8qLi6s2WediveR5mN39+92BWADJZwKXHk4W1i1F7WdC0rtlDbrDgWNShqMMxhK5y2umMoVGT2iy+OeUHrNI/aj6EW5M0EKZpdOGm8V8J4qPxnH3uu4rF'
        b'qL3ovkhTqUExyR6IKzgLTsXBJnjBJRHD95UoFRO2RhW8SHaltoE94DAPNieyKfZWj3ksCjbkEIswEKD5LNW6QYfKd3nbzJTissi+kCXYheaZ8YmJfEE1OKVCqSWxxWju'
        b'fpvEiQzEVDdWfFW9fBe7EHMFXeIhq1Tttes41C+fszNYlP0pskcQ7Yi5brIoVnC+yxJPB6oM295dkRJlZBSPjVNrKsvDcAPj3uKxqDnVTppe9d1GDsVRZtkPXi3D1f1A'
        b'A3N8VQdroiR+zCaXTzgHPviUTXU9pTQpTc00IpNljQqlRQ05oPV/PG3FYS6pZOrUfapM1a2idCid2BtivJH5sLXo089CPmPjHTcjkw5yd6YkrC81XXuD9mKttWlovs1n'
        b'HdY8Q061G1exCdqx9/NyJ4wx1h/m/HnRA7ItIcbmcHFf6KTuay6vxcybr0ypstjuo++RfHe9HDFJUWmNFJfiXlclr4Z6ayaVqFeaKWfK2WwDefVr+2Q9i7J8hVpGLfvh'
        b'TSKd5xLvehriBcIn1N5DWuTdp38ZRe/Wodr6lNqXZ0t25ipRe0VrmRjChiMyS0M1BOrZsWAEjJReU5dT4meoL3ql8lxVWkLSe8F6J5e99/gnWzsH9cOSPlVvq3txuulJ'
        b'NyW/chLfj0qrstN52dnpeIBVurPpur60x7ZvNn71lUO7UZnfkzuiio9ubBJNbf+y4+/GFs8snq6u++TqxA7JXq7F22+dMZBujl9c0dUPDIqlkZL3re1a1z1V2q77Fkvl'
        b'8tKowN1HSzIi1yxsLn7/4Lu3Ise70/z+Mf++aUT/+39W827lvFovpI40B+94ffW8/CfufxuU7O6Aa6KslVtdUt8uX/836QU32HP6H4dDG5/eX19Uud/1opnBWyG6K3f8'
        b'+ElD1YFlJSNvD8wb2PTOZ3YHzSpvXDJbtzFg/8bvLtns/XjX7b6LNXvfzMp6Vefk1lzHl3sCf+p71TrzT2+pD+8uiR2+65uwKvXsF32hfX+qGBWOfKo0Gndyyasf1CSH'
        b'vv59Rd5Jt7+d2e0hKZvK/7PPwsO+Z32e6dzNeGtg29vvpD+qEXtdjkh1f+nJkOUWYfnZHZYbJp/13x555x/1gUGOg7+sFyfXV/i/lPfB1w/Xf65TEvfoQ8eA8k8amvlb'
        b'PjFbWqH/bIdqOfzTW2MR5p98eW9jj3Ldk57dj/W6c14NfNPvxE1gtjH/4JXJy7/eqLA9/uF7HSsuXex/Wztok2pkRfmR884HcvZWvKy7Jrxl9yth41usz39mf1f4sVLg'
        b'nXMjn5bmrktnJeV9s5s3ov/as3/8svjEnmu6XD2yMM0HjRlxS8AZLr79o0KprGA7Z8P9DMHGZWQ21/FCEnO4wdZyTMLVxK6o3khWoHzQVI6x0QkuFOUHLyu5scCAObjO'
        b'IMeb2HAojowM8AD6cx0eU0WRO9k1QbCWIJfFq3ji9Rs2aOs4gvPgoK4uvKC1TplaCE9xwMlMeI3hE6iNwO4umdV7MHyJLOBdwE6yDPcAB0xhfQIYQCOhfQ3Yw4pydSMl'
        b'4oEub5752ljFelolhW1QAl8mIovdk+IUr8F+2E+W2qrwAPnN162SEHajzBJdlSl1TTZoyYXtzCZDN7yNe82zMbCey8c4ZJV8tu0SdWb9fkwIT/O07WZzlMDOCAb/exzu'
        b'hddwurUx/jHxaPGvCYbZ8CRsWk7iVurAvXExCbh+58GXUf0uYxfDwVKS6Up41iMOH8JOE0fj8Q8t9RmSkT3wFD4AsgajsC7p/1H3JgBNXfn++M1C2DcT9i1sQtg3FxBR'
        b'BJEdFVTcDZuiCEgCuIs74BZAJRGQ4AJBVEBUcG/PaW07nXaIoWPodLG2M539qbV1aqfT/znnJiEottrne+/3n44hOffec8/6Pd/1800VoJmbwuTBDnhTYPd/4NJLMLxe'
        b'4LirEcZHzreNet/J+XqbSR9rxXMYbHMHJObaOFTPVFtyBy3dcHanjXUb5V4qOx8JG//aVLdJPkll5y9hD9vx5byGbRL2F9YOUi+5gcp6/AMqwNxR4aHm2Tcm1SVJc1oL'
        b'ZYVNaxShPVl3JyQoJyRIklS8WRKGmsuTzJUIJROks+5wPYd5bnLm4Qx0fOPMVw3rJexPHJylc+RseXmbmcohUMIZtnWXu3f4tPkofHsSVB5TVLbRSLK0tZOypLEyA2mu'
        b'pAj95NpKveuj5bHyXIV7W74irofROVOe3pN/x2uK2tFdEqd2dJGbKB39JIZqe4dWQ5mh3FBhq7IPkRioufbS0PrIYWcfBaPbsNOwh9VTpAyZ8UaCyjdF5Zwqmal2dENi'
        b'pZ0TlvEWKd2Ce7yUbhNl7HvO7m1xCsOTqUrnEMnMYUckHnYUtBUoMnu8VeMnqxwj0UNcO7UTkqSlWdJJkngMkC1uilSwFPmdpkqnCEk8ZmQS6xKlWfJ42eIhnkDN95KL'
        b'20wlsZJ8SYEkScfnqJ3c6uLvoZrmycOl0XSCL5VT8B2nCT1hqF47Pi298t2JlMZSFHZaDtiq+NNRmRNfHnYsSu3l3ZHQlqCI6LFReU0acFd6TSGg2bSsNt6HNDyrJ1w1'
        b'fhIW07zkmQrrtnmKcHl0z4Q7npOxxKaV0R4YI5kGrRLv8XI0zPJUVI+XoCOtLa1n/ICXymva2L9T21J77FVeUeiXlXWjYZ3hYeMnCxlouTxcxKCseLrFNHqNPbP+LHmD'
        b'lnxUJp0nwVDPaq5ddcqTlbgWsvKeiszRen6TmjUpKZz1XrhBUrQhzQqafcwuFYpXfczOE4qFHxuvzBcvFxeKi14tvpY4U+rn9qLZx4tEshrZUpNNNJLVD0iyWos5Rc9v'
        b'kWTl+UqSFaozl6knKujklDyKllMI1qsBkqgoTc4K5igXrv8ututzLly6BughSCMmFB8lW0F3bEoGjqEgpjski4wD/YjHOc6CO0BdUqGZ4zSmCENo+cn7m34T3bK9pq2h'
        b'raGzYZ35l6vHczaxQ4wK7v2WotJnsf95awY9X6xnhx6LSiNg+Hj+RsjZ6J+EouEDCmfkLM0kGTnzFIVD3MmDZpP1pANO2SXslNn/Ah9YGuRdT0q4iqd59Ks2aGWCp1XU'
        b'dyWZaKZdXmWS8SHzfzrJz6G7Pz/JrPTCW7xrDDJ9u/78U1PLh/oTOIHLsg8JyworbWdRCe+xV/Ysf6npE42ePtFz06fBdX9YgabP3E4ilmZ9ZObx/Nxdftm5u0HmbtR7'
        b'NuvPXTmeO/vXM3cFFJ1Shswdg/a2LGD/D8zec+oEg+dmzySdSIlF8BZsT9HKmwxwDIuc8HQZkciCRG5MfuIPRlTpF9vWz64xJYXsPBaT0pidzdZprNbxGQy/CCRjUqXC'
        b'aQuC51E0VO0leMw7ExtAEE9kDzspcDwMNpH73/PlxLRRtGn5/TVlFHF1XAolQJIZCI/6JybxIFo3nIVMhmN64Z8a65gi7Kj98P7ept+EtbQ1TNAoKpaeTTVrCZg+4bfT'
        b'3KWr59oviCsHf160Z9x8aZF5nIlq9XhFckFST1FUXGCueVydoNbPVnrGfrzk2KJ2x9sBFQGXe38fMq83NCRvXU5dblylsefgVx63XTPlCz8Z2GKYtfvToO/S50uWGqmq'
        b'2t44+vbOzrB9lplnGyJbevess/5y0eUYyTaHnQ6TVYzzCnf7900ERoTDjd6y0D/QNzGQSeWD/RxwjBkIejWwYlHwEuzSsuzgVqiGZTcEN+nAvC7QYkY8HBDjngEbN2Nw'
        b'4f1MsAveBCdonvs0hlWljV/FQi2o3tU19MW9tskYXhgjENYwKNiRzdnK9MhcQUPTyWArODVi5eIEwz1MeGOKL331FGiDe/wTiT2KPQlJFvsY4DyUjid8sgdoI45MOsvZ'
        b'JtjAQJ26AnYIDF/maMTbUmMAoje5GaaUpXkFy/G5u3HUL7LF2ymNAQhTaPvGqLqohujq+GErF2le6xrZGoWPyjVMZRVeHfuVla1kndRbZcWXWyutPKtj1VwbdOM47ld2'
        b'LlIh5hnq2BKGJFRtxWs0rTNFnFSsLPuuc4DSOUAxR+UcPGQV8siQ4vIeGFHm1odSa1L3p6vNrA6l1KRIjeQRMsshM181100S1jipblJjdF20nD3IDZCL73ADquMJf6FH'
        b'dwzL7uO+sX8WmoOMxQr9/CDvYvIzagi26VGfJ5temfpgSIdRW99Y8/ebCgaiPuaNVD61iJFHLWLmMRahnbyA6mGhf2bon2EB8yyzS6MCraaISlbjC15tWmCUx9plpKU3'
        b'i9hogRvksXdReQZnOV0aareIQ0oNUamRXqkhKTVGpSZ6pUak1BSVmumVGpNSc1RqoVdqQkotUamVXqkpKbVGpeP0Ss1IKReV8vRKzUmpDSq11Su1IKV2qNRer9SSlDqg'
        b'Uke9Uis0Glj567TLaJE1ucO1ENHgfGvtmJxiHGQsskZ3YZW2MaLrzujOcRtcjAsEbh8bpgmLcTjI08BRWa8yZ86O5a+lL/FJirLRWbEEDHKcjTpOjLW0vJSiXfd12P66'
        b'ySJsgbHuYOG8Trbg6c7nk5UVF4oLhUWFG/NFJFfgqF4VFovEONwlyOS556JKhWXCtXy86qP4OHsb/sYXl/CFdBWz4xP4BYVF+b+QKUw3ILrDzTW9HENqLwDdpYSszV4I'
        b'unBSsMD5GrwScA5WBwQxqFkMw0ngALxRHorrgAeBxLR0XSa6pr0RHgHXsowqzEuzYHUaAbVGPGwu38gMPdVLo+1fBlfTLeANuG8EkR3sAQ1Ey1cMu8EefwxifqgQtqWk'
        b'YZouY24CNaCbOAoLK2Czf3JaUKBfMg7XCNlEcX1YsEkEaJ0vnzkuRQA7w5LRiQu7KdgPGotp56udFuB0CjixFFXNoJg5jFAuqCKHLjxisColKDktIAm9zLSEmbQcyopX'
        b'kcZw4ACXPlxqUuG+aeap6A4L2MqaMWEtDc/f4YcOKHAuEbXHQoSft/RkZS+AnaSp8WA7PEMr/cFpYTruCuhnboqAh8nDHuiEuZCSlOa3zQ3dwSTaTLAdHCmgW3V1q8tI'
        b'WoBk5pYI2OHGosevG5yArXOC4D597N1gdzorw2nYDnekwO2psFaTfMFYSGPkt2wLBBfBIbhPL7vCdBHtDC0BCtg8KkGCFQscBj02q2YRnfahrWzxZxpnuM9nz6Bod9c9'
        b'sNGBdh0Nhsfcc0AnYVWGs9nZUOP551jGxOp1ggJwBrXstF4yBNAAFcnaZAjgKrxJnp4WxTJzJ9E2K8xyKiIoMhFwNzwE9sKTOJeAXoYG1MJTxFduFbgQhnM04AwN4Abs'
        b'HsnSMABP070/BPeCZpymIc4yTZumgSMiDsiRsK9CL4uCHzw6ku2ATqNQC/fTTpXXoaISLxbEdYCdk8m8WUA5a6kh3F+4/sltStSMToP96pLT866lwxDeJa7P2mOnTq9N'
        b'XiyR2Dv4PZxwdmGAJFpsZGT8nnCFqPKtWYeDc/4UN5C+9p2h4szYPUu+/lfzDw+Smp58xTJI9PLg3lhbdayrNn6+Z+3E4afpZvZlwbZXpe9eXt//cZ5hlnLFf0I/yn06'
        b'pPJ923ELHFx6K/+j6pSCHGns+19V70mRhQenec/uqOLWrBn/93c2tnpOLLt2ou7tf1SW5u5rEpdusq18cG1W8K3u748GTY1tXC8eNr66fVZj5W8PL/qkLfaPKkXc8NXa'
        b'yPM3V334MPzMsrZb1blRh4/HOr+33u2Nv6a6f3n7g8GstX9bcez9qVF1lRX/6Iw8vXvr7/5G+b296JvI8E93XeVYvt/7nsvfLzAn9vaIdqe1uD5OF1bMqOvz7+8oa1/w'
        b'tyZVwd7JC9a13b8Q2aCeyt2Wdrks9N0y4U/pIassxdF3u25/vfu9e0++v9Mc8MWpp5zWmocyxcIa2RH08aVo8d5/v7ny/kPZv+HKsqGvF/+u8x8/fBI55a0rtaY2T7ZM'
        b'XHm/+y/fygZi+sAfXaTg3yVvTvIMbnz6FwNvy2kbvpSdGLdA4EgrQS9DBewDjck6Jo6AvdQTReZsd9uUVL8g+oppEXPVFHgqChwlrJ/rbD5Bbd0XDPcSU6ER3MfcYoqu'
        b'EgiLWnAuD2OhCLAdD3SKCJSLDdjLNgLV8BhBiwAyIFs7yt5XYaOH+OLHp7nTugp/jOcfiPb6dkwmiZixJ4VwmDHwCMZpDSZkEtNIUxETXC+Fx4IyiTq5DDGjjSngALiS'
        b'ocGC4U6kgWn3Z/DRczT9BMdhFwl5s4XH2VHwqgZOHJwCkuw0cAjsy8BklFXEmA/6lmsQNpZzbNgk5VgqBvJtZQAJ6AoiA5MtQrtxXwYmpOBcEaaFFqtYk0G1NXlxNhdc'
        b'IekJNLQUUVJwYi01bhILtG0AVTQ/358C2wlCBqanqAYLIKPGbWKB/iWghUaNUYC6KeT1WImM+z0Hs/t74DE0SrVkaNB4LUF3ILJKNqepNxPcnAvlYC9oJOPqB1oQEQqC'
        b'1SWZI8C9i4GMPLwVXl1CqsdksMSSEEJLY5a4ANRpRAZDeJHcYAykhAxxjJgOhT40FvFh2LYQTwpNhhAJYsIGahw8jb3Ab6HXEw/Aa1AKLqO7cL6YQOwBiIg+IhX9hY60'
        b'meI0qFmA3oApP+rTRUz9LeJYCSzDx/4UASVuBYf90wNfkJtlejnYAXYYWs+APeR1+WhBSvC4k5PYPQCfxRYrWVHrNQNq5otoHZk0om0KZi4GrdS4ySxwHf1XRW7JAvJ4'
        b'1N7EJPyBd4QtaKPGWbBAOyLIAwKL1+QOh42Do9zeNOw+lmI3Wml4QRzsjDgnDTTGbBat2CjLovVS8vghrkDt5CaJ1yh4XVonySZhGAxFhMopBBfTJTGyGIXXkFPwJ66+'
        b'g4IYleu0Qftpw06+Cp7KKQjrld0+cfUb9E9Quc4atJ+ldnGXj5ctkbAPmwy7BSiyenw7l6ncotFvM+wZ59Ph2+armKLymIRKLNXOfOyKJZ/XlIF+Gj/zc5gfqMjrXtW5'
        b'qmeDKihWxZ+BCs2H3YMU4u71nesHTFTBcSr3eFRoMWah2s2zdb1svcJI5RaKX3/PzRP/UTu4tNrL7OW+Kgd/CWeY66C248sTlHZ+X/gEqV085QmyZYr5PTM7lw46T1E7'
        b'e2AgAvwnUukc+I0h29dRym42e2BBCYIVG5S+kQMeSt+pd33jlL5xb8S9a63yTZGaD3sIeioGCpWTEoc8kqSGav/QHoHSP1pqOGTvq/ad0JODnpMaNpurAyIH3JUB5IJA'
        b'7RfS46D0mzIQq/SLQVct1SGTpOxWM5nZR/aBv9w0vZ9RSucg/HcykkK/MTfUtNiKsnFoTK1LvcsLU/IwYnKwMjx5iJeiDkAzjS8M8QT33L3JwDm5tU6WTZYnq5yCJUbD'
        b'XCc8QolKu4AvBCFqF295gdIlULF+wKBz26DzNLWzl3w+ehP+u1DpHIzGyA+/EfsZCkJRl3ynDMxQ+k676ztT6Tvzjdx3Q1W+afQYrX/DWDkpecgjBY9ReE+S0j/ml8Yo'
        b'rCdS6Td1QKj0m07GKCwSjZGFzOIj++CXaZz+70VK5xD8NxsNFxomTaPJMKXXpd/lRSh5ET3ZAyXKCelDvAyM3yDoFKChQheHeD5qPFRHLPTkczMa1+DSr8I10Kj3n3Wc'
        b'Gns3H9Yq+bEAn5+FBfjH1KtJ8SLMMMo4AqrTNIL16xPR/+dnMsHrmq3Npv0QNXskB/1TDyyPaWU4HQ7CqLzZZSeoX5mnfhed/dtwuahwZXF+3ku38TFu4z8Zo9pIGlhS'
        b'wMdVCcXlZa8vuTp7eU5Yzku37QluW4du/HwTioQr+YUF/EIxvxAn4J4RNkM3nq+lhWU47/NLN+/p6OY5k2TpZfl5heKSMn5h3mtq0ufsV2jSj7hJ53VNctU0SYjzh/Nf'
        b'zzhpFprx8rUleYUFha+w1HDGwjI33VLzwY0rEorEfLqm3NfZygJtK/PX5+eWi1+hlazRrfTStZKu6fU1cZV2xxLQkpdvIMd01I710+4KsR51QduDrvW1jaTh8rz8HLSw'
        b'X7qZxqOb6UYIC6mCL8zNJXnrX9cQGi/XbruXbp3Z6Fl2H7V3X1v7dKtQq4l+6fZZjm6ft74qD0+0Vo83uo36rx+d/xj7BTOrWRpPW4pJ1eg0llsYRINJ6WkwGXq6Smor'
        b'Q6PBfKb0VTxtOS/wA/7fSKn9NPs5XSf+H9k2lavy0WiWoSFFO0Zv85ShrV6GjmcxHy2H4hLx8+rS51SmY+bqbrz/NwbJ1c1PqGr6zeT//KjN1q3L1f3RLk2u7i3cxVrB'
        b'G+7hJY/I3cHg3Bh5oS9ioCc37bLRtXfEm7ZgZb54VNru1dkMypmA/g3y/F4xUfRLvY1rqpcyOjf7V6WMfhkDPVXN+B8x0L/EOkZTam90iU1is9KvCkf8KwoneLLsxWG3'
        b'w9+Y7l1ykrXSlMr7B/sLT2c0uUTtcxD0m47oVW4mjEwvkMJbP2/CL7vyi6Mv0sz1OEoj8aK59vFXTDi5RhJ/JGOULZ9MtgnjJW35L/VqR1M96/46PPEOr2rdFzCJdt6p'
        b'YE0KDgCk2JZ5sIkBOvJBNa3t3h0C96b4p+NL4RPSGaAPnIfHC99aXm4gwsBCUWuSsPP99oa2ndEywYHQ3b27T9q++9cV6bnJQuYFhzX2q+0zpV+HGISXXqaoN9uNcy7G'
        b'alf/WMIJnvCRQfgKfWy0fm4QyIi70COuZhs9XpHNYFv7f2vBsA67x/dS5CntwgetwkfttLGG/KXeNU47xOhd3wrxEBv/t9Kxj95bbEKB6VzWlMZ94vXS4ZWIDqc9R0Tj'
        b'sMe/iGZeENUdbeQS8UXiwqIifoWwqDDvF+xVz7vScNKzEoi5oHXpRsqIQRmlmPEr7J0MGYU/3BMwRGXoisdMCe374I0oMi98fhgzXxqSX7u+6n5A9lsO/rKqsKLs3943'
        b'qBXdG9o+s31Hr3RvHePaj5fMUs1afjvBrCW1q+3CTKUjc4LZwk+kfgtguTis4OH9o91Cxf2cFe/eh1l1oPkfzHUrvT0RNbDZab9I2ScwIjq8WAvQ7E/0ZctW0DpkC3CZ'
        b'NasYdhOd3FRwGG7316puwTnYRpu44OHxtAqwGVybmaJVcYKTJGS3n7nJIY7Wku6H1fCg1gS2ZxwhNcQGBq4JSQXZ4GYebZQCx1IDtVYp0AgvE/3uHHAyQ5OBHWyHh3AW'
        b'9kngMA0+7QMG/GFNRhI4y6Y4RUzYLvKAl6LItTzQLExBFwI46LnT8IIzA1yAskSBwYt1ANiHRs+LwahQtJzM9gg/pC0he62SXv8PZixkUPbOjVvqt6idiM/spvpN8ryO'
        b'NSfWqJ2wv2Lj1vqtCq/uwDOB6Pc9nn1jWl3aHV6IPKtjcdtiCWOYi10Z7Ie4ftg1lSPjNBlJYrETbXJdckOqPFTJ87rL9VNy/RRZd7ihdJWj3BLGOC/H9ErQ89Aoc+bo'
        b's3nabrnpHZlPNr3ykYkppyZxMfcXsBixK0XZl3iUWUgELxOQmw3woGvluI+NtLLSxxxaePiYQzPsHxtpWeOPjbScLCFUpFcC8/++chc7ko4Bkvg+duXQ2vkPYSWQrRYf'
        b'kWlu9YiD8RHDZWKp35C59xPmQob5+EcU/vyGRVmMf0AKHlYwtfCCkzG8YBRBF7R1HbYS0CW2UdUJI6CEGG+QO51BUAk1RWG4KIKUaPAGIzDe4ESCN6iBKZyKYQqnEZRC'
        b'TUkULokmJZqXYZxE2xkM8jZN0QRcNImUaB7DgIv2kfoVTcElU6sTvzUyMY94aEs5uCvtg9siT05Bf6qTnrCtzJ0fUOiDRi3EnOQqv42wT2dZh22gzgQcZIJroBvuGEU1'
        b'x2n+fhOFttcRxzH8WDjonwP6R51lar020CHBreYhBuxX+65gtwokiBjvMtJ4rNgTrw9dbcTrw2jk/WdNdB40+IgyRW9n55nqvd14zHsNkEBhpneXyageOZw117Yoz4HU'
        b'yiX1Wu4y1j1hqnuC0j6FfXo0/xzOWnVx6DuN0X95jtUMgvdIu4uYV1tUW1VbV4+r5lU7FJjnWevVaza6JZp/RuifcQHr7LguTZBnnhPxFzIgLiim1WaoRkvcymqbattq'
        b'u2p7VK9VHlevXvPn6tXUiVt8lqdXr4GmRktSmx2qyTjPRq8mC70RtR0ZUTRCzDw7vTG13GCBhFznjy00exT9Ea7ML/siAj0y6sSO5Y++Ax/z6K+IL0QnvP65j91dhGK+'
        b'sAyrSNeVFyLCM6qiAiSQkfvz0KVcMVYpFIr54jJhsUiYi7Uzome8YpLEiI8oKdO8SvcWoUgnQyMGpJgv5K8srMgv1lRbUrbhmWqCgviVwrLiwuKVUVHPu91g8fyZDur4'
        b'lxkzs2KD+PElxT5ifrkon/SgtKwkr5w01320cxKTVqdjXK1Rsb46b1OsaaAdXvfSMj2O9cW+SQa6CF+D1xnh+8WiZ6eSDOoz7klapm2ttvO/ykNJN/ZYLkcLQH/CxhTA'
        b'8Sohk5sXxE8ieuG8EtQiJLDz89cXisS4pBLPQY5GDZo/BiOpaZBG6UO36TlVUGUhbiS6UlCOqhPm5aEF9YI2Feehf3xhaWlJYTF6ob5K+Be4WA71LBdrnl6OEZtNYjA6'
        b'pDYHVcqCRJ09FtbDA6lzEkEnxqsMnpuYmq7NCgFuwb2m8DSsA4dIHqsJNvFjV4EeShLYgmvEkagC7jXeAutEtB/RRcf5sAEJXYlsysAHtoMrDCiF1+1orL4GsBdeoIGp'
        b'XBjrM8Bu4ojjBm+ZZAbCdngBng6jWEGUZTTT1MILDoCWcpx/ohz2RpGkxbqgauxMNntu4HymAeynJgkMQN0MA4I/uAFczcCg0CLKwFYED60m7LxTFDPsX7T3T5GtsyNF'
        b'+gZ7DWB9ykiPYHXqHJwhJAA058CDaXQyjTklhrAKVMMugmpXAW+CW6J1Bq5FFE4YDmo3GhU6OXsZiJhovc94fKnpN1FIMojEkoGoMQSqBfu7HNzPjk+Qr7ZlnpFJsvoK'
        b'eoVnPrz/Fu9veTv/8tcc2LbPqek8708fpVpVBLIstlz/V5F/BfOv99/p2FGHNQSn97jvNihoEGC/6dyj/PbzvPl/b1toILYD13khu2S335Xc3QH/CKQ5E0pFtd9LQPO5'
        b'BvPhg+MTFE3Dyk8Cagvvr5auvb/+K691758urfJaIxvcsnuq119lFz5wsK+VqEx95m4U/i3v0N53FpizQp9I3jH8sjyMteHfRsuOMtv/svA30hzBkpBvtj/dveLEEbPf'
        b'mO0xe3v/H1P3m9VNvxsW9li9IGRW2OHwnOqOGW9FhlNza+MiPjsu4JI0OnDv5GRjcYrOJW68DVFn5GKwV50XC/ZNARfhWdqNZS6QatKGg+OlKangyMYRHzXY4QOOEaif'
        b'ZXy4yz8d9ug514RuJs9lAhlsSEnNBtf1HGzgqYUTaAeL1vAguA/UGo6CHdq2gQ4TPBWVkoL9EDeCvoAgAYcy5jFBG2yEB+gwzRbYsxzuQ5xROl4ofoh9BBdZoAmembNk'
        b'HF17EzwNdvsHw1rMOXGAwhHuYQZYu5LapwPZeOLZcy5cAwJAPHtMYD9xqTEKga3+22BDchoaK7Y7A7QUz6Urvey8xX8kXLIQHGaGw71olPj44o6CCH86RzSsIYnhAznB'
        b'sJuyA5fZiZNgC6khBHX2tNa7guJwBf5McyiHMrqGdtAThvO5pIBDGaWwQdM2a9DIAoeWgp30yLSZkaQvI+TBIpMl2pbmwqKDOuUFfLhvIujV9xcU09ltwJHZk0Zlt/FD'
        b'8qg9n70MUZxeOm3R+SXYGSgY1Q1qMnDiLHiQM2c8ZYsqugXOFgiMXloOwPuar7EJ6xmE7UafraO9PBYyaKkwHZ1U9m5YFvzE0WvQO0HlOGuQN0tt59q4rX4bKZqmcpw+'
        b'yJuutnNorKyrbNxWt00uVtkFSNhav49oWbSCrVipcpooMdLetbVuqzxvyA5x4raNKXUpcvYQz3vYwUW6SsFSOQQ8oBg2Mxg9TLW9Y6uRzGjQPaxnQf/i3sVK9+lD9rFP'
        b'WPgqfc89B6dWO5ldq6vMVWE05BBKWjR5IEKpbdYXoyqdjit15beulK1sKmwtkZWoXIPvukYpXaNUrtEDc5Su06QsXP10xj3UQxzCl3vHTkAcVqapXKcP2k9Xu7hjnxS1'
        b'u4C4OPB9sDOJ2kPQEdAWcNcjUukROeCl8pgmYR+xfOIw0s6nT0xwrXQbnoqIL5yz28wYFpwYkmDCejvGIMHQ8LaJQQJXE+1npOcGgPmWF7vqE6o9ylf/Z2d3mqleaN+m'
        b'hUg4dketYri/ioT8MfUr7eka05LBz5ptnm251nqzwnSU4T9cx+Y8z9fo8TCvyROAWI1PMF9sNX5Rq3NN9Y3HZWzOM2EP/3sWpefiIf8fsighnrisl/nM0Ixp/Dn1Z8gk'
        b'xp/GY583/WYyMf1Af2L8aWdQU1TMLyfPEzBol89aFuyjSehKRDN1VFRDQ2/YvcgCNP6ZuRTlFi0nOCo/Ywhasvi/aQh6yZeu1LcHpSz+/5096Dl8ozHtQfHvzjcg9qAj'
        b'8f812h703TmtRUhrD2r6Fs03n8LJ+NaAdnq+7f2ene5K2P0yBqGXmYVn7UI5i1+nXeglW1Cmbx4SLv6V5iESu3DFYSa8Do9obUQM0OEYTq6UAjmsB+2mWhMRA/RFFRWu'
        b'fnKTScxD51TLteah541Di36rZx5CO/PNauP4r6++vHnoKh4L+xeNxbNWosTFDGNr/29t/1tWop9/ZYG+sShp8a8xFiF6gzXGo/afTgexiqJtRpooKU41o9pQp4FgjtJA'
        b'vIY9+LT9Oal5Vr6YL9SemvraoxfrG9aW5RfQsv1zHnhjqATK8sXlZcWiKH4sP4rEkEWt0Az2Cn5Jzur83DE8An7BIGWQTiKiFsNdxUQGwdrZebMXBG5aO3/BmIFUoCrC'
        b'eHXwovIQimSuPAsvpjwj9hMRl5Zv5fAylnHnmhpiqXegcO1njgYizCD8YekpLMpiqnSl4XRDIBJozxbsGLxk1nJW/VWfNPTt1fbzw2dkv73Z+2yIknc7/ajfRM7AEq7n'
        b'4LLxuz5edNvxdsDEVFXVP++/kRNse2T4T2Z/jzeb+Yn3J6VOMquKj0I4ZMOs7OQ2YVQWWtzpzEjSxkzAZtCPRTtQC/YROWQJ3AGO0uERcP8sWKUVohLtiSs5ewI8Nkqs'
        b'RCLlwS0kOKIDtBAxyw9sn0PLox7gLBZJ4ZVSUrWBHZCkaOSbkM1IwjFdxITnEZVtJxBqG0Ngpzam4iRofi6PLi/hVUJv9aBeTHGkqWZNbXR8ZkvqXSN0YJWGDm9EdNje'
        b'Sx6v8MI+tiq7CIy9MVreIPLBjDeylN5JKsfkQV7ysKO73KspUGKo5jo2TqmbIveiOXmcv/AON4xgs01VOcYM8mKQ0CPR99TVsOjEBvTzdisjasQrlyY1c7Hh6mf6Vanl'
        b'0rFv7hpMbOwfvKJvblnxC4/6HIpm5zTx/ZSG3Xztjh9PL41JZMTPO62VFGhjKf/naU4s/c6XpDljsieipzOYImzt27iikoYnFOBIf3HY+T21vw8bCskLFZ4xmigouFfE'
        b'oH6fZiD/m5GASXQ8M0E9aCNAI3RwSHoBMSc5whb2Rg/QR/Z6IjwqSNFE0tgv1wQoQtmKsdkX3ellz3zBktKMMdkq7vRWebBoCYNycrvr6Kd09FNEqBxD0AZAEi/aJoNW'
        b'3vr4gy9c4zQC4QgP+0uv36vHr3ybsuRVw8UjcGuYdOy6oUhYkb9cKEofpczX6XlJpjC2TplPH6RGSKyiCjj/A+r8XQLmFzljqfO1Sx1bRPI06eheaqHH6qw3+WIh9osV'
        b'0t5za0sq0MmMU/Zp631du4R+RjOsUVjrT+w2AVjVv7ZcJMaqfnrXisSFxbRLMRa9x9TV0+L4KH9KbLZBlY9lJ9BtUNzWMmElPVyoz6+s1jdJLw9D37OyV49iBcZgBMBF'
        b'Gx0vYAGqSc4UDlCU+eP45UTKNQMeCVhAYBcvvv0uwWssZf/oQbFlDPHJRqIwL5qCwSbVFubTV5g95WVQWbShmGRlOQ9qvPwzUE1zKXA0Hh5bAU8WLh9uoURv4dYlm67N'
        b'iDUBIVbNn0YU7lNUdt9nRf9rXIbBocjE4kWxAuMd/VULHlr/eCptDe9jr13mfX194cHfcuDKZU/vrNi4yPXMzt9lbvFsl85Mgd1Nf162JC9+woZh339vtPzrd36mH6x7'
        b'x+JggCz6i/uLXdbscvIxqpz4x8Pduz/0+PoN4YfG/r8NePOw8hB3kWyDR1rH6V7QunK4tr3yy33fjD/1YPeHswRHjb0POu5aZ/H+D/851zszbcH4LJfk9ceLT4Ajt9ff'
        b's2h59C/G3olBXw9aayBE4A4nR704TvlUcL4IdNDeMpfhAXhay5IkGZSDXTRLAi8hnoVE5F1atPhZpmQve0Ww0bJ1dMxjkzM4769V+8L6ctACuqCcfvYIqIV9/n60hpfh'
        b'C29QxlOYoNUYKgiR9VkMqp9V/xLdrwOUJM6NoOvYBXbCa/pwIYz1QAZ6wYnVpHPOoNYGq6w3wt0arTUzIGGWwORXuGFgRGG8fPWh7Aw1SBobbcegmKicEOtPaWL9cP2S'
        b'X8HX2GA8O7bKxhvxDdbeinEabWxTpCT+CQuVPODgrNaLZYsVDj2xKpeJdSYStiQP+/noaXDtHBvX162Xs+Vz5HPlRio7AUEzk+bVbZKwh7mOWGO7Et1LK1d9dApbOa/Z'
        b'AqtRfe7ZOUlMJWKJ6RMb/ErckqdPrLQXaD3om4bWcUYs4DcujseCRgZx1oaQZxDnqtGDGusdQNmcX+S0CN7waFYrD7NaLxjmen1lqBAfSu4PX1UZihGkkaRPlLTkeDLW'
        b'RfjQ7jwuHIy3UiQsXplrqEfAuFoCdhCfV+b0ebWXtZe912AvB51b2OMBYy+ZEa8Hy2ordJJhzwcuOsl4SEDEeTBtCrjkRDNEJ5qp7kQzIieaod6JZqR3dhluNdKcaM+U'
        b'jjrRtrLHONFi8/JwhFBxfuVor0JsnaUtwbThOrekrCxfVFpSnFdYvPJn0DHQORMlFIvLolbopOwV5KzAJ2cJf8WKrLLy/BUrAjSxSRX5ZcSnijgzPFeZ8IXOC/xcYTE+'
        b'wcpKsB+W1tlfLCxDq4CfIyxe8+JjdJT9+hmedUzr9QsP1587kPFAYPO6qDQ/l/QwgB7lMY/XkRi34vK1OfllL22L1y1LuhkjcWiVqwpzV40650mPioVr88dsQQkdFqMd'
        b'h1UlRXloS+lxDc8EzawVlq15xuFEN2kiPh1aF8TPwDEDlYUiugWI9VlVksePKigvzkXLA92jFY1WjFmRtvW5wqIiNMc5+QUlGiZEh1pDL4JyHL+DvUWEY9ajv4ZeOJI6'
        b'B+Io/rPRcyMxDtr3vijWQVNXTljO87Xox+D9wvOYriCOLTODPzE8MjCU/C5HNA5twrx87VRp60JLn14lY4dexOcXCMuLxCLtFtHVNeaM+4j45Cf26nmucaPYOs3KxF0p'
        b'RSIY+vYSTOkobk9HLHXcnm86UVEmgwuLRWFliNsqAU0TKNAPGuE5GnqkevEW04p1DIqBOQFwmoLNiC3ZKWCQq2vhMTv/dHiQQTHBQSSUHWfEwQ4oKZ+IrsWCBrADPTqH'
        b'Zhl9gwJ9YXWwX1LanETsDlIKL4jnE98KCrSC8/ZTjMGp5aCqPBk9ajpvvmkFvIxuJLrn+b7wIDwY4JuYBnrngv5tuMIF5HlcE8kNVD/TBBxPBwe3moAzcDc1Gd40R1xJ'
        b'L6M8EFW3EPThREJ6Dia0XEi8S5IDg5aAsxwqd5kRaIOXadS7No4ZhqvzrRKvLhJMs6PKfTAz1ehoiBkxnXsI7QYdIIDn1wYmG1BT/TnwWB6NgAP2waOwyh/Wc9BpDRUz'
        b'KXA8BRwmdafmYeBzykqSXBYwnmNFI+pZLMGY6RS/lC0066QEdOGbU5lE20CtLikyC9pM0RkVzwBFCjzpEYNOSlMMYgwGCFQweWKjszGFTvAQSVpO6k8uNlQ5PpXjOaCB'
        b'wBVlJpLsTUmo+fv9MSePupI9h+4MHuqA5NSgpEA/DgX3CczWVYCGciwvToXbF+hEgWJwUysN7BcgvhJ0ZmmUggIOheTrK8bgJDjvlyAwIihCUOKZqof0Ay6AWgZoAsfh'
        b'EcLkb4XXlqRooH6i4DVGMDyUS6+6W7APw1VrwX5cYhjghA+DQA8VFQWlWMPdo+F+bOCJqeRqJTwNukdwdjzgDQy1cwOcoXM0NqDFW+OvQ7lAS0KDtQMVsJPMXCTYHeav'
        b'AbgwDs0AA0wgdQgox0BrYEcUw38s5AqMs7N6dgHs4whMSSXe4JStDiEKNsFmBuiyMyQN3GYH63QO9Nh53hZeZm4CBzfRWEHX5pToIURRXB94ei52jz+7jlS8BFwB1Ska'
        b'hChQDa5QsD+9kOzhEnjcUOsNA/YKGaGwFjQSXymXMngqZSvs08OJgjJ4PZDO7zkAzxSP4ESlpiFevkGDFAVvrSatigQdcEeKFtoE7knWeOV3gp10q6Wg31Hn9Y89/sGB'
        b'INSpS3A37fULrsPrIxpizzUa4CFwCwzQmZB7vEu0yhqsqgE7QTUTbF8XR1YDPDAJ1GRCyTz8vSUD3KCKwRXYR7Cd/suZ3jjUcnHqJZdQGlqyHPRjtH3YkMGmmGaw1p+C'
        b't+BZZ4EJ6XE86Jkqsigrh71msNcS1EYHwn4xGurVLAyR3k/wntYW2+rfAvtF8GI51jC1s+LBQdQIb+IxBi/A7jT9GyvF64zLzC04OBDioi+LDXfAnWKy9CY6gz2wrxxe'
        b'FK0zWwcOWIKr68rKWRTXmTXJABwoD8C1HbYuEa0rNyE1WcJLxrAXvdUMnF+AHtA2YdoyjgGU+JM6y52m6e5H12fAS+QWbj4rFt40o9fsTnhom+4mXfNcwXnYDGTs8WBn'
        b'GgGhslk8T68qcYRJGbyIWjeTFQWkRTR8VM2KLM0t82eiqhD95VBWHCY8vyyNvuFEJrhhCi+LUVPMjM3LDCjzrWDAkAn6NjNInl1EEo+Cvsw0WJeJBvpIJjhgEIMTIRxj'
        b'wMvgLLhOR1PdWA0GMmfPxl93zoRHKCGipZfIMhNbmT5bfRW8hepfn02mPVIM94vgZUt0iQnbQcMqhh88AbsIFQNH4E7QCfdhTM3gtNQ5ERnz8OEzV6PPCMA0fX9SKqxF'
        b'YirYMc9YNAH0a5DHcFLjFJwOjxEF9/lgqJxd8BZZSdNBHaIofYmIJqQEou2TzqasQbP5ZhY4it52iZDk2xmOOGO7ERVbsVkwfT1Np98R+1NZqHB6Qs6M62ZJFJ3TlPrX'
        b'NM0X3+kCNvFknDEdHAddUQDHSWygNpSjA5LkaObBetA1HV5Fx8NGaiPsBRfofLiHQTNs9/dfRlwf16MzmfYoLECTup+I6bfQr0Kq0NOaCIaF35XdYopmsCjq0YWzLfM/'
        b'XcONtfr8xuZlQY0XG7cu/cOaY+0zZ87028oTeFR7VO/gCWJ5u2aW/lBhfPnwlKGbawV37B62/aOp5C99Px3Ztj34w5bKxjUV3w0ckywJ+6bp+w9++88PP3zye0uPo5F1'
        b'y4uXZy9p+GPMw8Rtc3xyjjbmBaoP5/9FcrDo0zUrCt+1P/T7P1T/3rV8QrL9pyd/vNfZYrdnDvtHJ1Z4woUTs75737PbMCvgUfvf6448WHXnckT1+hm3Hx/gLY98e+j7'
        b'qJPWocFRvfvnVfATJh3obn/wYePnVa27HBcn7trY/PnS+5mHHhU6hO8/vnli3Mqu8pu2b/2t8KxtVf0RdLAbxIi+dCz4e8d/HhoM9y2ovrT9HwUPTn0Se6Hr0Bmz6ok7'
        b'QjYYPux+u8Lu79f+6iy0afyX4/2aR/6ru+oqbW9+eanqJ/OA879zDM8WxfROEe9i2TTbpgcMX5l2mTs+YQpDEg62bym1qfHN+W6fxPDE13frPqntLemvy2nmfagelt6f'
        b'ZH37z39p5LdbNF/zVqyr+Xyu5/dXF9m1LPD4+ISBw2cJYQM782b/5pHs3O5vL/BS361ZwK/7Z/v0z94/8Mm7BzZLnK7InL4PmfSoLiD3nMrvs9CHTdSp7KUBFzm2x7p3'
        b'/6mgbUP2GenwUOcXjd90Ny9/bzm30n3ad7vCVF3Ng307lm9Xnb8QX9x0yn/BN//lt6LpuzNFty22tdrs+Dw2NK7gcXpKtnjzgRmHNv7m5H9+96V3unimUtngZH3V/OrB'
        b'wdi/Zt04adW5IylDGtTbcPI/E953LPrnxT/djX/nUttP0QnZ/1BPyzJtr+pJn3DZat5Wj7907Yn4IOBpuRA+zv3G58Ln6n8O2n53r7A+bWr2voyhTxPL189S57q4fsCL'
        b'ylt7/N+GjbePWnhf6dlZ8vnj356NfGvSBGb1ysSINW41C35IujXngfDB12EgfGFTYN/tHvvvV1P/3L2fa/G3qj95A6XxeLvL4OrXXXDVxN2LP7jXbXWZ09XRcdyqf3fv'
        b'0unXE6yu/PChQcYfElP/OJRV+zvG1Lf8ZKx/t4O/mud8tP/c06OuPTc+ALusb/3u/p7qlsA73jtXn13sXVxX7xoZ5PLjsPem3a7Dp5deSH8qXmD6Fe+zd94+uby34EFQ'
        b'/vD8+fwpdhup44cu58b8CJdLF9lkxf9bEEqjlO1Cp1qN/yiHQ2pcUjnoYQG51RpiKITXVxZo+R5wZBwj2ApeofVptZ68lFXgBDZtZJAbTOcwMc8Kj9LOkHXw8gY9hioU'
        b'8UVNczMeB1NY17YPohMGc8S9cD/OcwEPpCEmIglK16St06gHU0CXIegBp+EAaaxxJOhNoRsJDtIvtIZ7PeF5FtgPavJI8HcpOOil0TE6g1t6akaj2RWaAGJ4EV73h/ts'
        b'MwIQhcFZPQwpU3iTCfEpvIt4zqbAmxUpfLg3Vd/hFm4HN4ht1Z9y0nqJjriI+sFmFjgEz2WRnmfC42C/VpMJDoGLDNBiAI4TLaMTOBKn9WIN9iZpP4JBB3FmWe0NzuiU'
        b'mEBioq/HTIQ7A2kP1LqSKD0wZdAFLmA05Vi4l1iS5kWDnf7paCg5FDsCiT+HGOgguQTpd6dYZWh9csGZIqLgBLdWk4FD7Fk92K2vHEUsWycDa0eXkD6FTAAtKdo8Jjlb'
        b'cCYTNJZVNMafHLQlpvijY3p/Coda5sfZwPRCbOBuOgrTGuwayelC8rlshPuYW0PQMsIVz0Nsh1ynVC6De7CdW25N+zBDKTydouPZjXnztjJBG9glohXGvaBqEs4sFmyI'
        b'RLoTUM5lzAMH0x7TKaDZaZrYS/Z6eJaBxDZJEb3mj8GdvnBfAGKp8fKrTQtA7FQwOO3KgkdAfQE9GhLEeg+kwL6oEUdfYgafDXrptb0XKDBiNs3BwnOpjFC0Ti/Thvv+'
        b'jLARaQAxgUgcQLzXdqIm34C+daTAFrT2R8sE6MzvJ5OUY182IhLMRlIquBoI28hwmNix9MSBm1pxYHE4eW9speuILIB6eQkJA2h0ZI8xCn6ws/ELpQHYCi8UwHOzyfrK'
        b'hZfLcTU0ZuJG0IReAqtYJWVbSetKF2D9fk1wRiATLUUoRWvPL3vtY1/toNXBvhx0jus4x3XwkjnsYYSBHYwAeMLAeDYiDiT29pbb5hTd+BvBY7DVjokO/p6ptB9fG1re'
        b'Ug2gOKgJTgpHXPY5XwbllMAGLaDfhd4Ljc4OBLJ8AtohlCFsA33wONMI3Ch/TKRPuc8KtD/qwQ2a85gBzpPZ3SDO0gD7aRI/cJHgd42FyMo5A7JETMGhcfQdQUjCSAY9'
        b'C9OC0KuhlA2a3aCETGQZ7BKSezIC0sEAYqjQxDApuwnsaVDq/xjz2w6gByroatIDE8F+vLFS8A7whq0G4AyoX4HYtV5N4qMysDcFSf7XcJNq6akxBQeYsK2QRSY3MhgJ'
        b'rNi4UhOABn47g5POdEY9qyYkCV6H/UgKHfHIXwrqaKf8OVbwAtmFBrAxBPaBjmmWFRqqaAw7meAcqInSJESGLcvQfAQKfPH6WQnOipnggpW9wPP1wA7+r32IsCDxrGKp'
        b'6vn/aZxOhHl5L3Q60btGjDMFmuy/8csI+HtMfYza0b3VX+YviRt2cn3AZDm4qz18OgLbAnsM+816zVQeU6U42tXeSe3m1bpNtk0hGuBedXnD5k5kxrve0m1DbnM+8QgY'
        b'DEwbnJ2pDMxUeWQNOmfds3fFsHSDPlmDC5bdXZCrRP/3yR2yz9N3wNe6p3CdB7m+nZk9Dl3LBoR3AqfRvvAqx8hBXqSaayeJHnZwl3t1BLUF9XipHCY9oAxtggbC1HSu'
        b'1KYNuE0qt5C7blOUblNUblOl7GF3L3mWwr1twUlnKWfYw7stV+GlWNfpc7KoZ45y/ESVx6S7HlOVHlMHClQeM6Vs6RyZITYA4bREjGYTnS2ow6HNQRFx0m3IPlRTNnJx'
        b'HL540mnIPvCJJWrOAyvK2RWbqeQRCobCXR6pcgqUxN/j2smmyMUqp4A73ADSq1kqx8RBXuKwnedoqxjXhkDgx9TFyL2GuD7PWcXUtq6NRXVFDcUS1j1nvtrV547rDEVc'
        b'd2JnYlfy3YDpyoDpqoAZd1yT38hTu/upnVwxhGG0LPquk7/SyV/t5tG6RbalaZua79lh3mZ+0lLN91K7et7je+E8uXf5oUp+KEaL3CzbfNctWOkWrB51xdOnI7ot+q7n'
        b'JKXnpNFXvHxxaqG7XpFKr0i1x3jaA2mC0mOCWhDY7dzpfFcQpxTEPbQ2drd9YEu5++JH1W7jWzfJNqn5PuSXp1/HtLZp2l9e/ne9IpReETgwAc23WhByVxCjFMSgKtxs'
        b'Hwpc7cdJ2A9iKHfvkUZIzNEawckD7nID73AD1SEReNXeDUlWhSS/lzbotUiSNuzpo2B3m3Wa3fWNVvpGqzynDlrx1RGT+1N7U+9GJKoiEgeTFw0uXnonedmgz3J0TT5O'
        b'aeU17O4tX9lR0laicp8osVCHRfYH9wW/ETM4N+tO3LxB7/kSC2mZ0srjnnZ4wpWe4WrvMLVvQLdxp/Fg2AyVbxwaO3VA+N2AWGVA7J2AOW8seGfJm0twn9ET2vy8Fqrx'
        b'07RFqNv+bf53PCb22KjdPR/amNqOkzAf2lM8F3X4xP7o3ug3TD4KT3lv4eD4BZIZkk11GcO2jg0FEpbazrF+i7T8jl2QgoMtnHZ4AUTJopqiJfFqO6chz4ieLKVnlNIu'
        b'isSEJLzLUwrSVK7pg/bp95w8SKQLU2E96OR/1ylU6RSqcgp/9jm0PqTsT+x8FTwleolYSRtzSYKohs34q4dEjANPlHa+8rnoAxXZO7VayiwVbMWagbCBMpX9DImB2orb'
        b'aFJnIo2Qhym43TadNj3jOh17RAN5EpMhqzh81bzOXJovj5WtGrLywb8t6yzl7CErb/zdos5CKqZXaYjSLWTIKhSV3rVyV1oh+oDvt7VvXFm3srGkrkSep7L1x+NCm5u3'
        b'1G2RZw7ZCR4w2TYeeA+bykzlcUP2vjgpOY9u0pAVhnaQmP7r8QIWxQ/HSZvdP3bm48zM7k+f2KNd/hBTnh8eVzApZ89HFBPVRNMgvLsUmUNuoWpn94fo2bAHLHTxqQj7'
        b'arY4ZftQ0GBGTPYklpplvZBNqX2MsyNY6nAG/pxksJBhOMz2XhjAGvZnoE/aemxLW491ttmyfGxC1lllywp+0aL8ascNyYZI/++Zc4a2RbeM5fand7Kcw/boGejOn6qo'
        b'JwuWMhiMGYwnFP78jny+CjQnNoUrOJOpAdNYFkvA+thI64M0glqRy6ZG/qczsVSjjyNWWns08aAy1FijTTXWaCaxR2NrNEVi50cs0WwmVaOzK28xMB7lOYW+G+jZnNlb'
        b'DTSW6GdK9UNWvshkjmGJnleqifMZbYgmJlmhxqSoc7p6sXlXe8fomGmxxjqqV0WAxkiaKywe03KWg43gfJKVGlu5Xmzy/jXWYGxfH/Otftrm+fFJXDQx3GnbQZth6SZh'
        b'mzpqejFt+hzbEsuPK8nLD4/k5wjLiOmQ7nBZfmlZviif1P1qzmRkADWG82ehT8eyeKPqx8aD09hTtdZkbMD9JYPjq5oXjahnzYtu6eWTsYQDz8GLKbAmI4hWScx5zqEM'
        b'ni8YcS4/KDAmxo0DxCt9OeyeojW7UfAGMVZhpzRYnZGpM8Fh+9tG2GEMDhgvIBrPxSlA5p/MhN1p2BcNHomGR4nmNbACp0KmjO7ZlqW6+i2iI49++PwBnQqZOZ/B4FOz'
        b'U8oTKAx81Asa/YECuz9Vw0OZ2GCWlkpEjgUsqMBKhVS/5ABwJmssJTJrnjlsB1IBaY3PbEckne4CtxgUlUalIaGsmUaA+srvKWXFpNbPm7Qi337Sl0a0/lctm04nSbYU'
        b'L6Iw7uvZvKrV/8rpKKQvJ5yYTq6uSFrDGGJSVpRH0aY54UW0fdARSvLDoQQeR5MQRoUhQXR7eRyFTRVgb4C+ERRWByanwYY5iaBjMRGck+Zos6BgFc6cxOSAZIIEj6Rv'
        b'eMg82T2UKNLhZfvlP+8ZuAT06kUJIAmsUcAg5gqneeCIfnpAWDOLZAjE2QEbVxBtezZsXYOtYyklOvsYc1O5bTkOlAGy8Njn3qy1QuKVMBNU00+B7eCm8RbQkE+G6TyT'
        b'RcyoktCVZpty/TTK9umr6UH8KWMBdZGiJt+eVbVRuj7FrKwGB4viKwIDooKP5IILoGtRCkU08LAZHqTtsL1wOzgPumY70ZIwuGJEPCBXYQHQP4JHa+CNgYJGJDhjDo7D'
        b'fRgHCavf/cApYh8FVbB7HRb+sXaeQ7EnMmBXKsbCsactKkfgdcsUeDF8BOOeNpxtBcdp48QJKAHH9JKibOCAEw65hVMerGOKjBDJr+ccPNCQVjIUYrXnH5M/Hz7k9Qfx'
        b'tU/bjeYZWflYfDL5keXkefdXbf8q2bk+eWZX7/z7f7IxDKp2q3P9fvv+vvKYUt+iU2lhG/7UcvfLh4c+yjjx+x3qaW/+XZrstHHzGbv+4zVlZ+60ZFR//92RMxc+HJrB'
        b'vjzjm9Jph1vD9yq48868fzvy9hkrz5VnIqL2PtqeXRF/Jtl6anvt45PlJZ+1JYc9+Ofj870fdyZHhn/0mVVSVfVb8788/979zz4wneH1x/jl4xvqp57b1rmh5ZMPrzlv'
        b'G2y9kv3xmS2Vp1kH3x3/V46nR3+N5Z+nh/3l0eyNb6wfOj/pnSPn3vhjaI/L+YKvv920O8/LIUNS8X3R9PAYw7snHFqFe9pvrN5tYfIHRkjptKgbGfOGGhUD24Pap7qa'
        b'/GXn8nxF7/Hsr++3tmQf9DOrjHB5fMXKaUp/01Hmlvwzs7/O/Kbku7mcn7bF8KXRbtm5m2N6ii0YGf8UZZ7+tH92gtWjI5eXmH+T8Z/fvpPZ8+MPVy/eXrylY15nUHxh'
        b'g9/Mjk/PnmgKZFt9Zz3v+l2lbM5hnmJ9zt8ezFhuHr7h31m3rf5r6dTwHyp+n8c0Xt4vsvkm/Mc94dXLD/XtjrDJWPvpjZPl7rc/+eDHDV86bTnVXeTooZIdXT+x97Oc'
        b'+OjWQaPv5z9pWf7nn6x/LKt1te4e/x9ZtdxHPKn73TVzVVP21q/ZP/vRp98f3Sa8+9XBhNatrD//pukNUZXAlqia0mGNv56z6R4mOL9ME8jvC9o4RC0I6k1GAApsw2ht'
        b'yFl4wW40qMLZMFoJvAHQWZvhRdgq8oc14JKdDoLNw8GCvHY2vAwbtKpDBjwLzoBWI0M6YccOF1in81AFXdtAC+yzJ2ExaMPIM3FcTKq7LtuIXlQMbHIiL140Abs3BCdi'
        b'Cx07kVECGkDfLNBMAz0cAqfGpRCvh5RAP5yxook1bSuzjIZUyIGd8LA2qzU7j2FuCa4jKtZKFGHo2Mn2Tw4E2+EezR0kETW4UEzaXbEm2h81Zh28Rrpl7MIEkshEuksK'
        b'cELgHwglFiQzIEkLOG8jrSjdtxBcG6UoFfKxqhTrSQ/Do0SVZrQR7EihXxsMFKkahbjlRNaSUieiyIM7wcUSogSDh9IqJiIqjY4kfw7lBJrYaPSal5NWuMGrTKLRVuSl'
        b'pWYYUBxnJjt6Ha0aOwjaLPTVdY6LscKOBQ86ANoukAAPCDTaujDQihV2I9q6ieAw7Z28ncrSaOs0qjpQn0dr644xiYLUEZwAp+hqwAW/5xV2K8D1LDJNC+HNBKwoA52g'
        b'XqMsYyKiKxEK3P7vtV8vllPwSOkzQy9UiZnpe95tdHo2NlLvIlGK/ZapUYrlMCh7R52H8qohu2Cii4l7Y5XSO13lmDHIyxi2c1G7uLcuki1qWlKXMGzjJucoWEM2AcMu'
        b'foqJKpcwSQKGFCxAD3OD1S6e2FW5aakkQc11kMa3JsuSm1LvcH1JrdNVjrGDvFjs8uwrj1fZCLCjcZhirsblWR7aFKWwUzqFSOKw53PYF3aOw058kmxkjsp17qD9XLWj'
        b'W6ufzE+erXIMksQ9QAvSFWvy5LkqRz9JnNrLpyOxLbEuTTJTOvGeiwdqg52zVFy/GevH5ivKe8o7tyi9p6rcY6QcNd9LaqB290bf7Fzk7Potw3xP+UzFvJ75ncuUXtEq'
        b'/lTtZfyBh8DVvXW1bLXCu4ejcFW5TpayvnByG/YN6wnvspSZS9nSlcNOHmoP7w6/Nj9F5slgadw9Rxe9xg3bOZExSFE5pg7yUvVUCc8px37RZdzVXxE/ED/kGltnKmFL'
        b'8tVcO6lRfczzSjR3n7vuoUr3UJV7OLovu85imGur5jk2ZtRlyBMVeUO88GGeu9xLwR7iBT5wpeydJaYPnSgnt6bxaDB5duS+WPk6hfsQL0CNrsaq7R2kCTIT+TylvR/6'
        b'ZWcvDa+vVDvzpQy1s4vcQJak4Cidg9Av9DDOyZ4rn6NwV6zriR2YIUka4k3D5Wl1aXLvIZ6v9gXxOBM5+p5ely6PUJgoPcN7EpSeU4Z40aj0Ls9byfNGw8Dzx/ck1yVL'
        b'xUM8L6K3eLKOgRbJQ7yEnpJ8GsDSJjmC9ZsIg+QYw1FqheMcSg8C8jXqEV6kVnh+o9JqhWtYrfBzm3Mi6ocIY179u4p6UihkMBh+WK3gh7UKfq/i7F7JIqmRSafdcPf5'
        b'nGfUCHjEiCi1EX0cMdZTI7CqDauZmsyPtCqBwsqEAjOd4oDzWhUHsWMFZWkVByPpH3UxViQ06zWHH9LPaCFA6efGyHsQxI+jvZNJU17gdU2iFbF2Ad2alJkxeWJIKJbm'
        b'1wrF2LdWJC4rLF75wibQ2KMjnsbPYrPT1185/toovRzH9Fmj8/qCVsKB9bDqRZFXOuFKAJoSaEfL3eic13no4YTADOKh1+tELgfDS/AmOCke5aPH3AS7/Inz1yZwhqnv'
        b'AshA3OBJ4gEIrtsVvuvexRC1ott2uM/afTDUAoSYzWx5q5Dr28xcZ3KQayxgxVUxDluIf/h7ddzjevvkFausl93/ae1P1xeLfJQVaT2l0lmOC7r39nv/q3NDRG5wZvee'
        b'4lvR6vscg8rzfw7/2+F/L95SudjA4mlip8nheSFODyvWlC56b5n57RM9Xj4fmi0J6jY7+C170xcbOmKXB1z03Srg/vhfTdM2fCfj89Js5w3wWt4tcfv9257KzmkCA9qO'
        b'vNsZnN3mpZ8bD7aCdmKyy5gDO4rgyZGQKk081R4gp+GiLhuD2pEUeCfAbr0ceDfAMZrx2Qtu5YYtfM7ejZg4fhaxlIfDa+mw133Ejs6YF2HymrONPc9lWJSTXanjM1ye'
        b'IWWjLxNOo4eiY6MW5f+K2Cg7L3mWys4PG4ycpOVKrpfax18SL3W8w/MatnEZtnOX+yrihuxChj1DeuxVnlFSI7VP8F2fSKVPpMpnCr5TiQ4LrsMg11vtjZ+0r0tXe/pj'
        b'08PJmLueU9A5o/Kcis7GRUorPskHLY//yEqgF1drqRfWpKOjv/IEEVk+fzzQ58Jb+Fz4+cE8baaJgMInw6x83cnwKofCI9wjxseGGwtLsdLz/xReBqem6Hw+cKksd1Vh'
        b'hQatVJPDZRQ+6hj0Po7WOxZtIIrKwrWlRflY1Zqf5/7Cs0EzAM8icKLil0kP/Dx1ZafTOBUXgBR7O+F9j+hqKmx9gRt7jp1RIdwVUVgo2mYgikZPnp4Vg9Fz6PQYeaG5'
        b'teVh5wp29dT+KzlbeEKwvyV1XpGZWciV8bfHVUi3NH+ymiO1X+lI/V1hXMn5VMAmRGlWDDyhQ56oXkeIUiesoZ2+auANoEhhY2cJnVcOlr1hF5FE7b3S9ETvXCctQUq0'
        b'fowBJtPhjuVjuX2N+HzBq6m029cx2Pvz6D0fWwnpOdYubJEuwYLOzvLMDYSOhNJ05EF2AYPi2eqsxz5DXD8a3e4NHx3d+MRWoLL1H7Tyfx7i5+0XbN/nIH4+4OilfnhR'
        b'y94208P2mVWANqXTq2L7kNaVncGJ1QzS07MS0su+w821+gVA8xG8OQyGQ2AqSGQ/iaIk5ivCbBLKQvoicPx/QJx1pJ4BOh+DR/bGA/8MonIYNrct1YKfG5tbPbLF4Oee'
        b'bZVD5sHfMl3MpzMw6HnIA/L1YYwW8zwJY56nMAjouQa9HEOM20VWz/rWyMI84qHrM4Di9815Ms8hc9fvmObmbrhKtwf42yNX8jp04RumEQ2wji6gb494dDtEQ+b+T5j2'
        b'5s74UsAD/O1RBL60oDP8iuewm2cnrzfuMYthEXlverw6evoT1kymufMTCn8+IJ/fGKCLD9j466N0Nn40t5PVm3mFd2XVYMSsIfPEJ8wMBn4Ef35Df6J3JTEekPJHS1ik'
        b'JZ3czqxe30HfKW/GD5knPWHamvs9ptAHvjcZ3Yu+PorBd2YOmbs/ZpqYB+ArHg/xNzo0HnvilMCj8KwORR1ewl/44EAq9h/z9TGoANtXlj9Cq00MW7mgBdRPLYFNIVZg'
        b'D+yH12wmTQRVubCbEwWrQR2oN8JOSnCHmzmQwN1ADs6Chvh4cMIU1INahhPiGfvhTXMgi4IXwUFwQQguwc4sc4xdsxN2T40GN0FPIrg5C911CNZuAP2gE5wN2gxOpoLz'
        b'0ZvhDdhhCHvAGfTf1QngNDgJ21euC/OGslBYBduKwXG4CxHBC7Bp81SwD7TDGtBrN2tddIYt2OcJq+K2rA6HBxBp7C+MhnvWzHJ0EzomRKUYLAzbFJQBTi50xjm4L0WD'
        b'K7AD9AFJMTgD61A1lxPB5ci1fvBQ2HK43xy258EeLuJ65aAenkD/XYNHV8TBY7PDV4MDufAcBxwHl+GeEtAL6+DxTHgO9FSuhafAzS3gGmzMAnUO8MSaxfAoODXJBp5P'
        b'BNdCwH7U9zpw0DoedGeCnT4pqAGX4bHJoHsL7JoDZAzYjujsDngYNKO/h1YBBU7wW+nKMgWHwUXYGhaA+M/LqyabRMNLYG+uM6iatRbsykPVNqaB64LchBK3BHiwEN6E'
        b'TcnwyEJ7cG59LBwAF9A09UzlAOkcwTys7wRHwG6T8Vmwzx62wRPoV38a2Auas9FgHAGNAbB/coz3VC8eF16YjwqaN/ks9ocyeMaKC/dCCbiUJUKldRYmHvAWeuIM7AXd'
        b'qDk9FGwMz58CZUtAUxi4Pg62WuSkgYMrxTGwai5sdAX7lk80grfAgDMXDBSBW05gz0r0+NlSWAOloc7wRJ7H/EVTg2EDWgcDoF0kREvuKDyWZeawZGPxlE3wovNSF3As'
        b'HZxwWAy70fg0QoUR6sxFtJ6OwRPTS9Fq2G8E9s6EV0PQTB4FXZGoo2dRE/vBzmw0CYcCp6EVUbseXLBzgrVoiK5BucVWFrwOa2Z5gR3C8gNo2YP6LQ6gZW4sOIiWvRm4'
        b'DvtsNk9H89sxE1S5gmYoDTSLgOfRDPWC46yZoD1X6CkAklVssI+/LRicnly+cZUlPIIW4wmoQGO7v3TFAnDDJhscmw6OgV5wCuwUwmY/2Og/Hg7Aq6CfBXqM4WEneFlo'
        b'UApbwMV5CyunwaYtmUWgCzahobjhizqBVgg8V5wyBVVx3Bk0we2zs1Hd9dmgcRLiSvbmoK23nRmZButBTyC65wJUgDNbFm/hWmVvy4mYtRI2W2+IsIbnUE/3oaW8E+2K'
        b'HRPQtqqZ5ZbqtWE8WmyHgAyeDUWLvAstzgFYLYT1RRhWlz8TXgM1hvB0DKzfBFrLU2IL4TkfuNcXiZO3Nk8K2gb2LDPOBAP2rhj5GnZYT2aXwFsr4AUmlKy3Fc6Eu0Cf'
        b'Cdi/NRFI4XbnWeDgQlAFd+dZglagyMicF5Y7brwD7IydZcIbFxRi4BQ+D22hllRYnYkmWArP2INqRFOqhLB9IprGa2AH3M2C9emgDvbyYXM6rM2GZ0Af2xotvlo7JG8d'
        b'Apgs7V4ehkcWVMOz4GLlegdwwBW97xxaU4r1aC3s3WhthN19C+BheGVzGA80oDHcheamB5GtS0YrLZJhqwNisOSL5sMutOt2w363peBGWgq4NQnV22HsBepFiCa0gz2R'
        b'+bBvLazJBjeCHLGNYUkG6HdCS64LHpgL6lOSrZdUItG5HxEnBTy+GAMIoW50g+1hsIvrk+llkwG2ozG/tBCeLsKq9gxwQQAHDIA0xwu0weNgV7mKieO6LGzRipwKDuEV'
        b'iVp+xR9cLI+EzUvYqFo53FUsBPJ1pmhnNk6YHQDarVakgM4YsB9eRuN1HTY6oZV0E9Sizl0A3Ulgz2Ic4+oBbyTGxEyF0mRwMs/KBO7G0bloTfWDXZ7gGL8CLeFGZgy4'
        b'voGaGJQEG9aI/dHE9YF2xGPWgqto59SjXdeUs3hpMSIfJ5YxAmDTajTk11BrQS1arWfASXAUHl4yExHGW/52C8RLlwF5GmrjKSiBF33R7qib5hG2Hu7nGYMr+msW7ZCj'
        b'sx1QSy5Vwp2BxtvAxWJCMw9bbAAyRCzbY1MnbnTPBT3pmzbbspbNAvvswPYC1LVbqIJ2RJx2ToxBK1hquBYcAB3LQYM5muZOvjlomAxliUAuRrdsh7gvrWiED4IOUGXJ'
        b'hDunIjJy2sYQ9E+GV+3HowVxAVwNgzd5lfBksc0G9qoiWAX+v/K+Ayyu61p3hhnK0HuXAEkgugRIFFEEQqI3AaIIwdCGJpoGRkIgRBMd0XvvvYMQVcRrOXFi595IthPb'
        b'xE6cevMS5wVXxfZN8tYZFDvPL3n33u9778v7vof07Tkzs88+e6+91r/+tefsdTrIYquwXYlENU7Dm8RdWAuh6RxVwbroY2mkbxW44g7jJPTdG6cJjRajC/RJf0eyXLE5'
        b'njxYlxnM3CGTaLCmyRj1sCWcqyXNJM9549zN89himoHTxZcUC6mDFVBK2jwKazaGpskJsEaA81heHdtwGyvkscYLBm3DSSNg5C51oBabTOERjMAcNBXiqLTeKRLyDo57'
        b'RZ+BJ9gv62VOA64ikBwmt913Gda8U0NpKtegPC+aJrSHHOIQ7BRi/W3ojpUWYKdrire12KU3+eeTv6kSESo0U51OF2+tKOyCvptQJ3FbG/pJvUmCpN4weD2DermPQxzj'
        b'HD8vrM1WwBZBpPSxOFzQhS5Gt86QRY96qcAA1ol+xOj1HllrDYO12WKGsYtLFrjBvnI8HoalsSdUlg0rzAa7RrKabmjOh1UW4e0pDSy1IQl36xfhojRsw7jA2xR6PWFO'
        b'jRxCrw6z11sR+6Wz9DNIa3qVyBq7bc3wyTVrH+i7WoTt+tDgd9yB2aopS8J5gvXSITATz5hLAjv3BsOHBrJxCXdiIwkyGASeJywgCpJjD31q7hahqrgUDS3xl6H8Cmwr'
        b'47B3SQxJZtihSA0awgKiYcYY10uOecYTdszShMxlkVjmoC/mLhs7vexgK/xskaInlkEfdLslkWsup1ke1VYhcVfhOAf2VbD1mpayLvm+OnVojg1ICCfb3bO7eiGTrLgt'
        b'CtqsoSJA/Yw6TmfCvDtZX00GtJtguScbSyVDYDv5EnR4pcOaWxDsQM0lJ88r93Wxh5SfkHGCrlfNyiIfMIorUjBMVlCrSdayyuzzxH5b2IMGHTLSfmPYKcaNW26ktN3k'
        b'6Rqx0+UWjnoQpJQmXy2AKu8cMoDhYugs1mD2NSTfxZlUbewmDBwhnKhzxoeRKvZI+t6M497EjEijJwwdqA8DdDTm7lDgrUxe8bIurIWRGj6G9bvnyOT3cNYTG0hsleTz'
        b'hhyOM4xMCA0phqcZVcQW9YtiKBilbpbCYDp0JqoU3g7EfrrKOplVF7SmU29miBNUSECjiATfoFNEw+sjBzpHfjMvCkascRDHtYMVwkj1pjI0cUSAHb40v5O4cwMG4qmL'
        b'i26wSEZc4wQPcIymllCPetZ5jZqpjku7zTgiLMvSwbVcQphVrDzldV0Wl/VsvK4ey8d9USuj2nPHiIEMhNIwvqIRFrjJzsJGohGujhbw+Cws35Y77SQtJBbb7RWBrZdo'
        b'ODDsQZO8R1dfE5KgNhgUijoBVXZYYZNAhrNP4LucW+Qqf9wf9nApEYeoziIBSFeJAZRaRNCMb3IdCQo7Ycvc/iLOxRJP68AtAZNDk1zZLHnpR0jAVlFihe2qNLiaS7Ew'
        b'7Iedoe7kXpsF7tBzzZx4xzjsXKCrNRIjGYZdJbLvARhRxhkfaLQpwFbFQIPULEK7MmmykMEiWT4sG1+4HKDtqkBKNg8dilbHuCSzAVlVJ1w3MJHheGG5EYmx1JgUf0JF'
        b'j7x8I7W5cAMrYqHdAwib3MgREjwRS8BtPvbjoPMtgqwOmCJnMk5cf5lmih1iFQH1xtnkq/tgPhgrruPojQtQF2AZSGKrgFrPDL1g76sMj6mLvQ+TiWZYngSlakWG2EUO'
        b'qyUGN4SkPZ1XcS4ea6zOQpcEqdpQAFZ7kILtE64vpMZSVNLMLK7oaJOI1+OxzQRnnLEahnIcSfrTtlDlRqozji020eop9k7BiTAej5s5Nwibh52VZI3tHNR17MwI2Nfl'
        b'sVbtctBp8of7xtB/jRpuVSD9epIFdaERZCjbN2DYBCbVk3Elm67ZRyMdiCN1m4gRaBACtcKCNSzJkTzrsCsVag1gNTY3TusizGZSpQXoSSGM6OFkUK9Kw0jr1+2gyRX2'
        b'TpPH3cIHJer4hJWJfRakC0tYL3qL1DKC1HWDUcuybLFW7pFWFuCcAKfvyhD7qVArIiGWmRwjmruuf1YV25SJT0aGFvpAc4mBcZEIqhK0Q/jyoeTEx5h/UHGe8L+TwIRO'
        b'c2XY0z1lBZgvoMndxqGIi3LkMDdgXykeJ7AngxzulCSWirAjXAB7Rdn0VV9iLPGZRYZCWEKfsjCDFHgvnQxgLVEbK4UGOGFKujFK5jMXno0t9wwJJPoZ1ptGXaiJu5Cl'
        b'LUdntBCAdJJA6gOjmZtDisOKI9MKTsgHIRHXMZw4Qfg9dcOtQJHkWw+M9TbDZnaumypsKOWTdMqERCuao4LseKdwOTGIyeMaRlU24IE0zioIsOaqBZNctRyqc6FXiQKW'
        b'BzBYgKt8UtflM/IWfoRSPenKXhl33SiEGj1GZrpEmFOvZ8olaXacJdrZrKUO7dmGBlfIXueP4ZY3wddDAoh1csvb2cxWT2y9ZYyTJynGncUHxdBrakUouClNF6vASTtv'
        b'gV2B0Y0UsvQysogKERlDryy02mDjTTvsCzAme1hTU8lLZDZS4ux1nI0l0xk3Ih3sdyDe8tgOqnEzNxvG8ikQr6GAWeusOqFm10WC+jXnk9Tt5jR4SMRBEqevkcOsIVVt'
        b'c7uJj67pYCUX2nFJQNcdIHXrZZ2845p7PU8zhGZ45YQ5mcwAtCTnQ79bAdSdxFrJG1ifAT0uVHcV1ol5dmFtBPmKemIn/eoBijDkZ1ISTCo6j4uF0ZnEFrvC3K44MOHZ'
        b'nBNMeAjNb8BjUqqmQFgpSldPIRDqUSINX7fCsav3vLHNy5w0YlHrBJadCci4ho3yMGYmJb6lLhsrkv19JVnsMyxnOTqlF8fEmS1I6FWXX+zAZ4WoER2shbaj2+rmZNL8'
        b'LSRYbHeWiAyu5+LNo3vziEdALbPPk32RlRiHPcZh4nwjKt6ezG8ybBbbjwUd8eQP2lPEX9wNIadXb8lm7hU9Q7IehNLzIh8OtdTvSbxpgBzSQ7KJXnd5EvjSfVmDGB50'
        b'OocqJaiRY2qxJj0YJRF1MITdBB/4egVCVYabphnBzGOc0Ckk7zQCg77KHjEE3s3Mg3+aiK6Q8eKQPbPkQvbdUmAt8oRZTYblFcOEIAGr5WBEmED20gb7blAaeRU7gmgS'
        b'6Xuyw8ordDgOUyyC1+prqkTh+s7QXA3YXj9FKld2jMKBFfNoareJFUzXrBQQoi6RB26jSaYIJ/0eVFmTd20Jh2YTihRWSRWuE31pMSF4W4BWJ9iHynx+IDzxJz0fJx9R'
        b'Txq1qk8hUwVFUDVOZveg2o642zYBxDI5g2FYNiIyPA09jgLH2xxskhYoYbfPTZixx02hhQFuxeHcdV8NmJG+JxIECvnMo/9gnMcsHEC3vg6WkWDnCIfKGG994zq11UDy'
        b'7IxWzyBr3aIuNJ+noU666spGyuNgUrw47urlYIUthTGlJJUFJAzdt4UGDi5HmwfbYmUUkyXWGZdNyGKm7CyA2Yg7A83ORIeaaDylQi0Rl/xScx6NYRz2LscQl2yDOnMY'
        b'lMb5dGz2gY6LOHyNIqoGClz2pDWwPt4oycxTD+dlSHugQ0gWsmemKMKZJKEQJ+lfa7ECdbfWPiKKIsgFQuEWO1z19L6nkpIMj0wVYEMRh3xIO8sdcOGMLynaDFQhs7RT'
        b'qwT75yiEX4cyXejnEwZA50Wf60ExwsjrWmQINeTHt7QcsV14xo5AYvU2h7BhAuatNGFflIZzDhQNNJurYa8WA+Lk7KrPlpCFPjpPfLGWWY8yC0ohfwqPz0BfPulUNTyO'
        b'gepscuHjMHuZbHfBvwQW+BTxDdKsLvhdEK+/7HLIwwzFpFI0NQFNDlp69y2Iea4HMYEEtqTADo6epWIf9ww1oVOQZ5mvTZRrzg034xSwTAF32TAYVxJzDAdE0+S9NGnA'
        b'699cmiEEXXQzdFe6jfOaUrp3cCSZjKMskTB5JSQG6/zUNT3IAvehS0jirJJTl7zODwgl1Gm20yXVqSV/Qe5RBydttP2NXGCtiEKC6ijtYKskD2lyaptXI8TrNKvBBnSh'
        b'XmizJ6nsytIoVrMJYUbJo+yl4YYINsxgCepdLMg8JrE/m9403T4HveTUCN2bGXUdgxVzWDybQ3x/8AKuJseQpKsCI7QYwokE0xORbGJ8u2TYZfpkQyve5OEGufo4ZcHc'
        b'0ohjahEwfYJQtRH63IUBRLUHU8mbV7gz4LoCZcWZxPH13IkqjOkoMYtbAThVqOopC7NZsYTDDUdLAXlJZAXNN42pW+TOcOQ+ocGWPhnDAMW5MBUYx8rA6kuZBDv9cZdS'
        b'yS+sYb+AetiaT064gs5g9qMPJCXDUmaIA65rKcOTk9eZJz6p44SHNSMRc5zREuBWOvNUNBrPLIUPu0Lci5N0UcYePRtsDc4lWGtQw1FVCsHaiohIlcL+LSI76xdhRiXY'
        b'9KLdKXK9w9gRLYMj3jkk9D7T06LjZumaId6qKjisViK6oABVlySCSO9nSQNrYfI+gcGIKMIH6mMIasstYFNdQKa5S7axURyZRZ4yGxo5uELv54nobSXcJsDtd70XhRPR'
        b'VoRMvThnBjuX4mDBwNiXgKGNmWCahCeEbT0EEAsqNIw93L8fEkCNjp+H1iwN72C69rYeyWPHEzaZbGXVfMkTF/N1LorelmDSlzXjPgyEYf1XwW0kXfwhdJ0zYOLb6FA5'
        b'NjxSxZogWJKygoUYKU2YQULB9fOkBEtOERQd11mnO5F6tojXTGZPWBGQMet0PSqWUEm4RvpZBcsUGuCTO8FWZjRbc7jr5gEz+tCjpK9Lsm+A9WSy1rGLLiyY0SFomTWG'
        b'HicsNSK4W4X5KBy6Bn220YQ81b7QnxxNTmEpgiEnozgSLTwtyUlzwc4zOFGAtdawejIcK7LPwnjGJXIM4zTgKRpjvxcBDmwFYJ1lNLmOPnMy5wdWRpFpOOGgcV2IT4JI'
        b'1zrJeVSeU5eBoYxsWCYAG6QrLAdJk3iZtG/7ucEUureQyjTAeCENnFyWLk6egQ4ROZWuoAxSKApduiwVsqFS1vACLjilY7efZhbswowI+5xg20OIXSS/JlyOOA774SxH'
        b'fKAgg/sc6mlVoAZsSTLrI2NOMJmq6QOdV/R0nSjsqqNh4YIzgfkuacUSmcFjUoW9WxSCzquR4HsSkxjTSUkzJdx5KHHDI/WWPDyKwcmM4KD0lDiiqauK1IVecrpzsrjq'
        b'D/VJ0BVhoQUUZZTjwwz5BJwPhyY19/jYIhz0Czxmgy1nceVY2g1stJNgaCsBUSWF0kO4G1Bwj0Zfn6hMDmwEnxznGkOnWihWJUV5x10K9CITb3DFjjzHZNw6QYC0SNNa'
        b'T7GhFJ/QYV4uWl+MMAxytzM5AJLOwQo+OmFGptuNY3fJ4hph2ZRCoHoVafKRs7lRGnTR+mTcC7lF8/MQiSI082BD1dmaIG3wrlqJ0mkyrx7CmyeWWMOHQYcssspuXBB5'
        b'ccTP4V4ms/lb7abwdoMjoYXT2OKuJIRxdamM02Lqs0Zdn8ROG7ZfuC8TPyXhZhKuKZBtPaLRj1g6K2Kz/vVjXFLzXnLiDYTI84Uk745z4bxrsGiPvVGk4b2E3ttyTFwO'
        b'c/rXSOAUWEOjJlaGeTH8R40aW+AbwIQtLlwxRyI1fsdIRvUnYMjagEy0wwX6NEg4fXnkeaYEsBKlT7reKxF6Tg/GdJygNBFqzxD5dSVANLhmpkdQ0ZqGFTxYEQhLyHlV'
        b'wHq0PTmWNQGD4vXS+SF2MCPvQEJuwh5tPolpSxVHUzVwUca00MPllhYMOMBSwD1SqwnyfuPYo4Mb+X44o0p0p4kc6U4aOYNCWU8hzeIgNdJ6wjEfxp25Nrhw8RRMu8li'
        b'fz7OK6fEasOkivItaNPABv9UaqgM2i2lbQNpRoltkFg2uYaBue4OoRm4eILQYYaMqD/+BO57EXx1wYCvhyvRWfIKUwz/JvBqhQ25FKw+Tx6adLTeE5Z1ecyD2B/zbxDw'
        b'TdCUbFKrlSoakeTIH8KYDDxIgyonnLEiD1Bz/za0Ot5AZrF8lAVrcc56BCrbUJV+mgxtShtGrMjSe8gmlimu7o/n6ZzHHS3oCnf0z/UmBzoN07jApVPKYc1Q3YlCjjGY'
        b'9IBZSX2ypX7YN9bQIT770Byb72EzI5raO7DKyTVxpk9bXGD0dCRukafETpVTLqdw0BG6BVGkNzXYKSTPtFcQg0vnXK5BRWY+YWO7NcseJhMK1BMTSeqZabgDDxNh+RYx'
        b'6BbicA9JWisXCForTzlRSLiF1cIL/imuBAM1WFdkRcJdlWeT5s3KM+yYJrInOa+gGDaD6e0Y9AZQvDAES7k+uBgp9ovruOMS4wZdpuQzKfj1dsV1P+JwS3LJNkTmusku'
        b'm6LJOvalE4m1lZ6A3ZMiDplS8Q2CWzKkMtJnxpL2cMeC8Lib1HPDCde1ifFGYZtsuifMncI+zzPQwiEXN6zA1HBVTqeAcbco1ceH+ECF3zUnQ+KWWFWYQ0R7D6c8SAdW'
        b'mYzcu/bSmeR85tg4EobbxsUUrfRDh4mXklwYdiaLf2VbYBb8S4qgHbaZZa0x2AqlgZKpTDJLRsR4J2DSRxN77oaevn6GhtiBsy5YVoKN+EifPGTNDRi6RqTrkZVUWo6t'
        b'Niz7yJLtz1PFh7Yk3apMsoM9JRyOhUpiBcs05kYbbNaTpmFO8Kxw8V4aEcGqxAJ44EquuRGGObiqzcO+CG0vbVKaeVNJ5WO4efEaNCu6yxBybmOpN1GaOQbXzuMii9Co'
        b'A5vOKgpCoDLG39QxP0MW95QjC08TyBM9d8sKgaZcbLMNo7CaYaNrTmn3SEdqT8OyygV/suMRLdiWhY2ou5nmOG1MyPWYSZcTh9sFslh1JYxso5LCk2nCnRYKXYxI3l3H'
        b'cUBelpOihfXXM9Jj+XbY66/IvqJJ5y1AixS0qmiRzbXB4wx5X4szuHGcWQMl910Ku7rwmPkVb0r/GIV+DYkXXYnGD54jWYzA4jGrbGgJOEmW0UgRUJ4Ies7RHFT54iMX'
        b'OWLxO8QO+q8UauGo/H1JGkGrF/Sq8e6R0bXSuxbYt8iOvwuDRhRYVqg6BsMjbehXdnCVv4Plflipz5fGqXBoTWPSwpEeNYZGM+umOCViVr1o3ncIfpfJT1TguDXW3Ocb'
        b'kbMmHhRBdQeCmIyskbhRaE3kDCbIZNqYJXy56ETRdTLKIWD8CXHScXsa234xtB/HVgFR70e3SFsW7miTUs0VY3UJse5tOeIf5VF05U6oF/2UWTGdvV74lR24M0tTTZHk'
        b'hwnEMi4ahiqdwmaygchTRfR1v05qEk8bx3UcTzEZ6XAxFealfeLpIhvEkyYk7HFDD/ZxyiFDjkZUicP5wPwMXHbdBVq50KlNaL57B3v8YZRDh5OwLSB3M32fwLGJzKmd'
        b'5qJF9jiO+RGYzpHoG7D1HlG5HRd1rLWHHSscPRWI9ZnMj12+zEpVcggJp9KEYKVWnouzAl1S+/W7hmTlWzbBOaRv42q21LfWs5rYedLADPtMrhBlINPwJGXYU0/DR/LY'
        b'62yEEwoUPlbegApP3HKHOV4BIUwb8Z8OQucxFmn8thQM6PvQSPqgS47ihImzSjDiYQM9dsQYKrXDNXD65DkpKay56om1cljuGULh8Y41Ua1qJ1xRysVHZ+T9bWHUDts8'
        b'LriTYNagl0uGP06QX1UYb6jM7FXdIizYgjJDUvcFtjS0lty2IY1rC4VKObFibPEJxfdvmhAi9GN1DklukkGCR2eJgLSlpMGYI6k0sxjfhnVauGZPwU1LKtRIwWiaIUxz'
        b'YcntAm4wgTqWXiUMWw+4Q079iZ0U0esxaDDFCksSzpImjBZDlwrpR80J5mdlyXtS9qnh1HK7iyJ2En+QusPwoAq189kU9xGtLyeQaIFJNey5rFXA3GERRtLrhe2428Yw'
        b'awW7XjBmJgk9RsSx+qJg5ibFPQswZsUnFkS+2/5CzjnY9jt9C0eNodsPJi3OXsE1SXIsXb5GpKIDuGpDbm6GsZKeMNXLdsS056xx/9opwrau0HhFfnG4bjQpTw2Wng+g'
        b'a3SfdDVwL2YRx6y5iTM4wH7xlDcRzinm4RPPr7JMss1znI8y/u4Q/Xz4IokyK4X699ga28044nUqvu9df2Z1yZHlk0fzM0LBDrPsFF4ITf5M8i/2WdYl8mQNcVh7lASz'
        b'E6qZpapaLovtyWIeKoyd3vyjFI/TOrDxYpVM6TLWncMa6htzEvOzZr8/88gMW6bjZcyyMgwcraCVY4sl1gfQWU6s9HDiK4+h4eixdVVkMPt/XVxLLqJ3k6EvBsuhN/NY'
        b'b0ZnBbOgUQlHz8MjcScEOtewPlC8vHaGxtMCi3riz9WO4cKL9bhr1Oeey7hjxhZ/Y4M99/z9qCULFiwYkpzbBeIdrCVk4U++WpTLI53sI7zfNWN7iR9yKt6i+8Y5Ce14'
        b'CfGOZ/m6ZC+WGUf8sae9RMYwW/yxJdch4yizZkScRLzp0TO4Lc8dN2cFmUkEUVPiDb3pj1UyJPM+Y26NsgqqbPcN+7G7cuUrnZYx9hsflt9Z+8PcO28t/0G5Nfc1I+nZ'
        b'7QDjLePwS6ZC36vnrSpvmmv9mV1iG7x6qubhS9IdcXf2g9+z+8Xndic1Zl4tfTM5pIrA1vZETHL4d5JvbLz6IODV9oDX7Htaonva7kY3X4luFbzz58h/P/60kq9d7/WX'
        b'veC3L35UPKj189+lWPn92SUxLmglz+67e7fyxt0Wl23VcztiY5/ktisruPzevDT18NVCpdjPP5DtS3Xav2yt/pbv9u8+/9Ubro3vBKuE2ahnrMikfL/7i/Haqp/21BX8'
        b'sXazquCD2oIa6c/Xfzv1m5XFwO9mTrk2euzPmavvPPsX+4Pq67+MfHrrN1yLzqqMK6JXXzMefj0k3bnrgd/r7PwqvufU+5avG+VX1tdMt3ud+vJqt+TLJpvfWquRmlZ4'
        b'0sD/gKdo6Cab+muTy9G/+OVPonXs4j9wvDv3O6Pjv+JOuU/n6v3gUH87+ueBbr9syygXHv76D386/297dgszus7fmf2Xp5sVRVs/+Fl4gW7smzKv7X7ny2H9yLZw1kRU'
        b'8IdpB1tnf3H86hW+7it3Fdfa37dw+PSRY6Pml/XeUS2337xzLl9PtHlM3yNLfe87v89ui/pvB29Gf/9PTx+7Oj9Ouij3Ji+xy//cyX99deazdwfmnfOCC9p+8OOGrL7c'
        b'64FhDv/u6vVybNHS6b1G9fuN4YFXzzgWB+fCT+Iy9F/OL/5JfpLL5z8NiNmV/pFKms5vpbOGEwbK380a0H7lUb2GwjPDoLDaxk3pnoTjP5NMjpj10IV3bn7byeCXEf1f'
        b'JEzvfuwm4d3TOPKdu5ypHPWtfoes95/1t/W/0mU//+miV7q860OHT9Q/6o/9zeIrziuPil8rOyz4tx9lXa997R4rpczkW/Nv2pXI9o6b9U7q9E449e6/kVammV7bmV4Z'
        b'907hp/9aMvnGbzf+eKjwqdt1jFHM+XP9+JdN+5+94/DO9qfzTXFfRh7uWk2X2/decODnZp8XZe+//276b98t/sndopk6g1HvP847f/77K99aGFsuanN7d7rr1aIP35sa'
        b'+gvHUzJW8vsbZrLi7JPWHCaxWYAYjlzhATbqwa5452ks7Nz7653GMjp/k+gRKrQ+YR4jSnFBLY789VF139iQW05MYwkf2H/C3KMoJAbRJCdU4CkQT6hXYsGAUCRP7v0x'
        b'h6VfyCWKC1tHe1kH1GS+qnYHN+7cUpBiabtz8ImQHM8StovTvmGLLUzk3ZaHIRi/JcLHSlAHDUoyCrK4rHRbkmWmyMV5Bbb4bmhyYEZU83+pBQ//2nogVwpbY2ALNmFA'
        b'fP81sf0pCsG/as7TUAanJM4Qmxv6hLlxXJJoRV0ePJS5Rb3MI4dZ+3caxUdSRdHkXXbhsVhU9th+/m/TPX8jaV+IHFG+CbOwb96IK/P/UPFPvyP5n1/khbHEW3zd/zd/'
        b'//iW6f/gZuoDGT4/Mychmc8v/OpIfDe9IpfF+stf/vLvpazDCDZLQeOQK83TekdJtdm2/k63Ud29nrxh2+GEkfN9hdNXe0tWTi0LN41WRJtXVwrWrF+6/F1V9HndNuBd'
        b'bd1u2+6EnvN9vGG/Z9rWy1rPtB2fugQ90wp6Ghr+9FrEs9DI17Ui39U0HFZty36qfOqQw9KOYh/KslTVmz1aNGouHUqxtFxr5N7WMHx60u+Zhl+NLH2ibf6WlsMzLYca'
        b'+feN7N4yuvzM6PJTmePiY+dnRs50/KkUh+f8XFaZd+z5KWne2c9U9Xnan7lI0pEil3fuubwMT/u5ujJP/5DFFCYsHb0ahedcLzbzCVM+D5Uw4JkesqhoFnzCvBxeZrNk'
        b'lZ9L5EnwnJ6zvi4/Epcfc+jLQ/GXh5mSdPw2T+u5xH0OXYv1dfnxUUl1tY9O4DLvDy/JsPSPP5XRfp+nJD4tVYKn8xmLKf+2KvP+MJza1n4ucYLn/CmLCvH3h8zb535s'
        b'viSPSTH1d14+OXo5vCwnHkKsNO/Uc9bX5Yficlj/Y/Hri6Ewh4fuSuITQiWZql+Xh+KyO/Nj8euLE8RfZMiKT4iRYqp+s3xRUfzBPflINs/wYxZTPhdKXORpf8yi4rNL'
        b'Emye06dSbN7J51IKPO1DQ3F7fAmaEhZTfiYuX7TEHB5eljwalBTPkobzjfLjo/LFkOjwMEThtDT3MJxtQmUo++jYlMqIF5/Q8YfpUjQvEoc+Mmb0UdT/VOkb5Yciqctc'
        b'GYkP/WX8ZY5JPJXROYxSZqkafcSS4V1h13i8rXH6IxZb4Qq7mf2uufOmxzNzt838Z+aX31Q2GjZ6pnxq+OrryqcPOUyN9zWM/q9U1f+Pq34orvqhEtPnPx7GiNhsni/7'
        b'HVWDcfmnVl5vGHq/oerzVN7naAf1sId2gCLr+4pqAUYvErPZCzf/wUOx/78s8pjHzsT/3TwM/ylAFr7N7G75CostmCZDWeJnxD8PY7PZysyevn9c/FfSyjHz+RJHykON'
        b'9ZKanMdxTnpl0LZEnh/NptLvXxE0f8+P46FcVfSZ65pxW/fLD03T1Ds2y37sX/CsSFnhDS3eyxU/efBFWIGGAXTlf3DKcPLLwz8Flvww9s3UoXOvf8+wzXL1e0ZdLh+Z'
        b'DTefmL0awJtovxokygj50LjqIKT954G7dS1GnT96+8Z4TpaX4tTPvhttX/2FQeTQ1b69bGHgs58HPPv17ujVC68nRG5/4NP0u1fP+/OlMl9rXrib9XJZ4sOT3+6W+/YD'
        b'PY0F2w6dm7apnp/fju5S+Oza7dkby1O8pYMfvmPVt/rt7e2PX934IHd2lX/7V+avfPyXHzmWVZlcf7oiwcnq/s2wnJz9j1bKAh1zn1VUZ/3x7Zesv5BZri5+UJNb6qmf'
        b'UKobpPwL9VRH73J1HevcWn3RjZ/pOqQNFzgel/qDdV/YxxGfvFyw3P1eZ8HtX++Fv/em3k/qm3ZqC2z++7cvf5n6pyAf01+kJxQ0XZT61k21kz83MxDnrgmDCthjYung'
        b'YL0b4vwj0iw5WJVgfnnECvGO3ngKnf2DrXCFqRRsdREGJFgquMuBkbM4c7Qx+DGzXgL1VIqzPMNDa5yFJmmWoirnOPRZHe08Lo2AXeYxJoG4AuXSLCmuhIwtTh4lhVnA'
        b'JajA+jMUNMM+O4yFY7gqJ97fd/oC1FpgoymTRaWBzeJhKz6xloDekrPiM2VMtI7YtiSLG8S+Bp2wXAKd4n5zKeJfYzYBiU+FJVuqo4h1nCCYh+mjp0uWKUP515l3ppnb'
        b'4KxTxUPSgSnmRx+m5UBffGjma8NkfFbFNg5sE5nfEqfIyXXEKn8/y6DzdmyWtDIuY6uEFPHlo6TPcSTZbX9bOzpbnDLaG3skWUpGHGc3HDlKG9QIC6lMBd9AcXrtNdhj'
        b'OrjIsYFRfCRO/WKtiHNYb86k6OGwuFfZFBm0Mbe9ehwlFRqK4jEb0wMtabA2bBx3g/nbUC7eZB0VcMnCCh8yiYOy2Lo4CptYESrOXnP7EnRbMJnRA5irBsKIJgmAy9Ir'
        b'5kI51qeKSb9JiZ0/0yuchGmSACN4OTMJbPaGCvH3vtAZlsdUUCh48bWsrwRzix2si3PbwKIlPpHDVSV8lEd69DgX129RoAN78goslv5JrjQ0JImFdAx2VMSbTi2gF8eZ'
        b'Fplk2L0SOHr8wlHa7rKbMPk3Of3Z0CcLfdAKG58wz0bWgJYsf1gwpTlmkliLHyoQ7AsPzwRZmUmxvJmbDq9I34NhgyMVHORDoxzN03qxHPPMrhYWThrBhHguhVh3k9nk'
        b'ERgQDK05hEf3SKCwdEesDaJM0v418QbSM+a3rLKg/ii00xVxoQoeRx7tVK3GESkSeh3zQNAACRYPqkNNJKCeCz1H6Zae0BdDFn5WltjPCrSyZrPkNTiyOVgt1gYod+T4'
        b'07z4W1MtsiMzY6iTYqnZcXAQN9XFwuJjJ+xY+Fiap9FM1QaIZwWbmf1mw3niSSdJ0YAtmIUkXLjlz8LuBJgx8/hnBE//dHf3f9x9elDxD0Kd/6onZfbCMp40PTs9/0VU'
        b'8xqLiWr+XMr6WJ8lqfa2gvpbCsefKRzvL3hDwbTU622ubHVAWcBTFaNxxze5lj/mKvyYq/JjrtJPubbPuLY/5VrQ8V//a/6Ua/0e1/g9rvmhhJSkxqEEh6fznrzRp7Is'
        b'SYP3uEZ07nOp4guSV4iD/4cvnx29HN4XkbKqlwb/8ZOrt9ksZT2ibkyj2sTleDpf/lJOkz6Q1HhbWb1Okj6S1Pgiz5xRRzkpT10W6ip4mnPwtISnFQvN2MyxOYc5tpLz'
        b'dObgBTaVR4TN8oCTKcgWtpNADiTzRbmZggNuZnpe/gE3OT2JypxcQfYBJy9feCCZeDdfkHfATczJyTzgpGfnH0imEC2hF2FCdqrgQDI9O1eUf8BJShMecHKEyQdSKemZ'
        b'+QJ6k5WQe8ApTM89kEzIS0pPP+CkCQqoCjXPyRNlHUjl5QjzBckHsul56dl5+QnZSYIDqVxRYmZ60oH8laPd+YEJN6kl+VyhID8/PeUuvyAr80AmICfpplc69ZiXaGcv'
        b'yGaymx4opOfl8PPTswTUUFbuAdcr5LLXgUJugjBPwKevmOQqBypZOclODkfPJeUnp6em5x9IJyQlCXLz8w4UxKPk5+cQ5cpOPeBEBQYcyOWlpafk8wVCYY7wQEGUnZSW'
        b'kJ4tSOYLCpIOeHx+noDkxucfKGbn8HMSU0R5SeIHaR/w/vqGhiPKZtKbfs2L85ina8X/p/8MDb9WYnHBJAHOixTrL/0xdFCJzb4rybC+v1d+Ki7/y3TQSMrDhvWSjZyH'
        b'C+cLmRSackFSmvWBMp//4vgFLf1C98V7w9yEpJtMXlomswLznSA5yExGvBf9QJrPT8jM5POPxiDerf4WkcsDqcycpITMPOE2EzecIJ082uEu3onPjPkLGReaLlGmwE1o'
        b'Is2khaCBM09kJJ1nsz+U4LK5h/IsOYVS6Y+4Cc5s9UOfO0RYVN6S0Xsmo9ft96bM6aeWbi+ZoOkzS7+3ZZTfkdV8qmX3huy5p9xz77CUm7V/yNIVX+t/AJBRAIw='
    ))))
