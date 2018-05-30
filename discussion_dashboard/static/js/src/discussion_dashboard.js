/* Javascript for DiscussionDashboardXBlock. */
function DiscussionDashboardXBlock(runtime, element) {

var handle_Url= runtime.handlerUrl(element, 'get_discussion_id');

$(document).ready(function (){
	var option = $('#discussion_topic_id').find('option:selected');
	discussion_id = option.val();
	populateThreads(discussion_id);
});

function populateThreads(discussion_id){
	$('#tableBody').empty();
	$('#noThread').hide();
        $('#loader').show();
        var html = '<p>Loading Data ...</p>'
        $('#loader').html(html);
        $.ajax({
            type: "POST",
            url: handle_Url,
            data: JSON.stringify({discussion_id:discussion_id}),
            success: function (threads) {
		document.getElementById("thread_details").innerHTML = JSON.stringify(threads);
	        $('#loader').hide();
		if(Object.keys(threads).length === 0){
		    $('#tableBody').empty();
		    $('#noThread').show();
                    var html = '<p>There are not yet any participation for the discussion topic selected</p>'
                    $('#noThread').html(html);
                }
		else {
		$('#noThread').hide();
		$('#tableBody').empty();
                var tbody = ""
                for (username in threads){
                        tbody += "<tr>"
                        tbody += "<td><a href=#tableData class='threads_popup' id=" +username+ ">" +threads[username].full_name+ "</a></td>"
                        tbody += "<td>" +threads[username].thread_count+ "</td>"
                        tbody += "<td>" +threads[username].comments_count+ "</td>"
                        tbody += "</tr>"
                }
		$("#tableData").children("tbody").append(tbody)
		}
	        $('.threads_popup').click(function () {
	            selected_user = this.id
		    var option = $('#discussion_topic_id').find('option:selected');
                    discussion_topic = option.text()
		    var myWindow = window.open("", "", "width=720,height=480")
		    var thread_details = document.getElementById("thread_details").innerHTML
    		    thread_details = JSON.parse(thread_details);
		    var html = ""
		    html += '<!DOCTYPE html>'
		    html += '<html>'
		    html += '<head>'
		    html += '<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.0.13/css/all.css" integrity="'
		    html += 'sha384-DNOHZ68U8hZfKXOrtjWvjxusGo9WQnrNx2sqG0tfsghAvtVlRW3tvkXWZh58N9jp" crossorigin="anonymous">'
		    html += '</head>'
		    html += '<body>'
		    html += '<h1>Discussion Activity for: '+thread_details[selected_user].full_name+' ('+thread_details[selected_user].email+')</h1>'
		    html += '<h2>Topic: '+discussion_topic+'</h2>'
		    html += '<hr>'
		    html += '<h2>Threads</h2>'
		    if (thread_details[selected_user].thread_detail.length != 0){
			for (item of thread_details[selected_user].thread_detail){
			    html += '<h3><i class="fas fa-comment"></i>&nbsp;&nbsp;&nbsp; '+item.title+'</h3>'
			    html += '<p> '+item.created_at+' </p>'
			    html += '<div class="post-body"> '+item.body+'</div>'
			}
                    }else{
			html += '<p>This user has not started any thread yet<p>'
		    }
		    html += '<hr>'
		    html += '<h2>Comments</h2>'
		    if (thread_details[selected_user].comments_detail.length != 0){
			for (item of thread_details[selected_user].comments_detail){
			    html += '<h3><i class="fas fa-comments"></i>&nbsp;&nbsp;&nbsp;In Response to: '+item.parent+'</h3>'
                            html += '<p> '+item.comment_date+' </p>'
                            html += '<div class="response-body"> '+item.comment_body+'</div>'
			}
		    }else{
			html += '<p>This user has not commented on any thread yet<p>'
		    }
		    html += '</body>'
		    html += '</html>'
    		    myWindow.document.write(html);
    	        })
            }
        });
}
$('#discussion_topic_id').change(function() {

    var option = $(this).find('option:selected');
    discussion_id = option.val();
    populateThreads(discussion_id);
});
}
