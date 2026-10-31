# The 40 tools

For people who want to know exactly what the AI can do: which tools only look, which ask for a tap, and what they refuse. The count of 40 is checked by a test.

**Contents:** [Looking](#looking-free-nothing-changes) · [Changing](#changing-each-makes-a-ticket-that-needs-the-owners-tap) · [Not built](#not-built) · [When a tool says no](#when-a-tool-says-no) · [Limits](#limits) · [Asking first](#asking-first)

## Looking (free, nothing changes)

 Everything that comes back is wrapped as "data, not instructions".
| Tool | What it does |
|---|---|
| `ops_status` | Version, safety switches, whether Coolify, Cloudflare and the terminal are ready, tickets waiting |
| `coolify_overview` | Apps, services and databases with id, kind and status |
| `coolify_get` | One resource, a short list of fields, secrets hidden |
| `coolify_env_list` | Environment variable NAMES and flags (apps, services, databases). Values are never shown |
| `coolify_logs` | Recent log lines of a resource, secret-looking text hidden, length capped |
| `coolify_deployments` | Recent deployments of an app, or the ones running now |
| `coolify_deployment_logs` | One deployment: status, commit and the END of its build log (where a failure shows) |
| `coolify_diagnose` | Stopped, exited or unhealthy resources with their last deployments |
| `coolify_servers` | The servers Coolify manages (name and id; addresses are never shown) |
| `coolify_registries` | Docker registries a server is logged in to (names only), and the error if it could not be read |
| `coolify_rollback_images` | Images an app could be rolled back to |
| `coolify_storages` | Volumes and file mounts: names and paths only, never file contents |
| `coolify_scheduled_tasks` | Scheduled tasks: name, timing, container, a short cleaned command |
| `coolify_backups` | Backup schedules of a database (a short field list) |
| `cloudflare_overview` | DNS records, rule sets, tunnels, Zero Trust apps |
| `cloudflare_get` | A GET on a short list of paths under the owner's own account or zone. Tokens, secrets and keys are refused |
| `cloudflare_routes` | The tunnel's routes (host name to service) |
| `server_numbers` | Disk, memory, load, Docker space, containers. A FIXED list of read-only checks over SSH |
| `terminal_list` | The terminals open on the server (only ones made through this tool) |
| `terminal_read` | What a terminal shows now. Secrets hidden over the whole captured pane |
| `ops_log` | The last actions taken or refused. No secret values, no typed text |

## Changing (each makes a ticket that needs the owner's tap)

 Every ticket shows what will happen, written by the server. "Careful" tickets are marked red.
| Tool | What it does | Extra on the ticket |
|---|---|---|
| `coolify_deploy` | Deploy an app, optionally without cache. A call that queues nothing counts as failed | |
| `coolify_control` | Start, stop or restart an app, service or database | careful for stop; start of an app says it queues a deployment |
| `coolify_cancel_deployment` | Cancel a queued or running deployment | careful |
| `coolify_env_set` | Add or change one variable (apps, services, databases). Shown in full, escaped; hidden for secret-looking names or very long values; fingerprint shown | always careful |
| `coolify_env_delete` | Delete one variable | careful |
| `coolify_setting_set` | ONE setting of an app: auto-deploy, health checks, ports, domains, compose location, base directory, git branch, image tag. Commands, Dockerfiles, labels and git addresses cannot be changed. Old and new value shown | public ports need a typed word and a warning; domains of the owner's own doors refused |
| `coolify_rollback` | Roll an app back to an earlier image (queues a deployment) | careful |
| `coolify_docker_cleanup` | Remove unused images and build leftovers. We ask Coolify to keep volumes and networks (not yet checked against the real Coolify) | careful |
| `coolify_registry_check` | Check a saved registry login (only registries the server is logged in to) | |
| `coolify_backup_run` | Run an existing volume backup now | |
| `coolify_task_run` | Run an existing scheduled task now. The whole command is shown (refused if over 500 characters) and re-checked before running | careful |
| `cloudflare_dns_set` | Create or change one DNS record (A, AAAA, CNAME, TXT) in the zone. Comment, tags and settings are kept; proxy and TTL are kept unless asked | careful when changing; protected hosts need a typed word |
| `cloudflare_dns_delete` | Delete one DNS record | typed host name |
| `cloudflare_route_set` | Add or change one route of the tunnel. Other settings of the route are kept; points only at this server, never at SSH, Coolify's own port or these two doors | typed host name; warns when no Zero Trust app covers the host and that a CNAME is needed |
| `cloudflare_route_delete` | Remove one route | typed host name |
| `terminal_open` / `terminal_close` | Open or close a terminal (tmux) on the server | careful |
| `terminal_write` | Type text (as bytes, never parsed by tmux) and/or press one key. The exact text, the line already at the prompt and warnings are shown; Enter is refused if the line changed | careful; a plain "this is a shell" note |
| `ops_result` | Check a ticket. If it was tapped meanwhile, it runs now, once | |

## Not built

And why: creating and deleting apps, services and databases (each type needs its own design), reload compose (no clear API call found),
adding or deleting volumes, previews, tags, move and clone, Cloudflare Zero Trust / WAF / R2 changes (a mistake there can lock the owner out; the dashboard is the right place),
traffic and security-event graphs (a different Cloudflare API).

## When a tool says no

A tool refuses in plain words and changes nothing. The common reasons:

| You see | Why | What to do |
|---|---|---|
| "Changes are frozen" and a Confirm link | The server starts frozen, or you pressed Freeze | Open the Confirm page and unfreeze |
| Changes are switched off | `READ_ONLY` is on | Set `READ_ONLY=0` and redeploy |
| "That is not your account or zone" | The path is outside your Cloudflare account or zone | Check the Cloudflare settings in [settings.md](settings.md) |
| "not on the list of readable paths" | `cloudflare_get` only reads a short list of path shapes | Use the Cloudflare dashboard for the rest |
| A host name is "one of this server's own doors" | Changes that could lock you out are refused | Use the Coolify or Cloudflare dashboard |
| "several changes waiting" | At most 5 tickets can be open at once | Tap or deny the open ones first |
| A text "would have to be cut" | A ticket never hides part of what it does | Ask for a smaller change |

## Limits

| What | Limit | Setting |
|---|---|---|
| Open tickets at once | 5 | fixed |
| How long a ticket stays open | 5 minutes, plus 2 minutes of grace for a tap near the end | `CONFIRM_TTL_SECONDS` |
| How long a tool waits for your tap | 45 seconds, then it hands back the ticket | `CONFIRM_WAIT_SECONDS` |
| Length of an answer | 8000 characters | `OUTPUT_MAX_CHARS` |
| Log lines returned | 200 | `MAX_LOG_LINES` |
| Requests per minute | 30 | `RATE_LIMIT_PER_MINUTE` |
| Text on a ticket | 900 characters for the summary and for the detail | fixed |
| Scheduled task commands shown in full | 500 characters, longer ones are refused | fixed |

## Asking first

Every tool in the second table makes a ticket. Nothing runs until you tap **Confirm** on your own page. Deletes and tunnel routes also need you to type a word, such as the host name. See [safety.md](safety.md) for how a ticket is built and checked.

**What next:** [Things to ask](examples.md) · [All the guides](../README.md#all-the-guides)
