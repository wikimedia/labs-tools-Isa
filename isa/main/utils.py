import sys

from isa import db
from isa.models import Contribution


def commit_changes_to_db():
    """
    Test for the success of a database commit operation.

    """
    try:
        db.session.commit()
    except Exception as e:
        # TODO: We could add a try catch here for the error
        print('-------------->>>>>', file=sys.stderr)
        print(str(e), file=sys.stderr)
        db.session.rollback()
        # for resetting non-commited .add()
        db.session.flush()
        return True
    return False
