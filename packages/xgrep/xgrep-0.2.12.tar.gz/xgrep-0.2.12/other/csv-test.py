#!/usr/bin/env python

import polars as pl
from functools import partial
from io import StringIO

p = partial(pl.read_csv, separator="\t")

tsv = p("people.tsv")

print(tsv)


s = StringIO("hey\tyou\n3\t4\n")

s = StringIO("name\tage\ncyril\t32\nmaria\t81\n")
tsv = p(s)
print(tsv)
