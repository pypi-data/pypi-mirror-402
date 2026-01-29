import os
import io
import numpy as np
from PIL import Image


def save_plot(plt, output_path, dpi=200, suffix=".png", b_bgr_image=False, b_show_plot=False, **kwargs):
    assert suffix in [".png", ".jpg", ".bmp"]

    if b_show_plot:
        plt.show()

    if output_path is None:
        buf = io.BytesIO()
        plt.savefig(buf, format=suffix.split(".")[-1].lower(), dpi=dpi)
        buf.seek(0)
        image = Image.open(buf).convert("RGB")
        image = np.array(image)
        buf.close()
        plt.close()
        if b_bgr_image:
            image = image[..., ::-1]
        return image
    else:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=dpi)
        plt.close()
        return output_path
