import argparse
from nmutils.utils import Ionchamber

if __name__ == '__main__':
    ### Parse input
    parser = argparse.ArgumentParser(
        description='This script converts ion chamber readings (as current or TTL frequency) to x-ray flux.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--frequency', type=int, dest='frequency',
                        default=None,
                        help='Frequency output from the Oxford box at a given range')
    parser.add_argument('--range', type=float, dest='range',
                        default=10e-9,
                        help='Current corresponding to 1 MHz TTL frequency')
    parser.add_argument('--current', type=float, dest='current',
                        default=None,
                        help='Measured current on the ion chamber')
    parser.add_argument('--energy', type=float, dest='energy',
                        default=10000,
                        help='X-ray energy')
    parser.add_argument('--length', type=float, dest='length',
                        default=1.5,
                        help='Path length of the chamber')
    args = parser.parse_args()

    if (args.frequency is None) and (args.current is None):
        print("\nPlease specify either frequency or current!\n")
        exit(-1)
    elif (args.frequency is not None) and (args.current is not None):
        print("\nDon't specify both frequency and current!\n")
        exit(-1)

    if args.current is None:
        args.current = args.frequency / 1e6 * args.range

    print("\nEnergy  %.0f" % args.energy)
    print("Current %.2e" % args.current)
    print("Length  %.2f" % args.length)

    ic = Ionchamber(length=args.length, energy=args.energy)
    print('\nCalculated flux: %.2e\n' % ic.flux(args.current))
