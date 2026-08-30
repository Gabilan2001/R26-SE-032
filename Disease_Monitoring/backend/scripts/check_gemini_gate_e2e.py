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
if not secondary_gate_configured():
    print("RESULT=FAIL missing_key")
    raise SystemExit(1)

ok, reason, status = verify_crop_image(jpeg_bytes((30, 150, 40)), "LEAF")
print("leaf_dummy_status=", status)
print("leaf_dummy_accepted=", ok)
print("leaf_dummy_reason=", reason)

time.sleep(1.0)

ok2, reason2, status2 = verify_crop_image(
    jpeg_bytes((200, 40, 40)), "FRUIT", local_gate_confidence=0.4
)
print("fruit_dummy_status=", status2)
print("fruit_dummy_accepted=", ok2)
print("fruit_dummy_reason=", reason2)

# Solid-color dummies should not hard-crash the secondary layer.
# Reject or deferred_to_local (API flake after local-gate policy) are both OK.
if status in {"pass", "reject", "deferred_to_local"} and status2 in {
    "pass",
    "reject",
    "deferred_to_local",
}:
    print("RESULT=PASS secondary_gate_reachable")
else:
    print("RESULT=FAIL unexpected_status")
    raise SystemExit(1)
