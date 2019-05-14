from isa import db


def testDbCommitSuccess():
    """
    Test for the success of a database commit operation.

    """
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        # for resetting non-commited .add()
        db.session.flush()
        return True
    return False
