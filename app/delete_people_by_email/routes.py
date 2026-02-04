from flask import render_template, redirect, url_for, flash, session, request
from . import delete_people_by_email
from .forms import DeletePeopleEmailForm
from .services import parse_emails, fetch_person_by_email, delete_person
from app.utils import log_action
import logging


logger = logging.getLogger(__name__)


@delete_people_by_email.route('/', methods=['GET', 'POST'])
def delete_people():
    """
    Delete attendees (people) from the event by email address.
    """
    event_id = session.get('event_id')

    if not event_id:
        logger.warning("Missing event_id, redirecting to index")
        return redirect(url_for('main.index'))

    form = DeletePeopleEmailForm()
    results = []

    if form.validate_on_submit():
        raw_text = form.emails.data or ''
        emails = parse_emails(raw_text)
        logger.debug("Parsed %d emails for deletion", len(emails))

        if not emails:
            flash('Please enter at least one email address.', 'error')
            return redirect(url_for('delete_people_by_email.delete_people'))

        success_count = 0
        not_found_count = 0
        error_count = 0

        for email in emails:
            logger.debug("Attempting to delete person with email: %s", email)
            person = fetch_person_by_email(event_id, email)

            if not person:
                logger.warning("No person found with email: %s", email)
                results.append({
                    'email': email,
                    'success': False,
                    'error': 'Person not found',
                })
                not_found_count += 1
                continue

            person_id = person.get('id')
            if not person_id:
                logger.error("Person record for %s has no id field: %s", email, person)
                results.append({
                    'email': email,
                    'success': False,
                    'error': 'Person record has no ID',
                })
                error_count += 1
                continue

            status_code, response_text = delete_person(event_id, person_id)
            if status_code in (200, 202, 204):
                results.append({
                    'email': email,
                    'success': True,
                    'error': None,
                })
                success_count += 1
            else:
                logger.error(
                    "Failed to delete person %s (id=%s). Status: %s Response: %s",
                    email,
                    person_id,
                    status_code,
                    response_text,
                )
                results.append({
                    'email': email,
                    'success': False,
                    'error': f'Failed to delete person (status: {status_code})',
                })
                error_count += 1

        logger.info(
            "Deleted people by email: %d success, %d not found, %d errors (total %d)",
            success_count,
            not_found_count,
            error_count,
            len(emails),
        )
        log_action('delete_people_by_email', event_id)

        total = len(results)
        return render_template(
            'delete_people_by_email/result.html',
            results=results,
            total=total,
            success_count=success_count,
            error_count=error_count,
            event_name=session.get('event_name'),
        )

    # GET or initial render
    return render_template(
        'delete_people_by_email/delete.html',
        form=form,
        event_name=session.get('event_name'),
    )

