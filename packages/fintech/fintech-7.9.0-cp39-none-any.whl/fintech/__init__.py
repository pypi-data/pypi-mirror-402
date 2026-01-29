
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
        b'eJzcvQlck0feAPxcOQjhEBEBj0brQSAJ4IG34s2NigdSlYQkSBAC5EDBoChKOAXvW8ETPEHxPjvTwx7b7bXbyu72bbt9t7W11267u3W37TczTxLCpba77/f9fh/88uTJ'
        b'PHP8Z57/Pf+Z+TPV5U+CPtHoY96ILjoqjdLRabSOaWD0rJ7T02VMI50mWEmlCXWsjttEaUQ6gU6IvsXF3haRRVxGldE0tYQyRnOU3qOomKbSJDRVHKIT6SXpnjoxukrJ'
        b'vRe5euslG+kl1FJKJ0qTPCcxSvjvCCoCpaRQHpvkHo8GShZm6WXziixZeUbZHIPRotdmyfI12lWalXqJnH0gQoA+8MAXDH87rdLSbv1h0Ufk+DaPRxc7lUnrUI82iUvo'
        b'CqqMKmGK/Wx0GYLZxpRRNLWOXsekuN0jSCgEyUo5m6R1Hygh+kxAn764Yo4MVgollyW1U3/DjxfmiNE1axBHVYT3QUOqlvoWhVCf8mW/mdZM9QglqWwyhpKxU3Y2k3VB'
        b'Sj81pJu6QupsoDOkXJJVhe4HhK1KUcJdsH4hrFAsRh9QD6vD58csjAmFtbBGDithDUvNWiSE5+HxAAO756HAHIbKvXjy0y/Un6tzMh+qQ/SKbaGaGM1D9esZ/tqszBzm'
        b'gnXuxqDxo6mNRaKlH/wsZyzPohLg1MQAT1RpGK4y0aqENyyhsCqcoZ4BFzlUex0sswxA+YZ6yUE1qIN1QyfHo4ygFtSJKG8/dvA6XxN+zXK2nQmRmzCi8hec+Mh3cqYp'
        b'r1hvlGXyGDK13VtjNutNlvQMqyHHYjAyuPf4pVFBUtqbNkmdRZvZdi7TatS2i9LTTVZjenq7Z3q6NkevMVrz09PlrFtL+NJMm7zxvSe+4EqCccUDccWf+TJCmqGF5Mr8'
        b'm2HQi6Gpn/AvKx6BQWHwSrxClaQMBZXJbsMLL6RSitEC2DwgPwdD1Jr1Cv264J8BbP5d+l+pLTn+FEGmYI2VsYipkG80GzI+WPCv2Q5k+nAaefqJMJseQ58WUDL12ufp'
        b'Er5IWwJLDRyP79SKKL9wPhGuEFLfRSKIZeqcR1EjKKsSJ7ZkwI2eoEmBIKqAdSkRC9AXQoQQlTIEVoSvnREam0hTy54TJ8CzBjltHYLf6JE+ck/Um3ilJARcGASrwHnQ'
        b'xFHB4BYH9oFd8KZ1MMo1DtwAx/AbDUddxt8iyjOZiQYVcBs4t8z6DG78Nji5kH/p6JWDJrDN7bUPRqRn7YebOwwOecUr5XGJAkqYwljHBcDbydZB+EkpbAPX4smQxsYq'
        b'GcoT7GHAAWCHTYmBVhluoRnUr4DVybAqLtEblKtgZQI4zVF+oIyFpfBKEGoCVwQPwW0L4mMVsUpwQkTwVEB5wyo2Cd6Bp62BOIe9EN7EOQTgBDhDcRyNwNoAykgrHDgx'
        b'gUfvRLgV1sfCWnksagRuZ8F1eAmcRuOGESVBODB+1Gj0FG4CtfFwS3KsgPIZwk4Ce8BFlAUTATwbBk/iTLFwj18in8UbnmMjuYUoBwbV2CfAMwa9rXxYDWviUafTh1D+'
        b'8AALT8AmkbM7VfBoMKxWJMEtsQqVEA3LRWYkvAQvwgtwH8mxHhwWhMEtCWjgQS08oZAr4wRU38Es3F4MDpCX7AkaVscnK2PDELiVsYq4cFVMorAfPEEpKAHcC6/OJfD2'
        b'gUfRS0CQhKHHKpryhEeYlEnwSjKot4ZimgNt4HI8yRCLujMvJF4JN4PzoXALrEHYNk8ppGZyQlg6IIo0WjQCNKLMlckJ89cIQmIS4JakhORFOJdiomB2MLzaicEx7qy4'
        b'ifB4O404KGvn7AK70C6yi+0edond0y61e9m97T52X3sfu5+9r93f3s8eYO9vD7QH2YPtA+wD7YPsg+3P2GX2Ifah9mftw+zD7SPsI+0hdrk91B5mV9iVdpU93B5hj7SP'
        b'so+2j7GPtUfZx9nHZ05wcGqqgkOcmkacmiKcmibcGfHnFLf73mSKD/oM7Map7UnW4ZiO1GBbN+6xEJzD/JlwD3Ac1hA0BC1gazahuCSlXAkqMCX5qfVwNwvOga3gOKGm'
        b'RIQFx2E1wkKWYtb3T6Sjwen51v7oSb4KHg4DzQpYvjRGgHB6Ew3LQMsy8gxegdWLw+RKWBEryAKnKSE4xYQFJ1oD0LOYAQr8zhR9wTmEAVwsDW6tQjwAP3o2FRyIxzRX'
        b'C4/iZx40OD7EjxCUDGwHFxCniYFlaRgWLoYGF2FzMAHyGdgCLoap5AzFgMtjQT2dBo6uJsXAgURYEQ9OIVJFogmUUsIcJgReTbZidgwProWt8Qj768DpKbAONfgsDc6C'
        b'GriN1CpbgWgUoyKNqt2iHEAnwD2DSUHQhBDyWjxBPQUNKkyUMIrpD64gasHd8ECQbg6LQ/SWLJiaRAmjGW9wYDw/MPtl3qTOECVdCHZRwjVMpB88YfVHz6LhDYi6vyUE'
        b'dcMImoPoqYuG88zkIAuuob7HYUD2wFa4i56DXt4lQlJgS7Y8HtwGBFQ55mpicIdBPK08nW/xAjiWC6sTFYgAbPA6OEtPAwdgPXm2cig8BU7DKvwMXATnZtALYSm4Tp6h'
        b'32WR8ZgnwBrOM5kSBjOS+eAkGRl4adlqWB0DzqJyJbAV3KDnyBnS9bGIK19EDFSFQa2CO0PouWvhLp4v74d3wKUwFawV4NaKnqMXzx1A+jcE2heFjQJtcEs4ER8eYxmw'
        b'TQ/OE9ZjBS1yxJswGGGqWDSmSQKqvxI2ZHGj8v0JnwRlYEta/Bq4PQyLljiMHR5CBuyEleCalnGjG0wqndUnpDzZaZf6xFQgJamERUTJEKJkCSEy69gUt/tfpj6xSYZn'
        b'v74hME9FCQf/HvCF+tWMz9QVKz9D39zbNdH7PGJG04ZMmdcLSxWeqRsm79pcUyMdFP1DZv3Ey97lauEbUkod9s4D7/WrUuQiCxGmVWBDH14GGpNgbbIc1sbyQjBgOMd6'
        b'gVMWLExtiXC/S1DCy/CMm6CMslpG4opugEqwBVTDm8mIAygSUb7KDkXqGbCVg1s1sIZUN8p/OK4tGaE7KoIew9ZoCazHOFMGd5IsYBc4hdgGnythDmhWoepxiyw7JH2C'
        b'BVONBnGF02HKGCwVkSpZTYlhGwM2gbMKC2ZcqPR5sAPXANq8w3lhgwUND9DwUEEyrJ3oUO26KFsklaha7VyuxryKKHG++I2spzgxzf970xLa1NeZW861szqzpZ01m7Qm'
        b'zFBNOL+c6agU3WOqNPVz1k0Kb8JV4w5TpdRPj1HkCOldgvvDMOmp4XW4RUhxiFecjdD0rtJP5HGSyWR+hUKf2RNGcj1h5DsvqQXmoSiBnvjBF+pld998vv7F95+vf6mt'
        b'fmufe96ZH76OeNFzsgncv99uQUp5EO7J4bAV8YoQWB8SA2vjacRiTjNFSHWrtmBBMhCxzHM8usEDcFNndRw22PgBZ3p+X1aLIadD6V5PefnSpgCqQ+lm8zKye35BSMUO'
        b'dL0bXKTW7d187937u8F59TZYFaaEldqlsAYxfhMN7oC6gZ1eDe34pDihs/HDTCfx8Ae5etLRHW9jXnpeRqbVrNVYDHnGrbgoYUGMFRPdsHVEpJChSo4LUyYlYUW6Zj5A'
        b'dg1LhYGLArhvPjjyH4Ph4YRBv9MNAjw0WBO8gRg03zhSF/1gGRIC51hwywxu9o6a0Rg1ad7etHOZAheCMk+NoFldEZSmemKZwiTrCAxom9YCqpOJPgkqw+VxCUmJcUjD'
        b'Q/rpuDkSUC4Em8GVUZ3qc/J3bCsQjsvzdwQu99/g8BhcSU/0NDp1H21OQAmJb1857ffZXYn6ofqe7jN1Gnj/5cA3fF+/C+aBeQ/u3pv3GvoMf+v5ZfDN11Nfmwff5HbU'
        b'6mLoqvciPymYnsXKEujPP0oQUXMG+Tw74Ss5bcH9iEOamN0MzsYkIQOrEmvB+jwW6dH1LGiB+0bLaZ5XcV05YhcyE6RrNTk8nUl5OhvM0L6IJ4rp4mBzliHTkq43mfJM'
        b'qsk5eSineaqKFHCySk5jWmluF65ajb/dqLGb1cuYsMw2DXbRJRbQh9zo8hO/3ukyCr/2QyWByNKAFQlhSH9VYtMfGYAXUdcrk5OQggMuw+2gWrRgApKEAlA6zQMJlePP'
        b'Gqa9JOPMuPxPM3O+UKferQdX61srzg/6uky+p/Fg68Hmg8NrJ2yWb762+eiuxrJr5Y1lzUEh8D5DfZomWZGsQION2bx8LLI+kpVwFziB9JdCejpq9oJziAU9DnGXcfZ0'
        b'G0sy2hJ+tIMlNMf4Ck0yV3av3l9bH9fo4ex73UbvgX/vozcMj95OZC6dI+MHrmg6hpChBoDrHFJbt4P6J4gf2k65iZ//gLqd1XcmF0GSNQTdg0vgjtZJ3rBO1JXCefpu'
        b'HbbQAMW+tDkcFRl/5EO3N1sWuWfI5sayyEORmz1iRm24/7p6m2DYy3vpNIr6plTSb3ydXGDB4jt49Ej0RvHbRHrFNno62AgaiCI1FynpVURfSVIok4i8QkrzfqoPaGOR'
        b'knNynAU3ipTWm/AiMZJUypCQOKUKbElGw1sXFgvOIvP4bAiv5qSmizNHgc0WzLnCQaOSV4Qc+Rx5guFODhwER8FG2Aj2E8k5AOyTkspdnQdbgiU487BnBYO0fR8nOb2s'
        b'Rm2WxmDU69L1a7TuKs9IhGy00PFvGuIsJkfCFOXsRduhTUNdaIeLnHBDuz8+Rphij5UGybMm9CqR8RKDWFRNfKK3B0I9xLWE1PBiQXIurOuEGk6sw0qSk1ETO9zFqH+J'
        b'4tMN8ziqJ8VHnJSDWd+hbA+xrrBFTEe/um6/+f6yFSujnhs6h6OIKSFA5t8BuA2pbcpYRCuXUAo8QoNL8DBoIT63y8F/i4wYHPIMM+9D+qfUuVFS3ldWMYJiKNtVMZWv'
        b'mXZYvYZPbJ7sRw3z/wp1Vr1sUUIGZTBveJ02G9GTF73Gxmt0miZ9k/6hOl9ToWzSf64+pflcbcwMXdCsSUNI3lbfJ/Qlsb/nKQ1zaluz/pzmjCZA9DnztnSoeuLm+3RM'
        b'/+B+f303ot+31It7F6QODGxpTvamX21pH/3uqH5C+nejhKPzMQtbPuhegg0xN6wjgBMW2BYPnZ4kMahnRo3KKwKbeuZCTxQpXJbGnEXQTsajXSTWsiXkn9e4pQxHS/k7'
        b'2vRsBxryMqIDDXtun+azEYTEhVvcEPLtx0gRrN2lgqZYZKAqQL0RbkHI0I8Gx/sVPsGXTnfxpT897+umeuNh8eiGgdIkK06AJ5CpU4O9fTuR3RNOhXMrCb68OpSj0Pe8'
        b'gmR1wjsGjkei97JZjMtrxjDqnMXaSMqENcCeLu10uuHuwumMuQr9KDlGK1+P9AYRvrPe2nvp4Av+737CvDtB0D9mQ9OSg1mL5Rtn0YbopNnaAsm/Trw/tP3jfpMefV2y'
        b'417QlMUHCqalKpbptr23tWn1howXSkvvn5EmLG7eNjuxrmJ/0YHP7/gvy3731GsLcqL+8JtzwUVW/T/Ot30++vD/LPhym8/rw3Ytj1Z/8nLLd3P++UA04fSzvt6/k3ta'
        b'MF9R2kBNCahwGAldzVZwCjYT5z88Du2g3KyQy2FVQqgyEt6OtToEWOhzAnAH3lYRazMPZayCF5OiwRVw1uLI4QVL2TGwAe6wYFJevmQpbm0KnjLobJGoWAvGEdCUpwpT'
        b'wQpYqcjOpikh2MIop4+3YDGqh20SwpYVEljWo2U8zUAmIeBxLdgQBuq947CrKyFJQHmCVgYejIF2C/GsXkUG0eFs2BimilWEylWwDun7FBUo41aECElPApbDW6ipCwuw'
        b'vKjBqi5uhBjXl+N8iN0MToOTYDsyv2LghagO8ysO3rJg+2cAOAjLwmBZXpIyFg0cQ0nFrLgYbOzE3R9jMQvzrRk5Bl6AKHhKnsUgzdAX0a2Q9ieihPuZY7ifOJb7keO4'
        b'fwsFQkTjUkzVw1119e+xmSAXCeOc0I2E7zzGeCbO+ptgB7SHIXy4FZKIXnZlgpASwxYGlIrhKdKkVuhGcX7oI3ZSXAiLrSQbHUSVCCtENmEFVcaUiGwic0Kxt41toGzC'
        b'RrpEvIQy+nGUhS6KoknbSyljQASyA2xiXM4mxDVMpnQ0Lmn6ySbIX2ygSgQ2QQPTSM2ilu9ZxpR4lEhw/TaPMsakJi1x6K7JJmxgG0kdDRzJG1jiWcGifJ42JpM1UDbJ'
        b'MXoLTVMFNcZZpJQUwSet8LAJy2gEsaRCjO/KaFJSTEqKu5R8ySY1PayQ8iWcsKL0RwXqesY4jNTqWcbU06YRFXQFVUjhOwSPQMc00nzuetr4b5KPtggzGZJ3XoWnI++8'
        b'CgbX7cr5NskpJLkKKwSOXOiuU64zOrZBpON0gk1UBep3GY3G2UsnbBDZvBrEOpFO3MjgFJsXKntK52HzCqBKvOwiuydSOlmdBJUT21hcrsQbjYF3Ga0Tr8Itvm/z1nmi'
        b't+JtHOpK51D633VS3KLNu5EOwE85nVeJt42pZ0zRCF6awMuYBuu8bahEf8S4MxmUz8cos9E2ZhWLnkXpfPC9I12s87Xxd0Pdyqfp+vDlXXlwaz42H53fOPzthfJU2LzJ'
        b'1UfX1+Zt88L14WdGb5sPfpK/zeaFf1v4d+yLeuGLeuGPesGYvrP54t7p+qExZUwv8L9QmQ/QndiV/kf+F05HveyjC0C/KV3/zUwQZetD4PdFrQdWeOEWsiU2XycMNrae'
        b'NQVbaJtPGb2RNootnvydQ3QFJS18JMrRWAxGZeQjRiHrJCUZh6QkzgesT69EhLVcUkLb6GxqK1PA4Sp4sU63i9PTjZpcfXq6nGlnVBHttKWrX0IyOcdgtmjzcvOnMqgZ'
        b'ExbAxQO1WXrtKmRZdhifHdkesbI80yNa8QBD9UiSlymzFOXrZcPN3cAUOKlf5gQzAE/d27AgZ8xcBQK5jO4EslO7lhPxWfgYJmnCc9lCJ8QmLNEf+WhkhZocq16GYAoZ'
        b'bpYTKfwo0KwvsOqNWr3MYNHnyoYb8OORw80jH/UhCfjWlcSRa1+3nM7SjzxkuVazRZahlz3y0RssWXoT6jMaCnR9wOvuj+iRj+ihjzyGm59TqVTLUTpWbx/1UchW5lmc'
        b'ozQRfeTSdoHBqNOvaZcsxgDPxsYpSkKtmts5bV5+UTu3Sl+E7HvUcp5O3+6RUWTRa0wmDXqQnWcwtgtN5vwcg6WdM+nzTSZsv7V7LEQNkJrkfu0e2jyjBZsipnYW1dTO'
        b'YTRoF5LhMbcLMCzmdrHZmsHfCcgDnGCwaDJy9O20oZ1Fj9qFZj4DvapdbDCnW6z56CFnMVtM7VwhvrK55pWoOAajXVBgzbPo5V69m+VPeUGaZqILQ8VOZHwPo1I5QS6s'
        b'1XI0lolSWshifZZD/2IkIXldV0oHMhLyO4Cko/xMAO1HB5MUX6E/uhei1ADig0aSlcEyVYpS0S8GS1JvhteS/Rhv4qkOpP1/Ri3+zDD+qBSStowVS9L1sBRuxEZWItyS'
        b'o0tSxCGFJp2dMCm/0zQHFoNCJzF8jC5IbDE2qoEiougNJLbYEs7GmoMLpBak2+KPAYm5AywWbjbGxk5GRGOahwQhXUihbyQygqgGBrFJNohqRMIHCSQOiQAOCw2zzsat'
        b'pFF9HKp7HhJeLBYoSAjuQ6SHRYNAh+sT6DhUB4t/oW8kFHE9BVm8kDGd0HH5TTosogU2EWlL6Hgu4Fsn9TCTKfKbc/zmJlMFUhtDmJggCVEvdsHxrzIJXxJcdzhNLjBF'
        b'4xfMmvWWdlaj07ULrfk6jUVvmoGfittFGPdyNfntYp0+U2PNsSCUxUk6g9ZiindW2C7Wr8nXay16nSkZp8XhwsInYJmbfxiHmejSnfWGIJZiHkGQjEPIgpHMl0cEhARC'
        b'Yk5h5PKl8b8fTSZ4wa71ckcMA6gMB80KhA2VCdPEKpoKA1cEcBe4BrpPfOPWscZKWus27U3hie9MT6fpY6OdRk1Xi8mlYunQpQK/aboSifpsKt8XYRkqaBqDMMMLpdBY'
        b'gJbRnsj0ISIK4QQSfHQFW+GJ7yuxJ5lDgODmJQgcaabY5aT1sDEYh3qy7TFi4zElPt7vMBCcDesLVPEp1DCL74netBChPIMaQ6CV0asoBBa6syFASlhjAAFPiJB7Dr5D'
        b'KRxCthwbS9ICKrA+g8gA61sVQoz0Dp0rwIZrnlrC2ki9KG9VhRAhK4t0Gs4oxfconfyycaZ8LHEQEZF6bJyjjnykdUYgrZOzCDKZoo9ppFHSVLE/GiwBlskkyA2lrRMY'
        b'Jfw3DnJDZIJI1EbjOohnmk5COIe15HZRocZEnLPsSoTXiLOaVq02TcP4FsNjZoc/dj6+EETOIISgN5nk4qfmlB04LE0nPDIfNZxrjndhMMJWhvElTBIxQwYzwmDCOqWM'
        b'FGF2MMLfwXRxhEar1edbzB2yXqfX5pk0ls6+544GkHxW46ZxPxCNk6AqkpCFEzx/Lc9n20V42BAp81VqXN3zcAE0A/fNm6A+LwIGI0YcHFQc3HsfnCpFOq4uG99LfpVA'
        b'SneBI3I0No12uBIoVvYsmV40q1bHJyQlKUPkQgq0wl2eKgYeywru5oSVOL7Naeiip9KQ4pfGEAYgcno70tgdHrz/A1GjZ6aARG2Ky+g0zpXOMwtMq9JMDxLNiZ8L7BRH'
        b'pQkJpYra+zjiLucYcvQJeRqd3tT7/Dtx+zGoWsSN3OZn2Keen3lKhzOXZB2N7vNhOdxjBmdDYhJVsYnzsdmfnBCrXAArklNCMBMFF0ADCR0CG2GTx1JwLcBw5aO/MwTO'
        b'sYVnvlA/VH+uzsoM3RVCYhjv8TGMGQ/Vb2Sk3f3j8ztebKvfupVuKp9waPjmIeyIPRsuCqjRr3tumjxQLiC+3jF58AK8CGuUsCI8tAD7LMABZThDBVs5UA5LC/hp9Ga4'
        b'Bxx1Td3zPoeFRuK3GJ1CfA6LomKd0+z8HHuJicyyT4T7iD8AHoI3Zzim2ckUO2ybDTYFJlvmUtjBuRkcAdWrXSFWJC4sFgd7gVp+SEAVbjwcViXAOliDA+0qYR3i43g6'
        b'e68XbISb4B3HvNATGAWyBwxGgyU93X3eaT3KhvQdb7o4uBu2qJwFXPNOZn1OZrswhzx9zLwTorg8fG90tm3KRZcC2umcLEX/W3v3GT4OlN4xeAaPwSwiDCxRhZlCFxZz'
        b'vx6Le54UFSXxkXp74O7cjvg4WM9SfvCgNzjF+i6dZY1AOaLzwFk8w0xic0lGNpCE0iGMd7jdLi2gqGUhIrgDngK7SXQv2Lt8CF8oJARWhccoEW42LwyJS4R1ClUs3JKu'
        b'jEukKaOPxxR4HZ4jWog/uOiRolwcmREDa+RxiQkov4OmUM4xYJdwGCxfYBjVJOTM2HaMvx37hfqVjCZ9kyb17h48hZN6YpN8c3P59AONe1srW8uaU9l7K4WtqwInpr4W'
        b'WJVTatsVLIxssXmYRTNF5tHvMC/8zy7vXZtrnpceMFB/XeP35dSvEVlhdB8Odo+B1fEkBpMbDJuMNDgCr4BW4n8DpybAc2Eq0OrT1f3mB68TqgRtkWBPB1n6xziciTxV'
        b'Hp1rIYEcjcyYMNAC96qUMUqGEoJjTMR8uIVUELI4M14Vl6iAh8CxWERDTu+mgBo+V5AmLXBOHz69juilNemRXpqem6ez5ugJ7fg7aWct8bwxnMOrXvxMd8TtVNpJqJgw'
        b'EDVhcddBRb3PaCJ6IqRU4KKnfHRZ04meqgJ6p6cngdWNqDydGJ/gJCp35ZTupJ7+EvLq5pnHjbmMIxd5eSeRWLpgqxchriWrXORFaAuc8ydCJApcBpcJocDd8LCLwnql'
        b'r8PwihW7VH21cEPv9IWJK2sBIS8jOPj42A9dp9gPOd1OZ3b1sYgn52hyM3SaqXVOf4V1CUb0rbAMVJkJwLBuZCfeT/g+3BYPzsYkgi0uFIY7O028s6P8zGD7Aj94lgJn'
        b'YHkfgIzRyXxg9rYpkbzMWhQBa2C1whH7tYCNBPWwtVOXsJsGWxFEgZ9Dkbk/bAcI0Fsn79tlB7BEGeDQe2bJe+bIu2XXcSlu972xUYZyM1bc5gCteHGHRu8Tj6crVXxE'
        b'RUpMGA4CXYQ4gFIOtyTELnK9zAx4QUCBBr0E3pbDjWRG5liyiJJS3+SKZeqEz3NmIlohyX/yE1O+VENfTq2W5qkn87M3DbOfoSZTIVqvCLXt7yGzKMKiYV2Bb6fmcQg9'
        b'ej2HwpFa4gzMQVw0d71HIBroO9ZICgdWVkyOx8F8NUh7CYGVS3huO98F6SKKGgEvLYOtIngebIe1hmVf+QrMG1DRuvJPptRESkC0/6yVP3014n3PbS+NXtPf8+j3AY9Y'
        b'+QzJzmOR4pQiic/nJ7Y2Zw7+26H+e2c2e8JC3V9A/xcbF837ctfWL3O9TJ+15JeH+gyekpj14e9e/+uPVypffCtg7rJBI7/7V0Xruj9WjtUnx00687Dmg/avves9xoWs'
        b'++GjPvu/8DlfM3hN+Qi5mMwB6ZPh5R4mgOAWcBVPAk0GxwlDhXWgObizohQOTo10sOSJMWSiSBsNzmvBmbB4pSM2HFTz2kq1iBqSIvCDe1aT8JlEejbhzm6cWZbk4M3w'
        b'tg/JA8/C7escE/bJDqBGwqte8AIb2A8eInqZTAhK4xGk/KT+kBFhKqR0+61jkXa0E7aSLPAc3IbDl7c4KhJQnuOYFMQDcADTRl7YXDCAc45gHi80EOT1O6N5EKPpNGXz'
        b'a0wzbxy0k55vyrMQFwWRHQOdsmM9NZAh/ipOHED7Mn5kBsePLh7bnVnr1+i1DlbdYeR0rptnQALeeuowMjukyxMEnnMa2NtVlMgZC7rsxXJmqFPOlFIPgnufKnoO5Vo+'
        b'c7y5u0L7GKY2BRzqFFDEgm0TYKtgNrwWDS4NB81yaijc6Z8tgOdyMKhB8wO57/yo6G/6Fg3JGHk5MqXfpxSJBsjI20u3iChZRNCWAd+b9liO8MlzxX/12eFDh3xDPTPp'
        b'74EnTMcow5XXYgTmk5jbveo7POGGF4jwt60c2TooZehbEZS2hWU3ffzTOTmze9iRqgEDX6krD/KrnF4wy/pz3wGfJc7wDAwr/3NTqsegkI8EkbA561bBuauHYnNOvhwn'
        b'UzUfD7jBvHgju6BRvvcHbcvBP3v9YeTgKe9svvCG1ThKv/sPtzWw8HKroqwuZO20tzYNXr0tzgb6PzNr7FcvDGv5Q98roqrrlh17Yi9OSzm/jcn97Vd/Zwf+VvnwM43c'
        b'iwTJpIMdcDNPs+AQ2N55HhVcAdVkqhWWZUQ7JjjBbpubkuUBKnm83zonyUHR4OxQJ1E7lazGeRbsXoenwUVwnKdD58sEFei9VSaDY1MSeJESpRMu75NNlLLhcOe4MBVs'
        b'g3s7lDK4QcgvIrPDE/Am/+pPwQ1ur19ADRjLgeqMKMts3ObGPlHdrKFEsNeFP08yhsBusI2PXr6DlM6zDvaGi8KDHCktovrBDSwC8zS8xs8JbwAnHCFFPpQK4yYZ0EVs'
        b'iAlxErJo4XTfGfyyllglM9dMicFxZk0f1BAebEkJ5AcJnJjqMgGJATg+irAzcGpyEg/HEHCtizSG9pEWEoLQYkyD1QmIjMZTs5bBLTp4vJcojF/tYKH50AQ+Ks6NnxCe'
        b'FNrBkzxcGi0jwS5Q7DJicLRcQH8huvozvnTxoMdyqE46rtCR1sGHPH4Z3IypkOpkSVrRZXMXjvSjrHfd9/HAykX8/Ikk3ZGQnt4uTU8vsGpy+LkzYrkSdZu03O6FVxlq'
        b'zGatHnFfh2Es/U+mO5rpdg9Hnag+0sUcdMmjHdGKYsZXxNABUsRcMaQlxkWIuYLS9B75K0NNBLeEYG9xVDdXjHN2nrxsp9tJz+o4ZxhxJqdjdOwmD+xmIm4kAVHkBC43'
        b'0jyNBY2iEY1gkpbrUrPLCp+FmSpvLDj82pkihwLJVYiQAilACiRHFEgBURq5daidjvveDAWss7qmFN3DF7GsGgnqM0AF2NnZFOdthdaxcoZExc0EF8AJRw5oBydJLqQf'
        b'wEqOCp7FxQhAKVmHxSLmut+Z7wY8S/KFhcYIqWAzt2hmoGHowB8ocyzKuaDPG1+ol/IhkPdObWotay27ttdAp4jiRatEf5jxl7Ty4PKhF713+YcfOjFqjszrE33kuNG/'
        b'j3hh9HsR3OhjVOTKidQEte/iKx/JORJZAm/MHBSmMgd3NY6zk0k4bNRA3zBs8apBmYO/ZiCOT3hYKbgaR0COB5VkqR8VluanZ8GZ50AbqXodvIXsasTEkAnRxmMKYWOa'
        b'TKdBLPplqo1HJsKEdGzBEg7i18FBpkqk/jTHihlkDw/ohjoqVzmedoTtrDbH3C7OtOYQimvn8lHedqFFY1qptzwxKo0zrcP36/GlFF82uBhFCbrc6MIoXg7snVE8DlY5'
        b'k4Rd/JgATavxZQ0eA09Ctbl6S1aejjRnKnIOUvfJ62IXYDZ0ueZ0H4sZB2GHpdgwYe8scGCwuNMyUWoSUnlPgjawhxgyH8Sz1LtTcEPqnNmpOVQ3W6szPXaaYXLRI0WC'
        b'Op9u0WOPEz/dQ+qCkohJFbGSMSMFo82zwApPIZPoMlIcriBpWggveRaCWp98KWylqCnwhAC2gK3gkhUH/ME7EStRocqEJFgblrSI2PKx6KsyWbkYm2Rw++zw+THgLKxQ'
        b'qEDrAuIbbgPXJfDOIvMTl+WzJKLlvxDMSvXGhzDrWA4OF4WBpgSeeSD96VIijnfsu5AlpFdnJTG9gX7oPW+H+5xdhTvDQHMITQWDrZwJHoP1htzbItqMZ0n//a3wC/Wr'
        b'n36uTrvbUt+4vbms+V5zWWR1AV1/qb7PPVHr3kl7FgSm7AnweWFU2SeTAl8NrH44MTCgpXRhxChLhGD0McRn8k+w1Nv3/XY1bnR46EBj8HJkL5FlhkJwhgE3AkfD22AL'
        b'0eLGKcGlsBjCeTikUO4cR4NzC6BDrzw+OYD3tlQpSZZVMykfsIHNBg2LiCscHIZVeLkhtt7x+lYub9UEGrTCA2AXH/J6PHcW4lJgk8J93VJ/cPWJy8g8Nfn5ekSLmDd0'
        b'9sCtp7R4OktKJmoldHEo4hrpOQat3mjWp2ea8nLTMw3uVpNbRc5WCd94jDOb5nMQ2i1Dl4+6MJXGx4TOzcP0CJr7xScrsarqfOWgNpn4ONA3L793dllTEc8PEeLm/MvQ'
        b'IRPpKmjyzQVnppI1rxPBNXAsDI/zaGgfFMVQAniIBm0KcJC4gBRgG9JwL8LW1YWwrUAqzi+Ap8dICzgqYBK7MiWcX53QNhyxnDbY6uFV6CXxFsMLqzHRFgioYX6+yVwJ'
        b'3AXaSJzD4DnWeCST+JcqRqbxVREDyoPAceskXA2SkeAMOA23IxqvTCiRhcYpkJa/Y7UiBDtFEvg1VbAuRcxvShBKU+AYuOg5c+BKK17igEyOY9MdhXsoCvb161p6V44E'
        b'bg4FdsI34ZUYBlTnF4C61fAyvIL4jgUp21dgC7xiRT1JkQZwYAO4uMzqWK65CaEjhnU3Fv11CB0TREuUlA/cyi6A22Za5WRsrw/vVuVq2CqVCKlhseAq2M2BKrgdbCY6'
        b'NVksDC7qMsFFhJqT0GuuQddL4DI/RbDZH5yE25OVsWg4z8fEiijpFBxLycBD2kHElTTGLPBUYq9J/BK+027sD1wifG453ACPgosicBMBXm7FC1JAfT9wPgW1Pyx+NTUM'
        b'VA8jcmF8fzG1YwXSdtRqqWeChPd6/bBMRI1ZMhjvHKEwm2inhywon6V2qDGGq6XrlZF8XpuXiKr3HYDzSgOGFVLWsbitBoQlZ7DFGIZdXpXEzVUJjs7vCdY8UCouyQWH'
        b'DLfvR3Lm2YhWroW/nDivNQkiG/u3SW+fSPT0b/pwpG+OtF/fDPWpF0oD3z/U9G7c1n1xCeHxKc2ZG9ZtvCW7XRquyfh49MS/PjyxSH//2jt/uvHPyRvHRbwSqPCbqNjQ'
        b'eLXvuTOZ30z+8N6f79+dFTXixTf7l9dfkb6/iV1xarhie//EfUdmX5z1TuC4kENNGW+knhzpHVbw1Rot/NvkNfs//lG670Ji3JUV2YLf/mg8dWv3xwfvl7+Xbb+edH+H'
        b'98APgHlEbv3zX7yT/srE77K446Nkn/9r3ZUM5Z/SLG1fZmZM+0fB4uzfX/6yoWbwBtm2RYZryV9LFo+/cY2TfhEbNTfKPPUfR2omXB60d+vXkurGPmyL6vuBEtXi8YMu'
        b'bFtS/WP6ZM+Te8/VZi4aMih5xz9vp771yoT3390wl713ftWP3y3694u/fePL+4eThzX1vfO312Xfl2yXfHrvc/rtF6fN+G3Rmx8NkfPBx+n6gfF4M5ZqBawSRWJvlSe8'
        b'wDJB4AZZXgNuzgSIa+yDB/hFNvR081rC18GNbFALtqU6eTvm6+CCD8+Wb4L63PiEUFWMYhC4hR975jDwWO4Sfq1p49QhZDMK/I7xDGb1YHiAKRk6n58g3T8LHghLRtDg'
        b'52DbiHgRgug2gwhwH6whICfAPeBIvBvLDwLbmCJwBFYQoZEAD08KgxWxilgiWQSUz2QVQFaDFnWJENBlZJHvjcdTxYhE5MokpAz1T5gJDnLR/YoIhM+B82AnHzoOToFd'
        b'Ckfw+LJlpOdDpsGGTHiTKFLYHckpaXA2QU40asS4DhaAg8VhcYnI+OaG0OCgfCJxjsL9xRpHNDrmy6gsQu3+4DIoA1e4GNgG7hBZOh5cMRFZqgXHHeJ0NDjt0MqNJnC2'
        b'a6A5aIM7uBV9wK0n+uOeRh/vZNX361HyEWm5oENaLsWykiO+Rl9GwvhK0Ifxo/FVwvqitEBXuIiUxMeFkDUjfqiMN0r3ZnAoFI6ZkzKmTU4h3cy4yc9fZkiQSt7rIlFP'
        b'966mE5aZgJcAdYjUqWBfj1JVQK2wiMHOaHhYzpKdDZLh0eVkchLRwh0yQUmDI5HwCD9rcgZx6FJYnYTQg3cYwxaFJ7jEwOPgNqjgl5AfNoGTYQgHQ4Wo5WvohTcwo6fO'
        b'1rJdtMP+lFtcVrcdTSjXniZ0l11NGHtAZn/XfIvgqeZbWLInCffRKdSwROb2t0C/0mC26E1mmSVL33UPLpWkU95Yi8xglpn0BVaDSa+TWfJk2L2MCqJUvM0SXj0ty8Nx'
        b'tBn6zDyTXqYxFsnM1gzeadKpKq3GiONkDbn5eSaLXqeSLTEgA8lqkZEAXYNO5sBRApWzbvTAUoRA6FSTSW+2mAzYu90F2iVZeiMB0GBc2QXG1c7GTCutuXqjxawg7Tja'
        b'7FSLwYh6kqtxFEO9RVCb9BqdDBMPKaU3FhpMeUZcD4LdZMDRsZ1BnBObtHD2zJj0hNiZs5NSZqcnTU+creiWGj976czkWbPRoOkeW3pRyuwFKTiqWJOD3psRgVaozyni'
        b'4dG4xg2TdZdxytSbcJiyTpZR1K3SedMXxpA6SUGZplBjyMEd6VSFxoLeLomdJm8lLycnbzUeXKw24wEyy0JCjfrVMrMB40DhONWEUPnEzi9lkdGwpkuSUjYsddbc9JnJ'
        b'SXNi56bHJCfODs8vcmz1Fe7ojsqyxtKl0LpwlTbPmGlY+VS53ZuYFbsg5akKhest2vA1ut5a6JQ7UaNNTunWs3XhCYYMk8ZUFD49Px+V5fEoxZqP0f7pYPjlFXSmAoNR'
        b'l7fa3A2y4QnJM6cnTJ83b9b0hdOHPxUow6cnJBDkm7cgeU5swuzeSnUqNpFEBMqw12aiDO/2h++cKOQohfhMD0VW6YtwZDtfyvGjS0GdrBBxLjQiPVZgNaOHfHFX/tkz'
        b'YmemkCcygw7h60K9Iceoz8rVm5Sxs8zyzvXgP8TznEH9GhnmNAjfCZ3g1Q4YHGddKllSHuIo/FvqSjn4z5DpRp6IG2VoMEDobSIOadaaDPmWbh3p5tz0pnqIghiH7n2R'
        b'UlOTEu6MTliwJAYZiSkxcYIFEyaAZrkEXiuagITc0An9KFgPm6QqeDBIBm93k0m+zgYWd5ZJlEMq0S6pxNh9Mn1/xax/ty0asJQP7tYvZRLKRzSA7gHN3aO5HL5kVzTX'
        b'f7QHC26u+1JkgWPrDqxLGT7q35c2m9Bd7Jn9X6iVf4nRSDM/Uz9Q52Y+VMdquK0PpL+pMSTopbPTBtXIvk36/eTL3r+3yP70/LvPU36GTIum4nenBV+c1tTrqC/02ZkK'
        b'vaIqQ0ftFwek323xff2C5uK4kLYH6uV3r9Zv2NpYFqSbEcGuFFKHlg36KW2EnOF19f2gGdwOU4aQeTQN2AX2MUozzYc+VYCKJWFwS/hqeBCZwpyVRkrv4dRfHtUkSF9t'
        b'0uQT7XBwh3a4nkrGaymQDohUL1/anxYizU9MF8tNDl3CLSjYyRc6UnCNjn1i+Gj8p559bqb5AkQjtGMND0FmHtahEZZSl3uPb7LioNBVaNguhhEqUQ9Q4anmbttUdPhf'
        b'ZvvJw+OQwj4HNPkY4F5Q9YTAWJa4UP9LG5cIqJ5ciKIk60x0P2718NERY0ZFRY4dDa5MgidAi8ViKiywmolLow1egJdhK44P9RFLJd4eXp6gDlSAGoYCx+AVD2TQ7J9M'
        b'DHmFTxy1g6LE7/ipQ6XeE3nrflheLFVPUTGfZKpDLxnnOzC+daGdNS9Hd9/He/V7eYhfaYSUu/vJ5BtjhNX07Y3R37KKq2/I5jX0XTTr8Fs/7ThSGPV2Adg7c9frw8K2'
        b'FPXv7xM0Yv62MfBrask7gaqSXSdqfl6qjjg4L/aPJe/O0P5v+Vc/Ulehf1l9nmPror4IX3d2WIMF8dgFiFT2FmIrxoMacMPNgTiBhtsGgtYU0PC46LgnB76a8izpGaOj'
        b'CLoHuqP7cozufgjRxWTBULHiqRDdUZ1zptO18uTxIbEkRweaV6FLWjc0b3rMUvrpKN/8HCeWd8dxGTzeDc1xtE5l8qgolioE1b6q+BSCCCtHsdxzDNlhNOHFYA/Kiudv'
        b'loEmIdyOMFNFwfJVKg94lOSlhwgDf2QCycajtX2VPCZ9XCJY18764i1yFZSkiMck8mRhntj3LCvDLigFqxvBJ26QxAfqmBCa8lXH/Zy0lE/8tqiP9E9sNEXlqxXXJ0+k'
        b'+HXGu0ELvJICa+GORWMHg4oIWMVRwgU0OJMLd5NijyYMWPACm4UEmnrZNzFD+bo+LWilS5EA+WZtwao96nt64rcUghOgLQXgqobAm3ijO1ZNTwVXs8nWNhPBkaHYLe90'
        b'YoErXuBsCKxQxOH5BuxwINFcsC4Mm+6gMkwiB1dUJKJEN01INQ0Yj/dclt5PrZuso8heFn0WjRSLl1IRJ4ZfK9g1YHzIysXaqAUjfhaRbQbSwbkZ8CISQInUYlibiKzN'
        b'ywTyLTmT8jOoz3B3FqjzHZu9Dhk+DW9tFhJtWGoJ7Hd2Mb8t8fppjJX9J0VFqE214w18zpEjFLSaoXzvGrKtgak+/iTx6uj36DaWirk7d8aa91eZZpPEVTPm0jsYKvru'
        b'2EHr3n+2MIQfTF0/OgIh4d2kaUWBXg+m8CAxVuob9B296mN96mqFlCQ+q13o8Sk1T0D5auID0zL51hcv3kqHsFTE3ZmDsgMn9xtCEuP9l1JXUX+iB9F5qflRaSSRzX2W'
        b'Rkx9/F0VUL+/xMLX+d6MZ6hZuJvGFRmBM+IySWJ2eALdgHs03FIY2O8NvvhoccC0YDaVQ0g4ZfbaVL71sqVv6UuZaBGl1oR/m6nmE9mCF3QzaF8WYabHV5nRjvFMKIk+'
        b'xXxDU/PUix955vCJH3r8aUwklc+ixKVnzRP4RNl6qc4bsW6UKJ00TMcnilbkU6Xo1eUX9NMtXPTDDINcY6XNR1HK81/cXDT/NeO70b4PD9mfuX9m9ZAPX3xtko+4YubU'
        b'Uu3t0iky3z/G7YdxYa1/8RtjHnVvu+dfI+fu9/l41fhniwdu2jTnnT8tOtf8YLD95iFR2I2mTz/sd+ndEbntSe0/Fl5Pami4kzn1womDZ8dKz6i/+udrl47Wj7PttA+M'
        b'nb3k2ocz8ofcj7v8/JzbI4/BiuI5US1LWoPvrXolWzbi5XFxlT8EXqwKeLfp3u0RD78/MnBQjbb/fY/P9p+ateHHOZXpn8wue7D+ZmHw/W0ZithXSj7g3spNePn7Zd/d'
        b'bEwVzLkwf9zOF/wq3/uDT8gnf8yJ3RN+BJ4Z9oln2ukFtgPjHxZO/z6z4YOPd72uO1gYdf3hB/Yzyflr1Xtf++lW7qR1x9eEXrffUh977kEf0dV3sg5ztTdCWu9OWZj6'
        b'8dTBHw4Z/FHk9+mHPpR7FwzbPmjS5r5FD1a+/Rvzyvzi+Zs/Ft1p/PqTd96f/2Pft//wXPvgAY8OFNp+qJarvj0U9TDllfBhI7/OOv1GSMI3Fz4yP0r9pyJr95zZLx9e'
        b'd+OF4wP+1Pzod6lv3XnVkr1amPZWxY4G8w/9/xq36taRe5/2X0+NH1CXtuCKXEw0p3y4KZ336A0Dm50+wmdn8lrVDsQkNofBinA8W9M4X03Pg6fBQfIsChwKCItTxith'
        b'rTo0SUBJhQy8Fc6SZ3Nhqy+sHjHITV6B1vHPEd/inLDRiHEkx4LWEeAMhzc6HZoTyO9SUQVu+Yap5HFhjr2KfWApWxKTB1tpfhptT3q2w6UqQxp9jculujSdD5BsyJti'
        b'HprhvgmZawuyi+D8L42w8f1PoleeKHkdwpNI3gx3yRsvxUFF3r4SjnbfEhJ/D0bfgejfjx6GBOFApIR6k6W9OKzAjw5A35KfGIb5ScwKSSkxWeUmReU4PAUY3LsM57VT'
        b'AVl21y5yWJ7tAmJOugnv/3wRM9KA8faH/Pq+LS6ZX42RppvMvxHau8zH8dE5sNy3N5nfWeAHhggoYAdIEbwJSn2seMusHHa6ay6+yzy8EGmSV8ywzSqgpiDpCI+Blgwy'
        b'4QM3wDu5vZWCV9DFAi+vLhBQ87NBWR8htINj4A5ZuiKGF2O7FgT7Rrpm/vFMo5CaVSBcBG+DvWQTRlCmG0MmzF1zSy4PLDi+nAoHbQJ4JnoOmWAfA09nd8QIkNB+X7gZ'
        b'XAa32cHgGqgg3Pr0ErJHT2qil1o6yyuLZ+EnAwU4AF3cMkudUL1kGp/4fS6OHaeom2HqnE8y8yhD+45/UObbKCUW5ii3TPIGEdLyL0/UjcldI3rBOp45E7Nz3rsbmkNr'
        b'7kbXP1xWGnTupdiIfjD8h399f3/U/ttTy14uXf2JfPixkOMHJKHNR/a9NKZxgjLrftrhNd+/SZ+/e/kP33xWcf6Fk3k1u6xXfjSPOHPfap/2Kdjy5QOQ9vGwpaW3qqI+'
        b'/0xlqnzRO3TfgJYJU4JskbYFd3a8N1n759fGcsueHzD/4U8wbVRbTWLov97Xmdj9B8Ie/Oa3AaHfKnXnhHPXvj/9/jra8mjqWist9yBBkGhUT4Jm9937Qwej99exez8y'
        b'mQ4RliNFWLURTywtDSdTS66JpfTnLHi2cU10cTw4Ee6cVBpk5qeG9sHzxW4TK3q4mQZn4eWh/OZBR8CR1Qg5L651n/eGdQk40uEQlwePpfHsrB5UjHVHYsQR/ULpABY0'
        b'gQZwiUyl6J5bjHPoQH2Hd94bnGNnwUa4i9+Vp0yLKqoO95Uqk5SwKkEupHwGsukxsJwMRRA4B3C0+yG4K9mh5SmcrHMA2MqBo/CWwmlF9/+vc8RfxjSd/IswzQh3pjkH'
        b'x2Uy9Ig5ZAk6IyVsj8G7HDABZHGvkDBLEzLyKIdTowb3yP//lS7Uufgcbj+oG597ML53Pkd2jt6cDU7zjA5UwTYVjnvyiWIz4UZ4tscgHPxnltId8Yw6Oo3VMWmcjk0T'
        b'6Lg0IfqI0Ee8kkrzQN+SHewOTieopckGdzgWitMJdSKydNZTL9WJdR6bKJ1E51nLpHmh31Ly24v89ka/vclvH/LbB/32Jb/7kN++qEYywYPq9NP13SRO6+NqjXa15q/r'
        b'R1rzQ8/E+F8XUIv3RMV7DPfXBZJnfXt4FqQLJs/8Hb8H6AaiFvo5fg3SDUa/AnQccTc80+6dwIu7RI1Rs1Jv+kjEdJkawo7TznlkJJatU6YnlTCYsYeUTBbpioyaXAOe'
        b'kSmSaXQ67EY16XPzCvVuXtnOlaNCKJNrpsXpcnV5c0kJlWxejl5j1suMeRY8X6SxkMxWMz5EppMD1oyzyPRG7J4lsyCOTSNUjpktjdZiKNRYcMX5eUYy0aXHLRpzijr7'
        b'ZReZ+QkzDZ5CcvMuk1mm1ZoiklqoNxkyDSgVd9KCp2hQnXqNNquX6SvHKDhaVZHBtJg0RjOet9HJdBqLBgOZY8g1WPgBRd3sfa4qy6DN6jpdZzUaUOUIEoNOb7QYMosc'
        b'I4W0oE4VPRqUZbHkmyeGh2vyDarsvDyjwazS6cMd3v5HI5yPM9HLzNBoV3XPo9KuNCTh/YXyEcaszjPpeneeRVOOVeVkTa5rm+KnXVfOkgg87tHm7r57o8Fi0OQYivXo'
        b'3XZDTKPZojFqu85x4j/H/IETcn4KAf0wrDSicZw+L9b1qPt8wVPs5i1MIjoXqFaDtu4rDGEluOS+ypCsMRwFN5KgI3ATXoIX3BWhkBiFSgXr8DkDIaAsCuwWrgWXQI3j'
        b'JJF5fsPi4Q0k2BOSlXjlWm0yTfmBAyzcANpSDXPWedNmHHx272ECXukb8vEDdFUEPFDHaHIyX1+MV8qrFodo4jTMxaD+EasjwnXL7l6ob9x+rUxefansWllktXLztd3N'
        b'ZcMPTdk8hKye37i2z42Ee8iawoFUsHaUzE1mh4FDnWT7qlwitgfDUzNwLqfQHgl2OOT2bHCCF/574Rl43hP1WJ5ohRVrHCtR+gE7J4alRrIzoKQ/uBYGt8SM4Sh4aBIL'
        b'b9DGSeAC0UAGQfv8eH4IcGhJPVIZjjFgw0I9McHAtayBsDpeKcIHRoBNi+j4QHCZj4E8D7YvIXWOGstSomJGT8N9CfAYb9WtEJOuVSQmCCmGRdonDa9pNc4VVk8R04DX'
        b'DBDhHeAuvNdTM6RksyJsrxT374y0rgXuvNhu5tdPmPB+4U8Kgm5m+GydV9tfZZw7gZS6/l/tfb/iXuHpfQEsiRejsvkzUWjMETycdpa+mebB6bwY1mRGl5cRYPxOY12b'
        b'dK6UfRTU62wiaoTV5WmfCqhNPFDidIedZ9rXC0SvOiF65O82o+icmFQ9VWOZzsYwyzXozL029htXYwrcmFPX62ECU5tjQKxcaUYcXf50QDh67JmuX5NvMBFp0Sscb7rg'
        b'eBbD0VECi6OuA9+5eSeLJ7ueRFMdG7vbBW4s/ulnSLqdqNNp/zh35opbLAEbElNgLYd3rUZmrp0CdXAP2EfCMJG9cwRZxKcRtKvghRKqBG4sJuGyRYGwHFbHEp1/tETJ'
        b'IWZRzcTBU/C0IXP83zgzXrc47OHCQdWv9CmNkLLDRw40lL6UNYRN8PxddswK27LyP8lHhH/5MGts85ibNye8qVk4/oftC7MvfzL+RHPGNZFXyNp/a48rL08UTsqtzjj/'
        b'yoRVaXunfrat7//+QPn2D+L8pssl/Dq4JmSwn3K3dZxMcwIyhxHfTGSJMRM2DezGDuhYvD3wNXgB8TZ4gwGVC+fydtexDFjmmEOBd7SOOGoz2E64nsRzXOgsp2uJS6JB'
        b'Sx/YRsoVw92jQGu/TvMroBVeKuFXn+wEpeA2Bu5ZNc/7eM6nnkgKl4BGcB5eAVfj4ZZwfGAYF0WDmxPBVt78wifeHOK3OVkbIXCcJQIPgR18iOGmULDXudkx14/f7jhv'
        b'ErxKgghTQxbAreAgOcImxsnN/cBpFpb7grpOq3Cfatd3cbreqDUV5Vu6LrjF/0vwfkh+xNMkIUHj3Tmfo7T7Qran2yPZsd1+ByM+ii7v9MCIz/8SRuwA5/9Uy1rZo5Y1'
        b'M0tjXKnn48ecepGTM3TRuZDq9LTqFo4jekotq+dtAzjE5Mi6Lw9wEq8D71CBfAtcSpB9puE9o4QzY1k4Y5lHv5ohfmUR/oL/ee3neZ+fmiC4xSyJtpzKHlVRsS9t3p4l'
        b'86/+vXaG6Z3y+0svZrwoXfrRe5/svTBQIlki/qtuQN26/wWfeBb6+sxaox/9ccmNP4/2vnRo8mlJc7P9cnTC7nvp9XeuV3i894PPP7YHKH53VO7B7/tTCs7LHWoL1llC'
        b'wUUj0vGO8C7eirkpoDoZbzoATikMRSE05Q1rWX0c2MWv0K0FDZw7PcB9qAoHTQTAOtKCZ9gwUB2OVEua4sJpcAyeARfBdrifODw4sKfPKtjEbwEfnwxqwzu0yQjYIJwA'
        b'TsBrPKBbQRW4LUfE7VSV6Hg0rtsIXdvAVbAZj/BiWONUspCCNQLsJWVNxeAE7iM8M9uhSSE9SgNu853cBm7AAy5VClSvcHCUYUN/OU37aAkupjsRp+sqEPyfJSGO4BC6'
        b'eHAXGupS2OEa2d0rJZv2uEj4OLp80AMJH3sMCT+heTnbLszKM1sMunYPRCAWI9YY2oW85tD70kpC5pxrWaXAtaxS8FTLKlmipXAf4W3UulHddJ0OG1KYNN3UEN4QdSkB'
        b'vdI33xmeumPQfewsJ5fI0BhXdadxF1tw9J0vOY//iQqHxFuNyIxVxs7qIWzLLQTMWRIb7bhYp5AveU/wmvQWq8lonihTLzRZ9WocucXvhKNTyNRzNDlmPk2TgwNBi5BW'
        b'hJUzo+VXsSk2yTAsFfALuf6cMe8L9Yq7bz7//vPvPn+h/tqutB8ayxrLJlS37m1NP7WrtTyyurm8sW7IgQ2VQzZvEIj37w0K2hgkDapSSgMDn4/wq0gpzThgoBKSvaLm'
        b'r5ez/DzSjohpEqT6uPiIk4sobbzQvQB39+M5RCKs5ZnERVABm8mm6rAmHInkhFhQOWtmciKsSlCBLeEkul4OavDBC0dA0y8nU2+NTpeuzzBozUQRdj8Gw/lfhGm0eFAX'
        b'EulczmEECXlRis++MOHdGkxNnaWw++lTnFs2oysvIeFT6PJFDyS8+zEk/Hj4/k+JNAsR6dyeiHQBcakhOjXyiIkDFt2o1c2Z9v8/esXFYlOSZbwbzMJ7zYiZkmkwanJk'
        b'On2OvnuU5dNTqv+Ur3lKjQwf2JlSe6ZTes/jKPUBlTDPa9ypw4hSSVDLQXDDz41OJ8PbDlL1Bg1EkOaCNljplOZT4R1Cq7BqkgUvcVs9A2wNi4O1sDY8HtQ6iHUvbHYS'
        b'7DSwReQHL8395eTah/fSdqVYt9Xcjl0hCM120flU3Qo75OrpLrRpOuMixXPo8qgHUqx4DCk+sdn/gyOUnDpxRg9ESDCSUIvRmpuBCA8hoZubu8N5rLWaTEh45BS5Wfm/'
        b'Fj/nlL1Om/GWkTOj7+NDAlvq/3aykeBm5BNlSK0bZgZR70d41myQOWTI8CmDEV6CsoldRIgQHiS+t3RZkBMrk6N5AXIS7OFPrLzjW4JtwSUqZMiCSncZEipEOHlNJAO7'
        b'4a0uZzj2iIXaPKvR4vZCzT1jYR9xT1jYrXCSMwbV2Ku04L0iBCPxOTYeLD6lojNGllI/9H7M0pOB+D/ESWOvONkRuv7U+OhY12EwygqjVGNCe+DfT4eff//yW4bg57/7'
        b'fsLj5y/FzpfyeB3nfZVn1a5sB34OBqcMXRWcqXA7qzdICX7CihXwvBND48YRDFVFEfz0Sh5ADjZWueGmHyzn0XM8sAsRLlfCK0+Bn754VJ+MnkH8FpBdMKNrWQePbO0d'
        b'Iy+iS58eMfLbx2Dkk9qV9++6fYUoPV2Xp01Pb+fSraacdi98TXdO+7R7utYSGnQmfOid6SC+HMaXRsrhZG4X55vy8vUmS1G72OmjJYEv7SKHH7Rd4uaLxO4QYlARlYwI'
        b'A0J/pMu8u+VX7M/s5tjEB3weZRw7GYoZzpOj3f4ZMe3vhYaPZn4Ssr18c36eKJdUSvt644+3mOwdMy6O7Qg7gZcSkUmdkBzpj2RvCNggWA9Ogbpus0OYAUQ7EaXzBDXv'
        b'82zv61iT53hz5PiGR7LZa/AG09gRq8UL7kxGfpGbS61LQiZr5zdpanONQhdH7010CWJdW41wNDnWHdYU5Hbs0AZbHB0zw51JzuOd4iQiUGeaaMW7coETIVxHTHqngHRw'
        b'1vg0Mel7wbFu/LCnLUapzge/d+yA/wvWfHQLt8eNdXcmS5PkLB8vGuNJyVLxCllZTuD4mPUkwHdJnggf6S6j5uQoGrJ3K2xUDtYNx/lNFjwIvLby59kD5NdWzUs/9UzT'
        b'quupG0P2Jb00fszSWsXB5LOTjk9cPuid0CMZPyoeJa73+ssAr5Kbi1pCNs0cG/dpUtH0jwYLgyUD/5g6I+3PU2+MOLBg2sLKQTtCbz7z3Izw2AVr3vNpzftyTDu7NXRB'
        b'/qiBx8f+ZdbfdYcWlXuOUVxjovuYh04SDEr4wlyYH9L//uxTnkFe19f/jMyPD22lFIl3BnUTc11ObsFsh5PbF17iN78MZIjbUL1EK/33krF8BNQAWV8KW4PfLM6dPCHM'
        b'Ea1dsDSAUlCUrywkz7Y2YiplHYUSl08YC6sTlaqkhORFzg0vYV28CG4FzUWwcjbYKRhOgePgBtg0wgM2wj0SUlfqahJ3JSudkKMIWlHIN3B0iRDHXflGTCuWZphG8ru6'
        b'b9ger+0fQQiHXl1sEEqRQo6Xgiz8q2l47Q0vNrLwTelM+Sv/KAgYP2DpiEk6wZDE6zPjblQO0Huufefe1TkvPCtY0AwC+t4YO3V7rP2vDYdTQ+a98mb+3KNxl/eNCT0W'
        b'DyYdqPN50P7ZF2/sHPbZrnn3r+YfPf3i378a8+N0UYL3mvDf5L2X9bHnc+X/M+Vo5do/vH79n3EDH9a8kvzCe8+c3jJiWy7eowmPceo4sMfpyAZlAQ5PNrhJkWXjUlD6'
        b'DLw5rFPIlVu8FdwqJlItwDZdOyhMiY+kx4MooDzhdQZeAVvABTIDOQpuEYTBqlDscBOCBlAPTjATxsd0X1Twa7eDc99axWTWdPKXk5Add7kWxpHoSxxyJGZ8aRlmo+je'
        b'dNtZUTPbzuEYBjdd69cC1kyb7rq4F25gWI+C8IPeN3wje+yAXeDywrDQJNi6FNS4aQ8DwEEOnMZb/HXjR67NjGJ65EeZHv8NXtTzxJbEyYsOT/ekcF99M18v3rNk3VDC'
        b'i/oFOnmRNOanwMnSLTwv+mf8/8e8KKLI8/NuvOibkDJv0pW940kQJnV3fGEOE9+Hp/vfz/Uj3ObD0MLJe7PX8POP5InPXHLYouxDZa50+9RiPvFHHQnP9G2IMygurJVR'
        b'ZFNoeBBeno+EV7mPg9E52JwAnDY0BjbzJ3oWB2mUr7V6QbyS6eSKCwf6bGq7fy+sJaL+jUWSG36M7XLLOC/B1SHP3zn5B3r6w78fffX9SZPHjj+8xry2aEWD5V+K8l3l'
        b'e1JmrtS9k7vou5a8fxeeDZik2PeXwCWpAfopuc98u+m9Vd9d+7D1J3ps8qC9z4XLaaKLFqwGh+PhuWAsVMmRnssZvSa3k375y0Kzu1KpTv8YKp2C4wr8eSWH0KmUUK0J'
        b'uCq68ysgeN5FjLieqB6J8fWBvRMj2XSnGhFcGaLGYLgLUWNsopMY1RxohM2wstuaUfwhG1IvRFRaIeBPlLHRDRSmwUamhCH3rI5D96yFxs9nUfX0cukypoQrwefOCCoo'
        b'C4MPRDIZi71tggZWJ2ikSwRLKONAfNpLUTZ/xiB5gk8fFCyljIhqjXdt+Hw7FakBl26xsaYqlEvQyJ81KCSHNgWjdoQlograJsIn0+hEtSi/TTiZKthmXEfKClDZh6js'
        b'S/iIJAS9AEEpICfh4LLibmXFqOwbxhmkLH+qn6pbyYG9laynC8QVQj43SqFs+CimEP4kHseJfUk2SucRhJiNjd/VTJKEWLZenz/HhBeVLXwksFoyleNN2CuDEBYfDEke'
        b'mHBMNzlfTS4y6TEieuiN1ly9CR/UhLeWaxfis1Z0+nbpIqMB3xAlli8bzeNbx2bEHdWSs2/IUriF+IKlfjud/Uv3IJTig9HMo/il2zGsw7bGp8NIHWc28YeE4eO+JI4j'
        b'wgLc7qSObzE5BkzswNZNmfBSPMLQWGVUKKjLx7u7kDUYssEcbAXXTd0iMVzHQ2BHno0yi3V0CoVPeSTjz5Q51P0kMo6m8c4+4N3izb0dJk16lm7JS8/JM640sI7t5ikW'
        b'2zH85l2NysU8lMisxXvLLfTDUQVYI6NGgM2CopIuOjfmGq6AtTEEUh29ijZJsTmiY234NEVaxzVQ+Iw+BLcggGqkbXR/Cks8nELkmdDRCxI4wgxfQ9b9PWD47giKMw05'
        b'OXKmnTa201m9dQ33CPeMdDGfdR7KzvKRUQGOU7XOwDugCdvvqEegjvQwGZzVkB4LqRGDBUXpgiesHqd7XD3+HxwjTLs34bZwt2Px47VZ+dSHFDXvZLFauG7kSj5xediL'
        b'CB2o6LqZ6ti92oF84qNpRLZF/DlEnZDkNZQyJMffZMl2Mf9zvuEL9XKy39+lsuayS3vf2jzk96Olp3Y1ljeWNda0xpwus9Jar5mSP884kfT7GRuCywUJnkFVAtmRQYpB'
        b'r4+V/qZGnuAX7XeECXlJPGr45qXSkMulEzbrh2gj2JUTqckhQYXf5yFlFndi4diFzmXmYF+YllEu1hP9VAxucWHOM3RjwDbHMbrgOmjiZ5429BGRPaEqE2Cdgs6cgjKc'
        b'ZuC51fAG/7wM7GLA6ThsY8JKpMOuAwfhHmYouJb5y1eq98nN000Yx59Bla4zrDT0GNaB/ykxIWlMysG06W1XNRVP02Cls0FSsKhHSVf5mDXo+GAJJM5uRaJO14LboD4Z'
        b'tI4he8/j4wHxMfX8YFHjwUnhukEjemcjWIHmmQcWeI084TFJ7QKNWWswIA35JcohmZvproMlytKvyTFkFpVh+EnACEsWzsyD1+FhElBA9pgDpzkKloN9nnAzA6+DE8be'
        b'ocGcGx/BRsShPz63EMNU4oCQCBMmyfQOD81MJ2SP28zRw2p0QFnRwdiwrsLz3zLEZXeEwdrO0PZdmBjFIt2voeQXDZwLONO7TtBMv+sCTkbUGP6kzTq3QSMBDFXgdlL8'
        b'qNGxrlPafYZw09hJCnj9PxivlS6Q3nuq0ULg8TJ2R5fRIiDelvTFEDp1Tm94Lg4cYSMngt3dQvZcB8fi1c86GnF7rElRphALlgVsGYP0C6qE5Q+WtDGI8zMFYhuTP8pG'
        b'40MeCeiCpPZhEZGjRo8ZGzVu/ITpM2bOmj1nbkxsXHxCYlLyvPkLUhYuWrwkdWkaLxewoOK1BxopCoZCRMlyrl3IT5u0C7RZGpO5XYh3SxkdxesEHv9Pe18CHkWVLVxb'
        b'r+l0QhNCEiCEJUBWVkF2ZAmEQEDZFNAmSXUwodNJqjssoYMKSHezg4IiCEREWRQFAVdcqkZn1HGZcWaetow64+gM6jydUd8wOOp/zrlVnQ5JXObN/775/++lv1TVvXXr'
        b'7vfcc849y+WNHzqcjc1e0fBZJTJuHlohoy4Yqu5Sj5UMGV7SMkpda/qKo9RHv2OqOPSpIjO/hpU4JueNsgFGvdPuRBk6nI3E4csmytIboWyoQcso3KtuHiYOylZ3kt2x'
        b'JYOdeaUzyd5kjpkbPzZBBXL/4V4jv+eQQGh1SPDDyc428pTtO7EyoRgVSf6tvb4HY1cUkO3opAUztdPiIu34dSRUOVA7fTVQWBy3CM2Mc4vUp7TDVbt3X8P7kc2ee+bA'
        b'x0uuZfz+Db02nVw3+NaTdwy+tXjfXVuY3PiiaWbLIk03/zBNu3tQXoF2m3a8GLpj00ALZxsqqM1VzN1a/QzcVqAPyRTgzEptF8DLzgNFbRf6oTe2jg7wiip/rTtQVePx'
        b'B8pq6trn0N/EDbaalfdj4yxGrfRFaz9M8QQbr/zBKIG+OyYa5vJvbvV7s2POPDGQ1R3j1H3UNkJmsKuXzSks1jYXcFw/xXSTdnRQ0fd4YRJ1Ab84BmmIj/PC9MPlbdsY'
        b'NSYKvM386MTkbbU7UtVTJbDZb13dX9ssceYMwa7e4mK2Ia5O5fIne9A2xGKHS9TZkBsbtQNDh9RPUk8OGcT15iylvLpX265tYZPtgEV9eugQtblRPTtEPSPBe/UOXj07'
        b'5VoyQpE+bh7ZoOimrS/kCtVnVGYlYZ01jRs07LDELVkSPD14CsOhtszL4WbPvUGEyImTK8o5srPgSNHuI0us2uHi0dxoKPcUJV7dw8olT5iNOcyYyg1hOSwbBmT6mNVo'
        b'xsI7o0cKjHcDUvIpWaaSYvWBfG23dsrMSd159dQkdQd9cc+MCdzNVy4zc3VLFN47j2Xz3LRxXDD/CgktM4yssLLIJd3NnGPYR2iywPt+/RSu6olffiD5fwtvsj7dPGX2'
        b'c9N/MsExc8gbe4bPf+365G2Zzyd9NnBM+L3BP/v9xKRfb9r5+JXWt9b9vv/pm6pfKsz73Vhh4MCBP7l4pstjlmWbE3Nn3vHCUGvhY0sT3thy8ubXu9Ysea3i04zp2x/b'
        b'fvythZu+vTTjl/nXHi3nS17ocuvyYTWJCVv/o8jU5cM6JXtn5YtTF6yuKwh/9txHc8Z/9l7XKSs3PXNxza0P7177x8Dx93NScpsnT8q+sH7ZoKUjv3qBv+GuX057yDly'
        b'/O9/NfZv2VW/zBrzrHn6b46s+qPtjYNvPeo+/1yv0c8duv+mUdsCCR/XPvHnngefnvjyg+/mmJnw0QZA+TaWFNvVs3HsEHUDM9mp7tDONMQwTEQvl6wBBNM5g0kiH9aa'
        b'1a26Rc+T6jlDW19W6OMkQX2mRH1QvbmIBKQN4WhXMbO66RV1dRJivWr3aHt1fZLZ2kYykjpNfWwRDq/EzVEfFar58dnabT/cvc+/gueaWAcbn8cNEOvK4YMGE6wa0xZW'
        b'jZZ4xnmFzU508N3R3bUg8b15gehVF59GcczltfJBDKoxgzRRe2WtUuFxk0/lFuD2z/g/FZQPOS7edA2WdboDSPjqd7BmkaezYvGsvGn5uST5DuDw2hXqo4OGDpK4vryk'
        b'7qq1ExCYqW5XzyKq0quyB9cL9vdQhaHuiX+tBK7Q72yYR2/aESDu0ANyGElZU1BS8oMm+JdgnzelcSmQqiukCQoHeRKT1nfWsCiLxnfrxMmAozXzkEpUysPSQYgPis0C'
        b'5MyQSam0DU0d816HGxj5uU9hFHMQMuxKzpY79HJPOE/7+xm5uH9L1Entxqxyby2QP0z6qcWuwRg85a2orakbx9AsMWpqqKvzKAqe20UlIsfNUSngWRkA9AWz8Fc1eqI2'
        b'vweFsgLod35FlRy4UfkTphdlz/L2DBd9hM8XYrPXEV+XX4iGHK5o1RkqEp/5rSSijVna+rS7knNLtI1aZBaRQb2142x3h1XdU9svaae7jG2DqsY6FUcXUVXCqDnAqNOI'
        b'9Sc0YxyMJHQzbFayiN1MjEFBKYcRFmQJUohB8aDYTP7Nm0QcScphIcSaKAcRRzkIO6RsIqzJXHppwJjF41fWeAvzxhPaWeVbOnZR7/7XD1h0A1zzcvC5MHf84vHjCIO/'
        b'gJVlPLKfcERjIgEUNfs9ZUrFjVHTUqW2oS5qQgYV3Ly1K2BkXqAlGhWhlKilDkXZFF/UBD0JH1iNQr+LIEhGO7/wtdtI/K5oWLUSJcNOBnkqZ7BDP/TN0jZ0JpO56kNo'
        b'1kiNzGL4Mhk3tgDl+jR3ZY5ZvWNgp1Z4SKvT09tpNIAcEFI4JA8YTaMEUP1I6YvXg3wz5y8MCjKQD0HOjYpJgjIOr/RmchAIDjf8T+audzURnQS5iV1hXHiufhql9sZS'
        b'b2WpfRlBXtlK78KXv9PxXak0ytsvCVlZNBjQezRbP6dFECir8sLCkDxeTw0Mgme5x/sd6y7qqFM8AVSgxT7+tKVr2dzGYzAzPeFhWIqO3G1W78rMGzC9IAeJ1dsa1OMQ'
        b'Q73MA/S6xzRgkLtj9fWLXLx0AEAkbqHokcjjM4cenW8Xq83VloVWiEMvzxhn8ViqbbLFCAFWaAFohsrr1oV2ubdONyTIjvW2hQlyHz2cKDsh7NDd/Ugha6VJTpKT4ZvE'
        b'VnGdZBfEOWMxktxZToGYpFapusipEJdMSuvcwk5y35BYyZNaum2hS86mUKbcE0Kd5X7wjRlqkCX3gnAKORfqQvC0fzRhCgyLxxeYCERgq4ln8CvnGLC1hf8vA30Kz5Lx'
        b'TAQcUKZ8Ew3/hW/h7xI/CpB3FAM5qjtPnRUb57i15Ka16UZdQ39dWYVHkgzKTmjsHle1wssTtktaUl3xLBvJfpiqjAdBypGCYuIRxAbKlrankhe11XnLqnxueG2Nq0KX'
        b'+CrEUrQpWzDKdnFMF7DWaSxG6ma+9KgQNblxG6BF0a5SIC6ZpFjZYmNyfNn4aZvhiRXroOHB9S4baohHecWGDk8lvv2SUlpa2YbuibGpvbFhJ3jPM9Y0HYZMw0OgIEB9'
        b'hOKysExQhsnIuhDGcPWpECMt5/ypsiko4h0gPo/HPBBjYV+lckZamT8IOelcNmvpJX5glM+9JBQOhCEj4+q4UhURB49ffcm0Orcp24/7rL/OWxWI2oHaVAJ+tDpNe66h'
        b'LnYzp+/uUb6uI4LVDZAGtmEPOSNJkwxJeV0tDf2vZQguvjG91TSM/6a0lY1XMb7nMo1JSD0XYIcRwkHqs2bBUBUVlc7YLpO/AXAGRBd8siE2iQ2I2mPTvYODCqULfN9X'
        b'0qlGrHrraYM5/jcqeWNLJZUUrKkFMyzzepVUvkPEKQ1eDWhVpc6XVwlyaBfWUK0QhIRhKoUlRDfCNLGrYQpuEaiOvFHHZp6HdzqP8SgfNfn8NWV1UN2MWHXNzNuM7r45'
        b'avGwevwwJfJukEO+pCv4coTyJ/ONrvi2sOw77uBBrClCrClCrClCfFOwu6Exgs5pVtJ52kTjGlKFxrMCOfrkQJuoSnf+h6rD94CUQ1q3xHVZS1j+bQYlxrRC8igMNQ2L'
        b'0JJcAyYoWYiLyIRkN0FrEB/ElRwQ9KkkBg0QLMLKnsCwA0nphA3D40zWugS3G3CqqoCnxu02dovp3PcbFlV6wtdXSsYJFuFbiHU1dm21ZFsy73ikboifdIXf1T42Vr7c'
        b'2LgW6eMKWyGNq6iPq2Sk1WGyVKpk8ga6ms4GjzpiMUa0jDX0ht+osDHg2Bu0gf6wAe8F+YyX9L3Q6BenYCe7B637JlbU9zjaNjjnc1kx7W2hVre7vLbW63YXx+2gKa2L'
        b'YwkIW5/bajQMqgPZuXS2FIaVEuQqEdvlEZ/dB/vMvfxWXuefFUHXIOqm44urADBX+QLRJETMZU+Ft4yJvKJJgEAtO6E29gb8TOmL/U2n4pdxmc2KB33PzWyZVg5e+FaC'
        b'/9YrhiUrarcRNKWyYo2QadrIwhaJSCKeSU4w746lUali8DAfqiQyR3ZRm2dlhbfBX7XcE03Efc0N9CV5UvgcK5kFDfT5x/buTXQpQLZsgsuwK3lhmzCamIOty8XLl22b'
        b'qPSHF1fHwwPhW7PQeuPAOrWCBtgVMTrkVbhUcXh4gXQ/YAM3sIbRRiLB/AfKvRkP3/l0brHQZGoyB01BYTkHND2uFVM6ur4T/New56U83sfobwBmmBG01zuCZhYPT1y1'
        b'hCIgUFIm5GdpskLJ5qAFSrMErdi1QUtXDlIuh5SWJlvQppwN8v4jQI2eCtrgvTiG80lBG+IsfjUo+FWZal8N31bxTC9TP1jHJXrJ1AfxrRxb1AFrAyjJKq8Mwx21BGrd'
        b'clVFgCQraH+AHSYAc6s8asOEuJD8hGcy+sfCE8OH9h57Ra3Pz5QZo7yMZy+QaZSvUMyYjVAhM1OFhCRf4DrcXAdC6vmScTZKjmTsZD2ZOYWx8y5a5WbdcaxE9k5ab8B6'
        b'I8hUBeLFtBZzhKKiHL4oJ/Vy0WZqzWNGaxQu1jgbzyhtJKAZhoC4CO3+1DW06xCEJnCk9MZLP16fftSQOHeNP9y7d4sfR6wLL+m6TFbRKgm8XULzbHYJ6G/R6UiWkqUU'
        b'c4rZZUmxWyWn5DTRWay6Xr1Nvc2vbSmuQp2umdqWvPrp+aUmLn2CVKSGRszNYSIeXskWp/WlkdNkTJxj5obI2tZ+5rlFaboxIPWo1jylBN1pUwqeU9dq6xLWCNpxdW19'
        b'GwlEnGgkXuWKgYgqQGV06GYYEakpW+bRERalZzuAyqIPakMLtGV1Calr1Qf9cZVZqR2wq/sFbVNlSRs62ABffhQEitHByeSKFmXlgeoF+lICCpZnptoWmphyZaWoU7xm'
        b'NNgGaSyyQ06Eu1V2yknr0eAbW1mdoo7JDTU1q/Tqto80x85FGRkDGzAfR2vyLbQmYzrAVSQGhKQfqJhKFT62uQq8TjHAbonLi8hQNn8vUM+5EYX3xdApWoJmFnc5rYRa'
        b'Fk0tsNLMZ8J/Y5f4Fv04Uz1seJXRfAe7qA2wFVaVdbGB5RtTWxUYS9IxwqYfsBIqotPAhqsoanNJOzOK4WEI0dzuDXGFp13W2liijosfR0Mp80AXOlDkjXBHgPlK3zB1'
        b'BBLnWDEYaAF5gcoQHMi4ClfGBLYyGTJMA0m9RkhTFv+dx/YEeCItKJCVWHJOYsi1154fhQOxenWIB1ncbq/H53bvjOvClMuKpAQd8xGwMQFuqSHgQQBBwi2mI8QL37nd'
        b'u+JKbDNFKcUPaCGexRd12DqC43d+RzkMw8Mq2y/fS8iV91gcvfGxvWECXibGNgh2LNzxsI6CRI3GsFpFu9kqOsRkG0B/kWD2yjFD/DkIs9UHA3Bbp52OQcFM9XFJu0N9'
        b'fE3HMBANthkw8HaxWqyWFpo8THQNOX2SR6q2APKmh0J8JU/w0brQynhzABMZjLQRj81Og2eNumaVV3sqAmSyUO+oH8lCQqChWDsAGQTU7onjHHVtW96PYyARtLB/F/vo'
        b'/g7YR98FgyoNGKSM49sipTgljsfNq8x2GvFdoCemFYn+6htdAU4nwwgpXQCtkoAsXTWMyR0TEBKDdDSxTjBz17H3plU+XS6ZP2gmAnAJpLG0EIHNPEtrtIqF4uQVW0g8'
        b'QGlSjFketRcDsbCSyeYSIMNVEHVeRchjQ0CX2m0hi38IdDvRwrESgJ53ABqIyGDqd3SdTlQmXL4wJ7XC6hi6N6L1Ov1BnrUxn32x1RmHizlEZmPxwZxM7ZFZ2sbpMwtR'
        b'HG/TjJn12pbRBbE1OlG939Jnpnq64yWaEbdECSmhQ0RAVHTt3Gg3o/EGTJqEhlVn1NYua6hrdYpp0idO59iq0/erMAymjlYArO8eA0smhslLgVV1HmUfPtpi/Ll291Oz'
        b'l0p9qoUZZuUbe39H/QrZB+1oGBbH1uFly6YIXjxuLBsAgugROFsEVLWlm9XjgRgyWK9tLc4v1M6iXK+2rbCAU/dpGzl1V71du0vdo+5sc/YU45CgRBTs4hzxPLrT4uIZ'
        b'BRjEszzoPSU/jDQgFzYjcRvm6NnUrC/9S19PIkMvqCVd0eAP1NZUNXrkLC/Qs1l0HK9kDfAEFI8H7dLWtkzgnI5t4lLyUWgHg4zloJp11VJfrQJltDBO0ekfeSVEsx1l'
        b'slzF3B1m5ep00ICc3CxGebdWvY6rQusiytA3n59s8yhl6CQNzeP6CgxTNVk6zu5vnR0QWnQ2KV47cwYsISTLowlxZRBX4sf67iyBwX9eMgTzrMymGh38khjHPcPUR9RN'
        b'2sPaGYBp2klt7zxOO6XdrG0jMSFJPXu9ukndBu83aHswjejjr9YOz2uz+MzG4lsSt/jkllMrS6WJzstsC0WSkjJDDDsts8IuiVJTVtgZLbIVqQfZJtuBOjDHnZJZF1po'
        b'v7TSTHFGHfrKmAkUkFJa1MbYS2xO3suhqFQVzDWZ3yc2STEOXl8gEfgqFLHklvJ0UoFEhaCEY1y7cUFBfwP4ZzoHhIWEXIKg6PfhE4WldMgd+RLQFsYDFILCZBQwMMF3'
        b'JiMN8SgUg59bLVQiNSchNccb26kZ2ejTcA0Tn+9K2lpxBFvi2MFp1O4mNrYbmey0fyDSlKMb4qGEXYlJWKd4KqtWulF2kzQ8ooLP/8ONo56XDBUmANHw+9pswsmD1ssl'
        b'smKOUgTJuufZ2CkYjUcLtRMPKixcnEgIGgJaCkNyD3awgCwiHsIo2Qqdt4ExiFAUwD+EmEYSsXvSALgQ24hIT06WtmBXzzfYR0yDSAnQFzC12IDAcJrXwUBTDkUQbwEA'
        b'vhnTsDd6PIEl1BBaJ7CY+jQUO6ADJ9gyTHPwECkqTvHJUakUIEfUNL/M29D2jDGGL7EzRmRvycJyQ+STiYAIyjU4SnNj2wbfnmQtmQD9GqUXSLykoHUPV9T6ALAECD75'
        b'46VNmH1WyJIYwi3s5AKehBosiocAEmPATOB0YgnACu1cot9THzXVKrJHQTanv8EbIKqipoX39L2+vJytK/cXnEjkOZg8hyC/yS7YeUFAdX7zN07RLnRHbTh7Ct/Y7Tsa'
        b'2eYMMsZGLaLJhCsVpsPwJhFQL5IXIuWyfJxexJcXm9lgW4OizC/nFStKoWAsxQn6bo6kDbJaARn2wGBb3ZVelADxUYcZzNP52HnX4uW670HDFsP7ZFOMyGSWhV0kD3b5'
        b'otELand/pSmFShJxKnZwDWI70vCIi9ghsCyaUUQc3rHzhuW4HPBJhKdpAYBFQSEVduW1PElpAMxq5gnNhYUCy0JGnqcv2YjBNHgCK5vYE8RAn6ZyhpoRnbgKbjdNsEup'
        b'83zLfLUrfC0ba1bvbH/vS+bV2X48kDUr+dhhycRJYSBMKSUMktNxWoPZQlNtdluyIpro9qFEE9oUhwzSsVvJfDPPjDYn68cYqbxZSOYbM1p3b/ynbQBTjN9WycUfeNK8'
        b'QdwFsRiBPVVxTRKTWtJVBRH44Bekvhg0ByWC9rkBiZ1wVcNOgPzre/hrYlDfYPKYlTJenyTKwtiCpDMeoNjRWD/g4pY4FpTV4DQrgzBoY7xlaFHc+myfLVwO6fub4k6w'
        b'7SIyf1mftYHfetFiKSwGW7tE+sJYxakJ5f99Zu1MyOJN40zFKqV2cfUEst1J2uLdrtHOtfAr69SN2smZ2ma0rJXZVVKfzNP2tWv6Hf/ItXoMJUkiktxARZhvBgMNwTeX'
        b'oyBIP+gICInnIPOSDV9y1DqjtmJZUZXXU6ogcdAKCWklJIGgOEykOk4rf0pAkHlahIyeFugdHYSmIt8SphdcTcS9NBMn04Laf25r7JjwUmdyFC3XenSvCohZXrJk+wtR'
        b'7g+H7GaOzoT9mI5WWNRSVu5HkYSolWQD5SolakHR+tqGQNTkriEvS+SPPmpxYwrAq+MkJaISplCWtUOW43QY2TKzHIQluAhTMPONnYxOap8HigDOzsUJrzFBUWT+oV5j'
        b'Y3IYFx4AJATTCzhfOekG38wDoOK5xulBWF5AkonKqLX4jVkpXQD0NoKxNSR4pufGL5OU8oBFFrDXIc4q6/kZaeud7D4IKXWJ9fscDmOpx02lFzoRjKuobfDK1OVlFeTZ'
        b'Ad1vL/vjXXvw7+j4uTk2IP6gU6mjoqaaZdDNSjWdv82aQyR81ORRFIBFPox0XNPgw+T6G7/X46nToWDUAtsPZbW0w0UdlbD0SSad6OV4J2yqycTDFMjLDI4FCvs2JsZG'
        b'Ab/oWOkmn2OsJaWfTHMTZiZv9L/SD8ZCMsZC7xncLU3UGDZNTFX+WJNNSg0+Ez/qcrq3wYcVmWuKY5tjhRuTYhVlKb4PwWKoo8zFmKBKU0dsczSm5AGottDUwkJKjpud'
        b'9LLjrsmNKw+np86nFhifmo4boGt09W0SKJOURqyL1+gcpSZWtcv1ltxuAL7Ifb3eFDtUthKSDYPniquknqyNjDP+L+B0lJ1GMNVgDmL3MEFPxJ15gxNFcjs1NE4V3lrA'
        b'CLHjDDkYye1ZWdEOExkADaxgOX7Y7JevcpYGGSMIFTvYPqhnaKjW4OUmvKz9IexdDyS6wqQTtFbJaXd2ciCL10LmpvPV3ep2tAM1S9u6XD2WhOqtxSYusVq0a/cNb7NH'
        b'WPQ7bfsxnhEKn0tAjsb4RijouVCSk0PMK5EI5Ku10kyMXBvsFZ2IgLWQXyE84LLBvoEp7ZAHHnS1Jl5dUalo9uSiNlAwhoKgdZMApyMPsEcA0iAwUtEYQbhD7cJCtYQa'
        b'4BQ2yULAzEL6jmGoEV1KmL0KCxyStTzbfykRAsykFQYNDiQzFIYGVOvKlnqiDr8n4K5TauWGCqADHPi1e/6Ua+YUzyqNJuA7MsgLECvB7dZ9wLvdTGTdjW5wDEQuZlfg'
        b'uwYUy65tmfWpJLoLkCARi22flOyIMa2fvlzqNAdqklVT5iMDpGj3BgHDppb5zSzYXI5dYstibVgegxJCo4uq0up1aasKIaMwxl3eFzd+uP7QyntQYKywakG5ISwdRFBB'
        b'4u1A0YoHJeQjr2PC8PTcJAJqL3blUOyaYgEXOGhmMiGEjPLK7jCglbJpnbAtA9BR6aAlKLAdTYaJJHHrADf3JQ/m/JsHcYxffR2ni48hq4FE4z/HGtuzs+dMmX1V1ufY'
        b'BUxUcqXiqbQTTh8VVpTrUyRqBjyhriFAvRg1yQ01dX6mS4wylXR8GjWtQPkGnQnKIB71M30iVN74wzXKlR14iGMyJLtJX9yMAkqE37uIgTWAb0ygcWEVi9qmebzLPYGq'
        b'ijIFRdGYeisOTIXBnMI/VLOJ2RHCXSpIGAKg+jyNFaLyJOQN4yDqK436nZ6BfAL0XsQ3YT5gAkLSlMKhuCva/GDhbixslc1NNtnSZIcRNkM4AeZAAonF/rUJxVYc6VxT'
        b'YtCm/MRIF0yEEbbCLnunbGtK9GVS2A7hs3ICvDXKtmLZ9XWt6xJ0BAFHTeOWccp5zFt2dOXSubp3ICdn0LmdV8bIiUHnch6fgk5WDjxnBh1wxbwtOlSBPGVn0IJ5ymKT'
        b'DWrhZLWgL+E9iqOzMvE9isfIlqApmBi0A6Zgq8ZrQrVD7rQFqJWgXanDVFBbM+EKrtILqIZyAcdg7gUc8T+GUt969W9zvhxfRJyRS+LYsWNp4KKiGyAKP5eRlnxWlJ8Y'
        b'tUyqbVCqACDxxTlC1OTzrHCvZLdVOYlMk8BOIr/eKp/HzwBVTZmytMrnj3bGQFlDoJYAnLsc4NeyqBUjK2t9gP8qtQ0+mZ2ubMDZKlV4vN6odO3sWn9UmjGlaG5Uuo6e'
        b'S6dcOzcnic1wkhSQKAOJlHZM/sAqwJ8TsALuGz1VS2+ErFlt7JjA7YXqePRnIIChCJPigVpEzeWM52LzNdS46QsmmizhM8R6VgYo+nuZLwlM4JQEycMmXTGV0323OkhA'
        b'NZk0Tqw60Szp7DzSYUNrLEJ3Yusxv61s0eFyc3yLmm2w1SfToosrpl3GDO1kK7nW64vOy7rTgT7SQdNlIcKhDlZYJDoL91krMnHW6dZN0lGFhZfNQT6VCVeKsgWhXEDS'
        b'GamtSWtRZ6iyfdZ2KWNimYK64FlDaytHMgY/majwN9Qo6JLwUt4P0ZMvKMzqOzAvuw3GFRN1QxBFWmXOJmgLYx3o+mTrDf4eCjsYGmVXtENDoSrZWciR8fp6Uhdj1YeO'
        b'bE+T7AImvyTlZvtzad0gI+GPmE0n4hHAwJC4e9RJE7wKSPmKWm+togNylq9B3NGZXscbNdT93Vgtn4PvH44xs9CMFSk74pGCDov1vAn53YXtjIFiZTffITK4hddBvvIE'
        b'rxcTx0v4Z+yNtnAV1kFmy0wxrkKyxSqlOVMGkN60ulZ7QL3Pn1CnnXDXi5yg3cX30h4Zi5J+MdyARODE0lJDE189sGpJnKWAAb2YpQBZewKF48QGpBMnahvnk26kevcw'
        b'uIT749ekcfxGkcB19yMAXOLoU+yF7i2qSvSeF/z3AQo4ZoEwc+7fF3RemnJ3dt/btjT1334wvGje7odzXIN2/Oy+9Vnmtw9N/WpU9RPX5tU8ePfpM3v87+ztebHnZ+P/'
        b'/PW4p9/4r7rHfn5+xbvfmE99sOHT7X3emLDgpWfv7C6OvpffXGK6c3vv128rWHJN9bO3/5x7Q+l85w7XoLySZ0vfEpe/mPHwospbxp5K/GTXlCUHvMJXH+TUTXiac76U'
        b'Wzctkwt9wF3Z+6tnr36L2/rixk+fytj01zGvbPts/6G/vL6p6LPdP31b+mDSQx5Tapcbh5yOLn/5hc9NTxw5cPezv88ZMHXl+W2/SLnefu5sjw9evW7lrDc8r2wucR5L'
        b'f+e9jMCCPx2rtBx8Uvrm9RUXMq5fsPjlRG/1VW+9cm7xH7ILn7v/513eeT9jxMU3X/tl4hPp/X7324QPep43/XrUsC6+i/VPTBka/U2Xa29J3LuxftFX27LUK8d/OWdY'
        b'iT+389w9nY9XTb1w7Pn60kNbez/0p+Ckfe+P6nnPt45X5gz+4siAC2e7PX/ml5OWFha83vvilMe5d25rfGOkv6r4qde21tQLJ18KHnh0ZejjNWt3V5k6/7lPXoZ98YvT'
        b'Zn477LNFO6LdLP4nmj765YHPStTPM16r75l0cOeQ3KNZrzo/vefS+b9Lr08a/9vmeb/u/2GXhPPHXlrZaX/6z//sfPeDwQO2vX7h+oWTtiyrsZzrt2vr9NOZC0+vcS17'
        b'8j3X6U5ljzSOuPu89khlVBtV8cqsN8bm7r1uS/r1qSMbN1fvXfF133l/+ubx+37dfP+J5QuGLVp28KuZx+5K+2103M8+2tnz9d1lq4ct+tD28NunK94sO7/h1mD25LeK'
        b'Cuqjh8c29ap/8JmP3v5ie2b6lwc/PPHxV0rVgeoNB17/R5cbk474Hit95frh0UmN3osP/P5CeP+Rl4v2r//NrvfePljxRnPo7W8T5r1y6DcDL+SdWTffdb5/02/9Y779'
        b'9Jzvr52976WP/Y+7bt/69Yj81f9Iu879eskjz5ze85Z5vPTtFTuO3udeffp3gzcufnf7TSe2FYndvlr+5ge3fvu0491DC77IeHJNQcIrznOLus6qb5z0ypzRudN+l3/L'
        b'ilmLL/3Xr77xvp27lL+7aeq7Hw/8xS+urpk39tjFW97p/ZtFTSPOnrz3MfvL275w7l5xTU2/52t+umRW1Wr7yTX3/O3hc1P3337s4K6/u023DVm12zqkpuSP8+++9cgz'
        b'PXvMrT9u2v+Tu/e9/lplv7ey8uZ88fKx+R/5Ki7dk/vUQ0/zga/ymiacSFKO75n/+OypP7/x1yNWrJ9+06Fts4Nzp4wcm1V+/8nl7726dGV60zvaJ2cHPSl6L6ywH0yU'
        b'H98z+Bef3XTdXy/u7X/cl63dxO3o/1zmV3/OSWS+k+9Wd15Lh6PbgNqcUVygblS3WbguddpB7RZRO61udpG9UbVZ2zEQ082ic3U0bGnhOqlPqberR0X1tmnaYfLWqD6g'
        b'HSxG663F6uaB0/K1CMe51A3q49oBUT2tPqM+FECJd+3R0UEgaQ8Dhbs5r7QgFxXrzwjqbu0Z7Q4yz8FrB2f527idX0ie55sWUh4r0+3ISVWPVF4u2CplkcNHt3ZGPckO'
        b'hW2oBo4uftVntHuniG41oh4IkPvxHeodI6AGpKOqc2XhWVKf0lvJLJ2R/AAXHGWX4MtHA2ikdpL68PQWTm598cySfG1LTr22Fej2ywQPuJtK7NzcGQHc7dRtVm1HW8EQ'
        b'FOBqLRoyJD8wFNNv7aHu8BeS06ltDbHy/N3aiDdwK7S7bOrZuh40Dsnqlm4t1Zs9qDWfuVZ9hOxIqjtHaLhvSOoeY9+Ypz0DeOGP36k6uuSM/Bdm9v/fJac3wyr+n7gY'
        b'3DNvbZnsdjPbaIhOymYywvAjf3+QejptThRlF9l/ikPgk21wdwm8q7PAD5gt8BmpeGrfO98s5E5PS3ea0iZIgsCn8VfexEHKfg2Q0irRyX7fZLxm0bV7T7y6THS1QHob'
        b'PiWLeE0xXf7ssBoxLkjXuzuGUh303klXyLNfrQMJjG8lSIV1Tusl8JmQMs0CJAXllem00n3AIrxmDMNrfqmixs7/bv3f1fC9lxZKAvutgtM1pLgDwY5NfeB+oa2dqD4R'
        b'28VmLZsBcBr2J2e62EM9MLxq9KVhkr8QJmzzPzILdl7ne3uCY8PS09e+837TitTRq3/f99X77u32+tAvzKYdZ099sfO+plOfz7ZcDNWOXdu0btwXA8bOPlrV6+Z3La9u'
        b'v8faNPfePquuHNbrwuEP/c198hOuL7vqT7bQRPebKZXrH+33j3vWX9F5zfSR0z8+dPrU+tW3J497LGX2f2W/vOql+iXCS88smHsk7y/Ntt2NzTMGLRj6t48Hlnx5YP+g'
        b'fSVTh/7jvje6d3ljaO5dSz4c+819LstrG6ffW37H/ZUZq+Z+lJv72r6fjp81rib/y6SaWUMTav7q7/Hi3ovPLpzvnXTn+50jqzKn5ddNKt+xInv3xVffyXv53L4rLrww'
        b'dlmXk00XFkWOF285M3/4ojs+2X1mw5vNZ+578+SZ3W9uPXP2zVvPbH1zz5kT3mebj+050fiHBxt+9e2Jx8au2L2xx/uzHzz+5pl3B7/X5+Ve7oSP/1J56vkv5b2bXnR+'
        b'eiHQecvK2zc/dtfmx3d+8tct3zx699inT53/4+4P+NpFmX89+kGnFQXbHh/ofaH/izlfnT2bPa7s05sOPHJr3udP/OLxGftPLu+1e9cjy8fMLLzurdV3X8x9/MNX/rCh'
        b'/4sFK+Txtw249z9//vWFMWv6Pd/57Y99v3vl3K+/Xli9/qHNT/5mzPD3f73so7Hnrht9zRU3nDv89B/mHCjKu+LTiy57hnPx3+8fc/FnWRNSR/7h6gmdPN6Da3Orjxy6'
        b'pd/CGw+tK2z8U8XNvYafvLXmkyXrBy8/GWrq/l7y1CtfsJUOfi791fpbcgrrb112/r3UXv+Z+Z9VE7Q7PlEPfFWy54u3+n951Qc3fCO8Mumdxcd/lzOeUJ+J2gn1Vn1y'
        b'bdY2qfvUW/L1+XWNOFgLqZsoWRFqzRgYkrpZOxGHJQGGpD3tYQaJDo4ub/GLqp5hrlGz1NPkUrWfvUueeiLfzK1QHxC0W/gl2j7tGLlZVB9VN3F5JQW52tYEbQ/iROTv'
        b'cHOJtsnC9ZpjcqmndBxMe7qnukc3DN80qY1p+IV5hD9N0CI3lEAibXPOFO1mxLLyzFzSCHGZST1JpuHVezIXaZsGTtO2QCNPc9I0dMlzcDYZNlK3pGm7S7StAwROu80m'
        b'+PhxI5LZR3fkVOehtflZJs48QYDsjzjVu7vTO5d2YiH5ghhQwHPmlYJ2IHewttHG/FZFABV7rARf5xQDmmJVn4Hmq9vU0Cj1KeqZkkkLAK/Mh+Yd0rYLQX689pQWIo9W'
        b'krZL3aMe1zbiy5vnC+oj/FztlHqIeaLNVM+SSTHdoJh6r3bCrh1Sd5JZUvWx9D5k/ZHjeqcJTXyRqx8VVqlG6rVNswp5TjupbRTUjfxU9xByZre8YSQUFQZcL3cadQEi'
        b'cdDTD6hneS57mGmydnQsIdZjtUdgFAC5LSmwD1CPqI9qG9WH0JtthnpOUu8CfHotjcMYs8bMtUHHoJm2klJTxjSu643SkBtyWV8/0FcNwUCgO82pgnonXzS9gl5MX1Ka'
        b'p4UHWjjtsXJBPcIvULS9hNY1qad6a5sA9xM57S5tv3ATP0HUHqFvFt2wLK9Q22LiekM8dNR8dS9Hg5Om7Ridp20dmFs8k+dsVwjqM6vUnVdNoCqq6xauLiHICiObY+YS'
        b'1FugPHWLdlieS6i2ekg7N0ndNGsWoP2HtP04AWaaONdoEbpqO8xsyqRZ2+YvYR6JZw3UwqWUlXONODnnBuZDPVSE880ME/12jp+D43zrEKpb1bw5updhqDpzNKydVTfS'
        b'+F7vuwqW5FEygaLuUiOcVM6rT2tnurLpuB26LlxSkDMd6mOeI2h71IdSpyxjpmPP9SplC6AYZ1yCeqcwQ7tXO3Kldpoto7sXQKGbCFVXHzAX6uZBXeo6EdbLSe0ZsiC2'
        b'1F5fUpxfXLBYvV93hOzUNoql6s1TqL+TtbXX4HuTumk6J0m8ekCuYO7ob/eqh1mrZmpnx8Bg5RRD5tptovoEB2QS1rBRO5ScV6w+OCBndf3A6TC7k7RDonozwJYjlHm3'
        b'TPWOkrxpxeKUTE7K4NXmydpuarb2DA+LJReZO6L20GpOuppXnyxczKb8gfnakbzppt7aBo4v4bQ7ZxTQCkyshcHaNA0nIlpChQ4JCuoxgFP7Rql7aZ0VqfvVE7BC0cXq'
        b'fBcnJfMwjXdBXfFlqhrWzpYADXbFUJ6zaDuBmutk1s5cz1b3PvVu7Ryzb6rdOy5m4lQcnQTDSINxQHvUQeZFR/doMTAqDi7VNrLu2t+kHS0h+9j56lF1t76gnepBcVIh'
        b'zG2ahVt7aE+2tuWKVmfnqY9pTyRrDxOQ1u4ccZVh8VW9T9sfZ/WVbL7CChoMyYZqm8ikcAGsr1wYJFjjOwH6zKDO2VxSoB6TgHp9mpupHrdot0zQbqcZk329tjcBid46'
        b'/LYEZpV2n7qBS9H2idp92p0AV3EhTGzABY+rfdpMADAJ2j2Cej/Qvo9qDw1lfXGwu3qYjB4jiYfL7REhNVl7xK1tpQzqtLUa+sKdoW0ruWplfk7BdBPXOVPUbkvU7mWd'
        b'dWKgswTWIjY0Upw/fSDa2hy0ksvnTNqeAYnUEZO19UCOs01ty6wcpKS3wGal7kzjUrMlMRWmGI5cN/WA9jgax541izYbC9TmlKCunasdmWRhPbpXbVb3w8hDhZbjjFsK'
        b'8wDIWguXrj0iXaduESijWm17NtQJ1k2kST00C0CFACQ9bIzNiWqYZpBjtXoX9RtsaFOhb6UCXn1wqHaSoGm5ur8H1nYgbYCw++3V7sAdEPfXbn0ldZ1rCKNow+rhaSXF'
        b'M3NnWjizJGg71VusyZOJp6Ce0e5YiiaTqbUF0K/aYQHyeEp7oq+26/sO9QyToCP/Deiwf+NL7CicqEN0u8UlCIKVv/xnF5JNEh3dpAFVBZg9+xckHlM7WRo80InRlXYm'
        b'FSnY+bifkAzvrZR/CimHt/wclDumYfpCksDyhHjBLAZv4tr+gI5ljHzdZKuNjEY01LndLWYNjZMQjY9vLT4wSuVvjg4pFUrZSnYjEf7xZBDlJvw/gWs5J/PV8IvMD89H'
        b'2bpIf7gLcBfgLsI9Fe4S3OeF51dxcLeH56PuZKQnpq/GlHyID803pAGbOJQE9Io1UiSpxtTE15ibhBpLE557WmSb11pja5Lo2e611yQ0meg5weuoSWwy07PD66xJarLg'
        b'qWogGXLvAvdOcO8MdxfcM+HeGe7wHs+HI72CXDgJ7klBMqAUSQii0WA+kgzpUuDugnsXuDvhngr3bJRWh7slKEV6y5ZIV1mMpMmJkXTZGekmJ0W6y8mRHnKnJqvsarLJ'
        b'nSMZQVHmwukoER/pI6dEcuQukUI5NTJL7hqZKadFZsvpkalyRqRY7hbJlbtH8uUekTw5MzJA7hkpkrMiQ+RekVFy78g4uU9kvNw3cqWcHRkm94tcIfePjJUHRCbIOZHh'
        b'cm5kjJwXGSHnR0bLBZGRcmFkqDwwMlgeFCmRB0cGykMi0+WhkTnysMg0+YrIFHl45Cp5RKRAvjJytTwyco08KlIatq/jIn3l0ZGJga7w1EkeE5khj41MksdF5srjI4Nk'
        b'PjI5aIE3WWEhaA3aKrGXUkLOUNdQz9DMSkmeIF8F42cP2iMOktZpMcbrDCWFUkKpkDItlB7KCHULZcI3vUL9Q4WhgaFBoatCU0JFoWmh6aGS0JzQ3NA8mA+95Imx/Kxh'
        b'Z9gazlknRGyUs6Tn66Cck0OdQq5QFz33HpB371B2qF8oJ5Qbyg8NCQ0NDQtdERoeGhG6MjQyNCo0OjQmNDY0LjQ+NCE0MTQZSi4OzQjNgjIL5UmxMk1QponKNEN5rCTM'
        b'v18oD76YGiquTJAnx1InhkTyppAI6VyhznptskJ9oSb9oSaToITS0OzKzvIU45umhLAzmEAl9KNvE6CUROrPNOih7vB1H/p+AHyfFyoIDYb6FlE+V4euqUyXi2Kli1BX'
        b'kXKS1thxHJsc4eywI5wbdgQd4eJ1AkqlUEw+xeSzmDWOYALJpUxlbhroDJQpLSDM6FgiL4tjdtzRLmgDr2QE0IwKV80bEu66pvKlLtn+ATlZVUxUtiyrvKHKG6jy5QjK'
        b'CoRFdCCJx7EdGgFzV/qIdYeCd6+bdEVojk7GlecNPZ0cCcDeUk+gUkHtEKtnZQXJCZGyPp7311ZGHYasFMlI8WjOpQbgJDzZ0Wh5TZ3i8fshJHprl6I2N8rUKa9A3hew'
        b'yReob+gJT04voJjRBc4QFa+VPQBtSakDxeyjYl1tXdQOucueyjLU4rBWutlBMlMfbbG6EYPQUXMl5RNNqKh1lylLyWEqen51L1tR6/OuikXZIcrHMos64NkfKNOtlloh'
        b'VOktW+qPWuCJMrPRg88f8NNbUg6gEpaXKS0BlDvGEH1HD06KVfwkzeGrpXy8MIBl5ewDxeNZjrbpMYDCGhQwVXg9ZUrU7C2DAR4cFcurlpJIPVr4Yd5Monb0wc2emfzS'
        b'C/ogB5SyCg/61XS7IXm5mw2kBZ5Q+iIquRVPZdTplqv8ZeVej7uirOJGJioNE0NmJuiQzr0kDMhp49wQJwjSF8zcl8C8JaGEGBrLQsO2KN0wGSUIBNIbFtYBTV2fETRs'
        b'E7YvFfm9xq9wcuaaDdE6HT9wsEnbqo4oQ2c26vgUvA1bANI5YGGlY02CPMAgoRLVSTJl8lBESiZiOIvk2qSgFLY3cMrasKPJFBTCCcsEZRo8m30DKMQpN4QdCVyTKcwx'
        b'ObiwPeyCN05ou6Mr9oU5bIFwj3VC0BzuAiUKvnuDgrIT4jLDqZVoFmg3yq5BOZ2hnBOUOg2+7o65+VZCfM9wJ0r3YbgTwB0LKeGlNVkhpSWcAikl2Cugr9ehss9PghLs'
        b'IDzlZ27gtqNksxm+slG+3SCVYUbIDjnoXwZt8GTHJ/LmBOE5HGt/mKc81sC3SeHEBEMNUAwn09vENDR2DEShzAUT8F1QAHib2JVj+mlkpNXGfDnE5ASpPyHP/TAO9nAG'
        b'lC5gvwRNKaigk8b6Ad6fpRp3NXoiaJgNZPPF8d86YOn1b8DW/lGcb5zVw3C2lxJ4djLcVTCUzsyClYSaXPBLFpmDKSbmxNxLmQHbTeMl0Sk4hWS+O34n2skZlVNotVg6'
        b'6fsPLZZfCfpiccJQ5+iLJSV+scBbEQcvLMEeNajV8sHBy4NvJHrCiW8KSv4/hU0wGc1h/KXCoIsoXhi0KGuDFtI2sgahNDZ5YLlkjOF8crhbuE+4HyyC9EoT2raC6Tu7'
        b'yR5G0Tw75JoQtIe7waL8DUy8pAQuHTdmEZ6d+Bx00LKDfIIJgCIm6ROYBBbZu6B9DFd/u88X7htODHeT+XAf+O8H/z3DAyr5cCcsJ9wTF1cKoJgQnxHmw8nhZETNqiy0'
        b'uE04iWExdQpaoTWJMOHhHoSlEXamcU3OsAsQAoxxduVg2SQSopAAX+WTo7WVlAM8k96sGcW8mky+TyDWHM6FfJOCSeE0SgNAAWqcFM6iUJYe6kuhvnoom0LZeiiTQpl6'
        b'KMOoK4W6UaibHupDoT56qB+F+umh7hTqrod6U6i3HupBoR56qBeFeumhnrG+w1A6hdIxVJkEG0QBovhBbiuCTgQE0NZw/3AitDg5mLxd8B8LSnS14JXmS1ecL5AH9H8l'
        b'2kvXW9OVQ11I6NPOOM8gV5EMXEjY+wjAKT4vKGF8UDJs2LTYQu/0f2Xt5hT+G8CP/3kYVYMwamMLjEIBS8GqmwI3i06CVi6JtK7x95VkxbdobTYFlUfNhq9sNCLuuCg5'
        b'UC8bzZg5hFTRDtDLyXf4+0xyOcRk3iVa8az2G8nkEJHebwXfDNU1gm/MqidAMCCew1YdvpnDXBx8E8Mm2tQBbQnbAO0HuMaE2eMNurSPq/wLPDVQl75tNiwcsC4VsUPa'
        b'NMpqNAp9boclWCSIgQgAll2sIetIThWwARM0MhnNmFK8FKSU0MTEsBl3aOiKJABUiQi2MYRS+mH7tkE85poQduEixM4iICaaAMiGbSMAERzTVj5/Y7x8PgBBAKcA8EX9'
        b'ORlyIVlz9PhE+XGtMML2O7Xz/+x8/shs8HBoJqMal2Sx891FVF8qFHGG2VvPMHv8YCxHdBNQw3ASosKxwZD0wRhAg9EFEDTRn09vMJyKYfIlMBlmnQO1m+mdfVtf6jpU'
        b'/LekkfIEhtrp+OWtOh5QvrAlHTV7Jdhv6oKif7+BiPNYogRoJe7OJuUjdPqJcBb2NRPsPzDYTZZGO7IkSEHRJXEBbtV5I290WUpfpOH39UeIQHeGkoE4Twl1rbTovoGs'
        b'cWVYEepvx5YnYpzxNdsTAdOwVQrLWC1NeI3lbkN2CH1ZDl9CHLyxxb6M1QGQ1+EtPoba00KKGSaOecpESgWaC11OfjPQPAa6M0KDnbX5iLUuN4jtIoMHKATKlf9A+vI9'
        b'/kdbLYk6q/zu2vJK9woF5cyV4ZaYepCkG7SkmZfDEwn/T3lMSf932hLs2MDJcUsoGa4O2hxQAr8fgH4zWkkScIuwi3byLwPIq80hplkw1mVx6qxeF5+TxrgSqzF38jIi'
        b'+lf5lRcw7qd4+RleXmSy4GipyK+8RDoPjd6qcuVleqwpC9yo/JxUzOHBU4ZOLJRXSI+nSlb6UKZAsUfFsnKg9W8s86MietSi296KWvzGw1JvbXmZ15+T+K/pspwF/wa8'
        b'+v+9/DOHGzgnn0PuWRTnuSBIlx9sOE1pdPiABw1tDz6suvWQtj9Hu7H//M+s/8fCZofoskjijCtw7VVW4zXLIYmDuuPTmEm4LgWrmQhLQaB2lqKO0GmO3Fe447l+bre+'
        b'ImvK6mBZBhRlI89Uk8ngAjtFeZ7W3ZSVFZ46tESl4GkhnqlUlDX4PW53NMXt9jfUEbcQWWuogwOxCe6WgPJJa+sZcTq8Y2pq5QavB+3rMXOqEgCWZAFQpvZOdm7irtLj'
        b'e6OjZmfsVOn/AOsumPM='
    ))))
