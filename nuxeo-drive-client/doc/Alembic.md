# SQLite database migration procedure

## Alembic revision file generation

For each alteration of the model (create / drop / alter a table or column) we need to generate an Alembic revision file.
Let's say we added the column 'new\_colum' of type String to the 'server\_bindings' table, we can generate the Alembic revision file
with a relevant comment by running this command in nuxeo-drive/nuxeo-drive-client:

    alembic revision -m "Adding new_column to server_bindings"

The file is created in [nuxeo-drive/nuxeo-drive-client/alembic/versions](https://github.com/nuxeo/nuxeo-drive/tree/1.4/nuxeo-drive-client/alembic/versions),
as configured in [alembic.ini](https://github.com/nuxeo/nuxeo-drive/blob/1.4/nuxeo-drive-client/alembic.ini) by the `script_location` key.

## Alembic revision file implementation

Then we need to populate the `upgrade()` and `downgrade()` functions of the generated file with directives that will apply a set of changes to the database.
Implementing `downgrade()` is optional for now as we only handle database upgrade.

The modified file should look like this (see the list of [available operations](https://alembic.readthedocs.org/en/latest/ops.html)):

    """Adding new_column to server_bindings

    Revision ID: 16fdaaf7329
    Revises: None
    Create Date: 2014-01-07 18:13:05.865425

    """

    # revision identifiers, used by Alembic.
    revision = '16fdaaf7329'
    down_revision = None

    from alembic import op
    import sqlalchemy as sa
    from nxdrive.model import ServerBinding


    def upgrade():
        op.add_column(ServerBinding.__tablename__,
                      sa.Column('new_column', sa.String()))


    def downgrade():
        raise NotImplementedError("Column drop is not available in SQLite, can't downgrade")

## That's it, we're done!
