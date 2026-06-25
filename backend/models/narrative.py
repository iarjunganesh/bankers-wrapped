from pydantic import BaseModel


class Scene(BaseModel):
    id: int
    narration: str
    visual_prompt: str


class NarrativeScript(BaseModel):
    title: str
    personality: str
    scenes: list[Scene]

    @property
    def full_narration(self) -> str:
        return " ".join(scene.narration for scene in self.scenes)
