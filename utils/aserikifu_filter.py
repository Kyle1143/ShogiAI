# 評価値の逆転している棋譜を抽出するプログラム
# 評価値の差が800以上
# 先手：先ー後 >= 800
# 後手：後ー先 >= 800

import argparse
import os
import re
import statistics
import math

parser = argparse.ArgumentParser()
parser.add_argument('dir', type=str)
args = parser.parse_args()

def find_all_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            yield os.path.join(root, file)

nomal_kifu_count = 0
kifu_count = 0
current_str = None
input = []	# 評価値を記録
move_index = 0	# 評価値の出力回数
panic_index = 0	# 評価値の前後の差
move_len = 0
kifu_asericount = False
toryo = False

for filepath in find_all_files(args.dir):
    for line in open(filepath, 'r', encoding='utf-8'):
        line = line.strip()
        # line = line.strip()
        # ファイルを開いた後、文字列を最後まで読み込む(ここ)
        # for line in csa_str.split('\n'):
        # <score>の行を発見する(空白が6マスあるためline[6]から始めるかも)
        if line[:1] == '+' or line[:1] == '-':
            move_len += 1
        if line == '%TORYO':
            toryo = True
        if line[:1] == '*':
            move_index += 1	# 評価値の記録の回数
            current_str = str(line)	# *x*の文字列をコピー
            m = re.search('*(.+?)*', current_str) 	# 評価値をゲット
            # print('score :', move_index)
            if m:
                found = m.group(1)
                input[move_index] = int(m.group(1))	# 評価値を数値としてゲット
               # print('move index :', move_index)
               # print('value :', input[move_index])
            if move_index > 1:
                if input[move_index] > 0 and input[move_index -1] > 0:	# 評価値が正か負で判別し、前の評価値も
                    panic_index = input[move_index -1] - input[move_index]
                    if math.fabs(panic_index) > 800:
                        kifu_asericount = True
                elif input[move_index] < 0 and input[move_index -1] < 0:
                    panic_index = input[move_index -1] - input[move_index]
                    if math.fabs(panic_index) > 800:
                        kifu_asericount = True
                elif input[move_index] > 0 and input[move_index -1] < 0:
                    panic_index = input[move_index -2] + input[move_index]
                    if math.fabs(panic_index) > 800:
                        kifu_asericount = True
                elif input[move_index] < 0 and input[move_index -1] > 0:
                    panic_index = input[move_index -2] + input[move_index]
                    if math.fabs(panic_index) > 800:
                        kifu_asericount = True
    if not toryo or kifu_asericount:
        kifu_count += 1
        os.remove(filepath)
    else:
        nomal_kifu_count += 1
    
print('nomal_kifu count :', nomal_kifu_count)
print('aserikifu count :', kifu_count)
print('kifu asericount :', kifu_asericount)
print('toryo :', toryo)
# print('rate mean : {}'.format(statistics.mean(rates)))
# print('rate median : {}'.format(statistics.median(rates)))
# print('rate max : {}'.format(max(rates)))
# print('rate min : {}'.format(min(rates)))

