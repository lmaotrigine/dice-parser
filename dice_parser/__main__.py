# Copyright (c) 2022-present, Varun J., All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys

from dice_parser import roll


def __d20__():
    import argparse

    from dice_parser import AdvType

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--allow-comments', action='store_true', help='Allow comments in the input'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-a',
        '--adv',
        '--advantage',
        action='store_const',
        const=AdvType.ADV,
        help='Roll with advantage',
    )
    group.add_argument(
        '-d',
        '--dis',
        '--disadvantage',
        action='store_const',
        const=AdvType.DIS,
        help='Roll with disadvantage',
    )
    parser.add_argument('expr', nargs='?', help='Dice expression', default='d20')

    args = parser.parse_args()
    adv_type = args.adv or args.dis or AdvType.NONE
    roll_result = roll(args.expr, allow_comments=args.allow_comments, advantage=adv_type)
    print(roll_result)


if __name__ == '__main__':
    try:
        while True:
            roll_result = roll(input('> '), allow_comments=True)
            print(str(roll_result))
    except EOFError:
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(1)
