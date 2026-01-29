
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
        b'eJzMfQlcVEfWb93e2KFZm51GQGhomlVFxAURZUdZ2i0KTdNIKwL24pZocEdxQXFpNApuETQqinsSNVWZbONkUCQg40zMZJKZTPLNaHSSiTPz5VXV7W66Fbck897jp7fr'
        b'1q2qW8upc/7n1Km6SmDxxzX+3l+OL3WgAOiADOiYAkYEdJxZ3Ml24LG/Ak4iw4bCjTHlTgD4gwLuLH4wSDTGjcT/59iT+FTOLEEwKOCZclUys2yCwSxzKUGggB8C7OZI'
        b'BA/n2hemT04Vz68p11epxDUVYl2lSjx5ia6yplo8UV2tUykrxbUK5TzFHJXM3r6oUq01pS1XVairVVpxhb5aqVPXVGvFiupysbJKodXiWF2NeFGNZp54kVpXKSavkNkr'
        b'JRZNisT/HUgvcHCdFEDBKDgKroKn4CsEChuFrcJOYa9wUDgqnBTOCheFUOGqcFO4KzwUngovhUjhrfBR+Cr8FP6KAEWgIkghVgQrhihCFKGKMMVQRbgiQiGpA3IfeaDc'
        b'Tx4iHyoPlrvJ/eW2chv5ELmTnCd3kdvL3eWOcju5SB4gB3KuXCgXy8PlEXIPOV/uLA+S+8q95Q7yULmXXCD3lHPkjDxMLpG7JkQWABGosq2NLBw60PO1UX5AHjlwL48a'
        b'CAeBsZFjo0KAGBQ9FqsGo7gBQM3YrZYwSssBT8D/3UnvCIw0EgIkzlW2+Obv5RzAA3XzGFDq6DPuJZCnD8OxaBdagfagBrQ+P2fKPPgGqkeb8iVoU2bx5GgBCE/noSvh'
        b'CyVcvR9OC4+jN1/OzpT6wTcyo9F6tDGXD5zRBm6efbneCz/3SYGr8eNMProIzwAej4EtaK9QH0SyrrOHJ6NontwqeCUTbZJk8oAbauLCS/B8poSj9yeV2YcOgez4BPx4'
        b'GTqRjTbnZ/KBSzB3FHqthtZgOTybT55nesKDuexjZ3SCG2eH3sJFkBR8AXxTm4mf4TehjYVwJwPsMzmwg0Er9KH4+Ux0AB11QKdd0FktXI/O16IzC2CDC5kUIbw09JYN'
        b'2uIoYdjmXlqCW9yQk4U2cuFWeBFw0WUG7oGn4Q6cgpAkvFC0NBsej8iMjkHr0IZstBGuzyfVgpti8qIlAjAp3eYV9BrEg6T3xeknvgJ3ok5SsyuoJSefD/ivMOgQ2oZa'
        b'cQJPnCA/Bh6LyoqW5kbLmBkMcPTk2o+eYKyON2yEG6IypJFofQ7aqFQxwAE1ctCJMeigkrGggEQTBbyHLykJCkwFmEp5mDoFmIptMeUCTMMOmIadML26YPp1xTTujunX'
        b'E9OsCFOvD6ZhP0z1AXgWBGHqDsa0H4IpOgzPB0LpEnmkPEoulUfLZfIYeaw8Th4vT5AnyoclJBppnCl0sKBxDqZxxoLGOVbUzIzlUBp/LNZM45WP0HjAIDSeT2mcGWUD'
        b'HAGYljWkVHpSrQVVmKkBSbY3ry/vfzC1fxb+LedcnDBDwFQRXhmnaWauji91AeNK429rVtn4ARo9vua+y/asmCDO5DvM/05zrpoM+oE+mpDnOs4UPFMaYqZERKANMTMS'
        b'MqLRBtheFJGVi7ZIZZnRWbkMqHaxG422wAZ9Ks7hPGyoVqdZuECvRedRBzqDTqNz6BQ6izpdYiJtHe2d7Zwc4BZYDzfGxybGD48blgDPww4egJdn2qHjsMlWn4VL8UN7'
        b'J2TnZOVl5majLXiCbkQbMH2vR5twVSIwPWyBu2SS6Ch4ErbBNwpwCafxrN6KdqBGtBM1oe1TARDFOrnBbRFWhMLD/0WkGysIoXAIK8WkwmDy4CdwjQPJKeRZDCTXz2rw'
        b'5FyrIeOM5dKBfCzWPJBzHhlI3iADydWQG3WiTMjVTsKhQydmdiqqS23LbEvLr4J3Ng6dfJ3jHwm9OYa49NzSxKJJIKp6GN/xnWvMN9O+qbBXxipW/vXPV7d3/+X9Oa/H'
        b'c+ckg65Rto6jORL+AzqnN8BNy/EYbkD1cAfuzI1cwBvJwFOF6OID0hfLR+VFyXAXr5cyQCBGq+FmTjSqG/qATE70pgxdjIqOyIjmAIFXHNzNiZ6e+cCHPDk6Be2Mikab'
        b'cuL4QOCGjsxg0HHc/0dovlgp2o7q41FDBjwOAGcZMxHtE0p4/ZwIicYZPx+4aEmHiOvq6vo9Uyo0NUtV1eIKVpLKtKpaxZh+rl5drhHiRBySejK+/LMO3J3IAR5eu0Zs'
        b'HWFIbBpdP6HP3ZO9aUluTt6T0u0e0esuu+4u63aPJQ9Fu5K3JhvUbR7d7rJe9/jr7vG97knX3ZO63ZO7HJPvk3FpBxJBv121Yr5KiyW4qp+n0MzR9tuUlGj01SUl/Q4l'
        b'JcoqlaJaX4tjBipPxq20VIzrr3EhkULTZQJ5SkjiYR34Pp3DMAGfOYsa5tU53OXwGY9bDm4NIz/juazO7bN1uWXr/s97mC8KTXcP75N5vV0QCg45xHCVnMGop5LQL9dI'
        b'vzxKwYIEnpmC+f9FCnYbhIK99R6EJlajNfajcH3RVh1aA9CaRaiZSkksJHZgGZXDL8MtQ+0AHoFN8E09KakU1k9+GWeZh4XUYYAOa/NoUc5OqCk7h4+apgFGgrkQ2gyP'
        b'0qLgW+govnkTv1yE2tEuLM0D0WqaZy68COtRZz4/IgowfADPwuP5VMRgZvMaOohIHu5UdB6g83BTNFvaAbhTgBry+WiPGDDpABPwTniaZkJbgtEe+CYGoHPwtNkL0F64'
        b'wZe+B+4Y5+iQy0e7VIBxBfBN1AZPsO9Z65+ESA70FjyG3gbobdjsy76ncSjsiMJ5GmALYKYADD9Wwr000yTMtt6Gb2LyQYdCUCtArXDHND3pYHTKFbZGyQSj4SHAzATo'
        b'yMshbDcfgq/DE+gg7rW5qM0BOMAOOc0QhAEHasKl70QbAFgKckOq9IQsvdHhhYW4Wkme4SA8JVfvSrgNbFmKmnCPpPOlQIoOvExHg7N4HGqywfXdOC8WxMI96BTbF6vQ'
        b'3jmYre6yWYClC9wCSuDlJXoRHY7R6A3UOQ3Wa1HnQgZwUBsTWlvDMrQ91yBX+zscGic6u6zxyjw4znvtp7fDRCfbd0+MXpM1qvwvh5x/M0S3XvaxW+PdwL+OnRyxd7fX'
        b'ymOrXl38233BK9s/1fin/PZf/1l8//vYv/JPjAmNPfujB2+0fdZDxzbv05N+4zfxLVUL19nnfvX+qF/vDJRFjnq75CNe7nf/uqZadC8n/mRcUvzcJX8KD5+98G7IvPr3'
        b'IgJXOH1058eRZX/6/urHvmMzF/3xu5S/M12LV9r9uuPg931tO784dHPXxilxn5z20t4c8nfupyffG/u3P/1t5oSFsy+6/arrH+3pYb/7z8mSxLMP7rfcs1v2T37pthBt'
        b'weuYyXrjFvqjHdOiZBK0QQqAAEPKfdWcBHgBdlBemY2uzIrK8lFGo/rMnDw+HrBTHLR3GVpH+W8tlpKHUIMUI0AMPwWzp0k5IfOR4cEQ0r0Xi7H8bICnF2G5hzZgeIfW'
        b'wzey+MA9kYsx1B7MbsnbhyTDs5jD12kxkx9g8HxHie0j3PaJFy1hOWIx4WRGXtbvoKpW1pSrSggb1gSZGPAnLAP+fjJmwJ59Iu9G2z6Rn6GoNbHNo03XUXQh8arHIBG+'
        b'hrS7fI4ouH7SXQFwddtls9Wmya4+9VMXnz4Pz12Ttk4ypDXlNDJ9Xr4GxXZ1n7dPi12zXWtoG7fbW7ot9U5AaMus5ln7SrbaNfJIhsytmYbybo+Ibcw9LgiMviP06xWG'
        b'XReGtVa0KbqFsfWpfUL6jv2p3d4j96caFrTNbQ9qcTW47k+97j2yW5iMU7h7EInRNLLL0f+Hb7nAJ1nrSDo8xjbNxxamCPBVQ2aExKaf0fbbV9eUaLGyVqnSasiE0HgN'
        b'0oU2ZmFglAZBpksmeTzSKA3ysTTwuwvw5UVFwg5BGDjsEMvNew6ZQFAN30om/DdRDXcQmWBD4em3ee4AKyGx1aD0pY/1cWBi8lekn/LyLuV9RWqex/LHk5hhbk6IxWKh'
        b'DsfCJlAmhmfUH81Uc7VL8PMxv97WqVCX2lbIy20rEhXlYFWSs0OwYK1ujEDgo/NRNUgcHSXXxM3iiarWHFAk8DGM++qV90qH6iNGpdtX+SpBwusPS4cafojt+SpjOC/u'
        b'q4zgdpVj2cQvvxY3F14VXjvwgfA9kBBd/yu4akWyd2rzik4+OLXc5T+Rf5Zw6BwNmwb3UBiUgtZiJERwEFwBjzwIJHVvxSKgPkqWKY2UyDAoxjP0JO4LbzFvtj1aL+E/'
        b'ec7xAQt9jBPOVVmpUs4rUWpU5WpdjaYE455I07QrYafdPR0HCN0bExoWG4I3vtKsbU3Ys7htyGvLbon8+9w8d0m2Spqi6tM+dfEyaFuWNy9vm9MbNPxG0HDyGGcbv8PG'
        b'EGIo2xveIwyuT73lHto6pds9vC3xuntMl2OMhogFE81zleryfhtljb5ap1nyAiQfabrMtCR5LSZ5X0Lyvi9A8hrCAB9D75TKyo2UTtU8S+zOWFH5L62E8Qehciml8i98'
        b'3QiV166wLU35KxOFqTxPQ0wNeUV6ggZjitFrCSANncYKGIhz4lIJzC2G2xJ4c5cDEA/i4Tp4jkpgrDCtskngoDPxxLCRgM4tYWX+OrQbvpYgyEVnibqbCM+gfWz67Rjd'
        b'NCcw8igAhoFhcGUofeOrSnQpgQ8b8TAMB8P5y+gbZ+NchgTuLKzxjQAj0NlQWgLWoC6glgSbAHgMQwSQVJJDE8fBbeNhJwguI7aykbbwLC23NkIPO3lofQwAySA5ZgqN'
        b'RG+hXVlaXrYDViTBeKcpND+8vFCm5cBO9AYAaSCtSEghyvRZaLNWQCYMwcgT4Cm0m1YiFldtr5ZBK4oxIgHpufAKLQS1zVmq5c+FFwCYCCbCFbEUz/hloNe1XBkms0lg'
        b'0vIsFnu9AQ+gJq0NVmQ2A5ABMtBWjMooXDsFUAvqxKgPXSasOBOemk8fuMEtOK6Th+u4DoAskIVbTCsJd5doUCcHA82DWHiD7Fq0mWbgwyas43QK0GVcixyQA1uQge3C'
        b'9jx/1MlMgEcAyAW5cN9yGl0wBr2NOvn2BI3lgTzUZE+LyYXNaB/q5KJTeH7kg3xk6gTUUMBFnTaLxgAwGUzGgJOFyN7oAmpyAOhKMABTwBS4s5rt9aNBUQ68SNiMXwQK'
        b'GC1bxGZ+uAMHbkRnACgEheh8On1lJoa1Rx0EcC/aAUARKEKn4EW2gxsrYhwYuGIpAMWgOBKtpKVkov1ovQMfHY8FRJLAtjCaeHzJdAcuOlwFwFQwFbbAN2g94E54YriD'
        b'jWMyANPANL492yNndNWwAcCjEL9wOphuo6I9OwbD3hWwgYd7YBcAM8CMEjd29A7BixzYwCGWMcI7ZmJoX5dX9c8ff/zx1SwewFMs6ei4UmkXdzhQj/7iP1xtLuYL3y3S'
        b'67eNzEfjhBOv/OPhta9uf68WT9iwfWhGRhf/8P71VR8mXveYwstak960s+Xjxevd19VH/6F/95LZ/zNi+c5Pbd9w5WiDW71ubbEpDV8he+WzBb/qrZj/2icz7syN3vyv'
        b'P1149d/98ed6v/3xf/O1ziXhpzwvp5ZudttdHht92jB8ZM66b685ejZPj4zTFim+bH9PGnG+7aWpF8O+2Llj5pTqYQt/eG336a8/qo54M9O3Mz25M1dVse7oNZmqefS2'
        b'a2OarzG3rgV/YQiJjH3/T/GjP4qtafv4rcOfyKVrXp2U++r4TRfPebjabv1LqTJ0xJ8T//6f9nHbzjX0ONR21cXE3MzY0/zn7dsSF32e9JvJvPf6L30cv/3Ih2e7v5O+'
        b'unzzu19z7365Nn70h2MDoq6mtvz24r/zDtlMbDsy+jJK/M/yH67obt5e19eX+ft3P64/xn1Q9H5g/ul1b9f+4VXwz4pMwfu/xziWCrNd8HVMbg3SPGJy2yJlMFg9ho6O'
        b'4aATfIxXCdiEGzHdnyDSEB5Ba6ON4vBlCc1fPR62ZaNNUWhTbjQ6ifZmSTP5wA1d4KJ1IWg/aznYBTtTMVrdmJ1pH0/MA4Ikjg/ahA48EOOnc/ToghYez8iLjkAt8Bwx'
        b'n6ItXOCKGrmwIxIe/QmQ1iyd+p2NElavLCHQVpNoEq8zOKx4zeCaxGvcRiJU77h7NWp2jNg1duvYXvfQG+6ht0R+FoIWizEfZyJZp9zlkpC3n8EYEoe0GkMRUW3GUGxC'
        b'hzGUNOpCARtKnXC1jA1l5X6gYUOF8q5pM9jgSyVdCiUN3qFv4ZMQfQsN0bfQEH0LDdG30BB9Cw2Rt9yjIfoWGmLfQoPsW0iQoHMP/B4bNuzjbzCHg0NbC0zhyOi2MlM4'
        b'YXiHxhROGXuVMYUnMJOYD8x3OUw+0zXZXFgRM5UhrzfezmJKGVIFemtLqlBw144N+wYYykzhkKGtGlNYGtPBuWcMD0u64Hah8OoQel+fedcReHrVp9/lODoF3A6KaHNv'
        b'K2wra/P+JCh+66TGVKyzGOJ26bfr73gHtPr1BsdfD47vSOwOTroQ3xM8usd79G4+aXlgW+LhoB7v2N38e05AnHDXGQQMaR2/N6vRrs890LCkx13SVtjhdnzqTffEW37i'
        b'u1zgMeyeLfDw/ucDPvAIeAAYp4B+kf9dLv59qKVCJSE1cYIUvCt1mDCK+24yg68s2BJgsKVXPhljURuTBcRKNF0ICqI2ph+IjYnLMK4vqlA0CULAQQcZ95koi5jSgQXK'
        b'4v4XUdaTdYm/8hyBh3wElo6l0s6Xh2CUpSFLfHl5mqH4hwoSPZYkqxNix6EOoxqBGuEpdX+YjKOdih+vf81ALasVzsSyOnRycstIwxTXtvd4R4du7hlfvyJ4TfOK1LXB'
        b'9VN8ItzfPRSypsvmTwkh9/WN16Q4z9otBeW2yrpmz3fLPnvnauu1q80CsCrCrnna5xLmARm5CVy0g2oJaIvSpCVsjpfwBuVOJrsny5l8Wc6k1Wn0Sp0eawAlGlWFSoNV'
        b'cJUm2cSliHmdGD/H8zChEZNmU0r9hFsubo2JDUuMDKtPiOfODltDYitnb1KPMOSpMF/Qz9Pi1zw/6SWbListSS+VxzBuLwLsh4PnAPa8R4D9L0lyz6O+8ljFdBMyoJUO'
        b'peiyhtj13gCweRncM1F9cUYEo83GCe7Fi1iKcjRRlGvEbzdKgt4t5fQcdvbM/ExZ2qiwrSjg7bZtamg6Y+BsVwg+5MVFJvASxL+OTKitAa8z4LtTtud6j2Bdk7yyAL1d'
        b'xJrcUZuKpSJ/uOoBWSycLIyx0DO3witoPatook3TJNxHR4+0ykxg3o8olwPkNc5EXklG8ppsSV7EeI6lX2tir3vEDfeI9rQO3rHMC5w38jCx3XKPbivvdk/ockywpirl'
        b'C1HVONNlvSVV5f8kqnoewwhfzvzXDCOPMrNBl3uK1AvXLmK0ZA3qfwoXEcNGY4XthLAKzF4wGV3lDd0ovAQigt4rtfvT4cr42A/qihKUU5wOf94nXV0XmX41svlzb/0F'
        b'4dxvm1cMcSxd4tWY0rVwokrsXDGlvF65+taRVeVzxxxcFMslK0H+cx2v/v0OpiwyGnIfZIDHctKdcqUcwMtm4OlgeIKFfU0RYgz60OaY/Fx4BOO6TXmZ8A0eEBXwhk/M'
        b'eAEbhlO1arGupFyvKilX6FSaiSbaKjbS1ks84C665SdtKzo5vX16t9+IRltMYYbFNzGDmnAyvz2/Wzr6KnNTmtonlrSlHnZqzOwTiVvjti/r8w644y6qz8aS1tu/Wd3G'
        b'7KnqEUVu41lZLXjkpf12VSpFOX7/khex1U00XbYAC8PFTEyEAcRw8SLLN6zhwuS5Qv4EJiqoJpTIYz04MC1y5AJqqLOR2yYIjPTItVq84flZ0aCcZ0V53LE8So+PxT7R'
        b'V8JuMHqkwlUbn0ARRayas2iWagFQ//HbBYwWq+mg77O4TsU8zOIcWBZ3qS54Y3Cdz5YUZeyx5O17y965KkZCZF/ofs03XAF5il3cr4Z8Ubo5dmhAaOGGH74dWfd6p2J3'
        b'4HtVp2wq94EP3op9r1SWvjZpontb1NZ/iGLfq4XzPy/itX9Rd8v2y8/1oz64Xbqw6kv4bmmFZ8fqUxEJta9zwZ7V7qIvt2MVhQylDRbxa+matA3gZAfCA0zxZHiJErh9'
        b'9OLszHHwMlE6WF+MTfAQ5ZyoA56DO7PReinOuSlfOoEBtmgjB65GqwOpVgK3oeYq/KwenYWXYrBWw8tlMH99s5gWXIbOor2oIRe+gemZFwNXM5MiFRKH51VFHqU+4stj'
        b'0kzMU8dxjspi5kw2zZwVxplTi2eO3y7pVmmTrD6tz91rV9LWpKbk+gl/dvG8LQowVLSWdYskW3mNTJ9/WBuzN5cAVZrIsGD76D6/oP14Ph2U9vjJGif8SeT7mTDAUN6a'
        b'2S2UkZCypbK5cs/c9pEdRcfG9gQmdwtH3bfjezvXZ2As7eFfn28xy+zILMNTK4PUWaDU62oqnszr2eba0clWarG4QJtHL82m6fYvPN1q8HQL+xZPt7AXRbIGQQRoc0iw'
        b'RrJmex0VAHwzkiVOISCB/38FzXo9ccJVpP0abMdk2BGaZr9YWgDUdfztPG0VboCmzn9HUf48GOuRv/uT/jN5xxxf/8sE3iLJKicX538LlGLevvOLts0//49zX495d8xd'
        b't8zf7Spy+HX6/X/dX75kyf5//WVd+2cb2l/59a0ly76InDoi5uGnmfHD5/x14he/2tgz7/jZxZErBRIf5ykg6oAgbUrsaYf2Pyge7qu501H4fnjm0PfvlDTf9PuL89D0'
        b'LWJOuLgy+k7e8ZcnBYyvd5gx6+9//sPyBdEBvNedJxWoK3w+i17tseKDz172/jrzi96/e3GOrDN8d+f2pI337q0aEtD/v/e6R6Zz7GSLrjw8m/PxSVXpH9zWCg5fPt6x'
        b'9IehxyeOu9Hq9fkHUY6HfI97C3re1P1t8oydvdKRTcc9h52VbvvszJprb721Ltsz+vub74xe9NqEA3c1I7976/aydVe2pP02ZsFXwV+tqf77jIz/Weq/S/0//j3aD8Sj'
        b'aj+ZMfNfDWXfHw8fPbxp7TcPeR99oz84KtvlwCyH0x+dSvzdaxvajrfdcKy5PMbv86xe6ZIfudxZU/Nzt0m4VABOhzvGoS2wziQELQVgvJblEMeT0Tm0YWm2NCIDbcrG'
        b'IwePcZYshqspV4JNIeg1+LYoCmePZABPz6D1Fa9K3H4ii3geLuJm4iKmPwtm4kqYSZmiel5JZU2Vmk7Y6SaOMsFo7KjFmqqoUdc0sn4C1nix4rDspktonyi0tQhL1i5h'
        b'JDEGeBq4OxzoelqjwhC8Q2VQ7FC3pvZ4hvUIw9pc26Yc98RKsO8FTk9Ecg9dVhO6Nk4xuO4oNkzZMb01rscjtEcYSqI9GjU77HDA1b1RscMLF+Vr0NBlCJKjYIeNIQ5r'
        b'LCNap7QNOTy1x0/a4dpRdlbU4zuyRzjSKlf9+D5Xt8ZyQ1HrlL3Te7yGtrn2eEW2KXo8Y3pcY9iHZTvmtLrumNXjOgTfu3nsCMc/Lq6N4zcuuuVDuF5qq6Zt/OFF3T4x'
        b'WwWfmWK6fSIbBViDd/VsLDLEGRTdQnGf0KvZpzVujz9uKw5b3t7C7TElY8PxBk23cIhlmHSfCOeI3xPQIxzK5n48bMqxoFsYfE/w+OstU8UZynCqwd5nmXuQmiT4El5+'
        b'L8kyAe5VN3dWnrSm3nQL6/PwbLZrDd7jiMdsG9Pn6LElf32+IfWmY+AdHM5dn7sx/86QyPpcQ+h1x6A+dz8roWDbz1uiUmieLgcGrHKllrRKCZNeTphkAcH/0/kY/98D'
        b'L6gEUOhlyX95xt/7+8CAEjCLuBADHWf29zquF6hhCmwxFMNAC6ubDJEJVYyOR5yFCzgiYHID1gloDNcixobG8CxibGkM3yLGbhafuCImcAoEpGST1NDZF9joHOSMzlEO'
        b'RjE6pxBgV4FFq01qeblGpdUqBRZNsGVFiO39xeYmmPx/sUAj3o0ciiKpx2OCrVGsCQrtLcSaDRZrAguxZmMlwARjbahYeyzWLNYqnmMpjEcXCaZBA9paiAPBQBEZ7IEV'
        b'Z+oLsmDOVaBtwaEzDQnzt5xy5gQLJ9jY+r98eNOmDz29Fg6/oa7JrnaPdHA4+PsvxryTL/ojw6/qbP7w47sXbsV8PO0dHXx19qg7dSCmy7Hpd7ftqrR/TJO8cynxdtO+'
        b'z4qPvJM/a3b6h+26EQqvN17+W/qXvfLrf7aDX3+iXzL1k1M//L5L4Tfvj4qGY30p3y/YA8JHBH6Y1tggGZF89MYHw4/uPtLWJvx1yF/+w/3gO9GvplyW2FNmz5mB1gww'
        b'enQRrSXMvhieeUCcWrk5rEPdFrQCnTf7W6A10EDRYlzSSNYXBO2XUXcQTsKC0bTYMRN51HnWKD9aUtGbHLgetVTRVeZyeBDuipJFZ0Sj/XADsSAd4sR65lIBNRoSr58G'
        b'uAVtyUZHdNFwC9xiAxy8OGhdEapnlbjdcj1syMcCCG2KksCjPOBix0UX4QEdbEB7WV/ANaiNR9NIYTtcC0/xgMCW44NO45oHk1GHm+E+2BCDYfAVWBcjy2Qdjt3QYS5u'
        b'6tvoEG0+7ICXc3Aq3MazY7Jyo4lbbgMHnY/1/tmQuK7OEhLblJRUqxaVlPS7GOeFzBhB5VgTYJHxYhvgF9Bo86m7T5+H3668rXmtw296RH7q7tei6/MLbElqTmqddmR2'
        b'6+wOt46i8zM6Zlwo6Aod1+2X2jjBlD7xSPL+5IMpNz1iP3UPMkWS29sif8PUVuV1UXxHwgWbbtG4Rl6fOLyRt92pLyAY/9j3BUvwj3NfUBj+cewT+TU6WLBFh36uskqr'
        b'kZK28JRq3ZJ+29oarY6sPfQLtDqNSqXrd9RXD1j9nqywkv4ppX8WSquaXObiy79JklH48r+Yc+ptGGYc8wCQ6wvwTsqZ9wqiwXGHJGsczZgYkD+d7HIwGTz+RzkYk9fO'
        b'9NuWGP0GJEw/T6uqqtCSAsTskNqmVCnml5UrxvQLTWNqinFijOKhDrRNOJl7NJf25E+qyRxcE/x2fgnpdAmj0ZL+GaiFRkcuenxxxpH3je/0OOl71Pdnv9OuxDTET3uv'
        b'i8V7i07OPjr7Z7/XpoQlqKe9VWjRw4knU46mPP5WnumtZYD1kGZNsVh+/b+y/XPz1Ce/DOVpiWj/4OLfO1c8UMwtta2YPGAsm9G8IiEATLrHabn4voShjDYIbp9t4nOU'
        b'x6E6dx+4E66VcCwmFWEjZsuVWmthfu/3NFGnVTTlO2SOEvxcaQu8/Q0TWrKas7pF4V3CcIuZz6eDMNh0phYzC5dhot9riD3djRmwfn6nsH0x4ENpaZtgCDjgEM2V8DSL'
        b'SKkacllKLstonfLIn8QZT9AS4uiM+ap9SQm7QQmHHUtKFugVVcYnLiUlFWqNVlelrlZV15SUUF6D2Zemplal0S2hPE1TRS7zyaXa1JR+zxLcXwqdWlmi0Ok06jK9TqXF'
        b'5bkSB2qFVluuVuqUqqoqHOVkjGJvJXw8ddgIi2ckuaXH9UAXjhtnZoMvmS7fk4dF+PJwHaae7+1dnPzvAXIZAkRB14NGdnsl10+65e533T+h2z2xfsItHCse1S1Kqc+4'
        b'5RlwPXBEt2dS/cQ7Tp7/4HCdIu5zgbPX9yR0F+ALHV091QTrZqK92pzMibBJkhUtEwD7uVgMa+E+K1p2MP7eL8JUk+JKZpIJdxYwFHdifKnjeYEZvGCAr0L839X460x+'
        b'YzgJHOO91f8C7ggjPCwIp7BvYGuLK4Z/fBbBmpEmn25vw+izwKbAdoTRQI6xK4m1w7H2FrG2NNYBxzpaxNrRWCcc62wRa09jXXCs0CLWgca64lg3i1hHGuuOYz0sYp1o'
        b'rCeO9bKIdcYtcsD8RkTaoXMZ6J8CgqK9Rxi5FW23E0bsPla4WkjL9BWBWcICP1yq0Qyrc7XqZ2GBv+l9BRG4JIHcBpcU8EjPudGyAnH9gizq505jxTg22CLWw7p8/N8W'
        b'/7dLwOM8g18wxFSPAgkG61wK2u3pmLnIhQl2BSGPvNmTviMUvyPM4h1eBUN1IjnQeRfwKN+PxPqCkspatQ/ulaUu9sZbdmOhPVmKUZcpqvt5ZFIPNmXzlDYWFEvmFua+'
        b'jvfX4kCKrfVGQywH7LAkwGODac60kYpD1oVx7wkTnFnNqdbGSu2w9bNSNeS2VpLAZqwtlQ+PxVqoHRxFFm6+fWa1WqdWVKmXkt2SlSqxwthQNQZPimol2W6ZXKvQKOaL'
        b'SYOTxelqnEpDk2aOT80T12jECnF8tE5fW6XCmeiDihrNfHFNhT0xnajY9BEksVQ8PjNNQrJEpKal5RfnFZXkFeeOTy/AD1LzskvS8iekS2Q0WxEupgrzOZx1kbqqSlym'
        b'EitrqhdiDqkqJ7s6yWuUNRosSGprqsvV1XNoLlojhV5XM5/wSUVV1RJxRLmqVqNSKnA+iUycWs2mUWvFdNkOF4YrS/MuxJ1QjkGNzNReMrTJtCIkZNqUauqfypqqcpXG'
        b'nNgIzNj0xhvc6ML86IS44cPFqTmTM1LF8ZJHSqEvZksSR9TUkv2riirJQKG4OsYScWjwGgyWz4ST2Lymu+fPz+IdNjcbfo68VizaqFlbuxrQPaLVcDt6gywVSGVkX2X2'
        b'VKwRHYvMpvs/g+ABHnxLDl/XE1sFPAHPEx/9XPjGZFRPNLsYtB6H8gtRPUlfnEG8mXJrUXNuZi4D4AZ0wA6dE6NGfQzJ/fYUuIM4Q0VlE9/+nCkZZvUNXUY7eWibBLaD'
        b'wlQbtAuuhBvz9GQSTwxKssyC6sl+Tfy6mIIMtCFHACaVhaDDAnQKnYQH1PmKLq72PzjXH2r3LSt4M/Zvm2Gs0P93cUL3IVNWVibZ7/5axueHXXKWlB0uqre3ixw/6eWg'
        b'd2yUfqfXu28+nvJdysLO6Udeba10jm+uO3mjcfqYLUlhVx3/1evQkfarZAffxOJ1n/YEJJ374cA7U3d8veCP02afnBYz9fyIpdO/XvRX+7/O3PT69j8GNX/4Z4c3q986'
        b'NubOy/YnXtpf6DPjo5iT33xx6ddnlx/4qve7k5ci/iFvupy56PSyv77146vV7fPl/5YdG/fy0Y8FBx42ePyDp3w/8q6kR5/+4Zo50tIpWzo3pb8xVHW9LiFgA7eck+g4'
        b'Gcrg/L4fZ701actaxrc4omH2+Q9VHkmvD5shHjMabDoYF9SAJC4PyBZKeExo64C7TZKrj45EG2I4wBOu4y2BO2xHotOshnxcZGt2f4texDrAcdAJeIB1cHsFGrKzZVm5'
        b'0ky4CW2hG2VBBbzkC8/wqseMoaZgDdaPW6Ki4TERu2+OrODnzKHebelV8Hw22pyRizbDzabsnmg1l5+JLsA9rKEZtaM9Y7HKvmVECZuAj3Yz6FK5mCrf6AoPUwKGtmSk'
        b'uWjrVLSHwVp7O9zJPt40Fx4mmb2dWGrlo0scBjXA7bQDUMsr0kdsBHAjbLTj6tCJxAfEjaZmqYQYADZJ6M5luD6WbSlbWBTs5KM1s1E7axFvgW0VtLQcBnDhZR1qYWAj'
        b'Wl9M/QQXou3T8UNZLq5mLTyHzjFwD7oEm9huXqEIJ7XMJW6AZLnOuRi1z+EmowMymnlCqgrnzclk8ZWzI2pP406MhwZ2FFvnjSGZpXBzTF50Bg84o0MesI07Ae6DrRKX'
        b'X9LGTvCl2ShhaZrAGFqNZRKGqkKj0JWZYqiSkMKwSkKpHfAOaU3sFkU08j4V+d32DW2d3e2b2OWReMvdixjfDZrtY/7kG9oVNr7bN63LI+1Td99mbeuIPa+0LbgZFHub'
        b'PBnV7ZvS5ZHS5+XbyL3lTgzWxW2JrTm97nE33OPuiPwMqTsW7Xp166u9oogbooi+oNDeoNjrQbEdHh2Ks6ILoRcWvB3eHTS+mXcnNKLZzsAzKPtEfruWbl3a9Eojr0/k'
        b'3ysKvy4Kb+O1KXtF8TdE8fSdyd2+o7o8Rn3q7tXnG9AiaZbsiWpMu+sIAodQs4d/EP6xMxlBjCaRoZGNvJvCkD5/MX1o/BGHkoe3xOF9Hn63PIJaed0eYeTXtttDQn4F'
        b'3R7h9+34wW4kGX5DcFgjb6eThS7lyupSjeSylVwG0z2ebXl+dGjJC0otTCoWFumD5HKIwBGik43BgR+xOvEy1snGfg/whSxRjn1R08ohQSI44zD2p5lWKlnTCr+EwJsn'
        b'qPgDlGiyqLw0YGUwFLXM2D2D9urDsCIzLCLyEqMMk8CM0KgU5dE11VVLJDL8Om55jfInVXc1W11eSZla+SSDRBu+lFhVcPru6WwFQ0kFMQh7av1+jomKTxXgp9WsjKzD'
        b'tpM7WqOopwOsn18xYsXRLMDhp1VKZdVds3bPYisns0RzP7V+sU+p32TO43HGUZZwMCtUsLYSOiefVv9KMp2czfVvntUbEHMjIMaii5+GIP8bTaikTdBcAkZm8rTaz3u8'
        b'9gk3AljXt4cxz4Nh/xstqLBoQfUzWlD9eAvibgTEsS2IfjaO/rlEzrIFWtenVXMBmXvngWnuxRZRrQ3XydJULjYSnbiKHqzzxLoZDZqOjxs0mf+CQXO1hLO0zD6NKG1a'
        b'sfoR7qVVqebTw36wmkj1OHty4I9RGy3E2iFuZbpeUyOerFgyX1Wt04pTcatk9hG4qbjBOOHC4bJ4WazEWosxe5dZaDH8vCIJw+7QPlSFDkQRmEQUGsAbx8Cjeeio+j93'
        b'9mGUghPMXH+wk1pUiTVVPaZzqaNjvOM7jsw1g2ZcgHRa+q3Y9FXeqwzXmhWR3zYWK08V0+2RkRttOEdHSHjUuwoeHAdXWSKyMegEcCaILMSTritloi2Fj+PeBbAVQ190'
        b'Ab2xkK5/5S7DmJM9fGaa0nj0jAta+YA0LiYKI0WKeUtTObOZmArU+kRTrg2x2apqFf0uJoFojKDIjCyTUIcqB+LmOnrr6BvuEX2hkt7QxOuhiR1F56efmn6V977tO7Yf'
        b'6LpCE7tDixonbM8liGnZ1mVdwtCfZOT9kFw+whedpZFX5fCCq9ur2IlDQNBgnq6O1p6uxNGJwZTOM1L6L+3pylk61b5QpWMNMvoqnXq+QmcUknota7Kgh1mJdRpFtVZh'
        b'ce5V2RJ7kieZmqmSS3NxHM6KfxRzVJrSR5T0QZ2z8/TE3VeCianxmaq3We/Omoc1b69Ydfnx8zwt2ZOt/GE1u604q7icumlP5p3O9fa5Km6RGFybg/5cEbdmRfAam0Px'
        b'gsj3rgrftW36baljhX3Fx2kfxEYk1FYA8O0PB3fZ1X5zTsJ5QPZ5q9F5eIbql/AgrLfSMW3hkcIHEYBulztcjk5UWyhZj2tY8ODsp2wbsHDz0ap0Jaaup5im38dE8489'
        b'otQ/zEj9Exwx9d9wD7nlN7RV1+0nbZxwS+RrSGxa0hq/ffntwIguycTuwEld3pMoqv9EGGLpaMvS/dYnEP8TPGx/Sy5d+LKcsfCwXYLngDfxsPX+WVuDXxBHO1v3zNOE'
        b'0QaCuewBKzN7A2JvBMRayMvnJXsZZlZRpEjS/1a+wXzT3K0CA94ddYA6KTLEsyOBb5y/v6xn8Bw8f78ZmL81GvUcdbVChyuvLn+S/K9WLTJKoThZnGTA5qpUl7NmONpu'
        b'0x4DXJBMXKBaoFdrjN1SjkNKnbhcVabWaalVkXADXKK2Zr4JwaqxMFdUaWtoBrYoticrVBrtgM1Rr2TfmDY+E8MC9QI9yY+RVwSBAGKN6a247EydgoAC+2f65dvm6cne'
        b'lmLYrs/OQxuNx16VBuZFT8mQZeUS3+H1MQWoPmdKBrdAAtszxbPLNJrl6tl2YPwcl/nBjvo4nH02n5ygZmHQG8gK4Gm0oxjLyR3MAnR2sZPtVNQEX6P7ltSwBW1GnY5o'
        b'RxZDtj0DuG/+Qv04/GQoapJonfXyDOKKUYzqpXJUj7agBthelCEl79iYmYM2MJi/HZIshjtD0etF08s4AO2A5x0noyt8ajFEm+A6uN+yWrXGIsVzMosnT42W24DJrwrg'
        b'IdhRonYbdo2n3Ylz5c9L6VTMJ+xxE8se7TBC+OvkZMwRh671GRr4biW0VahiBQn8jrK/Jq648UPOO44bxs2s+7JTMeVXq+fmX4rtC8y7MDrnnZzkjIeNVaq8TWsu7XHo'
        b'vg1m55wSVxiqL8xPqXxl7rlT4j1beqdee2fjuBLF7vq/Lf+ktML/bzZrMwJH5aQYfD74vO7rsskVd6oYsEopGu/1hcSOGp8W6aSY81PzUa4+kw8cqjloDzoG36YHp7xc'
        b'lOcQSfahYv6aiM6YWXEQ2b1+ErbCFdTMlAkvk1OsTHa6LFTHiYaX4BVqSnP0fjnbaCirxoz9KA84Crme8AK6wprSNkvnOWSXk8PJrM2JtkPgYVq67FV4hMUzaCU8wjUi'
        b'Gu9Kipni4JuLomRoU8TAuRHGvTzHamlu16HEkEeMa9noFIMzE+OaB9pHH6KzxQHUuPYqrCdmQGpc60R7n7VVo+4R2TEw7UvU5dayw+oRlR1tRtlRiWWHaNtYgole2fVK'
        b'4yu3AyO7ouTdgVO7vKdaWIvINo/CjtDz0lPSXr+xN/zGUrGSdlXZI8nsDszq8s7qc/fCxfgFtYxsHtnrF3PdL6aD1+s37IbfMJo0rzswv8s736pISVtIr5/shp+Mphh3'
        b'NaHHLKiMNinys9PO0jmRFVdm9vtkmUV9E62E1mfk8kd82WQSWsRPfaojw/gT30T/F12i3yUIB0cc4n+aEchsVcH89mki6zDRnzqASX+Ko4r1AFN+mnb3M00rElo7/VNt'
        b'Pm3WtRs1KBdPK057dBVqkHpKuP28+RpVRb9Aq55TrSrvt8PyRa/RYN1JybOonSMwythXcCDFzrSwSaUsuxRLFtAZuRM9ToQjd05wNMpcXqHF8mUt389Kzsr5VtKVN5ZP'
        b'Ze5jsZbaoYKs1A6IXfY8WRb/UolnqTAOCFjSSFbemdKa9+8NLIfRLmBT0SS4+0icgqjLMnGaopronQrjs7K5WBJTEUyWRrGULMxPGh4bRxdFyYJmOTEFYJXUXLy5Z5PF'
        b'E6sUc8SLKlXGJVZcYVLngRSmSpqKr67BTUnWqHBFqrXJ4tRHgX+psTrPsTpnT8+Y1EXAcxYiGgtouP9lVG9cTCjOwLEFRrnLxLvBJtiEOrNRZxYIQ4ec0W4wUk8U3ymw'
        b'Du3JlkVHZmEWP8Uiu7lkIVyRkVUckcUe3IW1CHQ4wBG1TYOH9ISRTIe74AGqfkyb9ZgCEp2VW2ipfzQU2qErcP9QPdE/U2Ed3I0aaBos97dEZRJBHkVEu+VKYIY0Kwmd'
        b'ypFlRkcKAGqQOC6Y4KsnNqL8pS9RYZ4ZZ0pMKk5eHIHlBdYlpJLoLD5Yio7YYdXiYoKeHtzwOqKLmtFZ6DTclMsFvDEMPMaZS89pRe1wh08UzgzfgOdxAbnE7bWZ83Im'
        b'YI+p3etSFYU79ApsMXYYA9zDuVjiHlSqe51Xc7Sncaqw9oTOz7A+9aWjESisI7upKVQohbY3j2KwwNGfvnO9nbmxflYu8LMbHj/k1gdHPxBeE3z+vmRmzopjf159bM74'
        b'gt96Xdv4Bjrg37C0IvQf0nE9L71ze2hOZfUfef9aExDqULj3t/zi36zeP0P4xu6oOr/uXUMda3//0jsbmbcuFJf+w89h20wfD5+V01bdWtlXN/ze58PD60cb0oL+9n7p'
        b'xynOBvtvFhykO7c3TRRf/6YSgwkiDRahM2hLTXU2XcnilDFxGCwZHpCFYPhaGHrNDCWwnEfr4TYrLLEBGvHAbrgVC+EG85KWQzUGda9hVAJPs3vMkqRoR3ZmLtyL3o7E'
        b'eJADbMmRJyu47NpkKsZ0l02Lk2gjxwJQRIppLSvRCdiKyx4lMu1vc0N1FKr4wcPoLK5hPh6Qi3TjiqCKMwTuh3vosiNqz0Kr6NYWuLcqnz1KTooHMIaLdqDXcSI6xFtg'
        b'4xzTmtxiN3ZVjizJnYCnJI4/axWN8N/Hl9AcCMowsop+d0voYYykoON/AAs65joRc03SrqTGpNu+Q7vCJ3f7TunymEL2J6fsSmlMaZ1wJGd/Tm/oCPyvK3QETZPd7ZvT'
        b'5ZFjsdJ222KlDWdtHkWV35vuUvpgUrdvRpdHBlljq2hV9rpH3nCPvBUQ2Ta8OyC+cSIbXdnrHnPDPaYvIKRlZvPMPbMaJ/a5+7BegHtybrpH0ILGdfumdnmk0kUvX8OE'
        b'Pg9/Q0VvoOx6oKw7MLbPI6jV564NT+J2H/CC3emylz3w9t/1ytZXuqwUbRcWuXxNLt+QC+mMF1/qGljKtF7sMmKcH8jlIb4cM612/RtjnEInhokiq11RRDuPelGg0yKI'
        b'AScdkn/6apeEOBIbCeFpcOKatbE4mIg/LFyoMDRLS0vrsMSeNZafJJcvyYX6SX5FLkcAXdo1mgs1xG1Cc4Zcuslw8Ij/ZDsnD9dtosRHs5o8WEMuxF9Ksw6wHuvlNcqS'
        b'EnYJkeyepeuW/dwytfKJi5f9NqYFFGonJIaSficrAwWLQwcQ7A80l7F1GrJvXrOB1NBNs+mnT9Pn2G42ru7RP3Y0tpguBN1ot+PLD8QD8x6P4yT81hY4ezYn7OfvV7aH'
        b'tmu7ghK6fBMvJnzIveUb0M49lfaAyziP/J6X5BT2D4Av9/n49i65vadjgIf/LSGeQ6Me8Dkeo+sn3BMAd79bwqF9Hsk4xj2lPg3HGNOkkjRpDE0kCroljOzzmICjRBOZ'
        b'+knGVDHWqbzFt4QJfR7pOMp7ElOfgaO8Am8J4/o80nCUVzpTP3GgrImkrAxc1ne2tk5h33rQRrXyDFE3nYZ+x7FziiLuouF3SeieBwgIuyWM7YpPY4sKwEXlsv3gvj8E'
        b'Z/ie4+kkvgvwxZgLh+5JTW2bRNqWydDGGaOmkKhCHMWWErJf2554yrZr6Mh3im46ZX3PCXQK/Q7gCykum7lL7u+NMVV9BKn6yM2TWA9W4n4RIEXHtTl5WKs9yGq4DLBf'
        b'ykGbA+FFKwhmb/y9/xLxYXV7kg9rQYyOX8DV4Smvsyng6Wzxf7sCvs6+IFbnUCDQOXqBGQLqG2ln9HHlUL9I1wIbsxdmHIbdjnLXBG6B7SO+kE6znM2eqg5mX0gXGuuI'
        b'Y50sYoU01hnHuljEkje6zHLDbyC7f22p76JQ7pZgWyC09B01v9GdpDfX2bXA1exzSrxtSQluCfwCt0HzesxyJn6uA56cOA/xZvWg3qxeuIUM8XjFYVGBl4j4corw1afA'
        b'G199jWmpR6vOj3ix6vwL/PA1oMAfXwPlNjg39VLVBckZHA6kYXFBEH4aTGPENGZIQTCOCTGWN4TGhRIvU12YMS6Uxg013oXRu3Dj3VB6F2G8C6d3Elp6BA1H0rCEhqNo'
        b'OJKGpXJ7HI6i4Wi5HQ5LaVhWEE9NmWR/XbRxf11MgUwXKwe6OOrLulqS0C9InU9dWbuIK+tSe8LH2RjWm5X9OAbWVMjp4HM0xFNSzOobyiVmp0sNVplSNTjhfJVOrRQT'
        b'X3UFu+ygZNUfHEE0HJyXtUVWLRHXVLM6jEkH6eemFxfkPUyp1Olqk2NiFi1aJFMpy2QqvaamVoF/Yoh7uzaG3FcsxmrYQCi6XKGuWiJbPL9qYjunn79QUaVX9duaKmll'
        b'9TXqNo73FzPE6kvOgjB9rWQO/VrJ4LKRXcORm79NMpubtAjnENEcnMncx3OYCNFcujtJ+xLf9LwAD4zUYrfhwFdQiLVZzpjua5kCjpwhBpDyYfRtTAF3NlsbZrKlE7Gp'
        b'XHMdCwRS38fLl9oPxEn5FmEni9YyuXb4PTzrOLJeO1AvOag2a/q4BxzAY39mbR1Um9tJv+hSKbFZ+vfHPIuNNPe4YzEdTla9VrBpaIyFSZod52TqvluYH50YHzfCkkTL'
        b'sRaeWUG0YbG2VqVUV6hV5VKqI6t1RIPGyNfkM0xLNtk/WPI376agOZLJbXJpuapCgYFCiektpVgtVysrSWlqtl2YwI3lYqqW2T/0VFfTpeeBioWHacP7GVk/E/uQK4uN'
        b'zfvqR/wnsekXPlo4WVdVVNVWKvrt5aR+6RpNjaafr62tUuv6BSUsufP1tXiO9duZc0kELIh1IDjNkXkcV5BBsTikjyKnfhd2GMw+dX8kuGIXYM+e9sCSuy8opDco8XpQ'
        b'YmMGgfeLm0a3pt50D2ub1hs9+nr06N7osTeix1IsnnJhcY8Z2Xv7GdL32Dfy+9y9DGHbU/o8fAyFrant3Lb0k9nt2Re43dKUCwU90nHdEak9oak9AeN7PMZvTb+DkxXv'
        b'yGtMvxUY1qraU40hu0NfsORI4P7A7uC4Rt5O55+7fUsjYp7oE2HuDJNb1w9WbkAzd8+0WJCyJE1KQEtqVeJSTChKjCarZBPY39JSmebYz6lxO6PxeXKNNf444t9WtZy9'
        b'm93i9tCPOp8NPj2sqsMxVSfvKdV5GsubzHv8mcRsqeRSiuy3VWhL6K6AflvV4tqaalX1E3fQkUb9SOjQl21Uecvc5rm9gXHXA+O6AxN6A1Ou438B7J66h0rqMKafX6bS'
        b'kGEw9r+4tkqhJN4qCp24SqXQ6sTxEpm4WKuiE71Mr67SRaur8Xhp8CiWY10Nz1tF+Vw9TkgSWJdi3V1miUI0CrJ5w/gNHGD+Bo49Bjwmnxf+L7qJj6OYTayaxbVEHWHZ'
        b'qGqxslJRPUcl1tCoMgVZGq1hXV1wKoW4VlOzUE3cWsqWkEh74vhSq8JSOg0PgQY3cryieh5dH9TqarByRJlk9aAM0cgMTa8soa8sJf2qpwyQZa+E75rXBXG/ko0X9lTy'
        b'Y7BQWTOACKRirRpzfmM2kox4G1lt1zDW2ZgxmXzVK7nUCEJKiciwMHaW1dSQL4eIKyytpnraVeWPdBNl7YtUGjyNF2IooSgjbk9G++kzt9876WX4BrVmwzejojMyw6dJ'
        b'icUqeyoxQqLNGTiYXxyRJc2MFoD5brboCtyIjrGfdHrLbxFsQB3o7JSIrGjyKZgtUXnwLDpQEI1e54DESegwauDPmTSNbn5Dm8RjtbLcLLRjkcANuMBd8Cg6wZVN9qAL'
        b'jUuyNZarjBF50ZHZ0QWmYrP5AL4GDeVCW/hmfhC1OwajDWi3NsL4aS0+WhEPtzCoQ4VaqaIyzQceK4Sb0PZitAntKM5lQE26bT6DzrwSNJE1ah6GF6NoffahdXzAhQYG'
        b'1sEzhXpiUhuCi23RZrAWy2x4QgK384Ar3MWFb4ydTM/3i5+OVmoj6Cm1/JFw5zIGHfeFF4rU1zrfBVrC4T4Q9y4rGJ3NixPurTod9OHvLwauvNMb0NC6aVrAgdLoPw5P'
        b'43RuOqyRT7oKP4FB1aer4fhPspvufvmbPd+vTZF/Wur1gXik73DuJYG2LkXlvWZIeppop/vZz84tf/01w4e2w6e/FunX2jbn935z3EdPL48t6+Ve2st9DX095PTi0mWx'
        b'CSi5J/j1X/3mq4wRLnm1F8MzK+amPLxSfTMv9ZXPF3x05iWR/PbK36z/7MMJl+OTxq4+8ucr2y/5jjq7pt337yWbr1/YsS1p3+FLRTzBju9LQM3tmpyoqEv5kSdco1L2'
        b'ff6ry5eHnYkBbvJxzb8+l3Xx7RPfXtp3qmHm94XXbi/5su/QLMWig7fP5t96e2xS+e/+VfX7/L/87ejs9lnOsnfDPmgpmT9TukSSJnFlTwNuQ7tS6Gm+qAEe9bABvGgG'
        b'Yt2SPiwcXh0VjQd4fUwG2sQFjhMdYCtXAEqpNdQTU0QdbIghCY7CTgbwYhjY6QPXUlunGG5YFJWVm7MU7sdPghm4dxFqYE/aOeIBO7MzcyNzbYDACb7F49iigwJ2VbRj'
        b'MjyYTWszCm7E+UQMPIDOD3kQQh4eRCcyzZbcaOEja8LIgBqpLVU3zDtKJok0kSRaDze6oNPcJS8xD8hR2tVLlcS8m412Gm2wU1A7+/LdqAVeYs3Ec6fgh3kM7IAXkqgD'
        b'HOoshY3EuJoplcH1qHNJTHQGtbCKxTx0Dm5nHhCAji4Hw23ZdL6irfAynbNwUww7aSPRW3y0EpN5I3vawym4Fu5mG0tWD9YzwKHcEzWRVfCDhbSqPugQbM7Oj2YAB27O'
        b'WcikDkOt1NGuIga2zVJbH2QEN4Wx3dQEzwdn52Zni2JzZWi9NBtuyqc1jYSb+fAkroGBHYb9ry5ADXnwuBR1jBUA3gQGvj0lViL8xe1O5IxxqxOOzAZkT5aLllgz/n5/'
        b'I1wa9Cm1KY9njKcRCoGraJfDVocu/2E3hcP7vAJ21WytaVUeqdxf2e0V0+uVeN0rsdtreCO3T+i1y3GrY1dAfEfaTWHSLS8fQ0hTJY4X+e5avHVxq0O3SGrc4DG0K3xs'
        b't++4Lo9xff6hvf7R1/2j28o7Rhyff2FGt39Gr3/udf/cbv/8Rru+kPAjI/ePPDiqkXtTKO7z9uv1jrzuHYnBqU9go6DP17/Rps9f3JLTnNPm9Yl/bOMEjHlbs3uCYjHk'
        b'9RvSmthmc3h0t18cjhf571qydUmrd7cosq38pii+LzjMIOgbGmmI2JpvOs4i6RMP6T0nEBB31xl4BLRye8Xx18XxN93j+yTxjWk3PYaSzRwTb4lDW4uPzNg/4+BLn4jj'
        b'GzP6REGfiGR9/sGGfFzobsE9GxCccNcWeAc2Wm7RcNDMAz/FMs0ea/Ho9otkoiWMwhcux+JAoDQhw7iSUy1e5JhjDTmJBgM6onhYuUwKgKXbFd/8JS0+PY4R0AMZTW6T'
        b'gl/QbZIsAcsJWEpj0YJxOyuL2gnaw8KeAAQzMDZiJgKgtEaN0N60zvoIyHoEUokHhVQyall5JKeCQA4rhGMCKDUECZFF4yUEi9krFcpK1q1qvmp+jWYJXbOu0GtYUKNl'
        b'P3z6mEJsDfktHOR1Cs0crJ2aUlqtElebl4nZ+WxaJTahQILlVFpLM9Bz+HgJ6NF7Y+ydwLVsepB0zomylwCN/CjwPCDWmNaI95d5M4XGD4R1ogMhWicnuAqt4gAGbQbo'
        b'eFqhPoMCobSobAtshdaOJUDCtPpswhxFxLuKbB9tiJli4bCFGerSQGEy2p2qDpYWcLX/wiUyRYvYgzadTGcJDzMMM4yusytck87jptkncFc5psW+GS+06Sg9KqEHcr4/'
        b'fymj9F6VvH3vNm5cVB23cJm3EoyoLpSurrukTL204q+LFxxrUPKPPag7+idU5PP+vDh+G/T/xm0zSL1dwfxeslpyDK0ptYlb+Ru31Q+zPM5P/1a8JC7nB87Qb4KD3i2f'
        b'4px4K2BuvJenwnHn1aTcrfz2+q2rv1a+d2LGOqcPc7vONL7jfaIu7ayHm59EXndCteZSjvs38fK2qNVxL72zoXui3KN7+tZcF6V943s6p+8aHSriFCvf3DB964WCYMe/'
        b'DDfUx3Pn+IJvz0XOqPtI4kwFUyJsQW9Rf6xQuNG4dTIe1hk3PqaOoav1cFMo7VkecJFzq+AeH7pQi95Eb4osxmNAbsLDM6jorIEXKbQokObQ5X092mmDJeMBphjtT6Oy'
        b'D57KQauJ7HtU8hnGs8LvciF1Rn9FPYpd4uUp0B6CAUQOtIqvwta5Ufl+0GA+P9ABnuagY1lCFiEcTp5Njhilx4v6ox3khFF4GdazQOqtlNlRRszBQ8fQCgIfZsGzdAF3'
        b'2IgsCh4wdDhDAIQ1ejg+/AH9Vmc9PDkkij7BNbfqCQ46DTcwJRgPrImxhYdc4VHa3UK0Gq2MokvOcD3cxAeCuZzAhf4UXwxDq1CLAzqE3n5sv6xt1Ui6Yi1BLeOjpLkY'
        b'7vvALcYPk7nAJq4Gg/LVErsXE/N2wOIAKKMfv1Gj6nc2SnTjPZXhQ40yvMoV+Ie2jGke0+0XRQ4T9jPoWpY1L7vpLu3zC2rM7vP27/WOuu4dhcWqV+Cuqq1VTdWN3E9F'
        b'/uYHbcqTle2Vx+be9E7q8w9qyW7O3pPblnrTP7oj5HzEqYgLBWeiiRjObM7ck90W2hs56nrkqB7/UReUN/1T+zy8ez1k1z1kNz1icYEt9s3UtiQi2wpa02+6S4z7BtrS'
        b'b4riqMfatK6ZJb0zK6/PrOyRVHYHqru81Vi6toWejG6P7glN6vFPakwnjdDfdA/FwrdVf1MkNWVU9kiU3YHlXd7lJEvE4fwe/wSc2jugxbnZuVV3ZOn+pR2ju71TG/m3'
        b'RAEGVeu0bpGsSyizPLyVtcVRM9xznNXHHtxqdVhfDslKvr4i5Vh4cRe7Moz/ty/oEKf5HDzp8KGj4MkmH/mgO6GoZTqAfufbwrqN0woeT2u2QVs8CwEFzE/LR0T6Q06Y'
        b'+iEvTBZfIeHR3u13LKmuKTHaa7T9XEWZltqbHrct9QtLzD5XRhuqyGT8fORBHunyZNo1d4w0NqE3dNj10GE33Ydhaj8U0lp+ZO7+uQdjevziujzi7vgFH0pr4520b7c/'
        b'mN/jl9DlwW5Ws1qJsDP1eSRZieDUAdamX8hNNPay+SvqK1m7/xPGZJBYsjZRPtO4mjHImJlLDjCWzH88zeAlD6xK5EpfMq8+FGBolsw4kjWNQXPRZ5zBW0CfceNtBtY/'
        b'cDrbx9PV4nhqQuQt9TJjtPlqLR4nZSVFQ0u5yeLwpTbh1HYV3s+ES/gsSbir59dWqZVqXQnLx7Tqmmo6n/rtipbUsuZ0lkjYjUX9fAoF+23ZZSz80NqXV2zeX9TvXFKr'
        b'IQ4LqhI2i6eJgqyiiwn91ALKN4kzi6pV3usuvYE5JVYglm9d3uZxMqA94KZoOKalXr8E/K/LL6EvVHIkd39uR+j56FPR3aHjmtO/GBL1u5gRFzyuBLwV8AH/t87XnO9y'
        b'mehpzH3AhExn7gImYDpzxz+YcFLMnUT+jY6PW8eNBizb+2QsUhiCzgqZ4GeMtnlsB6Eldmzj2XUd7lJbtgMiwpfywqV4ODjhEo096VoOywHNe8bEA/v5cVdp6FmDpqUH'
        b'NqKUYzT5/nMFuBUT35F4PvlU8olXr/Led3rXqUuU1yXMe7x9XFP7xgMWe74IL0vgPMJhKiTMQxvCXcRhWrYZj7MRG3LuFqm/s7n+9F7JMVusyVH6E45k7c/q4J13OuXU'
        b'FTKmRzSmSziGrf4gG8ps708ERkZs2ThT5ZkCYGIStU8YFjmTxDH5LvczKe0czUzGuBhkGorpjGkojC0RlJRUkYMVnMwNIbcVOMn9ELYdZtGd3pHQ7T0Ci1z2QIPW9Osi'
        b'SZdQ8t9tUKR5TDgpozUVz2qKyrop+Hbu4E1J7PZOGmhK8XV6CPNTmnIOGBk2XRAt5DzGsEc9eSF5cCaYhPWaUYw5vy/JH/QEIsUlDBJLSgh54jvZp9SPnSVj3kC/PbLH'
        b'bYC34T5ULbDqQ3JbTch6ChiElwUEt8xontE27OSo9lHXA4Z/j/nReMqVxjN9wWFHAvYHdISdl52SXQ8eh/mWZxpz51k9bl6JYrdOT2WSpgEQaW4JRVZPoYBqawogtwTC'
        b'UtsHpgC/oBuiiC5hxH+XaFebHOv6mTHPpNk51tOP3C7CSTRqxuhm91+r5humFcaHnDHPnltzrHuW3JJviWuqzfUclCeT75MSmfNsiTOw2unwDOFBVnmshAcb8SrH6DlH'
        b'yFTk99hpkYN3pM5YwZ/TlVKLu1oO4RFTxYOtiJpKMlFHVDt3gEdT4GI1Sx0Y61lq6gIsfhTl5Vbih96vJLwunu2AQfg2qzO1FvcQuyfVWo7M2j+rW5TQJUx4vIPMI0gO'
        b'Knpy9zw+equfRkhE9LN1txD9NGIdqbwrYGWnH/HPbU3vfhZb/kUGz8I75jkHr4IMXrRm1QsMmFZfZo0XyP0GMoHWDjrRzd0fYex+ybMHgHLI+md1P1sTi+6nEVvI5HFn'
        b'u98nwMAnZxy16rtF0V3C6KcMADnx9KmKjA11gTJnDHmihLN0THrOYaBnonD7nfNqdJkY7qvIOQ6qcovJxB9sbAYF9XiE5uurrEaI3m8j3ZIAHhd9t/0kXR6S/ytzCgPQ'
        b'Hc8aVLbyFoNKIwyEvhqeLkguPGsEhxqRzU+fYBaOYk8Zf4tULzINY9hp+PxD7YAhgUavKlcvxD3mZu4xc9wewoiIH8xjaMdf3Osfc90/poPfoe32H4UVLr+gluTm5DZ+'
        b'j190l0f0HX8xETltnj3+ssb0W37BrWFEyev2G9HlMeL/7RBYxD5lCCxin3MIKHqIeeExcMQ6RlVNjYYdBHfzIAxEHiQT71mjoOv2TxkYBc8eP1mXh8w0CmE9/jH/n42C'
        b'lab5PKmefxT6mbAXHQQbeiC1Nc8j98cI19g3KNcwmxK+MXUWdVwt5D3WWZLn7ayXzAYy+aBeZJgdmhv6/GkphA4hQ4k7bzDzojEdTRH7tBQJHGMHCzBd4v7BAp9CtjZr'
        b'3CYY6PZ+/qLKmioV2SA7X6GuLldZGpOMHpjmQbAvKWHLJed2m8fBFNVJZgE5aOZps2Bxt/+4xvTbmNBDj0Tuj2xTdfuRMw//FB7dVn5ybvvcC2Hd4eOue4TiyeA/pHUY'
        b'sX53+yeR8MiT89vn4zmEdTP/MVht8xzzlEPqiXXl6Uhe8gSatmbZeU83DtHvUMyxokp6/xZhy77GrsCCVteytHmpYV5b4snR7aO7RSO7hCN/VuWH8X+ZytfWaK0qT++v'
        b'EHLsGFRTMk+pAosqvmRO8YRKMeanz1QziPtlgTWxPqX6ijLr6tN7SMjQ39z3rylZSttT06Y7uax9WbdodJdw9C+lBJIqa5Y/o5rqap1VNen9rzjGoyZpNX0NiUQsNL3a'
        b'JRz6SyqoT6+bHRViCvawUguxRmI+sFJQ/ckxkc0zup9gkDDTBdnsS3ctMLNBEs5d7kghtbkxBYz1PoICTgHXGk5bqqdmaz5ncMoadF2AUygwM2zus1km7Sge2eQHHg6h'
        b'3rXq6jni2ppFrH9uXCzrl6+vra0hh3c/5MTK+pk4zFg9TWTab7tAr6jWqZeqWIJlT0Hqt8ElzVHrtP1c1eLaR6TbwElIVp+hx+NBa2A1HsaYX1tgjD53X8OU7aOoF3tm'
        b't29Wl0fWLS9y/KuybdLh+T2Bid1ewxq5Rrxv1KzT/g9z7wEQ1ZX9Ab+p1AGUMsBQhiYzMDMgiAUrVTo4NDuMMCgJAk5BiSW2KIoFO9iA2ECNYkdN1Nyb7CbZ7AYEF8Im'
        b'G7Ml2b4YjWbdku/e+940GNTE/L/vM+HNe/fdd++5/Zx7f+ecDt8ez+nW+X7UQTCkkcaas8kPjeLmD3ASMnIGOCn5yQOc1ETlACctZ84AJ11ZOMDJnzm7HfP7f8YVKY2y'
        b'pvWoYbHoUmkrqnRoaGpc8bPTEFiWk7qsTF2iK6+hPVwifqtCpdUV0UCTAW6RXlOhmYVJKsQXk/6kcYoYsDWepzkQZAgNv6XhQuRcMhdfyEqI8cgaYsNzMb4Qr4rV+IK3'
        b'zDXL8WUlvryOL3h3QLMFX3bgyy58wdKNphFfDuNLK74QuxpYSVZzDl8u4ssVfOnEl5v48j5JCpNN9DFd/+/0Mem+haXj4UqZzFmtDYu5YJUqLS4vrZXJ5wpcBu0pr8i6'
        b'1Pv+wV2OPv2+/nVZ/b4B6CLyr8vod51Vl9gvSkJ3gaFdjv6/E7g1JbUGtS7uEimuu/YKpj5huwqiBil0wfqG0wbx44Mwyt33UxcJrfHonsSqS2JULMP73cZiFctoomGJ'
        b'Q6YMslkeOaxHPI6nEutd2lNOwn6B5xN2iMDvIYUvKFkvfBEOctHjgywWuh1AZJT0CgKxtmPEIIUuOEYQEw2HzUDRPB6wuYJxxHfHIL577Ggn8P3WgyXIZn3DZwmmf8Nn'
        b'C8K+sWULwh/bcgXh3ziyBFJT2Le2LIHkWz5HMO4bexZ6NNwpHqNKG4cjhz/m8wUTH7uYLjaCad+OZgliv+Uzl2n4Eoov0id8nmDcEwpdaOVLfN6eM8dVC7fB7bTepa3n'
        b'ZCFbr80dhu/G/x6uYRs8l1rTuyS+JLDTNy72S1dhy/j64AopJU/JH+LrwwaF2pqF2pp5AOEP8fVBewDhD/H1QXsA4Q/x9UF7AOEP8fVBewDhD/H1QXsAMYU6mXkA4Zvp'
        b'duJQIQr1NAulPXt4oVBvs9BRJFSEQn3MQmnPHb4o1M8slPbc4Y9CxWahbiQ0AIUGmoXSHjiCUGiwWagHCQ1BoWPMQoUkNBSFSsxCPUmoFIWGmYV6kdBwFCozC/UmoXIU'
        b'qjALFZHQCBQaaRbqQ0LHotAos1BfEhqNQseZhfqR0BgUOt4slNYdncDojk7EuqPKSegaqIzFWqPKybrgAkoXopxCOJ+pA87YSk2eyZpd+T2UkgqLUfYGo29mbxnnI+gV'
        b'1p4gqholqkq8ui5SM2p1unKCLTQoXBCHFwaFO6xzQYMA1aX2DJDRUs8Cb82a2dYrxuu3irakU1pVosc7bsbU7Ks0BjRkuY4+RaejG7CFCXGZeYnMV8XmWn+pZYwCiEq8'
        b'iJzto89oaKa5XT8ZnbSBdkbLVKdR4wLaq7REYRVnTFQ5atDXqooKsR4LYBW1mAOxMBJob8EOYm7GH3NbBznYazjmtoyirBONmFhImetW5tqmsZ7Fic038lbWkRZGPoyj'
        b'RBNLpVGwJU9ciyeexRPf4snG4snW4snO4sm4y20OsUXhDhaxHC2eBBZPTsYnG/TkbPHOxeJplMXTaIsnV4snN4snd4snD4snocWTp8WTl8WTt8WTyOLJx+LJ1+LJz+LJ'
        b'3/jEQU9iw9NCXGcBFjEDDU8F7JyZ1LB/hrp2oZJfZzYmkgq4OanDYyq5hl5h1CB2ICgrbgHX4oiJmxk2Qgq8oSmUujEpUDlpw+NjJEcBF1+jONXc+ZmG8MJxQzd0GF3m'
        b'bGNOfESTVV3m+bNMqRTwxjE9259KX4cBUH5Urh0StDg5PtSwf7k2w3Ll4FxnYYQQh0gVtppbKKOnMfRcN2w2fPbcl5U8wCoaYBcVPQ0Z+uUSFVZaM+m5EU1d+rRZOuCo'
        b'xLrySxklXD4NjaadtHGwKT9ekV6t02Db7LRdnQFn2h200W4YsXVCG0EhFk6IERRiGAXbOhlwGmIa0KaIxqijFKv1muoqrRplQTh3GwJO06kG+EVLtYtJ1q9im2y8IjX9'
        b'Qyy0CQyfFRHvlzZFJUswfpu4LVTp9FokPmjUGBSlqsBeDirLqhDFpEbLy8pLiBI/khjohcH4WrVUZyrQgFtRRVWJqmKIPVxblBNGmWsRfWQiR8mQX9pL5YBP0ZB6R4I7'
        b'mrCZuDx0v1Q7YI+I1Oi02AQBEYAGbFDj4IZB4r6heeiWsNGqdfiF1J5WicCTyQD/1eWIBK2Z2VwrciLN0OMp0aTrYnLzOSAcQqbBFervscB4nEUExi+EokZdS9yR5V2K'
        b'aT3+04guysIe76Iut6LPhL4Y4tVS0iMMa+BiaCx3r63Rfwdx0dEfGo79dwQbQhn/HRZxPhWHHrOzcPZh+PUPIh5QxYHm3lGZQOI0xMEQaPkTIsXfBxqiMj/YCcheJ0Mc'
        b'A2HBEvwbYHyWReJfKUPbfb8gkk1wCB3LEDtIempK65ST03alNyTiffnpTdPbovtEEXdFEf3+gS15R15r4vZ7+Tb7N/m3ufV5KXq8FP1h8vOyM7Ib3C7/qY3cz7C2jcHq'
        b'pKxLntdVOO+efF6P3/wuz/mfuYkaE9t4v3ZTPHCmgqMeuFCegS3Bp2Stsg5+n3DCXeGELpcJXcIJJt+wP9r2o5SlwXrwI6mJew7tIQZ9cQ+OhQljk8n/KXlEs6TyVZM5'
        b'QRltxFhXxdhjxOqzpYg3Ki+rRZyQGbfyEgrkZDftJDWy+jgL9WkvRLSZA44xlj5LsPrH0iqdyTgk8dz2Iy1XEnrOPYceH0yPyWylpYuS4eRgF3Iv4Qnk0nOo8bdSO+bu'
        b'SYaQw7iB+9F2PZ/pmQTTE4jpMVnhklrxSPITkkQa7N3nkBRiSdJv4sS09z+tfhFjUIaYysB0MEpYjEOJZ9JLdJnohAgmGwsr1egzLHQQO/hWXFQoxLmmsLJyNc6QkRRQ'
        b'6iiCSWXL5DNVHMbUX5gM3ZbryK/BwUgYAReH0d46wl6iXe8+pxJluBJ7jZU4brjN8xH6f1x8YVwEuiS9xChAhP1+5PmO0BdhSd8UC1O32OK4epGl0duhdCYokxIjEpPi'
        b'817K6q3mD8+hM4pjbgxj/sH5NL1K0pvMeD5GEdBguGOIBpxCnEhMp9P6ehXLVbVaxuyruFK9WIX3Vl+qtv/4nFKMtxxSYYYhZdDmMysIw+2JJbkFhXNfrg989RyqJlnO'
        b'haFkUauqehWL17SxWyR1V1dXYcNRiPHW0+Zxf/zMg2j5+jkkTcEkubINJDnnGW36/PisGQ7gT8/JejrO2pdlMRMvRXOMarHabBhUL6nVYk1PcU5cahaakypeoj7aWZo/'
        b'P4eoeCtNZCKmomqxJS1iSboyKfnles1fnkNSkiVJZF5XV5bKdVVy9GNiiMSSpB9PC1M9f30OLSmWtPhaNfQslmT+eEKYzvO35xCSbskpmpxzBdBKw0gwqsT2Z5jBTdvq'
        b'zslX5rxcW/39OWRlWQ6n0WSWJ/IjY2LnpdxRDT4n91mWrRM2dM7G0ijW08L3kvjs7PTUrJl5SbN/7IrCTDEPnkNVHqaKbayTfw6lylJ2VoiT0Sw4U43orCQcv9a4u2nN'
        b'JzKatgtTk/Owp2OZeGZBgkyco0zNjMvKzouTiXHZ0pPmSGVE3SkZd84lTJojpZaYnYnGNp1cclxmasYc+j43P978MU8Zl5Ubl5CXmk3iohzIjuvyci3WQa+uUGFXIbRZ'
        b'8pcZBd88p2rnWo4CxV1fWofyaaDZgkdvRdBDQEUmDJUW1fPL0PWP59C1wHIYjB/a5PROikIcZzL/lZqVnI0aLzFrJl4Fced8qU75z+dQWIwpDDAuPsI8wnHR2zqoU5Ti'
        b'3lj1I0crA+V+/BwSSoasf4yxemIVjyZAbdrTN5dnX6ZeHj6HqDLLwepL14thYsdmH8T4IMLKQmx0D3SaZYSVWyHFuDl5ZWR1SzPNngCjZo81xNoISmmm72kTlSN9X83K'
        b'ZQdQhS7W4BjoCytKlYYN2QKq0jym/fCYxhL4MOW0Esd6DVXynv0+RzA8DMV0Gh5q2Fb2f6ZU8HSykjZlgY+AjHw8LXaYDpqsiyUKqa3mS9yF2fgyxPEt2aMlzrS4uNdx'
        b'zLzjkh1EXJdGlL/DYrXOuAUsGrpBZPayHH2mxWCO79ZSWCFq9YHVDavxbtnEpol9oqldoqltbue92r06Eq+lXEjpkkztE6V1idLuuP3c612vhsRPg8PbEq9JL0g7827P'
        b'vz6/JzjN6DWPJDQ25prvBd9GbrOgSdDrqeh38zyQuSuzzy262y26I7FvXHL3uORet5lD3OxZH5K0GKVkhl8evSM+fPBhaMfwPTGDYg6upofEIw7Wy3kGFmshNfIEYOyN'
        b'o0ZGlhqOWsyRogpqiIaElK35DpPLxVvPVpQ7bZlN6SJrBaLf1OAGpDH8/a7CPtdg9H+XazBR5ZV1i2Q9BIj8mVDUGL9nRYPzM+p39ouUWDiybqF1R6ULmbKSwxJDeXmk'
        b'71nXZq1QV6LyWtn2Ji9W4uIGjVzcPlFUtyiqyy3qU6EnDX4SY4S3aWufHmBkMGHhneysksVF84RlOBjB07rmW3zBHCphyehzEiySEgmDPkX5At9hNpIIQppH+IJ5fiKs'
        b'0ccreCODyNeEBycsCFlNyaKvuY8v+NyFSJZZ0jEjwqzIYQABRg04DTnQIVMAmTFMkwWHxcwTAwLL8xw+c5xjw/DyGnxKOMBnjnJ49EkOlxzkcPE5DnFCMOBocYjDZ85w'
        b'uOQ8xmnIaY2D+WENnznlsTUd8tAHLE6WhziaqWxm6GoS8V0KvpjwVPxn46kIknmGGQKqj8VcMGJBi1diBgFlJ3B54qEQ+AxS6PKglEX5jSGG35WPeGy/PFZdlsmu/BRs'
        b'MX7as23Pm8VhbK5PxzbX42jT8yRokM11j3jE4wsjUZgTbSC+3y0NW4fPYNVlomhMECbBN48OwubopYNslvukRzyOR2xd8gNbQwYzcAbxJtv2iIqpmIrphAryYb9bCLZj'
        b'H0rM2DPgLEyXexwNzhr+GRMyHodMNA+JxiExJMQnmBjSx0blfSbVZZgyk+DMwkhmzFeYRrd42tg+qeBBNsd9FusRj+enxHXsSImCPnVBq8FEFFEUW5duSiwDJ5ZFW+Bn'
        b'QGRyDCKLICAyK4VhGhAT6hdTl/UtbaWfJfD5hs8RiJ/YcwRegxS60Dgs4trlrfRVDjWCakdpGtwWnpWhwNZ34E4OaAYXqLAlPNBRCDYMc0WK/z08SmFEhnVYlpDScRdg'
        b'zCtHaJzmdXwSwjULsSEhPLMQWyUffWtXwIlmYbBWha3OHhvD1zlg4+nRbAzVQmGO5L09uRcUcNG9A7l3UjrqnAsonYtSQJhlpwHXIVNnRrlWV74OlcHCNxbbMO3ThkUK'
        b'XUwsWKG40rhAFEZWGqd1BWbUTOgQ4yLGJdPfgF1RqZ7BeNph7Q1VRbmudiBw6DkrJqfIHMijNegtzmITsKchEVtDGgYNRrGZoWgfK6karUZvxIuEF71I+Abste8PkO51'
        b'oi9jJCavpj/+DMKPPfJxnFXKDEdyW7FAsIKirIDvf6DoUTQyCRpsM6Ee57TypXJi9riLn5PTtpFzMnJTCpLTi6oSmNybJ+B1QGWdALxQjNgPCG+0g2NUJMUMUCKtptIj'
        b'jOxyifwpYfiIOELjCEB8spoN48IZSglXswsTiiEDBm2BPpGiW6ToEUZ0uUS8GEu88Xks8Qg1RbPFe3EbxhkEVQtDQUa9FQ/Ws5XSFg+FoFEWRnWsKZhZ7QXEtYGMMQ1k'
        b'XU61ImGSrwg/Xii2JmsSo0Q0hSaYmRlIDqXqOPyrHOfhYSalWH807ZMuwHkqN9+QWYoNdy8y2WEPHVL1oZbRS6vUtJlq2pgQcXhhMPVIuKUsJBfOZjEzJOHYNIvwHVbS'
        b'oBUVcPdDvF11tbqy1GBGyMEsDzrqiOp3HFVp6TCWm3QQ9OIA7pyvUEznDGgJb3u9Tzj9rnD6Z95BXcG5Pd55XW55/a5+fa5B3a5BLbpTta21va6R/aIxfaLwblE4rZjT'
        b'K5rSLwo6tboV3Y0jqg15Pd75XW75/S5ufS5B3S5BfS5h3S5hbZN/7TLhGYMTI/FMg3OoPoy5TY5hw3AmriQva6Uk4kgLLqeAMg3CPbVdLuLhpPANpJQZSGFjUlyofJae'
        b'raD07GRPilo26kVFpCx2ujeNRtOzq830rfVsfxJSzswxbE0mbkMHk/A/wNJZEf15uiod4rOtlpO8OmaQGOlyXkjsEU26kNi2rDmlKaU563DWhcRu0aQeYWyXS+y/7oom'
        b'kdW3zk9uK+UOOFku3GQRomUfvEhkSUdZlV9MOh2k/5q6ronVJ5y/js00kuY1S/afNyL7TzryDBPjv4DNXDC/o8VNQBj/b/hcgRSxnW4+3T7RPa7j6hI/Ffp3iyf3CKfU'
        b'pZjdfsNlCcZiAH8k1hnwecy3EUzEGP+AJ+hx8kMKXWg+ErvkguvABpUVRnI0PAsvwS0yBYtKhG/ZZMDLyyy4SQMm9GEwPjH0ts5NKjlKLvrjKflKG/SHeMQIno6rtFPa'
        b'o3cOSkelQOmkdFa6KEcpRytdlW5Kd6WHUqj0VHqhuKOU3kqR0kfpq/RT+kcIdLwCTgEfcZK0kyA+4iv5BaMLXAu8o3kYAI/CbBbYIq400IwrtSMhNBA+xEwhAIeOQaGh'
        b'ZqEOJFSCQqVmoY4kNAyFhpuFCkioDIXKzUKdSKgChUaYhTqT0EgUOtYs1AVRb4dKE0UoH0XiTI2gFowyYYnjWVxKNwrFc0Xxokm80agGWMpx5N6V3MeQezflNMZBFPaX'
        b'QHuExY6inAtcCkaRWnIrcC/wKBAWeBZ4RbsrxzOOjNw9qLm2xFGUUDnB4ChKOR3nieqVg4H1Fu6sPIzx7ZSx5vERJZOHxBUqp+g8C7B7qIlkYpsx4IhHswGvXn4Kde4B'
        b'9sz4AVbOADs1aYCdlDvAyka3eQPshJQBdmL6ACcxHV1mxuMIuQOc1Nz0AXaKcoCTokQ3GakDnISU5AF2VvYAJysbheRkDHByMrIG2EoUosxGN7lJA5zcJPQqYS6KPBd/'
        b'nq/5gEUyRp/PTM0Zpt1KQOt4oZjCNrqzx3aVKSTGcJUU48ye/xM6s0dMzzBBDfN75qZ/OcRqb9Qk0IDHqg5uyVbA7ZnY9WsK6Jhr9PlKXLAqUtEFbsmQpWbOSkFDOA0b'
        b'hAXtXGoaXO8MLpfB4+W3d7lytRNRit+ffP/S6y2q8mLbMvuywUUpX6qKG1R1qtK168V8V8nkDWM32Y3xvvPRWtb6puKwfV4TeyihgjfPb5KUQ4yoKuC2JQ6gXZZisLA6'
        b'Ct7g5IMO8FY22ECsyvqBQ6AN1mfDrYgMbK39EHsluLQCHE4ihlrDQOuroB7shDvT5WAn2GlDOYBzsNWDDTdHwT1IprI2XeJmGgIwdTPvWgZ0KR5rWuwkgrjg9KXchI2y'
        b'HtcxZMXP7vHO6XLLMUeWGizj0OuvjQkCq/kfntitmBwl2pGMV0oTMZpWlPFVjpnL7XJfFssfe6L0/6GeKPfzx1AnHcZySsyZQcYjtO1DvE7R5r+xR2gVV8VT8VU2qMPa'
        b'ow6LZwMbNGfimYBv9AxNd2DbXAezDmyHOrCtWQe2s+iqttPtSAceFmrmQ8WyA1vzfeyrH48e1owLSs/Ior32zQLXV8E6uVwxKyWN9v6LO1J+znKwMQW0cSi4o9oBNsB2'
        b'0KKfij6FZ8AteML0NerZ2fICxjR1GtxeC8+hlWtneqEEbim0RYOES4Hr4LyDAO4BG29kaX6F9yb1uBHHgT3wuhY06wUCg1XsZTlkMYwFb0+B9T7wHTNHxpa2sG2oObk2'
        b'tfCkjLgTkY6B+9NTM9NlcLsU7EHd2yGLDU/KwW19AKb4CLwAWsJT4Da7EpTYnujISLCxOJ0KBFc44JYfPEG8IcPb4K3i8Cxs7nh7Zr6Zve2FKolCLoF1EWHYBXOV1BZe'
        b'AtfgIaKF55MMiM+Kg6WpGRF8ii9kO+nhPj1W6QBnwTpwPRy026+RpcjRO3CDPT7Oj7yDNyfBm+F0NduAY2GU7TK2faJMPwG/O6eGR3KZvCUKcGCVIfNZErhTBrfkSIxE'
        b'2mBPKHvsCxfA43rc7RVjx+RmVaDBIKEk4GoxqeXFFVVacE1ZAy9yKRZoouDOIrCROMAWzcX+fOF2mQLuwD5eqlGcPMloeBluh/UyWWZ+CtyRbTBFbmhvFgWPcxwhmihg'
        b'G3GPEjoFtKfT76RwawYqqetMcFbEgUfiUT546vGEh2XGigVr51CUQzob7A+B50ljx4A6cCUXe3ZBFdmeJ3GB2431PYtkTlHZLjbVofASKRDYAt+AB+GeWRSa0q5R1GtU'
        b'pp+vHk9iAVo3xCtdWF4DL4Mty+FFHZ8SiBaDi2zQNAqcJbUL3oLNEVr0CvVYWYEEbAfX0+So26DJmc7LVLmoJKiDdtpTpaBTj42PwT38ZeG4blB11UfAnbkSCZpt6yKy'
        b'8j3ANrqu6K4J1oJ2OwqcCdBjDZpVoInnAI7AW/AqvKyF15aB7cs1jsvgVYoSRnPARo1/lh7r5ICLoAXcgPWow2fKFajCedRosG+uioMnYnBYj0cy33GJdhkP3J6HPS1T'
        b'YGsp2ERmyXLX/UVcLT596Pm1z5G8T7JBpFultERUk5DYOD0n+GcrxjZ4OgX+j7Uw4+Ct0gczJu66b3e99tvsa6K/HjvHe2/B1fOr//vbJ+88uSH8X2bLb0Pvx+nzAv6l'
        b'vb1mFy/0ePrJy2sTd8968N+4d123zf6kbqLXlNIWfsLaWRtk9oGzLnklLTnf/pl+ZX6Bn8LxvcuHPqF27L09Y/HRC6ci9kV/qOUHPt1QX/Bhkvt6m4QzX275fdOTmNul'
        b'2ec3ZrQtbF5+6duFX42vWTGY4Xwo1+HqtJBXz8hDv593am/xke9YH89fubB7b+Vbe5w/W3Bq743ZanHE5YP5vEXdl0t0VdNK6nLDEnp+MfvBJ78JEejrmqWh39iu+N9X'
        b'O49+GtGt+VOdjlvz99h/ngzN+vuf3rrk989vf3Mn7OJe1bnUXa++/s/Z//ju6t4nndUDe0MDL0xSnrxUNmvnve1pn6aF/z7j3QWt9ys2/0ZzPvvat97/Ubr/V/raB98e'
        b'aBq4f7Op9FTXhI9rvX/30a9PfZ0w/zcrb35l9+YfLyxc+VC96Hd7w3o/E9eW1cT9/cj95WddstzaRFfe2/LhpN/czrEJWv7arF39M/UzbZwWb775/m9PT3/98pSZbmEb'
        b'/9FysutEcpzi0lmnBZ89dI+/95fsG5P9w3zK2k51ixMmiOTn2pf/tls7VfiXVf6Fe+aNXvMfKsOj1EVVLw2k3XG/HQj2Dl3zYTts4KA+jmYowhdUwZugAw1msCMiS56S'
        b'AK5gY/Ln2fAEPAlPkYUf1pfB09hhuArcHGKgHbbnkZxAM7ziBOqXOwnsNfCKFl7VCfjYp8EWt2WcXLBlIbFmvxTuhpvT40TEUUwNKw5siCbW4Tm2YC+sz0gbBa7AbRyK'
        b'A2+xwKGKScRZuGIG3IeIQ1yTFNalvAI2YerOseGxSriPePexhRumgfqMJOcaeLUaXtGjfB2E7CXBtCV8cAFNGjfD5VGTJSlyxs4/aIfbaUfkB3KmIg5sNrgoC5MqyMSJ'
        b'ZiIxd+FoeJB2PdOO1oL1qOCgVZHJp9i1rCmuoI3QLAGdHDTKt8Kd1WpMNHcSC1xYvpS4wwFnJq5Mfx2+jaY69NFCVgQ4Z/8oAg9zxNtt0NY4LtPDa85gK9jmbCuwhx3O'
        b'qAU21aAhD68uX4boz+TywXW4SUAy0oGtk8Ll8Ph0uD1jLIviz2HBs/bw5iM8pF+PFsF6m1Ep4C2KYq9mJRcvIT6A5PA0ml4QH1cPzqZkorlwpyItEy3SJ6O9UesuDxES'
        b'bs+FrcJxdqB1GFU+vFWE+LkZbLhfN510i9WlOuwJIB1cjTdNNh4ZXAHYAE6S2nEqAptBfQQ4JcY9jEfxi9mBNZl0j2mfjOaj+ghmooSn4QUe5ZDNRm15GWx6hPcCwPpC'
        b'2IDYyXrYjGoe7MjGHAHKBy3kfMofnuDCS3FwG2mnUBVoQvHqwEkSE3dTLuWE+I5E33S6lffCq3YoO3jRV46qCdVSKlsI37R7FEh3zU54lviblyuyMrLBdrgTRYH7ZnjD'
        b'w9xlk0AT6UdVK4Wgvgq0Z5tWMadcTma+N3krl8SgylLIESOT7h/KQX1wKxuegp155G0xPAKOovdpslTEohTHU7YT2YvA2/A0IQDum6LEL+XR+DWoy6bTT0X9MUzCg+s4'
        b'GaTObEOTQX2tIjtLBrZEMKsGD9XENR4Pbl31CE//IahStxE6GD6Hi6b/c2g924r6IvX6IywloEq6jHiZemdL2WM+C2wBOyMsNw7C0RjdHmSPauhwxCO8zqYnORi/BLsn'
        b'Gj4mn6LBUJch5VMZlA24OI9Hhn1+FbyIm7kIdfYdYAsqWUom3MFHQicH3k6Gp/4PvTQNt0JBjmnchwgX9PkMkS6wPSkkXTzQ+WLNqdC2CX3C6LvCaCJiMG477wv9sO3H'
        b'PqHkrlBC9gyTe7xndrnN/FroTxyBRnT7R/T5R3f7R3fMvJZxIePO6HvjEu+oe/wzfpB70K+Fvv3+oW0x3f6RfX5ZXX5ZHaXXll5Yeif13visPr+SLvS/sqRhJjYxvKBp'
        b'QZ+vottX0bb8/Kr2VZ3x9yKm3xH2+KY2JN/38m32bfLt8wrr9gprG9/jFdXA/0LoS3KbcWf8PYMtl37/EGwvqi20I6rHf3yDI2OHeM+qBm6/q7CxpmXxkdd7XRWfewf3'
        b'5Bb2zCnqCinu8VZ1uanuu3r1uQZ3uwa35Pe5ht91DUeFTr+W3pFOskjr8U7vcku/7xOITc61rOzxiW6w+8LVp0V4yqfVp23RvYCxnV69AfEo3d+EhLflnZ/TPqej9p48'
        b'bpDDGpOArbiLErG9ZHd05VNu/i0yRETH8msrr63sWElySLxTcy8ks8c7q8st62tXv5bJveMzeoMymAJOvheS1eOd3eWWfd81oGV+r+tYlIxEhr1THFvVFzqhO3RCX+jU'
        b'7tCpPaHTGxLvuQXfDw1vSOxFv/4hRPcvUNImuhcYg+6djXqE9BuDRh+jr0hbej40n0QJCj0V2xp7alrrtL6gCd1BE3qCJuHI4n5xKInMJMHoCI4JpbUWgyPoFM2cuTKH'
        b'g0SnMYAmSIrV+foCJ3UHTuoM7gmc3sDd72wm5zozloAMOCsu3uzXYNtZmrl4q9mhRKUzas3ytSVL1EvVL+yDA4+hYuafhScOspuKzTfdxHJyPHr6HjvH1SJBOZv1hMLX'
        b'QXL9AQKzFsudx/jR1CWHaZyXwFRjtV5SzJEORy3nA8Op6H8sAK4/On/Nr55xUtmF3v3PEkgrwXBMo+kImnAx46BBLNGoVaXyqsqKWulLqDyW0dXiUMSoYhSVlz6LQBbX'
        b'AoEsv+tLG7x9KrOmzlGuNVFvTu7LgOK/fAaiFVPIRRSaqQL55RE9DqzFYVStellK6GNnrCqu11WVlT2LGhuuRYNGEAUBvU6OPhNjLXmTpgmmkGi8vjR5BAAw4Tk9zR4T'
        b'ZkIjhxE0cnkZAz9eisHjqPXUldg+SOlPQxOqMscisxnnWeQJMHmRxnojWh4YIb0Yu3YzqnD9FA2pET+nQ7lgUkzQ8dCR3URbEmSel/GIupiij6ixgaRoNrNjR87njDt2'
        b'LBEi2GzHjmWxN0dNZ5Edu2Ghxh27siE7dla9zVkz/MilqWMRD81UNMvok5nzE/pkLpOyv5yBMrdPNvc6bIky1oq1S6r0FaX4hBrNdsQfvVi1WIWxyfY6xrCPOKFCrcIa'
        b'F+JEYrECdwzGJTFRmWLczDMaB+Vae8bbfHFxnkavRktWufnIM8wNqM8b4IjEm6A9rZlSa67wQeunGJNLVlVocXpYfw8F0OoWWvsqPJZKsH2FUtQ5llardOWLyjFYSCHO'
        b'r8YRayYoJipWEBrCXq2q1FWh6b3k1TD7avQVnkSXq7QWbqENhjqw1+chDgVZVpqYk1X+m4scHvGwErrk8SVVRbFtmW3xnc1HuR85Hv4zNWY865HyoZRFe4G9BtfDM7QA'
        b'ZmLLdWADzZnzQtEAcTIMEOYYl1u2WK0bCLZYL7UlFUWkGGjlxPWqnabAsQg7jRlxvFlfI6Z8xNjWQZeb+Z48A7GyZDzIcUCx4eRY81c8IfwNXdxQuBb3sH+tpb5Vi1ms'
        b'0T90830XP4BqdZBxrJk3puiDczbje5NXgLp8NIcZrOxc7k/qdfMFzoeyyrvcwzhaDGM58o/gS6pK1JI5pbZlUapSakOx08DPpvA9bRfllN3PsKGSj3LU1DnUrGIKy3bT'
        b'wYbRcP3QhqVbtfY1KWcoU4fzN5qD5JZpX6iFtUwLM9ZEH6wSU6HhbTHHXm1I3J9t1sSM2V+HkU5ccJnND1we4Ob+BhsVMDQ3dum2EjW31w/x5oZ3RchOZ3GeSJyZTvwO'
        b'c51Z4BS4lkh2f/PyY7NgW3p4Fn4RzQKX4DnQUr43qo6lxQcb//REdf5KcUOZbUlUmeMil8UffCmhLsLG7U3rPd+d8jPx3WMnIzeJv4pMXj1Gzf+VjjrxRxt2828MvXqk'
        b'Qy4TtsXOWKcDHtbrmtSumK7dfq7tt4vEdqPCH3uwRkXd9/Rr4baUtZV2maxpGnK2VsUWOWse4gp+hC6uhgpGGTwuQRVs90Mq+O/skSwJL2LGEfFgSxkXvJ92SXnBMfSK'
        b'YBxLi/dX5ubGX3rrBmpRehQ5Ft/hjtnmMrdpXbQvNfMBu3krCw0ffLwH2/3A9WE7I2AjPPnMvZG9MinbrMrZZEiZ4eyGnmcSgB1pYiEzgJIDKE+RFYwd3bI8azOlCWxi'
        b'NoAIcuU7dAk2my8fJwX8sPlSs4EaqX2LKQuG4f+idYceQFpd6/LK4V4Jh9TfxtOtaK37sKSYnhE5lN081pv9Tgbk4ZBVjEYeDt0EoiGHpEnsmCbJQE3i8wOXK4IZ+jdK'
        b'JtR8uUr/odU/8vD6f6H6X4SbRIOLG/UmS4u9rwTF5GJWg8AMijdRY/iOLne2SsvYx25/2voaARls7+C4VORIOWQnFJwAbUWwXoaYj414g5M7gwWuwDfh7Ufk3HJbuGr4'
        b'+DMbe2OpoaMPbAJrScqr/EEn8SBbC29myvmULbzJBrvgiVornYAAdYftBBKErvnU+0iJO4EBpdvnM77bZ3yPz0Qze+ov3jcIsoyFpqow874x60f1DXP8gI+hbxzHfcPd'
        b'Kn4AI4icMHbfiCHCmCCMKTBDEhV4F9gUiAo4iPnxKfAt8Iv2MeILBD8hvmDxC+ALJpFVumbJonRYz5yJw054hO2k9CennHla2OGggVfgFWd8EEoOaWs9XcBxNrwBzo/V'
        b'YwUCZ9AuI2e0KahLZIOzsgKJlUPaEnjJcE4LN61wAFfmwS0kc3gUHvXQ4vPVRaUUbKDAtsXgpOYEqn1y+J4LbsNN+JyYS5WDdyh4jAL7J4I3SM6gARyEG8AVcIDkPyRb'
        b'2KHTwMu5KeH4aIg+IG4AjXarwSZ4Wk+fSNVywW7YHg0boiO5FAs2U3CtBFzVY8S6J7iKUjFDNBjM987KKYT7ou0mpOXaUPmwkQ+vvAbO6nHvhHWF8GyRUzS6HUuNBW/C'
        b'HfQJ+Fpb+CZ4G+6De1CnjKAiYDs8qE/EHxwrAnvTjQnDuhQZhmZsj0jLl8AtKMdciRTuLExJzcRH/pmoesFVZY4IvIEBCpWCBajsF/XxJCFwHTZjMJNZ5GkBUtwkaBRv'
        b'ichm6sQcl4Fb4gy46QgvgrpoPeYnwA1wNEKAPtglAGsjbXlwbT48yoc78gTJo71tpyjBTfAOaq7zSYtXgDbYYFcmXGYP3+YvtwVb7bIdQQfcAI9HwndWSv1h3WQFPMgH'
        b'BxKk4NK0cbDJEzTCm2C3PhdlwwJ7PHlwHVwnoMbackBHfhjcAi7Ohfv4YAvcDPaFIT7gHbgT7MgTla9BGa0VgXdeCRSBa2AbeANcLVsJN3LGShAh2/3hhUTXTPBGpAb3'
        b'aX0MuqRmj4P1meBsDqxLRQWNgFtyCErGcPifAt5KycrMnDwNw0PAOXjNocSzWo+tr4PLBeMxWU12lNgR3RQsfBXsBmfhDdjKGgvWwxOTo1EN7ylGs+hZeDA/FB6bi2hY'
        b'654H1qtB3eJYe9gCO22WgLddasHheYQYsBbuzLBGToo8jeeWN9odI8xAuxT9T4Gt8IwdvOY6J0/K0uNpcUWqB25RNCXDHakyNIRwg50FW4W23EiMpSBDQAjOp6TL0zJz'
        b'U/DxYXgq9jUfXoB69SUCajN23h0psrQMRao8DKWxVepYbhuqjyZDwG60dZAE+gTUs4eAJOB1uB1RR4btgQJwPbxiNBrbLIoNdrASeOCmHtsChafhjYrwFFRz2zLpbh2R'
        b'lipXSkC7PEqWkm+AyliCRqrxAM5RygvYFKj3coYnKuFNfTqmcN2sDIcaeJWUAXXtAgkidYdMkpIJLihxWoXV9NyDyN+ezgK7k+zB0SywY429B+owp+Eb1ER4S4AKuGsq'
        b'ohxbYQUtsGVqOj5A5IPr2ekctH51sEEdPAC36/Mw/W+jpfNAbrY0k3YGn19oBW+FZgr4Buqup1ETb0HVvW2+GJwBneB4SgC4nRIQDc5zKXgRrhsNmsBeWEeQTW7gfCJq'
        b'l0vOdrbwojO8pFumZ1FuWg7q1m9nI8GokYCUMuDp5TX2uWiOSeOgOeksbvO3CvTY2zs4C26DHelSOSr3lowsRJrExCmD+kiiykYtENuC9QvTCJgH7ICNqCxgex6qnLJ8'
        b'1OV5YSw0adaJ9Ph4fB7YXuwwHmyqcWKhrPaj+cC2lEZ7gSvx8Dysx6ezLatZEym4wxZeIdW3uBbsT8+AuxXGw1mHuWxMPbxN0F0ZcKsPbEPzXX1GmglDUAibSelgHWhb'
        b'lQ7OphlP5OE+0E5Px2/Aoz5B8DCNqeFRXD8WeDMRNurxwgv2gp3z01GfPAcOEPASOM2lHF047rBxvp4cYr8F9sMW1JelmG3JlKXiw2WSELyopsaAtbwyuDWOpIVpALfo'
        b'eResL6FNssNGNthnM4HUGtz0GjgdLgkC1wxnv46LOc7wFGgghMIj8Dq4heSXi+moeyBCuSzQXAt2kvVqPAVPwnp5FjnZ5i9IgTvZ7vDgK/SYOQPO+Ds5wnoCAuCOZ4H2'
        b'WD+6Wo6A7b7wNjiHxzKHFP3YK250bhtqwGlwHjahVMm7aSxwZjZoIXMEeBNcXRjOjFnUXdHYqFNlI5oCwB6enWgNwcqB46AhDI2ALdlZcBvYEkHqSLzcspaoLLDOBjbA'
        b'VrCfZDsT7nEKV6TKlGCzFE08dpPY4ARqqga6W21Bk+BpNGbeQv35shZesqHY8C2W3J7PbEeQ3lUUjhdmtLAjTpks7OBqLV3afa+gxC7p0Vx0AqI1vZkCu3L9yTdrIsAN'
        b'B3iVR0VoKHiFAq1qsJ3sMITBS5RWx6KWgQ7UgBTYxF5A6tR7POWAGEBUxrcpeJ4CjYiyk+RNEayL1C5nU/DNFRTcjefXQ2BHxXfff//9ViEPc0PiSL5iUmttIFW+bdVd'
        b'lnYzWp2d9sn3FaRX9cxwWTh5x8OKPTd2jjv/1R/HvOGRJuo5+UqcLSt+fcqZBZf/mPNtTlLY1PevLZwkzprfMHHQ+buk//j/TLTy96+FvvWB6vef/6vsq0MPPj77iXeR'
        b'3RcnE7/v3rvmZ7YPp2gf/831VrzcN9r2+/Ovu94Vf+zyB27NnrKOmx9I0ses+OVfBlY+/s+n0WXfFzk+/mwC1Txz9kcrPUbt//XCpbceZt7/V2SY/reiz9mfCFnZXZI/'
        b'ey8MBKlj7hz1/+C72HcvRc557ZFXzZzr6RfyOm4uzHyvst7NL3T5d8rNHRm6KM2dAuXkXxzhDfzX6UsnedDHCY4Lkr5pqD9+6/1vwO7uVQf+I7+x4/7DUUd9P/+w+OC1'
        b'2MTjQX8+MenpGx0Rtq/O+psu4Qn/1KGn7X/4U+qO8rm3I8Z8e273t4Xv/Vd+/yqvSf+vtdc2l+V9/9E3KQUZ4TPeW+T8Snvj4HW3S3/67XrfL47eWCW4WBb6r4Wh+gNf'
        b'3/i9/pb3k5ON/bu3/PU3Z8fpfz4m/F9XOy78J3FfxqF69a1ffv5v3bp/lR3m/e2fX93fvOr7Dyd+dMHn8u92FT3O+U+aY1H+Lqf8X51x/tPkZas/7Pyo4NOBZd95dD+5'
        b'7NfTLm2ed3fx3xeFgyOeKaurBgfWew+cXDr10EdPm79vnDw9QRa1+r/bPmjz3h1TFPp23MrY0c1bX/F4728ZO07c5vv+acWudZ01j7QFk7IebRnPm5DE/6S38xeTdcIL'
        b'c96fVFIwd2Oh2/cX/+D/qPqNCVf+tzS9fGrDUe+tS8MmLt31i/s1nyV09r753cl9y0Iuf95X8fXxvy8U568e3Tph3OWgbvcb5/+du6DQqy/+v98eXzMx2snt56+dfVoT'
        b'Gxe8+YZ6yqm3T3+9Pmb2w398Dhf86Yvqfy5O8piy4mD7p5ezHvf/+sivJt69klewX12Qs61ZtPJJ4q8P7N6l2LLqoaL033kHLhVsHDz7Qc/62Kpf/HtN6pq/6v4zZfn9'
        b'goxP/pi7+G2W17SemD+nBx+dUsT/1R9bL2TPLiw97/jr34d33PhuHvvD8dNsZty1+TA8L4r68NW8i5zdE9r+MGp58er/fHi0733ZXzw+rv6H0y9nvzP7knZizIzFBwqL'
        b'P9/wn3cS5NNHTZrd/E3Y2X8HOv81euGGb4vfFfr/6p8NgvOO9d/xul7buSSg6NKi//0x1y3p/Vviv77FXZ7rdOPsX0985fmUdUFJZfRvaagP/EfRH552/O6/cT+3nTa5'
        b'ufTNrqClmi+Tow5l3L3kOOHDeQ9//4VIc/CV3aKgJ3/3D/pX7xHJV9JQgjYCm2WvY2DUST8DNooBRsGGVQR1xa8YnZ4GdhpQbAngIEG3xSyDe9PdkNRiWGNy9AS0Aw7B'
        b'9aAZw+dM2Dke6CTwuXyw8RFe3pRoJrlA41+bwTEksqCpAlxh13DhGfK+Fl6ah5a/1glDlr9N8BYNgGqbPXssXG+5+sEOZ/LxCtCxAonkuUgeYLBTDL6vKZVGuW0CDfAC'
        b'ka1RvvxXChew/YoX0une4qWEhymkoI0Dt8ooym4OmpCV4Dz98qQIbA9XYLZAhlYdsAO8EcCWL48lmYK1lYvw+pxuhlVyLuBUzAHrHmGd+ILxgGCyMKuZzUgPryNWfpuU'
        b'T/mncxGP2wpvEABc7mTQHq6Qkvz56KNbDuzoYnCYkADfQrzJ+nC5AdyX+Apbjlrg4iMsTFXCwwXwtLsWbLddJoAXtRjxywDuzMF28Aof3CrNJaA3FTidG26xtY743dGp'
        b'HNACmtikXPDIArg+PRvunC3HkXBbO8xioy9uaUim8ALYjhaDS5gzvAC3yQkHnukwBQO+MpcxzZ8OztggweWoDQ1Qa0C88Ol0OkMMhEOJYvQlNQpuRmwaPD2P5BwAW3iZ'
        b'szHKbWuEHLMb6TaUczZnCXxLQ/Bj7Klgb3g22AwvypDsWU/eO8BbbHgNibI3SdeuBXvgAcKEwrVgvRkXegmsJV0hFR4vAofhPjMWAx6bSaomsSrFHEmKhJjtRIMEvDUa'
        b'biINBU8sESDyDAg818lsITwDr9PVcm2WHtQ7z4fHrWz+WCDL0Eg4TI+btzynDQcxYgTjjKjl2UmPgvFOAWp0xH4aoHfDsXVwn4ZUHh+cC2eBOtSP0sIJq8ajnOFaThXc'
        b'4UNKBxvAflckM8F1iKHbRhffoZKNFu+tsJUeJa1jwc4F8JQ5Q5QcTgqOmLINs2LgRgsectUasm2lzaEwA7kOrLdgINM9Cf0Jk1ZbYx5d4HGaeQRXwRYaUHmrRIvIMwcw'
        b'onebPOAm7mj3GLK5hiSBEwueubtmsbcGT9nag2aNnExptdPD00GdU0YqmtKUrLBXAT2tzED9/kA6EnsyqrGYg+akM+zafLheKv2/8zT1/8GF6B2Jzf8Nd3Q1BGw44DzE'
        b'OQyt7W7cbhzyluw6ruXRB6ZzAyhxcPOqplU0nLDDpnN0j/8UDMvzO7DywMqGlf3CoJZVvcLoz/wkXdKMD3SfrPxw5T3p3B6/eV2e8+5LMrrcQvqDJacyWjP6gmO6g2M6'
        b'Ft0LntSQ2R8iOzW/dX5H4L2QmIasfmFwr3A8DitqLeoLGX83ZHynojd2QX9IVEdpb0hs55quWfm90/NJJikfTLsnndPjN7fLc+59V6+mmS3Jh7J7XcMZ4GLNvZCkHu/k'
        b'LrfkT33FLR4Y3tfjq+jzjen2jeko6fGNbbDvd/VoDOt1De73lzLF4vT4j+tQ3vOf2JCClZsn7lndsqxXKCH55XTlLrgnXdDjt7DLc2G/0BeDLtvG9IVN7Q6b2iucekfy'
        b'c8W7iq5ZeX3x+XfjaRKzumYV9s0q7p5VfE9a3OOn6vJUfenq27i4jddW2rKqz3XcXddxOJ8Je1YZ8hlks3yTWA85bP9k1iDF9krGOMOI8d1u4Q1ZLTM/FcV0VPaJku6K'
        b'kkgGC3v8iro8iwY5lE8yCxuDieyw6RNOvCuc2C+NbHTqDwxusrkvDUd3ARF9ATHdATE9ARP6AqZ2B0ztCZje4NTvHdAsb5Ifimiw+dQ7pGVxj7cC3bl6NCzfM6UlqNc1'
        b'hFSmoR5R+Joe1zFtow21rOzxzu1yy/3aVciogrdE7V1DCEvu8ZvZ5YlNljWtbBvXmdjrH9crjCOv0nv8Mro8M56NjRQemHZgWsO0lsWnqlqr+sZMuDtmAqY1vCm8IeEL'
        b'kd8gm+MV0B8YekreKu+wueZ4wbEncGojYsApT1G/f3Dz602vt2k7ubcF1wWNr/f5J9/1T/4sUNYln99VtOiefFFPYEmXTwmqNfFMXL1e/s1OTU5doXldhQv7Cku6C0vu'
        b'hZb0epbi5MStsW1LOjl9QVPuBk351D+8LeV8ZltmJ+tO8M/D3w3v9c/alfKpu3+LbVtQn7virrviU39Z22yMWE3B7l+XtNn2uY696zq23z+0eXXT6kOvo+heQS0pbaV9'
        b'XtF3vWgg77we7/ldbvO/NHjAbFl+alXrqo68vpi0rpi0zgX9ooCW5CPT22Z2LHzIYXkmsRq4qIZQ3ClNU3pdQ+kO3+M9tctt6n1s7isI/d/lGkTMfWHbArsSvxT50f5X'
        b'26PbdH0R8d0R8T3hCRjO69knje2WxnZO7JEmosRRN2pIxMhWzwNTd01tSep1lWJ3GIn9vkEti47M25V8XxSIcRN9oohuUURD4peeof1uwd9wXL1GfykUDfLQLzbWFDxo'
        b'g+4GbSnUZj4HfQbt8JM95SVudjjoMOiAnxwN7wT4yQl905x9MHvQGT+5UEFhfYET7gZOGByFUxxN+QQOuuI3bpRveJ9PSpdPSofTHZuuiJQ+n4Iun4IPCj9I+27QHcf1'
        b'oLwDB4U4ricl8m+OOBgx6IXDvSlvv0ERvvPBd774zg/f+eM7MRUoHwzAXwVSUvl5x3bHPkn8XUn8YBB+G4zzD0F3DbxBGfqmz0vW7SXr84rs9orscOvxGk8wzJ/6ooeO'
        b'FXc8e3zTGpL7XTwO2O+yb4xpkfS6hPfLohq4tAWHlsRuF2m/i9sBx12OhhDsp0Po0+D43aPXWZQ4+hHF8goY8BEPctDvU+KB9BdRokI3qs/NoTCI0xfIQld6A8GfPuf5'
        b'EB/lENMHWfiiJMha9Qojzs3cFAY17Mz2/3qtwqzREJiudaeM4Rh7is3qy7mMp08C2y0MYLFyCWzX8jpIrj8Ewoutmlzix3GodzkOcU4cKYtYW8iyhsBxfIj9OE/hMAgc'
        b'FsHg8KO5DCTtp8XgLJayVVIMiYwr06k14hJVRQVxgIbhq4yDN7Q8l+N1WVVh4ReNNndfWkoDtFTiSvVyexpAKSkuzlmqS60sQ5W+qKKq5FUpRqVhv3MGYJteqy7TV2AU'
        b'Wm2VXrxcVUngZKXlNeWlanuLTMoryYsyYomOMbii1tJWWGhfKGJslVxcXqpV2NvHVqs0qqVibCAvVpxKoGqoE2rLsZ83lA6GranEJXqtrmop/ZmR1NTS4mIpNo1sj1ka'
        b'jEtD5WEAoRJ8W16JQWtRqCjxqNjLceF1S1Q6Y+4m2B5JgaGNOJcjWFdsjZh8gF3NWRTRYI9msaZKX02cTpAUUFF05SX6CpWGhvxpq9UlRjt+WrEEW+GSoSKhbIi52tpq'
        b'9KjWlSikpNJIGlo1rhCd2lBvTDsQaHIlokmPKgKlh1u91tAapVXE2k01dheI07CosCHYO2sH4ra0tu412JiNNXnf9jFq8oJ2So+NQ8LN4JaXwzDtzanOtP4mWAv36bH7'
        b'sAhwEV5jjqHEthx81nVjWSTc6+2X4hqybDU8rwRvgLcSwN558ak6cAa2gg7bqVkyX3gYycOH4Q14LBHc9H8NnHaJhHvAUT0WIuQ8JODh3d1cCdahwmrBWLnaBh5eTAW+'
        b'woVnxoFttKGa8i//fZWjxRYnPRYqLhFLAk7Fd7isjxsXxTnGnR2T4VLDSnAp8dwQ0rBv9Cd3xJyoN3i5m2P3Zu3itW9RqW02H3qPm/fJuvaFmwXvjldt7PLa9u62SO3d'
        b'mHdrLnCrS/4Ss+76YZv6qu+WnflkZtT0pNEV0/YEJkQGffy/iep66Qwvvw5n7pfTipNrmmPAGx+L9d84xsne/bj2cOS9dz/+9TZWYGNlXUnvl0mDaU3fdN7/6pIkurqM'
        b'oj5cLHSQqqQORAoCJ5fDtYzSGpJ7zfZmwDrYQOve3ZCtxogwcLSY7M7A07CR6EXB63DfjOHi0eaSZ2F/QsARgqcEV+dkauEGsB6f48kljP0+JP82cJAc3w63ElkPHgGb'
        b'54SHLWG03pg9HNhaQwRIf3gwO1y+km2mxwfbbMgreBweQIIu1uObBHcQVb5CuJm8KlDCHeHyrFlm6ot7wCa6NrbMgnscdPBNi60lWi3z6gJ6a+EU2D3bqhC9Mou7HDbC'
        b'bUQMnQevYlW+pFUjidHZ8B0pb+Q1iRh3MslGdtiiA2110xIAZwwn8lAbRctD1SHW5aF+RqsHMb59wjD0f5cw7A9+oWihks5g9ccnY6bxWw5LmoVVifyJEopXNutrkT/i'
        b'uVCCiEM7tMqgsRXT7R/T4z+hkYv466aEFu6h1Db24SzE7bUU9XjHdLnFYLWeKS1T2sbRujzERNRdxE4su+ci6WPM9xmMTRhtB464/jPGJkyuuDWT8WqMvXWc5TLGJjD2'
        b'MT+ExfLEK6/nDwGJ4JbF+gpoySlCa44142nMgssymkWhjaJwmAWXg32l/2RGUZagBbcTEWGfq65kXBxZOknVa+kFWE2mYLQeJMWnJuSaO0FlVjn1ovISbVFJRTn6KpbA'
        b'vg0GrcuwU5WSJQoSQ5GErwkkmrkvVSYVpl5ixRiTLjOC0rGrMa2akFGlKcUBaH0h6wHj73XEPBTJ+RnFxAmBvrqiSlVqKI2hgCQR7AfIiCnHSxGjCqLVl+tor6zGTLUv'
        b'lmtCQl6x7EWj5r9w1NScF40aN3vuC6eamPjiUeNfNOrspKgXjxpdLGZ4nReIPK5YQaKmlhHWgOFE1KUycRjTfcIstAKsKBnQrMQIigbiZI2KeLl7np4BTUYhZv7oUVET'
        b'rYi06F3Eewbtg4nufiiDmnLVi5U0Pi8fZRFLm0jW0mOKzofujuVDdQ+sAbbcTcgo8CY4AzZqHdAzbKFK4GnQBBrgBvqE9TBongEvRUZG8ig22L0olYJH1bPpk/1bDjYE'
        b'hQAv8ihOhtKbNXWUKzlizfNxCgdNGVkKDOjYz0qvBltIYmG+8Db6okMHr1EUO3ox3McKEEjoE+1TpaBdm5wapWFTrCrEl4FL8DJtNGUT2AxPhcNjcH9WGhsluJ41Ebyx'
        b'hn63Dy2VWnjVWYOoK0afnGSFzYY3aPKO6MHFcLg3KQvvgII61hR4ahGBV83L4ID94LgBRcWCDfQHO/DJMD5mxofMoXAX2DYql37TFgt3OgjwrM8B53xkrOlw/0zyxhG0'
        b'wfP46NrBiUVxYssdWdNrPYmtKHBIFpaOmbZcYhYKo2IQF0fBN8HuVYgf3AY3grfBXnA4Dz3shW8jdmFHINyN+MG94O3RPAqxPx2OsxWwiRxmw+Yx03IhttH9CrUMvJkK'
        b'mkEzwUiAo6/BDXBPHsbo5GLqtoDGcay44kopm9S4AFxdYWojF7AVNdLcmTRK4pw22dQYVcG4MeA5uFHKISWbHuVl+pDLRt/BgwpyZj8BH22YvoSdYDf+FuxZSWidPxHs'
        b'cqix03IRNWcn2rEiKsHacuFCT5Y2hEVRTz78O60cIcBMagZmUmOVtgtZCZHzvEWcDY4Jngkux96w4SRMmxd5KDZv/AmPYNePR99Z/77PmHpNy1afhq3ir8T7xQXiModF'
        b'zr+z/V3vYrvin/eydEE2J9vsgnpDtqm2Vf/hzMq/v3tSw6suiXnDJnfctu5Gu8rRrjmC6R6HiteU8Z+muOROm/8p13vhR47ntt1S3HfZQt3Y5PUH75a6mJyNItlulpPw'
        b'7P/sRl/m/muGrbcG9K+itO1RiuiJd67e+dgl5BeO492i33tw6MuVHpul8cVfNMb/N3xdO9tvceSh43ad+0Nm7Jd9P9jy3cyjsugVsz7OCf6FY2/nrDHk+n5V8rbY+f7+'
        b'j3ur3v8Aury383NFx+EZno3jF21oOvjuB018as0/Z2Q17pS6Ed4zRRdrsLcE98sNB4Ru4BSx9QAPVk40HQ7eAO3kgBAcB1foQ61tSIK4GJ6OWMgd6P7SPMzcOso4NoXT'
        b'aP70GBrn76SDm6DJaLtj5zJy9rEcdf314bQBCC7Y5gY2suCGcC4NBl4H6+NoIxnEREbgXGwkA+6mz7NAA7gOOgxGf3ghoI3ml5PBVvpsr24aSgmfHSI2NKyAsoX1bLCu'
        b'sph+uRtc1mhBW4IDvIJRRPUUbEOiQSf98h3wTg2oByfgoeoYbDZqMxqkoyBtuCN3Gip/PWLV11XH8NE7NMx28eA7dDnrVsHjoL66sDoGJ7oFZ7PhFXJAVDwN9d16g/0J'
        b'cHuywQQFYp130bm2gFvgiBbcVBBgEzhJwUNI6DhFcl0D947TomF8FGwDdZikBgpenqmgP2yF68F+Lfr6Vo0TD315Cs2k02AHebkSXgFHtfAASumqI0YxnsNIoDe4NL03'
        b'J4O9Wrh7bs0ynGMjasj5kD7Jg5cRYWu1oL2iZhnKD+yn4FbfEFo5bCPcAxGhjCgDLrmZSzOOiNW3eZGNKMziMmcljHqRFrF/A6MsVV5QEGH2seMBzOzPCDUy+5Hd/pEd'
        b'o+/5j8Osvvfu6f3+4W26bv/ohplfu3o3rmLMLNT0+k/FO6b5bckdSf2+gS1JbeM7YgY5LN/YL2KnXg/qLL1dfr38pmKQQ7l7fy306Q8ac2pi68S2vPPz2ud1hnTJZvQE'
        b'xTXa9vsHNa9sWnlodSMX5cNIGrY9/tO7PKc/sKE8fQdtKY/Alrxed+mnbp797gHkFrsJqd1V2xU8rlc4zvQdt8c/psszBvvy9Wryainr9ZKN+FLd6xU+7CUi1lt2393r'
        b'wJxdc7oCY3vdY00eTIbGvT8sZfq7ljG97pJ+UShj8zaxRzS2y23sy78M6XUPHfbyjx7+/dETrk2+PPkO9+d279kNRE8f5LED4pDohZ0DDFLsUfGsYaphA47mDL1mKmc4'
        b'ip7WETPh6Im3sXx0+ciAo8dG+WaNYbGkP1hEGq1ZxaZdfOhWlJdqaUcc2PPGgJO5Z261RvMlHa+kqrKsfLHGC8f7jGz7FpWVr1CX0n7GHYvKtUWlVUvVWl15ieZ7TC32'
        b'9jBgT/x/a6tVJWrNJ3SASQOMV4QZfuwlXV9ealBawYXW/BLrKXtbs187wC3KTs1CmSfkK5VJWQmpSbm0sUKjXdsBh2pVeSVj+kDzMcnUpPBP72AbzUJofoEvxAzEQ0v7'
        b't0RpgewTE/GU1L3JCK7o2T4w/t/b8sarxYznHMhq1rCZC7ZVqq1lMYZ4B50od6/GoEZdS25bcAenI68z+g73TkmXa1odPpsZ5d6gbsxriUHveB26Tmwb2jLgTuIHIcMC'
        b'B224Iqe69MeOHEH4E/tpghmsBxS5zmATRxPShxyWKLwu/UvsPkLa7zYN+5iYQfuY8A781EXe7xaPgrwTWXVpJk8e47CjjfHEzwbjmyIJfzeTZe5WA3u6cI+nPVEwPi2w'
        b'gwzRJOLTgnFggR1teE6vS3ls6yQY98CP8gro9oxonXRsMvqpS33MZQkisc1hH3yJfcJfzRL4PqFM14fk+s0aDuXk3hTUK/B7whYJpIMUujxEYf6D+PGbWPw2r1cQ+Jg9'
        b'WRDPwm+C6FvaYrEYLzVnayYPMYLKorxnwhM6bjlcDzstJA8h8/vwt9juuxt9VjDEUDFLydZxialibKg4SGmjDFbaKkMisKFirtIehY1BYaFMmAMKc0RhEiYsFIUJUJgT'
        b'CpOisDAUFo7CXJh45mGjUNhoFCZDYXIUpkBhbijMHYVFmIV5oDAhCotkwsaiME9EjStKwVkpiHDQ8RbwC2yiWUovvPViNLlrYzTPy1ZK0FWADfWiP1fDn9J7gg0dVxlF'
        b'jILaRHOUoiGGe20X8AMopY+QwqaXjQaL7Uxpoz9H9MeJZjPpujG/o/BvBNsY7srQgH/t0Z9DNFcZrfQ30jAOm3TGVBTYFzgVuBa4R9vS5p3NqLFnDJliNaTR0XzG1LOD'
        b'MlDnWMDSCQqoySydE7HTEDMwGvMJCcSDMjEaXqbWlNvxKOo1b/vhb2gnk/ZPnfG0p4iMHIv+kJgcrcES5FMFEm1jy7VVsVpdKfmNioyMiorFEnHsCm1p7JCPBnhkD2bA'
        b'jvZ7XY5ueWUVqsVai+TRX/QPSZnEH5LApB+YwKSn7kNSVCChPjLqafwSna46NiJi+fLlCm35CjkW9zXYuoi8hLGaoCipWhpRqo6w+r0CZaV5A/WOoelPIu+jn3onxKfm'
        b'qGoxy6bEpy9aHXqviByHrk/H4CKg94TekeNpNuL0R05o7AsmNPZpOHqXoKnSauPJFoVltIyqxZnaxSTyWBx5wpBEX/TDAZtSdZlKX6H7/40mplVFWCJeV7BS4dmJDiZ9'
        b'CXgZ7C+PXHOcRTRklZ/Njo4n9iDMNGTj/jmChuyAbZGmSq9DXYZ2EGI50BSGl5bKsmGIQf6BCpHYb5pmFbok88wUIlPDfoRCZLsNzdF8ZIWt+djA21hoTdpTzC74Wspw'
        b'7GxFa9Jkd5nYXI62Z3bHbXMdf0KNyI1Stmo3qgP7VNqCSflrarM9ctqHPH16iic6sz3xXH11dZUGbydWE3+0hNnTxtrby8VDZjSxJDFJahmMB/+wkEliSZi2HB+t1kxQ'
        b'jA+z8gk9X4glCSnDXzKTBX4pEw9NZ+SJQSxJzXtmjLFmMV50+OJPhhJh2P5ntmTpvU7aHEypepEOO2dnvF4aYuJ1gI42tBmqNeVVmnJdLe1ORRKWla3MDEMZpqTOTAmj'
        b'd6TD8pUzc3BYalZuXhje/g/LTSyIC5MqTKfr4xVRishYJgr9mengPZK8YlIxBY8nwXRSBkJpw1QMqVbMTdHlC9USi1PG4hEZhz4FMR6CkE5n3SgUY23HmKfJshOdMd1f'
        b'hxptwoaSjFiIUvo8Bd3r8TEPPjEhO+sEZ6FW6XCDIiJrh9rIwkiCcvpUBO/Go++wnR0ahmHmtZSUTpyrVmPa9RVqsUqH1u9Feh2dbUJcXtLMbOWcIuwoPDs3qQj7ds4l'
        b'VBghE8R8kNZYSHpQ0eUjXuEZo2yGejXsYzDnBDQCwXRWQM536C9MW/thQ8ZUmBGDQWqwmu7XWlLoIXEnhdHUGqKUV5LvGKtUiFOhjxMw6qJSnJSvZM4wKsW5y8t1r6k1'
        b'FaQidc8ghh7gTF9EHS5Vp6qoJRFHHsFhpj7BmMeiK8xkNQv3JKbKjBa06OM2hkIdDQkx8zdkEbfKiu2mkc5nUPGYpVtr6B5D0qHrjDB35j0tNT4uS7xIXVFVuRh/OeTc'
        b'w87K8utC9s3hO6DVD+5JhzvGwFuwgUOx4TGWBDb6kcXZTwnWGfTY2aAOg0L4tFV1eCgJHtAKBOBaicF2faGO6GR68UA7EotS4K5qsA1eQ/9dAlu4lABuZMN62AhPEo3B'
        b'caAV3EpXyFdGGrSnKWo0fJMDtqnn6PFiA9vUy3KHabZiC/BgLaLUzAo8RYHt8Jq9nX2Qfhb6cFEMWG9mnd+kng3r5HAPfIfWO60WCJTYQL9EnpUvkcCtcFsE3CrD5tdp'
        b'q/RyvH16wJUVB64nkwME7AzgtLYGXgRtKQZD8oWz6LOjKZje9mp8tmGyJp+iSMuEW2RwS4QS1oFLBRmzUjhKsAUrj8Pr4ERtCAVucx1gYwrcaPC0RGq2AG6dTQ5SCtn4'
        b'KMWRNX0MWEcfQe30gQccBBq4A1zFJzAy1nRwoaJcMOchR/t79P6wtnxpzlQHEOnyTu/l8t1bNwQmJfJshKF/bvndTttJyzTVkt7Um9ef9mQqe7b+Oa7z/JN//OOPwb+t'
        b'5lV5tnaO/b00LWPsz7iTLq6P+TykJaem2429UiP4wHnMaXmg3aitm2MydQWJmfNdoevUxiXfsyWfUNquDQ4XJn/0xi/PQY+Ef1+fuXvdjl3zbh/jlZ9evl7p/PnhB18c'
        b'5v7x8dePdyxb98trBds/C3F8f8OVKYdOTPv3u1951M/fvlJ3Ys2NmQc4E+ac++UXZ1KdN1QtXlDmlp2wLfeKZl77R3DNyjmPT83Xzf077/GDv3C8zgZN/vIjqYCoI0nz'
        b'Xw1XyDFq5LXRfHCcHflKCUGNpNk40k48sB8SGQa/2FBOsGWVkjM2At4mm9Xlc93DTRgW2JiAt+Vz59CKEtfAhlfM7EYT/M1K+BbcD5tCiC5BATg1Kj1b7uzPHBQcXUMf'
        b'QVyflGahDAR2eBVwKuD1OUTbA/XXk7DJYQiUZd0ojGYRgcNEfUVbCY+Y9uDxBvw80Iz34KPhGWJTmotPI3AEeAK2WjUpjXp3PQ2eaYabwGWsa2pm+lsPGsTcheC8mhxf'
        b'xKrgm/jQBFz2MClVgQtgLa30sRYeSEKZodE7JwBeRu8zWclRr5G6r5alo9kiA3RWojpYxBoLD8+UOr7UFhh2I2KO9jSzeGyVize3e8yjt94f1YRTozy6PCRtwd0uEzuF'
        b'd4I/4Hfl5PdPSrxT9sGSRxzWqNkYwO3t1yxqEjXw+738W8Z3e0kbeHjr3Iq2gqvQBGsWBrZU9AqjPveT9E+cclvwtgDUDHJYYdkEmZNDkDk5rPtCUZd/RK8wAkPzKVYY'
        b'AfF8i6LNJNFSSLQU1tcicb9E3sg9LOiXjW3k9npKv3b1bEzu85F3+8jb1H0+4+76jPsS79H7HJi/a35L4D33ENpleK97VOeE25NvT+6cbG67+QGHmjKT1e0eZSbBCMyg'
        b'vs8UK0aG+GDHbRZAXDNruduR3FOA5R487RHYbXkYtpD7+IfaySW27Vr5Y6kLDlNexk6uZiFnZAei1nqQwVLuflQKTTuOSqxlKl6AWR5qx1ZqYw1SrZFjAXER2XgvWaLS'
        b'LFZrLUQ4Z4oR4fBe9BTbEQ3fYLM3NgVOSITDwpwzMXDjUjAq2tkozP2U5m0w1OkDLMzFlZYiDs4c9WpgRqzsXhnZSHvEzsRipjW22HhEUGwFZyJjmDijtUwMsyWmMs0z'
        b'LEFM4CLEHCOJ3cQq63BV6hhBwKpIxDDTdCtakYpoh910XPPs6HCxSisuq6hS4U0CxFaXo5BK/dJFao0BBIWIMgixmB8zALjiyNfFxlwsRAvzbAyChU69gua7caloq59L'
        b'acgvg+FFYeWlmAk1FcXo3puhSSxBhGgIqYTpDFQmKxSKQCnD/tLQGoL3VuHW1Oo0+hKdHhvoNKakECcbkF1m78n3xjikJ+irK9SGJmFgboi/xsQjln4pqgryjUSZlJyE'
        b'D3WSirLyM+OTlDKxQVrJS5qdJzXWj5oAvnHlqCtL5boqOfoxK5+kqpoGsJt9scKawIZC1RoMdDcX2Cw+x2QZ5TdcI88SvxjQt9G2K/l6SVUFEtitS2ZiVKokZVZcxnCp'
        b'jMaEjyCZGbwy00XBxljxE+kQTLvhfoaEUdQuqIGKi7OqKvHIMQO7r9CZUscf46+QIIAB6HjAGLtGmaZqKSpqqYpBqVfo6Q2axeU16kpDT0JduRRDsCQlVZXaclRc/CUq'
        b'eDkJRbVizJj+zFxMl5qTTZNStegVdYmOHi+0oJObPXF85FjSWVDlEfpwHjLG7jZDP5GrcV9Gg558V6bXkL5JRgMB0pukNXpajRXnMtKTVrx8STkSwDAOvxalUoHEb7VK'
        b'Q8tQdGR6bGm1VUho1zFZ0chNTRXq6ATIiaqCqXzUsehuRBfeNIoV4iwktamqqyvKSwj4EYu1pD+a6wnQfS+BHjMqZpCj1HNT4pRiCbpKZeLEpPg8sSQ7XynFlZWgTEoU'
        b'S+KTsph+G2amyDBeGmZvhnSLM049QxyTmiNGnysC0pZSQN1EeB1LeYErjcj/E060ZIPf+66Ex7SCHHjD6KUMCSAdyURYGQ3blxqQYq+mY4Mkx+EVgkjTx82mbYxhgM0p'
        b'sIkC+2E9uJJHXEKBneANsB0fnoFtMu+hQiI4DK4TS0VzwaUKJFLtzMAudJBshr2p5TEGetLlYQUpsrT8IcKhhXswbKDsfNIoUD9uCUF6jQcbwab/h733gIsqSRe+O5Gz'
        b'5NxkmpwlIznnJKIgShBFUBpUzJgQEAVFBRQBEQEDUYIRrNoZdcYZu22dRifoTh7XmVFxxwnu+FbVaaBRZ+/uvvvee3/ft07PobvqVDgVn6pTz/8hx8ymDqqh1RVssS1N'
        b'QZ5Gy3NgtcgG1z+W0IyRw3jLMLSEPDcFaOJI0jwd1GAf7EsjxwAZmobSYLfo3BxetV1ZUorNlhsVgNpIwnOzjYjFq1VLwniSgPvhTlkzbdAtO7NenAfL4VHkcXwOeoAT'
        b'SaA1Ox5UBmwGTWAbOI3+a0d/d61YB2rByYAlGaBKEjYGFOfHxy/PKDZbCBpXLFOmwb0+eqhs9+RQRwa3psMKWJMpB4dXyTPQuv8S3V4a7C9NxhkDB+GVP8wZrNQGlfNA'
        b'3RKwU5QluDeJytVOtKqoxznEZ/sWK8EKNg2ciVfRApfhKVIUepvBlYgtomNxMnR70BtEQGnwyCo4Or1s56SIGHOrSkuTYO0qBSW4P0lU6mIreryIx1UjMr43TWYD5aBL'
        b'eo2MVCRKRBHu1oBnN4A2YvINbJeA5X8XrYfCcZOop41WgL1UbcIhUKEQCnfASwQOx4pziBQ3dVkDzsSRJoMijcQOuB0dkOBGgKo5cLDMHVTBAwloYVpFh2OrUTznI0nz'
        b'doDH096IJ2xmXZeivmFWhGCnHKhXM4Mn1UEn6NBQZ9JAY7QK6ID7pUt98cOdMIR70MPZF7xO7mPANliPEjrnjapmG3qOKup8Jdi/hAYrEuQTNoKh0mgUBZMBm8Q2T6LC'
        b'ORG2dpSpOPEIV8GT9glT2VKY3VlQaTWXzgF1bBfSlLy90HghIiXFh70t6k0hb3AG/yjmhAg1cGkLrKNO69bIbeCuQWvhjhnTfmC7DQWuI2fB+sHofGz28DWjh0agiQmu'
        b'gCpj0bZLTFL+5iXX6VwFrOH3qOxg8vsxYJ5a86HbGvfvJ8gaKynoBEatyvoT67jj6jwX0w+iEhb1rSrfp15iEel39WDk2N3G/M5zzZyAuQcaN/zg8c1nZc/f/Z1x/Xtm'
        b'tvEmU+avCsfplzbQSui38+9M0l/17zGrfH/jJ/aTK5TH3d6Xo3+YKFF2gR2rMywcjAt4V8NSezJ1ZFI9zITzoZVRYpJt/fbbHd5Xu84HeDIj25xWsuYkvXtr3QfsFeXy'
        b'75doGCXtiTv2yVOf3OS+pdV5+u98MfSnX33Xhv2gYlnsf++9OLnxHa2x3YUe94YMGm89ZvV+YeDufcvh7tqUXyp29PfMGwxY4XmL0+jRsbzqWkyc6/qqn16GrP4+csMF'
        b'qzi3rmcPDXOcOwr8V7ys5D5ruOyauz61NTdxqPqMzrUvT9yRH7sxqfbrmRzPDywGnEOSUs8VHXvwua9afO9IXeDq+hTD79W9jjQ3nP6g/YCVtUsg5/kPuZfkSrK+o9/c'
        b'oFI9P3LU/q+uRcsrtnALN1/Xe2AKnkSfvnd2MiP31gXdX+P23VNau7goe73Jer4b56fPP1X56vvPjzeuNhqd3NySuf03G+ungQ/ssnc+Stp1Nq5Z39nmFPvHr1T2Sf5u'
        b'cqdu+/LrinfqNIIDFdLKh7ssvv3eR2+VQU/xWl7NhqSXISWc4+WvUqJf7QntH9nFyeq8UW3qe7Yv8Me2D2Oeg4g/B3/jV3NtLTdrIKy1eet7Hxv+4LluTONPHA2yNePi'
        b'Czsi7eAueGE27gWch/spW2snzPxnbxvB6mSsuSUL2sm20dqlSZGxoB82iA6YllpR20YHQ2Bf5IxNLjkw4oJPtmqGkuOR88G+9ZiwMwt8Ywx3kD2lKHgAnjIDQ6/bpcM2'
        b'6WCVBHX0dUAGa89NbynJwd2ahI6zyo3a72qHFW6vb0tVwEFZlrSRBxXDGGwG561jYH3xbL2vOjPyBKALdM4Hp+CF6VOy+IgsytUJipoyWCBljfr+BtAfDs6waJIFDGNw'
        b'TonsI4F23YRIWLU4XkQUCgEDJEk7eAVcxhtdngqz7aGtTSb6XCtWor6LvI1h29stq8ErBWSLazPoVp0yzEnQJK7zlZnq4FI+KVx/MApPgzbYjG6xwUaJWTZ0cCFUilRo'
        b'FriQ+9r2GXsBOMfKMAFtIjZPFmyyxrAZdUp37QTDAR4E5wn+Rx6ed4mMQvNwOKh8TfmOSXMAo5L2oD+NOibcA6/gQ7mx0VzCk4xFEotiENMH1PtRSnf7QB04bG0La9iL'
        b'ZhTrGmHPc3VqfKuVANX20ZZbbDkoEz4MNjeVo/k/cYoNV/Yf8EVmFLbvG79lL+ZtMBF8YA+/ml9ni42ZmXeZCzUdb2s63tM3aQ3pCuqN7o7GWI6Qh2/fu2Obdsq3yQvZ'
        b'jny2Y5/xXbZrrcKEkeW02a5axYemlkJTF76pi9DUnW/qPqovMA3lKRtNqGof9qvz63LlOQXyrILuqAY9NLaoi5xQN27NvqNu1bV5XO2OffBDY/O6yCeSNFNHvklAbSSG'
        b'Tdg32gt0rIU6YTydsD7JEaV+pXFXvkNYrdQT9pTlr5G1n+iYPqHRzd3wHqLcebm/MunmQcRMWDAxExZMp2AKHnUerZJ3VM0f6BqLdhL9yQZiANlADKB/o2siMtLV7t0g'
        b'/fNDsUOvM0FSSJBUEiSV/lDTAPmL4CQi0MoTJk2Lg1LU0JkJrmkgCh5MgoeQ4CF0DHLwavFq8KLgJgKDeJ5W/NQGaTLPxodn6ntH1RdFpqV3eFPdptuaDn2p46xrClcV'
        b'7rhGP2Tb9qndYbuOmgo9I9GHh65x6YSxkSwwxkgGbLANBeuSEGja9lmPqwn9E/j+CXecEkh6Im7LN5oGnRv6Nt2ZmzIxKztRAoNonlb0hJ5JS2xLbEMsZnyMyPfJi54k'
        b'gDxJIHmSQPpDPXZLVGOUUM8BfXh6Dn1JIwv7FwpdQ9CH5xry1jBPZHGteNV5CVU5fFVOl5lQ1eG2qsOEoXld2ENDo9qwL9V1eLq2XSV89aDx1Ou5vJRFvMylE8FxvIQF'
        b'vIXZk0y6Ri69loFKx9C8llEvhwtuOjaeFfrifVvV+4GRJWrX4d3hoxp3bPzuGRq3ulBVLDB0qA2oDyO0Dmyrrkv+jqrLhKUzNvVmNiGqhKg7KEOm1rVB9dEPNbVrZcS2'
        b'guf8IfVhZouy+MCbR5f/kT6PE3gT1iDGZziDLo0S4mbVimzo9ATCZEjApYyu/8x2MV7CnpR0ow3L+dNn7xdL0kT7qcuxxClJjjYxU1gpkilSKdIpNGfJafNAEv/WQ06M'
        b'9fNkE3IKs3OKuf/V9ijZWxKt3/FuSRaXPT866rVFugHtzUW6BVm4IDH3UlLkzEnT+Fl0Yrh7swSsTrV8Q9MbHgVnFdTRnLiVSMShsAe2TkvEYDB7liVwcMZXxA8PwZZc'
        b'kVRdqiOSqzfqExKAKayFJ7FPiR2SFuzWoEsE1qM2zUDrvqMScwPhfrJloAL2mWGRmwXbwREa3QBj4PaGkRfOqrB1IXnfLHrZDHbA83TLJDhMAmbBff4EHk6j0eGxeaCP'
        b'Bsb0l1GqX1thA+glumoJ4DSGfverkDCmcBjsk5MpZnqYoEDdeH+iBTZRWxvb54F6a44V5paVrQH76LA8B+6iVg87YS+ojoxcq4bEnxgJmqQGQx6c06eUyXpAAxhIhDUs'
        b'jO0FA2A3DeyDo2j1h+d+LXgIbpuhCcNLKhgoXOtJcqmzgTG1zjcGx+h+8CI4QJTF1MFpuE1MWeygD7hMN0IiZDfxLkYizekZPTMdrDdD9wHdYJR69TvCNpMjtuSZNFgO'
        b'2+lWYDvsJ15asH75zH4GHJaj+4G2dGKa3BAJc02JoAbWJ8N+1HDgQcwrlo6lw3Nm3Asx34Wge2LQX2XRXxPy9zus8f4dPmUWQxqNERLHRsUpy2WweQq0HAvOghGSDRtw'
        b'GGyf2UtQcqfbw+NyxCsRHgHDyGu1AhJi1aRBPd1rCSyPIeUF2mNR0xlEZSZFY5rLFdN9PJWmeNitTLCfG4Ok7RCwlcaQo7Phdi+yieC22QUDrJUYNKZMJJKK3cPliXuK'
        b'G7gkV8zER7Pz1qHFsSM4QtX1JQsjOIjKRgq0w35UaQfw4W1daotrDmmvVUmY+AIbYF88LX4N2E3CLZOFXXKWVtawPwoVWwSo9WYsAFfmED/JEBk4aO+WHgFHkKcE2E6H'
        b'h7aAC6KX+KBqBWya3vABB+h+EWCAJJWzKHBq9yNvLt0e7LXM10gOYnLP4YFybdwHaenL9JK1fL023Hhse+9TlxG379fUnD18su12fUh6d1d45NJHWWuOzs/X/FP9Oa1V'
        b'VUEqHI3+3duMd6/zZ+00Vlc7sRv/s9xtvK3X99cTD48obcsbdM679eGr5nuDn667d7jxb1+/GnvlJXz10rnCWTNt07l3H30xKDP89GJbadZpiXfN73XTcm5mtb1zL2jT'
        b'0fQ9L9c1LYkxfv4sTSnj0PNHZikJ69MKP48zLrjx3rHcyFMXfmZu5ag7cWzWVL8zGPBl7tcWzS65l4e6jc2O3XveCDzufV6SKJtSv5x7J7WyudDBL9Gwx9HC5GOfuAe3'
        b'9SIzWo/dfven+/0nj/R7Xzz5lyNGVR5Mo8Tt0UUSL9Pm/uWbQ4XPCzJOfsbQl7wvXXH4++wX3L8+nXPE3u6o6osy+1uhz202Z5WtvND1c25MzY2fy3yzlMdGN7Ztzxr/'
        b'4OnKO7eGfllTVeWWQm/6xsv/yx3PG4/H6ntttDP+/vitd7q+P9nldPjZ2fNfZn88sdxpvNhpzXGf02oPKhdf+fileavNj+onnVv1Px39idazLTVoYeGC+MvWixfv3lLq'
        b'UvjBue+/VrWuvlo1+EvG8u74LQsHbtH++s75u3t9H9ibfBJw1lVvO/faw1GFbat1t/3N+bPgpRavmhO+2Lzclsd89732m23PjOMyZA9WpCrkeYC0A4PfsId+al3QqVfT'
        b'of2xycCDry3lPjAyvm+UqNDgfGqF290LVRljzQsuPrJR+vWj6Nv3zNX06BeevVSsenbR8uuk4xfqR/0PPaqIPldo8O3gL/FVVZu9JD/X62xw2ld7zUftLxNyMe8lr7If'
        b'Strg+4mry+p1C48evFy849GdD4/ytUPuDUsd7Gl7L2fpwa38e7eTc7xuh38RprQ1zMRy/2KflTdlv674srws96tVBUpzLVOWvFDoSXcu+HSB8vJbr94zPOH2GdvgY9WP'
        b'js8vSxsOXPfb9sGrlWvd3Dsr035Tfjjwi/bunoQkQdWgmvMnkRZfXfeVbz/7jsNI+l+lh+Z8W7b1VN7LizmPQ7s75gnbjOFPXu3LNo7H/LL+8ct1e5YkvPruZN41z8Y6'
        b'2/VgvtduWtIPh27GFkpOJiQ7LGq99XRhybthknu+rnK5XvZofkvdbz8lxo3d8OjQWdX6cnn55M3RJZpHQ5OabxcG9Fu/d6mszmr/2Q/X/v6i4tKlrhInubHq3xIG3V5E'
        b'vMy/vAU2Xcz8k31RUjHv2er+4ZcDmWk6q4d/zSlQ7R62+qH25GfnWfw8jlXIK4+th36e/HVY+qRm661qNYlv3ndsKPpJoj3uc/t3+i0vCt+PYz45tLThxOp3fjHeuLR2'
        b'18WvWnJLr3z+NHLh98/GTsf82mvbU3QlOP7zvX+66z7vfbe4opepnS9X7er6bUIG3v/CrVv27pkjvUObDq2XcBqT5c3ZUnP8pcLSyFVuq8yVFjRXeToFOt2UX/ShMTtU'
        b'WqEoIWn44p8eHI/9s02Z7irYJMndb2D/dG2X+nuXq5oii4MzT65pOpA4csrpp8dZPQPCwdAfb7Z+uFHzyaN3WcHV3c6uBkcy8pZ//jw+r8m5Sdio86Hvoyjuu5v/EhV9'
        b'wvcvUZO/ZKXkLf/597ueieeeyz581PbhnXOg9cPHAz981t5wu0Lqy5/HlA42/SjNVoz72f9M05oPf1Y+Rb+nw92m/6PVUPH7EY+ti1/9Ij3//suluzczSjcvP/XZvZhf'
        b'u+TH7n9Pe3DfamDEl2lw99t0ZtYLD17y3vvn1bW+kHuYXvmrlceZ73/JQWO0bcnvH+v1Vj0qfLrvoyrUvXuGfvhE71XVgGuTyVPX3UsmiyytPlz7ICHp3uAVpq+J67O/'
        b'Rf72gQVz7JdvrzySH+/1dHt1bMErWLSN79Xc/CjD8uXmVre6X7/oXfxJ4qpbv0f3OPU5XzhbdIb97pBVyo/NTScDLiomBSfabUxv55/9yPruxEi6X0JUpa/GX35TfefL'
        b'jfHqjy+ukVj0k5r1hc/yTIYqXhre2Bfwwfyasns/Pfpp4GUe79hDT7OBglITwbHEHwZuvVTolfmoaKcdp4DsSuTBanBBzgpJZhvRRI+Rp1M7KoZgkAV74RhoJjsmpmgS'
        b'thaH6DiAK4w18DRoJDsCzNXgKLXzAHqMZjYfWBl5vmRnQnIp7IqENZEcMAzrp/yVHJh5KqCW7OlER4FDonNEsEJGbPsEjMBzlHH6SzGwR3QL+tPzli2UAniARAYa12fg'
        b'OzG41XbFGruwKCQpaUSxFGAdHKW2sDoVwS5rO7AbSSXTrGSGrTvsotCu+0AFOMLFcivYYT+lJKUAx5jzQMsSkh0Xb3iGawfKwSDKgW1xDEcGSbGD5AAXrGTSXOBpyUTH'
        b'HGo7abgQvzDZGwv2UBtmkpkMK1tDwkaCjTawJzLKShI2LaExFtHnRqNnwMJcHjiDsbigBVyyR+IyzuA+hpkC3EHyzzCDtRgCO4WARZLcZUYZOAKOi/a3kpAUg08O9sM9'
        b'kUyaFDy3wJERqwP3UAe7zsFdzpR3kRa6AQ4iWUAB7EYCEGiF50nGFpvFTZsnWGZLB93zYAOFmN5vicn8OLBtOEpcFuySZaTqJ5OSD4Tl+VyrcLh3FdEw3xcjRVMGfWBs'
        b'I7PEPJAKXsMGA5ER4OAijDWi0STgZQYTtiSRZqKzOAUORsKBWDnQjerqoKUkTQaOMEBHBtxO1ew2OAA6uBg9LWPnC1pgjQRNFu5lwGpPeJyqup0S4ArOngxoiefAPvL8'
        b'CuASUxUegAdJfaRrr5rZ94Pl4BwdboflCVTR1IBBc1yP1nYcWUsrvMM2R0sa9jGRHF8LTpPwVtLwgJxdJBzmwGpUAIoSoJ2R7u9KtkydfLy5MXQsyqmAQVQPHhtJvovp'
        b'3nAQPS+uDwLOlqCpaIB+QyZodFUV2ZHkwrbIGBtQaW9pa+WIhHVib0IXbGOBk/lwJ6lXNzCcybULR+uJHlghj+6j0RQlmX5wyIX0QmdjsFcuwjZqNTgbZrfSE1ZyOXSa'
        b'dhIrNMSKUkAfDgbHsRsNXskG2zEkuQPUkZgtypQjsZ0TuBNujyWoZUVQz/QGrVGkVN3AITiMSc1o/TE2i9aM+msjtbd4GpVdGzfcioPkW1BvCmrooMYYnCQpZ26CRzGA'
        b'W4JGl0M12IN6M5KOSaZNZWD31GYy6LCYwiTAU+A8dahvv57EDMUZVhbQwXHY4UV1434T2DS1WSoNdk6hnJMUSR8qgSfBZTlL1EFXRyUtRfmShU0McDFDiUTsUQa68CNF'
        b'29JpMo5b4DYGaIBn3MjDaIJO0Cxnx7FCFYYyLZ0PD6sx8hPMqd61ixFkjarHLi8SVSk2sqEEaphL4MkgqruPFYImOcsFYXarY7CI3UmHLWBAicRraWkgxwmej7oGKQwJ'
        b'2ECHaA3bRAqJA06CAzP7umZJdHAhoZTEuQpehG2o2eMHZMLKeB86aLeF+4lfbCysiCTvpRbQ7SRpchEM2BkFz1D9ZQSMgSvcKA4cwJUGdgVHog4jz0DdfGcCCc1JKMN1'
        b'Bs5kFBPgi4I9U9oQbiU7taATVmqRwYEGR+NAL1phZtqS53AIBY1wEJvVQqthcAUO59B1YROgzqq6roL7xXb/81Lo4IghuEKGFRdPNK7ixREHHCOLIzYcIoWaC3d64bOo'
        b'vrBb/GWFLygnCWJgXzvOaHFUHByxp9Nk5zFQH84jSDV3Z38upquTfguqFuCNBJxrNTQSw8PgEqggkIV18II9F+7lyIIeGzgMa8pAfzQcQPdpK7OsQBuk+PWqsB8PADVe'
        b'uZSnRAodVrnB06SKFoPK2EgCg2+F2yirNQdgO7UpvgeUw0Nc1LpHwfGSNXAQ1aEKPQMOoaELr/KU9Bn4Da6k/UoaHT073CftQErLa5kqWpHBSkvUbeAxl1TkifLSQyU3'
        b'H/SgHFtGrLVi0KTAgQWrGR7yc8hA5Qr2oGG8GtbEhsPOdfgdMmk2SgxmNjZ3RHWPCnAQjImswkSDPSL7NaCNQ6Iwg5ciuGTiQsOtEzwsGiy1wGmWIzhrQEVx1gO2ouFU'
        b'FlTYkvWkBDiC23N1OvUK6cAad9FoiVpYG7iM7pCFQ6hJmHuTJjQvBd+M4ejzYRuNkUK3zUUzPuH3tcLONC6qahlYudYBnkTfSAJonGZiyt8h0l7ikIgxMmULJwGVXLu+'
        b'JImYoQGqQbU9OBMXPfUWYQubwg1WwmEJuVIFGVSgRsvhQbr/Zl2qOe+CB6K5cI8tHXZtojHU6CYyUFRQ5yK41GNoa4evxnegyb6baSZrTj3laDaeJUXm2YiNIHDCkoEK'
        b'95zPc0tSSqANNIHqWNCI+gU2BxBtwwmPRmO5yIKDu7ckOJ5oTc3scHsgee0Wthmemnl5Eqr03AlnchhlpJ6YYSAvn+H2DVOWel6z05MMe6TtY8A50tGl4TZbOXKX7Woy'
        b'BKvAc37gFBO0e6EJXY/K4w7YhRKOirHRnXp1p5jIjA5BUwDZPupOVkTNAfUwcBnsxV0smAFOwW5z0kydvMEu7IsH90OgCx6lo5F/QJ50GdZSUIn94Blr0SDiypSJhdXP'
        b'LYiEA7vBdjGkvjZqEdMPQdljagCHSR6ZoDZk6ilIWipwWMqZSWz6kJ4O61HHO41bNGi3mzZ1NG3nCA4WUnNRJQtskyPzIxOOoPS76KBLAfRQw3edJNglB6umhCNpmiY8'
        b'wYhHow718uoQ6lfH0NgfQUeBz6XBnbhHngNDZJpGg140flTZCNAFRqJxo0FRqIEdTCRHdsCLpAV6oZF2TI5Do9F1YJ86Ekk84D5SSxFzONwY2G+PJAsylCsvRxPwcSao'
        b'AsNgkJqir8BjVnDQxs4ODweNZcFototfRr03a1sOauRQT1iChx4O3QCiRQ+FlNydBzq5aAqAlTL4uXoVRI+mBWtZnmgSPEwisMqEB+VsU0AteTZJA4Yq2KtFxi5/VKF7'
        b'iZHDGFsr3L6HtJUZaMqvA5eoprEPHNzItbeCfWEcPBBdgn0bGGElsIL4skETEr5t4Y4tMdSu0iY6RF0DHCSiQ3AuGgIpMwngXOSUpQRiJWHqlSe4sGUL1y6ilCMjbQkr'
        b'0QTFYIB60Ax6qYbbpYNaLiVaF3iFK1nicU4Bnmd6uPpTvfco3KpIHfunDv3D/eAyPaQYHiIiGTjlC4Yj7aIlvdRojDK69+o51GhQDtvhSawTQNfSIyoB+Ug+xK3Hz0xm'
        b'inGECUf5Ggx0704wxtH+n2VukLJ+85+4CQTJYrKtf1/7La8sKS/yprJCnnpTGeNIjCAfLttf9omOOc8iQqATyVOLxJwc3UZdobY9X9ue5+Av0A6olZzQ0Dm8om6FUMOG'
        b'r2HTlSzQcK5lTmjptcg1ygm17Phadjx7P4HWvFqJCS1doVY4Tyu8ldUp1yYnZLvw2S59yQK2F+U8HvwnGXyXQatpp3WbNV/LFv2i3qYJNSN4mhFdOUK7cJ5d+ChL6B7O'
        b'dw+/w4moZT00ZNfK3zM0b11zZAv6osZuVes0bDMUqDnW0r9R1bino9sQ1BLZGCnSSVgq0HPqc7yr5yrQcasNnGCb1IU/1NFtsWq0mtDSFmpZ8bWsBFo2k0yGrkZt4BNJ'
        b'mpFpq3+HZG34lwbGtSETJpxO7zbvdt/aqAk19l01h9qoT0xQyhhb375ZYOI24z6hby7Ut+Xr23Zl9S7rXoYib5FtlG116/Rq8xJo2ePf0o3SrepHlPBXVFatQZ0RbRFC'
        b'Uw+eqUefm9A0iGcaNJoq0Aqe0DM8KiXUCuBpBbT6d4a3hXdl9y28a+cvMA0QeQXxtIJEXrl9G+/aBQpMgx5q6wu15/G057WmnNChvmEC/jy+/bwXNEVtnaf4Mp51bfnV'
        b'5RNGpkdTX9AY+gY8fW9KO6Mvl8/xJk5P8GXcCPNbJ9imnTJtMl0pfLazkO3LY/uOSgrZYTx22Lg5KrBAugEqLwNjob47T9+9NakzrS2tz5xv5j4Tz2jW2LLzyybYRp2s'
        b'NpbYHUKzQJ5Z4GiK0CyaZxY9vkbAjkER+hk8UUbxtaQ1pnWZ8/UdhHqxPL3YvqyRFf0rUI5Mr5qOr4E2ArdYVItHQ4V6mTy9zC6W0NKdb+lO/RqNH1twfsF1+i3WDdb1'
        b'JGH0In70IkFYhsAnc1JXMZSu88SApq3TotCogKpwS+uWPvUXNLpFJH5Viq5T2UyhjHL48M18RpcLzMIF7IgXTIZFEAYpoetDQzNsdkFoOJdvOHdUVmAYOCnB1NZ5Io2j'
        b'lmyUnNDTbwlqDEKtUq9NT2jkxDdyEug5T0y/u+XrObygSekbPMWXvviRtP60Cba5kJ3DY+d0ufR6d3sLrX351r6Uy7jjNfer7teDbkXdiBJGZfKjMnmLl96NyhYE5jzE'
        b'oZbx2MumQs3jW8+jXMbjr6VeTb2edGvhjYXC6CX86CW8pbl3o/MEwctIWhE8dkSXY+/c7rl9LiPe/d5C5yC+c9B44l3ncIF1BC4IyTbJ1hLczIUWXnwLLwHbe8LU6oSs'
        b'kJ3LQ5/4ZGH8In78ImF8zu34HIF9Lj8+57raiEy/zKjpKPcy5yOHIOTCt8+dVJByM5iUkEflo4PLB3UJUfm8log738JdwPZArUDfgPRCXMHePD3vLnqvRLdEV3bvyu6V'
        b'AkvvSRkJFJc8jkumUQbHhUoVtQchO5XHTkU3K3QroBaT1583mj1WcL5A6BvL943lxSXd9U0WuKUILHHDN8rAdYmuD63tqaLzQh+etdcTJs3KQciJ5nGi+/xHQvtDR4PG'
        b'os5HCb2j+N5RApdoIWcZD33iE4TxKfz4FF5qOmVGQ5iax0/NE8Qv+3nCP+CaxlUNURNEjS9d4L9wUoqlbzDJlEQ5VyY6XA26raovaLjV4EuXUa9lt+WEvpFYy0/g6Yf0'
        b'5Y4U9RWNS+BfegnXQ1Bj1cetEF9x31RqVerSELIDeOyAPrcRv34/1BCtdSZX0D3sNSZpHgaatSHP19BphmYNDGwXo5hQl/26su7o2k+4uY8s71/O13NuiOkOfWjr2BAz'
        b'YW7ZubxteZ9Kx8qG0IdaBqSbZHWubFuJSzm0MRTXGB4OjHvNu80FbEf8W75NviuhN7U7VWgbzLMNHlUQsENIC8OjRJdTr3u3O/V9lD4meV5ytHhs3fl1AvcwUiKoGg1M'
        b'X9Ck8WAhjQejiK6gM9IvRN9H1YQeEXyPiDuuEWL3xMUL4xbw4xZMGJl1ardpd+XyjVxwjRrjCjUeNRqzPm+N7e+gsbFPg286V2gawDMNGA0RmkbxTKPGc1ED8zLGDcy4'
        b'U7pNesLUrDOoLYgaA3luIXxOiJCTxOMkXXe55XHDQ8jJ4KHP/AyBaSYKaEQCmgnZDny2A9XgUP9d0L9gnH6NdZU1niQMTuYHJwvmpQhcUyeVpOPRADmHps+eGQ9bg6iD'
        b'O2IjpMqYznkdXJSybbKoS7p0u/SxhA7z+A7zBNb+AnYAStcT9wh9g5bgxuCpG516Pbo9hNbBfOvg604kq5GL+JGLWmUF7IxJpiyKXIdmbN6p26rbpXpHz1aoF8rTC+0z'
        b'GrHstxx1GvM67yVwCp3QMxDqOaMmINRbwtNbgmpI7rzcuP+1oKtB1+cIwxfzwxcLgrIE7kvQjXhCbYltjH1Bw/WGL3103N1FbWDCzLozszWzq1RomsAzTUDVYHHeYtwY'
        b'TyLX7K/aCzwThKYFPPRJSRWmpPNT0nkLM4QL8/gL84QLV/AXrhCkFJDynWSyHA2eyOKHDWkMmRqQEzrT29KFZq58M1cB222CbUxJE85oWkIjqZHxU3xB2Zc5L4MGKaFp'
        b'Hs80r6u4d0P3BqG9P9/en3JBc9+yq8uuF2ODTcLYLH5sFm9Jzt3YXEFI3kMcajnPdPlUqEC+fSDlgjqy1A0pXlyCMC6dH5cujMvmx2XzcpbdjcsXhC0nyUXzTKO7Vveu'
        b'7V7bVzyyoX+DcG4of27odebduVEC+2jcxELaQlCNeXV7USO7wNRvwtLuBJr783nok5wqTF7MT14sTF52O3mZwDmfn7zsetJIeH/4aPa48+X8j1zCkAvfOR8Nph7GaDAl'
        b'tYuKKKIxQlREryXixbf2Eph6TxWpPilSQ0oocuXruQr1cnl6uVRnQcWSfTUbNSKvG17CyGx+ZLYgJEfgmYsrHVW4UC+apxeNKluyX7Jv9UhJf8lowFjs+VgBejiHaDwy'
        b'hDWGTbDtXtDkcB9Elz7HEbd+N5yjqLaoCUtOL6ubNWFj2xvZHTnh4DjC6mf1pQzKo7zZ2qFmbesltAnm2wSPZwtsIoU2i3jog/t4Cj8ODa8LBXGL0IjPsUJDBceKTASF'
        b'Aksf1LfMzFHXMrMRmobwTENQ9hT6FUbzBA4hk+pyLsY4M25PyEWDZm7RmdqW2pUqMHOd1FZA4/BaejjdQucFLZyurftcBQ2PT/0ZNEOTJ7ksmoqOUJnNV2a3qiDxKqwt'
        b'bEJN/XBoXSgSKFFRCNRs8O/wuvDGlUeKBGp2ol8N2a0L7xo4CtScphxyWzfeNXAWqLlgh4i6CCzxsRpZDUktCxsXCvXt+Pp2RCTUa5FvlBdqcfhanC7ju1q2fWoj2v3a'
        b'fC3PFzRZbdTN0GXc9VLZzC/R3HmPbYREZk4bpyuoN6o7Smjjw7fxGV1y18b/rnHA+FK+cbjQOIVnnHJ9mdA4i4c+C7JQUZuZ4zYiqpGuRGrEnjpDFsx3DRbapvFs066r'
        b'3dK7oScMT+OHpwksF0xYWgstE3iWCX0sbH6KGpooFyRlpFxNuR4MF6GJx8x8UkoKNzcZVMRSCuoak3KqZnOe01RVVJ9a0lT0GxLvKBtNaOocXl+3/sBGnrLJL88CWTSH'
        b'PPovzxYzaC7L6Vy8tPnIme0f4Gk3aYH++DlQZ8Bk3gY0+uPFET5ltXjWYqjYjIUu5uhiJini+/+ylfYi1JFOn/OM9k8yj44z8JH74nR8QAxjJjnM+ywMoLnPwviZ+yyM'
        b'jOmm32cEBaOrDF59ZcbGRKVxWMUWOBeW+MJhYY4k5s5QTyjxml+xHbkBY2ZQUtN+3QzCCSuuYRATAzJRsYH+UZkB4YEcOrmpm044XygItip0Xz4xPCY0KjgzwD8pMIzD'
        b'pOKZjn4qYuyAwjuzCBgUO32HizEpJiYGPxrW9rrPwnpe91lYv4vDQh7Frjg1pbfhMYvpdIKxSgwMC44OTiRATAo3RXSv35uGWpI6meZZFlfjctAo3oO//3eRLbm4Nc17'
        b'K7ySajc5TNEFs++436In+xVjK5+yGArKaEhVMZ5QM+QZxU+o6fL0XdH3Vk30tSHjiYyEKbb7NcvfB/vP+WP/4Gn/hGl/S+KfQ/xtsb/eVHgrMf/4P/S3Jf7h2DFtKns8'
        b'fU/kb/+av1j+xW/wJTcsmEmAusEO3TCPjo2ZqejwdG0mlNV4Gk7kavskn+6qpbg77Ekhnaao8ZyBiZVM9O0J/vbMAGMpU3nWsfz56fd0DbsTz6te5T5n0hWj6C9YXgqY'
        b'MoCvkxLY5QlxebqeTlPTu6dsMaEW9FyCoRZC3x30TJrE053TH9KVcXXpDVd+fBI/OY2/YBEvIoMXnHlPR7/b+bzJ+aVXTa+u43nETeg7o6CKri8kQxkKOn+l4eukFHJ4'
        b'QhxeJLACmApIEsXXZ+RKUTLxi3FwXMaAUDIpHMpafZkpfR4GzXuBJKyC9QGzzkCqiv5O9mBSpuo/QMpkJ0glGCVIJxiLkTKxm4nIbYqUKe42Rcpki1E2MSlTReRmLrpP'
        b'NQGTMWe7qaNU5qC7MQFTZpqAqfGHBEz2WwmYmtP0SYtpAqbWWwmY2pq0BJ0E3X87AVNvrqQoB5bT/EtFZ4kE/f+CfGkgIl8avka+3MHh3FcihOz84pylJUE5S/JL8h+h'
        b'NNZryr7m/Drz0p2CvTn9U8zL6UDL8DiTjy/L0WVWpI6YMPlPxEfufy0C938yAvdpEuVUjARM5fjPky5nh58hXWoFBoQnBgUl5KyejY5z+NX0NWTkW++icJZ/FInjPxSJ'
        b'Y/E6VNb/Y4DJvNcAkwzamyenWdQZ4GEwGsaFw3QHYhwDW8YAZwzJGU4rKbBTjuDl4Qjch2n5R+F5cDhfb442nWuDbqgreZewJ3OlF4+z/OU1VOTlOTfl5Z3k/fe4Zrzn'
        b'nsQhZrzOnmVxW25z6OT1Tqr6emvQHQ1bxNShWmHVm6xKMqvf13qtY8xmVOKXixgsv8ZdXDfkni57it2uzP5XyJWRyE1XSoxcyXX/F8iVxZuY/8vJlKtZf0SmzCYljtGC'
        b'GFzwz2Appwad17CUUz31DRf3P8RSzu7cU1jKP+qzYhzJt3ZHyv/vYCJfR6JQ9IOsQgwywKQTEfdj+jZsPOcNlOSschPhIwNjE4IpRGSAU4AVx+4f5TpOpfT3yI75uf+B'
        b'Ov73QR2nWqTVP45enN2I/wC9+NYG/f9b8KJEUqkPDZ8p0VKcxQuUB3umkYFwP6yJopThw2b0g8EYrJCDHZtBZUz+5bEXDC5WsH/2w6rBPy9fvDtra/niXYv3stawP1C7'
        b'qX1T46bezTk3DW4uB4p1B/OkGe9943g12Vmiz3ExrdSy+UM4zobKUEZVaYlL1o4+J63tDfXa7gLasIbMq7lD/kYcCcpACzgDzmM1122gfkbPdWwVOfUCrljPn0Xbgxez'
        b'CXAvgemYCvspDeODcxbNUO3s4e7p06hbRad56B62kXAvOOURReHkVGEteVntBHaXvKaanI8PILGk10dzZP+FxSqenN7KmHtzChYHzIVRU/DzAE+aikZtUWsJX9m1L2+0'
        b'ZDzlevKEm/+423V3jJdLppO97VpWvcLElKn71zhtWib/fYy2RDTzGUmJM9q2uP9LjLbiva9Lef8omw1JaDHFtX+HzPZGuU9h2SJRxsWwbMZ/MPG8gWKT/Pt6jkulxDIo'
        b'N0tUkZgtqqCnkhGJKgwRe00Bs9ec5USiitQsUUUaiSpSYqKK9CyhRMpPmogqb7iK6xFmfc/6L7lr4sun/5XQtdkgapF8ISKZrUQzCEZc/YfD9h8O2384bP8Sh81mWgop'
        b'QCOfuJXyfwrLJtaF/p1Ytn87nEyZUny9aA9b5DZNQagxnCwM9pTOxfLHkLYhdTo62zsxDFbG2qaIQFARsIZYCU/FhGdpojYL9oNqGXABHmATnVanXHiZwo/NwMfAfg8R'
        b'pLoGtFKqtaDGiKsAL8ND0+gzD9hO4akr4eGS6ZOsBDMd4zoDmp6GTDNo4ABskYGXwFbjUluc67bVy8gpfbAbnCdhkVBkQ3KeCndHI0mQKA1kWkj758uU2uEQo+vgjsjX'
        b'RENMi7LBljIPRVPqHwlyUijfPdaUtvhecBk22MIBWC2KMTku1TYlFUOvIqKjQHdSGDgbFm1nGx6NYrJngAE5J1CdkEgzAEcVC2BzMNHNXZkE9nGd2KB2yhQp3O1d6oyj'
        b'rwenwdnX4saQqFVOxRjeRCBqLFoRPLgYVEuBg76gr9QehduYCM4kTt0rqqskKgwVVRk4jZ49PVcKdISDZkp39wxKq1uuWBEVJWzZyFSh+4AW1ALIccc2UJ4OB+HIWi6T'
        b'Bi+oMOAY3RpUwWrKIPz8OfEsrgESO3IPVXQkRq9gOCo3Z5eOpSoHn7BMWP9th9oOn3OWP2sGSGooGfucOTP3xUdLfxMcqbl4r9TCVo0b3lD24wdHwgdqrtDbQ+cpNddv'
        b'z7glVKjijDN4/HtBtEUKXyR85fFBtVFNeG04tKYv+nNaSds3pj1H9RjtVxPW+DQ3fql96XTilTuFPkdiv7u0ySooM4d3ytLQ6KuDNkvH1msNP95T2TCgm3ulp2HNnqaP'
        b'd4esvB4jtfSLq5efOrTZON3Iib2aeInz1eVR/ZrCGu13jl159LuNh/P21E1elQ2Je56XFm3Ku/q3D6OEW1IfpJ+qeHXm93n9upNrnnUlZJbvuT//z3f6R7/8VvBz3aKX'
        b'8Dgf0M0NvYYuPrJ/V2vx7s3vCn790dt/XmvcS9rDPrdjCb9ylKnTvNX6qlhvIB/sFNcbCADDRB53RO14JzltDc6piOGx4aHV1s+xnJYO9spGxrqGihBHZQokGNgLu2AD'
        b'YRCZSIkoRARBlAi7qVXEPga4OC3oS4OjYobej4m0dRbBvUtIa8uEfVT3kCtkYAJ9JXWet7aUhYECA+CkaBEB28vIcVzbTHABdTbU1fZMM5awTkwG6KHO+1bC03CXnNVc'
        b'JeT3Fq09b30qjxfBCdys8CoGqwzhfl+JklKEF5lRjq5k388RbgWXYDU5YA9P67B86eA03G1EjjHLSRVHOm1cHYEHkV4aGm9qwCBZX0nCLrBLpEIVqUftFsId8BTFXjoE'
        b'h5ZaR0RTvDu8/GuKUbVgwiMq6yl9nkZrOMYMEIHQqaVZDzhAEESgaZlWZJQYf2gTqJmNIHIHhzmK/6b3gPgyG/wjBv0xfF3Mfxvxp5LCeD9N8foXiD8YPWN4eEvdFqGm'
        b'5W1NS7LsChToBPHUgh6qGhD+DnW+azznjnMk8Q4Q6ATy1AKfyNN0jTG/p1YK42+wj49Ax5en5juhqnPY67BXrVfrXHwCtc90xKbfRugUwHcKuGMSQM74Tt2paSDUtOBr'
        b'Wgg1Obc1OcQrnpeULkxazE9afNdisUAni6eWRSKs87qtajW9Pmwt6SxrK+sLvmPh8YmBFc86+LrULfkb8netkwQGyTyt5Al905b0lvSG9K6k3rTutFGzO7Z+5MaQ65r4'
        b'jMFd62SBQQpPK+WhrrFQ14avayPUncvTndunIdT15+n6j7rVSj/UNWnxafBpXV0r/aWmXkNmVzZfM3A89HoKL3khL2PJRFAsLz6Nl750kknXysFn41RyxE1dKv4j/Jj/'
        b'+mQBaSGzUTFinJh8tPaJwYtVL+T0Cq1V0zzp9HCCiQn/v1ur/s9xYXze4MK8bfn2L0NhDEr90I/MEMc3kTBgNHyaCvN3mDCgXY+8ny2xVpkCwuBdHmcH0EdbEujDlKMZ'
        b'wzNMuAPsg4OUmexKcAYeIFgYDIUB59F8vA9utSCz9GZwEF4gxBca3QAeBAdpoFYa7CBSlGHymimkC2hLh8doYIwO+gmwA7R6InGLMj8O9y21XwtPEMlDBY7BI9zVdDg4'
        b'BwszKO25C0lcgbAP1IqALnNBfxkdlttBCkDiiSSF3shIEc3Fz0CDIQ/r06hXQM2wA1RgnksJOIUFRzTrrJtPiRANoAuWT9FcQJciPEODZ6xhE4XxOC4F94m4K2pwN41u'
        b'ZQbPEPsloNXcXERWmcGq+MGL8FxienEfbtUD+HIOX4bRpRTPI3ZMgp6dBqkQigqo98AglQjYT4oZDoEdSDYV0VLiwKAa3QseBwMxU1SUDnB0I1H8ozEwDpTORqVKfDwW'
        b'gX1TWBRwgiNDd18uosfEg/1wv1wxEzYtxQq1aOaAl0TJgdYlsIJio2AuSqwpZtkcBZdm2ChgJzwCOvB+STwN9qbEe3iSgCHh6VNoFHgFHKZJRzAWoHm2m3qIPRoecNBe'
        b'xEaRQ/I1xqPMc81v933O5P6C+rteU+jltL+tMElW29SYbR5ukbly7kcfLZev7rnw6fE595RSNXLShzq+8tDurCoMrkzXVAntsDGuOs4+3toqXW1pbPl42/WBqm27Tzvb'
        b'GBsbW1nvNv7Z8Nuxh5EHyiadXlz67v2TTZlOHtwfz3+z6cFvxRNlx4YsjpxZVJQz8VFe7I/VK+u1juS8eBH/rrdGmvf+fOH5d65XfKw26VSXen3Xk4ETqe/e+uRopUtp'
        b'7sUmHc+T3ovfizBf0bzz3pqzNy4d/VPx908LPy4rXx+h67X7i1ulX0itSewcl5B9vDu/+YMPaJuvrQUv33Mt/+D9O+mtya01q1gfsjc0FAlXFFxd9DLNW3Mbw1A4uOOd'
        b'oe3ciMcO1o8tEh9f++iQ5GPu5mPC7stFk5yJ4/lbNX6WD27/Sabl/e/Sb1V+Vh2m8GvGHv5BteTcAx8fic7wfddtYNMZ9tL31wq7rwh8vNoK5salyFdxFZddW7Mwld7T'
        b'v1h+daXbj20fbftiwe4fJG4W/qnj+aRvYhH/4qSaxJ65tHcZY/E/nv6uw6T4+5Gu3iUjqT99/bvRfYb7gZX5X5le8584Gaj21UjcTWuzxnfmG5QvKNq5oIi5em+CzRLh'
        b'OpsEmx/e2Rn1zWcZfrIr1yZEZn7/NMfDyfLDhAVHP/T1WGCN6SLW7ZdLpQ+e3mX1o1OKjNbl94atvghb+UWY7+6k4DrWX5ocrRsM91dcVV/vPlTxY9v8mk+/L1wwWSBY'
        b'oLa85ec9D0JXMjT3fX9qyGag3PhiwLqKwtMtwed+7RxoGLpGO/yB4dZvt6vdPfe5UVWdj9KPmYPF2Ya7+Hs7Ha6d9fQ/y/rVct7dS9917fmb1pDat1/E1WX9dllHp+Xb'
        b'dI/02I4P99UuSXjV3/PNuGfjYdv17xG+SIZt49y128o6jBpibr9YZ7f+iy/vtFk8EowXBZS92pPvUu4rF7/0ctPv6/Yuqbqiyf6tWq1DO+LcnHOXk3Re6h/atu369uZ3'
        b'Pn6Hez79O1bO7/szPr1QOu9xYvP9lGNKtrGyErG/Dya8MIeyw2HZnyePnbixN3PXt9Zq6pcnrea9/9J1UyRL8BfeNwpV216uPfrY59HmgeUN1fr7V8h8c8qrue0d7uPo'
        b'8YVfF8XXj60skFmzrEi4OfJdb4mGgt8Vgx7sjH/AjH8gNSGllnj/9z+HfWJIv2lZrV4Xy/RKCx8akPnNyS/w+yzzV45D8J7j16YRq4u2LlqYpj10RWfjhZbD955Z1Eu0'
        b'8L62yq6v+dJjlN+bten95wUu+zwf33P3noxpqTnecivAzTux9n69Z8QX/V+U1pt/KF1a79Fept/xZ722vU55ekN7bwfp9O91ajHMLa3f9eOWs+1BkbfoPUaPLKOt5R91'
        b'rfzo0061xF+fmHv83hLY8bUXYzdTbXPdKXPfG1d2LJ/37naPq3tfqA89s454LCh+9YvO/PsvvYPGyj3HXJN/vBtumPww+pXZ8/rvoq5/9qviuigz58SsFz68ZCPtAvV3'
        b'f6b/nHLgynvaWht+b3ikveni9jHd4zppGY/Ojkqs/SXgxxu3JlssP16/1nQzPb5gc/lx49DfDx5/79hfdZ80Ltu/RfXc2vtp6zrPXhz6ML/w7JbOj149jba4MDia9Knc'
        b'zgeGd05uuHH6ZsPYV56MDS0PfouV7lt4xvyv9474rpJ6+c0SyaTCw784dN7+NuX0hZBHf7vZopZ4PLbj15OfSMlbjv7+uXrB4Ir5N9SjC+ccf1CpGtd17252uWrvg/E/'
        b'byn/6fnY2mruuf7SQ8fijlVdeyWxz6Na/4EGZxVR2rVfBXYQXAhZdeSXzF53lMEmsj5QDF8/zQpBK4NWCr4auo4srdbDSlBtbReuDypngUpZGX7zKUXqfZEyhBUixgkB'
        b'pyXywIATiWBLHBqwMd1jIR3zPWboHtagnOhQhlj4WNtNYT1sojHYQxoOkrBLkBQxxhW3fIyhHq7g7Lw58c856IZsaVDHtUNSBxgCHbbFnAi71eEYAjDF9fACOyTBIKh0'
        b'odYy7RvAxcipNZqkV1ImwwqeDaeUGpvhYTtUTlP0jgtzMMADHnWlNFTPKRdPATzQyhQzPBhloLaMCnqUaz1D79hshPkdjFjY701eTjkWaE57TpM7dJAccwm0x1HZ2puF'
        b'pnQRvWMl3O5GB93wCp0sSrPBcdg3je8AzQo0aVlGKgpdT+Ez6sDpgBmCR7DaFMODWQIrNpDiLYJNcCwyQoTv0HDFAA+bFEpV86g8OD3Pb5rhMc3vyASV1OLwiq9iOqgX'
        b'ATxm6B3gsh6JQFUxl7A7xMEdDuCKKugAu0jRmKMFbcU0fAN0xdKkFRnpYJ8+WbEWgsso8hh6jjolMHSBY5uI2q7fEhMx/gZaPR8TMTiYSCQ8DfpJsc2HrXOnwSBD8WRZ'
        b'64falIgY3IqafoytPGolEhGwHLTT0bK1H16gsCG9YBu2TEXU8cV08WGVX/YaWEvdU+HnNQ34oOgeLospvgcYhYcoVdb29fAcIXxM0z2QJLvfL82bdL9gUL+FAD6wyOyA'
        b'iT0cCvJhwGKB/iJwkepAI4HwFKF5zJA88uFubxZsp57lLDi4FJMvxEEeWllFHumkfvXAUVuRpncBOAAO0cFeKdBBaScfhrtzCLpiMRij0eVo4JIU7BUhl/OQCDZqIc6F'
        b'JhyPS1okqOZKqWmKRw6sNqCD4yvgHhFjAO7JNFs2C3qszFTfKNpGWWcP6+LgBRHHY5risRjsIRGHgk4lEcYDDujTZBwZoCGHRSp0oTWcgXhI0GjS+Yx8cFSPKqQTGmhZ'
        b'gSkeYgwPcCVjiYkOCWvgDnejJAnCA56JoigeY2sodWm4CxyV48xQPM4EEJBHGNhPsuQKj6pPczyC4FaMaN64nngxDGD1FMdDTgpW0kH7OnCCKoZmMGqjggYEijEvInmA'
        b'o7CVKuC2tXB4TeI0y2MK5OEJjlOd/hLcI0Hp74tU8O0TZHLsKcrQYViXh8eKzYGYZkADPSUJ1DB00RrzG0UgjwTUxq/QdeH2FdQwVGMCm6dBHmAvnZC83eAZSn96wBY0'
        b'T0n0QaCNztaB50hOF4GLoGaWXbkUZi5sKgBDq0lOC2CPVSaopvI6xRmwU32OOY5uG0IJygN1p8MUkWE2y2PPFD1iP2wFreI0D4rWsVAWwzxUUZkQXf4uJOJjmIcI5REH'
        b'RjDNY808agOucj2aazDNg8bIgI0adPtQcIXUkmGYEmZ1UBAPPIqo0DOWrSJFmaKfQTAeGOIRCLvQ+o+znkqrIjR9BuTRDobhMQwOaDAgz4zqLmuK5LHaH7M8GB6gnE5B'
        b'DQZRugQqgLoO3lMeQnmFbWBEC/axrOF+2E+1j8ZVsHdq8YI65i5q8dKJRi+yKC23mk+02WmMJQEJdEfY4USmC1YiGif2K8hNxY1brCzYzwBnTGAfKYeIFXpyIiCBJFrF'
        b'ndBgGDMVqOZxUDkd1rpbTw9YGB/ig1o52YXszIKDXNEM2Ql7ZdAkQ43a+l4sUGcNB0i5KGrDM9R8g2sAHgM9hCBiLEOdtNifCnbGgJPTEJFpgIgrqKHa7h73ZRRBhMZI'
        b'gTX2dNtl9qQJLIQX5DE/BK3/z2CGyGyAiAFso4K3OKHpiAKIbPRFw057FIVkskKtdDeVrBjyA01Fp8zWmJACj15QMAP9CMeMjQYGOIi6ZC8BW+Sjcesk3lp+G++jBLZi'
        b'5Afcb0kSMwF1c6eKaj+4gIqKRlOG29Ck2gLLycTLKfDEDTWSIwOrOOEifoNzmDYoZ4Uuyqdm12OwG1ym7sJPiqZWJBkcZfgXgj5q13oIHPYmhA8xvge8sDQaVjGoQa8W'
        b'NoHh1eDC9EsQ0Z509GLS7t3QDYdFu8EsLSeyGbx1AVVR28FheIqLEo5FTWlfKThtjYZi5TLmRmW4n2qfXfCyszVqgUg0i6bDk96owBoZGzZCigOhsjyei+3MVGLpsR/W'
        b'gi6UAzpNRZ25aQ7Y+Ry/aAHdATkz5BMx7Am4suIN8kn2FkqekS+ZJobo5omYIUxwIsaCtGAFnwR31LkIOGiKGgSOi6hUq+E2BxGwCm61BfV0UAOO51MQpxZLcIAKJqIi'
        b'SWpJSyQRaF5YGNg3xTMBtZ6zoCwUz6SOwmrAXclp01AWZUMRloUJ2mOcSAuGh4vZU30LNbQLs2Emm1DHJpPuVnjWQwQz8UDi9AgSe8JyqP7Z4pAxQzKJTqRJ0xjxSNIk'
        b'4cBecCB5imNSy4Ln0HDktIWIIsEm4CwacDaAgxzZiNcgJntBJ+k4kmmgTY5DA32gn0bXocGd+HAUea1QAWvh5SmOCTwLekUsE8wx2beBFF8EKpuBKYzJAkfYiKFd20sJ'
        b'j4MBKmMwxoTG4Lgh0dhA3YcaTk6i0bpDjGJCdQFLcJ5QTEzhDkqOKIbVcrYUwSQH7MAQk1YkguDS4OZKTTNMVuRhigkDHJIDPdT0OLpx4RTBZLMhZpgwwuBWexLQPWgR'
        b'HLQVwUs04E7CLzkAO6iGPxi9GfNL4GmOXUzULH7JCgYJrm5omwv7KIDJNL4Ets+nCFwHN6mJ4CVi6BJwVMIDnKLe9qyAFbBCDF8CT8Ht0fQQJDodIBWhuxacwvgSGlog'
        b'VMJLdG9n5EF6c++SwClQCahDc5E0rGaAcrAVHOBo/DezSXDV/B0wCdH7uq/x+jsVMSTJSVnqVUqu9/8tkkRXqOXF0/J6gz5SK/FEksY2+jdSRKz5WtYCLdt/nCLyNqd/'
        b'DCCidkTx/w1ARJSgSKW3Nb4zqS2py7x9IXpy7IbKootONEfJy5zTSgI9dxEYoDWkM7YtVqDn8q9wOWZ4DoqNihjL0bZFaOHHt/AblxVYRAq0onC+/oPV+A9W4+9iNRRx'
        b'znH30BBoWeIWo9CoIFYiItSDmPpzUu/C7oVCWx++rY/A0he7ynTLYDX10O7QvpDTsajEOFaTEhJm5pPMabVmppy2zmQ83QXjNVwIXqPgv8ZrdP1dvEZhW+E/ideYlGCi'
        b'upT+N3IlIhojWovxq1yhhT/fwn+8+FrZ1TJhaBo/NK0hQqC3QNT9cWQKbQq4IMPawlC+0rvThbbz+LbzUO74tsEC0xDsF9kW2ccYkeuXEzoE8h0ChQ4RfIcIoUMi3yGR'
        b'l5QhcMgUmC6euk9KYOo+KSWByxf12ifKNH3DfxBJoW/Ykt6Y3pLZmCnUn8vTn9sXeE7qBU0CPz26oPEm7XyaqAQfWttiLEKvX69flx9qiha2nUWtRX0SQrNEnlniqOPY'
        b'3PNzx52ueV31uuZ31U/glSg0W8lDn9T5wtSF/NSFvEWZwkXL+IuWCRcV8BcVCFJX/jwxz/+a5FXJ8dXXSq6WXI8WhC4QzEtHFYMfRMIXg03+Q7D4D8Hi/xnBIo3uiQEW'
        b'nlP8irV0zK/YzPxfyK/4/xaxopRJESsSKGKFPJJX+Qz2eiu7v5iz19vb/Vt5FZ+gS52UGK8i0/tf5lXQKVQF4z4LK7vdZwY4BRRb4URsWKKTMsUOGADBJOSIYkcso8sm'
        b'BEfHJgVjvkSxE0WH+BTTIfDCl6JDYBKEO/ZR/2/jNnAJSvZtyAaq5LxYogtW2+Ye/TvEhobMvwtsoLz/kNfwVu8ZXAPlrUeBHaZxDNbEP/TNxG3/S29x0oKDiLQQT+cQ'
        b'0kIKRVpgKhiJSAvo2zNZQkjo8r1q8gZnwYxwFszEOAv4+9OYac6CO+YseP7zmAWcQAJKwE8hh/6Mhq84gQSUAP7+IoBRwMCUBXx9Rq4UZQFvgOQWgSFCWYCVNhHRdqvD'
        b'o2GVDd0ZbEfL/jGJlYzwWSeKFEV/Jy1R4/bWwMeiXgMs0DBgYRozgIEBagQlICtCDCjNctWY9Utu5pc905mJwQcJzLlMKskEyxRGCjNFIkWSKNgopCimKKWopKimaDjL'
        b'J0i8Bh6QIPgDSU1aglSC9DT+QIq4yiBXWTFXCpUgh1zlxVxliKsCclUUc5UlrkrIVVnMVY64qiDXOWKu8sRVFbmqibkqEFd15Koh5qpIXDWRq5aYq5IYxGHGVZm46iJX'
        b'PTFXFeKqj1wNxFznEFdD5MoWc1UlrkbI1VjMVQ2VrGKKujMzwYRgGtRTJJ3pCabkuwb5bka+axLlJuoonEyKPAqjjOphDqkHc3KHVoJFiXYKrUQngUXUuTj35QP9o5OC'
        b'RGfX8udJ02hZ5ihdWaw8Ie5F0R2mVQdKirBRdi51j6uTDfXXmZg8x99cZKfOw3Ht2P5imj0iRReiiCtSn0G+JTnFxOp60ZqcYvSLKytudd2GnZO1dBm7OGdVcQ43p1As'
        b'mJi6ENYfk/0jHQU7WdmYIqwSEp6LckiO8K3NKc5hc0uXrMwnShL5hWL6yEQrA3lnof9LlhXn5MiuzClZVpRN1EhRHooK1uSQM4CleIemoAxrdMwyE88OzifKFJb+HJGW'
        b'W0GZLNa2ECn2UIVmLyqzqZKyYVsGcNii27LY3Bys0FKS83qB4jK2DORgBeYsMcUekcpNUXF+Xn5hVgHW1BXBbdHjYa1i9BBcblYe0ZPOoUzdIx/qydjZOatyCtEDFlEZ'
        b'JBo7liK/AFzrK4u4JbJLi1auxNp5pA1w7GQ5zPvMdSsL7ksuzVpZ4upyXy63qHhpTiYpyZilLLHhCc9E5NTmNvTFW35KN28rTXRuUxY1XDk0iMiLhg/lFBpqunRnJdFp'
        b'TlaiGBZglYQuLYUldppTYta5TZafBDnN+YbrLO28zYy3gARmtXgxhoBItwg9K6VWND86SqRXg9teFgk3cwIUVQXR5UL9g1L4ssyh2sMfdRYxBXtSkJ5YT3tpFupei1GS'
        b'iyl9HyrwdCDxdpNVSKm2ZWfnU9pZonjZ4m0Gt6jVpTmi/sItRY19uo9SitCzdNDWLstHd+AukFVaUrQyqyR/KWlVK3OK80S6Q2Iq1MWoW6wqKszGJUJ1pFkdYurxxNqH'
        b'J9aPwypwpHOLK/LlF6ICzKKiobSyxDxJuqjfikdPlOtJNEnrgkoKuOxCjAMgQaOxMjl6qGkSwPQjUzGJenP2WzJNqfrlzvSHpWTM4lK3Yt29Am4RRRdAT40Gr5x1OUtL'
        b'p5gLs8cDS6vCnLXsaWaEh52DFWf2iWAp2psngvW5eJM8Uzp9kP/CmnOqhHODM1zN+WignEvL36SUKd0REUuJC5hrAus2FoBBWAdH8CmBEg6s5IBhUM2Bh8AAICFAJ+yT'
        b'Bh3psIvYU08qxTYCi6TBEXBaAkmsCzbTNuuWkDO8sB82g+1gEHWRCFUvmhfYL0MsGnrYw1PYur0trFgL65wdXBk0+U2MFQHwJPGG1TbmlHdbPvGWpMlvZhTAnZqU9054'
        b'3oH4h20h3nSa/BbGynhwuRS/MiwocIHVlP5QGL4pHlRHh4mfRgpSktIsii9lo3s3wism1NuQeFs4DPdEglo4yKSpgr1M0CIHK0qxGUQwlOYkfpbakhyZikNxojJpjIqM'
        b'tGWs9gHNevAyqFKHA3AgUg1URcrJwgFQHZGQSMvJVZ7r5VSaTsOg/F544S1xYZUt+4hkS1gZBvckYjWpyGTYN10B5Lh2bLjEHLPF8IQs3Ak6JCTg+WAz0M2hBa9Vg802'
        b'IkuLmjmgibuKnBeAu0A3U56+GO6Koc7dXoaHYRV3NRyQp+Njzgy4lW4aB1tjSj1ImYJT8DAuVKrs4O5o24jYZFKAuIxlwZirKLNgKxykwZYCOdAFuvHRY/IGpjqVHokC'
        b'RmBjAaJjSzpwf64na7WnJwX7OgPaQdPsFGBfEkqERjPZwIL14GImdey6HJ4EexMtWSyqbFCblqHDy/MZBT+/evVKOJ9Fk476SYo2b3HB7QVOaOFFrI9G5+dxYZUirFxr'
        b'R0xFRcXYyVhZ0mlOsB52ukpagwY9cmK5SB7r9CCPRG1GNH0uqI1AEZDzAeXwiJZ4FLLghBn+S6cZe0oYy8DL5CC1HxgulKOcE1SY8AIddHssQVHgngN64Jk1s3IRbrU6'
        b'hgP7rcMj7fC5tvT4FNggrQcOoNoi7z87o5XhoDVsDxPdIO3KKNzgymFSvntARyocVFpVTKdFlzHgKN0cbgd11EnvKnm4Q066eA2qysO+TBbdCrZ4kFB+Ubh+5FejQLBC'
        b'igHP0E3BCDiEsoh9y2AFPMmFw9gblK9jgEt0DXBZjZQ7rANbt0wF3QEuU2FrQW1+1TFA50YhKX3IJfNu6l+Wq/qrHft0YVO0W7Rb/n43ztmVl9UqU5af6rf9XTl9xwK9'
        b'3FUH50TU3daoW/M0xV/NELyYs+UXz2P3snPnelm4R8c7KK958djjwdpC57y8wec1T7olQPqlT/rDf77IH6uFOkaDO2ITq5f5hTS8k96c9Oq7M0Pp+m15g0kL96X+crP7'
        b'9hdmV2/e3u/B9i1/MbzxR9Wmu47d259kezLvbLpd+Lv/XOvSNNseuZuN3x77WuXr43Z/YX9UsO1u2l7XBngyNaH8q/RzLvcHooZfSHtUdD2w+6X7yYW7kyc+qi4ZsLvG'
        b'iT/cfK8uI6W0sej9BvWImNaf13xStMd1d6RzRFOzxcXgipt1GdHBzYf1LDSSeno2qET9rFqi83S0+/3x3vCvNrnF3/VYuudZ2J5g5z0KkTkFMdkFGaEXlj+uOSVfZKN8'
        b'/Z2Bxo6b1uyugu2lvwEVm89V+ra15F9LuR9Xss5U4atQJ921yr19689mTPz2gcovc3Meaz36s8rIl5dVtmjWnTUZiHb+3XFw8aN3Ap3t2XKpyPmVSdBPEw0rvgtYGLtn'
        b'de+N3zY9LfFZUt78s9TjBA+/vPuJ5V94LS15Blp3ffjV+v2fCTo+5TZ80jP+o88Bp6/fXfO1XscF9SDFNJlnlyR/SzjmtCjwg9TTv/n4bl9i887u4ChJ38EsfufuB9uY'
        b'fw24P7KU+3+Yew+4qI61f/zsLktvAor0XpYtlJXee1maVFGKUlRsKAuCvSOCBTvYABUBG2DFjjPxionRPSKexZjEmGL6tSW55sbc/8ycRTHJm/ve99739/6Vz5yz58zM'
        b'eWaeqc88z/f5cZVV5vTHLnbcodsRH85xC+rZ6Rz4DkN/JYuq+cz7Z2vOjklQBAt0XWVlujtGCwYf+SnE7xW/d78mkc+/ElZgN2tt7bf9iiNNGlGZVXqLhRF3+QsLp26Y'
        b'eeJGdVRPB1M4v0z3lbCytW7t+0/ey3jBzIxqv3c8KkURWqeRdXPf8a6sz58bnh4Vs7jub8aNL2uPyi0Ntpr95LB4mX+huLs8aOulqmcbmc1LgxX057u2Mlfu572/TJk3'
        b'41be/gsfOQTc+D4tSJH39/O/LhvMm2Fj/rVk9Cd1iqGGlAfpLtcKXq2nUzRdys2nJD8b59U4oXl7jen7W54s/vpp3fyQY6uPWr/aL+3vWfjFd8nFEXrffnNxAXPvVtpX'
        b'IX+Z/c3NT60Tw/snPnwW37HlvTtHywv2VeV+bBV6/tPPoyoyg7K/2SFTmtxy/OjYoSL5A/76TeetJywbbCtc/b3aq69uvCv75GP/n/WGBEMnFXsFYawCwZ6IdKEkiYsN'
        b'Z3u5oIMjA2vAKaKmtQTWjWNVX0aOqrAH7LaJVYMN4BBYR5Q+wrLhLlAPuvAkgqYWWMeldMBFAehGPdgnjBxvG4HmEmF8oga1aCIX1HKC0RC0itWeWAGa0UQjeeOgD56H'
        b'rVxxIVjNKlwdAFfAJuwDiKhsqk/OByu49gEoNZ5TLOH5fDSar3NPwVaGS/HgwnXThadYZYAdfjPwgTzcIFan1POnFnMdwFnI+hvTmu8rSxHHi7AqiQ44xaniwosxYDch'
        b'yWWaOevlkFVNHg9WsJrLcI81KS64ZA9qRsK/wPpKlVUo2GjIKpYcnaUtd18ITr5xpsKNEyexvvFWmE56o4iwBKwXceD2WNBEtLSC0Jy9SxgPjqEZIlZDbRoH1hTkETWS'
        b'IngAnsF6M8TJyrCGgjncA9YL1ebBvVNI+pkzwHp4MjEBHOWodADhXiFhJlxVWoWqMSFJJsbaBMmwEa5UZeIIt/MDvcBl8p0J8OIoOdwQj5V3ZfrJYnhKhjW/d1jHqIE2'
        b'cA6cJ3U0GhzMx7q2m7QiYa8qkl40F57T5BBVXFFsBfpYsliUhL+l+g44Y2TrqQbb4C5fVrXhEFyXMFKjAlyBO7FWxeU49n0Nn4PanyQBO+VLEsUncSj96Tw/uA9sJu+5'
        b'8AhcT1ZPazzQWohVJdHz5mk4VLIqsC1jIFEixzrU9RqUupYtaODqgi1GRJdO4grWyYniT7I2byZnMRe0sU3uCKrDlmF9SXBEjYv1JX3gHvI2JgE0DmsAouXXRR7RAIQ7'
        b'FpNPhsAWsJ0oshF9Sj7cBQ95c+D52GrS2cRw5UwdiUyCkh6Ca3jwMAet8gyJVSxamJ0CR954OGNVIqXg5LBWJOoX59kG1Axrylj1RHgebGH9jPFgO9vy9uoXvdFqHAUO'
        b'yzn58PBi8vXoBRa4O2NVyEBQw4O7OWBjTCFJNn0CrMGl2iTkUot9ePAkB7QXoSyJjBt11jasBItqhs/qA2uDLvLKzMRp2AUn1pA9b+nO5bixupCwAe6FB1nVUbhbRlxk'
        b'n4JHWeWi1RXEXnuE9mgGXGkEjvNgvRvcxOrBHYDrpmBya7nDem6aYBcXrMtA3RQvmEJK574xUhg2UYBb4TqVU9ONPMIvOWxDxWEVjvFWgAdPc8BxsC2aVabb4evHvgWX'
        b'YCdZ66pT+sW86BlQpa22dRYmtWo+PKU37826GawDm9zhxrgkMYoP9ixNj9bUBzWwgTBIGzF3tVwId/G10UpMwKE0lnDHGUFW/3x0KDwsF1rCunK21WuUcL1gjQ/pNcWo'
        b'qfagMsdjZbMUIdbNR6NfF58aDQ+rjZrFFmge6g01OnBd5IIqVQ7gMDc4HHawLlyF8BzJwRSsRZmgdqpB6SfzwlKlrNu0erhGW56AjRXsUznwLMcwLpd9UVcGV+oIjKdT'
        b'rB4Y2AzryOciJ6m/5c1KMIbogC1JJONNCTg8HfF4rSNnWBe/A15gFdrOwu2WxA8bBY/lYj9saGdyjjT1CXKwAtGIqIhHPZOMDrDBxj0ObuBRDvAQ3xeuhsdIaebyiuXJ'
        b'ApVxhgzlVDvF0Io3HhyWkK9PckUbCgHa9iwn3i6xq8sdMaSWjcCxeDlbPbAphQfWcBaCTlQisn07DFcECBPEMtymxW7JaFgxmMabkgJXEMW/xVXw8mvqQI9MxrofQ5NM'
        b'Mp8S5PPBbmtd4g9OA/WM+ip4tugP2kaKD9oUBoLj6skOhSodbHhRprI7gOcrVeb0q+zYtr566Rwd/G64GfuWjYLneeDYQtBISC7jg26hLAt24EkHzWaa8AJWBlsL2P6k'
        b'DvejbUb9iJnBOWXY+9Y20C6w/H+rJ/ZPjnlwif9AheyP4M9Gj5RjvY19dozPqpJFRaIB0rqxqMWbMRbcMRYozS2bnZucFXbBvfK+yAHzuM2RD4cfBfUW9jkMmMc0RCod'
        b'3RvU7hraDY0xa3RorNg6p4GntLFvUNumq7Sybc5uym7Oa8rrkA5YuXdzBq28GCs/2sqv13jACh9sWoWjiNrYp8vEpomsXheKiJ89NLFW2AYqcehPwsgnGmpmRg38J9qU'
        b'vUu7RavFIavN8ejz9s6bZQ2RD0ytG+WMqetdU1eljQPWMWFsxtE247rTGRv/Ozb+SoGoMWpPwgNrp5aiAWv3Rt4DO9cO4wE770b1obFWTw0oe/cXRpSFk8IpYMA8UGES'
        b'qDSzbDZvMm9QV+mgMQ7jaIdxuKS2SidhR3hbTntuay7j5EM7+eCn9kpHtw7PtnjGMYB2DGAcQ2nHUMZxosJxYp9Pv901fyYyk47MZCIn0pET2fqyFXdM7ZrTOYeRhNMS'
        b'rGtCUOWsHFhtDU/aypOxmqiwmtid1Rt+Oqd3cf/UwdCMQe9Mxnsi7T2RrTeHlvC9Oc35TfnscTNjJaWtpGwVs4l7Y/o8L8VfST6XzAQl0UFJTFAaHZTGBGXSQZlM0EQ6'
        b'iM3I0r7Fc298c3JTMmPpTlu6M5YBtGUAYxlCW4YwlpG0ZSRjOVdhObdvfv+UawuuL726lImdSMdOZGJL6NgSJnYmHTuTiZ1Lx85F2Wm9RZcHdtQzgi7CXDuXDk6bWbt1'
        b'qzVjJ6XtpIydH22HX+krrW3QRecDK4eGaKWFbXNAU0BzcFNwQxQ+R9dq0sL6b6zCYodjl6BT0CXqFDFugbRbYJ/ade2r2ndNEwh4woQB6xzF2BylnXO7+UHzRv6QhXVj'
        b'ZfPSpqUDFpLuUfcsvB7YSxTu0wfsSxWWpU/5lL3oiTo12mynbIusVdpS2b6wdeGB0EETr50y1DisHZ8YUnYumEFD9u7d6t3zTmupDsw9YmmPWMYjkfZI7C8esE9HcQwI'
        b'a7vTjs1gJKG0JJSRxNCSGEYioyWy/owB2zScz0MLuxa7vf7NwXuDUSM2Nd85f/P8YYAJN9rUjTF1p03dFdL4e6bxQ2JpdyRWCDub2JPY53Dd5apLv/M19wFxWqPa3bFu'
        b'SgtrXEWMhZi2EHePuWvhq7S0ZSwldywl3faDluMGLSW4TyxrXta4bEgS2Bt5JeZczBXZORmrWcYE5SvQX2o6q4zBpObQqTlMaj6dmq+YXDwgKUEdJ4XtJJaCJ0aUm6Qh'
        b'6q6J82cWDq1RHWO6ucfMu6w7rQcc/RgL/z8pSnfoPdOIIQnqkWeze7KxckKf9LrvVd9+n2uhA5J0XBLhf1ES9zuW7t1eg5beg5buuCRLmpc0LhkS+fc6XHE+54yVW5iA'
        b'BDoggQnIVQTk9hfdnnpj6u3SG6W359yYo8gvHBAVoSIkqYoQgIogdMdFcFFa4bam/bGxmQpomTEV0qbCjgTG1PeOqe8DaxeFa9KAdbJibPKQqV2Lc4cjKsodU3elnUu7'
        b'VavVAZsm9SErlw71bpPukm5dxir4jlWw0t61ZWyj+gc2To28IWu3Dmlv1F3r8EY8JjZXN1UzNl60jVd3AGMTcscm5EN7Yb/JbbObZoqMbCYjdyAjVyHKG7DPV1jmK739'
        b'GtWIaqu0PaQ1ZGCs13MtytYZlcDEfARyhxGrRfEpPtD/DAefq/33lSr+yeyCPzACyuN3c0q5K5o4UjVRTIxS8cty6qe8CA6HI8KIHqLnOPgXNDDkGGF6v7oXdUInmPc/'
        b'QqKc+s+QKN+eAodhKM+hD4+AofQcPuUkx4ci25JpEls3fAQj8fCWDgPn/h6V8n+OnXmX+19SXO6GKvgipu8ed5g+C0yf6tjOtrT4LUr+R0RMR0R0cu5rFrBnGcV/RssV'
        b'TMvZ13VlR+D0CObcVPYoBB/H/NsUYUYKOPf1Cl6fZBaU/ilZAJPl/LqKnMNtK+eUzqss+QMMx/8QbboFwwdn/4S0a5g0j9ekueEak1egKiNHcK9P3/6T5JUL/0mL6n+7'
        b'xUvSyzBM9JypZQQn03ZKYVllxVso0/8+XasxXYeoP6frvbfpsngDak7Ql/8zlXP8nxBxCxPR/ZoI8zdERMRH/odoOPlPaKDfqojy09S/M77Ycv78Y3fxx+w4wwV2zfgD'
        b'bO1hrNf/yGCDuo82geMswGCZf0Yag+cWTZJjY0Zzwa6CEQ2DIG6yg89/pHUK8BBIqKoo+zOa7r89BJqpUFX/Q5RMHx76CqfMwnoGBWVzS+b8GTkfvj30+WFycBr20H3W'
        b'SFWY38Ln/sfqTf81tUWzyuQlf0buQ0zuXeotcnGif4tclUMS3efFFOuPApGslkVl8aW818Bf/0mnJBj464x2PFZQwmf/REFpyqxZb53vY12JWSUqXYLXGhAYkzZtSqmc'
        b'oPymoVKVzi6JLi8vK0fRS+a81iIomjIH49YXlrzWRdDGuMFzVNDBpXMIbqy8AnXRUhTd9Q2s7Fs6UtoqlOXZpXKCdiz4DeIY7lkY53OkfoFGpR/6IYQHgoZNeeFJcEw4'
        b'DERKUEhTYW1K+lvH8GCrv/YysNm6MgqzYhFYLUSPE8QYdUEgSxofR847Un+DUZYOG2CtJCEJnExLxRimK+EONcpjtn4g2OBYmUhhc1A30CYDx1zjkiTxSeNT4YYMV0RP'
        b'gyTJ7TdoZ3DH+Di4yZ0D1s0sNgVt4FCOAHSMmcmlwPrFBnBrGuio9EEZVoB9vjJwAmx8Dej6drFG0oNoAWsma40RS5JLr/76kit/hjJI+NuPJ6dkFTZMmz5Zc6r+5D61'
        b'q6K6MDNOTWpNmnOw7fxPiya7FmtOBhlfXf9M3NfXd8NWIyOzbzLQHDUY7lPvv5yf3hztz4vUNuCt0o3UDUwUaR4PXTWq+MIHxuo13BqPGko/8dXXqQGf6/avn+wc3RLQ'
        b'OKcx97xo18v1YSd7Pd6/MyWye3Pu8kLnVBcD/YKxLUNgdZ744PWaBRNyC2+u/1A8ZQK0NpFN0e2bUBhV5xS+sucdTanptwtfeBQ6O60PO3OB88MYjxrPLI9x3e9Kq+UR'
        b'3z5dSj1zyPjWLEpUG202/UqQX1sxmLC+SffQzab1e76iVs90358GBRpEkgdqwEmwXjZSzugelwi7sZzRxkgNNsKz8exBw+4CUDPcdMpgG5Y1EzPwxPksDsEZbecR2QxL'
        b'A8EeU8pRyA+ymUs+BzeDAyG/EUmDdrj5NXIOXD2HFeCvg71wDQuu4mdDUXwMrpIBzrKC2PXqThjVJUeOzbMxqIt2BXuA01oOD2LBJE4GalOIVHwUakccymasGj5KWCfg'
        b'/9f7Ij4e2F4j8d/Xw6qKBcM99b75W7uMt94RaZshxsD8CvW3J6mxHMpkLGPsSBs7tsqvqg0Io6+q9dp3xR+Nv6pGC6MHXGIGjWP6HZmEXDoh965xLjHwjBowj1aYRH9g'
        b'bt0QoTQ121m9s7qhesjGvsWruWpXFZFqTFBMymMmFdKTCgfdCwfsixSWRVj8Ub7bt6Wwvay17K6FN4lXoPQad9a9x/2qtK8c+vZH3I69EavwzPiBx/HI5KANnEMWcaOc'
        b'xXloYdXs3+TfybtaPiBKuFreW9KVezT3ajktShhwld21kJHsZP2Ft6fdmDbonjlgn6WwzPrAyaUxWmnvskf2nEc5uz5Rp2zs9mg+N6MsbF4+41OiGM7LZ0aUWMZ5KcdM'
        b'X2UUrc7ZbhIVpN0ZroNur3qHS9EFuppEc3RhULg2+sFuetX/3HRAjsezkb4SshDHyrNR8CleUHhTrKFAZCznXzQSwGPI/29cYakm6bdGb15y6fL6sXw5FnQ/+kHtjVOr'
        b'd3X3mHXtppx9OT/kovUEe2CzBnTrEKhflduRVWAbey4UnvoHfqziUOu9b/IbKfKskjkqITKez7EPq3LUqMda7ly0eZHC0P5f9FqFP1E+CfHp5xF8+mHev8wn7Lbq/4xP'
        b'0/87fMoorYn9jifH5ytPtLMInwrj61KnPrxJUVp5nIPT77G19ns2LOP8gTC/sKxslooP2iwfnlYTPvyLDMCZl+cjBrwayYCqf58B+FsWmAGLqWFdX7JI46t0fTkqTxys'
        b'ri+VZSDVVzGHmz7C58ZcnsVbDMnivcUGbiiPMOd3T0cs3d5mDjZN+u0SyJoFE10/N0ylYYfV62CbsaM1rGFf1YFacFyuX66F3+3ngBXLJNFLKj3QK3jOGbLYLCx4NF5g'
        b'rJehm2SM6Z6WagDPpomzuFR+mAZohWjBRCbXQ/CiEZ4UYT3Y+EatgE+5FfF14XlwZDG4wH742IIylUogT5dTBNsng13wDFGkBBfzg96Ar7Bz7rkUsD2CQxTC4uB+fESn'
        b'Or1XE3Pg0XBwDK4PS2YzPgsOy1R4qws4cCMPrgAXXFgE1P2gxhwf8YnBClDjlozPOw2m8UrgWrg7o5JM+VdAPViFCywQx6tRWhpcOdb6gztBPUF51YL77FnoFDU1VPug'
        b'GRytZkFJL8MjZVg/RCBWp7T8uVkxaOl2AGwjJCXZmAwjsqGZ+wpsBZ1h8Bh5NQ7s4sN6cTLcNBq7E1LP4452BysqCSD2gXywQQY3xmN3S4mwntQ7C4ctDOZPQTW9wcvj'
        b'rZapw7ZM6vl83DK132qZb7dL7Bfmf6NN/nbA0PmDNimYhRfrB7T4lKbmI4oKm5w42sKRYnUL20x9YM00FQIZgR+D+8EBUlNBY8A2sHmsCrOFALZUgwaWa/tAL9iGGRtF'
        b'jm6H+coBOwnXwDm4cVl+LKvVgXU65HA1qwh8GeyaLsfgMFxwylmTY6WpXolHGWlIogobKiokn+Me7c+qqp6Be/nos69hsQgmVkwUIc+6Gu6GW2e8xjnDIGcOUlIqw9k6'
        b'GN9sus9IhDOzIKKlTD632Aw0pqMrX2RH2YHjcHOygE/UV+FKL3CGYKOtgdtGpgYt4DDRuHSl4IGZC14DjmG0McEktrEfhnvgCYJy5ghOjwA6K1zEqmSCc16ghkVPGwfP'
        b'cVj0tNQZRAEZri8CO/DGByOoNWolSQTihCQOZQ/W8P3hPtjO1scVRNR6WWK8v2QEaBlnEusFoz4B7lQB4HCoUDN1Ta6pjwkZI+ABXbKrYvF93kLQKRZgDJ1JsI0dTI6A'
        b'7mUEYimRaOvgcQfUEaUh51yLbP7MPNBJhioHcHAeVvj6DXTQiKxhzSIqGazQQPuiTtDDNrbNoLEKrIfr3wxDk6XwHBmCdCaCla+HoKyM4YU/6JpPuuYivL16a5SLB2ff'
        b'DHSYbpU/jljYXTHaZORoBY45F5NXmWhguuIEdqoAqjA8FVjHZ8ewy3B1uIHBMBoTxmIC20tIpauB3RjCCY8YqBoy5uERA3TANSxH2sAeASZ7xHDTCXZmssjQnVPhJdR2'
        b'ORTHr1BEod3KZriCvCmByyPGwXZhkhh1LbUpHETYRZtKlVLECdiNmlecWJQ0wR91WbCDuxgN99uIdvIE1CVrVShGOWBn8tsgRthJHCFrakYKigR2jUQSg+dgU6UzhUEp'
        b'O1zfGuXgDtg+cqSDG0BtFVHmDwK7OHAr6jZFeiJKlOnw1uDHGx5qAlBgjwam5VQGFYOSzRsVyHFRRZqGYlmid2lUNbWcb0PJjLAnF2syMHnz2JVpMrvG4N7nSjzuc+bL'
        b'8VLElhX+3NcKmlYyp6R6bnnI/aDfKiHg3VGBJIgIWOUh7G6JSEHePHudulYLrUnwZIY3T4qoyfSEAkV6xvWcvpx+x3dyBiYUvCSywpW65pxNOuacyjBMw2TspQT934S2'
        b'/UfgVrEknuB4JYxPFWfF/cE8AU5ytTkU3AsP606G++YSq0tw2s1aCHdmJ4gFYrQPfaMFZ5mpBo7CTRyizV5ghDjtF8xHg7PobkU+1mZn4RZr3VCSE/PVKA6PwgB47eBy'
        b'LjuYNMH90XLYo46B49CSYjMFGgLgvtIxTkEc+aeo1juXLvxwwofJREf7V4VYLDr1y+gvz9hei1LjRYfVekaZR65Yf3JqVFHtOu/V0/vfWf2OTLKYawN0bN4RGhfcGBoa'
        b'Kql6fEp3W7Wd6awfb768/HyvVD516gWp31rLinUPdm348ei9stVjy4XKsHcL0kOaPsm6Ab7wjNgripDWjr3p6CyzOvRy2dYrba7gUN200hkNd9M+f/eEa3O706a1B+64'
        b'uT35KndhSFdV/EKBl3kJzBm9Qb5c3HX/zIbU9w6ZXj+34CB38qpfln8pipR+L7JOi43anr5vv++RgqwFa2YNrt3lOJD5lWtLy9F2t7St4ivOVSbLct1DCsRD6st+bZbf'
        b'Omnx5GR9dJOaYnTfvcDmIdvmsWedDbJ38La937FPJDvZe/j9GQuOvlerNzcj6Yfu8TOb5V9M/37Xt2lL5ztuepx5ZfLOukVns3tXci5SX3IPeH/+6+OWHzkRYw7bV12U'
        b'lNfeW/2YTu2Z/GPO4oLbW3UfadgujT/99b11B3aWbcqXrprx4rDvcpGCk/agv19X1+uz0fWHbnh4X5g/9OHRf/DPFfywse1jAx+FQWpzKHfWq+9GOUx5P+0f3VM/LPqK'
        b'mZXhGls9Omwc54NP931d94mW2t886yd+Ejwl8oGTKC7zS4fySpev837piE6gj+5+5vNp1k6vUe6rtpVs3L38UND7n7ocfrUrp/+9ID2vMR+U/u3C+tMDGo+rV8rLFLlz'
        b'v3iaHpy8sbGhdtr92vh1yu8if8qI+GnbZ4s/0pjmdDVn8x7xdzcPOT1a41MYY//j6VEny+8ZUO9stpY5/n2hMtrQ5l5W5vbDtQHvqu8MNoit1n2UTbnwZ11f2JOzYgyQ'
        b'5JvsvVV0bb7rl+vdXwScO37rZ8nCjw/7LM3O+XRG3US6PtV5Yd39b379bpVwEZN5rWFHXeuvmb3JeZ1VD0ff8gcuYZaTZ/dMCVhc77148OrpKA3G/JnWkqLvzfYWFF7S'
        b'/fSnhZ7xRe9df7XtG9Ff6kOp2oWpelMvDFzMmv9k6ZaPPiuI2Hti8onWl3Yv4y7NDDL4u+PSZ0szPG9cmPMYPA71LOxP1/vMc3XijF6PYBm08bw4zf699X/Lz9ues69y'
        b'03sxL1JOzP3iWpdehaPf2W3ai3qW1W7NW//OaZdfLr+3mN4g5DMTps1faX59Kc9uQcrt0tHmA4VLXL3mn9mw84vLuVP0//Guvdx4z239V5N+yVpafEa61KVrmkF95TWX'
        b'O+/t36m/80OzX+IHw7744YLrkO/72/5Rcf6Xj2DMV66/6s79+NdTq16OSwnMevQ3edLHXuI1tNjzwOdz95U/uhT13kznrhvBPStdvunfO1GaVb19/oZxhUUmdM/zJz7x'
        b'1y/vf2/9qh+P/miz7KO4KdbH2m/pfvNBwRnLV6UyR4E/UbJzg5eMx8OVeNkCOtTIHHQRXOARRDTftBJ4BKzWwTiHWq5oL4FWy6NAOw/s4YJ6FTjydHhYxw0Dna6XceFZ'
        b'HqVpwc1alsVqD56G+6oJJCgFe+EuuJcCx6cVslq9J2EjGvYOoUXPMKQp1s8FW0rZ11thE9wCemGXSo2aKFFj3was8t9R9PrKbNj2BsUT6++Oh9tYD9lLOdPi3172oQx7'
        b'WFX1U6ApmhTIWnNeortAndJDsZzRYvE8EdCB3Ymg/o0CrwF2//AWrOm2iax+cQM8A9qH8UV3gx6iwKsOugmBfnAbaHqtwYudNqiN4uSDA/AKC2faAdvtdAjEHFcb7Mng'
        b'hID9E1iF2xq0gm5lwWo5Og5wA9peRQFWmRatpS6m6LhKMBLqSHhdNKyzasPJ4GA2D7QMg9YSyFoeOMiiRa+AB40wIu0htMh6C5UWsaKV8DJUDR7AwJ51IsK6c+rgKFca'
        b'A/eRl5xCeFmFgi3gcFQg2BdBC/tSK+wNxu4SJz6B2LWHrII3OAb2wv0qgF54EBzmE4ReNOF1sdi1p+BhhyBPVOV1eHpDyyB/DugxgmtYMesFeGnxMDKwKWjjE2jgCb4s'
        b'Ey6Cy15yWBcfD8/K4Cq4j0tpzOO6VbqzQK6gQ6ICYS0FbRyCwQovVbLN4FBKHtZrRdu7zfNYhWHtbC447wDWkpzRxAxX6YDOuUT3tcKEj9cyXfBKOQuouwMeD2LVYrmB'
        b'8LQJxyEMrlVJhQFGEKxx1klIEqqjjc95DtgM14QQBi4FK8EauR/Yju3KJDKJNl70jQWn1Xz17FlgxfXwKHcYV3EzqqthmFYTtBGAW90hC+eKpuyd8DQGVCVgqrXGb+Op'
        b'oq0My5W5Jq8RSMH++RwWgTQolu1CDVaw9rUFAzwG2/gYS3EG2EWUmFPg5XwVdPlKAjr5Gr4cXkQLkU2sBvhOtPi7RPoJWD/3LUhYVOheVhJ+wQtukBToVOppoW5qxwmX'
        b'wu1sF7+wAFzGOLvE7GA8bORHc9BKuB10smPHVl8zuBy0qNA0CZSmxxii8q/Bh3XyZKKrbCCnQIcXYLs93J4OG4bhcV2i1cdw7RHLLpG68E6XvEbfhIdyeQR+0xB0EHa6'
        b'g0MJXFAzDMCJ0TddHUk1oIX8ZjWC95ugD3b9Bn7zDNxEUDIX6CEyCUpm8SgBxzoWnmDTnqmqlINt1b+FySQYmeFwFynmAlCbq8LIBK3guLo11xi2mxGSHdCGAtsBokaY'
        b'DHaWI/bJuHZwuR4p66gQsBxcEgzjdhLUThk4T2pWC43ZV14b44Ari9Uxrj44BjeSph8xFo0F9aJkeNgJjehwE4qjg3ozPG4YQwZ9M7gF284m5+DtooA4VNYBx7nwANpn'
        b'dLHDV3NEJt6pUhRXDQ18rZxU2DSGHaLWjQMXhSmiMNQw6sg2SoPSgZfRxDDPjW0OO2GbkY4b3IhqC27QS+KMS0siVDnA9fG45ecvecsIBO2VjrBtbc9YuJe1T6rijLRQ'
        b'4qLJoGO+wO7/Xif6v6PYZkf9Hnzzd/rT7OZF+82W5L7gv717IZLYgxqqg54XCfEcSuTdoqF0EmGl4QP5LVylg0uH18EApVjaEqMUebVGP1TdtUQr3TxZhdYWjYcOTi0z'
        b'2kMOhnRnn80/m9+drxR69cacDh0URjLCGFoYwwhltFDGCFNpYSojXKxAfxmTFCUzB3NnDmbMYjLK6IwyJqOCzqhgMqrojComYzGdsbglSuki7KjoWtC54K6Ln9IvuJuv'
        b'FEkZURAtCurN6iu5lD8oSmRE2bQomxFNokWTGNFkWjT5J4oST+I+IaGieCZTXEEXVygqF6EnyzhR3B8oaj57KeFEc3/Cl1TuU/ZCfmWxv7LYX5PYX5O4LdwW71YtpXhc'
        b'79TTBYPiaEYcR4vjGHESLU5ixGm0OI0RL1Wgv6w8xbTZg/mzB7PmMFnz6Kx5TNZ8Oms+k7WAzlrAZC2ls5aivHxatVFexwqGMfciaXHkcJZFCnFRf+z7KUxiPp2YzyQW'
        b'0YlFqiRunsfcGbdw2i0c8cnDl4XECqc9wtF7/1Y9pZsIPRdJu1KOpqDqcxVhIMQugw6D7jTGJYR2CWFcwu66hCld3bv0O/W7K84u6FlwzzX8KZ8SBz1Vpzz9lCJJx4Jj'
        b'SUqBR5dVpxUjCKQFgYjOrrzOPEYcSotDlUJJl1+nnyoHxjWQdg1kXMMVruG95X/48Amf5+38nOKJXH5Sp1zFrZUHqn7S4Il8n1A4UKekvk90KS//Fxb6nvZsIZ5YU74h'
        b'vdP61QdDkgd9UhifdNonnfHJon2yGJ9JtM8kxBjfcMxhFCoKpiqmzVHMqxqcVjVYUM0ULKILFqEIkznhmHP4gnINpW2lSp/g02WMTxztE8f4pNA44wzaJ4PxyaZ9shmf'
        b'XNondzhmEHZKV3ItZTAogwmaQAdNYIIm0UGTmKDJdBBuX8HR+OsoRO1LMUuumL9ocNaiweLFTPEyunjZT2zTespeWrgKBz/a1v8hqlKbThtGEEILQhhBBC2IYATjFYLx'
        b'fdOuz7w6s0X9YwdBx9SumV0zO2YOSf17icJw3/z+qdeWDkizFDl5g9K8loiW6tbEhy4SjAfaoqb0DWTB/RjfRNo3kfEtVqC/1DRFetFgajH+sJS2HYfYx7KOEUfR4ijU'
        b'VhXitH5uv8/72sPt0LOroBO1xHBaHP7mEQGExJCaqkcSr64ZnTO6yjrLGEmiQpLYZ9QXe80CvfRt1cHxXzcR1CcU4qQ+r76p1wJUaYchRINoYRB6NK5VE6fI6czpyu/M'
        b'V8Vxl3Yt7FzYtaxzGXrg16r70DsIq1+fLegpYLzjae94xrtY4V3cn80CthbQSQVMUjGdhAraEkLbeuE2a91p3aKu9PBiGxIarNhSsJ0rlhbHMuJEWpzYov2xg1jp6Nyy'
        b'oC2JcfSjHf16zRn/eNo/fsBfdtcxUenuzQIvxtx1j2mJfTum6RXLc5aMv4z2lw34J91zTH7KozxiOagpS8bh82Y0NL4VfzTG7nyd+z3HRBRfEvCJh3d3Ya/Z6dkDHlEq'
        b'aln6GUEwLQhGpfANxr3z7NKepYxvnsI3r99IkZg7GJ/3mq8OTgpnH8bBd9DBt3eEorwiNW8wKO+JIeXuqfAMH5REMJI4WhLXbzwgSWqJ/cRN3DHtiKh31F23gOFhoPye'
        b'a4DSRdIxr20h4+JPu/gzLoF3XAL7NPo517SZsDQ6LI0Jy7gTloHKGMGJ5/SPumben63IzHp/osI1pEOjm9Op3R3bG96TMCSUdFQdCer1vCsMUkoDzgb2BJ4M7ohCt4w0'
        b'mpZGM9IE9KeQJiiDw7u53T492p+4uHX4HljcPQ8N8efS+0xx3hcKFKnj7waPRwNcL+e0NuMRQXtEMB5Rdzyi+k0V49PeN2fiJ9Hxk5j4vDvxeUpPv95Rp817y+96hvdl'
        b'94+/NpGJzqajs5nonDvROR+HRvVW0kQMNxA1+UrluTc/BkInd3AVwsA7rkEPXSW4JhS+k3C1vwHNVFX5Cx5HUIA5LPTqknRK0BDr5tkl7BTiH4xbMO0WzLhlK9yy+0yv'
        b'W1y1YMLT6PA0JjybDs8mURm3ANotgHELpd1CWzQ+dnDrmqb0D+tzUfgloB69hHb0/sTVV+EXR7um9EegoIX/0MO3hX9QT+ksbNN5XsBD0/JL+adotl4VzplmxrnKH4VD'
        b'UykKgU6EFrq8MzrcHV3+wg93QZfr4nAJutywNMGhd3gAurznYY3CmwaWOBSFU+jyvjjCDF0UGuH66EKPwbFpIc6bDg7XRZcBbQEOx4VboMugIf4xGBAegi6Mf7gzugzZ'
        b'RuK8P7TAuX7oF+6BLh8L8I+H6uE4o0/GhnPR5RGJ8MjPDYWfOqjj0C2Cjy6fe+DcvnDXwKGvPQpVrj7va1VUF5dUTCmdJb+vUVBRXThFXvLvGAyonH6OXDuxh8mtWOti'
        b'PwqcseAWS5h/Xk79FB/P4XBssYmA7b9wovwcS3b3qIuoozq+PCJXdYV7bLDeTyDsJX6VsOLPXC57ENOUkSx7S7dHCJrmcShzcEAN1M+KJ0LdaaMN0EJ2E1p5x4tB3bBF'
        b'vk2g2liwH24Dq5NYN94toA1sF2LL2mE1tLnYRnF8HKx3B8v1sCMLDjV5tKajC+xhj5A2wfYCFvFmM9o57n6NaROpOqKcARvBaRncIHYFnRkkM09vlYYcRQU4qut4UEmz'
        b'WRCSrlQedpGEZdRoLZ7NftmVHBDrwhPs0Uku2KVp4JRLErhmWspHxMERMlX+t/GJ0AYZh5q6TDMelXBqKpFZ2wn4VFikIT5Q1A3VmsVqCpSGXt3Pkddip75l3peyZWUD'
        b'YYbWV56VG7XPyU9KGNhmlDp6fNTEDGsjze1pAu0T9wYPGWU6HmxJXbGy7LsejTm5n6hV/ar2qP/Kw3bbnvwPvpldZeFvQtfvHWr66+6XU+dfWpKxuKQrXOdW32x/21+3'
        b'P8xZeFv9CbXqQAKTvujKjfOP7llF5n6s3byvbrSL0/FAM7pm8mPDyUd5It6Mi2c1LsjfcZv3bZxdz16Hrcfe3xy58/kHaSsfW6x55/HWa6EZc2rKjD+43cafUCmKvzxx'
        b'9cbMg5X9A+KzK55s2/K0P3jzR7Pnvly7RP6dhLED0yq4an+3YbY9mpGwxvLzpuqpy9fe6Zn9QNP/YM+dj6bN/1EwbcfX1Ru+nrD9nXvGjz63/1zzkNk92vDVlkfzfjiT'
        b'M9vr4ufF1ftiZt59FORfk3vXrvjZybClj2FClqPoiDw7rWh7/5Ni4yP7Ixqv7nIszDu1IODe3lsPmt7fR9v7Hojeten7Bwl/+cRMOTk9Iac7PPm2Hr11X/SKtUE6wneB'
        b'tEYzR1rxVcKss05nBou9Gw7L7HarDclefvPLA4/MZXdmpB391eZq2eNbo8s3x378yr12ktFuy6faM2RVv45+sjDgm4/tJZ9qH39kPudRyQPgk//d54oIvY9KLr5wOlmR'
        b'cmqB2Vn6x5/6bj0YXbKq7oHzuttRz29+ESCb/5dVTU8HPZbeeLzpUe8PGR0T5h/8drFtrf+eopnmr24Zj9kz5UxdmVw4e+7MYP6Q39ox8+anX/s6PVrjtqVP+7cHzX8J'
        b'aP7BtTd4Vqpa6Ufr277/u2Xwxm/9vvu0dnGihvyJ+NaiX/z9jBuu/dXzxrbiPS6F+vG3BTZXjIPql13b+uTmhuTUqjY9OLDvvFbrvZfPv370yymra++8Cs9wz/jLy6QN'
        b'P3zpwDhsvXA189GFsV/dPu545fF+vcwDHR3fT3v3M+F3yx99W//rnpCJLbdXfD96rl3n957v/a3xoyly5Z6ParPWFhxKzF55x+ylvdnU8h/3JSgby5757XcxOvbTintT'
        b'VgdGPNq8Z0VzeFdt/a0VXw6o313/Rbvaoo/XtUe3959Xwvh93/dV+8x4EPxheXft+/Zfvb9l/5hze/+x7tv36ht/GCvvlsRaCRbn7XzAS9b02dv266T9jV9Z1oXcktFj'
        b'luypNQpeblz+3vOEj7j51UllVcW3t/3yq1r6/QLH/h26Zs1/3/LekOerXS/Ock50RzgvTX3SvMdItuf8F4I9ZuJnzVNsuMueZWl9lPpzwKyZ1xPmP9Ow+/72z9c6BZIX'
        b'QtQxEyaE/Jfm8/BwJGtBj83nF0aT3fwsNHa1DBvsE2P9FXALNtiHe1kxWbcOWDVC5OwF2sHFMXAFEUAkBYB1bxmMG1rxwA7QMh5sh9uJAEIqAOveCIaDUbY1LnZEfLsY'
        b'bPT+PaAA0dzcAtphFzw4hchIKsznyd9I4SZMVsnhQK8lEctMhqfBJVkK62ke1MNd4WAnrCESjFngPGxRyf5MOHCvk8OsdGIQr4VG3WOs8A724JLDU6yLJbhdDWyWg1Nw'
        b'P9jK+inZCFbO0HETsk7uUAF1jLnwEuyEq8A2CyLeCZGBHRicZB64UC3gUPwqDtyjBk+z0pcr8WA79iSHjeXnwCPgnATsZS3Qd8NTnnIiRt2UjCELtKu4oAHuBkec9UhS'
        b'ewqsVRnUY2t6vUkLOeDQC6zT4BCzSEeCeMjN5vDgysC4PFZas7JMWyVpo+D6ctABGg3ZL53n+rLsrYiFp98ALqAJbCdhsAlsTyO+CSmiGOIDe8BKcABsYbFX1giLhv0i'
        b'elMjRYtgHzxG5K+u4BwWPGLxpDHcQDBWsKeXA3NZYdBpTXjlLVN51lAeroGNRsIpJIfyMbB5WHxGZGdz4Qo7uB62sbLCTgu4icgKG0Ezcac1hmvvKVE53csH2+SIi5uw'
        b'jjEPdHJKx6O5dS3YwL7eVOKNDwg2YPE9D5zigC7U2ptgUwCpGgNnuEFHklTOxqhA3x5lwjOFa2ZUQ/bIJCkQHseSZbbWNPW4HmrF8CRoJKmr00HHb30yoqaxF7TljmLV'
        b'obsgJuV3gD42sWrgBDyHNR3GsHVUA+tQ0X6H6MMN4sCjozVJLWjDXtQ+6mVsT0rhmBjB5XC7nO2iB0ETaBghxt4JToDNM63IS/5seI51AgjWsQ41C7husyHrU290iPpr'
        b'34yrOYlj4CrYilo+5nwBOAN3jMTlIaA8YJ1/PiKzhYhNecExw52IiJ1xsAIe4FBjS9TsJ4AGwtwk1JdPDatRU5SmHzcf9hTCiyFkEHDWjv2tirVKv/oCOAgPg82o0ePK'
        b'9gCHtNk2hpiFPblpJ3JT0NsGuK2KdGkdWIMKXY/1VMRg+1iwbqSKnMdEdWNURW0v3FDMUAlaW/3hCPkaRGLauGRwGNSwDibr4QV4aXgVCHbri7FDJg1KfyLPE1xRYzl9'
        b'Wb6IrObe/qwbrOXD03AHOAX2FrPdaT1YVY7zSoHrEs3gZQn+LMqLx7MLRG0W8ysR7odHWRilZQUESInrABvhif9Vsan6/7bY9Dco4+zaP4r7R5ATRF5KZKPn0bbgJVGC'
        b'XxrLoaztm/P25jVEE2P9NvNGvtLOFfuvOWDdqI4xAEKbQhkLd9rCvdvnroU/2p43RSmt7N/gJHRn3bUKVDo4NkV9hvXQY/udbrvfcGcS8umE/EH3/AF77FznodSPdTTD'
        b'SONpaTwjLVVIS/uzbk+8MVExYfpAUmmjusLGnR7rMST07HY6K+gRnJX0SPqcrguuCvpjBiPSB4QZiuxJg8JJjeqN1fRYV6VAworxGEEYLQhjBFkKQVZfzPWEqwn98wei'
        b'slC0+U36SokUO49hJJEKSWRvBSOephBPQwSKb4hZvX7F5Kl0wlQUeSE91m1IiMUaFucsrlifs2b8E2l/jCogTB/+pL1Lu7hVzNh70fZejL0vWlAy9mkK+7Re7yvB54KZ'
        b'wCQ6MIkJTKMD0xo1hgQ+3VV9agOCaEaQoxDk9I9RpE4YjM9R0SX06PLv9H8jPWKEyQphch//utZVrev6V/VVn3xo69Su36rPeuFAnBFIWFlKEC0IYgRpCkFanzrGXej3'
        b'GQhLU2WNkhDHHR60rUcj/2Mbxw5+t8lZmx6bu65hSkc37I+po2rA0bcxWunm3ljVZIB4czakJ4SRxtHSOEaaTEuTGel4WjqekWbR0qxhzjxE7QM1C9QobIiExsb3ro3v'
        b'lZiHts74e2/IVLIPWALYR4ytH23r95sXAbRtAGMbStuG4he6rbrtBq0GrAcsxlamsJX18rFnlSv65/QZPxntJ3uixfezbozBYiLLcT/pz+WYiX6kcPikmEc5ubUntyYz'
        b'jv60o3+j1pCzoMOpS9wpZtyCaLcgxi1Z4ZZ8ldcXD/UHnFMadZQOLiykCOOQpXDIOqfWm3lBh73vW6TIzLq6rFHzYxsXpZuwUfbYxvUTR6liXNRTiuOUzemPe0KuyjDZ'
        b'Ex65Scl8Sm4ao7GnDa+9SUNWti1mu/M75t218ug1YfwT0J/CP+EzR9dOc6Wt4CmP6xbJUXr6PyE3D0W+T/jkJjD8Kbl5TnGdojhN0T+pU9bODyXjurOPlTGSiQrJxD6z'
        b'69ZXrZnwTDo8kwmfSIdPbIxp8W1KUYql3THH8hnxJIV4Uu+CK0vPLWVCs+jQLCZ0Eh06CUXyaUoecnDrCKAdZH0xKGiMGhKIOnKOWGNgliFHxDUPRJdTsNIv6Am5JmSS'
        b'60OxJ6IOXb0Dn+IrKqQmJfbZm8R29gH7OIVl3BNdytaxeUHTAsZGSttIuxMYm9ABm1BUHS4ixtmXdvZlnMMUzmG93o2xShvn5iVNSxgbT/RH23gq3aUt/IO6Su+wu7Ze'
        b'D/3Drtics2H8k2j/pP6q20tuLFE5kfErbOHftfVWOri1B7cGMw7etIN3rwmWQQ46RCrdJF1unW7d2WfzevIY71jaO3bQLa4lUinx7Jp1eBYtierNuiuJ6uAOuXt1e3VV'
        b'Ha564BWiCE0f8MpQiDIQ9R5ejHsY+lO4h+Eo0iPVvXZHFz/wiVBEThrwyVV45D7hUR5BD8XujDiEFof0zhsUh/dlXC+4WnBXnDEkGvcwMOxKyLkQJjCFDky5Fzi+U9YR'
        b'1e2kdB93eEmfviIt615YljI2/vqiq4sU6dmDsRO6+Wf1e/R7KwY8op7yqaA0zlN1SiB56kC5R3NeuFLugYrAzAFJlsI166G1w16dF5XqlL3oOY+yFr6UY0vu1RHuuW4c'
        b'MC5cgC7vWLug8Jq6Fg4Nw8Xo8pcQDxRed5eisN8hXBddbnh4ofBdh/BQdLnpEGGKLrcCw13RReFog0JazQCHJno4tMeZ0SKc5I6NNQ5D8NsBfZzjXW54ELoMhhqh8J4R'
        b'TnzPK1IbXYaCw53Q5QOXcB66sEIvQ9b24SD/T6yG/rW50PB3Qq+RU1/5XWwjpqVCxsBiryXYhsICi70ssG8Si3/FmuLvuAjG9/kFBUXe4+5rFhTIp5eUVMjLZbg4cTjo'
        b'QjHuqxcQI+1yD/zEDFtyROC7aGy0rFswAma7vB3T+QTHGMTEnsI/pTiuDw7yseRHo6B69qyywhkCbnKMwKJ8NY6yBgc1OFiLAw7OgOCA1OLgXZxVEUmrQpK4rzsSwOG+'
        b'zgjIhPJMHLsBp+PibDbjO11s2qL12jL8vobKHPu+7khr6Pt6b1kbs8ZdxHKIWK+Q6l+Hs6vD1Wb6/8Ldym8bB17V/5Hzlddt5JGaKsDOFeS1iO6XrP8VXT3DZ5bYnYhT'
        b'K6/RorOkJ/KcybnKq+m9M29402nZ9IRJivG5dH4hXVxKz5itKJqj8CtTiOcO2TlhryIuP6kVcfT8f6Jw+JSE2LWIyxPy+Gkib9h1SSx2XRLPqY1Cfd7cfshQrDTxRI/M'
        b'pbUJ6ImpzZChm9LEFz0x9a+NRU8sHYcM3ZUmQeiJZUhtInpi4TBkKFGahKEnFhGcWhl6pMo7Cucdw+ateoTzNpGSJ8YWQ4bOShMP9MTYqzbyTZxwHCeSTTbWdshQqDQJ'
        b'QY/GhnFq49AjM7shQxGbk5m0Nv4Nle6YSs+RVCZjKlM5hEwrpyFDD/aRFXqU9JPmaD27HyQcPYcf1Dl6lj+p5/KwrxUc/kjCN75WQsB+sEf+m70EhzKDHaNnq5Xow61v'
        b'aVJj+TSx8pqDgiBNYmGG/Z8MOzPQytKWar62N1P7D9qbrf6N+cho6vf2ZjMqUyjsAxw0RUs9xnn5eHpLwVnQXVFRPn9epRztvLrhKXgCnkG7vdPwpIGmrra+lp4O2ARq'
        b'x8NdYD3cArenp8LNcCfqbPA4PKejMxuursR7KPmkHD0XomFdL8SYl1jdmkcZw708eD4BHCNA3cVwpxQlXok1zT0pT7CFX0l2TBs0woWwHe7EaVBCHlhZjlJ2oZRwTwSx'
        b'NQHHwSq4fyK8JEV9xYvyAocCyFfhXldwCtbHg0PsZ1VJ8UfhMXCUfBVcQRvuZngoTcrFSu7SMZVEO7+wAi5HnG1AHyQpOZSJE0pmDdeQVBKwsygSrJSiyhtHjQNN8Byh'
        b'dZEjPIjK2AQ3DpeUZ4Q+WI9SOsAzrF3MelR/F+PBZSlqF96UN6wLI4Y2duBkCCqmDiklTsilTIxRulKwinwRnkSU1oHdsXgE9qF8YpOIxZZjyWxYrx+E06gScVCidHCa'
        b'tc7ZDZbDXnioWooGXF/KF7aB4+T4wTJ0AVgND6k4ogFaUb2AcyjlLLCP2APIDH1twVapBkX5UX7grCZrDLQJbIdnCfOEGg7oU9hQCiUyAhtI2UTgAhdcUgMYuMSf8gcX'
        b'4WnW1mb5hAiiXH+ZLRuqEHsVC6dakpSJoB0cCJsJTiIGBlABiN2nSfHG8jwWz1Mx3Zar4h04Dw+zxTudCLahrfFqbJ8YQUWAbtDB2lZ0wYOhpGgoqQPmgI01ZvpRQ2IU'
        b'BFrCNCeAemx+EElFlsCDLAp9nbXdnFIhaZ080BrE1j/YZMHWf2MWbIBrNbHVcBQVBTcFEI5nLitF31mNWruqcWsUqmoSHISt5GsacDU+G9qFzTOjqWjjCsIBcSLYKwQ9'
        b'cB9reYASGrG8AytNWCL3hEWCdbbYjDyGioH7s1gDn1bUCdtRq96mKh5bn2xvwhUK9nBIctRe9rlFwQY54nwsFRukT3oEqId7UmA92J2AUoCV2HUBuIh5346STtGvxNNO'
        b'VjloXTZWjlgfR8VV2rNnZe1wC1gtBCejCC/YdEGqT9qAXvJJc2NQrwN3QMz+eCq+NIowf1oeXAnrC8AJQi5uOYXDfbBrLNt9jxVZgsvzsPYtlUAlgHpwkpjAgI2wzgiu'
        b'QtVeP1y77sMDB+5SYmPCGROnCrAfDUnY54SMkk2El9nGugNs8iGsXAVP4G5fP3syrp+14DxrRXUANcj1aNRqhycRTxNRG7wMr5AxHe4BtaQjHwYtw2MOyYMwdiG8xLaI'
        b'/Xpw3xhdeBLxNYlKgqf92ZO9g8GwRTjVQdWOUMIglrGuYD9b3J0Z8LQTVlRGrE2mkufA9SxvejhY7mONGu9wt9w/zBpwUEBaPNwB1uiDLnAO+6ygUqiUZXAt+eoyHXg6'
        b'HRwQqlqTht3wELkVrGDHuRVqYPucZHgS8TWVSgWrEkmjjwXdsCPXgk0U8bqLhYQTjk4D221BL9iFbQ3HU+NzPVnPD+vd4XZ4YQlpdmAFbgyYzu0oXUog2/hqsBbl5Zk6'
        b'iKNpVBqPy47kB0En2Av3iUnFkHRBqu8tgpvY0fEQ3OUUDFfrIF6mU+lwOdxJ2h+4XGJhUq5q8q/HVlU7yAEqhmyLpUCXuQ7iZgaVAbaiZonTalqjBn8m83UjUo3oKm4a'
        b'RhOKJ00GzaXxOoiVmVQmIvI4Mb1Jza1i541V5RTG073Aw748jpMR0hj0xMzi6CAeotkbrAsmbIgPQW1mK5ZRsulWDE9V4OhC8p1UU9Rz15XoIO5lU9lxoI01cT0Mrixl'
        b'R3C0+PKFK9JRkgWwkx3lrmiCvaAR7NNBrJtATUBM3U/qUwr3VcL6uTPY2RTNVhdfz25bwUZSJQvCrDBkdT26zaFy4BWwnpAJuxEvdgin+bq/ThrETnABfiTdOFA/DXRN'
        b'AfWIgROpiTFosiRtG02zvqg2T2mqZvHhWSpF1cq80QJhiwCLexEDJ1GTNFLZibgV7B8D663g2uE+wdKKubcEnGHbzBZwLsUgDm5FNSqhJCYZpGb8YTPYLnJnZ0RbjmpM'
        b'bjZSNTMJol0At6LadKfc+fPI4F9io4P43JL/emQsZPufUwnhm4O9EJyfhW1CsUXohvmkYBVwgzmKu8NZNUTBlcOD2zJ1ttM2wFbd0dh5PCqYkBLCvdmEB3A3PD8e7MQT'
        b'Pi4aNu9TdXdwCRwiSb3AebDGFJ5KR43LiXJCy4097Ky4BdailPVe04TDK6JC1UcNAklKjKB8KrgAbkWM96A8QAdaQ2Bq1f0BamHm41/39ggV36Mgy4bibHjKGE3O2KBP'
        b'RIkWoDUEOWah0KijGlsicfXPcMGEnlZbqB9lvdhnfDrWwqCco90FHDKEwh4f2AkvTJbBdSK4Lk7MpTRBFxes0IXrHpNFZEN5WHJAcnLy411N+N+N0MdS8u95KCFjKlgJ'
        b'Do9eiEdsqowqqwQt7Mx2AR4wSYW9QlSsaqq6PIVInwXaxHg5zp1LcBg8nG+7ULGhFHkoMNClUGtw9ciKDPe2yGUfTgrRohBDPTyyrhh8aBDPPmyPN6LwPOkhORkdE5/G'
        b'Plxhz8crb1sP9Rqfd51i2IdquvoUqsyxHvNnG/qoz2Mf3lbXwMb+hh4+rdyPppSzDytmjUJra8rPY+rWcoslHPZh5RJtCvVOTY/5fdEOUnP2YZaDCeWKP6T/svATkZwi'
        b'2hOvJo9BTEB5SrKzAxZmUwJuRgx5cdxNjSUr67sZX1o5s7GDOOoqCng6siwdFDs5ufTLr6Zx5QWoFvMuPFiT8V65RbTJd3OGNlovjdvhvUV0zTh24/O0WX01miaak49S'
        b'dVs/SbyjPS9IfYrLtTrJ4YyhZ7yhkwfr/tq/wylzsXrmYq7Oxhjzc9cdjDK/Skz5eOBxyKLvDy4bZRgzSyeu43KUtvSdnJuj3G2TbtrKbk7Z17s8+pHRs3e4O9ZFHzWU'
        b'za0tyajNPGo0s8PYvXDDl4+M5lnt/PuWpebKhx+MnmXU9cj8acAcw7L98RfXiB/5fGR3uf6n2kCl0+VNBrVnafultZtqZz+wW7o+pbbqqeCpdHHyA2i65JxLzyb97z+R'
        b'LV7TRV9bYvmQYw2gL7U4CBRNf/GkOPCCy4YXDLPmrz+bBm/+5bvD9POv//bq2gnDyvA5bjd++DDPf+Krz34+7ru7eHKNy+ND3y5bNCnHZSD+L7L7y+Yoduw2+vRvpVN/'
        b'kX0T0f7kVGnP/sabop8X9HQFLCsPfuxbczPM5+S0mx+VDtQNnVHjhn6Z88H5wFuhGb9sqDM9szp+7WG3Z42me2eeKq64Pyku5sML7duPdUiT3rufmzT1Yd33enZehUkP'
        b'HV8sSvxB9OqLudO/WHv51Xsvmjf+7em3Rzv0F8xp/endH6eMqfT5+mn8FOWnHwn3/aO59uadFQtPTd+x8B+n8rcUGLz8R83Mab33zpWaaTwTGe/b99f5jZX67bMHs84E'
        b'vJrYrtG54v5nJxeNe3evy75rhTe+uXh224sxSWuEFdZrqyU3LG/FTjiw2ERrY2HehqltLc/PG77z9/ReSfGXs8tN02DuhWVzn/nOel9uzV1k/t3pnH0vRKY9xySzV+ct'
        b'nP348M5JFzVm+3+VMWfsCuHcxWd86+oWffxD/trKDyxv3/wp3y6nTXr7UP/x0R9nXD/rdvTh3W0V47u+db3V/m1x5GDa4o2JAsO/dI5/f1slLXQa/TQ1kK667ndfK6q+'
        b'YO/W8afL6O+btKtOeg66VT1aapnXdPcr1z3vzpjwTaFJWcfXa2DFjv3H/1JWn1dpeXZfw5B1qVrPohlZp1+8m344IvqSW9PnjlvrjvfpbL+b+lUfXZK3rnR751LJke+1'
        b'Av/2TTV4d8+n6TeGqnMtOsSeqXtHl8+YWD0oGHV3f5BNx3HprhUrvLZ++HDqwM9Gu89LFp0WuEUw7Uvqb3244so1x4BlGzbvsP9oo7lrtvIfMWNvXP76x+hTPy858fPM'
        b'oCPu5kWXO1+5et3+B+9p6536wekCfZWTk0OAWNIkJabwKf7iaGcOPAjOupJz2FKHwhS066hn0fPV4jjYPA6sUmHlwLMLZbDdAkOaCWViNw6lA3fzuKAdsmY+AbAL+4zC'
        b'DpvQ/7Nocc/T5ngGLGDdp2yYBw4lgxVCuBEcTeBTasUccHGJF0mYPx3WyHKTU8Tx8aJ4NUpnPhfNPNtRrqz3NLSwqvVCMVijL5XJly44yBptNcHj4KIn3IkydkckqVVy'
        b'0DxwCnaxiTdPAF0paAX9tk2XPeggRC3xh5eEDgkY2cMN25er4yPuHjFrULgjB+/bwGoZMR9BOZty0CJ3HrG08SgZ1soIhHXzOeFTlrLEHFmGF9XYvBocQ1OZH7wELnLN'
        b'RCastkWr3yy8ZJVhU6jhU2cDD9407BpL4PR/bxTyP5X14RPqP7Yl+Y1JicqeRF40ZU5B6ewp00rKX6BZmZyG3lJjsZMWJ3Oo0RGc2ugnXMOx+kpDi8b0Jzx8Zy/ukLN3'
        b'40L7jMndQ/KWj+/IW3JH3uK7J+rUKEv0XoO9d5CgGKp77zAOikR+aLKRtNh7Ekl1z0YiP7TZSDrsPYmkumcjkR+6bCQ99h5Heqq6ZyORH/psJAP2nuSkumcjkR+GbKRR'
        b'7D2JpLpnI5EfRmwkY/aeRFLds5HIDxM20mj2nkRS3bORyI8xbCRT9p5EUt2zkciPsSTSUzP2HkfqlvUZE/60CP/sx1MbQ+x7+qm9yq9Ce2BrIGPsfsfYXTnGYueMzTNa'
        b'jLeWNfCURqN3CjcLG4s6nPAhUoNwwMi7NlJpadMc1xS3Lqk2Wjl67M5JmydtzauN+WSUSUNWY/H2vIFRDrURD8zdG9SxENemcX7LlL3VHerHtAZtPLs9u4t67U9PZcyC'
        b'G8KV5pYNkUNW9i3e+3IbOcqxFgRV3Kcj+phLd/gx4aCDz72xvk95lLXbZ0K/RgOlrX0jX+ng0qg5ZOfcKu+QHqjutmtbfM9uXGO40t6pzbkx8rGNRCmUdI86Jj/m16r5'
        b'UChp0VTa2O9Z1u13VxqLT391W3U7xh80QJH2az60dWopbNfqGN+m36b11JSy90Z16CjoGNXm16ipHGvbrNekt8dA6SDsiOxIawlGn7Wxb5W2VB8I7vYadPAesPFpVMNv'
        b'o9D3Yrqjur0VDv7kaHTI0hGV3Ma+xXX37E55t9+RJb3yQfeIQevIRh5LuveBhffsvBDZLqK26m6H1qWMS7DCJbjXgXGJUrhE9Rk3Ru+OQyW3lz60sWuuaqpqqdy9FH1t'
        b'rJWKKFv7do1WjQ7+AX1UJfaOjRpKJ0GH98Gkxiils7ib0zazMVZp79CInVAoXd1a+Epnt/bS1tJund70AefwFp7Swblj1EHfIUeB0sWtRU3pKuwoPKaJ4wk6wtumtfA+'
        b'dnbrqOyR9447ueCue1hfRr+TInX8+y7X8hRZOXejc5Ru7t12xwQtkUqhFJ/U96r1ZvZJew36jQaEiawVl/zgIqWrWCny7I46ltgSjW8ijiXsj/7EUTQklPTz+4v6y29o'
        b'D7in39Du8+zmn9Xp0ekNP6N/Q5t2ZzUacgaFOYh/Dq4YZr7bqVfztDvjEHHXIUIp9Og27rbvCOip6I09uUQhjGIcoxSOUS/ElJPXi1BK5P9CizIPeapBWXg8WYh2cLYK'
        b'XZuXzzQojwwOgeB738Y8xcCQPYHTuc8rnT3tXz98k2MJxeTfjKJk5CTBx8Oq5RjQb1Eyh8MZ9YJCwb9yvIZ3jEUqv+XkH4ZQIxJ0AgmlwTomXk6NACvjqmChKKm2SqbP'
        b'S1cfIdNXs3gLBmqkY2IbKpQXqkZk+r97+l9CQr0+XRgh0zf7I4Q76nkhppnLItxlqUm5/ysYd7+FUeP9AX1qZON0XcAjtKXOqBZ52FhRxK2rSQBZldRnuxKUNLB/fOJ4'
        b'17j49Di8fIjnU76L1F3hZtNSuGqAIw9ECf5xfN7JKTMma06tLeo2LJwct3nK5IYpmhWBU3UnF/dRzqkT99nVmDmPeWc6N7Pp6tibLTf7hrjUszP81tMSAZeow2n7wOUy'
        b'FdjopGWUehDXdCY8QhTVoheBlTqh8OgfK6x2gd3wioA7okXiKXt4Otcpml5SNLOgdE5xSfV9mwLsn7sAI6m/MQodEYHM9djdEZ7r545HPWZ0w7xt3kqT0TtjN8duiyfw'
        b'nsPuZ0zHNmiOQO/j3+eU/lHvIWCkpH+wPeMX3DNeocBf+w2C349l41HPMPhXOsUqlDKZRak5BHv5MlEytkFQo9TNuTxnbXByEeu79DLogM1CuCWZS6UKuKM4FOg2EnBY'
        b'MewesB90yRKTk8Vjx0nUKc0UrtzDvxzDFxGwSCvn9PQ72/TmzuNR3CwOFXJ+FurL1Jg8PjWWctVH3V53aIIP9TnrhuJWw9r0zMofqngUj8/Rfdcp+hUxOznSF/IpN/Uk'
        b'xkzTOVJOHhnst/uUn7QRQw7qn9krx5XSkpn66eeo8r/83Jkam9Qpx7K3yVni9Ey9+XpzM9BSVRz/FWfbu7Qck31aCIhqZKcrNiYf99y4h/eZ9TEiyJDjJj41cMeAwQ3R'
        b'jeuaqKFqcLhek1kLmKi5ogFqBXaaTAkm/pU8OjE6d0Ctr4Gi3Cg3y+/JI+GDyHrOZvQoj8orLCLUlXQeqKdxH1J7RK0x+IE8239zZj2Nus3RnZ9SNZE+rE/X7jnFsD6e'
        b'4BQVuEnV0FagnpsANv5/1L0HQFNJHj/+Ugi9mdBb6ITeBEGKCCIdFcSuhKYogoaABbEXEMVgIzQJYgk2sILdndl2W8HAEl3vdO+23t7u2lb33PabmZdAQN1z9/Z+v///'
        b'9nwk8/LmzZuZ951v+czn60m8C98IiCfE/7WJ2UVZhrlU4fQjZxml3uipm+/VlmWmLvnY33Kt61vV/xqXujdYMMf8ypSP7Kxntm3gXFnXZR5R6DF+x96Y5BmWcdv2zV/x'
        b'VdtTuyfGTxY8Oe4m2O/+lmhNlWv0d48ivtv2OOqXxp/Yy/m7S9+7p3ONq2uQ+PpX3whueN1rt4355q2vzij/Oi3tkaw2Wxlj8PlA1YHZ6TO7Xr/cYjCvXfsnk7nwTNV+'
        b'6a5HXR94Lvtbx3e35YZyj78/uHnJw7aYe6Br2YOb//5ofiTzTlz4DEZpNvfrIK0Dn/61YKzVmq9uXTWsWl9mfnqTp2iPz/vHpM/sF8Sd8/7g2DsSd6c7/PrkzTp5c87N'
        b'OvfsxJW01AXBejOmDniwvUN+mPCPWYP+LvqTF5T/dO2j6KSncRLDE1u3u541e/iWx7cH3v3mLzvWOAX+/fHSDT1tW5d/yD367eLkzjT2J9tKTezezfjLel6t3L2mZKz2'
        b'qWdvHdxuGnvs0umPfohu//pusetfV9yavth51+zPn4kKqrb37F7gpBNbcu6L5S1vfJB17APZOz/7pX/0oc7D9oK8rUXxK458KLiicC+a+fm/3xL/OqHlyyPXvv+5UnF1'
        b'4Z4BvzcenDu+r/OdIn7VzimPvlhz6/uK27zJkzI9J10yrghy6Pi3XePZ6vPPpg/y5/7yJWw4dfSUJI75mV+Ep3OIx/RG/207svwzjAvmfiA59Y8TtcvGH23Nzx784L1v'
        b'ivt/WfPrL48Fl55+4ZH+tU59rOzj3mXHu0vXnPhl1ydjmyeG2RzZ+nTclgbRodZ33/WWvha5/dtfGJvsbpQvf+3LFoEJjTquMoM9yQK8R4lDcRYyrUCnJ7Lt9qiMTi1v'
        b'bMXB2vQkr0TMbiZhlsCNsI4+e3YVcUW2WMKdqd5oXQpggBOgR8370gK2FxCbMhHu9EzFHFo6oI25Fu43odmhG+ytS8Xl5YbgrK4RqDU2hmcMlmtR5vAAC7SAbriXtk4v'
        b'OIJNXmCbiaY5XQqqaWD+gUU5sCYVnMD45E1MsJkxOTeZLAElYLupV5LKoOVMY4I9k3guNExdDDeCM8nIyN+gae8yYTc5m1tZTMjM0YNsnIjup6uPrgX7UH8Q+bgBNmSj'
        b'ZxL4YBA0J5vJgp3OPuZ0S2WgGtap6VwwlYu9XRCotacpWU7paeF6qxJTkP2tD07DM+AkE7ZwwV7S3tWzopMTU1E3g3YG7ud5zHxYb05atBhuCVGvZngtA5ugxAK1qIm0'
        b'aBxFsNTV6SkCNHzjmbB2BS8Ntgos/h8AiQkW5iVwYZVFPLxqiow5Kov4NJNeuIqnMtiGVsjWNLNCVpAx96axA07VtLputcxFYeEuYeNvFXUVslCFhZeEfcuCL+PtWSdh'
        b'f2JqJXWRaQ2auvWbusmdlDzL+sS6RGlOa2FDYdMSeUBX5uDY+L6x8ZJEBW+yhKHk8iTT9o2VTu7nOt/iOciYe9PRAozzWO1ZKWHfsbKVTpWxZWWHDRRWPhLOLXNHmeNR'
        b'9zZ3uUdXvMJpvMI8Atlw5hZSljSmRUuaKylCX7nmUte9EbIYWa7c8XC+PLaLcXKSLK0rv99lvNLaURKrtLaT6Q1Ye0q0lZZWrdoN2jJthaW/REvJtZQG7A27ZesuZ3Rq'
        b'd2h3sbqKBvwn3ohXeCQrbFMkk5TWDpLYuxY2yOKSzR5w8OtyGcAm0g/3bB3bYuXa7SkDtv6SSbesXWXCowVtBXJkiYxTWIeha7gWShtkx0ozpaGSOEwILm4Kk7NO6g/Y'
        b'BEvisBaSUJcgzWyZ088TKPkuMvFhfUmMJF9SIEkcUlGUNg51cfdQLdOlEXSWLoWN36DN2F6bsV2Bkri7FnzafOQ7EsOJJS88adxjruBPQGU2fFlgc7jSxfVofFu8PLjL'
        b'TOES2uM44DKekITTRpSbO2lzZleQwi0U208usgxkKU6XB8kiusb2O49TIlOKNp4OslBVsnxZCrrcRXA0tS21y63HReES/eLvKW0pXZYKl3D0zcS0XrtOe6/u01kMaoz7'
        b'09kMyoQ3NHNGTqhRk82Yd9OYj8qk0yWY3lrJtahKfroQ14Jm2rNSrNu+ph8bnOyj9QYVhY/RMR7oz1seevgYNDEE/XnXRz85UpfW6gxus5cJxYtus/OEYuFt3YX54gXi'
        b'QnHR79uPW4pJjDXTdNGaIH6XyGGcnspG+hHZSEuxJuj8BNlIzr9HHTyMFJtcpobGP2RvFFC0vUFoc7WQbUQFsYZoctl/Ik3uaP5zLeoFvNpI98TeRmNwfk5yOt6zQQJc'
        b'SHqOAd2scg+0THUVFbb//Ud2Kdb8T7muPissRmbFlDydAr0Cgxz/hTkUq2tyPucDc8rvDMvyTB89TqzRXY4NnuEEAHjchoWYmVqIYT0TU3EvyyB5NfPkhf3ccb0G4zTU'
        b'eo7IBA/TGHx4kXZPmOw11HszjuqwSq3eY3BpSQYaVLvfM55YKv8/Hs/RuLWhFozks3dZk6RFnKw/fvJvzcEKFjLWosFatZXPQcNlQAUWsSwze19puEpHDJelerhUDPYP'
        b'ytFwGVpIxNLMjwycnh8r01cdK1wxOazRHKsyPFaWf85YLaLofDdkrBg02jCI/T8ZrdEeiRe9fRyaT/fkTOawuYh0Jqk1U88ZNBN3wGSuPXPNlO91qWWfrOtxf2MhwUFk'
        b'gUtgRwYOGlDB8XAzBQ7Y+ZKqJs0F6zN84H6vBLgDbExkUZxZTAY4Ji5cujmQSUDoRh4TzgoL0aQwpB0B4a1jpZNMD221ykg12aSb6X5bf4dvdpVwy1+2BrADGv1jlMsN'
        b'wqfpVGoZrDbQ2iE0+OeUtdu1WJsMtn/Q86t/y2cTLlUJdgSst6v5OUWYEl6ks5ZyP9I4zk0c+k7Qyo9Z32Qb3HvzmyWrOLYhgdpnnT6u8g+S+qzXzqikHI5Y+gc3fG8J'
        b'LX+2Sr3Fs5o5wfE1OfFB/LPXPKRqqUCHKHTeyyd6+XjgaDsHnIMbQCPTZxbcRSuKW+B1W5VWzV+q1qoZ5bTWfEAfXieh+hq403lJOmZW3oE0Wx01d19tGmyjI0TwUIg6'
        b'SAR3raHp+S7qgqPgOFF8YTXSfJeD/WuZTkHh9BbMLniaS+jdPfVs1GEgniFpLzgFJbDNK8FbGICjNexQBjil703HlqRjU+i4EqhHiqs6tgRq3ATar7JkaVNEKxzWAg2w'
        b'DF2WV7AAr4ciZ/U72USpIiNYhFrWh9eF74moirtlYifNa13SsETurrAPVJgEVcV8amIuWS51VZjwZaYDJs5VMUquWVXc3THcTy3spEK8tNexkZ5nwqvXr9OXZspiWmYO'
        b'2nr32XrLpyps/T4y8VcamOxKqU7ZkYY/JFcnS3VkwS3G/QYeqKL60LrQ+ojdETJ2L9dbJlZwvaviyNqvIR20RV/j52D/Jp0Gee5szdQk+EnJYZ16lcZCooIIifvU75QU'
        b'GFs34i3VVf19JGEgSWGIvYLzKDFjGiVmTmOIWeZUCTWNKWabU7ORrEBHQ/RPJ4g5jRWq8i0SXyeLxi9jGvwgnWlsLF3UUkKsNY/jSE3TsqCmcaZph6qklFiblOqgUl2N'
        b'Uh1SqodK9TVKdUmpASo11CjVI6VGqNRYo1SflJqgUlONUgNSOgaVcjVKDUkpD5WaaZQakVJzVGqhUWpMSi1RqZVGqQkptUalNhqlphjXjfrIFveDeAz5Dd+PmjdmWHZO'
        b'ZLAp8Rj0O+wv1kMS2Y78ljvNXszLosRm0xxIJkDH29qpwmK8yaFwFxr91WZ6GZOmxPCX0mV8kv7MV0/AIOvOiBVAl1JlPBNRNNp8KGmB9tBY4ZVbV5X/jDnCO/3fa2LM'
        b'1Rl6icWF4kJhUeHq/FKSI3BE2wuLS8V4j4avnl74MqFIuJSP3+twPs73hj/xxSV8IX3JlLh4fkFhUf6o5GSqRxyxwNimlWH36XQtsB5JJVg9BSch88lSUZyAk7DK25dB'
        b'BcJtkxnaoZFLygIonBECXMzTX7Y8A50El+Fp9a8zdbDzD1alEj5wJHFz+ToGoEYFT54MezC4FV6CFzXo5K/CA8QlmjiO44Vpw3clp2JZ3MA0Z1Z4gsM0OvW0sZFXUqqv'
        b'j2cS2S9QUsF1Z8EmTCpKu1Nr4JbQ5MAkJsWAnRRoYMBuUA8byUKYOh5eRStACoNi5jDglcQA0JBF+/5q4QlRsm+SwDDVOxHdU7+ECRuQ0b+DQNUM4ZWlpK3VcCfefQxr'
        b'UtBvjGAra2IKbCYVWOmhFWR+HDiZgFqGazB2Zs2Ex2A7DZCunQDlKn8CfiLQzQRNjAo7M3I2Gl4uTU5M9URnmcTp6AgbwYZZYAONyN4DO2YmpySCi/CoRkYDeHQu3fLd'
        b'8+EFWGMLqjSJgNNAHcHBTYaH4VFV1oj5jHHFfnM5pJNSDCbAmpngokZeCHgZnqGxa2ccyDrpN9FTM7sDvKwCocGWtRkZueAMRXCAFUCKbAIC6Ds/ZbwqO4NmagZ4vigM'
        b'7p5IN/YauA4OJsOT4Ihmcgir2TQ6Vr4OXPCCG9B/VX6+mskhJoI2uh/bcLYUOj0EnRtiwxwghT2RhLQ/Cu4180Lrbd0LszjgHA7wNJASHOACeHhZMqiL8U1KJQYM6ngj'
        b'KGPNA7VwA3H32i6ggW9ddsKiAmMrqjCj0oZRehlJbb7s7fPT56UDf97Vv76T3RWwwTF7R8Enr1mMddstr+6M2O299Iw73OT4T+597k+Tf5n07uTLly+UWor9Hp/74k7L'
        b'3yrMD/ycfm8tM+Le99Wsj79Y/JSlb3xvbvOJDa95Sq8+LND7fM+lz+2N3fK6Z2u5Hrud7vnVvUjluJUdyRzn3Q9iVjrHbB+bd+mdGZ7uM/Jv3Pk66PEHyzqa72c5HfPf'
        b'/uHhafcjLtbHWDd8O8twuY3ZXOPlP+sV2y1vmtSZtTb2Yd2psvUfdH+5kSVOrfE90ZOhv/zjxSs2HdTLj1q+2zTsgWDWneKCD8COCN0rP9x263aL4H705iPeOPDD30zH'
        b'u1u3ZySsP94cX8XNMbIR7nUzv/vXsLq7g7c/mZ/z0ZeRbzddvLTtvXnl/bcF11Kbyx6dDVu08Grgh5ygDwYjUvzeG+/9o2hs0y+pJVq1Y+8M3i8Umv9YYvIh+Hbs1YCn'
        b'cec3fPPxNd7YpOIIyfGlIduO7Y5sit2X2jh17/tvVYZ07E899v0u65/bZ/+6qDBkW1VpzJE1Id9bj2t67HAmcd2+98c/MooP2fXtyRunt/5o7fvukcYtfz0+tulcRFNh'
        b'0cPkS5Jfo9ngrQQnTu79u9cYrStXz/3LBoG1iu/D2sIrxy7Be0jpWs6gOWPhBXA9OcVzCtzvS5/VL2LCQ7ABHidKmQ4D0zMj1ZuOounAGiaQ8StBK4MwFFRAOdiJ+UzA'
        b'MW3BUJDLDGxj64CNqwin8awMsO0lxC37oBx2ihJU1LPT/XEahPF+RDhykII/rpTAfPzBBnAS1GBCmgPwgkpC6pcykcTYrU94g2Hn2Gg1p8tqII+B8miajKER7vVGVyaB'
        b'Tnh5WHyawwPscHhAlyiknqXa6LaHwNZ0LD9ZRYwssBmeoRXoXeB8PqiJ108n8pMFWxlAAs/50wpytXcqunCrXTp6oYgANVrEGrdYRQORgZ6sm2R10JCelbB9TCgLtAXn'
        b'0/ivTaDNDdSkDwvQVLh/TAULdPMCSN9HwyOeJJcauBKkEqP6U9Fjx6XQdCU7wT4uOp9oDK+rJKm+KxPKxGLS+ky/CV6+sBNsUNEF01zB27JoZokecMAD1ASAehWLBpF5'
        b'xrosMerqw+QBfeEV2I5vf8RXJbg4OkyrsfAiqWChDYWHZFhoIbW+fQw8jEHNbUvI1IqC7Uj41fj5FoGLtPTSR7MHdctZG1rf3xAIroKapLT0lERayhvFsuLhfrDjMXZ6'
        b'zcgBV73SfJ5PIyO0JtJtQpm2KdgkpLtyY5ALqAFH4Rm4a2jxNVrICgdSO5rWph60OKKH0RB+kZZjxrHAFfskMsnQHLtgjhqbkIgP5EVw8xxjxAJHwKlCgdGfBOzCh5Gc'
        b'wLTGjne83jZRKW6Y1QLpQSpWi9ks2oMgyqQdPrK4Qa7gJlegtHGQxKlcp3atoQ2hmNFCHqyw8cfFdElUQ5TcZdDG76aN3x17j15BlMI+utcy+paNh5ynsPGVxN21cbhj'
        b'79nrFa+wn9xrOVlp5yhza5krYe/Vu+XgLc/s8jg5X+EQgb4bYMCX+1GPNg/5eIVTKCoxVtryMZRINr0pHX3VHfX1Ft9Hnte5qGNR1yqFb4yCPxEVGt5y9JWLO1d2rOzR'
        b'U/jFKhzjUKHRCwuVDs6tKxtWynUUDgH49vccnPEfpZVdq2WDpcxDYeUl4dzlWklClBZ8WXy/hecn7r5KO2dZfMt8eVbXpJPzem3HK22dZCEtafhP2ICtzyNttoe1lN1s'
        b'cN+IEvjJVw14hPU4DXhEDnrE9nnE3oh921ThkSw1vOUk6CrvKRwITeh3SpRqK70CugQDXhFS7X5LD6XH2K4cdJ1Uu9lQ6R3W4zjgTU4IlJ7+XVYDnuN7YgY8o9BZY6V/'
        b'qJTdatBgMGDp85+bpvE1fMDWF/8dN2Dr/chQW9ViE8rMqj6lLmWQF9jHC+wK6fEbCErq5yUrvdFw4xP9PME9R1fSdTYOreMaxsmSFDZ+Ep27XBvJONxHCf0W3p8I/JV2'
        b'rrKCATsf+coerZPrem2jlbYusix0L/x31oCtH+olT3xPDKETBKCH8hjfM3HAI3rQY1Kfx6QbuW8HKDxS6V5aeUN3IDSp3ykZ91JQV+KAV9R/6qXArrABz8ge4YDnBNJL'
        b'gWGol4wajAYs/V6lcZrfZw/Y+uO/M1GHoY5SNZp0VFpd2iAvuI8X3DWzp2RgbFo/Lx1zKQg6BKiz0Ml+nrsSd9Z+Iw1j24Dez2/yElfcK/nLR2OKyE72WFTjXk1LPD8T'
        b'W+Lf/05LnCQiauR4Usf0x7L+cGptkTPzpanbhyVQRJFwaU6eMOoBavZw0vhnTtjUUptjQ/vwRyTRFh2n/mBieVXib+0FpYULi/PzXpbxexLqzce4WVzmiGaRNpUU8PHV'
        b'QnGZ6E9InF5At4i9ICcw57ea8xQ3p2uolzzii4QL+YUF/EIxvxAn5Z4YOHGo1/6U/Oiiz6iXDiJp0bORLbIlKdFF+XmF4hIRvzDvz8kpL/LT+u1W/IxbMZzW3l7VCiHO'
        b'JP4n5bZXDZHugqUleYUFhb89bXAWRJEjQ90ed9yeImGpmE9fnPtnNmyRumH5K/Nzy8S/3TDWyIa5DDWMvvhPb5U2TXPxm23i6I94xzzVk1qsIQLQ7KYr+nOmNWlZXn4O'
        b'mqS/1TLdkS1zIG8/uYovzCV0Jf99cxaqh0/91vxWgwxGDp/jiLftz2+S2qP9W00yHtkkV00fGR5BtYNsZLM07zgyvTGGqjKzWEPQTypDw9m3jGGDmq3h/GOMcPNR0Qzi'
        b'/Huu9KVh2BeF7TgvgqayRydfZvxPkmQzV/vrkfm/YlE+6j0R6kI09TXeAhF6TUVoMRTz0YgXl4hH+R1fklZ7znFfOq32j+UHRqbVfjCFpNV+jN4KYm3Fwf1LsB07ZMPC'
        b'7dm0GQu6YM8LMjp/jbnyHNTL+VDzhiGkBQvzxSNybC+eyaBsCS1eL8/zd6Z4xncTLUIPx9XXSPGcO/MPpXh+lQgyGtD/UQT5VVDIaOhMm1OZBJqxE+wfjiAHCvOoTdlv'
        b'VvlHcCx1cqYU3EthUfEtrDwXCzSOdF4lQ3AKGaqHYK3GYKpGssH4t4PMogf/cVBLVYM6hlIZjWhQ3b3kY9uXSOL2p4+IO5NRxVvYXynujG8tKkKl1voacefleIStfm/c'
        b'mXhpLXVnJWM0RVsBg2IbM8BRVz+C/l0y2SQZWf2w1h6VBzHAWbAJbCicNu4EuzQED8NCBgZtSwp0cgMLDHJMFr79iQd1Bkp3Nmy0fC3iTf4R/638z/3jK91cT+VzPhBT'
        b'hz/TZhbUqmfyixR3PMWGn/MbdLht+lwXk051pDtVydb5Pnsmg23q9cSIYRp4z9JexpYVyPN6LYJ6TYJGvDkv6tnn7ydaivp1jLpf0R2eCHG/6v4Z2ekN6DeHTQQknYCa'
        b'CmL/T8TkZiQmffRiMTS9lFYUkGAcGcAp5ZeKC4uK+OXCosK8UTLyRTJfKzOeRPh9UiuM+AwT9Iz88pkFT0IKF2QvYZRuQGfmGv6DjtXrIsn5zynhLQ0bYrY6VsVYHarV'
        b'7b7EE0rCZdbmEYv5BQEb38+BuUc9+r2NnN4HBz9oNC229ks4HGH01MKfHeQVuDmAHdTg33aLr3PT4s1dUSY3dna8y25rClhv0b3GcpORxcTg9cYZ+SZ73uDl3V0/sTHI'
        b'kJqhxf1F+a5Ah/i6YhzBDq+EHA3vkRG4wJoMO8A12td1FW6Hp0cGeKLNKvxVKdMswXEwKlhitagC1oCz9EbH46AFrNeMAOH4z/qFsAnupcP5FnAjPJwML8AtI8Mx4EQi'
        b'DSg9DiXgxFDGdNgyBbTCfXPoPapBll6wOj0RnGBTnCLYAeuYTvpAlaTvKKyDW5PROW8OxbZlwMNu4IwWqBNovdwUxjAOjSi8TmHpAjLgw+aluoS8VtvoSX9/4iwGZWlb'
        b'X1lfKam8ZUMgmRX1FZIKWd7RJUeXyJbcssEoufq19Wsla+UunT6dPnIfVHaPZ1mfWpc6yPPv5fnLMo/OaZsjYdzi4gC95SDX8ybXE2MhOQ2cJh1JDMZsJtUl7UmRBQzw'
        b'XNDpPq6nPLOfG4AqumVhMyL0/oJl74WRdw3EgWgldh6sQgcHfc09RGQhxJH337Ua4rERGIiScZ2f49pn4k+EiW8+/jQHH6bjwzR8+BrLciGHoF+HBJcoARWoEimbvwrj'
        b'HgYciP6Fx42FrF4RpogX3cZsfzpqC+u2jtqkuc2htf/bHFr9vq2j1npv6wzBLr4Z6pdhAj2jP4dAj7hTR3Li0cPgxlEdcAi81HKYCo9paPKQg6nwghrEUs9+Q9enzFkM'
        b'Q7dHFDmyKCO3+6TgQTlTzSE3DnPIhRMKOXP7WyYCusQ8vCp+mHkOk8pxJzAI9ZyqKBAXBZMSFalcMCaVCyGkciouukjMRRdNqOhUJeG4JIKUqG6GyfDMJzLI3VRFY3FR'
        b'KClRXYZZ9SzDNCsaj0siqxKe6OgZBj8wp6wc+yz92sLax6M/VYlP2SaGtk8odKCp6bAEMUdqySZ4NhXuWJtPywk9UMsEl0th4wg5PUb19xF+eyOsfwP+oU3gH9boH2Ma'
        b'Sw11QAsQL8sMKW//BeQD1YEBJXoEAEFDPaz9qHm6o8ASusNtmKY/BD7BS6ABagEbw0M0WqD3wl9zkE1hOOJ3+iOezHqakbpd02xIzTxStwm+pogxdJXB0FUM9ZUYFqP6'
        b'Zz3NNJSjqsUW2VlsVBOBxmQZZRlnmWaNyeJmmWVZBxliQMqIeg1Htkb1Dz+5HupjbqhqC+I0OwK54RAYh0GWIarVBLc0yzzLIssyywrVbYJhLSPqNnqublW9uNXTzDTq'
        b'5qhqNSE1WqLadDEcZkRtxhr9azHcv6i3mBgko9HDJtOsxKZZlHjMNGPisrC/baRaONAfvMe9MBBJ19X/0ovhjyzHigb6W8oXIh1DU/PAYBKhmC8UYa/l8rJCJKX0CpCl'
        b'Rn6Th77mirEHoVDMF4uExaXCXOxyKfXV00sUI42lRKSqcqg2YemQAY1UnWK+kL+wsDy/WFVViWgVutTXl79CKCouLF4YHq6nh2M+2AYf1eAhjWjipMwYX35cSbG7mF9W'
        b'ms/HrVsmKskrI01x1BMwacf0X5ij9pWqMJMGj4ooNW5TSBvrGCeE8TpaKm2PlaH1J+4mLUDa3rPn8DpqTW+p+vleCbIz1G3YvkZjpNnXpOfwwJFxyPPlJxK/al4JuiMy'
        b'tPn5KwtLxbhkBe7GHJWDEf1QfUOV/4W+53NemRWFuBHoTEEZulyYl4fGWnXP4jz0jy9ctqyksBhVqOk/HaW6alPPq64GZVHoC+wGJ1dqpltKUAcgYXWhH9wNd6aQNErT'
        b'ElLS1NkMwHW4TR8eBsdFZX6oisyp4hEVgG5wfiiKia5ThU7L4Tbdyni4jcacnIMnRHAPsqMS2JSWOwPsnQ+loApeJ5xW8JJfEs2mlOq0EnRWEnSIF9wJOjN84BF4Bh4O'
        b'pFi+lHEE0wd0u4CtLmlkg+0CcGwCyQhM9temBIAzUz0IYGrKNJ8sJhUqQGrhNNhNuJyWGOp6oZlaSoEr8EAp2AOrynAuhfGwujSZNN6qjDQfVqVMxUksvGFtKp3wYWqJ'
        b'NlzvaEBQNz7Tx5Yu10qpwJF4CmxP8S48XtfILrXHuMOF084KlyK930il92/Dev9WKzf717OBjjDfn1l2RiLbY5rovoSyOfIBlZZyOjtEempNiO2lntNf6c2wzwkUbuzS'
        b't1z25T/eWGhzx+IX/gIq9d5bR2cfcJROqnPc4VhlVXB8bG5EriBDUBqxSTezjJFrmbuef0QQ463MnaD9l/d1KjbOjOndbPXm05ZNcAWQ5ggNLK9x42ucL2SHFD1h5hr8'
        b'Pbqc+Qv3jXNmbg782slpY7rn2m6q5U08t143kt21bT57z6QwVqzeautPJzw0neNfYR9huDmAWrXGf75/kOStXfe0PLJvm8h2CMxf1w1ykC/Q8X3n2HuyG7KdOmVukuOB'
        b'DZ9a5W34VjvGYcWSgllbU+KZx97hHxs3h/r827Fjv/tYwCWgD3dwKVAF/QIH4L4cRsCsdTQu4ghoA1IM2xjCbMDtoIHGbbBt6TzZfHA1Gc8u2Ar3DEGwvMB+2p44BjuX'
        b'eA3BSczBBXCKBc4Rm2HWZKvkFE/fBNDhoQEokReQar3mwLYR5DFz4DZwOhJcpSEN8ulwQzIG3YEdcKM3zlujy2OCNqQqqaL4O41gDdJR0vAL4IlUOXCOxSmcmgs3kdpt'
        b'YTOysvzgdqy/cICcCY6wvdHN9pKz3uUGGMqyDh7QQLNUggsUnZf6uB44gWws1F1sRwZ6W6SghV1CP+1lr7GaG+5gQ0YQbC+ntxfumAYaVTmZ8WuNXlIfjjVopSzABXbC'
        b'GLiR9EnExIohy5DDZYJtsNoQNIM2ejgOwy5tnIwkGWf6wE2Lhu1alCmoZ4Fds9aQR19OsobXpA/LCaMMFmienwrOe6j4gHSdYI0GIO7oQtBk5UsefIyvwYjULHEuODnL'
        b'fJM08gTRYD+Uo9ahmkF1OqxNSIW1HHjZGK3VLHg9EDYKdF5ZI8fWuhreoAFtsBi57o1EOExh0AZg2mxkADrQRt8da5de13iF9eRe3mSlhX39uvp1knWkMFphPaGXN0Fp'
        b'YVW/om5F/bq6dTKxwsJbwlaDHiIaIuRs+UKFTYhER/2rtXVrZXmDFl43LZBubF6fXJcsY/fzXG9Z2UkXyVmDVt79Vt5dTKWldatOg06vY2DXjO45p+cMOE7ot4x5yqKs'
        b'fXqtvO9Z2bRaNFi02jfYy3UGrQJuWgWQBo3rCR5Qt+qTURXa81sXNixsKmwtaShR2PsN2of32Ycr7CN6pg7YR0tZpOp76PHw5rDcfgsBQWlEK+wn9FpOUNo5YiCG0lFA'
        b'ovp8d4ygUDoJjnq3eQ86hfU5hfW4KJyiJez9xk+tUD3ops+e6qk+lBLjPcQ5fqzW627Bk3W03hyrP1lL9y0d/cmWqn1iOhrxbqxWvBxgjgc1ewTCnNiLDejKaLWdi/eB'
        b'VcxCdq7jA2TnOv4eOxenyvxvYkZavxUNeW7qqUPb2ThCMhzaDhpSSZ7XQTT0jz8p1o1jOaJbL4/Ei5oxOltfM3wqWsAZBcT/vxmhGb1V5/9bEZpFSD3+kjmqe14SdJmy'
        b'eAwddNkGBjifjQi7fEW5hTAeVz8TMGjJfgZ0VcxCC+Mo0UjLRXhQ9LK4i9uoKVeaW7SAUHb8Rvhl7pz/MvxyCD3mQs3wS/Kc/x+GX0ZHAl8SfnkzLJlBwi+loaV0+CXy'
        b'a40AzFD4RZuKP8DKP78GjSgf96Y/3DI0movRsqs5oDxw+FXiL68yuKPDMDlz/swwjBxLbM0wjHDOHwrDkO1Y12CnIw7EMFimdBwGtoI6snFAOxhcx6EYRuQEOhIDj8wu'
        b'ZHytYJFADCN/36sFYshGysOfy97WZl1Z+eqBmEe4ry1f1tej4zEJcxi6pl5PzP/reAy+ragDdXCBZjwmcc4ficcg8YC9qSPeqCFzfTFFh2VUm2w4yFTX1jDWmSOM9T9j'
        b'c02B3uR8MTK2VeuYpntk2DpfKsovoC3l51BeyKAW5YvLRMWl4fwYfjjZSBSerRqgbH5JzmJkw79CTIddhqcPOArO4kQLKrDu9CkzfLJmDO+8ASdtNTbfgPXBuothI9xD'
        b'0ienp3GThwxguBs0WmIreqQVOU1fG9mzF+H2wk0+q9mleEfT36IO0RZjFpITugX6SOS7pZhcWu8oNWtaQwUdmWm5Sdd582Ejs0SLgmyJsEq4pUOHefso3Jqnn1nJyfXf'
        b'47T7F+ab/m9SLmX+lNhL27w7e2rh1A9uSADrwBsXWmyKxzuDa/7xZLp/8ZOhbOFKAYfeDXkV7liqNpUK4VkMvk+DPcTecQWHy0ah65fDbZWuYB+J6ixaFYuNNBfuaGj9'
        b'MYoYeFPhKSgZ2tzj6BswHspJvY5GMcnDlgK8Dmr1ZzPhqVhQTSD5k+bCxpdA8i/D/bBTYPl7dlxq8G7o4x2Xqqlz23rU26txjry/S1TScTWSjpYusji5C0ZoKiyCMUXC'
        b'c3o70bUn3sgccE1UWCf18pJuWTvKXJp8JNpKrnX9+LrxMhdaM8Zp7Pq5gYT4KlJhHdXLi0IWhEQT6qlSfUms47cjPDrUMKyTlhBnsPTFOQBWqFVfLIKXYAlh+eD3bq48'
        b'+JIV1+BRHkVrTapt2BTS6xj/kw3zzNVlRDKIn0dRlRSo99P994Iihq7zJYLiJcv8j3lvsQi52Ruz2TRXmx7ekv3aDrcpfcyt/lsptxSzd56UGDRbUVubWI3l/gImWedB'
        b'T0o+oWpQ7QYwBaexQ8AatrBXwxa4i7wjE5FEaVXvQQM1ZmQbGtiwBJ59sRowtEZE4qXpRZNb1W+ai9P92XMZlI3DoLVnn7WnPFhh7Y/mKzL40MTuNXHV5GJ76ZSk2diG'
        b'tT18e1EP6qhtGjrAk+S5v5cCAIthpDeTHcbapcLy/AXC0rQRvmWOejIWU+rFiviW6cVKB5kbVBDnf+JdRgr96odD0xL72vNUKT9fOCljhvz9+WIhhkoKaVDW0pJytNTh'
        b'vF/qel51BtO/UfVKOHY6Ew+/N/Y0Ly0rFWNPM/3GlIoLi2ngKLYeieuYtiBHwOywox9Vlqf5cuB7i4Qr6MdDbX4Fr7JeGc53NAMcKnrp0qleN9fCM+qlE8gNCLZmFjgM'
        b'dnklMak5QMJIoOA+UA22pBEGuvYubZq6jk2l32c3MMQ5jplkdoZ/ha2btDQ6LUgdqJvllc6kvHUZ0yjYyHItfD0pklH6KZ5Dm+dsqYvUB/4mW/3q1zr9/Z7b/tnh42Y2'
        b'XxpovWcypsMox+K1cv2Jy7/X/qE9NfpgzqbPdSx80x/+ramoebyOF1Oo3/raskPKfF0w9pug8BOfSXYXn/+XV73ghm3tBbeem8nNxvsO+FUvcyo7wD3ZVLexf6aCefPA'
        b'Phf398aKjz2t66570rJl2YTPjVelpfvta3pncNzRorx73n9tOXSnIHfTgnda8kLEzl9FpUXB8nHVQOEnmh/qd7PHzH7Frz0tlsFTj2++/03oWz0t+jOvrqNsrurF6vD6'
        b'Xn9S10d5Pmy63VER/oFf66/LXRcLrgjo5MpwK+q6PV4JsHHq8H66VIr2YG4ZE66xok+xJj5GeAVeJZIJ1oHLoJt4XufBjaNW9atwC70VbusU2OqVZJum9kW2wMYVxJGn'
        b'CxuyvDx9VTu6xOCy7ngmaNWHZ4nBCq9XwMu0KzIYHB/2RtKuSHh1LXFF5i4D27AHdo2RBoE3E9A0aGHT4SXiPwVy0KzyoXqzwDaB3h8Iz2PO0+HNTrSGoK3iZLht/gIB'
        b'isqJ8BykheeDlXP/mGZghom62INmrv1mrvIxKsdgU5gk7imLMne7z8HJgec0zJFbdcUo7ELq9GhOJg1XooV1/cq6lciOmHZYR2EhIOf3VUjYd7nW2Ge4UCYe5TOU8ZqN'
        b'VN48G4m+RCzRf2qGboWa8OypCSr+yMqbnKEdc69Zmcb6akGTMXEMLeirHxul+zpDP26MyjGnq7EUXPyPu1FKdSkNpiZ6iXgDX/UmOuzWdM8J8RLh+PD3uucwlS0yVImL'
        b'kCwWukNbLGhwRwXGnLCLhMULc7U15BdXvXrgjIyYJwKvHkKWkC3UEnLQKoJD0ZhfBgeOjUhAmqMKdTOzeMgkwrnuzIK4qvVFO0NfY33RQeuLtsb6ojNiJdGO1iHry3Ol'
        b'mgaRsBgtdXoxeXl4h0Zx/oqRUDUc/aMjiXRgM7dEJMovXVZSnFdYvFCDXgAtDOFCsVgUnj1km2YTYY+XrhJ+dnamqCw/O9tbtRekPF9EMDQkHq0nfGnsmZ8rLMZLjKgE'
        b'42zUoG2xUITeEn6OsHjJ8Do2Ir45SoF7YXTT91VWQLzi4fBq6bL8XNJib7qXyPo2vPOnuGxpTr7opbHXoYlC32Z4a86KRYW5i0YspKSFxcKl+eQOJfQ+A/VzLCopykMi'
        b'QmMZHrULYalQtCQ/j47blvLpDUS+/HSM1V5RWErfAekGi0ry+OEFZcW5aLjQb9TWSDa5UN2aXGFREerznPyCEtUqPkSeQQ9KGd7wgAP0QnKd5hgOPfkQACucP3o30DBW'
        b'XF2vGjOuujYnMOf5qzT3EI36PX7zkIqSkc4PCQrzCSDfy5BMRZM2L1/dlepr0VSiR8mXND4uv0BYViQuVU+xoWtfOALupXw6Heyq0XqMauRx05YhfR99eoFWNUK9cX2B'
        b'ehOhSmEFdlWWBoqYFMMmpoQC3fDsFOKsKosGF/XLlzMoRhQ4C6sIGzA8pqYGrjZc6YVMXmQKwyNACmoZsbBdWIYFwHywsRBdh30ENRmuflM9fH08YJWfZ2IqHXxfBs+I'
        b's+goNmgFp3TBoVj7slRc52mwh6NfDi+g3xFXYZYHrIW13h4JqeD0NFzdDHItrgVn0gC7bWDXJD1wIA3UrtUDx+AWahy8ZghrwEXQUeaLazwJjuMskxoBfdoCGY7k585f'
        b'EK8D2mA93ExTkxTC47AO6xOqyPtUDxpG6i3wSdKiIseIvDiwMQt0Eh3PvABu9IK7ORTDNBNco8ABjAkliGse6q7zsB2JcX24ZSw6nHMn/Jvhoivoz1dY8U8ri8BtrAWX'
        b'3GCNT1JqRgJJTZKIbrvDC2uXQ03A/eGdlOKbCPa5+HhyKFgjMFgeDi+Q/oZtGabP6ac73DGXR2oK6MhUOXYEHMxzelEXtLNhPT2Gh1J55Mawa42KHyULrKcpUDZPnKaG'
        b'z0IJPEZDaCtgM2wi58vQpwPDCNkpsIYGyTbNz6IZxC7CC+AIzZEC5EiD68TgjL3+ZMYlzPBSeVHg5sAcRgDcBHbSQIr98GJUsmqDvys8Q5OkwMvzyT3XLAKX8FCO4EcZ'
        b'H8+aGJ9DX90Be8KTNQG57pmsmWCjDyE5Ae1jQL0a87sOnKdhvxVzQXM8Oa9tCfYljyTrgG0mrHml/qRybViniveC6+vUHChgK+pJkvpvL5QyVSQoFuL5DD9wnU7hBw+D'
        b'RrgP1mCGEG+wWU2Eck5InsgFbsT5WYYYAULHER4UpLO20kQzW2baJRM2gKnwlIrJxAN20+nemkHjFK+RNCYTwS5WDjypQ0bXCPZwaB6TMHCZpjKR5mQRGhP0hlSBK16j'
        b'NvqD2lXDPCb+YDd9m/PwEqxX2e1LwHmmym4H18BF8uiVlQkZUDId17qhHLZQxYvBBjot4BmwxbTUSFQGTxvA08ZgO+wWM6iVQu5iViJohp0km2NyKGPkT0rNPOG5Muw8'
        b'OMKCLQsW04k1t8Jr8DT+YbqN+qcrxMt1RYZGHMqDxYYbdc3oXHYHZk2CZ8vgudLlBsvBTmNRGYsyAbu5tqxQ2AQvlmF8bWgC6C5dXqZHajHWQ49+XheeRjfFV6AGkNtH'
        b'z+dolcTSCSfb4G6wa+gK9S8mxXDzWTFgL+gqwzyUsDUEXBj6kapx4CI8gbRfcIrtBprnkBbmrABdGnWJRfAcbuIp7iRWOJQto59iCxJAl1W/4i5F1SGpx6FMOEx4yh60'
        b'kBesAh5Hs68G7klno9eoNcMAux0PwFpCczNzVbE+vCBGTTXQNRSBC6BHizJcy0RSvAXupW9xyCwgIxXWZcCdcF8G2ImpyBvFyE5Fr20blNOzrxruBVczpuCgKmgD++Em'
        b'ShgMqsk5pk9gKbxgLELlMi28BDA80ct7ocwfW02efrAGCbFkv9SU9OlY0CPZ7TCB2MreWKDtSEyB29GMBRun65Yml4oOIyFJ5pIQXobVyTh1EyMcHJ+FXqsMHs3bs8kK'
        b'jWsCmrDJPujtTyuH7WzKFDSzwP6k1XS6O+qHaNUHjwkCNr2ytSPJVw1w2HiVAOymVoG9q+hMlvvx7DzOxln8tiKxvVrMIQgoR7hxPoFqISneSK2cEkSb4dtgcyisIUvD'
        b'xjFUYdwCwt+jPYZNLYtD95mQnaI1J5l2LBWG5KZolR5D0n2/POvwjK8zFBNMrrtURnsc+mxq0iLWwynbzbxL3nwQUNZs2lxq3F5r+aapVlSd344FP0f/9OinyVeSSwvv'
        b'PVls97Fxw79+KV93uWLF5Xr4z3Qwe6/8+r4vV/1SIwkDRYuPSdevDPgWmPZwhIrgk04XK+P3lRsOfPjvs5KSRvPpP+kKB1jO8eZaZxLXG+RZZLkE3bgTULJQNNXskuLM'
        b'Y87+yber5XnB9W8+YDa1m+1zmLbSXlp/5O1Vc994s2/vt3F77O8HPZ0TeQKcSJZ6fbZ29eDns+6ef9ftX80HHkRyZ6f15Mxb6rJtbuixdzcsL7gjDf3I6qv4SzfuG4R3'
        b'3E6IbLE/ePzrsg2CwAcpd4s+dDsn+t7nwo32lj7nNe2pmYKl8h0HXM+DwTMrrfunLl+b0zLuYIcTP33e69cF3xTf8juW0DD+rvYjse6DvF6z6Z4nOX9zdP5lntdav+zl'
        b'lf5tVdO/Lbe/LTRq+nSg7FDeU+0z25KqI4Nde9d8d8Kpb9J494QHzSaR82IfpiTefXDxaoXRu++99qHj8b4yl+1fWh0S7gibIiw+6H7i8YfX64/YXXX9a+/Xkvm7Nyz/'
        b'aLNullbTYH7G+cPzpnOm20MTe/nPk6L/supotnWB7JRwUrjpe4u7Ep5u3cq5vDP7i2DlPPbXi7p+1CmfvykyrivV8InuxqWFXenTZ7lr+3YG3L61KrLvL28tWbjkn3lL'
        b'Fucsedg99uLtxitFEdvSAt7ece1ATPnjZ68vXBLV7O388Tc2rn+bdPXEyuLZzac/+eeJujCr9G13vhzvlzf3vqir6V9bKtc6mj3i72C2vBeQa78Avl1h//2B7yq2vbHu'
        b'S5OnaWe6DjUEhVkZej+y797YufrgjH0/Xk066zVj7MMfrZ+see+XCaW+H90v3SD+MOREbFuGjt57O1fcbO598MtT5oOfpoi2ff+tf+ixZYyP4Pc2K7S5snEPK+9PnZLz'
        b'veVFu28/Df+m46ebT8taBtIXvGkmcB1c8+GEI0rO8SXFe+Y0Whe7Vf4yw1u4//4Ps2v+ftr1bxvPzLAvr9f/vjPzanJ2Z+wVUOrs6j/p2ew3VuZ/+czVQ5xR1xlQOz5r'
        b'+XsPlsx9FD/ww/lPlxpfyLYpLz9Yohd1q+axDwj/nPuvX7h/t3pzrf4Do5gdd5JLVq3e9fr+xDXce0+P7KqavqZEz9P6eHrV9M++XXr81wGFyXut2z6BX143qNk0+Tvv'
        b'3eZh7yfO29p89Mcv3nW8+l7fd16i7LBP31lUd55xXWAy48iNYLjOr/Lx9L+n/by58zP5tp3N31Q3Ln27/C8Xa33zg/9dE91e+9fwvRaCAJqjp5UV76WJPODCZg41JpEF'
        b'ZPDqZBIAivVdoVrkwSZdtMrDRniURI4S4QFwnLjA0/F5cKSEUAfVVsKzNHvRSbhzIq0++IB2tfoghNWPiZa6C6wHe+FZrNaeRr+AVYl0qvrEVDfH5SqfVTI4rg264sAF'
        b'0tj5HnB7Mt1MUIvvmQQ3cShTuI0FdkxZRn4CZWD7ahXoEDRHaLq+zME2+pFl6KtXOobsYc58bbg/DCmq1zBpUA/sJh4qT1ANNiarlOUIeILGJYal0a0oTxqBo7PzVMPo'
        b'0LrQRMP89vs5YpQf7IYHVN41UL2cnKqcCaoJzA80mquQfkHursRvZw7qg4ZAfpNdRjrWqiHNmATbLOapSFHHoNUd86KuZTqBrQXEa2iKJH+tVxrqRiO4k0OxgxmgYwak'
        b'IZO5SAVroP1u1+PVbrcxQEJOhghN1YhJsCFL5bATo4HG91wDtoGTJFMA6AYSVbYAZ3BgJpkfy4K1k73AKbhjalQyh+KsYroYF5COmgJRoTppAtK+toFD6rQJqCU0U+t1'
        b'tNqRuGWQl8rH6Q62kJsaa4HqZJUSj4yT/SqUpnkaae8ScAlcwKl4/LTRvOycAQ4ypoMroE0VDWUhrRfZBcgSqiF70UCrN3pQMkEOgZ4FsMYbqY945m1P9aYCkBbvx4L7'
        b'wLWZxL2KZoTecGRTOIEicU0051poIrD2pZ4qTT4E1CNNPpbue7grD3TQSm/4eLXOe3IivTWvBXYYa+i8YNMYovQG6xBn7LwZjrTGCy9OUmm8SybQrt7dWkAySuFdksXK'
        b'SdCiZ0MNlIyn9V2wAxxSKbwrQe1jrEHmUcWj1V00wIeG9V2wfypNbXUa7IMncT10tBbdBq7PBQdYJf6h9KvcMg404NQMfuloml/GTMBrmZ6LUH9j4xEchx1opDRU0OXw'
        b'vKE70mu6GIFgI8MbHtTShc3LSFUFcINhsqrrxU7YxGpkgu2R8DiJGoON8AS4qMoaCar9EsFJDwY1HdTZxLPRS7QFXCSVsK1BK6YcThyLZsH5CDYaszamDjxrQI/QYW14'
        b'jNZ0rOAeajW8lk2P/TUghddUfF+EX33VYi2K68yCtUbo/vgdNIENE+kf+KbC7cjUY1DwwhobKGUj7f0o6KaxtE3JcAv5FZIitaAKaWdohJiUxVh2NLgUQfoedAvN6YrS'
        b'fBLADvJiSZEFWKNNucJWrWzQCU+TfZccpBFvISTJ2wmjIpCD9ZQ+2MmEbWHhZK6PgfvBeuLvr4ZHI71R36cxbeHWWCKEmT5IBR2FVrbwYk0dDy+R86ZwA3rbzhqX06JQ'
        b'W5fShR1MNFoXVpM3sMxHjAbDR+DhA+X2aP4sZIIzIn+B859DRvZ/7UBo8V+WwXL03r3b+sK8vJdCCDTOkUDBP7ToKGvcfELlHFUfJYlSWju2ejV4SWLv2tjfZ7KsHJVO'
        b'7kd92ny6tLsNThsonCKlsU85lKWN0sGldV3DOnlpD/e6XY/dDbPBsPTesPS3XaXrBh2m3nSYesfJu9cntXdKxoBPhsIps9c28z6L4k9j3OdQVg6YtKrXPbN3xvzBGbl9'
        b'M3IH3HP7LfNGQpXV6AOu7U2uR0dGl9Xx+T3Cfp9oGjassA7r5YUpuRZ7Im5ZOcpcjvq2+Xa5DFqF9luF9gQq6eSBTatwGxUO/oMO4/scxiscIqXsW44usky54+EZ7bZS'
        b'zi0n17ZcuYt8+Un39qKuqQNuIQqn0EGnyD6nyJ4ChdMkKVs6tUEbRylwOhBGs95QwOKoVZuVPLjdod8yQFU2fHIMPtlu02/p89SYsh5334SytccxFFmwnHU4TGHjI4m7'
        b'x7VoGC8TK2y8+7ne5IkmK6wTenkJtyycR0ZsVFzXUXVRMpdBrvtNrvtzERuluX19UV3RnmIJ6x7PWhqn5NlKCwftJ/baT5THdiZ0JBxPGvSe0Oc9QeE9cdA+qdc+6Uae'
        b'kucgs1LyrKRB+BCMcd+DNl59Nl5Knp20tLWyobJpnZJnL2MdNWwzbDfGH9m43nz0SYlBYjij5CA/oI+Pnt9OKm5d07Bm0MGvz8HvubOOsuCjEW0Rg86hfc6hz511ksXh'
        b'TCCDLmF9LmFKS74aiDK2z2ms0tJdzuu07bAdFMT2CWLvm+o6mt/nUWZ2uBZtXAu+94rWioYKjRJHWejR6LZojRIn2eRBl+A+l2BcvzueKrhmi0FBVJ8gCtXqYH5fYG85'
        b'RsK+H0U5ug63TmKIJlh9RF3EINcH/b+X66P0D8bvwaB/Ur9/0jupvS6zJam3nN3l7E6DDoNBj4g+jwiFc2SvCV8ZPK475XTKYHBCf3BCb9Ls3jnzBpPm97ovQOdkY/pM'
        b'XG45usoWHi1pK1E4hkiMlIFh3X7n/G5E9U7LHIyd3uuaJTGSivpMnO7xhrovqM8ZDZazbJ6S54ZuqNuh2xs4UeERq8Q/UfI85ZMHvWP6vGMGvaf2ek+9MeOtua/NxedC'
        b'8eVKnossj2TCNFK4RWsU4w7xavMadArpdQrpMsPzYsx9M33zMRLmU0uKZ6cMCumOOB1xQ++joOR3ZvW6zZBMlFTUpd8yt95TIGHhWF+lpFJaNmjh22vhK+fgKJ8FJtEL'
        b'bwhvipDEKS1s+p2DuzIHnMP7LcIJQj/+bd6AIFVhn9ZrmYZkguV4JBJsncnOA+aAjdegTUCfTYDCJmj0xUoHZyn7joWHnDeA7iQeoAOaJBvMnjWqNDG7K/osPGTT0AEV'
        b'WNq0GjcYy9nyJT2BPSKF5USJltKEW69XpycNlgXKuZ1mHWZdY05ad5X25En0+k1i8VnDOkNpviymZVG/iTv+blxnLGP3m7jiz0Z1RuqZ7t/n4N9vEoBKB00c+0yQBMK/'
        b'N7esX1i3sL6krkSWpzD3wv1DB1wr6yplGYMWgpsWgvtMtpkTFhX6Dfqy2H5LD5z0l0e3qt8E79KX6P/weAYSlkGPKYaV421b/n0W+vsMDYf1OCTheq1Cf3xczkR99phi'
        b'oqpoWYdfWXnGoEPATYcApa3jA3R94H0WOv+MIE47bOZaUa9rx+rN9dL6eKzp3GjqjpX+XA/WHXcGPnrpz43QvRPtNc+P9VcvBj764qN66zsJqQ7FMEVv4QjpUPRS9PYf'
        b'Iv17+YqHa8mm/zdqqaMDtL/i+2GEx0kcoJ2Iin5dTz2dMY/BYExkPKWGj7+HHxAHgjs4YdRF/Rg2S8C6raPGzAxv6s9lU8P/GwrQ4j35ESbqAC0B+GirwrP6qvAskwRo'
        b'cXiWyuJm8UaEZtkZGoHWZVo2I+A+WVojgrDsaC0Smn2uVBP6IzzLoCi96ctUmy9GRmZJTFOoivENwYKG46HqkpGbTMWq8KPGJd6qKGSusJiEwnJw1JdPsmjjMNZwjPeP'
        b'hEtxAJnU6qm+nSefbCQlkTb1feg4Jn1LHDRGTSmmY4t0KJMfW5KXHxTGzxGKSCyPbrAof5kovzSf1PXb8CXywKrI8Gh6xBeFeFF15MbqAKU6vIojnqMjfv8pvvdCrn0a'
        b'+9s1tQIp1em+tE9h6mgAU4ZQA/pbK9CFnWA3aC8LRJeWg6PxmpGwBBxgglXpGSNCYs6gbTU8qouMquspxGHq4mDjleQN2pkUgT3BA/Fk30XSyvUZqlyhPTMZlOXMtLI4'
        b'VOwOd8/xAnKMn6mCuzJw2Cs1BRsJyTOwAyDFMwnI9bzBsUwV3GqEC5k13RAeMdMn3lt+eizEUzmVgjKn1JmwiWazSY95RpkwKcsb49flzzR0iaO9xMqGCZnkdHXSHOoO'
        b'RfnfWCRZ3JP5TJ8+HX9wQhkWHfBKtGEQeosDqeTgwGWry2JRWSyoGqcZUoRVOIS2BwfpkFGbOFXbUdVS4lSZmpDknaTibO6GuwyTkNndSHoXrJ8947dwZelg3whINq9E'
        b'wCDOe3PYAjZp5MZKAztV6bHgRnBtCR236QYyWO2FWnh6oQYJTgUyv3eWYRQj3KkFO54PG6pihjjwuh22qa7E4R7dynWwhu6cCYsnkK77W9gM6hzqd8ncraul7L+6iLB9'
        b'QIKcAi3iZwe7LMAp2v9O6YC6VfD8PNqjvlUXdtFWKQW2+KweF00GEOwBm3zprdL+a1fCfSvo0r1j4Hra/U6lVRTGxZL4Rw48E4CtcDQXajgUOyRtEgN0gsPOdEKD64vK'
        b'VbG8lQHD1PtwtwGJjBlrm9HOCeyaAFdBEwMcFEUXhvv7aZVGoDXLqOb6zowPSxT+vAstC1IVp5aGd34dnnGwMGXRVdPCPW+aVbMSPjr76ZP1l951UXb0HdKtTVj2yQfr'
        b'XjP9xeEXM1u/5bvD51QbV//ju8q7FR/erYj8Zfvrm51//KT253SDjJ/ul2X99O9x8V9aVt5PYnu8Bzqdkn5y95ZWVz+yPP0Wa46jz99snqx1esJ1ka7cv/vI56nyfxg/'
        b'UuxeB/Ue35i4K7jxwX3BWLN/50XVR5tllBzPmnv82wkdxhv2/nPGD9Z391R8cds/L8HJ/pbeku48xhcPTwLhskf7zH9ubTcLafnx+JKvmn6Oja/cUzfjXfmH2hdml22y'
        b'qtu8q4j9g2FckXPUcevvpukEpof39rU0fHXlTd3d07/z3XxzVv8/564c6BaWt+0J651u4Bs3x8Do8aHLe17bkHD6U4MDFwu/mbQv6Hzp/COdCdPrZUc2HZ294pj4/VXz'
        b'724tuPbYsHSuf3rR59+3tth90+1Zcrmws3zF3vSl9v/I8ox/Z2mm7fn3l351w/uHXy/uf+2Di/Y6z96e+9axFQyxcOVUjyXrfpLYWfrUHqv63GdA+o/JDVat5/tnfH7i'
        b'hwWflgTZhabc/SxgYfley2PWNT99nvDemHM/TftYwXVZnTj2+MycqO5ZH62evkf3Hye8Lnt1f9s7Hf48y8VZOWg0aM9snPTu3bI1iq+3Gz96PWt+3dxV/9Y3yhZ9Uv9M'
        b'ryInN3/mkynOaXMuxdhUBdm0XaqYeT1S+tGKnV/WL+0zfH2VvpPcZNXT1vZH71S4fNfv0+B8JO3R91uv/Fj+mb+4Bn73K3XmQtknYbUCc+LGCgKbJwzt17YH9QxwytCf'
        b'3lR9FpyB7didt9VVFZYn3jy4HbQQL4g7ODNFc6/4ChuV1xbuV7NEnfNx8HICO4ZZpJhO4BK4RjtcayqXqImnQD1sY4BWeNCCzkpwai1bvePai4U9sdfmEA+NPbgMD2rs'
        b'UEBCYuuIBNpw81ra+XUNXhiPhFMCjtGxE4A8k2xUAhJyNhicmZFMIAzJPp6Yfr6JBfeFMaM5dMOa4akyr6F8r+bo0iuz9YhnxhzWgx6vJHhsjI/qPMnPCs/CK6TiBeA6'
        b'bPKC253gRj/yaLp2TCAB9RV0d2yEh/S8wIZIdWKuRqYPkIE9pLtZATGaLs7o5d4qFyfsNKLJvhrBEUIG5gfkKbDGxJUASY1DWHM94UWC8wwVgnPEf4UWpdOgLhWJc7Q6'
        b'eXEoG9DEBi1RnnSGr3aSBaYG1oEteAVL16I4tkw2rAatNBS1BlyFVzU8brAOyhJVPjcPWEMTFrbGAzn9G9uQIbcb7XMLA8dp6vyrYHuiyuVGu9u8nWmH2zS4jXa4HQUN'
        b'wTmmo3xuww431EQJ8dParUZzscZPCPdhr5fK5ZU+UeDw/96L9XJlH/fTK7m2DDRBZ7dtRm9u0zhJnFvvM1XOrRykm1gPoV4XDVr43bTwIz6U2BuLBlzTFNbpvbz0uxZ2'
        b'SjvH1tkNs5vm1sXfMnOQceSsQTPvm2bet+w85SEKu0BJPCZGK0BVcP1ucv2Uds4YBts0TxKv5FpJ41qTGpKaUvq5HqTuCQrrmF5eDAbTesjiBs0E/WYC+TQVmFYW0BQu'
        b't+iz8ZfEYkyt5xcW1ndt+CSXwFSF/bRey2lKa4dWzwZP2UyFta8kFhnINvbYLSfLVVh7SmKVLu5HE9oS6lIlk+7ZOaH7W9hKxXvXYNdWlrysq+xk5YBrpMIxSspR8l2k'
        b'WkpHV/TJwk7G3lt5i+8smySf3pV1cv6AS4SCH6k+jQ+4E+wdWxc3LJa7yu0V9uOkrC9sHG55BHYFHTduMJSypQvv2jgpnVyPerZ5yjPa/aSx96ztNBp218KGPH2ywjql'
        b'l5eiYZ0/59d6FSSyvZc8rieu3z6mTh97wiykOvVRe6Oe9385ug86BvQ5BigcgyRsycw6o7tccyXPuj69Ll2WIM/r5wXd4mELnedz356ytJXoP7ChbBya3FBP8izIr2Jk'
        b'y+WO/TxvJTobo7S0ksa36MmmD1h6om8WltKgvSuUtnwpQ2lr15Io5wzY+qLP6FKcwThXNlXuKF/eM1GS2M+LxqWpdaky136eh7ryOJy+F31Oq0uTBcv1BpyDuuIHnMf3'
        b'8yJQ6SDPtY/nKkON9MK/SapLkor7eS7EDfB0OQPNDjR5es0EzwhJPhhrlsrWep+tn2qmO8I4Z2hTGvRzf6I1/jLj/Pk3lTbO7XBD7NEhBLW3NBoV/YSM80IhMs49sVVO'
        b'H34PhPokiyQQJQ9XiU3/tZxRtjjuGWKLr0EfInQ1bHEWssWZqgRstD1OYYs8yGDI+ub8udb36k+GTO/hFGxD+2rI9pvfuR2M/o2aNZD+3QvozX35sTTAltxKBQQmu8Ww'
        b'PY5OJWakjwvxD8D28VKhGMNNS8WiwuKFQ7eg6QiHwbOjaZrp86+wSVWH4BhBA5Aio2O9+X/cbKO2iJYExqcRa2A6Kj5PQ/+iI4bYOD24NPLvqC7co8H2GQf3YuQfaIgj'
        b'ScVSkcG7XY0rTAd1GqnXckBN4WtBxlqlmNv/NvPk2U8w9+n0PJ3PdT43Gt7Ryn2lHa1NZEdr9n5+vN9WXrnkF/4R/zf5BWNlPZ1T/fXf+3zev3hLJXP9x/cae792xf8p'
        b'yA977cxc/ixpx7+9X/Nm/GvmT3ql0f37s49khnQVS656Z5t+TqXdeaYj/YteyIbJdY7Npp8nrZK17rUaF0TV37Rc9fEuAR0XBSdgE7g+zB0Ej+ghm2w7vECCqovN8kds'
        b'iD2G084zK0FbEJ12CGydow+k4KomdxGtjc4C54g6Eg726o4IIoOeApWKZTuTzutUhVSWZhKhnmGNY9Q4QH0QXPqT0/w8rwAYlZEXa0gFsBulAow8TZQAZM6SrTCz8//Y'
        b'VhgLF1mmwsITLz420jJkkyjdvSRxUuubPJe7Zna3LBxlHvLYQQv/mxb+t5z9uywVzuFSHaW736B7WJ97mMJ9PP5xH5LmXKubXFelK77Ysi5N6eyFne/tUYPO4/ucxyuc'
        b'I9GyNbvPhE/SqH5kItDY2missZ9lSPr9Qfleavy88FZxfmKp7Y4OhzWl9uT8Ial9//dK7R9x4xm3tVcXLsOOwBfv030hM8b/YqculsyFejGi3EWF5So+QlXuhRFMh0gm'
        b'x9Leu6JVxL1XuHRZUT52QObnOQ7Ja9UjjSbiQ8UvSpv5wizaZd7oi9uaNBpEMtpdYyUaBnnnWOgUgn1mhc+m7meWxqCrooSbaNIOzLuy9STjPWnOayluO0z2h2e6TJIS'
        b'IjezI0468vhthm2sI1GbArba+b5Jcf9RxKA2+3MWxHYI2DSqYzs4CeqGJAmQFiCrluNOrB/QOR2cV2NU+LBObdQ2gEbaaKkF12ZoWrWgKUklSDJmPMbPlrIw54UIKIJ/'
        b'coYtQxAoeKngP2QHNxHSw6Z+s0uHWNyHAtujfkDe/WD63b8/E8kvnvlQENWdpjWm2bBuuA+963fMBQpzr14Tr+cJRjy0X/zGPUcw4od/6I8ObxhoEIxMLkBvkc3v5i5m'
        b'iz5h4P1iC3ILFi7A80rUhN/8eSxV60TvM7BnLi0tMz5NhPl6BNxXoSgeZqwibB1kQz7ZFE22vZHQClHhiEQgDzTMPGzz5zAP//dLBJ6jI6mLX6CJbuKoDpjwtHT+MI+x'
        b'rqHJQ3PMY+zctqLf0O8J085wAgPzF/vfJx8fRKnpixMxfXEyg/AXq4iIMVuwRVjV5Cc6RobBD+xHcQP/3ZDX4NxvaP+UaWjogKt0uI8/PbQnt0MnHjN1aK5kdAJ9esij'
        b'21Hab+j1lGlpaPuAQgd83vs+/vowGJ+f0RF00fmWg3MH73TsYxbDKOwpexLT0PYphY8PyfGRFiq+T4ofprHxRbkdrNMZF3kXF/UGT+43THjKTGfgS/Dxe3LEd0lk3Cfl'
        b'D+eySEM6uB2Zpz16Pca/FtdvmPiUaW7o+YRCB/zbJPRb9PFhFP5lRr+h4/dMPUNvfMbpCf5EsyHz0WEdbDElZMgEqnYefbDQTU5J92FSHu5a5RNd6A0NDnA7fxyBnash'
        b'5/vAeRrQXW8ETiUnGiVpUQw/JKgCYGPZYzRHkZqxHdSDFrA7sgQ2+ZuArUi/uWwWGgLW58JOTjhSTerAbh1QDVvgRgdDIIFbgAycAHvi4sBBfbAbbGfYwGugG14zBA3h'
        b'8BwSY2eE4DzsyDRkwlNgE+yMjADXQFcCuDYZ/WoX3L4KdIMOcMJ3DWhPAaci1sCr8Kg27ALH0H+XxoLDoB0eWbg80BU2BMD1sK0YHICbYQc8A5vWRIIacARWg9MWk5dH'
        b'pJuDGme4PrZycRDcCa+C7sIIuHXJZGsHoXV8eLLWrMAK33TQPsvWB+yB5yNw5l5wFkiKwTFYh6q5kAAuhC31hLsCF8AdhvBIHuziIgVYBnbDgxDn4d2fHQsbpwQtBjtz'
        b'4UkOOAAuwK0l4DSsgwcy4EnQtWIpPASuVYLLsD4T1FnBg0vmwP3gUKgZPJUALvuDHejZ60CtaRzozACb3JNRAy7AxnGgsxIen4ozIh8BjXAjUrSb0d9di4AcNoKDK+xZ'
        b'+mAvOAdbA71hO7ywaJxeBDwPtuXagvWTl4LNeaja+lRwRZAbX+IQD2sL4TXYlAT3zbIEJ1fGwB5wBg1TVyQHSKcKpoM94fawBuwDW/TcMuFZS9gGD6Jv3algG2ieibpj'
        b'H6j3ht3jolwjXXhceCYLFTRXuM/xgg3wmAkXboMScD6z9P+U9yVQVWZXuvdyL/M8g4ICojIICCiKIIoDKKOiCCiKDJdJ5kFxQEFknkGZZQZlUuZJkGTvdHeqUkmsVNlV'
        b'RVV1VaauTN1NlVZMp/O63vdfrE5eOulOr/XWylvrWbUO/73/dM4+3/72t//7n3Pwbb2WmhWv4IxhnqDHqNA48OQq8+DWSGp3oSU97tKKCaSahBwvLgjh5k1UGeWmwis0'
        b'b6ZP8ym0spFKEnD6aAaXc4uzGffGWZ05u9+JG4GEeRrMjgbomrjttIZp5LU0j+s8bXbenNqCqNf0HHKPDmrmhyroxmkgqo17D3KVCpUe5cWd6MgmGnFHK0dRvzkqCkcf'
        b'1DocACAq8mjSeCOypafozG6tmxJekr8oW8m960O7xrfwlD9XH+E6YTCFMEBpjKZzqwWfWOARxOX7Id5UA5/QoCWeMrxxEJ3/4CgVbIJSb3HQ2MWP0H0T1Ck5SoOx0Vts'
        b'qS5RSpUWt5xoYG/utURtvgek9vJDmL0q42IYLRuGU9tBaqMJ6qeiaO6w42b7bTzPizQnoXFVvruRZ6MVM/g+TYdGXDnA7fmnUmiE22GlZRs0EfDhsTR/D1yi04zaufBE'
        b'uDDyJpyaoTSoNAZ+WajgHsgNNO6AYyb5IQ3nn8vX1wm/FbPLN4E7dK/u0uUx2KESOC+Cy9zeDZ8r990cYH11G5BYS6086gwPGAFy57ksmhtSaAltOspPqFyZB7y44Tp1'
        b'5fp7J/HYdi61Qca5cmOP4y0quaB6iuZNNgnT8fID3b3SdF65yJMKXJdnFH2U79CUGlXdPIbstdDMl2oiqICL47Spix4Gnwp1idXbZspD3r5qBnqOOxU3uoaiJ+4HcNkp'
        b'9H0LD5tQGQinIJoH3dDJT+g2F0u4IQh56IQFdwRxRTgP05RUF7isMAaf1ZLAWcVRLoJlqYxHafpKnilVb8L9xgC3h6l0Pw9gKb2mqwJ3mYpH1y/ccDGgRpjxDrpnHLQ2'
        b'o5Kg5cddpvSIu8+e4RF4ZTHPbT5Py4H+tIKE2ZoaskEYg1TiLuOpVC4Pp2XHDcKvA5HBNLcRgBzh6hBq8PfTjbzCM7jfILDQeY4K4V4rwjK4Ljyiv/2UtWEwFcLmMxE8'
        b'kALrPQymSVueV6SWGGvqsXVeH6dTCHZ45G9PSxYKIvFBEbceu5j7A0A1khbjANT9VCsAFa1ZsAeI3bkjUmp5Fffr5jtp0dSdqQ5vbt59YgcN6lz0pyEvquJZGHKJmzcC'
        b'Yk8RAxpokh4fRzYrjBK14uVjXl77ucWP+uJ01LgYUB4A2ObozhZqs7gMbDcreNHSVZGb43FuvJRjjx6dokHI2wpahMM1wFPbY86dTwPl9O7g9mT0xBP4GNLqNvRWHzXx'
        b'3cijINMVe+OwnPMXqDsQNeznOp62gdPUH7ByyeMqA1Va+EMow3GaTpiiHjNXuMhB9RZNp8l59q7WVWqF1w56B7hds4yl8aDrN4wkF3yp0pgK49GwFVxgEHRW5OYFYLco'
        b'p1I1PYiiRk10/ZCFJjXuhUWpOweHFLLQki7uRCR7QAXaCly0H8QzYKhMc3t50WQbQDJJiy781OAK96UZXpUmpnAB3YMjl/BdbRiqH80b5CWaOoFe7tXligjzRMCwiCcO'
        b'Uj9MvhS5HfHsUUSeGWDdk7qf6y4i6jXb0tAVeEqVI7qi19sFzFgOwCLaRu66tJvrbZL5Yf4hrWuoYBEVAOS9NOVsYRMXTVPgoTkNA27kRS7S4DIf6nQ5vV8YYXAVFSjn'
        b'WhuaoR4aodpr3Ku80RpGfsL9PhFO9JQ71Hzs0OAS0Go3Qn37EZryTQhBR07R7ewIdGcrgmgXPbnGlZep5byyjJv2x/s6ymVArX8OYlRJrvBjCY5p8vQ1Dudmar9EFQqX'
        b'TagDqIcFgXrqPJuMWq5wl2Rrup8Pl6dpcr0sTNn8Ao9tgPgAspzg6L0+utySKMe7gy8/9Hfg/nAlkfgA0M6FVJL7jkDNBbRiITBzmlysLPFje54VH910kbqVuTVETbw+'
        b'DLoGp7RQXQ5NisDO1oZc4AzDt5hd50fKtEj9Ml8bajtMI/qILG2mwhBqrV0XuEM51SwZcGrThve2uNjy01DHY9R+8jrfNaMqv017EFbm1GC1p1ypfIKGLgpeFC3OiBT0'
        b'2P00fsxPzoeBYgTGHgVxQM+ku1G7/kH7ED1+HEH1F4/Q7aO0qMPdvrfOwWTde67rU9WpgAga2srTt8wPXwTRDKOnRlJhrxFqP3dVzE0+rrRweud1rcOwQju1eMUizt9G'
        b'9/ea6KIfSrhfQiu63BBqrLMBYbTCgOrOB0Sfhksvu57clwLnbgynRkcqCjBwMuCHKTR6EE5Zlkx3t/Htw2IuUDwBEjlE93ySaMoriJ5Q2SH3w0dvbuBWeAWYdAD3KxWl'
        b'Imb08oQSdcM9yo3gRpMwVS13CGtmV5nCezu20pN8ns30AppbEBlruMkzk3u9wTQFcSfzqMQ3HZ7RnU9N+YbA20zcVR5KMOEWcGYP6KPCg6vDdN0YjlDH/b6QWYD6gMUe'
        b'IRJjq+/gnjxfHUTRIxto6hTwOUfTV3eBC5Z5+LCw3Dv4uZK69mwS5F0WVcVbbBcwyvUGB+Qc0YtqFlBnEjXF6F67HMgdwsrp8LdmakhCbYYgL4oUqCYXhq8yvY7mtSPg'
        b'jiDOZodTjyN3cr9JsOYphJYHyUbcI+N7x9G/g/wkku5fRBUfedEjeHeZO91hwf2XuSkUlyi9kHhZCFpcmGrKUxmgnUkutvY5q8bjG519Tppzsd/6tJfFN/SF538IM+1i'
        b'kdhPhLA/FZFbpyD8LKoTBsRj39di5I4DT9nzvDiVa6BH9u+1p7mdNH5Zfbu7cha0covPGW44hHZStzd6fxnVmsqCBWcF3gq3ohJXLnKOpvuoVwWNZ1zfr7HJn5b5cQx3'
        b'4ZhHoJzmW5upwP4MoDAv3QvybKIFO7cDPHIeWvAeL8igZGtQ02GE+xkGFRbdcuC7egB02aHz1O3HTSEHEafrZAepNdQOLemnJ/twtxpIm25a0gYj3KceHR46RjXOedyg'
        b'Fbg5IRX8WKgM1+m8rhZF41v3HQkw2a8J9I3SPS0HcykMel9Nz52nN29TkfjwbUvYuGArPGJAdyPkQg2uORbJRefprjeBzbwQUUFokBu8GCWMxPfIBMndowcIP/3IKMbR'
        b'heITDmeocmsaIn47jQZz0VnujdwnTOsfCLMVUfnh5I3BvicFQVRx/iYNxtjy7Vgq0L9uwc0IcPXneDYLsGo6ySMXucxhJzUrAINdAVzqDeStIBKMJZxH7lMHti83NYGJ'
        b'py9yoweXUlf6Xpj+oQuVeAFQ/VzvHGEQ7+YeHEP9F3k+PRJU3u2hrbbVdY+Bqast4sC0BpfrHwnajvC5spU6QnHVBk2g7mkqVYScgfssRlL3Nho0iOOJNNywHc28fwFO'
        b'MnBOZgheaqAxR3qsDmNWcHMClW+myfMZF4wP0HAKDhqj1ngwR6skGbUqOAVfmHal2v20vB0BeoHv3DLgp6IU4f2CJurIkM/qAJ1Uhf6s3LGLisXyl9g6Xfxy3wdclW/B'
        b'MwHXwjQ5WpcB1TwekfHDqyoQVkX614X187aZQ0RPm+3U40YdqNWwkGvHqO7W5q3Xc6kk2uRElEYItECf8B8V7UYYaQL14LT9gjC7oaNJo3no8UXuOnNAHXF3lla0L/IA'
        b'tyYjbj9Q5IJcvndaRsvX07CrPeY8ZNEjuQ4h6JAntJwEn5iKMeHirM08YAO49MKpRk6ncf0NCxBKh6CoE1GBsgv7Uk3UcUY9mtQEM1UGRkBNDuefyg9LzLPSCGKI4j4e'
        b'sALXP4j0ytOC1StJ8PY6mk/L8NKjWe0c2KwwC9qkLjzIVdWax2OC+DY1ncIhs3RHmYc1ZVx20l54seQ2lWZQmzbypDvUmceTUUDwuJOGvR8YrTVJxyf5qhcyt15zeO5j'
        b'8FPlRhspbHlvJyRtnbEB3U2z2HwULjxqzgu+oLpqJEfTiO2LacKITW7I3MqDW5BcD/OdfGqzcQBjzivjZkU86Oorc82zjIyH8xfCSYpy4R9tatTgzDWXXLk9YCtcZEpf'
        b'NzsGjLnEw2d5+Dy8qd8SyOzYA/Ez50qlPJ+RRn05PA2p037DeKcwu0fzAYSFKY8tqHZdIlVDfSjyw1AE1zIAuNHrEs+EmnKxlO7yYxnuex8gbBNtubI/42y20Qn074SV'
        b'HbzoPtXH5VCHVx5VbOFyxUiuTKZWTxw7SdMQr81cfgZxpRISp8MgQIu6/LbdCgZwR/nRtYgUSM7mU15H9wiJ4Yg7DXhn2UXSHCBVG0gT15MM4sFLrdrA/bQD95284cuN'
        b'PnZAxCNjK3DLEs86BSSHCm/cJMt1yQn4VuX6TDDpmciCaU41I9dXApIuzUlERRu5GsBsO6iBdj++qbb5nCo1eYRoR+sjltQ7ojt6UdN7gvTexneO+wRSSbKXkS04YI4H'
        b'TK8hoPRQ53Ed73Og1TrqiOFaeBk8SJg6YRTpyWOuz3PMPUzDRoJiy6cBWTSXqlNPVjRg20grXlQQdpLvBcGW2A9nKD6KzX56ICybVxqqBznW7gST3Xc5a42eL0T44Qm7'
        b'CFy3VhSMexbLwHWPETQbYWskMUk3qMQRAbH+NNVtg+afRI+cheKo3wbuGaMGd2RCxTlRgfTUH3DrB3tXomMnzZAVFSH5KnO3vUGlrhBci/DScdB0N41bQtg+pNa9sr2X'
        b'JVyrLNPmlmOXaMiN57PsN/PCBR45e9yQhpRv5MoCs6JAbfXUryo8NqAWM1MuhGFHQAaFwmy9kWdxrSrYsynCIBlOs4Aq1O1GUwf3b1AL0+DO2Ivy1KpNwkUuSEgKYJUx'
        b'BsGtuFCVhMcj7IJduDgcpNLjwePbANwHrvYkjGwdojoPKJhatKcgyzhXiohRl4029NPykXOQf41UYUedyjyaxHXH6N4B7g5FblSFJGRZeHPyomWs7eGNPKpC9y7SvSwA'
        b'ddlWK5eHYrOyeBD/NeRrorrlbmfCkSSOgQrrXXnysO8N3fg4mrHRpFkt7joGYN/ew2NOx+FbQ1TCwqOdcm2k6NNUaMzVG6gjCq5ITQeOnQ06lxV21hgqpgwRdsF4L9/N'
        b'cnKFr05elsBFB2jUwYhWchN5ZA+UfZ2dPrcZC0yKSFS68xYcZWY3JF658DzKNigekY7mnKg9B5gqpblzVJqG4NpPw0fgQmP+t2gsCtlbJ3p1zG+f/AHMkgQ033UuAZnR'
        b'ANXuMd540x5icTpISAq4Pl54dW4nihVetjCiJln2jhwTqKQRL56/oMmFmrwkps4LEMQNu3KFiS62K2n+8bMX0NgjL4uD2pd51EhpwxXuiYNrFMaAGCdOnOMKPwMjb+Qg'
        b'K9ScBWOWqBsono0KCIHr17luAHCa6LEpDzqb+Ft60tR16PfScJNgh1hvZcSU+ZNn5A9hJoM34yZt1OgGeyypof6TaWCFXlD6ciLP5tKsLT2mSk97OMYgd6ThQ+3lXdSG'
        b'mAJ6qBOA2kcTdvRoZzrEeec+noxDg6gk8IyxoA6F+TEGwsRQYUtw6UIzeM+EL0JMp9RMWMPmPny8T/8MPbQCrdWYw7btB7MCII07EyAYiw4KBDdBhfkp0OQbDyKI95lq'
        b'C4+2AvjBNb3DajSceh5cWLWe0WfHwgXqLm1FzRBSuOcmqGDBDJ5wHwkrPQi8IErm0kMp4JyOC4cSwM1T3CFDJRtyEAiLcAaENN+PjaPHKSf28LSxDj3dchZQaDHgAW9H'
        b'wSh2PGQs44UkoEaQ5sOQ+0tZvHxB0VOHWzc6c0NwBjitSp979ZAyNV6HxEHelgkZMn2AhnSDbQ64WiP8dfO9CBXu8U2H3dtttudusk0yOuGrp8vd+rdy92lSySGFIIB+'
        b'GPArp8GbYIKe3DPHqPIcePa2Pc0byOCXS3CM2fywVESrNKqR8AQ+j0J/LURfBtt27L8RzgMRDqClNh6xpSeHLtDY5q3HwQqNQh+jH56C2FrBDmO6aMYyr9w8EYCL9u+m'
        b'hlRD32Dce3Ej7PHkMM17g4JLoxStDuRYROf+PZAaDqNW0v1TXPkf6WgYbl5Nzbs2CxlpRIi6mGb0uCyIHis50Ng5JSMaYlDg9G7DWCDhsfsZXqYKxyR3YLRe/vhj2MoB'
        b'PCY8iWvV3UHFoDWAtITGodn56ZVgB1v01wgveXnTkBm1apttgPWraDoOztp3wFNEQ6ZgluGt1OrOBZZgu0kaDeeuUGp3iQDxlB6njrgIxITHZwSJ0Ms9EVnbFSWJntzk'
        b'xAN5XO5Ik1tOc1HaTupPPoS40I8mP0DQ6/AB39BCAFfsiEDkaLeDN99xsAxL5IE9hmez+GkQ0NaE2FG8y0CFupLTaBz81Yk7jAcpww9WMoKRatcDMFXUfw2NRrTawINO'
        b'dC8X8aQ5KBlwQj7RvEMzjYrVLPbxmHsSt/gZpdISDeVyuzstemdxM6xXy+NnNtHKadFevqOpwisS1LIk0JAWFIXHHH3uNJhgdIyajm7c4I5cqAJN4jEP8PgSMPEY/TUH'
        b'ICxnImEc1YfRW2NiBceJT7QBrVYrRHonZGrQzDkeTA4OSoq/AKE4qYUqtCHejqjxpD9VxlLzGXtjgvS/zdXJGtE8eppq9Q9ePH+dO/0CzZ25fidPmCdGco2rgiAcwULF'
        b'SHy7eCkg7wZaXxmjg9jVw083SbdSk34Il8SG+144FOgDB6/az/ey98bxghUY6ZGwLhUSNqUo0MOoeoSZnGIE0r4LQ7bE7qIJnrGyZeGdoL6r8LcaGrdBXlKpq4zwOJwR'
        b'boibVsbx8olM9E01Qx3UqdKsnocjOK3zqv4t7e1wrlYQztMdXBZFnXtSoVKQOeQelcjn6+qBU/whtpFzzkoUjPkh1x/UzqJ+A6Xk7WDd+2jOBDixyVnsd/q4kNfE8nws'
        b'T2nCs2bQ+p4dHlpcZ3bWXAqItyF+V0FDj16Dve/tOq0aSo/cuC0c6G4DdS+qC1k0jZiFwuBIeKnGiItP+QjSRx8XG4vaTAMuPHbUjqFn/Mxho0or6nLcDAe950nthjBO'
        b'ezaCzgMZTYSbAedtCiG7NlKfqTsVxFC5E+TnftDh5lDbjSCKhkQuUqUJWdYtxK0imo5wQ1SZkgk0Xqmcc8KVhjT2wMi13GoSBTMt6HFvgiE/UrG55u2ZaUz399DjgBuA'
        b'1QACXz+3mvJsjh8P6UHp1CKGPklENLimdjgLvdiJizRY7c2hfg+pM48dsKaHXmrckcOjOvHnTWhQVyeTGg25yj8BFyqkuzuUXQLRoxAaMMu81CIw4+CekGR+ZAVmGIIT'
        b'dVy04hUfkFcz3T/uvV9Yh6wCbgkFDOpqoFn1eC7djeAMjFYepvENqmJQwVxUJGhvAF0yj6sW6xqGIc5UU58K3UmkEncecgD/l928TA17I1l4Dt4roqkLHhtBKItUkrQd'
        b'jvbAhHoc4OWt8IlxJLsdF1VNd/MTY2o+vdc/wxcR9CE95DEpTrlNUxYG7hD9fTToTcOKZsIrTrSy1dAUUrbajutucJ1gmvIrNCnJ2LaPyz2wo96TereH8QKiJTfpWnta'
        b'c+deapGFAzpl3JSF0LScd44f7/IMpaKUHFDjXUeRGw1G5xnExMDwKYn8hKpjaDwT+rkeCq4aBpvYB2YttnZHXrbApVn7/OP3gwnKuOK6A+w7qSEG+IY1BG2MvmyNy87L'
        b'p/lgfOyjtgDkzl30OOMYPwqTB8ZpfuJ5zouabRA0kX/67udpPyi4x+pxzpByLRFwjhXlGOi1AiuetchVkKcG3oh+cKRC4FnwpGV+Yg8ubgE8Z9152gRiN5wb1ZIO04g1'
        b'tx92onoJAly3pnDEfp0kpGxL1xOOHYMaKPILdbfgkmvpENjL/MAbAJikLlVeclNOQdwZEXPPKV7cmk8FSL7ubfPRVj/FTXHy39bGhEf2t67TXVoUnkL10UIImgg/GRQe'
        b'4kDpDtDgMSNuvRqy/awTGnePhz258BZy/Bkz8EBZJHWFQm7NOCglpruY0PgxNTj+KA6sdoFdS1LgBMva3H2eiiEIxhFbapy5bqMy2jig6sCPbiRCAJbE5NGd/YjKNdQt'
        b'4UkTVW4/Y+JjAsSM2ijqmPP8gVCq0zqoAtpc5AJfqJkRgdR28yMR4vc9rt2pJTtBxef8bfbmJKvxsk7Yte1geMhyr9QTVJvBjS6nkNUKKnTKPfEG0FG+ncZ19/nDiXuM'
        b'aVGNZsOvptjxw62grTlup+ILvJinxiVHT1FDEJy0GJnJQ/BOPbIWS9i7eRPf11CTxBtz5dnkpPNRrtzmryU+aoRTx6heiRp0jeFzjTSXrHHc3olnNwlPLBG6C2hpA80J'
        b'v9E9MDNH1lcVc2A/FHznLpijhx6ZO6RRfcAWeEYNkp/sXGrdhW4oOc4znuoQ8E+gDDqOXjPmXo2bimhEgw+16avegNM14FM9rdinXbxKnZZg6yK9vcE0Y0IdOnv2a1zh'
        b'235cbBaFpP40NSRSJ40ARzUhEcJTTn6QKzyKQtc/Af2OI04Ucb8jl92MskSghgo6g2PvB6Ext8N49pojpBkNwF8aEavL1CNics/CI7tIiCdQpP1uaNtKPt3dxA0y6O6Z'
        b'TABm7IoJcDWSz6W3qBxUDu1xO5yaLXfkfio8ue9CKj/7H35wUHg0VBuGOAwSSz5gEaJtzXXwgTDr69jdYZoQq2rC/aZ7rbkiDjVb4UcJNKp87CLuMwuZNKDgxrMbaYUf'
        b'7ElWR6OKuTuHhF+BC896UoOUmkxA6EtXuNWfeiXYHKRFGSLOw5vgx1p41F10R73aJu7zA5+OwPpV3HCDV+iJpwGXu9ETB+61DuTKFOFnq+PC46K4E6hF8TbQSrmGlIdl'
        b'GwD+6asW8PQF5+B0oK5f3wV1a9hpxE1bNtty+7ajUA1wkMPAw7JBIs9ocJuHJQ9oInksjqSiw7xwkEZU88AwjfL528e4TwTcLyrRfbNj1KyOPGFgpzb1eDtTqysEQ7HJ'
        b'aUN+uGWXkhKXnTzM5ep8+/AJJMZPHKGySt15QjuDZ5w0/F2o15UbvfcdhFGmqE0K1+8H45dcu2ihIwwiXRDmEKVCC6B9TAxtduuyMwDXGELF6nJcLESBxFcubQMndHBp'
        b'Oqw2KHDBzE7oj8b4ROrbC0QLT84bucKYp9yQ3NQnUJkS9SZa0EMpPfbax7NCis4FJ0Fh0wFXENOfuipBW/dRlQ0X7YBhHhtRbz416wKYZVbCb8aKN5TcEk7jync9tbgJ'
        b'8kHpiiCDivR3pyHng6a/DZqop0F9bj1inCe8W3EKlmujxQuXt9KwAy35UJ+tIrVaQmK1h9PQJSQ9Y9TnEAXcIXS77UvfRYt+2zO5dyu1+NGg/c6jPKWIoNJ83BJ57X2e'
        b'dEaUGxKcpPWU3hFXiOwRR14JtQa7NYdc1IrKP70hAsAp44LdAbhHy5b9mw/miyAxyy7x0HVqWX+9TewjXwJQPvjzxxkKwpuKKmMaFzXCgrxFthL51692yb8+tl18MUVJ'
        b'S10k/3JHkET40iJRfFGjKGKTKMhWIQiXWh8qqiD/iUA38rwW1/7hyz1wpz7501ju5Ic3Xz+WQl9Oi2gu0cZWsj7x6lOPVP8dB6hMLBLvFeaPneDW9TeCVqJV/LnmOk+J'
        b'ROKdIq7yvLX+YsQkuHFUGDmqxl1SkfgwTjJyRSXkK7j6UIN/MN33x61cRPIfe++vV6EZbnuPKwP0AhRFYncRBM/iLZwk3zchsDJX2tKdFOwMFnGveMf6nmVHgKwyEJww'
        b'tP5TX33mTVvx+r4mLk7194MM7cFJ9iKYvkGWZBejK8nWRVg9fG/r/XsRwR8e1Pm79zJ/9NGrfP1DZNhQcHj+X9pP+P3dO3vuTIdsrbjzEz/PlzOfPPzFnl/lRXgU3un9'
        b'UanNi67WT8yelM9dj/xp2j//cMOrrM2vXoi0v9DRfqFS+4VJ7Qtp8BcGwS80vv+F2fdfKDh9oef04k2nWY9zcX/rU2363U76VvZnZ7964/3/JYnd+vOF2DGF7E3bgwwz'
        b'o45+9Nnn8x6ykCZDVeXZrSr7KzNG3q9Pfy4Z+Knp8KfJE7r+qbaHK1Wcks+FPi0+Yvj8jYwPP/oXv8zRwQ+k3z2tabjUF/pW2URW38TEZ28EXrt4+1H9ptbuf8vQ8r5S'
        b'6PSdTfnxilrOh940Pq+4MuBpF7+h5tgH3zD/we2Qyr7kpP47Ry78oFxF3ePoZb/fbKGgbzjbmv7uiN9pl4qMQ2eNK/sXLbc9TyltVfyBR/g3Qr/Is3BUad014vyy7sHR'
        b'qjsD3j+Y/+c3HNo2/fiIT7j+d2PVf9xi7Wf8zvvslTtXXppX/t41sxArj4+z3zg1c+UXbkFV573fHq9wfb+u3/EX737HNVb91VrH3rBrCi63G/O/m5l3tr31ZOnPB/9h'
        b'V1VMV/yb5W/9rr3VslVfL1R5uuv2t21qvjRr+pWdku2+AHPfo99XXf3qxcuItlvvL78vPvOzt9RP6L01+d1dRVmlac5fGfz2p78zT5Bcup21w6T7QbeVSuiWxK6id5q/'
        b'MrRfc2rqvGPrPRxoodjR+PyZv6tbh2lzxr/+TZxvns+0+HOXnQ55X07kX81cXTzs8i93L/+yyDST/TIqcr9w+NTqUWP6uVeHDv/Dmyb/y/Efd/qsNA6e/uIHnYYLsr1b'
        b'nlQr5+z5LO7I9z4oSIj7teytUz+V/NLs5c63Kh2N/3bxpfvC7l/M/fNHP/9M/7u6sS8DXik+viNbskgWGynOfNn226Jv6k33SM6Hlxg+61EeeVa6O7y0ukap/ScfWn3i'
        b'9q+Xvz3n/3T/F/90Zbrml29of+Z8+bftNmqRz+aU8rM/3varr3RvfO6k/E8nfzlmk7P759k7v9PSFWoS+dT/n24W7MtrXvxC/IvnT979969OKbt53rLefyLh1OibVe0b'
        b'nuT+g+unE5/o8dzfNJ2N16746t+dNoRpXB25Yqu2PkueQPeNcMRLVLXu8jXU4rs+FRlyaZ75P94xnqDG1y8Zx0leymfpXeJK0z+5FBcVB0sh/Qtk6ysaLR7g2+pZmqqx'
        b'appgjErtrFwNROY5icjsmlTF22x9RGepMF05DpIfcoVnr2RqKolMDirkSxA16iJeCism0hCVbsm+rJGZy3PaVEFV2iqaajyufVlRZKuFQFMr5dGjNCafBxKUvsgz2Zfz'
        b'Hf7z4VT99Q0CpUq0IH095FaPa73UVTR5YNvri6rwAwUnNV546Yy9oTwWm40kZYQ7VDJRy2yEu/I/cUWeUUJkeEjV8ioj0Pco//EUduvz1zlzxfoUdh7UYXvqj9+0Vfp/'
        b'qPirv3L81y+yhaVELCwsDv4X//78K9H/zcvSqypRUSnp0XFRUVmeyiLR+srSiPFfffXV7wpEa2fEIk3DNamyqvEH2np1LpVXWiyrbrRmd7t0Rw/sbr/28GTHrQnr8ax5'
        b'y5nc+ZMzeVOO3zzybT0+9q5LwEcmG1pcWqLv725X7fZ7buI4bvzcZO8zz6DnxkHPQk4/Cz3zPCTsXeOwj4wsuvUa057pWAszQoWL19REegZ13vcMyw6tKYmM95epv29o'
        b'8WyL33NDvzI1fGNi957xnreN95RpfGrp+p7lkbctjzxT2STf9njb0gPbv1aSqHq8UtNRNf9chOKVtbLqzs9FKF7pmamavPJUxJaWVHXXKw0VVZPPRSheGeiomn2Bg83W'
        b'tolMN5ZpvpL6iFXNPhcJ5asQhc2qNp+LUNTJXgp/1o6IRWo6rxSyFVTdX4l+X75YLyXYuSbfuQYdoabzvqrxK4WbEtxQ9PvypbwUjjVZP0EqfF47pCIy2/RMxeRTVW35'
        b'aQkKqqavREL5h4cKn9dO49omrxSsVD1+LUIh378mfHzlJ45SVBVmQvoTf75c/7N2RF3ehPPKqtavRL8vv5CX3WYv5H9fN0XYXDuoLT8hRFE49Pfl5/KyJeWF/O/rE4TN'
        b'tWQ1+QnnlIRD/7hck5evD5d/fUMjTKxq8VIklK+yFA6omnwpQvHqkIIYhhSh+LWSWHXLKyVNodNQrFnIrx+lgC4S/b58fU1hc+2I4nojlVR3oHl/VL6Ul183EZtrfpoi'
        b'sTIgJlZcE21Xlq6dFss3t2EzRPzH39pg88x/OkD4NkkJXakgdKVY6fXVbPF1+H91iT+/mat0RKqisOav4q9irvBMxfRFuI5Iz7LM+0PD7XXij+w85r2f23nN5zy3O/Ku'
        b'jmW35XMd6+6T7+hs/1wiMrL5saHlf3eM1V92jNl/dQxsaGT+QhvV+s3auVyxWPW4+AO9zf0azxx83rHwfUfv2DONY7+VzxzUrRFkLRrzdkX5PWv9oD2vpxlzy/rwz6zk'
        b'+/9lIZ+27U8Ms/5LKV1O5PJCWCYhO0wkX9j61SmxWKwjDOn784Uw1k/nfzJ3mjD++ptSJW8D0TcN1L03S5KqfRXE2f7ozW8p/6Os7ry/grdBScLKynu5YWEvtmiqvtl7'
        b'aMxi7JcRPzv0981pDZ8eNFZ9++fbX75zzqf4262Vn5n/Y6t76ZRJo88+07iGo27uP2nw9VI0CDni/NymZ9/A3ZNFbXe/KttzMrn4N0ZOMUllRTNur5IGU9/4oV3kvtL4'
        b'oa8yv3RQ/vCTwBpDhyDD1O/ZbSjeYn554Ds1L+d7IqfWZN+Y1fhgdbl674kq95DRzEctGVO9oe/K3mx76/0TT8/vimvMv3ff7rNfaR6ZW33+gcPZye8uLr6oqPlVVr7G'
        b'ednKz97weu/ylzXuhSVGq88ypRLzlp/1Kqu7KZn8SKoVWfXpDw28vpdR46wQ+amepVXkDzfsabH4W43dH/1I69WxE74Vym/V9xQqbvr8zrYvfj6tcfZH78iyZTXfOjG6'
        b'/d9+/sGPPjbsneu68Dw7ynMl7Vsf/ayy+tffn56LH7L95aX0q5tXNlmdVFZ0tt0sH+KbaHFFSHeDg+WTgJySKIvUaVKBH14wk4/M0zDjp/7BDkicy/dwXXCwMOhGl5ck'
        b'1GPND9bFcK3wqiFV4m+tPvcLEycJT56VRVp6kk1Umru+iN7Dc3TX/3igLNouUFmkJFVQSaLl9T3lyHWRHzuB06ja4JSI+9T05HOzuJlToz3X2AizmMxRPUPRqzoqUBsV'
        b'cqN8xKE/j59/PQ3zVa4QSYPENE4r+uvzSD/lcWf/4zv2Rh13eD1TsxZXSIJuWLyebYYaTsnnwYngkfV5r324XD6oeRM/3bJ+VbTD9DhX2x6XQkg3SmhRmPtYONtSl9v8'
        b'/XYE7aamba5ikTI3KCiFKsrv6+AIK7q44rSQTP/XE1FbSjyo3G99/uh76fRA2H/cOylwfbcWP5I4Q9k3rte7hFulXGknzJMjieQukfSkmJ7wCK0vJexPd3lMGI0euENY'
        b'v2JQJHUW0yjf5iG5RahFeOBm78DVAeIMGhdJU8U0b35MPk8N9XE1LdsLE4wHCHcOROuv86BUtDFfSrepY/P6PDV1O3gAHSXMXRbIVR7bxCJ1WwWuO8DD69NsD2sbZf/H'
        b'7hwXaJbjCjTOTQfW55a5T3PUos6T2shUCP2WwdOZSJA0RSKzLVIDb2Uqy5bj6mYELcoHq9rLL/aUekQAXpsC9/JQ0mtL0Ag9Xp8VX0Ij21/Pis/TYfI0RCWNl/xpzOa4'
        b'g/Ux+YTQ8on5g49TtVOQg62SyPeo8o0Qvic3iy1s1qnO4zyNCMj1InNq48EDF+T79tFUlDByI9BTKkzKo3hDzP1WNC2Hdh6XXBX2OQjrU63PtA9c3VMQbciVUkms+WuL'
        b'0VMegs0rhCUePa8FKIhUtylQZSYNfT2j+RSP2Ps57Ah0cKQCnhCLNAwlak68PlU/MsBuO390i79jggcLkwjVovb6rhLupPqz66BZQM9N2B/bYScsbVTFbZHC7El1Cvwo'
        b'TWN95qap4zxnL4xuozkdfxHcaTLS1vuvkXX91aPc//WoKQyR/jM50v80gPZ9XcjToe+IhHTo3wtEL8xEivrvaxq8p7npbc1NHXnvaNoU+LwvVSsNKAx4pmvZv/dd6Y4P'
        b'pZofSnU/lGp/InV5W+ryidQe21//b/SJ1PFj6daPpXZrCkqKhmsKElXTjzUsv1QTKW7+WGqJc18p5e9TPAq1/pf+WbuZC5gaFAT/5uXJy2KRzsaX0Mq4qMmaBH//7Sfq'
        b'RvhC0fB9HYMKRXylaPjbbDsBiOpKhzeKeKP2YQcJ24kP7xTxDrGw7SARtndqHoEXHxCjXJdoO1YlKbK0rDeFNZwVc3IzUmSr0pSk7JxVaVxSLMr0DFnaqiQ7J2tVMeaq'
        b'MFJbGpOenrIqSUrLWVWMR4KJP1nRaQmyVcWktIzcnFVJbGLWqiQ9K25VKT4pJUeGD6nRGauSa0kZq4rR2bFJSauSRFkeDsHlJdm5qatK2elZObK4VbWk7KS07JzotFjZ'
        b'qlJGbkxKUuyqxtH1wfqB0ZdwJY2MLFlOTlL81ai81JRVlYD02Es+SaixaoyrmyxNmBJ0VTMpOz0qJylVhgulZqxKfU4c8VnVzIjOypZFYZcwX8qqbmp6nPue9dUpo+KS'
        b'EpJyVpWjY2NlGTnZq5ryVkblpCN5TktYlYQHBqyqZycmxedEybKy0rNWNXPTYhOjk9JkcVGyvNhV1aiobBnsFhW1qpWWHpUeE5+bHStf/3hV9esPaE5umjBn6O+VcLYw'
        b'ov7iX/zPwuKP8Kv6tQD8SvgnqEBtsfiqoiD2/lT5a3n5PxaAVkreLqJvuqh775f8ViUeXS6LTXRc1YmKer39+gHDbze8/myRER17SZi8VZhoQdgniwuyVZGPV19VjoqK'
        b'TkmJilpvg3xY+2+F75VS0mOjU7KzPhYyhRJB4MqHwsuH7K8/x/BEd+WmyLyyKrBXWH05W1iLEJgXiz9XkIqlaxoidc0C5S+k0R5ig7VjVyBSdN9T2fi2ysYWv/dUtv9A'
        b'ZfuzHV7f3MY27+7we19F5wM1o2fGru+o7Xom3fWBSKfO5O9FG+S3+9+ifxKW'
    ))))
