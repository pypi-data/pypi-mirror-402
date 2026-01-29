
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
        b'eJy0fQdAW8f5+HtPExACY4zxlgc2AiEw3iOOMdhmCgx4BA8heAJkCwlreGA8wRHDGA+8dzxiEu+9Yqd3bZK2adombdKqM02bOk3apiNN42b8v7v3JMS03f7+xjzu7r13'
        b'993dd9+67773AdPpnwR+Z8KvczpceKaIKWeKWJ7luTqmiDNLjkt5yQnWMYqXmmW1zCrGqV/MmeW8rJbdwpoVZq6WZRleXsAE1WkVj5YHF8zOS9FU2nm31ayxl2lcFWZN'
        b'3lpXhd2mmWOxucylFZoqU+kKU7lZHxxcWGFx+p7lzWUWm9mpKXPbSl0Wu82pMdl4TanV5HRCqcuuWW13rNCstrgqNKQJfXCpNqAPOviNg98Q0o9GuHgYD+vhPBKP1CPz'
        b'yD0Kj9IT5An2hHhUnlCP2hPmCff08UR4+noiPf08UZ7+nmjPAM9AzyDPYM8Qz1DPMI/GM9wzwjPSM8oT4xntGeOJ9WjL4uioKNfH1UtrmfXx1RE1cbXMQqYmvpZhmQ1x'
        b'G+ILAtJJMJZ0VCSG0sDhZuF3HPz2JaBK6ZAXMNowg1UJ6XcXShhStmNCqfVeTBXjjoEM2p8/HjfhhtzsebgeN6Ob6FiuFjdnzM9LkDNjZkvxA7zfrJW4B8Gzc9GJyKyN'
        b'zgxdRgJuwNtyZIwaN0oM+AA6544idW1GLeh6FtyXMVLUOF7KomMLFruHwC0FanwmHl6qq4T3cjJwszZDykTg3RJ0J92t5dwD4Rl8fSY6kpWslY+D+1l4ey5UEzZcMm3O'
        b'AFrF2HHoeFYyasY3x2Vk5Ai31fiCZCzaio9CFYPhmTnQlbtOcheawdtYJrc0OINDl/A9dMs9krSxbzi+GYKvhOHrTtSAb1bhaysnlaKmsFCGGTxSqkhGp7Qs7awU7UGt'
        b'uCk7E2+TMBK8E13F91l0CO/Al+AJgg/oBVyLrmah87EwHo1ZeBtqyCVgoeZEQ4JWzsydrUBXQmvQ+ZHwQjR54QDej87jq+41AF12royR1bD4VMho3+1beNOo+MwEXU6C'
        b'nmWqDKp+kmB8BN+D22R4+k9Fr8Sn6+JwQzbpWX9UF4J3cPjCRl0p22nFjfehwFGCrR1xlfm/wFZPnCfeo/MkePSeRE+SZ6wn2TOubLyIwWx9EGAwBxjMUgzmKNayG7iC'
        b'gHRPGEzAH9wFg40CBk9MVzAqhglPihq6LtOiZ2jhyMkcReukVSkDLfPmCoVxKUomHMqSRmsXvrFBIRQuTZQx8FeTJN/Q57WijUwbYw2G4uTqaOk/I5iZnxbUjv47d2Ps'
        b'x31PMtYguBFt289eUsDzA9Q1v0+2Z6mE4r2xfw9rDWNjP2W+Wff+ojPjbYyXcevJBF5FW6WAgU2J82JjcWNiOqCFGu1EbYWxmTm4RafPSMjMYRlbWNAzi/Bu9xx4ZTq6'
        b'j7c5XY5VK91O9ABtxzfxJXwNX8E38GV8HV8NU6qC1UGhIbCw6tG25KTxyRPHThgHq/SSlEH3Fwfh8+h5fNedTroxak5WdqYhIycLt8BS3oYbYRU04GYAJ1YXp9cmxKOL'
        b'6Cw6lw9vX8H78E68B5B5L96NWxcCdiWF4jNrI5z4YAdsIgOrIMjno+GU9knKJOJcc/Uwo+slMNccnWsJnV9ug6QgIC3OdXl31EraZa6lBgdBAsv3a+tY5xRIfXFicJZp'
        b'yas/+tall3fuuLx3uOyNl0yLXr0V/sbiV6/tOLH3RK2FdSpKQ/GsM7qoHelJknI5k2kLHVy7SytzkYVTjV4qgllphGGBpSzNxi9PYdFlfBTfd5FltwEdqorXw4g16FgG'
        b'7UVn5Gg7lzCad/WDm1ExE+ITYtMTOCCU6KocHeQSRsTQ19BBdEEXn4Cbs8fKgD5slhex+HwoPugiQ4VP4etoN25KR+dh7NBdbj07B20u0bJeLlarlThIZwMuHFwe9Zte'
        b'5rBXm22aMoGX6Z3mKtMMr8Rt4cl9p5wMWWowG8E65L6XtFJvkM1UaXYC3zN7pSZHudOrMBodbpvR6A0xGkutZpPNXWU0arn25iBNVoODzKtDRi6kvjTSBll5zP1wTs5y'
        b'rJxeuS85DiaKZb4mOTcZE1SL9wMyHZwAfWcZDu1nUwfHzCnlukEbOrMzCNpwFHGkZVI/4kj+e8Qh+BHcBXH6Gih489BBvMeZDR1Dx9bjNga9yOIz7ggyKy9P6JcFN9jy'
        b'UVoGe4YAT6Bsqxm1oYv4KhBkthiflDHo+ijU7CaVy0dk4CZSjk+gk7MZvGdMLG0Dlt1efDQkh9y5VtqHQXejcJM7nLRujo0nxcUj5zH4UH6luw9B9AnSeL2cYasWLWbw'
        b'i2tgwZLKcau0Bu+eR1K3p1UzOcPwZnck5JajbcB1d8vhUR6EDx3g7SVtEH0lGV/PmsYxCfgEg7fC/zH4Om2gTzyuX8cxJhmDT8N/5zhaUSHg6FZ0V86MxYeB88H//Gfp'
        b'jRp0cCGGcnzRyuCb8N+Ft9J+TVaFoLsSBp9DZxl8BP6jOrRFGIl1qzG509Sfwa/Afx06IZTH4hvobhgjW8vg4/Af3csUOleLbhbgkxyTMgEEpxC8F7XSckMsvl8gYdBp'
        b'9IAZw4wB3t1Me4C35gH1261g1vZhkpikSesoPLqpsUCf9gEqWdF11MIY8TXU6CYrLAGoWBu+6sRXV7HV0GkOn2VHVQVT0tGBgnGBRIaQg3Kmhlkavp6tYetB4nRIa9id'
        b'3Eop4UV0SdFLG+fl9EletrSNbV+hdK14g6dbLU5Xqb2yasYiyP+DtOEmlBF5DAlZouBCRYB1y9JxK4gNDSBdGfA2LbohSU5GTVloF8Adgs8x6B6+E4IuDcHXLb/a/Dup'
        b'sx5qsb9ZHdM8TY2SwtNWj2FLlMe2XK3a0uo6UWerq2C1e5Zu/vaH6sh/5TTkTBqXe7B8zcTnl52Vxr97eOVbskFT9Q/09esHDc/c1edMS+lbS2KGfOvdpPTnWv98zfTt'
        b'r34bMyJjzL6vBqRIkj/707yH331p0crK0yv7ftyyZM/iv/x694Pd+z78zYPz/Vf/hz2zfcyiL5uAdg4g07K5EHCxHp2M12txI0jCcnSOG1eE7rmIjESo5gmQWHB9RrZB'
        b'BrNcNxFd5gBrTmQLZPBCIo89YbhJBxIdyJPyZdxI5Al2DSPDdVlWTXklbgRJDTegc5myKjXTd7wE7xqCjtPWo5JhLfsoN94Xx0gJ5U5Ar3QhoVppZ5raadpCzLZSO282'
        b'EqJKyamGTFy6lJWySvjhvpZLlJAOhrSaC2fVrIqNZh19Aggt6/QG2+xGJ2gNFWang0gCDkKEusLCOQiyOSL89JVUk+Gnr7cjeqavw+H+6DS8swMipePj+KKUGYh3SVej'
        b'fejIY0gt5dAdSO2T8+huNYquPDpIkMdmSCOYUfA3Sf+L4QdlEwQpa3B4BrODiF4xv6/YsMLBzKGlTfP6MDDkk5Mmpq08bc4WHi1fF8IAPVImyQfwt6fLGEoh0Laly8Yl'
        b'SfFW6AzazZTkoibL3dNuqfM5uPmDV2Z/XPyn4oqybNObZbF7H266dODKc418/v7aAVOjo5J0/EP+YbEuWXJlwLTo/slRh1L4/EX50UUHRqXono9cEJ51mMgLt+U8t/jz'
        b'n0wsAFkhhBn5z35HLe9pORfhBfn4AtoucPw+eBdDGX5KX4rs+CK6Pi5en6GL0+pBmMMNTHYoE62RLpts1rJPhoR9SivMpSuMpQ4zb3HZHUaRs6vJQBdFU1RUwxUQLzIA'
        b'8SSlFt6rKLW7bS7H2t7xjtBMR5Qf70gti/1492IveEf1mUtRswDp0kF7Qttz9Zl4Pz6fA1IRbkhEsASB1z+DDsnxmay4LgqHHwGpiMgCCraLiCxFvydTB7pwetKNmC7o'
        b'N0JAvy+XRqz6giWyb3HNpokzRUwrlYRX/YibyTBVxar5y6czhbT02CzZAo4DDj2zWLd95EAB/yScJP9TohIwxVYUYhAKX8lXRW2E9cDkFasMo/sJhZOskbpcNo+8vmTT'
        b'aq1QmD9nCBfPVpEnazYNNwqFFoMm9jVuE2l+8C+Gq4RC7fKYwT9gd5DXZ703fqhQuHms1votyXFovLjkoxmjhMI2m65Yz1widc56b1KpUHjPoCg5xYHUqSnOHiVdIBQa'
        b'U0NG2dlYUIeKVZWL5ULhcMPo/N9J9pMnS94rF1//V2p8chp7ljw5Am8cLxQ2PjNg6GlJMWl9+k+4SUJhkTTI1sBqSGH2XnmUUHg8Wj3xNW4yLOli3RKVqEtNShi06Fdc'
        b'BalzycppY4XC8OBho8q5NeTJJd+ZYBF7FDly+i2G8LbiWdeNs4XCD1OjBu7kFhE4p49JTxEKZyj08hDJLfL6CItrsFB40johScX9iAxd/o8nrhUKG/okS2slb5A6HbGD'
        b'44TCTe4k/SD2VTLyszYHGxjtKEGyuCLniU1kLIOa8P6xVj2VBYvxlWXjAKGSmb6oJRlkmIvCw5sYdGIcR6woqVPGocty+nApemnDODnRq/H2seNxC3peePgoarGPg7Uw'
        b'gRkVPiEbtQmSz04T3jsOEHcio0FtE9EZfEGQPl/AN5LHwWqZxAxHlycNRy8IxVdxy9hxsIAmg9aQMDkO5BtSN2qckY6uQmIK40anphQ9S0uDI9EddBXAngoSVOHUpSG0'
        b'1IV3p5PFMYtJHj8L70BnqCS6cj6674SepDLoWlrqjHTaWiE010xUiTRmNtqZNgadpsXofBy64oSezGaexTdnDwPtlBSb0XneCT2Zw6ALuG7OWnSEFi9AJ5Oc0JG5MFz4'
        b'7lx0dwNtsA86FuGEjqQzlQnp6PoYOhrr8V0YdtKRDGiFz0BbJlGYIyYvwKQjmcwGfClTiQ/S0qkD0GZ8FYDOYjYOzEKXnLSOpegCuoSvAtTZMLrPZQ9CWykci9HNXHwV'
        b'oM4BmflMTh66QqXb0aNALLkKYBsYfA9vNoAqdlxQXI6CaNKMrwLouTAd6GQuflklTMKDMvIOAJ/HxGTkDQdsoKyoVocaiNkPZPm76+chD64TJmcTj9pCAPp8Jn9SvgI3'
        b'CoP4vBXdCAHgC0DSHlCAm9YK+HAU9O59IQB9IbyIzxeu7yM83jYSHwsB6OczMrxjvg7vdYdB8ZDF8hCAfQE8a1/wrJ72CG/Gl/HpEIB7IUwm2rlwNt4k1HEAH3WEANiL'
        b'GG7FItyIdglN1svxHtQEqecYtH3Zc2iPgtaDbgB2bEJNAHkRA+T9VFHsHNqhyCBUi5o4wi0qBy4eiXZZ//3NN9/0Hy3L+0Yi0MwXs54TVtkAxaSKOPZnZOXmr08awVjO'
        b'lf9W4vwxWWDjVla2TDNIUsLTXi6PGvSPsfI30aeX+w579UDiq6FK3ag3lm2qq6tbyR1s0J0a/gEjvbv6tzMPb4l+je3z0lmjYn7iXWs8/stXJZvu5k+s2+hOaS56Juds'
        b'8IpzPz10OcWjP5pTbb38A/Xdb67MWKf62R83pT4fPXd89k8GO2f9tnXcW7f/vX/UjzP+hd4+P2ju6ZXmfXeO/PrW73e1bN9w/jvl1869Nvc3Az8oGhezrqYlqt/6f9/9'
        b'3pj5z10ONn8T+/C9D1dc+N249/Clt69Ufz1xz5KLHxV+5+XVn0tWTJ9y5OI7IAMTxol2hsCqadIZiOWtZTG6rGOZEPQyhy8sU1OhIRPdYIjMsFiWwAkiA0FXQcrdYkG1'
        b'IMzF4+achExAhE3EOBqBb0mwZwmuo6+HrDeDkLstK6NgMjEXyCdzA2LxXddQuGVNmudE59MNCbGgRWzGd0FQbpEwffAOCbrE52tl3cobVBbo1sYgSCFqUQpxlxqJSExF'
        b'EGLjZngVKwXZF8QQLpIlP6ov5XIpiAfRpESiBvEkHCRkFfx19PfVqZWAgOIu7U0uYR3RvsbpezzjE0mO9mJqGEMRGV3DF9uFkjWD9DnwRzD+avEmGdoNGuGDx8gjxPzJ'
        b'BMgj7H9vnuxeHFYI8ohUrWKgp7GaZRt069dbRXnEVhxMhdwd2srsowkTGEqKhuGz+ARIudDF59EVIubi0zKLbMrvZc5UuH1fcuPj4qJXL+04sbut9kRt24GxW8ceOpE+'
        b'Yqs2+o2It7JMBlOFeZf0cnT+/hTdyueLnle/NlB+fOpe6/GBb0UxP+oTeu+XZ7SsoII14r34qmjDAtxck8cl4IM2n8TaC5oMFNDE6XK4S11uEFmNDnOZ2QF6lIAyKjIe'
        b'GxlOCQhBZdYBASghdcLDvePEQD9OkBe3+HFiUy84kQz3xxehNj9GJC5eoNfG5ei1CZk5qCExMycrIRNUJ1BG0U7UGIw3owd462PRo6O4+uTo0UVc9TXQET3kBkqVp4Sn'
        b'hhD7BN4+nyj/B3LxZoogbMUEJq/iHUJmI7KXpzFzLEv3ZkqdkwhGaY99XLyE4sHl2pVsafAHs14bcVt9Rv1a2WuRZ6x7R5yO/LD4ebU8/Nn9m8cNYdTLDjWHxL5hBGWG'
        b'zP3kkXiHf+aPzqCEaTs65SK7KbZBcC9QmWGi8TYzaDPAIG+Js9gzbkR3UmQ6YkawgBlBSjYKMMMxKBAvSh+LF4P9eEFebCAVDqV4wXzxGMxAr+Bdq9uJBfJY9Zl+BSYQ'
        b'N9aitiBc3xcdfawmLelktPwfNenucIPigH15GDNYlyYhMnbtLIfAav+wVMYol3zFEv4bPnyiUGidJWGko25DTcWqU+5pjGX/H02sMwvuDH3t9x8Xf1L8RklF2Tnzw+Kz'
        b'pthSXfLD4kWv3toxHMgH+0ZZpmlX8UOee/tNzYYTSxWpCmdwwbiTk1PHpKKfDs/LBW14KjPPHG7/1gJAILIo0YMkvBu9nJ2j4xh8Hu+WZrFArF5Eeyhvq8pE+4At4u2J'
        b'uTm42YBewBcz0Dkp0z9fOhFdtz2pUhxqM69xGXm32cibXAIChQsIFB4MPIhaZ0Atdgzxo5HUKyWPeoOsZhMPb619jDWGoI9jmB+tSEUtAWj1j170YrJnKMF38GHcRDb6'
        b'1uJm1JCrzUHNuXSXMwZfkRWh1qmlkoCJlgXi0SwBj6R0F07mkZfJRVySUAO4FHBJQnFJSvFHskFaEJAWcamiO7VY3gWXZAIu/Xlg8uS3OaocRbxXOkNAm5/yUtd9Uf+d'
        b'PHQ+Y2nc/w7jLIE7g1TlQ7ZdDt2UpJL+ZlV+Usq731Vfa+0jS/2la17m3czSG8pDJfOOLNs49cWt/eXfeUEzpXrIJxXjvygu7dv/D1vmRu47+8vbC2N+2Dxmz6dz/x65'
        b'eLTim+fLv3kwQJZ1cJX1j4pnCgYMWqQDOYraJIDnbVmI7lOrn4Lh0Avs/Hy7iwim491zhG1ji1VKdo3xVnyCkinkQTeezSJruAk356KzDpZR4m0cqoOJ2EprTSjNgnv1'
        b'iUDk8KUgaQ6LHgxEp+nmzbJFo9FZdAg35aBzDLRXx85dL+lNaJL3eKsz0qrKzZ1wdqCAswMAXzkpS2QlkJQ4jlNyEV9K5Q6NH3tlBHsBZQlCeuWlbpe9LJAidrtcAKtH'
        b'kPTwjphMKj0QgMkfRfWMyeTZlerirHzckJvQAYmHoRek+BA+iPf1zChnMqIcRbaRmTLZ/4UsFQq//bog8TABif/m/h7Tah5M7AtaNEy017wZpGFmhv9DSmwrx1LXCIWK'
        b'VUomXBouJzaLYs06odAWG8JExh4kr2fPr64RCt+t7suMSjujIPaizdmiuXLB5MHM5NjbHJNXPBirwoTC7aMmMBW6erJakouGRwuFa1YoGFX6B3LQfHQLVwUJhf9cE8vk'
        b'Wedx0DoXxOYKhV/NeZapqXlGCtQ8wiIXzRNb46Yza5KaiGUneYFJNKPE6KcxrlHvywDO5AlVonXjQlQ0k5S0R0ZMMyWRJUJh/RAds2jyQgW8ztUPXiQUro/sw2giQRev'
        b'Ks6u5oaLFqjYmcymmq9kUBjxYL5ominRAi+p+EoBPbK+PsUpFN7sG8pEK98mIFm/VRgjFJ5dNogZP/mHBKTpqiROKHRWTGKsa6az0Pdk49DFYjfn5THH0x7KoaG47QXl'
        b'4nTwZuYN69dyaGj0yFGiDSgkrJx5U7eDg9fLfrJkoVDYp6w/oxu8m2iSg905iaJRLBMYYey3OMIIdc5hQuHMFdXMP1UfSgCkVRumiHBWsuMYPtxMGKFjmVstGtqeHcmk'
        b'6YYDNhWXpNsHMhZTGpI4RwNeh4Uumb8zxVabFD779Z9JVYYgrez1P8+rblpiOqUbMTuu6cJr8RP/op+r7P8wo3r70ZOl+46vGrfhNxvLrk3/UjY8ZHnEsLizml+brqVI'
        b'3ZtGSreizYo38yJcmxxMofrWhxn2/cGKqHuv/n1j2G/+tuAnz6xpOMgrRv2sbVF8/qJpv12ef750UsYvpx4d9uof/z1zOfO9A5N+VhX32X/izPdOfPTBX7hB3jzTX+/w'
        b'8x0PRjffvTrwQWr2xReuJGUYl2bf2XnqZOYvS6ZlvLTl246Iw8czf2k4PO6L/zwcU/3tktO2A2sb1zc82vO8+90Xlowumq7ra3M734x673e2E38+9t7RhSWfX/v8s7f/'
        b'hn4eemDQm18e+eHf415LTP78zV8v+c4vxvx0UkpZFLf/yoDfDfjmj/HH5v7oxWEb/2G5zN7WSlyEUADR3FMAZPUWfuDn737ejg9o6Q74cNSIrmbpYtOBFjePygLKDErx'
        b'WutaSnuXTBkfD2/GsYwUt+a7WdywEZ3Vhj6GwD7+0gv5DjS0E/JcYrKtMFbYrRZCbimNXiDQ6ClKCVBp+B1F5YtwVkN3e8KprBHBqaTBQLs5Nlj4kXT6K6T+KB2sAioP'
        b'+jBQeNCHR/rpOwi5a80mRwBJ74XjsI5RfmpOqrgQQM1/EtkzNY+HJ/ClxYlZlJZn4m24CW239aWeHy24IRsmSydnnsGX5fgWi5q7KCky8a+zDC5m4pPHFHF8CDXdc6AL'
        b'cbykLqhIYpbyUl5Wx9SyRTJIy8W0HNIKMa2AtFJMK81SwiTKOD6ID65TQkmQB8TqomAqw6i8ihSed5idTkOpPAAWpfhL+QBxihH9lPx+S2VKkd3I65XAbhTAbuSU3Sgo'
        b'i5FvUBQEpHtzGuiqussE3QxfycV3CghSg2p+bDjIH5sEL5RPv79Z5nRB6vc/bxnSeLkPSgqXfpO7t67A8+20yBTZW7Gb0kpfHJry78b0C6q2gl+PWuecdjer75k7+12/'
        b'ORG37a/x84bNvps89Cb3u1v9rdHef36SPe35L3+xZOGkzV/UHGtAn85uUY2WhB5WXUybPO7kP9DvD4fmHvh82BsXhyWNn6j0aIPpQpPjy7iNLDS0RQ8KjLjQ+o2g1qkE'
        b'fA7dpJukZ/Am0cWF+rfsQScFR5ULY/DF1ehyhx1cfMAkbGodCsVbqQsbqsd7hMrxXQ41hIyg0hU6jTbXoDPl8foEQY08xSVlD6KiGd5vK0BNqAUf1uCWrATUgloUTEgU'
        b'hz0T0V7qeBNXKEdNuUAFcHO8YbQWvSRlwoIkLglupNrFUlTbFx3HbfQZHWqTMnIlNyACwCZiDtqCD89BTYkg2ukz8HbcDHILNZ2dloBW34prae9hoi7jOngMbcrVazNz'
        b'ElgmBDdx+Ca61r+rKqB8YlLTTkoURqPNvNpo5PwrcyOI7eJWcRTdryM+OXLxpzpMxHG9+J5AFJReSanVSbfmQAe2uNZ6lVV24kbAm71yp8thNru8Kret3djSm0Yjd8SS'
        b'NDGQCZt9xFvVQbbwHPF+ajIaLl8GUJPnB/ZITbrA3EEOZMVfsjqcZJ3WMMuFBcYa2liv0ijuTEJa6jRby9q9KIQBVE63mipLeNOMUKjFQVS76nBfe75bT9yglvXKjGT8'
        b'HHp/K/6mHElwUftaeaI6K4Q6g4y+2eix3rCnqrdOqFdhFOa2x1rDu621g+g9lRFsVEBVn17oLuvOQsUxnamgxGDZseX3UidZlrtuLv24+GHxmyUVZaqy32ZLmDXz+n7K'
        b'IX6VlhVcQvbhE6s7rFklOj6gEG0RMJ3rdhWFWpwBlsR2f7aN8BNV3c+HDx2eEjxxJI5EUkv7cghsQO8fTOLyGsH6/Do2wc+n6p4RvvsGgRmQf9oQQGojcaszGr3BRqPg'
        b'RA5pldG40m2yCnfoAoNV7LBXmR2Aj3Qh0nXZvhrH064TNzyT01lqtlp95KDzkm4jKCg8Bo/QDpFd78/JOJF9HqUMQP8moo+KpT8cJ7gEoxv4Br7nzM7QZibgVrxPL2eC'
        b'lwMB1iZ2mfMQ8a9zGxvA8NkiSaukNaw1HH5DW8MsXBkHKfGH55rlvI4IBAEOw+HAjIlIEATMXWqWgUigqGNAAAhq5kAskPHBNB9C8wrIq2g+lOaVkFfTfBjNB0E+nOb7'
        b'0Hww5CNovi/Nh0A+kub70bwK8lE035/mQwGyYFgW0fyAOmWRmvSEJ8LHwGaWwqwCQWYQP5gKImHw7hDyrjmMHwpvS4rCac/D+GHNHJ8gGmckvIYfTvvWB54fQdsaSduK'
        b'gPwomo+h+b7C262KVmWZpFXKj26W8HoqsgjHAchoqT1hZUF8LK+lNUZCDXG0hnhaQz9eQglFIohFpZSGPhoTrAn4J5YK5xQ63NHKvVILiLdeKcHF7lDPUKoImHyyeNS+'
        b'RZ9P6IkgXwWRARQn1uchri5Ti3RGQaUtJdAZBaUzSkpbFBuUBQFpoDMSSpul7w8EstUBTPIvw2ZxWUxWSzU5aFFh1pjETlmA15lspeSkRudXplaZHKZKDengVM1sC7zl'
        b'oK9mzEoxaOwOjUmTnOByV1nNUAm9UWZ3VGrsZV0qIv/Mwvux5GWdZlZGqpZUEZuSmpo731BoNMzPmTU7H26kGLKMqblps7X6bqsphGasJpcLqlptsVo1JWZNqd22Cla+'
        b'mScHSAgYpXYH0JQqu4232Mq7rYX2wOR22StNLkupyWpdq4nlzVUOc6kJ6tHqNSk24RmLU0Mt7FA5dK7bulbBoPLACLvCK44fQY2pFHCS8p2X8Y0/6EWE2fX0ssjThffF'
        b'DAxiQW7CuLETJ2pSsvPSUzTJ2k61dguo0JIm1l5Fjt6YrN2MsK9R6I7YIqS6h/hJ6vHxcqEuX+6/r0/g4UJtQvq/qKvLXkBX+22Igdqb51ZJiLVTpyenWGJBtl6I67Po'
        b'cRtiqUP3ivBhaut4fsF2ZjDLRCctnDrymwkbGDeRFND1kfg8tXjm4XpyjiYRN0Aqt0CoY346Og9q+4vphpycjByWQY34hSBgIm34HK1zPIBFT1iUjRiUvsHKuMnGcDlq'
        b'TCc71PFZxFETH8UXsuelC2I9EerxLi1qYwpSFHhfeDqt5YOVviMZ3095f8x6wTRzP0I8fTE6bbRraTDjToBCE9oa2l41OYOUnYk86CreBgAn5qfjxmw5MxefBhVobbZl'
        b'YsUVxnkLXvth0IGYlrERtZrw2f0X9fvJqcwPQh2qv+6YOM4SPag8/3iMZdbVX2tOv/X741/s+HDsva++fO7b9VnLnb/b+/3MZTGfLXib/+Nnb74fXN74jqnuvU+nH0pC'
        b'C3++rnrnT5AjYtpHp1Ij//XZzLtTY8/l/3ng52XHHzzzz9dy42teb1h971DtxDmNW0ee+b7ilYmfzwn+Tfrao863n3kpvThB/e2hxz/7+S1041L8J1uTJm15sKnSdKzw'
        b'ewkv7pq87s7OQxs2lMR/OfNrR4o2jO6c6FA92h4CXdbmuPF1LiEONyZyTD/kkSpRG9pJNRsLpLYRr4Px+Dh1PPB7HRQmUxuNlZzdyNJn5ugyUDNuEQ4qwdy+MhBdk9os'
        b'iVR/S40Y3r73y2Xi+wn4NGoTFKwL6Hixf7dMUumroh+uk+BbeFca1eFwg2U8avLdk+GDLN6+Ed/R4zYqDGaiU+gIEQbJPCVMkOBDLNqOd6KLVLsMAWw5SN4W0FeG73Do'
        b'nItFZ3AzvT/CwRG7hV9J9KuIcruL8DO0S4oOEx2wWUsOnKH7k8XOCvXFo6syvDUJ36a7nSumyWhF2YDVtSUSfIxFO6SohYKZOwkfhZv6HDmD6vAlCb5BjnKdRDeoJmvA'
        b'R/BZfBFtJaDmEE8MYhZXl0umxqJjdDKc6ApuhbG9CZVQaQskLXWqZA6+iu8K+xRXcMsAdGI6qUGHthOnXSmjRmclactQk28nTP0/W786i9Ugp1qAwYraaZpPok5WUl9S'
        b'FaekRi0pq+ZUbBRHzFsqmlfK5WzHH46IyuTnS7kc9DOBrul91RsEsTVIkMWfJZeZjE/77CT0tkvqT6xuaxVCJVEda6d1JvorpmIx2U8b1kHO/2B0z3J+l448sVLYRhRN'
        b'IoL0qLotCVBnxVZ86uyjmEK/vEIYBbBzH6eIdZhNfILdZl2r1UMbEt5e+jTattRYYintESSjD6RHowgAIO302v7TDQYVNXtqucTfcnzvEsfTA1AGADgIG+qxcbO/cX2g'
        b'uPK/tB8str+c9RkeOFhsJkFrFJC1J2gqOg5Fb6LM04NC7RWcI9e/PHqCYoUfisQnEYKeHpK6AEjieoPE5ock4fEC1H+HnQIUPQGw0g9AUiFVG6DtQFObRpxWjZUeEu8R'
        b'hv8bq4yoLT16oYuEmEokfqfG0mnFOs3mSnpIHXQOKvR3eZEcXBdVoQJQPaCHs90OuybPtLbSbHM5NSnQo64CaSx0GzoPL66aqE/WJ2l7F1nJPxnT1XxeqGXpKbrZQ3Xx'
        b'lOtJcTO6PpNFL6FN6LalfNZizkmcc0aml31c/GZJuinWHJv/sPiNkk8gN/zvXMmHka9Fnln2ofq1NXJNy3Dqx/TtvwdNfL1eKxVMvPXFz/rYKj6f3M5Z8c4oKsgo8J5V'
        b'fjkGt2zA+wMFmRjsoSJADLqZ5j/OPROfEk5zX0CtLtIj43g+i8ow3DJ0eAmbiO/1782cpSB2I99JItHdaSNTHcxGEWOqyA3EZwTe6ZjQubZ22xXZlnJ14Gnbe7Fdda4f'
        b'pIuZ8NpjXJmIeg8q/1O7Mgk2CukjTxfsKDC7BJXebXVZQKEVqb7bKSitNJKCxuUw2ZymgKALJWu7VETqmEqNHFOLc+AZqAr+mMrNjuLHqFHkX1djpugG88MpLUya5Fmy'
        b'k2xYNXg4457MEPUI3U6h6pEDXexRQ+qkHcWhS5avfvAHxklq0J9N/bg4E7BYl/9R8cPi5WWf8H8qlv5Yu+3nutlxMSrtzFV981D8qdopR8duJdgcysRnhxxo3KDlqKC4'
        b'Ad3Ht0TR3yf3z1NSyf9kuIuY9EvwXdTaLvR2lHj7aanMixqXiK5Qj9sIdZpdRt8EURYe6GBFfmQ+qbB6gA+xurxj8DVGhTGCbb07XNEnEv34Tc5JbuiA33U9u1z1AsbT'
        b'CErqjq/2yBwaO3KnJ8Vlve+wFdlh69n7iwyE4DJDTIN+t5kn9f2SUPFH+j6oNF0ta/71Z3dYyi02kwvgtPA9MVabebVI6sfqx3ZjnujZJsMLhg86BD6HT2hIr8k3r3Rb'
        b'HOII8ZAqdWl4c4nF5ezWDkRWP0DgtFf6RDQLcFuT1WmnFQhVC4NcZnY4e7YSuUsFiFJnZQAft6x0k/pAtIklPFvj8EEFbWW4TISLP56IdPXLVBrcz0B6nAzfyDKQ7XUa'
        b'1cGQMC/d71Oaj+uz56VL8rWoLUOzrMTh2GBZFsTMwq+klIdVAmdpoE6pBtQ6M9DCAe+DVumrgiiOe+YDe9vDrsTXlQthxd+mRzUyVuKL+KoKJh6fZfTL0NF+uNY9G26A'
        b'1v8Svu9UuxekEzf4+bhet4Bu+jehtsJ0HWllW0Y2bmSBeJ3SrkF7R+EzhRyD96CbKnQIbclDZ3Eb9R/g8KHIQMiq1Hgb46s2b2HCAgWTt1GOTuF6laW8dA7ntMFLB2u/'
        b'SXjzLvEWnD1vI7Kzc0zh0Ztek72QnlLMvj39xoQLm3Iuc83mLx4OLHF9OlFz7tpn0waVzxjg+H7qvk0a/cGY0HVJm/9ZuCSr369eujtx/eTmv7x/9e24mu8ffuE38Q9/'
        b'88XN25sfWZtH/2lv/6VLNIfQQG0QFQFc6A66DFTbp5qHoAb0wAbw4/oIF3GgQHvUqDlkAHoljhy1IFTTR1yHoatSUO1Poq3USID2oPo4wSICZHa7cFpjQb4gaOxHz6Pr'
        b'WQGmCFUu2hUu6YduZAiHOR6gS3i3j3ijfbZAu83L2XS3fQ460r89asx9Fh8fig6tQLeEkyRb5+Ptotf1tFk+v2uNdBnenCl469cvSPEZMYgFIw5fRjsUVmEr/mRemWjD'
        b'IPaLsEUgvrw4X/QpfCKnGEJQ24mF7/TpiHZe0F/JylmBH6hEriDk5J3IcodaDD4YKMX3U8XeWIQk4LF2PrEULs2sD6RN9Oeznp1gegHp6VRqoHE98ofTfv4wlmpz7QSw'
        b'NxXmKTQYcadYSs7j9AjFWT8U07qlfKnzUzvb4ruBh7gmVTrMZV6501JuM/PeIKDZbocDlIQ5pdIAWIlpWuUjiQaBh7XHuWI8IaJvjqpMJXI0ab0MOJoMOJqUcjQZ5WLS'
        b'DbKCgHQARzvQK0cT4nwJoiBlDoEKUc87RqRvAmvwves/l9CzbZ+OhPAWfQVGkZSZiGqo16SabETvMon3SpYDk+uWu5F9KWA4BbmTJyaNpTtSZLeIJ+ouqGQ9Nu+fgKma'
        b'OVZTuWZ1hVnc74IOkz63P+HrVE/N2+yubppxmKEjNudUTUpnGbtY7M4TsMeuel+wwU2sjai1BjV05I+4XiTT89OhKD8dXUbbBJbJJkeg3Wg3vpqFr2YyMfiUGh9MRDvc'
        b'06CioDHAZ/UJcZlAeoUq8G7UIlTjrz49c36sGGwChHN8eogKnx05mwr7/QanM+GzhrNMcfHyGysGMW5y4jePM3XeCVmaLEj6CZk5BYGCflNBEH6AX15CgUF3cUMsbqLP'
        b'4O0G3Ipb4jMIX40nnLadk4POqcvM1mckxMkZ3KRVrVzlpCzfvNrUgeOTXuB6dGhAbkEskHYQ5nXahEwZU41fDELN6AQ6rpVQHXqdwQZs/JVR0LKEkc5g0cv4HjpEg4Nx'
        b'WSXxwrs5xEXrAIfuydaVwk3KV87jTUPjM3PEAWSZ5fhy3zES4I/HHJZ34h/KnOQYzStJW4e8dTcUJ6mkefnGJjZ5q+eN8I/e/kXzJsbRN/yoJvNbn+yY5R3fejB+aJVn'
        b'd+Gmi2PKzv17TqE24zufTr2yaNn8HxQmnii54fngFx9dORT1bfUzut/89MvxY0btW75md2zh37IKtn0v6+wX6rhRP5ul+NWjisQ3hz4ceP1nKXsHb7zxp5b1AxKH7ji6'
        b'cc+h+Nm/XAVcnVoMbPhMFmV1+Ai6y5WwY2G8TlF+nodOoQshAjNH91BtF4aOb2cJ2xOn+soCBQMbNxRfwYdS8X7h9n28BddmZeTEgbDFMUrUxKkXoc3oAU/58XOL0WnC'
        b'zvGxtAB1jLDzsQspiMnVqDlrEjohhLQjJxPQXrRf8H7FdbgWXUFn44ljGvGNlVu5EXOHUUkhA5/EW+nZmFwhwgkJLXXN0DdRgvfgJifd/EBXp8zzbTiE4ib/ngPIbgJD'
        b'Vf0fbRKEEPYoEg/K8fXtHH+ynMacUPr5fbD4q6LHbsieAPdVsKy6byCrFesS+b5c4OCEaDh4cjF3ZP5BT+ffKxVqMvtFA97PCcvh8nIn+eC9ET3LB90B/TSeZkrfSz3y'
        b'5Tf9fHk4YSBAXik78fOfQFuiVkqdizj4ZedooxwTSSXkkJ+DmBWInyFvLzUa6Q6Hg8Q9ozshXgkx+M8k2W42W7wKn0ma2JCoou0N7aj4EqEqQNoqp2/5+kUnsM//0bZU'
        b'TwjoIIrUADJvNZBQclJpJCv/Rkpm6puhUymKfS2X/Jd/pepgFRsRzAkxfKTBbGRU5yciWM0wIe0mhsA4fFXizDZQMb9gAxDL4GoOb8e7TV3YXrD41/l1J58pniuS8pIi'
        b'mYUpkvPSIgX8KnlZURAvLwrmFUUhrbJWZWt4K1smaQ3nlc0cnwsCU4gnvExCHaOJN5DKHMqH8CrqG6Vu5orUkA+j+XCaD4N8H5qPoPnwVrW5jxDYBwQx4rAT5ulTpuT7'
        b'8pHEvwlqjGhVQ7vhfL9m6sRNn+tTRjym+otP9IU6ia8UcdWOhGeI79RAflCdsqgfwMbyg/khkI7ih/LD6pii/tQXiimK5kfwI+HvAPGNUXwMPDWQH82PgdJB1L+JKRrM'
        b'x/Hx8HeIRw416fgEeGaoh4G0nk+E9DA+iR8L9zW0LJkfB2XD+fH8BCgbIdY8kZ8EpSP5yfwUKB0llk7lp0FpjJibzj8DudFibgb/LOTGiLmZfArkYmkLs/hUSGtpOo2f'
        b'Dek4mp7Dz4V0vCcI0ul8BqR1HiWkM/ksSCfweaKpRsLn8Ia6oCI9T0ODaed55SmV1EnrpQ7yEln2wg3BT0uIIguiIAniV+4gfj0aQYArXet3Gerkd9PR68sBFVSaXZZS'
        b'DfEsNAmm01JBDoUCIlpCnYK9xbpWY7cJwmJ3wpyW88qNq0xWt9kbZPRB4ZXMnp9veDS9wuWqmpqYuHr1ar25tERvdjvsVSb4k+h0mVzORJIvWwMCdHsqgTdZrGv1ayqt'
        b'WrlXkpqd55Wkz5/jlWSk5XslmXnPeSVZ+Qu9kvlzF81p47wyoWGlr90OVrIOeymELNRwzmBCfddz9WwNV8vy7AqJc2gNd5w9wTjjXBzP1XBRDIkLXM/VADKvZ3lJDbuK'
        b'cRTVsMQhEd5ij0tINGFePgCei2YimUnMetamhPsKkqpnyHs1jFEKtcpOAK03ynkl3UMKet/YnT7S2XdNnOd217XOL/Qk5dOREHQMk1AHLenFxCUM2VTqEFaQmzA+eeyk'
        b'QDTiQTXJKCMiv8ZZZS61lFnMvK5bxcDiImoEMECflxpt2acrCigLmorDUuLuQbWYSm5PLebNZSbgLH40KgZdxVJaQWq3COMEyCi2AwjWtW8fkTl/1M9io5tY7b0ZE+Mc'
        b'42X1XjbpI8IyPvoG/j2S6JOSDFqFN7xzs2TrxWStqjB5gxeQnsx2OOwOr8xZZbW4HCsJc5O5q2CZOBwMtTNQEYIgmGM90+uZdsp3f0e4VCSl/VLgGJGiCUTDEaGoOkxA'
        b'gKdzJhD0ewpaj2LEF35XAl8Tfk+ChM5IQ6dubZVZUwxTUgqM3qpPE/4WF+sd5PjME4PVxtJR6hGsL/3SzSDqz9A9InZpjvM1Fy42R9bwci7Et5kPk0AmxKs0OY3Uj9Or'
        b'NK+psttAx+0RlG/8oJRS/wJ3ZQloyTAU4hhoqqymUrJ5a3JprGaT06VJ1uo1851miuYlbovVlWCxwZg5YCT54mKCpSZ+uRseJA90rKXrtm/H40ksDRnhD/7tP57EUrP+'
        b'k20BEyPIX7ojOvOriGQmEBzzmtIKk63crHHQohIT2Y+wCzu98JRJU+Wwr7KQXdyStaSwS2VkH7jKDLwjlQwudHCWybaCWuKdLjvIjZQ82J6IFIhkwAeSkYJUTMbYTZe+'
        b'QGgIRfJb4GGMiZNrNxt+JDS72VVhb+djOo3TAjRVrIa8RjbmO7jK9tBHsaKpJLj71GKRxXazc9irbaTEbiehcjVlgUYYN50KvtM0dEskV5sdsExXAX80lRAPgx7MMR1E'
        b'TBoyhulsWVEbaCxpfKxfZXxCeoaOWLOzFhJbBd6eDsnc+bGZugx8DB9JkDOVEUr8AL80Qojfd8RQAQrlJXx9XmwmejAtgYTnbIk3oOv4hfwEfIZjxs+VlaMH6GUqB6O7'
        b'+BV0xqlfpMrJxHtWyyOYMLRPorePpI6ZM/GhkkAjRqwB3YtOiMtKyI/NFCrOkoGsqkR3I/Epob5LZVYniVO0rRRdId5+qIUFYC7IafT2mejOoALUjFvn42a8Z34Oy2Ti'
        b'I8pcFl9De0fNoSFd0WlcW+HU52TKGNQ2WYL2s2gTOhPtJgeY0Hm0a5YT7ylKF2wcWeiClOkD8KJz+PZsIYzvUXwvygmDU4xeAlVatp7F59MKCi0bFvxC5vwuPDDxkaRf'
        b'8zTbrHmqtD//5w8pEWd3/HpZ+uvqs32aT6dnyBry01b1zV8z4EbrHy4xe2vtk/5+eMq7y2c+rD/+g7x31jmufaI5/tPgGHnuj4fjfrLoc/mrIvkvf7lxQtzCL2f/4N0B'
        b'bW/N/MHuhJIj137x++MfXVP9MTPZrbVr9vz4aMX7tzwf2BZVHEw5OOvUH6ZvcL31rzd/sPM/c+9/+U5m8OvNv1Df8n6/IvytZw+ju+rfTXzb8szkhMu/WrMI3d/zWvPH'
        b'k5b9pfSr4NrJv7k9uPhRauE6Jvm1Z4/3WaXtQ40bz6E7MNokchRuUjCD0Q1pAgvj1Iw8gu1jczV6IT4B356CG3FDYjpuljCqORL5otHUfoEPrabbzAm4kWUmlksTWXQV'
        b'7UW1wl7DxSR0PD4zh9hmDuPD0uEsIFeBsEVxDzWh7cSkgvbiYzkKRi7llJXLhKNBr6BzZAeFwMQyEfi+tD+LXsDPG13ErzmGxOIJCdyhcaLGwE2a5ihqlVmPXwyJ12vj'
        b'YsWPDOAd+KUwfEWydi66IkD3Im7FewWLD2MWAkY0zaLQrUEnh8WL72Wi01IDiy6he0EuYjHAe/HNccTikqHTo4ZEWFywBG6TSjQaKb5RiF6mYKrQvags33Jj52blouZE'
        b'WHGw2uLwPRneglpm0J38YSVoN3QVXcTXifmJLBOWCeE5fKgC3aNnoNFL6Gp6lhRdyU1gGW4VmwJr9QId/MHoMr4hHJ0WjnOixhHcWlk2BQDvCkU7snKysnL0c/FW3KDL'
        b'8kVqiEPbZeiiAe+g1eMjycW4yYDO6+TMtBRpGotecTmewunyvzkN2U+gicaObIBalYibiWhV2shEBLPhoj2JeKJGwl85S05NCrYmteCfKpYSH1V6dnKwKP1024jBd3SK'
        b'nnv8b7xMWeFVKlTsIpwdKnQSc6NoS9rEfNPLIclegYO6iXzZsxMOjQNDA5GB2MAGxIHh6Pc+nswRh5yyebc7oSFV4HriERtBWiQSDjAhwsj8ApsoOxBBwinqAF15lLjd'
        b'0En46CRqdC9adOV4hV3FGBNhlR04u4/R2okEQPZa1hIZpStkptIKYWO/0lxpd6ylW0NlbofArJ30uy+P5/qdVayOom2Aj6TL5CgHfcb3ZK+bKzb/7oqAJb7NFZ90RWQi'
        b'szPQGPAY4aD70+pKwbXp60Ih0FzS6ODsX04VY2xcmjeYmUwK1ZuTrUk5QqF+5A1mDWDM8cmqWalLB2lo8Dk2FZ13hoZyQMuDWLydhHY69YybBKgGcvb8pKxOsoa4keNn'
        b'vIV5C1PQgYQFC0EKILsy7T4HQKKqh4ZPRUemWTYFY87ZBlXOevl7OWJA8/L31OEzhjTWT15QHReffutq+J53dpRZJrNbP48avKnWdOj5v/zgYfOcySl/KzZd7v/3wVMv'
        b'S5L/IR373djRjcoXf/mz9LZ5a+rGvjPr/Yev7ztdasexOUWWn99QTC4YdOjd4Lhflb0UNnLpW9V9l20dYYs8+t75FZl/SnrnyIjXf5ffMvLKD3/6tXLh50uXfj3u9usz'
        b'1u1858J0pfaP/UqWvTX9+DMb2XUNk1+zpGiFYI54Fzpb0X5mgsnkElBtJeWoCrwpYWRsVoAEErZAYsVt+BW6aYGvJqOXq/HVgPHrxDqShI2PUSsWiDGQ0AMpDYMEos8N'
        b'yqNK7BuBYZ4WqH9X0o9vmQQOeDYcbQtFt7ICNiaO5NJthUlL0Cvx7QE7QtAVDl8BVv0y/xxlPaXoLLTwwOoLmkQjJpnwJso+k9HxZ9AOs4+DUvZZiK5RtoQ24ZcXdGCf'
        b'pG1gr/so+0R30Usu4qaNboThi1R0zQDg28diwlgYDQJLI2tMVKJT+DJuoI1WZ/Px1KdCxsiXkw8FcEPRFdQkBBl4ee2YeehAJ4c5skODj1motLAqB70wCXnidTkgrAph'
        b'5EGQ3S1xrER13R2df1JOpxA1CcrbpgfytqkCV5PTkxSqbzgu+GuOU37NScK/4qSEk5EgIWrK6QRPCjVbrRaZh1hpR4e69R0ZWi/hQjjh2XaXiVa46LqwsXd7jgPVGZIu'
        b'2jshPFR7J1oI0d7hl9jZBvKsi4O0pJaNggd4rkPOF3HjERdjeSSN0SeDfkth9aqMNrtR1K+dXompxCmYY7rR9L3hRv/GuWC2NHC+g+IcDCNX3d9ngen0XBfbon/HOhsu'
        b'9fRbD7WcY04NS/vDrJA4ZpJ+OeJq2OOkH8wJdj1ri3JJeLaG5smTZRLB4ghpKfleBFXbOcOjMX5+WmlxAhilFZQTxQAjIMYsql+TBMwkHYK+lsoqq6XU4jIKg+602G10'
        b'5rxBhWurBBMWHRTRXuWVUbbtVQoGYLujBy9ktbHKYQZ2ZjbS5+dz4mlxhgZplcOAEfwkWFDdzzdwHd7odvLpsBEiwxOTKQwFMZouZ8u4KMHhHgYgQqgtlnRSJ3TVsc4/'
        b'qeqOUCqNRmjTYTQWE/iogBRoShPu9YyGERQSHyKKUNQRKBQEzWDUA5ruhE8KIzndD7UHtKz2t+y/5f9H0lJfw9EU/48DJvDsCW49HYQadoW/eXZ6G+c4xojmRUjTVXmk'
        b'GzDkRqPVZTSWcSIrZ2B2qkP9cJB7Tw2GHxm56c84TpOmzvTQstloXN5Ty+ZuWvbjgD5w6YzwLYoVnF0jwLCcXUEsW7ScpISTOut8sPSAtACSeaXRaON8nvMUWYOBjAYA'
        b'Rp7oApjfrqiiQ0IaVfl2a4UGehgCG3TTFYAC7e3YuhuAxw291I8BM3od+XKY19U9jHz5fzPnMtpZMuczep9z0EqM63pq2dzNavM70ZOh9a16v4tcAMHuuraJ5cxo3Njt'
        b'2hbudehnB7l2VLf97E82gRhKhrlazj/Y8W2S9uVGCasvNsgRf2kn8GD9m3jeaNziZyNU5wygAfR2t0sgANMIgCfY9tNG13saekLqaI2e7kld19aeYDiiOw8HXfZsgoME'
        b'1Xdc677bTneJ0djYY7fp7Z67raaAhLR3nK7sG711m9bY0n23u7YmYQLoDAmk4qczahdDaQrkI7t2nGweeNUGuysDOKqZnG4y8+34QAejpxM7RmOlG5BxFyfugzBUiOsw'
        b'KvSBJ0YGcWPnXm+jQmvc3/2odG2tAzJMDxwVTVe0GOQfp0GdxolvZ1GJ7UjSw7iEAGl0uM28ZZXReKgTTeZgdCL8APsf++9hHuiHeWB3MAu0LfHxQKuAmVrtdgcF52Q3'
        b'UPf1Q93+3H8PdpQf7KjuwKYiERvzWKgVNJSQ0fhyNwAHIKG9M42QBsKax3Rkyu2wugi0ZG8c4GpPL+HWc+slIsySWgK9REiV+eAn9MQrhzGCpkFqpzT220wgofUpKoTQ'
        b'emWrK+xWM/EdrjRZbLy5J+k02GgU6jQayRc9hK8c0R6rOPIZgeBvqvv4e+17smeJlMiBAmcKoZNR21Hi6I470dBt5UbjvW7FP3rrSdoLfor2quxOo/FBt+3RWz23F0nb'
        b'cwltsX6aVy5smO7vMB89tQ7KldGIum2d3npivk9om+NSLy1ZbCDAfKfbluitp5Iwem4piC5gE1T4RkBb4YGrm9x01DLd2F47rG+ySlYwjnAXaK7Ui4TlJbyUMJn+AMh6'
        b'sjqIJsjVcyeE9SKuEjrpMsNHpNJHI+juscVWrqmyrxb2n8cmCV4Y7qoqOwkG9IhL0nvZsbBi6n1T5lWudJtsLku1OXAxeRVQU7nFBTqxeU2VT/3r0RwBI0EbNxq/304+'
        b'lDR6qTpwRMSHBN5EhkWb2MnT0LFcrM9ptbtIuLHnSV7d0Z4N+bIyc6nLskoIcQ0k12pyuoyCpdYrNbodVsc+UtshciHWbcFn0Y+jXqVf6Q+hplFhn5Ya3qny6yCRqwVq'
        b'c4JcTpLLi+RCzIaOl8jlZXI5Ty4XyeUyuVDp6ya53CaXO+RCmfAr5PKAXL5FLphcXicXEgrdQXYAHd8jl++Ty5vk8hPfGGsj/v/4QHZyMbHD5UfExYS4XSglUpmUk7IB'
        b'P0AXI/v14OgoI964Q8cQR8doDccGy9UhKolSopQqpWq58FclUcmU9JeUqJX0JwhKxR/6XWt8ehDa4sTbcDM55sTil+2MMppz4y3oWBcHSKn41/mzTg6QvtisZVIaKVZJ'
        b'Q8HRSLEkIJwYCo5GheWDaF5BQ8PJaGg4hRgKTkXzoTQfREPDyWhoOIUYCi6c5vvQfAgNDSejoeEUYii4SJrvR/OhNDScjIaGU1B3ShkfTfMDaJ6EfxtI84NoPhzyg2l+'
        b'CM2TcG9DaX4YzZNwbxqaH07zfWk4OBkNB0fykTQcnIyGgyP5fpAfTfNjaD4K8rE0r6X5/jT4m4wGfyP5aMjraD6B5gdAXk/ziTQ/EPJJND+W5gdBPpnmx9H8YMiPp/kJ'
        b'ND8E8hNpfhLNC66XxJGSuF4SF0qmSEOdJ5mi4dRtkikawc+k1C3FG0YO3BS2H299/1LnTSbfCdCAh8S4dJ0eI84b1JOk1GQjhLHELPrLuSx0i8fn70Fjnfk86YjLh7CX'
        b'Yu646yPuNXV08SBaVMBZ3GJChk3CmSHeXuomWoG/5g612R2+Ci0uwbAmvOrbuklNySlME2so7sHNr0Mmo0z0VzFpSqgZEKoTdtwCzwrrhCZ9fRVdOV0OMxmQDvWZnNRz'
        b'lABHvUhWQU0mq1XjJmKWdS1hPB0OIXd4uQPLJVofITnkMIKTBGepYR3hhAcOYOo5N+uI9vFBF7V/nmDXS3jgeUbhKqVXGb3K6VVBr0p6DaLXYJBAyd8QmlPRayi9qnkJ'
        b'XMNoOpxe+9BrBL32pddIeu1Hr1H02p9eo+l1AL0OpNdB9DqYXofQ61B6HQbcW2LU8Cxch9OSETXc8ZEnmDRm6RKQeqXrZTXS47BGT7A7WCfQnhppf2a91DaQlspJqWMU'
        b'rwAuH1MjJWbF9VLXaOD60loOnp/uGsMra6SC/dcVS8prZLUSlln5ST30brm6nqXPLclktgAEghepwfEDIiVMEBZAl+XS+4KgbGKOlzV6OaPxkcwY44xxPorpXEmFifhY'
        b'tbtpCcZXrVeVD+zfUim6Q8qFzUchRKnEaOG9MqPb7HKQEDbCkQhvmBAe3X9AzpFGGBTZA3QQk7mD+AAJYVWKqHjQ8XwliIDCLjPUWOV2gGhrhiaoaKCgFnmXySs3VjrL'
        b'adMryJlDmdEs/KEnEEN9r9FPkMFLpRVkh5QGzDW53E6QTxxmYio3WUkcJluZHSCm42ops5RSp2gQSQSa4b9tqnS1d8gbabTaS03WjnEASLjiCrKv6wT46JqFauhfIYyx'
        b'd7Cx05CDQAvrUXxWBulKpzcYgHS4nMTVmwpXXgXMC5kTrzrFNzPCTCicZhe5oZULvgfE8uCVr1hNvtQeEE2hhnl8LAc6mx8Q4a+ICn/h1LuicxwvZZeSHn444W84NQ2p'
        b'6AePyTWCre7faQSeKip0mSB5PmSYnv1Ko0DpEdxdozs35fd7nV5I/RRsK9rPcOqEeAwuu3j2lTgd8kCqLWVrgQAHEMancIMlFj1Ham/ADvAB+2h0x6BeZFO/0u5qP3BL'
        b'Y4w+xalfR3pv7Q72t9sxllfXZklQ06doNau3Vod17G1gHK9OzYoBRJ/4PFXvIbxG+NvVdhPC639ommrsBb01HeNv+hcpGiGurNNdIh7moC7upD3RtUaMFNUrXFRYEiqi'
        b'm5NEtqmC14hcQuPldBN7Sq8paC8rs5hJg6KgALXDA+2ON37a79TEieMUp4OkxUX/+iJ9xdFtyDgh3Fbck0fTcjzX22Dp/IM1vmu4lB7wM2XWwpREuMx+qhPxjo96gyPR'
        b'D8f0DsfySSQSc0nHA/qd4UnNn52WmDZ7VuFTxBgDeP7UGzzJfnjy6ewHsGzRHcvntt/JT0ivSaMhUwSvKOtq01qneCZdYzOXm4gC/lRQftwblBP9UMb5UN3n6xQAsMiZ'
        b'NbEFCxYWPd0YfdJb61P8rY+hxN1uX0EkWuFkPQi6VVV2cmgKRCK3cBb/qZr+c29NT/c3HVboPwPz5E2ITO0vvTXxbEcKVglr1lRuDkDDqoq1TuLvpslLyTDAGrc+YePi'
        b'SY2/9tb4rI5D296o1V7esU1NbFb+7DlPtxI/7a3p2f6mBV8/G5/gsifAn3bGrYmd/eRtintsf+utzXR/m0O6jfagic15ugahk3/vrcEsf4PDBYdGEAlt5LyIuFSEKBx5'
        b'8/PznrBR4YSx4x+9NWrwNxpBaRyVkMWjL0+OtzCW/+qtlXntNKEz5SJyNXGzIenYWbm5WRmGuYWzFz0l3fy8t9YL/a3/tXPrHaV9vWYO0Ii5ZoDHRuVCp1/17i4WPBCv'
        b'hRlzCklEd51m7oJUnSYvPyMnxZBbmKLTkD5kzX5Oq6NuO3MIylSIdfZUW1puDqwgobo5KTkZ2c8J6YL5swKzhfkphoKU1MKMXPostEDNAastTuLXWmU1kQBYQkSQp0GT'
        b'f/c2hEX+IRwRQNQF1UhATBNdjCYnjOLTkLt/9tbqUn+rEztPnKDB6TUp7QfWMgxzcmEK0gxzCaUnqPRU/f+sN0iK/ZD0L6TcXlAbYQp5gjv2p5BRYa182VtTpe00XozW'
        b'Qk9ACg2Z281AgbrI0yyVL3prvKwj0WsndsTRW0NsV90wFZ9bCd0HWSA26DRQ37doukdInaqqBpO0cEaW7HvAr7QWrkbyvIz6ysnIm0Z6PS6Hq+IEywYgzKNp+YIzNLFg'
        b'+WUcQeRqt6V1L5LptUrHH0k3V5BLp+jS1AZBAhs4Khm6tdoegrrTZlEI+eibWKVF4ttxBD03mn6fifhkVg/qrHAGvNPzTBFrGs+Ku+qFQpPdTRPZn3BK2jequqi3fpeY'
        b'Hs9MRotz5FCTvd0TDNnLLW/fKoP+f036KiVGiW593pSiwcK4SuL3/iBmge6AER7sud+RAcAIYX95VtzwpqYuHzQyQQ/pwQXParYZjes6QdONkYE+Z9CO7G6/iho/6A6T'
        b'V93JcPWsH3PakcbqwxdvaEe7lVw0WylEzk2/DeyViyYrmWCxklKDlZTYq2gwEq+qg7FKLtqqpNTupO5klQoJNErJRWuWst2YJRiS1B2NVY6RrIg+jhiSGsOKg/hEkd0c'
        b'v4TLT4lliGxoKSXSkIjkpwyjoegpvMb/GJ6jp7/yJw3voQpWSpQyN/kaEjqCbvcJWRVapdJm5uEjeFu8IVtPPNVxi4SJq5ChS+NxXbehHck/GmWgfQ+L5+oY+n1DCS/1'
        b'f99QJqbl9FuHQlrBK3glPKv0cGWs8F3DoiAhdEdRMA2py5EQHlAaQp8I48MhrfJIIN2Hj4B0KN+Xrt5Ib99OSJ9tAV1dGgCsNJAUENQk5NhInTeMLNmSNnLlJHCBhPeL'
        b'51KqGXiD/F8jhmSlnTdZyUfmRnS2ZpIWjYG7J06fb4eepXu2vkqUvjo60ziy1Vsn8TtRiV+9G9xNO093Tp4aasgXvHoO1eo3G3bb2lN9S07UbKb21l6Tr72nEVWm9Vbj'
        b'th5r9E86cY/wOYG00/xRpNbpPVVNSMb2ALbT02R0T+178swQpcD2VjuyW0qjdga02pm1iq1Sqv4ErLXi8ay19fF9FNlr5+MAfi8bEszQ5z7ljHBB06KDP3X1WiFxjoc0'
        b'dZWiaZKSrpA4prtkwnYZ5OXHFcQDkA049JAQKP5WkqACJe1xGsZ0gnRMx8d5u1k4Ni8cJKDhY3xH8CivAOHoMCMuUOFT9s+Q1AxyoT4mZIaAsVVVgdLtO0EQEtAEfbQH'
        b'Jy2Jief3SQLODShFZ2xynqUbNk2HGd7pGYuCRSxq9yNqn9NOGEQ+y3w8YE4HdNdY96JZJ7cpgZ7XMGlMLSs2LDF0EYT9npxERiB0dKmKHOsgks1ObiVx6y4XmC7niCOj'
        b'WyOkybrwsq7OGBkGl1N+kpTQHewuu8tkBcJE9qGcMyBB6L29smpGj2PildF3Tj5uVOhTBq26s6zU7ohD0aUdU9rFCiplpLLi+Dtm+0WNx+0/TYEnN0vEMQeuLBe+RaiU'
        b'ED8U4mcifJX46FJ0W+TS+DjaGsim8VXcoAPA0vB5Rfbi2C68Okr86yRRuQN4Ncwu/ZEclhVJiJ8J8TIhHx3kgwknhhRwYMJ5D4cWkS8Qy4AnC7xXRs/b9vFEeAaUyYRg'
        b'WcDdFXw/Pkr8YrGC70/SJDAW9UNR8ANpfhDNB0N+MM0PofkQyA+l+WE0r4K8huaH03wo5EfQ/EiaV0N+FM3H0HwYQKME6EjwLGVRuFlRxlgYc3gtc4rdzhaFw90IuEtC'
        b'aimL+kA/WBpWS1kUQdNCWK2+/GQxEBgJQNL+aUa1J8wTTvva1xPp6eeJ8vT3RJf14xP5pLqgoshWRWsUP7aZ5aeQVmA8JPw4fjwNRtaPfMaQnwD3ptJ2SCAuUh7FJ1MS'
        b'N82rIkjo843wsnleNlcr83JzZ3m5jNlebnYB/C30cqnpXklaVpZXMndWnleSUQCp9Hy4pKbP8UoMuZDKyzZ4Jfm5cCmYTW4UZTlWUUI0NyNPG+rl0rIcGYSecRlQZXq+'
        b'l8vO8HKGXC+Xl+3l8uFvwWxHDn0gtQgemA8wZHRY6L7469TzQfz0gRDSS+qPvi59oujrgmLezfdTu0YLlxrcZFsNXQQM30+Q34UbcvV5eAtuziERTdtjmNIAovoMelYx'
        b'W5eRMy8dlkQmOetJPqY6A28JQ9fQTnTLMj+kr9RJAv3dmGf/uPhPxbHm2IhYU7rJWmYt0Q3ca1ry6k++dW3HWPq9jIp8+aeT1mglQpTqs6gB3w9Bbbp034HJPviORIZP'
        b'oPMjUQMN1MAWo+2YfLUrM2c83qMnIQgOcWsm4OddYrCNC/Pop50DvuuMjqM6DnuMticjFqNFmitEU9rY4Wc68VusjgxEqY5fS5a1b5Y7pIQ+dfv1V+B19Ikx/sf8Ld8g'
        b'ZIrERPEfiRR+3uzluwPdwlOqDJh3AkDHsMjKgM+Uk2UoRARqD4usrA8CVAsCVFNSVAui6KXcEFQQkE7yeex3QjXSx64fCRxscBOaPwBfGJolRjEkEXMTEvQkPi6JbhtL'
        b'pn5+3mp8DrWiunR0VsLg7VUheMd8o/CJwDPr0AP/uxODCArmJiwQT3Nnki9tk48OxuKGhUpAZSmDbqOLIaED8X16pDxJL2f42IEMoynWfbVWwdDgK4U21ESPlKMX9eKR'
        b'8nrcQp+fFKVkIpeNYJji4uwWp0z47h8+hC6j/R3j4tNj1alZwglzEn3+uQLFWrQNtdBv3U7HJ/VZGTlZOtysZWfhA0yIgcNn0PPoplsDt2vQwXnx6eQgOt49LikJ1RVn'
        b'MSPQdXznWQm6j88l0FaHLnPEG8hx5OYcGuBePMG+GDfE6hNicX1iHAkGbNcq8VXtEhp2Fx+oxhezcFNGdqKckQ9EV/pzanQB3aF4KjyxDd2WxZMhT4An+uSgO9xEdAvX'
        b'uoldAl2Wh8YL09HeXHtb82JxSxXapcMNebECXGhruoQZiraGopvo0kIaFickHbU6V+ErUgbvQFdYdIDBLdPxHfdMUv9ufEPd/rHIrIVVS9BueLYwFmaxSafLmS9E8xdO'
        b'8PumnGXwKYkKt4wKoqF5OHRZ4Yt6jxuzoRvo9KC+cyX4yGT0Eg2IjC8A8bjaPnQJ/i8OOHBzYUB/SDscauTId1YehEwYga65CfZqZ5AAm/MgVY0OzmVyUlGjm5AqXJe8'
        b'Fijm5dWr8DXUsBpfccmZlfhY6CAOHeDRBYro+AKqxVudcG8B+dRBbGYCYABQTNpWvjhsOWYlQCUn43ErmMHHltP4zyPxwbJ4MhDQelMibimIjQWCWJ9omI/OpwV+5gBt'
        b'Qm1BDIz+ZfcIukCGWELwDXzNiW+uRM2rHaqV+AbDLMM7+4+ToLp1aCtFOXQmi6Aw+TJLgh4GV8YAET8VgfZIAEPu4c0U+y0rpcxkMo8zi3U1piUMDcAAWFuX6FwJ5ApG'
        b'8RV8gUGN0xZbDHuaZE4SiPDRP0bOn5dlwEnhn/3M9qdT32zEw9Sv9pmcsvDSi4fmac/X5UWY99hi099ZOqW6pfivUyJef8hGvzis7VB5yx9fmTSsYObMkoR3bKPD3/1U'
        b'Jo06nD4sueHKNvejtPdnPZdz6ezxmZ+NLN3s/W7zmbiPJhSb294uf3ti8a/iP+beTp23POdOTHO1dve2Z15a1Pyd8u1lMTWuvyxSrhrvWf1BsUx26sEnUbt+frdf8YQ5'
        b'i5yOGO2V1xpy0uaxi1pmq787zDkocueB75a6B5W8k3Llg6nz7nxQ8/Hv3/kw+KW8xelDf3gnb8q/J3246o3i994N/sNvH9a/MuvDLf/o++5Pbu4w7H/v2X/N/XWlIW5F'
        b'61DnW6HpQ1px7d8PLb/x0bdf+MN/Xqzyfq28ND2k+JNP/x973wEX1Zn1fe+dYRgYmoio2LAzdKyIGkVA6SjFXuhFkTYUuyggHZQmiCA2FEVFkCLN5DnJJtmUNcWNMT2b'
        b'mN43m8QUv6fMDG2wZN99v+/3/VZkmJl779PLOec55/+fc/r2s5tqpx3/V878WV8dLXDOhZ7a+Knv3vr0o9kzrhQ3oB3OJd8ZP1uw5syYK7+k/au7Oq24PX7iN7991H36'
        b'9s6vFueNHvHyH7yvKK91naF8Ct3loAsOwPEB+6SZguyU6NJOlE2xEgJHj8CzSEnnGCjhZOiKAGfjoinwwJoNeJcdjEuwF1rEUt8ddCOGLrzBovw0A33dJGhVQFuyvoQz'
        b'ecIiURSAKlElA3K4Cq3mXgQfCPXAJYoRVACXaObohC8eG0oqCWjwElHGqtQRjEkiHZ32J+ygOH/IcRf7iHDhLgtwGp3zY7Ur3QSnUL5hKrQlQGsKzlk2GksW6UI0HELH'
        b'aN7bE3apcS4y8JA9Jth4oXMUREKEygOUPBVqlopdceLNvlBD6bLw5MiEq16Ei2J2srCTX6RtSp+DRsjehedbHh7XuNST4Yh4AY/rWIfyKGSRF1SnMp4tS3RN2MzbQTkU'
        b'JBM9iEeX8SxP1UtMgXZDlIcKDKX6utBkmIrnH7SlJeIK+IhRDSqQoOsRPhQ3wsZ6t5UNFHo78JxkHmpbx+Pcq9BxWrdN/nAB8t3RJQ7vAseFvfxy6EaXGQzUIX28b2Dh'
        b'Jx81uvtgWanYlsCtm01DhahVnDYLVdMWnhGznjJxEOqlfG9tyFdwsqUCVMAJaGDdW2GJF2QlualyATD1hhKoE+sroIX24Wo/LEbl25ExpsVJ4KBusDAF5eG1jDSWeMos'
        b'fE25gGlBgScn8xNwg5yA+mRi74QLqHKEkvnMj+zJOBe8U+JV7qTHJDgrhhYdJa/IfI+4wcSje1GjyBXlQAZt98idmyjUV6E3bit0dp6HMDrOnLLIQuustRSF3MbW19uP'
        b'EsnynJkZug7HxYk7USFD4TiITqILhPtUvYMYBEDjXJEPOmnI+E8vBUErYSexwbKEl8gLKvF4zBPgHGpUipziBDzwcIOWQxnBryvCKqSjEAonViYTgQ3qI7C4ku9HL0GG'
        b'DcpRUsJ64OFpaaGFp2o1ZNESW6LcKfhOX2uUa6dcz7U4dDRwErRraaGCCXT4C3CAo8VRQ7WstTVGl0W400/hcUDI2Ax8tpP5wWT1PeiQLZPVUS4qtsOqaz+11Qo3eeFU'
        b'XXRi9YZkYl2Bi1CG55L64ch9/Z9FDZDjLZdw3pw2asb7YBsDh2mGOiwq0P5GuX6Mrk6CNV50BLpFcAOdQRmaher/KRx4ahugInnCUJHcWZeXEn5YQcyPIbCn+K8pP0bQ'
        b'IwgnlEdWjzcSjPB1Xd6MhM3el4qMaRyfnqArwkK1IOnni0pO2iT9PlEL8ahB4jUzDdPiNegqI6JUzsliYjhLIpM1aT7R9WRhIclqP2OJIiw6YnvEo6OmNEiTKEMoSSop'
        b'irzQR2nylKyT2r8j+f7t1DWMAvHsA+DmNdfwcUhWtbco6zYsIqva3jQws8eyfVNvzK0PslP/oT5qtqC8KKqoClY6cyWEyQB0+8dzucV1lW1RukhteQD7Di9WFcRak1NV'
        b'jKKvbH+WOpQePA+Xv1id/8RA6k1FfKn+NJWukupHe0tYSnJ8ZOSwuWqrc6XcrfhuG3y7OfHv7/PrIiWh/tGPXQza/5Me1P+66gJYUj+HmEilY8N24k6CWz0ijgSohP/p'
        b'JtDb0m9GD1sMfXUxqNcV8bGIIrBvagfFP1Xzggd1uJE6y5nDQx4PzLhfvnR5HUgRyw4ImTWAIyEze/ldxns4ag3gqQWA28cH9Htv33euMCRpTTR1w1PUOtL8I/k/QVCb'
        b'KRd/QLgtNGLdDiAqGujJoTBXRMenxIZTrtqIJIpLbh4SFUL8PzSmpWZ7comNCCF+UeauNB6GdLMSRJe6FSohxpUeRTGaQXiV6OPBwYFJKRHBwYxJd/CsJVD5SpcAiiWo'
        b'MSXmZ7azv/vWACD14ODlIbEKkgfxVcVfMPcqzcWKJ7MnjMR8hJsT639IckxoDDlatTUPSiAPp863dbTdQctquS0+Ljk+jDABW2pMLAGnRJbAtBDFAKBlVVgRwU0eCi1I'
        b'48O4Qf/4IaNJ5BtTVWshVhCRMXPy+1+sSw5+LlQa+b63NifN5dteiJXzlHHXBRV6DxRljmLBmIozWJSZhSqYGY8ffNokjoyKoIBqP9Djpv2DfqbumjZgV1OExW6hTdF3'
        b'hEIS6Eeoy05P+ph0d+I6meBMFSTYYNDWnc59rTfs5k3ZrHb5oYtq4y2T6OCIlbqW6JwIy2xQgVqwWJjrR1Qv1AalXlR9gyZo17dfbT88AiiJQme26EjRY5LwalwQVIvC'
        b'kC78ZuUakYII5av+mvWFfx0jqQ0uiHIPwV35IlaIOkTn1ryBu5JqQx1QjQ5okEtFqBXLrDd0lSQxDwhNF0cqHtSrMx6hV3ECTBIU9wPs12j0VeFs7VH3+W7c55OG7fN/'
        b'GD24z9FFKLV6QKeP8tfY51a+pM+vjtNfhE6tkgvUqpO4G5V4eaGCvWQ8iA15dM4cXaEmPAFdg7NeVugYOkueE8/mUcs6VBbTkZMopuTYM7+z2BblHuYd4h2y9YPzEdFR'
        b'0VHeYZ4hviH892O2jdk6JmDtGy99Yq81OyGS45pqpG+U+agOKvvUBM0HvDrq5qaiv6mmHjLTkxkIu0w19xLrF0Fzb/TbPffjbhg5bDd88wBC62Ey/g9wrzM/k0edR6cO'
        b'5QgKorp+fuvZL/AsejE0OlIv8v1YnpuXZmIgvL/PAs8hctYqxkp+O1MH58GBfgPpQbokVEHpkE4c5F5Bu0zjpLIaclxB/Sz6VsZhqMZJqtOG7aV3H9BLGvP7Hxc+NB6E'
        b'kH9DNyuxb2CM120RryBfH3p1sVeIHlne7HdyYjlvaVXSJ94N2YjoGfjwK5btEFWOuZUMv++Q9GYO26xvDb/vDJPTf6RdNe4gQ0VKPPIvLlkipjvIb8WvWc3ZEvIpFgM2'
        b'Pnnt8Mkqdt449RfR98+PkYuYnbIJsvAqmm8KHdbEWiNeyqNWVLE0mXglzIT2eJQPh6MNBy6xD5wZ5wOoxcjZ0ZzhwtpIoA2uclLoEtCRtdA6TKdOf+CMcRiqn1N/qOE7'
        b'laRnOWyn3n6MTlXmRNp6yIHieFUHEHZlJcOqHj1WVJ3oC9kj6AHjgHP9bK3ssfSw0Sx7XPb4yPHqA0fZIx84DhkP+vjXZMh4sPZl9A5n0Xl0gGD7N8JZdhw2WjAQw1F2'
        b'FEYsomueCJMlQSu0GpJTE3qaE7TKCJ0RoBMPkeIUMnYXrphAz3Lcccf6ocZhD3SCVnLosI2Eg0M7ZKhVcJNL6Dkj5ESgWgU5jYH6LRwc5lDBdDhIt18xtEuhJUXCCVDM'
        b'wQkOHUHV4+gVQksQLYM2LW6TNgetHDq5AZ1jBzGVY1YrkvFOfiEKJ03OZaqhMYWMH3R94Q4ZboTUGRxcwfctXsseyEAXfBRpAjfZjYMSDuVBLRylBz3bHSXkcNgofcUu'
        b'a7O9ruxYFK6iYkNywiXm/NBhDk5zqGJMGk1pUlgQrYcVymf1QE2oMYXMGWhHNXBcgWrHk4Ya1D7QlJwE1wLcrYiNnZ15HUaVOnvFZjTDUWnJs+HwbHsxh6458LgVIB2K'
        b'3FKIyLRCb8mA81YCAbMfLtDz45VroHy2Z4A2FwSVEtyDRag3hWjBO02hcLY7GaYOnANc20mpydFVyEWVUOoKDXhE23F2ArTH/nz//v2byWJCamKebh/i/dSUZI4eUS6Y'
        b'st9LhTazCnLcKVt5oZ3JJs8gC8jFpQiwkEPxGncPImcV+FABy5/USxKnvwmV+tBEdBLGEveJ/neREURkMjs/Zcv0AZTjJeRgIEkCLqIuPWiWbk/ZghPxgYYwffzIEX2U'
        b'bi/VgvQgqJVAUaD+cmMz6SJ/1IV6cG9ecYvaoSNF2ZGjE3WhW5ImRXk6fnp4kcuAM/bQs1s+CXIW2sIxCTrqIkctT8yBqjGo0hWdSSHhFVAN57SItfqAPucgFaGmINS8'
        b'HsolKBeyIQ9dROWWKBN6oBgVBY6L2YfOQ/o41LN1yjgsQBSgLNQWuRsyRQ4WuCCFk+Cq60gfXJ1eunLQURYbOY6fI3DS941jN00Lc+RSiPwBnQbywUS31BGAmcfxmG3x'
        b'DerPdnsZ2mVhUGFHk8zy8uAOc5y9eXSq5WZ9MZdCzmlRjzPcIPWoQgegRYcz18MfVm/ehkpQI57NJ3kHdBDOLpyNe6U0GGsKjXAsaCacXo/LnT4qEB2MQDlRUAcd2tGo'
        b'22inFHWzs9yDcAB1aCqqu42nVuxK41HEDQY1yPF/Mrcu6kB7tHWgnKfHstCAm6uDjAO8d0CRhzVeKUgnn4H60VKxPeRp09YYgbJ2eSm5ex9C3Ds/iFL35sn1YvbCccrd'
        b'axMEZzSfGZPk6lMGnRnjEYpLRxeZZkfBytcKt0URjwX+It4FcmemeJIrpdEeVu643Qp82Byw8/Sw8WdeGkM8AuhQTkDX4QqZ/Cv9bVYLHMofawhnUfoE6mQEvQbQK0uF'
        b'NnTOhFYFT4nVFrhwRdYW7j7oqj9Jc00CW2RxFQq9eFTipotqfVHRPl10AbI4R+jVh/xJM2j/L3UXUUX1fZdQvXdXTMQbK+UUhovQgWq9lAc6eJdfJ4UmAeXgMdyZ4k+X'
        b'AQtUFuAn92EQ9UFrNDihcHjcX0DpeNI1QCYqgYKN5vj5DnTGfTK64T55NroiJicjB4xRFTrI01N1N7ywncBLZouhzgbIkEIzXj+TE1N4zkQh8rPHA4koVLPRtc0BZMki'
        b'BUPlPDRy0OgZzZiTeqB+p5fcBjdDrrcvLpgFVt5yBsoaIm6TuRSP4IOjqG+JJ56c7QGoMBAKCTORPjqoZcmjY6uggq3iB9dAjSwVXYo2wHs8VJC2ub6T7oqeuigbF/aa'
        b'Alq0uWi4IsAl3gYuo3L5CLpWwkmUuw3yyZkaOsU7clAUa8Ga9xRkuquccNBJqLTiOdl6AT/a8AT1KzEyclMd/qLm/ezwF05DB03WCp0d5YUbKifIG+935Bw1awTbpS/C'
        b'OQPmk6CF84gSTyQEPOdRJuOJrkDVHipXD3u8yl8Qc3pGolFwDR1MIadU6Pj2KDz65RT/n+D3Q7EXXoZoajNQulYknBQoipgbXOfUyzrPGUZKoVJA5dCL2lg5joVDthWb'
        b'OlBm6avF6UWJDOdAFy3+/nlwhVEXGE6l5AVR6DxzpjkPrVMg38YJjvvSk0jJJmEUnImi3WCL0udDPj2s9UMN4nk8algBmfQS4dO56EVps61QCan0aQsoppecTPBwyqeX'
        b'cOMco6zaxpupvDIPjgVYWcDx1WyG43FMfEK0uMmoVEtH35euB9AFR+EkXg6o8o9y7Qa2zhrUxtraFx3QhsMoBwsjZIBut0Dl5ABdThaoUgedBQI66wLXY7xneIoU57HE'
        b'lLrC2C3gha1vLTWpGbs49vnvp+57/uVf33nWMrnG8NPmm8s2fPq98UG9Kc/NuGlvOXnrCz+iuojRm9xvFlucfe+mm+mmn2Tf8+t+LPjyWs4rn9bu/vp68djvLIyzpnlc'
        b'CGwIXuj/2rbmax0mz79W5TaveMpui1k7pz7vMd16ZpLH4V89Ct0uPHk/ft36mG2h09+IHd3qP+2Mjc1JxaVRt2ZYVsXkfz7yU5c3Xvu7f/kE04+ikqaU2D057svGbx0W'
        b'rlpcmrXCWR5QfezOob/3tMlOHDt7xnSW09u3fGc8X3P7+XjX9tbf68yc5boXpOeizQo/mlhQ9F2j47bx3zv99HJgfVLV8aSj4PnCwVbZ1+uf0X2v4fWa7I2vxc1QLNir'
        b'5ffGjg9HdM0Qvhw9vt72x7shsQF2Ka0b5nituuZ55GBI74j37Dd++YL177mFHX+7aRa4rnN5zaFR90ZFrz3JN25wFd/f894H42z2rtSL9v5CFhS0R/a35R/HoM5/3G3c'
        b'G7O1S9T7/EtBfzt9vvTiR3t2LnvhivvZuZteuPXPN4Oy33rm2IIA7+5/rX9674YXO6/v2j8la+e7eWtrpNfCwOfdhIWff2b2z3vXWlfmPLGidvumDXdzF75tJ7kWdu3Q'
        b'qTL/puLzVi++/YnB3UslxzdIun5271o59tV3l730e8cWh7+M+sc4w7Hzw75eU7kmZMltu2Uv/nBg3fxP//lGrOuvQfvH3TSrbqys6fzZRTs5Os4ku/JK9d9TJvzxo9eR'
        b'DbnLelZcrIp98utji3/88KXyv4z55iXv77mx7Z92lFXV7Aq6UTxD97dPpvmfmLD1x2fezv3iuesTvuKOxE7O33Qr/c3Qr0K/Cvmq5fQm1303O0ZF3ezoeMr2lWcsnG5O'
        b'1L7zSeSP2V+9Frar+dN6/bXZWa9PfHnqTec4n/3NwmufOEeOPeP4qv7EMk/dCWMu/8s367Mmx7+nzE55Z4e8u+XGB68a2+h8KZ9JPQyw9NO7rM8fwne/tzZzh7CGLOoR'
        b'gg6nzfPyg2ITJdWVNbpKPQ/sk1ElXqnwWlusWqq6VtAkN02GtoH+M5DrSqk9xAsp3QrWItNTVE5nWpwWFEqxJpCKWhkbyxaom6paQKF+iXr9bLZl9Gf1qB7LL8oldClU'
        b'siUUdaZR5wt3LG51qpx7ZuxxFyude1D9EupcgjLRqalYYKjBEoeSmkSYOGIa03jr0VnIs7K0lUMe1g0d5Drr8PQWpVCt1XfhXitbLAWUk/3HmrhbFAk2eAnqoaWKm41a'
        b'+whkoD2EcciEobxk4saKxa1c4pwCxfi1gwg6fn0Sr4Sb5CXGAlaulLq4xOD6W9m6w3FWCglqFGYr/GnhDROg1soGb4R1KhobwSYFblBHm8QA1KtAhdJEfWhW4IU/Ixrl'
        b'avC1gVYJ6nUwpc4UK1F5sNVA+3BoqLGHCNWhUjhKm3MRnPHw8rMhd+Sh6+gY7mvZKgE/cmRSMvX3LPVAFXijxPII3k1sqPBHpCEPn0SbSGfW/V7oojaWsw9oUTcPvLKa'
        b'eLHsiPsL8RnCm2nHCMgW4a6rjmWeyll4zylEONU8OxvKlIjV1C5tztBPFD2Cp2467ugolgL9rPFuibUfXIhsLzx0oRcrLdCIGmmHWo1EV9SSzpRlTNCRIeaHhSt0Ga/y'
        b'jO0mAzUzvrljKXQQT9A2G+BBhsrgNPMh89/DBnEOuoA1i3y7saTa1P/GQxgN19E16kqSgMdJi8qTJB0Pm4EWkgG+JHDSiZ6+aHkQtzLqv4RquP4uTMR/SYKKmfdQKZQk'
        b'qjxqBrjT7IQW5lFTu585bRVNRRVWtnJPRvtjiLrwvgzponj7EDqi5y3Eoni+DyG5s0bXp+NmkMUJUO06g/EB9mzHehPbYEdAF91f4eI4NlE6A+QqYQR1T6LCCCIeXyTZ'
        b'+eZBKlHEATpVogi6KqL+MqaoYP5gSWTPvD5BBA+yJjoElqParbh0/d2XoCPRFA6JjVH56mRiK8aC7FFUiVsZnUGHHsMOVWnFlrYjqEDLy9t7lwde2vx5yzR0hbVbPU60'
        b'j8UPilZI0UVhJ9ZHTsv1/23YWPn4/yAk7eO/9J0oGA7C36QmNwIRM8TkNpeYk6WUhsaI0iFJ7gvkV5D8QX9FegIJISJAdgx+zhTfS+4UeOG+WETg7Qg4upiXECIbinZs'
        b'wH5xuuSdMX5HXJCMqYuRQHMh74xJOiJjnJ6ekmYQ/8V36d4XC3pKRycD8klEHJx0BalAwHXJTx8Yr8Cb0M+qKzj9ryWmhFZHT5kii0FUm/kGNQszUjLPJuZ/RGPKrKjD'
        b'EXVqitjR5wLRF6jVd84y6n+td+XSfiVcrCphUoa6UFZqNylqGT2IP9oMaxm9tewBJIoPajI5T6PWfIc/Q6XxPOQUlafYw493iqqiXX5T0ODY4ByZTIgSQ2JjKcpqP4Zi'
        b'XMgYUrqQ2AHgqwywKzycHb+HmMdFpA1JlDnNWAQHr9ye7BEXGRxsHhobH7ZNbqsEylW5SqQoIiJTYom/ws74FPO0EMbeGB5DCBeHsif3L0RMHL0xkuIIKANGIxQsipSh'
        b'JJoTvCfzmHDFo3MjEvgDJ3MP6vCAR6cihoDR4nyI80OIeViKIjl+O0tWXTWP8OBgOYHLGdbLA7ePqj3I25g44vZASLqX4WZMI42ZHB2SrC5tnyOJxhSVdaMIudQvimDc'
        b'0AQIXu6AJlLF40YlxackUBi9YRwrkpJjwlJiQ5KYQ4oiISJMjeqgMLcgUfHWuAlwthR0ZWcC/hiRHGYrp50wjEMKadDkCFW/KPuduq3FDSbBVPZ+eDyNBk4g2Mqa0hzQ'
        b'AQ8hkeQ5TSSSur6ML/k4ZLhC5VR1dMtowWC8LbPmE76/RHQcNaFmlKkhFILGQUzbneJD0ikfjcqVJk8RXDeXiohltTPRHsrMJrqPnJ64F674Y0Htkgsq27DMIxmLBydR'
        b'k3Sxr/UEOI5V6+OuqGvSLnTByB5K1lKL1EJLd27t1uk8Fxy8Vc/Ei6PoD1g0bsAyDdH/AywWzyT+0CSehoQqaXNTtorhItQsp49/PlnMWW81ISEXsX/ERXAxST8mCwoS'
        b'ZZjh+rfpf+3Rz7A3cfvg19qXvuH0jmhF354SOGdO+yyfj8wvnOHzjtp86XNxQ4Zr2j8/q5RMO7myZZ/zT08dcqyUFBbfemXLxwvHN+d/sLjSy225RUD5dxmTi1J/mWxt'
        b'OunZ1sidJ67k2teMCyi+2fz5ycoNH+be/U2Us3Tck/bvymXMRboXauRKFQplp1CvcqZDodYZVNAYiUXSy1M9vNR0wee30vPl+VhKqUGH4GKfy/GjiC9n9KggjWXWwxsU'
        b'xPprY6Gyfo2A4ig4LEJNS+EaFVO3QTVqUOla64kESHUtSyhhMnDVGCym1ixU+9sTZ3t0agdV8XxQN+S57lK62xNfew4a6JXY/dAxMaWPTFOwcUaVzKO8bh9UyLzmRQzh'
        b'dQyBS4wF+bjhCpSPqqFpiKc+EXNRCZyjcu5m/K4aN2vAjKGSLhVzUQuUKg8LHxa1eEeHBP3RyUqlGktNUs1+zpnKMgS6/z5+FRGZhcgqgxwZ1EkNJHu0HbjJD2GoFNgd'
        b'fZttFv7YSDZbW02bbTr39wfENA5TIuKEivecLXjTGQCVoIqd7fNXYpGzInXkrOiRImdVO+3PYg07bUBEnBJNdSBke4qC7bwRdO3DC7XbMg+XgH4w7MNtVxGhMWGKLWGx'
        b'MTgVRuerwp+KJHiSYdG29A5bN/LqQm8bDt29X6rK9nGi7o7Wan9Hgj6siKDFjE8KJ1/gjUDjQq1Eqx+2DLbLg7yDKQJdSkJsfEi4qvaqBtHsS5jUzyWR7CFKf2BFSkwy'
        b'w4xXF0rz9vHQUrm4BAZb/9lHg/70ox4r/+yjzmvX/+lcXV3//KPL/uyja91m/flHZwebDyNkPcLDc4I1u4Z6RDISGybyRIRbm1sqh7/lAKdXDX61mmWUYXxtzZcnhVAg'
        b'74e51Wou5hoi1bJVIXW2rf2A2UKhIBl8LptOOMPUmJA/11LLAoM0FKGP7pusMawcbLrFaHC5HRLKraakVQtiIxmbd6SvNvUcsJ+Xs1fLJJSjRyS7bPcpoGCrTCB7JYeq'
        b'UCFqo2LbflQ7GVrs7e21OMGDM9kGtagACmiYLRyfNMrK15YcP1YEQznvtTmVSXo5m52sfD0F/P1BaECdvCM6gppoNlqG0GXlSwwbKMc/mF+EilG1XEyPcFzQKThED+Kg'
        b'WYsTmfFwCWUsDoReesARG4su4ItNydBOoq3KeUPHyZaomiYaH41OKmbhXY+P90bnONQ+E2rp8Q46C4WoTgFthnhrE6CeRxkLLKFOn3pcTIc2c1TDQSlzKkCH1rBz1TpU'
        b'yCmgKpjIncxTItZHzk6hUDtKxzJh/zJWo5zFWFA8TKsAFatR4YBSBttPRtm4uWhp6qAMFfUrjR40WqLmFObo0YkTL1PWYiSWqdrFcEMuYodbtbupMbMv10K3xagEP0qS'
        b'9cMCSfeATPfB6ckxEuY7keWyUpaqg8eASIcft8oOl6CeXlgEZ41k+gRURmTNw/WEJSvRedrQqBG1bCJHjDIDnhPp8ShzyhIosUghJACAiwjZXkQIDqDQEuTMGkvFHJxC'
        b'JXuwzF0AmagblaHjgfhDGS7WGSjBQncZ6jbWgvJQLX38gkdWug/BaVlkPhKLjsaG6PzM+JhfajfwCoK7efGjNUE3e0gwsva3XYp7R/bVu114+i9PB3xrum5HesChM98H'
        b'O996KoQLmjVONDWj5TujnNyqKu335ZU/z/zs5l9f+CVt/4kIbduG8OkfZ2z093Eu+/r5TTv9Gz5ad9Bx3HmTueWfzU1cPbLxgEHKPytcR3Z4m11+s+Wtzx0NmibtshXP'
        b'OPCP8yfviPPC7N6dU1L6+9fnOnt+X1Z+6l5s1KfhK74e9fycBFiQMs/tpwnzFlwd+6Vo3lcvPZHs9OxnWwJn/5Tx7m+V5zoc6+O6Xj9VMjpp/7cfP//09LJNkpde/ubQ'
        b'Zpc1n7S7xNd9sfkb2znb3ns7dfGoSBe/33JuvCi3+YM/PHPT853hchMmpV5IQBVqpAQeXUGn2SEDFMMRasTEEzMrVHXIQE4YAiALVcejHibyl6PKjVZeWLwtonI3buUG'
        b'Ts9apI3yISd5BMnh6HIzpby/OIR3Xr+Aidul4fOsWNCoGGXyqHEEZODuO0SzjELnY/tCbEl87RHoQFf9OGZvroWspVZu7upjE3Zmch1l0svT4ShqtkI1PDmAICKyFPIF'
        b'dCAYMYEd5dlMUMiglRxz56/w4uC8A64oGZ9RK3ej/IS5eDZA9ho4jifi+mBq/zWFeim5IsFXcnAxr3BwJB6V0SMKOL85llwjyeUuhFYOSsKhmzVtFxbo+4JWTSxZ2KrI'
        b'FTVCLguN7sIzXZFKjtxRPWoLJL41R8JYutdnQZECFaAcUp7DK0ZwcG0iz566EIFy8VNa+KlzeMBfw6vixGW0VeNwv1Xg6a5Ho403wREOanDK6cyMXT0bdSpSE0lulVBs'
        b'RnAdeqCLXcMLH8rDF3FuqAKvH/Uc5I2NpccLc+CkjCpXgVDaX78iyhW6aj9MSOeDvOkVWD6m2kewZu0jhmgbxH5J9Q/8K6b2VWYbFagmovrRo8GXuoLKYqn+xU/ge+8L'
        b'93eNGOh8jfP2VWGw0JhMvf7SddKhAcoLdZjEdclVKyyH1EGUOfjdXx+gtXQM75evoUxYfyN6Cg0e85WPHoR6dUe8xc/D945si0uQv7+br4uHWwDDC1WjYd2RJYTExKmi'
        b'K0nQ5x3dfuGH1PipDjftFyO6fyBqFgXRIsZPqpTROrLGMvt/yUKftByX6xwJYA3Fn6TaRtSSLv1dIjHQMllKLPBi4U/CdooNDI0EA0ImJ+buz9sv5U0mSJnbDrSMRodk'
        b'06BuoIGC58xWiGPgQsQQx2M95V+FJT+QW47gfDGMr+NiJcoXe0+wvnTwD3mvp0T8Yt/3vTciuF/hI+l7k/BR6vem4aPx+zH0/dhws/Bx4eOPywhrXbYkkg+fED4xU0pw'
        b'P8u0y/hwWZlembTMmPyETyrUDnfIJihiEqwFTwufTnGxtCnb28xMjiB1ETY78lyZrEyIFPBTI/GvUZlxDPtkjFMzLtMp040UEywvnN4sglBGUszWydbPNs42iZSG24Tb'
        b'0pR1qKevhHr+joiUUOwuKcEZFXPrZdQ3fvYdYzI9XCjjBYWFi4xIujdrgPw59AYlWVv/m+7ZYmHWKUYR76RIDqd/Z9nbz5rlRGRipx2KcCcyZWzt7R3wL5a2Z8tFd8S+'
        b'fv4+d8TuHivc74iD/FesbODvCK5u+FWHZLnFz9d7XYM4iZgQ7mhRHfSODoMGjsFvtSKxJq14nGwdSLbipCNknpWQl1Iyc8UevgEMKfIx01qAF7WBaSXV0AQDXFc731sW'
        b'nZyc4GRnl5aWZquI2WFDtIMkEmFrE6aMTbQNi99uFx5hN6iEtliHsJ9li/OTC33pNwgUpyxpIwFfxA3k7efi7L0FKw33ZpBCuyzzoCXEf1eG7CQLnT8xLSuScaK29nPw'
        b'K17zSGINfJI3w288SsqqF+Dhu8Lbbcsy50AX90dMygGv0UcGVPne/EEPuiTFKxTLqDYzMA3v+CgfRRRNyYGkJPSlhAt4lqRlOKg97pkNX6l7ozQ2nlw2IBUy3JLOa0h7'
        b'QdIF8u2gRBbQRGYnNZBrw2fucM/qMWp6Rzs8IjIkJTaZNj/ty/+70S5UxVuih85ODZOlqh0RZyTHNBjsYkEwP2pvokEwsTwndnrZjV++3/EBQTB3pIQsNhmP6+Ejw8jP'
        b'SobsOnA9sVU9+4CYGFyJ5fidwl6zBJDOdT8ghOJBeTZosx07UsO2Ha3eu8k4/YyUKdB3SNCFrqp9iX8uDbrow3GjGG6RuuqACt1HCqhQRU0f1NZg8vRg0csxuyL6GT4Z'
        b'ZxE7qyIr9AMMnQEqdmHzBMogQcUYhdPQG23MB80icwtXN/mDbyOz8KF3LDC3sFTEkIOv1Pm28ywfIUk2sc0tXNwffrNyApObrc0fls/wi4u5hUfgYz3h8IAnHnWdIEkM'
        b'LvRwNmWlXYwZkFhYupKtSsWEMNyTZDNljw0eNglJMfFJMck7GdiwhSXZogkPGNmkLTWbGS3J1k3uIRupJbEpW5Id0FJu23c2O892lq29k/IWzcn0HePa01uVqfZ9PY9+'
        b'zZIermIMCkNZNQ1AF6x9Zioo1sWwzUNPNZwGIhPQSaYZtkKJLDBsmfqwKZzUzLdD4ScIFIT6JF/DQT35h69R0kJi5qfmVepFEBGSTAaUQkXp1g/Ng5xjDwNvQEy0OB2C'
        b'I8CcDvoxadDWMQ+IiCB1TYntxxKnMSkX50C3FX7+67YQyiK/ALcthK0mgJZSfeDPuOuGbSS2CLH2oexSSnAYVb+p1DelcVnz+XifwZkeYrAU+uzBloPWFMthPQxoDyWw'
        b'eapgzHeDlhhLVjvVLcMAPyhxPrC4qiLyjQ6JM3cL8h/GcB5nHpAWk7wrIimWdlzyAwrPFsRh5hKeMB7JIbE76YPDr3CWw49ZJUAJ65A+3BIy8pVdosYwYWdYw9QomTlM'
        b'9EMjH/BsvAZMjUc9VMDNo5SpFKrhOyhdzX2iJIPsy5eScIZGxMbHRZGUHmJ8JxKKzhCBytCXhn5AB3SthXrUDaVeUASHRZwAp3kLIyiipvOVAjqpdJCYCnnURwJapcxJ'
        b'gpiGVqOjnhT3lIKeFkMrXCJhkinETxNO4w+tBFsAFcDJcdCOf1pQrpjTh0wB8uVaKcQ+AafGo/o+l+DAlSok1oEwoWqM0H26xKznKXBzUYYBZHqiU3KBFtUNtaCSZehq'
        b'P1vxEu359JIMOlAFqoFGtYV5iT9cTlmJL5mtxbmrcWT7YugC1dE8Cfr6/gQL1sLGN2gvOmVhAXlQYAd51qghUAk1a0OMf0dH8sbo9HJmeC9CbWkMtJQAlqIb6AhunF5o'
        b'pgcef/hIuDHhFEFWz1N7P5dCjpo9cQkPq6BMLaCaoJm623r6QC6uup0/5Hivchf5o1wS8wfX0dmd03GyYhlUwpFNMYta8kSKOpzKz6NHTS900EVLjdyiIku/jCtZ3/Sj'
        b'Z9vBl+qMnMNH+k830kPtP0ifH5W0LK117I5vfrifLD5YHREiXaQ7JrzpuTUvvDL/+7a/Ni0uzH2xpOH8uoiP3K9Hzh854yXtr+XHO5flh4fYNZ+uOqF35erYiQ6J3+6f'
        b'v3JhQ/bCt95LOTL/9jPbrif9/LZhTf3h+sBXP5/+6z+v5v1u09n5zoeeNaZlRR9d2WL/rL3UZ5Vcn3mXH99jZGVr424jjINqToLOCPbQg6oYrmDDZuICTtCXCWi0NfHx'
        b'0OYM/Hd5ihySlNCBULJa0ecZj06gXmbm7YACal1dBU36/dEL0ZVVSleTY3CZ+pq4OkKZytEEnTJwRr1m1KF5BAlN9OqHm2e4GqfSI4pNQ9U0a5cAfqDX/row6rcRBpks'
        b'UqAaZfkORiMMhmyRq78vddhAp2J1BqAaQi1kK5ENGawh3HChWUUY6AwEoYQrcHGMuXgzF8wgBTdDgSk09De/o2p0WmnRHQl1IeMEnBOZd9fwZR9+OZTMoXbulegU1OP5'
        b'jlU7IZQfAdcdUIHrADQN3X/LAqeG2ls2nFa1n5MYE0uciHnIEuIFMS+9LxHIX4H4lVCSZgNB4M2G0YaUAHNKOJxwXpNdOWYAqt3qB6pjjRMfUx17HIQ7Rq92R2sLhfYb'
        b'Dn6rAr9j+HaaMlSTQ9s+giA8GJuOmK8C3J3974gJ9esdMWGBlWtr8sxlfq/EDfaOtpIsPKmD1xC6b6jaVAI5deg+0yP1lJqkPg3RN8g2jDR8zAB9EW0z8QfnNemTzuHh'
        b'ioGU16r9VIPlTy2JDVVLI82diJzoFKwGXQnWcN5vrZRr1IBexM9yqFvqYPpGxl5MVPY+aTWZtGayUpZ/JC1JKd+qCX4fpigxfi/2rAYW3hCFeWRsfAixIphTulkln+Zw'
        b'zjYhcQO46waT9w5XigHagyZu3eSIHUw0TlbT0W5nPqLDOH3ie2LCiVzX1xR9DICsDuYWlJaeVI3KbVP8l9va2k6RDyNxMpcJ6sAcQkZTP1JqdcqMdZNJwn3XNaanfqaP'
        b'RFM5BJTuXAMpNTWmYeHvttyNnOC4bfEN8lnm5m9trlJQGO/osC5g1GN5eP7Z+ATmwf2AFHZo0vmGIXp9QHLkn1olJC38II1N6bWshs/TmJqKVVyTcmeOW8XN39fZe6gi'
        b'p9nJ+RGVOxUNGGsKNR8zGbDKcUPmBdaHIyjldnCwb3wcWSke4P29I7kvd8rWS9ooJJZ4XJMFQj10I5Pit+OmCg8Zxk07NoXZ0KJiUiPiVCMfT81w4vpjERYfp4jBzUVS'
        b'wg0XQ7/FrTxswVgy/S0P8v7VVLJTh26NCEtm64FmXSfAz3GevYM548tl9SFlsFaClCrrS00BZG7iRVFjOpEpSXSu0dnOeG+HVfjYzuRkHqBUsFRs9cSRfSfOJTYWT76Q'
        b'JKZmsZs1ry0KRXxYDO0EtbqXkBRPSOdJK+KmVXY2nghs2GtuzH5cjua+WPELSUiIjQmjTolE86bzqb9jvua546Ikve/jjiWbtrkFfpVbm5Ot29zCL8hfTjqDbOHmFsvc'
        b'fIeZh5b9Ig3myYfiKT7Aw8tZvdQPYl96kOfoAK1TqlHrnORLvYt8ApKUWiXqXUG1SpTjQGUhqiCNnMuwZOyX79pYEiRiqia6vg0uqHVN6odwKQp6l9MER2qjQwrmIXXA'
        b'kzpJrUCd9IrWRnSGIdBwUBFAEWjW+AVSD39UgfXCNqWCqtZOl0M5U1BRNZxJIfSr+Eo2aoV8RvkQSEhBAi2Y17mXG+qysVztbu0ZNIy+yggjJBy64kbAzMvgKKtNMeRg'
        b'Za5l9OY+bXUznEwhTK/o2BzUrDm7AXmhk5b9s+uj1llloYbbkEs4J3sTaEJ5qJCeoFg7bZWhao8+RRiVp+wgmR5YR0IVCQSRjacfUYZZIlpQAlm608eiBt0+5RPKRy0l'
        b'7AH42iljlIXOBKK68FUod9k+dAwdRBfxz2n899C2Hegwql8WuhnlLUuKWbVq6+ak6RtR1bZoI6wiLx6PjvvYUwU9zRKOynTmQFuCnsAJ0M3bwQnopTAbTxiZDlsqyB2L'
        b'cpeiI6Eoa0BZsuAUlJH31Aksa12wIWSbc6hx1YgxAuqhOW5CTXBChk7AAZU3mt0aaEshQ9gZVfXzepKvVmINJaSkBMLhBH1DKAlUtri7rQ0qWqOyGBBDAekcJZGMGp4H'
        b'HUDnpTQXA8gxhUs7UC4F9YFevQ1L0MkHwkGR5wIH9Ca0omz9FXAOpae4UE3YNdSrP7tSIWpcSYcMTtILf+GAVV4ylEq1FJ4ozxiP8Two9cf6dR4PNxL1V5hLGapKoWnU'
        b'kHTc+1D3VyuTw9d7rElyKEuGykymQ/0odA6dNR0l4lCVzwh0do8BY36p2xikGIrfJMBVqISTeBoUwLVFuHMOQiZuXeqSh0pCOcj21/NHvfop3jiNdVGou59txttD7mlj'
        b'q2RB2ZI2EBYqh1VSf+Bkwc1Vk2KMjkziKDpR+NoIFZLFKvdhEn6EZOEs9OKk/T1NUDfkj2LzuUkW3GfwgSw8Gov3Qj1126EOImM2ofwhBD0u6ChqFaFevMQQ+seYwqVp'
        b'gqIe61pL5x30WdXj+/ZSo3cn7O7pXfhrusiWP2VStsi1Nj3vnwt0CqeEe60IF3lejXOcrB/4kzR1v1ax0dn3j3pm7UgvmzmRX3X3rcVTz3734k+z/1G1bqyn9VbnHwNN'
        b'mhuX7vvmdFzu3IAVhUJeXuWoFWnJdWY296ce3Lo+qfM1n2mJJx1TX0nrfOXWguoZtftTj5WWXDhRdPvec/Lbr8esmD73quv2Vxte+LjeuOCDAwHzL6xfEHDlsrXhK0tq'
        b'LmT13npOsmhZcVT0jZMRB1p/LJ32VVPAT6n7TBctWBT/bfeTsw0mwoaIwB4hfveiJTq9NSUVnU6pkvd0rnl8u/yZ6IYvwt5/548r3yyU/zwxffbqN8x2flCwIsLk+6aZ'
        b'zYqE68W2y08Ie/9174mx1V/chF9kn5z8mr/X+8bvJj86vd4IKd2dX5/bmbntjt98yX1Zouy3Sd9Ouvf1uI/jn+tuO/Svq2+8mlpt6LTkh+rKGVXP7rk9bc1CYbvzV67f'
        b'Js0qCZSEbnr1zb/kJaa2vbVm4smSCwHe7reO/iTbvTxpbPvuCZu1v957Y+R+VH7+3t35xz8O+UT/B3hva8WCX4P0bf/g58U3j/p8n9yUmXw64YxcZTOCiqXMbCSKRSeh'
        b'hN6wajbc6G+O4mTmqJWYoyainmTi+/uE21i1Mao6xBmd2sK8K8v2m/W5X3IyyDYl3pfTxMxL8noSKsdbxA15f/tPWBizoh0nYFGEfWVZ1AD+lURRgBRl0gRszf366F04'
        b'WUosRYBYEklNaE7oMjoziN/FV49YuhbiQpPHvddOV9rgNqAyladlCHSzwmWjjAVWUI7a+/w4ISNBm9ZLSjgurPBE9ECNYjiBTnOSWGEKHLRgTpjtTnCJsaQIm3koW2Dn'
        b'ga4zp8lsdGJxn20NshxVXpN2qIsCSIyAOrikiTOEWtbq8LbagkvEsCg24Hc1qhB8Gn8fDGeMRKPWhtIarEP1Tl5wHnVCkTXhphNb86jTBxpoSdwNUf0gghjoRdXm4s1w'
        b'eTzzC5VBGzNxRkCX0sR5FVVTE+AWdNbPy9sD5Q6IXUMX9xHfSXvUIbELQGcZz805LXScDh28s/ih63AKixIGrqLFkBtJs9kMx1CbMiwtDZ1ikWn73WhDKsamoXw7Hxu5'
        b'4AhHOcliwTwUXZFLHzkq2vA/4553UIVTWULkRM3GwRW6vJ5Ag+EFPZ6E0RsJEpGUNzbSY26fIhIWT9g6WIA8CWknbp4SZXC7kWiMMAb/Jb+mNHCecHeY8FItAxK4JihN'
        b'j4IBCbTnpffFgoHAQtslwq4pGkxvgyK1fR8W3d5nQ0vqGhjw9ujN3z8ovUtDZLqGoPQqYuAksE0aDZzp3GcWw5s4H6HawzsAEesqtfwx/xEuUqJ2BRI9Mup+lFx8L3iI'
        b'VuEfEYcVWsXDzHvUlqDUX4j2GqIwX+vj/RAlhbigTxyipFj7ppBAe9TlbO3V58q5iuLprRnfD1Evf43FkOBTvPBe0h8lHpdC0o3Uienb86HETs3Lh/f8ySup4OAA5f5K'
        b'wQELFpTdDq5BET1Bc9oxnVxKtsXLr20qfkFl6IgncVuftllr/nxIpxrOHjhgSdLHKcjQgYkcOmwMmewYqnsUXITS7dDe/2zPBXWwOOGVFPjO3EwcrJe/l2d0fqgSr5+X'
        b'ZvuhqwRGk8O6Vi2HblgvoiEqU/BOdwBKRRvQYRqjMnYHixXJDYEymQ6WdXh/XWgg/uIVyiiSCqjUt7JYILfE+4N4Jw8HULkDiyE5Dw1w3ovsL4Q47hTUSEwFvSC4wRDn'
        b'MuHYrgAoFBMUJA5d2oSKE7AyRi7pQIt3QJqCgd8x4DtUtp6FynSgQnRchrr7jvnm2bBaXTYzw0rgKTjTLyxlsme8UhVL8MAXz2JRTx3RstgpgYUOXV2B0mWQiXooEyTO'
        b'0RLK3dhjBQtROgGvgfI+FW7nLkbsd2wNyglAhVAWBIVQHuTDQ4MtJ/Xj4RqqQ/W0+bMTirjxPBfs4Bgct81mBNN8lwdM5Vw5bsfPsuApX8XK2ZdnnN0JQqWFaVyw57gd'
        b'k7khxM7qaWjOKYmdTfHE4+q4PXw4F85nCWO5kyqK50gsaH5GDgQI345zeJJ3TFxEg5LkWRyLPwxmqSZW/kiJ8lyCYsYH4I3sDMWMZ+eTOmrBuMSKiEC8/7wFcB1yUe4C'
        b'yEpdujwy0SNpNWrdF4cOTOD2zDJCV/W20opdD9XncPdY/GV1sPfzZj6stpOWjeassfLvYRO80WnGSo5OpBlL4AYDRRyIiLhkuh+0RzHsvE4sSVTL0DXffmokarVi9gEv'
        b'1CuD9gBoS9THkpIJv3AU6qbZhYZTW0NCsFVwbLatNicXaDzSypQVMhIDpR5JyXhO0UFWhQpHyrQgX603uuErdEDkoJw9eECcN8DjT5sTzeAXo1x0Tc5TvdspBHIVvkQ0'
        b'FNAxZxlvvjrt3+rHKNyPSb1kC7hBXp7iuSH84qTn2tQ9RwpvB9WmsmjoSIU2Q4EU3hH1bKNTWx46QUaUFTyh3EahqiVwnNXptJAKLXrQpo3n2sWxUIpvGIXOUHBcOCZb'
        b'I+OmQR0WcLlVm5LZTDuRYCyzsIRuVGsFV715TuoprIdmbepsgHqNEqDFzhPa8QVUBhlaKIOHivnQHaN9wlhQuOH5/sOYsIggr2KTIJPe9trfj3196MChsYfGjvlLyJPz'
        b'pxqOePaN8+dPFx2cOiUjb8XTU6q2Xnj+6coNttGvz3rqTGiBw6HKCxMcbDd2hMYUyPZl3EhvCt6+9ueagFtTRflvpbz8096Uly8p/na9xjH3jTd6/uXm1nnF7rOnZcmR'
        b'R8q/WFvepr87fWGTzWk4/eFbH91tKry18qrPxLCLlsufflLneccPxq61dTz6222vOUH3nP41UmaRtO9iQdE+3zzrJ4IUPn/kHDwVapmYcrb0fOPBoJeCbMe0JM797m7Q'
        b'57bvFW2rr7iVNOqNwqjPtYO+3NQoivlo/MmQPa9xd6u3zssc49NY0aD11Ua4s3TuzjjXux8Erph74VznW3XLLxfGnQ/MLg2e/8rhhrTXzVK525Fbjx0KjruwW7bc4bUN'
        b'71/J/NDUpMb/9+lNNq87xedfar70YfvfNjz3k1brkb/dPDTLd/3Wp7JuuCw8OPfeEtPfPW0+3X+68PrLre/DqR7+nXl/f9V+dsTd6pUFzwdEvPWCe9iLnxh0J8LC3rAv'
        b'X8+78+3MleUT3vS983Te658XvftVxieeXy7LbHiff37xKO9zq3+ef/OdnPCsc1rVI7widusWm2z/469mHzhdvVtSt/sZ/zczsrR9PrF9KcjeUOcH+0obLdGXR6bMvGjW'
        b'+OsX41JWv7ba7PrGEXdf2Xk87eu7pteKQxYXtfpVvtl6bO0H2+v8uHcMC8r3VGgX+n4VPf7vkxtn5qdFl7WNur5Kv2u3/024+UHjdwu1Pw7QWv295cJZ367peKH27uKV'
        b'q+JtPtn2k/CyyR9CZNxXgV99qrviy73bn67/Kie1/NYrfnNsU212SEZ8/unvkwNc/rbhhft/eelph5fef7O3Xic3MaMnYPXbeW9Z+fgn5u+tKm0bW/LyfoMvdjaOfvJF'
        b'L7ctmT8az3r7g02hhr63+e9nLXlqYsS4ndtD9s2p3LzPVGFtumvPpfaabz/qfDf11PR/tr22+KmensulaY0ffhVdvv3bE6+93Hz0WaN/ZP/qdGv5M8e/3fX8lqPHf9rq'
        b'+IdVru7mZ4q2yEw/Slvisy/K41bN10uS/lXk/fH4228cmJ8x33/+Rwt2lP56bO+Cs5FNOQGpLpdf3/DquI6wXaWVxvPvPBu12SLhbtzR3e8/96TdT9+ljt1+5Jxr7Ws5'
        b'qRePG8/vtr6tt2HR9Kz2OM+3vz1Wt/vND+Xy7pSADw/t/75MqvhbmcmCF+SJUD1retcOz8zruz2L9OtdK99s9nvzidpdST/0tPxr7rNecTovhtR9871O05Z9P+m85tnz'
        b'6e6134Qk2nUXp3h+fUa+sz3rvt7r4m9WLD0a03n8ydfqn6mIybgu3Be9Frnkx86fVzz3hInfJx1H5tZ/hFpl+9+fcT9nT0JU0xPLRx/+8v3Sp78ePff9X+98YTLvvdf2'
        b'xZzo+UZS7fbVjI7Ub59w23LvgwuJZt9bb4Wfd32cc+qdT+OXOC2d3fDeYtfdkpYi3x9Pu606IWqZ9veoPT+Yb05Lhw+vtP8y7lfT+9/HRJd3SO7n3vplfZWn6UefV16o'
        b'/dXQuNP1mC6Sb6NIcVgQuTxfZkkoTQiMmkqPnTRWC7WI4UrKZqqNWixBRRTerwvO9IsZdAijThghkWlKRc8QnVKTgYo3o4Y9LMYxdxzkeuFdT6UJoouoizO0F0WNwJIb'
        b'1eEal2/v7xACh3imtE5CVVQdNIQsKNOotKYSlGkxtGzEYgspzAadNX2Mmw6xSs5NsT6cG88CAy/rbbWyVSIvOi6n2ItbwihO3DhislP0i0zC+uohTh9uiJbK4XCyBXk6'
        b'HdWuUdjivG2SfOEKuiEnO3sL9cKBXBE3By5KAqAzkarH4yDH3EtlmUD5qFmyRbBEnVGMH7UAjuh5eVtiDX6b9SZ+PpyJow+NnJaAu8IOS9A8Nwq1SlCxMB01ogu0H7Bw'
        b'1uHlZW2BzgUzRDkKJ7cI2hjUYReWjrtkkGODmrAwexUKvEScNlwT/FA5lFGbxwQoRhXkDnoVy4l8aCinj3KwJICluxLmeXRZax4W9Fqhk2KpUBRdT3SElm7SDnSSPJ4M'
        b'TXDVxgMXQFdYA7XhNP+kYHRJYekBRQmQh9pXYym92FebM0JNomSU4ULTls6GM15Kck8XOKgFPYJoH1xlxW/wD4QWL2j2k6EGCwkWY9sFrCocRWehGV1i46QhBKoUBFRT'
        b'B/eRFqcLRQLcMId8NyUl6wpHOEfKpyPHBcTVj4MTuHrdopEb4CitQCjKhFIrqU9/kwucQk0MB+eQHOWQ3rSyleuiDuixsCRmDeMxItzvmcAYf+12oA6Zrde49dAmh3zc'
        b'AgbCBjxwztIYWKi3hAKFL0+lBA88hM3hEks6c/Q0aPFg3WI1C7WSSmhxI0xFqAp6oYP2TiA0yr0GspaOQwfFcHY7qh8DpXR8o4I4VKCw9UBX9PBNnCUW1Q0koiWoAbXQ'
        b'yWYIpWYyTxvvRHTJHQ9ThZznxgaKt6CKFQugnJZxDxYmyNcc9HJwOgZdh9MbGR5q0RhrLxVYt9aSTXgKlokWoWOQRVMWQTZk9IFAaqEq1MJQICHHiIE5lixfrYB6OOBh'
        b'KceyEyrjsbbRBIzHGMqd8aUWyNfCShge2sdR9xJ0jfmqtW316W/EWy9ALeqGy9AppqMGK20HIR8d0GY4kQyxulHGnq1BRVMGmKiMRNARMcoFtwcVqA6gNpHMAjdFojcu'
        b'lC4cE1CpB+raEM+McPn8BFwnyEAXPH1seE7HQcD63eEV1DrkPCNBZiu3W2+JOw0XWxojxGhtpalORL3zrXAP2XpQPOg1GzhDVCgKhYx1LMT4CDRhGc82EY+EiCAtdI6H'
        b'E0YGbAiTc5h6mRzPDtoWsv1aUMnj2ZYJubSyi9CJBV5wDOX2N6pN96UFmrd/iQKdmmhLKyqCXB6d1lGwlaED1fp6MTO9hJN5CiPnwTmyULKe7YJj0QrcK0nevrY8vnCE'
        b'07cTSVH9Yjbj270Jhj+JYoIO3Os56DIWPZvpo4tRK8EqQMT3MIk4yQmolx+HtVbWdah1K15u8/EkujjAxe4suspa4vx8VK4S6g9CN5bq90Mv2xYuQzqc7udICLVLmVG4'
        b'B9WwxKuxvtLMym3Hc7pLBbiACvBQ797NGHOP4XnZrCCorWzWRqPjuM6kIiZ4NYajkDebzj7rFEIJUoQn9WVraCOrezO+Z6yRGC7GWcahMjoULNaPx6kor1lAl9ZqHq9j'
        b'vWPopEF56Kyp0uK6f/pm3m4bOk3bjpA115FjHKwEiPGs3y0ewW/eksIG1xG8ZZ5RUJoTHurTUC0HxcvxVkJ6zB3XrRc3bMVcO8i1wNMFanlUuw/qaLKhqN0el9jC08Uz'
        b'zVLgtFGpsABykpgxvXmkP3GD9SNmllwySGbhfcpQEIVPXU8fTtwQYaVeQfSiRKgYKgylkXSVTfNdo/AluxZeZNkayY1BF8Xj4JjDdFwl0uXh6BDqZpsEbol1qFcLVeMB'
        b'vAKdp73iF7dYuUbSltKFVgFd34DrclZCm8p9LGG0pjCrQjCqXM3biM2YrHEUykIVuK91IDcNClPghhfNYSSUitCJ5XCRjvGdEajWC07DdYoXS4HaPTaxDkIHUYbSXEus'
        b'I5nEXgtnBTbQjo0ghT4JBSn6Org1J/POeNFkfXd6/hgFFJDDgzDINOGnwjVj2pBT1nuymngkkstQjyrwdt8gmo4OmbEB2JyqRTHsQ6awpYlh2OOfYioOoDbctIcp0q4d'
        b'5PlY28JpuYcPXr+9GCK04yIJgUiZQjvcAzr01HZqG4kW6qFm6tTUZAeS1KllDhTVWTOKPFv5guCyFM/UCjsLvK3QPfOaw24ZvdMmEZ1Dh+jCOwJPU3QaTngrb8ELzo3+'
        b'zNxYkmrjDAJEPujQRrZ4nJiCDuBRoZxmboI7XlUvSOEI7RARnHNTuEE5vk4W9QoeFe11Uo7vTaB8Di8rDjac/lyRTiDqpZNzNOrQIfC8qNx6SD0oPq+WCueh0aWvDidQ'
        b'Hc1nBLSJ0Bm9XWzg1OMVXTWi+2HwX44nMPyQG09Hvf04uIQHNSok+yIudTuPzmMBg3bkKjgP2TLIs8FN3KWUjKScsMoSWmgdZau2ytDJFLy58fjJa3giJqMDtPngwDwt'
        b'UkVdTx83gYwW/KQJyhRBDrqIN1SK/nvda6RMjrcpM24hngZZjugKm6ddW5crfOGqna4FHEEdlnTVNtoqQnnbN9Ixu3tbOE6xdLy1rS2Z/1VkW6uT0uOuVdMmycj4F1xR'
        b'j5yfCJWLqITghOo2K/AqD7k6uDLKioyBw2KedxqLdzw6E2pwe5+T2dDKrIICyURh5BMebDxnJRMAGDzk46Hd18aSDGg8eytM8WpOBkKMCE4p7CxR1whocpeTZadbcMc7'
        b'VjODYw4moQM2vsw2kYsatPbyUL4ATrHjtDOxZmqU5SuoS4m0TGGWocmDndad2hqksPVMkeNOw9KbIKAsVIPKlshpUztAA90ViTDtYWiB1zVjOIMn5HXRAjO4TkfcFNRI'
        b'IP/ywvu7bKOsGCZS546HHC9bHwmxH2nv5BftnM7m/yF/SFe6ckNdaijvwI9n2+IVVAQ1xCA3b3w/qBMduCQf8Z9B0ZU85DoDsWDBt5Ikatan50CriR1M8znQfm62lEIY'
        b'M3hkXd6YQncQAA8TCkFIznGk1H1cqoRIJu9N8VUTwYxwud8XRKa82X1Basab/yAYGvFG98WC7h+CmEAqG/DThGm8GX43/p7wh6BPgI/18BPGvwkS8n6aILlvwRv8LuDn'
        b'jfiJvNEfwguShboUdJkCJxP4ZN6IH/O7IBmP/5LcxPx4/DrmF0HHGOdFPuNv9cfgshDIEov7OC2tB+SNr47H95J0GRCzFKdhgssjxSka/Esik/5TeEbPSwVwwhjqzfHr'
        b'DJIzP+YPgZT2d+FXiYmU3zVWw6EOa/l+LLIP67h+Qc2Au2q6BPfZHPxpmEOmdO4d0+GPmYYvES4Gja1v4UnMsq+vXIxfqOd5g94gxJOkrRwN4A5wcXfzcQugGCc04JpB'
        b'nkSqcUpIeZMIBjo7sDP5X0EiWahuriKcvQ45k8vEn6SCWKJE0/5NrP0/+O5FyXyBNzCU0oNM3ND3TRar8ErIoBP+EIvItxP3c7opBBcGLlpCj9J+P91tgAVf4Batl0Ae'
        b'luxahwTl6yr/KnQfjFgiCpcq3+v0e6+L38vC9eh7ffzeQPm9Yb/3SvSS4zpqZBKT8FH9kElE/ZBJTAu1w2eokUnGhY9XI5MQNBMufFK4+WMgk0wulITPVOOS6EdqhU8J'
        b'n6oRkYRgoPRHJImSW9wxpIA9lLjbNSI0Jvme3RA4kn5X/w0sEkcW1j5LLtwRu/j5u90RLZu1LKmMDPIK8lLJPzooiCOLy5z1WEgiyoccHx8tRJUdDQN1IGghSSdZyA7B'
        b'9Ug6RTGJ/N18/ALdKErItEEIHQGurv4RiQODz+2TzpAKP8qtDmooDVVB7o0ZLlU1vsbAMst1BqRB+iHplf4gHarGSXqN1OhVcmm4PBySmsg9/1lojUek+tVieNibUdaU'
        b'fmCAcMPFcia6RI+NZH5QKUvVRQcJPBiB1zuOMubEpOWYiRREgvXQc/wi+LlQ95AXnwyJtPzQK0Q38lPu+4NjHTdwC3LFN+M2ynmleaoLKvrhusEhyISM2dOGI6lV+YkQ'
        b'iIth5QPyIyd75a4xg+bZI2J0jNNWtvKw2xn5+eQBWB3DZ9xM+vd5AsRBlIb/NSAOEjg1WfKoQBzhtOQEaYA4/f9PonCopslDUDhU0+yhdzg+MgrHwJk7HArHcAvAA2Ax'
        b'NE5mzfc/BgrG4PAuFokQEkeCCEiU1jAxR+rHNAGwDkHOGNDPSrQMsokwBAy8kVgOHx70MJgKVUkeB6giJvK/GBX//2BUqGacBogG8u9RkCIGTtpHRIrQOIH/ixPxJ3Ai'
        b'yL+hETtavoHMG64RdXup8AkGghNACboIF6DQW0lE3HfYgW4Qw9TZ0SYxy9/x4xUkYOEbe94q5NPgT9+Pjlz/5O2nXn/qzaf+/tTbT7361LtPdR5ed77myOSsqxlTaxsy'
        b'5PnXb9dlTs9qqLqa65A1ufJAixZ34A39VYK/XIuatRIsoJ552HKSVXLiYIt6eWprmTvNeQu6ogFDQOQA6ZbspOJsJORELRwcqC9y1UNN1N4yG866M7OK4SIhlHeAHjNq'
        b'0At18lZ6RcdBR3/iBriB6lVuof+Oe6w6dt7iYWKPnyqCXqJJBnn88PjJjyQJffCAMPlhS/FIMfKZct43qZVXSWga4uO9tJXeTENzUgfHTxlmrxsSEC95sONumPageSFT'
        b'zQ0Sm5KtPUhakxF5LVKmlNa0qbQmxdKaNpXWpFRC094nDej3vh9s2l5N0tqDw9z7a5T/X8S4D4QCU4pAysDv7XjTIBG4/w17/2/Yu/l/w97/G/b+8LB362EFpVi8E/Rn'
        b'TXusKPgHLBn/m1Hw/9HYbZFGSdCYxW6jg7PQiSmT+tOmWYUwRDBin986ei8DJApwh1w/CuZ1zIsGxHpCIaUrW0PQtKTUnx6VoHwd1AkVW5jbfK1f6OBwbBKLHWMN+cFw'
        b'iPpRS8NHKPThgEiFOXYp1CBlNpEhhM1qQnaK4+UBBRqgvAQOlcIJHeiGOu8UImZgEbXKsy/KFHLcrVloB+QwylcPLZQewG2ZKXWGisAUQua7ac5mr37CLxF8ScCsNRT5'
        b'WHtADWokDmD+Mm1c3zohxZlkUoTOr1FxyHoErVxjA6VRq9eQqF9PH2/UEOiOLrn72Np4+OCU7ATULJuF8v0DuInouEEsOoNOsmCEAizOZipmJcBlSsvBoXYvVJhCjmLQ'
        b'UdQNBwfksHoNCWhNmJVEolhpKLmYC0b52ugcZKJydGpvCpGo1kJtZIDqZmXkciB+CF2HEv++JuA2RGqjsxuhkzrHj14TJUsywG0pGsHDDchcjFr2M3fxTsjGT7ZAe5qC'
        b'RJvc4Cd4Wjm7Ukf7qePFBBTAsdktWA+SXbmY3ZdTxYqb+Eqzv3ZQ8WIDZK+X5Tn1qzOfLUkO+8jkeEaWzH6tnvOyoPWVr2bZRn4s/mqxo0fU08+NTXCd/nTojZ93f+Px'
        b'QdnUQ5vnWklWXR+1VzZO2819a+CEpon/lL5UX+j+0w63vEUbn9y+oHnp3fPvrHYfL922zemft7/8uCQzf8W4hZPqk2fMM22PD/C8EfvcmZ9sv/Ee/4vuXVfnhOXztT6e'
        b'WGIlP/q2y55n/pa2Xvtd79lr4ow3//Gj9dulpj/mV9SEBtxo6KxKff65nVcO5bX+Nv8flSPnbS583qAZtLNve6YmF8qN2AFsdiIq7OcBFANXqAeQxJ15CLVPXdQXFCqC'
        b'EjUdXq3y6H0zOuXp5ae3QEWHVwZ57NT+Buo0UkVukvvV7N1wAl2m59Vb4SKUDYjeRN27mJ6CzsIVWj5tL8hU8xo3TlHxGkOrNVWvoBIySNGKZs5jMGEOqNaVHrTvGQV5'
        b'qhljgK5YqZjHCyCTUdflWWwc5HWrjU4Qx1vqdos6oIQ5bxxNQVmsHmTq5nrz6Jo1ZwBdIu9UdIUe98vmbVJyK4uf4OFCElY0u3AVySBcHwlHvWZZEl4fHrcstKOcEEZX'
        b'0Wu1pp+VeXEIZGBVsJFmuQtdQM1Wnj6sV3DJR84UoWLUANWoCU4yf5FsXJFDcAFdUimXRLW0RSdpgKkAuSjDy9sRsgeHb6pjN3GPdA/ltZP9DwZOej9MM9xJwydFUsr6'
        b'K5VIyDEyb6JkECYH1uTHQDAQpDQUctekwdqU5nhHnUeJd+wLddQa3hVAe3jCXQ1hjb6PpJheMx9eMX1YBf/DkY2RcvG9TQ+NbNSk0f2psEZyyjE0rHGqL4WdmIundcuQ'
        b'uMaHRjWKoYMENk7TY2yk13fgR9WhjaiJC3VZLII6fxk3BRpFeIdpQ5V0S4Br6PB+EsW4a6sSG6EYdaJMxgbVG7mKPB7hgS+RwEXIXkH3ivMiGpo4pkkarOewdTwDgFmJ'
        b'Moxm90UlxuM5ewNVzaPhSyhPtoc42lWMooGJEcDIwuz3odOKROL5eR7qCWpMLl7fqtlW1QM5O61UgYliaIIDeGdkUU/u6FisKjRRYjoXXRb08LUmtglXoWKoZLGJiTNJ'
        b'dGIx9E6l4U178EJTHNAXmYjO46WuEdXhJ8mCqp0IdTJVGOE6dMCSeMlTHq/dxlsHBAuiivEsWHC9DW2OuRuLSahgdPDc4LjjhgKLkxsRS0MFzQ/ywaEvKxTsyzwLGiq4'
        b'8mJ8sO6+hdr/Xqhg9KOFmIHKKJOyAr+Mc0THZYwExRqvs4kePpBnDUesGOESlKAWAotC3ADlqE00C8s5XqgEWhSO+2W4yVwgxzAQ9aAjtDbJ+jQ+cGXw5mDr2QvtWRWD'
        b'J5mS+MCVs22CNwYpxrD4wBE2UKMpPnDSdr+VSna4pejESJk6/i8mciEnp+k5LKEBgI4L5cF6hlFbOWW83hbUYk1ce6eiDDEnyHhzb59/qzEzH60x9aSqxqRu5Se2Q5tM'
        b'Ha0Hl9McUecmNg5rguAcC9lrQulktFWNwOIZuaSLalnQHkqfROL2SNDeLGcas7cRLujI8FfXaMye/i56fzA6MF5mYamM1wv08RTWo15resnKfKc6YE8LZSiceKiIXRzz'
        b'4zt7xIqjOO+NDt+lBHopRrmZfP31Z1W/Hsv81v05faOlS02MpgrO3z011aLuL9pP7Jg25fby8e+/HLHs6udvJqxacbHx2FlZ3rFfplZY/fWs7IUsq7/b/sZXuP1S89re'
        b'S64vPHNd0ftDjaLL78SVrptucw6/ENaedUS0c43pqilWEYE2ig9+53qvzVr8oqO92doqe0PdmJXVXyw78Irol8KmWV2rOjpvztkagy4vXR4Niz73MTmVF1y4/vXxs0qm'
        b'zivOi/Yt2/Xd37pDxgW1mO58TdK2wOp7rkPr7eY7bemthRfmfb6w6fa8kiPr0bi5Pn9cfupC2Jt29bfu37q27cv5pp99k3Nl7oS3jhs98f3oKV94x24wOXBjYhs/L+7b'
        b'+PEnNxX948a8XYtyyzsvd5Z9FmMf8NuoWzNOLHCrapXcKXjb5ta1sT+2bgh56/DVxTtPVfz2zqoLZbPS1t9r/3X8W8/Unq9Nfk7actfr1tkJAS8Xj3/nJfxNknRBmFXS'
        b'PtEPc2bvfrIxRS909zvHyrLeuRi416bizLqov7+3bVZLvMFrDbB+8k9jb++73fLiiyu1327xlN8bf0rb6PSLn4RoX7IOauO+Mfqy6aLDuBc7NnRJ3rpfe7rluV9NuwKr'
        b'3O6OGP1D9/nNYz581+Jm/jXt2U998pnvt+fffO69o799vXliZOI7Vi/26C68e3eN1ZZxLiHb30pvfv3DjO6A6Lc8igzPVHVf/qt5QKZp4MRPpvasmvp9pf3FxKfb/g9v'
        b'3wEXxbX9PzNbWFhApIuKiIosXVEUsAZFYGkCYpfelL6AChYQEKQpgiIiIL0pUlSqktybmKIxz8S8JKQnpueZ3l/0f8vusljykrz/78lH2NmZueXcdtr3nM0R80Pnh8lC'
        b'fb+xuvBU1hXNX9X2HtT4Xe0zrivnqq9nl0FO551FnTfnxvzyU/ZnB9Z98pPwS5/XtxbenJ80/6uv7499cSvL+ntZWeW2D+/lZM364t/Zr6s1S8Cy2Z3Vtrkf1e8NdqkV'
        b'/jb7pWcXuBSn/PjUt7NO/nrAWy9Z0+Lsb4GLcmbfq1ffd+e1mvla3+1W++cvz+/a1FafHG+0tzmsIDhuU9tPS4drlr3c49a16Nwras1h0fdawgZaX+vxndV3uM0D3jh3'
        b'++tfGg5XV6cs7znInrj9+zMHh4feG5JGnXq5tm1amd6P++3HBzX7TUePhlWF3X7X4IC1U0pCyUCK480F3p9MvbLz8s+/fdNRunn2nNBudrp0PCjq9THe99XpXv+6HfBE'
        b'7YDp279qfDV+XP2p/dojwt/3PeXqURT63s3sd3qeHNv0fWbcVyH3X/ptYW5/TXM/bzhlXeX6zH/Wqr//6rTtYa0p0xvPJVw+uX6l05uHvyu43BQ/P+Zdfn/Mntcs625q'
        b'ffh1+xfZmdMtr2adOqQv2PEjm9kf9mrXM863tvw6fZbRZy+t/lSSRLyUEXfdDGowKw6q0YE+GQRHePFVi4ko4IueqJkIqCzaA9pIPOXOVdRYcgicWEVQcLZgeCLiiRl/'
        b'x+Yt1PX2AiyLUQXBbXMlEDiQO5XctwlJU+DWzOJs7ZS4NRPQTnhufXgqSIlbE4IyxIOf5GznQppGUAjqQY0qdA3kSShyDRzXTcNJqmeDWtgpR65JvNChg0EtBLY2CC9h'
        b'6JoryBOCfnB+TRqNWl6rp8SuCUPg6R2cVSzooF68vWGwUAlSE6LTvRnkcPN03cndTWhvldpYyvFp8AJiZrq4vUmgjZAxU0+shJ/xGDVQCAYwQG0Wkh2wUIa6UQ0uTgKo'
        b'qYMqOUItaS8FEh0OTyRJ3gk27aAVEk1OgR7iPmMLLwfTlwk2DebM0eA2gnqWlO0ACwMV8DSCTVsDWxTwtBZAYRebtbwU8DQBvAIvwwscTw300yFuRFOkbxJCbXsyHOBA'
        b'y/Is0vOpcyMnYdNqNmJ4WnGilLweDE6nqkLTYPliCk1bDGtIvxxm2YjtpApUmU+GNrc1C9YTMXcVbDxAUGVSHco0NQtJlw7ux/lXFagyXDc8HydHlemBfEKTJNidppop'
        b'shtN+VxwyJYiti5LzcW+tpoS1F/Q5ApPoAMUych1tMMFoPuJyUCTGToEZ7IyhMBqIkEVOP4IwJoU1oFWcNKSkDTBO2sCrrYM5BG42sJFadhlCRYglrle7GW7EeZ6p2Am'
        b'Gx6RUNCaKZ8PevkcmTQsLAb1E8i0nbCAQtP2rKcQr4EpS1VwacsWU1SaO2wndN29Bp3KE+CFjihQdgAMUgDDCTBEYh9iUFoUbBQzYBTkgFyqfaiGDXBIFZcGBlxIas8O'
        b'RFLcNSvQxMMRAeWgNDiQBBpZkE2d/8fAId9JuLSDoFSHZ4Ao2UCLH8GR3VSRaXWgAqPTRubDM3Si1/qG434RXNqueIJMq9ag41YOLoErYjuJAprmqRnHxS3RpcqPEcRU'
        b'D6nA09SQTEHxaUVoGeKiXcHZrXJ8mgC0GXmwsF4XlhFqWsB8mwl4mgCtrSbsiHZpbgx50yk0UzqBTFs9E0kqbXCIwshOgUo/2QQ4baMFRqGk0z3jItokRicAap5wzIuD'
        b'bVoUKZuZ6KiEkYBueJIASUBrMNFi6LlNl2PTCn3gIAO6k+EF8lYWaIfHECOrhKW5w5bpsISjFbYnOE4K+168BdTAHHiJ4jSz+aAC866iHZR19UA38DZsZQevqELSzsBy'
        b'opHagLZh3EcuFVZNIGU0QP9aDnQa2xKYCuhDx7sCjBaubW03CYsGCpIpErQctDg9Gox2ycFK35yiGsvBkMsEGk0QnARaMBrtLLhANgS75F0YjAbyQ0kEMHspGKCKnVJP'
        b'OKxEo/Gnbt/K7rCSA1dRu8YW4nvgBBwRIkETo9FcQSlV6YzB0Z2Ij1VC0ZI0QR0SRdrIq8YrwChBoxEsmh6aERWcsxkcpsCPvPWJBCGDFgoeokuowcawhw/KLK2noX19'
        b'Op0a1bB9goNGh1ED5qGz0VrD/ZkGc4XYlcAGnKCKtCnbySriwBkwLFYUjCekxlI3cJwD51L06DCfhCOwExVMZp3QEDZM48zREm6h+sWxUHhIBQoHOmFuDG8KHLMjWjhf'
        b'tMXnyiReoBeewieiuhISN9OVD8qJHo0Q5yhaba1KRJwA1MR7oRXjY0OVhAvcJ+HhQPsTGFRzNS6MLJgYLw2ChsOQSNS3YNYWLak8sv3FotOxVQ6IA/ngxG4cHG8CEQcb'
        b'XMlkFbHpUgUYbgGsAE374Qih/D54GrZNQrDlwk4Fgg3VQSjfvzVZqfXHZ+KYLcWwlWkQBig+EvRMANgknqs2Pohf2x5LT4NidAAek1HeAVOqI5hhdOAhXtpsBzqxOyKc'
        b'8ZSVStRhkcRTfsRPAzn8lbBvnetO2pxWHuo0eYr0VA1rG+EZbrXNUkJq2eIEVajaEwwBqqWi8aTZvF3QzClWqtzFoNaCKGSb59MdqGuOgYoydAAeBl3g+F6yK26FiNWT'
        b'oVr90Hw6ai2Bh0Atx+js5e2Dw6CTjOQUWGdsjWYhYsN8MKnywTCs5rJA1yayY2+0WynDQUaPYL0t7h0aY5aZasDbvxrUExAfrLV2/xMgvgrQCrtF9qB0NYW3daDlcUQB'
        b'gUMrCYwiisghcOAcOi9w3wSB4MIEFFYPlq/iQIfrdDJDAl0yZErM9QY0uKU2HpQgxWsclLhfdEFgv4wOZX2L0/ysH26gPTghB+jpgUJCdVe/CEXjUFHhCxQIwxmAIr9i'
        b'lsMGtMgE6x/E51UI1IPhGF2JQ5gqYiU0D528ZYiPqQen6X5XoA4uiCcgbaJp8DzDrUe70mnajysSOCaegOdVwPOgLsiOHqRdmVpk/4GX9b18JkH0NrhSPX0uA/sJQg+2'
        b'LzBh0LgOoG2PTOpBOHxQjtHDW4gEXJJD9Hz30U2zIwtNgn4lQk/gDhphJ6ghZJ/ulyX28kG7YRs6fySsKSgBQ2Qp4GxBmx+J08s46LIDTWbcqhmrfeUgPaEpbIZ1nB48'
        b'qUeneaMlCUlbYk0xem6bCUoPVsIKGoUBdljK7K0UGL12nMKd81CnMFPQuRRmK2F6gv1oTyhA5E5zo5t1mSEcpTC95bDc208Vpeci5+9nwCZQrgLTgxe1OQ5Urj9IyG2t'
        b'kToJo4fY/0oK0luB3ifMSQ0sjZuUVUXs6w5GdlN04jF3UC6180EC00V0du1ll6GOXabdLgCt+tbKtOPo/DlN8Hhq6LDU/t8D8AgyihgT/P8IfUd/zBUYPB3e49F3IiX6'
        b'Tpf88FltVgddm/2bE+qwfxFtpyaSo9/4BOEmuo+ev09+Xhc6PYS/u8fxKdZOn7yhjU0dBLNnzBqyfFSqHauN3xf+l7i725rLJuPujB+HuzN80N7w34LuyrEJBAPZ/tAE'
        b'ks188wfQu8c0CrUEQxRSX1Pg7ngYd/c0K9dNSvT+d3i5a6jSzzG8MJ75/4SXe11ozbHaAhVs3HwVbJz8O+PV6eTMaAQNaBuXK6/hEKhSKrBZxhKMCRIO2D/kMast/ys7'
        b'9gAqrlKtUr1SL5rDvyu15Z8N5H816N84XjSvUhTJlfIibZVGJpxGR7NAq0C7QKdAt8AgWhOj4wgWjR8lwBnB85hI9UiNUm6LEF2LybUmucboNy1yrU2uReh6CrnWIdfq'
        b'6HoqudYl1xroWo9c65NrMbo2INeG5FoTXRuRa2NyrYWup5FrE3Ktja6nk+sZ5HoKQd/ha1NyrYOuZ5FrM3I9FV3PJtfm5FoXXc8h13PJtR5JGaQfzYucF2mRJ9qiXyCI'
        b'ZiPnR1qizwbksyTSCn02JH6XPGKQExWI0TtTEK2mElpZR9qgJ4zkOBi7cU231T5Ba+TWtPcvcw/4WWJHJ9UnKDhP6aaTloTzScjoM4sX2tC/jiT7Av60aFJhCqOdzM5s'
        b'tYoHodwhjmAK5G536G5aVCpJDpGUgZPfpk32AFRNFGFjFhUWEWuWGpWcGiWLSlQpQsVFEfu4TirhcT5Ak02Hky58k7Drl2e0Gcn6KjPbHZUaZSZLD0+II85McYkqUA3i'
        b'XYVuh6H/abGpUZMrT4hKi02KJN7rqM1J8RlRxMiZjreb+L3YS2tSJgyztXHE4clytUTuuRs/2Q0Me0vJHQnpQNjLx0FBcRszyyckisfCzGRR2KEtLeqPBgmPoaWbBOM7'
        b'wlScBuXuekmpcTFxiWHxGGgghykjEmAQxQMdlcnCYgjEJIpm/EBP0d6bRUYlo/1VZpZEG048/yzl957AMywhSTbZASwiKSEBeyiTufeAl6GEN87bkxA/LowIS0hbvGhc'
        b'HJ2UGhEVQkbE1z2Cr7IlCZkHc3Px5UuFQZsLi7YXsXyD4dDC4Slzc/EL1XKZ/YJM3X18YtEWECs2/4AgUOWz3KIdK+G/v4P3JyBmkxbX4/3PHueSiLpMvRE3+XjL3elI'
        b'ShZS7sRYolEjLqdoqT7aT9Uyik6xx63jP4A+EXq7YARLRBjaCUJRk0KpWyAtTFmI6nR8TKKcsMjIOOpEKq930nTEEzclPUq+pGXpaK0pt5RHQz4mudrS/Dd4RYalpyUl'
        b'hKXFRZAJnBCVGqOS3eYx4JFUtFKTkxIjMYXpOv/jbDVy8qhMQxfsNow9gcl+per/HJeIBiiMFvufsufQdqJtR7V6AnsixQbtWZMWLzNLxMCuRxblg2E5iChKTJeShLRk'
        b'+YYU+YhOPtpjOnpi+UaQLVxGX8Uuz/GyJIobQ1RDe3nUnqiI9Meh9SZveZZWODmPEs3obOfwCDzjJG5DC8vJzINeHTN9ZVhwcXvv6S0X+m/9ZC3pTJM8L7lcLPlnX46M'
        b'idsvalm0hhqUsaFkq8E2UGsN+mE5HMCa2zQkxEnAZVAsgSdBH6BvYG1cHhEVgtJxhOyMxUmgC9UcB/oPMAfA5V3Ebr57Go/hr3oBNSRUc5b5VIY8Co8t2AD60SEr83Bl'
        b'XGfDsvif79+/b+rAZ0Sxb6gxq0JtEvUFOMYujkOwDHbCdjAK6mWwSBse2U3tN0iYV7eyZJmFsFJoDXuCqNNpVxKoFqOv4RXQwnA+7JJ9sBAVg+XRENgaTkuIMadlaOBf'
        b'LGPuIjAPhNR3cq7IEjbvFtMbPDjMgg4LcAaVgB06YQFs1JjUCE+rFF8J7LX2lKJLHuiEl5hgeEo0A1bsJuGr1YzDYL/8LiNaDM6BXi4RnoBjEh65f8AqGWdTsV2H5Lxy'
        b'R4fFHKO5n9vlDZqJowgHc2XkNuh1J7eFjOYBLh60zk4n2vVcbUdyG4m+h8h9ltE8yCUgofkwGcU18BS4TDO1eAR54CfXe6iax3oXMmumqBllggHiHDHbOYOK6+tt4WUi'
        b'rOuBMsE8rIRrhr3pnpi+x0FlDHEKAvXgktwxSJHlBh7xlkptuZTloHYGon+RAeyDfVJ9UCQVa8A+UOwVEMhERessgYMgh0yNTC803vtiBGi848cSFjHpWxniA9screp3'
        b'NJG2qNTea4MlPOIBSwKxr6p0A+yxBqe0FPOTOCX5eQp052nAfNAiEMChtfNAh4RZu1sf1k4FPYjoWGPhvnTjDNgN+6ckp+JgOIOsxVJ74h3k4g5P7dwoFqVmoLHns1Zo'
        b'XmO9y15tOGAD8mC/Zgp54Rw7FzbCI8T9Qxv0MQGcLJkEd+NpsqERGtTtogWUgu4AniwF9mnil7KRODkfzSM8S22XmR0AZTJ4mZQHRllDMRik3kYNPmDUCBFcta5hLzIb'
        b'tgiwnQnPhipPldEGza7pOOqJha6VamIeH1svvw1kzMmz66UwnxISByNnYH28GLTrg1EJm463hVjOATtfe4FyPtZdya1/JvA4P2WvCfV/zoFlLg9V4G8bTEtl4HF4Xo2J'
        b'hIMiJg62xCVui+XL9qMF7jcvLeH4UJLeav1rMdExV0bemTOgN18nMaLsvWRjvfkz1q6ZtrZR8HIJV7L+jtSucZp674uDq8Y11vvvqQnSD6ok/yXm9/g7Nd4pMYooAx/+'
        b'dPWXd7LGqjd/1O6xeUGcvdXBbOPoNWs7Xj36o3nF1hJt2YnAp7SDe65/ecpjrs6dNWaJWpbXW06FhDuv5ZeLyzfezrqsMbj8uRaL6L0f92fnJ9keEZgulYyvOeo0S9ez'
        b'eZ7Nz20v3x3m1DXm/tb6st7cZ2p5q9N+v7D8iHezeqrxpRUDP47sNXzm53lC3RAX8D47pcFc19nn6fneTtVRgcvi7z33QVy/Y9O3/o7XobGbk1pKToF64skCO6fZX3Lc'
        b'wI83Y06I/3EpdtvWiBfCnXbFNc/88Nlf+r754d4/fI3ffb48o6je6YXq8tR/3vnkFG+X5533uuukGwczy77Pq/K5z1/vdMJ+8Tn+wFjGS/2esul29m6v9t2w3njnl3zj'
        b'/g6h4NnZS1svzXnqvJuB/9NSr912zw4eFo1Lcg6Yfb81JK9m2rfbPqja2x4y87ZBU6b7lYUB1tUyg+gfm+33HTgR8uFrYQdbC3RffidYdHH6stvWNbbmgRvyv7TY87EJ'
        b'f1mSps+JvbtON2nEbPH0+GTOje/2lr57SK/iYzW91w68EvrpO79yYwmtY/07d/vsnfbuzpKIf0/xe+rrGb9Xta24FnHp+uG2um9u57Qd31R7foFp19779nUaX286/+yT'
        b'ssg9n7/0/XC35fe/ac90EprW+C2ItB8eeOPQAbWPLDvPmlx8rUj7bnO7308a7j8EDUq/9/2kttEvud5K45Oh+bz8tU/GB+9bG2l2bTjj6urX1i5f1zXSnH1jQCe7T/uF'
        b't7V8fqprUHsu61c93RfEozsXSlYpIlEWo23Yzgct9kS04NpZKcjeT9XOh0BBNFX9u2h4qcz9Wev48BjMjqUeyEe32IJicAHvQWhnWoV26yKOEYNRtEDDGaIGXQ3rYJm1'
        b'p7caGA5GVRSyyzkpNcez8LzLJK8Fzha2wQaqWe0FQ9bw6BpQbE+t08JQztwZdFElZhPaQy6hFYtjSx6x98M+xgc4K8aNdGorLFqyCTWxGLW31FbICHdwc9anEEVxlCxD'
        b'6mfraSOJQQcNbudFDo7yFxDNZdbyyAcS0pihpVvF3wHHwFVKklHQCCoeSOkDCsAhMMoX4aiGVL85smiqivp1NBXWcR7rQD41RhfjAxuW+KuoYFl4whuMkfZNj5kBCuFZ'
        b'a09wHh3g/BgWHkZvyMPPooPCCJsPfGw9xSSMGlXOmsAz/JQwWEa0xps2b1FE6gS9sIcB3QnwCLFmgYu71yJievlogjNSW6xG9ZUXMBeeELiCbNBIrE4bQCuslMFSTzts'
        b'opDAIqm2ry28KOUYU3c+aFkCjxFq6aJeHMHOBUfVjWC1/AmttRwcAidDKLWK4BUZqtHXdt4SGx+V+swW8GELPBdKCLJNAI5RZfIWtJHKw75VIr7mFLWtXYoCRWgW2nmB'
        b'RjMfG08fltGO5S3VjSIq4c3BdvhcjsXGA7kWXWsxTw3mgmEyFNFmIWtpYGjsLVKsxgjVOU14bjc1hrbDKniRD87IsPWD4e1i98EKeJVWmwvrYQ9iSipUDcjT5+hTs0AT'
        b'7IFHUbv6VU2iaOpfgY2kUx4gWzcMniCGPWJiFsDTLBzWAP3USgxO7wiAuWI7KTEbdLLoWLsK6qnPAyrDVCVm6YSRWH8PD1aZwUM0xVMZP41EDk2ANXJbrf5MujYaYMsK'
        b'F9inYuZld8B6MEgNLWdA2x5QZ48XNo5WyoM1LCiDHaCDtGzXdJgvCMC9OmqNm9bPgjZQuZ2aScrM5ykC9NrDYewLMcqQKmMWgkowZqpwUMJuAcMcCwdpwM+sODBMQryC'
        b'Q7uJMR1VTw1DoGceHtoJc3otLEUTq5sHixfB0/KEVbAaNBCUh9xCCU6jE5bDmR/D5VFeQU0SBUtchWOP8NCCXWaUMG3gDOK7OuejDU/uhHCJBd0pnnRMLwhAFb1jAIsI'
        b'1yRktCN5a6PBmTR8zMNiUCsAxbsz4EWtlAkmDAPj7WGZh4+tRIhKP8kErhVpx1M3jBXwHCiRWWsgpljCMmr7YbuQWwTqaBTWbXYwX2adSo0oalGrsjhMxS5CGTtvUIP6'
        b'7InNbn4keaKAMYCd4KiYP9UCHqc7yUm7GDEumRYAOr1gNbccTekmSrgy1N9jpBBteBqVgyaqGqPty1vlAS6SGJIuGvtlaHKy6QcZFg6wOiEbydf70DjScJVe8xmYvxXk'
        b'EvpYoa2vXsUUxudLqCVMhFYIHmYeTtgnj229APYxoF0zkRjvw0CXBYmvujSS4fTZOTshDdq+DBSSpY3aAAuzPNEKJRuEvQcs5TFzYKtgCThCneM0wYVYma9E7pQmZdEm'
        b'rzOTtx4tw1aapisMFstDVsMakMuAoc2wnBwF82DLAljMl1Ei8UA+m5kKL9EDZgB0elp72UpByz5bK1+0sUyJ4YWlu6ZhwQpcgZ0BtG3yhvlx22EZOmt8kfC1Q4CG5yis'
        b'J55zIdag9tHTws8JMaKuAPHToEnou8iXng6l4OhGM9itGsUpdxuoIoO2arNEjL+XT2B43oeZCod54DySKai9Hg5bILmTnEDoZBPBEXgSjnKgHJzXpufxWVswpIyzqbTe'
        b'BcfwdWHhUonWf28i+z/KaaYM2nAR/foP1rSDTKoGq8Nps0JWA/2fwWpyxFTxu1CgQyxomuQOuseJyCdt1gT9N2UtWEtWl9PBWc7QzwzyrA6xQglZQ9YQlaiL/mqjHxF6'
        b'WoMTcoYPfsPiH21izcPvCsknbC/LNFBV1D0QPUIipICcd7BN6F38673JSB/N/2pM+CplTtSjpKs/EillyzBd/9j0lc30/UF6s0f370/FpYj+j3EphhRe+w9UowxKsUBh'
        b'ZyCKehuzqBg7MyusWbRzWOyoiJzzcIyKP9W8WNy8hD9q3qiieb9Ox+2QK63N4iIn1finY3R0sOOiEKoKi3xsnWPKOmcTMDlBUEdTDRrW8v3lmvEoSNhxrRClrj4k7vHV'
        b'A2X1FqvN0hPjUtKjHhE54e/0HrVBM0Shp/2jJjyjbIIVpoAsDZGAaHqVSt6/2wwy4tP+aMSfU9ZtF5iE4zUlRieR6BNmYeFJ6WmTwj/9zfpxMJ/H1n998oxTCUf0t2ie'
        b'6vFHld1UVmYyUdkTnm5/va4YXJf0j+q6pagr1Yf5k+uTdKDkjwq9reyAZdAjgkgpIqL83SWjQYI6hOAQC49twmuTB4zEZaCL9m/NDgneIkitaUmPrXNcWec0eQyP/65G'
        b'rZDwsHhsXgpJSo5KfGy1byurXYqrxc9Sm0e8qjH1waAvf7tV2spWRcQnyaIe26z3JjcLP/xfNWsSihUfnwVcAVPAi+b9xUiicvzq+0L2UdY+bMXGFhFixQ6Lj59k5cAW'
        b'qfgoucVFaVd6VACSgLA4GQkhE4A6FZcQtTY1NSkVvR6VqLS1RIQl4jhp4VFKC85DpeCgNYnyuDVxiSQoiCwNraQ49LrlRMyQScb1hwqRhwxKiJOR0DyPMAxOssrgQcQG'
        b'VxyDYsIqo+H7EFiQp5giWNwgYEGN/ew+diejSOhH5kMHS0DREnlGRi5tz4NzBVt2P1eiBLF5F+bBY7BF9gAPD8uxCskWFNl72WLwgUTqA8sfg74ENaEyDL8E5XB0qhuo'
        b'hGfTcUhtJHeXgaMTYTVUolyU+cNCPxzigw8alYYHBlQ4axxMB3npmG/bkw7OW6OvldWv9wgBbUQN5/8AwjgQdaDQzssH9Af428KTfMYhQdvVwYgASjNM9kvBeUsPHztP'
        b'n/X+sDTI0s7H6gGAMjy53gPJXiw4sivSCLSA1s0S0G47x3AXx4CSfVNgRcrDyRb/03jkUZr/rDIaAmyVfOSAfKccEOzbla7roCQaPB/6AN0e6CrID1U3nA+PxB0OfY6T'
        b'HUOvCz6r+SL0RvinoV5h3mE7wz4NTQuLjY6P1lfr6zPury6+7aX/4qmAUzXTaoxXL+xNuKS5WHPzjbVdLtlpjhG9Rv4nBZbA/BoTzDMUfLs5x6U4O/WcmdO2ynml0xq1'
        b'n4vmjT8n7Os9zIbP8X9W86x2Rl6cWfWm7i3XTK45CN0PA+f8LYs1Q08Ga7g58GLEDDtgvdL9eYkaDetQBco3SCdkSirswjEHHjNLlw9PBYBDRAc0czlP5Sk/hdw51zoa'
        b'1AqWwWp4gigE7eDx1Q/mZouYolB7qK8msrHhdgMVyBIHh+fzojSoCqklPQkW27mvV6bxAsVTSP374ZAYC7/4NVAoV72AU44sM8uYDztF8CSVNStAVbBymJAs367MgHIe'
        b'tKEhnxBQHoqbpxz8cS3sxxOi2JGICLgKz7D/JAIeZPaaEjFOSGIy4NQAOveFnDERzjS4TJNJcsSkSlSdCB9q2YTX4G9o4n6IRSccvfE/ik7ZTL3O44WnP2jN/0nk6thH'
        b'Ra5mmQdt3zzfuK2iAVaG58NW17dwEGpR9HuidTcYRlTEDsQ5SWg8SBNQBZontHBo0jZgTRwHjoAzoP0x4afnKxxkLf7ceB5kxJn6DwiZ8VGJISGPDz+Nq/j1LwxR4R8E'
        b'oX5k1f+7sOIPDw7fNyju4upNfBnB+G2aLg3TjH7a6714luGvZd1Lyye20UeE/pbv0ak57EMydUhIeFJS/B+RFb/9+18ga/4fkPXRdU+iK247bgFWcMkCGMJoKeJ3K+JE'
        b'UpcrtkArWltOca5QgCjOQxTnCMV5hMrcAcRuTXyWUzzvQYpjTSc+kSYzHWa+xNa83Ex/wjoNu0EOOxd2gUriifGpKwnCZPaPHZHxe9SfoFEGltjDKzLtVHX8QiOsgtWs'
        b'3Tp4hFjyNczo8zpTMzTf3KTGkJhREaCIprKxpmF78PlWIkUffHFArAD/ANtg0JfJMTtWqYEGOMKl4105aIUxPhVgMSiz9/KRm3AEjFUEOGcpAF2bwCgxoeuv2qY0usN8'
        b'0M2GwhFNEiRjkYHaxKF6EtYrdutF8Ig8//M2DJ+Rm0r4tsnzWHB+B+iiWZs7rD0VwT5gM2xnYY6JBU1EPqAJirAi1dYKcUWxrkSRGmUHWoKIcX4XPAOKicbS1hPUgS4+'
        b'o67GgbLlgAYYASOgN5DCdfj8kPksqEc9LqbJ14dh/npskpPY2sOjQkbdmUOcSRHso2FRqmG3pRLoGwYOoQNMHeaTnsyFBTthsa0vPAEuEhWocDtnYAVP0+QdnXAMVkhh'
        b'mScOxOsNiwnVafgh6+WZMwSwdDMoeWiCihUT1Htigk6enqwyeOlfmZoxD05NkqP9oalp50umXw/6RpRchB2BvF01F9Gk1Abw4t6Zviog1jLY6EGIlLZ/GhylOfIUGRdh'
        b'Oygn5J0B8iAZt4RgMnJ03GDzYuK+AdrhqaywqAnbmI2AfO8BzsHzMm/QqW6PZruInalvROdHq95yKSxCP5e9KegQNG6nOatbvRfA4+DsJLhlDTgMs8kEEMBjK8ICVHCy'
        b'oBGMeJMJC3LhKWtVkCw45aeJQbJDRsS5ijSIj3qbi9lQLVA9m5mN5lOVREC8gMAZmLtd9XV4ARST90vVSNWZwTaJi6WqiRTBVVBFGg1LQa8+wchusaYoWQqRnb+D7hCw'
        b'bLG1XQY8K5lICwlqNInHCLjgBaoR226E0blWPnYSWy8fljEH+QJn+0V0xYwIYJMS7BqaLsZYV9APKunEPrYUVMgRVWjmigzWc0bwoh6JGhQJzuk8ApRFEFnaoFwQjdbM'
        b'WfIk6NZiCGrPmxg/8b6CNx20Fiw2gmFtwS60zE6kY2WxdMNWbEVXhaTpI9Fncvm+GGdzDDYi8pA2noBdsBOUT1Px70kEFdT5agCMLUJvWayeQBUSpnAIXEonbPAZMLRk'
        b'0lamDvqUuxnaypakkjHQBGNoCJtjVbYktCHBI6CROCupW9jghDvKNICgEDSRqWiSBU84608A/UDXanCMTsWL4DLdGOimAHJBPWcAe0E+eTHFGeSBMwET0QNAh2dgOgUE'
        b'g+4VaAJPNUQH21IGceTHZ9GQSrABW4ODrEnWQX4Y2haRxDdIhzln3z40u9ACPOlha0OyIp/k9hmCUhKqcYUJ6LC21IenHspbVyFQ3+1CS7gAa2dPAFRh6UzNGN6UObCe'
        b'bmRnjUD9pH0Mlm1X2crQRrYT9kg4MtfTnHD+wD5QIc3gY6Abg2Zc2RoaI6cI8evHZbAX9hkJ8dgy4JhfLI0KdQQcWQIr8LdV3jaMTfRWcqi9LxIz+jNCBIxOqM3rWzJp'
        b'WCFxGCJALJbkQ22s1tjRL/+ZiParSCfsyKZZu1ybfnmX1WSMvWcKGf9Qm8PbltAvw7eoMzr7QtB6CLVxMIh5OPASYSXxf7zDI2FTGwubyZqRTDDaUFO4SKX6kXBEcoGT'
        b'zXhA2BxXXxYTlRi1Jzl1RaG6QuTcQrbDTl1ZBtqmch/UAtAw6EQTgD5UTdIAwAoeEv4rdKXguKNOuBM2pO8FHQaCtRlos1pvgO61GpEAlvC02Bk7iKHVWGFr50kgql7r'
        b'/W2DPR5xEIF+ToNFow96YC3s1AxFB+5ZsnTQeigDTWjTltiiUZvwa5iBpuQGPjjnBC/Gnb76CSO7gTo8mD8SFTiU+OYqndrtx49bfn41/oXUfc8PyJxjGszzi79nDy1y'
        b'P51feo5xa2WNnkr86MnQcv6/GaO5x5JE32q5rzDb8HlQx7dsdW2Lgavdmqs/ffzijbuaBlU/maX8dHBX4dv6C/9hY6fu9PEt/+QX85tqm3RXOC9clxM5vsF7cPaZ0VUf'
        b'jFxr+umFDdv2OOocSmu2vnJksEH/60/i/PamrDd89tpXljdXv7lzXprhc59dX/hx6/24nO97tqbwB4a3vXP30M3j6Y3B5RvSfn9h84nGe4u2vCLYcCw94Pqcpfzta955'
        b'Pff3BruO49/rOk0rNEuIPtbT3loUd719WsRzR3ctODWq49BWulijb87y9Z4jhZmVv7nzC2NE4qkzvi55Y0uFR7ZV0efzXxmKvjnn86JXbD99+lOPC3E/vlX62dBMZ9cr'
        b'uxxfykiMvD/a+saXhr+uOtxn/4nDPbVvzvx4ov7r2LP7bjy1+4ZmwNXYguRrHwY8+9YFt7287cFRzkn7KrYHjTQcSZdkFNyuei6r+Ud/2+uCz13c9pR/bfP+vNR68ynP'
        b'zzw+7P35ujv7A35r7vZ/Z8b7s99n398Avru936c78O6897WK3mp4rlVb2+e8IDLnreNvpqqNPVXUOdf36VJT7m5/uFO4k1fdyOBvV7t9m5aOdO35YEbVLdnRGZc6mjJg'
        b'r95vTqnXvr1p9tV1re0b013aHKvPXvXYvW1GzjNHpm8P/Td7YLm07WR53Qr969NeKX09sNTRIvja67N/bTWJk/L3jolf1XFLuxttcaEg3uCNpi9uuCy9su7jIZdDox+M'
        b'n9oa8qvx/W9e3Fd119Nv8b9M22pLv3rLIfCL+uO7B36/+d3dkcDLpodEJd/dea6va9OXxVq9v7B+/QWvxgYvLW3asc2jvtDWVeyaeyMs+vC2gSDpipZpwxUX8lJeGy79'
        b'dNpV187S7Ve7tIPvN4x3ykKdRkuXvNcre/Kd95vHel7y3m3QfvfNTzp/MzGeMcLtyDn4s5HRL0tS5zwlcaYJwsGV/U4kpqY9aOeTLXoUHjalHhwlq73FGFquDvIWWCJm'
        b'2lbITAVtPHAmbr/cMwZxPmKrWHhRAvsojng6F7wRnCH+CzqwdhHs994MS4n3FDpAUylCPy4InNoMz0xyBFpgSd3nzmaBptWgX9Vfy49GyFmcAcdAZepkB6E53jQGDsz3'
        b'gnlwYDJHZAEukLvzYSOf9EPNLMXbXiJktNAzFh7wMNEhLUYHaeuD/kF6oFkRR+IAvESbdnnDVBnqZm9mmiKYAyMP5uCKdrA2FfcgeAoWsTvA6EyaDnN4Jg7FsGAXZoq4'
        b'IHbFDDBMbmg6ZGH3H8QZXSE5usHoKinxSTBBJ/vYRKSSFeAUSaM9kgTlObYLQB9iAHthrkw1NXUaaCTjtswfVMu88ZCgvU8qYKRwQEOTA2fBIXCZOmo1msJOEr7GBocy'
        b'OmcAznOOAYl0TOvigqU2oCbcUiXjPbwAiylkeBBtmJcnhStJmc7CS6aggUYr0QJnJ+KcwO4kFtZbzycFzwTNMFuA2KliEg4IjRLfmQW92kG0S5fBFTexHcyH/RKV9N/w'
        b'FM2YHS8OksGiCHjG0xMOSDlGLYWzWgjLyL2wQInYEh0yVYpgF17cFti4mdyb6qGJPWVSqPfRDiuNjRwYnrKWJoSej9oKOpJJpmIBOO0M+1jU0UYn4rUjgWWr0KupwTjU'
        b'rT47Z50unQX9XpFbQIvYy8daiPj/YRaU+8NKotKJAsUOmLtXt5PaaWB+xxh0In7oEn8JzAX9RA+IeOlBHTlOXR77Ap5jMHq+lAcrkIQwQB9rluL5pEjcjGNUPAGPKsNU'
        b'1MBeMs6xiEHLxbEdwDEHRXgHHNoBlMNjhKjaYHSHKjK9CJzFgQCOwEPyBPMl22iQjS0O8uBP8shPsCODQv3bYKuTarCNPbCC5J++ug01leg8e01heQasFSuzQMfA89Tj'
        b'rxsM7sdBTIgjo2AtPLeMRU1tz6Tj3Ymd7+FFcFSskj4YTWkaFwrxCJ2wXOYLL8Ns4gCFxKdNgAZm2A27YatKBJKzJpz5BiCHtF/dDkbQWkdTvclWJe8wbHah5R4BF9bA'
        b'qnSV0AZ1IaCTjJ/LbJgrzzxMghqsCVCENUAsynGaebjB2UjsBSphtg+NQBCyjnhmRmjBwofDD4DCg/AY3wWcRvsQyTSPun9iIgRBpSOnBwZgK7lnh9jtbDTFM4TaaEqi'
        b'5aMm5WbbrSdzDofd1A9SCYqABLq2jZTIdZZTVf19DcFZzhaxXO3UZa0VbWoXYbGNL9q8EcPFMuvAkBgtaNi9y4LGTd4HK8n9Egks9OAz1nvEoJuDTaBtBvXpuoRafxGJ'
        b'bWjvrbDHjpYNrD/oXEjmn9GuHdZ+Nmg1Y3FCDQd3GhPDqxzahsv3EHIthaObxFYO62AZDwNkFi0GJfRguRrqQ8g1QvwLJ/xME8AV6pl7domfihM09oAG2QepEzSsgJcl'
        b'hv/XAPAH/IH++1DJ4xpER01Mh4Txfguz4X9Gh7uEBjPgk/AG+Lc2a0GcsWxYK+xCRYD/Gqwuq4M1huQHBwLQvKfJ44TcdxpTLFlD1pLTZbVZY464ZclTF9O/mpwJ1vhz'
        b'2MVLF7tuIU7ZmNXhcMpiY5E2hy0BM3gm1AqAnjNjNe7z8X9O4x75z8OlapKsP4Y0KAOH9faZkgfdm3D/Q+yWEWcI2Qq7CXpQAYM/rp62JzIqLSwuXjauFpK2JzxMFqXi'
        b'0fU3chghoQVLOan3ld5b99AnC3WFSeQ/K2KzmbceH8M5HftlwIsmoORhS+ckGccYSRaPF3MYJ1g9xQY2ZBCx7dVIjqjHVqUlew9sd8bINLJhDoMCeErqZQOOgcNK6xOP'
        b'hf1ElwnOGqtTs9R2VHeh0rvXBDTxUeVnQbuERzR5G+FVMXoQB2afKCUdjKXjfSxueTotBLasfLiQY7BQrm4wTlPpHjVrwRx0as5y5cNKUAXa063Rc97g1D5r7IisMJUm'
        b'YyqRjFw49lES1pCFGojmwoY5RDg39TORKlFE8FyYHGI2ODddwhANSW2SFJbaWoKOIFRLPiltweL1HnJrnMtcITooQCup2weccVFNDUartlSqeWPMBcw2cFo0Ze9SKgeW'
        b'wUGPhzq1xFTRpxp4mSiaYxAV2mUPFLaBZCkI2k67hrmm6IMitEmXgNo49zdvCGQn0CT8Rbdme+BIot5q/drq7Rd2Xznw8ftP79UR6ezIOeQStaY0L8+y8K0SG2Pp9Wva'
        b'+rGtYVNHFt0KDpra11KosbZyH+/dVTk/M3f83ntrV67Oiz///FbWS8uzMi7HGqdYen0V+3GegfvCe59FTvW+HbQ0quWbkgsf+Zfe3fXDjrkj4ms8Wft+h39VFHXfeKP7'
        b'uTvT1WcYr3w12KfT5ZRXV1qymcbLGqV+bd0/rmnV6DX3F0/hD4r0Zu0x/+BI4RvjP1cY2l/VATfH/Rt03ayFejUug5nu23JHpj/d/O60xaVfLft+7+3ye411pgm7UmOu'
        b'XywNeWFR6Je5SQveXSC9OXB188efm/4W11/v9PnVzTk7nwn2cs4MtUZcgLbB1253v/Ce9+o/3twcm/6iyb/Y/qe9Zz39miAvq7HywwtOT8717b+5/Ps3f1NLcNiy9edm'
        b'vvEUw51DNzbc/ejAjuebRk8uSS1forb4yrmN7xzufuHNJds35X09+oxGv3lfmIXjZ+Y/v2O3YYt95z9fmjt7etzBT0dOnz+xc7R748zMHG2NC+2azecb3lnudvOTb4Nc'
        b'IpM+vNdy57ttUys6g5oiu118fTPiXz183y8s6cyoxe+3pniJprV/X6v1YtQLaeXTAqLvzfnu+o05PzXeLPp8aNPS9peWvJl5/4W3Gq7pvT68w/W7e5mab0QUjgz57ta9'
        b'mzF/Y3qSlTRpmduK17zsn5mervWmmVrLktOr590NKQh4611eFu+3ISf/0MSbC9ISr+je9om9+UPervHWoeU6B2eYFjUFvnboerD7b7qDr79n3xR19737Eisf37If65qG'
        b'PV9tlqZrLb+62fRVr69+PlL64r07d/Xf/ezWlbYXLm1/NuPiHnWjD5Myr19+4yVB9E+23zYlFt922Dv7szPlwoz4/tyfe499sOezpf/4oLyw7nehW5z2E5fmSuyoK/7p'
        b'lUie+CNXfE9wWkg88XUQt4sXazwYxrEwlY7/9mY4kuAAqKRipR1smpApEUPSheTKsCcIzxEJ+qciPsthkdL9nDqfV8IcGhMUViOhQSEAonZVISFwerg8gls2OPagiR50'
        b'Zyls9C5qlG9tAaVahBcPAaMT7DhmxS/PoAEJc7ciqdfPNgDmylNZ1IdShjYfVszBMoMVEksJ578K5FMgSdn6YMrkwV7cbcRZlUhBsZDHzIQn+OBi6lzqUN4Nq3aIkSxC'
        b'goQmwFrUP7EeB3ON18nRTIiFw5AnHLIzRYIY890sPLNIRGu/gDjXVrnrvcieAUP2iCUiPFM1vBohk0dS3Z3phR7R2M2BLtgGyylrWwjO7Z3wy+fbs5mI0z9J+dZmWBWD'
        b'eF5d2CFkuI2sK39lGo1f3wdK5RADJHq14FCn9YgjJax0H6idQweYgDdg/0qK39BNooJiLsbAkACvDDaS2CxmUdtHYBMBXFhFgHrVsLKw3V8hXCDptZPUHmA4l0gnh90m'
        b'cFtgxIkw40gSxAYO4na/ApRNipslsycN2AyHQR2GSGOGee1MyjLDRkQvonreCLKRkDAfXpLLCZz5IglteH8yvCDDeX8wLoIHOoKns2jfr3Ajw6O3kS8jMjkS1nngIiha'
        b'wSLSn7Gg8+pMyAqxnQ884ZBKn0lDtJuqz9sJekALHYVTa0ywUIkp5gLPChmRFhe5eioZQpkVbFCGs02BuTiiLYlnC0pcCdu7+cB8ig+cQAeGw1w5QDACthHK6oMWjNNT'
        b'MsfGiItWIgRFdI4Fwx4MRJTSNeS3nGXRuhlBQigRYRtgnb5SgIVloUiGjU6TQzhc4WW8bnE2IhqJmLNKAqU0JlwdGNCcQFnMQLxH7n54mXqudKG5VkDRfprpquGY4SA4'
        b'Q4XaUjQ9jtEFtBwtdjoxyPI3juKbw575tAmXQaFA4SszG55Be8lSLnxbLNHVZMAi9Yf9aC5i2Zg40hjBo2TuLgaNe6jgi4bpEswxxXEivTlwbMpyGoqvCtQgcd2PQJyP'
        b'TBh/V4BLAsZhi1AvBPan2eDW1GihZ+UbIziPJPRHAlKEvqHgCI331o5YhROTmT9nNUZ7C28BmiPHKcCqJByclj5Yt4CxgoUZ8LAATbrGaErVtngM6EH1IPnNDleYBopQ'
        b'YTze7HlooyVmtRGYg7kPG0/0XJsSnZkKiiW6/4fy0P+v8HCq4d/mKbxb/vlnJaOpWH4REXAK+o+kDkN2BpJBTFh99IOkFyTDGJPgb1hu0UUMPJZqsOSk/2+RmmmqiDwr'
        b'xOHY0Pcckmq4+0Ie+pbDnwgABkk43D0NHvaCMiblcOQOX35HyBdxIqE2T5PAZoQclsEwdAXVJ6R5bXRR6bqkPRo8Efcw5IPIRHL5hyJNiMDy/wvHIpd/7CcRGRvD/6wj'
        b'yiGLv4BfIZ2RcL7uEuNUHCcgFWdfS8V+Pak78S/sgpmKvThTo7FAhvXC42py1Ma4piqIYlysCmdYiJ9eid/bhX+twr/2M9j0pPQiH1eTu3aPa6p6XI9rTfZ0xh5oxMeJ'
        b'eOQQalDi/48VCiqORW+hNqzCrkGHGBJgTtsST0XOIloeFI73P/rL1zHS5GnySPySmU5xskTQ9gA7yDLTYDs/ClzlP+TEhQVX4muFIUIkEJoiwpNagShapHTp4v60S9dD'
        b'Xhx4X7dlHnTpWueb7s8QBqcCHHV0WLTQacFiRzAAetLSUjNS0mXoBOhBjFofvIwOnEuwf4pIU0NbXUsMjoJCUAKPwxOB/rAcVgULMOM2JIYXYJ54ljWJHANK9OEYdhpZ'
        b'wOwElxYYrSIW3GmwLd0R1b8QnyI9C+fAE8RrAhatB8WOHPYycQGjjuiQ7aCG7mOo3BpHIcMsYsAJWLjIFr2PbaSweM9MR0THxYxh+GI4tpGWcgXWwBxHNDGcmJ1w0Alc'
        b'FVHnkep4mOeIKL2EgTnxS2An7EnHTr66WYsd1RhmKfp22tLg7aSBYnAZnY796JMzYw4LnLfF03g1dSAPG0JR011wCNzTLgvkLQlDnS7DJH2CkUx5YtEq2pKLiGE4LkMd'
        b'cmOyYI0bqE6hCZLqV4NeGerOGga2gBNrQAccJNRyg6eSZag/axnnzLUYjk4aI0FsYq0M9cedcQOn3NcC2u4NSzxlqDfrmIWCdVmwnRKkyMpfhjrjwex28IiHnaTUdT7R'
        b'EHfFE/G3Oz01YSttxCUXkINtLYwXA3rgmBesl5BWu4FzSRAH+5EyauCiFHFuh+ko1IGWzbAfNdubwaljYCvoIuXHgZPbYT9qtg8DxnR91tGwLajyRNiPWu2L/VZKfOEF'
        b'0EseT1qSCftRw/2YANjvFwKPUXv/RYAnWD9qvD8iLazyxxQlnfLU34n9nNYzgaBnPTiznHypvwKMiVHjA5iYmICZgCYD2oj4wG4xhz3A0fBWBvLhFfLwctgIs8Wo5UHM'
        b'wRVBmomkHc7wspUYtXoDg2vasGkKedTbbZ8YNToY9b03WBP2kr44Y/c5MWrzRgyzH9qI2JAGMjRS2A16xKjNmxjYl7RpNswlX28B/aagGH3YzGSCps3hsIFOn0EzWA2K'
        b'Uau3YGoWbEH8RjV5wTlpIyhG7d7KgAFYuxWWTCNfs/qgH1ag5tgxrrDQDlykSYx0YNdsWMHDObFA6wp71LhiuWPEatiHvY5mo3UFS2b7b6ZfXzGbCStQ6dZMAmy33oUm'
        b'G/46Cw46BqL+z2NAgXgeLAZNNEOSOVrpFahLDjgz5UmHJ0AjXT5H4SE4RNwubJgsU5sEWEgINn2eTyBqoQWz28ICXAZNEhuqDGpGJTYS54JiUCG0xuB9nK+Sx+jBWh4O'
        b'X61GHJPWwH5wmNxBv3jgUCqjZ48quoAe4c0lT8Bhdx9cCi6CPrBZTIrAOUjT5XkLGkAuep88ogsqWEZ/Hq7jAuymGUg7wHFX2hb6CKMHzsGTOD/jMMzTTKdY8ouwmTYE'
        b'P8Ix+hEwWw894AAGieNXPLhqRUuQ30fiaw2LHgjyJe30Aqdhk7wSNdSgK4tRU8EQrqIrIp2KtaAVngOnQQGtR20Oo48LwH47uAlaoGeOoo2obeaMnucThBIycJ5o9+xA'
        b'o1hOJjPjJE5OSlgeSslQivV0/pDEkMKPzUEP4C66IzoRyDrMJqNAimjY4rKM0ccdRHOygJAJdagCDNIu4FaohTN6qAGkD6DQnOpQz82DV0jzyRO6jP4uV9wH3+lE+2mC'
        b'ZMJucg+MpdMBwVd41HFHVhiQ0FWC2YB+DQ7hoFNgFFEqGeSCNvSItjNtSzfoBL20s/SZZUiutCel7AG5pJjNK2fKu4qJiRoLc0EFJUkXmp1YYvJHc6Bc3iN0UMlHjzYI'
        b'k0bTlY5MpZc7uCwl1eXCvlT5XYikAVITEtN7XRRkxQ1CT2wBw4Qy3nOoX2CbFGYriIueQMR1n44p40Sz4Nqi/e2kkrZqoBFXctqR9BmeiCDVrIK5cExBXDV4CtbMlhMO'
        b'x0eng3wCDunR+0+YofG+qpgFDug4w/XshYczKW1zCN0a4WU8D0/gai7CAuqEmA/LEklDyTOLZi5TTKURERlGeD5kMalkK8lOq1g3crJEgjrC4sQehIdpf5JBNqGN/ClC'
        b'F3c16i7WYQaaTUAVXb65qXTKJ6GNjxD2MFrs3YrFnYNIWpgq7/J+MEC82TTmhcN6WEeXHY/RX4LuOYLDdJaU6IKr8hnAA41kIoGz6rQvedtJFZqwBpyVLyn8CBoYdL4M'
        b'4Q0iAVbSLaYX1PJpI6zp2oZdoI6sjewlpBAktV5dNDH8pCJTbIhHzxgkE6sAOBQBa+jeYbZmDUvXVghauWTYasEVH8XKRm+Fo+2jbhmmhFcEbcIVNBLtyskMD6EhidIg'
        b'hFhjQoqIR3O7jjYB5pC8wJXLKDG1NUkbd4GxMDoKpK9oPbCIvGT2DMF8Ust22Bkur4PMIESterTvYXLF6ZJpbAZH16GzuEExT93kYw4GTSUs3QFKdrpISZZkD1vQvQlH'
        b'Pb/AoYnUaP4JYTKPpa6SaBAzzPlFnJc/j2T3szmUqkVd6hqCtKwa0OHC+Id6f52sJv/SV914jENzKjQ0/t1lEvrl+Ay9hVIGY4RDt5l4udEvo/cLQp9k0MGzKtQ7aro6'
        b'/bJ4sbZ/DYeEJIdQm3O6W+mXTzoJbZbz0MiYhWremeXHxGOUhNUqHbs3uVUMk4ye9CTP3ZKJzUZ5luhYDfWuPGhKX9ZYarDjO8SJoGqWtWzLoF+6ZgiS0+V1L1myn355'
        b'RsDb4sLSTvab2zPEI9pkvaH+M+wmXPeyTfNckRAZ5E5ujIv5li9xtIgnEz3p07c01MwWMbSlp2QxzCenq/G/51eSCgrXq4W+ytG7buoRzCeO5N93KymDfXUZzjOM2Cpm'
        b'alQSzFtCzvYDC2GvNervHgbk6OwBJaCM+iaTNTOAjsPRyTMN1E6hEyVvCqnzQ3cjKzuGtH9fXPgTtKeeBw10XuQRmsyw25X0sDOkMowlXg4xcndImjhRmTAxRo4NGRfE'
        b'JUZG7UnFnN2jMiY6Ismd+kFikKsW2rxrrH2xNzDxL/Tx9oMnHoN6TIGFFPV4AZ4Wr54TQNr+jWhz0OdsKIsmmEtOQBQaEF/fuO5vHVlZEKp39Kkcn4DriXqrdb6s3p71'
        b'rx8cb45/sW5PfowZP9lMfe5s4b/VhmaDDv1m/trXh5I/dU7QqeAdX5kNf30h5s4No+T3nowx07/Vv9qw4NbNoI3p6VWGn1eeff+pddp7+ZZnC3XmVa5fbbD49oIC4cdT'
        b'G44Yhl+8tdpouc17unYfanR/YGKYMnNJst5A8vTdPXkjgwVRbz37wmtRbk4xy7u0LW89O+u814kfWj+/3f9OzqDG3fefMqq98vuSccum81Uft0Yu+6L/qNk1aDrvhZ/3'
        b'LGo+8k7NqTNa/H8NHJF9ue62xbkPekfm7bi2J+nbr57jg4AjJi/veE1/qcd3X6bUbVizrbDDLbAl9ns9v4XPHJYUmfOrj2vF1+WuGbpX/esliezJj7SrNYzm7xz9aMen'
        b'I6atmXdkzwQNgRY3v53vff6lYeve72uLHbzWpWv3ntTT+vWLO7cMfW7Hrnbg9r/8cse1S4tOHe/Zdeh8SOg/qzbvXHjd/Y5uu6z0iz1W029LHV9dM7O+9GbCU9/c663/'
        b'oX1dtN2bc73tFm6qtH1iQPDSzKKffl7iNP9zOCveeVHNx0aXX+EKAqNMFmbdenGh28e90eaJX//76snR2zt2LC2//uSaTYt94msMl7ys89KQ86utz/ucKyo2Hav99JbG'
        b'SW+b58p63vw2vdPi2YCZyVst4udafajdfPDNFrtpCaafF7sIwV2HlnkbPyp70+TND6bKSlpK0i1MVw4+0+uwtfG5ffzp16e9DmLGN+7JqZovSPTs29UNj22z2vOq+Ssf'
        b'BW+5/PT2n9ZF1jmefHXGvJ0huzw/uN8v7e5/Mz5txa8rfj38vp2B3z1uSuzLT2+2lGjJs5WBM+Gw1RCradGsFTCCfSxsTg6nauSW9ThDEI0uxPfwc2ZBv3kItQ1JQa+U'
        b'pPCV4nwa4hRnWMPjQGMI0SOvADiHDv4ZQIIhT0PLnV1gBQqpW1A2KAJ11kh+PeclYPiRiLnBDonlsIbeHtUDgzjenKeNJ58Rw2PzM3A2mi5YSdobGRsuz4QH8xF7S33X'
        b'ohSaecTAzkcl26MW8dPRqTzMwiO71eRuNODKOlXHNJg7nQW9FurkzS2bQJ4cjiNgNB1hn5CDV6ZZUaX4Ie8NUuIAg0o1MoHnWNCYDNqICWI9Ot4rUWtx4M0S2J/BrgZj'
        b'AmojumIVrshNCDvNibIcJyfcBPol0//HmqjH6g5Ff0eLO64hiwhLDIlLCIuJIsrcq3iD/TPK3INMCl8eDejRP/xvhFNpjCAN4q6iwTOXZ7yg+TH00bdCVptkAsGRivTl'
        b'ymEdVhdruHj66JMZyQaiQTJyiFg+xydRh0huDfRjQVKSa5ArnM3DHL2xkE3V5BRaQt44Ly4hRkU7+1dopMUpzghc4Lvq8kzef0IJi3+aTB7vhoK5I3dLmcoZA457kgVr'
        b'uIMvgqOrIngqpx1ugobitPNCv1SggawcfcVFa8h1drxCfi6zn5+pi3FWGxkch51lDvAOoPNw4vPjdHYYMaBUDSp1djN9Hw8CxflEUDu4aO5vwEAfAiXif9xD9Qt8ybHq'
        b'rs7bOYOhzI9F+hKGQEBSdIiHavFGSzmQ0NLDMzAGNHngNe4pYJZkCS0PzIyTvvAcX0Z8XKoufBHqEXYj2vL4p6Hbnuw5llPekLfg6Bf5HdW9R3pzZ5/KcdRikl4Rjt8w'
        b'kHBk3+SQJCklCPQlcTiZ9zLOCFTxKJx9eC/sE4NLaQ8YuBXWbVC3SYHFeIQmeVwcERsVsSuE8CZk7Tn8+bV3kPGm2XIyZ4XgVAUhODzPhK+WSsmKlcDGqawDbtJMn6Kc'
        b'6drokzN6Qrbmz8/0bOZ57cfP9VWoHFAp3UziYHoQCQ8jNh5yr5JivwUvUAvLhOhIaQHNwViZZCyGtYZSKtsdgsWgSgRapTY4310JnxGacBrYE4qcbsP6oMcaHvflCGS1'
        b'dirLwEYPytpH8KiDlt5B75N6Vjg7N1GQXZmvNjVA6u3rizFoIj9OpgmryQu6u8WMPloIoXMTNOeHTGVkmPeVBBsHaiWn8BguOH4/y2jNItz0Wi0KbvXfucd71/ydTDwm'
        b'cYCBgDHeVIHXjOYbm+Z4pzMyzCdbr7hYOx64If2H3TyGJ2Dn/cOf1OagTYtY5bAv3n1LEiPDDGrj+L8+9NPgMOhSvO43mpc9TQ2vT51V+jHxszdn0ed+Opr9YYWFAKOH'
        b'tT8JkWFmtunjSmbjhx9xWE1mPGZHYlN0B+oEbtDK0EoOYqruMEJbtnJcJsNk+z0VG4FPZdpYdVhinwu9Xt6d+0vI8UBA11FzF35z7ZUpz9s8j9aSGsstDP6U1LvVccYr'
        b'HkcxWRjJD9fIV4F61a/8UI4IbcVY1S8kX1kU9RTbdiI6bGe2f3CLtK541dE+YfEt9OkDJv/HYvJd1tfnjV8qvoVe/ZA53LGNCH57V0bDQqzD8CSIIEdEI1DMecGzgriv'
        b'd77Ll11Epe7/9uTaAJ+db6/SPBm97MeSd6/7vfLxG+rL3Tz7n+tc95xd8ctXRIsO/2PQNq0hJztw4QWdz9dOCQ05O1/i7DPFP+7fZ43jv/F8t82vz/TFOdumP7Fwygpu'
        b'9dN3RFfDD5Z3qh+vSfnieM2x+LKiOy4fCH8P7+wwvhF74HRswOCCeAtXnvMRsVX9l4bH29f/8PYZ5pebPy7n5bPrv37+RZ1/VR2fsbVzq7G3zaZvioK33Yh+8lPdnqZ0'
        b'66QNhfOqLr5Wfc/v2k9vbnfqmmXpWzD08Vpeb8C87iBJ5o93XIx737WZ2fxxe852o+evHTsT+ZJRYqpW/Nv/2vXj87LFZ9t/ufHdtr6XzrTc27GP/8LvEbWjifm83wy3'
        b'FFp3TInf++qT575z6V477ekjt8cCL2UKK//l0fZukcy/Nm5x8Ut+Yys06l649X3Spy3/Ln3mu65nZHXz0/KjXzWY2WW9JabepTh8unbAtD63t0OD21r7P/jtq9i7C+1K'
        b'HD54+7v796ZOa1t8Kc3my3krGl60e6fplWn9Nft/uLfjLaNvNQ3f//FT25KPv/uo+r1f9zG1m2cckGbstvX9+frvQa88lRpYkhkV8IPbj7mvfey1dKOO6T02sOLssZO1'
        b'Eh3qNdAFzyPJ8IKrVII9BIWMMIaz2gMvU6+Nk6AddqPtMxvzXBQUKALHuCTQBrrInpwejoSvYljqY8Mw/AVxKSw4FwSKCcvpCnOWRrsRFs8TlmJomAg0cAdAIU3CCE9H'
        b'ZsjSMjK0tK0tQdmUKbBPMwUdu7COB2pBLjhDPU4aYaP+BFMLzoIixNXqQzkao8wEoIJ9wDl0ONjCAZDHrgN5oZS9LFfb6B1q7SXnMIUBnD48DCooE9kKGkDJBPOJCjmL'
        b'XcNPwR7K1FZNjwclTiTYDalZXcyBCjjApxSrSlsMymAOel9ii114hKHcnH1yGIcYdC4LMFZBiHCO4IQRJWYdaCaAOVjo6e0rAEcz0dO9HKyFo6CavGxutnzHNqmnj5zQ'
        b'27koeAUcJbei4dU5sImVKgKw4MPPcDGVNdpcwIApOEyQs94SNIKunL47PPJfGsD/jtPwJHZ24jQkR+rJv3KkSrUFJDkdYVi1WUNWhxyxOAkdZkX58qCXOEUcZlw1SfhL'
        b'TeJDgJ/EwTKxL7cOYXr5HPbZ5lOfbfKeJYnUQtO/idhUHSWbKhjnJ4elxY7zI8PSwsbVY6LSQtLi0uJVnanV/gwheKm6uEw9/Guq8kzH9Sz9y2f6C6aPP9NJMt88EahX'
        b'OdTHwAk5FNPQh6+/CDRFcCpMHW7e5Ehi2OLMKiOJccTS/DfjBSgqeDB4CDroidp3MG4zkuowtPuIDRKRc+ERNM91wQAPHoqwjbvr9jUnw+tzPHT3F6G/ffdp6Oeh3mFf'
        b'RmlE40Aj07t5yXrvqQQa+aNAPnjgJk8/m78y/Q4yWqn6yknBp0OoN9m9RJVx4x4cafzy3r880kceH7WHWNey/OFVQj/EseVNYuLUmHlugqBomPN/NtaPDBTDe2iseb5x'
        b'1xYf5pE0Nl4hbl+E4kGMjw6P9AgTRb934/sNDDPrTZ6X/+CfHEjZfzuQOqkGDw6k7h8NpO7kgcQv7/vLA3n4DwbSDJWzKt3e2heN456VD44irBeErkh8/Chi5yMc+Q/J'
        b'm/xo/t8Yx4ckPTyGD2ci0qDhZzaCIh7h8vfhw5Iy+n6wi7DB2ptNuX18Zs/XK3eF/az2kjv5MhBRmr/UWQ2LhpJAOcje3RPJkmk8dSY5bCUM2UQD1ZjBAlgfiM6zfnAe'
        b'7w156IB0nkqef3YHYrBtzLAe2rt/eSpDQ8LUwkbrQFt40tpDGxR48hjhZo5dD3Pi1kuNOVkGeuKH1Zdm3hjR4hbo5L1f/c3yNTyPtFXOogBgMH+70Px7d9+TeSbxVs/s'
        b'/uynXRZBt75e7xAUF2+TNnoizKov7VBEjuOH6W+kWw5ff/+Fc89fOzfn89DAL6Qf7L3r4qSTVdv02otzzo8vesVFzTD63p5ndmfd0Sp4dta7kTN/r4uXiAi/kQZ6kOhp'
        b'a+kBa7VwDghwmrMFJzXJCR1jbSXnn0B2rIKFygI5hE0Sg1FTYlhBXJSRuR8OUVHCgbxUxAFhMh2cmUU1c+DcSgWodHUE5b3WrAVdhMFxlcAjLM47Yb7ViDo3nvRaOKF4'
        b'E4JmOMIhXmIYniP6teUwP9HagyjP+Avtl7Cgewa4QvWENeCkSEWftxxUYqxpCMh5aJmi5fSo829i8WriXTg5MjoEH6l/JZqa4kcPnfgcjqbGJzyAiHgIphqqrGc8k8f5'
        b'D8CdHmool2qE34lQtIwUcfAvr+pc3cev6rkMMeadALlSOBRAzjgPT3QoUyLPgnl82Aovg5yHtlB1+V+ZyYMpR3mVmpVq0VwkV8oS/RI3Ed8nWhTJi+TnieRpRHFKUQYn'
        b'E5WnEVUn1xrkWo2kFRWStKIieRpRLXKtTa7VSVpRIUkrKpKnEZ1KrnXJtZikFRWStKIieRpRA3JtSK61SFpRIUkrKpKnEZ1Grk3I9RSSVlRI0oriax2cGBX1amakaZ4I'
        b'JxGNZuKYqKm5TDNbxm6Ziu5ifZo62ttmRZqhJ3QjZ5MYcubjaj5hidhV8VfbSUE8cU5MswR6iyb8fCDXIku284e2VHXFnodNjSSIktzpDpEYH5Lqys2V/6c2V5qjlP9r'
        b'7n/MojipxRNZFB+XlA+vHpo2EX8yI8n3SBH+a9zNouPiH5E6b9IswzP+YVWiqS9Be3khEe8I2Qr8PdRgD5IgbEmGLvv1HuA8LLSxY5l1rNoS0AvKSYQeiAQ/R3FySiC6'
        b'p3gwSIT1GbCQJLuHI1o4gFaEmUgTVvOo6TgHbSZX5UFw4BAcJIFwEPdXR+MbHUYnQSXNZu8Mx2hC+2ouy82HGMA3wNwka3gC7Wg+ND2HNcvozefBmpmglgYAGgUXcByG'
        b'GveFXmhJwgsMHJgDKqgTVFvabClnhMpmGS6cXbBlJTl7pi/bILXz8rHxTDVCtYmTOFgNj1oRbXAwuELSsZViz3H0N3uJN070Aut5T3hkEPWXCNakScF5D9QcjOTBeWCm'
        b'zOFtEqmT3mwNBFeolAbLD+BUDiIwwGWBY7CRdrYS1C1AIp4VbFyHnuGIMgXkOMFjNM7YSdlaGo0JjnraCRkajqka9ZS83AeGJ4JXwTJLGq1BAvOoC58aqJOC7J0kmwoO'
        b'exWwjZ6cfaAKDa08rBUc2kYiWx0wI2XOBUcPKgJT7USk7OQzOC4V6N5B1GqxgQLzFTxiuY6/o76EJgYE2bAwknqcxRrPhm27qVrMQuC+lqWPPuG6hZEz/cGwMgFHjpUH'
        b'oJoKTytjUK2BQ9TuPJXnIabGdG/vKf4MIcWKeeC0IiAW6AAVJCgWzIVXiMPCXHBhL4mJ5QnLtOCAMigWKNSlOdquPLEKVekFzzgro2IZgBqKwiz1jUfTLeQxwasE0Qui'
        b'0uXAobOgGE8UdDzjOFR4vLThWd52aULc65uCWZJu/Yevftl/fCQAOuis3f2Rz52lXw0IxsqnnG1ua0ppakhe/X5k+x1hoKXAe8VTiT/7Bk//5hT78rm7b7/x6qvfvF7x'
        b'2o7FnVv2bs/Nbzrw1i871G0z335/fXHw6q92FzwdnvvSp3oXpp976ql7P64Kzq/j1Rh/HXfru/3/jDy7OuPc1oSs7f/o+PTqpzmxti7ffdJx0e2Nae4rCw/o7zf8fdNb'
        b'/hnznSJ9Wxw/73EvmH/unX+9/r5ez/BP7/3D17s9kDel6KXqQecxh/LtFyN4GWFna99o2Z7eGWwasfv3ovTUugzPBbutbvRu6Rkv/H/MvQdYlue5OP4t9h4yBBUVFGQK'
        b'TlQcKCJTARUVlb1ENqK4QGQjUzay95KNCEhz30na09OmuxndSZs2bU/S9nTmtKf/+3neDwRFk9jT3/UPl/GT732fee959s3/GDu3+8lYo8Gl/y00rPja76fjOz/005jv'
        b'XPdj3Ss/0EgfUk/N/9qmqcs5joZfvdRlfnTzybmtFls7++J3FZkXhRocM7h54sOBf7Z1rLufWl5x68SH5X/4SfjQud7p7/p+de9vHS1u+lfX/bDm9/O1Bm/CGvULLiLp'
        b'g1rTB81WqwWrRg6JIhVyIeUw3pExKWUPyBvO1FgkenptsaNvSwkk6Am1OAl27MB7PF0oloXq8OT8IsgXce8DyTSSmzAMg4LtqYykzrLF7llqMLTQQEumTGRvXOhS1e90'
        b'dFnCnArkLXUpNOI0l/zsCT97mPOI6Ns1rJVyITn6AF/oGmy9QFIAp22EmtcYtUmRYL2LvpBLV+QFlZ5QoMtdnczNOSqUj4hhncxYhyxG8i7gQ071DLBJ5ozzQkMfUgGL'
        b'aeIiX0b0iE7NSOPEp9Sxnn+ZesmEV0glqgdZcEeKzWIog5INgk2t1x1yeR8rb5uL+gttrOCekCiEuVBOkmIRNuFdluclkEFGA3V3SqGVTmdeyLBpx7I9tMhMmPIViCEb'
        b'Sfe6FKaioZBPJMFHwjKYySojhe39BO091YkfjZEyUZsiX0YKC6AXB+hg1Swk2OKuxLdgBD0L/digLlnekk0qT+kzgQdHF0vABnjwPDUtFWkqdMunPotlRMfZE0Q/YPYK'
        b'aS7KEmO4o8xTjQwdoAqKLuMdezkFYeRDFztZhFW/vPSN1J61LLInEuINDeF0PWoEQTgV48YtiLbEcrppfEaq7WCK+S00XaVuOIpFvBPPKezHMa7i2T9HZbwgmwjNgTQl'
        b'HTqZbH4Wt62v825qnIE+SWcMVDNK6gx5QncqnDfAHDrr2r2+AjHilEh3l5Q5+GGCQ4zbBuyDIm+TpWKnrqYUuoiGtVkpvNhUpfKq6RfMBcul+kdMyvj8Ur2dKq/FIGQg'
        b'KYsFOx/LBFLnFjz2w2q4srwgVYlEzFrrKP5DUUmfZwWp8hY6i78Xfj5VVNbmLuwv+o6qOENbLlU+2yVHnlOks9xW8Pm91hLhVftlx3VfVZ7o8bl1jkzRx6YvziN6bvGf'
        b'vwXOqpd1HPn9QhjW0xkWu99s4F1n5NLr0y4sr9buRt7UQuliSkxU/Esa0PxxYUHC9AsNaNhbIalpya/eZkJ2MdQx9IXT/mVxWku3uJAo1j46JlVoF37I8dDiKbxSL4/k'
        b'C6KX3MCnizOb8gYSyRHhMakJya/U5odXIvz5y+77H4uzrZXPJvT1+Zc6eKhcvJwQHhMZ85JrZZVshXk382YvISmpZsJLYf/KAqIWFrDQwvuFC5AuLsB8cQHCS68++yJM'
        b'88S5F8+tuDj3lgXgSl2CWgRlwgCv3NlI6WJ4RCgBzQtXoLK4gnUcq/jT/3KHGpWLC9D6wonVFydevwy6//WpF8xNL5xaa3Fqi6UqNTv5BX16+fRLZufs7tmAG/FiwI0o'
        b'X5QtuinO0L0h4pYCMbcOiG6J/Zd8flFRfDb08+Z05ZcE/Lxi1Xcpn132aeCKfe05JKZHR/C2K6nRBIRL4DE5QuhmlMqas8QnpD5veHjO+LBwac95CT4ccxVq/btWpcpr'
        b'/XspiXb1KheIJz/xkdf6jyZB/r5cDoa6WLn2L8jBI5teUG/+2kI2NAOBLyCX3BZZZ6xbYHeLW30ayRMZFZG6pF3Ds4Xq2bR6anJ70hfg75miT15csj5tj4jVvdD0xzEu'
        b'HNocwyrrRUPIautnmsBgpSePmoQ5RTWYc4Gmf5s76HMGjNFF1//yHcEdlL7z98wdFBv52+DiKPeQ8RvMISQSbXgk7d6pTBfOVe6GVLizqPjQFo8Yye/72qnPchYlX3/l'
        b'i7d/+cWnRKQK09wUPxNCdku8dPLVr3T9v3qJs2ifiCk7k1Cy4v3j6IHnAYC0DgYAW9Sw4DI2WEm4acgDu7Q9PXX2M+CQaYmh2zJNKJXevsrA0zoJ+9hLMicxDTbkHlPS'
        b'EiVJcaSv9bc5X4py/1J6mBdrXvOznojoqOgorzCPEJ8Q8R+MLhnFGvkH/tJBwSmxSyoablT+/vqZ56LsVo64S46Qgwuf5gvd1WZ1JU1Jhs5z9yUMnvnsDS2fUveVbuh3'
        b'L46qW2EhL6bY3HknlOsXLTrvvmDrrk+9nyO6rizEMEWQH4hKLzcvp5ilpMbExZldCYmLCf8MS7FYtBIPUvQJEHx7dW7XRcr0jLZJWFStg/L5mNaot2UpF+mbzes6fhP8'
        b'Vqjlhx4h6pG/ok82utIKryN+Vl7BLikjBmXhVt++84czql4H+mKNnWtjjZyNGuq+9e3CvbFGBsN24aJCB5vgc185jmavlb3RBI1f99NX+rbUscZJQ/TtD432RxdaKQt1'
        b'dSqx28F6iX6rCZNS/9Cj7tAtmEQqoXaXYEfmRuQMG2ZGttMTGkMnHZEHz3D78iCMMbvsEXjEv921SYXQ6oT2cgszNBlz9dwPulZ5PjVyaG2UkqLfH7gaWoVu1A/hsTvh'
        b'ZhQ08dYRYmg2l8e4l8lWWRNyHoMBe3+ZSDFOsgFacEx4qy8JH3jSN+ZqNooimakYRtdfkHOzz3StKcekXOQ3ynHo8BfFoZ1CoUP+h8WD81IfsiX65MLwS9sTrbympwzQ'
        b'gR5d90r49cGLHWsrLMlK7zNKZHA/Xzg7JilT7thhJ4sl7NQWFJL3lBc0g/cUBSH7PUVB+n1PeUEYfU95UZaMWNieQN3+9c7FS6iSEX0sZWYBtmBliUyqLjY99+8qVKGp'
        b'pi0RMl8rL/kusJRTMExgqwolEphRh/LnuLqu/O+UO896KBXvG98XhUvuMZ+dXp4+CRKf2ytJbzDfplq4+l1l5pPkXkBluRdQmY0crnFPzKPr1WhkWbhmuBYfWWXxOwUS'
        b'fbXDdfhvVflajMN170nCzfk7evwt/fBVd1XoezX6XsSeuK9EP8bhBvcUwy14tQ0FeccUjTzNPO08nTzdPP0840iNcOPw1fxNdWFk+lG+r0I7NLknDd/EvbEK3FXIWgFp'
        b'5mmx+fJW5RnkGeYZ0fva4abha/j7GvL3+dv3lcLX0vub+azsTS3+liG9ocL9newNTb7D9WyHtAdJ+IbwjXyPWuF6XLe1fE9TjhP0V0hURPLPtj3bzfGg2fInGDugv1N4'
        b'U8el/IE5JENSzUKSmSknKS0m+ZlGjJEk6PPnw+mrsFSmIsakLuu5+Izf8lgq8ZuEZPlUi7OEpCxqV8So4s1CzKJirkTEy4dNSL72zDB2dmbpIcmslaez8/OOUaa4PbPB'
        b'RT536EjAQTuzwwnxm1PN0lIi+A4SkxPC0/hy1y93DcuNdBF0fs8leixy7QMirucxUKRrj1RYTO+Qfq70DimXlmU/O7tiy81nXMMLbPvywrZeyTu8eKpMk6OrXXoVK6ps'
        b'7P75tYXbmR3jNq7wBFoRa9EZcTUmJZX9Jp2dbqjcOBSxgighX5BchxfW9Jxmnx7DFknfRKbRcCHh4QQqL1hTfDj9MQtJTEyIiacJl9rAPkOOWVZXZ1GO0fBJYwLYdS/o'
        b'Xlrf1H3RpM4cSBV4z4sXI/VzZz1MhCquMI95atiJ/dDLneBpGZueHQHuY6swCr0o76ZzBfNUbhrCQyFpogiGrmKlNVZAlY+tu0yksFmMtVjiKpRlqYM6HJTn7pbgk6vr'
        b'YZAT6iCoD/e3xS4SODod/WFYJLUTae2VmCdicdpmRsjrsVJjafsuS+7LPx6yzs/2lES000oByvfBvOAMr4C6SGsJa13ijZMpZ/ERF+s+DZAqtgveV/Uf2x8WpbEIOw1s'
        b'hlG56/MC1LB9Yb7XsuaXItGJBCXMNLokpH3kQ70sJUmBVAqs5hX+C7HbKSZ177BCyjfo+5/8+X+9S/dpgoN6TnOlxPafDgGHQoN/KkrUM1d8/XXdrfq9une3nv9V6Kah'
        b'skRLTVBJdGzdfO7W6J/ejQwY/mCPcexHB4s93u3cVdXYN/6NQKWMXwekB5qsCcj++eORsLqqT94ojB740s+DR0/NndLY/Yfpj5S1LEI/EWV7fTcW/jSTk2Zy/Nsn2oZ0'
        b'RxIdL/1k9OI7Fu9r/MnuxPVD5zfH7v+SlnmueNPFlhP//HnGlp9/Y//uCz/97pGfPDlk++3T9WPf+crBP9SGNX3la9/9htf+skfTr619429KM389GFWYZaUnOPBKYnEE'
        b'u/Z4LkYYbBJxlw0pUoMy7mCkG3qwmI0keBi7g7m8agtlQYKzHwp0F5z9zlgiJIk24KyetfsVfCSEaTH35zYLLlU63Ngrd362my36PsW3+ZgWWH+JhW8p4PCSVgFKcYIA'
        b'fQfm4D79eewpBHdYKYpU9CXQevCEUPX8jgizsIjEAh+6d5zdbbNFkYTscekJmBNizTfBFKvpsNMfC5mTShF6JDYwgw1CWP0jqPSGIRPB8/rU7SqVZ3VuuWFt7YG5MOVN'
        b'ZyVbL4YHjjjHd+SNZWut7U4lLomaxyp4zG1AFifMBT/ghVUsAYU1ZrBVFBnCpMwdR0/JWwtoZzAva9E6QS9Q1JNoxK/i9+CkD7WsXKEnKwUorEkHGqARaqRQqmbE1x1C'
        b'MvkUc+YxhI/Yz1Fe01/qnQI5fNPrcFCMRV4KMLWkRQaOhwsWi+bTG1n1xkS4u8VqafnGI1jOqzcqsJAPFp5NxGLCFwp8WXoVliiKDGikedrm4PMBay92163kf2Ntg7+Q'
        b'+H9eUd6rVF2syePh1cUO7DOpAo5cGRB8ZBmGy5nssy4yhSUuMsZCXxaCJxWeWMEntv+VVAbUf7HK8KJlfxHnhcLLrcjBC1bk5yZb9JM5LfLk55nwEob7io4z7tNJfJlP'
        b'J2xhicmM5P+bzNjPmQH/n5qxSaxKvip+ZnMLp/acIfIdrV2CxdnogwpmcW4sF2zOzOJ8wcVKzCNDApRZj0iGrAKmeuCdJcjapf0ZNufkDNbjdNMzMJESFneR54F+IWNy'
        b'1CshRsNLjMkMurAmff1TY+IE++Dla4sV1otbpv1i9YpmZaO1mth9aJ829P//wK7cduINGbcra51VW2pXZpcqFW2YXL9f2vlDU/m1XsM7V+hat0Ln0m3KrxVGtnxu23Ly'
        b'jc97wZ/XaJz8Stdc9hKjMbtm08TVr3DL3HZsdEgzECaOEd9ss5IIwXQFJtAqgIAsFEuZ/Rgn5PUBJenYK7wnW3OGG5AHk2J+sH63lFt2P3oj7lKU+1PzcYXSyw3I1mmf'
        b'14B8W/yqBuTr6mqakgyjF13hZ9qR2cyRr3RpjS+xI79wPURsGEK8GOMOiLhVWUY4Rxrqon4q4frp54tbJkL6addzOtXRiFRSJuVsaqnV4MXa6OXkiEhB83suQmQFhTE5'
        b'IjUtOT7F2eygmTOP3HYOlp9CsFlCaCzpsJ+h6K3MbRR80ljt0Z03WUECOQ7oO588ftr21Gn3lSKcIXObSiy04VQao8Cn92GX51OlsB0HBK1wue7jp6aE99big5i/hx+W'
        b'pfiKWHMU2W+Cfxv86+D/CI2O7ItgZvDALwXicNlIYOddKwXLjW9+82vvvP7Oa8elHZeMLxmN1WbFnhmtHZvIritq9Aj0rz0wur34NfXGj0SVNjpX9QasFIXmbSqkFzKx'
        b'1gGr5GoAC+njdul1WC0XtrW2LolyrMZCLvtuIlF0McaRqx+YCbNcBSGZtFIom98MdVsWtJfr2CneCr2CtV0B8jd4LurAWLdHpHZWgkPQhy1CUf/7q3Hw2YYCPDjy1CUW'
        b'HpkpW4bFn0ekfU+NZYzIIUeywE2+EHLfFukLgWTKvE5Jxupn0GrJBAL77ZUHenGj8VMBdkVjd69EeOypAOtCQ6S/Ei0oeokA+5JFv5gMPCfHfV62u0AAJlYkAKnPB4Yk'
        b'RC5kIPz76cFBYc7PSQ9WdmCRsLC1YFSWwnDin7/f9ZvgoC998zVCy+rW3PVFW2uz1EadNET2r8kybLutJBxzbuBdJ55oKY/JZG5XuvDV+ECWkUE6K9MKI8+d8xSCV2dU'
        b'F+P4I6BhwYWzMvPY+Mps67bIXHVl0JDfi1yc3C9ZECcPSJbOmqcmL1rzhcA0U/Q/L2FaL1mNlYAr7ymlhFyJuBiS4vNiAyvTAuXsS5GbWBVf0cQaupKJdQGImf05XF5y'
        b'/XOB8MFFW3lEagiLBQsRYmAuJ1whfshKpy+M+38F/8I78gNzZpZYbiW3YebXy2kpqcz8KuBjSmpMvBAhxzTMFe2ngta5LK6JGclp8JVst4uox9aaHJIuHBft+TMwjoH3'
        b'86ZWVYEDQ44FqwgkR6GTxyMx/+U82NVEsIb2Qe1Faw8ox06CNncRVhnH8yIo7lpSoXpK9BaZSFYnTg37BjdhfnunguiP0QYs9UQ9WmWPKECoIciLa+uus/bFTMIFsZ8I'
        b'6/0sYupVzCUpTfTVWGpkxD1rTclB7cP9M1Hp2a6//46p6OMsV23dcLVRyWsbrqvrVVwJCvnQINrnzeGSMo+qHo9f726c/ah8F3Qe3eTaGnIzzKLbWPdH//FuS+Nfp/PD'
        b'73ea/eHdT8SFx6vuJtbFb/3tjpYTX479wDRgm75L0s8tN01/q+u4/uWUS2kn9l4tSAiLc3xYunYo4WHveYtBN7+ooPzffTnjH6N/rm3cH/Gu1S+//G0rZW7bMt4CxfIs'
        b'COw6zfn/JRB6dUAe1rGKunJrG+SelUsABy5zc56LDUwv5f+G8EBugbwBA3xwVyg+au3BzHGnIItb5GACSrhsccgDOqy3CAH4OAHNYpHKHgk078FWoSdJ7hF4Io/PX7DK'
        b'IV2l3DK3nSaQd0GsS36aTqppyc2RIXuE9qPQG29tv2hJhHEdic1+6F6Z91opfl6X6ntK8rxTTmfdvziddVooFLFJos0bUShzT7mlOMNgBXpHEy23h3ER4ZDks8UJ0jef'
        b'PvtUpjhM/6x4RWL9O4MXE+sXLJ4OlpvmOLVWWYyoFpzeW5nbXBYXEh8V4BamtATvF7InOd4HMQLOMidZmqoqd2wyd6okT4u7VKV5uvIyaXqRenLSrpSvQqRdmUi7Eift'
        b'ypycK91S9l/yeQlpvyVbgbQfDA9nodjxEenLg16Y60hwUwletbCE5OSIlMSE+PCY+KiXpE0SwXUOSU1Ndg5e1L6COdFkLCTBLDg4IDktIjjYRh4EfiUimUcTcB/qc4OF'
        b'vNBnahYWEs9IeXICi0BYiD5NDUmmGzELDYm/9GJ+ssy59oxYtqJr7YVc5mWciR0E8/2lJEaE8R3aCKe8Ip95mgIQn3Y5NCL5czsKF0FNWMbTWP706Jiw6GUMj+8oPuRy'
        b'xIorSBACpxfOITohLpzAewn7fCas+nJI8qVn/NyLl5ZiJmQi2Jn5shDY9JgUYQUkA0QnhJs5R6bFhxF40DMLEnnwigMtrD4sJC6O7jg0IjJBzo0XU5UFIEhjEd7MSR2y'
        b'4jhLYeiFJ7kYeuZs9myawtOQ3YV5XxS6Kx8r1DH0+VGWJjt8xvuMVpDo4u9rtsNpt+1W/u80ojeEhOERC1e1MBaBvgAlK0cSH46IDEmLS01ZQJHFsVa88c0pZvyfLJjg'
        b'ucUtk2/kkMm2kkhaBn36HNLZMrFHeyn5WxR7LH24+OLijm0pjskS+5MicYIIpmACe7iPdCtOhqtdSRLDeIpIjPkibIR5KLAS8y81155g1jkxccoBkQRKxK6km8+nbaOv'
        b'tGDiFL13IkhHEJos7WwtMd9+yzFvwVWdiKOpp45zhy+9M6QCHScOpnkxfQgHsFHtCk7Sc9zkd8oSS7DExtLdG0b82GCn+bsL3Teh4ogqNPlAyS1V0vNzRLsgxxmfaGDR'
        b'VRjnthHswdy1gu/bBnrk7m+uBS3xe4ddUIZWGIFxLpu9tU5DZHTVQsIqf/849KwojeXHYQk0YiUTWxb91lgSgdUsdM/GytZDQbTPWhHrLaGMe661PTy09K2xQlEk1mF1'
        b'tB568KHBT0mkbvZQwuqEfGVXoFBsJCSapKADM2ImCwboBwm/tA5lrWH/l7hZcNy3lA+LhEYtnVi8Gdvpl+c81ERq0I8TvH4Vf+PoARWRtmm/VET03kO2TZTGQssikliD'
        b'C1sPb393XqT3GK292JqJsov7YAdt4+Fld8x2S7iBogiLrNSTduhycfgAtmPLEnFYkIWLrUgAg94A9wWXbJQiy5ifVoH2Y8ZuVspCXvikDPsXEr+l+OQSVjIfZL+SYJ+t'
        b'xGxo9GR532tgnKd+wz3I5xG+myVBC5nfsrXYHiyGNs1QIb15CGcOQsuhhezvxdTvcewUJn2CWTi1kIMtsyFp84EYHhus4pEJei5YzzOwA6FfnkLJM7Av46xQGL8FpiNY'
        b'CrYm3l9MwYahNTwF2+m4ufXz6dc4YSjPwLaDHCs1vn5lyLeWlw6QuRzBbDH0r5MXhOkRXxKiPdP9F4sGrIVmvjpFLDOxXlYxAB/HSrEhGhv5kVlhP3R5OnpIdkCRvGYA'
        b'3sNRjr9bIUuTm8RO4xz36WN3shDDUWrvhXU4I9QOWKwc0JrAz9MtbbO8bgD0b5fnzPK6AZB/ir/uFYllPIwUy4MWI0kDE7Cafxu4PVVeN6APyhYLB+BjBz64M+ZiBZtX'
        b'G2oXEkB5Knoy9AqX1X0zkNkjoDZgSV0BuHtBOKsq7IBRFkjiZ6uY6CSSRoj3EC4X85IHcAeasAcKsNCf1LKyk8dZKzxbMf2yHGt4FQBnJcKp4BqmX9kYHPeUn38WlirR'
        b'jit9ZdiHtSKJugjnMTvDSlUoS9aGjTifopmc5sl6FqrjiBYU4lQq3UWs9JgHVgk1U3IPQQF76OkTKTieduYms7Z0SfEB5EZwiAmAruvy52zO8yfTU5NUkjU0FUWWUhne'
        b'wRx7oelLIdbjLI6l4XgKNCsmqSfBPa3kNKlIz1S60ymaB7ecwMwMGDdOSUpT5SNp4YQKjtC07GFhAQqi/RcUFaBfJgzaiJk4wJ7fmb5klQoivQjpQRdNvpMrcBdrFodM'
        b'J7L/eGGBa2FItgnvgdCq4yS0+rPnoBpKFg4lGcdphUekzhpnedGEW3DXMAFLnw5HVFpRpK0owSHMMhU61+BjrFHDyVRai7qKBukOGrd2G0lgDCYEaMV86PF220N3evw4'
        b'u1IFnBaTSl0mEmqxlZqH+RMk+lsQ0N3DKn+4xyp71otxEpt9+Azqq489Mz7Mr6UJMBOEZlLWmHchBSe16DsJdjmuF285Zp7G3JnYtoOoaRGRR097by/fk4w3+ckVfhtG'
        b'KIuPeWHhMQVsSSLoO6mSgrM0JA/luA8lx9JYEfR7UpHYmdXLGIROoRlHZ3oQjrkT2SBVs8DLRybSgUZ4slsK1dgUxIl2xnYT0TbTm2KRdnDQR4oRAiX3iNoiCgi+Q8cX'
        b'HLrmtoJI6Fch+ut++QfLA1Yyzg92ehK49YtYE8zpa6JrUIWVgjkiC3O9CRSYBq6XIcqAYmwTsicescgwFrVFyxy5KroKo9AntMHqhTvbsYijQUaMKIYuOT/GIWyPJGWQ'
        b'2M0F3eHL/l+P/84B7aaJB+t+MPJBx2W/ysmPfL+6v9OsZF/iAeWkXxxfn/RTh767545U+ZetHrTXaPmv1jJ/333v9LxvddWoSfx70Y0Zn7Kysu0f1P0jMirqypOTJw59'
        b'VD6qW17e8a3KpI7YaYWf2A2P+uKk6+a3Pgo7+Ol1b9dLhkkfmZz03FJx/4FLVNLf79hO2g9861vHqtYcW1Of77S1OGDjw6Qjv/z18fWy1/pK38zvjQ2aqP1x0R/9rvVt'
        b'1wna0/FH3cAfBYsd6gv/2Km7xSPoyubvv520qeMrc3eS133b0nLs/mbbP4c21rzbN/jrlNJ/2KWudU9tffvPyntc43+1JXj77q9sjFkV+uGU6h+7YFbjeqvDxMd6ldkJ'
        b'oWo/fG3jdx3fe7fzb7bK7x+PCm5uaB4w2vOWdFVPoeqm97/p9qOEbx0Ld+4N3edhsPnUhz0OZ75W0+GvfPiG22FPhV+ct9r8Scu63562DX57tCL9Wx8kZ6WUzjv1do2W'
        b'W/jEi16L7a17dPmUp5fRj5wy3vjVyfa3iz82mXtL7XTaPp19Se5ao5IzOQMHP9XWIxno1ilbp8iJ5E++69H8B7+Y/3wv63vrzZ78fuvEwFsP/hB35pfxXqvf/v7a9W86'
        b'6thtSGxK/ef7Q6/951uxkVv+JPnO2ye9Bj9IGFO9rpiktvWh6TtaFz4s+8DaXnr7+Lu+308fe23f4Qmv+NLTZQ2b7v/tq26v23//f279d2z38PePf/xdn7erGhIMUj/e'
        b'8pdwzx2hn5oNf6qecsb/42KU3tzw8bvf8f/fi9v+8o2oJ8lhX5UYR1/59W3HXS3pPe+fvaHzu3/cOKc4+5aJqYGPgcf+aZXqhPdvF+2cef3c3p/+V5HqX3/1yymLR6tN'
        b'1sJM+526tKnGL39tZnP/hydjTv3o7YGv1r95y6whuNap8M31u+ba9339lz8T2f/tZ9/dreFp8E+93zz4+k8mmz/5ddCXsk///NbfpW6z6js3XbTayo1Jx4hA9lgv957r'
        b'Hlu9TUoSRIzgSipLxmouhOjuF2SQPGwRAsMGV+EYjFzgJnVfXp6GVYIogapb/M1zJrZLZJtEVRJtNluk2nOJuQSacYyJpyOsv33+MaGh4jHvJLm/yRP6oQhHlWB4DU4I'
        b'xT2G07HPU1gjlAjT6WBeMkxLoViKZdy8ZW8UtiN9uXOMW8b2RAiRcP0wAAPboMza14Y4CisUqyRSwycSnNJaLVTRqCI+nXPU2XNB6uXRe2FYwt9fc+boc1FnNYFiKZTi'
        b'jIZQzJyEoRzB9iZbHwFTzPZWsZPbxXz9cEheQRYqIuXhcE0yvjm4Q9Sz6Pa5Z0xvcrObmapw3lmQZykvDYcFrGzOHC8OB5VCIXX3hDBrHzpGRZFsmy6buhfL8A6/Che/'
        b'BLlJLmWVEN5njo38xAxJAJ1Y2ukB+m6IYSQRx/mY/jiavFARV9Wc18SNxCdCOd17xOryPa1J4Cz2VCQhuECkeE1iHrVWCKBrJSWoWSgTHETn87RS8K0jQlrPOItNWChX'
        b'txNy8aEYhvxs+NgncBjmhGhG6DRZDGi0u8R3swnmXZkF2l7pxiU68TbxSexP5d8EXoVMJoWzfB1tJlU2e2OXELl5B5p3YpENibQM7Aq9bUhisbcwkZIMlQ/lfM3YBXlQ'
        b'gzPbnzpIBe+oObYLuJCLRTIuQx6CXi5DOtA3/DDyYJIAdlEkh8kEVnp42kkw6Va7kCifyYT55UL55qNCQlFfMA4+lchhxpVu9/ox4SALN2AFl8h9ty0VyEkoKxFerrbW'
        b'YgI5LS53USI3dEll1ftJZKpRW0kkn8NWuUyuAZl8nlv44CQbRgUyBdcvzYOZ0gR4tHDfrfiQtU0rsPe1lVzDUQZ7W+AhVPGZjsMsDAjyGQ55CfJZEk5o4LDYEe6IbbBN'
        b'QSXdmYNcMp1xrie/hag97B6UsV4ChSb4gONCMg6vZrURo2CUlFcosD/Gu3abuMkIl9qhVqiEOIlZ+3npahJbmrYTloiUsFWi7H4mlbkHtDfgBGftqe7E2XHWXrjfHmUY'
        b'kZdvYUhGR6m3UTdQiiVpzhxILqXDY/499kfZ23ljIakaNDPWyqBxNeQKFXJ6sfQmFKTy53xtSGahu5GIDLfL9hOp4f2sA7ZCnTDNsor8bVAuLwUKnVpCBZgSHeiBThzn'
        b'lSILBeBRg3sSbIVH0C0cezHOqnFvQIGNxAdGRIo+ElO663q+JXeYuyKE9sK9eBbbsBjaO6YklKcuw0F8Yk6SypjWFTlJVMFeCclfd/05imvr+NFd2Frh3VhLBj5REhhV'
        b'umWl/a+nQz1jF9f7vx7xJREHIeHhyyIOJMyH/MX8BWd4jxWxhBWu4Z8MxJoSbR5gqy8Ut+HfrOXFqJXFdmJdieZi8K2yRELPs5bZQtAtfXq2l8tfZWoy8bKfv8p+q7hO'
        b'mY8ndHERzP7K9EedF9SRsYbbf1ZUVxSzQtjCWjRpVbpiTe7LUOZldlbz8jiaPABYU8zK42jyqIkV/MxLjknu7VARXBaLvoPkIzwOWCT3GiS7LfeA/OtJc1ZKwmRPR+fT'
        b'8hntFxfAXSge9GnwFV0o33P4/P7uJadiJX1PecG9/DQDMUwmevqfouhZnwnzigh+ExW530TMPSfMbyLhyWjSJT4TWb5ituimQoYuc36fFt1Q4H4S2S0F/yWfn1Z4+Jm/'
        b'ZAWfyclEeQTycpcJdx6EyI3fi37yFzsiFp5YnnqUKrfjLxnCRm7ODwuJX9HGG8rcNWa86xGzx77YOfMqfgvmCVpx1i0Ly9tixtOLuIl5YR2Cw0BYEvP+0NLjBSP9yj4D'
        b'M9eE8Ain3WahIcncyC1sODkiMTkiJYKP/cX8//wA5S6eZwsdreSboeFXLsQht/wv+D2Yq+GzTONf1BC+cp+idT5pLEX3BjTAhOfTNugnng/Bs1JaDAAosVLBh2txNo2F'
        b'xuCMAzYK9mEoD5GbVpnVFPN9/S2FHG/BUJyB3Spwb/MV7u138rlkTch/E9p52EDQVW4B+F8VNdHrKfa81+NNU1ehjczO3ItCG5mWOMkpsWjw62lH2bxT2Ca2hh4mWedj'
        b'qT8z7XrTZFACc8zYzaRury0eNtAXsII9QyQ9qUGy4YA7Xwx2WmKz0CI7MFLkvUNbSKM33/ipSFvyyEnNITjC6LxhiGCGeKfuQIBQQVvjrOiHIssD0uDM2L+uy/QTvnZr'
        b'O8C/zY6PFRcbDSqIzIL3/PxEoEiwNvT4QhPvrE7iWp3IEaZwOM2VfdF+Vn9pphrm23p4mzphJTNTk3x57IR8E1zDOeHuYeMhCI50DKUaHvgInvCLhHzW8GO56Zr0rpGX'
        b'hHIoQbmVWOg8WZ90YqHqP7RZ2iwp+k+ayahgq6oIhrnTkiXJ+8yYuwfucsM5ZrsbL59cG/KWmM4tF1+DLHiichPnt/LDMkiQiF531hCxzLbzDiZyy8+BWOEoe4+fEo2L'
        b'LI9oHsjMeMf8k8PJyox/MAeAlQK/v5A0mOD2oGsskvLaDi9uJVqzEYu4xJhBmsuAKGMnzPKnU6AbH/MMPmw3FV1V3cA9F2FuMdwMFGOKZaIYktZ6uGltLRZCHxORmTan'
        b'yMIkumU7xCQjl9DNMUUgGDKNPZcU+9PElvhQ6Xk66UbhwMYd6Fm5FgHl0MxruprjUMze78aJUwYJ6P7w4/f3lc+XfOeA9ptRb/9mv8me243/maOWp71qe6p+wOkNzqoy'
        b'5xP3htw79N+qGtOI36Sr9Bfl35QU/vJnxldVn2xff/ZM/YO//dfXdjZP/Nhv268VUx49niqO9p77W+z4vtkAk7Gskv+61Vs1+fi3l//iZnL5ekrcl71yv7bncrun/scb'
        b'51N+ZJg6GlZT4Kz4pw+umbXWOn2Y+GTstRvmm/K+E5X756K3U//658KvXXX5md5/R2t+8j3TWz82DCp+4GVT+dXgN94s/M/bzie+9f2fvFem8OWTX7EIK3339rj+l/X+'
        b'Yygmx/v4f6//YHXal7/+1r76IXH57wN+WPCVR+KqfNPvGf6q9O33P46rb13rQST9nV9+f+1Nyw5RmrTvw3fPfOPvX7v15sdFJ0ZKNW78vr7/7XerM0w81vzIoEep1+zc'
        b'nzbPq1lNf/iL7DfcTv7O7/dv5Dp8ZNjzvbrYD1JbAq7vyfjuP75/pLHX9egl91/6eXxv43u3T//aymhr0ls1H6n/ru7tkA16SdYeH989G3tLcjRu6sP+1Er1VY8kX40z'
        b'DP3Ont9tT/jrR67l/+sR94ZWZHH1p/sfZzb9RuP3YxoPHK17fb4V8d6qr/5d6Q/pt8XbDOru39C1MhA62jTDXcOFcJ8cBx7ug9U6glafd5BI4hBUPZO8B027BB2hCWbw'
        b'yXKbxiG4x80artjLdQRrnFGyxkzsFopSyEtSzOAk11q9sFJVUIoDYYbXsYCBczzP8bDnVcFWgfV2PE4I5yVcB7ty5Npl6FgxDFiGDx2FQvUq168ttLvEyTCZuxjGLmCO'
        b'oPAW4ZMIecdLorHFvOsl63mZZsMPRMviaVNLnNwvCxfDrAkIeqYRTKZAX9QzbXo0YJZ/qw5917HD1ZqWw7ekskZCKs4o1gnK0izRtGlruC+xtXRfrNdfCW18Vy5YDvmL'
        b'NgCoh44FO4AUq9KwUVCYuoH3o7OHHi+5kUdrB96JlAbBxH7BWDNz/oqgJZZ627hZejD9zlpRZAINpKH64iPhyrNWxzIbRZS8U6iiqURmBTXCFPPBMQtqqB22L2iipIce'
        b'w2p+6be1sFV4ws5bBlnLFNHbMMVVPzu3Lc/ooGsSmBZKYNSdylw1/moWC1qo7YXn2lFAU6SgSY8x76UR3uFK4KIGeA76/8VOQ/8P1T31pZEbXN/rYyzhi+l7t0Vn1bme'
        b'pSrviaks75dpw7U/+o2UvpHIuJYl488Jf7NWRYpcR1SVqHKdbEEL1OY6mDpvYsQSuAQtTZX/34DPo8v/n2HybJrIkv3IFTNFQRvyXNSQmCKyRBP7v9fXZUsms1+ckWti'
        b'x+mLHSQkprBwhC+oiWWKvvYSXexlJ7EQWefElrVNsoIexuRWLrP6iHjYPKvtIFT/l3BdTMq0sUj1Rc1L9rk1r0jSvA6uFIi8oHk9bQGwGFfMw5H/j4PphXcW6twI761Q'
        b'39LOzFUIROJLeUGAFY+9Z+oZPXrM33fXDoetTB26HJLKwmhSUpNj4qNeuAShwM7ToKJnqwoK379Spo+yoGdAJmZC73ORFc+KpvAEWxfEU3fsc+NebFfHs0Jpp81PXfLY'
        b'CN2ClNV1y4govBXULxSOYj75E1jDHZIbt8GA3OOPWeuWevxxCiZjJG2XxCmZ9FxZVrtt4YgGOOgf/qT5wYGWKNHrRvkWwSJVT3crbceOlPpHuyeHd77h3vtx048r/R+G'
        b'HP5Q/bKbvmfPn11uGnn9Q/yuQaXv5Sg96ebXPQ+M/vStq2vfuHp6c2yzccJ7he8+0S/q/7vJpY0yL4OLn44lxL1xeuDJpVnP/4o4+5sho7X7E7w2/vSfpVYKgmkfBqKs'
        b'3bVDn9YTiIcHAhNu38fOyQbG7ZYl7kOpGWdDh7EC8tU8Na8/5y7Bxg0CoyoPM6ABJNeWW82JW8KQCpcBku1IgeKmeBE+DuO2+FUwvyxF6F/iIkuIvGYax7RlZN7nVcj8'
        b'bZHbQjKR0Pp4gdQzwp6x5hkCtHzW5cR4OTVaQoy/WPVtorT8fafl5JZTWj/6Xaf6wla/KKXNFP1ow4tp7cu3ykrNZsQkMrPNvyUveKHyXe/zAcDJYdExV+TFhuTVcpeV'
        b'N1qBmLoKVpG4a9yMEnM5MS6CGYIiwte/kPDKN/dsmR369efpvyJakXTJfNJs6XNsBk4Lvq8V48EOm3M5P9RQOQZzgmJUtqgq8N7EtdImlsIe+KV3XhsvG3Fvu2ul8BXd'
        b'sOjIuFCbkPjI6FCvEOXI17/Lymt2P1BO+sNPrWQcCbekWFpDz1r3pyQAe7GJe9kSt9sv0StgDrqYbhEluENtSF2dX6JZQMfaBQpw1SiVhdQYwRMtHIOmIy931SrBsO3u'
        b'z+z6ph0i3OsCgKVwFN71aigcwRB4sb7nouX2mRmWV333X46ky7ORnz7B8e4kfXrjX8C7uRdncn/mqlmtCgUfnwA3HyuJj/BH+zOK4z2t1sHymHkCI08P42kH3HDOZTZO'
        b'TvjehINZ/e+W0b8IhU/eRR8d1eS5z8oSmRrJx+ueK3anpS1RFutrKYs1VVXFBquVxYr/lLHT/aflbZGyrtguXldstk5ZaK1IeujUycWM+VU4uJg0LxFZbla4EgnZaf9N'
        b's8LUBZhirvp9CdjgoA25OIUzq3bugMwwfKjozDzEUKFMGt8DvLNOgxTOHGiBAag8fBja1KACCsUm+ASm8MleIImgzhnHSesdDYEJ7A3QYOm12fhw3154AsPu8OQoPViK'
        b'hddoxl4YsLsB7V4wtPcGzmG3Eg5DH/083g6d0I5dUUmOFli3lVT71nhgrTt6SdVtuLEPiqALC2DE8GjSXl8DKNqIma43Y53wHs7BVMxezL10dPW6kNVuzp4KZxyv2/lC'
        b'+xlT0oNxYi9MYzeMQVk89JE2XAST7jC5+/IWLHW8iMUa2BWOw3qkt7dABbbRzwxWB7ti/XGnWLgXhoOK0ASTmJsAI1iOTf44CMPpl7EDntyEGawJgHJjbLt0DquhY+cq'
        b'HHKHGQcopr2XQ4nOYXjoD9mbPWkBk1i/Cx7exP4TUCfGLhLD7uB9aKS/S6OhB+uhLX2tVA3uwzg2O9pgO05G71LdixOQF2YKmUcvw91wGrbGG2atwtwS1rlhSQw+wQYP'
        b'rDpjBINXD+IjGKWbGt6nCLUnrE7SvougCnJUNwXgmBG2Yhv9a8ob8qAxkA6jCmpscGqXi8U+c309HD1Fv2i8vvmcNdZhn7Ye5mEZTASk0G/LNVU34Dy90Ycj8JCWMyzC'
        b'GqeIPVgXBA2OMKuLzZqh3lASleqCmX5YsxaKLu5Qxnl4ZKoHj+Jg3gRyo+j1gUSSLGu3mmJb+IZTZ/fZYyXBwSPoSgkhqKvG+gB146CM+D3Xcdz0/Bqo94E243OsMQ3U'
        b'MAd2JY4TPNVj2wEsVoa8I/jYga6xGvp30y4HaH1TkB1IN1Bqu5/AofAqjBqaYCGdzwy2aN6S4iwWHDV3wXtp9yQsAtJuPTzwOwglBPbqMItjq24coMvtPgKZa6ERa23V'
        b't+EQXc8INEmPQFdYyEYrKIuWQZHZbXvo3JWWEa2FVcwAjD10sMWJwadhblUg1B+AehiBDsgOwcYtWGO9CR/hY5iSwrAK3jfByRCFRHwA4yfPpO/Hhpv+cdCPDXQOc5a0'
        b'CQIPHIz33ENDNJlCA2YdD6SxKwKhZifUQl4ooV6WZLc3Sa/DtvTMKPZA381zN/W0A2+HbjsahY0617bpEKrPEgNuIeibgzvbCacKjq7zMr+2iSCtFOpwYCtBeD9B5iPM'
        b'D8GKOJilPR3BGShQwk4XrLgOzWmeB2NwcDPmWZIYPX9jp91tyL2g4g+PjNay0mzYrbNLloDzwTgqwbKrBiFH8C6MqULxLXeoxSzTo1ByhlSYnHAtaIYeX/+TjmG6m4yx'
        b'9+BRVX3drVhh56Bg4nSSUOiBF+b70wXXYp8R5BNZyQzBrh10kzNwB3OkWOED5Thiho0+WBiIfTAm0yHgKzSENtoJo0w5Fx3Z4UI+DsB4+lVjuLeWphwkmOq5SuCQl6Gj'
        b'TOgwFon3cfqGoz4rqAt36XqGiXJNKEdpemCzMckMLWdPYT9hXQ5OrTsPc96eMA/dKuZQkUIEoQtyd0fg2GUsCIQ5u9XMKhjkC1MmBHL9eM8PKjw9dILScYLm6yJYaDoH'
        b'WYRA87StLEfs19vsb77KF7LozCfOYGccnV6PL4xa4SMFqA01h1aog4607zCIHMJ7WgSS+6CUgSSte9oaxtN2Y2OQjMZtwbvxIdCSpEZ4WbP9uA10aQd7Qq8LFOMkndYs'
        b'1pgQKD2BQtraKDw8BrnnWMrDBpxzd3HZh7Ue0B6urYo5BLKdBFRTcHcj1JtdIRiukbjA7DXRDrtjWHkp1Zpubgy6SHQqhMeEOhWEcw2h587HE/Fos8GGWDruGRYfyuKS'
        b'+6AdqvF+0BEiivPWhqdTz1+AFm9aYQeW4bglIUf5/g2OV7FYXwWml4IsIUj1cWNax0Q6Ztuq3IbxeE4v72teowOZxq6DXjsy1ofBsM/1GwbSC0ehyBCyImlj8zRAFxGm'
        b'7B0uBMC1SpfhHnRfhEoNuuJeMw2o3IV17tCSSo9kIdtJMzYRR+qGTC0JZu8jEtK5SgmmduFjo00EDKPw2BGf6Kdje/yqa7LoONK7qwhhc/G+Fh1UB22vC2dh7DjdZpsO'
        b'Fp5ZE02wlo0jB6CDjnw2aDPxpaEzV00Jdlsv78OyYOJeNVbQm04YUWxHV9F20JFoXAFBJTHOoG2XtmO5ZSz23DykmUELZKFRpQTNY1vNLMNDYAzvhNB5TqnrYyU+xmx1'
        b'zHeDJscAAglovUZrKMBSS5ggoOmH0gxsUzIxp3OewQ63M/bwBBtV3bbQnnOJRrYQ4244DGNHo/zoLsfgTsoZutE64ofNMJOBRVeg9rxSBFbvizxqx5l6qWcqsZvcNKIL'
        b'ZfRM9d6jhoFYAw2XoFByxQga05lLhwE4NJ2NpYXOY7PUIsHDDQviNbA84rTSmgs4uBpqGHDZE0K3uenouKd9m+BaYQ2hHFHaeC5fzOJDa5wUH1kbDC1KWOenKhYSd0oI'
        b'Z2qhLBVGRURtzVdh5lY64FrT6zikBI+hI+KoJdS7Qr8e8YJ6Y5b0o4mNSpdNYwlo6rUIF2sdrfDJSTt3aDhxHe+bQrHH2p3EBqZU6WCeYJHScegNZrgSIk4MYrLQg3h8'
        b'iDPnTxO1YPR3gMgASR8JO6BB74C1ny4+PAPlwYfhzhF4rI0tR2+fo1Np2XldD4r9vc5ArwWOB8L07TWuwUQ5+ug++i/TqfRDw7lrYqx2c4LpAIfrmq6YBQ1Q6xJGjPkO'
        b'3XObkQ6ddi52SGFeBytOGmqvJs5XqA9l571CAgh355xOOMcRFlcGQqUdZHvp2+tjTxwMHCDsy4+F+5vwjqsYMxWOw+PwQ1DlFgNjLj4wA/mHdrseubUa6wj8iS520nx5'
        b'osusVRaOKLIS3VBgQPgySqdVio2OpA4VGxOaNlrAzE2cTHIhsK0lVleC1XuTsO0gkZTM8BNXIfdoAqFAy02ovrmKoGoi/Br2RhlhLRHBVqIThXvw3mmdHUgQX4YdR0ku'
        b'IpjuNNvJEmvoU/uBnVePahNbPLwaxvxZgXIYv7aNkH4O+1yxmI4th5he8861TB5LhuJIs80MErFcfz8nBm20zExoioHqUJ2MK97YSLOME2LVQEUMraaXpQlJoCSNtY4z'
        b'vk7bayAO2k+MMyUQWu2wCTuMfDX8ma831gBbI7DqGF1xF84EwYNgWuKQCwwRGufvhrvI8HwOq0/SEHkXoq8wFoRZl41xLJHoyyjmmLudVcVhk61uJ9ZsP5hWJuFhnpUb'
        b'Ca5pB4sihDU+El/GEhIh9u2yhikHGL6itnm3UjKJr7Vup7DiEO0EWg7S/c7RxGPJdEaTjAQFboBcJ8zeGsL8UER3hxOv71Nf6wlz+DAUm+mZIaIeNbfXQab1KbrsR7Jd'
        b'RAerYXrLjv3Yf54EtCqcjiDhsoR4WB9x6AkkqpZ92xbv6xLU5h86Dy0eWO13gPhqWcQBqDu5hWSODphxZqGUJI20wKwWYfYDaNXGXnco2XoVKzS910VdJlKXpUT40XRd'
        b'9SIMWzgf9jLap0HwNQBVmrZrZHRkD1R1d+P4uk3KUje8s55OMdOCYL5Tx4TYewmNORiE2efh/kEgquRCTJAIE0kI+PgiNmLTniQiVlXQTZykg4T8Ybok8XHbU1BkEU9M'
        b'ugEGfDH7LLYFOUOhl403HVs2FLjGmvgePcFkmMLzt6Ar1ArvhEGm3nUzrCFeVX4OJ5MJcKpPYH8w5ts6QI2EoKzZizkbc+jUCmAw6jypI2VEuAuMjeiIx4Oxcg/mQXPC'
        b'Ljr6HkfIdSGQ6cDyrWf0I3fs9g2FjmB8lBBEJLllj5aqhdNOfWMnKyLp4+pYoHfYZzNxwnkLaDxJo1ZoEFw9uQyFfqcIQR4HQcsm6NIPx5F4mrCBVU69QGjQeS5iFRGf'
        b'Chi0g4dqdJiFWBMFBetg9HziBcP90BdHDw1CXSTRhjppLK0q05+gfdwJSvfB3GbitdN49/YlO318IorDBmsSnXu2p73NgDIHn5xnQJkVz2FyjmDyKvZHYM81ZRJ6svWu'
        b'0xFmbVpDAu64qYMuVmqTJHnaL8Mdym6vs7ieBrkhRscvqvsR/25nP5C9neh+NVERem0fE5puaGvAwFW62sfYfGq/GvHKSZjXCsZOrIslXtutgJlpWBUQAXPX4+mrhtDz'
        b'JMgMcdkBSHaYgbkYAv6xUCPMSV6HnZYEF22EOv0B8Vh+w4xoQyOTdqNpAfkXnC8bqdEb5UQ3quk8irzPkJjXd9P/5unoqxvUfZAE1nbs3ECUuzvI5aomHW8RMMQtg0fx'
        b'iS66MKmVSliSlUzyRFmgj5OKOQ6H+uAdqPanRybhrhL2aURg/gnWzZV+nZcI9VqkpdyFpqs4epFAddhe3dqDiFNdjLZb7DUX0pva1hCKPiRSU2RiKaOzrHIgWbPMUB/u'
        b'x5utO0K4OrAGp48S1bpHqsk4MePH8SzDACuSLLBrIym2fXj3JtRb2hLxe6REk2Vjl9PRCKer64MieSGsKtLLCRHqVaFiK5ZccsIGLwvChTE9nZRQIn6z2HcW+84T2nSs'
        b'JxBs3EkCy5QT5OGjxHhoTyXtO5+0ZEMHfSKWNfuJwo/t2UjLLouGeyQuKGDPSWKV+QSplS6XcOKkMebI4D4+jKB5HxC01Ys2pu9LPJticJzud2QDKwb0AMrDU6HR5SoU'
        b'bsQChSAsioW6vfTsKIyTwFmDBaeIRRQROWzU99KEZo9Nt30JQgdwKONMHImJNf4uR3Yytax/N3QeTN4SBFMEUqXeMHI9Rj+SCFCdFgH4uC22n7jhdekoVrptIZgYMtyA'
        b'WfZesSeJPuW4WinySBU9UqQ9jymIxPYirNpOb+VdEtKWHotPLuRXkQxLkiC9xGNYwlP3elpLROIDop0bSMAotBXyZIcJaliOgXi/yIpwqS5YT+iiTFeey2z6YpHYQ+RO'
        b'TK4hFYWs02PEHluwyEbMy7dMJxNzybZOc5cyl7ZqJB1SJd4jpKg/oE5n/vCW6rpzKlC9x08rRI9YUrkdgUIbnVIVE9U34d1jbt6QG+tiYEWEZgo7jTOIL7VC0zHtg+eI'
        b'dpdBYyiWkqxC2IvNO5i1hZTu8qt2aa7QZ8DEu5vQGRGCeWrQmhxCKFMJ8y6QefoEVvnQPdL3hIg5R+hjB3SLiLrmndQl2a3Bnq7rgeNZc4K6rDWkCIxsOcMaTYt8ac6c'
        b'CCKoD4n3VtI9k3ITcwNy7YivlgdA2SbSEUYJGs7S4ZRvIgI3CBW7SUPKSb3oDU88CdQ7iEUUEVCNmpK2lE0aWf5uqxuQ50SC22OiEMPEC1pgeD0Jwj1Qtyti1xUplipF'
        b'aGGt+yXo3YGPkq3X4fQF7D97bBX0Kt1Ii/BOvkj0sxw6VJjBAGpNjTGLDrafCFEW0cauoLM0VjGdZ/UZ/VhC2GlaQtl22mrXvtWqp9WxKSyYq1z1Usx2JAUmk05lEImK'
        b'zjuylJnhM1t8HTEnkAha6x4c3kRI0+1kDSwXpBfK9pAgVEr7yUw2TJMRWypLoT10wNzhcyRIVkLhFmhSwoEYLHOHqv3YcpJ0Kda5dk5pFRYFrw+zcg3DchMcUIaqYKhK'
        b'JjyZs9JMw96w5GTsop+Kmxq04oIdpwJJfxwkSlzuhKOuR2/oRIbDhKUGTGpiszvh1Z2dOGh/jFC7F3KRWXUKtEh7H4es1dB4kcgAVO93P+tzLvn0WUMShvKJjU8b7sL7'
        b'yfZORCdGr0iJPHTCgK0BzKdFY/9OUgPKtuhhvSGj4sTu8hxuE5JObCdJsYDZoax8IomdwpQ9ENC30gNT5yAvnjh4B/QdJvQd9LwNgxdZaiLd6qCHMze9zEqJxTSfiyJN'
        b'qhNKdxqa3LImmXPch2kQWB4JM9jmQP+bxzkzA6iOSLFJNSJhq98FH13QwCwNnBVD04Xb5wjSG9J6iH+tZzLwU6tMN/FIbpkhQjrkYnZA6woOGCiuTsfWcEKQrFAizSPH'
        b'z2Ghh77BQVJb5qEmmc4zV01f4exFLz8iPmVOqwl8quGhMXZtNfJcvxfGrpM+kBdo5GsbdlCJuNqjE6e4iWbUdx1NUg+VO+hUZlVpF6PxRGHaiKnMReNkGkxawUMo2mtN'
        b'C+zCxnj6R+mVbVBPXI0IfBkD13YY2QJDDgks/dgZR8PP0Unnep8yZKImEqXuPC0mgW+WEDvLlHBo5CgxuSaZKXZbE+0dw3a9U9CzgQhrCTQcSPYiIbuJJYJkH2D0dQSy'
        b'bsaRdG9ygISFdmMtZtfywu4MXVdV6Lt8nkhxsWAESAmjUyu7ZEHLIo6GrbeIGkybEjI8IB0Xur0viGIx71AckZ3GC4eiiDWMYWMErbAilfhwNr1BIjk+CAuHh3HHd+K4'
        b'oTY82XiWoKFWHzsP2rET2YK9hhE4HUOAw4T8PqKMs8k4d0FhrzbWmWzFCt9EImvFetimS/pX5XUSpTJhPomucnw/9Or4Wu53Mifu24JVZ5Sx9WgCHXqD5ea0tVYxBseP'
        b'6upgi97tNGcNyD0k8SGg72OJ3NB1i4hBa9opdyg6R6T2jjU80o8g1JwlxJi8efoyMct4KJHiCP17gOS86ZArRHAb990IxM4ztkSZ6rHfCmYOXYDBdRbHiDBUsgumS3hC'
        b'tK2OCMSgDm1jDudvHfeiQTu2Q8XlVUd9ae7HJqwXtSs8OkhUOO+iwob9qRLsSvseAWsGtujDA38sWtRsT9Pk96Bm2zqm3J7xUxPDhC7m+8BDRVsYPKdoAL1IVHB8OwHB'
        b'w92ncA4K7WJ2E3iWc3tJ3wZbImTMRFenYwM5RNcIPnNhmDQDfJLua2tFt9WPsy4HodcU6rRMV9PZF8N4OGFr+/69Iug1JrrSZwF1uzFzPZG7URgIxOaT0OB4hshO3jFo'
        b'DD9DTOHhKSaftGHrmeTNCtLovVhtj51XscAORjcGYHa8A3TEHiLG0EEb7iaxtdGNCA5Me2GhzRliHQ1bCJ3v2q4/HY2dO1edTcYnPgRr1cQ8crbpK0NzbDwME/VqohmG'
        b'fZQIBeYTfUlnLydwKYaODNo0savV2GUPVWnEUGp8YgmYSGupsdGIhxxVM2cc3B2DtR4Gl2EWejXxcRo27IbHB5OxhiUg4fCptTAfINqFdzWUcV5KC831XgXTCswu0r4b'
        b'uqIM3KH6iMnq3aR0FbIos8E9RMtnCSgeEhZMESTMJZHuOaBH514XGsYwJzLakujqPUnQwagkdZg4h12xvj4xkRdIUB3VpFXUE8/tV8VRTygKg5pT1oZAOsYdvBerHoID'
        b'AVCqdyD4/HVs8vBesxXLHXBkTXQQljhJmOBKNCiHdOhmnPW6eoMOoChUm/hXKz5ZK7OAaj0/zA0LPHrhkLcbYXjxPqxK2RWO0xuIHg3RrRaRZqh4kYjDgNoZU05gGOG+'
        b'T2dZG7YNRnBigxVhbi22XyOEK4FhS1KAinSUiEX2JQauokmLwnHueBJdzz0kCaFMBSZ199gRRWu6pndbazNhVx2Rmyc2mH8RmnZeJqScv5LmJmVRm1gjWgbapNpOSiWG'
        b'2IPlB7SSoUNfMXYzUdwHtJkRoofVW8UeAceY+hSGj8JwTIMQa4L23mqzRxPLTM+ukRGM1xMHLyYJfiCDTrtqW4DKSRjagfWBBN71RLYfqzF1HPpNT9Jxk1INJQaY4+/G'
        b'hB89Gmzw4jrodMTBI1uQJBqPNXRCRRug2W4d4WfVXmhYRUfTkEJspzsCRgJNCdDrJX7bTKDdeDdkhkKBPQm/+4garjtpZUJ0oiIas1VgJCL5NnGubBg/s4M4ylgEI+FF'
        b'SqnHnaBXfScdcSnWGV2kQ5rWxbaoVTikbJlxcG+SITzYCQ+9bhBQdRLr68A6Y5xM9cBeXdalgrjoTDRxggxV12S6wyYapGLDrlTo2CPbioP7zaHHRRUbU3FAO/K8EXTp'
        b'aCdB5Sos9oyigbLgvo2SozfdJ4kadCyPZGbeiQd2+sXi0AYiDb2ERY3BG3DejWhXDTw4dnCfiPCikPCS5G+iXBUwqRaJeduJPbO4RlcYXq0iJlowdTGIqF4nXckjGjVH'
        b'Z9Vp4uL3oF0Z7kZD7m7stSXyn3/rClTsCkJmIW8TwdiFPSZEUR5Dbsxm1h7eCFptCc3rCCOGSdFsDFYx3o4zhlATsMsz8Shxzx7owUEZvXIHxsz0d5PK0Q5dB6FPwZQw'
        b'qRHmLVYZkzB7bwuW3cAydjQF6TAqTdy0h35bvhfaNp/GaWKTWK1jvtccm3ZBbUQgwU0+VicTW5q7eg4fbtt7ErLjUokw3rcT7YCukKv6oaF06nHROAP3QmE4icTnchLg'
        b'7tFpjTgTXc0x300q4TTmJTt7Ru4jIpCPhddt6XBH1cUEeX3qTDSmi2ykTdeFp1y9CY986VftUO9FOnozPEx0x6HTnDGO48zecy5QY0lMk9Tfo/tw3IMkuIdq4VtJlKs9'
        b'Q9gxrxRK8lrmBnqiNE3K1IN2B+xkqJRFEM1waQ5nrIkc1xKATu7GcSMSeAOxUjXGFfrNscHVHsqlxOFaNNgT+7RjSGWcvR7l7k7iQLbHyd1mmJuRQEL2HHYfJBAYhWYV'
        b'nN2hFEeMp1+Mrf742OImZJLyV7XJTUvNH6vDuWdtkJn5b1+H+/CYGbTaYdqP9kiY0sWsRSTtdkKXuwHWXfPbfNae1l6FfXsx6zbr8GFK3DE/CJpPkrA1YasYneBoBMPu'
        b'qoT6A/TgPUc63Nw4QoM5LWw5DzkkEQwTeynZimUmSrTHThVbHLoRTUJgbuhVuLuP2HIJtEhx1EgFG04ZuRkRzAxYKmivwUf7T0KZ5gFlIpuPMfMoiTP9jKhtxyERMfAq'
        b'LHXQjDgOOec8LXelxqrinPbpjM1E4Uk0d7l8HEoTsdLRnxXapLWM7Y6+QSBSsBmGdZw9CY1bDeGxKkwGXovbgj0WRLimsAFyLuDjq6qYe8SfUCOHVJMeIjvlpLasp8Ou'
        b'WYsP1FWlkYZYdDY25vxFJ6z31BQfMaD3BqFcESp0DJkFEKZi1Y9Z2+PkWmb5JNadCbOrYYo577pN15DaVxy6fx/J703b6CxaYWiNbTyUe20kxCgh7SclDeq20R3kHsOJ'
        b'vWokwc+QZNB4JMMQ29RvKdAOKtygXk/lBuFcBf2rHOat44OvQdN6UiqzdXf5woQRNGrv3Keejnc8MMf0ohJ2BwCRtgkHaIJ+gqMSvzPMYIrdaczmRVc/QwR4mPhENnbY'
        b'Yf6ti+uJV5MYdIqefeBD+7lzGicz7Eg2g05Cmkpi1/lqZ0LTzhJaNgPjJySSduyg7c3fhPtrsSKCpO6JJAKYwXQjgqv+m5h3GwqImJP4cSeQaFTPobSfMMsUaZrMmiBH'
        b'hAPMNlV6mhgx0bHY/WZ+WuZYRkhw2vw6fd1oHBWmYoQdxrvM6YbncSgKBpTcg2mWSZKTOiU7cNIE5rF7Z6wabSkHW1KBeYCzzu6FChlUGxFBn03HOk9ok9LHLngcQRyn'
        b'5xbRx1LCp/t0H+Wqa7Hdg+hpPx1/MVbcwHmY2auPBTtgxhbbzL2xKI45uo4xY1X4cTqdnE1EWQrUZdgXsZpAf/yaGSH69FbfBIK5Dj1HWluFgwFWb1xnhQ2bjpDMQOjh'
        b'SgAxp0/XoY71e9ZjpwapjzlBkO2K0wegX+UqEZhKkoGqiEC3iwjqHyvCA1N3qFEjHaHTQQtaD26FOicSF3KMAlZhz8ZtioqYf8IVC9TwjutxUo1n7EjMytuNI1qJOGGv'
        b'7mkCU47Q5oSVB50P0LmMQb2McL+DiH5uRrCZNksDmyZyMA1ZZgTxg2KSz25f2UpAV+kHOWocMKYvEh2fv7SJiEIj5iXQwXUxYjDhQAJIZWQ0tO8iqGZW+EosNMSxHaTb'
        b'lEdBviK0RZtBjwweujjjJNPTMfME0bBxr3Ri60+cFEm6bodiS8y2obN5aABtN6FGhyAzfwNzKCvcUNwRFUAj39+ridUkQSimMzkoW297PKl8JNXfITpRDl16WHfY8CoL'
        b'rPCnw6uHxxeuWECfLcy6QbuVAtStJxmrIRB6L5HaMwjtthdJCiLuvcM5YRs89tichG0WUOsBXdYOR3BMgVhLzbH1pNw+wNGtxOh6GZbU+esediJBu98O50+aE3mr8QvW'
        b'vHgzYPUZgp18zNzuRXPUbty37sBNEcmY+Zew91aMlUQoIfXAMnqhgBDxwWHsEm+hM23hNiRnwvn+lCM6jskSeR29Kpy2knJD1RHzjZ7MuLRLFEOcu3qzu1CoZ/AAdHiy'
        b'6vxiB9FOVt/K5Ty3VDF/5DhLt5KJxK4iHFfH6hio5wlaIbF6chvZDRLeCwNJsxdaJivfgD5PX5raUWRFcFloCSNChaKe1bSQIi96Z7eIxszG0tVQzOc/dIaEXrlhDcbU'
        b'8P4RrKPReMkNGN+IRVb0ki/LtGehJUP0Fjev5cvoK29uXiM1BstPm/HRbmLRark1DkZWk+Q6hYNWYv4KPNzu7+lBg1mLsN0W8/VJ2eNrq4OCqEWLHAFAGzZYZViJ3XhT'
        b'I5719r0AKQ/MdLjy+MJf0w+JrKT817+Okgi/jvRPu3F0k1A56eF6+S83me5w324pYhFmbnw0niYX8+V1/5ClTBK1agmcvun/to/JCf3Zmd+UfPTmvR9vDc74ZK7G3Fzs'
        b'Z17m5nPwkAe46r/mafCL335ote5LX478c8Yvgtdu+M/fPKhz+uVb03/5NP3tUrWor340rmF0+vtTTp+siXTTObd6nf5WydpfmppF/+axyck+NQt9sMr5SuGXRz7+6qcZ'
        b'SWFmsSb77/mnPdhx/y9Jmgler8dh2De+lxb3+ic/vdIGJ0sO7e38oWrUX8fSjH/qdNX4facbxuXxu+1qew5/7+brl1+/1GuWEjB8PPu9/+k5l+f/vlXdRv+8DMeTbXtz'
        b'd2UpZsR6ZOhavX/2/bOD3eXrh940rst4d2PlkY17OpJ8NtnHJIu3tdYFvV+Z7B+uZGER9vPs6IPWP/rTDzy8/rD78Q++eWvdwZmxhHNDHw3EWLgPHk32s9j+xw87fdwi'
        b'Gq91RZyZjJg/XqSZ+u3vxTRM/mz1W/VOvs0W3t+2W/Nkp/3GoLFf1ZcrvNuRMnU8zy71O+/+1+6PJlwsd378PxpDcceC3qwbU5ob+PWf+tvOlv46fk/jkNbuvt1zGV57'
        b'GswP7Xtz4oOMP8V+fGrrtTvv/vMX3/zb1iOd5d2VR/YrvhPxpR0/ym/6wTf1tnl+pTl4eBvevfIw9pOk9VkHf/7R1/bo/CD0zvG6PX/fn9661tWoK/2dv+T+Y82U+Zf+'
        b'/v81d+XBTVxnXNrVZcuHsDkd29gQF2RZGGxOxzUUXxhJNoTDHDYbWVrbwrqslXwBNWCoL8xZAgYC4XYAgxHGRw2leY/JUJqpKZkpYWkINDOFyTBp0yRN4hTa9+3awCTl'
        b'j3Y6Q2ZHP0n73j7tvn167/t2vt/vizr+z8dJi9+syZz+8GNz/atZk6+HHK0ZWN9Z8+DhrbNc5bjReGb/zLoZN7Pa8wesO3l77JYA49+XLv6z/tv5d/u1xvAJ66bWLR/w'
        b'V2WnxhguvcLtPXn3Xn9J2j77vJ0F5b+90z83bmTHtYzmlIU3zjnN/q6bpviDmXThtjzLwspr85Z2fTihOS7hQr//1oNcs/z0MpwyvaOxvV7Tdb6u8JF5rDJibNrePQsj'
        b'nW1fX/ksKPLzGWtK7ma4gp98sS351DcVZZPaZm9ItKXqPjg0+w8lfztinF195NB9tvXJp41P3vo4oi18xONvRtU9WvyYq9EGiomYT6B6YrYYhelkFvGTtuJWpRAXv3Tc'
        b'iqGg1/zK56LeU/FJLwQNLsItFWoyr7a+gP6G3s4WeGDSsfiQ2hMcMD0zmCzzzaEeXxBZmbtpSWSNTIV700S5kLpJ4erExaSaUKkSd1WWBysko+fQ6Gx2iijS4s9dzVUE'
        b'lftwdyhqQltCVcGBuCOUGNuNFXKJNkSGz6wgnhLE467BXeqhqplkan1WuwK1DLVtkilQr1wvsLvSx6A29WB7+/IrgAFwkkokXkGPdwopLrDgsxxqUZWTk+NIa8S6R43/'
        b'oUV8UUFcMeLHe+Pgmrq9rCj1Uh5U7iCr+Q+lXsoDf5gsbuqPINj0pYM2Uphkfywgph1nGLvLbGUYISD7BgGJjqIo6VRp9L8oCuhrYZSKlklVtIIiGx0iDwsLC9BEa5Qa'
        b'RVjg8HAZNTxn9DhSv1YyAyRPZkKANi2j4HN0LWlLGhGXAfuslDRVDN+2UNIUeM+npGnintiI5RE/09AhdJiGkibUSsZT0iyxREfFU1ry0hFcLzkjg30KKkHYA9t6yQkZ'
        b'hFx/pxgKDtcAl2P0cy/P0qchz7TnHlz4szDw5Jc/KF7uiJSKPSKEYEM/6WAUAMNUcsvz4nRkMLnpUc8iYqj1Ep9sGzg2eUbUiLYpJSFj6ChHhu3BQ4mMi5BKJA035kxr'
        b'ycnFczSZp3/af/7JW1F3WmNiNl19NWbi+qvewJENl+X7Pzvjj90YdTPvo3EFDZw7KMW0QH838fLAR+2lOTeVlz+Y/3574rufJ6263X78QlxbIVne0/eo07cZTCsHrpcw'
        b'8kfvbO/7yx937Gi6vSTgtf3O6zvM7zWa68vwAZ0pf+Qp6+uFT7773a7dp2ZNvX2r9/6cG0X+a19FXzv46QXNlxkXDqd/8e6d7re/2vt1Z/WJ1mnL77z34aGW47VH/zp3'
        b'1uLxvzdN2Lly9f4Lptr3ozQRX8bcqN8stQdN2UiPsjx6Y1T02kexv0mbG3lPk93g3hJ+dZ67KfnAJ5T2xDV3o67gaF2k3OluDiv80/3o0LYFV4x3ekxpdNeef4zffO5K'
        b'UUth4M4O7ViBiWGcjI+BIZuXJ5B0laD61KdGfgq3hTDCRO4KTDDk6Sv0+DzUgvj1YfgSjQ5HLhKWmXXY70DNr5fBfQD1AHjyQ+5DGB1N7kiTKLjWRzy+DgPeDMrOJqVE'
        b'IaNUxBneLa6Wh1DHStycSMzVRRJ0bCXxUrpjhMNGjEjV4a0TgWO8RSoJmERNlxPX5ViSKDk3snZILExGHMH9uVLUERsq0JPHEI+zyZCkyknI0Q9WCcFNdC7xKRqFY8OI'
        b'F75pUKyNnDLw0skyIy6aGz2TSbuodzI5zpSDW7Q5MkkY3kUT76QvW2B6Uz60zzA/IXdaslSixDsp4mltUuA61CmS6nfLcL0hCbVoksnRhkHZtFj6tQlThN7MI73SYEgq'
        b'YJNzckxiaQg+S08xposqgI3otAs3xwOBndjVxD/vXihFfRlJIrW7NWs2EARNZEWWVVVOkcKDO7RLzFl7FP1qiU6PW0AAMHyMQ4p60N5UkTZ+BP8CXdSBEp4RftIUISUX'
        b'L5O8sk6GNs7GTaJE2X6N0QCnBCJtpL/ROexXaym8vZysvQJd+8CMQu65CpLkwByKuFhd1YLtEonWF6ixPxRf5FAj7nbjznJ8AncQ6ySYFI6XKWm30MPZQSBGB0Is0BaY'
        b'KahJjfZR+Ag8zRXHS8MaMhiHBByj8TtCgtxYm1dLCi3Ij3sMqH0iubmgWybIR+bloJbEXL1WIcnOVKKeqLVoV4rYY22j8RY17sDdVbiTTCF4BzHPQpVCXy8h/usZiALb'
        b'OsiUl6+Vgq8+USDCj19thlhrPeiil+vnojbREIvwychgPmMUuiSK+OR9pM+bQDbRSEkCfkLJtfAQa6yoCeDHp1Gvbr4+waQHnuhhR9AIOhD9Mk4gyY9Cl/CbBh3eQTzz'
        b'FsMk0gT5B5ErCE+m8UF8EokqiaET0AbdvIR40j50Ov61Wo23U/hs0TAxX/S+dNypA8/NQDxESAB+PHcoYVT8y5/h/+8rxsiXYKU8S4zshqUpRCVw61XCNlxQYFMNUjiB'
        b'GUYN6raFDSZCJjVp93/PMhvaCkSqlWBAJPC0nXV6isl/j5d7fW47y8vsNs7Ly6w2C0GXm3XyNOf18PKiai/L8bIil8vO0zanl5cXE0OLvHnMzhKWl9ucbp+Xpy2lHp52'
        b'eay8othm97Lki8Ps5ukam5uXmzmLzcbTpWwVqUKapzmfg1dwLo+XtfKBNs7m5Lxmp4XlFW5fkd1m4YMyReajyVxGWgpye1iv11ZczVQ57LzK6LKUZdnIGQcUJU9nnaBr'
        b'xQfbOBfjtTlY0pDDzcuyFmRk8cFus4djGVIErHB+mMNlnTVDzJ3CWG0lNi+vNFssrNvL8cHCVTJeFzEinSU8vcxk5NVcqa3Yy7Aej8vDB/ucllKzzclaGbbKwgcwDMeS'
        b'fmMYPsTpYlxFxT7OImS94gOGvpDL8TlB2OqZnSZ2frzHBZacF6AcoBpgLUAlQCkAVPWsAigEqBJotQArBJYcwBsANoAiALB8PQ4AICV68gGWA0C2IU8FwDqAnwOsBlgJ'
        b'YAXwAbgBnABmgBoAO0ABQBnAMqE94OStgU+1ACVP+YYwvgKeGl7frnqh4SXUHFAVk+HEWkon8RqGGfw8aMQPRAx+j3GbLWWgdgaMWChjrblalcAc5JUMY7bbGUYc1wK3'
        b'ENLs8Qox0a3nE9izYcho/l4ial6VSsaDz86mgaqikItJBtbE//7/qpVQwwWlw38DHlmwdw=='
    ))))
