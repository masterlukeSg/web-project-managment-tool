import unittest
import database


class TestingDatabase(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        self.db = database.Database()
        self.con_login = self.db.create_connection(self.db.login_db)
        self.all_users_db = self.db.create_connection(self.db.all_users_db)
        
        super(TestingDatabase, self).__init__(methodName)
        
    def test_register_user(self):
        result = self.db.register_user(self.con_login, "LukasW", "ta@gmail.com", "starkesPasswort")
        self.assertFalse(result)

    def test_login(self):
        result = self.db.login_user(self.con_login, "LukasP", "starkesPasswort")
        self.assertTrue(result)
        
    def test_user_exists(self):
        result = self.db.user_exists("LukasP")
        self.assertTrue(result)
        
    def test_text_get_name_from_id(self):
        result = self.db.get_name_from_id("d8db3946275074dd3bd7e0323a85be112")
        self.assertEquals(result, "LukasB")

    def test_get_id_from_name(self):
        result = self.db.get_id_from_name("LukasB")
        self.assertEquals(result, "d8db3946275074dd3bd7e0323a85be112")
    
if __name__ == "__main__":
    unittest.main()
