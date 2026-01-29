import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add current directory to path so we can import mcp_client
sys.path.append(os.getcwd())

import mcp_client

# Sample data from user request
SAMPLE_LISTS_RESPONSE = {
    "result": [
        {
            "id": "693f1fa43a2eee44f12473c2",
            "name": "TODO",
            "closed": False,
            "color": None,
            "idBoard": "693f1f986ff29bdef94b9911",
            "pos": 140737488257024,
            "subscribed": False,
            "softLimit": None,
            "type": None,
            "datasource": {"filter": False},
        },
        # ... (truncated for brevity in source code, but logically represented)
        {
            "id": "693f1fa5f99512fcb0b819a2",
            "name": "In Progress",
            "closed": False,
            "color": None,
            "idBoard": "693f1f986ff29bdef94b9911",
            "pos": 140737488273408,
            "subscribed": False,
            "softLimit": None,
            "type": None,
            "datasource": {"filter": False},
        },
    ]
}

SAMPLE_CARD_FULL = {
    "id": "69405734b1006153fd57940d",
    "agent": {"name": None, "conversationId": None},
    "badges": {
        "attachments": 0,
        "fogbugz": "",
        "checkItems": 0,
        "checkItemsChecked": 0,
        "checkItemsEarliestDue": None,
        "comments": 0,
        "description": True,
        "due": None,
        "dueComplete": False,
        "lastUpdatedByAi": False,
        "start": None,
        "externalSource": None,
        "attachmentsByType": {"trello": {"board": 0, "card": 0}},
        "location": False,
        "votes": 0,
        "maliciousAttachments": 0,
        "viewingMemberVoted": False,
        "subscribed": False,
    },
    "checkItemStates": [],
    "closed": False,
    "dueComplete": False,
    "dateLastActivity": "2026-01-17T13:24:55.435Z",
    "desc": "## Status: 🔄 IN PROGRESS\n\n## Scope (Refined)\nThe Grimoire is a player-facing overlay...",
    "descData": {"emoji": {}},
    "due": None,
    "dueReminder": None,
    "email": None,
    "idBoard": "693f1f986ff29bdef94b9911",
    "idChecklists": [],
    "idList": "6940fe15a441af0cf2b63f59",
    "idMembers": [],
    "idMembersVoted": [],
    "idShort": 13,
    "idAttachmentCover": None,
    "labels": [
        {
            "id": "693f1f986ff29bdef94b9949",
            "idBoard": "693f1f986ff29bdef94b9911",
            "idOrganization": "6211445b24064d6220cef839",
            "name": "Medium",
            "nodeId": "ari:cloud:trello::label/workspace/...",
            "color": "yellow",
            "uses": 9,
        }
    ],
    "idLabels": ["693f1f986ff29bdef94b9949"],
    "manualCoverAttachment": False,
    "name": 'Implement "Grimoire" In-Game UI (Skill Generation + Loadout)',
    "nodeId": "ari:cloud:trello::card/workspace/...",
    "pinned": False,
    "pos": 140737488330752,
    "shortLink": "hKO8DKUN",
    "shortUrl": "https://trello.com/c/hKO8DKUN",
    "start": None,
    "subscribed": False,
    "url": "https://trello.com/c/hKO8DKUN/13-implement-grimoire-in-game-ui-skill-generation-loadout",
    "cover": {
        "idAttachment": None,
        "color": None,
        "idUploadedBackground": None,
        "size": "normal",
        "brightness": "dark",
        "yPosition": 0.5,
        "idPlugin": None,
    },
    "isTemplate": False,
    "cardRole": None,
    "mirrorSourceId": None,
}


def test_simplify_card():
    print("\n--- Testing simplify_card ---")
    original_size = len(json.dumps(SAMPLE_CARD_FULL))
    simplified = mcp_client.simplify_card(SAMPLE_CARD_FULL)
    new_size = len(json.dumps(simplified))
    
    print(f"Original size (chars): {original_size}")
    print(f"Simplified size (chars): {new_size}")
    print(f"Reduction: {100 - (new_size/original_size)*100:.2f}%")
    
    expected_keys = {"id", "name", "desc", "url", "list_id", "board_id", "labels"}
    found_keys = set(simplified.keys())
    
    # Check if we have essential keys
    missing = expected_keys - found_keys
    if missing and "due" not in missing and "member_ids" not in missing: # due/members are optional/empty here
         print(f"FAILED: Missing keys: {missing}")
    else:
        print("PASSED: Key verification")
        
    # Check simplified label
    if simplified["labels"][0]["name"] == "Medium" and "uses" not in simplified["labels"][0]:
        print("PASSED: Label simplification")
    else:
        print("FAILED: Label simplification")

def test_simplify_list():
    print("\n--- Testing simplify_list ---")
    original = SAMPLE_LISTS_RESPONSE["result"][0]
    simplified = mcp_client.simplify_list(original)
    
    if "pos" not in simplified and "name" in simplified:
        print("PASSED: List simplification")
    else:
        print("FAILED: List simplification")

def test_env_var_logic():
    print("\n--- Testing Env Var Logic ---")
    
    # Default (None/0)
    if "TRELLO_OPTIMIZE_RESPONSE" in os.environ:
        del os.environ["TRELLO_OPTIMIZE_RESPONSE"]
    
    if not mcp_client.should_optimize():
        print("PASSED: Default (unset) should be False")
    else:
        print("FAILED: Default (unset) should be False")
        
    os.environ["TRELLO_OPTIMIZE_RESPONSE"] = "0"
    if not mcp_client.should_optimize():
        print("PASSED: '0' should be False")
    else:
        print("FAILED: '0' should be False")
        
    os.environ["TRELLO_OPTIMIZE_RESPONSE"] = "1"
    if mcp_client.should_optimize():
        print("PASSED: '1' should be True")
    else:
        print("FAILED: '1' should be True")

if __name__ == "__main__":
    test_simplify_card()
    test_simplify_list()
    test_env_var_logic()
