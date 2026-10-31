# Function-by-function check

Made by `scripts/verify_functions.py`. 288 functions, 288 fully run by the tests, 0 with lines the tests never reach.

| File | Line | Function | Lines run | Missing lines | Tests that name it |
|---|---|---|---|---|---|
| access.py | 21 | `enforcing` | 1/1 | - | config |
| access.py | 25 | `team` | 1/1 | - | confirm_app, misc |
| access.py | 29 | `aud` | 1/1 | - | confirm_app, misc, server_more |
| access.py | 33 | `configured` | 1/1 | - | cloudflare_more, server, terminal |
| access.py | 37 | `_keys` | 3/3 | - | confirm_app, misc |
| access.py | 44 | `verify` | 10/10 | - | (only through other tests) |
| access.py | 61 | `who` | 8/8 | - | config, misc |
| audit.py | 16 | `log_file` | 1/1 | - | consent, misc |
| audit.py | 20 | `log` | 13/13 | - | consent, misc, new_tools, round3 |
| audit.py | 37 | `recent` | 13/13 | - | cloudflare_changes, consent, misc, round3 |
| auth.py | 25 | `oauth_file` | 1/1 | - | auth |
| auth.py | 29 | `private_write` | 9/9 | - | auth, edges |
| auth.py | 42 | `hash_passphrase` | 3/3 | - | auth, confirm_more, server_more |
| auth.py | 48 | `check_passphrase` | 5/5 | - | auth, server_more |
| auth.py | 57 | `passphrase_ok` | 6/6 | - | auth |
| auth.py | 67 | `token_key` | 1/1 | - | auth |
| auth.py | 78 | `__init__` | 14/14 | - | cloudflare_changes, confirm_more, terminal |
| auth.py | 94 | `save` | 4/4 | - | (only through other tests) |
| auth.py | 105 | `redirect_ok` | 8/8 | - | auth |
| auth.py | 115 | `get_client` | 1/1 | - | auth |
| auth.py | 118 | `register_client` | 15/15 | - | auth, edges, server_more |
| auth.py | 136 | `logged_in` | 1/1 | - | auth, new_tools, round3 |
| auth.py | 140 | `authorize` | 11/11 | - | auth, edges, server, server_more |
| auth.py | 153 | `describe` | 5/5 | - | auth |
| auth.py | 160 | `locked_out` | 7/7 | - | (only through other tests) |
| auth.py | 169 | `pairing_open` | 1/1 | - | auth, confirm_more |
| auth.py | 172 | `open_pairing` | 2/2 | - | auth, server_more |
| auth.py | 176 | `complete_login` | 24/24 | - | auth |
| auth.py | 210 | `load_authorization_code` | 4/4 | - | auth |
| auth.py | 216 | `issue` | 7/7 | - | (only through other tests) |
| auth.py | 228 | `exchange_authorization_code` | 4/4 | - | auth |
| auth.py | 234 | `load_refresh_token` | 4/4 | - | auth |
| auth.py | 240 | `exchange_refresh_token` | 4/4 | - | auth |
| auth.py | 246 | `load_access_token` | 4/4 | - | auth |
| auth.py | 252 | `for_us` | 4/4 | - | auth |
| auth.py | 258 | `revoke_token` | 1/1 | - | auth |
| auth.py | 261 | `apps` | 9/9 | - | auth, cloudflare, confirm_more, round3 |
| auth.py | 275 | `disconnect` | 7/7 | - | auth, confirm_more |
| auth.py | 296 | `login_page` | 7/7 | - | auth |
| cloudflare.py | 37 | `configured` | 1/1 | - | cloudflare_more, server, terminal |
| cloudflare.py | 41 | `check_path` | 13/13 | - | cloudflare |
| cloudflare.py | 57 | `get` | 29/29 | - | cloudflare, cloudflare_changes, cloudflare_more, confirm_app |
| cloudflare.py | 95 | `_rows` | 5/5 | - | (only through other tests) |
| cloudflare.py | 103 | `_line` | 1/1 | - | (only through other tests) |
| cloudflare.py | 107 | `overview` | 16/16 | - | cloudflare, cloudflare_more, coolify, coolify_more |
| cloudflare.py | 112 | `section` | 6/6 | - | (only through other tests) |
| cloudflare.py | 130 | `get_text` | 1/1 | - | cloudflare_more |
| cloudflare.py | 154 | `edit_configured` | 1/1 | - | (only through other tests) |
| cloudflare.py | 158 | `tunnel_configured` | 1/1 | - | (only through other tests) |
| cloudflare.py | 162 | `check_hostname` | 7/7 | - | cloudflare_changes, gaps2 |
| cloudflare.py | 173 | `is_protected` | 1/1 | - | round3 |
| cloudflare.py | 177 | `check_dns` | 27/27 | - | cloudflare_changes |
| cloudflare.py | 210 | `send` | 22/22 | - | cloudflare_changes, terminal |
| cloudflare.py | 241 | `dns_find` | 5/5 | - | gaps2 |
| cloudflare.py | 249 | `_pick_dns` | 1/1 | - | gaps2 |
| cloudflare.py | 254 | `digest` | 1/1 | - | gaps2, round3 |
| cloudflare.py | 258 | `dns_set` | 10/10 | - | (only through other tests) |
| cloudflare.py | 272 | `dns_delete` | 8/8 | - | gaps2 |
| cloudflare.py | 284 | `check_service` | 11/11 | - | cloudflare_changes, round3 |
| cloudflare.py | 300 | `tunnel_config` | 6/6 | - | gaps2 |
| cloudflare.py | 309 | `split_ingress` | 4/4 | - | (only through other tests) |
| cloudflare.py | 317 | `describe_routes` | 1/1 | - | (only through other tests) |
| cloudflare.py | 321 | `find_route` | 6/6 | - | (only through other tests) |
| cloudflare.py | 331 | `shadowed_by` | 1/1 | - | (only through other tests) |
| cloudflare.py | 336 | `route_origin` | 6/6 | - | (only through other tests) |
| cloudflare.py | 346 | `access_covers` | 13/13 | - | round3 |
| cloudflare.py | 366 | `route_set` | 17/17 | - | round3 |
| cloudflare.py | 387 | `route_delete` | 10/10 | - | gaps2 |
| config.py | 7 | `env` | 1/1 | - | new_tools |
| config.py | 11 | `env_int` | 3/3 | - | misc |
| config.py | 18 | `env_list` | 1/1 | - | (only through other tests) |
| config.py | 25 | `flag` | 1/1 | - | misc |
| config.py | 29 | `safe_flag` | 4/4 | - | (only through other tests) |
| config.py | 38 | `data_dir` | 1/1 | - | (only through other tests) |
| config.py | 42 | `public_url` | 1/1 | - | misc |
| config.py | 46 | `confirm_url` | 1/1 | - | misc |
| config.py | 50 | `redirect_hosts` | 1/1 | - | misc |
| config.py | 54 | `coolify_url` | 1/1 | - | misc |
| config.py | 58 | `coolify_token` | 1/1 | - | (only through other tests) |
| config.py | 62 | `cf_account` | 1/1 | - | misc |
| config.py | 66 | `cf_zone` | 1/1 | - | misc |
| config.py | 70 | `cf_read_token` | 1/1 | - | misc |
| config.py | 74 | `cf_edit_token` | 1/1 | - | (only through other tests) |
| config.py | 78 | `cf_zone_name` | 1/1 | - | (only through other tests) |
| config.py | 82 | `cf_tunnel_id` | 1/1 | - | (only through other tests) |
| config.py | 86 | `_host_of` | 2/2 | - | (only through other tests) |
| config.py | 91 | `protected_hostnames` | 3/3 | - | round3 |
| config.py | 98 | `route_hard_blocked_ports` | 1/1 | - | (only through other tests) |
| config.py | 103 | `route_blocked_ports` | 2/2 | - | (only through other tests) |
| config.py | 109 | `route_allowed_ports` | 1/1 | - | (only through other tests) |
| config.py | 114 | `read_only` | 1/1 | - | config |
| config.py | 118 | `enforcing` | 1/1 | - | config |
| config.py | 122 | `confirm_wait` | 1/1 | - | misc |
| config.py | 126 | `confirm_ttl` | 1/1 | - | misc |
| config.py | 130 | `output_max_chars` | 1/1 | - | misc |
| config.py | 134 | `max_log_lines` | 1/1 | - | misc |
| config.py | 138 | `rate_limit_per_minute` | 1/1 | - | misc |
| config.py | 142 | `http_timeout` | 1/1 | - | misc |
| config.py | 146 | `action_log_max_mb` | 1/1 | - | (only through other tests) |
| config.py | 150 | `host` | 1/1 | - | confirm_more, misc, round3, server_more |
| config.py | 154 | `port` | 1/1 | - | misc, new_tools, round3 |
| config.py | 158 | `admin_port` | 1/1 | - | misc |
| config.py | 162 | `allowed_emails` | 1/1 | - | (only through other tests) |
| config.py | 167 | `ssh_host` | 1/1 | - | (only through other tests) |
| config.py | 171 | `ssh_port` | 1/1 | - | (only through other tests) |
| config.py | 175 | `ssh_user` | 1/1 | - | (only through other tests) |
| config.py | 179 | `ssh_key` | 1/1 | - | safety |
| config.py | 183 | `ssh_known_hosts` | 1/1 | - | (only through other tests) |
| confirm_app.py | 39 | `e` | 1/1 | - | coolify, new_tools |
| confirm_app.py | 43 | `left` | 2/2 | - | round3, terminal |
| confirm_app.py | 48 | `page` | 16/16 | - | auth, confirm_app, confirm_more, gaps2 |
| confirm_app.py | 84 | `dispatch` | 22/22 | - | (only through other tests) |
| confirm_app.py | 109 | `home` | 1/1 | - | (only through other tests) |
| confirm_app.py | 113 | `ticket_page` | 8/8 | - | (only through other tests) |
| confirm_app.py | 133 | `ticket_view` | 1/1 | - | (only through other tests) |
| confirm_app.py | 137 | `decide` | 12/12 | - | cloudflare_changes, confirm_app, consent, edges |
| confirm_app.py | 155 | `approve` | 1/1 | - | cloudflare_changes, confirm_app, gaps2, round3 |
| confirm_app.py | 159 | `deny` | 1/1 | - | confirm_app, gaps2 |
| confirm_app.py | 163 | `freeze` | 10/10 | - | confirm_app, confirm_more, edges, round3 |
| confirm_app.py | 177 | `pairing` | 6/6 | - | auth, confirm_more, server_more |
| confirm_app.py | 186 | `disconnect` | 7/7 | - | auth, confirm_more |
| confirm_app.py | 196 | `app` | 1/1 | - | cloudflare_changes, confirm_app, confirm_more, edges |
| confirm_app.py | 210 | `start` | 4/4 | - | confirm_more, coolify_more, server_more |
| consent.py | 63 | `frozen_file` | 1/1 | - | (only through other tests) |
| consent.py | 70 | `frozen` | 1/1 | - | confirm_app, consent, edges, misc |
| consent.py | 74 | `set_frozen` | 8/8 | - | consent, misc, round3, server |
| consent.py | 91 | `_key` | 2/2 | - | (only through other tests) |
| consent.py | 96 | `csrf` | 1/1 | - | confirm_app, confirm_more, consent, edges |
| consent.py | 101 | `csrf_ok` | 1/1 | - | consent |
| consent.py | 105 | `payload_digest` | 1/1 | - | (only through other tests) |
| consent.py | 110 | `__init__` | 3/3 | - | cloudflare_changes, confirm_more, terminal |
| consent.py | 115 | `_sweep` | 8/8 | - | (only through other tests) |
| consent.py | 125 | `create` | 19/19 | - | confirm_app, consent, edges, gaps2 |
| consent.py | 149 | `get` | 3/3 | - | cloudflare, cloudflare_changes, cloudflare_more, confirm_app |
| consent.py | 154 | `cancel_all` | 10/10 | - | consent |
| consent.py | 167 | `open_tickets` | 3/3 | - | cloudflare_changes, confirm_app, edges, new_tools |
| consent.py | 172 | `decide` | 16/16 | - | cloudflare_changes, confirm_app, consent, edges |
| consent.py | 192 | `run_if_approved` | 41/41 | - | consent, edges, misc, round3 |
| consent.py | 238 | `wait_and_run` | 8/8 | - | consent |
| coolify.py | 30 | `configured` | 1/1 | - | cloudflare_more, server, terminal |
| coolify.py | 34 | `call` | 29/29 | - | terminal |
| coolify.py | 72 | `pick` | 1/1 | - | (only through other tests) |
| coolify.py | 76 | `short` | 4/4 | - | cloudflare |
| coolify.py | 83 | `version` | 1/1 | - | coolify_more, new_tools, server, server_more |
| coolify.py | 87 | `overview` | 8/8 | - | cloudflare, cloudflare_more, coolify, coolify_more |
| coolify.py | 99 | `get` | 1/1 | - | cloudflare, cloudflare_changes, cloudflare_more, confirm_app |
| coolify.py | 103 | `env_keys` | 2/2 | - | coolify |
| coolify.py | 108 | `logs` | 4/4 | - | coolify, coolify_more, new_tools, safety |
| coolify.py | 115 | `deployments` | 4/4 | - | coolify_more, edges, new_tools, server |
| coolify.py | 123 | `diagnose` | 14/14 | - | coolify_more, edges |
| coolify.py | 143 | `deploy` | 7/7 | - | edges, server |
| coolify.py | 153 | `control` | 5/5 | - | confirm_app, coolify, coolify_more, round3 |
| coolify.py | 161 | `cancel` | 2/2 | - | coolify_more, edges, server_more |
| coolify.py | 166 | `_env_uuid` | 5/5 | - | (only through other tests) |
| coolify.py | 174 | `env_set` | 10/10 | - | coolify, round3 |
| coolify.py | 187 | `env_delete` | 6/6 | - | coolify_more |
| coolify.py | 197 | `_log_lines` | 14/14 | - | gaps2 |
| coolify.py | 217 | `deployment` | 8/8 | - | coolify_more, new_tools, round3, server |
| coolify.py | 233 | `servers` | 2/2 | - | coolify, new_tools, round3 |
| coolify.py | 238 | `registries` | 6/6 | - | new_tools, round3 |
| coolify.py | 247 | `registry_check` | 4/4 | - | new_tools |
| coolify.py | 254 | `docker_cleanup` | 2/2 | - | new_tools |
| coolify.py | 264 | `rollback_images` | 3/3 | - | new_tools |
| coolify.py | 271 | `rollback` | 7/7 | - | new_tools |
| coolify.py | 282 | `_bool` | 7/7 | - | (only through other tests) |
| coolify.py | 292 | `_int` | 10/10 | - | (only through other tests) |
| coolify.py | 293 | `check` | 8/8 | - | new_tools, round3, terminal |
| coolify.py | 306 | `_pattern` | 7/7 | - | (only through other tests) |
| coolify.py | 309 | `check` | 4/4 | - | new_tools, round3, terminal |
| coolify.py | 317 | `_ports` | 9/9 | - | (only through other tests) |
| coolify.py | 320 | `check` | 6/6 | - | new_tools, round3, terminal |
| coolify.py | 352 | `check_setting` | 3/3 | - | new_tools, round3 |
| coolify.py | 358 | `current_setting` | 4/4 | - | new_tools |
| coolify.py | 366 | `exposure` | 8/8 | - | (only through other tests) |
| coolify.py | 379 | `set_setting` | 3/3 | - | new_tools, round3 |
| coolify.py | 386 | `storages` | 6/6 | - | new_tools, terminal |
| coolify.py | 396 | `scheduled_tasks` | 11/11 | - | new_tools |
| coolify.py | 414 | `backups` | 3/3 | - | cloudflare_more, new_tools, round3, terminal |
| coolify.py | 421 | `backup_run` | 2/2 | - | (only through other tests) |
| coolify.py | 427 | `task_run` | 6/6 | - | terminal |
| coolify.py | 438 | `task_digest` | 1/1 | - | round3 |
| coolify.py | 442 | `task_raw` | 7/7 | - | round3 |
| safety.py | 40 | `kind_of` | 8/8 | - | coolify_more |
| safety.py | 52 | `valid_id` | 3/3 | - | safety |
| safety.py | 58 | `valid_kind` | 3/3 | - | coolify_more, safety |
| safety.py | 64 | `valid_env_key` | 3/3 | - | safety |
| safety.py | 70 | `is_risky_name` | 1/1 | - | safety |
| safety.py | 75 | `is_secret_name` | 1/1 | - | (only through other tests) |
| safety.py | 79 | `strip_control` | 1/1 | - | safety |
| safety.py | 83 | `clean_label` | 3/3 | - | safety |
| safety.py | 90 | `redact_text` | 4/4 | - | safety |
| safety.py | 97 | `mask_obj` | 13/13 | - | safety |
| safety.py | 116 | `cap` | 4/4 | - | safety |
| safety.py | 123 | `untrusted` | 2/2 | - | round3, safety |
| safety.py | 129 | `as_json` | 1/1 | - | misc |
| server.py | 44 | `build_server` | 21/21 | - | (only through other tests) |
| server.py | 60 | `login` | 15/15 | - | auth, coolify, coolify_more, new_tools |
| server.py | 79 | `health_route` | 1/1 | - | (only through other tests) |
| server.py | 90 | `tool` | 13/13 | - | cloudflare_changes, consent, new_tools, round3 |
| server.py | 92 | `deco` | 11/11 | - | (only through other tests) |
| server.py | 94 | `wrapper` | 9/9 | - | (only through other tests) |
| server.py | 115 | `label` | 5/5 | - | (only through other tests) |
| server.py | 124 | `change` | 2/2 | - | (only through other tests) |
| server.py | 132 | `ops_status` | 12/12 | - | cloudflare_changes, server, server_more, terminal |
| server.py | 152 | `coolify_overview` | 1/1 | - | edges, server, server_more |
| server.py | 158 | `coolify_get` | 1/1 | - | server |
| server.py | 164 | `coolify_env_list` | 1/1 | - | new_tools, server_more |
| server.py | 170 | `coolify_deployment_logs` | 1/1 | - | new_tools |
| server.py | 177 | `coolify_servers` | 1/1 | - | new_tools |
| server.py | 183 | `coolify_registries` | 1/1 | - | new_tools |
| server.py | 189 | `coolify_rollback_images` | 1/1 | - | new_tools |
| server.py | 195 | `coolify_storages` | 1/1 | - | new_tools |
| server.py | 201 | `coolify_scheduled_tasks` | 1/1 | - | new_tools |
| server.py | 207 | `coolify_backups` | 1/1 | - | new_tools |
| server.py | 213 | `coolify_logs` | 1/1 | - | server |
| server.py | 219 | `coolify_deployments` | 1/1 | - | server_more |
| server.py | 226 | `coolify_diagnose` | 1/1 | - | server_more |
| server.py | 232 | `cloudflare_overview` | 1/1 | - | server, server_more |
| server.py | 238 | `cloudflare_get` | 1/1 | - | server |
| server.py | 245 | `ops_log` | 1/1 | - | round3, server, server_more |
| server.py | 252 | `run_deploy` | 1/1 | - | (only through other tests) |
| server.py | 256 | `run_control` | 1/1 | - | (only through other tests) |
| server.py | 260 | `run_cancel` | 1/1 | - | (only through other tests) |
| server.py | 264 | `run_env_set` | 3/3 | - | edges |
| server.py | 270 | `run_env_delete` | 1/1 | - | (only through other tests) |
| server.py | 274 | `run_setting` | 1/1 | - | (only through other tests) |
| server.py | 278 | `run_rollback` | 1/1 | - | (only through other tests) |
| server.py | 282 | `run_cleanup` | 1/1 | - | (only through other tests) |
| server.py | 286 | `run_backup` | 1/1 | - | (only through other tests) |
| server.py | 290 | `run_task` | 1/1 | - | (only through other tests) |
| server.py | 294 | `run_registry_check` | 1/1 | - | (only through other tests) |
| server.py | 299 | `coolify_deploy` | 3/3 | - | edges, server |
| server.py | 308 | `coolify_control` | 6/6 | - | server, server_more |
| server.py | 320 | `coolify_cancel_deployment` | 2/2 | - | server, server_more |
| server.py | 328 | `coolify_env_set` | 10/10 | - | edges, new_tools, round3, server |
| server.py | 348 | `coolify_env_delete` | 3/3 | - | new_tools, server, server_more |
| server.py | 357 | `coolify_setting_set` | 7/7 | - | new_tools, round3 |
| server.py | 373 | `coolify_rollback` | 5/5 | - | new_tools |
| server.py | 384 | `coolify_docker_cleanup` | 2/2 | - | new_tools |
| server.py | 392 | `coolify_registry_check` | 7/7 | - | new_tools, round3 |
| server.py | 406 | `coolify_backup_run` | 3/3 | - | terminal |
| server.py | 415 | `coolify_task_run` | 11/11 | - | round3, terminal |
| server.py | 437 | `need_cloudflare_edit` | 4/4 | - | (only through other tests) |
| server.py | 444 | `run_dns_set` | 1/1 | - | (only through other tests) |
| server.py | 448 | `run_dns_delete` | 1/1 | - | (only through other tests) |
| server.py | 452 | `run_route_set` | 1/1 | - | (only through other tests) |
| server.py | 456 | `run_route_delete` | 1/1 | - | (only through other tests) |
| server.py | 460 | `_dns_text` | 1/1 | - | (only through other tests) |
| server.py | 465 | `cloudflare_routes` | 4/4 | - | cloudflare_changes |
| server.py | 474 | `cloudflare_dns_set` | 8/8 | - | cloudflare_changes, round3, server |
| server.py | 492 | `cloudflare_dns_delete` | 9/9 | - | cloudflare_changes, server |
| server.py | 507 | `cloudflare_route_set` | 19/19 | - | cloudflare_changes, round3, server |
| server.py | 539 | `cloudflare_route_delete` | 9/9 | - | cloudflare_changes, round3, server |
| server.py | 554 | `run_terminal_open` | 1/1 | - | (only through other tests) |
| server.py | 558 | `run_terminal_close` | 1/1 | - | (only through other tests) |
| server.py | 562 | `run_terminal_write` | 1/1 | - | (only through other tests) |
| server.py | 567 | `server_numbers` | 1/1 | - | terminal |
| server.py | 573 | `terminal_list` | 1/1 | - | terminal |
| server.py | 579 | `terminal_read` | 1/1 | - | terminal |
| server.py | 585 | `terminal_open` | 2/2 | - | server, terminal |
| server.py | 592 | `terminal_close` | 2/2 | - | server, terminal |
| server.py | 599 | `terminal_write` | 14/14 | - | round3, server, terminal |
| server.py | 624 | `ops_result` | 2/2 | - | cloudflare_changes, consent, round3, server |
| server.py | 630 | `main` | 17/17 | - | coolify, gaps2, round3, server |
| terminal.py | 61 | `configured` | 1/1 | - | cloudflare_more, server, terminal |
| terminal.py | 65 | `check_name` | 3/3 | - | terminal |
| terminal.py | 71 | `check_text` | 3/3 | - | terminal |
| terminal.py | 77 | `warnings` | 1/1 | - | terminal |
| terminal.py | 81 | `session` | 1/1 | - | gaps2, terminal |
| terminal.py | 85 | `exact` | 1/1 | - | terminal |
| terminal.py | 90 | `pane` | 1/1 | - | terminal |
| terminal.py | 94 | `line_digest` | 1/1 | - | round3, terminal |
| terminal.py | 98 | `_rate` | 5/5 | - | (only through other tests) |
| terminal.py | 106 | `_connect` | 7/7 | - | (only through other tests) |
| terminal.py | 120 | `connection` | 8/8 | - | terminal |
| terminal.py | 134 | `_q` | 3/3 | - | (only through other tests) |
| terminal.py | 141 | `run` | 4/4 | - | auth, confirm_app, confirm_more, consent |
| terminal.py | 150 | `numbers` | 7/7 | - | terminal |
| terminal.py | 161 | `list_sessions` | 4/4 | - | round3, terminal |
| terminal.py | 168 | `open_session` | 8/8 | - | gaps2, round3, terminal |
| terminal.py | 179 | `close_session` | 5/5 | - | terminal |
| terminal.py | 187 | `_screen` | 5/5 | - | (only through other tests) |
| terminal.py | 195 | `prompt_context` | 5/5 | - | round3 |
| terminal.py | 205 | `visible` | 1/1 | - | round3 |
| terminal.py | 210 | `read` | 9/9 | - | cloudflare, cloudflare_changes, cloudflare_more, consent |
| terminal.py | 222 | `prompt_line` | 3/3 | - | terminal |
| terminal.py | 229 | `write` | 19/19 | - | gaps2, misc, terminal |
| terminal.py | 253 | `describe` | 2/2 | - | auth |
