# Usage Scenarios

Real-world examples of how Hestia can be used as a self-hosted home platform.

---

## Scenario 1: Digitize a Filing Cabinet

**Who**: A family scanning years of paper documents.

**Workflow**:
1. Scan all documents to PDF using a flatbed scanner
2. Upload the scanned PDFs via the dashboard (drag-and-drop)
3. Create a batch pipeline: **OCR → Compress → Store**
4. Hestia runs OCR on every page, making them searchable
5. Compresses the files to save disk space
6. Stores the results on a Samba share accessible from any device

**API calls**:
```bash
# Upload scanned files
curl -X POST https://localhost/api/v1/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@tax_2023.pdf" \
  -F "files=@insurance.pdf"

# Create a pipeline: OCR then compress
curl -X POST https://localhost/api/v1/pipelines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "digitize",
    "steps": [
      {"operation": "pdf_ocr", "parameters": {}},
      {"operation": "pdf_compress", "parameters": {}}
    ],
    "file_ids": ["file-0", "file-1"]
  }'

# Check job progress
curl https://localhost/api/v1/jobs/JOB_ID \
  -H "Authorization: Bearer $TOKEN"
```

**Result**: Searchable, compressed PDFs available on every device in the house via SMB share.

---

## Scenario 2: Home Security Camera Archive

**Who**: Someone running IP cameras that dump footage to a local folder.

**Workflow**:
1. Cameras save `.avi` files to a watched directory
2. An IoT automation triggers on a cron schedule (every hour)
3. The automation submits a transcoding job: **AVI → MP4** (smaller, web-playable)
4. Compressed footage is stored on a ZFS dataset with snapshots for integrity

**Automation setup**:
```bash
# Create a cron-triggered automation
curl -X POST https://localhost/api/v1/iot/automations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "transcode-cameras",
    "trigger_type": "cron",
    "cron_expression": "0 * * * *",
    "actions": [
      {
        "type": "file_process",
        "parameters": {
          "operation": "video_transcode",
          "source_format": "avi",
          "target_format": "mp4",
          "bitrate": "2M"
        }
      }
    ]
  }'
```

**Result**: Camera footage is automatically compressed hourly, saving 60-70% disk space, with ZFS snapshots protecting against accidental deletion.

---

## Scenario 3: Family Photo Conversion for Printing

**Who**: A parent preparing photos for a print service that only accepts JPEG.

**Workflow**:
1. Upload PNG photos from a phone via the dashboard
2. Select "Convert to JPEG" operation
3. Download the converted files
4. The download link stays valid for 24 hours

**API calls**:
```bash
# Upload PNGs
curl -X POST https://localhost/api/v1/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@photo1.png" \
  -F "files=@photo2.png"

# Convert to JPEG
curl -X POST https://localhost/api/v1/files/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "convert",
    "source_format": "png",
    "target_format": "jpeg",
    "file_ids": ["file-0", "file-1"]
  }'

# Download when done
curl -O https://localhost/api/v1/files/FILE_ID/download \
  -H "Authorization: Bearer $TOKEN"
```

**Result**: JPEGs with original dimensions preserved, ready for the print service.

---

## Scenario 4: Smart Home + File Processing

**Who**: A hobbyist with temperature sensors and a Home Assistant setup.

**Workflow**:
1. Temperature sensors publish readings to MQTT topic `home/+/temperature`
2. An automation watches for readings above 35°C
3. When triggered, it logs the event and sends a notification
4. A separate cron automation generates a daily PDF report from sensor data

**MQTT automation**:
```bash
# Alert on high temperature
curl -X POST https://localhost/api/v1/iot/automations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "heat-alert",
    "trigger_type": "mqtt",
    "mqtt_topic": "home/+/temperature",
    "actions": [
      {
        "type": "notification",
        "parameters": {"message": "High temperature detected!"}
      }
    ]
  }'
```

**Result**: Automated monitoring with full execution logs (timestamp, trigger, actions, status) for every event.

---

## Scenario 5: Remote Access While Traveling

**Who**: Someone who wants to access their home files and services from a hotel.

**Setup**:
1. WireGuard VPN is configured on the Hestia machine (port 51820)
2. Install WireGuard client on laptop/phone
3. Import the client config with the server's public key
4. Connect — all Hestia services are accessible as if on the home network

**Client config** (`wg-client.conf`):
```ini
[Interface]
PrivateKey = <CLIENT_PRIVATE_KEY>
Address = 10.100.0.2/24

[Peer]
PublicKey = <SERVER_PUBLIC_KEY>
PresharedKey = <PRESHARED_KEY>
Endpoint = your-home-ip:51820
AllowedIPs = 10.100.0.0/24
```

**Security**: VPN clients can only reach Hestia services — no lateral access to other devices on the home network.

---

## Scenario 6: Merge and Compress Monthly Invoices

**Who**: A freelancer collecting invoices from multiple clients.

**Workflow**:
1. Upload 15 invoice PDFs via drag-and-drop
2. Create a pipeline: **Merge → Compress**
3. Get a single compressed PDF with all invoices

```bash
# Upload all invoices
curl -X POST https://localhost/api/v1/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@inv_01.pdf" \
  -F "files=@inv_02.pdf" \
  -F "files=@inv_03.pdf"
  # ... more files

# Merge then compress
curl -X POST https://localhost/api/v1/pipelines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "monthly-invoices",
    "steps": [
      {"operation": "pdf_merge", "parameters": {}},
      {"operation": "pdf_compress", "parameters": {}}
    ],
    "file_ids": ["file-0", "file-1", "file-2"]
  }'
```

**Result**: One compact PDF. The pipeline definition is saved as "monthly-invoices" and can be reused next month.

---

## Scenario 7: Multi-User Family NAS

**Who**: A family of four sharing a home server.

**Setup**:
1. Admin creates user accounts with appropriate roles
2. Each family member gets their own Samba share
3. A shared "Family Photos" share is accessible to everyone
4. Kids have `user` role (no admin panel access)
5. Parents have `admin` role

**Share configuration**:
```bash
# Create a private share for one user
curl -X POST https://localhost/api/v1/storage/shares \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "alex-documents",
    "path": "/srv/storage/alex",
    "protocols": ["smb"],
    "allowed_users": ["alex"],
    "read_only": false
  }'

# Create a shared family folder
curl -X POST https://localhost/api/v1/storage/shares \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "family-photos",
    "path": "/srv/storage/family-photos",
    "protocols": ["smb"],
    "allowed_users": ["alex", "sam", "pat", "chris"],
    "read_only": false
  }'
```

**Access**: Mount `\\hestia\alex-documents` on Windows or `smb://hestia/family-photos` on macOS. Each user authenticates with their Hestia credentials (SSO via Authelia).

---

## Scenario 8: Audio Podcast Post-Processing

**Who**: A hobbyist podcaster recording in FLAC.

**Workflow**:
1. Upload raw FLAC recording
2. Transcode to MP3 at 192kbps for distribution
3. Also transcode to OGG for the website player

```bash
# Upload FLAC
curl -X POST https://localhost/api/v1/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@episode42.flac"

# Convert to MP3
curl -X POST https://localhost/api/v1/files/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "audio_transcode",
    "source_format": "flac",
    "target_format": "mp3",
    "parameters": {"bitrate": "192k"},
    "file_ids": ["file-0"]
  }'

# Convert to OGG
curl -X POST https://localhost/api/v1/files/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "audio_transcode",
    "source_format": "flac",
    "target_format": "ogg",
    "parameters": {"bitrate": "128k"},
    "file_ids": ["file-0"]
  }'
```

**Result**: Both jobs run in parallel on separate workers. Progress is visible in the dashboard in real-time.

---

## Scenario 9: Home Media Library with Playback

**Who**: A family with a collection of movies, TV shows, and home videos scattered across hard drives.

**Problem**: Files are in different formats (MKV, AVI, WebM), some devices can't play certain codecs, and there's no central place to browse and watch everything.

**Setup**:

1. Create a dedicated media share on ZFS (checksumming protects against bit rot):

```bash
# Create a ZFS-backed media share
curl -X POST https://localhost/api/v1/storage/shares \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "media",
    "path": "/srv/storage/media",
    "protocols": ["smb", "nfs"],
    "allowed_users": ["alex", "sam", "pat", "chris"],
    "read_only": false
  }'
```

2. Organize the share into folders:

```
/srv/storage/media/
├── movies/
├── tv-shows/
├── home-videos/
└── music/
```

3. Copy existing media files to the share from any device:
   - **Windows**: Map `\\hestia\media` as a network drive, drag and drop
   - **macOS**: Connect to `smb://hestia/media` in Finder
   - **Linux**: Mount via NFS or SMB, or use `rsync`

**Transcoding for compatibility**:

Some devices (smart TVs, tablets) can't play MKV or AVI. Use Hestia to batch-convert:

```bash
# Upload an MKV file
curl -X POST https://localhost/api/v1/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@movie.mkv"

# Transcode to MP4 (universally playable)
curl -X POST https://localhost/api/v1/files/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "video_transcode",
    "source_format": "mkv",
    "target_format": "mp4",
    "parameters": {"resolution": "1920x1080", "bitrate": "5M"},
    "file_ids": ["file-0"]
  }'
```

Or automate it — transcode everything in a folder on a schedule:

```bash
# Nightly automation: convert any new MKV/AVI to MP4
curl -X POST https://localhost/api/v1/iot/automations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "nightly-transcode",
    "trigger_type": "cron",
    "cron_expression": "0 2 * * *",
    "actions": [
      {
        "type": "file_process",
        "parameters": {
          "operation": "video_transcode",
          "source_format": "mkv",
          "target_format": "mp4",
          "bitrate": "5M"
        }
      }
    ]
  }'
```

**Playback options**:

Since the media share is accessible over SMB/NFS, any media player on the network can stream directly:

| Device | How to watch |
|---|---|
| **Smart TV** | Browse `\\hestia\media` via built-in SMB client, or use VLC/Kodi |
| **Laptop/Desktop** | Open `smb://hestia/media/movies/` in VLC, mpv, or any player |
| **Tablet/Phone** | Use VLC for Android/iOS, point to SMB share |
| **Kodi** | Add `smb://hestia/media/` as a media source — Kodi scrapes metadata, artwork, and subtitles automatically |
| **Plex/Jellyfin** | Point the media library at `/srv/storage/media/` — runs alongside Hestia on the same machine |
| **Nextcloud** | If enabled, stream via browser at `https://hestia/nextcloud` — no app needed |

**Recommended setup with Kodi or Jellyfin**:

Hestia handles the storage, access control, transcoding, and automation. For a full media browsing/playback UI with posters, metadata, and subtitle support, pair it with:

- **Jellyfin** (self-hosted, free) — runs on the same machine, reads from the Samba share, provides a Netflix-like web UI
- **Kodi** — runs on each client device (TV, laptop), connects to the Samba share directly

Example: Jellyfin running alongside Hestia:
```
Browser → https://hestia:8096 → Jellyfin UI → reads /srv/storage/media/ → plays video
Browser → https://hestia         → Hestia dashboard → upload, transcode, manage shares
```

**ZFS snapshots for protection**:

```bash
# Snapshot the media library before a big reorganization
curl -X POST https://localhost/api/v1/storage/snapshots \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dataset": "pool/media"}'

# Accidentally deleted a folder? Restore the snapshot
curl -X POST https://localhost/api/v1/storage/snapshots/SNAP_ID/restore \
  -H "Authorization: Bearer $TOKEN"
```

**Result**: A centralized media library accessible from every device in the house, with automatic format conversion, bit-rot protection via ZFS, and the option to add Jellyfin/Kodi for a full playback experience.
