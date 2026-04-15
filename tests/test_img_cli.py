import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

from PIL import Image

from img_cli import convert_image, infer_output_format, main


class ImgCliTests(unittest.TestCase):
    def test_infer_output_format_from_extension(self):
        self.assertEqual(infer_output_format("example.jpg"), "JPEG")
        self.assertEqual(infer_output_format("example.png"), "PNG")

    def test_convert_image_saves_new_format(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, "input.png")
            output_path = os.path.join(tmp_dir, "output.jpg")

            Image.new("RGBA", (20, 20), color=(255, 0, 0, 255)).save(input_path, format="PNG")

            convert_image(input_path, output_path, show_progress=False)

            self.assertTrue(os.path.exists(output_path))
            with Image.open(output_path) as img:
                self.assertEqual(img.format, "JPEG")

    def test_input_format_validation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, "input.png")
            output_path = os.path.join(tmp_dir, "output.webp")

            Image.new("RGBA", (5, 5), color=(0, 0, 0, 255)).save(input_path, format="PNG")

            with self.assertRaises(ValueError):
                convert_image(input_path, output_path, input_format="JPEG", show_progress=False)

    def test_list_formats(self):
        stream = StringIO()
        with redirect_stdout(stream):
            exit_code = main(["--list-formats"])
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
