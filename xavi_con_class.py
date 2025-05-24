
# llibreries a instal·lar en el entorn virtual per a que funcioni
"""%pip install --upgrade pip
%pip install paramiko
%pip install sshtunnel
%pip install SQLAlchemy
%pip install --upgrade pandas
"""

#imports per mysql de datanex

import warnings
warnings.filterwarnings("ignore")
from sshtunnel import SSHTunnelForwarder
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import inspect
import pandas as pd
from sqlalchemy import  Interval
from sqlalchemy import text
import hashlib

import pymysql
import pandas as pd
import psycopg2



#definicio de la classe

class db_connect(object):
    def __init__(self, db_host, db_port, db, ssh, ssh_user, ssh_host, ssh_pkey,flavour,db_user,db_pass):
        # SSH Tunnel Variables
        self.db_host = db_host
        self.db_port = db_port
        self.flavour = flavour
        self.db_user = db_user
        self.db_pass = db_pass
        self.db= db
        if ssh == True:
            self.server = SSHTunnelForwarder(
                (ssh_host, 22),
                ssh_username=ssh_user,
                ssh_password=ssh_pkey,
                remote_bind_address=(db_host, db_port),
            )
            server = self.server
            server.start() #start ssh server
            self.local_port = server.local_bind_port
            print(f'Server connected via SSH || Local Port: {self.local_port}...')
        elif ssh == False:
            self.local_port = db_port
            pass
    
    def schemas(self, db = None):
       
        db = db or getattr(self, 'db', None)
        if db is None:
            raise ValueError("No database specified and 'self.db' is not set.")
            
        if self.flavour == 'mysql':
            engine = create_engine(f'mysql+pymysql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}')
        elif self.flavour == 'postgres':
            engine = create_engine(f'postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}')
        else:
            print('Flavour not supported')
        inspector = inspect(engine)
        print ('Postgres database engine inspector created...')
        schemas = inspector.get_schema_names()
        self.schemas_df = pd.DataFrame(schemas,columns=['schema name'])
        print(f"Number of schemas: {len(self.schemas_df)}")
        engine.dispose()
        return self.schemas_df
        
    def tables(self, db, schema):
        if self.flavour == 'mysql':
            engine = create_engine(f'mysql+pymysql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}')
        elif self.flavour == 'postgres':
            engine = create_engine(f'postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}')
        else:
            print('Flavour not supported')
        
        inspector = inspect(engine)
        print ('Database engine inspector created...')
        tables = inspector.get_table_names(schema=schema)
        self.tables_df = pd.DataFrame(tables,columns=['table name'])
        print(f"Number of tables: {len(self.tables_df)}")
        engine.dispose()
        return self.tables_df

    def query(self, db, query,dtype=None,parse_dates=None,params=None): #query per datnanex mysql i pzero postgres
        if self.flavour == 'mysql':
            engine = create_engine(f'mysql+pymysql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}')
        elif self.flavour == 'postgres':
            engine = create_engine(f'postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}')
        else:
            print('Flavour not supported')
        print (f'Database [{db}] session created...')
        self.query_df = pd.read_sql(query,engine,parse_dates=parse_dates,params=params)
        print ('<> Query Sucessful <>')
        engine.dispose()
        return self.query_df

    def query_chunks(self, db, query,dtype=None,parse_dates=None): #prepara per chunks de dades
        if self.flavour == 'mysql':
            engine = create_engine(f'mysql+pymysql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}')
        elif self.flavour == 'postgres':
            engine = create_engine(f'postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}')
        else:
            print('Flavour not supported')
        print (f'Database [{db}] session created...')
        self.query_df = pd.read_sql(query,engine,parse_dates=parse_dates,chunksize=1000)
        print ('<> Query Sucessful <>')
        engine.dispose()
        return self.query_df
        
     
    def query_build(self, db, query): #query per executar creacions de taules tipus DDL
        
        if self.flavour == 'mysql':
            engine = create_engine(f'mysql+pymysql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}')
        
        elif self.flavour == 'postgres':
            engine = create_engine(f'postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}')
        else:
            print('Flavour not supported')
        print (f'Database [{db}] session created...')
       
        with engine.connect() as connection:
            connection.execute(text(query))
        print ('<> Query executed Sucessfully <>')
        engine.dispose()
        return
    
    


    def write_table(self, db, df, table_name, schema,dtype=None): #només per PZERO postgres
        
        engine = create_engine(f'postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}')
        df.to_sql(name=table_name,con= engine, if_exists='replace', index=False,schema=schema,dtype=dtype)
        print(f'<> Table [{table_name}] on [{schema}] created <>')
        engine.dispose()
        return
   
    def write_chunk(self, db, chunk, table_name, schema,dtype=None): #adaptat per afegir chunks de dades a una taula.
        engine = create_engine(f'postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}',pool_pre_ping=True)
        chunk.to_sql(name=table_name,con= engine, if_exists='append', index=False,schema=schema,dtype=dtype)
        print(f'<> Table [{table_name}] on [{schema}] created <>')
        engine.dispose()
        return
    
    def write_table_2(self, db, df, table_name,dtype=None): #per escriure taules a mysql 
        engine = create_engine(f'mysql+pymysql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}')    
        print (f'Database [{db}] session created...')
        df.to_sql(name=table_name,con= engine, if_exists='replace', index=False,dtype=dtype)
        print(f'<> Table [{table_name}] created <>')
        engine.dispose()
        return
    
    def return_engine(self, db): #query per datnanex mysql i pzero postgres
        if self.flavour == 'mysql':
            engine = create_engine(f'mysql+pymysql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}')
        elif self.flavour == 'postgres':
            engine = create_engine(f'postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.local_port}/{db}')
        else:
            print('Flavour not supported')
        print (f'Engine to connect  [{db}] created...')
        return engine
    
    def return_connection(self, db): #query per datnanex mysql i pzero postgres
        if self.flavour == 'mysql':
            connection = pymysql.connect(database={db},host={self.db_host}, user={self.db_user}, password={self.db_pass})
        elif self.flavour == 'postgres':
            connection =  psycopg2.connect(dbname={db},host={self.db_host}, user={self.db_user}, password={self.db_pass})
        else:
            print('Flavour not supported')
        print (f'connector to connect  [{db}] created...')
        return connection
       
        


   

    def encrypt_to_x_digits(number, x, salt):
        if pd.isnull(number):  # Comprova si number és NaN o nul 
            return None  # Retorna un valor especial per a casos de NaN o nul
        else:
            # Convertim el nombre a cadena i codifiquem en UTF-8 per a la funció de hash
            if isinstance(number, str):
                number = number.encode('utf-8')
            if isinstance(salt, str):
                salt = salt.encode('utf-8')

            number2 = salt + number
            number_str = str(number2).encode('utf-8')

            # Generem un hash SHA-256
            hashed = hashlib.sha256(number_str).hexdigest()

            # Reduïm la longitud del hash a x dígits determinats pel paràmetre x
            encrypted = int(hashed, 16) % (10 ** x)  # Limita la longitud a x dígits

            return encrypted