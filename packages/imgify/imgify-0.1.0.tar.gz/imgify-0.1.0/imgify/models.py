from enum import StrEnum

from pydantic import BaseModel, model_serializer

class ImageModelApiName(StrEnum):
    GPT_IMAGE_1 = "gpt-image-1"
    DALL_E_2 = "dall-e-2"
    DALL_E_3 = "dall-e-3"


class ImageQuality(StrEnum):
    STANDARD = "standard"
    HD = "hd"


class ImageSize(StrEnum):
    SQUARE_256 = "256x256"
    SQUARE_512 = "512x512"
    SQUARE_1024 = "1024x1024"
    LANDSCAPE_1792 = "1792x1024"
    PORTRAIT_1792 = "1024x1792"


class ImageResponse(BaseModel):
    b64_json: str


class ResponseFormat(StrEnum):
    B64_JSON = "b64_json"


class ImageGenerationConfig(BaseModel):
    model: ImageModelApiName
    prompt: str
    size: ImageSize = ImageSize.SQUARE_1024
    quality: ImageQuality | None = None
    response_format: ResponseFormat = ResponseFormat.B64_JSON

    @model_serializer
    def to_api_params(self) -> dict[str, str | int]:
        params = {
            "model": self.model.value,
            "prompt": self.prompt,
            "n": 1,
            "size": self.size.value,
        }

        if self.quality is not None:
            params["quality"] = self.quality.value

        return params
