import logging
for k,v in  logging.Logger.manager.loggerDict.items()  :
        print('+ [%s] {%s} ' % (str.ljust( k, 20)  , str(v.__class__)[8:-2]) )
        if not isinstance(v, logging.PlaceHolder):
            for h in v.handlers:
                print('     +++',str(h.__class__)[8:-2] )
import inspect
# print(inspect.getsource(logging))
logging.getLogger('foo').addHandler(logging.NullHandler())
logger=logging.getLogger('logger')
logger.debug('The system may break down debug')
logger.info('The system may break down info')
logger.warning('The system may break down warning')
logger.error('The system may break down error')
for k,v in  logging.Logger.manager.loggerDict.items()  :
        print('+ [%s] {%s} ' % (str.ljust( k, 20)  , str(v.__class__)[8:-2]) )
        if not isinstance(v, logging.PlaceHolder):
            for h in v.handlers:
                print('     +++',str(h.__class__)[8:-2] )