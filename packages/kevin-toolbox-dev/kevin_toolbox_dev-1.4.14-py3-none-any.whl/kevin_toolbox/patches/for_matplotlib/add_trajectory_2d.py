import matplotlib.axes._axes as axes
import numpy as np


def add_trajectory_2d(ax, points, draw_key_points=True, scale=None):
    """
        参数：
            ax:
            points:                 <np.array> 坐标点 shape [batch, 2]
            draw_key_points:        <boolean> 是否绘制关键点
            scale:                  <float> 放大系数
                                        不设定时，默认根据 points 推断得到的最小分辨率来设置。
    """
    assert isinstance(ax, (axes.Axes,))
    points = np.asarray(points)
    assert len(points) >= 1 and points.ndim == 2 and points.shape[-1] == 2, \
        f'expected shape of points is [batch, 3], but got a {points.shape}'

    if scale is None:
        if len(points) > 1:
            temp = points.copy()
            temp[1:] -= temp[:-1]
            temp[0] -= points[-1]
            scale = np.min(np.sum(temp ** 2, axis=1)) ** 0.5
        else:
            scale = 1

    # 箭头
    for beg, end in zip(points[:-1], points[1:]):
        # ax.arrow(x=beg[0], y=beg[1], dx=end[0] - beg[0], dy=end[1] - beg[1],
        #          width=scale * 0.05, head_width=scale * 0.2, overhang=scale * 0.2,
        #          color="red", joinstyle="round",
        #          length_includes_head=True)
        # ax.quiver(*beg.tolist(), *(end - beg).tolist(), scale=5, width=0.01, headwidth=4, color="blue", alpha=0.5)
        ax.annotate("", xy=end, xytext=beg,
                    arrowprops=dict(width=scale * 0.5, headwidth=scale * 6, color="blue", alpha=0.5))

    # 关键点
    if draw_key_points:
        ax.scatter(x=points[:, 0], y=points[:, 1],
                   marker='o', s=scale * 25,  # 散点的形状及大小
                   c="red", alpha=0.9,  # 散点的颜色及透明度
                   cmap=None)

    return ax
