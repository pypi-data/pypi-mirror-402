from kevin_toolbox.developing.temperate.my_iterator import My_Iterator

if __name__ == '__main__':
    a = My_Iterator([1, 2, 3, 4, 5])
    a.set_range(1, 3)
    print(len(a))
    for i in a:
        print(i)
    print(a[1])
    print(a[2])
