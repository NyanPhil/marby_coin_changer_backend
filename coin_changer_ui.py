"""Marby: an 800 x 480 Tkinter coin changer demo. No extra packages required.

Run fullscreen:  python coin_changer_ui.py
Run in a window: python coin_changer_ui.py --windowed

Exchange totals: PHP 5, 10, 20, 50 and 100.
Note inputs: PHP 50 and 100. Coin inputs: PHP 1, 5, 10 and 20.
All payouts use PHP 1, 5, 10 and/or 20 coins; bills are never dispensed.
Coin inputs accumulate, so two PHP 5 coins can become one PHP 10 coin.
Customers can choose preset payouts or build their own exact combination.
Back keeps credit and draft selections. Dispensing needs explicit confirmation.
Currency pictures are embedded PNG thumbnails from the BSP's official site.
The app runs offline; no image folder or extra package is needed.

Insertion controls and dispensing are simulated, as in the original file.
Real acceptor, hopper and inventory handling must be connected separately.
"""

import math
import base64
import ctypes
import ctypes.util
import hashlib
import os
import subprocess
import sys
import time
import tempfile
import tkinter as tk
import zlib
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import messagebox


CURRENCY = "₱"
SYSTEM_NAME = "Marby"
BILLS = [50, 100]
COINS = [20, 10, 5, 1]
EXCHANGE_AMOUNTS = [5, 10, 20, 50, 100]
MAX_CREDIT = max(EXCHANGE_AMOUNTS)
MIX_SHARES = {20: 40, 10: 30, 5: 20}  # Percentages; remainder is PHP 1.
FULLSCREEN = "--windowed" not in sys.argv
ALLOW_ESCAPE = True
ADMIN_TAPS = 5
COIN_DELAY_MS = 120
DONE_TIMEOUT_S = 8
WIDTH, HEIGHT = 800, 480

BG = "#F5F8F5"
SURFACE = "#FFFFFF"
TEXT = "#24352C"
MUTED = "#617168"
BORDER = "#DAE5DC"
ACCENT = "#24744D"
ACCENT_DARK = "#205C40"
TINT = "#ECF5EE"
HEADER = "#EDF4EE"
HEADER_MUTED = "#617168"
CTA = "#24744D"
BRAND = "#24744D"
LIGHT = TEXT
SOFT = MUTED
DIVIDER = "#D5E1D7"
GOLD = "#936116"
DISABLED = "#E7EDE8"
FONT_FAMILY = "Roboto"

# BEGIN BUNDLED ROBOTO
# Google Fonts / Roboto, distributed under the SIL Open Font License.
# https://github.com/google/fonts/tree/main/ofl/roboto
ROBOTO_FONTS = {
    'Roboto-Regular.ttf': (
        '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'
        'tol2ina/9ns6jI6TTplOs84VnSe6rK6FrrvuPN0i3RW6X+p5663Uu6dvrR+tf1b/OwNDg5kGqwx2G3xv6GhYZjhs'
        'ZGoUZXTI6E1jvrGL8SLjFuMPTViTaJMMkw6TL035pjmmp8x0zRLNFpojcxfzo+bPxvHHTRh3edxdC2zhYJFhcdHi'
        'nqW+patlpOUiy1rLG5b3Lb+0/M2KtUqyOmx11drCOt66e3zM+DPjv7Lxs9lh81hgJXAT5AjqBF2Cr4TuwhZbB9tZ'
        'tk2239rNtGu3+0w0WRQrahINiN4XPZyAJ1hPmDWhesLZCW9NkNkb2tvbu9qn2FfZ77I/Yv+p/df2Mgdnhw0OJx3u'
        'O/zoKHKscjw70WjiyomfTtKZVDXpk8kuk4smX5v8jVOA00mnR87uziud7zkrXHxcal1uurq57nB95Jbk1ur2w5SZ'
        'U/ZMeWvK71N9p9ZNfc99unu2e4P7ux4OHnM8Nnqc8PjYc5znPM9tnp94BXqt8vrOe453ofdJ76c+mT5rfc76fOdr'
        '6RviW+y7wW+cn9iv0q/R77a/hn+E/0r/2wETA4oDXplmOK102vlpv0+3nF4+/XogE5gReCHwlyCnoFVBb4jdxDuD'
        '2eAVwX+FLA75MNQpNCe0MVQ+IyMMh3WE64QvCe8P/ztiUkREhCRic0RLpFfkpsjDkUORT6OmRx2OejXq65m2M9Nn'
        'ls9cN3PHzPaZD6Oto+dF747uiL4Q/c0si1nJsw7FaMZUxKyP2R9zM+bZbL3ZtrMLZnfOfjBn+pzmOY9inWIDY+Ni'
        'a2OHY9+J/Vfs0zjduPS4zrhf4nG8Qbx1/MT41Hhpgn1CU6Je4vLEr5KCkw4lPZkbMHfz3LfmGc1LmHdx3mvz3k72'
        'TE7/L//yk0uTVyXvSD6efC35QfKfKYYp41MmpSSlVKa0pgym3Eh5L+Wn1I7Um6nfpCrSNNIM0yzTRGnOaV5pgWkZ'
        'aQvTatN60x6kG6VbpU9Id0n3Tg9Kj0yPS09Nz0svTV+Svjp9c/qZ9HczHDMyM/oyrmVaZmZn9maOZM3K2pr1WjaV'
        'XZN9O8cpJz/nVM61nLdzvs1R5Obnrs7tyb2W+33eirzz+Sb5wfmL84/mf5j/dQFVYF0wsSCroLngz8LUwvNF6UXp'
        'xfHFDcV3in8ucS2pKfl5vvb8tPlt819bMGlB3oIVC4YXfF9qUxpVurW0u/Tj0j/LEsrqy75ZaLkwe2HNQunC1xc+'
        'KxeVe5Wnl3eU36kIqthWcavi0SKTRfmLNi86vehNCU8SL9kt+Wmxz+L1iz+sHF+ZUllb+coSrSVpS64seVxlXZVY'
        'taPqStXP1YLq9Oq91Yeq31w6funSpVeXfrMsdFnNsqFlfy7PXD5/+eHlH6+wXBG9on3F45WeK/esfLwqYFXrqo9W'
        'u66eu7p+9aer/1yTseb4moE1v9TY1lxda7m2Yu2Rte+uY9f5rlu87vx6k/Uz1metr1t/Y/13G4w2xG7Yt2Fow7cb'
        'vTcGbYzcGLcxdWPextKNSzZe2qSzKWrTvk0/bdbdPGvzts1nN4/UmtcW1S6t/WbLjC1FW8q3VG9Zs2Xzlp1bDmxp'
        '29K5pXvLhS1Xtry25d6Wz7d8WxdVt6PuZJ1864ytB7YqtoVta9z2/Xbv7S3bH2//ZUfmjtod7+7U2Jmxc9vO1+Hf'
        '27usdxXsOrrr9m7ebovdzruDdsfvLty9fPeu3Ud29+2+tfuT3T/tofeY7Zm0Z/qe2D15e6r2bNlzcI90zyt73tvz'
        '7R5ZvUG9qN67PrI+tX5h/br6hvqT9UP1b9V/Wf/nXs29Vntd94bsTdxbtHf53m17W/f27r2+94O9j/fK9xnum7DP'
        'Z1/UvvR95fuu74/Zn71/8f5N+xv2n9w/tP+t/V/u/+OA5gHrA64Hgg8kHig6sPzAvYbpDbENuQ1LGjY3NDWcarjS'
        'cL/h64a/G3UaBY3ujWGNyY0LGlc37m480ni+8WbjO42fNf7axGuybHJtCm5KbCpuWtm0s+lw05mmwaY7TZ81/das'
        '0WzV7NIsbk5oLmhe2ry1ua35bPON5g+bvz+ID5ocdDjod3DWwayDiw5uOHjg4MmDVw7eP/jo4F8tOi2CFveWsJaU'
        'ltKW1S27W4609LXcannQ8nMr22rRWtL6auv7rY9bZW36baI277aotvS28rZ1bXvbOtsG2+60fdb2pO2vQ/Qhs0OT'
        'DgUcijmUc2jJobWHth86dOjsoeuHPjj0+NBIu367qN27Pao9vb28fV37/vau9kvtd9u/aP/9MP+w5eEFh1cf3nX4'
        'yOG+wzcPf3T4yWHFkbgjeUeWHKk90nyk+8i1I+8e+ebIsw5ex7gOpw6fjqiOjI6SjiUdtR17Ozo7BjvudHze8dtR'
        'dNToqP1Rn6OhR5OOlhxdcXTz0cajJ48OHb1/9OtjXscij6UeKztWc6z+2NFj/cfeOPbBsSedqNO407FzWueMzlmd'
        'iZ3pnfmdpZ2VnSs7N3Ru69zbebCzo/NU59XOdzr/1fn0uO5xwXGP4wHHQ49HH084nna8/Pi64/uOHz9+8fi94190'
        'BXVFdKV15XUt6Frdtbursau9q6urp+vVrje63un6pOtR15Ou37pGTjAndE6YnHA84XbC58TyE+tO1J1oPdFzYuDE'
        '8Il3Tzw48dNJ6qTpyYknA07OPpl7surklpMHT3acPHWy/+TrJ98++fXJv0/pnRKd8j4VdSr9VPmp6lNrTtWf6jx1'
        '9tSVU/dPfXXqr9Pap41PW50WnfY+HXU67nT+6erTW0+3ne483X362ul3T397+ucz7BmLMy5ngs8knik6s+zM9jPt'
        'Z86fuXXmrTMfnvm+G3ebdk/sDuiO6c7pruyu7T7YLe1+pfv97u+6f5XypVZSV2mwNElaLF0p3Sk9Iu2T3pY+kD7t'
        'MeuZ3BPYE99T2LO8Z0fP4Z6+nrd7fuplesf1OvUG9sb15vVW99b1tvb29F7v/aD3Sa/irPVZ37PRZzPPSs5uOtt0'
        '9szZ4bPvnP3m7LNz+ufsznmfizqXca7i3PZzXecunbt37otzv5/XOG913vW8+Hzi+eLzK8/vOn/kfN/5W+c/Of9j'
        'H9Vn2jexL6Avpi+nb0nflr6WPmnfK33v9X1zgb0w7oLThcALcRfyL1RfqLvQcuHohS/6bfrF/bn9h/u/HDAcCBtY'
        'OdAzMDBwZ+DdgQcDXw18P/D7gGyQHdQdNB2cOBgwOHswZ3DJ4JbBlsGeweuDHw5+fxFfNL046eL0i3EXMy4uurjx'
        'YuPF0xeHL7578duLsksGl0SXfC5FX8q6tPjS5kvNl7ovvXLp/UuPL8kuG162v+x3OeZyzuUll7dcPnj5zOVrl9+7'
        '/PiyfMhoyGHIfyh8KH4oc2j+UNXQuqEdQ/uHWoeODZ0Z6hsaGroxdHfovaFPh74e+mHojyH5FaMr9ld8r0RfSbiS'
        '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'
        '2p0ZA+57Z/5L+bdtHPDE3Ose7Nt89L0T71y/sIda1TP98xWTN6ZNv3fA9McHyfmdh6enNWoyfMb9Y8cund3zrq8W'
        'jLpnUO9Z/dsNTu9Wt+m42Q+NvWLpjIu7z18zd/DsAed3n3lmrT3nWtMVPf9WX9dOuHJyrIlxWVntT+gYdEeykdud'
        'smOsp8qLWIZSp77RswR2u176Z2fWlHrc39Vxdv1PLJUuI338RoWWS6VN6LvkuOOSHZwyTPHfpSL75Ldv5e2T4ir1'
        '/+9UaK/03DJN37xC+1XOXjnzKXWNvFR482708SB9vBx6Q/e3RlxZraLGubm4K2501Vev1Zrexvp4jIitST2iV5zX'
        'SK8kKjWsmbBALzd3VtSfw1rz3hnzBwYy9Vrzt2+95JJbnbXmmYG+8y4fe1O/hg363XR/t7OvNX90fj+v51tbl0k6'
        'la30G+vV8VXivzGbWlk1c2DgMHRhd7x2qyMTVTsfixu90zIYL9zeOT1XJKhmcpz7LGn74+hgOVFfN8wrkXQ9q6bY'
        '1fGe9qGYjj8aP3v3R6+Xf9VwEdNwb8Sp/NhDf6O1M/ZQ5zxf7335sYf+0hm90lQrz8ZrofGBw6uW/BNeCw1nfqSm'
        'iuelVzJc4q6xKNUjVwGr9Xn+lQyamy6vK126Mbq8HLp3z7riob/4zRkXSfKveCg/K7q/avspmdX3p22mdYGIQqXe'
        'G61Hz6waxoX6OKiPV9nHzcf1KH1AtzACRmrsiR9GeiDbm4mzwh7ozMRR60G8eLMDghiouMkHy6IXLdWOrryedVdT'
        '+ecPkM7g7TrlI12q15wxkc7++QMNo7O1PYvNr/6XXEzNTH3bMqvpzou3ncUOyiZEZ2ubEJtj/S/xpaY0jd4dFeVX'
        'HuW5rX9yLGGGZwn7yzmOJawifVTntnbCsUeHPXvUX+Q6dU/x8uoe0UPgAm3lNmg5XhNtHuina/oWfVwLLrnBAuL6'
        'uprLWitN/Kbb2OfVkLKtV/f+gK5K4BPo6jl05k57u6arW1vKO8oiiejgxHQ952K0LvVJ1lLHekcHV+qoZ291ds4H'
        '7tXnR0SHW7N13f9Fz9ibI5+331G6loFN8voNJ9BaXWcNharIpepnv6uo+iDt6d5sYnj5VqpBla95ydYBH69J0eH+'
        '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'
        '/rVhelX15MekhLtSkitX1ktfU7c677buHP8WCdWGLnuLxJUb4l8icaqqvgHtTNpD7pvHW4s66Ul1U+9uceGFrVoF'
        'kmKP8e9zTq8gT1C3+69fQ/75hv/iReTZOl0V2AYjOjwwR69o7aSfjjDH+MB+x9PTbzw9nS+W6xWNZnKir//SqTHf'
        'eDVm/iV61WO92j6aKehyUOtmFadO25FAN2uJ5axBTZCn5UF9Xr+BRcV0xpPuLNYVutUXrJsStzpyk7P+33gq7ikB'
        'Zgf/+v/+xNa+9YbE1i2iL1SwFq2/XOWsRatT2bc2rDzVQqOjQ1XrDCpti9x5YnK2cCxf48pnXaUvVGv2JdFIRwnD'
        '4ubmvCTvdJ+KEpCyhzeXxnk6sNd6fcmdFWtcwv2HlsV0E+JG+1+SPURl/TQK/xsDJ8HLP9b/knrxmm7JCx8vd5W/'
        '56Vfko0cmxIdpy2ZtvPqvCgQibFY3HtX4VlicSHFm+IR60LzD2pb4huJQrRXL5LVzyQue82QMXvRl7fe+uUi/ftI'
        'bEf9cv3TyLGv+brqj3pLiurUo/Y3USWfNl8zXz81UvVY3YBmrQl8JlJFHdFEtFJvQG+SemFindQGianqXZixd/Tc'
        'ql54VE29QrlmMEG9yiigTrCVbKXa6j/VmRsCtavLV5qMaJ2QMCKlXQM5JliruvwtWLvaH30DdapbH7MXTTh/eFv5'
        'KHtT2o5tcaX5c8uMOn/kVKlV+fZajYLftR3XYlbbsc3k3fwnjbZjWyLFT1pm1D119xj+ct64HJNLY5H6rkidlVhn'
        'lpZP69ZnSqi537zWrFUrTmKLZqyZOnXNjOkvT536cpz0hkx9ebr3n9Cf+vJy9eYUSuwiPVPd2W8ughw5+y3U8zXd'
        '/TaUdzV3v5NQPU3OfmeoG6l3sFhq9O5N0dTdl6KK+MHdN6gB+9x9UzQQRe6+5dsPiGYyyd0Piga0R539BJEuh7r7'
        'iaKKXOLuV4L+WXc/SdSUn7j7VXz7VeUFcoe7nyy6GaXuft2ytJH3ymZrd7+5qGJ2dfdbsN/X3W9Tln7yXsV000Pe'
        'K5tXjL9+2s0zh81bMHfKnPHTr79u5s2jpl+3cM6UBYNunjLn+mtHzZs75QbRT8zDfN4uFojrxXViprgZ5exEA7cj'
        '3yY01WaK6WxHQTUV3Aya0KxdwHYW/1yr6fuKhWxncm6BuInjFprPzfC9iUZGe77XwV1RLIRLO66aJ+bqs/P4Xifm'
        'wGkGezdAcxPnF/ju1hbqOZjpm/hez37LuLSM4srr4KooFpRLZfx/4zhaoHmo+zShSdtO57IrzRYnx51oco6Ku/Of'
        'cb9e53QKuJn/pohp0M7VdLM5N4/8NBGX+fLXLu6oH7JYoHnczO8UnSKHv0qlkoJKZfz1jtRUiTj3HuBKrIkYre93'
        's7hV33+6l7o5WmLTobqJ32mcWcj+NH2PJro8puurB4khbIdTXtN1Sso4D4nj0IYz5eXYkZQpNPGlLP6+ZbK6BVyv'
        'pTlV56kJKXb0wpHkADRppN6/Gb1pcoYWzXNTGNOV+Pu00/p33f/wqvGcnabTMkyfUWU5h7PTvXoxCExxrx6ly0KV'
        'm45I9ceepZ5HWcFHYmUStTdK0fvJzmmjBftX4F97c7Y/rVhJlZrF73y+kqJayO+9fNVbz+/j90G+UjzCVxIB/Z3f'
        'Z8QKfleJF/ldI17m999iHel5g68U74sP+P2ErxSf8pXic/yzFJv5SvENXym2iK38bhPb+d3BV4pdYje/+/hKkc9X'
        '4kkP8ntY/MHvab6EalIKKU2JrZGJEosqa8l6/DaQDfhtIi/g90Jslilb6RXWnSU+VnaT3fi9RPZUKwNkf/XcQDmQ'
        '38FYUSlHypH8jpET+J0kkYacKqfyO01O43emnKnmkcs5/N4gb+B3vkRKMlvmCEMeIXyURoBWjTSSjWR+U41UfmsT'
        'H0qjPvGfNBqpx5oaFxikzbjQaMZvG6MNvx2Nzvx2Nbry24/oQRoDjAH8DjRImzGYOEMai4y7+X3CeJrfvxtRobK+'
        'kd/PzM/4/cJEhuY282d+fzFP8Pu7+Tu/pyxliwNWAr+VLVJlpVrP8/uCRalZq6zV/L5k/YvfNwJVhQykBEhtoEGg'
        'JRKWWqtSQS3QRJ9Zh76oEl6rlIev3tNydrxiZQzYDTS1BgwZI+pde/uCOaLedQumzxb15ky5+QZRD58mdKxkuTpp'
        'Cuva+TfNF/VmT19AVZ47ZcFs0WLu7Lmz9RODpaOk+p7CodbbAD4wQaQaDa47NHPtzY8/9MJD2zSFRMclaQiICwWS'
        'Q1sSOaopziMHtfHJdUlBfbxqQzRerQZqgSlvRfujDYa2HdVUGeNOmOUumORu4mLRXfSgAl8ieope1BBliO+lFtwv'
        'HhdPiqeIt97Ao78l1ou3xTviXfGe2IC+f48G78R/ZosfxU/iZ3T5F5EjctHoPWIvGr1fHBB56HQInS4UB2V7NLOr'
        'vFj2QCv7yn7yUjkIbRwiJ8gr5I3yTfme/EhupMT/YTxrPG/801huvGCsMFYaq4zVxovGS8Ya42XjX8a/jf8Yrxiv'
        'GmuNdcZrxutGpvGG8abxlrHeeNv43thpZBs/GbuMHGO3sdfYb+QZIaPQOGSEjaNGxDhmHDdOGCeN341TRtSw0SvT'
        'DJgJZiUzyaxqppjVzJpmLbOOWc9sYDYym5gXmBeazcwWZiuzjdnO7GB2MruY3czuZprZ0+xtppt9zX7mpeZl5iBz'
        'tfmi+ZK5xnzZ/Jf5b/MV81VzrblOhaNmpvmG+ab5lrnefNt8x3zXfM/cYH5lfm1+Y35rbjG3mt+hy9vN780d5k7z'
        'BzPb/NH8yfzZ3IVu55i55m6zyCw2S8xSdLqKlWw1tVpa7a1n0erVgaaBi7StM0TlDCyZuVfpjDyc8EKvjF4ZCd/2'
        'WZTeqtfAjA59TiS2S1/Gt0v63Wqb0SF9Y9K3VZ7rW7nvzgyr18Q+iRn1qqb22Zm+v7dVdVz6O8mPp7/D10rfn34q'
        '5Ym+oZTjvdb3DaUmp+/P6JA6pndGajY8F1VrU71VjTY1k2tm9g3VfKfmxvR3ar9S95/1nqi/tv6m+t/W/77RtkbZ'
        'jVMbD2i87QKj6UsXLUpf1uzLFgt6TWy1U6Wh1/s6Rctav9J2Qvqy3nXa7m/37/Zp7f/Z4S+9kzvW7LU+7bOOhzp/'
        'kb7/4lEXL+2+Ne2f6ft7TOgRSktNm5H2T/Jl9d3ZN5T2GSnO6J3ca2Kv9eRNfZfpfZ1H53yvjLSwkkavjIyJPZ/o'
        'mZMxplf3jGEZYzKG9WoFkI7z7Vu5zyL/t9fAPiecr5NOh2fs2yexz07/t7flfLXU3G/fUN8QnHbG0Gug81Xl0dsq'
        'D/i/U3YnXVLO1znv4B1Kzooh/ZT6UoZ8M6w+idyNctTfMXwnkkv/d4z3dY97dXe+7tmJpPGEk0tyh+b0OZFRz02L'
        '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'
    ),
    'Roboto-Bold.ttf': (
        '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'
        '8bWna38Y6TgyfuSckXtG3hn526iMUctHPR3tMLp09KzRbaOvj+bqPOsi6yrq9tXdGjNgTNOYm2Oe1zvV19Yvqz9a'
        'f3es+diisc1ju8b1H7d83NPx8vE149eNv9Xg3DCq4dYENCFoQu2E3RO+mmg6MXrilIntE89N/HlS9KR1kx5ONpxc'
        'PXn75MdTnKfMnbJiypWpzNT4qQ1Tr02znVYy7cx0m+nV06/MYGcoZ8yacXam4Uy3mQtm3p75ZJZ4Vuasn2cnz946'
        '+3ajoDGscUTj7sZnc1LmTJmzds6FOdxct7lJc+fOvTr3j3miebXzxs+bPm/+vOXz1s/bNq913u/z+8+fNf/GAu8F'
        'SQvmLfhwwYuFoQuzFrYsbFe5q2aotqtaVe2qU6qLqo9Vt1T3VN+qnqt+V71eRC8yXuSyyGPR/EXXFz1bHLN47uK7'
        'S/otmb/k66X+SyctfbjMb1nYsu3Lri93Wp6xfOfyOyvs4M91xbAVR1b8sbLXyryVw1ZOXbls5baVx1ZeXflw5e9N'
        'gibHpj5NiqacpiFNk5qWNG1tam/6sOlu04+r0CrrVbJVEavSVpWtql81d9XaVXtXnV51c9XTVS9XG692Xe2/uv/q'
        'vNU1q6esXra6ZfWR1ZdX3139fDW3xnKN+5rQNclritaMXjN7zao1u9ecWGuxdv3a/WvPrf1s7Xdr/7XOaJ3LOr91'
        'cety19Wsm7xuybot6w6v+2B9r/UL1m9cf2B95/rP1j9Z/68NRhtcNgRsiN8weMPwDdM2LN+wfcOxDVc2fL3hxUa0'
        '0XqjaKN8Y8zGrI3VGydtXLxxy8b2jZc3frXxp40vN7GbHDbJN8Vuytk0ZNPETYs2bd6k3nRx051N/9jU3WzRLG0O'
        'a05tLmmua25sXtO8t/lU843mR81/bjbc7LzZd3Pc5rzNwzZP3bxs8/bNxzZ/tPne5p+2oC1WW2RbIrekb6nY0r7V'
        'Yqt0a+jW5K2FW0dvnb119dY9W09tvbH14dbfWwQtji19WsJb4lsyWipaxrfMb1nfsr+ls+Vay5ctz1u4bRbbpNtC'
        'tyVtK9w2etvsbau37dl2ctu1bQ+2/bad3W6/3Xt73+0Z2yu2H9l+efvd7T9u53ZY7HDbEbwjccf6Ha07zuy4uePb'
        'Hf/aabjTeaffzridaTtLd9bvnL5z+c4dO9U7T+/8ZOe9nS92oV3Wuzx3Re4asCt/14hd03Yt3LVx16Fd53dd3/Vg'
        '16+76d32u+W7p+xeunvr7vbdH+6+u/v5bs0e6z2iPUF7EvcU7Bm1p3HPoj1Nezbu2b6ndU/7nlN7Lu75eM+tPff2'
        'fLvn+Z7f9wr3Ou313dtv76C9Q/ZO3jt7r2rvyr0b9m7be2zvlb1f7/15H7XPbp/Xvvn7lu3bvq91X/u+D/fd3fdo'
        '3z/2/brvZatJq02rc6t7a5/W4Nbo1vjWga2DWotaR7dOaJ3RerH149ZbrU9bX+7H+w33u+z32B++P2V/8f66/Y37'
        '1+zft//s/k/3f7v/+f7f92sOWB3odcDngOJA7oHhB6YdWH5g24GjB84c+ODA3QM/HXh5kD3ocFB+MOZg1kHlwfKD'
        'ww5OPbjs4NqD+w6ePnjz4LcHnx/8/ZDgkMOhPoeCDyUeKjw0+lDjoTWH9h46deiTQ48P/VNtqLZUO6p91Ar1IPVQ'
        '9WT1YvVWdbv6svqe+uc2qs2uzbstsG1AW0HbyLaZbavadredarvR9rjtz8OGh50PRxzOPTzs8NTDyw9vP3z88NXD'
        '9w//2m7W7t0e057dXt0+sX1Re3N7W/ul9i/bn7drjlgdkR2JOJJ3pP7I3CPrjuw/0nnk9pEfjrw+anbU7WjI0eSj'
        'RUfrjjYeXXt039HLR789+s9jhsecj/kdizuWe6zm2ORjS49tO3bs2NVj3xz75Th93O641/Ho4xnHK46PPz7/+Mbj'
        'h45fPP7F8WfHuzssOtw6YjuyO6o7JnYs6tjc0dZxqeOLjgcnnE/kn5hyYvOJ+yfFJzNONp48dfLXky9PmZ6yPeVy'
        'yuOUz6mQU31PJZxKO5V7qubUlFNLT7WcOnrqyqlvTv16mj3teNrndL/TuaeHnZ52esXp5tNtpz84fff0T2fwGdsz'
        'Xmf6nsk8U3lmwplFZ7acaT9z+cy9Mz+fpc/an/U+2/ds1tnqs5POLjnbcvbo2Stnvz774hx1zu6c97mYc9nnhpyb'
        'fG7euZXnNp/bd+7YuQvnbpz7/Nz9c0/PvTj3z3Ncp6DTrNOu07VT1unbGdoZ05ndWd05sXNRZ1Pnxs5Dncc7r3Z+'
        '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'
    ),
}
ROBOTO_LICENSE = 'Copyright 2011 The Roboto Project Authors (https://github.com/googlefonts/roboto-classic)\n\nThis Font Software is licensed under the SIL Open Font License, Version 1.1.\nThis license is copied below, and is also available with a FAQ at:\nhttps://openfontlicense.org\n\n\n-----------------------------------------------------------\nSIL OPEN FONT LICENSE Version 1.1 - 26 February 2007\n-----------------------------------------------------------\n\nPREAMBLE\nThe goals of the Open Font License (OFL) are to stimulate worldwide\ndevelopment of collaborative font projects, to support the font creation\nefforts of academic and linguistic communities, and to provide a free and\nopen framework in which fonts may be shared and improved in partnership\nwith others.\n\nThe OFL allows the licensed fonts to be used, studied, modified and\nredistributed freely as long as they are not sold by themselves. The\nfonts, including any derivative works, can be bundled, embedded, \nredistributed and/or sold with any software provided that any reserved\nnames are not used by derivative works. The fonts and derivatives,\nhowever, cannot be released under any other type of license. The\nrequirement for fonts to remain under this license does not apply\nto any document created using the fonts or their derivatives.\n\nDEFINITIONS\n"Font Software" refers to the set of files released by the Copyright\nHolder(s) under this license and clearly marked as such. This may\ninclude source files, build scripts and documentation.\n\n"Reserved Font Name" refers to any names specified as such after the\ncopyright statement(s).\n\n"Original Version" refers to the collection of Font Software components as\ndistributed by the Copyright Holder(s).\n\n"Modified Version" refers to any derivative made by adding to, deleting,\nor substituting -- in part or in whole -- any of the components of the\nOriginal Version, by changing formats or by porting the Font Software to a\nnew environment.\n\n"Author" refers to any designer, engineer, programmer, technical\nwriter or other person who contributed to the Font Software.\n\nPERMISSION & CONDITIONS\nPermission is hereby granted, free of charge, to any person obtaining\na copy of the Font Software, to use, study, copy, merge, embed, modify,\nredistribute, and sell modified and unmodified copies of the Font\nSoftware, subject to the following conditions:\n\n1) Neither the Font Software nor any of its individual components,\nin Original or Modified Versions, may be sold by itself.\n\n2) Original or Modified Versions of the Font Software may be bundled,\nredistributed and/or sold with any software, provided that each copy\ncontains the above copyright notice and this license. These can be\nincluded either as stand-alone text files, human-readable headers or\nin the appropriate machine-readable metadata fields within text or\nbinary files as long as those fields can be easily viewed by the user.\n\n3) No Modified Version of the Font Software may use the Reserved Font\nName(s) unless explicit written permission is granted by the corresponding\nCopyright Holder. This restriction only applies to the primary font name as\npresented to the users.\n\n4) The name(s) of the Copyright Holder(s) or the Author(s) of the Font\nSoftware shall not be used to promote, endorse or advertise any\nModified Version, except to acknowledge the contribution(s) of the\nCopyright Holder(s) and the Author(s) or with their explicit written\npermission.\n\n5) The Font Software, modified or unmodified, in part or in whole,\nmust be distributed entirely under this license, and must not be\ndistributed under any other license. The requirement for fonts to\nremain under this license does not apply to any document created\nusing the Font Software.\n\nTERMINATION\nThis license becomes null and void if any of the above conditions are\nnot met.\n\nDISCLAIMER\nTHE FONT SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,\nEXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF\nMERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT\nOF COPYRIGHT, PATENT, TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL THE\nCOPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,\nINCLUDING ANY GENERAL, SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL\nDAMAGES, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING\nFROM, OUT OF THE USE OR INABILITY TO USE THE FONT SOFTWARE OR FROM\nOTHER DEALINGS IN THE FONT SOFTWARE.\n'
# END BUNDLED ROBOTO
_FONT_RESOURCES = []


def register_roboto():
    """Register bundled fonts for this process without a system installation."""
    paths = []
    for name, encoded in ROBOTO_FONTS.items():
        data = zlib.decompress(base64.b64decode(encoded))
        digest = hashlib.sha256(data).hexdigest()[:16]
        directory = Path(tempfile.gettempdir()) / ("marby-roboto-" + digest)
        directory.mkdir(mode=0o700, exist_ok=True)
        path = directory / name
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
        paths.append(path)
    if sys.platform == "win32":
        gdi = ctypes.WinDLL("gdi32", use_last_error=True)
        gdi.AddFontResourceExW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
        gdi.AddFontResourceExW.restype = ctypes.c_int
        for path in paths:
            if not gdi.AddFontResourceExW(str(path), 0x10, None):
                raise RuntimeError("Marby could not load its bundled Roboto font.")
        _FONT_RESOURCES.append(gdi)
    elif sys.platform == "darwin":
        core = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        text = ctypes.CDLL("/System/Library/Frameworks/CoreText.framework/CoreText")
        core.CFURLCreateFromFileSystemRepresentation.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                                               ctypes.c_long, ctypes.c_bool]
        core.CFURLCreateFromFileSystemRepresentation.restype = ctypes.c_void_p
        core.CFRelease.argtypes = [ctypes.c_void_p]
        text.CTFontManagerRegisterFontsForURL.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                                        ctypes.c_void_p]
        text.CTFontManagerRegisterFontsForURL.restype = ctypes.c_bool
        for path in paths:
            raw = os.fsencode(path)
            url = core.CFURLCreateFromFileSystemRepresentation(None, raw, len(raw), False)
            registered = text.CTFontManagerRegisterFontsForURL(url, 1, None)
            core.CFRelease(url)
            if not registered:
                raise RuntimeError("Marby could not load its bundled Roboto font.")
        _FONT_RESOURCES.extend((core, text))
    else:
        config = ctypes.CDLL(ctypes.util.find_library("fontconfig") or "libfontconfig.so.1")
        config.FcConfigGetCurrent.restype = ctypes.c_void_p
        config.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        config.FcConfigAppFontAddFile.restype = ctypes.c_int
        config.FcConfigBuildFonts.argtypes = [ctypes.c_void_p]
        config.FcConfigBuildFonts.restype = ctypes.c_int
        current = config.FcConfigGetCurrent()
        for path in paths:
            if not config.FcConfigAppFontAddFile(current, os.fsencode(path)):
                raise RuntimeError("Marby could not load its bundled Roboto font.")
        config.FcConfigBuildFonts(current)
        _FONT_RESOURCES.append(config)
    return paths

# BEGIN EMBEDDED CURRENCY PICTURES
# Official source: Bangko Sentral ng Pilipinas (BSP).
# https://www.bsp.gov.ph/Coins%20and%20Notes/Coins/NGCCS/NGCCoins.png
# https://www.bsp.gov.ph/SitePages/CoinsAndNotes/NewGenerationCurrencyBanknotes.aspx
# These are low-resolution display thumbnails, embedded for offline use.
CURRENCY_PICTURES = {
    "coin_20_84": (
        "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"
    ),
    "coin_20_64": (
        "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"
    ),
    "coin_20_44": (
        "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"
    ),
    "coin_20_32": (
        "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAK1UlEQVR42o2Xa4xd11XHf3vvs8+5j7mvufbM+DGe"
        "cTyOPXk0xHYeTaBSATUSlJAAMzxTlYcaWvGBRygQFKqWgvpSK6FIIV8SVBEhZvpAEc9KbUA0JSRENDaM7cZOYzse"
        "j2fua+7znHvO3osPE0dWlaAsaX/YX9Zae+m/9v//V/w/sbK0ZJZXV921+6/cWTl44vid95Ynq8cLhdKCaF0zWmFt"
        "1B4nyblut/Pyv33zG8//9Yvb33+nHD8Y6h2LryyZ5eVVB+hPP/Ten50/dPDDpUrl3nwhX7HWApogDDEmwBiLCSyC"
        "Ypy67mg4/Pb5tVN/9fDnv/JVwMvKilHLy+7dNqBEBKWUPPLAzR+4/dhtfz41NXVcB4bhaIzS2gdBKBPlqkriEaAR"
        "NCYIpDBRUuK9rlSqRGGOjY2Nl//1n5999NGnnvuGiCilFIBcXyy4/iKgFIhSSn3pYz/2+RsXjz6ijaY/jF1gQ7JM"
        "dLmS14Nej8LUbtJ4gNEaQQhDy65d07z+2nkJwrzf7vWp1XcdX/7wR//l6K3HvqCU+jgg12q83QSuvTx64vd+6m8X"
        "Fw/f39zu+SCwTJQqejQYYJSgbITKVSGcIMqX6PX6DAc9ZnZXqeRDrFHESQY6IF8o+n6vy/zcvP7vl1969r5ff+zn"
        "RSRBKa41cW0CamVlSSul5Inf+eDqTTfd+MGrjVaqdGAVml6nSTgxSZLbQ2InEZNHmYB8WODU+im63TGFRhc/HrI4"
        "N8XhvSWspIj3Op/Pc+7c2fS224/d/49P/smqUuqnRVYUatkDYq4H3Oc+8v4v3X7slg+tbzTSiXLVepehxBHsPko3"
        "v0Aa1dHGYgMN4gkDQ6vZQCuIwohGu8uFq9ucW+9QLE5QnwjY7rQpV2pm8+qV9OiRI4vHD9ar73nfx/9pZWXFrK6u"
        "illZWjLLn1x1j/7MsftO3Hn7463tbjZRrtjRaEixWGBUXuT73YirGxtsbVxmMOiTZY5isYQJDFtbW4zTlMAYRqMh"
        "udAyzhyvX+3ileXWw7Nsd9oUChNm8+pGNn/ohntmo8ELD//RZ19dWVky6k102qf+eOmVmZndR+Ik86lzZvfuSa5k"
        "M5y+kjDoNhkOR8RxTBAEpGnK/Nw8d919N6+88l2SJCGKcmxubrKzoqC1Ih47bluY5q5DFd64dIlave4ia/TVKxtn"
        "P/Abn7pNRNJAKSWf+qW7f27/vumjzU7fGWNMzmq6ajdnNhK2rlxies8epqamGQ5HjMdjxuMxzVaL9fXLhFHE5cvr"
        "BEGACQzeewTBe0Uhbzl5fpNKzjBfr5F5Ma1my+3bt+fo47/74JJS6pkAYN/c/oe9IMVCgXg0QsIKW26S1tYpBDBa"
        "UyqVmJ6ZITABIIjAxYsXcM7z5n7jMocXj0IR2IA4TkDgxbMb7L17llFvi1KlxmDQk7lDCx8BnjG/ds/eIzfduvhp"
        "Lz7oD4Y6FwVI7UY2B4qtjXWU1iTjlGqlQrlcwVqLUoriRJEszWg2m8RJjNKKarVKFEUkSYIA5XKZXBix2domCgP2"
        "lgMaWw0l3qtA65lyfOErwY2Lh3+0WMxFzuN37S7pzHnaqkwudARhiA0se/ftJY5jGo0GhWKRXC4iiRO0MYRRiO94"
        "ZudnSZKEfCGPtRbvPeVyBWM0yhjOXmxwdGqGaq2q0nTsA+Ojo7e85/1BsVQ6obUGbSTQCh/WcDpHr7tOYAylUola"
        "rUar2eL8+fOEUUi1WqPf71Or1chFEUEQ0Gw16XQ61CfrVKoVjDZcWV9HacXs/lmuXLnCMNPsLlm63VTEC5Xq5B06"
        "X8gfEhG00UobTSIBShn6/T42DKlN1nBZhrWWQwsL1CfrIILRGmMMgbVorRkOh1TKFaamp9jaamACgzYGrTTee3Rg"
        "aWwPcVmKKJT3Dq3VQa1gAqVQSoMIoixKaSqVCuKFKAzJ5fPU63UGgwGNZoM4jjl4w0HK5RLOOUSEQr7AzMw0l9+4"
        "vANkEZxzKK0RPCKQOkG8Q7wnTVO0VhP6LUJQgFJorXHeMTU1RalUYjgcUi6VqVQrOOcIggAvwnA4wpgAG1gE2D87"
        "S+Yc5UqZ4kSRdrvD9PQ0lUqFVqsNKJx3eO8QnyHe40XQAn0REL9DUIYd2g7DkPmD8wwGQ0QEay3lchlrQ3K5HNYG"
        "FIsFTBAQWku73SKOY9I0w5iA0WjEdqdDmo7p9XooBYES/JtNKAVZMu7r0XB0XmuF7FAhoUrReHYYS1EsFrlw8SLG"
        "GObn5pibO8Dc3BygKE5M4J0DBcYEpGm2Q7hAFEWkWUaj0aRYLIJ4SjmFc54sdSIijNPsNd3r917yzuNcprwoQhIs"
        "YwRNt7vN7OwsxWKRkydPcfHSJcbjlHanQ61Wo1go4pwjTTOSJKHdbpNmGVmWISI7IA0C4iQlMp5KTpFmnixLlHMZ"
        "nU7rJf2/a68+1x+MEhGvvUdwY8pmyGAwYjQaglIcOHCA2dn9aK0ZDAYkcUyptANAbQwiQqvdxntPr98jSRK63S79"
        "fh+loN3pcqAeEmpP5py4LNODYZKcPrP2nH7mO+tnB/3BCzkbiHOZdx5K0qa5+QYze/YzHA4YDAaEYUilXCaKIprN"
        "Jqf+5xRplqLUNXB5lNZ45xmORqRpSpqmDAYjQgNH9uRI0owsS70NlCRx/MJTz62f1QAXL7zxpFZKxaMhaIN2I6Zt"
        "h063T61apdlssr5+hXic0OsPaLXbbF7dZGtzC200LnNorRC/wwuB2fkDjFbEqeO2A3nKoeBEMRz0CYJAXbxw6clr"
        "MkwppezTj/3Cd6en64sqiFwY5UwutJxphuT23IJPh2xvd/EiJElCkiSk4zG5fJ5+r0er1UJphXh5i5gQzygVFqZC"
        "3nekyCgek2Wp82mi253emYce+/IPiUhqbl5bM6tra9mRevC9+fkDD8VJ7HP5gnZOmClDa7vPkCITxSL5XMS+ffvI"
        "nCOMoh0GdI5+r7fz2xkNCGnmiFPPwnTIDx8uEY9itNHS67R8LorMfz7/4i8/f2bj1ZvX1oxZXVuTlZUl89t/+q1z"
        "x+Yq5YUb5u5ttdtpoThh0ixjVy5lPOrSzyybrS7r65dpNZu02y1CGzIaDknGY6y1jFNHknqsFk4cLHLHwQKjeERg"
        "Q9qNzXRq16Q9efL0Fz/x5W8/sbKyo8TU9aJ0eXlVnnjkga/fdNPC/Y12L61O1i0oImuQIE/HV3h9K2aj2UPQRPkc"
        "jUaD4WBIYBT5wDO/O8/hmYiJUIjHDqWETmMrnZqq29Onzz/70c997cGVlRW1vLwjSt9Olod/+fsP/M3RowsPNre7"
        "vlgsiw1zBhzWaDAhiYQk3iI6oLO9TTLsUytaKgWN1cI4dXg0bpy4fq+jpnbV9Znvnf/6b37mq78oIuPrDYp6O2MC"
        "8IWP3feZI0cW/sBaTTx2LpcvYGykFaIUHqVAKfXW8QKZE5wX8Wnq43hAFFrjRXH2zLnPPvL4P/zhdV5E3pU1+62f"
        "XPzxu+48/mdTU/U7lYI4zVBKe22saK1BaSUiICLee7x3SrzXUWhBaxrNzosvPv/8o3/x96e/+U7W7N2YU/XJD937"
        "wPzBuV/NFwo/ksuFVWsNoBARBPXm6mnSzJGMs84oif/99XOvP/2Jp7/1d4Bcl+vdu2OApaUls3qdtf6Jxdzce+84"
        "cU9td/2EtfYGtK6CBqSTpNlrrUbrv06+8B/f+drp+MI75fjB+D8BiZ2gHVc7ygAAAABJRU5ErkJggg=="
    ),
    "coin_10_84": (
        "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"
    ),
    "coin_10_64": (
        "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"
    ),
    "coin_10_44": (
        "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"
    ),
    "coin_10_32": (
        "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"
        "7px7FMb/Alv0yMggwxAyAAAAAElFTkSuQmCC"
    ),
    "coin_5_84": (
        "iVBORw0KGgoAAAANSUhEUgAAAFQAAABUCAYAAAAcaxDBAAA2KElEQVR42u29aZBk13Xn97v37blWZmVWVXdX71gb"
        "aDSJjZRAsEFxhqKoZTwjNWw5KM1E+IPDYYdnwmE5wnY4mtCMvIwj/MnSTHgsx0zIsoJoS0NSJEFSIgmQQ0EkSIAg"
        "gALQjV6rq2vNfXn7vf5wX2YXQIgSKTI0M+FCJKprf3neuef8z//8z0nB3/ybPHv2rHz22WdzIYTe9/l2peK2j62e"
        "qJdqtUC6rkym03h9fX20u7u7A2wBavbNZ8+etZ944gn11FNPqb/JJyP+pv7uuXPn5Llz53jyySfz2ScPHTp05pFH"
        "Hvk7rVb7w43F5vFmo9kolUqB67qWkJI8z0niOBwOB4Nup7s+GPSfv3Tp0me/8Y1vfAOYAmitxZNPPikvXLig9xv8"
        "30eDvqsRgSM/8zM/85Ejx459fPXQoQ/ce+99VrlawbFsNBqljE2klFpKS9i2jW1bACRJwltvXeLK5SuXtra3fv/F"
        "b3/7s2+88cZ3Zr/46aefti5cuMCFCxcUoP99Mag8e/asfO6557J9nyufPn36ww+cOfMrKysrv3DnXXc32u02Ukqy"
        "LMuVUkJKaYxnWUJKiZASIQSALoysbdtWnudZlmWJ0XDEq6++km9vb31t7bXXnv7KV77yhTiOr72LcfN/Fw0qzp07"
        "J59++mm1Py4eOXLksfc8+OCvHD92/BcPHzl88sjho1i2RZ6rPMsypBTSc12hNUzDkPFkTBTFZFmGEALbtimXS9Rr"
        "NWq1Gp7nkaYpWmvleZ52Xc+SUnDr1i0uvvnm4PqNq5976Tsvfer5559/BhjPruPcuXPWqVOn9E8i3oqfgBG1EGJ+"
        "oYvVxbtPP3T6l++9775fWllZed/xYycolUvkea7SJNUIpOd6QghBGIVsbm3T7/fxgwBLShzXwXVcpJSkaUqeGweL"
        "opBqtcaJ48eo1+tYlk2eZ1oIoTzPx/NcK0szrly5zNWr1y6/+spLf/ytb337Dy9evPhvZtemtZZPPvmk+HGGhB+L"
        "Qc+dO2e94ygdeP9j7/+lE8dO/sqxo8ceO3LsWNBsNslzRZ5lmUZL27alZVlEUUx/0GdzcwshJfVajaWlNo2FBSzL"
        "QgoJUiCFxLLE/JKnkym3trYYDAckccLh1VUOHjxArVYHNHmea9u2le/7wnVdORqNuHTxIpcuXXrhpRdf+tSXvvSF"
        "T8ZxfPkHPIe/EYOK8+fPi+LoiHvvvffD733ovf/psWMnzi4tLbXb7SWkyc5ZluXSti1pWzZREjMcDNja3sGyrOIY"
        "12m1FnEcB5UrcqUQAoSUSCFuvxcSIQWObeO6Lhrodrt0Ol0GgwFZlnHXXXfRbrUol0torclzpRzH0Z7nWY5js7Oz"
        "w7Vr1yavvvrK17/27LO/+/zzz38KyM6fPy+feuop/dfx1r+OQaXWWgsh9L333vu3HnzooU888MCZxw6urmJbFmma"
        "5XmeIaWUjuOILM3oDQb0uj2GoxELjTqLzSYLCwv4nodSan6cpbSQUgLMvdKyLERhUCnNZc+M7LguruOglGLj1i32"
        "9vYYjyeUy2VOHD9Gq9Um8H1ypdA6V47rac/zLbTm2tUrfO1rX3/hc5/91+e/+91XngHg/HnJjxhff1SDygLjWR/+"
        "8If/x0cefd9/c/qB0+S50mmaKSGQruMK0AxHY/r9Pt1+H9/3WFleobFQJwgC8lyhVI5SGikFtu2gtUJKiUZjW/bc"
        "wKCNdwpRJCgLpRS2bc8Na9sOWZays7vL1StX6Pf7eL4PCO66805WDqzQbrUKNJFrrbUKAl84jitfeOGbfPrTn/7n"
        "f/D7v/8bwLjw1h/aqNYP+wPnz5+Xzz33nAIWf+mX/oOnP/YLv/APjh8/oaIoVEop6fu+jONYbG5vcXPjFrt7e9Rq"
        "VRabDTzXwfM89vb22N7eJgojxpMxlrRIkpiNmzfRwGQ8xrJstra2yLKMbreDEIIkjk18VDk7Ozs0Gg12d3dJkoQb"
        "6+vEcYRl2YRhSK/fx7JdVlZWSOKYbrfL9175Hts7u4DA9z1Rq9VkksQiiiJ1/Phx/eCDDz5SLlc+9OfPP//F5557"
        "bnDu3DlrbW1N/yQNKp977jl18ODBwx/72Mc+/7Ff+IUPViqVLAxD6bqeVLni8pUr3NrcQkqLw6urHDm8ymJzkdFw"
        "wObWFnEUk+U54/GYJEm5tbFBu71EliXc2tgkzVOm05Bqtcru7i79fh/HdWkttrhy9QpSSvwgYP3GDaS0mEzGbG5t"
        "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"
    ),
    "coin_5_64": (
        "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAiW0lEQVR42u2baZCl11nff+e8292X3rfZR9KMRtLI"
        "ixa8zcgGAxEmOFYPNlQSTFyhSKCgioIvKTIWISGfqCSVuCiqnGAWQ3oM2IZ4k2VrtBmhkYWsmZY0S0/3zPTet+9+"
        "77udc/Lhfe+dkTGxZEzxJV3qqVHXdPd7nvM8/+f//z/PK/iH+xDz8/Nyfn6eU6dOqcEXy+XygbvuuuvInj17pguF"
        "QgkpZej73dXV1Y0rr7zy6vLa2muDf2uMkSc//nF59tFHFWD+QR7y+/0DT58+LY8dOyZuPTQw8aMPP/xPjx458sjE"
        "5OQDlUq1XCqVcF0XKSVaa/q9Pq1Ws7u7Wzt/6fLlzz3/3HOfeeWVVy4NfsDCwoJ15swZzpw5o7+fwRDfr0MD8tFH"
        "H41v+XLu5MmTD91+5MhH5mbn/sn+/fur5UoVy5IARghhhBBGSoklpZCWJWzbFlJKer0eK8vLwbVrK08tXbnyR5/+"
        "9Ke/BGzc8vtsQD/66KP6HzMAYn5+Xi4sLBghxPBBjh8/fv/xe+/9yb179/747Ozc4fGJCSzLAlBKKbrdruz1+qLv"
        "91FKI6TAsW0KhQKlYtFUyhWTy+e0lNKWlkVjd5crV6/uXFu++oVzLz7/v7/6pa9+DfDTEhEf//jHrUf/HiUivteD"
        "nzlzZpjiU1NTR9994sSPzc3t+cm5ubm3TU9P43kexhgdK2V835etZkt0uh2MgWq1ius4wxJQSqGNptFoYoBqpcz4"
        "2JipVqvadV1s27aMMWxubLC0tHTxyuUrf/6lxx/7s8WXXvrrW0vk1KlTb7o8xPcQsMEvqHzwgx98ZP/BQ49UK5WH"
        "9u7b5+ZyOTCgtY77fl+2Wm3Z7fUQAhzHYWJ8nEKhgCUthBQIIRBSYkkLy5IIIfD9gK3tbfx+HwSMjY0xPTVl8vm8"
        "dhxXOI4twyji8qVLbG5sPHv+5W995hOf+MSngc1BOb6Z0njDAZifn7fSW7cefvjhX37LW9/2SwcOHNiTLxQA0Nqo"
        "KAxEs9WW3V6XMIwoFouUSyWKxQK27WCMRmuNkBIpJJYlkVIAEimTv9u2jet5WFLSbDZZXV2j1W5TLBbYMzfH+Pi4"
        "zufzWkpp245Dp93h/Msvb379a1//L5/85O/+NhDe8qzfnwDc8gOn/9XHPvZ7Dzzw4PsLxSJaaxXHMb1eT9YbDRFF"
        "McYYxsdGyeXy2LaFZVkYA8ZopJTYtj38tVIKpJS4rps8jBBpoAxhGFAqlel02pw/f4Fuv4clLQr5PFPTU+zdu9eM"
        "VKvGdT1t2Zbd7XT44he++Mxv/aff/BfNZnPpjQbBeiMI/4lPfELv2bPn2M989KNfftd7TtxnWVYcRZGo1Xbl6tqa"
        "9INAFAoFpqenCP0+vW6XeqPO1tYW6+vr5HJZmo0ma2trBEGAlJLl5WXCMMJxHDY3N8jmctxYXUVKweraKoHv0263"
        "kVLS6XQpl0pMjI/hZjwuXLhAbacmrl2/IRzHlrlc1ji2q47fe3z/bYdv+9Clixcfe/LJJzfn5+etxcVF8/cJgDx7"
        "9qyuVqt7P/yRjzz+wA/8wIE4CuMoiu3llWsijmPm5maZnJggn8sjpaBWqxFFMblcHiEEuVwey7Lo+32U1kRhiOd5"
        "tNttqtUqURjR6XSH2RAEAVEUMTY2Rr3ewHFser0uaabhOC5CQhCGGK25dv069XpDTE1NSq11fMeRo5Xp2dkP/M2L"
        "3/zsN77xjd3Tp0/Ls2fP/p1BkN8F7QXgfPCffeiP7n/gwb1hEMZBENmXL19hdKTK4YMH8VyXKIpRKiYIAnLZHNVq"
        "BSkFmUyGvfv2EscxrutRLBSYmJig2+0xMjJKoVAkVjGzs7M4jksum2VmZpapqSlqtRqVSplsNotBYNsWxWKROI6I"
        "oxitNKVyiWqlzPXr13nssa/S6XbtbrcTv/eh9+75xV/6pT8F8seOHRP/r1K3vlvdv//97/+37/+RH/k5KWUchqG9"
        "dPUqe/fsoVqtEEZhguQCLMtiZ2cHy7LRWhPHMZlMBsd1wQikJXFdBwHEKsayLKrVCsVikVqtxvj4OFtb21SrFfr9"
        "PrbjYDsOWmsCPyBWMTLtGv1+H8dxcB2HOFYIKfD7fVZWrrFv3z6JMfHBg4dmpZDur/3ar345ZZHmzWSAWFhY0MDY"
        "vW9567/L5/Naa21dv3GD6ekpSsUiURQhxOu/XQhBu9NO0tMYjDFIITDCoLWi1WoRRhFGa4yBnZ0aOzs7yDR4URTR"
        "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"
        "SUVORK5CYII="
    ),
    "coin_5_44": (
        "iVBORw0KGgoAAAANSUhEUgAAACwAAAAsCAYAAAAehFoBAAASgklEQVR42q1Za2wc13k99955z75I7i5FcrmkRD1s"
        "UY5lqwnit120NZK4SVN7JSNwkQQGihgG0kfyI0iB0gKKAkGQAPlRN0jTBE5TuyWNGEnhIKkdyYzlh5LYgmWJkmy9"
        "RXK55C73Pc879/bHDGnGcAM77QCz5M7O45vvnnvO+b5L8HtsMzMzFAA9fPgw33I4/9BDD/3Rtm2jN+dy2TxhCnV6"
        "nfV6s3ny+Z///BcXLly4tnHi0aNHlRdeeEEcPnxYfNBnkw9y7uzsLK1UKoIQIpNj7L777rv9+unpQ6Mjo58cGR0d"
        "S6fTUBQFlDIwShCEIVZrtUZ1pfrzs+fOPfX97373CAAHAKSU5LHHHmMA3nfw5P0GevDgwWjjwP6PfGTvbR/+8ANj"
        "4+UHRkZGbigUCgiCEK1WS3ieK3kUgRAKw9CRTqXI8PAwzWaz6HQ6uHLlyuVrV6/86FfHjz/1k5/85Dcb95RSMkKI"
        "ACB/74BnZmboxpsXbXv4vkOHPjk6WjpU3DZ85+jomCqlRKvdkk7fiYIwYCk7RTKZNFRVBWMMAOC4LhzHkZqmiUKh"
        "QMZL41TXNSxeu4bFpaVXrly68h8/+MH3n9mAzNZnfqCAt1yYeuSRR/9+1+5dn982MpJXVRXdbg/dXpeHQUhNy6Sp"
        "VAq2ZUNVFQAApQyUEjDGoKoaCAHCMES93kCz1RSDAwNicnK7MjI6gohzXLp4qf3GGye+9+UvfekwgHalUmFzc3PR"
        "+w54I9jp6empP/v0n8/eeOP+m/3AR71ejzw/AAAKSGKZJgghSKfT8H0fiqJAURQIIWBZNhSFQUoJSimEELBtGwtn"
        "zsD3fRi6AcM0xNTUlNg+uV2xLAvHjr14+jvf/uf7jx49eu5/yzR7r2Afe+wxOTc3V77/gYPz+2+6+braai2sVleo"
        "YRq0kB+iKTtFGo06giBEr9cDAKyvr8N1Xfi+D9/3EYYhXNdBGHJ0Ox0EYQjXcSClhKooMAwDK7UaWVpcokvLS9I0"
        "TX7gwIFtI2Njn6pVq8888cQTzZmZGTo/P/9bmFbenfGF6WlCCMHffunLP7xx//7ytWtXQ8dx1fHxEhRFhZQSvV4X"
        "mUwGnHPkcsPgnIMQAk3T4boOisUiOI/ijKsKdH0QzfV1WLYFx3UgpIQQAowxZDIZ+J5Hjhw5orquw2/56C3jrc99"
        "bm5+fv726elpnqBAvmeGZ2dn2eGDB6NKpfLQHXfe9dftdoe32x11vDwOKQEhIlBK0Gq14PsBpJSwLBuUMYRBACHi"
        "Sa6qGiAlhBRw+n3YKRuQgKIo6Pf7iCKBKIrg+0FCgRSu52FxcYkO5YfCPbuvG09l0u2/+uIXX5qdnWVzc3ObAdOt"
        "2a1UKnIISE/v+9A/6Lou6406LRaLkNE7bEMIBWUMhUIeumGA8xBhGEJVNeTzeYRhBMYo/DBAq9mCoqpo1BsIOUen"
        "0wEAaFo8UoCEhEQkJFRFBSHAiRMnGGVUHLjp5q/s37+/UKlU5NY4lS3YZYQQ/vmHH/7Knuv2lFdWViLDMJmua8mQ"
        "U2iaGmdWSPR6PXTabbREnK2BgQFwbqNYLGJgcBCpMITnehgcHIxxTgBGGa5cuQxVVWGZFtrtNngYAiAQIoKqqlip"
        "rtCzZ87yG268cejQgw8+Rgh5NOHodyCRTDTx3HPPTd1x511PWJbFVlfX6HCxQISQUFUVmqZhaWkZp948iUajjlqt"
        "Btd14XkewjDE2uoqarUaPN+D73nIZDJIpzOIIg7DtGBbFiSA1VoN3W4PnufFgoEYKmEYQsoYse1Wm5TGSjKVSt3k"
        "e+6PDx06tFKpVNjCwoKkADAdTzR584EDX5uYmLCq1RWZyaSJoihgjKHRaOCtt97C8vIyPD9AGEVIpTNIZTLQdANS"
        "AulsFnY6Dc45rl69itdeex2O4wCExLDhHFEUIYoEpJQIeQixEWGMNZCEu/tOn5w5c0aWJybUW2+/4xsAUKlU4gxX"
        "KhV2+PDh6N577737lltv+5oQImp3Omy4WEQUCZw7dxaXL11CFAkoigI7ZSObycaZUVUEQQApBDRVhapqYIoCP+SI"
        "hMBEuQxKKAgAQik452g1WwjCAJTQhKMJgiBAGHJEIgLnHJAS7XaLDg4ORtu2bdupKsqbX/3qVxdmZ2cZ3bt3rwSg"
        "3Hjj/m8MDw+jVlvF4MAgmKKgWl3G0tISDMuCojB4ngdDN7B9+yQmymXkMhkM5rIolUowTBNIcDY2OoKx0RF0Om0Q"
        "QiCEhEx2QEIKEU+2xHOMjo1hcvskyuUypqZ2YnSshG63izNnzpBMJiv3H/iDrwOwKpWKZPPz8/LBBx/8i4/eetsj"
        "zVYr4jxiA4MDkFJiaWkJYRgi8AMoqgLTNJHJZmDoBhhj0HUd6XQK6UwGw8UiBgcHYNs2CoUCpJSora4iP5QHCEAI"
        "AeccjUYDgR+AMgrP81AcLmJ67zRMy0Q2m0Uum4WmaajX6+h0OsSyrWj75OTQ0GC+fe+9f/KSAkDdPrXrb0zTlItL"
        "yygWCjGpJ0MIAKZpQNM0+EEAHsYioSgKNF0DowxCxiKgEAJKGQgIDN2AlBLNVhNDQ0MQQsRZlhKRENApgxACmUwW"
        "KysrOL1wGpQQOI4L0zJBKAERFJcuXqKFfEFOTu34AoDH6T333POhYrGwr9lsElVRmK5rydABpmnFAVAKQuKMMEWB"
        "lHJj9CGkAAGBlPGQb6iYqqnQdQOe6wESyW/xhBNCIAgDqKqKVMrG6uoqer0++ol0CyHAOQdjFOvNJq2uVJHP53d8"
        "5jOfuYWOlkq3ZrNZ5npeZFlWTOgEoJQi/i7AKIPreRBSgFKyiT1FUaCpGnRdh6qqEDKefLGYSjBKYwzL+EWklBCR"
        "gBQCvu8jncnAMAwUi0Xs378fk5PbQSiB7wUghCSsEmF9fV2kU2kM5vN3KLlMblxVNYRBCDNjIokXAIGRQKHv9KFp"
        "OmzLRi6bRch54il66HZ7CW3F4hEGAZZXajB0Dd1OB7t27UoMepJdKWIKA6CqSpLdHtLpNCYmykilUjizsAAhYgZR"
        "FQXdTheEUqTS6bKiGRrbyNo7lEgSfGVACAEhsTLmcllksln0uj0IKbHebGFpaQm2ZYEyhpRlwQ8CeK4LHnhIp9PI"
        "ZmPxAMgm1Cglmw6vWl2JPQpjyA8O4YYP3YB8IY/qchWGYSDgAXzfT1yeptJut9+Iogiapm3BZoxJTdMwlM9DURRI"
        "ACk7BcYYTMuC7/tYb6yDhwEy6TR2Te3A2toaGKMojY0glxvA8HAxvjaBAwBwzhGGyQvI2FcoigJKKNrtNlZrqygW"
        "hxElOA6DEIZhIIo4er3eutJsrJ11XReqqtAwCGGZMW4JIYCUcBwHNDHppmmChxz9Xg+e66I0NgKQUZimCS/xwL1e"
        "D/l8AaVSCf2+g263i2w2BykEhJSb2GSMbfoHxhikBDgPwTmHaZqbZktICcuy4Hke2p3WWbq4uHjG6Tu+punEDwK5"
        "YTIIAYSMSxvbtqEbOggl6Dt92LYNy469QTqVhmVZAABVVTFcHEZzfT2xkwyO44CQ+PFSSiiKCh7FDKDrBtyERYQQ"
        "oExBOpNBq92GlECY0Kqm66zT6ci1RuMNevz48aVer7tm2VasQgkshJTQNQ2lsTGomgohBNKp2Cv0nT7GRsdQHi+D"
        "UIow5KjVasgNDKDZamGlVoMENk08IWQTEkJE0DUde667DtPT0ygUCtB0HdlsFnv37gWlBNXqMnRdT2pCRabTabSa"
        "7fZLv/rVZQVAx/f9y6qilnjIhRARIwkdRUJgKJ9Hvd5APp8HYwy5XA5hyOFt1HBqjD/GYnMehhzF4SJoIjzpdCYx"
        "9glvC4kwDHH50iWUyxPYvXs3IiFAADhOH6dOnYbrOAl9ChBKpaZrRAh+ZX1xcUUBAMdxz1BGb1cURfJIQGMszooQ"
        "ME0LxWIRvh9gZWUF4+VxZDLZTQiYpolOp4Nt24YBCdi2jV6vC8/zoBs6dF3fDFgIAUpjX93tdnHy5BtIpzMwDD2u"
        "D7td8EjExWti723bFowy6vnhOQCRAgCtZvPtMIxnoxARCLQt9BahND4Oz/Nw6eJF1Ot1TJQngESehYgn6NpaHfVG"
        "A7Zlo9/vIzeQw44d25NMv5PhDVnfqA8dx4FIhIQqDGnLAqUUQRjEE9AwIKREbaV6YbPicN3+ad/3IaSgnuvFCifk"
        "lmEUGBwcACE7cPLkmyiNleI6LgzBIx7f2LJRoBSMMdipFAxDg8KUTZO+8ckTX6xpOggA0zQhEynXVBXtdgeMUaRS"
        "KXiuC8uyiOe68F3vjc2a7uzZs28119cjwzApjyK5cXu5mRXA9wMYhoGxsVG89vrraLVaIISAUopisYh903sxPDyM"
        "TCaLsbExpFPphLoEICWkjFlCQoIQCt/z4Hhuon4SClMQBAEsy4JhmnAcF0JImKZJO502rq0snd8M+MSJE4tO31m0"
        "LBNRFMkN3xqzRjxRGGNoNltQFAVTU1O4cOEC3j5/HozGeA95iJRtI2WZcJ3eZumz4SGQ/KWEIgzDWBhCHo8S53Ac"
        "B47jAkjMURCAUiotyyKddqf95uuvXwEAOjs7ywB46631X+qaDkgpXNeNK4LEDsa7QBgGuHr1GkzDwL59+zA4MICr"
        "V6/ijZMncfHCRbTabazWG3j7/EWYhoFIiE0PsbGTxBvHmY5FxA9i0aGMod93ECQthGwmIwzTkq1269fVarUupaQM"
        "AF1YWJAD2Xx1rDT6cDqTwXqjQTLZLJGJMlFKoaoKms1WbB1VFbphwDRNDA0NQUqJdruNXq8HRdWQy2YxMDgAnhSW"
        "MmGJkHOsrdYRiQgRj9WORxHUZCQAJKoX/79z924RBAE7/urxv1s4feoUAEbn5uai2dlZ9rOf/derb587+2Qul2O6"
        "YfDV1RpocnEQBFhcXES328XExASWlpcRBAEcx0Gn00Eul8POnTtx8003YbiQR7fTTriUIoqiBBYxhhljIKCbFcjG"
        "OZRSyKRlEPIQ4+Uyz+VyysLphVeenn1qLum1cQoAp0+fljMzM/T555/78sLpU4vj4+MqpYxfu3YVy8vLWFy8Btf1"
        "QCmFruswDAPVahUSgB8EaKyvo9vt4vz5t3Hu3DkMDeVx6fJlOK672XYVm9AQMXUm6rfh3Egi3WEYYqI8EZXHy8q5"
        "c291j7360sMAot9qVc3Pz8u7776bPP30010CeSSTHbhvx9T2XBRFXApBc7kcMpks6o0GaIK7bDaLbq8H27JgGibW"
        "1tbg+z6yuRzWW63YOPX78FwXqqaBMQWch6g3GpBCgJCNzDKomgbXcaFqCnbu2hWVxsvswsXz67888sKn5488/5ut"
        "nczN3tr8/LysVCrs2WefrV68sPSj4vDQbdu37xinlHLHcWgYhiCEQNd1LC0vI2Xb8HwfruvCdR2s1evIFwpYqzeg"
        "KAy2aSKby8F1XXQ7nU2V67Q78AMfhBJgS1VhmAZ2797DC4Vh5fSpNy888+NnPn5s/ujxSqXCHn/8cfGezcCFhQVZ"
        "qVTYyy/PN1+cn39qYnJiT6k8sU/TtKjT6ZAw5KRYLCZ9hHDTgnLOIYQEoQS2bcF3PdRWVyGFAI8iBEEYV8thACEi"
        "eF4ML0opwiBAKp3G9dfv5bZtK6+99utj3/rmP3382uW3L9x1113KT3/60+h39ocXFhZk0pf1X3nppdnituHUyMjo"
        "7elMGkIIefHiRWJZFnIDA+j1HQS+Dx4J8IjDdVw4rot+v4fA91Gvr8F1XHS6HUSRQDqdAY8iCBFt4rVYLMrde64X"
        "gFReefnlJ7/1za8/EIZOq1KpsHcH+54Bb8ADAJFS0j/9xCf+O5sbWCsUCh8rFIuUh2FUrVZpY72JUqmETFJIGrqO"
        "y5cvo9/vg8ZkCyklTMuCaVpxA9C2Efg+ev0eOOcolcbF1M6dpNvt0GMvvviP3/32448C4DMzM3QrDD7IKhI5evQo"
        "u+eee/ihQ4c+9uGP3vrvE5OTAyvVlbDVbjHLsqiqqlAVFRJxUboRbKvdhqZqMEwDUSRBWQyBWrWKKOJycsdUNLxt"
        "RFm8dpUff/WVL8w9+cN/nZ2dZQcPHvydK0nkfS4kKocPH+Z33nnnDX/4x/c+tee666YhJRrxMkEUd9+1mGMJAQiF"
        "67pQWMwAG41AISQsy6LZXI5QxvDW2bPLvzz2wmd/8eyzzyfPiP5Py15bty0rO6m/fOTRR8vlic8ODg5en0qnYtLH"
        "VrcUN77jsggxIyDusfWdPpqNxrXLV67M/cv3vvN1OM7KRkL+v1dC372Gpn/q/vtvLxZHDmSymQFKKX3vqygIIVII"
        "gU6322qvN07955P/9hKA5rsS8b62/wHpP1tAgcMX1gAAAABJRU5ErkJggg=="
    ),
    "coin_5_32": (
        "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"
        "Et/H2iN9hOkAAAAASUVORK5CYII="
    ),
    "coin_1_84": (
        "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"
        "TkSuQmCC"
    ),
    "coin_1_64": (
        "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"
    ),
    "coin_1_44": (
        "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"
    ),
    "coin_1_32": (
        "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"
        "0xTdbg/1RgNKjb1CSmEwGGA4GKKctGmlNYTH7gcR0izD1tYWer0eBoMBvPdIRyNkaYrBYCCkiLIsu/rcs8/+VK2u"
        "rq4PhoN/rcSx5HkeFBGMMWhvbUEphc3NTbzxxhtgZlSrVdxx5AgOHTqEO+64Y1InCIpoDL5tt4cApdR1UOd5DhZB"
        "HMcYjYbB2UgGg/6/rK6uvq0A4NLFNx7zwVOWZqSNwdWNq0jTFMlUgn379iHPc1y4cAFra2t48623EELA+sYG3nzz"
        "LSSNxjimEw+wCLTWqNfH84IignMOURShPxhAa0NFWdDPL/z3VwHALC0tqZWVladvuXX/v83v3fextYsXg7FGz8zM"
        "AgCyLMOePXvAwmhvtXHp0qWJ6w2mphK0Ox3EUQQXRYAPYGZElSoIAlIW1jmICBQpiEiI41hfWlv73te/9rUfi4gy"
        "586dIwB8/rVXPz0zM7saxTE16nXJ85ycsyAirK2tYXp6Gs1mE3GlAgDo9Xrj3mAMhqMRhqMRqtXqJBMYAF0vQESE"
        "vMwlhIBur5c/v/rcAyJCy8vL0OfOnZNWq6UfeuihK7+wsH94++0Hj2d57gHooignc55Fv99HlucoigIhBGRZBmst"
        "AMDasZV5nsMHD+cigIAxJhWYWUajka/XG+aFF5//sye++c2njh49qk+ePMlqwnjC0tKSeewrX3nkpbMvPpY06jaE"
        "UAKQwWAIbQxcFMF7PyYNMq6bxlqACMwBURSjWqvBuWg8hikFpRTKspThcBiazWn78stn/+bx06cfXVpaMttsSW+P"
        "x88884y0Wi196oEHnjywcNvO+b17P8TCFEIIIqKqlQqGwyHKskSWFyiKAoTJlFSUkyGEQQC6vR7KsgAE3geva7W6"
        "evnls4888td/9eetVkufPHmSb0RMtmdE/tP777//9oOHH55qNiu9bleYOdRqNb3VblO324U1BswCpTWMNXDWQWmN"
        "KHJy7drbwTmnb56fp06nM3jt1VcffPz0lx6fDMDvomj0frzw+PHjxz78sd/8/M6dO3+nWq2iLEtstdvI0izMzc2h"
        "9B5pmsIagyiKUXqvtdGo1RtIRyNsbl799tNPf+8vfvT97796I5J6I3L6Lla7uPgHHz149Mg9U0njt5xzt0RxvA2u"
        "MdhAEBmX3CL4C71O77vnXzv7d60nnvjp/8WQ6f3o+dLSklpeXsaE2QJAcuJP7v+luBL9ioJaiONoBkTIyuLtEMLP"
        "s2H6H3/71dMvAOhPKJhaXl7GysoK30jG/wDIM/cCurQi7gAAAABJRU5ErkJggg=="
    ),
    "note_50_146": (
        "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"
        "2QAAAABJRU5ErkJggg=="
    ),
    "note_50_96": (
        "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"
        "RK5CYII="
    ),
    "note_100_146": (
        "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"
        "i8f/D9Id2+Sr1Y2mAAAAAElFTkSuQmCC"
    ),
    "note_100_96": (
        "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"
        "RU5ErkJggg=="
    ),
}
# END EMBEDDED CURRENCY PICTURES


def font(px, bold=False):
    return (FONT_FAMILY, -max(16, px), "bold" if bold else "normal")


def money(value):
    return f"{CURRENCY}{value:,}"


def _positive_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def plan_single(amount, coin):
    """Return an exact payout without rounding away the customer's money."""
    if not _positive_integer(amount) or not _positive_integer(coin):
        raise ValueError("Amount and denomination must be positive whole pesos.")
    if coin not in COINS or amount % coin:
        raise ValueError("This denomination cannot return the exact amount.")
    return {coin: amount // coin}


def plan_mixed(amount):
    if not _positive_integer(amount):
        raise ValueError("Amount must be positive whole pesos.")
    plan = {}
    left = amount
    for coin, percent in MIX_SHARES.items():
        count = (amount * percent // 100) // coin
        if count:
            plan[coin] = count
            left -= count * coin
    if left:
        plan[1] = left
    if len(plan) < 2:
        # Small totals need a deliberate mix: PHP 10 can be one PHP 5
        # plus five PHP 1 coins, rather than another all-PHP-1 preset.
        plan = {}
        left = amount
        for coin in COINS:
            if 1 < coin < amount and left > coin:
                plan[coin] = 1
                left -= coin
        if left:
            plan[1] = left
    return plan


def valid_plan(amount, plan):
    return (
        _positive_integer(amount)
        and isinstance(plan, dict)
        and bool(plan)
        and all(_positive_integer(c) and c in COINS
                and _positive_integer(n) for c, n in plan.items())
        and sum(c * n for c, n in plan.items()) == amount
    )


def describe(plan):
    return " + ".join(
        f"{n} × {money(c)}" for c, n in sorted(plan.items(), reverse=True)
    )


@dataclass
class PayoutOption:
    title: str
    detail: str
    plan: dict


@dataclass
class CoinCombination:
    """An editable payout whose selected value can never exceed its budget."""
    amount: int = 0
    counts: Counter = field(default_factory=Counter)

    @property
    def plan(self):
        return {coin: count for coin, count in self.counts.items() if count}

    @property
    def total(self):
        return sum(coin * count for coin, count in self.counts.items())

    @property
    def remaining(self):
        return self.amount - self.total

    @property
    def ready(self):
        return valid_plan(self.amount, self.plan)

    def set_amount(self, amount):
        if (not _positive_integer(amount) or amount not in EXCHANGE_AMOUNTS
                or amount < self.total):
            raise ValueError("The combination must fit the inserted amount.")
        self.amount = amount

    def adjust(self, coin, delta):
        if (not _positive_integer(coin) or coin not in COINS
                or not isinstance(delta, int) or isinstance(delta, bool)
                or delta not in (-1, 1) or self.amount not in EXCHANGE_AMOUNTS):
            return False
        count = self.counts.get(coin, 0) + delta
        if count < 0 or self.total + coin * delta > self.amount:
            return False
        if count:
            self.counts[coin] = count
        else:
            self.counts.pop(coin, None)
        return True

    def clear(self):
        self.counts.clear()

    def fill_remaining(self):
        if self.remaining <= 0:
            return False
        self.counts[1] += self.remaining
        return True


def payout_options(amount, inserted_coins=None):
    """Offer exact, distinct, coin-only payouts that change the input."""
    if not _positive_integer(amount) or amount not in EXCHANGE_AMOUNTS:
        return []
    options = []
    seen = set()
    deposited = dict(inserted_coins or {})

    def add(title, plan, kind=""):
        key = tuple(sorted(plan.items()))
        if key in seen or (deposited and plan == deposited):
            return
        seen.add(key)
        count = sum(plan.values())
        detail = f"{count} coin{'s' if count != 1 else ''}"
        options.append(PayoutOption(title, detail, plan))

    for coin in COINS:
        if amount % coin:
            continue
        kind = ""
        if deposited:
            if coin > max(deposited):
                kind = "Larger coins"
            elif coin < min(deposited):
                kind = "Smaller coins"
        add(f"{money(coin)} coins", plan_single(amount, coin), kind)
    # PHP 50 can use two PHP 20 coins plus one PHP 10 coin. A remainder
    # must be returned rather than discarded or hidden behind rounding.
    remaining = amount
    fewest = {}
    for coin in COINS:
        count, remaining = divmod(remaining, coin)
        if count:
            fewest[coin] = count
    add("Fewest coins", fewest, "Mixed values")
    add("Mixed coins", plan_mixed(amount), "Mixed values")
    return options


@dataclass
class ExchangeSession:
    source: str = ""
    amount: int = 0
    inserted_coins: Counter = field(default_factory=Counter)

    @property
    def ready(self):
        return self.amount in EXCHANGE_AMOUNTS

    def begin(self, source):
        if self.amount:
            raise ValueError("Finish the current exchange first.")
        if source not in ("bill", "coin"):
            raise ValueError("Select a bill or coin exchange.")
        self.source = source
        self.inserted_coins.clear()

    def accept_bill(self, value):
        if self.source != "bill" or not _positive_integer(value) or value not in BILLS:
            raise ValueError("Accepted notes are PHP 50 and 100.")
        if self.amount:
            raise ValueError("Only one note is accepted per exchange.")
        self.amount = value

    def accept_coin(self, value):
        if self.source != "coin" or not _positive_integer(value) or value not in COINS:
            raise ValueError("Accepted coins are PHP 1, 5, 10 and 20.")
        if self.amount + value > MAX_CREDIT:
            raise ValueError("The maximum exchange total is PHP 100.")
        self.amount += value
        self.inserted_coins[value] += 1

    def options(self):
        deposited = self.inserted_coins if self.source == "coin" else None
        return payout_options(self.amount, deposited)

    def reset(self):
        self.source = ""
        self.amount = 0
        self.inserted_coins.clear()


class App:
    def __init__(self, root):
        self.root = root
        self.session = ExchangeSession()
        self.preferred_coin = None
        self.screen = "idle"
        self.options = []
        self.selected = 0
        self.custom = CoinCombination()
        self.pending_plan = {}
        self.review_origin = "choose"
        self.plan = {}
        self.total_coins = 0
        self.dropped = 0
        self.dispensed_value = 0
        self.coin_queue = []
        self.completed_amount = 0
        self.completed_plan = {}
        self.done_deadline = 0.0
        self.taps = []
        self.actions = []
        self.focus_index = -1
        self.focus_ring = None
        self.hover_index = -1
        self.keyboard_focus = False
        self.done_timer_item = None
        self.tick_job = None
        self.drop_job = None
        self.done_job = None
        self.closed = False

        root.title(f"{SYSTEM_NAME} | Coin changer")
        root.configure(bg=BG)
        root.minsize(WIDTH, HEIGHT)
        if FULLSCREEN:
            root.attributes("-fullscreen", True)
            root.config(cursor="none")
        else:
            root.geometry(f"{WIDTH}x{HEIGHT}")
        root.protocol("WM_DELETE_WINDOW", self.close)
        if ALLOW_ESCAPE:
            root.bind("<Escape>", lambda event: self.close())

        # Keep every PhotoImage alive for the lifetime of the application.
        self.currency_images = {
            key: tk.PhotoImage(master=root, data=data, format="png")
            for key, data in CURRENCY_PICTURES.items()
        }

        self.canvas = tk.Canvas(
            root, width=WIDTH, height=HEIGHT, bg=BG,
            bd=0, highlightthickness=0, takefocus=True,
        )
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Leave>", lambda event: self.clear_hover())
        root.bind("<Tab>", lambda event: self.move_focus(1))
        root.bind("<Shift-Tab>", lambda event: self.move_focus(-1))
        root.bind("<ISO_Left_Tab>", lambda event: self.move_focus(-1))
        root.bind("<Return>", self.activate_focus)
        root.bind("<space>", self.activate_focus)
        self.show("idle")
        self.tick()

    @property
    def amount(self):
        return self.session.amount

    def text(self, x, y, text, size=16, bold=False, color=TEXT,
             anchor="nw", width=None):
        options = dict(
            text=text, font=font(size, bold), fill=color,
            anchor=anchor, justify="left" if anchor in ("nw", "w", "sw") else "center",
        )
        if width is not None:
            options["width"] = width
        return self.canvas.create_text(x, y, **options)

    def rounded(self, x1, y1, x2, y2, fill=SURFACE, outline="", radius=14,
                line_width=1):
        r = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        return self.canvas.create_polygon(
            points, smooth=True, splinesteps=24, fill=fill,
            outline=outline, width=line_width,
        )

    def coin_icon(self, x, y, value="₱", radius=19):
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                                fill=TINT, outline="")
        self.canvas.create_oval(x - radius + 5, y - radius + 5,
                                x + radius - 5, y + radius - 5,
                                outline=ACCENT, width=1.5)
        self.text(x, y, value, 18, True, ACCENT, "center")

    def check_icon(self, x, y, radius=11):
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                                fill=ACCENT, outline="")
        self.canvas.create_line(x - 5, y, x - 1, y + 4, x + 6, y - 4,
                                fill=SURFACE, width=2.5,
                                capstyle="round", joinstyle="round")

    def currency_picture(self, kind, value, x, y, size):
        return self.canvas.create_image(
            x, y, image=self.currency_images[f"{kind}_{value}_{size}"],
            anchor="center",
        )

    def payout_pictures(self, plan, x, y, size=32, gap=27):
        coins = sorted(plan, reverse=True)
        for i, coin in enumerate(coins):
            self.currency_picture("coin", coin, x + (i - (len(coins) - 1) / 2) * gap,
                                  y, size)

    def action(self, rect, command, shape, outline="", line_width=1):
        self.actions.append(dict(
            rect=rect, command=command, shape=shape,
            outline=outline, line_width=line_width,
        ))

    def button(self, rect, title, command, primary=True, enabled=True, size=16):
        x1, y1, x2, y2 = rect
        fill = (CTA if primary else SURFACE) if enabled else DISABLED
        foreground = (SURFACE if primary else TEXT) if enabled else MUTED
        outline = "" if primary or not enabled else BORDER
        shape = self.rounded(*rect, fill=fill, outline=outline, radius=10)
        self.text((x1 + x2) / 2, (y1 + y2) / 2, title,
                  size, True, foreground, "center")
        if enabled:
            self.action(rect, command, shape, outline)

    def common(self):
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=BG, outline="")
        self.rounded(28, 26, 60, 58, fill="", outline=BRAND, radius=5, line_width=2)
        self.text(44, 42, "₱", 23, True, BRAND, "center")
        self.text(76, 23, SYSTEM_NAME, 32, True, BRAND)
        can_go_back = self.screen in ("deposit", "choose", "custom", "review", "admin")
        if can_go_back:
            shape = self.rounded(656, 18, 772, 62, fill=HEADER,
                                 outline=DIVIDER, radius=7)
            self.text(714, 40, "‹ Back", 16, color=LIGHT, anchor="center")
            self.action((656, 18, 772, 62), self.go_back, shape, DIVIDER)
        self.text(28, 464, "Demo", 14, color=SOFT, anchor="w")
        self.text(772, 464, "Coins only", 16, color=SOFT, anchor="e")

    def steps(self, current):
        titles = ("Insert money", "Choose coins", "Review", "Collect")
        self.text(28, 106, f"{current + 1} / 4   {titles[current]}", 16,
                  color=SOFT, anchor="w")

    def show(self, screen):
        if self.closed:
            return
        same_screen = screen == self.screen
        focused_rect = (self.actions[self.focus_index]["rect"]
                        if self.keyboard_focus and 0 <= self.focus_index < len(self.actions)
                        else None)
        self.screen = screen
        self.canvas.delete("all")
        self.canvas.configure(cursor="none" if FULLSCREEN else "")
        self.actions = []
        self.focus_index = -1
        self.focus_ring = None
        self.hover_index = -1
        self.done_timer_item = None
        self.common()
        builders = {
            "idle": self.build_idle, "deposit": self.build_deposit,
            "choose": self.build_choose, "custom": self.build_custom,
            "review": self.build_review, "dispensing": self.build_dispensing,
            "done": self.build_done, "admin": self.build_admin,
        }
        builders[screen]()
        if self.keyboard_focus and self.actions:
            self.focus_index = (next((i for i, action in enumerate(self.actions)
                                     if action["rect"] == focused_rect), -1)
                                if same_screen else 0)
            self.draw_focus()

    def build_idle(self):
        if self.amount:
            self.build_resume()
            return
        self.text(28, 81, "What are you exchanging?", 28, color=TEXT)
        for rect, title, description, mode, coin in [
            ((28, 132, 394, 244), "Change bills", "₱50 or ₱100 to coins", "bill", None),
            ((406, 132, 772, 244), "Change ₱20 coin", "Get smaller coins", "coin", 20),
            ((28, 258, 394, 370), "Change ₱10 coin", "Get ₱5 or ₱1 coins", "coin", 10),
            ((406, 258, 772, 370), "Change ₱5 coin", "Get five ₱1 coins", "coin", 5),
        ]:
            x1, y1, x2, y2 = rect
            middle = (y1 + y2) / 2
            shape = self.rounded(*rect, outline=BORDER, radius=12)
            if mode == "bill":
                self.currency_picture("note", 50, x1 + 56, middle - 10, 96)
                self.currency_picture("note", 100, x1 + 65, middle + 10, 96)
            else:
                self.currency_picture("coin", coin, x1 + 59, middle, 84)
            self.text(x1 + 122, y1 + 26, title, 22, True)
            self.text(x1 + 122, y1 + 66, description, 18, color=MUTED)
            self.action(rect, lambda m=mode, c=coin: self.begin(m, c), shape, BORDER)
        self.button((28, 390, 772, 438), "Combine small coins into larger coins",
                    lambda: self.begin("coin"), primary=False, size=20)

    def accepted_totals(self):
        self.text(28, 412, "Exchange amounts: ₱5 · ₱10 · ₱20 · ₱50 · ₱100",
                  12, color=SOFT, anchor="w")

    def build_resume(self):
        self.text(28, 101, "Continue your exchange", 29, color=LIGHT)
        self.text(28, 145, "Your inserted money is saved. Continue where you left off.",
                  14, color=SOFT)
        self.rounded(28, 191, 772, 374, outline=BORDER)
        self.text(50, 215, "YOUR INSERTED AMOUNT", 11, True, MUTED)
        self.text(47, 243, money(self.amount), 54, True)
        caption = "Coin exchange" if self.session.source == "coin" else "Bill exchange"
        self.text(50, 331, caption, 14, color=MUTED)
        self.button((441, 279, 746, 339), "Continue exchange",
                    lambda: self.begin(self.session.source), size=19)
        self.accepted_totals()

    def begin(self, mode, coin=None):
        if self.screen != "idle":
            return
        if coin is not None and coin not in (5, 10, 20):
            return
        if self.amount:
            if mode == self.session.source:
                self.show("deposit")
            return
        self.session.begin(mode)
        self.preferred_coin = coin if mode == "coin" else None
        self.custom = CoinCombination()
        self.pending_plan = {}
        self.options = []
        self.selected = 0
        self.show("deposit")

    def build_deposit(self):
        self.steps(0)
        is_coin = self.session.source == "coin"
        title = (f"Insert a {money(self.preferred_coin)} coin" if is_coin and self.preferred_coin
                 else "Insert coins" if is_coin else "Insert a bill")
        self.text(28, 135, title, 28, color=LIGHT)
        self.text(28, 177, "Tap the picture to insert money.", 18, color=SOFT)
        self.text(570, 152, "Your credit", 18, color=SOFT)
        self.text(567, 184, money(self.amount), 44, True, TEXT)
        count = sum(self.session.inserted_coins.values())
        caption = (f"{count} coin{'s' if count != 1 else ''} inserted" if is_coin
                   else "Note accepted" if self.amount else "Waiting for a note")
        self.text(570, 245, caption, 16, color=HEADER_MUTED)
        if self.session.ready:
            hint = "Ready to choose\nyour coins."
            colour = LIGHT
        else:
            target = next(v for v in EXCHANGE_AMOUNTS if v > self.amount)
            hint, colour = f"Add {money(target - self.amount)} to reach {money(target)}.", TEXT
        if not is_coin and not self.amount:
            hint = "Insert a ₱50\nor ₱100 bill."
        if self.amount == MAX_CREDIT:
            hint = "Choose your coins\nto continue."
        self.text(570, 298, hint, 18, color=colour, width=185)
        values = ([self.preferred_coin] if is_coin and self.preferred_coin
                  else sorted(COINS) if is_coin else BILLS)
        gap = 12
        card_width = 232 if self.preferred_coin and is_coin else (504 - gap * (len(values) - 1)) / len(values)
        for index, value in enumerate(values):
            left = 28 + index * (card_width + gap)
            rect = (left, 203, left + card_width, 405)
            enabled = (self.amount + value <= MAX_CREDIT if is_coin
                       else self.amount == 0)
            callback = self.insert_coin if is_coin else self.insert_bill
            shape = self.rounded(*rect, outline=BORDER)
            self.currency_picture("coin" if is_coin else "note", value,
                                  left + card_width / 2, 264, 84 if is_coin else 146)
            self.text(left + card_width / 2, 335, money(value), 23, True,
                      color=TEXT if enabled else MUTED, anchor="center")
            self.text(left + card_width / 2, 375, "Tap to insert" if enabled else "Accepted" if not is_coin else "Full",
                      16, False, ACCENT if enabled else MUTED, "center")
            if enabled:
                self.action(rect, lambda v=value, cb=callback: cb(v), shape, BORDER)
        if is_coin and self.preferred_coin:
            returns = {5: "Five ₱1 coins", 10: "₱5 or ₱1 coins", 20: "Smaller coins"}
            self.text(288, 240, "You can get", 18, color=MUTED)
            self.text(288, 276, returns[self.preferred_coin], 23, True, width=245)
        help_text = "₱5 and ₱10 coins can be changed to smaller coins." if is_coin else "Accepted bills: ₱50 and ₱100."
        self.text(28, 422, help_text, 16, color=SOFT)
        self.button((552, 377, 772, 433), "Choose coins", self.open_choose,
                    enabled=self.session.ready, size=18)

    def insert_bill(self, value):
        """Acceptor entry point; invoke on the Tk main thread after acceptance."""
        if self.screen != "deposit" or self.session.source != "bill":
            return False
        try:
            self.session.accept_bill(value)
        except ValueError:
            return False
        self.open_choose()
        return True

    def insert_coin(self, value):
        """Coin input accumulates until the customer selects Choose coins."""
        if self.screen != "deposit" or self.session.source != "coin":
            return False
        try:
            self.session.accept_coin(value)
        except ValueError:
            return False
        self.show("deposit")
        return True

    def open_choose(self):
        if self.screen != "deposit" or not self.session.ready:
            return
        previous_plan = (self.options[self.selected].plan
                         if 0 <= self.selected < len(self.options) else None)
        self.options = self.session.options()
        if not self.options:
            return
        self.selected = next((i for i, option in enumerate(self.options)
                              if option.plan == previous_plan), 0)
        self.custom.set_amount(self.amount)
        self.show("choose")

    def choice_heading(self, title):
        self.steps(1)
        self.text(28, 131, title, 26, color=LIGHT)
        self.text(772, 154, f"Credit {money(self.amount)}", 18, color=LIGHT, anchor="e")

    def choice_tabs(self):
        for rect, title, screen in [
            ((28, 196, 394, 240), "Quick combinations", "choose"),
            ((406, 196, 772, 240), "Choose each coin", "custom"),
        ]:
            chosen = self.screen == screen
            shape = self.rounded(*rect, fill=ACCENT if chosen else SURFACE,
                                 outline=ACCENT if chosen else BORDER, radius=10)
            self.text((rect[0] + rect[2]) / 2, 218, title, 16, True,
                      SURFACE if chosen else ACCENT, "center")
            if not chosen:
                callback = self.open_custom if screen == "custom" else self.back_to_choices
                self.action(rect, callback, shape, BORDER)

    def build_choose(self):
        self.choice_heading("Choose your coins")
        self.text(28, 168, "Tap a coin picture to pick a combination, or choose each coin.",
                  13, color=SOFT)
        self.choice_tabs()

        for i, option in enumerate(self.options):
            x, y = 28 + (i % 3) * 252, 244 + (i // 3) * 76
            chosen = i == self.selected
            outline = ACCENT if chosen else BORDER
            shape = self.rounded(x, y, x + 240, y + 68,
                                 fill=TINT if chosen else SURFACE,
                                 outline=outline, line_width=2 if chosen else 1)
            self.payout_pictures(option.plan, x + 38, y + 34,
                                 size=44 if len(option.plan) == 1 else 32, gap=12)
            self.text(x + 77, y + 12, option.title, 18, True,
                      ACCENT_DARK if chosen else TEXT)
            self.text(x + 77, y + 43, option.detail, 11, color=MUTED)
            if chosen:
                self.check_icon(x + 226, y + 12, radius=7)
            self.action((x, y, x + 240, y + 68),
                        lambda index=i: self.select_option(index), shape,
                        outline, 2 if chosen else 1)

        self.text(28, 394, "Your combination", 16, color=SOFT)
        self.text(28, 419, describe(self.options[self.selected].plan), 16,
                  color=LIGHT, width=490)
        self.button((548, 396, 772, 440), "Review exchange",
                    self.confirm_payout, size=17)

    def select_option(self, index):
        if self.screen != "choose" or not 0 <= index < len(self.options):
            return
        self.selected = index
        self.show("choose")

    def open_custom(self):
        if self.screen != "choose" or not self.session.ready:
            return
        self.custom.set_amount(self.amount)
        self.show("custom")

    def build_custom(self):
        self.choice_heading("Build your coin mix")
        self.text(28, 169, "Tap a coin picture to add one, or use the + and − buttons.",
                  13, color=SOFT)
        for i, coin in enumerate(COINS):
            x, y = 28 + (i % 2) * 258, 202 + (i // 2) * 120
            count = self.custom.counts.get(coin, 0)
            outline = ACCENT if count else BORDER
            shape = self.rounded(x, y, x + 246, y + 116,
                         fill=TINT if count else SURFACE,
                         outline=outline, radius=12)
            self.currency_picture("coin", coin, x + 43, y + 53, 64)
            self.text(x + 90, y + 14, money(coin), 21, True)
            self.text(x + 90, y + 44, f"Subtotal {money(coin * count)}", 16,
                      color=ACCENT if count else MUTED)
            can_add = self.custom.remaining >= coin
            if can_add:
                self.action((x + 8, y + 12, x + 80, y + 108),
                            lambda c=coin: self.adjust_custom(c, 1), shape, outline)
            self.button((x + 88, y + 68, x + 132, y + 112), "−",
                        lambda c=coin: self.adjust_custom(c, -1), primary=False,
                        enabled=count > 0, size=25)
            self.text(x + 161, y + 88, str(count), 22, True, anchor="center")
            self.button((x + 190, y + 68, x + 234, y + 112), "+",
                        lambda c=coin: self.adjust_custom(c, 1),
                        enabled=can_add, size=24)

        self.text(570, 219, "Selected / credit", 12, color=SOFT)
        self.text(570, 242, f"{money(self.custom.total)} / {money(self.amount)}", 26,
                  False, LIGHT)
        count = sum(self.custom.counts.values())
        self.text(570, 281, f"{count} coin{'s' if count != 1 else ''}",
                  12, color=HEADER_MUTED)
        self.button((552, 315, 655, 359), "Clear", self.clear_custom,
                    primary=False, enabled=bool(count), size=14)
        self.button((665, 315, 772, 359), "Fill with ₱1", self.fill_custom,
                    primary=False, enabled=self.custom.remaining > 0, size=11)
        status = ("Your total matches." if self.custom.ready
                  else f"Add {money(self.custom.remaining)} more.")
        self.text(552, 369, status, 14, True,
                  ACCENT if self.custom.ready else GOLD)
        self.button((552, 392, 772, 436), "Review exchange", self.confirm_payout,
                    enabled=self.custom.ready, size=17)

    def adjust_custom(self, coin, delta):
        if self.screen != "custom" or not self.custom.adjust(coin, delta):
            return False
        self.show("custom")
        return True

    def clear_custom(self):
        if self.screen == "custom":
            self.custom.clear()
            self.show("custom")

    def fill_custom(self):
        if self.screen == "custom" and self.custom.fill_remaining():
            self.show("custom")

    def back_to_choices(self):
        if self.screen == "custom":
            self.show("choose")

    def go_back(self):
        if self.screen in ("deposit", "admin"):
            self.go_home()
        elif self.screen == "choose":
            self.back_to_deposit()
        elif self.screen == "custom":
            self.back_to_choices()
        elif self.screen == "review":
            self.pending_plan = {}
            self.show(self.review_origin)

    def back_to_deposit(self):
        if self.screen == "choose":
            self.show("deposit")  # Retains every inserted peso.

    def confirm_payout(self):
        if self.screen == "choose":
            plan = self.options[self.selected].plan
        elif self.screen == "custom":
            plan = self.custom.plan
        else:
            return False
        if not valid_plan(self.amount, plan):
            return False
        self.pending_plan = dict(plan)
        self.review_origin = self.screen
        self.show("review")
        return True

    def build_review(self):
        self.steps(2)
        self.text(28, 139, "Check your coin combination", 27, color=LIGHT)
        self.text(28, 181, "Make sure this is what you want to receive.",
                  13, color=SOFT)
        self.rounded(28, 211, 480, 430, outline=BORDER)
        self.text(50, 233, "COIN", 11, True, MUTED, "w")
        self.text(251, 233, "QUANTITY", 11, True, MUTED, "center")
        self.text(458, 233, "VALUE", 11, True, MUTED, "e")
        self.canvas.create_line(50, 251, 458, 251, fill=BORDER)
        for i, (coin, count) in enumerate(sorted(self.pending_plan.items(), reverse=True)):
            y = 278 + i * 41
            self.currency_picture("coin", coin, 68, y, 32)
            self.text(100, y, money(coin), 21, True, anchor="w")
            self.text(251, y, str(count), 20, True, anchor="center")
            self.text(458, y, money(coin * count), 20, True, anchor="e")
        self.rounded(504, 211, 772, 365, outline=BORDER)
        self.text(524, 232, "AMOUNT INSERTED", 11, True, MUTED)
        self.text(521, 253, money(self.amount), 36, True)
        count = sum(self.pending_plan.values())
        self.text(524, 308, f"{count} coin{'s' if count != 1 else ''} in total",
                  15, color=MUTED)
        self.text(524, 338, "Full value returned.", 13, True, ACCENT)
        self.button((504, 382, 772, 434), "Confirm & dispense",
                    lambda: self.start_dispense(self.pending_plan), size=17)

    def start_dispense(self, plan):
        if self.screen != "review" or not self.session.ready:
            return False
        if not valid_plan(self.amount, plan):
            return False
        if plan != self.pending_plan:
            return False
        self.plan = dict(plan)
        self.coin_queue = [coin for coin, count in sorted(plan.items(), reverse=True)
                           for _ in range(count)]
        self.total_coins = len(self.coin_queue)
        self.dropped = 0
        self.dispensed_value = 0
        self.show("dispensing")
        self.drop_job = self.root.after(COIN_DELAY_MS, self.drop_coin)
        return True

    def build_dispensing(self):
        self.steps(3)
        self.text(400, 185, f"Dispensing {money(self.amount)}", 32, False, LIGHT,
                  anchor="center")
        self.text(400, 230, describe(self.plan), 13, color=SOFT, anchor="center")
        self.payout_pictures(self.plan, 400, 292, size=64, gap=84)
        self.rounded(154, 351, 646, 359, fill=DIVIDER, radius=4)
        if self.dropped:
            right = 154 + 492 * self.dropped / self.total_coins
            self.rounded(154, 351, right, 359, fill=BRAND, radius=4)
        self.text(400, 393, f"{self.dropped} of {self.total_coins} coins · Please wait",
                  14, color=SOFT, anchor="center")

    def drop_coin(self):
        self.drop_job = None
        if self.closed or self.screen != "dispensing":
            return
        # Real hardware must advance on confirmed hopper pulses, not a timer.
        if self.dropped >= self.total_coins:
            return
        self.dispensed_value += self.coin_queue[self.dropped]
        self.dropped += 1
        self.show("dispensing")
        if self.dropped < self.total_coins:
            self.drop_job = self.root.after(COIN_DELAY_MS, self.drop_coin)
        else:
            self.drop_job = self.root.after(600, self.finish)

    def finish(self):
        self.drop_job = None
        if (self.closed or self.screen != "dispensing"
                or self.dropped != self.total_coins
                or self.dispensed_value != self.amount):
            return
        self.completed_amount = self.amount
        self.completed_plan = dict(self.plan)
        self.session.reset()
        self.done_deadline = time.monotonic() + DONE_TIMEOUT_S
        self.show("done")
        self.done_job = self.root.after(DONE_TIMEOUT_S * 1000, self.back_to_idle)

    def build_done(self):
        self.rounded(28, 102, 772, 433, outline=BORDER)
        self.payout_pictures(self.completed_plan, 400, 154, size=64, gap=78)
        self.text(400, 222, "Collect your coins", 31, True, anchor="center")
        count = sum(self.completed_plan.values())
        self.text(400, 267, f"{money(self.completed_amount)} exchanged · "
                  f"{count} coin{'s' if count != 1 else ''}", 18,
                  color=ACCENT, anchor="center")
        self.text(400, 300, describe(self.completed_plan), 14,
                  color=MUTED, anchor="center")
        self.button((239, 342, 561, 394), "Start another exchange",
                    self.back_to_idle, size=17)
        self.done_timer_item = self.text(400, 415, "", 11,
                                         color=MUTED, anchor="center")
        self.update_done_timer()

    def go_home(self):
        if self.screen not in ("deposit", "admin"):
            return
        if not self.amount:
            self.session.reset()
        self.show("idle")

    def back_to_idle(self):
        if self.screen != "done":
            return
        if self.done_job is not None:
            self.root.after_cancel(self.done_job)
            self.done_job = None
        self.plan = {}
        self.preferred_coin = None
        self.pending_plan = {}
        self.custom = CoinCombination()
        self.options = []
        self.show("idle")

    def build_admin(self):
        self.text(28, 109, "Kiosk controls", 29, color=LIGHT)
        self.text(28, 153, "Device controls are available while no exchange is active.",
                  14, color=SOFT)
        items = [
            ("Exit to desktop", self.close),
            ("Restart device", lambda: self.power("reboot")),
            ("Shut down", lambda: self.power("poweroff")),
            ("Back to exchange", self.go_home),
        ]
        for i, (title, callback) in enumerate(items):
            x, y = 28 + i % 2 * 378, 208 + i // 2 * 110
            self.button((x, y, x + 366, y + 90), title, callback,
                        primary=i == 3, size=20)

    def power(self, command):
        if self.screen != "admin" or self.amount or command not in ("reboot", "poweroff"):
            return
        if not os.path.exists("/proc/device-tree/model"):
            messagebox.showinfo("Device controls",
                                "Power controls are available on the Raspberry Pi kiosk.",
                                parent=self.root)
            return
        title = "Restart device" if command == "reboot" else "Shut down"
        if messagebox.askyesno(title, f"{title} now?", parent=self.root):
            try:
                subprocess.Popen(["sudo", "-n", command])
            except OSError as error:
                messagebox.showerror(title, str(error), parent=self.root)
                return
            self.close()

    def on_tap(self, event):
        # Do not allow admin navigation to interrupt an active exchange.
        if self.screen != "idle" or self.amount or event.x > 100 or event.y > 80:
            self.taps = []
            return False
        now = time.monotonic()
        self.taps = [stamp for stamp in self.taps if now - stamp < 3] + [now]
        if len(self.taps) >= ADMIN_TAPS:
            self.taps = []
            self.show("admin")
            return True
        return False

    def on_click(self, event):
        self.canvas.focus_set()
        self.keyboard_focus = False
        if self.on_tap(event):
            return
        for action in reversed(self.actions):
            x1, y1, x2, y2 = action["rect"]
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                action["command"]()
                break

    def clear_hover(self):
        if 0 <= self.hover_index < len(self.actions):
            old = self.actions[self.hover_index]
            self.canvas.itemconfigure(old["shape"], outline=old["outline"],
                                      width=old["line_width"])
        self.hover_index = -1
        self.canvas.configure(cursor="none" if FULLSCREEN else "")

    def on_motion(self, event):
        hit = -1
        for i, action in enumerate(self.actions):
            x1, y1, x2, y2 = action["rect"]
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                hit = i
                break
        if hit == self.hover_index:
            return
        self.clear_hover()
        self.hover_index = hit
        if hit >= 0:
            self.canvas.itemconfigure(self.actions[hit]["shape"], outline=ACCENT,
                                      width=2)
            if not FULLSCREEN:
                self.canvas.configure(cursor="hand2")

    def move_focus(self, direction):
        if self.actions:
            self.keyboard_focus = True
            self.focus_index = ((self.focus_index + direction) % len(self.actions)
                                if self.focus_index >= 0
                                else 0 if direction > 0 else len(self.actions) - 1)
            self.draw_focus()
        return "break"

    def draw_focus(self):
        if self.focus_ring is not None:
            self.canvas.delete(self.focus_ring)
        if 0 <= self.focus_index < len(self.actions):
            x1, y1, x2, y2 = self.actions[self.focus_index]["rect"]
            self.focus_ring = self.canvas.create_rectangle(
                x1 + 4, y1 + 4, x2 - 4, y2 - 4, outline=GOLD, width=2, dash=(3, 3)
            )

    def activate_focus(self, event=None):
        if self.keyboard_focus and 0 <= self.focus_index < len(self.actions):
            self.actions[self.focus_index]["command"]()
        return "break"

    def update_done_timer(self):
        left = max(0, math.ceil(self.done_deadline - time.monotonic()))
        if self.done_timer_item is not None:
            self.canvas.itemconfigure(self.done_timer_item,
                                      text=f"Returning to the start in {left}s")

    def tick(self):
        self.tick_job = None
        if self.closed:
            return
        if self.screen == "done":
            self.update_done_timer()
        self.tick_job = self.root.after(200, self.tick)

    def close(self):
        if self.closed:
            return
        self.closed = True
        for job in (self.tick_job, self.drop_job, self.done_job):
            if job is not None:
                self.root.after_cancel(job)
        self.root.destroy()


if __name__ == "__main__":
    register_roboto()
    root = tk.Tk()
    App(root)
    root.mainloop()
