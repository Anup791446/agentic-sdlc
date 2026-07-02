from orchestrator.workflow import WorkflowOrchestrator


def test_workflow_expands_after_requirement_analysis(monkeypatch):
    monkeypatch.setenv("MOCK_MODE", "true")

    workflow = WorkflowOrchestrator()
    workflow.create_workflow("Build a simple todo app with login and persistence")

    task = workflow.task_graph.tasks["T1"]
    workflow.execute_task(task)

    summary = workflow.run()

    assert len(workflow.task_graph.tasks) > 1
    assert workflow.context.get("workflow_expanded") is True
    assert summary is not None


def test_mock_mode_generates_requirement_specific_todo_artifacts(monkeypatch):
    monkeypatch.setenv("MOCK_MODE", "true")

    workflow = WorkflowOrchestrator()
    workflow.create_workflow(
        "Build a simple todo app with user login, task creation, update, delete, and persistence."
    )

    summary = workflow.run()

    assert summary.code_artifacts
    assert any("todo" in artifact.content.lower() or "auth" in artifact.content.lower() for artifact in summary.code_artifacts)
    assert summary.test_artifacts
