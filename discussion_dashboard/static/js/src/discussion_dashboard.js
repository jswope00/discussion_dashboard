/* Javascript for DiscussionDashboardXBlock. */
function DiscussionDashboardXBlock(runtime, element) {

var handle_Url= runtime.handlerUrl(element, 'get_discussion_id');

$('#discussion_topic_id').change(function() {

    var option = $(this).find('option:selected');
    discussion_id = option.val();

        $.ajax({
            type: "POST",
            url: handle_Url,
            data: JSON.stringify({discussion_id:discussion_id}),
            success: function (threads) {
		if(Object.keys(threads).length === 0){
		    $('#tableBody').empty();
		    $('#emptyThread').show();
                    var html = '<p>There are not yet any participation for the discussion topic selected</p>'
                    $('#emptyThread').html(html);
                }
		else {
		$('#emptyThread').hide();
		$('#tableBody').empty();
                var tbody = ""
                for (username in threads){
                        tbody += "<tr>"
                        tbody += "<td><a href=" +threads[username].url+ ">" +threads[username].email+ "</a></td>"
                        tbody += "<td>" +threads[username].thread_count+ "</td>"
                        tbody += "<td>" +threads[username].comments_count+ "</td>"
                        tbody += "</tr>"
                }
		$("#tableData").children("tbody").append(tbody)
		}
            }
        });
});
}
