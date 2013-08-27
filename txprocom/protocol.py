import sys 
import psutil

from twisted.internet.protocol import ProcessProtocol
from twisted.internet.process import ProcessReader,ProcessWriter
from txProcom.message import *
from txProcom.interface import *
from twisted.internet import defer,reactor,fdesc
	
from zope.interface import implements



class ProcomProtocol(ProcessProtocol):
    implements(IProcomProtocol)
    def __init__(self,name,command,executable=sys.executable,messageAccepted = typestr.values()):
	self.tampon = defer.DeferredLock()
        self.name = name
	self.command = command
	self.executable = executable
        self.started = False
        self.onClose = defer.Deferred()
        self.onStart = defer.Deferred()
	self.buffer4 = BufferMessaging(messageAccepted)
	self.onOut = []
	self.onErr = []
	self.counterAsking = 0
	self.pendingAsk = {}
	self.onEvent = []
	self.commands = {}
    def __started__(self):
	self.started = True
    def start(self):
	return reactor.spawnProcess(self, self.executable ,self.command,childFDs={0:"w", 1:"r", 2:"r", 3:"w", 4:"r"})
    def makeConnection(self,p):
	self.process = p
	self.processinfo = psutil.Process(p.pid)
	ProcessProtocol.makeConnection(self,p)
    def inConnectionLost(self):
        """
        This will be called when stdin is closed.
        """
	print "connexion au in perdu"


    def outConnectionLost(self):
        """
        This will be called when stdout is closed.
        """
	print "out perdu"

    def errConnectionLost(self):
        """
        This will be called when stderr is closed.
        """
	print "err perdu"
    def childConnectionLost(self, childFD):
	ProcessProtocol.childConnectionLost(self, childFD)
	print "ON a PERDU :",childFD
    def connectionMade(self):
	self.__started__()
	self.onStart.callback(True)
    def closeMe(self):
	self.send(QuitCommand())
        self.process.write("quit\n")
	self.onStart = defer.Deferred()
        return True
    def childDataReceived(self,childFD, data):
	ProcessProtocol.childDataReceived(self,childFD, data)
	if childFD == 4:
	    self.buffer4.write(data)
	    for m in self.buffer4.getMessages():
		if isinstance(m,AnswerMessage):
		    self.answerReceived(m)
		elif isinstance(m,EventMessage):
		    self.eventReceived(m)
		elif isinstance(m,InfoMessage):
		    self.infoReceived(m)
		elif isinstance(m,AskMessage):
		    self.asking(m)
		elif isinstance(m,CommandMessage):
		    self.command(m)
		else:
		    print "____________________________________"
		    print m
		    print "____________________________________"
		
    def send(self,message):
	return self.tampon.run(self.transport.writeToChild,3, message.encode())
    def answerReceived(self,answer):
	try:
	    if answer.answer != None:
		self.pendingAsk.pop(answer.id).callback(answer.answer)
	    else :
		self.pendingAsk.pop(answer.id)
	except KeyError:
	    raise KeyError("L'appel n'existe pas")
	except Exception,e:
	    raise e
    def eventReceived(self,event):
	pass
    def infoReceived(self,info):
	pass
    def askHim(self,methode,args=(),kwargs={},keys={}):
	#print "!!!!!!!!!!!!!!!!!!***************On demande ",methode,"****************!!!!!!!!!!!!!!!!!"
	nb = self.counterAsking 
	self.counterAsking = self.counterAsking+1
	self.pendingAsk[nb] = defer.Deferred()
	#print self.pendingAsk
	a = AskMessage(command=methode,id=nb,args = args,kwargs = kwargs,keys=keys)
	self.send(a)
	return self.pendingAsk[nb]
    def processExited(self,reason):
        self.onClose.callback(reason)
	self.onStart = defer.Deferred()
    def processEnded(self,reason):
        pass
    def expose(self,methode_name,func,keys={}):
	#print "REF key ",keys.items(),"====>",hash(frozenset(keys.items()))
	if not self.commands.has_key(hash(frozenset(keys.items()))):
	    self.commands[hash(frozenset(keys.items()))]={}
	#print "REF methode_name====>",methode_name
	self.commands[hash(frozenset(keys.items()))][methode_name] = func
    def asking(self,ask):
	def returnResult(res,id_ask):
	    a = AnswerMessage(answer=res,id=id_ask)
	    self.send(a)
	#print "on demande avec ",ask.keys.items(),"(",hash(frozenset(ask.keys.items())),") la commande ",ask.command, " avec ",ask.args,ask.kwargs
	if not self.commands.has_key(hash(frozenset(ask.keys.items()))):
	    #print "pas la keys"
	    return None
	if not self.commands[hash(frozenset(ask.keys.items()))].has_key(ask.command):
	    #print ask.command
	    return None
	#print "Oki on envoi"
	d = defer.maybeDeferred(self.commands[hash(frozenset(ask.keys.items()))][ask.command],*ask.args,**ask.kwargs).addCallback(returnResult,ask.id)
	return d
    def command(self,command):
	pass
	    
class ProcomProcess(object):
    def __init__(self,messageAccepted = typestr.values()):
	self.tampon = defer.DeferredLock()
	self._reader=ProcessReader(reactor, self, 'read', 3)
	self._writer=ProcessWriter(reactor, self, 'write', 4)
	self.buffer = BufferMessaging(messageAccepted)
	self.commands = {}
	self.counterAsking = 0
	self.pendingAsk ={}
    def expose(self,methode_name,func,keys={}):
	#print "REF key ",keys.items(),"====>",hash(frozenset(keys.items()))
	if not self.commands.has_key(hash(frozenset(keys.items()))):
	    self.commands[hash(frozenset(keys.items()))]={}
	#print "REF methode_name====>",methode_name
	self.commands[hash(frozenset(keys.items()))][methode_name] = func
        #def wrapper(func):
            #def wrapped(*arg,**kwarg):
                #print "Avant on passe par moi Appel de ",methode_external_name
                #res = func(*arg,**kwarg)
                #print "c fini"
            #return wrapped
        #return wrapper
    def send(self,message):
	return self.tampon.run(self._writer.write,message.encode())
    
    def receive(self,data):
	self.buffer.write(data)
	for m in self.buffer.getMessages():
	    if isinstance(m,AnswerMessage):
		self.answerReceived(m)
	    elif isinstance(m,EventMessage):
		self.eventReceived(m)
	    elif isinstance(m,InfoMessage):
		self.infoReceived(m)
	    elif isinstance(m,AskMessage):
		self.asking(m)
	    elif isinstance(m,CommandMessage):
		self.command(m)
	    else:
		print "______________?????______________________"
		print m
		print "_______________????_____________________"
    def eventReceived(self,event):
	pass
    def infoReceived(self,info):
	print "info recu",info
    
    def childDataReceived(self, name, data):
	if name == 'read':
	    self.receive(data)
    def asking(self,ask):
	def returnResult(res,id_ask):
	    print "on a le resultat pour ",id_ask," c ",res
	    a = AnswerMessage(answer=res,id=id_ask)
	    self.send(a)
	print "on demande avec ",ask.keys.items(),"(",hash(frozenset(ask.keys.items())),") la commande ",ask.command, " avec ",ask.args,ask.kwargs
	if not self.commands.has_key(hash(frozenset(ask.keys.items()))):
	    print "pas la keys"
	    a = AnswerMessage(answer=None,id=ask.id)
	    self.send(a)
	    return None
	if not self.commands[hash(frozenset(ask.keys.items()))].has_key(ask.command):
	    print ask.command
	    a = AnswerMessage(answer=None,id=ask.id)
	    self.send(a)
	    return None
	print "Oki on envoi"
	d = defer.maybeDeferred(self.commands[hash(frozenset(ask.keys.items()))][ask.command],*ask.args,**ask.kwargs).addCallback(returnResult,ask.id)
	return d
    def childConnectionLost(self,nom,  reason):
        print "ON A Perdu la connection sur ",nom," parce que  : ",reason
	
    def askHim(self,methode,args=(),kwargs={},keys={}):
	#print "!!!!!!!!!!!!!!!!!!=============On demande ",methode,"====================!!!!!!!!!!!!!!!!!"
	nb = self.counterAsking 
	self.counterAsking = self.counterAsking+1
	self.pendingAsk[nb] = defer.Deferred()
	#print self.pendingAsk
	a = AskMessage(command=methode,id=nb,args = args,kwargs = kwargs,keys=keys)
	self.send(a)
	return self.pendingAsk[nb]
    def answerReceived(self,answer):
	try:
	    if answer.answer != None:
		self.pendingAsk.pop(answer.id).callback(answer.answer)
	    else :
		self.pendingAsk.pop(answer.id)
	except KeyError:
	    raise KeyError("L'appel n'existe pas")
	except Exception,e:
	    raise e
    def command(self,command):
	if command == QuitCommand():
	    print "On me demande de quiter"
	    reactor.stop()
	    return True
	raise NotImplemented("Commande inconnue",str(command))
#import sys
#sys.modules['txProcom.procomProcess'] = ProcomProcess()

