'''
Created on 25 août 2015

@author: tom
'''

#
# functions on the List (of Pages) article
#


def compare_sorted_lists(new_list, old_list):
    """ calculates the differences between a list and a newer one

    returns a couple of lists (insertions, deletions)
    """
    gain = []
    loss = []
    index = 0
    for elem in old_list:
        try:
            while new_list[index] < elem:
                gain.append(new_list[index])
                index += 1
            if elem == new_list[index]:
                index += 1
            else:
                loss.append(elem)
        except IndexError:
            loss.append(elem)
    return (gain + new_list[index:], loss)


def inter_sorted_lists(list1, list2):
    """ computes the commons elements of two sorted list """
    index = 0
    intersection = []
    for elem in list2:
        try:
            while list1[index] < elem:
                index += 1
            if list1[index] == elem:
                intersection.append(elem)
                index += 1
            # else:
            #    print [elem, list1[index]]
        except IndexError:
            break
    return intersection


def odd_index_list(long_list):
    """ Returns a list of indexes """
    return [long_list[i] for i in range(1, len(long_list), 2)]
