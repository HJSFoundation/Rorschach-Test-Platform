import os
import webapp2

from google.appengine.ext import db
from utils import fbutils, conf, sessionmanager
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

conf = conf.Config()
cache = memcache.Client()

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        access_token = self.request.get('token', None)
        session = sessionmanager.getsession(self, access_token=access_token, redirect_uri=fbutils.base_url(self)+'opensesame/access')
        
        objreturn = {}
        objreturn['result'] = False
        objreturn['message'] = 'Wrong session'
        
        if session:
            indexes = cache.get("%s_indexes" % session['me']['id'])
            if indexes == None:
                indexes = {}
                q = db.GqlQuery("SELECT * FROM Index " +
                                "WHERE uid = :1 " +
                                "ORDER BY updated_time DESC",
                                session['me']['id'])
            
                for index in q:            
                    if not index.networkhash == None and \
                    not index.value == None and \
                    not index.name in indexes.keys():
                        indexes[index.name] = index
                        
                cache.add("%s_indexes" % session['me']['id'], indexes, 60*60)
            
            for index in indexes.values():
                if not index.networkhash == None and not index.value == None:
                    indexes[index.name] = (conf.INDEX_TYPES[index.name]) % index.value
            
            for index in conf.INDEXES.keys():
                if not index in indexes: indexes[index] = "<null>"
            
            SERVER_ADDRESS = ('127.0.0.1', 33333)
            
            reqired_indexes = []
            try: reqired_indexes = eval(self.request.get('reqired_indexes'))
            except: pass
            
            template_values = {
                'appId': conf.FBAPI_APP_ID,
                'token': session['access_token'],
                'app': session['appid'],
                'conf': conf,
                'me': session['me'],
                'roles': session['roles'],
                'isdesktop': session['isdesktop'],
                'header': ''}
            
            root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
            self.response.out.write(template.render(os.path.join(root, 'templates/_header.html'), template_values))
            
            self.response.out.write('<header class="clearfix">')
            self.response.out.write('<p id="picture" style="background-image: url(/static/images/macchie.jpg); background-size: 64px 64px"></p>')
            self.response.out.write('<h1>Rorschach Test Platform index value retrieval for OpenSesame</h1>')
            self.response.out.write('</header>')
            
            self.response.out.write('<section id="normalsection" class="clearfix">')
            self.response.out.write('<h3>Index values to be submitted to the OpenSesame test</h3>')
            self.response.out.write('<p>The test you are about to take wants to download the values of some index computed on Rorschach Test Platform.</p>')
            self.response.out.write('<p>To proceed you have to verify that all needed indexes are computed for your profile, and then click on the "Save index values" button below.</p>')
            self.response.out.write('<p>If you haven\'t done already, you can compute your network statistics <a href="#" onclick="computeNetworkStatistics()">here</a>.</p>')
            self.response.out.write('<p><div id="computation"></div><br/>&nbsp;</p>')
      
            self.response.out.write('<script type="text/javascript">\n')
            self.response.out.write('<!--\n')
            self.response.out.write('  window.fbAsyncInit = function() {')
            self.response.out.write('    FB.init({\n')
            self.response.out.write('      appId      : ' + conf.FBAPI_APP_ID + ', // App ID\n');
            self.response.out.write('      channelUrl : "/static/pages/channel.html", // Channel File\n');
            self.response.out.write('      status     : true, // check login status\n');
            self.response.out.write('      cookie     : true, // enable cookies to allow the server to access the session\n');
            self.response.out.write('      xfbml      : true  // parse XFBML\n');
            self.response.out.write('    });\n');
            self.response.out.write('  };\n');
            self.response.out.write('  function computeNetworkStatistics() {\n');
            self.response.out.write('      FB.api("/me/friends", {fields: "id"}, function(response) {\n');
            self.response.out.write('        if (response.error) {\n');
            self.response.out.write('            $("#computation").text("Error occured while connecting to Facebook: " + response.error);\n');
            self.response.out.write('        } else {\n');
            self.response.out.write('          var nodes = [];\n');
            self.response.out.write('          var edges = [];\n');
            self.response.out.write('          var numEdges = 0;\n');
            self.response.out.write('          var totEdges = 0;\n');
            self.response.out.write('          for (var i = 0, l = response.data.length; i < l; i++) {\n');
            self.response.out.write('            totEdges = l;\n');
            self.response.out.write('            var friend = response.data[i];\n');
            self.response.out.write('            nodes.push(friend.id);\n');
            self.response.out.write('            FB.api("/me/mutualfriends/" + friend.id, {fields: "id"}, (function(curId) {\n');
            self.response.out.write('                return function(response) {\n');
            self.response.out.write('                  if (!response.error) {\n');
            self.response.out.write('                      $("#computation").text("Downloading friends information: " + (numEdges+1) + "/" + totEdges + " ...");\n');
            self.response.out.write('                      for (var i = 0, l = response.data.length; i < l; i++) {\n');
            self.response.out.write('                          edges.push([curId, response.data[i].id]);\n');
            self.response.out.write('                      }\n');
            self.response.out.write('                  }\n');
            self.response.out.write('                  numEdges++;\n');
            self.response.out.write('                  if (numEdges == totEdges) {\n');
            self.response.out.write('                    computedStatistics(nodes, edges);\n');
            self.response.out.write('                    $("#computation").text();\n');
            self.response.out.write('                  }\n');
            self.response.out.write('                }\n');
            self.response.out.write('            }(friend.id)));\n');
            self.response.out.write('          }\n');
            self.response.out.write('        }\n');
            self.response.out.write('      });\n');
            self.response.out.write('    }\n');
            self.response.out.write('    function computedStatistics(nodes, edges) {\n');
            self.response.out.write('      $.ajax({\n');
            self.response.out.write('        type : "POST",\n');
            self.response.out.write('        url : "/storenetwork",\n');
            self.response.out.write('        dataType : "json",\n');
            self.response.out.write('        data: {\n');
            self.response.out.write('          access_token: "' + access_token + '",\n');
            self.response.out.write('          id : "' + session['me']['id'] + '",\n');
            self.response.out.write('          nodes: JSON.stringify(nodes),\n');
            self.response.out.write('          edges: JSON.stringify(edges)\n');
            self.response.out.write('        },\n');
            self.response.out.write('        success : function(data){\n');
            self.response.out.write('          window.location.reload();\n');
            self.response.out.write('        },\n');
            self.response.out.write('        error : function(XMLHttpRequest, textStatus, errorThrown) {\n');
            self.response.out.write('          $("#computation").text("Error while sending network data to Rorschach Test Platform.");\n');
            self.response.out.write('        }\n');
            self.response.out.write('      });\n');
            self.response.out.write('  }\n');
            self.response.out.write('//-->\n')
            self.response.out.write('</script>')
            
            
             
            self.response.out.write('<form action="http://%s:%s/" method="post" name="valueSubmit" id="valueSubmit">' % SERVER_ADDRESS)
            
            self.response.out.write('<table width="800px" style="border: 1px solid black">')
            self.response.out.write('<thead><td style="padding: 5px"><strong>Index Name</strong></td><td style="padding: 5px"><strong>Computed value</strong></td><td style="padding: 5px"><strong>Action</strong></td></thead>')
            for cur_index in reqired_indexes: 
                self.response.out.write('<tr><td id="' + cur_index + '_name" style="padding: 5px"><a href="/index/' + session['me']['id'] + '/' + cur_index + '" target="_blank">' + cur_index + '</a></td>')
                self.response.out.write('<td id="' + cur_index + '_value" style="padding: 5px">' + (indexes[cur_index] == "<null>" and "&lt;null&gt;" or str(indexes[cur_index])) + '</td>')
                self.response.out.write('<td><p class="button"><a href="#" class="facebook-button" id="' + cur_index + '_button">')
                self.response.out.write('<span class="plus">Compute</span></a></p></td></tr>')
                self.response.out.write('<input type="hidden" id="' + cur_index + '" name="' + cur_index + '" value="' + str(indexes[cur_index]) + '" />')
                self.response.out.write('<script type="text/javascript">\n')
                self.response.out.write('<!--\n')
                self.response.out.write('$(document).ready(function(){\n')
                self.response.out.write('$("#' + cur_index + '_button").click(function() { $.ajax({ type : "POST", url : "/computeprofileindex", dataType : "json", ')
                self.response.out.write('data: { id : "' + session['me']['id'] + '", access_token : "' + access_token +  '", index : "' + cur_index + '" },')
                self.response.out.write('success: function(data) { if (data.error === true) { alert("Error computing index: ' + cur_index + '"); } else { ')
                self.response.out.write('if (data.value != "") { $("#' + cur_index + '_value").text(data.value); $("#' + cur_index + '").val(data.value); } ')
                self.response.out.write('else { alert("The computation has been sent background. Hit che compute button in a few minutes to get the computed value."); } } },')
                self.response.out.write('error: function(XMLHttpRequest, textStatus, errorThrown) { alert("Error computing index: ' + cur_index + '"); } }); ')
                self.response.out.write(' return false; }); });\n') 
                self.response.out.write('// -->\n')
                self.response.out.write('</script>')
                
            self.response.out.write('</table>')
            self.response.out.write('</form><p><br/>')
            
            self.response.out.write('<p class="button"><a href="#" class="facebook-button" onclick="$(\'#valueSubmit\').submit();">')
            self.response.out.write('<span class="plus">Save index values</span></a></p>')
            self.response.out.write('</section>')
            
            self.response.out.write(template.render(os.path.join(root, 'templates/_footer.html'), template_values))
        else:
            self.redirect(fbutils.oauth_login_url(self=self, next_url=fbutils.base_url(self)+'opensesame/access'))
        
    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()
