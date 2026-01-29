
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


"""The Python Fintech package"""

__version__ = '7.9.0'

__all__ = ['register', 'LicenseManager', 'FintechLicenseError']

def register(name=None, keycode=None, users=None):
    """
    Registers the Fintech package.

    It is required to call this function once before any submodule
    can be imported. Without a valid license the functionality is
    restricted.

    When calling this function without arguments, the license
    information will be read from the environment variables
    FINTECH_LICENSE_NAME, FINTECH_LICENSE_KEYCODE and
    FINTECH_LICENSE_USERS or alternatively from a license file
    referenced by FINTECH_LICENSE_PATH or a file available
    at one of the following locations (*new since v7.9*):

    Unix:

    - $XDG_CONFIG_HOME/pyfintech/license.txt
    - ~/.config/pyfintech/license.txt
    - $XDG_CONFIG_DIRS/pyfintech/license.txt
    - /etc/xdg/pyfintech/license.txt

    MacOS:

    - ~/Library/Application Support/pyfintech/license.txt
    - /Library/Application Support/pyfintech/license.txt

    Windows:

    - %LOCALAPPDATA%/pyfintech/license.txt
    - %ALLUSERSPROFILE%/pyfintech/license.txt

    :param name: The name of the licensee.
    :param keycode: The keycode of the licensed version.
    :param users: The licensed EBICS user ids (Teilnehmer-IDs).
        It must be a string or a list of user ids. Not applicable
        if a license is based on subscription.
    """
    ...


class LicenseManager:
    """
    The LicenseManager class

    The LicenseManager is used to dynamically add or remove EBICS users
    to or from the list of licensed users. Please note that the usage
    is not enabled by default. It is activated upon request only.
    Users that are licensed this way are verified remotely on each
    restricted EBICS request. The transfered data is limited to the
    information which is required to uniquely identify the user.
    """

    def __init__(self, password):
        """
        Initializes a LicenseManager instance.

        :param password: The assigned API password.
        """
        ...

    @property
    def licensee(self):
        """The name of the licensee."""
        ...

    @property
    def keycode(self):
        """The license keycode."""
        ...

    @property
    def userids(self):
        """The registered EBICS user ids (client-side)."""
        ...

    @property
    def expiration(self):
        """The expiration date of the license."""
        ...

    def change_password(self, password):
        """
        Changes the password of the LicenseManager API.

        :param password: The new password.
        """
        ...

    def add_ebics_user(self, hostid, partnerid, userid):
        """
        Adds a new EBICS user to the license.

        :param hostid: The HostID of the bank.
        :param partnerid: The PartnerID (Kunden-ID).
        :param userid: The UserID (Teilnehmer-ID).

        :returns: `True` if created, `False` if already existent.
        """
        ...

    def remove_ebics_user(self, hostid, partnerid, userid):
        """
        Removes an existing EBICS user from the license.

        :param hostid: The HostID of the bank.
        :param partnerid: The PartnerID (Kunden-ID).
        :param userid: The UserID (Teilnehmer-ID).

        :returns: The ISO formatted date of final deletion.
        """
        ...

    def count_ebics_users(self):
        """Returns the number of EBICS users that are currently registered."""
        ...

    def list_ebics_users(self):
        """Returns a list of EBICS users that are currently registered (*new in v6.4*)."""
        ...


class FintechLicenseError(Exception):
    """Exception concerning the license"""
    ...



from typing import TYPE_CHECKING
if not TYPE_CHECKING:
    import marshal, zlib, base64
    exec(marshal.loads(zlib.decompress(base64.b64decode(
        b'eJzcvXdclEf+APy0LSzLUkSKdUVRFtgFFQv2Lh0jVqJhF3aBFVhwCwJZFKR3ey+gqGDHgmJ3Jqb35FLI/fJLufTkLpcryZk7fWfm2V161Nz7e/944cPDU6Z8Z+bb5zsz'
        b'n1O9fiTobw76M5nRRUslUlo6kdYyjYyO1XE6uoRpohMFaVSiUMtquVJKI9IKtEL0X1wgNovM4hKqhKaplZRWlEBxlM4pfypNJUpoqkCmFekkSc5aMbpKyb0Lucp0ks20'
        b'VpQoeVqygd5AOaUrnO4PkyxL18mX5JvTsw3yRXqDWZeSLs/RpGRo0nQSBfuNCIH2jRO+YIg7aVUK3a0FLPoT2f6bwtClgkqltagNpeJCupIqoQqZAicrXYKgtDIlFE1t'
        b'pDcyCd3uERSpCjYupXu3CNFfOPobhAvlSNckUAp5XCf1N/x5WaYYXS9NF3iMY9xQB6ql3LN51Fd83h9nt1L9QkgKm4ohZCqoCjaVdUBJ/z4o7YX3hJKLs4Sg+xXrTAlK'
        b'uAtuWQYrg1fASlgT8lTEsohAWAdrFbAK1rLUAtAONy8XwnMKUKaf/101ZwrCvaz48Dv1t+rM1O/VAbrgz5SaiPJTmu/VryZ7pqSnZjIXNvtOfYcuThNFF32uYMxjUI6R'
        b'4BLscEYlB+FyYy3KQFgdwlAjR8HN4CIHz4EOsM8sRwnhXngMngQ1oAE2RKOUoA40iCiZBwtubhiRAPcZ8Sgr2E4mQGHEmMlf8Mv7bjNSjdkFOoM8lUeQWZ0yjcmkM5qT'
        b'ki36TLPewOBOwOMm9ZXRHG2U2rO2sp1cqsWQ0ilKSjJaDElJnc5JSSmZOo3BkpOUpGC71YQvrbRRhu+d8QUXMgQX7Ikubl8LGYYW0vjK0cIH+GoZiz7IwFa4JTpYBQ65'
        b'xykDQVV8904OniiAreAKbMvEwHw+70V6x9MHnKmcO/SvPh1MOUVQad48szlN+LUbpS5O/jj43EQbKn0ym3wdn5GRMYJtEVBy9dDRIgufxX0V+wyk8Z1a+r+RAv5llbdo'
        b'3gzah0IppX/0tlIWJXo5Zio86QxaghE8lbAhIXQpjwwBKmUArAwJjIylqTVPi4fDqpih4IyCtozCjYaNzmNBqzNqT7RSEgCrwTnQwlFDwE0O7EODeNYyEqVaAI/AbXg4'
        b'QwJhMxrcOnwvopzjGbhtIeiwkDE/shFU9jPk8CQ8PALUrVWwFi+UbATcAbdHKxVRsQJKSBcmMF7gIGizDEefhsEysDOa9CnCpQORkUqGcgZ7GNgyDpYTaME2eIqFNfGw'
        b'OipWhdoBTnGUByiBe9AAwKIlqFWsZShKNx82+ERHBkcqCZ4KKBmsZsEueCQua6nFG5dTA8rnoARgnx71KMfR4DC4CUstI9A3DTw/jMfv2EhYp4hENcDtYEcoC64NBttQ'
        b'tw1DiWZsALeiJ0xECaJhfTwqw3XUElDJTkd02IiSYFTyXQXrcZLIWD6FDJ5NhDfY8SK1rYwU93DnCDRYObAG1kbjxnrCA6znUng8yxW1A/cIvAmqfGFNcBysB/vA3shg'
        b'lRD1yEUGXoSbFaSQJLhnYRCsj0GdHqxQRgmoQSNg3QIWbk+Bp0iXBSzURscr4dXZkUGoY6sig6NCVBGxQiqYEqCBrIfXSTHw4iKwA8MRpOLArYhYFU05wyMMvDIanLAE'
        b'4x6rhEfB2WiSBLdoKaxfEhCNGEA9GqyGhCVKITWfE8IiNLpHLH54CMCRQJS6Kj7mqYCIGFgfFxO/HGxfjhMGTxMsBJvTe7A4pjsjbibcvYJG/JOt4CoEFcIKUYW4wqlC'
        b'UuFcIa1wqZBVuFa4VbhXeFQMqvCsGFzhVeFd4VPhWzGkYmjFsIrhFSMqRlbIK0ZV+FWMrhhT4V8xtmJcRUCFoiKwIqgiuEJZoaoIqQitGF8xoWJiRVjFpIrJFVMqpqaG'
        b'2/g0VckhPk0jPk0RPk0T3oy4c0K3e8Sn03rzaVeMxH34dHmcxR/34AWdf3QwaAdHVQMwD1i+jFAbuIw4LKG2OKVCiYgKEZIH3A2q1Sw4G5JnGYzS5MwFFaD4KViDUJCl'
        b'mE30nEGgnuB29ERwKgi0+oMLwREIt0EpDUuehddILlAXSAUplLAyUjA4gxKCk0yQwYeQZbYAnsDDJS8IRmPPRdLgJjgTwWe6sQkciIZVK0Nj8CcnGhwTLLP4YKypArvB'
        b'NcRjQGlCBIaDi6DBxZkrLZiLRoKdMXpwLEilYCgGtNOJoHosyQXq5OBmNDiJyFMI2nMpYSYTAA8gLoKpBhywwv3RsBoehKUQsRJU4WganIG7hxIwhQjK7eByGMFDGpVb'
        b'T8esHk6KTQPtm6IJxgXToBgUUcLJjPdM2EY6JRXuhh1BUYjO4gV58DIlnMPIwH4fiy+u8noMPEsKDFDS4DQ8SAnzmPFg5xqeVbSC7aA5B7YiQg9ALTHQs0ApOEWauBKe'
        b'XQ6qFagDojAse+hFuQbCf2C1LzxOiEURqRwSw1BicJtBA7YTVpGMGaAY3gbt02FNLCIuxkrPnqklfT0x0cM1E5yC1fg1uEgvQyLlDGn5gty8aMwHYC0Ht8JmSjiEkQz3'
        b'I5mSweU00IL6JAKcQdkK6UVrwW5ST4C3FSHTMcQxVRjAanrx+rGkVSvgIdSs84lBKlgnIDWtAHtBExkCeGNSEGIpWGCA/aCYppwmMYjx7obneD6/D24BRxFTwrCg/OdD'
        b'I1G3xgko73RuQgGoIfxkMSyDm6ODsDiJQtKidClLOQkZsBMUIc7EdCMZTCU9dSakMVXQDp2JqUSaUSGLaJEhtMgS+mM2sgnd7h9fZ2Lj9K/k3BWYZqEXE57b+Z365eSv'
        b'1ZVpX6P/nOKjt2vn7HOKmEjrU+Uuz60Odl5VPGNXWW2tdPicf6VumdYuK1cLX/ei3hXI9l/+k0JkJhJpx0KWF3qwLl4B6yKJ3IPNEygvfw4J7sPmkYSPZ4LL/chGCWwa'
        b'AbaMMWPlAuwPRx2LqT44FvHUKpSQSrIlHQm2olFHg7CTL64S7t8EaobAI6AhHiE8qMeJJHALGsiNYIeZCIZAxLBryPcYFagiFbJISK4aJfQ0YxwFh8AVUBSkjADHQTuS'
        b'lQJKDC8xoHQ2PGIejbUNPRo9DA4vXUAdjQUMD49/oCAeHBxvU+N6KVbkLVGrOrksjSmDKGxueDw2iTkxjX9ltASrboPsqRVcJ6s1mTtZkzHFiLmoEadXMF2FonuM0MbB'
        b'9rJJ5lJcNKYOqtjtP/0obZi8kcJyFG5DlBYGqxDOCikO8YczoGnTwLr7ZB4PmVTmCTX39P6wkOsPC312jBaYsJzUwktIC39lzZ03726598HdLc9f2rLV/UVZ6ievInsj'
        b'nPt3QjhSvnE7pk8Dh6KDAxCfjaYpxHcPisEpJh8eCjdjrSVn4dq++JULb7MjwH54le9kpv8xspj1mQ6lmtrk5oJGxovqUqrZ7OR1/Q8KUqF9HOOBs9R1jYfs7/2MB/5k'
        b'9o8JUoJyBCuSfIi9G2lw26+nqUfb/hLsUFnRLepcOo6H29fRgq5myAzZSdnJqRZTisaszzZsRe/+hlvFMZZxuFYlbEf8uKZAgDspPipIGReHFWWkvLBUELgoQGztCmh9'
        b'DDDSfhMMJzsMup34HSY0XpM7tmkoYsN8vYjWPOAWJMpKkEEEG9cOjIkzMCbSvB1ZwaUKHPjIPBY+9tFQaKo/riiMI330LDg0B9TEEz0RVIUoopDOXxkTFxuF1DekeE4B'
        b'5UJQtnFMjwLt/BuzJdM0ys6/Eazcf8vBMayS/mgnY8twxrQAvcgsnHDqs6/V36tf1H6tTgQvJn7wgs/rbq/eAUvAEsW9F5e8cufFJffeu7sGvvnqqleWwDef28N4nkoJ'
        b'SAtO+yRGRGkapGGrP1PQhI/Dm+i3zYR0njhkLdnwwh3u3QS3sOA82O6qoHk+xPXmdr3ISZCUosnM7MbzmBFuiN+JEfqLi5gHBUNM6fpUc5LOaMw2qmZkZqPUplkqksnO'
        b'CjmNMc3UKczYgP93o7w+FixjxKRvHOmgQYxph7po0OPzfmhwEvoyEbYGIxEPK2OCkCKqDMybhQx5NNoXUcur4uOQ2gLakZ5VI1oaToHq2U7wCrzA6k/Uf88R3nh35rbv'
        b'1KvubAFXt7RV3ixR7Gk62Haw9aB/XXiZokws7ig7uquppKO8qaTVNwDulVFfrpBMY/+Mehpzb9goA+eRSYIUkkXgSC49F5wAxfbeFfTbu7262LlbF5KOlpCOlgzhaDdG'
        b'IjSOciR3GXjE3B2dhpPv7eo0z/6sf8ypwY6V8Ki910qDSccR/8dQcI0DLdJe3KOvRKErqG4S5fEouF+J0peCBTwFw83w7PweJIzJNw9c7k7BUyYu0x++B2kT9h65ygbb'
        b'hrL+GBnM8XtGlTWVjD80vswpYkLxh6+qtwnGvIDG8C/VEpc/XVUIzB4oVwa84Brgxw8iHsFtM4nbZxKotSkdccHKOF4KuQcLwSUW1MMS0GTGliTcCU4kEcVCpQwIiFKm'
        b'LVeB+njUrQ1BkeBMAK+qrEoSp8Kd68zYcAqByDjnVRlboo1xtmRD4E4ObMa4SvxTKXC/FykZtxvuAHWEdfHa0ZjRguGwHJb9lih0sRhS0jV6g06bpMtL6UbDknEcxgjy'
        b'i6Sjnz2bAklHlHIAlYU2jnYgGc5yvAvJZB/1g2S4CSp4fHYQ8SpEIB5UGw2KXWIRpiG+JKT8CwTxyGw40AMf7GiGtXo7AyZms4MBP67y0kdYcFR/yos4LhN7y+pDnMTa'
        b'RZRct+m1/EzVuYn7N/24qRql4q242pXgRJAyEttq7rCNogTwCA0uF4KtxDn2NvuT646Rq0cySz6hH/j8TxbDO7VyvWgGVZh3frbSfVbhGP7lmokeFO6YUFW5u3/sJEo/'
        b'Od+HMWWjNyu2vhyt0WpadC2679U5msrLp3Xfqk9qvlUbUgM9TmoSEVJf2uIe+LzY853TGubkZ6d0ZzWnNV6ib5m3pX7qaWUf0hHeUV4X/hA6+EP23t6lq4b5nG+lXz7f'
        b'OTFo5rvMa8HvCU+mSlM/yaQpaejw1zT1iH1hZcd9wZxom9cHVpuQ0gy2MNmj4aH+2cwjxQWXrjGlE0wbSzBNPF6MdGP8y2vKEpr5DyeQ2p64fzNFnMA4pgv/eAnQhX/9'
        b'Q0HzyQgm4sznuzDR461+MJEYvnXZ2KScCE4hrRkhwmBk9ytgxSM83nQvj/fv5HK4R5z6oJ40zoLZNmidnx8Hz8HtqPoQKkSzgCCKkysaDIqShy7yHiFfLOexJ3w2Q1A4'
        b'dOz1IXcz51JGrMb1d+mkk/SCf5zlTFXoocn4rPLV8TIQ6rbgrb2Xh4+rrA+clPYpp3Ab/Fq1X4Sn2qn4gEQyEt5StFe2592rf/DRuMgD45Pvul85s1C9peZG7oLrgzwH'
        b'Harc8xp4MXNn4MJ3ayOu7vv11n8y7n4Rd+aa3x8Mfzj3z9eeu3jq+qZ73y35Zeq76w5XvDjPL9PPb9Ds8stTNNbnf3lAjff3+6rtOYUzsfeSQuAJh5HpMdRhZhIbMy+G'
        b'N0TrC0ebghUKWB0TqIwkrnlQ74SkU+DTAnAbnjIRo2/SzKfgxThwxoy/J8Ea9N0FFrFhi+BRUhO47QrPdTckUpFNytuqI+C5QYQCAuB+WI8M/0pkT2Uj8hCCekYJrz9D'
        b'mLVwDNje04jF1sheqsuK1YI2M+YRBfDIjKAo7IuKAaUr4gSUM2hj4MEpsI0YNJMQz28JUkUGB8KrSQoVbEDaOkX5yLlnQDOoIOJGABrdeblQi6UdbIJtDju4fTQ8R6pB'
        b'3H/XPN5uAi1gJ7KdeLupPMqMsXx1ln9QnDIyWAHOTVQwlFTMisElhOjd+fhvGLjCHEtypp4XFQGEgJkFMtoN0RPzUMh4IlribKSLiVcokNBS9ItEyFhHOd79VuHroFec'
        b'EnbRq9utAexc0JAxLiggFlYjg18dKUTW/HkGFCnAGVJNirAbdWERLrZTlweLDRsr7UsVCitFVmElVcIUiqwi09gCkZVtpKzCJrpQvJIyOHGUmc4fSlP4dzVlcN6AFHir'
        b'GOezCnEJMygtjXMai6yCnCA9VSiwChqZJmoBtTZ2DVPoVCjB5VudShhjIamJQ3fLrMJGtomU0ciRtNJC50oWpXO2MqmsnrJKmul6mqbWLzL4kVxSBJ+00skqLKERxJJK'
        b'Mb4roUlOMckp7pUzxSo15lZK+Rx2WGnCU9aH4isp1xlBs62SrqRyKeM2BI1AyzTRtnbZ09BmYSqD0h2rdCbpjlUyuNReqYQoRXulgKRA/3um0LKNIi2nFZRSlai1JTTq'
        b'XRetsFFkdWkUa0VacROD31hdjG9onawuXlShS4WowhmpjqxWgnKJrSzOVShD7ZaV0FpxBmP8wirTOqNxkBncHG8549+0UlyXVdZEe+FvjNalUGZltiCjHUFJYyjRvUgr'
        b's6L03oghpzIonavBz0pbmQwWfRukdcX3tvdeWjcrf+feLb+/1p3PT75wKA2uzdXqqvWYgv+7oDQzrDJyddUOssqsLrg8/M0gsrriLzlzrS742cyPKW6DG2qDZwaHchmt'
        b'brht2sG5FHpK5J9QnjR0J7a/z9byT/g9aqW71gs9U1rvMsaXsroT+N1Q7T6VLriGdRKrmx0GK25nqZm2upbQm2mzM/8f6UK+ccvuizI1Zr1BOf4+EyzvIfcYm+wjngHs'
        b'l0pDJLRWUEhb6XXUVmY9km9OpbyEpjvFSUkGTZYuKUnBdDKq0E7a3NtpIJmRqTeZU7KzcmYxqBoTQ2i0YFhKui4lAxmBXXZiV8L7rDzbeJ8O/gbDdV+SnSo35+fo5P6m'
        b'PoAK7JQutwPqjCfMrVg4MyamEgFdQtuATusCDbHAQCIYc3+DARqxRi+0wzyCMmJhe99VI8/VZFp0cgRVgL9JQSTsfR+Tbr1FZ0jRyfVmXZbcX48/j/M3jbvvTl7gW8cr'
        b'jlwHdUtpz33fSZ5lMZnlyTr5fVed3pyuM6JWo85A1294Hfw+Pe4+7Xffyd/0tEqlWoveY431vnuwPC3bbO+naehPIe0U6A1aXV6nZAUGeCE2KdErVKupk0vJzsnv5DJ0'
        b'+cgYRzVna3WdTsn5Zp3GaNSgD+uy9YZOodGUk6k3d3JGXY7RqMAd5rQMVUBKUnh0OqVkG8zYpDB2sqikTg6jQqeQdI+pU4BhMXWKTZZk/k5APuAXerMmOVPXSes7WfSp'
        b'U2jiE9AZnWK9KclsyUEfObPJbOzkcvGVzTKloewYjE7Beku2WadwGdiYfswLUhzjHFgqtqPj+xiZ6rEMYbAbl6FlRKYxD7F7l5d4bjYVVkojnf6hhMVvvGyyEMnGv3EP'
        b'Pdw80Bs32gP9eQo9yDcvlB5LSDeaY4Tovwd6ktESRoodKIyYvJEx2H3sQyPZ+pBBZXsyXqhEVC5DLI9nwPlkbDzFwvq44Kg5IqS6JLHhsAp29Jh2wNJPaKeLz9AFSSvG'
        b'SjVSRAKlIWnFFnJW1uSyXmhGqiv+0yPpdoDFMs3KWNkZiH6MAUj+0YjHB1iRrPClGhnELVlfqgnJHCSHOCQBOCwtTBOsXBqNyuNQ2QFIZrFYkiAZEYuoEMsGgRaXJ9By'
        b'qAwWP6H/SBbictaH8RLGmKDlcpZpsWQWWEWkLqHtu4CvnZTDzKDIM2d75mZQ64VWTNmpCkEcIuRYPJxkTOPxJdZxh98pBMa5eKRZk87cyWq02k6hJUerMeuM8/FXcacI'
        b'I2GWJqdTrNWlaiyZZoS7+JVWn2I2xtgL7BTr8nJ0KWad1rgEv4vGmYWPQLdunlwc6KFNspcbQNuMI45xI9jmRtswgYw7xhcf2g19w7iEdCGshoGTZngkOhBehC14kjUS'
        b'VIWA1mCEFFV4CjMIXBHAXaAN7Otjc2AAsJ5MKuwzAU3hKehUZ7txY6UTbKZLb5vIoVxp0aUSDzZdhcT9OipHjBANZTQOQcjhgt7QWJSW0M5INSDCCqEFEoF0JVvpjO+r'
        b'sOeXQ4Dg6iUIHGmq2OFXdbIyGI0S+rGfMG7jbiVu2a8xEJwVaw1UwXJUMYvvicYUiLCeQZUh0EroDAqBhe6sCJBC1uBMwBMi/B6N79AbJJwM7laWvJtUiXUaRAlY06oU'
        b'Yry3aVsIcFTyyELWSspFaRdWChG+skiv4QxCfI/ekycrZ1yJ5Q+iI1KOlbOVMRXpmx5I3+TMglQmP4NGuiRNFXCoswRYPmvR80YBDixD1IEo00rjfLY5AoRq2IDoFOVq'
        b'jMSTyqYhdEac1ZixwTgHo1kkj5BdztOl+ELwN4Xgvw6xcvFjc8ou1JUmER6ZgyrOMkVjxA3F2ICRlpER5oYYJGJgPjRThJknMgYYDrEyZNXf9xCJsYf4oYwpCNWkpOhy'
        b'zKYuua/VpWQbNeaeLuOuqpCs1mAgcIsQkZO4JvJCj184/17uz3aKcAciWuaLTHY01MkB0DzcSvxVzGJhMAK1cQgj8S0YMnAb7OqFGheXge8lv0s0qR3giGyVzaZt7gI5'
        b'y43mZ+J3Iko/HR0TFwdLYLEyQCGknFUMbAbb1/Rxq0ps/02J6KKjEhGaJTKEBYjsHo1EdocT7+NA9OicKiDRkuISOpFzvOfZBaZWaaoTiaLE3wUVFEclCgkjFnW626If'
        b'F+kzdTHZGq3OOPCkOPHpMahYxI+6TaqwjzWpUvrYoYQT0D3YPAOUm8CZgIhYVWTsU9jCj58WFROpXAor4xMCMAslATxgM2xxWg2Pgb36YOn/8LPpRy998p36e/W36vTU'
        b'wC8VmgjN9+oX+UjC5O/Vrycn3vnj3R33Lm3ZauW20i3l4Yf8y0btKZ7oQo0HzomnhigEdgeyD2LatUocr7ae+DCap4Yw1BALB8oXwhPEM7ActG2CbdJ+ptNHuMN2M54D'
        b'AQ1quE8X0Hf+e5QEniFODHAyBrTBg5YgZUS3uW9poXkxRpproBWUwKuwFtRscIQ8kTitSHgZxzRFKkE1rj4EVsfABliLwABVsAHxcQol2OsCm1LBZdt8ziN4BjIP9Aa9'
        b'OSmJOBGwokptojZJjDKk6kjogiF9UEVlz+CYLzLpMlM7hZnk62/MFyGSy8H32fa6jQZ0WY9pBncJVUwVezT09S78FggDo+0sHm1ZRA1YkApThQ7U5X4f6vY/dymKI1F7'
        b'8Ao4NawrPA1uGQxLWEoGTrJuoCiPYDesBxcQctXYAmQdaZcgPLfFblxeuhEcpqg1ASK4A+6eZcHcW4OwfT+fKyAAVodEKMFtxFWqQeuygKhY2BCsilRGxSLJ6Oo0E+yC'
        b'14gbP2c03JGgXBExLRPWKqJiY1BiQk0xOAgzDOwSjlk8U7/x61TWhE1I1Rs3vlO/lNyia9GsurMHz6rtOVeqKGstn3ugaW9bVVtJ6yruxTRhW4bPtFWv+FT/qci6a4hw'
        b'/Hmrk0k0X2Sa+A6zS7arLPsftXelB76hvurwOBsahgiKRGi1gz1iWBNNoiC5EeBKIQ2O+MHDJERkGOyQEQ9bN/daBjzEPbMUXiI+RTUoXmMjR7AP1tlI0k6PsHyxGfuk'
        b'/MG1iCCVMkLJaEAlJQTNTCjc7GImU2ZVsDg2WhUVGxwJ6rD3EuyAu0hXCyj/xYLEtA32ib/HVw9dUow6pJImZWVrLZk6QjSeNqIRPotFKhawYmJFFIzsi7k9ctspFFME'
        b'IiMs6LrIZ+C5SERIhIaMDkJajy553QnJq7IfQnoUOH2oydmO7hF2auqujNI91NHHpat+p3kctpCDrmRxfMTtFngUbOtOWIiqYCO4jikLnoJthEZgTSZie79NWYisxiZg'
        b'wpLAaguOP5fB4owedEVoyjmsD1V5yn47LAPDi8SqLSxDQXfSqb09LOIZmZqsZK1mVoPdV8FRluUY8jqwTW8agMfDbdHgTEQsqHdEd8GdPebI2QkeJrB9qQc8Q4HTsNwd'
        b'nF4GiiYYSZxcNpNj89nXwppgmwSC22DDUnY83Arbe7QJ+2iw0UD09XkUmcXDar8ADToZbofazxLJz6FhZskwc2Ro2Y1cQrf7/sIpGKqbXdJtNs8yBd3nBwRE42lHFawa'
        b'MZ5E9EYEwWrYsBwJYqUC1sdELneMpYACjToJvLUS7idzLHdWiCgkttxCx/46qHbtcEQd5PXoyU4UoqPQ0NzNDAwfys/H/JUeQc1AfCZUZcgRxg7i49ZDOGSs2WondfNx'
        b'60jnsIXLIDzYOChrk5MPbKAs4zFWnoM3o6Kj8Qwp0lMCYNVKnrvCpqCnHHCi4V0D20TwnBps10sKz7KmTZjp1fnPrB0vAXM8F6Q9+PPYgFXRf3YL+WRS8I07fr+wXqPk'
        b'UW/7lLbOKBNZrmxtTS25O+Jvh0R75+vFn+cmf/my9722lUu+27X1h6zhRp/zxuIhriNmvvb1J6+Bn/5zZe+9t7wXn66faLhe2Vo4rGrfhXHHZgZenz92TdMvX1SMy1TN'
        b'/lfdcK+HSoWYMMbloAahUu+4QbhVxM/piMFpMh0zC1Q+49CHhib0YL/gfByJ0wOVk2FFkCMUGxVM9JEacNhbRI1KEHjks4SZSwzh3TkxrhQegIdsnBicFxPlKjcMNFjB'
        b'Qdt0e7xtnskFXmB94LWl/BxRUZosGglT23y8CqnUHkPhrY0s0oEOw2Yyz7RsATxhT4OD3xHVdDhPYWBdTgApw6IDN3oH25hkfKwNUrt6TL/8HkNMhuNpknKM2WbihyBS'
        b'Qm6TEtQmZhgxxGgvsRvtgaQFV4RnZYjpNakvi9bl6VJsDLrLmOlZPs94BLyV1GVWdsmSR4g3+zyuzJGVSBULuuzFDGuITapQxUO+7Gf6Zw36On0MPP67+RjczoJt4bBN'
        b'sBB2zAGX/UGrgvJbGAF3eq6Du8GhTAzjBZ0v93cPaqqH06fjfmLax78zP5gis/lfxO2lz4soeajvf4L+aHSOnMC/fmHo31x3uNIBP1IrPR/4DM0opvT3xh/kTDgKYojP'
        b'If+YaNnmUE/rO0xW63odmHtjWmvRhh+pq3n65N3z1tx9ftvfO/4q3ZK3JHrNa5ueW1Sw/U3J8+WfTg1cMW+4/w156tTBZza8Pvh956of/rHK6Tn/y+8lT2nMm6JUTfaf'
        b'uKm2fcONlF+f+/xV87HTpoP7Yz78YnJY5geqXNUrX6ftuHk4fd6dg80eh3+8J7o4xDXZ44ODlR/Vp66dFvVq84dJAS3Nc3696Dz7py+UO+MXKVx4fL8wnF/80sPayAbb'
        b'kcExFhzlDY4yBl4nuhQ4Cnb2mK7MnUsofiGSo9d72jY8JcNd4xAx3wSXzVgoToLHQS1PffaxBJVo2NA4EhESPIGarBWuhSVgB5m/hFfgASOvfSEtdQ+vfrnIiDU1GJ6D'
        b't3uPvIAaOolTZ4Ca+c5mHEO3aT7c2mXlDAKlT2rowENJPB86DLbl2lhaVfwif1tWEQKjmIWXQD04R7ROeDBkKh/+g+EifSl1Wc4GwFvgAgl0VYGbs/iVI5ETwW0lDp4/'
        b'xuSB82P50djHIaW2l2EH9sJbyLgTwUOk4SNgOzzVV/iCPd5I9j4NKkjPIfPvCiyHNTE0RcfArVORfYAejwwQQfG7fSg0H2PAB651YyWEJQU6WJLQya66SoibE3uHJAxi'
        b'UYzQm6M9GTfGiy4Y/pvMqYcyK7S962JBTk8GN2PcQPWwFXPRpawnM5Lf70fJ/W0gFSJ+kkSSZHuRlNQpTUpab9Fk8pNkxCYl+jSpsdMFr+HTmEwpOsRwbSav9L+Z02il'
        b'O51sZaLySNOy0CWbtlnfYsqNYUReNCMdSxP1BBxBqFnexVvBVljdk0QYahq4KURIeCi+j7PFPu9OxtruVNKxWs4e1pvKaRktW+qEnUjESSTgvfUOJ9ESjRl1pgF1ZFwK'
        b'16tkh7k9B11sxoHNb50qsmmMXKUIaYwCpDFyRGMUEC2R24jq6bofyOB2TB52DzUkaxBa4TVRL7sAnJSCMmRw18AmBcPHTNaDVlDRPRnSCmAVt9GHGrKAixgE9vJWRge8'
        b'3KOwoMAIIVKSt1BDTNxyuO9pPZBAzoT9tqpdF75Tr+ZjTyPaS9tK2ko69urpBFG0KEP00bwvE8uHlPt9I9vleXzCIrnLn3Tjp0x8L/S5iaOi3w/lJjZT49OcKeUWN/k3'
        b'cxUcYUdPPQvPBqlAdURPO5h7BlT58XyiCTbCAzyLpYSLhmAGOwK2ErY/Bx4cTsCOBlX8sjoPHa1hwWnQbmNmc58JtvEynpGBmsVMHmJgrXbDV/Rkio1TKsKEJGyp9rB8'
        b'qU2SWZ5SxDZY7FDmfigY2gd5VI6cPBEJO9mUTFOnONWSSUivk8tBaTuFZo0xTWd+ZEgZZ8TatLEIX4rxZbODU2xEl+s9OYXPc/1wit+CUcHEYUc+5hXGPHzJx613JmSb'
        b'pTOnZ2tJNcYCe/f0naR+1gFQIbp00DZrUUwxzAjagskRVqfBs12E7QT2iXsuyJwuF4ITyNg4ToyXf1j5YLI5THZwqmY01ce86kmNPeaPHNRIkWjMRy8u7EONGPa+IXG+'
        b'ccQggs3ggr8JqReXnNdbEHpVItnWlghqzLnwsnMuqHPNkeIwzJnwuACeB5dhk2U2znULCcnNKFdVTBysC4pbTkz3SPSvKl5pX0oOzsDKYBVoW4o9vxJwCFwC1yTwdhqs'
        b'f+Tid5ZErfyXUajUQFxITlqQBfYFgZYYBHgxYsf8QKLEy1hkAZ2IJdyFnoYXKaJGuoNzpJ1wZxBoDaCpIWArZwwHHfoV7n6MCc//fDFn8ODqNveiUOlzH48M2LM55fjp'
        b'T6rLr3vGbPnsQ/Dxjqvb4zwOr5WOmeVGVX++7X+8at7e5T3lrdf2nrn2Y+fUsg++Da0cXl+f8uCFDg/D0GyFgLjHQFE8vBKkihIoyKo+ITjNTFwymHyCpZvArSCMcmsR'
        b'pXFTaHAW3JhB7DBwy9MT7IEHiYMEVisjCF9yBcXsuuVgO+/bq7QCpL9gMx3Wjg1nKS6cBm1j1STsbQZSx445lguJwSk3eJbJRzrPzkcu2nLW5OToEBlidkCYjJeDyUhT'
        b'OOJYE5P1W9yvBYGIVSRl6lN0BpMuKdWYnZWUqu9uJnUryl4vYRa/4aSm+RSEcPH6rk97chK3Q/0YQHjyGlzylkTHK7F2asdnUBdPvBjoP0ZsGl7ra/jY+gjxb76LteCQ'
        b'W5ZHKgmBjYoYHoQ7d+JkhlpECeAhGlwKhzd4zLuYhWjsImzbkAsvrZeKc9ZL13MULBd4TWfTgsBWsuYXtoKrXiZ4CbY5ueS6SGRieAGWrN2A6XS9gBrjwRVGghv86tUw'
        b'UTSOdWzAq4Hnq8TgPAPKR4ILFjz9A6/kDAen4HZUYVVMYFQwOAl3bAgOwD6PGPsqpgSxSglvCshKf5oCzeCi8/wNBRa8plo1Du5yZIYtwwbMb8+8K1MCy5bBVsIkwyFC'
        b'SlCTsx40bEB69RXEZcygQWJF5Z2HVyyoGQkcKIanwWXSL+CI1kRg3Y3t/6ph2GiqiRFRrnAruxSc87dglg4P4MmXPoWCxhEbYJtUIqTGRHLYeFhElGcLJv1AJbKMLiJ8'
        b'BI2K6dR0sA/UkpWmoJXDrYtXRsJbFrgLnIuIFFHSmQw8lLyS7I8x1BmccVZi5wgNN0ev5BvdjduBy4SzrYXFInAjw8eCgyP9kT1Wn4DqBi2gaAw1hhlEBEDjNCfKTW0W'
        b'Ump1zNsea3iXVssCVJ/PdrxpQ/CHk4ba3V+vypCwCC1EZaiDXX19+bT7ZwopaegukrYwaiJlwfuYwPJMsA9bhkHYoVUV81QfEGGD0gZlNigSF8KbE/TLXlvJkelO2b9u'
        b'xi6ZHseO97S+8cxfxs2eVRyxLCyHChwyxM9AeRxpfNYvICLozOi5KVOCl8bccz9/fQ0VdfYO/bX7C5/kbz/t98p3ew/mj25w3nMn6KpZMsKJTQxtbNjjHOKy4ONPxnz2'
        b'YVP0DT+N+jlp0zKZdd2QGd6mPSc2bBvjH9KxcHfsxKWu8xpczr79TtGk6U8fUubnd+aZ/vn+C89M2vdj+OCMEMuQN9ZP/8P/RFS9/vG2c+/Octn8oyBLcKPoox0fNRa3'
        b'rPRPy1ocRgcNO19w68PYTeuvyH44fT188FcfF6wY8s11OtPowjmdS/yp8KdBe27Obgs5O/TjsX+96ZZQscL3i19n3D3xQD2jce3rD097Lfoxo3XPM8qpbNB3ze6T3t5y'
        b'fdPQuc+KPqmh3A/+9WePFfcfjP769nvO96eMfeunQz/874fxE4vDqoevsz7/2YORhgDLDOGvClfir4J7dL7ReF+TmmDMMFjK2QpvwAssMyOdLFoCF8EBuJUseFkJa/Ca'
        b'F1jGs3dYzIE9q1KCeO5BeLgTaCCqJbgNtoEt0TGBKv6jM1L/NmcysBlWz+drRVoioni8vwMeZgE1P1mMSi+cBY8QJu6SMDEoHgOE9RER5TwdGai3GHjFupEXAHuWw3MO'
        b'Hr/Jmw9s3uNDBAgCfxcoCYKVkcGICxVHEjEioFxnsKkSeJhor3AfvG6JxtO9CSh1bbRCGYd0Hu8Ybg5sFBHtFV4dJ7RFetOgAzTbYr0vjSP1TwXFRpMzAQ7WiChOidfV'
        b'HoYdRG2OBPvR/Wl4NSgqFpnY3CgaHITXIwhsJteNfKmgIxuzH8SAohFye4N2LmLpKlI21rv2BamIzAyDFbzYhLdjCODD3eA57GxBLbzSU2mPAWcf6Wt7HI27h9k+uF8h'
        b'R0Qj9rwxNC8cuVU4Ck5KBCQy4hmJxI3xQGY8umPcWDfah7GHf0jJAmgJPeyhlESzMXz83M9SZzeGE0nvkyi4h5xA+sBYZpfNrUw3oflkRgMp5P1eCnlLP2IUT+VEu4Gb'
        b'A4vRlc/aMPUZsxjshGfAeQXLb+pwaD3cAWuiZ+F4KzLXSCO7uV1JgjDA3hEGWBMHzsTMNfL+YGdwmYHHQPMEsiQYbFfOC0LIFygE5Z5oqBuZiaAhPYXtpQF627VANbr0'
        b'2RmEcuwNQvfaHYSp8Er1dkyfCB5r+iRdwX56ElUqkXf7WapL05vMOqNJbk7X9d7BSiXpkTbSLNeb5EbdeoveqNPKzdly7DJGGdFbvEsRXqQsz8bRsMm61GyjTq4x5MtN'
        b'lmTeK9KjqBSNAUe76rNyso1mnVYlX6lHBpDFLCdhtnqt3IabBCp72eiDOR+B0KMko85kNuqxx7oXtCvTdQYCoN6Q1gvGDfbKjGmWLJ3BbAom9djq7FGK3oBakqWxZUOt'
        b'RVAbdRqtHBMNyaUz5OqN2QZcDoLdqMcxrj1BXBQZt2zh/IikmMj5C+MSFibFzY1dGNznbfTC1fPjFyxEnab9zdzLExYuTcCxwZpMNG4GBFquLjOfh0fj6DdMzr36KVVn'
        b'xMHGWnlyfp9Cl8xdFkHKJBnlmlyNPhM3pEcRGjMaXRIBTUYlOzMzewPuXKwZ4w4yyQMCDboNcpMe40DuFFV4oGJaz0FZbtDn9XqllI9ZtWBx0vz4uEWRi5Mi4mMXhuTk'
        b'23bKCrE1R2XOM/fKtDFElZJtSNWnPVbq7lUsiFya8FiZQnTmlJA87UA19Egdq0mJT+jTso0hMfpko8aYHzI3Jwfl5fEowZKD0f7xYHjyAnpSgd6gzd5g6gOZf0z8/Lkx'
        b'c5csWTB32Vz/xwLFf25MDEG+JUvjF0XGLBwoV49s00g0nxx7Y6bJ8V55+M6OQrZciM/0kyVDl4/j0/lctodeGbXyXMS5UI/0W4DFhD7y2R3pF86LnJ9Avsj1WoSvy3T6'
        b'TIMuPUtnVEYuMCl6loN/EM+zh+Zr5JjTIHwndIJXLWBw7GWp5HHZiKPwo9SbcvCPPrUbeSJulKzBAKHRRBzSlGLU55j7NKSP61JG9RPTEE5MN9AOdiaE8HEG8ND6SOXS'
        b'lRHIIEyIiBIsDQ8HrQoJ7MgPBzvn+IUPpuAW2CL1RSZOZR+J5GavYmlPiUTZZBLtkElMhWuq2xNO4fdxhWCJPqRPq5RxKB2R9n0DkfuGY9l8xI5wrN+9KSGuqu/qYIFt'
        b'bwysPenf3ruIMWFX/mFpyndqZWqkRpr6tfobdVbq99SFudpp8yemDKF+TfCdvzVdNDrixvZJDR0lk4ZHbAi1hBYt2Oe71if5Xsbd++t8xvjeKdi7zzfat8bs63tn7OZ7'
        b'3qHB3MVMH8kX01Z5h6q0au3XauFet1fvfMhQpX7DD/yjUMHwew3sGgaOhC0PUgYQ5y3YxygNat4rcwpUT0nMJ/scIe3UQiNltGTOk0cjCZI2GDU5RBfEmi2vCSJdMJ6j'
        b'fZAWJ2TcaE+kZnmQlQ8FCqNNg+gWxmvnBl1vcIm2zVf4APrHnkdupfkMROurRJcYBJlpmEPro4q9LvSj982kcKhEkyTIHnmDt4KIhBd67QbRpREu9FCERAVT1CLQ4qrP'
        b'B5sfEb3KEl/ok28J0iesXUD15wsUxVkW4iEtzgF7JoaGTZg8ftJEcAWcN5uNuestJuKouLQSlKMGtcM2eBledBVLJTInF2fQACpBLUOBZnjFCZ6ZB84RM/2D8dFhNB1A'
        b'I2M/aup6I2+7O62KQNDJaWT8R+318reh+Gf7aIZYAcmfzx78QpN7Uagbd+f6G/uXUeLy1K8pZ9VE94A3HwaO1Y056PHu62OnTTgwaVlr8IVZf/08MX79X5dotjW/GPrv'
        b'uJxJsZ++t2Hoy/8+7CJ8R3DwuUHbJw+Z7vrcv+lTpzxHLQhC2EyWsp4Be2FHdLAVnu7y6zH5YKsH+QwPLim0uwOxMxAZbOdp0GaCB38rlO3R4anGbHNSMnaB2cPb7Di+'
        b'lkN47UkwG6/3KQh+LOy2FWefrXSsEPntwFWSogu3a9AlsTduezT3g9t45QqyVPal9kDu38JsWB0CquInTGapXFDjNmOmCh4BdQQFDBNZjN3iIoE685QwlXdMeU7Ihdvx'
        b'rkJHKEpFqWATqCGJXxMIcViU+rpCHbN5lZpHounzORyEtWpnhDpm77ineSQiX5qlYixO3D5OV8dcWR1v2y7UGkXtQBW+PFIt2egk5l9SZndKTlHyvxWqg+8FRFNk9a8g'
        b'GN5KQLbXjuWTQmE1RwmX0lIVOD04gPc7BQylwpCFfH2Ees2LLqF8OSMiz9NFSEj8OF3qNGP1giji8oRn8xYnAFROhPdyvDUcq6ZnwdINJEhsNDgvIn50m28KnAmAlcFR'
        b'yhUrwC1YiR0JJPgKNgRhcxxUBUkU4BLqDTzSyT5CatiaVpqaQ0k/XPUG4sZkF4n7rmPF4tVU6HH/Dvc30pVTcpa8Plm2PIAhXjgxKNPAi8iOnENRsVSsGJwkcMdlTaPM'
        b'FJVXM0w94ef54/nGjJozG+8GFjAnPDNyik/YYvLyvGo2ZaWoOSfGqz3+12sjn3L2YiWtZii3O+Gvrho3t3IGefmc4j36EktF3Jny6uy/b/zHKvJyUsoiegdDzbkzqdZY'
        b'lPFQSl5GGj3pUIR5d2bFrGx96tUQ8vLFBWbqR/R/zvRan5Qw2Xjysjx7Od3CUOLNbpqgpihPvvZPF26lA1gq9M7EWqfVI7i15OW/J6yirqKxnzPz+/kjzWfDyEupZDSN'
        b'2PfUO7Nqx3qOXiciLz9zHUktwM2clTnqpWXhGvLyefcYuhG3aFLM4tKpm6eTl4fCvOhghoqYFKge3jg3nK/9ffmbdCNLiVXpmpCaLNsOG1nr71GVNJXjH6+OfNddy78M'
        b'CS2kfkFDMHu5OnfV2Fn8y61+f6Su0lRATpLad5wij3/pnCOlEFsIXbxGHZO91OboTGHXU0VIQ8gZv27Qz3M/mKp3+3iUwLQPvakOeH35ksj6d+e4vXr6tdwQQ/m9uv26'
        b'D3bns4ufmTPSTWRoEr60NPrSVreWb7V3JnmHxZ8Pz1nwN9HHd4de/ZG6UFtaGvX6i5WSNF1qcOeMxH+9PFmU3Xri43+snv0X7/8Yv2psnP3lqNbjST+ESU/nPPgRJgRP'
        b'm6VMple+ox91w/MZSeLcoVlvi+ZNjstU/2m0aOeFrZu9lo0en//gux2rYsaf08cejPp2EMh0+2rZ3bx/Rh4smdWaOGyVOepb/7UzVj04kXFua3bAveodP6qP/DLkndzP'
        b'vizvVE1Yc9Sj/fCnmz8+3Oj5cN38q+fjNp0NnNd2/ODJ5qRs2VdPjR7lktp897OIsW3PPPtRC7yyx1XmvXjX6u//Dn7+plz2Veu6AwtH/09k/NXSVw7KVOvWzC2bdPbI'
        b'88L3c4ZPyRn0wtWyj66WXJ/w0sxzOUmTf51zLe9rlxE3T6b8a+fht7wle6f8EB+x+A39Ju3XWf984J0wbemGD9e/yI10vuZ96asNnl9N/eYXxU3zqIbOtJf++uWVDbMy'
        b'/u575aLi6Ka94Z9D5tKxKoVmZ+baf1545+mogr/ed434tPrdbW8pxMTnB7YZBxPv3A4kK6uCbfs7JMBmojeNBG2gOAhWhlAU46MHTfQSsA8W8c7CM6AxMChKGa0MjBNQ'
        b'UiEDzsbDm2awj/d1XgatiNE65FMaOEfmq4bBC/yCjFvwMMCcIx4csEaC0xzeF9RvVjhx+C2Fp2EzAqoD3FBEBdk29XWFRWw2OJtCih8LTkX38JViR2lNGLwyIZvfkbrU'
        b'NcwWcAhug/NdO3zhkMPpsP5Jw2Pc/psQlEeKXJvUJCI3vZvIlUbjiCA3GSOxbyohs+0Ug9dd+aBfD3oYkoDDGI7sOSbBS2lpD9YLiWkJzTxgGPEDjuVIwCN2QzIPpKwE'
        b'5eWIO5J7WDBkYBHOa6QCskyuU2SzMTsFxHDsJrv/+0XHSOvFi4v59XgNDpFfiy6Le4v8wCv9iHw8+wzLQUU0L/LXez9K6AsoUAGQAnhj/Ah+Nr0lT9h7Mt0+k47nqi5Z'
        b'BNRMJB1hEWiBzQJQQTZVg2VpsHbgbOhihqXBsH3DegH11DohrICHwCGLCuP+ZVBj6Z0TtkQ5Zu/x5KGQWrBeuDwGniIzaEgTLAONJHTBMWsUB3b6gTMxvIc1BFwSwNPO'
        b'eWR1TMBUlMYxzQ9OINUQB+S7wTJ2RF4iL0RSsW6zJ0pAqWNWMuk8Gx8fidWVO1bhHHVm6pRRtj111uB471UuArk6c2rseEp/bKqRMd3FiklV2aT6cBmYI134Q8yul0o1'
        b'rpXbtm1zzqGjEpvDRpe2HOGmNaq3fN8h+KPnxcFJP/1a0P7q8ciGT9783CV/jruiWnGs1hjYMv8f78/89p3K58M+XO0dbnl/RMid9kOmn4saXrwXL91lufnLer/THad3'
        b'z44ri27/ofpy844xI9oDP2icn78rOrh95d01xbHXU3M+/Gr76/PDX5s/WXW4+AXFDPd7hsT3Xvvmowkr2r5P2fmiy+mlquYp2U8HbO/4ZWrnXeGDl34OSWVnVn18W+FE'
        b'QhlHgdZ1zkGgue9O92Sbe9iC2BrGwrTF8FjPWSN4gZX6MaAKXjJj3dAbNq6JhrcV9o3SAuAuPgbyNBrf810zJ2hESvDsCawBmwkE+brQ7giKQ7ZjaGoI3AJ2g0NcNrJa'
        b'OvidYDvSYGu3lFLQGIdYo0cgC1rABQ1hnoVxsAQniVujc2CHDJxlF8BL8Ajhva4zraAmRKkTxClhdYxCSLkOY5PAVT0BZTEsEoCaeJuy59gzcyhC/atgKweOJrjZzWbv'
        b'/9eZ4pPxTTvzInxzQje+yS0S0wwzlnZbhJeJSxkS7s1vOcDgSEu8r5sMc8xfjVsdZeLNTBWe/5+0YYuDy+HqfXtzualf9MPliEV4MkbbZdcchScYynUymwpr5/YbQoN/'
        b'TFK6Kw5RSyeyWiaR07KJAi2XKER/IvQnTqMSndB/yQ52B6cV1NFkTzkcxcRphVoRWdDqrJNqxVqnUkor0TrXMYku6FlKnl3Isww9y8izK3l2Rc9u5NmdPLuhEsnUDSrT'
        b'QzuoVJzo7qiNdtTmqR1MavNA38T4V+tVh7cXxVvzemt9yLdB/Xzz1Q4h3zxtz0O1w1ANg21Pw7Uj0JOXlsPbtChGdspieBEXqzFo0nTGT0VMr4kf7BbtmUZOItF6JHpU'
        b'Dr0J+z/JVJA236DJ0uP5lny5RqvFTlKjLis7V9fN59qzcJQJJXLMo9gdqg5fLcmhki/J1GlMOrkh24xngzRmkthiwges9HCvmnASuc6Ana9kjsO2n4PKNm+lSTHrczVm'
        b'XHBOtoFMY+lwjYbM/J5e1+UmfjpMgyeIuvmOyRzSBk0+eZurM+pT9egtbqQZT8CgMnWalPQBJqdsvWCrVUU602zUGEx4VkYr12rMGgxkpj5Lb+Y7FDVz4JmodH1Keu/J'
        b'OItBjwpHkOi1OoNZn5pv6ymk+fQo6P7wdLM5xzQtJESTo1ety8426E0qrS7E5su/P9b+ORUNZrImJaNvGlVKmj4O7wOUgzBmQ7ZRO7C3jGz3yxAfLV7tLXjC1d7pCvZ+'
        b'WV+vvEFv1msy9QU6NK59kNJgMmsMKb1nL/GPbWbADjU/OYAe9GkG1Idzl0Q6PvWdCXiMTbCFcUT3scTY1+TiVYDw2Bj7QsA+ywDhRdBMdveQwvb13TWfgIhglQo2hIDN'
        b'YEcUTU0Gu4XPwrNgt4Imyo8ZSdUj0ShhvBIvMKuLj4inKQ9wgIXFsEyjpzPfZU3Ys3QmbDNehRuQ/J16wnMvJQd/+a06QpNJ1q+rvAI0URrmoq936IbQEO2aOxe2NG3v'
        b'KFHUXC7pKBlfoyzr2N1a4n9opm1N+7N73Qv9NiB7CsvPdaA2CdREwa19xTkR5cfgMX4JyZZMJyKmewhpcAucXLAulV8NBm8bnOE1eB61W+HQSQaDCk6MmniBXw9SBfb7'
        b'B8H6iDCOYuF1Gt7QGhLBYd5/uA1US2wdQVPiUbASbGFAMQOukaxKeB0iDSRaCS7DCyJytkJ0FjxBvkWAFpaUOmESS4mSQwtouC8FVvHF7mHALqKDVMaCK4NihBRSPGnY'
        b'sWiCfVnUY4Qo4Kj/XsGGxOCZRzZORqLZiy7w7om7PdfBt/ILH4y7KOqR+2G2MnyyngvhrzJ2J36x/dfzXj9hywOBMfAiVaw1W6l19mWqCrwCwT6d10rzYPRcsGrEx3S9'
        b'wNj2MBdSfSq1r2e97zvgPCGqhtVmpzwJWOIkm11n3D8ATC8jeIwH0M19z25zhfYpx9/Yxr1bZaX2yjC71WtNA1b2mqOyYFyZXb3rZ2oyJVOP2LjShLi54vGASOeBcE7S'
        b'5eXojURSDAjHmw44RmM4unJgUdS743tWb2fvZHtewt5t+6NXCLqx9985HdJjd7fujJVEh21zAs1gP9icAOs4bGNSoAGUwhb+TJdixCAPgVMCcAxBW0gVgr3gKr9hylXs'
        b'7p4FGmBNJFH2JyITENQwUT5j9AEfDOJMT1N42uvV4TUvuRSFSrkNB3Oa6SFHy8TN735y45NPJxyIG5//Q/qllJeaP/10zM3XZGXvhL54uPntCyeKU/YFHprUAlv+2rCz'
        b'/Zdpb7b+XVl98/jd1e+88ve5uw8E/EXkNtFXvufvCgnZyhnc0sDT3Qwb1JCKHnwTFuUSr9Maj/XIJjqGvc+R/JwIvI4MsMUjea/TbngcXgK1sLh7LDSTDzrG8j6rS/AA'
        b'OMwbefD6JgHFxdHgPAVOELvIDV4U2j1WsENhi7A2TSdFbwDb3Gxcz8bywFHYDDvgtnl8dF412KGOhvUhoGUkaOcobjINbsCjK0i9Iag9jWAPKO+5/4iM5mdyDlkwDwYn'
        b'ox3nS5FthiMm8LHhV9JAMzntJYJn5hMnY4F2ioXlsHR5j7Wzj7WfujhJZ0gx5ueYCQMmhkcXA14pIduw8b4kMonZh//Zcndff/Z42xLb9q/vYsPH0OWdftjwycdhwzYw'
        b'/s+0q9J+tav56RpDmo6PCLPrQ3aO0EvXQirT46pZODLoMbWr/tf1c3G2A97AYXgDNES7wpvdNCCH/oNwUC88UsyZMlHSLxq1g18d5QFCPRe+9fNPs8MGr12w+05i4J6T'
        b'+6R+R4QjjhTrl782n3o6IrczNO3szeTi0z9l/TRvtdPgndO5/PaS25qvnv9+6C35nyN+/DI0uW7KjBe8q253HNsS8kPOGTfT7l+cfvIfG/P1yHG/lHvNqniocCIT9FPG'
        b'ki31sbbyLCzDCovB048PTq2FNc+Cmni8LQA4Cdt9gwNoSgbrWB28LSVkEAdao2DNbFjSRQh2MnACp814adRT057Fjg1YTVMpS7gQGlwMjjKTjfIvupEF6hH4RChQF8Jr'
        b'kHAfKMJHOYXCRmE4OIEUM6yNTNCArVgtEk0FRbxWhHS5vYRQR+fB610KFdgigDuRQgX2wXKejs+AKritS28qEEYgvQkcQp9JWOSuxFBQAypAdXcuAjtGgKYnJ2LXFIKI'
        b'SXas6UeZkqTLSHjqsIdDmIIRvcinV3a+5D0D0q5xr4NoT6DLx/0Q7eF+iPYRtSrYTmF6tsms13Y6IbIwG7B+0Cnk9YSBFz8SwuYcCx8FjoWPgsdd+Pgp3sasD53N1Wqx'
        b'yYSJsZvCwZubDnE/IEXzDeHpOQLdRy6w84VkjSGjL1U7GIGt3XzOJfwjyhwQbTEgY1UZuaCf0KtuYVz2nNg0x9l6hG0p+oPXqDNbjAbTNLl6mdGiU+PoK35fGm2wXL1I'
        b'k2ni32kycTBnPtJ/sBpmMP8uxsTG6f8VcIMz4SU70bKfv1M/c+fNux/cfffuhS0du5pKmkrCa9r2th2+squtfHxNa3lTw6gDxVWjyooF4v17fX03+0p9q3Uv+/r6zgn1'
        b'qEwoSj6gpzYWxLzmspzLV7CEcRjg5rl2vlEPqsBJB+MA17KIMaODVTmgJgEc4TkD4QtLwXZirU30SImGx+fGRIKq+FhYHYPKCCFh8QpQKwBnYC04/+S0KdNotUm6ZH2K'
        b'iai8hDQ9epCmLB9PyIx5WDC8F4H0zMlbOkJeYrbgSyu+nOwpbLuf0MR1S5btSEvo9jS6fNcP3W7rb1H3b4L1f0aZaYgyF/dHmUuJtwwRp4HHRhxp2I1Eu/nJ/v9HpDhb'
        b'ZEK8nPdwmXmHGLFCUvUGTaZcq8vU9Q2PfHzyrFz1Fk3I82LT9f+KPCv/yRMoJs+iQYg8sWrpBo+DrTx9jmdV3agzA14jerME7sGaP6ZN9HvDRp9RE4jcngLb84KiYB2s'
        b'C4nGyxHgxR5EOhvUizzgbdmTk6g773/tTaVd66ttdOpko9Neup2qT3a+7DO96NF41kF++AyO+/2QX0k/5PfI2v4PTh7C6m5yP4RHsJBQiMGSlYyIDSFeN691ly84xWI0'
        b'IimRmd/NcP+9OPnnoxaGbIKWeLX6O/WaO+e3NBFsHN8HG3cs6Y2P/q90ExdK6kPW+eUHvyBsJKukjk1d2qVkXu4uLErhLX6BV4fbxHkiuxpJkJGGdWY8CbsmAV7BFh62'
        b'T3uIi0BwG5YKETp2iOTwGDjT6yTDfhEwJdtiMHcbUlO/CCh2HwAB+2S3R5BmDygceH8HQcYL6OLE2jdJKu76lf3tMdCxT93/Nwdh3TcMiI5dIeaPjYq29Rd6gzx3sios'
        b'sB92/Xioub3tWZag5noX6W+jZi/EvOLeEzV9qQ++cj7r/JONUcKjYKubDTeD47ph5mBwlXf1tkhjbWgJypfzmDkVHiXHsCj8XHCkXrAK42UMPlDWgZpCaiqoEIKLQxMe'
        b'AyvdcLc+Gil9bUg5shdi9M7Nl3xxYDy8jC7u/eLhd/3tp/iI6hTevTeQECUlabNTkpI6uSSLMbPTBV+T7FM3nc6OVX56rXEfznQYX5rw5ShlcxN3inOM2Tk6ozm/U2z3'
        b'tZKAlU6RzZ/ZKenmU8QuDWIiEX2LcH1CbaSpvMvkd+x+3M1BuQ1djjK2PSLFFMdwzhzd9StmPGnGRUgzuNPY/v97cGJnT1oqdaOlMjdaJvMQW7Au7D4MieKLsCrfhZ+2'
        b'gJdjkbmMjF2GCgDFgk3wilufeR5M+HMom37bc5qZnJ3Jdg6yrZuzjR05KOG+fGEe3sAZu1RT8KI4o4FfiObQ4OKQGdpzLI3tjn7o5bK9hS6+rGO7D9QjNNlwMgScg0e6'
        b'tvuA53nfIjgRGhRnn02JkohAQ84myyIK+9nCQeWAAeUDRZOPhVsdAeVwH7zRhxf2t6kn1fOQ86495n/v6gxcUV/XsDROwZIYnhXLJBSeSsuJn5rpkzHZk8To/iIWrlBT'
        b'Uyk+RvfYyNeoTLKdv98MwTc+HWkPFw5VdGQsSTo5siXj2qrNAfvinp8atrou+GD8menHpq0d/k7gkeT/BN+P3eTy5VCXwhvLzweUzp8U9VVc/txPRwiHSIb9cdW8xM9n'
        b'XR97YOnsZVXDdwTeGPn0vJDIpXnvu7Zl/xAmWXFe5Le8Wa2bGpXxqtMPkTODXLzTVxkFRX5fLsiVfGvKzQnw/nDhSWdfl2ubHiIro3HmWhmJfI5ZMQfWRA6F9T281aB6'
        b'Ch9BPZLs2bLKlVXH5CXagltPPz0InymXU+GqXjPYkMO//MdibyqYovLy/NTDiif4UZaJ6GUyrM2CNbFKFT6+vgBU27eahA3RIrgVtObDqoVgp8CfAqVjnWAT2AtKSWF+'
        b'WeQwsoCQGLX061VRfA2vuJCNMvPWyNUxwiRvftt0UfCkFGpLAqYcOiFNn/jwLmfCKzfWLHnPv65NBuXSBW/sKV1icW2Jfth6+5OmpVdaRgfr1j9kHoQtWm0t2PDewSVl'
        b'qpcLMv58NWhD5dC/p/1DAHw/G5m+LPJKysovFpVpI3/55fN/+a8e+p9XO7ZxTk5/aA06+9Yfjjw9Zd+DxuEvTz+9+8sr+mXtZVs0G15Jz3xmz+q0p6ugb8pPzn8tZHaV'
        b'jk1/bo2CIw7rWHhycDSsSwCl3R3SS20HL2bALR7OXdFSsAxu6RkxVQE3E6E2AxzyDVJGITP61tJo3I0CyhleYxBFla4j2tbUqMVBsDpQqfKBR2iyFDgcHJP1XRHwe/dj'
        b'677PidGk6eH5xi3pLta4IAnxemO/txsjJ6wU3xvv2AtqZTs5HI3QTb/6vYC10kbg4GC4gjH9iUH5BwMcTgoP4+XYQYFxoDZeQvP6LNYYhoKDHDgF6kBZHz7k2ExoQb98'
        b'KNXpv925p//pKYmdB30h5XmQ2+Tguc3jbi8lPCiVElIIUeTU2L+4fOiT6iTjedBXmTOflAeFHJsypCA/SPOUWJTh+cbwvzFwpjTMc+rV8WVhLxTmxk713xQwaHrA8rzZ'
        b'7VySx7GccyOTkz7SX3oiHvT103oJacoSGgdPtviJKHVw0CDbgqHaBHxy5SdzZJR6xow8A2XESjD58oMZc4eI5dQcdfCnYcv5l3uH4/Ui8oVOcrX00NjZ/EGaDOIo3Wfi'
        b'wJFcwt6cVXof0d94t73z3gDlK9ddYKiUe/No3E8nYsdpB2d/OviDDlPWSmPRK14vHT9OTRmT95evc+e57S9sfftnOn7w61Mm/znkjaAdIw4/9+ZSd1NLem1mXqbnzO8H'
        b'3X4truZ4+P3Buxaujv7V78Ennzd9f/vnjuRbhsC7w9M2f6qg+VCByeBwNJahmBPkTxCvZXSgDZ7soVA+WUB1b7rU6n6DLmeK8fE/hB4xZUr56GXa+JyjoLu/AwLoID9c'
        b'zuT+yG/Y8/2QH+Zryc4invaemhkZayc9NQeaYKlXnyWc+I9s9ByBSLJSwB/MYqUbKUxwTUwhQ+5ZLYfuWTONvy+g1m5ewxRyhfjwFkElZWbIMXSTCkRWQSOrFTTRhYKV'
        b'lCEDH5mSH8Yf0Ue+4MP7BKspwzMbELEat5HcOOdyK2uch1IImvhj+oTk4CMXVIewUFRJW0X4aBetqA6ltwpn4MP3ZpK8ApTXhPKq8TFDCG4Bgk9A4MN5xX3yilFerWEk'
        b'ySskB+w9fr6iSiGfFj1TVnyUkSd/jA059K7JSmmdfBFHsR0OL4lDvFiny1lkxPtnL7svsJhTlVON2GuE8PIeHlf8wYj3BCLHlClExlSMb046gyVLZ8THHOFlhJ1CfFCJ'
        b'VtcpXW7Q4xuiofJ55/Jo1bXDb1ex5AgZskANbytuxGHknfS6J93eT4rPFzNN4NdOR7C2reTELL+riMx21hb6/5AjZ2/hlXee+IQtpvs9f8efjYTjZ8jGTCZwEFQ/Mz0a'
        b'IWekcnIg3lqFrJSQj+CQGrt5eZ+oCcdZC9grZ0UcXEsnUPh8RDIETIlNoY8jnWkMtzcE779uGuiAZdK8JHN2Uma2IU1v19HxkgQZze+Y1f4sOMnDiOxVWDULHuF3lMUa'
        b'FzUWlAnyh/n0OeLOEV0WRkDV0hm0UYgtDi1rxQcT0lqukcJH3iHABV5UE22lvSks2PAbgj1CWzMwj77P+OeRhXnfMHx7BAWp+sxMBdNJGzrp9IHahpuEm0bamIPbJiFj'
        b'x59sJubbB7aDq/7YNEftAQ2ogXjXq5R40mAhNXaEIB+eFz1iGTfd7zLux3Oj9LuM21F8tyW1XSsTO2evpz6h0gWuOWohlZrLv/yT9DmEC1tcJHPUisbg0fzLf2diBVed'
        b'xSAFd+/MaZTefPAkR87Aiq7K/U69FvtGtl8WBJW0llze+1bZqBXtu5rKm0qaatsiLpVY6BSX+ZLP5x2Pe29e/ZByQYyzb/XyUUeGBw9/dZL0tVpFjMccjyNMwPPiCf5l'
        b'q6UB7UXhZbpRKaFsmjOlyvFN/flzpKkSf10rPD80SBkwdqFjzXcBOEWU2EUquDMoChyfTU6ddRw5uyGG6KYeI+BRHMnfAg7GIcsQNgTTKMEpBp4NzCeeabH1KXAqCg3e'
        b'mRU48BCppxsZP3A688lXjbtnZWvDp/AnOCVp9Wn6/kIvqE3iTVIS+8YfGOVFG991FFP1OBVW2yskGfP7k2he/bibya632bAIaeU1sC4etIWBhnhwHmn15Fw9fFq7rXum'
        b'ghPCjaBx48C8A+vEPMfA4q2JJrFmTFynQGNK0euR0vsiZRO9rXTvXhKl6/Iy9an5JawtDk7G8lvP7n4Gmd81ZGfKSXAbAgac4pAdUcbAa6Hg9sDAYL6Njy0jElCCj/vD'
        b'IBXaALSBZvwDD8wCO2C/tVeik8VgA7ISA0mOXWNxtAwfe1EHapYHwTobrDZABxmdl7HwIDgBy56o39LswBnfs4NmfL8XOMmTw/iTKhtQScYP0TuinsAmf7g1esLESEc8'
        b'ketMeGYUO306OPlfdFcXRJ2P1VkIuv+nvS8Bj6LKFq6t13Q6K1kgQFgCWYGwyyJ7IIQk7AioTUh1INBZqO6wxI6CgN0tmwsKggtB2WQRQUCEgZkqlRln3MdRexzHZRwH'
        b'R2ec0eeCCv8551Z1EpK4zLz/ffP/3yMf1XWrbt313HPPOfcsbG/diq17K9K63drjC7B1BkXp1HZP1I6I+dq2Tq2U6SJhV9HKS+YBtSPBxCkdfIj4xbUCkBNcg8giMfqF'
        b'ZIrr6DX7hdqOfh7jIpICoqkk3LNffv8BAwcNHjL0mjFjx42fUDBxUuHkoinFJaVTp02fMXPW7DnXzZ3HtgGKt04kAw/UQeVyWL1ZUtjMzj/CpvLFZYo3bEYfJQMGM0LA'
        b'dnXPBwxm87JT1MOlkRkei5x52SGSJCPb3ruo/+Amna+YKeqtyeKwoX3bnyKHDiYyiwNI8PuOUTfgpffaBJIBg9k07BH1YCh2kbiNcu3RTGxBZB5KJmmPiP3UbctIkVo9'
        b'2KDdm1OCorN95A0fg6mpwL0fVbd+X2B4kvkLLWT+/4bPkdYhoEyo60SayDuc6n4mg8gjb8zq/VExc8T5PTrVocha3dtffQi4Jw6WXiM3n5uv3u2qrHgt0+RFItFzduFf'
        b'F1wHW9T2ikbYlrpteHxt/vrHt+WvL7wftbo7c/NzTB/9OTlLIA5oUVpxTl4hjMSGvhkWC2cbIKiNueo5sjVVT2gPoivsnbibALJEz3vFgC0T+oraPeppm7FftENHVHpr'
        b'XL7KKrfXV1ZV24auAO0M+bFm5cPIRIthK33RMoBRc26MV/5i1EDfPYpTj4KD5psBt8b5cjvyhVxt5wrqDhEtqC352MC8PoXaRtgreimmWzoOKPiB6EWirnjXTMwZ4JtF'
        b'L/pxOrCthAxId8S0Aom4EgYQt2t3anuKcku0RvUOdAEqceaOgl3dvJLoFT45Kekz7jqOS19wfVLFAOZJQbvToh0a0F99vH8/rjuqoYUsJby6s/9IVuIZbfdIeHuyv3pC'
        b'6s7Z1Cct6jZePdkln5xBaAdiBmp3m9ATxATtXB/1TnULM+Yfmnqzxi/guAUL0jYsmc/Ipd1lWf2eAqwKD4WZpf24OuxHR24guTkdzsUOHZ5WQhnfHG8bMUlMx4y5H02O'
        b'Z19fKDRJA0WY6NELPM6BPphi0uzV1uao24oK1UO5y1eYOSmNV491ZBae+28YM/TXAgxl7YLpRyQzK2XmiFELatHSv9+C+Ed66xaeX+Wbu7/Cp+C4eJIH3shVvvPRXpP3'
        b'VXhz5PjICSXPTxbHOC7fdd+bFzefSI45+fd3Xz71afqtF15au77L7DG59xVZus36PHX5H3+79d7JX41955sN97yeuXJ1Rs5tz2rqc9bGkPMZteI3tUsnpH/7q5y05056'
        b'N/ecdP8bb3oGbLjy7S/v6rXkrf3q9W9OWqlpD0zb88mmZRnPpPQ5UvLPNwcNP92r+8d3PfVR8pbL056e/+1XvdImvpv33bQradmvT334zmOfT5/X74/Kf40rOvvIDvmI'
        b'8/S17yuHPzzxasnarRmz9899+M/FaecG3vTFe132ve0sffvsheGX/qtrye9Hv/Ihn2VmDoFOqg9XRzBfw3yUaQCnQqqId2q7cnMmNyca1UfVp2ALb9QamaLfaTXoIqP5'
        b'E2ozo3n1RAop+o1U16lbmjSU1V3jmZJyZ+02ojwTbtHWZsdFtTbrsKj7mB+jY3KnIjKK1+7Q7haW8KPK1XM/PjDOf4e0NLoWNjm3C5DT0MH98gktXdsKLUnDdUty3NjE'
        b'NNjczLwkdAe21U4he1P4NGJJyfacF75SLkZQGPMEE7ZX1CjlbhcFHW7CZP9KfFBB+YjjmvuMwbqeaBvtpV9oB+1dpx3KyZmUm02q57nq9uWAAE/1G9BP4nryknqP9kgK'
        b'LVqLFDNDewzJhG5ct4m2csPYEv+10IdCY/4gj2GmQ8CxYVzgIPKnJr+kJPlN8F+C3dyUwiVCrmTI4xd28aSsrG+dQVEWje/WiuOBDGvkIZeo5AelXRjKXWwUoGRGnEkl'
        b'rRjlSJw33M8pFrydscF+KDCZQhC3CF/fPBI8UTZtb1oUBv5Ng5pI4+rTF3pqgLVhKkptha9n5JQYNtXV1roVBY/bwhJx2eaw5HOv9AGZgkV4K+vdYZvXjZpTPozNvqJS'
        b'9i1WPsb8ouxuHZseGvg3vP8kArmO5m15WdTPr1GmYiX3CF146YokogdWCt2YqZ5PbtAeLNJu10KljNsxNvCu2oOS9oR63NmKKo2MK04wUqVEN3NANztImCc04jOYTBhp'
        b'2KFkEUeaRH2Ckg+TLMgS5BD94i6xkWJ/N4g4mVRCHjw1UQkiTrQftkTZRFSsueRS5ojrR62s8vTJGUX0ZWX1opHzu/e+IXP+jXDNycL7Ptmjrh91LdHpF7GxTAL2LEcM'
        b'JHI5YbPXXaaULw6bFik1dbVhE4qf4MdTswKm5pe0OsMi1BK21KLCmVIdNsFQwgdWo9LvI/tj0X0ufO0yMv9R1IVKkojIIpHcTxhCXPyrQ3DS1sxTHyBPtOpjgFjPq4e0'
        b'TWqolFHH5DLYwg3NMqvbtHuGtCA9Whx97qb5AMpfSOSQF2C8izISrYCUeLzu4hs5b7JfkIFX8HMutA8SlK54pTfd/cA/uOD/eO4GWwPxQ1CamAwzw3PLelLuwZHcw1lu'
        b'pEHwv59XplCOiZEcJS1zUOxCXKph3n5JSE+nyYHRJPD9klaFr6zSAytFcnvcVTAp7uVuz/csxbCjVnH70KIVx/zvoi5WcIjMSVcsBU2PpXvpSiLyqlfosH/MWG3XddrR'
        b'nMzJeVnEqKobadw38Vw3dbcpUzvyPTblQD80O+wHRMXNE90SBUfmMPjxVnGJeYllnhWeYUBkfGZxW5bYZIuRAtLQAkgOLcqt8+xyd51fiJId62zzoiLpaNkJaYceO0cK'
        b'WCtMcowcC99Et3gWJ8fDM2fkiSQnyInwJKZFrg5yEjyLJUtybl6c3CMgVvBkK26bFy/3pFQXuSukEuQM+MYMLUiXu0E6kSL1dCCWq1c4agJMjbvaNxY4wBagaMgmZxgo'
        b't0nKLwN7CveScU9SSGBL+QYCgYtX4N8lfhgQ7hiR+IAecXRqZK6brS8XrVcXGgF6a8vK3ZJkIGKhPq1Z0/pcnbFNvpLaihwqMvwAtobwgS8BgLPxiHd9ZYvaspUL22o9'
        b'ZZXVLnhtNZrgEOo7NG9CJEerugWj7niOGenVWIzlqRsoHhDCJhfuDbQw2rTWw2UTI+niolixPrZ53fhpq+mJVOug6UEMIBtGigd4JRqaplj5tmtKNGqyC62Yn4hI2hOZ'
        b'dtoDeCaGpqOPnnjU44edADG7LCwVlI4ySi6EEdyyKHgiLee8fWWTX8Rf2AV4PM6BJxb2VRJn5JX5XVASTdS6LGvJJb5vmM++JPTpC1NGfsxxpSoWnDz+pkumm7IbMry4'
        b'+XprPZW+sB04TcXnRUfPtBEbNlwUhwMxTZivbY9ZdQG2gb3ZTSE+UiR9+gxbMbvQkY8VhNV2vj61BSA2/6qkhVtVsfnYdTHAkMbOx84ehF00ao2CYbcqKqnYM5O3DkgJ'
        b'pCKqZUPvEbsQtkcAvp1zCaUTfN8TJ1OixsfzLQEHS/w3Grm4qZFKR2ypBQss83iUNL5diqorvMrE3boL3NQnXN0c+LpNTEMtQrv6IABSUEICJEhgvQQAcJNA7eON9jXy'
        b'PLyjFgoA7GFTtbeqrBaa2i3SVDOL4KJHPA5b3KwdP86ouzuUkCvpdrd24AmQ3KqPb94XVnz7g9uPdUWIdEWIdEVo3hUcauhMRAiWztM22qwjlejDypelAwaGP1J68D/W'
        b'PL0n5OzfvCfxrXrCym81KRFxFZpCBKGlQRF60sHACEos0iYyUd4N0BukEHEd+wQdjES/gYBFWNejGX0gKcnYMTy+ZL2LcrmAyqr0uatcLmOvKOJ+2L2n0gu+HirpZ1V2'
        b'nQ6L5euTWyzXpsLbn6kFzYEu5fv6x+YKsWxkZnvqMwtbIc2sqM+s1Dw34DapRMngDRI2nU0fDcUN+KBptmE8vEaTjSmPuBD9cVOeCeWMkvS9kI0MxnVgnghajk6kqh+I'
        b'U83ws1Ayk1XT1hZqdbkW1tR4XK5CXPsoPKhPbFkZe030+8wWs2HwIfgR0XxBWCl+rgKpXx7p2/thl3mE38wOOsSSAhiYb7kIxbgKkHJltS8cg6S67C73lDENVrTU99Ww'
        b'E2ljZ8DPlBwcbToFv0rAbFbcGMyt2AAr8rV0BfjrKy1XDMtW0GYnCKTSI52QCWxkYZNETBLPtCMMmkkqzx9YjbaDLDJc2OZeWe6p81Yud4ejcVdzActJoQs+w0amQwer'
        b'vSO7d6fDXsBsuYSTYUfywBZhdLEf9i4fL1+37qLSB15Ma8IH2DegdFpsGtimFtgAhyLCl7wAl0o6m0BhANACfVnHaBORAPqBnW/Ec3Y+lbteaDA1mP0mv7AcmkQrxZSK'
        b'ceQEbxa7X8Tj7wj9DeAMM6L2ZWa/mT2HO26JhMoeUFMMlGdpsELNZr8FarP4rTi0fksyBzmHQ05Lg81vU+b7ee9M4E/n+m3wXhzBVQt+G1Is3jK/4C2TqfVL4NtKBlGS'
        b'foSOC/SSqQdSW1m2sANWBvCWlR4Zpjts8dW45MpyH2lS0P4AO4wPYGth2IYZcRl5icrUGXiepD+099jLa6q9zPIwzMt47AKFhvlyxY7FCOUy8xhIJPInXLsb62DIPRun'
        b'DnXPJMJ3iXTK6qT1HU9r3MyzEKwYrQW505YbsN6JA0QS00LMEgoKsviCrKSrlZSpK08ZXVGkSM+iecZ4Iz/NSINOvL7t07jQlkPomTCRkoWXPF6HPepFs+CHPz5GdlNU'
        b'RGwLbwyElbOKggTcoCRgt+HOKcY6YqVEKdEcb060WO1OySmlmOggqJu2K8GLUaQ3FWsB7ai2KWfZ5NwSE5c6WipI887M4uvwQCVPPao90cxYS6MgxMWQO0vbfYuZ6y+b'
        b'Z2qrO2cxDSpt73gMFIqFZsZhJp6LulnQDqontFOttAoRzkiDKj6CISqBkokgN+bao6psqVunV5T0NvCURZ/TOoNZiRWoKStK1IdZ98rVc6wpdvVBQdugbu/Zigc2kJd3'
        b'JteMB46lmK6o9g4cL/CWEnCvPPOdNs/EzCErRJ3bNaMHNchjkR1yNPxaZaccsw49sLH9Ii7sGF9XVbVKb23b5DJtMnjQxlgY2H75Znwm38RnMuEDXEUSREiycSCqmCIb'
        b'q5nXuQXcKfF+YgSAP6GBcyHxXh0hpmgBmtmzq/kkNJloMDClme8CSwuWU4fmPfppHnSY9xhlHN/ODmoDWoU1Za0xr2a+PqlFhZEs7ZNr+skqkSE6DW/EYaI+T2kDoBgV'
        b'hvjM5botwhvy9SlX9TaSqf3qr6WplHngCc2o4EaUI2B8JT5IA4GMOTYMJlpA2aCSSvRUU4MrIppZGYwUpomkUSOCqTf/vYf1hHlCBvnDkKCTBHRt9+dH0z+kMyBF6mpr'
        b'Bi0ul8dd7XLdZQwhkNqJV1VJGdqXIWBnfNwiQ02B8IGEG0x7RBe+c7nuMSDG2gaIUo4f0UPkPwra7R0h8u1I3E1Gxu7qWnTq7lq27121mVBo7Am0ICObQyFepkR2CHYc'
        b'3P60op+DeklXMLFydtFqdoixotVmFR0iaah5tbXaoZnqeW8WYm71sE9H9IgGu6inJW2bureyfTSI26+BBreKS8Ql0jyTm2mpoaBPcktLLEC96akAX8ETirTOszLRHKBF'
        b'hiZtJGKz04Baw/GlC5e4y33kRlAfrZ8oQaIV7GgHaxBe242z4sQBSm5d20+THlFlMd8nO9qHlcXCy5+OgpQCvjVFihBxEMtEpeL6Lm104PvwTsSyUYFLvc3H6fwX0aNz'
        b'oEcScKSrOjLFYsJAop/OKdYKZm4ue29aNURXPOZ3mYn36wd5LE38XyPP8hp9Yik91nETXwfETEcDvMP2QuARVjIVXMJgCP5h5xiiGet8unJuEzf8Y9DaEUNMJQAb7wDq'
        b'D2nAJNSq/a79gdN5yair12RxC4qOkXqjWi7RHxWjGsu5v2lhNtFhDjFFJLeH0+rV9drxUu32ycV9JqWiCt6GKcXLmq3Oseo+S4/lGe2vzY7N1iYRJHSmCESKyJjrcCej'
        b'9wZGGodeTqfU1Cytq21xqGnS4SYhstz0vSponGmgSIkELIYTQKLhJd+qWrfyIN7aIlK5NvdSs4dqPSsZdnx4MnSlvvv3tLAP+6QNU8EZkUV41aqZCi9OS7rmiJWLFSlA'
        b'lHqyj7bTGOpa9BY/RT3YhAeXaZsLc/toJ1GJV9vSJw8DjCyzazu6zW91DhWRjmAcHNjDOZJ2OGl18Yz78+PJHp4UJQWR/+OCZmRsgxzdmxqZljV/6btx5JEFTZ3L67y+'
        b'mqrKerec7gFeNp1O5pX0TLdPcbvRTWxNEwxnte+ilrIPQ98V5NUGbaUrF1XXKFBHk8AUI+xRCEB0tVEmy5UstmB6ts4DZWZlpzOuu6X9dLMmtKyiDAPhecmJjlKGEcnQ'
        b'W211nuFTJl0n2L0tiwM+i04qxeuKp8AqQpY8HNWsDpJI/NSwmLNg8p+RdERrt7Kg1qhpT5o+2lbtvHbSqj6mbgAW5wQgNu1xTju2UjtN7vVcJoyKrG6Zpx5ir8Vqflq5'
        b'uq/V6jMbq29Bs9UnNx1XWSpMdFBmmyeSjpQZnrBjMivsj6gzZYU90SJbkXWQbbIdWANzs+Mx6zwL7ZRW2imdYYe+MIqB+1FKClr5ZomA5CMcKktVAqjJ/P1igxQR3sUD'
        b'f8BXomolt4inIwrkKGAGIuK6rn5BfwPEZyoHXIWEAgK/6B2Cd5SWUqF0FElAX5j4T/AL41HhwATfmYw8JJ64xhDlLhFkM3ByEnJyvHE4akHp+XRcwiTgG02MNE5g07O+'
        b'TSg2bHeRGNuFAnbaSJBsytKd5lDuziQirFXcFZUrXai2SRYdYaHa++Odlb4l6ZZJgiCg/Oc7u8lKfsSRQjaTpDuWdF3i+Y585AyMJqWJ32mOLixcMz2RvRyqZ8j8bhxl'
        b'AUVEPKRRrRVGcBwTEKFygDeVhEYSiXscgGBIbETMJydLm3C8cwzxEbMTUobRFwBfbFZgTs1rYbaphB7w3AJovADzsDf6c0JNaAu0VmBPljlQEQFpM8C3YdMMPEIKixOq'
        b'5bBUAtgjbJpd5qlrfcIYIZjYCSOKt2RhOePrdIYF1vr1OEs3RjYPvi2lWvLM+V3knJGrz2s5xuU11YBefISlvM1VUJjjVCiUBMJN4uSBPCk6WBQ3oSUmhSE5FZIXgFxo'
        b'BxO97mVhU40iuxUUdHrrPD7iLKqapE8/GFPL2bJx/zBAycozb7d23o5AJZBb+st2MQ0teoR4u/A3KaG+0/d0s9UpZESUWkAAhUsWQKJTgwg0GCkSkRlZEoIYyebFRjbh'
        b'kl+U+eU8LvRdAj6lZ8bpCjI4KG4FitgNE251VXhQL6SahswQoC7A4VuIl/IfoMkq4H2sSSd9mLffeBoFYbXUaunoVbW50xJgofF0M2M6uPqxJw486CKxCCyORtQSh3fs'
        b'zGE5Lgq8E+Gupw/Qkl9Igv35Vp60NgB9NfJE8cJygcXRHyWf1VbjCebBU1jZxO7gCYxqEju0NpewU1cBeDoEsktJs6qXVtesqG7aYtO7Z3i7XzLflOHFQ1mzMgCHLIkk'
        b'KgyRKdcR1uN0EtcQuhC4zWvNXYSjXdWo6oQOv6GAVBxYVHBkpmCxPDvKSEIcJcTz9R1bDm/zT1uhp4jYrYJrfuRJkINUDNIzArur5Bokps2km/ghCsIvyFTRb/ZLhPg7'
        b'+CR2zrUENgWUYu/mp3PGBmCw7mZlKa+DiSJHFiWd8wDnjl70gTC3NBNFWQ15szIEkzYmYYYeNVujbQuHPZC/twGKOFJ2URLYmHVpjcX1qsUSWA62Npl1OdJw6oLn35fa'
        b'zoEi3jCIFiuXJMV3iO1qtSU5SXlNDWj7tH3qmsXeCLWqPV6sbUTnWF2SJfWMtim/Td/s+I+imEYolBjizQ3KhAVOMKgSfHM1RYL8hE6PkJoOCjKZADM2bJ1SU760oNLj'
        b'LlGQWWhBk7RQlpjMMXkuYzy9dp8g87QQGWst0Ds6Ek1CGSaAGFxNJMk0k1TTghZ/LqvM6UcSlxIoRrNc49ZDHiCdecmS4e2DSoE4bWs4Oh32Yj5aZWFL2UIvKiaEraQ4'
        b'KFcqYQuq19fU+cImVxWFPaIQ8GGLC3MAld1MYyIsYQ6lrg0eHUHiGgO6cD1iYFAz/dn5+jhjkNqWhyKSsxvjhE5fmB4pCgLRltHG1VuDuPwALSG6nsNV55M18Bge0BXP'
        b'1Wf4YZHJwlJR6XIrfmVWMucAA47I7GZSR9PL45dKSn8fjCOOOzyzyhIrz8hbbWe/K/gVeC5HIz+DW2YlKfLMi3GE5spr6jwyjXhZOUVdwMDXSz/ccR/+OzAqywasIAwp'
        b'DVPYVLUUBlnx4b2ldAbx9GGTW1EAG63Eh47pddWYXX/j9bjdtToeDFtgC6KiFre7rMMSVj7OpOv+ohmtQOa0dHJHRjhkorla+Npsk3jhs/royFzgl+3b3zB70yWc0oFG'
        b'AmGXN+ZASYb5kIz5aKHwt452UBN1jgGNqdIbGQKTUoX3JKa6miuuq8YGzTTpCIAFrgFi8ztJqI+JNJrl+iHii5GVcpP/dyXQnlAd/Sa5AdfNMxn0Fl8f2wxe6WX7w5Td'
        b'rD4EWF2KLTApNh1GwDDpptyE8yVlHbZluTFAyopI0642Z3K5ACWjbPYGk2FzSwS4mVQ0mjVSz9ZKKRr/z+F0GoxmM8qQG+LwMKVQpKv5JtUwgL4VNFflnhqgFXHgDB0Z'
        b'yeVeWd6GiBlQD6xp2RQ5C0E+wdFy3bM8KDpBPNnOpkIjQ1MVxEsILxt/jPC3BjINMhkyfc4pOe2OOBQAOyzk+32VtnkWOnwq1TYvRzdJhdMSTFz0EtE+qqDVpmHRf4kW'
        b'iAiVUFldAnY1IlhCDdB5khwbYDGERGBvrRVmEvHaYPOIIwbXQlGA8PTLBhsJ5rRDGXgK1pK5jQ9LBVPHF7RCixG6BA2NfJxOUcCmAZSEwFhJYwLhF1oXFJZIaAZOaUCK'
        b'PjNL6VsIZ+jbRE1dhRX2T1+e4b0UDQnmugqThpSSuQRDf6i1ZYvcYYfX7XPVKjVyXTkwCA782jV7wvQZhaUl4Sh8R451AYlFuVx6PHaXiym4uzBojUHdRVwMfN98Yt01'
        b'BtAnkV4v4rT6aKy2bS6zPaG1fnBxKW4GtCS9qqyafIqibxvEC/c0gTfzUnM1yYk9i/RhOTSJRNv18dSQFi9LWjTHxDWTPT/YbPZw8aFndr/A5GRLBKVvUNqFeII04YHV'
        b'FXdJKGVey/Tm6b5BBGpfTOZQP5ueAmmwy8yURYg+5ZUpQaA0ZdNaYYsTKFRpl8UvsO1NBjCSuLUi0yLL57wTV/BMnj2X0zXLFiE9j3r0n5HaR0bGjAlTx6R/hkPAdChX'
        b'Ku4KOxH6YWHFQh1EwmYgHGrrfDSKYZNcV1XrZdbFyJTR2WrYtAJVH3QpKUN4NM70iVCx+Mfblis7ceBNul6ik4gMB4GFg5TWUL5lvwJE7WXYMaJofljzwrZJbs9yt6+y'
        b'vEzBgODM9BUnqNwQYeE/NHeJeA5CHs9PZANwATzNGVL5pAMO8yHq643Gn+6BswLKX8Q3Qd5nAi7TlMihNiw6AGHpTixtlc0NNtnSYIeZNkM6CmAhirRmfQ0O4B8cqVxD'
        b'tN+mLDTy+aNhpq2w7U6RbQ3R1TGUtkN6vhzVYI/UbcW6lw1t2Ra/ww+kawq3FNYUli07krlUrrYGSnL6ncp9crTfCbzhfX6nXscGv0NZg6cbOk6BsmSn34JlyWKDrdpJ'
        b'ObH2+/At6qizmvAtas3IFr/JH+23A8FgW4LXqCUOOW6TGUqzK4cwF7TRTDAXX3IRDVYu4sjPvIiz/WEg6c0XvpzxX6MKSGBySRw5ciRNV1h0ATbhZzJek08P82PDlnE1'
        b'dUolICO+MEsIm6rdK1wr2c+qrGhmYmAnPWBPZbXby5BUVZmyqLLaG07ARFmdr4aQm2sh4K6lYSs+rKipBmJYqamrltnpyx0IqVK52+MJS9dNrfGGpSkTCmaGpbl0XzLh'
        b'uplZMQy6SYVAogIkMu8xeX2rgJiOwga4FrsrFy2Gollr7JjB5YHmuPV74IihCpPihlaEzQuZIMZWXVfloi+YvrKE9/DUvdJHj39QIhPF9FBJuzyIiwf9H7P4qg4isGKZ'
        b'M0XdoYqkS/mYpRs6ZUkjL0RMeGGms3K21MxX0P0gCTJiabE1q6hNaQ3tYyu5luuKTtOcdNaPbFGGLIQ4tNgKisR24S5rRcnOWt3BSSrauvCy2c8nMa1LUbYglvNJupi1'
        b'Jbct6uJWK53b2C51HFumoH14+oCaimuY9J9cVXjrqpR4mOdLOT/Gdj6vT3rPvjkZrcitiA4citHJBs3SAH1h0gTd+qzCEPyhnq5hfzaiDZYKLYVOGkRpElfflQYZGz/g'
        b'mrbszi6iI8hLUnaGN5vWDkoX/ooFJZPgAKaG9ODDTgLySuDvy2s8NYqOyFm5BrdHp37tb9TQ+vcj7fw1fH80QnoJiWQWiTKu7ryOhVnZ7ORfUh7CvkbQsLKLb5ca3Mbr'
        b'SF95mtcraiZi+Fd8izYJGzZBYUtNEWFDrGS1pEiJzpRMMjUerAULvFHDrqldJnKCtoPvpm5VV6MaYIQ6KCFKuaQEDfQp4sUds2YzBwJP5jf3H7BEO4racyLZUKtbotSD'
        b'M9STGGioG9dNe0o7jAWQZXLxQHLnyL3jXZb7bR8rVzl40Ezeux+IQM/fbiye+fWchEWJD2T0HDD3jRWC7fYnZ7ltO7vzCSHPZOvCoyPrw+c27+jzu8nzl/auqlJeuOkz'
        b'8Yp4ed/P/nhhxRMBzf3nc998MeSrpDeVHrW/vLNyV07Ggimb13Sebnl2j2PKJP4vv0p6aVt2v6wBP9/6lrR3j/U3v4w/OuOL1TccM39879wFWzziTe64N3rv/PnNq+xp'
        b'd/RdvfaYPe0uy8/LruE2//La2pmDV5cfix/a99ndaaWf9Ti7qPLsJxN6rPz1u1W3KlWPVa5P+qDyWNWJj/du+jDKN23U8MZnZkzd/OnK2IeznvrtF/OWbx256N2RxdsG'
        b'Degzd3/FyrUHX7qh8eCOzqv/Fv+V9vM9S303LCse8sQBm3vIl8qabU9aH4rftmrLwes/fD993JC/VPw+sKLv1luWJc/860tbT3d5+mLS84vnz1m8frAn+9mqT0bdan3/'
        b'24GTXsl9/sCUqXtKD93WeU920oVr1g+zn939WfSye5f6g5dfHVi6/uREU+GJtzKP3NNlmLdyTdIv+j5n+vTB33Z84b6iovcafJ4NCcFZ731z9pnh10fFPzElZ/virnNf'
        b'nvqXyfMevbRv8x+PzXRds/3VT2Zsu3zbQzEvLh1xoWHE6smT9z+ycejwsxs+Ov5hwuiY73yB2bMe2j4n15eT/f6ElXvzTw33b7uwa8TYfSsqowcdOZH2+Uc5nTtU/qzq'
        b'5UuFhz64teilgnXPf/QHnxLz4o7KmL9ufC19wpf75YpBFb7UP/0l/9Gqt6P92a9+5y0+Pq70hk+OLDg5e+KXO2fm5z91ouGO1zJG7crTvlh88umEBacqLxzVnoyO+vr2'
        b'4LFN8957ouimS2Pfm3fLoKMXu43s/9GY5294/csPXrl2VvSoxq9zXuoy9fnaB3ac8TwR+PyNT1OfeTVu5LRtm0bYDueop0ou7B0Xc+pKzKM7Jh52vTJniaW461uWhj94'
        b'R1y5eOOQr22DP9344NLi6RcuJ9878uaNh1yvDqm4JWvA8eibrZfnd59RfP6Lxb8oTzx97uF3ru+66bbBX3xy9NdRD53f+POHkz+PP3NzVtQm58/mJ5cuq5+wacbw54ou'
        b'565ZUXr9pcu/vbz499mLujzw3ehRH/V9+eVpVbNGPvpV6MYev1vaMOTk4z1PC79+8XPzvUOmV3713smFR3ufuv/EyNB151+a/8bb3Uunz3ppypXHbi28b0TRuov37vEe'
        b'fOHaXZdv9k39xeE/r4pfoYw9v+M+Wd045eWag/MOnNl0cUP2Z+cumV/65O+fO0+//avDBZM/GNs5/+FZf3wrLvu7tW+P+8eN/7U6+MCz4TXDH3rX/fmqmOO/Vz92Ht0z'
        b'Kmvd4K0fFITHa1fcv3q3ZvOhHR9YrvDq735hHrQgK5rF2UAfWHh+ir69SqfkDCnMU29Xt1i4DtoaUXtCO6OeJwft8xVtH2YrpTN3dTNmiSurV8+K6t0DSsk8/9oFy9BF'
        b'a6G6se+kXC3EcfG3qGvV20T1iVHqfrK/v1F7fBq5/UXP7HdouzBI2AlBvVd7Iol5gT/kGKAHh48Eho+dRqHhtZ9lsuiM99gbdJkqN6iFwqt2/mbmJWB/eQI7KrahwXie'
        b'wMXIbvW86FLv1nb60JmstkHdmgFtICtWXTqrhtQjQ4zOMT9nTKXAP8wujcrwoYBJXa3uUI82SXSXFRYXqfeot+dqm7Ja6yLcUmTnEgaSf/oR5ephQ41BfcjUnsrIEL8P'
        b'45crHm2Htw9FiNpSZ+RR1+S3oe+wQtthU09Cg4/RZKpntHuG1amPtCd0HqvtYG4MblNX+71Rmb0jO0ZHdROQhT99i2rvknXNf2Nh//9dsrozcuL/iYshN/PUlMkuF3mc'
        b'QFs4gTeXo6cGM//T/qQ/Obs6bajjLoj4P5EXHLG8YIPf+HheSMjkhakdeSFJAJLMnJstpEx2pqaYpNGCkMIP5blbBFsvXqgDFtqKJ/49eSFW4NPpmsYLXVGVTDDR1ZIC'
        b'paJ8WRAFdMhoannv4AUrewJ5bd15IU3gk6At9N5J19hevKNGIgttQQT+QoISu3WBnCm8w+KgsrrwVif+QqvnCzy0e6DA5/KOEuU3kRPB2/53PfzgpYmRwHFDISc5h/C3'
        b'EbuMLB+0gHZwWNO2Bdgb9iNnqtid72xVT1e65Gzem43RQpMa8+76VfXvRztuW/TEdW+/37AiafhN7/UsuT/zovnz1Pqs+txg4j17inZ8IX841fJV4NS1t363d8/e9dzN'
        b'XYeOu73757Pu3Pynd19a98icHX3Xbz6a61tvauydZm8om7E97u37Pj0T/7spX+V9kHl4yyvPxXeZOvarv0wf/ebruR9mXVhjy7wybVrjkacDva67uKf/L8Y+/4euD+W9'
        b'dku9Wtut8/Of7ivxzpzy4v7Ft57+8vP1k9POZmbfefsND+6o/NO0e80HDu4fseLB3YseOjn70qmT++7bM/jr9Zv/VOyX83JOZvzmH/c9PSKmZ9KT3R7/5TfxRf6av9/z'
        b'wY0v7PC9/+CJ299o/Pzw06898uy8nJ2Hi5ZfmDfu4zfmzfj4t/OKPC/Om//xc/MmfqzOmzP4namvTXl95D8HD/voyvS3bhya88zmZft/N+vj8N9TPg19cMcitf7sAx/X'
        b'jnzzg4XHLliG/WF8jy4ZPY70Kj/S8xv/wStVH66uyY057V719Jl7L/irV6k3/HrG36J2/mOu8sK5w1Wh0je++eOHCy8+d7bal3X3okM3hNwfHOpcevfS2V/c2PtcYcXZ'
        b'B976Z8/T72/+eFH8+t8+cOaWz1/dmFjqeeybPac+/V1MpwNx5/L/VvDZGxtfrznw5bfV7096beV3D166q7ShY8M7SzMXD6394KF/vtNjLTf3T3dM5CdsfXy9/dH9jZvN'
        b'OxY3bnI+9ZfGLfxtbzzrXP54IO7ZNy7wzmXryu9/J3HR0AtS8pNPd9j75LPRFU8+03nsW6OufWn1bY+9uef8p3P6X9xQ+tHdz428bLpu2O83vTAwa5SvG0c+8O7TDuiQ'
        b'tVHbkKuD1nRRu1vdl6/cSJ7FemhrgBS4mhxSz6pHegM9NDSfvFwuyZ6iBy29W31c26hHLb1Re4RCIqbkLclRj+SaYf9doz4ylF/AaQ9QC9yVMTlFednoJUvbYu5CoU03'
        b'FmkbLFy3GaZ4ixby4dnZPC1wU5On92I1UNfC0bu6Lp08GvVV11mKIJu2MQsz5pi5mCHiTZOWqvvUw+Q/bVaWdk7b0HdSJ3WvtgmaOIlXj3fUtjEPnrvV0+r+Im1zpsAJ'
        b'1eqZrvy1Pm0ttX6xeXjOZIzZaOLM6p4JowXn4Dwqb+6oTKLwMvPQ99L+FSuFfPWAtp3FWTykHphdhK+zCvMwVvUOzqqeF9RATQYVqu0c0RsoyFzYW/zaoUR+lEW7jRqy'
        b'TLu1H8ZOwTfqce1YP36mdsd1VJ/aqJ5qQMdizKlYvHqqo2CPGUnvZgDZdI58PsJ3DUDQ8gXq3SqLJqTuHqod0zaU9uGhyNvVk4X8RFE9Q1RUQvIcqCwIRF32JO1e6D7S'
        b'a0ikTdDuzxhoGq9t8TD3co/kJqh7x0QBMVuUZ8/UblcfU/dLXEf1ZxIAx6FCygTl7FYfJI9tMCroqK0I6NXkxdI07c7+EtBtKHxRnwAQOQzTMBlbs119StvNF4zVHmUt'
        b'PRKlrs7Rgn0xFPj+weo2fo52cASLPHO4FmevEGdOuEW7Q9vJj/ap21mZ92jHta05fbRNJhq0Tdp2fvZk9Sy9VK6NytE2980uLOYB3NdztkGCetd07U5GYt+q7bypiBDr'
        b'JPVOmGUSD6wRtD0j1aOMTt+m3QcQtKG0NK8QwaDYxMUPVx/V7hbVgyNGU4x0WAtn1QeLWOTg0hIqxHmzCAxBaLx6p5fmWz2h3rsIem3m+Bnc9JHaw2qQo5Vzk/qAup4g'
        b'W70fAEKPBnyjyqJ5lkEh+4CGPwBju9ePjlGkhbx6Tl3X34dii5Ha1h5FeVmT4TNzn/IZQtLSDgR9i9SfjWBLQTuv7SkECIRebRe0/WInWncJ6qPdASCISNc9hMara7UH'
        b'gAvRVsP8HKAFVQ3jFSgqzC3Mo4WHPjJvF7Wt3pKZ6iY2J2fUY9qjkEM9uLgQWi7x6kPV2nkaFO2suk09qi9ZmLWsQqhDu/t6s6g+paiPM/blnPZEaU6hejgzq+9kAPgY'
        b'7WFRW6/dBczH1niavGSAzlNFOZOAITtTCEu2Iw+L4BHtAIt2fGg4xiQG9DFX3YEMlDSNV8/kc2yxBNX1AIWTTRxfxMHtPm27dlbbRfWmedHr7iSE0y3AbqGTVBggv6Dd'
        b'P1TbR4AY0wumeIMWLHZdM8XMSbG8uqNO28/CN5/SGrU1RcCLDRrAT9a2cxbtLsGsPWVnXbq9SDvU0utpt4EwbMPVPepp+r7r4N4t/Y4e0Q72F/OXxtGYl1VkF5GTbGOZ'
        b'O9VdohrSTo6rTmTAdmAuDBFz7lqg3d/CEa1253Ra1YAL9qt7WjuBnQmYfqOoPZCurvOhs/DFvdRGRFF5sOKyYaZg7d8FMDgFag5CE/LURyWuWD0I6PKQRVujnc9jLdii'
        b'HegVhWxvLX5chNCVqN0v5nu0vdUwSNiNKnVHA+HGPhXag5OKAfNEabsF7RQA83YC7O43qVsBU0An7dNhV8FVd1zQjsdrdzFcXq8dh1U7RdtSlJuVB5OY0GVyJmxL2mZ1'
        b'DeGalE6di0rzamyF2MtQYe7kvuR8M5czAdDeqbLtJStT26Fvb5tKs4BRVDfh5pWUIWn32MVa7TGGA47fkIaSgdLSbuoDtAFZoDXHYLXEaY9TOeqty28crJ2BOYcmLUeo'
        b'Acw+xcKlaselueoR7STDFLcXak9Co7THsSyMWBSnne01WiSIPccg9mc3dKExg81mJ25zUh6vHnaPo4AmGLJEvU1Wz2OT+0a2RUxZuE49JXUtV8ZAe7/2kHawqLA4u9jC'
        b'madrqyXBWqIep0b01HbVkgflLFicd0OX82BotT0IHDvUdT90pGd4Cb3mP4AV+w++RA7CiUFEnXYhyipY+ZZ/dj5WkEwO8qSdBsS8wFsFp/7Gzjexk3ZdPdIu2Pmmv1jB'
        b'jCUKGHYisUW5DjoQom8EtCOSKJedHf0IfrGle0T2Z5bNPBPd6wrrNvIgUVfrcjW5PDTOP57nm/cRb4hBcXzZmkGhHC30NKI5dETKdCS8T8N1ISfzS+AvNDs4GxXrQr3h'
        b'V4BfAX5F+E2CXwl+ZwVnV3Lwaw/ORiPKUFfMvwRz8gE+MNtQBWzgUA3QI1ZJoZgqUwNfZW4QqiwNeM5pkW0ea5WtQaJ7u8deFdVgovsoj6MqusFM9w6PsyqmwYJnqL5Y'
        b'KL0D/MbBbwL8xsNvF/hNgF94j6fAoW5+LhgDvzF+8qIUivKjx2A+FAv5EuE3Hn47wK8TfpPgNwOV1uHX4pdC3WVLKFkWQylydChVdoY6yTGhNDk21FmOa7DK8Q02OSHU'
        b'0S/KXDAVFeNDPeTEUJbcIdRHTgqVysmhYjklNFVODU2UO4YK5U6hbDktlCt3DuXIXUKZctdQgZwe6i93Cw2Tu4eulXuERsk9Q0PljNBAuVdokNw7NFLODI2Ws0KD5ezQ'
        b'CDknNETODQ2X80LXyH1CA+S+oXy5X6hIzg/1lfuHJssDQjPkgaFJ8qDQBHlwaIw8JJQnDw1Nk68JTZeHhUqC9rVcqKc8PDTWlwx3cfKI0BR5ZGicfG1opjwq1E/mQ+P9'
        b'FniTHhT8Vr+tAkcpMeAMJAe6BoorJHm0PAbmz+63hxykmdPkltcZiAkkBpIgZ0ogNdAx0CnQBb7pFugd6BPoG+gXGBOYECgITApMDhQFZgRmBmYBPHSTx0bKswadQWsw'
        b'a60QslHJkl6ug0qODcQF4gMd9NI7Q9ndAxmBXoGsQHYgN9A/MCAwMDAoMDgwJDA0cE1gWGB4YERgZODawKjA6MDYwHiouTAwJVAKdfaRx0XqNEGdJqrTDPWxmrD8XoEc'
        b'+GJioLAiSh4fyR0dECl8QjTkiw8k6K1JD/SElvSGloyDGkoCUysS5AnGNw1RQac/imroRd9GQS3RNJ4pMEJp8HUP+j4Tvs8J5AXyob0FVM60wPSKVLkgUrsIbRWpJOlm'
        b'O85jgyOYEXQEs4MOvyNYuFZAHRR6kktPctmTmx3+KDqfnchiM5D3kibDl/aV73CLZgZnQa6OV6J9pLW5hDdU3HWj7EsdMryZWemVTE+2LH1hXaXHV1mdJShrEAfR0SMe'
        b'vrbrCcxVUU2yOtSxe8mkm+056CRcedGw2cmSAN0tcvsqFDQSsbpXlpNWEFnt4/l+TUXYYehFkT4Uj15dqgA/wp0d3ZZX1SpurxdSoqdmEZp1o/qc8iKUfRG7fJHGhu7w'
        b'oPTi/XjhDF3xGtkNWJYsO1DPPizW1tSG7VC67K4oQ1MOa4WLHRozc9Im/xsRzBw2V1A54ajyGleZsoiCn2L4VtfSFTXVnlWRR3Z4VM0KCzvg3usr0/2ZWiFV4Slb5A1b'
        b'4I4Ks9FNtdfnpbdkHUA1LC9TmhKodIwp+o5unPRU8ZL2RnUNleOBCSxbyD5Q3O7l6J0eE6icQQlTucddpoTNnjKY4PywuLByEenUo6MfFr4kbMcQ2uye6Sr9Up9kn1JW'
        b'7sZomS4XZF/oYhNpgTvUtghLLsVdEXa65Epv2UKP21VeVr6Y6UkDYMjMDx1amV8SMrNaBSxEAEGiinn9ElhgJNQHQ59Z6PQWdRnGo76AQDbEwlqhgV8W7ed1pcy2FSB/'
        b'0AcWAme22dAdJbrAYQBtizaSxq3RxifgbdACmM4BCysVW+LnAQcJFWhPEkPePzmyMhGD6aTFJvmloL2OU8YEHQ0mvxCMWop+rxwN5upESsFiDjqiuAZTkGNab0F7MB7e'
        b'OKHvjmQcC3PQAunOawW/OdgBahSqp/oFpRCedQkmVaB3oCLUU4N6EqCeOZQ7Bb5Ow9Kqh8HzrsE4yucNxgHesZBBnqPBCjktwUTIKcFeAWO9Fu19Fvol2EF4Ks8M5d0Z'
        b'NMM3Niq1E+TBmXBCD+3wvf6d3wZ3drzD8E1+2wyO9T3Iw/dn4buYYHSUYQwoBmPpXXQKukAGlk/m/FH4zi8Apo1O5piBGnlttbFIDhF9QDaSv4Hxtwc7Qr0CjofflEhG'
        b'hpEReJ3ammyMgL+FFX2W4986Sen2HyC9/kkCboTmgWbdQ4PToFUFZnFmhnszGSvGo6oTOYt1kKvYJKJzzUD3JqFKk+gUYoU0onKtYiIvSdbvAMELLZZJnL7z0DJ5RdCX'
        b'iROmOktfJonNlwm8FXH6ghLsTiktFg5OXw58I9EdgrzJL3l9QRMAojmIf0kw7SKqD/otyhi/hQyNrH6ojQEPLJSOI7jqJcFOwR7BXgD+qRUmdG4FoJvZYA+iEp4dSo3y'
        b'24OdYDkuBcCLieJScUsW4d6J934HLTgoxx8FxGGMDsCkkMje+e0A7pOrhwR7BqODnWQ+2AP+94L/XYOZFXwwDusJdsVllQjEJTzvGOSDscFYJMoqLbSsTQjGsJDi/Fbo'
        b'TTQAPPz6YWkEnSlcgzMYD6QAPnEmc7BsoolEiIKvgDhQztD3cCejwrMZlbkaTNXL4ak5mA2lxvhjgimUB5ABtDcmmE6pdD3Vk1I99VQGpTL0VBdKddFTHY2WUqoTpTrp'
        b'qR6U6qGnelGql55Ko1SanupOqe56qjOlOuupbpTqpqe6RkYOU6mUSsVURQxsDHlI2vu5zYgyERFAX4O9g9HQ41h/7B3ovEyiqwWvBC3JCC1QBox+BfpQ13uTzKEZJIxo'
        b'AkIZlCqSkwsJxx4RNz3P8UukHCwZzg2a/KPH/V9Zu1l9/gPwx/88jqpCHLUxgqOcuic2VK40806KphbPC5LAsz/pG6vVTq5mE0lRU/haimYKmokCqmBKX9kdFA9PspuT'
        b'BDvgL/jj2/uTPnXEx4rxgNvwUFa67DA5yDN8C/xmWKwRfmNuPQGDAdsctOr4zRzkmuE3MWii7RwIlqANCH7Aa0xpXTd2MQIgtAUD/37kBhrU35t1JT4d8YuA5KVWnbIa'
        b'nTqLnZJgmSDtIQBatrGOrCV9VCUBdeiDsejHlJ5LfsoJXYwOmnGHhqGIAUQVjWgbU6iNH7RvSeGx1KhgPC5DHCxCYqIJkGzQNgRIwBEt9PCrrfmcd0JzLXxAgoBOAeGL'
        b'+n0slEK65BjvicozrJm+b1AT/mch+iNzRBsfYFjAq92SxpthEuL5NIIx+9UwZm8+HfVIagJZGIxBMjgyHZI+HYk0HR2APBO9SfQG00mYpgAD3QHuHGjaTO/sW+Jp8ND2'
        b'35JCZhKYamPoh7cYeiD4gpZUNOuVlJN+0VtikOA81icBQYm7s0mpwwifiGlhXzPBDgST3WCpN6EwgqwSbRLn41ZVGSVX8ys4+iKFfe+dRcy5MxALjHliILnCokcIsjar'
        b'xYqYX7k7GI1PjK/ZngiUhq1CWCopT0JbnoqUbEMhCHxzGL6BJ/DcFvmmee07m9vp6aZxYkmbFkcR/8SR2JjIqUCnYdgppga6ysDARui3syYJadflhmecAkP2J/gWKu8i'
        b'f/kR/5MdmISdlV5XzcIK1woFtcqVwRadh5F4SffjS/CXxRML/y9FUUn9T9oa7BbdSJktJNTJdwgO2hiwu2mX7ZJEPpMwHCrabrO4MxIGRbVLf09JtFusQjzvsOBb3Ebg'
        b'+q30ipQn8VkpTEbhx7rQLicseld5lZfw2ct4eQUvrzItcHRi5FV+SxYP9Z7KhcprdFtV5lus/I4szuHGXYaxLpTXyYKnUlZ6UqHAv4fFsoXA+S8u86Jdetiie+UKW7zG'
        b'zSJPzcIyjzcr+r9nALPm/AfI6f/38q8cbCBM/gJlaRhgURCsUstDDaeQYnLw7K/1oQf7k9r4c7T59F//M+v/m9IOc7woWaaI0iA7XyFKS+x8uig5+olSmp0fIUrj7Oje'
        b'xIrsJpBwAvWzBC2ETnIU0cLVXAbocukrsqqsFpalT1G28swmmfwvsLOUF2ndTVhZ7q5FF1UKnr3iyUp5WZ3X7XKFE10ub10tyQ5R0Ib2N/A0ytWUUL5o6UyjmfHuiKoa'
        b'uc7jRtsMRvHBPinFonfgNk94uFusY9iv0B1NMo3TJQlNzC/9HxALhl4='
    ))))
