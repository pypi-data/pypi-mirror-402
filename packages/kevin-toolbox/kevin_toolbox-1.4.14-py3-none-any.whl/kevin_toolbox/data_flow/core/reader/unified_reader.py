from kevin_toolbox.data_flow.core.reader import Unified_Reader_Base, File_Iterative_Reader


class UReader(Unified_Reader_Base):

    def get_file_iterative_reader(self, file_path, chunk_size, **kwargs):
        return super().get_file_iterative_reader(file_path, chunk_size, **kwargs)

    def get_cache_manager(self, iterator, folder_path):
        return super().get_cache_manager(iterator, folder_path)

    def deal_data(self, data):
        return super().deal_data(data)


class Reader_for_files(UReader):
    """
        从 image_list.txt 中读取 images
            （images 与 features 是一一对应的）

        image_list.txt 的格式为：
            <str of image_path_0>
            ....

        得到的 images 格式为：
            shape = [sample_nums, 1]
            dtype = str
    """

    def get_file_iterative_reader(self, file_path, chunk_size, **kwargs):
        """
            如何迭代读取文件到内存
                要求返回一个按照 chunk_size 来迭代读取文件内容的生成器、迭代器（默认使用 File_Iterative_Reader）
        """
        reader = File_Iterative_Reader(file_path=file_path, chunk_size=chunk_size,
                                       pre_jump_size=kwargs.get("pre_jump_size",None),
                                       jump_size=kwargs.get("jump_size", None),
                                       drop=False, loop_num=1,
                                       convert_func=lambda x: np.array(x, dtype=str))
        return reader


if __name__ == '__main__':
    import numpy as np

    reader = UReader(var=np.ones((10, 1)))

    print(reader.read(5, 10).shape)
    print(reader.read([3, 3]).shape)
    print(reader.find(1))

    reader = UReader(file_path="test/test_data/test_data.txt", chunk_size=2, folder_path="./temp/233")

    print(reader.read(2, 7))
    # del reader

    # reader = UReader(folder_path="./temp/233", chunk_size=2)
    print(len(reader))

    print(reader.read(7, 10))
    print(reader.read([3, 3]))
    print(reader.shape)
    print(len(reader))

    for i in reader:
        print(i)

    print(reader.find('data/6/horse_race_pan/2132020102319002000161_43_4.bmp'))

    reader = Reader_for_files(file_path="test/test_data/test_data.txt", chunk_size=2, pre_jump_size=2, jump_size=2)

    for i in reader:
        print(2333, i)
    print(len(reader))
    # import pdb;
    #
    # pdb.set_trace()
    print(reader.read(100))
