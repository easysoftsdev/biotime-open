Ran command: `ss -tlpn | grep -E "5432|5433|postgres"`
Ran command: `ps aux | grep -E "postgres|docker"`
Ran command: `docker ps`
Ran command: `PGPASSWORD=biotime psql -h 127.0.0.1 -p 5433 -U biotime -d biotime -c "\dt"`
Ran command: `hostname -I`

To connect Navicat to your running BioTime database, use the following connection settings:

---

### Navicat Connection Settings

1. Open **Navicat**.
2. Click **Connection** (top left) → choose **PostgreSQL**.
3. Fill in the fields under the **General** tab:

| Field | Value |
|---|---|
| **Connection Name** | `BioTime DB` *(or any name you like)* |
| **Host** | `127.0.0.1` *(if Navicat is on this machine)*<br>`192.168.150.22` *(if Navicat is on another PC on the same network)* |
| **Port** | **`5433`** *(⚠️ Note: Use `5433`, not the default `5432`)* |
| **Initial Database** | `biotime` |
| **User Name** | `biotime` |
| **Password** | `biotime` |

---

### Step-by-Step

1. In Navicat, click **Test Connection** in the bottom-left corner.
   - You should see a prompt: **"Connection Successful"**.
2. Click **OK** to save the connection.
3. Double-click the new connection in Navicat:
   - Expand `biotime` → `schemas` → `public` → `Tables`.
   - You will see all 33 domain tables (including `devices`, `employees`, `attendance_records`, `device_attendance_events`, etc.).