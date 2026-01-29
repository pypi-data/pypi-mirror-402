from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel, Field

from tamar_model_client.schemas.inputs.base import TamarFileIdInput


class FalAIQwenImageEditInput(BaseModel):
    """Fal AI Qwen Image Edit Plus 请求参数"""

    image_urls: Union[List[str], List[TamarFileIdInput]] = Field(
        ...,
        description="要调整相机角度的图片URL列表"
    )
    image_size: Optional[Union[
        Literal["square_hd", "square", "portrait_4_3", "portrait_16_9", "landscape_4_3", "landscape_16_9"],
        Dict[str, Any]
    ]] = Field(
        default=None,
        description="生成图片的尺寸"
    )
    guidance_scale: Optional[float] = Field(
        default=1.0,
        description="CFG引导比例"
    )
    num_inference_steps: Optional[int] = Field(
        default=6,
        description="推理步骤数"
    )
    acceleration: Optional[Literal["none", "regular"]] = Field(
        default="regular",
        description="加速级别"
    )
    negative_prompt: Optional[str] = Field(
        default=None,
        description="负面提示词"
    )
    seed: Optional[int] = Field(
        default=None,
        description="随机种子"
    )
    sync_mode: Optional[bool] = Field(
        default=False,
        description="是否同步模式"
    )
    enable_safety_checker: Optional[bool] = Field(
        default=True,
        description="是否启用安全检查器"
    )
    output_format: Optional[Literal["png", "jpeg", "webp"]] = Field(
        default="png",
        description="输出格式"
    )
    num_images: Optional[int] = Field(
        default=1,
        description="生成图像数量"
    )
    rotate_right_left: Optional[float] = Field(
        default=0.0,
        ge=-90.0,
        le=90.0,
        description="左右旋转角度。正值=向左转，负值=向右转"
    )
    move_forward: Optional[float] = Field(
        default=0.0,
        ge=0,
        le=10,
        description="相机前后移动。0=不移动，10=最大拉近特写"
    )
    vertical_angle: Optional[float] = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="垂直视角。-1=俯视/鸟瞰，0=平视，1=仰视/虫瞰"
    )
    wide_angle_lens: Optional[bool] = Field(
        default=False,
        description="是否启用广角镜头效果"
    )
    lora_scale: Optional[float] = Field(
        default=1.25,
        description="LoRA控制强度"
    )

    model_config = {
        "arbitrary_types_allowed": True
    }
