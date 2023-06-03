import logging

import zetex_jr
import item_manager


def main():
    logging.basicConfig(filename='rex-log.txt', encoding='utf-8', level=logging.DEBUG)
    zetex_jr.zetex_jr.run(item_manager.get_bot_token())


if __name__ == "__main__":
    main()
