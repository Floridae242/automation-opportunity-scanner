# User Flows

## Happy path
Dashboard -> Project -> New Process -> Describe -> Analyze -> Review draft -> Confirm -> Analyze opportunities -> Prioritize -> Opportunity detail -> Report.

## Missing metrics path
Analyze -> system identifies missing frequency/duration/error/integration facts -> analyst sends questions to process owner -> update process version -> rerun -> score confidence improves.

## Failed model path
Start analysis -> timeout/schema failure -> job marked failed -> preserve intake -> user retries or manually creates steps -> no data loss.

## Version correction path
Reviewed process -> new information -> create new process version -> edit -> review -> run new analysis -> compare historical run.
