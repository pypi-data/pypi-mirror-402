import warnings
import matplotlib.pyplot as plt
from kevin_toolbox.patches.for_matplotlib.color import generate_color_list
from kevin_toolbox.patches.for_matplotlib.common_charts.utils import save_plot, save_record, get_output_path, \
    log_scaling
from kevin_toolbox.patches.for_matplotlib.variable import COMMON_CHARTS

__name = ":common_charts:plot_lines"


def log_scaling_for_x_y(data_s, x_name, y_names, **kwargs):
    d_s = dict()
    ticks_s = dict()
    tick_labels_s = dict()
    d_s["x"] = data_s.pop(x_name)
    d_s["y"] = []
    for k in y_names:
        d_s["y"].extend(data_s[k])
    for k in ("x", "y"):
        d_s[k], ticks_s[k], tick_labels_s[k] = log_scaling(
            x_ls=d_s[k], log_scale=kwargs[f"{k}_log_scale"],
            ticks=kwargs[f"{k}_ticks"], tick_labels=kwargs[f"{k}_tick_labels"],
            label_formatter=kwargs[f"{k}_label_formatter"]
        )
    temp = d_s.pop("y")
    count = 0
    for k in y_names:
        data_s[k] = temp[count:count + len(data_s[k])]
        count += len(data_s[k])
    data_s[x_name] = d_s["x"]
    return data_s, ticks_s, tick_labels_s


@COMMON_CHARTS.register(name=__name)
def plot_lines(data_s, title, x_name, y_name_ls=None, output_dir=None, output_path=None, **kwargs):
    """
        绘制折线图

        参数：
            data_s:             <dict> 数据。
                                    形如 {<data_name>: <data list>, ...} 的字典
            title:              <str> 绘图标题，同时用于保存图片的文件名。
            x_name:             <str> 以哪个 data_name 作为 x 轴。
            y_name_ls:          <list of str> 哪些数据视为需要被绘制的数据点。
                                    默认为 None，表示除 x_name 以外的数据都是需要绘制的。
                    例子： data_s={"step":[...], "acc_top1":[...], "acc_top3":[...]}
                        当 x_name="step" 时，将会以 step 为 x 轴绘制 acc_top1 和 acc_top3 的 bar 图。
            output_dir:         <str> 图片输出目录。
            output_path:        <str> 图片输出路径。
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
            color_ls:           <list> 用于绘图的颜色列表，默认根据数据序列个数自动生成。
            marker_ls:          <list of str> 折线图上各数据点的标记。
            linestyle_ls:       <list of str> 线型。
                                    默认值为 '-'，表示直线。
    """
    y_names = y_name_ls if y_name_ls else list(i for i in data_s.keys() if i != x_name)
    line_nums = len(y_names)
    paras = {
        "dpi": 200,
        "suffix": ".png",
        "b_generate_record": False,
        "b_show_plot": False,
        "b_bgr_image": True,
        "color_ls": generate_color_list(nums=line_nums),
        "marker_ls": None,
        "linestyle_ls": '-',
        #
        "x_label": f'{x_name}',
        "y_label": "value",
        "x_log_scale": None,
        "x_ticks": None,
        "x_tick_labels": None,
        "x_label_formatter": None,
        "y_log_scale": None,
        "y_ticks": None,
        "y_tick_labels": None,
        "y_label_formatter": None,
    }
    paras.update(kwargs)
    for k, v in paras.items():
        if k.endswith("_ls") and not isinstance(v, (list, tuple)):
            paras[k] = [v] * line_nums
    assert line_nums == len(paras["color_ls"]) == len(paras["marker_ls"]) == len(paras["linestyle_ls"])
    if "x_ticklabels_name" in paras:
        warnings.warn(f"{__name}: 'x_ticklabels_name' is deprecated, please use 'x_ticks' and 'x_tick_labels' instead.")
    #
    _output_path = get_output_path(output_path=output_path, output_dir=output_dir, title=title, **kwargs)
    save_record(_func=plot_lines, _name=__name,
                _output_path=_output_path if paras["b_generate_record"] else None,
                **paras)
    data_s = data_s.copy()
    #
    data_s, ticks_s, tick_labels_s = log_scaling_for_x_y(data_s=data_s, x_name=x_name, y_names=y_names, **paras)

    plt.clf()
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111)

    #
    x_all_ls = data_s.pop(x_name)
    data_s, temp = dict(), data_s
    for k, v_ls in temp.items():
        y_ls, x_ls = [], []
        for x, v in zip(x_all_ls, v_ls):
            if v is None:
                continue
            x_ls.append(x)
            y_ls.append(v)
        if len(x_ls) == 0:
            continue
        data_s[k] = (x_ls, y_ls)
    #
    for i, k in enumerate(y_names):
        x_ls, y_ls = data_s[k]
        ax.plot(x_ls, y_ls, label=f'{k}', color=paras["color_ls"][i], marker=paras["marker_ls"][i],
                linestyle=paras["linestyle_ls"][i])
    ax.set_xlabel(paras["x_label"])
    ax.set_ylabel(paras["y_label"])
    ax.set_title(f'{title}')
    for i in ("x", "y",):
        if ticks_s[i] is not None:
            getattr(ax, f'set_{i}ticks')(ticks_s[i])
            getattr(ax, f'set_{i}ticklabels')(tick_labels_s[i])
    # 显示图例
    plt.legend()

    return save_plot(plt=plt, output_path=_output_path, dpi=paras["dpi"], suffix=paras["suffix"],
                     b_bgr_image=paras["b_bgr_image"], b_show_plot=paras["b_show_plot"])


if __name__ == '__main__':
    import os

    plot_lines(
        data_s={
            'a': [0, 2, 3, 4, 5],
            'b': [5, 4, 3, 2, 1],
            'c': [1, 2, 3, 4, 5]},
        title='test_plot_lines', y_log_scale=2,
        x_name='a', output_dir=os.path.join(os.path.dirname(__file__), "temp")
    )
