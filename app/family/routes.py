from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import (FamilyDetails, FamilyRelation, RelationCategory,
                        RelationType, Address, City, State, Country, Profile)

family_bp = Blueprint('family', __name__)


@family_bp.route('/family')
@login_required
def family():
    categorized = {}
    no_brother  = getattr(current_user.profile, 'no_brother', False)
    no_sister   = getattr(current_user.profile, 'no_sister', False)
    person      = FamilyDetails.query.filter_by(user_id=current_user.id).first()
    categories  = RelationCategory.query.order_by(RelationCategory.name).all()

    for cat in categories:
        categorized[cat.name] = {}
        rel_types = RelationType.query.filter_by(category_id=cat.id).order_by(RelationType.name).all()
        for rt in rel_types:
            if rt.name == 'Brother' and no_brother:
                continue
            if rt.name == 'Sister' and no_sister:
                continue
            entry = None
            if person:
                rel = (FamilyRelation.query
                       .filter_by(person_id=person.id, relation_type=rt.name)
                       .join(FamilyDetails, FamilyRelation.related_person_id == FamilyDetails.id)
                       .filter(FamilyDetails.user_id == current_user.id)
                       .first())
                if rel:
                    entry = {'member': rel.related_person, 'relation': rt.name}
            categorized[cat.name][rt.name] = entry or {'member': None, 'relation': rt.name}

    return render_template('family/family.html', user=current_user,
                           categorized=categorized,
                           no_brother=no_brother, no_sister=no_sister)


@family_bp.route('/family/edit', methods=['GET', 'POST'])
@login_required
def edit_or_add_family():
    member_id     = request.args.get('member_id')
    relation_type = (request.form.get('relation_type')
                     if request.method == 'POST'
                     else request.args.get('relation'))
    member = address = member_relation = None

    if member_id:
        member = FamilyDetails.query.get_or_404(member_id)
        if member.user_id != current_user.id:
            abort(403)
        if member.address_id:
            address = Address.query.get(member.address_id)
        person = FamilyDetails.query.filter_by(user_id=current_user.id).first()
        if person:
            member_relation = FamilyRelation.query.filter_by(
                person_id=person.id, related_person_id=member.id).first()
            if member_relation and request.method == 'GET':
                relation_type = member_relation.relation_type

    profile        = current_user.profile
    relation_types = RelationType.query.all()
    cities         = City.query.order_by(City.name).all()
    states         = State.query.order_by(State.name).all()
    countries      = Country.query.order_by(Country.name).all()

    if request.method == 'POST':
        # Handle no-sibling flags
        if 'no_brother' in request.form:
            if profile:
                profile.no_brother = True
            person = FamilyDetails.query.filter_by(user_id=current_user.id).first()
            if person:
                FamilyRelation.query.filter_by(person_id=person.id, relation_type='Brother').delete()
            db.session.commit()
            flash('Marked as having no brothers.', 'success')
            return redirect(url_for('family.family'))

        if 'no_sister' in request.form:
            if profile:
                profile.no_sister = True
            person = FamilyDetails.query.filter_by(user_id=current_user.id).first()
            if person:
                FamilyRelation.query.filter_by(person_id=person.id, relation_type='Sister').delete()
            db.session.commit()
            flash('Marked as having no sisters.', 'success')
            return redirect(url_for('family.family'))

        relation_type = request.form.get('relation_type')
        if not relation_type:
            flash('Relation type is required.', 'danger')
            return redirect(request.url)

        try:
            addr_data = dict(
                user_id    = current_user.id,
                address1   = request.form.get('address', '').strip(),
                address2   = request.form.get('address2', '').strip(),
                address3   = request.form.get('address3', '').strip(),
                city_id    = int(request.form.get('city_id')),
                state_id   = int(request.form.get('state_id')),
                country_id = int(request.form.get('country_id')),
                zipcode    = request.form.get('zipcode', '').strip(),
                tag        = 'family_member',
            )
        except (TypeError, ValueError):
            flash('Please select valid city, state, and country.', 'danger')
            return redirect(request.url)

        def fill_member(m):
            m.first_name     = request.form.get('first_name', '').strip()
            m.last_name      = request.form.get('last_name', '').strip()
            m.contact_number = request.form.get('contact_number', '').strip()
            m.email          = request.form.get('email', '').strip()
            m.age            = request.form.get('age') or None
            m.occupation     = request.form.get('occupation', '').strip()
            m.marital_status = request.form.get('marital_status', '').strip()

        if member:
            fill_member(member)
            if address:
                for k, v in addr_data.items():
                    setattr(address, k, v)
            else:
                new_addr = Address(**addr_data)
                db.session.add(new_addr)
                db.session.flush()
                member.address_id = new_addr.id
            db.session.commit()
            flash('Family member updated.', 'success')
        else:
            new_member = FamilyDetails(user_id=current_user.id)
            fill_member(new_member)
            new_addr = Address(**addr_data)
            db.session.add(new_addr)
            db.session.flush()
            new_member.address_id = new_addr.id
            db.session.add(new_member)
            db.session.flush()

            person = FamilyDetails.query.filter_by(user_id=current_user.id).first()
            if person and person.id != new_member.id:
                db.session.add(FamilyRelation(
                    person_id=person.id,
                    related_person_id=new_member.id,
                    relation_type=relation_type,
                ))
            db.session.commit()
            flash('Family member added.', 'success')

        return redirect(url_for('family.family'))

    return render_template('family/family_form.html', user=current_user,
                           member=member, address=address,
                           relation_type=relation_type,
                           relation_types=relation_types,
                           member_relation=member_relation,
                           cities=cities, states=states, countries=countries)


@family_bp.route('/family/delete/<int:member_id>', methods=['POST'])
@login_required
def delete_family(member_id):
    member = FamilyDetails.query.get_or_404(member_id)
    if member.user_id != current_user.id:
        abort(403)
    try:
        FamilyRelation.query.filter(
            (FamilyRelation.person_id == member.id) |
            (FamilyRelation.related_person_id == member.id)
        ).delete(synchronize_session=False)
        db.session.delete(member)
        db.session.commit()
        flash('Family member deleted.', 'success')
    except Exception:
        db.session.rollback()
        flash('Error deleting family member.', 'danger')
    return redirect(url_for('family.family'))
