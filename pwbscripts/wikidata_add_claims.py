#!/usr/bin/python
#encoding: utf-8

"""
#Description: runs a bot to batch add claims, formated "Q...\tP...\tvalue", one per line on stdin


Example input:
    Q646365 P996    File:Dictionnaire_des_Antiquités_grecques_et_romaines_-_Daremberg_-_I_1.djvu
    Q646365 P996    File:Dictionnaire_des_Antiquités_grecques_et_romaines_-_Daremberg_-_I_2.djvu
    Q646365 P996    File:Dictionnaire_des_Antiquités_grecques_et_romaines_-_Daremberg_-_II_1.djvu
    Q646365 P996    File:Dictionnaire_des_Antiquités_grecques_et_romaines_-_Daremberg_-_II_2.djvu
    Q646365 P996    File:Dictionnaire_des_Antiquités_grecques_et_romaines_-_Daremberg_-_III_1.djvu
    Q646365 P996    File:Dictionnaire_des_Antiquités_grecques_et_romaines_-_Daremberg_-_III_2.djvu
    Q646365 P996    File:Dictionnaire_des_Antiquités_grecques_et_romaines_-_Daremberg_-_IV_1.djvu
    Q646365 P996    File:Dictionnaire_des_Antiquités_grecques_et_romaines_-_Daremberg_-_IV_2.djvu
    Q646365 P996    File:Dictionnaire_des_Antiquités_grecques_et_romaines_-_Daremberg_-_V_1.djvu
    Q646365 P996    File:Dictionnaire_des_Antiquités_grecques_et_romaines_-_Daremberg_-_V_2.djvu
"""


import csv, sys
import wd_lib


def main():
    claimreader = csv.reader(sys.stdin, delimiter="\t")

    for line in claimreader:
        print "Item: <{}> Property: <{}> value:'{}'".format(line[0], line[1], line[2])

if __name__ == "main":
    main()
