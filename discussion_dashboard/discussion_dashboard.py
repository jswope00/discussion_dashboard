"""TO-DO: Write a description of what this XBlock is."""

from django.template import Template, Context
import logging
import pkg_resources
import operator
import itertools
import collections
from xblock.core import XBlock
from xblock.fields import Scope, Integer, String, List
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
import lms.lib.comment_client as cc
from lms.djangoapps.django_comment_client.utils import get_discussion_category_map,get_accessible_discussion_xblocks,get_discussion_categories_ids
from lms.djangoapps.django_comment_client.constants import TYPE_ENTRY
from django.contrib.auth.models import User
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.courses import get_course_with_access, get_course_by_id
from courseware import courses
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from datetime import datetime, timedelta
from pytz import timezone
import pytz
import re

log = logging.getLogger(__name__)

def _get_users(course_id):
    enrollment_qset = User.objects.filter(
        is_active=True,
        courseenrollment__course_id=course_id,
        courseenrollment__is_active=True
    )
    return enrollment_qset

def _get_current_user(user_id):
     return User.objects.get(id=user_id)

@XBlock.needs("i18n")
class DiscussionDashboardXBlock(XBlock):
    STUDENT_VIEW_TEMPLATE = "discussion_dashboard.html"
    CSS_FILE = "static/css/discussion_dashboard.css"

    display_name = String(
        default="Forum Participation Dashboard", scope=Scope.settings,
        help="Display name for this block."
    )

    def _(self, text):
        """ translate text """
        return self.runtime.service(self, "i18n").ugettext(text)

    def resource_string(self, path):  # pylint:disable=no-self-use
        """
        Handy helper for getting resources from our kit.
        """
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def create_fragment(self, html, context=None, css=None, javascript=None, initialize=None):
        """
        Create an XBlock, given an HTML resource string and an optional context, list of CSS
        resource strings, list of JavaScript resource strings, and initialization function name.
        """
        html = Template(self.resource_string(html))
        context = context or {}
        css = css or [self.CSS_FILE]
        javascript = javascript or []
        frag = Fragment(html.render(Context(context)))
        for sheet in css:
            frag.add_css(self.resource_string(sheet))
        for script in javascript:
            frag.add_javascript(self.resource_string(script))
        if initialize:
            frag.initialize_js(initialize)
        return frag

    def get_course(self):

	return self.scope_ids.usage_id.course_key

    def get_current_user_id(self):

        return self.scope_ids.user_id

    def get_discussion_summary_url(self, course, user_id):

        return "/courses/{0}/discussion/forum/users/{1}".format(course, user_id)

    def get_discussion_topics(self, course_id):

	user_id = self.get_current_user_id() #user id retrieved via function
        user_logged_in_object  = _get_current_user(user_id) #This is User Profile Object for current logged in user
        course_object = modulestore().get_course(course_id) #This is course object
        content = get_discussion_category_map(course= course_object, user= user_logged_in_object, cohorted_if_in_list=False, exclude_unstarted=True)
	categories_id = get_discussion_categories_ids(course_object, user_logged_in_object)
	discussion_details = []
        for category,info in sorted(content["subcategories"].items()):
            for subcategory,value in sorted(info["entries"].items()):
		discussion_details.append({"name" : category + " / " + subcategory, "id" : value["id"]})
	return discussion_details

    @XBlock.json_handler
    def get_discussion_id(self, data, suffix=''):
	discussion_id = data.get('discussion_id')
	data = self.get_thread_elements(discussion_id)
	return data

    def date_conversion(self, created_at):
        created_at = datetime.strptime(created_at,'%Y-%m-%dT%H:%M:%SZ')
        utc = pytz.timezone('UTC')
        aware_date = utc.localize(created_at)
        aware_date.tzinfo
        ast = pytz.timezone('America/Grenada')
        ast_date = aware_date.astimezone(ast)
        ast_date.tzinfo
        date_converted = ast_date.strftime('%Y-%m-%d %H:%M:%S %Z')
	return date_converted

    def repl_func(self, matchobj):
        return str(matchobj.group(1))

    def filter_symbol_from_thread_body(self, thread_body):
        if re.search("(<.*?>)", thread_body, re.IGNORECASE):
            thread_body = re.sub(r'\<(.*?)\>', self.repl_func, thread_body)
            return thread_body
        else:
            return thread_body

    def get_thread_elements(self, discussion_id):
	course = self.get_course()
	num_pages = cc.Thread.search({'course_id': unicode(course), 'commentable_id': discussion_id}).num_pages
        threads = cc.Thread.search({
            'course_id': unicode(course), 'commentable_id': discussion_id, 'per_page': num_pages * 20
        }).collection
	tableData = {}
	for thread in threads:
	    thread = cc.Thread.find(thread['id']).retrieve(
            	with_responses=True,
            	recursive=True,
            	user_id=self.get_current_user_id()
            ).to_dict()
	    threadOwner = thread['username']
	    if threadOwner not in tableData:
	        tableData[threadOwner] = {'thread_count': 1, 'comments_count': 0, 'comments_detail':[]}
	        tableData[threadOwner]['url'] = self.get_discussion_summary_url(course, thread['user_id'])
		tableData[threadOwner]['thread_detail'] = [{'id':thread['id'],
							    'title':thread['title'],
							    'created_at':self.date_conversion(thread['created_at']),
							    'body':self.filter_symbol_from_thread_body(thread['body'])}]
	    else:
		tableData[threadOwner]['thread_count'] += 1
                tableData[threadOwner]['thread_detail'] += [{'id':thread['id'],
							     'title':thread['title'],
							     'created_at':self.date_conversion(thread['created_at']),
							     'body':self.filter_symbol_from_thread_body(thread['body'])}]

	    if 'children' in thread:
	        responses = thread['children']
	    else: #for question type
		responses = thread['endorsed_responses'] + thread['non_endorsed_responses']
	    for response in responses:
		comments = response['children']

		responseOwner = response['username']
		if responseOwner not in tableData:
		    tableData[responseOwner] = {'thread_count': 0, 'comments_count': 1, 'thread_detail':[]}
                    tableData[responseOwner]['url'] = self.get_discussion_summary_url(course, response['user_id'])
		    tableData[responseOwner]['comments_detail'] = [{'parent': thread['title'],
								    'comment_body': self.filter_symbol_from_thread_body(response['body']),
								    'comment_date':self.date_conversion(response['created_at'])}]
                else:
                    tableData[responseOwner]['comments_count'] += 1
                    tableData[responseOwner]['comments_detail'] += [{'parent': thread['title'],
								     'comment_body': self.filter_symbol_from_thread_body(response['body']),
								     'comment_date':self.date_conversion(response['created_at'])}]
		for comment in comments:
		    commentOwner = comment['username']
		    if commentOwner not in tableData:
			tableData[commentOwner] = {'thread_count': 0, 'comments_count': 1, 'thread_detail':[]}
			tableData[commentOwner]['url'] = self.get_discussion_summary_url(course, comment['user_id'])
			tableData[commentOwner]['comments_detail'] = [{'parent': thread['title'],
								       'comment_body': self.filter_symbol_from_thread_body(comment['body']),
								       'comment_date': self.date_conversion(comment['created_at'])}]
		    else:
			tableData[commentOwner]['comments_count'] += 1
                        tableData[commentOwner]['comments_detail'] += [{'parent': thread['title'],
									'comment_body': self.filter_symbol_from_thread_body(comment['body']),
									'comment_date': self.date_conversion(comment['created_at'])}]

	""" Get ALL active users in course """
	users = _get_users(course)
	""" For each user enrolled in course """
        for user in users:
            """ If the username of the user in the course exists in the Table of Discussion data """
            if user.username in tableData:
                tableData[user.username]['email'] = user.email
	        tableData[user.username]['full_name'] = user.profile.name
            """ else:
	        tableData[user.username]['email'] = tableData[user.username]
	        tableData[user.username]['full_name'] = tableData[user.username]"""
        return tableData

    def student_view(self, context=None):
        """
        The primary view of the leaderboard, shown to students when viewing courses.
        """
        try:
	    discussion_details = self.get_discussion_topics(self.get_course())
	    data = self.get_thread_elements(discussion_details[0]['id'])
        except Exception:
            log.exception("Unable to get_thread_elements() for forum participation dashboard.")
            return Fragment(self._(u"An error occurred. Unable to display forum participation dashboard."))

        context = {
            'threads': data,
	    'discussion': discussion_details,
            'display_name': self.display_name
        }
        return self.create_fragment(
            "static/html/{}".format(self.STUDENT_VIEW_TEMPLATE),
            context=context,
            javascript = ["static/js/src/discussion_dashboard.js"],
	    initialize = 'DiscussionDashboardXBlock'
        )

