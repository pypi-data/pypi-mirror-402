from kevin_toolbox.patches.for_matplotlib.color import Color_Format, get_format


def hex_to_rgba(hex_color):
    hex_color = hex_color.lstrip('#')
    assert len(hex_color) in (6, 8), \
        f'hex_color should be 6 or 8 characters long (not including #). but got {len(hex_color)}'
    res = list(int(hex_color[i * 2:i * 2 + 2], 16) for i in range(len(hex_color) // 2))
    if len(res) == 4:
        res[3] /= 255
    return tuple(res)


def rgba_to_hex(rgba):
    assert len(rgba) in (3, 4), \
        f'rgba should be 3 or 4 elements long. but got {len(rgba)}'
    if len(rgba) == 4:
        rgba = list(rgba)
        rgba[3] = max(0, min(255, int(255 * rgba[3])))
    res = "#"
    for i in rgba:
        res += f'{i:02X}'
    return res


NAME_TO_HEX = {
    'blue': '#0000FF',
    'red': '#FF0000',
    'green': '#008000',
    'orange': '#FFA500',
    'purple': '#800080',
    'yellow': '#FFFF00',
    'brown': '#A52A2A',
    'pink': '#FFC0CB',
    'gray': '#808080',
    'olive': '#808000',
    'cyan': '#00FFFF'
}
HEX_TO_NAME = {v: k for k, v in NAME_TO_HEX.items()}


def natural_name_to_hex(name):
    global NAME_TO_HEX
    name = name.lower()
    assert name in NAME_TO_HEX, \
        f'{name} is not a valid color name.'
    return NAME_TO_HEX[name]


def hex_to_natural_name(hex_color):
    global HEX_TO_NAME
    hex_color = hex_color.upper()[:7]
    assert hex_color in HEX_TO_NAME, \
        f'{hex_color} does not has corresponding color name.'
    return HEX_TO_NAME[hex_color]


CONVERT_PROCESS_S = {
    (Color_Format.HEX_STR, Color_Format.NATURAL_NAME): hex_to_natural_name,  # (from, to): process
    (Color_Format.HEX_STR, Color_Format.RGBA_ARRAY): hex_to_rgba,
    (Color_Format.NATURAL_NAME, Color_Format.HEX_STR): natural_name_to_hex,
    (Color_Format.NATURAL_NAME, Color_Format.RGBA_ARRAY): lambda x: hex_to_rgba(natural_name_to_hex(x)),
    (Color_Format.RGBA_ARRAY, Color_Format.HEX_STR): rgba_to_hex,
    (Color_Format.RGBA_ARRAY, Color_Format.NATURAL_NAME): lambda x: hex_to_natural_name(rgba_to_hex(x))
}


def convert_format(var, output_format, input_format=None):
    """
        在各种颜色格式之间进行转换

        参数：
            var:
            input_format:       <str> 描述输入的格式。
                                    支持 HEX_STR、NATURAL_NAME、RGBA_ARRAY 等格式，
                                    默认为 None，此时将根据输入推断格式
            output_format:      <str/list of str> 输出的目标格式。
                                    当输入是一个 tuple/list 时，将输出其中任一格式，具体规则为：
                                        - 当 input_format 不在可选的输出格式中时，优先按照第一个输出格式进行转换。
                                            若转换失败，则按照第二个输出格式进行转换。依次类推。
                                        - 当 input_format 在可选的输出格式中时，不进行转换。
    """
    global CONVERT_PROCESS_S
    if input_format is None:
        input_format = get_format(var=var)
    input_format = Color_Format(input_format)
    if not isinstance(output_format, (list, tuple,)):
        output_format = [output_format]
    output_format = [Color_Format(i) for i in output_format]

    if input_format in output_format:
        return var
    else:
        for output_format_i in output_format:
            try:
                return CONVERT_PROCESS_S[(input_format, output_format_i)](var)
            except Exception as e:
                raise Exception(f'fail to convert {var} from {input_format} to {output_format}, beacause: {e}')


if __name__ == '__main__':
    print(hex_to_rgba('#FF57337F'))
    print(rgba_to_hex((255, 87, 51, 0.5)))
    print(natural_name_to_hex('pink'))
    print(convert_format(var='#FF57337F', input_format='hex_str', output_format='rgba_array'))
    print(convert_format(var="#0000FF", output_format="rgba_array"))
