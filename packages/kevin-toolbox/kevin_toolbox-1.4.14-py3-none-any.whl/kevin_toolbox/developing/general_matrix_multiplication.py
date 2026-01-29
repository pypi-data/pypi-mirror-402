
def general_matrix_multiplication():
    """
        广义通用矩阵乘法操作
    """
    x = tf.cast(x, dtype=tf.float32)
    size = list(x.shape)
    pre_size, array_len, dims_of_point = size[:-2], size[-2], size[-1]

    # x_tile_lens [..., array_len * array_len, dims_of_point]
    x_tile_lens = tf.reshape(tf.tile(x, [1] * len(pre_size) + [array_len, 1]),
                             shape=pre_size + [array_len * array_len, dims_of_point])
    x_tile_dims = tf.reshape(tf.tile(x, [1] * len(pre_size) + [1, array_len]),
                             shape=pre_size + [array_len * array_len, dims_of_point])
    if return_type == "matrix":
        # distances [..., array_len * array_len, 1] ==> distance_matrix [..., array_len, array_len]
        distances = cal_distance(x_tile_dims, x_tile_lens)
        return tf.reshape(distances, shape=pre_size + [array_len, array_len])
    elif return_type == "array":
        mask = tf.linalg.band_part(
            tf.ones(shape=[array_len, array_len], dtype=tf.int8) - tf.eye(array_len, dtype=tf.int8),
            num_lower=0, num_upper=-1)  # 上三角1矩阵
        mask = tf.reshape(mask, shape=[-1])
        mask_index = tf.where(mask)
        # 将最后的两个维度提前
        index = list(range(len(x_tile_lens.shape)))
        target_index = index[-2:] + index[:-2]
        x_tile_lens = tf.transpose(x_tile_lens, perm=target_index)
        x_tile_dims = tf.transpose(x_tile_dims, perm=target_index)
        # 只保留上三角
        x_tile_lens = tf.gather_nd(params=x_tile_lens, indices=mask_index)
        x_tile_dims = tf.gather_nd(params=x_tile_dims, indices=mask_index)
        # 恢复维度顺序
        target_index = index[2:] + index[:2]
        x_tile_lens = tf.transpose(x_tile_lens, perm=target_index)
        x_tile_dims = tf.transpose(x_tile_dims, perm=target_index)
        # 计算距离
        distances = cal_distance(x_tile_dims, x_tile_lens)
        return distances[..., 0]
    elif return_type == "__test":
        print(tf.matmul(x, x, transpose_b=bool))
    else:
        raise TypeError