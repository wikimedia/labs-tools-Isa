import sys
import traceback

from isa import db
from isa.models import Contribution


def commit_changes_to_db():
    """
    Test for the success of a database commit operation.

    """
    try:
        db.session.commit()
    except Exception:
        # TODO: We could add a try catch here for the error
        print('Exception when committing to database.', file=sys.stderr)
        traceback.print_stack()
        traceback.print_exc()
        db.session.rollback()
        # for resetting non-commited .add()
        db.session.flush()
        return True
    return False
