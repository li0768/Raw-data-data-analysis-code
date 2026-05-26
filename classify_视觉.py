#!/usr/bin/env python3
"""轻量化视觉模态评论分类脚本 — 基于关键词+语义规则"""

import csv
import re

# ============================================================
# 分类规则 (pattern, 二级标题, 三级标题)
# 按优先级排列，匹配到第一个即停止
# ============================================================

RULES = [
    # ================================================================
    # 非遗视觉 - 技艺制作（手工、工艺、制作过程）
    # ================================================================
    ("crafts(?:wo)?man|craftsmanship|handicraft|handmade|artisan|handiwork|hand.?craft",
     "非遗视觉", "技艺制作"),
    ("embroidery|sewing|weaving|weaver|carving|dyeing|pottery|woodwork|carpentry|basket.*(?:weaving|making|craft)",
     "非遗视觉", "技艺制作"),
    ("loom|spinning|spindle|wax.?printing|batik|brocade|knitting|crochet|quilting|tapestry|calligraphy|ink.*(?:making|stick)|paper.*making",
     "非遗视觉", "技艺制作"),
    (r"\bmak(?:e|ing)\b.*\b(?:oil|ink|paper|cloth|fabric|silk|thread|furniture|carpet|basket|pot|vase|bowl|lamp|candle|soap|wine|sauce|tofu|noodle)\b",
     "非遗视觉", "技艺制作"),
    ("糖画|candy art|sugar art|sugar painting|paper.cut|剪纸|蜀绣|刺绣|竹编|漆器|陶艺|木工|染布|编织|纺线",
     "非遗视觉", "技艺制作"),
    ("(?:traditional|ancient|old.?fashioned).*(?:craft|skill|technique|method|way.*making)|(?:craft|skill|technique).*(?:traditional|ancient)",
     "非遗视觉", "技艺制作"),
    ("(?:grow|plant|harvest|pick|gather|collect).*(?:tea|cotton|rice|soy|herb|medicin|vegetable|fruit|crop|flower|rose|lavender|chrysanthemum)",
     "非遗视觉", "技艺制作"),
    ("she.*(?:make|made|makes|create|creates|created).*(?:beautiful.*thing|everything|all.*(?:this|these|that|those))",
     "非遗视觉", "技艺制作"),

    # ================================================================
    # 非遗视觉 - 传统景物（传统建筑、服饰、节日、文化元素）
    # ================================================================
    ("Chinese.*(?:New Year|lunar.*year|spring festival|festival|lantern|dragon|lion.*(?:dance|dancing))",
     "非遗视觉", "传统景物"),
    ("(?:new year|lunar|spring festival|lantern festival|mid.?autumn|dragon boat|qingming|winter solstice).*(?:chinese|china|traditional|cultural)",
     "非遗视觉", "传统景物"),
    ("hanfu|cheongsam|qipao|traditional.*(?:chinese|asian).*(?:clothes|dress|costume|outfit|attire|garment)",
     "非遗视觉", "传统景物"),
    ("traditional.*(?:dress|clothes|costume|outfit|building|house|architecture|decoration|festival|ritual|custom|culture|instrument|music|dance)",
     "非遗视觉", "传统景物"),
    ("cultural.*(?:heritage|tradition|relic|treasure)|intangible.*(?:cultural|culture).*heritage",
     "非遗视觉", "传统景物"),
    ("ancient.*(?:style|building|town|village|city|temple|pagoda|garden|bridge|road|path|tree)",
     "非遗视觉", "传统景物"),
    ("old.*(?:way|tradition|custom|practice|method)|(?:chinese|china).*(?:traditional|cultural|culture|ancient|heritage)",
     "非遗视觉", "传统景物"),
    ("decoration.*(?:chinese|new.year|festival|spring|lantern|red)|(?:chinese|new.year|festival).*decoration",
     "非遗视觉", "传统景物"),
    ("(?:love|like|beautiful|gorgeous|stunning|amazing|nice|great|wonderful|pretty|lovely|mesmerizing|enchanting).*(?:decoration|decor|ornament|adornment)",
     "非遗视觉", "传统景物"),
    ("(?:decoration|decor|ornament).*(?:love|like|beautiful|gorgeous|stunning|amazing|nice|great|wonderful|pretty|lovely|mesmerizing|enchanting|magnificent|gorgeous)",
     "非遗视觉", "传统景物"),

    # ================================================================
    # 自然场景视觉 - 氛围赞美（治愈、放松、宁静、助眠、怀旧）
    # ================================================================
    ("peace|peaceful|calm|calming|relax|relaxing|serene|serenity|tranquil|tranquility|zen|meditative|soothe|soothing",
     "自然场景视觉", "氛围赞美"),
    ("find.*(?:peace|calm|solace|comfort|relax|serenity|tranquil|escape)|escape.*(?:reality|stress|worry|anxiety|tension)",
     "自然场景视觉", "氛围赞美"),
    ("watch.*(?:before.*(?:bed|sleep)|to.*(?:sleep|relax|unwind|calm|chill|de.?stress)|when.*(?:stress|sad|down|anxious|depress|insomnia))",
     "自然场景视觉", "氛围赞美"),
    ("(?:help|helped|helps).*(?:sleep|fall.asleep|insomnia|relax|calm|anxiety|stress|depress|mental.*health|cope|pandemic|lockdown|quarantine)",
     "自然场景视觉", "氛围赞美"),
    ("sleep|fall asleep|insomnia|bedtime|ASMR|oddly.*satisfying|satisfying.*watch",
     "自然场景视觉", "氛围赞美"),
    ("nostalg(?:ia|ic)|childhood.*(?:memory|memories|feeling|days)|remind.*(?:me|us).*(?:child|childhood|past|old.*(?:day|time|memory)|home.*town)",
     "自然场景视觉", "氛围赞美"),
    ("warm.*(?:feeling|vibe|atmosphere|ambiance|home|heart|blanket|hug)|cozy|cosy|comfort.*(?:video|watch|feeling|zone)",
     "自然场景视觉", "氛围赞美"),
    ("vibe|vibes|atmosphere|ambiance|mood|aura|feeling.*(?:good|amazing|wonderful|nice|great|special|magical|different|unique)",
     "自然场景视觉", "氛围赞美"),
    ("(?:feel|feeling).*(?:peace|calm|relax|serene|tranquil|zen|good|warm|cozy|cosy|home|comfort|nostalg)",
     "自然场景视觉", "氛围赞美"),
    ("(?:so|very|truly|absolutely|really|soo+).*(?:peaceful|calming|relaxing|soothing|serene|therapeutic|healing)",
     "自然场景视觉", "氛围赞美"),
    ("氛围|宁静|安详|平和|平静|安逸|舒适|放松|治愈|身心|心灵|安静|助眠|安眠",
     "自然场景视觉", "氛围赞美"),
    ("find.*peace|inner.*peace|peace.*mind|peace.*heart|peace.*soul",
     "自然场景视觉", "氛围赞美"),

    # ================================================================
    # 自然场景视觉 - 生活环境呈现（乡村生活、田园、简单生活）
    # ================================================================
    ("(?:live|living|lifestyle|life).*(?:simple|peaceful|slow|quiet|country|rural|village|farm|cottage|countryside)",
     "自然场景视觉", "生活环境呈现"),
    ("(?:simple|peaceful|slow|quiet|country|rural|village|farm|cottage|countryside).*(?:live|living|lifestyle|life|home|house)",
     "自然场景视觉", "生活环境呈现"),
    ("dream.*(?:life|home|house|living|lifestyle|place)|ideal.*(?:life|home|house|living|lifestyle)",
     "自然场景视觉", "生活环境呈现"),
    ("(?:wish|could|want).*(?:live.*(?:there|here|like.*this|this.*way)|have.*(?:life|home|house|living).*(?:there|here|like.*this))",
     "自然场景视觉", "生活环境呈现"),
    ("escape.*(?:city|urban|modern.*life|rat.*race|hustle.*bustle)|away.*from.*(?:city|urban|noise|hustle|stress|chaos|modern)",
     "自然场景视觉", "生活环境呈现"),
    ("乡村|田园.*(?:生活|日子|风光|景色)|农家|隐居|慢生活|世外.*(?:生活|日子|桃源)",
     "自然场景视觉", "生活环境呈现"),
    ("grandma|grandmother|grandpa|grandfather.*(?:life|living|home|house|together|family|love)",
     "自然场景视觉", "生活环境呈现"),
    ("family.*(?:life|living|home|house|together|bond|love|moment|time|gathering|union|reunion)",
     "自然场景视觉", "生活环境呈现"),
    ("village.*(?:life|living|lifestyle)|country.*(?:life|living|lifestyle).*(?:beautiful|simple|peaceful|wonderful|amazing|nice|great|lovely)",
     "自然场景视觉", "生活环境呈现"),

    # ================================================================
    # 自然场景视觉 - 风景赞美（自然风光、山水、花木、季节）
    # ================================================================
    ("scenery|landscape|view.*(?:beautiful|gorgeous|stunning|amazing|breathtaking|magnificent|spectacular|wonderful|lush|pristine)",
     "自然场景视觉", "风景赞美"),
    ("(?:beautiful|gorgeous|stunning|amazing|breathtaking|magnificent|spectacular|wonderful|lush|pristine).*(?:scenery|landscape|view|mountain|river|lake|garden|flower|forest|field|sunset|sunrise)",
     "自然场景视觉", "风景赞美"),
    ("nature.*(?:beautiful|gorgeous|stunning|amazing|breathtaking|magnificent|spectacular|wonderful|lush|vibrant)",
     "自然场景视觉", "风景赞美"),
    ("(?:season|seasons|autumn|spring|winter|summer|fall).*(?:beautiful|gorgeous|stunning|amazing|lovely|wonderful|nice|great|\bi.*(?:love|like|envy|miss|wish))",
     "自然场景视觉", "风景赞美"),
    ("beautiful.*(?:place|country|village|countryside|nature|mountain|garden|area|world|earth)",
     "自然场景视觉", "风景赞美"),
    ("(?:mountain|river|lake|garden|flower|forest|field|waterfall|stream|pond|bamboo|hill|valley|sky|cloud|rain|snow).*(?:beautiful|gorgeous|stunning|amazing|breathtaking|magnificent|spectacular)",
     "自然场景视觉", "风景赞美"),
    ("风景|景色|山水|田园|自然.*(?:美|好|漂亮|如画|迷人)|风光|如画|世外桃源|人间仙境|仙境|美景",
     "自然场景视觉", "风景赞美"),
    ("envy.*(?:season|country|place|nature|garden|view|scenery|landscape)|jealous.*(?:season|country|place|nature|garden)",
     "自然场景视觉", "风景赞美"),
    ("beautiful.*(?:environment|surrounding|setting|location|scenery|landscape|garden|yard|backyard)",
     "自然场景视觉", "风景赞美"),

    # ================================================================
    # 拍摄制作视觉 - 画面赞美（镜头、色彩、构图、光影、画面美感）
    # ================================================================
    ("cinemat(?:ic|ography)|cinema|visual.*(?:feast|masterpiece|treat|pleasure|delight|stunning|beautiful|gorgeous)",
     "拍摄制作视觉", "画面赞美"),
    ("(?:beautiful|gorgeous|stunning|amazing|wonderful|magnificent|breathtaking|spectacular).*(?:shot|cinematography|scene|visual|footage|film|video|camera|lighting|editing|camerawork|film.?making|production)",
     "拍摄制作视觉", "画面赞美"),
    ("(?:shot|scene|visual|footage|film|video|camera|camerawork|lighting|editing|film.?making|production).*(?:(?:\bis\b|\bare\b|so|very|truly|absolutely|really).*(?:beautiful|gorgeous|stunning|amazing|wonderful|magnificent|breathtaking|spectacular|incredible|fantastic))",
     "拍摄制作视觉", "画面赞美"),
    ("color.*(?:grading|palette|tone|vibrant|rich|beautiful|gorgeous|saturated|amazing)|lighting.*(?:beautiful|magical|perfect|stunning|amazing|gorgeous|soft|warm|natural)",
     "拍摄制作视觉", "画面赞美"),
    ("every.*(?:frame|shot|scene).*(?:painting|masterpiece|beautiful|stunning|art|picture|photo|perfect)|aesthetic.*(?:video|visual|pleasing|beautiful|goal)",
     "拍摄制作视觉", "画面赞美"),
    ("high.*quality.*(?:video|content|production|image|picture|photo)|production.*(?:quality|value).*(?:high|great|amazing|top)",
     "拍摄制作视觉", "画面赞美"),
    ("well.*(?:shot|filmed|made|produced|edited|directed|done|executed)|beautifully.*(?:shot|filmed|made|edited|done)",
     "拍摄制作视觉", "画面赞美"),
    ("像.*(?:画|电影|仙境|童话|梦境|诗)|如.*(?:画|仙境|梦境)|每一帧.*(?:美|画|漂亮|好看)|构图|滤镜|画面|镜头|画质|拍摄|摄影",
     "拍摄制作视觉", "画面赞美"),
    ("(?:love|like|enjoy|adore|appreciate).*(?:your|the|these|those|this|watching.*your).*(?:video|videos|channel|content|edit|footage|film)",
     "拍摄制作视觉", "画面赞美"),
    ("(?:video|videos|channel|content|footage).*(?:is |are |so |very |truly |really |absolutely |such a? ).*(?:beautiful|gorgeous|stunning|amazing|wonderful|great|nice|fantastic|awesome|incredible|lovely|brilliant)",
     "拍摄制作视觉", "画面赞美"),
    ("(?:beautiful|gorgeous|stunning|amazing|wonderful|great|nice|fantastic|awesome|incredible|lovely).*(?:video|videos|channel|content|edit|footage|film)",
     "拍摄制作视觉", "画面赞美"),
    ("\bvideo\b.*\b(?:love|like|enjoy|adore|appreciate|miss|favorite|favourite|best|greatest|top|number.?one)\b",
     "拍摄制作视觉", "画面赞美"),
    ("content.*(?:is |are |so |very |really |truly ).*(?:good|great|amazing|wonderful|beautiful|nice|fantastic|awesome|excellent)",
     "拍摄制作视觉", "画面赞美"),
    ("(?:nice|great|amazing|wonderful|beautiful|awesome|fantastic|excellent|lovely|brilliant).*(?:video|videos|channel|content|sharing|share|upload)",
     "拍摄制作视觉", "画面赞美"),

    # ================================================================
    # 拍摄制作视觉 - 叙事画面风格（叙事、风格、节奏、意境、治愈风格）
    # ================================================================
    ("storytelling|narrative|story.*(?:telling|line|arc)|rhythm.*(?:video|editing|pace|film)|pace.*(?:video|editing|film)",
     "拍摄制作视觉", "叙事画面风格"),
    ("poetic|lyrical|dreamlike|surreal|fantasy.*(?:visual|scene|style)|fairytale|fairy.?tale|magical.*(?:visual|video|scene|style|world)",
     "拍摄制作视觉", "叙事画面风格"),
    ("style.*(?:unique|distinctive|special|beautiful|amazing|different)|(?:unique|distinctive|special).*(?:style|touch|flavor|feel|vibe)",
     "拍摄制作视觉", "叙事画面风格"),
    ("意境|韵味|叙事|节奏|风格.*(?:独特|美|好|棒|赞)|唯美.*风|文艺|诗意|仙境|梦幻|童话.*(?:世界|般|风格|感)",
     "拍摄制作视觉", "叙事画面风格"),
    ("everything.*(?:looks?|seems?|feels?).*(?:magical|dreamlike|surreal|fantasy|perfect|beautiful)",
     "拍摄制作视觉", "叙事画面风格"),
    ("(?:like|as).*(?:a |an )?(?:movie|film|painting|fairytale|poem|dream|work.*art|masterpiece)",
     "拍摄制作视觉", "叙事画面风格"),

    # ================================================================
    # 拍摄制作视觉 - 拍摄付出评价（称赞拍摄者的努力、付出、耐心）
    # ================================================================
    ("(?:must have|must\'?ve|must.?a).*taken.*(?:long|ages|forever|hours|days|weeks|months|so.*(?:long|much).*(?:time|effort|work))",
     "拍摄制作视觉", "拍摄付出评价"),
    ("(?:so|how|such).*(?:much|many|lot).*(?:effort|work|time|dedication|patience|hard.*work|commitment|devotion)",
     "拍摄制作视觉", "拍摄付出评价"),
    ("amount.*work|lot.*(?:of |a ).*(?:work|effort|time|dedication).*(?:put|went|goes|gone|spent)",
     "拍摄制作视觉", "拍摄付出评价"),
    ("hard.*work.*(?:video|film|shoot|make|produce|edit|put|go|went)|effort.*(?:video|film|shoot|make|produce|edit|put|go|went)",
     "拍摄制作视觉", "拍摄付出评价"),
    ("拍摄.*(?:辛苦|不易|用心|认真|付出|努力|辛劳|劳累)|制作.*(?:辛苦|用心|认真|付出|精良|精?美)",
     "拍摄制作视觉", "拍摄付出评价"),
    ("(?:dedication|devotion|commitment|patience|patient).*(?:video|making|filming|shooting|creating|producing|editing|channel|content)",
     "拍摄制作视觉", "拍摄付出评价"),
    ("(?:put|puts|putting|go|goes|went|spend|spends|spent).*(?:so|a lot of|tremendous|incredible|amazing).*(?:effort|work|time|energy|dedication)",
     "拍摄制作视觉", "拍摄付出评价"),

    # ================================================================
    # 拍摄制作视觉 - 食材视觉（食物、食材呈现、烹饪视觉）
    # ================================================================
    ("ingredient.*(?:fresh|beautiful|amazing|wonderful|gorgeous|color|colorful|organic|natural)",
     "拍摄制作视觉", "食材视觉"),
    ("fresh.*(?:vegetable|fruit|produce|ingredient|food|meal|dish)|food.*(?:presentation|visual|styling|photography)",
     "拍摄制作视觉", "食材视觉"),
    ("(?:food|dish|meal|cooking|cook|cuisine).*(?:looks?|is |are |so |very |truly |absolutely ).*(?:delicious|yummy|tasty|amazing|beautiful|gorgeous|stunning|wonderful|mouth.?watering|delectable|scrumptious)",
     "拍摄制作视觉", "食材视觉"),
    ("(?:delicious|yummy|tasty|mouth.?watering|delectable|scrumptious).*(?:food|dish|meal|cooking|recipe|cuisine)",
     "拍摄制作视觉", "食材视觉"),
    ("食材.*(?:新鲜|美|好|棒|赞|诱人|丰富|健康)|美食.*(?:画面|视觉|呈现|展示|镜头)",
     "拍摄制作视觉", "食材视觉"),
    ("foodporn|food.*(?:stunning|mesmerizing|hypnoti|drooling|drool)",
     "拍摄制作视觉", "食材视觉"),

    # ================================================================
    # 拍摄制作视觉 - 多元素肯定（同时肯定多个方面）
    # ================================================================
    ("everything.*(?:about|in|of).*(?:video|channel|content|this|that).*(?:is |are ).*(?:perfect|beautiful|amazing|wonderful|great|nice|awesome|fantastic)",
     "拍摄制作视觉", "多元素肯定"),
    ("(?:perfect|beautiful|amazing|wonderful).*(?:combination|blend|mix|balance|fusion|harmony|marriage).*(?:of |between)",
     "拍摄制作视觉", "多元素肯定"),
    ("(?:love|like|enjoy|adore).*(?:everything|all|every.*(?:aspect|part|detail|thing)).*(?:about|in|of).*(?:video|channel|content|this)",
     "拍摄制作视觉", "多元素肯定"),
    ("方方面面|各方面|全都|每个.*(?:细节|方面|部分|角落|画面|镜头).*(?:美|好|棒|赞|完美|精彩|出色)",
     "拍摄制作视觉", "多元素肯定"),

    # ================================================================
    # 人物视觉 - 形象赞美（赞美人物外貌、美丽）
    # ================================================================
    ("beautiful.*(?:lady|woman|girl|person|she|face|smile|eyes|hair|skin|dress|style|soul|heart)",
     "人物视觉", "形象赞美"),
    ("(?:lady|woman|girl|she).*(?:is |are |so |very |truly |absolutely |really |the most ).*(?:beautiful|gorgeous|stunning|pretty|lovely|elegant|graceful|charming|attractive|radiant|glowing)",
     "人物视觉", "形象赞美"),
    ("(?:beautiful|gorgeous|stunning|pretty|lovely|elegant|graceful|charming|attractive|radiant).*(?:lady|woman|girl|she|person|face|smile|eyes|hair)",
     "人物视觉", "形象赞美"),
    ("(?:most|very|so|truly|absolutely).*(?:beautiful|gorgeous|stunning|pretty|lovely).*(?:lady|woman|girl|person|face|smile|human|being|creature|soul)",
     "人物视觉", "形象赞美"),
    ("beauty.*queen|princess|goddess|angel\b|flawless|drop.?dead.*gorgeous|breathtaking.*(?:beauty|woman|girl|lady)",
     "人物视觉", "形象赞美"),
    ("美女|漂亮.*(?:姑娘|女生|姐姐|小姐姐|妹妹|阿姨|女孩|女人|博主|up主|up)|美貌|颜值",
     "人物视觉", "形象赞美"),
    ("pretty.*(?:girl|woman|lady|person|face|smile|eyes|hair|dress|outfit|style)|(?:girl|woman|lady).*(?:is |are |so |very |such a? ).*pretty",
     "人物视觉", "形象赞美"),

    # ================================================================
    # 人物视觉 - 镜头前形象（穿着、装扮、造型）
    # ================================================================
    ("(?:outfit|dress|clothes|costume|style|look|appearance|makeup|hairstyle|hair.?style).*(?:is |are |so |very |beautiful|gorgeous|stunning|amazing|nice|great|elegant|lovely|wonderful|perfect|flawless|impeccable|on.?point)",
     "人物视觉", "镜头前形象"),
    ("(?:love|like|adore|admire).*(?:her |your |the ).*(?:outfit|dress|clothes|style|look|hairstyle|makeup|wardrobe|fashion)",
     "人物视觉", "镜头前形象"),
    ("classy|elegant.*(?:lady|woman|girl|style|look|dress|appearance|outfit|fashion)|graceful.*(?:lady|woman|movement|gesture|appearance)",
     "人物视觉", "镜头前形象"),
    ("(?:dressed|dresses|dressing).*(?:so |very |really |truly |beautifully|elegantly|nicely|well|impeccably|perfectly|gorgeously|stunningly)",
     "人物视觉", "镜头前形象"),

    # ================================================================
    # 人物视觉 - 姿态呈现（品格、气质、性格、举止、神态）
    # ================================================================
    ("hardworking|hard.working|diligent|dedicated|industrious|determined|persistent|resilient|strong.*(?:woman|girl|lady|person|individual|character|spirit|will|mind)",
     "人物视觉", "姿态呈现"),
    ("smart.*(?:girl|woman|lady|person|individual|cookie)|intelligent|wise|talented|gifted|skilled|skillful|capable|resourceful|independent",
     "人物视觉", "姿态呈现"),
    ("(?:calm|gentle|kind|sweet|humble|modest|patient|graceful|poised|composed|soft.?spoken|warm.?hearted|good.?hearted|kind.?hearted).*(?:lady|woman|girl|person|soul|spirit|heart|nature|demeanor)",
     "人物视觉", "姿态呈现"),
    ("勤劳|坚强|优雅.*(?:姿态|举止|气质|风度)|温柔|贤惠|能干|灵巧|聪慧|善良|淳朴|大方|从容|淡定|恬静",
     "人物视觉", "姿态呈现"),
    ("(?:love|like|admire|respect|adore).*(?:her |your |their ).*(?:personality|character|spirit|attitude|manner|demeanor|way|nature|heart|soul|grace|poise|strength|determination|perseverance|resilience)",
     "人物视觉", "姿态呈现"),
    ("(?:she|her).*(?:is |are |so |very |such a? ).*(?:amazing|wonderful|incredible|remarkable|extraordinary|awesome|fantastic|great|lovely|sweet|kind|nice).*(?:person|woman|human|lady|girl|soul|being)",
     "人物视觉", "姿态呈现"),
    ("role.?model|idol|inspiration|inspirational|admirable|respectable|respect.*(?:\bher\b|\bthis woman\b|\bthis girl\b|\bthis lady\b|\bthis person\b)",
     "人物视觉", "姿态呈现"),

    # ================================================================
    # 补充：work/presentation 相关赞美
    # ================================================================
    ("(?:your|her|the|this).*(?:work|presentation|sharing|share).*(?:is |are |so+|very |really |truly |absolutely |such a? ).*(?:great|amazing|wonderful|beautiful|nice|fantastic|awesome|excellent|brilliant|superb|outstanding|magnificent|incredible|phenomenal|remarkable|extraordinary|perfect|good|lovely)",
     "拍摄制作视觉", "画面赞美"),
    ("(?:great|amazing|wonderful|beautiful|nice|fantastic|awesome|excellent|brilliant|superb|outstanding|magnificent|incredible|phenomenal|remarkable|extraordinary|perfect).*(?:work|presentation|sharing|share|job|effort)",
     "拍摄制作视觉", "画面赞美"),
    ("(?:love|like|enjoy|adore).*(?:your|her|the|this).*(?:work|presentation|sharing|content|job)",
     "拍摄制作视觉", "画面赞美"),

    # ================================================================
    # 补充：self-contained / Renaissance / multi-talented 人物赞美
    # ================================================================
    ("self.?contained|renaissance.*(?:woman|man|person)|multi.?talented|all.?rounder|jack.*all.*trades|versatile.*(?:woman|girl|lady|person)",
     "人物视觉", "姿态呈现"),
    ("(?:she|her|he|they).*(?:is |are |can |does ).*(?:everything|anything|all|it all|so much|so many)",
     "人物视觉", "姿态呈现"),
]

# ============================================================
# 通用美感词（不涉及具体对象时的 fallback -> 画面赞美）
# ============================================================
GENERIC_PRAISE = re.compile(
    r'(?:this|that|it|these|those)?\s*'
    r'(?:is|are|was|were|really|truly|absolutely|so+|very|just|simply|seriously|literally|honestly|actually|quite|pretty|most|totally|utterly|completely|extremely|incredibly|unbelievably|insanely|ridiculously|unreal|stunningly)?\s*'
    r'(?:beautiful|gorgeous|stunning|amazing|wonderful|magnificent|breathtaking|awesome|spectacular|incredible|fantastic|nice|great|lovely|excellent|perfect|brilliant|superb|fabulous|sublime|heavenly|divine|marvelous|phenomenal|outstanding|impressive|extraordinary|remarkable|unbelievable|unreal|insane|mind.?blowing|magnificent|mesmerizing|enchanting|dazzling|captivating|spellbinding|good)\b'
    r'\s*(?:video|videos|channel|content|edit|footage|film|work|job|thing|stuff|one|watch|watching|seeing|looking|liziqi|li.?zi.?qi|moment|moments|presentation|show|sharing)?'
    r'[^\w]*$',
    re.IGNORECASE
)

# 纯感叹词/表情
EXCLAMATION_ONLY = re.compile(
    r'^(?:wow|wow+|omg|oh\s*my\s*god|whoa|woah|damn|da+y?mn|holy|jeez|bravo|kudos|hats?\s*off|well\s*done|good\s*job|respect|salute|chapeau)[!.\s]*$',
    re.IGNORECASE
)

# ============================================================
# 人物相关上下文词（必须与 beauty 类词搭配才判断为人物）
# ============================================================
PERSON_CONTEXT = re.compile(
    r'\b(?:she|her|hers|woman|women|girl|lady|female|person|human|being|creature|soul|博主|up主|up|小姐姐|姐姐|妹妹|姑娘|女生|女孩|女人|阿姨|妈妈|奶奶|grandma|grandmother|aunt|mother|mom|mum|mama)\b',
    re.IGNORECASE
)

BEAUTY_WORD = re.compile(
    r'\b(?:beautiful|gorgeous|stunning|pretty|lovely|elegant|graceful|charming|attractive|good.?looking|hot|sexy|cute|adorable|radiant|glowing|flawless|breathtaking|enchanting|alluring|fetching|comely|fair|handsome)\b',
    re.IGNORECASE
)

# 人物特征词（不一定是 beauty，但明确指向人的特征）
PERSON_FEATURE = re.compile(
    r'\b(?:smile|smiles|smiling|eyes|face|hair|dress|outfit|appearance|look|looks|makeup|hairstyle|wardrobe|fashion|style)\b',
    re.IGNORECASE
)

# 视频相关词
VIDEO_CONTEXT = re.compile(
    r'\b(?:video|videos|channel|content|edit|footage|film|films|watch|watching|subscribe|subscriber|upload|uploads|YouTube|youtube|vlog|vlogs|clip|clips)\b',
    re.IGNORECASE
)

# 自然/环境相关词
NATURE_CONTEXT = re.compile(
    r'\b(?:nature|garden|flower|tree|plant|mountain|river|lake|forest|field|sky|cloud|rain|snow|sun|moon|star|animal|bird|cat|dog|pet|ocean|sea|beach|waterfall|stream|pond|landscape|scenery|view|environment|countryside|village|farm|rural|outdoor|wilderness|wildlife)\b',
    re.IGNORECASE
)

# 食物相关词
FOOD_CONTEXT = re.compile(
    r'\b(?:food|cook|cooking|dish|meal|recipe|cuisine|eat|eating|delicious|yummy|tasty|ingredient|vegetable|fruit|meat|rice|noodle|soup|sauce|spice|herb|bake|baking|roast|roasting|fry|frying|steam|steaming|boil|boiling|stir.?fry|dinner|lunch|breakfast|snack|dessert|appetizer|entree)\b',
    re.IGNORECASE
)

# 中国新年/节日相关词
CNY_CONTEXT = re.compile(
    r'\b(?:Chinese\s*New\s*Year|Lunar\s*New\s*Year|Spring\s*Festival|new\s*year.*(?:chinese|lunar|spring)|(?:happy|blessed|blessing).*(?:new\s*year|lunar|spring\s*festival)|year\s*of\s*(?:the\s*)?(?:dragon|snake|horse|goat|monkey|rooster|dog|pig|rat|ox|tiger|rabbit))\b',
    re.IGNORECASE
)


def classify(text: str) -> tuple:
    """返回 (二级标题, 三级标题)"""
    t = text.strip()

    if not t:
        return ("其他", "无具体三级")

    # ---- 第一层：遍历精确规则 ----
    for pattern, cat2, cat3 in RULES:
        if re.search(pattern, t, re.IGNORECASE):
            return (cat2, cat3)

    # ---- 第二层：中文 fallback 规则 ----
    # 中文视觉赞美：太X了、好美、真好看 等
    if re.search(r'(?:太|很|好|真|超|极|非常|特别|如此|多么|这么|那么|十分|无比|最|贼|老|越来越|越來越|实在|實在|真的|的确|确实|确实|绝对|简直|完全|好不|异常|格外|分外|相当|蛮|挺|够|可|怪|多么|多)\s*'
                 r'(?:美|好看|漂亮|精彩|棒|赞|震撼|惊艳|绝美|炫酷|厉害|牛|强|不错|不?简单|不?容易|给力|出色|完美|精致|唯美|梦幻|壮观|好|妙|优|佳|帅气|酷)\s*'
                 r'(?:了|啊|呀|哦|的|啦|呢|吧|耶|哈|哟|嘛|噢|喔|哇|噻|滴|得|很|极了|得很|死了|极了|翻天|至极|无比|至|不行|不要|不得了|要命|要死|透|坏|惨|爆|炸|翻|哭|疯|呆){0,2}\s*$',
            t):
        return ("拍摄制作视觉", "画面赞美")

    # 中文喜欢/爱+看/视频/内容
    if re.search(r'(?:喜欢|喜爱|爱|爱看|喜欢看|爱了|爱死|粉|迷|欣赏).*(?:视频|内容|作品|博主|up|这个|那个|这些|你的|您|看|观看|节目|频道)', t):
        return ("拍摄制作视觉", "画面赞美")

    # 中文传统文化
    if re.search(r'(?:传统|中国|中华|民族|古代|古老|非遗).*(?:文化|艺术|工艺|手艺|美食|节日|服饰|建筑|乐器|音乐|舞蹈|戏曲|书法|绘画|瓷器|丝绸|茶叶|中医|武术|太极)', t):
        return ("非遗视觉", "传统景物")

    # 中文生活/乡村
    if re.search(r'(?:生活|日子|人生).*(?:美好|舒服|安逸|惬意|快乐|幸福|简单|朴素|纯朴|淳朴|宁静|平静|悠闲|自在|自由)', t):
        return ("自然场景视觉", "生活环境呈现")

    # 中文自然花草
    if re.search(r'(?:花|草|树木|森林|山|河|湖|海|云|天空|雪花|雨|风|阳光|月光|星空|日出|日落|春夏秋冬|春天|夏天|秋天|冬天|四季).*(?:美|好看|漂亮|太|真|很|好)', t):
        return ("自然场景视觉", "风景赞美")

    # 中文人物
    if re.search(r'(?:女神|小姐姐|姐姐|姑娘|美女|妹子|很?漂亮|美丽|气质好|颜值).*(?:人|姑娘|女生|姐姐|小姐姐|妹妹|阿姨|女孩|女人|博主|up)', t):
        return ("人物视觉", "形象赞美")

    # 中文看视频
    if re.search(r'(?:视频|影片|节目|频道|内容|作品).*(?:好|棒|赞|不错|出色|精彩|好看|漂亮|美|喜欢|爱)', t):
        return ("拍摄制作视觉", "画面赞美")

    # 中文传统文化（广义）
    if re.search(r'(?:传统|中国|中华).*(?:文化|节日|食品|美食|习俗|风俗|历史)', t):
        return ("非遗视觉", "传统景物")

    # ---- 第三层：通用美学感慨 ----
    if GENERIC_PRAISE.search(t) or EXCLAMATION_ONLY.search(t):
        return ("拍摄制作视觉", "画面赞美")

    # ---- 第四层：知名人物名 + 赞美词 -> 人物视觉 ----
    has_creator_name = bool(re.search(r'\b(?:liziqi|li ziqi|李子柒)\b', t, re.IGNORECASE))

    has_video = VIDEO_CONTEXT.search(t)
    has_beauty = BEAUTY_WORD.search(t)
    has_person_ctx = PERSON_CONTEXT.search(t)
    has_person_feat = PERSON_FEATURE.search(t)
    has_nature = NATURE_CONTEXT.search(t)
    has_food = FOOD_CONTEXT.search(t)
    has_cny = CNY_CONTEXT.search(t)

    # 知名人物+外貌/特征赞美 -> 人物视觉
    if has_creator_name and (has_beauty or has_person_feat):
        return ("人物视觉", "形象赞美")

    # video + beauty/person -> 画面赞美
    if has_video and (has_beauty or has_person_ctx):
        return ("拍摄制作视觉", "画面赞美")
    # video context only -> 画面赞美
    if has_video:
        return ("拍摄制作视觉", "画面赞美")

    # beauty + person context/feature -> 人物视觉
    if has_beauty and (has_person_ctx or has_person_feat):
        if has_person_feat and not has_person_ctx:
            return ("人物视觉", "镜头前形象")
        return ("人物视觉", "形象赞美")

    # person context alone -> 人物视觉
    if has_person_ctx:
        return ("人物视觉", "形象赞美")

    # person feature alone -> 人物视觉
    if has_person_feat:
        return ("人物视觉", "镜头前形象")

    # beauty alone (without person context) -> 画面赞美
    if has_beauty:
        return ("拍摄制作视觉", "画面赞美")

    # nature -> 自然场景
    if has_nature:
        return ("自然场景视觉", "风景赞美")

    # food -> 食材视觉
    if has_food:
        return ("拍摄制作视觉", "食材视觉")

    # Chinese New Year -> 传统景物
    if has_cny:
        return ("非遗视觉", "传统景物")

    # ---- 第四层：中文宽松匹配 ----
    # 中文视觉赞美词
    if re.search(r'(?:美|好看|漂亮|精彩|棒|赞|震撼|惊艳|绝美|太.*(?:美|好看|棒))', t):
        return ("拍摄制作视觉", "画面赞美")

    # 中文人物词
    if re.search(r'(?:女神|小姐姐|姐姐|姑娘|美女|妹子|博主.*(?:美|好看|漂亮|气质))', t):
        return ("人物视觉", "形象赞美")

    # 中文氛围词
    if re.search(r'(?:治愈|放松|舒服|安逸|宁静|安详|平和|安静)', t):
        return ("自然场景视觉", "氛围赞美")

    # 中文自然词
    if re.search(r'(?:风景|景色|山水|花|草|树|山|水|云|天|田园|大自然|户外)', t):
        return ("自然场景视觉", "风景赞美")

    # ---- 最后一层：无法归类 ----
    return ("其他", "无具体三级")


def main():
    input_path = r"D:\桌面\沙湾飘色\视觉.csv"
    output_path = r"D:\桌面\沙湾飘色\视觉_classified.csv"

    rows = []
    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) >= 3:
                rows.append(row)

    total = len(rows)
    print(f"共读入 {total} 条记录，开始分类...")

    stats = {}
    classified_rows = []

    for idx, row in enumerate(rows):
        text = row[1] if len(row) > 1 else ""
        cat2, cat3 = classify(text)
        key = f"{cat2}|{cat3}"
        stats[key] = stats.get(key, 0) + 1
        classified_rows.append(row + [cat2, cat3])

        if (idx + 1) % 1000 == 0:
            print(f"  已处理 {idx + 1}/{total} ...")

    # 输出（逗号分隔，Excel兼容）
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=",", quoting=csv.QUOTE_ALL)
        header = ["作者", "内容", "点赞数", "发布时间", "原模态", "二级标题", "三级标题"]
        writer.writerow(header)
        for row in classified_rows:
            writer.writerow(row)

    # 统计
    print(f"\n分类完成！输出文件: {output_path}")
    print(f"\n{'='*65}")
    print(f"{'二级标题':<18} {'三级标题':<18} {'数量':>8} {'占比':>8}")
    print(f"{'='*65}")
    for key, cnt in sorted(stats.items(), key=lambda x: -x[1]):
        cat2, cat3 = key.split("|")
        pct = cnt / total * 100
        print(f"{cat2:<18} {cat3:<18} {cnt:>8} {pct:>7.1f}%")
    print(f"{'='*65}")
    print(f"{'合计':<18} {'':<18} {total:>8} {'100.0%':>8}")


if __name__ == "__main__":
    main()
