# 底图提示词

给任何文生图模型用。只出**不含人物、不含文字**的底图：字和人由脚本叠上去。竖版和横版分别生成，不要拿竖版裁横版。

竖版用 2:3 或 3:4 的尺寸，横版用 3:2 或 16:9。

```
Background artwork for a vertical social-media video cover about <主题，一句英文>, portrait orientation.
A dark studio scene: <一个巨大的主体物件，和主题直接相关>, with <两三个陪衬元素，画成发光色块，不是可读文字>.
Cinematic rim light, deep navy-black background with <主色> and <强调色> accents, subtle grid floor, volumetric haze,
high contrast, sharp, 3D render look.
Composition: keep the top third calm and dark for a headline; keep the lower right area darker and empty for a person cut-out;
the main object sits centre-left in the middle band.
Absolutely no text, no letters, no numbers, no logos, no watermarks, no people, no hands.
```

横版把第一句改成 `horizontal ... landscape orientation`，构图那句改成：标题区在左上，人物区在右侧，主体在中间偏左。

要点：

- 最后一句的「不要字、不要人」不能省。模型画的中文字基本都是错的。
- 主体只要一个，越大越好。封面上还要叠标题、卡片和人，底图越简单越好。
- 主色跟着主题走，但全图加起来不要超过三种颜色。
- 生成后如果上三分之一太亮，在 spec 里把 `dim` 调高到 0.5。

没有生图模型也可以：不写 `background`，脚本会画一个带主题色光晕的深色渐变。它比一张好的底图平淡，但字和卡片都读得清。
