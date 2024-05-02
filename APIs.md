# Routes

## Users

TODO: add routes for adding/removing integrations

### POST `/user/login/google`
Uses whatever google library returns
### GET `/user/logout`
session is kil
### DELETE `/user/session/{id}`
logout other sessions
### GET `/user/info`
gets everything in user except sessions.last_refresh, sessions.refresh_ttl, integrations.data, walls
### PUT `/user/info`
only receive name

## Memos

### GET `/walls/`
returns all walls
### POST `/walls/`
wall data without id
### PUT `/walls/`
### DELETE `/walls/{id}`
### GET `/walls/{id}/memos?after={}&limit={}`
get all memos 
### POST `/walls/{id}/memos/`
```json
{
    "name": "meow",
    "content": "meow"
}
```
### PUT `/walls/{id}/memos/`
```json
{
    "id": "meow",
    "name": "meow",
    "contents": "meow",
    "after": "id_of_another_memo"
}
```
### DELETE `/walls/{id}/memos/{id}`

# Models

## users
```json
{
    "id": "meow",
    "name": "meow",
    "email": "meow",
    "used_bytes": 102410,
    "created_at": 123123123,
    "sessions": [
        {
            "id": "meow",
            "name": "meow",
            "last_ip": "10.5.14.1",
            "created_at": 123123123,
            "last_refresh": 123123123,
            "refresh_ttl": 38400
        }
    ],
    "integrations": [
        {
            "service": "google",
            "data": {
                "id": "whatever google gave me"
            }
        }
    ],
    "walls": [
        {
            "id": "meow",
            "name": "meow",
            "colour": 1681354,
            "created_at": 123123123,
            "modified_at": 123123123
        }
    ]
}
```

## Memos
```json
{
    "id": "meow",
    "wall_id": "meow",
    "contents": "meow",
    "index": 1.0,
    "created_at": 123123123,
    "modified_at": 123123123
}
```
