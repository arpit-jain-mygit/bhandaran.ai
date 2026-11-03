# ---------------------------------------------------------------
# Guard rails for migration files (no database needed).
# ---------------------------------------------------------------
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND = Path(__file__).parent.parent


def scripts() -> ScriptDirectory:
    return ScriptDirectory.from_config(Config(str(BACKEND / "alembic.ini")))


def test_revision_ids_fit_in_alembic_version_table():
    # alembic_version.version_num is VARCHAR(32): a longer id makes the
    # migration's DDL run but the version update fail (half-applied).
    too_long = [r.revision for r in scripts().walk_revisions() if len(r.revision) > 32]
    assert too_long == []


def test_history_is_a_single_line():
    # Two "heads" would mean two migrations claim the same parent.
    assert len(scripts().get_heads()) == 1
