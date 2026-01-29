# Shared Types

```python
from anchorbrowser.types import SuccessResponse
```

# Profiles

Types:

```python
from anchorbrowser.types import ProfileRetrieveResponse, ProfileListResponse
```

Methods:

- <code title="post /v1/profiles">client.profiles.<a href="./src/anchorbrowser/resources/profiles.py">create</a>(\*\*<a href="src/anchorbrowser/types/profile_create_params.py">params</a>) -> <a href="./src/anchorbrowser/types/shared/success_response.py">SuccessResponse</a></code>
- <code title="get /v1/profiles/{name}">client.profiles.<a href="./src/anchorbrowser/resources/profiles.py">retrieve</a>(name) -> <a href="./src/anchorbrowser/types/profile_retrieve_response.py">ProfileRetrieveResponse</a></code>
- <code title="get /v1/profiles">client.profiles.<a href="./src/anchorbrowser/resources/profiles.py">list</a>() -> <a href="./src/anchorbrowser/types/profile_list_response.py">ProfileListResponse</a></code>
- <code title="delete /v1/profiles/{name}">client.profiles.<a href="./src/anchorbrowser/resources/profiles.py">delete</a>(name) -> <a href="./src/anchorbrowser/types/shared/success_response.py">SuccessResponse</a></code>

# Sessions

Types:

```python
from anchorbrowser.types import (
    SessionCreateResponse,
    SessionRetrieveResponse,
    SessionDragAndDropResponse,
    SessionGotoResponse,
    SessionRetrieveDownloadsResponse,
    SessionScrollResponse,
    SessionUploadFileResponse,
)
```

Methods:

- <code title="post /v1/sessions">client.sessions.<a href="./src/anchorbrowser/resources/sessions/sessions.py">create</a>(\*\*<a href="src/anchorbrowser/types/session_create_params.py">params</a>) -> <a href="./src/anchorbrowser/types/session_create_response.py">SessionCreateResponse</a></code>
- <code title="get /v1/sessions/{session_id}">client.sessions.<a href="./src/anchorbrowser/resources/sessions/sessions.py">retrieve</a>(session_id) -> <a href="./src/anchorbrowser/types/session_retrieve_response.py">SessionRetrieveResponse</a></code>
- <code title="delete /v1/sessions/{session_id}">client.sessions.<a href="./src/anchorbrowser/resources/sessions/sessions.py">delete</a>(session_id) -> <a href="./src/anchorbrowser/types/shared/success_response.py">SuccessResponse</a></code>
- <code title="post /v1/sessions/{sessionId}/drag-and-drop">client.sessions.<a href="./src/anchorbrowser/resources/sessions/sessions.py">drag_and_drop</a>(session_id, \*\*<a href="src/anchorbrowser/types/session_drag_and_drop_params.py">params</a>) -> <a href="./src/anchorbrowser/types/session_drag_and_drop_response.py">SessionDragAndDropResponse</a></code>
- <code title="post /v1/sessions/{sessionId}/goto">client.sessions.<a href="./src/anchorbrowser/resources/sessions/sessions.py">goto</a>(session_id, \*\*<a href="src/anchorbrowser/types/session_goto_params.py">params</a>) -> <a href="./src/anchorbrowser/types/session_goto_response.py">SessionGotoResponse</a></code>
- <code title="get /v1/sessions/{session_id}/downloads">client.sessions.<a href="./src/anchorbrowser/resources/sessions/sessions.py">retrieve_downloads</a>(session_id) -> <a href="./src/anchorbrowser/types/session_retrieve_downloads_response.py">SessionRetrieveDownloadsResponse</a></code>
- <code title="get /v1/sessions/{sessionId}/screenshot">client.sessions.<a href="./src/anchorbrowser/resources/sessions/sessions.py">retrieve_screenshot</a>(session_id) -> BinaryAPIResponse</code>
- <code title="post /v1/sessions/{sessionId}/scroll">client.sessions.<a href="./src/anchorbrowser/resources/sessions/sessions.py">scroll</a>(session_id, \*\*<a href="src/anchorbrowser/types/session_scroll_params.py">params</a>) -> <a href="./src/anchorbrowser/types/session_scroll_response.py">SessionScrollResponse</a></code>
- <code title="post /v1/sessions/{sessionId}/uploads">client.sessions.<a href="./src/anchorbrowser/resources/sessions/sessions.py">upload_file</a>(session_id, \*\*<a href="src/anchorbrowser/types/session_upload_file_params.py">params</a>) -> <a href="./src/anchorbrowser/types/session_upload_file_response.py">SessionUploadFileResponse</a></code>

## All

Types:

```python
from anchorbrowser.types.sessions import AllStatusResponse
```

Methods:

- <code title="delete /v1/sessions/all">client.sessions.all.<a href="./src/anchorbrowser/resources/sessions/all.py">delete</a>() -> <a href="./src/anchorbrowser/types/shared/success_response.py">SuccessResponse</a></code>
- <code title="get /v1/sessions/all/status">client.sessions.all.<a href="./src/anchorbrowser/resources/sessions/all.py">status</a>() -> <a href="./src/anchorbrowser/types/sessions/all_status_response.py">AllStatusResponse</a></code>

## Recordings

Types:

```python
from anchorbrowser.types.sessions import RecordingListResponse
```

Methods:

- <code title="get /v1/sessions/{session_id}/recordings">client.sessions.recordings.<a href="./src/anchorbrowser/resources/sessions/recordings/recordings.py">list</a>(session_id) -> <a href="./src/anchorbrowser/types/sessions/recording_list_response.py">RecordingListResponse</a></code>

### Primary

Methods:

- <code title="get /v1/sessions/{session_id}/recordings/primary/fetch">client.sessions.recordings.primary.<a href="./src/anchorbrowser/resources/sessions/recordings/primary.py">get</a>(session_id) -> BinaryAPIResponse</code>

## Mouse

Types:

```python
from anchorbrowser.types.sessions import MouseClickResponse, MouseMoveResponse
```

Methods:

- <code title="post /v1/sessions/{sessionId}/mouse/click">client.sessions.mouse.<a href="./src/anchorbrowser/resources/sessions/mouse.py">click</a>(session_id, \*\*<a href="src/anchorbrowser/types/sessions/mouse_click_params.py">params</a>) -> <a href="./src/anchorbrowser/types/sessions/mouse_click_response.py">MouseClickResponse</a></code>
- <code title="post /v1/sessions/{sessionId}/mouse/move">client.sessions.mouse.<a href="./src/anchorbrowser/resources/sessions/mouse.py">move</a>(session_id, \*\*<a href="src/anchorbrowser/types/sessions/mouse_move_params.py">params</a>) -> <a href="./src/anchorbrowser/types/sessions/mouse_move_response.py">MouseMoveResponse</a></code>

## Keyboard

Types:

```python
from anchorbrowser.types.sessions import KeyboardShortcutResponse, KeyboardTypeResponse
```

Methods:

- <code title="post /v1/sessions/{sessionId}/keyboard/shortcut">client.sessions.keyboard.<a href="./src/anchorbrowser/resources/sessions/keyboard.py">shortcut</a>(session_id, \*\*<a href="src/anchorbrowser/types/sessions/keyboard_shortcut_params.py">params</a>) -> <a href="./src/anchorbrowser/types/sessions/keyboard_shortcut_response.py">KeyboardShortcutResponse</a></code>
- <code title="post /v1/sessions/{sessionId}/keyboard/type">client.sessions.keyboard.<a href="./src/anchorbrowser/resources/sessions/keyboard.py">type</a>(session_id, \*\*<a href="src/anchorbrowser/types/sessions/keyboard_type_params.py">params</a>) -> <a href="./src/anchorbrowser/types/sessions/keyboard_type_response.py">KeyboardTypeResponse</a></code>

## Clipboard

Types:

```python
from anchorbrowser.types.sessions import ClipboardSetResponse
```

Methods:

- <code title="post /v1/sessions/{sessionId}/clipboard">client.sessions.clipboard.<a href="./src/anchorbrowser/resources/sessions/clipboard.py">set</a>(session_id, \*\*<a href="src/anchorbrowser/types/sessions/clipboard_set_params.py">params</a>) -> <a href="./src/anchorbrowser/types/sessions/clipboard_set_response.py">ClipboardSetResponse</a></code>

## Agent

Methods:

- <code title="post /v1/sessions/{session_id}/agent/pause">client.sessions.agent.<a href="./src/anchorbrowser/resources/sessions/agent/agent.py">pause</a>(session_id) -> <a href="./src/anchorbrowser/types/shared/success_response.py">SuccessResponse</a></code>
- <code title="post /v1/sessions/{session_id}/agent/resume">client.sessions.agent.<a href="./src/anchorbrowser/resources/sessions/agent/agent.py">resume</a>(session_id) -> <a href="./src/anchorbrowser/types/shared/success_response.py">SuccessResponse</a></code>

### Files

Types:

```python
from anchorbrowser.types.sessions.agent import FileUploadResponse
```

Methods:

- <code title="post /v1/sessions/{sessionId}/agent/files">client.sessions.agent.files.<a href="./src/anchorbrowser/resources/sessions/agent/files.py">upload</a>(session_id, \*\*<a href="src/anchorbrowser/types/sessions/agent/file_upload_params.py">params</a>) -> <a href="./src/anchorbrowser/types/sessions/agent/file_upload_response.py">FileUploadResponse</a></code>

# Tools

Types:

```python
from anchorbrowser.types import (
    ToolFetchWebpageResponse,
    ToolGetPerformWebTaskStatusResponse,
    ToolPerformWebTaskResponse,
)
```

Methods:

- <code title="post /v1/tools/fetch-webpage">client.tools.<a href="./src/anchorbrowser/resources/tools.py">fetch_webpage</a>(\*\*<a href="src/anchorbrowser/types/tool_fetch_webpage_params.py">params</a>) -> str</code>
- <code title="get /v1/tools/perform-web-task/{workflowId}/status">client.tools.<a href="./src/anchorbrowser/resources/tools.py">get_perform_web_task_status</a>(workflow_id) -> <a href="./src/anchorbrowser/types/tool_get_perform_web_task_status_response.py">ToolGetPerformWebTaskStatusResponse</a></code>
- <code title="post /v1/tools/perform-web-task">client.tools.<a href="./src/anchorbrowser/resources/tools.py">perform_web_task</a>(\*\*<a href="src/anchorbrowser/types/tool_perform_web_task_params.py">params</a>) -> <a href="./src/anchorbrowser/types/tool_perform_web_task_response.py">ToolPerformWebTaskResponse</a></code>
- <code title="post /v1/tools/screenshot">client.tools.<a href="./src/anchorbrowser/resources/tools.py">screenshot_webpage</a>(\*\*<a href="src/anchorbrowser/types/tool_screenshot_webpage_params.py">params</a>) -> BinaryAPIResponse</code>

# Extensions

Types:

```python
from anchorbrowser.types import ExtensionManifest, ExtensionListResponse
```

Methods:

- <code title="get /v1/extensions">client.extensions.<a href="./src/anchorbrowser/resources/extensions.py">list</a>() -> <a href="./src/anchorbrowser/types/extension_list_response.py">ExtensionListResponse</a></code>

# Events

Types:

```python
from anchorbrowser.types import EventWaitForResponse
```

Methods:

- <code title="post /v1/events/{event_name}">client.events.<a href="./src/anchorbrowser/resources/events.py">signal</a>(event_name, \*\*<a href="src/anchorbrowser/types/event_signal_params.py">params</a>) -> <a href="./src/anchorbrowser/types/shared/success_response.py">SuccessResponse</a></code>
- <code title="post /v1/events/{event_name}/wait">client.events.<a href="./src/anchorbrowser/resources/events.py">wait_for</a>(event_name, \*\*<a href="src/anchorbrowser/types/event_wait_for_params.py">params</a>) -> <a href="./src/anchorbrowser/types/event_wait_for_response.py">EventWaitForResponse</a></code>

# Task

Types:

```python
from anchorbrowser.types import (
    TaskCreateResponse,
    TaskListResponse,
    TaskRetrieveExecutionResultResponse,
    TaskRunResponse,
)
```

Methods:

- <code title="post /v1/task">client.task.<a href="./src/anchorbrowser/resources/task.py">create</a>(\*\*<a href="src/anchorbrowser/types/task_create_params.py">params</a>) -> <a href="./src/anchorbrowser/types/task_create_response.py">TaskCreateResponse</a></code>
- <code title="get /v1/task">client.task.<a href="./src/anchorbrowser/resources/task.py">list</a>(\*\*<a href="src/anchorbrowser/types/task_list_params.py">params</a>) -> <a href="./src/anchorbrowser/types/task_list_response.py">TaskListResponse</a></code>
- <code title="get /v1/task/{taskId}/executions/{executionId}">client.task.<a href="./src/anchorbrowser/resources/task.py">retrieve_execution_result</a>(execution_id, \*, task_id) -> <a href="./src/anchorbrowser/types/task_retrieve_execution_result_response.py">TaskRetrieveExecutionResultResponse</a></code>
- <code title="post /v1/task/run">client.task.<a href="./src/anchorbrowser/resources/task.py">run</a>(\*\*<a href="src/anchorbrowser/types/task_run_params.py">params</a>) -> <a href="./src/anchorbrowser/types/task_run_response.py">TaskRunResponse</a></code>

# Identities

Types:

```python
from anchorbrowser.types import (
    IdentityCreateResponse,
    IdentityRetrieveResponse,
    IdentityUpdateResponse,
    IdentityDeleteResponse,
    IdentityRetrieveCredentialsResponse,
)
```

Methods:

- <code title="post /v1/identities">client.identities.<a href="./src/anchorbrowser/resources/identities.py">create</a>(\*\*<a href="src/anchorbrowser/types/identity_create_params.py">params</a>) -> <a href="./src/anchorbrowser/types/identity_create_response.py">IdentityCreateResponse</a></code>
- <code title="get /v1/identities/{identity_id}">client.identities.<a href="./src/anchorbrowser/resources/identities.py">retrieve</a>(identity_id) -> <a href="./src/anchorbrowser/types/identity_retrieve_response.py">IdentityRetrieveResponse</a></code>
- <code title="put /v1/identities/{identity_id}">client.identities.<a href="./src/anchorbrowser/resources/identities.py">update</a>(identity_id, \*\*<a href="src/anchorbrowser/types/identity_update_params.py">params</a>) -> <a href="./src/anchorbrowser/types/identity_update_response.py">IdentityUpdateResponse</a></code>
- <code title="delete /v1/identities/{identity_id}">client.identities.<a href="./src/anchorbrowser/resources/identities.py">delete</a>(identity_id) -> <a href="./src/anchorbrowser/types/identity_delete_response.py">IdentityDeleteResponse</a></code>
- <code title="get /v1/identities/{identity_id}/credentials">client.identities.<a href="./src/anchorbrowser/resources/identities.py">retrieve_credentials</a>(identity_id) -> <a href="./src/anchorbrowser/types/identity_retrieve_credentials_response.py">IdentityRetrieveCredentialsResponse</a></code>

# Applications

Types:

```python
from anchorbrowser.types import (
    ApplicationCreateResponse,
    ApplicationRetrieveResponse,
    ApplicationListResponse,
    ApplicationDeleteResponse,
    ApplicationCreateIdentityTokenResponse,
    ApplicationListIdentitiesResponse,
)
```

Methods:

- <code title="post /v1/applications">client.applications.<a href="./src/anchorbrowser/resources/applications/applications.py">create</a>(\*\*<a href="src/anchorbrowser/types/application_create_params.py">params</a>) -> <a href="./src/anchorbrowser/types/application_create_response.py">ApplicationCreateResponse</a></code>
- <code title="get /v1/applications/{application_id}">client.applications.<a href="./src/anchorbrowser/resources/applications/applications.py">retrieve</a>(application_id) -> <a href="./src/anchorbrowser/types/application_retrieve_response.py">ApplicationRetrieveResponse</a></code>
- <code title="get /v1/applications">client.applications.<a href="./src/anchorbrowser/resources/applications/applications.py">list</a>(\*\*<a href="src/anchorbrowser/types/application_list_params.py">params</a>) -> <a href="./src/anchorbrowser/types/application_list_response.py">ApplicationListResponse</a></code>
- <code title="delete /v1/applications/{application_id}">client.applications.<a href="./src/anchorbrowser/resources/applications/applications.py">delete</a>(application_id) -> <a href="./src/anchorbrowser/types/application_delete_response.py">ApplicationDeleteResponse</a></code>
- <code title="post /v1/applications/{application_id}/tokens">client.applications.<a href="./src/anchorbrowser/resources/applications/applications.py">create_identity_token</a>(application_id, \*\*<a href="src/anchorbrowser/types/application_create_identity_token_params.py">params</a>) -> <a href="./src/anchorbrowser/types/application_create_identity_token_response.py">ApplicationCreateIdentityTokenResponse</a></code>
- <code title="get /v1/applications/{application_id}/identities">client.applications.<a href="./src/anchorbrowser/resources/applications/applications.py">list_identities</a>(application_id, \*\*<a href="src/anchorbrowser/types/application_list_identities_params.py">params</a>) -> <a href="./src/anchorbrowser/types/application_list_identities_response.py">ApplicationListIdentitiesResponse</a></code>

## AuthFlows

Types:

```python
from anchorbrowser.types.applications import (
    AuthFlowCreateResponse,
    AuthFlowListResponse,
    AuthFlowDeleteResponse,
)
```

Methods:

- <code title="post /v1/applications/{application_id}/auth-flows">client.applications.auth_flows.<a href="./src/anchorbrowser/resources/applications/auth_flows.py">create</a>(application_id, \*\*<a href="src/anchorbrowser/types/applications/auth_flow_create_params.py">params</a>) -> <a href="./src/anchorbrowser/types/applications/auth_flow_create_response.py">AuthFlowCreateResponse</a></code>
- <code title="get /v1/applications/{application_id}/auth-flows">client.applications.auth_flows.<a href="./src/anchorbrowser/resources/applications/auth_flows.py">list</a>(application_id) -> <a href="./src/anchorbrowser/types/applications/auth_flow_list_response.py">AuthFlowListResponse</a></code>
- <code title="delete /v1/applications/{application_id}/auth-flows/{auth_flow_id}">client.applications.auth_flows.<a href="./src/anchorbrowser/resources/applications/auth_flows.py">delete</a>(auth_flow_id, \*, application_id) -> <a href="./src/anchorbrowser/types/applications/auth_flow_delete_response.py">AuthFlowDeleteResponse</a></code>
