from whitebox import import_whitebox_plugin_class

# Do not proxy as a proxy class cannot be subclassed
DeviceWizard = import_whitebox_plugin_class("device.DeviceWizard", proxy=False)


def generate_info_step(
    next_button_text,
    plugin_template_name,
):
    actions = {
        "left": {
            "type": "button",
            "config": {
                "text": "Skip to end",
                "action": "WIZARD_STEP_LAST",
            },
        },
        "right": {
            "type": "button",
            "config": {
                "text": next_button_text,
                "action": "WIZARD_STEP_NEXT",
            },
        },
    }

    return {
        "template": plugin_template_name,
        "actions": actions,
    }


introduction = generate_info_step(
    "Start",
    "whitebox_plugin_device_insta360/wizard/intro.html",
)

step_1 = generate_info_step(
    "Checked",
    "whitebox_plugin_device_insta360/wizard/step1.html",
)

step_2 = generate_info_step(
    "Checked",
    "whitebox_plugin_device_insta360/wizard/step2.html",
)

step_3 = generate_info_step(
    "Checklist complete",
    "whitebox_plugin_device_insta360/wizard/step3.html",
)

step_4 = {
    "template": "whitebox_plugin_device_insta360/wizard/step4.html",
    "actions": {
        "left": {
            "type": "button",
            "config": {
                "text": "Back",
                "action": "WIZARD_STEP_INITIAL",
            },
        },
        "right": {
            "type": "button",
            "config": {
                "text": "Connect device",
                "action": "WIZARD_ADD_DEVICE",
            },
        },
    },
}


class BaseInsta360Wizard(DeviceWizard):
    wizard_step_config = [
        introduction,
        step_1,
        step_2,
        step_3,
        step_4,
    ]


class Insta360X3Wizard(BaseInsta360Wizard):
    wizard_step_context = {
        "model_name": "Insta360 X3",
        "introduction_step_picture": (
            "whitebox_plugin_device_insta360/insta360_x3/insta360_x3.webp"
        ),
    }


class Insta360X4Wizard(BaseInsta360Wizard):
    wizard_step_context = {
        "model_name": "Insta360 X4",
        "introduction_step_picture": (
            "whitebox_plugin_device_insta360/insta360_x4/insta360_x4.webp"
        ),
    }
