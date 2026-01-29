import pandas as pd
from k2pipe.mypipe import my_concat, my_read_csv, time_shift

pd.concat = my_concat
pd.read_csv = my_read_csv
pd.Series.time_shift = time_shift

print('K2Pipe initialized')