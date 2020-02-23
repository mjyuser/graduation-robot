# -*- coding:utf-8 -*-
from model.db import Base, engine, redis_client
from services import spiders
import sys
import getopt
import requests


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

def testRequest():
    response = requests.get("https://click.simba.taobao.com/cc_im?p=%D6%C7%C4%DC%BF%D5%B5%F7&s=19025149&k=577&e=Eu6D4J0f13ZclyW4IwaYMwluWa2VJAmj7hhSg4UD52kJ5%2BabB6v0syMdsc%2F0VDls3ZuiR12Vl3s01XJlP1%2FALhKSmLbMXicDzwA%2BLxzwdfvIR0UjkaCQdmA9hhJdLYAIi17RD%2BiK7K9aH09%2FahAPGUuvvE7jpK%2B4FZj8xHamRgQqucLUYR%2B8NnlVM2lG3WzaNiDbMzq3Tm4x2aNgM8hcR2hUz4o2kCduQA0G6AsXbWADPIBSLBiN%2BN0YkSK9T6pV00UXJO4cKjgtgVJHPEQkid2MnqWRwxngFz8i%2B%2B3wjZPqUWSWiF6%2BmK%2FwK%2F%2F%2BGQApW0xMZFwXhEJnOpUiG6lVG%2BIWUWeWDeQDhTszBSigUC%2FW65yPDM16m73a70gMJgpN3dIJk%2FmUwObBJmsNQFpilW7JEnk%2FY5Qc2rOwcZuf55YgeaR6oT8qOOWwoIPG0Az2xA9qL5M%2FHhoUEk%2FLvdxxCVMMs%2Fvt1cU%2Bbvk1hBtMGCuHoADYBYtec8K8BtJN8%2BlpgQ1nPb5zruSe%2BE3cUgCLwgJOKkBaWYGRkMnsqCIvrIEUb40uV5ZPminJJuuUEunt")
    print(response.status_code)
    print(response.url)


if __name__ == "__main__":
    main(sys.argv[1:])
    # testRequest()