import pymysql
import streamlit as st

USERNAME = st.secrets["USERNAME"]
PASSWORD = st.secrets["PASSWORD"]
DATABASE = st.secrets["DATABASE"]
HOST = st.secrets["HOST"]

class Database:

    def __init__(self):
        self.user = USERNAME
        self.password = PASSWORD
        self.database = DATABASE
        self.host = HOST

    def connect(self):
        """Connects to the Database"""
        try:
    
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
                    
            return self.connection
        
        except Exception as e:
            print("Could not connect to database: ", e)
            return 0
        
    
    def execute(self, connection, query, values):
        """ 
        Execute SQL command, to be used for insertion and updates
        """
        # Create Cursor
        cur = connection.cursor()
        # Select Query
        cur.execute(query, values)

        cur.close()


    def fetch(self, connection, command):
        """ 
        Execute SQL command and retrieves the desired data. 
        """
        # Create Cursor
        cur = connection.cursor()
        # Select Query
        cur.execute(command)

        return cur.fetchall()
    
    
    def kill(self, connection):
        """ 
        Execute SQL command, to be used for insertion and updates
        """
        connection.close()