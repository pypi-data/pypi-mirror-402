import janus_swi as janus
import sys


def main(argv):
    if len(argv) <= 1:
        print("Usage: run_prolog.py <prolog_file.pl>")

    # load the prolog program
    janus.query_once(f"consult('{argv[1]}')")
    # run the query
    janus.query_once("main")

    print(f"{argv[1]} ran successfully.")


if __name__ == "__main__":
    main(sys.argv)


