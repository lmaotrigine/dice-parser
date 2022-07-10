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
