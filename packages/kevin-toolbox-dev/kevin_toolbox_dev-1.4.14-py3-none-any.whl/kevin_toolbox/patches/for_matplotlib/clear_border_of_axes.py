def clear_border_of_axes(ax):
    """
        用于清除 ax 中的坐标轴和 ticks
    """
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['left'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.spines['bottom'].set_color('none')
    ax.spines['top'].set_color('none')
    return ax


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    #
    fig, ax = plt.subplots()

    x = [1, 4]
    y = [1, 10]
    ax.plot(x, y)

    # 设置坐标轴的范围，以便更好地展示直线
    ax.set_xlim([0, 5])
    ax.set_ylim([0, 15])

    # 添加标题和坐标轴标签
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    clear_border_of_axes(ax)

    # 显示图形
    plt.show()
