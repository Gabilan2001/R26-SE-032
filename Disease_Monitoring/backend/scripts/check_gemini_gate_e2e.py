"""End-to-end secondary gate check using verify_crop_image()."""

from dotenv import load_dotenv

load_dotenv()

import io
import time

from PIL import Image

from ml.predict.secondary_image_verify import secondary_gate_configured, verify_crop_image


def jpeg_bytes(color):
    img = Image.new("RGB", (128, 128), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


print("configured=", secondary_gate_configured())

ok, reason, status = verify_crop_image(jpeg_bytes((30, 150, 40)), "LEAF")
print("leaf_dummy_status=", status)
print("leaf_dummy_accepted=", ok)
print("leaf_dummy_reason=", reason)

time.sleep(1.0)

ok2, reason2, status2 = verify_crop_image(jpeg_bytes((200, 40, 40)), "FRUIT")
print("fruit_dummy_status=", status2)
print("fruit_dummy_accepted=", ok2)
print("fruit_dummy_reason=", reason2)

if not secondary_gate_configured():
    print("RESULT=FAIL missing_key")
    raise SystemExit(1)

if status == "unavailable" and status2 == "unavailable":
    print("RESULT=FAIL unavailable")
    raise SystemExit(1)

# Dummy solid colors should not be accepted as tomato leaf/fruit.
if ok or ok2:
    print("RESULT=WARN unexpected_accept_on_dummy")
else:
    print("RESULT=PASS secondary_gate_reachable")
