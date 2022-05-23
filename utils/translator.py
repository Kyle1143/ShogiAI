# 日本語を英語へ変換
# 空白を消去
# kfkファイルのクリーニング用プログラム


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
	with open(filepath, 'r',encoding="utf-8") as f:

		text_a = re.sub('[ぁ-んァ-ン一-龥]', 'X', f.read())
		text_b = re.sub('<analysisScoreList>', '[', text_a)
		text_c = re.sub('</analysisScoreList>', ']', text_b)
#		text_d = text_a.replace(' ', '')

	with open(filepath, "w", encoding="utf-8") as f:
		f.write(text_c)