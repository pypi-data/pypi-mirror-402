from kevin_toolbox.computer_science.algorithm.sampler import Reservoir_Sampler, Moving_Reservoir_Sampler, \
    Vanilla_Sampler


def count_duplicates(sampler):
    """验证重复项的出现是否符合统计规律（指数递减）"""
    sampler.clear()
    record = []
    for j in range(100):
        count = 0
        for i in range(100):
            sampler.add(i + j * 100)
            # print(rs.get())
            samples = sampler.get()
            if len(samples) > len(set(samples)):
                # 有重复
                count += 1
        record.append(count)
    return record


if __name__ == '__main__':
    print(f'test Moving_Reservoir_Sampler')
    mrs = Moving_Reservoir_Sampler(kernel_size=5, target_nums=3, b_allow_duplicates=True)
    for i in range(15):
        mrs.add(i)
        print(mrs.rs_old.samples, mrs.rs.samples)
        print(mrs.get())

    # 由于仅对 kernel_size 以内的历史序列进行采样，因此 duplicates 出现的概率不会随着总序列的长度增加而增加。
    # 而是应该稳定在 1-A_{5}^{3}/5^{3} = 0.52
    print(count_duplicates(mrs))

    print(f'test Reservoir_Sampler')
    rs = Reservoir_Sampler(target_nums=5, b_allow_duplicates=True)
    for i in range(10):
        rs.add(i)
        print(rs.get())

    # 应该呈现指数递减规律
    print(count_duplicates(rs))

    print(f'test Vanilla_Sampler')
    vs = Vanilla_Sampler(target_nums=5, b_allow_duplicates=True)
    for i in range(10):
        vs.add(i)
        print(vs.get())

    # 应该呈现指数递减规律
    print(count_duplicates(vs))
