# -*- coding: utf-8 -*-

import uuid
import time
import os
from tempfile import mkstemp

from flask.ext.wtf import Form
from flask import render_template, redirect, url_for, flash
from wtforms.ext.sqlalchemy.orm import model_form

from invenio.config import CFG_SITE_SECRET_KEY
from invenio.sqlalchemyutils import db
from invenio.bibtask import task_low_level_submission
from invenio.bibfield_jsonreader import JsonReader
from invenio.config import CFG_TMPSHAREDDIR

from invenio.simplestore_model.HTML5ModelConverter import HTML5ModelConverter
import invenio.simplestore_upload_handler as uph
from invenio.simplestore_model.model import (Submission, SubmissionMetadata,
                                             LinguisticsMetadata)
from invenio.webinterface_handler_flask_utils import _


# Needed to avoid errors in Form Generation
# There is an invenio forms class that should be investigated
class FormWithKey(Form):
    SECRET_KEY = CFG_SITE_SECRET_KEY


def deposit(request):
    """ Renders the deposit start page """
    if request.method == 'POST':
        if not 'uuid' in request.form:
            return "ERROR: uuid not set", 500

        uid = request.form['uuid']

        updir = os.path.join(uph.CFG_SIMPLESTORE_UPLOAD_FOLDER, uid)
        if (not os.path.isdir(updir)) or (not os.listdir(updir)):
            #would probably be better to disable the button in js until
            #upload complete
            flash(_("Please upload a file to deposit"), 'error')
            return render_template('simplestore-deposit.html', uuid=uid)

        sub = Submission(uuid=uid)

        if request.form['domain'] == 'linguistics':
            meta = LinguisticsMetadata()
        else:
            meta = SubmissionMetadata()

        sub.md = meta
        db.session.add(sub)
        db.session.commit()
        return redirect(url_for('.addmeta', uid=uid))
    else:
        return render_template('simplestore-deposit.html',
                               uuid=uuid.uuid1().hex)


def addmeta(request, uid):
    """
    Add metadata to a submission.

    The form is dependent on the domain chosen at the deposit stage.
    """

    #Uncomment the following line if there are errors regarding db tables
    #not being present. Hacky solution for minute.
    #db.create_all()

    #current_app.logger.error("Called addmeta")

    if uid is None:
        return "ERROR: uuid not set", 500

    sub = Submission.query.filter_by(uuid=uid).first()

    if sub is None:
        return "ERROR: failed to find uuid in DB", 500

    MetaForm = model_form(sub.md.__class__, base_class=FormWithKey,
                          exclude=['submission', 'submission_type'],
                          converter=HTML5ModelConverter())
    meta_form = MetaForm(request.form, sub.md)

    if meta_form.validate_on_submit():
        marc = create_marc_and_ingest(request.form)
        return render_template('simplestore-finalise.html',
                               tag=sub.uuid, marc=marc)
    #else:
    #   print meta_form.errors

    #Need to test that dir exists
    files = os.listdir(os.path.join(uph.CFG_SIMPLESTORE_UPLOAD_FOLDER, uid))

    return render_template(
        'simplestore-addmeta.html',
        domain=sub.md.domain,
        fileret=files,
        form=meta_form,
        uuid=sub.uuid,
        basic_field_iter=sub.md.basicFieldIter,
        opt_field_iter=sub.md.optionalFieldIter,
        getattr=getattr)


def create_marc_and_ingest(form):
    """
    Generates MARC data used bu Invenio from the filled out form, then
    submits it to the Invenio system.
    """

    json_reader = JsonReader()
    # just do this by hand to get something working for demo
    # this must be automated
    json_reader['title.title'] = form['title']
    json_reader['authors[0].full_name'] = form['creator']
    json_reader['imprint.publisher_name'] = form['publisher']
    json_reader['collection.primary'] = "Article"
    marc = json_reader.legacy_export_as_marc()
    tmp_file_fd, tmp_file_name = mkstemp(suffix='.marcxml',
                                         prefix="webdeposit_%s" % time.strftime("%Y-%m-%d_%H:%M:%S"),
                                         dir=CFG_TMPSHAREDDIR)
    os.write(tmp_file_fd, marc)
    os.close(tmp_file_fd)
    os.chmod(tmp_file_name, 0644)
    task_low_level_submission('bibupload', 'webdeposit', '-i', tmp_file_name)
    return marc
