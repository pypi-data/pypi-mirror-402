
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
        b'eJy0vQd8FMf1OD67e03SqSCEEP3oOnUkqihGSIDqSUiiycDdSXuSDk6FKzSLLjiBEGA6Fr2ZbrpphmQmsZ3EdhInceJLcRynuCVx4jiFn2P/38zune7UAOf7lz4a7czu'
        b'zpvy5rV58/YD1O5HgL+p8OeYBImIylAVKuNETuQbURlvEY4pROE4Zx8mKizKjWiJypH0LG9RicqN3AbOorbwGzkOiaoSFNSoVz9aHFwyvShDV1MnumwWXV2lzllt0RWt'
        b'dFbX1epmWGudlopqXb25Yom5ypIUHFxabXV4nxUtldZai0NX6aqtcFrrah06c62oq7CZHQ4oddbpltfZl+iWW53VOgoiKbhC79eHBPiLg78Q2o8NkLiRm3PzbsGtcCvd'
        b'KrfarXEHuYPdIW6tO9Qd5g53R7h7uCPdPd1R7l7uaHdvd4y7j7uvu5+7v3uAe6B7kFvnHuwe4h7qHuYe7h7hHumOdesr49ioaFbHNSk2otXxq4Ib4jaiuegEX4Ia4jci'
        b'Dq2JWxM/D8aQjYZgqPAfZg7+0uCvJ22igg11CdKHG2wauP6jQkC07LOFFbZ+pT2QayhkBqWZSTPZUpg/izSRlkI9acmZHW0rSlShkdMV5CE+i2/pBdcAeJLcxXvJpryc'
        b'hJxEsoVsKxhHdihRGNkqGPDtalc0PIE3kxfm5+XgRmVCjhIpFBw+ig8Mc+noy5eIG++PB0D4OrxbkENa9DkKFEl2C/gudhfqeQZjCb71TF4q2U2eT4Mn8sj2QqgofLAw'
        b'Eb9IDrkGUhjX5pC98MgBfCctJ6dAeiKMXBZGkVbyEKrpR6E9zB/toDcBFNnGIbJPG5zD4yvDSItrCNwfWUc2hZBr4eSmA28hL9eTG/NSl+Lm8FCE+g9VqPGdvnqOVYTP'
        b'kEZ8lDTnryWncsk2AQnkAYdb8WGyB56gyADd2oifz8OXYmFYtuaRbXhLIW0Ubkk2JOpVyFQ8c7q6Ab+IX4IXYugLW5NthI5BfqESKRs4fGEpObWM1UfHMHxKeXxuYkJB'
        b'YhKH8E6yV9tLCM4eLjdndQF5EJ+dEEe25NNu4Vv4VAjZyZPL+XwF1261jfaiwT6KqYF4iv4vMNUd5453J7gT3UnuZHeKe5Q71Z1WOVrGXq4pCLCXB+zlfNjLM+zl1vAy'
        b'9la2x17a7P4dsNcoYe+yEjXSIhSRonrn2c/6RCBW+DMTz1AaClV/GjpOKjy8KghFQFnKsknCWzmDpcJH85QI/utS5rwqVDknoXPIFgzFP8zoo/hH+m5AivdH/p2/Nera'
        b'2nc5WxDceNF4gLui/m1d8FRT6q9SW1Z9iljxv3r+PXxPeI90bdFvua/m7c3ZiDzIlUyn9Sg5g3fBUmpOnhUbC5OcDeiAz5XG5haQHeQVfD4hKScxt4BDteFBk+0prukU'
        b'uy7hW7MdTvuypS4HeZlcITfINXKLXCU3yfN4K7kertEGhwWFhuAduAlvS00ZnTp21Jg0/DK+okD4wbNB5NIIstWVDTVNj8Wb8/JzDTkFeQCtiWwjWwH5t5AWaE5sQlyS'
        b'PjEevwRr+eIa0lgMFVwj+8nzZC/ZSfbBYtszF6HeKaGRlooALKIDq4a/3nQ6RnvpnVApyHPMN8GMrhZgjnnfHAtsjvk1gjzHVZ1RKEWHOVYY7HTyrW8O+77SMQGuvn30'
        b'Wp55wbd+9O0rO6/uG6x8/bx53rduR7z+7LduTF628/i+4xutnENdEUqmnUmI3pmdIlSFoNytoeNPIL3SSVdZKd6bBZOxFUZj50i6cBUTOHx1TBK7GYbPjCMPV8cnwUht'
        b'SeCQCm/nE8n+xc4ouDlfVZnYJz4xNjuRhxsv8IkT8VUno25uvGfBitT4RNKSP0qJVGUcuaQtc9LRIefJCzCWzdn4EorAJxC/mptBmsfpOQ8fq9cLdtpPv4Sn+NhrUqW9'
        b'bpWlVlcpsawkh6XePMUjuKwive9Q0dHKDOYiObvK+5Je4QmqNddYHMDeLB6F2V7l8KiNRrur1mj0hBiNFTaLudZVbzTq+TZwcE0XgJ1OpV1JE1pfFoURRmE8iOBVHM8F'
        b's9TVC0rmTsDb4qGXHJqCb/L4AJeJjw6YUcF3ghtsGsdS3OAZdigqFT7sEJ4eOygSBHfAjp4GFy1YWEluO/KVc6EP5BwCktpsYuXkdg7el5dPNoUqEacHihzUm3UDXyR3'
        b'nyPXC6OegXIlwjfxHvyQEdkicgifI82FCeQU3JqOYCWcJUddkXS0cEttSEFCFJT3QPjeEnzTRbEijdzBrfEF4fg63JiFSOsAcpA9P4ecTo9PGhGrQtyziLyoxzsZbOCc'
        b'u/FlsnuWg7RCdhUqyMcHWU2r8XpY27thDsbg5gSUAAv/oD6I3SLNaeTmRBhmsmUe2YTIprV4N2svrOSzeNNzcCcKGOlpRE7jg3gbAzSKtIThe1AbuQ7sYj8i+5PJXlZb'
        b'uF5L6A28M4m8jADMNXyDjZe+hxbfg5HG94eSw4gcziK3WfkztlhCy1UjyCsISNZBco9xLHyKvEgu4nvhcLkOSMcxRI7h63iXqwe9ue2ZoeQkT5fHihAUEj+CjQq+U9ez'
        b'BKqCZt8fiUaSlwtYsbYaKt0NeAMcKwWlTMMXWffq8V6Yjt1kf9wYuId3ICN5gDey7vUeHkeuO8j1ZRziydnVQdwwcl7DaEUAqeL9qUpfSKpQA1oYsZpr4JpAnLQrGrjn'
        b'+aUKinJsIbHkHO/hk1I8XMU5rm1dshXiCZ5kszqcFXU19VPmeRejCqBokGsK7d6enIl5snzCGH022QNyzRYQbwwgAVwhzXp8S0hNxc15wBOuO0LIRRhtcjcEX+lBTls/'
        b'/vkxhcMN9cS/ZxjeMjESp0RkLv9DRKTm6Ibr9Rv2OI83GjIzlTeWTa+c9956/EC/9MNhr/SZTC6M0k4b/uG8pd9+IW+s7c6jWxnanGtZB6YUDnccHrPh8PuLfth8rXVs'
        b'1qTtiyKv/cM+eUHE6GNFLw1Mm9yat71fa7+Xz/3u8KPXC+58sObQl6/cv/nlVzUbb3wQfuqtkXXbfgs0k05D/1p8Kz5JT7aCoIu3a1T4Ip821OTsA7d6zCBH4gdYchNJ'
        b'U06+QYlC8FWeHCYHciTyd3YBvkWaE0BkA7kR7y1ULeKHVpY7B9F716pII2OLZCvIYmQLvpirRD1H64YJZFdhJqu9AoivTKwZpTaSW0Csyb20DqRTr2hPS9tNXIiltqJO'
        b'tBgpMWVkdARFj2wFp+A0HI/YL8d/pRI0UBIMZWF8BBfGabkYzh7hR2Y5hye4ts7oANWg2uKwU9Zvp4SpY4t4O8Vsew8fdaXV5Pio651If+o6mFIMwHZAnRZ8DB/wwyAF'
        b'6kt2KZaTA0MeQ2gZEw4gtI9nw50qCh3ZcJAkav2rOBINQ81QbGpY3jBVEqAO1mejnQ3PQZkp+MoKPZrBSveMj0C60QVqVG9KOCUskB7dsyoERenCORRhsr2nykcSRdwM'
        b'ZG9PWooCv5QP+LUbleMHA6zPzZmndMyH26Yflnxi+thUXZlvfqMydt+H664cvDZ/q1h8YKP2ZJ/0mOiUBPFD8UNTQqpwrc/EmN6p0a0ZYvG84piyg8MyEjZHzYnIO0TF'
        b'gjsqkX92bAkIBOlo6M97rf98u55nPB9vXUQu+7F1fBnfTsRnJjqp2jETpPjb8Uk5CXH6JLIjgWxB+Daw8hidYlHhaj33ZKjXo6LaUrHEWGG3iFZnnd0o83GGBWUxDAHD'
        b'IAVE6+mHaEKFVfSoK+pctU77yu7xjBJ1ey8fntFanvVBeDEAz6hm0pCeD+iVDVoQvp+MtxcmgSS6BfqWDPOwA3j7ZNyqImdgFZ/ooDv4EI5JfRygXJvUxzF0e0rJnjZ4'
        b'eAd0GyKhW1rfnoBuKPYLtan/qplpMmYNDAHMQmje3OUm24fTBqNSVtp7FRPjiz7IMCVMzBgv4VtECVNsiyapTVpPfA+pMNaqRTDxpvxik60gZ4pUWDk8CsUCPXg92zTp'
        b'VsU8GbPT+6PxAMk5yzQpatgIqfC7fQZTg8WK2w5T/0VzJ0uFNvtwBOJ2xI4cU/nJ8WFS4duaWFQEmsWgahP/uWatVIi4BAScY+qP55qmTZ2dKBXG8SqqwmTvTjbZ4sdM'
        b'lwpHZ8BiQUgT0c+U0DsrSC5cMgLBKjH9bLCpXB/URyq8uTgelUI73+1jmhaWtlIqPK6IQSkAKKvWNOnmzDFSYU4s04A0pVaT9muzvIDfGhpGtauUoFEmbVPSBKnwRb4f'
        b'1RRjY/uZJi3Q1EiF1TGD0CTo++o0U/+B9elS4ZblQ6jQOLWfYJq2PXS1VDinfzQ1i9RrR5om/SdEbtKSucloARTmjTINeS8sUyp8lR+NqgF6Ra4p9X2QcVhhcVYaYAKK'
        b'/Yw3pf4hu1Keo8wUZIJGfO4wDcHOnkg/TJLy9pH15GoasoJ6MAqNwidIIyvHF8h6vCVNgS/i6wilotS8ma5wWr4utDSNHzWJGkTS7D2YsEI2gBa0P03laKD68ej6GklY'
        b'2Ysv4CNpnBOIEhqDxpRHSA+7dQvTlGQXDORYNJbcX8ZK16aTh2lCA2lBaBwaR9aHSo3bibeQ+2lq3DIbAS6NJ9vXsKrJlbSZ0Cxy1YLQBDQB31rKHl+sB/nwuiIeX0Qo'
        b'HaWT4/i+9PhOsjvZoSBNzyA0DU3Dt1e6KDdZvABvcfAGvA4UApQ5r5rVYcNHyCGHCh/Br1BpPgsfRuxh8rK42MHNxVdAK0TTny1gra6aSPY6lOQ88KUZaAZ5fozU8av4'
        b'ND7tEEKSgASimXjPdKl4Dzlc5VDryR3AVZQdTlpZsYrcNZLrKA0AAX/LIedHSbLpQ3wfryPXFWQjaUYoF+ViNznMJFDcWIB3kOs8eZmObB7KwwccrDmLZuND5LpqFL6A'
        b'AM3z166QOMRlsn0auc7hJvIAoQJUQE6BkMvmeDO+OJ5cV84EwRQZkEEF0iETmI+Qy3gTuS70hZYUokJygexnL+SDMPECua4mxwiMQxEq6jWSDQ7eNwwfD0HmJQjNQrMU'
        b'UyWpFOBcCVGsBuJbjIpB9NzJGplPjkwI4bNoG0tQCb70jNSUHeNJS4iqHz4ESiaomW6ykVWSgK/h9SFcPtmB0Gw0G2/sxwDGOpwhytXkKCwVNGce3s5QUxDxvhAh0gCa'
        b'FppbMIlBm0nuzQ1R98cbYIGjefilfqx0tdWBmxG+Dm/NR/PDyBZpXC/hZnIANyvIzn7AW1DZEnxIutGMN+FduJknN5SUOTxLdmXZ/v31119/mMTIZsSuaab8uw050kKb'
        b'P3IcssHobIozRbbMtyDrj0a+Jjh+DHfmHf6gZsdEg5ARkXWhKnpjaMznz8ZMWfY7YedSrnaqaafuuYPDh0XPrB6Rmp35KqdZ9tdvrR+vGrxNGFI662HY+UXL3t23+c3V'
        b'aXhhfD/88O6xOYePnCnddPOdj96cd/K19COhj7S/EJv/vPbdnQNmfHrttSnqGPdP+y/N/21jyVvjvz4w4sd5/3wDX+r72uml1rl3H952fG/4oAGk7M2qGxd1i9+Z+V6f'
        b'3WX7c//574GJcY8+W7638Py18l7f/2rpj1568+f5360647779okXwl+oK/nen7e+d/bAF8Y16HffTy8pnwYSLjUe9iL3GkBOJdfJUQO1oe0A5T8EX+AB81rxPSaLkofP'
        b'4F0+OQG0EmoCANpyiAkKExzkKohuoBwXJOZSI2ckuS3g7fg2cavrnFTxGEFuTwZZdlteDggQUMNLZNt4vg8+ix84qfAHWHk6yIEvZRsSY6kVlewQUA+yU8AXzKA27MJ7'
        b'9cpOxQxFZzKBn/ARJgsfrgojlX+Z5GGjfEjUcgoQcUH64GXx1/+X+wZlX6pUCpAxYqDGKCEMpJoIEKTpf3u0t016AeQaV0V34gxn7+2TZKKZQOCVZI4E2COG0UFbR9wD'
        b'iid4pRkQZQogkUy/erJOiXePTn2MDEOtn8hPhuEeK8M8ocislmSYf68MXTWeMuIiU37hiFRZhlE3hKQO4EDgAEH4k5lmJBGtS+QePgGCMJWCyfkUVL6szjql30bOkUlZ'
        b'4tvf+cRU9q0rO4/vPrfx+MZzB0dtGtV6PHvIJn3M63krPzQbzNWWXYqrMcUHMhKWbi7bHPZqX9Wx9H22Y33fikY/6hF6//4lPce0ssG4dZ6MyGRnOjNlkWv4vFec7QaZ'
        b'+krI5HDaXRVOF8izRrul0mIH1UpCLC0djrWI14DexATaGL+JVzjg4e5nvo9v5umLG3wzvy5g5kdRgrarNMo37clJaKA+riBJn5hbgLck5xbkJeaCEg7qKH4ebw0m62fh'
        b'k49Fg0BR9vFo0EGU9VYciAYqyURVgW/gyyF2AY3lENX5DxZpGCL8nRsD0s9UbchUU+TplHo0w1o6eq3gGAe3vjfho09MC9iEX924lKsI/mDaq0PuhK08dybs1cpXo87Y'
        b'9g05HfVH0+YwVcQzB9ZfV6Kw8yHTj70Gag1TvbcBE98UP6OXn8GSnEl3UjP6ZHKLHKJajb7Mp9cwnWYuflGera5xIKadNhOIAcESBgRpuGjAAHtf//mveOz89/PNP31x'
        b'C60wgs0/+k8HDFg+Lc9v3bepMGz68a6FMgasxOeCSBN5kVx6rPYstDNTPl57ru6MFHSGA2yuT05mcnZMytglK5aLsuYwIELefhj7YUTU2nip8MZUaUMupbIpNG5OKbJy'
        b'xaM5Rx6UHOG+/4npU9Pr5dWVFy0fms6aX69MDrqT+qFp3rdu7xwMFIF7vTLXvMv0oci//YZuzfGF6ky1I7gk7eT4zJGZg4sKQf9VoaLiiCVNPwFEofR1HPC450FWvjo5'
        b'vyCBR4o8Dl8bvIiZaNbgLXgnacb38IYEsj25sIC0GHLwRQXqXawYO7PoSfXf0FrLCqdRdFmMotkpoUmEhCYRwVwU8AcNzGkYZ+/vQxaFR0Ef9QTZLGYR3lr5GEML5cD2'
        b'gT7koRXt8EOezyM7MI7Wyfgmaaa7c3hLob4At5BzZFNhDuXcw8k1ZVkKOVYh+E2s0h9f0iV8UbDNM6VbVamScUZgpm0F4IzgwxkFwxlhjaIr0zatWtUBZ5QSzsRpUikH'
        b'TDGEmlJ3xS2R0OPAXIYzsWezTAlXcqcg69G/HUaOcrjT4y/9B2y7GrouRat4b1lxSsY73wu7sUcf4ZyVey+34pamtfz1xlmHF61Nf3FTb9V3T+gmrBrwafXo/5gqevb+'
        b'w4aZUfvP/urO3OE/bBm597OZf496doT6681VXz/so8x7YZntT+rJs/sMWFAtb6OkAj27yqx3asTjExzZTY7Nxgcms52SySG98thQKnqQzXSzdyxpZVJSMrmFd+fRldpM'
        b'Wgo5pCHbeHK8D24EGdnNsHHWRALzQpqSgWYpyEFjAYcfLl0iUbQdClBAmguobsTjRo7Hm2cmkkPdyUWqLm+1x1FtlaUdivaVULQPoCevYGJMMKfleV7DR36pUNkH+ZBV'
        b'SZEVMJTin0dV4XLWVfqTuU5XByAxFfrsukDEpZUe9EPcj6Lb2wifwY1kc15hooy1EsYu6TkIn1CApHoZn+uaz41HsrhDN3tRpfIpeF0HOhcKf7064OwgCWc/XfZ9tGf2'
        b'Umrly3l7uWxLuZ83GE3VvMSjetOkmL4ZUuHtVA2KiHqLRyZTwgfla6TCb2lCUNSKW0w2MnHyLu33+keiYfnfhnVimnS9Z2+pMKlkABofO48H2WpBcp5sSwlSj0bV2ocq'
        b'NNVkf80uQ3+zXoW0WgJ01qRdP2GiVDg4Wo+KYn+qBOj8bpVsdfk8awpqWBEsoBRT5KPEkTL0osloxdTfUiGuWNnDimx0UKeUpyOn7dc8tDP13fnsuVfmxqCUiNNqqHFS'
        b'8Ci9bLZwJaB51Zn05WkGU5Zsx3muB9D8H1PzqDZjoWzcmarMQOsWmDkoTP0oUd7JdpkVSKPtp4T+JPy/scOlwnGVWhSjva6GOrXPDlZKhcsm9kOjxy+h497ww2eDpcLf'
        b'5YIupzUI0PPi706X+csFYRY6FnUNAaDFB0uHSIWfZIro9ayX6cBVig31UuFfnVXojexWHl5XuZblS4VDC3ujBO3rHBROGjRJHuIfJgF3m/elGgYuoWBSnFR4afYq9I+s'
        b'vnQu56yZKxuMXpsLNG3YI2pFjsyZLxvLllYPRVmK7YCxpiEz7FORVZExX3AMB2z+92fvzn7+zRqSot2kz/vq+Us/bc1f+vGrWz2z7k6fo9u5cT3/xcH0/5z4Teq0+1NH'
        b'ftT/8Mk9H8f8edOjIwNzJv9icMji6EFxZ3Wvll/LULg2pCk24fXqN4oi/7HOjkrDbv8xp3f+aSFkkemLh+6/roj/eOiKLS+I4cN+cW5+fPEvxv92cXFN+bicX004Muhb'
        b'f/r31MXo+wdDbBP2Plq9N/U3Pxr4wV8in407e2P5wqvnbxt3v/rfs2f+GvGTC2cT3nj753Ujfp399qzhf7nSOvxnGeVjQgxFI/9S+dbBLzP/0XNy+Z1ZD9+a9N0HWa+1'
        b'bK5558SCkemTLvWsdTjemPPz3605/eujPz8yrvxf9s/e9PwNvxt6sF/Cl4dnruz1k94Hn6usu/y7/+5+oVV3XcPlv8v/bdvXn+/9YdqHPwhf1mK9+HIPvcAI7JqJA6ga'
        b'uz05HB8OZNdR5DgjsIlkT7+8hNhskI44lFKrASV3pb5U2se+iN3j4uHlOJBR79UoXBzZYszThz6GiD4+6YZE+5vJKQkuN9cuMVbX2ayUpDI6PEeiwxM0AlBi+BvGRIYI'
        b'Tsf2ZiKY+BDJaxXBQJ+BVEq/Qrv/0tWfFP21QMlBLQUqDmrpEB8NB+l0pcVs9yPb3XAVzj7UR7FpFZf9KPZPo/wpdiKiuzqtZI9EsckhsjUXVPtmvJ05Y+wgW/JhghJU'
        b'IJFfVZHbKzsqFEr5v6MSEgt1jUNlvBjCTO886Cu8KDQGlQkWhagQlY1oI1emhGuVfK2Ca7V8rYZrjXytsSgoJ6jkxSAxuFEDJUFuEDjLgpl6q/WoM0TRbnE4DBUqv7Zo'
        b'5D9G9Olup+wy5HMhqtTIPEXVpAGeogaeovLxFDXjKao16u6cfDqq0UqDZJ+7MlZZgsi+eUC20eCJz0heIY399nEOJ1wNeuPdAVuv9sApEYqvC/c1lri/kxWVoXwr9s1/'
        b'rMuqeHFgxr+3Zl/Wniv5zbDnHBPv5fU8c/eA873jcdv+Gj9r0PR7qQNf5n93u7ctxvOPT/Mnbv7ylwvmjlv/n4ajW/Bn03doRwihh7QvZY1PO/k5/v2h0MKDLw96/fKg'
        b'MW849cFMLBmCz5O7dEUNsrE1xVZU/3wnczc7Pp1srcCH/PcwOdDL7uCHkk3pAlmH18lbq6CDn0Rsb7VPA3sb38dnBOZAhk+Pleom93i8JR7fZpCT8BZyND4pEfS7ggx4'
        b'8xSfgo+Rk8yghbfiLSW4Ge8gO0Ab2gG/R/FNNQqJ5ok7vIZpgeR0w3O4udBFjsOSJy3xenxegcKDBCc5Npc9gA/CS+fhEbI9AZ9TQGNPIJWG74MvkyOM2uSMXYCbk0FY'
        b'S8phNhd8uAJFktMCWY/3VzGjF95Knh8KzyTpcwsSI3kOhZBmnrxM7kzqKMZrnpimtNEMtdFYa1luNDJKMVCiFKsV8g5uNNtWo44yKvl3VbiM2Enye9Lq13iECpuD7aCB'
        b'lmp1rvRo6uvoLr9o8agcTrvF4vRoXbVtZo/utBGVfSS9ptvL0p5cLE2ou6g9zkc26JbXl35kY3NfP7LRoZUBMh0n/5XQ1+lybECLJRmNM5zjPBqjvGUI1wqHxVbZ5tYg'
        b'DZlmks1cUy6ap4RCLZ/TGldFeOF5bz0xQD3nURrpiNkTfVB8oOzU/S0MXrWnoHZuGV3VWSnVGWT0jn+X9YY/Vb1VUr1qozSbXdYa0WmtAWJ0KpLMRUA8/wcBmv7wqD2x'
        b'EwzWhjFZSgelDdd2z/3E9KHpDdD0tZW/zRdQz8++PMDjqvF6ji2tqUAvzvgWJwId/ghdnOm4SUJqvtMFE2p1+Jnv2vzJ1sJv9KpeXkQIeEryiRHsSbSWNsz3B5DoG0Vq'
        b'TYuEwXNESpi9Dn0W5o/bnYMAMk9/9CGAv0bqyGY0eoKNRsk7G661RuNSl9km3WGrB5aova7eYgfUY6uMLbq2pTaadZY6vpkdjgqLzeZd6+3X6zmKbdJj8AjrAjUQ/IuO'
        b'DNVlNUqGUF9H9tBy7JfnZXfdw+SO0pGfo89NTFKhYNLSczHQ1pBRHaY5RP7v2Mb5sXCuTNgj7AnfEwF/oXvCrXwlD1fyr8i3qMQEyuL9vHEjgL1SJh8E7FphUQKTVzci'
        b'YOlBLTwweqUYzPIhLK+GvJblQ1leA/kwlg9n+SDIR7B8D5YPhnwky/dk+RDIR7F8L5bXQj6a5XuzfCi0LBhWQIzYp1FTFkZ7IlJxom8Lx9qsBdGkn9ifiRbh8O4A+q4l'
        b'XBwIbwtlEazn4eKgFl5MlE0ogqgTB7O+9YDnhzBYQxmsSMgPY/nhLN9TenuPeo+mUtijEEe0CGISE0IkP3s6WmHu8MogMVbUsxqjoIY4VkM8q6GXKDCakAyCTgUjl49G'
        b'Buv8fuRS6QBAwB29yqOwgpDqUVBc7Az1DBVqv8mnyyXMu85zKemQJKYgOoDyxHrdr8Mqw2SSombykwZIitpHUjSMpKjXaICkCExOU7zfFyhTQPPoT06t1Wk126yr6MmF'
        b'aovOLHfGCgzMXFtBjz60fyW93mw31+hox9J1063wlp29mjMtw6Crs+vMutREp6veZoFK2I3KOnuNrq6yQ0X0xyK9H0tfTtBNy8nU0ypiMzIzC2cbSo2G2QXTphfDjQxD'
        b'njGzMGu6PqnTakoBjM3sdEJVy602m67coquoq10GK94i0hMZtBkVdXagJfV1taK1tqrTWlgPzC5nXY3Zaa0w22wrdbGipd5uqTBDPfokXUat9IzVoWOGbagcOtdpXctg'
        b'UEXgdR3bK48fRYl01nB65T2A4h1/0GqAn3X5ssy2pfflDAxiSWFi2qixY3UZ+UXZGbpUfbtaO22oBEkXW1dPz7KYbZ2MsBcodEeGCFedt/hJ6vGya6kub+6b1yexaak2'
        b'6fob1NXBMt/RyhpicFFBjZwjhzOpTTJhAb6QRE+H5M0lTXlkW4ESUdMaSOIn8Glmp0jP3IH614ynZo6k7+o0yEW3avC1sL7MMllEmujxlGSyBa4KS6Q6ZmfTbd2CgpwC'
        b'DgTiUfhFciKI3MKnbKzC92JVSJv1rgLpTPmVz+UjpjTiuyML6GZxfB71jMyflU3WpbVJ6WSXHp9DJRlqsp88xHtZNeU6HilSRqipY1P8RNnf7u3BSqTRlfBoqsn24/gg'
        b'5KInldInL/KvmjTlg04KTU0uxnfJg2yyNV+FZpLTKnJ1cKL125c/Vjpuw1uXB9wcvmNU5EZdxPTe83r99FTuB6F27V93jk2zxvSrKj423Drt+m90p9/6/bH/LLi084+j'
        b'7v/3y/nfacpb7Pjdvh/kLhr+xZy3xT998cb7wVVbf2Ju/Plnk1pT8Nx3n1v1/E+xPXLiR6cyo/75xdR76bEXi//c91+Vxx5O/serhfENr21Zfr9149gZWzcNPfMD9Stj'
        b'/zUj+L3slUccb08+n21KDPvOwGNfvHsb37oS/+mmlHEbHq6rMR8t/X7ii7vGP3f3+dY1a76c+tVPavXhTh0d0L3P4Dsh+GU2I/oCV2Ic2ZrMo17YrdBQtxSmz2TiO8DV'
        b'mxN8LgC4idyX3ACqhrBqLKQF38hLyi1IyMEtZAcdOfzQJaC++IaidpJ8HmBFKG70OgoU4Va685aNDzupWIGPk4PJefgqOe3dupIqEVAv0iiQ2+QaWceku1FzzbjZe0+5'
        b'jBwjL3DkLjmJNzPzO3moWgb3G3ML2XQJpJXD23lylr37DLmJb9C3JQRWjuDJXZ4jl/AVphqCHncZ32SSY5vaF4t3U82v1eak68HQF6DjUwPhvp4d6ZK6K9UXj68rySZ8'
        b'aiJTQqvwLeLGzTFqqC6fg5Yc5fDO0fHsXsJz8VDN3djCpALaxlv0gNQp0spU3xHPxNMmFlCHiAR2Uqt5UpWQvtDBurASPx8CLfRKV2H4es9MYQYM/iVJM30QP5C+nYC3'
        b'Sx6yYc+Qq/iskGXCD7y7UmH/s9mqvewMoqkVeKusbWZ5xeZUDXPh1PIaZo1ScGG8lovmqV1Ky/IalYoL/OXhl119qVKB9iWRtCRv9QZJUg2SBO5naDIVebXJdnJumzj+'
        b'xOqzXi1V0iuwdlZnkq9iJglPg2RQgDD/wQh/Yb5D059IGWuUNFWlkcobXapiC7yqWBsUr3r6aHipTzihXAF4t5ctxNotZjGxrta2Up8EMASxruKJFU+qMRvLrRVdNsno'
        b'bdKjYbQBINp0C//pBoPJk11BLvdBju9evHj6BlA13h6PvEpcJ8AtPuBJ/rLJ/wI/WIa/mJOHQM/D8jJLqqGEnl21pjpwKLqTW75pU+yFvgXRVSuW+FqR/CQSz9O3pMqv'
        b'JfruWlLra0ni46Wlb4adUiu6asBSXwNSSpmOALD9jWU6eVp1NnbEuss2/G9WFkmjUzw60UEMzKRivUNnbbdSHRZLDTvaDYoFk+w7vEiPe8v6TgnoF9Cz6S57na7IvLLG'
        b'Uut06DKgJx2lzljoLnQaXlw2Nik1KUXfvVxKf5Soo9W7VD72ay7DJ+Mpj4slbqSYyuHzuAU/sP659ZSCDdJv1b/5xPRGebb59T/GFn9oer38U8jx5X+MejXqzKI/hr26'
        b'QqXbMfhAv5nr0wT0nReDxuw+qVcwFluNt3CBPBQYqCs8a2mmk25vkEup+FxeBykFH8AnmaSCz9glC++tojzSzO6CcHPaew76Idkp7SltJGfxqTyyNR43gaDCL+KSyQvj'
        b'u7NQqalhyHtIR3YnWotWBXPR1DAqcwL5GYlT2se0r63NHEV3j5wBHGx7WKCpNbBGkB6mwoOP8RWiGjto8U/sKyTr64/cHXChxOKUtHSXzWkFHVWm7S6HpIeyaAM6p91c'
        b'6zD7BSYoX9mhIlpHOrNXpJsK4BmoCv6Zqyx202M0I/rT0RQp+59Ex2xH/blvccEpJsPfikA7oWdwsXsWvuCv75CX1d2pPEzfIWdwk/VcxuuSI8KdATM+MeUC0iYUf2T6'
        b'0LS48lPxY5Pix/pt7yZMjxuu1U9d1rPo1MYJR0ZtGnxgfVooym2O+zRk/5QIPc8k9eEgEO8OaRPlyfUBXmm+UHRS/lFpxVvo5oRPgK0l+9rLsEp8U/Y3etzWpMPiNHpn'
        b'iHFqfy8m+qv0inur+ngxqsM7Bi8wJmVRNOveq4k9keRDZXrecE0AKjf6+zV1A/hp9g/CAl/tkupvDWQ7T4q+Sd7jSlQ/6NrDivmqMD8Vatjz+ao8zr9KYP1QvA+KSEe7'
        b'mG+p1dmtVdZasxPaZxW74pS1luUyDR+VNKoT40LXFhVRMluwrnu9JAFQkq7YstRltcsjI8JVhVMnWsqtTkenVhy60KEFjroar8xlBfZptjnqWAVS1dLgVlrsjq5tPK4K'
        b'qUWZ03KAMVuXumh9IKvEUiass3tbBbBynGbKlh9PLzr6OGoMLhrBBd8ZjfIMdI+bxTswJM7K9vlmFpOm/FnZQrEen8vRLSq329dYFwWhaVXhGfhoTQXZztw6DfgVFGD5'
        b'SJozyFcBwtfI3tnAtfZyS8lNzVxynzwvnRA5HP8sua6N4jl66BThI3gv3uuiC4g3kLOOMNecbLpDOZs0rdUmzGFb7834XGl2AoWyLSefbOWATJ3Sr8D7hpEzpTwie/HL'
        b'2qJ5+B4zx5Bt48h5/1bVh7lW401ypUVzE+eoUdFaFT6FN+Kz1lXzbwqOWnjtzZ2qxDfuUW+86bPW4jpuhjkiZt2rvbL1mp4RW1+LvqKfc+xqwqCFmdvq3n2ntl9EtOfR'
        b'4Za0Qdo7fzieNzWi95u7Nk8+MHVV3OXTW2t/trB1yqEZ//psvrXXA4vhx3/t9Y+/fvnLX01dfWtGT9efQp79ve56TpE+SNo13llai1vNQJ69qnVILU9a8Wa8wUm9FUKS'
        b'cUtI3ARgzC3xjDR6bSGD8HUFeWkkaWS6Oz5LNoe1HYvE91fyibh1orStfX4mvl+H9+T5WRC0EUIvvLGcqecivrTcjzgnu1bKtJlsqZD2vRun4nswZ7LgIAsN5E41I+4g'
        b'YxzFbv9Tl6vIOclBeUE+ex83kYeVA6BTzf5WB3JalGSODeTCtAExcLPN7rD8WdlZ74k8USgFbaMS3gObQ9rIfW8NaO8SydfKhF/KqdrR4YBaDN42MKLuI4PdcQHB77E2'
        b'VrAQkhZO3qFirGAd+iKqS2YQ0IinU4eBnHXJAk77WMAopom10bru1I+n0D7k3WAFPb3SZSvO+loxsVMilzk7s73RvJP2UA+gGrul0qNyWKtqLaInCMizy24HQX9GhcKv'
        b'rdSGrPVSvxkSm2qL8ITcIbI7jLZSKzMtRZMSmJYSmJbCx7SUjGkp1ijbNJf3D3bLtKTIVpJgx+i/vzLT9ZYO7ZNE/b3v+vz1uza+sxGQ3mKvwOjRMjNV55J0meZaqjOZ'
        b'5Xvli4GPdcrA6MYR8JSSwvFjU0axLSO6nSNSFRXUqS7B+wY+XTfDZq7SLa+2yBtS0GHa57YnvJ3qCnxtnbMTMHYLdKTWka7LaC8xm+TuPAEH7KizBRtc1CZI7ohkZyAL'
        b'JE0yLZ6dDUXFEkfEL0UkcKmReDfeTa7nkeu5INSeCiMvkEv4hGsiJWP7gUafzEtKjMsFIutfCVRekCNVn507O1YOvgCiNjk9QEvO2k2SR+WEHM1fkI5DJlNu/dpxyEXV'
        b'pJQZizvfqCCN+F5ibkGJv+DeXBJEHpaQS4yzk73E3UCa2TMEFML4HMo64ykz9dum2J6dkJufRK4W5STGqYCR67VLcWOZi2qq5MWhosRD1xTKj9PeUPCxQMVBNE/QJ+Yq'
        b'0SryYhBI6tfwNr3gYqxoP0+OMsgCUkzh8slmfCEaH3FR9XN6JV4fD2/jLUugggLqInWQfw7fxsddzMfpooVsic8tkAdRO4pDPUcKwDgO4FPWk88P5Bz0kInu0+MD3roX'
        b'SlK0iqJiYzOXusn9esRHb/+yZee0Wh73zNIfGFCc3bq52PFd4S/1u4I/++I723q9F3suZtHM6B9cOH/w4+Glb/yzvmHiwmU/2fCL4+4/3Hvh6B8bf18cWhe5KW6Ndeus'
        b'lUFj3svYpHj2w2PPDvrzpneFhSejJ76+64Mfzvnv1eQPviu8/Xn43hfiLy/P8nwCLDxaYm9HoI0Px+Ux7saXc6PwK6PYBsIofLMqJK6NdZMXyQZ/9o1fIC8yFhkShne0'
        b'kwE2zyatixyMu4+syMrLKSBufRyIVTzS4GYer588VnId25Ap6Vb4/Ox2OyXkbjFr4GR8Cz+UXfwVXA45iY824JPsVmkGfplGc8tZbqOupyobPwTvKJI2Hq6TB8XMPbVQ'
        b'ivqRgI8bYEKSBbJXNVeSLC73LQzcFqgSYvGD9GSvpqb9P7Llh1C+KFMPxtyT2pj7eBWLyKDxsfZg+U/LTqpQ0z3/32Dlqp7+PFauS2bxKolZU6phF2liCeTzQU/nP6uQ'
        b'arL4pADRxwKrILnQThT4+RB/UaCzZj6Ng5fG+1KXLPgNHwseTHkGUFTGQXwsx9/kp1cwRx8e/rgZ+mg7tafY6R6qnep81KFPrKswGtnWg50aG9gWhUegdvmpNNvJLohH'
        b'7bUcU3MPU5Q9oYFqLJWY/ESpKvaWt19synr8H+0XdYVy9smQ9KEztRkuNLxCESUdnv1awSNpOr4emM6Q6yuV8A3/K8KCtVxkMOSkaDaKYC4quv0zkZxukHQthTK8CbrB'
        b'y458gyTNcyhYhS+u4sn23NEduF6w/N/xVTtfJpEvU4hCmdKKylSiokwNfxpRWRYkqsqCRXVZyB7lHs2eiD1cpbAnQtS08GIhyEkh7ohKgbkgUy8drSVUDBG1zGcprIUv'
        b'C4N8OMtHsHw45HuwfCTLR+wJs/SQQt6A/EUdacLdPSo1Yk8xivodQY2Re8IAboTYq4W5S7PnelRST6be8hM9oU7qw0SdoqPgGerT1Ffs16gp6wVt48T+4gC4jhYHioMa'
        b'UVlv5qOEymLEIeJQ+N9HfmOYOBye6iuOEEdCaT/md4TK+otxYjz8H+BWQU0JYiI8M9CN4DpJTIbrQWKKOAru61hZqpgGZYPF0eIYKBsi1zxWHAelQ8Xx4gQoHSaXposT'
        b'oXS4nJskTobcCDk3RXwGciPl3FQxA3KxDMI0MROu9ew6S5wO13HseoY4E67j3UFwnS3mwHWCWwPXuWIeXCeKRbIRRhALRENjUFmSqGCy+SyPKqOGOU+dDxCXKAmQbkj+'
        b'U1LYVJAEaTi7Kjv1u9FJ8lvFSp9LTzu/mEBvLDtUUGNxWit01OPPLNlBKyQxFAqoZAl1ShYV20pdXa0kK3Ymy+l5j8q4zGxzWTxBRm8rPML02cWGR5Oqnc769OTk5cuX'
        b'J1kqypMsLntdvRn+JTucZqcjmeYrV4D83HaVKJqttpVJK2psepVHyMwv8gjZs2d4hJysYo+QWzTfI+QVz/UIs2fOm3GO9yglwBov3AD7V8D2RwOlwrwjmFLi1XwT18Bv'
        b'5ERuieAY2MAf444jR5yTF/kGPhrRQLhNfAMg82pOFBq4JSp7WQNHHQXhLe6YQMPniqo+8FwMikLj0GquVgP31fSqCdH3GpBRAbUqjwPdN6pEDaP8Qe8bO1NH2vuWyfPc'
        b'5lrW/oWuhHw2EpKKYZbqYCXdGLGkIUtnDlslhYmjU0eN80cjETSTnEoq8esc9ZYKa6XVIiZ0qhdYnVSLAGbo9SJjkL0qooSyoKjYreWuLjSLdHo73SRaKs3AZXxoZAJV'
        b'xVpRTWu3SuMEyCjDAQTr2LeP6Jw/6mWtZftPbb0ZOdwx0sMlebiUjyj7+Ohr+HkkJKWkGPRqT0R7sHTHxGyrrzZ7gufQnky32+vsHqWj3mZ12pdSRqd01cMysdsRMygw'
        b'AYIimH016vaoN+PBv/PJFsEK4BlRsq1Dx1ORaFW4hABPv/+v51jTuhQp/uPb/feC8G3+J7ZHGjZ1K+stOhNMSQUwfVtSlvTfZEqyUx39KQzgbJS6bNaXPkmnH3NB6BwR'
        b'O4DjveAiZHB0DS/mQ3yu6QKbEI/G7DAyP0uPxrKivq4WVNwum/K1rykVzCXAVVMOSjIMhTwGunqbuYLut5qdOpvF7HDqUvVJutkOC0PzcpfV5ky01sKY2WEkRZOJYqlZ'
        b'XOyCB+kDgbV03KkNPAjEsQAKvmjXvoNAHDPYd79rW6lXvP+XzojN7HoqnUmExrKiotpcW2XR2VlRuZnuMNRJm7PwlFlXb69bZqUbr+UraWGHyujWbb0FeEYmHVTo2DRz'
        b'7RJmY3c460B2ZGSh9olIgLz8vU0ysiaZ6Ni62JKXCAylRD7bOowtdT7tZNeOxiC3OKvr2vhXgs5hBVoqV0Nfo3voAS6sXfRRriidRjFPN8mstZPtv25NIuV1dTRYrK7S'
        b'3/biYlMhtpuGTonjcosdlucy4IvmcuoM0IUVJkC0pMikQO0NKmEGKYDyJvIQvxSfmJ1jxdcTqN6bN5daKcj2bLgsnB2bm5CTqEI1kRrykJypd1FfFrx79RjQI6+Qm7Oo'
        b'eeQkvkJD+u6IN+Cb5ERxIjnDo9EzlVV4Oz7PnPm1FYMdSQW5ZO9yVSTeNQiF4/1CEt5VxhqAX8QX8H5/83+sITEuL7EYqmbV5ilBRtXg+0X4Hm6Z5GIW6i2j6x0skA/1'
        b'wAMR+zjewZErRQYWzRwfJmeTS3AL2TObtJC9s6ndopAj10eSG7MNM1ySin1A59Dgl6BVSiTgAxxeh+8UsbdN5OoqR7Zk0sjDlxUIb+7TAxqML+IjUVIYW7yOvOKIZYGI'
        b'lPn8ao5cCsEvllpnPniBc7wOD/y75v1eLRNrp83SZv35//0hI/Lszt8syn4t7OzQvnnPT1PmbPpUVbyiz609fxC5BPV7tb+f4Lj4s3U/6pHRevzMS7+vfjdj6oVeudoj'
        b'JzI3TwxOmXf609jX//3K19bSv6zIfPOdPufemvrm7sTywzd++ftjH93W/ik31aU/qtv740XV79927/j1lR+N3jh6U/YPVn754aE/720d+q+SB1/+ODf4tZZfht32/LI6'
        b'4q25hvcXqv/2zNtLJ49PvPrrFfPwg72vtnxyzjiw4r9hG8d/cfyZ2/1Nj1bzqcXPtEZ+R99DckK4Tu7j+6Q5luwHlCDNaqRI5PClYq+74Ll0mPtEspVsSc4mLQLeuQxp'
        b'ZwgqcgQfkUILHJ3SGzfHkIfJ8BCHFMkcvi6Q49K90+QCuRVfEJpbkA+3BnMweSfxURboAN9Lg9nPKYgrUCNV/mQFr5k5nllBbOTA9LwJMME04BO81ZvDJ0xVTnpwhbyC'
        b'H+Bj/jacOLJ1KN7ZZsK5gc9JB/Q2jMKvxCfp47x4FE6uCaQJP1wppkheoK14Pdmeh18hD3J8gfXJxVIpruXL/RXx5Bq+Ir+sMHD4Cr45lUWbWgNNO0INLTkJSXhLMqyt'
        b'BHxvNVSh0ynILXIrgxmblDVkd17bSsMtybnkhYFstcWR+0qyIQPfZjs2pHkiuZEnRbeiK4QbQ3agEJEnreSFaDZSE8nzqVDDIbw5kUP8Mi4DHw2VhvcWOe/yHUimhycj'
        b'8lYGjWKtXL0qNq8gL68giWxJyMMtheRKLutnHN6uxC/hTSo21uTI0pWkGW+rNOBLCSqkyOLwK317PYU/5Dc5eNhLoojGQCbAexmibElaiyKDuQjZhkSdRKPgv4qjBxQl'
        b'+1KY5Doql1L3UXZMsb8s83QKxOA9yMSOGH4TB1BOepWJErsoP4cKHXQoZfvROvR1wHnEbpsDtVE5smuPGRYthYXZAvGA84uWwrMPWXTvNUN389/pTDjIlLibfMRFkgap'
        b'BAPMhjIsn0AmywhUYHDIMn5HXiTvJrQTMtqJFJ2LEB05W2lHccVMWWIAB/cy1DrK6elWykoqi3RsmbmiWtqar7HU1NlXsp2fSpddYsoO9iGTx3P39ipUoOjq57boNNur'
        b'QF/xPtnt3kmtb/NEwg7v3olXiqKyj8Xhr+w/Rgjo/Py3RvJDihVo0Nazo7VFpnx3iRxk9P9NG4DGo3WDobD/5IVyAI+Q0FsoRfs3QMepS+eVbU2TQqudL012hIbirek8'
        b'4sh2RC71N7hyGCfm5+a1Eya8uzSMweID+D4w2VK6yT8XmD3dc2nzGgBitGpgRHo/3Gx9p/wCcpyly2uVoqBlYhhOiciq+nnY4Ib0qB5LL/6jdM7O+qpZ6aHWfZt7Fq2o'
        b'+zY3PuaW9cPfbPtNdWPPqPDo6OeG//B474lD0n4YsXtb+Zmm+rdaWvb03TTzQOqlqO1rGmoGPNdvhPXtsh/cmogPen5xY1bRR7ccq+vfaf0sLur9X352/88LNvQtKd6x'
        b'6S9RE6L3qw7tXH35nzNv3/3rx38/+j0h7N3mQ//8Q0b2hJciPre/3+PXfwhZsWn8/bUP9GESAd6UjVviw8gBv0BhBXgLM8eXDwb25idoZOCXwucINnyJXGC8DO9XwagF'
        b'cggve4g0AoMgt/A9CcpL5GyoFO37MjkgxQyavSKVuRri7SPwvQBC76XyJfgEJfQHGpzU6pszmtz3bjqQW2r6EZmTSOKUx8kuciK+LeJFiNGFr/HkQhi+LAkIl0kjPusL'
        b'LFSAD1dy+CEw9kOsZi05GBLv45OrVgOnrJ0uhWW83YNsDWSUObg138soL09x0iM19SAgvhgv3QQ2dcsUMCQ8cOGtnDFZg08lEzcDSA4NSojHB0qYk4QSqRbzAyOtEiu9'
        b'lz9L9p2Ygo8GHFPZtlDaIzmyUIxPKABpVI6ZjhvFcLxbsK9Z3Nlp9CflaGpZX2A8bJI/D0uXuJeKHWbQfs3zwV/xvOYrXoj4L6+gHCuYxXkM8zlEhHGrwmSWIVca6Pq2'
        b'OpBxdRNqg5eebfN82ANJQgd29Y5/nKT2sDto45TQMG2cVku1cfijdrO+Iufk4VrYyEXDAyIfkPPGrHjED7c+UgxPSgW9lbXOozXW1hllfdnhEczlDsm80onm7okw+vbB'
        b'JTOkgfceweZh4PhVvb0WlXbPdbAV+jag8yFpYt8z2MjbZzRwrD9oiWCfSvtlj2vgjtF+oOPcaq422imIXAPL0ycrBcmCCNcK+k0ExnF5w6ORPv5ZY3VAMyqqGecZDoSf'
        b'GqeY3kwvYO7YEPS01tTbrBVWp1EadIe1rpbNlSeodGW9ZJJigyLbnzxKxqY9GsmgW2fvwhk4zFhvtwD7shjZ87N5r/sjDcYFmBfGU4xUwbyv6uUduIA3Op18Nmwstig1'
        b'gcJQUCPoYq6Sj0beAYiUaoulnUyQump/zjepYYGt1BiNANNuNJpo+5gg5G8ak+51jYaRrCVeRJRbUUVboaZoBqPuB7odPqmN9BQ91O4HOcwH2XfL90OvFV7AMQz/jwEm'
        b'iNxx0BIp+AZuiW8QuEnnePtRJJsL4Zqtw8OdNENlNNqcRmMlL7NuBLOzKtTXDnrvqZvBeUeBnzTZfpqCOtMFZIvRuLgryJZOIPtwIMl/6QzxLoolfJ1OagOQBSqUsnJ6'
        b'xYx10mTQtnSBtNAky1KjsZb3OrAzZA0GwunXMPpEh4b57IRaNiQUqNZrI5QAdDEEtdBNpx8KtMGp7WwAHjf0CmalpRgwpduRr4J5Xd7FyFd9kzlXegHzU7qfc9A+jM91'
        b'BdnSyWrzebjTofWu+jarbxvB7ri2qUXMaFzb6dqW7gX0M0COHdZpP3vTTR3EyDC/kfcNdvw5oW25McLqjbpx2Ffarnmw/s2iaDRu8LERpk360QB2u9Ml4IdptIHHubYD'
        b'Pze7GnpK6liN7s5JXUdoTzAcMe2Hgy17LtF+ncK90Xm3Ha5yo3Frl91mt7vudhhrSEhbx6mvof1Wd91mNe7ovNsdoQnIj85QddtHZ8KciNEUyEe17zhzuRA8YYY6Zw5w'
        b'VAs9aGQR2/CBDUZXB2eMxhoXIOMuXt7XQExsCxgV9sBTIQOo9/e7GxVW44HOR6UjtABkmOQ/KrqOaNHPN0792o2TLIxRJEluQ5IuxiUESKPdZRGty4zG1nY0mYfRifQ1'
        b'2PfYN29zX1+b+3bZZj758Y3WAjO11dXZWXNOdtLqnr5Wtz33zZsd7Wt2dGfNltbj8Me2Ws1C9hiNFzppsB8S1rWnEQr/thahQKbc1lYnbS3d64Z2tV0v4FfzqwW5zcJG'
        b'2npBuqr0tp9KMx4VjBGABqmd0djvIH9C61VNKKH1KJdX19ks1AW4xmytFS1dSafBRqNUp9F4nffGKmc91vI09n3w16t6+HrtfbJriZTKgRJnCmGT4aMIXUueLP5ZldF4'
        b'v1Pxj916EnjBbfAaHwevvs5hND7sFB671TW8KAbPKcHifDSvUtoAPRAwH11BB+XKaMSdQme3norv2690A8laCwLMdzuFxG79H0EKYgvYDBW+7gcrwn9105v2jagTG2vA'
        b'+qarZAmyRzhBc2VeIZwoiArKZHpDQ1bT1UE1Qb6JPy6tF3mVsCYqDR/RSh8NYbvB1toqXX3dcmk/eVSK5FXhqq+vo8F3HvEpSR5uFKyYJu+UeTRLXeZap3WVxX8xedRQ'
        b'U5XVCTqxZUW9V/3r0gABI8GAG40/aCMfGhbrM8x/ROSHJN5Eh0Wf3M6L0L5Yrs9hq3PSsF7U484TFmi3hnxlpaXCaV0mBX0GkmszO5xGyTLrURhddpt9P62NfqfRzx/R'
        b'h6MejU/pD2GmUGn/lZnUmfJrp7GcJWpznCYnafIiTc7R5DxNLtDkEk1eoslVmjDp62Wa3KHJXZowJvwKTR7S5Ns0ITR5jSZ0T8/+PZp8nyY/oMkbNPmpd4z1kf//+De2'
        b'cxmpg+RH1GWEulFoBIVSwSs4v1+gi1G9unBeVFLf2oEjeZjyGB3PBavCQrSCRtAoNIowlfRfK2iVGvZHS8I07DcISuVfae/1MDld7SDbSIvkz7igQhPDu1aTlzq4Myrk'
        b'/45ftHNn9MY0rVSwCKsaFnCNRVilYdfkgGssmqoYxPJqFoBNyQKwqeWAa1qWD2X5IBaATckCsKnlgGsRLN+D5UNYADYlC8CmlgOuRbF8L5YPZQHYlCwAm5o5RyrFGJbv'
        b'w/I0yFpflu/H8hGQ78/yA1ieBlUbyPKDWJ4GVdOx/GCW78mCrilZ0DWaj2JB15Qs6BrN94L8CJYfyfLRkI9leT3L92Yh1pQsxBrNx0A+geUTWb4P5JNYPpnl+0I+heVH'
        b'sXw/yKeyfBrL94f8aJYfw/IDID+W5cexvORISd0iqSMldYhEZTrmConKBjMnSFQ2RJzKGFqGJ5yeniltO4b6/pX2W0reE5t+D8nR39o9Rl0ymH9IhbmWksVyi+z95rSy'
        b'DR2vFweLLOb1i6OOHNLOiSVwj0feWQp03KA6lN+ZWRMlwmbpAJBYV+GiOoGv5oDa6uzeCq1OyawmverdqMnMKCjNkmswdeG0F5DJqZS9UMy6cmYEhOqk/TX/M70JEkhv'
        b'X2XHTKfdQgckoD6zg/mB0sYx35BlUJPZZtO5qJBlW0nZTsBh4YCXAxgu1fkowaER8x00OkoDZ4+gHLAPauKXBNljvFzQyayfx7nVgggczyilCpYqWapiqZqlGpYGsTQY'
        b'5E/6P4TltCwNZWmYKEAazq4jWNqDpZEs7cnSKJb2Ymk0S3uzNIalfVjal6X9WNqfpQNYOpClg4B3C0adyEE6mJUMaeCPDT2OstDCBSDzKlYrGxTHYI0e53ZyDqA9DYre'
        b'aLWiti8rVdFS+zBRDTx+eIOCGhVXK5wjgOcrNvLw/CTnSFHToJCsv85YWt6g3ChwaOmnTdC7xWFNHHtugVO/AVog+YQa7G9SGWGMtAA6LJfuFwRjEjM8nNHDG42PlMbh'
        b'juGOR8PbV1Jtpp5Tbc5Xkuk1zqMtBuZvrZGdG1XSVqMUCFQwWkWP0uiyOO00hox02METLoUS9512s2dR9kS3/OzUYG6n2zZSXJMyJhwEHpIEAVDaU4Ya6112EGwtAIIJ'
        b'Bmpmj3eaPSpjjaOKgV5CDw4qjRbpHztGGOp9jX11C16qqKb7oSwCrdnpcoB0YrdQQ7nZRgMh1VbWQYvZuForrRXMxRkEEolm+G6ba5xtHfJEGW11FWZb4Hl9Gv+3mu7i'
        b'OqB9bM1CNey/FBfY09/YbshBnIX1KD+rhOsahycYGml3OqjjNhOtPGqYFzonnrAM78xIM6F2WJzyDYfDYqcVsht6leRjQO0QHtWS5fSL5H5xDxrQ46MusNn9gIqCZUwU'
        b'jGBeFO1DaWk6lHTxy0v/I5ihSMs+7UvTSG5V73Yj8lRhl6UzqvYPEeraazQaVCDJmTWmPSifV+ukUualULuk7YBmghRHwVknH2ilroUikG5r5UogyH6E8imcXJmZK7O7'
        b'xvbxNvbRiMAoW3RLv6bO2XaKlkX4fJooU9ndwe3vgxsYXKsjWBpS9MnDF9nzuoM6KLC3/oG12oGVw3c+cbjp7mNqDfHB1XcSU+t/AM26XNId6OE+0L/M0ElRXR2ucvmo'
        b'BnNgp/Bkxxo5dFO37WLCk1QR26qksk49vEblFBbappNgUEm6kraySquFApQFB6gdHmhzu/HxAocuTh6nuAS4tDrZf2/orTi2KRknxb+KewqsnN/dYCX4Bmt0xzAnXeBn'
        b'xrS5GcmQTH9CLJWCk9s/6q4dyb52TAo4a08jiVjKA0/dt29PZvH0rOSs6dNKn2LVQHs+7q49qb72FLPZ92PhsjOW1ym/nZdQki6LhTyRfKJsy80rHfKBc12tpcpM1fGn'
        b'CQ5g/6S7Vo71tTLOi+peTye/BsucWhdbMmdu2VPQM4D+aXfQJ/igj2TEva5uCZVwpWPzIPjW19fRI1EgIrmkg/ZPNT1/7g70JB/o8FLfCZenBvGX7kA8E0jBamDNmqss'
        b'fmhYX73SQb3ddEUZOQZY47YnBC7vyP21O+DTAoe2DaitrioQpi42r3j6jKeb1c+6Az3dB1ry9KsVE511ifCvjXHrYqc/Ocwqqbt/6w5mtg/mgE5DOehiC54OIHTy790B'
        b'zPMBHCy5M4KIWEtPg8hLRQqtUTS7uOjpaMrn3QE1+IBGMhrHJGb5YMtThSv8Z3dQZrXRhPaUi8rZ1OmGXsdOKyzMyzHMLJ0+7ynp5r+6g17qg/7X9tADpf8k3QygETMt'
        b'0J5aJhc6fKp4Z5HYgXjNzZlRSuOpJ+hmzslM0BUV5xRkGApLMxJ0tA950+frE5gTzwyKMtVynV3VllVYACtIqm5GRkFO/nzpumT2NP9saXGGoSQjszSnkD0LEJh5YLnV'
        b'Qb1a621mGsBKCvfxNET9390NYZlvCIf4EXVJVZIQ08wWo9kBo/g0y/4f3UFd6IM6tv3ESRpdki6j7ThajmFGIUxBlmEmpfQUlZ6qJV901xKTryW9Sxm3l9RImEKR4k7d'
        b'U8iosFa+7A5URRuNl0OxsPONEiBLm1nIXxd5mn7+pzvglYFEr43YUTdvHbVldcJUvE4mbFdkjgzQYWCecDFsx5C5WNX3p9fSCVi6CwJ/io2QGunzSuY5p6RvGll6TAWp'
        b'+jjH+Y3do4nFkis0tWj5ZBxJ5GqzrXUukiXpNfY/0W4uoUm7AM/MJkFDGNhrENtobYsC3W7rKIR+ME2u0ip49x9Bz41hnzyiPpmr+rVXOP3e6XqmqHVN9DoDlkogO5sm'
        b'ulvhENq2rTqotz4HmS5PRMbIc2QPozu9xxHd2a1q2ziD/n9F+6qgRopOPeA0sgHDuEzw+YJQs0BnjZEe7LrfUX6NkeLw+kaBmb68rVFKekgXDnk2S63R+Fy71nRiZGDP'
        b'GfRDO9u9YsYPtt/kCWtnyHrGhzltSGPz4osnNNCOpZLNWGqZc7NP5XpUsglLKVmwFMyApaD2KxZoxKMNMF6pZNuVgtmhwtpZqUL8jVQq2bqlaTNuSYalsEDjlX0YJ6OP'
        b'fQS9iuXkQXyiAG32X0HyM2oZottbGkEREpn6lIEy1F0F0PgfA3B09V/1pAE8tMEaQaN00QAnpJFcxFtDloXWa/W5ZFu8IT+J+qjjzeQc2SGguGolvkLOdR6ckf6wKAJt'
        b'u1oi34jYlwIFUeH7UqBSvlaxrwZK12pRLWrgWY2br+SkLwSWBUmhOcqCWdxbnobogNIQ9kS4GAHXWrcA1z3ESLgOFXsyKhnl6dkO7fOtoK0r/Bqr8CcGNEoQJchG5sxh'
        b'5OgWtZGvooEJBNEnHyiYbuAJ8n2vFy5r6kSzjX65bUh7+yaFaPTfT3F4fT2SObaH661E462jPZWjW7+Ngs+pSv6UXP9O4Dz9OXh7T64bFrjVZzjsFNo3+FybfWJ38Jq9'
        b'8J5GkZjUXY3buqzRN+nUXcLrFNJG9emXX+2Tu6qaEo3tfoynq8nonN5356kBHWqDGshwGZV63g9qe+YqQ2V0/QmYa+Xjmeuex/dRZrDtjwf4vG4MqM2dyhHpBNCywz9z'
        b'/VoiOEbDNXOdYtf0SrFEsE9yKqUNNMirjqmpRyDX9i27R4n+AnANDRpQ3haHYWS7lo4MfFyss0jH46WDBSw8jPcIHuMWIB4dQvIClb7tPoVePUMT5nNCZwhYW309qN3e'
        b'EwUhfiDYo104bQlmUdwv+J0j0MjO2fRESyeMmg0zvNM1FgXLWLTRG7ffb07bYdBIePGY35z26QxY58JZOzcqiZ43oCy00btuBEMHUdjn2UlPO1A6ulBLj3lQ2eZ5fil1'
        b'866W2C5vj6ej2yBd03Xh4ZztMTIcklOC7HStAgCrEjtrv7POabYBcaK7U44pcEFpfl1N/ZQux8WjZO+cfNzIsKcM+rD2ElObcw5DmTZsaRMumKyRxclzYJ/hEzgetwuV'
        b'Dk+uF+RxB96skr4CqBGobwr1PXHREGRkF947zo9V9y+XmDXZQa6TLQlJHMoil9T50aUduHW0/N+xmQvg1jC/7Fc4pCwTqO8J9Tyhn/sTgykvhivgwZT3Hgoto1/zVQJX'
        b'lrivkp207eGOdPepVErhsIC/q8VeYrT89V+12Jte09BXzDdFLfZl+X4sHwz5/iw/gOVDID+Q5QexvBbyOpYfzPKhkB/C8kNZPgzyw1h+OMuHQ2s00DoaHktTFmFRVyJL'
        b'xEa0nSuLgDuRcIcGzNKU9YA+cCxolqYskl1LQbN6iuPlMF80vEjbBxHD3OHuCNbPnu4ody93tLu3O6ayl5gspjQGlUXtUe+JFke1cOIECgXGQhDTxNEs1Fgv+vFAcQzc'
        b'S2dwaJgtWh4tpjK+PNGjpejn9ZXwcEUerlCv9PAzp3n4nOkefnoJ/C/18JnZHiErL88jzJxW5BFySuAquxiSzOwZHsFQCFdF+QaPUFwIScl0eqMsz76MkaGZOUX6UA+f'
        b'lWfPpdSMz4Eqs4s9fH6OhzcUeviifA9fDP9LptsN7IHMMnhgNrQhJ2CZe+OmM08I+esEUsAuhS9quqLbqOkSL+/kA6Udo3wr5FOzx8aRyxTbnWRLYRJpKaABSrMN43GL'
        b'N+wpiwqalMMOKeYn5BTMyoZVkEsPeNKPlU4hG8LxDdw03jp14TTBQRfQzeqHn5g+Nr3+x9jIWHO22VZpK08wL/jWT7/9i/E3do46sP66ElWPU4cs3qoX2JHPpXhjUMhk'
        b'cgWfS8j2xqjsQe4K+NJaF4t/0JOcHUmaC8nW3LzVBUk0tEArv6KCnJViXLbOnuT/dWQ1CiGtfejHkcktsunJCMNwmcZK0ZHWBvxOon6Lq6L8kSjwk8PKtu1xu5LSok6/'
        b'qwq8jT0xwveYD/ItSpLoQPgOQUq/bwR8E6DTFlRo/OaYggyMZ6zx+6Q3XWpSTJ+2eMaapiBApyBAJ40PnYIYOmnWBHWFThLHaI9O/Q0uirFD+uADed74g7PIvTGkKTEx'
        b'ica2ZcFh6RTPLlqOG7PxWQGR7fUhZKcBn2NBcvOz8Sn66iEgttLrgGiFiXPkk9q5pAVu7MibG0u2zNUAwioQvoNfCgnFZ1ez0+IH6lS0+xFXFlfbfj4/FLFo8gpyDTlC'
        b'Q9lRcXxuJCKXyL4Y9vjtARoUgVDKZynL8l8vq0Au+klnvQpfDQxZ7z0x/RzZWSpFh59fol65IpnFmsF7ivD6vJyCvATSoufQ1LwQA0/O1M930RWM72lt8dn0eDkiG8ju'
        b'tJQU3GjKQ0PwTQE/6Glm0eiH22LjDfR4cUvBbL9j6bF4Q1pSYixpSo6j0Xvr9BpyfUK4BHJHQVweac7JJ0fItmQVUvXmw8hJcojhIosYY60hzfF0oONJYyI8gO/yYyP7'
        b'u2gsi4xB+Gy8NAd+wLyQyK6xBbNiWZT2olipVXhTtoAG4k2h+GWlkdVuHIg3OpaRawrE4YN98V5EdqzCB1h8fnyhcDL78iL77CK5TF7Km1sPj5bGwtQ1JyQUzJaC7Etn'
        b'8tuCVJJTgpbsWMqziDgJsIaveKPRk6350IOeM3Pw8wI5XDLDRQNQLCF3lrcNWmLbJwBiaSRm37DNomB4vJWnUTEfhoyZiNezEMTkONmHt5Hds+hpdXIWrUI0gvN6NmUz'
        b'FAOBx19dvozcwFuWk2tOFQrth1tgBPFBLX7APhBZFkXOOuAWwE2YEwt1uXMTYfqBIjKIxbFtTVMhvJvcDgYSRY6zuMl475rh8XQwYICak8mOkthYoHdNyYbZ2fgEPuf3'
        b'CQK8Dp8LQilzXPSY1VCYiAshQM5uOMjLS3HLcrt2KbmFUO80K94r4EayE+qntDDMhteTZvpdlMQkGGAlisR78a4QAV8mx8g6hvaDYhQ0RpNuZ/lam7F/JnLRZYxvL+jp'
        b'WKpErlqYToS3zsanrD9dco93LAJCtUI1efasHIMwKsL5y7ds7/5LO3HSupGfbTj0W0NSoqZP0PG/Ne12DNa5alfif7+1e8WMgVOfu5Z9Z8+v/3L+4+9GReycl/OTeAUO'
        b'frDumGLkGwsHz5pzdWx4VHLpuaDoMVFn14hxRRPvvBO1axH3TqplYM5+7pMj83vvHLglt9/BUOtPD0795xsh/9SMyv/uayNn5L1/smRm/C9GeR7ODNtn+vaX157N//Fb'
        b'b047N+rbd3fn5eT0mXDVEHt1XUupaP7qtV+NGB71yuuZX6S+uu//Y+89wKI60/fhc2aGoQxNRMSGWFCGjtiwN5SOUuxKb4oCM4C9oChNkKqCXRABsYGCImryPNlNWZPd'
        b'bMpmTd/sJpueTY8pfm+ZGQYY1GR3f9d3/a8NEQbOOe95+/vU+967/Q/ZNm3/2P7jP1961+y5Zou/fzd+TaPb1+l3Pw3Pu9W6sXrv3jHfXrgreSFsxUuv7a6ZkJ7xz4Nd'
        b'rx+LfLFlxvvHhlXcc1207R9TXvnDoYHF7Z+f/NuKD2Y+8dHVJ177R+rvmw5umxEw4+OB6QmTG+3RbNH0mW//vuv8v15Mnrf2ZHjJvw6Mfc831N7T33vtl59/snlZusOl'
        b'6Jlvff/slkVNX91bZRs2+sQD6RTXohOFCcrRDCtgKdn2qhW9TkABOsghmGHBcA9mzhLIItIyPIVGKOCSBM/CITzIwQaaycFHwQbgNlT1hHr2C2cHZTiZdmVQvMnSwkyF'
        b'19TYnmUhF2wzsTBAGjHELYvOA6PtqqAwhuqDR+CIOBdzZ7N3WziRKdxN8AC7MZcyQ1VjG0eDLhkPnGzzgBILSO3g9EoFXJRgHRTAHla99eSZK1BslYPtGXgt2wLKsEUu'
        b'KAZLUiB3Jwc5asErsyhLBdmiL2nRK2bBRc4j0Qr7sYPySJh7apkkOI0E3Bm50jpj6OQgShAh2TI5RpyxaSiDzY6DS1hJ2lxEtgdSb5nvQJUIV5ZCPYNtgDy4vTOIUW5K'
        b'1k60Ej2hA1qzaKDPvFWZ6hzzzGzssIKiHXAdDliZWJjhZascsvKwfVMm6bYQmRxu7EzjFT+EzVjr6o4lwZBr5C0K8hUitlhMZmBJO/DIYCz2hwtEwNiBF0LEhQnRDI3C'
        b'eSl2UM6LYmjxDwFysHlQTPShcG0EHJJtgiPBvN1NwxwZMwZlOyoONhbScL9ijoTsOvvwMmdDvYP7/DQMoURmu6hd+XbBMguy8bWwxsbZ74RiTzK7Atb4GwnyGMloNzIu'
        b'DE/rCt7BKnJRs2sZCXA1RREmwer1cxn5EuVNhToNu1gYPYHJG8jRKBdGktm3e7QM20gVTjE4C5f4JD0askHQyJnIFsAtazYiU3eR5hZ7kp6Cs7A/mPRUgGQwGdrbrEfg'
        b'fMYkBhju7hEaHMY4WUVhKFkX+aNkmXgId3N8kM5xmyidqOb0gNsJomAZIQ2BZtjHbziGjbaUMMSdSA9BUmFigoIcAniOlFDOGUea8NRwckOg22goC8BSogpOlcRB7VSG'
        b'gzIe2kiN6FVyCQrC1JH8RQFkSro4G2EuXoKDHE+kfQ1pe3FYqBsUemr2cSPSKx1wPsXICOoD2dpYDo1LWG10yCs2cHGkjZT0RCXWZ1Egf/vRtnRlWAjp+kI4FMJBT31j'
        b'MR50JQdKyRgzOAkF3lkebM3AKXv2bJ8nSSsLgpXkgT1LggVj0qRzLhyh5SaexAY+4GRN1kNhGGeGkxP1VYp3RkG9YXH5P4XXzjR8Jmyr+grbc81EE0q3KpGJ9hSglPy0'
        b'E+0l5hSthNGymovWEmty3UwcSv4mEUwemEhtWI6eucRMSgRmiVwvspT6zeR6vzFr76BegjQ387IKNplpsp20occyagRT0dFWTaWamyI+NksXRSxXx6ckbkh8fAyUJhNV'
        b'kqgpSsXIL9mjrPhU+iuzZSeL+j11sx/l4OkewPCG2/Rr+GGMozWt6RcvVWfA7vmyX2W5ZjGr6x9mZf5F5yp2ZqQl2iwJXjtHDSBJDxz6xw+Z5Y7ye4poTYhT9EMocUSZ'
        b'tiJuhoKiUtXddfutXJzMcdzf+2W69ztEsmgoGgv1m7lpNQQAxtHx2VnpSUn9vtVY91ZGhkrudie3O9J4/e64LFoTFt/82xhqHR82/ma6CriwOIXUJE1gwgYaDkJ6PXEj'
        b'TThJ+M1dYB6tt4b7rYaFrhosaorGSCRT0DZdgOGvfTub+QceNuDWuleO7x+QuOeL9d7LttSenKvcvcc1fYGmwOwQiaYv6DR9kWn6wk6xP01fa3buDePWP9erF3tvkvgr'
        b'mF7zlLJ3KeuEQQTaHqxBPSMv1I7qlPTstARG+pqoYijhjrHJsTRew2BZOuql+WmJsTSOyXEBy2ehw6qBtmVhgBrAb00EUKphaFwNFnhMTKQqOzEmhlPS9l6lFLhe48Jn'
        b'yH8GS+JxYVv0w616wJrHxCyMTVPTd9DYUvIHHg5luFrpdLXE0xyNBEdqp4/NSo1LpY5QD8eoDPpwzhSPqR6bWV1d1qdvzEqPp5S6LgYLyyAl0S1vU6y6B/yxNi2Iohn3'
        b'BQJk+V1Cr//EPrNIGpoavelNqZqKpwm7jT6Ofy3mmTiTpHeIjGtSKLb7LFaKTMoatRVbNdJKT0mlhsjdd6DRmBvhxN6+IVlSciIDQPuKOYd29foas3Vsj1NMHZ8Wzbqi'
        b'29lBC9BjpeV+jm462q2kTbYyjae71+G8W/jMXO94ZmRSS5xiNWbWIXhYK6phuat+y4hc30ZEvcIwqklBO1YGMXUML2OHhRdWT+ofmXOioLUWJ0kfk8m2X1uxzhumP1id'
        b'pudkaqqSWGUP/ZjTvMYcSPaPJUN2VxBGXz9qLT1X8hEZNGpH2QqtuKfXqO0coJEwPVfwIXtI/rgsSf2wwRv3GINHCuAinUwPJd+gZVYLhrVdN7TbydCO7Hdo37PuPbRQ'
        b'7YzFmsE1g72PPbiuoXRwrwyzmLE0Uylh5jVswRq8HkSUucF05GVWIpxzmsVMmbOxwTPI1QSq6VMyH5EoKrfMUuvLZotsuzc+On19sn98cGxw7Lp3GxNTklOSg+MDY0Nj'
        b'xS/t19uvs49Y/oGXkarKJ6NBFC4fNXnFdp3WXdgt4ht2s5rq+peJ7XaGhmSoucJSstXO8LDwgZAY7n69U3A36feB/fb75z3Ynvt51X+QhlzrIH+89TH3L64yNVUvjUNr'
        b'6Pq4G5eSZJ70Tpoo2JqmWUreef4dsjao/TAVSmCvRmcLgYrHU/hMhD6D1SuYgQ2NwdXi2sd1wKIaune2fvi2aalj+x2Ntywf5pzoGzfx74gJ/e5UfY8VWWhk6upbCqma'
        b'/tmpNjco1jxp9bF3gqWCbLzo/ImeH7zPkcH8yv1vOh59lCwertH/CUHLG99vB75u/jAFzkCs5X+lB/uKd2QuR8IfRbbXL35irmvsP2NCBj8Tt/qJq2Wna7j3bqydzCrh'
        b'sFLKzF/xcA2KsNiNGkgmQg3ltb9GDubrWdQdNBmvwx2DBooxSf3N9eA13ExzBq9OhJvbXRmCqrtcMMGbEih3X9PP6I176CLw7qsis4Ci/kePlufS7+i99tDR05RNO7eP'
        b'h264tseTBOaho05wc+an07rBJfkDmMeuhzM83yh/CPPeDc0flj88abjOg6d4pAevzyZmQf7Z9hl4t1DmHzGfIzD/kifshzaNf+kYtHP/0mg2MFAHlQoVXsPrqXjNijok'
        b'mKvEGuol2CnDG5xZ/vpOF+Yn8SfjFwYtbkud9R0l2yb0cpXg/s0KuDYXCpVy5pNwSAhSY7uwYws5FMsEOBAHXeyEJJPn1iJsy5ZjGbRTvH8ByseJ7IQcjZUTFNhuNANO'
        b'kgvXBDiN5xcx0OjxmKdWZ4lQQGYWFgikaVctsulECcRGlUItCxpHcY0FOOKUyEpS4GE4ot4kgeJ0GhAiQFEInmT+k88suJdx8aZ0tzOq1QIrfpYI56njSBYyk9xeJ8Ah'
        b'58HswgJsdaOtiFynaQVeT2BepNj1cJb1To9OwU4o8QzHy1kqvBrh70pN19yNVAZHTHdIoZFVzmf1NB8s8/GSrZILImk/7oZcN0ZvkeK3mXsv4TI2a3k8NeApSxYvw2qf'
        b'wAhjIQqPyPEaNIayHsDKmdjhgxepo8lb8MbqJazmkLsErmAl7I4js9hT8CQCy9G07x88eGAUxh1IpzxT096dIQrZc+lqGbQjSPciLPBnxNzkt5NWgVHOWEgqEeGsxIPL'
        b'/AOoIHQghElA4bRp8o0Wa7DJKZvauiI1wNL6t9HpQ6UmTyjBgjCNj63bLRvJps55uGmOrSugMDtWYCwjbe4W5KFyC9jtZWKEu6PwhBxLIy0W2gw1mREON6GD9NktPIGX'
        b'/JI3myYNzjTDLvkmEygyDTMnXbcX673w1jblSCyY7oG1cjg8XwltsyZijT0cCcLG7Ejylu1kNKg5ONdC8DaRwuUoaF2J1XIoxHyodoE8vIUHoTRyWCrUzNgJjbh7GNxa'
        b'N3oYdMAB2AftSdswT+rtTOpQMhKvLBgYQh67zXYMNs1ckoeKEyWCScZE9Y4FI2IFtqSCsQv3GOJ81XMjailfh8ARCpXdoYiHRiNWpET0F8oEwasseJfL3wb5CtkUnW3z'
        b'Wig0Cif9kYs1poKjOWnR0rXroQJasBNPi96wB89O9yGDUhlDtvUWrI0aj3UrSa13D4qEPYlQkIyn8LpxCnRZb4EaPMqYaVdJ8LS2mmnB+hX1dw80shlEI0egSUn+JwsL'
        b'z5tixyq8FqkUs6nCp4Z6ep5gMRyEfDjgiaUBbmSbIMM82ETmBYcWMydwFlyxCHoMAlvSkpPBHpzBtkhpnpo6P9uHTpEObI/SeWKh0rinM7aPIxbrNpPq0e1nLuRBPZXr'
        b'RSy2FiRQKs5fAQXZgeTSVOyc5eqDh/1J5x0I4SvBMzDAPZyHPfTytmumcgbdBBaHuy+VCFA8xArPwkk8k01xLbDeBisUmdiag+2sNWRNLHUm9S11c/YPgSvhtMBlGXyL'
        b'LfakpBtQ4WcGJ0KhdKcZNOM+UqPbZEHZQB2bAH8ZL2FK45+mJ7utcI0nZygn1u3C23AsSOMvwSOLyEl7WQIF0AB52UtYZ8HtnIgwZQiHc49aZiCmg2zL2Ay7ychW4IHV'
        b'UOHqCOfhOtT7j4I7/qN84JJMwFbMtYGawXA125GUOgXbp5M98yRZGm1WpibYaoVtWZnZRF5WS8OwJJxFO+DZrVAQQfctaQLZ1EVsIRoS1IWyYI10V88gpTupQywZ71BS'
        b'MeeeEoVUWONoAnuCoI61E07AlagIKInEkqgQESuwVDByEaGWrMdrbF9dD0dWK3IsxQw4SN50iG4rDREchur2KLIXt1H/e5vxQOwSJHhBdIeOOcoBbLMMlK3G4mCRzNsz'
        b'gjhVwFJ7bGcPjolYHNQd6GCNnYqVEryIZZZsLo0ZYKfxqsLuCOpYFeHoNmt2KYLoz2eYexKbVwqStaInNsB5HgFSTDTJRu7mN1JAhyBzEOHMEns+mDdwP5Rp4yegWSY4'
        b'kb3RWjpoNpzKpv4f5eilZN4rGUK+W4AvkdRKmO8wxEgYB7uNkqBzFCtoEO6D67o9XST7FpkWRyQ04KOVNU1pDydddW4vqN5mniy1gnN4kh8fZ1bAVY7wv42T2YRs4RSl'
        b'h0kFyZpzD8WDwXgOykVBvkYyCKuwmIdnHMNL1lhMvaGYj62CbLIITartPJhHiifpopfKZ7NG19GJy3mlbw8hvzFeabzuSaml4bw93mETbTtZCm3amlJMf7K4jVyhUxgF'
        b'lUamuzaxk9N7SQqZ5tfIfsD0cyj07O6k7h4KhVxjInZcNGbV8d0VQj3SSnf5kiGCqa8EzuLpqamVqS9I1GeJtLQ99UW/iGdLX5pj/enGz0uPJ7T61uxI9h1d+pXRsbI5'
        b'cQOe/rPjXysmqVTzEpXg1Tx8tN+xqRmXPbdLjZ+acsr3C3G7MNJrfPP0IYtf/vDisktvfXxx40tTB12TmTYvOes4Peol3+XOEzo2T217oiFz3cEFTm8HZQQ+W17Z6fjE'
        b'z43jzkTefTByReOfnmuJC835dNIZ4eri1heGD9pc45KUknvyyqyP5SkXop4dJcY6+SzZntTl94L8ZFnl/eoWacHQFfes655f2ZHyl1FPleRNnj7t5fnnKt5JyvlX8fnp'
        b'KW83NbRULWyApvgLS96YUHfeZ9gLdk5XQ34OimqqdvNoXFT4YuvUaQmfHYp1So/80MPmyz9d+Htg6El1wzmfH46sXvPkJ+eqqjy+Hhywcf6drBcvvLfw5U8XVt390/qL'
        b'6akef1x/eG6S+s1J6y3en1oSFHYenzkVbR9iPjQzCwe9eOeNKS+U/MV36YEYyetBiTnbsWZEZaHv/fn/aqncsvV333v87qjPwZc+Cxz04f39r56PrHbY6jppx08Xg45v'
        b'DXpbuemNbaO+LHdPuuWW8NYY5defVz/zStDpv/5u/Uf1O75enilsC/rdN8rpn9Z15Dx3c2JjfsapVxaeKQ8ve3XuZ1v913x23WXWklXxy/6S8YzLmKkrm/2OWJnHx9lH'
        b'py74abLd6Scle3ecuxx6vW5TcHTdSyfbvIcfHfjZ5VcX3FR99/Ir6VNzI35ucH7X8ubZg7M+6PDZlDho8uffpb1UPaLUeKvH3u2b6rzfffBm4J/LRnz3Tld59Rr5+13f'
        b'TfjdT+MdnysbnmL1FDy749s3wqzsyxOuFG/49ok3/5H5zHsFT3v7Nh7/4JnP/1Yx6eKsL9x+sH3va5m0yKv+te3xT2eMdHDbllhc99LKuCem2MRebW2Y7e/tUx+bmFo/'
        b'C+0shjkZLawtfnLfn8a3/PHFv6x5+lWfAV0/K77KtXlhfIByPPPcL4WLZj3iDLBrHIszCJ7L2bFuJUEFtUVi+zjG+bQMb/IwioNj4CDfp66lsH1qHpxgNkByEFyDOkY+'
        b'XgRFvdjH/QazuJLkcGzWhnIZ4R1yYpnANUnOFjzAXfkFsAc69DbQLXCCbaBwfTnTPY3xOlmjfAu1ctHsoNjsxtq0Cs/F6UXM4JGtPGRmEeYyHhMohguzuXbpj3mcuWMU'
        b'djAiquCFK1xdPJRY5CbgiVjBdAVZ3INjuV56ahuccqVkcYVuZE++TfYvKJW4u7ixFq3FS3OD4rFZz99PaVZWQi7zvvsut6AhDlS4CeuWceXRRIofGSTDEwvwEq/bLRc8'
        b'48oqsI60RQ4tEp91sIfHmxyBo1BAI2Xc4RJ2aSJlrEKzqE0gG6vglhpKTDItsFVNw9g0wSuYn6Efv4LX5HA7EdrZUGE5Xg7qYauUZ5LT0SZACqfg6hxOVXIcroeQGUBv'
        b'oUEzS6BRsUSCpV5QlUWV5pET4CrcGkMOSSKKXMED7kxCpVJQQEimZuiD4LwxXB4Et1jkypZsOB/EX0cjS+gU6iJH6wDMlxI96Vwcn0U3sUJOuqwKj3qSMtwZZ6CxYBUm'
        b'TSHbbRer2vp4rHUNc8MixlpGRLbbWQq8LcGO4Wa86s3Gok68uQ3ntPJNOdSyORwUCVXsqMrEfA3x2qX5LPwmDRvk+kFZcMVNE5lsA7vZYKyGy1t4SEswnonnES1EIu5g'
        b'fQJFHjS2Rmf9iJpvIECDR2dUKLOobu2I9aFkXnbQDukTGSTbhIeGMTa3nXgxSC9GRRehMoKoqixIJQ2us+m4ZhoccF20ykMZ6KojntstTU/FAtYzsA9vDCaSOiV7o0f1'
        b'OihRbJTg0Y3QxVnp6uEqEVfYuToNjvNzFZp92ULAqgBysnIxhDTmKpdDsEHN3uw7zVZfCoEqPEPFELwTlUVDoKVwAq/qCSJkIdf0kkRi4RqbJ3gtWELq6E6Ujst6kUF2'
        b'uF9mQ7qngVlVyYE91XAgTDie68/QRLYZqgGPVmUFBQeIiXhWkISLLtnYzht/IzFMy2YHe4YzQrstWDJVafFvo6wqh/8XEVx//bduU79VL8BKZlCjGBx9DGqTqP3XhLG2'
        b'WDO+IPkDCf0nkf/C/knNJTS7hiK9cXw2O3IvvVMiSh7IpBT/jWKJy0Q55X1h4MCW/B8pl36yIZ9oVI8Ni9qRkJKs2ScbWo7UhpRnruHbIz/pXYJEICVLzDURRJYsOkgm'
        b'pbFDZhITCUWkpV/dCLYS0Zb9rr1C3vKZ3I5y0ZhryuWJejrDXq/O4YZIHjLEA3tY4pUb/ebFooUSN3dHGnRnMnW7QQb9n42x0kSvhrO0NVTl6Srlpos/YtbPveRX936t'
        b'n6/M68Ep+LBOUooskSu0f9clS3ShzkuRgfQ+nvNSSyj4V4mByIG5SVmUNzA2LY3BkOoR85LKpdJaxab1QCflCFYJCdy/Heu4MXFTn0J5FIpzTMziDVkBG5NiYhzj0tLj'
        b'1ys9NEiy2liEbHViUnYaDQjYkp7tuCmWkxkmpFL+wb6kwfqVSN3IbkxiifWa/MlENU+q5LCBjhQAyTE1Qf34VIEUD2CaYwCLKCDzUJ1K0VrJe2h0QaxjfLY6K30DL1bX'
        b'tICEmBglxY/pN4yC9I+2P+jH1I00roByUs8j3biJdmZWSmyWrrbdkRoGS9S0jUHIskAjCvrCCqCAsj26SJuemqxKz85guHL9RC6oslLjs9NiVTziQ0Mjz2EO1I7ONEnc'
        b'jXQBeS1DIdmSQX5NzIr3ULJB6Cfig3ZoVqJ2XDTjzuLANvbmhNSMfkI6S47NoODDhsrsMQCP4FQUBUOcimahTN0etRqK1/C8EE1OyNA53GI/lglAcCewR/6AK5zTphDQ'
        b'/IGT0JYdQk/RZtgNHRqrpqOJlFpOOzO9sGqog/9Ap8wdeCkc9sGF+VC1al5AFpzH03AZa6aZzAx1G0EU99N4bAHcHLkVmq29FNuYzen95f6qbKmjKMTErPtlkYLXxwku'
        b'TiTiTWE8kWwiKCPuQZqKQpN7jIXR62R4Hg9vYk+vz5KltdIsnTkxaQcWTxRSL7wkStQ06W75E6udnrtlsdfL1u/dH0+U/DDEcX5C7sQ0cZDF84P2pZbNr5l4ektabPrQ'
        b'sZ11YU9PHK3Yt/JrRafVq2VbX2r88Mb0++d/kub/9NQXnz3/j2bH/asHH/Oqf9Fjdt4rH710fcrSw+bf3QjJ+/CN2q1PlX6jKLoxRn71DyP3zxh2fOo1pYLpJesmw5ke'
        b'2pJiVSILyi7Cq1xdqoZyLFoEeZpoenGuYiXzh21bia2bHQ0LKv1IKWvwAhOD1obAfjU177o7a81bAwbABSyTwmW4BJVMb/CYGKzTp6i9xo+qU3MXcuLE87Af69Ixj4Wq'
        b'a+PU4RQeYnUe7AaVcCVZF6wuLlwdy8Tjxbg7fB4WueqRSvrP4al3h4fGawgOtcodlsEdquDFQQFXLaqSB/cNczd2ZuJsYiZTirBiwCRD0qzgkqKgwmwyHta4+x6VyHfP'
        b'lGbFsQXKJBcXQ5LLLmEuk1comv0D8l1K5RIqj/SKKdAV1ZPx0LPnEd6HplHC7+g+SmkycAs9Sh0NHaW7hVdt+o9r0NWBxm6SkyWaHC098AG0KaPdQUA8YVSqSxiVPjRh'
        b'VMpCE2Xvfi8zcI5GJG7UgIf2RCzPVvNzNZHtbGQb9psXMD9CD4W8v8MoMS41Xh0dn5ZKSuHctVq4pSQKnxif4sHu8PCj3+ez2/oDN9crVdMv01i0oJsuXJCC7aoTWTXT'
        b'VQn0D2SbN7gNa8Da+62Dx8Ko4BgGuJadkZYem6BtvbZDDIfiqfQi+ugJoQmfVWenZnHIdF2lDB8Oj6zV/PmRMW6/9dGo3/xowOLf+ujc5St/81sXLPjtj877rY8u95vw'
        b'2x/1iXHsR4R6jIcnxhiOrAxI4gwuXKBJTHBzdNFMf5ceMaMGwlINSyD9hKo6LlTFMtzqR0WlGq7mMiqz8l0hx8fDq8dqYciHHC2WLyfywpzU2N/WU/MiowxUoZvbmu4x'
        b'vB58uaUaiFjtk92s42PViVkDOXX17RVywTzBSyI4xqTVJ6dz5/8m7MJO9RA4oSDHBJ4SoMbXhXlI8DbcJkJXm5eXl5EgwZLYAAFP4C0s4m6c00RcKHCFetwf6kGEBDgk'
        b'BsF+qOFBDmfxwiBXKFsaGki0WtgjTsUbUMS8DjbQga2uE2eFBtCHCsQZcABKlDLmBonARjiMbdhmha1GgtTCYag40xUuc1faUY9h5NLlLOwgx3vSfKwWR8EBLGXBFtlw'
        b'I0jtsHUCOenEdAE6xuAJ7o25aAdH1dhuRY4yib8NNoguUAdXsgeQawtW4HGsJIeR8S5PwdMRDvMAxk4sHKzOJtWgDHws5mEZnlRKWI+sJiJjc3f94AZ0kBriPn921QjP'
        b'OHbXkMhEhayOxUNZuz2C8YK2JhthD63KDid2BVowL1gdj2d01Yfr85RS1up06ITW7jcOh9P0hZc38iG4bu7d/UJsJbUjL5y8gOfE5i7FDkWOKZkE0tjFpqJnQjL7+yIi'
        b'6F5WWFAEFemCGW7i7JThmiGzNaUuQoWlKEg9octcnI1HpmZTwHs8gw24J4hKuBEMT4Fm/xKRl1yAiu1Eoj6AedAFVXAskvxSReZTPVaQ11RBl40RVscZWcBJck91XAjs'
        b'wwMzHAcS0dDGChqjjVJrDqdK1RSK9ciwC1F/mhn6lJe10Ts1mZOPfpIumBaWFkVkFE8cXlQUUzV67Y3Lzs7DzawrPnR2Vh4rne/osm6d5RPKxs0B7a9VH/3XlD/G/7V8'
        b'1boVAT8EeDTWOQe2f3E4N7JlRpDt56Ovnfn90M8nYm3qxa863Gqe2fCq+uncn0OLJ+IsqzdMgkef2xJ2vLCqyPHJr8MrfzzRcH/6d/uaF3zje/dP+57/2bUi8e8n1g/d'
        b'UPjZ9LTMGNfXjNN8a26OzC556U7j0l+Mb30zKyy1LezNA00l1YO/3PXFp08+5V61w+hC6ef7184NK03PXzs/bPytmS+t2/zVnyxePqLe+nfjnxJDEr+y2l+y5pZRhdKW'
        b'2elM/QU9F4FiwE7mYs3dwa31bdiSo0tdDSFDQF0ECjjFReI6/0GuQUR2LeUCtfkMPOYmNR4B1VyMvzEJ8oNSYLdWioei+ZoUQjjhyxLpjQQZXBoJeSLuJSN4lJU6dTRc'
        b'1Ms7hSsjfEW4AsfwADe6HidroMp1OLZ3S+pUTFdiC2vPgOAUsmahhfoPqBRsgsUSyI0fxAT8GCharvaEdgVeEwURiwVsJF972DXHMcFQTL6qMyZRvIN8svqwELifJhvL'
        b'3aB4R2TGJBozRGZe+XYsZFcipmATFGNuWMYkWmIhDXeazN0vNdiwRS+hUyZYzhnF8jlrlzAvCV4h6l+H2j8kh8x5ERrIHoOHhnCS+Iap29VwyJlsTgW0MmUCXoUaCXss'
        b'CHdPVMOBgBxLI/LUOQGPQb3Gt4H71uItNbRBHbabE50XLlLHwyUZd3ycxksOaqLEtOZk0vcdEcio5UMrGyvz9a5q6HTKySRvg0MCFkF1Nk/TPBNINg6d4nSeaGZceWKa'
        b'E17f1U+648PC09VEMGYKRpxhBSOVKhTUBElTFCUP5ETRkDFDKTdySpi6of0yZ4mJZhKt0VH3jzxB7n0gebB1QM9gZ/L2UC32CMtXNNcXrFX5PTQUFtdIWlOk00rydQmG'
        b'heTTcw9RTa7rh7obqAVRy6gywhKrQpWDe2E53ZNFhwWE3lNEz48KD/cLnR/gF8GxMHUYT/cUGbGpG7WZhzQF8p6ZXmoes1jqki/1MiZ398SCYtBQ1GLJdC3WKt49Q///'
        b'ZFxXLSL1OkfTOakBw8TYWioR2Jeo+dn96We53NLIdg41qMskvxGmUmZpZS6xpFRqMuHB5F0mou0IE5GhRCSbWPcC/BEFLPYeukiWimcc+oQIm2t+ql3EnsxqFNGKo1kd'
        b'k2nwrPhnimplSr7oZ3MNthX/e/dna4pwlTCQfbZNGKT7bJcwmHy2Z5+HJAxNGJYw/JiCcrbly5PEhBEJDnkmFOOyyrhKTFBUmVeZVNnQr4SRJcYJ3vkUL0tOlN+xCU4M'
        b'BcqYcZ2NzxMoLhXlcqPPVSmqJEkS8tRA8s+6yiaV/2ZDSrOpMq0yS5JR5CpS3gSKxUVLzDfNt8i3ybdNMklwT/BgJZuyEF05C9kdkCRnSFUmFFNTJqxUMOO0zz0bumDm'
        b'M34HBn+WlKi6P6GH+Nn3Bg1Vmf5N9z2ILDstVZ0+TZ2VwH5O8PKaMGEaFYmnbVYnTKOLyMPLy5v8I8K2j1J6TxYaFh5yT+YfsMj/niwqfNHiJvGeZIEf+W5KXxkdFhq8'
        b'okmmopaDe0ZMBb1nyoFwU8lHoySiSKt/zWu96Wtlqgq68irptyq6lmUBoREcFfFXluVLNraeZalOsAIjFiyde39eSlZWxjRPz02bNnmoUze7U+VARfNR3eM1mX0e8ekb'
        b'PBMSPXvV0IOoEF4TPMj7lJLu8pskDJVLtYYCDZIOCg6bPzc4mugM98fRSs+fF8BqSH4ujt1Ct75wajdWZ5FCPbwmku9kF6SFNYmqEI5VeITW1TwiIHRRsF/0vLmR8/0f'
        b'syhvsk9X9Gjy/Sm9HpyvSler5zFlpmcZwenJIepkVpI3LUnSXRKpYAMty6pXf9wf2n+j7g8y2HlKRY9S6HRTNRko21d1nv61VyG+rBAfVTO91v/Lve+7/oqW3jNOSEyK'
        b'zU7LYt3PxvI/mjeR97iZJ1z/uUWE+gIFk4jwUNhAAc+vg7bUBtMdIstJcV+eQXNSaJ6jzPlTU1H5S+lDclLumVCO1CwypftPvaJfizmAac+txEP7bP9JDq2kHQvJJ/Vo'
        b'wwLAbqGrR6LDw97SZMwP7GQDp3aq7uimk/JDWovI0D6pEWbaTqUCAkuN6IYvY9BlSWa6tAezh6Y9aM2ae4wNmDUDeIJv6tZEPeMmp+Hh3ia6DT/EmBmhpc91zGCkCEx6'
        b'UU/re6O7Y6+l4ui8wE/58NvoUnvkHb6Ozi7qVOq6ypniMdnlMYrkq9fReb7/o2/WrFJ6s5vjo97T/w7i6BwQ+aue8H7IE4+7GdAiele6P7uxxvbFjUQ8c1tDwKQF9+/v'
        b'SXpi8sd6T5sMVWq6KjVrC0fPdXah5zCltqInsYthU6ILPZ/pPfS0dKF2Yxd6zLkoPbq9q5M9Jnh4TdPcYriYbkesF7tVU2r3nyezP/Oi+2sYR4fQNM0A9gPvn/FqBv/Q'
        b'b/cwj8W0nsn7bJEZRnLQJN/3W6duuIZpOnLXvogMFB1B54s34Gqn/5FrjIePmvKZCZXFASTGZtEJpdaylOkBXFBPdD8IANQMS8qhqfY8bECPHIL1jmNEYiJta3aaHvGZ'
        b'waLmz430WxQWviKasvCERfhFUwKWCFZLncue07H120l8E+L9wwiTNHgp2nHTam0aA7JhD3e3UZk5KngJ3TZfl157iku/MQJshDL4OlVzMrdeW4wLb532ln6wETTQF0Qm'
        b'1XLVpsRudPSLCu/HOL7RMWJTatbWRFUaG7ish1Seb4j9rCWyYAKyYtO2sAf73+Fc+p+zGswOPiDdUB505muGRAfrwf1U/bQoi4c86MFr93g23QDsxOM6Dkj3aAQntXb6'
        b'9irX8Jho+A2738t4JeMS09I3JtOSHmFgp7KIaR/pySqUm8xvYMlyrAzCUiyTChKsE+F8sjPs8eeyVSvWruwOcoD9DhLLjdwSwizxk/CIUm3hDtc53qeAF2YNZjlFGbAH'
        b'TlOdFw5gB/lqg0KZYIF5EsinCXNH12VTHk2oyIEzQfqpZUv75OwweMzOLd0ImSFGgRJhEuy1xDyo8NJk8adDwXKdLdhcNF47mzToNLOoe+NxzNWYj91EuAz5s/EgXMoO'
        b'p+27A+Vp3eipelluuoybDAuLcAqA6uweGuXsjEV4wBO7aLCBGwXA5NCe7tTEd3igCLkrF3LTfw00Jqtz4DZpaysD7hTw4Go8z3waySbGgu0ocptjjFt04hoheyZ/4jy2'
        b'd4N5Bi3z9wgMoRHPhZ7hWBCMJXhmib80HAppbh7egLNbnAS4I1PgEb+k1A3hhaL6JClm5ReXnUpmmsEc632bkip/DghXtK99dunlIW421n+tD55zANq+Mnl2kGpe8rUh'
        b'399+epuPvX1ezWDJGHjyzO5FN7aGv/3l64onN218LuHwvOWfPDdQWR2eNfnNs8Ob1B9OnJr5V4jenJy01fpMis+bE00Ldk2p/cVjwLuf7JrinP5FUNW6s1/fcHhig9PC'
        b'jwZ//tXTI99a+ePRzoa3s84+q4grHTfrjrLAa8CJUUoLZqtcApejXT3ceXRDPemlQokXHDZnIQ7p/us4uDBFQ16z1I1GahgLluFSb7yN5ziEXud4KNBEXcA50NlzoQOv'
        b'sjKGk/Gp7xkvMmcLHKMBI3vwMLc0n4bC4KAwuGausTTjoW2s8BlkdE+zOakkE6o7oByrsYRjL+7xg9zeQRgFC2kMhitcZVHMU6EFDmvtuAl+3JLL7LgXsJzFE5uSdbG/'
        b'D8bfpM0c5U+GbUPxKA+lPodVA2jSix4IY7K/o2xtaAAz0abgLZUeUKQ4H8vg6BRoYBeTZxuTd9D1d5Xa4kU4nriQtOM86wGs2qUiy37DpGDSAXGiN3TByR7YFGb/lu1N'
        b'Bzq3sD8Vapcgt+H2twcyKQ9tpYQCMtHkgVxCf0posAijH7aUSMSh/ShDGug1DXBMomjIkryuB8Lb0ofqXy0Oj9S/fgPam1E0A7brD4rqkJGgwXoz9EId0bHHY0jAvXHa'
        b'qHEqwn9u+D0ZpTG9J6OMpkpjQ+GzPDiVxqreM9YQYatuiAYy6q20p0mwoMuo54qjuUZ1tGCZ85b5VklWj5k3r0WmajSkQM5NSFD3pG3WHqAG7Hk60auvHprkOI0KhtNi'
        b'dPAlMQac+G4aQUYHckVDI/tGkvamIOQMvFQ37xZPs2gvZmmE98dSizQCrY6k9lGaEeeo4s8aYJKNVTsmpaXHUnOBI6NM1XBC9hdBE7uxB/9abwLa/mrRQ10wxA+blbiZ'
        b'y8JZOkrVDTyss584TXJPagIV5Lq7opvFjrfB0ZlRrdOmMUFtdPhCDw+P0cp+REweB8FijmPpbNIjVtaVzJkjuejbfd1gebpnuokgNVNAE6PVkxbSYBnO4X4L/ainxi86'
        b'NCpknl+4m6NWI+Hcmf3GdbEg4/45VNMzeND1Q0rYbEjJ64es9CHF0f90OiDt4YepaJpAYx2knMHStMzYhrQ5R9IrfuGhc4P7am6G45IfU5vTElnxrtBxCtMJq5k3dF0Q'
        b'BTiR0UbHxISmb6Q7xUMCtjdndb+dMc7SPopNo0HSdIPQTd0kVfoG0lUJsf1EVqdlc6NZcmpO4kbtzCdLM4HG8zjHp29Up5LuoiWRjktlfyW93G/FeDH6pgalfjM1DMtx'
        b'6xLjs/h+YFi5iQibOtnL25FzvvL20Dq4aYA6Ne1luj9dm2RTNFhOUraKrTW22jl3a78aHj+RpjlGaDQqLeM6jT3fQt6SlkYWX6yK61X8ZsN7i1qdHp/KBkGn32Wo0ilx'
        b'Ou1F0rWawSYLgU97w52px0foGEo0vdiMjLTUeBZpSFVttp70Y+kNr535GuL2bv5Telg7OpPvSjdHemQ7OodFhSvpYNCj29F5nl9oP+vQRS85YLKyL8bgQ8K25uq2+l7c'
        b'QQ8LB+2hZpoYVDNHhnKFqBRvOuopku1REkvMRQ5yw7QipyAK8/KaqYljjPna7ZmcWQE7tkEz0aNOW+gUTLy+biG7ttgV2tSamCc4jeUCHAjDkyw+CffsYFFZV2QUHIZo'
        b'fnBIERLJFFM8bwtdRGmCBgPKKRb7pGQHUe3gsAOcxGINzQHlvohct1YDdhDk7rLU3y0wqreO2q2gcgSZS34DoNjJhFVIMmOeVjudFUL009nQjAeyKcUqnIXmuT3f9Kj3'
        b'jMZji7spYpY469AvlHJhmpctXo4wZ4pvAORCPld84QycJsrvbKjCy9lbyDWvzXgniJEnuAeGUdWXl2KEFbjPzGkINJl1K5pzyEAdw4bt5NoZG9gH9ZFwKmEJFM7bCbVE'
        b'zT9PvurIz/3rN0MZNMyLWwtF81SpS5asW6tyWg0161OsyfDPHA7H8Awc4eAB5aTFhxXYnmEuIWOcKcEu0XOFHUN5SSd6X42makSNauxbPSwcAoVzoDwO9pF6dVdqH57B'
        b'KvqZRnjFWGG+owAtSwbYmyTwuXRpNFTw8DKKkSU1FT2hZnZ2IpsUuBtP6ewAyqUaJKCM7OxILBsF1zIsrLAiUjPMelYCahygY6RhTNEA54SFkJ5vNGGvssQCO7wAV+AW'
        b'4wOxxd1TH4LR5BlOn4ocLO8xqHgN8i0WQeFEhn04ONQ+KFRDFbQObtPothJoWcymDik1iP6BzqdKI3UgFNmQ2V2EleFEpy4S8U4mKec2lLNJvtg3LWgtNmvL0hbk3w05'
        b'v7RHebBPAVW2TtgwiCjdZ+0GSQWoCRkAZ/HobAZJRGbwfh99iCW8jtWadlF8miryoqszyPjswTzSvSzaDiriBMwPNw+n9AfZlL7XAcuxWs8kExygDHT34NwfPbtKWy+L'
        b'HDwFZ3osHNJnx7NtoNxPzhfZObg9VYs0sUQJJ/1/Xfm9yg4PJHuIWzSbyuPwEmUn2ReW023ogbqZLEqHgWFAwU68wVlpsNIn1aEHKQ2cT6A8hqlJKSNl6rNE1Vrh8FPI'
        b'kukbX59j/eYI1Y36Bc+1p7n+y1i5+n1r37ku5w4K8e/sUTwj/3D071oLY2I+CVzkuG2w77wyl6gyab2tSoaJb11McbRIfit5v0/bhPLIl2vv7XNOSCz5adSCNweub8id'
        b'ZlT1stI19LMPF2Sv/GWR7JWv//7NqZsL/rwy86PK9ar2G3EvnT2/aa36/cYf/la4oeDY3udvffv3xiCnD9vmvpmWUx1jPnjtjZYtXzbs6GybMffB9tOv3j+/cOkXtjN3'
        b'zv9RvHCgZcOugFfD5N/ELDv8YsSTX0n+GL056cX4zX90et7ni51PnP/uxU3vpNQdVaR/cXz+T6uOLkoPD5vSeUuYNfzB/c4I+dtjMp59btAz69MlqoC775145uITUaPu'
        b'2+5Y97Xv0B+r0lY7bP0+412XV2fOm2259ciZN39fu6ErdHHHexPffmflgZeef2LXojekDwb+dPTKj6E/DGw7teH0rRHXut7+oHLu/F0DXko8XxV285PP5py60HRSsTa0'
        b'oSJo1KvJez9tsU8/nB//jyEuTT8UmDb98MXWd5/wd2r7JeWJj5/YMTznb+rVhbV/jMXEQZve8u54d+kf/vx6WPP1X4zt5l751mmv0o6ZZizh1rYgPdiBpXCNGoqgEko5'
        b'lcQNsns2asxQcNJSa4mS4KGtcYz9w4Mszb1BY+GINtxRmsyiHa2MVrEVMAvrNTGWDIOhcxuznm1b4621+IxfxxEY4BrU8tTtvdYDKOMIWYvlPVlHpBEs/Z6GSzrsmsJh'
        b'GiDXhNmmOExDNDbwJKOLeBvqNRYuODNIH0ZiVSDPRC9xgFpX/WjKDXhBkuPvwyroswJyNbGaW+COjMVqYt08HsG4L9LNlSzEAGiRCfI0NzgjGR0WxgxSCXBGEZRGzmRO'
        b'ESJ6jtKhUkyY1iMqchw0MHPaTszjlBkNeAyO9DKnQRM5Dwp1BrVJwMko1FgezPPkjVbyTHmaJR+GZax6cDtjDLnqRonWoDla5iZC55xINpyriJixh1viBs7WJ0TBeuxk'
        b'gZ2Dh8E5PbPmfnOJ18K5jONiFTkpO4KCA6BQk3TmAbe6QZO84Lrcc9oKVj3zGV5sxpBTJYxIEcI8ywXSmVgPBaxnZaF+3blksHesiC3YBK3s7TE5ZB4Ue4a4K8nrZ87C'
        b'ixLHrLlKk8fOV7b678Tg7dWiRB6iQqJhO+AiM9FcwpLVJeYiTXO3lsilJqKNNU0llz2QS2naOqWo4AnsNN2cRm/KNYnn1lJ7iT35Sf/ZscR2SlhhK5oYWdKkM4melZEm'
        b'qT+gFkaZxFLCE8/lkq2jDdjcemVVhz4q97zbeKbq6pmw9vhDoJ8y3mUgb9xAyngNtWVSi7JBW+Zu4UNnfWvmYzS0/0geigLHjHw8NkRIkutieqSPBJ1PUcrux/RRIMIT'
        b'NxLdVf0oSx4zG2hUFaqoxqodl4cEP0IfoRkTDn30EbdQ5nnCE3AB84P0GRjxtrQXsl3xMuc+KaJko7lgMYhs6w2Mv2zs8hTN2V4a0ptxDhqWMsFzlQzr1POhWU9CkGId'
        b'wwbDUzZQRsndsjzIHuuRQ74Fkq37Mo1CH7vWaIo5UWhoESum2BP5qwXO+XiRIhwEKMPLeIMJIF5Y642VQaaKbg+eMxavYzrVmHSJIJv6Dt0cgk3nuXCdCgog39OH7Hcm'
        b'Pl4CUapOCHBnqQlz52Ee5BG5n6aYeBlRCMoqLGEX1uCNZYqktaZErBGxiWhhUDWX5WbYwvUFrsrgeS7kFJBtETE30ImLRXATmiiotjLUSJDbSVbgNfOZUMbzabBcFYEl'
        b'ZIMtnCvANQEOekM9uzIOdttR7LkYn0CpBnrO2ZLnhhyy26Cw2DxJ48WbDZ1jmF7pvYC6/S5Dh7MmpYTmr9RCHs+lKRJptkkb3HHlyShDxZlwYQTvhUrsgGpFzurxlNeQ'
        b'vM0FCuEk105y7eEmVdegfY7Gnzgb9jmx8V6Ex6E5AkqwKsqZCLQlWB0VIgomYSJexX14jfX6wREHheFbyN7tFRPqYLmBq7dNE0YLC1a/R/4aE/d08mb+R4elAULZxAES'
        b'mqv9wgRroQ8FsW7t0bOdURDbkdUmnBK2iwlCgrhPMkQ4rSUjpozYH1KDP+WWmZugCk7dmNikoSOWpZFfevMpUyt+klyPkTh7EW39ZXIC11LXLZliF7K4E9JUK/1ihSsV'
        b'd8Twyb54Awuh0Bf35cxZmJQZoNq5EXJHCNsnWMOVIVjG2tcWYC7YLyYn3OIYt3fjLHmjY3baCW5po6WCY8z2Lbu2C6xfA/EQ3qFjhXVRfbAJl/I5tQTOMKVxHdygeiNT'
        b'GgfDXjY/Rm6NIVcCRmZaSAWprTjdGK+wlx1eYCyYB5+V0/yxpcMXCkoJn+gHoGWYwmIF3NROqDXT+IW92G6jyIEbcSwNieiI0m3sBYFQFo1tipyhFipjQTpOnLk4Syny'
        b'6VLphXvURJlpC6VSoEQhOhL95sC/NZYpZCxVd+hu/wT9BqLQhw2bjl57j9EbxPe1orGKHOPx2G4lofWfOgmPsSuJRBxtVpAFvBlayboiupsN7uHZXHnk9jYrd3NsNyar'
        b'rpJcHZzDV91FuIVXFPTTbbi2RFiSPoc1eSIeHqdwdiEC4BG8Ekzmf6Bk5Rq4kE2FSzwEN42xjexjHeSKEewVYV8kHtqMDamyJ/5mpF5I6vuC9J+JUUEHbaNsb3ec+Ln2'
        b's/25+x32D7H/fewTU8ZYDXj6L42NZqq60j1jRu8t+suS9RU3QiaN+v0bqrl1dqbjBsUf8H4q8tOCzHdhUFD86i+G/WSUZ7Qe4fNjzRvPxWbefOGH25f+eCP7M9+OuPHf'
        b'bm19vcux6pNngyZ8K6lZ+dxzCWPNXt//5tMjXjtUfn/qj+0qn9d+31z4zFKH2PVr8wpy66ozv/Zd7jF12Q/lg4OiPnr2mYPup57Z4mc/5JfhH6zYHvVC/ZevS4oqlH7/'
        b'+Gap259tlvoOHBL/1MJ/vLbKuvCmanzzkcCVzy6InHSiycGufNNps/pDS/Jq/xVicST9uQ9N4l6+MrTBZqKP6frK5i/UPhMOjpvQ0rhu9PRJUX+oL59U7j/TKKd4qPcr'
        b'h+xj8ndviMqOiL8bkrDpRZO4zuKvDy1+Y/+ZqMY7kvaQSa+mtft1Hv/5/dp926Obx3055FpTQaXtyoz7m1JeXx7/IP7dS83iz+nr1ON8nv3eeX36vI69V9dVHRn9lbvz'
        b'739Q/vm4X33m33yM38o7PeLtSTlx+0K+r2x87mJWx715RU99dGDD109GOH3rCFlfCB+csEyyCXpgkeU5esV9t/i2tMKs6M+Up9t3brjWFFp/46l/7mxfcD/ms7kv3Tt1'
        b'Q/7+qCQHeZt78u6ZFR+MjSrJ2rXDdenZexfvHQ66O6Nz91cvvHF3z7feLU9fsfTymdJYePZzIib8c25MfX3bjLSEuPyBl0tjZtY8WFTSNGLLxkj87FjS185ZU9f/9ML8'
        b'HyJLB3X5H/zm5+yPWs+lWrlc6vj7V9duiol/vrO7ZuSx5hFrzxa8mW7++rrxZ9aMyf6+sjbmps2MvSZRX/9S0HTqgwvVu+q2fnJk6xdpYc0BpZmVXT5LXy6o/Tjb6Yz8'
        b'hxnjQ3zg+IPhr3613HP3ineKbpt87JRwPejmUw7D35R8OWHmkw7jh23ZkLRz4pG1W99X37Xbuv1Pr5fOmvny66HXD7yVM+1cY0f+tC1/qTX+dvRf37mz+GbxWodFB0Z+'
        b'9nHksEHqr0v23HnS9/NXFv+0LG5AV9GIO3ZuX34+d9I3x38XtWnagy/+On1G9Vcx0cZrrd7yXx2i/mLcN5N+2B74TYzpuU/WNb+86o1h1+M7I47YTJkxJ/mEa8b7G/O3'
        b'vrP8bc9v/5UzYENhQ95Jn4Kcm0dslkUnpR1yq614Y1gt+ZycNXvFRKcbUyY6XfylsiGvZlvD2D+uCC48n/6vqk9OK2OT3qs69s8wUx+138mKHRP+9f3725K/mDxesXHI'
        b'3SWnPv+zaVl013fKl/y7vti2/PPYJZ5dB7P3f16f+ku69G3zl2UPrHIvNtbESf5YK1/RYPq+y09WwZU/PfXxO8VlO585cZcoScHP/vDxBw+eCPml/Msnj+N9+zWnNhuf'
        b'fCrH85L45l/WunZ8eOJbxbZvbg9Ls7x2tP7ekz/a7vjw4+Lfz33zi7vr539/udX95bVfd4x0CG8rfNv3zLffJI84/lF+UMsv5ncnrDr50vN7Nx+fZVn81lsNmz5Z8XXQ'
        b'uVF+nwzdPvCs19mJzzxlumTtz1av31lQ+OI95XrOYlgzUKFwoewfFNgs290lOYHpqyOhTYaXsNaBKetqoimdYxprKp7tTgEkkswFpmPmwG05Ve6c8FRPusvpcIspZvNS'
        b'TYLIyaccFKG9auUlTYaT47nOnI+tcRoFFPZKPLtDPkgVrrF6BjoM66WhTpDp6aex6Zxdshx242ENvSTe9u3BLnkOm5gCj/vxsLMGEZGjIUKVlzteJG1hESo3d+ANNZVt'
        b'4QZUaxOOLPCOdA7e9MxyZkKgDd5UexC51l0VqjRVQheUBJLT9wAWk7ZJyQ5/Xh4BN7cwrdMzARqDtOme8mgJ3F7kMpLIBhyOksiiVUG2y4NdyCG0RpxCZKJDTJW23LSZ'
        b'DIknEadpFQ9KNng6YdsYXv8id/IMRXo7BEepOMGh3uxBwzh5AvfNUmCBO17BWnLDgSCpYIxXJWHL8Sy7YVjEJn5ZNZRcxDZy0FhAAREI1mAxtzLchAIjLPaAC+Mo+gmD'
        b'tN0SzN7tTA7nw5rCb+Jp9wDycjPJMjjlxuFTukidTqtdArA0g9qA/a3wYKixYA2XpVkz4BDHijyzHZqDGHoKzaG+JdkVKcXzu5iVYL6ItdgWhK1hCmhylgumUOqBHRI4'
        b'C2VEh2dJ185L1BRn0pRoHkaCmUsglkqwWMQKHtt0MQHyaPVMc0YoiQRG224BXdKBeGE1z/PMD4FzrtC0Es7yZFhqXdnlyQe+Pg7L6Ci6eijNnB3gogu1Y9jYS3H3WDjM'
        b'Uzr3TYC9Co8gbDfFm0ryXsHEUrJq9WZmj1JuwvPqUFGA9jAmIjRm8Ukpw2N4C9tIeynQpKvHBCwgDTASBthJocYOzrKXL4NiMSg0Wt6DnHMY7JFBAxb7s75PwdO2ao8A'
        b'uESmW5k5uYnMErl0NlR6s7YnYUekInC4m3twJlzwJ3NTrRSFIZGyRXgqjre9Mh4b6R+xFI4JeJvykRMRhU+a83gEaoIoZvbAhDAGrmgJVdIZeFQTlKXCk9BJOiaQiGqd'
        b'PcAZA+EMm8v2MjipDpBHuSiJ6ARVIpQ4QSebT+OTd1GcTSOBtP+qqBBI/fOhmScX78FTeEQ/HxoqFlJzXdRgNtwWWIHXKWhjA7SxV3LQxit2rEeU5OHL+rCN5kZw3Vo6'
        b'aKURe9gtbazCmXREZjCpktlEPI61EqKbdA3l8/A0nrCnLYKDTiHuomDqLYEjAYvZOMcmWCs8lC7QRnSVK7TmJqmSVCifwy2ThxxxrysZIY/JeDyAwTMLVlAijYMrcIf3'
        b'9PURI8ibM0OpCHdOHAeH8aQSb/GQtLMmKQolHuQ9YoRHRLqL4rVILGedlZKTQVoEN7yYFY2Z0GBfBM82Lts+T+1hhF2srVIsFKGOVLCZNXY7dswO4uZ4OenFRqgJlOA5'
        b'IqLzGh2eOVsd4KIMnK4KpvANFp5SE0/gwXxjsMuM7QKT40jNqdh6xo+/L38akHpmwdUoFY2BI1uXOCwaD7MSXa2HYXFw2Gpd7BzdapAb06BCFaUmwvTFbpm+3kID3NuG'
        b'RdTsG42H9AFnYV8mf2UtdsIlWlNVsKcomM0ZO0cCTb4+7AyI2rBOTTFTsc3GjS4kMgtptW3JlouHsQWu8wTq8zaJaiwdA/uUZnDRDdvpFt5K7htiLXMhB0QR75Ai06E0'
        b'QpFfMloqbgvHopEbefX3zMfOILy5TGdLxds2bHAmQ2c09dHkYBsZmwFk21m41iaBPYQnXZaroc2SUYuIcELAg1N4N07KiiES/TRowUJnsjTwBLkKe8kJwHaUmjRzUlvn'
        b'QOelm1wkgjFUSnyxnPQxXZUrTZbTmNawAKyhDi1yXtE5YSWRJkz05pbkW3ZY0I1qbg7H8Gyy1GrRTLanLMT6werQtbHkhAok+6lmP7SH8zJvvJjKumEKHh3Ft3OmbhwV'
        b'fWbhyemTOUV3MdQt1eyHrJfMMHckXiOzYCDkszZ7L4BccthedWcIp5Klojvkb2N7XnQAFKvJ+JoOos3eRD6xNwzESimchMJ4bi4+O1EZ5K7Gm+yUYQDpNMCUXkpQQ0m3'
        b'OVYyyNWRTJxTKwfI5UMU2QrRwpR05ChxbpQdD8bcMxEq1aPIiXSAugJsxTGjTFkPjJfgbd4C0qenAjLZdQtskjqRc+wO20PkWDGA48aHEcGAbkEcN35aFgN+xdtwdiBD'
        b'BPPEohA3ZUDIiPVki2bmfSNh6gw52Y2a0thobcE2clAx8zNcgwJugqYG6BV4goEdx0NpMINT1sdsP0V099647VF40cQzKpaNgn3qOAXDnXXPDMBc2Eu31wFkNUKdER7n'
        b'8kDnAn9GMZ3koN1FKcN0Mh7k4A+V0ByvDlVqVlQ6nvCTQDM0R7IhXIudw9ShSZOVbNc+JEKpG57jzx0MYI9BtUSzZ0ySmhKBqJT3S6sJlLnqg85DNRzvAYi7lDSbDkIO'
        b'5sEVbRtC07BZyZrQLoV6bNzI5bYGW0kPyHvoTKTbKoO8x0YNigXZ7DYonIlQc5CefVLsEKERm7CRY2MUD8R8BZWNrozFO2ymmwiSJXh6kubgx/zpCg+ySyoDRfLsVbII'
        b'FXiGdfFsvBFJW4olGWaBIXS+kIdtIU+KBauNGeSucyhUK5SCoBgiDqV8La2W/CTYbZqiDsUrnmbO5KzAs2xftl4nhSKo2clqtRz2QiW2uUEV7PXwoKu/hp5ft3E/Exkm'
        b'Y51cgXvM6QKQKEUHqPHhrNftcARvqYPxwPAA0m2mrFl89WKZjLpzLvNNp3EgFijcPWib5A6SpeT3FZHsxQmRCYxaJxSPp7i70ElNFu4hKIajvC9rt3moPV3IlnBzg7+S'
        b'7jtdEn+GvkE7K3kNnsQ291BuhNghkjpWh0I7a/NCuLKOwht77MTjvdCNVxnzE66CyCwH1R6B2UpTLCRCGukgCZGxF2An39XwfLBWWK4bHGDlTDc1C7wh9ZWMY3UnlSF6'
        b'AA29riPLVht+vRByjXjw+VkTl6AULPEIIZvzFnEGVEAJ6w2KwbMvyHoqlmqCsvEqXmW7rApvGjHTmzee7sYokY5RDvjvoNfKH3Gd41DwlFm5ipnxmZdnKTV7Gfby7BJ8'
        b'TBiAMAcnNhNtGN4GRd2wZeCAcgpTzGLATTQAxfSzHblqKxlK6ckfSKR24tAHEpOhouNXEitr0fqBTGL2i0RGAY0txbGSseJQ8mn4fckvEgsKOGxOnrD5SSKnn8dK5A+c'
        b'RcufJeR5a9FBtP5F8gf5dDMGecwAiylssWgt2v8skQ8nP+nbZOJw8t3+B4mpDXkX/Z381cKe1IUijTg/IGUZPeTd5Opwci8tlwMgm5AybEl9TEiJlt/KFSZfS35nHqRF'
        b'JeGk647k+zj6ZtH+Fwmt7c+SH+W2JuLWIQacN7zn9UhTHzVweqnIT5GhcqIWRLob9uM+2i28aafvQOq/DuTFLP39qkgzjUNDlTLyjYWPN5n3gilRrRNYonXEfH+/EL8I'
        b'BkzCEqM5TkmyDlyE1lBF3U7c+Wb7fwIfMl3XQQfJ602NNK5LE4lMrsGt/klm/B/8dFc+RSJaWplooUjIlBa47fiB7UwttIg9u2pGPsuk2qsOuwSzbOpdHgm7sZ4BjHgE'
        b'hmRv1LfXS4QZK+VYtAVu9UmoN9P8VJs9HGVEmmCi+Wyq99mMfFYkmLPPFuSzpebvVnqfNYgjx0x1aCK2CYP00ESkemgidiXGCeN0aCLDEobr0EQoAomQMDLB8VegiYwq'
        b'kSeM12GJWCQZJYxOGGMQRYTiluijiCQrne9ZMdgdRlW9IDEuNeu+Zx8IEb2r/wZ+yFSepT5BKbknmx8W7ndPOm/CPFU1nfWH6bca8fGBPKbyNMsJvwr9Q/PQ1F+P8KF9'
        b'Hcvq9KYIH6ozPPWGYnGo6hiyULhfSFikH0P2GNsLVSNiwYLwxMyeueReKhoC9Vi3euvgL7QVuW/fX6k6TIyedVaa9iiDjoPqz/rAGtrOUb1MW/QSvdTfO7xVV+g9/4dw'
        b'GH0pcY1CmTfHWLaNgvYtxb0Ut4+C9plpgAJnEUmzXMGRvJqghmKSHfNckpp86bxMTdXOdNfLH8c8E+cfezfJ5W9BXVtjzZL+KXy5Z8jUVYJvoexPI48qRa6yHdwxhIb3'
        b'ED23VmeBIqpWUT88oa3aCBCWctWfbEC/lPSc3Grfa4E9JqrGMGMt/nB/Rxn9+qAHukb/r2qjQ/kchc6gwRX/degMiqw/Sv640BkJrMYUG4BG7f8ncTO0K+ERuBnalfTI'
        b'O6Y+Nm5Gz8XZH25Gf2v8IUAWBter4ft/BW5F7/wsnkoQu5FmAdA0q36ShnSPGYJF7YN10WOcNfgW9JzgmBXkrHDpP7/nUcAS2pr8GmiJ1KT/oUr8v4MqoV1xBkAV6H+P'
        b'g+3Qc9E+JraDwQX8P2SH34DsQP/rm3JjFBqZPYP8smMZhb3VBxSAMhMtpgBWYEmwhtu323cBd6gF6myMRepUywKpmkbKGc3bTRnJ//lOStLKJ1578uUn//rkq0++8eSf'
        b'n3zryc6y4+Wj9l3ZO+ZE015l8Y3XTuU57dt4oqnmSqH3vlFHcn1GCLmdFhOzpymNmE0mDPPwFI+PXYm5NERW4rULqphNxmQWttK0/5UzeOK/Xtq/xTxmkxkHFSI1PQ6Y'
        b'2A2OylLq29cye6vfKNgTxOwm2IAlLKH9COxljzpjyXpdwv7Add3RzNmx2qjOfyfCVZfp7vYo+SZMP99dbkj8+PXJ7KMeS+x51+HhYs+vyWhPUYqhqnZRK4AZyGYPMhY0'
        b'2ex93qRLZR/dzwHXJ31d/vBo23jjXotBoV0QC6hgZtxLNFNQ4SxJoRHNjJloZkJEM2OdaGbCRDPjnSZ6Sek7DIlmD09K19cQ/5/ISO+J1KWRdzRp2hvICUHzZf+XpP6/'
        b'JHXH/yWp/y9J/dFJ6m79SkVp5ATQpyX7VTnrD9ky/i9z1v+rmdZSg2KfDYdDXTV6JM+zhj3QxZnJ5kM+h+yiFvhYbB/K08ci/LEwTIu45R+IJYwQbBkFu6LJpDJhijlU'
        b'QLEpdOJtKctlxD2z1RzUi8hW7b1zp03msBDqJNjnoLbAlvG6lO1BQ7KpAwDO4UVHLcG5FOv6xduS0Oj8k6bYhfnYnu3OHz1l3p0UigX+8xLceIoGFujIVKPHm8xdBgfY'
        b'ExJfKAzy0Jd2N+GdYJbj6oalITx2K1xhTFp9enr2HIH67CrgtI6aNWrxMvely2iWbmBIMDRF+sMF/xAP94AQUoSnBFoVE6A4nEiaNyMEBzhmmbZYzWnhIHeXegIWyrXE'
        b'GBvgWrY3bcGhYKjtVTrNOc2YoAqPX0eqxRLAZUIMFBtD9Vq8kk3lJ7xKei+C3wuHl7lpByuSPqbX8lVJxnA2FUt4akO+P5RGQqlCZUm6UjpAnImXoIgFbttBETbawwFs'
        b'w45Napotckd0dRjOQuW/MZIJJsIpP/mcmDSjqFVC6s7Ed6XqP5Er7nGfRR28YgFe1n5/zPnkqdw5i561vVu+38j5omqsra/y+P7Fq1eO8//2mbFNA5x8MuzKrZ9/87tb'
        b'D+4kPOc86p/k4Impnv7q/DfiqpwXh7ZKw+tqT/leM21e+4ZsnOjyXlDg8FMXqzxrjvj7+75Z6FiriP7zZlMYMvJvf3/h5SE5+ZPxkz8s/MMtq52rcv5uvHzgRzXD8p67'
        b'7+QyW72x2PeDpG837Lz9sfeXSStufK346tPosHdPLn/Z843siqyff//zqddHmD63zfezgH/tch8SGGDsezb58ndWe14ILHE7oLTmXt49cNNEP4GTOt1pKI+dEY+mOwD7'
        b'FvdEEcMya5q+ibewizlyU6AdaoLCRkGTJoFzKvIUSx84odKjwlZsmcFSLOHWbOZAdo5Y1AtBDPJHYafMJAhzeURE5Uw4o8cTrMiEesoTPCiYx52cxkqsoFFWJ1y18F3l'
        b'A9mTllin6hGNdnU9o+c44MmjZYsSXBUu9nBEL2BWL1x2WhaLgozEemzh9acLtpBqVZV42hJvSoOleJzHWBZtEaFuDucq5kTF2GrN3NhbsByuBk3IsgukW8AlgewTB3hm'
        b'61Yy907bYbGOyoPxeFzBPaxbbEm7SlwDyTqbBMfpsJAGDBwvxaNYs5G/89hUR6ZB4kmeZCnxgrIslgOK+WR9ndDPsexOsMQTNizHEq979KWPU/wHcxwXP0oD3MIyHaUm'
        b'jEDXRC6nPmHRVkPGa8Yod2kWpKXERJe1uHVkbx3KcGqi6eOkJnZnJRr179s37p+51kAGYuhjKaBXHfUV0Ec16b+YhLjmkUmIhjS335SBSJ0UfTMQx4RmU719FZyFcz0T'
        b'EPWyD6GYHIEPzUA8NZX5fpGsGNDhC0RDhY8XXBbi5s+UKoTR2CKl0c5r2LGQBFUraaqhi0qbhYin4BLPGspfAi00fRGKV2vyC9My2aEgWSxdkC5haVvBrb4DNagseTuc'
        b'Bi72wbLuBEIBG9n5ZwbXsZglEHrS6LtDnlhjxS5AsTNcUGeKAlzxEsjZC4UrTHn2UWkKXIBCtatSl0M4eRN7zTC8tI6nEOLeGSyL0BwL0nmFr+HlKSyHMAjP8xzCrUN5'
        b'zl9JNl4dM49mEepyCPGEA6tD5uyRfnhJkaPN+MM6OM/4OfA6HMYTPK2P5vSpo7qz+g7bs47Im1Zq9qFkqkTwivF4fvVwnspWs2T05qlCAe2duN+vMON/dM4KsLwqcgLW'
        b'6pw5/15SX97jJYKhsX4imD/5sAJbBmg4R9zIhpoZEIJFbljuyjmOsALaKFQJjeJTQrt0wgQ4lgHFQVCBbWoF6bT5WGAVSVpfwJp0SG0xzVRCBntxTLDloMW8neaz7HLu'
        b'CMspjOmMZFNHjnYRjh2kFyn7l34SHzb50zw+qFiZrTm99sBlPxq+1q5N2LOfygp9aqzx1iQpw0YNrp23UtDm2O0PxDx1KFyEZjzF43HhFjT+2/mSj9G15ia9c+yGQK0R'
        b'NCxT5Ohy7AKhgl2ZDoehiubY+cN+nmPnBJUsT3W2D17GNnNsJy3P12bZ4YlsPptLoByOU7vVEgGuQskS8usdhs4L1+KI6LvfiCbb6TLtsA5rWardOjw3X5NpB8V4mGfb'
        b'4aGFWJTqdiTSSH2YLMNLFw5mRwapB/nZfvbZhzU/1uZ94f+MhfWctXusRo8W/3HaetDivWaNKWfObHjK9I0bwc7LZg7zfCalOqotIXaJz66nVH43EmJvZPzj3r7ZT7S6'
        b'3VF3Xqr2vzF10wubbqs3fvfhV9mDOwvkqsRPDnmpHO9U+FU9Ezgk6g+rN8/e7Xkh+KCX5QH50nF3984b+vL7nYtjvp6zc0zL3YuDL3pMLFlZe9m1bMA9r4NbB+5rHL28'
        b'zm7S0wXP142uHXh27U8+6a8tfKXF762ruRteKJohbBQ7WtrdYzbUNZfct3RrL0moP/TFwpDKOx9f/mj5t22p3+zy/nTojyV+96f/7eOQpyePzzv4075n5ANft/N7Jz1v'
        b'w54Sz+hhPw1blHL4ve8vPe8QFnf24nmPxK12d213+V37XXLokqQLue2jN62atGHhjk9zXrNM+CTY4bzTrk3VLmfvvnnol0+3lX4aGxa5bcQEaLlZ13k1/rkfyut+fG3g'
        b'K+9ZjkpOi3rhUsy3Pmrh7tanHb/NW1XZenlbdfPNuIBai6T3Ph3nE/ZC7LTs5a5/n2W0bWhOWc2Qj3ZvW6r0Ozn3a+u4qh/cPrlcffY5u3dmGk//27q74/4/3r4DLopr'
        b'+39mdlmWtnTECqIiy1JUVMQKIggsTUBFLIAURekLiF0EpBcFUQREVECKIE1ARJJ7E9MT041pJjHFFNP7S/zfMrssqHnJe+//k4+wszNzeznnnvP9Hqd7b3Q8/tPXKWlm'
        b'u9/fesK25+mln289PeH1run3SrhlAXvnGO87fU8YPqfm173vfH3viTlFX/jP26X909ma8Iv7EnRz+xIEzwYV/fy9f0PC7N1xli/c6bbN9jUMC9xdW/aDZ8nTUaD9uuHb'
        b'sSV1R+qyXsjaXb1+t8Z7bTE3Vjz/e/BnK7wmhOr9kO4T1iYOmbVtTbqDy0sjeb4/L1k88mZEJ3zPNW35YPnVZ+7fr1qd1PnKSx5BqSW/a94zeuNXtuu581KwdHprtX32'
        b'8bylsjr/7P15n35kXvfkot8jPtaX77/vZ5ysa33m9+D5WdP/rNe6+sWbNbP1vt814Y1fn9kZ2myhiNfffT4y743toc39LlfKlr5yyX3n/PZXfz8fGfvnucj+pjcv+Vtc'
        b'OtLsBZ9vf+Obve56Tk4f7Ym4r23b8vvP97/6pPDT5Taw8t7SF5JrL3299+XrMSd/vL1f/LvY84/NH/dv1Xnzeubk/g+nwLRpLwc8v/DgiuV9c2XRwucXRER517Tq/h7O'
        b'7Y+tC1rSVxn46QvvJx4o2ZXwTM7t5Xmbsw9cuz11psec5G2uSaG3w+32DPf+fMJid3hsckZFWobrmyfOzfN5achp+tWF52TPz090r+x74ad5nz8V+1TynzcyKr/65MvJ'
        b'ERLdryc9+epg5JRp6VMDkwRP7tIPLj/72HPLXZMWtu/pG7AJk99npsTdfXbra9Ik6iXbDLNA+xj0GhLG7S1U6LU8bSI2L8uEV1fDStnY+HXL4BnqxFsLjpmP5QjeR5lJ'
        b'ykEueX/6fA8CXkO3N8AKFXpNX48qOj2gC8fXpr7PPOAsDBRjzJnJdGK7MdSbx+PNkMZTSzFn9ooNFAHTYjdBwQsyoMFkFGwmNiJYM2fQIOGhZlIftBMZwyZb7AvMQ82W'
        b'gBwR6HEGx4iEnzrVg4fDJLgSsJktqt0VqhOdgy0EuYMxZaEMRZXNgifAUVLEObrucAiJVBhWpoKU7VxHi9gNK0SgPITHfakAZeDENKLvgAFwFear7i7zVMOUwXp9iqnI'
        b'Ttq0zwMWOagQZWh5J2U+MEMDHjWjbyvxZIuSaNdczPQRgZpRPNkommxXGHl5V8B6CiVLA6comkwA6+0opKkc1m7hwWSC3RRORrFkxTJSrengGqyjYLIZcgonI2CyDHCZ'
        b'duyFDJZgyTCSrACUjqLJ0E56hm9UY1AFjoMTBBOmAoTBegeqcB0LhDUEElYF6ykmbAG4StosCF72m4/hZipY2CgmLA1WkDZbaWEilYzR9WCTGUl4594VOv72ulI4sBvV'
        b'GpxjYYcM9JAi6SwP4zEjSPN0jlEhRrwCeYResqbcfwzKDLQt4YFmhxbwgAK9OAI008XxEFuUQLMDoI9Ou4YAWKPjY++bgmVuWCDFUDPQgrSeaUIhmgs1aDCSZOql8DCB'
        b'lAV4+4DLKkyZaRzpn0xY6ofhV3jujuBAoUpAmRxeIE7bq0ELPGIOT2LXfCU4AfVDNtXh68AFNOoIiGqJMQWV5TvSk4lSeExBlXjDTDUCqAFwlrxqi5Td9phUjCpTIco8'
        b'ncmrvqBgMz+BFLBfxW+E0h6mIIO+mGUUUsaBQYIqI5Ay0GhCJpFFMPY4D8O1UiHKANLdSakG4TC4IkIStIPUdhRUBrthGU360gZnAirDgxmeUoHKdqdRt7HzsCeJYMqs'
        b'YQWFlcF6VCn+5Tx4IkGJKlu5hceV9YH+RfTls/CkD6jEzIClo7Cy9bCKtLMIjc7sqRyaCaOwMngWtNKUS7C2QIBlSbCbYMswrswKFpEap2qB0xRb4rZLhRFpTiDtvGkh'
        b'KOBXgiolsAxepjCvfDROjurIkIQ7iixLA50UxHkNnkBr0TA4rE7NDmrQYnKV9v05B3iZyLNlsJ2XZ68eJK18cB0c5A+lkAJVo8KXOfBgmGkwx4qUF82lOoKHwWCYlXCE'
        b'HO+Eynx4gJkavAwe3cwjzIp3k3VhSxAoV8DSceiy+B0YX7ZXh9TPA/REKNFlKTj0qcY6FhbODKagjS6Yu14OC33BIBii+DJvQwoGy9PZz8PLwAgsIBCzLbDWizS1PWgG'
        b'VfguLJykRJiBTpa8mAYqHGH/JiTOqmHMYIU3eVED5uiuAGcJykyFMYt3IstBCuiCZ3CDaKPpgo9E+zBQLtAcXhLK9qDeIaNnCByzhUVbxojRqHuqSWdoo25qw64DeDGg'
        b'h2kh8BRdvht9onRoupNhHRpHaMxrg2McaF8GO0hTCMGx1ShZNPBmRAqxjmoFOi1pcFgv2EQRQVuMCbRtm0B/P1oXCcJvaLmlgmyGtlo8rA3Nrk4BM3WJEBx1gPV0GJWj'
        b'PTmPB7eBwRCKb4P1aNVoozOydyOGuZC118mXR7hheNueYFKz6bBuHd7WfWEVaKXwtnjYm4b9MDfBZlhB8G1q4DaQ7UTxbWigXqBeFQFwAM2kIbn9KMKt24Nk7g7PbaF5'
        b'e6fE643i0kA3BdGsnD0PFNgoz/tVqDQkPxSREAiolMvHwNKUoDQ3ax6WFjqfbs5HQSM8gmbKmdEmYxgDeFiAthnQQRLbCi7BKyReg1QLFkq9+U0engHVE0GWcDXS8BvJ'
        b'UDC2lHhNpA+SKmvCWs4N7aiHSJnXgmEFAaKhFRTk+KmQaAzf4LNQ4vyprDPdD3TwqSxqsBw6/FucrcFhcFL9UBRcApXkZtTO6bt3KlC2AWhIlcnQ2muwW7DPR4uUayo4'
        b'v2ApqJPhYVgmx6cPsJrbizYbMmFN4NFpsHWHAlOCFmBhEVePZQxNBfvno6ITA0PNDjDyADZPDZcHTh0YheaB86GUt6BnTzpSP4+owG2jyDZLeJ6M42DQJiJwVm9jCmjl'
        b'QMt8NLHIOjYEBm1hrQzfV2Kmk41pU/TtgkcpDDZWoATsrgLFtO+P7YQ5SuydR/wY6CBB3oHWDZTPsAv2ox3oHDypghCOwgfhNRkdIHUpm8dg7wK8Y+OU0LsKI1qcAdgO'
        b'ru3S0rFRQ9618w5CoAEUgZwFoFlnFKaGoXeg3otMcvaAG7xwQMdhFHgHW/1p1hfhadhElh8V7s45gCLvYE0yFRyr94BujL0DWbCLoO9MkXxB8Kn9E0WgcJkSgDcKvkMl'
        b'a6Ir12VYAfODUZl67EbRdxIwREB9Hq5oC/Lxc97CY+/axaRTzWHXWoXvONjdTjkB3nnMIYYL1mImAd2BEieCuzOG2a50t6yFfQsmOlDknRrs7swBUp5kcGgaOCwnwDsV'
        b'6g5ko+FPSnsMZE/nYXegSZMg7+BxWObMmx4MkByOgXejqDu0xZ0gyDvQihbUyWQvvwpOEegdvLKDou8w9A4Ow8N0xF6ARW48+M5bHx5zHwXfgZMHaTGqJoHSvfDwmNgn'
        b'nhPQHMZnQzB3KWiXO/gtSqfguw2glO7ozRJwePV+2dgo4NZzpZL/e0gdQT5Ri8Jf4enoj5USVWcgeDSeTqzC0xmRHyErYQ3QteW/OJEB+w/xc5piHs8mJJg18X30/H3y'
        b'c1O08AFE3Z+ckKLnTMgbEmzvICg8c9aMFaJUHVgJfl/0XyLpXtNdOhZJZ/4oJJ3ZePPDfwujO6qpdP/7KxvIIebbMWC6RxQD5Y2BB6k3lUg6AUbSPcnyR5NS4/87BNxT'
        b'KNPPMURwH/M/QsDdFMk4VqLxULTb7HFoN+W9++Zu6WTXOARORY8/1BaCVjuWsQEjGglormc94B8r4f8qysfB3Co1K7UqjWM5/LtSwn825f9q079xglhBpTiaKxFE26us'
        b'TjjajW6eXp4kzyDPKM80VhfD3Qi4TBijgcNy5zDRWtHaJVyYCF3rkGtdco3hbHrkWkKuxehan1wbkGstdG1Iro3ItTa6NibXJuRaB12bkmszcq2LrieQa3NyrYeuJ5Lr'
        b'SeRagq4nk+sp5FqfwOnw9TRybYCuLci1Jbk2RNfTybUVuTZC1zPI9UxybUwi+5jECqJnRVvniMNM8jRi2ejZ0Tbosyn5LI22RZ/NiMOlgFjoxHk66B191FaGpK1k0Xbo'
        b'iQnEHrdN6nBL193NL0QZ4/6Dy9w4R0vs6aT+BEXbqfx00pJw+AcFfWbBPDv614kES8Cf5o9JTGnNUzhYuqm5EPIecQRBwPvdobtpMakklkNSBg5OmzbWBVA9roOdZUxk'
        b'1HbL1Jjk1BhFTKJaEmo+iti5dUwKj3ICGmtTHHPhn4R9v7xjLUlUVoXlrpjUGEtF+taEOOLNFJeoBswg7lXodiT6n7Y9NWZs5gkxaduToomvOipzUnxGDLF+puPlJ343'
        b'dtMaE7jC0iOOeDzZuEl5l934sX5g2F2K9ySkHeHI94Oyxe0sbVZKlY9FWipisEdbWsxfdRLuQxt3KUZzRKp5DfL+ekmpcdviEiPjMayAByKjJsCQiXEVVSgitxFASQwN'
        b'0IGeorW3jI5JRuutwjKJFpy4/tnw91biEZaQpBjrARaVlJCAXZPJ2BvnZigV3BJkJsTfEkVFJqQtmH9LJzYpNSomnPSIv2eUUG1JQgvquBBaQn6qMGhxYdHyosMvMBya'
        b'OAJVCC1hvmY2s19jj/Y+ocrErUFM3MIDGmoxmJE4+O+BZGMm1aMdzx7li4iqSt0QQ/18eT86EjmFpDvah6i3iK8pmqIPd1C1iaFD61Hz9y8ATqSdF2OcSlQkWgEiUJEi'
        b'qD8gTUyViPowfEQ8m8jo6DjqPcrnO2YY4gGbkh7DT2VFOppjqqXk4cCOMT62NEwNnomR6WlJCZFpcVFk4CbEpG5TC0LzCIhIKpqhyUmJ0biF6fz+66AyfPOoDb/F2F8Y'
        b'uwCTdUrd8TkuEXVQJE323wW5oeVEy4169gTcRJINyVyVFq+wTMTwrYcm5YfBN6hRVMgtVRPSlPmFKPohlXy4q3Ts6LSNIku3gr6KfZ3jFUkUHYZaDa3hMZkxUemPwuSN'
        b'XepsbHEMHRVm0cVhzkNQi2OkDD30X4MZ7+Yx1V+BVbzGBYKel3+WSVvTpM+cuyO9XCR9oztLwcTtFzemXiMYiXQsN26E+RtAD+YKwTRgaUQvNpTisxIprALdgL4CGmET'
        b'PE/UhBBKV9sByoNAG8r9gAMYZg6ALtBBnRA0BYyvO15kInQLxZOZdKwuLsGaZw+H7dTNfsySSNAT/8v9+/efWSdkls42YBjXCN8pEyZhjlxCqp8DjqxXwEIJLNhFrDdI'
        b'vBrAPDpatjYsMw9WimSwEQxR746WyaBOB3/P+YH+NNYZNNuhZAjFdT4ccVNPRht0gir8gWWsFmtY6cE8YuJPg4c8dMjXSONEeu4VFrSsAjkoFRm66w+rU1WJCKZgW5K3'
        b'bYq/FHbJvOUO2Iy0Dp4UT4Ft8BqxtyvC9mMfR9imvC1ewCW6wUKpIJ1YVg7bggEcRcUeHgWFXk5zFnCM7n5uJ1JgB8kD2rAAHOIfgLXgNHpCxOge4OLh+c3pJPiDNaxX'
        b'3r8ArqL7LKN7kEuYAXPTpbhFrjjY0rAqXgYgN8QLP7rGa9Tdh2VW6WtOgCdXEwcU293BVGFfY480fqyuG+vDK6BUAOqXgDLCywxb4fEl6v5Cymg0sMBXLrfnUpaBuilw'
        b'GBSawm7YLTcBhXIdbQyq8gkK3gPqmZhYA+elYJiMjv0TNZhfZBNwj9u9u34+k76Bwcxg3bNQ+k77xueAfWYdfdbawAIvWByMXVXla+El5TiVEp/UAG8No1naMBc0amjA'
        b'QY9ZoEXKeOwywWemu1CbE1PSEVjoDXv0k1PZKQkMBwdYa9htSB0gzgbN1hGnZrCg2INBCpst0veb6J0GqRXs0U1JZWWwAb3Uzs6cRd2MbTeBQ4pkTM82ZyGm6I4Ax7yo'
        b'Q1GJl5UiBXbrogHkgV45xM6csYAPE7zOBlxQwMsoOXgF5jIcuMqahVB2aViaGkBzcoHlNCc4AppIZ09AZS/je5vbrOprUAaPpC8iY3w/GJSrBdLxs/cJWOtFX0CP8y0J'
        b'DsEeBtbH7xTrgAvwEiyTssRpJhz0wSYc8sgHH1/5wKzl1D15EjwmTAHNEjID5FEzRnOYOJvPI9B+HU2bgceYaDggZhzBtbh3X4hnFfvRRG9aFJdwbDDJ2M3k+rbYbY57'
        b'dymWdAk+WPiJWJI3NwWsWVW5ZmaY5Qs2j5l7XKu0OnXU4O1infMXDTRy+7093DzI/+NWHwacabr9QubcT2yWHvh67/s1P9dUr+0orDSt8Pf+WDM/0jOkMuyP7c7zBp/8'
        b'bM76Uu3LXYdte6KsjrqWG2cNLDjzvPdcRZHYSt9q5MLOy9oDy5KDjHumPNdzKDfJvkBj2oD0lmvZwmlG3udn2f3S/Mq93ZyW9szfm16dMPPJdwVuafc7T62yfkUo8fzq'
        b'pa/+2FLqMfdAQdZMx80ffHco74ah1mrjb7Uq/GLfMtHfuKI781ZIbIhkT+xu86inP7F0+GbO4xefvfGkdc5m19tvvPdru4LNsJ/05icng56NtS/tjfrXovB514ZX9Bpf'
        b'35V6vu7D5pLU2PO1C351+QSEmUneeV1xVyvgpaPXvum5W2/5bNN3TzYdv/3im+/tXhiXCD8y/SzsmMvHBVNGDKIWvn7+9iLhU70ZMwf2X+AKMzfcrZPN7Zhx+PJzZyzE'
        b'f7wx4YPYI0tP/BIz7fP1mulvXbi2prP4tR2fbMqq3jvP8bt/2Y5c73Tf33R35vmeRoPtzpkX1i/cuKqpTfSW3zfPL9DKfM/81KTv1y9Yrfdib235vdUnT3yafkDH3zfM'
        b'wnfTfb/sNStvhd/uf/KHXeu+uGi74qONBSnF9z+Qmp8+d/+7+dcz2/2f/Gb+vNOib0KM24Zcrkf13bv/ZLDGtLY/zDNLdQM+qt7ypknuH9eg5AtB/QvN5t0Tht+OdxvJ'
        b'TjVde0Pv1k4PzV1BrzXvHB7SOPeb7TvTr7yyv/kz43eaC8Hue8+4RhrOqTENN5yY37V56P2IN4+dPvf61CDXTzaKXTcIPr53pWnvSzcEd1b8oaVxWqf7l6VSV3LUuHEV'
        b'qJA5+CGNHlxYY8DKwTHQR0wQO8DpSGoAwOPeHBwO4ClVLVYLYTmogp30CLgG9mAyLdCJFyK0AMJCjtEBV7nVoAi2a+lRO/VVoYnM21cTZZIPrsASdhnoh5fIuV6YJbys'
        b'zpU7AXRz9pbwJD0qzIXDsBoUOVIbtSgCNDhzVpZKtwm0fp7HcaMcA7C78QHYsYWzBVlwiCRsIEdFKkJFLrEXMaItoDeSm4HJX2nCA3bwlDzA3tsOn6jrgF7OwhxeBXVy'
        b'evBbAgdA77iwzv6WlsItRqCSHnMWgtz4cT7iW0ELRq3CJgeaRWPQJgU8AXvGHMbCUntquz4bD5rVKNBAAzzBwuNLQRelT+uFtfCwzBtctMFrYTYj3MbCI1GwkLZ5h2UA'
        b'tiXwZ7VXo/jj2kmwFq1Il5JJmyehHfY0MTDiuAjEOloBzhIDOxzhNFCj+vjJ7fFxqn8I7ORTmAmPayxBe1k2ORKeCWoOKGCJN3YdkMOu6RJ/e9gr55hpnkIk61wGA/R4'
        b'PhceD8d+BmVa/rOi6BN6HhwcnCCkVI060Sgzf3s7tGvFwHa5P5+X5VwhklCuRVJj2glQCwvUON04Do4Eo40mD9bQBst1JeSHDj5+aGE/buftxzKS7YJFmQnktmFYJN2i'
        b'D8B6/khdb4FAE9YakNt+oBrWE/NLMVrJNRmR1lpwjdP1h2fJJNitBzsVmINQDtsZwU52XyTqB7xb7QNXAngbcmQYtSJPzaDn0cNp4BRvD3ULVFpEq3eRm14B7sSwR4zL'
        b'GvDU5BWoF0GvM0lz/qS9Og5yBw4UZKDXWllQvwLkkCkHeoxA3YMGYhMRmi3YQOxLyWPhCec9CiUNKMrnKjbUtsA2Ouw6g1g1BlEcUpDdAgt5C5gbPANz8Kwu9BW5OaDs'
        b'a1hQugHNNmKEGTJE8xBVqUzGgYaV6G4PC5p1w6mZ5Ly7OfWGYG1DiTdEJaigOfY7LlR6J2HHgCsCeJFjYbsTaVr5AVim4GlapyKx0RKc20HtDV3xoB53qArhAYdAI2ME'
        b'OgSoBXJANxlcJqhRUOLZiwOUkAkxOIV5+I5PJ0N5DTzPjjpowS7QNRYxYQUukdkQyOnCHsLhC0sXoJr1saBjaSQpf4LDLHorDRzZgkUmESOJFngw89KwJ70zGum1oGhX'
        b'BuzVS0FCwjnQoZTAMAjeEZZ6+dmjV4I9xJLNurR/sizWKMDZGTIkpu6Ssozmfm4+muydxF7nYuml2A/Py1LpONeM4eaBi6CRmKu2OJIh7o3tbQEkxqEGYwoHDGCr0DAU'
        b'tJHEl8KBCJ2ZdjhlmgBo5ZaBox5kFsWDYgGfQC0sBCVodGoyEn+BqwBW8KMW9INLCh/M+s3CftAGD7MG8KItsVeZw8F12BCGVud8bAcL8aSr4Qg8D66oW8E4tCASQ5j5'
        b'JEqYmOMK8rAbEmMH24kX0t5AYswJAqVyBc+ZOnc6OyMOFBFyT6Qy5cM6VFJUEG80JcmSsCHd0QuWCJgZsEnDGRyFlG18rQwMKfylKd621KqKlowaxmCqYM1ONGlwHmtW'
        b'gHOYdJpZBrMJ53Qm5TOAJ2GeqYI0kuYiRgBy2T3wGDxGRzraJDJlPvZye1i32NYfLSX62wSR61cRqIopKts5Zdla7GjxMMyoAPsJSLdoYE8RMJSG9Yj1OzVHx4ZyXFij'
        b'hkVDI2AhEkSXgA6RfwZaw/AgdHCcQL2tdEEJ73A1BZaRairs1urgW/zoRcMsizFEUwlcNPWiO8JICGyXObNkz0E7mhgOcaiRakNJH6XDYwbjbHdm8IINNt15TJfq/ffW'
        b'sf9P4cdU5Ay96Ne/MaQdZFK1WQNOwopYbfR/CqvLEZvFHyINA2I80yV30D1OTD5J2Eno/zTWmrVhjTgDHJAM/UwhzxoQA5SINWPNUIpG6K8E/YjR09qciDMb/w2LfyTE'
        b'kIffFZFP2FS2x1T9pG4cQ4RURME472Pj0G3864OxKB/d/6pPhGppjuajatdA7BqPv/83Vq9DTPeYKGQPr9Hf4p7I+bfcE4NihueeGJuNinhirtKkQM7k7SxjtjlY2uLD'
        b'RIc5C5yUlDgP8lD8reJtw8VL/KviXVUW77fJuBz8+bRlXPSYHP9WZrEosxb2ljicnn5FPzLPEVWe0wlwnKClY+mhGT7Y+8c5YwYQKXtLL1x1LB8e9+jsgSp7azfL9MS4'
        b'lPSYh7Ak/NMybKNl0A1XHs3+VRGeVBXBFreAIg01ATncVZ3r/jfFSJ30Vz3+tCpvh+AkTMSUGJtEmCYsI7cmpaeN4XX6D/PHPD2PzP+5sSNOjWfoP+r3VK+/yuxFVWaT'
        b'RjNb6e3+H1ZM/ld5vazMK9WP+Sfzs/ivEn1NVQGbkIewQynZT/6jyYqGqzYhcAjHdAqPLMKbYzuMcDDQSfufThIxzTUt6ZF53lLlOZHn6/gPc4xVLg1bI+OxRSk8KTkm'
        b'8ZHZvqvKdhHOFj9LzRzx6nbT8QQv//GCJVGVKio+SRHzyGLdHlss/PB/VawxCNb56Fcel8fkCWIFf5MFVGnYE7EPM+xhQzU2fhBDdWR8/BiDBjY+xcfwxhWVCelhJCNB'
        b'kXEKQhMThCoTlxDjkZqalIpej0lUmVWiIhMx8dnWGJWx5oFUMDFNIs9NE5dIiD8UaWgGxaHXbUZ5QcbYzx9IhKcFSohTEPqdh9gAxxhgcOdhm6oTo26A0fZ/AB4oUA4N'
        b'rFMQeKD2fnYfu4NRht0j46CFJdBnKR87kUvLHD9GsF3l8zG4wCD0AbQmgMOKcaI6PIqPiOxBoaOPPfYvlsr94NEHwJdF8nmwUgW+RFL3VUN3UDeV0GZkzJ6pcqId5a/Q'
        b'gdnesDQQ5gcEj7EqgAoX7YMLwdF0DwYHUkKKugxD6pV5r/EiZ2yBo7DiVthCocXBsBzm48OPnqBAe1glZOYkSJZMgd3p3gw+CSuER+Xgoo2Xn4O335pAWBJi4+BnOw6c'
        b'DKvWeMEyRxYU7IyegDTNpg2Ru6TggtlOjgHF+/Rhxcpl/7hPYmm7/6rWIxrYCPnQTvl+TKcQ0pFzziDrIe1HGg9V2GelepVBboSWmR6siJuXNIVVlKP33wLTv4h4futn'
        b'ET6RvpE7Ij+LSIvcHhsfa6LZ3W3eU130ms/JoJM1E2vM3eZ1JfTpLtDd8LxH2+JDaU5RXRMCqzQ+XmADrK4z6wRmGt9tyFpcdCi13XLhpspZJRPPSp6OFdx6WtTddYTd'
        b'OiPwKd0zkoycOMvq0I6w65OuzxF5HgEuuWELdCOq1mm7zxFsEzFsjWzG0zOlmhTBUuUEyuTqyi1VbS2MosAlITw5DbSTwNOwAg7CAbUHVWrmTJmGFJQtBSVgkDwJsuEx'
        b'UD4eikZOOWBJuBB2gi7YT3RbP1gLWuQ+FqB3NAKWABTsI0qxjTc8jZTXenWc1G5wghRaCDtgFdZ78XsgX3XgYmFuC44IYasxrKPnfeXJBmP9xkERyOLAcZ35aAiMqicP'
        b'MOOpBsMtPey+E65cpYgC6IpH3L9TAA8yu6cRJU5EGBkwy7/BfRFnTlQzbW7PpDE6xZhM1L0HHyjZqLvgv9BA/kjMM0H/W8XpEFNvoK46/UX+/1PO6e0P45xmmfFGboF/'
        b'3OyBHkaBz+/K3V0xfbQ49ravgBHns19l9s36RcqS09HFvnCIMKns3ah+xuYCOh/BGW2j9H+1/nu9dpDR2WMyTq2Mj0kMD380ZzTO4rd/0BH5Y5ijH5rZ/7QLtv29LhD6'
        b'h8TV3+xhFfhrcaijPFJ3YHrs7XiWEXqwnrNmji6TD7ZyF78Gpx5mH9CXw8O3JiXF/1UD4rf/+AcNmKv7V4cANLcxLYhLi/Mk8Rt9GCI2Kem1lcyO1FeKzdOLlfBty+Vr'
        b'oLYVoLblVG0rIG3LHRDwbRs7vm3x6STeW8aKEJb+xDQcBYu8qUWZgVdAJTEpw25j4jwRG6TBoDawnCMKWPWvmTP4ENuHF4LjCkmqFsvIYCcHz7IOAXxwaJ09Qvq8Z1vE'
        b'GcEsJp1oyN2g1oqcyFO2HbxNFcvRB/99gZi+KigwyH4dx2xx1QQN4aAjHR/lWyVuwss6LAJoFe2GIypbiwZjG6UB2tankBC+841sqJWcEWpjK7kprCIeB+AKGMbQUn6V'
        b'hRfgYRVCpy2YkA/ALNBPQvAQgwY4sVZoz4KLJuAqMbNbhsBDlLMD9voQ2o4dsIZYy+ERcBaWgwYfcv5p64+PgvW3CWJAu2UITXgYtjrhqkrtvUFHgpDR0uQwY9UJavIf'
        b'mm9JSY/27xQKWbSVHAEj5M6GZTbYZCa1h6cXihgtFw40ChaQHloUqMlvOPAC6KLg3B5YR7kjBuz9YJG9v4cnObUUbeZMQRUSa8gxcZ7lQjks9cYUueAQzPKFRb7+dkra'
        b'INkyDVgCKgUPDEod5aBcNTooxw5JVkUx+neG4wMM/3gQaT0wHB38yZB7UcQPuXWuB/Yv38nQNj2KEYkKcBieUwObzoblxFlirvtUhTUcVEPpbIohjSOfbM330kEMD6Qd'
        b'tcOMNLcMFqcpQLechM7CNit4BubRLupaC6oUvo4gB55iGU7MToXDwWS4hUzej3GBKeAKhQUGwGJKZHEWHAVtaDA1a6kDIo3siLcOZ4fBju7guBqeFRTAAeKKA5AAo0ch'
        b'rbAdlMlUmFbYJCSuUCRjWJwATu4AR7AoOZ2ZDkZAs1SDvJ8EGsPo6+ASODX6Ohqk/aQ2m0Ls5AdAnjqwdOceWuomYxMlojVAqqsEtE5bQkq9B5TB8yqkrD44QsCywy6U'
        b'Ki/HDvZj0RuJQ6cc0DxxkNr7+LGMFcjVcIFVywmBxxrQCzoxMjURHvJRIVNBKeyh2Y+AftjMA5/Y5GBGJOYmoKF5hnjDTwbDZqPhy0A2OD0eRKVlQSiCWFC0kqDsfIl1'
        b'EuTDXLyogEIyH6zXa+wEjRF0HaoSW2Fz91gAGTizYQxAyx9kacJyb9BC1rrNoF2mQO1LFxniiDMMsuhC0CUApeqCXMAuusC0T07HBrpla4Ty0OnKRWz8AiZF6wEZ2d2w'
        b'Zh8qVR/Hr0RkGQqBx+hSm4NGfo882HQUoGiNJj6+lTIXtWTRTjAyisULADVk2Oug5a8WLwq4CZbRRWEmOE55kqbDy7AoykoN538V5FOfI9A3Ea0QOIDG8a2LMEw7P4E6'
        b'D+Ugna1Vhr4h8f6EkWg5jIKFtBertHH7eNnbYd4GOCwEVdw+WIhywxa5+TZrZTb2nrBAHb2mxK61G9OQ6oeQ/DuCEW6bF/JhErcJ9GEd6CMedrsPLpKHwgZ+GXvIEmZi'
        b'KuWoa9RAkCcogt0ZGgeEDAsvMLA5XIs6Zw2hna1HAbuQHu27Gh5HMrgt6CczSwC7wbAMSf8V6J4dY+cLK8lOFu6izaBGEc+x/t1yQuhWSgrUaiEgK+Qcz9WrQi3T6Jd/'
        b'zOP3vNjHEj6ZFUS/zNbUY9AsspmTsX6q9+Iw+mWOSMwYoLfneH63tjt554PcSUQmxP/xBES6ogTrism60cw6tKKmcNEqGwEReHh9kc0Ypyve0lq6LSYxJjM5dXm+Fr/C'
        b'CrHGiP3g4Ok5QQ9q8ZicHJYRTR59OAuz4YkxWjysEMAeUGEkB8ecDLYuhC1Y7Wkx1fDIYMDJNaawZ6Z+uhvugvY0DCOG2FOgwt7BmxD8+awJtF/n9ZAORILBIdDDaSPB'
        b'ow626kaAqniy+cfDPHAILdxoKywkTgcdifzkmLJWCNozYF9czM0+geJpVOWqb5xjggcT33Y1qNt87JjN59fin+22f/u7rza9uOGC1wdW+w9ZlhyNjRTIHiuPs/SYs9Fl'
        b'TujMrOWPafxo7Hbt8ac1z/tMPf+iZnSGlyxjU/6+r1+oqX53oq3DtMeeWPavBMsM45OHDVPcCo4Wi3wmtUz5qNbkM2mBizjMfEJuqvuivd6+nhY3PFquuojdltx6/b3Q'
        b'd4NSf/i+OG9L7Zu/Hv1xic2sk71hWbUuGb9d8Rp85mDYmWWfV1mAOof1u4bKe8oXe8vuzhs8ENP+/JqDZhdPTvkk7fjrHxqUPn6n4E3J7eQI7dAb760q3mvr9XnwyfwL'
        b'h389H/l6i8ETAbK5N68a2DR7L0i90rhsrc+tnMW1v6/TyPnUXGY65ZkWr50lMzROrv/4pcuKJ0+vXrvmO/tfnrjjlbj97uDOHsWSPQcy3txT9dU7z/65213eM/mOYOrn'
        b'HVvO/GIBdK6vPmh1btpvle5fh4bmXNtxJNnho5XPvdf55O5lwU+c3dJ77dvlLV/duH5rysatP5p+K2mbGlS0p3roxbn3nE5vuwruxW/++Qn3jLz2ju7fCjJPvO7QtrO2'
        b'/7HMxwaeyqz71mrX+zdqavc+mVk0Qz7lrYWPd13s87W7sWTP+q9fdg4FrzxRcP519zP7q770/NLzLUVZxvsLPt5QGbtrav2iZo/v3tm2OuaTC++kfvnkgUkuEzZsu6H/'
        b'Q1XL1uMv3S1+6vzPv5b+Mf185oeeJ0wOeoW/9KzNU8U/3jkaVqcdXLSsvU6nb+FZycvO7bP0TKP/cOhqEt15p/6W7dStXzwx7f3oFvfv9m6v/8L9advE4ujP5advrLh2'
        b'+qtXln0Rsezdj9p7ftwcGrvzj+Due3EjRe2//1mccOQM98XSJd5vpdv99HrVrT+9ml3O7FgqO3Xde/aLswJe919clCYKXn1zos+rjx05cN0p7anwia92+FXcUOzpv+S9'
        b'+VpUUev9x6wvl355ZNdd0byM0gt/Toi8Jb554Gfu7STXx1rabi/45amD7JSkhRvvLpC68CF9sZOr3A+MYIz2BSFZoq9qpFMnn9N2rjoY/61lM2kOkp/tRYwhaBaAWnDW'
        b'lb5dvAtc0rGVok2FgHzXw8rJ3Dpt6kmSskSXujP5gybizwQvMtQ16JAGwFFYr8JuNbYHNDlLieeKVhC4LHOwJL5U1I/KDlygHAAG+FDPVW8MqcF5bT4S9xaQDYtMQKG6'
        b'RDRXSpH9/TqggtQkxddRO0QqYvTQM9Zo2ucSRx7jdNin8uMBZYJxoYRBxSaShw4cBAPYWScOtCkZF2AnpN5t2/CJjtKTJwM0E64GkAeGachr9OQ1HRvQAgshamUuhF0O'
        b'B9ZQ1PcIFhJ4Xx14fhl21tkYRF11SoWahF4Elq1MGaUX8QwixTGdDrsUsBdeUifqAMU+pO/2aYKrCl/UM+AqLMfLn1yD0dblwBl42Zv6+I14LiUkM3ZMmD4jAu2cE6hf'
        b'S3ogJmHDKO+Puwtm/gmYwUOSnTaoglUjoZjnFdHK5GlWjUEzjXMNq/BNSkoyDHMoAU8n6IQ5sMgSNBDuHtRLQhcWdCFJ9hoNPpw6V40MJS0c06H0gA6S8yy8QStgobc3'
        b'7JdzjCZsTUjhbCNgPT3jGoS9oGWUkAKpJMOY2y0PDFEcdqFvInZsSVm+i3oMaa/nkNDSxtOPbF67WAe0JGPPF3BZisp9ioWdJkhgJ7JwnUsKfnd1KA0lDAsdyEsRoCFY'
        b'Bw3ALh8/mQjpAVdYJJRX8eHbnZE8mINd1LQc5A6gAORoY/nHHPQJnUGrFvGziwH1btQHDokLZUriChxotkQAKzJiyMhECtgV0M4zS8D6DeMiJx8EBbT+vdNA/Rgeht5w'
        b'TMVgjIYf6bdWcMJK6b4IBtBMJFjyA+mksOGgz0zF1gR7wmCHiq7JDB4mDivCYMAHTtYBOVI1bgzM20TG00rQCM/pOMKRdGUwZtQEx0nuWHI8hOlGsK8hOGvKaHiwSP24'
        b'OJ+fVWWGqB1BszqXwGk0kUxowYe3Elel6XOJpxLoMaTuQvnwkJhShQgng1rCFQKLaRh40D/fWp17AMkbFzH/QCNDeWjAqfU6aDnqUmMg2LuEMpRcM4VFhH9gWdC4yL8a'
        b'nsTpKiAwUMfHD02qAsoSYJFIveOqQZ2HGktA/qox8XlPmZCJtRUWbKDReUF9OiEKMIQDtMj5qI3OYkwGGoeouprr98q56XAQnqMLbS4YikXFGYCDasQFWhGkec1At5PS'
        b'JRcMLadsYqCMd1KDBXqYOMfOHxagoXQaaS12mMe4DTMgNaLcSbWr1weTR4pRDq1SmI9JlkEHB8/58VHoF4IhDay7wVMiHFe3gQ1EC08jXVzrTeARWYAdLNydRM43MLPz'
        b'NQ7277BIM0T3F6fP07GFpfH2qMH82PkLFOQtB3hGmx/9qKEOIM2GeoCCQkr1JbS3UDopb3VTc1NGSmuJldTs/zdoe5zrzn/PanxLmxwvE9sfEbvfw0L43zmKdaaUA0JC'
        b'QoB/S1hr4jdlx9pibycCz9dmjVgDlmOp5xOG6+v+qSvgRNz32vo2rBlrwxmxEtacIx5UfMhg+leXm4SP5znsjWWEvayQfGzOGnA4VLC5WMLhY/spgkn0yB49Z8lq3xfi'
        b'/5z2n+S/AKcqYkQkDI8ZJU/g8OHkHul4zyTcAuEOS4kfg2K5w2iLUAVDeEsrLTM6Ji0yLl5xSzM8LXNrpCJGzf3qPwgshJQWFqWdilUdes56H60l1lhNmYc74N+fsx5i'
        b'3lEnW07HCNNA0BT375QaqtAMwpqHKjXMQlitb4dW/CtEU9sTxlFFb2Hu7By3KAwao9KZMzgr97GDLbNHbUOhIJfo+4bgHJps46w/cGAmMwmcE4KiuEVSAdX4L4Hz4DBO'
        b'5ZhkNBU4kEp0H9AL+sHw+GTmwk4+mSU2JLOtq2DfJJlaDVXogiVCWAmLvGhggX5wHF6QYfdgpW0zGTUTaLfWI8GxMDURy0SYimfC/iiqjNcaHVgLlGigUSxQjpyg5lxg'
        b'8VI5LLFHglMIkpN6cWp6cxfwdle0tswUMfDiLJL5LrT5DqtH6CIPr7HZaaZ2FoLWfrE+bF1P6u4F8zfC9n2PrNUhjXTsjwfbxWsUNC1YZ6NKbC0fPQDXC0tKsQfF4Ozq'
        b'HXHTpp7UUJSg8Ta04NPNwUOJxm4mddVTO3/+YNs0/1rNMuYDU5sLwZ6vHS2/kP9OcfH8quKo1SFOep5vNRZcPmy9MsN4TVDQ9xNtLG5rf8ua1O59c2V+7P5994Y/nTL1'
        b'q0/SZaWrDGvtriYDn+srrj4Pq0/pdNb2Zr3uKXntl+o1Fk8kJz0jjCgtFr26uO2kzzMZT4Rcq3is4fUZH73WvgMMpj2bk2c1++LTO/ac2rHed63DG8LYlxuYCR99OCP8'
        b'iX2GTjW+HcWZ3x83WFqRBWbmrtO27luQ3CdNSX+vw9jpSuxrl25p3tTZHvVDRcaVO2/cfqEpYcPmp9c8HZqdNO/9y7ItSxLW777y0u6w2ubcwcs7Ay8O+Oz4dfpTL22e'
        b'1fn2j1nc8k+Gf9r0iu7QV43rnkos1z9pGrt4+cx3THNr9ymmO3zbW3PVfeTdgzfMzpXE+O84lHKwpeoZ3xi3ph4fs23e615a9cZns2Nfbx8u23f83f79laufvgq1R767'
        b'6RHscny55713V5bs2P363ZaZd7ae07w120H6WvSr7Xu/5KZ+4rblrvxExHuDq16qfy33h8/eaxyeDB0brRzWNlyHQenzlg7dbXX47b72tbvf2N8t62yZnnbG81OH7v4L'
        b'r8Zs217960vPd84re+/7SbKVWvf6Xnn99T39z6WJ7m5+IX6T6OD3HrWOYO+g99czjn31wr2T9zaZPR6dlXgPfNT/6rV7n9/ZIvxII+SV95bZNA7vv/TzBy84DTQNa846'
        b'8iJ083o7x6dDtg8u+PLctTNpqz+8A5yPXnKZ1bncKP7bCS/3ln17f0qFyNnz9ImTia+m3WwYzDIbWcO+UHj7h5uNP0X8FF369fd37so+3njtq1ueulY2+52XdDy5oSN5'
        b'7+0bkxOW9OY+J/N+SSPusagTxucdc02aZc0Nho6r/vWbvuM03fhfGqUOaRj3JvEOUneATt37CNf4UJBDxKwdYniWd8RnXOKpHz4YlBOZYD487SDn1UaQ60Q0R6sVVB4t'
        b'm+VBvcB1kNRC6bWwEzgs5OmsrhnCdgqXwXRyrUTNA0d3EJk3CDulg8GFD7WeC2EnG04kBHfYHqyUsLF0jUTxISphI4WESu7VS8BhUBgtD+DjSVhtpCgRw/0oiyylpzsS'
        b'6S+CPJJ1ElqR20NDlYIJrjeSc7AcNxUeF4Je4yVEk3FCGky1DlI2Svm66RjDKljMwez4SCqdXpqtjeFG60FvipRlNHaxsBY0LyWlSoM1C4gDPLxmJ0GayzSko+A2WwpP'
        b'Gyp4UlMMQ9DeBbpcONC2j9d+wSVdS+ofz8Crq6iD/GnYR2t6BfbHBsch7UnEcOvZJSDPnYjPkxWomlh6RvUd2Y3ZnmoTKUhg2FQCczGLtgp5SmEUSA0/Qh3YG6YjfdaW'
        b'LIeusINYQA6jcXKFvB/ouBs2w8tqWoNKZbCyIu/vB+WgEqsc7iCHB01h9qq+6ZSyLx8cQrroeBf4I/Ay7BAamcEmMkyW68FhpUy8DRxFYjESikG7K1Vgi5BUjzQA0BVF'
        b'hifWADZNJ3mboDGFFHWkNmMvjojNAtDCojU+byZpyDinBKzslxAm1IUCgOT/atgWTXrWcH6GjoNfKr4NK6aCljTUeIYmgh2oDuVUUD8Oa8yxsoibDJwATSJGrMdFw+aZ'
        b'tF2PgzYZTzKrpJiFx1C7gEbvJaTmq40MwBFwZhSqNwanF4UEfiy1S5BCUfIgSi8gHgvApzZTpe4kUq0vwiI5mUagwUAYwMJDaDrTY4V2e3BYh+imCwVUO9UBdXR0tqyA'
        b'DXjmJsYRSwLmBZYCiu9DA/CqAc8xC+pRuxLYg0MiURRlurBhHMzOEnXDZeEWpOafIgVf4LV1VKyXEw2KRZJQEWMeI7Ra608Kbg777ZWOK7NBP8OIF3FbQQ24SubgJKRp'
        b'5nkJHurZIoStO0ExmS4BkgCq0GJjBlZHfWFLGAfKYb8LJcUrXm2J5gxKBssWoEDdIjInTGQMTsC2NEwWMA3Ng3zVotiJTcbqiKFRWMhMUEr7+Owe/0lgYIy4p8lIwgRz'
        b'/UEXqYIjuCaS89nqrVI3xSA9EklcRbEkoU0rUTNdkeKEAmCBrwMfpVMgmA6rKVWeGLQHYo83F3seFsnNMF8pNfr/qOn8r+jZ1OnXrJXuJzf/rs5jiDUTMUGIoP+cAWfG'
        b'TkG6xSTWBP0gvQRpJ+aEfA1rJEZIMMf6CtaJTP4l1pyWKibPijAdGvqeQ/oKd18kQN9y+BNBoSDdhftTW4CdkcxJsBiO3mGU90RCMScWSQS6BL0i4rB+RUnexCIaXsYI'
        b'pW9ESqQtEHMP4jCItsNrNhTwQVSR/xWchNdsHMY0M7Zz/10PksPWfwkjIcWXcv6eUvNU7PuXiuOdpWKAfuoO/AtjVlJd8K9t2GG/FP26pcmDJ27pqmMZbumoowqc8NMr'
        b'8Hs78S9X/Gs/g81IKmfuW5q8h/UtXXXH51t6Yx2OsfMXcTwizjOk/rS5/4+PB9R8gN5FZXDFXjyHGULxJrHBw4+zjuXJ2AT/R3+FBhN0BboCoruZhIDa8doq2i9yHCbC'
        b'C8IYH9jwgKMVVkmJX9RyhqHcY0pSJc08caxY5XbF/XPPN7x02zPj3a5W+6f7M9ii6gyGnebMn7dw7gInjHxMS0vNSElXoEX+EpLDupF00AX74jDvhVhXW6KlpwPKQD4o'
        b'hsfg8eBAeBSeWIeEow44qKMDTsjT8emTrcTECSuma5m5DNJqQQ6xwoJ8WJjphMTWLrT9zGPmxYMe+n0uUqqvOnEMuKjFOCE5r3wJSQX0WC1zEjHg3F5mPjN/IWhPN2Dw'
        b'RgAub0TDeYqQWcAs2CgmSQTPBx1OaO+shPnMQqTml4Ja8jCSZD2dBMzWXYwz4wy6HEi6sH/XWifMYN/ELGIW7YeF9NuiWdNAD5JwUeFcGBdxBHUT6YbdoA1JwMxyeJFZ'
        b'zCwGzbCAPp8FWqajxoyfzaxkVlqCVsJPA0dAVaKCQ/tbA+POuG8CJ2mhh8L9FKgq9fOYVcyqmV7p2NM3eJ2pgmV2ejEejAc87UPeR+r0Rdip0GDmz2M8GU9wTot8vX4F'
        b'aFUIsIdMIbOaWQ3q4mjpsJ9qgUITS3b9jBfjBUbAaVI6XZeZsIcEBbjCeDPetqm0dIeWSjDkGTaCbMaH8Ul1px3QisTKOtjDMcu2MHJGvhQlQs6B2+AAutcjYlJhLuPL'
        b'+AbDYySd6QfBAOxhGTdYy/ihH3iGfD1PNxD2oLGQO5fxZ/xhPRggyWuuQQJTj4CZDoqYACYAvXqBj7JYsgX2oMI3w2EmkAmEZ1BrkWJmw2rQoYORsj3MGmZNaghtm6ZY'
        b'2K4jZLRhLxPEBM0Gx/dIVmwN0OGYYH80noN3L6e1OQqzbHVETCjKLoQJARfBGdphpeYpOlhevsKsZdaKQCP51jSC00ED5xpoYNYx68CgKclqCzjqpyPAEv5pNMnWwyPB'
        b'5GERKlm3jiYDOuVMKBO63pn67ZyKCUR5MdiKzWxgNtjDPFqNmhmTQBEa72VoVIYxYaHJtNMugJy9oIjDzdvMbGQ2IpGSlgUULl4GKzSYaTMYB8YBFDtTj4d8LRwXi/R+'
        b'FuPIOMIsWEUy3gaOwLxgPAyQUI49hoYk5HthBJqOFSiDa7CdkTEyJ1hM0rdBQk9pMFL+zuxjZjGzuFXUb6IJXABnYYUmDmrUzcxh5iC1itbAAvQaYZ+JVWHYawLpFn0k'
        b'HR9QBzqDNZjtEYw1Yz0fHpbaEYehBbBSTvwCimSOB5OxM30ZLBIwxrBOAK+YgGYaqCp7I+gld2bDevRXAA6nokc60SM+aMBgEW2p7zSSCKiKclQ9gNOAdaCFHq+dBlek'
        b'6OWtoFKGH2EZk1no/gp94pCSGY4WAlIOHKaJPGCEUihCT4BceJq6ZNXvAgOkGJnwBHmEY0yMcR4t0eSQbJKmOSkEUsWvOfL3WXTf0ZyUMQhctMD3Y8Fl9JAmaEBlBIP4'
        b'/XI4Qk/ZKkEvPISUopMkG5nmDJrAvu20HWpmraIZZINGR9JSVnw7wL4o3gtxMX35RCxuBEuObwYDtBTiHNLBIZRbvRdNpkwwg69kmhGpYjjIAQXoe3A0mLRzw1JaQzwe'
        b'qQPlcVg3mzYUUgJP427T3MpXI9yJNtN5kD+flB+elZEHjGgtImEp2ecsQmEFn78MXnEjFaGdjmsCcmS8K5m1Lvl+BjgGDpNF9SpusGZc2/PwCn2odQMZMwJYA84qn1rK'
        b'p6QP20iBNvkgrRDntwtp16RZt/Ktsi2WpLJKkspXqUiWtNrRUTkGccMgRaOFpCJFSvlR0D6JtAua06nKB1rBMN+9dWj3w2lMsydDkDxDWmbiLsq/1QTOJOBas2H8A0tp'
        b'y5jDS6QgaJcsN+WHYdEkMkjOquqcB4rIQI6H3WYoEZPlJC/N6Xxtg0Wkg7cdhK0khf5lMs2Vqv4Hp6JIIeckYDcv/BMtAFm4vXD6x9ETc0AvHQKbQRNKnlnO31+qnEj5'
        b'4DI5jZ0CTkv57kN/ajEbDJkMyunSv4b4Z60ABbBB1aygeiKqN32MNAkaJWfocOlCyudZcBX0kdsgO5W2CRyEF8kDfjDbH+d2BZ4jD2Qp5z5o1KBuaNUmsHkSqJeROSdg'
        b'TJzRzZUxdIAUoq3iGClsIP4rQMPkqnJtcAGDpM1WRR3AecNqH/6BpXRtYCxJg6fIInEVt/BDTTnpu2fSSdm7DrPjozvRGaRPafq4KVxhOTUPtGQulDl6ghr8tiXLv9+W'
        b'Qqo3A+mWFTh9kD2LnwlbaQvMSqGDohlWgNMkh1Q4jLscHlYOcVgFKki/oqGZjXtWBmtxIyBJ4yo/tpbCHLIypEdvJGlsWUDX2K3KJA65UzI21Fst5IkM1HNkaK3k20kb'
        b'TX5yptI5ERYsy+S7VNOdr+ZqWCFlSUUz7M3lsGBmkB0s8MJc4qCTA1mgb+enRKQsT3WVahMzinU69pdznc8wEfFNE5ZTLzgNVpcxZywD9QIj4p1YM/rly/u0GANG7KAb'
        b'EeF71VdCv5x50JiZyRxaqMdELF23TkC/rJ+F3e1O6otdI3wznfbSLxX6EmYKY5MpmBMRX7F4M/1yQYomo8tsT9axjIjfuXcV/fITiSFjyVxw106O0HUJ0KRfvuSFnf1O'
        b'zmcNIuL1py6kX4bqmTA2zGdpKKN9x0QR9EvjA9g7+aahxDXC7rTuNvrl6WnYWiReLmYifF/NdGOIH/MLW83QznjbSNcyYp9gUSzSD0M8yY1wHVwB1xiha0S8oVMmfXrT'
        b'bFxWGz19VNZ3LHczn56qxv+eWUEy6A7Bdx+Ll1hG6J73mct86kT+fb+CSgHH0Z5OljJQZ8kkMUngBKijYlEBPD5JhsSoq6FMJpO5EjZTl2IyHxt1QR4ZB4kbxg42RkH7'
        b'KWkCqsCllZqWEVN+1JpJq/qcKW6UQ65arhFTWiKXP+jCqKKKxONkG+/ESGMUqmITbuMBG7c04hKjYzJTscP5w4ITOmmr492w7rMKNmfK/LH/LuEi8vMNgMfHwg1RUxQQ'
        b'yOEo3rATntJxA33gPKnBRqtQ5hLjmqwZERE2i92B+sXfP067LUyoCEa5Z/pDv6DnEo3dDL6s3rz3qx+dXtzzh3bnN7o5jGRm1syIxw6WT7aq9fH0Ccyp08k7/erhk1PK'
        b'/8VOeWP98hnbrh0SaC4XNOSf1uteVJzRdKW1bag3cLZQT3956tMzXFmPHJuGYu3WCw2lGvMv5Yv9ntjeUCK58lmk1oRkwxPJE9dfKm6rjx048sVAVs1Aruk716e2f+jw'
        b'xrWOSd0uX2xIdy1Y/mfE2tZ25+DZp3+UPLE2Wf/na599+dXIG54TE4bnO8/4aEP9gns/26y5/lT2dL8f/3ztTrzl9hG/2qgVZxdGTtV/1/7bedeXVByUWxtU+bxW/tNQ'
        b'02Nup7aVfd9u9eHKosXzgwuvr/jWJji++qzNynLpW4994uJV+UV9S3j1PM1N98pbklNarZfcy732RWTr6uXrfY/LNi3+4byo48WkyFOr3x8Un0sL+dRgssvLZ0a8p311'
        b'I6TkhHDGjdn2dTs2ybMnag1Z3/zEJXZ/daN1T7yHQ9biNwdKn+p2G56/3u/1b+/+8rzZlK8tfvcu2xNt1u0H7izNjnnLKm3jN6AhM+BA1N7W9+4/XureE3cg0tk+eVFw'
        b'0/SeCe/aKaINJ1t/KHIs7b3T+NP3oGCTyBpcidv65hPveLkv/fgT3xpr5y4Hhz3fxbY+tTN0rr3baa0h+/DmHanyVkHiczklq2Leyfohaei1Wee+ct+/5SnXm1Obeu+0'
        b'vpOyMWr90rB3gM/1xaZlFlMU8pNdNvMsHrdOFV3+ptpT+6VvP4zKivLOgOnmx+QajlHzNpe+2j3r3pUVVt/X9rR/YrNmxsVZBfdfmjb4YmLPt2/98vsvk4/sDZnyh4a+'
        b'zytNdzdK9ejpcPlmAZIc2vERLBq3GozGPhaeB2f96OH5cY+1oNgdFlGgo9CLBT3mluSEe598n5wE8mqMlslxzAodWCPgkOzZTt6cOyVlFY5ThglBkXIo0Gbngvxl1P/r'
        b'OKyBJUh3apMhtbfdR4MRRrOYeWoxKdEEcA40yAPsQTfo8/a28xYyOhkcrNnlS+66O8FLcjvQBAvUI87BKhrsaDm84ILUp6soYUdUJGE6CwvWgmZyZD1BE/RlOqG9Q92p'
        b'bB04RZuhGDalYcTuBdiNgRkajK6Ig8P2ntQONQIHBPCEhpw4rqB0J7Dg7HRwiRhVtsfDJmI6Ao2wEZuPmAjqx1YculQZ/48cgsOT4Tj+H8ZYSCf/Hx89PfJ4UPyfHNXe'
        b'0lZERSaGxyVEboshJ7a/4HX275zYHmRShByJQcD+z39/KzKkPD7axE9FW2DFB6Sg4StM0LciVkICdWA2IRP+7NiANcKHYQIT9MmSBOvQJgEzxKyQExJmIBL6Av1Yk7Dh'
        b'2uQKB9uwQm/MY1P1OOWBouCWIC5hm9rR7T9pXYnK9wQn+L4Wz1rwN05o8c+5SereJ1in3AD73dQ3JaR6teEJbrZFKF4MCqMEalskzlZbuUXiE1s1yB/LI6y4WG3+RE+Q'
        b'L8xm9gv3aGNMFX+iJyQneoIDwkehqzAoQIt5kLD50fBN7HmD8udiuX8A4HwAZIj/cQ/kq+FPdl2z5QLmCSvMJR0RvxcJS8SbRApPIK2gCMcB55GBNl7ewVhnLfbWYLbB'
        b'Eue9IpvAlXG62dsFCmwtz5qt9UWEV+TzsTbHPovY9Nil8qyjxQUNOXNzW6q7Crqyp5/MctJjkl4V3Vp9Q8pR8+BhpHNk4/WzALRvx+AS0VJuAro8QwxDmS5w8KFmbTDi'
        b'iEHhdZFKqMVDDpdv6URtj4naGU6EGDI75/z92XmQ8aVBa/ZYhON4AeGYOGfUFUstZeWIZ+PUxjs3ZkQbqEa0PvrkgsWmhX9/RB9inpGoj2lX9Oa+OHgK84ZWWvjbe4Fi'
        b'nvjxAVQIRv74wVIRKASN4Pw61N7D5jqwLn5lOo0Xth20y+38XeZhByAhI5rEacM8WMtLrVMwhOwYzIa5/mhRMWQZD0cyVk6YYq1hUSrLROgG7J6sjJJtgvI+LvcFQy7+'
        b'/hhNJg7gFDNAAXmlQYgF+EX6DBLgjadqMgp8FsVtvBmsd+xIcooAx4Zjkh4nkvZNPSx+XzDFfOCccxATjxv15UVCDNdBmo2e5luhPwV9wCiw/Bx388XgtenviX7cJWAE'
        b'GuystwHJLdINJ3FzvQaS4H02ixkFll2DOud9xDEfBjE6jM6+r8hz3zuJ0Gws3yW0jLDrTPCiz/Utfv4jDQZWMhJG8vZWBZZzX/AQfvQx6jjr7jTGvGMH4Yr44EVx8Fq9'
        b'jO2H9JJDkABsz1b6/qTA+/3yHftkDrat3na2LTbYh9m4S3DH9iOyZRCQdPkPv72qXxT9jN0zaA5psty8nDskX+P6E68yTKULI2WkN3rJVzZS7lUhczyDsWVsM18lX0lW'
        b'ZRSxzPGnmM3MZo/XSek+GBgsehn9/fC5LUyuhRn5juvsLHoZDb6P8myYI4GN9NSjfT72JvdmYSXB9zihRgJFnA9sB/1xieXnhYpGtAL1lwV7BLn5v+uq27dt3jO+f2qG'
        b'aa9o+HziFdfDpie2b6hc0F3uc751ld2yoMbAuQfXHNXQ9HK4UWHp/6rHib72+Nnhn1tHLVuxYsWSA/PLkqPEzyz9RSw0rJjx2cqDp1u1jtWkfHGspjy+tPCOaP/c10N0'
        b'Y59oHnn5fPLOm74ZolSjCSF/dm/0Ouv5eoCCu7Pk7Z91TUSrHp/t7N778yyXyyH9c06GXvrQ9OLAyRcOvTwrYvUX6661Gsgd4jqd/pBf//ntzQvbLGz8k+Z9miDoCprV'
        b'ESLd89OdxeZd79tNzVHcfKyjKDrKy7+7WZ6Qqhf/br/+lxWf7nBd8/3gi4pnlr9p9y+LD2cE3rP44k66bMrN/hsrN2mtuPTxWkHPi18MmMUYzAYjgX17RJVfeTW/X6gI'
        b'rItbUPTS1y+FawR8vP23sh/8/7z+4a/bv639VGtzw4Z0j6c+L3zjreYXz948kj3HPePC5Oc/fy1t3b77E1/YfL3Rqjjz599GDq66HudnP1X+o1H9jdgJX7/8+8Semv0/'
        b'/qnx4m3jfUdk1f5XN80eGtKZ/fzHQa13IwaneQ7Pjnz3Oetvrm/yeWFWTt7B4o56QcZ6qQERLae6pcqlSICshf32NiJGtI2zTYD5RP6bC5pnI5krLlROEX1iUM4lMZQQ'
        b'FJYcIBiKEjgEjvrZMYxwLgvajSB1jbcTr8MrSTbMwqwdJRjVJQYN3AFYuo244YtgdZAizRsOZ2ToSUCpvj7s1k1Bmyk8jcRncHEeyYKDfaAMyZ5OoHdUroWn4HFipd8B'
        b'D+MzIL+wdNCOvaNz2NVBy2iozQQtmQ8sAsNriHgpCuJMQBbaC4gIftbDF5UMDNiNip72yTyd8N6pMh9w3N6el6O1dDhQAbs1qNDaBLpN0JtScBpetMeuI6IIbkaghKRq'
        b'OC1I5iDdhw1cdgyFdcjhIN2b2sDlJVgUzl8U642DUuuALg7WgY6NtBnr9oMhuTdSaBv8+EbezMWA/lQq219WwHqyr8Fz4IhqY6sCJdSl5HBGGsG6KkCjrxT13RLOBGa5'
        b'/pcm7v/E4XeMNDu61ZH9suqf7JdyiQYJAEekTglrxhqQ/RP7AGB5UsizS+IwbFj61CU8k7q8l4CYxayU2BPbgEiuQg57XAupxzV5z4iQotAQa2I21VAla2rcEiZHpm2/'
        b'JYyOTIu8pbUtJi08LS4tXt0RWvPvNIQg1RinaYJ/Gak2bJzPon+8YT87TX3Dxsd6m0DzWkITze/W0RYEMGnmJzRxh1ejODUhDZdmLF8XtiezKr4ujtiR/xrT/1AGFSHz'
        b'IH0H2rwJfAAem4dVzQJHWIB2B2+NmX6MEegXwMOgWRwXKX6eVeDFIbJH8kXEZxGf7x+I8I38MkabMH1M7hAkn5OoMX38FTMO7p6xg8zunwyyg4xeqqmq64W0o0zGuomo'
        b'y17c+P7EL+/+x/1ZoE6DQ47V0VrSmEpbjPRpGshTsW/PctcIgee1/+ed+lCRXvBApwr84+aHPCcgAWDcu/eQDouIj90a7RV5eSolyLF4S+Bl5Ps3u0zx33aZQarZ+C4z'
        b'/qsuMx7bZfjlff+4y46M6TKsTOxx9pT5qzoM9BmPdhis14jwhMOP7jGcNSbNQ0qgMFb4D/rsAR4d3F8PxuvR9icG3WCkpJ6T200x8h+VyLV2EmH1NZEFtw9JwYf2fXBw'
        b'QDtsHz0DN8OiePlUPaS2nXJMoGfAJt4sxwhPbkPLosXb67QoKUwcaIBZweAiI4EN2KiHBjA4bEief3YVFoPPyPQtI3QDJTsYYuGfEjg72B5WeTjIvLwFjGgDx1pMiDvX'
        b'+imjSEd3cyWLpj6/RALmGOR8UJ0y7UPO651DH1m+HNSRXylZNdjxjp3eatef/D46/8eBF3JsJ13TPmJbUpI70cLF16PK4enQ8ruZ70umFk579unUN6LPfVG8+OZrv126'
        b'cSxz81Cp3hNrPv0s/WevL3pfzJpdd/CPn1a8lxK28PzJqRdqo6Vi6nF5Gpz3ltkj0aTRBls3ROAUZx8OWsimPEMShY+a0Oafryb4OMJhHq62HhyWoxVuM8C2k5IATDpT'
        b'jAQQUAMuUgL58Hi5nQ28pKd+ptYPyqmbrNwDtPmAI4RKBOnDSEA5wFkZI6kGb+lhsNGNZzMBTZr8uZl3OnWhBVUTZF7k8EvozMIuUAY6PGADH18gGh/0q53GwWZ4BHRN'
        b'AlkPTEs0fR62f41OVl28viZHx4bjLfGfEI8pf4zRjs1h4jEh2cPx/m3Epk5Qm794NN8SjoMaPVBQLtUcvxOlLBlJ4uA/nsXZRuNnsd5icI2uu17eaEOljQoLPSxgjhAb'
        b'dkHPA0ukFv9XYTY+CKegUrdSM5aL5kpYcsDDjZLoxIqjBdHCHDEfWBMH2WRweE0+sKYWudYm15ok0KaIBNoU84E19ci1hFxrkUCbIhJoU8wH1jQk10bkWocE2hSRQJti'
        b'PrCmKbk2I9d6JNCmiATaFPOBNSeS60nkWp8E2hSRQJv42gCHCkW1mho9LUeMw2rGMjGG2UwpG2aI7uDDLC20hllEW6K7RtHTySGV1S1Nv8hE7Eb4m/0YvkscIdIygd6i'
        b'4S/HRR5kyVL9wNKpOuLCA5CwFPH+cKh58canpVpEhX+5iPLso79l/9uYgmNKOhpT8FEh6vAMoUEE8SdLEoqOJBG4ytMyNi7+IYHkxowsPKpVjn+qhXyaP4mXBJsMQDuZ'
        b'8ThEVoD9Oh78BC7CfDsHFikzcGA1q+kMBlMo981hpG0M6iSnBKP7yodDxBl6ySEwn0R8x5RUUZZiAWzT1Q8lJzQWaLgfh0UzI0YZZqZaU/+VQjhgowrmvhAM0HjucDCW'
        b'mhZrN4NimT4o8/Gj0SlkLGM8WwBrYH8qSVkyFdTJ5/lw8MoWhoWdDAbqF/FhtBZjT6FSXzYDVjDcVnYu6AFXyPnPTnCEkzv4+JHQJTqg1jOJg9ULZeQIFh4Cx+aTFRcW'
        b'YIYReGkljm8C6wUrQRY4R88nOhbBXjm46IUK5Y09aXDYghmCUFgGuiiVTTMsyJRTBkk/dh/sRstzP7d3kRl1x5gyV+7tZ4tucitgMTnaQKpjPrhKCjdlIryIqY4oz5Ge'
        b'J2E6yt9C6uS8GwzBoqV+6kQIs9ZQh68scBkexZxSIrt9hFIqAbZRZ4ejbphcdcdsNdIomGNInX9GrHnOJ57vCQ5vxIxRdeAsOeJKMVdSaH27IXG1Ow2PNwd7AxXM4Bmk'
        b'0Ag4RYOlTeKfjW2xvOtsyfBBu2DLfuyKVSIbJXeyhod5fqezoIa8+6S5EiWZpTdhkxlDnSDOGcIGuZ+XOuEUkgUq+JLb6qsop8BQspJzKhyeJLU2QxvXCE86NQ1eY7Qw'
        b'6VSKiLKZZTnABhmhySriaaHGU0JNAoOkrw7Om4pHClE1QLXckUND4Yxg88zpcRvvilgSdbzLrXL/saFEOEfXw7u6a8qnf1y+9f7TmmlfvnexaEKDTdCZ7Io1Wz73mBh2'
        b'x/jLxvc3FK6xcH3b7rVhYUtb1M2KN7csaA3bszk799yB9357TxL2wxV4zuzi4feS9AueFIXfmL3FOTQ7+4+vstq1l2kunHu7p/vT4Deiz7hVT8ho35iwd/ON6s9C0sJ7'
        b'zep+/z7kjYYvdc9+vXpF8fKyAzMTLYeiJs+b/crEjNBz0Hjd1xl3vpHGpH/9eMPUmsDZomkm9cEp/4+374DL+rr6f56HvREQUFFwg2xQUUBEEVCmCqiIg71ENg4QBRFB'
        b'kI3sLRvZSxmSntM2bd80adOVpknfdKdNmo63SZukffM/9/6eB0Exw/b9108q8hv3/u4943vGPcf+etim2VhPxfffcnWaVJt9P3DQ+Zsf/GH1e792/mNl6m8D6yJ2xUzq'
        b'TxZWxUynX/td4vGhf5ifO/zbmYrTh3f9s2bn3Nb3py58cGbNu9r1vok/U47aWP0TnyOlfv2ZEV7hXkFvJ+sf0f+GRaXFJx0Wpz5zP7Lf9Pebtv6rw2LTbxa+fcbhuFpf'
        b'a7X7G1Fen3S/9ZvU869+Fn5irdrl7934p+ijyNqPnPaareVAJCab+WVyoWERjMAQTp8WgNXIemzw9tlhJVxTc1dPkGDn0ZMc+zhDEW967yd4/10P8A712UGruFMIZqEM'
        b'e5Y1jAqGIdFq1jCKoPa0UOP1Lk81ftqdfxBHpAfVsBMK+EwUMI93/ikzhjku3BgODoESocrKrMSKFL9MurGz+d5pEmzAPhjlJQe2ysMEi0O6n+OH2MTYLxzsr8LHJGxY'
        b'XyiZ1LPBaea4knfEB1uE8gnlOH4Biv21/En6ieQSxCeu2vJ1S0+3gWIXuO/PRB/JiFYxlHtCMb+mkUlwjXdusjhioyPt2+R0lJ8ACsIJdn7lNKt8IhN+dIeOgxy0BxtI'
        b'+89Y08SKM7HBXyr82A1ZcjCtgLcFR9RIlg6vXypIPpEazikcoy8+u1M4HmSE1awrjiD86GqJ01YJthlF8KvJMAqF5lbQx+oNy7qQSSw3uvHBTxFgusnfzaVV9EYmr7RU'
        b'5NIhj5aND/4IB+zojqOs5A0XGYrKkjX0uhm+qoSdiwzY7FutZXKDhIYOdslhbjD0coSbDOUkxIutpcXq1JJYopWEyA5b+RBua9ga+XPxDJ1QQSJa003OA0vl0k3psg+r'
        b'EixYbosF55ZIFtcImMhQWuWWwsdaTQK7gzcP40pTZEOz0YyRc9wHk0Jns6krsEDX72G/v0wE0aLp7JGDOc8Ifks4drOaZ0o4sxRi6mjKQfcx7DNTeL4LSeVFj0GwSCNH'
        b'6w8ZsvjyaN1KlVc4EE7/KIsF/xs7g6POPWvsD6sswE7kqEokYtZbRvFfikp6/DyOKu8hs/h74c8nisraPD78VZ9RFWdqSxHk021ipKd5dJbb/F8+JCwRHrVatlzVzJZg'
        b'p2u+tC2RI/rAaOkJnmem++W7UOh/XsuNv9DMhB4wiyMstn/ZxNuuSDHqkzYkL9bvRdrtQOl8WlxM4ud0YPmbbELC8LIOLOypsPSM1Bfos3BLGFn+fLhd+HOH/fvisKYe'
        b'CWExrGVyXLrQIvug3cHFVXix3hznRJ+zA58sjmzEOyikRkXGpSelvlCfG17P7zeft9//Whxtg3Q0obHNv9U0Q+X8xaTIuOi4z9lWVghWGHc773YSlpZuIjwU8e9MIFY2'
        b'AVnb6udOQG5xAlsWJyA89OKj35LRND+y9vyxFRfH3iEjrvQlrEVUJrzg35hBZFQ4Ec1zZ6CyOANjzlX87hdv0XJLtuwyan3uwOqLA29cRt0vPPTijsscR88dWmtx6K1L'
        b'DWe28jKrefnwS0bnCu7pnBbxYk6LqFCUJ8oWZ6peEy36AcTcDyC6Ln6eA5y98lkHuPLn5NJ8xVLocnx55D85tWLvdk55l2OjeL+R9FgiuiX0lxoltO9JZ11JEpPSV+5L'
        b'/+XK3OP0SQkvc+/8x81LytzHOhaKJ3/5mpmY4xa8STAqnwFcHeh8YtlzgOuQ8Jwi7Jmys8a8k9qXRx43ROaZxjL1tvipTxJkomOi0pf0JHi6ejsbVpeIKc2RDfvlNXiO'
        b'6E9L67hnOIlY5YU0KMBxqZcE75kvAvylvU5ClYWMGCFDcV5RDeZdt/7HQzQrls1/NuuKtvTNlxzleYjmv254sBBNfPT7oXdjDofR1ibIXxeLNv1QDq9OSrd2bRgUL7Vc'
        b'sEcsllkuUPRFIZzUay+8ydafv8lpUenCMNfFT2Vh3RAvHXztC231u8tCOCy/HCoOsbbCX7DVa6FN2GsyGthe71DDO3ATJ8wk3IlxEmrJZGR0sBaHRfJaYuiBCrgnZD1N'
        b'qGvyxwJwXiRvL2aZZtvjHOI1FbjECvQVX4g5HOHDurH8ojcqNiY2xifCK8wvTPxXwwuG8YYBp97e9TsbBfvkKZFo5JHy/6RXPpOftnKuWmqUlE6EMltfZYu2qytpSjJX'
        b'PbNNwstzn96Y5UPqvNDG/HlpPtoKQz9f/PI4mlCyXrQYR/syQjiGhLDvMxLUjaXhpQnKn0Tucg9wmklaelxCgsmlsIS4yC9w5opFKykSRb9AD+5Je7w/SxToyuKSJpcM'
        b'Vz86Gxfday5OO09XCn++473QV8NNf+sVph79Lv1koSNX6eN+3Mwn1CVtVL88cq+J2es3/xqs6uPaH7/GsS7e0NGwsb7IOd5Qf8QqUlRkYxEa8q2jaPK18m+0QNN3j+sp'
        b'vS5nV2u/XvT67wxdf3bTTFlWJuW+sQvmmy8xSDVhSs4T7oHgI8AGyIUCcyxVxkdSxwj3+SrqCVb8mC7WMd9pGw5IvQjcebovjftUAuxh2Pwpb/A4FmGjlbSyzA1oVTl0'
        b'0fuJg4J5ZrfQRV41x3M9Y8cb9goioWVCAxQLmTc5LtBhTkx5BB7IixSxZG+CZBN07+JZQBvglpE3XbA4GqMokjcSw9gVmJEqqC+McynHpZ3n+8p55tBX5RkHoeYf/49l'
        b'SPPaGPJLTELZ65e21Vl5Tk90mi3davxC/PQrnRXt0sVJmOl+QUUJHmaLZAsjxywyPb5YErZOMiviTWUZnH9TUUDGbyoKkPVNZRmCfFN5EQBGyT5IkF//fofdJXJnDf1Y'
        b'xqx3NmFlibycutgo5P+qroOmmrqEhxcsoQ86FlWHgkg18RqUSmCWFGjvMxpbR/p32vWnI4aK1WuqRZGSEhZH0y3QI3DwpaOE9ASLNapFqt9SZjHCaFGUMo/KKbO3RmqU'
        b'iHmquRq9VT5SM1KLv1Vl8ZoCgVbtyFX8t6p8HmsidUokkVv4M7r8Kb3I1bdU6LoaXRexO6qV6M+aSP0SxcitvDCFgrRFiEaBZoF2waoCnQK9gjXRGpFrItfyJ9WFN9Mf'
        b'5WoV+rp1JXKR23hkVIGH7li/G80CLTZeweoC/QKDAkN6XjvSKHI9f15D+jx/ulopcgM9v52Pyp7U4k8Z0BMqPP7IntDkX7iRfSF9gyRyU+Rm/o1akbrcLDJ9U1PKEPRX'
        b'WExU6i92Pt2I8IDJ8juYDqC/03g/wqVKgQUKw9JNwlKZ8yUlIy71qR6C0QTV+f2RdCkinRl1cenL2gU+FU88kk5KJilVOtTiKGFpi/YQaadEkzCTmLhLUYnS1yalXn3q'
        b'NVZWJpfDUln3SUfHZwOWzNR66gMXldtB98ADViaHkhK3p5tkpEXxL0hOTYrM4NPduDxUK3WkRdP6PXPqYVFFM/kirV9C2x6tsHjWQe5zzzpIlfQvTq/YJfKpUK1MR1+U'
        b'fc4LRWsXV5PZYLSlS7dgRWOL7TvfrkgrkyPcGxWZRDNiXSWjrsSlpbPfXGarGi5140StgBukE5Ja28KcnrHBL8exSdKV6Ax6XVhkJJHIc+aUGEn/mYQlJyfFJdKAS71V'
        b'XwBa2BY+e5JEw0+Ayjlwn1V4f1Lf8/CivxsrscSHV+I8ftjHT1YuDBb8IrFADbvssYMHpR1soXDlF9BjR/a7CdHUS1igkg15UMDDi8Ewh91YRRD6sLxIAQuhZ7sY6/y8'
        b'hfoeBVgLTeZEaleCjEVXoBPnhYD0bIBCgCU9N4ZddiI5K5GWM/TJSbZAM9zMYH3ocQ7qUpe2qDLloXWhMZXDThw3U4AKnIeHvMjFRmhXNCdCT8MKX1EatF7hGK5BQ05U'
        b'fYVlx4f6zGxwEQkVWHNwBia9n3wYFm7f6bOsUaNIdCxJCXOgLo5Hi/djEdxJSyGLYojYBstEUATz8nEHk1+WS5uj69/9sbF76V6WGuX+2RsqwTkjehWuZ/JKvUU63/v+'
        b'Q9Xjqk2vxynnx72j+lHGntURDnr2Dfv/69OI77ueXG+29t0D+iXfW3di047vH6499fvfb41oPt3XabCvY23+nQ8eJAf3KteoB9oV+r9dtbF2oPpq7x9Or4qOSRh9WWww'
        b'0XPlrOEH7zlk2fZ4/PnC5Ypy27D1Kl0F69J8nAMfH7T+32rX3b/c9qfz2/T+EhJX9d4Pc9Ki3Fr+8upbloG/v/Oj478o/OXHcrHJTj//x5/MdDmeI/uoIJAljsOAj5gH'
        b'+dcd5TB0G4xtVPPeAYNL4nxCkO8Q1vB06mzRridhdnclFmbHQk0eJovFoYvwCLrMl4QeoSWJw1NDzCV4+iT0CNUnWOwxCFt5DMt1ly9MQdVTRxZVUKi8mAldcYRMMfci'
        b'y60wUxSp6EmgHSaVhHBh69YgLCa178e2eIci4eaJtdAld8wZu/iUFVP2m1tjEcMEilClAb0Si2SYE04u3sS8FCy2IOOxTBr4FMKeIdLeCzB4A4Z9bAg600LJbxQTweZe'
        b'FRK886DjjLRfgEgxbhdLLMfBJB4tpY99pGBuBbfSeUSOma3EXpaKIgOYkj98yEJIL5/CCptFsK8INed0JRpYjZO8KmI664jKavV5QxlOX/CXTm4V1MpBGYzhHb5fZlhw'
        b'ggXWFllcMwBz8KacL05iB0foFw9BM96OxuKlyQ9Qc0ZwKOXiXZg2t9LCzuU1DOXPWcICn4efJlTRJGmRaAy44y89byTSp1ctkAi6+2xm2PPjZysFxAKZoPsq0P6sorR/'
        b'prpYkyeOE7pkPxPM38CBvhC0yjRYrlGfjlkpLIlZMX35eblucsIdKwSp9r+QOYB6S82B5030q0QTFD7frRsqc+s+M9hi4Mp+UfU+q2uX6NUXjGTxIEvK5wVZImRTTLVg'
        b'2WZL1eC/71d+xmv3/8WvTGgp9ar4qY+RrdIz/sLscXV57gIe/47/e/eSl/Y6nfzFOTMxj8bbqaawQwbLWdHCgzNjP5Z8gQ84NYs14tz2FAmkRSSc58cdv5JzN+aFKL9x'
        b'mXOXkQ+0byVJuOjxm2Q/+PhbYqX50q/EGpn3D3LkZWcfuafXcIPmPnXH/7if95lTvTKqeWbf3vnpNyXczzv16Q+f8vO+4kJrtumhXM+2i7R/vMzvlCJUquGtZzeRbSFO'
        b'xX9pV29q9pfdyy/rw019oR0tX+bD9WQ7OgRVpl9lR2+JZTvK/bmGBzWP6GCbmYRDyiS/zcJGy2tJWNHentWm3MnriGNQLjwgb0+wY5q5ckd84+BstpgLifTff+dzXLnb'
        b'NzJn7lJXblv2l3Xl5ohf1JWbpa6mKck0fN6mfaFHl40c/ULb1LTMo/vcGZDsYFT/fHbixqOEeXeZ+bhoPEq48fj5Sb63zOQ/6X7G4PGMInNdplyWmvLPNxUvpkZFC2bZ'
        b'M4kWK1hzqVHpGamJaY4mB0wceXqzY6j060NNksLjycD8AitsZV2h4JfBRAtBsSF2iDLGX0rvQUdPWp44uWJOMOTsVImHVqsMdrwG29ZkeS8z2ByDnrZLjqspYQkMpcfF'
        b'f/oz+TR/euoXbpveC30/9A+h3w6Pjd7d2x/FPNKnXjqFI+Wjp7pumSmYbv7m91554+tvfO2oXOeFNRcMx+ty44PH6sbri5u8TgXUuY7tuvs19aY4UZX5qsunNpgppkvL'
        b'4fVADeHv/mXYvRrzhIY2Nekbn2QGMoCMY2JJNmHVMgFF98GYeGluoHmI1Go4oclR9I54nPO2hi6eW8fMDeyEHP7qY1gG895P8KuaA8ycltCStgTw+gCQq7p1WULhmawl'
        b'he/xHlYs49cvAz3fVGNHKKSUw9nY+auy8Q2RnpCBpcyrZ2SufYqdlgwgaNE+aYYUd+M+AZorOpz7JMJtT4DmfnrF5Rfi+uJlQPNzpvl8hn8Gb32R9pTl80+uyOrpz2ZS'
        b'JEXLEvP/7zn/gDDml+T8lYNGpPOnf3NHIY3hsfueVu+Fnnnpe18j/qtpv72x2LYu115OZI3yvzlwLeyOmUTobIbF0MXPtMjSFumnWWKltdgsn5niz+1BFRO4K0twF7Lb'
        b'+5UhF+dsZSGTlVXClhdWRjdEW1RXJgrpzkgRoKtEhgAPSJaOWqAm452vQpI5ok81v4gopeObCZzwplJa2KWo82Fpfs/3aTLOkColRe7VVPyKXs3wlbyaMoJlrt5IaSXw'
        b'L0WuBxbd0lHpYSxRKkxIGLmYdIm0HKvoLXvvf4rWhWekC+XInJ/cIW3BPJ4XM9LSmcdT4L209LhEIX2MWXsruiwFC3BZ0g/zR9PLV3KXLrIZm2tq2GVhueibv4C7GCE/'
        b'691U9ctgoTC4BTdhmvt1nq9VBzF3qWbNO8dPNp6EQhw3p4vdXhKR+LAI71lZ88oceq+uYSU9NJLlRfKhcfXi9E+iueNQx1XhhESiLRK5hlosXNIUBXI7lB/aCIb7+81h'
        b'3s+f3nRchA3u0XEbB8fk0oroWn5DrO8rlpoHD2jLveP3u3/Jux3Vdj75jkmOKNfowy0mMRpq397jHP/3bgtTH9G4e+P13PJ3t0duu+Vn+sve1LffitUZO1QzK7/+m6/8'
        b'xPmO9/eLvr556o2wMt2mLvvJob++8vXOoa7px17H133nnYu2zo++OZ0yM/Sm08x/OZ1+840ffsN/fXOQ/GcfiMdfVnK9tvW/71w2U+YuKV9osJEpcLxvxVP/J6FTSMGG'
        b'puRlOrwhmPm5dsCIkOXdCrOb1VjvCO9nXH8n8SbX4rY4slvqCCPVP8KcYW5BXHTtCcIq8x3SjnsilahEJwm0Eirq4zbPdqiDInNsULZayRuGI+H8He4iXhhY5v/zwQbm'
        b'AtRB4dgn9OAEPDa3huIQmSevV2LhAaUr61AzxS8brHxTSXqgksvQw19dhtrLKhjoSLR5FQNlHnXWE2fqryDZaKDl/ieu6t0kXwwLyCZ8cu8TbOBO/6x8QUH8Z/2lgvg5'
        b'06Wl5M4vLolVFlOKhQCyHQtByyeEJcYEekQoLeFtGV9z3mYuPn4wkJ3AVOVxQhadlBRo8QilXIGOtASXbrSuVGwrFaqQ2FYmsa20KLaVudhWuq68RGxfl19BbB+IjGQ5'
        b'yIlRl5cnjLBIjBD1EYJUEUmpqVFpyUmJkXGJMZ9zKpCEqWNYenqqY+iinRTKBSJTD0kmoaGBqRlRoaEW0uznS1GpPCLPQ5HPvCzsuaFHk4iwRCamU5NYFF+Wdpkelko7'
        b'YRIelnjh+bpiWazqKXi1YqTquRrk87QOWwgWSktLjorgX2ghrPKKOuRJ7ntixsXwqNQvHXdbJDFhGk+S2C/HxkXELlNm/IsSwy5GrTiDJCFjWLYOsUkJkUTWS1TjU/nE'
        b'F8NSLzwVLl7ctDQTIQXfysSf5YJejksTZkD6PTYp0sQxOiMxgsiD7pEh6tAVXySbfURYQgLtcXhUdJJU0y6ewBWIIIOlNrNYb9iK71lKQ89dycV0LUeTp/Pzn+SuysZ9'
        b'Xg6r9F3hduHPvmVplv8XPM9kBMGSAH+T3fZ7LW35vzNIzhATRkbJtkr2LiJ9gUpWTqk9FBUdlpGQniZjkcV3rbjj29NM+D9ZTP6ZyS3DLlLKZJ+STNYC/fQlkNcySKO9'
        b'VOwtQhpTP+7JCoWH/ml2JP2vkbmcJIJpo9U84LgzDOvULqWIRTgKBWIsFGHTRiw3E/N8xT14ZzXzmxHGqYIZCZSK3Rw3Z7A8IbiLHVhBDx7DQqUUBolMrSxNsdB6xxFf'
        b'IfSbjGPpJ4QQKun3IRXoxOkQ3q+TFO0Izqtdwim6k7vjTphiKZZamB72hdHjDGGd5E/LmjniwiGodFeFFj8ova4K/ZhPM3usgcVON3hLSKjEkVOyUPIVKOHRZMGYYaFk'
        b'IV4YcU4Z2uEO3Oaoa+SUuujafvqSo6EJs4czRTwODFU4c5FhlMU4sHAM0MLMEkYx30tBtM9cERvOnuaLI8Y8yDfHgi1YqSgSrxJBC60qf/mjVUqil5KMRCKTUJ+67euF'
        b'uhkqe+RFepJVDOclbL62Vfjlw80SkWkcq9kYapFts1vEA8xroAEL8L6EHcFIF6lZn+Q1lPj99noqon/oEK4JDfX58HqoiGcoY/GW1Vhs6eUbAI3QfJhVizU/Qh9w15yh'
        b'1cWPYWtt4eVjdcRyhyI9Y6aestFW8CI90nV6BuveNSOwBX2BUv+RmaKIzMFHKtCBrXDf9JSHmbJwarpZWX8xvAe5cJOH+A5hoZDv2ntiCz/eLIKbUex8M+GoHE520Kdr'
        b'xeEeO92sn8rON0fjHA/XK+IC9D054AzzBvIidXbA+T4M8CQAf5oSOyUunDDGNkt2yNgaK4UzxgPHWKIiOyx4bpdwXJCfMYZx4cz1mhsb+QljVTtLsXDAWI2eZDV35HfF'
        b'mUtPAOLMjmePF+Ocspka5yUVvb18vQkpxl9lB+MTvIXK6YP66dJz8QRm52VJkvF4h39Yyg1sNPcibJr71MH4JKwWzoPnYbMnOxkvWh8kHIyHPLHQcGUIitbwg/Gi1au5'
        b'D6vHXjhvXWqjLz0Wr5nFDj9KsB7vQadQU37MFB/IzsUTBS8Ix0P5wXjshDphwZqgOVFIvYQ2GFhMv4RhF+F61VVWx4afDsUHtrLUTngMxUJ2xRxUnxF8ibFQJJx35Oet'
        b'LaBHWJX78Oi44FuA+xoy90IulKVzSnAzwyKWnXGcMLlclFgtygkeYJtAXKOXoD2AbK7yoKOWWicUWSFEaMGqC/ycu99ueVGTqWA4/WqdqvT8+TBOGdEnV/nLs7YoDRJ1'
        b'1nlnepOZqlApYBzKd6dppmbgqDqOHoVcLSjC6XTah3i5I2lmGVvYqKV4/6Jwjzs8ptv4PWk4kcFcJt1y2CxW5UfSMQdysHXxbXTb5fQUlVQNTUWRqZw81nvgzWvYIexE'
        b'HVkW93E8AyfSUtRTIGcdlGilZsiJdI3kHCzo1cwpm4o5umkpGar8VTDqoIWTKjhKF+mBEtkM9p9TVMD+nbzFBt7CfO3FJ/AmjMnu0o2SO4Bdq4XD/I+OmS7etDjDDU7X'
        b'YUh+G5k4/KYjWAG5i3cZwxStSipO0ATd5RyPYbmweo+h4PSTV+EYPvRJVxRpK0pwKBFzeKkvzUO4oIZTRF6302k26ioaZCpoXJfAOM5c4Rtuq5tFe3r06FHLpFBFkQI+'
        b'EkNFTBAvYybZCJUBvlgRgCXiNLwXACWsimSDmN43CxN8DtuhGe6xAQpw9KkBIB+LBLEzr4iVaTilRVck2lrYLd7hsT+Duaiyt3tiMclGb2tfH/8gpp2OSw16CyYl7x7x'
        b'wSKSGHAzSCUN6tPcoVlgzCHsC/DGcmdWnVvsKMLqJCzgMw7whFocPwx1/iQ6vC2Jz/zkRaugSQ5qPHGOy2xjp3UiU5N40s+hzvuzNgiCfMO2HSJDyz72y4N/MjknEnon'
        b'iP6xX/qDqauZPOd8KIF70AUD9OPVDOwRXcWpDdw5cD6FWHCA1HymKnSJMtfBOG8o5RAOJTwFimymKzh9mQssZSxlRShErFRQA+n4OGWFuL6X/iJKayYl07Pr7YsBTkm6'
        b'B7Rb3h7Ptv7vn/oZORX8z/W/qJZLjv9GyeSQnJ6Kxo9MD8Z8e+zVvo75bfqvdx8e6T3e+fC9f9j+U/HrZW2ugddmf2eysf0Hr3z3lb//8f33X32Q2FNdMuHj7le0reB3'
        b'F/+or/M4YFOqz/3Eklfj0STL6lvX/hS3xf+lV1xiHQbNX/f7qPIb/1jtfWno15HpP36noWOD7zfyDSczxpMfJY592Kt3M/SqroIfvjODO/82vm79u68Gjjh1vq9YFzOq'
        b'XOeg+9N2/ZnmT973/83vUqyqTW9WFmm/bmFW63i0Mk/+09+Unvvez5tfDjOeKdR7NSzc89Y9Wwff1SOnjVZf3Opt+3enra92/ypc/FF43IV93QZ/u/3z11VSEh4apb5X'
        b'5ZNz1sPx9Yz1vt/43oH84WNpP/vxW65zzZd67IZ/v+eP+t79J1Rt7GwcHfsT3X9StGHHy5lvi3cHfNhR9gOL2p26v7L2melaH3nk9SxX7cGdutZvxOarDCidGD41H/9h'
        b'w4/eO5H0518Oxnzw83QDu5wHric2XijPKPxN8t93v7Iu6JtvDf741cip17zvDb4V8NPNJu0ffr/1rV+dm5z+68PW8q+VZBx65/B//flrL13/zmfFn+oP+/32zU//7vW3'
        b'nwbaVv3qvav5csX/6Ho4YPTGyXO/rav6mcnLnW1jSQkfRFcphWYkfJBzsryxu7rgTfGvnBoz9l/ZlRR/47eR3/vGiSO1jz96bSrIvr29+N2mUfEnY93/+njig7r1Ka/l'
        b'/v6vn70xd33v3ydbj27o+9Yr7R/3OPX0/uL0S5rFZ1f/RTEp9cyP/3oq//cboq+qffbp3I+2//y3638+3x/xB/hlLhzadunNd/b98PtvZQZ+GP7BvhMan1565dAfG+98'
        b'J+TH1ztO11nF/PVT52/+2mVXS/2b399w7v3xsJyiG0FJHxl/9FrxrIORvtK2dX9+d/3Hxp+JchPU+k69YmbLU40STLDf3C/22rKotc4ROWjLAKF+J0xAp6GANfxhjGON'
        b'InwsuG+Kdx7k/m9/unwD7iqK1I5JCCjaCqcIajbteIJgHkA5RzAbFNMZsrwAw9dxnMHQUdYSvfCI0K/viG+K1EfljSPBMKAEI/RcmxBkb4fcWNKX0IxzbJ5Q6s9ntQoL'
        b'5OCuGdwTXF7zBEXzloStcCJA5vKCMRse2doroaH8LVjfGZJYhvBASaSGjyU4bQ81wtQ7Sbc2SjPigjzpu1hGnKYRd/urkUAsg2L/DGhgaVzLc7jOQreQYXbHaqPMq9bo'
        b'xzPMGoXqr1Ac5bCYYAYPJI5m9lh9TkgwK81gpWGW+tNU8YHMpWZqLCz6XRw/CANeS2qZxVhugpvbhWqrNUehztyP1lJRJA+lljvF0Jdkwz/K3BYfPMmY65WQlJuycMFC'
        b'/lZjLA5f4qfDiUDmp4NSe/7WAEkIK8QqK8KKvTC3WUVX6HZgBe3e5jBEcyUYcVVCKPbOFmzFeR4IDLwIQ7zpAO0vNEUtVqVVh8dCs+feEJ1F32Y9dnHnZosp922mYi70'
        b'eAso+SJMyxIE9+ICn9MWLLBmRc6tlURRmC+BDnEQtlgJiZAT27OE0wLyzkr8ZMvNUzwzLgVv02ws1uJNArCM+Ip8LQiiWMvhvVh8yEdVgGroXwxdwqAuYT8WuvTN4K+2'
        b'x8ceAly8HMvLKHVBqbAtJWQ+NS4ibyi9wqB3JFYJ2YxdWI2jS7B3fooUe4+H8q/R9NVaBN4JZG+x6j4PhboWMAi92CYt7zNDFt4T7H0Fa4X90d/Msbcd1MvAN5Rv5v2B'
        b'TaA7SIa+12DZs+g7DW8J9eweX3JnLzH3UeBRWRoCc+SSCLQN8q3K2g1NrPSttT8r3kew4M6FHZi/Op0h/FVZaVIIlnmaYSqtFJzUwBGxHdwUW2CHgsoOofnFBXzs5C2s'
        b'+14PC4biGyRQFI59QqWXSRGrosj7YhATD6y1Fjqnr/OQh+bdNsIy3zq6g9dG3oWPnYkrRErYLlFWgDzeysIExqBB0N1YYybKhPIE4RxWlfwJc79g7FtSKVWku1kOS0/T'
        b'1zHWi0+CEaFWiZUvzidhkZevFY2MdfLQREB8kC+RSroOv8ffgvAIFnpiK0kWg13y+1U280o5+BgfYoPwGkIveUtrvEurVUZr8zetNYNeVtAQi9hO7PJkRYpLJEjE3SkI'
        b'oFIyWYS6PXcsaLn9JCdg3CgjWwjcz0vipKmx12hIWXas3LGYTCFw3xEnxnGtS1ySXoU+iUgF+yRERmPQzt9+BcfX0S5YmpnCA2NGMDESulYVbab9758Xesq9rfuffuPn'
        b'JACERUYuSwCQsEDvV3P7ByvyYsYSXt6Y/aQv1pRo87xUPaFICyvNwjNSWfFjQ7GORHMxZ1VZIqH7WdtlIVeVfpIoipf9+Ye8mrx42Z9/yL+vaKzM3ye0+hC898r0nzov'
        b'DCPPmjZ/pKiuKGaFloW5aNKsdMSaPCQhtABZy8u8aPK8WU2xhM9Tk8/4mVDskmWSBi1UhMjDYkAg1YNFIxZDAameywMZ//6pMjMlYbAnb+fD8hGtFifAIyHe9NPgC0ZC'
        b'fmTzeSHpJetgJvemsiwS/ORQXoS86Mn/FEVPhz5YcEMIf6hIwx9iHgBh4Q8JP6IltyT0IV+omCfKVshUZXFqaehDgYc+5K8rPMmv+AXrlvWMNzIoWZqwuzzywWMAYVIf'
        b'9mIo+/nxBNkdyw/kpEvd8UteYSH1ykeEJa7oqg1nURcT3j6HuVWfH2N5kfADC+isOOoO2fR2mPBDN9xTLJuH4PcXpsSCODT1RMHXvrLr38QtKTLKfq9JeFgq91ULH5wa'
        b'lZwalRbF3/3VQvR8AaWRmqcL9awUYqHXr1xYQurAl4UvWMTgizzcX9WfvXIrG2O/DHYoNRF64Zb3kxbaxxZj9KT/Hz2b/VZqpoLDhFDaM2zp6XBvmFjq6D3MPJ9Y6B/A'
        b'PL5r1AWfr5cC6eceFYJMnWszBL19a4u5NKxfR8PcO2/BjfnAbaz/yEN3Le1Q9Z7tPkL/kUfX/xCgkZwi57KK9x8JshDSU1tgbIc59DLgXIhlAcxB6+vDle9JBqjTYdZn'
        b'h5cF9Aeu5JeQC9LAboKog9xPvM1Mk/Va3g1zrNcytG8UTpM3Xfkk/ZbIRF5kExr1xt5hM8Gj8Ea9ayC/bH09RG+V6KFYFJoTf8Xls0vCZY8OV37V0uWC+IcS01BFk1Cn'
        b'GttrgkP6KHbuZ+25pzaz7tzQmiLkTpcnsa6gTw5wYaGlly9WMUezNUzjAyw5ckz6FdyCOXbYy8JLgIU4jWUaXnRLX4Y9gwKlUXjvC9ItFlMtdE3ir2CZmdB9KQUWZAV7'
        b'YUxehpmE2vKhOMl9goes4P5iuVLukvXAx1lb1LlHaD8WRj7X+W26+BTkwmMVB2zODtQUvPm8t+XDG6zpY6/YWuq/cY0XVtFd7sThP8vFikWuOZl1CWneqSpMUTAvvpkC'
        b'X9Eo7xjm0oFGfCy6Krq66ZBwgK2FZSEwYOjpKcok4iu0EZqEN2CpjbmSaL0m6+O4bTO/2fs660NLmwPjojhRHE1wVCgd2pYSzAAww2WKoW4i+d1iGHYM4b5cyAu97m3l'
        b'5QH3FkvTcVdtIDQLzz4KYb1HOewOxy6h7uipgLjaM6MKaS2kCmcfXN9Xvi9N94D67a6358vm/+cne2u1deP7J2z0qgPTt7gfj+zdqfeRT1Ga10U89i33l9xVvzO/AGXv'
        b'9HSWfmTTcnEi0/jI8JYP124qWpec9b+hh+/bv/sXJ6/xbPNtb4ovffdfx73iIn/a+EGeT+fvU35yd81A/WuvH6o1/VfZP7+ZcX6yas1s4C8P952/KLpdV/Fqe0KE5Ocv'
        b'Of1DcjJZ7W7WW48N3nLZ9+vqsiDD4l+bGu4e7fzl+YmPLm97451e9TUhf3X83bDe+73h8eeyxIMzJ76r5D35h9Jt/fsHEuO+80FbSINp1d8Sys52vT1Z87ZD1bbCk8a1'
        b'dlEZ12Muufy6yTyjL9B3/H7jxxX/6gyx8lhw8fub5JzdX+xC3JIObvzV2eB585+a/bRw/5ndv7sZf9pl7ds96i3ejsG5fp8MBmZ1NuxZbxJn/LJaxo3IVTG/nLh/oHyv'
        b'wZmP1r79md67G00imn4Ql5nn3jZ+NOUbQ/npjUfTfId3JyY5tv3P3yIGis65m52xfqPT8TcXTn//vZeNMsIT3tDa4+H9sXFzb2vx6u81rjays6wteHfnH/tf/eeufxhb'
        b'9ynXrv7uBTN9bmY5E9OMCebqjWNCNq0WNnFIHQ4313svRnSYodofBe2+btyCk+yHKZlHAptheEkWjgeWCobwY3tsfFJyIYEw+6ZQqOfDRsADA27OYhGMCaUabLFAcCYs'
        b'YI0e9zNgVYJwki0Ki7jhh5UaWLhiEy55MkpqcHgjjgsJQGstpP0RvaFJaJEYuI8bW7q7t/EWiaw/oi3OSFskwqhwMBBaz2GBtAPiWgNpr5jCs9yK9oYHUM16sCz2dcEK'
        b'aIYq3yTBimuEKnhsThPiVrrKeskJCyhPhpvCixd0ccbccrFKPM3MEluuctvH7Opmsoq49R59ean9HuouuH+ao6CV29m3yQbu9ZE6Z7R2y52BGexPF3pAwBQU04eVc1ON'
        b'GcVeTFGYK4rWQSPZmkfOCkZYNfRBH3sDbyypaCTBaif5wCw+kRj9PYKhpwDzyyzKSGvhEN7kuuNpGxdNyqX2JNZoCvZuO83iocyiNHZgmktqUOIYVPBdhEeX8eaS9gfL'
        b'rElDGAwNhYdCFdgCUyPBphMMut1kQY9hztV/szXN/0f7TX1pngU34PqZ6P9qBtwN0Wl1bjipSjshKktNJENuztFv5OiKhP2kLe2LKPzNetuwvjaseqYqN7JkZp02N6rU'
        b'edcbds5JMLtU+f/r83F0+P9nrnv6+MWS75FaWoqCeeOzaPIwO2OJafWfN8DllwxmtTgiN62O0YXdhAXT2Lnzr2ha5YheWWZcfd63y3LcdrKJ7JKsYFgxQMrBKIM/whkU'
        b'adF5CTeu5Jh5Fa2+aErJfylT6sBKyb8yU+pJ5fnFXF6eAvwfTlYXnpHVcBGeW6HgopWJm5AgxKfynMQnntvO7C269UiA/57dNrbMvrkYls7SW9LSU+MSY547BaF4zJNk'
        b'n6fL3gnXX+jMjLL0zEzhedaf7IuwZij0SzN7MU/Fg4ejWXUBmBFC5QpbFwPlB6yEAvN9dL1ksYC8SJlGqWORcn0QWrN77deRxeINIpdE4iE/Oy74tURJWi7ddOm7hy2L'
        b'RjXARu/Qn843abu9Jiq01fZ+SaSn775pY6Rps6LDKz94Wf+jbkOzH739g6w/7PyW/7fOtH33VrjKj8697JAX98bmn7386+M/+8bXX7p693c5ke1Ov0jR/pXvfO/Z6Ll4'
        b'vfFss5qhoRJtm0//8cPWsxHmQ+EfZv/qYrz1D05fzl34TJS4efPPTl42UxAc9PVb9hGEcCBYvljIu0xQmlAbj71Ls3kP72TJvJBzRlBtI1iNc0siG3uhTgYjMG8nd3Qm'
        b'metz9Qi3zjzl38ZxK67t915m3QS521xyScS85hfw8bLTNv+WwlgizzUzOKstk+h+LyLRb4g8ZOdyhN62MqnOZHfm+qckz/JRl8vd5WJoidz9ahWgSajy53cul6xcqDL/'
        b'TZe6rIHLVxWqOaK3Ny0Vq5//cazcaWZcMnO9/EdPysqO9fU9m4ObGhEbd0laNkdaqXVZoZ4V5Kab4NFIuMpdIHEXkxOimBMnKnLjc2Ws9KOeLhxDv/4yHT5EK0opeb8M'
        b'lv+PuVATIoSklhmlKdi9LCkr3EA5DqchN678pVwxPybu8xctVsPz1EtvfG2ifPRwxy2zj20VvqUTERudEG4RlhgdG+7DTweLRD3NyiniV8zkOZo9iyVW0hAXthgLDD8P'
        b'fQJomz2oIVgNOJmwWAJjnQbnZW2cTIKHhOGfzd338Ulnx7axPNb6SRAV6skyXSGQyqOocZIvbBimHSZsroy60jjH7nkxjo1i/LpYhHLR5frUCMsLjQcu58nlJ3af3MHZ'
        b'7AT99I1/g83ml55v/sJ5smoMCn5+gR5+ZhI/4T/tLyjt9qQCBTvdyw/78eNVPLWfe7U5/uLygn+NsBRr/6/x9lcR4al76Uc7NekJCmWJvBphXeNnSrVpqUuUxXpaymJN'
        b'VVWx/lploaP5Z/ISkVB24TPTGyJlHbFVoo7YxFhZaAeFIzFmMHn62fPkEpHpdoVLOjiY8VcJC8TjoBsZjpX7krDRRhtu4zTOrnbYDTkROKzoiIVQAZXKZMM1401jDSjH'
        b'fGgj07Pq0CHoUINKKBKvw8cwjY81oN4RJ6AUxsJgEvsCNSQ4BHk4vM8ZHsPIYXjsSXeVYdFVmCaj74HVNbjvA0PO13Aee5RwBPrpz8wu6IL72B2TYrcV620xB9sToYXU'
        b'aR+OYeO1fVAM3XgHRg08U5z99aF4M+a4ZcfbYwnx+3ScM96+4LnWOGyth6O3QrBdlpU/3A82soQqnHSGR9gD41CeCP2sPAxMHYapvRd3YJndebyrgd2ROKLLikBCJXbQ'
        b'n1msCXXDhqP28VASgYOKzKDF20kwihXYEoCDMHL5InbC42yYxdpAqFiDHRdCsAY6HVbj0GGYtYG79O0VULrqEAwHQN52b5rAFDbsgeFsluZZLyZh2IA3sZpwWQOWxUIv'
        b'NkDH5Q1yamQTT2CrnQXex6nYParOOAkFEUaQ43kRbkXSa2t9Yc4swiPJ2ANL4/AxNnrhvWBDnDOBwSsH8CGZpM04sk8R6o6ZBbHKQHAP8lW3BeK4IbZjB/1r2hcKoOkU'
        b'rcc9qLXA6T0uW/dt0dPFsRP0i6as7SHmWI/92rpYgOUwGZhGv63QVN2EC/REP47CMM1ohBClfZQT1p+BRjuY08FWzXBfKI1Jd8Gc41i7AYrP71bGBXhopAsPE2BhHdyO'
        b'occfJJMFXmdrhB2Rm06c3meNVUQKD6E7LYyorgYbAtXXnMlMdMrCCaOz66HBDzrWhOAwLVEt9irTx0wQSTVghyveVYYCd5yxoZ2sgYG99JUPaH7TkHeKNqHMcj9RRNEV'
        b'GDNYxzJpaDfbNK/L4Rze8dyipZBxV8LaNRkrQvPxA1BKVK8Oczi++porbW+PO+RsgCass1TfiUO0QaPQIucO3RFhm82gPFYeik1uWEPXnozMWC0GMKGDAGU73k0OPQnz'
        b'q09Bgys0wCh0Ql4YNu3AWvNt+BBnYFoORlSweh1OhSkkYzNMBAVf3o+N2QEJMICNtAzzpvQNRCA4mOjtRK9oMYJGzD16it5deQpqHaAOCsKJ83Ile32xEkYs6Z4x7IX+'
        b'7JBsXe1TN8J3esZg06qrO1fhIH1oMVFyHjHFzV3EVXc8jX22XN1GtFZGGuyBLdH4ANEmKb4wrEyAOfomd5yFO0rY5YKVWdCa4X0gDge3Y4Ep2RUL1xysbsDtcyoB8NBw'
        b'Ays1hj2r9sgn4UIojkmw/Ip+mDvegnFVuHv9MNRhrpEnlAZDDuZHakEr9PoHBNlF6Gxbg30HPFX1dKxsFNbZBxEHNftgYQBtbh32G0IhiZScMOzeTbs4CzcxXw4r/aAC'
        b'R02wyQ+LTmE/jMuvIsIrMoAO+gwmlfLP27GVhUJ8ABOXr6yBkg003iDRU+8VIoWCzFXKxArj0YTpH12z04MqWsNbtDcjJLUmlWM0vbB1DSGFttMncICYLh+njc/CvK83'
        b'LECPyhaoTCN50A2399rBwygcv4h3TsG81Vrm6jvjD9PriOIGsOQ4VHp7rTpzGSdpyG6ihZYQyCX+WaAvy7XDAd3tAVtW+0MurflkMHYl0Or1+sOYGT5UgLrwLdCOvQYZ'
        b'rxNB7of8/USQ+6CMESRN/JE5TGTsxaYz8vTWNryVGAZtKWrElLW7jlpAt3aoN/S5wF2couWaw9p1REiPoYi+bQyGj8DtEHbWYBPOH3Zx2Yd1XnA/UlsV84lgu4ikpuHW'
        b'ZmgwuUQUXCtxgbmrot1WR7DqQro57ds4dBNgKoIZ4ptKYrjG8JCziSQ5OiywMZ7We5aVPSgiUu2H+1CD1WfcSSgumBucTD97Dtp8aYadWI4TpsQaFfs32V3Bu3oq8Ggp'
        b'wRJ71BxdQ/OYvIx5lio3YCKRy8tqzatQT4Ky+4DP7syNETDil3VNX+6cJxQbQG40fdgCvaCbpFLebhci3zqli1ACPeehipX/6jPRgKo9WH8Y2tLpllxkX9KKLaSReiBH'
        b'S4J5+0h+dK1Wguk9OGO4jahhDGbs8LHeZbyfuPqqfGwC5sA9YtfbWK1FC8Uy1LpxDsaP0l52rMKi4PWxRGx5OOpKSnMO585sJ700FHzFiIi3/eI+LA8l7VVrBn1kAMJd'
        b'K9qKjgN2JODuEFmS1jyz88IurDAlCzT7oGYmTTAPcoiUO2Dc1sQ0MgzGSdpMq+thFc5gnjoWekCLXSDRA7RfpQncwTJTmIR2GICyTOxQWreFFnkWOz2CreExNql67KAP'
        b'vk3SsY1UduMhGPeMOU4bOQ4304I1SDdgPanDVpjNxOJLUHdWKQpr9kV7WnGFXuadTtrmdgYJhXK6p8bZ0+AU1kLjBSiSXDKEJqJuWkOibmg5HU/zXCDbf2uSlwfeSdTA'
        b'iqiTSuvP4eBaqGW0ZU0M3eGxCiaNOFknY40Zk7OJHFzM4bA5TondN4RCmxLWH1cVC4dmSolj6qA8HcZEJGu3rMYcW1rgOqMsHFKCGeiM8jSFBjcY0CVF0LCGHbjRxCal'
        b'i0bxRDQNWsSJdXZm+DjI6jA0HsvCaiO467XBgXTAtCqtzWMsVjoKfaGMV8LEyWcYEGpOxGGcPXuSxAWTvg9IDhD6SNoNjbqu5sd1cDgYKkIPwU13mNHGNs8bIbQsbQ5Z'
        b'unA3wCcY+rbixI31bqEkN/ppPwYu0poMQGPIVTHWeNjDo0CbLE03MoMaoc4lglTyTdrkDsNVtNa3sVMOFlZhZZCB9lrSeUV6UH7WJyyQlUq0P+aYQCxcdQqqrCDPR89a'
        b'D3sT4IErsV5hPFRvw5tuYsxROAozkQfhnkccjLv4wSwUHtzr5n59LdYT7ZNU7KLxCkQXSf534KgitBET3NEnZhmjpSrDJjuYh7triEebtsJsNk6luBDN1pGWK8Ua5xTs'
        b'OEDyJCfy2BW47ZlE9N+WDTXZq4mqJrfAQuRV7IsxxDoSge0kJ4qcsOTkqt1IFF+OnZ6Ei4imu0wcaBrN9NN9V4crntqkFA+thfEAIsRpmLi6k5h+Hvvd8C7L0COV1+qw'
        b'geGxVLgbbbKdkSJW6O3nwqCDZpoDLXFQE74q85IvNtEoE8RYtVDJMsH7CA7kSaA0g9b+7pos+sJG0p8DpDbTTkG7FbZgp6G/RgBpip54fWyPwntHaIu7cfYMNIfSFIdc'
        b'YIjYuHAv3ELG5/NYE0SvKDgXe4npIMy9uAbHk0m+jGH+Fo/Tqjiyztbj2PpN/hnlLH/E1piomua/CB/M8aH4IpYSfNi3xxymbWDkktr2vUqpBF7rPE5g5UH6Dmg7QBs8'
        b'T8OOp9IKTTEBdGoT3LbHPNswaKZxi2AkOWuf+gZvmMfhcGyle4ZIdtTeMIYc8xO02w/l97CIFDzasXs/DpwlbHYPH0URtCxlWZWknSeRZFreDUus1iGaLTx4Ftq8sOa4'
        b'K6nV8ihXqA/aQXijE2YdabRSQiJtMKdFjN0M7drYdxhKba9gpaavccxFEnS5SsQdLVmq52Fkq+MhH8N9GkRgD+CepuV6eVqwZlWdvThhvE1ZzgNvbqQ1zNlKRN+1ah1p'
        b'91J65+AZzDsL1QeAxJILKUCSTIQOcOY8NmGLUwpJq3vQQ3qkkyD+CG2R+KjlCSjemkg6uhEe+GPeaew44whFPha+tGx5cMctfp2/5zGGX4rOXofucDO8GQE5ulkmWEua'
        b'qiIEp1KJbGqO4UAoFlraQK2EaKzVBwsOEGUtkEgfjDlLxkg5ie07awxpiSdCscoJC6A1aQ8tfa8d3HYhgunECttgvejde/3DoTMUHyadIZnc5qSlutXeQW+NvRkJ9Al1'
        b'vKN7yG876cGFrdAURG+t1CCqenwRio4Th8ydIBaZOQNt26BbLxJHE2nQRvrU5nPECF0hUatJ/FTCoBUMq9GCFmFtDNwxhrGzyecM9kN/At00CPXRJCDq5eJpZjkBRO8T'
        b'9lC2D+a3k7Z9hLdu6OFjUQKLaNZYQl7GT5gpl7t/B6PK3EROlPNElFdwIAp7ryoT6MnTzaI1zN22ntDthJGNDlZpE4w8eTzzMJTfMN6alQG3wwyPnlc/Tur7PvsDebtI'
        b'7teQHKHH9jHQdE1bAx5cob2dwdYT+9VIVU7BglYodmF9PKnaHgXMycB7gVEwn5VIlxrDzxKOGeLQAQg6zMJ8HFH/eLgh5qcaY5cpEUYH8c5AYCJWXDMh0dDEoG4sTaDw'
        b'nONFQzV6ooLERg0tRrFvMMG8/uyA7JOxVzap+yGh1fvYtYkEd88ZlyuatLbFwPi2HB4mJrvowJRWOrFJbirBifJTfvYqW3Ak3A9vQk0A3TIFt5SwXyMKC4+xVqH064Jk'
        b'aNAiC+UWtFzBsfNEqyPW6uZeJJvq47Q94q+6kM3UsZ54dJgkTfE6U3lay3s2hDXLDfSgOtHE2J2Y9cF6fORJQquEzJIJUscziSzpHytTtmL3ZrJr+/FWNjSYWpLse6hE'
        b'g+Vht71nlP2VjWeiic1ziR3yMogTGlSh0hZLL9hjo89WYoZx3VVp4ST75rD/NPafJb7p3Eg02ORAeGXaHgrwYXIi3E8n47uQjGQDGz2SlbX7VcjcLsBxp8008/JYKCHM'
        b'oIC9QaQsC4laq1wu4GTQGsyXh2ocjqKhm4naGkSbL+9LPp2mf5S2eHQTO/bWDBWR6dDkcgWKNuMdhTNYHA/1znTvGEwQ5KzFOydITxQTMGnS89GEVq9tN/yJQh/gUGZw'
        b'AgHF2gAXdwdmlQ3sha4DqTvO0LQmocwXRrPi9KJJCNVrEYFPWOL9Y9c8scpjBxHFkMEmzLX2iQ9iTRsWzBT5aSI1bDNyhiLvIwoisTVr5FtEiIW3S8BurFFY5b14wImk'
        b'Wolw9LAE7h+muTV5m0tEYlcR1u88zS84kQorVoIcVkxDvJ9+T8KDX4iPIfazZ957sUjsJcLG1TgrbX9CeuIedChgsYWYZ1G17Dqd4SnHcgcGaPOaSR2VEGc0uKrTqg9f'
        b'VzUOUYEap+NaYbqsUa4V0UMHrdM9Bte34a0jHr5wO95F34zEzTR2rckk3dQOLUe0D4SQBC+HpnAsI7xCLIytu5m7hazuiitWGW7Qr89QXjZ0RYVhgRq0p4YR31TBggvk'
        b'nDyG9/xY3wuC2q2Y704/dkIPKwFSEKRDAK7Rmjas2e70FiK93PVkDIzuCKb3lon8acz8KBKrw6R/q2inybyJuwa3rUi3VgRC+TayE8aIHk4TfqnYRmJuECr3kpmUn37e'
        b'Fx57sywzUhTFRFZjRmQy5ZFZVrjX7BoU2BN4myExMUIaoQ1GNhIY7oX6PVF7LslhmVKUFtYdvgB9u/FhqrkxPjqHA6ePrIY+pWsZUb6p50mCVkCnCvMYQJ3RGsylhR0g'
        b'aZRL0rH7zGl6111az5pgvXji2kc0hfJd9Knd+9aqnlTHlohQbnQ1yGGeHRkxObQqg0hydMEO7srhSPAOfzvMP0VSrd0JR7YR5/TYmwM7ntEH5U6sDz19T06qQYY8Kafy'
        b'NPqGTpg/FEJgsgqKdkCLEj6Iw/LDcG8/tgWRPXWXDJd5pdVYHLoxwsxtHT5QhnuhcC+V2GTeTDMD+yJSU4lOu7EyW4Ome2f3iVNkPg6SLK6wxzE3z2uroiNh0lQDpjRZ'
        b'u+NavOmAg9ZHiLn74DYyn84dLTLeJyB3LTSdJ0EANfsPn/YLST152oCdiyOaf2SwB6tTre1JUoxdkiMB0QUPLPVhISMWBxzIFCjfoYsNBkyOk8YrsLlBPDq5i9DiHeaI'
        b'MvOLJo0K09bQmE4EVQDTIVCQSEq8E/oPEfcOet+AwfNk7rXQlg56OXLHy5wcKZnWkBgypbqgzMFg3XVzwp0TfsyGwIpomMWODCYlZ4nN5030oSYqzSLdkBhpwAUfntPA'
        b'XA2cE0PLuRshuy5l9JAGs9KgkZ/yypAcHXIxcdW6hA/0FddexvZIYo3ccJLMo0dDsMhLT/8AWS0LUJtKi3lbTU/h9Hmf4yR4yu3XEuHUwPAa7LY19N7oDONZZA0UnDL0'
        b't4w4oERK7eGxE9w9M+ZvTIM0QNVuWpI5VfqEsUSSSR2kU+ZjcSoDpsxgGIqdzYkxurEpkf5RdmknNJBSI/lezgj1PozugCGbJIL6LY44FhlCy3zb94QBA5pIgrrrpJiV'
        b'JCOWzjUi7hn1JB3XIm+EPeYkd8fxvu4J6N2kRiBhmt7Y6JrqQxiiJYawZ54rE6+jkJudQAh/nSthhftrtJhXywd7MnXcVKH/4lkSTncFL0BaBLFA+YWtNDPSadh+nUTB'
        b'IyPihGYycqHH95woHgsOJpDMaTp3MIY0wzg2RdEkK9NJE+fRE4TJsTkiEoYTjjrghIE2PN58mvakTg+7DlixRdmBfQZR+CiOCIeh/H4yHuZScf6cgrM21q+zxUr/ZJJp'
        b'd3WxQ4cMsKosQlM5sJBCaGdiP/St8jfdb7+F9G8b3gtWxnbPJFr3RtPtGRvM4vSPeuqswjbdGxmOGnD7oMSPiL6fKPAOdF8nSdCecYJkeQjJ2Zvm8FAvivhyjhhjKvvk'
        b'RVKXiVAqh6P07wcE9R6FXSJp27Tv2insCrYksdSAA2Ywe/AcDBpvPUJSoYrtMe3DYxJs9SQdBlfRZ8zjwvWjPvTSzl1QeXG1pz+NPbOO1mPWDR4eIBFccF5h0/50CT7K'
        b'+AHRaop6EDQHYPGiZXuSpY1C7U5jZtwGH1cTw6QOFvrBsKIlDIYo6kMfkgSc2EVkMLz3BM5DkVXcXiLQCu4v6d9kSUKMOejqV1lAPsk0otDbMEK2AT6+7G9pRps1gHMu'
        b'B6DPCOq1jNbS0t+FiUhi1vv7nUXQt4bESv9WqN+LORtJ1I3Bg1PYGgSNdsEkdQqOQFNkMCmE4RMMoHRge3DqdgW5WGesscauK3jHCsY2B2Jeog10xh8E1nC6ijRGOTZ5'
        b'kLyBRz5YZBFMaqNxB7HyLcuNJ2Oxy2H16VR87EekVkOKI3+nnjK0xifCCAmvFhphxE+JmGAh2Z9s9gqilrvQmUkfTapqLXZbw70MUia1fvFES2S31FpoJEK+qokjDu6N'
        b'wzov/YswB30Z2LgXZg6kYi2tXRmOnNgAC4GiPXhLg2CBHM3ytu9qeKTA/CL390J3jP5hqHFft3Yv2VxF9Ek46ERCfI4IYpg4YJqoYD6FDM8HurTo9eERjGuiY01JppZI'
        b'zhyISVGHyRDsjvf3i4s+RzB1TJOm0EDKdkAVx7yhOAJqT5gbAJkYN7EkXj0MHwRCma5r6NksbPHyXW+LFTY4uj72DJbaSxhsJRGUTzZ0K875XLlGX18crk2Kqx0fb5Df'
        b'CjW6x/F2xCnPcwd9PYi77+7De2l7IvHRJhJHQ7SlxWQYKp4n2fBALdiIyxcmtKtpIesi4EHAThjFyU1mxLh1eP8q8VspjJiSCVS8SonUY3/yqdU0bnEkzh9Noe0pQUIH'
        b'5SowpeNkRTKt5aruDa3txFz1JG0eW2DheWhxuAhTZ7ZmuBGecTuJXcsIm0zbKTmJAfZihatWKnTqKcZvJ4nbTF8zSvKwxlbsFXiEmU8R+DACxzWIqybp49stnDSx3Oj0'
        b'enmicFYV5C4B+AeZtNz3dgaqBMHQbmw4RcTdQGJ7Ro0Z4zBgFMQahtPXlOpjfoAHgz269LLB88bQZYeD7juQsIzXelqi4k3QamVMzHnPGQikFZDZTzqnJwpGTxkRmTdI'
        b'ju9cB/fX7IWccJZBiL37SBQaB5mtIyFRGYt5KjAalXqD1FYeTATvJo0yHsVEeLFS+lF76FN3oAUuw3rD87REj3SwI2Y1DimbZh5wTjGAZgcY9rlGVNVFeq8T69fgVLoX'
        b'9ukQyikjFTobS5ogU9UtlTaxhV5SuWlPOnQ6ydvi4P4t0Ouiik3p+EA7+qwhdK/SToGq1XjXO4ZelAvVFkp2vrSbBDJoWR7Km/gmuzocj8ehTSQY+oiHmkI34YIHCa5a'
        b'aD5yYB9L6ykiriTsTWKrEqbUorFgF+lmItFiNxhZqyImSTB9/gyJvC7akof01vxVq0+SCidkrAy3YuH2XnZkrwMKr1+Cyj1nkDnIO0Qwfs5pHcmTGbgdt534rMcQ2i2J'
        b'yeuJJUbIpm4KVVmzC2cNoDZwj3eyJ2nPXujFQXlefHDcRG8vmRv3ofsA9CsYESs1wcLW1WsIxpbswPJrtOcEqdjy3LkMY3LJ25zoSoUzdGw/iY9IVWLNqi3OW7BlD9RF'
        b'nSLaKcSaVNJL81dCcHincxDkJaSTaKy2Eu2G7rAreuHhtPIJsTgLJeEwkkLguYLgWwmt2KgjSdb8LXvJKnyEBamO3tH7SBIUYlGWJS3wmLqYZtKvzoAxbWZ9ZNqVbHjo'
        b'T/+8Dw0+ZJ+3wnDyYRw6ybXiBM46h7hArSkrBoGtnvtwwovg27BapC3huLpg4o4FpXACazmbDEMyJMRHOmR5PmaMlEv0zDhpHmfNSRTXEXlO7cUJQwK6p7BKNc4NBrZg'
        b'o5s1VMiRcmvTYHfs044je3EuK+bwYUICeV5Be03wdmYSget57DnADxq2quDcbqUEUjoDYmwPwJmt2ZBDlt+9bR5aagFYE8lDaoPMxX8jC6phhjmzWD0T+kLik27mK4Ky'
        b'G+rE7d2H9bH+6vHtp63p6+5hvzPm3sBSnDQi1Vh4BlqDCGxNWirGJtkZwshhVWL9B3RjiR0t7O0EYoN5LWw7C/kEB0ZIuZTaYvk6JVb6QcUSh67FEvy7HX4Fbu0jnVwK'
        b'bXI4ZqiCjScMPQyJZh6YKmivx4f7g6Bc01WZ5OYM5ngSlhlgIm0XDolIe9/DMhvNqKOQH+Jtuic9XhXntU9mbicRT6Dc5eJRKEvGKrsAMqoZDB3fG0sUBne2w8gqR29i'
        b'43YDmFGFqVNXE3Zg71YSXNPYCPnncOaKKt52DyDWyCejpJfETgUZLBtpuWs3YLO6qly0ARafjo87e94eG7w1xe769NwgVChC5SoDYrkqmI5XP2JujVMbmN+TFHcOzK2F'
        b'aRa46zFaTwbf3fD9+wi8t+yktWiHofWWiVDhs5kYo5TsnrQMqN9Ju3D7CE46qxF8nyVc0OSeaYAd6tcV6AsqPaBBV+Ua8Vwl/asCFswTQ69Cy0YyJ/N09vjDpCE0aTvs'
        b'U7+MN70w3+i8EvYEQmUstJA9WoWlx4OZrxR7MpjDi3aetXMbIRWRh51WWHj9/EZS0wSATtC9zX70MTdP4lSmFaEy6CJuqSJNXagWHJ5xmvixFZgqITDauZu+bSEbqjdg'
        b'ZRRB7skUopbBy4ZEVgPZWHAD7pAkJ+Rx8xTUbofujJ8TTEr0oZ2UcYEr80qVnSQlTCIsfr/Jca0tWE4ccHJLFl1uWhMToWKInWv2bKHNXcChGHigdDiUxpgigNQl2Y1T'
        b'62ABexzi1eiD8rEtHVjcN/e0M1TKQ40hyfK5y1jvDR1y9GM3zESRsum9TqKxjJipmraiQnUD3vciUTpAK38XK6/hAsw66+Gd3TBriR1bfLE4gUW4jjA3VeRRWpv8bSRQ'
        b'7qjLY3/UWqL6iasmxOOPbP2TiNw6de1obpU2+liz2dgMG7e5E14gznAjWpjXi8VJdWxw2ohdGmQz5p+BPDd85AoDKldItlQR+LlHsvm+iAh+RhGajQ5DrRqZB102WtB+'
        b'wBbq7Qkq5BsGrsbezTsVFbHwmBveUcObbkfJHp61InxVsBdHtZJx0lrd2w467LHqgKMrLco4NMgT13eSsL+dGWqizc5rPSJB8AhyTYjSB8WEym5csiViqzoO+WqcJh6d'
        b'J/m9cGEbGb1NWJBEq9bNhMCkDSGPquhYuL+HqJn53quwyADHd5NNUxEDhYrQEWsCvfIw7OKIU8wyx5xjJL0mfC6TOn9sr0iQ+j7cNcU8C1qYYX3oyIbaVUSUhZtYEFnh'
        b'muLumEB6c7WzJtYQclC8zABQnu6uRDL1CMrfJPlQAd26WH/I4ApLpwiglWuAmXOXtkK/Jcx5wH0zBajfSOCq8RT0XSBbZxDuW54n7ENae7dj0k6Y8dqegh1boc4Lpkyh'
        b'29zGHccVSKPUHtlIRm0zjtmSjutjPFIfoHPInhD2gBUuBG0hyVZ7PFTzfHbg2mCinULM2eVDw9Rt3mfsms2KFxVewD7sdTOT8GNaNthCFiPWywr3sLI9pJMredEg7DtD'
        b'V1j9OpjV5vXraAkmzOT4USjs34GTmVe8mVNpj4jmNJPNHVE7iN9ZOM2bFYQQ24jwbrSYD0WYvIZePczPr92RF4nd6ClHaBMq7kwFQ0cWDiw6yfzJshfaQWRgnjbT6N6s'
        b'Iq8dXbrkxB1bu32IU/pssdiHHtkrYm4nGObzDj9LND6KbU8ca6T7S+h13LXWsd5RnzVBM6PH/OmfqnCLX2DNyPoUCJn5Cq61ClUcEU6IzWQfYG7VRV+c+RozMS8HtCEN'
        b'yk5hk7cXvcpchIUnHYXKRWNw/9CFmCXOOHkaXuzBG/fws2qO5yU8E9PmhHPwx+GbRWZy/Nc33GS/Vj76w2s+QtUih3XSXyp6yP92h7yI5Zh58Lfxw21x7/7q2wpp0ySw'
        b'Nv3oveyAn/itO6Y3N/uen33oWznfc+r++8+zjhzUMXGXxE0cu3mr+laB6c1ai+/89LsBLjll333/w+98zflQzU+c7GNebU7704d/etXY4IPqn/3C0GboQVLM/zq90rRp'
        b'aqeLafita6/uc33j+xkO/YEGR8wO2auOrm6NePvehx/+8puub9leX9vzB8cLpp/9asPP6w7vuf1ay8B7Xw/+3tfec83vOZP/nbt/3fHWL177cVTha3+OuvXau1E+M79+'
        b'Y/ex/D98WveTQofjB377ranyQ3/MfmsAzf5S/UpFn9u++vhjLm5NB+X2fbuyxeP2w5qHJ94L/nXhhWSP7nMffevX3/+WZnBTldnhmjPKvrHbaj/pnFP/6YFvf8vwY5uW'
        b'9vwPPrm4ddvHLjMh379k7NY4+6dTLb8fitvqMxjySefpyr/pd/p5RDVd7Y4Knor67yF3J8d3/5Ds8/Kf1S9/t7nntcptcVUfvRRSvmooOP2737qZ8PqjCz9p1z2bfulj'
        b'v8zBsu8MqP9T8eRU5/Fv1o+v2/fgDyr9vzxd9l6iU9OQQXbgp3/7g8ofEyoNP5T/ydAPB36SPF307YBX/te64FXrEudm509sX7KSK/39N/721u2WtuBNX5PP61qzbSIr'
        b'KKvsj3qKx9rG3/mmUbHKpqgP3v3srUv7btv4/Cn5nRJF53tOiUcKP/6Z98efRvVafFiU8L0F1Iy7G1q93uPDv22M+8trtr1nf/fB121up7SkaCZ13Ttd9rfvbJkMdipS'
        b'8fnricBfrP94x89fM/PR7ZHbmff/mrv2qCiuMz6vfcCygEBeuCoKGmEXUNEYhahUl0iWBT1qFVGGZXeBkWV3mdlFfKQQ34iARK2PHt9EMaIY5KFHm5zem5Pm0drWpjYZ'
        b'z1Fb+zzxeNKkNalpTe93B9DT9J/29Bxz5uxvZ+feuXPnzp253539fr+v+P5n9UU5SY7LI5V9J2/E/qRy1gHf/Ksrat+7WXQp0rTMc8x+cKJl8Wx3z7WrzrRDdn5lW5F7'
        b'4ep380v7P3q2bbzt/M96bv6x0KU7vQzPfO5c05mtxv43Nq684xpjSBwza9/eWou/M+atu1GWv0xvqLzxdsD84PM25fUv66ozOmcfzSzOyfylmPOLyk97CmavOXb4N0v2'
        b'P7jf9ODgzZQPm7Zfb2BT9y9JLi1PjaTqKWQubMK9xLgu0B4orYmoh/q6zh6J3xr2c325+KGnKx5AjVrIiPNlhm+y2fBxfFgLGjEun4oETSbDu0k2R5jJ/dkcIz+LO8JR'
        b'ZIAe4BnLWsFox93UlX6aEfcN51qN+1fXmvXMPDTw9BwenV0UomIeXnRxnFIXVRvGA6AaB85wO2KMZvLAiKnTManRAu6qXU61jGrABawMNz+Sezgnahkq3ino0UX0Zgkl'
        b'wBXPXGAaLstoIKPpSS4TXhqGIGjWDPivmUwsFdRirCV1VMiY1/QfSsR9evRm7IgQaObNt+PXH8rgDSuw4PaUYREWdHnKN4OgTf0WOJw+dki10MfstwW0UNmi6Au4PKJI'
        b'3bB/Do60Vo7j2Kns6K85DuhocZyRF1gjr+fIwkfr4uLiImJHxxpi9XGRCfECl5D/9DiSv4GZDpokz4NbNi9wsD66gZTFJo6fB9s8HJujOW27OXYmfC/l2FnalrGJxYm5'
        b'sXw0HxfLsbYGJplj87QUK5fGpZKPlWAj0yXANj1no1tgaWROCOBo/ZV+yCU81kgVUx5+5KXDbs+8fAtO/KHzd9bj7xSPt0eyWotQN2xoJyv0AgjXwfxafjQ0VxJDtae6'
        b'EJkHEQu5DTcVFaAmsnYetRqY6Gf4UTkpUoEtrFMsLMPcXRU1rWVGIZ8baz9debNy0eace/U/Ttr09oQ5ZXPKs3XszrakI9dZ2ZO75a8rByZN/22SZUNdVueGLxzd31/+'
        b'YcqfN96Qxv/h2t5b9c9031Gvfhy3uPsMPnX0g/S5bQ5nyf33K0XdnVM7r1dca2/f/vGSiOyf+t9vd73T5Lqyx/WjUc6l/Yvf61D/8cUHu0Ytqa3q6Vb28rnN5+1Hv5pz'
        b'b/HhzUcMB1pGHYgpPT4QyP1kylN9647t/9uFe/985+uphx4cPBT1+wUtFyaVtFtOm68cMMVfyf3TMcMrs2xRZe5tIywX9pXFl3x6yz2SrYstf2rdRy9u4i3j8jYkW24L'
        b'J+dPtm9RVtyKmxHZG9xcvbvqtn7gwlzDrz7vbf3kd1ll66Sbi778zHR3Yul33i1MHaPRrPrRqWSwXouKKNnWQKxbfN6EekD2bEeyJsl1FG0vcxQxqD0dvwE5wW99BL7M'
        b'o6M63KWp1e3CvQu1SwKsf/rK5wTuIpckjh9NjPZuysZ6ArXaQMHVaWD0AmccY8Tn8CVNQO4cffHenKlnJNTNLiJD3VoHlXeqxv0Trbh1ImhQ7WAZkq0vIoMj04vLqFmL'
        b'YbodvVZKxkkyZ9TEyApZdO6FQsoxG7HKC+72dF9nFNqhY6Lxdr4Q7dZCOiX4ZEc+7sQ9VDwNmOZod4PWLE3L0R5SqCWb7OjMxy2p+QITh3fxZIpyeDAqadYE1Oh4yVY4'
        b'LYuFYLRbDPhVTp+GLmrRqDbbixxT8Mm6LLKzY1DEbCyfnZJNR8TvTkIdjimjU7Ly851aYjQ+y09eNxjKaiPqlHBz2jjSrK24jWeEhSy6hNvxK0OaeOBb1oxbwE/TaWMY'
        b'YTKLukrjNT75OfwD1GpNH0um9y2gyFfDogsLF9DT8uvwaStE+iqgbyHJgZ2keQRm5MsC2hCw04Ov8qQ6oFLkxGmDnzCbUjm8cwbaSm2XpPGoT3k0fRvui8znyFEHcKdG'
        b'xW9CPTYT7onBfQpqwgNB3OtDe2qJgWJmGEuyYECbMimpXEBHsik3yQrlQc3LTUCAP5Yua81wxj4XqtqI+h6N+3oIN1EbYLp+hQOdmUiuLsiKUUHHonzUklmYnqpnnsT7'
        b'X7Qb1pdPojREe2KeifS1Xhbi+m0lZgI5LS5Go70fRq9WgCc1Zb3r1rM1+CDuKBW0bt06ZzakpeNt6DipdtoQzSgxLKAtz+MttIvGk9540JoO/3PgpgIytdyDByImcKgZ'
        b'd0zVdAvOLs6wvpRuc6ZnsIwlJ+oJPhK/NllTL2tzTXNYM+ykk2SQ3cn9Qyofn8XjQ/lTNS29jpKZ1vm2NFKydjkSTHgnBBe7iH8YghnbIsVgJbO1CS+wDgbvIzdR51Cs'
        b'pbTH/2D/vw8UTz4G4+RhnN8gjEjRRkqRN9IlgSqjGQfpmUAD4wb11OIG9clITj7431PKhpYVGsuK2g02lfd5/XIlGdpUXSgc9HlVwScpIVXwSG6CgaDXr/JKSFZ15WtC'
        b'XkUVygMBn8pL/pCqqyD2FfmSXf5Kr6qT/MFwSOXdVbLKB2SPqq+QfCEv+VHjCqr8Wimo6lyKW5JUvspbT7KQ4nklXKPqlYAc8nrUSEmR/ErI5Xd7VX0wXO6T3GqUXeM6'
        b'Ol3VpKSooOwNhaSKNWJ9jU81FgTc1XkSqXFEedZzXj+oUKlmSQmIIanGSwqqCapC3oJ5eao56JIVr0iSgPKtjqgJeGZM1wKWiB6pUgqpBpfb7Q2GFNVMz1IMBYjt6K9U'
        b'+WXOAtWkVEkVIdErywFZNYf97iqX5Pd6RG+9W40QRcVL2k0U1Wh/QAyUV4QVNw0jpUYM/SCnE/aDDNVD80xr/DQ5CAZcGAC2yGsBXgaoB5AAgEUogw0rlwKsAfAAlFCC'
        b'HIALYBXl0gKUAfgBQgDLAJYDVAKsBvgeQANANcAKKlcHUAdQCxAAKAdYB1ADsBLAB1BMywM63npYawSoGiYXQv+KGLa3/l76iL1F0+4bK0gH8rqrMtRYURxcH7TW7ycO'
        b'/k4KutzVoEYGrFdI83oKU42UJqgaRNHl84mi1pMpkRC4cqpei+4q34YtG4as43+Lq6wac0gPCPu8s4BeR6l5AhgP//sd1cBwCVRz8F/y9GAT'
    ))))
