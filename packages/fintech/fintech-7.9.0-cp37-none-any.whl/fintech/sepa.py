
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
        b'eJy0vQdAHMfVOL67V4HjqAIkIenUOeAOBOodCRAdRFFBso6DPeAk4NAVFYyaQT6KUO/FKla1itUlS5Zsz7glcRI7dhznknxxSRw7TrFjJ7aVfPHvzezecQcnhP3//kIM'
        b'O7O786a8eW3evP2I8fongd/Z8GubDgnPlDM1TDnLszzXypRzJskxKS85zlpH8VKTrIVZIbfpl3AmOS9rYZ9gTQoT18KyDC8vYQKqtYoHywNLMorSNPUW3lFn0liqNfZa'
        b'k6Zorb3W0qDJNDfYTVW1mkZj1QpjjUkfGFhaa7a5n+VN1eYGk01T7WiospstDTaNsYHXVNUZbTYotVs0qy3WFZrVZnuthoDQB1ZpxfYnwm88/AaRPqyHxMk4WSfnlDil'
        b'TplT7lQ4lc4AZ6AzyKlyBjvVzhBnqDPMGe6McEY6BzijnNHOGOdA5yDnYGesc4hzqHOYU+Mc7hzhHOkc5RztHOMc64xzaqvj6Ygo18W3SVuYdQlN8ub4FqaEaU5oYVhm'
        b'ffz6hEUwdjAKtVpJQZV7aFn4TYXfCNI0KR3eEkYbUlCnhOvyZglDypKrfz+OGRDLOMZCBl/Ge9Bm3InbC/Pm47ZgtAt3FWpxV3ZZkU7OjM2Q4hdwB96mlTiGkKd3T0fP'
        b'oL2oMzc7MVuH2/GWfBmjxh2Sgkp8ykGg5kZNJvdkzBx0USpl0dHYOMdQ8ubevMUJ9IX8bNylzZYypuhwvEuC7sDPPS3nGEgeOqZPyU1JhQdy8dZCqKSxKGS4ZFriYHq3'
        b'KCiC3MzOF+49XqDGlyTj5uAj8PYguD+9FD1lI3cBCN7CMoHR+Eg2hy4vT3eMgtvoGtoyaCl6LghfDcE3bKgd32rE11eizpBghokdKVWgQ2la1hFNHr2KjptxZ14O3iJh'
        b'5s2W4PssOmQZBXfJkC234yu56GLlzDgYgo5cvAW1F5Imoa6kAp1WzszLUDSjIwp4OoZgO24bh9qz8TVoVV6hjJE1s/gkOlgk3kYX8d6JCTm6xHydnmVUuLVogCSwCm2B'
        b'24Ph9sywpQlZifG4PY/0KCgDHcHbOXwJH0Xbqliv9TTePek7CT76YiPzf4GPznhngjPRqXPqnUnOZOc4Z4oztXq8iKNsWwDgKAc4ylIc5SiOsus5fzhKmhvbC0cNAo6u'
        b'Hydn/vP4MIbRVKjMjtUMLRwwkWNiFgTCVYXqrdFrhUK+IIB5M384lFWoNjbFCIVzB0iZb+wwhbMr8vRRucw5po68NjxhoPSrcKbCFvTB2H9wN8f9ZaWDqQuAG5fKDrCX'
        b'FYzmzdXrUn6bsu7x20LxhvIvQ3aHsHEvrvyK/e+i7brXGRfj0MGNBHQQ0KsTdybNj4vDHUlZgADo3MwJpXE5+Xhboj5bl5PPMg0hATPwkxWOufBGDH5qvM1uXbXSYcO3'
        b'YLFdx1fxTXSiEF/BN/C1EKUqUB0QHIS2oTa0JSV5fMrEcRNS0S10Wcqg+0sC8EXUHuHII0tjF76/ITcvpyA7Pxdvw214CyzLrbCguqAxcYnxeq0uAT2LzqILxfD6VbwP'
        b'78B78Ha8F17cvZBhotFt9FRycDh+Dp3wYA4ZfQX8Epy3JbspmaRaIs4r1wYzuU4C88rReZXQeeXWS8R5re5Je6S95lVaYCUTbn79rb9LbFPgyvXp3lzj0hfffGnR3cvb'
        b'r+wdLnv9GeOiF2+Hvr7kxevbj+893mJmbYqqYDzndGLU9qxkSU0Qk9MRPPna77QyO10we+rWwAwATSKLE3eapVNYdGUtbyckAIqdqxNgAA7oYYjaE1lGjrZyupX4lj2K'
        b'vHsS7cGHEtLidHFZOg7uHeR0RYuFau/hTcMS0A70pA535Y2TMfJyFl8sWUzfg2nYjIFIZqGLGXgrw3Dr2MzBBVrWxcVptRIr6axXwkHyYMD0aqulydSgqRa4kN5majTO'
        b'dEkcZp7ct8nJkM0NZMNZq9z9klbqCmgw1ptswLFMLqnRWmNzKQwGq6PBYHAFGQxVdSZjg6PRYNBy3eDgmmC+lcyjVUYSUl86gaEmMO6HcnKWY+U0dZDeRCjwrQToJOpo'
        b'YhkO7Wfnok34ZGYV1wMr6ESmEKzgKF5Iq6UevJD0Hy/I9Af2wouIAkckGXYnuoHu2pan5UHT8TkGnTEXUz6Cro9Ez+Xi9hC4wWoZ7Jxb6xhAytvL0CV8bV0akFJWxsDb'
        b'h/FTtFuoxQHLoTMat5JbGQzwtVNoH61s7lp0LSgSPQfMig1j0N1h6IAjDMrnTItJMC0lpfMZfCgEHaFPD6hFJxPwExV6OcMuYfAZ1L6KluctDsC70AF8fj5kmhjgMVG0'
        b'DzK8H+2DO9fz5EQ4SERO/JQ2gL6i3oA2TRs6CEYWb4b/6Dl8kZYnob0lj09eQ8pPwX98D20SendjA7qJ7sZzUBPeB//xXbSR3imEfh7Fd4ebyZ1b8B+fQjeEfu/EZ2Hd'
        b'30V3y2Co8RH4r0ab6S38VCraClVsxk+SW/fgP9qioPU9tgIfRHeBFN0PIXwX/uPbcY5w8tLpRnjhabyHIEQQE7RhOe0lPgK05EBJHjoOVY1lxqIXYLjo87dzLdD7a3gj'
        b'IE0ykxwxiwJYiO7DktmF96vxPriBtjGGAYOEVh0xTcfXLIwNX1sFCIjPsqPKsJOSCQ9l4ryJCVnZNUwz81joOraZbQOZ0CptZndwK6WEt9ClI6wfzsXpk11slZbtXol0'
        b'TTwInF5nttmrLPWNMxeRKskdOeOYSduvwDdyU0HOEaQOysaz8G7oUTtIRQV4ixbdlKSkgNADQ33NFoQvMOh5fCcIXX4cv2B+6/6HrG0v1DPh3d+P3npP/URRZMvPP82Q'
        b'vnL0pZfeeu1zdn9XgOQDdftbF996KXtpTMUvXrb9/qUP/nGaa6j/8tTFDw7EBB4Pt2+ZbHxDG3H68Lq3F6jSpn6RfHFry8fPl2xr+skbjdvOzz2qvTZz82tVhpx7K0Yd'
        b'27VUfyi1vH5caNfEmPYS7cdPfIQyf25qm2ktu3R7/dezrGs/ffM7g27Uvf9l3m/UTjz6KVBNMhujlqEjCfq8NC3uAPFVji5wqUaHQDLvp6DnQQDBbdl5BTImCGipisNH'
        b'0HGrnQhdwPA6B+PORNSBNoFcBjKhfBk3El9bbR9BXr6KLk2g/BB3wHrA7ehCjozBOw0R4yV4J9qPd1EYEsDOW7gTXbG76TYl2nPRwV7UUyvtSU59Z9IVZGqosvAmA6Gn'
        b'lJIS6ZLJkrJSVin+SNlA+AnlwtlQVsXGsFa1F4Vlba7ABovBBoJ+rclmJezeSshT75Zw1lByHeIhrKSabA9hfS7cm7CSVij08lzcZcSnvfBIygzCO6WrU/CRPugr5bo+'
        b'9LVvvttL5u/NdwNEeWpWOAPCb9ytoIrmQYNUgpR0e0YWsx1kpPcsFTnzogKZTFoaOD+U0TBM7UxbReJrkyqER7nIIAZWf2hEWEWetVnB0BW/LC8S3VmamgzA0C6mEl3S'
        b'mDeOKeVsi0ndJ0Z/VjE+6M8VtdV5xjeq4/Z+svHygauLO/ji/S0Dp8ZEJSfyn/CfVCSmSK4OnBYTnRJ1KI0vXlQcU35gVFrik5ELQnMPEyHgOTnPLZlYAux/EDPy3QEb'
        b'gxdrOYrIkfWDEwTuPR2dpgx8CnrSTuRJJXpmfXpDgj47MV6rB2EMt4P0pZEuw9fRDpEgPBK5wqpqTVUrDFVWE2+2W6wGkVnT+S6PoSimhhRQKswLpSRVZt6lqLI4GuzW'
        b'tX1jFBk+a4QHo0gtSzwQzvhgVAKUBON74wCZskCpQVsL9SBktkO/kmAxAp/blscyM9AhOT6NnsTHfNQBD3pRoY4FBOsW6liKXA8X1n2YN2nl6F7INUJArq2jI5izS7Lg'
        b'qiJ2X+U6EY/CZ4Qx74zMZJjGirzsSTxTSksXLZQyowrCiGSuGqcUsSs6mmPscjJgFXk3mAyh8JUQFfPGrHGg71Xk5S81CYW/XBjJXFhfRF6f3jU8Wig8VDaEqVvSSJ5c'
        b'ujzeJhTW8xrm+dlPEvBLjeUThMLFY0cxbU27yOsjvomYLRS+nqJlZg85RTSIOT9ZZxEK79clMkvNV0mdlUUzNwiFRTYF80nsUKKVJL5RbxYKxyYGMqP0elgcFXV/SIkV'
        b'CqsGjmFKqw6TJ+cMj54oFA6cFc+Msl8gT46omC/qL1dKBjLS6AoCfemr0TOEwlcXBjBFuYJSIw8IEwqHN4UwoSqQnZMrVO0rlot9nz+Y+SqpgdS5NNiaIxSumTKUSR65'
        b'jjw5/YsZ1ULh18YRjHLgFjLII9SmKKFw7/ooplFnIO1sroUhpIVorZ5pXXKPvD5ic36xWJgynqkLfYsMXcqUuVOEwq6SVGZy7Y9JnSlXJRFC4UU+mblQ/BoZ+TkD69cz'
        b'2lGCfHAJ7dURo8S4NUuZcXgf2u4gdDUZt3CpgFEpI+cxKfhqM5WLcEcU6kqFZZUK8shdJtWBt9GH8aY5dakg+YwfEcmMR1tG04rROXQOd6QC3k+Iw9uZCeFlVKiLwefC'
        b'UwFvJ2alMBOB39ylNcyam5gKK2OSDrj3pCAQnQhZr6hZlApLZfIc1MJMdgwTar23DjjXNbiaoprETKnCJwVB9Tg+Xo6uQYOnFqA7zFRQsW4J3bsAHO0cWRtzeDkzpxFf'
        b'F+TX24XoHhEz5oKGeJuZmw0iGWlHY/gYIvun49YhTHoiPkgL0UFFlA36keFgmYxIvFkQuO6APveCDXqSiZ9ERyDdVy9A7EK38WYb9GYevriUmTcmSCi+h9rRAcBUJmva'
        b'BiYL3V9Nh2MdPpWPSXeyFyYw2bjFIgiat2EinsWkPzkMamVy8Em0WwB7AHUSCRuanotuyZhc/NRo2qNJ6AbeiK9B4/PwbXSDyWNKKNyB01E7vgatz7eiW0w+OjFTGIDj'
        b'aD96Bl+D9hcsHsEU4AsFQl/PVKfha9D4wsjlTGFIjSDDXgP9C2qBxhfhm/g4pC0gz5P2a/HWAGJpm482oSeY+ZNG0NLQacYgaHsx7loOyR4YRzoEmxPSg6DhJejWWqYE'
        b'hJjz9GHcijrKg6DhpQY9U7oIXRQm+sBU9HQQtLvMgPYzZcvxRooTa2aWBkGbFxTFMgvQC0Npm4eiY0uCoMkL16F2ZmHaWKHWI1HVQQpC2fAOZhHaulrAk82Vi1EnITkg'
        b'Dm1kFqONUC+58Ri+NQt1QpvL0U38FKQ30HEB559CbUmoE5q9ZCy+ySwJx3fqvvnuu+8+jJIyqtwBlGIiibjC76+fxLyY4iLrNuXt4DLGPLx1FGd7G+68/e+z9dtmNHDj'
        b'YtL/dG2Ictbw0Nflc7lgRdZrstusLDJ70ghZePjgwO1/CRx+YO/Byq/Dp4SeOabK3F37zNqSLcuK0m7OOfDZ9YIJmaFPNJ1JTPnDN0PeTN+bvfXe55tkUee+fT38Jxcu'
        b'//jM3Quv1jg63/31+0GH6uZ/8+NWS93bV7H+99+ujF1z+X1T6pJtC/784NedR5cM/ODfX+au/eONkgujs747LOVdny59rzC5dd8fX2pveftf745p/NVPDzE1dfZPFi/d'
        b'UvBW7RMZP6kwffzHrxLb2u0dtQsefKtQHJx6TPN3kF1jKVFYAmPZmViA2/PQpqHA2lkQU89z+FLeQioT5OKbEUQoiJ7mVurxvUQ7sVeW4ns8iGSg7ebrchJnjsyWMeH4'
        b'tgQ7QcNpp/JtVdNkkF+35GbjZ9BtdBFk48ncQFh49+1EogtEW8fZ0MWsAl0csV1mLcTbJEwY3i5Blyvwc1qZX3FC6o/3ewkZalHIcFQZiCRLJQxiT2Z4FSvlQomUwUWy'
        b'5Ceck4IkMIjkJaEge4RS+UPOWiM90ocEpA9HVV9CB2sd4JE3IikHd8sbT/mYBohpE51Qo9OCwNG1QZA58iERDK5avFGGduHT+HIfsgYxPDJesgbbp6xR82hBViHIGj99'
        b'XMXEALMLLqqoC3dki7LG9SFEPI0zcKEVquUNcYJ4On4UvkuE06A4Kp6moAvmP9y8JbURc9zTz3R8VlH+4uXtx3edazne0vrGuQPjNo87dDxrxGZtzOu5xgJjrWmn9EpM'
        b'8f60xJVPlj+pfnWQ/NjUvXXHBv3Mzvz8q+CjRfO1LEW6WcH2hG4zEtou06FdzW45s4/ZHyTMvs1udVTZHSBoGqymapMVtBoBE1RkKDYwnBJUFyppRnnNtdQGD/c92dGe'
        b'ySYvPuGZ7I0+k034Md7TiC/Na/LIl0l6bXy+XqvLyUftSTn5uboc0IhBJUQ7UEcg3oTO4q4+J95XyPweE++u0Hfi5QWUU4WggwVBxDiAL6A9q4BqA4O6TCf/mczxTC1Q'
        b'wuSATbavR6mZTHPU15tltkkEL7J2flaxlE7zlZaVbFXgR3NeHfGc+rT61epXI0/X7R1xKvLjiifV8tAW7az9m1KDGfWWoLEpcaBjUG70HLoWTSd3SaVIUNDZOZQgRKBj'
        b'6JCgY8hwi7eagS7iE+I0PXzyY3roF75THyhMfYCSjYKpt8Z4T3zVIyd+oGfiyYvtpMJQOvHMtz5TT2YLXUiV+tUruue9FlCaWYvOBeC29GF96q6SHrbBvnXX1p5L3t/M'
        b'0/kdVxVCNgriaiZU5P01YYnAADOVMgb+xu3Pq6iTWBOFwu1qjrRM+YGiQvXOismM+ePw46ytAO68pJpyvvGTir9UvF5ZW33B9EnFWePr1Ukpf65Y9OLt7cNh5bOvV+cY'
        b'd1Z8wnO/eEOznikqU9gCS1KfnhyxYu7YucNLJm8f9saLv+aYI9PDZv1sIuAHGVv8PL6K24NAQDufl58IoHNZdBU5h9uHkaG9KcW7gFvhrUmF+auBz3QVZKMLUia6WDoR'
        b'bUnsryYa3GBaYzfwDpOBN9oF9AgX0COEYwOBNxBDBwccwTrIgyZSl5Q87AqoMxl5eG/tI8wbZIPJGutBG1LRNi+0+dJHHR1O+taBb0/CnbnoYhxqL9Tmo65Cutc3Gl+V'
        b'hQ0o186ukogTK/PGk4kCnkjpvpTMKa+Wi7gioXZkKeCKhOKKlOKKZL30YaqovBeuyARcedaSAvnkVSDTh4fIIgW0mB4qBVy5zAeDBPXsfANjHhmTxNkq4Y7hRPGQLVeC'
        b'NyarpL9fVZyc9u6P1NfrZu/esf1YZ7GrbNC1jPciO//81YO3p+ieT46Lkv3orc8q5j39I8XgQ7fjoqefuJ3+x5/di1/bMP1c66ydZ95LmfLNpOn//u6ncYt+cb1q2qwZ'
        b'pQNjSyvE3Qq8eza+TQ1koK1sVDAcOsGW4WeiyB4Vk4Rv4JO52YljsBMGke6W4i68kcolkZGwQNsTTegQvN1VyDJKvIVDrXn1AoXauS4YytuS8FOLgANJ81n0QjZLK8Wn'
        b'8DWQ1Dvz0YXQlQwAbGXnxaNTfckq8ofe6omVqhpTD6SMEZByIKAjCCtqQMpAVsVxnJKL4qxDPKgpI6gJ+EiwzSWvctgt1d7kzO9qAJQlC8o61BdNSaUHvND00yhvNCVv'
        b'FLP4hdxCnReKzguXMcPQCSk+ZMZP+2diZAfVs23KVMt+CCMLht8BvVB0mICihVk/YXbDPDaaVpuvJsQJKBou1xBfiMlvzrdNP5Y+TiickxrAQOeS31y4Is9Z+5hQ2FRE'
        b'LXFKjWxF3T3FeKFw1ZQIYt5jjg2tiP1FdaVQuGjVEGYykMhjj9ubt0hGC4WOWoFZzg6qCb+rXykukAg5A/JG6IsDa1THA3RC4YbFcUwRQP+80cFtcNsBl2fOYpqB0VUU'
        b'Ly/WZ8QLhQvKpjNrAFBj8ZriKL1oBWiaMI2xQzuZJlPKNMdg0SgzbiADfCdZE7w8Nm/RHLGdpTpmEbzOSNZXRgQ4hELDbGqFnPzmsvWqDploFqkwzYaJZiZfjq0Lf3V+'
        b'qlCYV0xWN6Mpyn+8LmTNLNGAUkrERGhSiDHxjyaj2M01g8kGuXK7dv30WL1oAYkMnsjUQd81yetTOlc1CIVZcUXMMQD0/mO1y386YqRQ+GkTz7wOgI6trq3eb58vFP5h'
        b'ZTXzBrz+fixfvXmWOHH6cVHEOyT0sqUh9r1Jop3oX2vVhI3FFAU4VN8tE9nY1JFNzFfQpBcrmlZph8iEwi2pKVQ6f7/EXPz3WeLrt9NH0N282cMaKsebJjBm/eoW1qYD'
        b'HA6ff7hsR34BTg7d/NqVLz96eXR+QPagRY2hDW9lJCWHZ+3Y/nrHK2v2dP36n8q/Bk8OeO392C1dg1+q/s+MFw58UfJh+JmoL44ftlb++OOXAs78q5E5U7Slgo3YLdUd'
        b'+wv7S+XSt4+lnm5uZS+8+OGGkN9/seCdIYvaD/JBo97TLk4oXtT14i9by79t2Hl74Nr7ikMfBp8bGmf62eWPS//8dVnOmrm/+/Z3U97dPX/mUsdLz7y/fo80f9CtXQdf'
        b'OFL47PODKnbcbJ7wQebOf8U3tvx0xDl7eGdG4xMpjdcaf/b+358f9knUl3tck21/+jfnSPjnZ3/ZmFIw/va2iI/+fHp/+uoX60/+9Oiv/raw8uu1Neff++LFX//03yMP'
        b'pC79JrfwH6M+Tkr51TvvHn75N38KOzs1KCV6+PTR0Z+f+e5MYfPQ2S/8hxkRufzYwWKthCqEAyOr3by5mzGHZAFrPoL2Uoo9Bu+Yl5sYl0V2gzY1wHoFTXMtfl5Hiev8'
        b'crw9AWSmrsSkeJaROljcjg7ia9rgR1DQRyd90Gdv+zShv5XGhhWGWkudmVBUSoRLBSI8RSkBMgy/o6h8EMpq6PZHKJUVwjmVlGyLcHRzBH4kPf7SK7VEBc+Hs4FAwJWs'
        b'VeMh4CCCrjUZrV40uw+GwlqHe8g1qeKSF7l+J7KnkRt3FmcI5DqH6PloK/Vv2Abafja+noMuJMqZGfiKHN8eNdpHZZCJf23VkJiIDxlTzvFB1NzNgSbC8ZLWgHKJScpL'
        b'eVkr08KWy+BaLl7L4VohXivgWileK01SwgaqOT6AD2xVQkmAE4TL8kBK7FUuRRrPW002W0GVXISvFH8p1Z9K2IjgdePxwqlWisxE3qYEZqIAZiKnzERBmYl8veJh++a9'
        b'1WFZAbVS4W31y0vg7/Dxi5nhjfGCj8Vbf3+XtdnJeI9uG9JxJQwlh0q/K9zbWuJ8OT0yTfazuI3pVWeGpn3TkXVJda7kf0Y9bpt2Nzfi9J399t8fj9/y94T5wzLupgy9'
        b'xX14O7ouxvXVX/KmPfmfGzt+s3ThpE3fNh9tR59nbFONkQQfVj2bPjn16S/RHw4HFx64Nez1S8MmRD+nDaTLh0N348XlQ2SWkxVk+UxAO+hNKb7eKPhuWNAlzzbgPFbY'
        b'iAQ5B59P0ItblPgG2kO2KRPQ09QKNGERvkAEz2yx5iP4ML7LoXZ0ESqnMtENfAWdTdDrqE6uCEYnueScUDsRcnVDclLnok60DW/L1aFtaJuCCYrisHMW7hAsTDfmSVBn'
        b'IZAF3FUekaBFz0iZkACJHZS967RtFrQRXaZPJKJzUlAJ91UquYHoONpHqUr5/FDUmYTbFlQm6bMFY0k4PiUBnfku2khbgK8Ho1M1qA0e02tz8oF8B+FODt9Cpx29JXNl'
        b'vylHN2VQGAwNptUGQ/eW6AaQrOlWKFEn1fQqnJWLP00hIhrrxfeEVa50SarqbHSDClROs32tS9loIfvmvMklt9mtJpPdpXI0dBsv+lIw5Fayc2Ql8omw5TWGJMTMZI3z'
        b'kIeRkPzHizw8OciLPPRqpUd0Y8VfsgZsZPE1M8sF7ZIlfjlKg7gbB9dSm6muuttJQBgu5fQ6Y30lb5wZDLV8SWpsCnXDct96JLBqAZjMQEYKiF68B4YHkJUQODW8bCVe'
        b'o4+ssUaoMcDgHvU+ag3pd61iOxUGYQb7qDO0V50+MrKeEQw9QBz7Jx239jTzcExPgiYpMH+kOM/aiNIjufrbzyo+qXgDdHVV9ftvMPKvmYh/cC//pUMrkIhKdAVv8VqG'
        b'Sg7fwa0D8YENov+Hf1XabPMyt3V7X22An6imAe5p93nKbcmhA9WN45wPk4v3jB2xqYSzbh19I/x8rvbGY/9AgJiTf9ogwFcDcfwyGFyBBoPgoAzXKoNhpcNYJ9yhKwWW'
        b'o9XSaLLa1worarTvskqm3SWOYkabrcpUV+de173NRYBjwmPwCO0Ccef4mhGthUoZw4aHqlj6w1Gf2MnocLUtL1vbbMjR6eVM4HKgn6hL6TO7QeJf2xbWiyOz5ZLdkt0h'
        b'u0PhN3h3iJmr5uBK/OG5LjmfSDi2l49qKHBMwrMDgPtKTTLg2YpWBjh0QBcHfFvGB9J8EM0rIK+i+WCaV0JeTfMhNB8A+VCaD6P5QMiH03wEzQdBPpLmB9C8CvJRNB9N'
        b'88HQskBA+Bh+YKuyXE16whPpYFAXS9usAkljMB9LJYUQeHcIedcUwg+FtyXlobTnIfywLo7XidYPCa/hh9O+hcHzIyiskRRWOORH0fxomo8Q3t6t2K2sluyW8mO6JLye'
        b'yhWCjzkZLbUzpDqAj+O1tMZIqCGe1pBAaxjAS+gyTAK5pYrSxAdjAzVe/8RSwfHd545W7pKaQdZ0SQkC+sO3giqFOOFkhajdSzuTUAlBAAoggydOqtshWV2tFqmHgopD'
        b'SqAeCko9lJR6KNYrgXoIzZZ+MAgIkE+zyL/sBrPdbKwzNxFP/VqTxih2wgycydhQRVz9e74ytdFoNdZrSIemajLM8JaVvpo9J61AY7FqjJoUnd3RWGeCSuiNaou1XmOp'
        b'7lUR+WcS3o8jLydq5mTP1ZIq4tLmzi0sKyg1FJTlz8kohhtpBbmGuYXpGVq932pKAUyd0W6Hqlab6+o0lSZNlaVhFSxvE09OIJBmVFmsQDgaLQ28uaHGby20B0aH3VJv'
        b'tJurjHV1azVxvKnRaqoyQj1avSatQXjGbNNQ8zNUDp3zW9cqGFQemFnv9orjR1BhKm04uXIfuHCPPyglvMn60JdFniy8L2ZgEEsKdanjJk7UpOUVZaVpUrQ9avXbUAGS'
        b'Js7SSM5uGOv8jLAbKHRHhAhX/lvcn3rcHFmoy5374fUJvFioTbj+AXX5GNJ7G0eDChxkscaCLL2PiNeJenI4InchbsulJzeoSex+MHoeXcf3qLXBzm8N3cNN5pjkCvWD'
        b'2lGMg+ymoENjY3BnPr5gRBeKcBuRwJNwO1wVlgg1lWWRPdL8/Ox8ltiITwTgmya8VzCzhMhDh0tiqOuM0lLNOIh0IUXX0C6y7ZoAb8eDKtCeNz+LSt9U9sY7tegcU5Km'
        b'wPvCV9JaHjNJxp9nqSlI9e9Y0X/nYKps1b+4ULpB3hBtYxxJDPEhxnvRUXfd5NzEXe183EaOckBjk4qzcEeenJmHT8nxFZDvzaa/3eFsz8GLx2YZR2+bpgadKf1X/xpz'
        b'5cvjJ34UPDnzb7M706vSwtrR8fHBDRMnHcsbpf7xe+N//o/ffFGry1xafD7iVuzRP5QVW0bnW9evWvbz2ILG05OHjFkT/PNrARHNe+6dic7WJba8d6hgarrRsO36uSOo'
        b'5Jn8j/5ny1e37i771rg5afIXWydde/vHWVcaX7Z/e+xXH/9P1geDtT+3FdxZMSDgwiub3pNcnzl44XtRqzbfC/048/Poy7q/7Mp5zhTX3nIm9bl/h6z/39nfvf+VNoTq'
        b'ILNBmbgTBH3W5k/Cxxy6eNyRxDEDkFOqzI2g0tPUoRXiLjrZQk8oFzfRM1Ar3bjAxzXr8a2kXH1OfmI26sLbhOMvg9B1aQM6vozaP5aa0bMJOrxxQrf/PDqBW+x0c6BT'
        b'jZ53byodWkzUeKGGAbhVgm9PDKR2bfzsgDjUCdr9kSXCXRk+yOI7I6MF4/Xl8EQi35E5kuAnCvAhFm1tZAQV6nl8Am0l76LLkwX8leE7HBuBnxXun8BXQt1anEeHm7vA'
        b'bgmwk6NboHY+VUrUtC4tPYckdFKoKCEG3UPXZHgzbsPXqKo6i4ChteWxjGSxDB9l0Xb8LCc08+kJj8E9fT60sl6Kb7LoEL6Pt9FmOIzoBGlkPnEqIJsj6hoJPoj3TtWL'
        b'A3AQdcbAyyBKUUFKPVeyJiUTXeLoLOrwhSLydiLaKniPqtFZyUR0Jh2ac9q9d6T+/2xt6ikig/xpBp4qqo9z3NJxipK6PKo4wfVAyqo5FRvFEXOSiuaVcjnr+8MRoRd+'
        b'VBwoVAIh07srLxCE0QBBcCaHQazEXOJXlO2WufutDWsVQiURvrXTOuM9FVNhl5w8HOYjr380xlte79X0R+pYtW5dkEgYfWhYS90aVjcMt775YHSpRyAhnAD4tZsVxFlN'
        b'Rl5naahbq9UDFAlvqeqvKiw1VJqr+miQwd2gB6MIeBBm+oTe/4EgAkIfcCs9cBP6Fie+H3hB17WSBd8HcJMHuN5bFvmh8ANF+MtZ97hzsKSMgs5HkbKPttT6DkRfUsr3'
        b'awgdCs6a4V4EfbRhhacNSf2Rbr5fO2q92jG273Y0eNqhe7Rc9H3QQjCs0Db0AX6lB3xyKdUFALK3tUsjTqmmjh4d9tuCH24wkdCxkj440UvMm0vEdpvG3GNd2kymenpU'
        b'GRQHKrn3epEcXxb1mRLQH6BHGQ6rRVNkXFtvarDbNGnQg95SZRx0EzoLL66aqE/RJ2sfLneSfzKmt5G6VMtS752VRnQgoUA3HHUAL5POZtEzNeiAecfSZ1jqPdLZ8cZn'
        b'FW9UZhlf/ziu+JOK1yv/Ajmu8uPIVyNPL/tY/eoaOb9ds234/k2pEublMwETXtiglQrM/lR5fDef5DQip0wfho5QYaQJvxCaiy+BTCA6ufgKI6YAyserBs4hp3znzCF3'
        b'hFO++BJ6gfp3xaKNGMSZjjy0Z4Sc4ZaxSbPwmb7MTApi23EfShFdeTYwTYFsFLFjirRefKbge9qXciGx+/CrrWpfO6lv/fAy4X19uO0QbRw09H657UgoMZE+cPbCgxKT'
        b'XdDAHXV2M+ifIh132AQdk56c19itxgab0euQfeXaXhWROqZSG8TUinx4BqqCP8Yak7WiD62H/OttURRdQvZwW6sHMoIqo6xdI6gyikR8h/pG9NBjEvGzD1VlkHOY+Wen'
        b'X2Bsk6GCf05o+6wiB/D19r3E4k8rPqlYXv0X/s8V0re0W36dmBE/WqWdvSqi6GTLlKfGbRbwNv5vQQe+26zlqP+YfCEnyOheAjq6BSI22dA4Q+VUdAOfwrseJqiiayV4'
        b'Dwiqc5GIjI880mIz2Q3u6aFMmSJoqBtBNzAytzzXNNCNRr3eKXADozg51Rdr/bgW0Se68TcfkvU++Nvq7VzUB+D+mszVvq/1QeQ7fHlMfzFX7z69Q4iDfz8n6kJC3UeI'
        b'jc7jQtKXl5O4tD4AJaO3mcuzuixWc425wWiHdpn5h7HDBtNqkWSP04/zYyt4uIGEF6wQtMtu10QApNcUm1Y6zFZxRHi4qrJreFOl2W7za5QhaxtaYLPUu0UqM3BJY53N'
        b'QisQqhYGtdpktT3cZOOoElo0d0428F/zSgepD8SROMJrNVZ3qwBWtt1IuG/fJKK3h6GywEEwdD2++VhuAdl0pif6C3Tzs/SzHnN7Qxbjtrz5WZJiLTqXrVlWabWuNy8L'
        b'YObUhNSPm+Agcw1L9yA+52VrgNfFl3FHclIxg67iPWXApvawK/EN5UJ4/pBwArYDWNMxfE3FTgdmhc8y6Cl0MsGRBrcGo334tE3tWJBF9hHLcFviAroZ3onOlWYlEjBb'
        b'svNwBwu06aR2Ddo7Cp8u5Th0lxx3vqUqGmx1ELw3DA/yblajp76ihcX4im6BginaIEcnjeh5c+qyv0psFnhny+gvdG/8JGDjbFXGW82vGiR7K4eXbzy08Vhy0GuBh396'
        b'Leiv7yTfCRjuHNz21rt/laCcxzdcXvnxruEDz96abg9Qfnhi8S8apRFZha/cKH3r4p0Vbzvf/mTozISL6NYb2gf3nvjvkQ2HBp/9+bu1JxrWskte0+ytVWsDKCMfhU+h'
        b'J4lxSdSWgxo4NT6ND9XhHXay4xG9Cl0NwqfR/Xjixk/IoZtyDkPXpPjZobiT6usDDOi24I+Nb+Jr4imAm+g83d/NxF3VuV52AVWoBPTpswPQBbTPriEzuQefaiCEGV4+'
        b'70OcgTCD8k7tJ+jppWiHGBUE30PHRYkBHWIoaUfH8AF0PEGfravtcQIRKPoWQfe/bUTtolEhGe2HCohV4TH0BL27DN/CZwWzwhqoVCLYFXahp0UXun45iBAC2k0u3AcY'
        b'R3RT+2glaOcCxVeJdF/IyXuQYZ9aCtxtoFTVQwf7YgISr8e6OQE5O99FOEGkmxNsZP4Z+VBe4NOI/uqeUgPQtD44wCkPBxhHNa5ukteXqtFPTcOjdgMV66MNZz1tmOaX'
        b'0s0tm9vTEO6nNcQtp95qqnbJbeaaBhPvCgAa7bBaQbjPrJKKLSV2YZWbBM4ReFR3lCLGGSR6qqiqVSLHkrbJgGPJgGNJKceSUY4lXS/r1lI+ONAnxxKiMgmCHCX+3orL'
        b'w7dnSF8E0u9+1+Mh/3BDOu258BZ9BUaNlBmJyqbXzDU2EP3IKN6rXA5MzC/3IptAwFBKCidPTB5Ht3/I1gxPlFBQnR4K3jPgUzWZdcYazepak7i5BB0mfe5+wt2ph4Fv'
        b'sNj9gLGaoCMNtqmatJ4ScoXYnUewv976WWABjU0zWDrCl/vhNpEOl2VBUbHIzdiUcLQL7cIkHsJTufhaDjMan1QDWQSqTNkoahkbl6vXxecAffWuw1N3Vk5ZXM70MCHG'
        b'AAjW+NQQFT7bgM5SQX3nfHIcffYqeUVFzkfL9IyD+IsX4es6f4I6btPl5Jd4hHR8SQtyemdJAH4Bn0O7HdMIld0/pxF30scw6H0J2YRpJhA2KjLEFHSH7jdkJebkAbmO'
        b'lzO4U6tamYQu03Mx6NSaCh+mnp2Id+ONhBkXlsQB7QZhPFGry5GBlnkmAHWhc8laCdV2p6BNsRSyhJHOXJ/JovO4axqNTYV3AHF/enV+gvB6PvFgOsA9jq/G0dtD8+cl'
        b'5OSr0DlxFFkmYqwEH8JPzDf/Z9rjUhs5zfFa8LghP7sbjJNV0qJiQyebstn5euinv/hN10bGGhH6lCbnpb9sn+Mav/tgsSNhaKNzV+nGZ8dWX/gmM/uVz6deXbSs7Kel'
        b'Sccrbzo/+s2nVw9Fvayekfj7X/5n/NhR+5av2RVX+kVuyZYf5579Vh0/6r05it89qE16Y+gng268l7Y3dsPNP29bNzBp6PanNuw5lJBR9jfg3IR4y9E2fS7pzvYYluEq'
        b'2XF4exkNCjFAPTWoB7cGAeaum2Pj7XmUnQ7DTrMv40cX0SV8KLKa3k7At9CFx9GB3Oz8eBDGOEaJOjm0CV9eJ+xW3EV38HFfXaoYn6UcOwtdFsL23CtC94TapVLUgc6w'
        b'6Gje44Jf/tY0dAFaWJiNLoSNkTLyOm4E2oyPUZnEPGgwdRKtrCwUIlskwnwkSfAeo47eXxuKn/cx8Y8MU9dIpuJd+LbAJlX/R2b5IMICRaJB+XhiNx+fLKeHAZUeLh4o'
        b'/qrowRBOsMFHeDNTsSaRl8sF3rSAJAtJssiXoQd8P/9VqVDTIg+7X+jhd+WQnO/B8381wpvn+2tm/329xBf64LZveLjtcMImgIhSpuHhMj72dSl1yuHgl83URlnHkUqI'
        b'zcRKiANxtOMtVQYD3UOwEjWA7jW4JJXmqoduZ7gUbmMwseRQddgV7KOwUsHIS2Iqp2+J7RMmLOz/aNvnYehmJQaSgWSelsGFUirlIgGhGHboFI6KjP1OOXXg0CCOiJVc'
        b'IBsZ5X0nnNUMI1cOwe2S7OfZ8gpgNcYkUbIX2MThregAvu3DwQLFv7b/9vAr4rlyKS8pl5mZcjkvLVfAr5KXlQfw8vJAXlEetFu2W7k7dDdbLdkdyiu7OL4QZJ0gZ2i1'
        b'hHr3Eo8ZlSmYD+JV1H9I3cWVqyEfQvOhNB8C+TCaD6f50N1qU5gQrwVkKOLYEuIMq1byEXwk8QGCGsN3qwFuKD+gi3oi0+fCqolXUbT4RATUSfyJiL9xJDxD/IsG8YNb'
        b'leUDoG0sH8sPgesofig/rJUpj6b+Qkx5DD+CHwl/B4pvjOJHw1OD+DH8WCgdTH2AmPJYPp5PgL9DnHKoKZHXwTNDnQxc6/kkuB7GJ/Pj4L6GlqXwqVA2nB/PT4CyEWLN'
        b'E/lJUDqSn8xPgdJRYulUfhqUjhZz0/kZkBsj5mbysyA3VszN5tMgF0chzOHnwrWWXqfzGXAdT68z+XlwneAMgOssPhuuE51KuM7hc+FaxxeJVhQJn88XtAaU63kptZXM'
        b'd8nT6qkj0zM+Yg9Z18INwZdJCN0JEh2Jv1ZjJb4wGkEOq1rrcbPp4avi6xllhQrqTXZzlYa43BkF+2WVIE5CAZEQoU7BLFK3VmNpEGQ+fzKZlnPJDauMdQ6TK8DgboVL'
        b'klFWXPBgeq3d3jg1KWn16tV6U1Wl3uSwWhqN8CfJZjfabUkkX70G5ODuKx1vNNet1a+pr9PKXZK5eUUuSVZZpkuSnV7skuQULXZJcosXuiRl8xZlAmSZAFjphusxXvls'
        b'VTQTwsrZAglxXce1sc1cC8uzKyS2oc3cMfY4Y4u3czzXzEUxJBBrG9cMiLyO5SXN7Aq5tbyZJQ578BZ7TELCt/LygfBcDBPJTGLWsQ1KuK8gV20Mea+ZMUihVtlxIOUG'
        b'Oa+kKkXABwZ/KkVPXy9xjrtdvXq+8DBBnY6CoCYYhTpoSR9WKGG4plIHqpJC3fiUcZO8UYgH7SK7mkjtGlujqcpcbTbxiX5le7OdaALA29xeXRSyW70T0BWUDau50vEQ'
        b'7WAquT21gjdVG4FteFCoAtQNc1Utqd0sjBMgoggHkKt33z4lc/5ggLmB7hd192bsaNtYF6t3scmfEn7w6Xfw74FEn5xcoFW4QnuCJXsdxrrGWqMrcAHpSYbVarG6ZLbG'
        b'OrPdyhPOJXM0whKxmpjuXY4GkliYPg9IU6b6oUdUCJQCq4gUbRQajsg3TSECAnzfnXnarD4khG89+/JuAJ5teV1PlKETt7bRpKmACakCHl6nTxf+VlToAcYsph9O2WKz'
        b'TH036z8ewWUwdQ7wj4Y+wDg3sFARGFm9y7kgj7FcQqfCpTTaDNTj0aU0rWm0NICC2kdDvvM0pIpu1zvqK0HJhYEQR0DTWGesInuiRrumzmS02TUpWr2mzGaiKF7pMNfZ'
        b'deYGGDErjCNfUUEw1Mgvd8CD5AHfWnx3Uz1na0i0PmqrYLojLXvO1rDUys41BQo7qwsZIE1+dlc/+Js/IlPWSMQsgcCY1lTVGhtqTBorLao0ki0Bi7CJCk8ZNY1Wyyoz'
        b'2SCtXEsKe1VGtlgbTcAn5sKQWqFTc4wNK6hx3Ga3gBBIyUFDv5a+uOzdTTLQJlWQcXXQpS4QFkKBPEZxGFfiBOpnh43EvjbZay3dPCtRYzMDDRWrIa+RPW4fV9KH9FGs'
        b'aCqJnj21QmSnfrbq+jRnVFosJKKpptrbbuKgU8H3mAa/RHG1yQoLcxXwQmMl2ax/iAXFI0oSRJIyPY0h6gLBcfAEg64m6Iiy3058JImJAW/NgsvCsricxGx0GF/SyZn6'
        b'cCV+YR7eTM3suMs+FRTBy/jG/LgcHQk5uy2hAN3AJ4p1+DTaiK5yzPh5shq8cT2N9YzPbhhu0+fn4D2rS1fIw5kQtE+in4Q3OYibwGy8H532NjvEFejic3XF7opzZSCR'
        b'KvG5YegufmItrW9kEz5gi8NH9WIgbhnaxuLLjxcKwvXO1QElqAvvLsNdeE8ZsTgUstrH8XV0nc8UYkBtyVeR5sgYCdrPLg1DG+vxDiFY90nUkmXL0uvQubnEHpGLLkmZ'
        b'MGgtMZgLL49SRtviFuFbOUT/la1j8UV0q7zUPDjsI4ntLbi/aEnRgK5pxU+khbY+/q8fhcRnLvjf6Pcj94cdGBSzeFRJxp7ma+nH2JfquB8NrRrzxfSnNl6bfMjxz48+'
        b'e2pAXmbrst1N3wRmDgoOnrHiQ83l9wcGNLyjefONt87uePPrv51pvPPWnqZ34l9eK48OuvO545OysXND/n0qdaHOWv/pxr1JljkPXgx6esjMWy347S0Lpi7V/emL4tF/'
        b'fjpy5LnX1vz3j2W5Hz61Wzfqs7ezlGO/3Sitefbel5PeWT/j4L78wvsbJo79FucmFI8a9tm3M5XPxhx5+3e3Ph3y9gfDipakHVsQog0TTqk9g24l0IhBuFPBSHVsHMz0'
        b'RbQLbaGmgVp0OT1Bhztwe1IWfrIWd0kYVaZEjl8QbfyoAz3Hoc4keIRlpEksvo470DV8TEJ9DtD2QesTcvLz4NZwFh2JRkeWYic1tuD2BGNutnl0fny+gpFLOeUGfIG+'
        b'shifXJRL2wMvRbMDNOhE9UzqAmExbuhphuGC8HbRChODbtIGT4iuTNBr4+NEFArBV0mwzufWopPr7GSdLJ6R67agsOkydDQSX6euE3IYiOMJ4lvSAhY92YguZxbT3ZTh'
        b'1gRiHslO1KP2JLKismX4PDrAaDRSfBOfnm0nenEuXLbldi8y1JUEuAQrLB4/L8Pn8B38xBR8m7axMmJWrhikaQveXI7bWSaI5/AhdGalnYb9asF3g3MLdWxFDMOtYtNs'
        b'G6iNJxg/nes+iqhHz4sneTcuoftKEWhvUG5+bm4+LJ7EXHcgi3i0VYbbotGz6AnkpDakmHK8D3cWoIuJckaazpahdnSvZO33cEr8IYf5BghE0OBL9zk3DxQtQBuY8EAa'
        b'4ZTIRcRPk6jrcpYc+guldiC1GLBSKA1nhZ2fplhRwPELxOOZMophfpgXJiu8SiWHFsLCoUIbGUrR8rOR+U444xco2H76bA7URkRG/44sNK4IDTgF0gDrFVeEo99M6NOZ'
        b'5YN3/ckBcwVGJp4qEUQ+IqgAXyG8ySN1ieIAkQ1sohjfm+2IRv8e8kQP6cG/tNCbiZX2lkyMhPv5MGs377QQpk52PNYSsaN3y4xVtcL2eb2p3mJdSzdoqh1Wgf/a6Lcy'
        b'Hs3Ie2pJvvKpl/eg3WitAZXE/WSfWxwNnj0OASvcWxxugYmIOSabty7fB7/3f4JaKbgH/aEgmEaKSJ5YNKJLLUaM+cmMWBo6I1mdsfjkOPGjAsG1t5g1gC3HJquiEgtf'
        b'fozyP80KfNsWHMwxaKeaxVtJiPjdkY5sSsRT8ancHtKDe0NFJ7LT0qKFugULga+T3RFhWx+dHEt29oEKNQ0NnYoP55i/UQ9nbWegSvP1n+Z3CWcTan6lHt48NTJs5YWv'
        b'Shd03L4WNynYvPfJiKL3br3PxKp+M95uybSM/3FYQMiCBdN2/enN8yffHrLjQPTZ9jHG4Wm3P3418JUxL43MOzAxYOv66be23gveNXHloR/fnIYPuN67nXvsF3/d9+D9'
        b'C5M+KMt6/zefPz9kaUnxtj1/G5X4yik2mj96/n/nX/rb3Tv/qfnHxpJ/tX50ZXrc6J8lZC27NP3EoftrWifffT1Wq6YkM6sIHekOjYaduIPTDXhMcNtrRW2Z6N6MXM9A'
        b'SJmQBZK6OrTXTr9GAnwS7/DHFWB8WylneCIFnRWc8NsT4+n2koL4U+ymkXWWoFbhLMJdvDmlN3mfsIgQePRsXabAbu/jzuUCd8tEp2n8ndJ51A0f3cI78dEEIUgEbq8k'
        b'cSKCQJwDNrZ9GWUuyfgW/RJEWxJ0E5+fT0PwmNF1OgJyi9nNGoegc4Q7Xn4MejiMMqXna3syR0a3mLJGdHS0nXxlArXGob1UFM2GltPBQDtxu3tAOHwVdbCGJCU6GYuO'
        b'CI4FbcANLybQ3RAZI1+OD6P73NBGvFsYjVNoP97t2StBT+MzXu4NF9EdKtkM4eeOwqcSEvNBBBUDeYegXRJr6jp/R7v7y8oUom5AmVeKN/OaKrAtuXCwgI0SGRSJRKGm'
        b'GxuCi4KabVKLHEKsytcXzeLLp/qISsEJz3b7ImyGJLEXd3rXO55QT9g+mjahL1TTJvI70bThl1jDBvGsnYNrSQsbBQ/wnE/OHejhATfa/EA6Wp8C3Ii2zKUyNFgMoiZs'
        b'c0mMlTaqqfvXyl2hBs8etWBaLODcJ5s5GDauKdptKenxnI/9z7M5TD4y0kbD67dw1sxmlvaGWSGxzia9ssY3s8dIL5jj7Dq2Icou4dlmmidPVksEqyBcS0mIfmpp4Aoe'
        b'jPUwzHqzDZpQVUtZzWig9MTgRHVicgGzRgcgwlzfWGeuMtsNwnDbzJYGOkuugNK1jYKZSRgSwabkklG+7FIKBlqL9SGuuWpDo9UE/MpkoM+XcW4HSBKsCnBOzUlpbISm'
        b'Ae4h83m+16TTASNIwxODJgwCMWkuZ6u5KGFyoevhQk1xpHuJQiehcd02MGFOe32ogJzEAdBWg6GCEz9TwHjbvIR7/rEwnDbIjYdiY2pJYxQEy2DY/bSgJ1YpDOSAOoDw'
        b'Aq/2gPfcov/IX6kbegxdA8cAH3j2OLeODkgzu4Jx4wI7HaBvZ0RDIFxT6Fv9NEFuMNTZDYZqTuTaDMxRU7CnDeTe92oC6x4GbvqM79MGk8Gw/GFtMPVogwcr9N7LaIR7'
        b'gazgLBqhNUAguBKBWNAr8biI17x4teoh6AyNM600GBo40aIooLFPA8l9nwZ6rIIqOkgEuMq9ier2au9rNBqgx3YvnOgG1dBzLB41H1L3fLAzv8d01MC0r37IdNR8X5SQ'
        b'uZcpN/P7oARoJYbHH9YGU4916XFMJyPuJhPdhl8vyu6XChDjmMGwwS8VEO55euwj547y2+NosqfDUIrNtQhoRyYgAQipp/Nu43z3CDT4bRyQCCPPGwxPePgNjESgN5mg'
        b't3utDy/0I8077jUYxx8x9oQq0kqd/qmiL8B+jEeM//HQ/cDxsDkqDYaOh44Hve1/PNS0eUHdI1Ld/xGh1W7zPyK+ICWMF4ki1hcPiVLbGUqOIB/Zc0yE3QKXusBizwbG'
        b'bCJnhkx8X2PzkJMxBkO9AxB2pzfBkvoOEX2gXygjuH1Yz/RjgGil+/0PkC9AH5SZ7j1Amt7IM9gzZIN7DJkY9IagUlI/UMn/cAUBpbU6TLx5lcFwiHMfJqI0PpCDQQv3'
        b'dMLz2A/rxyBPPwb564dAIJN+eEdUwMTrLBYrbeLTfnoS4elJ93M/rCtRnq5E+euKwG5G/+CeKGhUHoPhvJ9OeOGwxZsKSb3bX8T4igXd7beTHpDddGhr9/VSbh23TiL2'
        b'Q9JCeiQRrqrdfSJSlUsOYwZgQYOgHXvWt3fS7t65ZKtrLXUm4iBcbzQ38KaHycqBBoNQp8FAvgEhxCMXBAwulKzZME9/3c/5l4+JOCqwvSA6Nd0kpT9yMI1nVmMwPO9X'
        b'DqW3HgU2sBts9fcA22ixGQwv+AVLb/kHG0nB2gWQrIeE1gobru2+89IHdFD6DAbkFzq91S8Ro7UfIoaCbKCD3PSKX1j0Vr9gVfcDVgBd4Eao8nUvaKHeq5/ctDqYHqZe'
        b'n/VPVswKxhpqB42a+qCwvISXEr4VDU1ZR1YK0VG5Nu64sHbEFUPRTlbwKan0wQi6/2xuqNE0WlYLO9jjkgUfDkdjo4WE3nnAJetd7DhYPU3uaXMpVzqMDXZzk8l7YbkU'
        b'UFON2Q66umlNo1sxfagpBEaBAjcYftJNRpQ0UKfaezTEh4RxJUOiTerhhGh9TKzPVmexkwhea0he7Ws6h3x1tanKbl4lhGsGclxntNkNgpHYJTU4rHXWNlIb+TaQlzuj'
        b'B09dSo8xIohaZYVdX2rVp2q5tYMklPKQ785ad5OEfAvPup8kJEqz9SBJDpPkKZIcJQkRbqwnSHKSJKdIQvi59SxJniHJBZKQuKHWqyQhH7CxXifJDZLcJMktkrzgHmNt'
        b'+P8/7pE9HFQqIXmTFYOOKhVSVspJWa8foJGRA3p5REo4VhMHv8NVCnWQSqKUKKVKqVou/FVJVDIl/SUlaiX9CYBS8Yd+/Bi1ohdwa/pEG96CuwRfSWUM55iQ7eMoKRX/'
        b'2t7r4SjpDkZaLaVhUZU0rBoNi0qCq4lh1WgIVD6A5hU0zJqMhllTiGHVVDQfTPMBNMyajIZZU4hh1UJpPozmg2iYNRkNs6YQw6pF0vwAmg+mYdZkNMyagrpdyvgYmh9I'
        b'8ySU2iCaH0zzoZCPpfkhNE9Cpw2l+WE0T0KnaWh+OM1H0NBqMhpajeQjaWg1GQ2tRvIDID+G5sfSfBTk42heS/PRNJCajAZSI/kYyCfSvI7mB0JeT/NJND8I8sk0P47m'
        b'B0M+heZTaT4W8uNpfgLND4H8RJqfRPOCiyZxuCQumsTVkinXUCdLpnw4da9kykfwsylLSXOFkPM1pd2nUz+43HM3y32g0+shMcZbj8eI4wf1QqkyNhAyWGkSfevsZrqX'
        b'5PYVoXHE3F53xF1E2LQx+W4viZtavu4hRDvzOkpbQYiuUTgixFuqHESt8NTsU5vF6q7QbBcMfMKr7j2iuWn5peliDRUPcQn0yWRXi74uRk0lNUdCdcLWnvdR30QBpLuv'
        b'osun3WoiA+JTn9FGPUxJ46gHyiqoyVhXp3EQAatuLWEzPmeIfV72sFeiMxLiQvYHbNUs4XTWUMLtBjJt3IoAa4yb49mpDfY4u07CA3czCKmUpjKaymmqoKmSpgE0DQS5'
        b'k/wNojkVTYNpquYlkIbQ61CahtE0nKYRNI2k6QCaRtE0mqYxNB1I00E0HUzTWJoOoelQmg4DPi0xaHgW0uG0ZMSa2mbu2MjjTDrz2FKQdqXrZM3SY7BCj7PbWRtQmmZp'
        b'NLNO2jCIlspJqXUMrwCOPrpZSmyb66T2McDhpS0cPD/TPpZXNksFK7Q9jpQ3y1okLLPybwuZNujhcnUbS5+ssGufgFZQISmgwHqbyAQThAXQa7n0vSAoU8h0sQYXZzA8'
        b'kBlG20bbHozuWUmtkfhndbt4CabgeJeqGJi9uV50nZQLu5xCjE+Jwcy7ZAaHyW4lUWSEkxGuECHut+c8nHUGYUezSTKHJCR0gBBjpYAKA75HJ0HcE7azocZGhxUEWROA'
        b'oIKAgu4K2I0uuaHeVkNBryBHCmUGk/CHHjAMdr9Gv1kFL1XVkq1YGlTWaHfYQBqxmojJ3lhHgiA1VFugxXRczdXmKuo8DQKIQDM8t4319u4OuSINdZYqY53vQX4SyreW'
        b'bCDboH10zUI19K8Q4tcVa+gx5CC8wnoUn5XBdb3NFQiNtNptxCWcilIuBcwLmROXOs09M8JMKGwmu3jDZjNZSYX0hlYuuDUQ84VLvmI1+Ti3VzCEBubRoRjo7H5ERL9y'
        b'KvqFUseNngG0lL1KHvLDCX/DqbGJ7JMREzCJ3d4U3WNE+h09WZTlyefk+nAFjQKlR3CVjekJyOMzO72Uukc0rOg+wJkoBFewW8SDrsR9kQfCba5eC+TYi0z224VWbO6M'
        b'vps70N3cB2N842sRb4J6i737fC2N59n/GFOz+4Yb64HrG1irN1gSQLS/gbXoYu8D6jDf3nqH1eoBVgzW2V+4j4ioNcIDV+snotYPBN3ar6hNoz2gf5OmEWK42hyV4iEQ'
        b'6h5P4Ik+PWIApz7bRYUnoSK6YUpknUZ4jcgpNNiNn5BQek1Jd1m12UQAioID1A4PdHv8eHiBTRMvjlN8Ilya7fSvO/hWPN0ejRdiYMX3e7AK+h6sRM9gje8d/eQh+Jk2'
        b'Z2FaEiQZ/Q+09U7frUjytGK6zwl8EmbEVOl7Fr9na+YWZ6QnpWfMKe3/mvll361J8bSmmM68F/sWfcDcDv89nJP0mnQaDUVwxapbbVxrE4+jaxpMNUaievebmrzbdxsn'
        b'etoY70Zyt3uVV3NFHq2JK1mwsLz/4/OrvmFP8cAeS8m6xbKCSLbCgXoQeBsbLeSQFYhGDuEIfr/R5L2+AU/3AA4p9Zya6R8AsWe/7hvALF+qVQ/r1Fhj8kK+xtq1NuJc'
        b'pylKyy6AdV3Xf9CuvkHP8R3UbpB1lhpfiJq43OKMzP7P5m/6BpzhASw4FTbwOrtFB3+6WbUmLqN/EEXc/W3fELM8EIf4De2gicv/XuB+1ze4XA+44YLXJIiDDeRsibg4'
        b'hAAbRWXFRf0O52H9n75BFnhAhlN6RmVj8ZBMv7v1Qd8w5ndTgJ5UisjTxMWHXMfNKSzMzS6YV5qx6HtQyA/7hl3qgf33nrB9ZXy9JhMowjwTtKaByn82j8LtL7o6EKqF'
        b'2ZmlJEZ6ombegrmJmqLi7Py0gsLStEQN6UFuxmJtInUayiSoUivW+bDa0gvzYdUI1WWm5WfnLRauS8rmeGdLi9MKStLmlmYX0mcBAjUCrDbbiNtsY52RRLESwn70d/I+'
        b'6nsAyz0DOMKLfAvqkICQRroAjTYYw/4i5e/7hvmYB+bEnpMm6Gx6TVr3gbbsgsxCGP70gnmEphMk6nff3++7HRWedkSXUn4uqIkweTzBGkv/BcE/9Q2oqpuai6FY6NlI'
        b'AYyp2+jjrWv0t49/6Bt0tS+J6yZtxHtcQ+xUPZgHed2zu7FABGcroL52MXQXkPpwNcaSa+HcLNnNgF9pC6QG8ryM+ubJyJsGmh6TQ6o4zrJe4/ZgWrHgXU0sVR75RRCm'
        b'um1m/oUtvVZp/QXpIgkI0DNgM7U1kEgG1gqmeyt+CuNvAyiIfLdMrNQsEd0eGNBgY6jfHfH4bBrcU5n0esf/LBG7Ge92NiwVdgH8TxHZdbBJureeeimuHp8avycpY8T5'
        b'sarJzu1xhuzU1gjbX+KGJtlcckmJ4eEhfnVK0SxhWCXxeInQ0xh+miI86L/PkV5NEeLr8qy4V0+NWe62yOi4PdzJr87UYDA83qMtfgwH9LkC7Uh/O1DUoEH3jFzqHsap'
        b'KR6s6UYYgxtXXMG+tim5aJpSiByafpjWJRfNUjLBKiWlRikpsUnRSCMulY9BSi7ao6TUtqTuYXkK8jY8yUWLlbLbYCUYi9S+BilrECuijpV8JcpKP7hEkaw/odisr0Hy'
        b'S2LtIRtdSpWUC0/pR+wMWe9oGt8z+kbvVNp3tA5VoFKilDlIxBJ03qoLWhXcqNLm4C0JBXl6vBmdJ57s5Lv38bUydDkQH+oVW5H8o/EDuneceK6VoZ/ek/BSz6f3ZOK1'
        b'nH6GT7hW8ApeCc8qnVw1K3xyrzxACMhRHkgj1HIkMAeUBtEnQvhQuFY5JXAdxofDdTAfQddhpCuiB/rmmUGTdm+JSb0XNDnkSAiqgTpYGFiyVWzgakg4AgnvEYukVIZ3'
        b'BXi+eAuX9RbeWEc+jDaip92RQDN473PY3P4XUSzdS3VXonTX0ZNKkS3YVonHR0r8UlusHzj9P/3e2i9lpMNj0vMLrd9fRBOlyRFsn9A63dD6y3xH9l3fFr/1eSabOCy4'
        b'HTO6KbaKrOZRD6+YLPmtXizjYdPQm1Y/wlPCC2YvRklpzA4vqD2ZogiVUuVHMMXq/jDF3Y/uocgYvQ8NeLxeiLHJ7dZkC7cDYPEYAHXLWiGxjYdr6sJEr8mVdIXEOt0u'
        b'Eza0IC8/piCOfazXwQidt6haT0IEVHbHXBjbo5VjfR/nLSbhQLxw3IAGgXGfxKNUHkSaLveiFL6APppcjSEJ9fcg8wMsqbERVGL3OYMgLxD00Yc4T0mMPL/PI9+I4bhU'
        b'9G8v5kqHF573jzuBIu54XIa9Z7I33pBPDB7zmsuB/oD1FqV6uC8JdLuZSWdaWBFlJQU+IqvHKZOcfiD08jEVOfBBJJEd3Eri2V3j9iYn38Nz+9SRD8O5WHuvNQbJSXer'
        b'5UyTzl+r7Ra7sQ5IENkbss2EC0LVLfWNM/scEZeMvvf0o8aEPlWgVfeUb7rdYSiidONItyhAJYMEVhx9q84jHjxqH2g4PLlJIo468F658Jk9pYR4hhDPD/pZXDXeuJbw'
        b'YnxrQDc7pqyYRGJM1LNMOr6oyMNP4+s+HDlK/Gt7kvXhyDC39EdyWFYuIb4fxPODfFSPDyT8Fq6AzxL+eji4nHwCVwacV+CwMnrANswZ7hxYLRMCXQEPV/AD+Cjxk7kK'
        b'Pppck6BW1DdEwQ+i+cE0Hwj5WJofQvNBkB9K88NoXgV5Dc0Pp/lgyI+g+ZE0r4b8KJofTfMh0BoltI4EvlKWh5oU1YwptIXZypaHwp1wuENCYSnLw6APLA2HpSwPp9dC'
        b'OKwIfrIYwIsEEen+7KDaGeIMpf2McEY6BzijnNHOmOoBfBKf3BpQHrlbsTuKH9fF8lMIFBgLCZ/Kj6dBxAaQT/TxE+DeVAqHBNAi5VF8CuU401wqgnxuXwUXW+RiC7Uy'
        b'FzdvjovLznBxGSXwt9TFzc1ySdJzc12SeXOKXJLsErjKKoZkblamS1JQCFdFeQUuSXEhJCUZ5EZ5rtVMSc+87CJtsItLz7WOIxSMy4Yqs4pdXF62iysodHFFeS6uGP6W'
        b'ZFgn0AfmlsMDZdCGbM8Sd4czp54I4ncChDBcUk8wc+lDg5kz/r742Tv4trTAkcPQOPcb8SGC4XbcXqjHXfkkfGh30FAarxM9hZ7QZ9MTiXmJ2fnzswDzc8ihTvL9z5n4'
        b'iRB0fVileenhx2Q2skH13uw5n1X8ueL1j9N/FRceZ8wy1lXXVSYal774zkvXt4+j4fhrB8v/3nhJKxHiPp9AHXhPECRb0LnELHcgyTB8R4IuopNqetB0UjA6gMlHqXIW'
        b'hufryRfBD3FrhmXSA61SfLui14eFZ8zCzkGT+kcLRoqEVQh4tMHnZzpxDmyK9MYc38/1yrr3pK2fk8T/lyQkwhOjPI95IN8kVIhEC/GcfhR+3vCJzu+3BVVKcYIJON/w'
        b'wkqvj1+TtSWE6ukOL6xsCwAcCgAcUlIcCqA4pFwf4A+HpIy/L9vFFtDPOeAL+GZDLgkgmCTEntXp9CTaLI3USma0rGg1as1CZ8nnPTbhrY1BeDveNZ1GrQ1Cl/HB7ncB'
        b'swp1C8QT2Tm4C0jtttywlIVxuH2hEpBUyqDn0LNBwfjUVHoq/JtVcuj2J3Pkmoq6D2cvZ2hgdxW+iS/hPfgkPRounAuXFdHnx+YpmVBmf4y6oiKvSxPO0AAyo+c34du4'
        b'xTeEvM8ZcQWzuESxds5sGiYW7cJP4k25+Nbq7PzcRNylZZmgAg6ffny6YwQZjV344LKELHKYHO9KTU5GrRW5DH4SPTcC3ZCg+/jqBAf5Qizg6WHUmlBAjlh35aMzaWVe'
        b'h9Hj9Lo43JYUT75/YdEq8bWMdNqz9Cp0tKEsF3dm5yXJGXk0p8Z70WmKhjQWjcmUj3ehYwlk0HXwALrDTcTP4zsOghH4JrqO9yYIE+IP1nx8b1IcjZheFCe0C23OkjBD'
        b'0eZg8nUM3E4/QYte0OFt09BztlX4qpRh0QEGb0N3ptO4+ZH4YJj3Jw4bV8WSHpfGwUx2Jibmlwnx74Vj+O5JZxl8UqIin5pHHQ5y7rtiOPnmixAovgHmsiMP+hIxT4KP'
        b'oHvzHeT7H0tq16EdVe7BKyvSdYfn9+oOAcOhDg6IHHohaMIMdNFB8HeKHSjJrvkM0ziQaWLy0U503UFI7bgifBaY+pXVq/B11I6uoK7V+KpdzgQP5tABw2M0IDI6FY2u'
        b'26B4AfkmQFyODuYfSCEFVRzX3R45g1tHA6LcDmRwS5hjgoA229GdBDIS5Mx6EnoaPYu3lcTFAblrSyooc38agGAb2ojOBTCpaJeDkAt5EogXXbgjCMYCgN9aCS2zqlbi'
        b'mwwTnSpBrdD3/XTgsNOIT+JO8pESnb4oF0ZYxoSjPRJ0yYKED0F+vEbGKJlPJqhmV9R9PnUGI4Qg2ok2o322lTIGHcqD2WRQB1trXrprJGerAJ6Ue2Nd2fzcApwc+s/3'
        b'Gj48qfvfDWiY+sWwyWkLL585FKbrai0Kv5IzKfLkp5fmXf46tr3qK2bL29vecf31p9de+/J/Dm3TajRXdq69FapM+Ibjggr+8PXm9MWvTN1wsvb4hTGL3ik69mBH++y/'
        b'/qG8JKtJtii37L/pLvmFx42PzW6Ki7/4o0kn559JSXhv5MvJYcOO1u5F885sPVUx79qGSeq9RXP++5OGsANHlgQsqNriGLtvZ+WKw4tei9y3sSv9pPFfr/12zCv8sj8e'
        b'v9P1+RtpN/84deX9PzZ/9snbHwc+Uzr49aEFd4rMn/x+/2+Gtzy2JGlPS8vIf+UckB8+evn0lU3N6Pn/Hp/1jwZbcca1f+y3Ncxe/mzs3/b8vvRWTUFi+f0NHaf/+jVz'
        b'/pr0VXVhak7zb/+YfcK8bc3It9e/ElM6+beffjvxw8e6ts6s+seD1uVb/jRqYFLjG2uyO77o2FDz2t31X65J/XLNZ2P/NGT0z1b8vWh6Z+2/QibFdxxpztGOEKId7FOg'
        b'c0ECA8ye4M0CV+PT9AMK0+eiW7gzGp/0fJcwCD3L4VP4AD4jfPzgLKDYtv/H3neARXWta+89M9Shg1hQxM7QsaAixIIoHWl2BaSJImWGInaQjhQRVEBURBEQERFQQCR+'
        b'K+UkMSY5yUmMiek9xhRTTftXmRmKA5qcc+9zn/85McI4e++11l71q+87GI55nowCDGyCs7SWHYucoTBNTxeORGlLUYcMdSbrqnMmScIgVBCYbEgm0aVp20cLCJAPhfFZ'
        b'o8Ogmq9uxxON0S5wywn3AmFd2LGQNgwOo/YgVLgWOmyw4CBBebRpLQJUtzSY4URnoKMoGwr1U1FnIupI0aVQEkfFowWboRSVUbgGEzzJTybo9mNWCGwN4QAt3xe1rLK2'
        b'8xxA6LB1PaF0QF2QSTEkUC3sR8egbJs3YYMUpPMuWqiFYjKIcNUE0KsAbw+45dvni+bzcHEU1FNcpR2Qg+rHj/WmVJeEXcpzA8V+QMe2bJGl6iSloMv6UAAH9DV1tVGr'
        b'firZEjrTknDz4Swq9BWpQ9eevbQeK8hGZyPhjLUtKvLBop/6Gh41wwHoZRgXOegcHPBzQIUecB6LGrv5Ze5bqOwTAGfDCRdFITRD1RIPX8AHnh2BLh8HHaI0y/W0cD+H'
        b'BVC4VtefAKnjzd8HyzeLBOiwXyDtnXCUT8Es2LKni95aauoj0kUlS6joFIBfoQ5alwHedPD0UuPUwwSTXTSp6OQcNxcKg6DbXr53qXFifwGqIAJZMtl7UB8+dfF7MJYv'
        b'f3Ie40rwEanOTURnROjSLnwjGWK4CnX4IBjImolfqZLygUnRZdqQNVCtOxVlUuStIh/cSZ6C0Quhj+KVQ9kOwspBikf7dOz8fPwp+ynPjUPHREmoGlWyVdI8F3IIcafy'
        b'8MACRJFekNAXXZ7F0E06hGgfFEpQpb+dLRYnvIV4LhYI0NkljnQmQ+lUdyj1wGV42Xhi2YDTnCfY5I3XARHFDE1Qm+IK5MlZTD3xfNwLGVaWaihj+gq60hJGa03FEmeh'
        b'v58N5NvLt3A13CWX1dQCGDma3/ggQiOC5QjXzXKQFSNoEaLCRbbJ5Cjxc8WLxpasiUGyN+6EEvvBmqY1nm5FU7ThxFq4mExS29GRsaQTHnoyBrrxw9CI8nwk6pwPpwFt'
        b'biiPrcAcL3yiFZJhhnx/xsemzs1INcUiWZ9sGAn5PwWhTvV4Kl/HPyxfL9bmNQmZqUDEjyEwo/i3KT9GoMOLmD5O4ikFBhTFehwB0BIY0Rw4HYG2EMvHAvUB0ZvEg6U+'
        b'4F/UcjtqiNzMTLZMdNeWZxApwntFxLglJf0lJcSkt8UR4cnKSF11WcTmqG1RfwHrRFNKGKVoUVI/8oM+Sov3J/+k9kBffmAv9QyjCzw7CKld9Ts9LjOLRih7k5EQT5Wm'
        b'6MFVPbYNWm5mXTGyzfgPpcPWkhKHKPIQWPss5OAjQ4hX/wqy621xqDycKHREMhpepGiIjaoQpFhZf9v+Bg8rdd+OULtIWbs5ZaMnRra/x/sarRjhiJTkhOjoEerUUNZJ'
        b'yUbx/bb4AQsSDd8fA0XaQeOH/85LPyJOQFvZACsaJxAbLQ8M2EYCMXCPR8WTdI7Iv0MxelsndMDKHaERuspG0CglEqEQQ7DYlCF8f+O9HwEmbKCscsbwYMKDK5bXS7fQ'
        b'waymzDXHFHqOpJfs5rFCz1GFnqcKPbeHX61IVR6g0CvMyENR2VQzqNrQuqL5x+dPfZ+QPajEix3EzzM40kFmIduckBIXSalUo6QUy9siPCacxEeoLEtJcuQWFxVOIoUs'
        b'ltK8EDKEciBaGl4nh+WWx9nEqgaylSN2h4UFS1OiwsIY0evQ1Uig5eVucwrep7IkFnmVPjCgaRD4eFjYsvA4GamDxGriL1jIkepmJZB1EUFyHSItiMU9PDl2UyxxXNpZ'
        b'hCSSh1Pn2s2z207barU1IT45IYIQ1VqpLCwRl0Q2trRw2SCwYkV6DcEefhjLj/w3yJzIPzRzhH6x9dOXqsmItGsZVPxl2D82fW6vGf1eHM9p1vOvRuK1wWx9pXBSWymH'
        b'6MYoJBEqh6CCvQp3whA/gig6Joqhl1Huyr1D/kzZMXXQMSWLiAulvdDvsSAFDEf4yiswM/tRyQhDuIlI7qQechbv4+7pDDiNUzw4ojE8AZlDzKjooPVAcQsdBkLelO9P'
        b'dCToRIe8scRcShUt1Iou6zpAGSpSjbFJDEbMCBwtfAyqWIUP7xEUrXjMpmTcEciIXJ3t7/Tl7umMSTXsQIxHOB67Gxw3+YrwrAzw2BGhJQL1biNDp80NEiLZ0F3dqujc'
        b'YVOvRdGykQZx+mMMIi5AYdHth7NXbW8VDLiDDukGPKQThx3SDw0GDukyMlVPoavQ/lfHFKuiF6z9yJheNNN1cdWSCKjlDpo3+XqTsZ6EijiRPo/1x3yoTCH2ZitUNc2b'
        b'PDJDnRPN4uGSEPXGWs/XV6O2/zd0Xtoa4xHhE+4TvuX9hqjNMZtjfCK8wv3C+e/GbB2zZUzQ6k8d1GaF/ZxYL+Raj2m+Hr9d4fob2BWqhkNL2cF0TExVjck4HbGeYIep'
        b'6nFRVKSy/wecehtxxxsP2/FfD+JQHqaq/wCxt0q/iMpFse3AUqGM6N3X5t35Ei+JG1sCN22O1qGbmYme4D2zH/GCIGbIVFQya2QFDlrwpBisxC1F1Q+N0JDYg+HXiPVD'
        b'bgAahDDMvjYckTWpY+qwA/KO3khuh8FBD39XSlC5Qz18qoj8gmP5oCaRjHz9oUWadzgeBR8NTmR/zpKX+H/SL1897Iw/wY3UkXYP6VAswuLxTwhS/oxhO/EtnZH0tSFh'
        b'jv/RXnxYqsNTuuTIlyK6zz95V9c6/LOKeHw+r3+yvbS2kvnjpjwQ3s96VsIA0FGJM97VCm0898y1FVC++A67DcmUYzAfb4onVEx5AVQNb7aAXlRA7VgzVsE1Bo9qq85p'
        b'oh4BNEAGHNy9c5gh1B1xLTg+rAbTMKDHH0JSvtWwQ3hrxCGU10V6e5ATbryi+zdx1AlHHNs61BWncG0Lcg2pU26QgztXLXcsddCNyzXLHR89XumkEz++k44Ecpg8NPo2'
        b'foz2oEzXTeE4ggroI84jqIQm5jyywD9mai0VS1EH6tBHfdCRpHB/GMBpAeo2hbIUYp+IQj2QRR0gHugAnJsr8YfmRzhCcraLoYMclRJ12hJogiOjZMR7waFaLDmUcnAA'
        b'jkIvOyev7BiNLqWoUzz5JnSCg4NQZcz4mquMUbEYdeKh27wAdXBQC1dRHz1C0Vk4DVdkyXg8n4hFeRzkjPGiF5zQaegVk86YjC6iCxwclabRC3vQGVQlI1CGqHQtKuOg'
        b'IGI99ZBkL9QgjlSDUr0tNj5BSRz1eXnCoVTiGhIR/mEsrNVRk3co69iDcHCW8nUq6evgWmupv8gpBrXR3hrSQ6g1WYragzysiWEadxNqjVcnsvFRrd1QMIF6ZRKcUPMs'
        b'VDrLQcTxuB+Wr0P7UvakkAAZZ2hah8WMnEEOSwUiScCKVahilleQBheCjqqjDlxoZQqx66vDkQWz/IEAwzhyjtC2jDrDoDoCv8ohqIF8PJXtOfuI3XE///nnn33hIsLU'
        b'YbFPIyzu59XmXMpScnMxZOz0ZjU1OjJfrwelxi6y9wqxpODIQZYSVLLKw5MIRwd8qVQUSKaBerzuBtSNcqifEAuS20h8AeqC2oH3kklFxCl7f3k/DfTDkrl0Dnp0UJv6'
        b'npRwXMpUaEMNuvj+g7qwz0FTDe0LQcfVUXGw7jKjcZougdCDd57j6IJ7zHat6NFJ2uiqehoe9nOaUKDlrwOteIaddkC9OyUTUd4CO1SFe8hNApeemI0qx8DRaNSUQkKc'
        b'0ZX5cFENZaAMXc5RUwitIdC2FlWoQz7KhQoryEK9qASKg81i90AD2mcGx1AD9G6ZbAaX8bzOhs7onShL6GiJW1I0EV1cauyLv7xINw464eYKzPjZAk7zycT0CfvXbeVS'
        b'SNT2Zg0sNwwkXo2Gejn3ar/DUEG/ynPQgi6LI9AhlEWL7E0lXK6cg4Mgzute+mouhQCfbYBTq8lrVGpxFjr4w8qNW6EMmvGY1PKOcBHaIROdWTALD8qhMLxem1FVyAxU'
        b'txY3e9+oYMiMgrwYdBJd0dgMVw3SZ6AL1KmpZiZUxQ/rYeulZjSKxIdAowT/Txg3jriic1roMhx2DpbwlOBEH2oJxWshPjmwSN1g42mDtw08yqM1RQ5LRHS7wcN1PtV7'
        b'BBZZMvOPwpFBNLIFEp1YDmroWgkxXdXvch3B3VojIB7XxbAft43sDwlxiZDlQ2R9nhNAMe+GDk1JIbSRblgpOGTtgTvugC9bAfZenraBLM5B7lFHjXBksBs6MJFsAisC'
        b'bVcKOCgcq4/OQNn6FH+ypo4QyhlxKuqkZLh4Kay0xI0ttrH08MWjUgndgaTUVYlsz8UvUeTNQ5m7Nhz3g+I92tCEsrl56JoufsdudJqOP79OQPVHg8Qon8+2auNDj6IX'
        b'oY4Z0OmtcIpoOqBM1CqAPFEwbYgDFEwO8pf4Mpj2kFUqwjjw+Y+aYB8e1zJ0YL0FnIMrcNpjEvR5TJo1EarhgohDbSjDCCq1/alLPWBhEN42L+lraaI2fSvcZ5eSk1Kw'
        b'EC0T+uNBqWTHQcnc0CCyZQnxPtfMQbkUNUMtOk/5eOAC3nM6rFO8Jba4F/J9/HDLLAeLGUJug4UmZOKmnKLhGcu8oSYIioJREaHbUdNDV614qEL74CrdVrdNQrVjIVec'
        b'qsfj+g7jLSUYHaKbPGp9Ahpxc9tl6JIGJ0Dn+bXrbUMnSAxTiPhhELoWFfrgZ7Tmz8P6rxBKGKVwh/cWRfhKEpRZ85x4rQC1pKJzrMv3zYb9Crcp8ZmiduiA6tA4OslG'
        b'yfSC4Vy/9xGdggzaJ3ugHA8OdeSrcSJzHpo1sODVGEw5hUzxtpKliI/AY3EEmkScjoFwFMqeyvIHcvC35/C0x1fReR1cCIGwZw5CNW467FOLFoxLMaN9D5VPeA8Asxq7'
        b'Dh0VQMUm1E67xGHtXmu2YPC25qfG6cQI9YNQOW3jfHQOFShZafCUz4ETRGFm3XIKb9W1qNDWj/rwoAAVqW8QjIIOb3bK56KqZaiQOjpFTvzKNGhMRSfYpSw46+HN2JvN'
        b'eXQNjkPdPH0mAOSMslYSO/Oo1h5PwBrPlElE3NlpI2+oH56/eAJVkOWtxk2CQ2paWI44QtmltqMriXiZEG29by4WX/LtWR8N7iA/yNBApTMhl86X2Ag94nqW4H0J717B'
        b'8wVwJmlq7KiwU5zsDJYeZh52cQ96rvjVRQZfxX9dXBPZNr9yd8z8ycX31Y6VLtpk+Ow/Nd8smyOVLrbyNswJ+NhA8sFTGft3v282z+Ia/2KG/nvCn/fND7jz3L5Tfmm9'
        b'O37YmJZS/UxjwzSPFUVWam82Vt28vuRg19OoUs2pKGjnVKtfNmYGeRUfe02Nv7d8juGZTX/8+Y8l2SujR8natl4wVDuZXZbyScOTLwQ7uol/O/DDmrmLtp730tPStK7M'
        b'/2DWh7ZSp5+zjr12IXLCotf+8c+cMdte73bv0ZsUP7X9zVdqzZ0rRHMvFYauv7P4V785UWdmzxzlN2Fr0QeHx26oeTOx07J22xehTV7nI5MWu3odOPz0K5Nkl3Ws0+u8'
        b'0g6W5sZPWyV9cGyWa81zz370hXb0wjOnk2v7PKRmD84Uxk+Yeyp+7qnInI2y3d6y9I09OjOrv2xZs3Xz+h1rJyxT/x02b3o5r86sJe+Pj68lxV+9eXGTyPjWRqtLH5rd'
        b'vHvU58YrEwtiam68av1MmuSdY+nHUlc1ebwxt33jmabvX17X+PmHaRu+eG3dA7+uD98RHyyJc/wyatJ9c8/avReWtmzUftFuY9CMr+qeLRDeWmfV4v9m7MTejqB3zix2'
        b'zRKedzIqKs9s15O+4faF9NmQb/Nvj+vpznFbOfb6K4G2sCtsjDH62WvKB5cvauqajrm7IDsFJvRGPBhX88exoirp+7eOJeZ2TL9d0XO2ZQ/SOvbFXHettFu2u7+f31fT'
        b'ZX2uNb0vprrlbqLLy7KxH/WYFWn9+fXKspy7VzQ+LWq+O9Ph094jkk8W8gE5Hy3aaWHqd+/Sp3t2PJk3tXBD3CWNe3YlbubLXYqfW/yVy/I9o480J/2QEfPc2TFnZ4xZ'
        b'kTXp6U/MFuT8+k3Ym9brxte8biS8dlCzrmLO74sLKifpWntP+WFs5+ZblhKHf67Xsct6Inx38bV7zp3H89/7KvTbBqOb54olM2igQACqtSGxBiyKALWMVwQSwL5AGg6B'
        b'RaLzCeEBytgP1Lecfm8xwykgsn+bwkfOAeaMr9gLF1m4iaYybJPxWZxaxygx9kNrrLUytkATtVpChyB1eiSLG7k2G44ods9NKE+xe6J61MAer7aFjIHb51w4D9WozZBW'
        b'b2iJG1zIwg2gG870B8Q0QyPTZLOgd5SCkMN4vfoWgblGPA1FgCMLNayt7CSoAOvbWmoBa/C6XoOfIrWaoSYTa0L3lm+Dt652dEgdigW2MuiijUZVOqjBG86j5iH0KXB1'
        b'L+XUggsIH4sklIGINv5MukWXNxMBV52b6C1Cx+GwOYsLad4xylreiJRR6tAsmJXkTa+MwxrRUXksTMx4Gg3jKEsmdmA7LGV2y7bbQpFmki7RLtoh/+H4FF/UoQ7X0Hmo'
        b'YTEilvMH2S3HO6pzRp5COIlKkijviC8UO+BxJzcUaKFGPNLiAAEqngjNNCBm70R8Hl0i0sdFrKagA7ZU3iMCkKdvknzgveGcBrRCqR81FictRde8WWUkbqTABx1DXeqc'
        b'IcoVwoHtT9BWbUdN3lA42s8eP29LCf80OH1/4Wbog1I6wujINNRu7W+DtSSs66C6ifgGMbomwGJkBYv22AmNXv0iDT52DlGZBuqgk0YVrUEHcSXKUyofC6InPAS0cLNo'
        b'PHn7A47d4ZAi4MocMhh1ffvsQGWwilSLhKukoRbaIXOgbJ5q0x8Nv0BZWxURGCFQST0f+mO05IE+JMrHCK4MDPQxgUs03MZ4EqocFH8SM14RgULDT7DcmE3HyyFC2xq6'
        b'Pe0kXtZK0rh9wgQLKGCRYFmomkgQvoSvzQZPkU7cAeJ4QtfWCfvpy61D3ev6T1MsCbRhdZ6ni0NTG9UNkD6molIsfZQY0sUxCu0PUggfcG61QvbwtafxMzZPhMrljiqs'
        b'DKsQPEw86OxYjLqfwK2ztfNDVXBOGetjinJERlGQk0zCiqNRjdFw1lV7dFWlqWkJOkOZ+qBkN1yMQxe8fTzxVhbIW6HLS1n0Tz2cMFfw0ZH9yIbw0aXHSnT/bXxSyfj/'
        b'QezTv/6j39CvPwT6kZrUCFrIQya1OcT0q0mZWAwo+48BobYTMEwzTTm6mSm+Tq4S0xjBTiP42yL8WSSnCNZjf3FJ5JMR/kTKMKLROAJaIkNMw6UIjXBpOjQ/i6CnEWZ6'
        b'PfqbxAPp4TtIFJC2gGTfsj/9GK8C3oT+W3GFZNgSFhkdeVkskU5psBvSBQPDf1iQDk2UMiY/RtPIn6jtyviBAXlH/ebEUf9rI6kIIzJSpkCRFkrDlI0yVsYSUasmIfC2'
        b'Hdaq+a8lA62aI3aShKdpV36qfZI0MYV4JXkKaPtorySDexS9/6ZARWTA4uhkQu0XHhdH4ToH0OTiRsWS1oTHDULxZGhPkZHMfx1uER+V9lChLJ7EMixsxbZkz/josDCL'
        b'TXEJEVsldnLEVUWsQYosKjoljjj80xNSLNLCGd9gZCyhCHyYwndgI2Lj6Y3RNFldntsYJWe9ZwB7FgQ2yCI2Uvb4bH4kx97ZwpNGDOD5J4slqKa4HhI9EG4RkSJLTtjG'
        b'ilW+mmdkWJiEILAMGyaB+0fRH+RjbDyJGyDs0EtwN6aRzkzeHJ6sbG1/JIbKEuXvRqFWacgQAU6hBRDg1UFdpEgdjZEmpCRS/LVhIhOkybERKXHhUhbRISdzZ9ABMgtL'
        b'krRtg7sAV0sRPdIT8T+jkiPsJHQQhonoIB2aHKUYF/m402iu+KG0jfLRj0ygiauJBKRXVZmDBmAE2kOeU0V7qO3HcihyYomrWJHGYQSHBXrLoY3Z4mkSyRk4HicmhjHV'
        b'If92zikE9EPfSWmatEDX9moKiQm0O8kBlY8z9zCelrQbXQiEbDjvBuXrlngmwzlUC62arn42E7A0VouOLYWeiTugycAB5UA1NR1di/GcfFNgwXNhYVamU+O4FEoI2I1a'
        b'Q6m6HkQoaktWoUZ8vufR5BwNbvIWEVb2W1EvI2/0VZvsyhlw3KIwHadpUi52w4tHBLJUfGU6XzPt+V7d/Q4m7u//erzol7EWbpEZs+P4UbovjsqOLXWrnF2bHheeMG5q'
        b'd53/s7M1zk4WZ6/9Xtyt/3rpjlcbPu9a8ODcb8Lc35765t6LHzdZ5Kwffczh9Ct2C7P+9cWrV+bq/NTlm/X521U7nir+QVzQNUW9/YWJOS5mNVOPS8RUINoxFwvlhVCD'
        b'Tg6NooZGqGbKQpcN1HtDiZFS/elCBdTPC23o2hOPH6nrvog4va6hq1TUMXS2kaEa1EWstbaWCpuVISoVQusodJTFLPetRxXW6Ix2v6ZE1CSogl7Gsli0AK70h5bHo0Ye'
        b'NUu0mJDaCxchGxXGTlTGlkPjLBa0fwjlOwwggSy2FdhiqfAErdPbIHVwpsCoOCOiukVj+ZCIcqgSFU4fILFicRVL/lVKkRVVclRkxf1Xroe1nWJDFWHTVGgNna1wvj0i'
        b'D++2Fklqo4uVyiiWqmSUvdxiIlcQeQPLHUIiixApZEjkgLKgwTyFpoMP8YcoFQXsjv7DdBP+ZzM5TC1UHab7uNeNho9eULaBRGTiMyYUHzLKDH5Fkmd/fA9L8RQqUzyF'
        b'w6Z4KmLsfhapOEmDouLlMJuDsb1TZOxkjaJ7G96I3Zd4ugUNwOse7jiK2hQbIQuNiIvFpTCCWQWAUTQBHIzYbEfvsHMnP93obcPBgA8oVd4fzjQe0EYZEEiAaWVRtJkJ'
        b'0kjyBd7oVW7EcljzYdtgtyzEJ4yClqUkxiWERyreXtEhqoPtpANi9sgZIQ+FlaXEJsvp7RWNUn08PLJVbm7BYTZ/99GQv/2o54q/++ji1Wv/dq1Ll/79R5f83UdXu8/8'
        b'+4/OCrMYRoh6jIdnh6mOnfSMZtwmTKSJirSxsJJPf6tBUaEqAk9VyyDDBKNaLJOGU4znR8Wdqm7mKiK1sl0hdZadw6DVQtEDGbYqW064wtTY8L/XU0uCQ1Q0oZ+Amuwx'
        b'rB1sucWqiEkdlJqs5E9VClrGjF+6bQ715q/+yC5Mx8gwhOU7LoQcyJOJie//JIcKoBcqvcZTD8NONehAlxwcHNQ4AT79qzw5dFyfOcq37UL11n52vIkfJ4DDvDfKX02/'
        b'N0ZXta39vAQ+O/H3mfw8VLeUVoKaUHGitZ8nDzmR+Eoe77IOMiUi6hXajC7j85Q4xlCbGidEl6B3HO+aANdYfnE+1EE1vtyajC7jAx1OOqEKfhIPBSxbsxXluctmSgWo'
        b'dz7HJ3BwGY6uph6ZBMhEtTLUqS8lzT8CTaiet0L1gSmEZdUEnUpEh4SjwqiXf5wj86g0G0KZPHahlCOOVDiwwkQiYIENlbqour+VUJWOG6kOV+jFyUHoYH8TtbxIC6EL'
        b'LlHxNhL1oCZFQwLRYdIOOGYrrxLLqwdI++ego6z9Xui8RMh8gTVQZNBfpRccwFVC4WjWL10LsQyjrBOV4rEiteaasn7pRL2cOFULzwEhlKGzWry9bRB13cHZ2T5iXak+'
        b'xwmtg2z4hTv92ft1QFEo8feJ9Xg8CLnomA6/MBa1payhpUGBnTeRcIMoCAJxH69CeRw6BWW7sEh9AGXBVSiHY8H4H+XoKjoNnZNRGRary+GqkRqq2KSmi3/4YsnsgIuF'
        b'MRYLjfShIQCOxp7IcOBl3+Mqzh+eFfKyq99TDgZq71UmOVXfTTCtf3nqVGcrv+u2/0zc94r20//Idr+Y7cYvmTlBbVr2q0maS919X+TnqY2yf860Rzrrj0/SbRZI3XSt'
        b'JQufm99h4v6c6R+TSwsqYvI/2HB62WurP6yJXm38YsqDw9OMu55zjp/f2vevyb6tLwkT1KYffLW97vWlXu6lYc6Nz+0uCfr95u5aq4DdP85Kjpb9WRA5tuvDKvXqul/1'
        b'qifcEvzIV5d8ck9jwwff2zdl/7k4oeuloLVfBb3htiXq4+zfJu7a7ZCkGxW6+NyHPbVHXn7x269etv7suYa0s2t/SLjXk9H5yQHzX/i9a4LS7+vnlGzo+8ZRYkKtl6h5'
        b'POrz7s/hC3Rldv8GJrc6wVF9pdXfGEporimcnUTlVgme14etvbHQWsxE6eWoQMdGqAG5U2j+6lRf1Ek8GHujqRDvPJPVmD0WHbdm6Y8idBQdgCwe7ccD204vW6Xg6azM'
        b'EhVtRlkkTRT6IF/e3gVwQOnGiEIZTD5HDVJ6eQ3WKzKtiS8Ay7y+upwmKhRABpyEAmZz7FKH0zIx6uDhDLrG8aiQQw1j8EWyHizs4BQUJs4R6MExfCkXL0TUl8J8FKfR'
        b'MagnF9VN7fA1PPsOxkAjfYwEaywhl3jUkYKv5XOobEcac1CcXpM+MA9zyRaOZmGiNvyyZKUEwjHUIkvV41H1XI6Heg5VWy6lxt04vBVVy+AA5Amg1wcXizeFdtxXV5im'
        b'ccwEivBzaqgVavGDZ/E3TlJapBo6MQkveB1u9yR8oYXDCs8+N9bQfViFzZSlJvELoBlfO8qhA1vGM4J2uJKILwjgPMEROEy24hy8uomkPR8aoFGmVJka4gdqTeZQPky+'
        b'4kjB5zIsF1OtYqVqrSKW6BHE6khYqEVyeydB56M2TvkfHZpVqC1QWBmVf7E2osnvMBwcvYxr9FNghNBEQ52BsjRltH44QFEojVaqIBHK3MAo/On5EfSQKwPD11W0A5cu'
        b'pJX4kf9HDwFaui0K9ff0uy0OdQsJDHT3c/N0D2KwkkoAptvixPDYeHniIM1evK3dn1knz3MkNw9Jdtw4GKiJ4jYRAyVVrOhbsQ4a93/JYi61w+06K5RDq2lqGAjJHNAT'
        b'6qmZLBLgT4+N+SjQ09cR6BH+MJHTHk3eZIImz8w7B33h7NDMgi4o5Llxy0WxqBudGBTSqyP/LbPiBxOKESApBiJ1TCSHkWKfCZiUFv5DPuvIIaXY9/2fDQiwVKQx/WwS'
        b'OUr52TRyNP48hn4eGzku0ixy/DExoSrLVY/mIydEmmdpEvjIco1yPlJcrlOuWW5E/kROLNKIdMwlMFXqWIudGjmNgi9pUIqvGVkcgYMiFGbkuXJxuSBagJ8yxn8Nyo1i'
        b'2b+McGlG5Vrl2tEiAhiFy5tJILBIiblaubq5Rrkm0ZqRtpF2tGQtGkWrTqNqDaPVKUCUJoGrFHFrxVRDnnXbiCwEN0psQDHHoqOkD2YOkiUfvkHO0DXwpgd2WDB1jpUl'
        b'OMuSI+nvmQ4OM2c6E/nWebss0pksDjsHB0f8F0vOsyTC2yI//0Df2yIPz+Uet0UhgctXSPjbgqXu+KcWqTLU389nDd7FiAngthrVJ29rMR6KWPxRLRprxbK/Uq0jqVYk'
        b'jacrj/xIJGtU5OkXxOAH/2JZ8/GWNbgsaRotMGjpysUPlmxOTk50trdPS0uzk8VutyWSvpQkitpGyBPx7CISttlHRtkPaaEd1gccZtrh+ggRqKJ8/JmAYUmX0mzh21o+'
        b'/m6LfUKxAvBgOmm02xJP2kL8e0V4OtnSAokZWJaMC7VzmI1/EupLlmk8mxUnJW3VCfL0W+7jHrpkcbCbx2MW5Yj33/hBr/xg7pAH3aQJMtkSqpkMLsMnIcZXFkNLciQl'
        b'CfpLwi3bTcrSH9IfD8YN/1IPRqnsPIl4UClkuj1c7JAv5g9T1tCv59OvR27V8NccH1j/he65rREZFR2eEpdMx4xOgP9IQsTmx0krYVHjJ6B1tDh19QZlKKCLSewd83QB'
        b'TTcpDdtC003mvxbHcyJ3ftn10BHSTW5rEsbQZDzzh0+mIn9WMDDRwTuOneLZx09dOIDfahn+JJusWh7Yx10dlL4wUq0SDXZ++6o4xP2VJzmZy58TRM1gv0EJD9qK7n2C'
        b'kyc89OOOUcyxaG1lMoP2sMkMCpNmpoYKk6YnS9+N3RE1wLDJ6GqYr4ns2iMYMoMUpLIWiZRUgAoxMueHb7S1GLKyLCzxlj3ybWQ1PfKO+RaWVrJY4rhKnWvnZPUYRbIF'
        b'amHp5vHom+XLltxsY/GoeoZf2haWnsF/6QnHEZ543G2AFDG00cPZjOV2L2YgYnnZcqIiBVT+cE+SA5Y9NnTaJEpjE6SxyekM19bSihzbhACKHNxWqs2IVuQ4J/eQw9WK'
        b'2IytyKloJbHr96062c20c3CW36K6mH43rAO9VV5q/9dO9GtW9HAvxnAe5K+mAsOB9c8MGYVxGLZ7qJfCeXBqPl1kqhEZ5Kn1w7apH3rBWUmB+jC2AsE5UHriVTjayX/4'
        b'GuWrI2Z8aj6lUQBR4clkQskUXF4DgCqIH3qY/H5igsXlkER6FjQwgGqB9o5FUFQUedeUuAH0YCqLclsc7L7cP3BNKOGv8Q9yDyUEJkG0lUqHPSMtG7aT2CbE+oeSDMkx'
        b'TxTjplDe5MZj1f7tfoMydVKwEvrtvVZD9hSrYSME6AglsnUqY5RnQ7YYK/Z2iluGQT6Qg1hgEVbB6Lo5PN7CPSRwGMN4vEVQWmzyjihpHB245BEazzbEYdYSXjCeyeFx'
        b'6fTB4Xc4q+HnrBx9gw1IPygHmfnyIVECdDAf1TBvlMwCHgYAXw96NkEFqMTjOg1w98hFJpli+g4pV/WYyFkA++ul7IubouIS4mNISSMY14k8ovWQ/KTPUgo3omrUQuIY'
        b'ilGpkBOgOjiixltGBDLhKjtl7wCgyqQEPeeVLL6BWoVOobokBs+ZBg0UoTMJMmnOiEekGdaMZ0NHIhxAl/GfS5Av4nRRlgAVrkNHWf5YJXRaew/MDVv5EJilEsnSxUdu'
        b't/MScHNgvx7K0pgmEVBDdXKUl9IArIOaIJNfCFdQJnuBQjjkJDcb2+hr4Cvlk2giFWqFVugZgFna3w5lzkyirm50ciBBLbW09QuxtEQF6IA9KrAhAJUMgNNWHcucR4z5'
        b'VTuWMWt0lUuaHFITnYduBqt5AWqoG8NlK4U5nahmEeaTYbyZo7lRLrgZ1RRtczrqlgNueth5+aJ8/N72gSjPJ8BDGAj5JKEOdcGZ9Gkc9InE6KgPOhv7/a6TnIyYZNZ/'
        b'u29akav2/kUG2WnRKXtfcy51WuVl5jFrtWVW61qrLI/3zrxg+L32cYdLnrO+2V3yU/RsB03xBdGyrP3ufIn0/ulrH14enfn1nWPPtWS33iqKCbQ689m2HR7zA77+Z1Ty'
        b'B23ZCb+Eme4wOrV51p05Wnl751a+7xc+yfD9L/bOtfz6m63lW+q+76p5csO0ZV+Mnnj/2bW/9nRH30o585x4083pnaGSLfb3896X6FL7YrTOWms7WxbHcFowGmocUPtE'
        b'GtgRCUdRBgP/JZjFNiQqQ4OL3agXKHSU+DDrbe5UlL0VdVsPia6oMKVxwHHWqLc/LN4HdaxSRIbUQymNf18TbsZi4lFvIokLuQJ11NI6xQ3qvQdEgeO6W2gkeAN0M1C8'
        b'QpQP+2mYBZzU8h0cIl9nypDZ9sNZqB0EnIdH/jQ12cI+RxpSjq74o/Z+DD7og31DcfigNYW26Ym1kEESVkLRwX64RAKWuBVOsliTHtSMi+oPqoe+mTyeSPXoMgsaaVmK'
        b'Z3ghXXrt+Abf1TJ+GXQ7sYD1QxOn4PWO1QVBCDRt4h1RI6odhDOg/W8Z3pRAcS7DKVB7OXUjXlsepkog/UXUTCuifwkhr55AwI8bRuGRA6X5PRz+ObLuM0LEyN/AeFs5'
        b'ot7WbP5Ive1x8d7kaGBqoUS2HQGS6jD+xNDeVFWnpBO2ewz5+WGkNmILC/JYHHhbROhCb4sIc6hC4xwcdMtCWkmE620NOd209CA/JL9eX3EaeXDK/HqmcOrIVU5dmkev'
        b'l6sfrf8YWfRC2k+i9xtUKZ6LIyNlg2mRFQevCrOhUmR7WH+NtnAmAqVzmBLQJEyF499GLgApoa9IQOXD8adDqf8Yvy3R5fvF2mTSe8lyof+x1Cm5IKwkgX2URsXYotiz'
        b'Krhaw2UW0XEJ4cS8YEGJSeU8jMNF3YTHD2JBG0rxOlwrBqkZqjhYk6O2Mxk6WUlduo0Fgw4T3YnviY0kAmB/V/TzyLF3sLCkRObk1aiANzlwmZ2d3WTJMKIpi52gkcrh'
        b'ZDYNoC1WlswYG5nI3H9dZXnKZ/oJGOVTQB7XNZiOUWUZloHuy9yJo8c91C/Ed4l7oI2FQpNhjJXDxoLR0OThGUsTElmo9gglbFelHA5DDzpCceQ/pe5Iengk1U4enqwE'
        b'mlNZmoJ3WpUWaIF7xT3Qb7HPwxqf6mjmx9QCFXRUrCuUzL1kwsrnDVkXWHGOorTMYWF+CfFkpxghzHt7cn/tlOGV9FF4HAmtJhuEcupGSxO24a6KDB8mHjsuhRnbYmJT'
        b'o+IVMx8vzUgSA2QZkRAvi8XdRUrCHRdLv8W9PGzDWDEDTRSSga8p5zHetCUqIpntB6qVoiD/eU4OjhaMaZW9D2mDjRykU/6+1GZA1ibeFFWWE50ipWuNrnbGmTqsZshO'
        b'ImeLILkmpuAzJxHr6biWuDi8+MKlTB9jN6veW2SyhIhYOghKvTBRmkBoyUkv4q6VDzZeCGzaq+7MAcyAFn5YQwxPTIyLjaDRiURFp+tpYAS+6rXjJqdF7+ceJYe0hSX+'
        b'KbGxIEe1haV/SKCEDAY5si0sl7j7DbMOrQakFDhJHkYeHCHUa7Fyqx/CCzRSCKlSPdVUqZ5OZOb9WbHQMkADdU/Vm6xOBR+qUgUGE5Vq3xbeIkxH0yKZRYbZobPoIlZL'
        b'g7GSISeO2BiyjGmshZbm/ZFSlegIHNiF6lioV0fIejk6DKrjNqM+OKztEkzz0oOF0CmmCNroMpyC2sHqrCU0p/iQAtp3EtqEElQYhh9uDCZMF8FymANvW6uVHjZeIao0'
        b'2wEoO3DB3RBrQTkzGexAJZRADwHnzlVot/xCrGi0U0QTrA2hClbfY1dGETcoB0yApRL8QqLOOTugkqUmqDVJnSrUEVCKTotRB5TLFWesNmeh+pTtVMOFK2u8KT6QrZc/'
        b'ftwDnZAXpobKULb2tLHQqN2vry5CGegYvnDKCLLhdDCcjAyA/CV7oAoy4Rz+U4d/52zdDqVQv2TTRihYIo0NCNiyUTptPVRu3WzAoWLX8XDMT50N38nQneItcBV1JuoI'
        b'sCJ3lbdfh7JTQki7atTQ4YHtGtQolD8W8hfBwU2QrWwNOiMgDcpGp1A5aRyJCAvTR7kWHDQHGI6BHChjJoR9qNhXjIpGsag0Ld5+aWRKJBFicfNblBYEyUo5DlBiSkow'
        b'Kk3U1UdlwfJ+H2BcSNTVDSSDI2dHYUg5qN3d3t8XMqBBk1aih/JM0XmUiY6mEH+MEWqE0wq4JpVYTeSxYEuPQPUBg4rHL1d3eUQ0Bf1B19b5eg/kAyqC5hV00uAivckX'
        b'ZCYdUpN5QYERnt0FBrikQ4F4MhbwqC9Jdzl02tJkFUPosXmoII9+RPmVHnhIjw0sE7LFUG4yDdWPwiryGdNRQg4qfQ3hDKpQpxYQ2dY95N0c0NUhbyVAtagc19Tugkcn'
        b'E2Xh3qWBeVC2iUO5gTqBJml04e0xQYcGGHJ8PCVetnYqqD0s9gQq2qQ7eLngzqpJMYKD5jPpXIL6dHM5wsSBAI/HKHn4cgO9TNCRmXDVewWzD7Wiky7EQOSKmpW0Kw1Q'
        b'RsN66F6zCF1DZf3EM9DGMe4ZxjszHZ0jVISxqy5GCmRnsFb1zkf1vgG98a8tMnhnws7eH2t2H1lfNiXD0t3LPHOGh5rrDPcppVf/mXHXRPK67ozTnk07RT3+16dYWFk9'
        b'JTzt8q2m5bR37803Koq5dmLsSzeeXxoYYLblyKnSijnf9Rik+DdXqn9hsiLwbPO8X7ximl79buHkhvoZFzTuTCt7vSDoxC6LmOqtThu6r31TNWv5i+dndE6S6jn9dPtQ'
        b'nV3F6ZfUf4jtuSCKuPLN81Ev7p/7FSr6WOvBp94dr4TObss8+9m3Zrf1N0dFbvvVu23PzIYFPXvMXEe5+H/zW0aMqWvOp3axfwgmiq7umbA7t7izu+t79XfV2t2/n/5D'
        b'8rm3vN+r+/bCSwuivrkjPNK8PuPqj9Mtjjzlci//7rj1o075v3J22YkPL/o/98zHtbn6o1s23XH9/tDJXMntDc1vPv2lKGWu333dlo/n3dH5Le2p+T+feC/0wJ2fno+4'
        b'kdm5P9V5S/reJ2P25/wxtf6F1yV9d9uq3TI6a/dM2j6/0ssue/UJ3c5Lm65umFBUcWGF54ujpp/+5MX72cIpFTcefMhfEP7keSv/paRpW97J1V0V8nb6SzkOu/Qur614'
        b'51rQ08/uNV1y8aeXPCWm1GYD1ZCb4G1nu8xyMOLAcdRNjT4O+uhwvwkLzjgpkpvQyUksH/oMXEFN3v62Ppost8kR9TAIhtKtmxUrAB8QSggGqIU+BsFQZE+It6DboB+F'
        b'AaqN4DS1vtkYQTflE5GTiYSgcgWfCF5r1Pq2fg50K1AabKRKjAY4Fs4y1Y8HOinykKAEHR5gIZuOjrKAxgzoRbnEeoeaTQcY8PCKPkurgB44CF3WcBhdkEd4sujOWg1m'
        b'PLSdYI2XpCfghaMeJwhMnjwLnWfBiQ1wEmoIskXaQjkED96YGfRAE3QlU5MbOmuoMMxRo5wxVFOjnACdppa0EhtTdEUlNwY0oRbawK34vO1VZM1zGoqkeSjcyNK7yueN'
        b'83aDC6jYhjCqiWx46J6C382Co/GTrahJzn4Cfbgv+016uEMusiBSOD5xgH10V5ADKoPzlFfDccIUbx/P6FmQbz8UN8kBrqjbB+6gw5y2BXcimUHSaHzG+GOJQm+p0BXa'
        b'VtH2h0MelA2kNqnAp3ozPnUKafVmgXgoCu19bSW4fldBKlRb7IZqieZjZzjr/8+E8YUq8CPzhrcmLtfmdQQ0oV2gw5P0dwOBulCTNzJgqecktZ1QUyg+adLgT3V5irqB'
        b'cIxgDP5N/prS5HdCVGHCa6rpkQQ1AbVUCvRosjtLTlcX7JiswsY2JPNahYFyOFOZtHxwFOnjd/rAtPJyFbnlKtLKK4nlcupwlst93OeWA22Xj/GiqiN+CHIiNemxCBIu'
        b'Wl0Z+yN8FPD8g7CH1IXAqHisqcoeZbejRgK5YkLU0nCZxWpfnxG0DxJtbv6Q9mHjl0LMnraJcNF7IKXiYPw61zmocJXlQ9mj6Bic1x2ViK7QE33FE9CKN5mWoWxy7EQn'
        b'+SIMFst5spKMzXkMkQvOQSONM50GBbCfXEu2w9uqXSr+4UXSMlHj6Kkb1eZCTnQKQ8vwnkFKxyWYe03AZ0IAXGX4YHVQ6KP08KEayBSgOt4SLkMDVaKetxdIPXjyKUzn'
        b'pU0rGVjmXJRpToErOW4LFPHoOAd9U9ElCkKpZQwn0SGKNLkQtdtbhLPUjUu+0CTWkhIEuEZv3Lzza/ALkCvb8U5oLbHCO/6eJaJ0HmsEVdBF33rLVGNvcmz4qUHZOE7d'
        b'VKADuZDLOqQLXVmEOnYFoSIRYbjE7zcGnablbQjg5FhzExwI2hxqnghFtA90IFONefugW0z0lk1whfYBLq3XQ5l2Ajlon4CknaCTqIHqWhJUACeUOSurIUM4jnfFCthp'
        b'pgI0OUWIKXFhCKrG72c1DaqoPBcMBElP7nx0hCyqobVCB/WBCtFVVBIERag8BB/L+OxAhwiYnaY/j9pj0QXa97eNSlYcFc4TcA5het8nLmRa7dmVUxYRIgg8IEtiLLaz'
        b'L2N3ekrvcjSn2yt77zhuEJewctGRw4ZyCZviZcad5HbxkVwkny0Yy9UqWYWxBPk5gUYnCa2LI6U+sfFRCl5hURz5x8MQvuT8VVeSC1ONwhq6HGjwM3NWarFVgA6h0962'
        b'WIIlEg4f6DQfd3w+5M9H2amLlkUneUr3xEPGBG7XTAO4GJJMXyzBUMf0NwGeZyvCfL7S12Jve4kfnZwmXI0PxbDxjtutmGwMF7Wgrx+KEF1Khl4tJRRhHxTQoYQWrDVc'
        b'EzMdEZ2AGqon7kRddF4vxrJCBr6YpIv1kAxoEZrwC1DhbFqp2SwNix/4MaRSHz/XKE4iYKN/Garj2KwydqTKcIUxTUlaNc+GpSpBgyvRC7cvoPdvh6Ix6BJ+QAPPQqlw'
        b'Ou+6y1MOSLlxwmSZHxH8BGKoQld4C21U/bcHcjMeSOkRFpd6lFeSQ0sreZUwzPhH54AxpEv2IMpyIqiV+gK8vKT4HeaJ97ArDQHQ4pQiJooJwXOsxLobQ3okehgcQpd0'
        b'UKcGXumHUAveU5rHxNI8OnRCN4C0IYCABdYF4L3mEksJ654M7WJLKxofjy7iI0vTS7A2bhtNCduxGQtHl+y90GUfPhCOcWqwn8dCbws6EfvkdzpqsgD8JnfvN0WFeMtM'
        b'QkyuXT5x//kbi5ZYGBiZO2bl6R/Iyzy1aelTq0xmP1GWt2Pq7UYvfVcbyy+d3KN2tR9e+UNmhfuaO39w1uLRLWvW2K3/2Wz9usPuXYkfp/n9lCUyTXtw7OtfH7z91qdJ'
        b'M5KMLpzt+cq6INn/wudPiZOjD1Z8ubqiU7enZEGrbR269MFbH33SWvSvFRd9zSOsNx7IyzAuSwL98K731n8XYf9K8Oef3/K3OXnr/tao5O93B979IGjOGx+VWFpa1Rut'
        b'WpVrXBHS2tT1vFqEU0v9OyFXHc8Fpn377pXoLWtsVyXd2V6/Z/3T71Q4ly67GTDumbm6Ydcao4V5rz61pXLtyzfnNG8LPvRp6t0njn7R4PlDcNrt1/7R8YpuxReJRncN'
        b'dI8+aL39pB/31mLfVw1u+Kak3bSM7pb9dmbFb7pPJzZuFHYeWmvdecvqrWl7dj4Ne95oKPq95dXOmTeLAsV2v429bdh8J631sxlbFvf5vSWr2Xpdw/3XBck7V3vvv1G+'
        b'4E+1pxtcQjovH5j9/K57T5rNsurofv5W4yjd6xOXr/wx6tfYvFGN/xr71t39C/elGBhOz/w18uv8sJkd8O4+8w88Aj/OD/OyqZhg5xLY/qF4a9b9p6rs1WpMvaN+Gm0+'
        b'G1XPHnt0Crhw0THXuZ2ttw6F6L7++4OK7tOxo4t2bTT8pHbNawvSZOLbuReLN7lOvnFjmV/zN04vL88wFz7z/LOtxWY1tw33vvvhan+Tr1+Ovx10tyjuVs20xf6Lctd+'
        b'+NPs8hni5o9Cfox8N/Rju50FLy1yv9bx2hv3Wr7ze78kzG9b8L+KA4tv/f5Mnu9OQ9uIlORDzzzVouY/ZcmE3xeW3l41Icjt3XWFfz794lOOL75Xebw+Kf++xk7xyrcL'
        b'3jrnG5hUuLvySOfY0nt7TQv9/xh/dM1zX9xvvXna79n3D30w3m+e+kdqezJdX3D6sTP7l+thBb+suXFp9Wf3i/5IPf1d2oO38g+//K7fp5N/+ulw/DuXP8jofcbp5y/b'
        b'++5+GvDUlXT/y7f/UWX8jtUv69o+vTOu+M9NpzJl8771vv7CdzsP6O2K8fyk5uaJwL3Lv9irfdf6yerr5xrNnPZdfab3xWvBTWNv1P4zfrveZ1/+c+KVmO5Xj5rM/eDN'
        b'hWssV6RdluV8+c5PL8iuBiyr/tDz4KdTT92xm/G0bt+ouALb4+Xw1kxJ/BW7z2avc5FkX44KXF/ZOwXeniN5+vjHp6+8v3CmRCM9MOtNF8mnvx6afMPnzXNxoR69ieNu'
        b'VJuFymo/ekdgsxRtmP3SqLC+3+5d9rX+4We7l965vmP0l67Nal1Hpn90x/SPBaXGV/8c+7J7lc3ZxOfab83c5jD3vb6E23fPbsyN+fjUdudnzzc7So688em/Pg79ZFT8'
        b'9/r/0Hhpw0+GzhkfmUyckXrhH8J333onMfz+7q+O/HhmZ3zb2I8Sjt3XSBjb+3nu1mcW39vVdbHk+b5Xv1v5cd4pt8+SFjr7BjW+W3kG/V65/PKDVzIbFvJBbxee+E43'
        b'a3t9CfpA59ZvNa6Fe7smr53Wcv3PupX1ZWpdzheaXvhTuKJ7ef575pKtDPeiMg0Oia1I5g4BYFPEdkyES0vQeRG6gAUEBu6xjMR3sNiTnkkDwk8OQBvTNKugCs4Yo+LB'
        b'FJdEwVvpTtWvJeaAZbAib3INnZDSy/oOwph5GkyH74hC15QBJAnxSk0VaqZSKA89yCPoJyopHK0tsaIau4G2xBdOpq0NGcIlSZgk4Tw6zTTteqgTK7AR8RtWcxQbcR1q'
        b'py0Zg3oIPa5c6m1eR5M7dVGfcJGTRjJB85gaC5dldrhyWym0o0t+EnL4X6KBOyhfyM1G59SDcB37qFo8DstVJ+RaMy9CZzj1UIFV+jQakoMux/t4+1hhpX0Dyt7Mz92L'
        b'eliuZaPrajwg9ljQ5kkYDW5fiWDaJkaECec3LfGmwMrlDP6NYL+pG9NREgvhohjl2aKLxgTf0lvIaaB2gT+UoA4WptPCKW7AV6FsCrqEzyJdyMMyAjrHSECXoH0oWw5r'
        b'i7LggsiJh0Yss16VU6hCxmRWwvrptp64em3BKlQ7k0UKZWxNlkENqrbyRMWJNBG1xE+DM4BWYTI668PerXI06vBmrJVQ58+poV6B0BHO0K4PQXmz0SVv1OYvhkZoMbGk'
        b'eLUCOLMQ5GCd1XAGFcoI2qSW3Qy4iorUOG1ULECF6DBH75gNV1AvaaCWBLXaoU7aC7pwVYh7ZBJ9QRdUROws1MaCjkTJzSxHgNlpXOfGokvp6BzxFEi0La2ILcNojBB3'
        b'ytn5zNxyJcxYbOeNOkNjJagQd4CeYJ0wgQUW1aOrRrPtZSSEhkgNDWg/lNNWLRPjeXbJeoUnsXbQolGBGmdoKoTKbWrURDIL9c7w7ifiJMiKhIzTDDJFeC5dnUFn7iY4'
        b'Do0yO0+4oGOJtaJuW6zZ6qkLFyZvZ2YWAo1UKPay9UmC8x5EIcuFPpmE58YGi5ZrI0YzC+UaQtSADpLvOXSNg66xcJKWPtcUKrwZdjZWjgoJ3KQelAtd5rDJhS7wUdYM'
        b'q9EEi/NKuMY5kEMnpvkU6JZ5WkmwLFWMGoVQzmPZv3cjnem+Hot2LCTYm2ocL+bwuF3ZQ8u0nYl1JYXlrg+VKi13lePobFmLqucpQByheT1BkT4FuYjBR+6aTXYUZo8a'
        b'j04qDFILUQUd5wA3OCW2xL2Q5DNjJm6VNqoSQI8BsIkcDUfHk7eBAj1fW57TchTAUXQKSuirLPGaI7aTWOH+rMfDhRutGSuIFWixjaoFWn2tUZ69HR7MSBMC0KwPRcJN'
        b'eN6z2LPAyagH15vkx2MB+zIW587y6MQT6Aht1PpxqFMswQuD9AU6PwrP/6M86jBbxeyUOagUKr3lJjS8ZqgVTagIajuF9VA898mLogryfT4PdRrGdFrOguoYb2qhXySz'
        b'U+fEXgJ01kDKkDCXzyfjIvWBdt7PDq93e6EmlFgxvKijG9fK1tJtgENXyMsdhkzWlhI4SnRCwvGAdYVePQFc482MoIy2xd1gqSL6bj5eXCy5vRflMENty0LYpxD01RN5'
        b'C8gXyfsOnY+WBxuKUb3SBkySmGixxuvXsaaiA9Bgz3PaiwTQaIT7jh5WddZpsB9VyCiO6iWyjPAUJ003wfsuXsH5eAcn68AgEh2RoWKJNrTY4B0A7+I9fqgN3zfWQGSF'
        b'WiewgMocrN9m42LwZXxtVASntpJHBVGQxWCEs5OCFWjBK1E3bx8QxPK9hauJuyYVXRKpwwVOZMhvtEUtLLX8EJwmrSOEIzwcnzkH96HLBrapLiWYHPYo31JASIYbhOg4'
        b'vgMOqtG3NkFlKAM32NLLEGWnWQk4DTgkmL/Gmi3qCqhGtSRE1p8YXvKhC52j00NfIIxEDabsSGtCR9zl4OGQ7S9HOcfaxhFaxhiswx2Q0YMKb6yodS1WT8i+OAbOiRxR'
        b'oQudJpsD0VG2s/vwskQ8b6vxvF1hTMvXtAljHS5BbXBpFu5KbdSBJwQXQmeRhzo6Q05cElK50gLaeFtTVEJrnhQMbejcVhk+qrRQfhr+RdUfY3RICCcgexqdL6hocSJD'
        b'S3fbTJZ4HardS8tNhxYjuU12QxqxylpApQcdnrQ1YeIUXS0BUc2OCSfxi3US2JFaaLlbhg6QOFcT8Th+ihQPJ7XQd/jjd6av4JmE96dueo8u3qempcq3k53m1nIU+cx5'
        b'DEiewsg7QVMyAaTXEDhRIDF7VOALVattJJ6+eLOWwzLPc1GHU2g/c3SkYt22jdqhPWy8oGSm0hBdK6awu9Gj51NgZepgi1o9DIJ7CGrRtA9PpusmbDQeGg0LepttEt1j'
        b'DfGqhDrYZ8XOxdNQBEcUlNKhcbT9hFAa2qCWTk73iR54AuCVtRCKyMJyF0BTyEo6OfGW2o2OkasCgotcKITDPBTDGWc6LUbD2ensSX4x3T3mCLVmQDG1y29e5W2tou2o'
        b'eCoDyg1LY2JHF25puxjVJMnfgFZliDqFeMHU2yUT4wZqwode20D8ewX2/e6palpwcDdtjG4Kuia2JMce9EEF3hh5aBgPlcy/1I16Y8SogAg3Gf50fmtyggB8kjbQHtCA'
        b'c9CJt3UvnhOhGiFqxyswbTervBuOo4NYYMkmb6rt5UtmCn7eBLKEuFnng5KNqCh3eHJcgljCcfw4DmWvhXN0auEzoi1dFo0K/dBFeywx0P3ZYIsQH9CNkMt8I8e2Eehp'
        b'Gzs73MMZ04SoEp9jKWPo5N8N16BSTCa/QALXUC5v7uxAe00wK1GGN3SUr0XfCTrx7kkXLSoVOVsykOM4qAkV25J3Qg1wlFM3FxhDF1SxDTwLDgRTeh0/50hbKzKf8ZI9'
        b'7PgEO0wOx1nL7PFuyNt5SMiOc1XggerhBL2Ygtqc0CVbP2KSgKrxnNpunpDFMDxrLdQr9V/CgI+Hgh4zQWI9VJrJ7LxSJFpbCHMcFtEEAiytkqlIBkrLFRXI5WVPfTU7'
        b'S7KZ6aIu4Xwfa7Yzt6NDa/qDt21QidCXXwblkMd25nOQhSq87Xzx1pw+V5d3cXGjHbkHTqJieVz3Jg9v3hF1p7OOODLJnRrk8IZfTSzHDNpkt5nE8H8G61b9EdcZjAVL'
        b'uVWXUsM+9fBoElOYag/PXm6WJoUYZuDF2rwRBesgkB0mDEZQQGA/2D2aFO5DE99nwpsIxvFjeFOBKT9eYxw/WWAgpyfX4fX4qYKp/Dj8yUKNgBHrCUwE5PdUwSKRAW/O'
        b'jxHpUdBjWjbxI/EG/DjhePzTFH9nLhgnMKKtMNUZg2sgkCM2QlXlGuBnxtDnGeixtsBUoC0w4ceJFHAkjCbdAv+cjksYz09X1+R3jFXheGF9NRwD6qO7vd8RVIW7ehox'
        b'BxIn6DCOoH3cHdOBrqDhW4SrplnyRTzJLPbzk4jwDxr2LdEZglIi3cDRROsgNw93X/cgiktCE6EZTImvElukiiaUc3IjpsTkfwM9BHeRk7KLtvKEVAB3UTQRAEQikRyj'
        b'Wvjv/NYUGhiQKcrxJi4MXWQM5bvnePO9nBYFal2GjkMpPn+uPWxe98aL12WtOiqQQMag9Hht+W+Z9sjgIsJITflnrQGftfFncaQO/ayLP+vJv9cf8FkONHJMSwkiYhI5'
        b'agCIiHAAiIhpkUbkdCWIiFnkeCWICAEe4SInRlr8BRCRSUXqkTOUECK60WqRkyOnqAQPIXAlA8FDoiWWt/Upig4llF4atSk2+YH9Q8ghA67+G7Ah81i2Oda0bovc/APd'
        b'bwuXzFyCJ1QSM8cTMAs5VIhURqY24bmTpvCPD+oxj+VQzvxLSCDyh+b9dbQPRXU0ZdNRjvbRj/AhpG8k3UlBhALdff2D3SnYx9QhQBtBS5cGRiUNzhd3kGN8PNbNjkoc'
        b'DEWLHowZrlwlFMbgxku0BpVBRunhQvWH9pjqskaofLgrjtJC0lX/WYSMmEez4KoxnGosd1yABoLkp+ZFQQUJoOD5eOaY6YAj/uJUPEd52I+lrzzivC5DjbGuZ58Uyoho'
        b'OPrMA8ID7hF+I9rqA++WPeHa0Z9x32WOnTeLm79N1G6RKGGSGGr1tiZGpSAo64/dqdMchhT0gCKog2ZQDXfkkz8ScmzuGDNknf5NsA0zDYK/NNKJR/58Ogh0Y9iqHw9x'
        b'4wRB3CDa+/8Y4kaMRPT+JPXHRdyIpG9CIAVI0P5/Em5DsbQeAbehWE6PvGPeY8NtDF6hw8FtDLduR8C/ULmaVd//F+AuhqZnsUyC8HiSBECyrIbJGVI+pgpJ9SGIjEHj'
        b'LIfFIMcSg7rAR5PV8Ok9j8KjULTkryBSxEb/F4zi/x8wCsWKU4HFQP57HEiIwYv2MSEhVC7g/wJC/EVACPLfwxk3an7BNN0gyAXKKSLBQ3AEqAwV+cg5fRVh8VhsaOQ5'
        b'6EO5YnQGHTWL7fWqV5O54XJGpe2wDv8s7LP3NkevffLW9deuv3n99etvX//n9Xeud5fWHJz05sLsi/unHG/cLynsunUya1p2Y+XFfMfsSZTLPKNHd45amESNmkHnGBK7'
        b'pa2HreUiFhvrAMc9qXl1O2qALDlwwFHoHQAeQKADeFdqT/HRn8r8pj38oBjg3d7M+lqiNpOZTZYZCkg2fA40U8NWAGqdNYRdAWqxYkby/pscFNGd/05sqzJTfvqjxCB/'
        b'li+vrkoe+b+RED/psWSr981Hlq0eNys+i2bFS0v4filPRU68N24Ty4l/qCZlQvzkYU5LFUnw6iNH8UZoDFhbYsX6WkTkO40hEp6YyHjRYrmEp0ElPE0s4WlQCU+TSnga'
        b'ezQHEC7tViXhjZzaPlCv/f8ir30wTphcbJIne2/DBw3Juv1vqvt/U90t/pvq/t9U90enutsMK1zF4b1/ICXaX8p8H2HL+N/MfP8fy9cWqpQejVi+dpSHryJdGwr11EcL'
        b'9FYy6OKU+UTUKoUmQklFAieCPFC+vwLyy8MLFVEmslUEbkuTxtpDGRRqCaAdujeyPGzIwVJevThVNxRdU4ErNi2ZJXIXuiRAnojhktHs70R0OYU4ErDoVhKuJEofAvm1'
        b'CI4pUb8EHBxCJ7TQVXQ+nTHYX9zi7I0FzExlMijK87ChbV+F8hg/q6caFzpDc3EinEohogfKXr7ZWyE5z7WUy84kYdYGFfvS8C8uUKyBihaG0VQTqILCWQquV8+QFats'
        b'V64i6b5evj7QGOwB5z187Ww9fXf54jLsBdAmngmFgUGcORzTiwuBavbqGbB/+nqoJMQcjJUDHYpNIR4WOIJf+wQtfjuq6a+B5LImzpSSBFaaSC7iwqBQAypwV59KIYLT'
        b'pNA9QYob5UMVzB5QvvU654hoDTgTZUeD4ido2Ymleh62uBOFhrwrykuhhsatEYSl43IanESHZQRnro+3RheggAbeN0xQIygAFgazU3zeX5rAxf6rpkkoe4VIcU4XQkou'
        b'6oKDgftLqXef8rTY4FUfVjzbZlGSmnRq1rFyP7equqjMSP3pnkWWlRmX8rI237v29e9/TgtapnXdsqdqX8i91e9+YHpoaYb0sLC06jWdO9f8VxR9YOWg9fK4d1d8wKWc'
        b'24WeWrrk+c8Xi16Z8EvZM94GN382mJFWf7N1wfdjo0Od1tzrvf9W25QL4ea8r4nm+R+8g/+43mUku+l6a9Vvuz7d8NGdNunnoz/5OPSlZxYmydLfTy09bZ/QHN/9btnJ'
        b'XeVB7gV/bn1uhZfzP+a77nPdzWW2eSXFlEkMmIu3KBhOeUNzyhD66XQhjXfYBq2CQWhmakqSbz+qs4yZCx1QAw1Klu9o1MHSLCumwQFFpqbHOGhVpGrqoVrqvV4CF82Y'
        b'UsPD0UFYZpDPsgg110co52EAqpJTDk9GB1n4XGuqBzqHchSOZqwvlfnRdxJA/QZlHjZqtlSEsjUJaKwEnjGSgZG26ihDGWwrQhcmQzcLVKkNssXa5zUv8gpksebjavRQ'
        b'j9AHKlBvsjyL+hT0ENrjRaheznx8zkKeRRnjCkWQ4e0904ss/wske+MIVLI4j0PQPYPYqFEWXr4KIzXUPEGbvwMqQq3xem2fz8bEmueMZwhR9e7ltFwx6jSXZ2duRDVU'
        b'CR0DDTQyBs6oGXv7eD6UnOkLx+T5majK8WEdS/wfzI30epT+mE4zJIWalJ5XU12dYq2ZyKl+tSmhL8me1BOQ6zsmDtWWVKc2aj1OamO/lqk2vN9VY3h2XBUZjH6PpWq2'
        b'WwxUNR/1Sv/hJMZoiejBhkcmMarS0P5yBiOB8344g3GKXwrRPMNRpssIGYwq8xeXW7MMRtSBelKI6wI6oY4fAErQCo2J3CY3V6GYm4yahShLHTLoLq8HbaiEpTGiKlTD'
        b'AA6EUMYy+nLXL2IJirugizfnoBRy4CI9AARmQkoBxtlExXkmzOcYVVQhlgAuyJMQA1ATS0KEXjhPsxDXakAROpSsTvMQ7aHBjlVyzQ2XWgpVMuJ3JTHW+YZQzk7Hg6bQ'
        b'wvIQY+NpHuJ8uEyvJEIBHJYnIpIsRM2FOmEBtLgkyIDT5roDkhChAc7Sd1WHa6hEnocI1biDaCZitDnzuXXCJXSY5QyiwyQqnreyQiUpZItOc4EBaYEhvmGQL88KHC2g'
        b'veG9rZgbz3NjEl3C9P4xZR3LiDuxfDK3FP9+zyFm01ORgezLGes9uFKOc3gyapNXuvOafy8p8K/lkiGN/lwykk2Ie6NwqpwNxcbL1y7J0xcV2KCDckYlVIY7JJ+F/Emg'
        b'Uzhz5qLlUOgNZeiSTIx7zg3l6QfHGdG3OhOiy+Eetty3dqfOcnURe9V3nEZzWCAxcEgId1mw1ZNlBKI8KEb1ypTABLhCsgIVKYH4qGIDn4kOrpTn/E0zJBl/G+WQrN9p'
        b'EPwgzsBiSpTOa1Yz8auy7LcmqINeFsDrhg4IxLzF5P/NvtXR7O9b6qUtlECTIk/vPKohiXroHF5WpLF716EeOIa6+nP1ZqBy+liUDFrkiXqwH7J5dAhfX48q6fLZpgWZ'
        b'4qXBHEnWC8Aj00fnrWTuBpqmR2JU8frLIGl6vrg4Gv9+hEEfsUw9lqZXp4tn98UZsQaBPgJZDW7Abf+tKcHeslHuJvfupb+9UzZjkouRFFlfnXgqa58oeNG0k1cFmQaG'
        b'p1yqOOMb66fbtH3W2HZlhV5w7Iv2J6NXf+ttefiwdWHF1tEtGx7UvLq7UfT805VPvPvLzcp7T/ye8uke89SPdv3pVhu1/Imy9DEvBMaGPOcz79399kU+eg4/tus3J5em'
        b'd73W8OJv6zO+XfBdo8PM3hNvdS96w6px/+FFy8IybY6Z3XAfC1sqGuYtizM1vb6kPNf4lGZ9yMoN383qaNuY3xzvEjRxdKXG21z8mHdn79ttfNj15+XGppVr317nuX13'
        b'980PZ954+8QfjWZfze0+C1VTDv62/2fpndk/LA6fku1jssk6OXKcyf4+o05tp5PfLix+ea3GN5f/pacf3vL6Ww88HZBLgbTohfH1N57XWFv4dsrHO+58umXuk8tKLzq+'
        b'E+xpPne0Ve2GOMfvL48e/9bzxy0vrzmdvfHHpR2bXyy/X1D31pvGH+sVlr7aZ/mpvcOCyjfVoruiDH598qbnmtW9Xl/05Y1tXPVZRcmXN+4ef3JsyGL3Db8Y/GgYpz+r'
        b'rl34ziWvH6d0j37F8SlL2cS4voPZXgnw65jUJ1//LGTHkzc3ZGxb+Oln877Tbg48U1Ka/vIz4+2fd9vg8obG91rnF+tLF27TWPivc+m/3Th/L3Fu4ZfFDmkmP3a59nl1'
        b'3dZ0/lLyGngH7b/22vf3myt/rR+795WDOzavHLVxnGF3fZvllzVfvjo54kb33Tmuze324c+GGYcV3/eZ8d7ukO1fTbm6LNt8+3M61pnLztWfaVoU8tucJr9nzv68oH5d'
        b'X6C+P7r55M3JzmNPFL50/8++pM9gsu6Gqa6rruS/d+1plwuGPUu7J984u3TOh9lz/8x56QX/1H29N2Iixy6csPTP3l/2FmWGng1q1fG7npBQG/TZB3/Oz5bMfXfq50ef'
        b'ffHop/pnIxbmz++scPnnRXfv5Lsz+pKSF6Sfjig8/Nkt/41lxZXpy59N9cP3/FKT4uLjHB19sbjvyy+OVgb0aPx4wWTxkp4///gqvmXePaujhksvvPKmYeqvx50CDE+L'
        b'v9mz73fNHr2e618/Pa6l6BuvFveJ+7M+6W18o2uB9IWlzaUbHSStTqf9Q0RfnciINzv3evS0aa/98t7Xkm/fe7P8SfHcOuE3aWFptbU7rxbM+8m5U//7qvR7H59adSPt'
        b'j7s7v75h+WDu0t+F3QvNTMM/eLBke+wy789+uGIY7nx6rkn4ztUlyXO43bmfj4n5U/RJ2E83A1y6Xi5CdTU72/uKP1iQd6h08rML3r3+h8+KmyEfnPp/vH0HXFRn9vad'
        b'wlCGJk1siKDI0FQQUUHEggIDWCgqKoIURRGQAXtDugjSFBARQREpFopKUcyek2Rjetk0N73H9GQ3Mclm873lDoIaN8nu95efMHfuvW8v57znPM/Z6PNvk6RXPru59qAq'
        b'lSHJduNB6Lkf9IYdFlwUx25uNxmPOc536ZahHcsY5m0U9nJVoxVKN2DHxvsRb746TNUIxCaqJ3DIG7lpDAc55A2piy4DG0EDXNPxegBYbUsq8yqJsNiqBaoxkJocB1wh'
        b'L5knH4JXNUMieZ+AwyJOzRsOMqDaeOxaLQLVVEFkR0rGC04UfiQC1byBCC5dTtioxZ7coD6yYjRDxTqpgYkTdGAeu2sGZfO1kDQGR9PH65OInnKaaSTu+6CbYtIYIG0z'
        b'XGeYNKxM4bih6s3YNgg6k1EQSBuDpU3x5BpPCZREDt7HrmBfLNSC0qSpHFlxGE9Yipg0qF/JIGlBPlyTrMJaqOWvUzwatkAJxaS5bWae3dCyF3o1w/FoeAj6GCYNDmEB'
        b'16gOJ4WKmDQGSPOCIzI8j+Ws/MEBpJ5aUJqjQvDcwzFpUDaTj4N+PAlHRUwaBaRt8uaQNKieJqp02A59WkwarWP+KhGTJsdq3vjnSONfZrAyBirzG0dhZWMwm4N02tZg'
        b'LZ6Fq3eRZVt9mf1PNgIKsGs4qgzqoYYhy7BD4JC7M3gKz4iIt0hs53pfrL0Y15G0Qq0y1NVQRepOxLhR8URnvRjMhtjkvZB/F3niAi3Qis0ceaKjENEpjnNF2BqR+Y5y'
        b'730tbA1LxnHP/HYXbBJha+SJIiuOWiOKai3rpC3YB0cZbI1K51iowkKKTvNYZCOXQwf0TuDtnAfnsEwEqLkEpuNREZ82ESo4BjUfy8iU5RA1Mp1WQYcIUTPGC9xJqxSb'
        b'NnGgA5btEnEOhRF8jHVt3IXXiWo8BKVWMpGP4O5lY4YE+kwhw5lF+uyHRj58Oi3IoBZhati3isHUzLGHd23BSh0tSo0iA4KhnaLUJlvxuxflE0SQGinUArzCUWrh07jG'
        b'3gRFUbRCFKJmC90cpXZChIkmjzGkKDWOUCNCXj1FqUH5atZaXnB2qRaltiRwPvXCZzA17MUG9rY+XIXzHKfGMWoXjLB+C/JYoQF4IGkQpsYxapfGEX3oxET2bgYZCYMw'
        b'NeiCHoZTiw/kANWDvkT94DC1na4cpLYdCnh1O8biBQ5Tc1OQfs9hODUrzGJ3nbAOqznWJNQNS1ZwsAkemsjSXROIWaTRi4eA1bAZ68SGIutArxasRpI5xtBqjuNZ/9GD'
        b'pENauBrp1hMcr0bGeTE7TYrbDee4tGsADVTazSQ36IhKIbmduEuOT9GVImlZOVnBaUu4Ed0wmxd5ChEZs5QMWDMplo3ruXI8AleTfwuvFmPODoYk0Xhci1aDS9jHEWta'
        b'uBpQ5C1TB6smUDZM7T0KVmuwppyAHP2ggiNLOV4tA4opCRi0rufdUZm2TYtYo3C1dKiJ3kcWFnovARqhkAPWYGCOBE5S1F/rXJ5fI14Zp8WszYASDlkjTXCWvToJiucw'
        b'yBrFqy3SY4g1OLWQ44Cr3EiVKJIm1IvsgSX0sPQyKbM1XpI7L/Vm0212xN5BSRtzF1BBG07O4w4JRwPgEj9fi4E+esS2cA9H2hyfF6gMFdNjg74Ncw2gXArtcMaCD4Qa'
        b'6IdqpYjCIbosHo+ygzLkQWz3k4X4tBZjpCMosYbC5BxHsaUM8+HcKg3bKJ30KUqO7VZBmeO85SSB3g18ALc7BGhBcgwiZ0MmZL0dEQloAT3gFCmYFihHdYir2MeRconQ'
        b'wZegfsizFLFylnBYGilxJVrcGVaCJGg1noBtvwGWO5/AGi5pLTRysJwM+xlajnKT8AUwB69TRDpHueFhVzyZLoLcFipYp5rOgZ5BC4BEWOzFMW67IYeHaGiCc2MGUW4U'
        b'4haccA/IzQBL2fqyDE5TDLG2tajKv8wUD8oyMEvF0JqkqQeILNVF5R8yh6HOQRUoSgCjIEu+GLpJrensnIU9eIA/x6obBU26eEI6LxLqWa1cyE5aqoW2kWJH4imObSOr'
        b'dQGr1SLsWjR4ZKsj7LVnJ7ZkUFSyFvOO30MPS0mLLcNcdliKxURCYiOqcCfkaUi+S8i4OuJMAXB9cNl0p2wP9JA+ZZvXlRAodyajkchoIaRHz0OVHtZId2Pfbg5uuxoF'
        b'zRpKO1pIJUpaQzKiS2eNsJTtdSHyEUV+SCCXUgxqMX+/gfhbjc0M9Ic3oJWXrnLXbOVQyBw0iKg5ktpZLv4cxh5TDpkl6w8eWMcQs6Q1y/jkv+IC1RyUvRRzOCY7ibzK'
        b'hnJhNBTzV0Pd/OEcBwavxnYmJG9znToE2hcGZXfLyaB9DljMy1iCPfbKocjEEKjl4EQvPMuSIpvFDWy5D9oXgY0ToEJHn7IXMjEnevpEEduX68+hfVg8ms/qzgQK6j+k'
        b'FSFdPSiyD2snsf7dsR7zOK5vE5zluL5YaGCdQ0akG5nX9Q+C9QVAC5euiiCb6PUlOwaRfXjIiY3xVCITF2qGwvqwciRD9u3w5pM5DwvsRVyfE3RxXF8SN1HAwWQdBuuD'
        b'VqiWqiQ22DyB7Qqe2LtQBPbNIwvqYKUYrg8r4TxPujxmCkf2UVQfHIUL5ngKLrDmWK5HJh8D9lFY3yIHDuwLhjxWH+Mpixiwj8L6IjcxYN+uBTwkube3FtXHIH319ngU'
        b'z8MA78huH6zA8vgHAfvcQ3k3NFMxhyP7qECht58B++Yv5vLZuXlOg7A+GiBoqwjrg15bPpNyoTH8Lq6PzNAcCuzDGujm2N1Te/QZrG8inJHulPhgfjrLNhLyYUAbmVzA'
        b'y/YcvxcXojL+vwfsMVwWszlIH4bW4z92Wsyeqey30Hp6g2g9M/JjwSLBmJJritT7Dyg9mZ6IqJMzBJ213r14PTOG0LNgTxhT3J/cWmIlkUsX/Vc4PevhOD2rew0L/1uQ'
        b'XpmuiA15qK3jgPDNMKjebxSK5E7xCOmXtDg9Gf31QIheei3DrNBPvwOdZ/5/Ccw7QfK+TbGLy4U/D8zTk5kqRCCegxaIZ0aurP3YybKjEQ4MO82O96Pn2RLBEW7obIFy'
        b'u2HOtMbiX03pPfC7St1K/UrzRCn9XWksfrYU/xrwv0myRFmlXry0WBbvOmhrohFxDPON8o3zTfPN8i0TDSkMj4He5Ak6NEp4jhCvH29QLI1SkGsluzZk1xRmZ8Sujdm1'
        b'Hrk2Ydem7FqfXI9g12bs2oBcm7NrC3atJNeW7NqKXRuS65Hs2ppdG5HrUex6NLs2Jtdj2PVYdm3CYH702oZdm5Lr8ezall2PINcT2LUduzYj1/bseiK7NmfRfywSZfGT'
        b'4h1y9KIs8nUSJfGT4x3JZ0v2WRXvRD5bMXdKGbPL6eUryTsmpK1GsLZyjnchT4wULXFutwwXzAsJXyga2N69Ir3HlZL6Mg19gqMABz1xMlJpmAgNf8bT3YX/9WBBFein'
        b'6cMS09rxNG6284Y4CYo+bwxqIHrWkbsZCeks5kPqNhr8NmO4k9/Q+A8utgmxcRtt0xPS0hM0CSlDkhjihUgdV4el8FtuPsOticMuQlOpd1dgoi2L+qqx3Z6QnmCryVy/'
        b'JYn5KyWlDEFwMAcqcjuW/M/YmJ4wPPMtCRkbU+OZUzspc2rytgRm98ykC1HyTuqINSzAha1/EvNpcpynEt1xk4d7elGHKNFXkHfEFLEftC3uYus4X6V9LNZWk0B91jIS'
        b'HtZJtA8dF6go7CN2iF+g6JGXmp60ISklNpniD0TAM2kCiq24p6IaTewGhjxJ4IE8yFO89rbxCWlk5dXYpvKCM+c+R/HefDrCtqRqhvt4xaVu2ULdjtnYu8eRUCW7Jdux'
        b'JfmWIi52S4bn9FvKxNT0uIR1rEdCF8XJxWWIrI33hNiSi9NEIAuLhCwtSnFxkZJJIxsMsSUv0M0W9ursUuyRM6O2DjNqy/fpDEGaRct+B9Js2GT6bZey3/IyJFXkDoYr'
        b'Q4JFDzkWWYWle7fvSC8xL1IyNR/seuqYwIfUb83bhyCgWPvOpkCWuFgy82NIkWK4px9PbDCRocPvN+LdxMbHJ3G/UDHfYcOPDtStmQniFNZkkrk1uIQ8GPkxzHuWh7Gh'
        b'MzA2MyN1S2xGUhwbsFsS0jcMCVLzGxiSdDIz01JT4mkL83n98KAzYvMMGXazqScwde5l69NQl+akFNJBsTzZ/xQEh5eTLDNDs2foJ5Zs+I6FGcka2xSK73pgUiEUnUMa'
        b'ZRDaNdiEPGVxAYp/QCUf7ASdeHe6xrElW8NfpV7MyZpUDh8jrUbW7oQdCXGZvwXaG77EOTrRGDuDoMZZblMfAGsclCyoKVhHuNexY1yohp4KvLfcp+uFH5w/bVe1Zqhu'
        b'qq4UqV7pzNIISXv1mtZsZJgH5oYYhP2WQLRhvOochleJDpdB9C4VXIEiFR6DTuCvQBNeCmUyfji3mPfCIaLot+kIyVAq7BP2QRc0MYv54mCpIBc+2UXJosdEZwqc9jUb'
        b'2tyhSyp4wTnBW/DG7lXJd3799de1/tSvzy9Axy/GsFE6ihLqUn8pfTi2V4OHjLFQjb3buX2GqOD6To4SwR0rFc5EK7vCyuG8GTqVeBw76S1piMQLq/EQSYVKaKGT5/BE'
        b'trvhMWynqRjQXxLBbraOHZy15k4kN/A8nlDSG3gQL0sEGfZJoGU/HCHJMD/Noyp3DWb5iUmxwgQ6bQ1VYYdzoNqN2okisVpv7BaoYAliE3YZYBe5B+Uu7LaepzSFtMBl'
        b'lYy5d+BZyIY8GiPFFcs8pnpKhc1QYrhXunky9nM+7v4wHLh7XyEkQK7hPmkyVOxiOUyB6pl3b1OmqXbD/dIt2Lcgkxq1LO3n8uAr0DYzIDyAPrgs4K4ZTCIsNNEdOQGy'
        b'uYNE3Szo5Mr2MleRDBDrsdYcSmRQvxOrMun2sBzy8Magl1DzPBY+Rwxdg4XBarWrdOscqBuL1+GQJXZip9oCDqmVBpTlKWh5mJCQaOoFlZjFRogvEdj1hOp1Mr8Yl3jL'
        b'1UJmlEBD2LRjw1A/pLsRiYqnBEU4YmEAHg6jXqjqCLzkrB2nzENpSaCO2SQDzIUmHZ3NW7HXfxK0qAT/7RZYB1eJCsNGiqW9HXaZpKVT1g4p9kgciB5+ltM318KVmUq9'
        b'9G1QZE26Xy5xCp/JfXQOmOMJ7DLcmq7xpi+1SybSkETcjagudKcmLRQuQP8iOQ28FEMm0UV2izzVr9mKnYZb8Rh97QD54ooDGU30ZvzYjRq8sjUdWiCL3IRrEivsE7hn'
        b'tDEMsNxMbcTc5s3ihNUNeN1+aIfP8Kb9Hb+IuUxD8xjIESPulMA1HnUnxDVoSUTA4Ctia1IqctK7yUo4h60ylYSxx3vSqLI0MFJQKPbiNSheItr5RmO5fCsUYy+bBlP1'
        b'nNRxU4cE9mFZLHWN5EkLWC7EY4+eQCZO0rWnv5FoCokQHXeqe0vFUynm0yzythypuDnR49M5W5Y7/mBqMEln9PyX0kes/4u7tDDA8dyYtgP2Eb2uibGp1vqzAk7tFKw8'
        b'zJSPyi6tf8zgGz2X/gs75I92eOSkvT7z43/9+7lZ9V8c7oyIXiX5tCrcbb6hR+O3HZ5Pjv8gJGXa7Gcjonp3r/yLm1pnoV2W7WTpVudGl3FxiSNHLBxVcKLxLbWqqrkx'
        b'I3n9sYRZH7l/dX5Sx68B7zxR8sKcf3yQUhtg5xr7lylHW2IX2c7L8q+OWlxqbfKWstH7X7cqnlh4fMKbC+e8MB9dntK9o6M4dqI795m1X87zjz7jaV4/7fXk8me2XvzZ'
        b'vvDjZ549+OT8Z+x+kBq+bvaozpe5Pf2+2zpGlTnZpm3+Kn15r3Rt0eMvn1gedLP95cJth8d/vPnxj39tqJs6UGH+hcXcLZUe5h+233xu2phXOk1eTlu9tmbEqDmBsyHw'
        b'o/1ZjjVPrfCOLPj57byPX28fMLkh/dLgb+dvtj9Z4HLDNGbGqw3vzJI/d+37nJ7trx0c2VhQdfTLaP20cSO6V+TVmbhO/EfbRTQq7nX7Vv3GS1+Z3M5bNu509MlzEb8m'
        b'vPdmzs29Neaz9uWu+/DVRzqeD8w/83akXrfrl58edbUqa2mbt22cj3qc9OT2vHOPn9jyzPLsri058V9bOny0o+7tAxUVX24wf3X/d9OXBez6wmr9T+NXfPe24dWjFaYp'
        b'ipmP/Pq1heFzL+zfOTrMJ3L/U19PNzup+Dp8weavdxz6623fO0XNm3aUmJ18XHP9S8fRL/ou3OOV/lr64YYf2t4NudL49vzXDzmd03FdPr3P8vSIOXOfd7R+edlbvi94'
        b'Zx855PuY/e23V1g8q1ncZ6Csalr5jWfZherb3neM96p3lUf+ECipSX1UJ0G38u/9jt276qe/ueADn5/1TV418Tl5SeXHfZOv4zWybM92cQuRksl3TqKOxm52BIvdcJQd'
        b'orOJwCYB5I5n82D8YjmWQpUeJ0I7Mp1GYLtI1yUyoa7DhSV4SCoo4RqZsWTl4wd1bnAV253tfAKDdUk2BZI5cn6+uBbr47m7ArSRacNdFlyjA7ih+Qg274eiKdDiAmWW'
        b'ATqCIkZql4Zt2ptFi2nMqSlLoHEsjQCzT+qEB2exm4HLyQZXRGZtMXZvd1UIimipPWVvZDc9F+mql7gGukzDCnpCroRuymXbashp8Yr3Yflw/wyok7GoM4U72aHlwhhs'
        b'GI5xtdnIvMFD4RA/88yGukB2nrpl9l2iNOoWwbbXJmgO4meqcHmceKx6FOqhhFcrC9o9nAPhvKMZ5kkE+QYJKTdZc7lrQjsUG1OjQIirmw603T1yHY0n5FuJyMGOkdeo'
        b'lcxkmAnHRJvnaUtmNlw8mWy6pDdD1K7YGkdPR0PF9yfiUR3vfdjCHiNiCTUvFgdS5wC1cagrnMRm7FaTii6SQ9MOKOOmo9NwbiP1JDiiH+rKbo9VGvlLiSDUjE2suGOh'
        b'iXIxhrq6hPC8oMifZWc7TY5N0LuJ1diGoqeCMlVYvlF/kPktEzvZzVlu+mQIugWFuARSS0q23HijbOYKOMYaWr5nFd+oxeNwS7WRp0x3BDRzY8XVyOXMgHJYbQ51WKQr'
        b'KPSlhpiVwI/wj42Gbg01GpfiIbLJbZbsUXDuNzgcCKJdmGz/B2QCswsn4GHOc2eQxC2cpC+OSAWRlbNgHc+yWsFw08FBa6GaWo518LgE+1bpcMtKO5RuULoRCalqF32z'
        b'VQL1KrjOiUrPUkvifVbfCDwkEpVWIj+qDyUNl6vZZKOlDCXzzyidn5VXwxXM5XbbE+R5bruNhhIsZCWfjg2YT+fzoWAvrFKQAtRKoMRiD7s5mYg4WbRiR5whK5iWrksC'
        b'zd48+vmIdZ7cqr8HDnMvh364xiq8WeoueiKR6ZsTQu3+fVLJKChlVpbR0AxHNXh8qcjrKrHFS5jLLac9MrI3k551hQb/QTyHGVyQ0TheeIJ7wfQQqbuYoTqmQD+17VCK'
        b'TTguhcLt2MOABCoiOxYOd8xqIgLsXZAEmVq5vG/ysWIVkUKJoDRqPRFQiGRLZJUc4My/q82M+T0mRCkEyDc1jpf5u09i9Jt+U/EcFNl4b9+G3UZbhzhQFcKRKVgSEOJK'
        b'Xgnz1zOGRmjhrJNEsqjXOBtgod+07SqJoLtXOj0FeaNhDxyGwxrndJUc29mQ102Qum8nd2mlM9wsSY0DqZVvCQuPqEMafLUltspHQN5mtoQkwWmoVBLZm9QeS3kK0Cqd'
        b'M2YDt6ocIVO+R5sIGau6JIUlxqEyP9Nd3G/lIlluBzT6IUHUNUuCVyWmkBPFTVC1cHYOtWqZQy8zbEGZDZ/t2VgYxgxbpI65wzgrNZFslKjJXtJJ3Y3wRozIZd07lrFg'
        b'hsRZa3aPEilWJfZEX8iYzOYDlhD5uGgJKUYgHlZiG1+PpgRgsUywx7M6VHmp5tk36MMlTahqqzHWBTqJJlPTcbJlZBVq4STb5/WoXZZkf4ooYIylGnsFXt/eldCgoQao'
        b'kZivI8ggV7IrYyXri1HQgVXOQa5qV6dQssBsjjbZIIuFCjzHjdt50OnDC5hA/djU3BRJ9pxQHUEVrUNai4i/GUwp6sVuByiiIwSvQP69o2TJDCKlesMFRajtVlamderp'
        b'zL0KSndoYTXekM3NwyehF2qU7G7tWO0mMwL7ZETBrBD4ZG+AOhUlnyXLJnaGkC1OD/ulUBYOl1l7LTXyvMcqR6Txk8wy57ZbZfTfWxf+P4UuG6R36CS//oOpbL+QbiAx'
        b'lVIuQAPyf6zEUMrMFBSuw4xPCmaEUkj12CdjyWjy30biIHGUmElN2Xd65C1q0jBldxUSK4kVuWNG/hpLqLHNhqSmYGaOYd9I6I8xe5MCgRQsN2ou22U59BzvXp4JBTdU'
        b'XaWGoB76q3c42sfwv+oR+ZA07+Yz2KpLqYc8RWb+B6vYAaFzWDSzB9foP7JNbPhdbBO95A3ONjE8m0GqiWlaQwM7qXexTdjgZutEjxrdpnp6aBl1HsQ88XvpMJY/vIDX'
        b'tAX8aQwtiXhubZsUPyzP35nZLb11/GQs/iE53hjMcQIDjDOUdCI/UqPHfn8oX94Lt4zWDR7Ur0t6WOYwmLnDPNvMlKStmQkP4Eb4EzU3XKc9sn14AR4bLIATrb0mg1Sf'
        b'HfsOnvj+mUJs5H39rvDQvn5iMG+3sFTK4ZSSmMrYJWxj16dmZgyjhPpj+Sfy/Oc8PP+nho+1IRRFf6LP0/0entmzg5mNvpvZ/MAFfyqv+Q/P64XBvJxpXimxdym2tMQk'
        b'nJnhT7VqwsMz/9tg5o7hDyCg0hbgz0wrA0bssI7SLDykAK8O71bGzsCn9Z9bQlieGakPyfHWYI6jRB6PP5HfRu3SsT42mdqi1qWmJaQ8JNM3BzOdSTOlT3MTSfJQW+u9'
        b'tC9/psdvGQ+WKS45VZPwkEK9M7xQ9PE/XahhKNep5Fe+NF/IlyXKfgf9qBik812F5EGmQGrSpuYSZtKOTU4eZgKh5qrkBNEcM2h0ehDhyPLYJA2jjFlOKpG0JcE/PT01'
        b'nbyekDJoiImLTaFcausTBs0796VCSWpSRJ6apBRGAqLJIDMmibzueJcjZJil/b5ERIqgLUkaRsXzAKvhoMmGg/YEgbrR3DXZGIQOAw/KtIOB6igMPGiwV7JHsknQBvbT'
        b'kqaa3UUL3pJm7Lh3TFD70O0hUEHqDgPnoDpUM6jZQeNeLrZjGT1BcoVDU4JcKchApQ7BsnshmUMBmVCG10YsgM55nLgjBy+EMcdZrIArIgPGXSqLpViwJGyYEQIqZhns'
        b'x+t7GAg5boaOM/l2MOdlAewMeuk90OMwLMUCtyAjdQh0LV/qisfkwtQtxt5u+plqWoRz0L9ZDecdA0LcAkPMxy5bisXhjm4hTvfgl/HYsgCidkmgcHP8SGiCs6tUcM5q'
        b's1SAw3tMsIL8tP/3vaFDTZUP7JDvhnQIdVnagJW+dzlHtI3mR/Qh1m6sxnfrC7kx+lYq7E162mikTFNN3m+5bPFZzNPrP4kJig2O3RT7SUxG7MbE5EQL3c5O666aor8F'
        b'VS+vrh1Va+3skPXB+v5NozZZd1YXzcgQPk18fP34Uz7KpTn+hyVnDOwMPuiS/vOY8OHKv52bl9zjqB7tsXBc6TOK7gqj+A1GskdDT5Ws8hv3ud5LTmf80jvWXD7seTjW'
        b'8LBhrhJGGWRusn4kuS4tzyIvRvFshvB4gmuO5BWVLj9YvR5kq+YqrxqbFw9RecebybEaWqGWP1c5EwvU7nBOfHao7jnRWcfHCvr4cV27dcrgCQhW7B8akk2OF+eIRzUZ'
        b'cAMb1EEucAzrB1FLMsohwY4db+CFdBEuJZ+BLXBVAi0riRpMz/EWrMciqgXT9jdyg4IlWljLeGs5tq7GRtFX0zYxwnyIqzh3FIcsOEnGwF095V5Wh7uj4ZYR9e5Zp12a'
        b'mB5I6RX/ox64X9hpw3Q+BSNnoIEFrFiAAUrhsGv0MNViWBa/5XJ4H/PEUB/Dl8iofl9P3AT+ozZ1QKg3HapPPaQ0/xOW6433slxLhHvt4bLQJJvJH0k09NQmb9VYSlat'
        b'l/hOsEzoL9QrkFxueVklYUNm4boMfvhGutMRerRnbxv3/wZFtYnk93Izan+UuyzuUS+TE1LWrfv9FNU0y5/+QF8UDCOqfmDm/5NeSPzPvSAPDU8aeHm1joZ+3flJtTrW'
        b'MPGdZIkg91d7ShY9tf3uUnl/S9cLf7Slje9T5Nenpib/kaamef7yB5o61/Bhxwg898G2prlRl1C6kGgoOcIQXm8tFyT3wZLkGyUai70gLdAhvSAjvSBlvSBjvSDdJ3sQ'
        b'4zs9iTQU7hU0bEOZFXq8B3YwEzU1NJ/3oyZqLPZjLhlRW3QWvimYCoJfjMumTA2PAxwGTdYa43R98vh2qMNGiVs0tDNj/vO2cquFMva4odkOKyFzCvlyHZzezA72OT0P'
        b'3dTI4l8YHEo5YpcvXe4aKRWi/XTDN0MD1OMBTiFSCTXWdKMgi2/JlCA8AT0haldmtdERnOJ0oM1eYNZwPA4deJ7Z3uWCDIrwIDW+52Edc67wwWvb7lmU8QTWwNElUJjJ'
        b'wXdBlBqIFqhIV5Dvs3eVwPnE/axZoBfyPTgBiNwYrlEGECiKYlQJo+HESvHglJ4im2yQ+bgkmGBVOGc+qCHCEjufdA2UC/q6UjyLjVCCzXCUtZ/reGzi0Bt50gS5BOqh'
        b'Cat5tOSr2A351AKnclUI+rOkcCwamszsuOG/C86SDUzcp/AynKS43hmQw0qr1IdzWOQays47N1go1kotp8MJ5kBjB1WWaiwJpAy9wduwE4tY21PxRyY4z9HBYmj1GzYa'
        b'ldrR6Hd3NA4fi5JBNtL/NA6HrQa0pPr3jUO3UDbYTm5jvF4zO+fHGL7jP0tg9VqBRYYaUvXLDNHDMaimMdxZpwTyoFqD/XiEIWk4XgcuYy9rL8OpePBuJ+Gp6bSfEqAk'
        b'lflXzIB8L40OXAymQbqoBQwOytgNyDWGM5rgKRJvPCJI9STjsGUVGyup0AcHGWYQOrFDYKDBHDzM8lLqwSUyjCp2cdCkCJg8Bp28W6+kpZKBnI+5HBHEAK9KaOIeQkUz'
        b'RpPewWu2g5hXCngNg2PMwyrTlD5TYQQnwoRgktgEYcI8S5UOdw0qgPL55F3IiRj2LtSvYG03aw4SEf3aWhF5ylCngi3LVRMtvQt31YFTWMrxrsmZbIjq7Fnh7D9ZRNJy'
        b'GO15JZtSK3WwnErnbmRiuKlcg0IkXlvICMvVmbVGzanbpkCpOtgWTouoVQZZnYbtLF0XrNktop8k66WCQk86UipngzQNzq9+UHA0Cp9yhCadRGzB5kwqG07EqkyGuAtm'
        b'9k26isAhNuwdVuydo7MZWxezdccNCmOpjZxDyEbCwQeiyEIhSxdLoXYhn2MtZHrc0JC+axSXFLqcHINrrL3tPXarR5Lhdq+U1wzdfNUqUeENdVzU4Lp1z5qFB8iMpG20'
        b'YQolAyglpRAXHrrsGGA3X3faJ8IN9Vg8wTB4PMDfgSB2KyHelyR8EK/xWwybV7SZjc59uou00x/roFOgC8BuMQg73AiF81i0HhpEGZeGqO3GHMbAN3cmZpEVQSJIoh1m'
        b'CkTJcOcuTQdmbHKG49hNowkK8liy+uFFL77m1psGqbGVgsACXF1YbONj0j1YKWTakruxUAMV96LXZsYKDLxGVTyaxDa8Ck1ErmqFa1p0KYWWTh3HxgIcMPZXW+JJ7Zp1'
        b'/4KFXcEqKV/B29zXkGW/c5scDykFCZ4TsHkpnBWJcPAixYd2KGi4O7iCR2nAvmMq5oUIxfPwNFYosH87GZeCy0K8yvawm4sMBLIO2P7LOiZ5wNib0wl9y/wYBT03Icbw'
        b'X/FLRY4lJ+q6Jpg+HhBj+P5uBf/SMYSxEdneWhGT7D7Zh385QV+fbqIr30yJcfnrtAXDyYGYLEP/0yITfdKY6pNphvFCJFlIt0rjtQdgXFoRNUrJtnu0yZ/0fTYkpCTs'
        b'SEv3LdAXdUq5kLmSLk6+5pp7jLfUw1PFidCZmk8+VA1T77FChl1QYUY0fA/T9VQpatkJLZY6/tsEqF5mSe71yRj9OxY6qqgTGJmLFa5ugQxUGrRsqWtkwD29N8aI9h90'
        b'SQ0kFHHeahiDbcszqdU3InosWadVrnhIdFmgU2JshOVIObTrxSQ9M7Vaonmf1Oc5p50J4d6pLy218B24Yu79rHdoVHPTc90hYY5LT7a6f6RrO+GFloPvtvp7nQt6adL8'
        b'HyILtn0t/faRv90ss642vXFaJrtxoLDlhjAt7cuOMVGzH/33wFd7Pt76VYfZ6/bOT//TtnPbfme989aPnzr8/LuL6o3+fkL1eEiCzcw78U8E68PSY9N7LB9ZZjJqjI1a'
        b'7Z6yZJ4AFscu6V68qBr1r9efPLat2vL1ge9ry6ctDfTUrRuV3meX31v/60s+sXFXk0emZPy4r0s5u+7Rwqhoi+czyzql/m8Gdp9zd7cPOvNR3yUTJ+9bC5veyH7zWPoZ'
        b'+8+fsHbZOuXC4QnueQNPPx5xvsTowFzZjw03ZBM+eUOY2paX6Q4jZzz318yFRk/ue2zOo2E5b6elHikuPnPrHVfdmg9zTfp2L3vuUXX5C4EbN2Xs6W2c1FU1uat2/a70'
        b't4KOb4l+6t+Z/urOtk9kIwrOVv/lzvhHPZ48mvJonuun640HFiyw//TbKGGyS8aevb713yZGhH70qOsXY5JPR5lktId2zFpePyG19Jaf5+SPWj6zeFcHXsoZeXPvYR/b'
        b'7X63zVrqS70Ct5T3Be/0yFmds0H/oumA/5srHhv94b9t3zj7xFj/V45evbj5GfvvFi5OLvj7nXEfJfi65886r3tgzDOfFX9SVxJ5M1P3h7fDcwPHpn714oiaXZ+dtvpp'
        b'xs2IEz2HXl3z9ztbegI/fzRgsrB1RXdE4LGN0Zqvjf+pM/uz+SPNxq7CVOsb+eteWD93weF/3PFdN3pMq89x5ZZVvtPupI/vN3wuYdaF9Clf/JipG19z9fnrnq8cnf1E'
        b'ZOmcnifNdE9vXzF3RV/pK2u+6Hp05NxH9x8I6lvx2Tl755uhk69f/irYY+1n9eXblvxU1/TmVYdkV+HLpI9f+Dln7ePzq67++JMq9CXclLFuh71u8VTzue/VfeBbvtu6'
        b'Nm9g8dnWTiebl+ZEZWugZ3vEgn/I3x5oj62qf/Gvt0d2OvwyJ+/HMTukVsd3r/z1dMNts/hfPgxbtV+iGDvb+5F3Z/U075e8fXHOOy88pxKDZneMwk71zqnU9+OcnC3Y'
        b'1+KmcR+tgeVQqUwiUushVaC+I5GjiaQ4ApplcMLRgx1nzIdiQ+WMRCcV2cpYVM8x0kgog1PMN8PXnswxxggBV4ikxDyk6qGW3RuPJ/ZilxHUcVoI5voDfQncMagMz0CN'
        b'M2YvoO5ZWt+sFuCeSlDhvxa75uA5Tn/AHYOiMI/TgTRjTgzZtmrw9FDpCCqgiCW9cjSeUtLabA2eolIsdhfIQiFz2Kx1xWu2iXsAI4QN5jPfIBwguTAZqxQr4SwjZ1gZ'
        b'KjoHwUnRGScGsuO1pA4xmcw1CMsniuEcpk1Q0piagVglSMMlvpC9h3ssnSHbQ4tIb5KMF6nvz0TsZ1UKxFYYIG9lwxEtFwknIklMFL3g5kAlyRALOK8HZ/XwwsvMhWX+'
        b'EjigCYa6HbSHyK6m1hEMDKVwasQ+VhMHCXQxbhoXIvtcEBTQLvUgskK76PkHB3aqJ0Ghlj6IcQe57eHxoo/QYMl342V3rxfjZUPXJuamsm5GpBhquyxejLQdmsYPsLKo'
        b't1IRnI9mvD+kl+SzJNBBRkcja40Rc+C6EitiBwlUKHnKglUiyYN5rAbqpuOhwEC8qpYKululTnADc3k7XjOBNiXc0GjpKyh3xcI9nMsAeqBTg4d3Y7brVu58ZLBCSrbq'
        b'2n2spcKxe6ESWtKo+wxcGkWKfFxCtvQS0pB0C589Ew+y6MVweDHzrjHyFP0IZ4YqiXZQFBTirCBqQR+pL5ZBBwdul5OhU0C93/Td1G4GVCCyplSNF+RemBXFHLQ2GWgR'
        b'54O8FhZjyTQplmEFPQ3kVD6nTMzup54YMGPsE3jDj4/9OughklbXAuUgXwMja8ABWzYwt0XuHQwcWzGHu0NaWLNyarA8bSjNkySMDAZO84S9aazhF40bTWeFZKuWP4Nz'
        b'Z8wL5yM7N3Ex6TIiA9LAzzTos5GUZermFUGpSKjb4u69go6/BIs34yHuEpuVtlk5A/oYrwAnFTAK4c5R/dYwwAiV9LYzBye4tp3dWJlsKfKHGDlQBhG7HXCWj8YsLIBL'
        b'SrxA1NtB1D4LMVylZCPDAc7iNSUURjDYPmcigOqRbJkz8oGT97AQ4HUTRkRgsYOvkWVkJPRQygAvvCQwxoDTWMu5g9ugEHuHRgPWMgZAXqZ8NnS5c86ARtJR/Zw1YNpM'
        b'Hg34DJxmI88GD5ICpBKx+ZAxGYCk3rpq6QRsx7Msc7vpRAfsWhvGqAw4jwG0RLBUbddDiZaEbNsU7tM7DbNYrSzJcnWG0om1+IaSlZs5/SrJBMYLLnCODZgVI+Xkvhe0'
        b'UDEMCwIoH/MFKalZ30zW2iGrsYoqboJmIlmgGyRL4Yohd3zrWjfXecnyaBdK3UOqqysocUBKZPQzmMPbq2U/ViudsESGtWkUHTMdryD3FnVYHTXUlzQUz1MmId3UPWyg'
        b'z4NOFjTnIpyGEu7pPMTLefkIldX/ZzT3vefR/z0T8i0DdvbMLINM/H6SCuO/5yjRi9MQyBktAf1tLHFgnlYuEieJDfOFoqB/Sk4glXBfKU4CIFUYSh0lVhJHqZnEWGIt'
        b'Zf5WYnhi/tdQOpoBy6nvFn1mNPk0WmIqpYGJOVmBqWSsbDTzvTIgz9lKxpIfmpIpS41RJ0jpweMu1b1+S7S269x8mKeDxtftbu25UiG/pZ+xIz4hIzYpWXNLd13GjvWx'
        b'moQhJ6J/ImwRUVReoz5Yrw46Yr1CPjlQ1YQyB/yOM9QDwhtDKZkzKWk1dNuvvU+XKXcgi/vv1GWEGVhj4gJ15vy8UikdfVlKP8UkX5k5QhB1yrQV2KPltwscy2xFZGZU'
        b'MYAM9kIf5vG7ULAkHWq1BqHRcFoORfpGKhlXTLsnZ2gT8cQWlgq0rmeJkBlVDGcGE4GBpcMT8drNTjq2wqU9QyqmheKM95aTze0wVuLR8QyNs122zpl6EYvGzmVptIVY'
        b'4C1KSyQRYiz18BSemgi1rvzIqZCIX3VDMUSG+6UR3ltc5JnM87NzBJarsdiViEXhLK1p6ZaeohWW7LoTFcJUbGKRDnYTKfLG0OhfPGvHIScfa+C4Htb5mBhDMat7VIb1'
        b'b9TpONnZKqHZKpMesqdCHhRq7kktggK88AqUTuG1owJQ4n49aHTcm4QrfeSaZjKcn/3sxbVh/Snm8yzqat68/MOHK96budXGFMbM9xWaggtNzcwWjSirLct9/Inkzx3T'
        b'p70Uc2bt8Y3ex/VeD1noX3aofMo75ueWL2vUWzbh2TcumzbWXN/95fWPx9bVPVP3zVftja/ZPFWXPV7x8Z3+xEMv/eyFXS+GP1094rjz4t7yHx77usHiq9diNpfM9LMJ'
        b'HBnwyxMV0VlXXsu58e459ZMh0UnTXJ968fDmCep+l641A+lfqJ7aMmPEqM3u//jXWoXLI4/r3tLbaG87feze8s//uWH1PI/PlRl2af5+dpayoslWbc9nPGZ3Uyci4sPR'
        b'upqSuoB9t2quRLS9GB/y8tHa784EXVZeW7Rjgav1iv5NZX3eHzSH7rv9SX+rfuSS3bPG+75i8+3q28q/PZd0Ydr7V/Jff/xEW9Ox88alOvOjzsZ/NuOpHz8pcos1b45q'
        b'GPVz8q9h55df9vkhyfxUn9cG9U6n5ZMzw6YYvTj1/BmX89/P73WsTd0b5vBPz/c3+PpcNMeLLs//O2dJj/47u+1HBno4b94OW5pkn36/1vz21JGnQ3rjpxZtmqJxv/jX'
        b'zIJ9n1nMujFy8hu2u8dlXjT0tTr8mkWv9dcSm5Htp98/3dbX/suvV0+NMSpx/fVrcMgxXJjeuPdykkfdhrxK/bn2e8rSPjj52KN6Duf+mtta0v+qwXb3V7JKPvy25btX'
        b'65f8e88bT1nuHv9u8uZda69s8Nm+qOqJjxZ9OfHOk2cbnSPnbM+riins8/qLRWaq5LrRltvzPG+/pdr09RtfVH3efd6g/ZngzD1n225HH1m1f/fn7zz6t3c6ZnRs0vdp'
        b'f3HusrAfvjl5Oqzp6fbbo/o2X/He+PqAfMybqr9+n/5x2v5rbfaX5+ydivt3XfpufnVf0id58XvHr1n3Yd+FinpNcurm+A3Nnmb45c78OR3P/WKc/aRiZ8HJac8ar/D+'
        b'fOrnU2+e7Hznw/E7V5ltnl6gcstgsUKOY1sg951+gHc9tIbddbDfjec4iVVpPIU4OIuqxdmp3J3/lChw7xy9VK1VHKFhBtUd8STUczH/5Bws0oT6OKm2DvMk18deLjmf'
        b'i8ZuZ1HFw1yoo2reLOjjqlgJnN9xPxEsNbVD8xK8CNmm3F89FypDRAE7OnRQxJZ7EfHuPHOKH7fLXxuKAhtXzYM2Iy6iXBmP1zVaX3nMG2tPpCyOy7G3xMNaGYVWnAjV'
        b'VKQbh0flzj6UxC2Ua8d5NHyxEg9iM9E2SsQaKs2lmB3sz/Po8XWjCKatKrIdrdPZLsET84ALdWRRbF6tUUnIwlomiF70lRLW5PqQu1EDJcEiKSpFNRhsl0KbxXrebNkT'
        b'Vms4yZMM++AqdbKn59UcbXPKEsuUbqQTpSskTnjZG89jO5epGzFXRWTqFGwWeUrTx3DRuXnNpGGQDON4GR6N8Cejoo/18W6igF5nPK1ETNezoFaRg3jOiMlrizAbyodp'
        b'Dlxt6LPHa2SQVLASW2EDGRZadiu8tJ6pHrG+3Ak/GxvxOvWhN8eGe8mtdMYzmdEO+7BPM1Q6JnrNBCxO4A1SHwm1WlpBC2inegHmYBVXiq5iDVzR0AA+1PNDtgQHoEVC'
        b'lNcmKXt567JgqvEXU5uFLCUFiF5QQ4p+kvdw/ah0pRvRCc6EpPOHMkj2Iyxkm7YTBZ92o++2EKoz8obTM5JGQV58xGoOqmmGJqIadDntuMtPK7LTZkED9yg5AYfIAB4K'
        b'/dPi/sLDsXQSXmUpKXbDQSha7KLF/g2RiLdDEytHKjaMofYXNpfgrP8SCR6YZMi6bx+WGSu5ckpqcJIrqJ372XAZs2nGIKuwtUyxTuqEzWbsrfnQBVUiL63cJ4XhJpKw'
        b'gbXpSKzf5+wWGJByD7cy1o1nbixT4IbNXRmfJHREzfQqkkeC3A5yxXF8ZKJC6+xCFL2ZUuzxXQ9dMRymVexCVhnx7nBHmCg8i61E1TzGNewTeI7k0jUVO+j4Ir1E2SwN'
        b'gqVQij1mnO2wwIOhX6gIAoVDDSVToxSk+a+Y2+lmqMiDPhoK2xu+OlYY3Qcs2efL5s2+FCwfJgnqCsZRMv/YaXh9O4+9cpKMwgq1Nlu4vG+IiQYLdKDbH/pZJfYSbecC'
        b'TWsJUdTcxCChMhlchqsTMrdx/fECXtzMkZauCmGxOwVamsF1ldn/R93nf0XhNpSizUjrutL3e7WgEVQX0WMoE/Jfaiq1IpqIFdFWLMgP0VaIzmLNKNqonmLGNBQ9piWN'
        b'ldmk67EniV4kpegUY6rfEF2K6jwUbcI9l6QSdkeqpzCWGTLfJgXRmyhShaWp4GFozEgaPEc9mZ70frQG03pEDYc7c7z2vwSdiBqO07CGpObt3+slctDhoWATVnyVNHSR'
        b'yvqBlGuMY41RrjGitU3k1y1dEWRxy3Ao6uGWcggCIX00fZq6aaZH01+z6S8asPWW/qBL9y1d0dP6luFQF+hbRsOcj5k3GHNDYg4yrP68uf+PjwSGeAddJmXwo5468eRK'
        b'z1hOlG6FxCGRcbZJ/qe/paYjDWWGMqbUxGE1NNyrmKZgqUQYhefkCZZwZJhnFdU4mUMUbXtGS6blXNLN10vUG/Szkj7UzypnqGcF3QRchXv9rBaHZoaSz8b+Iz2mTnef'
        b'Mc3TgwgnlzIy0rdtzdSQpfkSkaM68QpZrS9jl4kenEgyNDDWN1KSzbiAaJjleDRsKZZhVaQOXe16lUoohbPcJeFgkicditMEZ9m0BLjObMn78QDkeJDc3QVT6HHPIM/S'
        b'4CEbxmGph5R6fUyGEg9oMWQpQIepv4dCEKYLsxdMXwQt3PuijggFLR6ksTwF8qnJ0xU7WRrz8BRUeZAunkH2l10zDOxYhuGkDsc9SJN6CYux0kuAKvYwlmKOgYeuIMwU'
        b'NkPPzJ0R/Nv8KGyHLvJpluCZMCtIwuzAevOxi0iwRK8ViJhxYrYrnmDFc/bfS9txvmCzfT4chVqWRECEFbWsLhCgHI8sgNI1POHmTF8NqclCYSwcWmgDubwq9UQma9SQ'
        b'qviTcl7zJ6JCL694i66RhtRkkQDH9izyMMik5FuJsSYaUo/Fgtxz8RrIYrWLioFyDalFgECElvwAXTzA+XNqoBUakFYkUHCzDgzBMvb4TLg+gSKfhSBhxMQg8lQ5ZzS5'
        b'is1EvOgi5VYL9iPVRH++wp7HbHkIdpFyB1NC/crgGbG83Kfx4nbsIuUOoRQJh0ImQ7b4/MY92EUKHiosSg6FWsznz9+AK1iNXaT0SwRfPLIEOpJ4OZvg4DLsIhVYKizD'
        b'yqXQt5M1F9mfa/EyNWMvE6Jslo1wZU+rN2KRkhR+uUCl3OWYB0dZaxnrTFJKqc810Q3CsDWBJWEEl8OUpOThQgBWhadhHisgHLLBSiUpeIQgmRSBN7Cdl6N+40glKXak'
        b'gBXYEknjQLEmT/J0UpJCrxBWJq2YC/ks4eCF2KckJV4pOEDXyul4jde8zSIAisiHVcI0u1UwgJXcheAGVFEhgZQ6SpBCdlT6Evb9RhNohCJS6NUCnnZbTQSR6yzxHXsV'
        b'WEEK4iYYYbUb1PDRI9sIRCZhcamSV06B03NYtV2wbx71M58g2MRN2IAlvCZVS+dgBUnYmdT7oDO2Aa9hGh6C7jBS8UlEwtkwiYhWB3m5u4zHYAWpzlQhCrun7oVrYoNs'
        b'oadiCur3gMctXCDfgtfnDBlnZ8NICR0EEzzhALnpKhd2EoU0JkIes/MXORMl6zQFy9MYkDLBHOuIzrMghnnIWNqPZV+TX+l7ZXAwndy+SFWiGilnOypUTGZpkPctM8UH'
        b'6Pt4PJA9QNTherhCXqdPyIjgv0qwmEQTOE6agMr/GofBckzBfvqQGUmiiCZRpc+TaHHHA7wUU8jUvkgekQoW5uQJYRx7QGVI1CCWwBS4CDf4fQm5P4XMO6b/EMFuoZiJ'
        b'LjSkwxnspKBwWo5WMiyp8LfCx4jk4RpOH7HnrxPlsIe9H5tE9HOxlkjnRpHMTmwIop52Mg+YLQofZxrs7GC6rRT7N4vNAA2b2d3VY7bQBDyS6DP22gpeI+Vjrdg9GZud'
        b'WQ/IoMEH6qJ4/aAbcphHBRTZmfHy065oMpmiu14sP5lWTdx3LJeMklbWTOSZbUFTdM14LSKSOaMp9GMzf/9IKvazqhTx/qb1yJzPnH12YC3z/iD1IDWrBVq/a6RPoZk8'
        b'Y0hGJ+2yCbIdvKrkZhMeoI/4iMkYGrMGg3PYNkbMjFqK7ZxpgXmL1GE/y8ptx2RtleB0POk77fBjTdMwm7WbdOsckoQdnpNBNnami3fhoCmrs+uOfWImsolzaHHSxVbR'
        b'xLKCwhXPRG2z5pnTB3zEns3Dw6zlFyfMH2xXGR7ThUZtZZdvY1nsh4sB2kbVnYBnoUSs6V4v3uy12KTH7863lW6CRrGaznCDFSEZm+14g2ZR5qz0NDhIMjhKnthNVmFO'
        b'PB0HzayI7AkfrMc67SS6vI/NVqLOXojRNmc+WWzFsahtrY1QzPrYJsVBW5vNUKSddNqR3kw2QqbmFDo5kBt942ie2em8RZLHs+Ji42wywXjikJW+CXO1E75adG8ka2QN'
        b'nneeQhaNavqUTLDwokWt1WG9ipVwepnY7zJonEsWzmvaNYHM+RzeL71wGSv4EJRhrx99yIevC/GpLJcReGMiL4azMvzuhMcL/iwBJZFmOnnHw8HZgjhIWVtMGcdcxXZD'
        b'A1xl1ZDaSha4ia/X7uPrQTdZEa6I87mI0smTV9eLQ6MniLfECZlCrIdzElzSxYPaMe6EJ9nYWUV2H7EQmEUqsBayeRJQsYO1BZyjOx97gqZTBu0sG3HhaBnB8vGJxtNi'
        b'PpSJ3ZuMI7G5VkMjG2KTYQAa6d3IDDrMFminSA/WqCS8T47DoSlqFmo4wFUatkbQg4tSyCL7wMdMlixN91MZMAOJKlzmpJQwA0lw3MZN3JvthaVGUlMJ0XGWxgR3LtnM'
        b'v9ws0xP6JaQaMTHJxyN0+Jdn1pvrvSKlnHExa44s28q/DAiX24Vzn3JDv8B5/MtLq4wdbKUzyU4VY/j9WNFtboOp7qLvmTddTLJdgPilkcOI5WckfmTTiwleOyuNf1ke'
        b'qvS7ITgKgmmM4WPjQ/iXX2RYLAyULaUZ+Xxqn8i/DMqQuz8rYbkHf6cjRktUR0rdDvNquui7k3JSd+R/7LdyuEkEAZL72HnbpETfC1/EbvwwWj51Lk8i+ck5OvxpxQLF'
        b'8i94WV3Gmk0XPj5eQ//dnMsysIvXlb4t43d1IycIH3uwf9/NZdv0Prw4iq5lQqoAZVCaGubJRIDAtdudyd69Q8AcqNyhF8f9gcfzCXEB+7TDDbtXDhluc+A6y3KbidXK'
        b'WRJe/Gzv/byi7ydaWrdIeZMYWkwf7og4SB7JXFRFV0QepXAwOmGiCMq4pZOUEp+wQxuc0FD4reCEHgZ3AW7UX3AZnCT7eyj1yWXOfiHBS/DoA5GFZGcu1KILL+Jx5TzM'
        b'TmOVyB25MnSDECMhQ212uvcm0jGhoUmnt9+UaGhGM4Ui/+UhS8yXWVz/KuTvSc1Nrgk/fTHZ6ZDdpmVLJXPHrHi89NLG9TkvB3qWmioLa0p/jjy9dWX10yYx00LWfLd5'
        b'TU960pqu+A/3Zv/lsQ+u7/6q9+O3NG/5jTOdPja+1N/Y7VvHRxaMmBR86rBBa/VCo7Cvly2WhXQ/v0h37QncueYR/zWQEPy+wYX3RiemjfOaWlTbkzvrjcf/9e6JBscx'
        b's8puNS79SqcsKPyDwy9nmc9a7R7xrfGXe15KOrGzudh9dnr559WHzRNWvp9SNT/BvcO4JO3iko637qR0mo1bdCF8t+t7Lhv2bBphlfb2W/Mn+39R+8Zu95Sp9jMtW323'
        b'ZASffHPiX40/Xvnjoz86XE5qtyj+t+EZ+x25ukkfH1IFNOu6PxYzOf302P6Gzorlx66efdSt6la8Q49p25teM+Y/l17zbWje5OCayT09XwR8YV71XEp0+YLnQs0Xbm1+'
        b'0saq68Xst8xmdc/vGP2MSUCn/KfG3DY4+ui4inecy1fPfsZ/1Otn7f7u84/zzhEX0iyPLFRf3vGKZdv1eogs+dbqR5Nfe9Rr3SvmTXn5/dzmkuAiq+c2vXtzy7KB1Zje'
        b'PvenlR2vZzRXSGI9b3Z5RZ51GG2w7XTX0xZWxePbbP/qeXL0plifEZWpb071tQqec6c44qV3ot57V//Vv976W29JbsYr/15WMDr2lemT9jl9cuzElTabPe+cDT/SO2n3'
        b'K/OPrj+SeyNhnd+/ot56pTnTx3xPrUp1y+nq+X3tTx528JpW27jv/AivHlVP3jsvzeqweez7y4trl/3b2cjy5PuPfezj9ej7/k89P/kzo+gZT2T0lFXavVfyizpny3dz'
        b'nV78PH/TuVfDzlZ+9c9Hfoqwef6T/D2L31u9v84Ab+zyfOuFF19XGYkBo2dCBz1V9cJLZFjrCDp7JHjGDBq5deGAgwEWcbCjPEDiAc3QpcdDQUAPDQqlZrF21WPgGA1T'
        b'ocRamRRLXLlzWyN2zKdxS/EqURxlBhI8OHoaFvCIRXg1er4zlkB7kI4gj5fg1TFwzRSK2T2zyERK9xY4b5FLoFxQbpMSYaATj7BEff3CtEHo4PQu7kgGxVDPS1s5M5ok'
        b'OoWURJ4pwVyiCBZae/Lj+wtE0O0mG8xdRzHMN4GORdjD0g2HgQCGuxib6ET9uhVSImmegxZ+wnwYb8xVMw8VkvJIyWprsledggZmD3H04yHKsW0Gi1JOhNXjLMsRkAsF'
        b'Q0IDsriAULN/g5lUNeb/+KjpN48D9f7M4estA01cbMq6pC2xGxLYGewAXY1/zxnsfmGrXGTjefCPgZQz9BgwnxJjmQMLazGaIUQpRpRy+RizEBuUJ4j6oHA2IDN6Niuz'
        b'IH/tGEsQDXBhynxepMyXxYD9pV4wjiwouPa0Vk6eN5W4SdI/GDwGlN2SJW3ZMOTA9Y+00YeDniM0wbfpuSo97Pwd56r05/Toob4jTLyq24vlZtAwfPPREayi5XpE2G2O'
        b'k4l7Ic3TQLsX0j1rCBpPImKgpIkG4imdrECeLeyV71JQ5FOYQLnQJcI+2T75g07p6D6pL9zP0fxg3CW1D5M8pYnSP4u8lN6Xl04o20NfNWGABuGS9W6XTsc1QiY1tuAl'
        b'7FpHJccVjiJWzzEgMIzGczwcqCN47VZAfZwjnsf+JAuLT+Qa6nryUtVTTjafxQTEPp3oWP5JzJpHLpVmlTXkTMttqeko7MieUJ3lMU5I/Zvi74/cUkm5P+hZiaFai+VW'
        b'+EjtIGskXvDixrcrPol4zOPBNma8iB1ztSCIBxz93lLGbUyI27yOCSZsLk39/XNpvxDMQ8vsGr+ORgJYRwlw7jpMDUlZO7IlSUPGtXTYyP14cOR+RD7NMhAjw//OkXtA'
        b'uGk8dOxSghlsTZRTMtATcDXUNYAsohwmcZ+jk5oS8mGJAg4RHfBMJOU4tVZiHVSnMFXOAw5gjdol1Jt2wGG5oBgtNViIpRx2dA2PmztjOUmmKlQqSEdIBCgeyQbLoigW'
        b'bz1giVFM8t4NYTTuNV2uPaK3qYN9o0JDKcxLb4lUAydXsud7DZQUQpM2a3xMcMr+fYKGHnN9v8Y5zChtq95RmSCNlAgzFUxsPqFgmD/TQ4tiDF+2GCkk0zbtV8ipJC0I'
        b'ViUjX195dqWnoKFisvX498IiMjeG/3O7TJDpSCZt41G5VbtYEtb/XBTjYh/vImgolrbYIPt9aUgEhTIqD/3Inmvcrkvn38rFE2OIxBPHn/usWfW+zk9xFIBrHHhGQ48F'
        b'X/nlpfc/JJ3scHGlYF03gxE9BOiPD4sw2maUFk4EWVfJZaNKfXcNbTX5pRhGmNriSL0czDtkvh4fLHZk6zvDNufIW18ySRi46XKTzCBdidT9uadYvpMlXS8J8gJSekE1'
        b'+3H2VcGjDi/JP/hJEJwEp18/YF8998njRZLvdwnCWmHtq5asdNkOXxa9QP6+V2Qo5Mq/Zt9p7rQUvUA66P0MHSHvLX4SZ0gdTbEoEC5CNcNOecjJFl8kDVoyMyl6RJpE'
        b'00qG5kyFjf9y75Q3/AwnbZj+4uFtv9z8q/OsJyYYjrywp+DR1TN1ba0C5fJCU7nbzAOSSV8nx+5QjvfryzIpt8sP/NDpg41Z00e/980335S9V9ebXTxh4ncvLbYtqB47'
        b'b+RPReHFpW/krK56oyBeEz7R65OilrPrp3rv2VHikPtc3jMbJ9tO3jrvw+tvzjfzbN1XE2b79usDG05NtTXw7dNv/CW6PE6dqcwu1HGOfuFg0U1D67XSbd3JH7YZdHxQ'
        b'bjz7pV+fvRPb/1ziP+0f+3SmJnq6qXPEe0FHGzcsuZA97vu23uy06BmXvrJ73bq84vMf19Suka3+4UPXnz/oHb30b3sufLem8zlPj18j98if/CWu7lpKruxnq6gC5bu6'
        b'V65tjHlx57hXGw3fW3inqjVyyYHOcZ/+48xrZTN1Xx41suLOv366E/h1+JfB+xdd/CD16ZPrnjv5nU+D8/S2C58sXPuC+8+Vq1Ke9eh7z/aN0jm3jbt8PessP97/dkK4'
        b'Exjf+KU371djO/cS9aZPF7Z+fKcy8uc7B94Krv5lbOvPm7/51ebCO9lPT05xfP2XhJmxz15dXrz4u1+m3vbX/yz/c6lXoqvnZr3xv0qe2VufLtmrMmVi2bT4uWoVFkMN'
        b'tLk6KgTFBqkTdmxh0ud6IhkREQnasF/NI8bpQak0NWCsiNDASyuov0SIi0RDhu00CbQTtbKYebdIt2MOWU1WTKFkG8UUfaUHDdJ91lDNPd3zHUZrMrAtbts2I2MoMTGh'
        b'bOZk38STMqjDKhe2rOti/QIuheKVrUwQhWtwdTmXUM8qaMBB8sVRaCfZQY5kMQ4I2lCknXDaOQiLyB7cysRCxXKpxU4j7uqUiyehgcuLZGnqZDIjkRgvSfnty6lrnIPW'
        b'QZ+rKP/qK6WkpleBx6+cgwPYRl5W2WK2K/VoUMRI7SV4ie9DBVCYQh3nz8ykUAuOs0hVMHnTFQbCKf9MQSANMK2EDikcwRtYh+cNWaENsXmBOpCI4wUhYlOvlSbgQTzD'
        b'Ug7CAehjW9xObBd3uZH2ozgDcjWp5hEGS8UG32AV6UNvqQWegIH/0hj9Z1x0h8mhd7c9tndW/5G9U22swwK2MVnTmMiWpmwvpaHZTCW2TFqkciMNrUZlTkPGG8mZJ+mT'
        b'VPpUMCmTyqtUzqRe0VJyl/lFM0u/QkyfSqTpnwxKmDq35GmxGRtvyeNjM2Jv6W9IyFiXkZSRPNR5Wff3NIUs/TZN8zP669PB7ZvmM/MPb99P2twrenoQoekQ9s5nhNB3'
        b't29dwSpEboGdq+KkorxGyzKcZ4uahiWDPFtSZhL+bbD9fQQocuF+6g2yfdOTRAuT5eolhjRCeuEUdhZIxrEZXJXhQVcsTXrq08U6GjoXjL3LPov5JOZ2TPBz02M/TzBI'
        b'fOdpQRhTLgt3tBnC0vEwYhvaKcMHl8sfGVz7BaP0zwc7XM6757PhjhxD5S/pvb1IX975h3uxcChzDffaPjEfmoh+StpreC9OWqATPyIcilz+Z/244d5+lN3Xj7LQpCd3'
        b'ntJh0V3OFh/ifZS8IDlxfXxALKe0Gf+6LGDS+t/ZS5r/tpdM07+4t5duP6yXbg/vJfrynj/cS3nDeokaNRyWYbtz6AM6Cet1xsliNlk9uJOobw2ltCManjxR/me6iXbR'
        b'/fF3DEIZ8YGvxyi1C56JDr0reI9W8UNuQ5voQPkdPSHt3f0zrRVqfsg9jqtnaZGpycsz1vLD2w8mCvTbHcJ0zbrP/CbxOCGqyX5hcF6gnGsCFmAenJzjyZ5OtmLirunX'
        b'btsNpXY7BKYAJELLvDBXPOYcECgTFKukK6FPMh4OJm3fG6KjIXKm8NHOmnFPexvDVIuFL9Rsfeqi75OK0tfmH5PphAQ5l72Y5eh40tnrSN4k293N1d0/bHw8Yuk3x16K'
        b'sF5VU/N15QQn5zwPsxkTBxLx/fR/uG1eNr+8I+e12lDHtWM3/d3shx/zXvnZ4L2vX6j99TH0/fx0XNM3bUt+nh49bctclaVNk1+ISo+5P8YbWzm74mFTxwAa1gCOS12j'
        b'iBjCrJ4dSXCOHgLdlW6I8NCQihVYzXZtM+xcyawaRMxZQskZDkvh+ljIMcUcJg544xkoUA8FTi6FgZ37o7go0SCdDW1BeCmcgU0LJTSmgh32Qj7HOLYk4nWRTYSeae3U'
        b'p6daucCDw0MtlBg7Q6dfADuckntJ4ALmiKGfiVRTi71YtI9idodgK/EYFN9PtiV/uH/TLUO6mqbFJ66j2x6bpn5/bJqa07MaYxG7ZM12aTNJ+pdDpm4kzUd+DwTovoJK'
        b'07+i70RqS8aS2P+HJ3C22X3nNCdHRfJVNiCQbJi0SX3hJIUn58jx7BjFsHVRX/yrsZLcE0pTVmlYqZsojZcWS9i5jfQue02iXrwsXp6jJ4bHpKEyBRokUwyPqc+uDdi1'
        b'LguXqWDhMvXE8JhG7NqYXeuzcJkKFi5TTwyPOYJdm7FrJQuXqWDhMvXE8JiW7NqKXRuxcJkKFi5TTwyPOYpdj2bXJixcpoKFy6TXpjTgJ6nVuHibHD0aHDNRSBiRLZRI'
        b'okaQO/SMSp+sXuPjbclds/gJ7PzJ7pZuSGwKdej7yXUYFyWN82i7hd/iQSzviR8oYevzsAVz8PSKeh8yaiDRbY00Ld3h9AeXTvlvLp1icMCfsv9jZMBhJbwbGfC3As3R'
        b'OcFDAdJPtiygHEti6cJFtolJyQ8IBzc4mugYHvTLG1y+bUIzqX8n1mOJkXOAGOJqiSuLNDVlWQCcxwIXIzzuJhEWS3S9sGw+o57ZBhXblWlbw8hN7ZPhevT0gCgMcBgu'
        b'aUOvx9nqGULlam5mPwWVmC1GXpf7LoqUQBs0zOOMK+XQvFIbVN09gq5tNdLdftDGBLlp43DAOSgETmC+myuNJ+EsEcwny7AWeuAG2yR0xuIZtXtQgp9UkOBFAa9aYiPz'
        b'+Ik2wW6yngY7rJMI0vWSaXqQxXlwzsIBRzULPQIXrUIkgjJVijXYksFcEJJ3AvXBKV6Hh6h3NBYFkyeMsV42H5ohl9nT3TEvUw3nZ8PxgBA3Vxq/xMRetnLTCO4EUTke'
        b'S8QzwJBAqtXpwVXpbujBKzz3G9Bsrw4McSIP4Gk9KTu4gKxtozirS5lLkjqYsguNh5NagiEr6OLQtvNQTUHag0wD0GBIqZhyN3BftbaJgZTCKRyqFIzBCbuX8iyv2eAF'
        b'LNLyMxliFYX0XsF8bjBvSUkUnfJVo7Bfy7OER5zYIVaKmp1ABaQGx7jorQwSuDNadlpwmICVMYyzCY5hP9uW7/jzZwdCY4Kr1/vRszRm0c1PCRxGqwR92CDhxEpwbBd7'
        b'9e3xTCjYqGMSE/yN2kXgZGO9kAUH1IMUT1CF9RLogzKsYveT5+11xgKivlZoyZ440VM6NrBhFwQlWOTMmJ52xItcT1DoyfiMMNcJcp2xcOtv8DLpJMp3sUyMdkKZ2g16'
        b'8VJQCFMlpkjJeDglWxs/NilSN0JHs5QsIz/Y5ewt70/BqYb+gTUdYz/+5cqtt5/Qzfj8rfNFIxscl5/KrlgWfdt/VNQH5p83vb3q0LLxfn93+dt1eUtb3GsVr0Z7tkbt'
        b'Wpude3rfWz+9ZRz1jz48bXX+4FupJoWPKdY9Pznaa2V29i9fZLUbzNGdMe2drs6Pw16JPzVvW/vqLbvXPl/zSXjGum6rup+zsr4Lf6Xhc8PGrxbPPex7ZN/EFNv+uDHu'
        b'k18ctW3laTSP/GrbB1+rEjK/+kvDuNqlkxU2FvVhWz32xdr1b1ys+PwNP+/Lyv7Pw8/7PP7lbcvPPvD5ojz9o/DqOM8Nl60uF1RsuJqx5+OU5RfuOEcHfNRXFhXg+a9j'
        b'069N+vzK5i/XjPrEtCYk5e96CRMqXw0OLAlt3RUXtD4o4s00q0Crx1zKXX5qdFn5q3/gXMdP7Sb90uhi9+GNm2u8litb6iv9X0sI+unsGx+mr3v21/WRo5Xbn9//L+H7'
        b'+Krv2/pVo/nhygARcnOctZLHSj0ie+hiDZNaRqsgVx3s5Bbgsj6J3lYmS/EMWWSuc0NeF5RADha5hLIT/snbycjEIuleY+hngssGZ+gQgz2lQKN4Es+iPS0Yw3H2N8Zk'
        b'3ntWbwBnB4/rewI46KwFDmADtbjQtQ3boYXJvyT7TpZPPPRCPdnp+foGWXPpeqOR4nG4sCSDHh07+/kQgcA0mQHG5lnjaY5SKoCzG1hIJzdXOIgV4spnhSfls6GAg2nw'
        b'jDtRupe4B0kFWXI0NkoiHTGbnzv1GUE7Y/gMptwD9TiA5yVQOtmA3Z2OPSvozRPzteGXaOylODzEco6Gy0uYAalYRmbU4Apo5iWDBn8o4PJk+egIkgKcV6q0K6DZbhlc'
        b'3RHPmS/m/j/evgOuyvNq/HIvey8BFRUHygbBPcHBHgouUJG9ZChLxcWQvUH23kv2Uoa056QjbbrSNsMmbdP2y5c0aZumM03H/zzPe0FQNNH0/5VfKtz7vs88e5rzyRkJ'
        b'xEkntuPjbMcZMCgIjQ+wGspYHxtGBW9AOR29irEYmzHNTLj26iPn58sMxEGrUGdAJ4IPnhjBB69MkJIsRq80lCSJG6CYv+tyAYXOQoxm2CaxMmwroXCrkLwzCDNx7DJy'
        b'tl5YoBja2CHBNOy04VvbEqFHDzCSgVnYbcl81flinFyNLfxrZ2i3ZqOX7HSXloBTPyxxhFxI4xk96tugQtDPlqEqNHulyD5JQStGmut4hG55lJ21la3HPNdUD5fssXQR'
        b'ssHua8eyTkqOMPqY8mjvksAMdG3gdwVtMOgI3O9+al6cJFVBXUIsrgv6TeWebRNSetkchIVGLkMvJppbKXOxXJW7YhVlBJMaS4BR5cYy9sPS+5W5c5eZx+RlVGV1eSqM'
        b'Mm/yMv+p8KMq1uRO3hd5XlkmRVMqLD7ZwUWaQvPhUp3+y3t0xcKrZkuO6S5TGHa9iMKQKvq94eK0maeW+2UbN7wjem7vhD/SyoT2LAszLHRm2cD7oUjF0sc9Ql6mFYu0'
        b'1YDChYTI8NjnNkf58/yChOnnm6Ow9wITk+JfsMWBtJ2A7IUg26DnTPq3hUlNHKMDw1mn48hEobP1IdtDC2fwEt0c4r2ff/7/WJjZkLcviA8NiUyMi3/J9jPxszLPne1f'
        b'C7Otlc4mdJx58d1JD1bpQkxcSGRY5HOvlBVaFWbdwhuRBCYkGgmvBb/s9OHz08/3mX7O9JKF6TctTC+89pW2riBkhz1vZvmFmc3mwSpxEUoRfAlDvOT8IaFBBCrPmV9p'
        b'Yf51HJf48y/XD+XO/IHPQ+hzplVdmHb9Epj+Ko1YlBasQc+ZWGNhYuPF2jE783nVeOnk0rk5G3syHkVmIR5FlCMiJV+GlHwRV/JluJIvuiWznDtivnvCUgVb8RmxLy9Q'
        b'c3zenHBm2ZbqHL6uRITyph6JEQRai6AsPlToiZPIWn/ExiUu3y7+i0vKZ/x4tYSXlG9ct+KjgG//RiItKs9Kyue+bSojiCKTSsB7kOIQ9HosqOpcYMVyj2eUOz83n53L'
        b'+5d9eWHitsg8Zd0851rY5+OQlrDw0MRntQBYpgI6W4aOijRl8QWYdaroD4troSftFfEc+4pgHJUKdFhh7jp/GvNNRlZ7Pg5p4ZUiYFZeBWb9E/5rHpYvESpF91ocmiDD'
        b'PSzua70+Kr8W8EFAVNjHAQXh3MPymki04b6kq+HfdL9MZpczJmFT0EcWXa0Sju+xM/8i/0v8+Ze+ZuvnX3NCaOIS+S126VUv9ck8fmJhUate6tI/0Hzy0kmHcX/uncOg'
        b'7eNLJw2BXbqZCuaGy0rLMmEPzkAH3IUcASZkNWSga503N+xcE2PRfkfhNVk7GRj1g7LI6vWfy3LHTtFNz4vhzsHurCfKe92hEeER4e7BroGegTKfGlz8ZZVBlIHPmf+1'
        b'kbO7FCYSDTUovjlg9lSc2fIxZ/FnpJAjFLV6kWvboqqgLk7Reurq5mde9oqemFn7pe7mk8XhZcusYHmCzB1kQil40YKD7Ev0ffqHx1M09TCLpksQmD4R4aVG3gSjhMTI'
        b'6Gij5MDoyJDn2GtlRMuxE3nPE45ClonmdZEiPaOp4pL4lum39kQqvbNDNuECffMnta9/FPD9IJP3XQNVy7TDPqDfLbQlZe5HvU3dAw4kDOuVhJi+nv6pr7K7fW/Uyj3V'
        b'UQZ7DOpq8vZFGegNWYWI8mwsAs5++xgafb3kG41Q/z1vXYXXJbZVdhLR6x8YONjamipyHfwAdmGfudSDccqDKZ3qMCFx8scewT6QoecstehC5gUPqUkXW1HasTcPyiyk'
        b'JtIkPw+phTQZswS1txHbIc/cFZpw2GOpzffIGWlPG42jbtDPTQ+3sFBqfz2TLFR5HMQ0M2kHAhMcZy0IXI2E8JRebF1pjrleLnBPViQfDaWQKd4AU5DBw4/MYPqUG31l'
        b'IS+S3YLNhjIwgtNb59nFF7muFCMTLvBb5Qhz5EURZqdQSo//x0ObWYEJ2UUK4Pzwz+Jqy65vCZNTpBfXvRRO/Vp7WZ10YUmmOl9QwoH70U6zY5KQRhbPLMjxb7OKDorz'
        b'esQjxXmR/pG8IB0/khcE10eK85LkI8V5YZDTB74h4TS+etvbRbTnE1pYMdPc3ekvRVlZGZNzX72cgrqKqlhwDwzB1GGBVahe4VCqDEVimN4Lo0s4trb034RbT/r+5O+u'
        b'vCsKERcyj5hOti4JBV/a30dvMK+hSojqHUXm7QsThSpy/5oiGzVErVCGx4Kr0KiyIeohGnxUpYXv5Ehi1QzR4p8q83WsDNEuFIds4u/o8Ld0Q1bcUaLvVeh7EXvirgL9'
        b'rAzRK5QPMebVIOSkXTbUstWzNbO1srWzdbNXhqmFrAxZxd9UFUamH8W7SrS71YWSkM3cxynHHXGsV4x6tgabL3tFtl62frYBva8ZYhiyhr+vJn2fv31XIWQtvb+Fz8re'
        b'1OBv6dMbStyTyN5Q5ztcz3ZIexCHbAjZyPeoEaLDybzJI3UpzNM/geGh8e9te7Ldn4PR0icYyad/E3jXv8U8gLn+AhONAuOZbeVyUmT8E536wkhW58+H0FfBiUx7i0xc'
        b'0pTvCQ+hSyLxlLh46VQLswQmLCg/xIxijQKNwiOTQ2Olw8bFX3tiGCsroyuB8ayz4549T7sgmV71xAYXeNmhoyccrIyOxMVuSTRKSgjlO7gUHxeSxJe7fqnTVWonYzW6'
        b'l6QkLHBiRi+kBUPoysPkFhIRJM9MRJBwRVX2Pb9lezA+4XSdZ8Ux89t4Kb/rwiky5YuucvHRL6tlsfvm1xRiZeTCzUwhcbQi1rMx9GpkQiL75Ao7zSCpfSZ0GfFAuiCp'
        b'Qi2s6Sk1+0okWyR9E5ZEwwWGhBBoPGNNsSH0n1HgpUtxkbE04WIz1HNkE3ZtT6d5qHkmsS64WCR/fXHJTGcrV+LmJVLzNZZhoTuvbunt7O45X2ML5jBbBTtMFXhtTJyD'
        b'2sAnhpC+Ti85x0vN7smYrXQTJ2FaaELTd/wAlpOA7Cy7FdNEcltkkHlKi7mz8jypZA+FZFNdyL4K4ye5Z/lYArT5WGInjmCHrUhiJdLYJ8YcHN4ExXg/yUTEU6NnQxZ3'
        b'dzLhTnKhq9NOaFxlKgelmK7PE1ovYmWwuZh1uwjEoYTV4VxQU06SRP1cWoP1F2FiURKrYoNtDuZufFPYEMT3hTnuS3pIikTH4xQwFWZwRkhfaIVJ7Eq4LMdKurM28oWQ'
        b'5305cp3CFjGvaxU49dOjRSywSTXr9hbLm5+Edcv+irhWSWrhN4JMvBUebT3/gbbe/UPxazwzyzO/Xnn74MNf6G1/5OvkLtn/auup3526m+f600fGp66nfHim69ToX3ud'
        b'TrTZRO7tO6dnlm4s8ZT/S0+K7W/iPTOzlQOT5YOLJVYRnn+csnk97he/Mq5X/vrg20cPbb7jsenu2liLrX/85Y1C/3+ZpkX/5PzBh4dMfjX5aPObPWm/qVG7ZrVTtFdl'
        b'8jevl3ev+HXOr/4qKbi3b61LsKkOr5moqnPMTcGKu6uYp34/1HFR0B8K9aROukUeOqyHPMV1/tLgpMvW3F+O7TcWGvJgzTEu0WGNF4wsOA9lZA/CAA6Y8vduroV73Hlo'
        b'tMFiwXlohuWC+2lklfGSFMDNW2FYdFjw991nZRvceGyElak8Vt0UKemKocUFurmerIs9FphP7N2TAa2ZPAnGYxLsgPrj9vLCiquxBFvNrTGPmD+OeIvkoVtscUEiyL6T'
        b'WG694LSUo3suEdyWMCwtzn2TVa0h/ZJOSna9zDVMhwYcUhGk7ibMwBppdX3SJ+8IYd8wkyJUuCzDnCNSrxpTSQm3LOVF+jAhSydW64yDWMkFaGt7p3lXEo7aiOR1xGpr'
        b'dvBY+SBn7GJ17dx2s/JzXtLUKS2okhDKVNAC2Rb0dmAFPfQYvdV9JISntR60uHRB/H+AvdixKIxBJoIAvM79ulDGsJK+b+Z5J4uL/aWc9cdO6OLrML21iwUbYxHkeklz'
        b'gkR6NFArYekcFPk9Hc/1bEfYcp6tEy8qvZ9ngp48DwRX5yHdqjKG7HeS5NdyWV7wQaXoL+WhTzqh5BY5odyXeqKe2pFEeGIZr9PBl5LxUXexjP+shX5ZK7XcF9lsA+Zt'
        b'tk9NteCHsltguU/z2EX89KUcU1K/yeui5/pNgl/Eoj3PHr+aUfnO/5lRmUlMry0nMbH/LbErx4fGxCUuNFQnsS8iLik6hEkqyaHxXHszCgwPZILUsmMthLodjg4NjGeN'
        b'ro8sSE9SwzSXZCIFSY3ZRpKYqWTZwRJCE5kEFhBwIj4pNCBg3rcidLmfvxcSTePiI8MjY5kYReMuO5JTaDxB0zULoSP2lUiSXAXn38IUjoHRCWyOEFoOfUCXnUDi97KD'
        b'xYUZBQUGXyQJmqSouBiC2sigyOjIxGtWRicvsZeTd1rtsrrK12p2MS42MY4nXZotO9glGolQgeTxhAUdgY0RJI0SjI5eTjhcIqPNw/5TNt+pzAdCe9h3tNJZe9i3lR7b'
        b'8nv+JLXlH4lVeoK+XsIugcTO2UH6F9nyXygzVfiRS9n8BBlICI6+wM/oKxn1w1+KFtYtMeofZSwrQ8n+sX13nP3i7mWJZeaLDwkrHyesumLxIgO/wVr1/Wqu//8SKJY1'
        b'7wdMaYm5eb/rZuJHS4z77VtZO9oNP5HgJ+/SlbPEAn8cgVpsW7csX507CW1f3sb/Etev+KWu/6sa++NfChhKlhj7WQdbKMdyOqwXAQev1Yss/waH1F32Gknt/uegDYsX'
        b'TP67cAC6sA6rkqQ1eEcUF8z+ZtjPWoXCw8i2zHQJN1kbFYcIpv/O0eWM/49N/50S0VC94htvjX1Z07+/zMua/q+rqqiLUwyedZ9f1gPAFhD2UhdWv8QD8MyFEK1gZsnl'
        b'kZJbIcTMG8DsEAtWCDG3Qjw/7rvzKcrsRAwlcF5aWWwLerbNISY+NEzQ758KxFnGLBAfmpgUH5uwx8jBaA+PdN8TIN11gFFcUBTx2ueo88sLGXKeSezm3Xyhl2szbi7X'
        b'Ei1cTh47bXnq9NNB4lakxKduU4ryxZ4kC44hdjjmtqC3C2q/VMHdaCBVcb1VFLDQdlOk+JUZUYIXvXWoefqjgI8DfhvwalBEWG8o812c+doZHCoZPtNxx1TOZOM3f/ja'
        b'W6+89fVjkvaLKy8ajFanRfmOBP68erQmv971jE+1/cj2gq+r1luKyl20KtoKTeUFdeYCVEl1QI1QnryiTXoIU+UO4j0V0rUgBx5I9S1B19pN3zO6eRyboV3F7QyzACzV'
        b'QBV9wvjY9tex3Y1rraQAdTHN1RVmhKo37Vhj4ebuCXM4NK8IqfiJcUANKrkOYxeKg0+XgpBTFaJLD29bgqNfRn15pMKSZ6TgwlF334sTYl0hHE+R9+FJWfUE7iyaYGnY'
        b'3KmllHh5X4RYeOwxgzagIa68FIrnL1FWnrPM5bH7Kan8eQxXwrUa2X+ML4vXiU8H2JAsGPh/heYOwpxfAs2X9yiSmJCZWSqXwKQ+n7fsPwo497UfFlt/nVCusiVrff5W'
        b'XuHEGmSvq+0zFXNBAXrw7iaewYTFjC5gIVZyN8YqbJBNScBewchRgm0RQpKD9gbr+RwHVcm8nLY8zVd5aaZzW7RJeXlAkN7Kc+FV5hkAytaTrTKPSS8CoKmiz9W/CESl'
        b'K5NO+0ghITA59EJggufydnGWdyblR/LcMi7/ApbxoOX0vHnwZW6CEGll9i8FvA4LLo3QxEAWSRcoRBvFxCUTg2MV1ufH/W9BvvCO9ID2MAM6d2ZYMI0tJikhkalGAiYm'
        b'JDKtj0X4McvBskqSYE1YEh3GtD4afDmT+wLSsbXGB14Rjov2/BxcY9D0tIVc2TOJ+UZNMZ3lJUiFxwWOiuWnn8FUXWK4FdsDyyLNXVmOU/cpZxFWRDnxGizad0RC8RZZ'
        b'kex/MmpkEitsueV5dhfv32ykefO6Rbr2WdEJbsgQrMnjLGHH3IvGWgH3vEVYCzOYF9lQMC1OIC4pUt9s5vFav7rYQVPyS8//vZW+3kSxUV8sq/gbxXjtktGs7xn/+pPu'
        b'd3eGOgSaPfqzyp0jB9fbrU88pOVU8fnvHcpLto/sM/7AJuxhpcu5vFObGgPe+nWqXX2H3fjAp/BK+0DH5ENX79Xf+WXM1tfe+dXPdp3f+bs17/5ujWVM9G9/21X0fbP0'
        b'200Wf8v5xl8kJ+9tXm9QY6rITZ4nbPCOuf+2RemnUAadnIXbQSMJFwv2UlIkohgHxyGY42zY7Yz9E/ZjnA5lDBxm1QUT8X15TDeH+wbzFlVowDIZaam3SkVzM2kWgkhJ'
        b'T3OvGJowXWg5cgVKl7GlYg8UwYSsM5af4ZZOL6wOwHzD9UtTY9OxWJg7P9SF24EPbKGlczMwDBo+g3vKf1n/9SMFaRItp6TOL05J7VSllSm0eci8Ng/WV5XRlUnRW4aK'
        b'0URLrZechq4SfwmBQLLo2cdE15D+LHtJovuJ3mKi+4zl0lG6zyf3PlJaiDAXYgqUxCw9ODowNvyEY7CCFJ/ncZnj8zFGiFlKKMu7VeY+ZebJFmdrcG+2JFtbWk9NJ0xH'
        b'SqIVcpSIRCsSiVbgJFqRk2iFW4qPA4neuyW7DIl2CAlhweixoVeWxhExz53gJRScmsFx8fGhCZfiYkOYee3Z+aBEOPcEJibG7wlYUIMClpi8BKuahdQStmDeYy7rpwYL'
        b'fKaL2ig4MJaR5Pg4FtAxH4ubGBhPN2AUFBh78dl8YYlv8wnBalnP5jO5xfM4DDsI5npNuBQazHdoIZzysvzicQpEbFJMUGj8l/bTLoCWsIzHuQxXIiKDI5YwLr6j2MCY'
        b'0GdZF9lD8+cQERcdQuC8iA0+EV4eExh/8YmwgoVLSzAScjGsjLwW7J789dDEiLgQoz1hSbHBBB70zLwMHbDsQPOrD+bmSPotLE7KVRdyrgUgSGKR7iwmIHDZcRbD0DNP'
        b'ciF6b4/Rk4kaj4Oc5+d9VrCzdKwg26CnR1mc7vEF7zPaQCKIj5fRDrvdllv530nMXBscFxI6f1XzYxHoC1CyvL32SGhYYFJ0YsI8iiyMteyNb0kw4n+y2I2nFrdETpFC'
        b'JtvKJdIT6LcvIWUtiC+ai8ndgvhi4ikkGZdKQhJsieJvFMnEMX/lFNTyIiBKUH1EJfkyCS0l3jKYwxpl5SZJi+md177JTGMyolgnMRTJHMY7WJ/EJNo9m9XoneOC2GNi'
        b'ZWmCOdYwHG3m4iFECVzCkcRTgr8dmmBAidTqSuxPcucLwZarKsk4QU9ye9spEyzCIgsTZw8Y9mYjnuZvz/fShLKjytDoCUW3lKE3DOcwU7QLH6phvg828HafzPBmwwIP'
        b'/KFxIfZAyNP2dp7P9gv2V4QW1oOOC1m/SlRjtfxMROcCVAMvxIp4w1LsIgFligkkC2EDPBQSC2HazcLU0lVOtN9cHmt34SQ/OMyDKihlxQlrjsuLZLRE0HjrFh/+u9fl'
        b'WZUT52STAIt3DiYLhVLKdXiOdcD7bgHuISY2wofvreFFDA2MVQJUbbwTRDz/3SaR5Lw20rtu80qBmA1FvCYWf8PBQ5FdtPOrQQEWj3Y7iJIYu42GZn2epO/jzOv1utD6'
        b'C8yZVLqwF3bYFq7uVi7YD52WZvIkxZiqXob+UC7chq6Kfkq0LTAl2Qp66ERPOM+7zVn/7AdK0LYfOh1NFbmx89heA6yG7sVuYaiT1eRHZO4G1SyzXZ4B3ABPbc87yAM/'
        b'LsAIFlmypPj57HZWQa3slJAvn3YNW90W5Ymqakq8YWSFjSufMRnv4cyuvY/Ty2Xo2tL3z1flr0s2p4130fUvyS0PxUYhbT6P1WYxt6IttbMEc2l6uQXk8fRyO2xPMH8i'
        b'CRTabR5nl2PtflMVLo+ft4EKqDVYqI7AaiM8PCfsoOgUFLDKc9OJvDzCfCTtnFAvnwBnCDJ4tPn2oMWBsngHBvjYJJE2B7ixFOEoTBXKI+CMFj9UKHKBfMF6hXmezHiF'
        b'Lcb8UBX0XNzmU4NV4sTGUI41mA9FvNL/KUMoYFii6fxEeQQHwiOe3TsL6ZDpBv3Qg9WLCySswWqh4MNckB/NG7aVl0iQRv9iAzYLOf+TmzHPzSoEC59It9/kwo8kngbu'
        b'cHOBKkznuDlvXDh4SbCZN+AwzLG4Hm+SyCWhyjdk9obTlfG06HoS4At9SM0qOXmMvpW3lFl5BRova/NCB5+v5hrTrr3OARaSndGCrnTwyCrabLmXrAhGsUmsSovHnFhT'
        b'ZV7M5ayqY4J6fBIOq+KwBsHDMJbgZCJdQZTEBbIxhzccPq2F1UuemkyATJjAsSRmM+mUYAOMYxGHGRiFWt/Fz15JvKwUr6YuLzKR7IFyWUy/rcrv/Qp2nsTRJBxLuEy4'
        b'V6jhfz4+SSLSMZTshH5NTswUsSkm4XKSMh9GA8eVaHFjMAGpSewFWgOf/6C/vBwMYg2vLQWtpLykL7xEz/hBBX9MJ1TigFV7hJ4WdVaQs/AQLfDaJWGJa2FAdvPmSF5D'
        b'QwXbZRcNlLh6TTyO0QKPSvbsgiz+yDYXHE64rAkt8yMRrZYXacqLceA6POSAtFEDe1RwIpFWYg6TqkpqpCCo3RLTKXUFCXfdaH2TbvPYMXaZcvhA5mYQlOpHC+uswHJ/'
        b'Hw866AdY6oOFWOEDhaxKaK0MTuCgggBrlV5rpTNA/rpFM2jHC5py57pEogElCTihQV+JsVPGzNA/iXkHdmOxLOYTgXSz9nD3Osl4lLdUe7dwhh5GLQtc3DGPyAakn1RK'
        b'IMgr4mgnj/UbmNVshu5eJLNHhHevEkdjRxJFyJyLo85ENdyinS0JuzxlRVpQLyEy3rqDU+23olaL2OybtAJuBASpC6TcMtlMdEIkuqShFxB06oixSOhzIfr7QekvJvam'
        b'skLVjllioNAnsqa9XRNdg/s3BJZe6Y/0sex5LBCJUkQpRNFqeA+pA4dWmStA/2YWOXd1xwk+xk7MsMd8EQ6yNrKRosgbFyKDVobLJjSQ4qQQbhzjszdOx0Gz8d3Rm9a/'
        b'eNvTcG/2n279UblE3PEdDfsceRPtVb3HdRuMv7unK3fszVcOPdJV0juZp3tlzcGsX6T+XUs3Jy/ub4abNiXWPqj57GFDw7s1P/3d3ZHSyp5vu/zoN5+09r97CK64HimK'
        b'/En/j67FGIRYy9X8QVL4G6Xqt51+15l09NGr/sMGc2Gvfn+8vuD7q8/5/KSt575u20SsntWbHhNrKw5pWsS1fi3S4NyV6qxbyX2Sd2uUk7Pvviv+k4WezJ/CNuz9yaFJ'
        b'n6Z/9fxz3/cztY8e89Y6VGv8P94KrvElAXPv/Ejl0fTfdn18WL8Udrt/nDNk+35nj/hUfltrf4jp+7e6Xnk78ZzF1/wtYvq/9cqfK3/+I6XL0fcN4z8qd089P6x0dM/r'
        b'SWs8vvFDh8y4Ywk/e+Md+5mG5C7bwQ93/U7PrfeUso2tzZ49vbFH38xba/atlHdldvj8pbX4xxZV23R+be0+1bEmxOV1BXvN/m061m9FZCr1KZwaPDMb9Zfan350Ku6T'
        b'XzWE//7nifq2qffsT62/WJKU8z+X/mb12uqT33yn/43vh0z8wK2i/x2ftzcatfzlR03v/Np/fPLT+00lXy9MOvJL5+9+8vWv3frOf/I/1xv0fP/R539z/fPbJ7aW/7ru'
        b'WqYk/+8d9wcN3zrt/351+bTRt9qbR+Kifx9WrhCQFP371NMldZ13sx/J/HpvXdLBq9vjom6/H/LDb5xyOf3wrz+YPGnX0pL/gcw/Rjr/9dnY76vXXP5B2oef/uetmVvb'
        b'/zbedGxtz7dfa/msa29X93uOX1PPP7/ij/Jx8efe+PRM5odrw66p/Cd75qdbfv7+mp/PDgT/Fn5VCkc2Jz/65f43fvROivdfgn6//6Ta58mvHfldXe53zr5xq9Ov2ir8'
        b'0883fPM3B3Y21jz60Vr/j/MDU/Nun4z767q//uC7n+801FPYvPqTD/Z/Fn5bJP87lTc+mDTdKtSemNZOkrppZY3nndzaLhJoPmnG6/RjuauDIGtgozMTNXwhWwivS9t1'
        b'kRu+vfi3rKRFiwKJSS3WQhuD8k234rFnqfxyFWoSeVBr2mrsxlEmig6zxvQ5LkIXRRePy4JhiphakcgN+hSIBuRhBXcRmUCFqbTmNeZGQZEwrxZmS6AACiGTW8CuXQtU'
        b'ccOHp59yUems4vvddxHTzb0sMI+XmVUg0vxQHExCwCT0GXEb1eU4rHWbF29VXIn4kczT5QtFQtHyNCJJFTzoD4qvYfYTQX/N0ModYU606LueWGX+2IxmelPwBNyXww5p'
        b'TCKLR6T9FYjtoqP46CYwfIAkqG7igE9HJTrjANQLtVyqsYV4d5/r4+p1WLJNvAEGhOrAl5j5FBqw1dyTDlVeJLtNBnqgBtqEssKRitJoS2ZjuwEDYgsHLBTCLStJPirH'
        b'MmZDXGKj4y9zFjOIg6wwX76ptMbu1ivijTJH+NYCZSDLzRwGaMkkS1yjw6gRb4qBCn7u8XAP2XuQRZxoSeXhTSJp9ZaNyWo4bb7IrBktJ4DoANzBThKgWK9qQVzmIabE'
        b'y4qE6r4NpKtksgrY1goidXcxtMqc3IYZHHyVtLFHZp80/4klP4mhXSh0nMXrWuVbsKou+TiNqXQoHhYkrVhLsML8Cj/pHSQ8z7k9jt1U8RNDpS0O6Elnxl5shWGp0JiN'
        b'xUxqtMBZ/t2BZE2YZSe5SBInhYvjzmkV2tBSQRza7VdAixO/Ip21TlAtWSqIz63iK1LDmWtMDu+Ae0vlcCMXwYhaj4Pnza3ElxfJ4NpneR/m0xaGT0rgBNqtj0XwlVjF'
        b'V2dqcoygcMbK1FXwxtIMmCqJw/TdfApF7NrNihpbe7Gqjbcum4nNSHnk9V6gjnTBESaK5dKVzItjl3FcDYdkbCFdxgJb5ZRwzl0IfB24sZGBxL1b0qNXxFox5Kmd5VFX'
        b'ThuUpPUbIdfahST4LN5de7WjLDRcxmzBrTxAegPLnKuCB14u2wlLRArYIlaEEuhI5F0OH561J1buh62cldOyB6SdxaHJTqhMcx2q5yvi6myUEH05yZ+Q3aoufG/lgXmu'
        b'STEeVjQ3VstCvR9288hcWbiLqeae0B/PiKAFCSikrYtF+ttlD2JxmNCCuom2N/pEhVJo9F0oUhoAmSbCTu6Y+fB6lnkCuKhAofj8McLzYRzmp27uiLXcsp9rQafuCeXH'
        b'xYbHNkujpNf4MTWzXHlpmPVxolS5Agqle7COMhrJUoqohD1ieyUishM4KhDzCSLVJYRA0HLe0tSEQU64mG5yItRU86snkz1h6Nb5b4/4nCCAwJCQJUEA/2AS4Is5AHzl'
        b'ecFqMS9hLc/bqaiLNXl8s65QtYfV6uGRzazAtYGMtlh9IfZZUSzm5a3F0phn+u2JRi7KElmZxT/qEkU+kiqNpCwjWPAVeZlsWe56UOZ1flgRbWEN6rQabd7oZb6pyype'
        b'9Uedx12r89LamjyAYRmX8KLjkbotlATfw4JLIH4N80csOAPi1y51ZXz1VENTBWlw98LofFo+o9nCArgvZAP91v+SvpCf2jzPAb3oHEwljxTn/b+PMzWDZQXlQSQvetL5'
        b'wdwbggNESeoAkeEuEOYAEfOEPski54dsjnyG6KZcijzzTPuIbshx54fsLbnHMVPv+YiXcX6cvCQN9V7q++BegECpFXvBcf1sj8L8E0tTuBKlBvlFQ1hI7fLBgcsHDAcx'
        b'v4sRb2bEDKvP9rK8jAOCuXSWndVsfnlmRjxNi9uK59chWP6FJTE3Di09VrC2L2/8NzocFxJqt9soKDCeW6uFDceHXooPTQjlY7+YQ54foNRX82TFpuWcLDT88nHLUhP+'
        b'vAOD+Qy+yMb9Ihbt5TsTrfNM2skkjIuQ4fa4sfnxZ8S4QQb2Mpd8kakSDqrAII+Ps8C0M4stvc7M7ok5Xj6CyZeZe500XeWIEXcpkQAyAPlciY7bjtXcl39Ywlz5+1Ew'
        b'J8sn8tYyijbJg3vDfJ2E1jK/+et61lqGN5bZvFpkm5bkRJ9ugg7INYduJjPnYLEPM9F6uPN64KeZLO1u5mpBEnEa9J6Yt0osNklITqphJ/ZqcTvxZSgHUiDuSNtie0CN'
        b'l1BmIHr95yLNUylikU1A6JkLxuaCPeGtGvsT/OuVSWdF79j4SUQBqVF/3/bRNuFrx1Z7/u2Pr0TJ/EQs0hxac8NExdxYxNtBn3aEdJjeJHRRt72FzUlHGDPuc9NenPGH'
        b'OZauxN2ZrZkkRpfjmAO9JIizXXAt5rizq4WrIAqSJlOs5uoBadz8LB+Js0+HVjwZV7EB0qShFTimKu0XoLXaRyjLLIhGplvm2wWQ4NTDjYcWcP/IfJVaktw2JDJDLKlh'
        b'DzkgHIimpT/D8n1CCgweMKQkwzSqh0o3jQL4IY0rcLu9yEY+Qcn5RKDUdGMfJRzhLc9TojHVDAWRfWrKmWjZrQsNTLkZ31SO5x0G+Phg93HoE3GbzuojQrPrIajHKS8Y'
        b'J1mQC4IKhzngHcQuqNOHNiEb8iqk+gmttDuCL2HrBWRdwCNFkTCgJFifc3EyjEm+BDn5pFbtkIHScBhUxzl+IkcDFRdiPF12zJtpt+BDbudyV5BbpAqs8iRloC808nvy'
        b'92QSGgjO7v80en/J/gTdrapZxj/7/L13P/80VCf+Tq3Z9sMOLkcVdI+FdG+zSdhZHmTd8c5Q4YDiOQeHD/9l/k/FW8rbP41/537pXw6U+bs8styku/NX//7H10scT9v8'
        b'8vTdodtWm9/WUn/vluW4rK9G521TOyXJWrg7XHtt4/oH7h/e/tWVgf+0N7z2kw4tJ9ebf9hg056eqL5ir84fJZozmVc+0TIovn97/f3//PGY9+6Tgb0jbRFvtdf23v7R'
        b'G7+oiWhr26MX/epH9b/wHm7L+p1a4m/9tq+zHO/dW9vzb6ckt4Tkqfgt777uXnNP3+nj1b8bGP/4QN0+h5l/3K/Y3fenvQmfDP/Gu+dsh59f/bsWP/j44rvx2z/7S2Sn'
        b'/ifeOVXf0JPXMa/5/Xd+e/5V/1eN/p34dpl5VOS/IhKb9qQMfBgk2fNhl/e7NcqRBw694e+h/9vbr5pZvhLplGHkNnB/7bap/2y2sT/yzbH27/7TMd/+9PB7WecVPtsx'
        b'/D+VjR+/86M/27/52bdOrZjN875/fvjVpO9MjrV0FRv/9hXdt4p3Hb342brz3U11aj8cVau3XfNm1we2f+j9/j+vf3Lh32KRf9WWzp+Z6gkmjQx4cOyxgqqOlaTstkGV'
        b'kAjZjHkbFvIgRUqkoA8zLdUTGoUKpjNwH7qfzN7M82O2iUDIExTZVBjkRXhZSQ71w6woh3iDTiCX/3V3HlrQYkmFHiXVIhtzuZLjFha3YGjYTGTuOqnzzJyQSCtmMbWQ'
        b'rbhch7Vt2CeYJDLWrV3UrBLLoR1G1XGQ62jqPpHSXpWsUaUGZvFelTexQFhwCTBf2OOGlIdtYUYphQ+7HUqPsb460mY9h+RZu5419CL7cssB6DantfAdKUEVtK8RQ0nS'
        b'LuGcp7AD28wtTZwtMf2QtDMA3nHi5xgd5zuvtHOtEe5hulRpp3XmCcpUrgvrBVRkDd3ujEKmYA1Tk3dIzq1W5bmfpLk14wzXy7DYg4gnMYpbkGUuL1oNdaRfWpDeJHRS'
        b'usC0It48ECYhW04kbyiWvSwrqF0j0RHS4qYc5bEmRqpCsl5IRoy8B9JtPlYiPVxxbkGLhBps44s9LAd5/KFFKqSDDSmRRtjK9XbMSraUzlOCM083ugjAylB+G+svrqND'
        b'kapvOASpTIXzP/IVmw39H2prqovjLLi61sso/Iupa7dFfqpcWVKWdrRUlCpGBlx5o08k9I2Y/abJFa75f1m3ItapiBVQVeaq1bwSp8lVKVXex4jlQqlLe2PK8t5Fyjwq'
        b'jP1/yuonsysW7UeqX8kLSs3GBUWHaReLFKr/vrotu2gys4UZuUJlSl/sUJV2vnxBhSpV9NoSlep5e5+PbVNhC1EVP6FOMXGUi6KHRDwQnZW6ENoMiLlKJWFKVZjqggIl'
        b'+1wFigX4OiwX4DuvQD3uNbAQr8vDfP/L4enCO/NlfIT3lqm6aWV0WAgM4kt5RsATj2ZnWhY96uLjtWuHzVam1cQEJrKwloRElkb6zCUI9YMeB/k8WRdR+P6FU2IUPZNY'
        b'lSPdaxZfJGIaYPlC9O5GX0cuS52AEl9pzar1WD7vEscMfCCUBSomJpAm1MQi0a1hwS++2477BqFpM9Fw1vuFO92vYuuC3x3LtkTaH/ijJCGVnuvIvWOZN6zGWtz84UK9'
        b'5uEfrN0rytmq6fY1ke6AttL6wx9uq/7VW/Bz3Y0dU9dTvBrkP1OqURmrOWbR8uhPfw+yUbsecr3uXNR0tcGu4j8allgkbnlHI2imR3/8uwWnC4MmrL/x+k/HtcRh69b9'
        b'Y/Ri9DdO3nsYN+Pxu1C/j6w+aVoX67Dxs//tNZUTrLI5YViw0nexcXst9gumuSk54qE8ZPca7Xoh6wa7oZUzERzDSiwLg+mnKz8oYhrWC9LF7JbwJWxRxoSkV4ErVkKa'
        b'wFZTN7kLRnK8B0UibibHWuxeklrzlXjFIlKunsSxbQkx93wZYn5b5DifhCO0J54n6Ixsp6x5gugsnXUpyV1KgRaR3Ber/U30lL+vspSoClny9FmH6nyfnhelp6midzcs'
        b'pqjP3xwrfpsSeYnZXP4rmbRS2vmPnqfDbuODIyKTpRWVpLV6l9RwWoZkHhZMGNHXuM0jMuZSdCiz2oSGrH8meZVu5snaQvTxF7VzES1LoGQ9eX8WbIVyDd5V8rEiCgMy'
        b'Ul30cQhWkL5ipC4ORxrusBHzs/tnjw1LCT/ztbe+PlYy7Nx6x1Tu29rBEWHRQRaBsWERQQM/dee91xREXfWKl1R7TWUFmbGGNYY3d14Bk4saRM0FCS6PSgcdmDNbpCcw'
        b'HQGLlYSisTMkzY4vxfN4LOGovgLaE9l2oAhrjJdxnR7D4QXvqdRzSg80fGEvOM1A4XbnwSqBo+qul0PVUIaoCyVKF4yrT8ywNPnIYikyLpO2bLFgALai377xFfBrdnHy'
        b'8heukxXFkPP0POHoaSr2FP7T/ILKfo9rlbCEXZ7Sx9OmeBg/t19zmYsTCr4b4ShW/f+WsV+Edsdr0q+2KlIKoqgiKzY0WlK7T0NVbKipp6Iso7eKkWSRjMltkYK2jFWs'
        b'tozROh65pYx9hHA8IxzuGixOCheLTLbIJWM21Cb9ScxV6kkYhQYo2x+HdTaakIWTOL1i5w5IDcZB+T2YA6VQpkhqWgOmr1ODEsyEZrgH5UeOQKsKlEGezGp8CJP4UA1q'
        b'9uAYFMFIIIxjzwk1MQ5ABg7u3wcPYcgZHjrRU8WYd40m7IF7VjegzR0G9t3AWexSYEWatXygF6a2Qwe0YWf4ZVtjrNmKqdgSC414B3twBOtu7Id86MRcGNZ3urzPSw/y'
        b'N2Lq4ZtRdliIszAZuQ+zLjqtWhe4ynGPm5yv7XUrL2jzNbSEchzfBw+wi3ZaEgu9WErDTDjDxO4YMyy2vYAFatgZgkM6JO40Qxm20s80VgYcxtpjdlFQGIz98tAIE5gV'
        b'R6SlFBt9sB+GrsRgOzy8CdNYdQJKV2LrxbPE6tt3rsABZ5i2gQLafSkUaR2BQR/I2OJGC5jA2l0weBP7jkONDHZCLabjXVJFa7E4ArqxFlqvrJWowF0YwyZbC2zDiYhd'
        b'yvtwHLKDDSHVKQbuhNCwVR4wYxrsGLfOEYsi8SHWuWKFrwH0X3XA+zBCFzW0Xx6qj5uepH3nQwVkKm8+gaMG2EKUuAImPSAb6s/QYVRAlQVO7jpgvH+Trg6OnKIP6q9v'
        b'OWuONdirqYPZWALjJxLo01J15Q04R2/04jAM0nKGRFhlF7oXa85BnS3MaGOTepAHFIUnHsBUb6xaC/kXdijiHNw31IH70TC3GrLC6fV7LDCieqshtoZsOOW33xrLCRLu'
        b'Q2dCIAFdJdaeUF15LiV273UcMzy/Bmo9oXXlWRyk86nCbkXazBhBVC222mOBImQfxSkbusZK6NvNXNi0vknIOEM3UGx5kMAh7yqM6K/GPDqfaWxWvyXBGcx12gSDF5KK'
        b'xMxCgbXJ0ODtQOS8zkYVZnB0xQ17ut2uo5C6liTeakvVbThA9zMMjZKj0BkcuNEUSiJkId/otjV07EpKidAg2S4XWrGbTrbgUsBpmF1xBmrtoRaGoR0yArHeDKvMNyOr'
        b'0DUpgSElvLsaJwLlLmEDjJ30vXIQ6276REMf1tFBzJK8SBBWi/2xbntpiEZDqMO0Y2do7LIzULUTqiE7iFAvTbzbA8tgyJKeGSEZtffm2Zs6mmduB21zCsd6rWvbtLCf'
        b'tppPgJzBIl+3E1LlOq1z33RtM4FaMdTgva0E4n0EmvcxJxDLoonp5RsdxWnIVcCOA1h2HZqS3BwisX8LZpuQFjF3Y6fVbcjyV/KB+wZrWfI5dmntko3DuQAcEWPJVb3A'
        b'o3gHRpWh4JYzVGOaoRMU+UIqZoZoQBN0e/mctA3W3rwSexyclHW1rWzkVtudJARqcMccH7reauw1gByiKamB2LmD7nEa0jFTgmWeUIrDRljviXlnsBdGZbUI9PL0oZW2'
        b'wchS5gVbdrIkvd+DsStXV0LhWpqvn5n5rhIwZKdoKRIyjIbhXXxww1YXyukM79DdDBHZGlcMV3fFppUkGTT7ncI+wrlMnFx3HmY93FhHNKVNUJZA5KATsnaH4mgM5p6B'
        b'WatVzIp3zgsmVxNNu0NA14eF3lDm5qp17gqO05ydBAyNZyGNUGiOtpZmi306W3w2rfCCNDr0cV/siKbj6/aCEVO8LwfVQZug5Qw0J/2YQPKYPJHPBu/9pIQQRNLKH5jD'
        b'WNJurD8nS6M2453YQGi+rEJ4WbX9mAV0aga4Qc8BKMAJOq8ZrFpNkPQQ8mhzIzDoAllnCV0zN+Cs84ED+7HaFdpCNJUxkyC2g2BqEu5shFqjZALhKvEBmLkm2mHlguUX'
        b'E83p4kahk+SjPJgi1CkjnKsLOns+lohHqwXWRdGBT4sIlPIIVnuhDSrx7rmjRBTnzPVPJ573h2YPWmE7luCYCeFG6cENtlexQFcJHiyGWMKPymMraR3jVzDDUuk2jMVy'
        b'enlX/RqJbw+w08F9R8r6YBjyvH5DT+LvBPn6kBZGG5ujATqJMGXsOEDwW60QA4XQdQHK1eiSe4zUoHwX1jhDcyI9koap3ErbSDypC1I1xJixn0hIxwoFmNyFUwabCRxG'
        b'YMoWH+pewbbYFddkI6IxFSoIX7PwrgYdVDttrxNnYPQY3WWrFp1IB/b5rokgiMvAYXtop2OfObeFeNOA71VDguCWmP1YEkAcrMoUeq4QUhRY0XW0OtgSncsl2CTeeW7b'
        b'xe1YahKF3TcPqafQIjMgleC5FUa3GpmEBMIokZxJVV0sJ/07QxVzHKHR9gTBBLRco0XkYrEJjEML9EFxCrYqrN5EBz2N7Y6+1vAQ65UdzWjTWUQkm4lx1x2BUadwb7rM'
        b'UUhP8GVhtMQQm2A6BfOTofq8QihW7g9zsuJMvdgtkfhNVhLRhRJ6pnKfk/4ZrIK6i5AnTjaAeoJvOkWCb2j0i6JVzpGqbxzn6oi5sWpYGnpaYY0/9q+CKgZd1oTTrY5a'
        b'saFJrxNc22zbzghtLBcvZnDQHCdkjq4NgGYFrPFWlhGSY0ioxmooSYQRERHbTSswdSsdbrXhdRxQgCloD3UygdrD0KdDvKB2JUusUcd6hRjDKAKaWg3CxGpbU3x40soZ'
        b'6o5fx7uGUOC6diexgUllOpeHmK9wDHoCGK4Eylw6x4ShhlgcxOnzp4leMPJ7jwgBSR9xO6BOx97cWxsHfaE04AikH4UpTWx2un2WDqV553UdKPBx94UeYxy7veZwABGO'
        b'XrqLvhg6kT6oO3tNBisd7eDBCZvr6ocxDeqg+kAwceV0uuBWAy066Sxsl8CcFpad1NdcRWwvTxdKzrsHniDEnbU7vieaULj8DJRbQYa7rrUudkfDPXtCvZwouLsZ0w/L'
        b'YKrcMZgKOQQVjpEwesATpiHn0O7DR2+twhqCfSKLHTRftiiGxULisDw0ExLk6hGyjNBRFWO9LcxCwUrC0XpjmL6JE5cPELxWE5srwsp9l7HVgehJasjxq5DlFEfw33wT'
        b'Km+uIIgaD7mGPeEGWE00sIWIRN5eLDyttQMJ1Euw3YmEIgLmDqOdtIYG+q3NfudVJ01iiUdWwagPQeAkjF3bRhg/i72HSQHsJXqbD0071zJhLB4Kwoy2MCjEUt3dLgc5'
        b'LWilhaZCYyRUBmmlJHtgPc0zRjhVBWWRtB4WKJkhhqIkOvqClayfZR3xzz5imwlnoMUKG7HdwEvNhzhFV5QetoRihQvdcCdOn4OGAFrkwAEYIAzO2Q13kKH5LFaepCGy'
        b'/SOSGQ/CtJiVOHqJyMsIZm5y9FPGodVbHY+voelTk8oIrL2I6uYSYLNElHkRwhzvy8RgEYkQ+3eZw6QNDCWrbNmtEE/ya7XjKSw7RHuBZge641maejSezmmC0aAzGyDL'
        b'DjO2BkIDzZ0HQ5eu71dd6wazOBiETfTMAJGOqtvrINX8FF34fdldRAgr4YHZjoPYd54ktAp8EErSZRGxsV7i0ONIZC3jtiXe1SawzTl0HppdsdLbnlhrSag91Jw0I5mj'
        b'Hab30GxFJI00w4wGYXYDtGhijzMUbb2KZeoe68JjiM6lKRCCNF5XvgBDxnuOuBvsVyMYuwcV6pZrZOnQGpS1d+PYus2KEkdMX0/nmGpMcN+htZo4fBGN2X8OM87DXQcg'
        b'qnSAeCARJpIQcOoC1mPj3stErCqgi1hJO0n5Q3RNMscsT0G+cSzx6Tq454UZfth6bg/kuVt40LFlQO7hqNVeTsdJhgHm/cs7fws6g0wxPRhSda4bYRUxrNKzOBFP4FN5'
        b'HPsCMMfSBqrEBG1N7pjtQDA2R9fWH36eOHgJUe7clQZ0zGMBWL6XlKKmuF10/N22kHWAAKcdS7f66obt2O0VBO0BeD/uHJHl5r0aysZ2O3VX2pkSTR9TxVydI55biB3O'
        b'GUP9SRq1TI2g62EM5HmfIkSZOgfNm6FTNwSHY2nCOtpqgz+hQ8fZ0BVEgcqg3woGVehA87AqHHLXwcj5S/76B6E3mh7qh5owohE1kihaVaoPwfyYHRTvh9ktxHAf4J3b'
        b'uvhQFI115gQMdyyT3iSwPEpCxDADy7RYDpWzBJVXsS8Uu68psuQsnet0iGmb15CIO2Zoo43lmiRLnvZOcYaS2+uMrydBVqDBsQuq3sTC29gPZGwnyl9JtIRe288kpxua'
        b'anDvKl3uFDadOqhC7HIC5jQCsANroojddslhahJWnAiF2eux9FVd0HmSZQa4+AAkPkzDbCSB/2iQAWbGr8MOE4KMVkKevhOxWHrDiChEPZN3I2gBOf57YgxU6I1Soh6V'
        b'dBr5Hr4k6/Xe9Ll5OuLqBlVPJJG1DTs2ECB0nTtwVZ1FaAJD3hK4H3vpgDZMaCQy82s8iRQlZzztlDbhUJAnpkOlDz0yAXcUsFctFHOOs26w9HH2JajVIEXlDjRexZEL'
        b'2GzthkPWquauRKRqIjUdo64dIOWpdQ2h6SARnPzVJrJ0mhU2JHKW6OvC3VijdUcJX++twQdORLsKST8ZI4Y8Fcvi+7HssjF2biTtthfv3IRaE0sigvcVaLoM7LRzCrW7'
        b'uv5cGGF6GmFERhIhQ60ylG3Foot2WOduTJc6qqOVEEQkcAZ7/bD3PKFO+3oCwfqdJLVM2kE23r8UC22JBAA5pCrr2+gSyaw6SJR+dO9GWnZJBBSSyCCH3SeJX+YQpJYf'
        b'uIjjJ1diJoukHQyleRsI2mpFG6/sv+SXoHeMbnh4gxmjclAakgj1B65C3kbMlTuH+VFQs4+eHYExkjqrMPcU68ZDckm9rrs6NLluvu1FEHoPB1J8o0lWrPI5cHQn0836'
        b'dkOHQ7zZOZgkoCr2gOHrkbos97VGgwB8zBLbjt9wwnJHM4KJAf0NmGbtHnWSKNSEo6k8jyPRPU06TR8OubnIiWSsRZgX5MRThrA5lA44x8iN+dB5ElNsDI/6OEcsL4fe'
        b'mXIzF4tk7EVYEw1TQprrNGGNNeSy8H6Zg/QFUc4pnmW1hgjBHQ9k7o18GZGMq4jYQu1x/tJxBeg1xU7Mt6AvnEXEZBqwMclJwiKhz9KJNhBTKiTUqLVXpXMfvKW87qwS'
        b'VO711gjUIeZUakXg0EonVcFk9s14x8XRA7KiDuiZErGZxI6VKcShWqDRRdPhLNHwEqgPwmISWgiHsWkHs7qQ9l161SrpMPTqMTHvJnSEBmK2CrTEBxLilMPcAUg9fRwr'
        b'POku6XtCx8yj9Gs7dLF04uyT2iTD1VnTCTbY+m0iyEtbQxrBsJkvjVss8qI5M0OJRg+yDsZ016TnRN6ALCvisKUnoGQzKQsjBBF+JMSUbqYD64ey3aQsZSZe8ICHbgTu'
        b'7cQq8ukYRgxJccog5Sxnt+kNyLYjCW6K6MQQ8YRmGFpP0nA31OwK3ZUswWKFUA2sdr4IPTvcNfF+vPk6fOCPfX4uK6BH4UZSqEf8BaKipdCuxGwHUG24EtPoaPuIIKUR'
        b'hew850ejFdCJVvrqRhHiPqBFlGynzXbuX6V8WhUbgwO47lUrwQxb0mVSWRg7Ei2ds4UCCQ75mnnZYuYZImwte3FoM6FOl505sOyLHijZS2JRMe0oNV4/SZYYVEkC7aId'
        b'Zo+cJZmyHPLMoFEB70ViiTNUHMTmk6RWFZD+MquwAvMD1gebHl6N9xShIgAq4glVZk3Vk7AnOD6eAKgTy26q0XJzd5w6Q1pkP5HjUjscOex0QyssBMZN1GBCHZucCbXS'
        b'd2K/NUvf7IEsZNadXA1S4scgbRXUXyBKAJUHnf08z8af9tMnqSiHuPkD/V14N97ajkjFSLKEKEQH3LPUg7mkCOzbSdpAiZkO1uozUk6Anm1zm/B0fDsJjbnMHmXqGUYc'
        b'FSatoS6RQCobJs9Cdiwx8nboPUIY3O92G/ovkNbXSJfa77qHm2BmJMRnms6Gk0bVAcU79VffMifxc8yTKRJYGgbT2GpD/zeHs0Z6UBmaYJFoQFJX3wG876+GaWo4IwON'
        b'/rfPGkNXUg/xsIvQ7/ekbYbI6MABI3uNZLynJ7/qCraEEGqkBRFhHj52FvNcdfUcSHGZg6p4OsosFV05vwvu3kR6SuxWEdhUwuBK7Nxq4LZ+H4xeJ5Ug+4yBl2WwgwJx'
        b'tfvHT3EjzYjXOpqkFsp3sDxsZdrASCxRpUaivK3EWGYjcCIJJkxhEPL3mRNydGJ9LP1RnLwNaomzEYkvYaDaBsNmMGATRzJ/4x4cCTlLB53lcUqfiZxItLrjtAyJfTOE'
        b'1mmGhEHDTsToGmUNscucqO8otumcgu4NRFqLoM4+3p3E7cZwEkEz7BmFHYa0m9Ek56+2J3GhbaUGM2+5Y1eK9mFl6I05T8S4QLAFJAQTBpRcNKZlEVfDlltECx4YEiI0'
        b'kKoLXR7+oijMPhRNRKfe/1A4MYdRrA+lFZYlEi/OoDdYNk9DcAgMRh/biWP6mvBwox8BQ7UudjhY0am0mmGPfig+iCS4YeJ+L6kQM/E46y+3TxNrVm/FMq9LRNQKdLBV'
        b'm9Sw8uskTKXC3GUSeMYOQo+Wl8lBu03EgZuxwlcRW5zi6ODrTLYkrTWN1DvmpK2FzTq3k/aoQdYhsSfBfC8BYC503iJC0JJ0yhnyzxKhZXWSdEMJLWcILyZuno4hdhkL'
        b'RRIcpr/vkaT3IDCZyG39/htnsMPXkuhSLfaZwvQhf+hfZ+xCRKGcXTJdwkOibDVEHPq1aBuzOHfrmDsN2r4dymJWOHnR3FOrWYrSYbjvQDQ4+4LchoOJBMDlST9hpsRZ'
        b'v8PQ4IP5CxruaZq9EKq2rWNKrq+3igyMa2OOJwzKW0L/WXk96EEigmPbCQoGd58i7pRnFbmbYLSU2016N1gSFWOWuhotC8gkokZAmgVDpCDgwytelqZ0XX04c8ABegyh'
        b'RsNwFR1+AYyFELa2Hdwngp6VRFd6jaFmN6auJ1o3AvfOYNNJqLP1JbKT7QL1Ib7EEwZPMRGlFVt847fISSL2ETPEjquYawUjG09gRqwNtEcdIr7QTjvuIsm13pEIDjxw'
        b'xzwLXxa1aUbofMdy/ekI7Ni5wi8eH3oSsFUS78jcpqsITVGxMETUq5FmGPJUIByYu+RFunspwUsBtKfQpolbrcJOa6hIIn5S5RlF0EQsuMpCLRYylY32YP/uSKx21YuB'
        b'GehJwrrdMOUQj1V0dsU4dGotzJ0Q7cI7aoo4J6FVZnmsgAdyzDbSths6w/WcofLo6lW7SfHKoy1h/16i4jMEEoOEA5MEB7OXSQe9p0OHXhMUzPAmLMKEiGqh+JxD+GVV'
        b'GD+LnVFenpFh/iSqjqjTEmqJ3/Yp44gb5AdD1SlzfSAdIx0Lo1QD8d4JKNaxDzh/HRtdPdZsxVIbHF4TcQ6L7MRMdCUqlEm6dBPOuF+9QbvPD9IkztWCD9fKGkOljjdm'
        b'BZ9x8j/k4Uj4XbAfKxJ27dkSgg82EE0aoEvNJ/1Q/gIRh3sqvoacwDC6fZeOsjp4Gwzj+AZTwtxqbLtGCFcEQyYs501LgcVaXzqzgmVAheDssct0O4VI8kGJEkxo77Ui'
        b'itZ4Tee2xhbCrhoiNw8tMOcCNO6MIaQckCQ5MJEmLWbbEsAm/XZCItbHbiy114iHdl35qC1EdBtoN8NEDiu3yriecGH6UzDeD8ZRNcKrcdp8i8VedSwx9FsjSxBeS8y7'
        b'gIT4eyl03BXbTiidhIEdWMsiT2pZjLAK08qhz/AknTdp1lCkh5k+jkzy0aHB+i+sgw5b7D9qhiTOuK6hA8rfAE1W6wg9K/ZB3Qo6mboEYjpdoTB8xpDVsRB7b1sNbSt3'
        b'Q2oQ5FqT9LufiOG6k6ariUyURWCGEgyHxt8mvpUBY747iKmMhjIKnq+QeMwOelR30gkXY43BBTqjB9rYGr4CBxRNUhz2XdaHhp0w6H6DoKoDqhU3sxKrK3Ei0RV7tEnU'
        b'KSYuOh1BrCBF+XA8XWIjDVO2YVcitO+V3Yr9BzdB9wFlrE/Ee5ph5w2gU0vzMpSvwAK3cBooDe5aKNh60IWSnEEHc1/WyOOS/U7vKBzYQKShh7CoPmADzjkS8aqCBheH'
        b'/SJCjTzCSxLBiXSVwYRKGGZvJ/ZMQJp/GIZWKckQLZi8cI7IXgddyn0aNVNrxWni4oXQpgh3IiBrN/ZYEv3PuZUMZbvOIbOVt4pg1H/vaqIoU5AVuYUwrcsAWiwJzWsI'
        b'KYZIra4PUFq5Haf1oerELrdLTsRCu6Eb+2XplXQYNdLdTVpHG3Q6QK+cISFTPcwZr1hJsmyhGZbcwBJ2NLlXYERyafNe+rR0H7RuOY0PiE9ipdamfZuwcRdUh54hyMnB'
        b'ynjiS7NXz+Lgtn0nISM6kQjjXSvRDugMvKobFESnHh2B01AYBEOXSXouJemtkE5reA/R1cxNu0kvfIDZ8XvcwvYTHcjBvOusUMuIqgzBXq8qk4zpKmtCEq7ehPte9Gcb'
        b'1LqTit4Eg5ecceA054pjOL3v7AGoMiGOSfqv034ccyXpbVAlZCuJcdW+hBtzCkEkq6VuWOmRJEdYhIV6jO/60J0SS7dhOamkeXSSUFIBE7txzIDk3DNYrhx5GPo2Yd1h'
        b'ayiVEHNrVmNP7NeMJH1x5nq4szNJAhmuJ3cbYVZKHJG1BpKwZ7HLgQBgBJqUcGaHQjSxnT4ZbPHBKeObkEraX8VmRw0VH6wM4f61fmbsv30d7sIUs2u1wQNv2iVhSicz'
        b'GZGg2wGdznpYc817i5817a8Ce/dh2m3Sv8YNiTnmnIOmkyRvjVvKR8TZGsCQszKh/j16sNCWjjYrmtBgVgObz0MmCQRDxFyKtmLJagXaZ4eSJQ7ciCARMCvoKtzZj6y0'
        b'R7MERwyUsO6UgaMBQcw9EznNNXj/4EkoUbdXJLo5halOJM30MZq2HQdExL8rsNhGPfQYZJ51M9mVGKWMs5qnU7YQiSep/EDMMSi+hOW2zI3M5NDR3RE3CEByt8CQ1h43'
        b'QuMWfZhShokz16LNsNuYCNckKXaZ/jh1VRmzjvoQYmSSXtJNZKeUdJb1dOBVa7FBVVkSpo/5flGR5y/YYa2busxRPXqvH0rloUxLnxCuHCajVFnlxIm1zARKjDsVZlbB'
        b'JPPgdRmuIZ2vIOjgfpLeG7fRWbTAwBrLWCh130hoUUSqT0IS1GyjO8hywfF9KiS/T5NcUH80RR9bVW/JsdpOjlCro3SDMK6M/iqFOfPYgGvQuJ40ygztXV4wbgD1mjv3'
        b'q17BdFfMNLyggF0noCyCJNc+AqQib19mNMWuJGbxonufJuo7RDwiA9utMOfWhfXEpkkEOkXPNnjSZtJP40SKFcll0EH4Uk6cOkfFNyjJjzCyCRgvIXG0fQftbe4m3F2L'
        b'ZaEkdY9fJmjpv2JAQNV3E7NvkzI+pUKSR/oZIk8j0J30cxKU7KE3eAER7Jlpqvg0cWGiYFEHjbw1NmEJIcHpTdfp6/qV4cFKBti+ctcmut05HAiHewrOATTJBElIHeId'
        b'OLEa5rBrZ5QKqzyAzYnAfMBpfvugTBYqDYiYz1zBGjdoldCvnTAVStym+xZRxmLCp7t0F6XKa7HNlShpHx19AZbdwDmY3qeLuTtg2hJbN3lgfjRzdbkwW1XIMTqczM1E'
        b'U3JVZbE3dBWB/dg1I0LzB1u94gje2nVsaW1lNnpYuXGdKdZtPkoCA6HGYQKGWd0IHFfF2r3rsUONtMbMc5BxGB/YQ5/SVSIv5ST9VBBpbhMRxE/JQ4OhM1SpkHrQYaMB'
        b'LQ5bocaOZIVMgxMrsHvjNnl5zDl+GHNVMP3wMdKIp61IwMrejcMal3DcWtXNFlrtsNxhjz0dyijUyhLStxOtz0oJMNJk2VkPiA48gDQjAvV+GRLLbidvJWgr94ZMFQ4U'
        b'Dy4Q+Z67uJmoQT1mx9GpdTIqMG5Dgkd5WAS07SJwZlb4cszTx9EdpNOUhkOOPLRGGEG3LAwe2IMTTDfH1ONEwMbcrxA/f2gnT1J1GxSYYIYFHcygHrTehCotgsqcDcyd'
        b'LHdDfkf4CRr57j51rCTRQf4Kk38ydLbHkrpH0nw6EYhS6NTBmiP6V1lchQ+dXC1M+ScbQ68lzDhCm6kc1KyHAgvSUevOQM9F0nj6oc3yAglAxLl37InbBlOuWy5jqzFU'
        b'u0Knuc1RHJUjplLlsp5eacCRrcTiehiS1PhoH7EjEbvPCudObiLSVuUdoH7h5olVvgQ7OZi63Z2EuOqN+9fZ3xQRJc65iD3YFGIqFkr0FGpiMa/Ps8VVWqEHOzcKta8a'
        b'Id8pwTaehM5esVCtDjqtTSXcgiU+TmRzaq8bMyztEtGKsnFKqIbTahhxHXLcWLkHGRsRFvjCfcGAVeKvfZOEmHzMlRXJHKZ39GGWp0+pxG/bFrRgIiM4aKHF8YI7OWGQ'
        b's2anGyu1a0tfOa3gH9tgucjeCfPd6Y3dIixW8+DGNmtSq/dHPzapQXYgjcOmjsJ0C5IsmjHflF7xYiF+XTd5Qt0+zfWHrDHfQ7Cple6QFZZajrkwGo29C1Y4mL5uKsNn'
        b'SWZyUyCMu9FxyZiLMEfPSSgH1hLqH8Hi7BaMcNh/3lTGkXdK4ulooTpiUbcdKwwUEP3xXgeRqYR//EcNiahEmfe4c5cxCRNqEm1zFIvGnNT4syOrzolYNJkjH43nrkX+'
        b'0qlMkoAsHmzj9Zs+p71WOxi8M53QMZ06/OFs7c+v/8FYyUXVVNt5Y5fReuP30pw/KTv8j99/erdrX8s/33it30v9/fUjY1M1ce//7LPkNw/unWva6+OZHfO1+2MPG1J+'
        b'YfPjvLde/3tzqtYnu/5X5HD2o4GTx/Vdze74KJeuKG77/ev/SLkVYxS1+mBB/VTvzrt/S1Af9Lj7dta3Gnv6RnzmMn6WFn96t/IK0/+p3ItN/fmiN395NOfi3zdsOB9f'
        b'v/N4bu/nOT9LfdPb832TuBb54c+7VzsVXXV9/9uvlBr5GH8nOKe8u6Or88zg4bxdjoY//ktKe27fZdfN66+H2EYEZKfUl77quv+BaNWPjlh95vLAdCSjrGzrpw7b2jJ/'
        b'/8qEdvmNde/2R0wXN3/v7UnLNxPfSDT+tt/kn10qfvLDuor7Bd/Z9Sf3745Ef/fWgazkxB/+NLBu4r1V36+182oyLnx98+8e7jTf+M7oL2tL5d5uT9i5zmnL1Acff1r/'
        b'Z791d8++97na76NdMgvswnemdP/2jyePny/+beze+gH9m/f++uG73x0bPb7hXtXlPyjPXt/u1Vey79WP/xP/wT9f/9rPXm2uyFsn+dg2oC72yA9iPlCq3fQbL5sz9YGH'
        b'pk+P/21X0ytGI4lhDTkxWx26X1nz76a9TV/TzPpwzV9nA//ziqWSze3rW2/PqVa0+5eq/ePKWy3qGw1Cs4/vv2nvN3P9z+Mf7WtQ/KbN9/d6/rpwbOSNjbO2rz6KPlCg'
        b'5P7pyRO/svzM9eEPTN113vwsQn70z6GfFF21r/z7jvdtfpDSf7Dps4iR9T2/LnL7+bX3zYdTj272+0lu+sOpmlf98q17LumPJ+5/WHj03fWWK98OalKtHHrtwHf9m/Zm'
        b'rrgXpPbRW1/bPLH20FvfVE8ezr5pGHHj7wH+R+L+/ctLh2f/czP8nbFf51yo2funPSkXP/nF7fpTmYNnExz+pXwj8jXTqMaKiMaDP7oX8b187e+9qqM29n5o7vs/1Sks'
        b'/9MbVz0dGro/+NZc0yq/4rNvmyrzyivQLDLcZkxYLVCUIpI5C3nEu//Ra8bLR7MXn+YJT96Eaw+fbAahgA/mE9eI6E/xBDfsP4sZKvFqSmrE6/M14pNUiT9PSkSGKbIs'
        b'6lfR9hqPoNeLX73w0BWcuHJZjYh5nbzIwF4CA9fwXiKrS6dG5P9OQrLq5SSclMMKDciDAg1FNWUc0kiWE5mqy+K9JCxOZMXktoqgSvrk/GOkjGTzR6FQmEFe5CErDw9w'
        b'ypdnB2qRuNOsQsORuNomDKmIXWLrtdDJCyL9v+auNSiq647f174ENrAioYiPaqOyD5TwEEUNoPJadhc1HaqhXpfdi9y6L+9dpmpkEDVERMBoo0UxDyWB0ViRqhiMOjkn'
        b'TafTmU7TaSed0zbTmXyoTtK0/dJO7Yf2/M9dlKaf2ukMmTv8uOfec8+953H3/P+75/f7b8F3t+io30ofbUKns14vlEnNuC+XiW+a0b0V+GaSxePs5uncMkP3jgmtHFv3'
        b'b1orR/DJ/4yWV/IVWG8661CQzz57vypghE2X5Ug8GJZltgr7bQqcSxAEvoRfzPhnDsEqSrxVNAt0E+0mh8Nhy1yYack0O+Zkz5WE7PrcJWVdXLnAr4X12JJEr13cxbnz'
        b'l22CdLiMtxortUMlxl5zpZFekrc9rypTtIuOzMIu7ht1xtFtQoHgFFwUXeYitse2dBOw3fJm/GkrH69lFrWfQnWerOgunv2unt1xxhstwtZWQzuBKq5uh779WJsZTAuI'
        b'TdQ7eb01DD9rDOJB3BtoRL1o0MLZvyYuqEDXVPLRJK8v5DnO/ZG9tL/ejyszN19ZH+i98IF/uPtQpuM0V8X1Psx2H7r7o54v3E1lr+x6+uFoLCv2QVW59McPx3L+dHZn'
        b'xqtjdb9Y3vnzGvc7K9//y9pPfv3qWz98ZuzyVezZeLaiZ+F3S6MPXa93zhsfrf5iaHttjbOt+ZnPS+54BtJ/M5z7dktu2/CeqYlLU42Xf9x1f93QlcMbT3de+Ee+dcdO'
        b'd/HvLNobDTmHX2vfsLe96GDfJ/dNv1IKv/O3av2zd/+qfNqVF/inP9CjjXw4PHS1zv/LnMnzadv8VQ9CXLcjp2e8COXaWxqv9y/Y9+frfdyL1uuDYv4SlDWQtfR9m39v'
        b'j35j1cb5Z2+j0q3hB783Tz64+HLFb289/ym/5vjH2+c1/8S568Xoc1tvPzJ9fmTnt8//oWARY+jikQJ0DwzUQIAxZi1c2vwX0ISAx/CJJqZ7lLU8yxvwUCuWZoHF6av4'
        b'LPyeiN50xIzgq28cSMcjWUZvAHkfvtChveEQF6KjIYPadc6CTzXhKxDdxWfhzJJgVfE5NgNaqNN/ETSVrr1A7dFtHL7U0sLumoknIi48UIsvrwDK7wmesxUK1DGZlBmP'
        b'txadwSPT0lu+kOTn0bgfDRg08zulq9ElBdh2nlQOOz4u+tGok8mowarqRQZRvB33M8UzxwLWGPtDK4wyffW4v6BegrgXow58WkRT5TpjrvDr0QVvA51Setz+0mKeoxUT'
        b'zOXoIrs8rRzf8j5bTK/1pqQmzuGxp74uVlAfdsLgQw/RyfAe5Kn3pbJ8z23HPxCL8MRaVrHEXOo09zmBTy5yGXukLTy6g48GDSr5KXxmGzD6fG6Om2uXinjqUA8YrBk0'
        b'vAqPujy4HyJLjaKjUpRHt6mHaYSOQuf1ZhcIyjXCXX207hI3v1OiJn83OrwGv2Q83DW69XrhyWgTQJOnCWiqQAB3fh7rFN12UJ9xeg7qrqwX0HgZvsykvEqp83WCulBH'
        b'0vDEU/imjnrxZALf2EvtDmrW5y+VLPjkVmbfpOFTnYxv5ILiaDqjFp0T6EiA37eYjsQQHYBnppURvfiOIY6IBqqTy+H0FDqme9HV3EUraB+DHhiLoReoR/0r/Z4CM1e7'
        b'2XJwe6XRMqdoUWfT8Di+wXOlVTx+haN21g18iI3NA0vR1ZxqWDLtawyYONNBHo8EdrGAHU87l8BxDz620jnNGsrrgFjSfagHDaLDrCpB3LuYtvtLEGQZ1AgbBc62TKBZ'
        b'TiMjsJEHXTG7Gjxun6eQ59JxX+s8cQ59V46xe9DrqH/rpX3jLaRX01eIPjx+B92eWyzSlvz+ajai0+W9rjq3E3ic0Ct4agc+CdyNW+g4e4uyluG7rgb0GjpJHTQvB19y'
        b'3p8OUeSc/U/3//tskTMLdseTWM8JmJbsVkZ4t7Itm6maWVOMSyB4CSktNEdKY4zmFBP/PVlsemsx+FPMeHATMaLENB+d4Ygp2ZGIKESKqHqSSGE1RDGeUGJE1JMaMbXu'
        b'Tyo6kVrj8QgR1ViSmNqo6UT/acHYboWY1FiiI0nEULtGxLgWJuY2NZJUaCIaTBDxgJogpqAeUlUitiv7aBZavKh3RIlZj2tJJUzmqDoLLxsLKcSc6GiNqCGSvtmgMfqC'
        b'e2hJ6QlNSSbVtv3yvmiEWBvjoT01Kn1iW2txmRIDRSmSoepxOalGFVpQNEGkmqZNNSQjEdR0RaangMhNsqLx8JrVRvgROazuVpPEEgyFlERSJxmslnIyTs3C2G4ifsvX'
        b'SNL0drUtKSuaFtdIRkcs1B5UY0pYVvaFiE2WdYW2mywTeywux1vbOvQQCwBFbNMJWp2OGEhKPbHRjMZ3anVgxfkAGgC2AnwToAmgCsALsBqgDGALwDqAYoANAGsAqgEq'
        b'AMoBagAaAVYBPAvwHECA0WgBmgE2ApQArAfwA9QD1AKsBQB1NG0zQCnAJoAi9uBAtHueydUBVD6mDcL4sj02uv6+c4bRxc49srbRAaSE2gtJpiyn9lOG+KO8VPpxHGIg'
        b'tMI5JewvsDICILHIcjASkWVjJDOK4Gdw3GwEa9V+Bkd2TJvIX4qtTazr6AjoiCgbIMVCFEkCNSP+9zeqixOymWrgvwDm1tvv'
    ))))
