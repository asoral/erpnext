# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies and contributors
# For lice

from __future__ import unicode_literals, division
import frappe
from frappe import _

class OverlapError(frappe.ValidationError): pass

def validate_overlap_for(doc, doctype, fieldname, value=None):
	"""Checks overlap for specified field.

	:param fieldname: Checks Overlap for this field
	"""

	existing = get_overlap_for(doc, doctype, fieldname, value)
	if existing:
		frappe.throw(_("This {0} conflicts with {1} for {2} {3}").format(doc.doctype, existing.name,
			doc.meta.get_label(fieldname) if not value else fieldname , value or doc.get(fieldname)), OverlapError)

def get_overlap_for(doc, doctype, fieldname, value=None):
	"""Returns overlaping document for specified field.

	:param fieldname: Checks Overlap for this field
	"""

	existing = frappe.db.sql("""select name, from_time, to_time from `tab{0}`
		where `{1}`=%(val)s and schedule_date = %(schedule_date)s and
		(
			(from_time > %(from_time)s and from_time < %(to_time)s) or
			(to_time > %(from_time)s and to_time < %(to_time)s) or
			(%(from_time)s > from_time and %(from_time)s < to_time) or
			(%(from_time)s = from_time and %(to_time)s = to_time))
		and name!=%(name)s and docstatus!=2""".format(doctype, fieldname),
		{
			"schedule_date": doc.schedule_date,
			"val": value or doc.get(fieldname),
			"from_time": doc.from_time,
			"to_time": doc.to_time,
			"name": doc.name or "No Name"
		}, as_dict=True)

	return existing[0] if existing else None


def validate_duplicate_student(students):
	unique_students= []
	for stud in students:
		if stud.student in unique_students:
			frappe.throw(_("Student {0} - {1} appears Multiple times in row {2} & {3}")
				.format(stud.student, stud.student_name, unique_students.index(stud.student)+1, stud.idx))
		else:
			unique_students.append(stud.student)

		return None

# LMS Utils
def get_current_student():
	"""Returns current student from frappe.session.user

	Returns:
		object: Student Document
	"""
	email = frappe.session.user
	if email in ('Administrator', 'Guest'):
		return None
	try:
		student_id = frappe.get_all("Student", {"student_email_id": email}, ["name"])[0].name
		return frappe.get_doc("Student", student_id)
	except (IndexError, frappe.DoesNotExistError):
		return None

def get_portal_programs():
	"""Returns a list of all program to be displayed on the portal
	Programs are returned based on the following logic
		is_published and (student_is_enrolled or student_can_self_enroll)

	Returns:
		list of objects: List of all programs and to be displayed on the portal along with enrollment status
	"""
	published_programs = frappe.get_all("Program", filters={"is_published": True})
	if not published_programs:
		return None

	program_list = [frappe.get_doc("Program", program) for program in published_programs]
	portal_programs = [{'program': program, 'has_access': allowed_program_access(program.name)} for program in program_list if allowed_program_access(program.name) or program.allow_self_enroll]

	return portal_programs

def allowed_program_access(program, student=None):
	"""Returns enrollment status for current student

	Args:
		program (string): Name of the program
		student (object): instance of Student document

	Returns:
		bool: Is current user enrolled or not
	"""
	if has_super_access():
		return True
	if not student:
		student = get_current_student()
	if student and get_enrollment('program', program, student.name):
		return True
	else:
		return False

def get_enrollment(master, document, student):
	"""Gets enrollment for course or program

	Args:
		master (string): can either be program or course
		document (string): program or course name
		student (string): Student ID

	Returns:
		string: Enrollment Name if exists else returns empty string
	"""
	if master == 'program':
		enrollments = frappe.get_all("Program Enrollment", filters={'student':student, 'program': document, 'docstatus': 1})
	if master == 'course':
		enrollments = frappe.get_all("Course Enrollment", filters={'student':student, 'course': document})

	if enrollments:
		return enrollments[0].name
	else:
		return None

@frappe.whitelist()
def enroll_in_program(program_name, student=None):
	"""Enroll student in program

	Args:
		program_name (string): Name of the program to be enrolled into
		student (string, optional): name of student who has to be enrolled, if not
			provided, a student will be created from the current user

	Returns:
		string: name of the program enrollment document
	"""
	if has_super_access():
		return

	if not student == None:
		student = frappe.get_doc("Student", student)
	else:
		# Check if self enrollment in allowed
		program = frappe.get_doc('Program', program_name)
		if not program.allow_self_enroll:
			return frappe.throw("You are not allowed to enroll for this course")

		student = get_current_student()
		if not student:
			student = create_student_from_current_user()

	# Check if student is already enrolled in program
	enrollment = get_enrollment('program', program_name, student.name)
	if enrollment:
		return enrollment

	# Check if self enrollment in allowed
	program = frappe.get_doc('Program', program_name)
	if not program.allow_self_enroll:
		return frappe.throw("You are not allowed to enroll for this course")

	# Enroll in program
	program_enrollment = student.enroll_in_program(program_name)
	return program_enrollment.name

def has_super_access():
	current_user = frappe.get_doc('User', frappe.session.user)
	roles = set([role.role for role in current_user.roles])
	return bool(roles & {'Administrator', 'Instructor', 'Education Manager', 'System Manager', 'Academic User'})

# def get_program_enrollment(program_name):
# 	"""
# 	Function to get program enrollments for a particular student for a program
# 	"""
# 	student get_current_student()
# 	if not student:
# 		return None
# 	else:
# 		enrollment = frappe.get_all("Program Enrollment", filters={'student':student.name, 'program': program_name})
# 		if enrollment:
# 			return enrollment[0].name
# 		else:
# 			return None

# def get_program_and_enrollment_status(program_name):
# 	program = frappe.get_doc('Program', program_name)
# 	is_enrolled = bool(get_program_enrollment(program_name)) or check_super_access()
# 	return {'program': program, 'is_enrolled': is_enrolled}

# def get_course_enrollment(course_name):
# 	student = get_current_student()
# 	if not student:
# 		return None
# 	enrollment_name = frappe.get_all("Course Enrollment", filters={'student': student.name, 'course':course_name})
# 	try:
# 		name = enrollment_name[0].name
# 		enrollment = frappe.get_doc("Course Enrollment", name)
# 		return enrollment
# 	except:
# 		return None

def create_student_from_current_user():
	user = frappe.get_doc("User", frappe.session.user)

	student = frappe.get_doc({
		"doctype": "Student",
		"first_name": user.first_name,
		"last_name": user.last_name,
		"student_email_id": user.email,
		"user": frappe.session.user
		})

	student.save(ignore_permissions=True)
	return student

def enroll_in_course(course_name, program_name):
	student = get_current_student()
	return student.enroll_in_course(course_name=course_name, program_enrollment=get_program_enrollment(program_name))

def check_content_completion(content_name, content_type, enrollment_name):
	activity = frappe.get_all("Course Activity", filters={'enrollment': enrollment_name, 'content_type': content_type, 'content': content_name})
	if activity:
		return True
	else:
		return False

def check_quiz_completion(quiz, enrollment_name):
	attempts = frappe.get_all("Quiz Activity", filters={'enrollment': enrollment_name, 'quiz': quiz.name}, fields=["name", "activity_date", "score", "status"])
	status = False if quiz.max_attempts == 0 else bool(len(attempts) == quiz.max_attempts)
	score = None
	result = None
	if attempts:
		if quiz.grading_basis == 'Last Highest Score':
			attempts = sorted(attempts, key = lambda i: int(i.score), reverse=True)
		score = attempts[0]['score']
		result = attempts[0]['status']
		if result == 'Pass':
			status = True
	return status, score, result