def generate_list(var, indent=0):
    doc = ""
    if isinstance(var, (dict,)):
        for key, value in var.items():
            if isinstance(value, (dict, list,)):
                doc += f'{" " * indent}- {key}\n'
                doc += generate_list(value, indent + 2)
            else:
                doc += f'{" " * indent}- {key}: {value}\n'
    elif isinstance(var, (list,)):
        for value in var:
            if isinstance(value, (dict, list,)):
                doc += f'{" " * indent}- \n'
                doc += generate_list(value, indent + 2)
            else:
                doc += f'{" " * indent}- {value}\n'
    return doc


if __name__ == '__main__':
    # 嵌套字典数据
    nested_dict = {
        'Category 1': {
            'Item 1': [1, 2, 3],
            'Item 2': 20
        },
        'Category 2': {
            'Item 3': 30,
            'Item 4': 40
        }
    }

    # 生成Markdown列表
    markdown_list = generate_list(nested_dict)

    print(markdown_list)
