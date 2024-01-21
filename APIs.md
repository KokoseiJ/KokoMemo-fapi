# Routes

## Notes

### GET `/walls`

### POST `/walls`

### PUT `/walls/<id>`

### DELETE `/walls/<id>`

### GET `/walls/<id>/memos`

### POST `/walls/<id>/memos`

### GET `/walls/<id>/memos/<id>?before=<before>&limit=<limit>`

### PUT `/walls/<id>/memos/<id>`

### DELETE `/walls/<id>/memos/<id>`


## Users

### GET `/user/login/google`

### GET `/user/login/github`

### GET `/user/logout`

### GET `/user/info`

### PUT `/user/info`

# Schemes

## Users

```json
{
    "id": "WjOZCHb9dvED",
    "email": "orangestar@mikansei.com",
    "name": "Natsu Wo Ima Mou Ikkai",
    "used_bytes": 1024,
    "logins": [
        {
            "service": "google",
            "id": "google_id_or_smn_idk"
        },
        {
            "service": "github",
            "id": "github_id_or_smn_idk"
        }
    ],
    "walls": [
        {
            "id": "w4IQNUYO5JqA",
            "name": "wall_1",
            "colour": 1048560
        }
    ]
}
```

## Memos

```json
{
    "id": "kLD4kXhTKBGP",
    "owner": "WjOZCHb9dvED",
    "wall": "w4IQNUYO5JqA",
    "created_at": "utc_time",
    "edited_at": "utc_time",
    "content": "Sekai wo nibunka shite\nBoku wa kakou ni narou"
}
```
