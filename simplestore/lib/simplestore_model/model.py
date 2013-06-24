from uuid import uuid4

from invenio.sqlalchemyutils import db
from datetime import date
import babel


class Submission(db.Model):
    __tablename__ = 'submission'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.CHAR(32), unique=True, nullable=False)
    content = db.Column(db.LargeBinary())
    # metadata name is reserved, so using md
    md = db.relationship('SubmissionMetadata', backref='submission',
                         cascade="all, delete, delete-orphan", uselist=False)

    def __init__(self, uuid=None, content=None):
        self.uuid = uuid if uuid is not None else uuid4().hex
        self.content = content

    def __repr__(self):
        return '<Submission %s>' % self.uuid


class SubmissionMetadata(db.Model):
    """DataCite-based metadata class. Format description is here:
    http://schema.datacite.org/meta/kernel-2.2/doc/DataCite-MetadataKernel_v2.2.pdf
    """
    __tablename__ = 'submission_metadata'
    domain = 'Generic'
    icon = 'icon-question-sign'
    kind = 'domain'
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'))

    # id seems to be needed to maintain link to parent submission
    id = db.Column(db.Integer, primary_key=True)
    creator = db.Column(db.String(128))
    title = db.Column(db.String(256))
    publisher = db.Column(db.String(128))
    publication_date = db.Column('publication_year', db.Date(),
                                 default=date.today())

    def basic_field_iter(self):
        #why won't submission_id work?
        for f in ['creator', 'title', 'publisher', 'publication_date']:
            yield f

    # optional
    subject = db.Column(db.String(256))
    contributor = db.Column(db.String(256))
    date = db.Column(db.Date())
    language = db.Column(db.Enum(*babel.core.LOCALE_ALIASES.keys()))
    resource_type = db.Column(db.String(256))  # XXX should be extracted to a separate class
    alternate_identifier = db.Column(db.String(256))
    related_identifier = db.Column(db.String(256))
    size = db.Column(db.String(256))
    format = db.Column(db.String(256))  # file extension or MIME
    version = db.Column(db.Numeric(precision=6))
    rights = db.Column(db.String(256))  # not sure how to serialize rights
    description = db.Column(db.String(1024))

    def optional_field_iter(self):
        for f in ['subject', 'contributor', 'date', 'language',
                  'resource_type', 'alternate_identifier',
                  'related_identifier', 'size', 'format',
                  'version', 'rights', 'description']:
            yield f

    # administrative metadata
    # XXX are we going to use them?
    # last_metadata_update = hook?
    # metadata_version_number = schema migration version?

    # using joined table inheritance for the specific domains
    submission_type = db.Column(db.String(50))
    __mapper_args__ = {
        'polymorphic_identity': 'generic',
        'polymorphic_on': submission_type
    }

    def __repr__(self):
        return '<SubmissionMetadata %s>' % self.id

    def __init__(self, creator="", title="", publisher="", publication_year=None):
        self.creator = creator
        self.title = title
        self.publisher = publisher
        self.publication_year = publication_year


def _create_metadata_class(cfg):
    """Creates domain classes that map form fields to databases plus some other
    details."""

    if not hasattr(cfg, 'fields'):
        cfg.fields = []

    def basic_field_iter(self):
        # need to figure out how to refer to parent here
        for s in SubmissionMetadata.basic_field_iter(self):
            yield s

        #Normal field if extra is false or not set
        for f in cfg.fields:
            try:
                if not f['extra']:
                    yield f['name']
            except KeyError:
                yield f['name']

    def optional_field_iter(self):
        # need to figure out how to refer to parent here
        for s in SubmissionMetadata.optional_field_iter(self):
            yield s

        for f in cfg.fields:
            try:
                if f['extra']:
                    yield f['name']
            except KeyError:
                pass

    clsname = cfg.domain + "Metadata"

    args = {'__tablename__': cfg.table_name,
            '__mapper_args__': {'polymorphic_identity': cfg.table_name},
            'id': db.Column(
                db.Integer, db.ForeignKey('submission_metadata.id'),
                primary_key=True),
            'basic_field_iter': basic_field_iter,
            'field_args': {},
            'optional_field_iter': optional_field_iter}

    #The following function and call just add all external attrs manually
    def is_external_attr(n):

        # don't like this bit; problem is we don't want to include the
        # db import and I don't know how to exclude them except via name
        if n in ['db', 'fields']:
            return False

        return not n.startswith('__')

    for attr in (filter(is_external_attr, dir(cfg))):
        args[attr] = getattr(cfg, attr)

    # field args lets us control some aspects of the field
    # including label, validators and decimal places
    for f in cfg.fields:
        args[f['name']] = db.Column(f['col_type'])
        # Doesn't seem pythonic, but show me a better way
        if 'display_text' in f:
            args['field_args'][f['name']] = {'label': f.get('display_text')}

    return type(clsname, (SubmissionMetadata,), args)
