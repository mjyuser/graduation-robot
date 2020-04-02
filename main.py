# -*- coding:utf-8 -*-
from services import spiders
import sys
import getopt


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "ha:r:c", ["help", "router=", "clear"])
    except getopt.GetoptError:
        print("Error: fetch taobao home args error -r <router> -c")
        print(" or --router=<router> --clear --init")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
        elif opt in ("-r", "--router"):
            spiders.fetchAir(arg)
        elif opt in ("-c", "--clear"):
            spiders.clear()
        else:
            print_help()


def print_help():
    print("the script is fetch something website with home")
    print("main.py -r <router> -c")
    print(" or --init --router=<router> --clear")


if __name__ == "__main__":
    main(sys.argv[1:])
