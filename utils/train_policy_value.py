# マルチタスク学習での学習コード
# 方策ネットと価値ネットの学習用コードはほぼ同じ
# 異なる点はミニバッチデータ作成と順伝播

import numpy as np
import chainer
from chainer import cuda, Variable
from chainer import optimizers, serializers
import chainer.functions as F

from pydlshogi.common import *
from pydlshogi.network.policy_value import PolicyValueNetwork
from pydlshogi.features import *
from pydlshogi.read_kifu import *

import argparse
import random
import pickle
import os
import re

import logging

parser = argparse.ArgumentParser()
parser.add_argument('kifulist_train', type=str, help='train kifu list')
parser.add_argument('kifulist_test', type=str, help='test kifu list')
parser.add_argument('--batchsize', '-b', type=int, default=32, help='Number of positions in each mini-batch')
parser.add_argument('--test_batchsize', type=int, default=512, help='Number of positions in each test mini-batch')
parser.add_argument('--epoch', '-e', type=int, default=1, help='Number of epoch times')
parser.add_argument('--model', type=str, default='model/model_policy_value', help='model file name')
parser.add_argument('--state', type=str, default='model/state_policy_value', help='state file name')
parser.add_argument('--initmodel', '-m', default='', help='Initialize the model from given file')
parser.add_argument('--resume', '-r', default='', help='Resume the optimization from snapshot')
parser.add_argument('--log', default=None, help='log file path')
parser.add_argument('--lr', type=float, default=0.01, help='learning rate')
parser.add_argument('--eval_interval', '-i', type=int, default=1000, help='eval interval')
args = parser.parse_args()

logging.basicConfig(format='%(asctime)s\t%(levelname)s\t%(message)s', datefmt='%Y/%m/%d %H:%M:%S', filename=args.log, level=logging.DEBUG)

model = PolicyValueNetwork()
model.to_gpu()

optimizer = optimizers.SGD(lr=args.lr)
optimizer.setup(model)

# Init/Resume
if args.initmodel:
    logging.info('Load model from {}'.format(args.initmodel))
    serializers.load_npz(args.initmodel, model)
if args.resume:
    logging.info('Load optimizer state from {}'.format(args.resume))
    serializers.load_npz(args.resume, optimizer)

logging.info('read kifu start')
# 保存済みのpickleファイルがある場合、pickleファイルを読み込む
# train date
train_pickle_filename = re.sub(r'\..*?$', '', args.kifulist_train) + '.pickle'
if os.path.exists(train_pickle_filename):
    with open(train_pickle_filename, 'rb') as f:
        positions_train = pickle.load(f)
    logging.info('load train pickle')
else:
    positions_train = read_kifu(args.kifulist_train)

# test data
test_pickle_filename = re.sub(r'\..*?$', '', args.kifulist_test) + '.pickle'
if os.path.exists(test_pickle_filename):
    with open(test_pickle_filename, 'rb') as f:
        positions_test = pickle.load(f)
    logging.info('load test pickle')
else:
    positions_test = read_kifu(args.kifulist_test)

# 保存済みのpickleがない場合、pickleファイルを保存する
if not os.path.exists(train_pickle_filename):
    with open(train_pickle_filename, 'wb') as f:
        pickle.dump(positions_train, f, pickle.HIGHEST_PROTOCOL)
    logging.info('save train pickle')
if not os.path.exists(test_pickle_filename):
    with open(test_pickle_filename, 'wb') as f:
        pickle.dump(positions_test, f, pickle.HIGHEST_PROTOCOL)
    logging.info('save test pickle')
logging.info('read kifu end')

logging.info('train position num = {}'.format(len(positions_train)))
logging.info('test position num = {}'.format(len(positions_test)))

# mini batch
def mini_batch(positions, i, batchsize):
    mini_batch_data = []
    mini_batch_move = []
    mini_batch_win = []
    for b in range(batchsize):
        features, move, win = make_features(positions[i + b])
        mini_batch_data.append(features)
        mini_batch_move.append(move)
        mini_batch_win.append(win)

    return (Variable(cuda.to_gpu(np.array(mini_batch_data, dtype=np.float32))),
            Variable(cuda.to_gpu(np.array(mini_batch_move, dtype=np.int32))),
            Variable(cuda.to_gpu(np.array(mini_batch_win, dtype=np.int32).reshape((-1, 1)))))

def mini_batch_for_test(positions, batchsize):
    mini_batch_data = []
    mini_batch_move = []
    mini_batch_win = []
    for b in range(batchsize):
        features, move, win = make_features(random.choice(positions))
        mini_batch_data.append(features)
        mini_batch_move.append(move)
        mini_batch_win.append(win)

    return (Variable(cuda.to_gpu(np.array(mini_batch_data, dtype=np.float32))),
            Variable(cuda.to_gpu(np.array(mini_batch_move, dtype=np.int32))),
            Variable(cuda.to_gpu(np.array(mini_batch_win, dtype=np.int32).reshape((-1, 1)))))

# train
logging.info('start training')
itr = 0
sum_loss = 0
for e in range(args.epoch):
    positions_train_shuffled = random.sample(positions_train, len(positions_train))

    itr_epoch = 0
    sum_loss_epoch = 0
    for i in range(0, len(positions_train_shuffled) - args.batchsize, args.batchsize):
        x, t1, t2 = mini_batch(positions_train_shuffled, i, args.batchsize)

	# 順伝播の出力を変数二つで受け取る
        y1, y2 = model(x)

        model.cleargrads()

	#損失＝方策ネットの出力の損失+価値ネットの出力の損失
        loss = F.softmax_cross_entropy(y1, t1) + F.sigmoid_cross_entropy(y2, t2)
        loss.backward()
        optimizer.update()

        itr += 1
        sum_loss += loss.data
        itr_epoch += 1
        sum_loss_epoch += loss.data

        # print train loss and test accuracy
        if optimizer.t % args.eval_interval == 0:
            x, t1, t2 = mini_batch_for_test(positions_test, args.test_batchsize)
            y1, y2 = model(x)
            logging.info('epoch = {}, iteration = {}, loss = {}, accuracy = {}, {}'.format(
                optimizer.epoch + 1, optimizer.t, sum_loss / itr,
                F.accuracy(y1, t1).data, F.binary_accuracy(y2, t2).data))
            itr = 0
            sum_loss = 0

    # validate test data
    logging.info('validate test data')
    itr_test = 0
    sum_test_accuracy1 = 0
    sum_test_accuracy2 = 0
    for i in range(0, len(positions_test) - args.batchsize, args.batchsize):
        x, t1, t2 = mini_batch(positions_test, i, args.batchsize)
        y1, y2 = model(x)
        itr_test += 1
        sum_test_accuracy1 += F.accuracy(y1, t1).data
        sum_test_accuracy2 += F.binary_accuracy(y2, t2).data
    logging.info('epoch = {}, iteration = {}, train loss avr = {}, test accuracy = {}, {}'.format(
        optimizer.epoch + 1, optimizer.t, sum_loss_epoch / itr_epoch,
        sum_test_accuracy1 / itr_test, sum_test_accuracy2 / itr_test))
    
    optimizer.new_epoch()

logging.info('save the model')
serializers.save_npz(args.model, model)
logging.info('save the optimizer')
serializers.save_npz(args.state, optimizer)
