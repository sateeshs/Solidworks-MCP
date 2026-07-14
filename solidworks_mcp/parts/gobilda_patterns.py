"""goBILDA mechanical system constants.

All dimensions in mm unless noted. These constants define the goBILDA
build system used in FTC/FRC robotics.
"""

# Hole pattern
HOLE_PITCH_MM = 8.0
BOLT_SIZE = "M4"
BOLT_DIAMETER_MM = 4.0
CLEARANCE_HOLE_MM = 4.2

# Channel dimensions
CHANNEL_WIDTH_MM = 48.0
CHANNEL_HEIGHT_MM = 48.0

# Shaft system
REX_BORE_DIAMETER_MM = 8.0
REX_BORE_PROFILE = "D_bore"
SHAFT_SYSTEM = "REX_8mm"

# Motor mounting
YELLOW_JACKET_BOLT_CIRCLE_MM = 34.0
YELLOW_JACKET_BOLT_SIZE = "M4"
YELLOW_JACKET_SHAFT_DIAMETER_MM = 6.0

# Common compatibility tags
TAG_GOBILDA_8MM_PATTERN = "gobilda_8mm_pattern"
TAG_M4_SOCKET_HEAD = "M4_socket_head"
TAG_REX_8MM_SHAFT = "REX_8mm_shaft"
TAG_YELLOW_JACKET_MOUNT = "yellow_jacket_motor_mount"

# Part categories
CATEGORIES = (
    "structure/channel",
    "structure/bracket",
    "structure/plate",
    "structure/beam",
    "motion/motor",
    "motion/servo",
    "motion/wheel",
    "motion/gear",
    "motion/shaft",
    "motion/bearing",
    "motion/hub",
    "motion/pulley",
    "linear/slide",
    "linear/lead-screw",
    "electronics/sensor",
    "electronics/controller",
    "hardware/spacer",
    "hardware/fastener",
    "hardware/hub",
)
