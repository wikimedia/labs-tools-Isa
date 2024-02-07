import sys
import traceback

from isa import db


def manage_session(f):
    def inner(*args, **kwargs):
        # MANUAL PRE PING
        try:
            print('managing session now')
            db.session.execute("SELECT 1;")
            db.session.commit()
        except Exception:
            db.session.rollback()
        finally:
            db.session.close()

        # SESSION COMMIT, ROLLBACK, CLOSE
        try:
            res = f(*args, **kwargs)
            db.session.commit()
            return res
        except Exception as e:
            db.session.rollback()
            raise e
            # OR return traceback.format_exc()
        finally:
            db.session.close()
    return inner


def commit_changes_to_db():
    """
    Test for the success of a database commit operation.

    """
    try:
        db.session.commit()
        return True
    except Exception:
        # TODO: We could add a try catch here for the error
        print('Exception when committing to database.', file=sys.stderr)
        traceback.print_stack()
        traceback.print_exc()
        db.session.rollback()
        # for resetting non-commited .add()
        db.session.flush()
    return False
