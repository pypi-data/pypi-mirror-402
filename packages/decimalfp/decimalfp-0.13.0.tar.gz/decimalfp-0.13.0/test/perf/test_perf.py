# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        test_perf
# Purpose:     Compare performance of different implementations of Decimal
#
# Author:      Michael Amrhein michael@adrhinum.de)
#
# Copyright:   (c) 2019 Michael Amrhein
# License:     This program is part of a larger application. For license
#              details please read the file LICENSE.TXT provided together
#              with the application.
# ----------------------------------------------------------------------------
# $Source:     test/perf/test_perf.py $
# $Revision:   2020-11-19T16:55:08+01:00 $


"""Compare performance of different implementations of Decimal."""


from decimal import getcontext
import operator


ctx = getcontext()
ctx.prec = 1250


def test_decimal_from_str(benchmark, str_value, impl):
    benchmark(impl.Decimal, str_value)


def test_decimal_add(benchmark, dec_value_1, dec_value_2):
    benchmark(operator.add, dec_value_1, dec_value_2)


def test_decimal_mul(benchmark, dec_value_1, dec_value_2):
    benchmark(operator.mul, dec_value_1, dec_value_2)


def test_decimal_div(benchmark, dec_value_1, dec_value_2):
    benchmark(operator.truediv, dec_value_1, dec_value_2)
