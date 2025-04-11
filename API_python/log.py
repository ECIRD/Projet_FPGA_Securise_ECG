import logging


# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("login.log"),
                              logging.StreamHandler()])

class Login:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        logging.info("Login instance created")

    def authenticate(self, input_username: str, input_password: str):
        if self.username == input_username and self.password == input_password:
            logging.info("Authentication successful")
            return True
        else:
            logging.warning("Authentication failed")
            return False
        
    def warning(self,message : str):
        logging.warning(message)
        return False
    
    def info(self,message : str):
        logging.info(message)
        return False
    
    def debug(self,message : str):
        logging.info(message)
        return False
    
user = Login("admin", "password123")

if __name__ == "__main__":
    user = Login("admin", "password123")
    print(user.authenticate("admin", "password123"))
