from mpl_toolkits.mplot3d import Axes3D  # 3d坐标系
import numpy as np
from .arrow3d import Arrow3D


def add_trajectory_3d(ax3d, points, draw_key_points=True, scale=None):
    """
        参数：
            ax3d:
            points:                 <np.array> 坐标点 shape [batch, 3]
            draw_key_points:        <boolean> 是否绘制关键点
            scale:                  <float> 放大系数
                                        不设定时，默认根据 points 推断得到的最小分辨率来设置。
    """
    assert isinstance(ax3d, (Axes3D,))
    points = np.asarray(points)
    assert len(points) >= 1 and points.ndim == 2 and points.shape[-1] == 3, \
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
        ax3d.add_artist(Arrow3D(*beg.tolist(), *(end - beg).tolist(),
                                arrowstyle="-|>", mutation_scale=int(15 * scale),
                                color="blue", alpha=0.5))
        # ax3d.quiver(*beg.tolist(), *(end - beg).tolist(), length=1, normalize=True)

    # 关键点
    if draw_key_points:
        ax3d.scatter3D(xs=points[:, 0], ys=points[:, 1], zs=points[:, 2],
                       marker='o', s=scale * 25,  # 散点的形状及大小
                       c="red", alpha=0.9,  # 散点的颜色及透明度
                       cmap=None)

    return ax3d
