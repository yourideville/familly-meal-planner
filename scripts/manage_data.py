#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path
from urllib.parse import quote

import httpx


class MealPlannerDataManager:
    def __init__(self, api_url: str, username: str, password: str) -> None:
        self.base_url = api_url.rstrip("/")
        self.username = username
        self.password = password
        self.client = httpx.Client(base_url=self.base_url, timeout=30.0)

    def login(self) -> None:
        response = self.client.post(
            "/admin/login",
            json={"username": self.username, "password": self.password},
        )
        response.raise_for_status()

    def list_members(self) -> list[str]:
        response = self.client.get("/admin/members")
        response.raise_for_status()
        return response.json()

    def add_member(self, name: str) -> None:
        response = self.client.post("/admin/members", json={"name": name})
        response.raise_for_status()

    def delete_member(self, name: str) -> None:
        response = self.client.delete(f"/admin/members/{quote(name, safe='')}")
        response.raise_for_status()

    def list_dishes(self) -> list[dict]:
        response = self.client.get("/admin/dishes")
        response.raise_for_status()
        return response.json()

    def add_dish(self, name: str, category: str, tags: list[str]) -> None:
        payload = {"name": name, "category": category, "tags": tags}
        response = self.client.post("/admin/dishes", json=payload)
        response.raise_for_status()

    def delete_dish(self, dish_id: str) -> None:
        response = self.client.delete(f"/admin/dishes/{quote(dish_id, safe='')}")
        response.raise_for_status()

    def upload_members(self, csv_path: Path) -> None:
        with csv_path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            if "name" not in reader.fieldnames:
                raise ValueError("Member CSV must contain a 'name' column")
            for row in reader:
                name = row["name"].strip()
                if not name:
                    continue
                try:
                    self.add_member(name)
                    print(f"Added member: {name}")
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 400:
                        print(f"Skipped member (already exists?): {name}")
                    else:
                        raise

    def upload_dishes(self, csv_path: Path) -> None:
        with csv_path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            if "name" not in reader.fieldnames or "category" not in reader.fieldnames:
                raise ValueError("Dish CSV must contain 'name' and 'category' columns")
            for row in reader:
                name = row["name"].strip()
                category = row["category"].strip()
                tags = []
                if "tags" in row and row["tags"] is not None:
                    tags = [tag.strip() for tag in row["tags"].split(";") if tag.strip()]
                if not name or not category:
                    continue
                try:
                    self.add_dish(name, category, tags)
                    print(f"Added dish: {name} ({category})")
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code in (400, 409):
                        print(f"Skipped dish (already exists?): {name}")
                    else:
                        raise

    def cleanup(self) -> None:
        dishes = self.list_dishes()
        for dish in dishes:
            self.delete_dish(dish["id"])
            print(f"Deleted dish: {dish['id']} {dish.get('name', '')}")

        members = self.list_members()
        for member in members:
            self.delete_member(member)
            print(f"Deleted member: {member}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload CSV seed data and cleanup all dishes and members in Family Meal Planner."
    )
    parser.add_argument("--api-url", required=True, help="Backend API base URL, e.g. http://localhost:8000")
    parser.add_argument("--admin-password", required=True, help="Admin password to authenticate against the backend")
    parser.add_argument("--admin-username", default="admin", help="Admin username (default: admin)")
    parser.add_argument("--members-csv", type=Path, help="Path to a members CSV file with a 'name' column")
    parser.add_argument(
        "--dishes-csv",
        type=Path,
        help="Path to a dishes CSV file with columns 'name', 'category', and optional 'tags' separated by ';'",
    )
    parser.add_argument("--cleanup", action="store_true", help="Delete all dishes and members from the backend")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manager = MealPlannerDataManager(args.api_url, args.admin_username, args.admin_password)
    manager.login()

    if args.cleanup:
        manager.cleanup()

    if args.members_csv:
        manager.upload_members(args.members_csv)

    if args.dishes_csv:
        manager.upload_dishes(args.dishes_csv)

    if not args.cleanup and not args.members_csv and not args.dishes_csv:
        raise SystemExit("No action requested. Specify --members-csv, --dishes-csv or --cleanup.")


if __name__ == "__main__":
    main()
