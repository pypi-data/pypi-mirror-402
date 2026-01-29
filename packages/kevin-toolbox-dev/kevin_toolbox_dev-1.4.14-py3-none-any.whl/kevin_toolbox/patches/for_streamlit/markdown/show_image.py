import os
import streamlit as st
from kevin_toolbox.data_flow.file.markdown.link import find_links


def show_image(text, doc_dir=None):
    """
        对 st.markdown 中图片显示部分的改进，具有以下优点
            - 能够正确显示本地的图片，以 st.image 方式或者 base64 方式（待实现 TODO）
    """
    link_ls, part_slices_ls, link_idx_ls = find_links(text=text, b_compact_format=False, type_ls=["image"])
    for i, part_slices in enumerate(part_slices_ls):
        if i in link_idx_ls:
            link_s = link_ls.pop(0)
            st.image(image=os.path.join(doc_dir, link_s["target"]) if doc_dir else link_s["target"],
                     caption=link_s["name"] or link_s["title"])
        else:
            st.markdown(text[slice(*part_slices)])

# from PIL import Image
# from io import BytesIO
# import base64
#
# def convert_image_to_base64(file_path=None, image=None, output_format="png"):
#     """
#         将图片转为 base64 编码的字符串
#     """
#     assert output_format in ["png", "jpeg"]
#     if file_path:
#         image = Image.open(file_path)
#     assert image is not None
#     with BytesIO() as buffer:
#         image.save(buffer, 'png')  # or 'jpeg'
#         res = base64.b64encode(buffer.getvalue()).decode('utf-8')
#     return res
#
#
# if __name__ == "__main__":
#     image_path = "/home/SENSETIME/xukaiming/Desktop/gitlab_repos/face_liveness_datasets/deploy_for_streamlit/pages/test/test_data/images/7.jpg"
#     print(convert_image_to_base64(image_path))
