# -*- coding:utf-8 -*-
from model.db import Base, engine
from services import spiders
import sys
import getopt


def main(argv):
    router = ""
    try:
        opts, args = getopt.getopt(argv, "ha:r:c", ["help", "init", "router=", "clear"])
    except getopt.GetoptError:
        print("Error: fetch appliance args error -r <router> -c")
        print(" or --router=<router> --clear --init")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit()
        elif opt == "--init":
            init_db()
            sys.exit()
        elif opt in ("-r", "--router"):
            router = arg
        elif opt in ("-c", "--clear"):
            spiders.clear()
            sys.exit()

    if router != "":
        spiders.fetchAir(router)
        sys.exit()

    print_help()


def print_help():
    print("the script is fetch something website with appliances")
    print("main.py -r <router> -c")
    print(" or --init --router=<router> --clear")


def init_db():
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    main(sys.argv[1:])
