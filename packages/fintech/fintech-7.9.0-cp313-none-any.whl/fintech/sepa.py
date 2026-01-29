
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
        b'eJy8fQlck0f6//vmItyBBMJNEBACJJwq4MWp3CghXkUgQJAglwmoeLRerSioIFpAqoJHBU8Ur9ba2hm37XZ7kKaWyLZdu9vu9trfauu2XXe3/c/Mm0AQtbW7++ejb+ad'
        b'd+73mef5Ps88M++fKIs/tun329XospdSUFoqnNLSCtqD0rIK2HnW1IQ/BWsKzYSCTTEqWxTLLuBOoqaYYqaj/2UobzKrgDeJUnDMOdR0gdUkqmC0BAm1jGu9TMq7V2mj'
        b'SJ2XKKmuLWuoUktqyyX1FWrJvMb6itoayRxNTb26tEJSpypdrlqmltvY5FdodOa0ZepyTY1aJylvqCmt19TW6CSqmjJJaZVKp0Ox9bWSVbXa5ZJVmvoKCa5CblMqtehM'
        b'CPpvi/vPQi0qpArpQlYhu5BTyC3kFVoV8gutC20KbQvtCu0LHQodCwWFToXOhcJCUaFLoWuhuNCt0L3Qo9Cz0KvQu9Cn0LdQUuhXOKnQvzCgMLBwcmFQYXChdC+ldFf6'
        b'KD2V/srJSj+ls9JLyVdaKScp7ZUcpaPSRilU2imtlWKlt5JSspUCpUQZpAxWipRcpYPSV+mhdFPaKgOUrkqe0kXJUtLKQKVU6RQTgt9QJb8mJH/y2KjXhPpQypCxe2Xo'
        b'WFhCJYYkhgZQfg+ILadmsn2pchq9CVZOqeW7jkb/hXh4OIQ8llFSh5wqPgoXlbAqtlM4VGyXNesJqmEyCoIXloJB2Ay35YIueCZrPmyCO3KlcEe6cp6MRwWlcuArcDBQ'
        b'ym5wR4nTF63ITA9Ll8FtsCWbSznA7WzQlp+TWNDggp7CNngCnEcJhJXpXIrDocFBnnODN3oS6ukcivOoQWt2djrcIU3nUM6wnQ1eBJdipKwGT9yQQ2BrSmZUdEkOSpAJ'
        b'd+aiMhz92NPBBRWpe2WFPXo61z89PZt56ABPsyMXg9Om/PA0PJqg84Bd+DlqHmyhKZt0Fhgotm7wx+W/5FIAnn3CFp5zhBd0YBu8VAfPrwDNjvYU5eXPscoDXVKa1GQD'
        b'dsKXYHNWhmcubGFTbPgyDbrBM7AdPQ/FNR2PAhcywalgeBkeQIOxPRO2gG25uFVgR3iOTMqj5qZarQPHwEVTiWAQNDnAQdSqrFwuxV1Hw92J8AhokqLnYvS8EWzlh4Lz'
        b'bhmysGyZnKbsXNg28DkleuqFc5+HO+ALoWvs0sJC4LYs3DFb2MpCHe6PLKUt3nyM+c2/hi6zogvR20fkyUFkyUPky0ckSyHitUXEa48I1RERrhMibiEiXBdErGJEtu6I'
        b'eD0RuXsj8vdFZO2HiN4fkXIgmgiYxKXKEGWoMkwpU8qV4coIZaQyShmtjFFOiYkxETedb2tB3CxE3LQFcbPGkTGdyCLEPSF2lLi33E/c3hOIO5ch7k/irSg7ihLcVlfb'
        b'/ZhdQZHItRI2hRNKdJVVf18fwUQuZVtTAoqK6FneGDZk7ctEbqe5eGZIhhLXZhlmh1H9VJUNig4QuXPuOlMJt4WNdHf2Z5GXQ8LpKsxfo57opAesqLTPsoujPoziOs+m'
        b'SHRG9beOexxp/pUnbtE/Lmrz/5AaoRrCMc08Hd+AZllz+PzgYNAPjsLt4WmIckB/fnBGNtwVJk+XZWTTVI2j9UzQCi42JKE8roJlunrtyhUNOngJDsDz8By8CM/CC3DQ'
        b'kW9n42BtD07RtmAXaAItURExUVMjp0SDS2CAQ4GXn7CGp1aDXQ2ZmHx6wEVwOTMrIyc9OxPuQhO8BW5HU2Qboqrm8OCwELlUFgrOgD5wMg/lPwc70ETeC1vhs7Ad7oGb'
        b'7BdSlDjC3hlskY6jNjywmHi/LcfUxsKMGNEbjWiMG8M2UQMrn2NBDWyfce9ayR733lmJbEINE2Ifzuo4E6iBk6PFr1MDosNo3VwUumn978HS3yw+8KbgLbfrb2ygk9yy'
        b'ew81xuZvieJElm7fByr6dkoWfFj5jVtS52bjWePbojeL3+TceHejdNe7WS68d2Kov67jx65sknLvuuEm58INnBj0IrejgUS8gRNHg7M14OxdPBC8OXLYGxUqRyO8LYym'
        b'eGAnS5YIt9/FHEAOT4LjYA88HyoLTpOx0MN9LBnsgRtIseAyPLgMtupCZXBHViSX4i2h4SkZOHbXFT2Mh+1gM2xOA6cQGe0AG1nr6TmF4VLOCCtYqkWETI1ddITYN2zY'
        b'MOIyo1xbu0ZdIylnBLFcp65TzRphN2jKtM4oEQunnocuP2ygbs9hUSLXjmlt0zpj2mc2pRiFLszNwfiu+O4ZBmHwsFCuF8oNwgj8UNwR3xbfqekTGYTyYWGUXhg1LIzV'
        b'C2MNwvghu/hv8XvRWqGLlDdiXaOqVusQBlCPcFTaZboRq6IibUNNUdGIbVFRaZVaVdNQh2LG2s9Dl+JiCeqC1glHOpsvKfgp5m/3NlDfp7Jo2vsTB3Hz8g22t1lcWnTT'
        b'1rk57hOO45ZsI9/xJl/4wx3EZQXmu3vfYpLYwwugjtiGs0tZDyKgCkzDbBMNcwgV82I4o1TM/S9Scfn9VGwzgYqdchpwROZUF10Wl5oMN1OwnwLH4GbfBjwsXi5gVyZ6'
        b'4CCkpRTc6rKKCBE0gQ9FwUEkYMAzoBXxM3ABtCBWIkLP4sBZeAU2o2dPzqZTKbgX7E0gVfiBl0GrLZLl8ASPdqLAlRJ3kiES7PcLxdGtsIueT8Fud/BcA34R8EV4yDpU'
        b'zqMW59FPUPBYthspp2oJYhXt81ErNi6n1lDZjqCFSb51FjgD29F7DXOCG6mw9dOl1iSDF+JmL0xnYc7oAFrRdeWTJB7NknMRa3H80ep4dKkEfaRBYBt4uhRcQQUh/tQc'
        b'jK5lTxHUUVoE9kESfwmeA53oxwEcY/DIoWQkmK8guAz3g5eU6KoAz5JKqsFGcACSJ1drtOhSqiCVoCJOOYErjijUUxOHLtmghzwoRSzxIjyMmmWLMM4GynYNeIGUZBUE'
        b'DypQOUHwBDyCrs1wM6kbMeUucAW2o4kQgap6mYqAW3xJUdnwpSrEWDusEPSaToFdVJFgdgNmAp7rwF44qHMFL8DBlTTFgn10ALgMXmEY2smbF2ndmyj0VNOd9a25tpsS'
        b'BL85eOXFPx+cEZxS/+WtXoXTJ9LPP0zlL2s+nfi+1PbIrve+r37rekK1HH7945/f/lP1W+Lz+3qPD1K5kW9IEndnnUtry2Zr39g/Pe4nNW/J3nX/zNacWBAv0ye3d7hN'
        b'yX15wVe7D6yruJn4z7eaXd8Nl/7t67bF/35yUtXca+035xpPPWnn+dd6u9WdSWDx77s++qS078auXRLdSMsCJ4dzAlvRptp/Xlt/9O33aruWf3mu6AWhZt5H0hR5d8CP'
        b'QZ7RS6sLbhX8wTbQb9WnKxFPxXSLgVBVqFyyQAq3hyEuCk6yosH5iLsEFLbBFsfQDBlsSs/KcVrDpWzBWRbcD4+Do0zeE6ApGjaHxaUi0IjwKq+Q5b8ebL7rh54JloNN'
        b'WOQiYn8uHG5HgBBuAyczuJQwhg13a+AAqQHx4E5rwtB3woMWTH0BAm/8+9jrQy86/IokEsy3TJxrxFZdU1pbpi7CfFcrMXPctxmO+908xHFdjGK3Vr7R269PNJB/TTQW'
        b'8PK9w2WJ/Zrm3uZRTs4dVm1W7dZNiR87uhtFLh1z2+Z2JrdntdJGV49OVbvG6OZ+0LrLuiegj21wC2tNvM2mxJ6dqr0alNkn8ODSrqUHitqsWzk4b3pbemeZQRS8m77D'
        b'pnxktwSew4JAvSCwp7xPZRBENCUaBaS63kSDW9yhxM4VfZX9vgedehP1bnEGQTx6LhRhydAeN2Tn9Y9v2JR7vM4Ov6UQ62QRH0zjoSvD+q1GaN2ITU1tkQ7pdBVqnRYL'
        b'Mq34ASNnNcrxTSxfYr6k48dxJpafi1i+520KXR6X7+/lBVJHbSN+Cd/H6IU7ju//N9FLxc+jF2sGy7olOVMB6DeicNKMmS6rGITa8VQ61YriIlLTbTgJ2dQcEvtZsADV'
        b'Q8VGLMiM+dgph0kaHWtLIVbDj3DNanxnthXVgEefsLwt0RGwmYfqA+1UCbwKWjUhX79B6Vai57bXpg6Wdr0pACevC0DFm29QvFdbFiTZ2Uln2H3+x6wFCjc3540v1f9Z'
        b'8JqkLzgq4un3Xmjxy/KYt/JQ7JDXa5LyrBtu5X5ZEe2qSkVPudUgJ3qAauBGcwbPRXzOUiNwtWiPW5L7rRrV4DfFxfNUt96iqE/FjmVNT0pZDABqhQfgtjFsBLtiWTIt'
        b'fPmuD56iG0ATO1SeHhYilSOojIDrFXAcjZKEUwgPp0m5D5+WXIqBQ6Y56VRaoS5dXlSqVZdp6mu1RQgLBZtnZikzM+/UsyiBsDW6eXWnX/O6Ll1PdPfqvknd641iL6Oz'
        b'S4e0Tdoe2pT8saNrp+7gk11P9i0b9p2q952KH6Nsia1JrVad/p0lnSs6g/QCv6bEm8KAnvkGYVBfjF4YPmQXrsUv3DxH2KWashGr0tqGmnpt42NMkWDz5QnLKaJDU8QD'
        b'TxGPx5giWqwaT4D1hCrLTFODKJGWoJ4eNy3+UxVvAhziTpgWKcy0uJsjjO1lpeHRWGfN9TDNgFdjBfESVgJF1RXbfbIigMonuCMRnnTChpBIaj64EgmfAR0kcT6Py4th'
        b'o1FNKM5yWT2XImljYadrNKosigJHwMYosH8aSTsYwIr6DZsxl6RVB1MN+GVYwd3wXDQLW1myVNHRM0hKXqxdzft0BEXNK7YLzaSZUh1hJ9wfzcNaeRE4EQNOexPsVgi7'
        b'n4hG4z2FClZPgafgblJCyEpRxWlqHm5XQfqTQVQDgiCUyIEbjQZjKgUGJVP5LiRhRZaX82/pOlyV1+vzllKkTHAadoVGIxQyjSoEndNiGS6wT+uX4U5twAOzbvvqYiZp'
        b'43LQGY0IKpYCJ7JjeaCPJBXHBoSdxdwloZhFC6KYDqxF+uFOMIhCcVSkLA5sSyBpn9VIA1azezBJTnpqXiPFAKc20AGugkE0igi0bVkSDy7WkNQf5YbN28IewO1NWjRX'
        b'zTTCGxxeiVWVJCpNmIRQ6gkGQoJz4KwODW0yNQkeSYYn4QsMhHwhA5zCmkEKtRqcTokAR0ghMiTPX9ChkUylwAZuamMyk/iV+TSe9nMQAoPNc0DTMhK9GEGBHh0aobnU'
        b'XLBrLrjCoFZwBL17PL/SKPAc3JRWAtrJW4a7vPkQ9xzJoDnprAWkQnjYLgHiHmZQtvMywB4GQMOjoG0FHETNzqSywebMStBBagwAhxbDQdTqLMR57bMiwWYyHqc9eOu2'
        b'shHLkxTbQad6iimjw98RDqKuZFOgeXo2OAk2ksT202xCLmOLraA4rFcayySeXQaegYOoiznUWnA+B+4DXSRx8NrJCS/TnbjkpJIkNyYxuAqfR3Q4iHqeS9UF5C4AB0ji'
        b'8sDQhDdYfbjkSY7eWcwLp1mgBw6i0ZhHCWTzkO6whaTVFrvP6WUX4xfutSLfj6FNK1digp1PlcMz84s0jGHFzjplBpZGxcVZv/NfxBRaBrY72qJBy6PAfvhCXjy8RNIW'
        b'BzgE72HFInlWHPZ2BJ9JC7YgOuq3RWOpQEyfryiUMQP/nJ3WFo1kPpoI6/PXQ2Ykv0z1zOtlVeAuFFx0XWSiwy2wH160RUOppJLgi0q4ETIUXh3nW3mVvRrX5+XmLmPo'
        b'cOEsOGiLRnIBBTclLhDDrSTp5aJJ9ZPpJtzIkn1pk5ikCoTKd9uiYVxI2cNdCx2Zif9bsWtKHmsRHnOvNrG1acyfQS/otC0ax0WU/eRFYBM4RxLzV4envcq6jJuQ1Ctf'
        b'YGpwFzi8EDRjEsXT+NnFsFXBDObKmMkS9hCeklptZCQzpS9Mi4rVs9/ATdP+oXgdE3lAHFHfxLqG53mJX76CkrLIYC6bHAia0cAvQToGvLQEHpvM8IpTvktBMwvLjhi7'
        b'J1ah1/HDTz/9lJTJzdrGInwxzDDVVPCZkGmxS9hG3Dvtrfl1lOaHf6VzdMlocJ/febyh7bc5rETBMyeWcZ1SV8Cnb3DFU13EouvsbeLwf0Vvs7ZKKhlqFoa/FnRn/b+P'
        b'uV+/btx65r3fDd9YeiPyleu65j/GZQeuSbgwK3XOc1fdDrA3atJnj/xz5r75YXPvxMWEvftF908H1+u+ZHm+M+/V1JaW0p1Z1wL+0hYgHkh7fiBF7p99unjvMy0FMP6F'
        b'3o9aVk67cOXoR9V//b+KaZ4vvtVuWFn4e261eP6kVWfn/t+fNoT9qXUGiGzcZLM4dcfJ5Db753Yviw3qviwJX5FaeDj141sr+9bYVNfXLZyyJkRwnbV378aZ/750umh4'
        b't6ba8M084T8iUj7OfHlj3m+6btTucbqzd9n3H73y92/fPvh/H27NCZQ69809niv9g50hNdS+bcunje9+WlDceLH2ZntHPYz9qvrZj0LekEx9+5M3m/b/LnPn2lJNd5z7'
        b'iR++mjZFmD7zThJSfjzQGNdGgBeR/pKD7bq7wmgqjWULTrDg6ehggovK4eZJFqjoZbCDJQNdsINRjo6UhGbCHaFwR7YsI7A2LJ1LOcPLbLjVKobYnOCuDHgIqTYtmenY'
        b'dsSLrQJHWe624NJdCc69t2ylDpxKy5EFI72om4fY6S425QRb2WAA7gZnf4X2M4pQRhxMSKuhtAhrQdooygSzFrAYmJXGNsOsyGYMrm4JXVu1nXTrtI7ZbbOHhQF6YYBR'
        b'7GkBuRCYcXfAGGv+bTYOuXl2mkIS/x5TKDi0zxSKiB4whWKnX85jQokp10qYUEb2G1ompFgwtGgJEywoGlKVkuAtUgsXh0gtJERqISFSCwmRWkiI1EJCuJY7JERqISGm'
        b'FhJkasFBrNyJUD1WTNjdq3M07BfQk2cOh8j6Sszh6KkDWnN4xuxrtDmcQs+l3xi9y6Jz6aF5o4Xl0wtpXL3pdildTOMmkFs+bkLebWsm7OHdWWIO+0/u0ZrDYeEDrDum'
        b'cPyMa5O+weGm9Nt2lItrU+ptlp2994e+wX3CPkVfSZ/bB75RbXNbE5Fy2xnZ0XDLzbvHc9gvSu8XNRBj8Iu9jEIz9W4z93Fxn336Ynp99W4R+7h37ClJ9G0HyntST1JX'
        b'Rqu1UejT2agXSvsUA879Cw3CGKOnBKm2oimoDSK3H+5yKZH3txRt731T7HWbjX7v6QjvDUl0Tp5Nwdk2KXbs67Y0upptkWxEjA/H2MTwaAGxo8wXjIKJ4fEf2PDIpmmn'
        b'x1VA23n+1GFbOftnUTZeqKEsUDb7v4iyf4Hp3IpB2WsL7CmMT55eWGy3SLfchLK3RtpglbLulnNx1YU6CWVCRAvKoiOINumYQJVk1mt+9FWzdfmYA0wPGSw9gLRJL2x0'
        b'z+qtl+v4h53n7ZDmZ0cc3itgJ09q7XhHBLze8nrrGmuPfTm/vFw1xH3zL5FbIqSRW6Ku3Rhc1BgR0RdRd5F69h71h39b/+bEN1KasEyk/22CBxmuCNrgaZMt/WXQIeU8'
        b'kD2ZjeIMa/JgWJOuXttQWt+AVMEirbpcrVXXlKq1sWY2lUoxlvEkDqI2bO9un9GUctPRuTWmudHEsYwCNHtb81r5nTE9rB6nzli9wP+R+h5vhKNDVf1yGow1XzZZ0mAi'
        b'h6adH0fDwxl/Ae2N1/D+p7THnkB7vBzGano4Fw7Cs6DTVottsycp0LV4KqG/rNVTqHUFBgxQnDetDaLmaG6xSji6OejRtr5lDKm5mUnNf94Bd8WsTr3oeCY7ZPcb8JoA'
        b'HOHEOE4W8hveKpvCDXb49Gj01gjJ7xB5lVPUjaV83Wd9UhYxKNbDzeAFizUasDtMBq/MIXaIZY7gEtwKBi1NEYwZAhyCh6Ts+98n7uYo2bndZ3sYI7pZZqKLNRHdPEui'
        b'w+stSCT2xAwLg/XC4P7kAc6J9MusEzmIBG8KZX1lBmH0kF30eDorfSw6m2W+bLOks9xfRWe/xMjGVdL/MyPbhAXjiXyOx/C5/VoHyqusgIfgeNUOdhQDeV1rOBQ/wYOD'
        b'yKxKrbZlIr9WsihOQAIPGwI+QmHNxoj3aV0JegLVxdhmJnkdEdh1TIAbrLPc/ep95s3a86rHG5n5JVS/+rVDrhlW0Uus6Rt36BuRVtFfaCMjPo1iL36reH7PrJ71LSEJ'
        b'YgcvcOi64C3OYKK4See+/iN3t9gnKMXHdtXf02b72B4lOABOZGWHsdDvAMXJpME5W/j0XbweDl4KhX2wOUsYBneG52bDHTnp4CSHEudxpmYsegzzmH2NenV9UVmDuqhM'
        b'Va/WppjpcomJLgs4lFB80zOsL//M4v7FBs9prXxEnZ2rMbtLOZPbn2sIm3mNNoQlGiXSvsRe+9Z0o1jSE9m+3ujmfUsobspEAtzNq0vTR3dX6cUhrRwk9IXicRYxDq55'
        b'xLpKrSpDjWh8HLtxivmyi7Iwij2BqNgbG8UeZ72QMYqZ3azwH89MRTWYlDmM0xEiZpaSR6zGVkp+DM9E0Oxxq4Ucn3HkquSMI112IocQ9ITYh1uNrScQNJch6Kj1UdT5'
        b'snfxuEQtnV7A0K4E6bct6SLMN6t8a2opzWes7WzdZvRkQ+buwdJuxDZdTWzTJzk4WRDt0/iaYIF98PT5uzb67XN5ftKWKZ36PdZAzn2P+6afV2/WiwmFcquhrKlZ0cld'
        b'p76jsj/hnXNLdv7L5T1um7qyeuUG7u9Fb1tP61ZYH3mGXT6rc9fwfsm3Sca2tzefVZV/enbLOSLSKd/XnW9Vz0M6EOH6l1bAvslziHuEFcUCh2hlaghZ+g5DWncf9jji'
        b'UhywE17ALkXTGxnlp2VRZCbcFoZy7cilKT7Y6QhbWGCLFG5llJ8t7uAsetgUjjg5JxlszKbBK/ACPM1U2QNbykJnweZscBJROdhCz52nktr+Uo3nfmLEphCzAjQ6neyW'
        b'qS1mU455Nm00zaY6NJs8O8LawtrlTclGoWtHbFtse3xTyp8dXT4Ue3eW95QYxNI2Titt9Arso7uyMSYmiTpXtM80evr2ojl2OEzvKW9N+VTs8YnAu7OsJ90gkONQ6cGK'
        b'roruyv64gfwTs/U+8QbB9G+tuW4OTWkItIu8mnItJp01nnRopmFROsIrbaivLX+47GC6a03mXrHFchfpHrl0mWffP9Hsq0WzL/AbNPsCHxc0d/KCqT7b6PGgedQyTAQK'
        b'dxQ0Y+8mKob7PwEvEwSK64T558vMP6Pj76g9yqNcSlAs/YBayMw/frWESshaRlN1xV7rZWVMZMB0a5TIhYMNZdMcJjGRf5uEEPbqf+Psdq2Z1kzki1VCKoAvRYRT7PV2'
        b'XiMTOTzJi4otXoxtquuWTyplIoWhMVTF6os8NNGjgkLtmUhHqRVlV3GRS0mKs244yZjIloJgal6aE6590k8sk4x7VzSbWuelxNIw75s5GUzkcvZMavWiaVxUkfPaOpP7'
        b'1L9WTKfq1wWyUDu1cX7hTGRQuTsVwbnBwjZCHr2IiUxnyahFM+5YYdvvfI90JtJ3qYCSuHlxsLk+eJWCiTxVmUhtqPgbF0VG/Vi7hImcpeZS/GCuFWZdOTamMrdOs6Pc'
        b'0jbhJlXt45hG6cnJnlQMFcjBpsAMO9PI2xZMpaqqArH1Ku983Eom8iW/+VSPVx6uqPK7TFPjF1erqTcEL2OhX/6nGVZMZK6mnHpL8g8rlH1OrtCZiXw7w5UKq/JgY3vf'
        b'q4JAJnKjEwISEUlW2JQZotUxkZML1lJ3OWor1CTXbYiISaShJpoq87rOwea7ewkeTOTfp0+iUjibEW0XT/renUtpNH+oYOuUiO59zozsaH8h53qE4Jn9se+slw9rRQNL'
        b'toUcyhhMe4lOGrmT9vv3KHtNo9PqovKX3ukNSIt9+vWDf/np9QMBuV/O/bzEv/5GLGh5N2Nh/FNH1l/7XGndq1uqD7i4h875q43epi7xUJ/15pMaxxl/npz37D/LXdx8'
        b'2l/bWDcfrpXHzb2Q27aFH/iXnlJtSfLMu5JPqvYppgft9wgsm7zgdeF5G+3d2CT1B7NE9QcrY/1ffO1Kca1i9oY/3n5H3/T0VsfDOyM2ab/PvvpGv9j9e+sZ5c/deKP0'
        b'9ZEfAi+udT68ccmc3NcjPvhsToLx7yMfSi6ef4pdcLNy4eYPdgv55Z/W//GpqSvPfb1u49Kw/ILNz/2wsC7uzitLhqR1QS9O2SPcLfvwz2vmrLkBj2ev+Sz7D8Miw9VT'
        b's3127E/8v5c/X/+RXmNoLPqp//naz7q8d1997i8lI3Efa5+59/sd3//D8cVlynMu+t+Hl/1xQVjyPSmbYPl4O/gcbB4DTAVwgxkzwUOhRM8E20JBe2ZYcBrckYkETDk8'
        b'A06wGpF2cpQImAywFfaEogJCaNCEtFBOAw23geNwm9T5V4qRXyJpnM2SxvxnIXCcsMApUdUsL6qordIQpr7QLHXyTXa3Oi4lErfWt8c1pdzmUUiFXW9wDDCKA3ryESIb'
        b'EoRgq5RLJ7vNljgDtKo6/drUnao2TU+i3gW7CvQ59c3vdxlw7ve4zNIHx+uJV4DAqXV+p1ObsnN+2+KeSL0oQC8IwNGiVm2bNQo4CVtVba6oKI9OLVkVxTny2qw6I3tY'
        b'XdN65vdN6l2o9wwbcBooOSvWe8TpBXHjcjUlGZ2cW8s683vmdy3Wu07uc9K7hvSp9C7heqdw5mFJ27Iep7aleqdJ6N5Z1BaEfhydWpOaV910x5IxsUfbl9S7yuAe3sb7'
        b'xBxjcA9p5d3hox635ndGdqoMAolR4Nrl3hPZ7YX6isKWtzdRf8zJmHBUp9YgmGQZxsMnRjmiur31gslM7olhc44VBoHfHd7E6i1TRXaWoFQPqs8y9wNaEu2B5f2dWMsE'
        b'aFSdhQzm6Ek0OAcaRS5d1j1+3XbonbXSCJ4LReanN5wDb9mJduVuy+1MfN/OB4ezt2W35N6aFNKU3Rmgt/M1Cj3HAQn+CKdRrdI+GjuMGYyLLWmXECq5nDbjB6yDLuYi'
        b'HfQO9ZiKKEHvliKbY/r9tpMyGzwK8IYJSstS0FqkcvpQCmvi88eKYStYGEVU0loO3hyhYHtQ5o0PWh6J4VjEWJEYrkUMn8TwLGKsC7hIT2DHsBRWuGQzztDaKPhaWyU1'
        b'k9baBVDWy6Q2I1aJZWVatU73xfe4BzyLHvDNoGM1ZValzZseEAbCnt0soocQb+8YvgkJ8fJtLJCQFUJCPAskZDUO8/ASrQgSmhD7cCQ0caGey/gtgn1gF9iugBdWoBs/'
        b'yg9umsw4sU279jlLtw+FNgUEV+decWBF2ul0X341dfICHm+qazy4Lvb+2933rCMlfmd7/tn9z6Ltl593rn72jZ37Y8WXbjW5f+34w41SdkDK088bt+79aONS/ezqAxUr'
        b'ijam/6b3TyuXBfrc+7/Opobf7e8r6FLOnps3/1JV8NVyr5+ePLc/v/TGH54bYHf/c+qqdkFFdnKV8OqOivo559qWzrnxt+hvdnd8d/uM4+0E8ZSuuVIboiDEzppsZv1W'
        b'jki7QJw/ZTpjfnwhIwI2g0vgxDgn4HjAaBa1vhmhKVVyS1+2Y/aMxtIEN0nwtgG8v4H2hlsoPrzCAtuWwANE2YFni3NC4WCuXMYYn46wIgrgsbt4B4CvbDloBrvgrkwZ'
        b'GtldVpStK7p/mgW3FqwjCUBLpC1ohi2huUggwR2hUnCcQzlas+vhxZnErlW1GLwImhetRc/DQD+H4vFZ7nAbIwslylRU2glwPBxpS/J0ZneFMzzKhhsXoF7hTicEwEOg'
        b'OVwuzciW4d0HzU/UseAlcAFc/I+Vpg0bLJUmq6KiGvWqoqIRR9NckJsiiBTDqj3WnVZbUZ7erVYfC92NIs+OnLacnqnvi0I+FnoeqDd6+hyM7YrtWXSscMB5IP/Skst5'
        b'QwEJBs/E1hRz2phj8b3xh2e8L4r4WOhrjsS3H4q9Ohf2lOrFUQPRl60M4oRWjlES1MrZY2/09kM/NkY/KfpxMPoGoh87o9iz1daCAdqOsEurdFq8PWmEU6qpbxzh19Xq'
        b'6vEC2AhPV69Vq+tH7BpqxizPD7du4LEpJn8WFg6s9Wg16PIvnARv1/oR8cgGK5pOoO9S+PoYXJLw4P08GXXKNna8lkWbp7UXmdZKKo+a+Ic41hYpndNPj/CLTA5MUnqE'
        b'o1NXlWOfDErCvE7+jCpVdUmZataIwPw+zTH2tEkQbKD6Us5kH88mI/mrWlKOWoJq5xbhQZfSWi0en7FWIEyOLvXo4oAivzXVKTrjcdzjP67Tusj8ih9Vr6NFvflnCo8X'
        b'/vp6lzH1WhUxBPWoWgUWIxxzZsbxGRNrHbWOYmsm3sPBLAUgWfX/RZeeuBDAztGs+yGco5uEIn73ZsFg6b43BaBnzLZ63rjdhr3Mg8pKY7302T0pzVhHm92LQXMufGGu'
        b'JXdrzpKyLKYUZiCjlk6NzmIBaMTFTJvjognHwSwd4+YKPuXm1ZlyMKMrwyAOGhIEWcx7LnkFD5rMxMJqsZ1hA75gA5AzPWZp/07FfzyAQyhpNxLlh2xlbClHi703tVjU'
        b'ahvxZR1pUw7+k9qj6VmEN2EgjmpTVMRsv0Rhu6KiFQ2qKtMTx6Kico1WV1+lqVHX1BYVEU6DmJe2tk6trW8kHE27HF+q8KXa3JURlyI0Xqp6TWmRqr5eqylpqFfrUHn2'
        b'eHOHSqcrVVdVFRVJOWiWMBGWez3G1uYSRjncEvMFAyAdhoP/eIa6bUMl0Cm0MWrq92xHe687FL5MosS+et84g2t809ybQk+9V7RBGNOUchPFSqYbxDOa0m66eOt9phlc'
        b'Ypvm3LJ3+TuLbR/8LZtycP0Oh8jbI26xk53W6LLArqx0aYZMzqNsKpFQzXQaR6W2pt9vv0ZvbZbTePCoYGk57tRiNE3Q1RH9F5h+7fFvBCuGZbof91/BjuMR2BmEQSeC'
        b'b+ZteQIE3rgMAB0FilyyHxdBSoWVgh/HQqAT31ujextyzyf3tujejtxbk3t7dO9A7m3IvSO6F5B7W3LvhO6dyb0duReiexG5tyf3Lujeldw7oBbaIJYgxu3SOo71VsFB'
        b'sW5xNOmBHYLO7uMAroCU4+FBFQgUnqgkttZp3Eg5KrziWIpglBs7XbMV3vf125nk90Ht8CXtEJJ7Cbr3I/ei8aWh/1boPz+Gja4cxaQ4tkKqxG1jtj7i8XVQOsZYK/zv'
        b'q8eFlBuAyg0k5boqJmvFyziI1YYgSF5KxJvGHb37NY42pltmr7INXmvTII17hINn0oPmSU6plQUlOZj53TOY3fLH711GrNcaMV82aik9ukUTjw2C7YguHEws2WocqOf7'
        b'jIPsSv445muVyCcseUKspfetKgNxOpv0Gk29RlWlWYM3YFeoJSpTRzUIr6hqSvEO7vg6lVZVLcEdjpekalAqLUmanpSYI6nVSlSSKFl9Q12VGmUiD8prtdWS2nIbbKdQ'
        b'M+mDceIwSVJ6shRnCU5MTs5V5uQX5Sizk1Lz0IPEnMyi5NyUVKmcZMtHxVQh5oKyrtJUVUlK1JLS2pqViC2py/BGcVxNaa0Wce+62poyTc0ykou0SNVQX1uNmZOqqqpR'
        b'ElymrtOqS1Uon1QuSaxh0mh0ErIuiwpDjSV5V6JBKEM4Qm7uL3618aQhOGTe524en4raqjK1djSxCQsx6U03qNOKXFl05NSpksSseWmJkijpfaWQipmSJMG1dXhLvKpK'
        b'OlYoao6pRBR6cAselM8MTZi85rtfnp+BGExuJvwL8o5jnaN666iAt81pCERh2CIC3XjtJqwInJfjDduZC2FTJtlW7gsOccBLoIlD7KPWkbsoL5pyiwiapRmYPZtqmIYi'
        b'48EZ0EZWb+bBJqxPhcNtKJSrYMpQpmHHtuzs9GyaAttT4B54yBpeXD2XFBhKMTuFI8o7pz5VyaEakKJGVYLnBdhVLjQTbxPKmp82pkfB3VLQTyngkamJVrCDDQZIKW11'
        b'LIKeIlx7BOsWKxlb7mUfZhdxxJznpktS1jJFr4MXFjJFZ89kCodNWRmwBbU1PC8Nbs/iUXPhUR48C44kaxrePszRfYNyLfn0xvq8K7s3RYhmcuS7Nry1cuepvb4SV9cf'
        b'N0V/mlf9WcuJHca/fr3r85/WJArtvq45vnb3txnFCz9+Ve988gT178opX93QXY+0mlX0zw3WYX8JvXV3aen77V98x/Nat/KH1xxO/UnlcHfJqspDf303JXPzB7dsclIS'
        b'C7QXF+xdcyD29R2xu7el/zn+epnS7Y4Y7Fq+L+o3gX52NVP7j86MXH+iZrc8P+ipY+cDPr5Z+7H9a2/PPdPtsKrmmYu+CZt/cr4yp6Dgw/Ue/O1LT7t++r6XTcbSktff'
        b'mnFk5p61fXXyxO//fe+VOTffmfnmzJjBvu2FV36j/nPcs6772/b7XGgNt3rFWupItNF1cCM8ZotegzTbAXQ2yELg9nAW5QK2cvhgexjRdmFLBmix9Jq0BSekFSx4egrY'
        b'SlbEZ8OXnDPlGdlh6WAH3IUHm03lST3AeU6NZilR04WwO9Ps5rEQbsMeRDZPkG1j4LkK0JEJd6Zlw53FsWCnOb8L3MKGl+G+yYzCfTh4GVK4Tc+44DK62UfDF+Ep0Mpg'
        b'0p31KoxJ8etlw266EW5BZZ1cSGzHViHwWZyboXcu7I2AL7JosHchGQGwfx48iPMyJAivwqtmdR70LL0bhLFR1FKkjsMdUnISQ1g6oqs+3FWmwFAwyIVPgy5Hxo79EjiI'
        b'NHVcXhaN2nKQhn2LQCt8voQ0dIkd6EAP5dm4nRdpuB1uBN0LQRvpphO42oAbmo2dSMPAs3AnPnhhGTsePhNIcpcFY+RN0FMD7EQAyiGZPccVtjN7617xdcG5w8DO8BxZ'
        b'TWwah3IAfewUcOopqeN/0yqOPdJHDQmW5gSEfjVIsCFMKjBJbrk5hsD7GTQD74utKTf/nhiDOLiV87HY80OPgJ5Cg0fMkCjmptAVm8s7te2zPvUIGApMMngkD4mSPxZ6'
        b'dOl6pnWv61th8I34ED+ZbvCYMSSaYXT1aGXfFGITs7IvpidrWBipF0beEnt2Jrat6niq7alhcbBeHGz0DRj2jdD7RgyIBlRnxZcDLq94Icjgm9TFuRUQ3GXdyeksNYo9'
        b'O9a0rWlf18oxir2GxUF6cVAfp690WBylF0eROuMNHtOHRNM/FroaPbwPSruk3aGtybftKJ9JxFzh5Yt+rM3GC5MpY3JIK+d9gb/RS0Iemn4kAfjhTUmQUeR5U+TbwzGI'
        b'AvEv3yCS4l+eQRT0rTXXzxknQzX4BbZy9tpbaEFOjBa0A1924suDtIaftw3f/2rxayy2MIVY2Ix78KUXXXyxNoUdmH7aQH2/FmlTs7+n0AUvPM9+XJPIEV4Mdd529n9k'
        b'EuEWYYz0ENV8jBLNlpCCMetAZ/7BJfuWkFG9F5g/iq2w0EVQxSx1g7VqVZmstqaqUSpH1bHLakt/tQ0D5ecUlWhKH2ZIOIouReMauHjfYqaBAbiBCMk9sn3/ScO4RHV9'
        b'VMtKUKT2eXxHWhT6aJT2nzcMW1+0dSj8qEapxw3X0n1LmcbJLSHhr21fxCPal8eaGIfaXIEtRizEClWMlYPMyUe1vwJPJ4fR9nctHfYOf8873GKIHwVD/xddIEYvlvYS'
        b'ZWImj2r98omtj37Pm3GQvBf+S4Dw/6IHWyx6UP0zPaiZ2IPI97wjmR7Ifh6M/6dEXkFmH2nro5q5As+985R57kXkE9UPtcnSxC0xEZ2kihz49dC2/f81RCKtd02JTTLW'
        b'/HQSzX3cS6dWV5NDyJCuSZRBG3wQmUmlVSAVE/UytUFbK5mnaqxW19TrJImoV3KbYNRV1GGUcOVUeZQ8QjpeFRp1IbRYLcuX0uToBzAQCk4jfejF0BwZAkmcBBocRzC4'
        b'RbPlg32ULh6liBxYwNhCsR109wU3tyS3TZ2R6g1fLh7Yfk61nRfNi14ctTXiz5ITsCSioNuGvSyesl3L+zr5gJRDIDFszgdHxsBYWj1sMaExuKvkLja3+ungXgb3ngBN'
        b'cOf9yFeAsDVuqwy2r4NN4AQ+IGvseKwlMXdx5xa4x2USyAsOgR2sQjrcI/KhRlgrbG1V16lGHM0C0RRBkBle3iBucrbYGXpm20y9MNgYIB0OiNEHxAzkX1p8dvE1zuv8'
        b'V/lv1A8FxAwF5Lem7MnGiGl92/ohQcCvMs/iY7O0r6NLvaV5Vm37mOvPm5iJg0HQL/CHxu5rNKL0/40/9DJE6QttFOp6xqrTUFWvqVbVm4Rkg46xe5BD9iT1WlWNTmVx'
        b'Hl9Jow3OE09sXfHF2SgOZUU/qmVqbfF9mv5EU77JLfVz0U5Gf5+7eH3dmtVUA3Zzh2fgdjsL/X0tUrkepcIT/R3sqdJE70ln6bCXr/reNua4gj0B714TgB5OWVdU1IZE'
        b'uYLvHzW7U19pw06eNI2dHJPPCeZ1ZKvtVDaqdzb+7kg09j7tlbz0qbVdyEUpi9G3XpwB92KNE+xxkWaP0zhZoIXoW+oZnHH61n261vYgpG41PXIDioWbjk5dX2R+EQTh'
        b'jLibZ8CER2QuTDHNhRQ7NBf0Qv+bnpN76g2eYa0pN8UenTHtjT1R7U9+6BM8JJ1j8Jk75DaXYPwbAn9L32pmFux8yFR4iFP1W/iCDy15krZwqm5EM8INO1W7/UcnDTye'
        b'PBpxGD8yjxJN2zECw8cqYQk67B3xnneEhfT8pZNAjlgXPndSiw8SGOcOPur5UEWNuWPspYgjKrY4jzmj/nedwfFs/npsNtdqNcs0Nap61HhN2cPQQI16lUkmRcojpWNm'
        b'3FJNGWPZI/0270tBBckleeoVDRqtaVjKUKi0XlKmLtHU64ihEvMGVKKuttqMZzVItKuqdLUkA1MUM5Llaq1uzIzZUMrUmJyUjkCCZkUDzo9wWDAGBBKtuVZUdnq9CkME'
        b'm5/ZysHPacBqH+wDr4CLmTmwxXTEXo5sfpo8Ixu7h28Lz4NNWfPT2HlS0J8uKSzRap/UFFpTScvAySLHaifY2hCJecDGFNrS/oek7ymLIihwDu5VIvG5l14BL/AXyqYS'
        b'R5cML384aEdTTkGoDRQ4AE/FkZP74FWVUufQsCAN+1IoYVPYAtgEd8Fm0J+fFoZraEnPgttpxNeOSFeDZwPg8/ksCm6Xwr3gkt088CI8wBw0eRSe97ZsVR0uc7malDpv'
        b'oWyBFTXvKR44Ug0Oat7a+xxLtxtleq3q5GDpfswYRdcRY2QFRGzg7cn5tLy4qfyZbbzofVFJi/pb/LIST3bew3ulFPzNzkO8ni+qFuVH9o7sBlbnnxbW2Cr47fJ54t1L'
        b'30pXFXdoVftcrjdLXd+yM9he2uj5G55r2eCde5vjtjh97pj17bylb3mAlj+X9LyrM1bOV33j91aCj1VLxzvXbrKotXGuu7OflloTo5dsGegJmoOYPrElpXMp2xoW7IbH'
        b'ZAR9gP3TKdsQuCN0GZINmMma+bAvGOTAM86gm/ixFMBnK0e3Z10hO//AedhBDF25KWDfU+BUpoULjJ2A7QL2TCYbnuHGXLiTMSyay4YHwFHC5+FR8DIxWZXBK+AlM7RB'
        b'L/RF0+mfXXAXeR6SyB2//UvKIufQnIMnSCcXglbwvNnWBl4GW7G9DbROWkpcfGwWjNra0hqwtQ10LwVbfm6Lzob7ZMfYtC/SlI2XHeMeEdnxvEl2VCDZIW6bjRHSuo51'
        b'H/qEDIUuMPgsHHJbaGE5wpt7FAMBl8LOhg17ztZ7ziZCJflaqV6abvDJGHLLMApdUSGevgfjuuKGPcP1nuEDnGHPKXrPKSRpjsEnd8gtd1yR0j7/YU+53lNOUiRci9aP'
        b'iimTfQr/7LW2dCVkhNUo8324xCKehONE1sf48gd02WEWWXgnwkI7mvbCnoRej7vQ3sELoo7ZRv1HBiFOEeK2jxJYR7EudYoy61KRRMkeY8mP0vT+QzOLlLSu4ZH2n77x'
        b'rZv+QB6erEy+f1nrAe2Uskc41Vp1+QhPp1lWoy4bsUbSpUGrRXpUKceidXbmLmBvhlnW5pVSImP5o+vltNKenE3EUjrE2JkkLiffYj20huszTp4queNkKyeRSyTuhNhx'
        b'66N46XdM6DJnXjNYmMg7S+VxTLziTjLSzpx2dMfn2PoaGQImFUmChg/HqbDqLJckq2qwDqoyPSupRHKYCGC81opkpCI3dmpEJFllxSukZdgsgNTT0eJHRzZeMqdKtUyy'
        b'qkJtWrNFDcZtHkthbqS5+Jpa1JV4rRo1pEYXL0m8XwkoNjVH/nM6rk0OIxB7lsA9FgI6xB2JaNhkEgXKNBSZZxK3dJQzaAftcDATDmZQgfCIA9wHjuc2zMTF7IeXQX+m'
        b'XBaSgTi8ZQHmokHTkvlpGcpg05GBSHmAR73tYB/cNLsKs5ZsVjrVWjyfjZhGyNL1Dfitx/tq7l9JjAFHGE1ElpGtsFREmhXWEEENuKMBM5asCPAcbCZpINKWQ/EyTEso'
        b'lvUt7BSLlcS0sIwseboshIe0cKndCklyAz5Z4Akhe9yKI+4HrjUYyQ6kXYRJZRlchEvgljXwmDXYAVptpWxiLXgSXAH9qF64NyEjm01xZtFIGz8FNjLHaO8D58HToag9'
        b'3eG4GNRqPuxirYWneA1YSLqllodmgA64K9s0ijQlDGLD7lWVmh9936d0J1Caz8OPDP4J61bu1zdYx/TUE0UqOiumU7/HCWSoOV+Wvno4t4q3YyN9Zbtk6qHq0qRzO5Tb'
        b'/LbYv+ZYfnEfS/m29cK3Nx3ZJ9vivviqMu6ZygUBN8ISLhT4ffh8VsXpT6h7G70DrBTdv+Mqf7eldwHV92xok6eh9nm7uqsFfi2JL11WFt8Reu4OdU+YxRp5ddfvtwh2'
        b'Fq+cWd55QPCOl0OnzdcresG1LpoSNflm1lUgbIFlQy08DDZlEqHLKqF18HgkOARb7pKV5svgNOwj0ILBFbATXBqHLZRgF7NQdgm2xI3HJ0lLYbcEnCSGjzw6LzMdHJVm'
        b'hyBEyKL4oJkFNmaCA3d9cd520CQdDy4QsAAbwR4OH5xrIAV4wc1gIDMdtoLuMPMB6ajOTgJswEANODwDHkCNzCXbd3lVrEk5SaRwRL4HQS9sDotFXdmZi8gcbs8OQy8u'
        b'nI0U10mMd/EW1zWmlToEYI4zPcArdbbFUrv/aHENs+KJK2u2GG6YuMaI0BKDmCIJ+rhFMeij0h5bcWI7Yj/0mDwUNM/gMX9INB9vbZ/RMaMn5VhWb9ZwwDT0jzzONHhk'
        b'DYmyLFbePrRYeUO5uqYT9dcgDCMP5ho80oZEaXjNrbyndFgYoheG3PQO6Ztq8I5qncNEVwwLw/XCcKO3/8Enup7oXto6xyh0Z/z5urMMwmBSUILBI3FIlIgXwbwkRp+A'
        b'YR+53kdu8Ikw+oXcseJInb+lOH5CsgBmQ7l5daxrWzc0Tsl2ZHDL5/jyBb58Sf2aRa+xRc3xy14mhPMdvmAPuRPmda9/IYSjsKfpULzuFYo189DHhTkHeeHUGdv4Xwdz'
        b'KhggwTe/+0eBibfGm439sPBDooWIwlFZaWknltowZvOT+PInfCG+jn/GlyMUWeQ1GQ6193DcWXwZwq+Dg30g+1k5qG1zpG5avOtZuwVfnsYX7IOF/c3LakuLipjFxK2U'
        b'aQVzhF2iKX3oMuaIlXkphVgMsZFkxH6ccYJBoWP49TuSy9Q7LT5bTOr0v9kg5nTfbLWgmxbzBQMaXSde+n6GusNh2Qu+4VMOLl3Rvdze0v6Aft2Qb/SQR8wL0b9l3/Tw'
        b'7mefTb7Dph3ibkVPM8bP+p4dax/4dwpdvuWiyNscFLpTj9ix101BkFE0/Q6XJZrZlHKHRwk9bwomG0XxKEY4oykZxZjSJOI0yTRJJPa9KQgxilLwibdz6Ka5plTh41O5'
        b'SW4Koo2iVBTlNpduSkNRrj43BZFGUTKKck2lm+aMlTUHl5WGyvqOz7cP/EZEutbD6QzV20/+jmVtH4rdQINu49AdEeUdeFMQMRSVzBTljYrKZkZD2OuPMnzPcrGX3KbQ'
        b'xZQLhe6Emfs2F/ctnSadM0XNx1EKFMWU4t+r6485yx+aHPdqvt4+43uWj33AdxS64OIy6dv4/s4sc9On4abHNc9l3FOxTMqyhxt1Wf7gRA6j1dKUzRoWEu6H1084Qhz/'
        b'fRuF2O4s54kuqgq2lqvgaHkRiFMpuFo++m+t4GltFFZapOxr7dypxVziSsk3ubDSxI1SoLCOYykiEdC2VQpi2Aqb+1wn7QscRl1P7eNYWkdy74DuHcm9gNwL0L0TuccO'
        b'oA4FzqadSlbEzdFR6RTDVzhbuo6Oli/E6UfbJlAI48guLZLXKYarED0wl6jAAbuvjjl44u9exLAUrsSB1RX1hDY5s4oVbh6U1g07rmrdsauq1sOU1pM891R4oTgv7Jqq'
        b'9cauqFofJQ/l9iVPfZUUCktIWKLwQ0/9SMwkEjMJO5pq/U3lBZC4AEUgigs0xU0mcZNNd0HkLsh0F0zugk13UnInJaWHkHAICYeScCgJh5FwmNIahWUkLFPyUVhOwnJF'
        b'FNkhhne4hZt2uIUrIrQRy7hIyYke4SVWEz/XIeznusYGc2UmhnF1ZT7Gg7QO/DmBZVrsRilhdIfSxlGPTC1SfxK1KGG1ul5TKsHe4ypmOaGUUWVQBNZWUF7GqljVKKmt'
        b'YfQRsz4hZY3wilaqqhrUI9ZF5hpG2KnKvJx7Myrq6+viw8NXrVolV5eWyNUN2to6FfoJx17ounB8X74a6VljIVmZSlPVKF9dXYWPAEvOmjfCTlPOGWGnp+SNsDPmLR5h'
        b'Z+YtHGEr5y6a088a4TIV8831jjP6jvoyzsJu4FgVZZk/plRmRz1EODLLOcrRjycp6PhVKL0LXrTMY09Mb6bZ0ZIdkKLANT9VsJQsGVKyxj7NhM3LStp8X0Mr2EoaL52p'
        b'AlANtIKj4JL66TxLN2RzaezRVvFwFeY7GeImMhQhs8cl5nJROVZMGC/CjtWmpKpGVXbUG1tqwt+o2k1Vje5mXMZHcMF6zd8meBybyG2iwzF5KYyWrGLSkBgLuzLztuKJ'
        b'W68iVxYTFTnNkjrLkDKdXo6VWomuTl2qKdeoy8KIqqupx4owQq1mX2JSstmMwVD+6NYGkiMe38YXl6nLVUjij1JoMdKuNaUVuDQN0y9E26ZyEe3Kbb7AL/uei6aGLCmP'
        b'tS4oUBc0QstH6IgvMGL+4if0d48tj4jIkVqNCO6vBi+aqqrqKlQjNgtwS1O12lrtCFdXV6Wp13LRexnhNtShWabl0fgkKAaO4n1AWid6IlbA78Ti1EaCgUYcmfcw6if3'
        b'RwwWOijm3HoREsVGX/9h3xi9b0xrGoboq9tn9iQahIF9i4ZlM/WymcOy2XrZbIKnZ1xerR9F526enandNq1co9C1M7B9hlHk3qnoSexn96WeyezPvMw2hM24nKcPSzAE'
        b'J+oDEvXeSXpRUlvqLZRM2ZbTmnrTJ7BH3V2DwLet0U96zKfXx+AX2crZ6/Drt1IRnwyaDNvDfLXMg2F21frHONeeJ/Y9YbGsZEmbhIIa69SSYkQppQgXVslTmN/iYrm2'
        b'79e22OSZwXt4i7V+KOJf41pZuI/ZbnbPkziUPXh+jGsOy9ycnEc051HcK48z8VnIqCMPm1DkCF+lKyLbBUb46tV1tTXqmofuZsOd+gnToQfTqbKDlV2Vwz6Rep9Ig0/0'
        b'sM8MPfrnzexvu1dKnMAaqkvUWvwaTOMvqatSlWIPFFW9pEqt0tVLoqRyiVKnJjO9pEFTVS/T1KD3pUVvsQxpXWjiqsoqG1BCnGB8KeOHa1QwkMOh+KOf3aJGP7tlM7ol'
        b'mx63HvhfOFlPVYitk8o6rFgwfFS9urRCVbNMLdGSqBIVXuCsZdxXUCqVpE5bu1KDXVVKGnGkDXZmqVMjCZ2MXoEWdTJJVbOcrPLp6muRmkO4ZM0DOaKJG5qrLCJVFuNx'
        b'bSAckOGvmPGOru6hccU7MmyI1EdAoaJ2DA2ESXQaxPpN2XAy7EE0bh+Hqc2mjPH4C4LxxSYAUoxlhoXRsqS2Fn9jSFJuaf1sIENVdt8wEd6+Sq1F03glQgyqEuzKZLKD'
        b'/symd4cc8oUv8ArcXBAqS0vHHyhoyVyIzYZwZxoK5iqD4YaijLB0JLqrnfnwFfg0vNyAJXwi3LAONMMBeGF+cKU2Q4Y/HbUrNAdcgIfyZPB5FhUzl7tsBnyGmP3g9iVP'
        b'6eTZNn4ZcO8qnjPlCDrYcrhnWYMc197rWUmsifBFeMlkUQzOkYVkyvKCTeVmcqkyAR9cgS/HMR/MO+8K9+uCTd/y44Jd8LAPDQdAC+xqIJ9d6AgFlxRgB9wDLsuVcAfc'
        b'q8TGxFwanofP+Mwhu+e0+aATtSmDC/rgAYoNOmmwoXAOyQ5emcyBB+CzujTG0JgJTnMoJ9RmcHIqPMC4PW2DmzJ1wRnYVMVdDwbBLhqeglsX5WueWv8qVyfCUNTLZf38'
        b'7Ex2pGB/1TnfmxdO5QlS9izhrP2q30ckqi38Luq31zYF9f4m87e/2fzK9Z++OlKzqdV4NaDx2/KP1w7mvj3NaG2TNst/qv+L1PTUrqiq5pDUZPEHXSOr48/0R+/jvvp8'
        b'0/E11qK/xL1c2vFFW5tf2sk59b9761L6p33Xblr//pOw/Ulgz9FlCxJ93935Q/jXdn/5abj6Sq3fx3dmqOM1lcc+uJXhvLot/Qbndd3q9T++XX5+1echvw+7+ocPXin5'
        b'bl9AYblWuTHx71B8bfqx6P0KGKRc5SO78+WiYdY98YaduSGxv214c2bWZ0998dU/Ly8+o/9ClWs8dr37fNDXX+S+1p879Wsf95vnXj/w/bQPv4LP/Vhf31OT+NS/qA/C'
        b'QsvZm6VOZKlxBmjLJ6c7w2YruAdeoDgyGpzyBueYYwoOgIvgdKgMbvdbBLeFp8EdbMpuDpu3xJ/5cM6uFVLQHI4e077eFCecBoNwEPQxBxHsKYEXQjOys+hZ8CWK40eD'
        b'/SGgncl2bB44nJmeHZJtRfE4oC2QxQdb4YG7+CjzoqXVmaQ9dMwMiiOmwaE87V1/Up4VvIQNsMvB5dAHrO2Cl5YSE2YgZ1GoXApOw0MhZqp0hOfYjQq4ibQLvARPwF5i'
        b'2QQbqhj76YonyaN5oKuOKZprDfZSnBwaDMxlln3DQRtowZbRdDtZmBxsC8dTFBGcRMKBF8FFK6aJJ5TpmWMTFuwIJ9M1y4oKgS9x4SZw0JE0UZFvTfo4jZeJjf3baMq2'
        b'jAW70Rh0k20lMfA4vJyZKxPCDppiraQTwRb4PPM+noZH4anMsGB4BZ43HSmET5XIX8004DzoghsyszMzs+VwW1gm2JGLW/kU3EmFgJ1ccCZfTV5ADGgCO2FzDjgVxoNH'
        b'aYqTQoOr/pVSwX/dkIQv4w4ZGjX9ujAstGg81x/xMmGlBz4l1uAk2nSQpIByEnfYttkOeU15XzDV6OrdUdtW21N6rKK3wuAaPuwao3eNMbhObWUbBa4ddm12Q95RA8nv'
        b'C2Jvurp3+rdXoHixR8fqttU9tgZxmGnHxuShoNkGj4QhUYLRK2DYS6b3kvWVDUzrr768xOCVNuyVrffKNnjltlob/YOOxfXGHZ7eyn5fIDG6eQ67hejdQhAydfdp5Rk9'
        b'vFqtjF6Sg1ldWX2uH3hFtKYgwNuTqfeNQHjXc1JPTJ9V70yDZySKF3t1NLY19rgZxCF9ZQZxlNEvsJNnnBzSGdyWaz5XIvYDUdgde8o78rYDJfLuYQ9LovSSKIMwyiiN'
        b'ak1+XzQZ786Yc1MS0KM8tqR3yeGCDyRRrWlGse8Nsdzo5deZiwrdx7tjRflF3+ZTbj6tlnsubLWV1K8xMDPnS9y/n2I2VhES0IXNsjiDJ1lA0074eInHOfhaO58iEBVr'
        b'HeN8IEdXCInnFHf0g3tccogmZXGMJiuf91/0g9yCkNICjJSSGahg2uTKQHYM9ZCkx+hgFBWbABNGTzqTPmhjXiy9D2Hdh6ckD8RTcmJSuS+nCuONcfDGjE5qMQzCK7+N'
        b'GIjZlKpKKxjPqGp1da22kSw8lzdoGUSjY76wPEEdHo/3LTze61XaZUg3Nacct9RbM7rWy8xn81KvGQJiIKfWWdp/foGbFnNEYaIdPllc8GN+cVWmKN50uG6dNxWLIk8u'
        b'Ll63UCpmIu24F6myoruIcBJWuIk/9SRoIRd/+VRnD3fDg/YsikacEZ4Cu8FLDfiwbnHQ7ExLwJUxtqpsRh/58xauipUtWIiwUHP4fAs/LCQM1vgI4rmTNDmd+1g6vGbz'
        b'mucnDW1nbUCE4Jnws8MLmlNtt7+Xev3Vo5s3b3bhFPllJ9SFTLpsvCHWf/93jxKrQMMZ6Z5nP+z42+z/y/nEKiaE/vrmlb8Jp3yZlp6zR7xh3zsN53sXcp+rSNga8s0V'
        b'T1XxVz9+9cTyvMhjO+Zt+8P88vrhRZVfHwtRvTD4Wd47ynPrFOvnzrxe+eX387a6n3H1j7I7qSrp6vrDQOVXusLasp/2nOhZ1/Z98dWZDey5I4VXqcvyK9MP7HDx+/sn'
        b'K9eLO5Szn5Z1GXcOHf3Lnp1y6b8zk8pTl1/7oPjIm41JP3HqBzo+CuMtj9jz0/Sb127f4b6/OPhIElvqQOTKTNCOwCN2rAIXHc2fJ92USdYtNXOdMuWO08ZQnOMCdpUH'
        b'eJYsr4Yj+b19dOhhv3BMeppk50qwg8jGBWqafI6vx818yiu4LLqLv3MGu8Rgi0n2da+1EH8m2Qe2w3Yi5r1BD7zILG2i2OcJAohPIZJ5mgt4PnTs8GNbcI4FT8vgiWCw'
        b'hwE1h/zrzcfBToPbOPg42IB60vdFiKSOmNADVTmfgIcpqNEYPcBXksBVjB6mVaVPQA8s2H8X7/AFO8DTyQT6p6OGW8IIcARuDWfBc2A7XRTOB0cEUQQqzQ8qCyVrxeDF'
        b'QC7Fq2T5xLNJL560dpqwiJy5nMOfh1AE2fl6ApypDA0rWJCNoT7zOUNH0M7WsuBFqfXjCXhryuL8JZNLvkmRGnEwyXLTPZHek03Su8qJ8go4OKtrlsEzFJ8A7dlZf3B9'
        b'13qDMMzo6duaaXTzGnYL1buFIoHq6tNR1VbVXtPK/ljsNfqgr/RMRX/FiUqDW6zRy/dgZldmd3ZfosFLNuB/Kfhs8OW8QRkWwOld6d2ZfQHDIdP16J/X9MulBq9Eo8ht'
        b'WCTXi+TviyJQgQdtuohJSYx3CPSkGoRS0xaAvlSDOJI4nC0aeqJo+IkKPfonrTD4aIbcNEiu9gWckfXL9AGxeq/Y1lTciQYD/uSIb08DghTmjKV6aanBp2zIrQxnCe7N'
        b'1XtFo9Ru3gcduhx66o+t6V0zMNPgltjKvSn27lT3LDKI5UMCueXpuowJjljffsHBeMzJuuNOxpuPs+ahSxjLwgVb6UTTXt88pj+b9hb1sPN/OqmHW3qUD9zURKzMbtii'
        b'PWafRil5E1OO2pV52IilYD1eeutyKTvnHitQc48TKI8ql3LIYI7YFdXUFpmsMroRtqpER6xKEy1II4KiUQ8p08KC2GzivO9BDh5hvNtmA3XLRFIpwwFT9AFTDMIpiLiP'
        b'+PeUHavsrTwcrveMHBJF3vL0O5Lcxzlj029zOFfvGT0kYraZjVs2GD2vOwAvG7D2UoxBPp89xTSoZlO/6ilssn/IC3hALF5IUC1+2OsZLdWLlMqdmOLBpY4tJeSGPTG6'
        b'aKCglawZtANegHhgLvKM/eDWk2ecaKuxRQuUjj8xXQ2KJzZObs4a11EcVq3RoVdUWkEQzxp2vCRojVUQMU4FjdBBUi5DDUJNdV2VplRTX8RwLJ2mtobMnBHr/MY6xkzO'
        b'0AezG2iES+DeCJ9Zo8IPKfMcJKfij24KGnEoqtNi3wJ1EZPFxUw846KVmHSwbwDikNjjRN2zYFgYpkc8ESkJT7Y92Sc6493vbRBPRWQ07BmN/hkDpMeye7MHAi7JzsoM'
        b'AQldqZ9NCv19+LTLole8X/J+g/uuw1sOt9m0bBH9LUX7L6ZvU7T3YvqWlx9mmIgJib1a7SbavkfNU/PQZRbC1go6n570M+969M0+gI6YNxvNJfZyTs4aPtP94KA1nKAw'
        b'9DJYQVItPt5MyjItNlCmbV6SsS34aKC05Eg/88oCE1HMMll0f9hI3QyPGoi5FH82/vRT1ziv21+3HxLnDAlyJnZwdJ8Rnqe4e4/Ds2JYJp6CT9W/Z4X5iSRQx7R/IuOw'
        b'wqdb4YY7jDac3JeyRi3R+AMHKccyejMGOJfsz9oP+c/Si2cNCWYx7X7g5q85lInT0hOah1fsaDNbqKEf3AclHc8a7cMIPaOfpS2mTas85peAbcLMSzB1hVdUVIVPQbAf'
        b'7Qm+LUdJvvVnOjIqnFMHog1u05BQZU4f6EnVi6VDAun/tkchpgUZ9FZYM2Zql/9cX9Tj+4JuKx/clxgEMsb6omQOOX5EX85RJiZNVjrzWROYdNzDGOeDmV98GsLW9Ghu'
        b'd6yYPmwUHhSL8wc8tEbmKVnIYoiYMzZm9+0/G2NoaPzUK8aNH76twUSdST2AgXn7HVzStaRvypnp/dP13lO/R3woiTb6BR7z7vUeCLwkPyvX+yUgTuWSTP8/5r4DIKor'
        b'C/u9afQivc/QhKEMINhQVBCQDjJgV0CaRAScYew9FhQLdrABMVHs2GsSc+9uYrLZDTjJgqybNVuy2Ww2i9GYrFvy33Pfm0ZRs2b//7e8efe9+94979Zz7/3Odx48L5/1'
        b'O0tg3ryXmcbGTgNCHp1lPVWZnlHuVablDkHQTelyBil3T+ld1+AO++D/bV1dr6+rPey451bVctNmB8HFJIoKjLz/t3KeNvR0gnHPb1PlpnkLweUgqFov6IDdMMDjYJx5'
        b'/ijDF/IJ1qSrGmi8gH0bk/GCu7BawBOgQxV19ezHxjhwTlbyAr5MXoYzFMlB+oRpsoH2NnVv0NeL0BNCQ69MVRTTpsmaNk3dt5MRp6ikxGTEoeF10LkN4758gJ6amweR'
        b'VgermHQmcnx262yta3SHfXT/nNEX3VDmWXXMqNg4Og7V5mfVIBjmOdmNhnl6YRMIT2GJDLU+2rmCTNSe1w//JKVm+cKlxo2l4aq6H1FSas1cU90AwlugydQP2Lb1+R7M'
        b'53vIi+W8atvz8p2TxCjf6YUd0FwcuXx3924UA/cQzG7DO+zDn5HzwG7yzGmKhPM7rpNx0NwX/4g2A6iAHtus6tpUoseXAqtCaYlR2xEPVCIDauukXBZoKk3KhYZ3QWYA'
        b'FLfv8HbfU97hJP+/0oSIinngeUXJCW9UlPRCI9SqhmePGMeeV26+zMu1JqtnlrbVC5d2GW1rEVxbe/GStSJjvUpTWlKxiGSQgz6D9NcOCnjASj8FxkvW5RXR6RXRLm5X'
        b'a73GkLmTp7Q5tim2TdzpGd7hFP7ASwYjSZtzp5eiIemep29LIJ2seY7scBr5/zLHBc/MccEL53g51QEifnSWW5MpQmV1tYrLc0d9nhsuHoVm9bxMr9V6jTVkunOnp6LD'
        b'SaHL9EAS5/+rTJc8M9MlP7KaB/7YPDejLM2mHRiET0EXcHTALkA/5/9SlzcUFJon6pc3wS+WNzP161f5A0K58lnDd754XA35rfGHciN5N9CyHx+Pxoh8VowYgS5/JaQW'
        b'kuwhQzbVts6YqlwSQ673iBfPq64sBXPTBUUVVSWlxis+PA5SXwaWBQXce0kxDNEXg+7SRajzQOHyrDq/ROs1oSHpPqnWAcdDWkPaSrWewCb4x6DwtpJzr5x45VqgNmgC'
        b'eF1Juufl1zIcFqO1XqPgfPS5BScWkBZDZlRe43oZ1nncM2jbwbby2dp3yCB12aSm6qaPg+nk1CtDuUmlpOFb0Od68FlBBs3a5mVNyxrnt8WcizsRp3Ud3WE/+qWEHyn+'
        b'aYSvqVabCE/Db0OLujzg7EbfonKNRJypjzGIUKz+7vO6YwqCnGpaWZ8hftFcU/FpGEE19NLn/aFirqYdrG6rPbfyxEqta1yHfdxPNXGjKwyvPkfMiqpaEzFp+OcC3iiJ'
        b'iunRGAODwO7VHfZDfyrZyp4rmwUdsoo4GlCjQQyu3DGZVHoBAWPTDO0gywj6etHC8CYApN+MJU8XEfXHUD+UAlOAvlKoFHEKcbiR6FWDrLgOuFYvyJPo+2fh83tIWsvE'
        b'WWCDyDz1o5DWiqpyWU31Yg4UGxXJoeE1NTXVQKX9VBCp6GGjSD/qpauVPeYLNUVVtRXLSrn6yREI9ZiRN5VX1Kp7hKVLavqMZQYSIZkRrByyn0pgkv38lV8YKRDdjh6N'
        b'k3ePodDxVK1HWodT2j0X4FEtbpvUuqDTJ0brMrxByKvq/Bx4Yru31m38wCo7qQ+AlKYA7xNU/XaFD4kayBBQ9R9eUnVldS34KfCALLDtA3GyLS0rKy2urVjEOfUkClJl'
        b'kbq2gANt9IgKNKpKFaBMVEDpaWRSqG/lPeb6LSsrirLgcKwc9Ibu9E2DAx3MoGmoyuFQCQdKt6eBwxI4rIDDGjishwPMzVXb4bAbDvvgAJMN1WE4tMLhGBxOwqEdDhfh'
        b'cBUON+DwJhxuw+EDOFATxf+1I7t+dor8lqeI5Q9gjKReynKGihKRjX2vJeMeWZf6QBrQYe3V7S2ty+r29iUHT2ldRrfj5LrEbs8kcuYX1GEt/b2NU1NSq39reYen4rpj'
        b'p03cdwJHm2G9DDmA8d24Xgg+DGGcve/ZB3Pmf85JbF0Sb28Y2u0UBfaG0dTcEK6M7RWwLjnsQ7HQLReMEC0ZW9duG7fvBIE2Po8YOJDXusPBtVdEgg+zWHLaQ8Qo7rTx'
        b'A9O/iF6GHCCGPx8Nrk0g0VweCkQ2MdRBRS+cPbG2sPH+1oW1yWa/kbA247+RCGxCvjEX2IQ+MRfZhH5jzdrIDde+NWdtgr+VCG1ivrFkSVB3pnhCMi0GIoc+kUhsRj2x'
        b'NxzMbMZ968DaxH4r4Q/j4BAEB/l3ErFNzGOGHDhLRICbotaZaI0ab8XbODtEc7cKa4FmIbrUDx4Nfx7dZwHf1d8QkfJjCfNFMSJwrfaKOe/dQuTBKMVKid67hRkJm9Ow'
        b'uZG3C4neuwVncijRe7fgvF1I9N4tOG8XEr13C87bhUTv3YLzdgFhWyNvFxJqwghhVxJ2o2HOi4U7CXvQ8BAa9iRhLxrmvFR4k7APDXNeKqQkLKNhJxr2JWE/Gua8TfiT'
        b'cAANu9BwIAkPpWFXGg4i4WAadqNhOQmH0LA7DYeScBgNe9BwOAkraNiThiNIOJKGvWg4ioSH0bA3DUeTcAwN+9DwcBIeQcOcUeNI3qhxFBg1KkeTo58yFswZlWNUAeVj'
        b'yegS12MHVCh5BsK0ik9IZ16UQwreUscrZnSXd5lBbgG0n9oRFBdVwSg0t5Q3+qqtoNg3nTUAddOgMwcDgwAOpFZaYskD7UyNAGCx0Yi+rRDGuSKOrqWkulgDi0r6t1lW'
        b'q3RovYpabgeYi67Dvk2Mz8xL5J8qNLZJSy3jrROKZHPpvjR5jIMOGlPHhXGv1snOmz/WqkrhAy2L1NSSEhKmdgaLyNNFlZUyDcxLKpfCSG3CQ2dpoiXBsA+sEI8WCcEX'
        b'OSgh+gmeOTeVg1aYZ57BDq6WzNQrHgNDA/RKilDJ5Asr9ZM8GhKZhMQmIYlJyMwkZG4SsjAJ6SyYGWPYJ7luZRLL2iRkYxKy1YeEJGRncs/eJDTEJORgEnI0CTmZhJxN'
        b'Qi4mIVeTkJtJyN0k5GES8jQJeZmEvE1CPiYhqT4kIiGZPsSSkK9JTD9dKF+QO4np90eX145MSi0/SU/KF+Wm9o+pFOtqhd46VQJX80V0f0SULR/kOUnf54oc6XNMblr/'
        b'2AA4yBfBMVpYJZqZqbs+Labvcga1jc3Wp2JG5DCxjZ052fBsvng4X4dlTOYi8OkkY/IsyOxCmKvPc8OfPLN+aZGwK0BXhHQ2ZJ6lwiSdp8O5jqxfV/fsjo3ucyb3sAU9'
        b'goKCp4F9n55XBCZTBisraiMql/dY54KB9gLe6FPCwXI5X11CYIITF2hKa1VA9M2xsfTYcd6A9cRTlC6D49GgJBmUR4NyawBdRo9tH2Y5swIOH03eWKNRkTlzKUmCarpm'
        b'FC9VW9QjKVigLqdJzwdSL3FBKfdDKb5sdI8VUBeIZgXF8wA7TH3XFdVq1ETdVpUCWKeoEijzq8qqicQ0QyvKKoqp5TjRsLlOX3+7aEGt4YN6nAoqq4uLKvvQqZqTlADh'
        b'rCby0U6avIb+cq4Ke7wK+mQ5mauSzpiPKybnC9Q9lkRIVa0a7N7phKHHjJQLlAmZ4epKhisJM3VpLdyQW3JwfOgmeiTzFxMR1EasqwPMlThVGLo+g52Fwddjj2sfMXW+'
        b'MP8Ak6bXWTpp+tTVs7G2Jb5pcYdi3F3pOGoHMUfrUdDhVHDf1RugRy3FWteQBhGAM0V7zPXOIKi/h+6gUHAGEaC7yjuDMIlzTxZ01MLEc4TuV+pP3WDK/IxdZPIXqQcK'
        b'K91F059AOTzvp4vK/4BHiT22ujg6wQKC4ddXHw6LhF85L9sDH3+aTEAgF0sX219+fGzr2GPjdqY3JMLC8/im8W3RHF9ht9SvJa9pWZOo2927WdokbXPqclfcdVd0h4Sf'
        b'CzsVdkPUIY1rFN0HSw8dbWFYR3hex9SZneEztT6zOtxm3XfybExsE//aSfHQjgkY9tCecfNrCTge1hrWLulyHdnpOrLDfmSH60iDg9CXoOdTPWAHt09261tDdIbKLkIT'
        b'BlwDf/zYPGrVUDXfwEcXxnHg1lbzhH5gt1lC9J6KsqVEyzHSRF7Scll1lBncbhnMe92FjLE3h6GmDjDA9GBBda2BXZD6EnsZRw6nniOPF8hj4D009XfRXxxwavbfM+6r'
        b'2p8jjXSA3DH2ddFHHN4x2f/GzQXI4wfyGIic5AO4t/gJRaKrfG89R6RAU5F+Ey/j/NGpNXN5FhNK0gBy8AZAvHeCZ8pL7Wi4F1GYMExEashjMKGgpOoD+DtQyJSGa2UV'
        b'pZAgPwsgbycRDOZCBteZshA+/0LCyGlFLf3VeasIoaDXEM71Q8h/l4l0Gfej52RiGGRipz4TY/pTZg9S/+MTpsZHkEPSS7QCIthng/d3VL4IU/nGmnClAmF16VxT1tS+'
        b'ck7MTUqMSExKyHs5OX//HDmHCY1ZGGYdmMXJm0trk5G6xxuh6Rgj+lhfKWSJlHmbsxWrXFy0VM3zhsqqSsuLYC3yv68LRPw/POcrRpg2qRBdk9JZkhl9CK/tyYKVU6bO'
        b'eClKWtUfnyPVaNO+MIgOatXV82HqzLGlkhl1TU01sBURvVvD8au+VHH/6TkijQWRhgh0Itnl6dlkXjrpz5+T9HhI2o816YkXkD6mqLzUqBnUzFuqBitDWU58ahbpkypf'
        b'ouKcYFV/fo5QCQMUkUGYyupyU1lkwem5Sckv1yK/eI5ISaYi0X69tKokvLY6nPwYFCJZcNJ/LwuPcfzLc2RJMZXFe0CmYFlw5n8vCN/Av3yOIOmmmqLB05MvZ7BKJkZV'
        b'QHzCN26O7DknPzfn5crqr88RK8u0OTnQXp7OH3lul5eqvF8/J/XJpqUT0rfPhtkomA7BeXBCdnZ6atakvKRpLzmi/P05UuWBVIw+T/7eVyrTubNClkx6wUmlRM4qqvGr'
        b'9SuXA3npJd321NTkPPC9GyabNGVimCwnNzUzPis7Lz5MBt+WnjRdHkbNcJKhcs7j3znY2xKzM0nb5l6XHJ+ZmjGdO1fmJxgH83Ljs5TxE/NSs2lckgJdTV1coQb755rK'
        b'IvA0wfFav0wr6H1O1s4wbQWKu96cFd9TP6MBj1uK4JpAEe0witQkn19Grq+eI9ds02Ywom+RcyspClm8gXcqNSs5mxReYtYkGAWhcr7UUPy350hYCBIO1Q8+rnlU4+KW'
        b'dUilKIHaWP1ftlae7+rxc0Qo7jP+8WznlI+NE6DUsF5vPJ99mcb68DlClZk2Vm8uX3QdO1AOyGCTYYCBWI8yeI3Vg6AHEEW/NHl+MESKkeGJG294MhBCaxBTKcPTQG84'
        b'2NNVbJ7Aj5lmPxAagTwxgJ2fbiE2n6k0jmnZP6Zees/BYgycM5XiZ9/Ptel/jcS07X9Vt5gse2ZDfjoml6NPgG0dvf7OTTcMm0cDT0cUcnPV76Dq/kBe19d7Kl2bpT6Y'
        b'WKhtQiMXq3TlEHJSD0m3Ki+t1S/9evZdGDK6WUEeU69k6PIhWOys3L8S1shGNY3q8oxrczrnfsK9PfFqyvmUjuC4Ls+0207vub/j3pB4LyC0LfGq/Lz8Wt7bs67P0gak'
        b'6V2ukRdEDb/qfd67UdRs02TzsZui28ltf+bOzC6n6E6n6PbErpjkzpjkj50m9fHQNnADhKq0lymn/GZZeZxVUP+WBriH/gtgOmMRyJtH1HsKWB08A2s0ixm8tesroP1g'
        b'wEnd7okxEDKir8mLXKB6AsKKYJV5AENDc379uWCgz+HuwF6fmjdvc3Ttcgwg/6gpaVinZ5iWImrvu3o2Juxe0mD3jJzNe5GPdRm03QzQTwRAOQEWk26I6L5UTCvawDaV'
        b'laVV5EsHWNumN5bDh8oG+dAuz2GdnsM6nIZ1u7pxEB8ZgJQNi/dcU6LNBqbndO2UDh+qb1nd1gd03KpHcAAdlCpd3E4ITDrpHILbJ/ktnIGiSKc6qm/gAFo9nY5xGyiw'
        b'VEFn0FTLpkoGHS/psK76FA6ws0LnjlnywEGBR3S5n0KFemz7bNnQxk77BkO3AOVJe4QeG9MdGwm/YWPGa+sqoEbpkfCbNWJur0ZEt2pEsFNDmep7rE22aST8Lo2I7rjY'
        b'9tmPsTLejpHw+zjmhm0cbgvF1nSbRjVGwLdXVQKcJcOBIoxe2POR6hOWPwDIQP2U5TFBFjb237kobLx6GXJ4WMIyPkMpL3juQ7HAJ4+tyzLQjo8FQvFxz6YmN4rDU3KP'
        b'B0rueI6ZnF7qFYicIx6KJa6R5Jotxx/e7ZQG5OEZbF0micZfAhG887hLwFYu7xWwzqMfioUusXXJD811CUyABBIM1OdEijiQYjyVgj7Y7RQINOdBlOWchyuBXM7xHFyp'
        b'/2P8lRFwZZTxlWi4Mpxe8QqgPOvAOe41ui7DkFgwJBZCE+OfAhmdEjgudprBvQKh82T2oVjskwt5bM14+t+zJ53+KBLRM7Yu3fCyDHhZFkfQzsOqwgFWFUFhVQN8DF+A'
        b'IKjP8LqsbzkSd9bG6xuJ0Eb2raXQxp0DJVHmmCN4b6ZVhP8imxpreRreGpqVoQAiF7xDyITME6P28ehgPzeV8OfRLoYDT5jikzwYlWgWRWx66DtxlYReERldMaNXxEZX'
        b'zJUS8qxFviCGBezSK+YqS6U5uWIFpNsxAsAvkWvW9D4lUVfZ5AvJuRU9t1Vaq+zKbchgYdvj2KdjzKhQ11asJXKb+EfSG9KCN829RP8y6FLTZJX6vn9aZKW+z44AjUs/'
        b'SJXzQ5OI9m49FgUlGh7UaAEGB0WVFbVLe/z6bpSCMAXGKBu1zlouW0DRjbqXmOveobObkxlRDHsN8FY93/B6GADcuQHA23ePZbevfI8tdxgabPBq+d/vs3gJBt9PG1Ay'
        b'3Z7aFtDoFzPMAIDxHzmnmj24CCpAGtRDSsteKqVyLqU5z0lp6+Ap6TUkBU3pReHvBmfX8dDNFwwsAIwDg9YDqvFsF+rNF0GzSeRMK7SukR32kT8ldJwIR2UcBDxOB6t+'
        b'6jQvKdVYdoKgABTSIdy5bWOta0SHfcSLaLnznqvlDpJRnKa7B4pwvG6iacI9oze1sGafbTVVYgoUY024WgayhBqwClBqezmlMhh4njnAHJE+Ywe91kBzRcpxA7IZYGBG'
        b'IDbyRuv+z+Ta9b9msMWUQc83DyiFwo3XURYA0fNcA293UJ8cDzKNXlJdytEac9w01DmCjh2QqkBkVjeb5btFqoWpgO1EBb6tOYg91Dmir9XUlFaV6EhprIyS4KIOaiYm'
        b'LCop6adD02pBbuyHGglQFFojfVtC21Z3uY7vdB1/38O/I0Cp9cjrcMrrdvTpcvTvdPRvqT2+tHWp1jGy23Nol2dop2cob0HiObbb0//4ylZyFkNB+Xlaj/wOp/xue6cu'
        b'e/9Oe/8u+5BO+5C2MZ/Yj3xGiwScnKFFGrW+eX0pH/q1vSTIJPeBvpLOL1rgO20YQ8vbvbTDXtZfFD3p5DydKAIQxZGZwqoFESRJRybFjWGqh7zopCdHkOnBYcjUgioj'
        b'M1+1gLtSxnctAlU6LUXD5L2HrR1g6i6ura4l2vOAX0pvHYUvHar/0vOJWs/RFxLbFjanNKU0Zx3KOp/Y6Tla6xrbYR/7j7ueo+mgWydVmMtFPbam4zUde7gZDYwNWXL7'
        b'AWclLQw/IeFqsKHyGhR4qs+rBHwxqZbolfoXcIKtAvwpPYBmwxmAbGS+kYhs5ESZdPLq9IrWOsbUJd5zlXbKxmhdx9alGJ1+I2JtogCoHgnYeK8nEjObUYBl9/2OBMf0'
        b'MuTAqYiAS0Qb8CW0zqq/hogv4s1hCpZJxGfQeluzDHQGvWmiK+oAno9+Br2nR19dkfwV0r8ihVglAvS60kxprrRQWiqtwB0OObNV2intlUMUNipxviBfTPRA6uZGJckH'
        b'v+9D8h3y3WPEgEUn18xmmROd0slIp7SgVzhkuitFukPYjYTdadiKhj1I2JOGrWnYi4S9adiGhn1IWErDtjQsI2FfGrajYT8S9qdheyKTud5VzRB6NyKSmTXEAMhNZEew'
        b'qiEkngOJF0jjOZDvYnlXNo70nHNk4+TDKCN5Rz/g417ns9Mm3zbfLt+efr1jvlO+c75Lvmu+W4wz5/LmFVbl7M5MN6MOf1yU8tGsMgrSIzkl5NzdGLkfctHHNFeGcTF1'
        b'zm+MYrkqFSq38hDS3wzrsYYmpgN2VxwXQovM6WGz5eIewaSEHkFqUo8gSUl+83oEE1N6hInp6T3CSQk5PcJUJTlLySWHiSnJPcKsbHKWk5HVI8zNJgdlEtyYka6yhPFa'
        b'OCk1R27TI0hMVwFpCXkdeWVKbo8gI7VHkJXdI8jJ6BHkkl9lkupVGmHiDBIhn8iQ2s9WkmK9oTcfJ9A7Gge6XIZMJkR6N+OSn9DNOHCY9Js10Q5UT+kqytIA0hc14a3o'
        b'NDSuWrw5W4G3ZYJfTr03zsngCjNUkUrJKjPCUjMnp5A2l7YQbwKWa3RCxIzD6+zQpdmjKj6XRIjVI8kr/b6/erEYnE/uCHRCD3DDnV/etv/lHUb8ztZjOYtCimMcM2Lq'
        b'9rLC9ZHv5J2MrDnGMg6HxNMneMiFlCBzGr6Jj1ihE2EqeYqOQ3MIviFEZ9iFnJPHBnzJF9dn4y1pRIaN+BbwcB8ULHGUPKas9Qfw5emoPq4Y7cA70sPRDrTDjLFyEeBN'
        b'6HV87IW6NgrddDKuZzrcJowkajnDu0T0ZpxcG8PuOg6lo3K21iOnwynHGLOpY0jhxkgzA7hUBQ4+BqKTpLZ3vMtAgzCqZpLwFaGRN+QKb5aVgptA6Y91E7hPMpQ5ZhUl'
        b'LDZW1vTOemEQ4UidwVnvHNEc8RzJHDNSXy1JfYVuwIx0B9AFSPo47TXPszKqvxak/pob1V8Lk5pqHm9B62+/q/r6O69v/dV76NDXX2mWBmbO+LUl6HJ6Bu9cbTI+jE7g'
        b'uvBwBfiQpb5YSU1Kyc9ZjNanoDYhg7fXWOGGCXi7BtjnRk7wMjyasgy9TZpA+BSeXjgNbyPDzI70qcF481Rz0kBEDLqOzlnZ4I3oDWoJUS40g5yzX7NqWYZoij1DHSqg'
        b'teLlanwQbbcxcByfZmn8lbXmDCnkSPtaTWXqtNXc6IbbBLjVxI2sAjfhTUacx+AlfrrSbOlq/Da144pFZ0amz0cnUzPTw/A2OctYZQnwsRR0QyOD9+3MEoQCke9WvBtd'
        b'QW9ER0ai9YXpjB+6LERvZWXTREvkc0LRUe8soLndlkk90fOsysGK8GBcFxECznKr5eb44gRvDVRRzwR8El0rTMf1qRkREkbiKrDFa9A+WrMpufNoe1xXgDeEQn6Hkwjo'
        b'hmAEakAnqMgSdA0dD8Un8XWuOMwY84UCS3xgNvXfi7ZkxSv16eM3U3QiTA6mPtpzgvWCmjHoENptObW6SgOtIy4GXVTK0WtmMBEKxm+Po7KiG6XT1BPwsUX4gohhURND'
        b'VIUmdIH6MUaH/IjaUI+3hSnwdvDyUUNi5QWTsq4PC8vMT8Hbs3W80xnogK/eaR9+XWhNXlOPtnCuN3bML9S5qcdbMsgHO06KHSPEh1e7cE5891WjC6Foi6tOcqJspgvQ'
        b'vmR8UwMTXD98wleJjyvBrQd56Yk8Q75PpqkzTLa9WQ1eO1MDE9NAV3QV7wZrCLQHn1nGZLJ4D/XREYMOMOR7zi9eRHSkzYvxhVoJY+PpKRKgJrTWUjMCnnjb2lVNbpB6'
        b'HTYlGJ/D19LCSb0JS+NTMmQu+Qq0G1+zZNDhhZooaHGBpaE5pDaSzCGZVR+BdyiDg0mfXBeRxecUVzvRGnTCginAm+iSXghpJpetiABn8BV8SY2vLkTbFqusF+IrDOMa'
        b'LUTr8XlzDVjGjFyFj+J6Uu0zwxUpGVlixgHtLcMbhOisBK+nLaY6XARNXxZppg4LmyZmaGYE4bV26oVkOoXPT8I7SO0JxE0VexNzWDWsLkdEb9ub934ummD/t1Rziwbr'
        b'lgdbPIPi6qZMnlUzevn50wf+cmjs9D+p4s+u2vzD/OxCj3ctgq8HnHt043d//Tr1a2317WXSSPRB8Jrfxzb/9sFltjfsc+aS2y+bfydKDhH93SM+ddXP/vFO7ip0yIr5'
        b'MO+Tc8deWbW19q+r8l61DW2590P5Opsvg88vi/VYvTN3/zeOe/+Nr9aumBp1PWB1+tfKsnEHDtwYtoq55jji6V3RqOGz33c4d15+68Fbko2ndv/F8j/HlHfWHm+oyom6'
        b'/NvMJMWUD1s3nhizadaeT+5qftvuc4xN++TJ6EW/b3YoVdS+kljV9nX6e5M/zPnU0mLG3Bn3D+J5S61euZn4Zqn7rW1zQt2izm//aPbCrN+sXnTt51rLRw2a5NWVQ8Ni'
        b'vxoz4zePfhV749Sif3849lLaxuGnww795fDYa1EngzZ8+emBr++Hf/2fT/3evc/mv/P9P26rrN6ueuLzbtWVT5v/6ZZTpfT+x7ivzn5y/oeq3967XXn3wvnj08aMcl3f'
        b'Y/W63WvT3923rTXgZ38W/mVmY69F8Csa70v4w8tx9ruvJhZ0tbx+9Jc3//jbzvGjDn4VfXLI72cX7u3wXT4u4OM/LI7yXZT5w7Vvl33V29PiWH/WOnb2EvmY998omPXR'
        b'EckH4y922rW9+QPzJ9ui3F3pcj+OPPs0Ol4BuoGxZuDnRHSDUeHUo4qn2h7XC33D0PaIrPAUIBE/J8Bv5KILVDXAF9A2K46dG7+KdhoxdIvMpZMfQ5XE1ybhZlS/2NbG'
        b'UoUvq/EVu4m1NhLGaaFQuaz0MRiazUcXstPRqZrscM4/yChPSkGek49O4fqMtJBpeKuQEeK3WHTQGrVz6Tajm2gvaeZt+WFEsZLjOiraWQE+ipoXU6UmDZ9PQPXxpXaL'
        b'8JUafFlD0rRyFcyLROcp9/lsJbqI1syh9O48t3spfo3mia1HKtHPwkLwW1PlCtpdMoybTDQHHUUnKFU5aidDTLo9flWRKWEES9mxE1ErpSqfPBvvIQ17C95B+tQ2EFs0'
        b'mkXn8R60iXvwYC5uS2dJ69+SQZ6cw0aopjymrooOkaZ9Ro1OpS2yXqjBV+3QFrTVztzGErfbLSJtHV9ZvJB8QKZIgq4vSKQM9HjTeNQeGB4ajrdlRLGMZDqLT+M6dIsm'
        b'5LKkENfPSEpBZxhGsJJNxvvQxcdg9IaOB2UiounVo9MpmYgMxgrc4gse0z3QZdFi/Dp6lX6IbSRqQfWe+Fw2OHEnQ1QG0fgmCPC+4jm0UD1wqwswwENPswTv5jsblwyR'
        b'DXrDmhPvANqKLlWjE6g+AqqXmJEUCvycF9LH0Tp8GK9F9dNtI/iuUsxYZQvwXqIe7KIU+qRLI0M3qpeWkQJA27NBbyB9GhnNJYwUvyHCF6vQAVrOAYI4VM/m0WhcFbUl'
        b'akliBl7L6bbbSJXYlklGS/Dssy2D5FSqwBXvRxsf+8Lt02htPPURHq7IyshG24aT4WAHieWBD4kWTkaHqLx56OhCVI924obsDP34ZasUZuIr6BrNsFDUMgTVL3LLVoQT'
        b'jSddSCrjFgE+TpSnnTQ75Oh6Laq3xW9mp4WlEhWGMR8lmIv2TKGObl5B24gM3B1Ul80lkFpUSCpmSLAYry0kpcp55CEirAXnWPbZWWFocwQ/cohJllwVi/F69AZtHdMC'
        b'SbOuzzbyMeWAzqKmZUJcb4caH1MlbytR46+jejvTaQrajHZE8EsClVn8okAoGcS2+Vui5mL8Jq2teA1uW0nyo3HsQI+DupghlzAZjBm6MAWvofWOyHZDTIqA5B6pdVdx'
        b'M/nKlEy8XcK4kKb9Nj7l9j9019OfTaGFAZ89feYj3F4LnZCcE9AJycNabzBjCmob2eUa3ekaTWclvPPGB64+wB7Y5Rrc6cq5Sk/WekzqcJr0uauUuoOM6JRGdEmjO6XR'
        b'7ZOuZpzPuO1w27cjJvF2qVaa8aPcRH7u6t0tDWob3imN7PLJai+5uuD8gtupnSOyunyKO3KLGyYBHe3sptld3opOb0Xb4nMrTqy4lnBtckfE+NuuWu/UhuQH7t7N3k3e'
        b'Xe4hne7gA959WIPkU1dvzsH77RGdOmqRbmkgsBW1BbUP00pHNFjz3LW7VzSIuh1dGxe1lDet1joqfusRoFVO1U4v6Ags1HoUdTgVPXB073IM6HQMaMnvcgztdAwln5x+'
        b'NZ0mkKb1SO9wSn/g5QfkZi3LtV7RDRafOnq1uB73avVqm9u2sMM36pq71jeBvPc3gaFteeemn5jevvST8PheITt0InB9eyYC17czOZKRQ9oSRoRoX3x1+dXlNIXE24s6'
        b'AzO1HlkdTlmfO/q0jPl4RIbWP4P/vDGdgVlaj+wOp+wHjr4ts7SOUeQlwWHgqODoiq6gkZ1BI7uC4jqD4rRB4xsSP3EKeBAU2pD4MfmVBlIjPL/gNs9Ov+Hk3E5v0Mfd'
        b'0ZnW8YaDHCvwwVk0in/Q8djW2OPjWsd1+Y/s9B+p9R8NkWXdsiAamX8Fb6w3NIgzHwyI4N5o5M6T3+SjxoW+nEBysKvr8hvd6Tf6WoDWb3yDaK+d0bTYjqel0QGfRLB8'
        b'rwL2c9U0WFmxKi6q1ZuvStTF80oXlL6wOwbYSSjk/5g4ZYA2pQJqo5swrYaZwQ+kCX2nJvPqbPY7Bo699Pgj5tdqUFmPSqKZi1bjhC8Bbgb7WvqZg21ymvYFut3Nf5kg'
        b'Tf9786JfPGPH8Zfk3n9MEa3BgIvU8zNwgst4Bn9ZsKq0qCS8uqpyqfwlbA85RH6PVQFvE1FQUfIsAVmRCRQ4/K43R5f6NGwgu4oKtUF6Y3Ffxnbgd8+AloKEIiKhkU2O'
        b'Tx41qABzCr2N08tKwsGTwWZbU1tdVvYsacxEJgUaQZH6mtpw8pgMzNUNJh8gITU9fWnx6NbR8OfUNEsQzAALDqGw4IoyHge8AFDcpPRKq4CEo+SnKTySZdYFRj3Os8Sz'
        b'AfEU+nyj5hYAVS4H/156W6qfoiBVgc+pUPYgigHDHTS4o2BTgYzT0u81FzLcXjPw/MQI+AU+uuWmX+BjfYjARgt8rMlSHhPP0gW+flcHX+Drv0AtyRqYdJBKx1IfvcBz'
        b'o/PKK/wJvfKulws+m0ASt0w29jtrCvtVy9TzqjWVJbDnTHo76pJcVlReBGBhy1qePUc2sbK0CEwfZImUOQIqBu+Ultou8Z7Geeh/hdqSdzheWJin0pSSIavCuOXp+gZS'
        b'53WoQepSzpIzEVlqbHlh4he9sDC5qFIN7wNDOnKBs3tQW1ZDWyoGooMSUjkW1BTVVsytANCPQpZfAxEXjVSMUiyhMoTMr66qrSbde/H8EMsa8hR0oouL1CaOgXWEGeD3'
        b't49XOX1915ewMKvi8vfvCagnjr80TLtYrK459IE9sv/ZGos8t1FaRm4lsFWckrPUj5dahF/TqeRo/UpTjRxdmEBah72udfCbsqKy8tLangCTwVJdXFlAv4EMm5Cp6nEK'
        b'iEX1aHgeFvYXyRgvGTAOdDgZr9/zOClTrYNuHRTq9oFVX0BvAH7gnch1dQxDPTB+WypjWYcfu1C/U+LLtFqFCQdm0S1jdNtJdDMJMGpCvd9F0U/od/EFWiopx6/PdgvU'
        b'MBW+6FH5S+Zi8RFSji0/s0clH9xhJL5bR1tHNvzq9j0Bk+gv3H4rmxQpnWYdL0J1ujI1KlDcjDZBoZ5eAp7GdTlt2HXX8xKKytQvVMBqvoB5FsuHK2RMUGjb8KPzGxL3'
        b'ZhuVME83az/Y5gzAEIz3Zr6G0v47OUh1pQ2evZaT0nb/MU696JRbwO0enETH0K309Gx0MDecZUR2LDruN0IDe0a4FTcx6aFZ8dVwI5pFF0ehMxWL1TtFanAs8Ho1e7H4'
        b'wAey9+zv13xQgtw+DP55w893mpVsGnYwUhy9dunWIVvf+XBZRoj1oQpmu0CiKSrQ1erBNsQMWBULfab2uAyc2TR7eR7ZbpH5t3NlFkNCn7iwQ4Y9kAV0GhgddWkOlLsm'
        b'aap6IW8fkoOjLm/Jq58Uk7y1+DF5+6VgMPLauXwLot5LGf0499OOJGUv1Hr+nfVIqIYW4fP504tOtqQYudbjRnrCDHffS5bCcgmTkSZ46+Yi0nRgj3Ue2oJODbwgMmKO'
        b'KUpCvyCCLwTLBUb5LaBNyQgj13fLk4LjaMm68g0n2Zdx8xwAH8cVq3igDtIAfjJqOBR+8i05BBh1k0+SfH9cN6laxwxWuIXM/1xJ6Ncx9h/gRFl5FYuSlwjU0H6XvW5/'
        b'sfjQBw2/utMkYXZNNNvDns76lQ402Gfo4kCDfZd8OLQgLRALrkB6M0iBeP3IMYrCfr4nrwkyHqPSf2zmD96y/i9kfj+AQ3+ftaRdfXspTki364NWCyHvKQzB1zo+Yyhj'
        b'7Sarc1Z+6JQ88duTkTVXyDMzhBmTcuRCztfo2mTYmgpLDRcwognsuGnoMjo49zFsp40Wow2DrURWZQ7Y8NDmaM6D+PHleCPnNjRcwphPdsM3BWgnuo42DFADKL6236If'
        b'BdbSGiDjasDjXKgBOnBtl9eITq8RWq9RRtTdL14xKDLsP+QQYlwxJv9XFcMYXeClKxuwyhnnPCC6AIBFtpRaVActkuQ7UsSBHmCU757vkW+W75kvJOqOV753vk+Mlx59'
        b'YPMTog/6Va7+6IOxWXRMrpiG1xhtia9EzbY5Ym5PHMoHHcSX0NtWKnwZX7ZzmgP7oHSH1h69LsA3bMUagHPgjblVdH82hVSMbHQ6bEow3aAtrhp4ixZvXGKFLg/Dm+QS'
        b'KsNYdCpQDXurjHQ0bmDQVtSKTtE76HisI76oIVrLium4mUE78Tm0g95RDUWbrfAV0iujIwJ8mSGP7AvlFJDdQ/EZdS2piOgoOoDrGLQRr/Wm+65oswidtoI6U8jgcwxq'
        b'zMPt3DON6JZIDU6x0L4IvIshY9Or6BDdwP3DagnzRa2UZHGh9buefhxEIh+dyINNa/KmZehNfJQ8tgy10617/1hUz30MbsPXuc/ZhddQqMdyfAAfpDkVTIS6aLqLjdtr'
        b'VfiSMiUU9rO4rewG1GixEr/BaU/oglQajRuiI0VDpjEsyQ28ZlUk3eQmbfdoBg/AuEw+mQNh6GhyJ+dMxXuj05RmTD5ulJCCPDKSIg/Q7jmTo8lv1ArywVHoShSno5Gv'
        b'AuAFGeUjkvEOJgJfwFsqv//hhx8sp4uYr2Y4MMyEQuvv4swYTTyJrsAX89L1KeG6lDAAn2yLSMsPxpuJCMpgOd4xNSU1E6AKpG+Royu4xTIXvk5SZTPb11szARK9gQ+u'
        b'BLSWUcyiYXKoT6Qj2hyRzWeRsSNtqEen0E1rfMFaoZlDXsLiG1Y2JPpOG7Qm0lyM1+TjIxK8Pc8m2cHDfGwuukkK6gg+l1S+xKLMdaElviVZbI62WGSjJndr1I5fxa9H'
        b'4jeXy6W4bowCH5Cg/RPl6OK4GNzkhhonBGjAbBHvxq/j42K8Fq+1YaLMhag9H12YgfdK0OZa9BrehPaGoPX4TbwDbc/zrFiF2vAaT/TmK36e6CqpBRvQlbLleL0wKpjI'
        b'sU2Kzyc6Zlq4qKCS0Zr23ghPtsNzvoixL1yZvNSF4dBBzQF4I67PRKdzcF0q+fYIvJmcZedMNwIyoDMpWZmZAHhBZ/FVq2IPvIO+8djkFGasmy9LVP60nzsUMBpYk4Yd'
        b'RnwYPqLJgpFZk5Mpc+ajXeg0KYVWNgqtw2+MiSaFsbsQXcan8YH8IHx0BpF4jXMeWleK6spxC75mNg/dskdrJi4d5kPFtMfXlg4gpTIlPE3s4Aw4O3RCDv/OoWukdeFT'
        b'FvgqakGH8+SsRkoL7xLaDjWAjEJ4e41ZahjpL0gRu5qLIl9BxyjWCa/D+7LTw9MylVbSFPiK0FQACYVOoQg/HfaIPBeWlqFIDQ8hFWSL3LoCnZBpYCQgvcFmvDb0eVAQ'
        b'Mx0YhBT1OSIdNIrFpHqGkh6MRa/lMAK0nZ2I90RowFNhHtqwODSF5N1W3Iq2Z3KNICItNTyXg231hSRx9bgGuoCc3PApAgbVu9vhN9BhtFkDNKNoXzY+Z7UIX6EfQtrC'
        b'lGAi7Paw4JRMdD4X3ja1hutpyQdsS2fRriRLdCQLbV9liU7iDcwo/JZNHKmK9bgObaN1QOEuYAot4Kyw8hf5YqKqUTxTPHoL7Ukn/ZRuA9UctwtQne0kWkfQNnw+QJkt'
        b'z+ScoOdPHQCRRrqdUmt8Eq0hpbsLb50lI+r8NfR6ii96O8U3Gp0TMaTrWOuAmtBGF1rGeIMbUeEv4ot2FmPxa+b4gh2+WLtQwzJOamF2bSHtWF1w40wldFdCfN6S1IrT'
        b'DD7txWrCaPGjrb7p8nBcpwwhJZ1FxArua283W2aO1mXiWxTPJbDDTUoXKdqWh7flk7YhDmHRAbTNiiY0O8DbapEtS6riBpLMPtKXkOp/gJZ2TgDpJOszWHJ9k+so0l7Q'
        b'IVynARWANOj1toC3O0h6dn5b2mqGAJ/Fb8lork4YS7KjPoNIJcQNK3kQBd6H39LA4DvMXZ0OSASfRIpFQG+j7fQpfAvtFnMwIjFuXc6IfEhFw21oD0d6/mroKwDUypkJ'
        b'UC10UsRY2wudI9FuClVCm2ajE6RSyyEL0InkTPD/zgEFxMxQtEZctlJDZV9JRok96WhNghF9Om4UoL0r8QUN6HYzzdCB0OBwdB5d5He5rcuFdmTE2k3HtVXoDN5E/d6T'
        b'LvwaQ/3eT0NvcXC1m0mRuD48i+7kS2YL8IZg53G4gY65EzzzcL0iLVPouIIRjWDRiUn4VW48O0EEPgftWVg8hX7z0Zph9HW14aQ06uEGXouOMKJxLKla60M1sCePjpCs'
        b'bwzlGy6pntBySa5NYHxJJlrgDahVEwk6BW6gAODN2Vkkmc0RfA7R7EHr43U5lIXWmpGY58fShPFJ3Dg/dJxakRomJ52PxWgBegO1zaP3pGjTeFJ5L6nxRTNHT0aAz7Dh'
        b'UehMxc8XfS9Qv0KGyyeT7m6bsqD6yGcO8fafLv9syXHxjE/T1qK9r4WvfNS2YUbx1smORwNuXkzdvWregY/fjbg/8tuL/5FsG4/f/uL+wqv3z1vttPvFhUcffhh9Mfri'
        b'rcr/DG3P3vyv1o0r3o05tuPxPz4NzHn92FZ30e/sxttX16g2/POfHr5XU4t+nrhDPl09b8iwu5//8yOP9Gsevx9mWTZaHI3Cdl+LVc0IH161bPff77zr6/OdjfvIGVs+'
        b'Gxd/55dN0vhX7c9e/OMfJd/d2e0Z9qe/SS3P37l7v24SG3hnscUv1gftdvjyPc2FnBl3/7LYYs8Xx9YVrGktTdp6PefLA2EfZTZ/O7LklbsLxLHS16b7fvaXgJbfBo71'
        b'zTrzfsTmv0hG7j961PneiCO//qOy+aOob1I7Dmu+Svr6D8Mvnnhy+WfHNzRd/IyJ3d6mLLKL6Kof8lXK1jnDS4pXbRky/8nUS5/NiPa8Ejny10QnvFZW0Tr6t+tUHysv'
        b'Hbm9KHzKkXvKw3tn1888Wblek7J46i9mWX2luXHnhsuf1rz9h87qf4z02lE0xmHlGI/oU8Edn5jfUMz1kiw9e+6TM0malcc0U8q3nT97bfdh8ytDztjNu38l4eO9Qz+Z'
        b'7+iR/u357DGqd9f/fPwPca6rdjlrP8r85vW2HUN9wwWZPbsXfjk6MHbU3J//1f3SQtnRpQ5/cL/z58rFp61sH269tGTYkZ0VVk++aEXJM38ZefK3vjnOYZ07frcyv3tv'
        b'rN0pp0Vj710euuQvR8b9tVA0yfLvy4tXTjk8RVC/8n2/t3w6HpW8duMUe8WvqL7uzF3He/Vf7Pnyks+86oj5/4xbNXSJxv9yzBfLIv58vXLq4dFt6Z3fNcY1/7uw+Ph0'
        b'ddPB38sv/fWOy78sPP6+9d/TFhTcifWzWprwsfnIOM2vf3b3u8D9FwIeW8/+8Ou9YeX/to8aNjE79Mtvb6/OV3465m9lLT+znHho90WHT1fvfKvh4eM3/LZYOzX85djR'
        b'ww4jHpwYsy1urd/Z7E+urt01UWN29I/mgef27PJNmxMa+F7w0qN7Dk2w6FJWhX/9w6ePv27+g2jx45R8t1XZ97Zv/D667ffLtrsvP3Xp6dbjCzUt2/9aV17z5hrJ2Y+m'
        b'/qs8V32z5A9j/pagvtj27ZzWN763u6Odm/anJVk1k5rb10Yke9xsGzPMxfxpfJF/fWOLNtJu9OXFR55sPHLD9YtJ4nGXGzPGzt8dp5q/6UJJw6MRS4+vfvrPlLPbRiz9'
        b'+G7Bf9gLso+y1L+SB1GUkBBtXQDYqu2kIz1ogprC9aMeQ4eLtnrNT88OZyejixTpVoPrHtOu5ww+tYB2xfg4ukA744RaDim11nkhh68rmWmCrgPMDEUWDRm7LNQzWw+j'
        b'MkeXBYtQC77EoZ8Oj0UHyABhITIdHm5J6LMyf9J3csMDelWiGx72S7ikz+E9+CqZsqPt6ABrjP4jky06p5/xynhu7i1mJK8IyNzbB6/HG7mE2/FZ51B8XB6ikOMtZLi0'
        b'mA5910l0i6IK0W7UNjVUQfSHzWGkh0bbBXaV4aQDvk4fXrgMXU4H1RrVLecBTHZThJUFeBvFhpE+lWiGANoC9SzboMtLphUz0nQR0Q2PJFEBI/Aml1BeAAk6LQgMji7B'
        b'r9NPj0MH0R4j9B8+jPaH46t2j6M4deMsuqpG28wX2uAmfBhfUAMYeABAHr4sQW/ViOh+ClrH4JuhJkvvgfg445AqJOVxGu/hvvys/VJSBdD6AIgFMECryQK8XelHkVU1'
        b'6KwXgKkjYNITTlVX0OFSMxcWowa++NPRKTPUjppR02PQYqYXladzqQFMjrxwDj7ADMGbSG1Em1ArVxqHEqYh8tItEaTuwbCTbsbYZQvnRcgpeM1Hjl4PzQ7DNwVkqldP'
        b'71rhtwT46qJMbpWlPRy9QXQzfMBUOUufQHM5yy+SjsP4LbSLG4fJkLiGZgk+LsNbjOGlZES7whuf4CPoVQr0xJuqyGTICJ43LNUVX5jxOAJmqDFoPawNoT249TlQM/wa'
        b'qXuQqO0MvJ/HOKI6Cx7mqMc4VoY9piwJ62QrOcwd2phnDLvTge7CcROXd+vx6ZGkEqWFhq2mI7aYscNrhNWjU2ne5eDjGjLRIGN6M15Ds4GxqhLgg2jffIrEzBk3nVcd'
        b'zoZxmsM0G/rVSaQ57OKVrNBXOB1LjXdRBCraEI9PgY7lT77QSMlCV/EtKj1qnLdQp2Sl5ffXschM6TBtxCTHkoh44YqsWeg04BupSuSCN4oclJWPYRYzGreQumS8/IZe'
        b'R019wYD9FuDOo/W0S8OXbJ3TM1JZdEjJCHLZEAu0hubLMlK8Z9LRTnyTzBVgZkB6plOCpXgTbpbL/3c+lP4fHOhyqMz4T38fTn3whz12fRyzcNbs+mXJPnfp6mS1mFuf'
        b'nuHLyAKaVzSt4BCG7WbXHLTSsYDV89m/fP/yblf/lhVa1+j7PsEd8ow7tR8tf395p3yG1mdmh9vMB8EZHU6B3QHBxzNaM7oChncGDG+f276wI2B0Q2Z3YNjxWa2z2v3a'
        b'ozoChzdkdbsGaF1HwNWC1oKuwBGdgSOuKbSxs7sDh7WXaANjr63qmJyvHZ9PE0q5M65TPl3rM6PDbcYDR/emSS3JB7O1jqE8lnFRZ2CS1iO5wyn5nresxQVwf1pvRZf3'
        b'8E7v4e3FWu/YBstuR5fGEK1jQLdUzn+YUCuNac/tlI5qSAFD5lG7V7Ys1LoG0/RyOpSzO+WztT5zOtzmdLt6AxKzbWhXSFxnSJzWNe528HuKdxQdk/O6EvI7EzgRszom'
        b'T+2aXNhJ/skLtT5FHW5Fnzl6N5a3idtKWlZ0OcZ0OsZAOiN3r9Cl0ytgvZPYR0KBNJntZQTuyQA/jBjR6RTakNUy6Z7n8PaqLs+kTs8kmsAcrU9Bh1tBr5DxSmaB2SWy'
        b'3azLdVSn66hueWSjbbdfQJPZA3koOfON6PId3uk7XOs7sss3rtM3Tus7vsG228O3Obwp/GBEg9k9j8CWcq2Hgpw5ujQs3j22xV/rGEgzU5eP5PoqrePQNgddLudqPZQd'
        b'TsrPHV15s++WYbtXUcGStT6TOtyAZqxpeVvMtcROabzWNZ7eStf6ZHS4ZTwbNOm6f9z+cS3lx6tbq7uGjuwcOhIkDW0KbZj4qadPr0Do7tvtF3Q8vDW83eyq9XlrrV9c'
        b'48Qn5Ps9u6UBzaubVrepr4netrlu07j619Lk+35hHeGzOgrmdobP1foVd3gVkwyTTYKcdZc22zbZdgTldUyd0zW1uJP8Cyr+2K0E3iVrjW2bd03Y5T+203/sPWloW8q5'
        b'zGvs7YD3Qt8J7ZRm7Uy55yxtMW/z73JWdDor7knD2qYBgjUFnJHOazPvcozqdIzqlgY1r2xaeXA1ie7u35LSVtLlHt3pzsF6Z2o9ZnU4zfpM54+xZfHxFa0r2vO6hqdd'
        b'm93t6duS3DS+bVL7nEdC1i2JbRCRfCERxzaN1ToGcdVc6xHX4RT3ABi6/Mk/ytAF1AE7Ez/z9OH8gJ6IbqvtikjojEjQhk4EUK9blzy2Ux57bZRWnkjeTGpOQyJgXN32'
        b'x+2Ma0nSOsrBR0Vit7d/y9ymmTuTH3j6AYyCc9vQkPiZW1C3U8A3Qkd3h89cPXvF5BfIlgJ6zchZrzlDCsrrgFevBYQsGXdZs9UBq14rCFnr7tlAyJY805x9ILvXDkL2'
        b'jH9Il9/Iu34je4fAGx0YL79eR7jjxHiHdnmltNveNuuISOnymnJn6p2073udIZYL4+HX6wqx3BhPaXPEgYhed7juwXj49HrCmRececOZD5xJ4UzG+IX3+sJTfow8/Jz1'
        b'Ceuu4IS7wQm9/nA3AFIOJGcN4t4w8kyXe1ine1iXe2Sne2S7k9Z9BMUx3/MmgfYlt9203mkNyd32Lvstd1o2Dm8J/tg+tDtsWIOIo2ZoSey0l3fbO+233mmtuwJuM1y9'
        b'Gqy/f7yaZWTRjxjW3bfHS9YrJL9PqUO+D6I88xXMJwrL/LHCT8aw5Mht/0i57Z93YYeHMhpkwCGH4mtLl+jRbkY0Ac8H1/7kQxMoiH3AugO7FwwGBKqcHMJFPPcABe9O'
        b'9WVZJQXvmh576fHHAHmBrOSiJF7IvCO0ircVyllKopA1MBSHclIIeSgOS8E4Er1d908LximXC4rkAIyML6stVcmKiyorqa8xALHyvtTIaFwBw3BRpYkLMo59vqSEg2kV'
        b'yapKF1tyMMrgwsKcBbWpVWUk0+dWVhfPlwM2DVy86eBtGnVpmaYSsGhLqzWyxUVVFFRWUrGooqTU0iSRiip6o4zSxvFEKqVqjl2Fc00iA5JwWUWJWmFpGVtTpCpaIAM2'
        b'u1hZKgWskUqorgCXauQ9AF4rkhVr1LXVC7jH9KKmlhQWyoGp2BI0GECnke/hYaHBcFpRBdC1YeRTEshnL4aPr51XVKtP3QDeo2/gZaN+3CjiFciB6QPg1c3kE3U8M+Wq'
        b'ak0N9QFB30A+pbaiWFNZpOKAf+qa0mI96Z5aFgycWmHkk0gylD12aQ0JltYWK+Q00+g71KWQIbWlunzjy4EClKuITBqSEeR9UOpLdaVRUk1ZbGrAMx+8wyTD+iDw+u+R'
        b'W2bR5dxXlPicfhuTdXQV2KJWtJ3bx6R2WIdsl1sNZMyJj6eBPeeheLqc7xkcwe/uyMyFeA2ZMuzOxzcWRuI9Hj4pjoELV+JzuWgDOjMR7ZmZkFqLTpF5cbt5XFaYNz6E'
        b'W/GhRHRTugydtI8UhdHF94teqUwDw7jtm1toeXTmJEYD/Cl4Az6NrtNFUWVwAXmMzJfAdhhMtc0Yv1dE+FQyPkif/4qh1qNLniYXZtwpWsZUlIWvFKhPkju+ybM4igKv'
        b'n62xWNcY9fN17q82ZTTJvhq7sfDzHMl8WWjUOrZEYnVsmU3w4eB3btv/0nbkBnHbAaHyssJT+Krc/9776w9/4IbMtYcFJevbRQuLv4zccH2vWf0//7Hw1EdJw+Ime82L'
        b'3e0w0dz/w68Lp5yST1jYsrJzXc3Ii743P3T5bEThvOBIkfDfzdhC6Ykqf+EWsK5ieeRNRYRwYpTS1jUj4PDaaCFzZ4HL2Jsj5FZ0guIwZiV+g8zq6/uauDnG0YlbGHob'
        b'3UznbBLxSVTPxqs5uMIYdHbU4IZTeM+8AaZLIUXUMMupCu9Rw+ZYsjw8WLdHMAQ3CFE7vjKFioXPofqKUOPlHLwjT7AI7cOtdN0i15LM1XU2f/i4Gsz+YIuVWlImSmtw'
        b'PW/052nHJk/OpRN0G3ygRrfUgXcrwdZRjnfQ5KLC8QZufUkzJ9R4fWmsNTdN3oT3gUjZ49AmI6NB/WwaHUJvcAZ7p6fiN/sbsYXjV4fyE+pKfOl53JYGZ189FsAOwTFn'
        b'mgLk9NfprAjcJ8GsqCZw4FlRN2/yQ5TfLtcQ8u+PPkFk8JJPYLsTkkF5fChk5VlgYiSl5inu2eznnlKigZG3EX3t4AqdHdfwTulwrXRko4go2E0TW0QHU9sEB7OI4tdS'
        b'oPUY3uE0HAx+xrbFcDY+lA3qLlEwFnbaB/+ap+fTcVbouQEH1Qh4zgqDv2jVKBifwcPHaRHPWQG4yPxAlnWDsdjtx6BJYNsC7BjIIFRARqGB2dE4Wig9uQpHrSLUU6uI'
        b'f0JqlTIyBF8jQlgqS6t4H0SmHko1am5ILqWdMhkhkhJSJyqNPZDy417p3IpidUFxZQV5KpbCwXXM02Xg9aR4noLGUCTBcSKNZuzIlH8Lny+xMsCqh+nB6uALTF1KxahW'
        b'lcAFMuLQEYJ3tjpoGork/IxC6iVAU1NZXVSi+xrdB9KXgKMePdYcBifeREStqajlXKLqE1W/WKoTJ+YVhr1o1PwXjpqa86JR46fNeOG3Jia+eNSEF406LWnYi0eNLpTx'
        b'2s8LRI4pVNCoqWWc03hONyktCZOF8NUnxMRaYADjA065GMQAQZasKqJu6J5nf8CJMRXUQa5VLIpWRJrULuregnOSxFU/ksCiiqIX+9KEvHySRCzHcKzm2hSXDlcdK/ra'
        b'JPQHdjlnUdXhG2uzqhzWjeKWlgdEcMQTuDkQnVZbkb4QtzBlaCdqcsqm+tMQ5RB8MTIyUswIUmE5vhEfcUabOWzUmiXojdAsBRmY0T4WbylLxzfQBrqhPdIfbwjNShOQ'
        b'O+tYtN971Ow59JFYfBPdCs1KhUfqWDN0aSy6gC7JRdx+9kF8WEJhAPiCmBF6sOh8QRy6gvdxtCRnUTO6RG631+KrZFzFe1kZ3uSL3ybScFCMfeimephKwLDVJLIEXV2N'
        b'62iiCnx1GdAdqMg34GMsOonOhKR4Ujkt0AmiZlFME6NBlyIK8Wnu0+rxxhU8WKuBscMn0FZP3CAX0A1fNdo9zVhMP7Q9bj46S6EFM9IWmIiIzo70RZvQBe6tW2YHGguy'
        b'pywEtfvTW/gcbpfopV+PtqOreG2ZXMjlGjo8zzjBEpu4fB4DgK/Zo0MmKeL9q31tUBMHWCDa5D6rRRZqESO0YNEblhGoPYAr7+v4wCgrG5UdwwjD2FVo1/hJJTQt23no'
        b'bdjNtrJlGaE1W4hujo9BNzTgm9cSn8xIB2VUSbmzACpDtFMGv4Z2rSC671Yi9i20Bx3KI4E9+BZ+He8iyu8edMsb73QQM6R82q2n+RTRjMetJbOVJGuJgs5MRa+moreU'
        b'tJRV6By6gXfn4boMokNvVcJm3mY2niR3suKjLfdFajeWYSbP3MSZYXhQFTeSqLjr3Ke7xWd/45bQvWu6u1uC+7qm02Pd3FT3ErpjWkIcfkEuTVs3rf2L0iuCDwKPCaeH'
        b'Tbjj8aHLh2ffc/jZ9hMOX/jYZkxWJpsffs/tA/Orv7Sd5zHJfuSU6CWRSRPdMxsffB7JftJbfN4s7c9Rwn/71smlrZWWNu7OksXJq9NrghOZ3wqcxN/YrF2RFTlevD97'
        b'3fXT8VWuok17Ikdcxffb1v1CVNVuY++Y+P6wtWbvixb+a+j30veKJBHd0ncLV6cVfoCLLebWx7CLL4je3/Unx3EBzXd2lwrG77LYUtK0xkv6AT2e/D6zbsqmvzrcPvKr'
        b'BW7/cFsnPv8b0T5HS7H23cpIpdJ9dDRjeWSc3/XP5E4clUgj3havJ3/CR1Erv9sowLuoromOonW4md9vpJuNRK++ig6GkPuw0xKK6vDe0HSihW4HzTilVMhYhwnNovEB'
        b'utMwFben8fo4i68Ux6MLyVQjVuE2tCmU45gQofVskj1+lUyUXqU3l6Lmco6Rg2fjiCxF59HJanqzcM4QE01bgDdlLiINmEojQIf8QgHcBztC5rheMJ7owWvxLbSG6tSz'
        b'lPgNtRW+DKicekZGvqxtHt7AUV8cRcdjUX3NcGCr2sQUA+oSH0dX6P4fmcStx5vgroTcrQP2odfwzoWojU46pk6UwC146WYGnS/Eu8wYuo9jic5LYMfThORiKrqWSATa'
        b'xO2i7UFrVqoXkfbDomNMAX4VH0R78VFu0/E1vBc1qNFWVAcyNTBiMzLzIVM+Dpp9E7dFkyfF5MnjzJRlpPXcxFfpS+fjMwzpOqwZcussg7fhI/gwPudJZV2Nb+D16kUL'
        b'IcFGxn8e3poxnXvfvrwicp2khPYxeHsJ3oKO4J3cfuBp/KYZnQGZzn/w5VDUPhfdINrxC6xqgXbM77PwVktqojn2DDE1pCGX6BShm+WmCBOC9FOEyE5pZLtDu2+HNAam'
        b'CB47x3dLQ9tqO6XRDZM+d/RoXMHzNizSSuO6A0Pak7oD5O3DyVTBO/Z3sXHX/a+VvF1xveKmolfIOHt87urV7T/0+KjWUW1552aemHktsCNsgtY/vtG8W+rfvLxp+cGV'
        b'jSLyfn5mYq6Vju9wG//QjHHz7jVnXPxa8rTO8ntObt3OvvQU3IEs3bm0IyBG6xpjeE6klQ7vcBsOHnrdm9xbyrTuYYPeLNW6h/a7SYT1CHvg7L5/+s7pHX6xWudYnZ+S'
        b'vjEf9Hsv91TLUK1zcLdnEM+Im6j1jOpwinr5m4Fa56B+N//kIu2OHnl1zKUxt0XvWfzMoid6fK9Y4BtP5mrgG6CXEQxJYPtZmvVYG88BVLHC/gh9zuTMgNGnfs1yyeED'
        b'HUYf6AAnD2VZ+Y+eVTmolgk4jx61SypK1JzrDfC10WNr7G27VKX6lItXXF1VVlGukkC8e3TtuKCsYklpCec73LqgQl1QUr2gVF1bUaz6F0h7FyJZUp/e6pqi4lLVh9wF'
        b'gz2ZuADmCOD5XFNRorOGAQ1M9SGYPLsPxG3bIyrITs0iiU/Mz81NypqYmqTkaBJb4ECdcFjVFFVU8SwKqvdpogbuAG4ZXM8woboDB8oo0WvKjUsNIuhiM53R0rynBLke'
        b'/x9s5EK3/5ydW9UKAX8AnlT1DM7nRq8t4+nTomwXXou+XdzpmFYHeziuXi3D28XX8rtdPLmTO4H604dmIk/buvQn1kKb0O8sx9lMYB8y9DhBQN1GyB8JWc/QuvTPwBmE'
        b'vNtpHHiMmMB5jPDwu2cf3u2UQC55JLJ1aQa/HDHgNmME9ZrBe5pIgucmscZOMsBvhXMC51eC91AB7i48R1MPFbw7CnCb4Ta+LuWJua1NzEMfxt230y2idfTRMeSnLvWJ'
        b'iLWJBK5hLzjEkl4snp3Ifidcydp4f8cYjo/o8ZtVQsbWucm/08bnO4GnjbyXIYdH5Jq0F4LfxMLdvE4bvyeCMTYJLNzxf0RPOcJiCtV9Oww3AqWqlavRohvLeEwSVTih'
        b'VpMZiI7+/NFGoCh2AqMpU5JilQgIijlyYoWIpyfmzoGk2JL8hXMbnqqYu244H6J0UDoqnei5s9JFf+6qdCPn7vTcQ+mp9FJ6K6xU4lmSfEkMC5TDr5jr6XfN9CS9rNKa'
        b'HOG/OfnvoPuvlI4282F8GKWc3/0QAkmxCYWv+SyJH6P09WCUfkr/0QKVheGd5L8V+S+IEfDvc+R/7eE30nDdgU8bfuF5yxiRMkAZyKcdAgTNkHq+Rb5NvkO+U4w5R2ps'
        b'JIUlJTOWUALjITESnujYShmsss5n4liVDWWmCO1xgMF5InVJTNm8y0pVFRZihlnmYdn/Due10fKpgkw6YyvU1bHq2hL6OywyctiwWJirxi5Rl8RCl6SIjIwi/8msN1ou'
        b'7BFlZedm9ohSUiel9IjycyflnGB7BIlJ5GgByRRkZ2VMPyFSgf7SI6ZrKT0WnIPpCnIqLqssKlf/mGSjIFmRqgT6sVI4gIu7HlFqlpLzXvAj3zVaLu7zLlUNfaEycUr8'
        b'04R5tbU1sRERixcvVqgrloTDrF0F5CHhxTwpgqK4ekFESWlEHwkVZG4fOUxB0pMLDO8/IaBEy6pdlDOkxyIje2J8RgGZ3D8dCkJPTEilEpLfnKKloFPlwl6Lupa8VBEZ'
        b'Q45kXIGXnWBV6zhvEQA77rFWpmZNykgqSIjPm5jygq+Kkgs5ufSf/HRknwcnqqrV6gS66mD6jozq8kx1OX1TFLxJYHgTEXAJvMuuT3489Rj8o546D5h5ciuTt0B1Uy0f'
        b'4N2jVSvhap+XjKYviVatgHuDJx71NPRHfGmPWUlpWZGmspZmPy3L/2fWo+UvYrrLYdov4VOTZ6GjVnSqQi0d0D7UVjH20zSWWvXKn2p1Vr0sY7YvpoY9+7BlEKveHvMC'
        b'VbWmltR8zh2JaTei0N00NfANIZr3j7Tj3Ag1ahM5JIuN7DhTQ/4LO84TZpyy9N4AGtP7OrXJxNjTUpeVaxjdtvgAxp4GMmlKJB1jqTfktP5paaSLdpE8sEzleFYqlpUa'
        b'rdhzLue53V3oxo1W6JWamppqFSxu1lD3tVSPVMdaWobL+jQrWXBiktz0MjTDfldGy4JD1BWw9btopGJEyACPcC1XFjwxpf9NvkXCzTBZ3/cM3jvIglPznhkjyijGizZk'
        b'eKSvELrNCH6BmFt55UhrSkrn1oIvd95Zpi4mjGZctL7FUKOqqFZV1C7l3LgEh8AYGUIShFEyhFsfD4GxEq7ByBUCmxEhMOSEyBWG3f8RimGKyFg+CveYARgQSW/xbzFc'
        b'HkEvc6/SCcrRZ/GiDkCKxX1fkJryYuk/j06fuD0Z/ZYMrXQDU1fxnED6NA38U1zCXH3tSy0FdE56rEYJt7tDzjWw6QT7N3Sdn+JASotqoUCJkEv7MnkB0qGC26OBvQHy'
        b'HLABcTARI2en9OtkytJSkF1TWSorqiVayFxNLZfsxPi8pEnZudMLwK94tjKpAFxBK6kUekgHJTlS6z+Sa1Tc91En8jx1nC5fdUsj/K4Fh5Aw7FzQ3SbuCcNGQ0ifNhWi'
        b'x4jQHKzh6rWafnSfuKNDOGl1USqq6HM8dxbRt7jNDUCFVMmS8nP5HZUqmXJxRe2yUlUlzcjaZwjDNXC+LpIKl1pbVLmURhy8BYcY6gRP4sVlmIHbC2oSn2V6ni9u84+X'
        b'sJaDrBj5OTKJWz0Aw9Rgu0Xk8/hBXK2rHn3ew+UZVVGNa1pqQnyWbG5pZXVVOTzZZxfGot/oa59FF+4rwCoA707H23GDkBHgo2wSaghehlvpNgI+vxpd0MFW8FEzykm/'
        b'DV/icCswQnqideiiWjXPiIq/HW2ikBZ8Db+GDsAkzQG9hrbiq+TvRbRZxNjg9QKAyB+hdn9445QYMO6IjOAtpxnGAb8mRFvN0H4N2H+jtpgUpc5OFdW7DEpdT+00rlpa'
        b'LMyQC7hdELyDbtXodhHM8drxeCc+TCXPwxtwk37rAe9YMB7tRaeodenSSSojpwUGm+4MtENvZ1pjY5MLbguCw7Pyg4PxFrw1Am8JA5p5jn8/HJZz9zuy6AY+m0wTHOsQ'
        b'pEYX8HUjznxbdILuhdXPlTDWXk8EjKwwI2ZxHqMZx1CK3LPoPE+kfxnt5sj0UxRpmXgz+e6IXFyXMTlFmIs2gw06vo7eWBrIoLdFVriRFFnFe7WfidTdkO5c6YKG8w7r'
        b'Iq03KsP2XPn9a+9dX/LnL37/x/Ntf3Yc1Rm50Pb+ibAPvtz9/VvH5mbmxJ8tSb37Q/rdP77+ac66aOuc2aKl2z2KraMSNvs5nrkhyRtt9tGRu5F7zLZ4pCeO25n+wy9F'
        b'ZbvEC+5HnlT6W//ubeZkdFLRO1+tf0WcM/Swz7Yu73vWWydU/Ht7+emVb0Z9PPQ/i5psbqR8PPOp5iPn9n9UTPXblvCtvfeCi92lq0vSFu/+x4oSq7/Fjrny2q1joX+u'
        b'H+Lx4Z7fjDn21ueKCXvTC/626jWz3wT+e87wzL3f2f1rll+24DdyG2orhbcUO4UqwgHMkoUuSNDrgsgRhZyfkn3D8FZUD15KwNQyDDA5ZoytQ1auMGrGIroQviIFn9Yv'
        b'+eN9lZy5VCW+zlGVXyjFe/sAgvDJOAHe542vcAZcN9Cr6Fj6ApGOq5ydwj15Cb2N96cbMS7b4eNo7xRhpQt+g5rp4HPL0R4eaRM+Gm0zgtqg4+gi/QAhfhNvMV3ld0TN'
        b'wGaNDqGdFGYzD+2TkE9syx6MFpvkwGG621I+ArdSGnO5onSaEYs5vjqaLu3Pi0S3jPdirCTo4Dx8jDP4OUDaHREEmvAlcjuTRS3uyWgLbuPM1VpwKz6cbmuDt2eQbJjL'
        b'RuF10+TWL7X2Bqs2xghVI57mATV7Y7ZmMbfC/3hRKDPEpcMluC2g037UNdfbAXckHTn53aMTb5fdmfdYyA6ZBjBzD59mzybPBkm3u7RlRKe7vEEM6/QDGFQ4uhpA2K5+'
        b'/4e994CLKskWuG8HYhMFyaFBUgNNTgqoIDlKFsGAZAQJDYg65ogRjCAgICJgAkQJioJVM6OTVnramWacILsT30QVd5zgrF9V3dvYOLo7u2+/9973+3bHbW6sW+FU3Tp1'
        b'z/mflkKJvtvHZnbjPn4j6sPqoPI+h2UfSyyHFhLLoYWsCX3jMXNnib4z9h2gWPbEyOgBuiyUXBZGLgtjfWHMH7cT1nEb1ccdXeu4dwwEX+gY1IVITYRiE2FnttTEQ2zi'
        b'MYE/CJgcS69Nb7FscR2baU0HIZfMdBv0HvEd8ZUnTt/nUH6hrLGZbnJajbqcefLfVTVeboSEo8hNMx6W4/zWIV0oGetCfhRjKpxvj9m+P/6zhF8C5mtVdKV6eX7/HcJv'
        b'WRrn5SFMXyRBMsbvUVSKstP4UsL5dPoDE+jnCbx43SkhLCD+LjcoODDxLndBfHCQQOlFpuFl9liRXE7W/jPzMspys0XTVD1NWZl3o5+5yi/l+mCqj1KSBlL1sNKnSfg9'
        b'WknaHpr/r9B7sI30Laz0BWRloZmevPWubNLygjW8qemmKpr2zMGT2znLp75SLH+BdYwjM9mbYn9ic2EC/pR/YCaaLK5Ak2ik2T+bUpfjqixnFIYXqk7MpJtu2RdoT3SU'
        b'cPpa+cfRx/kZIn5OYXEGXkxA0+98dGRVRdGK7DKZ6RbKlEzZxfM2mdlZALl7+dRTpqkg8o+RKSDl2VX0/ByXimaYFtGmy4wtMjqWn4Unq8+KMhVTnMkT3w5lpIxklUxO'
        b'LeNDnJycLAXMNJk2CCJ26xm4NUXlZRWZ5RUYNzqVkhM/RGaPJnee3D91DZGEipLCbFmTMMZ5aB6OM4+m/kWoKsg9dvHBIcH4u1Lwspik6MDgeEe+TKtJDF6UKJiqn2xi'
        b'uI4rJ3tVlrC8WIj+yJXPrriENsSXu6PqRYodOppdhg325RW7abfjbE3pebhG/p6axhivT5Fqyd15xYVIsX+xBsdHpQqOjwmI+r32Rtu2v0SDk8WKpouC0bJ4jwgE025Y'
        b'zpDSitoFNdDy5THFq3DPkTParyp/ljq+Gd+FFAZsSI87zJRo5JQVF6GiZmUw1vaFFfRCTm5+ZfYqmSQhUc7ChmN2mcWrRPmouPhOVPB8chTVytSD6dvk1XmBfLbprBSv'
        b'KMjOLKf7C60QJcT6eLm4EmFBlUfyh5/hyFDEmfwT/RvLMur05L6cijIim6Q3EIeAZ1odPazO4ScwWpaIvzovHylq2J9gDUqlEKnp2RlltK5FX0z3LZGoGCn35cyjaHvT'
        b'smIk6MT8FFUFU/lIsGgxogv/rBc78WOQdpdRUlKYn0lMNrH6S+RR3t+Blr0FdJ/JYDo5Sh2/Qfh26FfgyMfvEb5dbFK8AFcWfp/w7QKDYxi5tZdzyPAS2KvK2ecFTA09'
        b'z8VNlbdz/QeqojmzUDsAOnyIMsgCB5gAZeCsLpleEC0mzAlpMZRAAWsx/XOWU8T2a6MBPCJSV4cN82QKogqoDaFRXge84WlRsrnMvg3sTYBtRFXiC43QzHUfaCIEM4Iv'
        b'Wwj7Eunoa4NulVipJBplt+d0pRL0BBE/CR1wMA4SIMCyDUgnw7HlEhkYT6TQPjnMMSJJjnn0uxhomG3WHayNJtanPYgmGQsbddFzGsDBKWVyHjiLNMkUPP29npRGP+z5'
        b'R2mBEy992rOwj3F2BNCEv2AKFKk5LrqwB9SDXhpCM2Qdy0NaRrdMUZ0HGjQrqnA9HIGD9pGY1gSaltgJI2KxskqnpAAPwu2q1oagS/WZcjgfboaN6MTJGWA7OJUIWrLi'
        b'QHXgBnAcafBn0X9t6O+OlVWgBpwOXLEU7A4sy4+LK1haZp0O6lfmaVFwv78JaIxfSFg84Aw4Cmp54Chsh/0lamyKDYdZzvA0OF2RgE7bbgBbSNZelC9YbQhOGYDq+aB2'
        b'Bdg+LU/b4Ul4GG9jS77lmnAnnwLn4rQN1jNIHlivB4d5efCczJbQeT1or8CY2Vxq+ZTKLkhmGHUlFRWJsKZEXRMeTGRqPQx0gv5nGj3W4nHzMAEJp3BuYDPoVCYP0YC7'
        b'9OB5eCSM6OSLXG1fBBKcYuThexKfNSeq0j2oSZH2vlM9tEyLhMdbGwSORq6MkQ//uQ+cW0jkBiUbiQ9gYTqkIIoAu2cgqdsND8UjUdzNgiOl6qEhShVRKBkjsAN2Rz6f'
        b'StgzBRDl8aRQPj2wnQcO61rD0zORgtmuN5NDgfpobdC+UrnCH88KbbVp8t+0EuHIiYfRQy4Vgmo/1DBb4DZUtcScEhxcQcGd8WrxC2FtRSzpB7ADnpBbOYkKF0QIneio'
        b'eHSq4LjSFE6QyZb69L6JaqupYgaojcggRDvHtU4ySBJK7++kPD3ZKljzgpTjI3TBsLIHbbHaApvgdlElvAhbKdl6DGiA3cQ0how0unAX2OEAjoQxsR6nx3lMKsMh6fP/'
        b'PPguW/Q3pGD4fDt0JCk6FszXajq64X4ST1frxk8zNVacVJqlZFHmJd526mp01F6lvTZmPa5Ln2gu9fuvHyoqMyKlH1uPR2Z8+c664pzcgUP3jfM+Vc47orfT6/6XVQ+2'
        b'dChv0ltzznDrL8pPHPZ8WOBX+Z7nCu20z9o3rTlh0935Bie+hH85Lzv6Tsj1hzlzZ6zMEy7RzUtKMS09CLb7h9w5t+npR3fqQ6qDh8WmFw7X3LCZ+/Sdk8F756zeJ/Z8'
        b'OPsr14U/73jr8RHrX3x5LI3RU38aSo+PWP52z6+dX+X4SliDmu6Fht9c6DLpGE+L+7xve92OkA6w0qd23GHGOs+b2jkGd9rSSt9K/3Klz3rvPMX0vpEQkUOHYU3Jo81V'
        b'hnFpFqd1tsY0fdP4ecXfejzK5hwZPF9m8CQ4ftl7Hq7+UQ/UxxtXJ779qbXo9IEHu5UKY47pSP/suKQP1h/IuzkxIPj5va+0H+st25jj/3pLivjb+Stfq//wpvkbr+lT'
        b'J1SP/lr9t6eSP/dfcr+68usLoi+u7asfaF/61ffNFQX+Lh8vbvD9KkzDw9Z7bqL01v5bbw5PvLNg652Gu6ca1j4OZYdHXvq5BF7Z4r06aOWlGPiq8S978r6W8B98Gbfj'
        b'k48CYktLnJrOG+W6N1e9f1VvQ+zdB/Nf27VuQV7LzW8rxbetPvj8y7eWRX3nd6u1Qud64Kf1DSmvrf3L49ZHD3ntfym/LvxcoEeDOnbDQXBx2rpPBGxM5hQugWfIKsxs'
        b'LuaXkBWlVDU5J7ONoFkWSu6qO+bBXIfd9IrSAmXaWLZxbgbpWjPhgDy5pw0cJss3BeAUhvOs93q2ggMalpSQtSawH42sB+Vj7q0slcXcywb7yRJPFezOI2wf50CeHNoH'
        b'dhnT8J8ecMqSN2cZs2AlDx7aLaDXiK6nVMpbz55AWbvMrqwCx2gj2CMKIQ6gHYw8M8yFW2GTIm0Euwf0Yhvh6thwS9ACznEpxUI22ppL2492gRF4DeOQYJMKHSYPHIkl'
        b'9a1SgRfo5BfI4CDcjFfIFkeQEGl+5qCbXJAAdr1wfax4GanebHAwno42Ci/DU3KElb0LSR5Qvg84RfpXwP2OOCQz15EFrswII6t0mei1d8kB7oR99Oqa/NraFg+6BDvQ'
        b'uxgvUoKz2YQvdIrtYjLnEXG2PKGqFxkVDqqdn2cFukTDnWBQ0Rm9fU7SroCXfMF5IjzolRWL5iga4HhkEMc/G/SQWjQCfaCJ+AJagEtTIQA70FkyfTsFrhmBPc7RQngc'
        b'tAhQLvzZ/LWqAv3/Dcs6nKGX0FGe+Z/ftXzBMs2LUCgOHJqdXiXE0dlsOm2k+q5ifdcPTGe1hHQGdUd3RWOkSMjEi5f1+FYdaq1qUr6rmO9KaCd8zxr1cQs7uWhkNRoT'
        b'VnZSKw+xlYfUykds5TNoKrEKHdOyGNcxPDavdl6n55jbgjH7IIlO0ISlbW3k+EzLlizJTPvODaO6EufgCUub2sj7ipSVq3hWYE0kxmU41ztLjBykRmE9igOavZqjnmKX'
        b'sBql+3xZNLP+1R8ZWd2nWDZeeH2RN8R7wGHZBJHQZ8Ek9Fkwi8ZCzK6d3aIo0bH5xNiSWWUMIIuLgWRxMZD1hfEsJvRYm1+d8k8Tcva3z25JJrekkFtSWBP6Zug8Q1Zh'
        b'SDH3OZSBAD1Rz+jZ7fpmzO3B5PYQcnsICyMpfJt9aS6LxCxuzCBOtnSaNOboP2Y1V6IzFyVlYHJsfe16sb5LT8oo96b6DXWJZ/QEX9ijK+F7DlpJ50Sif+8vTCOAkCSJ'
        b'ZfKYSTKOP4fu6VR4V1/Y4zCqKw2IFwfES9ziycMY3swX+man1/Wsl3gnj8vlJEpiFj1mED1uMqs5tjkWk0kG1JjsB5LsLyDZX8CaMOE3R9VHSU1c0L+exIH03nSpZwj6'
        b'98Kr76viRvCt9ZXqCMQ6gk5rqY6LWMdl3NymNmzC3KIm7LOZRmPGws5y8cyg0ZRbOWPJS8aWZY4HLxyLXzyWnjXJYenlsGrYqDrMbWrYh3m4pqZSG7NHG35iHb9PLOyQ'
        b'HId3hQ/qSRznfWBu2eJBt6jE3KUm8HAYYYzgcHudahIdj3E7dxyvznqcqfUoCcqQlUNN0OHoCX3DGhW5VeEZL4VWPFuZLGv9vdH0H+nj2AH596wJObzEFfRTryAfG67Y'
        b'kcWKJ0iJeFzL6PefWTnGmutpRS+qnxfAmr50rCjTaXF4+LmKxPKJNlNUSlJOojwUp2ygFP69NlBr56vGZ6/Kyi4T/aNVUbKkxKjteJEkQ8RfFB31nG5uRj2vmwtiiFIB'
        b'd4DjmB1Gm8KCeiMyS36OQbwnxe539C7YCM6rz4S71xF4aSWsAXUOz0134TF4mZ7ywmawn6jDSCG9AppFzJfMy9Zk8jwfDhPiKzwDu8FRfLLcCU0TnCrRTwR2moGDYVZL'
        b'FbzBGXiYOH+5Wfrip6AkYG2OGQVqYEsWrV226BpOfZMGx2AD/i5tBy+CK2SdYZkbp5DFoonBReYKdHB0sAmcsyb4cUw/P8CCJ9A7uwSersBiqA02ZzDudbB2trML6Ccr'
        b'GjmwCbTzVMo4FCsfdMIu/PV6BGwjmYsDFxY7COzRVAbWW3LXsODm2Zo0S7YbdLlG4nlQjAKlmFShx1ZDJR6m3eeOgoPFCXAfl4I1ayhwmQJIE9lOf0ofUAXnaXIwVjTO'
        b'0ejgTBWi10bBNgv6UzS4CLdjLR+ecSVqyjzsZiPzq1uEAxofYVkgNauB9uS7ALsqp1zyrIM5Riz/hGSSf4MS0IGXSbiYp92ESmivsZrO43Duetk3cbBPk6xkHHchn+KL'
        b'CmBLAtgHDyehadCRFWkYSqwci9HXV1eSmjew3D+niuXDplyWxyyxVqeXfU7nWarqsLDR/vIVx/hG9MGrnuFLl1B8TPZWvb3Egz64xU7dbzELNdDC5Wp3TZLpg13r9My+'
        b'ohZhP1C/FX75VAUOw+uOZoQXaRSzMmr3LeC4PIs5CB6ni3IJ1C3l0QsQ8JIHWYMwz6EdCy9rK6Ezpeocyg/UcnRZvlos8jhfS6UNHRRxO41aq6AwFRXoFGgFx5g2OCoi'
        b'Cy3n5tENfgHNMTfR7otIk2/Hyw5wuxZ92/4F2MIA3adEwTovjg3Lfw64zFC50TxrW6goBmsBbNQXeSw+OKZFkjSFw+AspmhrstGTfVGKPnAYVpOcz0I6RB8PySTcooUk'
        b'BCnpRnnkWRY5+rBPDfYrof4ygNTXQ+isxQbixgi2gqtLMFEnjoJIgYgrgDvoTrHZCHSBHRt4dvYOsDcKtWYEe/F6cJRkIqt4NuxzjoAD6LhCySKwlQWPuoGh/MYYPQVC'
        b'lzvz7ug7qb+tNAk2OPHhr3evXvvs+7KfC1Y0TB6/8/7BM3l5DTMcDh/kqwvcB4zSHLmS5J702oUBp35iWaru5gdoC+x22dnt0p0pCA4KCtDVfrWZG3Bf/6nSl6tyH3/x'
        b'4/oc32OvH3hy8VjuvcdrTvw8Xr9m9Q/vFF38Im+r580v489NDngP9lQc6JWoZkadAr/mJrxT+r3Lw5t9ujoxde+tWJ/V3nZuwyW3uKOfdujFZ/i+/6NrsnfXl6xYr8/E'
        b'Pg+LNO6pPL13e3F+LWwMvavh9vBE5A/5e3VMX9+74/Dh25bvSMr7LO+96blS3eajzms/f1GyjrumOifE9cK9pCv7XO8V1f1yKso1TnlN0NyzfXpPAs8Oun13dTiiz2ox'
        b'Z/9f/mQVOnrX3uvmysLeS4+uPvnuZzNz19yBiLP6OUqfea5e6/ju5E8avGub33ur6e3hZZ8dGvtrzK4Y1p1PK1rqdpdVSq6e7Py4ufXx553ftnZ6xTb+6Ke9VD9Vsyb+'
        b'1Yav/6QvLB50/zT9umaV0f3IvtnvrHGDG0ZdvtJ85JLlufFGeu4ukX/G+6vb9BJWhh750XGf+6DQ4QvOaNGav70S2/xJ1/gPJ3sVd7z5ZIbBEVXDI/bf1mYVX3s7460f'
        b'FIWrfzYJFq7hbMz+S5VduclS9VcuGyxb8rNf3jcJd/4SsaM2feG1il1leXEDDr/N6v+lzvX7fCedUkcqR++HefPU/UwV6s1GDpx8YvDaqyUfHTo9+4O4QRWn//rep+TL'
        b'h8G73zRLY895nBDV4Gv3Kfe1tSd+zDxzL3mT+/q3D5yt3+wRY5N/7rsk1S0hH0yq2IS4fXziUsX7l8p+bLnsPmrbtM+ocfsTzdTJ5i1PMg3Xa/gXvqP4+vVvdOY+3Tnj'
        b'l4dqrxV8u/mG+pca/X++M/6uXab+089Werxp/q3ptUN/euiTeSLxbsniraKvt83+Mkj4Crdk8Ilj0O2EOxNP43anXth9qMDEfOti/RlVV4uuKH88T2Phb0HrFwqKR7+N'
        b'HDuQ/eFrg+O1Fv4t51c3qIj+rLI7+ETsaye2GL63w/b8x+zKCefP1hf4VqWctpJkrzW/7esa8OOFn6LePPhxhLnU/c1fJWNX36kHvJi1Qa9ZfLk/XJiTYmsTuWJVdbPO'
        b'53Mfq1VoX373m99Gkn70T4397OiFN+8dqTzyTcpPoi9e6RVtSCpIqbP4/mD5e2f6dySfCVxauvdM1o4nF1v7q8xOOs9/FLzpp8TknyK/0LvVeCzjTw661l9eVxlMM/nq'
        b'0brtI8df1Tof3B1QUWO8L9UoL0ZhknVhbVKDfeqep++lez85ULC1Yd7HPxSYr7vxIVcr8pWozTpPN4re18jdet2+qWfOb+YxnZoD93JXf+RlMfkNdf6+t92b9y7t5/pe'
        b'6TSvPPj+j6+KOIs+b3+YprtP1/6J6jVezmsfbjJ8X6eu9lHZ9pEFbWPXu9asSV6zRn9tgG3jZxFOfx5e/kP3yGTg0+HlG64rVUVnbr4zo8B3wev971cq7hNKK398xfvM'
        b'd2pRaRe++/bn/uQPDX8aWPThBweuRRflLv/1ccHVx6xQ88tNN0aCi1Zvzf0vzu789asPGH2n2Rr7a65JJ7XR3HqtivRvB1r1eyQrQnq2rGeXnT3+cGb7KzPtN6qKb1v8'
        b'sv386lKHB6nb750ymkiLT/r5muJfVm81+m1OSZJ16YL5f46sma17+86PJ11+OPvq8P3FX/824uRw/vPbWzpQT30Sev8t54fdAb6T8Z8bt/zlYbHA/nbWvbjEBot7Wxtr'
        b'FX9+mPnkx9pvfi7L+OV67YHg36jfnh4qjhb/OiP1cs7dB/PeXde7e6J7Ys+s9O0bE2Zppgzv2Dyy7Nh3SkFR8G7ejjtW635ZMylOcN5rM2zxS/WK42XxX9zW/eZ68x7p'
        b'W2lxsen67z7o8Lry+oPxT2yu7fWsW/bV3PYNm5+y7568ICnbqVb5huhuNxgaYblx3uFt9RcUkgj0+rAukGdPVkPgXnePqcUWc9DHRROrKwn0iskQmrdF+k13V660Apto'
        b'1+ut6a4O01Yj4NFUvCBhCvaQpYQVjgmRcF8kPg1PxpMrNF04uWATvEwS4M0Ae6bWVUADPCNzMQ5KnkPWVWzBkULmglhYDXa4PL+u4r+UrBs5BabjyzCKVugUFoWmTPDE'
        b'Wr0orjo8BC+ShSF9uFtbjvzcthzsZwvh9XxyuzW8DutEMg+vEQ+y8KUORzjz4ZHZj2zRFR75cI/ICT1ZWBYj4IA9KmiK20fMvWA1h/KAZxUT4FZ4jiyBrFWBmyNl4GtF'
        b'PjyyjG2/ERwhllwuy2FtZJS9IsUGe8HWJSzvFCai1DFHWIvawhnNo3H+LsBj4ADbWhFuJe1QCS6mRoDdkdOgtqAR7iVnPeFOL81FPLhLiPnNkRxKCV5ix4aCi2ThKMAG'
        b'nJo6B9t9YB96E6uDXWgeAzpdSOVswJ7adHgCNL/QIvEJYCccoJfUzleZguGFdBLCcPRwVXYKB26h1/zOgjNgv8g+HO4vgbvxmuEBeCBGidICPZzyGQJitzV3gVIk4TNR'
        b'lAI4XgqvsTnepfTdNeAcaIJ9kfBiLA906YNmO0VKBQ5gZvc+cJ7IkFY4X4RZ2ipOsAH7+itQqnA//gbXr0GvhfaC08Y4cyoC2FO4lJRfHQxzdGC3Cp3/S2gCd5nx1I9d'
        b'zywJ7vai7ePawQE4iJvSwUmgCroV7ezxwtsMA4w9a/AnCdiCE3C7NTzGc4qE/QK4B9WABjvNkiIrqUHLwR5RDIuCbYFkGtUJT+fSWO5DvnixDhUbV7xDmCsuhAKlrccB'
        b'9bALHiWPXwquwZHIGEdQ7WyXDjqETMQJY7CFC04HF5DHq1doiZzCQbeaHVaYhPYUpaHImbd0Ld0Fz4OODF6EMKoUnM/eGIYEVCRgUYaJ3FBlNVL5cXqwHx8Ch8F1Cl6n'
        b'wFA2vE5Ebm4FvBBJhzYJhvswQVoDHOb4uYMd9Epwl4cR4U/D6pioZ/xpsBuceMRoQqdXicLtBXjMOMsBh1moyXaCC7S15LUEfQwUV6BWInnmUWAYXrSgVxf3w2Yr2ceb'
        b'PD3ZAjMYAtdJ5ymGXcYMnpqCXTmET50AzzLL3hHOTMcSwAZwbGr1dB+gxxM4CKrBPp4dqobSKHBFHeVNFR5ng6tgWyVJfTHYbeELr+FyRQtZlIorG9TFMIj0SlgLW23B'
        b'SZ6TwB41Gcq7cj47X4OpDgHsD3ZAreOEOWOb9WJRdWmCfZwVsGXdI2b6fghcRo8uRcKgkL0BdLBg87xZNMv7MBxw5AlQ1yBVopBfAetY8LISaCa3ZmIcXCSz5KtmSxZ9'
        b'I5hMwV2g2wvJPy4q3KvMgdUs0AZ60ABMRPv6OrgpknylgvXKTooUL4INOzzMSI5ThDmiKAG8SJTwbtAUiXqOGhu0wL3a5OZIU3ABt19ZFNisi7k26s4cZdinQ5aSLUtR'
        b'k+GBAmngm1G9ovLlg0b6oact4TWkJpVhG02kzlxgg+ss48x0UpYqcCBOZt6pCdvo7wMb/cnYV7wODDJ6SoACUlNcUKsZEVXkig3zLQPUh01x9wvBFboKBirAQTqjsHmh'
        b'M4tSnc9G6sbOShJ61hxpxYdEGB9Pd2JUWpxt2Kqvi0ZmeMx4NnndFa4Cp0RwP+riFxxzwVbYjwf6i+hCQy2uPbgIakiVrYatJDQPc04BvZ3qklnozQH3kM5elLechEug'
        b'2EpwJ/4+cBgeoTtDJwuM4O+aSE3mUlx4ZqU2aylo86HtVpvnw3oRiRfHSnMBJ5BirknDAGEzPI9GzT5nWG2HVLRWQw48wQInkCJaR4ruPxcM+cEDKON2Eavt2ZQSOMSe'
        b'DQ7CNnqEqdtAQhyhDky+KPfBWiJCmmxOFjgHB5kPIunwJBMnJgUeZ8LZrCkitQLabOBmUYwAvc1CkeCjQb+HjJ8G4CzXFa8y0Ekc0gc19PCPKyXDBzQg2fZnkS43F57k'
        b'MsMnvJhCLHNV4WUkEuvRy4kMBdXg5Ez8csY2u8KFySwh3M4mTRcAWsCACL3PVGD1avSHJA+awnTgIQ5oRp2WNvv1hN1aJDwODie8hwTI8Q4hZ6xhry/51IA/M4QZ+bP5'
        b'2eAoIRLy04J4FeoqqE6rF3IsWAGJRXQzHQJn4SYRGkUxkmkEntZlzUJvAHo2s0JfgS5IeCk4A6+Si9RhF8cad3F8QbiWEriMhuvnIweBJtBKJgmosw6h/oJjADjD3dGO'
        b'Ai0wEB6NxnYmWoWPnyKqZSMi9CnhhG9IPrIogQHynSWI478WdTIX3P/goUoSaoIO3FOr9FzsHhl2PwleUHZOgztpgdgOj4AOHrlOWAqOpZHRWRv1UzRm1MFuIlNLMlej'
        b'55IB2DeJlEIjgRMNt9uRGrKAvQBLBOpsXnAT7mzBbHBGrYIWhJ3O8fgcGwcFa+OAoyywH8eTIydXh1fR98E2BTKaeHJU4FnI1Mxl9MJudnhRCeAWcJUED1gND9LzFbgp'
        b'c6oMR+FO8kBt2M8Bp4JgDyno/Dmgm5FpeBWcmop/RAc/Ujalv0TtgFtm8OzwCxO0LeTAARboBJu0SCU4qOeCJjse3C2bMSlT7DgwBOmPiO6gWxW9BSKQNLaDPRx4CfVJ'
        b'9IqiX9lgeJkhLqhqRDQWF3QvPLxQF2zjoNY/Da/SPf463AZ28AQUpQYOsYwouJ0FzpEeb4kGTFS/sNdZ1Y5fZU/Gda0CDprazaJDh4ArfNjn6OSE6nhoNgfWo9efdckj'
        b'vJq9TCmWh3sBO0dbwDJzgr0kOwpIUneI0CsAVquorn5WIANYw52zUpcMW3OQ1DfzhKREivM3mLF1dK1JbuLKwTawBY2gOGhijNAeSzTqu0dhmzepJh7K7ZUkMCxytoc9'
        b'YQI8AA2zw+CJQnpiMh/1kz5hDL20YwXPrmehWWSrD11NDaAWtNMxIKYCQIC2eBIDwi6VJLC0SFvkFFEhUAFXImE1ej2x2WhE3RdDJzAAdugwc+xwzVg0NcRjmzoc4sxG'
        b'DbWP1FZWHmx65i+QtIETzQox9iMvm7mLMiOdovE8+yzYvoblB/aU0U3TVqIVSTsQoPlvNXYi2KtDujcbnIJb0Yy0dhp+CWyGLeCwwPB/FxGCG4P/+//Jx3ZQLCNfAO4a'
        b'vuBrJn2KfMRcy6M/Ysa4kgDQGPnzkZHNmG2ExChyTDcSo3yM642lhs5iQ+cxlwCJYWCN4rie0bGVtSuleo5iPcfOJImeew1n3MCkmVfPkxo4iQ2cxpznSQzm1yiMGxhL'
        b'DcJbuB28Vp6U7yHme/QkSfi+6Nho8Ksq+LxZi1WHQ6uD2ECI9ujPbFL9iM5sqVP4IFfqEy72Cb8jiKjhTpjza9Q+MLdpqWzYiDZ0+S26Heat5hJd1xrWFzp6HxgZ1wU1'
        b'R9ZHMt4LmRITtx5XsYmnxMirZsE4f1Zt+ISRcbN9vf24gaHUwF5sYC8xcJzksI31ahbcV6QsrFoCWhVrwj8zs6wJGZ8l6PBr9WubWxM1rssX67rURH00Cz0Zg/jbNkhm'
        b'eT07Pm5qIzUVik2FnRndeV15KPFm1XrVFq8O31ZfiYEz3leuV26Z2aCJN1H9tAR1RLRGSK1m93hJrYIGUyQGweMm5o1KUoPAloCO8NbwzqyedLFTgMQqkDkexBzP6XlF'
        b'7LRAYhU0YWgqNZzfknzKCP3BHP/5Yuf5jykNQ6P7+Gc042bBjYJxC6vGFKmpH+2u0ZMjFvg9ptimZqMWmDY7zrfqUGlV6UwW892l/LmDilJ+2KgNqo4FLDNUG2aWUlOf'
        b'lsSO1NbUHhuxtQ+5czBjJG8ob5xv0cFt5cqdlFovGEyWWkePVkr4MSiJeWb3tVAKzan1qZ02YlMXqUlsT8bAyt6V6NFWN6xGK6GjxCsWNUljqNRkWSdXaucjtvNBm4Nx'
        b'I4uHFt9i3ea+wb2VKI1eIo5eIglbKvFfNmmsEcoyum9GGRo1q9ero5bY2DPzMcWyjWTJ8pNMhwfxF1v7DxZIrMMl/IjHHLZtEGvC3BoHf5Cae4vNvQdVJeYLJhU4qKqU'
        b'cWKK9YrjJqbNQfVBSJxMWk2kFm5iCzeJifv41NdYsYnLY0rJ1Ow+/umJG0jtTR3n20j52Z0e3X5dflKHuWKHuWh31PWmzw2fW0G3o96IkkYtE0ctG1ueOZaRORaVJVmQ'
        b'PYFvyZPdMl/sMB/tjsbdTLmRcivxdvob6dLoFeLoFWOZOWNZOWPRuZLgPPKUiE7Xbu8u7x6PAb9eP6l7kNg9aDRhdMWYe7jEIQKXXbFVsaUcC6bU1lds6yvh+41b2Z9S'
        b'lfJzxuKSpHFLxHFLpHHZ78ZlS5xz0O8t3QGVXpVBq0HRKHtQ8L5LkDguW+ycM6mu5GU2qaCG6sUI1wuSYaZennuGj9jWR8KfjZrZ1Ix0G9yIfp2sboUuhc6s7qKuIomd'
        b'36SKAkpIDSekUq+CE0JViRpcyk9BV6p3qSN5yO3NHcwaKRwqlM6NFc+NHVsYNxafODY3SeKVLLFLQQJnsZQ14eBM15cv+nefQ9m7SAXRPQEDob2hg0EjUUNRUr8osV+U'
        b'xCNaKsgbi4uXxiWL45LHUtLoqB3SlFxxSq4kLu+n8YDAm3o39BjRQkKVJglIn1TimppNchRRVrWIM1aLzmMKSUanRbddl924qcUzCTYN6ckZKB5VkJrE3wpBcmcaxMI9'
        b'SLNTT8oP7PEamNc7DwmVg9HkStZsZ71JaraZfk3Io0oWZW5dx8ZBN8oIxHleZ4bE2Hncy2egoLdAbOJeF9MVOiF0rYsZt7HrKGgt6NFuLaoLnTAwI0Ke0VHUWoQrL7Q+'
        b'FLcC7q+W3TZdNhK+K95Xa1XrjO9O6UqRCoMH1SX8ECIwYZ1u3T5dPmhjkDWiOKQ4WDZSNVQl8QkjxUWNYmYlNY3oDDqnjP4M6kpnR4hnR9zxjHhMKZuaoVaQLlwsXrh4'
        b'3MK6w7DVsDNHbOGB28Jy0GLEYcgBR+xBQ1GPntjKW2oVOBgitYoazUHC4GuJhcGyQ7lVedzKuiOoNYged8a8QsSCEKkg8ZbH7dlvzJYKlo4tWiqxWoZusSC3WEv5LmK+'
        b'C5IM1LUW9y4eZd3k3uCOJkqDk8TBSZL5yRLPlElN5Tg0LM2gTPlkIGoJok1i6FFJe8RoyAjXh2qrKuosHl0ePVypy3yxy3yJQ4CEH4geNQeLqqlZc3B9sOxCt+7ZXbOl'
        b'DsFih+BbbiRrkUvEkUtaVMf4Syc5qqimjChLmw7jTp07JkKpSWiPxYBdr92g24jvkK/ELXTcxExq4o6aUGqyAtUzb4g3GnAz6EbQrRnS8OXi8OWSoAyJzwp0FX4lNcfW'
        b'xz6mUO33sHDnY9pu3NqhY1lnhdQqHtWt7ZDtqCUemG8633CWzImXWhWOJadIk9PEyWlj6Uul6bni9Fxp+kpx+kpJciGpvUkO19XsviouV0h9iGwYjO9Ia02TWnuKrT0l'
        b'fK9xviX95nVH4zwaxVCd4x+UY5UhFTROSK1yO8u613WtkzoHiJ0D0C56eeTdyLtVhsM1SWMzxLEZYyuyxzKzx2JzJCG5E/iWAtktC8TOC9Au6lVKbyiNLYyXLkwTL0yT'
        b'LswSL8way84by8kbW5gvCSsgD4ruLO1e3bW6p2xgXe86qXeo2Dv0FufWjDHvKIlzNJaZkNYQ1Cq+Xb70iCqxmjdu53QKvSnzx5JSpEnLxUnLpUl57yblSdzz0e+txIHw'
        b'3vDBrFH30cDB/Pc9wsRJeWL3fDSQzbZEAxlpQFQ1EfURTNU89wxfsYOvxMpPVpWmpCrN6RmEJ5o3SE1yaJlHNZJ1IwsJie8bvtLILHFkliQkWzInBzcualipSTRqVsVe'
        b'xZ7SgfLe8sHAkdihWAkqlUs07rth9WHjfKfHFM/Cssd1wKvXC2cjqjVq3E7Qze3ijjsKuyO7IsddXAe4vdye5D41lCGhExJXoa/UMVjsGDyaJXGMlDouIV0zWbwQDW/p'
        b'koVL0BArsEe9WWBPRt5VEjt/1E2sbVAvsXaUWoWgPKn3qg/mSlxCJmfyPCxxDrzu61E2th0prSmdKRJrz0lDdTT+rWaFs2yNHlPhLENjpFWYWz8IYFPms+7ncCltI6kW'
        b'X6zFb9FGM5Cw1rBx3ZnHQmtD0TwLlVui64j3w2vD64saiiW6TsxeXVZLutjMVaLrJjuQ0/KK2MxdouuBD0TURuCJELeeW5fYnF6fLjV1Eps6kZmSSbNavZrUQCA2EHRa'
        b'drqOGQh7dAcMew3FBnMeU6qGZqOew2vIBvNm+oBvgeaOglZBZ1B3VFeU1NFf7Og/uGKwdMwxQGwZOJoptgyXWibfypNaZowtzkB1am2DJYCp+s4ENG7K7KyCxZ7BUmHq'
        b'Ld3bJm+YSMNTxeGpErvF43YOUrv4Hi6OJkUPKWgXvbSTbyTfCoZL0JBvbTOppIQFSAVVpZL6TL1Jno71jEeUjrbOAztK27Qu4Y6Wxbi+0bG1tWsPvTKmNevnhwu4lEsu'
        b'6+eHy9mURwFLpIHm4O8JTQPmqzg9MEZ/NFxoCymVF9GAXq4PYBuk5dPm/2X2XPTjgH6sFRlU/8+bqMehrizWjIfUPwkMaqG5Wouw+RTGPwoUCdzqv3DuE2NiYgRc9FN2'
        b'AkO4NF7EdSz7G0UgSQkLwoKjgxMIyZGGGbVQMsdgYptFMo1tOsqq8WNmlu3+n9KosC44/+W8xRUc5gfD4kR7WKg2d1APuGx1LdQLLeNZ46ae4xZo1uDwQEXBCgeyIsf8'
        b'xy1mPX8smBwznzqWg44Jxy2E9HX2U9c9fywCHbMhz5iDjjlPHfN87lgafS865oSOzWfhgybCcT23cT3hg3yWp4HGrrD7q1iUht4jNoYjctDWfbz10AwTEFPGHGLFi9I+'
        b'MDbvShjSuSF6wGFpRLEmQiLGA4Ifc3zVsfc4/p1UwMfvc/H2g7UsStfkAy3bcd2gBwps3RDWrqCHyiS1ruzekM6lNzLf8BTHJYqTUsWLl4xFLB0LXvaBkWmX+9Csocwb'
        b'VjeqxmYvHDd1R7dqeKJ+GsJC5QqPfcwJZasb/ZXCv5NK5BTefBzPDeSoWz2m8O998ksDGrFZc4E/rMXmR+UMrqKHoyJzxGBTfosV4W54EOyaZtzGY/5O5mBOo84f4DRy'
        b'E1SYbVW5bR7aVktQJ9saaFuTOa4lt80wG51UpniMM1/KY+S+kMeoxzARzad4jPov5DEaGFEJhglG/0Yeo/FsRfJk/hSNUd1DIcHkH3AYTRkOo5kchzFXYHFXk0CS88uy'
        b'M8uDslfkl+d/jUaptfqqzx3+JwmMPjS7y03AvstdEBsffJcT6BZYlov7bj7+Wcn54yhEHxru4/ZP8ROZm3z+eUai7HGEJeSKGYll5RglwCE0w7IKbJiuGh8cHZsYTNiI'
        b'Vs9xCROCguKzS6cTvVzKVuMC/5FLXacAgrKM/GLwslSnqILT8yxQmZYGboeyOVw5NKGscsr88Cjvi0+97BmuZVtxqf8PAgXZ1PO2sAp0qC14frYSDm+QCk8yEQ7sk+AJ'
        b'YpFnnwsv8DChHA6XY9g6bHSEx/MjE55wSNDWO5wPMWlQ6+oioIWR/obnLQ0MZhgaGrxb33N2YcZEIYs6pc/d2hsnYJFl0hxwZRH+fA1HQp+5tByEl3/PJSTv2LsGz3Wq'
        b'6TxCvLaKeYSVPvJ2/ePGfBkAXIv/r1AK0TyHMlaSoxSKfP4FSmHZLs7/cQphKfdlFMIsUuMYI4edz/8ZBKGs+zyHIJR1t98d8XkpgnB6D5UhCF/WseWYgS/slPT5v4ME'
        b'fB5rQXuwZ6zCzuiYVsGwG6Yuw2FbfocNnFZvDCoQD+Y0DhAN6PYCpz/K8JM96e9R/PJz/gPw+58D+Mkk0v6PY/amC/FLMHsvFOj/n0L2FGISidu4G7gATzIkN4biBvtg'
        b'g4zkht4Z+6Jo9+UpH2cWBUbgTh5s91uQ3xpxiyXCfvW5v6T0fXr8Ta13KI6FmoVJ77fzjwu2uW8Tbpu9zXqb/7b3HFQOm1qeHdV62wDUQm7KO7qvvr6J5dFSrurNWeBh'
        b'G+VR98ZhbRCRHZU7EaVENeeodAbVCRToiCBts0APg1HD7olgL2xzAc3gCvnklyrCbpbPg9TS4YF4jis8soJGnh2ErQXTfTHjwTUCKzuuRXtB7oMHwE7yjQ8MWBJOmBnc'
        b'Qm7OhLvAIR4YZP3ev3QlGnn/BTUSv55eSA/7/UtYHh0WQr+EHwXOobT1aopbysVanj25g+WjybeSxr0CRr1u+WBwWBKLLJrWcA+rj9Nx1p/jbxnM+p9jb0UiebNQkmdv'
        b'bfT5l9hbZfWc52Z4f5S5lSdgxZQ1/B3i1u9qXYbbikQZl8NtWb7kxfM7xJbi33day1SSyyBv2lRFYfpUBZVKhZmqsBl+ljrmZ3nwmKmK0rSpijKaqijJTVWUp01KlAKU'
        b'yVTld0enpirb0FTlO+4/ZGfJq17/J8FZ06HDzPyCoVEVoTcIxhT9h6X1H5bWf1ha/xJLy3FqFlKIRj75iNn/FFpLrgv9O9Fa/2bA1IwY2lvtegrspWnD4CKspwlTcJBN'
        b'04ZxqOW8Ah3ahjUhDFbHColTq/MccC4uLAJNLnB86hTM5FUmfo/gINijAq6U25GIMXNsIfGHZMHDv2cRhxWTlQNTMOghggc05GDGjXB3hRs6ZV2+asq8UB4JvDFKngjM'
        b'psAh2KwCh1GSFY54XqNp+IyHA3eFOdJ+uHBXNJoFaoKt4di6e5mtcoA1PF/hjOdI7ebgaCRoh+1O02eHGPDjCPdH0+b68TwlVOCrJhXz8LsQtGVhnvLeSJRc0sIUYXIK'
        b'5hNFREeBrsQwcD4s2kmIJp+N4dEoFWc2uMhzA3viEygz0KhRGOZIPAiDwAjYKqoMY0I/ggHTDaTcPNBk+lzaGLpT4lYGBuFJTNsh2CsutRzsUQJHFoBrFa7otnVgJ+hN'
        b'kF3N0JUS0V3x2ISWLj4pe1qOEirsgaXE9RFcg6fAXl6ZBqpIjjaruMg/TYfhULMIyHlgtQhDqkdYzvCkQxaoJR6dmUIudT8VzZLmL1erU1tD5R9LiOOKdNAMZOK7D5sS'
        b'rq0CLlpzfWueblqoFbi9NdB00ZmY1Pmjvq/qq6i4nmJXb1db8ovVcHF3zKce/gNn7q/45vtffd/6JMR7NI/1Veuh8LGVqcUlEawx8TUrpetGT/7a57xm3g+Tx2dEeA2r'
        b'jr3jv8fpyS1tlgm7bSLr5Nym7V/P7DmdMLvt1Alh29fdn3TdSypJU4jQKku2Vn2w56q0jFd7s/HD+2/qU75bVq00ejR61uvUG3Pd/rbh5rzPTSrXSTTm8d+v6zuxZMWG'
        b'lBMlb3/TcOLWu67uzn8tT9i/sPVEe4P1lXl76r93vukv2vv0v34adTWetIxYO3Kg5WB/2RmHrREnb5+BZzfWeduPw88G2z5uXzYzc5PFL9vfvr7hhg73mGb5Lx6fUh8K'
        b'aDNLUO+aSyy7VUGzDFSD4cS5xOBOHVxZgWbyQzOeD4UOBlJp0+GrKqA2EpzLlGGPwWmwi3ZOaHCfBfdkgvopLYDmyGiAPUSTSAfDoFqGPRaA4/IgmeugnmTO0A/sR0J1'
        b'nTslJbxVbNiwLpFoEYtALeiPRF3z0hRtOBFeJwaqsB/2gv2RYB8YfKZG0V4MO8BRYtpsDPvjeGAInJF5WD3nX7VUm06pMcKZpuFELkGCvhdWo0dpwKucKJSxU2TxTwDb'
        b'AuEeYv7MnctCSV0CZ+FleIZUUKCXWaQy6HSLwANJN4VGm2PgEF3zTaARdMqFp+TpwK2gDrTQjhQ9sMHFISLaKduKDDEo/zq2HNiANLEztDdDExyE3URR81diSDJzQRPx'
        b'yYq2httfgpIBg2UFis5OcwUa/6avdPiD43R2ixy3xfz5yf6LoC3raEjzg2TffwHagvEh5sc21m6U6tuJ9e2I8rVAYhQ0phs0oWNGCCq0OdBotsQ9kpwOlBgtGNNdcF+N'
        b'MrbE+JUaJQwwwWf8JUZzx3TnjusYHfM95tvijW0Ge6wGHHsdpW6BYrdAyaxAYokpu07fTKpvK9a3leoLxPoCcipuLDFNmrhcjP7ZLpcYZYzpZpDkan3FOvaMhthS3rGm'
        b'dU1PsMR29kdm9mMOwbeUbqu9oSZ2SJSYJY0ZJI2bWjWnNad1JnandqUOWkuE88hlIbf08cdwsUOSxCx5zCB5wthSauwoNnaUGnv36EmNAwa9apQnjGc1+7eU1ih/pm9S'
        b't6wzS6y/YDT0VvJYUvrY0hXjQbFjcaljaZmTHJZBNgaXaGfLR0rU+CMQkH/8AZzIxHTehxzsIwO97WOwkuqLDj1FOmrqHBYrnLA+wv97Our/DtwD6XFr/X8H93iR2vYv'
        b'kj34NNljTjr2wpsKcfePoB6gGtTIgz2GQGsF5sTDGl2wxcEU7JmCe4AeasUCfw6PsoTnOHAbmnEN0J9PTm50EoEmG7kwBaDViz5VkxwOD8ErYD+hdmBkB7heSF7CjQvY'
        b'1N5ojKte7ljo408RjgeshVfhFgbKgYkcKmjSNYLeAJsqsGAk2trRUA40WeihnJeo0cTLYxrgjKiUtQhexE5pFKiGh3zJ4xVzK2kiB3cNC92yjwAt95NT6irgZGQWuCTD'
        b'cuix1UCXAz2r7MYADAzlAC1oACZQDvRyu0IYCPNRFusZKgcmchSgyoDVJSQjHDTWbqIRGvhk/Up72FhSQd4ObRlgrwyU4QGPwCNTpAx4zInUx8e2+6mw9YSUsWqprRmN'
        b'ujiQYkl1zjiAKykwPjKSPjiZG0YtmmtDSBkhFUL6oFehOvXZBndMyijMc4pnbo/Xp37SoUkZ6WZadCREJAOJU6AMGpLxCqihORkbYQ/dbj0R8ChDw+DosmbAs76wPYik'
        b'aVmoSN33NCdR2I0rAigGXQEu5xSIwBHYSnuF8Vh8fVBL5mi+8GAUQ67AsbyvsHy0HcmJtTNVeWUc0AJ7KBpboQgvk6d7BeO5W2wgg67A2Ap4VI9wWUADbC0h3Ipy2EfF'
        b'wS4F0mSKM8EuGbIC9sAagq2AIxwmMjgqr4OmDFxBsBUBrvmzzq9niXDE1pgdl68t+m1PWrBu0/DwsazHRQdPf1A4r789sjB/5Qe721u/f9P+/QNL9nzzfr3f1UVBJ4vy'
        b'e68LHYODdIMCggIC0rR6d7W08OPP2F1q33U4PihI91TwV80TIxNZ7j9kP/y+Xhr+0fFlBxuHHn/kfu/xnzhD7udSz/flnK/NcGg2bXKufDX32x5goFPf+Vve6dRPNWaZ'
        b'fx8X5VObcuuX+2++vrSe736oWvfy64YNLg8+Yx0wnvQBvL53PCtsyly/8HL4bsMk+697i4ZbjNf7Zm5O8X7tccCTV16d5Reb+47CkMtIj+f9qtq14ZfUdK2PhO/XWFlX'
        b'/P6ZwvebfQUb9bewu+uuwdbXusIN3d+OuFqw++P7f9k809f71qTRnUGNk8bU4gnjgFNR3/bV9+/e8v717f1vza5r6eyPb/wxQnvBks/ClAz3r/n06JIr9/I+jHh9mJf3'
        b'cGvrG42n/ZoyjJcbqOxYZ+B3vWlxeLlt0GrW6ytebS+Nubv2rbiPouNGq5yXO973z1kGx9/u/O3qsbUFyavPan8kDZ1HZV40V/f+om7Lb/Wn7Zpb6+w2a6/VKlivXPCx'
        b'5l/8Ant3fTzxwOC1K5k+Dfn+50IelLZEmX8X+l5ji4HSuysuVXYqT95580SsS1zl1Vn5Z78Nd8iOTXXgvBL/gdHWi7uWLZr0ttj42nvSMYuVXi6PlzSVfPnxMbeje3TP'
        b'Xuz4LftLs/5vEz/4yCAz8t4kvGN/f13uDy3uIydcl4UsrgwcaV314w6dx/dTR//84Ev+3ZOdAU8ndWf56jaHflpgdgAsuhlfdXX9HNZ7I8oL/Q990GE5wr12rMXsret7'
        b'Lp/8+qD22CrgLlj5Z93XVrxz26ryhtd7O7NXXt5k+tWeqthuxR+A3huP3IpufhOz92Da1hN/7aZGjr//tzNFHtXXFeNWXtvxoKppxfHr3vxfG3TbPwi+9P2+No93f51n'
        b'oqLq5v3OO28Muzj2f7O35dY9t7M6mZKHHgVvPNH/sOnog9jf+hZqOzpm8I7oHNuqveCTX7yC7m3+6iolfPj47V/ab/869iVn98GPyg83Ov1S/WBb0vce7T9q/Mkhxbft'
        b'6x9/WTCa/pl53OHmy/3cL7sXeX9+K8+co3FgI1scmzEs4n+SS/3auGJx98hPsR8tY7/tde+J6vhrl6NnNfQ4P+zu8r81ONKa7LPntb1Btma8ksUr11mMnFS4Jz12+E/F'
        b'rTHlXy522JU5PLburYofcybGP17344MNE79cffzLl9c4jz9Zc2tHilJ8Q/ynBn7Jl193fdVg8PXeL68u2Ze53AhvGZ973fW+5qJPx29fi0bHfn1a0Mjb1HbA6GbLvZOv'
        b'D72z9Jf9K+6Of5fU9xvnTv7IzQDdlh9uJgrFReXaBawPVHO4tuPZE2nvWjYn1HaP3poX8Ch319LL7zm9r9Nk/ZPN9c2fGJzf/e469fFi7uWvK1rOBH37Jh84j/Y1Prrz'
        b'/cVbP0gTR7768Iff5lk47Pg5ummJ1ze3nSs2KKz5m/FXHbZtTzROVj3R3P3m8I+xuwscPnOe6OuPWXpvn/OrH7z6q9MGhUqdZO+Wv/n+vHbXJ+pZf/28/7vid/t/Tb19'
        b'5Wp7jv6JggpO6EjE3Yb5e2Nvb179W/SpyrsfxfZLElL2tQ/veBLtKiw7nrtY4ULoPf+8R3euNUd/HxU/EPpU5/GxO272Kx+lr7ZVnL2B9yh4ffGRgeVf2vid/s1ozt+c'
        b'r3C2X9NqFZQ8wjwt0GiBOQGXwOGX6CwqcAvttHodXoBDz8LZHM6jqRBwtwrtuLUDvQu3OziFgz3LnwdV9oHDtKP2Pn1wnEZDgF1JzBUYDaEB9tFBdc46qxOiQwJsfgZ1'
        b'IESHK6CXaEacDWkOsNX+GdMBAx3aQSN5gDfohA0M0YFrGP0M6FAFRx4J6HfClixCdIDtcIuwTBDhVBqO/b5lTAdfsE0R9BnYEUUrNGFOpFnWFNNhGdt+DmyjNdHL8ATY'
        b'7wCG9Z/BGw6wreE1sJ0oYhW28KIM26AHaxlyw0nYRM4GLo99hm2wRSocITfkgGu0P+eFcHhRdh624oBLz9gN8FoYjQxtFBQz6AbMbTgUArr44Bztr1ldhaYWMm5DSTYh'
        b'N4BdJqSG55rDS4TbUGSOyQ1y2Aa4A2nZ+P4yB3g2EnaulMEbMLkBnGe+pcGjcbCBQTcows2gawrdkAcHiIurHtyURKMbMoqcnoEb4Glt0kShATE0tgHsjWD8jmluQy8D'
        b'Gk2H532mmAugC7QQ7gLs4dOLA1264LQohrVQRE8EOsF1VKlYAPO98LIbAS+gecIw7ZssQy+kz2BCDXnDbXLqMbiALt0KBhmtuwz2G/LgJsUYoZoAUyvaWEi5bwbHae35'
        b'nM8amdt1AiZ5T3ldq6+m220nOGzKUB1opENFhgzqgMR3Oy0450GzAw12iAMn7WRcB3AE1JFEYkE3GOI5p2K2A56Mw2oBDXcw43JBb4ojScQX9sNNNMQBNHHCpyAOofAI'
        b'Ob9upjnNcLgCakmXllEchiyI8GwEu9Npj17szcuKAPvhFrCbcZ8FnVwCLPCCLRTNcGgAnXTeD1bBdnrFMUVZbvljJ2giySquzJQxHLhmrCh4Gpxci3otWZjoB6f8GYiD'
        b'kDcFwLVMJVVrhiT9BM1vgH0Lo57xG/bBQXphot1OlaE3VETT/AZ4BJwmjZZWBa9OwRsUKwm+AZwCHSTLWWDnHIbfcAJ1pv1TAId8T5rR0AOGQC3PGAwyCAcCcECazkFa'
        b'2k+Dy6/wwAC48gzjQCAOoBH0k6c7KpZFymF7W9GwcAXsQqMNWWsyAycZigNBOJxD/7XBXaCNrpPLy8EhgnFYAw8JZRiHYtQQZCisg4NgiEE5mMNNqKcwJAeUZxq6Owuc'
        b'o4jztRAejZI5X1fS/SRkfhAeNTSInoM5DqAP1DNoAKpSxnHADAd72GIMz8JNpAkz4eYo+ThdgaWgwSWGhkcPzeWIlMHRqUk7rJ9ByqHo60lW+4Rgs9xqHzweTM6qKc4i'
        b'eQTXwYUomWc56AAnCYoAXveDHYTjsCRuGsmBxjiUzCJde82aZBnFQYZw2Aj6aYoDPJ9Bd+0mYwq9aM7nT2EcMMIBM43ocaMeDGogJW4XDXJYynKGHam0bPWBLbqiYsMp'
        b'jANmOOyvInf5GMB6EWjzpikOhOGwqoB+HR5FbdkhYzhggIMikpoT8DgaJwm+4iDsjpARHOCZNAbiMBJEDxX7Fs4n3uSoL+H16stRSIu5zKIMYA/XAXaGkIwV+YJ6maIC'
        b'RgKJnoJUIro4PQJ4MhIc5k4tU4JhdZqlvRW9p6/w6IQ587ALPpIbcJANznkvJ+mGwnYlHtwfaUf7oSN11hKeAi20cAyDS860j70PqHFmuBEuJSTXG+EpVKQTcCf91lSZ'
        b'AkeY+nJBrWAZ3aPOzJzJA6dg5xQ5gnAjqmA9XW8nQHM0Q46o9CQNRYMj4hLp1mhGOjqaAuwW0OiIZJYQbIcXaGE5UrYCgyNQsx6Rh0fQ5Ah4eS5dNdfVZ9DgCDQIwUHU'
        b'hds4oXTV1IKD+gzsAZwLK33GegCbjJhW47jIgR70GNRDVAmhaaOuWAL2KMKeKdLD7zAPoM2S5mOgF+YhEaqnlbCdriqK0oJbOOUCUEOWiuEBz3SMHIkUqKCyhpOpABob'
        b'znAoQ7CZGwp2ULRUX7Jj05fhki5UQzOFRnYAdt5nIgHCrkqG6wBavJynwA549KCHIOtU5gsLrDWaWu0G+6NIXSksjpBbZW6PAmft0KsQF0BpATwiQg+NhcP5SJgOOKBB'
        b'WWsN5xXUjw7QDXUop8IBSR+arEWz8j1RTdWz13k4E0FZjwbLUyIcpaIa7EOSjSaWuHwsSnsmZz2aCj3CX3HMQW/BFOtiE7iCl5deDrsAO11IvgzAmSU0JkIFdghL5SgR'
        b'8y1pCT6jkkawMXCve5QMGwPr0skYxvIBh2l4ESYXFRqCfcVOtFgegM155DZQAy9FTXFxOlA14uZKWFXikJvwotwRiAXql8ygDS550dkDtbrCUnkSxwEDUjduEYYOoAls'
        b'Z6YI0xkW8GQ0qdxCsBf00xALTLCAnV6gcyagJ4/wAhqBnzEswDE+wViEzSQltIAXXGiIBQZYVC4EJywzyXPxawfuRYNONmiWo1jQCItX0PBPUJ9nsit5AvS29qAIvwL0'
        b'xJByrUf9qJbwK/LgeVU7OYAFGvIaSZa1UMUdYRgWGGChB9rByZR4msoAzs7hwRG4g4AsBCyzDRY0iKYfnIN9DMZCViI1KwZjIUAvLLJcVK8AjvNiwxiShRlbB+6zIa2G'
        b'OpznFMQCtmXJOBY9DEgHzU36Qa0MYzFrAQ2yACO6RFKK0UwT9sVFyFAWmGOBhojLtDrTvQ71oT3RQthjLoeyIBwLKwYYYrAWbiUkC7BphsoUySLDiEaMdXFAtQxksRoc'
        b'03wGsoAdaEpJpi5rVKfFvUQ61tUQU9hFWhJNsy/6R4Kz8CwBWqxh+dlEk1JXwJPwkIxWgd6kO2TEir4kgd7/MKGCxFN6OZ6CeHrd1Xv+i40cmMJKlf5Qk+P33wVTGEsN'
        b'fH/HoKhRuK9I8S3+jVAJB7GBg8RA+MehEi869Md4EroNGv8+ngTzEMZdtSWuI7E1sdOmLR2VFh9D5e9kEY9J8oXorKbExIdxS28J6YhtjZWYePxzNIdneACNeg0Mc2jd'
        b'KLWdJ7adN6oqsY2UGEThHP0HzfAfNAPKqgbOKhZ5PYmBHZYL9Xp1ufIzwAE5t97E7vSudKnQXyz0l9jNxUdVulSwn3VoV2hPyNlYVD8C+0kFBWubSc6U6y6HZ2g0Gcfy'
        b'wPAGDwJvKPzH8IbOvwtvWNW66p+BN0wqcFCzKf+3GQcR9REtZfiDr9Q2QGwbMFp2c82NNdLQVHFoal3EmMlipkfjxNRb1XHdhbWGoaykdaVJhfPFwvkoQ2JhsMQqBJ+L'
        b'bI3sYQ/wenlSlwVilwVSlwixS4TUJUHskjCWuFTiskxitVx2nZLEymdSSQFXKe6TWpSp+R9hJJiaN6fVpzUvq18mNfXuWXBJ6TGlgIocN5I6lMrU1ISDEDvtd8/rnodE'
        b'zVbYUdyjILVOGHQd8R7yHnW76XvD9+a8G/MkvglS66KxlEXSlHRxSvrYkmXSJXniJXnSJYXiJYWSlKKfxucH3FS8oThaerP8RvmtaEnoYsn8NFTzOM8KczEd4z80hf/Q'
        b'FP4bNIVU1hwMU5gjYymsZmGWwgbO/zWWwv+3EQoVHBqhEE8jFHDI9jEN0yq+09eUaZW1078VoHAH/dQqyQEUlvn9ywAFloyd4IYS/S/8jYWwEziYnSBEhwS6/xO4AxFW'
        b'IV5EOqBL7cJlfrBDtmjxC0AHji8AHTi+AHTw/LEc+phw3DR4CmoQNi094cuOYX6BC+YXxLEEhF+QTPMLOOoWDL8AbT1UJcSBzrk3Zr2EXmBN6AXWcvQCvP0gZope4IPp'
        b'BXP+eXgBfkw8ayI4fNx33mPOPPVs1kMK/+LHxKPH4O3HgexCNuYW4N/75JfmFuBVhGWwz48HGpdhdAGsdoyIdioNj4a7HVmUHRhRKAJbV00z29Fg/k4CzCzQ+z2xYMrn'
        b'H3vv6xC/fhXG319j2tGZ0/ZUn+25cDw4mD6QwJnNSbAjXirYRwX7rKglqSdpJGklzUia6aGWoPAcAUCB8AcUjagEpQTl2ewyJbKvgvZVyT7NJ+ChfTWyr0L21dG+BtlX'
        b'JfuaaF+L7PPIvjban0H21ci+DtrXJfvqZH8m2tcj+xpkXx/tG5B9TbJviPaNyL4W2TdG+yZkX5vsm6J9M7I/g+ybo30+2dch+xZo35Ls6xJPHV0PTsIswjaYmaTgwUqw'
        b'Itt6ZNuabOsnUajWOOhqxSTlJB66RxPVmTapMxtyhUGCbZlhLldlm0BwV21BQHRiEGO6lT9fmaIybNCYoYp9BuRP0UCEKYv58mIcT1pEX+Pp5kj/dSfRmvGWh6rMHEzk'
        b'xA+Qc2hh/DuI/ynjNYLOlmeXkYDRxZXZZWhPpCofMNqRn52Rmccvyy4pyxZlr5K7Tc5LBrtNqb7MNN9JVTWmGHtChOegHBILttXZZdl8UcWKonziG5C/Ss4NlzgjoNMZ'
        b'6P/leWXZ2apF2eV5xVnEexLlobiwMpuYwFXgRYPCNdiRYVqEa35wPvEhsAsQMM5dhWtUsZMB489CV5ozU2eymnLk2wUK+MxlGXxRNvbjKM9+vkJxHdstEGC/3Qw5fxbG'
        b'06S4LD83f1VGIXZQZaibqHjYmRYVQiTKyCXuwdl0lG50hi4ZPyu7JHsVKmAxnUHiqGLHnAvErV5ULCpXzSwuKsJOaUQGBE6qAs5dTlVR4V3FzIyick+Pu7yc4rLM7GWk'
        b'JmMyuXIDB7aUI/Z+W/Dim5rMJe0IxZgtqqJuzkNCS3dxLLAUElmWhyZjzMhNlPOGX6VgRiVx5YwZFaaZLXIDFIgx4++OTvOf38B+gf/8NImXc51nXGpQWWlvmkXRUYw7'
        b'CYmLTu57ZgCJmoK4MKH+Qfs52WXT8vCyziLnV04qcg52T87MQN1rOXrkctrNhb556iZ5uWGiyWdkZeXTTklMunx5mcESVVqRzfQXUQUS9qk+Svv/TnO9ooPG4y6QUVFe'
        b'XJRRnp9JpKoouyxXLkQ84zlchrpFSfGqLFwjdEeaHvKdKZ6cfMzBbmHY84t0bnn/tfxVqAIz6GSeDzFPPxf1W/nkiU85SSaxKqi8UMRfhb3gya3R2IcaFWrKAX6qyHRK'
        b'TG/OekGmaQ+3nGf9IZOMWSL6UuyyVigqpp3qUanR4JVdlZ1ZIUMNTB8P7OxxxPopVMJsJxd7wXSDWCXqeYNYsxgR/qCy2sKxb0xR/NhBcKZc8Iagf4/g/YubRVT+euX2'
        b'97bSL3IhhT/124O9oG8VPABr4QAO6FougNUC0A/2COBRcBHQ94B2OAiPk5jPicQkURleLgdnFShqA8UCDRvgKU1iJ3lEn6NczCEx59SqvJIo4jSjDw9UgT7Ub3wpcLnU'
        b'Fz2osfCnp0+fjjsqLE1nE4+UwpX6pjjGGGZt64I94KQIXoSn4W4NWL2ajloSFeOkYm/HotzgYUUHUAs76Yhezf7gGg8fh1sK2dEs7xVLUSokvF47aACXRXJJqKIfsBtu'
        b'ErIoyzkKlvDSamJF6QS2oanMMP5eK8TfGq5gU41LsAmlQypo2BHUMcmAU2CYzk24fWmMAPY6hEc6YVubZFinbAJ2apJYdCXgQAnsk51S9mTDbfqrQBM8JeCQ8xsy5uCA'
        b'5EJY6+7iyabU1rNhm+JKUJNEzq4GdeXPTitSahvY8LRH4To9ktn8UpVnJ1mU2ka2qWMRvGpeYY+z2gm2wB460HlYYhi+Li7smU00C5VFKUhTST+ysAJLSAlLWRQVrgPa'
        b'UIPHCWE/+YqiA/ZzQDNlUhGK6/Agaort8mbVsvDwsDoqMlLILvUHTSbwGtg9EzXXxUhdsDuSpwovloIzYE9EfAKVnaPlHWtLux8FKXhY0o0dVTovh6pYgnPcgSRsxwse'
        b'gN24nCOS7GB1GLZR2QUPRCbBninxJBbdseEKM6xV4XbQrqAAh4KtQZeAB4ao4NW6sAlcBtWouolhM2o0eBD2gTpwVrOkDHOzB1k2ESJi2IzuPgKv87xAl3JZJWp9Lsse'
        b'7JRZeG9PdEO39YMBtVJy2zmWlb8fYymcBPeIgmFDCbEh4KixlsNTS4lJcIUVOC3KAPWl8KIavmkTy4qrhmQJZ0XXA3SJwAXYCvtJimCYpYdE+SSdZqP5ctiHZtPPngbq'
        b'7SrIN71dieDcc+1uBPcWxYK2Cm903g9JbId8kPtoYURsUtjUDXF22otIvYJNsI+CzYU80GkEuwUsEkQQ7FuCQ2w7R8SAHnAB7ItlzKWM4EFuKbwKz5CrnIPXPv8E0KmT'
        b'RFGz1nHhYXNwjUjvbCSBtQlMI6LRSYWViu645hOfrxP/joLIg0NRF4ws30tJLZbM11rq+86ffUKbPFJmtdp93qnVOrPI591PWZvvKJ1p+dhzt12gUFWh9dUziU4qN7o3'
        b'Pd1WNXHv/p/G37jQ9P3gXcW/bv7sxicP3n5F9MqJv36vt1Hr+h2b4Tf0r9qobDh7iDd7seU2aVfAYXP3ujcaPn41y3PVj2+5rlXp13rv0+xPDML9lz4qTY2fWPuq9f2P'
        b'dG8vCUw4E1tg4dP1/R2HSNtPy93ibz6soASCWfljjlsOp2Qvydde3OfYl7r/8+L/h7n3AIjqWNvHzxY6AgpI73V32aUsvfdepINIUUCCDQERey8oFqyADbABigKiAlaY'
        b'SRRvipys5iwmMWraTbUmJjftPzNnQUhy8333u/f7ff9c7+HsOTNz3pl5pz/v8zr4Q4/XXO+fiv9eecOKNZpJGR+EL1y54oHqmUEwoqU58+pH27Z3dvxtRmqRYOXxlaXu'
        b'eZp0bSzccXz68abemFrTtKKLSmuf3FujlX7X8Mr5gyerbO8XpyuX6xd93V768uxr70uEF+cHvG8W9l5riGVQ6ep0k5yMJuYe3y0v/YJLXHLAE8u56u/1Skyr7Yy9RJdu'
        b'aV0R3/phydwpCZ9c2lEw68L1yofyb9++k2ZQkpqqfbtT8O3tN67uHFpWMy9H+2Woz1ezHn85M+wdcflqybdh4d9HmxRGaBQmvf+RR/ntd7sumS/b/MUPuiejbrz9d7cb'
        b'PTPmai2+uC4x+7cbXssy930fOHi2FG74RkMtZ1v8m5orT90Lfs+l8opT54DerZRTc4ZWvvnFSu2XG1QjBa8/KfEo+9rwhdqUnp1rblh+7df18eEDM5O+Xz15lkrHpsQP'
        b'9676ealD35P47yJVajTbZ/Y9X//yHaPHGR0vDSqX5OumGL1smcM5/APvcFfuwWuhLptqvs6S7n82tXHxAt6jW2GbPFeeLqmde84uqDZ604c1v0ZLT8Vq+1alWeneuBLm'
        b'3pEoKNjwQuvK6rNf3vKqTfipJFV7y8NwZ8mnCW9cnek2f/9g9fZPpQffvvPtg7QPns7ZsHHzqcynN2q+sqtoXfbFB19EvPj843eWh4ctjFqm8u2VtMHd3/1q8u2QkRs0'
        b'a/zw0vV7U0TfDqXeeWz5/Laq9bNf3plTcv2j9b98UrsiT7tk5cIFlUtifHp9AgN/ObXMINzCb+Gsg1mZPz472X7Ib8q1zR6FXy9UaZi0Z/DNp9wX9jd3dzwdeFGxYMGv'
        b'2zZ5zXabfuN0z3w91bmPvH/t2b5x6J0DPAuL9ICuX0/Gco58vdPe732TH3JuruZcsJNllUoEwez58frFoFskSeBSCeAcF7Rx4hzHwHbn4WXWcUesn1/iq0ZsEcWHdYGq'
        b'5OxbTwduRR16J+5cUZcLt3IpNPBxA1NhB9zkzh6br+NJRTHxKtQKeJILajgBVctYB1vlU0TwCOyfAFbVBv0EamVuSYHacrjfmYUjKhdwrSPgWRLP2gGug7VgbyDc4pyE'
        b'OVNWcYXghAJKB1vhXrgG9w+rkLDbxcqUch7XJhucZfF7O/3N4pLEMU4YGKEBznNn5MErWqksOqEN7CwSSWK0QOvvEbqd4CSBVwhBSxg2oIQdab9jSnGfzsK50Lxn1wTH'
        b'ENU60ajz30wEt5W8BntgKzg7/kx9JjzOIkaOW1SK4BWzGHAGzTz4JRy4Ce5B3yW9aSc8LsZokASxJBNeeHXgbgwP8cu9wAGSwmLQjAbcnngO6AGnFbi2KSjj2D4RzVsu'
        b'gT6AajIhTowPxxNxCvorURq2cJ+SH9wWz0KvjsPTYF0l3B4jESwshVvjtBLF8HwclzKP5IMTi4QK9zaXJBhLulNN8XJSBBfsBFdh/9LJLHynCXYsQh9LFDuVgmsJo59D'
        b'H7N05cMTHvAcge8Y8RUIgTF4wGawG+ydB7axzlPA8deQ+kliE5xiEjiU1ms8e9DuHWBK4jqCtVwWGqHw7THJg2fvrwI6XVjEym54DLSgIjvpgYlz0FCkQimrcTUTwEXW'
        b'+8dCcK4SW1MRMAtvLmfFyiTyUcs5oB0N0B1w5ysMoEkp2EWqVw3068EeEwzUHMW1gSNoFrafRSPtm54DatHUBeWUQASV4AEOvLQArGN1r2VRpgYSt0YSR0AgpzigCey1'
        b'JDhz2AxbQDNB+s1GDeePUD/YGM8Cm3clW7Nek8AJdxZypw/2k1dq4GoKytLs8Ug9Y0vy6de8fFEbPWmaROB9PHiQA3bAOi7bYA6Dq3gI9/FxhjtFWLAeDppCtQpJ201O'
        b'1yDAzngfBdr15GIWHeICOkFtFdI3BdBHCV7icio0WWxGA9jBZ51aJYFODIZcZk60KyMCFReq0VETfj7mJapHOspDOd8DTpBiTJgjJD6AFN6EwAEuXKcPtoBDeSQNZS2p'
        b'wkWjK5oX/B6PX+LCgkcPwTNo1tqjulCkwJdewGjm86EEF6YNrqOoPWMzP2VKq4gH++ZFoOdHX0hQiODF8DqorV4Mz0+C56aUv5pLYvolZ7gjOkGMYqVGqGqBI7CRrZnN'
        b'XHGlSB3N6AUcSmUlVwOecq/KZqU5AptBfaWoglV0lWKuMTjiBi84sri9EwK4GeU4BvTB/Rg7lSTC0HMlSh+e4k+OADvZNJo9wjRw4mwS4BRXBxwJAEf8WPT1QXgIaRNK'
        b'BCeAtFOF0kpENZkZHOxJpBOg3u10ZSyG4sMdFhzYy9GBXTYscnVtWRJGNV0DZxWwprowUkyzwAa4Q+GWh8U0geYwAmuKAi3s2FEH98+sTOSUwiMKvDm8EEm+pwcvgsus'
        b'Tyl4GG7mYp9SV0PYrmiNSQGSFMkSgxom6Rico7l6cDuPsoEnlbwouIFF752CW1ZXJgoUFghxaKnRCA7pmPGSwdXJ7Oc7k3QrBRywNYdivfgh/dxFFN4JnIRXK9EoxRYX'
        b'D2zkLAMNq9hmuh+ctRDFiuPEwkTUrWiX8FBr3zQzHQ082FrTEB4umSAeUkVLQzTUJCpRgjwlVNInYcMLRxSyBO4OUijJqIbMyVHoSJInmlH7gbPKiQuDWeDnRVU0zKLh'
        b'4ewrfD1cj/oa1jTDcpqqBn4xqs1CuG0yvMQDZ8DVSFL/ZWq5IgKlRCOaKrzMRTP+tWia3+9IymqSEup1ahPEK8Ha38OxyiwFpv9vYU//xdELye4fEVF/xhemP34PbCJZ'
        b'WK0Si4wKD0NdpHlDYbMHoyugdQVyY9Mm+0b7YauAvsqBMJlx9K6wB6OP/PtmDdjIjCPrwuS2znX8OzpWI1ONGmwaFu1ZUMeTW1jX8fdqys0smzIbM5tyG3PbpDIz5y4O'
        b'bebGmHnTZt59ujKzgL5ZtFkICqiOnWNMb5zOIpVQQPzsgaWf3NJHbhn2VIVvNKVO6Yk6mqy0mrSYnDTbFYO+am2/K64u7AMD84ZKxsBRZuAot7DBwArGwp22cO9KZSx8'
        b'aAsfucCpIfxQ7Afmds2FMnPnBt4HVo5tujIrjwblEUOzp9qUtfOLKZSJ3bCdr8zYb1jPT25k2mTcaFynrABTMTbutI07zqCl3E7UFtKS3TqjZQZj50nbeeKn1nJbYZtr'
        b'Swxj60vb+jK2QbRtEGM7fcBzyGrQhwlLp8PSmbDpdNh0towsxW2zOxe0L2AkIRhEZRlKqNfMbFi8gitt5sqYTe/K6Avpzu5bMTSbDkqjPdIZj+m0x3S2oGyaQxqzm/Ia'
        b'89jTWcZMSptJ2TJFMfsiB1z7Y64n9icy/gm0fwLjn0L7pzD+6bR/OuM/nfZnUzG1bnZtjGlKbExkTJ1pU2fG1Jc29WVMA2nTQMY0jDYNY0wXDiwemjm49OaqwVVM1HQ6'
        b'ajoTVUxHFTNRc+mouUzUQjpqIUpLbYJELsS5ySuJSD1aObRxWoxazVvMGSspbSVlrLxpK/xKS25ugf5ovG9mUxchN7Fs8m30bQpoDKgLxwfOao1qGM7FGPq12XYK2gWd'
        b'Tu1OjNCPFvoN8G+qD6rLDGIJr0CWzDx72DBbbmXfanzcuEFpxMS8oappVeMqmYmka/JdE7cPrCXDzq/JrEuHTUufKlHWTk+UKX2j+rjdcS3S5qrWZS3LjgXRem71cUgb'
        b'zG2f6FBWDrhSRqydu5S7yrvVFMfMLlG0SxTjEk+7xA8VyaxTURhtUp1dKe1zGEkQLQliJJG0JJKRxNGSuKE0mWUKTueBiVWzVaNPU8ChAKS1Bsb1i3ctHuVdENIGQsbA'
        b'mTZwHpbG3DWIGRFLu8Iw5qk3vjt+wOamw6DDkP2gs0yc0sC/YyiUm5jj8mFMxLSJuGuqzMRLbmrJmEreNZV0WdOm7ndNJbgRrG5aPSLx6wu7HtkfeT2uP46FTjH+ecPT'
        b'UlmUAjMtm56WzUzLo6flDRcUySTFqJEksQ3CVPBkCiWU1IXf0bP/xMSmJbxtahe33bjTvN1cZuv9nonPX+SiK+iuQeiIBLW+3szuTHyOPyC96TXoNeQ5GCSTpOJMiP5J'
        b'JpzfNXXucqNNPe6aOuNMrGxaOeLk02dz3b7fHgM9GN9Y2jeW8Z0xVHh79q3Zt0tvld5ecGvBcN4smVMhkj5BIb0vkl7kjKV3kJth9VK/r2ukYB5mDES0gagtljHwog28'
        b'PjB3GHZMkJknDhsmjhhYNdu32bK5kFs5tJq1mB2zaFQeMXNoU+7S6yru0mTMAmizALm1Y7Nhg/L7FnYNvBFzYZu0L5w2D2nAPV7TksYljIUbbeHW5ctYBNIWgR9ai4b0'
        b'bhu9ZTSclsmkzZClzRh2ypVZ5w2b5sk9vBv4BIopbQ1sCZQZuj1Toyztn2hTesbjKC2msKADOT5DH8GXe/z/Pgbhvxg78C7xOI6LP4wYFWZoWJimikJicqaf11Avc0M5'
        b'HI4Tprpweo4v/wJgoRJvMR5VdqPOaQTw/neoGScOcKO8jP3ow+N4GV1Hzz/JwaKTZXGJxFKID2ckLh7SUSbZP9I0/o8kno0lprn/VOIKC1TAV7B8Mu6ofCZYPsWBnmVp'
        b'0QRJ/sdCtHPuqeazpxxFfyXLdSzL+bGysiL8coSEbTZ7SIIPav5tiUqQRALOvUn5Y2ec+aV/KRbAYtmOFZF9iGXVgtLyquI/ITX8d2V7jZVNM3/0SO2/EO0NLJpkTDQh'
        b'LrHKRajIyOHc2Lncf0o8olGC/0KjhiZqvCS1DPMmL5hdRogjLWfOKqtaNIF2+T8k1zHqr+V6c6JcJq9Yvgkd8X9GiNP/hRDvYCHOjAlh/EqI0Jiw/5AMXf+FDPSEgqg4'
        b'R/07/Ysd568/dgd/zJ4zmmHHtD8hmx4lP/23s7+BbT7qhJ8yH7NH/pVoDB5b8LiwhmpIa8o/kD9OMQgFJdv5/EcqRYC7QCLVorK/kunexC7QSEEz+h+SZKzrmzVzHkYg'
        b'5JctLF7wV+J8OLHr88bi4Djscfy88SCZ3/PJ/sdqU2tM2sJ5ZZXFfyXuAywuTU0QF0f6t8Qd885RRLEOGpDI/HQqXcmd97/ioeM1AXfZRfUYDF3CqAACXZo5b96Ek3+M'
        b'ophXrEAZjGEjMElryszSSkJ7m4JyVTq/OKKioqwCBS9eMIYvKJy5ABO5zyoeQymoYyLdBQou3dIFhEi1chFqoqUouOMrntUJ6Cl1Be3w/NJKQv8r+B0VF25ZUmo88kAl'
        b'scob3YO9sGfOKxZQuBOeHc/KOQ3WJKVOPJbe46O+OpwiPF5wE6ifITLVRi9ixZg2QBCXkBxNDjOmOU7k60uFdbBGEpsAelKmieF+PuUyX8vP2LoqDiWz1BVsiQNnHKMT'
        b'JDEJydPg9jRHSYJwYnwR3J8cDXc6c8CWuUUG4AQ4mS0AbVPncqly2Aq2rdCGe0ArrKnCDkH0FoJt47KkyM4UPTZDv5MDbCxQm2qSXPr1vBpO5bco9l3q/vZdAeogWGfj'
        b'R9/e+KjG0XO/lec6vklEV1eibl2DPEvJffobocN7lphqz7TKu5n98dY3I911zr31zk/3i+7Hv3jwYFv0BpemoYovTq63E+tqrYguU1mlK7f5ZPbjQyriAft7a0sMe658'
        b'GbNVVdyzehl3iklWelrx4N458Pjp1Ty311VPn7z02z/sDR5V1l/am/Fhx2Xjg7qtCyquuD15eGpXNP2D28vgwtpHieszHgRN+Qe//OGCYi1XR5WTnw7/2giXH7vd/t32'
        b'rN/mhV/6x/FbWW/t8K435V84ZD7j06Crc15euWh32/+3tMNZW7dEZ89/SV064hx69l2BCnuw0FqhGzdh5xA0wQ3ReO/QYgofNpQos1QMJ/XABbZoQwPGOaUvgvVsMie5'
        b'8EzchC0+ssHnBvdRtiIlf3OK7FTqgA2gVmM888uKknF7zWAzZJkd8Hl2WpzicCwkh1CCLEwn++TgKGgHnQoqEh94ALORtIM6L5I+3D0pD2814oighmx5t+oScS0M+fAU'
        b'rAPHBUr/fDGkhPuBMT76e5MwcjF/tHneM56wtJjwjmygaWEOyC/QOPZkWhSH0jNkdG1pXduWykG+TBQB+H3WnTEdMYN8WhQhc4ikdSOHbJnYGXTsDJnuDGKCGC4zjhjW'
        b'i3jf2LwuVG5gVL+kfsmIhXWzW1N1YzXZvsgazsllcmbR6J/zLJl14bBpId7nqDjo1TyrtaylTGbiQcLly93ce527nQelAxXQayj0dtStqGHXtKc8jks6B63ZbDIwbaJZ'
        b'BueBiVmTT6NPO2+wQuYUCyr6ijtndMwYrKCdYmWOcTKTOJJc3NCs2yW3SmjndJl1xrBpxvt2Dg0RcmuHQ3HPeZS94xNlysLqkOozI8rE4sdnSpRTJOfHZ1MocRznRwJx'
        b'Wj8l3I2zTz/cUf1UqDO6hUb64WJNKAnhox/sAlf5r1H1lZgUcbyjgDhUURXx6PIxnjzgHhxj6MOiOP8ifh73Gf9nPqA2/N4H1NiIPNZV8xJLc802K1Xi7e7S7QdDMohD'
        b'J+LOKc3QW0oJJnF1fkEDNHtAd9GiAJ9JOU446QFbwJpZf+LCKRKp7D293+0GzyteoNgMxmGw+6YKpMmGpvXLdy0f1rH+Fx02RRLiTVRL/xhXS9+V/8u19OX/rzx1/bGW'
        b'+IlppXcqv+YSZ49GjnW4kureGWpUplT2pp7gdMh/Ycvsj5WwgfMnW/KzysrmKWpBXVELS0gt/IvFjxOvSEXF/8v44q/+94sfmwlghXu+ghpF+5LJmJIC7ctRuKBg0b5U'
        b'ura7lqJquGnjnE0s4JlPKPh03oRK4IbwSNX84elY1cz+fdVgk52Jcx3LRJYAstvapbIcnoPrvUbRXiujCLhxsTkfT5GWWMUWaDbbRlIk+My5WpVaFbAhVA0HPsqRgE3w'
        b'CoHHLQsiwYM9Qgs0Dy71pAg9OGwJnEoOmOMItTKed6BZyJb4RMx3njItRZzBBd3wLJUXrAJaYAdsJ8hHcMAQNuIRU6IJa8GOVzACJUpYqAROY7p2VvhD8MDKyoWJc8H+'
        b'URRbdijL3NkGD6A0xvhD0JjapBiX4e4ClrT0ADwA1uJT8DjYoY3P7PliDjjDgXUssG4t6AK7RAJh2DyWiRQ9OAG6CEhsvvpCxZke3MaB6yvxuV4x6IW1aVWKcXh/NDlA'
        b'E8fw1fQpNRUuJrp2Jyi5QsmUuBgncAE0xqBk+fhc/hLYrog3L1gkiXESiJXBBnVKzYeLvtgPm4g8FepwLR7awX54SsE01m4DzlWxZNFeOrB2FtwqTiRnccq5XH1wyI84'
        b'6CywhtgVTwyqYuKVCHMK4eJnCaNFAUpwOzyWNUGLNUa1eDHWYvUJWjxRh185T/nP6u8fBgCNP+ivOJFoab6ZEqWq+R0XozI3K3NZLdV2CpkN9r2i1QIo+2dJzcFLqEBP'
        b'w4Pmr6hHwHZUpB1EJUAPRxNXbA7sY+uWrdgGcJFgdeNWRVXB+soxFAe8lsxiePfq2lfGO4OD81GjUOWYgbZClua+D/aAlji4Nd4/lyU6mhPF0tz3wgNps0HzeHoncJBv'
        b'xSpeczG4OFM0jr4L6dM1J1ZnT4K1LgruLpa5y9JMh6dvCFoIsplIYwN2wXbsRAqcg21WlBU8kClQIijMlRiKMCE22JyLooeAflI4ibAJdoEjYMN4Gq1LC+EJEttwBtxL'
        b'+LtQ+XXGjOPv4ueQ2OAcaAQ7WWqwZbCdo+AG25VK6GvBqRUlIvRdiUCYIBGIYxPUQQuHsgYblXzAPtDCFv8etBBpITRchINrKjiAabgiwWlSau6ZoJ8ldBFz0Bz2KKWs'
        b'yjXQgNcJ77EQtJqIFKQw4CDc/EdimArYX4UnwolgvQshDYqHO7MlqPXjvghsJQ3HPlNpLriSSDw0aBpkwZOopmoJK84/Y8RJBGtV0Ny5dpWC0xjutg8GLZWvYLVL7FkE'
        b'bH8UaB/rj3zdRlcJIXA7aaZoobYbrsOd3liXB7ZMGd/roVz1sa193aKVM2zYjmu014Kd2azKHVyZAS/NGCNdAsfiEljFrwHn4WZwSeUVyRBKcgO4QpL0CsM9Idt7CEEj'
        b'6UBU4X4W1ls/OSghZRzBYTvq0U+wHVYHKqEapMUcTOfTDXooVC+nQDMRhQuOTHKCm0UJYtTQ+DNR/1nNwsdLURNsQCoWLXZKgDuRFqmC/dwVoLewyhK9FcNOiWgiIw8a'
        b'GK4pWHkWLWY15UoIuDAaSgnp8Q6wp4SnnQIvVjkSuazBXtzpjXV4qPD2TOz0wB7QLOCSWkty8gG18Nxi0L2IT3FgG1r5KemTvJvjCq2E3coYcOW/BGNQNsBrxH5gFrcU'
        b'7lHGSD7Y4kQ5acMzZBjUzdKg9PzXKlM6BfG/WC5hCZ03U6jkojWUMWn2Mc9o9mF2BhowHdWUsTuLYZVq9uHHOZqUIX8N5oOOlyursw8d/dUoHUshZo7WvM/Pnjjl4I32'
        b'jHjnwgZ1pHjGp0tFa1NU2eQAjqMiGF6HWVKp1GJqn5IllTAZd6mWqB/14pEdHU4iO3vi3uNKXO5xFlfiSZYlu311T82/pHhB8ZKFFYH3/H8PksBLvXyJP9kirgxkl35k'
        b'H+fVs7HYNWpotoXVDa8Eh8ML3s3KH05Nu5k9ZPt6Nrr/kczS1hkYcYi3E1ibGY7B2nAnpuSLIS4iYpOniTOix1esolJBD1cdo3+q4VZ4SrMATUuIMtnmLkL9uUCMYaNj'
        b'0DzTdL4/etBhDutLr20O4lZiN+qShe53s+Ym6YboXb38zf5ra0It9qb8ffonVlstBW1tr+tYb5jmKvXbZFho+6xmsoO97arvk55cjv854n7jOxKRVBxGaz9b+839gM8/'
        b'qHx85eKHQwnrtQ10foiQJz7+mf9A504N795Hpy5VODQcfecfnIEWleDcb9/lJ33t8PR6bbWa8ut3R/xvmR4I5751eohWpWbt8fUMN12l5C0/ft961dT43e92286vKf5O'
        b'ruHwt8v8rKcXLi0Ne2uD9JNH5s/XxbgdD9qVC7817ViRM3hPw3ddv7v+j8Yen4hGltbcvez05TfSnDckJju+GTD9uenYxvsys8cpV+cU3F3w9aV75d98uGZ7oJurRZXZ'
        b'YKpTxMmOu+dC56v9QJ1bYZa84bDZnfieFx4X+o5OPWAj8xV+oPtI7qmlZ2IpVU66EX96TufTlqsadXDutNLY345q/31lxueGosRdS/1s397zU+SvPL9r900+Cfy6/v0K'
        b'qPXiy64b0Fw22GquGvR9afQ2ady7Mz+LnPvJ47ceXfrA59e0i01vb5TP8zzzRnHY14u/WmL7ZfijpiprOsoh8oSzpUg58k2dnK++sOv8vpK3tSTL3jfgDd+3GkwjVDuE'
        b'hnMXh3Rrirf6Zt4tNY8XLzt3YPepz7ZYrd5ffOtSy9H7H35XFKElflN/Z+a+h0s/itU/kbYrNvvczNYN21zfWFL6dpvwxuyPFtzc9375ifN3e1MSBHf3viv6SmivV3jz'
        b'QHLmtty5N44bMwG8jy8cju2YnX+Gt+eeydyk1L/p0k3PPtgd7G5rHcVd/1lO2NcDEq/bPSvOTzn4blzYt6KTe6QffTWvzz/kct+K1ptPXtz0EgXKpV813+o9vOf7Y+9k'
        b'79hxv/rtwDvSn4a/6VHZPvsO86TU/WhwoOGLSdLN2j0PAz8r6bNfecH+F5+q7as17i3WWl2wqGHFeVlr9ZGqrJv10z/Zw2E0v/p0YwH38jTVx1+88L32hYVnXb7Ld4c/'
        b'k/z0WtHWav9bJ6uLvy/M/fjL5S2LcpqlU1bPWVuW/wj6f372B3dmy1s1X+lX9zx7/+65jq8qX5queP3Xoi077UzUbuueEVk/Xmr4uO/qsxeO7zkf/MfLWb+c+6Is7tHn'
        b'/COfhUc+nWS7LUugF3J2qm9+WF5yTurDnz/MV/3yk9qzUY9Hbj9ceP+sve/LVfUfcX5wNLErUX571W31ngOfZg/WDn2+Xz5FFNmv0vUo5U5JeWbRif21uVl1Pe33NhRc'
        b'+dSpMP/iIY/N9UZdz7JfLH7jbx89BM9n+n34692Ru4kPyx+9fuvQz8r3Ln0D9n0k8GEJ5Q6HToLXYB2ew4A2PhmNrniCvQSWluK+EKzhaWAKPzVHtMYQK1OTQSsPrRF2'
        b'KvzNmIPTGhpCzOKJOoKNETxK1YSbAVthA4EmllUtJBhYCvahiUgHBc4mKJGvaqKZzaXl2AJnHEoXHrMh4L8ZYG8AuABPisZBqcFmFfK9uSmwHs3ga8dTU4Ijc+BRFgu7'
        b'CdSD+rJFEyeBvvA4gfCpoKnjRpIZHW55vLNAmZqEAtkHgV3spuIxW7iFQHh/j98thDt4sN7VkUiXiuY1dRjCGwrbR1kzp8PdZCPRJAV0VSrwu0vjWa7Nk2osvLQDbAUH'
        b'NRxBO9hTxKe4aZxAT9hNSikH5YllX+VoSKMxSLdhOdljkcKOUJY3liWNbUOlgolj4WbWh7Yfmm40aK8az8F6DGwCPewGzbEgdQW/KkuummeF6VXhHnCGJZLsLTYnHMJO'
        b'VFUypQw6uFLXEpJDtwJzBbkz2JbFYcmd4ekKUsLBsE9dY5QttipcwRfrD3eyytQMGiHKJCabBXU+Cr7ZBQYsbnOtP55UYZZhzMyMqofvw0FL1b1ubN2dh/3w2CjVLWWo'
        b'RKhu80Edi1cGDaaVcGtMDOyNgyeMuJRKOVeIEan45ZJC2KKgEtWAbRyWSrQDdrCs3OeWwm0YyVrOQoXVwb6gTC64hMr8vIJSscpMA7QvxGDXTBsk8wEO7IQXprHg2mZ4'
        b'LQ/HBju90EpEj2MTZ84W37mSQDdljdgEkTJa8lzioBVC/SRS8DOLF+P1jJokTqKO53eG4AIfTXHavRZMI3YKC6t0FZyAYwyjemC7GjjDg3viqwm7no4xvIypQH9HAxoQ'
        b'xwNNMeAIm6/rsIE3Rp4JL4N+DkufmQ5Ps4jjk6B+KuxhbRWq4A4FBeCxctK0q1RCWBJtLzwNGEfBjeZje0iIiBJfBZMpy2OKliLNhMsUOzxhy2AzODkFtM/QqJqkhpqi'
        b'FScEbAln0bKtaA53ERPEYvsCU1BDKUVw4PZQ2EtK1aYggpvwigAShW0KY1NsngI3VybiHqMDNoBLaCoYy2fbT2M0agsExgz2ZrK0rqdZo404eAB7+1UQLCrBazxCGZmR'
        b'zsL2+8FVwUx48RVtJDhiB1mPWvDsAgtCVDueMHIpqOehqf06WPOC7GyByyGomtM1WG7HpbYE9J2C1n21v6N2ZIkd4QFw3NfBi83O9uwCDULsCK96sdyO/ebsucJVPu4q'
        b'tmohxUu0X4CqLo5rBftWEpGtcsBmOzRNfkU3CY7mwW2smckxeEFFpDC5Ca9ijW6K5hHN0oc73GGtUyLqqeFOJw6lATaiddRpLjyLlH0HSxJ7Kg31CDjMNgGswS7Gov3B'
        b'WS48hlap3SwouyHXGK9JC2APXnC0cKaBnmKi2NWgP1WU5IRaL14nqVAaNubwGhf2gl511k7ofJilhhDugLWuqKwSOO5ueqymXtQHHbisVjqNt/ZQQcq4gSXvRM2r7/dG'
        b'SPBqBbjChR3e4ILA6v8e9vzfQbdZUX+ki/wDRJqd/6u/mtXfE/y3FwBkm3a6iuLg50VsDIdy8mhWkds5YYDwsbxmrtzGoc3tmK9cLG2OlDu5tUQ8UNw1R8iFriyWtVnl'
        b'gY1d85zWwK7M3rzePLnIrS+yO4gWhTGiSFoUyYjiaFEcI5pGi6YxohXDaTnDxXPpGXPptHlMWhmdVsakLaLTFjFp1XRaNZO2gk5b0RwudxC1Lepc2r5U5uAt9w7oUpI7'
        b'SRknf9rJvy9joLg/j3aKZ5wyaadMximHdsphnApop4KXaGmawx0umssULaKLFg1XLX9CUas54dynFLWY/VPMieC+xH+msb+msb8y2F8Z7K8c9lcOt5nb7NGiJhe7983u'
        b'zqfFEYw4mhZHM+IEWpzAiFNocQojXjWckTtcMp/Om09nLGAyyumMciZjMZ2xmMlYSmcsZTJW0RmrUEKeLeooofb8UUa5MFocNppe4VDUrSQmPo+Oz2PiC+n4QkV4oWu7'
        b'MyMMoYUhqFJcvFjCqBDaJQS992mZJBc6oedO0s6kjiRUZI5OmNavU7srhXEIpB0CGYdgmUOw3NG5U6tdq2tR79Lupe85hjxVosT+T5UpV2+5k6RtaXuCXODSadZuxgj8'
        b'aIEfErEztz2XEQfR4iC5SNLp3e6tSIFx9KMd/RjHkL6KPz55osTzsH9O8ZwcXipTjuKWqmPVL1V4Tl5PlCmp1xNNys3nqYmWqzUr9xNzyiuwr2RImQ5MpD2TGM9U2jOV'
        b'8cygPTMYzxzaMwfVglcIdzh/9nDJguHyarqkms5fwuQvp/OXo1cFnBBcQfgPSi+ItpTKPQO6yxjPaNozmvFMIkmm0Z5pjGcm7ZnJeM6gPWeMhvTHztiKB5No/zTGP4v2'
        b'z2L8c2j/HMa/gPbHChQQgRVoeF7l8OLl9LzldNEKpmg1XbT6Jas7ChVq5g7beNOWPg9Q2Vm0WzCCQFoQyAhCaUEoI0geKLk5d3Bus/J9G0Hb7M65nXNHpD59BAE8sHho'
        b'9uAqmTRjODuXluY2hzYvaYl/4CDBbJXNfLmXH8tbx3jF017xjFfR8LSU4dRCeloR/qCUtnRH9cPWDSMOp8XhSAmHuEOet9RHFcy1Mx+rWAgtDnn1iPAYYvJHxSOJW+ec'
        b'9jmdZe1ljCR+YMpA1KAJeuPVooEDj9U+UvMBt4HZg76KWKPslv60yB89cm9RxcGz27M789rzFGGcpZ3L2pd1rm5fjR54t2g+8PDHCOre/O58xiOG9ohhPIqGMlkC0Xw6'
        b'IZ9JKKITUOaaA2lLN6yI5u3mzcpyFzdWUVBnwwrPNpYoWhzFiONpcXyz+n0bsdzWvnlpSwJj603bevcZMz4xtE+MzCfujm283NmDZRCMvOMc2Rw1MaTBddN+U8YnjvaJ'
        b'k/kkvGeb+JRHuURhL/ISd3yCjLq2CeH1MdPkWOrv2caj8BLfhy4eXbP6jLrny1zCFdKy8jOCAFoQgHLhFYCbXO+q7lWMV+7QlOH4GXRM7lhF2tgN23syNl7DNl594yDu'
        b'w9Ny7/jnPtGhnF2HXUNoSSgjiaYl0UO6MklCc9RDobit5LRT32SZ0He0YVfccfRFEokk7Ju7Ql+kUG3lLcsYBx/awYclWh1QGeIMqjPBKXRwChOcRgenoeyGcmI4Q5MH'
        b'jYcyh9Mzbk0fdgxsU+nitKt3RfWFdMeOoBSrT/v3ucpE/nKpb69ft19PQFs4umWkEbQ0gpHGon/ygJAubpdnt/pDB2Gb17EVXeWox+5PHTDACV/OH56WLAtIRn1XH6db'
        b'nXEJpV1CGZdw2iV8yGA4OeWWMROTQ8fkMDG5qGjkrt59k7uN+ypkriEDmUPJg9OZiEw6IpOJyKYjskeCwunwAjorXxZeIAsqaOMOi/zedfR/4CjBpTDslYPL+xXzo6K4'
        b'X/A4gnxctSK3Tkm7BHWXQtdOUbsI/2CEAbQwgBFmDhjcNBk0YUJS6JAUJiSTDskk4RihLy30ZYRBtDCoWeW+jfBsidwneMBh2DsWNdyVtK3HQ0evYe9o2jFpKBRdmpUe'
        b'uHg1Kx2fJLcXndB4ls9Dg+mPhFlufbRtoQlnSJTqgv58YBYZiP4o/D3eU1u0pKh40czSeZX3VPIXLZk1s7L43wHHKzw/jp8isAeq+zHqoB5d7PEWny969I811MuYGA6H'
        b'Y4nh8Jb/wqnqc+JmUNmJ6tDw4pH9zyv6XHyw/VoEr0CzhbLCNCtkdtkIDmLXPkvHe8dRSiRkD4mVYEvceKwLPvSHe8FuY3CMD2qtygQ8spEcBU7hE5pL4NQEFzt7wFpy'
        b'VgBPpsP6P6QDLsIWNp1V4DwJB3aCHgpNCneiqWyMGGxVGK/DfRLKwo+PvnutgnCxwD4TcEGEF6ujyK6F2KIvOVrhxYADL4J6qkBf1XYx3EDODUCHUeY44gx4EK7H5Bnz'
        b'wXaHKgFZqKI5/O44uF2MVutpC+FasBan6OqhwJxRlK+tMpqIq7JcMCcWgHPYcw7eP0Vz20z2846vTliXZVMzwAFV7VJwpIpdO/Sa/zFj4GgZm7G8CHJWYgA2wY2VE9Ny'
        b'gFcT0xUeoXH2tsdxqNmrVcHRyDSinqUqWad4laU8ivoqM/dq5psLZMF6Zn6Lv3x9KeoKPb+waYgShcdtfHfdumYnocdBndIbBhGnNug5poUO+plbUFOm5FxaW0Y95XQE'
        b'O/1odG2Nn+775X57hlpqonc5VH/r89KH2XN54+ZPa4/HJNb0Rm75ub1u/aLP/awCOaHfqf3UVJ7/fGq74PFjflK+yvaTn66cc8vt5IWfNmim9L3bVL98udQydfK7wceX'
        b'vxblN7tif8Kd9+nIrxyMH1XcWlh9fntB1Sc6bwn+fr7tiatZxfp33v3qhxenJCGiE0UZdw7M2+Gw2qGtLvO+u9L1C4Ghe38r5Tdm8RsHQquEB98ZyYp3y5ryc+yhc+dG'
        b'FkfJeyJuZITfmKP+9azQazMaRJ+8peJ657cjzlPnSmvi37h4aNvbSVtUUwudC3/+rM3NqWzHFWf+/U5h30Hp8nyNK5nd7ZeSS94YuHY6eMbu4msc5atuPfmyf3TrfXVz'
        b'95MbzSbnjrjJ7BuSkx71c3U/f5CenfSW/ub4ZwNqAU/eDix+Z++2GalDF/XOzXb7zfVRRUHC4NetPwY+3uO4M2ial1nEz9t/O/r+512dkR/94LztzOvbPh/qelTUtP5M'
        b'cbj+6WD9z1qUNYbXFGetd3PPyc5o31OyP8irZfni4saypVX11T+fafy4e4l/Ho/OkF9Ptih5Ynq+9ehp7tXX5292LI0tbqBXrZ+XPXTjI6WOL0sGttrqH/r7c8nTqdON'
        b'iyZLr59Yf63zmznXPizTPBZz56eqe5mffNY6ZU/79x6BMq2XoYK3ynf07D/a9839m92d66sfbfCxT36xNuLxLc8975i9cylw2f7ZBUneXtDn72cuHf/t0omyPZZN/TKj'
        b'DR88Ca1REw1U1K01PT3/xFHjKzvvDuz4sH3qjV7bjoFroJeXfWNqWJrh07WLKwxfZMR37ehY+b0WZ1PT5hXvOu0Ua/r/+o7K8iU+H3y12jhyJPzGT7cM97y/4IvXxO8m'
        b'7IDxQsmj3qd+PwSUevn4Pfa4Til9eWu5ZKZoZmta9Ocac6ZGXNe7nfG16nLL91Tiut+v2BVY12hjev8kv9Bq8aaggqLWH78svHb/wIFdRv671R5/mTlU8+G7K7c1dpfm'
        b'v9e8+ZzTz63rdpVNecZ9uupW9cDSDdlFkxyfqj8x//pZTnDyG+qPbE+L13nv/PCrDXL5Gwnvvvm8xOmzT7O0vqn/5PV5j4JOf8vsCjy7akfGzU9mf9m+3+dX3o/T3wrZ'
        b'/1ggIQbn5fCS8He2xL+zNgfr4RZicQ5rEsgWgBHozCVG7Gdcx5m4b5KS7Q5TcBg04j3ZGTPGdmX9BWRvJWCJdIJVtY4Zv4qXDPfDXrJ+TwbXZ+Cd0wrlMRqKY9Ws4XYf'
        b'bIET8ZAYDTnJchQP2aNG9ggqQTs4N2ELC15chXexvPRhwwt8UAebwm3iksQc2OVHXJjbqLB7NC2wC9MybBNzCkEX2S3LBeeJVXYk3JI5SveAD8rhebwNANeDq5QZ3McH'
        b'52E3WEuyl5EP12sIRdjRGcmehi4XdC+H67X47K7WdlQy2zQc4NE4uK1cwKGUqjnwEDxnwG5etMG9DtifGLYnR4+3gH7tpezu4+UI30qFSzhs4a9ezQWX/MBpfTHZVtEH'
        b'u8IqBWqoiGrHDM5nw31sbjdHVmtIBMpF4RQ3k+MH6l3ZzZ3DheCIYq+KAq0qoE0C69hNlt3a0vH0BLANnsQUBREQO4ZSbFTvhzsqhTECYzyeEEDFOnganlX4CYSXbMdc'
        b'6OG9uRjtUQd5XdVsAkfR8HAC9rhZjuciCQSbyU7NbA1/bE2OTcmzXMcbk2utIKrnnaU5uvfEgUems5tPe8Bpkq8sV3hIo7RwnP8kcFmF3VLe9Bq8WomqcCdch3ceeUjw'
        b'dg7YmaJwrwQOJAvwBvr2BbAPYx144DwHNAZ6kV2gNDSO1mhIEipwANC+CBXcZD24PYs3J0uq4HywB3vxRiwpszDQRqlO4hatBttImVrDNh2FY75XXvm6J4MT8DRoIpt5'
        b'unlRCrKbV1Q3xs4s2Q0XriFhHMEFcPxP6G7gJh/YkTKbqEJEDB/WotkEOATqcRNK4sA1sCmPdQNTAddqxCbAa4Fj275gE9jE5n4/6FgaB9rhsfEuFb3nKEgLYA84in3z'
        b'gcPw2iv+gLVhpHCs4HEzDFMSCiRTUQrjqGs2TiOHE2g2dAiuHUeYQvYr0bxpl6phMd96CawlZRgALqaOIpJRm7tGqXpzZ6GMsG5+QA9s0/8dYBnJmQY7WcDycnsijCgC'
        b'NrH7xqiqLuCt33guOFUI6mBjHklnSbkEpYJnUGDLOCQZ6HehXKYr686D54g3SqTPV+1edYqivPHd4iuChQXJRLkMneeMmxSBnSpgPZfSms5zTVhCehCwDbbCC3je5gyP'
        b'TvwwJYQ1SqgL6QsklewKNqOGj9JKglviJfhjKqhj3UJp8XhWi1BlkYnuleI0WOsF2saRDMGzi/9XdxpV/7d3Gn9HiM2uI0K5f0bEQLYYyXbifLTE+JHgyFdFcShz66bc'
        b'w7l1EcS0/YRxg5LcyhF7Ljlm3qCMzeWDGoMYE2faxLnLU2bigxbFjeFyM+tXTAJdGTIzP7mNbWP4JxjMHTVkd9v5ljMTm0ejf855Muv8YdP8B1Jv1tcII42hpTGMtHQo'
        b'4/Z0tKDNek2WUNqgPGzhTBu6jIhcu+x6Bd2CXkm3ZMDupmBQMBRJh6bKRGnDmTm0KKdBuWEJbegoF0jYvTBGEEwLghlBxkDkzdjB2KHFsvAMFGZxo5ZcIsW+QxhJWN8i'
        b'RlyChBLfErNw+OGC2XTsbBRsGW0oHBHh3QOTfpPr5v3mjE887YPt7kWpo1+ydmgVt4gZazfa2o2x9qKtvRjrlD6P6wH9AYxfAu2XwPil0H4pDSojAs+u6gG+TBDBCLKH'
        b'pg5Py6JjshWyiFw6fdp9Xu3NMKLEAaWbaoNqN7UGtRRfemBp16rVosW6aUCVIJCwOxX+tMCfEaQMKGM2giFPWXCKIlEUnrh1cKEtXRqU7lvYtil16fVadFvIHIPltkLs'
        b'X6etWmbr1RAhFzo3VDdqozroDewOZKTRtDSakSbS0kRGmkxLkxlpBi3NGK2EB0gPUPWjyrcg+x8WXtciH1ja44+9ElDOPmC/zj5iLL1pS+/fvfClLX0ZyyDaMgi/0GzR'
        b'bNVu0WbdGTGWcX1K2L/Gda1+LcY7jvaOe6Km5G3eEIm3X0zdX2ot5Bg5fU/h65MiHmUnbE1sSWRsfWhbnwa1EXtBm12nuF3MCP1poT8jTBzkDcRALZl9UoOG3MaBJdRg'
        b'bDL6+X3plzXQzcDy4fSMwdUNqvctHORCUUPcZxaOD22lw+7hTyiOXSZnKFoeHPeUh2/lSensTUME9sLgdjhhxMyy2ehgXlu5zMylT4/xiUX/PrF1bDeWWwqe8LjCMI7c'
        b'1Ufu5PVUCd8/8Athb55TXLtwTmPE98qUuf0DiXtXJt7Qmz5gdNN80JwJSadD0pmQ6XTI9IbIZq/GJLlY2hXZnseIc/qWXl/Vv4oJyqCDMpigHDooB4XwbEwcsRG2+dI2'
        b'cQOR6NIQPiJwass+bY65R0ZsUaW4IFnsAuTe/kMiudgVyWAX8MDDj/xFWVGlxJ6HE9hWKrOOHjaNfqJJWdo2LW1cylhIaQtpVyxjEfSuRRDKtIMTY+9F23sx9sF9Hg1R'
        b'cgv7ppWNKxkLV/Rv2MJV7ixtVjquKfcIvmPp9sAn+LpFvwXjk0D7JAxV3155a6XCbYj3rGalO5Yechtha0BLAGPjQdt49OnhzTqZTZhcKOkUtgu7Mntzu3MZjyga/RNG'
        b'N4fJJa6d807NoyXhfRl3JOFt3BFnty437DjkA7fA4aBUmVvasFMaEt3FjXEORv/we+npJX1Wp1d84Bk6HJYj85wx7DLjCY9y8X8gdmbEgbQ4sK+cFocMpN3MH8yXidNG'
        b'nNwf+AVfD+wPZPySaL+k9/yS2+Pawrvs5M7u7SsHtIZTMu4GZ8ijYm4uH1w+nJpJR2V1KfVqdWv1LZK5hD9VovxTOE+VKYHkqQ3lHMF54Ug5+w37pcskGcOOGQ/MbQ5r'
        b'vKhSpqydnvEoc9GPxNfDhum6OUaceyaB6MruLOmwIPtGpb8wTfnXBgmdP+wsjR8TKm5h+yM1BdUC3ltaicH6JnhvyQT7hjD5V2D7P+As6N5Tys8v9HC/p5qfX/lacfGi'
        b'yopgnJ0AfOlAIe4p5xOr3wo7/EQZmwx44TtfbAWrmT+O0bniOJbzWxziXSxsN/7piMOK8CWHhyKo5C+ZP69s1hwBNzFSYFyxHgfZgC8b8WUTvvyKL834shlfbuKkCkhc'
        b'BTXBPc3xjAD3NMbZ4Fek4tDbcbzf8GUHvkzGNhRqY6bG91QU9r33NMeb196bNMF8lbUgIgYqxEyCFH8NLrH/C4d2f+I1Y0wxGL7igsn7KzdhEzPsOENzks4zU+xNwq6F'
        b'12DSXtwd1q/XXzWY2jf3lgedkkln5Qwnz6DzZtFFpfSc+cOFC4a9y4bFC0es7LBTCYeX/ELOJJ+XFL4+JVfsU8LhCXn8NJ436rkiCnuuiOHUhKPGZGw9oiOW6+Fuy1ha'
        b'E4ueGFiM6AjlerhXNfCpiUJPTG1HdJzlev7oiWlgTTx6YmIzoiOR6wWjJyahnJo49EiRdjhOO5JNW/EIp60nJU90TUZ07OV6LuiJrltN2KswuOvWC2OjGVqO6IjkeoHo'
        b'kWEwpyYaPTKyGtFxYlMyktbEvJLSGUvpOl7KRCzlNA4R08xuRMeFfWSGHiW8VNWfZPWdhDPJ5jtlziTTl8ozeNjJBr4+J1eWm5uwzZ18zYPsCsKtceXjDWaNYBu/GO72'
        b'nIBkJfBZ9P/nC9AlUJXYLmFvDqNU+Wrp6u6qY5ZM/P+gJdOfmstMtGQqSaxKxDnaMH+J1MXdzdPVQwp6QdeiRRWLy6sq0eqjC56H5+BFtN65AHu0VTXVtdQmaaCVUA1a'
        b'C+yG+1KngS22cBesz1Ci4FnYr6EBm1VZnu8tcCO8RJCutSJMi4hWrLU8ShceBj3WPGywAC4TxHEWaAR7MdTXdS7YRLkagnWEBXtmISpSd8w8WYui8sC6ChS3E0dsh+tI'
        b'RLgVLTK2SlFe3MAZI8rNTr0KL51mT0PLu1r+YvazioiHUcTXYC9BcJfDflAvRe1filaOpygpPAKPkp33RU426FMiZxe0jtnJ41B6dihWnE4VbrY6XLhOqkxR7q5gD+Ve'
        b'RrHmOA3wJNgHawP4o7nkTUEfq0XRTMHhKtyc4TEfiRSpgwfsW055pMDdZH++FK1E20RGMSR3OBqX0tNFsSw02EhHpoO1UtRheboVUZ5wsztrJXEBXIuDtR4+OI4iEgdF'
        b'MpxNIoHrcAdHijpWr5VwL+VVHUY22uepUIo68CxVAS2oLEA/ioMWyG0kX87gwlwpGvy8QbMG5T0jgeDDS8Da6qnRpMZEKjbsVxKy2UJvD7IDPejGZxo8QvksAnuJHQS8'
        b'gmrjIPpOXTGbI1QI1qMV1pXC2pPUTod7QQ+qL18/0Er5gh32pMJgbyzYwNbxctBaYclV1BdshxuIjDawZj4GUYeCBk8qNHMKa2xyJW3ObHOSMxTVRlHswhDyKctgeBBj'
        b'vcNgK2igwtCiey0pDVuwC14REWUMANt5oMWfLXfQ5M3mbg3YbImNT8MLS6hwpCftRBdt3IzRh47D5lF1VpmlKMcU0E8+GAVO2WA7vwiwDSlxBGouW9i89cHr4IpIewYu'
        b'ERJzClucs5Ey4loLB/vBJmyGHAlq7KjIOYsIwHsq6F+syBpbmGzT6QS1DijuzCgiLGgNt67kYW/bR+E2JEG9N1FKO7AWaUgWPIDigHWY/x1cwdXeimIuCiMfNYWn9SpR'
        b'pUfngOtU9ArUEEkdHsiAzSKwS4NUBRvRf7QOGyvYtqMHTmNQEhUDmmEHFYP6h24iMTwLjoGtsBb0YX/gCtWZNVqTW5RZFd1msxDTqlKx8MQKKlZZg0T10pjNlqtCr9m8'
        b'1uap4pj7wCE26sVklCPsrCCu1IWKW8Eh9SmIQb3BlTCiPOvhuQqFFsBr8GqVAvG5D5yFPahG41HtHUPXI6COFJPUARyBtWnYgk2kyPBo40iCV6qwg5MsARf2oEpNmI7+'
        b'bxDOVmhLGTgpKgKEp4CN5s/WqFo5q0IHjW1gjxI2yOnOohLT4DZSuAnTjFDhHMC4SpJRFXB0tFJQd7WD5HGhKwbVohpNWphAJVWDbeSLnHiwXsTqANgP20QqVoo6gRsT'
        b'2HaFin0Z7EH1OQ20V6LLBRPWNudaIurayMdQZ3w1dKxhaRuSz5ksC8f2Z8lBYB2VjL7cxGrBfm2whygcWAvPZGM1wILuw4KuAWvIFzXgWrhWg4+P0XaDQ+i6rYx8cWk1'
        b'2ExKZa29LY7or/igJbhGGvIkN9iogaow1S+eShXCwyzN/fUYsULXx3pRXI9w9zwUVQdcJZ+EB9H392Bbk7Q8UE+lwc1erN7VzOWMaQ/bWrCzhP5QW1xCNcFs5C1LwXUN'
        b'VJPpqJO8TqXPRPnAHb6LK7xiAo+z48T6CrYeC6LZUl3jCms0UD1mgLWgE11bl5PqSC70VfRwDbAR5XRsWGoAl4jWGM8XaqA6zNQxozKjUMbJVvFG0A1PuCLNIR03mm15'
        b'4Sj11URlBBqwTwNVXxbcDk+g66EcoqGhMfAUrFUHHezQCY6SdszWINJQHLMY1PuCWnSTDdscqWwruJFY/sB6LXAY1KIKmo6qYR81HZyBJ1lDql4jcADUojrIges8qRyA'
        b'xmHWxKvfFY3ne5Sw342jsAtdT6HECBNx9xy4Ae5BWXKG9aALjRhd3kR/VoDGRdggzyoVnqSsQuEZIpIx6FSHe9AHROqzKRE4gtovfhwCTsxIRTVgBxvhLspuJdxF0igG'
        b'TTPgHpR3F9irRLn42rFSbkkBx4kZkhPcoEw5gXbA9pawOakKGzjbg/OVlH0OOCxQJ0Ojp3aBKHKq81g5+bNjNzw0m/TfS1CzOwdrY8B1xUxkdLyFZ0AD0Xou7LAkndfp'
        b'0VbNFjbuTZbBfrY97UUdcD9RFngNtHItOYrBY6cf0QxXFAm1nJW+Y132LFajdFEfiSu0ACnBVVjLQWKw/SNcN9q/wi4HksZUNOb0sz0SXK8H15Ks4DTiYAcRVBOcBbuR'
        b'pCeniEbnVLNG0zgCdpE2AXb5wE1IgDWge7RRqYSODaqgkRQZ14AP1qWM9kZhoz1nM2gQcEihoSnCliVxcAsGjG6GO6PFXEoVdGIv4E3g1OdkPllXESxQJ1iGVaY8qsMV'
        b'dycFTg8zfVgDL/XMSdTrC72w1ZfmAgMd9qGDrxqV5WSPl8XzLmjqsg+fzdGlHM3icfQZTxMURmO5AXxKU2KAPZNoPrfIYx9mxmpR3iu8kcIUaN7wUGEffrFSmTqkjhqa'
        b'ZcG8TH9v9uHfVCdT/LBw1K0WxFstNmcf1q9Wp4azBGg+VzDP26KMfXhNqkctXJmOP2SajSbV5OG7mkpU1uTJxC+KnGfMPlyxjEuFl7DZXBnsSRFb3bNCA8pdOh1/3X+l'
        b'VTol4KZFkhfOGXyqw1iH+NG5W5zMhv42UYUy1DPEoeOrU5dQnx9oxP/dCiIfGEhRobocTfBbpxMOTtTnUvLf8yC2T1oPNi3CwyNVpg92UGWVYCM7EzjNB5dFqBUtCVBB'
        b'yr4fbmbtZrHSJRsQfWkkU6yJSgfazMhHT0mnUn02ufijM4JSFcZ9zpp61B2laVj4Fb/6OrMPbxhkU+Ghhdhkb3qgmxRlNTGx9DX6Z16lEAlVv89yY9qtClmwjlnC1w/k'
        b'2V873tf1M/Gzd1Krtfraaq0ld5mxzlxVvrdrxL7aRyJvsCvo4c6+8k8HDu6ya+3inX2Wejv+5VdMgDj31gr9hee97Sxdz39judG93FClxmibTs/Q5CjXSNObfNed3PIp'
        b'knL1iFlqxbOU0mdNqnrkPrtmkvuWngabdwpnvj/zSITpJ1/qaOnufOD41HCHblJzhP8Wu0eCQ/ZHBrMfuWXUfL7wyBKOwZb5M6zzbgifqp+d0vnQ96nygillM+e/n125'
        b'0OQr+YDZB2/YfzsIV857OHjr6wPHDhcsyOO/XXDD4Jfr+kYBOxcxl5Ws/u5z57GRe+ahoX8Max5YdekjXmmklrZ89ZLkew3xv404fPZb30DPB9T8D1sTlXqeh04aLKNF'
        b'GS2yNaL3Pr2hcg8OrvtOdXq2FegVo9LXM28/n31mkejc5Jxt3l22i25E3mqg9U1k/kbJRqs78hP6zh6fmWIjPhv/Y/kHHU+MQz/54fXCN/Nt4vb/7KMaMKeC//ytPVt+'
        b'sdm3/Nz9o79l/fDGwi/L921/PGvzL+rXhy8fTEqaF+Nx1gE0fXPbv3j/k94LW9P2mRw3CkmysYm6+vyG7sNTM/Z9Ea12zDfMbGmD6PHiNKUAfnjs36/87Sfdnz7SCHj+'
        b'YsUs/7cnjQifx+xLmv/Rx+8L264IHzR+U/Awqz6g0Tdx7cvD0ot99Q+dr33+2fdv5yfZB7z9RuvySyNdH/4888vUPfPdOn1jok4kbze4evjD1z4v/gEuLri4fOf7q1qu'
        b'f5vn+c25j7697vs8f5Ngw6W2GR4XnNp/7P3UKbL6TO20S3csN0tEjPP3zx/sE75RdlbSPiVtudupdwqN5Hf0v/0m66zwTM2F48IYi8XtJ+b4/f3GVqewoZWZ6cfULug+'
        b'O/r21cPLb1h0ipMSfFYtDZ6/LfWCXrrD34Sn1iWY3DbNEadn6L85zT6z42xr+8WdJ5+udG+c0/7mT+8dPuhW4hpfzjW/61cRsyg+v7Xh2NkN+WbNveYlSy2vpix6bNa+'
        b'J/dK6dOck63pI53aNVPnLHvsZdkOrtTm2oWsP7W1++a5r6P3tLzM17vf6fj40ovZU95M6ti567tVXluDQoe/q571yYcWxqvoS1lXBFosx9JFcAKtWfAhMtyWEJ+kRCmt'
        b'4KB1Rh04wx7HduaDy7DWmZAz8aPR4LGNg9YyHexRsF4y3BkH+nIwG5coTizkoHnZQR4X1sAdBAoQnYjG7R70v160vuCpg/0mHNfoQHJOugxsBGtFcAfoiFWi+EURsIUD'
        b'rgjhRtZw5JAIm4Gf8U4Sx8Q4xfApjcVcNP3qhAfIazzna8fGSYXoEUY/scZJtbCFZa0Hx/VRys5IHH4V6AXXOWgptJB1RoEGyJPjTY/8kzloiBKyp+k74LVcEZpvswwU'
        b'SpSmMhdluI61h4J752rHEZsHlKwB3OHKQbOU6+nE5gEeNdfASAiKuxjlvZkTYuvL2rBZluqBLSRSDDhDUcreXCN4xY61YTPIiMNmO6MuSrRduOAwr8SqUmD3f2/E8D/d'
        b'WcRHtH9u+/A7EwiF/UNl4cwF+aXzZ5YUV3yBJlXkKBKzDWMCmhWJHEo/lFMT8YSrY6gl1zFpSH3Cw3fW4rZK9s49aECX3D0gb5XwHXlL7shbfPdEmZpsit6rsPc2EhRC'
        b'ce8RzEGByA9VNpAae08CKe7ZQOSHOhtIg70ngRT3bCDyQ5MNNIm9x4GeKu7ZQOSHFhtIm70nKSnu2UDkhw4baDJ7TwIp7tlA5McUNpAue08CKe7ZQOSHHhtIn70ngRT3'
        b'bCDyYyobyIC9J4EU92wg8sOQBHpqxN67SAd05WaWbZUT/zyz0MHejZ9aK2j9W/1a/BhdZ1rXWT7VpH7OrjnNunvK6njyKfr1ol2ihsI2O3zuUycanuJREyY3tcAO0rck'
        b'1ETI9Q3rc3bl7MmtiXw4Wa8uo6FoV65ssk1N6AfGznXKeIfYomFx88zGJW3K7Wq0hWuXa1dhn3X3bMYooC5EbmxaFzZiZt3scWRGA0duaEJorz3bItodukLaRbSN53uG'
        b'Xk95lLnwE5F3g7bc0rpBSW7j0KA6YmXfUtkmPbaky6plxXtW7g0hcmu7FvuGsM8sJHKRpGtye2W7d4vqA5GkWVVuYX1wdZe3TBqFj181WzTbko9ro0BHVR9Y2jXPOqbW'
        b'ltyidULtqQFl7YHKy1bQPrnZu0FVbmjZNKlx0iFtuY2oLawtpTkAfdbCukXavORYQJcbbeMhs/Bs4OO34eh7kV3hXR7DNj7kqHLE1Bbl3MK62fHg/PbKLu/TK/sqaedQ'
        b'2jysgceK7nFs2XtWbkhsB6eWJV02LasYh4A+G8YhfEC3IeJgNMqztfSBhRVmeWuuOrgKfcfQTCGOpXWrSotKm9IxLVQY1rYNKnI7AUovoSFcbi/u4rTMbYiSW9s0YDcI'
        b'ckdhs5LcXtha2lLapdGXKrMPaebJbezbJh/zGrEVyB2EzXy5o6htVrsqDidoC2kpaebdtxe2VXVX9rn3LJU5Bw+kDdkNT0u+5TCYO5yRLYvIlgudu6zaBc1hcpEUH4/3'
        b'8fvSB6R92kNTZKJ41sSo8thyuaNY7uTaFd4e3xyBb0LbY5sjvp9Eobf/LO27EdlPdSg78YhIMqQ0VDhUcUtd5pz6N/UB1y6lXo1ujb6Qi1q31GlnFlqQTYuyUeXaOGKS'
        b'9C67PtVuZ8YmlLYJlYtcunS7rNt8uxf1RfWsHBaFM7bhw7bhTx0oG4cXKpSd24sgysnnhRplHPhUhTJxebIMrdIsf3ymQrmkcQit3JseJgmmOuyBn8Y9Xun8kn/9rK+S'
        b'LAF+16GSTpRcPhqFi2OSuuWJHA5n8gsKXf6V07xkFL2QR736D1ODkc17Ql+kwrrc3UeNI+HiKiiMKHd1xXkCL0153HkC33wCOdF4l7uWVAgvhE/OE/7w9J8zo/3Ryalp'
        b'4p/zts3CMnNZ3rZ0vjv3/w2/Hu8P8iklknXM5UQe9fN8vFtT4KQv4VKEqwbu8yfr4UxHBa2XY3RMKg/0ReMpRIwS5bVc2XGpbelD/Vn8Sh8UvvzizZ7CA5id763X7F4f'
        b'qHN8e0AHGL4+tIYT33KeG+YujXdquKV3ym2f64aQjWu/tZXyqK+NlJYXPRNwyXQoaxE4E4emPRvRFI24xlH25xrACzzWEn5TXMJ4mKhEf7yLJrgFnBdwx+kjHrtHx3WN'
        b'wteKC+fmly4oKl5yzyIf+53Oxzzgr6wZxwUggz5mU8GD/sJk1Fj068r3eMj19OujdkXtjSE8laM+UgwM61THcdIp3eOU/lnbIayapHWw7eIpbhfP0MVH/RUv3fdlyahd'
        b'aP8rTQL7mmb3/g+jOega2OgY55SIAf98StmYq24jYHeyNsNzUSK4O5GLjSAo7mQONd+Q1PphVTTpXIgPwQs0Z1WtpgQcsklsCc/MiotPTBRLlJdPoVSTuJWgA25l9USo'
        b'Tuk5PSTbBYeqC1iWRCWmN3XSwnIexf21PoNDjVwl6/qf9ZQoVReZEt4v+FtcDDUP9QHUNxpKFBI4+BGazo4YdliWse4X6Cqh0/PU9KrvqnkUT4ljt/oo+docZZRE+Dt8'
        b'vF/wuvYC1i7Fprn4Y1RJX2prUBqixyRcYpoKpTnjAh9vErhmVbDhXEuvf4yKOPwrLUrL8dtKrNtJbT99/CmKa09pPzC8sZaY1Zi+ppoak5M+afGkhWloSizm7C2KJUfS'
        b'vxwPJ+jHdkefJRhvrNvN+2RLEdlHqMRV7p5RLtO+5XQrRikOUCocrluEjHxXK+sbGfqjuUFACS5cI49KNxvJUIuTpQgp4dU55FHx8fha1DGsDcilct9QJ9JZOnjVYs7o'
        b'R9R79Rt3vEeeCcw/rqVR1I+p6ZWbOnaxpEi7NQxhbQxhxJHy4RkrtOCo5cbCfb6lrY5DSpVqKIdLtxZVpeXOfd9F7+ruT3+wiU399Fiu18Wi/4+69wBo8tr7x58MwoZI'
        b'gLAJSwhhgyJDZYlsVMCFK0xRBA0gKg5cKKISREsQlQCO4ERRwW3P6bretpc0tgRrvXbvVltbW3t7+z/nPEkIjt621/f3vv/b60Oe5zzPec5zxvd85+d7eHdwkTr++57d'
        b'L4z/plA004rN2fjC1BuCVb4Pwh+s2fjrrl+vzv1b06evS+KCmt4cv6n2089uL5778T9/Chww3NuelXwANt6sZcfv7l9jKj9ss/7NyfVvl1WJdis6A+Lesv2gR33K7v3f'
        b'POxPLLwS9+KUMac+CGg4nPPW3LkrzetySmKi/s1dcuEDq49q16e900iFb1VNqU270ujlM8/8l6H0B1U3g0Kc/3b89WXVnw4F/b3O7MPatSdbX105hic6mR9x1imyaAFn'
        b'leDnVRvfZH9S8jDxh3k7Yv9pWMZf+ZG6wzL1782bxoRb7ujNPrLrhPfM3HeKLWYIunq2M069tiDE685X0oBL+69KxuQum/tZ9hsmA/WnfL+8MTuT7XSnuvKWg+tck9aX'
        b'mttuh/zWJnujvG3rr61ukkzWbX5hAz9KVPnNbcnrzDePd63su1G9qv77nd6Pun76pD626nbjZc8731Yv+vLOuyUHwop/qr+y926bquVh5cTywe7KHTnhjQPNe/d9fvPD'
        b'ZSHXqz/NcV17srduYkX9O6Et7yc4XwhnZF3MuH0Rrp7Qe+vHj+oWTtvPHtf48fH3v4LRzd+Pf72B+uTg55ff+KyQr/xm66+rEt9Vji6sEe1o+O1buXTeLxZ7pzcEdL7R'
        b'8Tf/XtHefaqs1QfA4hWG6ddGVU9u6YkJTP3pu89DZl93/ts3vzE7msp4D5uFXNoLfsPSifByXqoQBxBxKE4x0xfK5xGqmxUYiCU/AvSGyHw3mk1SZrnImYiFacRq3QB3'
        b'pPuhzWs23IjkzOPgAOyiBeNDoHk1kUKT4Q7YYDglBT3cwVybJyEh9FwoF1ZULl9ubgF2WlrCM2bLDMCuSMoWHmCB/eCoBS3SN8Pj1jrJ2wUcKUCSN7gK5aTdC+DWCbAh'
        b'HRzHAJYUE2xiTDaGF+iXnwVH4V7YBfaLUjSCMGca0xpeZNIC8tVQeE0nIQN5MB9JyGt59KON4CDsJrjd+LWgsZQyNmWC5rmB5KVG8CrcbZWCHhb6Y094zgKmh+cSUpRb'
        b'sYwFt2ggSmiAEj+wj6708lQbUVkmqnRrchravEzBaSbcD/eCFro951gBqcnppJslgZTRXGYh2AIO0BECu/nLoyalagCjybaXS6cztYe1kklEd12fmSZEAxfFtAaHYLOQ'
        b'/7/g9UswvZ7h26uRoIc3Vwmbo5GgzzLp/a1sKoNtbo9kUxt7JElZ8pSWrjgf0aqmVXJPFd9bysZnNU018nAVXyRlD/EFcuvmdVL2+6PsZZ5yg5ujRivc1dZ2LclNybK8'
        b'9pLWkrbFiuCe7MExicoxidLkAevJUoaaZy2dJhVLx8gmq3geQ9aucubuTLRN4zRNzSuk7Nv2TrKpcra8qsNMZe8v5QzZusndjnh3eCt8ehJV7lEq22gkBtryZSxZbKuB'
        b'LF9aik55tjKv5mh5rDxf4dZRqIjvYXRPkmf0FKo8o9QObtJ4tYOz3ETp4Cs1VNvZtxu2GsoNVXZBUgM1z04W3Bwx5OStYJwy7DbsYfWUKoPiridiZGmnNOkktYOrNP4O'
        b'3xEJbfLZStfAHk8llrJ+uuvk1hGvMOxKUzoFSScNOXjJxUeKOooUSKQZp3KIQM/w+GpHJPbKsmXh0gSMgF3ZFqFgdZsqHcOkCZhXSWpKkmW35t60FqoFnvLKDlNprLRQ'
        b'WiRN1jEyakfXpoS7qJYcWTSdhErlGDjoOKYnRJpwhy+gxU+BGxG/WIqSbst+W5UgBl1zFMhD2iLVnl5HEjsSFWE9NirP8H43pWcUgcSmRbHR3qTB2T2hqtHhWArzlGcp'
        b'RnXkKELl0T1jVB7j1Egg04pg942RrILmhddoeaE8DdXiKTyS3pHeM7rfU+U58ennaR1pPXYqz0h0xh3VYthkuNv44SwGZeX942wGxbXWTZ6Rc+qx+WZprbQUoGuyHCkG'
        b'd1bz+FtTHxbjWt4eNfpRhTmavS8yk4xTzFk3zE1SHA1pLs/sFnupuHLhLXaBuFJ8y7i4sHJ+ZUll6Z+LuCUOl/pJp2jOEC8achhnopGYfkES0xLMGXr8iCQmjz/DHu5F'
        b'7E8+U4/910kfRRQtfRDAVwMkKVG6HBLMER5Xzx2g2IB6EjsasZ14u4AX4HZwLtUcyjJxKAUxtCEpwwr0seCGfLCj5JVJLmwSZWD30abe/ANI0JC/xAXWwO71hX+7s+8g'
        b'uN5qQXk4sBzPxNADxXq8z7H4MwxtjwdumFyZaMkVZgpxEsilWSQJZIGiRMkbN2A2To/P50gM8DgZ4sPT2H0C1q7H7+O6yWGllt/Hrq3lWWhUnf/MgOId4f/agOqaoA/Z'
        b'3mb1DqsCh/fd6LmhGamD9mSsFt54ieKYmH1uts+eCuxnee+9/YfGqmLEWJlrx0qD0X5/ORorc760Upb9tpn7kwPF+aMDhSsmh9X6A1WFB8ru+QzUQorO3UIGikF7PYax'
        b'/7fWnkkGcfvwdQA9+pJjSaoJuAKuEdnqHzauzNVGsUbU0vfXrZjlu5JcPFRBIvWpu1WFaS8ZCmhb6K1ZDHx1hTxj8fwD88IpUrUPvAj3Z2FrAxUBWuEmChwAO4CcPNBu'
        b'YIg9MLlTEhaXrkwUUcQzZNpMIMuCjbDWH74gSkpmUZxZTAY8C86XvDd1i0GFHN0Sa8bvzW9Fk8qB1i1UBiw2arBKMg89vHdBYpYiw27/q9w3TJrNC42KQgo3HC0oMvj7'
        b'F6EfBdeFLIzJ8ZwdLD9avL470OAtg7SO7bFfzSwtNC98qzB/gdEHL7m/WveNuwHH85faw4+YX7P3/n3Hu6+amI37qtBSbDDUEBSxyX+rYdZcruthuyB26w/28fasPKn9'
        b'G0Ovx4ivK8D1ISZ1MNbmiw8OCo0IV8c1XSny98FuAhychWCbt3+ZNu+yrBgeTPVep2W7aZYbdmbQRrBzsC8o1X0eJoCI887EEMLbEesLzmvC9vbPhCdS14I9NB6ext4E'
        b'9oGNdCZ70D4FHCMsMaxn4ET2swrdYbsd4UJngu1cDaS5gUkEbVIqBldIqxIR1426nJh/2GgEjobj2N9O0E4HpzWsSdYzVUmEGCfPLl1o+Ec2O7wYNeYWekGbYeK7tKBo'
        b'Pt5JJXba9XyQ0hhbMO21a4lsimyO3powxHWWFbQvbl2s8Fa5hKi4oVtjP+LaSpfJvFRcgXyUkuuxNVbNs9macMeK9xHfWSbGW38TG3GDXOsW0yZTWbY8tnXmoJOf0slP'
        b'MVXlFHiTG/TQkEKsots9I8p8VGNafdr2DLUZtzG1PlVmJA9rtbxp5oNqbAlvCm+J3hUtZw/w/OSVb/H8tiYQJkGPxBhKPsMfxP5dzA3SAQv083fgTyaHddqNHlOaGkJp'
        b'7lF/ktxgSjtipRtr/n4fzUDkxnwPNYeSMLIoCTOLIWFlMSVse2oWIhzoaIb+GYYxs1gRaM8gKlONC3aOaZhRFhuTJS15kRjM4bhTWQYOVBYnyzCCKTEk50bo3JicG5Fz'
        b'E3RuSs6NybkZOjcn5ybk3AKdW5JzU3LOReejyLkZObdC5zxybk7OrdG5DTm3IOe26JxPzi3JuR06tyfnXHLugM4dyfko9DVYteqEv0JiRUoFQdQcq2GSmcAYy5BYofuw'
        b'0tgYEWJnci8vy0ViXexqvEnodsswXVyGAypKGtFIrbIxyZo0JVawhL4mILm7AkyEDLLRjCD5xlpqi0NosJu7Dl1f18NknzbWEX/O80XWX5VlklxWUlkiLi1ZVVhBEtyN'
        b'aHtJWUUljgcJMDGJXCqWiJcI8GKMFOBkZfiXoLJcIKYfmZKQKCgqKS18LLOW7hN1G4pLBgHmziwELYSSTMH5s/yjYO10DUIIOAG3+gUwqMkMw/A89yoMUzAJnlthunRZ'
        b'FirQ3pVthNVxcGs6QYNGBDIf7uYLjMxg4xIaO38zNvPrEM7DRoNj4DI8QXShcazRIgwa3ZiazgD1oBNRz1ZmjYiGZ+flLxWlpAd4gxP+vikkRIHnzYJtsAXSXn+wa5JN'
        b'akgKk8Jwm21LKESJ4QvE1WgWXE8SLKQxKGZeWi4j2MeMvG5CwrzUgJR0P1APtyWnMyjTciZsXQxPEpcxIejOIDQcox82pIGTq9EdFrCdFWcHrpAvKbFdlApOJKUH+CfP'
        b'BVdw6ngP1kyTUhpp/wTYH6PRCqQzcriI0Pcxa8AVA7r0dCHaBpLTfVExcwpsJVpAsD4hj5Syl8M2grAPN4DTBGUfQ+zDazXkrfMs0Ofp4dHaw1Ogbbod8Z0KiorBqQxw'
        b'IgO4YzYj0Gg2eWQh7IOt+skK6saCzvGhtCN+Sxao1yQcgAeX0DkHuCybrBiiCZ6+jKQMEQQVfZOeHLmYor0od8MTE8EOeIJ4TFJu4DDcR7iCKBvN3ZxFDj6R47FSGvv5'
        b'OaXBTm1iATQNSG4BTWIB2AgOk0ffW8sibEnQ6A6XPeUmGt34JbBjmV6mA04EuAgPgYNkPogzsC/x1sAAnOggbKI21QG4BLpo7KHT4yzoVAeMsDQ60wGoBRvp9CWNeTyS'
        b'iqCT80S6AJKJADTNJz6MLHDQFc8RItGAzvmBTDQH5Ky58DS4WNJifIBRcQSR6SnW9w5lp2bAIO45nveSvZvecl0SGye18ZPOHDCI+8Bkz79mnWYYsxvG8u86Oe0cwxfv'
        b'u7Uz61K6wayC0aHfvvFq4N/yv9u8YprgwP033WPerjoX/JlXHDdwVPyXpT+/XmN9gW/+nt0/bFd8eKLX+fhC19SH69JHrfris2gY+Vvdyr6ee15W6Rl542LfGLV18xn/'
        b'f8w4HJVpejfEneVg/PPMTw0611RPs52lLjMde74n2fR8vrjmDfsrP518JffyA2reB+8XGt5b5TLvzpmsReLGtOwJP+TKzl2dueD7jLXxo/k/xT5qnzJmQ0lw1C6TDV+n'
        b'1vBrq4+7b0x5d+D1KdUv+7VEjN1dverz1gUvvfKozYflwh9TLGn8+5QZ/PcXLTjKaVvFdZx9mmfjGPFeVVFpiNs/Pr8Q9caizisf/yDO3bjfNypr+bz9iV8dqLvmfWVZ'
        b'/pSPb/57XkDtpfwPun/0vVJ8eMP8b0O7wke99NmvWZ+np37tsIp3LiK4DR2WPTh5adfEz9IdVjWv+yz9xy/WfBlxZcmV3D5OVM7yw1+dv/NJ2L/GX1nFm1EeuXxZ1HnF'
        b'b/n2D9q/PFK9e/W/mB9/U97YME/o8ECTBaMTHtJyS4hT6hoPTqK1tpuG762fBXanpvkGJHGcyR2mpUx40NGAPJpuhOY+RjslVjSPCYhANTDXjAEXaNzRPbBPbIqTyqRX'
        b'+YMuuJ42c9mALWzE54GTD0gs0enFsG7YGgZlsE4DnKKxh00CXYRrmzsb7sOQ+IRSIs4e1MLDJlEeNCJIO5CPBg2BhFiitV2fislXBRPuhRsXEUhcd7ANKrSeRJvBYUas'
        b'dz5BYzAtTkUPIkKKXnqimiaktvAAO3IKqCNPZoFt/qAhE1NSViljNuicPsaG9IwnbA3HiBiYjrJgO8PcCUgRa0t7UsEjNkCOSjE9Tc6FhzCxXMgatw5sICZA1CngKgH4'
        b'35EJXgAHaaKKbrIKZ4EONB6XaKSSHiHchWpBZBX2zMSUFd9SwwJ9YCtoodFft4PjiLo20Dn6wB5OBv70qejThZbkBj9UjjouE5FXJAldxCSWMvViQrmdBiwlGlwJ1yLe'
        b'ErxbeADs8/eDJwjaA2iEnVBG6idJWKIREUI00dKYVQk3wgtkaEzgeQa5gxAmjhETbIm190ogIkA+FYIHZmugZ26AJgWLFTzEguv9KfL2qpDFqBzRJUsHRJkoUzSBEHlu'
        b'g4doz7HNgXmoZpJfJQduR8TfIp6VCBVLCQKGPdw5R5Th/9Q8J6APXjOgYqoMR4HjTnRPreejWY36nN6K4VF4GjXGopgVucSNzCL0ZddSyJjBC5k0iUN9ZTWOBS7XiEkV'
        b'doGwGbU2KRnsmYX/kgVhZcECh6exhRbPydUL29RGotoOJ3C/xdWwcBhkAnFEGpCJ6SxaeSDJphU98oRBnlDJE6odXaUJGu2oc3t4azgGmFCEqRyD8GX6yoTWCQpPGnTi'
        b'tovPgHCCymXigN3EIUcfhbXKMUCacMfR9baL74AoUeUyecBustrZTT66dY6UvdtkyNVPkd3j0z1P5RqNzs2wC5j3EZ8OH0WUyj0cXbFUOwmww5E8py0TnRo/djok8FcU'
        b'nFrYvbBnpSogViWIQxfNh9wCFJWnVnSv6DdRBcar3BLQRYunXlS7erSvaF2hMFK5BuPX33X1wH/U9s7tdq12ch+VvUjKucOzV/MF8kQV3/d97wC1s4c8sXWeYnrPpO65'
        b'A05Raid3HOmP/0Qonfy/N2T7OMjY+8zuWVDCQMVKpU9Ev7vSZ/ygT7zSJ/56/GujVD6pMvMhd2HP8v4SZXiS0j1ZZqgWBfcIlaJomeFNOx+1z5iePPSczHCfudovot9N'
        b'6UcKhGrfoB57pW9Uf6zSdwIqtVQHhcvY7WatZm/b+f/npumdRiqdAvDfcUgI/N7cUNNiLmVj35LWlDZoHaK0DukZ2x+oDE25aZ2q9kODjQtuWgvvunmRjnN0bR/XOk6e'
        b'onIMlBrd4TniHkpS8f3eFwapnb3kRUpnf8WKfoPudQNOE9VOnvLp6E347yylUyDqI1/8RuxQJwxGn+QT1R+n9Jk46DNJ6TPpev5rwSqfdLqPVlw3VoanKN1TcR+F9iQr'
        b'RRP+Ux+F9EQofcf3i5W+MaSPQiJQH1m0WrxtF/hHGqd/PlvpFIT/zkTdhbpJ02jSTRlNGYPWYUrrsJ6Z/eXKMRk3rTMxQIKwW4i6ChXetPZW467aY6EnHpvRCAIGz9DA'
        b'/SEl+eNuRXhNS8ahGnfry86F2Vh2/uFPys4k7/Zeji911HQM6y9lhyZJddyenYt+mPpEl4qX5BWIJ9xHzdZLAO+OBS6tUKaL/B+RB1qioP5ibvSFdO5qw/kVJcVlhQXP'
        b'SlodiXrzAW7WKOaIZpE2lRcJ8NPiyirJc8j9rcmmzZ6fF5L3e815iJsznKHeJ7FUXCwoKRKUVApKcF7puJA4Xa/9140ig/gB9ewU8rhFj0a2yIlk9ZYUFpRUlksEJQXP'
        b'Jy26xNPg91vxK27FcGZ2F00rxDgZ9nNKz64ZIuP5S8oLSopKfn/a4Jx9ktEMbXu8cXtKxRWVAvrh/OfZsGJtwwpXFOZXVf5+w1gjG+apaxj98HPvLkMaWON328QxHbHG'
        b'fLWTulKPBKDZTVf0fKY1aVlBYR6apL/XMuORLXMlq588JRDnE4CU59Yc4/naVfN7DTIbOXxuI1bbc2uSbqprldG/1yTLkU3y0teU4RHUqslGNkv/jSPz9mJvVWYOS+f9'
        b'SWXrqfzKGC6o2XoqQMYIZR8VyyAqwCeuPts79UnvT84zvFNJ6/5nswovFDJXBZmQ+V+9sBD1ngR1IZr6eqtAgpapBG2GlQI04mXllY9pH5+aLPpwpQmLJIv2aHtRmyq6'
        b'xpcki86lhEKm37G9QgYRXGLgjtUaIRacK/PVE2KXwsanZCr+DGPWuWr3cl3bhp1Ii4oLK0dkjl40k0E5EXi6AWvfP5m6GL9NMhfNOZ6pXuri/Jl/KXXxHzEZo9H8HzIZ'
        b'/wEvZDRw53KnsEjAznFB47Bxv+DGaxTHbXuEWZD0zeutnJJ2KsGAtTS0F40hkbPrweFqehChLMlffxBBMzj0+1ZlyTf/cUQrNCNqRWlERTSi3iLFmK7F0oQ9mSMMzWRI'
        b'uYw/aGjGr5aI0VUHUz1D8zI8vPZ/1tAsZNJJOk+AhpmpRFvDBlJ4xpIBjsAmsItO7vlCEKhPRWI/KoRbQVcoA/SOXVZypNfBoCIED0noj735Zsf23hC8yr1RAOxe93lZ'
        b'+nKTYcGWkLYgg9D1K7eP2v7i66vSfM32lVA7mZyqwQ7tVH4a247Hdfhbv0CHW6Oe6GbSsY50x6rZRj8smMlgjxL9aMEYFXJX4Knkhw5wQ0csmqf165NvkuShXrXS9iqq'
        b'+0cx7lXj55NunSwaNiGMdJ5kSme8f/7k0d8kHvulV9AMAiKII803FYKKypLSUsFycWlJwWO08UmvDE5GdiJRkh8Lq6GM0Mdxo2LF6qTYspKfr3/AqFiDSvKHcmi7utVL'
        b'tcZh8koTD1Z8pMcUc17ZmPoNZoKsmfcUVCtgZ8O6V0e79QidEmQbJu3w97jt5MLhGHC+Cngz30j8Zf/0PKNCI3FIYVxobi3Dx+WlHd2vWne0BG/l96322RjAZ8VzXQ9v'
        b'W1B0TBg0eCRUcphBud2xerjgF6ER0XyFu0OZKCmZ6IniMWoMRVmA86zJZrCDNo53gbNzNPadcaAunUGbd2AtfIGoEEv8wjQWE3gY9OBiYjPZBRTk8eI55iKitkSUggu6'
        b'dfafHfAyrTrrXjJNa48Bl3w19piV8BBtA98K6+D51GS/dFdtUm94BfaRMgE8AmtFsD4zebU/OM6mOKVM93VgPfEahdvgnqrUZHB8mq0fh2I7McAZWD9daPBswRe7auiZ'
        b'y41KKuaTYR4WJrVXyDJaRU/1e3GzGJSdU8ualjVqR+JcWdNSIy84svjIYrUjdnRrWduyVuF5yv+UPzq/a23Xkt6UPmgdJM8+ktuRK2UM8bDx3G6Q56vk+WJfRk4rp81I'
        b'Gou9LlOaUprT5MFKa0+6WJGt4gXTtY6whj9la3uqMVzPG0CyBGsHytDB1VQ/TohsdtgY/qd2PEISzSQxuM4Pce3p+BcB98vCv6bgQwo+TMaHzzHJns4hzqs62iQZjy5o'
        b'UuXa/BEQP+wDIPkcDxULibUSrGeV/AMDCBppRahbRlqZ5RaHZu9vcWj++paRlq29ZaRzifhC1y8Ek8/8v9eQYm/Gp6DrOXI0B2zerrDVousxzbnfcTC6XmhrpcxXae71'
        b'kDmLYT76e4ocWZTF6Hvkwv3lTC0s3TgMSxdJUOlsXYa4QvqKbeTWxGEwO4xTx4thEDQ7zaUQfCmMXNHg1IVhnLqxBKdOA283HsPbTSTodporkfhKNLmieRnG17ONY5C3'
        b'aS6NwZfCyRXNYxiozy5CvyKMPWo3fmvSj0Ym5mH3bSl7N6VdYEdEVxT6szX5IZtr7vQ9hQ402h1RidfZ4gD19BhwQWueNgE7cQrMi0EjiLCV5u/3ArRIJzg81QuDQ7ww'
        b'7NE/KosVgf0QeDnWiBH7k54X2KsAiREmxHuB9rtwCKLmGD/m6WA8/MYs0wgG2cNM0fvY2EtD730mj91ngIQA8xF3mI5ou32WRQQzy5HUxiP1cfHdixi6+8109+uewZ4n'
        b'mn/2WaMiOC6UC5XllMMgYIC0f4R5jkUON2dUjlWOdY59mDn2DRlRq/nIVmj+GaF/xqgPeRGsLGfi02JAPC5Mc8xQfZa4hTk2ObY5/Bw7VCsXe5iMqNXiiVo1NeLWZtmQ'
        b'Wg009VmSuvioHmPsmTKiHku9XuTjXkQ9w8T+Knr9yM2yl4wqtkT7vcstCw1tR39wCHpJCKKGq74yiRWMvI45APS3QiBGm78+S4B9PMSVArEEqxGXVZUgqmJShEQnck8B'
        b'Os2vxCJ9SaWgUiIuqxDnYx1IRYCJSXIlYiXKJZoqdbWJK3QSLeJBygRiQXHJ8sIyTVXlkpXo0YAAQbVYUlZSVhwZaWKCDTBYKH6swTpWJW5SdmyAIKG8zLtSUFVRKMCt'
        b'WyopL6giTXEzETJpTfErzMdiPXWui6WU1n9yHi0941hP7EZjoIvwNHiOEZ5FiA179IQbjZYFW6L9vj/kSaPrNizwojHS72vSc3jgyDgUBAiSiaKzoBy9EUm+gsIVJRWV'
        b'+Eo17sY8jcYP3ah9oUYhQr/zCTVJdQluBCopqkKPiwsK0Fhr3llWgP4JxEuXlpeUoQr1FZqP8ZQc6nGe0jyDZHBH3FVPqn62oSSts0Mg3AV3pJG8QNOS0jI02P5geykG'
        b'Z9xiisjoSXCxCmNdwh7YTeAEn1IJehSbMgM41HK4CbFqW4zXwDrQSks9vUgG7ILNSLRJYlMGnsu9GVAGe4QEHcveCcjArjEECIhaAZqTic+H42SwLcsfHoZn4KEQxPFF'
        b'sQIoy2imZzXYQada6gEdsJWkmdXGvcL1bsSbaco0/+lMKlxoAJpASw1xlwkEPXAHHzUATdkKqqIUbiFctuEM2kM2iPPTjO7Vy6gqP9yDoB+0pw5/F9yaNhUnffCDO9Pt'
        b'Mug0TlPLDWGtD7hKi23dsNOqYhma/bAR5xGRg22gfWxJS/wqZgWGb+to/3HHrvGZMIhbN//d+nfPdtrIj+YdXb+Z8YpfUqEicmNB1BfXs7vTW6xO33dV/3zNiR1eEli/'
        b'1PPV6qufTvjVet2LItOr3/z7321u945ueKc+e/eRE4KAR+Hei+eUjvm0FFTNM/wivW8KHH2jO/uFT5n+t2fNOBtvbvqvex8G5LJc3xNsbIhLq48rAAcqbrz8xpW1cjPR'
        b'um8emt4xmxfYMiF3Uf9HF82O1ymVTmcHf1gYtiPklzvJP/K+iTJfdsS5esbX1SddVfNeUz3aW3NmV6Pr9Uc/2Xidu3zu268ts16PecsnaV5T2EnPxf3rav5eVcb9F2/d'
        b'qLNRcz68+oX3rI/eWpDY6hgd+OmiujmVMy+32Cb/21z8VeAut38KecTxYBrYOE3jpQXOWOQxguHW2XTacNgn1LlVyAv1vCpsAc3dwwNx6dhlKhg0peg8psZn0XJBE+r5'
        b'jVp3D3vYgX1j4U7QQ+cgOQA7x2F3D7jDLWnY3wNsABvo8t2JoFHPeTYcbCJZpveAPiK05INt+anYMw5eWegXIORQxtZMNAd3g3o6I/A10JYJG9Lh9gwyc2phsy/izcBZ'
        b'1lTQAA7TAX4H1hmKAuE2zI1wgtYBBdMP7sohtSfCYzbY3wTIUZ105DbxOLFfSp5cCrqskUyUhtUGu+BpNwbYD49SdPaQTeAKTxfslguO43i3GiQM4SCMUvSBBzUuELAe'
        b'1rvy0ar1R0wcOM9OApdhC6midAE4qzP6c4Asl8c0h2fAFdpT47hfDk7akYrTYtAtGxUIT4EWFmgUmZNbYCdawjuxNwNNPZCUdQhJbRZZrHQ7sImMTQIXXtI5swkQYcH5'
        b'1WEt2E++PmC6gyaJyYKxejlM3FDXC3ATWuGVRaiBqHZQj91BZA5J6XAnYiEpFryWPllo9IcZbLzstQ4Ies4H/JGb4UgfhEQGLbhlzEaCmysW1247eA54JaocJg9YT1bz'
        b'XVrWtawjlyaqHGIGrGPUfPuW6qbqlnVN6+SVKr6flK11SYhujVawFcUqx7FSI+1da5vWygsG+SIlH3G6ti2pTaly9k1rryF7Z9lCBeumvV8PU23n0G7UajTgFtIzoy/3'
        b'dK7SLeamXexDFuXgP2Dvd9fesZ3fym93aXVRGA3aByvtg0lrxvWHKbVNel+/NhdBe3FrcVtJe3lrucolcNAlUukSqXKJ7p+qdJkoY5F676LPwjFZ+Sq+kHhPTFS5xAzY'
        b'xaid3bCDhNpNSOztAm/s2aB2Fx7x6/AbdI9Qukf0e6rcJ0rZeywf2qN63rb3e/TQRPOjgkxYkWsij/WSSVCiJ+sVnkmim+ErniaJIZrALSM9WzTmMJ7tro2HcsEIf208'
        b'lBI0LaiJWhEVB2bVzEIiqtt9JKK6/RkR9S71F625GvuXwe9ZKp6YcFqz8wJsvRg2O4fquJMn2RE9VuQ52aGxnUXyzrOt5JIm7D+NW6gzbUqyOY+5tf+/tJ48ET3zf8p6'
        b'glonwUgG/9kgcvPYhwbEINLRk6Y1iBBziOq3v1FCU6aFK5pUNCncjkg8oYRwH2wm1FCPFFaXPcsmMvqx+VaRXzqfAGr8jmlkTu5/aRppRXOjWN80kpr7/0PTyB+YZGgI'
        b'76/7gElMI0WCXj3TyIZ/jjCOWFAJHNayI4FoNElive2gDqcVywJ7dJub3nCizfvyHzGP/JHBfdxKkpf7PK0k+zG51reSiHP/opUEO/jHgw1xGiOJJQMJD9fAkTBT2p9+'
        b'O9gH9mtsJKEMcBRuAr2IYdtUYv+TFYtYSUKtyjDAjeBVbuSnv28l8ad2CjjN3Sv/uJXkHu5tu2f19uPGkqRchvEo0Y+2/4WxBL9QcoCDE/PpGUuSc/+KsQSRBqwBHbGa'
        b'dCL7Ioq2mWjiXzhIXDfUE9iZIwT257CiVhWZTC6sRAK3ZgPTV5EMS+hLJIVFtLT8hOsVEqolhZVVkrKKSEGsIJLE+EQu0AzNAkF53iIkx/9Hg4tBRlUYhWUDsAP7e2tC'
        b'WXKmzPCfPoNExTweEgNqw4xBp3iRTRSdw/c8uJqIhMU0rxGytFZepKXFaaaGiCfeM76kxDSSWVGOe+zlzb35+xGNOI5ohBWwRcQ+rVVQ6RJvJBr7s6Ao7fQUTlaiUSrL'
        b'dxd49ToOk7QsMhMrC/Nrj6UUmomnxb2151W7G3Yv1ZUEDGx2mjmndtKhnAjnU6x49/CBjLL+/WlG78bZ56Ddg3Gg2nxz5EQhh5ad+hCbXyfyRTRG5xF/cnI6bbLZM81b'
        b'6++OEw1q5Y8y2EH8g4MW8LWCGZLKkETTr5XMGEtJIGUVkoa1kTcMf7AlGMrhFsLch4B62JGallEET2vzG5rOZsKT3Nl0bsGTVPUTqUWJh7w/OAVPwZ7wPxO+qIdzYYrD'
        b'FzXz5pbDY4tWr4ws28UasrgKkUU7T3mCwhP7TKr4YRiP4Ak+nbDXcdezlV7JKoeUAeuUIQc3uWebv9RQzXNoiWqKknvS/DDO96bihRA8qvEqhwkD1hOQvCDVd77UMLzE'
        b'OPH7JhkjatjRkiYPRzDZVaBDtZbhxbR3MSYPdvf/bICi/JlbbQFF80qaeGhKx809dx+EVVWELFQ+6ddUXqSNc/vvqUQsXeczqMRTt3fLnn1sgjjmxnOj8dOsX3qtfXEt'
        b'I84uvaNzpVmHWWyazBdxbKHUDnPW+a/qhUwigJuBC+WpGCpB65yfDK6AEwaUA9zPXgWvwGt0oEo/bMLAM8tgPYkU04SJ8ZOfvvvrtocovB89bWpreo1MbTd6at+bPYdB'
        b'OboOOvgqHXwVYSqHIDRbkZCHpvUA10sfIO2ZE5KGSBtm8vDrJSfQ9Nuit/X/mDrnz0biYxKMeGUSo2tYIV5eOF9ckTFCtaxTa5J0RGydapnep4yQiEGFcf5HlMt4Un6n'
        b'm5RY1V6gyYb51CkZq1P3F1aKseuimHaSWlK+HO1yOPOXtp4/On/pezS9Eol1zkTB74cVzUuqKiqxopleLxWVJWW0IyeWGInmmJYaR7i9YT0/qqxAf2ngd0vE1fTnoTb/'
        b'R6WySUYV5rXAdhPrx3dNO8S3PmPjXDTbkga7uwabXGFvnAjHcCZRcA9QQAXBa/v+wmtZBOaNTeW+zG5lVJptJJrad3NJvOHCH5IWlDJT06ls2tJHYOQP+RZEuYoyUVXT'
        b'KLgXbOaV3Ltzx6DiTVQW2vpBlTTdAgi4m12nLHTsculQL/oABFy66dFPOaTPaV343piyOSu434p+fXG0f9xrHqH/NPt+3FbLNClYyhOlzYiNOiGOmz/vdMnxhNiL755v'
        b'vG17fcUrmy9dHl33KXPiFxnbk5bsOfzNmG17dydsPrBy1YnuxN65m1+qP7rixuLDrFcvH5/Qu6u7dcuHZXv3lnR84jLjfHNi7fqo4pVR9fX7/vElZ+FlWdIWj8DUzMlf'
        b'rEre/t7uyvcO2CyHgbMvdlrVv5Hq9M+aF+Tuv9Ufvpr/wat8+yJBC1gjNNI4OKQaEiUn7EnWbOKwEfSSbRrUV4PO4bg1ClyMJNs4uAiuEQ2rEWgbn2Skt5Xrwtb2waO0'
        b'krIFNFViXSPcz0NMNlY1AikNdAWu8VNEvtqAqpBI4ygmaHcGrWQf9wZycNgcNOppG/V1jXtAHc1oHM8DPVo1K1w/DyNqM8Bp0Ad2kHeIZ4GdWEcKt7oTNSlWkgIF2C00'
        b'+QvmdIw+OhxvRLMFhhpUg1u2T6Gb6DqhmSqaZt5fMeevsQM2GA2LfdPGS2GlUf21RUgTHrIo29H3ODhXbm5rrsK+J1blPLbJhIY80lMW8h1aVjStkLPlU+XT5EYqvpDc'
        b'0VQjZd/hOWC9YLG8Ul8vKLfeZ6FR2jlKTaWVUtOHNuhNb9t4PXrIRZfRvaSE1r+9aDYqnssCIVbxbizINYl3MYRuJvFBGv2bsR71P/kfA0IqjCk9hCR6V7iAn7qIDrv0'
        b'tXBivCu4ffdntXAYUBaJpEQTSPYHY12UA+1+sRR7hbBLxWXF+YZ6JIunJVlSvGGY0xvGPNY89jyDeRy0cWDTNTb2mhHztWUOF20l2ITNQ1uJNRKAcLY7mzCeZksxzDbV'
        b'21KM0JZiqLelGI3YPAxjjciW8sRV/S1FXIZ2N5PYggIcJFFWWD3Sawzb+2jbIW3KzC+XSAorlpaXFZSUFevF+aO9IFJcWSmJXKCTQRcQ+o53q3LBggXZkqrCBQv8NOEY'
        b'ywslxMuFWKBNxM+0NgvyxWV4V5GUY08Yrd90pViCVoggT1y2eHjrGmHRfIxje6o9M+CPbHp4k8MG1YqlhfmkxX50L5EtbTj4pqxqSV6h5JnWVt1EoV8zHB1TvbAkf+GI'
        b'vZO0sEy8pJC8oZx29dd+x8Ly0gJEHvR23scCAZaIJYsLC2hLbYWAjuEJEGRid+nqkgr6DYgdWFheIIgsqirLR8OF7tGKHwvIg9rW5ItLS1Gf5xUWlWs2bh2KBT0oVTjm'
        b'AJvkxeQ5/THUfbnORSpS8HhAzrC7trZerdu25tm8kLwnn9IP43nsfrzyEFeSlSkYGxrhH0zOqxA9RZO2oFDbldpn0VSiRymAND6hsEhcVVpZoZ1iumefOgLeFQI6B+zK'
        b'x1kXzcjjpi1FDD769RRGagRHoyMPOo7GJ4OwJnwktu6uCJEgbqKcGg0VoK8CtBAzb4A7PGC6fBmDYsCtFDjlCPeBF+AeIYM8tgKemiDKgDuxRXMnIwgeiocNEVXhqMSn'
        b'CuxCj02l2SGfAH8fuDXQNzmdtrcvhWcqp9MGa9AOThqD1lBwEIdXV6WgZw1WgD7T5fD81CSXmbRicLoP3Al3+vkkpYPT03CVM0gNuC6MMgR2TTIBBzLAzrUmOBMWNQ5e'
        b'NYcNYMd0guEBN6Jd+OgI8z2NTDEtgKmz3ufPMwIdcDuoJ3xXTbUZhgL2WZBdUPpJ0RSqyhtdLAdtiZi/0FnewVE27ezpJ/RPMaDGizhw7wQxjc2AdvkFIriLA48DGcUY'
        b'haGlLgMZqdzCjYaWEqyq8js8y50GqNpiaUCQJQRZeWb1+aX0xbV82lAfs7g87aKdkCJgH5Ww1wN2McAxJg5vMgV1cDPBzCRPnOMbU2iDCloaUGnm4MymqqJxY47CTatg'
        b'gxcJtc9KIilIktE3bBdhblX3PUlYQZKSFpDs78uhYIPQbJkTbKvCxNwftmP/h8fURNuFKXBjWXoa6M7WsLtCDgXWwwvGoAvsZyUKjWjd5dUCnMuI2EDD4AmC6QHaPMEJ'
        b'MoPKwX4MhUpjejBA1+TAZLiX9p6oQyxZjwbVAzRICLBHZ6kB8ZMog13gkAbVg4b0ADtALZdlU7iO9L8oFmzS4GrAK0CKsTXARfYi2kduuy9sEM3ETQ7URrATZI0U0ESm'
        b'vDXsctcAa2BYjdBwIANnrOlEqWcEySJ4mfdkeLoGV8MTXBTSOlt4NAP00jgw8AjYibFgwDF4EJyk85M1wc1Y+aMBgyGewqBzcQ3YN44u3wQv2xF34DBwUB8OJsuMQJTM'
        b'gC32WjAYJFXvhH3T00iHLoad4KROIxUOrwTD7XQSTgv0GZsJHgzBgikEBzAcjGQZDXB4DZwEGE33HJTpMGG0gDBx8DLBUpkIT8DNqajhdRo3ZI0P8ux0us3HQQ/OeqoB'
        b'hSHuzVngUg3oDSEdHwL3gyup4BTo1bmZaNBGFohJlyWBF0CjFjaGKAMm1oD1YPda8snxsH9cFpTm4DftpzIyy0CTLcFwsXSj105QQpGfJGEtDe62CB5AfdwAmzPZFNMM'
        b'iWzLkIB2nCs0oRMnyqtgY4WFpAqeNoOnLcE22FeZmYq6eBELjWggGevVsAnsrMj0H3FXBTxbhdUYh1lwP9w0hZ4UTfHgon5l1ZXLjCXmFhx4IZLyYbHhBqtwArnjkxkH'
        b'e6vg2YplZsvADktJVcIaFsVzYoWjCbKBeOGAs5x1FcuqTEg1lvCcMTyNXojv1r56Ygg4PY9jAPYupdMbb8c+DLpH6LvgOTMDilfIigVH15LP5YHjlO4ebesksykXcJI9'
        b'mm1Dco+ZcCbqVVMpgWctbVDrJrEi4Rl4jAzwukBDdIsFT1MPIsEcisthwpPehXSK3StIxK01hecrUTuEsMHM2FxiQJmvZYJeL7CVdIEn7I7KqghLh01ZWDmcBXYgCRfs'
        b'ZcDzloAGM4LHHGF91pQphHJT+UyxSbzGtRWeD9PUnQKb9epezSQjnpMjrEDVSAzQMjtKMeFhhi/cBGTEhcvWGB6HDYjopQamp2Xm4K2H7COBnkA2NckPU8DtyWlwG5Yd'
        b'N+QYV7iAc6QxhS4Q0ZEdLNhaQjEiKbjbQkTnwbxQjhZ3bxKiA6lgF9jpjxZMBpsaBfax0BzeDs/TqIN+jlQYEj5jzFfOaWJrUt21lIqobHSRO2tN3t+SplN0dj7qp4ma'
        b'Hz4xQjbtIQaaKPQpG+ej3yuplb7JJGPlsjVG4JiRJ9oWVlGr1k6ldQG9oA1eFKU50c5kUDaXXF6YBXE2uZN48ZRQJbDZmsg6JfnpoxkV0xAnPnHajf0zcjPfDbJe/taD'
        b'vfMEBik+JW0Us+R6wPGFQTHNy8Vvnc3odT7dfevgzr87rnzPVa268zD0If+wc3F9291mn+N7Fg19GvVpFP8X9fgv/+2+OqH+0VD9K0OZcf2TqmxGced3nnzH2J57p6vQ'
        b'xvCWTVXV8e7pRVsS1EE5ZzNXPMxuHnevKEE2dv6FR32dvW81BQze2pSWe9qg6KeCUyGfXnlngtlPkV8r5hzfXrPvpku9wjZ7+0djs27viRBVX/tBcGNM49LweYVv55t2'
        b'pnx50yryzY/LB2Y9SDjh99KHj8YdbcxgvjH42Zlt9pM9vv74ta9KZ8lN29fsH5NQX/hDym3Wqek5xqEPrUJvzfD/5dBM38q+lxVTDetPRvwjUlBn1Dlp7ktXXb489CD8'
        b'TP6moxaf2eYld707NLviS79/vXKudqXj91/GFY/+0m7at++8bzG/zi/y/o371YXhfp7L4bbrIEN9YXFr0jfXa5O4EWtqE4pfOv/xzynt+yZ9czDTYn5njVF1GKfw3pvp'
        b'+96Jlf0cskZ2It61+O+7szJ+kla7/ds7aXVm0083Mm1XvvP9oSmZoo3Gn3Ptkw5WFwksTT3abRJd+IkHrBMP2CRenTI4s/paXfXMfx1Yn+MXaLuXZbpjMC6/d2Dccb/2'
        b'obeu2mdvmxGgsP1HfbTozTUhKzvPdTz8OSfYZXftqW8LSzyq93z1/rkPavwK5vy4uPSQ0xsWKXmjb+W/tvPOtl3dO2f4n5mdOevE5OkN7d8vemW8oHzaZ6kLq3jOh+3f'
        b'+/qnnfHTQ8d9uet7l6i5n1eOf6fo2C875C/OvRD/SPyPVfUr8l7dJ54w2O9YeObFR+LR/MsrG8eaXjnyzsbRfV6L+KXqB+duOOVeOXdh/BqPigHrt1efFD6sh19HBZ6e'
        b'G506sMaR83Ng4r128zIb+76Xywe+y135rXzKv6fvqdm0ZLz72g/3LFcwXjn4bfb2f+bFj837+vSooUWsb65s+9CiIjYktnP5yx/fiD7/4tjGG0sr9j7wAKqiNz6qEb0U'
        b'vN17871RCe/vfOFM5fqfspMvN95/+GpxQurViRsy6t6xVn5xe825ObPeXydl/Lpri8Wa9o9XMq5Gtb3kpZrtd2xXq9s7Wz66HPJzZXxGaryk60JB9ZvmF8Mvxmy/W1OW'
        b'9u+XZJ8Pbtrzxr7XrRtGfTJ4PeTC9iuK334yHYh9dV8BXxhMO49JYft0kda0Ha+1blsls4CcVU70TZlADq/qGB94BcoD4XE+rc3q59gQ5XkmKTaFLfDaVCaqTAaPE1UY'
        b'A+xz1HBUaWwNQ+UK2h9gbpcDzoPLsBdzxqfhdgz4Tie8T05fRuu94PpxVCo4Zgh6psDTRFmPOIadoCuVbiU4DteDnfSbR8EtLLDdLZy0ysaQjfVnS0DHEyo02pYWlww3'
        b'iTL94DYCbG+IWNNNQfAqE/atFNB2uHawc2GqluE2XcfGPoxz8+hgyboZ9hpvO/+5On874myHKBj91U5wsy9xBkT0dT2toYN74Qm6bB3s0jgDwu4gGvwe7siiP+80+q8F'
        b'6+fcvJ/U0LFBJ1HAZYDGUcPQpCvTMTip+yTYRAdJbVw2RpSBupGDtrjzFDuMAbodgshzk8UhGt9GeAJsohV38Cg8S2yAfj44h6zGtxLsnkIr/WAXrKM9NzuTwTUtlH8J'
        b'2rQwmj9UwCO0wnOjcXaqCJxEjeWA3aCT4qxkekaOoZGNNonAdr3sBiS3AWIu29Z6aBIKgrqFsI12ChVEadSlBzxJxQkzElN1DLuxNTM4DYk+x+NJ2axSJN41oNljiES6'
        b'Tgbsgwdz4AFn8qkGpONwUAnaVy5oYsyugr30lG83ngcb/BA7DRtcylCPpPshdiqQBffAs7CfNvccW1maqvO0pkwDnLA9FEolxJLqD07G6PhWU9AbDBvBBbqL4VUMCUi4'
        b'7ESwhxYExsNmGpdr31qHEYJAogSJAQBte3Qn7i0I0AoCG2fTcgBHozWGB6JhnSgBHHhcEAgCF+kZu48BNupJAh4rgWwlaCUwZ0vh0RQRH7Y+UxJwAs30W06DrrEieDEN'
        b'1UMbe9FbYC2rvBIeotXLG+BZtOoaENOb6c/0Bevx1PM1TyWIWGhr74GH9bhGRAR2Wi6D58xhDyMEbGD4wU4DY9Awhnbm3eAxKhUvfdL7RnAvE9aDNrBtIdxO3KhC4CW4'
        b'J5XG5gX1gcnghM8YeIpBOSayAeLNhaQ9y6ODCPTvGLQ8KEPYwUwGp9EiDyb5G0EL3JULjlXirsYcyASwh56Q++HhaTR0V9YKLTw6z4MFd64BjWSCiMHOAPqGgHS4DUk2'
        b'XDZ6MZSxwb4SuIlWkl8ud0C35KxEpM8PsVRoXJgUfwx7YnjUA+xj5Af7keQmAq2kmgz/JJzZHeJ1YEh5wXaDBaAbbiOzomh2BcmGvI0eENMpaWAHE3bAEwIaA68HKLjE'
        b'XlDvx0wEOyhOBtNpLKgl09RhwgzYUDNL69KsdWe2cae7GD0qgr2WyzUk0NgQLYZuJjjBFJE3l4HNSNYO9Bf64DlTzERi/2VwBr4Atwk9ng+e2P+zA0FJf1ZayseD9W6Z'
        b'igsKnul3oFdGDA1IkCHG2YR5BEx5QssEtYNbu6hVJI2/4+hyj8myd1O7ex/x7/DvMewzO22mch8vi/+RQ9k5ql0929e1rlNU9POuOV+3GYzIfM1Ltu4d16m33f0G/NMH'
        b'pmQp/bNU7tkDTtn3WJRgGuMeh7J3xYhTA97ZAzPmDc7IV6L/e+fftCvQ92HWuinwnJQ8n+6sHvtj8/rFKv+JtEuxyiFiwDpCzeM3RQ/Zu8k9jwR0BPR43rQP7w9R08kB'
        b'21biZqlcgwZdo5SuUSrX8TL2kJunPFvh1jGjy0nGGXL36shXeCqWdXt3lfZMVY4eq3IPH3Qfr3Qf31+kcp8kY8umthpi0wbO0sHYZ6Kzchyx77BXhHW53rQL1lwbLrTC'
        b'hV2ON+38H1pSDuPucSknF2x3kYcpGAo3eYTK0V+acJfHb42SV6oc/VQ8P/JBk1UOSQPWSUN8j5FGHg2u9ISmCXLPQZ63kuf9hJFHbevSUtpU2lwmZd11EqhdvAdd4hTx'
        b'p5K6k46lDPrFKP1iVH5xgy4p1wvUbr5qRxeMTRbdGj3oKFI6itSu7u1rWte0rVMLPI6Yd5h3WaoFnmoXj7sCT5wQclAQrBQEYxi41a2rB10Dla6B6hElHt5HojuiBz3C'
        b'lR7hI0s8fXDejUHPCKVnhNp9NO2HMkbpPkYt9D/l1O00KIxXCuPvjzJ2s71nS7n54EfVrqPba1pr1AJvcubhe2Rix0Ttmado0DNM6RmGnbzRaKuFQYPCCUrhBFSFq+19'
        b'oYudlZR9bwLl5jXcCKk5miEt0U3Rgzx/9H91UBieu4NBKTeDUm6kD3jOlqYPeXgr2KfMus0GfaKVPtEqj/EDXIE6bFxf2um0wbCkm2FJAymzB3LnqlLmDXjPR2VyKyXX'
        b'c8jNS158pLyjXOU2VmqhDonoCzwbeH3CwLRsVXzOgNd0qYVMouS639V2T6jSI1TtFaL28Ttl3G08EBKn8olHfaf2Cx30i1X6xQ76Tb0+49U5L87B34ye0GamtFCNnqi9'
        b'hD5b1CEadB/bY6N287hvY2prJWX+aEdZO6tDx/ZFn46+bvJOaOqNWQOjZ0jjpDVNmUO2Ds1FUhY2462RVQ3yAxQcbLnj4wkQ2RrZFi1NUPMdb3qE9WQrPSJV/EjiX5/4'
        b'mrVSmK5yyRiwy0AL1i4KrVcnDxIxwFSMGnAUDToGKx2DVY6hjz+OpomMfZvvo7BWondVKmkrJUmi0rxak11lV42S7yOfhg7ogp1ju2WrpYKtWNwf0i9R2cVJDdRcXotJ'
        b'k4ksTB6i4J2y6bbpsep26KnoL5CaKLnxuNS8yVxWKI9tXXiT643PLZss5eybXC/826LJQlZJT9UgpWvQTW4wujrIdVNyEYnA99vatRQ3FbeUN5XLC1S2Itw5tBV1TdMa'
        b'edYgX6jkC+8x2TbueDmbtprK42/a+eD0utZ0q25ycQy71PSnBzMQLQv9nmLYu91yEtxjob+PHtqhBf+OffgvD5YzUZd9TzFRPTQxwmtMkTXoGqx0DVY7ud1HD4fcY6Hy'
        b'RxVBiPwecZxtTkFh3ITZLqwh4ajZQdQtc5PZjqxbDgx8dDGZ7W94K0iU68J615mBjrSJ1JY2kepskpJL2OKps0ZKLv8lHL1n7z4kxxb9v8e2Hdrg+h1+3/focAIbXOPQ'
        b'pd9qqYcz5jIYjDjGQ2r4+Gcg97Bht5sTQV0wjWWzhKxbRlq3l+Ew+nw2Nfw/nUVlGzpM4GoNrsRHx1BjbjXVmFuZxOCKza0UifPVN7Wys/UMp2UGLiN8c3IMRhhV2bEG'
        b'xNT6xNURptZeBkWZ5CzVxEyMtLQSG6VYY7PTefYM2ze1V0aGiVZqzIl6j/hprIr54jJi2srDVlwBSVONzVLDNtu/Yv7EBmFSq6/2db4CEgpKLGfa99B2SfqV2AiMmlJG'
        b'2wpp06QgvrygMDRCkCeWENsc3WBJ4VJJYUUhqev3PZDIB2ssvY8jDj7NZIuqIy/WGhy15lJswXzcgvef7HVPgti7ZhDzWhXogu2Iw80MQNJ94ngk/Ez9HefdnUJjeApJ'
        b'0l3E6xf0T8vRt2MlYZsO3JqZ5TNszQI74XYDahU8YowkjlOwnthFgAL2gcPgMmzUeTDBk+uIUjMnwpS6LvTHuTf9RFmOdDBFc7mEzr0Z0c6czqDOvVUVj66uqFwqAgos'
        b'hm+FjVnYAJWeRrj4GdiBJs03xQ8czdZ8wQjFLCsnscgcHg6DJ4l61HMKklTxJE+fWEylw/2JNIRMoNEjisuk7HpCXp/JCQp0p7Wq6taYbFJ8tmg2dZuigmLGrJ5iazu0'
        b'mC5O7IwhpffKFzH+NfekASVY4EhVT6TIi6A0b0UoGoAQB7iZCgFHrKowrWF5ItFVz6YIt/qnpMNmbEVDsmiyxvBJ0tGmTk1K8Uuh5UskUDfOrzRP8YW76MHYB47CfX/Q'
        b'BXthovEiIB8nZBBtvKlDbGpW1VPyUU0PoQ1vF/NX0AYm0LNGa2OqqQYXiA/bbHhy6dNMesSe56OzS4H14KpfpfEaWOtCeuiLCBblmUsyKqe9azZfo72OWUT3X5l4OnUW'
        b'UaOY8aVj63K+zZSoMbQJLhEa0JrqI2ji9oJj6OfKtMXUSqt5RM0O1huCPnAMi5Rwmwe1ahE4RLq+IhNsIhHSE+AmagVoXE0qmYa+aD9sQL9KwAVjqqR8FrFOrQMKYsFC'
        b'IjZsQNsCbGWPZaDJq5hfRaPzjAN7U0dansAeY9bc1eOJ+WACqJ+pzSEA980nSoal4GLJwKhqZoUL2vQ4TeN3ZP+9TBVjfWXtq8tclk/zTuc1hxnYsIe8GmxftJ0ueGP/'
        b'VPfT27Iv/n2ruZXr9brxqw1S1274xwc7HRuXvHL2pWlOvxyoeXPNvr99+b7l3XzOJ1siPolyKT9+aX5mY3nZKsr1svtO28YZE2LWP1p4P82Dd+Pb09cL3nP6dstXv25t'
        b'91tf/C/lKye//Cp395qjeQYPk99yi8r7hTN2dOkr4JfdPt/emX3yGi8z+8s3TlaOcf/Ybn/cEMeYObPgu47cgo7qX21jZht94RvC7zn3YNParPfm/nrw5qW9r55SVM/6'
        b'Z7ZvtccSce/BjhfkdXayrf/IfvvImPMHvZ3MvrfnbrNsEcwpNS2eNObEZcm1t16eEmk36s7LGebfLpjRz7nzosXHPpeP9E2yz05fNL0399TXZ/IOfPG3OdJXNoVVZr+9'
        b'JulQ4Oo39n50/MM64QOXfVnXpp77pq7/TOPu9DTbr8/t9v7ohd3tY/afAYYhP/2W5bPBMEMMVNcy3q89bLNg00ZR1D/vhytBxwyxetA+w6xue/pv73XlXcqu/vrjX7cv'
        b'D8tvbYX5R+dfas9s6fll2soMV9a3fmN6z256+ZPRpoe/uDVuksvOgtyzfScl74592L09YdOHt5sfZNYeCbn16zRl1AyrW3mfjv72nemXL7WPe7FXtC7W+bQpzwvkhUR8'
        b'kBzfUmK+bOi6EnQ7jHvzZrX5r8eN58ZHl8ewveLS7zvN2/1v+WsnrtRGvGx775W1D7/bE7olV/SvR4Zvv7J08oCV0JbEeE9xgRc1odgWEqJ1MysmWoVpoAn20Wo3w9nD'
        b'cdS1IbT27LCtGTgETz/FQ1ECaQUlrAObBQTEiYZwAi+EM9294Dai7fNDdHkfjfcC5aVEM1cI6kmLRImpdAg1PJVMuzXuTCfKIPfJi0gAQj7viRAEeArudyNaOXhsrAiR'
        b'oSS4g0WlLWMnMUCvJYcoQirhlZxU4kuQCpvhWX9fjPXexmLGAgWtPGvk+Wpzp4KLcAsbJ0+t4ZJvcagCF0mK0/R1pJxkOIXH55PCSoiIhAi1JTkeduIvMnZmAqkDnSy2'
        b'AOytGc5cle3G9AcX4AW6D/fyUHMawH4jWgupr4NckUCUM+zAPKwrBIo0jYrZcizcn8SaE5FKNMUz3OELREUFG9PXQgWi2WhfEnEoR9DGRhRnXz75MI9gdEMD3rYyDSiO'
        b'kwCcZ7It4EXShgTQB/eIQIdZhj5ZJnowR9hNut1NMFejBoObQTOtCtMqwsBWcJB0rpWhrRA0kftGasISrIn2cSo4ZyMSgoZnKcLgCXCCfPEKIEM9i/VRoB9u1uqkzriD'
        b'A0LX/30N07OZf2wU+ENqJzN9p7Jbjo8HqekVEsXTy0yN4imPQdk56DxaFw7yA5X8QKLsiL++UOmVoXLIHLDOvMN3Vju7tc9und02pylxyMZVzlGwBm38lDZ+Q86+irEq'
        b'5xBpIoYmK0JV8AKVvEC1swf2cm2bK01U8+xlCe0prSltaSqeD6k7RuUQO2Adix1lfeQJN22EimkaR1l5cFukgq90DJLGY39Z30/4DnccBQSnf6rKZdqA3TS1g2u7b6uv'
        b'fKbKIUAaj8RkRxesMZPnqxx8pfFqT+8jSR1JTenSSXed3dHL+U6yyubVWAU1XVHVU9W9Ruk1XuU2QcZRCzxlBmo3L/SL7yxnN68ZEnjIJylyeqZ3z1N6RqsE47XF+IB7'
        b'wMWtfVHrIoWXwkXlMk7G+sTRdcgnpCf0mGWruYwtK77j6K529zri2+GryOoKlMXfdXDWa9gdviP59FSVQ9qAdZqehP6E9umPuBi7iBQJ/QlKl9gmU6yv4suMWiY8qaNy'
        b'8x50C1a6BavcQqVs6cwmizs8W7W1Q0tmU6Y8SVFw0zp0yBrL6Nb+91woOyep6X1HytG1bTTqR2s+uStWvkzhdtPaT41KY9V29rLEVhN5jtLOF53x7WShzdVqJ4GMoXZy'
        b'bk1WcJROAeg3ehQnAM6XT1W4KZb1x0mTldYT8dX0pnS5101rH23lCTj3Lfqd0ZQhD1OYKD1CexKVHlE3raPR1UFrL6W1lxw1UoTvSWlKkVXetPYkioCHyxhobrxjI3xE'
        b'8OeBp02qP+vv/iap0YYjhPQHHEoP+O05SuXPEtKfXKG0kM5FrZKMQoexqL0VGJHnX0hILxEjId0XS+f04c+4Rl9ikZSc5OMk+DNxaO4ImRz3DJGaVmO2zlhPJmchmZyp'
        b'yXBGy+UUlszDzHRSOOc5SuEYJ/N9nQg+nONMFyJDImn+ZFwXfY8Wr4++7ynI4QGCeNpxlrxK4+BLwr6wXI6KkrMyx40NCsZy8hJxJXYjraiUlJQV615BAwEOO8U+joBM'
        b'l//HUFOjDBpDaVsZPD9S3gDnXJ4dbLqIZZdI2HJmZHWqnreZ92IP1sxycI1IOOXZxcTbDJwFu3UeZzXgEJPOygW3E2SbEd5sh9E22M6KAw3JJb+4mRpUYElk4jWv3g8x'
        b'tujRl7hgFHAeDkv1fiws1fvscGDq+wPawNQsEpgKrF7/CEqNsnmvc2/YvX7cwvqHcCPx+tYWxd+uc4FF5ZhUo8DXNy+NsJA78ZMsiuYFpBqlcqNsr7142/Sc2yZhvU0C'
        b'82e/BRMquN5lc9lpBQZt17te4r5oVNHBjI9kFTtQG4bsjCUZQgPCBUXDNg+ay5ws0dh2N4NztLlxN2wG67FtqwwbTYchdVigk2aTOsxg/wg+Mxac1ljyz9jTxrxzjoYr'
        b'o7XWXH0+KhQ00czoGcRHHtQZiltR5YycNLj+OefMeXK7t6giy0m34Ts/tuGPLKZzvFN0UMvswr8W1ML3lGer+L54t3GUVb3F81R7i6QJMoe3rD3v2DgP8d3kPor4QX6Q'
        b'kh805BHUY6fyiJQZqb0DB70jlN4RKu8ofLMSEXCevZLnpfbCD9s1Zag9RFjP3jVh0CMK0X6Vx3i0U81WcgUkpejbXKFebKKlXnSKjub9RapeYfkkyaZptT2m1Q7ocEif'
        b'Vk8u1NHqe3+WVv+EG8+4ZbiqZClWA/7vg32vKjGJleQvLFmuwRPUJDMYgVSIKHE8rbsrXUmUeyVLlpYWYvVjYYGbjkprPulxID10+WnZKJ+ki+wM4pxuzQXnEdvOAAfQ'
        b'Sn1cDTPsVp3HNyqZBraU1C7IZVbEoud6gj6i4TYwYsoGWfDLcbI0eze/n26bK5LcXVnxYaK0CbLgTcktO9YzDvvuCd7rPLr4BsX78HWKynudE+0+IGQT6RDKK8eIkqJd'
        b'hiPjvVKI4GADzmBnXW0DQkYTeRVsgbtpEnF4+fTU+KcF1HWDXuKIBHaCKzFPcUQCB3g6XySNI5Ih2PgfkmxzxfSoaRd2hQ4bXWdhfuwGsvTD6KV/b2YRg7K21Zk2vWmY'
        b'YBq76rq3bqnfthWqbEUDXNGTuCCOhk9fcE/ggrjjGz3Q4WUzPVyQyUVoETn+aVwQtuSfDBz8NT+/qHg+nlYSKV74s1ma1kleZ2DVWkZGdmKG5Ff8hNUfQQQeRpkiQBsk'
        b'nJ4ENZMYNmJXIXwbIQjkgwjQr8P/AbnQgXoMKfgpPOcKjuaAQUor8rSwwcbm3O9sMWywR0e10jzwR6azeQwDwwUH3SM/70/QogUnY7TgVAaBC9bg/mJwXn7E1sk/GlmY'
        b'h913eQyK9wNz61YPpbnLQ6a5uSuu0vUe/vWdC3kdKnjANKKhiVEB+vWdNd2OCqW56CHTztzpPoUOuNzvHj79LgyXz+gOveAx5OrRbX06/j6LYRFxNyZBHR3zkDWJae70'
        b'kMLH78jxewNUeI9NLmSw8aP53azTWResLywcCJusNE96yMxk4Efw8QdyxO9KZtwj17+bwyLN6eZ1Z5/2GfCJejFBaZ78kGlr7vsjhQ743hR0L/r53QR8Z5bS3O0Hpom5'
        b'Hy5x/x7/ogOTaW94sDEH9mo4PXgO/0jL9GdSPt7wCtdgOTgJtlQ9YBIQkd3RiI3YNb4ctgVxQR3sg5dswseC2nx4ihMJt4ImsMsI1MP9cIOrOZAiFkcOjoPmhATQaQp2'
        b'gW0MR3gV9MGr5qA1Ep5F9OaMGJyD3dnmTHgSbISnxkeDq6AnCVydjO5qhNtWgj5EnY4HrAZdaeBk9Gp4BR4xhD3gKPrv4hhwCHTBw8XLQrxgazCshR1liCZvgt3wDGxb'
        b'PR6DGSJG8zR/8rLoTFvQ4AFr49csCoU74BXQVxIN6xZPdnAVOyRGphrMCqkJyARds5z8QTM8Fw0uwCOgF0jLwFHUNQ3gfBI4H7HEFzaGzIfbzeHhAtiD9VZysAt2ov8u'
        b'wRcWxMO9U0IXgR358ARshYc54AA4D+vKwWnYBA9kwROgp3oJPAiurgGXYEs2aLKHnYtz4QvgYLgNPJkELgWB7ej7m8DOUQngVBbY6J2KGnEe7h0HTq2Bx6aCVgbig/fC'
        b'DXA32If+Ni4ECrgXdFa7sEzBbnAWtof4wS54fuE4k2h4DmzJdwK1k5eATQWo2pZ0cFmYn1jumgh3lsCrsC0F7pllB06siIX94Awaqp7xHCCbKszBWiewB2w2GZ0Ne+1g'
        b'B+xEZ33pYAvYNxN1yB7Q4gf7xk3wGu9pzYNnpqML+2q8c0Xoe49yeXALlIJz2RXoapOFiTu8hp44Ck+DU6g5PRRsCS2Mgq1zQFsIuGwF2y3y0sHO4soJsHYabHEBDfPH'
        b'GsFroN+JB/pLwTVHUFeMHj++FNZDWbAT7Cxwnz57PM772A36weEKMZp2L8C92Wb2c1aVRdXAs05zncHeDNBpnwtPof5pgQoj9DFn0ZzaCztj4HYjsGUSvBiEhvIFcCwC'
        b'u6ei9vWBjTPRCDT6T0RTYtsKcIbvCLeh/rkE5RZrWfAyrJ/s+f+V9yVQVWVX2u/xHsNjngdBBUVlEBRQBAUUUeZJEAEFkUkGmWRQVFAQmVEZlHkWkFEZlVFSe3eq0qmk'
        b'W1NJW0VVOumk82dOqCpTZuik/u8+TCdd3enhX/9a+df6y1rn3ffuueees8/e3/724Z597am2oBaKL1HIoK4wT7oDtVcXHtY1KDqCuX14nEq2UCe32qnv40eYnSnqlhyn'
        b'ocT47dZUnyqlWvMbe2jQpeBqqhbfF97Wy8OQa13OuUhaMYii9iPUTlM0QGXx3GnDLbY7eZ4X6amEJmV8z5SfxCvmcBfNRkRfPswdxeEZNMYdEMOKFcbwRHiUNivgEJro'
        b'NqMOLg2NQtuNUdQi7H6qTIDplSq4BnEjTdqhzjQP02jxmWI97agbCft8UrhT58o+HajrMmKCXijfCt3cD7Oq9tkaaHllJxTtLrXxuAOUfAyKOc9V8dyYQcsY03Feompl'
        b'HvTgxmvUUxDgmcYTu7jSCkHhatEB+xtUcVYWTvPG3Jm3RUh8yw91XKTZvHqOpxW4vtAw/riQDEuV6q77UiuXmvnQnWgq4fIkLeqh4ZDwCMdE3Z0mPOLpo6qva79X0dQp'
        b'AhbUFchV4ZjfVh41pirASkk8DzljIpfoJpdLuDGYGnjKnDuDuSaKR2lGqgPdqzGifoxEQKbyOEdBuFTF4zR7udCEbm/B/SagUsOF0IbKqzoqsIaZ84jHFooc9akJYryF'
        b'6ZkEcs2ppGj6c48Jwrbe06d4DEZXzk+3Ci/ZDhCyfsksqTEPmDBEFa7JPJPJ1VG0Yr9JWKaPCaGnptC4Mb4dRo0B/joxl3lO+LMsdKH7DAK/NozhMZU68pjernBLgxAq'
        b'hcznonkwA6IbDqFpa55XpNYES+q7QlMFQtrDY7h2DBrpjnAZGoluL9jSbIErd8ZIcaqXb2XFU+9FNVhly/7Q3TSkfS6ARjyEbS4Q1jK3mEKTnlENRjZNj/2o4oywC3Mb'
        b'r/h6eLhzqz89SNJW5XJo7CB06ind2k7t5pegwi0KHrR8ReRs78dNF/JtMWszNATKWUOLMJxGWFxHwpnYLEBH/27uSIe0lxDfUg10dZQeUDPfizkOSFy1NYrMjz1LvUHo'
        b'4QDX86wVbKPh8DbHQq7Tl9HCn2ss7KM51AT9mLvMZXayGzSbJUfLe5pXqA0wOeQZ6HzVIpEmg68VGUrO+lCtEZWex8BW0cAQYKnM2QP626qcSbfpYRw1aWCGR8w1qMmF'
        b'23ypNx9VSlkYSQ93wyc9pBItBS5zB4AMGijTUxdeNN4pbCikRUd+pn+ZH2QZXJGmZnAJ3Ye9VvA9LQhqAMMb4mWaCcVk9utwTfTmVKhaGU8dQdi9zMsxu+CZHkUXmkF1'
        b'+zLduf4c/FeLNY1chjXU2WMq+j0dgXDVUEr4zZh9F/Zzg1U6Dxcf1byKDpZRCRS5n2YczK2S4mkGcPNUXZ+beJHL1LnKm7odT0IfoCToQDXftaI5sP8xunuV+5VNLSHk'
        b'JR7wjt5Dz7hT1dsGA64APPbCaXccoxmflDBM5AzdzIvGdLbBHfbQ0lWuvUStscrJ3Ox+3sde7tDvBuQLT8MXABPqUafZzccoiluo4wLVKFwypk6IB0YyBylCwan7dDp6'
        b'uso9kh3Z/t5cnaXBDcmRypvP8sQmahG0aw8Mut9bB90pLfgGVPuE2SYBarPkBGOZH9vyE/HxLeeoV5nbwlTFG7uJ78BoWqk+n6ZFgFtLAy5xgIhbza7xI2VapIFkHytq'
        b'96IxPfiCdhNhJ7ImdypnmqVDbdq1YIytjtb8LMLelzpOXON7ZlTnv+UA3MBTVUjnGdcqh9LIOcFa4sU5MQIh6hKWZpZieck5EoghYPA4RgkSku1MHXpHbMN0+XE0NZw7'
        b'RjeP06I29/rcOCO8EfvANT2qCw+MppEdPHtjs9c5mO0oJmUsE2IZo44zV8Tc7O1ECyf3XtP04lLqoFaPRDjmm5jpfmMdiLyCByS0qsONEUbam+D5avSpPjYw/iSsd8Xp'
        b'xMEM2HFTFDXZU1mg/h59Hs6g8SOwv6p0ureTb3qJuUQxlBaTjtJ97zSa8QimJao66up1/PomboMBABgHcb9KUSa8QD9PKVEvLKHaEBYzDWnd5U5HWqE6Exhq5w5aKuYn'
        b'Fz2guK3wdXe42e0i93sCVEqSThRShU82jKC3mJqLDaBac0lXeCTFmFuBgn1AippDfDtSx5mh8/U84ANeBK0eND+APnTh6MGRA4U+2vCLxzbRTDhU8SnNXtkHs1/hUS+u'
        b'g9jK4fV6DmwROFku1Z033yWoIzfoH5bDQT+6WULdadScoHP1UhB34i6zMK0WakxDb0bACMoU6E4BBF9ncg3D64ALHYPnzIuiPnvu5gHjEI1weIqH6Ybcl8z3/TC/Q7wU'
        b'Q13n0MVHHqDBA1zlSrdYsPQVbo5AE5VnUy8JPohLM014JgcIM83llt6nVXnS1MH7xGZ+5FXQKFDnDqrdB8XGEP6VRNjyvDiT74BEuLvY0tO9NHlJbZerci44bKv3KW48'
        b'iqFQrycmeAV3nsmFkJ4IKBS1jSqcuMwhXtiJDeidzLnmrr4lgFb4cQL3oM4jAEjLja1UYnsKsz0vdQEUNtOCjfNhHosFQ7vPC8lgl3fgxUbhoOcYwFZ2w47v6UJnq47G'
        b'Uq8/N4cdgWetTz5CbRE2YB0DtHQQd7sDPtJLy1qw7S7q0+YRX7rjUMiNmkFbUzKBdqXKsI7ua6pxNLnj4LFAY3cNKNg43de02yyFzLpUdV15dutOFYk337SAGEt2QOkH'
        b'dUzh4O+gzYkYLoule54EbPKAGwQ8gSDwYhx3cvehi4Cs+/QQzmQATH8SsyQOtTtFtTuy4KY7aDyEy05zf8xBqgncHQSxlVG1V7ppiM8JgcXUxF6noQRrvplIJXrXzLkF'
        b'7qrhDD/JheY0n+Cxc1xlt5daFKBmPYFc6QnlWgWuT6TEIiapB3ZXmxhDxLPnuOkQV1JPtgtEP+xIFR7C34C5wSFa/7yza0gCDZzj+ewYAHPvIS3VHU4H9E2crIHqs+pc'
        b'rXcseBec4eoO6oxAq40aUKxnmVQTdgoWshhDvTtpSD+Jp7Jwww4Ms+ss7GDwTLIB0KeRJuzpsRqEWcMtKVS9laZjc84axdLoYRrNQL0JajsPfGiTpKNjJeHQ+FknuutO'
        b'K7vgcRf41g19fibK4A5bkOc6npETCao2vSRoZWmWXClXoJSFPJbMw1dUwHvK9K5BhqU7N4Pjzprt1eUmbZDJyLCrvlR/Y+uOawVUEW8cGqceBh/+QPhHZfsB/c3AEVzm'
        b'LvCmIm0NGi/E3C5yz6nDavCXT2hV6xwPcls6/O1DRS4p4Psnk2nlWhZOdSTEgsw8kvMHAn9YopU0aP9MgjGX527lQSsoRj9sZ+xkFjcUmQMdOgXCm4oOVJ09mGmshisa'
        b'gBzNwvvrgqLB9EaLw4sjUwu3qQczOOsDHtwG4H4Y41GoCfnWkmC69TSfleOhS0+08mEmpbngFPVRwU4yS55MCOab1ByOKk/oljKPaiRz1QlbIQ3ATarMoXYtxCm3qLuQ'
        b'p+Ogq5N71G39AU9tadre6Vc8EDn1b4aNPgbY1JpaSSHL+3tBN+uN9OlelvnW4zDW8c284APcuo3gZBZOcDFL2ILIjRd38NB2hLejfKuY2q3sAH/zyrhZGQ85+SQ7FVrE'
        b'nIeZl8IcygpgCe2q1OjAdy44cUfgDhjDjJ5OXgLgb5lHT/NoLOxmwAI62HkApOWpE1XyfE4WPchHDF6FWNlorz7gsuUwMH7m0HZ0uz6VboM1KPJwBJxlFVS1yeMCz0WY'
        b'cLmU7vHjZNy3C7rWLtp+2T3ndJ5hKOZ3apsN7KWLGpLyqdOjkGq2c7ViDNemU5sb6k7TLEhnC1efgpOoBTXp1A/UpB7/nTdCoJ/j/OhqdAaoYku4x/EDRzOE0GzMlQY9'
        b'c21i6CmU6m4QTV1L0z8PDGrTgoLP2vGDE0U+3ORtA514ZLSNS/cEpkcIj69oWSvJEysgQq5WDfBz4iZFkXiP8N40/JMnJvCFqt4L4NtXeEWysUu8yE9+gibDqT3AVocG'
        b'FETiIyKYZ5N9wcaqK+jBYIBdoL+SSHxYJGjvqvwRy1RnYcWUa2XcIxaJ/UXwCfe5TH7/G4qA1trdwJ6HYvnDl9359KTAVyISOQqvWuiCR7oNy2g/og7BP76uuvWMjJoP'
        b'hWnF68EzNdhDH/ohqvsCZ9/Jt/y8g6gi3cPQGnDzlAdNrsI99VG3n7bnGdymnjoT+C4oC0yYe5yFVRfE3g2F9gVeNGooUL1iGkyO50o16suNh9000aoHlUSe4PvBQsoz'
        b'8O0eLj+OwwF6KALGVkbogsN17MGcdTmetoTqlW5GRDBlE41274pCcM/yZAxNeEq1CZONICetiCrs4V4bTlL9TgQL01CJ0+AvDTshxwlqdEWkVJ4fF0TPAqDvA3AUtdCs'
        b'aTNETWWIzKpcrYuo0gn8bREwMQmP0EuTFmDEw9TmkuxyScJ3lZO1uNX3ArjsEI0483yu7VZeOMtjp/0MaES5qCA5KDcOSNpAAzJh7YBazUy4FMIdAyKVAiKHYk6jvTrI'
        b'tDlaPx2Wu4Bu1O/HcIfcN6lGqnN34jl5+NUu4TJHRDMlkMwEA0xXHalOwpPRNiGOXB4FZOs7xJM7YT0PnWxJ2C86QvWHwImEza8luUYFUjio+jyMY4BWjp0Bp2yiGhvq'
        b'VubxNK73pfuHuTcCgVUdIpgVZQOuPWeRaO1lyuMqdP8c3c8VXmphrVnAI4m5uTyEf43FGuhutfOpKASSE8DjBiee9vIp0jmfRHNWGvREk3t8YV03D/DEHj8Y+AhVsLC6'
        b'U62FMH6WSjdRZxzAgJoP+54OPpMbedoIpKgK3nzByIXv5e5xAlpMX5IAJAZp3M4Q2p3KYwcQE9Tb6HG7kYDl8HqVe2/AVOf2gzFWC+tR1sHn4VXp6R7qyIdSVdLTM1SZ'
        b'BUc+QKPHYMITATdoIg5xXzemdcL/oHwJZlkCR9NzJgUx1SDdPWBket0W3HM2WAgnuOE8LXH/XhSrvGJuSM3JebvzjUG6xjx4/qwGl2rwspi6z944I6XWgkH4sLg8iy8u'
        b'zgBIH3mYH9G6xOOGSpsuc18SbKM0AdA8FXqGa/z1DT0RvaxSSy4kWaGmr3g6LjAM4FPvtAla00yPTXjIwTjAwo1mriEiqIwyDrFL9FSGV5s/cUq+SjMdshU3aacmZ8hj'
        b'WRX9n84CKvXDqayk8pMCemJNj6EY94rdbGEcQ9yZhe93L+2jdjg2oFS9oKgPaMqGHu3NBt3vPsjTSWcg5oqgU0YC32SA9WCkGKRvWdg+bQYLmvKBn+uWmvFDW8DvDD/Q'
        b'O0XD24Ctd6jjSG4gmHZ3Cvhn2REBYqeotDgDFN/0CAjDAxMtYXErkB9e1fVSpdHMWKBx3cZaQF4i9L/+wg50C06N+64DCxbMYAZdQiz3MOisKJ0rj2YAdDrPHk2Bd5jh'
        b'zmT0sDEfrrgMVwiP8HYlJtHjjNADPGukTc+2n4YqtOrzoKe9IBQbHjFK5oU0aI3A9EcRPSzn8spZRTdtbjN14MaQHIBanR736wJlm66BTpXQ6kVQntnDNKITYnXYyRIO'
        b'uJfvR6twn0825N5htatgi3WaYaiPrg736t0oOKhBFUcVgqHxo1C/ahq6DhjoKzjlS7VnALQ3bWlePxlGuQyreFIcmQl/mUV3JDyF7+PgegvxlwC3ne5FUTwYbQdcaucx'
        b'a1o6epYmtu7wAyQ0CXOMSXgGZGsDNEzoYBgrvHo9NBCNDuynxkwDnxDce9EU8ljyonlPYHBlnOK2w/mytIJvQVOjirZSVzjX/mtwG4lb36aWfVuF+DY6TE1Mc7pcFUyP'
        b'lexo4oySIY0wEHB2P1TgsespXqEa+zRX6GeDfNFkdJsdAExYpmvT2U3lwDMoaAVNIjbgZ5dD7KwxV2O87OFJI2bUpmW2CZKvo9kkGOqDw24iGjEBpIzuoDZXLrEAzE3T'
        b'eBT3RFCHYzQQp9KPOpOi4RAenxIISj/3RefuUpSkunHzHh4s5Gp7mt5+ksuy9tJA+lE4hQEM9yGIa6c3sIYWArlmdzTcRocNLPmWnUVkKg8eMDidy8+CoWnNcBzl+/RV'
        b'qCc9iyYBXN24w2SwMgxgNScEYXsDlKWOBq5i0HBVm3hoD90vgDNpCU6HKiFuadmtkUXlquYHecI1jVv9DTNpmUYKuMOVFj1zuQWyu8uTp7bQ6kmRC9/SUOFVCXpZEWRA'
        b'C4rC4sgDVxpKMfSl5uOmm1wRc9VgSDxxCAC+DH14DAN4CiVYuYjYc1wPQm9LSBSM5nyqFfD0tkKMZ8pFdZo7w0PpIcFp58+Cpk5rogvtcLZjqjwdQLWJ1HLK1ogQYtzk'
        b'2+nq8Tx+ku7qHTkXe427/YM2O3DDXp7anBrDd5wUBNoKBCpHDN3Dy4GFRRh9bYI2nFYfP9si3UHNemFckRjlc/ZokDeMu86d7+e5JPHCNqDRI0xpLQJDpTjgwrhatJkc'
        b'WwTAvgdBtibuoyme22YNo23lB1dga3do0kpINaOjDL84mhNlgJvWJvFK6EUSXl8LalAvoye6h+yBZ91X9G5o7YJhdaIBgM2z3VwVR90HMmGSc/yswAuERgtY3/9vdBvR'
        b'7ROJghEPc8MRrVwa0FdK3wXM7cKApgCHzQ5i/5N+QgSVyPOJPKMBu5rD+Pt2H9LkerPTm6VQ8na47jpw+PGrkPj9fSdlEfTImdujoN/tAO5FNSEkpzGzCIgccTXdMeTy'
        b'cG+B+eihsYm4rTToyBPHbRh0xn+zsPtjG/XYb4V53nejDgOIpyMPLudhMk1FmUHT2xXC9pnSAxNXKkmg6j2gv+4Aw60R1qaAicZULpPRVHLuDXitMpqNdhaS2SYLCF6r'
        b'nB/qRCPqByDmu9xmHAcpLehyf4oBP1KxuurpdtGIug7Q48AiKNYg3N4At5nwk3x/HtEF0bkLD7qUCkdwVdUrF/PYjUYat7nk08AhqQNPHLakYQ9V7szn0gM8rn0+1piG'
        b'dLQvUpMB1wWkoK1Surdb2TEI0wqaAcnMS82Dco4cCEvnR9sADyOwpM5z23jVG+jVQl1+nu4imEcNbBMkHNjVSE/UznPlfnhnKGqtF01ukomBB0/jYoB7g5iVeSFdsY5B'
        b'JJz4bXqgQrdSqcKVR+ww51XXL1GjSwwLK+X9Ipo5e8gUqLJIFWm7YG0PjanPDqbeBsOYRGTdeU5msp+XjKjlpEtAjg9c6DAN84QUl9ykGXN9V8QdD2jIk0YVzWBQnbS6'
        b'w8AEZPa2DdcXcb0gnerLNC3J2XkIvza4Uf+uSF6Ao+RmHUs3S+52odbkKKhOFTfnwjGtFJ7hx/vcIqgsIx/geM9e5ExD8YX6CQkQfEYqL9HtBJq8CPrcAPJ2G9KaOghs'
        b'Lbd0RVy4wJW5BwPOuwMLqrjmmh2EO60uhvKNqgvUGHPZlpRXWEzzIcImGWoPRJTeQ49zfPlRpNwtzvKS2xkParGCy0T86+POs/4gb4/VkhzA4lqjYRyrygmgaiXbCpwL'
        b'JLAj2GcTPxMMqRT6LFjSCi/ZAo1boZ5PXHnWGDw3iptU07xozJI7vPZQgwTurVdDqOGunYaQcflaiq8vuECZf4SrOVdczQZZXuGHnpj9aeqR8bKzcgb8zpiY+8J5cUcx'
        b'lSD4u7/TW0stnJuT5H9bmxCW+m9co3u0KCxpPaCFMAwRdjIkLBeB5A7SkK8ht10J23V6DwZ3n0fduPQG3+E5M7jGqhjqiQDZmrNTSs12NKZJX1UY/jjNJJrxbSGjRUUG'
        b'zGBFi3tjqRyEYBL+5Y4D15sqY5SDMjt+VJQKAliRUEi33OW5bnolPG0s445Txt7GUJhxK0XtzTx/OILqNY+oADoXucQHbGZMALb9/EgE/32f7+7VTA6l8jMBVi756aq8'
        b'oh15dRdQHpzcIzOU7uZwk2M44mqBhc64phZBP6p30aTOwQCYcZ8RLarSk6grGTY8vAPA9RSBXflZXixU5Yrj4bCLcsQlw4CdBsQsFhB3yxbuUleVnDfi2tPpabFxTtwe'
        b'oCk+bojrJqhBiRp1jGBvTfQ0Xd3Pdg8/2SKsfsJ3l9DyJnoq/AXvodlmxHx1CYfdwd2790EWffRos10WNQRuh1XcQeiTV0Bt+zALFX4856YG9r4EatB5/KoR96tfV8QI'
        b'Gr2pXU9WBINrxLcGWrXNOneFui0QUZbpuoTQnDF1ah9wV7/MN/253CxOmR+epMZU6qYxqNGdsGhhxZQfFghrXpj5JSFDIBxFGQ/Yc9X1OAt4alCgU6jbFYzB3IzkJ1ft'
        b'wctoEObSBGddpRadUHAaBtlDgkMBHR1wxthWi+neFm5MBumeuwh9mbhsDLUaK+bKG1QNJAf5uBlFLRnUU/CPYEquQhaSP1rBEWFh6m4k/DDwK/2weZiWJdfDAiItr+F0'
        b'p0lKosyYB0xcLDG5q/wohcaVfc/hHk/AkQYVnPmJKa3ywwPpahhQOffmk/AH4NLTbtQopWZjYPnyZW4LoH4JDodoMRnOZvg6cPEujOkepqJBdQs/8AeOjkHyddxYxKu0'
        b'5KbP1c60ZMf9lkFcmyH8pUt4Y8JMUihkU74TiFKtLuXR5E3Q+9kr5jDyBYeQbKjbgJ4j+ta415Cbt2+15o6dx0EZYBtewssD9VN5Tp3bD1nwoAZCxvIYKvPihSM0JisE'
        b'uDSB/9wHMD8QtucsKlGXmS+1qCE6GNyrRX2eDkJS1j4uNz5pwMPb9ykpcdUJL65W45teoQiHl+xBsSpdeUorh+f2qAc4Ur8TN3kePAKhzFC7FFY/AKSvuHrOXFvY7rkA'
        b'IFigUnNo+oQYxOzGJQcoW1MYlavJdWIhDuC9emEn4KCTK7MhtSEBBub2gnw0nU8Vdu/Nylfgm7jGiGecEdI0pFCVEvWnmtOwlB57HOQnQmDOJSeAXrOBl+HOnzkpgVQ/'
        b'oDorLtsNwTw2pP5iatGBUlZtE/6UrFik5JxyEi3fc9PkZjAHpcsCByrT25+FYA9k/ibwoYGG9LjtmFGh8FBFOCTXTotnL+2gUTta9qYH1orUZgF+1RFFIxcQ7UzQA7s4'
        b'MCB4beeD2fto0X/XRe7fQa3+NGS79zjPKMKftPhZgOR08bQDvNuIYCBt4brHnMCwx+x5NcISsNYSdk4zrvjkpmgoThWX7A/EPVp3c8t2961HioUEoVUXeCSWKqwVNvKl'
        b'3gUL7d7IgChkP+Ru7hLbGDjJt0z6btYUsvvGBAr5fempBTdZSzayLfYIz3sE7D5sJhaJXUTcfMVAfsH2S0JWpTBHkUi8VwRJrRTJn8Z2oIpN8i2W5bwqFYm9cAFYXLt8'
        b'Ues6AGwxwA868/jNClmKFfom3EWGaKczIAS0TEEkdsSZQ9Hyu+RsvsG1gZftUd9VBAup8N/oVIOHTwCI47PiN+tpUT5vXpFFXRJtrrWmXprBNSEi7udbJ+V3V8F4H3Jt'
        b'kNuWjSW1Bh7Tll9igXh2NsAW3HXyzSpcJFVbizfeYdsWg8H7w0c2ozlbEVchBOqTn9KiDvlu0lpqjX2zFIdJtBZ7y19zuJEl2GsjPW/J5uyMd08dEllL5D//+OjGz+bx'
        b'KeofbXXYyPq4A0MRfvyS1rndUvfDomBrhWA0Jd8bm2bTo6CYJzwS9ZZt2u1772R9eES7osXm5C9XPszdY/PEeuHdiF9c0tX6YdK5UlG1xPicqCdX/RPtK99R97Fdaxj/'
        b'm4OhnTc++9zFaSnp7+uzftxwdiSg59W7JepfrVd/t6ruq611794K/Oq9wHfrvvbVzq+9e3P3Vxt3v1sz/gfDSrWI+KyX5a7feSH9/MiHv7H4m5ZnoQfnlwcORh9IWbr3'
        b'+/VGxb//6f5LSstc9TKyvDB0yjjlJxqqb72c/OXvNW5H7n3x2XXNhpfur46e+9FvRyM2N+7Xsng3c9Eiw2l8eOH649qp78xUvvqu6WLw1Vca375bW5g9bx6mH3J9TPWH'
        b'xjt+0PRPFcMTbmmnlOx9P3i7+BsJ/gG9H/6Db/XMnh+M++Z0Drl8/TeW7/jNW+6ofTowoP9AGjkwN3VsVPkb/l+fK4+wXCk//rPQt9VMdiZ92m//PKAtIiEpUyP3f8X6'
        b'BH39k/biOfpFqizSodS6f9ahTOnSyOJmt7dtl51061Mu931/U+GhdMPmd37W4T70oyiO7gwfcM4KtZO8bb/lu4oXs+os9dvCN/3AxW1lx3grvwrNPPj2ZID7/Q+i236k'
        b'bhvS2nM16NOR6QfOp/KOTV0w7v+WzqjL2/t3pf2h7Bd53/w84FdukvFvdBvF17S95zVkEOb0KufzcOPQ3z/tlGU4/uCeyWvvTT8JbHXw4uKcn6jWTd78PMHEujX5Gx+Z'
        b'DvTOzBz87fA7rg/fUXr0+299IOvW+3l7YXRryj/S+8tFUU//vv6TrhcZv5/8yq5x9ZcuXgvJMW/ZffXnJh5RYQ8dg3/55W1v/9g9+pS/55dtfzbxJY0vB7n1zyyMnvrn'
        b'Lllh3K+eVShe/aRhRctbuikmOW/cf/X7XUNXUzqd3N9/4eZw9pc/tvj0q1FvBfRf2mLY9+Vvfmb1q6WS/VGVGnt7JbHvZ/xkUvHDScnSpPLvzF63P/qh6FXY9763a+Ll'
        b'd0t+oZr/w6u+mqvGwx+/XH/+7M7oj073/jTTr6q+VTdn34vif9F8/bfHXv/40Ee/r/7FzOdL2Tc0/rBanbbYvvWn33vrUIzWW//08jc/sF355aNqH7v1XysbHVO4cLve'
        b'WnVjuyj8tzfAAM6gfQOK7oD1dr9JHVYR8uePGsMldL153DiJWjZeKVgi3Xid1nlY7b/fzgo3d19eLwuoO6OWqyET3vRbq5VboA7H/lQiMhMeimiRqkTyA3m9MHiheaEe'
        b'fq6W173MTy5f1FASGR+RwPfc52V5SrKkgNy8S+oXC/ipFtVQnZaKhsAyVHlS65KiyFpTCmo8qPPKVrDyy1T5haryanR7o+UdikqiIKkSLRw+KX8A+xiVeaupcA+3a7xp'
        b'ToUfKuw5yZOv9gjymgo3yKPbKhfRuTx4y+ovtmcSiPZ4TgmuZZw7XgkvceIqL/kzNs/Ai/41C/G/yyVX7mId/sVnb1X+Hyr+6g8h//WLvHCRfHvskf/kv7/8lPR/8fz0'
        b'mkpcXEZ2fFJcXO4eZZFI/iC9KnzX559//i8lovVTYpGGwbpUWWb0gZZuvWPt5VaL2qK2vF7H3vi+/R1Xh0903JiynMydt5gqmD8xVThj/9axr+iy73uOgR8Zb2p1bI1v'
        b'298h6/V/YWw/afTC2OW5W/ALo+DnYSefR5x6ERb5nlHkR4bmvbpNWc+1LYV8UFHidVWRrn69Z4NB1dF1JZGRe5Xa+wbmz7f7vzDwr1LFL8Y2L40OvDA6UKX+XQunlxbH'
        b'Xlgce66yRX586IXFIRx/piSRHXqtqi3b/LEIxWtLZdnej0UoXuuayYxfuyniSFMq2/daXUVm/LEIxWt9bZnZJ6hstr5TZGJapfFa6i2WmX0sEsrXYQpbZVYfi1DUJ78S'
        b'PtaPiUWq2q8V8hRkrq9Ffyo/3SglOLkuP7meoYjj92VGrxWuS3BD0Z/KV/JSqGu8cYFU+L5+VEVktuW5ivF3ZVryy1IUZCavRUL551WF7+sn0bbxa4VtskOfiVDIz68L'
        b'X1/7i+MUZUI6pP/g41cbH+vH1ORDiFWWWb4W/an8RF72mn0q/3wzFOFw/YiW/IIwRaHqn8qP5WVrxqfyzzcXCIfr6aryC84oCVW/WK7LyzfV5T8XqUeKZeavREL5Olfh'
        b'sMz4VyIUr48qiCFIEYrPlMSy7a+VNIRJQ7FuLm8/TgFTJPpT+aZN4XD9mOLGIJVkuzG8L5Sv5OUfh4jD9VCNXcrS9ZPinSjDxBvHVihPvfkFxx+nKWGeFNZ9VazxU9S/'
        b'qfSF8uMCpWNSFYWPA1QCVDYrPFcx+TRKW6RrUeX5ocGuevFHNofmPV/YeMznv7A59k1ti16LF9qWvSfe0971sURkaPV9A4v/qs62/14ds/+sDkZvuPkTLXTr1+tnCsRi'
        b'mZ/4A92tA+rP7bzfM/d5T9f3ubrvxt7jXk+zQDfR19z0grTeJAhzzv3gL7w99//LIs9ZtPFq6P9DHJajr7wQ6ENepEj+MunX4WKxWFvYjveXC2Gfnvb/JOuZMJ9vSZU8'
        b'9UVv6at5bpWkJbZ9TzHPD7PpvWUhuf7DYAUH7Yqld36hY7jfozlWu97rm8deDHs+P1au/KOdZ0Wf37ZsKuTyi0WqcW+9Lgj/knHanmerP375d0n/a7vjVyxrM3K/ssNv'
        b'y2/0Q311vnyyz2bHyQcHB7/ZW/dJ9tS+5n7tHoWE+OqyuSev09Iz/vaFzemveOWl/eHi1+2UP/xO5qPUgzEv813t0gzC/D67907Ybz56/ihWapMUefxnP/vHt83ST7n8'
        b'w3juo7acU9+wTh/9uwr/D77x7My+k2+X/t3011x/J3lhe/nKZzVD6VMjv/yX/omDMe+5Wi3+pHVs6ap78LneasNAs7eOmjof/BGV1nooGR8llhV1WnzJ1X7v0aqAGIuj'
        b'dRc++q5h4sm9ngbhH31fLEsf/r5OiO+LLzmdb93u5bFwpiLz419MrUyHfDl0/J3f/djv4503UiIvfWS057Gpw8xvExL/5VOzn8t+XvSzzZ//VFkvNzSlI9N6q3x7rt4F'
        b'a4SUU+ZcHRIiT9kh5MmeVuBhqrLdSP7ddZwfBoTYGSTzlFBJ2Dmjw8sS6su12HgV+ojKYaqluxvJhoVVZmWRpq5E2BCzhYfotjxtS/xuN+E9GkHKIiWpAj8qVqEKHpUn'
        b'8DVyCeTaPUo04i8Sh4N184TGRl7bYRzX2/Idq+3uQsKROrFIZq9A7TysI29RwSJWnr3YlkuCFEXSYDFNpmyTbwWk+yDOwl4fuzfZjTW5RgJG2hnMw1HyTYYSDxuc52lF'
        b'P8WNrNE0FyIn9ua0nCNvlduOBgX58W1rP6lIl5sktMhlUvlW52B7Hgjw352fEbzfSSxS5kYFJb4ZK++ySZJ1gKMTgvcKXBnwJn+zheQQ9UXJRelDA9yIGpBVq59f0EYF'
        b'TX4kcTigsJF5+bYJblRrw3cunee7CNBPiIUnzHs2MkfPUcMhYft4EJWe3S0SSR3ENF7ktLH9uZRrzWzt+DaXcUmgWCTNFNM8VxfJJ4jHDxvZClm5A4U7qtKjIMhGKjIt'
        b'ltJNhAMLG9u079PA0QDqOiz0C1IT5K1mrcD1VLtHPri4fM08NWr+s9OqfgryXNB98gDlME8dptEsNZ7W4rk8quanOTx7ESGNhkhktl2qTM2X5e0EhTgGxJrL870JbYmg'
        b'bu0K3M+dVCcfygle3iHkks+hEa6TvEkmTw+SXwmvPOLW64cDaMJKmQYxu0IyZXlC+xDhHSnBdtZKIp/jykXXDeUKYkBVmWo8ybNZbsLLohpEPOR4SZ76yJpHuVXYuiHP'
        b'mKNYJFahIR6gO1flqd/TeCBWOGknvCDq4nbTN3HbpgIpVRyA0gqdtAlygrRrjiKMq+bqQAWRbKcC1fqJNyLH+YAA211U6W+3O8jOXixSN5ComnKlXDfdHPlOACaDBr0D'
        b'7HEtrAa91nOScPeBSxv5w8cKImwDFX132whZAoRZ4HpYjAPiO/kjXEM2Crb+irDPBpE4AALZRyvWnn+NoOiv7s/+r/tHYR/zXwhh/qeusvePhTxaeVckRCt/KBF9aiZS'
        b'1HtfQ/+lxpYXGls6C9/TsCrxfl+qWhlYGvhcx2LA5ZvS3R9KNT6U6nwo1fqO1PGF1PE7Ulsc//F/w+9I7b8t3fFtqc26gpKiwbqCRGbybXWLX6mKFLd+W2qBa18rFR9U'
        b'PA4y/d/9WL9eAB3VLwn59asTl8QibdNPQWXRqPG6BJ+/+2c1Q/ygaPC+tn6NIn5SNPhtno2giGpKXqYiNtX02i1ha7HXHhHbioXj3RLheI+6l4eE3cUoN8jY7jVJRnJW'
        b'7jvCq5IV8wtyMpLXpBlpeflr0qS0RJTZOclZa5K8/Nw1xYQrwoZqaUJ2dsaaJC0rf03xPOI/fOTGZ6UkrymmZeUU5K9JElNz1yTZuUlrSufTMvKT8SUzPmdNcjUtZ00x'
        b'Pi8xLW1NkppciCpoXpJXkLmmlJedm5+ctKaalpeWlZcfn5WYvKaUU5CQkZa4pn58Y0t9UPwFtKSek5ucn592/kpcYWbGmkpgduIF7zT0WJbg5JycJaTtXNNIy8uOy0/L'
        b'TEZDmTlrUu/QY95rGjnxuXnJcTgl5DJZ08nMTnI9sPFGyLiktJS0/DXl+MTE5Jz8vDUN+Sjj8rMR22alrEmiggLX1PJS087nxyXn5mbnrmkUZCWmxqdlJSfFJRcmrsni'
        b'4vKSIbe4uDXNrOy47ITzBXmJ8tcMr8n++AXDKcgS8nr+ifPmCW9xOvff/s/c/Av6K/sj1ftc+E/ge1pi8RVFgdb9R+Vn8vJ/TPW2KXk6it5yVPN0l/xW5TymPDkx1X5N'
        b'Oy7uzfGb+P+3m958N8+JT7wgJFgV0iEI55KTgq1V5NvK15Tj4uIzMuLiNsYg333+a2HTulJGdmJ8Rl7uh0JMcEWgsvId6/Kd9RvLDG6YroKMZI/cYpwRCwMPQgGdF4s/'
        b'VpCKpevqIjWNEuVPpPGHxPrrvpfBSHReqpi+UDFt9X+psuuFyq7nuz3e2slW7+32f19F+wNVw+dGTu+p7nsu3feBSLve+FuiTfLb/W/3fT6x'
    ))))
