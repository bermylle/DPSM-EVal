import uuid
from datetime import datetime
from src import login_manager,db, mongo
from flask import Blueprint, render_template, session, redirect, abort, request, url_for, flash,jsonify
from src.user.models import Evaluation, UserAccounts
from flask_login import logout_user


# Set up a Blueprint
dpsm_admin_blueprint = Blueprint('dpsm_admin_blueprint', __name__)

#ADMIN TEMPLATES
@dpsm_admin_blueprint.route('/admin-dashboard')
def admin_dashboard():
	active_forms = []
	inactive_forms = []

	active_data = mongo.db.evaluation.find({"is_active" : True})
	inactive_data = mongo.db.evaluation.find({"is_active" : False})

	for document in active_data:	
		active_forms.append(document)
	for document in inactive_data:
		inactive_forms.append(document)


	print(active_data)
	return render_template('admin/dashboard.html', active_forms = active_forms, inactive_forms=inactive_forms )


ROWS_PER_PAGE = 10
@dpsm_admin_blueprint.route('/admin/user-list')
def admin_user_list():
	
	page = request.args.get('page', 1, type=int)
	#user_list = UserAccounts.query.all()
	user_list = UserAccounts.query.paginate(page=page, per_page=ROWS_PER_PAGE)
	return render_template('admin/user/user-list.html', users = user_list)

@dpsm_admin_blueprint.route('/admin/add-user', methods=['GET', 'POST'])
def add_user():

	email = request.form.get('email')
	first_name = request.form.get('first_name')
	middle_name = request.form.get('middle_name')
	last_name = request.form.get('last_name')
	unit = request.form.get('unit')
	status = request.form.get('status')
	position1 = request.form.get('position1')
	position2 = request.form.get('position2')
	position3 = request.form.get('position3')
	work_title = request.form.get('work_title')

	
	if position1 == 'True':
		is_unit_head = True
	else:
		is_unit_head = False

	if position2 == 'True':
		is_unit_apc = True
	else:
		is_unit_apc = False

	if position3 == 'True':
		is_dept_head = True
	else:
		is_dept_head = False
	
	
	user = UserAccounts.query.filter_by(email=email).first()

	if user:
		# If user exists then handle here.
		flash('User already exists.')
		return redirect(url_for('dpsm_admin_blueprint.add_user'))
	
	# New User ID
	new_id = UserAccounts.query.order_by(UserAccounts.id.desc()).first()
	eval_email = []
	eval_email.append(email)
	if request.method == 'POST':
		new_user = UserAccounts(id = new_id.id + 1,email=email, first_name=first_name,
		middle_name=middle_name,
		last_name=last_name,
		is_unit_head=is_unit_head,
		is_unit_apc = is_unit_apc,
		is_dept_head=is_dept_head,
		status=status,
		work_title=work_title, 
		unit = unit,
		is_evaluated_email = eval_email)
		
	
		db.session.add(new_user)
		db.session.commit()


		return redirect(url_for('dpsm_eval_blueprint.admin_user_list'))

	return render_template('admin/user/add-user.html')

@dpsm_admin_blueprint.route('/admin/delete/<int:id>')
def delete_user(id):
	user = UserAccounts.query.get(id)

	try:
		db.session.delete(user)
		db.session.commit()
		
		return redirect(url_for('dpsm_eval_blueprint.admin_user_list'))
	except:
		return 'Problem deleting user'

@dpsm_admin_blueprint.route('/admin/add-form')
def open_form():
	return render_template('admin/forms/renewal/open-form.html')

@dpsm_admin_blueprint.route('/renewalAction', methods=['GET', 'POST'])
def open_form_renewal():
	title = request.form.get('title')
	purpose_eval = request.form.get('purpose_eval')
	start_date = request.form.get('start_date')
	end_date = request.form.get('end_date')
	release_date = request.form.get('release_date')
	evaluatees_data = []

	id = uuid.uuid4().hex

	# Renewal Code
	if (purpose_eval == "Renewal Evaluation"):
		data = {
			"title": title,
			"purpose_of_evaluation": purpose_eval,
			"start_date": start_date,
			"end_date": end_date,
			"release_date": release_date,
			"is_active": True,
			"evaluatees": evaluatees_data,
			"evaluators": [],
			"evaluation_answers": []
		}
		
		evaluatees = UserAccounts.query.filter((UserAccounts.status == "Full Time - Temporary") | (UserAccounts.status == "Part Time - Lecturer") ).all()
		for user in evaluatees:
			evaluatee_data = {
				"user_id" : uuid.uuid4().hex,
				"email" : user.email,
				"first_name" : user.first_name,
				"middle_name" : user.middle_name,
				"last_name" : user.last_name,
				"evaluation_results" : [],
				"self_eval" : []
			}
			evaluatees_data.append(evaluatee_data)
		
		mongo.db.evaluation.update_one( {"_id": id}, { "$setOnInsert": data}, upsert = True)
	# Tenurial Code
	else:
		data = {
			"title": title,
			"purpose_of_evaluation": purpose_eval,
			"start_date": start_date,
			"end_date": end_date,
			"release_date": release_date,
			"is_active": True,
			"evaluatees": [],
			"evaluators": [],
			"evaluation_answers": []
		}
		mongo.db.evaluation.update_one( {"_id": id}, { "$setOnInsert": data}, upsert = True)

	return jsonify({"success" : "Evaluation added "}), 200


@dpsm_admin_blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('dpsm_eval_blueprint.index'))