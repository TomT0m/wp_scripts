
ORD_MAP = {1: "first", 2: "second",
           3: "third", 4: "fourth",
           5: "fifth", 6: "sixth",
           7: "seventh", 8: "eighth",
           9: "ninth", 10: "tenth"}


def get_en_ordinal(number):
    """ formats a number into a correct (I hope) ordinal english version of that number
    """

    if number <= 10 and number > 0:
        # suffixes = ["th", "st", "nd", "rd", ] + ["th"] * 16
        # return str(number) + suffixes[num % 100]
        return ORD_MAP[number]
    elif number > 10:
        if number % 10 == 1 and number > 11:
            suffix = "st"
        elif number % 10 == 2 and number > 12:
            suffix = "nd"
        elif number % 10 == 3 and number > 13:
            suffix = "rd"
        else:
            suffix = "th"

        return u"{}{}".format(number, suffix)

    else:
        raise ValueError("Must be > 0")
