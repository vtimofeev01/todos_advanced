import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))


def create_sqlite_uri(db_name):
    # return 'mysql://vtimof01_todo:VaTeFairePrendre01.@localhost/vtimof01_todo'
    return "sqlite:///" + os.path.join(BASEDIR, db_name)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "secret key, just for testing"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    # DEBUG = True
    SQLALCHEMY_POOL_RECYCLE = 35  # value less than backend’s timeout
    SQLALCHEMY_POOL_TIMEOUT = 7  # value less than backend’s timeout
    SQLALCHEMY_PRE_PING = True
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_recycle': SQLALCHEMY_POOL_RECYCLE, 'pool_pre_ping': SQLALCHEMY_PRE_PING}

    # SQLALCHEMY_ENGINE_OPTIONS = {'pool_recycle': SQLALCHEMY_POOL_RECYCLE, 'pool_timeout': SQLALCHEMY_POOL_TIMEOUT,
    #                              'pool_pre_ping': SQLALCHEMY_PRE_PING}


    SQLALCHEMY_DATABASE_URI = create_sqlite_uri("todolist-dev.db")


config = {
    "development": DevelopmentConfig,
    "default": DevelopmentConfig,
}
