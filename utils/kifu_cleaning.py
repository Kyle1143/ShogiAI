#棋譜ファイルを開く


import pandas as pd
import argparse
import os
import re
import statistics

parser = argparse.ArgumentParser()
parser.add_argument('dir', type=str)
args = parser.parse_args()

def find_all_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            yield os.path.join(root, file)

for filepath in find_all_files(args.dir):
    rate = {}
    move_len = 0
    toryo = False
    for line in open(filepath, 'r', encoding='utf-8', skiprows=8):
        line = line.strip()



# df = pd.read_csv("ryuousenkessyou1.kif", encoding="UTF-8", skiprows=7)
# df.head(200)