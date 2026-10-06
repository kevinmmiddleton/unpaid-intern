"""The ask-first hook: which connector tools make Claude stop and ask, every time.

The skill's rules already say "drafts are fine, sending is yours." This hook backs that up outside the
prompt. When the plugin is installed, any connector tool whose name sends, shares, deletes, or changes
something outside the user's folder triggers a permission prompt, even if the user clicked
"always allow" earlier. Reads, searches, and drafts pass through untouched.

The matcher is one regular expression over tool names (mcp__<server>__<tool>). It uses only features that
behave the same in JavaScript (Claude Code) and Python (these tests), and tools/hook_check.mjs proves it
against the same names in JavaScript. Its repetition is bounded, so it stays fast on long names. The command is a single-quoted echo, which works in bash and PowerShell
and needs no Python on the user's machine.
"""
from __future__ import annotations

import json
import re
import time

# How a tool name is read: mcp__<server>__<tool>. Only the tool part counts, so a server called
# "post-office" never trips it. The action word has to come first in the tool name, or after at most two
# leading words that aren't read words (slack_send_message, google_calendar_create_event). That keeps
# get_merge_request and get_schedule (reads) apart from merge_pull_request and schedule_message (writes).

# Verbs that always ask, whatever they act on.
ALWAYS = ("send reply forward post share invite publish delete trash untrash remove archive respond transition upload "
          "schedule assign move duplicate merge grant revoke cancel decline accept approve submit close "
          "reopen push spam unsubscribe refund pay charge buy purchase finalize void execute rerun retry trigger "
          "invoke deploy rollback pause start stop enable disable reset rebase restore transfer terminate revert "
          "manage upsert reject escalate acknowledge snooze").split()
# Verbs that ask when the object lives somewhere other people can see it, or when they stand alone.
CHANGE = ("create update edit add change copy save set write put patch insert append rename import bulk batch modify "
          "replace clear").split()
OBJECTS = ("issue issues page pages task tasks event events item items comment comments canvas database databases "
           "project projects file files folder update updates message messages column subtask subtasks doc docs "
           "document record records ticket tickets card cards epic story bug row rows sheet spreadsheet deal contact "
           "lead account opportunity case board block blocks reaction meeting invite attachment link note notes post "
           "reminder status value values field fields member members permission permissions pull review release "
           "branch repository commit refund refunds invoice invoices customer customers subscription subscriptions "
           "payment payments order orders product products price prices coupon object objects crm worklog transaction "
           "transactions deployment deployments migration migrations sql query source envelope contract policy user "
           "users group groups role roles domain webhook secret key keys token environment config configuration "
           "view section goal goals form list cells cell range text api firewall rule rules alert monitor dashboard "
           "tag tags sprint milestone version cycle component calendar channel workspace team space chart slide "
           "presentation design frame node variable style incident incidents responder responders application "
           "applications bill bills flag flags email emails").split()
# Verbs that ask only with one kind of object (applying a migration, not a private mail label).
PAIRS = {"apply": "migration migrations changes patch policy template".split(),
         "mark": "spam junk done complete completed resolved".split(),
         # "run" a command or a job asks; "run" a report or a read query doesn't
         "run": "command commands script scripts code job jobs workflow workflows pipeline pipelines session migration task tasks automation".split(),
         # "resolve" an incident or a thread asks; resolve-library-id (a lookup) doesn't
         "resolve": "incident incidents issue issues ticket tickets thread threads comment comments alert alerts conversation conversations".split()}
# Claude's own app tools, which talk to you rather than to anyone else.
SKIP_SERVERS = ["cowork", "visualize", "memory"]
# Read words that, at the front of a tool name, mean the rest is a noun (get_merge_request, list_posts).
READS = ("get list search read fetch find query describe show view count lookup retrieve check download export "
         "browse preview").split()
# Write tools whose names don't follow any pattern.
EXACT = ["use_figma"]

REASON = ("Unpaid Intern: this tool sends, shares, changes, or deletes something outside your folder. "
          "Approve only if you have seen exactly what will happen.")


def _alt(words):
    return "|".join(words)


def _cap(words):
    return "|".join(w[0].upper() + w[1:] for w in words)


def _both(words):
    """Each word as written and in capitals, for names like GMAIL_SEND_EMAIL."""
    return words + [w.upper() for w in words]


def matcher() -> str:
    a, b, o = _alt(_both(ALWAYS)), _alt(_both(CHANGE)), _alt(_both(OBJECTS))
    reads = _alt(_both(READS))
    # up to three leading words that aren't read words: "slack_", "google_calendar_", "GMAIL_", "notion-"
    prefix = rf"(?:(?!(?:{reads})(?:[_-]|[A-Z]|$))[A-Za-z0-9]+[_-]){{0,3}}"
    snake = (rf"(?:{a})(?:[_-]|$)"
             rf"|(?:{b})(?:$|[_-](?:[a-z0-9]+[_-]){{0,2}}(?:{o})(?:[_-]|$))")
    camel = (rf"(?:{a})[A-Z]"
             rf"|(?:{b})(?:[A-Z][a-z0-9]+){{0,2}}(?:{_cap(OBJECTS)})(?:[A-Z]|$)")
    pairs = "|".join(rf"{v}(?:[_-](?:[a-z0-9]+[_-]){{0,2}}(?:{_alt(objs)})(?:[_-]|$)|(?:[A-Z][a-z0-9]+){{0,2}}(?:{_cap(objs)})(?:[A-Z]|$))"
                     for v, objs in PAIRS.items())
    exact = "|".join(rf"{e}$" for e in EXACT)
    skip = "|".join(SKIP_SERVERS)
    return rf"^mcp__(?!(?:{skip})__).+__{prefix}(?:{snake}|{camel}|{pairs}|{exact})"


def hooks_json() -> str:
    decision = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                       "permissionDecisionReason": REASON}}
    payload = json.dumps(decision, separators=(",", ":"))
    assert "'" not in payload, "the echo is single-quoted; keep apostrophes out of the reason"
    doc = {
        "description": "Ask before connector tools whose names send, share, change, pay for, or delete something outside your folder. A name pattern: it catches the common tools, not every possible one.",
        "hooks": {"PreToolUse": [{"matcher": matcher(),
                                  "hooks": [{"type": "command", "command": f"echo '{payload}'", "timeout": 5}]}]},
    }
    return json.dumps(doc, indent=2) + "\n"


# Tool names from Gmail, Google Calendar, Google Drive, Slack, Atlassian, Notion, Asana, Linear, monday.com,
# ClickUp, Box, GitHub, Microsoft 365, Stripe, HubSpot, Supabase, and Vercel, plus a few made-up ones in other
# naming styles (mcp__x__..., mcp__s__...) to cover camelCase and short names.
MUST_ASK = """
mcp__g__send_message mcp__g__reply mcp__g__forward mcp__g__trash_message mcp__g__trash_thread mcp__g__delete_draft
mcp__cal__create_event mcp__cal__update_event mcp__cal__delete_event mcp__cal__respond_to_event
mcp__drive__share_file mcp__drive__trash_file mcp__drive__create_file mcp__drive__update_file mcp__drive__copy_file
mcp__plugin_unpaid-intern_slack__slack_send_message mcp__plugin_unpaid_intern_slack__slack_schedule_message
mcp__slack__slack_create_canvas mcp__slack__slack_send_message_draft
mcp__atl__createJiraIssue mcp__atl__editJiraIssue mcp__atl__transitionJiraIssue mcp__atl__addCommentToJiraIssue
mcp__atl__createConfluencePage mcp__atl__updateConfluencePage mcp__atl__createConfluenceFooterComment
mcp__notion__notion-create-pages mcp__notion__notion-update-page mcp__notion__notion-move-pages
mcp__notion__notion-duplicate-page mcp__notion__notion-create-comment mcp__notion__notion-create-database
mcp__asana__asana_create_task mcp__asana__asana_update_task mcp__asana__asana_delete_task mcp__asana__asana_create_project
mcp__linear__create_issue mcp__linear__update_issue mcp__linear__create_comment mcp__linear__save_issue
mcp__monday__create_item mcp__monday__change_item_column_values mcp__monday__delete_item mcp__monday__create_update
mcp__clickup__clickup_create_task mcp__clickup__clickup_update_task mcp__clickup__clickup_create_task_comment
mcp__box__upload_file mcp__box__delete_file mcp__gh__create_pull_request_review mcp__gh__merge_pull_request
mcp__gh__add_issue_comment mcp__gh__push_files mcp__gh__create_or_update_file
mcp__hubspot__create_contact mcp__sf__updateRecord mcp__teams__post_message mcp__x__sendMessage mcp__x__deleteFile
mcp__zd__update_ticket mcp__x__postMessage mcp__s__slack_post
mcp__claude_ai_Asana__add_comment mcp__claude_ai_Asana__update_tasks
mcp__g__mark_message_spam mcp__g__mark_thread_spam mcp__g__untrash_message mcp__supabase__execute_sql
mcp__supabase__apply_migration mcp__supabase__pause_project mcp__supabase__deploy_edge_function mcp__vercel__buy_domain
mcp__vercel__create_deployment mcp__vercel__request_rollback mcp__stripe__create_refund mcp__stripe__finalize_invoice
mcp__stripe__create_invoice mcp__stripe__create_customer mcp__stripe__update_subscription mcp__hubspot__manage_crm_objects
mcp__atl__addWorklogToJiraIssue mcp__notion__notion-update-data-source mcp__docusign__send_envelope
mcp__figma__use_figma mcp__supabase__reset_branch mcp__supabase__rebase_branch
mcp__vercel__update_firewall_config mcp__vercel__start_rolling_release mcp__vercel__run_session_command
mcp__vercel__create_api_keys mcp__x__update mcp__x__create mcp__x__batch_update mcp__x__upsert_record
mcp__gcal__google_calendar_create_event mcp__s__slack_schedule_message
mcp__pagerduty__create_incident mcp__pagerduty__update_incident mcp__pagerduty__add_responders mcp__servicenow__resolve_incident
mcp__greenhouse__reject_application mcp__qb__create_bill mcp__gm__modify_email mcp__gdocs__replace_all_text
mcp__gsheets__clear_values mcp__posthog__create-feature-flag mcp__composio__GMAIL_SEND_EMAIL
mcp__zapier__google_calendar_quick_add_event mcp__x__run_workflow
""".split()

MUST_PASS = """
mcp__g__create_draft mcp__g__update_draft mcp__g__get_message mcp__g__search_threads mcp__g__list_labels
mcp__g__label_message mcp__g__create_label mcp__g__update_label mcp__g__get_draft mcp__g__list_drafts
mcp__cal__list_events mcp__cal__get_event mcp__cal__search_events mcp__cal__suggest_time mcp__cal__list_calendars
mcp__drive__read_file_content mcp__drive__search_files mcp__drive__get_file_permissions mcp__drive__list_recent_files
mcp__drive__download_file_content mcp__drive__get_file_metadata
mcp__slack__slack_read_channel mcp__slack__slack_search_public mcp__slack__slack_read_thread mcp__slack__slack_search_users
mcp__atl__getJiraIssue mcp__atl__searchJiraIssuesUsingJql mcp__atl__getConfluencePage mcp__atl__getAccessibleAtlassianResources
mcp__atl__getTransitionsForJiraIssue mcp__atl__lookupJiraAccountId
mcp__notion__notion-search mcp__notion__notion-fetch mcp__notion__notion-get-comments mcp__notion__notion-get-users
mcp__asana__asana_search_tasks mcp__asana__asana_get_task mcp__linear__list_issues mcp__linear__get_issue
mcp__linear__list_comments mcp__monday__get_board_items mcp__clickup__clickup_search mcp__box__search_files
mcp__box__get_file_content mcp__m365__sharepoint_search mcp__m365__sharepoint_folder_search mcp__m365__outlook_email_search
mcp__m365__outlook_calendar_search mcp__m365__chat_message_search mcp__m365__find_meeting_availability mcp__m365__read_resource
mcp__posthog__get_events mcp__postgres__query mcp__plugin_unpaid_intern_box__search_files mcp__x__getPosts
mcp__x__listMessages mcp__x__list_posts mcp__gh__list_pull_requests mcp__gh__get_commit
mcp__claude_ai_Asana__get_task mcp__claude_ai_Asana__search_objects
mcp__g__apply_sensitive_message_label mcp__g__unlabel_thread mcp__supabase__list_tables
mcp__stripe__list_customers mcp__stripe__retrieve_invoice mcp__hubspot__search_crm_objects
mcp__plugin_post-office_x__get_mail mcp__x__getSchedule mcp__x__get_schedule mcp__gitlab__get_merge_request
mcp__gcal__google_calendar_list_events mcp__x__batch_get mcp__x__get_firewall_config mcp__vercel__list_deployments_by_status
mcp__ga__run_report mcp__bigquery__run_query mcp__sf__run_soql_query mcp__context7__resolve-library-id mcp__cowork__send_user_message
mcp__composio__GMAIL_LIST_THREADS mcp__composio__GMAIL_FETCH_EMAILS
mcp__vercel__get_deployment mcp__supabase__get_advisors mcp__vercel__list_deployments
Read Write Edit Bash
""".split()


def selftest() -> int:
    rx = re.compile(matcher())
    missed = [n for n in MUST_ASK if not rx.search(n)]
    leaked = [n for n in MUST_PASS if rx.search(n)]
    t0 = time.perf_counter()
    for i in range(2000):
        rx.search("mcp__atlassian__searchJiraIssuesUsingJqlAndAVeryLongNameWithoutSeparators" + str(i))
    slow = (time.perf_counter() - t0) > 2.0
    hj = json.loads(hooks_json())
    shape_ok = hj["hooks"]["PreToolUse"][0]["hooks"][0]["command"].startswith("echo '{")
    payload = json.loads(hj["hooks"]["PreToolUse"][0]["hooks"][0]["command"][6:-1])
    ask_ok = payload["hookSpecificOutput"]["permissionDecision"] == "ask"
    checks = [
        (f"hook asks before all {len(MUST_ASK)} send, share, change, pay, and delete tools", not missed),
        (f"hook lets all {len(MUST_PASS)} read, search, and draft tools through", not leaked),
        ("hook matcher stays fast on long names", not slow),
        ("hook command is a portable single-quoted echo", shape_ok),
        ("hook output asks for permission", ask_ok),
    ]
    for name, ok in checks:
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
    for n in missed:
        print("        should ask:", n)
    for n in leaked:
        print("        should pass:", n)
    passed = sum(ok for _, ok in checks)
    print(f"hook rules: {passed}/{len(checks)} passed")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
