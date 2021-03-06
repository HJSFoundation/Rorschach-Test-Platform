import webapp2
import networkx as nx

from google.appengine.ext import db
from utils import conf, sessionmanager
from google.appengine.api import memcache

conf = conf.Config()
cache = memcache.Client()

def loadGraph(nodes, edges):
    graph = nx.Graph()
    for node in nodes:
        graph.add_node(node)
    for edge in edges:
        graph.add_edge(edge[0], edge[1])
    graph.name = "Social Network"
    return graph

class MainPage(webapp2.RequestHandler):
    def renderPage(self, extension):
        uid = self.request.get('uid', None)
        network = None
        
        strpage = "Error."
        supported_extensions = [ 'gdf', 'graphml' ]
        if not uid == None and extension in supported_extensions:
            session = sessionmanager.getsession(self)
            if session and session['me']['id'] == uid: 
                network = cache.get("%s_network" % uid)
                if network == None:
                    q = db.GqlQuery("SELECT * FROM Network WHERE uid = :1", uid)
                    network = q.fetch(1)
                    if len(network) == 0: network = None
                    else:
                        network = network[0]
                        cache.add("%s_network" % uid, network, 60*60)
        
                if network:
                    graph = loadGraph(network.getnodes(), network.getedges())
                    
                    strpage = ''
                    if extension == 'gdf':
                        for line in nx.generate_gdf(graph):
                            strpage += line + '\n'
                        self.response.headers['Content-Type'] = "text/gdf"
                            
                    if extension == 'graphml':
                        for line in nx.generate_graphml(graph):
                            strpage += line + '\n'
                        self.response.headers['Content-Type'] = "xml/graphml"
            
        self.response.out.write(strpage)

    def get(self, extension):
        self.renderPage(extension)

    def post(self, extension):
        self.renderPage(extension)
