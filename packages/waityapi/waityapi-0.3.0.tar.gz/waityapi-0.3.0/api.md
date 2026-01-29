# Shared Types

```python
from waityapi.types import ErrorResponse
```

# Health

Types:

```python
from waityapi.types import HealthCheckResponse
```

Methods:

- <code title="get /health">client.health.<a href="./src/waityapi/resources/health.py">check</a>() -> <a href="./src/waityapi/types/health_check_response.py">HealthCheckResponse</a></code>

# Partner

## Stores

Types:

```python
from waityapi.types.partner import (
    CheckInRequest,
    CheckInResponse,
    CheckOutRequest,
    CheckOutResponse,
    QueueHistory,
    QueueStatus,
    Store,
    StoreListResponse,
    UpdateQueueRequest,
    UpdateWaitTimeRequest,
    WaitTime,
    StoreUpdateQueueResponse,
)
```

Methods:

- <code title="get /stores/{id}">client.partner.stores.<a href="./src/waityapi/resources/partner/stores.py">retrieve</a>(id) -> <a href="./src/waityapi/types/partner/store.py">Store</a></code>
- <code title="get /stores">client.partner.stores.<a href="./src/waityapi/resources/partner/stores.py">list</a>() -> <a href="./src/waityapi/types/partner/store_list_response.py">StoreListResponse</a></code>
- <code title="get /stores/{id}/queue">client.partner.stores.<a href="./src/waityapi/resources/partner/stores.py">queue</a>(id) -> <a href="./src/waityapi/types/partner/queue_status.py">QueueStatus</a></code>
- <code title="post /stores/{id}/queue/check-in">client.partner.stores.<a href="./src/waityapi/resources/partner/stores.py">queue_check_in</a>(id, \*\*<a href="src/waityapi/types/partner/store_queue_check_in_params.py">params</a>) -> <a href="./src/waityapi/types/partner/check_in_response.py">CheckInResponse</a></code>
- <code title="post /stores/{id}/queue/check-out">client.partner.stores.<a href="./src/waityapi/resources/partner/stores.py">queue_check_out</a>(id, \*\*<a href="src/waityapi/types/partner/store_queue_check_out_params.py">params</a>) -> <a href="./src/waityapi/types/partner/check_out_response.py">CheckOutResponse</a></code>
- <code title="get /stores/{id}/queue/history">client.partner.stores.<a href="./src/waityapi/resources/partner/stores.py">queue_history</a>(id, \*\*<a href="src/waityapi/types/partner/store_queue_history_params.py">params</a>) -> <a href="./src/waityapi/types/partner/queue_history.py">QueueHistory</a></code>
- <code title="post /stores/{id}/queue">client.partner.stores.<a href="./src/waityapi/resources/partner/stores.py">update_queue</a>(id, \*\*<a href="src/waityapi/types/partner/store_update_queue_params.py">params</a>) -> <a href="./src/waityapi/types/partner/store_update_queue_response.py">StoreUpdateQueueResponse</a></code>
- <code title="post /stores/{id}/wait-time">client.partner.stores.<a href="./src/waityapi/resources/partner/stores.py">update_wait_time</a>(id, \*\*<a href="src/waityapi/types/partner/store_update_wait_time_params.py">params</a>) -> <a href="./src/waityapi/types/partner/wait_time.py">WaitTime</a></code>
- <code title="get /stores/{id}/wait-time">client.partner.stores.<a href="./src/waityapi/resources/partner/stores.py">wait_time</a>(id) -> <a href="./src/waityapi/types/partner/wait_time.py">WaitTime</a></code>
