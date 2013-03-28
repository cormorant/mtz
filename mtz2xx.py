#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convert mtz dat file(s) to baikal-XX(5) format.

Вопрос: возможно ли обрабатывать большие (гигабайт) файлы в программе xxseis.
Возможно, надо создавать файлы длиной не больше чем 1 час?

WARNING:
Программы xxseis xxseis(6), да и формат байкал предполагают целые числа (int16(h)/int32(i))
в массивах данных. Не забыть делать astype(np.int32).
Данные в файлах мтз - с плавающей точкой.
TODO:
умножать все значения в массивах данных на 100.
"""
__version__ = "0.0.1"
COMPANY_NAME = 'GIN'
APP_NAME = 'mtz2xx'
# imports
import os
import sys
import argparse
import numpy as np
import pandas
import struct
import datetime
import numpy  as np
#DefaultMainHeader = '\x00\x00\x00\x00<\x00\x18\x00\n\x00\xdc\x07\x0c\x00\x00\x00\x00\x00\x18\x00\x00\x00d\x00fU\x88w\x00\x00\x00\x00lvrz.s\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00{\x14\xaeG\xe1z\x84?\x00\x00\x00\x00@E\xd2@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@\x0f:k\xcd\xad\x03\x00\x00\x00\x00\x00\x00\x00\x00'


MainHeaderMap = (
    # назв          разм тип  знач. по умолч.
    ('kan',           2, "h", 0),#ends on 2 
    ('tip_test',      2, "h", 0),#4
    ('vers',          2, "h", 53),#6
    ('day',           2, "h", 1),#8
    ('month',        2, "h", 1),#10
    ('year',          2, "h", 1970),#12
    ('satellit',      2, "h", 10),#14
    ('valid',         2, "H", 0),#16
    ('pri_synhr',     2, "h", 0),#18
    ('PAZP',          2, "h", 24),#20
    ('reserv_short',  2, "h", 0),#32
    ('reserv_short',  2, "h", 0),
    ('reserv_short',  2, "h", 0),
    ('reserv_short',  2, "h", 0),
    ('reserv_short',  2, "h", 0),
    ('reserv_short',  2, "h", 0),
    ('station',       16, "16s", "_st"),#48
    ('dt',            8, 'd', 0.01), #56
    ('to',            8, 'd', 1.),#64
    ('deltas',        8, 'd', 0.),#72
    ('latitude',      8, 'd', 0.),#80
    ('longitude',     8, 'd', 0.),#88
    ('reserv_double', 8, 'd', 0),#104
    ('reserv_double', 8, 'd', 0),#104
    ('reserv_long',   4, 'I', 0),#120
    ('reserv_long',   4, 'I', 0),
    ('reserv_long',   4, 'I', 0),
    ('reserv_long',   4, 'I', 0),
)

ChannelHeaderMap = (
    ('phis_nom', 2, 'h', 0),                 #0 2
    ('reserv', 2, 'h', 0),                  #2-8
    ('reserv', 2, 'h', 0),
    ('reserv', 2, 'h', 0),
    ('name_chan', 24, '24s', "ch"),             #8 32, stripnulls
    ('tip_dat', 24, '24s', "tipdat"),               #32 56, stripnulls
    ('koef_chan', 8, 'd', 1.),                #56 64
    ('calcfreq', 8, 'd', 1.),                 #64 72
)


def adjust_freq(freq):
    """ определить ближайшую дискретизацию к данной """
    # 2 4 8 16 32 64 128 -- двойка в степени
    stepens = np.fromiter((2**i for i in range(2, 8)), int)
    # найти индекс ближайшего значения к нашему
    b = np.abs(stepens-freq)
    ind = np.where(b==b.min())[0][0]
    return stepens[ind]

def write_file(filename, channels, station, a, dt, date1):
    ''' Записывать файл формата Байкал(5), '''
    """
    new_fname = "%02d%02d%02d.0%s" % (
        dic['day'],
        hour,
        minute,
        dic["station"][0]
    )
    """
    #
    print("Now we write file %s from date %s with dt %f. Station is %s" % (filename,
        date1, dt, station))
    #=== writing
    filename = filename[:filename.rindex('.')] + ".%s0" % station[0]
    # создадим файл для записи
    if os.path.exists(filename):
        print("File already exists! Aborting...")
        return
    _f = open(filename, "wb")
    #= main header
    # подготовим данные для записи в главный заголовок
    pack_values = [i[3] for i in MainHeaderMap]
    # количество каналов
    pack_values[0] = len(channels)
    # изменим название станции
    pack_values[16] = station
    # установим дату
    pack_values[3:6] = (date1.day, date1.month, date1.year)
    # установим дискретизацию
    pack_values[17] = dt
    # запишем точку первой секунды t0
    date = datetime.datetime(date1.year, date1.month, date1.day)
    t0 = (date1 - date).seconds
    pack_values[18] = t0
    # готовы данные для записи главного заголовка
    pack_header = struct.pack('hhhhhhhHhh6h16sddddd2d4I', *pack_values)
    # запишем главный заголовок
    _f.write(pack_header)
    #= channel headers
    for num, channel in enumerate(channels):
        # подготовим заголовок канала
        pack_values = [i[3] for i in ChannelHeaderMap]
        # номер канала
        pack_values[0] = num
        # имя канала
        pack_values[4] = channel
        # запишем заголовок канала
        pack_channel = struct.pack('hhhh24s24sdd', *pack_values)
        _f.write(pack_channel)
        #
    # пишем данные в файл
    #TODO: make sure that dtype is np.int32
    a = a.astype(np.int32)
    _f.write(a.tostring())
    # закроем файл
    _f.close()


def main(filename):
    ''' считывать данные из dat-файлов с непрерывными данными мтз '''
    # возвращать начальную дату/время, дискретизацию, имя станции, и массивы с данными
    #data = np.loadtxt(filename, delimiter=",", skiprows=3, )
    data = pandas.read_csv(filename, header=None, skiprows=3,
        index_col=[0], parse_dates=[0], )
    # умножим всё на 1000 чтобы сделать целые числа
    data *= 1000
    data = data.astype(np.int32)
    # first and last date is
    date1 = data.index[0]
    date2 = data.index[-1]
    # определить дискретизацию
    dt = (data.index[1] - date1).total_seconds()
    freq = adjust_freq(1. / dt)
    dt = 1. / freq
    # проверка правильности положения последней секунды при такой дискретизации
    try:
        assert date2 == date1 + datetime.timedelta(seconds=((len(data)-1) * dt)), (
            "Error calculating date2 (%s) from date1 (%s) and discretiz (%f)." % (
                date2, date1, dt))
    except AssertionError:
        while True:
            reply = raw_input("Continue processing (y/n)?")
            if not reply: continue
            if reply.lower()[0] == "y":
                break
            else:
                sys.exit(0)
    # имя станции - взять первые буквы из имени файла
    station = "".join([s for s in filename if s.isalpha()])
    # названия каналов
    channels = ["X%02d" % i for i in range(data.shape[1])]
    # определить сколько нужно считывать элементов массива, чтобы получился 1 час
    #n = 3600 * freq # число секунд в часе (3600) * частоту в Гц
    # массив для записи в файл
    a = data.values.flatten()
    write_file(filename, channels=channels, station=station, a=a, dt=dt, date1=date1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # общие парсеры
    parser.add_argument('-V', '--version', action='version', 
        version='%(prog)s.' + __version__)
    # файл с данными
    parser.add_argument("filename", nargs="+", help="filename to process")
    # подробный вывод
    #parser.add_argument("-v", "--verbose", action="store_true", default=False,
    #    dest="verbose", help="verbose output")
    #== end of parsing parameters
    args = parser.parse_args()
    #print args
    #=== start job
    # переконвертируем и запишем файл формата Байкал
    for filename in args.filename:
        main(filename)
    #
    #=== ends
    
