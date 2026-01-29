#!/usr/bin/env python3
"""
Simple Trello MCP Server using FastMCP

Setup with uv:
    uv init
    uv add fastmcp requests

Run:
    uv run mcp_client.py
"""

import os
from typing import Any
import requests
from fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("Trello")

# Get credentials from environment
API_KEY = os.getenv("TRELLO_API_KEY")
API_TOKEN = os.getenv("TRELLO_API_TOKEN")
# API_KEY = "e4457319090ef485a16b824d03312513"
# API_TOKEN = (
#     "ATTA04d104eafe6fa39de5f18025157b8da6f15310fcd4dfbf5ae7dc881801907edb14D0EE7B"
# )
BASE_URL = "https://api.trello.com/1"


def trello_request(endpoint: str, method: str = "GET", data: dict | None = None) -> Any:
    """Make a request to Trello API"""
    url = f"{BASE_URL}{endpoint}"
    params = {"key": API_KEY, "token": API_TOKEN}

    if method == "GET":
        response = requests.get(url, params=params)
    elif method == "POST":
        response = requests.post(url, params=params, json=data)
    elif method == "PUT":
        response = requests.put(url, params=params, json=data)
    elif method == "DELETE":
        response = requests.delete(url, params=params)

    response.raise_for_status()
    return response.json()


# ============== HELPERS ==============


def should_optimize() -> bool:
    """Check if response optimization is enabled"""
    return os.getenv("TRELLO_OPTIMIZE_RESPONSE", "0") == "1"


def simplify_label(label: dict) -> dict:
    """Simplify a label object"""
    return {
        "id": label.get("id"),
        "name": label.get("name"),
        "color": label.get("color"),
    }


def simplify_card(card: dict) -> dict:
    """Simplify a card object"""
    simplified = {
        "id": card.get("id"),
        "name": card.get("name"),
        "url": card.get("url"),
        "list_id": card.get("idList"),
        "board_id": card.get("idBoard"),
    }
    
    if card.get("desc"):
        simplified["desc"] = card.get("desc")
    
    if card.get("due"):
        simplified["due"] = card.get("due")
        
    if card.get("labels"):
        simplified["labels"] = [simplify_label(l) for l in card.get("labels")]
        
    if card.get("idMembers"):
        simplified["member_ids"] = card.get("idMembers")
        
    return simplified


def simplify_list(list_obj: dict) -> dict:
    """Simplify a list object"""
    return {
        "id": list_obj.get("id"),
        "name": list_obj.get("name"),
        "board_id": list_obj.get("idBoard"),
    }


def simplify_board(board: dict) -> dict:
    """Simplify a board object"""
    return {
        "id": board.get("id"),
        "name": board.get("name"),
        "desc": board.get("desc", ""),
        "url": board.get("url"),
        "short_url": board.get("shortUrl"),
    }


# ============== BOARDS ==============


@mcp.tool()
def get_my_boards() -> list[dict]:
    """Get all boards for the authenticated user"""
    boards = trello_request("/members/me/boards")
    if should_optimize():
        return [simplify_board(b) for b in boards]
    return boards


@mcp.tool()
def get_board(board_id: str) -> dict:
    """Get details of a specific board"""
    board = trello_request(f"/boards/{board_id}")
    if should_optimize():
        return simplify_board(board)
    return board


@mcp.tool()
def create_board(name: str, desc: str = "") -> dict:
    """Create a new Trello board"""
    board = trello_request("/boards", "POST", {"name": name, "desc": desc})
    if should_optimize():
        return simplify_board(board)
    return board


# ============== LISTS ==============


@mcp.tool()
def get_board_lists(board_id: str) -> list[dict]:
    """Get all lists on a board"""
    lists = trello_request(f"/boards/{board_id}/lists")
    if should_optimize():
        return [simplify_list(l) for l in lists]
    return lists


@mcp.tool()
def create_list(board_id: str, name: str) -> dict:
    """Create a new list on a board"""
    list_obj = trello_request("/lists", "POST", {"idBoard": board_id, "name": name})
    if should_optimize():
        return simplify_list(list_obj)
    return list_obj


# ============== CARDS ==============


@mcp.tool()
def get_board_cards(board_id: str) -> list[dict]:
    """Get all cards on a board"""
    cards = trello_request(f"/boards/{board_id}/cards")
    if should_optimize():
        return [simplify_card(c) for c in cards]
    return cards


@mcp.tool()
def get_list_cards(list_id: str) -> list[dict]:
    """Get all cards in a list"""
    cards = trello_request(f"/lists/{list_id}/cards")
    if should_optimize():
        return [simplify_card(c) for c in cards]
    return cards


@mcp.tool()
def get_card(card_id: str) -> dict:
    """Get details of a specific card"""
    card = trello_request(f"/cards/{card_id}")
    if should_optimize():
        return simplify_card(card)
    return card


@mcp.tool()
def create_card(list_id: str, name: str, desc: str = "") -> dict:
    """Create a new card in a list"""
    card = trello_request(
        "/cards", "POST", {"idList": list_id, "name": name, "desc": desc}
    )
    if should_optimize():
        return simplify_card(card)
    return card


@mcp.tool()
def update_card(card_id: str, name: str | None = None, desc: str | None = None) -> dict:
    """Update a card's name or description"""
    data = {}
    if name:
        data["name"] = name
    if desc:
        data["desc"] = desc
    card = trello_request(f"/cards/{card_id}", "PUT", data)
    if should_optimize():
        return simplify_card(card)
    return card


@mcp.tool()
def move_card(card_id: str, list_id: str) -> dict:
    """Move a card to a different list"""
    card = trello_request(f"/cards/{card_id}", "PUT", {"idList": list_id})
    if should_optimize():
        return simplify_card(card)
    return card


# ============== ACTIONS ==============


@mcp.tool()
def get_board_actions(board_id: str, limit: int = 50) -> list[dict]:
    """Get recent actions (activity) on a board"""
    # Actions are complex and variable, leaving as-is for now or could simplify later
    # The user request focused on lists and cards mostly.
    return trello_request(f"/boards/{board_id}/actions?limit={limit}")


@mcp.tool()
def get_card_actions(card_id: str, limit: int = 50) -> list[dict]:
    """Get actions (activity/comments) on a card"""
    return trello_request(f"/cards/{card_id}/actions?limit={limit}")


@mcp.tool()
def get_action(action_id: str) -> dict:
    """Get details of a specific action"""
    return trello_request(f"/actions/{action_id}")


@mcp.tool()
def update_comment(action_id: str, text: str) -> dict:
    """Update a comment (action must be a comment type)"""
    return trello_request(f"/actions/{action_id}", "PUT", {"text": text})


@mcp.tool()
def delete_comment(action_id: str) -> dict:
    """Delete a comment (action must be a comment type)"""
    return trello_request(f"/actions/{action_id}", "DELETE")


# ============== COMMENTS ==============


@mcp.tool()
def add_comment(card_id: str, text: str) -> dict:
    """Add a comment to a card"""
    return trello_request(f"/cards/{card_id}/actions/comments", "POST", {"text": text})


# ============== MEMBERS ==============


@mcp.tool()
def get_me() -> dict:
    """Get information about the authenticated user"""
    return trello_request("/members/me")


def main():
    """Entry point for the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
