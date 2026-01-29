from .base import BasePluginTestCase


class TestPlugin(BasePluginTestCase):
    def test_device_classes_available(self):
        device_classes = self.plugin.get_device_classes()
        device_class_map = {class_.codename: class_ for class_ in device_classes}

        self.assertEqual(len(device_class_map), 2)
        self.assertIn("insta360_x3", device_class_map)
        self.assertIn("insta360_x4", device_class_map)
