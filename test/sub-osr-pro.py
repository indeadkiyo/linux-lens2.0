import json
import sys

import easyocr
from PIL import Image


def main():
    # once when subprocess starts
    reader = easyocr.Reader(["en"], gpu=False, verbose=False)

    for line in sys.stdin:
        try:
            data = json.loads(line.strip())
            img_path = data["image_path"]

            # Process image
            result = reader.readtext(img_path, detail=0, paragraph=True)
            text = "\n".join(result)

            # Send back result
            response = json.dumps({"success": True, "text": text})
            print(response)
            sys.stdout.flush()

        except Exception as e:
            response = json.dumps({"success": False, "error": str(e)})
            print(response)
            sys.stdout.flush()


if __name__ == "__main__":
    main()
