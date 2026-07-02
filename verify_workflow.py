import os
os.environ['MOCK_MODE'] = 'true'
from orchestrator.workflow import WorkflowOrchestrator

w = WorkflowOrchestrator()
w.create_workflow('Build a simple todo app with login and persistence')
print('before', len(w.task_graph.tasks))
w.run()
print('after', len(w.task_graph.tasks))
print('expanded', w.context.get('workflow_expanded'))
print('code_artifacts', len(w.context.get('code_artifacts', [])))
print('test_artifacts', len(w.context.get('test_artifacts', [])))
