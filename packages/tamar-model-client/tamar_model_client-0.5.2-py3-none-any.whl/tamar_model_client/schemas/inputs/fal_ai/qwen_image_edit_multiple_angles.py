from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel, Field

from tamar_model_client.schemas.inputs.base import TamarFileIdInput


class FalAIQwenImageEditMultipleAnglesInput(BaseModel):
    """Fal AI Qwen Image Edit 2511 Multiple Angles 请求参数

    该模型支持调整图片的水平和垂直拍摄角度，以及相机缩放距离。
    适用于需要改变物体观察角度的场景。
    """

    image_urls: Union[List[str], List[TamarFileIdInput]] = Field(
        ...,
        description="要调整相机角度的图片URL列表"
    )

    horizontal_angle: Optional[float] = Field(
        default=None,
        ge=0,
        le=360,
        description="水平旋转角度（度数）。0°=正面视图，90°=右侧视图，180°=背面视图，270°=左侧视图，360°=正面视图"
    )

    vertical_angle: Optional[float] = Field(
        default=None,
        ge=-30,
        le=90,
        description="垂直相机角度（度数）。-30°=低角度仰视，0°=平视，30°=俯视，60°=高角度，90°=鸟瞰"
    )

    zoom: Optional[float] = Field(
        default=5,
        ge=0,
        le=10,
        description="相机缩放/距离。0=广角（远距离），5=中景（正常），10=特写（非常近）"
    )

    lora_scale: Optional[float] = Field(
        default=1,
        description="LoRA模型的缩放因子，控制相机控制效果的强度"
    )

    image_size: Optional[Union[
        Literal["square_hd", "square", "portrait_4_3", "portrait_16_9", "landscape_4_3", "landscape_16_9"],
        Dict[str, Any]
    ]] = Field(
        default=None,
        description="生成图片的尺寸。可以是预设尺寸枚举值，或自定义{'width': 1280, 'height': 720}"
    )

    guidance_scale: Optional[float] = Field(
        default=4.5,
        description="CFG (Classifier Free Guidance) 缩放系数"
    )

    num_inference_steps: Optional[int] = Field(
        default=28,
        description="执行的推理步骤数"
    )

    acceleration: Optional[Literal["none", "regular"]] = Field(
        default="regular",
        description="图像生成的加速级别"
    )

    negative_prompt: Optional[str] = Field(
        default="",
        description="负面提示词，用于生成时排除的内容"
    )

    seed: Optional[int] = Field(
        default=None,
        description="随机种子，用于可重现性"
    )

    sync_mode: Optional[bool] = Field(
        default=False,
        description="如果为True，媒体将作为data URI返回"
    )

    enable_safety_checker: Optional[bool] = Field(
        default=True,
        description="是否启用安全检查器"
    )

    output_format: Optional[Literal["png", "jpeg", "webp"]] = Field(
        default="png",
        description="输出图片的格式"
    )

    num_images: Optional[int] = Field(
        default=1,
        description="生成的图片数量"
    )

    model_config = {
        "arbitrary_types_allowed": True
    }
