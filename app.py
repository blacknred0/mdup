#!/usr/bin/python
"""Mediacom Data Usage Prediction (mdup).

Process main gathering or prediction of mdup

Irving Duran <irving.duran@gmail.com>

"""

import sys
import getopt


def main(argv):
    """getopt(args, options[, long_options]) -> opts, args.

    Parse the list of arguments whether is to gather data or to predict.

    """
    try:
        opts, args = getopt.getopt(argv, "hvgp", ["gather=", "predict="])
    except getopt.GetoptError:
        print('app.py [-g, -p, -v, -h]')
        print('Wrong command. Do `app.py -h` for help.')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('app.py -g ')
            print('            <gather data and log it>')
            print('app.py -p 5557779999@vtext.com')
            print('            <gather data if necessary and predict>')
            sys.exit()
        elif opt == '-v':
            print('app.py version 1.1')
            sys.exit()
        elif opt in ("-g", "--gather"):
            import main_gather
            sys.exit()
        elif opt in ("-p", "--predict"):
            if len(args) < 1:
                print('Error! Need to pass phone number to send data to.')
                sys.exit(2)
            else:
                import main
                sys.exit()


if __name__ == "__main__":
    main(sys.argv[1:])
