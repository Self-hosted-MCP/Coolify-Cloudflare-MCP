# Undo and backups

For when you want to know how to take a change back. This tool changes real things, and it has no undo button. You leave knowing what is easy to reverse, what is not, and what to back up.

**Contents:** [The record of changes](#the-record-of-changes) · [At a glance](#at-a-glance) · [What can't be undone](#what-cant-be-undone) · [Backing up](#backing-up)

## The record of changes

Two logs tell you what happened:

- The **action log** of this tool: `ops_log`, or `actions.log` in the data folder. It lists what was asked, tapped, run or refused. It has no secret values.
- **Cloudflare's audit log**, which shows who changed what on the Cloudflare side.

Coolify also keeps its deployment history.

## At a glance

| Change | How to take it back |
|---|---|
| Deploy | Roll back to the earlier image with `coolify_rollback` (a ticket), or in Coolify |
| Restart, stop, start | Do the opposite |
| Environment variable added or changed | Set the old value again. A ticket shows the new value, and the name tells you what changed |
| Setting changed | The ticket shows the old and the new value. Set the old one again |
| DNS record created | Delete it (you type the host name) |
| DNS record changed | The ticket shows the old and new value. Change it back |
| DNS record deleted | Create it again from the old value in the action log or Cloudflare's audit log |
| Tunnel route added or changed | Remove or change it again. Other settings of the route are kept |
| Tunnel route removed | Add it again |
| Docker cleanup | Images come back when Coolify rebuilds or pulls them |
| Backup or scheduled task run | Depends on the task |
| Terminal text typed | Depends on what ran |

## What can't be undone

- **Environment variable deleted:** the value is not shown anywhere, so keep your own copy.
- **Terminal commands** that delete files or change the system.
- **A task you ran** that deleted data in its container.
- Anything done while **Allow all** was on that you did not read.

## Backing up

- Coolify can back up its own database daily to S3-compatible storage. Switch that on.
- Back up your databases and volumes with Coolify's backup schedules. `coolify_backup_run` runs one now (a ticket).
- This tool's own `data` volume holds only login records and the action log. It is nice to keep, not vital.
- Keep your tokens and your passphrase in a password manager, not only in Coolify.

**What next:** [Safety](safety.md) · [All the guides](../README.md#all-the-guides)
