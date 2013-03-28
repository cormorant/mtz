#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Графический просмотр больших массивов данных. Последовательно.
"""
__version__="0.0.1"
COMPANY_NAME = 'GIN'
APP_NAME = 'mtzview'

# imports
import os
import sys
import argparse

import pandas
import pylab as plt

# сколько загружать строк по умолчанию
N = 10000
# какой столбец загружать по умолчанию
COL = 0


def process_file(filename, col=COL, N=N, skiprows=None, header=None, sep=None):
    """ загружаем файл кусками по N строк. Даты в первом столбце """
    data = pandas.read_csv(filename, header=None, skiprows=skiprows, sep=sep,
        index_col=[0], parse_dates=[0],
        iterator=True#, verbose=True
    )
    #
    while True:
        try:
            a = data.get_chunk(N)
        except StopIteration:
            print("End of file reached.")
            break
        print("Plotting data from %s to %s" % (a.index[0], a.index[-1]))
        # какой столбец выводить
        column = a.columns[col]
        a[column].plot()#(subplots=True, legend=False)
        plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # общие парсеры
    parser.add_argument('-V', '--version', action='version', 
        version='%(prog)s.' + __version__)
    # файл с данными
    parser.add_argument("filenames", nargs="+", help="filename to process")
    # сколько строк пропускать
    parser.add_argument("-s", "--skiprows", type=int, default=3,
        help="nrows to skip (default 3)")
    # сколько строк загружать
    parser.add_argument("-n", "--nrows", type=int, default=N,
        help="nrows to load (default %d)" % N)
    # какой столбец загружать
    parser.add_argument("-f", "--field", type=int, default=COL,
        help="column to load (default 0)")
    # подробный вывод
    #parser.add_argument("-v", "--verbose", action="store_true", default=False,
    #    dest="verbose", help="verbose output")
    #== end of parsing parameters
    args = parser.parse_args()
    print args
    #=== start job
    for filename in args.filenames:
        print filename
        try:
            # обрабатывать файл
            process_file(filename, sep=",", skiprows=3, N=args.nrows, col=args.field)
        except KeyboardInterrupt:
            print("Interrupted by user.")
            break
        #except BaseException, msg:
        #    print("An error occured: %s" % msg)
        # parse file
        # plot file
    #=== ends
    print



