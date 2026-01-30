# Troubleshooting Guide

## 1. Connection Refused (MongoDB)

**Error:** `pymongo.errors.ServerSelectionTimeoutError: localhost:27017: [Errno 111] Connection refused`

**Solution:**
1. Ensure MongoDB is installed and running.
   ```bash
   systemctl status mongod
   # OR
   docker ps | grep mongo
   ```
2. If using Docker, ensure path port mapping is correct (`-p 27017:27017`).
3. Check `MONGO_URI` in `.env`.

## 2. Notification Failed

**Error:** `[ERROR] Failed to send notification: [Errno 2] No such file or directory: 'notify-send'`

**Solution:**
1. You are likely on a system without `libnotify-bin` (e.g., barebone container, server, or MacOS).
2. **Linux (Debian/Ubuntu):** Install `libnotify-bin`.
   ```bash
   sudo apt-get install libnotify-bin
   ```
3. **MacOS:** `notify-send` is not native. The bridge currently supports Linux notifications optimally.

## 3. Path Permission Error

**Error:** `PermissionError: Access denied: /path/to/file is not within any registered project.`

**Solution:**
1. The `PathValidator` blocks access to files outside registered project roots.
2. Register the project that contains the file first using `register_project`.
3. Ensure you are using absolute paths.

## 4. Watchdog Not Triggering

**Issue:** Changes in files are not monitored.

**Solution:**
1. Check if the project is registered with `role="producer"`.
2. Check `watch_patterns`. Default is often `["openapi.json", "**/*.md"]`. If you changed a `.txt` file, it might be ignored.
3. Check logs for "Watcher started" messages.
4. **Linux Limits:** You might have hit the `inotify` watch limit.
   ```bash
   echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p
   ```

## 5. Systemd Service Not Starting

**Error:** `code=exited, status=203/EXEC`

**Solution:**
1. Check the paths in `jtech-bridge-mcp.service`.
2. Ensure `uv` path is correct.
3. Check logs: `journalctl --user -u jtech-bridge-mcp -f`.
