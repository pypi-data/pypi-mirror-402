# Equos Python SDK
[Equos.ai](https://www.equos.ai) official Python SDK.

## Prerequisites
- Go to [Equos Studio](https://studio.equos.ai).
- Create an organization.
- Create an API Key.


## Installation
```bash
pip install equos
```

## Usage

### Setup Equos Client
```py

import os
from equos import Equos


equos_key = os.getenv("EQUOS_API_KEY", "")

const  client = Equos(api_key=equos_key)
```

You don't have an api key ? [Create one here](https://studio.equos.ai)


## Reach Us
- Equos Slack Community: [Join Equos Community Slack](https://join.slack.com/t/equosaicommunity/shared_invite/zt-3d8oy19au-jZpsJB0i~gdL0jbDswdzzQ)
- Support: [Support Form](https://docs.google.com/forms/d/e/1FAIpQLSdoK7LvORdQf7KOQKvhhlESStJcKc3bDB9HPsEet6LuOmVUfQ/viewform)

## Documentation

- Official Documentation: [https://docs.equos.ai](https://docs.equos.ai)
