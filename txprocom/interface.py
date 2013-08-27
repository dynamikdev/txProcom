from zope.interface import Interface,implements


class IProcomProtocol(Interface):
    """Interface pour adaptation"""
    def askHim(methode,args,kwargs,keys={}):
	""""""
    def eventReceived(event):
	""""""
    def infoReceived(info):
	""""""
    def outReceived(data):
	""""""
    def errReceived(data):
	""""""
