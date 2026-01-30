"""
Copyright (c) 2016- 2025, Wiliot Ltd. All rights reserved.

Redistribution and use of the Software in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

  1. Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.

  2. Redistributions in binary form, except as used in conjunction with
  Wiliot's Pixel in a product or a Software update for such product, must reproduce
  the above copyright notice, this list of conditions and the following disclaimer in
  the documentation and/or other materials provided with the distribution.

  3. Neither the name nor logo of Wiliot, nor the names of the Software's contributors,
  may be used to endorse or promote products or services derived from this Software,
  without specific prior written permission.

  4. This Software, with or without modification, must only be used in conjunction
  with Wiliot's Pixel or with Wiliot's cloud service.

  5. If any Software is provided in binary form under this license, you must not
  do any of the following:
  (a) modify, adapt, translate, or create a derivative work of the Software; or
  (b) reverse engineer, decompile, disassemble, decrypt, or otherwise attempt to
  discover the source code or non-literal aspects (such as the underlying structure,
  sequence, organization, ideas, or algorithms) of the Software.

  6. If you create a derivative work and/or improvement of any Software, you hereby
  irrevocably grant each of Wiliot and its corporate affiliates a worldwide, non-exclusive,
  royalty-free, fully paid-up, perpetual, irrevocable, assignable, sublicensable
  right and license to reproduce, use, make, have made, import, distribute, sell,
  offer for sale, create derivative works of, modify, translate, publicly perform
  and display, and otherwise commercially exploit such derivative works and improvements
  (as applicable) in conjunction with Wiliot's products and services.

  7. You represent and warrant that you are not a resident of (and will not use the
  Software in) a country that the U.S. government has embargoed for use of the Software,
  nor are you named on the U.S. Treasury Department’s list of Specially Designated
  Nationals or any other applicable trade sanctioning regulations of any jurisdiction.
  You must not transfer, export, re-export, import, re-import or divert the Software
  in violation of any export or re-export control laws and regulations (such as the
  United States' ITAR, EAR, and OFAC regulations), as well as any applicable import
  and use restrictions, all as then in effect

THIS SOFTWARE IS PROVIDED BY WILIOT "AS IS" AND "AS AVAILABLE", AND ANY EXPRESS
OR IMPLIED WARRANTIES OR CONDITIONS, INCLUDING, BUT NOT LIMITED TO, ANY IMPLIED
WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY, NONINFRINGEMENT,
QUIET POSSESSION, FITNESS FOR A PARTICULAR PURPOSE, AND TITLE, ARE DISCLAIMED.
IN NO EVENT SHALL WILIOT, ANY OF ITS CORPORATE AFFILIATES OR LICENSORS, AND/OR
ANY CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
OR CONSEQUENTIAL DAMAGES, FOR THE COST OF PROCURING SUBSTITUTE GOODS OR SERVICES,
FOR ANY LOSS OF USE OR DATA OR BUSINESS INTERRUPTION, AND/OR FOR ANY ECONOMIC LOSS
(SUCH AS LOST PROFITS, REVENUE, ANTICIPATED SAVINGS). THE FOREGOING SHALL APPLY:
(A) HOWEVER CAUSED AND REGARDLESS OF THE THEORY OR BASIS LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE);
(B) EVEN IF ANYONE IS ADVISED OF THE POSSIBILITY OF ANY DAMAGES, LOSSES, OR COSTS; AND
(C) EVEN IF ANY REMEDY FAILS OF ITS ESSENTIAL PURPOSE.
"""


min_tx_step_per_inlay = \
    {
        "tiki": {
            "coarse": 8.47546,
            "fine": 0.98521,
            "efine": 0.03377,
            "power_mode": 'LPM'
        },
        "teo": {
            "coarse": 10.45000,
            "fine": 1.19478,
            "efine": 0.04250,
            "power_mode": 'LPM'
        },
        '086': {  # TEO
            "coarse": 10.45000,
            "fine": 1.19478,
            "efine": 0.04250,
            "power_mode": 'LPM'
        },
        '096': {  # TIKI
            "coarse": 8.47546,
            "fine": 0.98521,
            "efine": 0.03377,
            "power_mode": 'LPM'
        },
        '099': {  # TIKI
            "coarse": 8.47546,
            "fine": 0.98521,
            "efine": 0.03377,
            "power_mode": 'LPM'
        },
        '107': {  # Battery
            "coarse": 9.6,
            "fine": 1.097,
            "efine": 0.039,
            "power_mode": 'HPM'
        },
        '117': {  # TIKI
            "coarse": 8.47546,
            "fine": 0.98521,
            "efine": 0.03377,
            "power_mode": 'LPM'
        },
        '121': {  # TIKI
            "coarse": 8.47546,
            "fine": 0.98521,
            "efine": 0.03377,
            "power_mode": 'LPM'
        },
        '122': {  # TIKI NAP
            "coarse": 8.47546,
            "fine": 0.98521,
            "efine": 0.03377,
            "power_mode": 'LPM'
        },
        '136': {  # TIKI
            "coarse": 8.47546,
            "fine": 0.98521,
            "efine": 0.03377,
            "power_mode": 'LPM'
        },
        '160': {  # TIKI GEN3
            "tx_min": 2350,  # MHz
            "tx_max": 2540,  # MHz
            "span": 190,  # MHz
            "power_mode": 'LPM'
        },
        '168': {  # TIKI GEN3
            "tx_min": 2350,  # MHz
            "tx_max": 2540,  # MHz
            "span": 190,  # MHz
            "power_mode": 'LPM'
        },
        '169': {  # TIKI GEN3
            "tx_min": 2350,  # MHz
            "tx_max": 2540,  # MHz
            "span": 190,  # MHz
            "power_mode": 'LPM'
        },
        '170': {  # TIKI GEN3
            "tx_min": 2350,  # MHz
            "tx_max": 2540,  # MHz
            "span": 190,  # MHz
            "power_mode": 'LPM'
        },
        '179': {  # TIKI GEN3
            "tx_min": 2312,  # MHz
            "tx_max": 2544,  # MHz
            "span": 190,  # MHz
            "power_mode": 'HPM'
        },
        '184': {  # TIKI GEN3
            "tx_min": 2350,  # MHz
            "tx_max": 2565,  # MHz
            "span": 215,  # MHz
            "power_mode": 'HPM'
        },
        '191': {  # TIKI GEN3 TODO Currntly uses 190 values, need to update when data is available
            "tx_min": 2392,  # MHz
            "tx_max": 2545,  # MHz
            "span": 165,  # MHz
            "power_mode": 'HPM'
        },
    }