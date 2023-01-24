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
    SQLALCHEMY_DATABASE_URI = create_sqlite_uri("todolist-dev.db")


config = {
    "development": DevelopmentConfig,
    "default": DevelopmentConfig,
}
