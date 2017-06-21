from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
if 'RDS_DB_NAME' in os.environ:
            db = os.environ['dcss-analyzer']
            user = os.environ['RDS_USERNAME']
            pwd = os.environ['RDS_PASSWORD']
            host = os.environ['RDS_HOSTNAME']
            port = os.environ['RDS_PORT']
else:
    user = "kr4n3x"
    pwd = ""
    host = "localhost"
    port = "5432"
    db = "dcss-analyzer"
url = "postgresql://{}:{}@{}:{}/{}".format(user, pwd, host, port, db)

engine = create_engine(url)
db_session = scoped_session(sessionmaker(
    autocommit=False, autoflush=True, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    import models
    Base.metadata.create_all(bind=engine)
