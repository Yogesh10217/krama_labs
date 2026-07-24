"""
app/jobs/ — Phase 10: Async Job Execution Framework

Package structure:
  context.py       — JobContext (correlation ID propagation)
  cancellation.py  — CancellationToken (cooperative cancellation)
  queue.py         — JobQueueProvider interface + InMemoryJobQueue
  stage.py         — PipelineStage abstract interface
  state_machine.py — PipelineStateMachine (legal transitions)
  registry.py      — Concrete stage implementations (typed tasks)
  executor.py      — JobExecutor (orchestrates a single execution)
  dispatcher.py    — JobDispatcher (submit + idempotency)
  worker.py        — BackgroundWorker (polling + heartbeat)
"""
