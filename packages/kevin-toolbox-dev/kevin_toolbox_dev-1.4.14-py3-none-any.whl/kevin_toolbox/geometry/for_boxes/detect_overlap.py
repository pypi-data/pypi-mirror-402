from kevin_toolbox.geometry import for_boxes
import copy
import numpy as np


class Node:
    def __init__(self):
        # 用矢量描述
        self.description = dict(
            by_item_ids=dict(
                difference=set(),
                intersection=set(),
            ),
            by_boxes=None,
        )


def detect_overlap(**kwargs):
    """
        在将 boxes_ls 中的每个 boxes 视为一个 item，检测所有 item 之间的重叠区域

        参数：
            boxes_ls:       <3 axis np.array> 需要检测的 item
                                each boxes inside the list is an np.array with shape [batch_size, 2, dimensions]
                                各个维度的意义为：
                                    batch_size： 有多少个 box
                                    2：          box的两个轴对称点
                                    dimensions： 坐标的维度
        输出：
            node_ls:        <list of Node> 由于重叠分割出的不同区域
                                每个区域由一个 node 表示，其中：
                                    node.description["by_item_ids"]["intersection"]     <set of item_id> 这个区域是由哪些 item 相交而成的
                                    node.description["by_item_ids"]["difference"]       <set of item_id> 在上面交集的基础上，应该减去哪些 item
                                    node.description["by_boxes"]                        <boxes> 该区域由哪些 box 组成
                                可见 node.description["by_item_ids"] 描述了该区域的“来源”，
                                node.description["by_boxes"] 描述了该区域的形状。
                注意：
                    - 将排除所有体积为0的区域
                    - node_ls 中除了 item 之间的重叠区域，也记录了各个 item 的独有区域
    """
    # 默认参数
    paras = {
        # 必要参数
        "boxes_ls": None,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    assert isinstance(paras["boxes_ls"], (list,))
    boxes_ls = []
    for boxes in paras["boxes_ls"]:
        if boxes is None or for_boxes.cal_area(boxes=boxes) == 0:
            boxes_ls.append(None)
        else:
            boxes_ls.append(boxes)

    # 计算碰撞情况
    collision_groups = for_boxes.detect_collision(boxes_ls=boxes_ls, complexity_correction_factor_for_aixes_check=1.0,
                                                  duplicate_records=True)
    # 按照潜在的包含关系进行排序
    # 目标：保证 collision_groups 中后一个 id 指向的 item 不可能被之前的包含
    # 条件：
    #   - （充分条件）如果两个 item 之间具有包含关系，比如 item_0 included by item_1，那么必然有 item_0 相关的碰撞 pairs 数量少于 item_1 的。
    #       如果将配装关系看做 graph，则应该按 节点度数 进行排序，最大度数在前。
    #   - （必要条件）比较两个 item 的外切 box 的体积，体积大的在前。
    #       （这个条件相较于上一个更加严格，但是由于该条件需要计算面积，代价较大，因此可以先使用第一个条件进行初筛以减少计算量，
    #       但是为什么我不这样做呢？因为我懒，完毕。）
    #   - （改进的必要条件）上面的条件有可能出现体积为0的情况，尤其是对于高维的 box 而言。此时无法保证排序。
    #       因此改为对外切 box 的每条边的边长进行比较。
    sorted_collisions = [(k, v_ls) for k, v_ls in collision_groups.items()]
    sorted_collisions.sort(
        key=lambda x: tuple(np.max(boxes_ls[x[0]][:, 1, :], axis=0) - np.min(boxes_ls[x[0]][:, 0, :], axis=0)),
        reverse=True)

    # 为所有 item 创建 node
    item_node_ls = []
    input_node_ls = [None] * len(boxes_ls)
    output_node_ls = []
    ids = set(collision_groups.keys())
    for i, boxes in enumerate(boxes_ls):
        node = Node()
        node.description["by_item_ids"]["intersection"].add(i)
        node.description["by_boxes"] = boxes
        item_node_ls.append(node)
        if i in ids:
            # 有碰撞，需要计算
            input_node_ls[i] = node
        else:
            # 完全没有碰撞，可以直接输出
            if boxes is not None:
                output_node_ls.append(node)

    recursion(collisions=sorted_collisions, input_node_ls=input_node_ls, output_node_ls=output_node_ls)

    return output_node_ls


def recursion(collisions, input_node_ls, output_node_ls):
    if len(collisions) == 0:
        return
    k, v_ls = collisions[0]

    # 1. 处理 items[k]
    node = copy.deepcopy(input_node_ls[k])
    #
    boxes_ls = [node.description["by_boxes"]]
    boxes_ls.extend([input_node_ls[v].description["by_boxes"] for v in v_ls])
    binary_operation_ls = ["diff"] * (len(boxes_ls) - 1)
    res_boxes = for_boxes.boolean_algebra(boxes_ls=boxes_ls, binary_operation_ls=binary_operation_ls)
    #
    node.description["by_item_ids"]["difference"].update(v_ls)
    node.description["by_boxes"] = res_boxes

    if res_boxes is not None:
        output_node_ls.append(node)

    # 2. 处理 items[k] 内
    # items[v] intersect with items[k]
    # 构建 node_ls
    inner_node_ls = [None] * len(input_node_ls)
    included_box_ids = set()  # 用于记录被 items[k] 包含了的 items[v]，被包含的 items[v] 将不参与到后续的“处理 items[k] 外”流程
    for v in v_ls:
        res_boxes = for_boxes.boolean_algebra(
            boxes_ls=[input_node_ls[k].description["by_boxes"], input_node_ls[v].description["by_boxes"]],
            binary_operation_ls=["and"]
        )
        #
        if for_boxes.boolean_algebra(
                boxes_ls=[input_node_ls[v].description["by_boxes"], res_boxes],
                binary_operation_ls=["diff"]
        ) is None:
            # items[k] 包含了 items[v]
            # 第 v 个 item 发生的碰撞全部都在第 k 个 item 内
            # 因此后续不需要计算位于 items[k] 以外的 items[v] 的残余部分与其他 items 的碰撞情况。
            # 注意：此处不能通过 交集的体积 是否等于 被减数的体积 来判断包含关系，因为可能存在某个维度边长大小为0，而导致所有体积都为0的情况。
            included_box_ids.add(v)
        # intersection
        node = copy.deepcopy(input_node_ls[v])
        # 相交部分仅需考量两个节点都有的 difference
        node.description["by_item_ids"]["difference"].intersection_update(
            input_node_ls[k].description["by_item_ids"]["difference"])
        #
        node.description["by_item_ids"]["intersection"].add(k)
        node.description["by_boxes"] = res_boxes
        inner_node_ls[v] = node
    # 构建 collisions
    inner_collisions = []
    for i, j_ls in collisions:
        if i in v_ls:
            inner_collisions.append((i, j_ls.difference({k}).intersection(v_ls)))
    # 递归处理
    recursion(collisions=inner_collisions, input_node_ls=inner_node_ls, output_node_ls=output_node_ls)

    # 3. 处理 items[k] 外
    # items[v] reduced by items[k]
    # 构建 node_ls 和 collisions
    outer_node_ls = [None] * len(input_node_ls)
    outer_collisions = []
    need_to_be_excluded = included_box_ids.union({k})
    for i, j_ls in collisions:
        if i in need_to_be_excluded:
            continue
        outer_node_ls[i] = input_node_ls[i]
        outer_collisions.append((i, j_ls.difference(need_to_be_excluded)))
    for v in v_ls.difference(need_to_be_excluded):
        res_boxes = for_boxes.boolean_algebra(
            boxes_ls=[outer_node_ls[v].description["by_boxes"], input_node_ls[k].description["by_boxes"]],
            binary_operation_ls=["diff"]
        )
        #
        outer_node_ls[v].description["by_item_ids"]["difference"].add(k)
        outer_node_ls[v].description["by_boxes"] = res_boxes
    # 递归处理
    recursion(collisions=outer_collisions, input_node_ls=outer_node_ls, output_node_ls=output_node_ls)


if __name__ == '__main__':
    from test.test_data.data_1 import boxes

    # boxes = boxes[[0, 1, 2, 3], ...]
    print(boxes.shape)

    output_node_ls = detect_overlap(boxes_ls=[box.reshape(1, 2, box.shape[-1]) for box in boxes])

    counter = 0
    print(len(output_node_ls))
    for node in output_node_ls:
        print(node.description)
        if node.description["by_boxes"] is not None:
            counter += len(node.description["by_boxes"])
    print(counter)
