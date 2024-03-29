from datetime import datetime
from http import HTTPStatus
from logging import getLogger
from typing import Any
from uuid import UUID
import discord
import httpx
from pydantic import BaseModel, TypeAdapter

LOGGER = getLogger(__name__)


class UserSchema(BaseModel):
    username: str


class PersonSchema(BaseModel):
    id: UUID
    display_name: str
    discord_id: int | None
    current_score: float
    created_at: datetime
    updated_at: datetime

    def get_display_for_message(self) -> str:
        if self.discord_id:
            return f"<@{self.discord_id}>"
        return self.display_name


class PersonLinkSchema(BaseModel):
    id: UUID
    display_name: str


class ConsequenceLinkSchema(BaseModel):
    id: UUID
    content: str


class RatificationSchema(BaseModel):
    id: UUID
    consequence: ConsequenceLinkSchema
    created_by: PersonLinkSchema
    created_at: datetime
    updated_at: datetime


class AccusationSchema(BaseModel):
    id: UUID
    quote: str
    suspect: PersonLinkSchema
    created_by: PersonLinkSchema
    ratification: RatificationSchema | None
    created_at: datetime
    updated_at: datetime


class FerryAPI:
    def __init__(self, api_url: str, api_key: str) -> None:
        self._api_url = api_url
        self._api_key = api_key

        self._client = httpx.AsyncClient()

    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }
        resp = await self._client.request(
            method, self._api_url + endpoint, headers=headers, **kwargs
        )
        resp.raise_for_status()
        return resp.json()

    async def get_current_user(self) -> UserSchema:
        data = await self._request("GET", "/users/me")
        return UserSchema.model_validate(data)

    async def get_leaderboard(
        self,
    ) -> list[PersonSchema]:
        data = await self._request("GET", "/people/?ordering=-current_score&limit=10")
        ta = TypeAdapter(list[PersonSchema])
        return ta.validate_python(data["items"])

    async def get_person(self, person_id: UUID) -> PersonSchema:
        data = await self._request("GET", f"/people/{person_id}")
        return PersonSchema.model_validate(data)

    async def get_person_for_discord_member(
        self, member: discord.User | discord.Member
    ) -> PersonSchema:
        try:
            data = await self._request("GET", f"/people/by-discord-id/{member.id}")
            return PersonSchema.model_validate(data)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == HTTPStatus.NOT_FOUND:
                LOGGER.info(f"Creating new person for {member}")
                payload = {"display_name": member.display_name, "discord_id": member.id}
                data = await self._request("POST", "/people/", json=payload)
                return PersonSchema.model_validate(data)
            else:
                raise

    async def create_accusation(
        self, created_by: UUID, suspect: UUID, quote: str
    ) -> AccusationSchema:
        payload = {
            "quote": quote,
            "suspect": str(suspect),
            "created_by": str(created_by),
        }
        data = await self._request("POST", "/accusations/", json=payload)
        return AccusationSchema.model_validate(data)

    async def get_accusation(self, accusation_id: UUID) -> AccusationSchema:
        data = await self._request("GET", f"/accusations/{accusation_id}")
        return AccusationSchema.model_validate(data)

    async def create_ratification(
        self, accusation_id: UUID, created_by: UUID
    ) -> RatificationSchema:
        payload = {
            "created_by": str(created_by),
        }
        data = await self._request(
            "POST", f"/accusations/{accusation_id}/ratification", json=payload
        )
        return RatificationSchema.model_validate(data)
