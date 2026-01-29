import numpy as np
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from kevin_toolbox.patches.for_matplotlib.common_charts.utils import save_plot, save_record, get_output_path
from kevin_toolbox.patches.for_matplotlib.variable import COMMON_CHARTS

__name = ":common_charts:plot_confusion_matrix"


@COMMON_CHARTS.register(name=__name)
def plot_confusion_matrix(data_s, title, gt_name, pd_name, label_to_value_s=None, output_dir=None, output_path=None,
                          replace_zero_division_with=0, **kwargs):
    """
        计算并绘制混淆矩阵

        参数：
            data_s:             <dict> 数据。
                                    形如 {<data_name>: <data list>, ...} 的字典
            title:              <str> 绘图标题，同时用于保存图片的文件名。
            gt_name:            <str> 在 data_s 中表示真实标签数据的键名。
            pd_name:            <str> 在 data_s 中表示预测标签数据的键名。
            label_to_value_s:   <dict> 标签-取值映射字典。
                                    如 {"cat": 0, "dog": 1}）。
            output_dir: <str or None>
                图像保存的输出目录。如果同时指定了 output_path，则以 output_path 为准。
                若 output_dir 和 output_path 均未指定，则图像将直接通过 plt.show() 显示而不会保存到文件。

            output_dir:         <str> 图片输出目录。
            output_path:        <str> 图片输出路径。
                        以上两个只需指定一个即可，同时指定时以后者为准。
                        当只有 output_dir 被指定时，将会以 title 作为图片名。
                        若同时不指定，则直接以 np.ndarray 形式返回图片，不进行保存。
                        在保存为文件时，若文件名中存在路径不适宜的非法字符将会被进行替换。
            replace_zero_division_with:     <float> 在归一化混淆矩阵时，如果遇到除0错误的情况，将使用该值进行替代。
                                    建议使用 np.nan 或 0，默认值为 0。

        其他可选参数：
            dpi:                <int> 图像保存的分辨率。
            suffix:             <str> 图片保存后缀。
                                    目前支持的取值有 ".png", ".jpg", ".bmp"，默认为第一个。
            normalize:          <str or None> 指定归一化方式。
                                    可选值包括：
                                        "true"（按真实标签归一化）
                                        "pred"（按预测标签归一化）
                                        "all"（整体归一化）
                                    默认为 None 表示不归一化。
            b_return_cfm:       <bool> 是否在返回值中包含计算得到的混淆矩阵数据。
                                    默认为 False。
            b_generate_record:  <boolean> 是否保存函数参数为档案。
                                    默认为 False，当设置为 True 时将会把函数参数保存成 [output_path].record.tar。
                                    后续可以使用 plot_from_record() 函数或者 Serializer_for_Registry_Execution 读取该档案，并进行修改和重新绘制。
                                    该参数仅在 output_dir 和 output_path 非 None 时起效。
            b_show_plot:        <boolean> 是否使用 plt.show() 展示图片。
                                    默认为 False
            b_bgr_image:        <boolean> 以 np.ndarray 形式返回图片时，图片的channel顺序是采用 bgr 还是 rgb。
                                    默认为 True

        返回值：
            当 b_return_cfm 为 True 时，返回值可能为一个包含 (图像路径, 混淆矩阵数据) 的元组。
    """
    paras = {
        "dpi": 200,
        "suffix": ".png",
        "b_generate_record": False,
        "b_show_plot": False,
        "b_bgr_image": True,
        "normalize": None,  # "true", "pred", "all",
        "b_return_cfm": False,  # 是否输出混淆矩阵
    }
    paras.update(kwargs)
    #
    _output_path = get_output_path(output_path=output_path, output_dir=output_dir, title=title, **kwargs)
    save_record(_func=plot_confusion_matrix, _name=__name,
                _output_path=_output_path if paras["b_generate_record"] else None,
                **paras)
    data_s = data_s.copy()

    value_set = set(data_s[gt_name]).union(set(data_s[pd_name]))
    if label_to_value_s is None:
        label_to_value_s = {f'{i}': i for i in value_set}
    else:
        # assert all(i in value_set for i in label_to_value_s.values())
        pass
    # 计算混淆矩阵
    cfm = confusion_matrix(y_true=data_s[gt_name], y_pred=data_s[pd_name], labels=list(label_to_value_s.values()),
                           normalize=paras["normalize"])
    # replace with nan
    if paras["normalize"] is not None:
        if paras["normalize"] == "all":
            if cfm.sum() == 0:
                cfm[cfm == 0] = replace_zero_division_with
        else:
            check_axis = 1 if paras["normalize"] == "true" else 0
            temp = np.sum(cfm, axis=check_axis, keepdims=False)
            for i in range(len(temp)):
                if temp[i] == 0:
                    if check_axis == 0:
                        cfm[:, i] = replace_zero_division_with
                    else:
                        cfm[i, :] = replace_zero_division_with

    # 绘制混淆矩阵热力图
    plt.clf()
    plt.figure(figsize=(8, 6))
    sns.heatmap(cfm, annot=True, fmt='.2%' if paras["normalize"] is not None else 'd',
                xticklabels=list(label_to_value_s.keys()), yticklabels=list(label_to_value_s.keys()),
                cmap='viridis')

    plt.xlabel(f'{pd_name}')
    plt.ylabel(f'{gt_name}')
    plt.title(f'{title}')

    res = save_plot(plt=plt, output_path=_output_path, dpi=paras["dpi"], suffix=paras["suffix"],
                    b_bgr_image=paras["b_bgr_image"], b_show_plot=paras["b_show_plot"])

    if paras["b_return_cfm"]:
        return res, cfm
    else:
        return res


if __name__ == '__main__':
    import os

    # 示例真实标签和预测标签
    y_true = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 5])
    y_pred = np.array([0, 2, 1, 0, 2, 1, 0, 1, 1, 5])

    plot_confusion_matrix(
        data_s={'a': y_true, 'b': y_pred},
        title='test_plot_confusion_matrix', gt_name='a', pd_name='b',
        label_to_value_s={"A": 5, "B": 0, "C": 1, "D": 2, "E": 3},
        output_dir=os.path.join(os.path.dirname(__file__), "temp"),
        replace_zero_division_with=-1,
        normalize="all",
        b_generate_record=True
    )
