import uuid

from pydantic import BaseModel, ConfigDict


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    tools: list[str] = []

    @classmethod
    def from_model(cls, agent) -> "AgentRead":
        return cls(
            id=agent.id,
            slug=agent.slug,
            name=agent.name,
            description=agent.description,
            tools=(agent.config or {}).get("tools", []),
        )
