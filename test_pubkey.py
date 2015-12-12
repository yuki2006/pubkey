__author__ = 'ono'

import unittest
from pubkey import *


class MyTestCase(unittest.TestCase):
    def test_get_key_path(self):
        self.assertEqual(
            get_key_path("~/.ssh/", "id_rsa"),
            ("~/.ssh/", "id_rsa", "id_rsa.pub")
        )

        self.assertEqual(
            get_key_path("~/.ssh/", "~/.ssh/id_rsa"),
            ("~/.ssh/", "id_rsa", "id_rsa.pub")
        )

        self.assertEqual(
            get_key_path("~/.ssh/", "~/.ssh/sample"),
            ("~/.ssh/", "sample", "sample.pub")
        )

        self.assertEqual(
            get_key_path("~/.ssh/", "~/.ssh/sample.key"),
            ("~/.ssh/", "sample.key", "sample.key.pub")
        )

        self.assertEqual(
            get_key_path("~/.ssh/", "~/.ssh/sample.any"),
            ("~/.ssh/", "sample.any", "sample.any.pub")
        )

        self.assertEqual(
            get_key_path("~/.ssh/", "~/.ssh/sample.any.key"),
            ("~/.ssh/", "sample.any.key", "sample.any.key.pub")
        )

        self.assertEqual(
            get_key_path("/home/", "sample.any.key"),
            ("/home/", "sample.any.key", "sample.any.key.pub")
        )

    def test_gen_config_data(self):
        self.assertEqual(
            gen_config_data("~/.ssh/id_rsa", "","abc@home.com"),
            "Host home.com\n\thostname home.com\n\tUser abc\n\tIdentityFile ~/.ssh/id_rsa\n\n"
        )

        self.assertEqual(
            gen_config_data("~/.ssh/id_rsa", "server1","abc@home.com"),
            "Host server1\n\thostname home.com\n\tUser abc\n\tIdentityFile ~/.ssh/id_rsa\n\n"
        )

        self.assertEqual(
            gen_config_data("~/.ssh/hoge", "server1","1@home.com"),
            "Host server1\n\thostname home.com\n\tUser 1\n\tIdentityFile ~/.ssh/hoge\n\n"
        )


if __name__ == '__main__':
    unittest.main()
