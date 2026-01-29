import matplotlib.pyplot as plt
import numpy as np
from kevin_toolbox.patches.for_matplotlib.common_charts.utils import save_plot, save_record, get_output_path
from kevin_toolbox.patches.for_matplotlib.variable import COMMON_CHARTS

__name = ":common_charts:plot_heatmap"


@COMMON_CHARTS.register(name=__name)
def plot_heatmap(matrix, title, column_label="Column Index", row_label="Row Index", output_dir=None, output_path=None,
                 **kwargs):
    """
        绘制矩阵热力图（Heatmap）

        参数：
            matrix:             <np.ndarray> 矩阵
            title:              <str>     图标题，同时用于保存文件名
            row_label:          <str> 行标签。
            column_label:       <str> 列标签。
            output_dir: <str or None>
            output_path: <str or None>

        其他可选参数（与 plot_scatters 保持一致）：
            dpi: <int>   默认 200
            suffix: <str> ".png" / ".jpg" / ".bmp"
            b_generate_record: 是否保存记录文件
            b_show_plot: 是否 plt.show()
            b_bgr_image: 返回 ndarray 时通道顺序是否为 bgr（默认 True）
    """

    paras = {
        "dpi": 200,
        "suffix": ".png",
        "b_generate_record": False,
        "b_show_plot": False,
        "b_bgr_image": True,
    }
    paras.update(kwargs)
    #
    _output_path = get_output_path(output_path=output_path, output_dir=output_dir, title=title, **kwargs)
    save_record(_func=plot_heatmap, _name=__name,
                _output_path=_output_path if paras["b_generate_record"] else None,
                **paras)

    plt.clf()
    plt.figure(figsize=(10, 8))

    plt.imshow(matrix, cmap='viridis', aspect='auto')
    plt.colorbar()
    plt.title(title)
    plt.xlabel(column_label)
    plt.ylabel(row_label)
    plt.tight_layout()

    return save_plot(plt=plt, output_path=_output_path, dpi=paras["dpi"], suffix=paras["suffix"],
                     b_bgr_image=paras["b_bgr_image"], b_show_plot=paras["b_show_plot"])


if __name__ == '__main__':
    import os

    A = np.random.randn(20, 30)

    plot_heatmap(
        matrix=A,
        title="test_plot_heatmap",
        output_dir=os.path.join(os.path.dirname(__file__), "temp")
    )
