import argparse
from nmutils.utils import Ionchamber

if __name__ == '__main__':
    ### Parse input
    parser = argparse.ArgumentParser(
        description='This script converts ion chamber currents to x-ray flux.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--current', type=float, dest='current',
                        default=None,
                        help='Measured current on the ion chamber in A')
    parser.add_argument('--energy', type=float, dest='energy',
                        default=10000,
                        help='X-ray energy in eV')
    parser.add_argument('--length', type=float, dest='length',
                        default=1.5,
                        help='Path length of the chamber in cm')
    args = parser.parse_args()

    if args.current is None:
        print("\nPlease specify the current!\n")
        exit(-1)

    print("\nEnergy  %.0f" % args.energy)
    print("Current %.2e" % args.current)
    print("Length  %.2f" % args.length)

    ic = Ionchamber(length=args.length, energy=args.energy)
    print('\nCalculated flux: %.2e\n' % ic.flux(args.current, args.energy))
