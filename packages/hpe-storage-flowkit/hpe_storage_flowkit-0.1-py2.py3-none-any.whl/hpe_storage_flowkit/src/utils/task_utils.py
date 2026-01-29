TASK_DONE = 1
TASK_ACTIVE = 2
TASK_CANCELLED = 3
TASK_FAILED = 4

class Task(object):
    
    def __init__(self, object_hash):
        if object_hash is None:
            return
    
        self.task_id = object_hash.get('id')
    
        self.status = object_hash.get('status')
    
        self.name = object_hash.get('name')
    
        self.type = object_hash.get('type')
		