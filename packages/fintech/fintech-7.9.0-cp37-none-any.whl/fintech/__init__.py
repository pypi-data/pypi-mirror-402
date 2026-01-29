
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
        b'eJzcvXdclEf+OP60LSxLFWm2VVFZYAFFUbEXDHVREEWisgu7wAousEVFF0URlyZg7wW72MDeTWbSL8nlklwS93K5tLvElEv/fC4ml/vNzLO77AK2fO71/eMHLx6eMuU9'
        b'M+8+75n5hHL5kaC/qejPWI0uGiqX0tC5tIY5yGhZLaela5g2OldQROUKNayGW0+pRRqBRoj+iyu9TSKTuIaqoWlqPqWfzFFajxKJYQVN5UpoaqVMI9JK8jw1YnSVknsv'
        b'cvXWStbR8ymNSCPKlTwtyaEWUHomBz1nUR7r5R73+0vmFmtlsytNxWV62Syd3qQtKJaVqwtK1EVaiZy9J0Jg3vPAFwy9jY4uoO0tYdGfyP7fGIUuVqqQ1qC2rBdX0XVU'
        b'DVXFrBRa6Boqi7IwNRRNraZX45rRs0eRnFUWOLpEiP7Go78+uCCOdEsWJZcpbdQP+PPcUjGuOVBAof+yjqdXRX00Ygz1GZ/32yknqR4QkYJiMUSMlbKyhawTKvqhUBW7'
        b'QuUo0B0qTmnGBYfCS+BElgJuXwWbYOtcWBc1D9bBxpg5SXOTIuBG2CSH9bCJpWZmC+E50B6o87j5usAYiXIqNku/VH2hKi38SvXSP6I2R6iT1F+pXs0POONfUFxYypxf'
        b'FzIujlo3TTR/x5tyxjQE5YAdKYs8UaGpsDESl5puVkTAhhiGGgQucPDcRNhi6o+SmVNMoBG0wJZUlARsBC2i0Qzl7c8OhNuGGvAAylkbEy43YATkL/jlfd+JhYaylVq9'
        b'rJAf+8k2b7XRqDWY8vLNulKTTs/g9uMhokKktDdtkDqyovK4QrO+wCbKyzOY9Xl5Ns+8vIJSrVpvLs/Lk7MuNeGLnDZ44XtPfMGFhOKCvXHBn/syQpqhheRqDsNtPgMO'
        b'Z6ZGRSsVEaA+w7VHo+IEYO8YeNJ/QikGYtesl+hX1d6eVPkz9C85lbF1FMGWw4PM1ETh576Uam3+/kFcsh1bPpxCvooqltBvM5RvR+WaCV8NSuSzZGezFB7mVqNJ+vrk'
        b'KfzLt6VCCsHq22HUS1eWCymzAgN3JRJe9QQnohBEdbAlKzaTH/vwaLh7piIc1sVEJKfT1MKnxWlx4+W0eRDKAzb0T/JErTEuTlVIwmEDOAdOcFQouMWB3fCC2DwQp2mA'
        b'baAaDeLRPqAlBjUaj6eI8sxg4OaBw0gSeGVQLmgMg0fcBpoMcxDYK2fNgSiRDNyCB1MV8pR0UFchoIRZTKAHaDP3w1VcHPJ0KjgylfRocrKCoTzBTgaeAJfLzQPQ95wK'
        b'P9iYARtS0qNhfRo4pZjGUf6ghoXVwbATFY8RbQ6wwk2p8FhIclSygiCkgPKGDawyFraY+5JKQFNAKvoqoDiOBvXJ4EBwnBmjMjgDGuFxHovTk+FGeTI4Au6gKuAWFlyH'
        b'tXAP6i4MB1wLD8DG1FFxyRjvmzOSQ0GLgPIZzE4Au1ejNLgtcdGgCadITucTrMNgnGVHlsNjKAXurZzV0Z5JaJTKYSNsSsWtDYB72TlotI5JwSnUHFyMBWyG12Ej5xGl'
        b'hM3JUdFC1CUXGHghB2wkzU2E+7MjYXMa6u8ouSIlEuwQUH0GsnDLWLCNNEqB+mNXaoYiORJ1an1yVEpMdFK6kIqiBEtQ0bvAmWVmjOpgU/EY2JiHmtkUiRJE05QnPMTA'
        b'KzMrzSPQ58lLDKkYzEjcnNnhqYjGmxFvaWGXZM1WCKkZnBBWg52DSY0S2JqO0tZnpM0JT0qDzcq0jOzZCrgT3kTVJggSfSROLsa48ta9hElbacQWWStnFViFVpFVbPWw'
        b'SqyeVqnVy+pt9bH6Wv2s/tY+1gBrX2ugNcgabA2xhlr7WftbB1gHWgdZZdbB1iHWodYw6zDrcOsIa7hVbo2wRlqjrAprtDXGGmsdaR1ljbOOto6xxlvHWscVjrezX6qO'
        b'Q+yXRuyXIuyXJuwXMeDehIIP+uvfg/1aleahGD0OBCx7EHcozoMnU+AVgkYzKXAbE1GMUiFXgDpENOsqRJS/igVno/0JrcBtcGsUbF0DGxGmsRSzhp7qB1rMIXjAboKt'
        b'CFnByagkhMhgPc0kwRrQikYdDyciALg1Uq6AdQjNwXGwVgjamUhwB+wxB+HMLWGYKcD6KDTQXDKtRwLjVmomqXMyaIJnUxF94U8etHYxOJoAz/DZtqmGI1aShGHhkujJ'
        b'GeACQs7thKw00IoKREwhMlrOUAy4TOeurDAHoy+rwXmwPxW0I3oUUgngirCUCYfHwA2SbaVHZCpsgIhfoNqG0sVx4EyMjlSGyjs7D95CVWC8o1GRzXTa5BTyrQhsfyqV'
        b'4FgUTcF2cEYYzwSNjeTp+2b+qMgURFEZAmpVX+FUxhteLCK5xoPL8aSwcAVNGeAN4QpmJLjJmQPQt2R4pTAWHELUHI6g19OTYe0Ivs1n4VY/BO5N1PAUDMVOehY4PYyM'
        b'wRKwezohCwu8KscELAZ3GGBNXE4A8QcdaOw3L4aN6Uj/YCz0FHhIyA/rZvmAfvA8OAUb8BdwgZ4LWkaQIiNRpn2pmNhhE0fBJrBNGMpIwJXlBBgp3AKbFoF1sDEJnEE5'
        b'q+hZcA+8TLo5De6ArfAgorPGjGgMaAP9FOrZOwQWKTwXpgDtkdFwo4BUOG84GjecbRA8BXYhDhIzeCqRCx5jGMQX9gWYZZh5wDsQ9X8UbAZ1JswZklG/KgVUUDE3CtTD'
        b'XQTkSblgd2okbAiaAs6lYNTwEDJgmydsKWDs1ML10HyQ3mOlnZoPU4d0nSoWkR5DSI8lpMesZu2kt/7Rmg+r1NnGHqOMkzFOPTPoS9Ur+Z+r6oo+R/+5N5um7vZIiqN1'
        b'hTKv5xZEeWaPzVk7cXttU5N0wNSfC1sTLntvUAlfH0299Zl31cW+cpFpMB6j5ogFvMYCN2bI4cZkLMtAS6KIChzGsRzcb8IkrAJtskhFN82GCDzQMdo0DHMJTSyh8ah0'
        b'xC/ru9IMApsQoTVwcNMSuNFEhHDNFHAJpwV7sjIQaoNmnA5xUzRecaDeRITwJtC4BCHBOZwuAxMpqCc1suzg0ZEmjCMmUWKkIonINzG8CPelMWA93FVpwpwpDm5H4g+D'
        b'A5s1YLNDavAQDYsQZARPtStP3dQj8pYoRzZuqdpYQtQuXzwUayhOTPO/3rSENvg5FTDOxmqMJhtrNBQYsCJlwExTzrjoXIzBH9/3cZRNMq93Fl1N/eameuHWRYHzlZig'
        b'YLOQ4qJoHdI1znjDzt6V7Gge1ZhC5jFV7KLuiMb1hmifff8BZ8SS7vo3332pWvjHwc+88Wzr8+892/rCxdZNfi95F374KrKixnO/Kr9GSjKGeuoscDg1Khxu0SDemUoj'
        b'PnGKqYxK44d0a7xnNwQCh2bwunFbJd+VTO8jYTbpSrsU4DWUly9tCKC6FGC2LH/JA7qeNvR19jrOstGl13/y7t7rpb4JkUSZQkzaQAfC3UiS7IM1zl6n7X9ZDmAsuDcL'
        b'5bSSB8Vem4c7/N76sryy/EKzsUBt0pXpN+HMhGUw5nA8lImIQBoh6ZqMlEiFUolVWqx0IC55QQBugMsIkA7Z/xEKDwcI2m0uAOCRMcGzQYiZ8lUng93ggADpgjUsuAVq'
        b'XRrvhnKjMcrRvGVn5QoFTsRjHt+2o6neOJxQaZaj+yHgOqq/MYOoc6A+Rp6SpkwfAk6mIE0LaYdjwQYhqEWS5ZyzOAf3xTzGOIpycF8EHfeY/LewO3SS3sji6i+3aGMK'
        b'enFmQuupT79QfaX6XPVFgbRQpd49OFz90j8izqs0J7Toz/9z1Vl1ceFp7Ql1cb60KIkGuRsSNog3JG2YeEwsi9m59gLSWQ55rVldJacJZ4Q3JoHjRnAmSYnsFx4FLBWU'
        b'H2xlQQdo748GluA0151pdaMXQV6BupQnGClPMAMZxLJ8EetaGWos1hWa8rQGQ5khemJpGUppnBxNMji4Gac2FBltwpLl+L8LWfUwJRkDFouGUCeBYTm734XAPvV3JbCx'
        b'6F0uPAKbPYKQHIZ1aZFIbSRGNNyMtJ96JAqUSIVE2L4FNIoyxyNLbIoHvAJvw406oS5DYIxHBfztatuXqpxnWsHV1s66czXynW37Oved3Dds4/jaS+vktddqD29vq7m2'
        b'oa3mZEg4vMtQn+VKFk/5FvUvJgm4AbTCnchI4MB2pDkso6dVwgOOXhX02qvdutbTpftIB0v4Dg6V0BzjKzT06+JKvJ3d1X29jpqbOY4z73LpvnsBrt2HGfFAsFPYre8Y'
        b'uBacoPqB6xw4AVt1DxEQtJVyERAPp9MeAqInnQqUhHuZweEh3cnUQaNw8zhCpvAcPDdXV/HOR5QxBmW5N0jiOoYjdw6ubdv1Qs3I/SNrPZJGrb37qmqzIOzFXd7Ut2sk'
        b'AZv6ygUmzLl9ngLtaOjQuMG9Q9HQIYTZapKhD6DNs4yoCcoohZIX8X7wDLq5yCLV4kYfE/aKgUOTVhKFIFoRHp6iiAbNGagfWyKTwZlwXrXIAfvn5YkL4dokokLQcF0x'
        b'r3zYk8Ftc+wpQ+E2DqzzW0X8QkPhpUxSsL3l4MZSpEUSlSZsqGDASHDjYaLNy6wvKFbr9FpNnnZFgau2MQJhFC20/xr6d+GVjUUpHyjtBjixCWc55oJN77tJO9xEJHA6'
        b'YPMgbSSx7pMQv2lKTUd4hRiQkBq2UpCRbnTigAOdglyYK7Ffncz1iXQOjupN5xArSzHDmjRQLNbMomTaNa9VlkZftCwuig9Z1J+meN9JXTbS4xXJKfA44hOXKEoAD9FI'
        b'nzwMrhBXVHrEDz5bfejwb8tPeP6W0zfgVd6FNGcqzVDc5zOZcnVedoiIf/m/uf5UGBU+W0Kp+r8tjaV0JXXnOWMl+pJX5Jeq1qhPaE9oTxd/ripX1505of1C1a7+QqUv'
        b'jMg8pc5F6Hux1S/iBXFA4wnxSTXTvuWk9qz6tDpQ9AX3pnSIKqH2Lp0UtLs2LuD77M/fju17ifr7zsjPM3P6B3ecZF/psMW9ParvrLVvW+PejhXGlV+mKI8Zg79s3IY4'
        b'FWaq4kh4OdXudEH6LWhl4AVh2SzY8QA28iiRwBWrjcUEvWQ8eo0UI4ng+CVKLcILKblDytVAFzYW8nhsLMSJeDhzhwvivekmBbCMgLtoGTLtkHKLsKAvLQPt4CgyAc89'
        b'xIVMd3MhP5x9uRlSuNkePXBNqjRjpRzUehYaQSfcgqqMoWLgDT+CGenzeD937KzBAS3R43h0eS2eIUgbO+/rmX2VZsqAda/eLjY6T3dh8mDOWI8eftt7UvHqSG8Q6zvz'
        b'T7su7XtOfuJlwThJUBI94LWIxCFzuLFJysSCCskvx8YNsX3cd8L9b7I2PxfCxr//7cSnOeEuzb13PTsP5D83wO/C3eBd7xWfyTxat5v2aFxw7pc7gQv1b7dHZi71/gvU'
        b'j/3uoy/+maf7c9Dt25ds2kELktZPHjLqu4KcVUN//ZGd/5ehadEX5Z6EYS2ZBHbYDb4rYLeL0cdbfPCAmegiqxcKjFFyuH+CHDakRSiSHe7uiKcF4M6qKuLsRnz9dDi8'
        b'oARnTPgr2FWOEnjBana0/xTe1NuHbLiDrlp/+jKH4Qg3DyKoHgnbwE15P2Sy18H6KJoSgmZGAbaCc8SsDAb7NQ678vKIHqYlMitheywBBlwDa+GtyBTsC0pTCsLSKE/Q'
        b'ycB94DhsJgYIut0xC5v2p0FrVIQ8GrYgPRvVIOMWwxtCXpQ0j+jHM/0mLM2wibIFbuBt08tgW4IJYy/YD06bkZXTZeLA3fmV8gXkIzy0EuyMVCqSo+RyBhwdRknFrBjU'
        b'atzY9EOsTmG5Ob9Ux0uCMJ5UZzLI4vQnciCAyATeCpWgOwkiWSltkLmQa193cu3F/99lEOF80IVS77iZoaRTd5dPjwxPR/JsP2xAZrgQ2dodDKiGB2A9qbFAaKcyTExi'
        b'B5VFs9gosdAhVJWwTmQR1lE1TJXIIjIqK70t7EHKImyjq8TzKX0AR5noEolhHE3h3wWUPjAH6eUWMc5pEeIyJlIaGudtpQ2cRVCeq6OqBCsOWQQHmTZqJrVo+0KmyqNK'
        b'gmuxeNQwhkJSH4fuzlqEB9k2VM6KQnTHkdQBVZ51LErpaWEKWYukmaapiq0IjpkklxRBKa3zsAhraJQrrE5SJ8b3NTTJKSY5xS45X59PWaSG7+ukfA4HvLOpisL5VCuj'
        b'DyOletYwCPaoOrqOKhHiOwSNQMO00XzqVlr/K0lHm4SFDEk7r87TnnZeHYPLdqZ8k6QUklSWOoE9FbpzS3Vawx4UaTiNYD1Vh1pdQ6Pe9tIID4osXgfFGpFG3MbgNxYv'
        b'lLdD42HxCqSqvKwiqyfSEFmNBOUTW1icr8ob9YB3Da0Rl+AaP7B4azzRyHjrhzjfc+j9rxoprtHi3UYH4q+cxqvK28K0MoZZCF6awMsYwjTeFpQjCLHrQgal89HLLLSF'
        b'KWHRt4kaH3xvfy/W+Fr4uyEu+VUaPz6/Mw2uzcfio/Efi/97oTTNFm9y9dH0sXhbvHB5+Jve2+KDv5TvtHjhZxM/xr6oFb6oFQGoFYzhvsUXt07TF/UpY3iFf0J5PkV3'
        b'Yuf7j/kn/B610k8TiJ4pTVAtE0JZ/Aj8vqj24DovXMMSicXXAYOFbWUNMhNt8amh19F6scmTv7MrRyHKufdFpWqTTq8YeZ+J6rL2Gbs8JNY+VoSLEGktklTRFnoJtYmp'
        b'4LDhajf8beK8PL16qTYvT87YmOhYG23q5ga4L5lYqjOaCsqWlk9maLsfQEit7F9QrC0oQRZfl1HYlfA+Kysz3Kej7tGkhLJCmamyXCsbZnQDUuCgfpkDyEA8A23Bwpox'
        b'cnUI4BraDnBxF1iIM4YRmbnsIXzRMByD2QWvAcvh+z5q2TJ1qVkrQxCFDzPKifC9H2zUVpi1+gKtTGfSLpUN0+HPI4YZR9z3Iy/wrfMVR659XFI6ct/3kC01G02yfK3s'
        b'vo9WZyrWGlCLUUeg6z1fAvh9esR9esh9j2HGp6Ojoxeh91h9ve8XJSsqMzn6KAH9yaU2gU6v0a6wSeZhgBOx/YheoVqNNq6grLzSxpVoK5HVjWou02htHvmVJq3aYFCj'
        b'D0vKdHqb0GAsL9WZbJxBW24wYO3d5jEXVUBKkvvbPArK9CZsSBhsLCrJxmE0sAlJ9xhtAgyL0SY2mvP5OwH5gF/oTOr8Uq2N1tlY9MkmNPIJ6BKbWGfMM5nL0UfOZDQZ'
        b'bNwyfGWXGotQdgyGTVBhLjNp5V4Ptpwf84KkUpJTBIodqPguZQ/QoBgs7jgaC0JvWshi8ccLQn+7/upNBzIS8oxFJBGPTCB6CkXabCDtKwwgAlSM7rHz1pv2ZXB+Kcnv'
        b'zWAx6s3gXOgN403KC6b7o7ICsZBleFG4D9mAu1PhqeHIVkqHzcqoFKTI5LHjwc2hzhkAMcUHUhA6+AJdkLRiVnxgoQ5SRP68iaQVW8VZWGP/Cm8TUl7xnw5JuL1slcAi'
        b'sDAWdiKiGEMmkoF0iRD9R5IihDrIIO7IhlBtSOogKcQhzs9hWWEstHBFdBW3IsfCodJnI2nLYkmCpN9+RHlYJgg0uESBhkOlsPgJ/UeyEJdUUcpLF0O7his/rcESWmAR'
        b'kdqE/Pf5FJIsBAJSEjORf+bsz9xEqsIbyUCGqNwCJSLgp/AwkrFMxpennHf4nVxgmIBHmDVqTTZWrdHYhOZyjdqkNUzCX8U2EUa+pepym1ijLVSbS00IZ/Erja7AZJjl'
        b'KNAm1q4o1xaYtBoDdsMZEnFm4SPQzMUdi0MqNHmOcsMxVxlOsIxD+ICxzJfHBIxrBL+kdDDji559EUaQaWJ4Cm5JSuWn70F9DJ6cTOdnEiPBFQHcCfbC7aBW6GaC4Lqx'
        b'AUvq6jH7S+H530JPh31joR0Ws6tJ5NSvNOhSh8eZrkcSfglV7ovwDGUyjEaY4YXe0Fhu1tCeyNYhkglhBJJ3dB1b54nv67HflkNA4KolCBRpodjpI/WwMBiDeosPwj1J'
        b'3KtfYQA4C1YRqMoTKxajaln8RFQlZRWDimAxYDV0CWWIx3cWBEYVqw8gwAkRaifhO/SGmY0UPvImuA6rMIgECtEzRneiZAXPp1ZMt+ByE6pYCykVpW2oEyI0ZZEaw+ml'
        b'+B69J08WzlCORQ0iIFSOhSNllM/HwVrRSNnkTIJCBimcH9BIjaSplVLUUQIshuejrtKgd6sFjuAsRByo45ppu28dYRg2V2yiZWoD8ZCyRQiLESM1lCw3JGDsmsHjYZdT'
        b'NA1fCNouImivNRjk4sdmjF0YK80jLLEcVbzUmOrEV4SlDIOxVIp5IMOg52CG4CsjRXgcjLA1lF4Zqy4o0JabjF2CXaMtKDOoTe4O4K4KkEB+GleN2+FwY5IXGBXknr+X'
        b'xbM2Ee42RLh8kQudzfNwAjSddgQjsTzHH4i4b2jIytAHt8GhQ+Ti4rT4XvK75E+uExyRvbIptN1fQLGyoWQGWAv3wdbUNKVSES4XUp7RjBC2wyNV8LSbq1Ri/2/ERWqp'
        b'XKTh5TKE3EUOB0Yuu9WDd2kg+vMsFJAoQ3ENncs53/OsAVOntNCDRB/i7wIrxVG5QoKSIpufPVJwlq5Um1am1mgNvU9FE38dg4pEfMdlMoR96GTIY7iA7WF4uQkhRnAm'
        b'PCk9Ojl90TQc2FOfkZasyIR1GVnhmDdm49gZsA6e8FgAD8LtuqQ3ghkyg705f8CXqq9UX6iKCyO2h5MgvJfyA3AIXv5Xqtfzc595/6/Rz259/mLrpk30iQ3j9w+rHbxz'
        b'bZwXFXfWs3DTLbmAOBl0C+BJLh5egE0KHPRVYXdUhJo5sAFez+Vt/xqREhv2HuBO9wnsRLiOn5/c7Q9x2FfLmsHdJpwRt99FjPuBoG48qK1ymXZmwPpgeMU0E30MBxdA'
        b'O2hc7gwfIvFOyfAS3xugATtBYmBDGmyBTZpABASohy2IRVMoyS4v2BYMt9mnYB7BDpCSr9PrTHl5rlM8a1AypMR40ytDe2BFtCODc4rHqC0ttAlLydeHT/Eswfc6R92G'
        b'YnSpwISB7X2qGv1ucnXvPazy3nEznsdNFqE7lorCQqETP7nHx8/epxJFSj6i7+YUeADHr2z1tQ8NbGUpb9DO+k4ARwgKT4Tr1WQO9noBiR7tigFD2Gx3kV3KpKiF4SK4'
        b'dRE4Z8ZzCnmgGu7HuWLmhIcjnEtSwAZw8mn/ueEp6bAlKjpZkZJOU3ofj0nFWjPm2PCQDziVpZiXBJvkKelp4ORcO62kB8ItNDUabBeG9UvQCZdKGCM299bN2vKl6uX8'
        b'E9pd906oc57ZiSdMco6tl9ee3DBtb9uuzvrOmpM57EtFws6S4IScC3cbSqst20OFIzssHkbRDJEx7i1mu/f22qZnpXtDqO9e8f/iVzmiGYzJnuBWFmxMzQUdJHCQG0iD'
        b'Q4g0ThJP2lJwuCwyOjkqQg4Oc65ushTQRmJGwC5wVOVCcGBdgAvNgbWVJhz9Y4QbwKnIaEUSPBSpYCghOMLEDvckfrZlquLU6JT0qGR4ETaDjc7YEwE17ClBLvu0Y07u'
        b'8ZU6rwKDFimSeUvLNOZSLSGMAAdhrCKOMoa3C6T0ykE9cdQtt4MKMdYjUsESq4tEHjxNiIiF0Empk1hK0GWFG7E0BLoSy6MAcaMYTwd6T3VQjKv2SLvpj4+infXd52Kc'
        b'NouTdryVfAjoxafB6a6QSHgr20k7ky2EdFYYwVWeCBDdVJHouAeTDjwYZsaTkeOSBvcgnLnh6Pum7qQDWsG+B0c+aLpFPtjowu5xD+KJpeql+Rr15BaU04D5jjkb4/At'
        b'T9hsfACzhptTwZmkdNDsxEy4zW2Kmh3lbwRbMv3hGQqchhv8xGtAtT9oI8Fk4IxcYHewN8HGKCRHjsMWIksy2ZFgX4mzNdhhglV6olFjDdKulAvQ6JJxdSrlLJHVHBpP'
        b'lownR8aTXc31FrjAUC6WgsvcmhlHoC5brUzF831ieDCaDzHISorEgYnZiJQVcticlpztHDcBBQ5qJfA2PA06yQxI4HI+EDs2MC7kLhuGUN4eyS2mfCkqNjawIWhxmj2S'
        b'u3TEQGoi4huxq+mAOM/+FBn3fHi7NDUSHACXEAwOAPi4baQt2CNQ0MgvXeMRLFlC8OtpsA7Up6bi2cnk9DnhsH4+zzTBIeEcJ6RoRBfCThE8V7BQ56+dKzBaUM6FftJJ'
        b'TZ0SEBuQ+E1Vcu4XUUlj//Pys++NH3dzqvWNRF1Q6kfpqy+8PGT59f6vV6YPl3je3fYDeG7foNDU0UW3UqZvnjErbEenscb8xdslOSOn39j453/f+eeobZf8SuCVFwb8'
        b'8OeCez+cvFl/OWVdrWdolWq7uE/NzzFlwfunmK8NpA9OkYsJp4ySJmNUSIetbvF1/FQLqAYH+Ri8lrIIOzuFNeBwNx0GtMaRGenoJXBDpDMiGTRi/EKUKaIGZ/WBrQJ/'
        b'Cl4mEzyLJ8HrPHd15aywcxphrvAm3GmfNs+CW+AZhJ78LHeGHTIveJ4NBpcK+Amc63CrLBXxaPs8eDTSe/1Xg9PgKgubjENNJAIc7i1OTYHr7anwhKXnWAZulCF4sDiZ'
        b'oMx1j2nBES0eC1nQkad3mxb5PaaRN45cySs3lJmIQ4Aw/v4Oxr+G6s8Q9xAnDqR9kakkJTMpK8f05LvaFdoCO9ftMjLcy+ZZjIC3XrqMvC7R8Ahp5ZhL9XJmJUKiDF12'
        b'0Q55VU1+74W6TsRgOyJDKP89zKrK2x5Rw4LN42GnIBFemwouDQMn5dQQuC1gyVhQX4phC14UzP3oT4Uncx+N+J65PHJr32k0P50+fdfga6zKh5qqGvX+qC8XxlDktY/x'
        b'h8r7A8MHMbM/pH/LYRM8Kd0W20LaeAR9a/yxZFjTLS8Q61v7zd3k0he3JumCq0e+t5aeXmFQJ2wepS8PG+QVF7bn47ov/n1vVf7QqqRituBF066+kW1rR33gG7eo5B3r'
        b'Zxv+su255pV67uPzttzOCbNvWAODblzfdWfWhITJF9fsnq+6nvWno4pFbR+nDEqIL52/JyKkavrf/z3dkznid+C7xMwfktOEN+Iqpsx+0zw/P/C1gj/+NmuaVpCweNG/'
        b'6NxTUe9eb5N78ejdqkI6n8v0ZDG85QxsPbnQHrcYA6xIHQI3QE33acOjBl4fugwPZPVmgKyEe5ANstfbFIFSTYGbl/O05hhHUIeGDLMybGoszafiNcJF6H4PUZ/Atkng'
        b'DFafFIwRtvPqU1yMCfvKwV7EQXd1H3UB1W8MBzaHozqs4JoJe8Vy4B64vYdNEhn8AKukp00C9iLTBzdxuCKQ7yewdUpXVhHVF65lkRK3qYSQ+uIZ8CgfZYMhWw0PkM7M'
        b'ZsNBU4oJo7wWgXaFXzTBx5EfZcRg3wp40ZMPgGsfBI67hPyGIO5nN8KQknGd72wraAhwl6+H4AWHfJWDjXzvXQabQQ1sTKPhiYkUPY5C7OsC+4Dohd/t06D5OX8+NMyF'
        b'hRA2FNHFhjycGiiD4/A47M9mcMhYYJAQB44xvvTKAQ9lSm46qdD+rov1eDwZ3IyhgnIz68rRpbYbE/q3zFVXfTh4chE/JyHJs7/Iy7NJ8/IqzOpSfj6KGI5EISZ12bzw'
        b'IjW10VigRSzWbpdK/29TCDYPe5moPNKoInQpo+2aopjxFQV7mfHiP1iTUswzU9gJDvVkqAyVAG4JkZHTrnBzgDimusnIOhw7WlbDOQJhCzkNo2HXe2BHDnHUCHjHuNNR'
        b'M1ttQh2oR52nLOBcSnVaw+PQxa7X233EhSK7DsjViZAOKEA6IEd0QAHRATnsr+yp02MV0zkf5xqyh3V6pFAdzx5f6qLVO1T6keCQnCFL/8B5uBFuhzfBWddkSBOA9RwV'
        b'OpNLCoJHyJK6CUhdCACbXFNFRiQJqVAjlz0EbNUF/zSXM+IZAEa8/UvVgmdawVEvZMa+1L6+s6az5touHZ0lShWViP4y/R+5G0I3DLngvT3gWOkymden2pFj496JfS7u'
        b'3Vgu7gg1ssiTGveTrz6pSc6RJQmwFalA13k7FTHlcKOTLa8Bt0k0OjgJ94I9PAv1A008C9X4EE6zEG6GzQToVFDPLxXzh5dAp5YFpyeAGmIk54aMHwHPunOrFeAA47BO'
        b'RU+mqngUopHPw+YkYQ/+XexhskQaQHOsmEHGab8eqBLtzMeTidDGFpQabeJCcykhLhtXjtLahCa1oUhremSoFmdYge9xlJthJb6scnKB5ehyoxsXeDHYlQs8DDo5o8RO'
        b'cswHDAZ8MRK2SEhyqdZUXKYhFRhMjm7pLTjF7ARmGbpcc7hgsXebhIVngV1I8STINgpswvgmdl9bOEEmRPbW+iJig2zL5CO2fAuMUV8YxlNuNpI70blNyTiJjiJBjY+5'
        b'WM4xQ+JOdCFK80iMjB1gNzxqRFrCRc8KM7yMZP8V2GlaBi95LgMbfcqlsMEMOylqEjwmgB2DwXXzRJxrPTwyHeWpT1PCjZHKbOKYSkb/6jMU82Dd+FXE7gZnYF1UNOjM'
        b'JH7Wi+C6BN4ZEfzQBdksCfV4vMjNwu6e4F45iwzT5E6wTR4JTqTx3ACezUrHMX595rJIzToHdvLLTzcvQ81CVJW2FJ4nzYLbIsHJcJoKBZs4gx5s1r1V+TZrTEdpX2aD'
        b'vlS98tkXqtxnOlrbtpysOfnSyZqRjRV066VWv5dEnbsm7MwMztoZ+NlfR9V8OiH4/N3GrxKCAzuq58aOMsUK4o4g1lFeSFFvLvTfHJskFxB7BdxGJvtVRP+bkDlDVqYJ'
        b'wWkmDukzVp5tXJoPj0UmEXbCgX3UWBqc1cL1vMK4Dp7IJJ4L2KAgScBJcIXyAWvZJUNgI2Eba2DtEpQEL/ZrYimOhnfG06Bz+nKil5hho48jdmyQgF8gY1rzyMVInury'
        b'ci2iM0zp7s6tNVQBnuyRkklLCb0yAvGAvFJdgVZv1OYVGsqW5hXqXG0al4IctRIu8NCQsZVOqqxCl4+6sYg2t7CxDPR+OTicnZqhwMokshW3OtAXbMwgvgb0nxe427rF'
        b'/dt7BnFkvvs1YL/vUl9+5e5ixIqPRuJOjYtnomAjJYD7aXARnkkncgjuKQeXEKV0Ll8GLy5IqJCKyyukFRwVOIEtKoXN/Hr2W3OkRngR1PvDTg+vZV4SbzE8vxyTZIWA'
        b'CvPnqsBmPz7I+DxohXdSkWiBLbND8DCKQQcDNnjATWbsqCk0o2E/hcznK6hpESlRoB1uXR4Vjh0TaY7VO1niaH4VOg2v+lDgCLjgOcNDRrKDPbBxyMNyyxBFuxRAge2l'
        b'ElhbAY7w+svRIBloLIfHwMkK0LIcXoZXEF8xIY34CuyAV8yoLVkcWIv6pt1MNOZtfdIItDuQ/J6LvVFI8KWJKB+4ic1EfOk4CeQHdaMDcKl34Bb3UpfDTqlESIUlc4hE'
        b'bo0iKq8Zkz84DI7PBheYcGhFegA1YRysJpESJlithFsyFMnI9jiXlCyC59ZQ0kkM3A/vzCNeoBm+qZ4K7MZIJb6ctGK4zZW9gUuEkS2Ca0Xgpl8VidOFnQbETYTzwV6K'
        b'CqPCngKHCYPfNckDe55yRhWr0t7UePGep3cziJeKOjNMlTaPXerwUl3Xk60FcnRSVenZMWI+bYhIhNMm/TNcJb03mKbMeGHTYHAW7sT2XCSyiApSEIRz+MHpCWQZqBZX'
        b'IQNov868tZk1TkOksbi2Nb31Rgo7Lbj2j1NWJceP/YZelfodHZbtm/pd5umNf21ZywWej3/61XVha5u2vTMvbmOtT/5Hcf+KenZN/J7WJa9/ZDHujAt/fujNZ58ryMk3'
        b'zJ0+9E7gudKDH1UdnXEuTzj8ol/kxtvjpr8zqqPz7I+Zis6mA6z3uIWjU0dtrKg5XP9K0e4v/ue9Py186UzZ6art80uz3jsXkXX55Zc3/H3e8++Xll1anjvx7oJfPj79'
        b'+o33ja8Mv/nZ55KMAXdnhO7f+dvR22V/+9IvJftmqHjOV9Gvzj/f8bxoT+3w75f/bZX2IPuXZeEwoGnC+5/4PX/Ue+mLPzc3jnpz09cp0Z+J/j6jYtJkU9juKcUJb6f8'
        b'Jv9+4wdHrz5v2ga43NfqW4anXM04869/BcRXfLukunT2ZyO25Hz/t48tf0hN/e2TCSHmz5Y3nC6o++W3vxt3b5rnkxT4H//7K2fN75D78AG97YlrUlGP43W5DUiTq8Gu'
        b'I0+kbjKDIk0Y/1aPqyILQsCF4XgtDxoWKx+DuwfprYd5Dg7rQygOc3CwPZpYoMhyvpGUmhYRnRSllWAe41nKwCPwPMpLPh8cOgtVqMRjHDiHTPI1MlXwBNzDw7QemZXt'
        b'kRkYIpSieGqqCIF0m4FXnhaSaOY58A64xbMxeGeFYwkkrLOQ0qdXLI6EdclRyUSACPLgZcpnIjIb4DoimfqCjqxUPJMKm+JHpcoVSqTPBKVxU1fbFdLMIpEjTBpawQY+'
        b'VBreyuQhPzoFHiZqEGwUlcArFKegwRlwHWwia58WC+DNyJT0NBqsL6C4wTTYB/cPJ/5CI9yLPvHloq47gDkyKgUhdxC4zCUp4CY+7PnILHjbLjHh+jReaMJallRuiEwk'
        b'mjhSPNw8JBEjH+kVexwt2s3Q7turhCNSMbNLKi7AMpEj8dG+jITxlaA/xp/GVwnri96F4uUOyCQnwV/oigMpxCQAyBeJMm8SWOFL+zNSxrDaIYyR4dwlJ59M/SeFvNtN'
        b'cp5yVa6Jt1uVJAOX5thl54PkpoBabBKDbeAOvCJnyYoKsBccnwobUx2zefGp4BA8hPg/sffq4DUtbFSCM2l29yy4xExJgEdBE7hA1r0OgTczIxG6RQjxoqALQnAQ6UOb'
        b'UgpYF4UvyKH05WANsvvOFZRz7wq62+4VjDWwMMg5jyF44DwGSzRN7qN2VJlE5vKTqS3SGU1ag1FmKtZ23xwpWuKWNtkk0xllBm2FWWfQamSmMhn24aKM6C3eJQevv5WV'
        b'4djQfG1hmUErU+srZUZzPu+0cCuqQK3HsZ+6peVlBpNWEy2br0M2jNkkI0GnOo3MjoIEKkfZ6IOpEoHgVpJBazQZdNiF3A3a+cVaPQFQpy/qBuNyR2WGIvNSrd5kjCL1'
        b'2Ot0K0WnRy1ZqrZnQ61FUBu0ao0M0wbJpdUv0xnK9LgcBLtBhyM+3UGclaycmzgjKS8teUaiMisxTzktPTGqx9vUxAUzMmYmok7TPDR3dlZiZhaOlFWXonHTI9CWaUsr'
        b'eXjUzn7DVNutnwq1Bhx6q5HlV/YodPa0uUmkTJJRpl6m1pXihrgVoTah0SXxwGRUykpLy5bjzsXaL+4goyw8Qq9dLjPqMA4sGxs9PkKe4D4o2Xrdim6vFLKwnJlP5c3I'
        b'UM5KfiovKSM9Maa80r5TU4y9OdGmFaZumVbHRBeU6Qt1RY+V2rWKmcmZWY+VKUZrKohZoXlQDW6p09UFGVk9WrY6Jk2Xb1AbKmOmlZejvDweZZnLMdo/HgxPXoA7Fej0'
        b'mrLlxh6QDUvLmDEtbdrs2TOnzZ027LFAGTYtLY0g3+zMjFnJaYkPyuWWLYGEvcmwKyVBhrdhw3cOFLLnQnymlywl2kocrc3nsj90y6iRLUOcC/VIrwWYjegjn92ZPnF6'
        b'8ows8kWm0yB8navVleq1xUu1BkXyTKPcvRz8g3ieI1BdLcOcBuE7oRMcv4/BcZQVLVOWIY7Cj1J3ysE/ukIX8kTcKF+NAUKjiTikscCgKzf1aIibx9G7h1/AW2keg+5n'
        b'UyOyYhwz+5nzk5C9l5Wkh3Upgszx48FJuQReqxwPtk0dMr4vBVvhCWkIuDzXTfr4OopOcZc+lF3+0E75w1h9Cn1/z7w5FtWhPVqgUKI0RIwre3eoOAOY7G5bZwDTo9wq'
        b'PRy2PRfECviaifKj++27l2kj9qld/3P5lyrFP5LU0sLPVfdUSwu/UiWruU33pK816dLulibmDmiSfad8Z+Jl73dMskXqt559+1nKv6TQpK7780nBl6fVrRrqy8Ilha/+'
        b'I6qB2SMOXPRMh++r59XhFz1F5wNjozUqzecq4S7fV5/ZJaR+jdhROPA/dXvkDD+r0gprxJGK8CQSz7PHG+xmFD7zyfLs/rN1kbA5dAY2VzkzjVTI7VFPHsYjyFtuUJcT'
        b'XW5gly63hsrgSECrBClKfIh/AN7MQG6wqwYugawOMu96g0t0uDow9jzBjC3NZyD6WzW6pCHIjIFd+ls1ddk1oMeMo9uXDsiJdKB6LxsbdGl1iaGJ/vKYlCiKmgVO+OiC'
        b'YcdDojdZ4qB8/K0s3JBLQPXmsxMpzXiOEDTNXRAXO3pU/MgxceAKqFGCDpPJsKzCbCTuhIvINLoMO+EleMFHLJV4e3h5ghZQB5oYZBHAKx7wDLwJjxBbumx+CrWVosr7'
        b'+asks1bP5w3s4VXJVCv6n1OiWpIZmGPH5T81fEAb1ehu7sZDfV9s858621fwxqr/Xfqn1z6cHzbtDUHt/xRy9WFfHRtx848fZmx6fW/Si5LPxn/aOiwuueXovuefn7Eh'
        b'eWvYgY+urDulk+4Z+Nfjb/+nEqpsHw6+vKpzR59DH4ye3H/Owpiw2333X+hAmEt8+dOXdy3ZNMJ2bJUh/bmdX8d6B+6mnS477BmkOOyzg6fhqYcFfD06UNNQZsrLj4sn'
        b'CB3sitCLOILEASQmzZ9eGfVYqGwvzjEZSJAz0R2lewnhJCm6EHkt7o4eiHzCbZX2dIwYt1ZNeQgmbyfbCHZhsz+yDGNAfcaoeJZaBhp9o/sEEQTYLWYozdM46EElzZGZ'
        b'KbINGagHN1DeLQgroxNhLRUNj5j4DUZXCKl/ZSLal6nS+qcO4nHIf6yAmqlC+aaqpJ/kiHgcIl82KTwoVchQVLZK+tUgM//SsgY1FjsGfFVLdmh8+ZfbKnypcp8ZCD1V'
        b'0sX9llHEU9UfHF2ShSz1rdljYsEWUAMbOEqYSYPT4FwByTU/vR81ly5B8kfV/w9jFvNFvZLdQT9XJkAE+uHy94YcWElchohE1sKtWQAXBjcK4OFCilXRk8Fa2GLGIqIc'
        b'NKiI0xv3VgTcqsxOQpY+rItKwY58bPWTaCbYEoltZ1AfKZEngH0k2OL1RUKqv2W/gJpKSe/mDJ46myLbJHy4eIRY7LE/llalpRoKFGPLZ78e7x/8Mu+bGzMfXIEXkFRJ'
        b'nwDaqXSwF24jsPdfPIGKWv45blDmjvgivkETJk6hNEWeNDW72hCcLkkgL7OiJlOnR/5GUbGqzC+nhvApM2IV9NVFz3KUrNq4c45wJO9vm/QO/WtpsYjyXVsWPHfYUPJy'
        b'ITuLPpGiQAO8tmTnmO2jyMsvQvrS78Xjqc/qqp0jEyLIy98mmKhf4z5FsFYv25n4gpy8PB+YTb9RkCmgfNWRl0ct4Gs/MruVtqycJ6RU1UU5qpDh5OW1eQuoz3MNNAJp'
        b'ZXDaVQt5+fenh9Ady3ZxVHl1VfCwAVn8S69BlManDqkj1Zbgop3zyMutfun0keBZApS9ZOfENB6kiOGBdPHQRaiZqkUnhwn52q/lvEHfVE4XUSq1jyV0uB0BE56nquf3'
        b'ZRFqyk8pkvmXTfOrqGrp/6L+VC37Jjqff7na/D4118fAopchZ0XF/Ev9VC+qLhHhx2yVtGKWHd0/W1RBaSRYy/gwPyDqwFTd8PXTGOMR1EHtph+z59xofnuq71eVtg9u'
        b'/RQtWvHd9wmLXxw6RBYWJvvbh9S0eaPWHt2Wk/dMctymaftTlc3iTf+eYvEeNLUlaPDgPyz66993f/HPipd2Z8f++o/XJPmpA8yXU69XLn9bEeHp8ZPip01//uv5zDdi'
        b'FzYuXvhrecD5eQsLB9co7o36JOGzhKLRTcN3vuSzXrO3fZpsQO2Okf1ejpw1frNshHdK892Atza/8/YrL90e/qpwntLb5hF0d/znN6IWrD0873zepwtqnl9z0yC5tyE/'
        b'Kskw5Rz75ZK/NhY+v3JO1qvrqs/8ffAnOc+svPRL3d4/Ksau/3NCQpTn9MvHUgK/+uQ99R0fwxtDvYTvrhjxyda4P2n/M/hIzfPfha+I+eHKX/T3U76ba/K5cLAyd7/f'
        b'uxWHsz8Q1u4J73hBsfW9D+P/+WH0Pz+arPyW8vmubuyqr8L2f5t+4PvRGfteuNAu/TmjMnFy/Q+j7zyzZd+f/jn3rcrMP159t2zad+pvEiMt4F97/3T7+D7LU3lj1c1B'
        b'Z1bMOGA4IPz7hIubT9z7e1DC0KJFmacWx8ccb/pNe33HL/MPfj1t8LWVf/hPTVl75tMNlv/52Ud5o2XL54vlYt4ddw5shkcc7jpwKYX31lWALcQd9xSo00fCuhiKYooR'
        b'K22jZyvBeuJBjMYx2ZEpilRFBGgZpRRQUiEDb40FdUSO6USRWFANhFvs00tYTrGwmXwcDLfPQOwjIxmc5sC6JZSwlBkCbsL1PEDXJ4+JjJanRNo3i/WB1UNXs2Xw6nA+'
        b'zOk2uLHc6dgsB/VOzyaoAVvJ5Ndk0KzrHskHGuAusj+VtPBJg1B8/y/hHo+UvHbhSSTvQlfJmyrFcTfevhKOdt3QD/8fiP4Ho19/OgwJwv60kHyRYIWT9acDibwWkh1S'
        b'xGQlqjfKgR2IK0MfLL0dUYN4GZhNZDcSbQJi+bmI7f/CGlrWUIPvyXqz9U5pvw4jWw9pfyPCVdrjwGDQDM7mEXHvAToeqbsKcBgWUv5uVswy4y2dYE3pggfNbado8EzS'
        b'RbOAmoQF4xFwYSyZZUEyqTGvW6Z1yV354BV0McHLyysE1JwlQmhNhu1k52dwPDvlgRPpeFpPSM2EDSMqhNlgfxiZ24JXwXnUlkZ+RgfWc0Y8o9PlEI0BFwXwdEwGmcSO'
        b'gjfgka45dxK87jscVVLLDoRWeIHw6LU+zPA/0fhOFZXqmcMz7vQswdxprC/WU9JuPe3HvwwrEel/YoOxRlM6dXgSpdN4v8UYb6MvFw8cVjRP8Aax0g1fr7p9rGX00hWi'
        b'58zjmNNJ22a/vfZkRNMzU1u/WlgdcvaF5Ni+MObnX366O2rP7ck1L1Yv/1Q+7Ej40b2SiJOHdr8wum28ovhu7oEVP71Bn3vm8l++/bzu3HPHy5q2m6/82zj89F2zdcpn'
        b'oPnreyD347AF1bca4r/4PNpQ/7x3xO5+HeMnhVhGWjLvbH13YsEnfxjDLXy235yvfoO5oy42pUf88p7GwO7ZG3nvtT8GRmjOCp9a9d60u6tp0/3Jq6Z9Kvcg4XhqeKgf'
        b'3hedsJVCeKzbvuj9FpNgnXykHB0ikzkXB/DzOY65HLghjNiPLNwO1/H7e4G6wGX0NFCjJdPxyxbOxgMH2vQk2JnMasBT/NRF1FypHSvh7iq7qxy2pOFIgv1cGRrzPfys'
        b'/dY+ma7Yi7ifvwpsj2DBCTSgtwiEAnjchNPwSAG3gsMYMbzBWXZm7CTCmOG+AAo0xiiUCgT+8YFpciHl05/Nm11MorPnytJBYwZS46aDW1irc+7h2A9s4sBhcBLUOMzh'
        b'oP8643sy3uhgVoQ3Rrvyxlk4QjH8KV8aT5BIyeQJg9fTM4EMv+EM5oiGWpRD6crXeMZDeE4XRwv4f9GsBzA9DGFID6Z3b5wr0yMyceN8uCnSr9Jh5TCUTzxbCLeDbT3i'
        b'XfCPUUp3Bf5p6FxWw+RyGjZXoOFyhehPhP7ERVSuB/ov2cpu5TSCjTTZKA3HFHEaoUZEVnF6aqUascZjPdLyNJ4bmVwv9Cwlz17k2Rs9e5NnH/Lsg559ybMfefZFJZKJ'
        b'F1Smv6bPenGun7M22llbgKYvqc0ffRPjX03gRrwfJt4mNkgTTL716eVbiCaUfAuwP/fT9Ec19LU/DdAMRE+BGrLtiHyQzTuNl3Ppar26SGv4SMR0m77Bzk33NDISEuaW'
        b'6FE5dEbsxSQTOppKvXqpDs+aVMrUGg12dRq0S8uWaV08p+6Fo0wokXM2xOEWdXpcSY5o2exSrdqolenLTHhOR20iic1GfAKHm5PUiJPItHrsQiUzFfa9CqLts0/qApNu'
        b'mdqECy4v05PJKC2uUV9a6e47zTbyk1pqPM3j4gEmM0HL1ZXk7TKtQVeoQ29xI014GgWVqVUXFD9gisneC/Zao0lnmgxqvRHPrWhkGrVJjYEs1S3VmfgORc188HxSsa6g'
        b'uPuUmlmvQ4UjSHQard6kK6y09xRSf9wKuj+g2GQqNybExKjLddFLysr0OmO0Rhtj98jfH+74XIgGM19dUNIzTXRBkU6J97UpRxizvMyg6d1FRnajZYgHFi9xFjzGEmeW'
        b'7EbL3a/t6U/X60w6dalupRaNZQ9E1BtNan1B93lH/GP36Tsg5d366EFXpEf9Nm12svNTTx/+IzZjFir5Iy/2wPVYGDaawcFuS+e6L5vzY8lGFVXIDDmAxSfcCw/xug8+'
        b'rSAqOhq24G3e48EO4aqs+XKaX7l2FR4FZ/Ce+BkKvDhrI6hNyqApf7CXRfL7pJfONuFN2jgbpfzzgq/xytTwj++ha1TgPVWSupQs2o6eF65OUTMXQoJil8fGaBY+c761'
        b'bcu1GnnjpZprNSMbFbXXdpysGbZ/kn0h97pFfn5g35F8ZDRheT4InMfx/64z31icx4LtvETnRhBZPXcCPC8Qd0lrp6SGl+BB4tGbOxwe90TNldvVkTAVQ/UFVk4Mry8j'
        b'6oalMCcSNieN5pDicQN0JNH60eOJDTUhbDzqgBjYivuAJlsvgrV9YR3v/66BnfAUbExViMg+/ZVIJzkYQNSU0Xnz8M6sp0RJo0eNYSnRShruhm1xRHMA7TOQuozAHaCD'
        b'delpQqRsnKbhtfAlDiH6GOEDOH6eCOxAV4G9hpouJZvhYINkZZA7sjpXXitdVw8YGtzldO9RwgyfzH3h91XG4casdv6+4rpJ7QMh6H0FJ3HWUUt4fzWtJCH8jgk3pCzp'
        b'nD3Q1Q16dHkRgUEWcvaozrHU837IA+fxUCWspqzgkQAV8gCJ8+wm20PgecUBz/0Al5k8x4Rg9OO2XZyHWahOY3xIVa85q4rCVTk0uV6mDQtKdYg5K4yIR8sfGwTPPO2K'
        b'cp2B8P6HQPGGE4qhGIquPFi8dO/yrsodLDvIybLtG3RbBS4s++HzGsXdV7r2nNdAzBLX4AvPpoNr8EIW3MjhoF4KtIDrcDfvft4P2rPAKZoCDUOoKqoKHgJXiUMY7gMn'
        b'QAdsTEbqexg+hCKOQyygkUkBtR46KiuTM+KdUKKKXxnQ+LJXdayUW76v/AgderhWfOTtD29++NGovcqRlV8XXyx4+chHH73mXftW7EsHjrx5/vjagt0R+3/+y5gT8MR3'
        b'Ldsu/yvhjZM/KhpuHXt2wVt/+HHajr3h34h840Jkb06SS8i2l/B8FVzXkxESLoha0VIGD0ArP3dxAJyCt7H/OBncgBv5CQ54gwH1xfMJQxPAE3AnnvsAu+K7NuVfI+Rj'
        b'nW8HJfMOoRHgjoDilDToGArb+M3801jHnEgxbfc0iZGVhBVnuFcG2wl8mJ9pVto5mgrc4hleE7DCK6mwOQZ15yaGo7h4GtycDpr4AOyzcANswLtogHWgs2snDXhjBO+p'
        b'2pSUy29+C7dqHPvfloELcCO/WnY97MBjlATOJCHevY4XV1hMnWLhBgk44bao9LG29RbnafUFhspyU/f1o/h3vpREh0lIfDXZRL0Hl7PndmOzj7Vvrn0L9S42i/fmf6sX'
        b'Nnvu4WzWDsD/A+1oRrFaX6TlY7Ec+oyD4rvpSkjleVw1CcfkPIZ21PtWvpzSfryXDonc4y7qSwYtmWfXXhDxn9P1f0vEkfC1uh2veL0SGVgtC+DeCFnx2+6ns2riPZ+F'
        b'obIFLxz8ZaGeXtY+Nq9z6u3vvz8//eePIyLiuAU/jvjbyLiRuYDNT3xmfUi/T/N/+Oby9KZFH36tWTWoQzVu8omxAQfkSrkHIblCpDkdBJtjujQMWg/PggNEeQHVYAc5'
        b'2QCvgAftUeEL82nKG25ktX7Aym9WczUNL5Ik+M3jdhg8bEdvzxjiPh45ORY0GbE3AjbQFBdDgwvTltk5x2R4LBXuABfJlt6pGWBjTJe+FwsPCscLFxP6RkDuANucyowO'
        b'7KBTYYMXT4LbVmECRLWD1uldehC44M+HwW5AeuUR0jywE95wKjzgsIPEa8H5Aid/oODxwTyDgOf8n5w6fQoIzuU5EKT7Agj8Wywh+2AF0CsHdqONbpn/G7rQDnT5oBci'
        b'PeJGpI8ARM7ahMVlRpNOY/NAJGHSY9lvE/I6QO+rAwkhc86VgQLnykDBA1cGOqIq8c5aPehqmkaDTRxMfC7qA28SOsX3AymYB56n3yR0nzzTwQfy1fqSnlTsJHx7W/mc'
        b's/lHlDk81axHBqUieWYvQU4uAVOOnNh8xtncAqTkvcFr0JrMBr0xQaaaazBrVTjOid9nRRMlU81Slxr5d+pSHDZZifQZrFTpTU/MiFil7i5kOCNeufVsUeuXv/ykWvzM'
        b'G8++9+zbz55vvba9raatZnxj567OA8e3d24Y2XhyQ1vL4J2DWwfXDV43WPDSx2ksFe/lqf9MJmd5TrEWHqtyYRSYTexNw5yiD6zmSdgaMgozATk44+QD4+Alskg8Apwd'
        b'lJqWDOoz0mFDWjRojlEoEe85pmAoOWgSgDMFcN2T06K3WqPJ0+brCoxEW3U9scDxW4kJceWAbtjvns9OhUKeqHbiCz75wrDbnR5dweNckumcaQk94hP1vuyFHne40ePD'
        b'IfqvUhwSnR891RvFZRJPFSI6PY9lOFbPhfRcfFT//yM+nC05K0PGe5dMvDOKWAuFOr26VKbRlmp7Bhg+HtnNf/sllpDd+ouaL1U/vv8kZPcqRcX7eJZPn4LIDsuuRaAN'
        b'HACNdLAb4SGq65fAK7fXwYlKp+gFx3Ix1YHDsNlEppougc6VkSlYE48Bu2WpYKML/SHamwKaRf5KUP/kpOfHuzm7U5/LOmL7ZgOE/ropY9E9Mv93SRAf+3O/FxKscyPB'
        b'RwL1Xzi+xqG65vdCfAQTCZXozUvzEcEh5HPxGnf5YgvMBgOSAKWVLib278HLQ+vC+HOLLphe+VK1EC9iJfg40hUfPf7aUxDc+6fHS6F77IIA7l+NTB5XQaCEewlKTgUX'
        b'7PYY0sP2dOmD4NZ4jJT74E4TdgOCLaCpEptjyJR0Ewh4xccUcE1UBHfJYkq7HVrXKxIWlJn1JpcRM/aOhH7i3pCwR2alIzBT92Cso100r4O4oxFuGEPd0aya+tn7YYjW'
        b'o+L/EqKtR4imfyCidYVgPzaS2dcn6PSyZfHRoyN6YcaPRjpF5w80QboTf1xjR7ryhp5o1x3pRNS9bzxeNv9kZ4OrRoBToHHxrO5cUArPEN1j3hi4GTTmjXMxQUADvGnC'
        b'q/SR5X5uGn/uKkY3cB7ZGa4oNw5YhTh5yWNgnC/uw0cjXAi/tV+3ce+e90nx7RC6+PWKb9+54duj6pUHdd8XQZSXpykryMuzcXlmQ6nNC1/zHBMhNk/nAjedxtCEM7Xg'
        b'Cz460LCFsrtjbeJyQ1m51mCqtIkd/k0yHWoT2T2JNkmXb464FojpQvQlwrEJPZFG8v3yO7bOdXENbkCXw4w9JF7syTE4xtX5y/T3Zkj0TI8r4+/Z36u/T38fbzG/TeZZ'
        b'uGVaVwAGvJSO7FhkBzNUOFgrAHfA1jXwrL/blAmm5qkOvHCfoeWdhrY+9oVj9oEi++bflyWuwFv9Ys9lAV4VZtDzK7GcCpgSyTz3gTMcdja6m2f0FLqEsM4NKziabBIK'
        b'9y4Ee7u27oIdsH5uLt8wR6REikQEWmANqCPx2CK4FtS6BGTz0djgHPf4AdknS93YW287R1Lu50537Tz+JHtB4MJ7+l+lSjnLR/4me1JYJfIVrloTPLt1GglmjU4Q4ROl'
        b'Y80zKend4ECf4VQp3uihaNREwb3ga0X/Sewnv1YyO6990ImS6znrwncrXxg3esHGqH0ZZyYc1U9Zfj3hWPbMxF8W/NjvP6Gvjg1dWRmpniMWlQT8ccAPDJwkHR0w7urI'
        b'2tEvVi1LHzdsTXifCeHZK6Zc5vL8j5afG5Sf9xfdRdGQ7CMq7biUklc9vk6eFOkVVJxjEFQP+cfMZZIvjMvKw4PuJrZ7hnhdX/MfZAqsmLeV4gMFzgWpYGM0PJtM4jqc'
        b'XuGrkaSlL4Wzsybx0UBSv/RUPvDn1xl9pp9m8b73qv4vJ9tjh/tHB40qp3NwNJAlVTGMInuD+BtBPWxMV0TjI8QdOxzCllQR3AROVnJ9YX0i2CYYRoH1wz1g2zBwhQ+7'
        b'XSpY7UuRaKNSblECX35gmKj/YoZEG6Wlj1vA76b9reKrAkIk//s1XWnRyQ9+TBmt6MVtXfKwjTe82JHSGfKX/7cicFy/BcMnaATme97yr4cr20rVZaEh79atODI1Ivu9'
        b'1+Lz86+8UDTq3uyBP/bxFESEhP6zeO7L87bMqjUlr6j94bvhi/pVvX9tM/dX/4h+QXrTpfc+2HdsyufVL9PfHP3569B0i/oP394oGl1RtmdBUF59zb6RP9f/69/sqdPD'
        b'O2IWyjmiVwvyh6XC9UPcTj0rQ4bted6vtQm2g03OSCNHmNE0sMEeaQSvgku8R/wmPL0mEtwOUuDTsXFHCihPeJ2BV/oOJJJrBjwBj0TChojxOdi1hVe7jgf1Y3qGzv/e'
        b'fcFcN+4wGNVuzuWw7oIrkiMxhjjmRsz40jJGTAfgM9jOOLkya+PwtL2LuPo/bFh21smvcAVhvcq2D1x3/uJnho94x0RGKEFTlzYAroLNVD+wjwOnsrzc+I1TKZnYK78p'
        b'9Pg9Jwb2PtcjcfCazUl2XhMvfdow7VwI4TXnc4WY18ioee8G3A2e4nWC5zVDfB+D1yQsGvBWxKH8f0fdT1/j9Y9+XlU3szvC188Yk/KZsnLaRwOFoZL+7+dMz/1k8o3h'
        b'ezOnzK0fsDXi5qCnp8ckZ65416ezbJKP7Ul5jWe7iA//TmKophUYflXaiyOlVClWT78p7kN9mqTELyf+NJNMvpHE1CKO2msgSyNKx8yR8C9r/UXUt3NDMROQSiKyKH4n'
        b'372gHQf3OjkYPA3PEC4WAG/qqgedEBjx3J5iTqbiD51eMFbKPXN88fm9fusv3n0p0rd80+vZkhv+jOVyx1gvwdXBz945/hd62lf/c/iV9yZMHDPuwArjqsrFB02/RG3Y'
        b'vmFn1owizVtLs3/sKPt12YSo3f8Inp8TqJ20dNB3698t+fHaH2d+2PkbPUY5YOe3++U0v2NDA9wCz6diAYkpPwXWixcx2qX5bnrZk4UXd6dBjfYhNDgJT6AHkH35AggV'
        b'SglNGs510SBPOL97xz1XwsOlxvdKeK/270F4h8B2eIsnveR0nvL6llP9VBxog9tgo9vqRfxHNhMuRuRYJ+CP57DQBylMcG1MFUPuWQ2H7tlWekW4icZpZlKt9KLQhUwV'
        b'V4WP8RDUUSYGny6DFEtvi+AgqxG00VWC+ZR+ID5Ao0RiKOdPayPf8EluAv7ADP2rFnxK2FRSBs5/3cIaWlEqQRs+s+0suhOSU3BwXcIqUR1tEeHjPjSijSiHRTiRqtiN'
        b'atlA8gtq8IlcrOENfOIMaodghR5BKyAHjOD84h75xSi/DeWfRfLzZ6RNdeYOd+bu/6DcrTQ+bKROyOdA7ygLPuEmar79qBP7KWj5FkrjEYIZFj8hLVEi/qzVls8yYH43'
        b'977AbCpUjHMe5oVwGJ+GST4asHFEzq6SiwwqjJseWr15qdaAz8CZgp+F+GALjdYmzdbr8A3RU/m8E3i069p5tqtYctBICr7g3ZcMeJMgG73kSTeok+JDp4yj+CXESax9'
        b'U2p8FAcOBMVHJ/EHMPmTY3E4snAt2OVOav8vJjtqiGn75kMlWakIbZMV8RHRcnhYh2i9KVVEyQZysBNsATfcYhOce/hjrmChjGINnUXhk/NI/zM1dm1eSfrQEOckT9pG'
        b'Gx90xC5pVZ6pLK+0TF+kY+37QVIstkp4e2MP2Ak3R4OTPJzISoX1ZHtRooNRw0GtoDKvxO2sM2eI1mgCp4YuoQ1SbGtoWAs+n47WcAcpfPYZgloQSLXRFjqIwgIPvyFt'
        b'ENrbQMIomGEryJq2ewzfGMHKQl1pqZyx0XobXfyghuH24HaRBpbjhkns48WRo674jRyPeFqiwHFsjKPWgBbStgzSUCE1fKCgElqphyxspntd2PwEh0fTrkW6rD3tWsOn'
        b'LyinqhOfoalylXD9IJp/6eP9HDU3sQ9ZV/X1LPvCvkJvIbVwen8SSh8et5LSnX7/ZcqIt/kc/MF/vlQtInvEXQJnak7WXNr1p9rB77Rvb9vQVjN4z62k4zVmusBrhuST'
        b'6ceU70y/7tMWukGQ5hnSUCs7NCBqwKtjpK81ydP8p/ofGtI/7BXxqBG1C6Th16vH12oHF8SyRULq6rbQFpsAaaokDOwI6ITHIiUVjpXQuxmF/2riNYF7Jgc7zyDlTyC9'
        b'AXfBfbMhP/uLlNMzSKfFOwzVp8GWKBqlOcUs8kc273otH2Z+0CMDnOrjnULC9uqRfrqaGQLWwvonX03tt7RMM34sf7ZPnkZXpOs1vgH/UmKaP/ZMTPenDc846er/tGIa'
        b'F1PZq5yrd1s1jReQgEawF6n4jXBjBurbFnBkNNlMHB+0ho/qtvfVOHBcuBpWw6bemQaeiOJZBRZ5bfzJTYzSJlAbC3Q6BNtFyimK7b3p0luiYu2KUl1hZQ1rP2aQYsnx'
        b'IRw8Di6Q6XiyCRg4xSFzopaBuzPh9QRZ75DgfPg0KyIGA/DxbxieKjt0xHHIKA3P8nBMdoHqIXsAepj1dgjrupgYVlP4/e/aQyfjQ9hd4AyazpGtF/cthm2P3WHFLoA9'
        b'tLs88uNH86cVtrh0GMYtj2FgT+qouGS7JQeOwdsCymcwOwGuC/p/2F0IPl6Ybu3WXSSC4Qw4vwQDyeucYHemgPKGZ9mR2XCXW8Ca8+hNLAs1NOLsSI9aMcRCGSJMmPOz'
        b'NQzSJ6gqlj+hz8IgPs9USPCpeOXxFhqflWc/Hc8WFjtyVNzoMfFjx42fNn3GzMRZTyUlp6SmpSszZs/JzJqbPW9+zoJcXg5gzs3rCTRSCXTLECHLOZuQn7WwCQqK1Qaj'
        b'TYj354iL56W/R/fWx8Xzo7OHdRwSRCSekGxrRZYsL4LXnkodFe84ZxzWVqJhCmITQPug3odJakcXDW0XxGhQXnTyCtrw8gMQJS6eH4ij3RCFHQ0vYQD4MYD75+AxOMLG'
        b'wv2wgR+l43DbU5FK7DdrScVHboH/r70vAY+izBatrdd0OgshJCGEsAQSsoBsIvsaCYGAgkFBbZJUB0JWqjskYAdk0e4mLMouIiYugLLIroiKU6WOs1yX0ZmL7eio44aj'
        b'4zaO3jij75zzV3U6EBicN+++ee+76S9V9Vf9+3L+c85/FiDj9ydoR4rU4GU4+EIHDv5PYGh17kbIhPJFJNVydOUixn3IJYvBMdpW9em54nz1YFfmTPzx+dphoKhQf9s9'
        b'n5s/bGBF8/rPOA8ewTz5lwV/WnAjOwC6s9eD3uaja6664+iOq+4o2I2i0CI3P8f0p2Kbbq5g9PxB2bkFY7tAw5sHWjjbEAHQ/Q3a7SQftHwcYCfNOdBn8HFhjrZuBoDG'
        b'LgNFoAfuUJ80tolLIA0VnlqXt6La7fGWVNd1zkpH7/Bm5aXwwIohK6Xo6AinI8v8ZaMESveoaGwzt3f4nYtkmjP05B5tv3q07CZqD2En1LsF2vpcjuunmFbeoO7Pv4wf'
        b'HFEXa4vgZfr5CD84l5cm7YCpENpx0eDHFZGBtaVl2lOFsGlv1NZLsOFvU+9NEewD1acIL2kcm8jlDP0j4iWpb5bEceQsTj2ttqpPDxmsHh08iOvN5aELMl69N/N6NrP3'
        b'a0fs8PHUYPWk1JuDoTtiUXfw6qlG7WkmorqzXltFBhK0Y848SL5WO0mFvZqWzA3KnC5xCxakPtBrPsOMJpVncbNu3oovBY9vJkfT0aaeGqceh75bpB4YxY3yqDso7r7Z'
        b'Ni52RIUZ4k7/fpDCMvjWKnHWoXWIb1X9vl8lDCmzK3dEO9hbXaOtLSxQD+aYOSmVV49pq6opjStmAnf7guclQNzif56oK69n1Y1DOzsSN2iB4rFNYy/PJVs4R2q8CbmS'
        b'3NU9uYqqr20mz5vw5bFf+6fc9bNpz4133PmjvPe+4cUzbzvX9eW0JuEPavPqn6eXtvo/mfLizQcn/rXlu5Ep1s/uHfl8fUZf6Qfff026eU/356OfUpZMH33rE7+eNW/R'
        b'wLQXsrvd8ZXl8yM7WrNTKl55ou66LVen/fjNPSfnLXovOPippfdMPf3Rl69mvVZ3fvcvBvn73FA5ctZ/DDwZ++7Jo4O/ueHPwcbg077XGotu1Gb5QtueiLnH8+Krv7hx'
        b'/rasxkeWf1Uwf/QNp3/z0rRPzvfa9NakHZUHcvdXHZ1UlJj7zdERVTnbPlv4n999vULrYX7m+bYdf/275aHPJz5lTsoyM2Rxg1ndEWZtzLgOORszJtMqbzQXq0djL0AX'
        b'78teyMQM7l000lAfhxn3KCJCQm6sdhcTsDvu1VaT1C/J9GrbtZNM6rd4IjFBrcXWSP0HgdP23EAKEOr6ISRBqO3opR7BUZU47ekFwmJ+3DyAHVfsguVfwRuNroNdzO0C'
        b'iDRi+KCrCBaNvhgWjZJ4xiGVeKfoAPTUAfBD4nvzAmlix5OnXoeuwa28EoZazDxKyF5eq5S5XeRlth14/TM+IgXlVY6LNKSCZZ24BKR7qQMLFQnhGpu6d2h69tScASTM'
        b'jeDu8UFDBklcX15St2k7EurjcFz3zJo624MuEnpxvdS16tYyQ/mwg1wSHv8FeHQqHARqDB3BBpDsNPkkJcdngn8J9mlTEpcAsbpBHJ/QwpPwr74tBkRZNNKtEZmLeIgl'
        b'KqUBqQXe+8RWAXJmCKFU1IH2DfsKw72I/HwnMMrWB5l1I3+zupfvtRd5+SZcpfOtiVx8v2FgCGZueXppVS3QLUxcqDO35AxBEkOm+ro6t6LgfhCSiHA2hySvu9ELqAdm'
        b'4alY7g7ZPG6UYvKi3+2GCtm7SHkN44uy+2K/41DB3+Lz6+Gp6oisy6uisWsSawRnIcxHAY2NMjPTdw7SthRq67TgTEa9NA+cXc526Z7aHkk7oZ0d2gHHDPcoDivimIQL'
        b'c4ALJxHHTmjFdzCE0MfoplbEPiZ+nqCUwtAKsgQxRJ/YIraSd+cmEYeQcpgHb02Ug4jD6xNnc7KJtj5zUVvm6JvHNVZX5WWPI1yxombhmPm9+9+SOf9WuGZn4XPegHE3'
        b'jxtLuPd5rCyxsHQeF1CDiIyHzB53iVK2KGRaqNTW14VMyEGCW1VtAwwLERFSSIRyQpY6FPxSakIm6EZIYDWKvRwiH4v2XiG1y4j8B9GQMxIlwz4DmXFlUEJingKG3xJD'
        b'ZlTVx9CuztDeanAmQ3TJuq2Fg9qrO9TTEVa3Ohxn7qShAAReSOAQpWekiNKICjNKX7y28K2Ab/oEGVB+H+dCVRpBGYtX+jLZJ8BboTHFhyzP+CYicCA/sRsMC88tmTaX'
        b'pagLp9jMUtSk+HhlM31bf+E3HWWVikK8vU1IT6fRgM6jmfoHWgDekooqPDJyV7mrYQzcS91Vl1l1IUed4vaiEid28eftPcvmNZ5LmUn9AU+nEhi/TN2gHtbWZmdOy80i'
        b'OlNdP1Zbx7qZB6D1gClTfVTd07kG9Xdc5Pk8gCJunuiWyP8th/5tt4qLzYst86zwDn3e4juL27LYJluMEKB7FgBjqD9tnWeXe+vYfpTsWGubFyX30cPRshPCDt01i+S3'
        b'lpvkGDkW0kR3eBcnx8M7Z/iNJHeRE+BNTIdYXeVEeBdLetPcvDi5r18s50kz2jYvXs6gUJrcE0Jd5H6Qxgw1SJd7QTiBHMF0JRqwfyhqCoyKu8Y7ESi38LwzGIqzDaDa'
        b'zrInd+2cLBnPNPpASvJNNPLnf4S/Nn4kIOATuHYPlNPCQxyxily0Kl2oFOepKylzS5JBjAnLUyOqlXdhxItoQaon7qVIqMMMNRgHfBFU4AuCqt6ShZ3rj4VsdVUlFTUu'
        b'iGCNqEDXyAqEY3QoWTBKjueY2lqt01iF4dJDJhfCfVoJl9Bfw5USEy5ZXB4bWTIm7jAs4UIdNCy4zMMuJ6GAry/f6VRYQnszO9AxYRZyXXjEEcw33kjsbl73pT4VD22Y'
        b'73SfKAuVgjJcRlaDMJpbkgRvpEqzJ0k2+US8A6jn8UAG3lhYqkTOiDsX8m+BvFoZO8Va1MYPDPED2oS8gdACsq6Ni1T5HAeJv63NdNuApgwP7q6euqoKb8gOBKPi9aBd'
        b'YtppDQ0Kcg0xnRLVXYrmdAGMgc3XTV4nkiRDZJzgipV8YqUAbFme3GEWRqYpCtsCFSN7Ls2Yg9RzXnZMILRQj7UKxqwQlb9hLUyeesASEEGokQ0BMKx8yB6e6Zc4QlB+'
        b'gEtfSacKsdodZw3m+E9WcG17BZW/Y2UsmFkJoDARNVR+5C6JNOHSyOxQtS4XVg1yuwjUhHklAZhMAQkxjQDN78UwTTYIVFfeqGsrz8M3nQuHpxM1nuqSOqghzxvVNjO3'
        b'IvpaCFncrA5XptoMuyGXI+kKqdgG5FAtj49sB8u+804exJohhJshhJshRDYDuxwaIoQbQvXv2IwKtNjkNTof7SIpIn+lKtoSxBzcsR3xF7SD5d9hOML8JqR9AlDPgAjt'
        b'GGBABCUdcRCZ0OomaAsigbiGvYI+mUSfAX9FWNPjGUYgKW1YowXheRXlcgEaVeF1V7tcBsSawv1jG5aKGRo1QjLOlgjFQkRrebcOi7U9887H6NbIqZZ3ubaxUaoZEB7R'
        b'fH1EYf+jERX1EZWMuGGcSDHxOn5qjK2JdcNcvLSPMvSFJ9wXYntfEAi/sqG2QGbjJH0bNHrFKdhJC79jz4SLuowXY4PxPsfgpHa2c1pdrtLa2iqXqyBi40zoWBiLoKPn'
        b'7RaUDSIDOQdErQZghfi4csRvecRgd8PuskPYyOsM0Xzolve5MHa4DIBxRY03FINYuOwuqyoxVMRDVm8tOy829oP3qb7Y1ylcZ9xgs+JGt2Ez2mGW44I1wiLkX1R5mkjp'
        b'4crLNFlkYYNElA/P5BoMBEkqu2poDarYMc9jIZu7sayq3lOx1B2Kxj3MBRQk2dX/GquWDg2r8Yzp3ZuOY2F9oKGfkAV2oCrYFoymxWKr4vDybmdNU5zw6TrJOGsgjkTH'
        b'jQLrFF77mDhMbfwOLhVAZTQuxu2ChCRuZc2irUOCOQ90eSsegvPJ3M1Ck6nJ7DP5hEqzItP6MCWjqzLBM4c9L+TxPlr/AjDCjEB8idNnZu+XOOdyjTmwqiQUzoDS0iBP'
        b'S5MVSjf7LFCixWfFzvVZunEQ20e0iqXJ5rMpz/h4zxEfCnfYIIY4mquRfDbEUjy/9AmeX8rQCogLqSsM7gE76MbF2WbqgyhWli3kgDUBJGNFlQzDHbJ4a11yRZmXZBxo'
        b'P4AdxQvzqjRkw4i4gDyEWjJK5yuOeDi019jLams8TGEvxMt4NgKZhvgy5Uv8KpTJzDjUNCPxJTbSRCi0GAcvkwZPItN/CbqhPzSGlSAwYog575TI6kbHzVZvBKGGiArb'
        b'IMs5WUJ+fhafn5V4oRwxtWaf0Rrl03DjvuYYSY2UMsMMEP+gnZ66hvYZgssEhhQrXqJ5fQJSQyJ87F05Ry/S+d6n1Af6erOKVslhsgoOk1NyOmKlWCnBnGCOtyTYrRK8'
        b'MdEpqXpKW6/t9aD34Q0ztA3ZS6blFJlS5nDJ46X88l5zsniyR6M+ou5aoWtHoWqURu5rMX6WRztr5gbL5jnF2tks/ZDuHqDVzxSG8+S5qBXC1SO0A1rrDR0EAxFUkOCT'
        b'MwwefLwOzZhhi+qSSreBlAjtMjSdnALrI1rfDmSZZYgD87Qznoiq2NU9Aq9ozeoacwdS1wBbnjlcBKkbS55BUSAdCFsgISUgUnlmEGyeiekXlos6UWtGs2AQxyI75Gi4'
        b'W2WnHLMWzYqxFRUXckyur65eptf0YuSYNhYU32AUC2y3fAQ5ybeTk4ylAFeR2AuSbBCYymecvpUqf+Z0qgB2RlxSRGmyOfs6dZgL0fSaMNJEy87M3l1IDyF/q6kdQzLz'
        b'afC/vGtka36qyRilN3/JHdMGWAmryJrwaPLLEzsUF47SOVKmH3kSykFcM77I4GdSifmdTiKGbSEEc7nujCg66YKWhiN1XvhYGkKZB6rPgcJmhB0ClFf6BqgTkPbGasEA'
        b'C8jiUwbjAHaorhgBfWGEaACxxwgx6oAIXpoDR7Am2I7tWInd5iRmW2dNuiJ0ZyEeHktGOZcYQIvLVeWucbk2R/RhwgUFUoTOOQXYDC+3kIkQLGSQQML95NIYFn51ubZF'
        b'lHfR7KQY/6B1SGDkX6ZlBLR3XqYUhshhle0XbhzkSbkvjmFGeCPoh5fM8G5g+wcD2gsiLTcG1CrazVbRIcbaANCLjMN3UDurPuPJQjitHvIS1FPXygzwpamnJW1HsfpI'
        b'52APzYMZYG+ruFhcLM0zuZnoGPLvJLe02AK4mh7y8+U8gUTrPCvjuAEYZGDRRpwzO0Ekayh+Zulid5mXbOHp3fQT2EML2Y6MW+s/Yg49EMEc6nZxoVfOI1p75TyifZ3w'
        b'iC4HhhZdERii+XEgYpKlddKcSwEhq1F0FVyWxXo5nezSyU8JCNBKuzKISQITOBJ9dPaAFYSvJvgq63LCfIuZyL15EMPSTvJhPu2NijDwFEHIWYlko0keshcAYdDIJGK/'
        b'NBZByDmBEMV6ry4rGyZ8fwp0O9zOlBIAy3PSP7KnLt1nOv0YdeHyzOIjETmG4aV1XK1X6AEZc9ptkN5WiSFgDpFON9SW6B7a8Znaup7a6mkz8lBArnn6jCUR+MlEdZ+l'
        b'T87wzhdpSsQiJUyETgUBO9GVWkPdjWYbMGkS2uycXltbWV8XPpI06XOlS3jd6ZtVAEZSH02A8mIYJJkYyi55l9W5lY34aAsz3y6xlZqrqMyn2ulFoKp6X6Z2eSxBJ5p7'
        b'A8P1uGil5MCn08ZKASB4NdxuvUndTF3M+lc94G1HbrWNtuqCnDztFErVapvyclHQeYld27WkocNxUpgBgtJjsH1zxNJIpbXEI6HUAiRaK0npKzkBJPe4gBmp2ABHzyaD'
        b'jdn290lksQSVisvqPd7a6orlbjm9CgjXdDpGV9Iz3V7F7UZTp7XtUzbr0mZWKfpItAFBVl9QK7liYU2tAmW0c0TR1xs5o0OTFSWyXMG83KUP0ImdzKwB6YzE7qipHFGF'
        b'jkWUoEs2DxmZUUrQNxZaXK3JNWyupOtIuqdjdrCW6aRRvHHGdFg0SH+HoiLKILbDT/XIeBUM+vOSIR1nZQa+6BSXVOpbtPXqCfWsWW3WjmgnAZBpRzntmLZ3Kon3TJXU'
        b'O9VmdRP7Jtbw2r3aievUQ8s6LDizseAWRCw4uf0EylJuorMv2zyRRJnM8IadfFlhb0TRJivshxbZimSCbJPtQAaYI068rPMstEtaaZY4Qw59PcwAckcpyu9g1CQ8Fx/i'
        b'ULapAuaYzO8Wm6QwY64v0AJ8Bco4cgt5OnhA6kFQ1oeZcWN9gv4FEM5kDigICVkAPtFTg08UlpIhd2Q9QDsYa09oTPUJk1FOwAQpTUYsYkR453IGk3axUA5fNvK8ATvM'
        b'yBvPw1VLzLueRPziyLW/Y+efIbuLeNIumF1sw0AkybBtQRF/pClTp7jLKxpdKDhJRGBIqPFcuf3N3+NkQTulnCCg+ImAUwaNYktkHDuWfIc6iG8QPtGikWgnagzgYOEi'
        b'pDmO4YDgtghTYaGEx/rIA+IBc20SGzf78BxoHeMB4ZG+ZwTxhSTi6KQ11gBYId4QOzCVLRuwq4sNHlELUJWw9fooDU4hGhIYUPMaGGrKowje2wFsb8U47Iv+ngASquas'
        b'EdibuVDiXM7HbGxEFYVMs/FUKCROqZFDUhFAjZCpuKSq3t05asbODJGDJQuV5kj6BNb3CBylkREguhOxVrI++XeUQiDzn7kd+7istgYAipfgkidSYIQZBYUsicsbRi4M'
        b'bpSEnD4CRYy/QkyoNgZQaL8SPe4lIVOtIrsV5F966qu8REdUt7OW/qEvKGfH6n1pMFc43qETVHaYToKAEroJ8JyKemj2JH5598s0ssOBYphHivVZiKtuLE2d4U0iYFkk'
        b'7kNaXXk4vYjZLraygbb7RNi3AXqiLAm+xXdz2VEJ7uBIzCAvFTrLDQNtdZVXoRxHDXWXwR0dg103Di/j+csjXJPge6wpTE5K+kkJmbC9YNnoBV20p9J0CnCRR+Uome3D'
        b'ViThWRXxPGBBtaJ0NnxjRwjw1UtPIjxN9QIU8gmJsBOv5knQAuBVK0+YLCwRWBAyMjNrYo03GAcPU2UTe4I30KOJBqxiR6eCy8UmV+INNZU1tQ017Ztpeu8MT+82820Z'
        b'HjxZNStdsLP+CxOZGfhShtIa4AwEVmxH7pXh/EWrIRTtqkGBJDRVDRkkY5cmRkypWP1cIpE3C7H88pSOXRuZtANYwv4lZprMRZ5e0oxBXAWxFoE9VXBNUmM/Jnek6+Uh'
        b'0ME0pDPoM/skgvI5AOUldmC1GPaAcshpj4Cw3jikNStTeX1qKBPCi5COa4AqR2vvgGtbIjhMVoN5rHRDKsDG2MXQlog12TmntwDi9zdFHELbReTnxlNfXQS39aLFIlgC'
        b'tk5J8QnhilMTCv4V/NchkMm5dtQ/sWt8TyDPnSRIOHqgr50PqR2dod01VVuPpqXSuknqGW3b2IuMieMf+cYOYyAxRHcbmAez7G9gHfjlQowDSQQd3yDJGmRKMqZKbMg6'
        b'vbasMr+iyl30ESvqnXFhvKODoAOOSYBocpxRngSvIPO09hjNLNA3Os5MRJ6k5AOK0mUizqSZuJQW1K5zWcMHfm1dyBWwXOvWbfIjEtlmyfDkobQejhcd8JsrPBiPFlbI'
        b'UlLqQZGCkJUk+uQKJWRB6fbaem/I5Kom5zzkUDxkcWEMQKEjJB1CEsZQZvOdERE4G65pn1gOQg7iCUEw88vjjG66mMOJUM1u9BJae2GincjeQ63BxqXLYgO45gAOIWye'
        b'y9UU65q4S3mAUDy3fIQP1hXAcFEZuxrTwXIiViDLh6+UlJu9FlnA3oZ3VlnPR+YQwqEuxE3ckligwCXW17MhNNfgYpiKzscRQCurra+SqaNLysgbALpVrvxo1z3498i4'
        b'OVk2oOygK6l7QqbqSuhc5Xo6SZs5m4jzkMmtKAB4ivGl4/r6Goyuf/FUud11OsgLWWCfoaxKL7mOQxKWPslkyN+SeqpAdhTsZFdGohFAjerl0eG+xzSdK7fkcIxvpPST'
        b'aT7CbOSNPlf6Qf9LRv/rqgO4KZqoKWxqmCo84QablGp41rlMnRC19TVYkTmmCFY4KuYsjwlXlMW4HB7FcEQ5zN7iFfelWeFobsgNgGyeqZ0dFBsxI+lj5x0zIKI0nJI6'
        b'91lg3Gc6PICOCatD80h5l2KvzDG6RrmhvWKd6Ae5XABvkal6iyksZ2AlfBqGLj6iknq0DtLI+I/n+6TUT+OXaPD9sHOYYCaix5FdJVKNQqayqlpA+qjbdMkVyeVuLOuE'
        b'LwygBVasHDlg9gtXNYuDHI8ZPKlqd7ZbUM9giUo5XhbiZfGV8GynQ6RhJp1atUpOuzPOgXxbCx2/aa3ammTtuLqtmKSOl6LyaIGJi14s2jn19g47gkW/e8q5CCYQiodL'
        b'QGuGGUEokTlPkmP9zIONCLSptdxMvFkb7AxxRJ1ayAcNHlPZYJfAmHbIA4+rIinT8qz4kJQ/a3J+B4gXxjMmc8im17EDOtVHGtAYNbhDrQLCYgn1qClskgWvmYX0fcHQ'
        b'5GqLmrUMCxqcvjTD0xYNAWb1CYMGL5GZzkLrn3UlC90hh8ftddUptXJ9GaD3DkztKp5y/eyCmUWhKPxGpmIBQkW5XLovb5eLiZO70FWKgaW1nyleZhCx7Nr2WR5PQraw'
        b'7qOx2IupxEuxl/UDlLa42VCL9OqSGrKkiUZiEAx42uczszpxIdqIrQrXf2kYIgjL46kaHT4XhSuD3D6bARQCEWOGaw2tifsExtNaLCi3BqQWBAskdw4EqtgiIQd4DZNS'
        b'p+cmEfB1sRuHAtH0Fnb6FjOT4iAsk1dWBwBXlE1rhE2xTRIQuRafYOxb13HXczcyCqUcce+fQX2+xpVpz8iYPWXWhPSvsalMaLERiH47IeUhoaFUnwYhM+z4dfVe6q2Q'
        b'Sa6vrvMQj4mkG+mQM2RqQMkDnWvJIBn1JyURyhdduSq2sgxPXEyGdDUpWpvJTAIinfG0VyXwy6Oo/1nFQrap7qqlbm9FWYmC7EimGIqDUGZwlWIiR6SOZ9RQK4pS8TQm'
        b'iImTlDX0t6ivJOpfegbaB7BzEb8EeK8JaEBTAodip2gbg4W7s7BVNjfZZEuTHUbSDOGou7jGH2C8o0hE9asmB+D5jmSuKdpnU1404vqiYTSR9bBbtjVF16RR2A7hJ+Uo'
        b'+GqUb8Xyl3g71sfn8AG2mcRVcso7mLfs6MYlc3XvQU5OnxPtesjRPmelBZ98TlYOPPf2OeDqxFMGHXJAnrLTZ8E8ZbHJBrVwslpQSviOMuGsTPyOgiuyxWfyRfvssP/b'
        b'FuM1arFDjttghvzsihdjIc/KZ2Zwreg8Kuudx5GYcx7H/CN/4hsvfTv7m3H5xNhoE8eMGUNDFxJdADf4OYw65NND/MSQZVJtvVIBYIcvQOHlGneDq5HdlmVFM3l+O4nf'
        b'VlXUuD0MHFWXKAsrajyhLhgoqffWEhhzlQKUqgxZ8WV5bQ3gskptfY3MTkNqcL5KZe6qqpB046xaT0iaPiV/Tki6iZ6Lptw4JyuGzXE60ZcoA4nUZkwe7zLAhaOwAq5F'
        b'7oqFiyBrVhs7RnBVQXXc+jPQsFCESXFDLULmUsYwsdXUV7soBRMTlvAZ3robvfT6H3JOopjwJ0l2B0w6HcHpjjsddFYTS2ofzDEnMzdo122UkM0SIZX4cmZKwZadpC87'
        b'FNGiRRdRyEVcFdqlFK7j+qITrVQ6ekdqZposBDnUgAqIRC3h/mlF/ssa3QZIMqqR8LLZxycyYUdRtiA080o697OdLhaJB2olIG9rS5lYoqD2dPqQ2vJrGC+eLDp46quV'
        b'b3AuZV+JXnluXnrfgdkZHXCnsPgZAiXS5HI2QQsYxa/rcJUb7DgUhjW0uFI7pX/w5PiUsZuYueU9qWOx6kOu6Ux/6zzaqWmTBmR4BtBaQS7Abzid94a6QTKJm4ecNKkr'
        b'gA4vq62qVXTwzfI1iLPXL78FQ2V/Ga7nI1D7I2H+E9p8In1C5P7rEFjPm1DZJkTOwgBYWXFp1K6e1wG98gCvFxPBCPhnVA4jWQKVkF2lKcwSiLVYpSRnQmY96ZgeaIz1'
        b'RNUtETkBPdnfre7vNVHbgKJ34a2fZNLEoiLUZSfj8qu1bdpdF+jWq6e1U9qR4b1QYE1k+oiPrNTunz0FUcVeXK9y9QBmQDq94wWRFshdt6ycvnF4JlQ2v8KzvczkQS3/'
        b'vZY/zZjzX3O7LEy4L6Pvlg1N/e9qCZw5tnbG3bcHJw/PkK46t+ev+1+Oe+3Rkw+cXPqb3/X76Kmrx30x7p2Voe+bfPu+qXvi179v+MMP5mMfPPn5XX22jJ+77tlAqvDm'
        b'Q+b102xJW0a/siV6wc0Dnl07nd+iiDs3C4Nyo55d+ga/9EX7kdl7V91yzPbp9mULNh0Ub/vAdmTmYf57d/KI9G9XrTlmSd18yztHDvLXyr9ouHXj2pv2vO9vfPmVRb+K'
        b'8n+x/fk3k9zzb9XsOb98tfFXi0PR3V/+6OOnViwVmvu3pL533biJXbytHwz7bJDnBfW2zXmLy+cMnjXjy5S5LWcm7xj2puUt0xffP1M49+NH30upWTBb/GXRnz8cPbCO'
        b'Hzsl70vn3Cde8K/Ydfi1DcWpb78164df9Jh1aOLs93b1fPjeoQ9X91jV9dyRR5IeP/FjbO/1X3UZN+G1oQ8OnrBt5KlPlu7MmZ/6Qd9PXvx680tXP5t8+KuxbTNfzflg'
        b'ftoHGW94tf3Fyz/+9cPX7LKMG/jRs7ddf2jUvrzcwLe/PZq7sVfx3Z9/aa5d8ttNr/bOLXlgjHyHuCo765GP709ZUXj9sg8WFD1edHNb1Ioljbe+m/znd8fOuX5yRsZz'
        b'b7xXPef+a+7lln/88JsnDrY991TvVfOLk1/Whtxx+q0PR40WPuBHPj0pe/+Sh8+3/OcTv7luVfH8xENp1+7KeyLp0B3nDr49Y1TDlyfu+WvLSzd+ucW7Y115cZ/8Hfkb'
        b'8x4MvV89rijjyYa9FSfOP3LgrQ/+43eLP15x3y/75e879e3xJ9///kTJubz/SFzm+LRfdfLS2MdLern464ZfV7j1VMW1rqlz/jTw++FjWvz5bz12+kDbMzeHHl737s+H'
        b'rrSFxjyacvgWT7cNS+9PSx57qHFky88/OXZ3/731pu9+9/Er3o/f/euP+Tcc3//NqLZbP2uJs3w7xfWt4+UfGh7709+Sun+3asXru9Zu/HtMzqi/WW+6/zdDjp996J43'
        b'UsZxP+5+cc5rB8bs+iIp/3C39+8/r7377AvP9Fi67M8/DtS+/TijR8l/Xjt4bu1rZ+q/THh47pxxR7Xd7xeVNX773MP3F3362KlDyoevvPHyX+atDG7cuPjAJ9c93315'
        b'842137x17oXN7wzOOfvKqBvfLjid1u3x5FVjWj+zPde27W3tr1lNacviH12d/8m99hfcfxua+NCu7S8dGlnZ+sOt3lkvHPqwMbVBmd7z19N/M2Fev4//eKz4k5o+bQ9M'
        b'e+rAM7z3++5NEw/PVI7vmXN61rXPLfrt1Q23T1u57+VZvuIx6aVnjp5696V9jXFNbz//6fBBZ8ZUnY+xt0TLR/cMfvWLlTcd++7ejAOLn9/0g+nuqJ8Jo21Z0eS5diK6'
        b'xaKjzE3aliIgH6cX5Krr1E0Wrqu2StROaGs58rsUp7WswGhAXhbk5Kkb1U0+7ZSFi1OfEtUt6mPaw950BBhn1fu1B9CaaYG6fuDUHC2oHtY2cFy8eqeonojqwbTXW7QD'
        b'6hYyiqvu8hblDkCfVScFdXvpHCpK3aAd7t7B1bh2SDsuQhXQ1Xhf7RQVBVmvUtdfIHKq3qGeIqHTpdeS719tW4N6kB3h2lD3Olc92VXgYtSzokvboj3pHYZxDmZpB7Lh'
        b'E6qIYmbqJvSlhabS9bYyY2DsoN830i4Vqnd6ByMcLq+MKL9gRmGO9iB6HspaQgkj5QNWFtq5+dpWL2566v3Z2laSLYjVjl5GfKOX9gxVcLa2O92TR06NNtVDJPVBbVdY'
        b'EuGCchq0XTb1lF1tIY+KI7RWrbkDu7ihXyS3+O4mMlKg7UvrEbGBnFS391IfnwpY4U/esy69mV3zL8zs/79LVm+GX/w/cTG4YlW1JbLLRZYbPoYLJ5vJ4sFP+9lFp80p'
        b'OeCXGB1vT+ySkCDwmbMEPiVR4PvmmoUB05KSnaak8ZIg8En8iJWcLXOpg7daMdwvTuB7w39ausAnmOHfmmIX+HhJ4BPN7XenjT3Hw713KnKJEx3wH4NPCbFpvL3WgaSC'
        b'EGtK6Z3AO1JjebvFwTtE/J7mtMI9jXfMF/jUYZCedxQpj4YZdkKEUYn/meCXvbQTCth9yJJkCPj9vkhTGcjM7KJurYadZm8as8I4c7oaxO3ImSz26KXdVVH77G2iByAY'
        b't6ThqdzNN9W8Od5x58ITN779x6aGxFG3vdf3pb0PdX9lyF/MprtPHPvL5g9ffWlSj3d6PvON9a/Rba88+JfxD+9dxa3oOWLSut5/ueHuje+/+8rah3bsevmOjUdyvHeY'
        b'Wvun2ptKZu+Me3vXF2fifzf9u53K1t9dW+G2fZvZy1eX1fJp5favt/7xWWnrjwf3z5r73qQuOd9MvGfB4fI/b/rD9k827Bm0u/DaIbs/+E1q19eGDNi14MMxf2+Ntwxc'
        b'N+2h0h37ylOWzflkwICXd+87+/LY6pxvZlbPHBJV/ZWnxy/u/e7ZecVVk3b+sUtwWdrUnLpJpXc3ZGz/7qW3s3/19O5h518YU9n1aNP5+cEDBRtOFg+fv+PT7SfvPNd6'
        b'cu+5oye3n9t48tS5O05uPHfPycNVz7Y+es/h5e8fqn/9fvcTYxq2r+vxx1mHDpw7+Yer3unzq16uqD99WX7s+W/ke5t/4fz8vLfLhsat65/Ytf705k+/2vDD2fvGPHPs'
        b'9x9t/4CvnZ/21SMfxDXkbjo9sOqF/r/I+v7UqYyxJZ8fevkNdduytz6+ud/LN56J/dUvbxq1p9+Og58+XeTbdvPX5Yq25f3to47dX5BwfcOHPyh7nrn7veBn9Y9/8eHb'
        b'n6zIHaY2vHBLZdq9X34y5ps94w72eCTlsbHXu756ZOaDM302U7Tl8N9mp/nk2PTm1K8yWwKDh8+a0HXY66+O75J74tUJ3cb85apnY5+/695z6vClg9SkM+e0sc66QJ/U'
        b'P0r7dr7j+OiJZxN2PKEOq6lrjm2I+XZoy7uVS999+e8PT297b0vbA8qmH7mzv397xKPurHGENKT3qoSptU9rpbm1XmvO0SfX9eJVWjPsmhhJva/Xgo6oTqa6w0B1AGkh'
        b'Ezvd1TPqPYaHTPKPqd2uHVKPqvu1O8jHsHr3opxs9XCOmRPUe7tpq/gF0YvINZei7tIOZhfmDkBzUtom8pO3vlBrtnC9tOZls03x16kPE2qWNFx94iKT51xP9faFzOT5'
        b'M+opsgh27Uj1aKG2W3sQ4mrrszB2tpmLuVqs1DZrp5mJ5dOz0cj8wKnaBqjrVH5KNjotUo9TTceqT5gLtY2ZAtT0eHYNP1Y7PZSsBGWUWrLRivpM7cRIE2ceLzjVHdUs'
        b'vwerVhICl5kL9d/Dc+ZG4aombRtzR3O3upMrJAOWD5qzCmCtWtWzgurv18BMIrWqjy0DFDEHqG/os90+ftyt2gOUrbpTvcOsHtDW0bed2nr1OD9HPTabDLdP6am26ka4'
        b'1CdWSpw5RbBrW25jrtDunYZ2NaeqhyDhZO2hJj4fBmMfw262jlmkNc/M4yHLO9zqOv5aba22xku2XzdcAwN9AG1XZA1Q16vNU7Xt6HgUEDLEwjKGmiarW7oTKqVtqdZW'
        b'RQGymqE9Vphrz0SbF+p+iUtRn5bUXeqd2n1k4XNMtnqMrJlB36Ads8IiE9dtkaSu7jt4bhH19qxSRMrQHaMgarerO/n8IXOpDT3Vh9OztcBA9Me4U92u7ufnqge1A2wy'
        b'7dEeL9WaC3D4hGGelfz4LAv7cHb8mOw8bYOJE7pqT0N3FS8eQl1ZMXREtrZxYKHaPKBgBs/ZhgnqZpgCjzEfk4egC54p1O50EISFMSYWwCpBe9ijBQlJz1SPx6nNM2fm'
        b'FuAUmKHuvd7ExY8S1QMDm2j+51bVFMaoTzIvtTOLKAfnCnGy9pS2y4tsJc1fmgztNHP8bG6ldkZ70NpIzXRXNLAJzRzOtqiH1CPapoXMs+SjWgsMRrP6CDMnIpXy6lb1'
        b'bvUZbWscZTpGu3N6YW7WtBmz62BCzhYS+yk05VLVtYMKU5NoARTgjItSdwpAKat7iQxQV5tugCnQLsw7OE4CmmQNDgAUxvzt7UxW1xQmajsKcgpy9Qo6tXVikbZX3UkT'
        b'yQnDWViAHmslCdksp9T7PdpmRmds0I5NYM2aAYOUVaDdr66GIrQtovqkqUFvnLqpMrtYDRaohzKzBk6DOR6jPSiqt0/RHmRGuVY3zCvMnloAKzSFr9D2qK1F2k42vU8W'
        b'zdSaEWBsgo/X8Q2L1TNd1HWUSt2hnQb6ZZqJ4ws5dU2NttOubacCu8J43wXLcPuoqTgh0SwodIxP0HanzWQF7vcOh+/kpFOK5a1L1F2Dk1iBZ6cMK5yWA2MTLBo2hOcs'
        b'2mbBnDyOsq0u0e6LMPCpHbfo9j3v1k7Q1Onh05rbjWtqO+fqxjUT1I3U04vUfdcUZqwkU9CGUT2n2iJOUk9qeylGtKyhzeKDt1xkdvXJ6xIJRl/tUzdfYPAUiNBVusnT'
        b'mTd50bOGum1lI4KhXFhVA2BwYFlvBsAznTrjIPyvL8xVH5W4GeoB9LtyJJsWh3okzR2FpGsdpi3E2ZSg7RaTkrS9WktPNlda1Ye6wzRd3w2X+dQZAFuitAcE7XFYgpsZ'
        b'jXu3+vhIrbl6MjYQdhFcXscF7XiR9gj7/ljSbFif07VNhTlZudPGAHztkiYCTXpgOoP96mn1TCGuPmhksCBn2kCyOZnDmbRj2j3aPerjNxBYUptvU/fr5PuGmVlIHW7A'
        b'DS0xQ+qtPiBCw9nc2zzEozX3h0bNnEnbjQXqcwxWyFLtGNvzNuaWw4BrG8drq6cvJa4g0KQWLlk7Lt00Rn2ANXu/eqoeKqUdxXxm5lZrOwSgymFbbDWXs3lz4NbR1Gu4'
        b'nUm5fNcKVCA6RPtelLYdOhmqOrBQO1jZvv1hdbv3ldQ1/dUnCaaN1rbJhQUzBsxo6m/hzJJgLdKadU9oqePRlPVNelNzoVe1h2FSADy78wqME+uE6P99Curf+BI+qCa6'
        b'DoXFuShBsPIX/uxALzEZG7TAJ/EYx8m+4PFLmA60MzFEwc5H/IRYAT0/WcnvQkKHfB2UJ8bBM1EHKVxb6ZzUIZhF30ru4h/QnYwFz4QoUKTE4/bW17lc7eSZcY5xgI9s'
        b'Iz4wMuRbRwQZQt/CUhPR8I/GUlBqwfMcXEs5mV8Mv2BxoBhl2IL94S7AXYC7CPdEuEtwvyFQXMHB3R4oRjXEYE+Mvxhj8n7eX2xI3TVxKHFXJVZLwZhqUxNfbW4Sqi1N'
        b'eCppkW1V1mpbk0TP9ip7dVSTiZ6jqhzV0U1menZUOatjmix45umNhdy7wj0O7l3gHg/3NLh3gTsqRpvh3svHBWLgHuMjU0PBKB9axuWDsRAvAe7xcO8KdyfcE+GegWLg'
        b'cLf4pGBv2RLsJovBJDk6mCw7g93lmGCqHBvsIcc1WeX4JpvcJZjiE2UukIyi5sE+ckIwS+4azJMTgzPlbsEZclJwlpwcvFZOCRbI3YMD5NRgjtwjmC2nBTPlnsF8OT04'
        b'WO4VHCn3Do6V+wTHyX2DI+SM4FC5X3CY3D84Rs4MjpezgsPlAcHRcnbwajknOErODV4j5wWHyAODV8mDgoXyVcGB8uDgNHlIcLY8NDhVHhacIg8PTpCvDubKI4LXydcE'
        b'r5dHBosC9jVcsK88KjjR2w2e4uTRwenymOAkeWxwjjwuOEjmg5N9FviSHhB8Vp+tHHspwe/0d/P39M8ol+Tx8gQYP7vPHnSQnEy7IVqnP8af4E+EmEn+ZH+Kv7s/DdL0'
        b'8vf35/kH+gf5J/in+PP9U/3T/IX+2f45/htgPvSSJ4bzswacAWsga40QtPmZ/3aWr4NyjvXH+eP9XfXce0Devf0Z/n7+LP8Af45/sH+If6h/mH+4/2r/CP81/pH+Uf7R'
        b'/jH+sf5x/vH+if7JUHKBf7p/JpSZJ08Kl2mCMk1UphnKYyVh/v382ZDiWn9BeZQ8ORw72i+Sa4BoiBfv76LXJt3fF2rSH2oyCUoo8s8q7yJPMdI0RQWcvigqoR+ljYJS'
        b'oqk/k6CHUiF1H0qfCemz/bn+q6C++ZTPdf7ry5Pl/HDpItRVpJykFXYcxyZHICPgCAwIOHyOQMEaYQ1KNuCbHHqTw96scPii6Oz+WuaDgFQJmKo7QojOZeBwg2RKWwGu'
        b'0qakeNH8CLeYN4THdUH5tq4Znsys9AomjlqSXlpfUeWtqMkSFBdCnT4Rm9ClTGW5ymuIrYaCbq+YwsZE8MxaOWQowGRJAOIWur3lCqpcWN2NZSSrQwrveBJfWx5yGLJK'
        b'JKPEoyGUaoCJ8GRHY9zVdYrb44GQWFW7ENWiUY5NOQN5n8dGn6eeoadGvKDHwPPYJSSNXSu7AbKSrgTKsIfEutq6kB1yl93lJagcYS13seNeZoGo3VZFGBqHzOWUTyiq'
        b'rNZVoiwkB53oXdRV2VBbU7Us/MoOr2pYZiEHPHu8JbpFTyuEyqtKFnpCFniizGz0UOPxeugrSd5TCUtLlPYASvdiiNLRg5PeKh6Ss6ippXyqYAhLSlkCxe1eihbXMYBi'
        b'FBQwlVW5S5SQmfy8XBUSSysWktQ62sRhPjlCdnTozJ6ZbNEJfZC9SkmZGz09ulwQvdTFBtICTygXEZJcirs85HTJFZ6S0iq3q6ykbBETSIaJITNDbUh0tAmZWR288eHk'
        b'QCyM/JKgvuEa3Yo+GpVCc69NfGMiGaR0kklLHqC+0MQvSZ3LLHy1KxZfdIL+jwxF4eQcYDZE2wgXsBuTNlxHlGEzG3V8Dr4ELADjHLCskrEePh6gj1COehppMnnYIe0N'
        b'MZBOsmWSTwrYK63K6oCjyeQTAlGVgjIVns01mRTilFsDjiiuyRTgmCxawB6Ihy9OaLujG/aFOWCBcI81gs8c6AolCjUHfYKyGd6lBRLL0ZzOdpQpg3K6QDmHKXYSpE7F'
        b'3Gpuh/c9A3EU75NAHEAcS2M6abYlNVkhriWQAHEl2Cegt9egFs0L0K8S7B885WmutN7FK3kBM6S0NeZR7t0hpmGAxw656Kl9Nniy4xP5JbJCPrbZHOuHAE/53AmpYwLR'
        b'UbqOnU8MxNLX6CQ0BQxUnsz5ovCbTwCIG92NY6pfZMzUxvwUhGX2qF8hz70wHvZACpQvYP/4TAmoAZPE+gO+P0N17mb0iC5/Z8wZx//WAUivfwMe9U9iY+PMHoozvohA'
        b'tJPhqoStomCRWbCSyFE8Wk8VmXiSg/DhJMJnzXwin8JLolNwCrF8KqYT7fAOVo0QXjBx+g5EC+Z1QV8wThjmLH3BJEQuGPgq4sAFJNilBnVYQjhw2ZBGoiec/Caf5PmU'
        b'PNmbA/hLhAEXUfzPZ1FW+yykzGP1QWls4sCSSRnN1SwKdA/0CfSDhZBcboJp/KLPBtN3VpM9gIJzdsg3ymcPdIeleQ6mXUwUl4wbswjPTnz2OWjxQU6+KEARY/TpG4Ux'
        b'2DeffTS3ZPtcrqYm0DcQHegu84E+8N8P/nsGMsv5QByWFOiJSywBkEx4nxLgA7GBWETOKiy0yE04iWE5xfms0KJomPBw98HSCDiTuCZnIB5QAnzj7MbBsokmVCEKUuWQ'
        b'27BGygGey6HVG/kmU82n8MYcGAB5xvhiAkn0HQAD1DcmkE6hdD3Ul0J99VAGhTL0UBqF0vRQilFPCnWnUHc91IdCffRQPwr100OpFErVQ70p1FsP9aBQDz3Ui0K99FDP'
        b'cL9hKJlCyRgqj4FNIhcRfB+3EcEnAgFoa6B/IBpaHOuLvUvwPOqT6GrBK82XbjhfIA/o+3K0JK63phuHaobQn11wnkGuIhmIkLDnEYjT+2yfhO99ku6jJ8JSeNz/kXWb'
        b'lfdvADv+++FTNcKn1e3wCUUfBatuKdssOpnzNkng2c9MHnJQsTkBYiaYDd/NaGE7VkJ1ZzT+5RDiRTtALSd/qV+84BBj+XgRPTyniA4RafowTDOUwgimMauXALWAXA5Y'
        b'dZhmDnARME0MmGgzB2QlYANEH2AZEyTvsPl0ip/8C9wUUDe+aTbMBLBuFLEjOjTIZjRoPzZIgkWBWIcAYDieNWINyY0q/VCmPRCLJj7pveSjmNC86AC6KcGFFANAKRrB'
        b'NIZQOj5g39SPx1yjAvG46LCjCGCJJgCpAdvVgPyNjpCLB+AGYBKAOS49fI6FFCTnjV6KKK2hC3O5zuvy3ztXPzFH6HJJAipESRY7nyqiKhCbRfb2WWSP7PQqRCUB7QvE'
        b'IJob7nRJ7/RM6vSugHiJnhz6guFEDJMR/ckwsxyoEkzf7JtSqNtQT96SRMoJGOrQwYC0BSywbwFKCvtFuU/0rDPQaR5zlwA9hP2zMd9nUkLohBKhJexMJthFYAibLMvs'
        b'yFYgZb4EifNylXbl18xcDnOmSWmSMA/cC4nQdgLR38Wf4O9WbtH921jbSwK0EVYJ1CUlEI3vjPRsZwOcwQYriuraONpngrscLsGGjA1KWwxp4R18sYXThusBaOiAuRF+'
        b'cy7U5Qkb4w37bUS6A5oMnUz+IdCCBLrkQbOVtTmIe5IRgAhbWWJI8JYqZ5FSfJH/yQY9Qs4Kj6u2tNzVoKA0tzLcEla0kUjg286oESDBkRz/pyRyk/+dgLvdomtPGQsm'
        b'Fq4OAvMo5R4PYNwsSWRYAMVsUC0SSTKzzSkmWfBtvMWps2vj+awkxl8giePxHJk9WOZRDuO7x/ByBC9HeZK9RgM+HuUY6RUsr6ooVY7TY3WJd5FygvSx4cFdgt4alJOk'
        b'LVMhK2mUKdDeIbGkFKj2RSUe1NoOWXQLVCGLx3hYWFVbChR/VvS/psuy5v4b8NX/5/LPHETgnPwZ8sFCOM8FQbrwEMJpSqIjAzweuPiQgv2kTn6OTt/+8z+z/h8Omx1i'
        b'vEUSpw+DFSiWL8ZrukMSB6Xi0+hJuC4Fq5nIQ0GgdhahHs6DHHlrcEXy71wufUVWl9TBsvQqisIzpV6yTsDOPg7RupvSWOauQyNNCp6X4UlIWUm9x+1yhRJcLk99HfH9'
        b'kEmGmi7wNsrVHlBe72hkIkIDdnR1rVxf5R5LRyBoWlQSACMUABHq7DxmJTdBf99bIPO5xlnQ/wIksS7p'
    ))))
