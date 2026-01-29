import os
import time
import torch
import random
import numpy as np

from kevin_toolbox.machine_learning.dataset.face import verification
from kevin_toolbox.data_flow.core.reader import Unified_Reader_Base


def get_fail_case_from_iterator(**kwargs):
    """
        接受数据集的 iterator，然后在给定的 threshold 下挑出 false positive 和 false negative cases，
            当 fail cases 的数量达到目标值时，停止并返回

        选取 fail cases 相关的参数：
            threshold：              <float> 阈值
                                        作为选取 fail cases 的标准是：
                                            false positive：     score > threshold and label == False
                                            false negative：     score < threshold and label == True
            lower_bound：            <integer> 至少选取多少个 false positive / false negative cases
                                        默认为None
            upper_bound：            <integer> 至多选取多少个 false positive / false negative cases
                                        默认为None，亦即只要满足下界即可

        多进程相关的参数
            world_size:             <integer>
            rank:                   <integer>
                        （设定后，将只统计第 n 个数据集，其中 n 满足 n % world_size == rank）

        控制输出相关的参数：
            verbose：                <boolean> 是否打印过程信息

        返回：
            fp_db：                  <dict> 过滤出来的 false positive cases 部分的数据集
            fn_db：                  <dict> 过滤出来的 false negative cases 部分的数据集
    """
    # 默认参数
    paras = {
        # 数据集相关
        "iterator": None,
        # 选取 fail cases 相关
        "threshold": None,
        "lower_bound": None,
        "upper_bound": None,
        # 多进程相关
        "world_size": 1,
        "rank": 0,
        # 控制输出
        "verbose": True,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    # 数据集相关
    assert paras["iterator"] is not None
    # 选取 fail cases 相关
    assert paras["threshold"] is not None
    lower_bound = paras["lower_bound"]
    upper_bound = paras["upper_bound"]
    assert lower_bound is None or (
            isinstance(lower_bound, (int,)) and
            lower_bound > 0)
    assert upper_bound is None or (
            isinstance(upper_bound, (int,)) and
            (lower_bound is None or upper_bound >= lower_bound))
    # 多进程相关
    assert isinstance(paras["world_size"], (int,)) and paras["world_size"] > 0
    assert isinstance(paras["rank"], (int,)) and 0 <= paras["rank"] < paras["world_size"]

    """
    选取
    """

    count = 0
    beg_time = time.perf_counter()
    index_ls = [i for i in range(len(paras["iterator"])) if i % paras["world_size"] == paras["rank"]]
    index_ls = random.sample(index_ls, k=len(index_ls))
    fp_db, fn_db = dict(), dict()
    for i in index_ls:
        #
        db = paras["iterator"][i]
        # false positive cases
        cond_fp = ((db["scores"] > paras["threshold"]) & (db["labels"] == 0)).reshape(-1)
        # false negative cases
        cond_fn = ((db["scores"] < paras["threshold"]) & (db["labels"] == 1)).reshape(-1)
        for key, value in db.items():
            if key in fp_db:
                fp_db[key] = np.concatenate([fp_db[key], db[key][cond_fp]])
                fn_db[key] = np.concatenate([fn_db[key], db[key][cond_fn]])
            else:
                fp_db[key] = db[key][cond_fp]
                fn_db[key] = db[key][cond_fn]
        #
        if lower_bound is None:
            rate_n = 0
        else:
            rate_n = min(len(fp_db.get("labels", [])), len(fn_db.get("labels", []))) / lower_bound
            if rate_n > 1:
                break
        #
        if paras["verbose"]:
            count += 1
            rate = max(count / len(index_ls), rate_n)
            time_gap = time.perf_counter() - beg_time
            print(f"--world_size {paras['world_size']} --rank {paras['rank']}\n"
                  f"\t progress rate: {rate * 100}% \t eta: {time_gap / rate / 60 / 60 * (1 - rate)} hours")

    #
    if upper_bound is not None:
        for db in [fp_db, fn_db]:
            db_size = len(list(db.values())[0])
            if db_size > upper_bound:
                index = random.sample(range(db_size), upper_bound)
                for key, value in db.items():
                    db[key] = value[index]
            else:
                continue

    return fp_db, fn_db
