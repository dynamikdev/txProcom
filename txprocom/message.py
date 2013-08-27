try:
    from cPickle import dumps,loads
except ImportError:
    from pickle import dumps,loads 

import re



class BasicMessage(object):
    __type__ = None
    message = None
    def __init__(self,keys={},message=None):
	self.keys = keys 
	if message:
	    self.message = message
    def setByRawData(self,rawdata):
	self.data = rawdata
	part = rawdata.split(r"\2")
	spl,rawmess = part[0],r"\2".join(part[1:])
	self.keys = dict([e.split("=") for e in spl.split("\n") if "=" in e])
	self.digestMessage(rawmess)
	
    def digestMessage(self,message):
	self.message = message
    def __str__(self):
	return str(self.keys)+str(self.message)
    def __eq__(self,other):
	if not isinstance(other,BasicMessage):
	    return False
	return self.__type__ == other.__type__ and str(self) == str(other)
    def encode(self):
	if self.__type__ is None:
	    raise RuntimeError("Using BasicMessage is not allowed") 
	return r"%s\1%s\2%s\0"%(self.__type__,"\n".join([str(k)+"="+str(self.keys[k]) for k in self.keys]),self.getBody())
    def getBody(self):
	return self.message 


class CommandMessage(BasicMessage):
    __type__ = "COMMAND"

class QuitCommand(CommandMessage):
    message = "QUIT"
    
class PingCommand(CommandMessage):
    message = "PING"
class PongCommand(CommandMessage):
    message = "PONG"


class InfoMessage(BasicMessage):
    "Information classique"
    __type__ = "INFO"

class LaunchedMessage(InfoMessage):
    "Information classique"
    message = "LAUNCHED"

    
    
class AskMessage(BasicMessage):
    __type__ = "ASK"
    def __init__(self,keys={},command=None,args=tuple(),kwargs={},id=None):
	BasicMessage.__init__(self,keys)
	self.command = command
	self.args = args
	self.kwargs = kwargs
	self.id=id
    def getBody(self):
	return dumps({"command":self.command,
	              "args":self.args,
	              "kwarg":self.kwargs,
	              "id":self.id})
    def digestMessage(self,message):
	print "On digere la question"
	message = loads(message)
	#print message
	self.command = message["command"]
	if message.has_key("args"):
	    self.args = message["args"]
	if message.has_key("kwargs"):
	    self.kwargs = message["kwargs"]
	self.id = message["id"]
    def __str__(self):
	return "calling of "+str(self.command)+" nb "+str(self.id)
class AnswerMessage(BasicMessage):
    __type__ = "ANSWER"
    def __init__(self,keys={},answer=None,id=None):
	BasicMessage.__init__(self,keys)
	self.id = id
	self.answer = answer
    def getBody(self):
	return dumps({"answer":self.answer,
	              "id":self.id})
    def digestMessage(self,message):
	#print "On digere la reponse"
	message = loads(message)
	self.id = message["id"]
	self.answer = message["answer"]
	
class EventMessage(BasicMessage):
    __type__ = "EVENT"
    def __init__(self,keys={},data=None):
	BasicMessage.__init__(self,keys)
	self.data = data
    def getBody(self):
	return dumps(self.data)
    def digestMessage(self,data):
	self.data = loads(data)
    def __str__(self):
	return str(self.keys)+str(self.data)

typestr = {"INFO":InfoMessage,
           "ANSWER":AnswerMessage,
           "ASK":AskMessage,
           "EVENT":EventMessage,
           "COMMAND":CommandMessage}

	
class BufferMessaging:
    def __init__(self,messageAccepted = typestr.values()):
	self.buffer = ""
	self.messageAccepted = messageAccepted
    def write(self, data):
	self.buffer += data
    def getMessages(self):
	while True:
	    try:
		i = self.buffer.index(r"\0")
	    except ValueError:
		break
	    try:
		msg = self.buffer[:i]
		self.buffer = self.buffer[i+2:]
		part = msg.split(r"\1")
		typemess,rawmess = part[0],r"\1".join(part[1:])
		mess= typestr[typemess]()
	    except ValueError,e:
		print "erreur de split",msg
		raise ValueError("erreur de split",msg)
	    if type(mess) not in self.messageAccepted:
		continue
	    mess.setByRawData(rawmess)
	    yield mess
	    
	raise StopIteration

