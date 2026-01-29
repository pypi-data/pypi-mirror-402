import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # 兼容部分旧版 matplotlib
from scipy.interpolate import griddata
from kevin_toolbox.patches.for_matplotlib.color import generate_color_list
from kevin_toolbox.patches.for_matplotlib.common_charts.utils import save_plot, save_record, get_output_path, \
    log_scaling
from kevin_toolbox.patches.for_matplotlib.variable import COMMON_CHARTS

__name = ":common_charts:plot_3d"


@COMMON_CHARTS.register(name=__name)
def plot_3d(data_s, title, x_name, y_name, z_name, cate_name=None, type_=("scatter", "smooth_surf"), output_dir=None,
            output_path=None, **kwargs):
    """
        绘制3D图
            支持：散点图、三角剖分曲面及其平滑版本
            
        
        参数：
            data_s:             <dict> 数据。
                                    形如 {<data_name>: <data list>, ...} 的字典
                                    需要包含 x、y、z 三个键值对，分别对应 x、y、z 轴的数据。
            title:              <str> 绘图标题。
            x_name:             <str> x 轴的数据键名。
            y_name:             <str> y 轴的数据键名。
            z_name:             <str> z 轴的数据键名。
            cate_name:          <str> 以哪个 data_name 作为数据点的类别。
            type_:              <str/list of str> 图表类型。
                                    目前支持以下取值，或者以下取值的列表：
                                        - "scatter"         散点图
                                        - "tri_surf"        三角曲面
                                        - "smooth_surf"     平滑曲面
                                    当指定列表时，将会绘制多个图表的混合。
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
            scatter_size:       <int> 散点大小，默认 30。
            cate_of_surf:       <str or list of str> 使用哪些类别的数据来绘制曲面。
                                    默认为 None，表示使用所有类别的数据来绘制曲面。
                                    仅当 cate_name 非 None 时该参数起效。
            tri_surf_cmap:      <str> 三角剖分曲面的颜色映射，默认 "viridis"。
            tri_surf_alpha:     <float> 三角剖分曲面的透明度，默认 0.6。
            smooth_surf_cmap:   <str> 平滑曲面的颜色映射，默认 "coolwarm"。
            smooth_surf_alpha:  <float> 平滑曲面的透明度，默认 0.6。
            smooth_surf_method: <str> 平滑的方法。
                                    支持以下取值：
                                        - "linear"
                                        - "cubic"
            view_elev:          <float> 视角中的仰角，默认 30。
            view_azim:          <float> 视角中的方位角，默认 45。
            x_log_scale,y_log_scale,z_log_scale:    <int/float> 对 x,y,z 轴数据使用哪个底数进行对数显示。
                                    默认为 None，此时表示不使用对数显示。
            x_ticks,...:        <int/list of float or int> 在哪个数字下添加坐标记号。
                                    默认为 None，表示不添加记号。
                                    当设置为 int 时，表示自动根据 x,y,z 数据的范围，选取等间隔选取多少个坐标作为记号。
            x_tick_labels,...:  <int/list> 坐标记号的label。
    """
    # 默认参数设置
    paras = {
        "dpi": 200,
        "suffix": ".png",
        "b_generate_record": False,
        "b_show_plot": False,
        "b_bgr_image": True,
        "scatter_size": 30,
        "cate_of_surf": None,
        "tri_surf_cmap": "viridis",
        "tri_surf_alpha": 0.6,
        "smooth_surf_cmap": "coolwarm",
        "smooth_surf_alpha": 0.6,
        "smooth_surf_method": "linear",
        "view_elev": 30,
        "view_azim": 45,
        "x_log_scale": None,
        "x_ticks": None,
        "x_tick_labels": None,
        "y_log_scale": None,
        "y_ticks": None,
        "y_tick_labels": None,
        "z_log_scale": None,
        "z_ticks": None,
        "z_tick_labels": None,
    }
    paras.update(kwargs)
    #
    _output_path = get_output_path(output_path=output_path, output_dir=output_dir, title=title, **kwargs)
    save_record(_func=plot_3d, _name=__name,
                _output_path=_output_path if paras["b_generate_record"] else None,
                **paras)
    data_s = data_s.copy()
    if isinstance(type_, str):
        type_ = [type_]
    #
    d_s = dict()
    ticks_s = dict()
    tick_labels_s = dict()
    for k in ("x", "y", "z"):
        d_s[k], ticks_s[k], tick_labels_s[k] = log_scaling(
            x_ls=data_s[eval(f'{k}_name')], log_scale=paras[f"{k}_log_scale"],
            ticks=paras[f"{k}_ticks"], tick_labels=paras[f"{k}_tick_labels"]
        )

    x, y, z = [d_s[i].reshape(-1) for i in ("x", "y", "z")]
    color_s = None
    cate_of_surf = None
    if cate_name is not None:
        cates = list(set(data_s[cate_name]))
        color_s = {i: j for i, j in zip(cates, generate_color_list(nums=len(cates)))}
        c = [color_s[i] for i in data_s[cate_name]]
        if paras["cate_of_surf"] is not None:
            temp = [paras["cate_of_surf"], ] if isinstance(paras["cate_of_surf"], str) else paras[
                "cate_of_surf"]
            cate_of_surf = [i in temp for i in data_s[cate_name]]
    else:
        c = "red"

    plt.clf()
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # 绘制数据点
    if "scatter" in type_:
        ax.scatter(x, y, z, s=paras["scatter_size"], c=c, depthshade=True)

    if cate_of_surf is not None:
        x, y, z = x[cate_of_surf], y[cate_of_surf], z[cate_of_surf]

    # 绘制基于三角剖分的曲面（不平滑）
    if "tri_surf" in type_:
        tri_surf = ax.plot_trisurf(x, y, z, cmap=paras["tri_surf_cmap"], alpha=paras["tri_surf_alpha"])

    # 构造规则网格，用于平滑曲面插值
    if "smooth_surf" in type_:
        grid_x, grid_y = np.mgrid[x.min():x.max():100j, y.min():y.max():100j]
        grid_z = griddata((x, y), z, (grid_x, grid_y), method=paras["smooth_surf_method"])
        # 绘制平滑曲面
        smooth_surf = ax.plot_surface(grid_x, grid_y, grid_z, cmap=paras["smooth_surf_cmap"],
                                      edgecolor='none', alpha=paras["smooth_surf_alpha"])
        # 添加颜色条以展示平滑曲面颜色与 z 值的对应关系
        cbar = fig.colorbar(smooth_surf, ax=ax, shrink=0.5, aspect=10)
        cbar.set_label(z_name, fontsize=12)

    # 设置坐标轴标签和图形标题
    ax.set_xlabel(x_name, fontsize=12)
    ax.set_ylabel(y_name, fontsize=12)
    ax.set_zlabel(z_name, fontsize=12)
    ax.set_title(title, fontsize=14)
    for i in ("x", "y", "z"):
        if ticks_s[i] is not None:
            getattr(ax, f'set_{i}ticks')(ticks_s[i])
            getattr(ax, f'set_{i}ticklabels')(tick_labels_s[i])

    # 调整视角
    ax.view_init(elev=paras["view_elev"], azim=paras["view_azim"])

    # 创建图例
    if "scatter" in type_ and cate_name is not None:
        plt.legend(handles=[
            plt.Line2D([0], [0], marker='o', color='w', label=i, markerfacecolor=j,
                       markersize=min(paras["scatter_size"], 5)) for i, j in color_s.items()
        ])

    return save_plot(plt=plt, output_path=_output_path, dpi=paras["dpi"], suffix=paras["suffix"],
                     b_bgr_image=paras["b_bgr_image"], b_show_plot=paras["b_show_plot"])


if __name__ == '__main__':
    # 示例用法：生成示例数据并绘制3D图像
    np.random.seed(42)
    num_points = 200
    data = {
        'x': np.random.uniform(-5, 5, num_points),
        'y': np.random.uniform(-5, 5, num_points),
        "c": np.random.uniform(-5, 5, num_points) > 0.3,
    }
    # 示例 z 值：例如 z = sin(sqrt(x^2+y^2))
    data['z'] = np.sin(np.sqrt(data['x'] ** 2 + data['y'] ** 2)) + 1.1
    plot_3d(data, x_name='x', y_name='y', z_name='z', cate_name="c", title="3D Surface Plot", z_log_scale=10, z_ticks=5,
            type_=("scatter"), output_dir="./temp")
