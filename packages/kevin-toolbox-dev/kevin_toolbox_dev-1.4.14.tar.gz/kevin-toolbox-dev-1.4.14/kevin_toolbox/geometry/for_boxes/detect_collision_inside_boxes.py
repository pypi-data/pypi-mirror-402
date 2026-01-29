import numpy as np


def detect_collision_inside_boxes(**kwargs):
    """
        基于分离轴定理，对 box（属于凸多边形），进行碰撞检测
            特点：
                - 时复杂度为 O( N*log(N) + M ) 其中 N 表示 box 的数量，M 表示发生碰撞的 pairs 数量。
                - 不需要像AABB包围盒和四叉树那样依赖树结构。
                - 可以配合 for_boxes.convert_from_coord_to_grid_index() 将 boxes 映射到格点阵列内，
                    从而实现多阶段碰撞检测的 Broad-Phase 和 Narrow-Phase。
            注意：
                - 我们将接触但不重合的情况也视为是碰撞。

        基本流程：
            1. 计算各个轴的碰撞概率
            2. 选取碰撞概率最小的轴开始进行 aixes_check
                （aixes_check 是基于分离轴定理，使用 Sort and Sweep 的方式进行的碰撞粗检测）
            3. 比较后续进行 aixes_check 和 fine_check 的时间成本，选择成本最低的方式进行迭代
                （fine_check 是对前面碰撞粗检测得到的潜在碰撞 box pairs 进行逐一精细准确的碰撞检测）

        参数：
            boxes:          <3 axis np.array> 需要检测的 box
                                shape [batch_size, 2, dimensions]，各个维度的意义为：
                                    batch_size： 有多少个 box
                                    2：          box的两个轴对称点
                                    dimensions： 坐标的维度
            complexity_correction_factor_for_aixes_check:   <float/integer> 进行 aixes_check 的复杂度修正系数
                                通过设置该系数，可以调整 aixes_check 与 fine_check 的复杂度比例。
                                - 该系数越大，计算得到 aixes_check 的复杂度越高，程序对于进行 fine_check 的偏好越大。
                                - 该系数越小，对进行 aixes_check 的偏好越大。
                                系数默认为 1.0，建议根据不同设备的实际情况（最好进行测试比较）进行调整。
            duplicate_records:  <boolean> 是否在输出的 collision_groups 的每个 box_id 下都记录一次碰撞。
                                    默认为 False，此时对于每个碰撞对，只会在其中一个 box_id 下的 set 中记录一次。
                                        至于碰撞对的具体分配方式则是随机的，不应作为后续流程依仗的特征。
                                    当设置为 True，则会重复记录。
        输出：
            collision_groups:   <dict of integers set> 检出的碰撞对。
                                其中的第 i 个 set 记录了 box_id==i 的 box 与其他哪些 box 存在碰撞
                                    比如：  collision_groups[0] = {1, 2} 表示0号 box 与1、2号 box 发生了碰撞
    """
    # 默认参数
    paras = {
        # 必要参数
        "boxes": None,
        #
        "complexity_correction_factor_for_aixes_check": 1.0,
        # setting for output
        "duplicate_records": False,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    paras["boxes"] = np.asarray(paras["boxes"])
    assert paras["boxes"].ndim == 3 and paras["boxes"].shape[1] == 2
    boxes = np.sort(paras["boxes"], axis=1)  # 对两个端点进行标准化
    #
    assert isinstance(paras["complexity_correction_factor_for_aixes_check"], (int, float,))
    correction_factor = paras["complexity_correction_factor_for_aixes_check"]

    # 1. 计算各个轴的碰撞概率
    #   - 通过指标 box在该轴上投影长度的均值/box的中点的均方差 估计各个轴上检出碰撞的概率，该指标越小，碰撞概率小。
    edge_lens = boxes[:, 1, :] - boxes[:, 0, :]
    indicators = np.mean(edge_lens, axis=0) / (np.std(edge_lens, axis=0) + 1e-10)  # 指标
    indicator_and_dims = [(indicator, dim) for dim, indicator in enumerate(indicators)]
    indicator_and_dims.sort(key=lambda x: x[0])  # [(indicator, dim)] sorted by indicator

    time_cost_for_aixes_check = len(boxes) * np.log(len(boxes)) * 2 * correction_factor

    # 2. 选取碰撞概率最小的轴开始进行 aixes_check
    #   - 从碰撞稀疏的轴开始进行碰撞检测，能够缩小每个碰撞group的size，从而降低在此基础上进行 fine_check 的算法复杂度。
    #   为及时从 aixes_check 切换到 fine_check 做好准备。
    last_collision_groups = None
    collision_groups = None
    for step, (_, dim) in enumerate(indicator_and_dims):
        # 2.1 获取各个box在该轴上的投影
        ticks = dict()
        for box_id in range(len(boxes)):
            (p_0, p_1) = boxes[box_id]
            beg, end = p_0[dim], p_1[dim]
            for tick in [beg, end]:
                if tick not in ticks:
                    ticks[tick] = list()
                ticks[tick].append(box_id)
        sort_ticks = sorted(ticks.items(), key=lambda x: x[0])

        # 2.2 检测潜在的碰撞 pairs
        #   - 只要轴上的投影有重合，就视为潜在的碰撞。
        meet_beg_ids = set()
        # collision_groups 中的第 i 个列表记录了 box_id==i 在轴上的投影与其他哪些 box 存在碰撞
        # 例如 collision_groups[5] = {6, 1} 表示5号框与6、1号框发生了碰撞
        collision_groups = dict()
        for k, v_ls in sort_ticks:
            # 将 meet_end_id_ls 的生成与 collision_groups 的生成分离开来是为了适应 接触但不重合的情况 和 box 体积为0的情况
            meet_end_id_ls = list()
            for v in v_ls:
                if v in meet_beg_ids:
                    # meet the end
                    meet_end_id_ls.append(v)
                else:
                    # new beg
                    meet_beg_ids.add(v)
            # 保证每次碰撞只被记录最多一次
            for v in meet_end_id_ls:
                meet_beg_ids.remove(v)
                collision_groups[v] = meet_beg_ids.copy()

        # 2.3 根据本次检测结果，剔除之前检测中的疑似碰撞 pairs
        if step == 0:
            last_collision_groups = collision_groups
        else:
            # 3. 比较后续进行 aixes_check 和 fine_check 的时间成本，选择成本最低的方式进行迭代
            time_cost_for_fine_check = sum([len(g) for g in collision_groups.values()])
            if time_cost_for_aixes_check * (boxes.shape[-1] - 1 - step) > time_cost_for_fine_check:
                # 进行 fine_check 的时间成本更低
                # 直接进行一次 fine_check 就可以得到最终结果，跳出循环
                for i, j_set in collision_groups.items():
                    true_collisions = set()
                    for j in j_set:
                        # intersection
                        beg = np.maximum(boxes[i][0], boxes[j][0])
                        end = np.minimum(boxes[i][1], boxes[j][1])
                        if (end - beg >= 0).all():  # 对于接触但不重合的情况，也视为碰撞
                            true_collisions.add(j)
                    collision_groups[i] = true_collisions
                break
            else:
                # 进行 aixes_check 的时间成本更低
                # 合并之前的 aixes_check 结果 last_collision_groups，然后继续下次循环
                for i, j_set in collision_groups.items():
                    for j in j_set.copy():
                        if j in last_collision_groups[i] or i in last_collision_groups[j]:
                            # 两边都检测出碰撞
                            pass
                        else:
                            j_set.remove(j)
                last_collision_groups = collision_groups

    #
    if paras["duplicate_records"]:
        for i, j_set in collision_groups.items():
            for j in j_set:
                collision_groups[j].add(i)
    for i in list(collision_groups.keys()):
        if len(collision_groups[i]) == 0:
            collision_groups.pop(i)

    return collision_groups
