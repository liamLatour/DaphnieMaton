import unittest

from app.libraries.classes import Input


class TestCustomInput(unittest.TestCase):

    def setUp(self):
        self.textInput = Input(inputName="I'm an Input",
                               input_filter="int",
                               boundaries=[0, float('inf')],
                               default_text="5",
                               callback=self.callback,
                               inputType=0)

        self.switchInput = Input(inputName="I'm an Input",
                                 input_filter="int",
                                 boundaries=[0, float('inf')],
                                 default_text="True",
                                 callback=self.callback,
                                 inputType=1)

        self.buttonInput = Input(inputName="I'm an Input",
                                 input_filter="int",
                                 boundaries=[0, float('inf')],
                                 default_text="Hey",
                                 callback=self.callback,
                                 inputType=2)

        self.called = False

    def test_defaultValues(self):
        self.assertEqual(self.textInput.label.text, "I'm an Input")
        self.assertEqual(self.switchInput.label.text, "I'm an Input")
        self.assertEqual(self.buttonInput.label.text, "I'm an Input")

        self.assertEqual(self.textInput.input.text, "5")
        self.assertEqual(self.switchInput.input.active, True)
        self.assertEqual(self.buttonInput.input.text, "Hey")

    def test_callback(self):
        self.textInput.input.text = "3"
        self.assertTrue(self.called)
        self.called = False
        self.switchInput.input.active = False
        self.assertTrue(self.called)
        self.called = False
        self.buttonInput.input.trigger_action(duration=0.1)
        self.assertTrue(self.called)

    def test_write_read(self):
        self.textInput.write("3")
        self.assertFalse(self.called)
        self.assertEqual(self.textInput.read(), 3)
        self.switchInput.write(False)
        self.assertFalse(self.called)
        self.assertFalse(self.switchInput.read())

    def test_hide(self):
        for i in range(5):
            self.textInput.hide()
            self.assertIsNone(self.textInput.label.parent)
            self.assertIsNone(self.textInput.input.parent)
            self.assertEqual(self.textInput.height, 0)

    def test_show(self):
        for i in range(5):
            self.textInput.show()
            self.assertIsNotNone(self.textInput.label.parent)
            self.assertIsNotNone(self.textInput.input.parent)
            self.assertEqual(self.textInput.height, 30)

    def callback(self):
        self.called = True


if __name__ == '__main__':
    unittest.main()
