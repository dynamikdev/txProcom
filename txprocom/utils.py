##################################
##################################
## Consumer/producer System Based 
## technic
##################################
##################################

from zope.interface import implements
from twisted.internet.interfaces import IPushProducer,IConsumer
from .protocol import ProcomProcess,ProcomProtocol
from .message import EventMessage


class EventC2PResume(EventMessage):
    def __init__(self):
	EventMessage.__init__(self,keys={"EventC2P":"RESUME"})

class EventC2PPause(EventMessage):
    def __init__(self):
	EventMessage.__init__(self,keys={"EventC2P":"PAUSE"})

class EventC2PStop(EventMessage):
    def __init__(self):
	EventMessage.__init__(self,keys={"EventC2P":"STOP"})

class EventP2CWriteMessage(EventMessage):
    def __init__(self,data):
	EventMessage.__init__(self,keys={"EventP2C":"DATA"},data=data)
    #def __str__(self):
	#return "EventP2CWriteMessage - "+str(self.keys)+" # "+str(self.getBody())



class ChildProducer(ProcomProcess):
    implements(IPushProducer)
    def eventReceived(self,event):
	if event.keys.has_key("EventC2P"):
	    {"RESUME":self.resumeProducing,
	     "PAUSE":self.pauseProducing,
	     "STOP":self.stopProducing}[event.keys["EventC2P"]]()
    def writeToConsumer(self,data):
	return self.send(EventP2CWriteMessage(data=data))
    def resumeProducing(self):
	pass
    def pauseProducing(self):
	pass
    def stopProducing(self):
	pass



class ChildProducerProtocol(ProcomProtocol):
    consumers = []
    def eventReceived(self,event):
	if event.keys.has_key("EventP2C"):
	    if event.keys["EventP2C"] == "DATA":
		#print "ON RECOI DE LA DATA"
		for c in self.consumers:
		    #print "ON lecrit a :",c
		    c.write(event.getBody())
    def resumeProducing(self):
	self.onStart.addCallback(lambda r:self.send(EventC2PResume()))
    def pauseProducing(self):
	self.onStart.addCallback(lambda r:self.send(EventC2PPause()))
    def stopProducing(self):
	self.onStart.addCallback(lambda r:self.send(EventC2PStop()))

class FatherConsumer(object):
    producers=[]
    
    def registerProducer(self,producer, streaming=True):
	""" register a producer that's must be a ChildProducerProtocol
	streaming argument is use less"""
	assert isinstance(producer,ChildProducerProtocol), "Producer Must Be A ChidProducerProtocol"
	producer.consumers.append(self)
	self.producers.append(producer)
	
    def unregisterProducer(self):
	for producer in self.producers:
	    producer.consumers.remove(self)
	    self.producers.remove(producer)
    def write(self,data):
	pass
    