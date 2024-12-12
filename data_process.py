import json
import os
import shutil
from random import shuffle
data_dir = './logs/some examples'
data_file = [data_dir + '/' + map_name for map_name in os.listdir(data_dir)]
def remove_empty():
    num = 0
    for f in data_file:
        if len(os.listdir(f)) == 0:
            num +=1
            shutil.rmtree(f)
    print(num)
data_train = dict()
data_dev = dict()
data_test = dict()
num = 0
num_train = 820
num_dev = 102
num_test = 102
len_train_inst = 0
len_dev_inst = 0
len_test_inst = 0
len_train_act = 0
len_dev_act = 0
len_test_act = 0
shuffle(data_file)
for f in data_file:
    map_file = os.path.basename(f).split('_')[0]
    data = json.load(open(f + '/sample.json'))
    data['map'] = map_file
    num += 1
    if num <= num_train:
        data_train[str(num)] = data
        len_train_inst += len(data['inst'])
        len_train_act += len(data['0']['act'])
    elif num <= num_train + num_dev:
        data_dev[str(num)] = data
        len_dev_inst += len(data['inst'])
        len_dev_act += len(data['0']['act'])
    else:
        data_test[str(num)] = data
        len_test_inst += len(data['inst'])
        len_test_act += len(data['0']['act'])
print('average train: ', len_train_inst/num_train, len_train_act/num_train, '\n')
print('average dev: ', len_dev_inst/num_dev, len_dev_act/num_dev, '\n')
print('average test: ', len_test_inst/num_test, len_test_act/num_test, '\n')
print('average all: ', (len_train_inst + len_dev_inst + len_test_inst)/1024, (len_train_act + len_dev_act + len_test_act)/1024, '\n')
with open("logs" + "/train.json", 'w', encoding="utf8") as f_in:
    json.dump(data_train, f_in, indent=4, ensure_ascii=False)

with open("logs" + "/dev.json", 'w', encoding="utf8") as f_in:
    json.dump(data_dev, f_in, indent=4, ensure_ascii=False)

with open("logs" + "/test.json", 'w', encoding="utf8") as f_in:
    json.dump(data_test, f_in, indent=4, ensure_ascii=False)