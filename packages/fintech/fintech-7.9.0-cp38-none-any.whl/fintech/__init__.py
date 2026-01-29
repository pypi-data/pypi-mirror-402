
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
        b'eJzcvXlck0ceMD7PkYMQThEFr3ighBBARcX7ttwo3qglgQSIxoA5EGhQFDEgh+BVb8UbT8T7tjNtt+dut7dsu7s9ttVe2+7VXXe3fWfmSUICWG33fX9//ODDQzLPHN+Z'
        b'+d7znZlPQKcfGf6bgv8sFfihA1lAx2QxOvYgq+f0vJ6pZJuZLFE+yBLrOB2/AWglOpFOjP9Ly/ytEqu0ElQyDFgITJN4oPdZITOXMCBLxoAyhU6il2X76qT4Kaef/ejT'
        b'Xy9bzywEo4BOkiVbIlsEFgMTuwh/mwt88pU+D/vK5hXoFbNLrQWFJsUsg8mqzy1QFGlzV2jz9TIl90CCwXzgQx4E+nYmJpfx6A2H/yTO/5Y4/HCAPEaH+7NBWs5Ug0pQ'
        b'zpbJ7EwlhvgQOxfY2UrAgDXMGgIBwBDkKbn0XM/hEeO/sfivB6mQp0M0FygV6e3gr+T1PKMUPwvLRAD/X3QgSRM9v3gh+Fwo++3kFtAtdLSyeAId6wAOLo9zQ8g8FsL8'
        b'zhC6KvaGkE+3ke7Hol3auWq0AzXOQ9XRC1A1qo2dkzgvMQrVozolqkF1cDO6xIEZ88Xo3FB02mC46MtYVLjk9KDDX2q+0BjzvtK89Fn0lihtovYrzWs5IQuUuQV5RrZt'
        b'fVjCErB+mcTy74+UrHUILoGOoV3LfHHN8BBsUpG602zqKLQplgUD4AUenUN7kqwDcEZ42IhqYS28MQc3vjkF54P1cLME+Adz/dNglZnMrpJrZyOVZoKdwoMkPgyckGcu'
        b'LNObFHkCYkxq99daLHqzNTvHZjBaDSaWDAKZMxAmZ/wZs9xVtIVr5/Nsptx2SXa22WbKzm73zc7ONeq1JltRdraS82iJPFoYsz/57EsepJJwUjFJAvcDWTHDMjL6tJGO'
        b'w1ZY458SHZOujoI1Ga6hTZ2M6jgQPVKEWuDBtUYChH/ES8xrIpDwxynl0X/WbSkcDij6fGu2sdYpET2BZl1Of8m1WCf6/HEyfbszYQXzNgsSK2I04/svjBWKvK/hAJ7r'
        b'Kf9mNamDFxQLidNDxQDDWnBiiMb4yYAFwBZLgLsCj6AKX3giGs9INdo8Ny5zKGwTECEyRh2JqmOjktIYsHSJNBUe6q9kbApcKhFVwXpf3KEUtSwSbYLnpNHwBA/C4S0e'
        b'7l4JN9vIPC5DVeg0nsfNsWTS8X8JahgKfDNYtAXVoUZbX4KV8HQYeeUxz6vX0pmemqrkbD1xFmMm3JWiVianidBJWAHEc9nQsOG2fgR2B7wgTqEDmpSkZtGNecAX7mTR'
        b'CXgBnaIgsPDyCFSbgTZNhoeS02LwqMNTPAiGlRyq6AG34BYIELjeQ5NSkqKT1BQrRcERwB9t4tLhbnjDFoIzpA6GF/B7RWSSCPA8Aw/A06m2/gSCShm6TXEZ7bKnpSWh'
        b'emUSrh9t5eD1mEA8WAQveCusTBkxErZl4fcpqCED1xIwkBtvKXdmQFuH9cAZJickJaUJr/3RWW54CbyJM5Bm0LankcM3EU9REapFdSm4syBkbV+0l0PH1MW4F87RqIN4'
        b'3qLTUUNSdIy47wA8GhdYdAG1oUs0x9yl6LoKNaSiugF4vKOV6mQR6NGfQ1vRcXTNNpA05BiCWlIy1EkqPKg1SdHJsTGJfvBgmhhEAxHaNXWMAG9jn1EEDlVMYloMMxTW'
        b'AV90iEVXREE2whrs8DI8kUIzkP7MjkzBZN6Ah2jz3NlqMZiODqTyYlQBd6BmgT72ogorzl6TkTonMjEVNcDD6FR6asZ8kjt6nGgmqlzuxdJYT6Z7kHJxB4N5JefgHSKH'
        b'2CFxSB0+DpnD1yF3+Dn8HQGOQEeQI9jRwxHi6OkIdfRy9HaEOcIdfRx9Hf0c/R0DHArHQMcgx2DHEEeEY6hjmCPSoXREOVSOaIfaEeOIdcQ5hjtGOEY64h2jHKMdYxwJ'
        b'eWOdPBlU85gnM5gnAzdPZihPxlz5UVIjAP/17cKTHem2CDIcTYvDPLkF3KF28mInu0BX4AWKFsvQAZbSV7raCg8p1bCasMlgDQfPwqpplHjkyGFBtRjvOMCuZSxo05RY'
        b'eNzWiyADrIKH5/qpYEt0IsZquIFBlZMx5fYmE9zAwqMqpRpVY1wUw5NoHaxnVfnzbaHk5fZcPWwdSCYsOoYBfBIDb2VPpOUS4BFMM7fnpGBCI698GHgUc/vtFBR009hj'
        b'SgTmK4kEGj6RgRfytJS84AnNOFWMkiXkyhSlZKFGtIXCKAlC61LgSUyYYiA2ouMYikjUEGfrQwrVw11oA2ydmII2Icw/cHODGXgG7YK3aFmMU3AdRUIG19vA+MIjqfDi'
        b'QAonbMI4V51CcS6aAeLRsLkv2ytkCC24BjbDrapkTGYZuPNTnlGx/pg/7aLvhviPplVGqnGpEtgawg7H3G+PLRi/m+8TgIk7EvfCxKiiJ6GjiwQ42lAFppbYZALGTgLh'
        b'nlkl8BAlpHnABwPxFNqDJ5jQtBTeYaED7UdHhKJnwuE+VJsWjVHezsA9sHoyOg8P03fwLLpRAE+hTeQlvMDA3QvnTYa1tjBS7jjcj3anEEaA6nggDi/DAydDdVJhHo4s'
        b'wtSWCM/gguXMJHhylgadoTPrC2vgLcwuYwiomxjNwqfQZniNTtFMDTygikH1IqGx4/yC4FI6DehZuCsOMxWsQzgESeEzioVb0D6Mo0RSwE0T52CeRCBRxSThQU0XgV4F'
        b'WOYd50dgjeAsBRgeUMSlqAbDWiJKkgl6+IhZuL2QzWU9qIYQird6hJUjB+NWj9hqrAyVc5gUWTcpcpQU2TXcz1OPuHRD7PMfAsskAtyLvb/UvJJzX1Odfx//59+sm7Lb'
        b'J3EkY8hT+D2/ONp30boJO6rq6uT9pnz34F95jeMu+2/UiH8dCt4W+e9puaWUWMkwTER38EhRQYfqM5SoPknQaUIjeNMEbsloKxnLkWVzOslCIgl7Lu8fH2Ydht9PxYz1'
        b'FiX46DTMTmuc2RoxzuOsA2ATj5rgmfG0wUjYjG6QvBmITOqeDNhAMslQI57ATLSbZkKt8CY86cyVGoOnnzTJcQBuH4iFdKOVYtpheHaOSp2I5SNWY9FF1qyFG8ZNsw7C'
        b'78bAY2g3hYiIFSJTRkeqkwXQI6JEGeoUp7bWSX+iqVR7audXai0rqF4WSOZiLeCljPDrz8gYcw9XbiXfzuks1nbOYs41EwZqJvmVbEel+DNBVXNPV9208AZ31RXgBy/d'
        b'jGLeGXgyAJ6DNYTMUIMY8NGERI/7PloxHyFgHpvH/q9qOd8d3t2RjhJZyNi+0XzzS83Su2881/jC+881vnix0ZzZFPSSf94fjQyYMl/U256BFWvKzS4VwaMp0ZGYr6Yw'
        b'mIecYuU5pfBOX0GZ3oaOT3VjVUy+hy6NX10VhpbtfmZsVoOxQ2NeC/wCGXMo6NCYucKc5d1PBdaPe7tngRSp95iFv/t7zgJVKNbNRq2YmZ9WUQ0Ms3IzA+/AXfCA1zQw'
        b'zr+5LpjsZGg3KJl0AeowN/wdnfA3FWYX5uTZLLlaq6HQ1ESKUqbC2pRkeCrRRXgV83Q6QhnJKnV6eo810VSj28wBFbwgwgh+Hu17AkDyfxIQHxcU+u0eMBC1DO1ZkoW5'
        b'Lm4b7itPTydkFowqOUy1Z+HtR+NhAsFDRjARHXyeyI2N7GOxsaAzNjKgOy4oTrcRtoO2BcGrsDaD6oSwJlaZnJqeloz1tBh4nRNjHrBRDKumB3tV6OLVBAUto4GLV2M4'
        b'+f+FWxM4Zd1RzbrGcpElBSdoyh+e+viB5ivNfc0XufJ8aZ5GG6l96bOothzdCb1Gd+KdFcH3NWe1BXmn9Se0Bewre0YcAS982XtQ70Fhf9k5qOImZt3x4L3/+DWcT1Yy'
        b'VqoTH5MlW+CZxHRsDDnRIgg1YpJq4LBldw6dVjIC++E7M7lO9CTKztUaBYKSCwTVn2XkTCBmdWXhlgJDnjVbbzYXmmMmGAtxTsukGFrAxf14rTnf0i5esZr89yC7LrYp'
        b'ayZYZe7vJkCiau73IMBPgz0JcBRBRNgyhAjx6lQVVjqpVY62YCuqRrUSq0jpWD2Bl9FWWCvJHIsl+mQfdKUc7jCMDuvF0snd//HzX2oW3W2EVxvPV7c2nKtU7mzed35f'
        b'y76I+rFVyqprVYd3NFde29hc2RIWiXb5g88nyqZWDcfjS+YRXk3LTckYA29hnYotZqaiqr6uERV1O6KdhtXXY+jo4MqEwQ2XMTwbKDYr3Nn9Hj1LQe7BItl3eQzWgxDP'
        b'wSKMGetnZyI6jRaL1Vt4pA+8zsMTi8yPER6MA3gIj8eT64YnU1pE6bZIAt66PKx112LT4WhXinWRawA6Mc8Q1SuctxAnwL5nznbMn1xyrnL4zoFVzZXD9w+v8kkcse7e'
        b'a5otoiG/useCb/fKhr+tU4roxNmx1NyLjUUGjFtOJ25jH0owsB49iw5RrSI9erpenS6InCB4kcNKyC7UYsU6K5gJD6+gmkOMOnIxaotMVsfAhgw8qptVSfBMpKCLLMqW'
        b'5vWCjVZiF4UVOyv1zHNiJMkWjrbzcD08DjfSnOgcJtNLtHLa82J4k3Re0ICGDBb1Q2dg209JPj+bKbdAazDpddn6klxP5WQYRipG7Pw1D3QVU2JhiHM+Qi9hzIPc6EWK'
        b'HPNArw+8hCG1/y6VwmMqLbpBnQWJuCt1KWkYzzALEoOIMlEGhr7SCx1cGEa0NRezpdawm9k+iYrSxUrlQXcqijTdSLjXuf4+Ut0soNCvfb3UGHMu42r+aJ/5TzOAynPY'
        b'hFp6q9RJmGU0DoKXABChQwy8xKA71M8lZv4SsC2AiZyy6Gvmh94rZfsE/5RjNbbseVD0tl07IGTidCHxL0E9wBDM1t/21UwoLBkDDBUrvxFZTPjNHy98mqLVaU/oT+i/'
        b'0hRpq9Un9F9oTmq/0JjyojJbtFkYnS82BkW9KA3xPallT25p0Z/VntaGSr5g35QP0oyrusck9grv+Ze343p+B17Ylbmob+/WFuaV1jcOtY98e0RPMfPOCPHIojzMG7P7'
        b'vfKSATMralo1ieH6iehQituTI4WNbGGP+O75ymNlAl+gtRRQBFMICDacaL4y+itowXKWx0KCfmLMgzsQTmDyHQjXffuMkI2iHinc6oF6bwZ31sPgabgdnkbHcrB9iLVh'
        b'PP09iQW/G7Y8xk/NdPJT/wIVhAyCTxdsk6fbCGsO7oeV8q0cKEFXQCyIjVxCcYPV8UAKAsXcFI0xIcAoIMxvS4jr836CFGiiJ8pWAzPRz7p7tDPZhlWq3wLLJvzlzFvp'
        b'6tdUwTAupOojy18K9sjsi5mU5xYCmUXy218rkkO2nhw0aNGMtrlbmi0vDPumYMOuH8uro8ywomevCZvF+5+e+PYHscMO/d5vfdBCPrVMrxkxbc7imv6Bw7/809Ifj2rn'
        b'Dp5lXPBC3pUPvz7ZtHpJ8Y/Jqpi//l39Tsy1u6nwe2Zd0568B/VFBwZsqRn82u8jlL7UskL7RikxB1sHL3VnM3JSWCuo95fnhFuilUq0iZ+aGqVOcnnUo5aI4J01w6xU'
        b'uz4sW4EupMMzacDqfO2HKrj4nFQr0REiRBanYbojxdvZjk6ijRTr4Sa4q2Qe2qGKQdWohnhMYAOrRgfmULMUg3hlVhezNAtWdlilqB5uozXJULNJlUwcS6npIhDX1xee'
        b'Z9E+CbxAQUEbFqWo4EZ0OiYpOkoZgzZjRRyA3gr+adgMb1PhkoBOo2uCGKgjso20geG8Tg3by3BnkQDwTdQWK5hEMxY5jaJStAfeogYTOjkQXVKlq5PwwLEA69nn5VJO'
        b'GjTAi2n/hMkqLrLlGA2CXIgXyHYGi83VYEykYiaESggWsD/yLH7+wHP4+V+ex8//iEViTNhyQsoR7jp7ddtcmJtuqUjzoNs7XlYsdcKcwqLxhioyb00a2oQteTG201tZ'
        b'WFEGT9ImcsUehEZ8VVIXoQ3iiPFiZ8JAubhaYhdXg0q2XGKXWNLL/O3cQWAXNzPl0oXAFMIDK7NCZk5gAPldDEyhi7DCbpeSknYxqWMC0DGkrPmfdlHRIgMoF9lFB9lm'
        b'MAMsa1zKlvuUy0gLdp9K1pxD2+Lxp2N28UGumdZxkKd5Q8p9qzmcz9fO5nF2WQPDgFUNpim0hBxDJ6/2sYsrGQyvrFpKPlUytJSUlpJ6lHreLjd/Vi0XcrtgxOl/W5XT'
        b'yJqG0Bp9K9lGxqyoZqrBCjH5hOEQ6dhmRsjdyJj+Q/MxVnEeS/MmV/s68yZXs6Rud843aU4xzVVULXLmwp+8cp3WcQclOl4n2gCqcX8rGTzCfjrxQYnd76BUJ9FJm1mS'
        b'YvfDZY/ofOx+oaDczyFx+GKtkdPJcDmpnSPlyv1x//0rGZ10BWnxTbu/zhfPhr9pkDudx+nf6uSkRbt/MxNK3vI6v3J/O9vImsdheBkKL2vurfO34xK9MKfOY3G+AJPC'
        b'ztjZFRx+F6cLIJ+d6VJdoF34NMij/DxdkFDenYe0FmAP0AWPIf/9cJ71dn/6DND1sPvb/Uh95J3J3x5A3hTV2f3Id6swv4G4F4G4FyG4F6z5G3sg6Z2uJx5T1nxb+IbL'
        b'vI8/Sd3p7wrfSDruZZAuFH8Hul5VbBiwB1H4A3Hrvav9SAvLZfZAFwx2rpEzh1gZe0Als54xSa2+wienGRqWPu+hxKi1Gkzq4Q/ZaIWXOGSdIpF6A4gHKh+T1DJZOWNn'
        b'loMmdhVPxJ0gtZl2aXa2SbtSn52tZNvZmLh2xtrZUSCbYDRYrLmFK4smsYxTFopxI2V9cwv0uSuw9ddhIHZkfcgpCs0PmegHBLKHssI8hbW0SK+IsHQBVeSifYUL1FCy'
        b'9m0nUpu18NUY7ErGCXZeB3CYOSqp1Cz+CdZoJus/YsbpFSFQy4CZdOBhgFZRrDXa9AoMWWSERUlF8MPeFv0qm96Uq1cYrPqViggDeT0swjLsYRBNIB/dSTx99vDI6Sr9'
        b'0Eex0maxKnL0iocBeoO1QG/GPccDgp8PBHX8ITPsITPooU+EZUlMTMwynE602IdB0Yr8QqtrrMbhP6W8XWQw6fQl7bIFBOCZxK7ESbhVSzufW1hU2s6v0JdiSxy3XKjT'
        b't/vklFr1WrNZi18sLzSY2sVmS5HRYG3nzfois5mYZO0+83ADtCZlcLtPbqHJSqwLczuHa2rnCUK0i+nwWNpFBBZLu9RiyxE+iegLkmCwanOM+nbG0M7hV+1ii5CBWdEu'
        b'NViyrbYi/JK3Wqzmdr6YPLmVlnxcnIDRLlplK7TqlX6Ptqif8IFVyjQ3rkpdKPkeQaiNFMWI+sozRB76M2KOKK48/pUygU6lVs6EsDL6PZim4/xsKP4cjlNCmUBxCP4s'
        b'xqmh1AHszwSyRJ7KcSr+xhLp6c8K6nAw60/dxL2ZkB9xiz+ybAguhSUsS5d1F6KT8AI8n06sqDTUkB6djNWabG4s3IKueS0sSIEQyEGp4mP8wLKLtYODgMqjX2PZxZXz'
        b'ds4SvkpuxRot+TNgWbeXIxLOztq5CZh6zLOxNGRWiPF/LD/CwEEW80wuDDRjSYQlE4/lAU8kiEVn5/MZXB+P656NpRhHpAuWhLsxDRI5IdKR+kQ6HtfBkW/4P5aMpJ5V'
        b'BYLEMR/T8UUndERSi+wS2pbY+V4ktE7rYScA+p13fucngFVyO0s5migdk3EqmUg6m+nkker+RNKUIvMUMsecRW9t57Q6XbvYVqTTWvXmaeSttF1C0G+ltqhdqtPnaW1G'
        b'K8ZakqQz5FrNKa4K26X6kiJ9rlWvM2eQtGRSWPwYRPPw35LIDV22q95IwluGUjzjMb4QPAsUcIFgGzWd5ExvNpAJpPhlIzbPwuxxziABWBNLljvH9ksTFihV8IoI7RgA'
        b'r3axREjbRLOibXVZXAZkeTnP12Xu2BmXr7KzleTWs3T4UU3mmanBUn85KArEOIYLmuMxXvjhFIbI0krGF5s9VFphjMAykKnmqn3J5xri5uUxIKR5GQZHnid1O1J97CzB'
        b'oO6sKoLWZESpH/YzAgRvJ6oDKDuEG+bIZ6o+zcYIz+LGMGiVzAqAwcKf7BiQcs4USsETY9SeRT7hFJ6gmp2jaaHVRLXBRJCHvxOEp6pXqJ3UOq6cs9M6cb6N1WKMphxW'
        b'bXiTnHzG6fSbnTcbidDB5IPrsPO0vBGrnDFY5eStojwWq53vM1idZECZHA+TiAhmGiKG09aIXCFimDTwsDUwTk88xjFi+rZLirVm6jnl8jEeY2ZqXrHaPJngV6KAiR3O'
        b'0jnkQRE3hyK+3mxWSp+YOXbgrDybssUi3PBKS4obYzF2shgz/TGGYv7HEt4XSrmlnJVjTA7FlkM4Uxanzc3VF1ktHUJep88tNGut3o7hjgawYNaQpkk/ME3TuCSaUEAS'
        b'fH8pm+faJWTYMOkKVWrd3fNxAzSNcUU9cQLX7495b3hYWfij++DSJbJJdcvJZ9kvkkHZbnAkzsYmu5QlwCkG0zXyUWa/lNT0dHWkEm1ETWLgG8OiI+LgLq5UmfO/JQs/'
        b'9CALa31ZLCV5icunkcVt8xG8HJj+fPNENNpRWslk8e50gT0Q6pTn+dAoSPJe5AA8yBJTL66kPcgZsTjLYNSnFmp1evOjV7ipI4/F1WL+47Fqwj121aSLI8/FjboNAdRY'
        b'+lrgmcjEtJiktDnEvM9ITdKgO+pMVJ0xN5KwSxqHA9ejEz6Lg9Exg+nmORFdGP+Lqe1LzVeaLzQFeRtnRO2IpCGAL+WEkADAnK80v87JuvvBc9teuNjY1MSc2Dh2f0TV'
        b'wJ3rRvqBkWd98/qcVYoEZ3Ez3Asr0AVUlz9DTYLNVjldFOE2Hm4MhOetBK+nje7VsTK+AJ7s8FGsRHXUdWCBV9Ex90r2KNToXsweGI2aBT9IfRk85rGQjWrRHhZuCELH'
        b'rDPIoKAasqyz2h24RGOtktAlVLM4FA+KGm4iEMSiTaloM6rDkMAatBlzbICz7PJDzUXonHOt5jH8AdsABpPBmp3tuRa0FmfDmo0/UxbeBUliXAXca0EWvTGvXWykb39i'
        b'LQgTWiH5bHK1bV6JH6sIpRA3AKjAv02ebsCfavzRqDpOQFUOUwARluI8sRtd+V+2yNcVXSXpdLF0CDwW1xFbhho5HVwP/OFJLhA2a2zDCUa19YcHyYoujWQlWVETuiaE'
        b'omH8dnrSLmUCsDRSgraF5drIcgS6CA+ohFKRkRgBExf2VKNNsGVeZHIa2hwdk6ROTmOAKcBnYojVRtg5xpWrA+eqF6DLfCKqUyanpeLMTvrBOePhDvGQgGGGXduP8xZi'
        b'GYrf//rLN1ZqXs45oT+hXXR3J1lrWXRsg7KqZePUvc27ztecr2xZxL2ULz6/ove4RRfubTJW2HeEi4e32n0skukSy8i32B3+O6rqnpPvfQC+ezn4wcQ/YxKi7qxqeBjW'
        b'oVqMkWLUliYCfH8GHlpptRIlGF7Q+Krc7jQ773KooRNor0CAVXA/PEMI0Jv8MmEdocD5RhoEgi77w92oqlwVo05Us0AMj7BxU+EG6qrMgHvnpaAN6THJadFJsN7trRSB'
        b'iKdEWeg4anSt5z252ueXa9ZjVTN7ZaHOZtRTOglx0ckz1IfG8k6neNmArijrVdpFlIQIMOUQidZBMY9eYsS0Q8lmlZt2ivCjxIt2NoV60s7jAOlCQL4uLJ/hIiBPHZPx'
        b'0jKfhJS6LBQKvoPOpOQvkBLaHab1JKUEuIsTSKkcOqhsiEY7V3tRUlcqUuiddISuwX22GIJQOxeaPAnJRUZwHTzaiZQGwsafjqvQeQV4KJl2Jq+zu0Q6wahdmaPTTtqM'
        b'S5oJS7ItJFCcHAqbLd3wcsLJ0ZYUeCYxDTa4cRVtJ6vd7rVubkSwRQf3wK2ZwegMgKfRxiBYAbehehpVPAUdyna6zDHZRRNJs8KEZU0mNxybGZVeXSLeFmIFUAWcSE2n'
        b'Hi/C000n2q3Hc1S083iCOfcE83SCuTX8oyaYBR5GhscanW0M/ly8eEqKCtWnxAhxC3MTVSRUcj7mFwfiYtVK1JCaNN89lyIAD+pl6HZxIl1Geau/BMhBQT5QaKKnxkow'
        b'NdDkgjlSEAgSAoBGE10ijhCWXPIl/cEEMHtOQJzG/rucaYCiQXkWPOrVuhBTjrUKGmQTnbQQNWM0WLnWpzc6v4yiG9o2ErWQNQj/hXiy0uZEopqFAked4wZzPkY3dF6C'
        b'zqGm5YbfHHgTWOy45OqJcyfWDZehuED++/QtaZmS9Tf+o5wZ8l4U9FkqXfiiKUe+5E+vN4VfeGfEa9GD37nbOFq87NrrW3TPnpudfCS3cHfj395gXtZ/1bZu39i/hi6Q'
        b't5q2frG/cHt79aWPlnxS9eCj4d//Kyt06pKIdR81zPrDzvj1yW/8+GnNq58HFE/vz28IVEopF5yRjy53H+CH9jMcuoO1jEFUOmE6qO3Kbm1wcwJmt8FoA13ChnvQKXRb'
        b'5Y6cxkU2YxTeSfSOWgkYOFcU/LSYxvAtQJXPpHiw3hnwuAf3neRH9aeAfqhZUI72Z5JlSwE2P9TG9Z68gi4koWd7LExBDc7ldTGsU8UoxSB4DYfVnFZ0XJAl2+LRVVem'
        b'jPjBuA3fMSxG+a3oLK1k7ix40RkqkwwdHtEyHGz1R5Ve6yu/xLDyJ/Ew2UXmQit1KFCx0NclFtaCvix1MPHSUCaQDSaOIiaYKRvVlSvrS/S5Tp7cYaJ41y0wHJFg+3SY'
        b'iB2C4zGyzLVA6+8uSkWIFT92MS5pVkF/H4R7rucsIwO9D67z/cXMi+w+2DIWnRfNRNemwEsRsAXuHqAEg9D2kOWT4S0jAe+7/DD+b8Fgyre5Dwf/hb08PCPxHKBr8z1N'
        b'O5lWCVDEhZnCQiTf8luE5F0T/kqX7L8Fa42T5v1+2TVgCM6+zFqOkCKZVyLqbvnBuMCqP99LMv5qW2K8/G7vr+6C5oSwl61D9AcVH/wxcVJ4XuLoF4Le+fdb3z8/62Hj'
        b'G7IXN343Qblg2rBXSqa/VtKy+M/7+5h6BY+/3xJU/erylS+Ypnz9TdbSr77I+yH86z+WvPeD4el1D2bNfPaytWqTqvz++63LjCd1f/PZ/v3I16WNs+wv9kpKkwwP+6rh'
        b'+f/WbDl7I3jkin8slEWp3vjhi/6Ts05Hv/9qk9JPWGBcD48A7xhb7XTnYuc5KQ3C7V8Kr6liOLSr8xLkECGSFx1C+8we9Dte5GGvPA0PW6NwprF56IRAb7WjYJtzGmE1'
        b'njE8hYJlMlonXgYPrrKS6MgBc8xEsTKi2y7dCjbAo8I6cAtsXeQ54bAuSCDvPqN43MT2mdaZJJsjQNe97fJIyyUB1XsYL1j/vUK3aUWhZ7Gow7DDLXCnALBQgQT0ROs4'
        b'dHE83CSM5SlsE54RQngIdLjEVlSDB3M+Fzm1P2UYGRiRbwg7O3Adl1ElCXE/ypYgB7baCHlkL5rrFX2MeclBwWgrhXvpcM/VZXYStXgcTjqF7W14xEpD2reiK7jO2tQp'
        b'UxjAJAA81hXsIyIifrFDhBFCB4SYMw8OQrlQVAcX8nGrp6yMuCiJi4clsWihvcQkIo0NZMr6/SRP8lJYxc60Ds7j8/PgZs3FwMsEtOFHVSce9F+FpyL70+ApJcKihizb'
        b'mZCd3S7Pzl5l0xqFpS1qZFJtmbbV7ke20mktllw95rBOG1b+v6xBtDDtPs46cX20U0b8KGSc0X9SNlDCMqFyzE6pbXcLrUcVj+KnvRJYMA7eEsNd6CB0dHGcuJbO6RS7'
        b'nEN6Tse7Ym/zeB2r4zb4EGcQdfaIqCNW5Hb2zNZa8Uia8Cim5/Kdanab0BPww6n9O/3NeRKnYshXS7BiKMKKIe9WDEVUMeSJ9/PRRrR7pc8zRJDQpQxuiHFq/iPgYcGO'
        b'FjT/uFIlS4McVWiP0tM4mEHsywZUw4PwGdjgPQ6vUVUYHRiG7njmW402qaISxSDcws+X+xu28kbekoQzXvvH519qFgshhi+d3HC+8nzltV0GZq4kRbJC8rtpn/14PGtj'
        b'+MZBF/x3hBwzFiv8PtUPHzPy3bjnR74Xx488Aobn+4KEvweaJn2n5ClrQcfQuaXYsI0wdWLTseg85akzUuY7jVV4HZ6iTNWEHJRzrVkJj1CYU2AN5l1w09I0rOroOazn'
        b'X0CHhDivPRhpdrhYl8C2FINKRme5TFnJz9NcfPIwAmQT25Oyi+AOdjFJJg9heE7KYku2TxeMiXGXE8hG3M7lGi3t0jybkRJbO1+E87aLrVpzvt762HAw3ryGfF5LHhXk'
        b'sc7NFcrx40YnrvCr3p5c4aegU7LpxONO+IJ5NXmUkF77UhJdqbcWFOpoA+ZS17B0XUQuc4NCNPprLm+ulMVUTBwuEyajdR00LPXcDRkUxILxCjE8LkumBkl4NktN37hZ'
        b'4swPystBF5PJm+y8FnjcZAdozORP7+zrYo+51lu8yS4sXfBM7cUK/DULRrKLvqts2FyoxmLrvLUYXfIthvUBfsuK5Og82St0TIRasZVWZ6P7j66iRuqgqUlNR/Wq9PnU'
        b'Ek/C/2oy1K4t2zhDdciE6Bh4PpN6ay/C6zJ0RwyPPXaDOUfDSp48TLTbYORuOY2C0FFdFjqtgidS3RNHYtbQnh7zOJzSNptuAEUX4MFBhNaEDqLtKtiC2uChSAaEwybe'
        b'jAtsNPz55ieshaxLLn7L9KXmlc+/0GTdbW1s3tpS2fJSS+Xw2lVM46XGoJck53eN35nZe+7O0BGVn47v3Xav9qtxvUNbK+bFjbDGiUYeieObm2lY55tLg7dYxzhdaPMM'
        b'sB4bPHQ3HVYKr4vhaXZkFGwRNkBVwpO8SgUPJFImw49h4FlYl0dZCawogkeotwNtUqNN2UKWALiOWw7v+FC3cxC6irahWngE7qM7Fes4wI9l4Pms/pTTTMOa02mv3Tvo'
        b'NDxZmlL62J1TvtqiIj2mP8IBvD1ka0EuWVES9hbImLIozBuyjYZcvcmiz84zF67MzjN4mj4eFblapdzhJxzLjJCD0mslfnzUiXU0ewWpkUVl1DR6UkqGmqierpkemgzr'
        b'M6hTAv8XhHJnU8Y5MphRC0Org/sDV6IDU4V9Q7uwzXtYFSknwzpyNAtE2NbGuN8aToUT3BuOtcIL6PzqYnQRValWyaVFq+SreBA6nstXLaNyzjAbnbTgt+d9/Ir9ZP5S'
        b'1Laa0OcqERgSzNtyypcPpBITnoSHUGMKtgmEGZTCVhaeVcGN8PYQG3F/owMLZfAUVURrUqOSo+FJtG11dCRxX6SmO/cTzZU6N9QzAGPDBd+gqdOXo5NC8U1+WHveiqoK'
        b'n7SCHUYZqkJ7421EL3lqNbwDa4tWwc2r0WV0BbMYK9aZr2AucsWGezKXh1vQVrhOjPbTgclPGU9hfZaIdGwJ1aZKQABq4hSiTKyBb6DbCHqgK/BSlzpXo/NymRgMSeLh'
        b'kZVwE9rgR7ViugEW1qJLs+AFjIrjAby9cHxmkbBR9/qkUWhrhjoJ7YDnEpMkQD6RnTAB7Ye7Z1OvjxbdSfBVEzdHykKhtx5cDl6i/GwZWidB6wbDm2jbfBoQjI6GF87F'
        b'LQ8B8I5syNPoOOX7Z+TSwEoW8x2NJvrjNQpgJMzuP2WShDCAqVyhSZ2Q6fRj/R5wBe0s+aSJfjdhouDH2jtJsmgJS3Ma/yBigY2wSGz6NBKWXadKIRGn1BXVLYyFsEIK'
        b'D4wuRxeeMZw6dJCxjMEkMeG+Pa1xYjo3PLDqDyVrt6Tt+HZATcobA5sjIw4d5GSRB/sEKZsWvPLm7NdG+2Smznze56uNuUWg4W5S5ojfGw/F/+OZsj9MKJ0AJcZxGwcP'
        b'zejJ/+lS2SeDpn57qaFyTb/29yOMfLltw6HcjzJb/g6jWxOzBzUkrClcqFvySeiwHnN/vWH3P95+a+nLZwrPlM9527jk3p/HjTz7+r2Nf0p//QPj8evj1etee+920vdX'
        b'P69/teQPb/Xcb/lwIz/wwA+G96bOHjzvxWlvXfnww1e2f/PuR+h102gfy4FbUVtesk08+U+m19UX+vUfeP7V8oKEc8FJH+w/Vhbb0vfEl981DXsnI2W3//P3fxzSHHv1'
        b'YfRxVZ/mippdPQZk1Jmzc/75qTzmr9Ll1R+3vZwxrOWzyUuyjr/6hzdeKghf1rTk4zUlf92bN+Sz/vfuD3iQXVzFz1MGUPMQ3Qgm4cT1Ksw+rwyOJoyCA76ojWNz4U66'
        b'BwXdwUyinm5CEQ0km1AKl1gJFxo4s1zlZtfTsJl6dvTTlBvDo9iG3JCSGhWDNgwQcvgaWXSkqIxa/3D/yhH0CAUysWSVsJbF832mHDkE78BTY4JUGRgQuENJdQ8JBuc2'
        b'iynt0EgqSIaiLajJi5tP6lWaiipp4VJYI1Oh6qToJCovRCBgAodpuC2vX5lgUZ9ZjW6mkMVYXLNSna5mg2AV6JXKT8EC5zqVFlgWKlTwILrpFYkdgM7Qzk3H1HuJwkWc'
        b'hLyawch7Fp6BZ+R0UNDBaHhblZyWygB+IBMwBe5LF3bsDEVn0LPO4G7CfXEFajHcNwH0gpf5RA5eEuTgFUWSytjfKSapiCSntNCZgnXwJtyk8ozb9kHVVCGX9Xysr+xJ'
        b'lGkv+7tntwKNCsHMDiG4mIhAnoZbB7IyNlCG/9hghjxlXCBO6+0OxJDTYLNgutOChKX543R/NpgGsQWycta8wSV7W1gPsfjzrABayXudBOUpTx2bMsQS49BOcrKzlBSB'
        b'p63SMVgt3I5R4aySE7Yyb0P7pmMV8wJdCXQtA8aiU8IZJ3UzMXLUpsMzqcQBPKdMBHzhJRYdHQ630s3/umlLVBjlosR4Zg+iffPx5O5GTblcJy2vl0vTW4ofXU7cAO4z'
        b'N5hOp26wjtC8Xu6VDtFPrnRw1KDlPzqJG5QpPH4y9fkGi1VvtiisBfrOpz/FyLzyJlkVBovCrF9lM5j1OoW1UEEcvLggTiUn/ZDdwIpCEnqao88rNOsVWlOpwmLLEVwa'
        b'XlXlak0ktNSwsqjQbNXrYhQLDdiisVkVNKbVoFM4MZFC5aobv7CWYhC8ajLrLVazgfiXO0G7sEBvogAaTPmdYFztasycb1upN1kt0bQdZ5tetRhMuCcrtc5iuLcYarNe'
        b'q1MQEqGl9KZig7nQROrBsJsNJKDUG8RZSenzZk5PzE5Nmj4zfe7M7PSpaTOju6SmzFw8PWPGTDxoup8sPX/uzMy5JBBXa8TzZsKgFeuNpQI8Wve4EeLtNE55ejOJ7NUp'
        b'ckq7VDp76rxEWictqNAWaw1G0hGvKrRWPLs03JjOSqHRWLiaDC7ReckAWRSRUSb9aoXFQHCgeEzM2CjlOO9JmW8ylHRKUiuGLJrxVPb0jPRZSU9lJ2akzYwtKnWeNhXr'
        b'7E6MtcTaqdCa2JjcQlOeIf+Jcns2MSMpc+4TFYrVW3NjS3SPasErd5o2N2Nul56tiU015Ji15tLYqUVFuKyAR3NtRQTtnwyGn1+BNxUYTLrC1ZYukEWkZkyfmjp19uwZ'
        b'U+dNjXgiUCKmpqZS5JudmTErKXXmo0p5FRtHI+oUxLEyTkHOmSOfXCjkLIX5TDdFVuhLSTC4UMr5pVNBnaIYcy48It1WYLPgl0Jxd/6Z05Kmz6VvFAYdxtd5eoPRpC9Y'
        b'qTerk2ZYlN71kB/M81xx8FoF4TQY3ymdkG0CBBxXXTGK9ELMUYRZ6kw55MeQ50GemBvlaAlAeDYxh7Tkmg1F1i4d6eJ+9AfdBB6Q3ebPTDXOjXWF1WQuTMS23tzEZFHm'
        b'2LGwRSkTB6BrpWPh9imDxvYEqBGdkIfBs6i5iyQKdFWf7i2JgFMWMW5ZxDoC8gJ/xip7F2cqkeDhXXqjTsf5qHTvGvjbNTTK6dt1h0b9olNDSDNdt+SKnMdOEP3IMKjf'
        b'04zFTCT+hD1fatSfJWrlefc1DzQr877SJGn5pgfy1+sMqfeMM7P61Sm+S393wmX/d62KD597+zkQbMizaqvfOSX68pS2UQe+1C/Pe+2z6E05OrBHGpp9tzXwtTZt5MXe'
        b'ygeaZXevNq5raq4M002L4/LFYK+03/dfQSVL1cxhT01UqSMTmX50MWs3q+6DDgmBSpcmwzoVaiD2K2+DO5MYVANbYcXPDw8SZa82a4uovte/Q99bCzLIVoPeVJkKZEIY'
        b'Md2SV6Y0O/UGjwBaFw/oSCE1Ok82ESLVn3itt4URClAdz4EfqRgyS2iHjlcBLnsGCtkmEnVtrxnuUTmpYOY8tXDegtdpCx0K4MxgZWwyVrpnwRMBBnhn+GOiRjnq0vx5'
        b'Z210iRoVge78epJ023T8Ocd36si4+BGjh48aCa/AVqvVXLzKZqEeh4uoDV1G57EhciFAKpf5+/j5ws2wGtaxaMfTAB5BV3zQGQOqpib3woQUsA2AhBfDNckney0W7PB3'
        b'C5JAIwBFA40a2YM1Oidin5lWzFCt8787+/f81cDgijg5f/dGvLiWub1+yncvNHHRV/2lIfdnvPO3sK8zlMvzB/frtXes7uXUto93rl71XaM2OCJp5H/8i0bVf/TuasMr'
        b'/zwgEr/ls/35t55Sxy8w3f91wNWjIfqX/41RmMzbOP+gFNEaTzOudA3uJVGzp8DKTKyEY23cTM7tcjrz4FnZT4WSPT4i1Fxozc4hLiw82L09UXoZQelgjMxSumemLPqJ'
        b'kNlZnWsl0b3z4qdjRWmODlTehB9ZXVD5hNe2cbIXZHpMoguRH4XGaDPvxmS0KRbWZIwYzYFiWBsYA6vgCTrto8M5EB9KDunQyPstn+V0KlXAbavRVoyIMSp0A8Qk9qR5'
        b'V08Wg3/2HEBcNfL2oKcEvOlfIgJ9DT3xHGmMPqUxAt7QN3/I9AGLFIOJY8j4jSlXSHx6XDJYNEzNgEBN8hfDVgiJ/wZBoMA0C2OfxljFjQTUeDKjip5zsfm0bf6oODzz'
        b'h9E2HogzGXi6DzxIS8Uu6ANOZxZgoaSZ8Bv/AUJV2WXnmYoVf8Ok+cfV7wcdTBXOZts+Et6cC3FdaAeuj5yoxmmYSePnCc6mwzOULkf48nTiYYJnIlF1dDJx9BPPAA2E'
        b'QptVxG8Ba1QyZbw/jc+IfkZMThRUAPEh6b3e9U83A3pKg37SUKl0cdFQRpOaYs5Vjyma/evR/tYgET3TDdNomw5dwDIlrQgdBmnojLM3Viy1/vjMF6Q3wZNSWKE3i6dP'
        b'BhuK5kjA7ArzogLfPJr4636TwE7LQwDiNCO+GFAm5Hx1rprR9E8SA0WFZedsxUSaKLe8y1ws/FYCAtcVLnrm9DM08dbwp5htOaMwiq1b0XuISHDNvWcMYeLSh+LEivLe'
        b'U0PVNDE+1Qq+nfA9SSzeOXnRKGGrf+B8xjhvjggEalUVtiyh9XvLmpjI7DQ81RX5vadGRtHE4eGLwdXU8yIMUtn7A19T0cSPCwcxqeanJKAINzRknNDQH9IGgBkJGClm'
        b'V9gXPfWNL0386/w05mDURgYXX9G7IEKIkJOFhDKLchfxGAUnPrd2sNB6U/AbTN+SWRKg0Wa8FTJWSNyd8Tx4bXggh/EyqU9EqJCYEGUH82b8AzekCR3m21tIrC77APwt'
        b'ycLhxLBibpWQqGP8QGvWCIAT5c8uniAkvjl7FaiYuBpj+B9zQtLCUg1HN4YzloN4Mte8JZ4/51XT21MCvypt//3rZb3Y35dwG/JLqrkBjbk/aAKm8Fe2xO5Y8MruHrvH'
        b'hn36suhfzw9v+9Hxm4/6/vYTxRDdtRunls79cKL/4guyjX+4uXiqseXwr4uTxvzZ//pM/cDm20cntV1fskAWvvH8/RfeO9Aw7d1Np6J1rRHL9HWWF8fmo3t8j3+ta6zr'
        b'Ec6/Oack7FTTzY+jnwr+9PkzW3JHv3DxyKhLI9ryN9y7+8rLU8d/NGi8pPzZCFXRG8n/qJ2wovWfmxemD/xwdp0o6ZvPS2U2zbIzz/z29KLY5ZvmB7ZeunkmIbT16a8n'
        b'Dfzc8qqf9lKD/6vrG8+0bBH9O6H4/T9X9v1bYuVz/X7/csKfUq33sjdYW6+Ol/3+1f98fXnP7cwJPT9E0QX7d+Q/P/CbS6/87mDRANG7CdNq/Bq+AwHfSYeV1A0r2ZR/'
        b'855l2HfrCx9uO176IP7p+fqXzv0p4C9Je4//S7T/q4lfp48qT/oi7PuH6shJX90qqMpIuPOZcfKb6WsOxv1qz4K9b33+wfGp14ZEla0q/eR0yvJ3Xv3s63m/vZP8vflH'
        b'/4tHfZJmff6f2H/uiLp09KX8dwbMNmx+dtIbSqngiFyHbqDLxOkGm8d2uPLguklUiVoyGe5SYWLfODeWHM/UzMwWzxDK3UZXl6uS1SnqqHTUMloE5GIW3UKn4BaqYw3u'
        b'OxjVxmIe7LnUZEfC6QvoUsRozDoyUAu8nARPYyZmZAfBZ9EW6p5UodNBqhhlsko3RzgHFwSgCq4QboL7hfC/nfCSiHo/qYtRAY+6vJ/DVlM34jjUCLd0OiorHDYJ8X9w'
        b'B2z7uaErgf9LkMhjRa5TalKRa/cUuSlyEq3jHyjjGc+zCMn//vh/b/wbzAxhxGxfrGH6022tZAk/mAklxz50/u1I+4Fl2R/EnJgKcindCCbHNfJkiS780WJdUEpFdGda'
        b'u8RpXLaLqMXoIc//9629WPEl5/QJW+Aa3GpALX481UUNuBHlqQaQw+jCIhc9Tg1ITVf1JFqAiJxWjPXAm3AXOkTPodaYzJ0WxrezHWvjZPnpok0EJmJ5iY6g06ttI3GZ'
        b'QrhX1lFohN57PR1dwQ8rurx6lQjMWS5GDqyVXrOpcbkZ8ES0Z2PwjM57Ib7YTyYGM1aJ56Om3vRIY1SjQdfoErZ7EcjlSRWBWHhRBPdgS/U0rELHhVNPj2hRJVmyn462'
        b'Ol24ZMNJIKri+sMWdJ2y8PFizvodJ6xB9Q+zCnz9hxR+kA8bSHSY1LshzsT37JKif3HCEtZzehswjBH9yFpuEwl6+E11w3h/GCff+PWxzfErSyTP2xLY04nbZ7+9riWq'
        b'7u6Uxq+WVoSdfTEprieK/de//35vxJ7bkyp/VbH6U2XEkcije2VRLYd2vxjfPFZdcC/rQMnf32DO3b38u2/vV597/nhh3Q5rvO3Kfy1DT9+zOSZ/Dhu+fgCzPh6yuOLW'
        b'ptFf3I8x17zgH7W7T+vYiWH24fbMO9vem5D7yauj+KXP9Znz1Q8oa8TFurSof7+vM3N79qoevP6b0CjdWfFTz7w/9d4axvpw0jPi15Q+NMZvhWwYORe+65nwsFaMzg0q'
        b'ElYYrmKMqhcWg5wrQfJiuhYEr8+mLDMVXkfr6VIQW8ygU/2m6tFNqs2js8nFHasifWarGXjGvw8Nr/RDW4d4Glokhjp1PrxDIg/284U6uF04ZmdjAqwn+RLgcVdWzB+D'
        b'ozh4AjXkCxHULRj+JpKpAzX84VkOHe87owwdEJaXNsC2nrA2Vp2uRptSlWIQ0JdbuiYbNSMh2tO03BfWZjh1PueiL7oj5kAf2MTDw7BpgctW7vV/nTX+PO7pYleUe8Z5'
        b'cs9ZJPKRZYbOopuwWTnlcizZ6s8K213FlGuasYUHnI6LOtKjkP9PurDZzdZI+2Fd2NqDhC5HxJ7DwixU6WZtLAgYzeXB491HwZAfi5zpCBXUMVmcjs3idVyWSMdnifGf'
        b'BP9J80GWD/4v28Zt43Wieoae2Ubij3idWCehe0d99XKdVOezAehkOt96NssPf5fT7370uz/+7k+/B9DvAfh7IP0eRL8H4hrpygyuM1jXY4M0K8jdGuNuLUTXk7YWjN9J'
        b'ya8utJ4c1UkOuO2l603f9ejmXZgunL4LcX7vo+uLW+jp/NZP1x9/C9XRw0+UA9r9UwVhlqY1afP15o8kbKe1HeL59M6joNFjXpkeV8JgIS5OutqjKzVpVxrIkkqpQqvT'
        b'ET+oWb+ysFjv4Vb1rhwXwpncSyUun6nbHUtLxChmG/Vai15hKrSSBR+tlWa2Wcj9I14eVAvJotCbiH+VLmM4T0mIcS5NaXOthmKtlVRcVGiiK1V60qLJWOrtWJ1vEVa8'
        b'tGQNyMM9TJeJVmtLaWqx3mzIM+BU0kkrWWPBdeq1uQWPWH9yjoKz1Rg6mFaz1mQhCy86hU5r1RIgjYaVBqswoLibj15sKjDkFnReb7OZDLhyDIlBpzdZDXmlzpHCOo5X'
        b'RQ/7FVitRZZxsbHaIkPM8sJCk8ESo9PHOt31D4e6XufhyczR5q7omicmN9+QTk7XKcIYs7rQrHu0g4wem8tSdyzZWC16wo3VzjXJh1Vdne4mg9WgNRrK9HhOuyCkyWLV'
        b'mnI7L06SH6fj3wWx4PvHXwz5Jjx+U2cnuV91dfQ/wVHS4nSq6+hho6i73XgCM1sodu/Fgy3wCj3uF9YNhl66TmRidEwM2hybzMCTaCcYDZ8VPyMfrWRoKBGHxR857j9D'
        b'TfZ51WcwIBjuhVvgfg6tgzuBYexHbZxlNs64498nv9S8nBP58QP8jA59oEnUGuk+8ZgFkdpkLXshrFfc6rhY3dK7bY2N7zZvvVaprL1Uea1yeK266tqzLZUR+yc694+v'
        b'Xxa0zzTWue0K3Yju5xTgugUdItwpv9EueF4Q4NVYPJ/3EM5RVqd4ngE3wutUDYHn0AG03xf3WiloIYPReqyI9IQOXgq3ws2CCbUeVk5SoYZEeATtiedx/28wJnQVnaTy'
        b'fR625o6mwMvwtDAkDD0eEq6DuxKFEIo7sCke1WI1oClFLaH3EqQUwKvCmXVX4FHYoIL7MnHt8SNGcUBSxqDdEiHeGevL1UtoR6vTUsXwONwBROg0g7XSbRmuvUpPEIFA'
        b'IvOpyA71FNlrwTQ5PaeHGCVlvbxx2L3/WxDWLcK+BDM5xfpx8cYtrJDNe/v5Vdbl46xw/77iecruIyF49GZRoiXbwXLXdlEl2SDgWrBrYQQAvDeOmi348SsMCt0z2qVJ'
        b'167Sh2GPXAfEjXC6wtwnAqpAAEqa7TTfzLsfAdErLogehnisBbqWFGOeqLE8V2OE1xp0lkc29rq7sWjSmEun62bpMddowDxcbcGsXPlkQDinwTdbX1JkMFMx8Ug43nDD'
        b'MZjA0VGCyKHOA+/dvIu307NvKW93HjTuEHnw9scvf3S7s7br8gfmqnQ7/G5MgafmrobrUT1PTsAEcDPcMdZGMivQNnKYPaqBpzCg5aA8XzgUdynak4Zqk6hWP5InOwrU'
        b'sJZNRifSDOtCI3nLEpynaZtfv9qXgyri5FzEsL6GihcLBnKpyxOf1v/WvnTjh8qhsV9/VTCqJf7mzbFvaOcl/GvrvOWXP0041pJzTeIX+cx/co+qL48Tj19Zm3Pu5bEr'
        b'snZNur+lx5/+BQJ7hfGBAUqZcDbyJQk84mnxoNNovxfL3Iw5HXU0XZIZiMs5SVgDecYX3WAhuSPqtHCahmNAD49At13oHFklgXvgbsrNStFBtE6w6ESwNRHw6QxsxXKl'
        b'UeB1F9T9hUUUVMehvahS8FNNnCyE/a1DJ+EugdnBW+gcZnhOZgcPxgjHEazrl5iCGmLhCT4abgD8aAbeRFVjhOsQdqFrg93HfMzoiy6ycAM6NFBg39tGwTaPw3vTUBU9'
        b'v7ecSgkjqrGhHdjOJNejJLpYeDA8xaGNRXCv1/7VJzqbXJqtN+WaS4usnbeqkt+FchpyJqMx2vQU+C58z1nac0PYk5376zwDvoPxHsaPt7phvOd+mvE6Afh/ok5t6Fad'
        b'ml6gNeXrhQgvlwLk4gCdlCusIz2pXkUifZ5Qner+IGI+3XkXF2wNjvdQePyHCSoPVnewtnTB8Oqn7bxlMc4X3/yx3yu3mClxvfk3bti/e2/xi4rI+/EtI6bPCzl+V/by'
        b'sZsPa8La4KufjtTf6xnyTeCnh/vZ/72v5rfDJihC5b2Ha6uWnv5hWa/q8z439/3nXfFr12/d/3VA85WQuoijSh+K5pMxLV6jishhdMKliIxGNVQP0aEdclg7Ni2D7L+H'
        b'J6MjGeCP6jl9NNpDI031BZgkOpAcXoPX3YgeJBHI/5AfJunaWDVqIBsXGMDHMvACbINtdJtocpmPcDp5Sgasj4UVsM2tJYI4dFA8tgQdpHsz4a7opajWpe3A3ehCyqDp'
        b'AhM4OaQ8xUtPWi/BqtK2EOq0USxHJ1QemlDJELS7D0N7twLuhFvduhBhDXDDGswdxnfaYv5EJBqQSxEu24UdnXdSkN8CGXXWhjBl/TsRSKfCTn/Gs48kTPNON0UexY/f'
        b'd0ORR7wo8jENKrl2cUGhxWrQtftgvLeaiMBvFwuC/9G7DSnV8u6dhiL3TkPRT+40dFLtR+Tcry5ENFWnIwYQoTQP7UEwHN2y+5HkKnRCINZE/Dlphovoc7SmFV1J1k3l'
        b'zj4LJWcLX3HhyBSbCZud6qQZ3cRJecRcuUoSI5sU84qxUnYHr1lvtZlNlnEKzTyzTa8hoVLCKS+6aIVmltZoEdK0RhJ5WYqVGaJTmaxPwHVkXbgOl254sMOfp+fDmKaB'
        b'LzVP333jufefe/u5tsZrO5ormyvH1p7fdT770I7zG4fXtmxs3jxw77qa57YNbMwdMbBaO3x63M4GTSLTljAS/Crbb/befyo5wRragaX8dljrxR5ayTHdnB62LqQidiGq'
        b'R7dgrWI65gAu6h8F66zkRMVg2Ay3p8CaCalJsCYjDW1KjYENxKnJAiWsE8Ez45N+PiH6a3W6bH2OIddC9VbPWxdcv6WECsv6dSIJ73JOK0UsyD5y1YL5OHmc8BabnpcV'
        b'8R7ZTO68lEhP4seX3RDps15E+tMQ/T8hQxIf/VR3ZJhJnVyYEk0C6pEYQA969HBv/f+PIkmxpLkZCsExZRX8WNR+yDOYtEaFTm/Udw1cfHJatPynv0CL2ntfPAktTjMJ'
        b'1OhFi0vAr57xM+aOxrRI9YnthfC0NynCvaiBkuIWf0FpPb6WHidxC9V7EOMgLMvpfS8VWIVvUCVjeq2PTYH18ILSmyQnwwZJ8FrTz6fIIMFh2pkoPTYvO088oGTZSTuL'
        b'6VLYKRxPdSI/82k3tZ3Fj4fdUFu1F7U9tqH/i9fvuPTUnG7ojCIdJQiTbWUOpi2MZx6+5Q6Pba7NbMYSwFjqYWH/UhTk/lIonL5Y/df95Hq41sZminzDvZDvvc86REEn'
        b'QZDv8D2ZfQ4jH7FGmEx4E9bq0J7OiiJsy6daphEbdE2wdiU84IF5+fA4PeUEK2B7UCVHdhA2xGJb0lsWRIkx5l2TKOAduK/TNX3dIltuoc1k9ZhFS/fIFiTtDtm6FE53'
        b'hXKaHsn3BXcERTxyLYoPxhRLuDfiVYB/+f8U6nVp9v8y6hVg1DM9EvU64rqfGO2cmx4MJkXx6Jj4qG448ZOh4Zp5JgENl77e9Gg09EbCQevdaPgWk7/Rt2XBmxgNqcFf'
        b'jzX6Zg8myC1y4mEiOkOtiMhkyywttUZcSDgQnraSYwFGW1GjcBdtF/QLGZYAHWJ4IQM1PgECBpLBfDz+hQlnDnZChM5lnbzu/KNR7gJ+BHWLct95odzjWlL26nzqgiQ7'
        b'W1eYm53dzmfbzMZ2P/LMdq2dtPu6980ZdGZy0Zl5H3kcII9m4HTRtkuLzIVFerO1tF3q8nfS2JB2idOn2C7z8OsR5wK1Z6i+RNk4JSnaScF58QtO+fVwEpJrGw8TwTAL'
        b'kBMheF+e8fhlpUyIH0suXflBzD3iPx/si3PJ5UygP/nzl9JNztic3Y4Nd/fZCuhSGqrDVm5tCrZKWRAJ14nW4vcbu6y3EDKf4sIP76VeIW6/vYdze5pz+ujh/w8VM0vI'
        b'WcXEs5lL9p6ZTcJ+L7c6lo7NRu/pNF90D0Unz+lN/Ajj3Mdk8AwNVSkbBiudx2QsRJvImSytrt65QiuSZRK4OQ7ethFVxoYOj+ocyg23ocuPD+d2xXJP0nbhet0dbAm8'
        b'7+buOD79lxw6QRrp6p2Vpys5GjCTu9IXRIKXAvyAwrioz91FNEb26lghRvaNHB/5vUXDV4uAkZwn0ZYyQfSg97X8H2f2UX4w37ywedL8ybMX2oaL5sT3q19VMKLP4nED'
        b'lqxOtl0fd2z+jJn/Xvy3Pj+GvzYmvKxUpZ0jlawI+U2/v7Joojw+JOHq8Kr4X5UXpyVErI3sMT5yfsnky3x28NGicwNysn9nuCgZNP+IRp+QvOI1n6+TJqr8ehUsMosq'
        b'Bn02o1j2haW4KLLXvZknfcP8rq/9EZsJkTHbJML2+WNoz9qpcIuX67iWTY6Hd4TI2HwW8LpDPIki+rPSTwgY2skHgyHSoXhaNBPe7T1DSBwp7wWiU9tIFNGEE6UJwEZE'
        b'ErqTuRTVpqljyIXrkSQk0XnoIpbqEtQEW0pRzUy4XRQB4IahPqg5wkzrOtxXBKS8gyWh1g/HzRMasGaQMyPFHDkzcqhYIxwNPqJPGJm5839kAPPtBMOG2lZgIXskakYO'
        b'jai/4adRcsPl05Uvf78qNKHP4qHjdaKBadenJ9+o6aP3featl67Oen6wKLMFhva4MWrS1iTHXw4eWBQ5++U3ip46nHx5d3zUkRQ4fu/mgAft97/89fYh93fMvne16PCp'
        b'F/7xTfx/p0pS/UtiXy98r+Bj3yUb/zDxcM0zv3vt+j+T+35V93LG8+8NONUwdEvrB0qeqtg6eECOdqd3utYNXhonXAG6twxt6ByiNMFfCFJC50aYBE2+GW1E+yyTVWpy'
        b'eTgZQRHwRddZdAU+Cx3UqJ6AGhJUaFMU8XiJ4UE2WDYW7UW7usbi/9JTyjyPBzFbtF7uZ+K28xJlKp7GLpI4HSkbyCgIH8WfzbddFbVw7TyJBPDQn34pYC2M+a6bc5EG'
        b'hnQr+37veQ4ZPaAjvQe6o4pKh3UeKircBK/3gft4eApVwMtduI/bezulW+6T5/MzOE+399R15TwyF+f5pCfhPAAEFn9h7j1InkQ5z3GxhHIe/1kAc55lIa8LnKdcNdHN'
        b'ea6tmJ19csCJFdcXrY/cnf5iQvzi+uh9GWfGHx23rN9bUYdy/hv9MG2t32d9/Mpvzm+N3DB9VPLn6aVTP+ovDpf1/WDRtKxPJt0Yujdz8ryaftuibg5YMi02KbPkvYDz'
        b'hV/Ht3NNUZlFI/oeHfXZjH/o9s/f6BsffY2dEmQZNF7097HjE7alfDXonZl14g/Xfsj+gDmPdNCzMtqVsDhykx4oeNtHkzqsV4hA40d6BZP7GAO1Io394yC9sGxH31zK'
        b'J7fxgaKHszTGun7OPRZjwglLAHG3IzSpIUUDhJWw8HnwOqpdg9q8OVoOumCoif8GWIgGkm4eoH71vB8im3yOP922N2jDxXsvqVr5QNOb15K1C6dV/Cb0H8eawZgh//ze'
        b'Ol5R/eGaeWHPOI6LP+9RaIr9je8204EX3ngz0LL8fp3x+plN/f9R/weTY+ZbfT+RvXro9PGvB+//tqx+Uq8J704eldbv2eGJSoa6nH1R89qUNUpyShFlActYfSq84qU6'
        b'/rwA5s7UqNP/BDVOJMvvIYI2Q+lRTqnTDN0V3fkFEDznJjpSz+huie61vp5ERxyE5XBruEB0SWkumjuNbvbR8LA5C1OcJ0H4OP/oCccLMC1Wi4QrRuzMQUAorZktZ+ln'
        b'Tsfjz5yVIe9ngEZmmf9StpwvJxeRiKqBlSX345iLyvztooOcTtTMlIsWAlN/cg3ICpnZKNw8R9+RW+lEwrUfprt2cvtZHK2DlG+zc+Y6nEvULNxAJ6a3+ITjlsTlkmrG'
        b'LiGXlegk9Ti/XTwBrNpmWkPLiirJLWOc+SVyZw6GX4ThFNHLUUhZaZeyUlz2DdM0Wla48y2uS8m+jyrZyKySVYuF3DgF2MndPJHC5SzO+9xm24HOJwwzF+ct57J0zIz1'
        b'+qJZ5ql4pOc9FNmseeoEM7GBMIqSCwLpCzM5fJneuaWUmPUE9Xz0JttKvZnc3EPUsXYxuYxDp2+XzzcZyAeqmgplpwgY1nHebUe19HIUujdsHnmQkM92ZvnPPQdPTi7L'
        b'sowQ9iYncs4NsuT6ELnzEh/h4ihyBZTMeW1UqMcnufO/lF4NJRWW5IImoYYUjKVJ6tFRMZNzlGgTPZlF0Z9H5wfKu0QruO8WIA4OO7BIdcxcQC4ApIPPui/SoYNoTnB1'
        b'gJw+bnnUhcG0W9nWwmxjoSnfwDmPLwccsU/oGWcL0PYBKWiLDwUTW6iohh5qStUsMBRWiUpXMF2uanNHdcVTSHXMCsYsJxaGjrOTi/YYHX8QkKvbMNyiUNDM2JlegIg1'
        b'kkLtELGzFzS4go0ooVviHrBCd0RleQajUcm2M6Z2puBRXSM9Ij2jXSzinEdskimjN9gIlxb7ohPYVqiFh0jkE+4T3Ex7mEG7KwZD+4tKly14zC5ppttd0r/wNnt31R47'
        b'Vzv2A/qmrAJ/BCAhbnrFsKGpsULiC7NewGgAFK3xD8oKlywSEkv9qQALjCsePPPWwghgUH2oFtHrnNZNCfpSs4yeQXepsqXy0q7fVg189+SO5o3NlQP33Eo8VWljcv2m'
        b'yz6Zdiz93WnrwjeKUn3DNokUh/pF93ttlPzd3q/XKVODpwQfYiNflI6IqFosj7xcMbZKPzA3jssfB8YdC1u1LBxrp8T7sQrVLFGpI3sPSHRtqY6BB6hCOXRGucpnhvtC'
        b'VeE61Yw51Lm3ajK6g2o5dDs6HVuAaHM0g9+fYtHZNHhbiJSo6TEZnkrGxuI5enEr1knXsIMmxv78/dhBKwt1Y8cItxJl6wz5hm4DHsgvkFIaJrQbzpjfdFdT/SQN1rga'
        b'pAVLuxVmNV47rcnxr/DYnBG4j/UZ8Hw8Pbqc3AZH7hqng8Kh3QxIgMfFa9Ax1PRoZkG0X4FFEKnWzNA4Kza9XaS15BoMWL19ETjFbQvTeXgkBfoSoyGvtJJATEMpOOEG'
        b'hltrrHQZnp4pBk9ND+AxJVWx6DrcNfbRoBCeR27douIuhFxURwAqd4JH6Z5NN78lgDLdBdZPHSXoYzM5Qazu4F1E+6C7WfzRMRu5Sp5CugsecELLA3KK4778sJ81aAUu'
        b'2MxvuyAzv9MJmpzR8cLlips7D9hNtH1lyoiRSage7oZbnLZawEBu/GLU8D8M2AY3UO890XBhAAUhuq3TcBF07JuCThMYkybA3U5V0h+d5YZLfLpErrmvDSXb9nUMZuhE'
        b'VwLmSCth91wli/UHUM4JNwnaWczc2VVSO1s0ws6QW/0o5KL09iFxw0eMjB81ekzC2KnTps+YOeupxKTklNS09IzZczLnzpu/YOGixVkC6yeySNAOGKwIGIox4Sr5drGw'
        b'gtEuyi3Qmi3tYnLcx8jRgsz/P+19CXgUVbZwbb2m01kIIQkhhCVAVnaUfQ+EkAQBQUFoklQHs4fqDgmxA2LU7mZVEFBEDCDIIggoiKDiVKmzu8zMm8F2dNxQcHwz6oyj'
        b'L87of8651Z0OSdTxzf+++f/vpb9U1a26+3LuOeeexXJt20eOYYPzoBj0XiQyRhxu3MSzWKved2v+iDFATZdrO4KD1EscJ2hPdz9INn2uyMyVHQ3J74NlA0h6q8uZMnIM'
        b'G4iDYTOF7F2dXaE+gnXIa5gaGoRHxGHqCe1uZtHxoPpgj8zCArKAmD4uyQjAEWj1k9qdqv87uPhCBy7+D+Bede3hyIAiRjTLn1J3qLsYryE7Z7b2lNZSYOSiFotL1cPT'
        b'ScZw+CrYa48tBaqJ45ZyS2Et3FH+zfAmgwsFuK981vuPK25iLPm7+2081TL8rlO7ht+Vt6ff/eufMHBLZxvTzpkmjE8XmEpSa572bGZ2HvTDxqEmzjISNpAV6JVLO0iy'
        b'AqPVs9o5VLkCgIlW6wpgG6lUT/QYKmo7NG98cK/oBnkod9U63OXVTpe7uLqua4Y6+rw3Ku+FRloMmClFRz894UQYr7wfLIHSHRWDe83tHX6XwhnpzNLsTnUDqa9uuzUL'
        b'/VgM1fs4T9uUDZupYlhX4M79Djc9oi7sFsbL9PJhbnq+W9a0E8KCiEZUp/kQU8iMnD6qPagdyIdNfIu2SeKMSaoPdnmreoDp0N9h6MVlXf8e4C0rbnGPauBIPjVjWvTI'
        b'EWqLer96asQwrj9nKuTVB8e7WX5He5WPHDFcfVw9O0I9I8FHdRevnuXUk/XY08PytL1kb2FkZA6Xs6yZbGh+WJXIDRv1uMitWOHpv4rKzbtuCDdvyCcGeCU861jCrDXU'
        b'JWv7yAKo5h84nhvfU32G4p5Ybeaik6dIEHeucF0Ww6wmJwLd7znJc1NWZN2ePhaGlawS3HRdYX6e+lhW8kQjJyXz6mn1nkFMDV6ewt0+4Q2eq1uhXGlczTJ5WZgMtNNA'
        b'nhu2Yv5fGzzsZXpPwNmSeVKX/PukZq580oGVvAvhx5MpB2bOOzVHmmorGPHEyAurzjzXIyIz/+LzF0/O+9GIw+dOvliR9sBLU3/Sc8PDJ796tOzp9wY+M+vty5fvSrjo'
        b'KzwjPLVi86mpB6+qjcYfGRqqis+PiY9u25/9cePHy6ZbYnspo5dWfup4OG+3IfPGrBU/Pbf/1Sm/3lj8o09/drhVTd5yYuB/vV3xxQlDzKSbmj8y/env+81/XvW2Y09O'
        b'zG/nf/JIzecT7p6Wdt+thwc+VBf5QdbgP5xb/7tDo351bHph1PWri5rzdo8y166ISKv8zYQZRdf/7uM3XqlZ8fDet3/0l8kPzTrv/Xz8m3/pm3X7dLnnS+lGWtHabhiE'
        b'Z/PztAPa+TBWhvqsdoR9f8yjHs1kOKN6Vn04hDfenEpo4Y3q09rdmWEGJrXzjUL2kqUs8UPavaPy1eN92iWDSS64WNtPTNBI7bS6KUyHgilQqJtWSWattYxsdqonFsv5'
        b'pH6eoj0jVPCTlxm/vzeYfwVnNLIONjmnA2DT9WOGDSeoNKEzVBov8Yw/ChubaOOTAW81ChLfHyEKOZdNoHfMpbFyOQS/mLWVgLWsVil1OshhbjsY+yHOLgUFHbeG2WXB'
        b'sp7sBua93IGBisJa6skbtfOZEdLsrAzSjUHA99SwkcMkbiAvwUazU/MySyv71bvUI45GxEf6cf20B5TSoEIj/nUQXELXoj4eHST7gUJDt7Y+pEcNHknJ8hjgX4Kd3JDA'
        b'xUGsXhDHI7TyJB+sb5s+URaD6VrImf0+HmKJSolPaoX3HnGfADkz1Ewq7EQYh3ya4ZQjH+ZxjOz1QIa9yINutx7MCavper8i9+WvB4/UyOl6aklVLdA0TKKoK8frDJkS'
        b'A4b6ujqnoqAzloBEdLUxILmdjW5AUjALV3mTM2BxOVHQyY0exRvKZfetyhWML8rOzl7VoYof4fPV0Ly1hdflNTEopyqadbaIxKd8I4lo8JQUubSt2k7t2XzY7/xFjODZ'
        b'iIbU9D28r7ZX0p50qHd3QkpDnYujjEgpoc4coM4JxMYT9uE7GFHobtipZBG7m5h8glICIy3IEsQQPWKruI9cVzeLOKKUwxJ4a6AcRBxtj7iAk5m/DGNh25AJt0xurK7K'
        b'yZxMCGZ5zcqJS/sPXjZk6XK4Zqbjc07G5FsmTyJU/SpWlnG7XuCIeERSJ2B0OYuV0lsDhpVKbX1dwICsJrhV1TbA6LxECzQgQikBUx2KiCk1AQP0JiQwBwv9Nsw/Gg3P'
        b'QmpHMPIfxKC4kigFLUGQE2oGOSSe7HOrD2hbJDLqqj6OFnxUfxE7aSJbuybu+vTF2jGjumvmvA7IR4dTzvtoNADxF+I4JAQY8aK4Ud9GGYjXVn4f58rxCDIQCh7OgZo4'
        b'gjIJr/RlhgdICwf8z+CWxTYTQQS5ib1gXHhu1WyKXRWKvYXFrkny8MoW+ua79ptuo04qDPDWNiE1lQYDeo9m7F9oIbiLy6tgcUjOKmc1DIJztbPqW9ZfwFanON2oKop9'
        b'/Of2rrXp/uOjeWY8Aw+s4nTwdqFJ25c5ZE52OhGldT3VTayPea6fut8wRDvq7l5R+0su/PQeIBO3RHRK5NyXQ+e994kVxgrTEjO8Q4e++M7kNFVYZFMwBKigCaAaqmmb'
        b'l1jl/jpxECHb7rQsiZAH6OFI2Q5hm+4zRvKaywxylBwNaSI7vIuRY+GdPfRGknvIcfAmqkOsnnI8vIsm9WxuSYw80CuW8aSAbVkSK6dRKEXuC6Ee8iBIY4QapMr9IBxH'
        b'Hmp60oobHIiYCcPirHFPA3Kvw8QLMh8XBGFsOy+f/NFzshR8DtKgfDMN/9Vv4K+NHwdIOspqHNGdaBaFxjlsLTlobTpQuc5VV1zqlKQgDSc0JYdVLefaiF0SkVRXPHFG'
        b'+h6mKmM3kBqaoBh4BLPu4pVd6aAFLHVVxeU1DvhsDqtCz/AqhGJ0KlsIlh3LMeW3WntwMeq6eEeEgMGBWwEtii614HDJRIXKFpuiw8vGpJ2GJ1SsjYYH17u+HqFAXrGg'
        b'N0yJ77qkuPZWdiJ2QjznqtCwE7znGZ+ZjjVm44EO8w7vEWWhUlBGycikECag53dYPZVGV7xs8Ih4B4jP44ENvDGxVPFcMK7Mt0JO+xjPylzYxg8N8BltQs5QGDKy9o0r'
        b'VRFx8Pjb2gy3ZTSnuXCvddVVlbsDVqAqFbcLDSTTvhvUkLqd03f5AF/XHWHqAEgDW7GTnF4kSEFZc10TC113JQmxfFNih2kYnqawg0FSMbznUoKTkHrOzU4WhFbqs31C'
        b'cFKKSg9sl8FVD3gDogw1clBcERsQsIamezenDkpPSD9Q0rEVrHrHaYM5/msqqcRhTU2YYXFVlRLPd4tAJcCnIR2q1OPaKkEOXcIaqhWCEB9MJZ+E6IaPJnYFTMHNAtWR'
        b'D9ZxH8/DN50He4QPGGpc1cV1UN2kUHWNzKuJ7sY3YHKyenw/PenekEOWpGu0cnTYFM03xYa3hWXffQcPY00RQk0RQk0RwpuC3Q2NEfTGKIk8baJhDSlHI1DudH1yoNSl'
        b'gtTt92tJH4g5omNLYq9pCcu/06CEOFRIHPmgpj4RWpIRhAlKKuIiMiHbzdAaxAdxJbsFfSqJniDHV4SVPYVhB5ISgw3Dg0nWugiHA3Cqcrez2uEI7hZzuO+2man0hdTX'
        b'S8HjKMK3EOtq6tVhybZn3v1ILQ+fdDnf1j42VjUZoXHN1ccVtkIaV1EfVykYN4QjKSl8EF1NZINHHYEGTcPGGnrDFaxwcMCxN2gD/X4D3g/ymSzpe2GwX+yClVT7O/ZN'
        b'qKjv8MIcXGgLWTFdbaFmh6OktrbK4cgL20HjOhbHIhC2vrDDaASpDmQwEFHrg5Xi4coQ2+URn90D+8wuYQuvM1NzoWsQddPxxTUAmMtr3IEoRMxlZ2lVMZNLRR14dy07'
        b'aw7uDZhMGYj9Tefb1/CTjYoT/ZoVtE8rGy98I8F/xxXDouV22QiaUqmhRsg0bWRhs0QkEc+kIIJYk1Q6fFQNKvExJ2kBi7OxtKreVb7aGYjEfc0BNCYZ/f8LVjIVGljj'
        b'mti/P53nAmRLI7gMu1IVbBPBJqZj6zLw8nnnJiqD4cMN4fBA+MYodNw4sE4doAF2RYgOeRku5RweUyD9D9jActYw2kgkmP9Awe/Dk3Q+kbtFaDY0Gz0Gj1BpBNoe14oh'
        b'ER2rCa757Hklj/cJ+heAGUYE7atsHiN7D09chYTCHFBSCuRnajZDyUaPCUozeczYtR5TLw5iroaYpmaLx6Kc9fCuwx4UBbHAd3ECVyN5LIizuFSP4FJlqn0FpC0PchjY'
        b'KTku0TbDAMS30i0BG6wNoCTLq2QY7oDJXeuQy0vdJCNB+wPsMG6YWyUBC0bEheQiPJPRPyae2D2091hLa2tcTA0wwMt4ygKZBvhSxYjZCKUyM7lHSPJVrtvNdSjEXoRD'
        b'N4SGTiJ4F0enqeilxMrH0io36j5HJTLp0XED1htBthkQL6a1mC7k5qbzuenx14oeU2vOBVujcKHGWXhGaSMBzTAExEVo96euoV2HIDSBI6U/XlAclaYfNSTMFeD3dwXd'
        b'7iMQ68JjX6D8i1k0SwJvldDumFUC+lu026KlaCnOGGeMNcVZzZJdshvobCXGtdyFLpM3F2ibM1fNyUJThHvUexKnSLkLSham65yTB7QH7O0aVeQSm6UYk5Zu5EbIxoXa'
        b'c+p2/bhmRbq6Pz+Up7oTD5Qj1graMe0+7d5OsoMIMkhUyh4CER5+S4hU4QMR1cWVTh1ZUfp2AaRM+oDWt0Nappl+Qr1bvdjeOvWktonnrOpeQds4K7ETERyEXS6U5wkR'
        b'wdHkzBQF2YHkBeJSAvKVZxbJlhiYpmKZqJO7RrRLBnFMsk2OhLtZtstRd6JdM7btxwRsM+qrq9fo9e0aYw4dfzIaBnZfPozQ5NsJTcZxgKtI3AdJDpKeCh/aWQVeJxdg'
        b'q8S1RTQom7xXqesciL/XhHApWn9G9u5aQgmlEJvbAaWRT4H/pp7hLfohhmmU8Xw3W6gFUBVWlZbQyPJN8R0KDEXpHlvTz1EJD9EtzwQdF1Gb87uYUgwJQ3DmcNwdVnjC'
        b'Na0NReq++Ek0lDIPRKENJdcIcQSArwz0UUcgZd5CvjRbBWQEKiNwIMMqXBYSvUphmDANJPUaYUyp/LcezhPU8bfjP2bix9mJG9dVe/4pBIjVq1skyORwVDlrHI5tYV0Y'
        b'd02RFKF7JgI2xs2tZGIJuiEfCfeX7rAu/OZw7AgrsdMUpRjfs4W53baOgPj931IOQ++wytZrNxJyCD0RR29yaGOYgpdpod2Bnf12P6zjIFJTcFjNotVoFm1itAVAv0hH'
        b'u2PV7Stc6Qiy1eNugIEJqM6OYJDnUtSnJW2XeianexiIFsqCMPA+sUKskJYYnEwIDdl8klOqMAHmpoe8fBlP8NG8xMwYcwATGYy0EIPNyhgagdiikgpnqZss8+kd9QP4'
        b'R4q5G5BBQG1/GNuoV+fy/jnuEcIoxfptvKNHu+EdfS8YpEziO2OkOCWOhc2rlC4a8W2gxxwsFbGDplg3p9NghJEuhlZJQJNWWpUxTICYwJDooZOJFsHI3cxiGCCGoosY'
        b'861GogBliGVqpwL38Sx2sGUsFHao307jAU4TF5zpAWseUAuNTMyWgBmuhIB9KmGP9W5dALedLv4+EO5EO8tKILnZOIJx8d/SfTpVGXHt4pzeAa1j+N51Hdfq93LbjPns'
        b'Ca3QMGTMJjI37Ke0R7QL2hNF2oY5BTkofbdxbsEqWKrqzonBpTpNfdQ0QNue2f1KTQpbqYSb0IEi4Cu6qnagd7D9QdA0Hc2Izq2trayv63CiadDnT4/Q4tO3LR+Mp74a'
        b'AOQnh6CTgWHzkntNnVPZg4+WEI+uy23VWEWlPtPOEDPzTf2/pX45LEEXWoB5oeV4zerJhQ9PB1cPwMKxHMLCTdrxsI5Wj7nbcV5tS15W9pgcVPQCrHZrTjbaIFhl1XZr'
        b'O02dTp9CPBKU0IWtnCOuRzKtMJ7RgB48zYO+U7J8SAVyPiOStz6Ong1BVmLbP6aTkRTUWi6td7lrq8ubnHJqFVC0qXQcr6QOcboVpxNtsNa2z+D07u2/UvRxaGGCDM2g'
        b'2nP5yppaBcpoZ52ihzpyoYcGMYpluZz55kvN0CmhIekZqYz27qgKHVaFjkUUoyM5F9m1UYrRoxeagq3JDpp5SdUxd1fH7IDUotNJ8aaCubCGkDAPRISVQXyJf9adZD4M'
        b'/YtSUAjPzAyJ0fEvCXY9oe5VD6kbtZPaGYBq2imuVjukndbOq0fI4aO6dWltnqRuVLeyGGINf0Oz0GnhGYMLb0XYwpPbT61MZQY6L7MsEUk0yghv2GmZGTZKFJUyw+Zo'
        b'ks1IQMgW2QoEgjHslMy8xERbppk2O3vApq+KAqCClMLcTsZTQjOylUM5qXKYaTK/R2yWQhy8gUAl8OUoTMmt5OmkAukKQfGFuHaTPIL+BVDQRA5oCwm5BB7RVYNPFJYS'
        b'IXfkS0BbGA9Q8AgzUNDAAOkMwTjEo1CC/NwKoQzeb+H54J5gRBb6bFy7xOO7nnZWHLv2d+zQNGB1EAvbgQx22joQZ0rXzdhQxF7EIKxTnGXljQ6U0CQ9jYBQ4/r+tj9/'
        b'LwVVjwA6w+8fRgNOGzTJLZFpbpQiiNbdoIZOwGgs2omdcCBh4sLEQo7ikOB2CRNipYQdhiwiHtBZlGGFzrubMYhQFMA1hphGErF7kgG0ENuIHbPKps3Y1YuC7KNWoDhh'
        b'O26kFDiJaEBgOI0tMNCUwxx4bwXgfQ/GYV/09wSUUNenRWBvViV7mG2FiMKAYQEeIQXEmTVyQCoEqBEwLCququ98whhCmNgJIzK3ZKHSGE6vwBqfj+O0MLRh8F1J0JLF'
        b'y3+g7AIZHs3u2MeltTUAVNwEm1zh8ibMHClkSezgdmZyNk8iDSbFScCIsV+mcDq1BCCF9izR5VwVMNQqslNBJqervspNZEV1O+fpO51U2TtW7lOcSv2pf4LGY62ClRcE'
        b'1Lg3fm0XrUIy6rFZ4/im3t/SyE4nkCEmKhLvK3Hd4dQZ0ywC3kVSQ6QmloWTi7jy4j421GaPCPu3STGjDAq+pXdBWWKkbZDRCtiwEwbb7CirQvmPGuqwIOsU1deUm/By'
        b'83fgYLfA92hDiMpkpnNjSRbs2mWjF9Tl3kpTCnUfwpTl4OrBdiTgARfxQ2BB7UNRcPjGThvgq5ueRHia7QZI5BHiYUe+gycZDYBY+3jCcmGZwKKQkeNZEx18g3Hw/FU2'
        b'sCd4A30az8gNYyE7bxUcDppgbfE31lTW1DbUtG+qqf3TXP3bjLelufA41qhkYYdFEyuFATGlkNBHTkdog9wWmmrzOtMVgUhHDco0oQ1tyCARuzU+bGJF64cY8bxRiOab'
        b'kjp2b3jSTqAJ+5i4bSu48ONOmjeItyAGI7Cncq5ZYjJLusofgh5MQYqIHqNHIlif4ZbY+VYF7ANlkMteASG+fvIOvVHM69NDWRJainS2A8Q6mqMHFNwUxn0yBznMyjAM'
        b'WhhPGdoStjK7ZgeXQPzBhrCTa6uITF/WW51gt160WAjLwNIlfb4kVHFqQsl/n0lbAFlcCp6lmKX4nrF9gWK3k1LJmv5yO6tSO2VYU6BtQmtVKb0k9YJ2emyXJs7xjzx8'
        b'hxCRKKLFgwgI8z0QRD7wy7WIB1IMOtpBQjnItWSDFx0wz60trcwtr3IWKkgOdEA9OohGIAj2EY2O08kV5xZknhYfI6QF+kbHn/HIsIRpBVcDsS2NxMI0oQKfw6wjCVJh'
        b'Ww/yZCzXOnWvAYhNtpnSXDko8YcDdjtHJ8EujEcrK2AqLnGhIELATFKBcrkSMKHgfG29O2BwVJOPIHKLHjA5MAbg0mHyEQEJYyiVXdDjOBnGts8rG+EHsYQjGPmmmGAn'
        b'dc38RMBmDfYT+hBiYqLI9UPVxKZoHy44AEQInhdzNbfo2r1NPIAonmsC1KzCAGBcVCbcgamMytzFQGbvH0RcQpYXXykpK9wmWcA+h3dmWc9tNIeADvUubuZW2YEwl1iP'
        b'L4CQ3teGwqsxBNVKa+urZOrs4lLyWYCeoSs/3P0A/h2ZvDDdAoQedCd1UcBQXQkdrFTQeVvRAqLYAwanogD0qcGXtvn1NRhd/+KqcjrrdLgXMMGGQ1mt7HYxByQsfboh'
        b'qNHG22Ebjaa1LJAqLI4Cqmk3RYb6H1N0r06TxTFukjJIplkJc5IP9rwyCEZBCo6CfkSN+6OBGsMmiKHcFWqyQanGZ2JBXUvj1tdgRRYawjjl6N+lKSpUURbju1AqhiqG'
        b'ZJgA02nujlOOFo6cAM2WGNq5RtFh85I+dt81GWHl4cTUWdMCY03TCQN0ja54TZbbJZyfHKqg69JF1aGqXauR5HAA0EWG6zJD6BDZTIg1DF5sWCX1aJ1km/F/Maej6TSC'
        b'8UF+IHYPE+xEXDlEZJCcTjWNU2lVLeCA2HFBuRfJ4Wws7YJvDCAG1q4cPmzWa9c3i4NMEISH3Wwb1DM0VGvxsg4vd3wfjq4TIo026OSrWbJb7TE25OqaaH9o1naoh9Vn'
        b'1X1onalI20IenPIMXGSFaFXPqJs77Q8m/e4q48I4RCh2LgEBGuISoWjnEkmO9jKPOyIQrOYyI3FvLbBPxBDJaiKfOXiqZYE9A2NaIQ883epIrsYGpNx5M3I7QcAQ2oEa'
        b'Q25ORxhIEgCJw+D4wR1q5hMqJFTeprBBFtxGFtJ3iqAGWVvEvDVY2IjU1WmutkgIMANTGAyyG5ntLjQ/Wle80hmwuZxuR51SK9eXAt5vw9SORTPnL8grKgxE4DcyXAvw'
        b'KsLh0J2TOxxMSN2B7l2CiFvIHsC3DSeWXds+52NJUBfgQCQW2zXx2B0nWtcTbYtZADVJrS6uITOeaIkGwcLG9tnNbMpci01iy0JtWB2CEUJTLFWlw+fCDhVClmDIeowv'
        b'bOxw9aFRc4/A2F4VgrLcJ7UioCBhdqBfxVYJmcYtTPSdnptFQOXFXhwKWdNbwAFajUwChJBPXrnDB2ikbGgRtkYD+im1mjxCcC+7gZvP3cQEw5CRQELvfyHPo2lpC2bO'
        b'm5r6F2wuE4JsVJxlVsLXA0JDiT4dAkbABerq3dRjAYNcX13nYvrAKC1JZ6MBQwNKLuisTQbbqE8piVB26/dXAlfuxRMaQ1Bmm1S8jSh6RLtXLDGmgBSMoDFgFQtYZjur'
        b'Vjvd5aXFCgqZMRVVHITSINsJ/6LCRwX3Iw/hAYDG8zQuiKaT+Db0uaivKupjegbSCFB3Eb/4eLcBiERDHIeCrGiXg4V7s7BZNjZbZFOzFUbTCOEIGO8IEnj9rBkFUmyJ'
        b'XHOkx6K8EIzniYTRRM7E/bKlObImhcJWCJ+VI+BrsGwzlr2qrmNdPDYP4KEJXCWn/B7zlm29uESu7i3Iye6x38MrE+RIj73ShE8eOysHnlM8Nrhi3iYdgkCest1jwjxl'
        b'sdkCtbCzWlBK+I6C5qxM/I6CL7LJY/BEeqyAE1gq8BpRYZNjNgM94rEqdRgLamukeRdbeBWVTK7iGCy8iiP+oTf+9Ze/WPD55FzierSJEydOpIELiA6AHvxCRjbyqQF+'
        b'WsA0vbZeKQfgw+elCwFDjbPB0chua9IjmY6AlYR5q8prnC4GlKqLlZXlNa5ADwwU17trCZg5SgBWVQbM+LKstgZwXKW2vkZmxyZ342yVSp1VVQHppnm1roA0d2buwoB0'
        b'Mz0XzrxpYXoUm+EkBiBRBhKp5Bhc7jWAI0dgBRy3OstX3gpZs9pYMYKjCqrj1J+BuIUiDIoTahEwljB+iqWmvtpBKZjQsYTP8NbZ6KbX38lYiWCipCQi7sMFVEgLyKz7'
        b'CLUTIigRj4ERxJLOrCPdNLSYIiQT085IKdiiw+Vm5IzfoM4abOvRtOzCCuqS7UJ7lsJ1XGF0FJZM5/VI7cyRBT+HelY+kagp3FHNyKJp0c2QJKJ6Ci8bPXw8E5wUZRPC'
        b'NLekM0nbCWeRWKVmQvksbUnTihXU5U4dWVs2ljHtyaKEq75aQZd6bZnfR889Oyd14NDMtE54VUiADcET6YzZm6EVjCXQQVsM9hiUYgjqi43ugkZCRbGzhnBFsb7UwVj9'
        b'kWO70hO7iknapIw0VwatG2QVfIhZxRAXAIaFBNkDdprg5UCsl9ZW1So6IGf5Bgk4OqzrflOG+v8hVNMfQfqTIUYVGpciJUY8KtBhsZ43obk7sK0hUKzs5LtF+zbzOshX'
        b'zvN6MWHcgh9i7rOdb9ACmVUaQnyDaJNZSrDHDalHWyhNU7Rd2k7ZFVG3SuQEbTffb6b6HErwhbAAEm0TCwtRnZ40/R9XW1eHNP21B8aGVP1PFKDYm1iPwE3bNnPudWZd'
        b'+TG9HlOTMnFjIVlB44YNGn/zL9atgs7NLZ/08gXOhRYHHHJRwcL/WtxjZdxDaQO3b24efE+r78LpOwvuvd0/Y0yaNPzS3r8dfiXm10fP7D+z+le/HfThM9dN/mTy2+sC'
        b'XzV7Hv287twvft/wh6+Npy+f//M9A7ZPWbzheV+y8MYjxk1zLAnbJ7y6PXLFLRnP3zmX366I928ThmVHPL/6dX71T6wnFxxav+y05eOda1ZsfUy87bLlZNEJ/itn4vWp'
        b'X6xvOW1K3rbs7ZOP8bPknzYs33LnzXvf9za+8uqtP4/wfrLzxTcSnEuXa9asn73W+POKQGTvVz688sza1cLGwa3J794weVoP977Lo/9zmOsl9bZtORVlC0fMK/g0aXHr'
        b'hRm7Rr9hetPwyVfP5S++cvTdpJoVC8SfFf7pgwlD6/hJM3M+tS8+95J37e4Tv968KPmtN+d9/dM+845PW/Du7r4HHxx1sLrP+p6XTh5JeOrJb6L7b/qsx+Spvx51YMTU'
        b'HePOfrT6/qylyZcHfvSTv2x7+brnE098Nqmt6LWsy0tTLqe97tYOL2q68ouDY3ebJg/98Pnb5h8f/2hOtu+L/ziVvaXfonv//KmxdtV/bH2tf3bx/onyXeL6zPQjVx5O'
        b'Wps/f83lFYVPFd7SFrF2VePydxL/9M6khfNnpKW98Pq71QsfHvsg13Tl4BtPPtb2wjP91y9dlPiKNvKup9/8YPwE4TI/7tnpmYdXHbza+rtzv7ph/aKl8cdTZu3OOZdw'
        b'/K5Lj71VML7h0ycf+Fvryzd9ut29a0PZogG5u3K35BwIvF89uTDtfMOh8ievHjn25uVf/rbiytqHfjYo99GzXzxx/v2vniy+lPPL+DW2jwdVJ66Ofqq4n4OfH3XDmBvy'
        b'7ztbPssxe+Efh341ZmKrN/fNx58+1vbcLYGDG9758ah1lsDEo0knlrl6bV79cEripOON41p//NHpewcfqjd8+dsrr7qvvPO3b3JvfOLw5+Pblv9na4zpi5mOL2yvfN3w'
        b'+B//ntD7y/Vrf7P7zi3/iMoa/3fzzQ//auQTFx954PWkydw3e36y8NfHJu7+JCH3RK/3H76qvfP8S8/1Wb3mT98M1b64ktan+HezRiyu/fWF+k/jDi5eOPmUtuf9wtLG'
        b'L144+HDhx4+fPa588Orrr/x1yTr/li0Vxz664cXeTRtvqv38zUsvbXt7RNbFV8ff9Fbe0ym9nkpcP3Hff1peaNvxlva3lDWxR+/I/ehB60vOv4+Kf2T3zpePj6vc9/Vy'
        b'97yXjn/QmNygzO37i7m/mrpk0JX3Ti/6qGZA2/45zxx7jnd/1bt52oki5Ym9C5+eN+uFW//juobb56x79JV5nkUTU0sunDr7zsuPNsY0v/Xix2OGXZhYdTXK2hopn9o7'
        b'4rVP1t18+ssH045VvLj1a8O9ET8Slg9OjyQjnku0JzLotHMr0JNz87LVDepWE9dTW792uag9CeCAzF2kAlg4j9GA5MwrLMrKUbdgtBj1GVHdXiYwX3wHpGa0mZqnbpos'
        b'DZ2dpfnRJcbdovrk9FVMSf6kkIvkqva09nhmYXYGKsmfEdSdDdpdpCRv6tmPuUnXfGNCntKZm3RtQyNF0c6PNlwrqDpPbUE5Ve3QeCrFlqKeZ8e7ltkzXVkZyD2NUi+K'
        b'jqlr3GgwTFC3a3dB8aRsGpQJRVI6D1tFxsc2a7cHZQA846xSRCQl1Daox29sL7yP+uiqvIL8LG1zOgkPdBAdWJdv5dT7tKNukvDY5lTv7ELAQzsKVQmX8JinnnSPhgRD'
        b'B6n7XDnkSWlrfUcRBVbKpvYKNmi7LepZp7aNXJDAOPrc4QzkkcZwBjIKQJDprEbXMvVZdXPYdqHtuAmQwX9+e+rukj72X5jZ/3+X9P4Mlfh/4hJkjlXVFssOB7Nhhnik'
        b'bOSNgpH/J3/vS33tFjtKpovsP84m8NEWuMcKfGwPgR8yT+CT4vEgvn+WUciYk5BoNyRMkQSBT+CvX8dBzEH1ENMs0WH9wGi8ptI1uS9eYw10NUF8Cz5Fi3iNM1z7bDMH'
        b'38RCvP7JGIq30Xc7XSHPQbU2pCq+kSAW1jmhn8CnQMwEk423UV4pdjPdhyzFa9IovGYVKmroQO+u/10N33lpJyGw35CJyRDzhz3hdjtInP8Z7fTC9g1L9cM+NEc7wdkT'
        b'xT5rhPLju0yCC8Add8/Jv2Vvu7nmjSm2u1c+edNb7zU3xI+/7d2BLx96pPc9I/9qNNx79vRft33w2svT+7zd97nPzX+LbHv1wF+nHDy0nlvb9/rpG/r/dea9W95/59U7'
        b'H9m1+5W7tpzMct9l2Dc42dpcvOD+mLd2f3Ih9rdzvxx9ecjxrb/6Weyfbpj25ZX5U17/XdaH6T9ebxnyTevheYvfnd4j6/NpD6w4UfanrX/Y+dHmvcP25M8auefyr5J7'
        b'/npkxu4VH0z8x75Y09ANcx4p2fVoWdKahR9lZLyy59GLr0yqzvq8qLpoZET1Z64+P33wy+eXLKqafv97PfxrUmZn1U0vubchbeeXL7+V+fNn94y++tLEyp6nmq8u9R/L'
        b'23xm0Ziluz7eeebuS/vOHLp06szOS1vOnL1015ktlx44c6Lq+X1HHzjR9P7x+t887Dw3sWHnhj7vzTt+7NKZPwx/e8DP+zki/vhp2ekXP5cf3PhT+5+vuntsbrxv07nd'
        b'm57e9vFnm7+++NDE507//sOdl/napSmfHbkc05C99emhVS8N/mn6V2fPpk0q/vPxV15Xd6x588otg1656UL0z3928/i9g3Y99vGzhZ4dt/ylTNG2v79z/OmH8+LmN3zw'
        b'tbL3uXvfvXea/z/rn/rkg7c+Wps9Wm14aVllyoOffjTx872TH+tzJOnxSfMdnx0pOlDksRgiTSf+viDFI0enbkz+bEirb8SYeVN7jv7Na1N6ZD/52tReE/86/PnoBy+p'
        b'Y1YPUxMuXNIm2et8A5Lfkx69/23bh+eej9t1Th1dU7cxumHrF6Na36lc/c4r/zg4t+3d7W2PKY9/w138r7dujFTSmYfN+tJF+szapG3M0qfWRs4+Xxwu9yK/yiO1bdpj'
        b'DA86BSgGwxnaMSH1okz2J/subGJ+PAeM1DaJzIvnLPUic9L5rLZDvTNRO5OpnsgCGllbz6/oqZ5j2/dhcXhmfnYG2rTStpIvv6eGotX0jSau3wJDrLZtHLkZ1Fpg4odb'
        b'XlfPD2dWhZjpde0MoFSIkykx6vF8iKdtSseYmUbtIYWLuk6sVDf1Z06UTqI1uo1DZ6v3qMe1zVDX2bz6xDL1TrJJlL12+QrtgXxtyxCBE2r4SYO108xh84km9blMtOde'
        b'ZNB2awc44xTBPspEqMW462eSn4Uh2bx2IZYzNgrDm/NZWS2FDfn4LT0PVqh5oXa3elFQvTfUMpREvaCdVe/sASgkIE2Ch5+s7ZfJAPU0dUOdtv4W9Zi2Ab+oT/ALNf8N'
        b'LMvddrUlaARMu1+9wBmTBGuV1kJZartujgZ86SiZaISUzXzukpXsy/oFkeqWEm1jUQ4POW7gZ5nUrcxv1CaIfwHK8gFip92h3psxW9sJPYB4GyJqaaMMM3BoaDqoF9XN'
        b'6vkIwGXzs61DAEF8XN3dqB6WuCT1WUndLWkPEfZc0huIc7QVB92CRtXyAWvttU578lZphPaUeoAaCd24Y552TlsPgzEH63Q/n5tncCOXMb2uEfDHPZmabyi6izzML+7d'
        b'kzmRfCpuhLZX9Wob83DohHX8lEYL+3K3c2Dm8MwcbbOBOmwRzFvdx+wO7TkhU9syNCOvgOcs6pbi0YK6bax2JyHPcderO/IJssLgphs57RkuQl0vaAfnxjOXNHuhfHVj'
        b'UdFE9Y7sPJwBBQYudryoHjNB/mRh8KK2b3o+c6VbVIiZqM+u4exrxRlZxayhLdrhamikkePVvdrmBZx2QPXPYUujpUjz05RWN9ggY/KO2zCOEQ93atvUFm2jekTzqXst'
        b'aMhEKuHV5xapm8k8F6Q5ph7Iz06fU2DQTquPc8YFQjwsJKrUDdnqZrYM8mDqqU+pXmjW/YJ2eKR2iOiK0WOvg7mgbVjWPygaLAHt0iICnn1Yu50qUFOstubnZeVlM++9'
        b'y7RjnF3bIBau0M5Tl09WdzTAd1hReVBziVcfVg/0pk5boe0pp1a5ZxUUwEil50Hm2nZRPb9G28FIp9PqjqzMPPX4kPShcyCLM8O5KO2AqN6u7VjJOu1QQ2J+5mzou3vy'
        b'YI0m8eo+gEDMXO0x7RCsOGiqumsxUkzSDbx6wdVIC7iverEic44Bunr7hHwOFsh2BumGzlWfglWBUxKtlgrqUW03F+ERtD3qqeFU4hDtpPoQLFZfQUHNXCMnRfPqbrmM'
        b'TaFN6sN98oH2Gj2S50zqIfVpbZtgHKUeYxPggHZC25g/YuSMvLyQ3wi0RaodKWMukh8a0QCfhy/Pywu3A5qpPsu8MO6GoX40n6xV6ws7F6ahXW0Vp2vnaqn6aqt2V164'
        b'iVipb75uIrbnZOZ14s5JxWScNW9pWCxmmjV9nRutELjUM4MRGgG5OTQDhgcW+DYAPnPVs6OpWzblZ6tHJa4A5/b6Zu1xdyokKlym7o9A2rYOk+YjIItT/doRbY+oHVI3'
        b'3EhdkATh7QQEc2YX5PDqo7iMtP2C9lTldDaZj6knpwNEKKQdxKj6SmA+PiFoTySbWPvOaAfVe2CVzi1p0LbmZ6Vnwxj2SBG17Uu1M9RL9ikp+UWwAqGJ/rysOUNzZq8q'
        b'LjByWZxBe6BKu5/qqt4960Z9P9tclI4aBZtxq4pXL9yWJomFMlvR+7Uj6HTaX1SE+16+ic+FupyGtaGdmE0cAvXCMhlGGyqzmniFsAYf107PNXGJ2hPSzeq+GjZse2O1'
        b'g2jL6XbtIOyNkB26CorRYFvclwAVopFfnzGIuk19VjuGe5qUzcPg3KU+5kb9UnU9UKhPYo2Hhu2B6hF1N1a790BJbVF9QCLj9LxutboxP68go8Ck7lcvckZJMEeoR3UX'
        b'3KOXk2FjbHK2cdo66PuDMDOmGb/r1C5otXPsvwHN9W98CZ1rEyWIbq24CEEw89f+rEK0QaKzmQSgoATeyP4FicfYdhYHT2xCNKSViTQKVj7sJ0TDdzPlH0d63e0/G+WO'
        b'cfAQ1UYa3mY6WLUJRtGzjuv8A5qVcep1q6oWsvdQX+dwtNsjDB53aHx4a/GBUSVf2MKoEvrWQewiEv7xsA9FHlwvwLWEk/kK+PkX+RahSJx/MNwFuAtwF+EeD3cJ7jf6'
        b'FpVzcLf6FqGuo78vxq/AmLyX9y4KCvE1cyjAVyVWS/6oakMzX21sFqpNzXiUaZItVeZqS7NEz9Yqa3VEs4GeI6ps1ZHNRnq2Vdmro5pNeFDqjobce8I9Bu494B4L9xS4'
        b'94A7amEb4d7Pw/mi4B7lIWtH/ggPmvPl/dEQLw7usXDvCXc73OPhnoai5XA3eSR/f9nk7yWL/gQ50p8o2/295Sh/shzt7yPHNJvl2GaL3MOf5BFlzpeI4uv+AXKcP13u'
        b'6c+R4/1Fci9/gZzgnycn+mfJSf48ubc/Q072Z8l9/Jlyin+I3NefK6f6R8j9/OPk/v5J8gD/ZHmg/3o5zT9KHuQfLQ/2T5SH+KfI6f4xcoZ/gpzpv07O8o+Xs/1j5Rz/'
        b'SHmof7g8zJ8vD/cPlUf458gj/QvkUf7Z8mj/THmMf6p8nT9bvt5/gzzWP18e5y/0WVs4/0B5vH+auxc8xcgT/HPlif7p8iT/Qnmyf5jM+2d4TPAl1Sd4zB5LGfZSnNfu'
        b'7eXt6y0ok+Qp8lQYP6vH6reRoE27uVy7N8ob542HmAneRG+St7c3BdL08w725niHeod5p3pnenO9s71zvPneBd6F3hthPvSTp4XyM/vsPrMvvUXwW7zM9zzL10Y5R3tj'
        b'vLHennrufSDv/t407yBvujfDm+Ud4R3pHeUd7R3jvc57vXesd5x3vHeCd6J3kneyd4p3mncGlJznnestgjJz5OmhMg1QpoHKNEJ5rCTMf5A3E1LM8uaVRcgzQrEjvSL5'
        b'MYiEeLHeHnptUr0DoSaDoSbToYRC77yyHvLMYJrmCJ/dE0ElDKK0EVBKJPVnAvRQMqQeQOmHQPpMb7Z3ONQ3l/K5wTu/LFHODZUuQl1Fyklaa8VxbLb50nw2X4bP5rH5'
        b'8lqEFhSFwDdZ9CaLvVlr80TQkf8s5iiB1BOYjgFCie7F6XAHZgphPq7SoiS50eYJV8EHBdJ16cK2nmmuIemp5UzCtTi1pL68yl2ObmkbEPrQGSOesnZrsctRVkOMOZSa'
        b'e9WgKy5zdNitvBhUrEmXANCtdLrLFFTmMDsbS0nMh5Tr8Qi/tixgC4o6kYgTj7ZXqgEywpMVbYlX1ylOlwtCYlXtStS+RoE45ZeQ91Vs8lXqG3rCw9CrqAd4lQvKd9fK'
        b'ToCvpIOBUvEBsa62LmCF3GVnWTEqXZjLHOxsmKl6tpvICMHkgLGM8glElNY6ipWV5GMU3aM6Khtqa6rWhF5Z4VUNyyxgg2eXu1g3M2qGUFlV8UpXwARPlJmFHmpcbhd9'
        b'JVl+KmF1sdIeQHFhDFE6erDTW8VFAho1tZRPFQxgcQlLoDidq9FkPAZQ/oIChtIqZ7ESMFYVwwAPD4gl5StJDh7N8TA/IgErOqJmz0wk6SV9kN1KcakTPVU6HBC9xMEG'
        b'0gRPKFARkByKsyxgd8jlruKSKqejtLj0VibhDBNDZvbikHHQJgxJ7+QxECcIkl/MNpfA3BShgBdatkJrtCiuMAMFAwTS8RVagJJeleQJ6uJ3LdL4nZaqcHJmGIOScTpG'
        b'YGOTtkMdUQTOGKzjM/DVZwJIZ4OFlYg18fAAg4Qy1P5IkckxEOmEiL5UEkuTPJLPWmlW7vDZmg0ewRdRKSiz4dlYM4RCnLLcZ4vgmg0+jomx+ay+WPhih7bbemFfGH0m'
        b'CPdpETxGX08oUah5xCMo2+Bdii++DG347ERxNCinB5RzgmInQOpkzK2mEd739cVQvA98MQB3TKQxl9BshpgmXxzElGCvgL5uQd2cFzwS7CA85WesNN+DYslGSGWhfHtD'
        b'rKDNHyvkoKf0WODJik/kRAnCCzjWfh9PeayFtFG+yIigzp7oi6avkQlooRgoP5nzROA3jwDwNrIXx5TJyKKqhblYCIn5UX9CnnthHKy+JChdwH7xGOJQnyaB9QN8P0s1'
        b'7hXsCY+gyzCz+WL7bx2f9Ps3YFr/U3xtnNWjjCEpJjvDVglfRQkmo2AmOaVY+EWLzK8Tk1xiXp2MgN8m8JJoF+xCNJ+M6UQr+YCyd1ROjdH3H1osrwr6YrHDUKfriyUu'
        b'fLHAVxEHzyfBHjWsw/LBwcuENBI94cQ3eCTXFZ8BJqPRh794GHQRJQY9JuUOj4mUg8weKI1NHlguSRO4GtnX2zfANwgWQWKZAQ1RwfSd12z1obSdFXKN8Fh9vWFR/hYm'
        b'XlQEl4gbswjPdnz22GjZQT6eCEARo/QJTDKI7JvHSt7KanwDfZG+3jLvGwD/g+C/r29IGe+LwXJ8fXFxxQGKCe+TfLwv2heNqFm5iRa3AScxLKYYjxlaEwkTHu4eWBo+'
        b'ewLXbPfFAkKAb+y9OFg2kYQoRECqLPJv5qYc4LkMWryFbzbUfAxvjL4MyDPKE+VLoO8AEKC2Ub5UCqXqoYEUGqiH0iiUpodSKJSih5KC9aRQbwr11kMDKDRADw2i0CA9'
        b'lEyhZD3Un0L99VAfCvXRQ/0o1E8P9Q31G4YSKZSIobIo2ByyEb33cFsQbCIQgLb6BvsiocXRnuh7BNchj0RXE15prvTCuQJ5QN+XoYFzvTW9OFRbhP7sgXMMchXJFIWE'
        b'PY/Am95neiR875GCjnLajZfH/F9Zt+k5/waw438ePlUjfLq/HT6hvKRg1m12G0U7QapYiVSk8feVZMavaBYW7WzEGgUO3rb/CwIXqz9bv5RsqFKN1sdsQqxoBThm57v9'
        b'fSLF2sRoPlY045ns15LBJiKt3wHSBXXPCNIxY5wAy4CM9pl1SGf0cWGQTvQZaHsHBMZnAQIAIByTSg83xdI11vIvcK9AHfyGMWiWgHWwiB3SqVGWYKMOY6MkWDKIiwgA'
        b'oGNZQ1pIBBXwAgM0Mhqtj9J7yUMxoYmRPiPu1dAVUQCyIhGAYwjF7X3WrYN4zDXCF4tLEjuLwJloAHDrs1wHKOGEMEF7AH0ARAHM48LE52hIQULj6H6J0nLfowN7/M/O'
        b'5I+MuslMjuYwal5JJiufLKLGUZKIs8nacTZZwzteRiQTEEJfFCLAoY6X9I4fQh3fE9Ay0ZVFXzAcj2Ey9z8DZpgNVZDpm3VrEnUd6uabEkjjAUMdOhmQOp8pEVVtJdhR'
        b'lntE14Ygqs1j7hIgjrj/GpRL6E0ToSnsXAbYZWAQm01NVmQ6kOZgnMS5uUqr8jNmtId5A6U0CZjDqvuICLd7o4EAj/P2KjPpHnrMYaWYEbpDPeJ9kfgumJrte4BNWGBV'
        b'sXoa8BrK3YIsD0o5D1LCO/hiCaUM1QEQ1IHtHn+6UhIKWQoO+aFEagQaDB1MDi3QXgU6FUILmrVZiJnqRgeCprrSxYDgLlF+hzTk2/w/bUQkYC93OWpLyhwNCgqHK2NM'
        b'IQ0eSbcwSfMsnScy/Qc5MEn8dwL9VpOulhVcMNFwtdEmgILzaELTiFaLBNwKrKKV3L3YeaPFJiaY8G2sya4zcGP59ATGebgNcyfXH6JrjUt5Cd/9GC8/wctPmQg3mg1y'
        b'4XTlAlJTVXmJ8nN6rC5236r8gnS/4cFZjF4llF+S+k25rAygTIEqD4jFJUDP31rsQg3xgEm3hxUwuYIPK6tqS4qrXOmR/5ouS1/8b8CB/9/LDzmywDn5I+SQBXCeC4J0'
        b'7XGF3ZBARwp4fND5OIP9pC5+ti7f/vCfUf8PhY02MdYkiXNH49orq8Brqk0ShyXj04TpuC4Fs5GIR0Ggdhaias+THPmTcIRz9hwOfUVWF9fBsnQrygae6Q6TJQR2NvIi'
        b'rbuZjaXOOjQMpaCsA56UlBbXu5wORyDO4XDV1xFHENlnqDgDbyMc7QHl444GLcKUbCdU18r1VU60ecdMnEoAWKIFQIa6Oq9Zx03V3/cXyJ5v8Kzo/wBngRtn'
    ))))
