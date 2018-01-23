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

    def get_thread_elements(self, discussion_id):
	course = self.get_course()
        threads = cc.Thread.search({
            'course_id': unicode(course), 'commentable_id': discussion_id 	#'commentable_id': "40b963b21ac147aa9bf4b1350a1ec48c"
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
	        tableData[threadOwner] = {'thread_count': 1, 'comments_count': 0}
	        tableData[threadOwner]['url'] = self.get_discussion_summary_url(course, thread['user_id'])
	    else:
		tableData[threadOwner]['thread_count'] += 1

	    if 'children' in thread:
	        responses = thread['children']
	    else: #for question type
		responses = thread['endorsed_responses'] + thread['non_endorsed_responses']
	    # Not adding responses in comments as its reqirement

	    for response in responses:
		comments = response['children']

		responseOwner = response['username']
		if responseOwner not in tableData:
		    tableData[responseOwner] = {'thread_count': 0, 'comments_count': 1}
                    tableData[responseOwner]['url'] = self.get_discussion_summary_url(course, response['user_id'])
                else:
                    tableData[responseOwner]['comments_count'] += 1

		for comment in comments:
		    commentOwner = comment['username']
		    if commentOwner not in tableData:
			tableData[commentOwner] = {'thread_count': 0, 'comments_count': 1}
			tableData[commentOwner]['url'] = self.get_discussion_summary_url(course, comment['user_id'])
		    else:
			tableData[commentOwner]['comments_count'] += 1

	users = _get_users(course)
        for user in users:
            if user.username in tableData:
                tableData[user.username]['email'] = user.email
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

