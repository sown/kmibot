from datetime import datetime
from logging import getLogger
from typing import Any, Optional
from uuid import UUID
import discord
import httpx
from pydantic import BaseModel, TypeAdapter, HttpUrl, validator

LOGGER = getLogger(__name__)


class UserSchema(BaseModel):
    username: str


class PersonSchema(BaseModel):
    id: UUID
    display_name: str
    discord_id: int | None
    created_at: datetime
    updated_at: datetime

    def get_display_for_message(self) -> str:
        if self.discord_id:
            return f"<@{self.discord_id}>"
        return self.display_name


class PersonWithScoreSchema(PersonSchema):
    current_score: float


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


class FactSchema(BaseModel):
    link_token: str | None


class PubSchema(BaseModel):
    id: UUID
    name: str
    emoji: str
    menu_url: HttpUrl | None = None
    map_url: HttpUrl

    @validator("menu_url", pre=True)
    def parse_menu_url(cls, val: str) -> str | None:
        return val if val else None


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
        LOGGER.info(f"{method} {endpoint} -> {kwargs}")
        resp = await self._client.request(
            method, self._api_url + endpoint, headers=headers, **kwargs
        )
        resp.raise_for_status()
        data = resp.json()
        LOGGER.info(f"{method} {endpoint} -> {resp.status_code} {data} ")
        return data

    async def get_current_user(self) -> UserSchema:
        data = await self._request("GET", "v2/users/me/")
        return UserSchema.model_validate(data)

    async def get_leaderboard(
        self,
    ) -> list[PersonWithScoreSchema]:
        data = await self._request("GET", "v2/people/?ordering=-current_score&limit=10")
        ta = TypeAdapter(list[PersonWithScoreSchema])
        return ta.validate_python(data["results"])

    async def get_person(self, person_id: UUID) -> PersonSchema:
        data = await self._request("GET", f"v2/people/{person_id}/")
        return PersonSchema.model_validate(data)

    async def get_person_for_discord_member(
        self, member: discord.User | discord.Member
    ) -> PersonSchema:
        try:
            data = await self._request("GET", f"v2/people/?discord_id={member.id}")
        except httpx.HTTPStatusError as exc:
            raise exc

        ta = TypeAdapter(list[PersonSchema])
        try:
            return ta.validate_python(data["results"])[0]
        except IndexError:
            pass

        LOGGER.info(f"Creating new person for {member}")
        payload = {"display_name": member.display_name, "discord_id": member.id}
        data = await self._request("POST", "v2/people/", json=payload)
        return PersonSchema.model_validate(data)

    async def get_fact_for_person(self, person_id: UUID) -> FactSchema:
        data = await self._request("GET", f"v2/people/{person_id}/fact/")
        return FactSchema.model_validate(data)

    async def create_accusation(
        self, created_by: UUID, suspect: UUID, quote: str
    ) -> AccusationSchema:
        payload = {
            "quote": quote,
            "suspect": str(suspect),
            "created_by": str(created_by),
        }
        data = await self._request("POST", "v2/court/accusations/", json=payload)
        return AccusationSchema.model_validate(data)

    async def get_accusation(self, accusation_id: UUID) -> AccusationSchema:
        data = await self._request("GET", f"v2/court/accusations/{accusation_id}/")
        return AccusationSchema.model_validate(data)

    async def create_ratification(
        self, accusation_id: UUID, created_by: UUID
    ) -> RatificationSchema:
        payload = {
            "created_by": str(created_by),
        }
        data = await self._request(
            "POST", f"v2/court/accusations/{accusation_id}/ratification/", json=payload
        )
        return RatificationSchema.model_validate(data)

    async def get_pubs(
        self,
    ) -> list[PubSchema]:
        data = await self._request("GET", "v2/pub/pubs/")
        ta = TypeAdapter(list[PubSchema])
        return ta.validate_python(data["results"])
