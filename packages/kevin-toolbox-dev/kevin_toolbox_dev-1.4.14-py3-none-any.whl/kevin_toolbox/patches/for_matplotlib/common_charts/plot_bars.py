import matplotlib.pyplot as plt
from kevin_toolbox.computer_science.algorithm import for_seq
from kevin_toolbox.patches.for_matplotlib.common_charts.utils import save_plot, save_record, get_output_path
from kevin_toolbox.patches.for_matplotlib.variable import COMMON_CHARTS

__name = ":common_charts:plot_bars"


@COMMON_CHARTS.register(name=__name)
def plot_bars(data_s, title, x_name, output_dir=None, output_path=None, **kwargs):
    """
        绘制条形图

        参数：
            data_s:             <dict> 数据。
                                    形如 {<data_name>: <data list>, ...} 的字典
            title:              <str> 绘图标题。
            x_name:             <str> 以哪个 data_name 作为 x 轴。
                                    其余数据视为需要被绘制的数据点。
                    例子： data_s={"step":[...], "acc_top1":[...], "acc_top3":[...]}
                        当 x_name="step" 时，将会以 step 为 x 轴绘制 acc_top1 和 acc_top3 的 bar 图。
            x_label:            <str> x 轴的标签名称。
                                    默认与指定的 x_name 相同。
            y_label:            <str> y 轴的标签名称。
                                    默认为 "value"。
            output_dir:         <str or None> 图片输出目录。
            output_path:        <str or None> 图片输出路径。
                        以上两个只需指定一个即可，同时指定时以后者为准。
                        当只有 output_dir 被指定时，将会以 title 作为图片名。
                        若同时不指定，则直接以 np.ndarray 形式返回图片，不进行保存。
                        在保存为文件时，若文件名中存在路径不适宜的非法字符将会被进行替换。

        其他可选参数：
            dpi:                <int> 保存图像的分辨率。
                                    默认为 200。
            suffix:             <str> 图片保存后缀。
                                    目前支持的取值有 ".png", ".jpg", ".bmp"，默认为第一个。
            b_generate_record:  <boolean> 是否保存函数参数为档案。
                                    默认为 False，当设置为 True 时将会把函数参数保存成 [output_path].record.tar。
                                    后续可以使用 plot_from_record() 函数或者 Serializer_for_Registry_Execution 读取该档案，并进行修改和重新绘制。
                                    该参数仅在 output_dir 和 output_path 非 None 时起效。
            b_show_plot:        <boolean> 是否使用 plt.show() 展示图片。
                                    默认为 False
            b_bgr_image:        <boolean> 以 np.ndarray 形式返回图片时，图片的channel顺序是采用 bgr 还是 rgb。
                                    默认为 True

        返回值：
            若 output_dir 非 None，则返回图像保存的文件路径。
    """
    assert x_name in data_s and len(data_s) >= 2
    paras = {
        "x_label": f'{x_name}',
        "y_label": "value",
        "dpi": 200,
        "suffix": ".png",
        "b_generate_record": False,
        "b_show_plot": False,
        "b_bgr_image": True,
    }
    paras.update(kwargs)
    #
    _output_path = get_output_path(output_path=output_path, output_dir=output_dir, title=title, **kwargs)
    save_record(_func=plot_bars, _name=__name, _output_path=_output_path if paras["b_generate_record"] else None,
                **paras)
    data_s = data_s.copy()

    plt.clf()
    #
    x_all_ls = data_s.pop(x_name)
    #
    for i, (k, y_ls) in enumerate(data_s.items()):
        if i == 0:
            plt.bar([j - 0.1 for j in range(len(x_all_ls))], y_ls, width=0.2, align='center', label=k)
        else:
            plt.bar([j + 0.1 for j in range(len(x_all_ls))], y_ls, width=0.2, align='center', label=k)

    plt.xlabel(paras["x_label"])
    plt.ylabel(paras["y_label"])
    temp = for_seq.flatten_list([list(i) for i in data_s.values()])
    y_min, y_max = min(temp), max(temp)
    plt.ylim(max(min(y_min, 0), y_min - (y_max - y_min) * 0.2), y_max + (y_max - y_min) * 0.1)
    plt.xticks(list(range(len(x_all_ls))), labels=x_all_ls)
    plt.title(f'{title}')
    # 显示图例
    plt.legend()

    return save_plot(plt=plt, output_path=_output_path, dpi=paras["dpi"], suffix=paras["suffix"],
                     b_bgr_image=paras["b_bgr_image"], b_show_plot=paras["b_show_plot"])


if __name__ == '__main__':
    import os

    plot_bars(data_s={
        'a': [1.5, 2, 3, 4, 5],
        'b': [5, 4, 3, 2, 1],
        'c': [1, 2, 3, 4, 5]},
        title='test_plot_bars', x_name='a', output_dir=os.path.join(os.path.dirname(__file__), "temp"),
        b_generate_record=True
    )
